from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bot
from trading_bot.research.walk_forward import generate_walk_forward_report


FORBIDDEN_TERMS = [
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


def main() -> int:
    failures: list[str] = []

    equity_curve = [
        {"date": f"2020-01-{day:02d}", "equity": 100_000 + (day * 1_000)}
        for day in range(1, 11)
    ]
    trades = [
        {"date": "2020-01-02", "ticker": "SPY"},
        {"date": "2020-01-07", "ticker": "QQQ"},
        {"date": "2020-01-09", "ticker": "IWM"},
    ]
    benchmark_curves = {
        "spy": [100_000 + (day * 900) for day in range(1, 11)],
        "qqq": [100_000 + (day * 800) for day in range(1, 11)],
        "equal_weight": [100_000 + (day * 700) for day in range(1, 11)],
    }

    rows = bot.build_etf_rotation_result_rows(
        equity_curve,
        trades,
        starting_equity=100_000,
        top_n=3,
        universe_size=14,
        min_rebalance_notional=100.0,
        benchmark_curves=benchmark_curves,
    )
    by_period = {row["period"]: row for row in rows}
    expected_periods = {"full_period", "in_sample", "out_of_sample"}
    if set(by_period) != expected_periods:
        failures.append(f"period rows mismatch: {sorted(by_period)}")
    if by_period["full_period"]["ticker_or_portfolio"] != "portfolio":
        failures.append("ETF rotation result rows should be portfolio-level")
    if by_period["full_period"]["source_file"] != "etf_rotation_results.csv":
        failures.append("source_file was not populated for walk-forward pairing")
    if by_period["full_period"]["number_of_trades"] != 3:
        failures.append("full-period trade count failed")
    if by_period["in_sample"]["number_of_trades"] != 2:
        failures.append("in-sample trade count failed")
    if by_period["out_of_sample"]["number_of_trades"] != 1:
        failures.append("out-of-sample trade count failed")
    if by_period["out_of_sample"]["starting_equity"] != equity_curve[7]["equity"]:
        failures.append("70/30 out-of-sample split did not start at the expected row")
    if by_period["full_period"]["turnover_proxy_trades"] != by_period["full_period"]["number_of_trades"]:
        failures.append("turnover proxy should mirror trade count")
    expected_spy_oos_return = ((109_000 - 107_200) / 107_200) * 100
    if round(by_period["out_of_sample"]["spy_buy_hold_total_return_pct"], 6) != round(expected_spy_oos_return, 6):
        failures.append("out-of-sample benchmark return should use the period benchmark starting value")

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(data_dir / "etf_rotation_results.csv", rows)
        result = generate_walk_forward_report(data_dir)
        report_rows = {
            (row["source_file"], row["strategy_name"], row["ticker_or_portfolio"]): row
            for row in result.rows
        }
        etf_key = ("etf_rotation_results.csv", "monthly_etf_momentum_rotation", "portfolio")
        etf_row = report_rows.get(etf_key)
        if etf_row is None:
            failures.append("walk-forward report did not include ETF rotation")
        else:
            if etf_row["has_in_sample"] is not True or etf_row["has_out_of_sample"] is not True:
                failures.append("ETF rotation in/out rows were not paired")
            if etf_row["walk_forward_view"] != "portfolio_active":
                failures.append("ETF rotation should be a portfolio active walk-forward row")
            if etf_row["robustness_label"] == "insufficient_period_data":
                failures.append("ETF rotation should not be marked insufficient when split rows exist")

    checked_sources = "\n".join(
        inspect.getsource(function)
        for function in [
            bot.build_etf_rotation_result_rows,
            bot.etf_rotation_period_slices,
            bot.filter_etf_rotation_trades_for_period,
            bot.build_etf_rotation_result_row,
            bot.build_etf_rotation_period_benchmark_metrics,
        ]
    )
    for term in FORBIDDEN_TERMS:
        if term in checked_sources:
            failures.append(f"ETF rotation walk-forward helpers reference forbidden term: {term}")

    if failures:
        print("ETF rotation walk-forward verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ETF rotation walk-forward verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
