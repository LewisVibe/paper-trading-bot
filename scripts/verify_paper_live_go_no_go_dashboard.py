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
