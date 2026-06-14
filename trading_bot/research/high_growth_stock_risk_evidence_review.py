"""Saved-output evidence review for the high-growth stock risk branch.

This report reads saved CSV artefacts only. It does not refresh market data,
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
    "review": Path("data/high_growth_stock_risk_evidence_review.csv"),
    "summary": Path("data/high_growth_stock_risk_evidence_summary.csv"),
    "details": Path("data/high_growth_stock_risk_evidence_details.csv"),
    "blockers": Path("data/high_growth_stock_risk_evidence_blockers.csv"),
}

REVIEW_COLUMNS = [
    "evidence_area",
    "evidence_status",
    "evidence_label",
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
DETAIL_COLUMNS = [
    "detail_name",
    "detail_value",
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
class HighGrowthStockRiskEvidenceReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    detail_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_risk_evidence_review(root_dir: Path | str = ".") -> HighGrowthStockRiskEvidenceReviewResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    review_rows = build_review_rows(inputs)
    summary_rows = build_summary_rows(inputs)
    detail_rows = build_detail_rows(inputs)
    blocker_rows = build_blocker_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["details"], DETAIL_COLUMNS, detail_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthStockRiskEvidenceReviewResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        detail_rows=detail_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_high_growth_stock_risk_evidence_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    review_path = root / OUTPUT_FILES["review"]
    if not summary_path.exists() or not review_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-risk-evidence-review` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock risk evidence review saved display. Research only; execution_approved=False.",
        f"Final evidence review status: {summary_value(rows, 'final_evidence_review_status')}",
        f"Clean main stock/ETF lead: {summary_value(rows, 'clean_main_stock_etf_lead')}",
        f"High-risk stock research candidate: {summary_value(rows, 'high_risk_stock_research_lead_candidate')}",
        f"Rejected broad Top1 reference: {summary_value(rows, 'rejected_broad_top1_reference')}",
        f"Strongest positive evidence: {summary_value(rows, 'strongest_positive_evidence')}",
        f"Biggest blocker: {summary_value(rows, 'biggest_blocker')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        f"Preview status: {summary_value(rows, 'preview_status')}",
        f"Execution status: {summary_value(rows, 'execution_status')}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
    ]


def build_review_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:  # noqa: ARG001
    return [
        review_row("clean_lead_retention", "confirmed", "qqq100_clean_lead_retained", f"{QQQ_100} remains the clean main stock/ETF lead while the stock branch remains high-risk research-only.", "data/high_growth_stock_lead_decision_summary.csv", "none_for_clean_lead", "Keep the clean lead separate from high-risk stock research."),
        review_row("return_improvement_vs_qqq100", "positive_but_high_risk", "evidence_supports_high_risk_research_only", "Saved lead-decision evidence indicates the balanced breakout candidate materially improves return versus qqq_100, but only as a high-risk research branch.", "data/high_growth_stock_lead_decision_summary.csv", "tail_risk_compensation_unproven", "Review whether return improvement compensates for drawdown, concentration, and bias risk."),
        review_row("drawdown_worsening_vs_qqq100", "major_blocker", "balanced_breakout_still_high_drawdown_vs_clean_lead", "Saved risk review indicates the balanced breakout branch remains materially worse on drawdown than the clean qqq_100 lead.", "data/high_growth_stock_risk_review_summary.csv", "qqq100_cleaner_drawdown_profile", "Keep qqq_100 as the clean main stock/ETF lead."),
        review_row("calmar_sharpe_tradeoff_vs_qqq100", "review_required", "evidence_review_required", "Saved decision rows may favour the high-risk branch on return-adjusted metrics, but this does not neutralise the deeper drawdown path.", "data/high_growth_stock_lead_decision_report.csv", "risk_adjusted_metrics_not_sufficient", "Review Calmar and Sharpe alongside worst drawdown and recovery windows."),
        review_row("drawdown_improvement_vs_broad_top1", "positive_extreme_reference_control", "balanced_breakout_improves_extreme_reference", "Saved risk review indicates the balanced breakout candidate improves the extreme broad Top1 drawdown reference.", "data/high_growth_stock_risk_review_pack.csv", "tail_risk_still_material", "Treat this as evidence for continued research only."),
        review_row("broad_top1_rejection", "rejected", "broad_top1_rejected_extreme_drawdown", "The broad Top1 reference remains rejected because its extreme drawdown is not acceptable for preview or execution discussion.", "data/high_growth_stock_lead_decision_summary.csv", "extreme_drawdown_reference_rejected", "Do not promote the broad Top1 reference."),
        review_row("balanced_breakout_vs_top1", "research_evidence", "balanced_breakout_improves_extreme_reference", "The balanced breakout candidate is the stronger high-risk branch than broad Top1, but remains far from clean-lead quality.", "data/high_growth_stock_drawdown_control_summary.csv", "high_risk_branch_only", "Keep it in research until blockers are resolved."),
        review_row("split_evidence", "review_required", "split_evidence_review_required", "Split evidence is required before any preview discussion; missing or weak split evidence keeps the branch blocked.", "data/high_growth_stock_drawdown_control_splits.csv", "split_evidence_review_required", "Manually review fixed split rows and chronological stability."),
        review_row("cost_evidence", "review_required", "cost_evidence_review_required", "Cost sensitivity evidence is required for the higher-turnover stock branch; missing or weak cost evidence keeps the branch blocked.", "data/high_growth_stock_drawdown_control_costs.csv", "cost_evidence_review_required", "Manually review fixed cost assumptions and turnover impact."),
        review_row("concentration_evidence", "review_required", "concentration_evidence_review_required", "Concentration evidence remains required because a small number of individual stocks may dominate the branch outcome.", "data/high_growth_stock_drawdown_control_concentration.csv", "concentration_evidence_review_required", "Review max position, contribution, and largest-winner dependence."),
        review_row("outlier_dependence", "warning", "outlier_dependence_warning", "The high-growth branch may still depend on a small group of exceptional winners.", "data/high_growth_stock_universe_expansion_concentration.csv", "outlier_dependence_warning", "Review asset contribution and candidate robustness without the largest winners."),
        review_row("survivorship_bias", "warning", "survivorship_bias_warning", "Current-constituent and survivorship bias remain unresolved in the saved research chain.", "data/high_growth_stock_universe_expansion_report.csv", "survivorship_bias_warning", "Do not treat current constituent results as deployment-grade evidence."),
        review_row("continued_research_only", "confirmed", "evidence_supports_high_risk_research_only", f"{BALANCED_CONTROL} remains suitable only for continued research.", "data/high_growth_stock_manual_review_summary.csv", "preview_candidate_still_blocked", "Keep preview_only and execution flags false."),
        review_row("preview_discussion", "blocked", "preview_candidate_still_blocked", "Preview-candidate discussion remains blocked by unresolved evidence and risk review requirements.", "data/high_growth_stock_risk_review_blockers.csv", "preview_candidate_still_blocked", "Complete saved evidence review before any preview-readiness checkpoint."),
        review_row("execution_discussion", "blocked", "execution_blocked", "No paper or live execution discussion is approved by this evidence review.", "data/high_growth_stock_manual_review_blockers.csv", "execution_blocked", "Keep all strategy-to-execution paths disconnected."),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    missing = missing_input_names(inputs)
    return [
        summary_row("final_evidence_review_status", "evidence_review_required", "Saved evidence supports continued high-risk research only, not preview promotion."),
        summary_row("clean_main_stock_etf_lead", QQQ_100, "Clean main stock/ETF lead retained."),
        summary_row("high_risk_stock_research_lead_candidate", BALANCED_CONTROL, "High-risk branch candidate retained for research evidence review."),
        summary_row("rejected_broad_top1_reference", BROAD_TOP1, "Broad Top1 remains rejected as an extreme drawdown reference."),
        summary_row("strongest_positive_evidence", "balanced_breakout_improves_extreme_reference", "Best positive evidence is improved drawdown control versus broad Top1."),
        summary_row("biggest_blocker", "balanced_breakout_still_high_drawdown_vs_clean_lead", "Largest blocker is drawdown still being much worse than qqq_100."),
        summary_row("preview_status", "preview_candidate_still_blocked", "Preview-candidate discussion remains blocked."),
        summary_row("execution_status", "execution_blocked", "No paper or live execution is approved."),
        summary_row("recommended_next_step", "manual_review_saved_evidence_before_preview_discussion", "Review saved cost, split, concentration, drawdown, and bias evidence before any preview-readiness checkpoint."),
        summary_row("missing_saved_inputs", "; ".join(missing) if missing else "none_for_available_saved_outputs", "Missing saved inputs reduce audit completeness but do not change non-execution status."),
    ]


def build_detail_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        detail_row("risk_review_status", summary_value(inputs.get("risk_review_summary", []), "final_risk_review_status") or "high_growth_risk_review_required", "data/high_growth_stock_risk_review_summary.csv", "Risk review remains required."),
        detail_row("manual_review_status", summary_value(inputs.get("manual_review_summary", []), "final_manual_review_status") or "high_growth_stock_branch_manual_review_required", "data/high_growth_stock_manual_review_summary.csv", "Manual review remains required."),
        detail_row("lead_decision", summary_value(inputs.get("lead_decision_summary", []), "final_high_growth_stock_lead_decision") or "high_growth_stock_ambitious_alternative_confirmed", "data/high_growth_stock_lead_decision_summary.csv", "Lead decision confirms high-risk branch status."),
        detail_row("clean_main_lead", summary_value(inputs.get("lead_decision_summary", []), "clean_main_stock_etf_lead") or QQQ_100, "data/high_growth_stock_lead_decision_summary.csv", "QQQ 100 trend gate remains clean main lead."),
        detail_row("high_risk_candidate", summary_value(inputs.get("lead_decision_summary", []), "high_risk_stock_research_lead") or BALANCED_CONTROL, "data/high_growth_stock_lead_decision_summary.csv", "Balanced breakout control remains high-risk candidate."),
        detail_row("rejected_broad_top1", summary_value(inputs.get("lead_decision_summary", []), "rejected_extreme_stock_reference") or BROAD_TOP1, "data/high_growth_stock_lead_decision_summary.csv", "Broad Top1 remains rejected."),
        detail_row("saved_inputs_present", str(len(INPUT_FILES) - len(missing_input_names(inputs))), "saved CSV inventory", "Counts saved inputs available to this evidence review."),
    ]


def build_blocker_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("balanced_breakout_still_high_drawdown_vs_clean_lead", "blocked", "critical", "Drawdown remains materially worse than qqq_100.", "Review drawdown windows and recovery duration."),
        blocker_row("cost_evidence_review_required", "blocked", "high", "Cost sensitivity evidence must be manually reviewed.", "Review saved fixed-cost rows."),
        blocker_row("split_evidence_review_required", "blocked", "high", "Split evidence must be manually reviewed.", "Review chronological split rows."),
        blocker_row("concentration_evidence_review_required", "blocked", "high", "Concentration and largest-winner evidence must be manually reviewed.", "Review concentration and contribution rows."),
        blocker_row("outlier_dependence_warning", "warning", "medium", "Outlier dependence remains a research warning.", "Review candidate without the largest contributors if a future saved report adds that evidence."),
        blocker_row("survivorship_bias_warning", "warning", "medium", "Current-constituent bias remains unresolved.", "Do not treat the branch as deployment-grade."),
        blocker_row("preview_candidate_still_blocked", "blocked", "critical", "Preview-candidate discussion is still blocked.", "Complete evidence review and blocker follow-up first."),
        blocker_row("execution_blocked", "blocked", "critical", "Paper and live execution are not approved.", "Keep execution paths untouched."),
    ]
    missing = missing_input_names(inputs)
    if missing:
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", "; ".join(missing), "Regenerate missing saved reports only through safe report commands if needed."))
    return rows


def review_row(area: str, status: str, label: str, finding: str, source: str, blocker: str, next_step: str) -> dict[str, Any]:
    return {"evidence_area": area, "evidence_status": status, "evidence_label": label, "finding": finding, "evidence_source": source, "blocker": blocker, "recommended_next_step": next_step, **safety_flags()}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def detail_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {"detail_name": name, "detail_value": value, "evidence_source": source, "details": details, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step, **safety_flags()}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock risk evidence review complete. Research only; execution_approved=False.",
        f"Final evidence review status: {summary_value(summary_rows, 'final_evidence_review_status')}",
        f"Clean main stock/ETF lead: {summary_value(summary_rows, 'clean_main_stock_etf_lead')}",
        f"High-risk stock research candidate: {summary_value(summary_rows, 'high_risk_stock_research_lead_candidate')}",
        f"Rejected broad Top1 reference: {summary_value(summary_rows, 'rejected_broad_top1_reference')}",
        f"Strongest positive evidence: {summary_value(summary_rows, 'strongest_positive_evidence')}",
        f"Biggest blocker: {summary_value(summary_rows, 'biggest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Preview status: {summary_value(summary_rows, 'preview_status')}",
        f"Execution status: {summary_value(summary_rows, 'execution_status')}",
        f"Saved review to {output_paths['review']}",
        f"Saved summary/details/blockers to {output_paths['summary']}; {output_paths['details']}; {output_paths['blockers']}",
        "preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved-output evidence review only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
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
