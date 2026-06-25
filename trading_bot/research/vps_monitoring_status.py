"""Console-only VPS monitoring status summary."""

from __future__ import annotations

import subprocess
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from trading_bot.research.monitoring_freshness import build_freshness_statuses, format_freshness_lines


LOCK_WRAPPED_COMMANDS = [
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
]

SAFE_NEXT_COMMANDS = [
    "Monitor lockfile readiness report flag: --monitor-lockfile-readiness-report",
    "Promoted review refresh flag: --refresh-promoted-review",
    "Defensive research refresh flag: --refresh-defensive-research",
]

HIGH_RISK_BOUNDARY_LINES = [
    "Normal bot runs remain high-risk/manual-only and are outside safe VPS monitoring.",
    "Paper-order smoke tests remain excluded from safe monitoring and scheduling readiness.",
    "Slow-SMA paper execution remains excluded from safe monitoring and scheduling readiness.",
    "No execution-capable paper-trading command is approved for scheduling or automation.",
]

DEFENSIVE_SAVED_INPUTS = [
    "data/vol_managed_etf_robustness_report.csv",
    "data/etf_rotation_robustness_report.csv",
]

PROMOTED_REVIEW_SUMMARY_PATH = "data/promoted_review_refresh_summary.csv"
PROMOTED_DECISION_PREVIEW_PATH = "data/promoted_decision_preview.csv"
PAPER_LIVE_MONITORING_STATUS_PATH = "data/paper_live_monitoring_status.csv"
QQQ100_DAILY_DECISION_SUMMARY_PATH = "data/qqq100_daily_decision_summary.csv"
QQQ100_MANUAL_FLATTEN_READINESS_SUMMARY_PATH = "data/qqq100_manual_flatten_readiness_summary.csv"
QQQ100_MANUAL_FLATTEN_RUNBOOK_SUMMARY_PATH = "data/qqq100_manual_flatten_runbook_summary.csv"

PAPER_LIVE_REQUIRED_SUMMARY_VALUES = {
    "active_strategy": "qqq_100_trend_gate",
    "active_ticker": "QQQ",
    "saved_position_state": "paper_position_long",
    "saved_position_quantity": "1",
    "alignment_state": "aligned_long",
    "followup_policy_status": "no_action_required_already_aligned",
    "no_action_required": "True",
    "recommended_next_step": "hold_no_action_and_monitor_only",
    "never_schedule_order_capable_commands": "True",
    "execution_approved": "False",
    "paper_execution_approved": "False",
    "scheduling_approved": "False",
    "live_trading_approved": "False",
    "followup_order_approved": "False",
    "repeat_execution_approved": "False",
}

PAPER_LIVE_APPROVAL_COLUMNS = [
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
]

GENERATED_OUTPUT_PATHS = [
    "data/monitor_lockfile_readiness_report.csv",
    "data/promoted_review_refresh_summary.csv",
    "data/defensive_research_refresh_summary.csv",
    "data/promoted_strategy_preview.csv",
    "data/promoted_strategy_action_preview.csv",
    "data/promoted_risk_preview.csv",
    "data/promoted_consensus_preview.csv",
    "data/promoted_decision_preview.csv",
    "data/defensive_candidate_comparison.csv",
    "data/etf_defensive_drawdown_comparison.csv",
    "data/charts/etf_defensive_drawdown_comparison.png",
    "data/paper_live_monitoring_status.csv",
    "data/paper_live_monitoring_components.csv",
    "data/paper_live_monitoring_blockers.csv",
    "data/qqq100_daily_decision_report.csv",
    "data/qqq100_daily_decision_summary.csv",
    "data/qqq100_daily_decision_blockers.csv",
    "data/qqq100_daily_decision_evidence.csv",
    "data/qqq100_manual_flatten_readiness_report.csv",
    "data/qqq100_manual_flatten_readiness_summary.csv",
    "data/qqq100_manual_flatten_readiness_blockers.csv",
    "data/qqq100_manual_flatten_readiness_evidence.csv",
    "data/qqq100_manual_flatten_runbook_report.csv",
    "data/qqq100_manual_flatten_runbook_summary.csv",
    "data/qqq100_manual_flatten_runbook_blockers.csv",
    "data/qqq100_manual_flatten_runbook_evidence.csv",
]


