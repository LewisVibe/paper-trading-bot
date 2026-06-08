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

from trading_bot.research import promoted_risk
from trading_bot.research.promoted_risk import (
    PROMOTED_RISK_COLUMNS,
    build_show_promoted_risk_lines,
    show_promoted_risk_file,
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
    "submit_alpaca_order",
    "init_database",
    "sqlite3",
]


def risk_row(
    strategy_name: str,
    ticker: str,
    desired_position: str,
    current_position: str,
    preview_action: str,
    risk_check: str,
    risk_status: str,
    risk_reason: str,
    latest_close: str = "100",
    assumed_quantity: str = "1",
    estimated_desired_notional: str = "100",
) -> dict[str, str]:
    return {
        "created_at": "2026-06-06T00:00:00Z",
        "strategy_name": strategy_name,
        "ticker": ticker,
        "desired_position": desired_position,
        "current_position": current_position,
        "preview_action": preview_action,
        "latest_close": latest_close,
        "assumed_quantity": assumed_quantity,
        "estimated_desired_notional": estimated_desired_notional,
        "risk_check": risk_check,
        "risk_status": risk_status,
        "risk_reason": risk_reason,
        "research_only": "True",
        "preview_only": "True",
    }


def add_failure(failures: list[str], message: str) -> None:
    failures.append(message)


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = "\n".join(
        [
            inspect.getsource(promoted_risk.build_show_promoted_risk_lines),
            inspect.getsource(promoted_risk.build_missing_promoted_risk_lines),
            inspect.getsource(promoted_risk.show_promoted_risk_file),
            inspect.getsource(promoted_risk.read_csv_rows),
        ]
    )
    command_source = inspect.getsource(research_reports.run_show_promoted_risk_command)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in helper_source:
            add_failure(failures, f"show promoted-risk helpers should not reference {token}")
        if token in command_source:
            add_failure(failures, f"run_show_promoted_risk_command should not reference {token}")


def verify_missing_csv(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        missing_path = Path(temp_dir) / "promoted_risk_preview.csv"
        status_code, lines = show_promoted_risk_file(missing_path)
    output = "\n".join(lines)
    if status_code != 1:
        add_failure(failures, "missing CSV should return status code 1")
    if "READ-ONLY DISPLAY. NOT EXECUTION." not in output:
        add_failure(failures, "missing CSV output should include the read-only warning")
    if "python bot.py --promoted-risk-preview" not in output:
        add_failure(failures, "missing CSV output should instruct user to run promoted-risk-preview first")


def verify_normal_csv_display(failures: list[str]) -> None:
    long_reason = (
        "Current position data is unavailable; do not assume flat. "
        "This deliberately long reason should be truncated in the table but remain readable in the warning summary."
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "promoted_risk_preview.csv"
        rows = [
            risk_row(
                "sma_50_200_trend",
                "AAPL",
                "long",
                "long",
                "no_action_already_long",
                "max_open_positions",
                "ok",
                "Strategy wants 2 long position(s), within the conservative limit of 2.",
                "250.5",
                "1",
                "250.5",
            ),
            risk_row(
                "buy_above_200_exit_below_200",
                "AAPL",
                "long",
                "flat",
                "would_open_long",
                "duplicate_ticker_exposure",
                "warning",
                "AAPL is desired long by 2 promoted strategy rows.",
                "250.5",
                "1",
                "250.5",
            ),
            risk_row(
                "fifty_two_week_high_breakout",
                "MSFT",
                "flat",
                "unavailable",
                "position_unavailable",
                "position_availability",
                "blocked_for_review",
                long_reason,
                "300",
                "1",
                "0",
            ),
        ]
        with input_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=PROMOTED_RISK_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        original_contents = input_path.read_text(encoding="utf-8")

        status_code, lines = show_promoted_risk_file(input_path)
        output = "\n".join(lines)
        after_contents = input_path.read_text(encoding="utf-8")

    if status_code != 0:
        add_failure(failures, "normal CSV display should return status code 0")
    if original_contents != after_contents:
        add_failure(failures, "show-promoted-risk should not modify the input CSV")
    for expected_text in [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "does not refresh market data, read positions, or submit orders",
        "Rows: 3",
        "- ok: 1",
        "- warning: 1",
        "- blocked_for_review: 1",
        "- max_open_positions: 1",
        "- duplicate_ticker_exposure: 1",
        "- position_availability: 1",
        "- long: 2",
        "- flat: 1",
        "Estimated desired notional by strategy:",
        "- buy_above_200_exit_below_200: $250.50",
        "- fifty_two_week_high_breakout: $0.00",
        "- sma_50_200_trend: $250.50",
        "Estimated duplicated desired notional by ticker:",
        "- AAPL: $501.00",
        "- MSFT: $0.00",
        "Estimated unique desired notional by ticker:",
        "- AAPL: $250.50",
        "Estimated unique account-style desired notional total: $250.50",
        "Blocked-for-review rows: 1",
        "Warning rows: 1",
        "sma_50_200_trend",
        "fifty_two_week_high_breakout",
        "blocked_for_review",
        "Current position data is unavailable",
    ]:
        if expected_text not in output:
            add_failure(failures, f"display output missing expected text: {expected_text}")


def verify_line_builder(failures: list[str]) -> None:
    lines = build_show_promoted_risk_lines(
        Path("data/promoted_risk_preview.csv"),
        [
            risk_row(
                "unavailable_case",
                "ZZZ",
                "long",
                "unavailable",
                "position_unavailable",
                "position_availability",
                "blocked_for_review",
                "Current position data is unavailable; do not assume flat.",
                "100",
                "1",
                "100",
            )
        ],
    )
    output = "\n".join(lines)
    if "Blocked-for-review rows: 1" not in output:
        add_failure(failures, "line builder should summarize blocked_for_review rows")
    if "position_unavailable" not in output:
        add_failure(failures, "line builder should preserve position_unavailable context")
    if "Estimated desired notional by strategy:" not in output:
        add_failure(failures, "line builder should include strategy notional estimates")
    if "Estimated duplicated desired notional by ticker:" not in output:
        add_failure(failures, "line builder should include duplicated ticker notional estimates")
    if "Estimated unique desired notional by ticker:" not in output:
        add_failure(failures, "line builder should include unique ticker notional estimates")
    if "Estimated unique account-style desired notional total:" not in output:
        add_failure(failures, "line builder should include unique account-style total")


def verify_command_output_warning(failures: list[str]) -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        research_reports.run_show_promoted_risk_command()
    output = buffer.getvalue()
    first_line = output.splitlines()[0] if output.splitlines() else ""
    if first_line != "READ-ONLY DISPLAY. NOT EXECUTION.":
        add_failure(failures, "command output should start with the read-only warning")
    if "does not refresh market data, read positions, or submit orders" not in output:
        add_failure(failures, "command output should include the no-refresh/no-order warning")


def main() -> int:
    failures: list[str] = []
    verify_no_forbidden_source_paths(failures)
    verify_missing_csv(failures)
    verify_normal_csv_display(failures)
    verify_line_builder(failures)
    verify_command_output_warning(failures)

    if failures:
        print("Show promoted risk verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Show promoted risk verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
