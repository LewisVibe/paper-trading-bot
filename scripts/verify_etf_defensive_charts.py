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

import trading_bot.research.etf_defensive_charts as charts
from trading_bot.research.etf_defensive_charts import (
    DRAWDOWN_CHART_FILENAME,
    EQUITY_CHART_FILENAME,
    plot_etf_defensive_comparison_charts,
)


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
        chart_dir = data_dir / "charts"
        write_csv(data_dir / "etf_rotation_equity_curve.csv", equity_rows([100, 105, 103, 110, 108, 115]))
        write_csv(data_dir / "vol_managed_etf_equity_curve.csv", vol_equity_rows([100, 104, 104, 109, 107, 113]))
        result = plot_etf_defensive_comparison_charts(data_dir=data_dir, chart_dir=chart_dir)
        expected_paths = [
            chart_dir / EQUITY_CHART_FILENAME,
            chart_dir / DRAWDOWN_CHART_FILENAME,
        ]
        if result.chart_paths != expected_paths:
            failures.append("chart result paths changed unexpectedly")
        for path in expected_paths:
            if not path.exists() or path.stat().st_size <= 0:
                failures.append(f"expected chart file was not created: {path}")
        summary = "\n".join(result.summary_lines)
        if "Research/display only" not in summary or "not execution approval" not in summary:
            failures.append("chart summary should clearly deny execution approval")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        try:
            plot_etf_defensive_comparison_charts(data_dir=data_dir, chart_dir=data_dir / "charts")
            failures.append("missing chart inputs should fail clearly")
        except RuntimeError as exc:
            message = str(exc)
            for command in [
                "python bot.py --etf-rotation-backtest",
                "python bot.py --vol-managed-etf-backtest",
                "python bot.py --etf-defensive-drawdown-comparison",
            ]:
                if command not in message:
                    failures.append(f"missing-input message should mention {command}")

    source = inspect.getsource(charts)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"ETF defensive charting references forbidden term: {term}")
    if "execution_approved=True" in source:
        failures.append("ETF defensive charting must not introduce execution approval")

    if failures:
        print("ETF defensive chart verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ETF defensive chart verification passed.")
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


if __name__ == "__main__":
    raise SystemExit(main())
