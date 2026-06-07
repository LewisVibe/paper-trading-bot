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

import trading_bot.research.short_strategy_lab as short_lab
from trading_bot.research.costs import CostModel
from trading_bot.research.short_strategy_lab import (
    SHORT_STRATEGY_BORROW_FEE_BPS_ANNUAL,
    SHORT_STRATEGY_BORROW_FEE_STATUS,
    SHORT_STRATEGY_EQUITY_COLUMNS,
    SHORT_STRATEGY_NAME,
    SHORT_STRATEGY_RESULTS_COLUMNS,
    SHORT_STRATEGY_TOP_N,
    SHORT_STRATEGY_TRADES_COLUMNS,
    SHORT_STRATEGY_UNIVERSE,
    build_and_write_short_strategy_lab_outputs,
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

DANGEROUS_SHORT_COMMANDS = [
    "--execute-short",
    "--short-execution",
    "--short-paper",
    "--short-selling-execute",
    "--crypto-short",
]


def main() -> int:
    failures: list[str] = []
    price_by_ticker = synthetic_etf_prices()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = build_and_write_short_strategy_lab_outputs(
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
        verify_result_rows(result.result_rows, result.trade_rows, failures)
        verify_trade_rules(result.trade_rows, failures)
        verify_equity_rules(result.equity_rows, failures)
        verify_iteration_log(result.iteration_rows, failures)
        verify_summary(result.summary_lines, failures)

    verify_static_safety(failures)

    if failures:
        print("Short strategy lab verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Short strategy lab verification passed.")
    return 0


def synthetic_etf_prices() -> dict[str, list[dict[str, float | str]]]:
    start = date(2024, 1, 1)
    rows_by_ticker: dict[str, list[dict[str, float | str]]] = {ticker: [] for ticker in SHORT_STRATEGY_UNIVERSE}
    post_200_prices = {
        "SPY": 90.0,
        "QQQ": 82.0,
        "IWM": 72.0,
        "DIA": 94.0,
        "XLF": 96.0,
        "XLK": 98.0,
        "XLY": 97.0,
        "XLE": 99.0,
        "XLI": 95.0,
        "XLU": 98.5,
    }
    for index in range(300):
        current_date = (start + timedelta(days=index)).isoformat()
        for ticker in SHORT_STRATEGY_UNIVERSE:
            if index < 200:
                close = 100.0
            elif index < 260:
                close = post_200_prices[ticker]
            else:
                close = 112.0 if ticker == "SPY" else 110.0
            rows_by_ticker[ticker].append({"date": current_date, "close": close})
    return rows_by_ticker


def verify_columns(result, failures: list[str]) -> None:
    with result.results_path.open(newline="", encoding="utf-8") as file:
        if csv.DictReader(file).fieldnames != SHORT_STRATEGY_RESULTS_COLUMNS:
            failures.append("short strategy result columns changed unexpectedly")
    with result.trades_path.open(newline="", encoding="utf-8") as file:
        if csv.DictReader(file).fieldnames != SHORT_STRATEGY_TRADES_COLUMNS:
            failures.append("short strategy trade columns changed unexpectedly")
    with result.equity_curve_path.open(newline="", encoding="utf-8") as file:
        if csv.DictReader(file).fieldnames != SHORT_STRATEGY_EQUITY_COLUMNS:
            failures.append("short strategy equity columns changed unexpectedly")


def verify_result_rows(
    result_rows: list[dict[str, object]],
    trade_rows: list[dict[str, object]],
    failures: list[str],
) -> None:
    periods = {
        row["period"]
        for row in result_rows
        if row["strategy_name"] == SHORT_STRATEGY_NAME
    }
    if periods != {"full_period", "in_sample", "out_of_sample"}:
        failures.append(f"short strategy period rows changed unexpectedly: {sorted(periods)}")

    for row in result_rows:
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"safety flags failed for {row['strategy_name']} {row['period']}")
        if row["borrow_fee_bps_annual"] != SHORT_STRATEGY_BORROW_FEE_BPS_ANNUAL:
            failures.append("borrow_fee_bps_annual should be visible on every result row")
        if row["borrow_fee_model_status"] != SHORT_STRATEGY_BORROW_FEE_STATUS:
            failures.append("borrow_fee_model_status should be visible on every result row")

    full = result_row(result_rows, SHORT_STRATEGY_NAME, "full_period")
    if full and int(full["number_of_trades"]) != len(trade_rows):
        failures.append("short strategy full-period trade count should match synthetic trade rows")
    cash = result_row(result_rows, "cash_flat_baseline", "full_period")
    if cash and int(cash["number_of_trades"]) != 0:
        failures.append("cash baseline should have zero trades")
    buy_hold = result_row(result_rows, "spy_buy_and_hold_baseline", "full_period")
    if buy_hold and int(buy_hold["number_of_trades"]) != 1:
        failures.append("SPY buy-and-hold baseline should use one-entry convention")


def verify_trade_rules(trade_rows: list[dict[str, object]], failures: list[str]) -> None:
    if not trade_rows:
        failures.append("expected deterministic short strategy trades")
        return
    sell_rows = [row for row in trade_rows if row["side"] == "sell_short"]
    if not sell_rows:
        failures.append("expected at least one synthetic short entry")
        return
    first_sell_date = str(sell_rows[0]["date"])
    first_sell_tickers = sorted(str(row["ticker"]) for row in sell_rows if row["date"] == first_sell_date)
    if first_sell_tickers != ["IWM", "QQQ"]:
        failures.append(f"weakest-N selection should be deterministic, got {first_sell_tickers}")

    open_tickers: set[str] = set()
    for row in trade_rows:
        if row["side"] == "sell_short":
            if float(row["spy_close"]) >= float(row["spy_sma_200"]):
                failures.append("short entries should occur only when SPY is below SMA200")
            if float(row["ticker_close"]) >= float(row["ticker_sma_200"]):
                failures.append("short entries should occur only when ticker is below SMA200")
            if row["ticker"] in open_tickers:
                failures.append("strategy should not pyramid an already open synthetic short")
            open_tickers.add(str(row["ticker"]))
        elif row["side"] == "buy_to_cover":
            open_tickers.discard(str(row["ticker"]))
        else:
            failures.append(f"unexpected trade side: {row['side']}")
        if row["side"] not in {"sell_short", "buy_to_cover"}:
            failures.append("short strategy lab should not create long entries")
        if row["borrow_fee_model_status"] != SHORT_STRATEGY_BORROW_FEE_STATUS:
            failures.append("borrow fee status should be explicit on every trade")


def verify_equity_rules(equity_rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in equity_rows:
        if row["strategy_name"] != SHORT_STRATEGY_NAME:
            continue
        if float(row["gross_short_exposure_pct"]) > 101.0:
            failures.append("gross short exposure should stay near or below 1x in deterministic fixture")
        if int(row["open_short_count"]) > SHORT_STRATEGY_TOP_N:
            failures.append("open short count should not exceed weakest_N")
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append("equity rows should remain research-only and non-execution")


def verify_iteration_log(iteration_rows: list[dict[str, object]], failures: list[str]) -> None:
    if len(iteration_rows) != 1:
        failures.append("short strategy lab should record exactly one controlled iteration")
        return
    row = iteration_rows[0]
    if row["strategy_name"] != SHORT_STRATEGY_NAME:
        failures.append("iteration log should record the approved short strategy name")
    for expected in ["weakest_N=2", "126-day", "SMA200", "borrow_fee_bps_annual=300"]:
        if expected not in str(row["allowed_parameter_set"]):
            failures.append(f"iteration log missing fixed parameter: {expected}")
    if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
        failures.append("iteration log should remain research-only and non-execution")


def verify_summary(summary_lines: list[str], failures: list[str]) -> None:
    summary = "\n".join(summary_lines)
    if "SHORT STRATEGY LAB. RESEARCH ONLY. NOT EXECUTION." not in summary:
        failures.append("summary should clearly mark the lab research-only")
    if "research_weak_etf_short_momentum" not in summary:
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
    if "--short-strategy-lab" not in help_text:
        failures.append("command inventory should include --short-strategy-lab")
    for command in DANGEROUS_SHORT_COMMANDS:
        if command in help_text:
            failures.append(f"short execution command should not exist: {command}")

    config_source = (ROOT / "trading_bot" / "config.py").read_text(encoding="utf-8")
    if 'parse_config_bool(raw, "allow_shorting", False)' not in config_source:
        failures.append("allow_shorting should still default to false")

    source = inspect.getsource(short_lab)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"short strategy lab references forbidden execution term: {term}")
    if "crypto" in source.lower():
        failures.append("short strategy lab should not add crypto shorting")


def result_row(rows: list[dict[str, object]], strategy_name: str, period: str) -> dict[str, object] | None:
    return next(
        (row for row in rows if row["strategy_name"] == strategy_name and row["period"] == period),
        None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
