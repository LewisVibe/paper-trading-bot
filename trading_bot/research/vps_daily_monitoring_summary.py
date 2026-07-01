"""Concise daily VPS monitoring summary."""

from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

from trading_bot.research.monitoring_freshness import (
    build_freshness_statuses,
    format_freshness_lines,
    has_stale_or_missing,
    has_warning,
)
from trading_bot.research.vps_monitoring_status import (
    DEFENSIVE_SAVED_INPUTS,
    GENERATED_OUTPUT_PATHS,
    HIGH_RISK_BOUNDARY_LINES,
    LOCK_WRAPPED_COMMANDS,
    PROMOTED_DECISION_PREVIEW_PATH,
    PROMOTED_REVIEW_SUMMARY_PATH,
    QQQ100_DAILY_DECISION_SUMMARY_PATH,
    all_false,
    build_paper_live_monitoring_context,
    format_counts,
    paper_live_monitoring_status_lines,
    qqq100_daily_decision_status_lines,
    qqq100_manual_flatten_readiness_status_lines,
    qqq100_manual_flatten_runbook_status_lines,
    read_csv_rows,
)


DEFENSIVE_REFRESH_SUMMARY_PATH = "data/defensive_research_refresh_summary.csv"
VOL_ACTIVE_SEED_READINESS_SUMMARY_PATH = "data/vol_targeted_growth_active_seed_readiness_summary.csv"
VOL_CANDIDATE_DECISION_RECORD_SUMMARY_PATH = "data/vol_targeted_growth_candidate_decision_record_summary.csv"
VOL_EXECUTION_BLOCKER_ROLLUP_SUMMARY_PATH = "data/vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv"
VOL_EXECUTABLE_TICKET_GAP_LIST_SUMMARY_PATH = "data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"
VOL_MANUAL_EXECUTION_DESIGN_APPROVAL_GATE_SUMMARY_PATH = "data/vol_targeted_growth_manual_execution_design_approval_gate_summary.csv"
VOL_NON_SUBMITTING_TICKET_SCHEMA_DESIGN_SUMMARY_PATH = "data/vol_targeted_growth_non_submitting_ticket_schema_design_summary.csv"
VOL_NON_SUBMITTING_TICKET_INSTANCE_DESIGN_SUMMARY_PATH = "data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"
VOL_FRESH_BROKER_PRE_TICKET_GATE_DESIGN_SUMMARY_PATH = "data/vol_targeted_growth_fresh_broker_pre_ticket_gate_design_summary.csv"
VOL_FRESH_BROKER_PRE_TICKET_GATE_RUN_READINESS_SUMMARY_PATH = "data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_summary.csv"
VOL_FRESH_BROKER_PRE_TICKET_GATE_RUN_SUMMARY_PATH = "data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv"
PAPER_LIVE_GO_NO_GO_DASHBOARD_SUMMARY_PATH = "data/paper_live_go_no_go_dashboard_summary.csv"
PAPER_LIVE_GO_NO_GO_EXPECTED_DECISION = "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"
VOL_EXECUTABLE_TICKET_GAP_LIST_EXPECTED_DECISION = "EXECUTABLE_TICKET_DESIGN_NOT_READY"
VOL_MANUAL_EXECUTION_DESIGN_APPROVAL_GATE_EXPECTED_DECISION = "MANUAL_EXECUTION_DESIGN_APPROVAL_NOT_RECORDED"
VOL_NON_SUBMITTING_TICKET_SCHEMA_DESIGN_EXPECTED_DECISION = "NON_SUBMITTING_TICKET_SCHEMA_DESIGNED_NO_TICKET_CREATED"
VOL_NON_SUBMITTING_TICKET_INSTANCE_DESIGN_EXPECTED_DECISION = "NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES"
VOL_FRESH_BROKER_PRE_TICKET_GATE_DESIGN_EXPECTED_DECISION = "FRESH_BROKER_PRE_TICKET_GATE_DESIGNED_NOT_RUN"
VOL_FRESH_BROKER_PRE_TICKET_GATE_RUN_READINESS_EXPECTED_DECISION = "READY_TO_REQUEST_EXPLICIT_READONLY_ALPACA_APPROVAL"


