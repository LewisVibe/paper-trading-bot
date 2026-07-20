"""Report-only VPS/Hermes operations readiness audit."""

from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VPS_OPERATIONS_READINESS_COLUMNS = [
    "check_name",
    "status",
    "risk_level",
    "evidence",
    "required_next_step",
    "scheduling_approved",
    "execution_approved",
]

OLD_ONEDRIVE_PATH = "C:\\Users\\lewis\\OneDrive\\Documents\\Paper Trading Bot"
SAFE_HERMES_MARKET_MONITOR_COMMAND = "--refresh-market-monitor"

REQUIRED_PROJECT_FILES = [
    "bot.py",
    "README.md",
    "requirements.txt",
    "scripts/verify_repo_safety.py",
    "scripts/verify_command_inventory.py",
    "docs/CURRENT_STATE.md",
    "docs/VPS_SETUP_CHECKLIST.md",
    "docs/HERMES_WORKFLOW.md",
    "trading_bot/runners/research_reports.py",
]

GENERATED_IGNORE_PATTERNS = [
    "data/*",
    "!data/.gitkeep",
    "logs/*",
    "!logs/.gitkeep",
    "*.log",
    "*.db",
]

MARKET_MONITOR_COMMANDS = [
    "--refresh-market-monitor",
    "--market-monitor-scheduling-readiness-report",
]

NEVER_SCHEDULE_COMMANDS = [
    "python bot.py",
    "python bot.py --paper-order-test",
    "python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper",
]


@dataclass
class VpsOperationsReadinessReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vps_operations_readiness_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/vps_operations_readiness_report.csv",
) -> VpsOperationsReadinessReportResult:
    root = Path(root_dir)
    rows = build_vps_operations_readiness_rows(root)
    output_path = root / output_filename
    write_vps_operations_readiness_report(output_path, rows)
    return VpsOperationsReadinessReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_vps_operations_readiness_summary(rows, output_path),
    )


def build_vps_operations_readiness_rows(root: Path) -> list[dict[str, Any]]:
    cli_source = "\n".join(
        [
            read_text(root / "trading_bot" / "cli" / "parser.py"),
            read_text(root / "trading_bot" / "cli" / "report_only.py"),
        ]
    )
    runner_source = read_text(root / "trading_bot" / "runners" / "research_reports.py")
    inventory_source = read_text(root / "scripts" / "verify_command_inventory.py")
    readme_source = read_text(root / "README.md")
    current_state_source = read_text(root / "docs" / "CURRENT_STATE.md")
    vps_checklist_source = read_text(root / "docs" / "VPS_SETUP_CHECKLIST.md")
    hermes_workflow_source = read_text(root / "docs" / "HERMES_WORKFLOW.md")
    gitignore_patterns = read_gitignore_patterns(root / ".gitignore")
    tracked_files = git_tracked_files(root)
    docs_source = "\n".join([readme_source, current_state_source, vps_checklist_source, hermes_workflow_source])

    rows = [
        repo_path_not_old_onedrive_row(root),
        python_executable_inside_venv_row(),
        required_project_files_exist_row(root),
        repo_safety_verifier_exists_row(root),
        market_monitor_commands_exist_row(cli_source, runner_source, inventory_source),
        deployment_readiness_command_exists_row(cli_source, runner_source, inventory_source),
        generated_data_ignored_row(gitignore_patterns),
        config_json_not_tracked_row(tracked_files),
        env_files_not_tracked_row(tracked_files),
        generated_outputs_not_tracked_row(tracked_files),
        no_execution_commands_approved_for_scheduling_row(docs_source),
        safe_hermes_candidate_documented_row(docs_source),
        normal_bot_manual_only_row(docs_source),
        execution_commands_never_schedule_row(docs_source),
        scheduling_not_approved_row(),
        execution_not_approved_row(),
        final_approval_flags_row(),
    ]
    return rows


def repo_path_not_old_onedrive_row(root: Path) -> dict[str, Any]:
    resolved = str(root.resolve())
    old_path_active = resolved.lower() == OLD_ONEDRIVE_PATH.lower()
    return readiness_row(
        "repo_path_is_not_old_onedrive_path",
        "pass" if not old_path_active else "error",
        "high",
        f"repo_path={resolved}",
        "Use C:\\dev\\paper-trading-bot for VPS/Hermes operations work.",
    )


def python_executable_inside_venv_row() -> dict[str, Any]:
    executable = str(Path(sys.executable).resolve())
    expected_fragment = "\\.venv\\Scripts\\"
    in_venv = expected_fragment.lower() in executable.lower()
    return readiness_row(
        "python_executable_is_inside_venv",
        "pass" if in_venv else "warning",
        "medium",
        f"python_executable={executable}",
        "On the VPS, run deterministic report commands with .venv\\Scripts\\python.exe.",
    )


