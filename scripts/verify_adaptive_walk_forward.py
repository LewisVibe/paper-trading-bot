from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bot
import trading_bot.strategies.adaptive as adaptive
from trading_bot.research.walk_forward import generate_walk_forward_report


FORBIDDEN_TERMS = [
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

    expected_parameters = {
        "ADAPTIVE_MOMENTUM_LOOKBACKS": (63, 126, 252),
        "ADAPTIVE_VOLATILITY_LOOKBACK": 63,
        "ADAPTIVE_VOLATILITY_PENALTY": 0.25,
        "ADAPTIVE_TREND_WINDOW": 200,
        "ADAPTIVE_TOP_N": 3,
    }
    for name, expected in expected_parameters.items():
        actual = getattr(adaptive, name, getattr(bot, name, None))
        if actual != expected:
            failures.append(f"adaptive parameter changed: {name}={actual!r}")

    equity_curve = [
        {"date": f"2024-01-{day:02d}", "equity": 1000.0 + (day * 10.0)}
        for day in range(1, 11)
    ]
    trades = [
        {"date": "2024-01-03"},
        {"date": "2024-01-08"},
        {"date": "2024-01-09"},
    ]
    benchmark_curves = {
        "spy": [1000.0 + (day * 8.0) for day in range(1, 11)],
        "qqq": [1000.0 + (day * 9.0) for day in range(1, 11)],
        "equal_weight": [1000.0 + (day * 7.0) for day in range(1, 11)],
    }
    rows = bot.build_adaptive_momentum_result_rows(
        equity_curve,
        trades,
        1000.0,
        bot.ADAPTIVE_TOP_N,
        5,
        bot.MIN_REBALANCE_NOTIONAL,
        benchmark_curves,
    )
    rows_by_period = {row["period"]: row for row in rows}
    if set(rows_by_period) != {"full_period", "in_sample", "out_of_sample"}:
        failures.append(f"adaptive rows should include all periods, got {sorted(rows_by_period)}")
    for period, row in rows_by_period.items():
        if row["strategy_name"] != "adaptive_risk_on_off_momentum":
            failures.append(f"unexpected strategy name for {period}")
        if row["source_file"] != "adaptive_momentum_results.csv" or row["ticker_or_portfolio"] != "portfolio":
            failures.append(f"adaptive row should be portfolio-level and source-labelled for {period}")
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"adaptive safety flags failed for {period}")
    if rows_by_period["in_sample"]["number_of_trades"] != 1:
        failures.append("in-sample adaptive trade count should be sliced by date")
    if rows_by_period["out_of_sample"]["number_of_trades"] != 2:
        failures.append("out-of-sample adaptive trade count should be sliced by date")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(data_dir / "adaptive_momentum_results.csv", rows)
        result = generate_walk_forward_report(data_dir)
        adaptive_row = next(
            row for row in result.rows if row["strategy_name"] == "adaptive_risk_on_off_momentum"
        )
        if adaptive_row["has_in_sample"] is not True or adaptive_row["has_out_of_sample"] is not True:
            failures.append("walk-forward report should pair adaptive in/out rows")
        if adaptive_row["walk_forward_view"] != "portfolio_active":
            failures.append("adaptive walk-forward view should be portfolio_active")
        if adaptive_row["robustness_label"] == "insufficient_period_data":
            failures.append("adaptive should no longer be insufficient when split rows exist")

    source = "\n".join(
        inspect.getsource(function)
        for function in [
            bot.build_adaptive_momentum_result_rows,
            bot.adaptive_momentum_period_slices,
            bot.build_adaptive_momentum_period_benchmark_metrics,
            bot.build_adaptive_momentum_result_row,
        ]
    )
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"adaptive walk-forward helpers reference forbidden term: {term}")

    if failures:
        print("Adaptive walk-forward verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Adaptive walk-forward verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
