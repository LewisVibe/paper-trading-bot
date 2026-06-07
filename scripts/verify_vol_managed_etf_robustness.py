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

import trading_bot.research.vol_managed_etf_robustness as robustness
from trading_bot.research.costs import CostModel
from trading_bot.research.vol_managed_etf import VOL_MANAGED_ETF_UNIVERSE
from trading_bot.research.vol_managed_etf_robustness import (
    FIXED_SPLITS,
    VOL_MANAGED_ROBUSTNESS_COLUMNS,
    build_and_write_vol_managed_etf_robustness_report,
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
        temp_root = Path(tmpdir)
        data_dir = temp_root / "data"
        data_dir.mkdir()
        cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_root)
            base_result = build_and_write_vol_managed_etf_robustness_report(
                price_by_ticker=price_by_ticker,
                starting_cash=100_000.0,
                cost_model=CostModel(slippage_bps=Decimal("0")),
                data_dir=data_dir,
                created_at="2026-01-01T00:00:00+00:00",
            )
            write_rotation_robustness_fixture(data_dir / "etf_rotation_robustness_report.csv", mode="two_of_three", vol_rows=base_result.rows)
            result = build_and_write_vol_managed_etf_robustness_report(
                price_by_ticker=price_by_ticker,
                starting_cash=100_000.0,
                cost_model=CostModel(slippage_bps=Decimal("0")),
                data_dir=data_dir,
                created_at="2026-01-01T00:00:00+00:00",
            )
        finally:
            os.chdir(cwd)

        if not result.output_path.exists():
            failures.append("vol-managed robustness output CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            if csv.DictReader(file).fieldnames != VOL_MANAGED_ROBUSTNESS_COLUMNS:
                failures.append("vol-managed robustness columns changed unexpectedly")
        verify_rows(result.rows, failures)
        verify_three_of_three_case(price_by_ticker, data_dir, failures)
        verify_missing_comparison_case(price_by_ticker, failures)
        verify_summary(result.summary_lines, failures)

    verify_static_safety(failures)

    if failures:
        print("Vol-managed ETF robustness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Vol-managed ETF robustness verification passed.")
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


def write_rotation_robustness_fixture(path: Path, mode: str, vol_rows: list[dict[str, object]]) -> None:
    columns = [
        "strategy_name",
        "ticker_or_portfolio",
        "split_name",
        "in_sample_fraction",
        "out_of_sample_cagr_pct",
        "out_of_sample_sharpe",
        "out_of_sample_max_drawdown_pct",
        "out_of_sample_calmar",
        "out_of_sample_trade_count",
        "research_only",
        "preview_only",
        "execution_approved",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        vol_by_split = {str(row["split_name"]): row for row in vol_rows}
        for split_name, fraction in FIXED_SPLITS:
            vol_row = vol_by_split[split_name]
            vol_cagr = float(vol_row["out_of_sample_cagr_pct"])
            vol_sharpe = float(vol_row["out_of_sample_sharpe"])
            vol_calmar = float(vol_row["out_of_sample_calmar"])
            vol_drawdown = float(vol_row["out_of_sample_max_drawdown_pct"])
            if mode == "two_of_three" and split_name == "split_80_20":
                sharpe = str(vol_sharpe + 0.25)
                calmar = str(vol_calmar + 0.25)
                cagr = str(vol_cagr + 1.0)
                drawdown = str(max(0.0, vol_drawdown - 1.0))
            else:
                sharpe = str(vol_sharpe - 0.25)
                calmar = str(vol_calmar - 0.25)
                cagr = str(vol_cagr - 1.0)
                drawdown = str(vol_drawdown + 1.0)
            writer.writerow(
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "split_name": split_name,
                    "in_sample_fraction": fraction,
                    "out_of_sample_cagr_pct": cagr,
                    "out_of_sample_sharpe": sharpe,
                    "out_of_sample_max_drawdown_pct": drawdown,
                    "out_of_sample_calmar": calmar,
                    "out_of_sample_trade_count": "3",
                    "research_only": "True",
                    "preview_only": "True",
                    "execution_approved": "False",
                }
            )


def verify_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    split_names = {row["split_name"] for row in rows}
    expected = {split_name for split_name, _ in FIXED_SPLITS}
    if split_names != expected:
        failures.append(f"fixed split rows changed unexpectedly: {sorted(split_names)}")
    for row in rows:
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"safety flags failed for {row['split_name']}")
        if row["benchmark_strategy_name"] != "monthly_etf_momentum_rotation":
            failures.append(f"{row['split_name']} should use matching ETF rotation robustness benchmark")
        for column in [
            "benchmark_oos_cagr_pct",
            "benchmark_oos_sharpe",
            "benchmark_oos_max_drawdown_pct",
            "benchmark_oos_calmar",
            "cagr_gap_vs_benchmark_oos",
            "sharpe_gap_vs_benchmark_oos",
            "calmar_gap_vs_benchmark_oos",
            "drawdown_reduction_vs_benchmark_oos",
            "comparison_splits_available",
            "comparison_splits_won",
            "comparison_splits_lost",
        ]:
            if row[column] == "":
                failures.append(f"{row['split_name']} should calculate {column}")
        if row["comparison_splits_available"] != 3:
            failures.append("all-comparable fixture should report three available comparison splits")
        if row["comparison_splits_won"] != 2 or row["comparison_splits_lost"] != 1:
            failures.append("two-of-three fixture should report two wins and one loss")
        if row["robustness_status"] != "promising_but_split_sensitive":
            failures.append("two-of-three fixture should remain promising_but_split_sensitive")
        if "2 of 3 fixed splits" not in str(row["robustness_reason"]):
            failures.append("two-of-three fixture should use accurate split-count wording")
        if "split_80_20" not in str(row["robustness_reason"]):
            failures.append("two-of-three fixture should name the losing split")


