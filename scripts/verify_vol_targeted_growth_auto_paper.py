from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARSER = ROOT / "trading_bot" / "cli" / "parser.py"
DISPATCH = ROOT / "trading_bot" / "cli" / "dispatch.py"
APPLICATION = ROOT / "trading_bot" / "cli" / "application.py"
RUNNER = ROOT / "trading_bot" / "runners" / "vol_targeted_growth_paper.py"
RUNBOOK = ROOT / "docs" / "HERMES_AUTO_PAPER_EXECUTION_CRON.md"
CONFIG_EXAMPLE = ROOT / "config.example.json"

COMMAND = "--run-vol-targeted-growth-auto-paper"
SCHEDULE = "5 14,15 * * 1-5"
TIMEZONE = "Europe/London"


def main() -> int:
    failures: list[str] = []
    parser = read(PARSER)
    dispatch = read(DISPATCH)
    application = read(APPLICATION)
    runner = read(RUNNER)
    runbook = read(RUNBOOK)
    config = json.loads(read(CONFIG_EXAMPLE) or "{}")

    if COMMAND not in parser:
        failures.append("autonomous paper command is missing from parser")
    if 'CommandDescriptor("run_vol_targeted_growth_auto_paper", SideEffect.PAPER_EXECUTION)' not in dispatch:
        failures.append("autonomous paper command is not classified as paper execution")
    if "run_vol_targeted_growth_auto_paper" not in application:
        failures.append("autonomous paper command is not wired in the configured application")
    if config.get("auto_paper_trading_enabled") is not False:
        failures.append("checked-in autonomous paper config must default false")

    for token in [
        "MANAGED_SYMBOLS",
        "auto_paper_trading_enabled",
        "paper_kill_switch_enabled",
        "AUTO_WINDOW_START_MINUTE",
        "AUTO_WINDOW_END_MINUTE",
        "acquire_auto_lease",
        'open("x"',
        "recent_client_order_ids",
        "vtga-",
        "partial_or_failed_manual_review_required",
        "send_discord_alert",
        "live_trading_approved",
    ]:
        if token not in runner:
            failures.append(f"autonomous runner is missing safety token: {token}")
    if ".submit_order(" in runner:
        failures.append("autonomous runner must submit only through the audited paper gateway")
    strategy = read(ROOT / "trading_bot" / "strategies" / "vol_targeted_growth.py")
    if 'PAPER_CAPITAL_USD = Decimal("100000.00")' not in strategy:
        failures.append("autonomous strategy must retain the exact $100,000 paper cap")

    for token in [COMMAND, SCHEDULE, TIMEZONE, "paper-bot-auto-paper-rebalance", "script-only / no-agent"]:
        if token not in runbook:
            failures.append(f"autonomous Hermes runbook is missing: {token}")
    scheduled_command_lines = [
        line.strip()
        for line in runbook.splitlines()
        if line.strip().startswith(".venv\\Scripts\\python.exe bot.py --")
    ]
    if scheduled_command_lines != [f".venv\\Scripts\\python.exe bot.py {COMMAND}"]:
        failures.append("autonomous runbook must contain exactly one scheduled bot command")
    for forbidden in [
        "--execute-vol-targeted-growth-paper TICKET_ID",
        "--paper-order-test ...",
        "--execute-slow-sma-paper --confirm-slow-sma-paper",
    ]:
        if forbidden in scheduled_command_lines:
            failures.append(f"autonomous runbook schedules forbidden command: {forbidden}")

    if failures:
        print("Autonomous volatility-targeted paper verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Autonomous volatility-targeted paper verification passed.")
    print("Verified default-off config, paper-only routing, session lease/idempotency, Discord reporting, and DST-safe 10:05 ET Hermes scope.")
    return 0


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
