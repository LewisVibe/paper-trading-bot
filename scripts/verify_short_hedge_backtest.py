from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.short_hedge as short_hedge
from trading_bot.research.costs import CostModel
from trading_bot.research.short_hedge import (
    SHORT_HEDGE_BORROW_FEE_STATUS,
    SHORT_HEDGE_RESULTS_COLUMNS,
    SHORT_HEDGE_STRATEGY_NAME,
    build_and_write_short_hedge_outputs,
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
    price_rows = synthetic_spy_rows()

    with tempfile.TemporaryDirectory() as tmpdir:
        result = build_and_write_short_hedge_outputs(
            price_rows=price_rows,
            starting_cash=100_000.0,
            cost_model=CostModel(slippage_bps=Decimal("0")),
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )

        for path in [result.results_path, result.trades_path, result.equity_curve_path]:
            if not path.exists():
                failures.append(f"missing output file: {path.name}")

        if not result.result_rows:
            failures.append("short hedge result rows were not produced")
        periods = {
            row["period"]
            for row in result.result_rows
            if row["strategy_name"] == SHORT_HEDGE_STRATEGY_NAME
        }
        if periods != {"full_period", "in_sample", "out_of_sample"}:
            failures.append(f"short hedge period rows changed unexpectedly: {sorted(periods)}")

        with result.results_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != SHORT_HEDGE_RESULTS_COLUMNS:
                failures.append("short hedge result columns changed unexpectedly")

        for row in result.result_rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"safety flags failed for {row['strategy_name']} {row['period']}")
            if row["borrow_fee_model_status"] != SHORT_HEDGE_BORROW_FEE_STATUS:
                failures.append("borrow fee model status should be explicit on every result row")

        verify_trade_rules(result.trade_rows, result.equity_rows, failures)
        verify_no_pyramiding_or_leverage(result.trade_rows, failures)
        verify_result_trade_counts(result.result_rows, result.trade_rows, failures)
        verify_research_conclusions(result.result_rows, failures)
        verify_summary(result.summary_lines, failures)

    verify_static_safety(failures)

    if failures:
        print("Short hedge backtest verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Short hedge backtest verification passed.")
    return 0


def synthetic_spy_rows() -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    prices = [100.0] * 200 + [90.0, 85.0, 80.0] + [105.0] * 10 + [110.0] * 47
    for index, close in enumerate(prices, start=1):
        rows.append({"date": f"2024-01-{index:03d}", "close": close})
    return rows


def verify_trade_rules(
    trade_rows: list[dict[str, object]],
    equity_rows: list[dict[str, object]],
    failures: list[str],
) -> None:
    if not trade_rows:
        failures.append("expected at least one synthetic short hedge trade")
        return

    equity_by_date = {str(row["date"]): row for row in equity_rows}
    for trade in trade_rows:
        date = str(trade["date"])
        equity_row = equity_by_date.get(date)
        if not equity_row:
            failures.append(f"missing equity row for trade date {date}")
            continue
        close = float(equity_row["close"])
        sma_200 = float(equity_row["sma_200"])
        side = str(trade["side"])
        if side == "sell_short" and not close < sma_200:
            failures.append("short entry should occur only when close is below SMA200")
        if side == "buy_to_cover" and not close >= sma_200:
            failures.append("short exit should occur only when close is at or above SMA200")
        if trade["borrow_fee_model_status"] != SHORT_HEDGE_BORROW_FEE_STATUS:
            failures.append("borrow fee model status should be explicit on every trade")

    if [row["side"] for row in trade_rows] != ["sell_short", "buy_to_cover"]:
        failures.append("synthetic scenario should open one short and close one short")


def verify_no_pyramiding_or_leverage(trade_rows: list[dict[str, object]], failures: list[str]) -> None:
    open_short = False
    for trade in trade_rows:
        side = str(trade["side"])
        if side == "sell_short":
            if open_short:
                failures.append("short hedge should not pyramid while already short")
            open_short = True
            if float(trade["notional"]) > 100_000.01:
                failures.append("short hedge should not exceed 1x starting notional in the deterministic test")
        elif side == "buy_to_cover":
            if not open_short:
                failures.append("short hedge should not cover without an open synthetic short")
            open_short = False


