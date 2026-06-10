from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RUNNER_PATH = ROOT / "trading_bot" / "runners" / "research_reports.py"
DEFENSIVE_REFRESH_PATH = ROOT / "trading_bot" / "research" / "defensive_refresh.py"
LOCK_HELPER_PATH = ROOT / "trading_bot" / "safety" / "monitor_lockfile.py"

DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "CODEX_WORKFLOW.md",
    ROOT / "docs" / "VPS_SETUP_CHECKLIST.md",
]

DEFENSIVE_REFRESH_COMMAND = "--refresh-defensive-research"
EXPECTED_LOCKED_COMMANDS = {
    "run_monitor_lockfile_readiness_report_command": "--monitor-lockfile-readiness-report",
    "run_refresh_promoted_review_command": "--refresh-promoted-review",
}

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

FORBIDDEN_REFRESH_TOKENS = {
    "alpaca": ["alpaca", "TradingClient("],
    "sqlite_trade_log": ["sqlite3", "trade_log", "insert into"],
    "discord": ["discord", "webhook", "send_discord"],
    "paper_positions": ["paper_position", "paper positions", "positions"],
    "yfinance": ["yfinance", "yf.", "download("],
}

LOCK_TOKENS = ["acquire_monitor_lock(", "release_monitor_lock("]
SCHEDULING_TOKENS = ["schtasks", "task scheduler", "crontab", "cron job", ".service", ".timer"]

GENERATED_OUTPUTS = [
    "data/defensive_research_refresh_summary.csv",
    "data/etf_rotation_robustness_report.csv",
    "data/vol_managed_etf_robustness_report.csv",
    "data/defensive_candidate_comparison.csv",
    "data/etf_defensive_drawdown_comparison.csv",
    "data/charts/etf_defensive_drawdown_comparison.png",
]


def main() -> int:
    failures: list[str] = []

    verify_command_exists_and_is_documented(failures)
    verify_refresh_is_research_report_chart_only(failures)
    verify_no_execution_or_external_paths(failures)
    verify_generated_outputs_are_ignored(failures)
    verify_outputs_are_not_execution_approval(failures)
    verify_not_scheduled(failures)
    verify_not_currently_lock_wrapped(failures)
    verify_future_candidate_only(failures)
    verify_blocked_commands_remain_blocked(failures)
    verify_current_lock_wrappers_remain_limited(failures)

    if failures:
        print("Refresh defensive research lock readiness verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Refresh defensive research lock readiness verification passed.")
    print("Verified --refresh-defensive-research is a future-only no-overlap candidate, remains unwrapped, research/report/chart-only, non-execution, unscheduled, and separate from current lock wrapping.")
    return 0


