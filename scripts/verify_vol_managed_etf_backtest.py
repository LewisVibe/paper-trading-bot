from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.vol_managed_etf as vol_lab
from trading_bot.research.costs import CostModel
from trading_bot.research.vol_managed_etf import (
    VOL_MANAGED_EQUITY_COLUMNS,
    VOL_MANAGED_ETF_UNIVERSE,
    VOL_MANAGED_GROSS_EXPOSURE_CAP,
    VOL_MANAGED_ITERATION_COLUMNS,
    VOL_MANAGED_RESULTS_COLUMNS,
    VOL_MANAGED_STRATEGY_NAME,
    VOL_MANAGED_TOP_N,
    VOL_MANAGED_TRADES_COLUMNS,
    VOL_MANAGED_VOL_WINDOW,
    build_and_write_vol_managed_etf_outputs,
)


FORBIDDEN_SOURCE_TERMS = [
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_simulated_positions",
    "decide_trade",
]


def main() -> int:
    failures: list[str] = []
    price_by_ticker = synthetic_etf_prices()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = build_and_write_vol_managed_etf_outputs(
            price_by_ticker=price_by_ticker,
            starting_cash=100_000.0,
            cost_model=CostModel(slippage_bps=Decimal("0")),
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )
        for path in [result.results_path, result.trades_path, result.equity_curve_path, result.iteration_log_path]:
            if not path.exists():
                failures.append(f"missing output file: {path.name}")
        verify_columns(result, failures)
        verify_result_rows(result.result_rows, failures)
        verify_monthly_rebalance_and_selection(result.trade_rows, result.equity_rows, failures)
        verify_no_leverage_or_shorting(result.trade_rows, result.equity_rows, failures)
        verify_iteration_log(result.iteration_rows, failures)
        verify_summary(result.summary_lines, failures)
    verify_static_safety(failures)

    if failures:
        print("Vol-managed ETF backtest verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Vol-managed ETF backtest verification passed.")
    return 0


def synthetic_etf_prices() -> dict[str, list[dict[str, float | str]]]:
    start = date(2024, 1, 1)
    rows_by_ticker: dict[str, list[dict[str, float | str]]] = {ticker: [] for ticker in VOL_MANAGED_ETF_UNIVERSE}
    slope_by_ticker = {
        "SPY": 0.08,
        "QQQ": 0.20,
        "IWM": 0.17,
        "DIA": 0.14,
        "XLK": 0.16,
        "XLF": 0.05,
        "XLE": 0.03,
        "XLV": 0.08,
        "XLY": 0.12,
        "XLP": 0.04,
        "XLI": 0.10,
        "XLU": 0.02,
        "TLT": -0.01,
        "GLD": 0.06,
    }
    for index in range(340):
        current_date = (start + timedelta(days=index)).isoformat()
        for ticker in VOL_MANAGED_ETF_UNIVERSE:
            close = 80.0 + index * slope_by_ticker[ticker]
            if 280 <= index < 310 and ticker == "SPY":
                close = 70.0
            rows_by_ticker[ticker].append({"date": current_date, "close": close})
    return rows_by_ticker


def verify_columns(result, failures: list[str]) -> None:
    with result.results_path.open(newline="", encoding="utf-8") as file:
        if csv.DictReader(file).fieldnames != VOL_MANAGED_RESULTS_COLUMNS:
            failures.append("vol-managed result columns changed unexpectedly")
    with result.trades_path.open(newline="", encoding="utf-8") as file:
        if csv.DictReader(file).fieldnames != VOL_MANAGED_TRADES_COLUMNS:
            failures.append("vol-managed trade columns changed unexpectedly")
    with result.equity_curve_path.open(newline="", encoding="utf-8") as file:
        if csv.DictReader(file).fieldnames != VOL_MANAGED_EQUITY_COLUMNS:
            failures.append("vol-managed equity columns changed unexpectedly")
    with result.iteration_log_path.open(newline="", encoding="utf-8") as file:
        if csv.DictReader(file).fieldnames != VOL_MANAGED_ITERATION_COLUMNS:
            failures.append("vol-managed iteration columns changed unexpectedly")


