"""Saved-output QQQ100 manual flatten readiness report.

This report interprets saved QQQ100 paper-live evidence only. It does not call
Alpaca, read live positions, refresh market data, create executable order
instructions, submit/cancel/replace orders, write SQLite, send alerts, schedule
anything, or approve flatten/follow-up execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_bot.research.paper_live_evidence_audit import evaluate_paper_live_saved_evidence
from trading_bot.research.qqq100_followup_policy_report import evaluate_followup_policy


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

OUTPUT_FILES = {
    "report": Path("data/qqq100_manual_flatten_readiness_report.csv"),
    "summary": Path("data/qqq100_manual_flatten_readiness_summary.csv"),
    "blockers": Path("data/qqq100_manual_flatten_readiness_blockers.csv"),
    "evidence": Path("data/qqq100_manual_flatten_readiness_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "flatten_execution_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "monitoring_only": True,
    "saved_output_only": True,
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
    "flatten_readiness_status",
    "active_strategy",
    "active_ticker",
    "desired_state",
    "saved_position_state",
    "saved_position_quantity",
    "alignment_state",
    "followup_policy_status",
    "manual_flatten_discussion_status",
    "largest_blocker",
    "recommended_next_step",
    "research_only",
    "report_only",
    "monitoring_only",
    "saved_output_only",
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
class Qqq100ManualFlattenReadiness:
    active_strategy: str
    active_ticker: str
    desired_state: str
    saved_position_state: str
    saved_position_quantity: str
    alignment_state: str
    followup_policy_status: str
    flatten_readiness_status: str
    manual_flatten_discussion_status: str
    largest_blocker: str
    recommended_next_step: str


@dataclass
class Qqq100ManualFlattenReadinessReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_manual_flatten_readiness_report(
    root_dir: Path | str = ".",
) -> Qqq100ManualFlattenReadinessReportResult:
    root = Path(root_dir)
    readiness = evaluate_manual_flatten_readiness(root)
    report_rows = build_report_rows(readiness)
    summary_rows = build_summary_rows(readiness)
    blocker_rows = build_blocker_rows(readiness)
    evidence_rows = build_evidence_rows(readiness)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return Qqq100ManualFlattenReadinessReportResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_qqq100_manual_flatten_readiness_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "QQQ100 manual flatten readiness report is missing.",
            "Run `python bot.py --qqq100-manual-flatten-readiness-report` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; flatten_execution_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 manual flatten readiness saved display. Report only; no orders approved.",
        f"flatten_readiness_status: {summary_value(rows, 'flatten_readiness_status')}",
        f"active_strategy: {summary_value(rows, 'active_strategy')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"desired_state: {summary_value(rows, 'desired_state')}",
        f"saved_position_state: {summary_value(rows, 'saved_position_state')}",
        f"saved_position_quantity: {summary_value(rows, 'saved_position_quantity')}",
        f"alignment_state: {summary_value(rows, 'alignment_state')}",
        f"followup_policy_status: {summary_value(rows, 'followup_policy_status')}",
        f"manual_flatten_discussion_status: {summary_value(rows, 'manual_flatten_discussion_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; flatten_execution_approved=false",
        "Warning: this readiness report does not create order instructions or approve any flatten action.",
    ]


def evaluate_manual_flatten_readiness(root_dir: Path | str = ".") -> Qqq100ManualFlattenReadiness:
    snapshot = evaluate_paper_live_saved_evidence(root_dir)
    policy = evaluate_followup_policy(root_dir)

    if policy.final_policy_status == "no_action_required_already_aligned":
        status = "flatten_not_needed_currently"
        manual_status = "manual_flatten_discussion_not_needed_currently"
        blocker = "none_current_state_aligned_long"
        next_step = "hold_no_action_and_monitor_only"
    elif policy.final_policy_status == "future_manual_flatten_discussion_possible":
        status = "future_manual_flatten_discussion_possible_not_approved"
        manual_status = "manual_flatten_discussion_possible_after_separate_approval"
        blocker = "manual_flatten_not_approved_by_readiness_report"
        next_step = "separate_manual_flatten_readiness_review_required_before_any_action"
    elif policy.final_policy_status == "no_action_required_already_flat":
        status = "flatten_not_needed_already_flat"
        manual_status = "manual_flatten_discussion_not_needed_already_flat"
        blocker = "none_current_state_already_flat"
        next_step = "hold_no_action_and_monitor_only"
    else:
        status = "blocked_manual_review_required"
        manual_status = "manual_flatten_discussion_blocked_pending_saved_evidence_review"
        blocker = policy.blocker or "missing_or_contradictory_saved_evidence"
        next_step = policy.recommended_next_step or "manual_review_required_before_any_flatten_discussion"

    return Qqq100ManualFlattenReadiness(
        active_strategy=STRATEGY_NAME,
        active_ticker=TICKER,
        desired_state=snapshot.desired_state,
        saved_position_state=snapshot.saved_current_position_state,
        saved_position_quantity=snapshot.saved_current_position_quantity,
        alignment_state=snapshot.current_alignment_state,
        followup_policy_status=policy.final_policy_status,
        flatten_readiness_status=status,
        manual_flatten_discussion_status=manual_status,
        largest_blocker=blocker,
        recommended_next_step=next_step,
    )


def build_report_rows(readiness: Qqq100ManualFlattenReadiness) -> list[dict[str, Any]]:
    return [
        report_row("qqq100_manual_flatten_readiness", readiness),
        report_row("flatten_execution_boundary", readiness, "flatten_execution_not_approved"),
        report_row("scheduling_boundary", readiness, "scheduling_not_approved"),
    ]


def build_summary_rows(readiness: Qqq100ManualFlattenReadiness) -> list[dict[str, Any]]:
    rows = [
        ("flatten_readiness_status", readiness.flatten_readiness_status, "Saved-output manual flatten readiness status."),
        ("active_strategy", readiness.active_strategy, "Only qqq_100_trend_gate is in scope."),
        ("active_ticker", readiness.active_ticker, "Only QQQ is in scope."),
        ("desired_state", readiness.desired_state, "Saved desired QQQ100 state."),
        ("saved_position_state", readiness.saved_position_state, "Saved QQQ paper position state."),
        ("saved_position_quantity", readiness.saved_position_quantity, "Saved absolute QQQ quantity."),
        ("alignment_state", readiness.alignment_state, "Saved QQQ alignment state."),
        ("followup_policy_status", readiness.followup_policy_status, "Saved follow-up/no-action policy status."),
        ("manual_flatten_discussion_status", readiness.manual_flatten_discussion_status, "Manual discussion status; never order approval."),
        ("largest_blocker", readiness.largest_blocker, "Largest blocker or no-action marker."),
        ("recommended_next_step", readiness.recommended_next_step, "Monitoring recommendation; never an order instruction."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("repeat_execution_approved", "False", "Repeat execution approval remains false."),
        ("flatten_execution_approved", "False", "Flatten execution approval remains false."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must never be scheduled."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(readiness: Qqq100ManualFlattenReadiness) -> list[dict[str, Any]]:
    rows = [
        ("flatten_execution_not_approved", "blocked", "critical", "Readiness report does not approve flatten execution.", "Do not run QQQ100 paper execution from this report."),
        ("order_instructions_not_created", "blocked", "critical", "Readiness report does not create executable order instructions.", "Use separate explicit approval before any future action workflow."),
        ("repeat_execution_not_approved", "blocked", "critical", "Repeat execution remains blocked.", "Do not repeat QQQ100 paper execution."),
        ("scheduling_not_approved", "blocked", "critical", "Order-capable scheduling remains prohibited.", "Do not schedule order-capable commands."),
    ]
    if readiness.largest_blocker not in {"none_current_state_aligned_long", "none_current_state_already_flat"}:
        rows.insert(
            0,
            (
                readiness.largest_blocker,
                "manual_review_required",
                "high",
                f"Flatten readiness status: {readiness.flatten_readiness_status}.",
                readiness.recommended_next_step,
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


def build_evidence_rows(readiness: Qqq100ManualFlattenReadiness) -> list[dict[str, Any]]:
    values = [
        ("desired_state", readiness.desired_state, "Saved desired position."),
        ("saved_position_state", readiness.saved_position_state, "Saved paper position state."),
        ("saved_position_quantity", readiness.saved_position_quantity, "Saved absolute QQQ quantity."),
        ("alignment_state", readiness.alignment_state, "Saved alignment state."),
        ("followup_policy_status", readiness.followup_policy_status, "Saved follow-up/no-action policy."),
        ("flatten_readiness_status", readiness.flatten_readiness_status, "Manual flatten readiness result."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in values]


def report_row(
    check_name: str,
    readiness: Qqq100ManualFlattenReadiness,
    override_status: str | None = None,
) -> dict[str, Any]:
    return {
        "check_name": check_name,
        "flatten_readiness_status": override_status or readiness.flatten_readiness_status,
        "active_strategy": readiness.active_strategy,
        "active_ticker": readiness.active_ticker,
        "desired_state": readiness.desired_state,
        "saved_position_state": readiness.saved_position_state,
        "saved_position_quantity": readiness.saved_position_quantity,
        "alignment_state": readiness.alignment_state,
        "followup_policy_status": readiness.followup_policy_status,
        "manual_flatten_discussion_status": readiness.manual_flatten_discussion_status,
        "largest_blocker": readiness.largest_blocker,
        "recommended_next_step": readiness.recommended_next_step,
        **ROW_SAFETY,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ100 manual flatten readiness report complete. Saved-output report only; no orders approved.",
        f"Flatten readiness status: {summary_value(summary_rows, 'flatten_readiness_status')}",
        f"Active strategy: {summary_value(summary_rows, 'active_strategy')}",
        f"Active ticker: {summary_value(summary_rows, 'active_ticker')}",
        f"Desired state: {summary_value(summary_rows, 'desired_state')}",
        f"Saved position: {summary_value(summary_rows, 'saved_position_state')} quantity={summary_value(summary_rows, 'saved_position_quantity')}",
        f"Alignment state: {summary_value(summary_rows, 'alignment_state')}",
        f"Follow-up policy status: {summary_value(summary_rows, 'followup_policy_status')}",
        f"Manual flatten discussion status: {summary_value(summary_rows, 'manual_flatten_discussion_status')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report/summary/blockers/evidence to {output_paths['report']}; {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; flatten_execution_approved=false",
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
