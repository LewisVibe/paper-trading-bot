"""Saved-output manual review pack for the high-growth stock branch.

This command reads saved report CSVs only. It does not refresh market data,
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
LEAD_DECISION_LABEL = "high_growth_stock_ambitious_alternative_confirmed"

INPUT_FILES = {
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
    "qqq_lead_decision_report": Path("data/qqq_lead_decision_report.csv"),
    "qqq_lead_decision_summary": Path("data/qqq_lead_decision_summary.csv"),
    "qqq_trend_gate_manual_review_pack": Path("data/qqq_trend_gate_manual_review_pack.csv"),
    "qqq_preview_candidate_readiness_report": Path("data/qqq_preview_candidate_readiness_report.csv"),
    "project_research_state_summary": Path("data/project_research_state_summary.csv"),
    "project_research_state_next_steps": Path("data/project_research_state_next_steps.csv"),
}

OUTPUT_FILES = {
    "pack": Path("data/high_growth_stock_manual_review_pack.csv"),
    "summary": Path("data/high_growth_stock_manual_review_summary.csv"),
    "evidence": Path("data/high_growth_stock_manual_review_evidence.csv"),
    "blockers": Path("data/high_growth_stock_manual_review_blockers.csv"),
}

PACK_COLUMNS = [
    "review_area",
    "review_status",
    "review_label",
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
class HighGrowthStockManualReviewPackResult:
    output_paths: dict[str, Path]
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_manual_review_pack(root_dir: Path | str = ".") -> HighGrowthStockManualReviewPackResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    pack_rows = build_pack_rows(inputs)
    summary_rows = build_summary_rows(inputs)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], PACK_COLUMNS, pack_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthStockManualReviewPackResult(
        output_paths=output_paths,
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_high_growth_stock_manual_review_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    pack_path = root / OUTPUT_FILES["pack"]
    if not summary_path.exists() or not pack_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-manual-review-pack` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock manual review pack saved display. Research only; execution_approved=False.",
        f"Final manual review status: {summary_value(rows, 'final_manual_review_status')}",
        f"Clean main stock/ETF lead: {summary_value(rows, 'clean_main_stock_etf_lead')}",
        f"High-risk stock research lead candidate: {summary_value(rows, 'high_risk_stock_research_lead_candidate')}",
        f"Rejected extreme reference: {summary_value(rows, 'rejected_extreme_reference')}",
        f"Preview status: {summary_value(rows, 'preview_status')}",
        f"Execution status: {summary_value(rows, 'execution_status')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
    ]


def build_pack_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        pack_row("branch_status", "manual_review_required", "high_growth_stock_branch_manual_review_required", "High-growth stock branch is credible enough for continued review, not preview promotion.", "data/high_growth_stock_lead_decision_summary.csv", "preview_candidate_not_approved", "Build a deeper manual review pack before any preview-candidate discussion."),
        pack_row("research_boundary", "confirmed", "high_growth_stock_branch_research_only_confirmed", "All current labels are research-only and non-execution.", "data/high_growth_stock_lead_decision_report.csv", "execution_blocked", "Keep execution_approved=false and paper_execution_approved=false."),
        pack_row("clean_main_lead", "unchanged", "clean_main_lead_unchanged", f"{QQQ_100} remains the clean main stock/ETF lead because drawdown and simplicity are much cleaner.", "data/qqq_lead_decision_summary.csv", "", "Keep QQQ lead separate from high-risk stock branch."),
        pack_row("high_risk_stock_lead", "candidate_confirmed", "high_risk_stock_lead_candidate_confirmed", f"{BALANCED_CONTROL} is the high-risk stock research lead candidate.", "data/high_growth_stock_lead_decision_report.csv", "high_growth_stock_not_preview_ready", "Review concentration, split/cost sensitivity, and drawdown windows."),
        pack_row("extreme_reference", "rejected", "extreme_drawdown_reference_rejected", f"{BROAD_TOP1} remains rejected because broad Top1 drawdown is around -70%.", "data/high_growth_stock_universe_expansion_summary.csv", "drawdown_too_extreme", "Use only as a cautionary reference."),
        pack_row("tradeoff", "high_return_high_drawdown", "high_growth_stock_branch_manual_review_required", "Balanced control keeps large excess return versus qqq_100 but still carries materially deeper drawdown.", "data/high_growth_stock_lead_decision_summary.csv", "drawdown_still_materially_deeper_than_qqq100", "Quantify drawdown periods and recovery behaviour before preview discussion."),
        pack_row("cost_sensitivity", "review_required", "high_growth_stock_branch_manual_review_required", "Cost sensitivity must remain an explicit blocker until manually reviewed.", "data/high_growth_stock_drawdown_control_costs.csv", "cost_review_required", "Review 10/25/50 bps assumptions."),
        pack_row("split_sensitivity", "review_required", "high_growth_stock_branch_manual_review_required", "Split sensitivity must remain an explicit blocker until manually reviewed.", "data/high_growth_stock_drawdown_control_splits.csv", "split_review_required", "Review fixed 60/40, 70/30, and 80/20 splits."),
        pack_row("concentration_risk", "high", "high_growth_stock_branch_manual_review_required", "Single-name concentration and stock-specific event/gap risk remain high.", "data/high_growth_stock_drawdown_control_concentration.csv", "concentration_review_required", "Review largest contributor and maximum single-name exposure."),
        pack_row("survivorship_bias", "high", "high_growth_stock_branch_manual_review_required", "Current-constituent survivorship bias remains unresolved.", "data/high_growth_stock_universe_expansion_report.csv", "survivorship_bias_unresolved", "Do not treat broad universe results as bias-free."),
        pack_row("preview_gate", "blocked", "preview_candidate_not_approved", "The high-growth stock branch is not preview-candidate approved.", "data/high_growth_stock_lead_decision_blockers.csv", "preview_candidate_not_approved", "Create separate preview-readiness report only after manual review."),
        pack_row("execution_gate", "blocked", "execution_blocked", "No paper or live execution discussion is approved by this pack.", "data/high_growth_stock_lead_decision_blockers.csv", "execution_blocked", "Keep strategy disconnected from orders."),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    missing = missing_input_names(inputs)
    return [
        summary_row("final_manual_review_status", "high_growth_stock_branch_manual_review_required", "High-growth branch is credible for continued research review only."),
        summary_row("clean_main_stock_etf_lead", QQQ_100, "Clean main lead unchanged."),
        summary_row("high_risk_stock_research_lead_candidate", BALANCED_CONTROL, "High-risk stock research lead candidate confirmed as research-only."),
        summary_row("rejected_extreme_reference", BROAD_TOP1, "Extreme Top1 reference remains rejected."),
        summary_row("preview_status", "preview_candidate_not_approved", "No preview promotion is approved."),
        summary_row("execution_status", "execution_blocked", "No paper or live execution is approved."),
        summary_row("remaining_blockers", "; ".join(missing) if missing else "manual_review_required_even_with_saved_inputs_present", "Missing saved inputs or unresolved risk reviews block preview discussion."),
        summary_row("recommended_next_step", "manual_review_cost_split_concentration_drawdown_pack", "Review cost, split, concentration, survivorship, outlier, and drawdown evidence before any preview-readiness report."),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        evidence_row("lead_decision_label", summary_value(inputs.get("lead_decision_summary", []), "final_high_growth_stock_lead_decision") or LEAD_DECISION_LABEL, "data/high_growth_stock_lead_decision_summary.csv", "Saved lead decision confirms ambitious high-growth alternative label."),
        evidence_row("clean_main_lead", summary_value(inputs.get("lead_decision_summary", []), "clean_main_stock_etf_lead") or QQQ_100, "data/high_growth_stock_lead_decision_summary.csv", "QQQ 100 trend gate remains clean main lead."),
        evidence_row("high_risk_stock_lead_candidate", summary_value(inputs.get("lead_decision_summary", []), "high_risk_stock_research_lead") or BALANCED_CONTROL, "data/high_growth_stock_lead_decision_summary.csv", "Balanced breakout control is the high-risk stock candidate."),
        evidence_row("rejected_extreme_reference", summary_value(inputs.get("lead_decision_summary", []), "rejected_extreme_stock_reference") or BROAD_TOP1, "data/high_growth_stock_lead_decision_summary.csv", "Broad Top1 remains rejected as extreme drawdown reference."),
        evidence_row("saved_inputs_present", str(len(INPUT_FILES) - len(missing_input_names(inputs))), "saved CSV inventory", "Counts saved inputs available to the manual review pack."),
    ]


def build_blocker_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("preview_candidate_not_approved", "blocked", "critical", "Manual review pack does not approve preview promotion.", "Create a separate preview-readiness report after manual review."),
        blocker_row("execution_blocked", "blocked", "critical", "Manual review pack does not approve paper or live execution.", "Keep execution and paper execution approvals false."),
        blocker_row("cost_split_concentration_review", "blocked", "high", "Cost, split, concentration, outlier, survivorship, current-constituent, and drawdown risks remain unresolved.", "Review saved evidence manually."),
    ]
    missing = missing_input_names(inputs)
    if missing:
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", "; ".join(missing), "Regenerate missing saved reports through safe report commands only if needed."))
    return rows


def pack_row(area: str, status: str, label: str, finding: str, source: str, blocker: str, next_step: str) -> dict[str, Any]:
    return {"review_area": area, "review_status": status, "review_label": label, "finding": finding, "evidence_source": source, "blocker": blocker, "recommended_next_step": next_step, **safety_flags()}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def evidence_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "evidence_source": source, "details": details, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step, **safety_flags()}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock manual review pack complete. Research only; execution_approved=False.",
        f"Final manual review status: {summary_value(summary_rows, 'final_manual_review_status')}",
        f"Clean main stock/ETF lead: {summary_value(summary_rows, 'clean_main_stock_etf_lead')}",
        f"High-risk stock research lead candidate: {summary_value(summary_rows, 'high_risk_stock_research_lead_candidate')}",
        f"Rejected extreme reference: {summary_value(summary_rows, 'rejected_extreme_reference')}",
        f"Preview status: {summary_value(summary_rows, 'preview_status')}",
        f"Execution status: {summary_value(summary_rows, 'execution_status')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved pack to {output_paths['pack']}",
        f"Saved summary/evidence/blockers to {output_paths['summary']}; {output_paths['evidence']}; {output_paths['blockers']}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved-output manual review only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
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