def verify_command_exists_and_is_documented(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    docs_lower = docs_text().lower()
    if "run_refresh_defensive_research_command" not in runner_source:
        failures.append("run_refresh_defensive_research_command is missing from research report runner")
    if DEFENSIVE_REFRESH_COMMAND not in inventory_source:
        failures.append("--refresh-defensive-research is missing from command inventory")
    if DEFENSIVE_REFRESH_COMMAND not in docs_lower:
        failures.append("--refresh-defensive-research is missing from docs")
    if "research/report/chart" not in docs_lower and "saved-report/dashboard chain" not in docs_lower:
        failures.append("--refresh-defensive-research must be documented as research/report/chart refresh only")


def verify_refresh_is_research_report_chart_only(failures: list[str]) -> None:
    source = read_text(DEFENSIVE_REFRESH_PATH).lower()
    required_phrases = [
        "research-only defensive report refresh",
        "research_only",
        "preview_only",
        "execution_approved",
        "not execution",
        "does not approve execution",
        "saved research csv inputs",
    ]
    for phrase in required_phrases:
        if phrase not in source:
            failures.append(f"defensive refresh should include research/report-only marker: {phrase}")
    if '"execution_approved": false' not in source:
        failures.append("defensive refresh rows must set execution_approved=False")


def verify_no_execution_or_external_paths(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    refresh_body = extract_function_body(runner_source, "run_refresh_defensive_research_command")
    source = "\n".join([refresh_body, read_text(DEFENSIVE_REFRESH_PATH)])
    source_lower = source.lower()
    for token in EXECUTION_TOKENS:
        if token.lower() in source_lower and token != "create/cancel/submit orders":
            failures.append(f"--refresh-defensive-research path must not include execution token: {token}")
    for category, tokens in FORBIDDEN_REFRESH_TOKENS.items():
        for token in tokens:
            if token.lower() in source_lower:
                failures.append(f"--refresh-defensive-research path must not include {category} token: {token}")


def verify_generated_outputs_are_ignored(failures: list[str]) -> None:
    for output_path in GENERATED_OUTPUTS:
        if not is_git_ignored(output_path):
            failures.append(f"generated defensive refresh output should remain ignored: {output_path}")


def verify_outputs_are_not_execution_approval(failures: list[str]) -> None:
    docs_lower = docs_text().lower()
    required_phrases = [
        "does not call alpaca",
        "does not approve execution",
        "execution_approved=false",
        "no order instructions",
    ]
    for phrase in required_phrases:
        if phrase not in docs_lower:
            failures.append(f"docs must state defensive outputs are not execution approval: {phrase}")


def verify_not_scheduled(failures: list[str]) -> None:
    grep_output = run_git_grep([".github", "."], patterns=[DEFENSIVE_REFRESH_COMMAND])
    for line in grep_output.splitlines():
        line_lower = line.lower()
        if any(token in line_lower for token in ["schedule:", "cron", "schtasks", "task scheduler"]):
            failures.append(f"--refresh-defensive-research appears scheduled: {line}")
    docs_lower = docs_text().lower()
    if DEFENSIVE_REFRESH_COMMAND in docs_lower and "later scheduling review only" not in docs_lower:
        failures.append("--refresh-defensive-research scheduling mentions must remain future-review only")


def verify_not_currently_lock_wrapped(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    refresh_body = extract_function_body(runner_source, "run_refresh_defensive_research_command")
    for token in LOCK_TOKENS:
        if token in refresh_body:
            failures.append(f"--refresh-defensive-research must not be lock-wrapped yet; found {token}")


def verify_future_candidate_only(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.safety.monitor_lockfile import LOCK_WRAPPED_COMMAND_NAMES, SAFE_LOCK_COMMAND_NAMES  # noqa: PLC0415

    docs_lower = docs_text().lower()
    if DEFENSIVE_REFRESH_COMMAND not in SAFE_LOCK_COMMAND_NAMES:
        failures.append("--refresh-defensive-research should remain only a helper allowlist candidate")
    if DEFENSIVE_REFRESH_COMMAND in LOCK_WRAPPED_COMMAND_NAMES:
        failures.append("--refresh-defensive-research must not be in the wrapped-command allowlist yet")
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


def verify_current_lock_wrappers_remain_limited(failures: list[str]) -> None:
    runner_source = read_text(RUNNER_PATH)
    runner_without_expected_wrappers = runner_source
    for function_name, command_name in EXPECTED_LOCKED_COMMANDS.items():
        function_body = extract_function_body(runner_source, function_name)
        if command_name not in function_body:
            failures.append(f"{function_name} should only lock-wrap {command_name}")
        if function_body.count("acquire_monitor_lock(") != 1:
            failures.append(f"{command_name} should have exactly one acquire call")
        if function_body.count("release_monitor_lock(") != 1:
            failures.append(f"{command_name} should have exactly one release call")
        runner_without_expected_wrappers = runner_without_expected_wrappers.replace(function_body, "")
    for token in LOCK_TOKENS:
        if token in runner_without_expected_wrappers:
            failures.append(f"no command other than current safe report commands should use monitor lock helper: {token}")


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


def run_git_grep(paths: list[str], patterns: list[str]) -> str:
    command = ["git", "grep", "-n"]
    for pattern in patterns:
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


if __name__ == "__main__":
    sys.exit(main())
