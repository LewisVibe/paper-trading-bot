"""Concise daily VPS monitoring summary."""

from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

from trading_bot.research.monitoring_freshness import (
    build_freshness_statuses,
    format_freshness_lines,
    has_stale_or_missing,
    has_warning,
)
from trading_bot.research.vps_monitoring_status import (
    DEFENSIVE_SAVED_INPUTS,
    GENERATED_OUTPUT_PATHS,
    HIGH_RISK_BOUNDARY_LINES,
    LOCK_WRAPPED_COMMANDS,
    PROMOTED_DECISION_PREVIEW_PATH,
    PROMOTED_REVIEW_SUMMARY_PATH,
    all_false,
    format_counts,
    read_csv_rows,
)


DEFENSIVE_REFRESH_SUMMARY_PATH = "data/defensive_research_refresh_summary.csv"


def build_vps_daily_monitoring_summary_lines(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    freshness_statuses = build_freshness_statuses(root_path)
    decision_rows = read_csv_rows(root_path / PROMOTED_DECISION_PREVIEW_PATH)
    promoted_decision_counts = Counter(row.get("decision_state", "") or "blank" for row in decision_rows)
    decisions_execution_false = all_false(decision_rows, "execution_approved")
    defensive_rows = read_csv_rows(root_path / DEFENSIVE_REFRESH_SUMMARY_PATH)
    defensive_counts = Counter(row.get("status", "") or "blank" for row in defensive_rows)
    final_status = determine_final_status(
        freshness_statuses,
        decision_rows_present=bool(decision_rows),
        decisions_execution_false=decisions_execution_false,
    )
    action = classify_action_required(
        freshness_statuses,
        decision_rows_present=bool(decision_rows),
        decisions_execution_false=decisions_execution_false,
    )

    lines = [
        "VPS DAILY MONITORING SUMMARY. REPORT ONLY. NOT EXECUTION.",
        "execution_approved=False",
        "scheduling_approved=False",
        "",
        "Safety reminders:",
        f"- config_presence_only: {(root_path / 'config.json').exists()}; contents were not read.",
        f"- generated_outputs_ignored_untracked: {generated_outputs_ignored(root_path)}",
        "- missing or stale saved outputs are prerequisite/status issues, not trading approval.",
        "",
        "Lock-wrapped safe commands:",
    ]
    for command in LOCK_WRAPPED_COMMANDS:
        lines.append(f"- {command}")

    lines.extend(
        [
            "",
            "Promoted review summary:",
            f"- promoted_review_summary_present: {(root_path / PROMOTED_REVIEW_SUMMARY_PATH).exists()}",
            f"- promoted_decision_preview_present: {(root_path / PROMOTED_DECISION_PREVIEW_PATH).exists()}",
            f"- promoted_decision_state_counts: {format_counts(promoted_decision_counts)}",
            f"- promoted_decisions_execution_approved_false_for_all_rows: {decisions_execution_false}",
            "",
            "Defensive refresh summary:",
            f"- defensive_saved_inputs_present: {defensive_saved_inputs_present(root_path)}",
            f"- defensive_refresh_summary_present: {(root_path / DEFENSIVE_REFRESH_SUMMARY_PATH).exists()}",
            f"- defensive_refresh_step_counts: {format_counts(defensive_counts)}",
            "",
            "Saved-output freshness:",
        ]
    )
    lines.extend(format_freshness_lines(freshness_statuses))
    lines.extend(
        [
            "",
            "High-risk/manual-only boundaries:",
        ]
    )
    for boundary in HIGH_RISK_BOUNDARY_LINES:
        lines.append(f"- {boundary}")
    lines.extend(
        [
            "",
            f"final_status: {final_status}",
            f"action_required: {action['action_required']}",
            f"action_reason: {action['action_reason']}",
            f"suggested_manual_action: {action['suggested_manual_action']}",
            "Warning: this daily summary does not call Alpaca, yfinance, Discord, SQLite trade_log, or read config.json contents.",
        ]
    )
    return lines


def determine_final_status(
    freshness_statuses: list,
    decision_rows_present: bool,
    decisions_execution_false: bool,
) -> str:
    if has_stale_or_missing(freshness_statuses) or not decision_rows_present:
        return "monitoring_stale_or_missing_inputs"
    if has_warning(freshness_statuses) or not decisions_execution_false:
        return "monitoring_warning"
    return "healthy_monitoring_state"


def classify_action_required(
    freshness_statuses: list,
    decision_rows_present: bool,
    decisions_execution_false: bool,
) -> dict[str, str]:
    if has_stale_or_missing(freshness_statuses) or not decision_rows_present:
        return {
            "action_required": "manual_review_required",
            "action_reason": "one_or_more_saved_report_inputs_stale_or_missing",
            "suggested_manual_action": "refresh_or_investigate_saved_monitoring_inputs",
        }
    if has_warning(freshness_statuses) or not decisions_execution_false:
        reason = (
            "one_or_more_saved_report_inputs_warning_stale"
            if has_warning(freshness_statuses)
            else "one_or_more_saved_report_approval_flags_need_review"
        )
        return {
            "action_required": "refresh_stale_safe_reports",
            "action_reason": reason,
            "suggested_manual_action": "manually_run_safe_refresh_reports",
        }
    return {
        "action_required": "no_action_required",
        "action_reason": "all_status_inputs_fresh_or_acceptable",
        "suggested_manual_action": "none",
    }


def defensive_saved_inputs_present(root: Path) -> bool:
    return all((root / path).exists() for path in DEFENSIVE_SAVED_INPUTS)


def generated_outputs_ignored(root: Path) -> bool:
    return all(is_git_ignored(root, path) and not is_git_tracked(root, path) for path in GENERATED_OUTPUT_PATHS)


def is_git_ignored(root: Path, path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def is_git_tracked(root: Path, path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def print_vps_daily_monitoring_summary(root: Path | str = ".") -> int:
    for line in build_vps_daily_monitoring_summary_lines(root):
        print(line)
    return 0
