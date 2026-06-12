from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT_PATH = ROOT / "bot.py"


def main() -> int:
    failures: list[str] = []
    verify_early_route_precedes_alpaca_imports(failures)
    verify_execution_imports_still_present(failures)
    verify_report_only_commands_run_without_venv_site_packages(failures)

    if failures:
        print("Report-only import safety verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Report-only import safety verification passed.")
    print("Verified report-only commands can route before Alpaca imports while execution imports remain present.")
    return 0


def verify_early_route_precedes_alpaca_imports(failures: list[str]) -> None:
    source = read_text(BOT_PATH)
    early_index = source.find("_early_report_only_route()")
    alpaca_index = source.find("from alpaca.trading.client import TradingClient")
    if early_index == -1:
        failures.append("bot.py must call _early_report_only_route()")
    if alpaca_index == -1:
        failures.append("bot.py must retain TradingClient import for execution paths")
    if early_index != -1 and alpaca_index != -1 and early_index > alpaca_index:
        failures.append("_early_report_only_route() must run before top-level Alpaca imports")
    if 'sys.argv[1:] == ["--vps-monitoring-status"]' not in source:
        failures.append("early route must be limited to exact --vps-monitoring-status invocation")
    if 'sys.argv[1:] == ["--vps-daily-monitoring-summary"]' not in source:
        failures.append("early route must be limited to exact --vps-daily-monitoring-summary invocation")
    if 'sys.argv[1:] == ["--market-monitor-scheduling-readiness-report"]' not in source:
        failures.append("early route must be limited to exact --market-monitor-scheduling-readiness-report invocation")


def verify_execution_imports_still_present(failures: list[str]) -> None:
    source = read_text(BOT_PATH)
    required = [
        "from alpaca.trading.client import TradingClient",
        "from alpaca.trading.requests import MarketOrderRequest",
        "validate_alpaca_asset_for_order",
        "insert_trade_log",
        "send_discord_alert",
    ]
    for token in required:
        if token not in source:
            failures.append(f"Execution dependency/safety import must remain present: {token}")


def verify_report_only_commands_run_without_venv_site_packages(failures: list[str]) -> None:
    commands = [
        ("--vps-monitoring-status", "VPS MONITORING STATUS. REPORT ONLY. NOT EXECUTION."),
        ("--vps-daily-monitoring-summary", "VPS DAILY MONITORING SUMMARY. REPORT ONLY. NOT EXECUTION."),
        (
            "--market-monitor-scheduling-readiness-report",
            "Market monitor scheduling readiness checks:",
        ),
    ]
    for command, marker in commands:
        completed = subprocess.run(
            [sys.executable, "bot.py", command],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        if completed.returncode != 0:
            failures.append(f"{command} should run without Alpaca import; exit code {completed.returncode}")
        if "ModuleNotFoundError: No module named 'alpaca'" in output:
            failures.append(f"{command} must not require top-level Alpaca import")
        if marker not in output:
            failures.append(f"{command} output marker missing")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
