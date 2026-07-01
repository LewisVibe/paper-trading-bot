from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "vol_targeted_growth_criteria_source_closeout_record.py"
DASHBOARD_MODULE = ROOT / "trading_bot" / "research" / "paper_live_go_no_go_dashboard.py"
VPS_DAILY_MODULE = ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py"
APPROVAL_PHRASE = "I approve closing the criteria_source_reviewed blocker only."

COMMANDS = [
    "--vol-targeted-growth-criteria-source-closeout-record",
    "--show-vol-targeted-growth-criteria-source-closeout-record",
]

OUTPUTS = [
    "data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record.csv",
    "data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv",
    "data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_blockers.csv",
    "data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_evidence.csv",
]

REQUIRED_TOKENS = [
    "vol_targeted_growth_criteria_source_closeout_recorded_manual_review_required",
    "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY",
    APPROVAL_PHRASE,
    "criteria_source_reviewed_closed",
    '"criteria_resolution_plan_closed": False',
    '"approval_criteria_not_approval_closed": False',
    '"other_blockers_closed": False',
    '"executable_ticket_approval_recorded": False',
    '"order_values_populated": False',
    '"order_instructions_created": False',
    '"executable_ticket_created": False',
    '"orders_submitted": False',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
]

FORBIDDEN_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    "LimitOrderRequest(",
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
    verify_dashboard_and_vps_integration(failures)

    if failures:
        print("Volatility-targeted criteria-source closeout record verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted criteria-source closeout record verification passed.")
    print("Verified one-blocker closeout, remaining blockers, false execution approvals, ignored outputs, and dashboard/VPS integration.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command in bot.py: {command}")
        if command not in inventory_source:
            failures.append(f"missing command in inventory verifier: {command}")
        branch_index = bot_source.find(command)
        if branch_index < 0:
            failures.append(f"missing early route for {command}")
        elif load_config_index >= 0 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("closeout record module is missing")
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
    from trading_bot.research.paper_live_go_no_go_dashboard import generate_paper_live_go_no_go_dashboard  # noqa: PLC0415
    from trading_bot.research.vol_targeted_growth_criteria_source_closeout_record import (  # noqa: PLC0415
        generate_vol_targeted_growth_criteria_source_closeout_record,
        show_vol_targeted_growth_criteria_source_closeout_record,
    )
    from trading_bot.research.vps_daily_monitoring_summary import build_vps_daily_monitoring_summary_lines  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_closeout_record_inputs(data)
        result = generate_vol_targeted_growth_criteria_source_closeout_record(root)
        status_code, lines = show_vol_targeted_growth_criteria_source_closeout_record(root)
        write_go_no_go_fixture_inputs(data)
        generate_paper_live_go_no_go_dashboard(root)
        daily_lines = build_vps_daily_monitoring_summary_lines(root)

    output = "\n".join(result.summary_lines + lines + daily_lines)
    if status_code != 0:
        failures.append("closeout record display should return 0 after generation")
    for phrase in [
        "vol_targeted_growth_criteria_source_closeout_recorded_manual_review_required",
        "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY",
        "closed_blocker=criteria_source_reviewed",
        "closed_blocker_count=1",
        "criteria_resolution_plan_open",
        "approval_criteria_not_approval",
        "ticket_values_not_approved",
        APPROVAL_PHRASE,
        "criteria_source_reviewed_closed=true",
        "other_blockers_closed=false",
        "executable_ticket_approval_recorded=false",
        "order_values_populated=false",
        "executable_ticket_created=false",
        "orders_submitted=false",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "vol_ticket_criteria_source_closeout_record_decision:",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")


def write_closeout_record_inputs(data: Path) -> None:
    write_summary(
        data / "vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording_summary.csv",
        {
            "final_approval_wording_decision": "CRITERIA_SOURCE_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
            "future_approval_phrase": APPROVAL_PHRASE,
        },
    )
    write_summary(
        data / "vol_targeted_growth_executable_ticket_criteria_source_closeout_candidate_review_summary.csv",
        {"final_candidate_review_decision": "CLOSEOUT_CANDIDATE_READY_FOR_MANUAL_REVIEW"},
    )
    write_summary(
        data / "vol_targeted_growth_executable_ticket_criteria_closeout_candidate_review_rollup_summary.csv",
        {"final_candidate_review_decision": "CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED"},
    )
    write_summary(data / "paper_live_go_no_go_dashboard_summary.csv", {"final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"})


def write_go_no_go_fixture_inputs(data: Path) -> None:
    write_summary(data / "paper_live_monitoring_status.csv", {"recommended_next_step": "hold_no_action_and_monitor_only"})
    write_summary(data / "qqq100_daily_decision_summary.csv", {"daily_decision_status": "qqq100_daily_decision_hold_no_action_aligned_long"})
    write_summary(
        data / "vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv",
        {
            "final_execution_blocker_rollup_status": "vol_targeted_growth_paper_live_execution_blocker_rollup_created_manual_review_required",
            "largest_blocker": "executable_ticket_prerequisites_not_met",
        },
    )
    write_summary(data / "vol_targeted_growth_post_gate_review_summary.csv", {"final_post_gate_review_status": "vol_targeted_growth_post_gate_review_manual_review_required"})
    write_summary(data / "vol_targeted_growth_manual_ticket_value_design_summary.csv", {"final_ticket_value_design_status": "vol_targeted_growth_manual_ticket_value_design_manual_review_required"})
    write_summary(data / "vol_targeted_growth_executable_ticket_prerequisites_closeout_summary.csv", {"final_prerequisites_closeout_decision": "EXECUTABLE_TICKET_PREREQUISITES_NOT_CLOSED"})
    write_summary(data / "vol_targeted_growth_executable_ticket_approval_readiness_summary.csv", {"final_approval_readiness_decision": "NOT_READY_TO_REQUEST_EXECUTABLE_TICKET_APPROVAL"})
    write_summary(data / "vol_targeted_growth_executable_ticket_approval_criteria_summary.csv", {"final_approval_criteria_decision": "APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED"})
    write_summary(data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_summary.csv", {"final_resolution_plan_decision": "CRITERIA_BLOCKER_RESOLUTION_PLAN_CREATED_APPROVAL_STILL_BLOCKED"})
    write_summary(data / "vol_targeted_growth_executable_ticket_criteria_source_review_summary.csv", {"final_source_review_decision": "CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED"})
    write_summary(data / "vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_summary.csv", {"final_blocker_closeout_review_decision": "CRITERIA_BLOCKERS_REVIEWED_NONE_CLOSED"})
    write_summary(data / "vol_targeted_growth_executable_ticket_criteria_blocker_specific_review_rollup_summary.csv", {"final_review_decision": "CRITERIA_BLOCKER_SPECIFIC_REVIEWS_CREATED_NONE_CLOSED"})
    write_summary(data / "vol_targeted_growth_executable_ticket_criteria_closeout_candidate_review_rollup_summary.csv", {"final_candidate_review_decision": "CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED"})
    write_summary(data / "vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording_summary.csv", {"final_approval_wording_decision": "CRITERIA_SOURCE_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED", "future_approval_phrase": APPROVAL_PHRASE})
    write_summary(data / "paper_live_checklist_status_summary.csv", {"checklist_phase_status": "paper_live_checklist_status_only"})


def verify_dashboard_and_vps_integration(failures: list[str]) -> None:
    dashboard_source = read_text(DASHBOARD_MODULE)
    vps_source = read_text(VPS_DAILY_MODULE)
    for phrase in [
        "vol_ticket_criteria_source_closeout_record",
        "vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv",
        "vol_ticket_criteria_source_closeout_record_decision",
        "vol_ticket_criteria_source_closed_blocker",
        "vol_ticket_criteria_source_remaining_blockers",
        "remaining_execution_ticket_blockers_after_criteria_source_closeout",
    ]:
        if phrase not in dashboard_source:
            failures.append(f"go/no-go dashboard missing closeout record integration phrase: {phrase}")
    for phrase in [
        "vol_ticket_criteria_source_closeout_record_decision",
        "vol_ticket_criteria_source_closed_blocker",
        "vol_ticket_criteria_source_remaining_blockers",
    ]:
        if phrase not in vps_source:
            failures.append(f"VPS daily summary missing closeout record integration phrase: {phrase}")


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
