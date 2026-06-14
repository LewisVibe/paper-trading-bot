"""Saved-output branch decision checkpoint for the high-growth stock branch.

This checkpoint reads saved CSV artefacts only. It does not refresh market
data, call yfinance or Alpaca, load config, read positions, create orders,
write SQLite, send alerts, schedule anything, approve preview promotion, or
approve execution.
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
    "checkpoint": Path("data/high_growth_stock_branch_decision_checkpoint.csv"),
    "summary": Path("data/high_growth_stock_branch_decision_summary.csv"),
    "evidence": Path("data/high_growth_stock_branch_decision_evidence.csv"),
    "blockers": Path("data/high_growth_stock_branch_decision_blockers.csv"),
}

CHECKPOINT_COLUMNS = [
    "decision_area",
    "decision_status",
    "decision_label",
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


@dataclass
class HighGrowthStockBranchDecisionCheckpointResult:
    output_paths: dict[str, Path]
    checkpoint_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_branch_decision_checkpoint(root_dir: Path | str = ".") -> HighGrowthStockBranchDecisionCheckpointResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    decision = decide_branch(inputs)
    checkpoint_rows = build_checkpoint_rows(decision)
    summary_rows = build_summary_rows(inputs, decision)
    evidence_rows = build_evidence_rows(inputs, decision)
    blocker_rows = build_blocker_rows(inputs, decision)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["checkpoint"], CHECKPOINT_COLUMNS, checkpoint_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthStockBranchDecisionCheckpointResult(
        output_paths=output_paths,
        checkpoint_rows=checkpoint_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_high_growth_stock_branch_decision_checkpoint(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    checkpoint_path = root / OUTPUT_FILES["checkpoint"]
    if not summary_path.exists() or not checkpoint_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-branch-decision-checkpoint` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock branch decision checkpoint saved display. Research only; execution_approved=False.",
        f"Final branch decision: {summary_value(rows, 'final_branch_decision')}",
        f"Clean main stock/ETF lead: {summary_value(rows, 'clean_main_stock_etf_lead')}",
        f"High-risk branch candidate: {summary_value(rows, 'high_risk_stock_branch_candidate')}",
        f"Rejected extreme reference: {summary_value(rows, 'rejected_extreme_reference')}",
        f"Strongest reason to continue: {summary_value(rows, 'strongest_reason_to_continue')}",
        f"Strongest reason to block: {summary_value(rows, 'strongest_reason_to_block')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        f"Preview status: {summary_value(rows, 'preview_status')}",
        f"Execution status: {summary_value(rows, 'execution_status')}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
    ]


def decide_branch(inputs: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    missing = missing_input_names(inputs)
    summary = inputs.get("risk_evidence_summary", [])
    strongest_positive = summary_value(summary, "strongest_positive_evidence")
    biggest_blocker = summary_value(summary, "biggest_blocker")
    preview_status = summary_value(summary, "preview_status")
    execution_status = summary_value(summary, "execution_status")

    if not inputs.get("risk_evidence_summary") or not inputs.get("risk_evidence_review"):
        final_decision = "high_growth_branch_insufficient_saved_evidence"
        next_step = "regenerate_saved_risk_evidence_review_before_branch_decision"
    elif strongest_positive == "balanced_breakout_improves_extreme_reference" and biggest_blocker == "balanced_breakout_still_high_drawdown_vs_clean_lead":
        final_decision = "high_growth_branch_requires_final_validation_pack"
        next_step = "final_validation_pack_before_preview_candidate_discussion"
    elif biggest_blocker == "balanced_breakout_still_high_drawdown_vs_clean_lead":
        final_decision = "high_growth_branch_pause_due_to_drawdown"
        next_step = "pause_high_growth_branch_until_drawdown_blocker_is_resolved"
    else:
        final_decision = "high_growth_branch_continue_research_only"
        next_step = "continue_research_only_with_explicit_drawdown_cost_split_concentration_review"

    return {
        "final_decision": final_decision,
        "clean_main_lead": QQQ_100,
        "high_risk_candidate": BALANCED_CONTROL,
        "rejected_reference": BROAD_TOP1,
        "strongest_reason_to_continue": strongest_positive or "insufficient_saved_positive_evidence",
        "strongest_reason_to_block": biggest_blocker or "insufficient_saved_blocker_evidence",
        "recommended_next_step": next_step,
        "preview_status": preview_status or "preview_candidate_not_approved",
        "execution_status": execution_status or "execution_blocked",
        "missing_saved_inputs": "; ".join(missing) if missing else "none_for_available_saved_outputs",
    }


def build_checkpoint_rows(decision: dict[str, str]) -> list[dict[str, Any]]:
    return [
        checkpoint_row("branch_decision", "decided", decision["final_decision"], "Saved evidence supports a conservative branch decision, not preview approval.", "data/high_growth_stock_risk_evidence_summary.csv", decision["strongest_reason_to_block"], decision["recommended_next_step"]),
        checkpoint_row("clean_main_lead", "retained", "qqq100_clean_lead_retained", f"{QQQ_100} remains the clean main stock/ETF lead.", "data/high_growth_stock_lead_decision_summary.csv", "none_for_clean_lead", "Keep clean main lead separate from high-risk stock research."),
        checkpoint_row("broad_top1_reference", "rejected", "broad_top1_rejected_extreme_drawdown", f"{BROAD_TOP1} remains rejected as an extreme drawdown reference.", "data/high_growth_stock_lead_decision_summary.csv", "extreme_drawdown_reference_rejected", "Do not revive broad Top1 as a preview candidate."),
        checkpoint_row("balanced_control_branch", "research_only", "high_growth_branch_continue_research_only", f"{BALANCED_CONTROL} may continue only as a high-risk research branch when saved evidence improves versus broad Top1.", "data/high_growth_stock_risk_evidence_review.csv", "balanced_breakout_still_high_drawdown_vs_clean_lead", "Run the final validation pack before any preview-candidate discussion."),
        checkpoint_row("preview_gate", "blocked", "preview_candidate_not_approved", "The branch decision checkpoint does not approve preview promotion.", "data/high_growth_stock_risk_evidence_blockers.csv", "preview_candidate_still_blocked", "Keep preview discussion blocked until final validation is complete."),
        checkpoint_row("execution_gate", "blocked", "execution_blocked", "No paper or live execution is approved by this checkpoint.", "data/high_growth_stock_risk_evidence_blockers.csv", "execution_blocked", "Keep all strategy-to-execution paths disconnected."),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, Any]]], decision: dict[str, str]) -> list[dict[str, Any]]:  # noqa: ARG001
    return [
        summary_row("final_branch_decision", decision["final_decision"], "Conservative decision from saved risk evidence."),
        summary_row("clean_main_stock_etf_lead", decision["clean_main_lead"], "Clean main stock/ETF lead retained."),
        summary_row("high_risk_stock_branch_candidate", decision["high_risk_candidate"], "High-risk branch remains research-only unless paused by insufficient evidence."),
        summary_row("rejected_extreme_reference", decision["rejected_reference"], "Broad Top1 remains rejected."),
        summary_row("strongest_reason_to_continue", decision["strongest_reason_to_continue"], "Positive evidence is only a research reason, not preview approval."),
        summary_row("strongest_reason_to_block", decision["strongest_reason_to_block"], "Blocker keeps preview and execution unavailable."),
        summary_row("recommended_next_step", decision["recommended_next_step"], "Next step before any preview-candidate discussion."),
        summary_row("preview_status", "preview_candidate_not_approved", "Preview is not approved by this checkpoint."),
        summary_row("execution_status", "execution_blocked", "Paper/live execution is not approved."),
        summary_row("scheduling_status", "scheduling_not_approved", "Scheduling is not approved by this checkpoint."),
        summary_row("missing_saved_inputs", decision["missing_saved_inputs"], "Missing saved inputs reduce audit completeness but do not change non-execution status."),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, Any]]], decision: dict[str, str]) -> list[dict[str, Any]]:
    return [
        evidence_row("risk_evidence_status", summary_value(inputs.get("risk_evidence_summary", []), "final_evidence_review_status") or "high_growth_branch_insufficient_saved_evidence", "data/high_growth_stock_risk_evidence_summary.csv", "Risk evidence review drives the branch decision."),
        evidence_row("strongest_reason_to_continue", decision["strongest_reason_to_continue"], "data/high_growth_stock_risk_evidence_summary.csv", "Improvement versus broad Top1 can justify continued research only."),
        evidence_row("strongest_reason_to_block", decision["strongest_reason_to_block"], "data/high_growth_stock_risk_evidence_summary.csv", "Drawdown versus qqq_100 blocks preview discussion."),
        evidence_row("clean_main_lead", decision["clean_main_lead"], "data/high_growth_stock_lead_decision_summary.csv", "QQQ 100 trend gate remains clean main lead."),
        evidence_row("high_risk_candidate", decision["high_risk_candidate"], "data/high_growth_stock_lead_decision_summary.csv", "Balanced breakout control remains high-risk research-only unless paused."),
        evidence_row("rejected_broad_top1", decision["rejected_reference"], "data/high_growth_stock_lead_decision_summary.csv", "Broad Top1 remains rejected."),
        evidence_row("saved_inputs_present", str(len(INPUT_FILES) - len(missing_input_names(inputs))), "saved CSV inventory", "Counts saved inputs available to this branch checkpoint."),
    ]


def build_blocker_rows(inputs: dict[str, list[dict[str, Any]]], decision: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("balanced_breakout_still_high_drawdown_vs_clean_lead", "blocked", "critical", "Drawdown remains worse than qqq_100 and blocks preview discussion.", "Complete final validation before any preview-candidate discussion."),
        blocker_row("cost_split_concentration_evidence_required", "blocked", "high", "Cost, split, and concentration evidence still require manual review.", "Review saved evidence rows before final validation."),
        blocker_row("preview_candidate_not_approved", "blocked", "critical", "Preview is not approved by this branch decision checkpoint.", "Do not promote the branch automatically."),
        blocker_row("execution_blocked", "blocked", "critical", "Paper/live execution is not approved.", "Keep execution paths untouched."),
        blocker_row("scheduling_not_approved", "blocked", "high", "Scheduling is not approved by this checkpoint.", "Do not schedule branch decision or execution workflows."),
    ]
    missing = missing_input_names(inputs)
    if missing:
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", "; ".join(missing), "Regenerate missing saved reports only through safe report commands if needed."))
    if decision["final_decision"] == "high_growth_branch_insufficient_saved_evidence":
        rows.append(blocker_row("insufficient_saved_evidence", "blocked", "critical", "Risk evidence review outputs are missing or incomplete.", "Run the saved-output risk evidence review before deciding the branch."))
    return rows


def checkpoint_row(area: str, status: str, label: str, finding: str, source: str, blocker: str, next_step: str) -> dict[str, Any]:
    return {"decision_area": area, "decision_status": status, "decision_label": label, "finding": finding, "evidence_source": source, "blocker": blocker, "recommended_next_step": next_step, **safety_flags()}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def evidence_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "evidence_source": source, "details": details, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step, **safety_flags()}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock branch decision checkpoint complete. Research only; execution_approved=False.",
        f"Final branch decision: {summary_value(summary_rows, 'final_branch_decision')}",
        f"Clean main stock/ETF lead: {summary_value(summary_rows, 'clean_main_stock_etf_lead')}",
        f"High-risk branch candidate: {summary_value(summary_rows, 'high_risk_stock_branch_candidate')}",
        f"Rejected extreme reference: {summary_value(summary_rows, 'rejected_extreme_reference')}",
        f"Strongest reason to continue: {summary_value(summary_rows, 'strongest_reason_to_continue')}",
        f"Strongest reason to block: {summary_value(summary_rows, 'strongest_reason_to_block')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Preview status: {summary_value(summary_rows, 'preview_status')}",
        f"Execution status: {summary_value(summary_rows, 'execution_status')}",
        f"Saved checkpoint to {output_paths['checkpoint']}",
        f"Saved summary/evidence/blockers to {output_paths['summary']}; {output_paths['evidence']}; {output_paths['blockers']}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved-output branch decision only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
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
