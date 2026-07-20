"""Saved-output closeout checkpoint for the current paper-live seed phase.

This report reads saved paper-live monitoring plus exact ticket, execution, and postcheck summaries. It does not call
Alpaca, read live positions, refresh market data, write SQLite, send alerts,
schedule anything, create executable order instructions, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_STRATEGY_NAME = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_STRATEGY_NAME = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"
PAPER_LIVE_MONITORING_SUMMARY = Path("data/paper_live_monitoring_status.csv")
DEFENSIVE_MANUAL_REVIEW_SUMMARY = Path("data/paper_live_defensive_sleeve_manual_review_summary.csv")
DEFENSIVE_PREVIEW_READINESS_SUMMARY = Path("data/paper_live_defensive_sleeve_preview_readiness_summary.csv")
VOL_TARGETED_PAPER_TICKET_SUMMARY = Path("data/vol_targeted_growth_paper_ticket_summary.csv")
VOL_TARGETED_PAPER_EXECUTION_SUMMARY = Path("data/vol_targeted_growth_paper_execution_summary.csv")
VOL_TARGETED_PAPER_POSTCHECK_SUMMARY = Path("data/vol_targeted_growth_paper_postcheck_summary.csv")

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
    "paper_ticket_present",
    "paper_ticket_id",
    "paper_ticket_execution_ready",
    "paper_ticket_blockers",
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
    paper_ticket_present: str
    paper_ticket_id: str
    paper_ticket_execution_ready: str
    paper_ticket_blockers: str
    paper_execution_status: str
    paper_postcheck_status: str
    paper_cycle_complete: str
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
        f"paper_ticket_present: {summary_value(rows, 'paper_ticket_present')}",
        f"paper_ticket_id: {summary_value(rows, 'paper_ticket_id')}",
        f"paper_ticket_execution_ready: {summary_value(rows, 'paper_ticket_execution_ready')}",
        f"paper_ticket_blockers: {summary_value(rows, 'paper_ticket_blockers')}",
        f"paper_execution_status: {summary_value(rows, 'paper_execution_status')}",
        f"paper_postcheck_status: {summary_value(rows, 'paper_postcheck_status')}",
        f"paper_cycle_complete: {summary_value(rows, 'paper_cycle_complete')}",
        f"previous_seed_monitoring_recommended_next_step: {summary_value(rows, 'current_monitoring_recommended_next_step')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_checklist_snapshot(root: Path) -> PaperLiveChecklistSnapshot:
    rows = read_csv_rows(root / PAPER_LIVE_MONITORING_SUMMARY)
    values = {row.get("summary_name", ""): str(row.get("summary_value", "")).strip() for row in rows}
    active_strategy = values.get("active_strategy") or ACTIVE_STRATEGY_NAME
    active_ticker = values.get("active_ticker") or ACTIVE_TICKER
    previous_seed_strategy = values.get("previous_seed_strategy") or PREVIOUS_STRATEGY_NAME
    previous_seed_ticker = values.get("previous_seed_ticker") or PREVIOUS_TICKER
    saved_position_state = values.get("saved_position_state") or "missing_saved_evidence"
    saved_position_quantity = values.get("saved_position_quantity") or "missing_saved_evidence"
    alignment_state = values.get("alignment_state") or "missing_saved_evidence"
    followup_policy_status = values.get("followup_policy_status") or "missing_saved_evidence"
    no_action_required = values.get("no_action_required") or "False"
    recommended = values.get("recommended_next_step") or "regenerate_report_only_paper_live_monitoring_status"
    defensive_manual = read_summary_value(root / DEFENSIVE_MANUAL_REVIEW_SUMMARY, "final_manual_review_status") or "not_run"
    defensive_preview = read_summary_value(root / DEFENSIVE_PREVIEW_READINESS_SUMMARY, "final_preview_readiness_status") or "not_run"
    defensive_preview_candidate = read_summary_value(root / DEFENSIVE_PREVIEW_READINESS_SUMMARY, "preview_candidate_status") or "defensive_preview_candidate_not_approved"
    ticket_rows = read_csv_rows(root / VOL_TARGETED_PAPER_TICKET_SUMMARY)
    paper_ticket_present = str(bool(ticket_rows))
    paper_ticket_id = summary_value(ticket_rows, "ticket_id") or "missing"
    paper_ticket_execution_ready = summary_value(ticket_rows, "execution_ready") or "False"
    paper_ticket_blockers = summary_value(ticket_rows, "blockers") or "missing"
    execution_rows = read_csv_rows(root / VOL_TARGETED_PAPER_EXECUTION_SUMMARY)
    postcheck_rows = read_csv_rows(root / VOL_TARGETED_PAPER_POSTCHECK_SUMMARY)
    execution_ticket_id = summary_value(execution_rows, "ticket_id")
    postcheck_ticket_id = summary_value(postcheck_rows, "ticket_id")
    paper_execution_status = summary_value(execution_rows, "execution_status") or "not_run"
    paper_postcheck_status = summary_value(postcheck_rows, "postcheck_status") or "not_run"
    submitted_order_count = parse_int(summary_value(execution_rows, "submitted_order_count"))
    filled_order_count = parse_int(summary_value(execution_rows, "filled_order_count"))
    aligned_symbol_count = parse_int(summary_value(postcheck_rows, "aligned_symbol_count"))
    symbol_count = parse_int(summary_value(postcheck_rows, "symbol_count"))
    paper_cycle_complete = (
        bool(ticket_rows)
        and paper_ticket_id not in {"", "missing"}
        and paper_ticket_id == execution_ticket_id == postcheck_ticket_id
        and paper_execution_status == "filled"
        and submitted_order_count > 0
        and submitted_order_count == filled_order_count
        and paper_postcheck_status == "aligned"
        and symbol_count > 0
        and aligned_symbol_count == symbol_count
    )

    evidence_complete = (
        active_strategy == ACTIVE_STRATEGY_NAME
        and active_ticker == ACTIVE_TICKER
        and previous_seed_strategy == PREVIOUS_STRATEGY_NAME
        and previous_seed_ticker == PREVIOUS_TICKER
        and saved_position_state == "paper_position_long"
        and saved_position_quantity == "1"
        and alignment_state == "aligned_long"
        and followup_policy_status == "no_action_required_already_aligned"
        and no_action_required.lower() == "true"
        and recommended == "hold_no_action_and_monitor_only"
    )
    if evidence_complete:
        if paper_cycle_complete:
            paper_live_monitoring_status = "vol_targeted_paper_cycle_filled_postcheck_aligned"
            checklist_phase_status = "paper_live_checklist_complete_user_hermes_setup_pending"
            next_step = "configure_user_owned_hermes_status_cron_and_monitor_only"
        elif ticket_rows:
            paper_live_monitoring_status = "vol_targeted_manual_paper_path_implemented_exact_confirmation_pending"
            checklist_phase_status = "paper_live_checklist_code_complete_market_hours_confirmation_pending"
            if paper_ticket_execution_ready == "True":
                next_step = "review_exact_ticket_then_request_final_user_confirmation"
            else:
                next_step = "prepare_fresh_market_hours_ticket_then_request_final_user_confirmation"
        else:
            paper_live_monitoring_status = "vol_targeted_manual_paper_path_implemented_ticket_preparation_pending"
            checklist_phase_status = "paper_live_checklist_code_complete_ticket_preparation_pending"
            next_step = "prepare_fresh_market_hours_ticket_then_request_final_user_confirmation"
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
        paper_ticket_present=paper_ticket_present,
        paper_ticket_id=paper_ticket_id,
        paper_ticket_execution_ready=paper_ticket_execution_ready,
        paper_ticket_blockers=paper_ticket_blockers,
        paper_execution_status=paper_execution_status,
        paper_postcheck_status=paper_postcheck_status,
        paper_cycle_complete=str(paper_cycle_complete),
        next_safe_development_step=next_step,
    )


def build_report_rows(snapshot: PaperLiveChecklistSnapshot) -> list[dict[str, Any]]:
    steps = [
        ("1", "baseline_freeze", "complete", "Baseline, pytest foundation, and paper-only boundaries are established."),
        ("2", "test_foundation", "complete", "Pure/no-network pytest foundation exists and remains part of verification."),
        ("3", "active_seed_status", "complete", "Active status seed is higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x / MULTI_SLEEVE; QQQ100 is retained as previous-seed context."),
        ("4", "paper_only_boundary", "complete", "Alpaca paper-only and no-live-trading boundaries remain documented."),
        ("5", "owner_scope_approval", "complete", "Owner approved the $100,000 maximum, four managed symbols, untouched unrelated positions, and paper-only boundary."),
        ("6", "sleeve_symbol_mapping", "complete", "QQQ/MGK/IBIT/SGOV map to the approved 70/20/5/5 base sleeves."),
        ("7", "readonly_broker_and_price_path", "complete", "Read-only Alpaca account, position, order, asset, and market-data checks are implemented."),
        ("8", "deterministic_ticket", "complete", "A hashed semantic ticket uses completed-session volatility, fresh prices, and non-leveraged account capacity."),
        ("9", "manual_paper_execution_path", "complete", "The volatility-targeted path is isolated, paper-only, kill-switch protected, and gateway routed."),
        ("10", "execution_and_postcheck_gates", "complete", "Confirmation-time state checks, deterministic client IDs, fill stopping, and read-only reconciliation are implemented."),
        (
            "11",
            "fresh_ticket_final_confirmation",
            "complete_filled_and_postcheck_aligned" if snapshot.paper_cycle_complete == "True" else "pending_market_hours_and_final_user_confirmation",
            "The exact confirmed paper ticket filled and the read-only postcheck is aligned."
            if snapshot.paper_cycle_complete == "True"
            else "No order is approved until a fresh market-hours ticket is reviewed and explicitly confirmed.",
        ),
        ("12", "monitoring_only_scheduling_boundary", "boundary_complete_user_hermes_setup_pending", "Execution commands are forbidden from scheduling; user-owned Hermes status setup remains external."),
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
            "paper_ticket_present": snapshot.paper_ticket_present,
            "paper_ticket_id": snapshot.paper_ticket_id,
            "paper_ticket_execution_ready": snapshot.paper_ticket_execution_ready,
            "paper_ticket_blockers": snapshot.paper_ticket_blockers,
            "finding": finding,
            "next_safe_development_step": snapshot.next_safe_development_step,
            **ROW_SAFETY,
        }
        for step, name, status, finding in steps
    ]


def build_summary_rows(snapshot: PaperLiveChecklistSnapshot) -> list[dict[str, Any]]:
    rows = [
        ("checklist_phase_status", snapshot.checklist_phase_status, "Closeout status for the current report/status seed phase."),
        ("active_strategy", snapshot.active_strategy, "Current paper-live monitoring seed strategy."),
        ("active_ticker", snapshot.active_ticker, "Current paper-live monitoring seed instrument group."),
        ("previous_seed_strategy", PREVIOUS_STRATEGY_NAME, "Previous QQQ100 seed retained as saved context."),
        ("previous_seed_ticker", PREVIOUS_TICKER, "Previous QQQ100 seed ticker retained as saved context."),
        ("saved_position_state", snapshot.saved_position_state, "Saved QQQ paper position state from previous seed context."),
        ("saved_position_quantity", snapshot.saved_position_quantity, "Saved QQQ paper position quantity from previous seed context."),
        ("alignment_state", snapshot.alignment_state, "Saved QQQ100 previous-seed alignment state."),
        ("followup_policy_status", snapshot.followup_policy_status, "Saved QQQ100 previous-seed follow-up/no-action policy status."),
        ("no_action_required", snapshot.no_action_required, "True when current saved previous-seed state needs no QQQ paper action."),
        ("defensive_sleeve_manual_review_status", snapshot.defensive_sleeve_manual_review_status, "Saved defensive sleeve manual review status."),
        ("defensive_sleeve_preview_readiness_status", snapshot.defensive_sleeve_preview_readiness_status, "Saved defensive sleeve preview-readiness status."),
        ("defensive_sleeve_preview_candidate_status", snapshot.defensive_sleeve_preview_candidate_status, "Defensive sleeve preview candidate approval remains blocked."),
        ("paper_live_monitoring_status", snapshot.paper_live_monitoring_status, "Saved paper-live monitor interpretation."),
        ("paper_ticket_present", snapshot.paper_ticket_present, "Whether a saved exact volatility paper ticket exists."),
        ("paper_ticket_id", snapshot.paper_ticket_id, "Latest saved exact ticket identifier; not approval."),
        ("paper_ticket_execution_ready", snapshot.paper_ticket_execution_ready, "True only when the latest saved ticket passed preparation checks."),
        ("paper_ticket_blockers", snapshot.paper_ticket_blockers, "Latest saved ticket blockers."),
        ("current_monitoring_recommended_next_step", snapshot.recommended_next_step, "Saved paper-live monitoring recommendation."),
        ("steps_1_to_10_status", "complete", "Implementation and verification are complete through the guarded manual execution path."),
        (
            "step_11_status",
            "complete_filled_and_postcheck_aligned" if snapshot.paper_cycle_complete == "True" else "pending_market_hours_and_final_user_confirmation",
            "The confirmed paper basket filled and reconciled exactly."
            if snapshot.paper_cycle_complete == "True"
            else "A fresh exact market-hours ticket and final user confirmation are still required.",
        ),
        ("paper_execution_status", snapshot.paper_execution_status, "Saved execution result for the latest exact ticket."),
        ("paper_postcheck_status", snapshot.paper_postcheck_status, "Saved read-only reconciliation result for the latest exact ticket."),
        ("paper_cycle_complete", snapshot.paper_cycle_complete, "True only when matching ticket, filled execution, and aligned postcheck evidence agree."),
        ("step_12_status", "boundary_complete_user_hermes_setup_pending", "Scheduling boundaries are complete; user-owned Hermes status setup remains external."),
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
        ("scheduling_not_approved", "blocked", "critical", "Scheduling remains monitoring-only; order-capable commands must never be scheduled.", "Do not create, edit, trigger, or schedule execution commands."),
        ("live_trading_not_approved", "blocked", "critical", "Live-money trading remains outside project scope.", "Keep Alpaca paper-only boundaries."),
        ("repeat_execution_not_approved", "blocked", "critical", "A completed paper cycle does not approve a repeat or follow-up order.", "Require a new fresh ticket and exact confirmation for any future rebalance."),
    ]
    if snapshot.paper_cycle_complete != "True":
        rows.insert(
            0,
            ("exact_ticket_confirmation_pending", "blocked", "critical", "No current order is approved without a fresh exact ticket and final user confirmation.", snapshot.next_safe_development_step),
        )
    if snapshot.paper_ticket_execution_ready != "True":
        rows.insert(
            1,
            (
                "fresh_market_hours_ticket_required",
                "blocked",
                "high",
                f"Latest ticket {snapshot.paper_ticket_id} is not executable: {snapshot.paper_ticket_blockers}",
                "Prepare a new ticket during an open U.S. market session.",
            ),
        )
    if snapshot.checklist_phase_status == "paper_live_checklist_manual_review_required":
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
        ("latest_exact_paper_ticket", f"present={snapshot.paper_ticket_present}; id={snapshot.paper_ticket_id}; execution_ready={snapshot.paper_ticket_execution_ready}; blockers={snapshot.paper_ticket_blockers}", "Saved ticket context only; this report cannot approve or submit it."),
        ("latest_paper_cycle", f"execution={snapshot.paper_execution_status}; postcheck={snapshot.paper_postcheck_status}; complete={snapshot.paper_cycle_complete}", "Completion requires matching ticket IDs, all submitted orders filled, and every managed symbol aligned."),
        ("current_scheduling_boundary", "monitoring_only; never_schedule_order_capable_commands=True", "Hermes/VPS scheduling remains status/report-only."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live checklist status complete. Report only; no orders approved.",
        f"Checklist phase status: {summary_value(summary_rows, 'checklist_phase_status')}",
        f"Active strategy: {summary_value(summary_rows, 'active_strategy')}",
        f"Active ticker: {summary_value(summary_rows, 'active_ticker')}",
        f"Previous seed strategy: {summary_value(summary_rows, 'previous_seed_strategy')}",
        f"Previous seed ticker: {summary_value(summary_rows, 'previous_seed_ticker')}",
        f"Saved position: {summary_value(summary_rows, 'saved_position_state')} quantity={summary_value(summary_rows, 'saved_position_quantity')}",
        f"Alignment state: {summary_value(summary_rows, 'alignment_state')}",
        f"Follow-up policy status: {summary_value(summary_rows, 'followup_policy_status')}",
        f"Defensive sleeve manual review status: {summary_value(summary_rows, 'defensive_sleeve_manual_review_status')}",
        f"Defensive sleeve preview readiness status: {summary_value(summary_rows, 'defensive_sleeve_preview_readiness_status')}",
        f"Defensive sleeve preview candidate status: {summary_value(summary_rows, 'defensive_sleeve_preview_candidate_status')}",
        f"No action required: {summary_value(summary_rows, 'no_action_required')}",
        f"Paper-live monitoring status: {summary_value(summary_rows, 'paper_live_monitoring_status')}",
        f"Latest paper ticket: {summary_value(summary_rows, 'paper_ticket_id')} ready={summary_value(summary_rows, 'paper_ticket_execution_ready')}",
        f"Latest paper ticket blockers: {summary_value(summary_rows, 'paper_ticket_blockers')}",
        f"Paper execution status: {summary_value(summary_rows, 'paper_execution_status')}",
        f"Paper postcheck status: {summary_value(summary_rows, 'paper_postcheck_status')}",
        f"Paper cycle complete: {summary_value(summary_rows, 'paper_cycle_complete')}",
        f"Previous-seed monitoring recommendation: {summary_value(summary_rows, 'current_monitoring_recommended_next_step')}",
        f"Step 11 status: {summary_value(summary_rows, 'step_11_status')}",
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


def parse_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


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
