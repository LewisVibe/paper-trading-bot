"""Saved-output QQQ100 manual flatten runbook/design report.

This checkpoint documents the future manual-review conditions for a QQQ100
flatten discussion. It reads saved QQQ100 evidence only and never calls Alpaca,
reads live positions, refreshes market data, creates order instructions,
submits/cancels/replaces orders, writes SQLite, sends alerts, schedules
anything, or approves flatten execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_bot.research.qqq100_manual_flatten_readiness_report import evaluate_manual_flatten_readiness


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

OUTPUT_FILES = {
    "report": Path("data/qqq100_manual_flatten_runbook_report.csv"),
    "summary": Path("data/qqq100_manual_flatten_runbook_summary.csv"),
    "blockers": Path("data/qqq100_manual_flatten_runbook_blockers.csv"),
    "evidence": Path("data/qqq100_manual_flatten_runbook_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "flatten_execution_approved": False,
    "manual_flatten_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "monitoring_only": True,
    "saved_output_only": True,
    "design_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "action_preview_created": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "check_name",
    "check_status",
    "runbook_status",
    "active_strategy",
    "active_ticker",
    "desired_state",
    "saved_position_state",
    "saved_position_quantity",
    "alignment_state",
    "flatten_readiness_status",
    "manual_flatten_discussion_status",
    "required_next_step",
    "research_only",
    "report_only",
    "monitoring_only",
    "saved_output_only",
    "design_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "action_preview_created",
    "alpaca_called",
    "live_positions_read",
    "market_data_refreshed",
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass(frozen=True)
class Qqq100ManualFlattenRunbook:
    active_strategy: str
    active_ticker: str
    desired_state: str
    saved_position_state: str
    saved_position_quantity: str
    alignment_state: str
    flatten_readiness_status: str
    manual_flatten_discussion_status: str
    runbook_status: str
    primary_blocker: str
    recommended_next_step: str


@dataclass
class Qqq100ManualFlattenRunbookReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_manual_flatten_runbook_report(root_dir: Path | str = ".") -> Qqq100ManualFlattenRunbookReportResult:
    root = Path(root_dir)
    runbook = evaluate_manual_flatten_runbook(root)
    report_rows = build_report_rows(runbook)
    summary_rows = build_summary_rows(runbook)
    blocker_rows = build_blocker_rows(runbook)
    evidence_rows = build_evidence_rows(runbook)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return Qqq100ManualFlattenRunbookReportResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_qqq100_manual_flatten_runbook_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "QQQ100 manual flatten runbook report is missing.",
            "Run `python bot.py --qqq100-manual-flatten-runbook-report` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; flatten_execution_approved=false; manual_flatten_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 manual flatten runbook saved display. Design/report only; no orders approved.",
        f"runbook_status: {summary_value(rows, 'runbook_status')}",
        f"active_strategy: {summary_value(rows, 'active_strategy')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"desired_state: {summary_value(rows, 'desired_state')}",
        f"saved_position_state: {summary_value(rows, 'saved_position_state')}",
        f"saved_position_quantity: {summary_value(rows, 'saved_position_quantity')}",
        f"alignment_state: {summary_value(rows, 'alignment_state')}",
        f"flatten_readiness_status: {summary_value(rows, 'flatten_readiness_status')}",
        f"manual_flatten_discussion_status: {summary_value(rows, 'manual_flatten_discussion_status')}",
        f"primary_blocker: {summary_value(rows, 'primary_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; flatten_execution_approved=false; manual_flatten_approved=false",
        "Warning: this runbook does not create order instructions or approve any flatten action.",
    ]


def evaluate_manual_flatten_runbook(root_dir: Path | str = ".") -> Qqq100ManualFlattenRunbook:
    readiness = evaluate_manual_flatten_readiness(root_dir)
    if readiness.flatten_readiness_status == "flatten_not_needed_currently":
        runbook_status = "manual_flatten_runbook_not_needed_currently"
        blocker = "none_current_state_aligned_long"
        next_step = "hold_no_action_and_monitor_only"
    elif readiness.flatten_readiness_status == "flatten_not_needed_already_flat":
        runbook_status = "manual_flatten_runbook_not_needed_already_flat"
        blocker = "none_current_state_already_flat"
        next_step = "hold_no_action_and_monitor_only"
    elif readiness.flatten_readiness_status == "future_manual_flatten_discussion_possible_not_approved":
        runbook_status = "manual_flatten_runbook_manual_review_required_not_approved"
        blocker = "manual_flatten_requires_separate_explicit_approval"
        next_step = "separate_manual_flatten_review_required_before_any_order_capable_workflow"
    else:
        runbook_status = "manual_flatten_runbook_blocked_missing_or_contradictory_evidence"
        blocker = readiness.largest_blocker or "missing_or_contradictory_saved_evidence"
        next_step = readiness.recommended_next_step or "manual_review_required_before_any_flatten_discussion"

    return Qqq100ManualFlattenRunbook(
        active_strategy=STRATEGY_NAME,
        active_ticker=TICKER,
        desired_state=readiness.desired_state,
        saved_position_state=readiness.saved_position_state,
        saved_position_quantity=readiness.saved_position_quantity,
        alignment_state=readiness.alignment_state,
        flatten_readiness_status=readiness.flatten_readiness_status,
        manual_flatten_discussion_status=readiness.manual_flatten_discussion_status,
        runbook_status=runbook_status,
        primary_blocker=blocker,
        recommended_next_step=next_step,
    )


def build_report_rows(runbook: Qqq100ManualFlattenRunbook) -> list[dict[str, Any]]:
    checks = [
        ("manual_flatten_runbook_status", runbook.runbook_status, runbook.recommended_next_step),
        ("saved_desired_state_check", desired_state_status(runbook), "Saved desired state must be flat before any future manual flatten discussion."),
        ("exact_one_share_position_check", exact_quantity_status(runbook), "Saved QQQ quantity must be exactly one share for this narrow future flatten design."),
        ("unknown_or_excess_position_boundary", unknown_or_excess_status(runbook), "Unknown, fractional, or excess QQQ quantity blocks manual flatten discussion."),
        ("order_instruction_boundary", "blocked_order_instructions_not_created", "This runbook must not create executable order instructions."),
        ("approval_boundary", "blocked_manual_flatten_not_approved", "This runbook must not approve paper execution or a flatten action."),
        ("scheduling_boundary", "blocked_scheduling_not_approved", "Order-capable commands must never be scheduled."),
    ]
    return [report_row(name, status, runbook, next_step) for name, status, next_step in checks]


def desired_state_status(runbook: Qqq100ManualFlattenRunbook) -> str:
    if runbook.desired_state == "flat":
        return "desired_flat_saved_evidence_present"
    if runbook.desired_state == "long":
        return "desired_long_saved_evidence_flatten_not_needed"
    return "desired_state_missing_or_unknown_manual_review_required"


def exact_quantity_status(runbook: Qqq100ManualFlattenRunbook) -> str:
    if runbook.saved_position_state == "paper_position_long" and runbook.saved_position_quantity == "1":
        return "exact_one_share_saved_position_confirmed"
    if runbook.saved_position_quantity == "0":
        return "no_saved_position_to_flatten"
    return "exact_one_share_saved_position_not_confirmed"


def unknown_or_excess_status(runbook: Qqq100ManualFlattenRunbook) -> str:
    if runbook.saved_position_quantity in {"0", "1"}:
        return "no_unknown_or_excess_quantity_detected"
    return "manual_review_required_unknown_or_excess_quantity"


def build_summary_rows(runbook: Qqq100ManualFlattenRunbook) -> list[dict[str, Any]]:
    rows = [
        ("runbook_status", runbook.runbook_status, "Saved-output manual flatten runbook/design status."),
        ("active_strategy", runbook.active_strategy, "Only qqq_100_trend_gate is in scope."),
        ("active_ticker", runbook.active_ticker, "Only QQQ is in scope."),
        ("desired_state", runbook.desired_state, "Saved desired QQQ100 state."),
        ("saved_position_state", runbook.saved_position_state, "Saved QQQ paper position state."),
        ("saved_position_quantity", runbook.saved_position_quantity, "Saved absolute QQQ quantity."),
        ("alignment_state", runbook.alignment_state, "Saved QQQ alignment state."),
        ("flatten_readiness_status", runbook.flatten_readiness_status, "Saved flatten readiness status."),
        ("manual_flatten_discussion_status", runbook.manual_flatten_discussion_status, "Manual discussion status; never order approval."),
        ("primary_blocker", runbook.primary_blocker, "Primary blocker or no-action marker."),
        ("recommended_next_step", runbook.recommended_next_step, "Runbook recommendation; never an order instruction."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("repeat_execution_approved", "False", "Repeat execution approval remains false."),
        ("flatten_execution_approved", "False", "Flatten execution approval remains false."),
        ("manual_flatten_approved", "False", "Manual flatten approval remains false."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must never be scheduled."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(runbook: Qqq100ManualFlattenRunbook) -> list[dict[str, Any]]:
    rows = [
        ("manual_flatten_not_approved", "blocked", "critical", "This runbook does not approve a manual flatten action.", "Use a separate explicit approval workflow before any future order-capable command."),
        ("order_instructions_not_created", "blocked", "critical", "This runbook does not create executable order instructions.", "Do not derive order instructions from this report."),
        ("execution_not_approved", "blocked", "critical", "This runbook does not approve execution or paper execution.", "Do not run QQQ100 paper execution from this report."),
        ("scheduling_not_approved", "blocked", "critical", "Scheduling remains prohibited for order-capable commands.", "Do not schedule QQQ100 execution or follow-up workflows."),
    ]
    if runbook.primary_blocker not in {"none_current_state_aligned_long", "none_current_state_already_flat"}:
        rows.insert(
            0,
            (
                runbook.primary_blocker,
                "manual_review_required",
                "high",
                f"Runbook status: {runbook.runbook_status}.",
                runbook.recommended_next_step,
            ),
        )
    return [
        {
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for name, status, severity, details, next_step in rows
    ]


def build_evidence_rows(runbook: Qqq100ManualFlattenRunbook) -> list[dict[str, Any]]:
    values = [
        ("desired_state", runbook.desired_state, "Saved desired position."),
        ("saved_position_state", runbook.saved_position_state, "Saved paper position state."),
        ("saved_position_quantity", runbook.saved_position_quantity, "Saved absolute QQQ quantity."),
        ("alignment_state", runbook.alignment_state, "Saved alignment state."),
        ("flatten_readiness_status", runbook.flatten_readiness_status, "Saved flatten readiness result."),
        ("runbook_status", runbook.runbook_status, "Manual flatten runbook/design result."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in values]


def report_row(
    check_name: str,
    check_status: str,
    runbook: Qqq100ManualFlattenRunbook,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "check_name": check_name,
        "check_status": check_status,
        "runbook_status": runbook.runbook_status,
        "active_strategy": runbook.active_strategy,
        "active_ticker": runbook.active_ticker,
        "desired_state": runbook.desired_state,
        "saved_position_state": runbook.saved_position_state,
        "saved_position_quantity": runbook.saved_position_quantity,
        "alignment_state": runbook.alignment_state,
        "flatten_readiness_status": runbook.flatten_readiness_status,
        "manual_flatten_discussion_status": runbook.manual_flatten_discussion_status,
        "required_next_step": required_next_step,
        **ROW_SAFETY,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ100 manual flatten runbook report complete. Saved-output design/report only; no orders approved.",
        f"Runbook status: {summary_value(summary_rows, 'runbook_status')}",
        f"Active strategy: {summary_value(summary_rows, 'active_strategy')}",
        f"Active ticker: {summary_value(summary_rows, 'active_ticker')}",
        f"Desired state: {summary_value(summary_rows, 'desired_state')}",
        f"Saved position: {summary_value(summary_rows, 'saved_position_state')} quantity={summary_value(summary_rows, 'saved_position_quantity')}",
        f"Alignment state: {summary_value(summary_rows, 'alignment_state')}",
        f"Flatten readiness status: {summary_value(summary_rows, 'flatten_readiness_status')}",
        f"Manual flatten discussion status: {summary_value(summary_rows, 'manual_flatten_discussion_status')}",
        f"Primary blocker: {summary_value(summary_rows, 'primary_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report/summary/blockers/evidence to {output_paths['report']}; {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; flatten_execution_approved=false; manual_flatten_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
