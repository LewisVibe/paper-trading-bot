"""Saved-output paper-live monitoring status for VPS/Hermes reporting.

This report reads saved paper-live evidence and QQQ100 prior-seed policy outputs only. It does not
call Alpaca, read live positions, refresh market data, create executable order
instructions, write SQLite, send alerts, schedule anything, or approve
execution/follow-up orders.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_bot.research.paper_live_evidence_audit import evaluate_paper_live_saved_evidence


ACTIVE_STRATEGY_NAME = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_STRATEGY_NAME = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"
FOLLOWUP_POLICY_SUMMARY = Path("data/qqq100_followup_policy_summary.csv")

OUTPUT_FILES = {
    "summary": Path("data/paper_live_monitoring_status.csv"),
    "components": Path("data/paper_live_monitoring_components.csv"),
    "blockers": Path("data/paper_live_monitoring_blockers.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "monitoring_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_FLAGS.keys(),
]

COMPONENT_COLUMNS = [
    "component_name",
    "component_status",
    "component_value",
    "details",
    "research_only",
    "report_only",
    "monitoring_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "alpaca_called",
    "live_positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]


@dataclass(frozen=True)
class PaperLiveMonitoringStatus:
    active_strategy: str
    active_ticker: str
    previous_seed_strategy: str
    previous_seed_ticker: str
    saved_position_state: str
    saved_position_quantity: str
    alignment_state: str
    followup_policy_status: str
    no_action_required: str
    largest_blocker: str
    recommended_next_step: str


@dataclass
class PaperLiveMonitoringStatusResult:
    output_paths: dict[str, Path]
    summary_rows: list[dict[str, Any]]
    component_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_monitoring_status(root_dir: Path | str = ".") -> PaperLiveMonitoringStatusResult:
    root = Path(root_dir)
    status = build_monitoring_status(root)
    summary_rows = build_summary_rows(status)
    component_rows = build_component_rows(status)
    blocker_rows = build_blocker_rows(status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["components"], COMPONENT_COLUMNS, component_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return PaperLiveMonitoringStatusResult(
        output_paths=output_paths,
        summary_rows=summary_rows,
        component_rows=component_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_monitoring_status(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live monitoring status is missing.",
            "Run `python bot.py --paper-live-monitoring-status` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live monitoring status saved display. Monitoring/report only; no orders approved.",
        f"active_strategy: {summary_value(rows, 'active_strategy')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"previous_seed_strategy: {summary_value(rows, 'previous_seed_strategy')}",
        f"previous_seed_ticker: {summary_value(rows, 'previous_seed_ticker')}",
        f"saved_position_state: {summary_value(rows, 'saved_position_state')}",
        f"saved_position_quantity: {summary_value(rows, 'saved_position_quantity')}",
        f"alignment_state: {summary_value(rows, 'alignment_state')}",
        f"followup_policy_status: {summary_value(rows, 'followup_policy_status')}",
        f"no_action_required: {summary_value(rows, 'no_action_required')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_monitoring_status(root: Path) -> PaperLiveMonitoringStatus:
    followup_rows = read_csv_rows(root / FOLLOWUP_POLICY_SUMMARY)
    snapshot = evaluate_paper_live_saved_evidence(root)
    followup_status = summary_value(followup_rows, "final_followup_policy_status")
    no_action_required = summary_value(followup_rows, "no_action_required")
    recommended = summary_value(followup_rows, "recommended_next_step")
    blocker = summary_value(followup_rows, "largest_blocker")
    if not followup_status:
        followup_status = "missing_saved_evidence"
        no_action_required = "False"
        recommended = "regenerate_saved_followup_policy_report_for_monitoring"
        blocker = "missing_saved_followup_policy_summary"
    if recommended == "hold_no_action_and_do_not_repeat_buy":
        recommended = "hold_no_action_and_monitor_only"
    return PaperLiveMonitoringStatus(
        active_strategy=ACTIVE_STRATEGY_NAME,
        active_ticker=ACTIVE_TICKER,
        previous_seed_strategy=PREVIOUS_STRATEGY_NAME,
        previous_seed_ticker=PREVIOUS_TICKER,
        saved_position_state=snapshot.saved_current_position_state,
        saved_position_quantity=snapshot.saved_current_position_quantity,
        alignment_state=snapshot.current_alignment_state,
        followup_policy_status=followup_status,
        no_action_required=no_action_required or "False",
        largest_blocker=blocker or "manual_review_required",
        recommended_next_step=recommended or "manual_review_required",
    )


def build_summary_rows(status: PaperLiveMonitoringStatus) -> list[dict[str, Any]]:
    rows = [
        ("active_strategy", status.active_strategy, "Active paper-live monitoring seed strategy."),
        ("active_ticker", status.active_ticker, "Active paper-live monitoring seed instrument group."),
        ("previous_seed_strategy", status.previous_seed_strategy, "Previous QQQ100 seed retained as saved context."),
        ("previous_seed_ticker", status.previous_seed_ticker, "Previous QQQ100 seed ticker retained as saved context."),
        ("saved_position_state", status.saved_position_state, "Saved QQQ paper position state from previous seed context."),
        ("saved_position_quantity", status.saved_position_quantity, "Saved QQQ paper position quantity from previous seed context."),
        ("alignment_state", status.alignment_state, "Saved QQQ alignment state from previous seed context."),
        ("followup_policy_status", status.followup_policy_status, "Saved QQQ100 prior-seed follow-up/no-action policy status."),
        ("no_action_required", status.no_action_required, "True when saved prior-seed state says no paper action is needed."),
        ("largest_blocker", status.largest_blocker, "Largest monitoring blocker or no-action marker."),
        ("recommended_next_step", status.recommended_next_step, "Monitoring recommendation; never an order instruction."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must not be scheduled."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("repeat_execution_approved", "False", "Repeat execution approval remains false."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_component_rows(status: PaperLiveMonitoringStatus) -> list[dict[str, Any]]:
    values = [
        ("active_seed", "vol_targeted_seed_status_only", f"{status.active_strategy}:{status.active_ticker}", "Active seed label changed for reports only."),
        ("previous_seed_qqq100_position", status.alignment_state, f"{status.saved_position_state} quantity={status.saved_position_quantity}", "Saved QQQ100 previous-seed position/alignment evidence."),
        ("previous_seed_qqq100_followup_policy", status.followup_policy_status, status.no_action_required, "Saved QQQ100 previous-seed follow-up/no-action policy evidence."),
        ("approval_flags", "pass", "all_false", "Execution, scheduling, follow-up, and repeat approvals remain false."),
        ("scheduling_boundary", "pass", "never_schedule_order_capable_commands=True", "Monitoring status must not create or alter schedules."),
    ]
    return [
        {
            "component_name": name,
            "component_status": component_status,
            "component_value": value,
            "details": details,
            **ROW_SAFETY,
        }
        for name, component_status, value, details in values
    ]


def build_blocker_rows(status: PaperLiveMonitoringStatus) -> list[dict[str, Any]]:
    rows = [
        ("execution_not_approved", "blocked", "critical", "Execution remains unapproved.", "Monitor only; do not run execution commands."),
        ("followup_order_not_approved", "blocked", "critical", "Follow-up orders remain unapproved.", "Do not create order instructions."),
        ("repeat_execution_not_approved", "blocked", "critical", "Repeat execution remains unapproved.", "Do not repeat QQQ100 or volatility paper execution."),
        ("scheduling_not_approved", "blocked", "critical", "Order-capable scheduling remains prohibited.", "Do not create, edit, trigger, or schedule Hermes/cron/Task Scheduler jobs."),
    ]
    if status.followup_policy_status == "missing_saved_evidence":
        rows.insert(
            0,
            (
                "missing_saved_evidence",
                "manual_review_required",
                "high",
                "Saved QQQ100 previous-seed follow-up policy summary is missing.",
                "Regenerate saved report-only QQQ100 previous-seed follow-up policy output.",
            ),
        )
    return [
        {
            "blocker_name": name,
            "status": row_status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for name, row_status, severity, details, next_step in rows
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live monitoring status complete. Monitoring/report only; no orders approved.",
        f"Active strategy: {summary_value(summary_rows, 'active_strategy')}",
        f"Active ticker: {summary_value(summary_rows, 'active_ticker')}",
        f"Previous seed: {summary_value(summary_rows, 'previous_seed_strategy')}:{summary_value(summary_rows, 'previous_seed_ticker')}",
        f"Previous-seed saved position: {summary_value(summary_rows, 'saved_position_state')} quantity={summary_value(summary_rows, 'saved_position_quantity')}",
        f"Previous-seed alignment state: {summary_value(summary_rows, 'alignment_state')}",
        f"Follow-up policy status: {summary_value(summary_rows, 'followup_policy_status')}",
        f"No action required: {summary_value(summary_rows, 'no_action_required')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved summary/components/blockers to {output_paths['summary']}; {output_paths['components']}; {output_paths['blockers']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
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
