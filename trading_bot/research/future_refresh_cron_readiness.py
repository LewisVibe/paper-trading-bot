"""Future safe refresh-cron readiness pack.

This is static/docs/report-only scaffolding. It does not create, edit, trigger,
delete, enable, or schedule any cron job.
"""

from __future__ import annotations

import csv
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("data/future_refresh_cron_readiness_pack.csv")

FINAL_NOT_READY = "future_refresh_cron_review_not_ready"
FINAL_MANUAL_REVIEW = "future_refresh_cron_review_needs_manual_review"
FINAL_READY = "future_refresh_cron_design_ready_for_manual_review"

CANDIDATE_SEQUENCE = [
    (".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py", "verifier_only", "not_applicable"),
    (".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py", "verifier_only", "not_applicable"),
    (".venv\\Scripts\\python.exe bot.py --monitor-lockfile-readiness-report", "report_only", "lock_wrapped"),
    (".venv\\Scripts\\python.exe bot.py --refresh-defensive-research", "report_only", "lock_wrapped"),
    (".venv\\Scripts\\python.exe bot.py --project-research-state-quality-report", "saved_data_only", "manual_review_required"),
    (".venv\\Scripts\\python.exe bot.py --stock-etf-paper-execution-readiness-report", "saved_data_only", "manual_review_required"),
    (".venv\\Scripts\\python.exe bot.py --alpaca-paper-readiness-report", "saved_data_only", "manual_review_required"),
    (".venv\\Scripts\\python.exe bot.py --paper-order-smoke-test-readiness-pack", "saved_data_only", "manual_review_required"),
    (".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary", "display_only", "manual_review_required"),
]

FORBIDDEN_CANDIDATE_TOKENS = [
    "--confirm-readonly-alpaca-check",
    "--paper-order-test",
    "--execute-slow-sma-paper",
    "--confirm-paper-order",
    "--confirm-slow-sma-paper",
    "python bot.py",
    "git pull",
    "git commit",
    "git push",
]

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "command_name",
    "safety_category",
    "lock_status",
    "evidence_source",
    "details",
    "blocker",
    "recommended_next_step",
    "cron_created",
    "cron_enabled",
    "scheduling_approved",
    "execution_approved",
    "order_execution_approved",
    "future_refresh_cron_review_status",
]


@dataclass
class FutureRefreshCronReadinessResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_future_refresh_cron_readiness_pack(root_dir: Path | str = ".") -> FutureRefreshCronReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows(root, created_at)
    final_status = choose_final_status(rows)
    rows.append(
        report_row(
            created_at,
            "final_future_refresh_cron_review_status",
            final_status,
            "blocked" if final_status == FINAL_NOT_READY else ("warning" if final_status == FINAL_MANUAL_REVIEW else "info"),
            "",
            "summary",
            "mixed",
            "readiness rows",
            final_details(final_status, rows),
            final_status == FINAL_NOT_READY,
            final_next_step(final_status),
            final_status,
        )
    )
    output_path = root / OUTPUT_PATH
    write_rows(output_path, rows)
    return FutureRefreshCronReadinessResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows),
    )


def build_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    docs_text = "\n".join(
        read_text(root / path)
        for path in [
            Path("docs/HERMES_CRON_JOB_DESIGN.md"),
            Path("docs/HERMES_CRON_MONITORING_RUNBOOK.md"),
            Path("docs/HERMES_TASK_BOARD.md"),
            Path("docs/CURRENT_STATE.md"),
            Path("docs/HERMES_WORKFLOW.md"),
            Path("docs/VPS_SETUP_CHECKLIST.md"),
        ]
    )
    rows = [
        existing_status_cron_boundary_row(created_at, docs_text),
        no_refresh_or_execution_cron_row(created_at, docs_text),
        generated_output_ignore_row(created_at, root),
        secrets_boundary_row(created_at, docs_text),
        stale_lock_policy_row(created_at, docs_text),
    ]
    rows.extend(candidate_rows(created_at))
    rows.extend(candidate_exclusion_rows(created_at))
    return rows


