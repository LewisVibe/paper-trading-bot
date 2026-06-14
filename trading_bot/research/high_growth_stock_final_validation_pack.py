"""Saved-output final validation pack for the high-growth stock branch.

This pack reads saved CSV artefacts only. It does not refresh market data,
call yfinance or Alpaca, load config, read positions, create orders, write
SQLite, send alerts, schedule anything, approve preview promotion, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


QQQ_100 = "qqq_100_trend_gate"
BALANCED_CONTROL = "codex_broad_growth_balanced_breakout_control"
BROAD_TOP1 = "broad_liquid_growth_50:concentrated_growth_momentum_top1"

INPUT_FILES = {
    "branch_decision_checkpoint": Path("data/high_growth_stock_branch_decision_checkpoint.csv"),
    "branch_decision_summary": Path("data/high_growth_stock_branch_decision_summary.csv"),
    "branch_decision_evidence": Path("data/high_growth_stock_branch_decision_evidence.csv"),
    "branch_decision_blockers": Path("data/high_growth_stock_branch_decision_blockers.csv"),
    "risk_evidence_review": Path("data/high_growth_stock_risk_evidence_review.csv"),
    "risk_evidence_summary": Path("data/high_growth_stock_risk_evidence_summary.csv"),
    "risk_evidence_details": Path("data/high_growth_stock_risk_evidence_details.csv"),
    "risk_evidence_blockers": Path("data/high_growth_stock_risk_evidence_blockers.csv"),
    "risk_review_pack": Path("data/high_growth_stock_risk_review_pack.csv"),
    "risk_review_summary": Path("data/high_growth_stock_risk_review_summary.csv"),
    "risk_review_evidence": Path("data/high_growth_stock_risk_review_evidence.csv"),
    "risk_review_blockers": Path("data/high_growth_stock_risk_review_blockers.csv"),
    "manual_review_pack": Path("data/high_growth_stock_manual_review_pack.csv"),
    "manual_review_summary": Path("data/high_growth_stock_manual_review_summary.csv"),
    "manual_review_evidence": Path("data/high_growth_stock_manual_review_evidence.csv"),
    "manual_review_blockers": Path("data/high_growth_stock_manual_review_blockers.csv"),
    "lead_decision_report": Path("data/high_growth_stock_lead_decision_report.csv"),
    "lead_decision_summary": Path("data/high_growth_stock_lead_decision_summary.csv"),
    "lead_decision_evidence": Path("data/high_growth_stock_lead_decision_evidence.csv"),
    "lead_decision_blockers": Path("data/high_growth_stock_lead_decision_blockers.csv"),
    "high_growth_lab_report": Path("data/high_growth_stock_lab.csv"),
    "high_growth_lab_summary": Path("data/high_growth_stock_lab_summary.csv"),
    "universe_expansion_report": Path("data/high_growth_stock_universe_expansion_report.csv"),
    "universe_expansion_summary": Path("data/high_growth_stock_universe_expansion_summary.csv"),
    "drawdown_control_report": Path("data/high_growth_stock_drawdown_control_report.csv"),
    "drawdown_control_summary": Path("data/high_growth_stock_drawdown_control_summary.csv"),
    "drawdown_control_costs": Path("data/high_growth_stock_drawdown_control_costs.csv"),
    "drawdown_control_splits": Path("data/high_growth_stock_drawdown_control_splits.csv"),
    "drawdown_control_drawdowns": Path("data/high_growth_stock_drawdown_control_drawdowns.csv"),
    "drawdown_control_concentration": Path("data/high_growth_stock_drawdown_control_concentration.csv"),
    "qqq_lead_decision_report": Path("data/qqq_lead_decision_report.csv"),
    "qqq_lead_decision_summary": Path("data/qqq_lead_decision_summary.csv"),
    "qqq_trend_gate_manual_review_pack": Path("data/qqq_trend_gate_manual_review_pack.csv"),
    "qqq_preview_candidate_readiness_report": Path("data/qqq_preview_candidate_readiness_report.csv"),
    "project_research_state_summary": Path("data/project_research_state_summary.csv"),
    "project_research_state_next_steps": Path("data/project_research_state_next_steps.csv"),
}

OUTPUT_FILES = {
    "pack": Path("data/high_growth_stock_final_validation_pack.csv"),
    "summary": Path("data/high_growth_stock_final_validation_summary.csv"),
    "evidence": Path("data/high_growth_stock_final_validation_evidence.csv"),
    "blockers": Path("data/high_growth_stock_final_validation_blockers.csv"),
}

PACK_COLUMNS = [
    "validation_area",
    "validation_status",
    "validation_label",
    "finding",
    "evidence_source",
    "blocker",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_value",
    "evidence_source",
    "details",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": True,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
}

POSSIBLE_VALIDATION_LABELS = [
    "high_growth_ready_for_manual_preview_discussion",
    "high_growth_needs_more_research_validation",
    "high_growth_paused_due_to_drawdown",
    "insufficient_saved_evidence",
]


@dataclass
class HighGrowthStockFinalValidationPackResult:
    output_paths: dict[str, Path]
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_final_validation_pack(root_dir: Path | str = ".") -> HighGrowthStockFinalValidationPackResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    validation = decide_validation(inputs)
    pack_rows = build_pack_rows(validation)
    summary_rows = build_summary_rows(inputs, validation)
    evidence_rows = build_evidence_rows(inputs, validation)
    blocker_rows = build_blocker_rows(inputs, validation)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], PACK_COLUMNS, pack_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthStockFinalValidationPackResult(
        output_paths=output_paths,
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_high_growth_stock_final_validation_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    pack_path = root / OUTPUT_FILES["pack"]
    if not summary_path.exists() or not pack_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-final-validation-pack` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock final validation pack saved display. Research only; execution_approved=False.",
        f"Final validation status: {summary_value(rows, 'final_validation_status')}",
        f"Clean main stock/ETF lead: {summary_value(rows, 'clean_main_stock_etf_lead')}",
        f"High-risk candidate: {summary_value(rows, 'high_risk_stock_candidate')}",
        f"Rejected extreme reference: {summary_value(rows, 'rejected_extreme_reference')}",
        f"Preview-discussion readiness: {summary_value(rows, 'preview_discussion_readiness')}",
        f"Strongest positive evidence: {summary_value(rows, 'strongest_positive_evidence')}",
        f"Largest remaining blocker: {summary_value(rows, 'largest_remaining_blocker')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        f"Preview status: {summary_value(rows, 'preview_status')}",
        f"Execution status: {summary_value(rows, 'execution_status')}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
    ]


def decide_validation(inputs: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    missing = missing_input_names(inputs)
    branch_summary = inputs.get("branch_decision_summary", [])
    risk_evidence_summary = inputs.get("risk_evidence_summary", [])
    branch_decision = summary_value(branch_summary, "final_branch_decision")
    strongest_positive = summary_value(branch_summary, "strongest_reason_to_continue") or summary_value(risk_evidence_summary, "strongest_positive_evidence")
    largest_blocker = summary_value(branch_summary, "strongest_reason_to_block") or summary_value(risk_evidence_summary, "biggest_blocker")

    if not inputs.get("branch_decision_summary") or not inputs.get("risk_evidence_summary"):
        final_status = "insufficient_saved_evidence"
        readiness = "preview_discussion_not_ready"
        next_step = "regenerate_saved_branch_decision_and_risk_evidence_before_final_validation"
    elif branch_decision == "high_growth_branch_requires_final_validation_pack" and strongest_positive == "balanced_breakout_improves_extreme_reference" and largest_blocker == "balanced_breakout_still_high_drawdown_vs_clean_lead":
        final_status = "needs_more_research_validation"
        readiness = "manual_preview_discussion_not_ready_yet"
        next_step = "design_targeted_drawdown_cost_split_concentration_follow_up_before_preview_discussion"
    elif largest_blocker == "balanced_breakout_still_high_drawdown_vs_clean_lead":
        final_status = "paused_due_to_drawdown_or_evidence_quality"
        readiness = "preview_discussion_not_ready"
        next_step = "pause_high_growth_branch_until_drawdown_blocker_is_resolved"
    else:
        final_status = "ready_for_manual_preview_candidate_discussion"
        readiness = "manual_preview_discussion_ready_but_not_approved"
        next_step = "manual_preview_candidate_discussion_only_no_execution_approval"

    return {
        "final_status": final_status,
        "preview_discussion_readiness": readiness,
        "clean_main_lead": QQQ_100,
        "high_risk_candidate": BALANCED_CONTROL,
        "rejected_reference": BROAD_TOP1,
        "strongest_positive_evidence": strongest_positive or "insufficient_saved_positive_evidence",
        "largest_remaining_blocker": largest_blocker or "insufficient_saved_blocker_evidence",
        "recommended_next_step": next_step,
        "preview_status": "preview_candidate_not_approved",
        "execution_status": "execution_blocked",
        "missing_saved_inputs": "; ".join(missing) if missing else "none_for_available_saved_outputs",
    }


def build_pack_rows(validation: dict[str, str]) -> list[dict[str, Any]]:
    return [
        pack_row("final_validation_status", "decided", "high_growth_final_validation_required", "Final validation converts saved branch evidence into a conservative preview-discussion readiness status.", "data/high_growth_stock_branch_decision_summary.csv", validation["largest_remaining_blocker"], validation["recommended_next_step"]),
        pack_row("return_improvement_vs_qqq100", "positive_but_not_sufficient", "high_risk_candidate_research_only", "Saved evidence supports return improvement versus qqq_100 only as high-risk research evidence.", "data/high_growth_stock_risk_evidence_summary.csv", "tail_risk_compensation_unproven", "Review whether return compensates for drawdown and concentration risk."),
        pack_row("drawdown_worsening_vs_qqq100", "blocking_review", "high_growth_needs_more_research_validation", "Saved evidence still names worse drawdown versus qqq_100 as the largest blocker.", "data/high_growth_stock_branch_decision_summary.csv", "balanced_breakout_still_high_drawdown_vs_clean_lead", "Run targeted drawdown validation before preview discussion."),
        pack_row("drawdown_improvement_vs_broad_top1", "positive_reference_control", "high_risk_candidate_research_only", "Saved evidence supports the balanced candidate as an improvement over the rejected broad Top1 reference.", "data/high_growth_stock_risk_evidence_summary.csv", "tail_risk_still_material", "Continue only as research unless blockers are reduced to reviewable warnings."),
        pack_row("calmar_sharpe_tradeoff", "review_required", "high_growth_final_validation_required", "Calmar/Sharpe evidence must be read alongside drawdown, concentration, and bias risks.", "data/high_growth_stock_lead_decision_report.csv", "risk_adjusted_metrics_not_sufficient", "Review risk-adjusted metrics in the follow-up pack."),
        pack_row("cost_sensitivity", "review_required", "high_growth_needs_more_research_validation", "Cost sensitivity remains a final-validation input, not a solved preview gate.", "data/high_growth_stock_drawdown_control_costs.csv", "cost_evidence_review_required", "Review fixed-cost assumptions before preview discussion."),
        pack_row("split_sensitivity", "review_required", "high_growth_needs_more_research_validation", "Split sensitivity remains a final-validation input, not a solved preview gate.", "data/high_growth_stock_drawdown_control_splits.csv", "split_evidence_review_required", "Review chronological splits before preview discussion."),
        pack_row("concentration_risk", "review_required", "high_growth_needs_more_research_validation", "Concentration and outlier dependence remain unresolved branch risks.", "data/high_growth_stock_drawdown_control_concentration.csv", "concentration_evidence_review_required", "Review largest-contributor dependence."),
        pack_row("survivorship_bias", "warning", "high_growth_needs_more_research_validation", "Current-constituent and survivorship bias remain unresolved.", "data/high_growth_stock_universe_expansion_report.csv", "survivorship_bias_warning", "Do not treat current-constituent results as deployment-grade."),
        pack_row("portfolio_role", "not_clear_enough", "high_growth_needs_more_research_validation", f"{BALANCED_CONTROL} still needs a clear portfolio role separate from {QQQ_100}.", "data/high_growth_stock_branch_decision_summary.csv", "portfolio_role_unclear", "Define whether this branch is a satellite research branch only."),
        pack_row("clean_main_lead", "retained", "qqq100_clean_lead_retained", f"{QQQ_100} remains the clean main stock/ETF lead.", "data/high_growth_stock_lead_decision_summary.csv", "none_for_clean_lead", "Keep clean lead separate from high-risk stock research."),
        pack_row("broad_top1_reference", "rejected", "broad_top1_rejected_extreme_drawdown", f"{BROAD_TOP1} remains rejected as the extreme drawdown reference.", "data/high_growth_stock_lead_decision_summary.csv", "extreme_drawdown_reference_rejected", "Do not revive broad Top1."),
        pack_row("preview_gate", "blocked", "preview_candidate_not_approved", "This final validation pack does not approve preview promotion automatically.", "data/high_growth_stock_branch_decision_blockers.csv", "preview_candidate_not_approved", "Preview discussion remains manual-only and not approved by this report."),
        pack_row("execution_gate", "blocked", "execution_blocked", "This final validation pack does not approve paper or live execution.", "data/high_growth_stock_branch_decision_blockers.csv", "execution_blocked", "Keep execution paths untouched."),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, Any]]], validation: dict[str, str]) -> list[dict[str, Any]]:  # noqa: ARG001
    return [
        summary_row("final_validation_status", validation["final_status"], "Conservative final validation status from saved evidence."),
        summary_row("preview_discussion_readiness", validation["preview_discussion_readiness"], "Readiness for manual preview-candidate discussion only; preview is not approved."),
        summary_row("clean_main_stock_etf_lead", validation["clean_main_lead"], "Clean main stock/ETF lead retained."),
        summary_row("high_risk_stock_candidate", validation["high_risk_candidate"], "High-risk candidate remains research-only unless paused."),
        summary_row("rejected_extreme_reference", validation["rejected_reference"], "Broad Top1 remains rejected."),
        summary_row("strongest_positive_evidence", validation["strongest_positive_evidence"], "Positive evidence supports only continued research."),
        summary_row("largest_remaining_blocker", validation["largest_remaining_blocker"], "Largest blocker keeps preview and execution unavailable."),
        summary_row("recommended_next_step", validation["recommended_next_step"], "Next step before any manual preview-candidate discussion."),
        summary_row("preview_status", validation["preview_status"], "Preview is not approved by this validation pack."),
        summary_row("execution_status", validation["execution_status"], "Paper/live execution is not approved."),
        summary_row("scheduling_status", "scheduling_not_approved", "Scheduling is not approved by this validation pack."),
        summary_row("missing_saved_inputs", validation["missing_saved_inputs"], "Missing saved inputs reduce audit completeness but do not change non-execution status."),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, Any]]], validation: dict[str, str]) -> list[dict[str, Any]]:
    return [
        evidence_row("branch_decision", summary_value(inputs.get("branch_decision_summary", []), "final_branch_decision") or "insufficient_saved_evidence", "data/high_growth_stock_branch_decision_summary.csv", "Branch decision is the direct input to final validation."),
        evidence_row("risk_evidence_status", summary_value(inputs.get("risk_evidence_summary", []), "final_evidence_review_status") or "insufficient_saved_evidence", "data/high_growth_stock_risk_evidence_summary.csv", "Risk evidence remains the underlying saved evidence source."),
        evidence_row("strongest_positive_evidence", validation["strongest_positive_evidence"], "data/high_growth_stock_branch_decision_summary.csv", "Improvement over broad Top1 supports continued research only."),
        evidence_row("largest_remaining_blocker", validation["largest_remaining_blocker"], "data/high_growth_stock_branch_decision_summary.csv", "Drawdown versus qqq_100 remains the largest blocker."),
        evidence_row("clean_main_lead", validation["clean_main_lead"], "data/high_growth_stock_lead_decision_summary.csv", "QQQ 100 trend gate remains clean main lead."),
        evidence_row("high_risk_candidate", validation["high_risk_candidate"], "data/high_growth_stock_lead_decision_summary.csv", "Balanced breakout control remains high-risk research-only."),
        evidence_row("rejected_broad_top1", validation["rejected_reference"], "data/high_growth_stock_lead_decision_summary.csv", "Broad Top1 remains rejected."),
        evidence_row("saved_inputs_present", str(len(INPUT_FILES) - len(missing_input_names(inputs))), "saved CSV inventory", "Counts saved inputs available to this final validation pack."),
    ]


def build_blocker_rows(inputs: dict[str, list[dict[str, Any]]], validation: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("balanced_breakout_still_high_drawdown_vs_clean_lead", "blocked", "critical", "Drawdown versus qqq_100 remains the largest blocker.", "Run targeted drawdown validation before preview discussion."),
        blocker_row("cost_split_concentration_review_required", "blocked", "high", "Cost, split, and concentration evidence still require manual review.", "Review saved evidence before manual preview discussion."),
        blocker_row("portfolio_role_unclear", "blocked", "medium", "The branch still needs a clear portfolio role separate from qqq_100.", "Define whether this remains a satellite high-risk research branch."),
        blocker_row("preview_candidate_not_approved", "blocked", "critical", "Preview promotion is not approved by this final validation pack.", "Do not promote automatically."),
        blocker_row("execution_blocked", "blocked", "critical", "Paper/live execution is not approved.", "Keep execution paths untouched."),
        blocker_row("scheduling_not_approved", "blocked", "high", "Scheduling is not approved by this validation pack.", "Do not schedule this branch or execution workflows."),
    ]
    missing = missing_input_names(inputs)
    if missing:
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", "; ".join(missing), "Regenerate missing saved reports only through safe report commands if needed."))
    if validation["final_status"] == "insufficient_saved_evidence":
        rows.append(blocker_row("insufficient_saved_evidence", "blocked", "critical", "Branch decision or risk evidence outputs are missing.", "Run saved branch decision and risk evidence commands first."))
    return rows


def pack_row(area: str, status: str, label: str, finding: str, source: str, blocker: str, next_step: str) -> dict[str, Any]:
    return {"validation_area": area, "validation_status": status, "validation_label": label, "finding": finding, "evidence_source": source, "blocker": blocker, "recommended_next_step": next_step, **safety_flags()}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def evidence_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "evidence_source": source, "details": details, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step, **safety_flags()}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock final validation pack complete. Research only; execution_approved=False.",
        f"Final validation status: {summary_value(summary_rows, 'final_validation_status')}",
        f"Clean main stock/ETF lead: {summary_value(summary_rows, 'clean_main_stock_etf_lead')}",
        f"High-risk candidate: {summary_value(summary_rows, 'high_risk_stock_candidate')}",
        f"Rejected extreme reference: {summary_value(summary_rows, 'rejected_extreme_reference')}",
        f"Preview-discussion readiness: {summary_value(summary_rows, 'preview_discussion_readiness')}",
        f"Strongest positive evidence: {summary_value(summary_rows, 'strongest_positive_evidence')}",
        f"Largest remaining blocker: {summary_value(summary_rows, 'largest_remaining_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Preview status: {summary_value(summary_rows, 'preview_status')}",
        f"Execution status: {summary_value(summary_rows, 'execution_status')}",
        f"Saved pack to {output_paths['pack']}",
        f"Saved summary/evidence/blockers to {output_paths['summary']}; {output_paths['evidence']}; {output_paths['blockers']}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved-output final validation only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
    ]


def missing_input_names(inputs: dict[str, list[dict[str, Any]]]) -> list[str]:
    return [name for name, rows in inputs.items() if not rows]


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
