"""Research-only defensive strategy report helpers.

This module reads saved research CSV files and writes a defensive usefulness
report. It does not call market data, Alpaca, Discord, SQLite, or execution
helpers, and it does not approve trading.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFENSIVE_COLUMNS = [
    "created_at",
    "strategy_name",
    "ticker_or_portfolio",
    "strategy_family",
    "research_cagr_pct",
    "research_sharpe_ratio",
    "research_calmar_ratio",
    "research_max_drawdown_pct",
    "out_of_sample_cagr_pct",
    "out_of_sample_sharpe",
    "out_of_sample_calmar",
    "out_of_sample_max_drawdown_pct",
    "robustness_label",
    "has_lower_drawdown_than_benchmark",
    "beats_benchmark_cagr",
    "beats_benchmark_sharpe",
    "beats_benchmark_calmar",
    "defensive_score",
    "defensive_status",
    "defensive_reason",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class DefensiveStrategyReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def generate_defensive_strategy_report(
    data_dir: Path | str = "data",
    output_filename: str = "defensive_strategy_report.csv",
) -> DefensiveStrategyReportResult:
    data_path = Path(data_dir)
    warnings: list[str] = []
    research_path = data_path / "research_report.csv"
    walk_forward_path = data_path / "walk_forward_report.csv"

    if not research_path.exists():
        raise RuntimeError(f"Missing required research report: {research_path}")
    if not walk_forward_path.exists():
        raise RuntimeError(f"Missing required walk-forward report: {walk_forward_path}")

    research_rows = read_csv_rows(research_path)
    walk_forward_rows = read_csv_rows(walk_forward_path)
    if not research_rows:
        raise RuntimeError(f"No usable rows in required research report: {research_path}")
    if not walk_forward_rows:
        raise RuntimeError(f"No usable rows in required walk-forward report: {walk_forward_path}")

    rows = build_defensive_strategy_rows(research_rows, walk_forward_rows)
    output_path = data_path / output_filename
    write_defensive_strategy_report(output_path, rows)
    summary_lines = build_defensive_strategy_summary(rows)

    return DefensiveStrategyReportResult(
        output_path=output_path,
        rows=rows,
        warnings=warnings,
        summary_lines=summary_lines,
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [
            row
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def build_defensive_strategy_rows(
    research_rows: list[dict[str, str]],
    walk_forward_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    created_at = datetime.now(timezone.utc).isoformat()
    selected_research = select_portfolio_active_research_rows(research_rows)
    walk_forward_by_key = {row_key(row): row for row in walk_forward_rows}

    rows = [
        build_defensive_strategy_row(created_at, research_row, walk_forward_by_key.get(row_key(research_row), {}))
        for research_row in selected_research
    ]
    rows.sort(
        key=lambda row: (
            defensive_status_sort_order(row["defensive_status"]),
            -float(row["defensive_score"]),
            row["strategy_name"],
        )
    )
    mark_strongest_defensive_candidate(rows)
    return rows


def select_portfolio_active_research_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if str(row.get("is_active_strategy", "")).strip().lower() != "true":
            continue
        if str(row.get("is_portfolio_level", "")).strip().lower() != "true":
            continue
        key = row_key(row)
        current = selected.get(key)
        if current is None or research_row_priority(row) < research_row_priority(current):
            selected[key] = row
    return list(selected.values())


def research_row_priority(row: dict[str, str]) -> tuple[int, float]:
    period = str(row.get("period", ""))
    report_view = str(row.get("report_view", ""))
    if period == "full_period" or "full_period" in report_view:
        period_priority = 0
    elif period == "out_of_sample" or "out_of_sample" in report_view:
        period_priority = 1
    elif period == "in_sample" or "in_sample" in report_view:
        period_priority = 2
    else:
        period_priority = 3
    score = number_or_large(number_or_blank(row.get("active_combined_rank_score", "")))
    return period_priority, score


def row_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("strategy_name", "")),
        str(row.get("ticker_or_portfolio", "")),
    )


def build_defensive_strategy_row(
    created_at: str,
    research_row: dict[str, str],
    walk_forward_row: dict[str, str],
) -> dict[str, Any]:
    row = {
        "created_at": created_at,
        "strategy_name": research_row.get("strategy_name", ""),
        "ticker_or_portfolio": research_row.get("ticker_or_portfolio", ""),
        "strategy_family": research_row.get("strategy_family", ""),
        "research_cagr_pct": number_or_blank(research_row.get("cagr_pct", "")),
        "research_sharpe_ratio": number_or_blank(research_row.get("sharpe_ratio", "")),
        "research_calmar_ratio": number_or_blank(research_row.get("calmar_ratio", "")),
        "research_max_drawdown_pct": number_or_blank(research_row.get("max_drawdown_pct", "")),
        "out_of_sample_cagr_pct": number_or_blank(walk_forward_row.get("out_of_sample_cagr_pct", "")),
        "out_of_sample_sharpe": number_or_blank(walk_forward_row.get("out_of_sample_sharpe", "")),
        "out_of_sample_calmar": number_or_blank(walk_forward_row.get("out_of_sample_calmar", "")),
        "out_of_sample_max_drawdown_pct": number_or_blank(walk_forward_row.get("out_of_sample_max_drawdown_pct", "")),
        "robustness_label": walk_forward_row.get("robustness_label", "insufficient_period_data"),
        "has_lower_drawdown_than_benchmark": bool_or_blank(research_row.get("has_lower_drawdown_than_best_benchmark", "")),
        "beats_benchmark_cagr": bool_or_blank(research_row.get("beats_best_benchmark_cagr", "")),
        "beats_benchmark_sharpe": bool_or_blank(research_row.get("beats_best_benchmark_sharpe", "")),
        "beats_benchmark_calmar": bool_or_blank(research_row.get("beats_best_benchmark_calmar", "")),
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }
    score, status, reason = defensive_score_status_and_reason(row)
    row["defensive_score"] = round(score, 4)
    row["defensive_status"] = status
    row["defensive_reason"] = reason
    return row


def defensive_score_status_and_reason(row: dict[str, Any]) -> tuple[float, str, str]:
    required_metrics = [
        row.get("out_of_sample_cagr_pct"),
        row.get("out_of_sample_sharpe"),
        row.get("out_of_sample_calmar"),
        row.get("out_of_sample_max_drawdown_pct"),
    ]
    robustness = str(row.get("robustness_label", ""))
    if any(not isinstance(value, (int, float)) for value in required_metrics) or robustness == "insufficient_period_data":
        return 0.0, "insufficient_data", "Missing usable walk-forward out-of-sample metrics."

    if robustness == "out_of_sample_failure":
        return 0.0, "not_defensive", "Out-of-sample CAGR is negative."
    if robustness == "severe_decay":
        return 5.0, "not_defensive", "Walk-forward performance decayed severely."

    score = 0.0
    reasons: list[str] = []

    if row.get("has_lower_drawdown_than_benchmark") is True:
        score += 35
        reasons.append("lower drawdown than benchmark")
    else:
        score -= 15
        reasons.append("does not show lower drawdown than benchmark")

    score += score_threshold(row["out_of_sample_sharpe"], [(1.0, 20), (0.75, 15), (0.5, 8)])
    score += score_threshold(row["out_of_sample_calmar"], [(1.0, 20), (0.5, 12), (0.25, 6)])

    if robustness == "improved_out_of_sample":
        score += 20
        reasons.append("out-of-sample metrics improved")
    elif robustness == "robust":
        score += 15
        reasons.append("walk-forward metrics are robust")
    elif robustness == "moderate_decay":
        score += 5
        reasons.append("out-of-sample remains positive with moderate decay")

    if isinstance(row.get("out_of_sample_cagr_pct"), (int, float)):
        oos_cagr = float(row["out_of_sample_cagr_pct"])
        if oos_cagr < 3:
            score -= 20
            reasons.append("return drag is very high")
        elif oos_cagr < 8:
            score -= 8
            reasons.append("return drag remains meaningful")

    if isinstance(row.get("out_of_sample_max_drawdown_pct"), (int, float)) and float(row["out_of_sample_max_drawdown_pct"]) > 30:
        score -= 15
        reasons.append("out-of-sample drawdown is high")

    if row.get("has_lower_drawdown_than_benchmark") is True and score >= 45:
        return score, "defensive_candidate", "; ".join(reasons)
    if score >= 25:
        return score, "weak_defensive_candidate", "; ".join(reasons)
    return score, "not_defensive", "; ".join(reasons)


def score_threshold(value: Any, thresholds: list[tuple[float, float]]) -> float:
    if not isinstance(value, (int, float)):
        return 0.0
    numeric = float(value)
    for threshold, score in thresholds:
        if numeric >= threshold:
            return score
    return 0.0


def mark_strongest_defensive_candidate(rows: list[dict[str, Any]]) -> None:
    candidates = [
        row
        for row in rows
        if row["defensive_status"] in {"strongest_defensive_candidate", "defensive_candidate"}
    ]
    if not candidates:
        return
    best = sorted(
        candidates,
        key=lambda row: (
            -float(row["defensive_score"]),
            -float(row["out_of_sample_sharpe"]) if isinstance(row.get("out_of_sample_sharpe"), (int, float)) else 0,
            row["strategy_name"],
        ),
    )[0]
    if best["defensive_status"] != "insufficient_data":
        best["defensive_status"] = "strongest_defensive_candidate"


def defensive_status_sort_order(status: str) -> int:
    order = {
        "strongest_defensive_candidate": 0,
        "defensive_candidate": 1,
        "weak_defensive_candidate": 2,
        "not_defensive": 3,
        "insufficient_data": 4,
    }
    return order.get(status, 99)


def write_defensive_strategy_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEFENSIVE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEFENSIVE_COLUMNS})


def build_defensive_strategy_summary(rows: list[dict[str, Any]]) -> list[str]:
    summary = [
        "Defensive strategy report summary",
        "Research-only defensive review. Defensive status is not execution approval.",
    ]
    summary.append(best_line(rows, "best defensive candidate", "defensive_score"))
    summary.append(best_line(rows, "best out-of-sample Sharpe active strategy", "out_of_sample_sharpe"))
    summary.append(best_line(rows, "best out-of-sample Calmar active strategy", "out_of_sample_calmar"))
    summary.append(lowest_line(rows, "lowest out-of-sample drawdown active strategy", "out_of_sample_max_drawdown_pct"))
    summary.append("Warning: research_only=True, preview_only=True, and execution_approved=False for every row.")
    return summary


def best_line(rows: list[dict[str, Any]], label: str, metric_key: str) -> str:
    valid_rows = [row for row in rows if isinstance(row.get(metric_key), (int, float))]
    if not valid_rows:
        return f"{label}: unavailable"
    best = sorted(valid_rows, key=lambda row: (-float(row[metric_key]), row["strategy_name"]))[0]
    return f"{label}: {label_for_row(best)} ({metric_key}={best[metric_key]})"


def lowest_line(rows: list[dict[str, Any]], label: str, metric_key: str) -> str:
    valid_rows = [row for row in rows if isinstance(row.get(metric_key), (int, float))]
    if not valid_rows:
        return f"{label}: unavailable"
    best = sorted(valid_rows, key=lambda row: (float(row[metric_key]), row["strategy_name"]))[0]
    return f"{label}: {label_for_row(best)} ({metric_key}={best[metric_key]})"


def label_for_row(row: dict[str, Any]) -> str:
    return f"{row.get('strategy_name', '')} [{row.get('ticker_or_portfolio', '')}]"


def number_or_blank(value: Any) -> float | str:
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def number_or_large(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 999999.0


def bool_or_blank(value: Any) -> bool | str:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return ""
