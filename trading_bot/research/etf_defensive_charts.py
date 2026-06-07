"""Saved-CSV-only charts for ETF defensive strategy comparison."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ETF_ROTATION = "monthly_etf_momentum_rotation"
VOL_MANAGED = "volatility_managed_dual_momentum_etf"
EQUITY_CHART_FILENAME = "etf_defensive_equity_comparison.png"
DRAWDOWN_CHART_FILENAME = "etf_defensive_drawdown_comparison.png"


@dataclass
class EtfDefensiveChartResult:
    chart_paths: list[Path]
    summary_lines: list[str]


def plot_etf_defensive_comparison_charts(
    data_dir: Path | str = "data",
    chart_dir: Path | str | None = None,
) -> EtfDefensiveChartResult:
    data_path = Path(data_dir)
    chart_path = Path(chart_dir) if chart_dir is not None else data_path / "charts"
    curves = load_required_curves(data_path)
    chart_path.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for ETF defensive charts. Install project requirements, then try again."
        ) from exc

    equity_path = chart_path / EQUITY_CHART_FILENAME
    drawdown_path = chart_path / DRAWDOWN_CHART_FILENAME
    write_equity_chart(plt, curves, equity_path)
    write_drawdown_chart(plt, curves, drawdown_path)
    chart_paths = [equity_path, drawdown_path]
    return EtfDefensiveChartResult(
        chart_paths=chart_paths,
        summary_lines=[
            "ETF defensive comparison charts",
            "Research/display only. This is not execution approval.",
            f"Saved equity comparison chart to {equity_path}",
            f"Saved drawdown comparison chart to {drawdown_path}",
        ],
    )


def load_required_curves(data_path: Path) -> dict[str, list[dict[str, Any]]]:
    required = {
        ETF_ROTATION: data_path / "etf_rotation_equity_curve.csv",
        VOL_MANAGED: data_path / "vol_managed_etf_equity_curve.csv",
    }
    missing = [path for path in required.values() if not path.exists()]
    if missing:
        missing_labels = ", ".join(str(path) for path in missing)
        raise RuntimeError(
            "Missing required saved ETF defensive chart input(s): "
            f"{missing_labels}. Run python bot.py --etf-rotation-backtest, "
            "python bot.py --vol-managed-etf-backtest, and "
            "python bot.py --etf-defensive-drawdown-comparison first."
        )

    curves: dict[str, list[dict[str, Any]]] = {}
    for strategy_name, path in required.items():
        rows = load_equity_curve(path)
        if len(rows) < 2:
            raise RuntimeError(
                f"{path} does not contain enough saved equity rows. Run the required research backtests first."
            )
        curves[strategy_name] = rows
    return curves


def load_equity_curve(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or "date" not in reader.fieldnames or "equity" not in reader.fieldnames:
            raise RuntimeError(f"{path} does not have the expected date/equity columns.")
        for row in reader:
            date_value = parse_date(row.get("date", ""))
            equity = number_or_none(row.get("equity", ""))
            if date_value is not None and equity is not None:
                rows.append({"date": date_value, "equity": equity})
    rows.sort(key=lambda row: row["date"])
    return rows


def write_equity_chart(plt: Any, curves: dict[str, list[dict[str, Any]]], output_path: Path) -> None:
    figure = plt.figure(figsize=(11, 6))
    for strategy_name, rows in curves.items():
        plt.plot(
            [row["date"] for row in rows],
            [row["equity"] for row in rows],
            label=strategy_name,
        )
    plt.title("ETF Defensive Equity Comparison")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(output_path, dpi=140)
    plt.close(figure)


def write_drawdown_chart(plt: Any, curves: dict[str, list[dict[str, Any]]], output_path: Path) -> None:
    figure = plt.figure(figsize=(11, 6))
    for strategy_name, rows in curves.items():
        drawdown_rows = drawdown_curve(rows)
        plt.plot(
            [row["date"] for row in drawdown_rows],
            [row["drawdown_pct"] for row in drawdown_rows],
            label=strategy_name,
        )
    plt.title("ETF Defensive Drawdown Comparison")
    plt.xlabel("Date")
    plt.ylabel("Drawdown %")
    plt.grid(True, alpha=0.3)
    plt.legend()
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(output_path, dpi=140)
    plt.close(figure)


def drawdown_curve(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    peak = float(rows[0]["equity"])
    curve: list[dict[str, Any]] = []
    for row in rows:
        equity = float(row["equity"])
        peak = max(peak, equity)
        drawdown = ((equity - peak) / peak) * 100 if peak > 0 else 0.0
        curve.append({"date": row["date"], "drawdown_pct": drawdown})
    return curve


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def number_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