def build_vps_daily_monitoring_summary_lines(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    freshness_statuses = build_freshness_statuses(root_path)
    decision_rows = read_csv_rows(root_path / PROMOTED_DECISION_PREVIEW_PATH)
    promoted_decision_counts = Counter(row.get("decision_state", "") or "blank" for row in decision_rows)
    decisions_execution_false = all_false(decision_rows, "execution_approved")
    defensive_rows = read_csv_rows(root_path / DEFENSIVE_REFRESH_SUMMARY_PATH)
    defensive_counts = Counter(row.get("status", "") or "blank" for row in defensive_rows)
    paper_live_context = build_paper_live_monitoring_context(root_path)
    daily_decision_rows = read_csv_rows(root_path / QQQ100_DAILY_DECISION_SUMMARY_PATH)
    daily_decision_approvals_false = all_false(daily_decision_rows, "execution_approved")
    final_status = determine_final_status(
        freshness_statuses,
        decision_rows_present=bool(decision_rows),
        decisions_execution_false=decisions_execution_false,
        paper_live_monitoring_consistent=paper_live_context.consistent,
        daily_decision_present=bool(daily_decision_rows),
        daily_decision_approvals_false=daily_decision_approvals_false,
    )
    action = classify_action_required(
        freshness_statuses,
        decision_rows_present=bool(decision_rows),
        decisions_execution_false=decisions_execution_false,
        paper_live_monitoring_consistent=paper_live_context.consistent,
        daily_decision_present=bool(daily_decision_rows),
        daily_decision_approvals_false=daily_decision_approvals_false,
    )

    lines = [
        "VPS DAILY MONITORING SUMMARY. REPORT ONLY. NOT EXECUTION.",
        "execution_approved=False",
        "scheduling_approved=False",
        "",
        "Safety reminders:",
        f"- config_presence_only: {(root_path / 'config.json').exists()}; contents were not read.",
        f"- generated_outputs_ignored_untracked: {generated_outputs_ignored(root_path)}",
        "- missing or stale saved outputs are prerequisite/status issues, not trading approval.",
        "",
        "Lock-wrapped safe commands:",
    ]
    for command in LOCK_WRAPPED_COMMANDS:
        lines.append(f"- {command}")

    lines.extend(
        [
            "",
            "Promoted review summary:",
            f"- promoted_review_summary_present: {(root_path / PROMOTED_REVIEW_SUMMARY_PATH).exists()}",
            f"- promoted_decision_preview_present: {(root_path / PROMOTED_DECISION_PREVIEW_PATH).exists()}",
            f"- promoted_decision_state_counts: {format_counts(promoted_decision_counts)}",
            f"- promoted_decisions_execution_approved_false_for_all_rows: {decisions_execution_false}",
            "",
            "Defensive refresh summary:",
            f"- defensive_saved_inputs_present: {defensive_saved_inputs_present(root_path)}",
            f"- defensive_refresh_summary_present: {(root_path / DEFENSIVE_REFRESH_SUMMARY_PATH).exists()}",
            f"- defensive_refresh_step_counts: {format_counts(defensive_counts)}",
            "",
            "Paper-live monitoring status:",
        ]
    )
    lines.extend(paper_live_monitoring_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility active-seed readiness:",
        ]
    )
    lines.extend(vol_active_seed_readiness_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility candidate decision record:",
        ]
    )
    lines.extend(vol_candidate_decision_record_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility paper-live execution blocker rollup:",
        ]
    )
    lines.extend(vol_execution_blocker_rollup_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility executable ticket gap list:",
        ]
    )
    lines.extend(vol_executable_ticket_gap_list_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility manual execution-design approval gate:",
        ]
    )
    lines.extend(vol_manual_execution_design_approval_gate_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility non-submitting ticket schema design:",
        ]
    )
    lines.extend(vol_non_submitting_ticket_schema_design_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility non-submitting ticket-instance design:",
        ]
    )
    lines.extend(vol_non_submitting_ticket_instance_design_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility fresh broker pre-ticket gate design:",
        ]
    )
    lines.extend(vol_fresh_broker_pre_ticket_gate_design_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility fresh broker pre-ticket gate run-readiness:",
        ]
    )
    lines.extend(vol_fresh_broker_pre_ticket_gate_run_readiness_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility fresh broker pre-ticket gate run:",
        ]
    )
    lines.extend(vol_fresh_broker_pre_ticket_gate_run_status_lines(root_path))
    lines.extend(
        [
            "",
            "QQQ100 daily decision:",
        ]
    )
    lines.extend(qqq100_daily_decision_status_lines(root_path))
    lines.extend(
        [
            "",
            "QQQ100 manual flatten readiness:",
        ]
    )
    lines.extend(qqq100_manual_flatten_readiness_status_lines(root_path))
    lines.extend(
        [
            "",
            "QQQ100 manual flatten runbook:",
        ]
    )
    lines.extend(qqq100_manual_flatten_runbook_status_lines(root_path))
    lines.extend(
        [
            "",
            "Paper-live go/no-go dashboard:",
        ]
    )
    lines.extend(paper_live_go_no_go_dashboard_status_lines(root_path))
    lines.extend(
        [
            "",
            "Saved-output freshness:",
        ]
    )
    lines.extend(format_freshness_lines(freshness_statuses))
    lines.extend(
        [
            "",
            "High-risk/manual-only boundaries:",
        ]
    )
    for boundary in HIGH_RISK_BOUNDARY_LINES:
        lines.append(f"- {boundary}")
    lines.extend(
        [
            "",
            f"final_status: {final_status}",
            f"action_required: {action['action_required']}",
            f"action_reason: {action['action_reason']}",
            f"suggested_manual_action: {action['suggested_manual_action']}",
            "Warning: this daily summary does not call Alpaca, yfinance, Discord, SQLite trade_log, or read config.json contents.",
        ]
    )
    return lines


