"""Saved-output closeout record for approval_criteria_not_approval blocker."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve closing the approval_criteria_not_approval blocker only."
FINAL_STATUS = "vol_targeted_growth_approval_criteria_closeout_recorded_manual_review_required"
FINAL_DECISION = "APPROVAL_CRITERIA_NOT_APPROVAL_BLOCKER_CLOSED_ONLY"
NEXT_STEP = "refresh_execution_blocker_chain_after_third_criteria_closeout"
REMAINING_BLOCKERS = "ticket_values_not_approved;executable_ticket_prerequisites_not_met"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_record.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_evidence.csv"),
}

INPUT_FILES = {
    "approval_wording": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_approval_wording_summary.csv"),
    "criteria_resolution_plan_closeout_record": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_record_summary.csv"),
    "approval_criteria_candidate": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_not_approval_closeout_candidate_review_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "criteria_source_reviewed_closed": True,
    "criteria_resolution_plan_open_closed": True,
    "approval_criteria_not_approval_closed": True,
    "single_blocker_closeout_only": True,
    "other_blockers_closed": False,
    "executable_ticket_approval_recorded": False,
    "approval_readiness_changed": False,
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
class ApprovalCriteriaCloseoutRecordResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_approval_criteria_closeout_record(root_dir: Path | str = ".") -> ApprovalCriteriaCloseoutRecordResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(inputs, report_rows)
    blocker_rows = build_blocker_rows(inputs)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return ApprovalCriteriaCloseoutRecordResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, build_summary_lines(summary_rows, output_paths))


def show_vol_targeted_growth_approval_criteria_closeout_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted approval-criteria closeout record is missing.",
            "Run `python bot.py --vol-targeted-growth-approval-criteria-closeout-record` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted approval-criteria closeout record saved display. Report only; no execution approved.",
        f"final_closeout_record_status: {summary_value(rows, 'final_closeout_record_status')}",
        f"final_closeout_record_decision: {summary_value(rows, 'final_closeout_record_decision')}",
        f"closed_blocker: {summary_value(rows, 'closed_blocker')}",
        f"closed_blocker_count: {summary_value(rows, 'closed_blocker_count')}",
        f"remaining_known_blockers: {summary_value(rows, 'remaining_known_blockers')}",
        f"approval_phrase_used: {summary_value(rows, 'approval_phrase_used')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "criteria_source_reviewed_closed=true; criteria_resolution_plan_open_closed=true; approval_criteria_not_approval_closed=true; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    go_no_go = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard"
    return [
        row("approval_criteria_not_approval_closeout", "closed_for_approval_criteria_only", "high", APPROVAL_PHRASE, "This closes the approval-criteria blocker only.", NEXT_STEP),
        row("remaining_blockers", "manual_review_required", "critical", REMAINING_BLOCKERS, "Ticket values and executable-ticket prerequisites still block any ticket or order.", "continue_without_ticket_values_or_execution"),
        row("execution_boundary", "execution_blocked", "critical", go_no_go, "Closing this blocker is not executable-ticket approval.", "keep_go_no_go_dashboard_no_go"),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_closeout_record_status", FINAL_STATUS, "Single-blocker closeout record is saved-output/manual-review only."),
        ("final_closeout_record_decision", FINAL_DECISION, "Only approval_criteria_not_approval is closed."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("closed_blocker", "approval_criteria_not_approval", "The blocker closed by this record."),
        ("closed_blocker_count", "3", "Three blockers are now closed when combined with previous closeouts."),
        ("criteria_source_reviewed_closed", "True", "Prior criteria-source closeout is recognised."),
        ("criteria_resolution_plan_open_closed", "True", "Prior resolution-plan closeout is recognised."),
        ("approval_criteria_not_approval_closed", "True", "This closeout record closes the approval-criteria blocker."),
        ("remaining_known_blockers", REMAINING_BLOCKERS, "Known blockers still preventing execution-ticket approval."),
        ("approval_phrase_used", APPROVAL_PHRASE, "User-approved closeout scope for this one blocker."),
        ("approval_wording_decision", summary_value(inputs["approval_wording"], "final_approval_wording_decision") or "missing_approval_criteria_closeout_wording", "Saved approval wording decision."),
        ("criteria_resolution_plan_closeout_decision", summary_value(inputs["criteria_resolution_plan_closeout_record"], "final_closeout_record_decision") or "missing_criteria_resolution_plan_closeout_record", "Prior closeout context."),
        ("approval_criteria_candidate_decision", summary_value(inputs["approval_criteria_candidate"], "final_candidate_review_decision") or "missing_approval_criteria_candidate", "Saved candidate review decision."),
        ("go_no_go_decision", summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard", "Saved go/no-go dashboard decision."),
        ("closeout_record_row_count", str(len(report_rows)), "Saved report row count."),
        ("largest_blocker", "ticket_values_not_approved", "Primary remaining blocker."),
        ("recommended_next_step", NEXT_STEP, "Refresh the report-only blocker chain after this third closeout."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("ticket_values_not_approved", "blocked", "critical", "No side, quantity, order type, or time-in-force is approved.", "do_not_populate_ticket_values"),
        blocker_row("executable_ticket_not_created", "blocked", "critical", "executable_ticket_created=false", "do_not_create_executable_ticket"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
    ]
    for name, input_rows in inputs.items():
        if not input_rows:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("approval_phrase_used", APPROVAL_PHRASE, "Scope is exactly one blocker."))
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, order, alert, SQLite, or scheduling path is used."))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Executable-ticket approval-criteria closeout record complete. Report only; third blocker closed.",
        f"final_closeout_record_status={summary_value(summary_rows, 'final_closeout_record_status')}",
        f"final_closeout_record_decision={summary_value(summary_rows, 'final_closeout_record_decision')}",
        f"closed_blocker={summary_value(summary_rows, 'closed_blocker')}",
        f"closed_blocker_count={summary_value(summary_rows, 'closed_blocker_count')}",
        f"criteria_source_reviewed_closed={summary_value(summary_rows, 'criteria_source_reviewed_closed')}",
        f"criteria_resolution_plan_open_closed={summary_value(summary_rows, 'criteria_resolution_plan_open_closed')}",
        f"approval_criteria_not_approval_closed={summary_value(summary_rows, 'approval_criteria_not_approval_closed')}",
        f"remaining_known_blockers={summary_value(summary_rows, 'remaining_known_blockers')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "criteria_source_reviewed_closed=true; criteria_resolution_plan_open_closed=true; approval_criteria_not_approval_closed=true; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for item in rows:
        if item.get("summary_name") == key:
            return str(item.get("summary_value", "")).strip()
    return ""
