from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT_PATH = ROOT / "bot.py"
MODULE_PATH = ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py"
COMMAND = "--vps-daily-monitoring-summary"

REQUIRED_OUTPUT_PHRASES = [
    "VPS DAILY MONITORING SUMMARY. REPORT ONLY. NOT EXECUTION.",
    "execution_approved=False",
    "scheduling_approved=False",
    "Safety reminders:",
    "Lock-wrapped safe commands:",
    "Promoted review summary:",
    "Defensive refresh summary:",
    "Paper-live monitoring status:",
    "active_strategy: higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
    "active_ticker: MULTI_SLEEVE",
    "previous_seed_strategy: qqq_100_trend_gate",
    "previous_seed_ticker: QQQ",
    "Volatility active-seed readiness:",
    "vol_active_seed_readiness_present:",
    "vol_active_seed_readiness_warning: monitor only;",
    "Volatility candidate decision record:",
    "vol_candidate_decision_record_present:",
    "vol_candidate_decision_warning:",
    "Volatility paper-live execution blocker rollup:",
    "vol_execution_blocker_rollup_present:",
    "vol_execution_blocker_rollup_warning: monitor only;",
    "Volatility executable ticket gap list:",
    "vol_executable_ticket_gap_list_present:",
    "vol_executable_ticket_gap_list_warning: monitor only;",
    "Volatility manual execution-design approval gate:",
    "vol_manual_execution_design_approval_gate_present:",
    "vol_manual_execution_design_approval_gate_warning: monitor only;",
    "Volatility non-submitting ticket schema design:",
    "vol_non_submitting_ticket_schema_design_present:",
    "vol_non_submitting_ticket_schema_design_warning: monitor only;",
    "Volatility non-submitting ticket-instance design:",
    "vol_non_submitting_ticket_instance_design_present:",
    "vol_non_submitting_ticket_instance_design_warning: monitor only;",
    "Volatility fresh broker pre-ticket gate design:",
    "vol_fresh_broker_pre_ticket_gate_design_present:",
    "vol_fresh_broker_pre_ticket_gate_design_warning: monitor only;",
    "Volatility fresh broker pre-ticket gate run-readiness:",
    "vol_fresh_broker_pre_ticket_gate_run_readiness_present:",
    "vol_fresh_broker_pre_ticket_gate_run_readiness_warning: monitor only;",
    "Volatility fresh broker pre-ticket gate run:",
    "vol_fresh_broker_pre_ticket_gate_run_present:",
    "vol_fresh_broker_pre_ticket_gate_run_warning: monitor only;",
    "QQQ100 daily decision:",
    "qqq100_daily_decision_present: True",
    "daily_decision_status: qqq100_daily_decision_hold_no_action_aligned_long",
    "manual_discussion_status: manual_trade_discussion_not_needed",
    "QQQ100 manual flatten readiness:",
    "qqq100_manual_flatten_readiness_present: True",
    "flatten_readiness_status: flatten_not_needed_currently",
    "manual_flatten_discussion_status: manual_flatten_discussion_not_needed_currently",
    "flatten_execution_approved: False",
    "QQQ100 manual flatten runbook:",
    "qqq100_manual_flatten_runbook_present: True",
    "runbook_status: manual_flatten_runbook_not_needed_currently",
    "manual_flatten_approved: False",
    "Paper-live go/no-go dashboard:",
    "paper_live_go_no_go_dashboard_present:",
    "paper_live_go_no_go_warning: monitor only;",
    "vol_ticket_prereq_closeout_decision:",
    "vol_ticket_approval_readiness_decision:",
    "vol_ticket_approval_criteria_decision:",
    "vol_ticket_criteria_resolution_decision:",
    "vol_ticket_criteria_source_review_decision:",
    "vol_ticket_criteria_blocker_closeout_review_decision:",
    "vol_ticket_blocker_specific_review_rollup_decision:",
    "vol_ticket_closeout_candidate_review_rollup_decision:",
    "vol_ticket_criteria_source_closeout_approval_wording_decision:",
    "vol_ticket_criteria_source_closeout_future_phrase:",
    "vol_ticket_criteria_source_closeout_record_decision:",
    "vol_ticket_criteria_source_closed_blocker:",
    "vol_ticket_criteria_source_remaining_blockers:",
    "vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision:",
    "vol_ticket_criteria_resolution_plan_closeout_future_phrase:",
    "vol_ticket_criteria_resolution_plan_closeout_record_decision:",
    "vol_ticket_criteria_resolution_plan_closed_blocker:",
    "vol_ticket_criteria_resolution_plan_remaining_blockers:",
    "vol_ticket_approval_criteria_closeout_approval_wording_decision:",
    "vol_ticket_approval_criteria_closeout_future_phrase:",
    "vol_ticket_approval_criteria_closeout_record_decision:",
    "vol_ticket_approval_criteria_closed_blocker:",
    "vol_ticket_approval_criteria_remaining_blockers:",
    "vol_execution_design_approval_wording_decision:",
    "vol_execution_design_approval_record_decision:",
    "vol_execution_design_approved:",
    "vol_non_submitting_executable_ticket_design_decision:",
    "vol_non_submitting_executable_ticket_order_values_populated:",
    "vol_ticket_values_approval_record_decision:",
    "vol_ticket_value_discussion_approved:",
    "vol_ticket_values_approved:",
    "vol_ticket_value_placeholder_decision:",
    "vol_ticket_value_quality_gate_decision:",
    "vol_ticket_value_proposal_approval_record_decision:",
    "vol_proposed_ticket_values_decision:",
    "vol_proposed_ticket_values_quality_gate_decision:",
    "vol_executable_ticket_draft_readiness_decision:",
    "vol_executable_ticket_draft_discussion_ready:",
    "vol_non_submitting_executable_ticket_draft_decision:",
    "vol_non_submitting_executable_ticket_draft_quality_gate_decision:",
    "vol_draft_ticket_value_approval_readiness_decision:",
    "vol_ticket_value_approval_request_ready:",
    "alignment_state: aligned_long",
    "followup_policy_status: no_action_required_already_aligned",
    "recommended_next_step: hold_no_action_and_monitor_only",
    "followup_order_approved: False",
    "repeat_execution_approved: False",
    "never_schedule_order_capable_commands: True",
    "Saved-output freshness:",
    "final_status:",
    "action_required:",
    "action_reason:",
    "suggested_manual_action:",
]