def required_project_files_exist_row(root: Path) -> dict[str, Any]:
    missing = [path for path in REQUIRED_PROJECT_FILES if not (root / path).exists()]
    return readiness_row(
        "required_project_files_exist",
        "pass" if not missing else "error",
        "high",
        "Missing files: " + (", ".join(missing) if missing else "none"),
        "Restore required project, docs, runner, and verifier files before VPS operation.",
    )


def repo_safety_verifier_exists_row(root: Path) -> dict[str, Any]:
    path = root / "scripts" / "verify_repo_safety.py"
    return readiness_row(
        "repo_safety_verifier_exists",
        "pass" if path.exists() else "error",
        "high",
        "scripts/verify_repo_safety.py exists." if path.exists() else "scripts/verify_repo_safety.py is missing.",
        "Run python scripts\\verify_repo_safety.py before commits, handoff, and scheduling review.",
    )


def market_monitor_commands_exist_row(cli_source: str, runner_source: str, inventory_source: str) -> dict[str, Any]:
    missing = []
    for command in MARKET_MONITOR_COMMANDS:
        if command not in cli_source or command not in inventory_source:
            missing.append(command)
    runner_ok = (
        "run_refresh_market_monitor_command" in runner_source
        and "run_market_monitor_scheduling_readiness_report_command" in runner_source
    )
    if not runner_ok:
        missing.append("market monitor runner")
    return readiness_row(
        "market_monitor_commands_exist",
        "pass" if not missing else "error",
        "high",
        "Missing command evidence: " + (", ".join(missing) if missing else "none"),
        "Keep market monitor refresh and scheduling-readiness commands available before VPS operation.",
    )


def deployment_readiness_command_exists_row(cli_source: str, runner_source: str, inventory_source: str) -> dict[str, Any]:
    command = "--deployment-readiness-report"
    passed = (
        command in cli_source
        and command in inventory_source
        and "run_deployment_readiness_report_command" in runner_source
    )
    return readiness_row(
        "deployment_readiness_command_exists",
        "pass" if passed else "error",
        "medium",
        f"{command} present in CLI/inventory/runner: {passed}",
        "Keep deployment readiness available as a separate audit before VPS handoff.",
    )


def generated_data_ignored_row(gitignore_patterns: set[str]) -> dict[str, Any]:
    missing = [pattern for pattern in GENERATED_IGNORE_PATTERNS if pattern not in gitignore_patterns]
    return readiness_row(
        "generated_data_files_remain_ignored_by_git",
        "pass" if not missing else "error",
        "high",
        "Missing .gitignore patterns: " + (", ".join(missing) if missing else "none"),
        "Keep generated data, logs, databases, and cache outputs ignored.",
    )


def config_json_not_tracked_row(tracked_files: set[str]) -> dict[str, Any]:
    tracked = "config.json" in tracked_files
    return readiness_row(
        "config_json_is_not_tracked",
        "pass" if not tracked else "error",
        "high",
        "config.json tracked by git: " + str(tracked),
        "Never commit config.json or use it for monitoring-only report commands.",
    )


def env_files_not_tracked_row(tracked_files: set[str]) -> dict[str, Any]:
    tracked_env = sorted(path for path in tracked_files if path == ".env" or path.startswith(".env."))
    return readiness_row(
        "env_files_are_not_tracked",
        "pass" if not tracked_env else "error",
        "high",
        "Tracked env files: " + (", ".join(tracked_env) if tracked_env else "none"),
        "Never track .env files or secrets.",
    )


def generated_outputs_not_tracked_row(tracked_files: set[str]) -> dict[str, Any]:
    tracked_generated = sorted(
        path
        for path in tracked_files
        if is_generated_output_path(path) and path not in {"data/.gitkeep", "logs/.gitkeep"}
    )
    return readiness_row(
        "logs_databases_generated_csvs_are_not_tracked",
        "pass" if not tracked_generated else "error",
        "high",
        "Tracked generated outputs: " + (", ".join(tracked_generated) if tracked_generated else "none"),
        "Remove generated CSVs, logs, databases, and cache files from tracking before VPS operation.",
    )


