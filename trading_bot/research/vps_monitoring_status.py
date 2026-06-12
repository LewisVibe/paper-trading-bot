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
]


@dataclass(frozen=True)
class StatusLine:
    label: str
    status: str
    detail: str


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