REQUIRED_FINAL_STATES = [
    "healthy_monitoring_state",
    "monitoring_warning",
    "monitoring_stale_or_missing_inputs",
]

REQUIRED_ACTION_STATES = [
    "no_action_required",
    "refresh_stale_safe_reports",
    "manual_review_required",
    "all_status_inputs_fresh_or_acceptable",
    "one_or_more_saved_report_inputs_warning_stale",
    "one_or_more_saved_report_inputs_stale_or_missing",
    "manually_run_safe_refresh_reports",
    "refresh_or_investigate_saved_monitoring_inputs",
    "paper_live_monitoring_saved_status_missing_or_inconsistent",
    "refresh_report_only_paper_live_monitoring_status",
    "qqq100_daily_decision_saved_status_missing",
    "refresh_report_only_qqq100_daily_decision",
    "qqq100_daily_decision_approval_flags_need_review",
    "vol_active_seed_readiness_missing_saved_output",
    "vol_active_seed_readiness_status",
    "vol_candidate_decision_record_missing_saved_output",
    "vol_candidate_decision_status",
    "vol_execution_blocker_rollup_missing_saved_output",
    "vol_execution_blocker_rollup_status",
    "vol_executable_ticket_gap_list_missing_saved_output",
    "vol_executable_ticket_gap_list_status",
    "vol_manual_execution_design_approval_gate_missing_saved_output",
    "vol_manual_execution_design_approval_gate_status",
    "vol_non_submitting_ticket_schema_design_missing_saved_output",
    "vol_non_submitting_ticket_schema_design_status",
    "vol_non_submitting_ticket_instance_design_missing_saved_output",
    "vol_non_submitting_ticket_instance_design_status",
    "vol_fresh_broker_pre_ticket_gate_design_missing_saved_output",
    "vol_fresh_broker_pre_ticket_gate_design_status",
    "vol_fresh_broker_pre_ticket_gate_run_readiness_missing_saved_output",
    "vol_fresh_broker_pre_ticket_gate_run_readiness_status",
    "vol_fresh_broker_pre_ticket_gate_run_missing_saved_output",
    "vol_fresh_broker_pre_ticket_gate_run_status",
    "paper_live_go_no_go_dashboard_missing_saved_output",
    "paper_live_go_no_go_status",
]

