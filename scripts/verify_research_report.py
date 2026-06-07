from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.reporting import generate_research_report


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
            data_dir / "strategy_comparison_results.csv",
            [
                {
                    "strategy_name": "sma_20_50_basic",
                    "ticker": "AAPL",
                    "period": "in_sample",
                    "total_return_pct": 500,
                    "cagr_pct": 80,
                    "max_drawdown_pct": 10,
                    "annualised_volatility_pct": 20,
                    "sharpe_ratio": 5,
                    "calmar_ratio": 8,
                    "number_of_trades": 2,
                    "final_equity": 600000,
                }
            ],
        )
        write_csv(
            data_dir / "etf_rotation_results.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "total_return_pct": 120,
                    "cagr_pct": 10,
                    "max_drawdown_pct": 20,
                    "annualised_volatility_pct": 12,
                    "sharpe_ratio": 0.8,
                    "calmar_ratio": 0.5,
                    "number_of_trades": 100,
                    "final_equity": 220000,
                    "commission_per_trade": 0,
                    "commission_bps": 0,
                    "spread_bps": 0,
                    "slippage_bps": 5,
                }
            ],
        )
        write_csv(
            data_dir / "adaptive_momentum_results.csv",
            [
                {
                    "strategy_name": "adaptive_risk_on_off_momentum",
                    "total_return_pct": 90,
                    "cagr_pct": 8,
                    "max_drawdown_pct": 30,
                    "annualised_volatility_pct": 15,
                    "sharpe_ratio": 0.5,
                    "calmar_ratio": 0.25,
                    "number_of_trades": 150,
                    "final_equity": 190000,
                    "commission_per_trade": 0,
                    "commission_bps": 0,
                    "spread_bps": 0,
                    "slippage_bps": 5,
                }
            ],
        )
        write_csv(
            data_dir / "strategy_portfolio_comparison.csv",
            [
                {
                    "strategy_name": "buy_and_hold_baseline",
                    "period": "full_period",
                    "total_return_pct": 200,
                    "cagr_pct": 20,
                    "max_drawdown_pct": 5,
                    "annualised_volatility_pct": 12,
                    "sharpe_ratio": 1.2,
                    "calmar_ratio": 0.8,
                    "number_of_trades": 3,
                    "final_equity": 300000,
                },
                {
                    "strategy_name": "sma_50_200_trend",
                    "period": "full_period",
                    "total_return_pct": 120,
                    "cagr_pct": 12,
                    "max_drawdown_pct": 15,
                    "annualised_volatility_pct": 14,
                    "sharpe_ratio": 0.9,
                    "calmar_ratio": 0.6,
                    "number_of_trades": 10,
                    "final_equity": 220000,
                },
                {
                    "strategy_name": "fifty_two_week_high_breakout",
                    "period": "full_period",
                    "total_return_pct": 80,
                    "cagr_pct": 8,
                    "max_drawdown_pct": 4,
                    "annualised_volatility_pct": 10,
                    "sharpe_ratio": 0.7,
                    "calmar_ratio": 0.5,
                    "number_of_trades": 7,
                    "final_equity": 180000,
                },
            ],
        )

        result = generate_research_report(data_dir)
        if not result.output_path.exists():
            failures.append("research_report.csv was not created")
        if not result.warnings:
            failures.append("missing input files should produce warnings")

        rows = {row["strategy_name"]: row for row in result.rows}
        if rows["sma_20_50_basic"]["rank_by_cagr"] != 1:
            failures.append("ranking by CAGR failed")
        if rows["sma_20_50_basic"]["is_single_ticker"] is not True:
            failures.append("single-ticker report classification failed")
        if rows["sma_20_50_basic"]["is_in_sample"] is not True:
            failures.append("in_sample report classification failed")
        if rows["sma_20_50_basic"]["decision_rank_by_cagr"] != "":
            failures.append("in-sample single-ticker row should be excluded from default decision ranking")
        if rows["buy_and_hold_baseline"]["is_benchmark"] is not True:
            failures.append("buy_and_hold_baseline should be classified as a benchmark")
        if rows["buy_and_hold_baseline"]["is_active_strategy"] is not False:
            failures.append("benchmark row should not be classified as active")
        if rows["sma_50_200_trend"]["is_active_strategy"] is not True:
            failures.append("SMA trend row should be classified as active")
        if rows["fifty_two_week_high_breakout"]["strategy_role"] != "active_breakout":
            failures.append("breakout row should be classified as active_breakout")
        if rows["monthly_etf_momentum_rotation"]["strategy_role"] != "active_rotation":
            failures.append("rotation row should be classified as active_rotation")
        if rows["adaptive_risk_on_off_momentum"]["strategy_role"] != "active_adaptive":
            failures.append("adaptive row should be classified as active_adaptive")
        if rows["buy_and_hold_baseline"]["is_portfolio_level"] is not True:
            failures.append("portfolio report classification failed")
        if rows["buy_and_hold_baseline"]["is_full_period"] is not True:
            failures.append("full-period report classification failed")
        if rows["buy_and_hold_baseline"]["decision_rank_by_cagr"] != 1:
            failures.append("decision ranking by CAGR failed")
        if rows["fifty_two_week_high_breakout"]["rank_by_max_drawdown"] != 1:
            failures.append("ranking by max drawdown failed")
        if rows["sma_20_50_basic"]["rank_by_sharpe"] != 1:
            failures.append("ranking by Sharpe failed")
        if rows["sma_20_50_basic"]["rank_by_calmar"] != 1:
            failures.append("ranking by Calmar failed")
        if rows["buy_and_hold_baseline"]["decision_rank_by_sharpe"] != 1:
            failures.append("decision ranking by Sharpe failed")
        if rows["buy_and_hold_baseline"]["decision_rank_by_calmar"] != 1:
            failures.append("decision ranking by Calmar failed")
        if rows["buy_and_hold_baseline"]["active_rank_by_cagr"] != "":
            failures.append("active ranking should exclude buy_and_hold_baseline")
        if rows["sma_20_50_basic"]["active_rank_by_cagr"] != "":
            failures.append("active ranking should exclude in-sample rows")
        if rows["sma_50_200_trend"]["active_rank_by_cagr"] != 1:
            failures.append("active ranking by CAGR failed")

        first_score = rows["monthly_etf_momentum_rotation"]["combined_rank_score"]
        second_result = generate_research_report(data_dir)
        second_rows = {row["strategy_name"]: row for row in second_result.rows}
        if second_rows["monthly_etf_momentum_rotation"]["combined_rank_score"] != first_score:
            failures.append("combined_rank_score should be deterministic")
        first_decision_score = rows["monthly_etf_momentum_rotation"]["decision_combined_rank_score"]
        if second_rows["monthly_etf_momentum_rotation"]["decision_combined_rank_score"] != first_decision_score:
            failures.append("decision_combined_rank_score should be deterministic")
        first_active_score = rows["monthly_etf_momentum_rotation"]["active_combined_rank_score"]
        if second_rows["monthly_etf_momentum_rotation"]["active_combined_rank_score"] != first_active_score:
            failures.append("active_combined_rank_score should be deterministic")
        if rows["sma_50_200_trend"]["cagr_vs_best_benchmark_pct"] != -8.0:
            failures.append("relative CAGR versus benchmark should be deterministic")
        if rows["sma_50_200_trend"]["return_gap_vs_best_benchmark_pct"] != -8.0:
            failures.append("return gap diagnostic should match benchmark CAGR gap")
        if rows["fifty_two_week_high_breakout"]["drawdown_reduction_vs_best_benchmark_pct"] != 1.0:
            failures.append("drawdown reduction diagnostic should be deterministic")
        if rows["sma_50_200_trend"]["sharpe_gap_vs_best_benchmark"] != -0.3:
            failures.append("Sharpe gap diagnostic should be deterministic")
        if rows["sma_50_200_trend"]["calmar_gap_vs_best_benchmark"] != -0.2:
            failures.append("Calmar gap diagnostic should be deterministic")
        if rows["sma_50_200_trend"]["trade_count_vs_best_benchmark"] != 7.0:
            failures.append("trade count diagnostic should be deterministic")
        if rows["monthly_etf_momentum_rotation"]["active_trade_penalty_note"] != "materially_higher_than_benchmark":
            failures.append("active trade penalty note should flag high turnover")
        if rows["sma_50_200_trend"]["underperformance_reason"] != "lower_return_and_higher_drawdown":
            failures.append("SMA underperformance reason was unexpected")
        if rows["fifty_two_week_high_breakout"]["underperformance_reason"] != "defensive_but_return_drag_too_high":
            failures.append("breakout underperformance reason was unexpected")
        if rows["sma_50_200_trend"]["beats_best_benchmark_cagr"] is not False:
            failures.append("active CAGR benchmark comparison failed")
        if rows["fifty_two_week_high_breakout"]["has_lower_drawdown_than_best_benchmark"] is not True:
            failures.append("active drawdown benchmark comparison failed")

        summary_text = "\n".join(result.summary_lines)
        if "best all-row CAGR: sma_20_50_basic" not in summary_text:
            failures.append("all-row summary should still show the strongest single-ticker CAGR")
        if "best benchmark by decision combined score: buy_and_hold_baseline" not in summary_text:
            failures.append("benchmark summary was missing")
        if "best active strategy by active combined score:" not in summary_text:
            failures.append("active combined summary was missing")
        if "best active strategy by CAGR: sma_50_200_trend" not in summary_text:
            failures.append("active CAGR summary was missing")
        if "best decision-view CAGR: sma_20_50_basic" in summary_text:
            failures.append("decision summary should exclude in-sample single-ticker rows")
        if "in-sample single-ticker rankings can be misleading" not in summary_text:
            failures.append("misleading-ranking warning was missing")
        if "no active strategy beats the best benchmark on CAGR, Sharpe, Calmar" not in summary_text:
            failures.append("benchmark superiority warning was missing")
        if "adaptive_risk_on_off_momentum ranks below monthly_etf_momentum_rotation" not in summary_text:
            failures.append("adaptive underperformance warning was missing")
        if "best active lower drawdown than benchmark: no" not in summary_text:
            failures.append("best active drawdown diagnostic was missing")
        if "best active gives up too much CAGR for drawdown reduction: yes" not in summary_text:
            failures.append("best active CAGR/drawdown tradeoff diagnostic was missing")
        if "Conclusion: active strategies currently do not justify replacing the benchmark." not in summary_text:
            failures.append("research conclusion was missing")
        if "Conclusion: ETF rotation is the best defensive candidate but has too much return drag." not in summary_text:
            failures.append("ETF rotation conclusion was missing")
        if "Conclusion: adaptive strategy remains below ETF rotation despite added complexity." not in summary_text:
            failures.append("adaptive conclusion was missing")

    with tempfile.TemporaryDirectory() as empty_tmp:
        try:
            generate_research_report(Path(empty_tmp))
            failures.append("empty research folder should fail clearly")
        except RuntimeError as exc:
            if "No usable research CSV files" not in str(exc):
                failures.append(f"empty folder error was unclear: {exc}")

    if failures:
        print("Research report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Research report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
