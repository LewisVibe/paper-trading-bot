from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bot
from trading_bot.research import promoted_consensus
from trading_bot.research.promoted_consensus import (
    PROMOTED_CONSENSUS_COLUMNS,
    build_promoted_consensus_rows,
    run_promoted_consensus_preview_files,
)


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


def preview_row(strategy_name: str, ticker: str, desired_position: str) -> dict[str, str]:
    return {
        "strategy_name": strategy_name,
        "ticker": ticker,
        "desired_position": desired_position,
    }


def add_failure(failures: list[str], message: str) -> None:
    failures.append(message)


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = inspect.getsource(promoted_consensus)
    command_source = inspect.getsource(bot.run_promoted_consensus_preview)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in helper_source:
            add_failure(failures, f"promoted consensus helper should not reference {token}")
        if token in command_source:
            add_failure(failures, f"run_promoted_consensus_preview should not reference {token}")


def verify_rows(failures: list[str]) -> None:
    rows = build_promoted_consensus_rows(
        [
            preview_row("sma_50_200_trend", "AAA", "long"),
            preview_row("buy_above_200_exit_below_200", "AAA", "long"),
            preview_row("sma_50_200_trend", "BBB", "flat"),
            preview_row("fifty_two_week_high_breakout", "BBB", "flat"),
            preview_row("sma_50_200_trend", "CCC", "long"),
            preview_row("fifty_two_week_high_breakout", "CCC", "flat"),
            preview_row("unknown_strategy", "DDD", "watch"),
        ],
        created_at="2026-06-06T00:00:00Z",
    )
    by_ticker = {row["ticker"]: row for row in rows}
    expected_states = {
        "AAA": "unanimous_long",
        "BBB": "unanimous_flat",
        "CCC": "mixed_long_flat",
        "DDD": "no_supported_votes",
    }
    for ticker, state in expected_states.items():
        if by_ticker[ticker]["consensus_state"] != state:
            add_failure(failures, f"{ticker} expected {state}, got {by_ticker[ticker]['consensus_state']}")
    if by_ticker["AAA"]["long_votes"] != 2:
        add_failure(failures, "unanimous_long ticker should count long votes")
    if by_ticker["BBB"]["flat_votes"] != 2:
        add_failure(failures, "unanimous_flat ticker should count flat votes")
    if by_ticker["CCC"]["strategies_long"] != "sma_50_200_trend":
        add_failure(failures, "mixed ticker should list long strategies")
    if by_ticker["CCC"]["strategies_flat"] != "fifty_two_week_high_breakout":
        add_failure(failures, "mixed ticker should list flat strategies")
    if any(row.get("execution_eligible") is not False for row in rows):
        add_failure(failures, "execution_eligible should be False for every row")
    if any(row.get("research_only") is not True or row.get("preview_only") is not True for row in rows):
        add_failure(failures, "all consensus rows should be research_only and preview_only")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def verify_file_runner(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        missing_preview = temp_path / "missing_promoted_strategy_preview.csv"
        output_path = temp_path / "promoted_consensus_preview.csv"
        status_code, lines = run_promoted_consensus_preview_files(missing_preview, output_path)
        if status_code != 1:
            add_failure(failures, "missing preview input should return status code 1")
        if output_path.exists():
            add_failure(failures, "missing preview input should not create output CSV")
        if "python bot.py --preview-promoted-strategies" not in "\n".join(lines):
            add_failure(failures, "missing input output should tell user how to create preview CSV")

        preview_path = temp_path / "promoted_strategy_preview.csv"
        write_csv(
            preview_path,
            ["strategy_name", "ticker", "desired_position"],
            [
                preview_row("sma_50_200_trend", "AAA", "long"),
                preview_row("buy_above_200_exit_below_200", "AAA", "long"),
                preview_row("sma_50_200_trend", "BBB", "flat"),
                preview_row("fifty_two_week_high_breakout", "BBB", "flat"),
                preview_row("sma_50_200_trend", "CCC", "long"),
                preview_row("fifty_two_week_high_breakout", "CCC", "flat"),
            ],
        )
        status_code, lines = run_promoted_consensus_preview_files(preview_path, output_path)
        if status_code != 0:
            add_failure(failures, "valid consensus preview inputs should return status code 0")
        if not output_path.exists():
            add_failure(failures, "valid consensus preview should create output CSV")
            return
        with output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            output_rows = list(reader)
            if reader.fieldnames != PROMOTED_CONSENSUS_COLUMNS:
                add_failure(failures, "consensus output columns changed unexpectedly")
        if len(output_rows) != 3:
            add_failure(failures, "consensus output should contain one row per ticker")
        if any(row.get("execution_eligible") != "False" for row in output_rows):
            add_failure(failures, "output CSV should mark every row execution_eligible=False")
        if any(row.get("research_only") != "True" or row.get("preview_only") != "True" for row in output_rows):
            add_failure(failures, "output CSV should mark every row research_only=True and preview_only=True")
        summary = "\n".join(lines)
        for expected_text in [
            "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION.",
            "Rows: 3",
            "mixed_long_flat=1",
            "unanimous_flat=1",
            "unanimous_long=1",
            "Tickers with disagreement: CCC",
            "Tickers unanimous long: AAA",
            "Tickers unanimous flat: BBB",
            "Saved promoted consensus preview",
        ]:
            if expected_text not in summary:
                add_failure(failures, f"summary missing expected text: {expected_text}")


def main() -> int:
    failures: list[str] = []
    verify_no_forbidden_source_paths(failures)
    verify_rows(failures)
    verify_file_runner(failures)

    if failures:
        print("Promoted consensus preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Promoted consensus preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
