"""Executable ticket-values approval wording and record for the volatility seed.

These saved-output checkpoints allow a later step to populate non-submitting
executable ticket values for manual review. They do not create an executable
ticket, submit orders, call a broker, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve creating executable ticket values for manual review only; do not submit orders."
WORDING_STATUS = "vol_targeted_growth_executable_ticket_values_approval_wording_manual_review_required"
WORDING_DECISION = "EXECUTABLE_TICKET_VALUES_APPROVAL_WORDING_DEFINED_NOT_APPROVED"
RECORD_STATUS = "vol_targeted_growth_executable_ticket_values_approval_recorded_manual_review_required"
RECORD_DECISION = "EXECUTABLE_TICKET_VALUES_APPROVAL_RECORDED_NO_ORDER_SUBMISSION"
NEXT_STEP = "populate_non_submitting_executable_ticket_values_for_manual_review_only"

WORDING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_executable_ticket_values_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_values_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_values_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_values_approval_wording_evidence.csv"),
}

RECORD_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_executable_ticket_values_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_values_approval_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_values_approval_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_values_approval_record_evidence.csv"),
}

INPUT_FILES = {
    "values_readiness": Path("data/vol_targeted_growth_executable_ticket_values_readiness_summary.csv"),
    "draft_values_manual_review": Path("data/vol_targeted_growth_draft_ticket_values_manual_review_summary.csv"),
    "review_only_draft_values_quality_gate": Path("data/vol_targeted_growth_review_only_draft_ticket_values_quality_gate_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

BASE_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "executable_ticket_values_approval_wording_defined": False,
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

REPORT_COLUMNS = ["check_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *BASE_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *BASE_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *BASE_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *BASE_FLAGS.keys()]


@dataclass
class ExecutableTicketValuesApprovalResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_executable_ticket_values_approval_wording(root_dir: Path | str = ".") -> ExecutableTicketValuesApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        report_row("approval_wording", "approval_wording_defined_not_recorded", "critical", APPROVAL_PHRASE, "This phrase is only permission to create later non-submitting values for review.", "wait_for_explicit_executable_ticket_values_approval_record", wording_defined=True, approval_recorded=False),
        report_row("submission_boundary", "orders_blocked", "critical", "orders_submitted=false; execution_approved=false", "The wording is not a broker order, ticket submission, or execution approval.", "keep_orders_blocked", wording_defined=True, approval_recorded=False),
    ]
    summary_rows = build_summary_rows(inputs, WORDING_STATUS, WORDING_DECISION, wording_defined=True, approval_recorded=False)
    blocker_rows = common_blockers("approval_wording_not_recorded", "Wording exists but approval is not recorded.", "wait_for_explicit_executable_ticket_values_approval_record", wording_defined=True, approval_recorded=False)
    evidence_rows = build_evidence_rows(inputs, wording_defined=True, approval_recorded=False)
    paths = write_all(root, WORDING_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return ExecutableTicketValuesApprovalResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, summary_lines("Executable ticket-values approval wording complete. No approval recorded.", summary_rows, paths["report"], "final_executable_ticket_values_approval_wording_status", "final_executable_ticket_values_approval_wording_decision"))


def show_vol_targeted_growth_executable_ticket_values_approval_wording(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / WORDING_OUTPUTS["summary"], "Volatility-targeted executable ticket-values approval wording saved display. No approval recorded.", "final_executable_ticket_values_approval_wording_status", "final_executable_ticket_values_approval_wording_decision")


def generate_vol_targeted_growth_executable_ticket_values_approval_record(root_dir: Path | str = ".") -> ExecutableTicketValuesApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        report_row("approval_record", "executable_ticket_values_approval_recorded", "critical", APPROVAL_PHRASE, "Approval is limited to a later non-submitting ticket-values population step.", NEXT_STEP, wording_defined=True, approval_recorded=True),
        report_row("ticket_boundary", "ticket_not_created", "critical", "executable_ticket_created=false; order_values_populated=false", "The approval record still does not create values, tickets, or order instructions.", NEXT_STEP, wording_defined=True, approval_recorded=True),
        report_row("execution_boundary", "execution_not_approved", "critical", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false", "Execution remains a separate future decision and is false here.", "keep_execution_blocked", wording_defined=True, approval_recorded=True),
    ]
    summary_rows = build_summary_rows(inputs, RECORD_STATUS, RECORD_DECISION, wording_defined=True, approval_recorded=True)
    blocker_rows = common_blockers("ticket_values_not_populated", "Approval permits a later non-submitting value population step only; no values are present.", NEXT_STEP, wording_defined=True, approval_recorded=True)
    evidence_rows = build_evidence_rows(inputs, wording_defined=True, approval_recorded=True)
    paths = write_all(root, RECORD_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return ExecutableTicketValuesApprovalResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, summary_lines("Executable ticket-values approval record complete. Values and execution remain blocked.", summary_rows, paths["report"], "final_executable_ticket_values_approval_record_status", "final_executable_ticket_values_approval_record_decision"))


def show_vol_targeted_growth_executable_ticket_values_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / RECORD_OUTPUTS["summary"], "Volatility-targeted executable ticket-values approval record saved display. Values and execution remain blocked.", "final_executable_ticket_values_approval_record_status", "final_executable_ticket_values_approval_record_decision")


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], status: str, decision: str, *, wording_defined: bool, approval_recorded: bool) -> list[dict[str, Any]]:
    status_name = "final_executable_ticket_values_approval_record_status" if approval_recorded else "final_executable_ticket_values_approval_wording_status"
    decision_name = "final_executable_ticket_values_approval_record_decision" if approval_recorded else "final_executable_ticket_values_approval_wording_decision"
    data = [
        (status_name, status, "Saved-output executable ticket-values approval checkpoint."),
        (decision_name, decision, "Approval boundary for non-submitting executable ticket values only."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_phrase", APPROVAL_PHRASE, "Narrow approval wording."),
        ("values_readiness_decision", summary_value(inputs["values_readiness"], "final_executable_ticket_values_readiness_decision") or "missing_values_readiness", "Prior saved readiness context."),
        ("values_approval_request_ready", summary_value(inputs["values_readiness"], "executable_ticket_values_approval_request_ready") or "False", "True means a request could be considered."),
        ("draft_values_manual_review_decision", summary_value(inputs["draft_values_manual_review"], "final_draft_ticket_values_manual_review_decision") or "missing_draft_values_manual_review", "Saved manual review context."),
        ("review_only_draft_values_quality_gate_decision", summary_value(inputs["review_only_draft_values_quality_gate"], "final_review_only_draft_ticket_values_quality_decision") or "missing_review_only_quality_gate", "Saved review-only quality gate context."),
        ("go_no_go_decision", summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard", "Saved dashboard context."),
        ("executable_ticket_values_approval_wording_defined", str(wording_defined), "True when the wording checkpoint exists."),
        ("executable_ticket_values_approval_requested", str(approval_recorded), "True only in the explicit approval record checkpoint."),
        ("executable_ticket_values_approval_recorded", str(approval_recorded), "True only when the approval record checkpoint is generated."),
        ("executable_ticket_values_approved", str(approval_recorded), "True means later non-submitting value population may proceed; it is not execution approval."),
        ("ticket_values_approved", str(approval_recorded), "True only as non-submitting ticket-values approval; not order submission approval."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, price, account, or broker field is populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("ticket_instance_created", "False", "No ticket instance exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_created", "False", "No orders are created."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "ticket_values_not_populated" if approval_recorded else "executable_ticket_values_approval_not_recorded", "Approval record is not value population or execution."),
        ("recommended_next_step", NEXT_STEP if approval_recorded else "wait_for_explicit_executable_ticket_values_approval_record", "Next step remains non-submitting and review-only."),
    ]
    return [summary_row(name, value, details, wording_defined, approval_recorded) for name, value, details in data]


def common_blockers(name: str, details: str, next_step: str, *, wording_defined: bool, approval_recorded: bool) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step, wording_defined, approval_recorded),
        blocker_row("order_values_not_populated", "blocked", "critical", "order_values_populated=false", "populate_values_only_in_later_non_submitting_step", wording_defined, approval_recorded),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", wording_defined, approval_recorded),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", wording_defined, approval_recorded),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], *, wording_defined: bool, approval_recorded: bool) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", wording_defined, approval_recorded)
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("approval_phrase", APPROVAL_PHRASE, "Narrow approval phrase; not an order instruction.", wording_defined, approval_recorded))
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", wording_defined, approval_recorded))
    return rows


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def flags(wording_defined: bool, approval_recorded: bool) -> dict[str, bool]:
    updated = dict(BASE_FLAGS)
    updated["executable_ticket_values_approval_wording_defined"] = wording_defined
    updated["executable_ticket_values_approval_requested"] = approval_recorded
    updated["executable_ticket_values_approval_recorded"] = approval_recorded
    updated["executable_ticket_values_approved"] = approval_recorded
    updated["ticket_values_approved"] = approval_recorded
    return updated


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, *, wording_defined: bool, approval_recorded: bool) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(wording_defined, approval_recorded)}


def summary_row(name: str, value: str, details: str, wording_defined: bool, approval_recorded: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(wording_defined, approval_recorded)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, wording_defined: bool, approval_recorded: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(wording_defined, approval_recorded)}


def evidence_row(name: str, value: str, details: str, wording_defined: bool, approval_recorded: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(wording_defined, approval_recorded)}


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


def show_summary(path: Path, title: str, status_name: str, decision_name: str) -> tuple[int, list[str]]:
    if not path.exists():
        return 1, [f"{title} is missing.", "Run the matching report command first.", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false"]
    rows = read_csv_rows(path)
    return 0, [
        title,
        f"{status_name}: {summary_value(rows, status_name)}",
        f"{decision_name}: {summary_value(rows, decision_name)}",
        f"executable_ticket_values_approval_wording_defined: {summary_value(rows, 'executable_ticket_values_approval_wording_defined')}",
        f"executable_ticket_values_approval_recorded: {summary_value(rows, 'executable_ticket_values_approval_recorded')}",
        f"executable_ticket_values_approved: {summary_value(rows, 'executable_ticket_values_approved')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: approval is limited to later non-submitting value population; this does not submit orders.",
    ]


def summary_lines(title: str, rows: list[dict[str, Any]], report_path: Path, status_name: str, decision_name: str) -> list[str]:
    return [
        title,
        f"{status_name}={summary_value(rows, status_name)}",
        f"{decision_name}={summary_value(rows, decision_name)}",
        f"executable_ticket_values_approval_wording_defined={summary_value(rows, 'executable_ticket_values_approval_wording_defined')}",
        f"executable_ticket_values_approval_requested={summary_value(rows, 'executable_ticket_values_approval_requested')}",
        f"executable_ticket_values_approval_recorded={summary_value(rows, 'executable_ticket_values_approval_recorded')}",
        f"executable_ticket_values_approved={summary_value(rows, 'executable_ticket_values_approved')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
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
