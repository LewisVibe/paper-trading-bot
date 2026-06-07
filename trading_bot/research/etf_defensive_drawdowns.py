"""Saved-data-only ETF defensive drawdown comparison report."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research.drawdown_periods import days_between, identify_drawdown_periods


ETF_ROTATION = "monthly_etf_momentum_rotation"
VOL_MANAGED = "volatility_managed_dual_momentum_etf"

ETF_DEFENSIVE_DRAWDOWN_COLUMNS = [
    "created_at",
    "comparison_period",
    "strategy_name",
    "peak_date",
    "trough_date",
    "recovery_date",
    "drawdown_depth_pct",
    "drawdown_duration_days",
    "recovery_duration_days",
    "is_recovered",
    "matching_other_strategy_drawdown_pct",
    "drawdown_advantage_pct",
    "fixed_split_context",
    "split_60_40_oos_calmar",
    "split_70_30_oos_calmar",
    "split_80_20_oos_calmar",
    "interpretation_label",
    "interpretation_reason",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class EtfDefensiveDrawdownComparisonResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def generate_etf_defensive_drawdown_comparison(
    data_dir: Path | str = "data",
    output_filename: str = "etf_defensive_drawdown_comparison.csv",
) -> EtfDefensiveDrawdownComparisonResult:
    data_path = Path(data_dir)
    warnings: list[str] = []
    curves = load_etf_defensive_curves(data_path, warnings)
    rotation_context = load_split_context(data_path / "etf_rotation_robustness_report.csv")
    vol_context = load_split_context(data_path / "vol_managed_etf_robustness_report.csv")
    rows = build_etf_defensive_drawdown_rows(curves, rotation_context, vol_context)
    output_path = data_path / output_filename
    write_etf_defensive_drawdown_comparison(output_path, rows)
    return EtfDefensiveDrawdownComparisonResult(
        output_path=output_path,
        rows=rows,
        warnings=warnings,
        summary_lines=build_etf_defensive_drawdown_summary(rows),
    )


def load_etf_defensive_curves(data_path: Path, warnings: list[str]) -> dict[str, dict[str, Any]]:
    sources = {
        ETF_ROTATION: data_path / "etf_rotation_equity_curve.csv",
        VOL_MANAGED: data_path / "vol_managed_etf_equity_curve.csv",
    }
    curves: dict[str, dict[str, Any]] = {}
    for strategy_name, path in sources.items():
        if not path.exists():
            warnings.append(f"Missing equity curve file: {path}")
            continue
        points = []
        for row in read_csv_rows(path):
            date = row.get("date", "")
            equity = number_or_none(row.get("equity", ""))
            if date and equity is not None:
                points.append({"date": date, "equity": equity})
        points.sort(key=lambda point: point["date"])
        curves[strategy_name] = {
            "source_file": path.name,
            "strategy_name": strategy_name,
            "points": points,
        }
    return curves


def load_split_context(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    context: dict[str, dict[str, str]] = {}
    for row in read_csv_rows(path):
        split_name = row.get("split_name", "")
        if split_name:
            context[split_name] = row
    return context


def build_etf_defensive_drawdown_rows(
    curves: dict[str, dict[str, Any]],
    rotation_context: dict[str, dict[str, str]],
    vol_context: dict[str, dict[str, str]],
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    period_specs = [
        ("full_period_worst_drawdown", None),
        ("split_80_20_out_of_sample", 0.8),
    ]
    for comparison_period, split_fraction in period_specs:
        period_curves = {
            strategy: slice_curve(curve.get("points", []), split_fraction)
            for strategy, curve in curves.items()
        }
        for strategy_name in [ETF_ROTATION, VOL_MANAGED]:
            points = period_curves.get(strategy_name, [])
            other_name = VOL_MANAGED if strategy_name == ETF_ROTATION else ETF_ROTATION
            other_points = period_curves.get(other_name, [])
            if len(points) < 2:
                rows.append(insufficient_row(timestamp, comparison_period, strategy_name))
                continue
            rows.append(
                build_strategy_period_row(
                    timestamp,
                    comparison_period,
                    strategy_name,
                    points,
                    other_points,
                    rotation_context,
                    vol_context,
                )
            )
    return rows


def slice_curve(points: list[dict[str, Any]], split_fraction: float | None) -> list[dict[str, Any]]:
    if split_fraction is None:
        return list(points)
    if len(points) < 2:
        return []
    split_index = max(1, min(len(points) - 1, int(len(points) * split_fraction)))
    return list(points[split_index:])


def build_strategy_period_row(
    created_at: str,
    comparison_period: str,
    strategy_name: str,
    points: list[dict[str, Any]],
    other_points: list[dict[str, Any]],
    rotation_context: dict[str, dict[str, str]],
    vol_context: dict[str, dict[str, str]],
) -> dict[str, Any]:
    periods = identify_drawdown_periods(points)
    if periods:
        period = periods[0]
    else:
        first_date = str(points[0]["date"])
        period = {
            "peak_date": first_date,
            "trough_date": first_date,
            "recovery_date": first_date,
            "drawdown_depth_pct": 0.0,
            "is_recovered": True,
        }
    depth = round(float(period["drawdown_depth_pct"]), 4)
    other_depth = matching_drawdown_depth(other_points, period["peak_date"], period["trough_date"])
    advantage = round(float(other_depth) - depth, 4) if isinstance(other_depth, (int, float)) else ""
    split_context = fixed_split_context(rotation_context, vol_context)
    label, reason = interpret_drawdown_tradeoff(strategy_name, comparison_period, advantage, rotation_context, vol_context)
    recovery_date = period.get("recovery_date") or "not_recovered"
    return {
        "created_at": created_at,
        "comparison_period": comparison_period,
        "strategy_name": strategy_name,
        "peak_date": period["peak_date"],
        "trough_date": period["trough_date"],
        "recovery_date": recovery_date,
        "drawdown_depth_pct": depth,
        "drawdown_duration_days": days_between(period["peak_date"], period["trough_date"]),
        "recovery_duration_days": days_between(period["trough_date"], period["recovery_date"]) if period.get("recovery_date") else "",
        "is_recovered": bool(period.get("is_recovered")),
        "matching_other_strategy_drawdown_pct": other_depth,
        "drawdown_advantage_pct": advantage,
        "fixed_split_context": split_context,
        "split_60_40_oos_calmar": split_calmar(strategy_name, "split_60_40", rotation_context, vol_context),
        "split_70_30_oos_calmar": split_calmar(strategy_name, "split_70_30", rotation_context, vol_context),
        "split_80_20_oos_calmar": split_calmar(strategy_name, "split_80_20", rotation_context, vol_context),
        "interpretation_label": label,
        "interpretation_reason": reason,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def matching_drawdown_depth(points: list[dict[str, Any]], start_date: str, end_date: str) -> float | str:
    window = [point for point in points if start_date <= str(point["date"]) <= end_date]
    if len(window) < 2:
        return ""
    series_peak = float(window[0]["equity"])
    worst_depth = 0.0
    for point in window:
        equity = float(point["equity"])
        series_peak = max(series_peak, equity)
        if series_peak > 0:
            worst_depth = max(worst_depth, ((series_peak - equity) / series_peak) * 100)
    return round(worst_depth, 4)


def fixed_split_context(
    rotation_context: dict[str, dict[str, str]],
    vol_context: dict[str, dict[str, str]],
) -> str:
    vol_80 = vol_context.get("split_80_20", {})
    if not vol_80:
        return "fixed split comparison unavailable"
    wins = vol_80.get("comparison_splits_won", "")
    losses = vol_80.get("comparison_splits_lost", "")
    calmar_gap = number_or_none(vol_80.get("calmar_gap_vs_benchmark_oos", ""))
    cagr_gap = number_or_none(vol_80.get("cagr_gap_vs_benchmark_oos", ""))
    sharpe_gap = number_or_none(vol_80.get("sharpe_gap_vs_benchmark_oos", ""))
    drawdown_reduction = number_or_none(vol_80.get("drawdown_reduction_vs_benchmark_oos", ""))
    if all(value is not None for value in [calmar_gap, cagr_gap, sharpe_gap, drawdown_reduction]):
        if calmar_gap < 0 and cagr_gap < 0 and sharpe_gap < 0 and drawdown_reduction > 0:
            return (
                f"vol-managed wins {wins} and loses {losses} fixed splits; "
                "ETF rotation leads split_80_20 CAGR/Sharpe/Calmar while vol-managed has lower drawdown"
            )
    rotation_80 = rotation_context.get("split_80_20", {})
    if rotation_80:
        return f"split_80_20 comparison available; ETF rotation Calmar={rotation_80.get('out_of_sample_calmar', '')}"
    return "fixed split comparison available"


def split_calmar(
    strategy_name: str,
    split_name: str,
    rotation_context: dict[str, dict[str, str]],
    vol_context: dict[str, dict[str, str]],
) -> float | str:
    source = rotation_context if strategy_name == ETF_ROTATION else vol_context
    value = number_or_none(source.get(split_name, {}).get("out_of_sample_calmar", ""))
    return round(value, 4) if value is not None else ""


def interpret_drawdown_tradeoff(
    strategy_name: str,
    comparison_period: str,
    advantage: float | str,
    rotation_context: dict[str, dict[str, str]],
    vol_context: dict[str, dict[str, str]],
) -> tuple[str, str]:
    if advantage == "":
        return "insufficient_data", "Missing matching strategy drawdown window for comparison."
    if abs(float(advantage)) < 0.5:
        return "similar_drawdown", "Drawdown profile was similar to the paired defensive strategy."
    if float(advantage) < 0:
        return "worse_drawdown_profile", "Drawdown was worse than the paired defensive strategy over the matching window."
    if comparison_period == "split_80_20_out_of_sample" and strategy_name == VOL_MANAGED:
        vol_80 = vol_context.get("split_80_20", {})
        if negative_metric_gaps(vol_80):
            return (
                "lower_drawdown_but_lower_return",
                "Vol-managed has lower drawdown, but ETF rotation leads split_80_20 return and risk-adjusted metrics.",
            )
    if comparison_period == "split_80_20_out_of_sample" and strategy_name == ETF_ROTATION:
        vol_80 = vol_context.get("split_80_20", {})
        if negative_metric_gaps(vol_80):
            return (
                "better_drawdown_and_return",
                "ETF rotation led split_80_20 return and risk-adjusted metrics, while vol-managed was more defensive on drawdown.",
            )
    return "better_drawdown_and_return", "Drawdown was lower than the paired defensive strategy over the matching window."


def negative_metric_gaps(row: dict[str, str]) -> bool:
    return all(
        (number_or_none(row.get(column, "")) or 0.0) < 0
        for column in [
            "cagr_gap_vs_benchmark_oos",
            "sharpe_gap_vs_benchmark_oos",
            "calmar_gap_vs_benchmark_oos",
        ]
    )


def insufficient_row(created_at: str, comparison_period: str, strategy_name: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "comparison_period": comparison_period,
        "strategy_name": strategy_name,
        "peak_date": "",
        "trough_date": "",
        "recovery_date": "",
        "drawdown_depth_pct": "",
        "drawdown_duration_days": "",
        "recovery_duration_days": "",
        "is_recovered": "",
        "matching_other_strategy_drawdown_pct": "",
        "drawdown_advantage_pct": "",
        "fixed_split_context": "insufficient saved equity curve data",
        "split_60_40_oos_calmar": "",
        "split_70_30_oos_calmar": "",
        "split_80_20_oos_calmar": "",
        "interpretation_label": "insufficient_data",
        "interpretation_reason": "Missing or insufficient saved equity curve data.",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def write_etf_defensive_drawdown_comparison(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=ETF_DEFENSIVE_DRAWDOWN_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in ETF_DEFENSIVE_DRAWDOWN_COLUMNS})


def build_etf_defensive_drawdown_summary(rows: list[dict[str, Any]]) -> list[str]:
    etf_worst = row_for(rows, ETF_ROTATION, "full_period_worst_drawdown")
    vol_worst = row_for(rows, VOL_MANAGED, "full_period_worst_drawdown")
    etf_80 = row_for(rows, ETF_ROTATION, "split_80_20_out_of_sample")
    vol_80 = row_for(rows, VOL_MANAGED, "split_80_20_out_of_sample")
    lines = [
        "ETF defensive drawdown comparison summary",
        "Research-only drawdown comparison. This is not execution approval.",
        "ETF rotation worst drawdown: " + drawdown_label(etf_worst),
        "Vol-managed ETF worst drawdown: " + drawdown_label(vol_worst),
        "split_80_20 comparison: " + split_80_label(etf_80, vol_80),
        "challenge assessment: lower drawdown alone is not enough to displace ETF rotation while vol-managed remains split-sensitive.",
        "Warning: research_only=True, preview_only=True, and execution_approved=False for every row.",
    ]
    return lines


def row_for(rows: list[dict[str, Any]], strategy_name: str, comparison_period: str) -> dict[str, Any] | None:
    return next(
        (
            row for row in rows
            if row.get("strategy_name") == strategy_name and row.get("comparison_period") == comparison_period
        ),
        None,
    )


def drawdown_label(row: dict[str, Any] | None) -> str:
    if not row or row.get("interpretation_label") == "insufficient_data":
        return "unavailable"
    return f"{row.get('peak_date')}->{row.get('trough_date')} ({row.get('drawdown_depth_pct')}%)"


def split_80_label(etf_row: dict[str, Any] | None, vol_row: dict[str, Any] | None) -> str:
    if not etf_row or not vol_row:
        return "unavailable"
    return (
        f"ETF rotation drawdown={etf_row.get('drawdown_depth_pct')}%, "
        f"vol-managed drawdown={vol_row.get('drawdown_depth_pct')}%; "
        "saved robustness context says ETF rotation leads CAGR/Sharpe/Calmar while vol-managed has lower drawdown."
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [row for row in reader if any((value or "").strip() for value in row.values())]


def number_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
