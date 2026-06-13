from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "docs" / "HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md"
LEGACY_POINTER_PATH = ROOT / "docs" / "HERMES_PROMOTED_REVIEW_CRON_DESIGN.md"
DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "HERMES_WORKFLOW.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "VPS_SETUP_CHECKLIST.md",
    ROOT / "docs" / "CODEX_WORKFLOW.md",
]

LOCK_WRAPPED_REQUIRED = {
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
}

CURRENT_STATUS_CRON_PHRASES = [
    "paper-bot-vps-status-check",
    "345188fbb60c",
    "daily at 10:10am UK local time",
    "10 10 * * *",
    "Telegram",
    "script-only / no-agent",
    ".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py",
    ".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py",
    ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    "healthy_monitoring_state",
    "no_action_required",
    "freshness_warnings: none",
]

DESIGN_PHRASES = [
    "No promoted-review refresh Hermes cron job is currently created",
    "This design does not approve scheduling",
    "execution_approved=False",
    "future-only design/checklist",
    "separate from the existing `paper-bot-vps-status-check` daily status cron",
    "after the daily status cron runs reliably",
    "C:\\dev\\paper-trading-bot",
    ".venv\\Scripts\\python.exe",
    ".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py",
    ".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py",
    ".venv\\Scripts\\python.exe bot.py --refresh-promoted-review",
    ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    "`--refresh-promoted-review` is already lock-wrapped",
    "fresh, malformed, stale",
    "require manual review",
    "must remain preview/report-only",
    "Read-only paper-position context is allowed only through the existing preview path",
    "submit, cancel, or create orders",
    "mutate positions",
    "write SQLite `trade_log`",
    "send trade alerts",
    "change config defaults",
    "inspect or print secrets, config contents, account IDs, logs, databases, or full generated CSV contents",
    "commit, push, pull, or update code automatically",
    "create, edit, delete, trigger, or recursively create other cron jobs",
    "Cadence is not approved yet",
    "Output destination is not approved yet",
    "Strategy disagreement, no-action states, blocked review states",
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
    print(f"Hermes promoted review refresh cron design checks: {len(checks)}")
    print(f"Pass: {sum(check.status == 'pass' for check in checks)}, warning: {sum(check.status == 'warning' for check in checks)}, error: {len(errors)}")
    print("scheduling_approved=False")
    print("execution_approved=False")
    print("Warning: this verifier checks design only and does not create Hermes cron, Task Scheduler, services, loop mode, or execution.")
    return 1 if errors else 0


def build_checks() -> list[CheckResult]:
    design_text = read_text(DESIGN_PATH)
    docs_text = "\n".join(read_text(path) for path in DOC_PATHS)
    all_text = design_text + "\n" + docs_text

    from trading_bot.safety.monitor_lockfile import LOCK_WRAPPED_COMMAND_NAMES  # noqa: PLC0415

    return [
        design_exists_check(design_text),
        design_required_phrases_check(design_text),
        design_excludes_extra_status_display_command_check(design_text),
        legacy_pointer_check(),
        current_status_cron_documented_check(docs_text),
        lock_wrapped_set_check(set(LOCK_WRAPPED_COMMAND_NAMES)),
        no_scheduler_artifacts_check(all_text),
    ]


def design_exists_check(text: str) -> CheckResult:
    return CheckResult(
        "promoted_review_refresh_cron_design_exists",
        "pass" if DESIGN_PATH.exists() and text else "error",
        str(DESIGN_PATH),
    )


def design_required_phrases_check(text: str) -> CheckResult:
    normalized = normalize_text(text)
    missing = [phrase for phrase in DESIGN_PHRASES if normalize_text(phrase) not in normalized]
    return CheckResult(
        "future_only_design_requirements_documented",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def design_excludes_extra_status_display_command_check(text: str) -> CheckResult:
    forbidden = ".venv\\Scripts\\python.exe bot.py --show-current-research-state"
    return CheckResult(
        "future_cron_design_excludes_extra_status_display_command",
        "pass" if forbidden not in text else "error",
        "extra_status_display_command=" + ("present" if forbidden in text else "absent"),
    )


def legacy_pointer_check() -> CheckResult:
    text = read_text(LEGACY_POINTER_PATH)
    required = [
        "legacy pointer only",
        "docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md",
        "python scripts\\verify_hermes_promoted_review_refresh_cron_design.py",
        "does not approve scheduling",
        "does not approve scheduling, execution, orders, paper execution, live trading, or any cron changes",
    ]
    normalized = normalize_text(text)
    missing = [phrase for phrase in required if normalize_text(phrase) not in normalized]
    return CheckResult(
        "legacy_promoted_review_cron_doc_points_to_canonical",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def current_status_cron_documented_check(text: str) -> CheckResult:
    normalized = normalize_text(text)
    missing = [phrase for phrase in CURRENT_STATUS_CRON_PHRASES if normalize_text(phrase) not in normalized]
    return CheckResult(
        "current_status_cron_state_documented",
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
