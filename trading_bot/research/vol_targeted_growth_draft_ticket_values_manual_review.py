"""Manual review and readiness checkpoints for review-only draft ticket values.

These reports read saved outputs only. They can confirm the review-only draft
values are coherent enough for a later approval-request discussion, but they do
not approve executable values, create broker-ready order fields, or submit
orders.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
MANUAL_REVIEW_STATUS = "vol_targeted_growth_draft_ticket_values_manual_review_required"
MANUAL_REVIEW_DECISION = "DRAFT_TICKET_VALUES_REVIEWED_MANUAL_REVIEW_REQUIRED_NOT_EXECUTABLE"
READINESS_STATUS = "vol_targeted_growth_executable_ticket_values_readiness_manual_review_required"
READINESS_DECISION = "READY_TO_REQUEST_EXECUTABLE_TICKET_VALUES_APPROVAL_NOT_APPROVED"
READINESS_BLOCKED_DECISION = "NOT_READY_TO_REQUEST_EXECUTABLE_TICKET_VALUES_APPROVAL"
NEXT_STEP = "manual_review_before_any_explicit_executable_ticket_values_approval_request"

MANUAL_REVIEW_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_draft_ticket_values_manual_review.csv"),
    "summary": Path("data/vol_targeted_growth_draft_ticket_values_manual_review_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_draft_ticket_values_manual_review_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_draft_ticket_values_manual_review_evidence.csv"),
}

READINESS_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_executable_ticket_values_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_values_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_values_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_values_readiness_evidence.csv"),
}

INPUT_FILES = {
    "draft_values": Path("data/vol_targeted_growth_review_only_draft_ticket_values_summary.csv"),
    "draft_values_detail": Path("data/vol_targeted_growth_review_only_draft_ticket_values_values.csv"),
    "draft_values_quality_gate": Path("data/vol_targeted_growth_review_only_draft_ticket_values_quality_gate_summary.csv"),
    "approval_record": Path("data/vol_targeted_growth_draft_ticket_value_approval_record_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "review_only": True,
    "manual_review_completed": False,
    "executable_ticket_values_approval_request_ready": False,
    "executable_ticket_values_approval_requested": False,
    "executable_ticket_values_approval_recorded": False,
    "executable_ticket_values_approved": False,
    "ticket_values_approved": False,
    "order_values_populated": False,
    "order_instructions_created": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REPORT_COLUMNS = ["check_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class DraftTicketValuesManualReviewResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_draft_ticket_values_manual_review(root_dir: Path | str = ".") -> DraftTicketValuesManualReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_manual_review_rows(context)
    summary_rows = build_summary_rows(context, MANUAL_REVIEW_STATUS, MANUAL_REVIEW_DECISION, manual_review_completed=True, readiness_ready=False)
    blocker_rows = common_blockers("manual_review_is_not_execution_approval", "Manual review does not approve executable ticket values.", "prepare_executable_ticket_values_readiness_if_review_is_clear", manual_review_completed=True, readiness_ready=False)
    evidence_rows = evidence_rows_for(inputs, manual_review_completed=True, readiness_ready=False)
    paths = write_all(root, MANUAL_REVIEW_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return DraftTicketValuesManualReviewResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, summary_lines("Draft ticket values manual review complete. No executable values approved.", summary_rows, paths["report"], "final_draft_ticket_values_manual_review_status", "final_draft_ticket_values_manual_review_decision"))


def show_vol_targeted_growth_draft_ticket_values_manual_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / MANUAL_REVIEW_OUTPUTS["summary"], "Volatility-targeted draft ticket values manual review saved display. Not executable.", "final_draft_ticket_values_manual_review_status", "final_draft_ticket_values_manual_review_decision")


def generate_vol_targeted_growth_executable_ticket_values_readiness(root_dir: Path | str = ".") -> DraftTicketValuesManualReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    ready = context["quality_gate_passed"] == "True" and context["review_value_count"] != "0"
    decision = READINESS_DECISION if ready else READINESS_BLOCKED_DECISION
    report_rows = build_readiness_rows(context, ready)
    summary_rows = build_summary_rows(context, READINESS_STATUS, decision, manual_review_completed=True, readiness_ready=ready)
    blocker_rows = common_blockers("executable_ticket_values_not_approved", "Readiness can support a later approval request only; no executable values are approved.", NEXT_STEP, manual_review_completed=True, readiness_ready=ready)
    evidence_rows = evidence_rows_for(inputs, manual_review_completed=True, readiness_ready=ready)
    paths = write_all(root, READINESS_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return DraftTicketValuesManualReviewResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, summary_lines("Executable ticket values readiness complete. Approval not requested or recorded.", summary_rows, paths["report"], "final_executable_ticket_values_readiness_status", "final_executable_ticket_values_readiness_decision"))


def show_vol_targeted_growth_executable_ticket_values_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / READINESS_OUTPUTS["summary"], "Volatility-targeted executable ticket values readiness saved display. Approval not requested.", "final_executable_ticket_values_readiness_status", "final_executable_ticket_values_readiness_decision")


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "draft_values_decision": summary_value(inputs["draft_values"], "final_review_only_draft_ticket_values_decision") or "missing_draft_values",
        "draft_values_created": summary_value(inputs["draft_values"], "draft_ticket_values_created") or "False",
        "review_value_count": summary_value(inputs["draft_values"], "review_value_count") or "0",
        "quality_gate_decision": summary_value(inputs["draft_values_quality_gate"], "final_review_only_draft_ticket_values_quality_decision") or "missing_quality_gate",
        "quality_gate_passed": summary_value(inputs["draft_values_quality_gate"], "quality_gate_passed") or "False",
        "executable_order_field_count": summary_value(inputs["draft_values_quality_gate"], "executable_order_field_count") or "unknown",
        "forbidden_field_count": summary_value(inputs["draft_values_quality_gate"], "forbidden_field_count") or "unknown",
        "approval_record_decision": summary_value(inputs["approval_record"], "final_draft_ticket_value_approval_record_decision") or "missing_approval_record",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
        "detail_row_count": str(len(inputs["draft_values_detail"])),
    }


def build_manual_review_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row("draft_values_present", "pass" if context["draft_values_created"] == "True" else "manual_review_required", "critical", context["draft_values_decision"], "Draft values must exist before review.", "refresh_review_only_draft_ticket_values", True, False),
        report_row("quality_gate", "pass" if context["quality_gate_passed"] == "True" else "manual_review_required", "critical", context["quality_gate_decision"], "Quality gate must pass before readiness can be considered.", "refresh_review_only_draft_ticket_values_quality_gate", True, False),
        report_row("execution_boundary", "execution_blocked", "critical", context["go_no_go_decision"], "Go/no-go remains blocked for execution.", "keep_execution_blocked", True, False),
    ]


def build_readiness_rows(context: dict[str, str], ready: bool) -> list[dict[str, Any]]:
    return [
        report_row("manual_review_context", "ready" if ready else "manual_review_required", "critical", f"review_value_count={context['review_value_count']}; detail_rows={context['detail_row_count']}", "Review-only draft values can support asking later for approval only if clear.", NEXT_STEP, True, ready),
        report_row("non_executable_quality", "pass" if ready else "manual_review_required", "critical", f"executable_order_field_count={context['executable_order_field_count']}; forbidden_field_count={context['forbidden_field_count']}", "Readiness requires no executable or forbidden fields.", NEXT_STEP, True, ready),
        report_row("approval_boundary", "approval_not_requested", "critical", "executable_ticket_values_approval_requested=false", "This readiness report does not ask for or record approval.", NEXT_STEP, True, ready),
    ]


def build_summary_rows(context: dict[str, str], status: str, decision: str, *, manual_review_completed: bool, readiness_ready: bool) -> list[dict[str, Any]]:
    status_name = "final_executable_ticket_values_readiness_status" if status == READINESS_STATUS else "final_draft_ticket_values_manual_review_status"
    decision_name = "final_executable_ticket_values_readiness_decision" if status_name.startswith("final_executable") else "final_draft_ticket_values_manual_review_decision"
    data = [
        (status_name, status, "Saved-output checkpoint status."),
        (decision_name, decision, "Manual-review/readiness decision; not approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("draft_values_decision", context["draft_values_decision"], "Saved review-only draft values decision."),
        ("draft_values_created", context["draft_values_created"], "True means review labels exist."),
        ("review_value_count", context["review_value_count"], "Saved review value count."),
        ("draft_values_quality_gate_decision", context["quality_gate_decision"], "Saved quality gate decision."),
        ("draft_values_quality_gate_passed", context["quality_gate_passed"], "True only when review values remain non-executable."),
        ("executable_order_field_count", context["executable_order_field_count"], "Must remain 0."),
        ("forbidden_field_count", context["forbidden_field_count"], "Must remain 0."),
        ("manual_review_completed", str(manual_review_completed), "Manual review checkpoint completed for saved-output evidence only."),
        ("executable_ticket_values_approval_request_ready", str(readiness_ready), "True means a future explicit approval request could be considered."),
        ("executable_ticket_values_approval_requested", "False", "No approval request is made."),
        ("executable_ticket_values_approval_recorded", "False", "No approval record exists."),
        ("executable_ticket_values_approved", "False", "No executable values are approved."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("order_values_populated", "False", "No broker-ready order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "executable_ticket_values_not_approved", "Readiness is not approval."),
        ("recommended_next_step", NEXT_STEP, "Separate manual approval request would be required later."),
    ]
    return [summary_row(name, value, details, manual_review_completed, readiness_ready) for name, value, details in data]


def common_blockers(name: str, details: str, next_step: str, *, manual_review_completed: bool, readiness_ready: bool) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step, manual_review_completed, readiness_ready),
        blocker_row("executable_ticket_values_not_approved", "blocked", "critical", "executable_ticket_values_approved=false", NEXT_STEP, manual_review_completed, readiness_ready),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", manual_review_completed, readiness_ready),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", manual_review_completed, readiness_ready),
    ]


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]], *, manual_review_completed: bool, readiness_ready: bool) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", manual_review_completed, readiness_ready) for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", manual_review_completed, readiness_ready))
    return rows


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def flags(manual_review_completed: bool, readiness_ready: bool) -> dict[str, bool]:
    updated = dict(SAFETY_FLAGS)
    updated["manual_review_completed"] = manual_review_completed
    updated["executable_ticket_values_approval_request_ready"] = readiness_ready
    return updated


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, manual_review_completed: bool, readiness_ready: bool) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(manual_review_completed, readiness_ready)}


def summary_row(name: str, value: str, details: str, manual_review_completed: bool, readiness_ready: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(manual_review_completed, readiness_ready)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, manual_review_completed: bool, readiness_ready: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(manual_review_completed, readiness_ready)}


def evidence_row(name: str, value: str, details: str, manual_review_completed: bool, readiness_ready: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(manual_review_completed, readiness_ready)}


def write_all(root: Path, outputs: dict[str, Path], report_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in outputs.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def show_summary(path: Path, title: str, status_key: str, decision_key: str) -> tuple[int, list[str]]:
    if not path.exists():
        return 1, [f"{title} is missing.", "Run the matching report command first.", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false"]
    rows = read_csv_rows(path)
    return 0, [
        title,
        f"{status_key}: {summary_value(rows, status_key)}",
        f"{decision_key}: {summary_value(rows, decision_key)}",
        f"manual_review_completed: {summary_value(rows, 'manual_review_completed')}",
        f"executable_ticket_values_approval_request_ready: {summary_value(rows, 'executable_ticket_values_approval_request_ready')}",
        f"executable_ticket_values_approved: {summary_value(rows, 'executable_ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def summary_lines(title: str, rows: list[dict[str, Any]], report_path: Path, status_key: str, decision_key: str) -> list[str]:
    return [
        title,
        f"{status_key}={summary_value(rows, status_key)}",
        f"{decision_key}={summary_value(rows, decision_key)}",
        f"manual_review_completed={summary_value(rows, 'manual_review_completed')}",
        f"executable_ticket_values_approval_request_ready={summary_value(rows, 'executable_ticket_values_approval_request_ready')}",
        f"executable_ticket_values_approval_requested={summary_value(rows, 'executable_ticket_values_approval_requested')}",
        f"executable_ticket_values_approved={summary_value(rows, 'executable_ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
