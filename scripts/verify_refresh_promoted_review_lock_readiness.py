from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RUNNER_PATH = ROOT / "trading_bot" / "runners" / "research_reports.py"
PROMOTED_REFRESH_PATH = ROOT / "trading_bot" / "research" / "promoted_review_refresh.py"
LOCK_HELPER_PATH = ROOT / "trading_bot" / "safety" / "monitor_lockfile.py"

DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "CODEX_WORKFLOW.md",
]

PROMOTED_REVIEW_COMMAND = "--refresh-promoted-review"
LOCKED_COMMAND = "--monitor-lockfile-readiness-report"

BLOCKED_COMMANDS = [
    "python bot.py",
    "--paper-order-test",
    "--confirm-paper-order",
    "--execute-slow-sma-paper",
    "--confirm-slow-sma-paper",
]

EXECUTION_TOKENS = [
    "submit_order",
    "cancel_order",
    "create_order",
    "replace_order",
    "TradingClient(",
    "MarketOrderRequest",
    "LimitOrderRequest",
    "StopOrderRequest",
    "submit_order(",
    "cancel_order(",
    "create/cancel/submit orders",
]

SQLITE_TOKENS = ["sqlite3", "trade_log", "insert into"]
DISCORD_TOKENS = ["discord", "webhook", "send_discord"]
LOCK_TOKENS = ["acquire_monitor_lock(", "release_monitor_lock("]
SCHEDULING_TOKENS = ["schtasks", "task scheduler", "crontab", "cron job", ".service", ".timer"]

GENERATED_OUTPUTS = [
    "data/promoted_review_refresh_summary.csv",
    "data/promoted_strategy_preview.csv",
    "data/promoted_strategy_action_preview.csv",
    "data/promoted_risk_preview.csv",
    "data/promoted_consensus_preview.csv",
    "data/promoted_decision_preview.csv",
]


def main() -> int:
    failures: list[str] = []

    verify_command_exists_and_is_documented(failures)
    verify_refresh_is_preview_report_only(failures)
    verify_no_execution_trade_log_or_alert_paths(failures)
    verify_paper_position_usage_is_readonly(failures)
    verify_generated_outputs_are_ignored(failures)
    verify_outputs_are_not_execution_approval(failures)
    verify_not_scheduled(failures)
    verify_not_currently_lock_wrapped(failures)
    verify_future_candidate_only(failures)
    verify_blocked_commands_remain_blocked(failures)
    verify_current_lock_wrapper_remains_limited(failures)

    if failures:
        print("Refresh promoted review lock readiness verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Refresh promoted review lock readiness verification passed.")
    print("Verified --refresh-promoted-review is a future-only no-overlap candidate, remains unwrapped, non-execution, unscheduled, and separate from current lock wrapping.")
    return 0


