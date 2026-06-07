from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.defensive as defensive
from trading_bot.research.defensive import generate_defensive_strategy_report


FORBIDDEN_TERMS = [
    "yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def research_row(
    strategy_name: str,
    family: str,
    cagr: float,
    sharpe: float,
    calmar: float,
    drawdown: float,
    lower_drawdown: bool,
) -> dict[str, object]:
    return {
        "strategy_name": strategy_name,
        "ticker_or_portfolio": "portfolio",
        "period": "full_period",
        "is_portfolio_level": True,
        "is_active_strategy": True,
        "strategy_family": family,
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "calmar_ratio": calmar,
        "max_drawdown_pct": drawdown,
        "active_combined_rank_score": 1,
        "beats_best_benchmark_cagr": False,
        "beats_best_benchmark_sharpe": False,
        "beats_best_benchmark_calmar": False,
        "has_lower_drawdown_than_best_benchmark": lower_drawdown,
    }


def walk_row(
    strategy_name: str,
    label: str,
    cagr: float | str,
    sharpe: float | str,
    calmar: float | str,
    drawdown: float | str,
) -> dict[str, object]:
    return {
        "strategy_name": strategy_name,
        "ticker_or_portfolio": "portfolio",
        "walk_forward_view": "portfolio_active" if label != "insufficient_period_data" else "insufficient_data",
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
                research_row("monthly_etf_momentum_rotation", "rotation", 9, 0.75, 0.5, 18, True),
                research_row("high_cagr_high_drawdown", "trend", 25, 1.2, 0.9, 45, False),
                research_row("missing_walk_forward_strategy", "trend", 8, 0.4, 0.2, 20, True),
                research_row("severe_decay_strategy", "trend", 10, 0.8, 0.5, 15, True),
            ],
        )
        write_csv(
            data_dir / "walk_forward_report.csv",
            [
                walk_row("monthly_etf_momentum_rotation", "improved_out_of_sample", 14.1434, 1.0352, 1.1878, 12),
                walk_row("high_cagr_high_drawdown", "robust", 30, 1.3, 1.1, 45),
                walk_row("missing_walk_forward_strategy", "insufficient_period_data", "", "", "", ""),
                walk_row("severe_decay_strategy", "severe_decay", 3, 0.2, 0.1, 35),
            ],
        )

        result = generate_defensive_strategy_report(data_dir)
        if not result.output_path.exists():
            failures.append("defensive_strategy_report.csv was not created")

        rows = {row["strategy_name"]: row for row in result.rows}
        etf = rows["monthly_etf_momentum_rotation"]
        if etf["defensive_status"] != "strongest_defensive_candidate":
            failures.append("ETF rotation should rank as strongest defensive candidate in fixture")
        if "lower drawdown" not in etf["defensive_reason"] or "out-of-sample metrics improved" not in etf["defensive_reason"]:
            failures.append("ETF defensive reason should explain drawdown and improved OOS metrics")
        if rows["high_cagr_high_drawdown"]["defensive_status"] in {"strongest_defensive_candidate", "defensive_candidate"}:
            failures.append("high-CAGR high-drawdown strategy should not automatically become defensive")
        if rows["missing_walk_forward_strategy"]["defensive_status"] != "insufficient_data":
            failures.append("missing walk-forward metrics should become insufficient_data")
        if rows["severe_decay_strategy"]["defensive_status"] != "not_defensive":
            failures.append("severe decay should not be defensive")

        for row in result.rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"safety flags failed for {row['strategy_name']}")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != defensive.DEFENSIVE_COLUMNS:
                failures.append("defensive report columns changed unexpectedly")

        summary = "\n".join(result.summary_lines)
        if "best defensive candidate: monthly_etf_momentum_rotation" not in summary:
            failures.append("best defensive candidate summary failed")
        if "Defensive status is not execution approval" not in summary:
            failures.append("execution approval warning missing")

    with tempfile.TemporaryDirectory() as tmp:
        try:
            generate_defensive_strategy_report(Path(tmp))
            failures.append("missing input files should fail clearly")
        except RuntimeError as exc:
            if "Missing required research report" not in str(exc):
                failures.append(f"missing input error was unclear: {exc}")

    source = inspect.getsource(defensive)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"defensive report references forbidden term: {term}")

    if failures:
        print("Defensive strategy report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Defensive strategy report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
