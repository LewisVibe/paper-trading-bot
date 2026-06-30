"""Saved-output blocker resolution plan for volatility executable-ticket criteria.

This report turns the approval criteria into an ordered manual-review plan. It
does not resolve blockers, request approval, create ticket values, create
executable tickets, call Alpaca, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
FINAL_STATUS = "vol_targeted_growth_executable_ticket_criteria_resolution_plan_created_manual_review_required"
FINAL_DECISION = "CRITERIA_BLOCKER_RESOLUTION_PLAN_CREATED_APPROVAL_STILL_BLOCKED"
NEXT_STEP = "manual_review_resolution_plan_before_any_approval_readiness_change"

OUTPUT_FILES = {
    "plan": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_evidence.csv"),
}

INPUT_FILES = {
    "approval_criteria": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_summary.csv"),
    "approval_criteria_blockers": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_blockers.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "plan_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "blockers_resolved": False,
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

PLAN_COLUMNS = [
    "sequence",
    "blocker_name",
    "current_state",
    "resolution_question",
    "allowed_resolution_path",
    "forbidden_shortcut",
    "required_next_step",
    "status",
    "risk_level",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class CriteriaResolutionPlanResult:
    output_paths: dict[str, Path]
    plan_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_executable_ticket_criteria_resolution_plan(root_dir: Path | str = ".") -> CriteriaResolutionPlanResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    plan_rows = build_plan_rows(context)
    blocker_rows = build_blocker_rows(context, inputs)
    summary_rows = build_summary_rows(context, plan_rows, blocker_rows)
    evidence_rows = build_evidence_rows(inputs)
    paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(paths["plan"], PLAN_COLUMNS, plan_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return CriteriaResolutionPlanResult(paths, plan_rows, summary_rows, blocker_rows, evidence_rows, build_summary_lines(summary_rows, paths))


def show_vol_targeted_growth_executable_ticket_criteria_resolution_plan(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted executable-ticket criteria resolution plan is missing.",
            "Run `python bot.py --vol-targeted-growth-executable-ticket-criteria-resolution-plan` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted executable-ticket criteria resolution plan saved display. Report only; blockers not resolved.",
        f"final_resolution_plan_status: {summary_value(rows, 'final_resolution_plan_status')}",
        f"final_resolution_plan_decision: {summary_value(rows, 'final_resolution_plan_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"approval_criteria_decision: {summary_value(rows, 'approval_criteria_decision')}",
        f"approval_request_allowed_now: {summary_value(rows, 'approval_request_allowed_now')}",
        f"plan_step_count: {summary_value(rows, 'plan_step_count')}",
        f"open_blocker_count: {summary_value(rows, 'open_blocker_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "blockers_resolved=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "criteria_decision": summary_value(inputs["approval_criteria"], "final_approval_criteria_decision") or "missing_approval_criteria",
        "criteria_status": summary_value(inputs["approval_criteria"], "final_approval_criteria_status") or "missing_approval_criteria",
        "criteria_blocker_count": str(len(inputs["approval_criteria_blockers"])),
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_plan_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    raw_rows = [
        (
            "1",
            "confirm_criteria_source",
            context["criteria_decision"],
            "Do the saved criteria accurately describe the manual review boundary?",
            "Review the criteria report and correct wording only if it is misleading.",
            "Do not treat criteria wording as approval.",
            "review_approval_criteria_report",
            "open_manual_review_required",
            "high",
        ),
        (
            "2",
            "close_prerequisites",
            "EXECUTABLE_TICKET_PREREQUISITES_NOT_CLOSED",
            "Which prerequisite blockers can be closed through report-only evidence, and which require a later explicit prompt?",
            "Close only with a separate saved-output checkpoint and verifier.",
            "Do not auto-clear prerequisites from this plan.",
            "create_or_review_prerequisite_closeout_followup",
            "open_manual_review_required",
            "critical",
        ),
        (
            "3",
            "refresh_broker_context_if_stale",
            "fresh_broker_context_is_review_only",
            "Is the saved read-only broker context fresh enough for discussion?",
            "If stale, request explicit read-only Alpaca approval in a separate prompt before any broker read.",
            "Do not call Alpaca from this plan.",
            "separate_explicit_readonly_prompt_if_needed",
            "open_manual_review_required",
            "critical",
        ),
        (
            "4",
            "review_ticket_values",
            "order_values_populated=False",
            "Could any future side, quantity, order type, and time-in-force be manually justified without deriving from strategy output?",
            "Keep values blank until a future explicit value-approval checkpoint exists.",
            "Do not populate order fields in report-only code.",
            "manual_value_review_before_any_ticket",
            "open_manual_review_required",
            "critical",
        ),
        (
            "5",
            "review_sleeve_boundaries",
            "high_growth_crypto_defensive_sleeves_research_only",
            "Can the multi-sleeve candidate be discussed without turning research sleeves into executable orders?",
            "Keep research sleeves unmapped unless a later design explicitly handles them.",
            "Do not convert sleeve weights into orders.",
            "manual_sleeve_boundary_review",
            "open_manual_review_required",
            "critical",
        ),
        (
            "6",
            "preserve_scheduling_boundary",
            "never_schedule_order_capable_commands=True",
            "Does every future step preserve manual-only order-capable commands?",
            "Keep Hermes/VPS automation status-only.",
            "Do not schedule execution-capable commands.",
            "keep_status_cron_monitor_only",
            "open_manual_review_required",
            "critical",
        ),
        (
            "7",
            "recheck_go_no_go_dashboard",
            context["go_no_go_decision"],
            "Does the go/no-go dashboard still block execution after the criteria review?",
            "Regenerate the dashboard as saved-output monitoring only.",
            "Do not use dashboard output as execution approval.",
            "keep_dashboard_no_go_until_separate_review",
            "open_manual_review_required",
            "critical",
        ),
    ]
    return [plan_row(*row) for row in raw_rows]


def build_summary_rows(context: dict[str, str], plan_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_resolution_plan_status", FINAL_STATUS, "Resolution plan is defined for manual review only."),
        ("final_resolution_plan_decision", FINAL_DECISION, "The plan does not resolve blockers or request approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("approval_criteria_status", context["criteria_status"], "Saved approval criteria status."),
        ("approval_criteria_decision", context["criteria_decision"], "Saved approval criteria decision."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go decision."),
        ("approval_request_allowed_now", "False", "Do not ask for approval from this plan."),
        ("blockers_resolved", "False", "No blockers were resolved."),
        ("plan_step_count", str(len(plan_rows)), "Ordered manual plan step count."),
        ("open_blocker_count", str(len(blocker_rows)), "Open blocker row count."),
        ("largest_blocker", "criteria_blockers_not_resolved", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Manual review before changing approval readiness."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("criteria_blockers_not_resolved", "blocked", "critical", FINAL_DECISION, "manual_review_plan_steps"),
        blocker_row("approval_request_not_allowed", "blocked", "critical", "approval_request_allowed_now=False", "do_not_request_approval_from_this_plan"),
        blocker_row("go_no_go_remains_no_go", "blocked", "critical", context["go_no_go_decision"], "keep_dashboard_no_go"),
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
        "Executable-ticket criteria resolution plan complete. Report only; blockers not resolved.",
        f"final_resolution_plan_status={summary_value(summary_rows, 'final_resolution_plan_status')}",
        f"final_resolution_plan_decision={summary_value(summary_rows, 'final_resolution_plan_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"approval_request_allowed_now={summary_value(summary_rows, 'approval_request_allowed_now')}",
        f"plan_step_count={summary_value(summary_rows, 'plan_step_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={paths['plan']}",
        "blockers_resolved=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def plan_row(sequence: str, name: str, state: str, question: str, allowed: str, forbidden: str, next_step: str, status: str, risk: str) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "blocker_name": name,
        "current_state": state,
        "resolution_question": question,
        "allowed_resolution_path": allowed,
        "forbidden_shortcut": forbidden,
        "required_next_step": next_step,
        "status": status,
        "risk_level": risk,
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