def vol_active_seed_readiness_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_ACTIVE_SEED_READINESS_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_active_seed_readiness_present: False",
            f"- vol_active_seed_readiness_missing_saved_output: {VOL_ACTIVE_SEED_READINESS_SUMMARY_PATH}",
            "- vol_active_seed_readiness_status: missing_saved_output",
            "- vol_active_seed_readiness_warning: monitor only; missing saved readiness does not approve execution or scheduling.",
        ]
    return [
        "- vol_active_seed_readiness_present: True",
        f"- final_active_seed_readiness_status: {summary_value(rows, 'final_active_seed_readiness_status')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- readiness_pass_count: {summary_value(rows, 'readiness_pass_count')}",
        f"- readiness_warning_count: {summary_value(rows, 'readiness_warning_count')}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- action_preview_added: {summary_value(rows, 'action_preview_added') or 'False'}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_active_seed_readiness_warning: monitor only; this is not action preview, order approval, execution approval, or scheduling approval.",
    ]


def vol_candidate_decision_record_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_CANDIDATE_DECISION_RECORD_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_candidate_decision_record_present: False",
            f"- vol_candidate_decision_record_missing_saved_output: {VOL_CANDIDATE_DECISION_RECORD_SUMMARY_PATH}",
            "- vol_candidate_decision_status: missing_saved_output",
            "- vol_candidate_decision_warning: monitor only; missing saved decision record does not approve implementation, execution, or scheduling.",
        ]
    return [
        "- vol_candidate_decision_record_present: True",
        f"- final_candidate_decision_status: {summary_value(rows, 'final_candidate_decision_status')}",
        f"- selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"- incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"- decision: {summary_value(rows, 'decision')}",
        f"- open_blocker_count: {summary_value(rows, 'open_blocker_count')}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "- implementation_approved: False",
        "- paper_live_candidate_approved: False",
        "- seed_change_approved: False",
        "- order_instructions_created: False",
        "- execution_approved: False",
        "- paper_execution_approved: False",
        "- scheduling_approved: False",
        "- vol_candidate_decision_warning: manual discussion only; QQQ100 remains the incumbent seed and this is not implementation, execution, or scheduling approval.",
    ]


def vol_execution_blocker_rollup_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_EXECUTION_BLOCKER_ROLLUP_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_execution_blocker_rollup_present: False",
            f"- vol_execution_blocker_rollup_missing_saved_output: {VOL_EXECUTION_BLOCKER_ROLLUP_SUMMARY_PATH}",
            "- vol_execution_blocker_rollup_status: missing_saved_output",
            "- vol_execution_blocker_rollup_warning: monitor only; missing blocker rollup does not approve execution or scheduling.",
        ]
    return [
        "- vol_execution_blocker_rollup_present: True",
        f"- final_execution_blocker_rollup_status: {summary_value(rows, 'final_execution_blocker_rollup_status')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- execution_blocker_count: {summary_value(rows, 'execution_blocker_count')}",
        f"- closed_blocker_count: {summary_value(rows, 'closed_blocker_count')}",
        f"- criteria_source_reviewed_closed: {summary_value(rows, 'criteria_source_reviewed_closed')}",
        f"- criteria_resolution_plan_open_closed: {summary_value(rows, 'criteria_resolution_plan_open_closed')}",
        f"- approval_criteria_not_approval_closed: {summary_value(rows, 'approval_criteria_not_approval_closed')}",
        f"- ticket_values_not_approved_closed: {summary_value(rows, 'ticket_values_not_approved_closed')}",
        f"- executable_ticket_prerequisites_not_met_closed: {summary_value(rows, 'executable_ticket_prerequisites_not_met_closed')}",
        f"- remaining_known_blockers_after_closeout: {summary_value(rows, 'remaining_known_blockers_after_closeout')}",
        f"- missing_checkpoint_count: {summary_value(rows, 'missing_checkpoint_count')}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- executable_ticket_prerequisites_met: {summary_value(rows, 'executable_ticket_prerequisites_met') or 'False'}",
        f"- executable_ticket_design_allowed: {summary_value(rows, 'executable_ticket_design_allowed') or 'False'}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_execution_blocker_rollup_warning: monitor only; blocker rollup is not execution design, order approval, or scheduling approval.",
    ]


