"""Saved-output approval criteria for future volatility executable tickets.

This checkpoint defines what must be manually true before the project can even
ask for executable-ticket approval. It does not request approval, create ticket
values, create executable tickets, call Alpaca, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_SEED = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"
FINAL_STATUS = "vol_targeted_growth_executable_ticket_approval_criteria_defined_manual_review_required"
FINAL_DECISION = "APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED"
NEXT_STEP = "manual_review_approval_criteria_before_any_approval_readiness_change"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_executable_ticket_approval_criteria.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_evidence.csv"),
}

INPUT_FILES = {
    "prerequisites_closeout": Path("data/vol_targeted_growth_executable_ticket_prerequisites_closeout_summary.csv"),
    "approval_readiness": Path("data/vol_targeted_growth_executable_ticket_approval_readiness_summary.csv"),
    "ticket_value_design": Path("data/vol_targeted_growth_manual_ticket_value_design_summary.csv"),
    "fresh_broker_gate_run": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "criteria_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "approval_requested": False,
    "approval_recorded": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "order_values_populated": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
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

REPORT_COLUMNS = [
    "criterion_name",
    "required_state",
    "current_status",
    "risk_level",
    "evidence",
    "manual_review_question",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class ApprovalCriteriaResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_executable_ticket_approval_criteria(root_dir: Path | str = ".") -> ApprovalCriteriaResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_report_rows(context)
    blocker_rows = build_blocker_rows(context, inputs)
    summary_rows = build_summary_rows(context, report_rows, blocker_rows)
    evidence_rows = build_evidence_rows(inputs)
    paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return ApprovalCriteriaResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, build_summary_lines(summary_rows, paths))


def show_vol_targeted_growth_executable_ticket_approval_criteria(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted executable-ticket approval criteria are missing.",
            "Run `python bot.py --vol-targeted-growth-executable-ticket-approval-criteria` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted executable-ticket approval criteria saved display. Report only; approval not requested.",
        f"final_approval_criteria_status: {summary_value(rows, 'final_approval_criteria_status')}",
        f"final_approval_criteria_decision: {summary_value(rows, 'final_approval_criteria_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"approval_readiness_decision: {summary_value(rows, 'approval_readiness_decision')}",
        f"approval_request_allowed_now: {summary_value(rows, 'approval_request_allowed_now')}",
        f"criterion_count: {summary_value(rows, 'criterion_count')}",
        f"open_blocker_count: {summary_value(rows, 'open_blocker_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "prereq_decision": summary_value(inputs["prerequisites_closeout"], "final_prerequisites_closeout_decision") or "missing_prerequisites_closeout",
        "approval_readiness_decision": summary_value(inputs["approval_readiness"], "final_approval_readiness_decision") or "missing_approval_readiness",
        "ticket_value_decision": summary_value(inputs["ticket_value_design"], "final_ticket_value_design_decision") or "missing_ticket_value_design",
        "populated_ticket_value_count": summary_value(inputs["ticket_value_design"], "populated_ticket_value_count") or "missing_populated_ticket_value_count",
        "fresh_broker_status": summary_value(inputs["fresh_broker_gate_run"], "final_pre_ticket_gate_run_status") or "missing_fresh_broker_gate_run",
        "broker_position_read_status": summary_value(inputs["fresh_broker_gate_run"], "broker_position_read_status") or "missing_broker_position_read_status",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        criterion_row(
            "prerequisites_closeout_ready",
            "prerequisites_closeout_must_be_closed_by_separate_manual_review",
            context["prereq_decision"],
            "critical",
            "Approval cannot be requested while prerequisites remain open.",
            "Have all prerequisite blockers been reviewed and explicitly closed without changing execution paths?",
            "keep_approval_not_ready_until_prerequisites_are_closed",
        ),
        criterion_row(
            "fresh_broker_context_current",
            "fresh_readonly_broker_context_must_be_current_and_unambiguous",
            f"{context['fresh_broker_status']}; {context['broker_position_read_status']}",
            "critical",
            "Broker context can only be read by an explicitly approved read-only command and does not approve orders.",
            "Is the saved broker context fresh enough and free of unknown-position ambiguity?",
            "rerun_readonly_gate_only_after_explicit_user_approval_if_stale",
        ),
        criterion_row(
            "ticket_values_explicitly_reviewed",
            "side_quantity_order_type_time_in_force_must_be_separately_approved_if_ever_needed",
            f"{context['ticket_value_decision']}; populated_ticket_value_count={context['populated_ticket_value_count']}",
            "critical",
            "Current ticket-value design keeps executable values blank.",
            "Are any future ticket values explicit, non-secret, non-derived from strategy output, and manually reviewed?",
            "do_not_populate_ticket_values_in_this_checkpoint",
        ),
        criterion_row(
            "go_no_go_dashboard_allows_request",
            "go_no_go_dashboard_must_stop_reporting_no_go_before_any_approval_request",
            context["go_no_go_decision"],
            "critical",
            "The dashboard is still no-go and monitor-only.",
            "Has the dashboard stopped reporting no-go through a separate safe review?",
            "keep_dashboard_no_go_until_manual_review_changes_it",
        ),
        criterion_row(
            "sleeve_mapping_boundaries",
            "high_growth_crypto_and_defensive_sleeves_must_not_become_order_instructions",
            "research_sleeves_unmapped_to_execution",
            "critical",
            "The active seed is multi-sleeve, but only review context exists; no sleeve is mapped to executable orders.",
            "Is any future single-symbol proxy or sleeve mapping explicitly justified without promoting research sleeves?",
            "keep_research_sleeves_blocked_from_execution",
        ),
        criterion_row(
            "scheduling_boundary",
            "order_capable_commands_must_never_be_scheduled",
            "never_schedule_order_capable_commands=True",
            "critical",
            "Monitoring cron can remain status-only, but order-capable commands must remain manual-only.",
            "Does the future approval request explicitly preserve no scheduling?",
            "keep_order_capable_scheduling_forbidden",
        ),
        criterion_row(
            "approval_prompt_boundary",
            "future_prompt_must_be_explicit_and_separate",
            "approval_requested=False; approval_recorded=False",
            "critical",
            "This checkpoint defines criteria only and does not ask for approval.",
            "Has the user explicitly approved the next narrow step in a later prompt?",
            "do_not_request_or_record_approval_here",
        ),
    ]


def build_summary_rows(context: dict[str, str], report_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_approval_criteria_status", FINAL_STATUS, "Approval criteria are defined for manual review only."),
        ("final_approval_criteria_decision", FINAL_DECISION, "Criteria exist, but approval is not requested or recorded."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("prerequisites_closeout_decision", context["prereq_decision"], "Saved prerequisites closeout decision."),
        ("approval_readiness_decision", context["approval_readiness_decision"], "Saved approval-readiness decision."),
        ("approval_request_allowed_now", "False", "Do not ask for approval from this checkpoint."),
        ("approval_requested", "False", "No approval was requested."),
        ("approval_recorded", "False", "No approval was recorded."),
        ("criterion_count", str(len(report_rows)), "Manual criteria row count."),
        ("open_blocker_count", str(len(blocker_rows)), "Open blocker row count."),
        ("largest_blocker", "approval_readiness_not_ready_and_prerequisites_open", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Manual review before changing approval readiness."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("approval_not_requested", "blocked", "critical", FINAL_DECISION, "do_not_request_approval_in_this_checkpoint"),
        blocker_row("approval_readiness_not_ready", "blocked", "critical", context["approval_readiness_decision"], "review_readiness_after_criteria"),
        blocker_row("prerequisites_not_closed", "blocked", "critical", context["prereq_decision"], "close_prerequisites_in_later_manual_review"),
        blocker_row("ticket_values_not_approved", "blocked", "critical", context["ticket_value_decision"], "keep_values_blank"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_all_approval_flags_false"),
    ]
    for name, input_rows in inputs.items():
        if not input_rows:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Executable-ticket approval criteria complete. Report only; approval not requested.",
        f"final_approval_criteria_status={summary_value(summary_rows, 'final_approval_criteria_status')}",
        f"final_approval_criteria_decision={summary_value(summary_rows, 'final_approval_criteria_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"approval_request_allowed_now={summary_value(summary_rows, 'approval_request_allowed_now')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={paths['report']}",
        "approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def criterion_row(name: str, required_state: str, current_status: str, risk: str, evidence: str, question: str, next_step: str) -> dict[str, Any]:
    return {
        "criterion_name": name,
        "required_state": required_state,
        "current_status": current_status,
        "risk_level": risk,
        "evidence": evidence,
        "manual_review_question": question,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