@dataclass(frozen=True)
class StatusLine:
    label: str
    status: str
    detail: str


@dataclass(frozen=True)
class PaperLiveMonitoringContext:
    present: bool
    consistent: bool
    approvals_false: bool
    missing_or_mismatched: tuple[str, ...]
    values: dict[str, str]


def build_vps_monitoring_status_lines(root: Path | str = ".") -> list[str]:
    root_path = Path(root)
    status_lines = build_status_lines(root_path)
    lines = [
        "VPS MONITORING STATUS. REPORT ONLY. NOT EXECUTION.",
        "execution_approved=False",
        "scheduling_approved=False",
        "No dashboard, web server, open ports, loop mode, scheduling, or execution controls are enabled.",
        "",
        "Repo safety reminder:",
        "- Run python scripts\\verify_repo_safety.py before committing or relying on VPS state.",
        "- Generated CSV/chart/log/database outputs should remain ignored and untracked.",
        "",
        "Lockfile final state:",
    ]
    for command in LOCK_WRAPPED_COMMANDS:
        lines.append(f"- lock-wrapped safe command: {command}")
    lines.append("- Lockfile protection prevents overlap only; it does not approve scheduling or execution.")
    lines.append("")
    lines.append("Prerequisite status:")
    for row in status_lines:
        lines.append(f"- {row.status}: {row.label}: {row.detail}")
    lines.append("")
    lines.append("Promoted review state:")
    lines.extend(promoted_review_status_lines(root_path))
    lines.append("")
    lines.append("Paper-live monitoring status:")
    lines.extend(paper_live_monitoring_status_lines(root_path))
    lines.append("")
    lines.append("QQQ100 daily decision:")
    lines.extend(qqq100_daily_decision_status_lines(root_path))
    lines.append("")
    lines.append("QQQ100 manual flatten readiness:")
    lines.extend(qqq100_manual_flatten_readiness_status_lines(root_path))
    lines.append("")
    lines.append("QQQ100 manual flatten runbook:")
    lines.extend(qqq100_manual_flatten_runbook_status_lines(root_path))
    lines.append("")
    lines.append("Saved-output freshness:")
    lines.extend(format_freshness_lines(build_freshness_statuses(root_path)))
    lines.append("")
    lines.append("Next safe manual report actions:")
    for command in SAFE_NEXT_COMMANDS:
        lines.append(f"- {command}")
    lines.append("")
    lines.append("High-risk/manual-only boundaries:")
    for boundary in HIGH_RISK_BOUNDARY_LINES:
        lines.append(f"- {boundary}")
    lines.append("")
    lines.append("Missing config and missing saved research inputs are prerequisites/statuses, not execution approval.")
    lines.append("Promoted review saved-output summaries are compact counts only and do not approve execution.")
    lines.append("Normal bot runs, paper-order smoke tests, and slow-SMA paper execution remain high-risk/manual-only.")
    lines.append("Warning: this command does not call Alpaca, yfinance, Discord, SQLite trade_log, or read config.json contents.")
    return lines


def build_status_lines(root: Path) -> list[StatusLine]:
    config_path = root / "config.json"
    defensive_missing = [path for path in DEFENSIVE_SAVED_INPUTS if not (root / path).exists()]
    return [
        StatusLine(
            "config_status",
            "present" if config_path.exists() else "config_missing_for_readonly_promoted_review",
            (
                "config.json exists locally; contents were not read."
                if config_path.exists()
                else "config.json is missing; read-only promoted preview may refuse, but this is not a safety failure."
            ),
        ),
        StatusLine(
            "defensive_saved_inputs",
            "present" if not defensive_missing else "missing_saved_research_inputs",
            (
                "Key saved defensive prerequisites appear present."
                if not defensive_missing
                else "Missing saved inputs: " + ", ".join(defensive_missing)
            ),
        ),
        StatusLine(
            "generated_outputs",
            "ignored_untracked" if generated_outputs_ignored(root) else "review_required",
            "Generated data/dashboard/chart/log/db outputs should remain ignored/untracked.",
        ),
        StatusLine(
            "execution_boundary",
            "blocked_manual_only",
            "normal bot, paper-order-test, and slow-SMA paper execution remain high-risk/manual-only.",
        ),
    ]


