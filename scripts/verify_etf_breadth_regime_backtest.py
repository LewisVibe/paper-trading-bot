from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.etf_breadth_regime as breadth
from trading_bot.research.etf_breadth_regime import (
    ETF_BREADTH_RESULT_COLUMNS,
    ETF_BREADTH_STRATEGY_NAME,
    ETF_BREADTH_SUMMARY_COLUMNS,
    ETF_BREADTH_UNIVERSE,
    calculate_breadth_pct,
    classify_regime,
    generate_etf_breadth_regime_backtest,
)


FORBIDDEN_SOURCE_TERMS = [
    "yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_simulated_positions",
    "decide_trade",
    "download_close_prices",
    "download_backtest_prices",
    "configure_yfinance_cache",
    "sqlite3",
]


def main() -> int:
    failures: list[str] = []
    verify_threshold_logic(failures)
    verify_fixture_backtest(failures)
    verify_missing_input(failures)
    verify_static_safety(failures)

    if failures:
        print("ETF breadth regime backtest verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ETF breadth regime backtest verification passed.")
    return 0


def verify_threshold_logic(failures: list[str]) -> None:
    if classify_regime(60.0, True) != "risk_on":
        failures.append("breadth >= 60 with SPY above SMA200 should classify risk_on")
    if classify_regime(45.0, True) != "neutral":
        failures.append("breadth between 40 and 60 with SPY above SMA200 should classify neutral")
    if classify_regime(35.0, False) != "defensive":
        failures.append("SPY below SMA200 with moderate breadth should classify defensive")
    if classify_regime(24.9, True) != "cash_protection":
        failures.append("breadth below 25 should classify cash_protection")

    closes_by_ticker = {}
    close_by_ticker = {}
    for index, ticker in enumerate(ETF_BREADTH_UNIVERSE):
        final_close = 110.0 if index < 7 else 90.0
        closes_by_ticker[ticker] = [100.0] * 199 + [final_close]
        close_by_ticker[ticker] = final_close
    breadth_pct = calculate_breadth_pct(close_by_ticker, closes_by_ticker, 199)
    if round(breadth_pct, 4) != 50.0:
        failures.append(f"breadth percentage should be 50.0, got {breadth_pct}")


def verify_fixture_backtest(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_price_fixture(data_dir / "etf_breadth_price_history.csv")
        result = generate_etf_breadth_regime_backtest(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if not result.output_path.exists():
            failures.append("etf_breadth_regime_backtest.csv was not created")
        if not result.summary_path.exists():
            failures.append("etf_breadth_regime_summary.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            if csv.DictReader(file).fieldnames != ETF_BREADTH_RESULT_COLUMNS:
                failures.append("ETF breadth result columns changed unexpectedly")
        with result.summary_path.open(newline="", encoding="utf-8") as file:
            if csv.DictReader(file).fieldnames != ETF_BREADTH_SUMMARY_COLUMNS:
                failures.append("ETF breadth summary columns changed unexpectedly")
        verify_result_rows(result.rows, failures)
        verify_summary_rows(result.summary_rows, failures)
        summary = "\n".join(result.summary_lines)
        if "ETF BREADTH REGIME BACKTEST. RESEARCH ONLY. NOT EXECUTION." not in summary:
            failures.append("terminal summary should mark ETF breadth report research-only")
        if "No orders were created, submitted, or cancelled." not in summary:
            failures.append("terminal summary should confirm no order activity")
        if "No execution approval was granted." not in summary:
            failures.append("terminal summary should deny execution approval")


def verify_result_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    periods = {row.get("period") for row in rows}
    if "full_period" not in periods or "split_70_30_out_of_sample" not in periods:
        failures.append(f"expected full and OOS period rows, got {sorted(str(period) for period in periods)}")
    for row in rows:
        if row.get("strategy_name") != ETF_BREADTH_STRATEGY_NAME:
            failures.append("ETF breadth report should use the fixed strategy name only")
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"safety flags failed for period {row.get('period')}")
        for column in ["cagr_pct", "sharpe_ratio", "max_drawdown_pct", "calmar_ratio", "exposure_pct", "number_of_regime_changes"]:
            if row.get(column, "") == "":
                failures.append(f"missing metric {column} for period {row.get('period')}")


def verify_summary_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    regimes = {row.get("regime") for row in rows}
    for expected in ["risk_on", "neutral", "defensive", "cash_protection"]:
        if expected not in regimes:
            failures.append(f"summary should include regime {expected}")
    for row in rows:
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"summary safety flags failed for regime {row.get('regime')}")


def verify_missing_input(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_etf_breadth_regime_backtest(
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.rows[0].get("robustness_status") != "insufficient_data":
            failures.append("missing saved price input should produce insufficient_data")
        summary = "\n".join(result.summary_lines)
        if "data/etf_breadth_price_history.csv" not in summary:
            failures.append("missing-input summary should name the required saved price CSV")


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--etf-breadth-regime-backtest" not in help_text:
        failures.append("command inventory should include --etf-breadth-regime-backtest")
    source = inspect.getsource(breadth.generate_etf_breadth_regime_backtest)
    source += inspect.getsource(breadth.build_etf_breadth_outputs)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"ETF breadth regime module references forbidden term: {term}")


def write_price_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    start = date(2024, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "ticker", "close"])
        writer.writeheader()
        for day in range(320):
            regime_block = day // 80
            for index, ticker in enumerate(ETF_BREADTH_UNIVERSE):
                close = synthetic_close(index, day, regime_block)
                writer.writerow(
                    {
                        "date": (start + timedelta(days=day)).isoformat(),
                        "ticker": ticker,
                        "close": round(close, 4),
                    }
                )


def synthetic_close(index: int, day: int, regime_block: int) -> float:
    base = 100.0 + index
    if regime_block == 0:
        return base + day * 0.05
    if regime_block == 1:
        return base + day * (0.08 if index < 9 else -0.03)
    if regime_block == 2:
        return base + day * (0.05 if index < 6 else -0.08)
    return base + day * (-0.03 if index < 4 else -0.12)


if __name__ == "__main__":
    raise SystemExit(main())