def vol_executable_ticket_gap_list_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_EXECUTABLE_TICKET_GAP_LIST_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_executable_ticket_gap_list_present: False",
            f"- vol_executable_ticket_gap_list_missing_saved_output: {VOL_EXECUTABLE_TICKET_GAP_LIST_SUMMARY_PATH}",
            "- vol_executable_ticket_gap_list_status: missing_saved_output",
            "- vol_executable_ticket_gap_list_warning: monitor only; missing gap list does not approve ticket design, execution, or scheduling.",
        ]
    return [
        "- vol_executable_ticket_gap_list_present: True",
        f"- final_gap_list_status: {summary_value(rows, 'final_gap_list_status')}",
        f"- final_ticket_design_decision: {summary_value(rows, 'final_ticket_design_decision')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"- gap_count: {summary_value(rows, 'gap_count')}",
        f"- critical_gap_count: {summary_value(rows, 'critical_gap_count')}",
        f"- closed_blocker_count: {summary_value(rows, 'closed_blocker_count')}",
        f"- criteria_source_reviewed_closed: {summary_value(rows, 'criteria_source_reviewed_closed')}",
        f"- criteria_resolution_plan_open_closed: {summary_value(rows, 'criteria_resolution_plan_open_closed')}",
        f"- approval_criteria_not_approval_closed: {summary_value(rows, 'approval_criteria_not_approval_closed')}",
        f"- ticket_values_not_approved_closed: {summary_value(rows, 'ticket_values_not_approved_closed')}",
        f"- executable_ticket_prerequisites_not_met_closed: {summary_value(rows, 'executable_ticket_prerequisites_not_met_closed')}",
        f"- remaining_known_blockers_after_closeout: {summary_value(rows, 'remaining_known_blockers_after_closeout')}",
        f"- largest_gap: {summary_value(rows, 'largest_gap')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- order_fields_created: {summary_value(rows, 'order_fields_created') or 'False'}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- executable_ticket_created: {summary_value(rows, 'executable_ticket_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_executable_ticket_gap_list_warning: monitor only; gap list is not ticket design, order approval, execution approval, or scheduling approval.",
    ]


def vol_manual_execution_design_approval_gate_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_MANUAL_EXECUTION_DESIGN_APPROVAL_GATE_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_manual_execution_design_approval_gate_present: False",
            f"- vol_manual_execution_design_approval_gate_missing_saved_output: {VOL_MANUAL_EXECUTION_DESIGN_APPROVAL_GATE_SUMMARY_PATH}",
            "- vol_manual_execution_design_approval_gate_status: missing_saved_output",
            "- vol_manual_execution_design_approval_gate_warning: monitor only; missing approval gate does not approve ticket design, execution, or scheduling.",
        ]
    return [
        "- vol_manual_execution_design_approval_gate_present: True",
        f"- final_approval_gate_status: {summary_value(rows, 'final_approval_gate_status')}",
        f"- final_approval_gate_decision: {summary_value(rows, 'final_approval_gate_decision')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"- explicit_future_prompt_required: {summary_value(rows, 'explicit_future_prompt_required')}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- manual_execution_design_approved: {summary_value(rows, 'manual_execution_design_approved') or 'False'}",
        f"- manual_execution_design_approval_recorded: {summary_value(rows, 'manual_execution_design_approval_recorded') or 'False'}",
        f"- executable_ticket_design_allowed: {summary_value(rows, 'executable_ticket_design_allowed') or 'False'}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_manual_execution_design_approval_gate_warning: monitor only; gate is not approval, ticket design, order approval, execution approval, or scheduling approval.",
    ]