def generated_outputs_ignored(root: Path) -> bool:
    return all(is_git_ignored(root, path) and not is_git_tracked(root, path) for path in GENERATED_OUTPUT_PATHS)


def promoted_review_status_lines(root: Path) -> list[str]:
    summary_path = root / PROMOTED_REVIEW_SUMMARY_PATH
    decision_path = root / PROMOTED_DECISION_PREVIEW_PATH
    lines: list[str] = []

    if not summary_path.exists() and not decision_path.exists():
        return ["- promoted_review_missing_saved_outputs: no saved promoted review summary or decision preview found."]

    if summary_path.exists():
        summary_rows = read_csv_rows(summary_path)
        status_counts = Counter(row.get("status", "") or "blank" for row in summary_rows)
        execution_false = all_false(summary_rows, "execution_approved")
        lines.append("- promoted_review_summary_present: True")
        lines.append(f"- promoted_review_step_counts: {format_counts(status_counts)}")
        lines.append(f"- promoted_review_summary_execution_approved_false: {execution_false}")
    else:
        lines.append("- promoted_review_summary_present: False")

    if decision_path.exists():
        decision_rows = read_csv_rows(decision_path)
        decision_counts = Counter(row.get("decision_state", "") or "blank" for row in decision_rows)
        execution_false = all_false(decision_rows, "execution_approved")
        status = "decision_execution_approval_false" if execution_false else "decision_execution_approval_warning"
        lines.append("- promoted_decision_preview_present: True")
        lines.append(f"- promoted_decision_state_counts: {format_counts(decision_counts)}")
        lines.append(f"- {status}: execution_approved_false_for_all_rows={execution_false}")
    else:
        lines.append("- promoted_decision_preview_present: False")

    return lines


def build_paper_live_monitoring_context(root: Path) -> PaperLiveMonitoringContext:
    rows = read_csv_rows(root / PAPER_LIVE_MONITORING_STATUS_PATH)
    values = {row.get("summary_name", ""): str(row.get("summary_value", "")).strip() for row in rows}
    if not rows:
        return PaperLiveMonitoringContext(
            present=False,
            consistent=False,
            approvals_false=True,
            missing_or_mismatched=("missing_file:data/paper_live_monitoring_status.csv",),
            values={},
        )

    missing_or_mismatched = []
    for name, expected in PAPER_LIVE_REQUIRED_SUMMARY_VALUES.items():
        actual = values.get(name, "")
        if not equivalent_summary_value(actual, expected):
            missing_or_mismatched.append(f"{name}:expected={expected};actual={actual or 'missing'}")

    approvals_false = all_false(rows, "execution_approved")
    for column in PAPER_LIVE_APPROVAL_COLUMNS:
        if not equivalent_summary_value(values.get(column, ""), "False"):
            approvals_false = False

    return PaperLiveMonitoringContext(
        present=True,
        consistent=not missing_or_mismatched and approvals_false,
        approvals_false=approvals_false,
        missing_or_mismatched=tuple(missing_or_mismatched),
        values=values,
    )


