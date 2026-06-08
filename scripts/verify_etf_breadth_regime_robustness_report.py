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
    ETF_BREADTH_ROBUSTNESS_COLUMNS,
    ETF_BREADTH_UNIVERSE,
    generate_etf_breadth_regime_robustness_report,
)


FORBIDDEN_ROBUSTNESS_TERMS = [
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
    verify_fixture_robustness(failures)
    verify_missing_input(failures)
    verify_static_safety(failures)

    if failures:
        print("ETF breadth regime robustness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ETF breadth regime robustness verification passed.")
    return 0


def verify_fixture_robustness(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_price_fixture(data_dir / "etf_breadth_price_history.csv")
        write_benchmark_fixture(data_dir / "defensive_candidate_comparison.csv")
        result = generate_etf_breadth_regime_robustness_report(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if str(result.output_path).replace("\\", "/").endswith("data/etf_breadth_regime_robustness_report.csv"):
            failures.append("temporary output path unexpectedly included project data prefix")
        if result.output_path.name != "etf_breadth_regime_robustness_report.csv":
            failures.append("output path should be etf_breadth_regime_robustness_report.csv")
        if not result.output_path.exists():
            failures.append("robustness report CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            if csv.DictReader(file).fieldnames != ETF_BREADTH_ROBUSTNESS_COLUMNS:
                failures.append("ETF breadth robustness columns changed unexpectedly")
        labels = {row.get("split_label") for row in result.rows}
        if labels != {"split_60_40", "split_70_30", "split_80_20"}:
            failures.append(f"fixed split labels missing or changed: {sorted(str(label) for label in labels)}")
        for row in result.rows:
            if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
                failures.append(f"safety flags failed for {row.get('split_label')}")
            if not row.get("out_of_sample_start") or not row.get("out_of_sample_end"):
                failures.append(f"OOS date range missing for {row.get('split_label')}")
            if row.get("robustness_label") not in {
                "robust_diagnostic_candidate",
                "split_sensitive_diagnostic",
                "not_robust",
                "insufficient_data",
            }:
                failures.append(f"unexpected robustness label: {row.get('robustness_label')}")
        summary = "\n".join(result.summary_lines)
        for expected in [
            "ETF BREADTH REGIME ROBUSTNESS REPORT. RESEARCH ONLY. NOT EXECUTION.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "etf_breadth_regime_robustness_report.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected text: {expected}")


def verify_missing_input(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_etf_breadth_regime_robustness_report(
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )
        if {row.get("robustness_label") for row in result.rows} != {"insufficient_data"}:
            failures.append("missing saved price history should produce insufficient_data rows")
        if {row.get("split_label") for row in result.rows} != {"split_60_40", "split_70_30", "split_80_20"}:
            failures.append("missing-input report should still include all fixed split labels")


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--etf-breadth-regime-robustness" not in help_text:
        failures.append("command inventory should include --etf-breadth-regime-robustness")
    source = "\n".join(
        inspect.getsource(function)
        for function in [
            breadth.generate_etf_breadth_regime_robustness_report,
            breadth.build_robustness_rows,
            breadth.robustness_row,
            breadth.overall_robustness_label,
            breadth.build_robustness_summary,
        ]
    )
    for term in FORBIDDEN_ROBUSTNESS_TERMS:
        if term in source:
            failures.append(f"ETF breadth robustness path references forbidden term: {term}")


def write_price_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    start = date(2020, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "ticker", "close"])
        writer.writeheader()
        for day in range(420):
            for index, ticker in enumerate(ETF_BREADTH_UNIVERSE):
                slope = 0.08 if index < 10 else 0.03
                cycle = ((day % 31) - 15) * 0.05
                close = 100 + index + (day * slope) + cycle
                writer.writerow(
                    {
                        "date": (start + timedelta(days=day)).isoformat(),
                        "ticker": ticker,
                        "close": round(close, 4),
                    }
                )


def write_benchmark_fixture(path: Path) -> None:
    write_csv(
        path,
        [
            {
                "strategy_name": "monthly_etf_momentum_rotation",
                "out_of_sample_sharpe": "0.7",
                "out_of_sample_calmar": "0.8",
                "out_of_sample_max_drawdown_pct": "20",
            },
            {
                "strategy_name": "volatility_managed_dual_momentum_etf",
                "out_of_sample_sharpe": "0.8",
                "out_of_sample_calmar": "0.9",
                "out_of_sample_max_drawdown_pct": "18",
            },
        ],
    )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
