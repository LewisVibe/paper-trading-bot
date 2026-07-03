"""Draft ticket-value approval wording and record for the volatility seed.

These saved-output checkpoints allow a later step to populate review-only
draft ticket values. They do not populate side, quantity, order type,
time-in-force, broker fields, account references, or any executable order
instruction.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve populating draft ticket values for the active volatility seed only; do not create or submit orders."
WORDING_STATUS = "vol_targeted_growth_draft_ticket_value_approval_wording_manual_review_required"
WORDING_DECISION = "TICKET_VALUE_APPROVAL_WORDING_DEFINED_NOT_APPROVED"
RECORD_STATUS = "vol_targeted_growth_draft_ticket_value_approval_recorded_manual_review_required"
RECORD_DECISION = "TICKET_VALUE_APPROVAL_RECORDED_NO_ORDER_VALUES"
NEXT_STEP = "populate_review_only_draft_ticket_values_without_execution"

WORDING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_draft_ticket_value_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_draft_ticket_value_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_draft_ticket_value_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_draft_ticket_value_approval_wording_evidence.csv"),
}

RECORD_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_draft_ticket_value_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_draft_ticket_value_approval_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_draft_ticket_value_approval_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_draft_ticket_value_approval_record_evidence.csv"),
}

INPUT_FILES = {
    "approval_readiness": Path("data/vol_targeted_growth_draft_ticket_value_approval_readiness_summary.csv"),
    "ticket_draft": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_summary.csv"),
    "ticket_draft_quality_gate": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

BASE_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "ticket_value_approval_wording_defined": False,
    "ticket_value_population_approved": False,
    "ticket_value_approval_recorded": False,
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
class DraftTicketValueApprovalResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_draft_ticket_value_approval_wording(root_dir: Path | str = ".") -> DraftTicketValueApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        report_row(
            "approval_wording",
            "approval_wording_defined_not_recorded",
            "critical",
            APPROVAL_PHRASE,
            "This phrase is only permission to populate review-only draft values in a later step.",
            "wait_for_explicit_ticket_value_approval_record",
            wording_defined=True,
            population_approved=False,
        ),
        report_row(
            "order_value_boundary",
            "values_not_populated",
            "critical",
            "ticket_values_approved=false; order_values_populated=false",
            "The wording is not a side, quantity, order type, price, account, broker, or submit instruction.",
            "keep_order_values_blank_until_separate_population_step",
            wording_defined=True,
            population_approved=False,
        ),
    ]
    summary_rows = build_summary_rows(inputs, WORDING_STATUS, WORDING_DECISION, wording_defined=True, population_approved=False)
    blocker_rows = build_blocker_rows("ticket_value_approval_not_recorded", "The wording is defined but not recorded as approval.", "wait_for_explicit_ticket_value_approval_record", wording_defined=True, population_approved=False)
    evidence_rows = build_evidence_rows(inputs, wording_defined=True, population_approved=False)
    paths = write_all(root, WORDING_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return DraftTicketValueApprovalResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, summary_lines("Draft ticket-value approval wording complete. No values or execution approved.", summary_rows, paths["report"], "final_draft_ticket_value_approval_wording_status", "final_draft_ticket_value_approval_wording_decision"))


def show_vol_targeted_growth_draft_ticket_value_approval_wording(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / WORDING_OUTPUTS["summary"], "Volatility-targeted draft ticket-value approval wording saved display. No approval recorded.", "final_draft_ticket_value_approval_wording_status", "final_draft_ticket_value_approval_wording_decision")


def generate_vol_targeted_growth_draft_ticket_value_approval_record(root_dir: Path | str = ".") -> DraftTicketValueApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        report_row(
            "approval_record",
            "ticket_value_population_approval_recorded",
            "critical",
            APPROVAL_PHRASE,
            "Approval is limited to a later review-only value population step.",
            NEXT_STEP,
            wording_defined=True,
            population_approved=True,
        ),
        report_row(
            "order_value_boundary",
            "values_not_populated",
            "critical",
            "ticket_values_approved=false; order_values_populated=false",
            "No concrete ticket values exist yet and no order can be submitted from this record.",
            NEXT_STEP,
            wording_defined=True,
            population_approved=True,
        ),
        report_row(
            "execution_boundary",
            "execution_not_approved",
            "critical",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
            "Execution approval remains a separate future decision and is false here.",
            "keep_execution_blocked",
            wording_defined=True,
            population_approved=True,
        ),
    ]
    summary_rows = build_summary_rows(inputs, RECORD_STATUS, RECORD_DECISION, wording_defined=True, population_approved=True)
    blocker_rows = build_blocker_rows("ticket_values_not_populated_or_approved", "Approval permits a later draft-value population step only; no values are present.", NEXT_STEP, wording_defined=True, population_approved=True)
    evidence_rows = build_evidence_rows(inputs, wording_defined=True, population_approved=True)
    paths = write_all(root, RECORD_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return DraftTicketValueApprovalResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, summary_lines("Draft ticket-value approval record complete. Values and execution remain blocked.", summary_rows, paths["report"], "final_draft_ticket_value_approval_record_status", "final_draft_ticket_value_approval_record_decision"))


def show_vol_targeted_growth_draft_ticket_value_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / RECORD_OUTPUTS["summary"], "Volatility-targeted draft ticket-value approval record saved display. Values and execution remain blocked.", "final_draft_ticket_value_approval_record_status", "final_draft_ticket_value_approval_record_decision")


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], status: str, decision: str, *, wording_defined: bool, population_approved: bool) -> list[dict[str, Any]]:
    data = [
        (status_key(decision), status, "Saved-output draft ticket-value approval checkpoint."),
        (decision_key(decision), decision, "Approval boundary for draft value population only."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_phrase", APPROVAL_PHRASE, "Narrow approval wording."),
        ("approval_readiness_decision", summary_value(inputs["approval_readiness"], "final_ticket_value_approval_readiness_decision") or "missing_approval_readiness", "Prior saved readiness context."),
        ("ticket_draft_decision", summary_value(inputs["ticket_draft"], "final_ticket_draft_decision") or "missing_ticket_draft", "Saved non-submitting ticket draft context."),
        ("ticket_draft_quality_gate_decision", summary_value(inputs["ticket_draft_quality_gate"], "final_ticket_draft_quality_decision") or "missing_ticket_draft_quality_gate", "Saved quality gate context."),
        ("go_no_go_decision", summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard", "Saved dashboard context."),
        ("ticket_value_approval_wording_defined", str(wording_defined), "True when the wording checkpoint exists."),
        ("ticket_value_approval_recorded", str(population_approved), "True only when the approval record checkpoint is generated."),
        ("ticket_value_population_approved", str(population_approved), "True means a later review-only draft-value population step may proceed."),
        ("ticket_values_approved", "False", "No concrete values are approved by this checkpoint."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, price, account, or broker field is populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("ticket_instance_created", "False", "No ticket instance exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_created", "False", "No orders are created."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "ticket_values_not_populated_or_approved", "Approval record is not an order-values checkpoint."),
        ("recommended_next_step", NEXT_STEP if population_approved else "wait_for_explicit_ticket_value_approval_record", "Next step remains non-executable and review-only."),
    ]
    return [summary_row(name, value, details, wording_defined, population_approved) for name, value, details in data]


def status_key(decision: str) -> str:
    if decision == RECORD_DECISION:
        return "final_draft_ticket_value_approval_record_status"
    return "final_draft_ticket_value_approval_wording_status"


def decision_key(decision: str) -> str:
    if decision == RECORD_DECISION:
        return "final_draft_ticket_value_approval_record_decision"
    return "final_draft_ticket_value_approval_wording_decision"


def build_blocker_rows(name: str, details: str, next_step: str, *, wording_defined: bool, population_approved: bool) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step, wording_defined, population_approved),
        blocker_row("ticket_values_not_approved", "blocked", "critical", "ticket_values_approved=false", "keep_values_unapproved_until_review_only_population_step", wording_defined, population_approved),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", wording_defined, population_approved),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", wording_defined, population_approved),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], *, wording_defined: bool, population_approved: bool) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", wording_defined, population_approved)
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("approval_phrase", APPROVAL_PHRASE, "Narrow approval phrase; not an order instruction.", wording_defined, population_approved))
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", wording_defined, population_approved))
    return rows


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def flags(wording_defined: bool, population_approved: bool) -> dict[str, bool]:
    updated = dict(BASE_FLAGS)
    updated["ticket_value_approval_wording_defined"] = wording_defined
    updated["ticket_value_population_approved"] = population_approved
    updated["ticket_value_approval_recorded"] = population_approved
    return updated


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, *, wording_defined: bool, population_approved: bool) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(wording_defined, population_approved)}


def summary_row(name: str, value: str, details: str, wording_defined: bool, population_approved: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(wording_defined, population_approved)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, wording_defined: bool, population_approved: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(wording_defined, population_approved)}


def evidence_row(name: str, value: str, details: str, wording_defined: bool, population_approved: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(wording_defined, population_approved)}


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
        f"ticket_value_approval_wording_defined: {summary_value(rows, 'ticket_value_approval_wording_defined')}",
        f"ticket_value_population_approved: {summary_value(rows, 'ticket_value_population_approved')}",
        f"ticket_value_approval_recorded: {summary_value(rows, 'ticket_value_approval_recorded')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: approval is limited to later review-only draft value population; this does not create orders.",
    ]


def summary_lines(title: str, rows: list[dict[str, Any]], report_path: Path, status_name: str, decision_name: str) -> list[str]:
    return [
        title,
        f"{status_name}={summary_value(rows, status_name)}",
        f"{decision_name}={summary_value(rows, decision_name)}",
        f"ticket_value_approval_wording_defined={summary_value(rows, 'ticket_value_approval_wording_defined')}",
        f"ticket_value_population_approved={summary_value(rows, 'ticket_value_population_approved')}",
        f"ticket_value_approval_recorded={summary_value(rows, 'ticket_value_approval_recorded')}",
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
