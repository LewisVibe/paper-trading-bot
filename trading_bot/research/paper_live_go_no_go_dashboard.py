"""Saved-output paper-live go/no-go dashboard.

This dashboard reads saved status outputs only. It does not call Alpaca, read
positions, refresh market data, create order instructions, schedule anything,
or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "report": Path("data/paper_live_go_no_go_dashboard.csv"),
    "summary": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
    "blockers": Path("data/paper_live_go_no_go_dashboard_blockers.csv"),
    "evidence": Path("data/paper_live_go_no_go_dashboard_evidence.csv"),
}

INPUT_FILES = {
    "paper_live_monitoring": Path("data/paper_live_monitoring_status.csv"),
    "qqq100_daily_decision": Path("data/qqq100_daily_decision_summary.csv"),
    "vol_execution_blocker_rollup": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv"),
    "vol_post_gate_review": Path("data/vol_targeted_growth_post_gate_review_summary.csv"),
    "vol_ticket_value_design": Path("data/vol_targeted_growth_manual_ticket_value_design_summary.csv"),
    "vol_ticket_prereq_closeout": Path("data/vol_targeted_growth_executable_ticket_prerequisites_closeout_summary.csv"),
    "vol_ticket_approval_readiness": Path("data/vol_targeted_growth_executable_ticket_approval_readiness_summary.csv"),
    "vol_ticket_approval_criteria": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_summary.csv"),
    "vol_ticket_criteria_resolution": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_summary.csv"),
    "vol_ticket_criteria_source_review": Path("data/vol_targeted_growth_executable_ticket_criteria_source_review_summary.csv"),
    "vol_ticket_criteria_blocker_closeout_review": Path("data/vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_summary.csv"),
    "vol_ticket_blocker_specific_review_rollup": Path("data/vol_targeted_growth_executable_ticket_criteria_blocker_specific_review_rollup_summary.csv"),
    "vol_ticket_closeout_candidate_review_rollup": Path("data/vol_targeted_growth_executable_ticket_criteria_closeout_candidate_review_rollup_summary.csv"),
    "vol_ticket_criteria_source_closeout_approval_wording": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording_summary.csv"),
    "vol_ticket_criteria_source_closeout_record": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv"),
    "vol_ticket_criteria_resolution_plan_closeout_approval_wording": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_approval_wording_summary.csv"),
    "vol_ticket_criteria_resolution_plan_closeout_record": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_record_summary.csv"),
    "vol_ticket_approval_criteria_closeout_approval_wording": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_approval_wording_summary.csv"),
    "vol_ticket_approval_criteria_closeout_record": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_summary.csv"),
    "vol_ticket_final_blockers_closeout_approval_wording": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_approval_wording_summary.csv"),
    "vol_ticket_final_blockers_closeout_record": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_record_summary.csv"),
    "vol_execution_approval_request_readiness": Path("data/vol_targeted_growth_execution_approval_request_readiness_summary.csv"),
    "vol_execution_design_approval_wording": Path("data/vol_targeted_growth_execution_design_approval_wording_summary.csv"),
    "vol_execution_design_approval_record": Path("data/vol_targeted_growth_execution_design_approval_record_summary.csv"),
    "vol_non_submitting_executable_ticket_design": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design_summary.csv"),
    "paper_live_checklist": Path("data/paper_live_checklist_status_summary.csv"),
}

ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_SEED = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"
FINAL_STATUS = "paper_live_go_no_go_dashboard_execution_blocked_monitor_only"
NEXT_STEP = "manual_review_go_no_go_dashboard_before_any_future_execution_design"

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "monitoring_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "executable_ticket_created": False,
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
    "check_name",
    "status",
    "risk_level",
    "evidence",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class PaperLiveGoNoGoDashboardResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_go_no_go_dashboard(root_dir: Path | str = ".") -> PaperLiveGoNoGoDashboardResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(inputs, report_rows)
    blocker_rows = build_blocker_rows(inputs)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveGoNoGoDashboardResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_go_no_go_dashboard(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live go/no-go dashboard is missing.",
            "Run `python bot.py --paper-live-go-no-go-dashboard` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live go/no-go dashboard saved display. Report only; no execution approved.",
        f"final_go_no_go_status: {summary_value(rows, 'final_go_no_go_status')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"previous_seed: {summary_value(rows, 'previous_seed')}",
        f"previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"qqq100_daily_decision_status: {summary_value(rows, 'qqq100_daily_decision_status')}",
        f"qqq100_no_action_state: {summary_value(rows, 'qqq100_no_action_state')}",
        f"vol_execution_blocker_status: {summary_value(rows, 'vol_execution_blocker_status')}",
        f"vol_largest_blocker: {summary_value(rows, 'vol_largest_blocker')}",
        f"vol_post_gate_review_status: {summary_value(rows, 'vol_post_gate_review_status')}",
        f"vol_post_gate_review_decision: {summary_value(rows, 'vol_post_gate_review_decision')}",
        f"vol_post_gate_largest_blocker: {summary_value(rows, 'vol_post_gate_largest_blocker')}",
        f"vol_post_gate_saved_qqq_quantity: {summary_value(rows, 'vol_post_gate_saved_qqq_quantity')}",
        f"vol_ticket_value_design_status: {summary_value(rows, 'vol_ticket_value_design_status')}",
        f"vol_ticket_value_design_decision: {summary_value(rows, 'vol_ticket_value_design_decision')}",
        f"vol_ticket_value_largest_blocker: {summary_value(rows, 'vol_ticket_value_largest_blocker')}",
        f"vol_ticket_prereq_closeout_decision: {summary_value(rows, 'vol_ticket_prereq_closeout_decision')}",
        f"vol_ticket_approval_readiness_decision: {summary_value(rows, 'vol_ticket_approval_readiness_decision')}",
        f"vol_ticket_approval_criteria_decision: {summary_value(rows, 'vol_ticket_approval_criteria_decision')}",
        f"vol_ticket_criteria_resolution_decision: {summary_value(rows, 'vol_ticket_criteria_resolution_decision')}",
        f"vol_ticket_criteria_source_review_decision: {summary_value(rows, 'vol_ticket_criteria_source_review_decision')}",
        f"vol_ticket_criteria_blocker_closeout_review_decision: {summary_value(rows, 'vol_ticket_criteria_blocker_closeout_review_decision')}",
        f"vol_ticket_blocker_specific_review_rollup_decision: {summary_value(rows, 'vol_ticket_blocker_specific_review_rollup_decision')}",
        f"vol_ticket_closeout_candidate_review_rollup_decision: {summary_value(rows, 'vol_ticket_closeout_candidate_review_rollup_decision')}",
        f"vol_ticket_criteria_source_closeout_approval_wording_decision: {summary_value(rows, 'vol_ticket_criteria_source_closeout_approval_wording_decision')}",
        f"vol_ticket_criteria_source_closeout_future_phrase: {summary_value(rows, 'vol_ticket_criteria_source_closeout_future_phrase')}",
        f"vol_ticket_criteria_source_closeout_record_decision: {summary_value(rows, 'vol_ticket_criteria_source_closeout_record_decision')}",
        f"vol_ticket_criteria_source_closed_blocker: {summary_value(rows, 'vol_ticket_criteria_source_closed_blocker')}",
        f"vol_ticket_criteria_source_remaining_blockers: {summary_value(rows, 'vol_ticket_criteria_source_remaining_blockers')}",
        f"vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision')}",
        f"vol_ticket_criteria_resolution_plan_closeout_future_phrase: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_closeout_future_phrase')}",
        f"vol_ticket_criteria_resolution_plan_closeout_record_decision: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_closeout_record_decision')}",
        f"vol_ticket_criteria_resolution_plan_closed_blocker: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_closed_blocker')}",
        f"vol_ticket_criteria_resolution_plan_remaining_blockers: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_remaining_blockers')}",
        f"vol_ticket_approval_criteria_closeout_approval_wording_decision: {summary_value(rows, 'vol_ticket_approval_criteria_closeout_approval_wording_decision')}",
        f"vol_ticket_approval_criteria_closeout_future_phrase: {summary_value(rows, 'vol_ticket_approval_criteria_closeout_future_phrase')}",
        f"vol_ticket_approval_criteria_closeout_record_decision: {summary_value(rows, 'vol_ticket_approval_criteria_closeout_record_decision')}",
        f"vol_ticket_approval_criteria_closed_blocker: {summary_value(rows, 'vol_ticket_approval_criteria_closed_blocker')}",
        f"vol_ticket_approval_criteria_remaining_blockers: {summary_value(rows, 'vol_ticket_approval_criteria_remaining_blockers')}",
        f"vol_ticket_final_blockers_closeout_approval_wording_decision: {summary_value(rows, 'vol_ticket_final_blockers_closeout_approval_wording_decision')}",
        f"vol_ticket_final_blockers_closeout_future_phrase: {summary_value(rows, 'vol_ticket_final_blockers_closeout_future_phrase')}",
        f"vol_ticket_final_blockers_closeout_record_decision: {summary_value(rows, 'vol_ticket_final_blockers_closeout_record_decision')}",
        f"vol_ticket_final_blockers_closed_blocker: {summary_value(rows, 'vol_ticket_final_blockers_closed_blocker')}",
        f"vol_ticket_final_blockers_remaining_blockers: {summary_value(rows, 'vol_ticket_final_blockers_remaining_blockers')}",
        f"vol_execution_approval_request_readiness_decision: {summary_value(rows, 'vol_execution_approval_request_readiness_decision')}",
        f"vol_execution_approval_request_ready: {summary_value(rows, 'vol_execution_approval_request_ready')}",
        f"vol_execution_approval_requested: {summary_value(rows, 'vol_execution_approval_requested')}",
        f"vol_execution_approval_recorded: {summary_value(rows, 'vol_execution_approval_recorded')}",
        f"vol_execution_design_approval_wording_decision: {summary_value(rows, 'vol_execution_design_approval_wording_decision')}",
        f"vol_execution_design_approval_phrase: {summary_value(rows, 'vol_execution_design_approval_phrase')}",
        f"vol_execution_design_approval_record_decision: {summary_value(rows, 'vol_execution_design_approval_record_decision')}",
        f"vol_execution_design_approved: {summary_value(rows, 'vol_execution_design_approved')}",
        f"vol_non_submitting_executable_ticket_design_decision: {summary_value(rows, 'vol_non_submitting_executable_ticket_design_decision')}",
        f"vol_non_submitting_executable_ticket_order_values_populated: {summary_value(rows, 'vol_non_submitting_executable_ticket_order_values_populated')}",
        f"paper_live_checklist_phase_status: {summary_value(rows, 'paper_live_checklist_phase_status')}",
        f"vps_monitoring_status_assumption: {summary_value(rows, 'vps_monitoring_status_assumption')}",
        f"final_go_no_go_decision: {summary_value(rows, 'final_go_no_go_decision')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_instructions_created=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: saved-output dashboard only; no Alpaca, broker read, order, live trading, or scheduling approval.",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    qqq_status = summary_value(inputs["qqq100_daily_decision"], "daily_decision_status") or "missing_qqq100_daily_decision"
    vol_status = summary_value(inputs["vol_execution_blocker_rollup"], "final_execution_blocker_rollup_status") or "missing_vol_execution_blocker_rollup"
    post_gate_status = summary_value(inputs["vol_post_gate_review"], "final_post_gate_review_status") or "missing_vol_post_gate_review"
    checklist_status = summary_value(inputs["paper_live_checklist"], "checklist_phase_status") or "missing_paper_live_checklist"
    monitoring_recommended = summary_value(inputs["paper_live_monitoring"], "recommended_next_step") or "missing_paper_live_monitoring"
    return [
        report_row(
            "qqq100_previous_seed_state",
            "no_action_monitor_only" if qqq_status == "qqq100_daily_decision_hold_no_action_aligned_long" else "manual_review_required",
            "high",
            qqq_status,
            "QQQ100 is previous-seed context and should not repeat orders.",
            "hold_no_action_and_monitor_only",
        ),
        report_row(
            "volatility_active_seed_execution_state",
            "execution_blocked",
            "critical",
            vol_status,
            "The active volatility seed remains blocked from executable ticket design.",
            "review_vol_execution_blocker_rollup",
        ),
        report_row(
            "volatility_post_gate_context_state",
            "manual_review_required",
            "critical",
            post_gate_status,
            "Fresh broker context can inform review but does not approve ticket values.",
            "review_vol_post_gate_context_before_ticket_values",
        ),
        report_row(
            "paper_live_checklist_state",
            "manual_review_required",
            "high",
            checklist_status,
            "Checklist status is monitoring/readiness context only.",
            "review_paper_live_checklist_status",
        ),
        report_row(
            "vps_monitoring_status_assumption",
            "status_only_monitoring",
            "high",
            "vps_daily_monitoring_summary_includes_rollup; existing_cron_status_not_changed_by_dashboard",
            "The dashboard assumes VPS monitoring remains status-only and does not create or edit cron jobs.",
            "keep_monitoring_cron_status_only",
        ),
        report_row(
            "final_go_no_go",
            "no_go_execution_blocked",
            "critical",
            f"{monitoring_recommended}; {vol_status}",
            "Paper-live execution is not approved; monitoring only.",
            NEXT_STEP,
        ),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qqq_status = summary_value(inputs["qqq100_daily_decision"], "daily_decision_status") or "missing_qqq100_daily_decision"
    qqq_no_action = "hold_no_action_aligned_long" if qqq_status == "qqq100_daily_decision_hold_no_action_aligned_long" else "manual_review_required"
    vol_status = summary_value(inputs["vol_execution_blocker_rollup"], "final_execution_blocker_rollup_status") or "missing_vol_execution_blocker_rollup"
    vol_blocker = summary_value(inputs["vol_execution_blocker_rollup"], "largest_blocker") or "missing_vol_largest_blocker"
    post_gate_status = summary_value(inputs["vol_post_gate_review"], "final_post_gate_review_status") or "missing_vol_post_gate_review"
    post_gate_decision = summary_value(inputs["vol_post_gate_review"], "final_post_gate_review_decision") or "missing_vol_post_gate_review_decision"
    post_gate_blocker = summary_value(inputs["vol_post_gate_review"], "largest_blocker") or "missing_vol_post_gate_largest_blocker"
    post_gate_qqq_quantity = summary_value(inputs["vol_post_gate_review"], "saved_qqq_position_quantity_if_readonly") or "unavailable"
    ticket_value_status = summary_value(inputs["vol_ticket_value_design"], "final_ticket_value_design_status") or "missing_vol_ticket_value_design"
    ticket_value_decision = summary_value(inputs["vol_ticket_value_design"], "final_ticket_value_design_decision") or "missing_vol_ticket_value_design_decision"
    ticket_value_blocker = summary_value(inputs["vol_ticket_value_design"], "largest_blocker") or "missing_vol_ticket_value_largest_blocker"
    prereq_closeout_status = summary_value(inputs["vol_ticket_prereq_closeout"], "final_prerequisites_closeout_status") or "missing_vol_ticket_prereq_closeout"
    prereq_closeout_decision = summary_value(inputs["vol_ticket_prereq_closeout"], "final_prerequisites_closeout_decision") or "missing_vol_ticket_prereq_closeout_decision"
    approval_readiness_status = summary_value(inputs["vol_ticket_approval_readiness"], "final_approval_readiness_status") or "missing_vol_ticket_approval_readiness"
    approval_readiness_decision = summary_value(inputs["vol_ticket_approval_readiness"], "final_approval_readiness_decision") or "missing_vol_ticket_approval_readiness_decision"
    approval_criteria_status = summary_value(inputs["vol_ticket_approval_criteria"], "final_approval_criteria_status") or "missing_vol_ticket_approval_criteria"
    approval_criteria_decision = summary_value(inputs["vol_ticket_approval_criteria"], "final_approval_criteria_decision") or "missing_vol_ticket_approval_criteria_decision"
    criteria_resolution_status = summary_value(inputs["vol_ticket_criteria_resolution"], "final_resolution_plan_status") or "missing_vol_ticket_criteria_resolution"
    criteria_resolution_decision = summary_value(inputs["vol_ticket_criteria_resolution"], "final_resolution_plan_decision") or "missing_vol_ticket_criteria_resolution_decision"
    criteria_source_review_status = summary_value(inputs["vol_ticket_criteria_source_review"], "final_source_review_status") or "missing_vol_ticket_criteria_source_review"
    criteria_source_review_decision = summary_value(inputs["vol_ticket_criteria_source_review"], "final_source_review_decision") or "missing_vol_ticket_criteria_source_review_decision"
    criteria_blocker_closeout_review_status = summary_value(inputs["vol_ticket_criteria_blocker_closeout_review"], "final_blocker_closeout_review_status") or "missing_vol_ticket_criteria_blocker_closeout_review"
    criteria_blocker_closeout_review_decision = summary_value(inputs["vol_ticket_criteria_blocker_closeout_review"], "final_blocker_closeout_review_decision") or "missing_vol_ticket_criteria_blocker_closeout_review_decision"
    blocker_specific_review_rollup_status = summary_value(inputs["vol_ticket_blocker_specific_review_rollup"], "final_review_status") or "missing_vol_ticket_blocker_specific_review_rollup"
    blocker_specific_review_rollup_decision = summary_value(inputs["vol_ticket_blocker_specific_review_rollup"], "final_review_decision") or "missing_vol_ticket_blocker_specific_review_rollup_decision"
    closeout_candidate_review_rollup_status = summary_value(inputs["vol_ticket_closeout_candidate_review_rollup"], "final_candidate_review_status") or "missing_vol_ticket_closeout_candidate_review_rollup"
    closeout_candidate_review_rollup_decision = summary_value(inputs["vol_ticket_closeout_candidate_review_rollup"], "final_candidate_review_decision") or "missing_vol_ticket_closeout_candidate_review_rollup_decision"
    closeout_approval_wording_status = summary_value(inputs["vol_ticket_criteria_source_closeout_approval_wording"], "final_approval_wording_status") or "missing_vol_ticket_criteria_source_closeout_approval_wording"
    closeout_approval_wording_decision = summary_value(inputs["vol_ticket_criteria_source_closeout_approval_wording"], "final_approval_wording_decision") or "missing_vol_ticket_criteria_source_closeout_approval_wording_decision"
    closeout_approval_wording_phrase = summary_value(inputs["vol_ticket_criteria_source_closeout_approval_wording"], "future_approval_phrase") or "missing_vol_ticket_criteria_source_closeout_future_phrase"
    closeout_record_status = summary_value(inputs["vol_ticket_criteria_source_closeout_record"], "final_closeout_record_status") or "missing_vol_ticket_criteria_source_closeout_record"
    closeout_record_decision = summary_value(inputs["vol_ticket_criteria_source_closeout_record"], "final_closeout_record_decision") or "missing_vol_ticket_criteria_source_closeout_record_decision"
    closeout_record_blocker = summary_value(inputs["vol_ticket_criteria_source_closeout_record"], "closed_blocker") or "missing_vol_ticket_criteria_source_closed_blocker"
    closeout_record_remaining = summary_value(inputs["vol_ticket_criteria_source_closeout_record"], "remaining_known_blockers") or "missing_vol_ticket_criteria_source_remaining_blockers"
    resolution_closeout_approval_wording_status = summary_value(inputs["vol_ticket_criteria_resolution_plan_closeout_approval_wording"], "final_approval_wording_status") or "missing_vol_ticket_criteria_resolution_plan_closeout_approval_wording"
    resolution_closeout_approval_wording_decision = summary_value(inputs["vol_ticket_criteria_resolution_plan_closeout_approval_wording"], "final_approval_wording_decision") or "missing_vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision"
    resolution_closeout_approval_wording_phrase = summary_value(inputs["vol_ticket_criteria_resolution_plan_closeout_approval_wording"], "future_approval_phrase") or "missing_vol_ticket_criteria_resolution_plan_closeout_future_phrase"
    resolution_closeout_record_status = summary_value(inputs["vol_ticket_criteria_resolution_plan_closeout_record"], "final_closeout_record_status") or "missing_vol_ticket_criteria_resolution_plan_closeout_record"
    resolution_closeout_record_decision = summary_value(inputs["vol_ticket_criteria_resolution_plan_closeout_record"], "final_closeout_record_decision") or "missing_vol_ticket_criteria_resolution_plan_closeout_record_decision"
    resolution_closeout_record_blocker = summary_value(inputs["vol_ticket_criteria_resolution_plan_closeout_record"], "closed_blocker") or "missing_vol_ticket_criteria_resolution_plan_closed_blocker"
    resolution_closeout_record_remaining = summary_value(inputs["vol_ticket_criteria_resolution_plan_closeout_record"], "remaining_known_blockers") or "missing_vol_ticket_criteria_resolution_plan_remaining_blockers"
    approval_closeout_approval_wording_status = summary_value(inputs["vol_ticket_approval_criteria_closeout_approval_wording"], "final_approval_wording_status") or "missing_vol_ticket_approval_criteria_closeout_approval_wording"
    approval_closeout_approval_wording_decision = summary_value(inputs["vol_ticket_approval_criteria_closeout_approval_wording"], "final_approval_wording_decision") or "missing_vol_ticket_approval_criteria_closeout_approval_wording_decision"
    approval_closeout_approval_wording_phrase = summary_value(inputs["vol_ticket_approval_criteria_closeout_approval_wording"], "future_approval_phrase") or "missing_vol_ticket_approval_criteria_closeout_future_phrase"
    approval_closeout_record_status = summary_value(inputs["vol_ticket_approval_criteria_closeout_record"], "final_closeout_record_status") or "missing_vol_ticket_approval_criteria_closeout_record"
    approval_closeout_record_decision = summary_value(inputs["vol_ticket_approval_criteria_closeout_record"], "final_closeout_record_decision") or "missing_vol_ticket_approval_criteria_closeout_record_decision"
    approval_closeout_record_blocker = summary_value(inputs["vol_ticket_approval_criteria_closeout_record"], "closed_blocker") or "missing_vol_ticket_approval_criteria_closed_blocker"
    approval_closeout_record_remaining = summary_value(inputs["vol_ticket_approval_criteria_closeout_record"], "remaining_known_blockers") or "missing_vol_ticket_approval_criteria_remaining_blockers"
    final_closeout_approval_wording_status = summary_value(inputs["vol_ticket_final_blockers_closeout_approval_wording"], "final_approval_wording_status") or "missing_vol_ticket_final_blockers_closeout_approval_wording"
    final_closeout_approval_wording_decision = summary_value(inputs["vol_ticket_final_blockers_closeout_approval_wording"], "final_approval_wording_decision") or "missing_vol_ticket_final_blockers_closeout_approval_wording_decision"
    final_closeout_approval_wording_phrase = summary_value(inputs["vol_ticket_final_blockers_closeout_approval_wording"], "future_approval_phrase") or "missing_vol_ticket_final_blockers_closeout_future_phrase"
    final_closeout_record_status = summary_value(inputs["vol_ticket_final_blockers_closeout_record"], "final_closeout_record_status") or "missing_vol_ticket_final_blockers_closeout_record"
    final_closeout_record_decision = summary_value(inputs["vol_ticket_final_blockers_closeout_record"], "final_closeout_record_decision") or "missing_vol_ticket_final_blockers_closeout_record_decision"
    final_closeout_record_blocker = summary_value(inputs["vol_ticket_final_blockers_closeout_record"], "closed_blocker") or "missing_vol_ticket_final_blockers_closed_blocker"
    final_closeout_record_remaining = summary_value(inputs["vol_ticket_final_blockers_closeout_record"], "remaining_known_blockers") or "missing_vol_ticket_final_blockers_remaining_blockers"
    execution_approval_request_status = summary_value(inputs["vol_execution_approval_request_readiness"], "final_readiness_status") or "missing_vol_execution_approval_request_readiness"
    execution_approval_request_decision = summary_value(inputs["vol_execution_approval_request_readiness"], "final_readiness_decision") or "missing_vol_execution_approval_request_readiness_decision"
    execution_approval_request_ready = summary_value(inputs["vol_execution_approval_request_readiness"], "approval_request_ready") or "False"
    execution_approval_requested = summary_value(inputs["vol_execution_approval_request_readiness"], "approval_requested") or "False"
    execution_approval_recorded = summary_value(inputs["vol_execution_approval_request_readiness"], "approval_recorded") or "False"
    execution_design_wording_status = summary_value(inputs["vol_execution_design_approval_wording"], "final_execution_design_wording_status") or "missing_vol_execution_design_approval_wording"
    execution_design_wording_decision = summary_value(inputs["vol_execution_design_approval_wording"], "final_execution_design_wording_decision") or "missing_vol_execution_design_approval_wording_decision"
    execution_design_phrase = summary_value(inputs["vol_execution_design_approval_wording"], "approval_phrase") or "missing_vol_execution_design_approval_phrase"
    execution_design_record_status = summary_value(inputs["vol_execution_design_approval_record"], "final_execution_design_record_status") or "missing_vol_execution_design_approval_record"
    execution_design_record_decision = summary_value(inputs["vol_execution_design_approval_record"], "final_execution_design_record_decision") or "missing_vol_execution_design_approval_record_decision"
    execution_design_approved = summary_value(inputs["vol_execution_design_approval_record"], "execution_design_approved") or "False"
    execution_design_approval_recorded = summary_value(inputs["vol_execution_design_approval_record"], "manual_execution_design_approval_recorded") or "False"
    non_submitting_executable_ticket_status = summary_value(inputs["vol_non_submitting_executable_ticket_design"], "final_executable_ticket_design_status") or "missing_vol_non_submitting_executable_ticket_design"
    non_submitting_executable_ticket_decision = summary_value(inputs["vol_non_submitting_executable_ticket_design"], "final_executable_ticket_design_decision") or "missing_vol_non_submitting_executable_ticket_design_decision"
    non_submitting_executable_ticket_order_values = summary_value(inputs["vol_non_submitting_executable_ticket_design"], "order_values_populated") or "False"
    non_submitting_executable_ticket_created = summary_value(inputs["vol_non_submitting_executable_ticket_design"], "executable_ticket_created") or "False"
    checklist_status = summary_value(inputs["paper_live_checklist"], "checklist_phase_status") or "missing_paper_live_checklist"
    monitoring_next = summary_value(inputs["paper_live_monitoring"], "recommended_next_step") or "missing_paper_live_monitoring"
    data = [
        ("final_go_no_go_status", FINAL_STATUS, "Dashboard is report-only and blocks execution."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker."),
        ("qqq100_daily_decision_status", qqq_status, "Saved QQQ100 daily decision status."),
        ("qqq100_no_action_state", qqq_no_action, "QQQ100 action state from saved daily decision."),
        ("vol_execution_blocker_status", vol_status, "Saved volatility execution blocker rollup status."),
        ("vol_largest_blocker", vol_blocker, "Largest saved volatility blocker."),
        ("vol_post_gate_review_status", post_gate_status, "Saved post-gate review status."),
        ("vol_post_gate_review_decision", post_gate_decision, "Saved post-gate review decision."),
        ("vol_post_gate_largest_blocker", post_gate_blocker, "Largest saved post-gate blocker."),
        ("vol_post_gate_saved_qqq_quantity", post_gate_qqq_quantity, "Saved QQQ quantity from post-gate review."),
        ("vol_ticket_value_design_status", ticket_value_status, "Saved manual ticket-value design status."),
        ("vol_ticket_value_design_decision", ticket_value_decision, "Saved manual ticket-value design decision."),
        ("vol_ticket_value_largest_blocker", ticket_value_blocker, "Largest saved ticket-value design blocker."),
        ("vol_ticket_prereq_closeout_status", prereq_closeout_status, "Saved executable-ticket prerequisites closeout status."),
        ("vol_ticket_prereq_closeout_decision", prereq_closeout_decision, "Saved executable-ticket prerequisites closeout decision."),
        ("vol_ticket_approval_readiness_status", approval_readiness_status, "Saved executable-ticket approval-readiness status."),
        ("vol_ticket_approval_readiness_decision", approval_readiness_decision, "Saved executable-ticket approval-readiness decision."),
        ("vol_ticket_approval_criteria_status", approval_criteria_status, "Saved executable-ticket approval criteria status."),
        ("vol_ticket_approval_criteria_decision", approval_criteria_decision, "Saved executable-ticket approval criteria decision."),
        ("vol_ticket_criteria_resolution_status", criteria_resolution_status, "Saved executable-ticket criteria resolution plan status."),
        ("vol_ticket_criteria_resolution_decision", criteria_resolution_decision, "Saved executable-ticket criteria resolution plan decision."),
        ("vol_ticket_criteria_source_review_status", criteria_source_review_status, "Saved executable-ticket criteria source review status."),
        ("vol_ticket_criteria_source_review_decision", criteria_source_review_decision, "Saved executable-ticket criteria source review decision."),
        ("vol_ticket_criteria_blocker_closeout_review_status", criteria_blocker_closeout_review_status, "Saved executable-ticket criteria blocker closeout review status."),
        ("vol_ticket_criteria_blocker_closeout_review_decision", criteria_blocker_closeout_review_decision, "Saved executable-ticket criteria blocker closeout review decision."),
        ("vol_ticket_blocker_specific_review_rollup_status", blocker_specific_review_rollup_status, "Saved executable-ticket blocker-specific review rollup status."),
        ("vol_ticket_blocker_specific_review_rollup_decision", blocker_specific_review_rollup_decision, "Saved executable-ticket blocker-specific review rollup decision."),
        ("vol_ticket_closeout_candidate_review_rollup_status", closeout_candidate_review_rollup_status, "Saved executable-ticket closeout-candidate review rollup status."),
        ("vol_ticket_closeout_candidate_review_rollup_decision", closeout_candidate_review_rollup_decision, "Saved executable-ticket closeout-candidate review rollup decision."),
        ("vol_ticket_criteria_source_closeout_approval_wording_status", closeout_approval_wording_status, "Saved criteria-source closeout approval wording status."),
        ("vol_ticket_criteria_source_closeout_approval_wording_decision", closeout_approval_wording_decision, "Saved criteria-source closeout approval wording decision."),
        ("vol_ticket_criteria_source_closeout_future_phrase", closeout_approval_wording_phrase, "Simple future approval phrase; not approval yet."),
        ("vol_ticket_criteria_source_closeout_record_status", closeout_record_status, "Saved criteria-source closeout record status."),
        ("vol_ticket_criteria_source_closeout_record_decision", closeout_record_decision, "Saved criteria-source closeout record decision."),
        ("vol_ticket_criteria_source_closed_blocker", closeout_record_blocker, "Single closed blocker from saved closeout record."),
        ("vol_ticket_criteria_source_remaining_blockers", closeout_record_remaining, "Known remaining blockers after the single closeout."),
        ("vol_ticket_criteria_resolution_plan_closeout_approval_wording_status", resolution_closeout_approval_wording_status, "Saved resolution-plan closeout approval wording status."),
        ("vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision", resolution_closeout_approval_wording_decision, "Saved resolution-plan closeout approval wording decision."),
        ("vol_ticket_criteria_resolution_plan_closeout_future_phrase", resolution_closeout_approval_wording_phrase, "Simple future approval phrase; not approval yet."),
        ("vol_ticket_criteria_resolution_plan_closeout_record_status", resolution_closeout_record_status, "Saved resolution-plan closeout record status."),
        ("vol_ticket_criteria_resolution_plan_closeout_record_decision", resolution_closeout_record_decision, "Saved resolution-plan closeout record decision."),
        ("vol_ticket_criteria_resolution_plan_closed_blocker", resolution_closeout_record_blocker, "Second closed blocker from saved closeout record."),
        ("vol_ticket_criteria_resolution_plan_remaining_blockers", resolution_closeout_record_remaining, "Known remaining blockers after the second closeout."),
        ("vol_ticket_approval_criteria_closeout_approval_wording_status", approval_closeout_approval_wording_status, "Saved approval-criteria closeout approval wording status."),
        ("vol_ticket_approval_criteria_closeout_approval_wording_decision", approval_closeout_approval_wording_decision, "Saved approval-criteria closeout approval wording decision."),
        ("vol_ticket_approval_criteria_closeout_future_phrase", approval_closeout_approval_wording_phrase, "Simple future approval phrase; not approval yet."),
        ("vol_ticket_approval_criteria_closeout_record_status", approval_closeout_record_status, "Saved approval-criteria closeout record status."),
        ("vol_ticket_approval_criteria_closeout_record_decision", approval_closeout_record_decision, "Saved approval-criteria closeout record decision."),
        ("vol_ticket_approval_criteria_closed_blocker", approval_closeout_record_blocker, "Third closed blocker from saved closeout record."),
        ("vol_ticket_approval_criteria_remaining_blockers", approval_closeout_record_remaining, "Known remaining blockers after the third closeout."),
        ("vol_ticket_final_blockers_closeout_approval_wording_status", final_closeout_approval_wording_status, "Saved final-ticket-blockers closeout approval wording status."),
        ("vol_ticket_final_blockers_closeout_approval_wording_decision", final_closeout_approval_wording_decision, "Saved final-ticket-blockers closeout approval wording decision."),
        ("vol_ticket_final_blockers_closeout_future_phrase", final_closeout_approval_wording_phrase, "Simple future approval phrase; not execution approval."),
        ("vol_ticket_final_blockers_closeout_record_status", final_closeout_record_status, "Saved final-ticket-blockers closeout record status."),
        ("vol_ticket_final_blockers_closeout_record_decision", final_closeout_record_decision, "Saved final-ticket-blockers closeout record decision."),
        ("vol_ticket_final_blockers_closed_blocker", final_closeout_record_blocker, "Final checklist blockers closed from saved closeout record."),
        ("vol_ticket_final_blockers_remaining_blockers", final_closeout_record_remaining, "Known remaining checklist blockers after final closeout."),
        ("vol_execution_approval_request_readiness_status", execution_approval_request_status, "Saved execution approval request readiness status."),
        ("vol_execution_approval_request_readiness_decision", execution_approval_request_decision, "Readiness to ask for a separate explicit approval only."),
        ("vol_execution_approval_request_ready", execution_approval_request_ready, "True means ready to ask, not approved to trade."),
        ("vol_execution_approval_requested", execution_approval_requested, "This remains false until a separate explicit approval process."),
        ("vol_execution_approval_recorded", execution_approval_recorded, "This remains false until a separate explicit approval record."),
        ("vol_execution_design_approval_wording_status", execution_design_wording_status, "Saved execution-design-only wording status."),
        ("vol_execution_design_approval_wording_decision", execution_design_wording_decision, "Saved execution-design-only wording decision."),
        ("vol_execution_design_approval_phrase", execution_design_phrase, "Design-only approval wording; not order approval."),
        ("vol_execution_design_approval_record_status", execution_design_record_status, "Saved execution-design-only approval record status."),
        ("vol_execution_design_approval_record_decision", execution_design_record_decision, "Saved execution-design-only approval record decision."),
        ("vol_execution_design_approved", execution_design_approved, "True means design may continue; it is not execution approval."),
        ("vol_execution_design_approval_recorded", execution_design_approval_recorded, "True only when the design-only record exists."),
        ("vol_non_submitting_executable_ticket_design_status", non_submitting_executable_ticket_status, "Saved non-submitting executable-ticket design status."),
        ("vol_non_submitting_executable_ticket_design_decision", non_submitting_executable_ticket_decision, "Saved non-submitting executable-ticket design decision."),
        ("vol_non_submitting_executable_ticket_order_values_populated", non_submitting_executable_ticket_order_values, "Must remain False."),
        ("vol_non_submitting_executable_ticket_created", non_submitting_executable_ticket_created, "Must remain False."),
        ("paper_live_checklist_phase_status", checklist_status, "Saved paper-live checklist phase status."),
        ("paper_live_monitoring_recommended_next_step", monitoring_next, "Saved paper-live monitoring recommended next step."),
        ("vps_monitoring_status_assumption", "status_only_monitoring_no_cron_change", "Dashboard assumes existing VPS monitoring remains status-only."),
        ("final_go_no_go_decision", "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY", "Execution remains blocked."),
        ("largest_blocker", vol_blocker if vol_blocker != "none" else "execution_not_approved", "Primary go/no-go blocker."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any future execution design."),
        ("dashboard_row_count", str(len(report_rows)), "Saved report row count."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("execution_not_approved", "blocked", "critical", "Go/no-go status is no-go for execution.", NEXT_STEP),
        ("volatility_ticket_prerequisites_unmet", "blocked", "critical", "Volatility executable ticket prerequisites remain unmet.", "review_vol_execution_blocker_rollup"),
        ("post_gate_ticket_values_not_approved", "blocked", "critical", "Fresh broker context does not approve ticket values.", "review_vol_post_gate_context_before_ticket_values"),
        ("manual_ticket_values_not_approved", "blocked", "critical", "Manual ticket-value design does not approve executable values.", "review_manual_ticket_value_design_before_executable_ticket"),
        ("executable_ticket_prerequisites_not_closed", "blocked", "critical", "Executable ticket prerequisites closeout remains open.", "review_executable_ticket_prerequisites_closeout"),
        ("executable_ticket_approval_not_ready", "blocked", "critical", "Executable ticket approval readiness is not ready.", "do_not_request_executable_ticket_approval"),
        ("executable_ticket_approval_criteria_review_required", "blocked", "critical", "Executable ticket approval criteria require manual review.", "review_executable_ticket_approval_criteria"),
        ("executable_ticket_criteria_resolution_plan_open", "blocked", "critical", "Executable ticket criteria resolution plan is open and does not resolve blockers.", "review_executable_ticket_criteria_resolution_plan"),
        ("executable_ticket_criteria_source_review_does_not_close_blockers", "blocked", "critical", "Executable ticket criteria source review does not close blockers.", "review_executable_ticket_criteria_source_review"),
        ("executable_ticket_criteria_blocker_closeout_review_does_not_close_blockers", "blocked", "critical", "Executable ticket criteria blocker closeout review does not close blockers.", "review_executable_ticket_criteria_blocker_closeout_review"),
        ("executable_ticket_blocker_specific_reviews_do_not_close_blockers", "blocked", "critical", "Executable ticket blocker-specific reviews do not close blockers.", "review_executable_ticket_blocker_specific_reviews"),
        ("executable_ticket_closeout_candidate_reviews_do_not_close_blockers", "blocked", "critical", "Executable ticket closeout-candidate reviews do not close blockers.", "review_executable_ticket_closeout_candidate_reviews"),
        ("executable_ticket_criteria_source_closeout_approval_wording_not_recorded", "blocked", "critical", "Criteria-source closeout wording is not recorded approval.", "wait_for_explicit_simple_criteria_source_closeout_approval"),
        ("remaining_execution_ticket_blockers_after_criteria_source_closeout", "blocked", "critical", "Only criteria_source_reviewed may be closed; ticket values and approval blockers remain open.", "refresh_execution_blocker_chain_after_single_criteria_source_closeout"),
        ("remaining_execution_ticket_blockers_after_resolution_plan_closeout", "blocked", "critical", "Criteria source and resolution plan may be closed; approval criteria, ticket values, and prerequisites remain open.", "refresh_execution_blocker_chain_after_second_criteria_closeout"),
        ("remaining_execution_ticket_blockers_after_approval_criteria_closeout", "blocked", "critical", "Criteria blockers may be closed; ticket values and prerequisites remain open.", "refresh_execution_blocker_chain_after_third_criteria_closeout"),
        ("execution_still_not_approved_after_final_ticket_blockers_closeout", "blocked", "critical", "Final checklist blockers may be closed, but no executable ticket or execution approval exists.", "manual_review_before_any_separate_execution_approval_request"),
        ("execution_design_approval_is_not_order_approval", "blocked", "critical", "Execution-design approval may be recorded, but order values, tickets, and execution remain unapproved.", "design_non_submitting_executable_ticket_values_without_order_approval"),
        ("non_submitting_executable_ticket_is_not_an_order", "blocked", "critical", "The non-submitting executable-ticket design has no side, quantity, order type, account, broker id, or submit-ready state.", "manual_review_non_submitting_executable_ticket_design_before_any_ticket_values_or_order_approval"),
        ("repeat_followup_orders_not_approved", "blocked", "critical", "QQQ100 follow-up and repeat orders remain unapproved.", "hold_no_action_and_monitor_only"),
        ("scheduling_not_approved", "blocked", "critical", "No order-capable scheduling is approved.", "keep_monitoring_status_only"),
    ]
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(0, (f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return [blocker_row(*item) for item in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        (f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, order, alert, SQLite, or scheduling path is used."))
    return [evidence_row(*item) for item in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live go/no-go dashboard complete. Report only; no execution or scheduling approved.",
        f"final_go_no_go_status={summary_value(summary_rows, 'final_go_no_go_status')}",
        f"final_go_no_go_decision={summary_value(summary_rows, 'final_go_no_go_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"qqq100_no_action_state={summary_value(summary_rows, 'qqq100_no_action_state')}",
        f"vol_largest_blocker={summary_value(summary_rows, 'vol_largest_blocker')}",
        f"vol_post_gate_review_status={summary_value(summary_rows, 'vol_post_gate_review_status')}",
        f"vol_post_gate_review_decision={summary_value(summary_rows, 'vol_post_gate_review_decision')}",
        f"vol_post_gate_largest_blocker={summary_value(summary_rows, 'vol_post_gate_largest_blocker')}",
        f"vol_ticket_value_design_status={summary_value(summary_rows, 'vol_ticket_value_design_status')}",
        f"vol_ticket_value_design_decision={summary_value(summary_rows, 'vol_ticket_value_design_decision')}",
        f"vol_ticket_prereq_closeout_decision={summary_value(summary_rows, 'vol_ticket_prereq_closeout_decision')}",
        f"vol_ticket_approval_readiness_decision={summary_value(summary_rows, 'vol_ticket_approval_readiness_decision')}",
        f"vol_ticket_approval_criteria_decision={summary_value(summary_rows, 'vol_ticket_approval_criteria_decision')}",
        f"vol_ticket_criteria_resolution_decision={summary_value(summary_rows, 'vol_ticket_criteria_resolution_decision')}",
        f"vol_ticket_criteria_source_review_decision={summary_value(summary_rows, 'vol_ticket_criteria_source_review_decision')}",
        f"vol_ticket_criteria_blocker_closeout_review_decision={summary_value(summary_rows, 'vol_ticket_criteria_blocker_closeout_review_decision')}",
        f"vol_ticket_blocker_specific_review_rollup_decision={summary_value(summary_rows, 'vol_ticket_blocker_specific_review_rollup_decision')}",
        f"vol_ticket_closeout_candidate_review_rollup_decision={summary_value(summary_rows, 'vol_ticket_closeout_candidate_review_rollup_decision')}",
        f"vol_ticket_criteria_source_closeout_approval_wording_decision={summary_value(summary_rows, 'vol_ticket_criteria_source_closeout_approval_wording_decision')}",
        f"vol_ticket_criteria_source_closeout_record_decision={summary_value(summary_rows, 'vol_ticket_criteria_source_closeout_record_decision')}",
        f"vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision={summary_value(summary_rows, 'vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision')}",
        f"vol_ticket_criteria_resolution_plan_closeout_future_phrase={summary_value(summary_rows, 'vol_ticket_criteria_resolution_plan_closeout_future_phrase')}",
        f"vol_ticket_criteria_resolution_plan_closeout_record_decision={summary_value(summary_rows, 'vol_ticket_criteria_resolution_plan_closeout_record_decision')}",
        f"vol_ticket_approval_criteria_closeout_approval_wording_decision={summary_value(summary_rows, 'vol_ticket_approval_criteria_closeout_approval_wording_decision')}",
        f"vol_ticket_approval_criteria_closeout_future_phrase={summary_value(summary_rows, 'vol_ticket_approval_criteria_closeout_future_phrase')}",
        f"vol_ticket_approval_criteria_closeout_record_decision={summary_value(summary_rows, 'vol_ticket_approval_criteria_closeout_record_decision')}",
        f"vol_ticket_final_blockers_closeout_record_decision={summary_value(summary_rows, 'vol_ticket_final_blockers_closeout_record_decision')}",
        f"vol_execution_approval_request_readiness_decision={summary_value(summary_rows, 'vol_execution_approval_request_readiness_decision')}",
        f"vol_execution_design_approval_wording_decision={summary_value(summary_rows, 'vol_execution_design_approval_wording_decision')}",
        f"vol_execution_design_approval_phrase={summary_value(summary_rows, 'vol_execution_design_approval_phrase')}",
        f"vol_execution_design_approval_record_decision={summary_value(summary_rows, 'vol_execution_design_approval_record_decision')}",
        f"vol_execution_design_approved={summary_value(summary_rows, 'vol_execution_design_approved')}",
        f"vol_non_submitting_executable_ticket_design_decision={summary_value(summary_rows, 'vol_non_submitting_executable_ticket_design_decision')}",
        f"vol_non_submitting_executable_ticket_order_values_populated={summary_value(summary_rows, 'vol_non_submitting_executable_ticket_order_values_populated')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "order_instructions_created=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {
        "check_name": name,
        "status": status,
        "risk_level": risk,
        "evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


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