def paper_live_monitoring_status_lines(root: Path) -> list[str]:
    context = build_paper_live_monitoring_context(root)
    values = context.values
    lines = [
        f"- paper_live_monitoring_status_present: {context.present}",
        f"- paper_live_monitoring_status_consistent: {context.consistent}",
        f"- paper_live_monitoring_approval_flags_false: {context.approvals_false}",
    ]
    if context.present:
        lines.extend(
            [
                f"- active_strategy: {values.get('active_strategy', 'missing')}",
                f"- active_ticker: {values.get('active_ticker', 'missing')}",
                f"- saved_position_state: {values.get('saved_position_state', 'missing')}",
                f"- saved_position_quantity: {values.get('saved_position_quantity', 'missing')}",
                f"- alignment_state: {values.get('alignment_state', 'missing')}",
                f"- followup_policy_status: {values.get('followup_policy_status', 'missing')}",
                f"- no_action_required: {values.get('no_action_required', 'missing')}",
                f"- recommended_next_step: {values.get('recommended_next_step', 'missing')}",
                f"- followup_order_approved: {values.get('followup_order_approved', 'False')}",
                f"- repeat_execution_approved: {values.get('repeat_execution_approved', 'False')}",
                f"- never_schedule_order_capable_commands: {values.get('never_schedule_order_capable_commands', 'missing')}",
            ]
        )
    else:
        lines.append("- paper_live_monitoring_missing_saved_output: data/paper_live_monitoring_status.csv")
    if context.missing_or_mismatched:
        lines.append("- paper_live_monitoring_manual_review_items: " + "; ".join(context.missing_or_mismatched))
    lines.append("- paper_live_monitoring_warning: monitor only; repeat/follow-up orders are not approved.")
    return lines


def qqq100_daily_decision_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / QQQ100_DAILY_DECISION_SUMMARY_PATH)
    values = {row.get("summary_name", ""): str(row.get("summary_value", "")).strip() for row in rows}
    if not rows:
        return [
            "- qqq100_daily_decision_present: False",
            "- qqq100_daily_decision_missing_saved_output: data/qqq100_daily_decision_summary.csv",
            "- qqq100_daily_decision_warning: monitor only; run the safe daily decision report before relying on this status.",
        ]
    lines = [
        "- qqq100_daily_decision_present: True",
        f"- daily_decision_status: {values.get('daily_decision_status', 'missing')}",
        f"- active_strategy: {values.get('active_strategy', 'missing')}",
        f"- active_ticker: {values.get('active_ticker', 'missing')}",
        f"- desired_state: {values.get('desired_state', 'missing')}",
        f"- saved_position_state: {values.get('saved_position_state', 'missing')}",
        f"- saved_position_quantity: {values.get('saved_position_quantity', 'missing')}",
        f"- alignment_state: {values.get('alignment_state', 'missing')}",
        f"- followup_policy_status: {values.get('followup_policy_status', 'missing')}",
        f"- no_action_required: {values.get('no_action_required', 'missing')}",
        f"- manual_discussion_status: {values.get('manual_discussion_status', 'missing')}",
        f"- recommended_next_step: {values.get('recommended_next_step', 'missing')}",
        f"- followup_order_approved: {values.get('followup_order_approved', 'False')}",
        f"- repeat_execution_approved: {values.get('repeat_execution_approved', 'False')}",
        f"- never_schedule_order_capable_commands: {values.get('never_schedule_order_capable_commands', 'missing')}",
        "- qqq100_daily_decision_warning: monitor only; this is not order approval.",
    ]
    return lines


