from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_manual_execution_design_approval_gate import (  # noqa: E402
    FINAL_DECISION,
    FINAL_STATUS,
    OUTPUT_FILES,
    generate_vol_targeted_growth_manual_execution_design_approval_gate,
    show_vol_targeted_growth_manual_execution_design_approval_gate,
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
    "manual_execution_design_approved",
    "manual_execution_design_approval_recorded",
    "paper_live_candidate_approved",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
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
        print("Volatility-targeted manual execution-design approval gate verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted manual execution-design approval gate verification passed.")
    print("Verified saved-output approval gate, false approvals, ignored outputs, and no broker/order/scheduling calls.")
    return 0


def verify_commands_registered(failures: list[str]) -> None:
    bot_source = read_text(ROOT / "bot.py")
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    for command in [
        "--vol-targeted-growth-manual-execution-design-approval-gate",
        "--show-vol-targeted-growth-manual-execution-design-approval-gate",
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
    source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_manual_execution_design_approval_gate.py")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"approval gate source contains forbidden token: {token}")
    for phrase in [
        "saved_output_only",
        "MANUAL_EXECUTION_DESIGN_APPROVAL_NOT_RECORDED",
        "manual_execution_design_approved",
        "manual_execution_design_approval_recorded",
        "executable_ticket_design_allowed",
        "order_instructions_created",
        "execution_approved",
        "scheduling_approved",
    ]:
        if phrase not in source:
            failures.append(f"approval gate source missing safety phrase: {phrase}")


def verify_vps_daily_summary_integration(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py")
    for phrase in [
        "VOL_MANUAL_EXECUTION_DESIGN_APPROVAL_GATE_SUMMARY_PATH",
        "Volatility manual execution-design approval gate:",
        "vol_manual_execution_design_approval_gate_status_lines",
        "MANUAL_EXECUTION_DESIGN_APPROVAL_NOT_RECORDED",
        "vol_manual_execution_design_approval_gate_warning: monitor only;",
    ]:
        if phrase not in source:
            failures.append(f"VPS daily summary missing manual execution-design approval gate phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_manual_execution_design_approval_gate(root)
        code, lines = show_vol_targeted_growth_manual_execution_design_approval_gate(root)
        if code != 0:
            failures.append("show command failed after fixture generation")
        output = "\n".join(lines + result.summary_lines)
        for phrase in [
            FINAL_STATUS,
            FINAL_DECISION,
            "explicit_future_prompt_required",
            "manual_execution_design_approved=false",
            "executable_ticket_design_allowed=false",
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
    if summary_value(rows, "final_approval_gate_status") != FINAL_STATUS:
        failures.append("summary final status is incorrect")
    if summary_value(rows, "final_approval_gate_decision") != FINAL_DECISION:
        failures.append("summary final decision is incorrect")
    if summary_value(rows, "largest_blocker") != "explicit_future_prompt_required":
        failures.append("summary largest blocker should remain explicit future prompt")
    if summary_value(rows, "explicit_future_prompt_required") != "True":
        failures.append("summary must require a future explicit prompt")
    for flag in FALSE_FLAGS:
        if summary_or_flag_value(rows, flag) != "False":
            failures.append(f"summary flag must be False: {flag}")


def verify_report_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    gate_items = {str(row.get("gate_item", "")) for row in rows}
    required = {
        "explicit_future_prompt_required",
        "scope_must_name_active_seed",
        "approval_must_be_design_only",
        "gap_list_must_be_reviewed",
        "go_no_go_must_change_from_no_go",
        "blocker_rollup_must_be_reviewed",
        "fresh_readonly_broker_state_still_required",
        "order_capable_scheduling_remains_forbidden",
    }
    missing = required - gate_items
    if missing:
        failures.append(f"report rows missing required gate items: {sorted(missing)}")
    for row in rows:
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).strip() != "False":
                failures.append(f"report flag must be False for {row.get('gate_item')}: {flag}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_executable_ticket_gap_list_summary.csv",
        {
            "final_gap_list_status": "vol_targeted_growth_executable_ticket_gap_list_execution_blocked_manual_review_required",
            "final_ticket_design_decision": "EXECUTABLE_TICKET_DESIGN_NOT_READY",
            "largest_gap": "manual_execution_design_approval_missing",
        },
    )
    write_summary(
        data / "paper_live_go_no_go_dashboard_summary.csv",
        {
            "final_go_no_go_status": "paper_live_go_no_go_dashboard_execution_blocked_monitor_only",
            "final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY",
        },
    )
    write_summary(
        data / "vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv",
        {
            "final_execution_blocker_rollup_status": "vol_targeted_growth_paper_live_execution_blocker_rollup_created_manual_review_required",
            "largest_blocker": "executable_ticket_prerequisites_not_met",
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
