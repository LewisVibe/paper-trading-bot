from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "stock_etf_paper_execution_readiness.py"
COMMAND = "--stock-etf-paper-execution-readiness-report"
OUTPUT = "data/stock_etf_paper_execution_readiness_report.csv"

REQUIRED_TOKENS = [
    OUTPUT,
    "codex_ambitious_concentrated_growth_persistence",
    "codex_ambitious_active_research_lead_cost_review_required",
    "paper_execution_discussion_blocked_by_cost_review_and_execution_gates",
    "paper_execution_discussion_needs_manual_review",
    "paper_execution_discussion_ready_for_design_only",
    "execution_approved",
    "scheduling_approved",
    "survives_10_bps=True; survives_25_bps=False",
    "crypto_execution_out_of_scope_not_approved",
    "execution_scheduling_not_approved",
]

FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "create_order",
    "get_alpaca_positions",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "load_config(",
    "yfinance",
    "yf.download",
    "download_close_prices",
    "download_backtest_prices",
    "allow_shorting = True",
    "enable_margin",
    "sched.scheduler",
    "Task Scheduler",
]


def main() -> int:
    failures: list[str] = []
    verify_command_registered(failures)
    verify_module_source(failures)
    verify_generated_output_ignored(failures)
    verify_missing_inputs_degrade_gracefully(failures)

    if failures:
        print("Stock/ETF paper execution readiness report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Stock/ETF paper execution readiness report verification passed.")
    print("Verified report-only command, ignored output, false approvals, missing-input handling, and no execution-path tokens.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    source = read_text(BOT)
    if COMMAND not in source:
        failures.append(f"{COMMAND} is missing from bot.py")
    branch_index = source.find("if args.stock_etf_paper_execution_readiness_report:")
    load_config_index = source.find("config = load_config(")
    if branch_index == -1:
        failures.append("missing stock/ETF readiness branch")
    elif load_config_index != -1 and branch_index > load_config_index:
        failures.append("stock/ETF readiness report must route before config loading")
    early_route_index = source.find(f'sys.argv[1:] == ["{COMMAND}"]')
    alpaca_import_index = source.find("from alpaca.trading.client import TradingClient")
    if early_route_index == -1:
        failures.append("missing exact early report-only route for stock/ETF readiness command")
    elif alpaca_import_index != -1 and early_route_index > alpaca_import_index:
        failures.append("early report-only route should be before broker imports")


def verify_module_source(failures: list[str]) -> None:
    source = read_text(MODULE)
    for token in REQUIRED_TOKENS:
        if token not in source:
            failures.append(f"missing readiness-report token: {token}")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"forbidden execution/config/scheduling token in readiness report: {token}")
    if "DictWriter" not in source:
        failures.append("readiness report should write its expected generated CSV via DictWriter")
    if source.count("write_rows(") > 2:
        failures.append("readiness report should have a single generated CSV write path")


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


def verify_missing_inputs_degrade_gracefully(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        code = (
            "from trading_bot.research.stock_etf_paper_execution_readiness import "
            "generate_stock_etf_paper_execution_readiness_report; "
            "r=generate_stock_etf_paper_execution_readiness_report(r'.'); "
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
            failures.append(f"readiness report should handle missing inputs without traceback: {completed.stderr.strip()}")
            return
        output = root / OUTPUT
        if not output.exists():
            failures.append("readiness report did not write expected CSV in missing-input fixture")
            return
        with output.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not any(row.get("check_name") == "final_paper_execution_discussion_status" for row in rows):
            failures.append("readiness report should include a final status row")
        if not any("blocked" in str(row.get("check_status", "")) for row in rows):
            failures.append("missing inputs should produce blocked readiness rows")
        if not all(str(row.get("execution_approved", "")).lower() == "false" for row in rows):
            failures.append("readiness report rows must keep execution_approved false")
        if not all(str(row.get("scheduling_approved", "")).lower() == "false" for row in rows):
            failures.append("readiness report rows must keep scheduling_approved false")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
