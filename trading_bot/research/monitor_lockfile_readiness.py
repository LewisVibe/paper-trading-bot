"""Static readiness report for future monitor refresh no-overlap design."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MONITOR_LOCKFILE_READINESS_COLUMNS = [
    "check_name",
    "status",
    "risk_level",
    "category",
    "evidence",
    "required_next_step",
    "scheduling_approved",
    "execution_approved",
]

SAFE_FUTURE_CANDIDATES = [
    "python bot.py --refresh-market-monitor",
    "python bot.py --market-monitor-scheduling-readiness-report",
    "python bot.py --vps-operations-readiness-report",
    "python bot.py --deployment-readiness-report",
]

BLOCKED_COMMANDS = [
    "python bot.py",
    "python bot.py --paper-order-test ...",
    "python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper",
    "any execution-capable command",
]


@dataclass
class MonitorLockfileReadinessReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_monitor_lockfile_readiness_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/monitor_lockfile_readiness_report.csv",
) -> MonitorLockfileReadinessReportResult:
    root = Path(root_dir)
    rows = build_monitor_lockfile_readiness_rows(root)
    output_path = root / output_filename
    write_monitor_lockfile_readiness_report(output_path, rows)
    return MonitorLockfileReadinessReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_monitor_lockfile_readiness_summary(rows, output_path),
    )


def build_monitor_lockfile_readiness_rows(root: Path) -> list[dict[str, Any]]:
    bot_source = read_text(root / "bot.py")
    runner_source = read_text(root / "trading_bot" / "runners" / "research_reports.py")
    docs_source = "\n".join(
        [
            read_text(root / "README.md"),
            read_text(root / "docs" / "CURRENT_STATE.md"),
            read_text(root / "docs" / "VPS_SETUP_CHECKLIST.md"),
            read_text(root / "docs" / "HERMES_WORKFLOW.md"),
            read_text(root / "docs" / "HERMES_TASK_BOARD.md"),
            read_text(root / "docs" / "CODEX_WORKFLOW.md"),
        ]
    )

    return [
        report_only_command_row(bot_source, runner_source),
        no_runtime_locking_row(bot_source, runner_source),
        safe_future_candidates_row(docs_source),
        blocked_commands_row(docs_source),
        stale_lock_policy_row(docs_source),
        metadata_constraints_row(docs_source),
        no_secret_lock_contents_row(docs_source),
        future_tests_required_row(docs_source),
        scheduling_review_required_row(docs_source),
        execution_not_approved_row(),
        scheduling_not_approved_row(),
    ]


def report_only_command_row(bot_source: str, runner_source: str) -> dict[str, Any]:
    passed = (
        "--monitor-lockfile-readiness-report" in bot_source
        and "run_monitor_lockfile_readiness_report_command" in runner_source
    )
    return readiness_row(
        "monitor_lockfile_readiness_command_exists",
        "pass" if passed else "warning",
        "medium",
        "command_design",
        f"cli_and_runner_present={passed}",
        "Keep this command report-only and routed before normal config/runtime loading.",
    )


def no_runtime_locking_row(bot_source: str, runner_source: str) -> dict[str, Any]:
    combined = bot_source + "\n" + runner_source
    forbidden_tokens = ["acquire_lock", "release_lock", "LockFile", ".lock"]
    found = [token for token in forbidden_tokens if token in combined]
    return readiness_row(
        "no_runtime_locking_added",
        "pass" if not found else "error",
        "high",
        "command_design",
        "Runtime locking tokens in command routing: " + (", ".join(found) if found else "none"),
        "Do not add lock acquisition or release until a separate implementation task.",
    )


def safe_future_candidates_row(docs_source: str) -> dict[str, Any]:
    missing = [command for command in SAFE_FUTURE_CANDIDATES if command not in docs_source]
    return readiness_row(
        "safe_future_candidates_documented",
        "pass" if not missing else "warning",
        "medium",
        "safe_future_candidates",
        "Missing candidate docs: " + (", ".join(missing) if missing else "none"),
        "Limit any future lock helper to report/display/monitor refresh commands after manual review.",
    )


def blocked_commands_row(docs_source: str) -> dict[str, Any]:
    missing = [command for command in BLOCKED_COMMANDS if command not in docs_source]
    return readiness_row(
        "blocked_commands_documented",
        "pass" if not missing else "warning",
        "high",
        "blocked_commands",
        "Missing blocked command docs: " + (", ".join(missing) if missing else "none"),
        "Never schedule or lock-wrap normal bot execution, paper-order tests, slow-SMA paper execution, or execution-capable commands.",
    )


def stale_lock_policy_row(docs_source: str) -> dict[str, Any]:
    lower_source = docs_source.lower()
    passed = "stale lock" in lower_source and "conservative" in lower_source and "manual review" in lower_source
    return readiness_row(
        "stale_lock_policy_documented",
        "pass" if passed else "warning",
        "high",
        "future_implementation_requirements",
        "Docs describe conservative stale-lock handling." if passed else "Could not confirm conservative stale-lock docs.",
        "Define stale-lock handling conservatively before implementation.",
    )


def metadata_constraints_row(docs_source: str) -> dict[str, Any]:
    required = ["command name", "started_at", "host", "pid"]
    missing = [item for item in required if item not in docs_source]
    return readiness_row(
        "safe_lock_metadata_documented",
        "pass" if not missing else "warning",
        "medium",
        "future_implementation_requirements",
        "Missing safe metadata docs: " + (", ".join(missing) if missing else "none"),
        "Keep lock metadata minimal and non-sensitive.",
    )


def no_secret_lock_contents_row(docs_source: str) -> dict[str, Any]:
    required = ["secrets", "account IDs", "config contents", "order IDs", "webhook URLs", "API keys"]
    missing = [item for item in required if item not in docs_source]
    return readiness_row(
        "no_secret_lock_contents_documented",
        "pass" if not missing else "warning",
        "high",
        "future_implementation_requirements",
        "Missing forbidden lock-content docs: " + (", ".join(missing) if missing else "none"),
        "Never include secrets, account/order identifiers, config contents, API keys, webhook URLs, positions, or generated trading data in a lock.",
    )


def future_tests_required_row(docs_source: str) -> dict[str, Any]:
    lower_source = docs_source.lower()
    passed = "lock helper tests" in lower_source or "isolated lock helper tests" in lower_source
    return readiness_row(
        "lock_helper_tests_required",
        "pass" if passed else "warning",
        "medium",
        "future_implementation_requirements",
        "Docs require isolated lock helper tests." if passed else "Could not confirm lock helper test requirement.",
        "Add pure helper tests before applying a lock helper to any command.",
    )


def scheduling_review_required_row(docs_source: str) -> dict[str, Any]:
    lower_source = docs_source.lower()
    passed = "manual review" in lower_source and "consider scheduling safe monitor/report refresh commands" in lower_source
    return readiness_row(
        "scheduling_review_required",
        "pass" if passed else "warning",
        "high",
        "future_implementation_requirements",
        "Docs require manual review before scheduling safe monitor/report refresh commands." if passed else "Could not confirm manual scheduling review requirement.",
        "Require separate manual review before any repeated safe monitor/report refresh schedule.",
    )


def execution_not_approved_row() -> dict[str, Any]:
    return readiness_row(
        "execution_not_approved",
        "pass",
        "high",
        "approval_boundary",
        "This report does not approve execution, paper orders, order instructions, or execution-capable workflows.",
        "Keep execution-capable commands separate, manual, and never scheduled.",
    )


def scheduling_not_approved_row() -> dict[str, Any]:
    return readiness_row(
        "scheduling_not_approved",
        "pass",
        "high",
        "approval_boundary",
        "This report does not create or approve scheduling, cron, services, Task Scheduler entries, or loop mode.",
        "Treat scheduling as a separate future review after safe single-run commands and no-overlap design are stable.",
    )


def readiness_row(
    check_name: str,
    status: str,
    risk_level: str,
    category: str,
    evidence: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "check_name": check_name,
        "status": status,
        "risk_level": risk_level,
        "category": category,
        "evidence": evidence,
        "required_next_step": required_next_step,
        "scheduling_approved": False,
        "execution_approved": False,
    }


def write_monitor_lockfile_readiness_report(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MONITOR_LOCKFILE_READINESS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_monitor_lockfile_readiness_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts = Counter(row.get("status", "unknown") for row in rows)
    execution_false = all(str(row.get("execution_approved")).lower() == "false" for row in rows)
    scheduling_false = all(str(row.get("scheduling_approved")).lower() == "false" for row in rows)
    return [
        f"Monitor lockfile readiness checks: {len(rows)}",
        f"Pass: {counts['pass']}, warning: {counts['warning']}, error: {counts['error']}",
        f"Execution approved false for all rows: {execution_false}",
        f"Scheduling approved false for all rows: {scheduling_false}",
        "Warning: this is report-only design scaffolding and does not create locks, schedules, or execution approval.",
        f"Saved monitor lockfile readiness report to {output_path}",
    ]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