def existing_status_cron_boundary_row(created_at: str, docs_text: str) -> dict[str, Any]:
    required = [
        "paper-bot-vps-status-check",
        "345188fbb60c",
        "10 10 * * *",
        "10:10am UK local time",
        "Telegram",
        "script-only / no-agent",
        "C:\\dev\\paper-trading-bot",
        ".venv\\Scripts\\python.exe scripts\\verify_repo_safety.py",
        ".venv\\Scripts\\python.exe scripts\\verify_hermes_cron_readiness.py",
        ".venv\\Scripts\\python.exe bot.py --vps-daily-monitoring-summary",
    ]
    missing = [phrase for phrase in required if phrase not in docs_text]
    return report_row(
        created_at,
        "existing_status_cron_boundary",
        "pass" if not missing else "blocked_status_cron_docs_incomplete",
        "info" if not missing else "blocked",
        "",
        "status_cron",
        "not_applicable",
        "Hermes docs",
        "Current single status cron docs checked. missing=" + (", ".join(missing) if missing else "none"),
        bool(missing),
        "fix_current_status_cron_docs_before_refresh_review" if missing else "none",
        FINAL_MANUAL_REVIEW,
    )


def no_refresh_or_execution_cron_row(created_at: str, docs_text: str) -> dict[str, Any]:
    required = ["No refresh cron", "No execution scheduling", "does not create a refresh cron"]
    ok = any("No refresh cron" in docs_text or "No refresh cron job is currently created" in docs_text for _ in [0])
    ok = ok and ("No execution scheduling" in docs_text or "does not approve execution" in docs_text)
    return report_row(
        created_at,
        "no_refresh_or_execution_cron_created",
        "pass" if ok else "manual_review_required_cron_boundary",
        "info" if ok else "warning",
        "",
        "status_cron",
        "not_applicable",
        "Hermes docs",
        "Docs must preserve no refresh cron and no execution scheduling boundaries.",
        False,
        "review_cron_boundary_docs_before_any_manual_scheduling_review",
        FINAL_MANUAL_REVIEW,
    )


def generated_output_ignore_row(created_at: str, root: Path) -> dict[str, Any]:
    ignored = git_check_ignore(root, "data/future_refresh_cron_readiness_pack.csv")
    return report_row(
        created_at,
        "generated_outputs_ignored",
        "pass" if ignored else "blocked_generated_output_not_ignored",
        "info" if ignored else "blocked",
        "",
        "verifier_only",
        "not_applicable",
        "git check-ignore",
        "Generated report output should remain ignored by git.",
        not ignored,
        "update_ignore_rules_before_any_refresh_cron_review" if not ignored else "none",
        FINAL_MANUAL_REVIEW,
    )


def secrets_boundary_row(created_at: str, docs_text: str) -> dict[str, Any]:
    required = ["config contents", "secrets", "logs", "databases", "API keys"]
    missing = [phrase for phrase in required if phrase not in docs_text]
    return report_row(
        created_at,
        "secret_config_generated_content_boundary",
        "pass" if not missing else "manual_review_required_secret_boundary",
        "info" if not missing else "warning",
        "",
        "policy",
        "not_applicable",
        "docs",
        "Candidate review must not inspect or print config, secrets, logs, databases, or full generated outputs. missing=" + (", ".join(missing) if missing else "none"),
        False,
        "review_secret_boundary_docs",
        FINAL_MANUAL_REVIEW,
    )


def stale_lock_policy_row(created_at: str, docs_text: str) -> dict[str, Any]:
    ok = "stale lock" in docs_text.lower() and "manual review" in docs_text.lower()
    return report_row(
        created_at,
        "stale_lock_requires_manual_review",
        "pass" if ok else "manual_review_required_stale_lock_policy",
        "info" if ok else "warning",
        "",
        "policy",
        "not_applicable",
        "lockfile docs",
        "Stale lock policy must require manual review. Lockfile protection is overlap control only.",
        False,
        "review_lockfile_policy_before_refresh_scheduling",
        FINAL_MANUAL_REVIEW,
    )


