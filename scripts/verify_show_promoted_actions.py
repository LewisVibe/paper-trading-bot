from __future__ import annotations

import csv
import inspect
import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bot
from trading_bot.research import promoted_actions
from trading_bot.research.promoted_actions import (
    PROMOTED_ACTION_COLUMNS,
    build_show_promoted_actions_lines,
    show_promoted_actions_file,
)


FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "OrderSide",
    "TimeInForce",
    "download_close_prices",
    "download_backtest_prices",
    "download_slow_sma_preview_prices",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "init_database",
    "sqlite3",
    "get_alpaca_positions",
    "get_open_orders_for_ticker",
]


def action_row(
    strategy_name: str,
    ticker: str,
    desired_position: str,
    current_position: str,
    current_quantity: str,
    preview_action: str,
    preview_quantity: str,
    reason: str,
    diagnostic_warning: str = "",
) -> dict[str, str]:
    return {
        "created_at": "2026-06-06T00:00:00Z",
        "strategy_name": strategy_name,
        "strategy_family": "trend",
        "ticker": ticker,
        "desired_position": desired_position,
        "current_position": current_position,
        "current_quantity": current_quantity,
        "preview_action": preview_action,
        "preview_quantity": preview_quantity,
        "reason": reason,
        "promotion_status": "preview_candidate",
        "required_next_step": "Research preview only.",
        "preview_only": "True",
        "diagnostic_warning": diagnostic_warning,
    }


def add_failure(failures: list[str], message: str) -> None:
    failures.append(message)


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = "\n".join(
        [
            inspect.getsource(promoted_actions.build_show_promoted_actions_lines),
            inspect.getsource(promoted_actions.build_missing_promoted_actions_lines),
            inspect.getsource(promoted_actions.show_promoted_actions_file),
            inspect.getsource(promoted_actions.read_promoted_action_preview),
        ]
    )
    command_source = inspect.getsource(bot.run_show_promoted_actions)

    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in helper_source:
            add_failure(failures, f"show promoted-actions helpers should not reference {token}")
        if token in command_source:
            add_failure(failures, f"run_show_promoted_actions should not reference {token}")


def verify_missing_csv(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        missing_path = Path(temp_dir) / "missing.csv"
        status_code, lines = show_promoted_actions_file(missing_path)
    output = "\n".join(lines)
    if status_code != 1:
        add_failure(failures, "missing CSV should return status code 1")
    if "READ-ONLY DISPLAY. NOT EXECUTION." not in output:
        add_failure(failures, "missing CSV output should include the read-only warning")
    if "does not refresh positions or submit orders" not in output:
        add_failure(failures, "missing CSV output should include the no-refresh/no-order warning")
    if "python bot.py --preview-promoted-actions" not in output:
        add_failure(failures, "missing CSV output should instruct user to run preview-promoted-actions first")


def verify_normal_csv_display(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "promoted_strategy_action_preview.csv"
        rows = [
            action_row(
                "sma_50_200_trend",
                "AAPL",
                "long",
                "flat",
                "0",
                "would_open_long",
                "1",
                "Desired long and current position is flat.",
            ),
            action_row(
                "buy_above_200_exit_below_200",
                "MSFT",
                "flat",
                "long",
                "2",
                "would_close_long",
                "2",
                "Desired flat and current position is long.",
            ),
            action_row(
                "fifty_two_week_high_breakout",
                "SPY",
                "long",
                "unavailable",
                "",
                "position_unavailable",
                "",
                "Current paper position unavailable: alpaca_keys_missing.",
                "Current paper position unavailable: alpaca_keys_missing.",
            ),
        ]
        with input_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=PROMOTED_ACTION_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        original_contents = input_path.read_text(encoding="utf-8")

        status_code, lines = show_promoted_actions_file(input_path)
        output = "\n".join(lines)
        after_contents = input_path.read_text(encoding="utf-8")

    if status_code != 0:
        add_failure(failures, "normal CSV display should return status code 0")
    if original_contents != after_contents:
        add_failure(failures, "show-promoted-actions should not modify the input CSV")
    for expected_text in [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "does not refresh positions or submit orders",
        "Rows: 3",
        "- would_open_long: 1",
        "- would_close_long: 1",
        "- position_unavailable: 1",
        "- long: 2",
        "- flat: 1",
        "Diagnostic warning rows: 1",
        "sma_50_200_trend",
        "fifty_two_week_high_breakout",
        "position_unavailable",
    ]:
        if expected_text not in output:
            add_failure(failures, f"display output missing expected text: {expected_text}")


def verify_line_builder(failures: list[str]) -> None:
    lines = build_show_promoted_actions_lines(
        Path("data/promoted_strategy_action_preview.csv"),
        [
            action_row(
                "unavailable_case",
                "ZZZ",
                "long",
                "unavailable",
                "",
                "position_unavailable",
                "",
                "Current paper position unavailable.",
                "Current paper position unavailable.",
            )
        ],
    )
    output = "\n".join(lines)
    if "Diagnostic warning rows: 1" not in output:
        add_failure(failures, "line builder should summarize diagnostic_warning rows")
    if "position_unavailable" not in output:
        add_failure(failures, "line builder should preserve position_unavailable rows")


def verify_command_output_warning(failures: list[str]) -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        bot.run_show_promoted_actions()
    output = buffer.getvalue()
    first_line = output.splitlines()[0] if output.splitlines() else ""
    if first_line != "READ-ONLY DISPLAY. NOT EXECUTION.":
        add_failure(failures, "command output should start with the read-only warning")
    if "does not refresh positions or submit orders" not in output:
        add_failure(failures, "command output should include the no-refresh/no-order warning")


def main() -> int:
    failures: list[str] = []
    verify_no_forbidden_source_paths(failures)
    verify_missing_csv(failures)
    verify_normal_csv_display(failures)
    verify_line_builder(failures)
    verify_command_output_warning(failures)

    if failures:
        print("Show promoted actions verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Show promoted actions verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