FORBIDDEN_CALLS = [
    "TradingClient(",
    "get_alpaca_positions(",
    "submit_order(",
    "cancel_order(",
    "create_order(",
    "send_discord_alert(",
    "sqlite3.connect(",
    "insert_trade_log(",
    "yf.download(",
    "download_close_prices(",
    "download_backtest_prices(",
    "load_config(",
    "open(\"config.json\"",
    "read_text(\"config.json\"",
]


def main() -> int:
    failures: list[str] = []
    verify_command_registered(failures)
    verify_module_source(failures)
    verify_command_output(failures)

    if failures:
        print("VPS daily monitoring summary verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("VPS daily monitoring summary verification passed.")
    print("Verified command registration, report-only output, false approval flags, compact saved-output summaries, and no forbidden calls.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    bot_source = read_text(BOT_PATH)
    if COMMAND not in bot_source:
        failures.append(f"{COMMAND} is missing from bot.py")
    if f'sys.argv[1:] == ["{COMMAND}"]' not in bot_source:
        failures.append(f"{COMMAND} should have an exact early report-only route")


def verify_module_source(failures: list[str]) -> None:
    source = read_text(MODULE_PATH)
    for token in REQUIRED_FINAL_STATES:
        if token not in source:
            failures.append(f"Daily summary missing final state: {token}")
    for token in REQUIRED_ACTION_STATES:
        if token not in source:
            failures.append(f"Daily summary missing action classifier token: {token}")
    for token in FORBIDDEN_CALLS:
        if token in source:
            failures.append(f"Daily summary contains forbidden token: {token}")
    for token in ["write_text(", "DictWriter", "with path.open(\"w\"", ".mkdir("]:
        if token in source:
            failures.append(f"Daily summary should not create generated files: {token}")
    for high_risk in ["python bot.py", "--paper-order-test", "--execute-slow-sma-paper", "--confirm-slow-sma-paper", "--confirm-paper-order"]:
        if high_risk in source:
            failures.append(f"Daily summary should not suggest high-risk command text: {high_risk}")


def verify_command_output(failures: list[str]) -> None:
    completed = subprocess.run(
        [sys.executable, "bot.py", COMMAND],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    if completed.returncode != 0:
        failures.append(f"{COMMAND} failed with exit code {completed.returncode}")
    for phrase in REQUIRED_OUTPUT_PHRASES:
        if phrase not in output:
            failures.append(f"Daily summary output missing phrase: {phrase}")
    if "vol_active_seed_readiness_present: True" in output:
        for phrase in [
            "final_active_seed_readiness_status:",
            "active_seed: higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
            "active_ticker: MULTI_SLEEVE",
            "previous_seed: qqq_100_trend_gate",
            "readiness_pass_count:",
            "readiness_warning_count:",
            "action_preview_added: False",
            "order_instructions_created: False",
            "execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary active-seed section missing phrase: {phrase}")
    elif "vol_active_seed_readiness_present: False" in output:
        for phrase in [
            "vol_active_seed_readiness_missing_saved_output: data/vol_targeted_growth_active_seed_readiness_summary.csv",
            "vol_active_seed_readiness_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved active-seed section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether active-seed readiness is present")
    if "vol_candidate_decision_record_present: True" in output:
        for phrase in [
            "final_candidate_decision_status: vol_targeted_growth_candidate_decision_manual_discussion_only",
            "selected_candidate: higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
            "incumbent_seed: qqq_100_trend_gate/QQQ",
            "decision: manual_discussion_only_no_implementation_approval",
            "open_blocker_count:",
            "implementation_approved: False",
            "paper_live_candidate_approved: False",
            "seed_change_approved: False",
            "order_instructions_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary candidate decision section missing phrase: {phrase}")
    elif "vol_candidate_decision_record_present: False" in output:
        for phrase in [
            "vol_candidate_decision_record_missing_saved_output: data/vol_targeted_growth_candidate_decision_record_summary.csv",
            "vol_candidate_decision_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved candidate decision section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether candidate decision record is present")
    if "vol_execution_blocker_rollup_present: True" in output:
        for phrase in [
            "final_execution_blocker_rollup_status: vol_targeted_growth_paper_live_execution_blocker_rollup_created_manual_review_required",
            "execution_blocker_count:",
            "executable_ticket_prerequisites_met: False",
            "executable_ticket_design_allowed: False",
            "order_instructions_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary execution blocker rollup section missing phrase: {phrase}")
    elif "vol_execution_blocker_rollup_present: False" in output:
        for phrase in [
            "vol_execution_blocker_rollup_missing_saved_output: data/vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv",
            "vol_execution_blocker_rollup_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved execution blocker rollup section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether execution blocker rollup is present")
    if "vol_executable_ticket_gap_list_present: True" in output:
        for phrase in [
            "final_gap_list_status: vol_targeted_growth_executable_ticket_gap_list_execution_blocked_manual_review_required",
            "final_ticket_design_decision: EXECUTABLE_TICKET_DESIGN_NOT_READY",
            "gap_count:",
            "critical_gap_count:",
            "largest_gap: execution_not_approved",
            "order_fields_created: False",
            "order_instructions_created: False",
            "executable_ticket_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary executable ticket gap list section missing phrase: {phrase}")
    elif "vol_executable_ticket_gap_list_present: False" in output:
        for phrase in [
            "vol_executable_ticket_gap_list_missing_saved_output: data/vol_targeted_growth_executable_ticket_gap_list_summary.csv",
            "vol_executable_ticket_gap_list_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved executable ticket gap list section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether executable ticket gap list is present")
    if "vol_manual_execution_design_approval_gate_present: True" in output:
        for phrase in [
            "final_approval_gate_status: vol_targeted_growth_manual_execution_design_approval_gate_not_approved",
            "final_approval_gate_decision: MANUAL_EXECUTION_DESIGN_APPROVAL_NOT_RECORDED",
            "explicit_future_prompt_required: True",
            "largest_blocker: explicit_future_prompt_required",
            "manual_execution_design_approved: False",
            "manual_execution_design_approval_recorded: False",
            "executable_ticket_design_allowed: False",
            "order_instructions_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary manual execution-design approval gate section missing phrase: {phrase}")
    elif "vol_manual_execution_design_approval_gate_present: False" in output:
        for phrase in [
            "vol_manual_execution_design_approval_gate_missing_saved_output: data/vol_targeted_growth_manual_execution_design_approval_gate_summary.csv",
            "vol_manual_execution_design_approval_gate_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved manual execution-design approval gate section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether manual execution-design approval gate is present")
    if "vol_non_submitting_ticket_schema_design_present: True" in output:
        for phrase in [
            "final_schema_design_status: vol_targeted_growth_non_submitting_ticket_schema_design_created_manual_review_required",
            "final_schema_design_decision: NON_SUBMITTING_TICKET_SCHEMA_DESIGNED_NO_TICKET_CREATED",
            "schema_field_count:",
            "ticket_instance_created: False",
            "order_values_populated: False",
            "largest_blocker: ticket_instance_not_approved",
            "executable_ticket_created: False",
            "order_instructions_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary non-submitting ticket schema design section missing phrase: {phrase}")
    elif "vol_non_submitting_ticket_schema_design_present: False" in output:
        for phrase in [
            "vol_non_submitting_ticket_schema_design_missing_saved_output: data/vol_targeted_growth_non_submitting_ticket_schema_design_summary.csv",
            "vol_non_submitting_ticket_schema_design_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved non-submitting ticket schema design section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether non-submitting ticket schema design is present")
    if "vol_non_submitting_ticket_instance_design_present: True" in output:
        for phrase in [
            "final_ticket_instance_design_status: vol_targeted_growth_non_submitting_ticket_instance_design_created_manual_review_required",
            "final_ticket_instance_design_decision: NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES",
            "ticket_field_count:",
            "ticket_instance_created: False",
            "executable_ticket_created: False",
            "order_values_populated: False",
            "largest_blocker: fresh_broker_pre_ticket_gate_not_created",
            "order_instructions_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary non-submitting ticket-instance design section missing phrase: {phrase}")
    elif "vol_non_submitting_ticket_instance_design_present: False" in output:
        for phrase in [
            "vol_non_submitting_ticket_instance_design_missing_saved_output: data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv",
            "vol_non_submitting_ticket_instance_design_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved non-submitting ticket-instance design section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether non-submitting ticket-instance design is present")
    if "vol_fresh_broker_pre_ticket_gate_design_present: True" in output:
        for phrase in [
            "final_pre_ticket_gate_design_status: vol_targeted_growth_fresh_broker_pre_ticket_gate_design_created_manual_review_required",
            "final_pre_ticket_gate_design_decision: FRESH_BROKER_PRE_TICKET_GATE_DESIGNED_NOT_RUN",
            "gate_check_count:",
            "fresh_broker_pre_ticket_gate_run: False",
            "readonly_alpaca_check_run: False",
            "broker_positions_read: False",
            "order_values_populated: False",
            "largest_blocker: future_explicit_readonly_broker_gate_run_not_approved",
            "order_instructions_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary fresh broker pre-ticket gate design section missing phrase: {phrase}")
    elif "vol_fresh_broker_pre_ticket_gate_design_present: False" in output:
        for phrase in [
            "vol_fresh_broker_pre_ticket_gate_design_missing_saved_output: data/vol_targeted_growth_fresh_broker_pre_ticket_gate_design_summary.csv",
            "vol_fresh_broker_pre_ticket_gate_design_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved fresh broker pre-ticket gate design section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether fresh broker pre-ticket gate design is present")
    if "vol_fresh_broker_pre_ticket_gate_run_readiness_present: True" in output:
        for phrase in [
            "final_pre_ticket_gate_run_readiness_status:",
            "final_pre_ticket_gate_run_readiness_decision:",
            "readiness_pass_count:",
            "readiness_blocker_count:",
            "ready_to_request_readonly_approval:",
            "readonly_alpaca_run_approved: False",
            "fresh_broker_pre_ticket_gate_run: False",
            "broker_positions_read: False",
            "order_values_populated: False",
            "order_instructions_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary fresh broker pre-ticket gate run-readiness section missing phrase: {phrase}")
    elif "vol_fresh_broker_pre_ticket_gate_run_readiness_present: False" in output:
        for phrase in [
            "vol_fresh_broker_pre_ticket_gate_run_readiness_missing_saved_output: data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_summary.csv",
            "vol_fresh_broker_pre_ticket_gate_run_readiness_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved fresh broker pre-ticket gate run-readiness section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether fresh broker pre-ticket gate run-readiness is present")
    if "vol_fresh_broker_pre_ticket_gate_run_present: True" in output:
        for phrase in [
            "final_pre_ticket_gate_run_status:",
            "readonly_confirmation_status:",
            "broker_position_read_status:",
            "position_symbol_count_if_readonly:",
            "ticket_instance_created: False",
            "executable_ticket_created: False",
            "order_values_populated: False",
            "order_instructions_created: False",
            "orders_submitted: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary fresh broker pre-ticket gate run section missing phrase: {phrase}")
    elif "vol_fresh_broker_pre_ticket_gate_run_present: False" in output:
        for phrase in [
            "vol_fresh_broker_pre_ticket_gate_run_missing_saved_output: data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv",
            "vol_fresh_broker_pre_ticket_gate_run_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved fresh broker pre-ticket gate run section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether fresh broker pre-ticket gate run is present")
    if "paper_live_go_no_go_dashboard_present: True" in output:
        for phrase in [
            "final_go_no_go_status: paper_live_go_no_go_dashboard_execution_blocked_monitor_only",
            "final_go_no_go_decision: NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY",
            "qqq100_no_action_state: hold_no_action_aligned_long",
            "vol_largest_blocker: execution_not_approved",
            "vol_post_gate_review_status:",
            "vol_post_gate_review_decision:",
            "vol_post_gate_largest_blocker:",
            "vol_post_gate_saved_qqq_quantity:",
            "vol_ticket_value_design_status:",
            "vol_ticket_value_design_decision:",
            "vol_ticket_value_largest_blocker:",
            "vol_ticket_criteria_source_closeout_approval_wording_decision:",
            "vol_ticket_criteria_source_closeout_future_phrase:",
            "vol_ticket_criteria_source_closeout_record_decision:",
            "vol_ticket_criteria_source_closed_blocker:",
            "vol_ticket_criteria_source_remaining_blockers:",
            "vol_ticket_criteria_resolution_plan_closeout_approval_wording_decision:",
            "vol_ticket_criteria_resolution_plan_closeout_future_phrase:",
            "vol_ticket_criteria_resolution_plan_closeout_record_decision:",
            "vol_ticket_criteria_resolution_plan_closed_blocker:",
            "vol_ticket_criteria_resolution_plan_remaining_blockers:",
            "vol_ticket_approval_criteria_closeout_approval_wording_decision:",
            "vol_ticket_approval_criteria_closeout_future_phrase:",
            "vol_ticket_approval_criteria_closeout_record_decision:",
            "vol_ticket_approval_criteria_closed_blocker:",
            "vol_ticket_approval_criteria_remaining_blockers:",
            "vol_ticket_final_blockers_closeout_approval_wording_decision:",
            "vol_ticket_final_blockers_closeout_future_phrase:",
            "vol_ticket_final_blockers_closeout_record_decision:",
            "vol_ticket_final_blockers_closed_blocker:",
            "vol_ticket_final_blockers_remaining_blockers:",
            "vol_execution_approval_request_readiness_decision:",
            "vol_execution_approval_request_ready:",
            "vol_execution_approval_requested: False",
            "vol_execution_approval_recorded: False",
            "order_instructions_created: False",
            "execution_approved: False",
            "paper_execution_approved: False",
            "scheduling_approved: False",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary go/no-go dashboard section missing phrase: {phrase}")
    elif "paper_live_go_no_go_dashboard_present: False" in output:
        for phrase in [
            "paper_live_go_no_go_dashboard_missing_saved_output: data/paper_live_go_no_go_dashboard_summary.csv",
            "paper_live_go_no_go_status: missing_saved_output",
        ]:
            if phrase not in output:
                failures.append(f"Daily summary missing-saved go/no-go dashboard section missing phrase: {phrase}")
    else:
        failures.append("Daily summary must report whether paper-live go/no-go dashboard is present")
    if "ModuleNotFoundError: No module named 'alpaca'" in output:
        failures.append(f"{COMMAND} must not require top-level Alpaca import")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
