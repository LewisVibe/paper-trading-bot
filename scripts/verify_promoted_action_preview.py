from __future__ import annotations

import csv
import inspect
from decimal import Decimal
import io
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bot
from trading_bot.positions import Position
from trading_bot.research import promoted_actions
from trading_bot.research.promoted_actions import (
    PROMOTED_ACTION_COLUMNS,
    build_promoted_action_preview_rows,
    read_promoted_strategy_preview,
    write_promoted_action_preview,
)


FORBIDDEN_PROMOTED_ACTION_SOURCE_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "OrderSide",
    "TimeInForce",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "sqlite3",
]

FORBIDDEN_COMMAND_SOURCE_TOKENS = [
    "MarketOrderRequest",
    "OrderSide",
    "TimeInForce",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
]

EXECUTABLE_ORDER_FIELDS = {
    "order",
    "order_request",
    "order_data",
    "order_id",
    "order_status",
    "side",
    "time_in_force",
    "order_type",
}


def preview_row(strategy_name: str, ticker: str, desired_position: str) -> dict[str, str]:
    return {
        "strategy_name": strategy_name,
        "strategy_family": "trend",
        "ticker": ticker,
        "desired_position": desired_position,
        "promotion_status": "preview_candidate",
        "required_next_step": "Future preview-mode research only; not approved for paper execution.",
    }


def add_failure(failures: list[str], message: str) -> None:
    failures.append(message)


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = inspect.getsource(promoted_actions)
    for token in FORBIDDEN_PROMOTED_ACTION_SOURCE_TOKENS:
        if token in helper_source:
            add_failure(failures, f"promoted action helper should not reference {token}")

    command_source = inspect.getsource(bot.run_promoted_action_preview)
    position_loader_source = inspect.getsource(bot.load_promoted_action_preview_positions)
    for token in FORBIDDEN_COMMAND_SOURCE_TOKENS:
        if token in command_source:
            add_failure(failures, f"run_promoted_action_preview should not reference {token}")
        if token in position_loader_source:
            add_failure(failures, f"load_promoted_action_preview_positions should not reference {token}")

    if "get_alpaca_positions" not in position_loader_source:
        add_failure(failures, "position loader should use the read-only Alpaca position helper")


def verify_no_executable_order_fields(rows: list[dict[str, object]], failures: list[str]) -> None:
    for index, row in enumerate(rows, start=1):
        forbidden_fields = EXECUTABLE_ORDER_FIELDS.intersection(row.keys())
        if forbidden_fields:
            add_failure(
                failures,
                f"row {index} contains executable order field(s): {', '.join(sorted(forbidden_fields))}",
            )

    forbidden_columns = EXECUTABLE_ORDER_FIELDS.intersection(PROMOTED_ACTION_COLUMNS)
    if forbidden_columns:
        add_failure(
            failures,
            f"CSV columns should not contain executable order field(s): {', '.join(sorted(forbidden_columns))}",
        )


