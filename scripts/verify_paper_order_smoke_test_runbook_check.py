from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_order_smoke_test_runbook_check.py"
RUNBOOK = ROOT / "docs" / "PAPER_ORDER_SMOKE_TEST_RUNBOOK.md"
COMMAND = "--paper-order-smoke-test-runbook-check"
OUTPUT = "data/paper_order_smoke_test_runbook_check.csv"

REQUIRED_RUNBOOK_PHRASES = [
    "AAPL buy 1",
    "Before Market Open",
    "Near Or During US Regular Market Hours",
    "After A Separately Approved Tiny Manual Paper Order",
    "execution_approved=false",
    "scheduling_approved=false",
    "followup_order_approved=false",
    "No second order without manual review",
]

FORBIDDEN_PATTERNS = [
    "TradingClient",
    "yfinance",
    "load_config(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "MarketOrderRequest(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab -e",
    "systemctl enable",
]


def main() -> int:
    failures: list[str] = []
    verify_command_registered(failures)
    verify_sources(failures)
    verify_output_ignored(failures)
    verify_fixture_run(failures)
    if failures:
        print("Paper-order smoke-test runbook check verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Paper-order smoke-test runbook check verification passed.")
    print("Verified static runbook, report-only command, false approvals, ignored output, and no broker/order/scheduler paths.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    source = read_text(BOT)
    if COMMAND not in source:
        failures.append(f"{COMMAND} is missing from bot.py")
    early_index = source.find(f'sys.argv[1:] == ["{COMMAND}"]')
    alpaca_index = source.find("from alpaca.trading.client import TradingClient")
    if early_index == -1:
        failures.append("missing exact early route for runbook check")
    elif alpaca_index != -1 and early_index > alpaca_index:
        failures.append("runbook check should route before broker imports")


def verify_sources(failures: list[str]) -> None:
    module = read_text(MODULE)
    runbook = read_text(RUNBOOK)
    for phrase in REQUIRED_RUNBOOK_PHRASES:
        if phrase not in runbook:
            failures.append(f"runbook missing required phrase: {phrase}")
    for token in ["smoke_test_order_approved", "execution_approved", "scheduling_approved", "followup_order_approved"]:
        if token not in module:
            failures.append(f"runbook checker missing false flag: {token}")
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in module:
            failures.append(f"forbidden broker/order/scheduler pattern in runbook checker: {pattern}")


def verify_output_ignored(failures: list[str]) -> None:
    completed = subprocess.run(["git", "check-ignore", OUTPUT], cwd=ROOT, check=False, capture_output=True, text=True, timeout=10)
    if completed.returncode != 0:
        failures.append(f"generated output is not ignored by git: {OUTPUT}")


def verify_fixture_run(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir()
        (root / "docs" / "PAPER_ORDER_SMOKE_TEST_RUNBOOK.md").write_text(read_text(RUNBOOK), encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        code = (
            "from trading_bot.research.paper_order_smoke_test_runbook_check import generate_paper_order_smoke_test_runbook_check; "
            "r=generate_paper_order_smoke_test_runbook_check(r'.'); print('\\n'.join(r.summary_lines))"
        )
        completed = subprocess.run([sys.executable, "-c", code], cwd=root, env=env, check=False, capture_output=True, text=True, timeout=30)
        if completed.returncode != 0:
            failures.append(f"fixture run failed: {completed.stderr.strip()}")
            return
        if "python bot.py --paper-order-test" in completed.stdout:
            failures.append("terminal summary should not print a pasteable paper-order command")
        output = root / OUTPUT
        if not output.exists():
            failures.append("fixture run did not write expected output")
            return
        rows = list(csv.DictReader(output.open(newline="", encoding="utf-8")))
        for column in ["smoke_test_order_approved", "execution_approved", "scheduling_approved", "followup_order_approved"]:
            if not all(str(row.get(column, "")).lower() == "false" for row in rows):
                failures.append(f"{column} must be false for every row")
        final = next((row for row in rows if row.get("check_name") == "final_runbook_check_status"), {})
        if final.get("check_status") != "runbook_check_ready_for_manual_review":
            failures.append(f"fixture final status should be ready for manual review, got {final.get('check_status')}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
