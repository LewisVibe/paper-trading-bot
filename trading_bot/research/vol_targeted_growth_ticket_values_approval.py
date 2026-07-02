"""Ticket-values discussion approval checkpoint for the volatility seed.

This records readiness, wording, and a design-only approval record for
discussing future ticket values. It deliberately does not populate side,
quantity, order type, time-in-force, price, account references, or any
submit-ready instruction.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve ticket-value design discussion only; do not populate order values or submit orders."
READINESS_STATUS = "vol_targeted_growth_ticket_values_approval_readiness_manual_review_required"
READINESS_DECISION = "READY_FOR_TICKET_VALUE_DESIGN_DISCUSSION_NOT_VALUES_APPROVED"
WORDING_STATUS = "vol_targeted_growth_ticket_values_approval_wording_manual_review_required"
WORDING_DECISION = "TICKET_VALUE_DISCUSSION_APPROVAL_WORDING_DEFINED_NOT_APPROVED"
RECORD_STATUS = "vol_targeted_growth_ticket_values_approval_recorded_manual_review_required"
RECORD_DECISION = "TICKET_VALUE_DISCUSSION_APPROVED_NO_ORDER_VALUES"
NEXT_STEP = "draft_non_executable_ticket_value_placeholders_without_values"

READINESS_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_ticket_values_approval_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_ticket_values_approval_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_ticket_values_approval_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_ticket_values_approval_readiness_evidence.csv"),
}

WORDING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_ticket_values_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_ticket_values_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_ticket_values_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_ticket_values_approval_wording_evidence.csv"),
}

RECORD_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_ticket_values_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_ticket_values_approval_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_ticket_values_approval_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_ticket_values_approval_record_evidence.csv"),
}

INPUT_FILES = {
    "execution_design_approval_record": Path("data/vol_targeted_growth_execution_design_approval_record_summary.csv"),
    "non_submitting_executable_ticket_design": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design_summary.csv"),
    "manual_ticket_value_design": Path("data/vol_targeted_growth_manual_ticket_value_design_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

BASE_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "ticket_value_discussion_only": True,
    "ticket_value_discussion_approved": False,
    "ticket_value_approval_recorded": False,
    "ticket_values_approved": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "order_values_populated": False,
    "order_instructions_created": False,
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
class TicketValuesApprovalResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_ticket_values_approval_readiness(root_dir: Path | str = ".") -> TicketValuesApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    ready = readiness_ok(inputs)
    report_rows = [
        row("execution_design_approval", "present" if ready["design_approved"] else "manual_review_required", "critical", ready["design_decision"], "Design-only approval must exist before ticket-value discussion.", "refresh_execution_design_approval_record", False),
        row("non_submitting_ticket_design", "present" if ready["ticket_design_present"] else "manual_review_required", "critical", ready["ticket_design_decision"], "A non-submitting ticket design must exist before value discussion.", "refresh_non_submitting_executable_ticket_design", False),
        row("order_value_boundary", "values_not_populated", "critical", "order_values_populated=false", "Readiness does not populate or approve values.", "keep_order_values_blank", False),
    ]
    summary_rows = common_summary(inputs, READINESS_STATUS, READINESS_DECISION if ready["ready"] else "NOT_READY_FOR_TICKET_VALUE_DISCUSSION", "False", "False", "True" if ready["ready"] else "False", "wait_for_explicit_ticket_value_discussion_approval")
    blocker_rows = common_blockers("explicit_ticket_value_discussion_approval_not_recorded", "approval_recorded=false", "wait_for_explicit_ticket_value_discussion_approval", False)
    evidence_rows = evidence_for(inputs, False)
    output_paths = write_all(root, READINESS_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return TicketValuesApprovalResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, lines("Ticket-values approval readiness complete. Report only; no values approved.", summary_rows, output_paths["report"], "final_ticket_values_readiness_status", "final_ticket_values_readiness_decision"))


def show_vol_targeted_growth_ticket_values_approval_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / READINESS_OUTPUTS["summary"], "Volatility-targeted ticket-values approval readiness saved display. Report only; no values approved.", "final_ticket_values_readiness_status", "final_ticket_values_readiness_decision")


def generate_vol_targeted_growth_ticket_values_approval_wording(root_dir: Path | str = ".") -> TicketValuesApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        row("ticket_value_discussion_phrase", "approval_wording_defined_not_recorded", "critical", APPROVAL_PHRASE, "Defines the narrow wording for discussion only.", "wait_for_explicit_ticket_value_discussion_approval", False),
        row("value_boundary", "values_not_approved", "critical", "ticket_values_approved=false; order_values_populated=false", "The wording cannot become a buy/sell/quantity instruction.", "keep_order_values_blank", False),
    ]
    summary_rows = common_summary(inputs, WORDING_STATUS, WORDING_DECISION, "False", "False", "True", "wait_for_explicit_ticket_value_discussion_approval")
    blocker_rows = common_blockers("ticket_value_discussion_approval_not_recorded", "ticket_value_approval_recorded=false", "wait_for_explicit_ticket_value_discussion_approval", False)
    evidence_rows = evidence_for(inputs, False) + [evidence_row("future_approval_phrase", APPROVAL_PHRASE, "Discussion-only wording; not value approval.", False)]
    output_paths = write_all(root, WORDING_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return TicketValuesApprovalResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, lines("Ticket-values approval wording complete. Report only; no approval recorded.", summary_rows, output_paths["report"], "final_ticket_values_wording_status", "final_ticket_values_wording_decision"))


def show_vol_targeted_growth_ticket_values_approval_wording(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / WORDING_OUTPUTS["summary"], "Volatility-targeted ticket-values approval wording saved display. Report only; no approval recorded.", "final_ticket_values_wording_status", "final_ticket_values_wording_decision")


def generate_vol_targeted_growth_ticket_values_approval_record(root_dir: Path | str = ".") -> TicketValuesApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        row("ticket_value_discussion_record", "discussion_approval_recorded", "critical", APPROVAL_PHRASE, "Approval is limited to drafting non-executable placeholders for future values.", NEXT_STEP, True),
        row("order_value_boundary", "values_not_populated", "critical", "order_values_populated=false; ticket_values_approved=false", "No executable order values are approved.", NEXT_STEP, True),
        row("execution_boundary", "execution_not_approved", "critical", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false", "Execution approval remains separate and false.", NEXT_STEP, True),
    ]
    summary_rows = common_summary(inputs, RECORD_STATUS, RECORD_DECISION, "True", "True", "True", NEXT_STEP)
    blocker_rows = common_blockers("ticket_values_not_approved", "ticket_values_approved=false; order_values_populated=false", NEXT_STEP, True)
    evidence_rows = evidence_for(inputs, True) + [evidence_row("recorded_approval_phrase", APPROVAL_PHRASE, "Discussion-only approval recorded; order values remain blank.", True)]
    output_paths = write_all(root, RECORD_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return TicketValuesApprovalResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, lines("Ticket-values approval record complete. Discussion only; no values or execution approved.", summary_rows, output_paths["report"], "final_ticket_values_record_status", "final_ticket_values_record_decision"))


def show_vol_targeted_growth_ticket_values_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / RECORD_OUTPUTS["summary"], "Volatility-targeted ticket-values approval record saved display. Discussion only; no values approved.", "final_ticket_values_record_status", "final_ticket_values_record_decision")


def readiness_ok(inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    design_decision = summary_value(inputs["execution_design_approval_record"], "final_execution_design_record_decision") or "missing_execution_design_approval_record"
    ticket_design_decision = summary_value(inputs["non_submitting_executable_ticket_design"], "final_executable_ticket_design_decision") or "missing_non_submitting_executable_ticket_design"
    design_approved = summary_value(inputs["execution_design_approval_record"], "execution_design_approved") == "True"
    ticket_design_present = ticket_design_decision == "NON_SUBMITTING_EXECUTABLE_TICKET_DESIGNED_NO_ORDER_VALUES"
    return {"ready": design_approved and ticket_design_present, "design_approved": design_approved, "ticket_design_present": ticket_design_present, "design_decision": design_decision, "ticket_design_decision": ticket_design_decision}


def flags(recorded: bool) -> dict[str, bool]:
    updated = dict(BASE_FLAGS)
    updated["ticket_value_discussion_approved"] = recorded
    updated["ticket_value_approval_recorded"] = recorded
    return updated


def common_summary(inputs: dict[str, list[dict[str, str]]], status: str, decision: str, discussion_approved: str, approval_recorded: str, readiness_ready: str, next_step: str) -> list[dict[str, Any]]:
    recorded = discussion_approved == "True"
    status_key = "final_ticket_values_record_status" if recorded else ("final_ticket_values_wording_status" if "WORDING" in decision else "final_ticket_values_readiness_status")
    decision_key = "final_ticket_values_record_decision" if recorded else ("final_ticket_values_wording_decision" if "WORDING" in decision else "final_ticket_values_readiness_decision")
    data = [
        (status_key, status, "Saved-output ticket-values checkpoint."),
        (decision_key, decision, "Discussion/design only; no values or orders approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_phrase", APPROVAL_PHRASE, "Narrow phrase for ticket-value discussion only."),
        ("ticket_value_discussion_ready", readiness_ready, "Ready to discuss future non-executable placeholders only."),
        ("ticket_value_discussion_approved", discussion_approved, "True only for discussion/design approval, not value approval."),
        ("ticket_value_approval_recorded", approval_recorded, "True only for the record command."),
        ("ticket_values_approved", "False", "No actual values are approved."),
        ("execution_design_approval_record_decision", summary_value(inputs["execution_design_approval_record"], "final_execution_design_record_decision") or "missing_execution_design_approval_record", "Saved design approval context."),
        ("non_submitting_executable_ticket_design_decision", summary_value(inputs["non_submitting_executable_ticket_design"], "final_executable_ticket_design_decision") or "missing_non_submitting_executable_ticket_design", "Saved ticket design context."),
        ("manual_ticket_value_design_decision", summary_value(inputs["manual_ticket_value_design"], "final_ticket_value_design_decision") or "missing_manual_ticket_value_design", "Prior ticket-value design context."),
        ("go_no_go_decision", summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard", "Saved go/no-go context."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, price, account, or broker field is populated."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "ticket_values_not_approved", "Discussion approval does not approve values."),
        ("recommended_next_step", next_step, "Next step remains non-executable placeholders only."),
    ]
    return [summary_row(name, value, details, recorded) for name, value, details in data]


def common_blockers(name: str, details: str, next_step: str, recorded: bool) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step, recorded),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", recorded),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", recorded),
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def evidence_for(inputs: dict[str, list[dict[str, str]]], recorded: bool) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", recorded) for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", recorded))
    return rows


def row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, recorded: bool) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(recorded)}


def summary_row(name: str, value: str, details: str, recorded: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(recorded)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, recorded: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(recorded)}


def evidence_row(name: str, value: str, details: str, recorded: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(recorded)}


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
        f"ticket_value_discussion_approved: {summary_value(rows, 'ticket_value_discussion_approved')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def lines(title: str, rows: list[dict[str, Any]], report_path: Path, status_key: str, decision_key: str) -> list[str]:
    return [
        title,
        f"{status_key}={summary_value(rows, status_key)}",
        f"{decision_key}={summary_value(rows, decision_key)}",
        f"ticket_value_discussion_approved={summary_value(rows, 'ticket_value_discussion_approved')}",
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
