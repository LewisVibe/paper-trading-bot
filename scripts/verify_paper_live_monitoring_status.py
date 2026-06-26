from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_live_monitoring_status.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = ["--paper-live-monitoring-status", "--show-paper-live-monitoring-status"]
OUTPUTS = [
    "data/paper_live_monitoring_status.csv",
    "data/paper_live_monitoring_components.csv",
    "data/paper_live_monitoring_blockers.csv",
]

REQUIRED_MODULE_TOKENS = [
    "active_strategy",
    "active_ticker",
    "previous_seed_strategy",
    "previous_seed_ticker",
    "saved_position_state",
    "saved_position_quantity",
    "alignment_state",
    "followup_policy_status",
    "no_action_required",
    "hold_no_action_and_monitor_only",
    "never_schedule_order_capable_commands",
    "missing_saved_evidence",
    "qqq_100_trend_gate",
    "QQQ",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
    "MULTI_SLEEVE",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"alpaca_called": False',
    '"live_positions_read": False',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
]

FORBIDDEN_CALL_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    "submit_alpaca_order(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_alpaca_positions(",
    "get_all_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "download_daily_price_data(",
    "yf.",
    "import yfinance",
    "sched.scheduler",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(
        read_text(path)
        for path in [README, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST]
    )

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(failures)

    if failures:
        print("Paper-live monitoring status verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live monitoring status verification passed.")
    print("Verified saved-output monitoring status, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-monitoring-status": 'if sys.argv[1:] == ["--paper-live-monitoring-status"]:',
        "--show-paper-live-monitoring-status": 'if sys.argv[1:] == ["--show-paper-live-monitoring-status"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live monitoring status module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    if "evaluate_paper_live_saved_evidence" not in module_source:
        failures.append("monitoring status should use saved paper-live evidence helper")
    display_start = module_source.find("def show_paper_live_monitoring_status")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_paper_live_monitoring_status" in module_source[display_start:]:
        failures.append("display command must not regenerate the report")
    for phrase in [
        "Monitoring/report only",
        "never_schedule_order_capable_commands=true",
        "Follow-up orders remain unapproved",
    ]:
        if phrase not in module_source:
            failures.append(f"missing boundary phrase: {phrase}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "paper-live monitoring status",
        "hold_no_action_and_monitor_only",
        "never_schedule_order_capable_commands",
        "does not approve execution",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


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


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
