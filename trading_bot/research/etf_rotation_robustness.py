"""Saved-data-only fixed-split robustness report for ETF rotation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from trading_bot.research.backtesting import calculate_cagr_pct, calculate_max_drawdown, calculate_sharpe_ratio
from trading_bot.research.vol_managed_etf_robustness import FIXED_SPLITS, fixed_split_index


ETF_ROTATION_ROBUSTNESS_COLUMNS = [
    "created_at",
    "strategy_name",
    "ticker_or_portfolio",
    "split_name",
    "in_sample_fraction",
    "out_of_sample_cagr_pct",
    "out_of_sample_sharpe",
    "out_of_sample_max_drawdown_pct",
    "out_of_sample_calmar",
    "out_of_sample_trade_count",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class EtfRotationRobustnessResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_etf_rotation_robustness_report(
    data_dir: Path | str = "data",
    created_at: str | None = None,
) -> EtfRotationRobustnessResult:
    data_path = Path(data_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    rows = build_etf_rotation_robustness_rows(data_path, created)
    output_path = data_path / "etf_rotation_robustness_report.csv"
    write_rows(output_path, rows)
    return EtfRotationRobustnessResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, output_path),
    )


def build_etf_rotation_robustness_rows(data_path: Path, created_at: str) -> list[dict[str, Any]]:
    equity_rows = read_csv_rows(data_path / "etf_rotation_equity_curve.csv")
    trade_rows = read_csv_rows(data_path / "etf_rotation_trades.csv")
    if not equity_rows:
        return [
            insufficient_row(created_at, split_name, fraction, "ETF rotation equity curve is unavailable")
            for split_name, fraction in FIXED_SPLITS
        ]
    dates = [str(row["date"]) for row in equity_rows]
    equity_curve = [parse_float(row.get("equity")) for row in equity_rows]
    rows: list[dict[str, Any]] = []
    for split_name, fraction in FIXED_SPLITS:
        split_index = fixed_split_index(equity_curve, fraction)
        oos_curve = equity_curve[split_index:]
        trade_count = count_trades_for_oos(trade_rows, dates, split_index)
        rows.append(robustness_row(created_at, split_name, fraction, oos_curve, trade_count))
    return rows


def robustness_row(
    created_at: str,
    split_name: str,
    fraction: Decimal,
    oos_curve: list[float],
    trade_count: int,
) -> dict[str, Any]:
    metrics = metrics_for_curve(oos_curve)
    return {
        "created_at": created_at,
        "strategy_name": "monthly_etf_momentum_rotation",
        "ticker_or_portfolio": "portfolio",
        "split_name": split_name,
        "in_sample_fraction": fraction,
        "out_of_sample_cagr_pct": metrics["cagr_pct"],
        "out_of_sample_sharpe": metrics["sharpe_ratio"],
        "out_of_sample_max_drawdown_pct": metrics["max_drawdown_pct"],
        "out_of_sample_calmar": metrics["calmar_ratio"],
        "out_of_sample_trade_count": trade_count,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def insufficient_row(created_at: str, split_name: str, fraction: Decimal, reason: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": "monthly_etf_momentum_rotation",
        "ticker_or_portfolio": "portfolio",
        "split_name": split_name,
        "in_sample_fraction": fraction,
        "out_of_sample_cagr_pct": "",
        "out_of_sample_sharpe": "",
        "out_of_sample_max_drawdown_pct": "",
        "out_of_sample_calmar": "",
        "out_of_sample_trade_count": 0,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "robustness_reason": reason,
    }


def metrics_for_curve(curve: list[float]) -> dict[str, float]:
    if not curve:
        return {"cagr_pct": 0.0, "sharpe_ratio": 0.0, "max_drawdown_pct": 0.0, "calmar_ratio": 0.0}
    cagr = calculate_cagr_pct(curve[0], curve[-1], len(curve))
    sharpe = calculate_sharpe_ratio(curve)
    max_drawdown = calculate_max_drawdown(curve) * 100
    calmar = cagr / abs(max_drawdown) if max_drawdown else 0.0
    return {
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_drawdown,
        "calmar_ratio": calmar,
    }


def count_trades_for_oos(trades: list[dict[str, Any]], dates: list[str], split_index: int) -> int:
    if not dates or split_index >= len(dates):
        return 0
    start_date = dates[split_index]
    end_date = dates[-1]
    return sum(1 for row in trades if start_date <= str(row.get("date", "")) <= end_date)


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    return [
        "ETF ROTATION ROBUSTNESS REPORT. RESEARCH ONLY. NOT EXECUTION.",
        "Fixed splits: split_60_40, split_70_30, split_80_20.",
        f"Rows: {len(rows)}",
        "Warning: this is research/reporting only and not execution approval.",
        f"Saved ETF rotation robustness report to {output_path}",
    ]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=ETF_ROTATION_ROBUSTNESS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in ETF_ROTATION_ROBUSTNESS_COLUMNS})