def qqq100_manual_flatten_readiness_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / QQQ100_MANUAL_FLATTEN_READINESS_SUMMARY_PATH)
    values = {row.get("summary_name", ""): str(row.get("summary_value", "")).strip() for row in rows}
    if not rows:
        return [
            "- qqq100_manual_flatten_readiness_present: False",
            "- qqq100_manual_flatten_readiness_missing_saved_output: data/qqq100_manual_flatten_readiness_summary.csv",
            "- qqq100_manual_flatten_readiness_warning: monitor only; run the safe readiness report before relying on this status.",
        ]
    return [
        "- qqq100_manual_flatten_readiness_present: True",
        f"- flatten_readiness_status: {values.get('flatten_readiness_status', 'missing')}",
        f"- active_strategy: {values.get('active_strategy', 'missing')}",
        f"- active_ticker: {values.get('active_ticker', 'missing')}",
        f"- desired_state: {values.get('desired_state', 'missing')}",
        f"- saved_position_state: {values.get('saved_position_state', 'missing')}",
        f"- saved_position_quantity: {values.get('saved_position_quantity', 'missing')}",
        f"- alignment_state: {values.get('alignment_state', 'missing')}",
        f"- followup_policy_status: {values.get('followup_policy_status', 'missing')}",
        f"- manual_flatten_discussion_status: {values.get('manual_flatten_discussion_status', 'missing')}",
        f"- recommended_next_step: {values.get('recommended_next_step', 'missing')}",
        f"- followup_order_approved: {values.get('followup_order_approved', 'False')}",
        f"- repeat_execution_approved: {values.get('repeat_execution_approved', 'False')}",
        f"- flatten_execution_approved: {values.get('flatten_execution_approved', 'False')}",
        f"- never_schedule_order_capable_commands: {values.get('never_schedule_order_capable_commands', 'missing')}",
        "- qqq100_manual_flatten_readiness_warning: monitor only; this is not flatten approval.",
    ]


def qqq100_manual_flatten_runbook_status_lines(root: Path) -> list[str]:
    rows = read_csv_rows(root / QQQ100_MANUAL_FLATTEN_RUNBOOK_SUMMARY_PATH)
    values = {row.get("summary_name", ""): str(row.get("summary_value", "")).strip() for row in rows}
    if not rows:
        return [
            "- qqq100_manual_flatten_runbook_present: False",
            "- qqq100_manual_flatten_runbook_missing_saved_output: data/qqq100_manual_flatten_runbook_summary.csv",
            "- qqq100_manual_flatten_runbook_warning: monitor only; run the safe runbook report before relying on this status.",
        ]
    return [
        "- qqq100_manual_flatten_runbook_present: True",
        f"- runbook_status: {values.get('runbook_status', 'missing')}",
        f"- active_strategy: {values.get('active_strategy', 'missing')}",
        f"- active_ticker: {values.get('active_ticker', 'missing')}",
        f"- desired_state: {values.get('desired_state', 'missing')}",
        f"- saved_position_state: {values.get('saved_position_state', 'missing')}",
        f"- saved_position_quantity: {values.get('saved_position_quantity', 'missing')}",
        f"- alignment_state: {values.get('alignment_state', 'missing')}",
        f"- flatten_readiness_status: {values.get('flatten_readiness_status', 'missing')}",
        f"- manual_flatten_discussion_status: {values.get('manual_flatten_discussion_status', 'missing')}",
        f"- recommended_next_step: {values.get('recommended_next_step', 'missing')}",
        f"- followup_order_approved: {values.get('followup_order_approved', 'False')}",
        f"- repeat_execution_approved: {values.get('repeat_execution_approved', 'False')}",
        f"- flatten_execution_approved: {values.get('flatten_execution_approved', 'False')}",
        f"- manual_flatten_approved: {values.get('manual_flatten_approved', 'False')}",
        f"- never_schedule_order_capable_commands: {values.get('never_schedule_order_capable_commands', 'missing')}",
        "- qqq100_manual_flatten_runbook_warning: monitor only; this is not manual flatten approval.",
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error):
        return []


def all_false(rows: list[dict[str, str]], column: str) -> bool:
    return all(str(row.get(column, "")).strip().lower() in {"", "false", "0", "no"} for row in rows)


def format_counts(counts: Counter[str]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def equivalent_summary_value(actual: str, expected: str) -> bool:
    actual_clean = str(actual).strip()
    expected_clean = str(expected).strip()
    if expected_clean.lower() in {"true", "false"}:
        return actual_clean.lower() == expected_clean.lower()
    return actual_clean == expected_clean


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


def print_vps_monitoring_status(root: Path | str = ".") -> int:
    for line in build_vps_monitoring_status_lines(root):
        print(line)
    return 0
