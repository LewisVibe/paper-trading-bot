from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = ROOT / "docs" / "HERMES_PAUSED_STATUS_CRON_CHECKPOINT.md"

REQUIRED_PHRASES = [
    "paused-vps-safe-paper-bot-status-check",
    "66c8a5bb438e",
    "State: `scheduled`",
    "Enabled: `true`",
    "Schedule: `*/30 14-20 * * 1-5`",
    "Intended timezone: UK local / Europe-London",
    "Next run: `2026-06-29T14:00:00+01:00`",
    "Last run status: `null` / never run by cron",
    "Delivery: current/origin Telegram chat",
    "Toolsets restricted to: `terminal`",
    "Mode: script-only / no-agent",
    "Script: `vps_safe_paper_bot_status_check.py`",
    "Working directory: `C:\\dev\\paper-trading-bot`",
    ".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py",
    ".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py",
    ".venv\\Scripts\\python.exe scripts\\verify_vps_daily_monitoring_summary.py",
    ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    "VPS daily monitoring summary includes the active volatility seed readiness section",
    "Manual One-Off Test Result",
    "On `2026-06-27`, the status command sequence was run once manually as a",
    "the existing job was then enabled without being manually triggered",
    "state `scheduled`, enabled `true`, next run `2026-06-29T14:00:00+01:00`",
    "repo safety: passed",
    "Hermes cron readiness: `9` checks passed, `0` warnings, `0` errors",
    "VPS daily monitoring summary verifier: passed",
    "VPS daily monitoring final status: `monitoring_stale_or_missing_inputs`",
    "VPS daily monitoring action required: `manual_review_required`",
    "vol_targeted_growth_active_seed_monitoring_incomplete_manual_review_required",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` / `MULTI_SLEEVE",
    "previous seed context: `qqq_100_trend_gate` / `QQQ`",
    "no order-capable commands were run",
    "not permission to add refresh, broker-read, or order-capable scheduling",
    "`execution_approved=False`",
    "`paper_execution_approved=False`",
    "`scheduling_approved=False` for strategy execution, refresh jobs, and",
    "`live_trading_approved=False`",
    "`followup_order_approved=False`",
    "`repeat_execution_approved=False`",
    "This enabled status cron is approval for this status/report monitoring job only",
]

FORBIDDEN_APPROVAL_PHRASES = [
    "scheduling_approved=True",
    "execution_approved=True",
    "paper_execution_approved=True",
    "live_trading_approved=True",
    "followup_order_approved=True",
    "repeat_execution_approved=True",
    "execution approved",
    "order approved",
    "paper execution approved",
]

FORBIDDEN_COMMANDS = [
    "python bot.py",
    "--paper-order-test",
    "--execute-qqq100-paper",
    "--execute-slow-sma-paper",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
    "scripts\\verify_vol_targeted_growth_active_seed_readiness.py",
    "--paper-live-monitoring-status",
    "--paper-live-promotion-ladder-status",
    "--paper-live-checklist-status",
    "--vol-targeted-growth-active-seed-readiness",
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
    verify_checkpoint_doc(failures)
    verify_no_scheduler_artifacts(failures)
    if failures:
        print("Hermes status cron checkpoint verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Hermes status cron checkpoint verification passed.")
    print("Verified enabled status-only cron boundary, command sequence, and false execution approval flags.")
    return 0


def verify_checkpoint_doc(failures: list[str]) -> None:
    text = read_text(CHECKPOINT_PATH)
    normalized = normalize_text(text)
    lowered = normalized.lower()
    if not CHECKPOINT_PATH.exists() or not text:
        failures.append("Hermes status cron checkpoint doc is missing")
        return
    for phrase in REQUIRED_PHRASES:
        if normalize_text(phrase) not in normalized:
            failures.append(f"missing required phrase: {phrase}")
    for phrase in FORBIDDEN_APPROVAL_PHRASES:
        if phrase.lower() in lowered:
            failures.append(f"forbidden approval phrase present: {phrase}")

    sequence = command_sequence(text)
    for command in FORBIDDEN_COMMANDS:
        if command in sequence:
            failures.append(f"forbidden command in status-only sequence: {command}")


def verify_no_scheduler_artifacts(failures: list[str]) -> None:
    docs_text = read_text(CHECKPOINT_PATH)
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
