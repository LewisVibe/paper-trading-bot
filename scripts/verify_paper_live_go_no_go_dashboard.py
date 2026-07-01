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

    output = "\n".join(result.summary_lines + lines)
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
