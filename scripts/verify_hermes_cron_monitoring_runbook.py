from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = ROOT / "docs" / "HERMES_CRON_MONITORING_RUNBOOK.md"

REQUIRED_PHRASES = [
    "paper-bot-vps-status-check",
    "345188fbb60c",
    "healthy_monitoring_state",
    "action_required",
    "no_action_required",
    "monitoring_warning",
    "monitoring_stale_or_missing_inputs",
    "repo_safety: FAIL",
    "hermes_cron_readiness: FAIL",
    "vps_daily_monitoring_summary: FAIL",
    ".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py",
    ".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py",
    ".venv\\Scripts\\python.exe scripts\\verify_hermes_promoted_review_refresh_cron_design.py",
    ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    ".venv\\Scripts\\python.exe bot.py --vps-monitoring-status",
    ".venv\\Scripts\\python.exe bot.py --refresh-promoted-review",
    "future/manual diagnostic only",
    "Manual refresh is not cron creation.",
    "Manual refresh is not execution approval.",
    "generated monitoring outputs only",
    "lock issue means stop and manual review",
    "execution_approved=false",
    "scheduling_approved=false",
    "does not approve execution",
    "does not approve creating the second cron",
    "does not approve live trading",
    "Do not print or inspect secrets, config contents, logs, databases",
    "Do not schedule execution-capable commands.",
]

FORBIDDEN_APPROVAL_PHRASES = [
    "execution_approved=true",
    "scheduling_approved=true",
    "create the second cron now",
    ".venv\\Scripts\\python.exe bot.py --show-current-research-state",
]


def main() -> int:
    failures: list[str] = []
    verify_runbook(failures)
    if failures:
        print("Hermes cron monitoring runbook verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Hermes cron monitoring runbook verification passed.")
    print("Verified status interpretation, safe manual checks, false approval flags, and no execution/scheduling approval.")
    return 0


def verify_runbook(failures: list[str]) -> None:
    text = read_text(RUNBOOK_PATH)
    normalized = normalize_text(text)
    if not RUNBOOK_PATH.exists() or not text:
        failures.append("Runbook doc is missing")
        return
    for phrase in REQUIRED_PHRASES:
        if normalize_text(phrase) not in normalized:
            failures.append(f"Runbook missing required phrase: {phrase}")
    lowered = normalized.lower()
    for phrase in FORBIDDEN_APPROVAL_PHRASES:
        if phrase.lower() in lowered:
            failures.append(f"Runbook contains forbidden approval phrase: {phrase}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def normalize_text(text: str) -> str:
    return " ".join(text.split())


if __name__ == "__main__":
    raise SystemExit(main())
