from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "qqq100_postcheck_readiness_report.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = ["--qqq100-postcheck-readiness-report", "--show-qqq100-postcheck-readiness-report"]
OUTPUTS = [
    "data/qqq100_postcheck_readiness_report.csv",
    "data/qqq100_postcheck_readiness_summary.csv",
    "data/qqq100_postcheck_readiness_blockers.csv",
    "data/qqq100_postcheck_readiness_runbook.csv",
]

REQUIRED_MODULE_TOKENS = [
    "qqq100_postcheck_manual_approval_required",
    "data\\qqq100_paper_postcheck.csv",
    "position_quantity_abs_or_current_position_quantity_abs",
    "python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check",
    "manual_approval_required_before_running_postcheck",
    "postcheck_creates_orders",
    "followup_order_not_approved",
    "qqq_100_trend_gate",
    "QQQ",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
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
        print("QQQ100 postcheck readiness report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 postcheck readiness report verification passed.")
    print("Verified static runbook, exact missing postcheck evidence, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--qqq100-postcheck-readiness-report": 'if sys.argv[1:] == ["--qqq100-postcheck-readiness-report"]:',
        "--show-qqq100-postcheck-readiness-report": 'if sys.argv[1:] == ["--show-qqq100-postcheck-readiness-report"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("QQQ100 postcheck readiness module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    display_start = module_source.find("def show_qqq100_postcheck_readiness_report")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_qqq100_postcheck_readiness_report" in module_source[display_start:]:
        failures.append("display command must not regenerate the report")
    for phrase in [
        "postcheck was not run",
        "must not be run without explicit user approval",
        "does not approve follow-up orders",
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
        "QQQ100 postcheck readiness",
        "confirm-readonly-alpaca-check",
        "does not approve execution",
        "followup_order_approved",
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
