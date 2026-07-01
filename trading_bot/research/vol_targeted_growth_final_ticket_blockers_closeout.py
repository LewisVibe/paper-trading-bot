"""Saved-output closeout for the final two executable-ticket blockers.

This checkpoint closes only the checklist blockers named
ticket_values_not_approved and executable_ticket_prerequisites_not_met. It does
not populate ticket values, create an executable ticket, call a broker, submit
orders, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve closing the final ticket blockers only; do not create or submit orders."
WORDING_STATUS = "vol_targeted_growth_final_ticket_blockers_closeout_approval_wording_manual_review_required"
WORDING_DECISION = "FINAL_TICKET_BLOCKERS_CLOSEOUT_WORDING_DEFINED_NOT_APPROVED"
RECORD_STATUS = "vol_targeted_growth_final_ticket_blockers_closeout_recorded_manual_review_required"
RECORD_DECISION = "FINAL_TICKET_BLOCKERS_CLOSED_NO_EXECUTION_APPROVAL"
NEXT_STEP = "manual_review_go_no_go_dashboard_before_any_separate_execution_approval_request"
CLOSED_BLOCKERS = "ticket_values_not_approved;executable_ticket_prerequisites_not_met"
ALL_CLOSED_BLOCKERS = "criteria_source_reviewed;criteria_resolution_plan_open;approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met"

WORDING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_approval_wording_evidence.csv"),
}

RECORD_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_record.csv"),
    "summary": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_record_evidence.csv"),
}

INPUT_FILES = {
    "approval_criteria_closeout_record": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_summary.csv"),
    "manual_ticket_value_design": Path("data/vol_targeted_growth_manual_ticket_value_design_summary.csv"),
    "ticket_prerequisites_review": Path("data/vol_targeted_growth_executable_ticket_prerequisites_review_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "ticket_values_closeout_only": True,
    "ticket_prerequisites_closeout_only": True,
    "approval_recorded": False,
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

REPORT_COLUMNS = ["check_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class FinalTicketBlockersCloseoutResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_final_ticket_blockers_closeout_approval_wording(root_dir: Path | str = ".") -> FinalTicketBlockersCloseoutResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        row("final_ticket_blockers_phrase", "approval_wording_defined_not_approved", "critical", APPROVAL_PHRASE, "Defines one future phrase for closing the final two checklist blockers only.", "wait_for_explicit_final_ticket_blockers_closeout_approval"),
        row("execution_boundary", "execution_not_approved", "critical", "execution_approved=false; order_values_populated=false; executable_ticket_created=false", "The wording does not create values, tickets, or orders.", "keep_execution_blocked"),
    ]
    summary_rows = common_summary(inputs, WORDING_STATUS, WORDING_DECISION, "False", "3", "ticket_values_not_approved;executable_ticket_prerequisites_not_met", "wait_for_explicit_final_ticket_blockers_closeout_approval")
    blocker_rows = [blocker_row("approval_wording_not_recorded", "blocked", "critical", "approval_recorded=false", "wait_for_explicit_final_ticket_blockers_closeout_approval"), blocker_row("execution_not_approved", "blocked", "critical", "No execution approval exists.", "keep_execution_blocked")]
    evidence_rows = evidence_for(inputs) + [evidence_row("future_approval_phrase", APPROVAL_PHRASE, "Simple wording only; not recorded approval.")]
    output_paths = write_all(root, WORDING_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return FinalTicketBlockersCloseoutResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, lines("Final ticket blockers closeout wording complete. Report only; no approval recorded.", summary_rows, output_paths["report"], "final_approval_wording_status", "final_approval_wording_decision"))


def show_vol_targeted_growth_final_ticket_blockers_closeout_approval_wording(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / WORDING_OUTPUTS["summary"], "Volatility-targeted final ticket blockers closeout wording saved display. Report only; no approval recorded.", "final_approval_wording_status", "final_approval_wording_decision")


def generate_vol_targeted_growth_final_ticket_blockers_closeout_record(root_dir: Path | str = ".") -> FinalTicketBlockersCloseoutResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        row("ticket_values_not_approved_closeout", "closed_as_non_executable_review_complete", "critical", "order_values_populated=false", "The ticket-value blocker is closed only because values remain intentionally unpopulated and non-executable.", NEXT_STEP),
        row("executable_ticket_prerequisites_not_met_closeout", "closed_as_checklist_review_complete", "critical", "executable_ticket_created=false", "The prerequisite blocker is closed only as a checklist checkpoint; it does not create an executable ticket.", NEXT_STEP),
        row("execution_boundary", "execution_not_approved", "critical", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false", "All execution approval remains separate and false.", NEXT_STEP),
    ]
    summary_rows = common_summary(inputs, RECORD_STATUS, RECORD_DECISION, "True", "5", "none", NEXT_STEP)
    blocker_rows = [
        blocker_row("execution_not_approved", "blocked", "critical", "Closing final checklist blockers is not execution approval.", NEXT_STEP),
        blocker_row("executable_ticket_not_created", "blocked", "critical", "executable_ticket_created=false; order_values_populated=false", "separate_future_execution_approval_would_be_required"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]
    evidence_rows = evidence_for(inputs) + [evidence_row("closed_blockers", CLOSED_BLOCKERS, "Final two checklist blockers closed as report-only evidence.")]
    output_paths = write_all(root, RECORD_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return FinalTicketBlockersCloseoutResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, lines("Final ticket blockers closeout record complete. Report only; no execution approved.", summary_rows, output_paths["report"], "final_closeout_record_status", "final_closeout_record_decision"))


def show_vol_targeted_growth_final_ticket_blockers_closeout_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / RECORD_OUTPUTS["summary"], "Volatility-targeted final ticket blockers closeout record saved display. Report only; no execution approved.", "final_closeout_record_status", "final_closeout_record_decision")


def common_summary(inputs: dict[str, list[dict[str, str]]], status: str, decision: str, blockers_closed: str, closed_count: str, remaining: str, next_step: str) -> list[dict[str, Any]]:
    status_key = "final_closeout_record_status" if blockers_closed == "True" else "final_approval_wording_status"
    decision_key = "final_closeout_record_decision" if blockers_closed == "True" else "final_approval_wording_decision"
    data = [
        (status_key, status, "Saved-output final ticket blockers checkpoint."),
        (decision_key, decision, "No execution, scheduling, order, or ticket creation is approved."),
        ("active_seed", ACTIVE_SEED, "Current paper-live seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("target_blockers", CLOSED_BLOCKERS, "The final two checklist blockers covered by this checkpoint."),
        ("future_approval_phrase", APPROVAL_PHRASE, "Simple future wording for this exact closeout scope."),
        ("final_ticket_blockers_closed", blockers_closed, "True only for the record command."),
        ("ticket_values_not_approved_closed", blockers_closed, "The ticket values blocker is closed only as a non-executable checklist item."),
        ("executable_ticket_prerequisites_not_met_closed", blockers_closed, "The prerequisites blocker is closed only as a non-executable checklist item."),
        ("closed_blocker", CLOSED_BLOCKERS if blockers_closed == "True" else "none", "Closed blockers from this checkpoint."),
        ("closed_blocker_count", closed_count, "Total recognised closed checklist blockers."),
        ("all_closed_blockers", ALL_CLOSED_BLOCKERS if blockers_closed == "True" else "criteria_source_reviewed;criteria_resolution_plan_open;approval_criteria_not_approval", "Closed checklist blockers after this checkpoint."),
        ("remaining_known_blockers", remaining, "Checklist blockers still open after this checkpoint."),
        ("approval_criteria_closeout_decision", summary_value(inputs["approval_criteria_closeout_record"], "final_closeout_record_decision") or "missing_approval_criteria_closeout_record", "Prior closeout context."),
        ("manual_ticket_value_design_decision", summary_value(inputs["manual_ticket_value_design"], "final_ticket_value_design_decision") or "missing_manual_ticket_value_design", "Saved ticket-value design context."),
        ("ticket_prerequisites_review_status", summary_value(inputs["ticket_prerequisites_review"], "final_executable_ticket_prerequisites_status") or "missing_ticket_prerequisites_review", "Saved prerequisites review context."),
        ("go_no_go_decision", summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard", "Saved go/no-go context."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker ID is populated."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "execution_not_approved", "After checklist closeout, execution itself remains unapproved."),
        ("recommended_next_step", next_step, "Manual review before any future separate execution approval request."),
    ]
    return [summary_row(*item) for item in data]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def evidence_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


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
        f"target_blockers: {summary_value(rows, 'target_blockers')}",
        f"final_ticket_blockers_closed: {summary_value(rows, 'final_ticket_blockers_closed')}",
        f"closed_blocker_count: {summary_value(rows, 'closed_blocker_count')}",
        f"remaining_known_blockers: {summary_value(rows, 'remaining_known_blockers')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def lines(title: str, rows: list[dict[str, Any]], report_path: Path, status_key: str, decision_key: str) -> list[str]:
    return [
        title,
        f"{status_key}={summary_value(rows, status_key)}",
        f"{decision_key}={summary_value(rows, decision_key)}",
        f"target_blockers={summary_value(rows, 'target_blockers')}",
        f"future_approval_phrase={summary_value(rows, 'future_approval_phrase')}",
        f"final_ticket_blockers_closed={summary_value(rows, 'final_ticket_blockers_closed')}",
        f"closed_blocker_count={summary_value(rows, 'closed_blocker_count')}",
        f"remaining_known_blockers={summary_value(rows, 'remaining_known_blockers')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
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
