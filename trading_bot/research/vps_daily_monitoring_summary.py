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
    QQQ100_DAILY_DECISION_SUMMARY_PATH,
    all_false,
    build_paper_live_monitoring_context,
    format_counts,
    paper_live_monitoring_status_lines,
    qqq100_daily_decision_status_lines,
    qqq100_manual_flatten_readiness_status_lines,
    qqq100_manual_flatten_runbook_status_lines,
    read_csv_rows,
)


DEFENSIVE_REFRESH_SUMMARY_PATH = "data/defensive_research_refresh_summary.csv"
VOL_ACTIVE_SEED_READINESS_SUMMARY_PATH = "data/vol_targeted_growth_active_seed_readiness_summary.csv"


def build_vps_daily_monitoring_summary_lines(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    freshness_statuses = build_freshness_statuses(root_path)
    decision_rows = read_csv_rows(root_path / PROMOTED_DECISION_PREVIEW_PATH)
    promoted_decision_counts = Counter(row.get("decision_state", "") or "blank" for row in decision_rows)
    decisions_execution_false = all_false(decision_rows, "execution_approved")
    defensive_rows = read_csv_rows(root_path / DEFENSIVE_REFRESH_SUMMARY_PATH)
    defensive_counts = Counter(row.get("status", "") or "blank" for row in defensive_rows)
    paper_live_context = build_paper_live_monitoring_context(root_path)
    daily_decision_rows = read_csv_rows(root_path / QQQ100_DAILY_DECISION_SUMMARY_PATH)
    daily_decision_approvals_false = all_false(daily_decision_rows, "execution_approved")
    final_status = determine_final_status(
        freshness_statuses,
        decision_rows_present=bool(decision_rows),
        decisions_execution_false=decisions_execution_false,
        paper_live_monitoring_consistent=paper_live_context.consistent,
        daily_decision_present=bool(daily_decision_rows),
        daily_decision_approvals_false=daily_decision_approvals_false,
    )
    action = classify_action_required(
        freshness_statuses,
        decision_rows_present=bool(decision_rows),
        decisions_execution_false=decisions_execution_false,
        paper_live_monitoring_consistent=paper_live_context.consistent,
        daily_decision_present=bool(daily_decision_rows),
        daily_decision_approvals_false=daily_decision_approvals_false,
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
            "Paper-live monitoring status:",
        ]
    )
    lines.extend(paper_live_monitoring_status_lines(root_path))
    lines.extend(
        [
            "",
            "Volatility active-seed readiness:",
        ]
    )
    lines.extend(vol_active_seed_readiness_status_lines(root_path))
    lines.extend(
        [
            "",
            "QQQ100 daily decision:",
        ]
    )
    lines.extend(qqq100_daily_decision_status_lines(root_path))
    lines.extend(
        [
            "",
            "QQQ100 manual flatten readiness:",
        ]
    )
    lines.extend(qqq100_manual_flatten_readiness_status_lines(root_path))
    lines.extend(
        [
            "",
            "QQQ100 manual flatten runbook:",
        ]
    )
    lines.extend(qqq100_manual_flatten_runbook_status_lines(root_path))
    lines.extend(
        [
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


def vol_active_seed_readiness_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / VOL_ACTIVE_SEED_READINESS_SUMMARY_PATH)
    if not rows:
        return [
            "- vol_active_seed_readiness_present: False",
            f"- vol_active_seed_readiness_missing_saved_output: {VOL_ACTIVE_SEED_READINESS_SUMMARY_PATH}",
            "- vol_active_seed_readiness_status: missing_saved_output",
            "- vol_active_seed_readiness_warning: monitor only; missing saved readiness does not approve execution or scheduling.",
        ]
    return [
        "- vol_active_seed_readiness_present: True",
        f"- final_active_seed_readiness_status: {summary_value(rows, 'final_active_seed_readiness_status')}",
        f"- active_seed: {summary_value(rows, 'active_seed')}",
        f"- active_ticker: {summary_value(rows, 'active_ticker')}",
        f"- previous_seed: {summary_value(rows, 'previous_seed')}",
        f"- readiness_pass_count: {summary_value(rows, 'readiness_pass_count')}",
        f"- readiness_warning_count: {summary_value(rows, 'readiness_warning_count')}",
        f"- largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"- recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        f"- action_preview_added: {summary_value(rows, 'action_preview_added') or 'False'}",
        f"- order_instructions_created: {summary_value(rows, 'order_instructions_created') or 'False'}",
        f"- execution_approved: {summary_value(rows, 'execution_approved') or 'False'}",
        f"- paper_execution_approved: {summary_value(rows, 'paper_execution_approved') or 'False'}",
        f"- scheduling_approved: {summary_value(rows, 'scheduling_approved') or 'False'}",
        "- vol_active_seed_readiness_warning: monitor only; this is not action preview, order approval, execution approval, or scheduling approval.",
    ]


def summary_value(rows: list[dict[str, str]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def determine_final_status(
    freshness_statuses: list,
    decision_rows_present: bool,
    decisions_execution_false: bool,
    paper_live_monitoring_consistent: bool,
    daily_decision_present: bool,
    daily_decision_approvals_false: bool,
) -> str:
    if (
        has_stale_or_missing(freshness_statuses)
        or not decision_rows_present
        or not paper_live_monitoring_consistent
        or not daily_decision_present
    ):
        return "monitoring_stale_or_missing_inputs"
    if has_warning(freshness_statuses) or not decisions_execution_false or not daily_decision_approvals_false:
        return "monitoring_warning"
    return "healthy_monitoring_state"


def classify_action_required(
    freshness_statuses: list,
    decision_rows_present: bool,
    decisions_execution_false: bool,
    paper_live_monitoring_consistent: bool,
    daily_decision_present: bool,
    daily_decision_approvals_false: bool,
) -> dict[str, str]:
    if (
        has_stale_or_missing(freshness_statuses)
        or not decision_rows_present
        or not paper_live_monitoring_consistent
        or not daily_decision_present
    ):
        reason = (
            "paper_live_monitoring_saved_status_missing_or_inconsistent"
            if not paper_live_monitoring_consistent
            else "qqq100_daily_decision_saved_status_missing"
            if not daily_decision_present
            else "one_or_more_saved_report_inputs_stale_or_missing"
        )
        action = (
            "refresh_report_only_paper_live_monitoring_status"
            if not paper_live_monitoring_consistent
            else "refresh_report_only_qqq100_daily_decision"
            if not daily_decision_present
            else "refresh_or_investigate_saved_monitoring_inputs"
        )
        return {
            "action_required": "manual_review_required",
            "action_reason": reason,
            "suggested_manual_action": action,
        }
    if has_warning(freshness_statuses) or not decisions_execution_false or not daily_decision_approvals_false:
        reason = (
            "one_or_more_saved_report_inputs_warning_stale"
            if has_warning(freshness_statuses)
            else "qqq100_daily_decision_approval_flags_need_review"
            if not daily_decision_approvals_false
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
