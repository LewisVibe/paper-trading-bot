"""Saved-output QQQ100 daily decision report.

This report interprets saved QQQ100 paper-live evidence only. It does not call
Alpaca, read live positions, refresh market data, create executable order
instructions, submit/cancel/replace orders, write SQLite, send alerts, schedule
anything, or approve follow-up/repeat execution.
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
    "report": Path("data/qqq100_daily_decision_report.csv"),
    "summary": Path("data/qqq100_daily_decision_summary.csv"),
    "blockers": Path("data/qqq100_daily_decision_blockers.csv"),
    "evidence": Path("data/qqq100_daily_decision_evidence.csv"),
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
    "daily_decision_status",
    "active_strategy",
    "active_ticker",
    "desired_state",
    "saved_position_state",
    "saved_position_quantity",
    "alignment_state",
    "followup_policy_status",
    "no_action_required",
    "manual_discussion_status",
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
class Qqq100DailyDecision:
    active_strategy: str
    active_ticker: str
    desired_state: str
    saved_position_state: str
    saved_position_quantity: str
    alignment_state: str
    followup_policy_status: str
    no_action_required: bool
    daily_decision_status: str
    manual_discussion_status: str
    largest_blocker: str
    recommended_next_step: str


@dataclass
class Qqq100DailyDecisionReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_daily_decision_report(root_dir: Path | str = ".") -> Qqq100DailyDecisionReportResult:
    root = Path(root_dir)
    decision = evaluate_daily_decision(root)
    report_rows = build_report_rows(decision)
    summary_rows = build_summary_rows(decision)
    blocker_rows = build_blocker_rows(decision)
    evidence_rows = build_evidence_rows(decision)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return Qqq100DailyDecisionReportResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_qqq100_daily_decision_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "QQQ100 daily decision report is missing.",
            "Run `python bot.py --qqq100-daily-decision-report` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 daily decision saved display. Monitoring/report only; no orders approved.",
        f"daily_decision_status: {summary_value(rows, 'daily_decision_status')}",
        f"active_strategy: {summary_value(rows, 'active_strategy')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"desired_state: {summary_value(rows, 'desired_state')}",
        f"saved_position_state: {summary_value(rows, 'saved_position_state')}",
        f"saved_position_quantity: {summary_value(rows, 'saved_position_quantity')}",
        f"alignment_state: {summary_value(rows, 'alignment_state')}",
        f"followup_policy_status: {summary_value(rows, 'followup_policy_status')}",
        f"no_action_required: {summary_value(rows, 'no_action_required')}",
        f"manual_discussion_status: {summary_value(rows, 'manual_discussion_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def evaluate_daily_decision(root_dir: Path | str = ".") -> Qqq100DailyDecision:
    root = Path(root_dir)
    snapshot = evaluate_paper_live_saved_evidence(root)
    policy = evaluate_followup_policy(root)
    status = policy.final_policy_status

    if status == "no_action_required_already_aligned":
        daily_status = "qqq100_daily_decision_hold_no_action_aligned_long"
        manual_status = "manual_trade_discussion_not_needed"
        blocker = "none_no_action_required"
        next_step = "hold_no_action_and_monitor_only"
    elif status == "no_action_required_already_flat":
        daily_status = "qqq100_daily_decision_hold_no_action_aligned_flat"
        manual_status = "manual_trade_discussion_not_needed"
        blocker = "none_no_action_required"
        next_step = "hold_no_action_and_monitor_only"
    elif status == "future_manual_buy_discussion_possible":
        daily_status = "qqq100_daily_decision_manual_buy_discussion_possible_not_approved"
        manual_status = "manual_buy_discussion_possible_after_separate_approval"
        blocker = "manual_buy_not_approved_by_daily_decision"
        next_step = "separate_manual_buy_readiness_review_required_before_any_action"
    elif status == "future_manual_flatten_discussion_possible":
        daily_status = "qqq100_daily_decision_manual_flatten_discussion_possible_not_approved"
        manual_status = "manual_flatten_discussion_possible_after_separate_approval"
        blocker = "manual_flatten_not_approved_by_daily_decision"
        next_step = "separate_manual_flatten_readiness_review_required_before_any_action"
    else:
        daily_status = "qqq100_daily_decision_blocked_manual_review_required"
        manual_status = "manual_review_required_before_any_trade_discussion"
        blocker = policy.blocker or "missing_or_contradictory_saved_evidence"
        next_step = policy.recommended_next_step or "manual_review_required_before_any_action"

    return Qqq100DailyDecision(
        active_strategy=STRATEGY_NAME,
        active_ticker=TICKER,
        desired_state=snapshot.desired_state,
        saved_position_state=snapshot.saved_current_position_state,
        saved_position_quantity=snapshot.saved_current_position_quantity,
        alignment_state=snapshot.current_alignment_state,
        followup_policy_status=status,
        no_action_required=policy.no_action_required,
        daily_decision_status=daily_status,
        manual_discussion_status=manual_status,
        largest_blocker=blocker,
        recommended_next_step=next_step,
    )


def build_report_rows(decision: Qqq100DailyDecision) -> list[dict[str, Any]]:
    return [
        report_row("qqq100_daily_decision", decision),
        report_row("execution_boundary", decision, "execution_not_approved"),
        report_row("scheduling_boundary", decision, "scheduling_not_approved"),
    ]


def build_summary_rows(decision: Qqq100DailyDecision) -> list[dict[str, Any]]:
    rows = [
        ("daily_decision_status", decision.daily_decision_status, "Saved-output QQQ100 daily decision status."),
        ("active_strategy", decision.active_strategy, "Only qqq_100_trend_gate is in scope."),
        ("active_ticker", decision.active_ticker, "Only QQQ is in scope."),
        ("desired_state", decision.desired_state, "Saved desired QQQ100 state."),
        ("saved_position_state", decision.saved_position_state, "Saved QQQ paper position state."),
        ("saved_position_quantity", decision.saved_position_quantity, "Saved absolute QQQ quantity."),
        ("alignment_state", decision.alignment_state, "Saved QQQ alignment state."),
        ("followup_policy_status", decision.followup_policy_status, "Saved follow-up/no-action policy status."),
        ("no_action_required", str(decision.no_action_required), "True only when saved state says no paper action is needed."),
        ("manual_discussion_status", decision.manual_discussion_status, "Manual discussion status; never order approval."),
        ("largest_blocker", decision.largest_blocker, "Largest blocker or no-action marker."),
        ("recommended_next_step", decision.recommended_next_step, "Monitoring recommendation; never an order instruction."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("repeat_execution_approved", "False", "Repeat execution approval remains false."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must never be scheduled."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(decision: Qqq100DailyDecision) -> list[dict[str, Any]]:
    rows = [
        ("execution_not_approved", "blocked", "critical", "Daily decision does not approve execution.", "Do not run QQQ100 paper execution from this report."),
        ("followup_order_not_approved", "blocked", "critical", "Daily decision does not approve follow-up orders.", "Do not create order instructions."),
        ("repeat_execution_not_approved", "blocked", "critical", "Daily decision does not approve repeat execution.", "Do not repeat QQQ100 paper execution."),
        ("scheduling_not_approved", "blocked", "critical", "Order-capable scheduling remains prohibited.", "Do not schedule order-capable commands."),
    ]
    if decision.largest_blocker != "none_no_action_required":
        rows.insert(
            0,
            (
                decision.largest_blocker,
                "manual_review_required",
                "high",
                f"Daily decision status: {decision.daily_decision_status}.",
                decision.recommended_next_step,
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


def build_evidence_rows(decision: Qqq100DailyDecision) -> list[dict[str, Any]]:
    values = [
        ("desired_state", decision.desired_state, "Saved desired position."),
        ("saved_position_state", decision.saved_position_state, "Saved paper position state."),
        ("saved_position_quantity", decision.saved_position_quantity, "Saved absolute QQQ quantity."),
        ("alignment_state", decision.alignment_state, "Saved alignment state."),
        ("followup_policy_status", decision.followup_policy_status, "Saved follow-up/no-action policy."),
        ("daily_decision_status", decision.daily_decision_status, "Daily decision result."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in values]


def report_row(
    check_name: str,
    decision: Qqq100DailyDecision,
    override_status: str | None = None,
) -> dict[str, Any]:
    return {
        "check_name": check_name,
        "daily_decision_status": override_status or decision.daily_decision_status,
        "active_strategy": decision.active_strategy,
        "active_ticker": decision.active_ticker,
        "desired_state": decision.desired_state,
        "saved_position_state": decision.saved_position_state,
        "saved_position_quantity": decision.saved_position_quantity,
        "alignment_state": decision.alignment_state,
        "followup_policy_status": decision.followup_policy_status,
        "no_action_required": decision.no_action_required,
        "manual_discussion_status": decision.manual_discussion_status,
        "largest_blocker": decision.largest_blocker,
        "recommended_next_step": decision.recommended_next_step,
        **ROW_SAFETY,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ100 daily decision report complete. Saved-output monitoring/report only; no orders approved.",
        f"Daily decision status: {summary_value(summary_rows, 'daily_decision_status')}",
        f"Active strategy: {summary_value(summary_rows, 'active_strategy')}",
        f"Active ticker: {summary_value(summary_rows, 'active_ticker')}",
        f"Desired state: {summary_value(summary_rows, 'desired_state')}",
        f"Saved position: {summary_value(summary_rows, 'saved_position_state')} quantity={summary_value(summary_rows, 'saved_position_quantity')}",
        f"Alignment state: {summary_value(summary_rows, 'alignment_state')}",
        f"Follow-up policy status: {summary_value(summary_rows, 'followup_policy_status')}",
        f"No action required: {summary_value(summary_rows, 'no_action_required')}",
        f"Manual discussion status: {summary_value(summary_rows, 'manual_discussion_status')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report/summary/blockers/evidence to {output_paths['report']}; {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
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
