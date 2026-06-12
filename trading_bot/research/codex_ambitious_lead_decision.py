"""Final saved-output lead decision checkpoint for the Codex ambitious candidate.

This module is research/report-only. It reads saved research CSV files, writes
ignored decision CSV reports, and does not load config or touch broker,
position, order, database, notification, scheduling, or execution paths.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET_STRATEGY = "codex_ambitious_concentrated_growth_persistence"
STRICTER_GATE = "growth_biased_rotation_breadth_stricter_gate"
PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"
SPY_BENCHMARK = "spy_buy_and_hold_benchmark"
MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"
EQUAL_WEIGHT_BENCHMARK = "equal_weight_etf_buy_and_hold_benchmark"

INPUT_FILES = {
    "validation": Path("data/codex_ambitious_validation.csv"),
    "validation_summary": Path("data/codex_ambitious_validation_summary.csv"),
    "validation_costs": Path("data/codex_ambitious_validation_costs.csv"),
    "split_drawdown_validation": Path("data/codex_ambitious_split_drawdown_validation.csv"),
    "split_validation": Path("data/codex_ambitious_split_validation.csv"),
    "drawdown_windows": Path("data/codex_ambitious_drawdown_windows.csv"),
    "lead_change_checkpoint": Path("data/codex_ambitious_lead_change_checkpoint.csv"),
    "persistence_summary": Path("data/growth_biased_stricter_persistence_filter_summary.csv"),
    "threshold_summary": Path("data/growth_biased_stricter_threshold_neighbourhood_summary.csv"),
    "cost_turnover_summary": Path("data/growth_biased_stricter_cost_turnover_stress_summary.csv"),
    "manual_review_pack": Path("data/growth_biased_stricter_manual_review_pack.csv"),
}

OUTPUT_FILES = {
    "decision": Path("data/codex_ambitious_lead_decision.csv"),
    "summary": Path("data/codex_ambitious_lead_decision_summary.csv"),
    "evidence": Path("data/codex_ambitious_lead_decision_evidence.csv"),
}

DECISION_LABELS = [
    "codex_ambitious_new_active_research_lead",
    "codex_ambitious_active_research_lead_cost_review_required",
    "codex_ambitious_active_lead_candidate",
    "codex_ambitious_promising_but_not_lead",
    "codex_ambitious_split_sensitive",
    "codex_ambitious_cost_fragile",
    "codex_ambitious_blocked_missing_inputs",
    "manual_review_required",
]

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "decision_area",
    "check_name",
    "strategy_name",
    "comparison_strategy",
    "metric_name",
    "metric_value",
    "reference_value",
    "metric_delta",
    "status",
    "severity",
    "evidence",
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
class CodexAmbitiousLeadDecisionResult:
    decision_path: Path
    summary_path: Path
    evidence_path: Path
    decision_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_codex_ambitious_lead_decision(data_dir: Path | str = "data") -> CodexAmbitiousLeadDecisionResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(data_path / path.name) for name, path in INPUT_FILES.items()}
    evidence_rows = build_evidence_rows(created_at, inputs)
    summary_row = build_summary_row(created_at, inputs, evidence_rows)
    summary_rows = [summary_row]
    decision_rows = [*evidence_rows, summary_row]
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decision"], decision_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["evidence"], evidence_rows)
    return CodexAmbitiousLeadDecisionResult(
        decision_path=output_paths["decision"],
        summary_path=output_paths["summary"],
        evidence_path=output_paths["evidence"],
        decision_rows=decision_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_row, evidence_rows, output_paths),
    )


def build_evidence_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    rows.extend(build_input_rows(created_at, inputs))
    rows.append(build_full_period_row(created_at, inputs))
    rows.append(build_cost_row(created_at, inputs))
    rows.append(build_split_row(created_at, inputs))
    rows.append(build_drawdown_row(created_at, inputs))
    rows.append(build_turnover_row(created_at, inputs))
    rows.append(build_benchmark_row(created_at, inputs))
    rows.append(build_remaining_blockers_row(created_at, inputs))
    rows.append(
        decision_row(
            created_at,
            "required_next_step",
            "manual_decision_boundary",
            status="manual_review_required",
            severity="review_required",
            evidence="Lead-decision labels are research labels only.",
            interpretation="This checkpoint does not approve preview promotion, paper execution, scheduling, or strategy-to-execution wiring.",
            required_next_step="Review cost sensitivity and saved split/drawdown evidence before updating active-research-lead docs.",
        )
    )
    return rows


def build_input_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for name, source_rows in sorted(inputs.items()):
        rows.append(
            decision_row(
                created_at,
                "saved_inputs",
                name,
                metric_name="row_count",
                metric_value=len(source_rows),
                status="input_available" if source_rows else "input_missing",
                severity="pass" if source_rows else "insufficient_data",
                evidence=f"{INPUT_FILES[name]} rows={len(source_rows)}.",
                interpretation="Saved research inputs are required for a conservative lead decision.",
                required_next_step="Regenerate the missing saved research report before changing the active research lead." if not source_rows else "Input available for manual review.",
            )
        )
    return rows


def build_full_period_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    validation = inputs.get("validation", [])
    summary = first(inputs.get("validation_summary", []))
    full = next((row for row in validation if row.get("check_name") == "full_period_result"), {})
    evidence = f"{full.get('metric_value', 'unavailable')}; {summary.get('evidence', '')}"
    beats_spy = has_true(summary.get("evidence", ""), "beats_spy")
    beats_stricter = has_true(summary.get("evidence", ""), "beats_stricter_gate")
    beats_original = has_true(summary.get("evidence", ""), "beats_original")
    status = "full_period_beats_core_references" if beats_spy and beats_stricter and beats_original else "full_period_review_required"
    return decision_row(
        created_at,
        "full_period_performance",
        "full_period_evidence",
        comparison_strategy=f"{SPY_BENCHMARK}; {STRICTER_GATE}; {PREVIOUS_RESEARCH_LEAD}",
        metric_name="full_period_cagr_sharpe_calmar_maxdd_cash_turnover",
        metric_value=full.get("metric_value", "unavailable"),
        status=status,
        severity="pass" if status == "full_period_beats_core_references" else "review_required",
        evidence=evidence,
        interpretation="Full-period strength supports research-lead discussion only with split, drawdown, and cost context.",
    )


def build_cost_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    cost_rows = inputs.get("validation_costs", [])
    summary = first(inputs.get("validation_summary", []))
    survives_10 = cost_survives(cost_rows, 10) or has_true(summary.get("evidence", ""), "survives_10_bps")
    survives_25 = cost_survives(cost_rows, 25) or has_true(summary.get("evidence", ""), "survives_25_bps")
    if not cost_rows and "survives_10_bps" not in summary.get("evidence", ""):
        status = "cost_inputs_missing"
        severity = "insufficient_data"
    elif survives_10 and not survives_25:
        status = "survives_10_bps_cost_review_required"
        severity = "review_required"
    elif survives_10 and survives_25:
        status = "cost_survives_review"
        severity = "pass"
    else:
        status = "cost_fragile"
        severity = "review_required"
    return decision_row(
        created_at,
        "cost_survival",
        "cost_evidence",
        metric_name="survives_10_and_25_bps",
        metric_value=f"survives_10_bps={survives_10}; survives_25_bps={survives_25}",
        status=status,
        severity=severity,
        evidence=f"cost_rows={len(cost_rows)}; summary={summary.get('evidence', '')}",
        interpretation="Failing 25 bps does not block an ambitious research lead by itself when 10 bps survives, but it keeps cost review open.",
        required_next_step="Keep cost review open before any preview promotion or execution discussion.",
    )


def build_split_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    split_rows = [row for row in inputs.get("split_validation", []) if row.get("split_name")]
    positive = [row for row in split_rows if split_positive(row)]
    broken = [row for row in split_rows if row.get("status") in {"split_broken", "insufficient_saved_inputs"}]
    if len(split_rows) < 3:
        status = "split_inputs_missing"
        severity = "insufficient_data"
    elif len(broken) >= 2:
        status = "split_sensitive"
        severity = "review_required"
    elif len(positive) >= 2:
        status = "fixed_splits_positive"
        severity = "pass"
    else:
        status = "split_mixed_review"
        severity = "review_required"
    return decision_row(
        created_at,
        "split_validation",
        "fixed_split_evidence",
        metric_name="split_60_40_split_70_30_split_80_20",
        metric_value="; ".join(f"{row.get('split_name')}={row.get('status')}:{row.get('metric_value')}" for row in split_rows) or "unavailable",
        status=status,
        severity=severity,
        evidence=f"positive_splits={len(positive)}/3; broken_splits={len(broken)}/3.",
        interpretation="Positive but decaying splits can still support an ambitious research label when clearly disclosed.",
    )


def build_drawdown_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    drawdown = first(inputs.get("drawdown_windows", []))
    status_value = drawdown.get("status", "insufficient_saved_inputs")
    references = drawdown.get("reference_value", "")
    unavailable = "unavailable" in references or not drawdown
    acceptable = status_value in {"drawdown_acceptable_for_return", "drawdown_concentrated_review"}
    if unavailable:
        status = "drawdown_inputs_missing"
        severity = "insufficient_data"
    elif acceptable:
        status = "drawdown_window_acceptable_for_research"
        severity = "pass" if status_value == "drawdown_acceptable_for_return" else "review_required"
    else:
        status = "drawdown_window_review_required"
        severity = "review_required"
    return decision_row(
        created_at,
        "drawdown_window_validation",
        "drawdown_evidence",
        comparison_strategy=f"{SPY_BENCHMARK}; {STRICTER_GATE}",
        metric_name=drawdown.get("metric_name", "max_drawdown_pct"),
        metric_value=drawdown.get("metric_value", "unavailable"),
        reference_value=references,
        metric_delta=drawdown.get("metric_delta", ""),
        status=status,
        severity=severity,
        evidence=drawdown.get("evidence", "unavailable"),
        interpretation="Drawdown-window comparison is research risk context only.",
    )


def build_turnover_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    validation = inputs.get("validation", [])
    turnover = next((row for row in validation if row.get("check_name") == "turnover_holding_period"), {})
    return decision_row(
        created_at,
        "turnover_holding_period",
        "turnover_context",
        metric_name=turnover.get("metric_name", "turnover_and_holding_period"),
        metric_value=turnover.get("metric_value", "unavailable"),
        status=turnover.get("status", "turnover_review_required"),
        severity=turnover.get("severity", "review_required"),
        evidence=turnover.get("evidence", "Turnover context unavailable."),
        interpretation="Turnover matters because the candidate survives 10 bps but not necessarily higher costs.",
    )


def build_benchmark_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary = first(inputs.get("validation_summary", []))
    evidence = summary.get("evidence", "")
    metric_value = (
        f"beats_spy={has_true(evidence, 'beats_spy')}; "
        f"beats_stricter_gate={has_true(evidence, 'beats_stricter_gate')}; "
        f"beats_original={has_true(evidence, 'beats_original')}"
    )
    status = "benchmark_comparison_supports_lead_review" if "True" in metric_value else "benchmark_comparison_review_required"
    return decision_row(
        created_at,
        "benchmark_comparison",
        "benchmark_evidence",
        comparison_strategy=f"{SPY_BENCHMARK}; {STRICTER_GATE}; {PREVIOUS_RESEARCH_LEAD}; {MONTHLY_ROTATION_REFERENCE}; {EQUAL_WEIGHT_BENCHMARK}",
        metric_name="core_benchmark_wins",
        metric_value=metric_value,
        status=status,
        severity="pass" if status == "benchmark_comparison_supports_lead_review" else "review_required",
        evidence=evidence or "Saved benchmark evidence unavailable.",
        interpretation="Benchmark wins are research evidence only and do not create trade signals.",
    )


def build_remaining_blockers_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    blockers = collect_blockers(inputs)
    return decision_row(
        created_at,
        "remaining_blockers",
        "blocker_count",
        metric_name="remaining_blocker_count",
        metric_value=len(blockers),
        status="blockers_open" if blockers else "no_blockers_for_research_label",
        severity="review_required" if blockers else "pass",
        evidence="; ".join(blockers) or "No blocker to a research-only lead label found in saved reports.",
        interpretation="Any blocker here is about research labels only, never execution approval.",
        required_next_step="Resolve or explicitly accept remaining research blockers before changing docs.",
    )


def build_summary_row(created_at: str, inputs: dict[str, list[dict[str, Any]]], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing_required = any(not inputs.get(name) for name in ["validation_summary", "validation_costs", "split_validation", "drawdown_windows", "lead_change_checkpoint"])
    summary = first(inputs.get("validation_summary", []))
    summary_evidence = summary.get("evidence", "")
    split_row = next((row for row in evidence_rows if row.get("check_name") == "fixed_split_evidence"), {})
    drawdown_row = next((row for row in evidence_rows if row.get("check_name") == "drawdown_evidence"), {})
    cost_row = next((row for row in evidence_rows if row.get("check_name") == "cost_evidence"), {})
    beats_core = all(has_true(summary_evidence, key) for key in ["beats_spy", "beats_stricter_gate", "beats_original"])
    survives_10 = "survives_10_bps=True" in cost_row.get("metric_value", "")
    survives_25 = "survives_25_bps=True" in cost_row.get("metric_value", "")
    split_ok = split_row.get("status") in {"fixed_splits_positive", "split_mixed_review"}
    drawdown_ok = drawdown_row.get("status") in {"drawdown_window_acceptable_for_research"}

    if missing_required:
        label = "codex_ambitious_blocked_missing_inputs"
    elif beats_core and survives_10 and split_ok and drawdown_ok and survives_25:
        label = "codex_ambitious_new_active_research_lead"
    elif beats_core and survives_10 and split_ok and drawdown_ok:
        label = "codex_ambitious_active_research_lead_cost_review_required"
    elif split_row.get("status") == "split_sensitive":
        label = "codex_ambitious_split_sensitive"
    elif cost_row.get("status") == "cost_fragile":
        label = "codex_ambitious_cost_fragile"
    elif beats_core and survives_10:
        label = "codex_ambitious_active_lead_candidate"
    elif beats_core:
        label = "codex_ambitious_promising_but_not_lead"
    else:
        label = "manual_review_required"

    blockers = collect_blockers(inputs)
    return decision_row(
        created_at,
        "lead_decision_summary",
        "final_decision_label",
        metric_name="final_decision_label",
        metric_value=label,
        status=label,
        severity="pass" if label == "codex_ambitious_new_active_research_lead" else "review_required",
        evidence=(
            f"beats_core={beats_core}; survives_10_bps={survives_10}; survives_25_bps={survives_25}; "
            f"split_status={split_row.get('status', '')}; drawdown_status={drawdown_row.get('status', '')}; "
            f"remaining_blockers={len(blockers)}."
        ),
        interpretation="Final decision is a research label only and does not approve preview promotion or execution.",
        required_next_step=required_next_step(label),
    )


def collect_blockers(inputs: dict[str, list[dict[str, Any]]]) -> list[str]:
    blockers = []
    for name in ["validation_summary", "validation_costs", "split_validation", "drawdown_windows", "lead_change_checkpoint"]:
        if not inputs.get(name):
            blockers.append(f"missing_{name}")
    cost_rows = inputs.get("validation_costs", [])
    if cost_rows and cost_survives(cost_rows, 10) and not cost_survives(cost_rows, 25):
        blockers.append("cost_review_25_bps_not_survived")
    split_rows = [row for row in inputs.get("split_validation", []) if row.get("split_name")]
    if split_rows and sum(1 for row in split_rows if not split_positive(row)) >= 2:
        blockers.append("split_sensitivity_review")
    drawdown = first(inputs.get("drawdown_windows", []))
    if drawdown and drawdown.get("status") not in {"drawdown_acceptable_for_return", "drawdown_concentrated_review"}:
        blockers.append("drawdown_window_review")
    return blockers


def show_codex_ambitious_lead_decision_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    decision = read_csv(data_path / OUTPUT_FILES["decision"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    evidence = read_csv(data_path / OUTPUT_FILES["evidence"].name)
    if not decision or not summary:
        return 1, ["Run `python bot.py --codex-ambitious-lead-decision` first."]
    final = summary[0]
    approval_values = {str(row.get("execution_approved", "")).lower() for row in decision + summary + evidence}
    return 0, [
        "Codex ambitious lead decision. Display only; execution_approved=False.",
        f"Final decision label: {final.get('status', 'manual_review_required')}",
        f"Becomes new active research lead: {lead_answer(final.get('status', ''))}",
        f"Full-period evidence: {evidence_line(evidence, 'full_period_evidence')}",
        f"Split evidence: {evidence_line(evidence, 'fixed_split_evidence')}",
        f"Cost evidence: {evidence_line(evidence, 'cost_evidence')}",
        f"Drawdown evidence: {evidence_line(evidence, 'drawdown_evidence')}",
        f"Remaining blockers: {evidence_line(evidence, 'blocker_count')}",
        f"Required next step: {final.get('required_next_step', '')}",
        f"execution_approved values: {', '.join(sorted(approval_values)) or 'false'}",
        "Warning: saved lead decision does not approve orders, preview promotion, scheduling, or execution.",
    ]


def build_summary_lines(summary_row: dict[str, Any], evidence_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Codex ambitious lead decision complete. Research/report only; execution_approved=False.",
        f"Final decision label: {summary_row.get('status', 'manual_review_required')}",
        f"Becomes new active research lead: {lead_answer(summary_row.get('status', ''))}",
        f"Full-period evidence: {evidence_line(evidence_rows, 'full_period_evidence')}",
        f"Split evidence: {evidence_line(evidence_rows, 'fixed_split_evidence')}",
        f"Cost evidence: {evidence_line(evidence_rows, 'cost_evidence')}",
        f"Drawdown evidence: {evidence_line(evidence_rows, 'drawdown_evidence')}",
        f"Remaining blockers: {evidence_line(evidence_rows, 'blocker_count')}",
        f"Required next step: {summary_row.get('required_next_step', '')}",
        f"Saved decision to {output_paths['decision']}",
        f"Saved summary to {output_paths['summary']}",
        f"Saved evidence to {output_paths['evidence']}",
        "Warning: lead decision does not approve orders, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def decision_row(
    created_at: str,
    decision_area: str,
    check_name: str,
    *,
    comparison_strategy: str = "",
    metric_name: Any = "",
    metric_value: Any = "",
    reference_value: Any = "",
    metric_delta: Any = "",
    status: str,
    severity: str,
    evidence: str,
    interpretation: str,
    required_next_step: str = "Manual research review only; do not connect to execution.",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "codex_ambitious_lead_decision",
        "decision_area": decision_area,
        "check_name": check_name,
        "strategy_name": TARGET_STRATEGY,
        "comparison_strategy": comparison_strategy,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "reference_value": reference_value,
        "metric_delta": metric_delta,
        "status": status,
        "severity": severity,
        "evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "promotion_approved": False,
        "scheduling_approved": False,
    }


def required_next_step(label: str) -> str:
    if label == "codex_ambitious_new_active_research_lead":
        return "Manual docs update may mark the candidate as active research lead; execution and preview promotion remain unapproved."
    if label == "codex_ambitious_active_research_lead_cost_review_required":
        return "Manual docs update may mark this as active research lead with cost review still open; do not approve execution."
    if label == "codex_ambitious_blocked_missing_inputs":
        return "Regenerate missing saved validation inputs before deciding the research lead."
    if label == "codex_ambitious_split_sensitive":
        return "Review split dependence before any research-lead change."
    if label == "codex_ambitious_cost_fragile":
        return "Review cost sensitivity before any research-lead change."
    return "Manual research review required; do not connect to execution."


def evidence_line(rows: list[dict[str, Any]], check_name: str) -> str:
    row = next((item for item in rows if item.get("check_name") == check_name), {})
    if not row:
        return "unavailable"
    return f"{row.get('status')}: {row.get('metric_value')}; {row.get('evidence')}"


def lead_answer(label: str) -> str:
    if label == "codex_ambitious_new_active_research_lead":
        return "yes_research_label_only"
    if label == "codex_ambitious_active_research_lead_cost_review_required":
        return "yes_research_label_with_cost_review_required"
    return "no"


def split_positive(row: dict[str, Any]) -> bool:
    if row.get("status") == "split_broken" or row.get("status") == "insufficient_saved_inputs":
        return False
    metrics = row.get("metric_value", "")
    return extract_metric(metrics, "CAGR") > 0 and extract_metric(metrics, "Calmar") > 0


def cost_survives(rows: list[dict[str, Any]], cost_bps: int) -> bool:
    return any(str(row.get("cost_level_bps")) == str(cost_bps) and row.get("status") == "cost_survives" for row in rows)


def has_true(text: str, key: str) -> bool:
    return f"{key}=True" in text or f"{key}=true" in text


def extract_metric(text: str, name: str) -> float:
    match = re.search(rf"{re.escape(name)}=([-+]?\d+(?:\.\d+)?)", text)
    return as_float(match.group(1)) if match else 0.0


def first(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(row.get("status", "") for row in rows)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMMON_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
