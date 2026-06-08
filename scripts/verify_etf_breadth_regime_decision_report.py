from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.etf_breadth_regime as breadth
from trading_bot.research.etf_breadth_regime import (
    ETF_BREADTH_DECISION_COLUMNS,
    generate_etf_breadth_regime_decision_report,
)


FORBIDDEN_DECISION_TERMS = [
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
    verify_underperforming_decision(failures)
    verify_missing_comparison_data(failures)
    verify_static_safety(failures)

    if failures:
        print("ETF breadth regime decision report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ETF breadth regime decision report verification passed.")
    return 0


def verify_underperforming_decision(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_breadth_fixture(data_dir)
        write_comparison_fixture(data_dir)
        result = generate_etf_breadth_regime_decision_report(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if not result.output_path.exists():
            failures.append("etf_breadth_regime_decision_report.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            if csv.DictReader(file).fieldnames != ETF_BREADTH_DECISION_COLUMNS:
                failures.append("ETF breadth decision columns changed unexpectedly")
        overall = result.rows[0]
        if overall.get("decision_label") not in {"not_promoted_underperforms", "useful_diagnostic_not_strategy"}:
            failures.append(f"underperforming breadth decision should be conservative, got {overall.get('decision_label')}")
        if overall.get("execution_approved") is not False:
            failures.append("overall decision must not approve execution")
        if not any(row.get("benchmark_name") == "monthly_etf_momentum_rotation" for row in result.rows):
            failures.append("decision report should compare against monthly ETF rotation when available")
        if not any(row.get("benchmark_name") == "volatility_managed_dual_momentum_etf" for row in result.rows):
            failures.append("decision report should compare against vol-managed ETF when available")
        verify_safety_flags(result.rows, failures)
        summary = "\n".join(result.summary_lines)
        for expected in [
            "ETF BREADTH REGIME DECISION REPORT. RESEARCH ONLY. NOT EXECUTION.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected text: {expected}")


def verify_missing_comparison_data(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_breadth_fixture(data_dir)
        result = generate_etf_breadth_regime_decision_report(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        overall = result.rows[0]
        if overall.get("decision_label") != "useful_diagnostic_not_strategy":
            failures.append("real breadth metrics without comparisons should be useful_diagnostic_not_strategy")
        if overall.get("comparison_status") != "insufficient_comparison_data":
            failures.append("missing comparisons should be labelled insufficient_comparison_data")
        verify_safety_flags(result.rows, failures)

    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_etf_breadth_regime_decision_report(
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.rows[0].get("decision_label") != "insufficient_comparison_data":
            failures.append("missing breadth metrics should be insufficient_comparison_data")


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--etf-breadth-regime-decision-report" not in help_text:
        failures.append("command inventory should include --etf-breadth-regime-decision-report")
    decision_source = "\n".join(
        inspect.getsource(function)
        for function in [
            breadth.generate_etf_breadth_regime_decision_report,
            breadth.load_benchmark_rows,
            breadth.build_decision_rows,
            breadth.selected_benchmarks,
            breadth.final_decision,
        ]
    )
    for term in FORBIDDEN_DECISION_TERMS:
        if term in decision_source:
            failures.append(f"ETF breadth decision path references forbidden term: {term}")


def verify_safety_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"safety flags failed for metric {row.get('metric')}")


def write_breadth_fixture(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        data_dir / "etf_breadth_regime_backtest.csv",
        [
            {
                "strategy_name": "etf_breadth_regime_allocation",
                "period": "full_period",
                "cagr_pct": "5.0",
                "sharpe_ratio": "0.40",
                "max_drawdown_pct": "25.0",
                "calmar_ratio": "0.20",
            },
            {
                "strategy_name": "etf_breadth_regime_allocation",
                "period": "split_70_30_out_of_sample",
                "cagr_pct": "10.0",
                "sharpe_ratio": "0.80",
                "max_drawdown_pct": "11.0",
                "calmar_ratio": "1.00",
            },
        ],
    )
    write_csv(
        data_dir / "etf_breadth_regime_summary.csv",
        [
            {"regime": "risk_on", "pct_of_days": "70.0", "average_breadth_pct": "75.0"},
            {"regime": "neutral", "pct_of_days": "5.0", "average_breadth_pct": "50.0"},
            {"regime": "defensive", "pct_of_days": "10.0", "average_breadth_pct": "35.0"},
            {"regime": "cash_protection", "pct_of_days": "15.0", "average_breadth_pct": "15.0"},
        ],
    )


def write_comparison_fixture(data_dir: Path) -> None:
    write_csv(
        data_dir / "defensive_candidate_comparison.csv",
        [
            {
                "strategy_name": "monthly_etf_momentum_rotation",
                "period": "out_of_sample",
                "out_of_sample_sharpe": "1.10",
                "out_of_sample_calmar": "1.30",
                "out_of_sample_max_drawdown_pct": "10.0",
            },
            {
                "strategy_name": "volatility_managed_dual_momentum_etf",
                "period": "out_of_sample",
                "out_of_sample_sharpe": "1.20",
                "out_of_sample_calmar": "1.40",
                "out_of_sample_max_drawdown_pct": "9.0",
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
