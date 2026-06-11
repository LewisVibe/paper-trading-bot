from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RUNNER_PATH = ROOT / "trading_bot" / "runners" / "research_reports.py"
HELPER_PATH = ROOT / "trading_bot" / "safety" / "monitor_lockfile.py"

REQUIRED_FILES = [
    HELPER_PATH,
    ROOT / "scripts" / "verify_monitor_lockfile_helper.py",
    ROOT / "scripts" / "verify_monitor_lockfile_contract.py",
    ROOT / "scripts" / "verify_monitor_lockfile_integration_readiness.py",
    ROOT / "scripts" / "verify_refresh_promoted_review_lock_readiness.py",
    ROOT / "scripts" / "verify_refresh_defensive_research_lock_readiness.py",
]

DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "VPS_SETUP_CHECKLIST.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "CODEX_WORKFLOW.md",
]

EXPECTED_LOCK_WRAPPED_FUNCTIONS = {
    "run_monitor_lockfile_readiness_report_command": "--monitor-lockfile-readiness-report",
    "run_refresh_promoted_review_command": "--refresh-promoted-review",
    "run_refresh_defensive_research_command": "--refresh-defensive-research",
}

BLOCKED_COMMAND_PHRASES = [
    "normal `python bot.py`",
    "python bot.py",
    "--paper-order-test",
    "--confirm-paper-order",
    "--execute-slow-sma-paper",
    "--confirm-slow-sma-paper",
    "any future execution-capable command",
]

REQUIRED_DOC_PHRASES = [
    "prevents overlapping safe refresh/report commands only",
    "does not approve scheduling or execution",
    "safe vps manual monitoring commands",
    "report/refresh/display only",
    "execution-capable commands must never be scheduled",
    "generated csvs/charts/logs/databases/secrets/config must not be committed or pasted",
    "stale lockfiles require manual review, not automatic deletion",
]


def main() -> int:
    failures: list[str] = []

    verify_required_files(failures)
    verify_wrapped_command_set(failures)
    verify_blocked_commands_not_wrapped(failures)
    verify_lock_decisions(failures)
    verify_docs(failures)

    if failures:
        print("Monitor lockfile final state verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Monitor lockfile final state verification passed.")
    print("Verified final three-command lock boundary, blocked execution commands, false approval flags, stale-lock manual review, and VPS handoff documentation.")
    return 0


