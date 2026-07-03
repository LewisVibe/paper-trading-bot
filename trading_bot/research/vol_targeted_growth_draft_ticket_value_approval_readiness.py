"""Readiness gate before any future ticket-value approval request.

This report reads saved outputs only. It checks whether the non-submitting
ticket draft and its quality gate are complete enough to support a later,
separate manual request to approve populating real ticket values. It does not
ask for that approval, record it, populate values, or create an executable
ticket.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
FINAL_STATUS = "vol_targeted_growth_draft_ticket_value_approval_readiness_manual_review_required"
FINAL_DECISION = "READY_TO_REQUEST_TICKET_VALUE_APPROVAL_NOT_APPROVED"
BLOCKED_DECISION = "NOT_READY_TO_REQUEST_TICKET_VALUE_APPROVAL"
NEXT_STEP = "manual_review_before_any_explicit_ticket_value_approval_request"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_draft_ticket_value_approval_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_draft_ticket_value_approval_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_draft_ticket_value_approval_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_draft_ticket_value_approval_readiness_evidence.csv"),
}

INPUT_FILES = {
    "ticket_draft": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_summary.csv"),
    "ticket_draft_quality_gate": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_summary.csv"),
    "draft_readiness": Path("data/vol_targeted_growth_executable_ticket_draft_readiness_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "readiness_only": True,
    "ticket_value_approval_request_ready": True,
    "ticket_value_approval_requested": False,
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

REPORT_COLUMNS = ["check_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class DraftTicketValueApprovalReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_draft_ticket_value_approval_readiness(
    root_dir: Path | str = ".",
) -> DraftTicketValueApprovalReadinessResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_report_rows(context)
    summary_rows = build_summary_rows(context, report_rows)
    blocker_rows = build_blocker_rows(context)
    evidence_rows = build_evidence_rows(inputs)
    paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return DraftTicketValueApprovalReadinessResult(
        paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        build_summary_lines(summary_rows, paths["report"]),
    )


def show_vol_targeted_growth_draft_ticket_value_approval_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted draft ticket-value approval readiness is missing.",
            "Run `python bot.py --vol-targeted-growth-draft-ticket-value-approval-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted draft ticket-value approval readiness saved display. Readiness only; no approval recorded.",
        f"final_ticket_value_approval_readiness_status: {summary_value(rows, 'final_ticket_value_approval_readiness_status')}",
        f"final_ticket_value_approval_readiness_decision: {summary_value(rows, 'final_ticket_value_approval_readiness_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"ticket_draft_quality_gate_decision: {summary_value(rows, 'ticket_draft_quality_gate_decision')}",
        f"ticket_value_approval_request_ready: {summary_value(rows, 'ticket_value_approval_request_ready')}",
        f"ticket_value_approval_requested: {summary_value(rows, 'ticket_value_approval_requested')}",
        f"ticket_value_approval_recorded: {summary_value(rows, 'ticket_value_approval_recorded')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"executable_ticket_created: {summary_value(rows, 'executable_ticket_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: readiness only; this does not ask for or record approval, populate values, create orders, call Alpaca, or schedule anything.",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    draft_decision = summary_value(inputs["ticket_draft"], "final_ticket_draft_decision")
    draft_created = summary_value(inputs["ticket_draft"], "draft_ticket_created")
    quality_decision = summary_value(inputs["ticket_draft_quality_gate"], "final_ticket_draft_quality_decision")
    quality_passed = summary_value(inputs["ticket_draft_quality_gate"], "quality_gate_passed")
    readiness_decision = summary_value(inputs["draft_readiness"], "final_executable_ticket_draft_readiness_decision")
    go_no_go_decision = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision")
    ready = (
        draft_created == "True"
        and quality_passed == "True"
        and quality_decision == "NON_SUBMITTING_EXECUTABLE_TICKET_DRAFT_QUALITY_GATE_PASSED_NO_EXECUTION"
    )
    return {
        "ticket_draft_decision": draft_decision or "missing_ticket_draft",
        "ticket_draft_created": draft_created or "False",
        "ticket_draft_quality_gate_decision": quality_decision or "missing_ticket_draft_quality_gate",
        "ticket_draft_quality_gate_passed": quality_passed or "False",
        "draft_readiness_decision": readiness_decision or "missing_draft_readiness",
        "go_no_go_decision": go_no_go_decision or "missing_go_no_go_dashboard",
        "approval_request_ready": str(ready),
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row(
            "non_submitting_ticket_draft",
            "pass" if context["ticket_draft_created"] == "True" else "manual_review_required",
            "critical",
            context["ticket_draft_decision"],
            "A saved draft can support a future approval request only if it remains non-submitting.",
            NEXT_STEP,
        ),
        report_row(
            "ticket_draft_quality_gate",
            "pass" if context["approval_request_ready"] == "True" else "manual_review_required",
            "critical",
            context["ticket_draft_quality_gate_decision"],
            "A passing draft quality gate can support asking for future value approval, but is not approval.",
            NEXT_STEP,
        ),
        report_row(
            "go_no_go_boundary",
            "execution_blocked",
            "critical",
            context["go_no_go_decision"],
            "The paper-live dashboard remains no-go for execution.",
            "keep_execution_blocked",
        ),
    ]


def build_summary_rows(context: dict[str, str], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ready = context["approval_request_ready"] == "True"
    data = [
        ("final_ticket_value_approval_readiness_status", FINAL_STATUS, "Ticket-value approval readiness checkpoint status."),
        ("final_ticket_value_approval_readiness_decision", FINAL_DECISION if ready else BLOCKED_DECISION, "Ready to ask later; not approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("ticket_draft_decision", context["ticket_draft_decision"], "Saved non-submitting draft decision."),
        ("ticket_draft_created", context["ticket_draft_created"], "True means saved review draft exists."),
        ("ticket_draft_quality_gate_decision", context["ticket_draft_quality_gate_decision"], "Saved draft quality-gate decision."),
        ("ticket_draft_quality_gate_passed", context["ticket_draft_quality_gate_passed"], "True means draft remains non-executable."),
        ("draft_readiness_decision", context["draft_readiness_decision"], "Prior readiness context."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved dashboard boundary."),
        ("readiness_check_count", str(len(report_rows)), "Number of readiness checks."),
        ("ticket_value_approval_request_ready", str(ready), "True means a later manual approval request could be considered."),
        ("ticket_value_approval_requested", "False", "No approval request is made by this report."),
        ("ticket_value_approval_recorded", "False", "No approval record is created by this report."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "ticket_value_approval_not_requested", "A separate future prompt is required before approval can be requested."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any explicit ticket-value approval request."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("ticket_value_approval_not_requested", "blocked", "critical", "This readiness gate does not ask for or record approval.", NEXT_STEP),
        blocker_row("ticket_values_not_approved", "blocked", "critical", "Ticket values remain unapproved and blank.", "keep_order_values_unapproved"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]
    if context["approval_request_ready"] != "True":
        rows.insert(0, blocker_row("draft_quality_gate_missing_or_blocked", "blocked", "critical", context["ticket_draft_quality_gate_decision"], "refresh_non_submitting_ticket_draft_quality_gate"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
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


def build_summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Volatility-targeted draft ticket-value approval readiness complete. Readiness only; no approval recorded.",
        f"final_ticket_value_approval_readiness_status={summary_value(rows, 'final_ticket_value_approval_readiness_status')}",
        f"final_ticket_value_approval_readiness_decision={summary_value(rows, 'final_ticket_value_approval_readiness_decision')}",
        f"ticket_value_approval_request_ready={summary_value(rows, 'ticket_value_approval_request_ready')}",
        f"ticket_value_approval_requested={summary_value(rows, 'ticket_value_approval_requested')}",
        f"ticket_value_approval_recorded={summary_value(rows, 'ticket_value_approval_recorded')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
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
