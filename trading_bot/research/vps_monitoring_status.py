"""Console-only VPS monitoring status summary."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


LOCK_WRAPPED_COMMANDS = [
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
]

SAFE_NEXT_COMMANDS = [
    "python bot.py --monitor-lockfile-readiness-report",
    "python bot.py --refresh-promoted-review",
    "python bot.py --refresh-defensive-research",
]

BLOCKED_COMMANDS = [
    "python bot.py",
    "python bot.py --paper-order-test ... --confirm-paper-order",
    "python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper",
    "--paper-order-test",
    "--confirm-paper-order",
    "--execute-slow-sma-paper",
    "--confirm-slow-sma-paper",
]

DEFENSIVE_SAVED_INPUTS = [
    "data/vol_managed_etf_robustness_report.csv",
    "data/etf_rotation_robustness_report.csv",
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
    lines.append("Next safe manual commands:")
    for command in SAFE_NEXT_COMMANDS:
        lines.append(f"- {command}")
    lines.append("")
    lines.append("Blocked/high-risk commands:")
    for command in BLOCKED_COMMANDS:
        lines.append(f"- {command}")
    lines.append("")
    lines.append("Missing config and missing saved research inputs are prerequisites/statuses, not execution approval.")
    lines.append("Normal python bot.py, paper-order-test, and slow-SMA paper execution remain high-risk/manual-only.")
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