def verify_required_files(failures: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not path.exists():
            failures.append(f"Required lockfile checkpoint file is missing: {path.relative_to(ROOT)}")


def verify_wrapped_command_set(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.safety.monitor_lockfile import LOCK_WRAPPED_COMMAND_NAMES  # noqa: PLC0415

    expected_commands = set(EXPECTED_LOCK_WRAPPED_FUNCTIONS.values())
    if set(LOCK_WRAPPED_COMMAND_NAMES) != expected_commands:
        failures.append(
            "LOCK_WRAPPED_COMMAND_NAMES must equal "
            f"{sorted(expected_commands)}, got {sorted(LOCK_WRAPPED_COMMAND_NAMES)}"
        )

    runner_source = read_text(RUNNER_PATH)
    runner_without_expected = runner_source
    for function_name, command_name in EXPECTED_LOCK_WRAPPED_FUNCTIONS.items():
        body = extract_function_body(runner_source, function_name)
        if not body:
            failures.append(f"Missing expected runner function: {function_name}")
            continue
        if command_name not in body:
            failures.append(f"{function_name} must lock-wrap only {command_name}")
        if body.count("acquire_monitor_lock(") != 1:
            failures.append(f"{command_name} must have exactly one acquire_monitor_lock call")
        if body.count("release_monitor_lock(") != 1:
            failures.append(f"{command_name} must have exactly one release_monitor_lock call")
        if "finally:" not in body:
            failures.append(f"{command_name} must release the lock from a finally block")
        runner_without_expected = runner_without_expected.replace(body, "")

    for token in ["acquire_monitor_lock(", "release_monitor_lock("]:
        if token in runner_without_expected:
            failures.append(f"No command outside the final safe set may use monitor lock helper: {token}")

    bot_source = read_text(ROOT / "bot.py")
    if "acquire_monitor_lock(" in bot_source or "release_monitor_lock(" in bot_source:
        failures.append("bot.py must not acquire or release monitor locks directly")


def verify_blocked_commands_not_wrapped(failures: list[str]) -> None:
    helper_source = read_text(HELPER_PATH).lower()
    docs_lower = docs_text().lower()
    runner_source = read_text(RUNNER_PATH)

    for phrase in BLOCKED_COMMAND_PHRASES:
        if phrase.lower() not in docs_lower:
            failures.append(f"Docs must list blocked/high-risk command: {phrase}")

    for blocked_token in [
        "paper-order-test",
        "confirm-paper-order",
        "execute-slow-sma-paper",
        "confirm-slow-sma-paper",
    ]:
        if blocked_token not in helper_source:
            failures.append(f"Helper must continue to reject blocked command token: {blocked_token}")
        if blocked_token in runner_source and "acquire_monitor_lock(" in surrounding_text(runner_source, blocked_token, 500):
            failures.append(f"Blocked command appears near lock wrapping: {blocked_token}")


def verify_lock_decisions(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.safety.monitor_lockfile import (  # noqa: PLC0415
        build_lock_metadata,
        evaluate_existing_lock,
        validate_lock_metadata,
    )

    now = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
    for command_name in EXPECTED_LOCK_WRAPPED_FUNCTIONS.values():
        valid_decision = validate_lock_metadata(
            build_lock_metadata(command_name, now, "vps-host", 1234, stale_after_seconds=900)
        )
        assert_false_approval_flags(valid_decision, command_name, failures)
        stale_decision = evaluate_existing_lock(
            build_lock_metadata(
                command_name,
                now - timedelta(seconds=1200),
                "vps-host",
                1234,
                stale_after_seconds=900,
            ),
            now,
        )
        assert_false_approval_flags(stale_decision, f"stale {command_name}", failures)
        if stale_decision.status != "stale_requires_manual_review":
            failures.append(f"Stale lock for {command_name} must require manual review")
        if "silently delete" not in stale_decision.required_next_step.lower():
            failures.append(f"Stale lock for {command_name} must explicitly refuse silent deletion")


def verify_docs(failures: list[str]) -> None:
    docs_lower = docs_text().lower()
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in docs_lower:
            failures.append(f"Missing VPS handoff / lockfile final-state doc phrase: {phrase}")
    for command_name in EXPECTED_LOCK_WRAPPED_FUNCTIONS.values():
        if command_name not in docs_lower:
            failures.append(f"Docs must mention lock-wrapped command: {command_name}")
    for command_name in [
        "py -3 scripts\\verify_repo_safety.py",
        "py -3 scripts\\verify_monitor_lockfile_final_state.py",
        "py -3 bot.py --monitor-lockfile-readiness-report",
        "py -3 bot.py --refresh-promoted-review",
        "py -3 bot.py --refresh-defensive-research",
    ]:
        if command_name.lower() not in docs_lower:
            failures.append(f"VPS handoff docs must include manual command: {command_name}")


def assert_false_approval_flags(decision, label: str, failures: list[str]) -> None:
    if decision.execution_approved is not False:
        failures.append(f"{label}: execution_approved must remain False")
    if decision.scheduling_approved is not False:
        failures.append(f"{label}: scheduling_approved must remain False")


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


def surrounding_text(source: str, token: str, window: int) -> str:
    index = source.find(token)
    if index == -1:
        return ""
    start = max(0, index - window)
    end = min(len(source), index + len(token) + window)
    return source[start:end]


if __name__ == "__main__":
    sys.exit(main())
