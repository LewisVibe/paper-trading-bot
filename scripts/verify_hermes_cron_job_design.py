from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "docs" / "HERMES_CRON_JOB_DESIGN.md"

DOC_PATHS = [
    DESIGN_PATH,
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "HERMES_WORKFLOW.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "VPS_SETUP_CHECKLIST.md",
]

LOCK_WRAPPED_REQUIRED = {
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
}

REQUIRED_DESIGN_PHRASES = [
    "This document records the current verified first Hermes cron job.",
    "Job name: `paper-bot-vps-status-check`",
    "Job ID: `345188fbb60c`",
    "Cadence: once daily / every 1440m",
    "Delivery: Telegram",
    "Mode: script-only / no-agent",
    "Working directory: `C:\\dev\\paper-trading-bot`",
    ".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py",
    ".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py",
    ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    "final_monitoring_status: healthy_monitoring_state",
    "freshness_warnings: none",
    "does not run `--refresh-promoted-review`",
    "does not run `--refresh-defensive-research`",
    "does not approve scheduling beyond this one status job",
    "does not pull, commit, or push code",
    "does not inspect or print config contents, secrets, API keys, webhooks",
    "does not create, edit, delete, trigger, or recursively create other cron jobs",
    "Lockfile protection is for overlap control only",
    "`scheduling_approved=False`",
    "`execution_approved=False`",
]

FORBIDDEN_FIRST_JOB_APPROVAL_PHRASES = [
    "first status-only job should run --refresh-promoted-review",
    "first status-only job should run --refresh-defensive-research",
    "scheduling_approved=True",
    "execution_approved=True",
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
    print(f"Hermes cron job design checks: {len(checks)}")
    print(f"Pass: {sum(check.status == 'pass' for check in checks)}, warning: {sum(check.status == 'warning' for check in checks)}, error: {len(errors)}")
    print("scheduling_approved=False")
    print("execution_approved=False")
    print("Warning: this verifier checks design only and does not create Hermes cron, Task Scheduler, services, loop mode, or execution.")
    return 1 if errors else 0


def build_checks() -> list[CheckResult]:
    design_text = read_text(DESIGN_PATH)
    docs_text = "\n".join(read_text(path) for path in DOC_PATHS)
    docs_lower = docs_text.lower()

    from trading_bot.safety.monitor_lockfile import LOCK_WRAPPED_COMMAND_NAMES  # noqa: PLC0415

    return [
        design_doc_exists_check(design_text),
        required_design_phrases_check(design_text),
        first_job_status_only_check(design_text),
        first_job_excludes_refresh_check(design_text),
        execution_boundary_check(docs_lower),
        secret_boundary_check(docs_lower),
        no_scheduler_artifacts_check(docs_text),
        lock_wrapped_set_check(set(LOCK_WRAPPED_COMMAND_NAMES)),
        docs_reference_design_check(docs_text),
    ]


def design_doc_exists_check(design_text: str) -> CheckResult:
    return CheckResult(
        "hermes_cron_job_design_doc_exists",
        "pass" if DESIGN_PATH.exists() and design_text else "error",
        str(DESIGN_PATH),
    )


def required_design_phrases_check(design_text: str) -> CheckResult:
    normalized_design = normalize_text(design_text)
    missing = [phrase for phrase in REQUIRED_DESIGN_PHRASES if normalize_text(phrase) not in normalized_design]
    return CheckResult(
        "required_status_only_design_phrases",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def first_job_status_only_check(design_text: str) -> CheckResult:
    required = [
        "status-only",
        "scripts\\verify_repo_safety.py",
        "scripts\\verify_hermes_cron_readiness.py",
        "bot.py --vps-daily-monitoring-summary",
        "healthy_monitoring_state",
    ]
    missing = [phrase for phrase in required if phrase not in design_text]
    return CheckResult(
        "first_job_is_status_only_checkpoint",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def first_job_excludes_refresh_check(design_text: str) -> CheckResult:
    forbidden_found = [phrase for phrase in FORBIDDEN_FIRST_JOB_APPROVAL_PHRASES if phrase in design_text]
    required = [
        "does not run `--refresh-promoted-review`",
        "--refresh-promoted-review",
        "does not run `--refresh-defensive-research`",
        "--refresh-defensive-research",
        "Refresh cron jobs require a later separate review",
    ]
    missing = [phrase for phrase in required if phrase not in design_text]
    return CheckResult(
        "first_job_excludes_refresh_until_later_review",
        "pass" if not forbidden_found and not missing else "error",
        f"forbidden={', '.join(forbidden_found) if forbidden_found else 'none'}; missing={', '.join(missing) if missing else 'none'}",
    )


def execution_boundary_check(docs_lower: str) -> CheckResult:
    required = [
        "normal bot run",
        "paper-order smoke test",
        "slow-sma paper execution",
        "future order-capable command",
        "submits, cancels, or creates orders",
        "mutates positions",
        "writes sqlite `trade_log`",
        "sends trade alerts",
        "changes config defaults",
    ]
    missing = [phrase for phrase in required if phrase not in docs_lower]
    return CheckResult(
        "execution_capable_commands_excluded",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def secret_boundary_check(docs_lower: str) -> CheckResult:
    required = [
        "config contents",
        "api keys",
        "webhooks",
        "account ids",
        ".env",
        "logs",
        "sqlite databases",
        "generated csv/chart contents",
    ]
    missing = [phrase for phrase in required if phrase not in docs_lower]
    return CheckResult(
        "config_secret_generated_content_boundary",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
    )


def no_scheduler_artifacts_check(docs_text: str) -> CheckResult:
    found_tokens = [token for token in FORBIDDEN_SCHEDULER_ARTIFACT_TOKENS if token in docs_text]
    tracked_files = git_lines(["ls-files"])
    scheduler_files = [
        path
        for path in tracked_files
        if path.endswith((".service", ".timer", ".cron", ".task.xml"))
        or path.lower() in {"crontab", "schedule.ps1"}
    ]
    problems = found_tokens + scheduler_files
    return CheckResult(
        "no_scheduler_service_cron_artifacts_created",
        "pass" if not problems else "error",
        "problems=" + (", ".join(problems) if problems else "none"),
    )


def lock_wrapped_set_check(actual: set[str]) -> CheckResult:
    return CheckResult(
        "lock_wrapped_command_set_unchanged",
        "pass" if actual == LOCK_WRAPPED_REQUIRED else "error",
        f"lock_wrapped={', '.join(sorted(actual))}",
    )


def docs_reference_design_check(docs_text: str) -> CheckResult:
    required = [
        "docs/HERMES_CRON_JOB_DESIGN.md",
        "python scripts\\verify_hermes_cron_job_design.py",
    ]
    missing = [phrase for phrase in required if phrase not in docs_text]
    return CheckResult(
        "design_doc_and_verifier_referenced",
        "pass" if not missing else "error",
        "missing=" + (", ".join(missing) if missing else "none"),
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
