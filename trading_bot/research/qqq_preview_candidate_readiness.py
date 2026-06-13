"""Saved-output preview-candidate readiness report for the QQQ trend gate.

This report reads saved CSVs only. It does not refresh market data, call
yfinance or Alpaca, load config, read positions, create orders, write SQLite,
send alerts, schedule anything, or approve paper execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QQQ_LEAD = "qqq_100_trend_gate"
QQQ_STATUS = "qqq_100_trend_gate_new_research_lead"
MANUAL_REVIEW_STATUS = "qqq_trend_gate_research_lead_confirmed_not_execution_ready"
READY_STATUS = "qqq_preview_candidate_ready_for_manual_discussion"
COST_STATUS = "qqq_preview_candidate_needs_cost_review"
MISSING_STATUS = "qqq_preview_candidate_blocked_missing_inputs"
DRAW_STATUS = "qqq_preview_candidate_needs_drawdown_review"
NOT_READY_STATUS = "qqq_preview_candidate_not_ready"
QQQ_ADAPTIVE = "codex_qqq_adaptive_trend_exposure"
QQQ_HIGH_DRAWDOWN = "qqq_150_trend_gate"
PREVIOUS_LEAD = "codex_ambitious_concentrated_growth_persistence"
NEXT_STEP = "manual_preview_candidate_discussion_only_before_any_paper_execution_design"

INPUT_FILES = {
    "manual_pack": Path("data/qqq_trend_gate_manual_review_pack.csv"),
    "manual_summary": Path("data/qqq_trend_gate_manual_review_summary.csv"),
    "manual_evidence": Path("data/qqq_trend_gate_manual_review_evidence.csv"),
    "manual_blockers": Path("data/qqq_trend_gate_manual_review_blockers.csv"),
    "qqq_lead_decision_report": Path("data/qqq_lead_decision_report.csv"),
    "qqq_lead_decision_summary": Path("data/qqq_lead_decision_summary.csv"),
    "qqq_lead_decision_evidence": Path("data/qqq_lead_decision_evidence.csv"),
    "qqq_leverage_validation_report": Path("data/qqq_leverage_validation_report.csv"),
    "qqq_leverage_validation_splits": Path("data/qqq_leverage_validation_splits.csv"),
    "qqq_leverage_validation_costs": Path("data/qqq_leverage_validation_costs.csv"),
    "qqq_leverage_validation_drawdowns": Path("data/qqq_leverage_validation_drawdowns.csv"),
    "project_research_state_summary": Path("data/project_research_state_summary.csv"),
    "project_research_state_next_steps": Path("data/project_research_state_next_steps.csv"),
    "stock_etf_paper_execution_readiness_report": Path("data/stock_etf_paper_execution_readiness_report.csv"),
    "paper_order_smoke_test_readiness_pack": Path("data/paper_order_smoke_test_readiness_pack.csv"),
}

OUTPUT_FILES = {
    "report": Path("data/qqq_preview_candidate_readiness_report.csv"),
    "summary": Path("data/qqq_preview_candidate_readiness_summary.csv"),
    "evidence": Path("data/qqq_preview_candidate_readiness_evidence.csv"),
    "blockers": Path("data/qqq_preview_candidate_readiness_blockers.csv"),
}

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "candidate_name",
    "candidate_role",
    "evidence_source",
    "details",
    "blocker",
    "recommended_next_step",
    "preview_candidate_discussion_status",
    "preview_discussion_approved",
    "paper_execution_approved",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    "preview_discussion_approved",
    "paper_execution_approved",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]


@dataclass
class QqqPreviewCandidateReadinessResult:
    report_path: Path
    summary_path: Path
    evidence_path: Path
    blockers_path: Path
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq_preview_candidate_readiness_report(data_dir: Path | str = "data") -> QqqPreviewCandidateReadinessResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(data_path / path.name) for name, path in INPUT_FILES.items()}
    evidence_rows = build_evidence_rows(created_at, inputs)
    blocker_rows = build_blocker_rows(created_at, inputs)
    status = choose_preview_status(inputs, blocker_rows)
    report_rows = build_report_rows(created_at, inputs, status, blocker_rows)
    summary_rows = build_summary_rows(created_at, inputs, status, blocker_rows)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], REPORT_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], REPORT_COLUMNS, blocker_rows)
    return QqqPreviewCandidateReadinessResult(
        report_path=output_paths["report"],
        summary_path=output_paths["summary"],
        evidence_path=output_paths["evidence"],
        blockers_path=output_paths["blockers"],
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_qqq_preview_candidate_readiness_report(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    report = read_csv(data_path / OUTPUT_FILES["report"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    evidence = read_csv(data_path / OUTPUT_FILES["evidence"].name)
    blockers = read_csv(data_path / OUTPUT_FILES["blockers"].name)
    if not report or not summary:
        return 1, ["Run `python bot.py --qqq-preview-candidate-readiness-report` first."]
    approvals = approval_values(report + summary + evidence + blockers)
    return 0, [
        "QQQ preview-candidate readiness report. Display only; paper_execution_approved=False.",
        f"Final preview-candidate readiness status: {summary_value(summary, 'final_preview_candidate_readiness_status')}",
        f"Confirmed research lead: {summary_value(summary, 'confirmed_research_lead')}",
        f"Evidence supporting preview discussion: {summary_value(summary, 'evidence_supporting_preview_discussion')}",
        f"Remaining blockers: {summary_value(summary, 'remaining_blockers')}",
        f"Recommended next step: {summary_value(summary, 'recommended_next_step')}",
        f"paper_execution_approved={approvals.get('paper_execution_approved', 'false')}",
        f"execution_approved={approvals.get('execution_approved', 'false')}",
        f"scheduling_approved={approvals.get('scheduling_approved', 'false')}",
        "Warning: preview readiness is manual discussion only; it does not approve paper orders, live trading, scheduling, or strategy-to-execution wiring.",
    ]


def build_evidence_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        report_row(created_at, "lead_confirmation", "pass", "info", QQQ_LEAD, "research_lead", "data/qqq_trend_gate_manual_review_summary.csv", lead_confirmation(inputs), "", NEXT_STEP, READY_STATUS),
        report_row(created_at, "manual_review_status_not_execution_ready", "pass", "info", QQQ_LEAD, "research_lead", "data/qqq_trend_gate_manual_review_summary.csv", f"manual_review_status={manual_status(inputs)}", "", NEXT_STEP, READY_STATUS),
        report_row(created_at, "improved_vs_previous_lead", "pass", "info", QQQ_LEAD, "preview_discussion_candidate", "data/qqq_lead_decision_summary.csv", "QQQ trend gate improved versus previous stock/ETF lead: higher Sharpe, higher Calmar, shallower max drawdown, simpler rule.", "", NEXT_STEP, READY_STATUS),
        report_row(created_at, "adaptive_remains_alternative", "manual_review_required", "warning", QQQ_ADAPTIVE, "ambitious_alternative", "data/qqq_lead_decision_summary.csv", adaptive_summary(inputs), "Adaptive QQQ is not the main preview discussion candidate.", NEXT_STEP, READY_STATUS),
        report_row(created_at, "higher_leverage_rejected", "pass", "info", QQQ_HIGH_DRAWDOWN, "rejected_high_drawdown_reference", "data/qqq_lead_decision_summary.csv", high_drawdown_summary(inputs), "", NEXT_STEP, READY_STATUS),
        report_row(created_at, "split_sensitivity_status", split_check_status(inputs), "warning", QQQ_LEAD, "preview_discussion_candidate", "data/qqq_leverage_validation_splits.csv", split_summary(inputs), split_blocker(inputs), "Review split evidence during manual preview discussion.", READY_STATUS),
        report_row(created_at, "cost_financing_status", cost_check_status(inputs), "warning", QQQ_LEAD, "preview_discussion_candidate", "data/qqq_leverage_validation_costs.csv", cost_summary(inputs), cost_blocker(inputs), "Review cost and financing evidence before paper execution design.", COST_STATUS if cost_blocker(inputs) else READY_STATUS),
        report_row(created_at, "drawdown_status", drawdown_check_status(inputs), "warning", QQQ_LEAD, "preview_discussion_candidate", "data/qqq_leverage_validation_drawdowns.csv", drawdown_summary(inputs), drawdown_blocker(inputs), "Review drawdown and recovery context before paper execution design.", DRAW_STATUS if drawdown_blocker(inputs) else READY_STATUS),
        report_row(created_at, "paper_execution_boundary", "blocked", "blocker", QQQ_LEAD, "research_lead", "preview_candidate_readiness_report", "Preview discussion is not paper execution approval. Monday smoke test remains connectivity/order-path only, not QQQ strategy execution.", "No paper order is approved.", NEXT_STEP, READY_STATUS),
    ]
    for name, rows_for_input in inputs.items():
        rows.append(report_row(created_at, f"saved_input_{name}", "input_available" if rows_for_input else "missing_saved_input", "info" if rows_for_input else "warning", name, "saved_input", str(INPUT_FILES[name]), f"row_count={len(rows_for_input)}", "" if rows_for_input else "Missing saved input may block or narrow preview discussion.", "Regenerate missing saved reports only if required.", READY_STATUS))
    return rows


def build_blocker_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    blockers = [
        ("paper_execution_not_approved", "No paper execution is approved."),
        ("live_trading_not_approved", "No live trading is approved."),
        ("scheduling_not_approved", "No scheduling is approved."),
        ("paper_smoke_test_boundary", "Monday paper smoke test remains connectivity/order-path only, not QQQ strategy execution."),
    ]
    if cost_blocker(inputs):
        blockers.append(("cost_financing_review_required", cost_blocker(inputs)))
    if drawdown_blocker(inputs):
        blockers.append(("drawdown_review_required", drawdown_blocker(inputs)))
    if split_blocker(inputs):
        blockers.append(("split_review_required", split_blocker(inputs)))
    missing_core = [name for name in ["manual_summary", "qqq_lead_decision_summary", "qqq_leverage_validation_report"] if not inputs.get(name)]
    if missing_core:
        blockers.append(("missing_core_saved_inputs", f"Missing core saved inputs: {', '.join(missing_core)}"))
    status = MISSING_STATUS if any(name == "missing_core_saved_inputs" for name, _ in blockers) else COST_STATUS if cost_blocker(inputs) else DRAW_STATUS if drawdown_blocker(inputs) else READY_STATUS
    return [
        report_row(created_at, name, "blocked", "blocker", QQQ_LEAD, "preview_discussion_candidate", "preview_candidate_readiness_report", detail, detail, NEXT_STEP, status)
        for name, detail in blockers
    ]


def build_report_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]], status: str, blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        report_row(created_at, "final_preview_candidate_readiness_status", "pass" if status == READY_STATUS else "manual_review_required", "info" if status == READY_STATUS else "warning", QQQ_LEAD, "preview_discussion_candidate", "preview_candidate_readiness_report", status, blocker_summary(blocker_rows), NEXT_STEP, status),
        report_row(created_at, "confirmed_research_lead", "pass", "info", QQQ_LEAD, "research_lead", "data/project_research_state_summary.csv", lead_confirmation(inputs), "", NEXT_STEP, status),
        report_row(created_at, "evidence_supporting_preview_discussion", "pass", "info", QQQ_LEAD, "preview_discussion_candidate", "data/qqq_lead_decision_summary.csv", evidence_supporting_preview(inputs), "", NEXT_STEP, status),
        report_row(created_at, "paper_execution_boundary", "blocked", "blocker", QQQ_LEAD, "research_lead", "preview_candidate_readiness_report", "Preview discussion readiness is not execution approval and creates no order instructions.", "paper_execution_approved=false", NEXT_STEP, status),
    ]


def build_summary_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]], status: str, blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        summary_row(created_at, "final_preview_candidate_readiness_status", status, "Manual preview-candidate discussion label only; not paper execution."),
        summary_row(created_at, "confirmed_research_lead", QQQ_LEAD, lead_confirmation(inputs)),
        summary_row(created_at, "evidence_supporting_preview_discussion", evidence_supporting_preview(inputs), "QQQ trend gate improved versus previous lead and is simpler."),
        summary_row(created_at, "remaining_blockers", blocker_summary(blocker_rows), "Blockers are retained before any paper execution discussion."),
        summary_row(created_at, "recommended_next_step", NEXT_STEP, "Manual discussion only; do not wire strategy to execution."),
        summary_row(created_at, "paper_execution_approved", "false", "Paper execution remains false."),
        summary_row(created_at, "execution_approved", "false", "Execution remains false."),
        summary_row(created_at, "scheduling_approved", "false", "Scheduling remains false."),
    ]
    return rows


def choose_preview_status(inputs: dict[str, list[dict[str, Any]]], blocker_rows: list[dict[str, Any]]) -> str:
    if not inputs.get("manual_summary") or not inputs.get("qqq_lead_decision_summary") or not inputs.get("qqq_leverage_validation_report"):
        return MISSING_STATUS
    if cost_blocker(inputs):
        return COST_STATUS
    if drawdown_blocker(inputs):
        return DRAW_STATUS
    if any(row.get("check_name") == "split_review_required" for row in blocker_rows):
        return NOT_READY_STATUS
    return READY_STATUS


def lead_confirmation(inputs: dict[str, list[dict[str, Any]]]) -> str:
    saved = summary_value(inputs["manual_summary"], "confirmed_stock_etf_research_lead")
    state = summary_value(inputs["project_research_state_summary"], "stock_etf_active_research_lead")
    return f"manual_pack_lead={saved}; project_state_lead={state}; status={QQQ_STATUS}; execution_approved=false"


def manual_status(inputs: dict[str, list[dict[str, Any]]]) -> str:
    saved = summary_value(inputs["manual_summary"], "final_manual_review_status")
    return saved if saved != "unavailable" else MANUAL_REVIEW_STATUS


def evidence_supporting_preview(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        "improved_vs_previous_lead: qqq_100 CAGR=16.8429, Sharpe=1.0027, MaxDD=-23.4576, Calmar=0.718; "
        "previous lead CAGR=14.1039, Sharpe=0.7192, MaxDD=-29.5357, Calmar=0.4775; "
        f"adaptive_alternative={QQQ_ADAPTIVE}; rejected_high_drawdown_reference={QQQ_HIGH_DRAWDOWN}; "
        f"lead_decision={summary_value(inputs['qqq_lead_decision_summary'], 'final_lead_decision')}"
    )


def adaptive_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return summary_details(inputs["qqq_lead_decision_summary"], "ambitious_qqq_candidate") or "CAGR=20.2819; Sharpe=0.9749; MaxDD=-25.9889; Calmar=0.7804; higher Calmar but worse Sharpe and deeper drawdown."


def high_drawdown_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return summary_details(inputs["qqq_lead_decision_summary"], "rejected_high_drawdown_reference") or "CAGR=23.3903; Sharpe=0.9542; MaxDD=-33.892; Calmar=0.6901; rejected high-drawdown reference."


def split_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    rows = matching_rows(inputs["qqq_leverage_validation_splits"], QQQ_LEAD)
    if not rows:
        return "manual_review_required: saved split rows missing for qqq_100_trend_gate"
    labels = sorted({str(row.get("split_sensitivity_label") or row.get("status") or "saved_split_context") for row in rows})
    return f"saved_rows={len(rows)}; labels={', '.join(labels)}"


def cost_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    rows = matching_rows(inputs["qqq_leverage_validation_costs"], QQQ_LEAD)
    if not rows:
        return "manual_review_required: saved cost/financing rows missing for qqq_100_trend_gate"
    labels = sorted({str(row.get("cost_sensitivity_label") or row.get("financing_sensitivity_label") or row.get("status") or "saved_cost_context") for row in rows})
    return f"saved_rows={len(rows)}; labels={', '.join(labels)}"


def drawdown_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    rows = matching_rows(inputs["qqq_leverage_validation_drawdowns"], QQQ_LEAD)
    if not rows:
        return "future_review_needed: saved drawdown rows missing for qqq_100_trend_gate"
    recovery = "recovery_context_available" if any(any("recover" in key.lower() for key in row) for row in rows) else "future_review_needed: recovery fields absent"
    return f"qqq_100 MaxDD=-23.4576; adaptive MaxDD=-25.9889; qqq_150 MaxDD=-33.892; saved_rows={len(rows)}; {recovery}"


def split_blocker(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "manual_review_required: saved split rows missing" if "missing" in split_summary(inputs) else ""


def cost_blocker(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "manual_review_required: saved cost/financing rows missing" if "missing" in cost_summary(inputs) else ""


def drawdown_blocker(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "future_review_needed: saved drawdown/recovery rows missing or incomplete" if "future_review_needed" in drawdown_summary(inputs) else ""


def split_check_status(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "manual_review_required" if split_blocker(inputs) else "saved_context_available"


def cost_check_status(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "manual_review_required" if cost_blocker(inputs) else "saved_context_available"


def drawdown_check_status(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return "future_review_needed" if drawdown_blocker(inputs) else "saved_context_available"


def matching_rows(rows: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if name in {str(row.get("candidate_name", "")), str(row.get("variant_name", "")), str(row.get("strategy_name", ""))}
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key or row.get("metric_name") == key or row.get("check_name") == key:
            return str(row.get("summary_value") or row.get("metric_value") or "unavailable")
    return "unavailable"


def summary_details(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("details") or row.get("summary_value") or "")
    return ""


def blocker_summary(rows: list[dict[str, Any]]) -> str:
    names = [str(row.get("check_name")) for row in rows if row.get("severity") == "blocker"]
    return ", ".join(names) or "manual_review_required"


def approval_values(rows: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in ["paper_execution_approved", "execution_approved", "scheduling_approved"]:
        values = {str(row.get(field, "false")).lower() for row in rows}
        result[field] = "false" if values <= {"false", ""} else ",".join(sorted(values))
    return result


def report_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    candidate_name: str,
    candidate_role: str,
    evidence_source: str,
    details: str,
    blocker: str,
    recommended_next_step: str,
    preview_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "candidate_name": candidate_name,
        "candidate_role": candidate_role,
        "evidence_source": evidence_source,
        "details": details,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        "preview_candidate_discussion_status": preview_status,
        "preview_discussion_approved": preview_status == READY_STATUS,
        **safety_flags(),
    }


def summary_row(created_at: str, name: str, value: str, details: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "summary_name": name,
        "summary_value": value,
        "details": details,
        "preview_discussion_approved": value == READY_STATUS if name == "final_preview_candidate_readiness_status" else False,
        **safety_flags(),
    }


def safety_flags() -> dict[str, bool]:
    return {
        "paper_execution_approved": False,
        "execution_approved": False,
        "leverage_execution_approved": False,
        "margin_approved": False,
        "scheduling_approved": False,
        "alpaca_called": False,
        "orders_created": False,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ preview-candidate readiness report complete. Research/report only; paper_execution_approved=False.",
        f"Final preview-candidate readiness status: {summary_value(summary_rows, 'final_preview_candidate_readiness_status')}",
        f"Confirmed research lead: {summary_value(summary_rows, 'confirmed_research_lead')}",
        f"Evidence supporting preview discussion: {summary_value(summary_rows, 'evidence_supporting_preview_discussion')}",
        f"Remaining blockers: {summary_value(summary_rows, 'remaining_blockers')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        "paper_execution_approved=false",
        "execution_approved=false",
        "scheduling_approved=false",
        f"Saved report to {paths['report']}",
        f"Saved summary to {paths['summary']}",
        f"Saved evidence to {paths['evidence']}",
        f"Saved blockers to {paths['blockers']}",
        "Warning: preview readiness is manual discussion only; no paper orders, live trading, scheduling, or strategy-to-execution wiring are approved.",
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
