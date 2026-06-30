from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "vol_targeted_growth_executable_ticket_criteria_source_review.py"
DASHBOARD_MODULE = ROOT / "trading_bot" / "research" / "paper_live_go_no_go_dashboard.py"

COMMANDS = [
    "--vol-targeted-growth-executable-ticket-criteria-source-review",
    "--show-vol-targeted-growth-executable-ticket-criteria-source-review",
]

OUTPUTS = [
    "data/vol_targeted_growth_executable_ticket_criteria_source_review.csv",
    "data/vol_targeted_growth_executable_ticket_criteria_source_review_summary.csv",
    "data/vol_targeted_growth_executable_ticket_criteria_source_review_blockers.csv",
    "data/vol_targeted_growth_executable_ticket_criteria_source_review_evidence.csv",
]

REQUIRED_TOKENS = [
    "vol_targeted_growth_executable_ticket_criteria_source_review_manual_review_required",
    "CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED",
    "manual_review_criteria_source_before_closing_any_blocker",
    '"criteria_changed": False',
    '"blockers_resolved": False',
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
        print("Volatility-targeted executable-ticket criteria source review verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted executable-ticket criteria source review verification passed.")
    print("Verified source-review-only output, no blocker closeout, false approvals, ignored outputs, and dashboard integration.")
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
        failures.append("criteria source review module is missing")
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
    from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_source_review import (  # noqa: PLC0415
        generate_vol_targeted_growth_executable_ticket_criteria_source_review,
        show_vol_targeted_growth_executable_ticket_criteria_source_review,
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_summary(
            data / "vol_targeted_growth_executable_ticket_approval_criteria_summary.csv",
            {
                "final_approval_criteria_status": "vol_targeted_growth_executable_ticket_approval_criteria_defined_manual_review_required",
                "final_approval_criteria_decision": "APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED",
            },
        )
        write_summary(
            data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_summary.csv",
            {
                "final_resolution_plan_status": "vol_targeted_growth_executable_ticket_criteria_resolution_plan_created_manual_review_required",
                "final_resolution_plan_decision": "CRITERIA_BLOCKER_RESOLUTION_PLAN_CREATED_APPROVAL_STILL_BLOCKED",
            },
        )
        write_summary(
            data / "paper_live_go_no_go_dashboard_summary.csv",
            {"final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"},
        )

        result = generate_vol_targeted_growth_executable_ticket_criteria_source_review(root)
        status_code, lines = show_vol_targeted_growth_executable_ticket_criteria_source_review(root)

    output = "\n".join(result.summary_lines + lines)
    if status_code != 0:
        failures.append("criteria source review display should return 0 after generation")
    for phrase in [
        "vol_targeted_growth_executable_ticket_criteria_source_review_manual_review_required",
        "CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED",
        "source_review_result=source_consistent_for_manual_review",
        "criteria_changed=false",
        "blockers_resolved=false",
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
        "vol_ticket_criteria_source_review",
        "vol_targeted_growth_executable_ticket_criteria_source_review_summary.csv",
        "vol_ticket_criteria_source_review_status",
        "vol_ticket_criteria_source_review_decision",
        "executable_ticket_criteria_source_review_does_not_close_blockers",
    ]:
        if phrase not in source:
            failures.append(f"go/no-go dashboard missing criteria source review integration phrase: {phrase}")


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
