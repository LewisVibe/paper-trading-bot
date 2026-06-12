"""Turnover and cost stress for the 55% stricter breadth-gate cluster.

This module reads saved threshold-neighbourhood research CSVs only. It does not
refresh market data, load config, call brokers, read positions, write SQLite,
send alerts, schedule anything, create order instructions, approve preview
promotion, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_RESEARCH_LEAD = "growth_biased_rotation_breadth_stricter_gate"
PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"
MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"
SPY_BENCHMARK = "spy_buy_and_hold_benchmark"
TARGET_THRESHOLD_PCT = 55
COST_LEVELS_BPS = [0, 5, 10, 25, 50, 100]

INPUT_FILES = {
    "threshold_detail": Path("data/growth_biased_stricter_threshold_neighbourhood.csv"),
    "threshold_summary": Path("data/growth_biased_stricter_threshold_neighbourhood_summary.csv"),
}

OUTPUT_FILES = {
    "detail": Path("data/growth_biased_stricter_cost_turnover_stress.csv"),
    "summary": Path("data/growth_biased_stricter_cost_turnover_stress_summary.csv"),
}

DETAIL_COLUMNS = [
    "created_at",
    "strategy_name",
    "threshold_pct",
    "cost_level_bps",
    "cost_model_mapping",
    "base_cagr_pct",
    "cost_adjusted_cagr_pct",
    "cagr_decay_vs_0_bps",
    "base_sharpe_ratio",
    "cost_adjusted_sharpe_ratio",
    "sharpe_decay_vs_0_bps",
    "max_drawdown_pct",
    "base_calmar_ratio",
    "cost_adjusted_calmar_ratio",
    "calmar_decay_vs_0_bps",
    "trade_count",
    "turnover",
    "average_holding_period_days",
    "average_cash_weight_pct",
    "cagr_delta_vs_original_after_cost",
    "calmar_delta_vs_original_after_cost",
    "cagr_gap_vs_spy_after_cost",
    "calmar_gap_vs_spy_after_cost",
    "credible_after_cost",
    "turnover_status",
    "status",
    "review_warning",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "promotion_approved",
    "scheduling_approved",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "active_research_lead",
    "threshold_pct",
    "cost_levels_tested_bps",
    "base_no_cost_result",
    "result_10_bps",
    "result_25_bps",
    "result_50_bps",
    "result_100_bps",
    "worst_credible_cost_level_bps",
    "turnover_status",
    "summary_label",
    "gap_versus_spy",
    "comparison_versus_original_crash_gate",
    "review_warnings",
    "interpretation",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "promotion_approved",
    "scheduling_approved",
]


@dataclass
class CostTurnoverStressResult:
    detail_path: Path
    summary_path: Path
    detail_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_growth_biased_stricter_cost_turnover_stress(data_dir: Path | str = "data") -> CostTurnoverStressResult:
    data_path = Path(data_dir)
    created_at = now_utc_iso()
    detail_input = read_csv(data_path / INPUT_FILES["threshold_detail"].name)
    summary_input = read_csv(data_path / INPUT_FILES["threshold_summary"].name)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}

    source = find_threshold_row(detail_input, TARGET_THRESHOLD_PCT)
    if not source or source.get("status") == "insufficient_saved_inputs":
        detail_rows = insufficient_detail_rows(created_at, source)
        summary_rows = insufficient_summary_rows(created_at, summary_input)
    else:
        detail_rows = build_cost_stress_rows(created_at, source)
        summary_rows = [build_cost_stress_summary(created_at, detail_rows, summary_input)]

    write_rows(output_paths["detail"], DETAIL_COLUMNS, detail_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    return CostTurnoverStressResult(
        detail_path=output_paths["detail"],
        summary_path=output_paths["summary"],
        detail_rows=detail_rows,
        summary_rows=summary_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def build_cost_stress_rows(created_at: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    base_cagr = as_float(source.get("cagr_pct"))
    base_sharpe = as_float(source.get("sharpe_ratio"))
    base_calmar = as_float(source.get("calmar_ratio"))
    max_drawdown = as_float(source.get("max_drawdown_pct"))
    turnover = as_float(source.get("turnover"))
    trade_count = as_float(source.get("trade_count"))
    cash = as_float(source.get("average_cash_weight_pct"))
    original_cagr_delta = as_float(source.get("cagr_delta_vs_original"))
    original_calmar_delta = as_float(source.get("calmar_delta_vs_original"))
    spy_cagr_gap = as_float(source.get("cagr_gap_vs_spy"))
    spy_calmar_gap = as_float(source.get("calmar_gap_vs_spy"))
    base_original_cagr = base_cagr - original_cagr_delta
    base_original_calmar = base_calmar - original_calmar_delta
    base_spy_cagr = base_cagr - spy_cagr_gap
    base_spy_calmar = base_calmar - spy_calmar_gap

    for cost_bps in COST_LEVELS_BPS:
        cost_drag = turnover * cost_bps / 100.0
        adjusted_cagr = base_cagr - cost_drag
        adjusted_calmar = adjusted_cagr / abs(max_drawdown) if max_drawdown < 0 else 0.0
        adjusted_sharpe = adjusted_sharpe_for_cost(base_sharpe, base_cagr, cost_drag)
        cagr_decay = adjusted_cagr - base_cagr
        sharpe_decay = adjusted_sharpe - base_sharpe
        calmar_decay = adjusted_calmar - base_calmar
        cagr_delta_original = adjusted_cagr - base_original_cagr
        calmar_delta_original = adjusted_calmar - base_original_calmar
        cagr_gap_spy = adjusted_cagr - base_spy_cagr
        calmar_gap_spy = adjusted_calmar - base_spy_calmar
        credible = adjusted_cagr > base_original_cagr and adjusted_calmar >= base_original_calmar * 0.90
        turnover_status = classify_turnover(turnover, trade_count)
        status, warning = classify_cost_row(cost_bps, credible, cagr_decay, calmar_decay, turnover_status, cagr_gap_spy)
        rows.append(
            {
                "created_at": created_at,
                "strategy_name": ACTIVE_RESEARCH_LEAD,
                "threshold_pct": TARGET_THRESHOLD_PCT,
                "cost_level_bps": cost_bps,
                "cost_model_mapping": "Fixed one-way ETF trading friction; applied as turnover * one_way_cost_bps / 100 to CAGR.",
                "base_cagr_pct": round(base_cagr, 4),
                "cost_adjusted_cagr_pct": round(adjusted_cagr, 4),
                "cagr_decay_vs_0_bps": round(cagr_decay, 4),
                "base_sharpe_ratio": round(base_sharpe, 4),
                "cost_adjusted_sharpe_ratio": round(adjusted_sharpe, 4),
                "sharpe_decay_vs_0_bps": round(sharpe_decay, 4),
                "max_drawdown_pct": round(max_drawdown, 4),
                "base_calmar_ratio": round(base_calmar, 4),
                "cost_adjusted_calmar_ratio": round(adjusted_calmar, 4),
                "calmar_decay_vs_0_bps": round(calmar_decay, 4),
                "trade_count": int(trade_count),
                "turnover": round(turnover, 4),
                "average_holding_period_days": round(252.0 / turnover, 2) if turnover > 0 else "",
                "average_cash_weight_pct": round(cash, 4),
                "cagr_delta_vs_original_after_cost": round(cagr_delta_original, 4),
                "calmar_delta_vs_original_after_cost": round(calmar_delta_original, 4),
                "cagr_gap_vs_spy_after_cost": round(cagr_gap_spy, 4),
                "calmar_gap_vs_spy_after_cost": round(calmar_gap_spy, 4),
                "credible_after_cost": credible,
                "turnover_status": turnover_status,
                "status": status,
                "review_warning": warning,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
                "paper_execution_approved": False,
                "promotion_approved": False,
                "scheduling_approved": False,
            }
        )
    return rows


def build_cost_stress_summary(
    created_at: str,
    detail_rows: list[dict[str, Any]],
    threshold_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    credible_rows = [row for row in detail_rows if parse_bool(row.get("credible_after_cost"))]
    worst_credible = max((int(row["cost_level_bps"]) for row in credible_rows), default="")
    turnover_status = str(detail_rows[0].get("turnover_status", "unknown")) if detail_rows else "unknown"
    warnings = sorted({str(row.get("review_warning", "")) for row in detail_rows if row.get("review_warning")})
    row_0 = find_cost_row(detail_rows, 0)
    row_10 = find_cost_row(detail_rows, 10)
    row_25 = find_cost_row(detail_rows, 25)
    row_50 = find_cost_row(detail_rows, 50)
    row_100 = find_cost_row(detail_rows, 100)
    summary_label = classify_summary_label(detail_rows, turnover_status, worst_credible, threshold_summary)
    comparison_original = (
        "beats_original_after_cost"
        if row_100 and as_float(row_100.get("cagr_delta_vs_original_after_cost")) > 0 and as_float(row_100.get("calmar_delta_vs_original_after_cost")) >= -0.05
        else "original_comparison_needs_review"
    )
    return {
        "created_at": created_at,
        "summary_name": "growth_biased_stricter_cost_turnover_stress",
        "active_research_lead": ACTIVE_RESEARCH_LEAD,
        "threshold_pct": TARGET_THRESHOLD_PCT,
        "cost_levels_tested_bps": ",".join(str(level) for level in COST_LEVELS_BPS),
        "base_no_cost_result": format_result(row_0),
        "result_10_bps": format_result(row_10),
        "result_25_bps": format_result(row_25),
        "result_50_bps": format_result(row_50),
        "result_100_bps": format_result(row_100),
        "worst_credible_cost_level_bps": worst_credible,
        "turnover_status": turnover_status,
        "summary_label": summary_label,
        "gap_versus_spy": row_0.get("cagr_gap_vs_spy_after_cost", "") if row_0 else "",
        "comparison_versus_original_crash_gate": comparison_original,
        "review_warnings": "; ".join(warnings) if warnings else "none",
        "interpretation": "Cost stress is fixed research friction analysis only; it does not approve execution or promotion.",
        "required_next_step": "Manual review turnover and cost decay before any preview-candidate discussion.",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "promotion_approved": False,
        "scheduling_approved": False,
    }


def classify_summary_label(
    rows: list[dict[str, Any]],
    turnover_status: str,
    worst_credible: int | str,
    threshold_summary: list[dict[str, Any]],
) -> str:
    if not rows or rows[0].get("status") == "insufficient_saved_inputs":
        return "insufficient_saved_inputs"
    row_10 = find_cost_row(rows, 10)
    row_25 = find_cost_row(rows, 25)
    row_50 = find_cost_row(rows, 50)
    row_100 = find_cost_row(rows, 100)
    threshold_label = str((threshold_summary[0] if threshold_summary else {}).get("summary_label", ""))
    if row_100 and parse_bool(row_100.get("credible_after_cost")) and turnover_status == "turnover_acceptable":
        return "cost_resilient_turnover_acceptable"
    if row_50 and parse_bool(row_50.get("credible_after_cost")) and turnover_status in {"turnover_high_review", "turnover_extreme_review"}:
        return "cost_resilient_but_turnover_high"
    if row_25 and parse_bool(row_25.get("credible_after_cost")):
        return "promising_but_cost_sensitive"
    if row_10 and not parse_bool(row_10.get("credible_after_cost")):
        return "edge_collapses_under_costs"
    if turnover_status == "turnover_extreme_review":
        return "turnover_fragile"
    if "promising" in threshold_label and rows:
        return "benchmark_lagging_but_active_candidate_improved"
    return "manual_review_required"


def classify_cost_row(
    cost_bps: int,
    credible: bool,
    cagr_decay: float,
    calmar_decay: float,
    turnover_status: str,
    cagr_gap_spy: float,
) -> tuple[str, str]:
    warnings = []
    if abs(cagr_decay) > 5 or abs(calmar_decay) > 0.20:
        warnings.append("severe_cost_decay_review")
    if turnover_status in {"turnover_high_review", "turnover_extreme_review"}:
        warnings.append(turnover_status)
    if cagr_gap_spy < 0:
        warnings.append("still_lags_spy")
    if credible:
        return "cost_level_credible", "; ".join(warnings)
    if cost_bps >= 50:
        return "cost_level_fragile", "; ".join(warnings or ["manual_review_required"])
    return "manual_review_required", "; ".join(warnings or ["manual_review_required"])


def classify_turnover(turnover: float, trade_count: float) -> str:
    if turnover >= 20 or trade_count >= 150:
        return "turnover_extreme_review"
    if turnover >= 10 or trade_count >= 75:
        return "turnover_high_review"
    return "turnover_acceptable"


def insufficient_detail_rows(created_at: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    warning = source.get("review_warning", "") if source else "missing threshold-neighbourhood input"
    return [
        {
            "created_at": created_at,
            "strategy_name": ACTIVE_RESEARCH_LEAD,
            "threshold_pct": TARGET_THRESHOLD_PCT,
            "cost_level_bps": level,
            "cost_model_mapping": "Fixed one-way ETF trading friction; applied as turnover * one_way_cost_bps / 100 to CAGR.",
            "credible_after_cost": False,
            "turnover_status": "unknown",
            "status": "insufficient_saved_inputs",
            "review_warning": warning,
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
            "paper_execution_approved": False,
            "promotion_approved": False,
            "scheduling_approved": False,
        }
        for level in COST_LEVELS_BPS
    ]


def insufficient_summary_rows(created_at: str, threshold_summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    warning = (threshold_summary[0] if threshold_summary else {}).get("review_warnings", "missing threshold-neighbourhood input")
    return [
        {
            "created_at": created_at,
            "summary_name": "growth_biased_stricter_cost_turnover_stress",
            "active_research_lead": ACTIVE_RESEARCH_LEAD,
            "threshold_pct": TARGET_THRESHOLD_PCT,
            "cost_levels_tested_bps": ",".join(str(level) for level in COST_LEVELS_BPS),
            "summary_label": "insufficient_saved_inputs",
            "worst_credible_cost_level_bps": "",
            "turnover_status": "unknown",
            "gap_versus_spy": "",
            "comparison_versus_original_crash_gate": "insufficient_saved_inputs",
            "review_warnings": warning,
            "interpretation": "Run threshold-neighbourhood with usable saved data before cost stress.",
            "required_next_step": "Run `python bot.py --growth-biased-stricter-threshold-neighbourhood` with market data available first.",
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
            "paper_execution_approved": False,
            "promotion_approved": False,
            "scheduling_approved": False,
        }
    ]


def show_growth_biased_stricter_cost_turnover_stress_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    detail = read_csv(data_path / OUTPUT_FILES["detail"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    if not detail or not summary:
        return 1, ["Run `python bot.py --growth-biased-stricter-cost-turnover-stress` first."]
    summary_row = summary[0]
    approval_values = {str(row.get("execution_approved", "")).lower() for row in detail + summary}
    return 0, [
        "Growth-biased stricter cost/turnover stress. Display only; execution_approved=False.",
        f"Base/no-cost result: {summary_row.get('base_no_cost_result', '')}",
        f"10 bps result: {summary_row.get('result_10_bps', '')}",
        f"25 bps result: {summary_row.get('result_25_bps', '')}",
        f"50 bps result: {summary_row.get('result_50_bps', '')}",
        f"100 bps result: {summary_row.get('result_100_bps', '')}",
        f"Worst credible cost level: {summary_row.get('worst_credible_cost_level_bps', '')} bps",
        f"Turnover status: {summary_row.get('turnover_status', '')}",
        f"Summary label: {summary_row.get('summary_label', 'insufficient_saved_inputs')}",
        f"Gap versus SPY: {summary_row.get('gap_versus_spy', '')}",
        f"Comparison versus original crash gate: {summary_row.get('comparison_versus_original_crash_gate', '')}",
        f"Review warnings: {summary_row.get('review_warnings', '')}",
        f"execution_approved values: {', '.join(sorted(approval_values)) or 'false'}",
        "Warning: saved cost/turnover stress does not approve orders, preview promotion, scheduling, or execution.",
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    summary = summary_rows[0] if summary_rows else {}
    return [
        "Growth-biased stricter cost/turnover stress complete. Research/report only; execution_approved=False.",
        f"Cost levels tested: {summary.get('cost_levels_tested_bps', '')}",
        f"Base/no-cost result: {summary.get('base_no_cost_result', '')}",
        f"10 bps result: {summary.get('result_10_bps', '')}",
        f"25 bps result: {summary.get('result_25_bps', '')}",
        f"50 bps result: {summary.get('result_50_bps', '')}",
        f"100 bps result: {summary.get('result_100_bps', '')}",
        f"Worst credible cost level: {summary.get('worst_credible_cost_level_bps', '')} bps",
        f"Turnover status: {summary.get('turnover_status', '')}",
        f"Summary label: {summary.get('summary_label', 'insufficient_saved_inputs')}",
        f"Saved cost stress detail to {output_paths['detail']}",
        f"Saved cost stress summary to {output_paths['summary']}",
        "Warning: fixed cost/turnover stress does not approve orders, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def find_threshold_row(rows: list[dict[str, Any]], threshold_pct: int) -> dict[str, Any]:
    for row in rows:
        if str(row.get("threshold_pct")) == str(threshold_pct):
            return row
    for row in rows:
        if row.get("strategy_name") == ACTIVE_RESEARCH_LEAD:
            return row
    return {}


def find_cost_row(rows: list[dict[str, Any]], cost_bps: int) -> dict[str, Any]:
    return next((row for row in rows if str(row.get("cost_level_bps")) == str(cost_bps)), {})


def format_result(row: dict[str, Any]) -> str:
    if not row:
        return "unavailable"
    return (
        f"CAGR={row.get('cost_adjusted_cagr_pct', '')}, "
        f"Sharpe={row.get('cost_adjusted_sharpe_ratio', '')}, "
        f"Calmar={row.get('cost_adjusted_calmar_ratio', '')}, "
        f"credible={row.get('credible_after_cost', False)}"
    )


def adjusted_sharpe_for_cost(base_sharpe: float, base_cagr: float, cost_drag: float) -> float:
    if abs(base_cagr) < 0.000001:
        return base_sharpe
    return base_sharpe - (cost_drag / abs(base_cagr)) * max(abs(base_sharpe), 0.25)


def now_utc_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
