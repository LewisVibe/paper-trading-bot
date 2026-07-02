from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_live_go_no_go_dashboard.py"

COMMANDS = ["--paper-live-go-no-go-dashboard", "--show-paper-live-go-no-go-dashboard"]
OUTPUTS = [
    "data/paper_live_go_no_go_dashboard.csv",
    "data/paper_live_go_no_go_dashboard_summary.csv",
    "data/paper_live_go_no_go_dashboard_blockers.csv",
    "data/paper_live_go_no_go_dashboard_evidence.csv",
]

REQUIRED_TOKENS = [
    "paper_live_go_no_go_dashboard_execution_blocked_monitor_only",
    "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY",
    "qqq100_daily_decision_hold_no_action_aligned_long",
    "vol_post_gate_review_status",
    "post_gate_ticket_values_not_approved",
    "vol_ticket_value_design_status",
    "manual_ticket_values_not_approved",
    "vol_ticket_prereq_closeout_status",
    "vol_ticket_approval_readiness_status",
    "vol_ticket_approval_criteria_status",
    "vol_ticket_criteria_resolution_status",
    "vol_ticket_criteria_source_review_status",
    "vol_ticket_criteria_blocker_closeout_review_status",
    "vol_ticket_blocker_specific_review_rollup_status",
    "vol_ticket_closeout_candidate_review_rollup_status",
    "vol_ticket_criteria_source_closeout_approval_wording_status",
    "vol_ticket_criteria_source_closeout_record_status",
    "vol_ticket_criteria_resolution_plan_closeout_approval_wording_status",
    "vol_ticket_criteria_resolution_plan_closeout_record_status",
    "vol_ticket_approval_criteria_closeout_approval_wording_status",
    "vol_ticket_approval_criteria_closeout_record_status",
    "vol_ticket_final_blockers_closeout_approval_wording_status",
    "vol_ticket_final_blockers_closeout_record_status",
    "vol_execution_approval_request_readiness_status",
    "vol_execution_design_approval_wording_status",
    "vol_execution_design_approval_record_status",
    "vol_execution_design_approved",
    "vol_non_submitting_executable_ticket_design_status",
    "vol_non_submitting_executable_ticket_design_decision",
    "vol_ticket_values_approval_record_status",
    "vol_ticket_values_approval_record_decision",
    "vol_ticket_value_discussion_approved",
    "vol_ticket_values_approved",
    "vol_ticket_value_placeholder_decision",
    "vol_ticket_value_quality_gate_decision",
    "vol_ticket_value_proposal_approval_record_decision",
    "vol_proposed_ticket_values_decision",
    "vol_proposed_ticket_values_quality_gate_decision",
    "vol_executable_ticket_draft_readiness_decision",
    "vol_executable_ticket_draft_discussion_ready",
    "vol_non_submitting_executable_ticket_draft_decision",
    "vol_non_submitting_executable_ticket_draft_quality_gate_decision",
    "non_submitting_executable_ticket_is_not_an_order",
    "ticket_value_discussion_is_not_value_approval",
    "ticket_value_placeholders_are_not_order_values",
    "ticket_value_proposal_approval_is_not_values",
    "proposed_ticket_values_are_not_executable",
    "draft_readiness_is_not_a_ticket",
    "non_submitting_ticket_draft_is_not_executable",
    "executable_ticket_prerequisites_not_closed",
    "executable_ticket_approval_not_ready",
    "executable_ticket_approval_criteria_review_required",
    "executable_ticket_criteria_resolution_plan_open",
    "executable_ticket_criteria_source_review_does_not_close_blockers",
    "executable_ticket_criteria_blocker_closeout_review_does_not_close_blockers",
    "executable_ticket_blocker_specific_reviews_do_not_close_blockers",
    "executable_ticket_closeout_candidate_reviews_do_not_close_blockers",
    "executable_ticket_criteria_source_closeout_approval_wording_not_recorded",
    "remaining_execution_ticket_blockers_after_criteria_source_closeout",
    "remaining_execution_ticket_blockers_after_resolution_plan_closeout",
    "remaining_execution_ticket_blockers_after_approval_criteria_closeout",
    "execution_still_not_approved_after_final_ticket_blockers_closeout",
    "execution_design_approval_is_not_order_approval",
    "status_only_monitoring_no_cron_change",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"order_instructions_created": False',
    '"executable_ticket_created": False',
]