def vol_non_submitting_ticket_schema_design_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_NON_SUBMITTING_TICKET_SCHEMA_DESIGN_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_non_submitting_ticket_schema_design_present: False",
            f"- vol_non_submitting_ticket_schema_design_missing_saved_output: {VOL_NON_SUBMITTING_TICKET_SCHEMA_DESIGN_SUMMARY_PATH}",
            "- vol_non_submitting_ticket_schema_design_status: missing_saved_output",
            "- vol_non_submitting_ticket_schema_design_warning: monitor only; missing schema design does not approve ticket instances, order values, execution, or scheduling.",
        ]
    return [
        "- vol_non_submitting_ticket_schema_design_present: True",
        f"- final_schema_design_status: {summary_value(rows, 'final_schema_design_status')}",
        f"- final_schema_design_decision: {summary_value(rows, 'final_schema_design_decision')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"- schema_field_count: {summary_value(rows, 'schema_field_count')}",
        f"- ticket_instance_created: {summary_value(rows, 'ticket_instance_created') or 'False'}",
        f"- order_values_populated: {summary_value(rows, 'order_values_populated') or 'False'}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- executable_ticket_created: {summary_value(rows, 'executable_ticket_created') or 'False'}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_non_submitting_ticket_schema_design_warning: monitor only; schema design is not a ticket instance, order approval, execution approval, or scheduling approval.",
    ]


def vol_non_submitting_ticket_instance_design_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_NON_SUBMITTING_TICKET_INSTANCE_DESIGN_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_non_submitting_ticket_instance_design_present: False",
            f"- vol_non_submitting_ticket_instance_design_missing_saved_output: {VOL_NON_SUBMITTING_TICKET_INSTANCE_DESIGN_SUMMARY_PATH}",
            "- vol_non_submitting_ticket_instance_design_status: missing_saved_output",
            "- vol_non_submitting_ticket_instance_design_warning: monitor only; missing ticket-instance design does not approve order values, execution, or scheduling.",
        ]
    return [
        "- vol_non_submitting_ticket_instance_design_present: True",
        f"- final_ticket_instance_design_status: {summary_value(rows, 'final_ticket_instance_design_status')}",
        f"- final_ticket_instance_design_decision: {summary_value(rows, 'final_ticket_instance_design_decision')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"- ticket_field_count: {summary_value(rows, 'ticket_field_count')}",
        f"- ticket_instance_created: {summary_value(rows, 'ticket_instance_created') or 'False'}",
        f"- executable_ticket_created: {summary_value(rows, 'executable_ticket_created') or 'False'}",
        f"- order_values_populated: {summary_value(rows, 'order_values_populated') or 'False'}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_non_submitting_ticket_instance_design_warning: monitor only; ticket-instance design is not order approval, execution approval, or scheduling approval.",
    ]


def vol_fresh_broker_pre_ticket_gate_design_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_FRESH_BROKER_PRE_TICKET_GATE_DESIGN_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_fresh_broker_pre_ticket_gate_design_present: False",
            f"- vol_fresh_broker_pre_ticket_gate_design_missing_saved_output: {VOL_FRESH_BROKER_PRE_TICKET_GATE_DESIGN_SUMMARY_PATH}",
            "- vol_fresh_broker_pre_ticket_gate_design_status: missing_saved_output",
            "- vol_fresh_broker_pre_ticket_gate_design_warning: monitor only; missing gate design does not approve broker reads, order values, execution, or scheduling.",
        ]
    return [
        "- vol_fresh_broker_pre_ticket_gate_design_present: True",
        f"- final_pre_ticket_gate_design_status: {summary_value(rows, 'final_pre_ticket_gate_design_status')}",
        f"- final_pre_ticket_gate_design_decision: {summary_value(rows, 'final_pre_ticket_gate_design_decision')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"- gate_check_count: {summary_value(rows, 'gate_check_count')}",
        f"- fresh_broker_pre_ticket_gate_run: {summary_value(rows, 'fresh_broker_pre_ticket_gate_run') or 'False'}",
        f"- readonly_alpaca_check_run: {summary_value(rows, 'readonly_alpaca_check_run') or 'False'}",
        f"- broker_positions_read: {summary_value(rows, 'broker_positions_read') or 'False'}",
        f"- order_values_populated: {summary_value(rows, 'order_values_populated') or 'False'}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_fresh_broker_pre_ticket_gate_design_warning: monitor only; gate design is not a broker read, order approval, execution approval, or scheduling approval.",
    ]


