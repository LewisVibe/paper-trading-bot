from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.defensive_comparison as comparison
from trading_bot.research.defensive_comparison import generate_defensive_candidate_comparison


FORBIDDEN_TERMS = [
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
]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    failures: list[str] = []

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "walk_forward_report.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "out_of_sample_cagr_pct": 14.1434,
                    "out_of_sample_sharpe": 1.0352,
                    "out_of_sample_calmar": 1.1878,
                    "out_of_sample_max_drawdown_pct": 12,
                    "robustness_label": "improved_out_of_sample",
                },
                {
                    "strategy_name": "adaptive_risk_on_off_momentum",
                    "ticker_or_portfolio": "portfolio",
                    "out_of_sample_cagr_pct": 11.606,
                    "out_of_sample_sharpe": 0.8019,
                    "out_of_sample_calmar": 0.7916,
                    "out_of_sample_max_drawdown_pct": 14.6617,
                    "robustness_label": "improved_out_of_sample",
                },
            ],
        )
        write_csv(
            data_dir / "vol_managed_etf_results.csv",
            [
                {
                    "strategy_name": "volatility_managed_dual_momentum_etf",
                    "ticker_or_portfolio": "portfolio",
                    "period": "out_of_sample",
                    "cagr_pct": 15.5766,
                    "sharpe_ratio": 1.2256,
                    "calmar_ratio": 1.5339,
                    "max_drawdown_pct": 10.1551,
                    "number_of_trades": 134,
                    "research_status": "promising_research_candidate",
                }
            ],
        )
        write_csv(
            data_dir / "vol_managed_etf_robustness_report.csv",
            vol_robustness_rows(wins=2, losses=1),
        )
        write_csv(
            data_dir / "defensive_strategy_report.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "strategy_family": "rotation",
                    "defensive_score": 90,
                    "defensive_status": "strongest_defensive_candidate",
                },
                {
                    "strategy_name": "adaptive_risk_on_off_momentum",
                    "ticker_or_portfolio": "portfolio",
                    "strategy_family": "adaptive",
                    "defensive_score": 82,
                    "defensive_status": "defensive_candidate",
                },
            ],
        )
        write_csv(
            data_dir / "strategy_promotion_report.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "trade_count": 120,
                },
                {
                    "strategy_name": "adaptive_risk_on_off_momentum",
                    "ticker_or_portfolio": "portfolio",
                    "trade_count": 405,
                },
            ],
        )

        result = generate_defensive_candidate_comparison(data_dir)
        if not result.output_path.exists():
            failures.append("defensive_candidate_comparison.csv was not created")
        rows = {row["strategy_name"]: row for row in result.rows}
        etf = rows["monthly_etf_momentum_rotation"]
        vol = rows["volatility_managed_dual_momentum_etf"]
        adaptive = rows["adaptive_risk_on_off_momentum"]
        if etf["comparison_status"] != "preferred_defensive_candidate":
            failures.append("ETF rotation should remain preferred when vol-managed wins 2 of 3 fixed splits")
        if etf["policy_rank"] != 1 or etf["comparison_rank"] != 1:
            failures.append("ETF rotation should have policy/comparison rank 1 when it remains preferred")
        if vol["metric_rank"] != 1:
            failures.append("vol-managed should keep raw metric rank 1 when OOS metrics lead")
        if vol["policy_rank"] != 2 or vol["comparison_rank"] != 2:
            failures.append("vol-managed should have policy/comparison rank 2 while it remains split-sensitive")
        if vol["comparison_status"] != "promising_but_split_sensitive":
            failures.append("vol-managed should be promising but split-sensitive when it wins 2 of 3 fixed splits")
        if vol["fixed_split_win_count"] != 2 or vol["fixed_split_loss_count"] != 1:
            failures.append("vol-managed should report 2 fixed-split wins and 1 loss")
        if "wins 2 of 3 fixed splits" not in vol["split_comparison_summary"]:
            failures.append("vol-managed split summary should describe the 2-of-3 result")
        if "promising defensive research candidate" not in "\n".join(result.summary_lines):
            failures.append("summary should mention the promising vol-managed research candidate")
        if adaptive["comparison_status"] != "research_only_high_turnover":
            failures.append("adaptive should be secondary/research-only due to high turnover, not rejected outright")
        if int(adaptive["policy_rank"]) <= int(vol["policy_rank"]):
            failures.append("adaptive should rank below ETF rotation and vol-managed when turnover/complexity are worse")
        if "Higher turnover than ETF rotation" not in adaptive["relative_turnover_note"]:
            failures.append("adaptive turnover warning should compare against ETF rotation")
        if "usable defensive metrics" not in adaptive["comparison_reason"]:
            failures.append("adaptive reason should acknowledge positive defensive evidence")
        for row in result.rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"safety flags failed for {row['strategy_name']}")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != comparison.DEFENSIVE_CANDIDATE_COMPARISON_COLUMNS:
                failures.append("comparison CSV columns changed unexpectedly")
        summary = "\n".join(result.summary_lines)
        if "preferred defensive candidate: monthly_etf_momentum_rotation" not in summary:
            failures.append("preferred summary failed")
        preferred_index = summary.find("preferred defensive candidate: monthly_etf_momentum_rotation")
        promising_index = summary.find("promising defensive research candidate: volatility_managed_dual_momentum_etf")
        secondary_index = summary.find("secondary defensive candidate: adaptive_risk_on_off_momentum")
        if not (preferred_index != -1 and promising_index != -1 and secondary_index != -1 and preferred_index < promising_index < secondary_index):
            failures.append("summary should follow policy-rank order: preferred, promising, secondary")
        if "adaptive turnover warning" not in summary:
            failures.append("adaptive turnover summary warning missing")
        if "not execution approval" not in summary:
            failures.append("execution approval warning missing")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "walk_forward_report.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "out_of_sample_cagr_pct": 10,
                    "out_of_sample_sharpe": 0.7,
                    "out_of_sample_calmar": 0.8,
                    "out_of_sample_max_drawdown_pct": 14,
                    "robustness_label": "robust",
                }
            ],
        )
        write_csv(
            data_dir / "vol_managed_etf_results.csv",
            [
                {
                    "strategy_name": "volatility_managed_dual_momentum_etf",
                    "ticker_or_portfolio": "portfolio",
                    "period": "out_of_sample",
                    "cagr_pct": 16,
                    "sharpe_ratio": 1.3,
                    "calmar_ratio": 1.5,
                    "max_drawdown_pct": 10,
                }
            ],
        )
        write_csv(data_dir / "vol_managed_etf_robustness_report.csv", vol_robustness_rows(wins=3, losses=0))
        write_csv(
            data_dir / "defensive_strategy_report.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "strategy_family": "rotation",
                    "defensive_score": 80,
                    "defensive_status": "defensive_candidate",
                }
            ],
        )
        result = generate_defensive_candidate_comparison(data_dir)
        rows = {row["strategy_name"]: row for row in result.rows}
        if rows["volatility_managed_dual_momentum_etf"]["comparison_status"] != "preferred_defensive_candidate":
            failures.append("vol-managed can become preferred when it wins all fixed splits and leads metrics")
        if rows["volatility_managed_dual_momentum_etf"]["policy_rank"] != 1:
            failures.append("vol-managed should have policy rank 1 when it wins all fixed splits and leads metrics")
        if rows["volatility_managed_dual_momentum_etf"]["metric_rank"] != 1:
            failures.append("vol-managed should have metric rank 1 when it leads raw OOS metrics")
        if rows["volatility_managed_dual_momentum_etf"]["execution_approved"] is not False:
            failures.append("vol-managed preferred research row must still deny execution approval")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "walk_forward_report.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "out_of_sample_cagr_pct": 14,
                    "out_of_sample_sharpe": 1,
                    "out_of_sample_calmar": 1,
                    "out_of_sample_max_drawdown_pct": 12,
                    "robustness_label": "robust",
                }
            ],
        )
        write_csv(
            data_dir / "defensive_strategy_report.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "strategy_family": "rotation",
                    "defensive_score": 80,
                    "defensive_status": "defensive_candidate",
                }
            ],
        )
        result = generate_defensive_candidate_comparison(data_dir)
        rows = {row["strategy_name"]: row for row in result.rows}
        if rows["adaptive_risk_on_off_momentum"]["comparison_status"] != "insufficient_data":
            failures.append("missing adaptive rows should become insufficient_data")
        if rows["adaptive_risk_on_off_momentum"]["execution_approved"] is not False:
            failures.append("missing adaptive row should still deny execution approval")
        if rows["volatility_managed_dual_momentum_etf"]["comparison_status"] != "insufficient_data":
            failures.append("missing vol-managed rows should become insufficient_data")

    with TemporaryDirectory() as tmp:
        try:
            generate_defensive_candidate_comparison(Path(tmp))
            failures.append("missing input files should fail clearly")
        except RuntimeError as exc:
            if "Missing required walk-forward report" not in str(exc):
                failures.append(f"missing input error was unclear: {exc}")

    source = inspect.getsource(comparison)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"defensive candidate comparison references forbidden term: {term}")
    if "crypto_" in source:
        failures.append("defensive candidate comparison should not add or reference crypto strategy logic")

    if failures:
        print("Defensive candidate comparison verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Defensive candidate comparison verification passed.")
    return 0


def vol_robustness_rows(wins: int, losses: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    split_names = ["split_60_40", "split_70_30", "split_80_20"]
    for index, split_name in enumerate(split_names):
        is_win = index < wins
        rows.append(
            {
                "strategy_name": "volatility_managed_dual_momentum_etf",
                "ticker_or_portfolio": "portfolio",
                "split_name": split_name,
                "benchmark_strategy_name": "monthly_etf_momentum_rotation",
                "out_of_sample_cagr_pct": 15,
                "out_of_sample_sharpe": 1.2,
                "out_of_sample_calmar": 1.4,
                "out_of_sample_max_drawdown_pct": 10,
                "sharpe_gap_vs_benchmark_oos": 0.2 if is_win else -0.1,
                "calmar_gap_vs_benchmark_oos": 0.2 if is_win else -0.1,
                "cagr_gap_vs_benchmark_oos": 1 if is_win else -1,
                "drawdown_reduction_vs_benchmark_oos": 1,
                "comparison_splits_available": wins + losses,
                "comparison_splits_won": wins,
                "comparison_splits_lost": losses,
                "robustness_status": "robust_candidate" if wins == 3 else "promising_but_split_sensitive",
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
            }
        )
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