def verify_csv_roundtrip(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        preview_path = temp_path / "promoted_strategy_preview.csv"
        output_path = temp_path / "promoted_strategy_action_preview.csv"

        with preview_path.open("w", newline="", encoding="utf-8") as file:
            fieldnames = [
                "strategy_name",
                "strategy_family",
                "ticker",
                "desired_position",
                "promotion_status",
                "required_next_step",
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(preview_row("roundtrip_long", "AAA", "long"))
            writer.writerow(preview_row("roundtrip_flat", "BBB", "flat"))

        preview_rows = read_promoted_strategy_preview(preview_path)
        rows = build_promoted_action_preview_rows(
            preview_rows,
            {"BBB": Position(Decimal("2"))},
            "alpaca_paper",
            Decimal("1"),
            created_at="2026-06-06T00:00:00Z",
        )
        write_promoted_action_preview(output_path, rows)

        with output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            output_rows = list(reader)
            if reader.fieldnames != PROMOTED_ACTION_COLUMNS:
                add_failure(failures, "output CSV columns changed unexpectedly")

        if len(output_rows) != 2:
            add_failure(failures, "CSV roundtrip should write two output rows")
        if any(row.get("preview_only") != "True" for row in output_rows):
            add_failure(failures, "CSV output should keep preview_only true for every row")
        if output_rows and output_rows[0].get("preview_action") != "would_open_long":
            add_failure(failures, "CSV roundtrip long/flat action should be would_open_long")
        if len(output_rows) > 1 and output_rows[1].get("preview_action") != "would_close_long":
            add_failure(failures, "CSV roundtrip flat/long action should be would_close_long")


class FakeLogger:
    def __init__(self) -> None:
        self.warnings: list[str] = []

    def warning(self, message: str, *args: object) -> None:
        if args:
            message = message % args
        self.warnings.append(message)


def fake_config(
    dry_run: bool = True,
    api_key: str = "paper-key",
    secret_key: str = "paper-secret",
) -> SimpleNamespace:
    return SimpleNamespace(
        dry_run=dry_run,
        alpaca_api_key=api_key,
        alpaca_secret_key=secret_key,
    )


def verify_readonly_position_loader(failures: list[str]) -> None:
    original_client = bot.TradingClient
    original_get_positions = bot.get_alpaca_positions
    calls: list[tuple[str, str, bool]] = []

    class FakeTradingClient:
        def __init__(self, api_key: str, secret_key: str, paper: bool) -> None:
            calls.append((api_key, secret_key, paper))

    try:
        bot.TradingClient = FakeTradingClient
        bot.get_alpaca_positions = lambda client: {"AAA": Position(Decimal("2"))}

        logger = FakeLogger()
        positions, source = bot.load_promoted_action_preview_positions(
            fake_config(dry_run=True),
            logger,
            use_paper_positions_readonly=False,
        )
        if source != "dry_run_position_unavailable" or positions:
            add_failure(failures, "normal dry-run promoted action preview should not read paper positions")
        if calls:
            add_failure(failures, "normal dry-run promoted action preview should not create TradingClient")

        positions, source = bot.load_promoted_action_preview_positions(
            fake_config(dry_run=True),
            logger,
            use_paper_positions_readonly=True,
        )
        if source != "alpaca_paper_readonly":
            add_failure(failures, f"read-only flag should report alpaca_paper_readonly, got {source}")
        if positions.get("AAA") != Position(Decimal("2")):
            add_failure(failures, "read-only flag should use fake read-only paper positions")
        if calls != [("paper-key", "paper-secret", True)]:
            add_failure(failures, "read-only flag should create one paper=True TradingClient")

        positions, source = bot.load_promoted_action_preview_positions(
            fake_config(dry_run=True, api_key="", secret_key=""),
            logger,
            use_paper_positions_readonly=True,
        )
        if source != "alpaca_keys_missing" or positions:
            add_failure(failures, "missing paper keys should fall back to unavailable position source")

        def raise_position_error(client: object) -> dict[str, Position]:
            raise RuntimeError("paper position read failed")

        bot.get_alpaca_positions = raise_position_error
        positions, source = bot.load_promoted_action_preview_positions(
            fake_config(dry_run=True),
            logger,
            use_paper_positions_readonly=True,
        )
        if source != "alpaca_position_error" or positions:
            add_failure(failures, "position read failure should fall back to unavailable position source")
    finally:
        bot.TradingClient = original_client
        bot.get_alpaca_positions = original_get_positions


def verify_readonly_position_source_rows(failures: list[str]) -> None:
    rows = build_promoted_action_preview_rows(
        [
            preview_row("readonly_long", "AAA", "long"),
            preview_row("readonly_missing", "BBB", "flat"),
        ],
        {"AAA": Position(Decimal("2"))},
        "alpaca_paper_readonly",
        Decimal("1"),
        created_at="2026-06-06T00:00:00Z",
    )
    by_name = {row["strategy_name"]: row for row in rows}
    if by_name["readonly_long"]["current_position"] != "long":
        add_failure(failures, "alpaca_paper_readonly should mark provided position as available")
    if by_name["readonly_long"]["preview_action"] != "no_action_already_long":
        add_failure(failures, "alpaca_paper_readonly should use read-only current position context")
    if by_name["readonly_missing"]["current_position"] != "flat":
        add_failure(failures, "missing ticker from successful read-only source should be treated as flat")
    if by_name["readonly_missing"]["preview_action"] != "no_action_already_flat":
        add_failure(failures, "flat desired position with successful read-only source should stay flat")
    if any(row.get("preview_only") is not True for row in rows):
        add_failure(failures, "read-only source rows should remain preview_only")


def verify_flag_scope_guard(failures: list[str]) -> None:
    original_argv = sys.argv[:]
    stderr = io.StringIO()
    try:
        sys.argv = ["bot.py", "--use-paper-positions-readonly"]
        with redirect_stderr(stderr):
            result = bot.main()
    finally:
        sys.argv = original_argv
    if result != 2:
        add_failure(failures, "--use-paper-positions-readonly without --preview-promoted-actions should return 2")
    if "can only be used with --preview-promoted-actions" not in stderr.getvalue():
        add_failure(failures, "flag scope guard should explain required command")


def main() -> int:
    failures: list[str] = []
    verify_no_forbidden_source_paths(failures)
    verify_readonly_position_loader(failures)
    verify_readonly_position_source_rows(failures)
    verify_flag_scope_guard(failures)

    rows = build_promoted_action_preview_rows(
        [
            preview_row("long_flat", "AAA", "long"),
            preview_row("long_long", "BBB", "long"),
            preview_row("flat_long", "CCC", "flat"),
            preview_row("flat_flat", "DDD", "flat"),
            preview_row("flat_short", "EEE", "flat"),
            preview_row("long_short", "FFF", "long"),
        ],
        {
            "BBB": Position(Decimal("2")),
            "CCC": Position(Decimal("3")),
            "EEE": Position(Decimal("-4")),
            "FFF": Position(Decimal("-5")),
        },
        "alpaca_paper",
        Decimal("1"),
        created_at="2026-06-06T00:00:00Z",
    )
    by_name = {row["strategy_name"]: row for row in rows}
    expected = {
        "long_flat": "would_open_long",
        "long_long": "no_action_already_long",
        "flat_long": "would_close_long",
        "flat_flat": "no_action_already_flat",
        "flat_short": "unsupported_short_position_preview",
        "long_short": "unsupported_short_position_preview",
    }
    for name, action in expected.items():
        if by_name[name]["preview_action"] != action:
            failures.append(f"{name} expected {action}, got {by_name[name]['preview_action']}")

    unavailable = build_promoted_action_preview_rows(
        [preview_row("unavailable", "ZZZ", "long")],
        {},
        "alpaca_keys_missing",
        Decimal("1"),
        created_at="2026-06-06T00:00:00Z",
    )[0]
    if unavailable["preview_action"] != "position_unavailable":
        failures.append("unavailable position should be handled safely")
    if not unavailable["diagnostic_warning"]:
        failures.append("unavailable position should include diagnostic_warning")
    if any(row.get("preview_only") is not True for row in [*rows, unavailable]):
        failures.append("preview_only should always be true")
    if by_name["flat_long"]["preview_quantity"] != "3":
        failures.append("close preview quantity should use current long quantity")
    verify_no_executable_order_fields([*rows, unavailable], failures)
    verify_csv_roundtrip(failures)

    if failures:
        print("Promoted action preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Promoted action preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
