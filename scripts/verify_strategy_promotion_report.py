from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.promotion as promotion
from trading_bot.research.promotion import generate_strategy_promotion_report


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


def research_row(
    strategy_name: str,
    ticker_or_portfolio: str,
    strategy_role: str,
    strategy_family: str,
    cagr: float,
    sharpe: float,
    calmar: float,
    drawdown: float,
    rank: float | str,
    lower_drawdown: bool = False,
) -> dict[str, object]:
    return {
        "strategy_name": strategy_name,
        "ticker_or_portfolio": ticker_or_portfolio,
        "strategy_family": strategy_family,
        "strategy_role": strategy_role,
        "report_view": "portfolio_full_period",
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "calmar_ratio": calmar,
        "max_drawdown_pct": drawdown,
        "active_combined_rank_score": rank,
        "beats_best_benchmark_cagr": False,
        "beats_best_benchmark_sharpe": False,
        "beats_best_benchmark_calmar": False,
        "has_lower_drawdown_than_best_benchmark": lower_drawdown,
        "number_of_trades": 10,
    }


def walk_row(
    strategy_name: str,
    ticker_or_portfolio: str,
    view: str,
    label: str,
    cagr: float | str = "",
    sharpe: float | str = "",
    calmar: float | str = "",
    drawdown: float | str = "",
) -> dict[str, object]:
    return {
        "strategy_name": strategy_name,
        "ticker_or_portfolio": ticker_or_portfolio,
        "walk_forward_view": view,
        "out_of_sample_cagr_pct": cagr,
        "out_of_sample_sharpe": sharpe,
        "out_of_sample_calmar": calmar,
        "out_of_sample_max_drawdown_pct": drawdown,
        "robustness_label": label,
    }


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "research_report.csv",
            [
                research_row("buy_and_hold_baseline", "portfolio", "benchmark", "benchmark", 20, 1.0, 0.8, 25, ""),
                research_row("sma_50_200_trend", "portfolio", "active_trend", "trend", 12, 0.8, 0.6, 20, 1),
                research_row("sma_20_50_basic", "portfolio", "active_trend", "trend", 8, 0.4, 0.2, 45, 4),
                research_row("failing_strategy", "portfolio", "active_trend", "trend", -2, -0.1, -0.1, 40, 5),
                research_row("monthly_etf_momentum_rotation", "portfolio", "active_rotation", "rotation", 9, 0.7, 0.5, 18, 2),
                research_row("adaptive_risk_on_off_momentum", "portfolio", "active_adaptive", "adaptive", 7, 0.5, 0.3, 28, 3),
            ],
        )
        write_csv(
            data_dir / "walk_forward_report.csv",
            [
                walk_row("buy_and_hold_baseline", "portfolio", "portfolio_benchmark", "moderate_decay", 22, 1.1, 0.9, 24),
                walk_row("sma_50_200_trend", "portfolio", "portfolio_active", "moderate_decay", 13, 0.9, 0.7, 21),
                walk_row("sma_20_50_basic", "portfolio", "portfolio_active", "severe_decay", 6, 0.3, 0.1, 50),
                walk_row("failing_strategy", "portfolio", "portfolio_active", "out_of_sample_failure", -3, -0.2, -0.2, 55),
                walk_row("monthly_etf_momentum_rotation", "portfolio", "insufficient_data", "insufficient_period_data"),
                walk_row("adaptive_risk_on_off_momentum", "portfolio", "insufficient_data", "insufficient_period_data"),
            ],
        )

        result = generate_strategy_promotion_report(data_dir)
        if not result.output_path.exists():
            failures.append("strategy_promotion_report.csv was not created")

        rows = {row["strategy_name"]: row for row in result.rows}
        if rows["buy_and_hold_baseline"]["promotion_status"] != "benchmark_only":
            failures.append("benchmark row should become benchmark_only")
        if rows["sma_50_200_trend"]["promotion_status"] != "preview_candidate":
            failures.append("moderate-decay portfolio winner should become preview_candidate")
        if "not approved for paper execution" not in rows["sma_50_200_trend"]["required_next_step"]:
            failures.append("preview_candidate should not imply execution approval")
        if rows["sma_20_50_basic"]["promotion_status"] != "pause":
            failures.append("severe_decay should become pause")
        if rows["failing_strategy"]["promotion_status"] != "reject_for_now":
            failures.append("out_of_sample_failure should become reject_for_now")
        if rows["monthly_etf_momentum_rotation"]["promotion_status"] != "research_only":
            failures.append("insufficient walk-forward data should become research_only")
        if "Walk-forward split data is missing or insufficient" not in rows["monthly_etf_momentum_rotation"]["promotion_reason"]:
            failures.append("missing ETF rotation split reason failed")
        if "Add in_sample/out_of_sample validation" not in rows["monthly_etf_momentum_rotation"]["required_next_step"]:
            failures.append("missing ETF rotation split next step failed")
        if rows["adaptive_risk_on_off_momentum"]["promotion_status"] != "research_only":
            failures.append("adaptive without split rows should remain research_only")
        if "Walk-forward split data is missing or insufficient" not in rows["adaptive_risk_on_off_momentum"]["promotion_reason"]:
            failures.append("adaptive without split rows should use insufficient-data wording")

        summary = "\n".join(result.summary_lines)
        if "benchmark row: buy_and_hold_baseline" not in summary:
            failures.append("benchmark summary missing")
        if "preview candidates: sma_50_200_trend" not in summary:
            failures.append("preview summary missing")
        if "Promotion does not mean execution approval" not in summary:
            failures.append("execution approval warning missing")

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "research_report.csv",
            [
                research_row("buy_and_hold_baseline", "portfolio", "benchmark", "benchmark", 20, 1.0, 0.8, 25, ""),
                research_row(
                    "monthly_etf_momentum_rotation",
                    "portfolio",
                    "active_rotation",
                    "rotation",
                    9,
                    0.7,
                    0.5,
                    18,
                    2,
                    lower_drawdown=True,
                ),
            ],
        )
        write_csv(
            data_dir / "walk_forward_report.csv",
            [
                walk_row("buy_and_hold_baseline", "portfolio", "portfolio_benchmark", "moderate_decay", 22, 1.1, 0.9, 24),
                walk_row(
                    "monthly_etf_momentum_rotation",
                    "portfolio",
                    "portfolio_active",
                    "improved_out_of_sample",
                    14.1434,
                    1.0352,
                    1.1878,
                    12,
                ),
            ],
        )
        result = generate_strategy_promotion_report(data_dir)
        rows = {row["strategy_name"]: row for row in result.rows}
        etf_row = rows["monthly_etf_momentum_rotation"]
        if etf_row["promotion_status"] != "research_only":
            failures.append("ETF rotation with period data should remain research_only")
        if "walk-forward period data" not in etf_row["promotion_reason"]:
            failures.append("ETF rotation period-data reason failed")
        if "needs in_sample/out_of_sample split data" in etf_row["promotion_reason"]:
            failures.append("ETF rotation period-data reason should not use stale missing-split wording")
        if "Split the ETF rotation backtest periods" in etf_row["required_next_step"]:
            failures.append("ETF rotation next step should not use stale split wording")
        if "Review defensive-strategy criteria" not in etf_row["required_next_step"]:
            failures.append("ETF rotation next step should mention defensive review")
        if "execution approval" not in "\n".join(result.summary_lines):
            failures.append("execution approval warning missing from ETF rotation scenario")

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "research_report.csv",
            [
                research_row("buy_and_hold_baseline", "portfolio", "benchmark", "benchmark", 20, 1.0, 0.8, 25, ""),
                research_row(
                    "monthly_etf_momentum_rotation",
                    "portfolio",
                    "active_rotation",
                    "rotation",
                    9.7,
                    0.75,
                    0.48,
                    20,
                    1,
                    lower_drawdown=True,
                ),
                research_row(
                    "adaptive_risk_on_off_momentum",
                    "portfolio",
                    "active_adaptive",
                    "adaptive",
                    8.9,
                    0.61,
                    0.31,
                    28,
                    2,
                    lower_drawdown=True,
                )
                | {"number_of_trades": 405},
            ],
        )
        write_csv(
            data_dir / "walk_forward_report.csv",
            [
                walk_row("buy_and_hold_baseline", "portfolio", "portfolio_benchmark", "moderate_decay", 22, 1.1, 0.9, 24),
                walk_row(
                    "monthly_etf_momentum_rotation",
                    "portfolio",
                    "portfolio_active",
                    "improved_out_of_sample",
                    14.1434,
                    1.0352,
                    1.1878,
                    12,
                ),
                walk_row(
                    "adaptive_risk_on_off_momentum",
                    "portfolio",
                    "portfolio_active",
                    "improved_out_of_sample",
                    11.606,
                    0.8019,
                    0.7916,
                    14.6617,
                ),
            ],
        )
        write_csv(
            data_dir / "defensive_strategy_report.csv",
            [
                {
                    "strategy_name": "monthly_etf_momentum_rotation",
                    "ticker_or_portfolio": "portfolio",
                    "defensive_status": "strongest_defensive_candidate",
                    "defensive_score": 90.0,
                },
                {
                    "strategy_name": "adaptive_risk_on_off_momentum",
                    "ticker_or_portfolio": "portfolio",
                    "defensive_status": "defensive_candidate",
                    "defensive_score": 82.0,
                },
            ],
        )
        result = generate_strategy_promotion_report(data_dir)
        rows = {row["strategy_name"]: row for row in result.rows}
        adaptive_row = rows["adaptive_risk_on_off_momentum"]
        if adaptive_row["promotion_status"] == "preview_candidate":
            failures.append("adaptive should not become preview_candidate from improved defensive metrics alone")
        if adaptive_row["promotion_status"] != "research_only":
            failures.append("adaptive improved defensive scenario should remain research_only")
        reason = adaptive_row["promotion_reason"]
        if "improved out-of-sample walk-forward metrics" not in reason:
            failures.append("adaptive reason should acknowledge improved out-of-sample metrics")
        if "defensive_candidate status" not in reason:
            failures.append("adaptive reason should acknowledge defensive-candidate status")
        if "trails ETF rotation on out-of-sample Sharpe/Calmar" not in reason:
            failures.append("adaptive reason should compare against ETF rotation defensive metrics")
        if "405 trades" not in reason:
            failures.append("adaptive reason should mention turnover burden")
        if "future metrics improve" in reason or "future metrics improve" in adaptive_row["required_next_step"]:
            failures.append("adaptive reason should not imply metrics have not improved")
        if "Keep research-only; compare turnover, cost burden, and defensive portfolio role against ETF rotation" not in adaptive_row["required_next_step"]:
            failures.append("adaptive next step should focus on turnover/cost/portfolio role")
        if "execution approval" not in "\n".join(result.summary_lines):
            failures.append("execution approval warning missing from adaptive scenario")

    with tempfile.TemporaryDirectory() as tmp:
        try:
            generate_strategy_promotion_report(Path(tmp))
            failures.append("missing source reports should fail clearly")
        except RuntimeError as exc:
            if "Missing required research report" not in str(exc):
                failures.append(f"missing report error was unclear: {exc}")

    source = inspect.getsource(promotion)
    for term in FORBIDDEN_EXECUTION_TERMS:
        if term in source:
            failures.append(f"strategy promotion report references forbidden execution term: {term}")

    if failures:
        print("Strategy promotion report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Strategy promotion report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
