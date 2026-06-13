from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_order_smoke_test_live_preflight.py"
COMMAND = "--paper-order-smoke-test-live-preflight"
OUTPUT = "data/paper_order_smoke_test_live_preflight.csv"

REQUIRED_TOKENS = [
    OUTPUT,
    "live_preflight_ready_for_manual_confirmation",
    "live_preflight_wait_for_market_open",
    "live_preflight_manual_review_required",
    "live_preflight_blocked",
    "confirm_readonly_alpaca_check",
    "get_clock()",
    "get_asset(",
    "get_orders(",
    "order_execution_approved",
    "execution_approved",
    "scheduling_approved",
    "run_command_now",
    "Warning: this summary intentionally does not print a paper-order command.",
]

FORBIDDEN_MODULE_PATTERNS = [
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

PASTEABLE_COMMAND_PATTERNS = [
    "python bot.py --paper-order-test",
    ".venv\\Scripts\\python.exe bot.py --paper-order-test",
]


def main() -> int:
    failures: list[str] = []
    verify_command_registered(failures)
    verify_module_source(failures)
    verify_generated_output_ignored(failures)
    verify_default_mode_no_alpaca(failures)

    if failures:
        print("Paper-order smoke-test live preflight verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-order smoke-test live preflight verification passed.")
    print("Verified command, ignored output, default no-Alpaca mode, explicit read-only gate, false approval flags, and no pasteable order command.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    source = read_text(BOT)
    for token in [COMMAND, "--ticker", "--side", "--quantity", "--confirm-readonly-alpaca-check"]:
        if token not in source:
            failures.append(f"{token} is missing from bot.py")
    early_route_index = source.find(f'"{COMMAND}" in sys.argv[1:]')
    alpaca_import_index = source.find("from alpaca.trading.client import TradingClient")
    if early_route_index == -1:
        failures.append("missing early route for paper-order smoke-test live preflight")
    elif alpaca_import_index != -1 and early_route_index > alpaca_import_index:
        failures.append("live preflight early route should be before broker imports")
    branch_index = source.find("if args.paper_order_smoke_test_live_preflight:")
    load_config_index = source.find("config = load_config(")
    if branch_index == -1:
        failures.append("missing argparse branch for live preflight")
    elif load_config_index != -1 and branch_index > load_config_index:
        failures.append("live preflight must route before normal config loading")


def verify_module_source(failures: list[str]) -> None:
    source = read_text(MODULE)
    for token in REQUIRED_TOKENS:
        if token not in source:
            failures.append(f"missing live-preflight token: {token}")
    for pattern in FORBIDDEN_MODULE_PATTERNS:
        if pattern in source:
            failures.append(f"forbidden execution/alert/market/scheduler pattern: {pattern}")
    for pattern in PASTEABLE_COMMAND_PATTERNS:
        if pattern in source:
            failures.append(f"module must not include pasteable paper-order command: {pattern}")
    if "load_config(" not in source:
        failures.append("confirmed read-only mode should use the existing config loader")
    if "TradingClient" not in source:
        failures.append("confirmed read-only mode should create a paper TradingClient")
    if "paper=True" not in source:
        failures.append("TradingClient must be created with paper=True")


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


def verify_default_mode_no_alpaca(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture(root)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        code = (
            "from trading_bot.research.paper_order_smoke_test_live_preflight import "
            "generate_paper_order_smoke_test_live_preflight; "
            "r=generate_paper_order_smoke_test_live_preflight('AAPL', 'buy', '1', False, r'.'); "
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
            failures.append(f"default fixture run should not fail: {completed.stderr.strip()}")
            return
        for pattern in PASTEABLE_COMMAND_PATTERNS:
            if pattern in completed.stdout:
                failures.append(f"terminal summary printed pasteable order command: {pattern}")
        output = root / OUTPUT
        if not output.exists():
            failures.append("default fixture run did not write expected live preflight CSV")
            return
        with output.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            failures.append("live preflight wrote no rows")
            return
        for column in ["order_execution_approved", "execution_approved", "scheduling_approved", "run_command_now"]:
            if not all(str(row.get(column, "")).lower() == "false" for row in rows):
                failures.append(f"{column} must remain false for every row")
        if any(str(row.get("alpaca_called", "")).lower() == "true" for row in rows):
            failures.append("default mode must not call Alpaca")
        if "alpaca_called: false" not in completed.stdout:
            failures.append("terminal summary should show alpaca_called false")
        final = next((row for row in rows if row.get("check_name") == "final_live_preflight_status"), {})
        if final.get("check_status") != "live_preflight_manual_review_required":
            failures.append(f"default final status should need manual review, got {final.get('check_status')}")
        if final.get("ticker") != "AAPL" or final.get("side") != "buy" or final.get("quantity") != "1":
            failures.append("final row should preserve proposed ticker/side/quantity")


def write_fixture(root: Path) -> None:
    (root / "data").mkdir(parents=True)
    write_csv(
        root / "data" / "alpaca_paper_readiness_report.csv",
        ["check_name", "check_status"],
        [{"check_name": "final_readiness_status", "check_status": "alpaca_paper_readonly_check_passed_manual_smoke_test_next"}],
    )
    write_csv(
        root / "data" / "paper_order_smoke_test_readiness_pack.csv",
        ["check_name", "check_status"],
        [{"check_name": "final_smoke_test_discussion_status", "check_status": "smoke_test_discussion_needs_manual_review"}],
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
