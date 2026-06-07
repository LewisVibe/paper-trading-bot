"""Saved-data-only drawdown period report helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET_STRATEGIES = [
    "buy_and_hold_baseline",
    "sma_50_200_trend",
    "monthly_etf_momentum_rotation",
    "adaptive_risk_on_off_momentum",
    "fifty_two_week_high_breakout",
]

EQUITY_CURVE_SOURCES = [
    "strategy_portfolio_equity_curves.csv",
    "etf_rotation_equity_curve.csv",
    "adaptive_momentum_equity_curve.csv",
]

DRAWDOWN_PERIOD_COLUMNS = [
    "created_at",
    "source_file",
    "strategy_name",
    "ticker_or_portfolio",
    "period",
    "peak_date",
    "trough_date",
    "recovery_date",
    "drawdown_depth_pct",
    "drawdown_duration_days",
    "recovery_duration_days",
    "is_recovered",
    "benchmark_drawdown_depth_pct",
    "drawdown_reduction_vs_benchmark_pct",
    "drawdown_overlap_with_benchmark",
    "drawdown_status",
    "drawdown_reason",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class DrawdownPeriodReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def generate_drawdown_period_report(
    data_dir: Path | str = "data",
    output_filename: str = "drawdown_period_report.csv",
) -> DrawdownPeriodReportResult:
    data_path = Path(data_dir)
    warnings: list[str] = []
    curves = load_drawdown_equity_curves(data_path, warnings)
    rows = build_drawdown_period_rows(curves)
    output_path = data_path / output_filename
    write_drawdown_period_report(output_path, rows)
    return DrawdownPeriodReportResult(
        output_path=output_path,
        rows=rows,
        warnings=warnings,
        summary_lines=build_drawdown_period_summary(rows),
    )


def load_drawdown_equity_curves(
    data_path: Path,
    warnings: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    warnings = warnings if warnings is not None else []
    curves: dict[str, dict[str, Any]] = {}

    portfolio_path = data_path / "strategy_portfolio_equity_curves.csv"
    if portfolio_path.exists():
        for row in read_csv_rows(portfolio_path):
            strategy_name = row.get("strategy_name", "")
            period = row.get("period", "full_period") or "full_period"
            if strategy_name not in TARGET_STRATEGIES or period != "full_period":
                continue
            append_curve_point(curves, strategy_name, portfolio_path.name, period, row)
    else:
        warnings.append(f"Missing equity curve file: {portfolio_path}")

    dedicated_sources = [
        ("monthly_etf_momentum_rotation", data_path / "etf_rotation_equity_curve.csv"),
        ("adaptive_risk_on_off_momentum", data_path / "adaptive_momentum_equity_curve.csv"),
    ]
    for strategy_name, path in dedicated_sources:
        if not path.exists():
            warnings.append(f"Missing equity curve file: {path}")
            continue
        for row in read_csv_rows(path):
            append_curve_point(curves, strategy_name, path.name, "full_period", row)

    for curve in curves.values():
        curve["points"].sort(key=lambda point: point["date"])
    return curves


def append_curve_point(
    curves: dict[str, dict[str, Any]],
    strategy_name: str,
    source_file: str,
    period: str,
    row: dict[str, str],
) -> None:
    date = row.get("date", "")
    equity = number_or_none(row.get("equity", ""))
    if not date or equity is None:
        return
    curves.setdefault(
        strategy_name,
        {
            "source_file": source_file,
            "strategy_name": strategy_name,
            "ticker_or_portfolio": "portfolio",
            "period": period,
            "points": [],
        },
    )["points"].append({"date": date, "equity": equity})


def build_drawdown_period_rows(
    curves: dict[str, dict[str, Any]],
    created_at: str | None = None,
    max_periods_per_strategy: int = 3,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    benchmark_curve = curves.get("buy_and_hold_baseline", {})
    benchmark_series = drawdown_series(benchmark_curve.get("points", []))
    rows: list[dict[str, Any]] = []
    for strategy_name in TARGET_STRATEGIES:
        curve = curves.get(strategy_name)
        if not curve or len(curve.get("points", [])) < 2:
            rows.append(insufficient_drawdown_row(timestamp, strategy_name))
            continue
        periods = identify_drawdown_periods(curve["points"])
        if not periods:
            rows.append(no_drawdown_row(timestamp, curve))
            continue
        for period in periods[:max_periods_per_strategy]:
            rows.append(build_drawdown_period_row(timestamp, curve, period, benchmark_series))
    return rows


def identify_drawdown_periods(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(points) < 2:
        return []

    peak_equity = float(points[0]["equity"])
    peak_date = str(points[0]["date"])
    active: dict[str, Any] | None = None
    periods: list[dict[str, Any]] = []

    for point in points[1:]:
        date = str(point["date"])
        equity = float(point["equity"])
        if equity >= peak_equity:
            if active is not None:
                active["recovery_date"] = date
                active["is_recovered"] = True
                periods.append(active)
                active = None
            peak_equity = equity
            peak_date = date
            continue

        depth_pct = ((peak_equity - equity) / peak_equity) * 100 if peak_equity > 0 else 0.0
        if active is None:
            active = {
                "peak_date": peak_date,
                "trough_date": date,
                "recovery_date": "",
                "peak_equity": peak_equity,
                "trough_equity": equity,
                "drawdown_depth_pct": depth_pct,
                "is_recovered": False,
            }
        elif depth_pct > float(active["drawdown_depth_pct"]):
            active["trough_date"] = date
            active["trough_equity"] = equity
            active["drawdown_depth_pct"] = depth_pct

    if active is not None:
        periods.append(active)

    periods.sort(
        key=lambda period: (
            -float(period["drawdown_depth_pct"]),
            period["peak_date"],
            period["trough_date"],
        )
    )
    return periods


def drawdown_series(points: list[dict[str, Any]]) -> dict[str, float]:
    if not points:
        return {}
    peak = float(points[0]["equity"])
    series: dict[str, float] = {}
    for point in points:
        equity = float(point["equity"])
        peak = max(peak, equity)
        depth = ((peak - equity) / peak) * 100 if peak > 0 else 0.0
        series[str(point["date"])] = depth
    return series


def build_drawdown_period_row(
    created_at: str,
    curve: dict[str, Any],
    period: dict[str, Any],
    benchmark_series: dict[str, float],
) -> dict[str, Any]:
    benchmark_depth, overlap = benchmark_depth_for_period(
        benchmark_series,
        period["peak_date"],
        period["trough_date"],
    )
    depth = round(float(period["drawdown_depth_pct"]), 4)
    reduction = (
        round(float(benchmark_depth) - depth, 4)
        if benchmark_depth != ""
        else ""
    )
    status, reason = classify_drawdown(depth, reduction, curve["strategy_name"], overlap)
    return {
        "created_at": created_at,
        "source_file": curve["source_file"],
        "strategy_name": curve["strategy_name"],
        "ticker_or_portfolio": curve["ticker_or_portfolio"],
        "period": curve["period"],
        "peak_date": period["peak_date"],
        "trough_date": period["trough_date"],
        "recovery_date": period["recovery_date"] or "not_recovered",
        "drawdown_depth_pct": depth,
        "drawdown_duration_days": days_between(period["peak_date"], period["trough_date"]),
        "recovery_duration_days": (
            days_between(period["trough_date"], period["recovery_date"])
            if period["recovery_date"]
            else ""
        ),
        "is_recovered": bool(period["is_recovered"]),
        "benchmark_drawdown_depth_pct": benchmark_depth,
        "drawdown_reduction_vs_benchmark_pct": reduction,
        "drawdown_overlap_with_benchmark": overlap,
        "drawdown_status": status,
        "drawdown_reason": reason,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def benchmark_depth_for_period(
    benchmark_series: dict[str, float],
    start_date: str,
    end_date: str,
) -> tuple[float | str, bool]:
    values = [
        depth
        for date, depth in benchmark_series.items()
        if start_date <= date <= end_date
    ]
    if not values:
        return "", False
    return round(max(values), 4), True


def classify_drawdown(
    depth: float,
    reduction: float | str,
    strategy_name: str,
    has_benchmark_overlap: bool,
) -> tuple[str, str]:
    if strategy_name != "buy_and_hold_baseline" and has_benchmark_overlap and isinstance(reduction, (int, float)) and reduction > 0:
        return "reduced_vs_benchmark", "Drawdown was lower than the matching benchmark window."
    if depth >= 30:
        return "severe_drawdown", "Worst drawdown exceeded the severe threshold."
    if depth >= 15:
        return "moderate_drawdown", "Worst drawdown was moderate."
    return "mild_drawdown", "Worst drawdown was mild."


def insufficient_drawdown_row(created_at: str, strategy_name: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "source_file": "",
        "strategy_name": strategy_name,
        "ticker_or_portfolio": "portfolio",
        "period": "full_period",
        "peak_date": "",
        "trough_date": "",
        "recovery_date": "",
        "drawdown_depth_pct": "",
        "drawdown_duration_days": "",
        "recovery_duration_days": "",
        "is_recovered": "",
        "benchmark_drawdown_depth_pct": "",
        "drawdown_reduction_vs_benchmark_pct": "",
        "drawdown_overlap_with_benchmark": False,
        "drawdown_status": "insufficient_data",
        "drawdown_reason": "Missing or insufficient saved equity curve data.",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def no_drawdown_row(created_at: str, curve: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "source_file": curve["source_file"],
        "strategy_name": curve["strategy_name"],
        "ticker_or_portfolio": curve["ticker_or_portfolio"],
        "period": curve["period"],
        "peak_date": "",
        "trough_date": "",
        "recovery_date": "",
        "drawdown_depth_pct": 0.0,
        "drawdown_duration_days": 0,
        "recovery_duration_days": 0,
        "is_recovered": True,
        "benchmark_drawdown_depth_pct": "",
        "drawdown_reduction_vs_benchmark_pct": "",
        "drawdown_overlap_with_benchmark": False,
        "drawdown_status": "mild_drawdown",
        "drawdown_reason": "No drawdown period found in saved equity curve.",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def write_drawdown_period_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DRAWDOWN_PERIOD_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DRAWDOWN_PERIOD_COLUMNS})


def build_drawdown_period_summary(rows: list[dict[str, Any]]) -> list[str]:
    benchmark_rows = [
        row for row in rows
        if row.get("strategy_name") == "buy_and_hold_baseline" and isinstance(row.get("drawdown_depth_pct"), (int, float))
    ]
    active_rows = [
        row for row in rows
        if row.get("strategy_name") != "buy_and_hold_baseline" and isinstance(row.get("drawdown_depth_pct"), (int, float))
    ]
    lines = [
        "Drawdown period report summary",
        "Research-only drawdown analysis. This is not execution approval.",
        "worst benchmark drawdown period: " + label_for_row(worst_by_depth(benchmark_rows)),
        "worst active drawdown period: " + label_for_row(worst_by_depth(active_rows)),
        "best drawdown reduction versus benchmark: " + reduction_label_for_row(best_reduction(active_rows)),
        etf_vs_adaptive_line(rows),
        "Warning: research_only=True, preview_only=True, and execution_approved=False for every row.",
    ]
    return lines


def worst_by_depth(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return sorted(rows, key=lambda row: -float(row["drawdown_depth_pct"]))[0]


def best_reduction(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid = [row for row in rows if isinstance(row.get("drawdown_reduction_vs_benchmark_pct"), (int, float))]
    if not valid:
        return None
    return sorted(valid, key=lambda row: -float(row["drawdown_reduction_vs_benchmark_pct"]))[0]


def etf_vs_adaptive_line(rows: list[dict[str, Any]]) -> str:
    etf = first_strategy_depth(rows, "monthly_etf_momentum_rotation")
    adaptive = first_strategy_depth(rows, "adaptive_risk_on_off_momentum")
    if etf is None or adaptive is None:
        return "ETF rotation versus adaptive drawdown: unavailable"
    return (
        "ETF rotation versus adaptive drawdown: "
        f"ETF={etf['drawdown_depth_pct']}%, adaptive={adaptive['drawdown_depth_pct']}%"
    )


def first_strategy_depth(rows: list[dict[str, Any]], strategy_name: str) -> dict[str, Any] | None:
    matches = [
        row for row in rows
        if row.get("strategy_name") == strategy_name and isinstance(row.get("drawdown_depth_pct"), (int, float))
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda row: -float(row["drawdown_depth_pct"]))[0]


def label_for_row(row: dict[str, Any] | None) -> str:
    if row is None:
        return "unavailable"
    return (
        f"{row.get('strategy_name')} "
        f"{row.get('peak_date')}->{row.get('trough_date')} "
        f"({row.get('drawdown_depth_pct')}%)"
    )


def reduction_label_for_row(row: dict[str, Any] | None) -> str:
    if row is None:
        return "unavailable"
    return (
        f"{row.get('strategy_name')} "
        f"{row.get('peak_date')}->{row.get('trough_date')} "
        f"(reduction={row.get('drawdown_reduction_vs_benchmark_pct')} percentage points; "
        f"strategy_drawdown={row.get('drawdown_depth_pct')}%; "
        f"benchmark_drawdown={row.get('benchmark_drawdown_depth_pct')}%)"
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


def days_between(start_date: str, end_date: str) -> int | str:
    if not start_date or not end_date:
        return ""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    return (end - start).days
