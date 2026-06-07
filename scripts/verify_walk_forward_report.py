from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.walk_forward as walk_forward
from trading_bot.research.walk_forward import generate_walk_forward_report


FORBIDDEN_EXECUTION_TERMS = [
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "strategy_portfolio_comparison.csv",
            [
                {
                    "strategy_name": "buy_and_hold_baseline",
                    "period": "in_sample",
                    "cagr_pct": 11,
                    "sharpe_ratio": 0.8,
                    "calmar_ratio": 0.7,
                    "max_drawdown_pct": 18,
                },
                {
                    "strategy_name": "buy_and_hold_baseline",
                    "period": "out_of_sample",
                    "cagr_pct": 15,
                    "sharpe_ratio": 1.1,
                    "calmar_ratio": 0.9,
                    "max_drawdown_pct": 17,
                },
                {
                    "strategy_name": "sma_50_200_trend",
                    "period": "in_sample",
                    "cagr_pct": 10,
                    "sharpe_ratio": 1.0,
                    "calmar_ratio": 0.8,
                    "max_drawdown_pct": 12,
                },
                {
                    "strategy_name": "sma_50_200_trend",
                    "period": "out_of_sample",
                    "cagr_pct": 9,
                    "sharpe_ratio": 0.9,
                    "calmar_ratio": 0.7,
                    "max_drawdown_pct": 13,
                },
                {
                    "strategy_name": "sma_20_50_basic",
                    "period": "in_sample",
                    "cagr_pct": 12,
                    "sharpe_ratio": 1.0,
                    "calmar_ratio": 0.9,
                    "max_drawdown_pct": 10,
                },
                {
                    "strategy_name": "sma_20_50_basic",
                    "period": "out_of_sample",
                    "cagr_pct": 7,
                    "sharpe_ratio": 0.75,
                    "calmar_ratio": 0.65,
                    "max_drawdown_pct": 14,
                },
                {
                    "strategy_name": "sma_20_50_regime",
                    "period": "in_sample",
                    "cagr_pct": 20,
                    "sharpe_ratio": 1.4,
                    "calmar_ratio": 1.0,
                    "max_drawdown_pct": 10,
                },
                {
                    "strategy_name": "sma_20_50_regime",
                    "period": "out_of_sample",
                    "cagr_pct": 8,
                    "sharpe_ratio": 0.4,
                    "calmar_ratio": 0.4,
                    "max_drawdown_pct": 20,
                },
                {
                    "strategy_name": "fifty_two_week_high_breakout",
                    "period": "in_sample",
                    "cagr_pct": 15,
                    "sharpe_ratio": 1.2,
                    "calmar_ratio": 0.9,
                    "max_drawdown_pct": 11,
                },
                {
                    "strategy_name": "fifty_two_week_high_breakout",
                    "period": "out_of_sample",
                    "cagr_pct": -2,
                    "sharpe_ratio": -0.1,
                    "calmar_ratio": -0.1,
                    "max_drawdown_pct": 25,
                },
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "period": "in_sample",
                    "cagr_pct": 7.8672,
                    "sharpe_ratio": 0.6266,
                    "calmar_ratio": 0.3897,
                    "max_drawdown_pct": 20,
                },
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "period": "out_of_sample",
                    "cagr_pct": 14.1434,
                    "sharpe_ratio": 1.0352,
                    "calmar_ratio": 1.1878,
                    "max_drawdown_pct": 12,
                },
            ],
        )
        write_csv(
            data_dir / "strategy_comparison_results.csv",
            [
                {
                    "strategy_name": "buy_above_200_exit_below_200",
                    "ticker": "SPY",
                    "period": "in_sample",
                    "cagr_pct": 25,
                    "sharpe_ratio": 2.0,
                    "calmar_ratio": 1.5,
                    "max_drawdown_pct": 8,
                },
                {
                    "strategy_name": "buy_above_200_exit_below_200",
                    "ticker": "SPY",
                    "period": "out_of_sample",
                    "cagr_pct": 30,
                    "sharpe_ratio": 2.5,
                    "calmar_ratio": 2.0,
                    "max_drawdown_pct": 7,
                },
            ],
        )
        write_csv(
            data_dir / "adaptive_momentum_results.csv",
            [
                {
                    "strategy_name": "adaptive_risk_on_off_momentum",
                    "ticker_or_portfolio": "portfolio",
                    "period": "in_sample",
                    "cagr_pct": 8,
                    "sharpe_ratio": 0.5,
                    "calmar_ratio": 0.4,
                    "max_drawdown_pct": 20,
                },
                {
                    "strategy_name": "adaptive_risk_on_off_momentum",
                    "ticker_or_portfolio": "portfolio",
                    "period": "out_of_sample",
                    "cagr_pct": 6,
                    "sharpe_ratio": 0.45,
                    "calmar_ratio": 0.35,
                    "max_drawdown_pct": 21,
                },
            ],
        )

        result = generate_walk_forward_report(data_dir)
        if not result.output_path.exists():
            failures.append("walk_forward_report.csv was not created")
        if not result.warnings:
            failures.append("missing input files should produce warnings")

        rows = {row["strategy_name"]: row for row in result.rows}
        robust = rows["sma_50_200_trend"]
        if robust["has_in_sample"] is not True or robust["has_out_of_sample"] is not True:
            failures.append("in/out sample rows were not paired correctly")
        if rows["buy_and_hold_baseline"]["is_benchmark"] is not True:
            failures.append("benchmark classification failed")
        if rows["buy_and_hold_baseline"]["wf_active_rank_by_oos_cagr"] != "":
            failures.append("active-only ranking should exclude buy_and_hold_baseline")
        if robust["is_portfolio_level"] is not True or robust["walk_forward_view"] != "portfolio_active":
            failures.append("portfolio active classification failed")
        if rows["buy_above_200_exit_below_200"]["is_single_ticker"] is not True:
            failures.append("single-ticker classification failed")
        if rows["buy_above_200_exit_below_200"]["walk_forward_view"] != "single_ticker_active":
            failures.append("single-ticker active view classification failed")
        if robust["cagr_decay_pct"] != -1.0:
            failures.append("CAGR decay calculation failed")
        if robust["sharpe_decay"] != -0.1:
            failures.append("Sharpe decay calculation failed")
        if robust["calmar_decay"] != -0.1:
            failures.append("Calmar decay calculation failed")
        if robust["drawdown_worsening_pct"] != 1.0:
            failures.append("drawdown worsening calculation failed")
        if robust["robustness_label"] != "robust":
            failures.append("robust label failed")
        if rows["sma_20_50_basic"]["robustness_label"] != "moderate_decay":
            failures.append("moderate decay label failed")
        if rows["sma_20_50_regime"]["robustness_label"] != "severe_decay":
            failures.append("severe decay label failed")
        if rows["fifty_two_week_high_breakout"]["robustness_label"] != "out_of_sample_failure":
            failures.append("negative out-of-sample CAGR label failed")
        if rows["monthly_etf_momentum_rotation"]["robustness_label"] != "improved_out_of_sample":
            failures.append("improved out-of-sample label failed")
        if rows["monthly_etf_momentum_rotation"]["notes"] != "Out-of-sample CAGR, Sharpe, and Calmar are equal to or better than in-sample.":
            failures.append("improved out-of-sample note failed")
        if rows["adaptive_risk_on_off_momentum"]["has_in_sample"] is not True:
            failures.append("adaptive in-sample row should be paired")
        if rows["adaptive_risk_on_off_momentum"]["has_out_of_sample"] is not True:
            failures.append("adaptive out-of-sample row should be paired")
        if rows["adaptive_risk_on_off_momentum"]["walk_forward_view"] != "portfolio_active":
            failures.append("adaptive walk-forward view should be portfolio_active")
        if rows["adaptive_risk_on_off_momentum"]["robustness_label"] == "insufficient_period_data":
            failures.append("adaptive should not be insufficient when split rows exist")
        if rows["monthly_etf_momentum_rotation"]["wf_active_rank_by_oos_cagr"] != 1:
            failures.append("improved ETF rotation should be eligible for active ranking")
        if rows["sma_50_200_trend"]["wf_active_rank_by_oos_cagr"] != 2:
            failures.append("active portfolio CAGR ranking failed")

        summary = "\n".join(result.summary_lines)
        if "best portfolio benchmark by out-of-sample CAGR: buy_and_hold_baseline" not in summary:
            failures.append("portfolio benchmark summary failed")
        if "best portfolio active by out-of-sample CAGR: monthly_etf_momentum_rotation" not in summary:
            failures.append("portfolio active summary failed")
        if "best portfolio active by out-of-sample CAGR: buy_above_200_exit_below_200" in summary:
            failures.append("single-ticker row should not dominate portfolio headline summary")
        if "single-ticker diagnostic best out-of-sample CAGR: buy_above_200_exit_below_200" not in summary:
            failures.append("single-ticker diagnostic summary failed")
        if "severe-decay portfolio active strategies: sma_20_50_regime" not in summary:
            failures.append("summary severe decay list failed")
        if "insufficient period data: adaptive_risk_on_off_momentum" in summary:
            failures.append("adaptive should not be named in insufficient period list when split rows exist")
        if "adaptive_risk_on_off_momentum currently have insufficient period data" in summary:
            failures.append("adaptive insufficient data note should not appear when split rows exist")
        if "monthly_etf_momentum_rotation currently have insufficient period data" in summary:
            failures.append("ETF rotation should not be named in insufficient period note when split rows exist")

    with tempfile.TemporaryDirectory() as empty_tmp:
        try:
            generate_walk_forward_report(Path(empty_tmp))
            failures.append("empty research folder should fail clearly")
        except RuntimeError as exc:
            if "No usable research CSV files" not in str(exc):
                failures.append(f"empty folder error was unclear: {exc}")

    source = inspect.getsource(walk_forward)
    for term in FORBIDDEN_EXECUTION_TERMS:
        if term in source:
            failures.append(f"walk-forward report references forbidden execution term: {term}")

    if failures:
        print("Walk-forward report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Walk-forward report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
