"""Saved-output closeout checkpoint for the current QQQ100 paper-live phase.

This report reads saved paper-live monitoring evidence only. It does not call
Alpaca, read live positions, refresh market data, write SQLite, send alerts,
schedule anything, create executable order instructions, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"
PAPER_LIVE_MONITORING_SUMMARY = Path("data/paper_live_monitoring_status.csv")
DEFENSIVE_MANUAL_REVIEW_SUMMARY = Path("data/paper_live_defensive_sleeve_manual_review_summary.csv")
DEFENSIVE_PREVIEW_READINESS_SUMMARY = Path("data/paper_live_defensive_sleeve_preview_readiness_summary.csv")

OUTPUT_FILES = {
    "report": Path("data/paper_live_checklist_status.csv"),
    "summary": Path("data/paper_live_checklist_status_summary.csv"),
    "blockers": Path("data/paper_live_checklist_status_blockers.csv"),
    "evidence": Path("data/paper_live_checklist_status_evidence.csv"),
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

REPORT_COLUMNS = [
    "checklist_step",
    "step_name",
    "step_status",
    "active_strategy",
    "active_ticker",
    "saved_position_state",
    "saved_position_quantity",
    "alignment_state",
    "followup_policy_status",
    "no_action_required",
    "defensive_sleeve_manual_review_status",
    "defensive_sleeve_preview_readiness_status",
    "defensive_sleeve_preview_candidate_status",
    "paper_live_monitoring_status",
    "checklist_phase_status",
    "finding",
    "next_safe_development_step",
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

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
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

EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_value",
    "details",
    *SAFETY_FLAGS.keys(),
]


@dataclass(frozen=True)
class PaperLiveChecklistSnapshot:
    active_strategy: str
    active_ticker: str
    saved_position_state: str
    saved_position_quantity: str
    alignment_state: str
    followup_policy_status: str
    no_action_required: str
    defensive_sleeve_manual_review_status: str
    defensive_sleeve_preview_readiness_status: str
    defensive_sleeve_preview_candidate_status: str
    recommended_next_step: str
    paper_live_monitoring_status: str
    checklist_phase_status: str
    next_safe_development_step: str


@dataclass
class PaperLiveChecklistStatusResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_checklist_status(root_dir: Path | str = ".") -> PaperLiveChecklistStatusResult:
    root = Path(root_dir)
    snapshot = build_checklist_snapshot(root)
    report_rows = build_report_rows(snapshot)
    summary_rows = build_summary_rows(snapshot)
    blocker_rows = build_blocker_rows(snapshot)
    evidence_rows = build_evidence_rows(snapshot)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveChecklistStatusResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_checklist_status(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live checklist status is missing.",
            "Run `python bot.py --paper-live-checklist-status` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live checklist status saved display. Report only; no orders approved.",
        f"checklist_phase_status: {summary_value(rows, 'checklist_phase_status')}",
        f"active_strategy: {summary_value(rows, 'active_strategy')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"saved_position_state: {summary_value(rows, 'saved_position_state')}",
        f"saved_position_quantity: {summary_value(rows, 'saved_position_quantity')}",
        f"alignment_state: {summary_value(rows, 'alignment_state')}",
        f"followup_policy_status: {summary_value(rows, 'followup_policy_status')}",
        f"defensive_sleeve_manual_review_status: {summary_value(rows, 'defensive_sleeve_manual_review_status')}",
        f"defensive_sleeve_preview_readiness_status: {summary_value(rows, 'defensive_sleeve_preview_readiness_status')}",
        f"defensive_sleeve_preview_candidate_status: {summary_value(rows, 'defensive_sleeve_preview_candidate_status')}",
        f"no_action_required: {summary_value(rows, 'no_action_required')}",
        f"paper_live_monitoring_status: {summary_value(rows, 'paper_live_monitoring_status')}",
        f"current_monitoring_recommended_next_step: {summary_value(rows, 'current_monitoring_recommended_next_step')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_checklist_snapshot(root: Path) -> PaperLiveChecklistSnapshot:
    rows = read_csv_rows(root / PAPER_LIVE_MONITORING_SUMMARY)
    values = {row.get("summary_name", ""): str(row.get("summary_value", "")).strip() for row in rows}
    active_strategy = values.get("active_strategy") or STRATEGY_NAME
    active_ticker = values.get("active_ticker") or TICKER
    saved_position_state = values.get("saved_position_state") or "missing_saved_evidence"
    saved_position_quantity = values.get("saved_position_quantity") or "missing_saved_evidence"
    alignment_state = values.get("alignment_state") or "missing_saved_evidence"
    followup_policy_status = values.get("followup_policy_status") or "missing_saved_evidence"
    no_action_required = values.get("no_action_required") or "False"
    recommended = values.get("recommended_next_step") or "regenerate_report_only_paper_live_monitoring_status"
    defensive_manual = read_summary_value(root / DEFENSIVE_MANUAL_REVIEW_SUMMARY, "final_manual_review_status") or "not_run"
    defensive_preview = read_summary_value(root / DEFENSIVE_PREVIEW_READINESS_SUMMARY, "final_preview_readiness_status") or "not_run"
    defensive_preview_candidate = read_summary_value(root / DEFENSIVE_PREVIEW_READINESS_SUMMARY, "preview_candidate_status") or "defensive_preview_candidate_not_approved"

    evidence_complete = (
        active_strategy == STRATEGY_NAME
        and active_ticker == TICKER
        and saved_position_state == "paper_position_long"
        and saved_position_quantity == "1"
        and alignment_state == "aligned_long"
        and followup_policy_status == "no_action_required_already_aligned"
        and no_action_required.lower() == "true"
        and recommended == "hold_no_action_and_monitor_only"
    )
    if evidence_complete:
        paper_live_monitoring_status = "qqq100_aligned_long_one_monitor_only"
        checklist_phase_status = "paper_live_checklist_current_qqq100_monitoring_phase_closed_out"
        if defensive_preview == "defensive_sleeve_preview_candidate_not_approved_manual_review_required":
            next_step = "manual_review_defensive_sleeve_before_any_preview_or_candidate_label_change"
        elif defensive_manual == "defensive_sleeve_manual_review_required":
            next_step = "run_defensive_sleeve_preview_readiness_checkpoint_before_candidate_label_change"
        else:
            next_step = "continue_monitoring_only_then_review_future_f6_f7_or_generic_promotion_ladder_separately"
    else:
        paper_live_monitoring_status = "paper_live_monitoring_saved_evidence_missing_or_inconsistent"
        checklist_phase_status = "paper_live_checklist_manual_review_required"
        next_step = "regenerate_or_review_saved_report_only_paper_live_monitoring_status"

    return PaperLiveChecklistSnapshot(
        active_strategy=active_strategy,
        active_ticker=active_ticker,
        saved_position_state=saved_position_state,
        saved_position_quantity=saved_position_quantity,
        alignment_state=alignment_state,
        followup_policy_status=followup_policy_status,
        no_action_required=no_action_required,
        defensive_sleeve_manual_review_status=defensive_manual,
        defensive_sleeve_preview_readiness_status=defensive_preview,
        defensive_sleeve_preview_candidate_status=defensive_preview_candidate,
        recommended_next_step=recommended,
        paper_live_monitoring_status=paper_live_monitoring_status,
        checklist_phase_status=checklist_phase_status,
        next_safe_development_step=next_step,
    )


def build_report_rows(snapshot: PaperLiveChecklistSnapshot) -> list[dict[str, Any]]:
    steps = [
        ("1", "baseline_freeze", "complete", "Baseline, pytest foundation, and paper-only boundaries are established."),
        ("2", "test_foundation", "complete", "Pure/no-network pytest foundation exists and remains part of verification."),
        ("3", "qqq100_candidate_scope", "complete", "First paper-live candidate remains qqq_100_trend_gate / QQQ only."),
        ("4", "paper_only_boundary", "complete", "Alpaca paper-only and no-live-trading boundaries remain documented."),
        ("5", "execution_gate_boundaries", "complete", "Order-capable commands remain separate and confirmation-gated."),
        ("6", "qqq100_exact_alignment", "complete", "QQQ100 exact zero/one-share alignment is enforced by saved evidence checks."),
        ("7", "saved_evidence_reconciliation", "complete", "Saved postcheck/evidence audit state reconciles aligned long one share."),
        ("8", "manual_paper_execution_narrowness", "complete_for_current_qqq100_monitoring_phase", "No broad strategy-to-execution path was added."),
        ("9", "post_execution_verification", "complete_for_current_qqq100_monitoring_phase", "Read-only postcheck evidence exists in saved state."),
        ("10", "followup_no_action_policy", "complete", "Follow-up policy says no action required and do not repeat buy."),
        ("11", "monitoring_only_scheduling_boundary", "complete", "VPS/Hermes daily monitoring includes saved QQQ100 status without cron changes."),
        ("12", "generic_promotion_ladder", "future_only", "Generic promotion ladder is not built in this phase; start QQQ100 only later if separately approved."),
    ]
    return [
        {
            "checklist_step": step,
            "step_name": name,
            "step_status": status,
            "active_strategy": snapshot.active_strategy,
            "active_ticker": snapshot.active_ticker,
            "saved_position_state": snapshot.saved_position_state,
            "saved_position_quantity": snapshot.saved_position_quantity,
            "alignment_state": snapshot.alignment_state,
            "followup_policy_status": snapshot.followup_policy_status,
            "no_action_required": snapshot.no_action_required,
            "defensive_sleeve_manual_review_status": snapshot.defensive_sleeve_manual_review_status,
            "defensive_sleeve_preview_readiness_status": snapshot.defensive_sleeve_preview_readiness_status,
            "defensive_sleeve_preview_candidate_status": snapshot.defensive_sleeve_preview_candidate_status,
            "paper_live_monitoring_status": snapshot.paper_live_monitoring_status,
            "checklist_phase_status": snapshot.checklist_phase_status,
            "finding": finding,
            "next_safe_development_step": snapshot.next_safe_development_step,
            **ROW_SAFETY,
        }
        for step, name, status, finding in steps
    ]


def build_summary_rows(snapshot: PaperLiveChecklistSnapshot) -> list[dict[str, Any]]:
    rows = [
        ("checklist_phase_status", snapshot.checklist_phase_status, "Closeout status for the current QQQ100 paper-live monitoring phase."),
        ("active_strategy", snapshot.active_strategy, "Current paper-live monitoring strategy."),
        ("active_ticker", snapshot.active_ticker, "Current paper-live monitoring ticker."),
        ("saved_position_state", snapshot.saved_position_state, "Saved QQQ paper position state."),
        ("saved_position_quantity", snapshot.saved_position_quantity, "Saved QQQ paper position quantity."),
        ("alignment_state", snapshot.alignment_state, "Saved QQQ100 alignment state."),
        ("followup_policy_status", snapshot.followup_policy_status, "Saved QQQ100 follow-up/no-action policy status."),
        ("no_action_required", snapshot.no_action_required, "True when current saved state needs no QQQ paper action."),
        ("defensive_sleeve_manual_review_status", snapshot.defensive_sleeve_manual_review_status, "Saved defensive sleeve manual review status."),
        ("defensive_sleeve_preview_readiness_status", snapshot.defensive_sleeve_preview_readiness_status, "Saved defensive sleeve preview-readiness status."),
        ("defensive_sleeve_preview_candidate_status", snapshot.defensive_sleeve_preview_candidate_status, "Defensive sleeve preview candidate approval remains blocked."),
        ("paper_live_monitoring_status", snapshot.paper_live_monitoring_status, "Saved paper-live monitor interpretation."),
        ("current_monitoring_recommended_next_step", snapshot.recommended_next_step, "Saved paper-live monitoring recommendation."),
        ("steps_1_to_11_status", "complete_for_current_qqq100_monitoring_phase", "Current phase is closed out through Step 11."),
        ("step_12_status", "future_only", "Generic promotion ladder remains a separate future design."),
        ("next_safe_development_step", snapshot.next_safe_development_step, "Next safe development path; not an order instruction."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must never be scheduled."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("repeat_execution_approved", "False", "Repeat execution approval remains false."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(snapshot: PaperLiveChecklistSnapshot) -> list[dict[str, Any]]:
    rows = [
        ("repeat_or_followup_order_not_approved", "blocked", "critical", "No further QQQ order is needed while aligned long one share.", "Hold no action and monitor only."),
        ("paper_execution_not_approved", "blocked", "critical", "Paper execution approval remains false after this closeout.", "Use separate manual review before any future order discussion."),
        ("scheduling_not_approved", "blocked", "critical", "Scheduling remains monitoring-only; order-capable commands must never be scheduled.", "Do not create, edit, trigger, or schedule execution commands."),
        ("live_trading_not_approved", "blocked", "critical", "Live-money trading remains outside project scope.", "Keep Alpaca paper-only boundaries."),
        ("generic_promotion_ladder_future_only", "future_only", "medium", "Step 12 is intentionally not implemented in this checkpoint.", "Design a promotion ladder later, starting QQQ100 only."),
        ("defensive_sleeve_preview_not_approved", "blocked", "critical", "Defensive sleeve review/checkpoints do not approve a preview candidate, promotion, or execution.", "manual review required before any defensive preview label change."),
    ]
    if snapshot.checklist_phase_status != "paper_live_checklist_current_qqq100_monitoring_phase_closed_out":
        rows.insert(
            0,
            (
                "saved_paper_live_monitoring_evidence_incomplete",
                "manual_review_required",
                "high",
                "Saved paper-live monitoring status is missing or inconsistent.",
                "Regenerate or review report-only paper-live monitoring status before closeout.",
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


def build_evidence_rows(snapshot: PaperLiveChecklistSnapshot) -> list[dict[str, Any]]:
    rows = [
        ("paper_live_monitoring_summary_source", str(PAPER_LIVE_MONITORING_SUMMARY), "Saved-output source only; no broker read."),
        ("current_saved_alignment", f"{snapshot.saved_position_state}; quantity={snapshot.saved_position_quantity}; {snapshot.alignment_state}", "Explains why no further QQQ order is needed now."),
        ("current_followup_policy", f"{snapshot.followup_policy_status}; no_action_required={snapshot.no_action_required}", "Repeat/follow-up orders remain blocked."),
        ("defensive_sleeve_saved_review_state", f"manual={snapshot.defensive_sleeve_manual_review_status}; preview={snapshot.defensive_sleeve_preview_readiness_status}; candidate={snapshot.defensive_sleeve_preview_candidate_status}", "Defensive sleeve remains blocked from preview/execution."),
        ("current_scheduling_boundary", "monitoring_only; never_schedule_order_capable_commands=True", "Hermes/VPS scheduling remains status/report-only."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live checklist status complete. Report only; no orders approved.",
        f"Checklist phase status: {summary_value(summary_rows, 'checklist_phase_status')}",
        f"Active strategy: {summary_value(summary_rows, 'active_strategy')}",
        f"Active ticker: {summary_value(summary_rows, 'active_ticker')}",
        f"Saved position: {summary_value(summary_rows, 'saved_position_state')} quantity={summary_value(summary_rows, 'saved_position_quantity')}",
        f"Alignment state: {summary_value(summary_rows, 'alignment_state')}",
        f"Follow-up policy status: {summary_value(summary_rows, 'followup_policy_status')}",
        f"Defensive sleeve manual review status: {summary_value(summary_rows, 'defensive_sleeve_manual_review_status')}",
        f"Defensive sleeve preview readiness status: {summary_value(summary_rows, 'defensive_sleeve_preview_readiness_status')}",
        f"Defensive sleeve preview candidate status: {summary_value(summary_rows, 'defensive_sleeve_preview_candidate_status')}",
        f"No action required: {summary_value(summary_rows, 'no_action_required')}",
        f"Paper-live monitoring status: {summary_value(summary_rows, 'paper_live_monitoring_status')}",
        f"Current monitoring recommended next step: {summary_value(summary_rows, 'current_monitoring_recommended_next_step')}",
        f"Step 12 status: {summary_value(summary_rows, 'step_12_status')}",
        f"Next safe development step: {summary_value(summary_rows, 'next_safe_development_step')}",
        f"Saved report/summary/blockers/evidence to {output_paths['report']}; {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def read_summary_value(path: Path, key: str) -> str:
    return summary_value(read_csv_rows(path), key)


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
