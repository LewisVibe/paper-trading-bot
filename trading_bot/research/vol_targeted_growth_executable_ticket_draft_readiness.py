"""Readiness checkpoint for a future non-submitting executable-ticket draft.

This report reads saved outputs only. It reviews whether the existing
review-only proposed ticket values are clear enough to support a later manual
discussion about a non-submitting executable-ticket draft. It does not create
that draft, populate order values, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
FINAL_STATUS = "vol_targeted_growth_executable_ticket_draft_readiness_manual_review_required"
FINAL_DECISION = "READY_TO_DISCUSS_NON_SUBMITTING_DRAFT_VALUES_NOT_EXECUTABLE"
BLOCKED_DECISION = "NOT_READY_TO_DISCUSS_NON_SUBMITTING_DRAFT"
NEXT_STEP = "manual_review_before_any_non_submitting_executable_ticket_draft"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_executable_ticket_draft_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_draft_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_draft_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_draft_readiness_evidence.csv"),
}

INPUT_FILES = {
    "proposed_ticket_values": Path("data/vol_targeted_growth_proposed_ticket_values_summary.csv"),
    "proposed_ticket_values_quality_gate": Path("data/vol_targeted_growth_proposed_ticket_values_quality_gate_summary.csv"),
    "non_submitting_executable_ticket_design": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "readiness_only": True,
    "draft_discussion_ready": True,
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
class ExecutableTicketDraftReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_executable_ticket_draft_readiness(
    root_dir: Path | str = ".",
) -> ExecutableTicketDraftReadinessResult:
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
    return ExecutableTicketDraftReadinessResult(
        output_paths=paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, paths["report"]),
    )


def show_vol_targeted_growth_executable_ticket_draft_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted executable-ticket draft readiness is missing.",
            "Run `python bot.py --vol-targeted-growth-executable-ticket-draft-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted executable-ticket draft readiness saved display. Readiness only; no ticket created.",
        f"final_executable_ticket_draft_readiness_status: {summary_value(rows, 'final_executable_ticket_draft_readiness_status')}",
        f"final_executable_ticket_draft_readiness_decision: {summary_value(rows, 'final_executable_ticket_draft_readiness_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"proposed_ticket_values_quality_gate_decision: {summary_value(rows, 'proposed_ticket_values_quality_gate_decision')}",
        f"draft_discussion_ready: {summary_value(rows, 'draft_discussion_ready')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"executable_ticket_created: {summary_value(rows, 'executable_ticket_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: readiness only; this does not create a ticket, order values, Alpaca calls, execution approval, or scheduling approval.",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    quality_decision = summary_value(inputs["proposed_ticket_values_quality_gate"], "final_proposed_ticket_values_quality_gate_decision")
    quality_passed = summary_value(inputs["proposed_ticket_values_quality_gate"], "quality_gate_passed")
    proposed_decision = summary_value(inputs["proposed_ticket_values"], "final_proposed_ticket_values_decision")
    design_decision = summary_value(inputs["non_submitting_executable_ticket_design"], "final_executable_ticket_design_decision")
    go_no_go_decision = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision")
    ready = quality_passed == "True" and quality_decision == "PROPOSED_TICKET_VALUES_QUALITY_GATE_PASSED_NO_EXECUTION"
    return {
        "proposed_ticket_values_decision": proposed_decision or "missing_proposed_ticket_values",
        "proposed_ticket_values_quality_gate_decision": quality_decision or "missing_proposed_ticket_values_quality_gate",
        "proposed_ticket_values_quality_gate_passed": quality_passed or "False",
        "non_submitting_executable_ticket_design_decision": design_decision or "missing_non_submitting_executable_ticket_design",
        "go_no_go_decision": go_no_go_decision or "missing_go_no_go_dashboard",
        "draft_discussion_ready": str(ready),
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row(
            "proposed_values_quality_gate",
            "pass" if context["draft_discussion_ready"] == "True" else "manual_review_required",
            "critical",
            context["proposed_ticket_values_quality_gate_decision"],
            "Passing the proposal quality gate can support discussion of a later non-submitting draft, but not execution.",
            NEXT_STEP,
        ),
        report_row(
            "non_submitting_design_context",
            "context_only",
            "high",
            context["non_submitting_executable_ticket_design_decision"],
            "Prior non-submitting design context remains design-only.",
            "keep_ticket_design_non_submitting",
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
    ready = context["draft_discussion_ready"] == "True"
    data = [
        ("final_executable_ticket_draft_readiness_status", FINAL_STATUS, "Readiness checkpoint status."),
        ("final_executable_ticket_draft_readiness_decision", FINAL_DECISION if ready else BLOCKED_DECISION, "Readiness decision; not a ticket or approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("proposed_ticket_values_decision", context["proposed_ticket_values_decision"], "Saved proposed values context."),
        ("proposed_ticket_values_quality_gate_decision", context["proposed_ticket_values_quality_gate_decision"], "Saved proposal quality gate context."),
        ("proposed_ticket_values_quality_gate_passed", context["proposed_ticket_values_quality_gate_passed"], "True means proposal labels remained non-executable."),
        ("non_submitting_executable_ticket_design_decision", context["non_submitting_executable_ticket_design_decision"], "Saved non-submitting design context."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved dashboard boundary."),
        ("readiness_check_count", str(len(report_rows)), "Number of readiness checks."),
        ("draft_discussion_ready", str(ready), "True means a later manual draft discussion can be considered."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "future_manual_draft_review_required", "A separate future prompt is required before any draft ticket artifact."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any non-submitting executable-ticket draft."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("future_manual_draft_review_required", "blocked", "critical", "This readiness checkpoint does not create a draft ticket.", NEXT_STEP),
        blocker_row("ticket_values_not_approved", "blocked", "critical", "Proposed values are review labels only and remain unapproved.", "keep_order_values_unapproved"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]
    if context["draft_discussion_ready"] != "True":
        rows.insert(0, blocker_row("proposal_quality_gate_missing_or_blocked", "blocked", "critical", context["proposed_ticket_values_quality_gate_decision"], "refresh_proposed_ticket_values_quality_gate"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
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
        "Volatility-targeted executable-ticket draft readiness complete. Readiness only; no ticket created.",
        f"final_executable_ticket_draft_readiness_status={summary_value(rows, 'final_executable_ticket_draft_readiness_status')}",
        f"final_executable_ticket_draft_readiness_decision={summary_value(rows, 'final_executable_ticket_draft_readiness_decision')}",
        f"draft_discussion_ready={summary_value(rows, 'draft_discussion_ready')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"executable_ticket_created={summary_value(rows, 'executable_ticket_created')}",
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
