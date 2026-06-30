from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "vol_targeted_growth_executable_ticket_approval_criteria.py"
DASHBOARD_MODULE = ROOT / "trading_bot" / "research" / "paper_live_go_no_go_dashboard.py"

COMMANDS = [
    "--vol-targeted-growth-executable-ticket-approval-criteria",
    "--show-vol-targeted-growth-executable-ticket-approval-criteria",
]

OUTPUTS = [
    "data/vol_targeted_growth_executable_ticket_approval_criteria.csv",
    "data/vol_targeted_growth_executable_ticket_approval_criteria_summary.csv",
    "data/vol_targeted_growth_executable_ticket_approval_criteria_blockers.csv",
    "data/vol_targeted_growth_executable_ticket_approval_criteria_evidence.csv",
]

REQUIRED_TOKENS = [
    "vol_targeted_growth_executable_ticket_approval_criteria_defined_manual_review_required",
    "APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED",
    "manual_review_approval_criteria_before_any_approval_readiness_change",
    '"approval_requested": False',
    '"approval_recorded": False',
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
    verify_dashboard_integration(failures)

    if failures:
        print("Volatility-targeted executable-ticket approval criteria verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted executable-ticket approval criteria verification passed.")
    print("Verified criteria-only output, false approvals, ignored outputs, and dashboard integration.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command in bot.py: {command}")
        if command not in inventory_source:
            failures.append(f"missing command in inventory verifier: {command}")
        branch = f'sys.argv[1:] == ["{command}"]'
        branch_index = bot_source.find(branch)
        if branch_index < 0:
            failures.append(f"missing early route for {command}")
        elif load_config_index >= 0 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("approval criteria module is missing")
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
    from trading_bot.research.vol_targeted_growth_executable_ticket_approval_criteria import (  # noqa: PLC0415
        generate_vol_targeted_growth_executable_ticket_approval_criteria,
        show_vol_targeted_growth_executable_ticket_approval_criteria,
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_summary(
            data / "vol_targeted_growth_executable_ticket_prerequisites_closeout_summary.csv",
            {"final_prerequisites_closeout_decision": "EXECUTABLE_TICKET_PREREQUISITES_NOT_CLOSED"},
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_approval_readiness_summary.csv",
            {"final_approval_readiness_decision": "NOT_READY_TO_REQUEST_EXECUTABLE_TICKET_APPROVAL"},
        )
        write_summary(
            data / "vol_targeted_growth_manual_ticket_value_design_summary.csv",
            {
                "final_ticket_value_design_decision": "TICKET_VALUE_DESIGN_REVIEW_ONLY_VALUES_NOT_APPROVED",
                "populated_ticket_value_count": "0",
            },
        )
        write_summary(
            data / "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv",
            {
                "final_pre_ticket_gate_run_status": "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_completed_readonly_manual_review_required",
                "broker_position_read_status": "paper_positions_read_readonly",
            },
        )
        write_summary(data / "paper_live_go_no_go_dashboard_summary.csv", {"final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"})

        result = generate_vol_targeted_growth_executable_ticket_approval_criteria(root)
        status_code, lines = show_vol_targeted_growth_executable_ticket_approval_criteria(root)

    output = "\n".join(result.summary_lines + lines)
    if status_code != 0:
        failures.append("approval criteria display should return 0 after generation")
    for phrase in [
        "vol_targeted_growth_executable_ticket_approval_criteria_defined_manual_review_required",
        "APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED",
        "approval_request_allowed_now=False",
        "approval_requested=false",
        "approval_recorded=false",
        "order_values_populated=false",
        "executable_ticket_created=false",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")


def verify_dashboard_integration(failures: list[str]) -> None:
    source = read_text(DASHBOARD_MODULE)
    for phrase in [
        "vol_ticket_approval_criteria",
        "vol_targeted_growth_executable_ticket_approval_criteria_summary.csv",
        "vol_ticket_approval_criteria_status",
        "vol_ticket_approval_criteria_decision",
        "executable_ticket_approval_criteria_review_required",
    ]:
        if phrase not in source:
            failures.append(f"go/no-go dashboard missing approval criteria integration phrase: {phrase}")


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