def candidate_rows(created_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for command, category, lock_status in CANDIDATE_SEQUENCE:
        manual_review = lock_status == "manual_review_required"
        rows.append(
            report_row(
                created_at,
                "candidate_future_refresh_command",
                "manual_review_required" if manual_review else "candidate_listed",
                "warning" if manual_review else "info",
                command,
                category,
                lock_status,
                "fixed future design candidate",
                "Design-only candidate command. Not scheduled, enabled, or approved.",
                False,
                "manual_review_lock_and_scheduling_boundary" if manual_review else "none",
                FINAL_MANUAL_REVIEW,
            )
        )
    return rows


def candidate_exclusion_rows(created_at: str) -> list[dict[str, Any]]:
    candidate_text = "\n".join(command for command, _category, _lock in CANDIDATE_SEQUENCE)
    checks = {
        "no_confirmed_readonly_alpaca": "--confirm-readonly-alpaca-check" not in candidate_text,
        "no_paper_order_test": "--paper-order-test" not in candidate_text,
        "no_slow_sma_execution": "--execute-slow-sma-paper" not in candidate_text,
        "no_normal_bot_path": "\npython bot.py\n" not in f"\n{candidate_text}\n",
        "no_git_mutation": all(token not in candidate_text for token in ["git pull", "git commit", "git push"]),
    }
    rows = []
    for name, passed in checks.items():
        rows.append(
            report_row(
                created_at,
                name,
                "pass" if passed else "blocked_forbidden_candidate_command",
                "info" if passed else "blocked",
                "",
                "policy",
                "not_applicable",
                "candidate command list",
                f"{name}={passed}",
                not passed,
                "remove_forbidden_command_from_future_refresh_candidate" if not passed else "none",
                FINAL_MANUAL_REVIEW,
            )
        )
    return rows


def report_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    command_name: str,
    safety_category: str,
    lock_status: str,
    evidence_source: str,
    details: str,
    blocker: bool,
    recommended_next_step: str,
    future_refresh_cron_review_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "command_name": command_name,
        "safety_category": safety_category,
        "lock_status": lock_status,
        "evidence_source": evidence_source,
        "details": details,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        "cron_created": False,
        "cron_enabled": False,
        "scheduling_approved": False,
        "execution_approved": False,
        "order_execution_approved": False,
        "future_refresh_cron_review_status": future_refresh_cron_review_status,
    }


def choose_final_status(rows: list[dict[str, Any]]) -> str:
    if any(str(row.get("severity")) == "blocked" or truthy(row.get("blocker")) for row in rows):
        return FINAL_NOT_READY
    if any(str(row.get("severity")) == "warning" for row in rows):
        return FINAL_MANUAL_REVIEW
    return FINAL_READY


def final_details(final_status: str, rows: list[dict[str, Any]]) -> str:
    blockers = [row for row in rows if row.get("severity") == "blocked" or truthy(row.get("blocker"))]
    manual = [row for row in rows if row.get("severity") == "warning"]
    key = blockers[:5] if blockers else manual[:5]
    key_names = ", ".join(str(row.get("check_name")) for row in key) or "none"
    return f"final_status={final_status}; blocker_count={len(blockers)}; manual_review_count={len(manual)}; key_items={key_names}."


def final_next_step(final_status: str) -> str:
    if final_status == FINAL_NOT_READY:
        return "resolve_blockers_before_future_refresh_cron_review"
    if final_status == FINAL_MANUAL_REVIEW:
        return "manual_review_candidate_sequence_locking_and_output_destination_tomorrow"
    return "ready_for_separate_manual_scheduling_review_not_approval"


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    final = next((row for row in rows if row.get("check_name") == "final_future_refresh_cron_review_status"), {})
    manual_rows = [row for row in rows if row.get("severity") == "warning"]
    blocked_rows = [row for row in rows if row.get("severity") == "blocked" or truthy(row.get("blocker"))]
    key_rows = blocked_rows[:5] if blocked_rows else manual_rows[:5]
    key_names = ", ".join(str(row.get("check_name")) for row in key_rows) or "none"
    candidate_count = sum(1 for row in rows if row.get("check_name") == "candidate_future_refresh_command")
    return [
        "Future refresh cron readiness pack complete. Report-only; no cron created or approved.",
        f"final_future_refresh_cron_review_status: {final.get('check_status', 'unavailable')}",
        f"candidate_command_count: {candidate_count}",
        f"blocked_or_manual_review_command_count: {len(blocked_rows) + len(manual_rows)}",
        f"key_blockers_or_manual_review_items: {key_names}",
        f"recommended_next_step: {final.get('recommended_next_step', 'unavailable')}",
        "cron_created=false",
        "cron_enabled=false",
        "scheduling_approved=false",
        "execution_approved=false",
        "order_execution_approved=false",
        f"Saved readiness pack to {output_path}",
        "Warning: this summary does not print high-risk paper-order execution commands.",
    ]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def git_check_ignore(root: Path, path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", path],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.returncode == 0


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
