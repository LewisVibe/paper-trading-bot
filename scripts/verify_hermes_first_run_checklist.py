from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST_PATH = ROOT / "docs" / "HERMES_FIRST_RUN_CHECKLIST.md"

REQUIRED_PHRASES = [
    "paused-vps-safe-paper-bot-status-check",
    "66c8a5bb438e",
    "State expected before first run: `scheduled`",
    "Enabled expected before first run: `true`",
    "Schedule: `*/30 14-20 * * 1-5`",
    "First expected scheduled run: `2026-06-29T14:00:00+01:00`",
    "Toolsets restricted to: `terminal`",
    "Mode: script-only / no-agent",
    "Working directory: `C:\\dev\\paper-trading-bot`",
    ".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py",
    ".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py",
    ".venv\\Scripts\\python.exe scripts\\verify_vps_daily_monitoring_summary.py",
    ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    "The job should stop on verifier failure",
    "Healthy First-Run Result",
    "Warning Result",
    "Failure / Stop Conditions",
    "Stop and disable the job for manual review",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` / `MULTI_SLEEVE",
    "`qqq_100_trend_gate` / `QQQ`",
    "`monitoring_stale_or_missing_inputs`",
    "`execution_approved=False`",
    "`paper_execution_approved=False`",
    "`scheduling_approved=False` for strategy execution, refresh jobs, and",
    "`live_trading_approved=False`",
    "`followup_order_approved=False`",
    "`repeat_execution_approved=False`",
    "not approval for refresh automation, broker reads, trading",
    "First-Run Result Log Template",
]

FORBIDDEN_APPROVAL_PHRASES = [
    "execution_approved=True",
    "paper_execution_approved=True",
    "scheduling_approved=True",
    "live_trading_approved=True",
    "followup_order_approved=True",
    "repeat_execution_approved=True",
    "execution approved",
    "paper execution approved",
    "orders approved",
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
        print("Hermes first-run checklist verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Hermes first-run checklist verification passed.")
    print("Verified first scheduled-run expectations, stop conditions, and false execution approval flags.")
    return 0


def verify_checklist_doc(failures: list[str]) -> None:
    text = read_text(CHECKLIST_PATH)
    normalized = normalize_text(text)
    lowered = normalized.lower()
    if not CHECKLIST_PATH.exists() or not text:
        failures.append("Hermes first-run checklist is missing")
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
