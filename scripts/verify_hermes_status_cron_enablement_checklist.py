from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST_PATH = ROOT / "docs" / "HERMES_STATUS_CRON_ENABLEMENT_CHECKLIST.md"

REQUIRED_PHRASES = [
    "paused-vps-safe-paper-bot-status-check",
    "66c8a5bb438e",
    "Current state: `paused`",
    "Enabled: `false`",
    "Placeholder schedule: once at `2099-01-01 00:00`",
    "Last scheduled run: `never`",
    "Toolsets restricted to: `terminal`",
    "Working directory: `C:\\dev\\paper-trading-bot`",
    ".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py",
    ".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py",
    ".venv\\Scripts\\python.exe scripts\\verify_vps_daily_monitoring_summary.py",
    ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    "hourly during the US regular market session",
    "every 30 minutes during the US regular market session",
    "only after several successful hourly runs",
    "09:30-16:00 America/New_York",
    "14:30-21:00 UK local time",
    "DST mismatch weeks must be reviewed manually",
    "`execution_approved=False`",
    "`paper_execution_approved=False`",
    "`scheduling_approved=False`",
    "`live_trading_approved=False`",
    "`followup_order_approved=False`",
    "`repeat_execution_approved=False`",
    "not create, edit, trigger, enable, or schedule any Hermes cron job",
    "not approved by this document",
    "This checklist is not the approval itself",
]

FORBIDDEN_APPROVAL_PHRASES = [
    "Enabled: `true`",
    "Current state: `active`",
    "scheduling_approved=True",
    "execution_approved=True",
    "paper_execution_approved=True",
    "live_trading_approved=True",
    "followup_order_approved=True",
    "repeat_execution_approved=True",
    "activation approved",
    "scheduling approved",
    "enable now",
    "approved cadence",
]

FORBIDDEN_SEQUENCE_TOKENS = [
    "--paper-order-test",
    "--execute-qqq100-paper",
    "--execute-slow-sma-paper",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
    "--refresh-market-monitor",
    "--market-monitor-snapshot",
    "--vol-targeted-growth-broker-position-comparison",
    "--confirm-readonly-alpaca-check",
    "git pull",
    "git push",
    "git commit",
]

FORBIDDEN_SCHEDULER_ARTIFACT_TOKENS = [
    "schtasks /create",
    "Register-ScheduledTask",
    "crontab -e",
    "systemctl enable",
    "New-Service",
]


def main() -> int:
    failures: list[str] = []
    verify_checklist_doc(failures)
    verify_no_scheduler_artifacts(failures)
    if failures:
        print("Hermes status cron enablement checklist verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Hermes status cron enablement checklist verification passed.")
    print("Verified market-hours cadence planning, paused job boundary, and false approval flags.")
    return 0


def verify_checklist_doc(failures: list[str]) -> None:
    text = read_text(CHECKLIST_PATH)
    normalized = normalize_text(text)
    lowered = normalized.lower()
    if not CHECKLIST_PATH.exists() or not text:
        failures.append("Hermes status cron enablement checklist is missing")
        return
    for phrase in REQUIRED_PHRASES:
        if normalize_text(phrase) not in normalized:
            failures.append(f"missing required phrase: {phrase}")
    for phrase in FORBIDDEN_APPROVAL_PHRASES:
        if phrase.lower() in lowered:
            failures.append(f"forbidden approval phrase present: {phrase}")

    sequence = command_sequence(text)
    for token in FORBIDDEN_SEQUENCE_TOKENS:
        if token in sequence:
            failures.append(f"forbidden token in status-only sequence: {token}")


def verify_no_scheduler_artifacts(failures: list[str]) -> None:
    docs_text = read_text(CHECKLIST_PATH)
    found_tokens = [token for token in FORBIDDEN_SCHEDULER_ARTIFACT_TOKENS if token in docs_text]
    tracked_files = git_lines(["ls-files"])
    scheduler_files = [
        path
        for path in tracked_files
        if path.endswith((".service", ".timer", ".cron", ".task.xml"))
        or path.lower() in {"crontab", "schedule.ps1"}
    ]
    for problem in found_tokens + scheduler_files:
        failures.append(f"scheduler artifact or command found: {problem}")


def command_sequence(text: str) -> str:
    marker = "```powershell"
    start = text.find(marker)
    if start < 0:
        return ""
    start += len(marker)
    end = text.find("```", start)
    return text[start:end] if end >= 0 else text[start:]


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
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
