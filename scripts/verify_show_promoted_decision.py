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

from trading_bot.research import promoted_decision
from trading_bot.research.promoted_decision import (
    PROMOTED_DECISION_COLUMNS,
    build_show_promoted_decision_lines,
    show_promoted_decision_file,
)
from trading_bot.runners import research_reports


FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "OrderSide",
    "TimeInForce",
    "download_close_prices",
    "download_backtest_prices",
    "download_slow_sma_preview_prices",
    "configure_yfinance_cache",
    "get_alpaca_positions",
    "get_open_orders_for_ticker",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "decide_trade",
    "init_database",
    "sqlite3",
]


def decision_row(
    ticker: str,
    consensus_state: str,
    long_votes: str,
    flat_votes: str,
    risk_status_summary: str,
    action_summary: str,
    decision_state: str,
    execution_approved: str,
    reason: str,
) -> dict[str, str]:
    return {
        "created_at": "2026-06-07T00:00:00+00:00",
        "ticker": ticker,
        "consensus_state": consensus_state,
        "long_votes": long_votes,
        "flat_votes": flat_votes,
        "risk_status_summary": risk_status_summary,
        "action_summary": action_summary,
        "decision_state": decision_state,
        "execution_approved": execution_approved,
        "reason": reason,
        "research_only": "True",
        "preview_only": "True",
    }


def add_failure(failures: list[str], message: str) -> None:
    failures.append(message)


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = "\n".join(
        [
            inspect.getsource(promoted_decision.build_show_promoted_decision_lines),
            inspect.getsource(promoted_decision.build_missing_promoted_decision_lines),
            inspect.getsource(promoted_decision.show_promoted_decision_file),
            inspect.getsource(promoted_decision.read_csv_rows),
        ]
    )
    command_source = inspect.getsource(research_reports.run_show_promoted_decision_command)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in helper_source:
            add_failure(failures, f"show promoted-decision helpers should not reference {token}")
        if token in command_source:
            add_failure(failures, f"run_show_promoted_decision_command should not reference {token}")


def verify_missing_csv(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        missing_path = Path(temp_dir) / "promoted_decision_preview.csv"
        status_code, lines = show_promoted_decision_file(missing_path)
    output = "\n".join(lines)
    if status_code != 1:
        add_failure(failures, "missing CSV should return status code 1")
    for expected_text in [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "does not refresh data, read positions, or submit orders",
        "python bot.py --promoted-consensus-preview",
        "python bot.py --promoted-risk-preview",
        "python bot.py --promoted-decision-preview",
        "python bot.py --show-promoted-decision",
    ]:
        if expected_text not in output:
            add_failure(failures, f"missing CSV output missing expected text: {expected_text}")


def verify_normal_csv_display(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "promoted_decision_preview.csv"
        rows = [
            decision_row(
                "AAPL",
                "mixed_long_flat",
                "2",
                "1",
                "warning",
                "would_open_long,no_action_already_flat",
                "blocked_strategy_disagreement",
                "False",
                "Promoted strategies disagree; review before execution discussion.",
            ),
            decision_row(
                "MSFT",
                "unanimous_flat",
                "0",
                "3",
                "ok",
                "no_action_already_flat",
                "no_action_unanimous_flat",
                "False",
                "All promoted strategies desire flat; no action is implied.",
            ),
            decision_row(
                "SPY",
                "mixed_long_flat",
                "2",
                "1",
                "blocked_for_review",
                "would_open_long,would_close_long",
                "blocked_strategy_disagreement",
                "False",
                "Promoted strategies disagree; review before execution discussion.",
            ),
        ]
        with input_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=PROMOTED_DECISION_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        original_contents = input_path.read_text(encoding="utf-8")
        status_code, lines = show_promoted_decision_file(input_path)
        output = "\n".join(lines)
        after_contents = input_path.read_text(encoding="utf-8")

    if status_code != 0:
        add_failure(failures, "normal CSV display should return status code 0")
    if original_contents != after_contents:
        add_failure(failures, "show-promoted-decision should not modify the input CSV")
    for expected_text in [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "Rows: 3",
        "- blocked_strategy_disagreement: 2",
        "- no_action_unanimous_flat: 1",
        "- False: 3",
        "AAPL",
        "MSFT",
        "SPY",
        "blocked_strategy_disagreement",
        "no_action_unanimous_flat",
        "Execution approved: False for all rows.",
    ]:
        if expected_text not in output:
            add_failure(failures, f"display output missing expected text: {expected_text}")


def verify_execution_warning(failures: list[str]) -> None:
    lines = build_show_promoted_decision_lines(
        Path("data/promoted_decision_preview.csv"),
        [
            decision_row(
                "XYZ",
                "unanimous_long",
                "3",
                "0",
                "ok",
                "would_open_long",
                "research_only_unanimous_long",
                "True",
                "Fixture intentionally contains true execution approval for warning check.",
            )
        ],
    )
    output = "\n".join(lines)
    if "WARNING: at least one row has execution_approved=True; manual review required." not in output:
        add_failure(failures, "display should warn if any fixture row has execution_approved=True")


def verify_command_output_warning(failures: list[str]) -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        research_reports.run_show_promoted_decision_command()
    output = buffer.getvalue()
    first_line = output.splitlines()[0] if output.splitlines() else ""
    if first_line != "READ-ONLY DISPLAY. NOT EXECUTION.":
        add_failure(failures, "command output should start with the read-only warning")
    if "does not refresh data, read positions, or submit orders" not in output:
        add_failure(failures, "command output should include the no-refresh/no-order warning")


def main() -> int:
    failures: list[str] = []
    verify_no_forbidden_source_paths(failures)
    verify_missing_csv(failures)
    verify_normal_csv_display(failures)
    verify_execution_warning(failures)
    verify_command_output_warning(failures)

    if failures:
        print("Show promoted decision verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Show promoted decision verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
