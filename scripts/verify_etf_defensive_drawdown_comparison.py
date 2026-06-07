from __future__ import annotations

import csv
import inspect
import sys
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.etf_defensive_drawdowns as report
from trading_bot.research.etf_defensive_drawdowns import generate_etf_defensive_drawdown_comparison


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
        write_csv(data_dir / "etf_rotation_equity_curve.csv", equity_rows([100, 120, 90, 130, 140, 150, 155, 160, 110, 90]))
        write_csv(
            data_dir / "vol_managed_etf_equity_curve.csv",
            vol_equity_rows([100, 120, 100, 130, 140, 150, 155, 160, 110, 100]),
        )
        write_csv(data_dir / "etf_rotation_robustness_report.csv", rotation_robustness_rows())
        write_csv(data_dir / "vol_managed_etf_robustness_report.csv", vol_robustness_rows())

        result = generate_etf_defensive_drawdown_comparison(data_dir)
        if not result.output_path.exists():
            failures.append("etf_defensive_drawdown_comparison.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != report.ETF_DEFENSIVE_DRAWDOWN_COLUMNS:
                failures.append("ETF defensive drawdown comparison columns changed unexpectedly")

        rows = {(row["strategy_name"], row["comparison_period"]): row for row in result.rows}
        etf_full = rows[("monthly_etf_momentum_rotation", "full_period_worst_drawdown")]
        vol_full = rows[("volatility_managed_dual_momentum_etf", "full_period_worst_drawdown")]
        vol_80 = rows[("volatility_managed_dual_momentum_etf", "split_80_20_out_of_sample")]

        if etf_full["drawdown_depth_pct"] <= vol_full["drawdown_depth_pct"]:
            failures.append("fixture should show ETF rotation with deeper full-period drawdown than vol-managed")
        if vol_80["interpretation_label"] != "lower_drawdown_but_lower_return":
            failures.append("lower drawdown but weaker split_80_20 metrics should get the tradeoff label")
        if "ETF rotation leads split_80_20 return and risk-adjusted metrics" not in vol_80["interpretation_reason"]:
            failures.append("split_80_20 reason should explain lower-drawdown/lower-return tradeoff")
        if vol_80["split_80_20_oos_calmar"] != 1.2:
            failures.append("vol-managed split_80_20 Calmar context was not included")
        if "ETF rotation leads split_80_20" not in vol_80["fixed_split_context"]:
            failures.append("fixed split context should describe the 80/20 tradeoff")
        summary = "\n".join(result.summary_lines)
        if "split_80_20 comparison" not in summary:
            failures.append("terminal summary should include split_80_20 comparison")
        if "not execution approval" not in summary:
            failures.append("terminal summary should warn this is not execution approval")
        for row in result.rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"safety flags failed for {row['strategy_name']} {row['comparison_period']}")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(data_dir / "etf_rotation_equity_curve.csv", equity_rows([100, 99]))
        result = generate_etf_defensive_drawdown_comparison(data_dir)
        vol_rows = [row for row in result.rows if row["strategy_name"] == "volatility_managed_dual_momentum_etf"]
        if not vol_rows or any(row["interpretation_label"] != "insufficient_data" for row in vol_rows):
            failures.append("missing vol-managed equity curve should produce insufficient_data rows")

    source = inspect.getsource(report)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"ETF defensive drawdown comparison references forbidden term: {term}")
    if "crypto_" in source:
        failures.append("ETF defensive drawdown comparison should not add or reference crypto logic")

    if failures:
        print("ETF defensive drawdown comparison verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ETF defensive drawdown comparison verification passed.")
    return 0


def equity_rows(values: list[float]) -> list[dict[str, object]]:
    start = date(2020, 1, 1)
    return [
        {
            "date": (start + timedelta(days=index)).isoformat(),
            "equity": value,
        }
        for index, value in enumerate(values)
    ]


def vol_equity_rows(values: list[float]) -> list[dict[str, object]]:
    rows = []
    for row in equity_rows(values):
        rows.append(
            {
                "date": row["date"],
                "strategy_name": "volatility_managed_dual_momentum_etf",
                "ticker_or_portfolio": "portfolio",
                "period": "full_period",
                "equity": row["equity"],
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
            }
        )
    return rows


def rotation_robustness_rows() -> list[dict[str, object]]:
    return [
        robustness_row("monthly_etf_momentum_rotation", split, calmar)
        for split, calmar in [
            ("split_60_40", 0.9),
            ("split_70_30", 1.0),
            ("split_80_20", 1.6),
        ]
    ]


def vol_robustness_rows() -> list[dict[str, object]]:
    rows = []
    for split, calmar in [
        ("split_60_40", 1.1),
        ("split_70_30", 1.3),
        ("split_80_20", 1.2),
    ]:
        row = robustness_row("volatility_managed_dual_momentum_etf", split, calmar)
        row.update(
            {
                "benchmark_strategy_name": "monthly_etf_momentum_rotation",
                "cagr_gap_vs_benchmark_oos": 1.0 if split != "split_80_20" else -1.0,
                "sharpe_gap_vs_benchmark_oos": 0.1 if split != "split_80_20" else -0.1,
                "calmar_gap_vs_benchmark_oos": 0.2 if split != "split_80_20" else -0.2,
                "drawdown_reduction_vs_benchmark_oos": 2.0,
                "comparison_splits_won": 2,
                "comparison_splits_lost": 1,
            }
        )
        rows.append(row)
    return rows


def robustness_row(strategy_name: str, split_name: str, calmar: float) -> dict[str, object]:
    return {
        "created_at": "2026-01-01T00:00:00+00:00",
        "strategy_name": strategy_name,
        "ticker_or_portfolio": "portfolio",
        "split_name": split_name,
        "in_sample_fraction": split_name.replace("split_", "").replace("_", "."),
        "out_of_sample_cagr_pct": 10.0,
        "out_of_sample_sharpe": 1.0,
        "out_of_sample_max_drawdown_pct": 10.0,
        "out_of_sample_calmar": calmar,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
