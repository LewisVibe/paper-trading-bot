"""Ticket-value proposal approval checkpoint for the volatility seed.

This records wording and approval for drafting proposed ticket values in a
future report. It does not populate side, quantity, order type, time-in-force,
price, account references, broker identifiers, or any executable instruction.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve drafting proposed ticket values for review only; do not create or submit orders."
WORDING_STATUS = "vol_targeted_growth_ticket_value_proposal_approval_wording_manual_review_required"
WORDING_DECISION = "TICKET_VALUE_PROPOSAL_APPROVAL_WORDING_DEFINED_NOT_APPROVED"
RECORD_STATUS = "vol_targeted_growth_ticket_value_proposal_approval_recorded_manual_review_required"
RECORD_DECISION = "TICKET_VALUE_PROPOSAL_DISCUSSION_APPROVED_NO_VALUES_POPULATED"
NEXT_STEP = "draft_proposed_ticket_values_as_non_executable_review_only"

WORDING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_ticket_value_proposal_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_ticket_value_proposal_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_ticket_value_proposal_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_ticket_value_proposal_approval_wording_evidence.csv"),
}

RECORD_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_ticket_value_proposal_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_ticket_value_proposal_approval_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_ticket_value_proposal_approval_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_ticket_value_proposal_approval_record_evidence.csv"),
}

INPUT_FILES = {
    "ticket_values_approval_record": Path("data/vol_targeted_growth_ticket_values_approval_record_summary.csv"),
    "ticket_value_placeholders": Path("data/vol_targeted_growth_ticket_value_placeholders_summary.csv"),
    "ticket_value_quality_gate": Path("data/vol_targeted_growth_ticket_value_quality_gate_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "ticket_value_proposal_approval_recorded": False,
    "ticket_value_proposal_discussion_approved": False,
    "ticket_values_approved": False,
    "proposed_ticket_values_created": False,
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
class TicketValueProposalApprovalResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_ticket_value_proposal_approval_wording(root_dir: Path | str = ".") -> TicketValueProposalApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        report_row("proposal_approval_phrase", "wording_defined_not_recorded", "critical", APPROVAL_PHRASE, "This approves only future proposed values for review.", "wait_for_explicit_proposal_approval", False),
        report_row("order_value_boundary", "values_not_populated", "critical", "order_values_populated=false", "No side, quantity, order type, time-in-force, or price is populated.", "keep_values_blank", False),
    ]
    summary_rows = common_summary(inputs, WORDING_STATUS, WORDING_DECISION, False, "wait_for_explicit_proposal_approval")
    blocker_rows = common_blockers("proposal_approval_not_recorded", "ticket_value_proposal_approval_recorded=false", "wait_for_explicit_proposal_approval", False)
    evidence_rows = evidence_rows_for(inputs, False) + [evidence_row("future_approval_phrase", APPROVAL_PHRASE, "Proposal approval wording only; not order approval.", False)]
    paths = write_all(root, WORDING_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return TicketValueProposalApprovalResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, summary_lines("Ticket-value proposal approval wording complete. No values approved.", summary_rows, paths["report"], "final_ticket_value_proposal_wording_status", "final_ticket_value_proposal_wording_decision"))


def show_vol_targeted_growth_ticket_value_proposal_approval_wording(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / WORDING_OUTPUTS["summary"], "Volatility-targeted ticket-value proposal approval wording saved display. No values approved.", "final_ticket_value_proposal_wording_status", "final_ticket_value_proposal_wording_decision")


def generate_vol_targeted_growth_ticket_value_proposal_approval_record(root_dir: Path | str = ".") -> TicketValueProposalApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        report_row("proposal_approval_record", "proposal_discussion_approved", "critical", APPROVAL_PHRASE, "Approval is limited to drafting proposed values for review only.", NEXT_STEP, True),
        report_row("order_value_boundary", "values_not_populated", "critical", "ticket_values_approved=false; order_values_populated=false", "Actual ticket values remain unapproved and blank.", NEXT_STEP, True),
        report_row("execution_boundary", "execution_not_approved", "critical", "orders_submitted=false; execution_approved=false", "Execution approval remains separate and false.", NEXT_STEP, True),
    ]
    summary_rows = common_summary(inputs, RECORD_STATUS, RECORD_DECISION, True, NEXT_STEP)
    blocker_rows = common_blockers("ticket_values_not_populated_or_approved", "ticket_values_approved=false; order_values_populated=false", NEXT_STEP, True)
    evidence_rows = evidence_rows_for(inputs, True) + [evidence_row("recorded_approval_phrase", APPROVAL_PHRASE, "Proposal discussion approval recorded; no order values populated.", True)]
    paths = write_all(root, RECORD_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return TicketValueProposalApprovalResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, summary_lines("Ticket-value proposal approval record complete. Proposal only; no values or execution approved.", summary_rows, paths["report"], "final_ticket_value_proposal_record_status", "final_ticket_value_proposal_record_decision"))


def show_vol_targeted_growth_ticket_value_proposal_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / RECORD_OUTPUTS["summary"], "Volatility-targeted ticket-value proposal approval record saved display. Proposal only; no values approved.", "final_ticket_value_proposal_record_status", "final_ticket_value_proposal_record_decision")


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def flags(recorded: bool) -> dict[str, bool]:
    updated = dict(SAFETY_FLAGS)
    updated["ticket_value_proposal_approval_recorded"] = recorded
    updated["ticket_value_proposal_discussion_approved"] = recorded
    return updated


def common_summary(inputs: dict[str, list[dict[str, str]]], status: str, decision: str, recorded: bool, next_step: str) -> list[dict[str, Any]]:
    status_key = "final_ticket_value_proposal_record_status" if recorded else "final_ticket_value_proposal_wording_status"
    decision_key = "final_ticket_value_proposal_record_decision" if recorded else "final_ticket_value_proposal_wording_decision"
    data = [
        (status_key, status, "Saved-output proposal approval checkpoint."),
        (decision_key, decision, "Proposal-only approval; no values or orders approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_phrase", APPROVAL_PHRASE, "Narrow proposal-review phrase."),
        ("ticket_value_proposal_discussion_approved", str(recorded), "True only for drafting proposed values next, not execution."),
        ("ticket_value_proposal_approval_recorded", str(recorded), "True only for the record command."),
        ("ticket_values_approved", "False", "No actual ticket values are approved."),
        ("proposed_ticket_values_created", "False", "No proposed values are created by this checkpoint."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, or price is populated."),
        ("ticket_value_discussion_record_decision", summary_value(inputs["ticket_values_approval_record"], "final_ticket_values_record_decision") or "missing_ticket_values_approval_record", "Prior discussion approval context."),
        ("placeholder_decision", summary_value(inputs["ticket_value_placeholders"], "final_ticket_value_placeholder_decision") or "missing_ticket_value_placeholders", "Saved placeholder context."),
        ("quality_gate_decision", summary_value(inputs["ticket_value_quality_gate"], "final_ticket_value_quality_gate_decision") or "missing_ticket_value_quality_gate", "Saved placeholder quality context."),
        ("go_no_go_decision", summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard", "Saved go/no-go context."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "ticket_values_not_populated_or_approved", "Proposal approval does not populate values."),
        ("recommended_next_step", next_step, "Next step remains non-executable proposed values only."),
    ]
    return [summary_row(name, value, details, recorded) for name, value, details in data]


def common_blockers(name: str, details: str, next_step: str, recorded: bool) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step, recorded),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", recorded),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", recorded),
    ]


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]], recorded: bool) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", recorded) for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", recorded))
    return rows


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, recorded: bool) -> dict[str, Any]:
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
        f"ticket_value_proposal_discussion_approved: {summary_value(rows, 'ticket_value_proposal_discussion_approved')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"proposed_ticket_values_created: {summary_value(rows, 'proposed_ticket_values_created')}",
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
        f"ticket_value_proposal_discussion_approved={summary_value(rows, 'ticket_value_proposal_discussion_approved')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"proposed_ticket_values_created={summary_value(rows, 'proposed_ticket_values_created')}",
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
