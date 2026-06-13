"""Saved-output manual review pack for the QQQ trend-gate research lead.

This module reads saved research CSVs only. It does not refresh market data,
call yfinance or Alpaca, load config, read positions, create orders, write
SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QQQ_LEAD = "qqq_100_trend_gate"
QQQ_STATUS = "qqq_100_trend_gate_new_research_lead"
QQQ_LEAD_LABEL = "qqq_100_simpler_lower_drawdown_candidate"
QQQ_ADAPTIVE = "codex_qqq_adaptive_trend_exposure"
QQQ_ADAPTIVE_LABEL = "qqq_adaptive_higher_calmar_but_drawdown_tradeoff"
QQQ_HIGH_DRAWDOWN = "qqq_150_trend_gate"
QQQ_HIGH_DRAWDOWN_LABEL = "qqq_150_rejected_high_drawdown"
QQQ_HIGHER_REJECTS = ["qqq_175_trend_gate", "qqq_200_trend_gate"]
PREVIOUS_LEAD = "codex_ambitious_concentrated_growth_persistence"
PREVIOUS_LEAD_STATUS = "codex_ambitious_active_research_lead_cost_review_required"
FINAL_STATUS = "qqq_trend_gate_research_lead_confirmed_not_execution_ready"
NEXT_STEP = "review_qqq_trend_gate_as_new_stock_etf_research_lead"

INPUT_FILES = {
    "qqq_lead_decision_report": Path("data/qqq_lead_decision_report.csv"),
    "qqq_lead_decision_summary": Path("data/qqq_lead_decision_summary.csv"),
    "qqq_lead_decision_evidence": Path("data/qqq_lead_decision_evidence.csv"),
    "qqq_leverage_validation_report": Path("data/qqq_leverage_validation_report.csv"),
    "qqq_leverage_validation_summary": Path("data/qqq_leverage_validation_summary.csv"),
    "qqq_leverage_validation_costs": Path("data/qqq_leverage_validation_costs.csv"),
    "qqq_leverage_validation_splits": Path("data/qqq_leverage_validation_splits.csv"),
    "qqq_leverage_validation_drawdowns": Path("data/qqq_leverage_validation_drawdowns.csv"),
    "qqq_adaptive_leverage_lab": Path("data/qqq_adaptive_leverage_lab.csv"),
    "qqq_adaptive_leverage_lab_summary": Path("data/qqq_adaptive_leverage_lab_summary.csv"),
    "qqq_adaptive_leverage_lab_costs": Path("data/qqq_adaptive_leverage_lab_costs.csv"),
    "qqq_adaptive_leverage_lab_splits": Path("data/qqq_adaptive_leverage_lab_splits.csv"),
    "qqq_adaptive_leverage_lab_drawdowns": Path("data/qqq_adaptive_leverage_lab_drawdowns.csv"),
    "project_research_state_summary": Path("data/project_research_state_summary.csv"),
    "project_research_state_next_steps": Path("data/project_research_state_next_steps.csv"),
    "stock_etf_paper_execution_readiness_report": Path("data/stock_etf_paper_execution_readiness_report.csv"),
    "alpaca_paper_readiness_report": Path("data/alpaca_paper_readiness_report.csv"),
    "paper_order_smoke_test_readiness_pack": Path("data/paper_order_smoke_test_readiness_pack.csv"),
}

OUTPUT_FILES = {
    "pack": Path("data/qqq_trend_gate_manual_review_pack.csv"),
    "summary": Path("data/qqq_trend_gate_manual_review_summary.csv"),
    "evidence": Path("data/qqq_trend_gate_manual_review_evidence.csv"),
    "blockers": Path("data/qqq_trend_gate_manual_review_blockers.csv"),
}

COMMON_COLUMNS = [
    "created_at",
    "review_section",
    "check_name",
    "check_status",
    "severity",
    "candidate_name",
    "candidate_role",
    "metric_name",
    "metric_value",
    "evidence_source",
    "details",
    "blocker",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
    "manual_review_status",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]


@dataclass
class QqqTrendGateManualReviewPackResult:
    pack_path: Path
    summary_path: Path
    evidence_path: Path
    blockers_path: Path
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq_trend_gate_manual_review_pack(data_dir: Path | str = "data") -> QqqTrendGateManualReviewPackResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(data_path / path.name) for name, path in INPUT_FILES.items()}
    evidence_rows = build_evidence_rows(created_at, inputs)
    blocker_rows = build_blocker_rows(created_at, inputs)
    status = choose_final_status(inputs, blocker_rows)
    pack_rows = build_pack_rows(created_at, inputs, status, blocker_rows)
    summary_rows = build_summary_rows(created_at, inputs, status, blocker_rows)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], COMMON_COLUMNS, pack_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], COMMON_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], COMMON_COLUMNS, blocker_rows)
    return QqqTrendGateManualReviewPackResult(
        pack_path=output_paths["pack"],
        summary_path=output_paths["summary"],
        evidence_path=output_paths["evidence"],
        blockers_path=output_paths["blockers"],
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_qqq_trend_gate_manual_review_pack(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    pack = read_csv(data_path / OUTPUT_FILES["pack"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    evidence = read_csv(data_path / OUTPUT_FILES["evidence"].name)
    blockers = read_csv(data_path / OUTPUT_FILES["blockers"].name)
    if not pack or not summary:
        return 1, ["Run `python bot.py --qqq-trend-gate-manual-review-pack` first."]
    approvals = approval_values(pack + summary + evidence + blockers)
    lines = [
        "QQQ trend-gate manual review pack. Display only; execution_approved=False.",
        f"Final manual review status: {summary_value(summary, 'final_manual_review_status')}",
        f"Confirmed research lead: {summary_value(summary, 'confirmed_stock_etf_research_lead')}",
        f"Ambitious alternative: {summary_value(summary, 'ambitious_alternative')}",
        f"Rejected high-drawdown reference: {summary_value(summary, 'rejected_high_drawdown_reference')}",
        f"Previous lead displaced: {summary_value(summary, 'previous_lead_displaced')}",
        f"Main reason for lead change: {summary_value(summary, 'main_reason_for_lead_change')}",
        f"Remaining blockers: {summary_value(summary, 'remaining_blockers')}",
        f"Recommended next step: {summary_value(summary, 'recommended_next_step')}",
        f"execution_approved={approvals.get('execution_approved', 'false')}",
        f"leverage_execution_approved={approvals.get('leverage_execution_approved', 'false')}",
        f"margin_approved={approvals.get('margin_approved', 'false')}",
        f"scheduling_approved={approvals.get('scheduling_approved', 'false')}",
        "Warning: manual review pack does not approve preview promotion, paper execution, leverage, margin, scheduling, or strategy-to-execution wiring.",
    ]
    return 0, lines


def build_evidence_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        review_row(created_at, "lead_confirmation", "current_research_lead", "pass", "info", QQQ_LEAD, "confirmed_stock_etf_research_lead", "lead_status", QQQ_STATUS, "data/qqq_lead_decision_summary.csv", qqq_lead_details(inputs), "", NEXT_STEP, FINAL_STATUS),
        review_row(created_at, "why_displaced_previous_lead", "previous_lead_comparison", "pass", "info", PREVIOUS_LEAD, "previous_stock_etf_research_lead", "comparison", previous_lead_comparison(inputs), "data/qqq_lead_decision_report.csv", "QQQ 100 trend gate improves Sharpe, Calmar, and max drawdown versus the previous Codex ambitious lead while using a simpler rule.", "", NEXT_STEP, FINAL_STATUS),
        review_row(created_at, "conservative_vs_ambitious_qqq_choice", "conservative_main_lead", "pass", "info", QQQ_LEAD, "clean_main_research_lead", "lead_decision_label", QQQ_LEAD_LABEL, "data/qqq_lead_decision_summary.csv", "The unlevered QQQ trend gate is the cleaner lead because it keeps better Sharpe and lower drawdown than the adaptive alternative.", "", NEXT_STEP, FINAL_STATUS),
        review_row(created_at, "conservative_vs_ambitious_qqq_choice", "adaptive_alternative", "manual_review_required", "warning", QQQ_ADAPTIVE, "ambitious_alternative", "lead_decision_label", QQQ_ADAPTIVE_LABEL, "data/qqq_lead_decision_summary.csv", adaptive_details(inputs), "Adaptive QQQ remains an ambitious alternative, not the main lead.", NEXT_STEP, FINAL_STATUS),
        review_row(created_at, "rejected_high_drawdown_references", "qqq_150_rejection", "blocked_for_manual_review", "warning", QQQ_HIGH_DRAWDOWN, "rejected_high_drawdown_reference", "lead_decision_label", QQQ_HIGH_DRAWDOWN_LABEL, "data/qqq_lead_decision_summary.csv", high_drawdown_details(inputs), "Higher CAGR alone is not enough when drawdown and risk-adjusted metrics deteriorate.", "Keep high-drawdown references rejected unless a later risk review changes that.", FINAL_STATUS),
        review_row(created_at, "cost_financing_split_review", "cost_financing_sensitivity", cost_check_status(inputs), "warning", QQQ_LEAD, "confirmed_stock_etf_research_lead", "cost_financing_summary", cost_financing_summary(inputs), "data/qqq_leverage_validation_costs.csv", "Saved placeholder cost/financing rows are review evidence only and do not approve leverage, margin, or execution.", cost_blocker(inputs), "Complete manual cost/financing review before any future preview discussion.", FINAL_STATUS),
        review_row(created_at, "cost_financing_split_review", "split_sensitivity", split_check_status(inputs), "warning", QQQ_LEAD, "confirmed_stock_etf_research_lead", "split_sensitivity_summary", split_summary(inputs), "data/qqq_leverage_validation_splits.csv", "Absence of split warnings is supportive research context only, not execution approval.", split_blocker(inputs), "Review saved split evidence before any future preview discussion.", FINAL_STATUS),
        review_row(created_at, "drawdown_recovery_review", "drawdown_tradeoff", drawdown_check_status(inputs), "warning", QQQ_LEAD, "confirmed_stock_etf_research_lead", "drawdown_summary", drawdown_summary(inputs), "data/qqq_leverage_validation_drawdowns.csv", "Drawdown context confirms QQQ 100 is cleaner than adaptive or 150 reference, but recovery evidence still needs review when unavailable.", drawdown_blocker(inputs), "Review drawdown and recovery windows before any future preview discussion.", FINAL_STATUS),
        review_row(created_at, "preview_execution_blockers", "preview_execution_boundary", "blocked", "blocker", QQQ_LEAD, "research_only_lead", "approval_boundary", "preview=false; execution=false; leverage=false; margin=false; scheduling=false", "manual_review_pack", "Monday paper smoke test remains a connectivity/order-path test only, not QQQ strategy execution.", "No preview, paper execution, leverage, margin, or scheduling approval.", NEXT_STEP, FINAL_STATUS),
        review_row(created_at, "final_manual_review_status", "final_status", "blocked", "blocker", QQQ_LEAD, "confirmed_stock_etf_research_lead", "final_manual_review_status", FINAL_STATUS, "manual_review_pack", "QQQ trend gate is confirmed as the stock/ETF research lead but is not execution-ready.", "Execution and preview discussion remain blocked.", NEXT_STEP, FINAL_STATUS),
    ]
    for name in QQQ_HIGHER_REJECTS:
        detail = candidate_metric_details(find_candidate(inputs, name)) or "high-drawdown reference if present in saved outputs"
        rows.append(review_row(created_at, "rejected_high_drawdown_references", f"{name}_rejection", "blocked_for_manual_review", "warning", name, "rejected_high_drawdown_reference", "high_drawdown_reference", detail, "data/qqq_leverage_validation_report.csv", "Higher synthetic exposure remains a rejected over-levered/high-drawdown reference where saved outputs include it.", "Do not treat higher CAGR alone as a lead-change reason.", "Keep high-drawdown references rejected.", FINAL_STATUS))
    for name, rows_for_input in inputs.items():
        rows.append(review_row(created_at, "saved_input_status", name, "input_available" if rows_for_input else "missing_saved_input", "info" if rows_for_input else "warning", name, "saved_input", "row_count", str(len(rows_for_input)), str(INPUT_FILES[name]), f"Saved input {INPUT_FILES[name]} {'was found' if rows_for_input else 'was missing or empty'}.", "" if rows_for_input else "Missing saved input may require future review.", "Regenerate missing saved report only if the review needs it.", FINAL_STATUS))
    return rows


def build_blocker_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    blockers = [
        ("preview_not_approved", "No preview promotion is approved."),
        ("paper_execution_not_approved", "No paper execution is approved."),
        ("leverage_margin_not_approved", "No leverage or margin is approved."),
        ("scheduling_not_approved", "No scheduling is approved."),
        ("paper_smoke_test_boundary", "Monday paper smoke test remains connectivity/order-path only, not QQQ strategy execution."),
    ]
    if cost_blocker(inputs):
        blockers.append(("cost_financing_review_required", cost_blocker(inputs)))
    if split_blocker(inputs):
        blockers.append(("split_review_required", split_blocker(inputs)))
    if drawdown_blocker(inputs):
        blockers.append(("drawdown_recovery_review_required", drawdown_blocker(inputs)))
    missing_core = [
        name
        for name in ["qqq_lead_decision_summary", "qqq_lead_decision_report", "qqq_leverage_validation_report", "qqq_adaptive_leverage_lab"]
        if not inputs.get(name)
    ]
    if missing_core:
        blockers.append(("missing_core_saved_inputs", f"Missing core saved inputs: {', '.join(missing_core)}"))
    return [
        review_row(created_at, "preview_execution_blockers", name, "blocked", "blocker", QQQ_LEAD, "research_only_lead", "blocker", detail, "manual_review_pack", detail, detail, NEXT_STEP, FINAL_STATUS)
        for name, detail in blockers
    ]


def choose_final_status(inputs: dict[str, list[dict[str, Any]]], blocker_rows: list[dict[str, Any]]) -> str:
    if not inputs.get("qqq_lead_decision_summary"):
        return "qqq_trend_gate_blocked_missing_inputs"
    return FINAL_STATUS


def build_pack_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    status: str,
    blocker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        review_row(created_at, "manual_review_pack", "final_manual_review_status", "blocked", "blocker", QQQ_LEAD, "confirmed_stock_etf_research_lead", "manual_review_status", status, "manual_review_pack", "Final manual review status is research-only and not execution approval.", "No execution, preview, leverage, margin, or scheduling approval.", NEXT_STEP, status),
        review_row(created_at, "manual_review_pack", "confirmed_stock_etf_research_lead", "pass", "info", QQQ_LEAD, "confirmed_stock_etf_research_lead", "lead_name", QQQ_LEAD, "data/qqq_lead_decision_summary.csv", qqq_lead_details(inputs), "", NEXT_STEP, status),
        review_row(created_at, "manual_review_pack", "ambitious_alternative", "manual_review_required", "warning", QQQ_ADAPTIVE, "ambitious_alternative", "candidate_name", QQQ_ADAPTIVE, "data/qqq_lead_decision_summary.csv", adaptive_details(inputs), "Ambitious alternative is not the main lead.", NEXT_STEP, status),
        review_row(created_at, "manual_review_pack", "rejected_high_drawdown_reference", "blocked_for_manual_review", "warning", QQQ_HIGH_DRAWDOWN, "rejected_high_drawdown_reference", "candidate_name", QQQ_HIGH_DRAWDOWN, "data/qqq_lead_decision_summary.csv", high_drawdown_details(inputs), "High-drawdown reference remains rejected.", "Keep rejected references out of lead status.", status),
        review_row(created_at, "manual_review_pack", "blocker_count", "blocked", "blocker", QQQ_LEAD, "research_only_lead", "blocker_count", str(len(blocker_rows)), "manual_review_pack", "Blockers are explicit and do not remove research-lead status.", "Manual review required before preview/execution discussion.", NEXT_STEP, status),
    ]


def build_summary_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    status: str,
    blocker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries = [
        ("final_manual_review_status", status, "Research lead confirmed but execution is not ready."),
        ("confirmed_stock_etf_research_lead", QQQ_LEAD, qqq_lead_details(inputs)),
        ("ambitious_alternative", QQQ_ADAPTIVE, adaptive_details(inputs)),
        ("rejected_high_drawdown_reference", QQQ_HIGH_DRAWDOWN, high_drawdown_details(inputs)),
        ("previous_lead_displaced", PREVIOUS_LEAD, previous_lead_comparison(inputs)),
        ("main_reason_for_lead_change", main_reason_for_lead_change(inputs), "QQQ 100 trend gate improves risk-adjusted metrics versus the previous lead while staying simpler."),
        ("remaining_blockers", blocker_summary(blocker_rows), "Manual blockers remain explicit."),
        ("recommended_next_step", NEXT_STEP, "Review QQQ trend gate as the stock/ETF research lead without preview or execution approval."),
        ("execution_approved", "false", "Execution remains false for every row."),
        ("leverage_execution_approved", "false", "Leverage execution remains false for every row."),
        ("margin_approved", "false", "Margin approval remains false for every row."),
        ("scheduling_approved", "false", "Scheduling approval remains false for every row."),
    ]
    return [summary_row(created_at, name, value, details) for name, value, details in entries]


def qqq_lead_details(inputs: dict[str, list[dict[str, Any]]]) -> str:
    row = find_candidate(inputs, QQQ_LEAD)
    saved = summary_details(inputs["qqq_lead_decision_summary"], "conservative_qqq_candidate")
    return saved or candidate_metric_details(row) or "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718; label=qqq_100_simpler_lower_drawdown_candidate"


def adaptive_details(inputs: dict[str, list[dict[str, Any]]]) -> str:
    row = find_candidate(inputs, QQQ_ADAPTIVE)
    saved = summary_details(inputs["qqq_lead_decision_summary"], "ambitious_qqq_candidate")
    return saved or candidate_metric_details(row) or "CAGR=20.2819; Sharpe=0.9749; MaxDD=-25.9889; Calmar=0.7804; label=qqq_adaptive_higher_calmar_but_drawdown_tradeoff"


def high_drawdown_details(inputs: dict[str, list[dict[str, Any]]]) -> str:
    row = find_candidate(inputs, QQQ_HIGH_DRAWDOWN)
    saved = summary_details(inputs["qqq_lead_decision_summary"], "rejected_high_drawdown_reference")
    return saved or candidate_metric_details(row) or "CAGR=23.3903; Sharpe=0.9542; MaxDD=-33.892; Calmar=0.6901; label=qqq_150_rejected_high_drawdown"


def previous_lead_comparison(inputs: dict[str, list[dict[str, Any]]]) -> str:
    previous = find_candidate(inputs, PREVIOUS_LEAD)
    details = candidate_metric_details(previous)
    if details:
        return f"{details}; status={previous.get('candidate_status', PREVIOUS_LEAD_STATUS)}"
    return "CAGR=14.1039; Sharpe=0.7192; MaxDD=-29.5357; Calmar=0.4775; status=codex_ambitious_active_research_lead_cost_review_required; blocker=survived 10 bps costs but not 25 bps"


def main_reason_for_lead_change(inputs: dict[str, list[dict[str, Any]]]) -> str:
    tradeoff = summary_value(inputs["qqq_lead_decision_summary"], "main_tradeoff")
    if tradeoff != "unavailable":
        return tradeoff
    return "QQQ 100 trend gate has better Sharpe, Calmar, and max drawdown than the previous Codex ambitious lead, with a simpler SMA200 trend-gate rule."


def cost_financing_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    rows = matching_rows(inputs["qqq_leverage_validation_costs"] + inputs["qqq_adaptive_leverage_lab_costs"], QQQ_LEAD)
    if not rows:
        return "manual_review_required: saved cost/financing rows missing for qqq_100_trend_gate"
    labels = sorted({str(row.get("cost_sensitivity_label") or row.get("financing_sensitivity_label") or row.get("status") or "saved_cost_context") for row in rows})
    return f"saved_rows={len(rows)}; labels={', '.join(labels)}"


def split_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    rows = matching_rows(inputs["qqq_leverage_validation_splits"] + inputs["qqq_adaptive_leverage_lab_splits"], QQQ_LEAD)
    if not rows:
        return "manual_review_required: saved split rows missing for qqq_100_trend_gate"
    labels = sorted({str(row.get("split_sensitivity_label") or row.get("status") or "saved_split_context") for row in rows})
    if not any("sensitive" in label.lower() for label in labels):
        return f"saved_rows={len(rows)}; no split sensitivity warning in saved labels; labels={', '.join(labels)}"
    return f"saved_rows={len(rows)}; labels={', '.join(labels)}"


def drawdown_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    rows = matching_rows(inputs["qqq_leverage_validation_drawdowns"] + inputs["qqq_adaptive_leverage_lab_drawdowns"], QQQ_LEAD)
    base = f"qqq_100 MaxDD=-23.4576; adaptive MaxDD=-25.9889; qqq_150 MaxDD=-33.892"
    if not rows:
        return f"{base}; future_review_needed: saved recovery rows missing"
    labels = sorted({str(row.get("drawdown_label") or row.get("status") or row.get("period_name") or "saved_drawdown_context") for row in rows})
    recovery_fields = [row for row in rows if any("recover" in key.lower() for key in row)]
    recovery_status = "recovery_rows_available" if recovery_fields else "future_review_needed: recovery fields absent"
    return f"{base}; saved_rows={len(rows)}; {recovery_status}; labels={', '.join(labels)}"


def cost_check_status(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "manual_review_required" if cost_blocker(inputs) else "saved_context_available"


def split_check_status(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "manual_review_required" if split_blocker(inputs) else "saved_context_available"


def drawdown_check_status(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "future_review_needed" if drawdown_blocker(inputs) else "saved_context_available"


def cost_blocker(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "manual_review_required: saved cost/financing rows missing" if "missing" in cost_financing_summary(inputs) else ""


def split_blocker(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "manual_review_required: saved split rows missing" if "missing" in split_summary(inputs) else ""


def drawdown_blocker(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "future_review_needed: saved drawdown recovery rows missing or incomplete" if "future_review_needed" in drawdown_summary(inputs) else ""


def find_candidate(inputs: dict[str, list[dict[str, Any]]], name: str) -> dict[str, Any]:
    rows = (
        inputs["qqq_lead_decision_report"]
        + inputs["qqq_leverage_validation_report"]
        + inputs["qqq_adaptive_leverage_lab"]
        + inputs["qqq_lead_decision_evidence"]
    )
    for row in rows:
        if name in {str(row.get("candidate_name", "")), str(row.get("variant_name", "")), str(row.get("strategy_name", ""))}:
            return row
    return {}


def matching_rows(rows: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if name in {str(row.get("candidate_name", "")), str(row.get("variant_name", "")), str(row.get("strategy_name", ""))}
    ]


def candidate_metric_details(row: dict[str, Any]) -> str:
    if not row:
        return ""
    cagr = first_value(row, ["cagr", "cagr_pct"])
    sharpe = first_value(row, ["sharpe", "sharpe_ratio"])
    maxdd = first_value(row, ["max_drawdown", "max_drawdown_pct"])
    calmar = first_value(row, ["calmar", "calmar_ratio"])
    label = first_value(row, ["lead_decision_label", "candidate_status", "summary_label"])
    return f"CAGR={cagr}; Sharpe={sharpe}; MaxDD={maxdd}; Calmar={calmar}; label={label}"


def first_value(row: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return "unavailable"


def summary_details(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            details = str(row.get("details", ""))
            value = str(row.get("summary_value", ""))
            return details if details and details != "unavailable" else value
    return ""


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key or row.get("metric_name") == key or row.get("check_name") == key:
            return str(row.get("summary_value") or row.get("metric_value") or "unavailable")
    return "unavailable"


def blocker_summary(rows: list[dict[str, Any]]) -> str:
    names = [str(row.get("check_name", "")) for row in rows if row.get("severity") == "blocker"]
    return ", ".join(names) or "manual_review_required"


def approval_values(rows: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in ["execution_approved", "leverage_execution_approved", "margin_approved", "scheduling_approved"]:
        values = {str(row.get(field, "false")).lower() for row in rows}
        result[field] = "false" if values <= {"false", ""} else ",".join(sorted(values))
    return result


def review_row(
    created_at: str,
    section: str,
    check_name: str,
    status: str,
    severity: str,
    candidate_name: str,
    candidate_role: str,
    metric_name: str,
    metric_value: Any,
    evidence_source: str,
    details: str,
    blocker: str,
    recommended_next_step: str,
    manual_review_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "review_section": section,
        "check_name": check_name,
        "check_status": status,
        "severity": severity,
        "candidate_name": candidate_name,
        "candidate_role": candidate_role,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "evidence_source": evidence_source,
        "details": details,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        "manual_review_status": manual_review_status,
        **safety_flags(),
    }


def summary_row(created_at: str, name: str, value: str, details: str) -> dict[str, Any]:
    return {"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": False,
        "execution_approved": False,
        "leverage_execution_approved": False,
        "margin_approved": False,
        "short_execution_approved": False,
        "scheduling_approved": False,
        "alpaca_called": False,
        "orders_created": False,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ trend-gate manual review pack complete. Research/report only; execution_approved=False.",
        f"Final manual review status: {summary_value(summary_rows, 'final_manual_review_status')}",
        f"Confirmed research lead: {summary_value(summary_rows, 'confirmed_stock_etf_research_lead')}",
        f"Ambitious alternative: {summary_value(summary_rows, 'ambitious_alternative')}",
        f"Rejected high-drawdown reference: {summary_value(summary_rows, 'rejected_high_drawdown_reference')}",
        f"Previous lead displaced: {summary_value(summary_rows, 'previous_lead_displaced')}",
        f"Main reason for lead change: {summary_value(summary_rows, 'main_reason_for_lead_change')}",
        f"Remaining blockers: {summary_value(summary_rows, 'remaining_blockers')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        "execution_approved=false",
        "leverage_execution_approved=false",
        "margin_approved=false",
        "scheduling_approved=false",
        f"Saved pack to {paths['pack']}",
        f"Saved summary to {paths['summary']}",
        f"Saved evidence to {paths['evidence']}",
        f"Saved blockers to {paths['blockers']}",
        "Warning: manual review pack does not approve preview promotion, paper execution, leverage, margin, scheduling, or strategy-to-execution wiring.",
    ]


def read_csv(path: Path) -> list[dict[str, Any]]:
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