def no_execution_commands_approved_for_scheduling_row(docs_source: str) -> dict[str, Any]:
    lower_source = docs_source.lower()
    scheduling_refused = (
        "scheduling is not approved" in lower_source
        or "must never be scheduled" in lower_source
        or "scheduling_approved=false" in lower_source
    )
    orders_refused = (
        "does not approve orders" in lower_source
        or "execution_approved=false" in lower_source
        or "no follow-up or repeat order is approved" in lower_source
    )
    passed = scheduling_refused and orders_refused
    return readiness_row(
        "no_execution_capable_commands_approved_for_scheduling",
        "pass" if passed else "warning",
        "high",
        "Docs state scheduling is not approved and orders are not approved." if passed else "Could not confirm explicit scheduling/order refusal wording.",
        "Keep execution-capable commands out of all schedules.",
    )


def safe_hermes_candidate_documented_row(docs_source: str) -> dict[str, Any]:
    passed = SAFE_HERMES_MARKET_MONITOR_COMMAND in docs_source
    return readiness_row(
        "safe_hermes_vps_monitoring_candidate_documented",
        "pass" if passed else "warning",
        "medium",
        f"Candidate documented: {passed}",
        "Document only the monitoring/report/display market monitor refresh candidate for future Hermes cron review.",
    )


def normal_bot_manual_only_row(docs_source: str) -> dict[str, Any]:
    lower_source = docs_source.lower()
    passed = "python bot.py" in docs_source and ("never schedule" in lower_source or "manual-only" in lower_source)
    return readiness_row(
        "normal_python_bot_py_remains_high_risk_manual_only",
        "pass" if passed else "warning",
        "high",
        "Docs identify normal python bot.py as never-schedule/manual-only." if passed else "Could not confirm normal bot scheduling warning.",
        "Keep normal python bot.py out of Hermes cron and Windows Task Scheduler.",
    )


def execution_commands_never_schedule_row(docs_source: str) -> dict[str, Any]:
    missing = [command for command in NEVER_SCHEDULE_COMMANDS if command not in docs_source]
    return readiness_row(
        "paper_order_and_slow_sma_commands_remain_never_schedule",
        "pass" if not missing else "warning",
        "high",
        "Missing never-schedule command docs: " + (", ".join(missing) if missing else "none"),
        "Keep paper-order tests, slow-SMA paper execution, and normal bot execution out of schedules.",
    )


def scheduling_not_approved_row() -> dict[str, Any]:
    return readiness_row(
        "scheduling_not_approved",
        "pass",
        "high",
        "This audit does not create or approve Windows Task Scheduler tasks, Hermes cron jobs, or services.",
        "Request and review scheduling separately before creating any schedule.",
    )


def execution_not_approved_row() -> dict[str, Any]:
    return readiness_row(
        "execution_not_approved",
        "pass",
        "high",
        "This audit does not approve trading, orders, paper execution, Alpaca access, positions, trade_log writes, or Discord alerts.",
        "Keep VPS/Hermes operations limited to monitoring/report/display commands.",
    )


def final_approval_flags_row() -> dict[str, Any]:
    return readiness_row(
        "final_approval_flags",
        "pass",
        "high",
        "scheduling_approved=False and execution_approved=False for every report row.",
        "Do not treat this report as approval to schedule or execute.",
    )


def readiness_row(
    check_name: str,
    status: str,
    risk_level: str,
    evidence: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "check_name": check_name,
        "status": status,
        "risk_level": risk_level,
        "evidence": evidence,
        "required_next_step": required_next_step,
        "scheduling_approved": False,
        "execution_approved": False,
    }


def write_vps_operations_readiness_report(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=VPS_OPERATIONS_READINESS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_vps_operations_readiness_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts = Counter(row.get("status", "unknown") for row in rows)
    scheduling_false = all(str(row.get("scheduling_approved")).lower() == "false" for row in rows)
    execution_false = all(str(row.get("execution_approved")).lower() == "false" for row in rows)
    return [
        f"VPS operations readiness checks: {len(rows)}",
        f"Pass: {counts['pass']}, warning: {counts['warning']}, error: {counts['error']}",
        f"Scheduling approved false for all rows: {scheduling_false}",
        f"Execution approved false for all rows: {execution_false}",
        f"Saved VPS operations readiness report to {output_path}",
        "Warning: this is audit/report only and does not create or approve scheduling or execution.",
    ]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_gitignore_patterns(path: Path) -> set[str]:
    source = read_text(path)
    return {
        line.strip()
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def git_tracked_files(root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return set()
    if result.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def is_generated_output_path(path: str) -> bool:
    lower_path = path.lower()
    return (
        lower_path.startswith("data/")
        or lower_path.startswith("logs/")
        or lower_path.endswith(".csv")
        or lower_path.endswith(".log")
        or lower_path.endswith(".db")
        or lower_path.endswith(".sqlite")
        or lower_path.endswith(".sqlite3")
    )