def vol_fresh_broker_pre_ticket_gate_run_readiness_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_FRESH_BROKER_PRE_TICKET_GATE_RUN_READINESS_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_fresh_broker_pre_ticket_gate_run_readiness_present: False",
            f"- vol_fresh_broker_pre_ticket_gate_run_readiness_missing_saved_output: {VOL_FRESH_BROKER_PRE_TICKET_GATE_RUN_READINESS_SUMMARY_PATH}",
            "- vol_fresh_broker_pre_ticket_gate_run_readiness_status: missing_saved_output",
            "- vol_fresh_broker_pre_ticket_gate_run_readiness_warning: monitor only; missing readiness does not approve broker reads, order values, execution, or scheduling.",
        ]
    return [
        "- vol_fresh_broker_pre_ticket_gate_run_readiness_present: True",
        f"- final_pre_ticket_gate_run_readiness_status: {summary_value(rows, 'final_pre_ticket_gate_run_readiness_status')}",
        f"- final_pre_ticket_gate_run_readiness_decision: {summary_value(rows, 'final_pre_ticket_gate_run_readiness_decision')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"- readiness_pass_count: {summary_value(rows, 'readiness_pass_count')}",
        f"- readiness_blocker_count: {summary_value(rows, 'readiness_blocker_count')}",
        f"- ready_to_request_readonly_approval: {summary_value(rows, 'ready_to_request_readonly_approval')}",
        f"- readonly_alpaca_run_approved: {summary_value(rows, 'readonly_alpaca_run_approved') or 'False'}",
        f"- fresh_broker_pre_ticket_gate_run: {summary_value(rows, 'fresh_broker_pre_ticket_gate_run') or 'False'}",
        f"- broker_positions_read: {summary_value(rows, 'broker_positions_read') or 'False'}",
        f"- order_values_populated: {summary_value(rows, 'order_values_populated') or 'False'}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_fresh_broker_pre_ticket_gate_run_readiness_warning: monitor only; readiness can support asking for future read-only approval but is not that approval.",
    ]


def vol_fresh_broker_pre_ticket_gate_run_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_FRESH_BROKER_PRE_TICKET_GATE_RUN_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_fresh_broker_pre_ticket_gate_run_present: False",
            f"- vol_fresh_broker_pre_ticket_gate_run_missing_saved_output: {VOL_FRESH_BROKER_PRE_TICKET_GATE_RUN_SUMMARY_PATH}",
            "- vol_fresh_broker_pre_ticket_gate_run_status: missing_saved_output",
            "- vol_fresh_broker_pre_ticket_gate_run_warning: monitor only; missing read-only gate output does not approve broker reads, ticket values, execution, or scheduling.",
        ]
    return [
        "- vol_fresh_broker_pre_ticket_gate_run_present: True",
        f"- final_pre_ticket_gate_run_status: {summary_value(rows, 'final_pre_ticket_gate_run_status')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"- readonly_confirmation_status: {summary_value(rows, 'readonly_confirmation_status')}",
        f"- broker_position_read_status: {summary_value(rows, 'broker_position_read_status')}",
        f"- position_symbol_count_if_readonly: {summary_value(rows, 'position_symbol_count_if_readonly')}",
        f"- qqq_position_quantity_if_readonly: {summary_value(rows, 'qqq_position_quantity_if_readonly')}",
        f"- ticket_instance_created: {summary_value(rows, 'ticket_instance_created') or 'False'}",
        f"- executable_ticket_created: {summary_value(rows, 'executable_ticket_created') or 'False'}",
        f"- order_values_populated: {summary_value(rows, 'order_values_populated') or 'False'}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- orders_submitted: {summary_value(rows, 'orders_submitted') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_fresh_broker_pre_ticket_gate_run_warning: monitor only; read-only gate context is not ticket value, order approval, execution approval, or scheduling approval.",
    ]


