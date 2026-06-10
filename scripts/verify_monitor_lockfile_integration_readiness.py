from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "CODEX_WORKFLOW.md",
]

REQUIRED_FILES = [
    ROOT / "trading_bot" / "safety" / "monitor_lockfile.py",
    ROOT / "scripts" / "verify_monitor_lockfile_helper.py",
    ROOT / "scripts" / "verify_monitor_lockfile_contract.py",
]

HELPER_USE_TOKENS = [
    "trading_bot.safety.monitor_lockfile",
    "from trading_bot.safety import monitor_lockfile",
    "import monitor_lockfile",
    "LockMetadata",
    "LockDecision",
    "build_lock_metadata",
    "validate_lock_metadata",
    "evaluate_existing_lock",
]

LOCK_RUNTIME_TOKENS = [
    "acquire_lock(",
    "release_lock(",
    "create_lock(",
    "delete_lock(",
    "with_lock(",
    ".acquire(",
    ".release(",
]

BLOCKED_COMMAND_PHRASES = [
    "normal `python bot.py`",
    "--paper-order-test",
    "--confirm-paper-order",
    "--execute-slow-sma-paper",
    "--confirm-slow-sma-paper",
]

FUTURE_ONLY_PHRASES = [
    "future",
    "only command protected by the monitor lockfile helper",
    "does not approve scheduling",
    "does not approve execution",
    "report/preview/display/monitor",
]

OUTPUT_APPROVAL_REFUSALS = [
    "preview/display/report only",
    "report/preview/display/monitor",
    "does not approve execution",
    "does not approve orders",
]

SCHEDULING_FILE_FRAGMENTS = [
    "task scheduler",
    ".xml",
    ".service",
    ".timer",
    "crontab",
    "cron.",
    ".cron",
]


def main() -> int:
    failures: list[str] = []

    verify_required_files_exist(failures)
    verify_bot_is_not_using_helper(failures)
    verify_lock_wrapping_is_limited_to_readiness_report(failures)
    verify_future_only_docs(failures)
    verify_blocked_commands_documented(failures)
    verify_helper_decision_flags(failures)
    verify_no_scheduler_files_added(failures)
    verify_outputs_do_not_approve_execution(failures)

    if failures:
        print("Monitor lockfile integration readiness verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Monitor lockfile integration readiness verification passed.")
    print("Verified helper/test presence, no bot.py helper wiring, single-command lock wrapping, future-only docs for other commands, blocked commands, false approval flags, and no scheduler/service additions.")
    return 0


def verify_required_files_exist(failures: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"Required file is missing: {path.relative_to(ROOT)}")


def verify_bot_is_not_using_helper(failures: list[str]) -> None:
    bot_source = read_text(ROOT / "bot.py")
    for token in HELPER_USE_TOKENS:
        if token in bot_source:
            failures.append(f"bot.py must not use monitor lock helper yet; found {token}")


def verify_lock_wrapping_is_limited_to_readiness_report(failures: list[str]) -> None:
    runner_source = read_text(ROOT / "trading_bot" / "runners" / "research_reports.py")
    function_body = extract_function_body(runner_source, "run_monitor_lockfile_readiness_report_command")
    if "acquire_monitor_lock(" not in function_body:
        failures.append("monitor lockfile readiness report command should acquire the monitor lock")
    if "release_monitor_lock(" not in function_body:
        failures.append("monitor lockfile readiness report command should release the monitor lock")
    if function_body.count("acquire_monitor_lock(") != 1:
        failures.append("monitor lockfile readiness report command should have exactly one acquire call")
    if function_body.count("release_monitor_lock(") != 1:
        failures.append("monitor lockfile readiness report command should have exactly one release call")
    if '"--monitor-lockfile-readiness-report"' not in function_body:
        failures.append("lock wrapping must name only --monitor-lockfile-readiness-report")

    runner_without_readiness = runner_source.replace(function_body, "")
    forbidden_tokens = ["acquire_monitor_lock(", "release_monitor_lock("]
    for token in forbidden_tokens:
        if token in runner_without_readiness:
            failures.append(f"monitor lock helper must not wrap any other report command; found {token}")

    other_sources = [
        ROOT / "bot.py",
        ROOT / "trading_bot" / "research" / "monitor_lockfile_readiness.py",
    ]
    combined_other = "\n".join(read_text(path) for path in other_sources)
    for token in LOCK_RUNTIME_TOKENS:
        if token in combined_other:
            failures.append(f"Lock acquisition/release must stay out of bot.py and report generation code; found {token}")


def verify_future_only_docs(failures: list[str]) -> None:
    docs_lower = docs_text().lower()
    for phrase in FUTURE_ONLY_PHRASES:
        if phrase not in docs_lower:
            failures.append(f"Missing future-only lockfile documentation phrase: {phrase}")


def verify_blocked_commands_documented(failures: list[str]) -> None:
    docs_lower = docs_text().lower()
    for phrase in BLOCKED_COMMAND_PHRASES:
        if phrase.lower() not in docs_lower:
            failures.append(f"Missing blocked command documentation: {phrase}")


def verify_helper_decision_flags(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from trading_bot.safety.monitor_lockfile import (  # noqa: PLC0415
        build_lock_metadata,
        evaluate_existing_lock,
        validate_lock_metadata,
    )

    decision_cases = [
        validate_lock_metadata(
            build_lock_metadata(
                "--monitor-lockfile-readiness-report",
                "2026-06-10T12:00:00+00:00",
                "vps-host",
                1234,
                stale_after_seconds=900,
            )
        ),
        evaluate_existing_lock(None, datetime.fromisoformat("2026-06-10T12:00:00+00:00")),
    ]
    for decision in decision_cases:
        if decision.execution_approved is not False:
            failures.append("Helper decisions must keep execution_approved=False")
        if decision.scheduling_approved is not False:
            failures.append("Helper decisions must keep scheduling_approved=False")


def verify_no_scheduler_files_added(failures: list[str]) -> None:
    status_output = run_git_status()
    for line in status_output.splitlines():
        path = line[3:].strip().lower()
        if not path or path.startswith("docs/") or path.startswith("scripts/") or path.startswith("trading_bot/safety/"):
            continue
        if any(fragment in path for fragment in SCHEDULING_FILE_FRAGMENTS):
            failures.append(f"Scheduler/service file appears in git status: {path}")


def verify_outputs_do_not_approve_execution(failures: list[str]) -> None:
    docs_lower = docs_text().lower()
    if not any(phrase in docs_lower for phrase in OUTPUT_APPROVAL_REFUSALS):
        failures.append("Docs must state report/preview/display outputs are not execution approval")


def docs_text() -> str:
    return "\n".join(read_text(path) for path in DOC_PATHS)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def extract_function_body(source: str, function_name: str) -> str:
    marker = f"def {function_name}("
    start = source.find(marker)
    if start == -1:
        return ""
    next_def = source.find("\ndef ", start + len(marker))
    if next_def == -1:
        return source[start:]
    return source[start:next_def]


def run_git_status() -> str:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout


if __name__ == "__main__":
    sys.exit(main())
