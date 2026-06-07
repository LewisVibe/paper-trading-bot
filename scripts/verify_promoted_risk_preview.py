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
from trading_bot.research import promoted_risk
from trading_bot.research.promoted_risk import (
    PROMOTED_RISK_COLUMNS,
    build_promoted_risk_rows,
    run_promoted_risk_preview_files,
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


def preview_row(
    strategy_name: str,
    ticker: str,
    desired_position: str,
    latest_close: str = "100",
) -> dict[str, str]:
    return {
        "strategy_name": strategy_name,
        "ticker": ticker,
        "desired_position": desired_position,
        "latest_close": latest_close,
    }


def action_row(
    strategy_name: str,
    ticker: str,
    current_position: str,
    preview_action: str,
) -> dict[str, str]:
    return {
        "strategy_name": strategy_name,
        "ticker": ticker,
        "current_position": current_position,
        "preview_action": preview_action,
    }


def add_failure(failures: list[str], message: str) -> None:
    failures.append(message)


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = inspect.getsource(promoted_risk)
    command_source = inspect.getsource(bot.run_promoted_risk_preview)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in helper_source:
            add_failure(failures, f"promoted risk helper should not reference {token}")
        if token in command_source:
            add_failure(failures, f"run_promoted_risk_preview should not reference {token}")


def verify_rows(failures: list[str]) -> None:
    preview_rows = [
        preview_row("sma_50_200_trend", "AAPL", "long"),
        preview_row("sma_50_200_trend", "MSFT", "long"),
        preview_row("sma_50_200_trend", "SPY", "long"),
        preview_row("buy_above_200_exit_below_200", "AAPL", "long"),
        preview_row("fifty_two_week_high_breakout", "MSFT", "flat"),
        preview_row("bad_price_strategy", "BAD", "long", "not-a-number"),
        preview_row("missing_price_strategy", "MISS", "long", ""),
    ]
    action_rows = [
        action_row("sma_50_200_trend", "AAPL", "long", "no_action_already_long"),
        action_row("sma_50_200_trend", "MSFT", "unavailable", "position_unavailable"),
        action_row("sma_50_200_trend", "SPY", "flat", "would_open_long"),
        action_row("buy_above_200_exit_below_200", "AAPL", "flat", "would_open_long"),
        action_row("fifty_two_week_high_breakout", "MSFT", "flat", "no_action_already_flat"),
        action_row("bad_price_strategy", "BAD", "flat", "would_open_long"),
        action_row("missing_price_strategy", "MISS", "flat", "would_open_long"),
    ]
    rows = build_promoted_risk_rows(
        preview_rows,
        action_rows,
        max_open_positions=2,
        created_at="2026-06-06T00:00:00Z",
    )
    if not rows:
        add_failure(failures, "risk rows should be created")
        return
    if any(row.get("research_only") is not True or row.get("preview_only") is not True for row in rows):
        add_failure(failures, "all risk rows should be research_only and preview_only")

    statuses_by_check = {(row["strategy_name"], row["ticker"], row["risk_check"]): row["risk_status"] for row in rows}
    if statuses_by_check.get(("sma_50_200_trend", "AAPL", "max_open_positions")) != "blocked_for_review":
        add_failure(failures, "max_open_positions breach should be blocked_for_review")
    if statuses_by_check.get(("sma_50_200_trend", "AAPL", "duplicate_ticker_exposure")) != "warning":
        add_failure(failures, "duplicate ticker exposure should be warning")
    if statuses_by_check.get(("buy_above_200_exit_below_200", "AAPL", "concentration_risk")) != "warning":
        add_failure(failures, "concentration risk should be warning")
    if statuses_by_check.get(("sma_50_200_trend", "MSFT", "position_availability")) != "blocked_for_review":
        add_failure(failures, "position_unavailable should be blocked_for_review")
    if statuses_by_check.get(("bad_price_strategy", "BAD", "notional_data_quality")) != "blocked_for_review":
        add_failure(failures, "malformed latest_close should be blocked_for_review")
    if statuses_by_check.get(("missing_price_strategy", "MISS", "notional_data_quality")) != "blocked_for_review":
        add_failure(failures, "missing latest_close should be blocked_for_review")

    rows_by_key = {(row["strategy_name"], row["ticker"], row["risk_check"]): row for row in rows}
    long_notional_row = rows_by_key[("sma_50_200_trend", "AAPL", "notional_data_quality")]
    flat_notional_row = rows_by_key[("fifty_two_week_high_breakout", "MSFT", "notional_data_quality")]
    bad_notional_row = rows_by_key[("bad_price_strategy", "BAD", "notional_data_quality")]
    if long_notional_row["latest_close"] != "100":
        add_failure(failures, "latest_close should be copied from saved promoted strategy preview data")
    if long_notional_row["assumed_quantity"] != "1":
        add_failure(failures, "assumed_quantity should default to 1")
    if long_notional_row["estimated_desired_notional"] != "100":
        add_failure(failures, "desired long notional should equal latest_close * assumed_quantity")
    if flat_notional_row["estimated_desired_notional"] != "0":
        add_failure(failures, "desired flat notional should be zero")
    if bad_notional_row["estimated_desired_notional"] != "":
        add_failure(failures, "malformed latest_close should not produce a notional estimate")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def verify_file_runner(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        missing_preview = temp_path / "missing_promoted_strategy_preview.csv"
        action_path = temp_path / "promoted_strategy_action_preview.csv"
        output_path = temp_path / "promoted_risk_preview.csv"
        status_code, lines = run_promoted_risk_preview_files(missing_preview, action_path, output_path)
        if status_code != 1:
            add_failure(failures, "missing preview input should return status code 1")
        if output_path.exists():
            add_failure(failures, "missing preview input should not create output CSV")
        if "python bot.py --preview-promoted-strategies" not in "\n".join(lines):
            add_failure(failures, "missing input output should tell user how to create preview CSV")

        preview_path = temp_path / "promoted_strategy_preview.csv"
        write_csv(
            preview_path,
            ["strategy_name", "ticker", "desired_position", "latest_close"],
            [
                preview_row("sma_50_200_trend", "AAPL", "long", "250.50"),
                preview_row("buy_above_200_exit_below_200", "AAPL", "long", "250.50"),
                preview_row("fifty_two_week_high_breakout", "MSFT", "flat", "300"),
            ],
        )
        write_csv(
            action_path,
            ["strategy_name", "ticker", "current_position", "preview_action"],
            [
                action_row("sma_50_200_trend", "AAPL", "unavailable", "position_unavailable"),
                action_row("buy_above_200_exit_below_200", "AAPL", "flat", "would_open_long"),
                action_row("fifty_two_week_high_breakout", "MSFT", "flat", "no_action_already_flat"),
            ],
        )
        status_code, lines = run_promoted_risk_preview_files(preview_path, action_path, output_path)
        if status_code != 0:
            add_failure(failures, "valid risk preview inputs should return status code 0")
        if not output_path.exists():
            add_failure(failures, "valid risk preview should create output CSV")
            return

        with output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            output_rows = list(reader)
            if reader.fieldnames != PROMOTED_RISK_COLUMNS:
                add_failure(failures, "risk preview output columns changed unexpectedly")
        if not output_rows:
            add_failure(failures, "risk preview output should contain rows")
        if any(row.get("research_only") != "True" or row.get("preview_only") != "True" for row in output_rows):
            add_failure(failures, "output CSV should mark every row research_only=True and preview_only=True")
        notional_rows = [row for row in output_rows if row.get("risk_check") == "notional_data_quality"]
        if notional_rows[0].get("latest_close") != "250.5":
            add_failure(failures, "output CSV should include parsed latest_close")
        if notional_rows[0].get("assumed_quantity") != "1":
            add_failure(failures, "output CSV should include assumed_quantity")
        if notional_rows[0].get("estimated_desired_notional") != "250.5":
            add_failure(failures, "output CSV should include estimated desired notional")
        flat_rows = [
            row
            for row in notional_rows
            if row.get("strategy_name") == "fifty_two_week_high_breakout"
        ]
        if not flat_rows or flat_rows[0].get("estimated_desired_notional") != "0":
            add_failure(failures, "flat rows should have zero estimated desired notional")
        summary = "\n".join(lines)
        if "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION." not in summary:
            add_failure(failures, "terminal summary should include research-only warning")
        if "Estimated desired notional by strategy" not in summary:
            add_failure(failures, "terminal summary should include strategy notional estimate")
        if "Estimated duplicated desired notional by ticker" not in summary:
            add_failure(failures, "terminal summary should include duplicated ticker notional estimate")
        if "Estimated unique desired notional by ticker" not in summary:
            add_failure(failures, "terminal summary should include unique ticker notional estimate")
        if "Estimated unique account-style desired notional total" not in summary:
            add_failure(failures, "terminal summary should include unique account-style notional total")
        if "Saved promoted risk preview" not in summary:
            add_failure(failures, "terminal summary should include output path")


def main() -> int:
    failures: list[str] = []
    verify_no_forbidden_source_paths(failures)
    verify_rows(failures)
    verify_file_runner(failures)

    if failures:
        print("Promoted risk preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Promoted risk preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