def paper_live_go_no_go_dashboard_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / PAPER_LIVE_GO_NO_GO_DASHBOARD_SUMMARY_PATH)
    if not rows:
        return [
            "- paper_live_go_no_go_dashboard_present: False",
            f"- paper_live_go_no_go_dashboard_missing_saved_output: {PAPER_LIVE_GO_NO_GO_DASHBOARD_SUMMARY_PATH}",
            "- paper_live_go_no_go_status: missing_saved_output",
            "- paper_live_go_no_go_warning: monitor only; missing dashboard does not approve execution or scheduling.",
        ]
    return [
        "- paper_live_go_no_go_dashboard_present: True",
        f"- final_go_no_go_status: {summary_value(rows, 'final_go_no_go_status')}",
        f"- final_go_no_go_decision: {summary_value(rows, 'final_go_no_go_decision')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- previous_ticker: {summary_value(rows, 'previous_ticker')}",
        f"- qqq100_no_action_state: {summary_value(rows, 'qqq100_no_action_state')}",
        f"- vol_largest_blocker: {summary_value(rows, 'vol_largest_blocker')}",
        f"- vol_post_gate_review_status: {summary_value(rows, 'vol_post_gate_review_status')}",
        f"- vol_post_gate_review_decision: {summary_value(rows, 'vol_post_gate_review_decision')}",
        f"- vol_post_gate_largest_blocker: {summary_value(rows, 'vol_post_gate_largest_blocker')}",
        f"- vol_post_gate_saved_qqq_quantity: {summary_value(rows, 'vol_post_gate_saved_qqq_quantity')}",
        f"- vol_ticket_value_design_status: {summary_value(rows, 'vol_ticket_value_design_status')}",
        f"- vol_ticket_value_design_decision: {summary_value(rows, 'vol_ticket_value_design_decision')}",
        f"- vol_ticket_value_largest_blocker: {summary_value(rows, 'vol_ticket_value_largest_blocker')}",
        f"- vol_ticket_prereq_closeout_decision: {summary_value(rows, 'vol_ticket_prereq_closeout_decision')}",
        f"- vol_ticket_approval_readiness_decision: {summary_value(rows, 'vol_ticket_approval_readiness_decision')}",
        f"- vol_ticket_approval_criteria_decision: {summary_value(rows, 'vol_ticket_approval_criteria_decision')}",
        f"- vol_ticket_criteria_resolution_decision: {summary_value(rows, 'vol_ticket_criteria_resolution_decision')}",
        f"- vol_ticket_criteria_source_review_decision: {summary_value(rows, 'vol_ticket_criteria_source_review_decision')}",
        f"- vol_ticket_criteria_blocker_closeout_review_decision: {summary_value(rows, 'vol_ticket_criteria_blocker_closeout_review_decision')}",
        f"- vol_ticket_blocker_specific_review_rollup_decision: {summary_value(rows, 'vol_ticket_blocker_specific_review_rollup_decision')}",
        f"- vol_ticket_closeout_candidate_review_rollup_decision: {summary_value(rows, 'vol_ticket_closeout_candidate_review_rollup_decision')}",
        f"- vol_ticket_criteria_source_closeout_approval_wording_decision: {summary_value(rows, 'vol_ticket_criteria_source_closeout_approval_wording_decision')}",
        f"- vol_ticket_criteria_source_closeout_future_phrase: {summary_value(rows, 'vol_ticket_criteria_source_closeout_future_phrase')}",
        f"- vol_ticket_criteria_source_closeout_record_decision: {summary_value(rows, 'vol_ticket_criteria_source_closeout_record_decision')}",
        f"- vol_ticket_criteria_source_closed_blocker: {summary_value(rows, 'vol_ticket_criteria_source_closed_blocker')}",
        f"- vol_ticket_criteria_source_remaining_blockers: {summary_value(rows, 'vol_ticket_criteria_source_remaining_blockers')}",
        f"- vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision')}",
        f"- vol_ticket_criteria_resolution_plan_closeout_future_phrase: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_closeout_future_phrase')}",
        f"- vol_ticket_criteria_resolution_plan_closeout_record_decision: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_closeout_record_decision')}",
        f"- vol_ticket_criteria_resolution_plan_closed_blocker: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_closed_blocker')}",
        f"- vol_ticket_criteria_resolution_plan_remaining_blockers: {summary_value(rows, 'vol_ticket_criteria_resolution_plan_remaining_blockers')}",
        f"- vol_ticket_approval_criteria_closeout_approval_wording_decision: {summary_value(rows, 'vol_ticket_approval_criteria_closeout_approval_wording_decision')}",
        f"- vol_ticket_approval_criteria_closeout_future_phrase: {summary_value(rows, 'vol_ticket_approval_criteria_closeout_future_phrase')}",
        f"- vol_ticket_approval_criteria_closeout_record_decision: {summary_value(rows, 'vol_ticket_approval_criteria_closeout_record_decision')}",
        f"- vol_ticket_approval_criteria_closed_blocker: {summary_value(rows, 'vol_ticket_approval_criteria_closed_blocker')}",
        f"- vol_ticket_approval_criteria_remaining_blockers: {summary_value(rows, 'vol_ticket_approval_criteria_remaining_blockers')}",
        f"- vol_ticket_final_blockers_closeout_approval_wording_decision: {summary_value(rows, 'vol_ticket_final_blockers_closeout_approval_wording_decision')}",
        f"- vol_ticket_final_blockers_closeout_future_phrase: {summary_value(rows, 'vol_ticket_final_blockers_closeout_future_phrase')}",
        f"- vol_ticket_final_blockers_closeout_record_decision: {summary_value(rows, 'vol_ticket_final_blockers_closeout_record_decision')}",
        f"- vol_ticket_final_blockers_closed_blocker: {summary_value(rows, 'vol_ticket_final_blockers_closed_blocker')}",
        f"- vol_ticket_final_blockers_remaining_blockers: {summary_value(rows, 'vol_ticket_final_blockers_remaining_blockers')}",
        f"- vol_execution_approval_request_readiness_decision: {summary_value(rows, 'vol_execution_approval_request_readiness_decision')}",
        f"- vol_execution_approval_request_ready: {summary_value(rows, 'vol_execution_approval_request_ready')}",
        f"- vol_execution_approval_requested: {summary_value(rows, 'vol_execution_approval_requested')}",
        f"- vol_execution_approval_recorded: {summary_value(rows, 'vol_execution_approval_recorded')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- paper_live_go_no_go_warning: monitor only; dashboard is not order approval, execution approval, or scheduling approval.",
    ]


