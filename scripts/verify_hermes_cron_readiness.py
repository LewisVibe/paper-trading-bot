from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "VPS_SETUP_CHECKLIST.md",
    ROOT / "docs" / "HERMES_WORKFLOW.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "CODEX_WORKFLOW.md",
]

INITIAL_HERMES_CRON_CANDIDATES = {
    "--vps-monitoring-status",
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
    "--market-monitor-scheduling-readiness-report",
}

LOCK_WRAPPED_REQUIRED = {
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
}

FORBIDDEN_SCHEDULING_COMMAND_PHRASES = [
    "normal bot run",
    "paper-order smoke test",
    "slow-sma paper execution",
    "future order-capable command",
]

REQUIRED_DOC_PHRASES = [
    "Hermes cron preferred for future monitoring scheduling if configured.",
    "No scheduling is currently approved or created.",
    "Use Hermes cron for safe monitoring/reporting only; not for execution.",
    "Do not paste config/API keys/webhooks/account IDs into Hermes prompts.",
    "Initial cron candidate should probably be a status/checkpoint job before refresh jobs.",
    "Refresh jobs should remain protected by lockfile/no-overlap.",
    "A stale lock requires manual review.",
    "Scheduling cadence is a separate future decision.",
    "enabled_toolsets",
    r".venv\Scripts\python.exe",
    "C:\\dev\\paper-trading-bot",
]

FORBIDDEN_CREATION_TOKENS = [
    "schtasks /create",
    "Register-ScheduledTask",
    "crontab -e",
    "systemctl enable",
    "New-Service",
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def main() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    checks = build_checks()
    for check in checks:
        print(f"{check.status.upper()}: {check.name}: {check.detail}")

    failures = [check for check in checks if check.status == "error"]
    print(f"Hermes cron readiness checks: {len(checks)}")
    print(f"Pass: {sum(check.status == 'pass' for check in checks)}, warning: {sum(check.status == 'warning' for check in checks)}, error: {len(failures)}")
    print("scheduling_approved=False")
    print("execution_approved=False")
    print("Warning: this verifier is planning/checkpoint only and does not create or approve Hermes cron, Task Scheduler, services, or execution.")

    if failures:
        return 1
    return 0


def build_checks() -> list[CheckResult]:
    docs_text = "\n".join(read_text(path) for path in DOC_PATHS)
    docs_lower = docs_text.lower()
    from trading_bot.safety.monitor_lockfile import LOCK_WRAPPED_COMMAND_NAMES  # noqa: PLC0415

    return [
        docs_phrase_check(docs_text),
        candidate_command_set_check(),
        lock_wrapped_command_set_check(set(LOCK_WRAPPED_COMMAND_NAMES)),
        status_commands_documented_check(docs_text),
        execution_exclusion_check(docs_lower),
        no_scheduler_creation_tokens_check(docs_text),
        generated_outputs_policy_check(),
        repo_safety_check_documented(docs_text),
        manual_review_requirements_check(docs_lower),
    ]


def docs_phrase_check(docs_text: str) -> CheckResult:
    missing = [phrase for phrase in REQUIRED_DOC_PHRASES if phrase not in docs_text]
    return CheckResult(
        "hermes_cron_required_planning_phrases",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def candidate_command_set_check() -> CheckResult:
    forbidden = [
        phrase
        for phrase in FORBIDDEN_SCHEDULING_COMMAND_PHRASES
        if phrase.startswith("--") and phrase in INITIAL_HERMES_CRON_CANDIDATES
    ]
    expected = ", ".join(sorted(INITIAL_HERMES_CRON_CANDIDATES))
    return CheckResult(
        "initial_candidate_set_limited_to_safe_monitoring",
        "pass" if not forbidden and len(INITIAL_HERMES_CRON_CANDIDATES) == 5 else "error",
        f"candidates={expected}; forbidden={', '.join(forbidden) if forbidden else 'none'}",
    )


def lock_wrapped_command_set_check(actual: set[str]) -> CheckResult:
    return CheckResult(
        "refresh_report_overlap_commands_lock_wrapped",
        "pass" if actual == LOCK_WRAPPED_REQUIRED else "error",
        f"lock_wrapped={', '.join(sorted(actual))}",
    )


def status_commands_documented_check(docs_text: str) -> CheckResult:
    missing = [command for command in INITIAL_HERMES_CRON_CANDIDATES if command not in docs_text]
    return CheckResult(
        "safe_status_report_commands_documented",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def execution_exclusion_check(docs_lower: str) -> CheckResult:
    required = [
        "execution-capable commands remain high-risk/manual-only",
        "normal bot run",
        "paper-order smoke test",
        "slow-sma paper execution",
        "future order-capable command",
        "lockfile protection does not make execution-capable commands schedulable",
    ]
    missing = [phrase for phrase in required if phrase not in docs_lower]
    return CheckResult(
        "execution_capable_commands_excluded",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def no_scheduler_creation_tokens_check(docs_text: str) -> CheckResult:
    found = [token for token in FORBIDDEN_CREATION_TOKENS if token in docs_text]
    tracked_files = git_lines(["ls-files"])
    scheduler_files = [
        path
        for path in tracked_files
        if path.endswith((".service", ".timer", ".cron", ".task.xml"))
        or path.lower() in {"crontab", "schedule.ps1"}
    ]
    problems = found + scheduler_files
    return CheckResult(
        "no_scheduler_service_cron_artifacts_created",
        "pass" if not problems else "error",
        "problems=" + (", ".join(problems) if problems else "none"),
    )


def generated_outputs_policy_check() -> CheckResult:
    generated_paths = [
        "data/market_monitor_scheduling_readiness_report.csv",
        "data/monitor_lockfile_readiness_report.csv",
        "data/promoted_review_refresh_summary.csv",
        "data/defensive_research_refresh_summary.csv",
        "data/promoted_decision_preview.csv",
    ]
    failures = [
        path
        for path in generated_paths
        if not is_git_ignored(path) or is_git_tracked(path)
    ]
    return CheckResult(
        "generated_outputs_ignored_untracked",
        "pass" if not failures else "error",
        "failures=" + (", ".join(failures) if failures else "none"),
    )


def repo_safety_check_documented(docs_text: str) -> CheckResult:
    required = [
        "python scripts\\verify_repo_safety.py",
        "repo-safety check",
        "concise output capture",
    ]
    missing = [phrase for phrase in required if phrase not in docs_text]
    return CheckResult(
        "repo_safety_and_output_capture_documented",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def manual_review_requirements_check(docs_lower: str) -> CheckResult:
    required = [
        "exact cadence",
        "exact command list",
        "enabled toolsets",
        "output destination",
        "failure behaviour",
    ]
    missing = [phrase for phrase in required if phrase not in docs_lower]
    return CheckResult(
        "future_manual_review_requirements_documented",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def is_git_ignored(path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def is_git_tracked(path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


if __name__ == "__main__":
    raise SystemExit(main())
