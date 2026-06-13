from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "project_research_state_quality_report.py"
COMMAND = "--project-research-state-quality-report"
OUTPUT = "data/project_research_state_quality_report.csv"

EXPECTED_INPUTS = [
    "data/project_research_state_summary.csv",
    "data/project_research_state_refresh.csv",
    "data/project_research_state_next_steps.csv",
]

REQUIRED_TOKENS = [
    OUTPUT,
    "freshness_for_path",
    "execution_approved",
    "scheduling_approved",
    "blocked_non_false_approval_flag",
    "warning_missing_approval_flags",
    "blocked_missing",
    "blocked_stale",
    "warning_stale",
    "final_quality_status",
]

FORBIDDEN_TOKENS = [
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
    "config.json",
    "yfinance",
    "yf.download",
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
        print("Project research-state quality report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Project research-state quality report verification passed.")
    print("Verified report-only quality command, false approval flags, ignored output, and missing-file handling.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    source = read_text(BOT)
    if COMMAND not in source:
        failures.append(f"{COMMAND} is missing from bot.py")
    branch_index = source.find("if args.project_research_state_quality_report:")
    load_config_index = source.find("config = load_config(")
    if branch_index == -1:
        failures.append("missing project research-state quality branch")
    elif load_config_index != -1 and branch_index > load_config_index:
        failures.append("project research-state quality report must route before config loading")


def verify_module_source(failures: list[str]) -> None:
    source = read_text(MODULE)
    for token in EXPECTED_INPUTS + REQUIRED_TOKENS:
        if token not in source:
            failures.append(f"missing quality-report token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in source:
            failures.append(f"forbidden execution/config/scheduling token in quality report: {token}")
    if "DictWriter" not in source:
        failures.append("quality report should write its expected generated CSV via DictWriter")
    if source.count("write_rows(") > 2:
        failures.append("quality report should have a single generated CSV write path")


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
        completed = subprocess.run(
            [sys.executable, "-c", "from trading_bot.research.project_research_state_quality_report import generate_project_research_state_quality_report; r=generate_project_research_state_quality_report(r'.'); print('\\n'.join(r.summary_lines))"],
            cwd=root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0:
            failures.append(f"quality report should handle missing inputs without traceback: {completed.stderr.strip()}")
            return
        output = root / OUTPUT
        if not output.exists():
            failures.append("quality report did not write expected CSV in missing-input fixture")
            return
        rows = list(csv.DictReader(output.open(newline="", encoding="utf-8")))
        if not any(row.get("check_status") == "blocked_missing" for row in rows):
            failures.append("missing inputs should produce blocked_missing rows")
        if not all(str(row.get("execution_approved", "")).lower() == "false" for row in rows):
            failures.append("quality report rows must keep execution_approved false")
        if not all(str(row.get("scheduling_approved", "")).lower() == "false" for row in rows):
            failures.append("quality report rows must keep scheduling_approved false")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
