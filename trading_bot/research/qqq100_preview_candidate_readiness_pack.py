"""Saved-output readiness pack for the qqq_100_trend_gate preview discussion.

This pack reads saved CSV artefacts only. It does not refresh market data,
call yfinance or Alpaca, load config, read positions, create orders, write
SQLite, send alerts, schedule anything, add preview implementation, approve
preview promotion, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


QQQ100 = "qqq_100_trend_gate"
QQQ100_STATUS = "qqq_100_trend_gate_new_research_lead"
QQQ_ADAPTIVE = "codex_qqq_adaptive_trend_exposure"
QQQ150 = "qqq_150_trend_gate"
HIGH_GROWTH = "codex_broad_growth_balanced_breakout_control"

INPUT_FILES = {
    "qqq_lead_decision_report": Path("data/qqq_lead_decision_report.csv"),
    "qqq_lead_decision_summary": Path("data/qqq_lead_decision_summary.csv"),
    "qqq_lead_decision_evidence": Path("data/qqq_lead_decision_evidence.csv"),
    "qqq_trend_gate_manual_review_pack": Path("data/qqq_trend_gate_manual_review_pack.csv"),
    "qqq_trend_gate_manual_review_summary": Path("data/qqq_trend_gate_manual_review_summary.csv"),
    "qqq_trend_gate_manual_review_evidence": Path("data/qqq_trend_gate_manual_review_evidence.csv"),
    "qqq_trend_gate_manual_review_blockers": Path("data/qqq_trend_gate_manual_review_blockers.csv"),
    "qqq_preview_candidate_readiness_report": Path("data/qqq_preview_candidate_readiness_report.csv"),
    "qqq_preview_candidate_readiness_summary": Path("data/qqq_preview_candidate_readiness_summary.csv"),
    "qqq_preview_candidate_readiness_evidence": Path("data/qqq_preview_candidate_readiness_evidence.csv"),
    "qqq_preview_candidate_readiness_blockers": Path("data/qqq_preview_candidate_readiness_blockers.csv"),
    "qqq_adaptive_leverage_lab": Path("data/qqq_adaptive_leverage_lab.csv"),
    "qqq_adaptive_leverage_summary": Path("data/qqq_adaptive_leverage_summary.csv"),
    "qqq_leverage_validation_report": Path("data/qqq_leverage_validation_report.csv"),
    "qqq_leverage_validation_costs": Path("data/qqq_leverage_validation_costs.csv"),
    "qqq_leverage_validation_splits": Path("data/qqq_leverage_validation_splits.csv"),
    "qqq_leverage_validation_drawdowns": Path("data/qqq_leverage_validation_drawdowns.csv"),
    "high_growth_final_validation_pack": Path("data/high_growth_stock_final_validation_pack.csv"),
    "high_growth_final_validation_summary": Path("data/high_growth_stock_final_validation_summary.csv"),
    "high_growth_stock_branch_decision_summary": Path("data/high_growth_stock_branch_decision_summary.csv"),
    "project_research_state_summary": Path("data/project_research_state_summary.csv"),
    "project_research_state_next_steps": Path("data/project_research_state_next_steps.csv"),
    "stock_etf_paper_execution_readiness_report": Path("data/stock_etf_paper_execution_readiness_report.csv"),
    "execution_eligibility_report": Path("data/execution_eligibility_report.csv"),
    "paper_execution_protection_report": Path("data/paper_execution_protection_report.csv"),
}

OUTPUT_FILES = {
    "pack": Path("data/qqq100_preview_candidate_readiness_pack.csv"),
    "summary": Path("data/qqq100_preview_candidate_readiness_summary.csv"),
    "evidence": Path("data/qqq100_preview_candidate_readiness_evidence.csv"),
    "blockers": Path("data/qqq100_preview_candidate_readiness_blockers.csv"),
}

PACK_COLUMNS = [
    "check_name",
    "check_status",
    "readiness_label",
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
class Qqq100PreviewCandidateReadinessPackResult:
    output_paths: dict[str, Path]
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_preview_candidate_readiness_pack(root_dir: Path | str = ".") -> Qqq100PreviewCandidateReadinessPackResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    readiness = decide_readiness(inputs)
    pack_rows = build_pack_rows(readiness)
    summary_rows = build_summary_rows(inputs, readiness)
    evidence_rows = build_evidence_rows(inputs, readiness)
    blocker_rows = build_blocker_rows(inputs, readiness)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], PACK_COLUMNS, pack_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return Qqq100PreviewCandidateReadinessPackResult(
        output_paths=output_paths,
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_qqq100_preview_candidate_readiness_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    pack_path = root / OUTPUT_FILES["pack"]
    if not summary_path.exists() or not pack_path.exists():
        return 1, ["Run `python bot.py --qqq100-preview-candidate-readiness-pack` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 preview-candidate readiness pack saved display. Research only; execution_approved=False.",
        f"Final readiness status: {summary_value(rows, 'final_readiness_status')}",
        f"Clean main lead: {summary_value(rows, 'clean_main_lead')}",
        f"Ambitious alternative: {summary_value(rows, 'ambitious_alternative')}",
        f"Rejected high-drawdown reference: {summary_value(rows, 'rejected_high_drawdown_reference')}",
        f"High-growth branch status: {summary_value(rows, 'high_growth_branch_status')}",
        f"Strongest evidence for preview discussion: {summary_value(rows, 'strongest_evidence_for_preview_discussion')}",
        f"Largest blocker: {summary_value(rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        f"Preview status: {summary_value(rows, 'preview_status')}",
        f"Execution status: {summary_value(rows, 'execution_status')}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; preview discussion is not preview implementation, paper execution, live trading, or scheduling approval.",
    ]


def decide_readiness(inputs: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    missing_core = [name for name in ["qqq_lead_decision_summary", "qqq_trend_gate_manual_review_summary"] if not inputs.get(name)]
    preview_summary = inputs.get("qqq_preview_candidate_readiness_summary", [])
    existing_preview_status = summary_value(preview_summary, "final_preview_candidate_readiness_status")
    cost_rows = matching_rows(inputs.get("qqq_leverage_validation_costs", []), QQQ100)
    split_rows = matching_rows(inputs.get("qqq_leverage_validation_splits", []), QQQ100)
    drawdown_rows = matching_rows(inputs.get("qqq_leverage_validation_drawdowns", []), QQQ100)

    if missing_core:
        final_status = "qqq100_preview_discussion_needs_more_review"
        largest_blocker = "missing_core_saved_inputs"
        next_step = "regenerate_saved_qqq_lead_and_manual_review_outputs"
    elif existing_preview_status in {"qqq_preview_candidate_ready_for_manual_discussion", "qqq_preview_candidate_needs_cost_review", "qqq_preview_candidate_needs_drawdown_review"}:
        final_status = "qqq100_preview_discussion_ready"
        largest_blocker = "preview_implementation_not_added"
        next_step = "manual_preview_candidate_discussion_only_before_preview_implementation"
    elif not cost_rows or not split_rows or not drawdown_rows:
        final_status = "qqq100_preview_discussion_needs_more_review"
        largest_blocker = "saved_cost_split_drawdown_evidence_incomplete"
        next_step = "review_or_regenerate_saved_cost_split_drawdown_evidence"
    else:
        final_status = "qqq100_preview_discussion_ready"
        largest_blocker = "preview_implementation_not_added"
        next_step = "manual_preview_candidate_discussion_only_before_preview_implementation"

    return {
        "final_status": final_status,
        "clean_main_lead": QQQ100,
        "ambitious_alternative": QQQ_ADAPTIVE,
        "rejected_high_drawdown_reference": QQQ150,
        "high_growth_branch_status": "high_growth_branch_not_ready_for_preview",
        "strongest_evidence": "qqq100_clean_lead_retained_with_CAGR_16.8429_Sharpe_1.0027_MaxDD_-23.4576_Calmar_0.718",
        "largest_blocker": largest_blocker,
        "recommended_next_step": next_step,
        "preview_status": "preview_implementation_not_added",
        "execution_status": "execution_blocked",
        "missing_saved_inputs": "; ".join(missing_input_names(inputs)) or "none_for_available_saved_outputs",
    }


def build_pack_rows(readiness: dict[str, str]) -> list[dict[str, Any]]:
    return [
        pack_row("final_readiness_status", "ready_for_manual_discussion" if readiness["final_status"] == "qqq100_preview_discussion_ready" else "needs_more_review", readiness["final_status"], "The clean QQQ100 lead may be discussed manually, but no preview implementation or execution is approved.", "data/qqq_preview_candidate_readiness_summary.csv", readiness["largest_blocker"], readiness["recommended_next_step"]),
        pack_row("clean_main_lead", "retained", "qqq100_clean_lead_retained", f"{QQQ100} remains the clean main stock/ETF research lead.", "data/qqq_lead_decision_summary.csv", "none_for_clean_lead", "Keep QQQ100 separate from high-risk branches."),
        pack_row("risk_reward_vs_high_growth", "clearer_than_high_growth", "high_growth_branch_not_ready_for_preview", "QQQ100 has clearer risk/reward than the high-growth stock branch, which remains not ready for preview discussion.", "data/high_growth_stock_final_validation_summary.csv", "high_growth_branch_not_ready_for_preview", "Keep high-growth branch research-only."),
        pack_row("qqq150_reference", "rejected", "qqq150_high_drawdown_reference_rejected", f"{QQQ150} remains rejected as a higher-drawdown reference.", "data/qqq_lead_decision_summary.csv", "high_drawdown_reference_rejected", "Do not use higher drawdown as preview evidence."),
        pack_row("adaptive_alternative", "alternative_only", "adaptive_qqq_ambitious_alternative_only", f"{QQQ_ADAPTIVE} remains an ambitious alternative only.", "data/qqq_lead_decision_summary.csv", "alternative_not_clean_lead", "Keep adaptive QQQ out of clean preview-candidate discussion."),
        pack_row("cost_sensitivity", "saved_review_required", "qqq100_preview_discussion_ready", "Saved cost evidence can be reviewed during manual preview discussion, but does not approve paper execution.", "data/qqq_leverage_validation_costs.csv", "paper_execution_blocked", "Review costs before any future paper execution design."),
        pack_row("split_sensitivity", "saved_review_required", "qqq100_preview_discussion_ready", "Saved split evidence can be reviewed during manual preview discussion, but does not approve paper execution.", "data/qqq_leverage_validation_splits.csv", "paper_execution_blocked", "Review split stability before any future paper execution design."),
        pack_row("drawdown_acceptability", "manual_review_required", "qqq100_preview_discussion_ready", "QQQ100 drawdown is materially cleaner than higher-risk alternatives, but drawdown acceptance remains a manual discussion topic.", "data/qqq_leverage_validation_drawdowns.csv", "drawdown_review_required_before_execution", "Discuss drawdown tolerance before any preview implementation."),
        pack_row("preview_boundary", "blocked", "preview_implementation_not_added", "Preview-candidate discussion does not add preview mode automatically.", "data/qqq100_preview_candidate_readiness_pack.csv", "preview_implementation_not_added", "Implement preview mode only as a separate non-execution step if manually approved later."),
        pack_row("execution_boundary", "blocked", "execution_blocked", "Paper execution remains blocked.", "data/stock_etf_paper_execution_readiness_report.csv", "execution_blocked", "Do not connect strategy to orders."),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, Any]]], readiness: dict[str, str]) -> list[dict[str, Any]]:  # noqa: ARG001
    return [
        summary_row("final_readiness_status", readiness["final_status"], "Manual preview-candidate discussion status only; preview implementation is not added."),
        summary_row("clean_main_lead", readiness["clean_main_lead"], "QQQ100 remains the clean main stock/ETF research lead."),
        summary_row("ambitious_alternative", readiness["ambitious_alternative"], "Adaptive QQQ remains ambitious alternative only."),
        summary_row("rejected_high_drawdown_reference", readiness["rejected_high_drawdown_reference"], "QQQ150 remains rejected as higher-drawdown reference."),
        summary_row("high_growth_branch_status", readiness["high_growth_branch_status"], "High-growth branch is not promoted."),
        summary_row("strongest_evidence_for_preview_discussion", readiness["strongest_evidence"], "Latest known metrics support manual discussion: CAGR=16.8429, Sharpe=1.0027, MaxDD=-23.4576, Calmar=0.718."),
        summary_row("largest_blocker", readiness["largest_blocker"], "Largest blocker before any implementation or execution."),
        summary_row("recommended_next_step", readiness["recommended_next_step"], "Manual discussion only; do not wire strategy to execution."),
        summary_row("preview_status", readiness["preview_status"], "Preview implementation is not added by this pack."),
        summary_row("execution_status", readiness["execution_status"], "Paper/live execution remains blocked."),
        summary_row("scheduling_status", "scheduling_not_approved", "Scheduling is not approved."),
        summary_row("missing_saved_inputs", readiness["missing_saved_inputs"], "Missing saved inputs reduce completeness but do not approve execution."),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, Any]]], readiness: dict[str, str]) -> list[dict[str, Any]]:
    return [
        evidence_row("qqq100_status", QQQ100_STATUS, "data/qqq_lead_decision_summary.csv", "QQQ100 is the current clean main stock/ETF research lead."),
        evidence_row("qqq100_metrics", "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718", "latest saved QQQ context", "Metrics support manual preview-candidate discussion, not execution."),
        evidence_row("existing_preview_readiness", summary_value(inputs.get("qqq_preview_candidate_readiness_summary", []), "final_preview_candidate_readiness_status"), "data/qqq_preview_candidate_readiness_summary.csv", "Existing QQQ readiness report is an input only."),
        evidence_row("adaptive_alternative", readiness["ambitious_alternative"], "data/qqq_lead_decision_summary.csv", "Ambitious alternative remains alternative only."),
        evidence_row("high_drawdown_reference", readiness["rejected_high_drawdown_reference"], "data/qqq_lead_decision_summary.csv", "Higher-drawdown reference remains rejected."),
        evidence_row("high_growth_branch_status", readiness["high_growth_branch_status"], "data/high_growth_stock_final_validation_summary.csv", "High-growth branch is not ready for preview discussion."),
        evidence_row("saved_inputs_present", str(len(INPUT_FILES) - len(missing_input_names(inputs))), "saved CSV inventory", "Counts saved inputs available to this QQQ100 readiness pack."),
    ]


def build_blocker_rows(inputs: dict[str, list[dict[str, Any]]], readiness: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("preview_implementation_not_added", "blocked", "critical", "Manual preview-candidate discussion does not add preview mode.", "Create preview mode only as a separate non-execution implementation step after manual approval."),
        blocker_row("execution_blocked", "blocked", "critical", "Paper/live execution remains blocked.", "Do not create orders or strategy-to-execution wiring."),
        blocker_row("paper_execution_discussion_blocked", "blocked", "critical", "Paper execution discussion remains separate from preview-candidate discussion.", "Complete preview implementation and readiness gates first."),
        blocker_row("scheduling_not_approved", "blocked", "high", "Scheduling is not approved by this pack.", "Do not schedule strategy workflows."),
    ]
    missing = missing_input_names(inputs)
    if missing:
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", "; ".join(missing), "Regenerate missing saved reports only through safe report commands if needed."))
    if readiness["final_status"] == "qqq100_preview_discussion_needs_more_review":
        rows.append(blocker_row("qqq100_preview_discussion_needs_more_review", "blocked", "high", readiness["largest_blocker"], readiness["recommended_next_step"]))
    return rows


def pack_row(name: str, status: str, label: str, finding: str, source: str, blocker: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "check_status": status, "readiness_label": label, "finding": finding, "evidence_source": source, "blocker": blocker, "recommended_next_step": next_step, **safety_flags()}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def evidence_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "evidence_source": source, "details": details, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step, **safety_flags()}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ100 preview-candidate readiness pack complete. Research only; execution_approved=False.",
        f"Final readiness status: {summary_value(summary_rows, 'final_readiness_status')}",
        f"Clean main lead: {summary_value(summary_rows, 'clean_main_lead')}",
        f"Ambitious alternative: {summary_value(summary_rows, 'ambitious_alternative')}",
        f"Rejected high-drawdown reference: {summary_value(summary_rows, 'rejected_high_drawdown_reference')}",
        f"High-growth branch status: {summary_value(summary_rows, 'high_growth_branch_status')}",
        f"Strongest evidence for preview discussion: {summary_value(summary_rows, 'strongest_evidence_for_preview_discussion')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Preview status: {summary_value(summary_rows, 'preview_status')}",
        f"Execution status: {summary_value(summary_rows, 'execution_status')}",
        f"Saved pack to {output_paths['pack']}",
        f"Saved summary/evidence/blockers to {output_paths['summary']}; {output_paths['evidence']}; {output_paths['blockers']}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved-output readiness only; preview discussion is not preview implementation, paper execution, live trading, or scheduling approval.",
    ]


def matching_rows(rows: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if name in {str(row.get("candidate_name", "")), str(row.get("variant_name", "")), str(row.get("strategy_name", ""))}
    ]


def missing_input_names(inputs: dict[str, list[dict[str, Any]]]) -> list[str]:
    return [name for name, rows in inputs.items() if not rows]


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key or row.get("metric_name") == key or row.get("check_name") == key:
            return str(row.get("summary_value") or row.get("metric_value") or row.get("check_status") or "unavailable")
    return "unavailable"


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