def verify_result_rows(result_rows: list[dict[str, object]], failures: list[str]) -> None:
    periods = {
        row["period"]
        for row in result_rows
        if row["strategy_name"] == VOL_MANAGED_STRATEGY_NAME
    }
    if periods != {"full_period", "in_sample", "out_of_sample"}:
        failures.append(f"vol-managed period rows changed unexpectedly: {sorted(periods)}")
    for row in result_rows:
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"safety flags failed for {row['strategy_name']} {row['period']}")
        if row["realised_vol_window"] != VOL_MANAGED_VOL_WINDOW:
            failures.append("realised_vol_window should be visible on every result row")
        if row["gross_exposure_cap"] != VOL_MANAGED_GROSS_EXPOSURE_CAP:
            failures.append("gross_exposure_cap should be visible on every result row")


def verify_monthly_rebalance_and_selection(
    trade_rows: list[dict[str, object]],
    equity_rows: list[dict[str, object]],
    failures: list[str],
) -> None:
    if not trade_rows:
        failures.append("expected deterministic vol-managed trades")
        return
    trade_months = {str(row["date"])[:7] for row in trade_rows}
    if len(trade_months) < 2:
        failures.append("expected monthly rebalance trades across more than one month")
    for row in trade_rows:
        if row["side"] not in {"buy", "sell"}:
            failures.append("vol-managed ETF lab should only create long buy/sell research trades")
        if row["side"] == "buy" and str(row["ticker"]) not in {"QQQ", "IWM", "XLK"}:
            failures.append(f"unexpected selected ticker for deterministic momentum fixture: {row['ticker']}")
        if float(row["target_weight"]) < 0:
            failures.append("target weights should never be negative")

    if not any(str(row["selected_tickers"]) == "" for row in equity_rows):
        failures.append("strategy should hold cash when SPY regime is not eligible")


def verify_no_leverage_or_shorting(
    trade_rows: list[dict[str, object]],
    equity_rows: list[dict[str, object]],
    failures: list[str],
) -> None:
    for row in equity_rows:
        if float(row["gross_exposure_pct"]) > 100.0001:
            failures.append("gross exposure should be capped at 100%")
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append("equity rows should remain research-only and non-execution")
    for row in trade_rows:
        if str(row["side"]) in {"sell_short", "buy_to_cover", "short"}:
            failures.append("vol-managed ETF lab must not add shorting")
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append("trade rows should remain research-only and non-execution")


def verify_iteration_log(iteration_rows: list[dict[str, object]], failures: list[str]) -> None:
    if len(iteration_rows) != 1:
        failures.append("expected exactly one controlled vol-managed ETF iteration")
        return
    row = iteration_rows[0]
    for expected in ["top_N=3", "63-day", "10% target volatility", "gross exposure capped at 1.0"]:
        if expected not in str(row["allowed_parameter_set"]):
            failures.append(f"iteration log missing fixed parameter: {expected}")
    if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
        failures.append("iteration log should remain research-only and non-execution")


def verify_summary(summary_lines: list[str], failures: list[str]) -> None:
    summary = "\n".join(summary_lines)
    if "VOL-MANAGED ETF BACKTEST. RESEARCH ONLY. NOT EXECUTION." not in summary:
        failures.append("summary should clearly mark the lab research-only")
    if VOL_MANAGED_STRATEGY_NAME not in summary:
        failures.append("summary should name the strategy")
    if "not execution approval" not in summary:
        failures.append("summary should deny execution approval")


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--vol-managed-etf-backtest" not in help_text:
        failures.append("command inventory should include --vol-managed-etf-backtest")

    source = inspect.getsource(vol_lab)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"vol-managed ETF module references forbidden execution term: {term}")
    lowered = source.lower()
    for forbidden in ["sell_short", "buy_to_cover"]:
        if forbidden in lowered:
            failures.append(f"vol-managed ETF module should not add {forbidden}")


if __name__ == "__main__":
    raise SystemExit(main())
