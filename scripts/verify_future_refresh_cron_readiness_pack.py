from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "future_refresh_cron_readiness.py"
COMMAND = "--future-refresh-cron-readiness-pack"
OUTPUT = "data/future_refresh_cron_readiness_pack.csv"

REQUIRED_TOKENS = [
    OUTPUT,
    "future_refresh_cron_review_needs_manual_review",
    ".venv\\\\Scripts\\\\python.exe bot.py --refresh-defensive-research",
    ".venv\\\\Scripts\\\\python.exe bot.py --alpaca-paper-readiness-report",
    ".venv\\\\Scripts\\\\python.exe bot.py --paper-order-smoke-test-readiness-pack",
    "cron_created",
    "cron_enabled",
    "scheduling_approved",
    "execution_approved",
    "order_execution_approved",
]

FORBIDDEN_MODULE_PATTERNS = [
    "TradingClient",
    "yfinance",
    "yf.download",
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

FORBIDDEN_CANDIDATE_TOKENS = [
    "--confirm-readonly-alpaca-check",
    "--paper-order-test",
    "--execute-slow-sma-paper",
    "--confirm-paper-order",
    "--confirm-slow-sma-paper",
    "git pull",
    "git commit",
    "git push",
]


def main() -> int:
    failures: list[str] = []
    verify_command_registered(failures)
    verify_module_source(failures)
    verify_output_ignored(failures)
    verify_fixture_run(failures)
    if failures:
        print("Future refresh cron readiness pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Future refresh cron readiness pack verification passed.")
    print("Verified static report-only command, candidate exclusions, false approvals, ignored output, and no cron/order/broker paths.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    source = read_text(BOT)
    if COMMAND not in source:
        failures.append(f"{COMMAND} is missing from bot.py")
    early_index = source.find(f'sys.argv[1:] == ["{COMMAND}"]')
    alpaca_index = source.find("from alpaca.trading.client import TradingClient")
    if early_index == -1:
        failures.append("missing exact early route for future refresh cron readiness pack")
    elif alpaca_index != -1 and early_index > alpaca_index:
        failures.append("future refresh cron readiness pack should route before broker imports")
    branch_index = source.find("if args.future_refresh_cron_readiness_pack:")
    load_config_index = source.find("config = load_config(")
    if branch_index == -1:
        failures.append("missing argparse branch for future refresh cron readiness pack")
    elif load_config_index != -1 and branch_index > load_config_index:
        failures.append("future refresh cron readiness pack must route before normal config loading")


def verify_module_source(failures: list[str]) -> None:
    source = read_text(MODULE)
    for token in REQUIRED_TOKENS:
        if token not in source:
            failures.append(f"missing readiness token: {token}")
    for pattern in FORBIDDEN_MODULE_PATTERNS:
        if pattern in source:
            failures.append(f"forbidden broker/market/order/scheduler pattern: {pattern}")
    candidate_block = source.split("CANDIDATE_SEQUENCE = [", 1)[-1].split("]\n\nFORBIDDEN_CANDIDATE_TOKENS", 1)[0]
    for token in FORBIDDEN_CANDIDATE_TOKENS:
        if token in candidate_block:
            failures.append(f"forbidden token in candidate future cron sequence: {token}")


def verify_output_ignored(failures: list[str]) -> None:
    completed = subprocess.run(["git", "check-ignore", OUTPUT], cwd=ROOT, check=False, capture_output=True, text=True, timeout=10)
    if completed.returncode != 0:
        failures.append(f"generated output is not ignored by git: {OUTPUT}")


def verify_fixture_run(failures: list[str]) -> None:
    code = (
        "from trading_bot.research.future_refresh_cron_readiness import generate_future_refresh_cron_readiness_pack; "
        "r=generate_future_refresh_cron_readiness_pack(r'.'); print('\\n'.join(r.summary_lines))"
    )
    completed = subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=False, capture_output=True, text=True, timeout=30)
    if completed.returncode != 0:
        failures.append(f"report run failed: {completed.stderr.strip()}")
        return
    output = ROOT / OUTPUT
    if not output.exists():
        failures.append("report run did not write expected output")
        return
    rows = list(csv.DictReader(output.open(newline="", encoding="utf-8")))
    for column in ["cron_created", "cron_enabled", "scheduling_approved", "execution_approved", "order_execution_approved"]:
        if not all(str(row.get(column, "")).lower() == "false" for row in rows):
            failures.append(f"{column} must be false for every row")
    final = next((row for row in rows if row.get("check_name") == "final_future_refresh_cron_review_status"), {})
    if final.get("check_status") not in {"future_refresh_cron_review_needs_manual_review", "future_refresh_cron_design_ready_for_manual_review"}:
        failures.append(f"final status should be manual-review/design-ready, got {final.get('check_status')}")
    for token in FORBIDDEN_CANDIDATE_TOKENS:
        if token in completed.stdout:
            failures.append(f"terminal summary should not include forbidden/high-risk token: {token}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
