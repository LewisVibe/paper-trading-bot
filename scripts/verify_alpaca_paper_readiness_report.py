from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "alpaca_paper_readiness.py"
COMMAND = "--alpaca-paper-readiness-report"
CONFIRM = "--confirm-readonly-alpaca-check"
OUTPUT = "data/alpaca_paper_readiness_report.csv"

REQUIRED_TOKENS = [
    OUTPUT,
    "alpaca_paper_static_ready_needs_readonly_check",
    "alpaca_paper_readonly_check_passed_manual_smoke_test_next",
    "alpaca_paper_readiness_blocked",
    "alpaca_paper_readiness_manual_review_required",
    "confirm_readonly_alpaca_check",
    "execution_approved",
    "scheduling_approved",
    "orders_possible",
    "alpaca_called",
    "TradingClient",
    "get_account()",
]

FORBIDDEN_CALL_PATTERNS = [
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "MarketOrderRequest(",
    "LimitOrderRequest(",
    "StopOrderRequest(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "download_close_prices(",
    "download_backtest_prices(",
    "yf.download(",
    "yfinance.download(",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab -e",
    "systemctl enable",
]


def main() -> int:
    failures: list[str] = []
    verify_command_registered(failures)
    verify_module_source(failures)
    verify_generated_output_ignored(failures)
    verify_default_mode_no_alpaca_and_false_approvals(failures)

    if failures:
        print("Alpaca paper readiness report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Alpaca paper readiness report verification passed.")
    print("Verified command, output path, explicit read-only confirmation gate, default no-Alpaca mode, false approvals, and no order/alert/scheduler call patterns.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    source = read_text(BOT)
    for token in [COMMAND, CONFIRM]:
        if token not in source:
            failures.append(f"{token} is missing from bot.py")
    early_route_index = source.find(f'["{COMMAND}"]')
    alpaca_import_index = source.find("from alpaca.trading.client import TradingClient")
    if early_route_index == -1:
        failures.append("missing exact early route for default Alpaca paper readiness command")
    elif alpaca_import_index != -1 and early_route_index > alpaca_import_index:
        failures.append("default Alpaca paper readiness route should be before broker imports")
    branch_index = source.find("if args.alpaca_paper_readiness_report:")
    load_config_index = source.find("config = load_config(")
    if branch_index == -1:
        failures.append("missing argparse branch for Alpaca paper readiness report")
    elif load_config_index != -1 and branch_index > load_config_index:
        failures.append("Alpaca paper readiness report must route before normal config loading")
    if "confirm_readonly_alpaca_check=args.confirm_readonly_alpaca_check" not in source:
        failures.append("read-only Alpaca mode should be gated by explicit confirm flag")


def verify_module_source(failures: list[str]) -> None:
    source = read_text(MODULE)
    for token in REQUIRED_TOKENS:
        if token not in source:
            failures.append(f"missing readiness token: {token}")
    for pattern in FORBIDDEN_CALL_PATTERNS:
        if pattern in source:
            failures.append(f"forbidden order/alert/market/scheduler call pattern: {pattern}")
    if "load_config(" not in source:
        failures.append("read-only mode should reuse existing config loader")
    if source.find("TradingClient") < source.find("confirm_readonly_alpaca_check"):
        failures.append("TradingClient should only appear after the explicit read-only mode path is defined")
    if "api_key_present=" not in source or "secret_key_present=" not in source:
        failures.append("credential checks should report boolean presence only")
    for risky in ["account_id", "account_number", "webhook_url", "secret_key="]:
        if risky in source:
            failures.append(f"source should not print or expose sensitive field token: {risky}")


def verify_generated_output_ignored(failures: list[str]) -> None:
    completed = subprocess.run(
        ["git", "check-ignore", OUTPUT],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        failures.append(f"generated output is not ignored by git: {OUTPUT}")


def verify_default_mode_no_alpaca_and_false_approvals(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "config.example.json").write_text(
            '{"dry_run": true, "allow_shorting": false, "alpaca": {"paper": true}}',
            encoding="utf-8",
        )
        (root / "trading_bot").mkdir()
        (root / "trading_bot" / "config.py").write_text(
            'raise ConfigError("alpaca.paper must be true. This bot refuses to use live trading mode.")',
            encoding="utf-8",
        )
        (root / "bot.py").write_text(
            "--confirm-paper-order confirm_paper_order --paper-order-test "
            "--confirm-slow-sma-paper confirm_slow_sma_paper --execute-slow-sma-paper",
            encoding="utf-8",
        )
        (root / "docs").mkdir()
        hermes_text = (
            "paper-bot-vps-status-check --vps-daily-monitoring-summary "
            "does not run refresh commands normal bot 345188fbb60c 10 10 * * * "
            "Telegram script-only / no-agent C:\\dev\\paper-trading-bot "
            "scheduling_approved false execution_approved false"
        )
        for name in ["HERMES_CRON_JOB_DESIGN.md", "HERMES_TASK_BOARD.md", "CURRENT_STATE.md"]:
            (root / "docs" / name).write_text(hermes_text, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        code = (
            "from trading_bot.research.alpaca_paper_readiness import generate_alpaca_paper_readiness_report; "
            "r=generate_alpaca_paper_readiness_report(r'.'); "
            "print('\\n'.join(r.summary_lines))"
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0:
            failures.append(f"default report should run without traceback: {completed.stderr.strip()}")
            return
        output = root / OUTPUT
        if not output.exists():
            failures.append("default report did not write expected CSV")
            return
        with output.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            failures.append("default report wrote no rows")
            return
        if not all(str(row.get("execution_approved", "")).lower() == "false" for row in rows):
            failures.append("execution_approved must remain false for every row")
        if not all(str(row.get("scheduling_approved", "")).lower() == "false" for row in rows):
            failures.append("scheduling_approved must remain false for every row")
        if not all(str(row.get("orders_possible", "")).lower() == "false" for row in rows):
            failures.append("orders_possible must remain false for every row")
        if any(str(row.get("alpaca_called", "")).lower() == "true" for row in rows):
            failures.append("default static mode must not call Alpaca")
        if "alpaca_called: false" not in completed.stdout:
            failures.append("terminal summary should explicitly show alpaca_called false in default mode")
        final = next((row for row in rows if row.get("check_name") == "final_readiness_status"), {})
        if final.get("check_status") != "alpaca_paper_static_ready_needs_readonly_check":
            failures.append(f"default final status should be static-ready/needs-readonly-check, got {final.get('check_status')}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