def verify_three_of_three_case(
    price_by_ticker: dict[str, list[dict[str, float | str]]],
    data_dir: Path,
    failures: list[str],
) -> None:
    cwd = Path.cwd()
    try:
        import os

        os.chdir(data_dir.parent)
        base_result = build_and_write_vol_managed_etf_robustness_report(
            price_by_ticker=price_by_ticker,
            starting_cash=100_000.0,
            cost_model=CostModel(slippage_bps=Decimal("0")),
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        write_rotation_robustness_fixture(data_dir / "etf_rotation_robustness_report.csv", mode="three_of_three", vol_rows=base_result.rows)
        result = build_and_write_vol_managed_etf_robustness_report(
            price_by_ticker=price_by_ticker,
            starting_cash=100_000.0,
            cost_model=CostModel(slippage_bps=Decimal("0")),
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
    finally:
        os.chdir(cwd)
    for row in result.rows:
        if row["robustness_status"] != "robust_candidate":
            failures.append("three-of-three fixture should become robust_candidate")
        if row["comparison_splits_won"] != 3 or row["comparison_splits_lost"] != 0:
            failures.append("three-of-three fixture should report three wins and zero losses")


def verify_missing_comparison_case(
    price_by_ticker: dict[str, list[dict[str, float | str]]],
    failures: list[str],
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        cwd = Path.cwd()
        try:
            import os

            os.chdir(Path(tmpdir))
            result = build_and_write_vol_managed_etf_robustness_report(
                price_by_ticker=price_by_ticker,
                starting_cash=100_000.0,
                cost_model=CostModel(slippage_bps=Decimal("0")),
                data_dir=data_dir,
                created_at="2026-01-01T00:00:00+00:00",
            )
        finally:
            os.chdir(cwd)
    if not any(row["robustness_status"] == "insufficient_data" for row in result.rows):
        failures.append("missing comparison rows should still produce insufficient_data wording")


def verify_summary(summary_lines: list[str], failures: list[str]) -> None:
    summary = "\n".join(summary_lines)
    if "VOL-MANAGED ETF ROBUSTNESS REPORT. RESEARCH ONLY. NOT EXECUTION." not in summary:
        failures.append("summary should clearly mark the report research-only")
    if "split_60_40, split_70_30, split_80_20" not in summary:
        failures.append("summary should list the fixed splits")
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
    if "--vol-managed-etf-robustness" not in help_text:
        failures.append("command inventory should include --vol-managed-etf-robustness")

    source = inspect.getsource(robustness)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"vol-managed robustness module references forbidden execution term: {term}")
    lowered = source.lower()
    for forbidden in ["sell_short", "buy_to_cover"]:
        if forbidden in lowered:
            failures.append(f"vol-managed robustness module should not add {forbidden}")


if __name__ == "__main__":
    raise SystemExit(main())
