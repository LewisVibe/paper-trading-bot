"""Strategy promotion report helpers.

This module combines existing research and walk-forward CSV reports into a
conservative checklist. It does not call market data, Alpaca, Discord, SQLite,
or rerun backtests.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_bot.research.reporting import classify_strategy_role


PROMOTION_COLUMNS = [
    "strategy_name",
    "ticker_or_portfolio",
    "strategy_family",
    "strategy_role",
    "report_view",
    "walk_forward_view",
    "research_cagr_pct",
    "research_sharpe_ratio",
    "research_calmar_ratio",
    "research_max_drawdown_pct",
    "research_active_combined_rank_score",
    "out_of_sample_cagr_pct",
    "out_of_sample_sharpe",
    "out_of_sample_calmar",
    "out_of_sample_max_drawdown_pct",
    "robustness_label",
    "beats_benchmark_cagr",
    "beats_benchmark_sharpe",
    "beats_benchmark_calmar",
    "has_lower_drawdown_than_benchmark",
    "trade_count",
    "promotion_status",
    "promotion_reason",
    "required_next_step",
]


@dataclass
class StrategyPromotionReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def generate_strategy_promotion_report(
    data_dir: Path | str = "data",
    output_filename: str = "strategy_promotion_report.csv",
) -> StrategyPromotionReportResult:
    data_path = Path(data_dir)
    warnings: list[str] = []
    research_path = data_path / "research_report.csv"
    walk_forward_path = data_path / "walk_forward_report.csv"
    defensive_path = data_path / "defensive_strategy_report.csv"

    if not research_path.exists():
        raise RuntimeError(f"Missing required research report: {research_path}")
    if not walk_forward_path.exists():
        raise RuntimeError(f"Missing required walk-forward report: {walk_forward_path}")

    research_rows = read_csv_rows(research_path)
    walk_forward_rows = read_csv_rows(walk_forward_path)
    defensive_rows = read_csv_rows(defensive_path) if defensive_path.exists() else []
    if not research_rows:
        raise RuntimeError(f"No usable rows in required research report: {research_path}")
    if not walk_forward_rows:
        raise RuntimeError(f"No usable rows in required walk-forward report: {walk_forward_path}")

    rows = build_strategy_promotion_rows(research_rows, walk_forward_rows, defensive_rows)
    if not rows:
        raise RuntimeError("No usable rows found for strategy promotion report.")

    output_path = data_path / output_filename
    write_strategy_promotion_report(output_path, rows)
    summary_lines = build_strategy_promotion_summary(rows)

    return StrategyPromotionReportResult(
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


def build_strategy_promotion_rows(
    research_rows: list[dict[str, str]],
    walk_forward_rows: list[dict[str, str]],
    defensive_rows: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    selected_research_rows = select_research_rows(research_rows)
    walk_forward_by_key = {
        row_key(row): row
        for row in walk_forward_rows
    }
    defensive_by_key = {
        row_key(row): row
        for row in defensive_rows or []
    }
    promotion_rows: list[dict[str, Any]] = []
    for research_row in selected_research_rows:
        key = row_key(research_row)
        walk_forward_row = walk_forward_by_key.get(key, {})
        row = build_strategy_promotion_row(research_row, walk_forward_row, defensive_by_key.get(key, {}))
        promotion_rows.append(row)
    apply_promotion_statuses(promotion_rows)
    return sorted(
        promotion_rows,
        key=lambda row: (
            promotion_sort_order(row.get("promotion_status", "")),
            number_or_large(row.get("research_active_combined_rank_score")),
            row.get("strategy_name", ""),
            row.get("ticker_or_portfolio", ""),
        ),
    )


def select_research_rows(research_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: dict[tuple[str, str], dict[str, str]] = {}
    for row in research_rows:
        key = row_key(row)
        current = selected.get(key)
        if current is None or research_row_priority(row) < research_row_priority(current):
            selected[key] = row
    return list(selected.values())


def research_row_priority(row: dict[str, str]) -> tuple[int, float]:
    report_view = str(row.get("report_view", ""))
    period = str(row.get("period", ""))
    if "portfolio_full_period" in report_view or period == "full_period":
        period_priority = 0
    elif "portfolio_out_of_sample" in report_view or period == "out_of_sample":
        period_priority = 1
    elif "portfolio_in_sample" in report_view or period == "in_sample":
        period_priority = 2
    else:
        period_priority = 3
    score = number_or_large(number_or_blank(row.get("decision_combined_rank_score", "")))
    return period_priority, score


def row_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("strategy_name", "")),
        str(row.get("ticker_or_portfolio", "")),
    )


def build_strategy_promotion_row(
    research_row: dict[str, str],
    walk_forward_row: dict[str, str],
    defensive_row: dict[str, str] | None = None,
) -> dict[str, Any]:
    role = normalized_strategy_role(research_row)
    defensive_row = defensive_row or {}
    return {
        "strategy_name": research_row.get("strategy_name", ""),
        "ticker_or_portfolio": research_row.get("ticker_or_portfolio", ""),
        "strategy_family": role["strategy_family"],
        "strategy_role": role["strategy_role"],
        "report_view": research_row.get("report_view", ""),
        "walk_forward_view": walk_forward_row.get("walk_forward_view", ""),
        "research_cagr_pct": number_or_blank(research_row.get("cagr_pct", "")),
        "research_sharpe_ratio": number_or_blank(research_row.get("sharpe_ratio", "")),
        "research_calmar_ratio": number_or_blank(research_row.get("calmar_ratio", "")),
        "research_max_drawdown_pct": number_or_blank(research_row.get("max_drawdown_pct", "")),
        "research_active_combined_rank_score": number_or_blank(research_row.get("active_combined_rank_score", "")),
        "out_of_sample_cagr_pct": number_or_blank(walk_forward_row.get("out_of_sample_cagr_pct", "")),
        "out_of_sample_sharpe": number_or_blank(walk_forward_row.get("out_of_sample_sharpe", "")),
        "out_of_sample_calmar": number_or_blank(walk_forward_row.get("out_of_sample_calmar", "")),
        "out_of_sample_max_drawdown_pct": number_or_blank(walk_forward_row.get("out_of_sample_max_drawdown_pct", "")),
        "robustness_label": walk_forward_row.get("robustness_label", "insufficient_period_data"),
        "beats_benchmark_cagr": bool_or_blank(research_row.get("beats_best_benchmark_cagr", "")),
        "beats_benchmark_sharpe": bool_or_blank(research_row.get("beats_best_benchmark_sharpe", "")),
        "beats_benchmark_calmar": bool_or_blank(research_row.get("beats_best_benchmark_calmar", "")),
        "has_lower_drawdown_than_benchmark": bool_or_blank(research_row.get("has_lower_drawdown_than_best_benchmark", "")),
        "trade_count": number_or_blank(research_row.get("number_of_trades", "")),
        "defensive_status": defensive_row.get("defensive_status", ""),
        "defensive_score": number_or_blank(defensive_row.get("defensive_score", "")),
        "promotion_status": "",
        "promotion_reason": "",
        "required_next_step": "",
    }


def normalized_strategy_role(research_row: dict[str, str]) -> dict[str, bool | str]:
    strategy_name = research_row.get("strategy_name", "")
    existing_family = research_row.get("strategy_family", "")
    existing_role = research_row.get("strategy_role", "")
    if existing_family and existing_family != "unknown" and existing_role and existing_role != "unknown":
        return {
            "strategy_family": existing_family,
            "strategy_role": existing_role,
            "is_benchmark": existing_role == "benchmark",
            "is_active_strategy": existing_role.startswith("active_"),
        }
    return classify_strategy_role(research_row.get("source_file", ""), strategy_name)


def number_or_blank(value: Any) -> float | str:
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def bool_or_blank(value: Any) -> bool | str:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return ""


def apply_promotion_statuses(rows: list[dict[str, Any]]) -> None:
    preview_names = preview_candidate_names(rows)
    for row in rows:
        status, reason, next_step = classify_promotion_status(row, preview_names, rows)
        row["promotion_status"] = status
        row["promotion_reason"] = reason
        row["required_next_step"] = next_step


def preview_candidate_names(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    portfolio_active = [
        row
        for row in rows
        if row.get("walk_forward_view") == "portfolio_active"
        and row.get("robustness_label") == "moderate_decay"
    ]
    candidates: set[tuple[str, str]] = set()
    for metric_key in ["out_of_sample_cagr_pct", "out_of_sample_sharpe", "out_of_sample_calmar"]:
        valid_rows = [row for row in portfolio_active if isinstance(row.get(metric_key), (int, float))]
        if not valid_rows:
            continue
        best = sorted(valid_rows, key=lambda row: -float(row[metric_key]))[0]
        candidates.add(row_key(best))
    lower_drawdown = [
        row
        for row in portfolio_active
        if row.get("has_lower_drawdown_than_benchmark") is True
        and isinstance(row.get("out_of_sample_max_drawdown_pct"), (int, float))
    ]
    if lower_drawdown:
        best = sorted(lower_drawdown, key=lambda row: float(row["out_of_sample_max_drawdown_pct"]))[0]
        candidates.add(row_key(best))
    return candidates


def classify_promotion_status(
    row: dict[str, Any],
    preview_names: set[tuple[str, str]],
    all_rows: list[dict[str, Any]] | None = None,
) -> tuple[str, str, str]:
    name = str(row.get("strategy_name", ""))
    robustness = str(row.get("robustness_label", ""))
    walk_forward_view = str(row.get("walk_forward_view", ""))

    if name == "buy_and_hold_baseline":
        return (
            "benchmark_only",
            "Benchmark remains the reference case, not an active strategy promotion.",
            "Use as comparison benchmark.",
        )
    if robustness == "out_of_sample_failure":
        return (
            "reject_for_now",
            "Out-of-sample CAGR is negative.",
            "Do not promote; revisit only if future research changes materially.",
        )
    if robustness == "severe_decay":
        return (
            "pause",
            "Walk-forward report shows severe out-of-sample decay.",
            "Pause strategy work and inspect decay before any further consideration.",
        )
    if robustness == "insufficient_period_data" or not walk_forward_view:
        return (
            "research_only",
            "Walk-forward split data is missing or insufficient.",
            "Add in_sample/out_of_sample validation before promotion.",
        )
    if name == "adaptive_risk_on_off_momentum":
        return adaptive_promotion_status(row, all_rows or [])
    if name == "monthly_etf_momentum_rotation":
        return (
            "research_only",
            "ETF rotation has walk-forward period data, but remains research-only because it does not beat the benchmark on all required promotion metrics.",
            "Review defensive-strategy criteria, benchmark comparison, turnover, and portfolio role before any preview/execution discussion.",
        )
    if row_key(row) in preview_names:
        return (
            "preview_candidate",
            "Moderate-decay portfolio active strategy ranks among the best active walk-forward rows.",
            "Future preview-mode research only; not approved for paper execution.",
        )
    return (
        "research_only",
        "Does not currently meet conservative preview-candidate criteria.",
        "Keep in research reports and compare after more validation.",
    )


def adaptive_promotion_status(
    row: dict[str, Any],
    all_rows: list[dict[str, Any]],
) -> tuple[str, str, str]:
    defensive_status = str(row.get("defensive_status", "") or "")
    defensive_phrase = (
        f" and {defensive_status} status"
        if defensive_status in {"strongest_defensive_candidate", "defensive_candidate", "weak_defensive_candidate"}
        else ""
    )
    improved_phrase = (
        "has improved out-of-sample walk-forward metrics"
        if row.get("robustness_label") == "improved_out_of_sample"
        else "has walk-forward split data"
    )
    etf_row = next(
        (
            candidate
            for candidate in all_rows
            if candidate.get("strategy_name") == "monthly_etf_momentum_rotation"
            and candidate.get("ticker_or_portfolio") == row.get("ticker_or_portfolio")
        ),
        {},
    )
    trails_etf = adaptive_trails_etf_rotation(row, etf_row)
    etf_phrase = (
        "still trails ETF rotation on out-of-sample Sharpe/Calmar"
        if trails_etf
        else "still needs comparison against ETF rotation's simpler defensive role"
    )
    trade_count = row.get("trade_count")
    turnover_phrase = (
        f"higher complexity / turnover burden ({int(trade_count)} trades)"
        if isinstance(trade_count, (int, float))
        else "higher complexity / turnover burden"
    )
    return (
        "research_only",
        f"Adaptive {improved_phrase}{defensive_phrase}, but {etf_phrase} and carries {turnover_phrase}.",
        "Keep research-only; compare turnover, cost burden, and defensive portfolio role against ETF rotation before reconsidering.",
    )


def adaptive_trails_etf_rotation(
    adaptive_row: dict[str, Any],
    etf_row: dict[str, Any],
) -> bool:
    adaptive_sharpe = adaptive_row.get("out_of_sample_sharpe")
    adaptive_calmar = adaptive_row.get("out_of_sample_calmar")
    etf_sharpe = etf_row.get("out_of_sample_sharpe")
    etf_calmar = etf_row.get("out_of_sample_calmar")
    if not all(isinstance(value, (int, float)) for value in [adaptive_sharpe, adaptive_calmar, etf_sharpe, etf_calmar]):
        return False
    return float(adaptive_sharpe) < float(etf_sharpe) and float(adaptive_calmar) < float(etf_calmar)


def promotion_sort_order(status: str) -> int:
    order = {
        "benchmark_only": 0,
        "preview_candidate": 1,
        "research_only": 2,
        "pause": 3,
        "reject_for_now": 4,
    }
    return order.get(status, 99)


def number_or_large(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 999999.0


def write_strategy_promotion_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PROMOTION_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PROMOTION_COLUMNS})


def build_strategy_promotion_summary(rows: list[dict[str, Any]]) -> list[str]:
    summary = [
        "Strategy promotion report summary",
        "Research-only checklist. Promotion does not mean execution approval.",
    ]
    add_status_line(summary, rows, "benchmark row", "benchmark_only")
    add_status_line(summary, rows, "preview candidates", "preview_candidate")
    add_status_line(summary, rows, "research-only candidates", "research_only")
    add_status_line(summary, rows, "paused strategies", "pause")
    add_status_line(summary, rows, "rejected strategies", "reject_for_now")
    if not any_active_beats_benchmark(rows):
        summary.append("Warning: candidates are not benchmark replacements because no active strategy beats the benchmark on CAGR, Sharpe, or Calmar.")
    summary.append("Any execution requires preview mode, risk checks, and explicit confirmation.")
    return summary


def add_status_line(summary: list[str], rows: list[dict[str, Any]], label: str, status: str) -> None:
    matches = [label_for_row(row) for row in rows if row.get("promotion_status") == status]
    if not matches:
        summary.append(f"{label}: none")
        return
    preview = ", ".join(matches[:8])
    if len(matches) > 8:
        preview += f", ... ({len(matches)} total)"
    summary.append(f"{label}: {preview}")


def any_active_beats_benchmark(rows: list[dict[str, Any]]) -> bool:
    return any(
        row.get("strategy_role", "").startswith("active_")
        and row.get("ticker_or_portfolio") == "portfolio"
        and (
            row.get("beats_benchmark_cagr") is True
            or row.get("beats_benchmark_sharpe") is True
            or row.get("beats_benchmark_calmar") is True
        )
        for row in rows
    )


def label_for_row(row: dict[str, Any]) -> str:
    return f"{row.get('strategy_name', '')} [{row.get('ticker_or_portfolio', '')}]"
