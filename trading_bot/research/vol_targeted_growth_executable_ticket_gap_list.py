"""Saved-output executable-ticket gap list for the active volatility seed.

This report reads saved CSV summaries only. It does not call Alpaca, read
positions, refresh market data, create order fields, schedule anything, or
approve execution.
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
FINAL_STATUS = "vol_targeted_growth_executable_ticket_gap_list_execution_blocked_manual_review_required"
FINAL_DECISION = "EXECUTABLE_TICKET_DESIGN_NOT_READY"
NEXT_STEP = "manual_review_gap_list_before_any_executable_ticket_design_discussion"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_executable_ticket_gap_list.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_gap_list_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_gap_list_blockers.csv"),
}

INPUT_FILES = {
    "ticket_prerequisites": Path("data/vol_targeted_growth_executable_ticket_prerequisites_review_summary.csv"),
    "execution_blocker_rollup": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
    "candidate_approval": Path("data/vol_targeted_growth_paper_live_candidate_approval_summary.csv"),
    "allocation_policy": Path("data/vol_targeted_growth_allocation_cap_sleeve_mapping_policy_summary.csv"),
    "target_position_plan": Path("data/vol_targeted_growth_non_executable_target_position_plan_summary.csv"),
    "order_ticket_boundary": Path("data/vol_targeted_growth_order_ticket_boundary_design_summary.csv"),
    "broker_comparison": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "criteria_source_closeout_record": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv"),
    "criteria_resolution_plan_closeout_record": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_record_summary.csv"),
    "approval_criteria_closeout_record": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "order_side_created": False,
    "order_quantity_created": False,
    "order_type_created": False,
    "time_in_force_created": False,
    "executable_ticket_created": False,
    "executable_ticket_design_allowed": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "paper_live_candidate_approved": False,
    "manual_execution_design_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REPORT_COLUMNS = [
    "gap_name",
    "status",
    "severity",
    "saved_evidence",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthExecutableTicketGapListResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_executable_ticket_gap_list(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthExecutableTicketGapListResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(inputs, report_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(report_rows, inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthExecutableTicketGapListResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_executable_ticket_gap_list(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted executable ticket gap list is missing.",
            "Run `python bot.py --vol-targeted-growth-executable-ticket-gap-list` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted executable ticket gap list saved display. Report only; no ticket design approved.",
        f"final_gap_list_status: {summary_value(rows, 'final_gap_list_status')}",
        f"final_ticket_design_decision: {summary_value(rows, 'final_ticket_design_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"gap_count: {summary_value(rows, 'gap_count')}",
        f"critical_gap_count: {summary_value(rows, 'critical_gap_count')}",
        f"largest_gap: {summary_value(rows, 'largest_gap')}",
        f"closed_blocker_count: {summary_value(rows, 'closed_blocker_count')}",
        f"criteria_source_reviewed_closed: {summary_value(rows, 'criteria_source_reviewed_closed')}",
        f"criteria_resolution_plan_open_closed: {summary_value(rows, 'criteria_resolution_plan_open_closed')}",
        f"approval_criteria_not_approval_closed: {summary_value(rows, 'approval_criteria_not_approval_closed')}",
        f"remaining_known_blockers_after_closeout: {summary_value(rows, 'remaining_known_blockers_after_closeout')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_instructions_created=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: saved-output gap list only; no Alpaca, broker read, order, ticket design, live trading, or scheduling approval.",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    prerequisite_status = summary_value(inputs["ticket_prerequisites"], "final_executable_ticket_prerequisites_status")
    rollup_status = summary_value(inputs["execution_blocker_rollup"], "final_execution_blocker_rollup_status")
    go_no_go_decision = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision")
    return [
        gap_row(
            "manual_execution_design_approval_missing",
            "blocked",
            "critical",
            "manual_execution_design_approved=false",
            "No separate manual approval exists to design an executable ticket.",
            "record_separate_manual_execution_design_approval_only_if_user_explicitly_requests_it_later",
        ),
        gap_row(
            "executable_ticket_prerequisites_not_met",
            "blocked",
            "critical",
            prerequisite_status or "missing_ticket_prerequisites_summary",
            "The saved prerequisite review still says executable ticket design is not allowed.",
            "review_prerequisites_before_ticket_design",
        ),
        gap_row(
            "execution_blocker_rollup_not_cleared",
            "blocked",
            "critical",
            rollup_status or "missing_execution_blocker_rollup_summary",
            "The blocker rollup remains uncleared and explicitly blocks execution design.",
            "review_execution_blocker_rollup_before_ticket_design",
        ),
        gap_row(
            "go_no_go_dashboard_is_no_go",
            "blocked",
            "critical",
            go_no_go_decision or "missing_go_no_go_dashboard_summary",
            "The current dashboard decision is no-go/monitor-only, not ticket-design approval.",
            "keep_monitor_only_until_manual_review_changes_decision",
        ),
        gap_row(
            "fresh_readonly_broker_state_required",
            "blocked",
            "critical",
            "broker_positions_read=false; alpaca_called=false",
            "This report intentionally does not read the broker. Any future ticket design would need fresh read-only broker state with explicit approval.",
            "run_readonly_broker_check_only_after_separate_user_approval",
        ),
        gap_row(
            "allocation_cap_not_approved",
            "blocked",
            "critical",
            summary_value(inputs["allocation_policy"], "allocation_cap_approved") or "allocation_cap_approved=false",
            "The multi-sleeve allocation cap remains review-only and cannot size an order.",
            "approve_allocation_cap_separately_before_ticket_design",
        ),
        gap_row(
            "sleeve_mapping_not_approved",
            "blocked",
            "critical",
            "high_growth=research_only; crypto=research_only; defensive=unmapped",
            "Component sleeves cannot become executable order instructions by implication.",
            "complete_component_sleeve_reviews_before_ticket_design",
        ),
        gap_row(
            "target_position_plan_non_executable",
            "blocked",
            "critical",
            summary_value(inputs["target_position_plan"], "final_target_position_plan_status")
            or "missing_target_position_plan_summary",
            "The saved target-position plan is explanatory only and creates no executable target positions.",
            "manual_review_target_position_plan_before_ticket_design",
        ),
        gap_row(
            "order_ticket_boundary_blocks_order_fields",
            "blocked",
            "critical",
            summary_value(inputs["order_ticket_boundary"], "final_order_ticket_boundary_status")
            or "missing_order_ticket_boundary_summary",
            "The boundary design forbids side, quantity, order type, time-in-force, account, secret, and webhook fields.",
            "manual_review_boundary_before_any_ticket_schema",
        ),
        gap_row(
            "scheduling_not_approved",
            "blocked",
            "critical",
            "scheduling_approved=false; never_schedule_order_capable_commands=true",
            "Even a future executable design would not approve scheduling.",
            "keep_order_capable_commands_unscheduled",
        ),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    critical_count = sum(1 for row in report_rows if row.get("severity") == "critical")
    missing_inputs = [name for name, rows in inputs.items() if not rows]
    closed = closed_blockers(inputs)
    closed_blocker_count = len(closed)
    remaining_known_blockers = remaining_blockers_after_closeout(inputs)
    data = [
        ("final_gap_list_status", FINAL_STATUS, "Executable ticket design remains blocked."),
        ("final_ticket_design_decision", FINAL_DECISION, "No executable ticket design is ready or approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("gap_count", str(len(report_rows)), "Total gap rows."),
        ("critical_gap_count", str(critical_count), "Critical gap rows."),
        ("closed_blocker_count", str(closed_blocker_count), "Closed blockers recognised from saved closeout evidence."),
        ("criteria_source_reviewed_closed", str("criteria_source_reviewed" in closed), "True only when the saved criteria-source closeout record closes that blocker."),
        ("criteria_resolution_plan_open_closed", str("criteria_resolution_plan_open" in closed), "True only when the saved resolution-plan closeout record closes that blocker."),
        ("approval_criteria_not_approval_closed", str("approval_criteria_not_approval" in closed), "True only when the saved approval-criteria closeout record closes that blocker."),
        ("closed_blocker", ";".join(closed) or "none", "Closed blockers recognised by this gap-list recalculation."),
        ("remaining_known_blockers_after_closeout", remaining_known_blockers, "Known blockers that remain open after the criteria-source closeout record."),
        ("missing_saved_input_count", str(len(missing_inputs)), "Missing saved input summaries."),
        ("missing_saved_inputs", ";".join(missing_inputs) or "none", "Saved inputs missing from this gap list."),
        ("largest_gap", "manual_execution_design_approval_missing", "Primary blocker before any executable ticket design."),
        ("fresh_readonly_broker_state_required", "True", "Future ticket design would need separate explicit read-only broker approval."),
        ("component_sleeves_executable", "False", "High-growth and crypto remain research-only and defensive remains unmapped."),
        ("order_fields_created", "False", "No side, quantity, order type, time-in-force, account, secret, or webhook fields exist."),
        ("recommended_next_step", NEXT_STEP, "Manual review the gap list before any future executable ticket discussion."),
    ]
    return [summary_row(*item) for item in data]


def closed_blockers(inputs: dict[str, list[dict[str, str]]]) -> list[str]:
    closed = []
    source_rows = inputs.get("criteria_source_closeout_record", [])
    if (
        summary_value(source_rows, "final_closeout_record_decision") == "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY"
        and summary_value(source_rows, "closed_blocker") == "criteria_source_reviewed"
    ):
        closed.append("criteria_source_reviewed")
    resolution_rows = inputs.get("criteria_resolution_plan_closeout_record", [])
    if (
        summary_value(resolution_rows, "final_closeout_record_decision") == "CRITERIA_RESOLUTION_PLAN_OPEN_BLOCKER_CLOSED_ONLY"
        and summary_value(resolution_rows, "closed_blocker") == "criteria_resolution_plan_open"
    ):
        closed.append("criteria_resolution_plan_open")
    approval_rows = inputs.get("approval_criteria_closeout_record", [])
    if (
        summary_value(approval_rows, "final_closeout_record_decision") == "APPROVAL_CRITERIA_NOT_APPROVAL_BLOCKER_CLOSED_ONLY"
        and summary_value(approval_rows, "closed_blocker") == "approval_criteria_not_approval"
    ):
        closed.append("approval_criteria_not_approval")
    return closed


def remaining_blockers_after_closeout(inputs: dict[str, list[dict[str, str]]]) -> str:
    approval_remaining = summary_value(inputs.get("approval_criteria_closeout_record", []), "remaining_known_blockers")
    if approval_remaining:
        return approval_remaining
    resolution_remaining = summary_value(inputs.get("criteria_resolution_plan_closeout_record", []), "remaining_known_blockers")
    if resolution_remaining:
        return resolution_remaining
    source_remaining = summary_value(inputs.get("criteria_source_closeout_record", []), "remaining_known_blockers")
    return source_remaining or "criteria_closeout_records_missing"


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        (f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(
        (
            "runtime_boundary",
            "saved_output_only_no_broker_or_market_refresh",
            "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.",
        )
    )
    return [evidence_row(*item) for item in rows]


def build_blocker_rows(
    report_rows: list[dict[str, Any]],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = [
        blocker_row(row["gap_name"], row["status"], row["severity"], row["interpretation"], row["required_next_step"])
        for row in report_rows
    ]
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(
                0,
                blocker_row(
                    f"missing_{name}",
                    "blocked",
                    "high",
                    f"Saved input is missing: {path}",
                    f"refresh_{name}_report_only",
                ),
            )
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted executable ticket gap list complete. Report only; no ticket design or execution approved.",
        f"final_gap_list_status={summary_value(summary_rows, 'final_gap_list_status')}",
        f"final_ticket_design_decision={summary_value(summary_rows, 'final_ticket_design_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"gap_count={summary_value(summary_rows, 'gap_count')}",
        f"critical_gap_count={summary_value(summary_rows, 'critical_gap_count')}",
        f"largest_gap={summary_value(summary_rows, 'largest_gap')}",
        f"closed_blocker_count={summary_value(summary_rows, 'closed_blocker_count')}",
        f"criteria_source_reviewed_closed={summary_value(summary_rows, 'criteria_source_reviewed_closed')}",
        f"criteria_resolution_plan_open_closed={summary_value(summary_rows, 'criteria_resolution_plan_open_closed')}",
        f"approval_criteria_not_approval_closed={summary_value(summary_rows, 'approval_criteria_not_approval_closed')}",
        f"remaining_known_blockers_after_closeout={summary_value(summary_rows, 'remaining_known_blockers_after_closeout')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "order_instructions_created=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def gap_row(
    name: str,
    status: str,
    severity: str,
    evidence: str,
    interpretation: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "gap_name": name,
        "status": status,
        "severity": severity,
        "saved_evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **dict(SAFETY_FLAGS)}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **dict(SAFETY_FLAGS)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