FORBIDDEN_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    "submit_order(",
    "cancel_order(",
    "replace_order(",
    "get_all_positions(",
    "get_alpaca_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "config.json",
    "yf.",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_fixture_output(failures)
    verify_vps_daily_summary_integration(failures)

    if failures:
        print("Paper-live go/no-go dashboard verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live go/no-go dashboard verification passed.")
    print("Verified saved-output dashboard, early routing, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command in bot.py: {command}")
        branch = f'sys.argv[1:] == ["{command}"]'
        branch_index = bot_source.find(branch)
        if branch_index < 0:
            failures.append(f"missing early route for {command}")
        elif load_config_index >= 0 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("dashboard module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"module missing output path: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"module contains forbidden token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(
            ["git", "check-ignore", output],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_fixture_output(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.paper_live_go_no_go_dashboard import (  # noqa: PLC0415
        generate_paper_live_go_no_go_dashboard,
        show_paper_live_go_no_go_dashboard,
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_summary(
            data / "paper_live_monitoring_status.csv",
            {
                "active_strategy": "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
                "active_ticker": "MULTI_SLEEVE",
                "previous_seed_strategy": "qqq_100_trend_gate",
                "previous_seed_ticker": "QQQ",
                "recommended_next_step": "hold_no_action_and_monitor_only",
            },
        )
        write_summary(
            data / "qqq100_daily_decision_summary.csv",
            {
                "daily_decision_status": "qqq100_daily_decision_hold_no_action_aligned_long",
                "execution_approved": "False",
                "paper_execution_approved": "False",
                "scheduling_approved": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv",
            {
                "final_execution_blocker_rollup_status": "vol_targeted_growth_paper_live_execution_blocker_rollup_created_manual_review_required",
                "largest_blocker": "executable_ticket_prerequisites_not_met",
                "execution_blocker_count": "10",
                "executable_ticket_prerequisites_met": "False",
                "executable_ticket_design_allowed": "False",
                "order_instructions_created": "False",
                "execution_approved": "False",
                "paper_execution_approved": "False",
                "scheduling_approved": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_post_gate_review_summary.csv",
            {
                "final_post_gate_review_status": "vol_targeted_growth_post_gate_review_manual_review_required",
                "final_post_gate_review_decision": "FRESH_BROKER_CONTEXT_SAVED_TICKET_VALUES_NOT_APPROVED",
                "largest_blocker": "ticket_values_not_approved_after_readonly_context",
                "saved_qqq_position_quantity_if_readonly": "1",
                "execution_approved": "False",
                "paper_execution_approved": "False",
                "scheduling_approved": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_manual_ticket_value_design_summary.csv",
            {
                "final_ticket_value_design_status": "vol_targeted_growth_manual_ticket_value_design_manual_review_required",
                "final_ticket_value_design_decision": "TICKET_VALUE_DESIGN_REVIEW_ONLY_VALUES_NOT_APPROVED",
                "largest_blocker": "ticket_values_not_approved",
                "order_values_populated": "False",
                "order_instructions_created": "False",
                "execution_approved": "False",
                "paper_execution_approved": "False",
                "scheduling_approved": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_prerequisites_closeout_summary.csv",
            {
                "final_prerequisites_closeout_status": "vol_targeted_growth_executable_ticket_prerequisites_closeout_manual_review_required",
                "final_prerequisites_closeout_decision": "EXECUTABLE_TICKET_PREREQUISITES_NOT_CLOSED",
                "largest_blocker": "executable_ticket_values_and_approval_not_approved",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_approval_readiness_summary.csv",
            {
                "final_approval_readiness_status": "vol_targeted_growth_executable_ticket_approval_readiness_not_ready",
                "final_approval_readiness_decision": "NOT_READY_TO_REQUEST_EXECUTABLE_TICKET_APPROVAL",
                "approval_prompt_allowed": "False",
                "largest_blocker": "approval_request_not_ready_prerequisites_open",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_approval_criteria_summary.csv",
            {
                "final_approval_criteria_status": "vol_targeted_growth_executable_ticket_approval_criteria_defined_manual_review_required",
                "final_approval_criteria_decision": "APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED",
                "approval_request_allowed_now": "False",
                "largest_blocker": "approval_readiness_not_ready_and_prerequisites_open",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_summary.csv",
            {
                "final_resolution_plan_status": "vol_targeted_growth_executable_ticket_criteria_resolution_plan_created_manual_review_required",
                "final_resolution_plan_decision": "CRITERIA_BLOCKER_RESOLUTION_PLAN_CREATED_APPROVAL_STILL_BLOCKED",
                "approval_request_allowed_now": "False",
                "largest_blocker": "criteria_blockers_not_resolved",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_source_review_summary.csv",
            {
                "final_source_review_status": "vol_targeted_growth_executable_ticket_criteria_source_review_manual_review_required",
                "final_source_review_decision": "CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED",
                "source_review_result": "source_consistent_for_manual_review",
                "largest_blocker": "criteria_source_review_does_not_close_blockers",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_summary.csv",
            {
                "final_blocker_closeout_review_status": "vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_manual_review_required",
                "final_blocker_closeout_review_decision": "CRITERIA_BLOCKERS_REVIEWED_NONE_CLOSED",
                "largest_blocker": "criteria_blockers_reviewed_but_not_closed",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_blocker_specific_review_rollup_summary.csv",
            {
                "final_review_status": "vol_targeted_growth_criteria_blocker_specific_review_rollup_manual_review_required",
                "final_review_decision": "CRITERIA_BLOCKER_SPECIFIC_REVIEWS_CREATED_NONE_CLOSED",
                "largest_blocker": "blocker_specific_reviews_do_not_close_blockers",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_closeout_candidate_review_rollup_summary.csv",
            {
                "final_candidate_review_status": "vol_targeted_growth_criteria_closeout_candidate_review_rollup_manual_review_required",
                "final_candidate_review_decision": "CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED",
                "largest_blocker": "closeout_candidates_reviewed_none_closed",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording_summary.csv",
            {
                "final_approval_wording_status": "vol_targeted_growth_criteria_source_closeout_approval_wording_manual_review_required",
                "final_approval_wording_decision": "CRITERIA_SOURCE_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
                "future_approval_phrase": "I approve closing the criteria_source_reviewed blocker only.",
                "largest_blocker": "approval_wording_defined_but_not_recorded",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv",
            {
                "final_closeout_record_status": "vol_targeted_growth_criteria_source_closeout_recorded_manual_review_required",
                "final_closeout_record_decision": "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY",
                "closed_blocker": "criteria_source_reviewed",
                "remaining_known_blockers": "criteria_resolution_plan_open;approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_approval_wording_summary.csv",
            {
                "final_approval_wording_status": "vol_targeted_growth_criteria_resolution_plan_closeout_approval_wording_manual_review_required",
                "final_approval_wording_decision": "CRITERIA_RESOLUTION_PLAN_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
                "future_approval_phrase": "I approve closing the criteria_resolution_plan_open blocker only.",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_record_summary.csv",
            {
                "final_closeout_record_status": "vol_targeted_growth_criteria_resolution_plan_closeout_recorded_manual_review_required",
                "final_closeout_record_decision": "CRITERIA_RESOLUTION_PLAN_OPEN_BLOCKER_CLOSED_ONLY",
                "closed_blocker": "criteria_resolution_plan_open",
                "remaining_known_blockers": "approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_approval_criteria_closeout_approval_wording_summary.csv",
            {
                "final_approval_wording_status": "vol_targeted_growth_approval_criteria_closeout_approval_wording_manual_review_required",
                "final_approval_wording_decision": "APPROVAL_CRITERIA_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
                "future_approval_phrase": "I approve closing the approval_criteria_not_approval blocker only.",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_summary.csv",
            {
                "final_closeout_record_status": "vol_targeted_growth_approval_criteria_closeout_recorded_manual_review_required",
                "final_closeout_record_decision": "APPROVAL_CRITERIA_NOT_APPROVAL_BLOCKER_CLOSED_ONLY",
                "closed_blocker": "approval_criteria_not_approval",
                "remaining_known_blockers": "ticket_values_not_approved;executable_ticket_prerequisites_not_met",
            },
        )
        write_summary(
            data / "vol_targeted_growth_final_ticket_blockers_closeout_approval_wording_summary.csv",
            {
                "final_approval_wording_status": "vol_targeted_growth_final_ticket_blockers_closeout_approval_wording_manual_review_required",
                "final_approval_wording_decision": "FINAL_TICKET_BLOCKERS_CLOSEOUT_WORDING_DEFINED_NOT_APPROVED",
                "future_approval_phrase": "I approve closing the final ticket blockers only; do not create or submit orders.",
            },
        )
        write_summary(
            data / "vol_targeted_growth_final_ticket_blockers_closeout_record_summary.csv",
            {
                "final_closeout_record_status": "vol_targeted_growth_final_ticket_blockers_closeout_recorded_manual_review_required",
                "final_closeout_record_decision": "FINAL_TICKET_BLOCKERS_CLOSED_NO_EXECUTION_APPROVAL",
                "closed_blocker": "ticket_values_not_approved;executable_ticket_prerequisites_not_met",
                "remaining_known_blockers": "none",
            },
        )
        write_summary(
            data / "vol_targeted_growth_execution_approval_request_readiness_summary.csv",
            {
                "final_readiness_status": "vol_targeted_growth_execution_approval_request_readiness_manual_review_required",
                "final_readiness_decision": "READY_FOR_SEPARATE_EXECUTION_APPROVAL_REQUEST_NOT_APPROVED",
                "approval_request_ready": "True",
                "approval_requested": "False",
                "approval_recorded": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_execution_design_approval_wording_summary.csv",
            {
                "final_execution_design_wording_status": "vol_targeted_growth_execution_design_approval_wording_manual_review_required",
                "final_execution_design_wording_decision": "EXECUTION_DESIGN_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
                "approval_phrase": "I approve execution design only for the active volatility seed; do not create or submit orders.",
            },
        )
        write_summary(
            data / "vol_targeted_growth_execution_design_approval_record_summary.csv",
            {
                "final_execution_design_record_status": "vol_targeted_growth_execution_design_approval_recorded_manual_review_required",
                "final_execution_design_record_decision": "EXECUTION_DESIGN_APPROVED_NO_ORDER_OR_EXECUTION_APPROVAL",
                "execution_design_approved": "True",
                "manual_execution_design_approval_recorded": "True",
            },
        )
        write_summary(
            data / "vol_targeted_growth_non_submitting_executable_ticket_design_summary.csv",
            {
                "final_executable_ticket_design_status": "vol_targeted_growth_non_submitting_executable_ticket_design_created_manual_review_required",
                "final_executable_ticket_design_decision": "NON_SUBMITTING_EXECUTABLE_TICKET_DESIGNED_NO_ORDER_VALUES",
                "order_values_populated": "False",
                "executable_ticket_created": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_ticket_values_approval_record_summary.csv",
            {
                "final_ticket_values_record_status": "vol_targeted_growth_ticket_values_approval_recorded_manual_review_required",
                "final_ticket_values_record_decision": "TICKET_VALUE_DISCUSSION_APPROVED_NO_ORDER_VALUES",
                "ticket_value_discussion_approved": "True",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_ticket_value_placeholders_summary.csv",
            {
                "final_ticket_value_placeholder_decision": "NON_EXECUTABLE_TICKET_VALUE_PLACEHOLDERS_CREATED_NO_VALUES",
                "populated_order_value_count": "0",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_ticket_value_quality_gate_summary.csv",
            {
                "final_ticket_value_quality_gate_decision": "TICKET_VALUE_PLACEHOLDERS_QUALITY_GATE_PASSED_NO_EXECUTION",
                "quality_gate_passed": "True",
                "populated_order_value_count": "0",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_ticket_value_proposal_approval_record_summary.csv",
            {
                "final_ticket_value_proposal_record_decision": "TICKET_VALUE_PROPOSAL_DISCUSSION_APPROVED_NO_VALUES_POPULATED",
                "ticket_value_proposal_discussion_approved": "True",
                "proposed_ticket_values_created": "False",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_proposed_ticket_values_summary.csv",
            {
                "final_proposed_ticket_values_decision": "PROPOSED_TICKET_VALUES_CREATED_REVIEW_ONLY_NOT_EXECUTABLE",
                "proposed_ticket_values_created": "True",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_proposed_ticket_values_quality_gate_summary.csv",
            {
                "final_proposed_ticket_values_quality_gate_decision": "PROPOSED_TICKET_VALUES_QUALITY_GATE_PASSED_NO_EXECUTION",
                "quality_gate_passed": "True",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_draft_readiness_summary.csv",
            {
                "final_executable_ticket_draft_readiness_decision": "READY_TO_DISCUSS_NON_SUBMITTING_DRAFT_VALUES_NOT_EXECUTABLE",
                "draft_discussion_ready": "True",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
                "executable_ticket_created": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_non_submitting_executable_ticket_draft_summary.csv",
            {
                "final_ticket_draft_decision": "NON_SUBMITTING_EXECUTABLE_TICKET_DRAFT_CREATED_NOT_EXECUTABLE",
                "draft_ticket_created": "True",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
                "executable_ticket_created": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_summary.csv",
            {
                "final_ticket_draft_quality_decision": "NON_SUBMITTING_EXECUTABLE_TICKET_DRAFT_QUALITY_GATE_PASSED_NO_EXECUTION",
                "quality_gate_passed": "True",
                "ticket_values_approved": "False",
                "order_values_populated": "False",
                "executable_ticket_created": "False",
            },
        )
        write_summary(
            data / "paper_live_checklist_status_summary.csv",
            {
                "checklist_phase_status": "paper_live_checklist_vol_targeted_seed_status_only_phase_ready_manual_review",
                "execution_approved": "False",
                "paper_execution_approved": "False",
                "scheduling_approved": "False",
            },
        )
        result = generate_paper_live_go_no_go_dashboard(root)
        status_code, lines = show_paper_live_go_no_go_dashboard(root)

    output = "\n".join(
        [
            *result.summary_lines,
            *lines,
            *[str(row) for row in result.blocker_rows],
        ]
    )
    if status_code != 0:
        failures.append("dashboard display should return 0 after generation")
    for phrase in [
        "paper_live_go_no_go_dashboard_execution_blocked_monitor_only",
        "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY",
        "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
        "MULTI_SLEEVE",
        "qqq_100_trend_gate",
        "QQQ",
        "qqq100_daily_decision_hold_no_action_aligned_long",
        "hold_no_action_aligned_long",
        "vol_targeted_growth_paper_live_execution_blocker_rollup_created_manual_review_required",
        "executable_ticket_prerequisites_not_met",
        "vol_targeted_growth_post_gate_review_manual_review_required",
        "FRESH_BROKER_CONTEXT_SAVED_TICKET_VALUES_NOT_APPROVED",
        "ticket_values_not_approved_after_readonly_context",
        "vol_post_gate_saved_qqq_quantity: 1",
        "vol_targeted_growth_manual_ticket_value_design_manual_review_required",
        "TICKET_VALUE_DESIGN_REVIEW_ONLY_VALUES_NOT_APPROVED",
        "ticket_values_not_approved",
        "EXECUTABLE_TICKET_PREREQUISITES_NOT_CLOSED",
        "NOT_READY_TO_REQUEST_EXECUTABLE_TICKET_APPROVAL",
        "APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED",
        "CRITERIA_BLOCKER_RESOLUTION_PLAN_CREATED_APPROVAL_STILL_BLOCKED",
        "CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED",
        "CRITERIA_BLOCKERS_REVIEWED_NONE_CLOSED",
        "CRITERIA_BLOCKER_SPECIFIC_REVIEWS_CREATED_NONE_CLOSED",
        "CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED",
        "CRITERIA_SOURCE_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
        "I approve closing the criteria_source_reviewed blocker only.",
        "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY",
        "criteria_source_reviewed",
        "CRITERIA_RESOLUTION_PLAN_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
        "I approve closing the criteria_resolution_plan_open blocker only.",
        "CRITERIA_RESOLUTION_PLAN_OPEN_BLOCKER_CLOSED_ONLY",
        "criteria_resolution_plan_open",
        "approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met",
        "APPROVAL_CRITERIA_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
        "I approve closing the approval_criteria_not_approval blocker only.",
        "APPROVAL_CRITERIA_NOT_APPROVAL_BLOCKER_CLOSED_ONLY",
        "ticket_values_not_approved;executable_ticket_prerequisites_not_met",
        "FINAL_TICKET_BLOCKERS_CLOSEOUT_WORDING_DEFINED_NOT_APPROVED",
        "I approve closing the final ticket blockers only; do not create or submit orders.",
        "FINAL_TICKET_BLOCKERS_CLOSED_NO_EXECUTION_APPROVAL",
        "READY_FOR_SEPARATE_EXECUTION_APPROVAL_REQUEST_NOT_APPROVED",
        "vol_execution_approval_request_ready: True",
        "vol_execution_approval_requested: False",
        "vol_execution_approval_recorded: False",
        "EXECUTION_DESIGN_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
        "I approve execution design only for the active volatility seed; do not create or submit orders.",
        "EXECUTION_DESIGN_APPROVED_NO_ORDER_OR_EXECUTION_APPROVAL",
        "vol_execution_design_approved: True",
        "NON_SUBMITTING_EXECUTABLE_TICKET_DESIGNED_NO_ORDER_VALUES",
        "vol_non_submitting_executable_ticket_order_values_populated: False",
        "TICKET_VALUE_DISCUSSION_APPROVED_NO_ORDER_VALUES",
        "vol_ticket_value_discussion_approved: True",
        "vol_ticket_values_approved: False",
        "ticket_value_discussion_is_not_value_approval",
        "NON_EXECUTABLE_TICKET_VALUE_PLACEHOLDERS_CREATED_NO_VALUES",
        "TICKET_VALUE_PLACEHOLDERS_QUALITY_GATE_PASSED_NO_EXECUTION",
        "ticket_value_placeholders_are_not_order_values",
        "TICKET_VALUE_PROPOSAL_DISCUSSION_APPROVED_NO_VALUES_POPULATED",
        "ticket_value_proposal_approval_is_not_values",
        "PROPOSED_TICKET_VALUES_CREATED_REVIEW_ONLY_NOT_EXECUTABLE",
        "PROPOSED_TICKET_VALUES_QUALITY_GATE_PASSED_NO_EXECUTION",
        "proposed_ticket_values_are_not_executable",
        "READY_TO_DISCUSS_NON_SUBMITTING_DRAFT_VALUES_NOT_EXECUTABLE",
        "vol_executable_ticket_draft_discussion_ready: True",
        "draft_readiness_is_not_a_ticket",
        "NON_SUBMITTING_EXECUTABLE_TICKET_DRAFT_CREATED_NOT_EXECUTABLE",
        "NON_SUBMITTING_EXECUTABLE_TICKET_DRAFT_QUALITY_GATE_PASSED_NO_EXECUTION",
        "non_submitting_ticket_draft_is_not_executable",
        "status_only_monitoring_no_cron_change",
        "order_instructions_created=false",
        "executable_ticket_created=false",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")


def verify_vps_daily_summary_integration(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py")
    for phrase in [
        "PAPER_LIVE_GO_NO_GO_DASHBOARD_SUMMARY_PATH",
        "Paper-live go/no-go dashboard:",
        "paper_live_go_no_go_dashboard_status_lines",
        "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY",
        "vol_executable_ticket_draft_readiness_decision",
        "vol_non_submitting_executable_ticket_draft_decision",
        "paper_live_go_no_go_warning: monitor only;",
    ]:
        if phrase not in source:
            failures.append(f"VPS daily summary missing go/no-go integration phrase: {phrase}")


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