def summary_value(rows: list[dict[str, str]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def determine_final_status(
    freshness_statuses: list,
    decision_rows_present: bool,
    decisions_execution_false: bool,
    paper_live_monitoring_consistent: bool,
    daily_decision_present: bool,
    daily_decision_approvals_false: bool,
) -> str:
    if (
        has_stale_or_missing(freshness_statuses)
        or not decision_rows_present
        or not paper_live_monitoring_consistent
        or not daily_decision_present
    ):
        return "monitoring_stale_or_missing_inputs"
    if has_warning(freshness_statuses) or not decisions_execution_false or not daily_decision_approvals_false:
        return "monitoring_warning"
    return "healthy_monitoring_state"


def classify_action_required(
    freshness_statuses: list,
    decision_rows_present: bool,
    decisions_execution_false: bool,
    paper_live_monitoring_consistent: bool,
    daily_decision_present: bool,
    daily_decision_approvals_false: bool,
) -> dict[str, str]:
    if (
        has_stale_or_missing(freshness_statuses)
        or not decision_rows_present
        or not paper_live_monitoring_consistent
        or not daily_decision_present
    ):
        reason = (
            "paper_live_monitoring_saved_status_missing_or_inconsistent"
            if not paper_live_monitoring_consistent
            else "qqq100_daily_decision_saved_status_missing"
            if not daily_decision_present
            else "one_or_more_saved_report_inputs_stale_or_missing"
        )
        action = (
            "refresh_report_only_paper_live_monitoring_status"
            if not paper_live_monitoring_consistent
            else "refresh_report_only_qqq100_daily_decision"
            if not daily_decision_present
            else "refresh_or_investigate_saved_monitoring_inputs"
        )
        return {
            "action_required": "manual_review_required",
            "action_reason": reason,
            "suggested_manual_action": action,
        }
    if has_warning(freshness_statuses) or not decisions_execution_false or not daily_decision_approvals_false:
        reason = (
            "one_or_more_saved_report_inputs_warning_stale"
            if has_warning(freshness_statuses)
            else "qqq100_daily_decision_approval_flags_need_review"
            if not daily_decision_approvals_false
            else "one_or_more_saved_report_approval_flags_need_review"
        )
        return {
            "action_required": "refresh_stale_safe_reports",
            "action_reason": reason,
            "suggested_manual_action": "manually_run_safe_refresh_reports",
        }
    return {
        "action_required": "no_action_required",
        "action_reason": "all_status_inputs_fresh_or_acceptable",
        "suggested_manual_action": "none",
    }


def defensive_saved_inputs_present(root: Path) -> bool:
    return all((root / path).exists() for path in DEFENSIVE_SAVED_INPUTS)


def generated_outputs_ignored(root: Path) -> bool:
    return all(is_git_ignored(root, path) and not is_git_tracked(root, path) for path in GENERATED_OUTPUT_PATHS)


def is_git_ignored(root: Path, path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def is_git_tracked(root: Path, path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def print_vps_daily_monitoring_summary(root: Path | str = ".") -> int:
    for line in build_vps_daily_monitoring_summary_lines(root):
        print(line)
    return 0