def verify_result_trade_counts(
    result_rows: list[dict[str, object]],
    trade_rows: list[dict[str, object]],
    failures: list[str],
) -> None:
    hedge_full = result_row(result_rows, SHORT_HEDGE_STRATEGY_NAME, "full_period")
    if hedge_full and int(hedge_full["number_of_trades"]) != len(trade_rows):
        failures.append("short hedge trade count should reflect actual short/cover transitions")

    for period in ["full_period", "in_sample", "out_of_sample"]:
        buy_hold = result_row(result_rows, "spy_buy_and_hold_baseline", period)
        if buy_hold and int(buy_hold["number_of_trades"]) != 1:
            failures.append(f"buy-and-hold benchmark should use one-entry trade convention for {period}")
        cash = result_row(result_rows, "cash_flat_baseline", period)
        if cash and int(cash["number_of_trades"]) != 0:
            failures.append(f"cash baseline should always have zero trades for {period}")

    hedge_split_counts = [
        int(row["number_of_trades"])
        for row in result_rows
        if row["strategy_name"] == SHORT_HEDGE_STRATEGY_NAME and row["period"] in {"in_sample", "out_of_sample"}
    ]
    for row in result_rows:
        if row["strategy_name"] in {"spy_buy_and_hold_baseline", "cash_flat_baseline"}:
            if int(row["number_of_trades"]) in hedge_split_counts and int(row["number_of_trades"]) not in {0, 1}:
                failures.append("benchmark trade counts should not be copied from hedge split trade counts")


def verify_research_conclusions(result_rows: list[dict[str, object]], failures: list[str]) -> None:
    hedge_full = result_row(result_rows, SHORT_HEDGE_STRATEGY_NAME, "full_period")
    if not hedge_full:
        failures.append("missing full-period short hedge result row")
        return
    if float(hedge_full["cagr_pct"]) >= 0 or float(hedge_full["sharpe_ratio"]) >= 0 or float(hedge_full["calmar_ratio"]) >= 0:
        failures.append("deterministic fixture should produce poor short hedge metrics")
    if hedge_full["research_status"] != "not_useful":
        failures.append("poor short hedge metrics should be labelled not_useful")
    if "borrow fees are not modelled" not in str(hedge_full["research_conclusion"]):
        failures.append("short hedge conclusion should mention unmodelled borrow fees")
    if "Pause short hedge research" not in str(hedge_full["required_next_step"]):
        failures.append("short hedge next step should pause the weak research path")

    for row in result_rows:
        for column in ["research_status", "research_conclusion", "required_next_step"]:
            if not row.get(column):
                failures.append(f"missing research conclusion field {column} for {row['strategy_name']} {row['period']}")


def verify_summary(summary_lines: list[str], failures: list[str]) -> None:
    summary = "\n".join(summary_lines)
    if "SHORT HEDGE BACKTEST. RESEARCH ONLY. NOT EXECUTION." not in summary:
        failures.append("terminal summary should clearly mark the report research-only")
    if "not_modelled_initial_research" not in summary:
        failures.append("terminal summary should disclose borrow fee modelling status")
    if "Research conclusion: not useful / pause short hedge research." not in summary:
        failures.append("terminal summary should clearly pause weak short hedge research")
    if "not execution approval" not in summary:
        failures.append("terminal summary should deny execution approval")


def result_row(rows: list[dict[str, object]], strategy_name: str, period: str) -> dict[str, object] | None:
    return next(
        (row for row in rows if row["strategy_name"] == strategy_name and row["period"] == period),
        None,
    )


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--short-hedge-backtest" not in help_text:
        failures.append("command inventory should include --short-hedge-backtest")
    for command in DANGEROUS_SHORT_COMMANDS:
        if command in help_text:
            failures.append(f"short execution command should not exist: {command}")

    config_source = (ROOT / "trading_bot" / "config.py").read_text(encoding="utf-8")
    if 'parse_config_bool(raw, "allow_shorting", False)' not in config_source:
        failures.append("allow_shorting should still default to false")

    source = inspect.getsource(short_hedge)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"short hedge module references forbidden execution term: {term}")


if __name__ == "__main__":
    raise SystemExit(main())
