from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "docs" / "HERMES_PROMOTED_REVIEW_CRON_DESIGN.md"
LOCK_WRAPPED_REQUIRED = {
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
}

REQUIRED_PHRASES = [
    "No Hermes cron job is currently created, scheduled, enabled, triggered, or approved.",
    "This does not approve scheduling, execution, orders, paper execution, or live trading.",
    "separate from the existing `paper-bot-vps-status-check` daily status job",
    ".venv\\Scripts\\python.exe bot.py --refresh-promoted-review",
    ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    "`--refresh-promoted-review` is lock-wrapped today",
    "stale lock detection as manual review",
    "avoid committing, pushing, pulling, or updating code automatically",
    "avoid creating, editing, deleting, triggering, or recursively creating other cron jobs",
    "avoid printing secrets, config contents, API keys, webhooks, account IDs",
    "avoid normal bot runs, paper-order smoke tests, slow-SMA paper execution",
    "avoid submitting, cancelling, or creating orders",
    "avoid mutating positions",
    "avoid writing SQLite `trade_log`",
    "avoid sending trade alerts",
    "strategy disagreement, that is a monitoring result, not execution approval",
    "`scheduling_approved=False`",
    "`execution_approved=False`",
    "Candidate cadence remains a future manual decision.",
    "Candidate output destination remains a future manual decision.",
]

FORBIDDEN_SCHEDULER_ARTIFACT_TOKENS = [
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
    errors = [check for check in checks if check.status == "error"]
    print(f"Hermes promoted review cron design checks: {len(checks)}")
    print(f"Pass: {sum(check.status == 'pass' for check in checks)}, warning: {sum(check.status == 'warning' for check in checks)}, error: {len(errors)}")
    print("scheduling_approved=False")
    print("execution_approved=False")
    print("Warning: this verifier checks design only and does not create Hermes cron, Task Scheduler, services, loop mode, or execution.")
    return 1 if errors else 0


def build_checks() -> list[CheckResult]:
    text = read_text(DESIGN_PATH)
    from trading_bot.safety.monitor_lockfile import LOCK_WRAPPED_COMMAND_NAMES  # noqa: PLC0415

    return [
        design_exists_check(text),
        required_phrases_check(text),
        lock_wrapped_set_check(set(LOCK_WRAPPED_COMMAND_NAMES)),
        no_scheduler_artifacts_check(text),
    ]


def design_exists_check(text: str) -> CheckResult:
    return CheckResult(
        "promoted_review_cron_design_exists",
        "pass" if DESIGN_PATH.exists() and text else "error",
        str(DESIGN_PATH),
    )


def required_phrases_check(text: str) -> CheckResult:
    normalized = normalize_text(text)
    missing = [phrase for phrase in REQUIRED_PHRASES if normalize_text(phrase) not in normalized]
    return CheckResult(
        "required_future_only_design_phrases",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def lock_wrapped_set_check(actual: set[str]) -> CheckResult:
    return CheckResult(
        "lock_wrapped_command_set_unchanged",
        "pass" if actual == LOCK_WRAPPED_REQUIRED else "error",
        f"lock_wrapped={', '.join(sorted(actual))}",
    )


def no_scheduler_artifacts_check(text: str) -> CheckResult:
    found = [token for token in FORBIDDEN_SCHEDULER_ARTIFACT_TOKENS if token in text]
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


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def normalize_text(text: str) -> str:
    return " ".join(text.split())


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


if __name__ == "__main__":
    raise SystemExit(main())
