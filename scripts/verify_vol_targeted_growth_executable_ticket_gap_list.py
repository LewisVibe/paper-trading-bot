from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_executable_ticket_gap_list import (  # noqa: E402
    FINAL_DECISION,
    FINAL_STATUS,
    OUTPUT_FILES,
    generate_vol_targeted_growth_executable_ticket_gap_list,
    show_vol_targeted_growth_executable_ticket_gap_list,
)


FALSE_FLAGS = [
    "alpaca_called",
    "broker_positions_read",
    "paper_positions_read",
    "market_data_refreshed",
    "yfinance_called",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "order_side_created",
    "order_quantity_created",
    "order_type_created",
    "time_in_force_created",
    "executable_ticket_created",
    "executable_ticket_design_allowed",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "paper_live_candidate_approved",
    "manual_execution_design_approved",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
]

FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient",
    "submit_order",
    "cancel_order",
    "replace_order",
    "get_all_positions",
    "get_open_position",
    "get_account",
    "sqlite3",
    "Discord",
    "Telegram",
    "schedule_task",
    "TaskScheduler",
    "cron",
]


def main() -> int:
    failures: list[str] = []
    verify_commands_registered(failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(failures)
    verify_vps_daily_summary_integration(failures)
    verify_fixture_output(failures)

    if failures:
        print("Volatility-targeted executable ticket gap list verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted executable ticket gap list verification passed.")
    print("Verified saved-output gap list, false approvals, ignored outputs, and no broker/order/scheduling calls.")
    return 0


def verify_commands_registered(failures: list[str]) -> None:
    bot_source = read_text(ROOT / "bot.py")
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    for command in [
        "--vol-targeted-growth-executable-ticket-gap-list",
        "--show-vol-targeted-growth-executable-ticket-gap-list",
    ]:
        if command not in bot_source:
            failures.append(f"bot.py missing command: {command}")
        if command not in inventory_source:
            failures.append(f"command inventory missing command: {command}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for path in OUTPUT_FILES.values():
        result = subprocess.run(
            ["git", "check-ignore", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_boundaries(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_executable_ticket_gap_list.py")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"gap list source contains forbidden token: {token}")
    for phrase in [
        "saved_output_only",
        "alpaca_called",
        "broker_positions_read",
        "orders_created",
        "order_instructions_created",
        "executable_ticket_design_allowed",
        "execution_approved",
        "scheduling_approved",
    ]:
        if phrase not in source:
            failures.append(f"gap list source missing safety phrase: {phrase}")


def verify_vps_daily_summary_integration(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py")
    for phrase in [
        "VOL_EXECUTABLE_TICKET_GAP_LIST_SUMMARY_PATH",
        "Volatility executable ticket gap list:",
        "vol_executable_ticket_gap_list_status_lines",
        "EXECUTABLE_TICKET_DESIGN_NOT_READY",
        "vol_executable_ticket_gap_list_warning: monitor only;",
    ]:
        if phrase not in source:
            failures.append(f"VPS daily summary missing executable ticket gap-list phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_executable_ticket_gap_list(root)
        code, lines = show_vol_targeted_growth_executable_ticket_gap_list(root)
        if code != 0:
            failures.append("show command failed after fixture generation")
        output = "\n".join(lines + result.summary_lines)
        for phrase in [
            FINAL_STATUS,
            FINAL_DECISION,
            "manual_execution_design_approval_missing",
            "EXECUTABLE_TICKET_DESIGN_NOT_READY",
            "closed_blocker_count=3",
            "criteria_source_reviewed_closed=True",
            "criteria_resolution_plan_open_closed=True",
            "approval_criteria_not_approval_closed=True",
            "remaining_known_blockers_after_closeout=ticket_values_not_approved",
            "order_instructions_created=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        verify_summary_rows(result.summary_rows, failures)
        verify_report_rows(result.report_rows, failures)
        for name, path in result.output_paths.items():
            if not path.exists():
                failures.append(f"fixture did not write {name}: {path}")


def verify_summary_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    if summary_value(rows, "final_gap_list_status") != FINAL_STATUS:
        failures.append("summary final status is incorrect")
    if summary_value(rows, "final_ticket_design_decision") != FINAL_DECISION:
        failures.append("summary final decision is incorrect")
    if summary_value(rows, "largest_gap") != "manual_execution_design_approval_missing":
        failures.append("summary largest gap should remain manual execution-design approval")
    if summary_value(rows, "criteria_source_reviewed_closed") != "True":
        failures.append("summary should recognise criteria_source_reviewed as closed from saved evidence")
    if summary_value(rows, "criteria_resolution_plan_open_closed") != "True":
        failures.append("summary should recognise criteria_resolution_plan_open as closed from saved evidence")
    if summary_value(rows, "approval_criteria_not_approval_closed") != "True":
        failures.append("summary should recognise approval_criteria_not_approval as closed from saved evidence")
    if summary_value(rows, "closed_blocker_count") != "3":
        failures.append("summary should count three closed blockers from saved evidence")
    remaining = summary_value(rows, "remaining_known_blockers_after_closeout")
    if "ticket_values_not_approved" not in remaining or "approval_criteria_not_approval" in remaining:
        failures.append("summary should preserve exact remaining blockers after third closeout")
    for flag in FALSE_FLAGS:
        if summary_or_flag_value(rows, flag) != "False":
            failures.append(f"summary flag must be False: {flag}")


def verify_report_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    gap_names = {str(row.get("gap_name", "")) for row in rows}
    required = {
        "manual_execution_design_approval_missing",
        "executable_ticket_prerequisites_not_met",
        "execution_blocker_rollup_not_cleared",
        "go_no_go_dashboard_is_no_go",
        "fresh_readonly_broker_state_required",
        "allocation_cap_not_approved",
        "sleeve_mapping_not_approved",
        "target_position_plan_non_executable",
        "order_ticket_boundary_blocks_order_fields",
        "scheduling_not_approved",
    }
    missing = required - gap_names
    if missing:
        failures.append(f"report rows missing required gaps: {sorted(missing)}")
    for row in rows:
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).strip() != "False":
                failures.append(f"report flag must be False for {row.get('gap_name')}: {flag}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_executable_ticket_prerequisites_review_summary.csv",
        {
            "final_executable_ticket_prerequisites_status": "vol_targeted_growth_executable_ticket_prerequisites_review_created_manual_review_required",
            "executable_ticket_prerequisites_met": "False",
            "executable_ticket_design_allowed": "False",
            "largest_blocker": "executable_ticket_prerequisites_not_met",
        },
    )
    write_summary(
        data / "vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv",
        {
            "final_execution_blocker_rollup_status": "vol_targeted_growth_paper_live_execution_blocker_rollup_created_manual_review_required",
            "largest_blocker": "executable_ticket_prerequisites_not_met",
            "execution_approved": "False",
        },
    )
    write_summary(
        data / "paper_live_go_no_go_dashboard_summary.csv",
        {
            "final_go_no_go_status": "paper_live_go_no_go_dashboard_execution_blocked_monitor_only",
            "final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY",
        },
    )
    write_summary(data / "vol_targeted_growth_paper_live_candidate_approval_summary.csv", {"final_candidate_approval_status": "discussion_only"})
    write_summary(data / "vol_targeted_growth_allocation_cap_sleeve_mapping_policy_summary.csv", {"allocation_cap_approved": "False"})
    write_summary(data / "vol_targeted_growth_non_executable_target_position_plan_summary.csv", {"final_target_position_plan_status": "non_executable_plan"})
    write_summary(data / "vol_targeted_growth_order_ticket_boundary_design_summary.csv", {"final_order_ticket_boundary_status": "boundary_blocks_order_fields"})
    write_summary(data / "vol_targeted_growth_broker_position_comparison_summary.csv", {"final_comparison_status": "saved_readonly_manual_review_required"})
    write_summary(
        data / "vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv",
        {
            "final_closeout_record_decision": "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY",
            "closed_blocker": "criteria_source_reviewed",
            "remaining_known_blockers": "criteria_resolution_plan_open;approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met",
        },
    )
    write_summary(
        data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_record_summary.csv",
        {
            "final_closeout_record_decision": "CRITERIA_RESOLUTION_PLAN_OPEN_BLOCKER_CLOSED_ONLY",
            "closed_blocker": "criteria_resolution_plan_open",
            "remaining_known_blockers": "approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met",
        },
    )
    write_summary(
        data / "vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_summary.csv",
        {
            "final_closeout_record_decision": "APPROVAL_CRITERIA_NOT_APPROVAL_BLOCKER_CLOSED_ONLY",
            "closed_blocker": "approval_criteria_not_approval",
            "remaining_known_blockers": "ticket_values_not_approved;executable_ticket_prerequisites_not_met",
        },
    )


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def summary_value(rows: list[dict[str, object]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def summary_or_flag_value(rows: list[dict[str, object]], key: str) -> str:
    value = summary_value(rows, key)
    if value:
        return value
    for row in rows:
        if key in row:
            return str(row.get(key, "")).strip()
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
