"""Saved-output readiness checkpoint for requesting execution approval later.

This report can recognise that the paper-live checklist blockers are closed,
but it does not request approval, record approval, create ticket values, create
an executable ticket, call a broker, submit orders, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
FINAL_STATUS = "vol_targeted_growth_execution_approval_request_readiness_manual_review_required"
FINAL_DECISION = "READY_FOR_SEPARATE_EXECUTION_APPROVAL_REQUEST_NOT_APPROVED"
NEXT_STEP = "ask_user_for_separate_explicit_execution_approval_only_if_they_want_to_continue"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_execution_approval_request_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_execution_approval_request_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_execution_approval_request_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_execution_approval_request_readiness_evidence.csv"),
}

INPUT_FILES = {
    "final_ticket_blockers_closeout": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_record_summary.csv"),
    "execution_blocker_rollup": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv"),
    "executable_ticket_gap_list": Path("data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
    "manual_execution_design_approval_gate": Path("data/vol_targeted_growth_manual_execution_design_approval_gate_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "checklist_readiness_only": True,
    "approval_request_ready": True,
    "approval_requested": False,
    "approval_recorded": False,
    "manual_execution_design_approved": False,
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
class ExecutionApprovalRequestReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_execution_approval_request_readiness(root_dir: Path | str = ".") -> ExecutionApprovalRequestReadinessResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_report_rows(context)
    summary_rows = build_summary_rows(context, report_rows)
    blocker_rows = build_blocker_rows(context, inputs)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return ExecutionApprovalRequestReadinessResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, build_summary_lines(summary_rows, output_paths["report"]))


def show_vol_targeted_growth_execution_approval_request_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted execution approval request readiness is missing.",
            "Run `python bot.py --vol-targeted-growth-execution-approval-request-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted execution approval request readiness saved display. Report only; no approval requested.",
        f"final_readiness_status: {summary_value(rows, 'final_readiness_status')}",
        f"final_readiness_decision: {summary_value(rows, 'final_readiness_decision')}",
        f"checklist_blockers_closed: {summary_value(rows, 'checklist_blockers_closed')}",
        f"approval_request_ready: {summary_value(rows, 'approval_request_ready')}",
        f"approval_requested: {summary_value(rows, 'approval_requested')}",
        f"approval_recorded: {summary_value(rows, 'approval_recorded')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "final_ticket_blockers_decision": summary_value(inputs["final_ticket_blockers_closeout"], "final_closeout_record_decision") or "missing_final_ticket_blockers_closeout",
        "closed_blocker_count": summary_value(inputs["execution_blocker_rollup"], "closed_blocker_count") or "missing_closed_blocker_count",
        "remaining_known_blockers": summary_value(inputs["execution_blocker_rollup"], "remaining_known_blockers_after_closeout") or "missing_remaining_known_blockers",
        "rollup_largest_blocker": summary_value(inputs["execution_blocker_rollup"], "largest_blocker") or "missing_rollup_largest_blocker",
        "gap_largest_gap": summary_value(inputs["executable_ticket_gap_list"], "largest_gap") or "missing_gap_list_largest_gap",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
        "manual_approval_decision": summary_value(inputs["manual_execution_design_approval_gate"], "final_approval_gate_decision") or "missing_manual_execution_design_approval_gate",
    }


def checklist_closed(context: dict[str, str]) -> bool:
    return (
        context["final_ticket_blockers_decision"] == "FINAL_TICKET_BLOCKERS_CLOSED_NO_EXECUTION_APPROVAL"
        and context["closed_blocker_count"] == "5"
        and context["remaining_known_blockers"] == "none"
    )


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    closed = checklist_closed(context)
    return [
        row("checklist_blockers_closed", "ready_for_separate_approval_request" if closed else "manual_review_required", "high", f"closed_blocker_count={context['closed_blocker_count']}; remaining={context['remaining_known_blockers']}", "Checklist blockers are complete only if the saved final closeout record exists.", "review_saved_closeout_chain"),
        row("go_no_go_boundary", "execution_blocked", "critical", context["go_no_go_decision"], "The dashboard remains no-go until a separate explicit approval process changes it.", NEXT_STEP),
        row("manual_approval_boundary", "approval_not_recorded", "critical", context["manual_approval_decision"], "This checkpoint does not record execution approval.", NEXT_STEP),
        row("ticket_boundary", "no_ticket_or_values", "critical", "order_values_populated=false; executable_ticket_created=false", "No ticket values or executable ticket are created.", "keep_ticket_creation_blocked"),
    ]


def build_summary_rows(context: dict[str, str], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closed = checklist_closed(context)
    ready = str(closed)
    data = [
        ("final_readiness_status", FINAL_STATUS, "Saved-output readiness checkpoint."),
        ("final_readiness_decision", FINAL_DECISION if closed else "NOT_READY_MISSING_FINAL_CHECKLIST_CLOSEOUT", "Readiness to ask for a separate decision only; no approval requested."),
        ("active_seed", ACTIVE_SEED, "Current paper-live seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("checklist_blockers_closed", ready, "True only when all five saved checklist blockers are closed."),
        ("closed_blocker_count", context["closed_blocker_count"], "Closed checklist blocker count from rollup."),
        ("remaining_known_blockers", context["remaining_known_blockers"], "Remaining checklist blockers from rollup."),
        ("approval_request_ready", ready, "Ready to ask the user a separate approval question only."),
        ("approval_requested", "False", "This command does not ask or record approval."),
        ("approval_recorded", "False", "This command does not record approval."),
        ("manual_execution_design_approved", "False", "Manual execution design approval is still absent."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved dashboard decision."),
        ("manual_approval_decision", context["manual_approval_decision"], "Saved manual approval gate decision."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker ID is populated."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "explicit_human_execution_approval_not_recorded", "Only a separate explicit human approval process could change the no-go state."),
        ("recommended_next_step", NEXT_STEP, "Ask only if the user wants to continue to a separate approval process."),
        ("readiness_row_count", str(len(report_rows)), "Saved report row count."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("explicit_human_execution_approval_not_recorded", "blocked", "critical", "approval_recorded=false", NEXT_STEP),
        blocker_row("no_executable_ticket", "blocked", "critical", "executable_ticket_created=false; order_values_populated=false", "do_not_create_ticket_without_separate_approval"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]
    if not checklist_closed(context):
        rows.insert(0, blocker_row("checklist_closeout_incomplete", "blocked", "high", f"closed_blocker_count={context['closed_blocker_count']}; remaining={context['remaining_known_blockers']}", "refresh_final_ticket_blockers_closeout_record"))
    for name, input_rows in inputs.items():
        if not input_rows:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Execution approval request readiness complete. Report only; no approval requested.",
        f"final_readiness_status={summary_value(summary_rows, 'final_readiness_status')}",
        f"final_readiness_decision={summary_value(summary_rows, 'final_readiness_decision')}",
        f"checklist_blockers_closed={summary_value(summary_rows, 'checklist_blockers_closed')}",
        f"approval_request_ready={summary_value(summary_rows, 'approval_request_ready')}",
        f"approval_requested={summary_value(summary_rows, 'approval_requested')}",
        f"approval_recorded={summary_value(summary_rows, 'approval_recorded')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
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
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
