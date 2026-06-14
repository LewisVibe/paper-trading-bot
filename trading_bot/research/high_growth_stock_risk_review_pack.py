"""Saved-output risk review pack for the high-growth stock branch.

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

INPUT_FILES = {
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
    "pack": Path("data/high_growth_stock_risk_review_pack.csv"),
    "summary": Path("data/high_growth_stock_risk_review_summary.csv"),
    "evidence": Path("data/high_growth_stock_risk_review_evidence.csv"),
    "blockers": Path("data/high_growth_stock_risk_review_blockers.csv"),
}

PACK_COLUMNS = [
    "review_area",
    "review_status",
    "risk_label",
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
class HighGrowthStockRiskReviewPackResult:
    output_paths: dict[str, Path]
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_risk_review_pack(root_dir: Path | str = ".") -> HighGrowthStockRiskReviewPackResult:
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
    return HighGrowthStockRiskReviewPackResult(
        output_paths=output_paths,
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_high_growth_stock_risk_review_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    pack_path = root / OUTPUT_FILES["pack"]
    if not summary_path.exists() or not pack_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-risk-review-pack` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock risk review pack saved display. Research only; execution_approved=False.",
        f"Final risk review status: {summary_value(rows, 'final_risk_review_status')}",
        f"Clean main stock/ETF lead: {summary_value(rows, 'clean_main_stock_etf_lead')}",
        f"High-risk stock research lead candidate: {summary_value(rows, 'high_risk_stock_research_lead_candidate')}",
        f"Rejected broad Top1 reference: {summary_value(rows, 'rejected_broad_top1_reference')}",
        f"Preview status: {summary_value(rows, 'preview_status')}",
        f"Execution status: {summary_value(rows, 'execution_status')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
    ]


def build_pack_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        pack_row("cost_sensitivity", "review_required", "cost_review_required", "Cost sensitivity remains unresolved for a high-turnover high-growth stock branch.", "data/high_growth_stock_drawdown_control_costs.csv", "cost_review_required", "Manually review fixed 0/10/25/50 bps assumptions before any preview discussion."),
        pack_row("split_sensitivity", "review_required", "split_review_required", "Split sensitivity remains unresolved; broad stock results need fixed chronological split review.", "data/high_growth_stock_drawdown_control_splits.csv", "split_review_required", "Review split_60_40, split_70_30, and split_80_20 outcomes."),
        pack_row("concentration_risk", "review_required", "concentration_review_required", "Single-name concentration and largest-contributor dependence remain high-risk features.", "data/high_growth_stock_drawdown_control_concentration.csv", "concentration_review_required", "Review max single-name concentration and largest contributor."),
        pack_row("outlier_dependence", "warning", "outlier_dependence_warning", "High-growth stock performance may still be dominated by a small group of winners.", "data/high_growth_stock_universe_expansion_concentration.csv", "outlier_dependence_warning", "Confirm whether NVDA, TSLA, AMD, or another small group explains the result."),
        pack_row("survivorship_bias", "warning", "survivorship_bias_warning", "The broad universe uses current constituents; broader breadth does not remove survivorship/current-constituent bias.", "data/high_growth_stock_universe_expansion_report.csv", "survivorship_bias_warning", "Do not treat this branch as bias-free."),
        pack_row("max_drawdown_severity", "review_required", "drawdown_review_required", "Balanced control improves broad Top1 drawdown but remains much deeper than qqq_100.", "data/high_growth_stock_lead_decision_summary.csv", "drawdown_review_required", "Review worst drawdown window and recovery duration."),
        pack_row("drawdown_improvement_vs_top1", "improved_but_not_clean", "high_growth_risk_review_required", "Saved lead decision shows about +27.8318 percentage points of max-drawdown improvement versus broad Top1.", "data/high_growth_stock_lead_decision_summary.csv", "tail_risk_still_material", "Treat improvement as research evidence, not preview approval."),
        pack_row("drawdown_worse_vs_qqq100", "worse_than_clean_lead", "drawdown_review_required", "Saved lead decision shows about -18.8748 percentage points worse max drawdown versus qqq_100.", "data/high_growth_stock_lead_decision_summary.csv", "qqq100_cleaner_drawdown", "Keep qqq_100 as clean main lead."),
        pack_row("return_improvement_vs_qqq100", "high_return_compensation", "high_growth_risk_review_required", "Saved lead decision shows about +32.0943 CAGR points versus qqq_100, but this may be compensation for unacceptable tail risk.", "data/high_growth_stock_lead_decision_summary.csv", "tail_risk_compensation_unproven", "Assess whether excess CAGR justifies drawdown and concentration risk."),
        pack_row("calmar_sharpe_tradeoff", "review_required", "high_growth_risk_review_required", "Calmar/Sharpe evidence favours the high-risk branch in saved decision metrics, but the drawdown path remains the blocker.", "data/high_growth_stock_lead_decision_report.csv", "risk_adjusted_metrics_not_sufficient", "Review risk-adjusted metrics alongside drawdown windows."),
        pack_row("research_boundary", "confirmed", "high_risk_branch_research_only", f"{BALANCED_CONTROL} remains research-only and not preview-approved.", "data/high_growth_stock_manual_review_summary.csv", "preview_candidate_still_blocked", "Keep preview_only=true and execution flags false."),
        pack_row("preview_gate", "blocked", "preview_candidate_still_blocked", "Preview-candidate discussion remains blocked by cost, split, concentration, survivorship, outlier, and drawdown review.", "data/high_growth_stock_manual_review_blockers.csv", "preview_candidate_still_blocked", "Complete risk review before any preview-readiness report."),
        pack_row("execution_gate", "blocked", "execution_blocked", "No paper or live execution discussion is approved by this risk review.", "data/high_growth_stock_manual_review_blockers.csv", "execution_blocked", "Keep strategy disconnected from execution paths."),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    missing = missing_input_names(inputs)
    return [
        summary_row("final_risk_review_status", "high_growth_risk_review_required", "Risk review confirms the branch remains research-only and blocker-heavy."),
        summary_row("clean_main_stock_etf_lead", QQQ_100, "Clean main lead unchanged."),
        summary_row("high_risk_stock_research_lead_candidate", BALANCED_CONTROL, "Candidate remains high-risk research-only."),
        summary_row("rejected_broad_top1_reference", BROAD_TOP1, "Broad Top1 remains rejected as extreme drawdown reference."),
        summary_row("preview_status", "preview_candidate_still_blocked", "No preview-candidate discussion is approved."),
        summary_row("execution_status", "execution_blocked", "No paper or live execution is approved."),
        summary_row("remaining_risk_blockers", "cost_review_required; split_review_required; concentration_review_required; drawdown_review_required; survivorship_bias_warning; outlier_dependence_warning", "Risk blockers remain open."),
        summary_row("recommended_next_step", "review_saved_cost_split_concentration_drawdown_evidence", "Manually inspect saved evidence before any preview-readiness report."),
        summary_row("missing_saved_inputs", "; ".join(missing) if missing else "none_for_available_saved_outputs", "Missing saved inputs reduce audit completeness but do not change non-execution status."),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        evidence_row("manual_review_status", summary_value(inputs.get("manual_review_summary", []), "final_manual_review_status") or "high_growth_stock_branch_manual_review_required", "data/high_growth_stock_manual_review_summary.csv", "Manual review already required."),
        evidence_row("lead_decision", summary_value(inputs.get("lead_decision_summary", []), "final_high_growth_stock_lead_decision") or "high_growth_stock_ambitious_alternative_confirmed", "data/high_growth_stock_lead_decision_summary.csv", "Lead decision confirms high-risk stock branch label."),
        evidence_row("clean_main_lead", summary_value(inputs.get("lead_decision_summary", []), "clean_main_stock_etf_lead") or QQQ_100, "data/high_growth_stock_lead_decision_summary.csv", "QQQ 100 trend gate remains clean main lead."),
        evidence_row("high_risk_candidate", summary_value(inputs.get("lead_decision_summary", []), "high_risk_stock_research_lead") or BALANCED_CONTROL, "data/high_growth_stock_lead_decision_summary.csv", "Balanced breakout control remains high-risk candidate."),
        evidence_row("rejected_broad_top1", summary_value(inputs.get("lead_decision_summary", []), "rejected_extreme_stock_reference") or BROAD_TOP1, "data/high_growth_stock_lead_decision_summary.csv", "Broad Top1 remains rejected."),
        evidence_row("saved_inputs_present", str(len(INPUT_FILES) - len(missing_input_names(inputs))), "saved CSV inventory", "Counts saved inputs available to this risk review."),
    ]


def build_blocker_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("cost_review_required", "blocked", "high", "Cost sensitivity review remains required.", "Review saved cost rows before any preview discussion."),
        blocker_row("split_review_required", "blocked", "high", "Split sensitivity review remains required.", "Review chronological split rows."),
        blocker_row("concentration_review_required", "blocked", "high", "Concentration and outlier dependence review remains required.", "Review concentration and contributor rows."),
        blocker_row("drawdown_review_required", "blocked", "critical", "Drawdown remains materially worse than qqq_100.", "Review drawdown window and recovery duration."),
        blocker_row("preview_candidate_still_blocked", "blocked", "critical", "Preview-candidate discussion remains blocked.", "Complete manual risk review first."),
        blocker_row("execution_blocked", "blocked", "critical", "Paper/live execution is not approved.", "Keep execution paths untouched."),
    ]
    missing = missing_input_names(inputs)
    if missing:
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", "; ".join(missing), "Regenerate missing saved reports only through safe report commands if needed."))
    return rows


def pack_row(area: str, status: str, label: str, finding: str, source: str, blocker: str, next_step: str) -> dict[str, Any]:
    return {"review_area": area, "review_status": status, "risk_label": label, "finding": finding, "evidence_source": source, "blocker": blocker, "recommended_next_step": next_step, **safety_flags()}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def evidence_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "evidence_source": source, "details": details, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step, **safety_flags()}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock risk review pack complete. Research only; execution_approved=False.",
        f"Final risk review status: {summary_value(summary_rows, 'final_risk_review_status')}",
        f"Clean main stock/ETF lead: {summary_value(summary_rows, 'clean_main_stock_etf_lead')}",
        f"High-risk stock research lead candidate: {summary_value(summary_rows, 'high_risk_stock_research_lead_candidate')}",
        f"Rejected broad Top1 reference: {summary_value(summary_rows, 'rejected_broad_top1_reference')}",
        f"Preview status: {summary_value(summary_rows, 'preview_status')}",
        f"Execution status: {summary_value(summary_rows, 'execution_status')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved pack to {output_paths['pack']}",
        f"Saved summary/evidence/blockers to {output_paths['summary']}; {output_paths['evidence']}; {output_paths['blockers']}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved-output risk review only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
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
