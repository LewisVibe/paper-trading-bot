from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.drawdown_periods as drawdown
from trading_bot.research.drawdown_periods import generate_drawdown_period_report


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


def curve_rows(strategy_name: str, values: list[float]) -> list[dict[str, object]]:
    return [
        {
            "date": f"2024-01-{index + 1:02d}",
            "period": "full_period",
            "strategy_name": strategy_name,
            "equity": value,
            "drawdown_pct": "",
        }
        for index, value in enumerate(values)
    ]


def simple_curve_rows(values: list[float]) -> list[dict[str, object]]:
    return [
        {"date": f"2024-01-{index + 1:02d}", "equity": value}
        for index, value in enumerate(values)
    ]


def main() -> int:
    failures: list[str] = []

    if set(drawdown.TARGET_STRATEGIES) != {
        "buy_and_hold_baseline",
        "sma_50_200_trend",
        "monthly_etf_momentum_rotation",
        "adaptive_risk_on_off_momentum",
        "fifty_two_week_high_breakout",
    }:
        failures.append("drawdown report should not add or remove target strategies")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "strategy_portfolio_equity_curves.csv",
            [
                *curve_rows("buy_and_hold_baseline", [100, 120, 90, 80, 121]),
                *curve_rows("sma_50_200_trend", [100, 110, 100, 99, 111]),
            ],
        )
        write_csv(
            data_dir / "etf_rotation_equity_curve.csv",
            simple_curve_rows([100, 105, 103, 101, 106]),
        )
        write_csv(
            data_dir / "adaptive_momentum_equity_curve.csv",
            simple_curve_rows([100, 120, 95, 85, 86]),
        )

        result = generate_drawdown_period_report(data_dir)
        if not result.output_path.exists():
            failures.append("drawdown_period_report.csv was not created")
        rows_by_strategy: dict[str, list[dict[str, object]]] = {}
        for row in result.rows:
            rows_by_strategy.setdefault(str(row["strategy_name"]), []).append(row)

        benchmark = rows_by_strategy["buy_and_hold_baseline"][0]
        if round(float(benchmark["drawdown_depth_pct"]), 4) != 33.3333:
            failures.append(f"benchmark worst drawdown detection failed: {benchmark['drawdown_depth_pct']}")
        if benchmark["peak_date"] != "2024-01-02" or benchmark["trough_date"] != "2024-01-04":
            failures.append("benchmark peak/trough dates failed")
        if benchmark["recovery_date"] != "2024-01-05" or benchmark["is_recovered"] is not True:
            failures.append("benchmark recovery handling failed")

        trend = rows_by_strategy["sma_50_200_trend"][0]
        if trend["drawdown_status"] != "reduced_vs_benchmark":
            failures.append("active reduced drawdown status failed")
        if round(float(trend["benchmark_drawdown_depth_pct"]), 4) != 33.3333:
            failures.append("benchmark overlap depth failed")
        if round(float(trend["drawdown_reduction_vs_benchmark_pct"]), 4) <= 0:
            failures.append("drawdown reduction should be positive for reduced trend fixture")
        if round(float(trend["drawdown_depth_pct"]), 4) != 10.0:
            failures.append("strategy drawdown depth should remain unchanged in CSV")
        if round(float(trend["drawdown_reduction_vs_benchmark_pct"]), 4) != 23.3333:
            failures.append("drawdown reduction value failed")

        adaptive = rows_by_strategy["adaptive_risk_on_off_momentum"][0]
        if adaptive["recovery_date"] != "not_recovered" or adaptive["is_recovered"] is not False:
            failures.append("unrecovered adaptive drawdown handling failed")
        etf = rows_by_strategy["monthly_etf_momentum_rotation"][0]
        if round(float(etf["drawdown_depth_pct"]), 4) != 3.8095:
            failures.append("ETF strategy drawdown depth should remain unchanged in CSV")
        if round(float(etf["drawdown_reduction_vs_benchmark_pct"]), 4) != 29.5238:
            failures.append("ETF drawdown reduction value failed")

        breakout = rows_by_strategy["fifty_two_week_high_breakout"][0]
        if breakout["drawdown_status"] != "insufficient_data":
            failures.append("missing breakout curve should produce insufficient_data row")

        for row in result.rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"safety flags failed for {row['strategy_name']}")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != drawdown.DRAWDOWN_PERIOD_COLUMNS:
                failures.append("drawdown report columns changed unexpectedly")
        summary = "\n".join(result.summary_lines)
        if "worst benchmark drawdown period: buy_and_hold_baseline" not in summary:
            failures.append("benchmark summary failed")
        if "best drawdown reduction versus benchmark" not in summary:
            failures.append("drawdown reduction summary missing")
        expected_reduction_line = (
            "best drawdown reduction versus benchmark: "
            "monthly_etf_momentum_rotation 2024-01-02->2024-01-04 "
            "(reduction=29.5238 percentage points; strategy_drawdown=3.8095%; benchmark_drawdown=33.3333%)"
        )
        if expected_reduction_line not in summary:
            failures.append("drawdown reduction summary should print reduction, strategy drawdown, and benchmark drawdown separately")
        if "best drawdown reduction versus benchmark: monthly_etf_momentum_rotation 2024-01-02->2024-01-04 (3.8095%)" in summary:
            failures.append("drawdown reduction summary should not print strategy drawdown as the reduction value")
        if "not execution approval" not in summary:
            failures.append("execution approval warning missing")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "strategy_portfolio_equity_curves.csv",
            curve_rows("buy_and_hold_baseline", [100]),
        )
        result = generate_drawdown_period_report(data_dir)
        rows = {row["strategy_name"]: row for row in result.rows}
        if rows["buy_and_hold_baseline"]["drawdown_status"] != "insufficient_data":
            failures.append("single-row benchmark curve should be insufficient_data")

    source = inspect.getsource(drawdown)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"drawdown report references forbidden term: {term}")

    if failures:
        print("Drawdown period report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Drawdown period report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