def verify_command_exists_and_is_documented(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    docs_lower = docs_text().lower()
    if "run_refresh_promoted_review_command" not in runner_source:
        failures.append("run_refresh_promoted_review_command is missing from research report runner")
    if PROMOTED_REVIEW_COMMAND not in inventory_source:
        failures.append("--refresh-promoted-review is missing from command inventory")
    if PROMOTED_REVIEW_COMMAND not in docs_lower:
        failures.append("--refresh-promoted-review is missing from docs")
    if "preview/report/display only" not in docs_lower:
        failures.append("--refresh-promoted-review must be documented as preview/report/display only")


def verify_refresh_is_preview_report_only(failures: list[str]) -> None:
    source = read_text(PROMOTED_REFRESH_PATH).lower()
    required_phrases = [
        "preview-only promoted review refresh",
        "research_only",
        "preview_only",
        "execution_approved",
        "not execution",
        "does not approve execution",
    ]
    for phrase in required_phrases:
        if phrase not in source:
            failures.append(f"promoted review refresh should include preview/report-only marker: {phrase}")
    if '"execution_approved": false' not in source:
        failures.append("promoted review refresh rows must set execution_approved=False")


def verify_no_execution_trade_log_or_alert_paths(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    refresh_body = extract_function_body(runner_source, "run_refresh_promoted_review_command")
    source = "\n".join([refresh_body, read_text(PROMOTED_REFRESH_PATH)])
    source_lower = source.lower()
    for token in EXECUTION_TOKENS:
        if token.lower() in source_lower and token != "create/cancel/submit orders":
            failures.append(f"--refresh-promoted-review path must not include execution token: {token}")
    for token in SQLITE_TOKENS:
        if token in source_lower:
            failures.append(f"--refresh-promoted-review path must not write/read SQLite trade_log: {token}")
    for token in DISCORD_TOKENS:
        if token in source_lower:
            failures.append(f"--refresh-promoted-review path must not send Discord alerts: {token}")


def verify_paper_position_usage_is_readonly(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    docs_lower = docs_text().lower()
    if "--use-paper-positions-readonly" not in runner_source:
        failures.append("promoted review chain should scope paper-position usage to --use-paper-positions-readonly")
    if "read-only paper-position" not in docs_lower and "paper positions readonly" not in docs_lower:
        failures.append("docs should describe paper-position usage as read-only")
    if "paper positions" in runner_source.lower() and "--use-paper-positions-readonly" not in runner_source:
        failures.append("paper-position usage must be read-only only")


def verify_generated_outputs_are_ignored(failures: list[str]) -> None:
    for output_path in GENERATED_OUTPUTS:
        if not is_git_ignored(output_path):
            failures.append(f"generated promoted review output should remain ignored: {output_path}")


def verify_outputs_are_not_execution_approval(failures: list[str]) -> None:
    docs_lower = docs_text().lower()
    required_phrases = [
        "does not connect promoted candidates to execution",
        "does not approve execution",
        "execution_approved=false",
    ]
    for phrase in required_phrases:
        if phrase not in docs_lower:
            failures.append(f"docs must state promoted outputs are not execution approval: {phrase}")


def verify_not_scheduled(failures: list[str]) -> None:
    docs_lower = docs_text().lower()
    for token in SCHEDULING_TOKENS:
        if token in docs_lower and PROMOTED_REVIEW_COMMAND in surrounding_text(docs_lower, token, 240):
            failures.append(f"--refresh-promoted-review appears near scheduling language: {token}")
    if PROMOTED_REVIEW_COMMAND in run_git_grep([".github", "."]):
        grep_output = run_git_grep([".github", "."], patterns=[PROMOTED_REVIEW_COMMAND])
        for line in grep_output.splitlines():
            line_lower = line.lower()
            if any(token in line_lower for token in ["schedule:", "cron", "schtasks", "task scheduler"]):
                failures.append(f"--refresh-promoted-review appears scheduled: {line}")


def verify_not_currently_lock_wrapped(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    refresh_body = extract_function_body(runner_source, "run_refresh_promoted_review_command")
    for token in LOCK_TOKENS:
        if token in refresh_body:
            failures.append(f"--refresh-promoted-review must not be lock-wrapped yet; found {token}")


def verify_future_candidate_only(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.safety.monitor_lockfile import SAFE_LOCK_COMMAND_NAMES  # noqa: PLC0415

    docs_lower = docs_text().lower()
    if PROMOTED_REVIEW_COMMAND not in SAFE_LOCK_COMMAND_NAMES:
        failures.append("--refresh-promoted-review should remain only a helper allowlist candidate")
    required_phrases = [
        "future",
        "manual review",
        "lock",
        "does not approve scheduling",
        "does not approve execution",
    ]
    for phrase in required_phrases:
        if phrase not in docs_lower:
            failures.append(f"docs must keep future lock candidate language: {phrase}")


def verify_blocked_commands_remain_blocked(failures: list[str]) -> None:
    helper_source = read_text(LOCK_HELPER_PATH)
    docs_lower = docs_text().lower()
    for command in BLOCKED_COMMANDS:
        if command == "python bot.py":
            if "normal python bot.py must not use monitor lock helper" not in helper_source.lower():
                failures.append("normal python bot.py must remain blocked in helper")
        elif command.strip("-") not in helper_source:
            failures.append(f"blocked command is missing from helper source: {command}")
        if command.lower() not in docs_lower:
            failures.append(f"blocked command is missing from docs: {command}")


def verify_current_lock_wrapper_remains_limited(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    readiness_body = extract_function_body(runner_source, "run_monitor_lockfile_readiness_report_command")
    if LOCKED_COMMAND not in readiness_body:
        failures.append("current lock wrapper should remain limited to --monitor-lockfile-readiness-report")
    if readiness_body.count("acquire_monitor_lock(") != 1:
        failures.append("current lock-wrapped command should have exactly one acquire call")
    if readiness_body.count("release_monitor_lock(") != 1:
        failures.append("current lock-wrapped command should have exactly one release call")
    runner_without_readiness = runner_source.replace(readiness_body, "")
    for token in LOCK_TOKENS:
        if token in runner_without_readiness:
            failures.append(f"no command other than readiness report should use monitor lock helper: {token}")


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


def is_git_ignored(path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def run_git_grep(paths: list[str], patterns: list[str] | None = None) -> str:
    command = ["git", "grep", "-n"]
    for pattern in patterns or [PROMOTED_REVIEW_COMMAND]:
        command.extend(["-e", pattern])
    command.extend(["--", *paths])
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def surrounding_text(source: str, token: str, window: int) -> str:
    index = source.find(token)
    if index == -1:
        return ""
    start = max(0, index - window)
    end = min(len(source), index + len(token) + window)
    return source[start:end]


if __name__ == "__main__":
    sys.exit(main())
