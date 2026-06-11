"""Report-only scheduling readiness audit for VPS-safe monitoring commands."""

from __future__ import annotations

import csv
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_bot.safety.monitor_lockfile import LOCK_WRAPPED_COMMAND_NAMES


MARKET_MONITOR_SCHEDULING_READINESS_COLUMNS = [
    "check_name",
    "status",
    "risk_level",
    "scheduling_approved",
    "execution_approved",
    "evidence",
    "required_next_step",
]

ASSESSED_SAFE_COMMANDS = [
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
]

PROMOTED_SAVED_OUTPUTS = [
    "data/promoted_review_refresh_summary.csv",
    "data/promoted_decision_preview.csv",
]

DEFENSIVE_SAVED_OUTPUTS = [
    "data/vol_managed_etf_robustness_report.csv",
    "data/etf_rotation_robustness_report.csv",
    "data/defensive_research_refresh_summary.csv",
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
    "data/market_monitor_scheduling_readiness_report.csv",
]

FORBIDDEN_REPORT_TOKEN_PARTS = [
    ("Trading", "Client("),
    ("get_alpaca", "_positions("),
    ("submit", "_order("),
    ("cancel", "_order("),
    ("create", "_order("),
    ("insert", "_trade_log("),
    ("sqlite3", ".connect("),
    ("send_discord", "_alert("),
    ("yf", ".download("),
    ("download_close", "_prices("),
    ("download_backtest", "_prices("),
    ("load", "_config("),
    ("open(", '"config.json"'),
    ("read_text(", '"config.json"'),
    ("scht", "asks"),
]


@dataclass
class MarketMonitorSchedulingReadinessResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_market_monitor_scheduling_readiness_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/market_monitor_scheduling_readiness_report.csv",
) -> MarketMonitorSchedulingReadinessResult:
    root = Path(root_dir)
    rows = build_market_monitor_scheduling_readiness_rows(root)
    output_path = root / output_filename
    write_market_monitor_scheduling_readiness_report(output_path, rows)
    return MarketMonitorSchedulingReadinessResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_market_monitor_scheduling_readiness_summary(rows, output_path),
    )


def build_market_monitor_scheduling_readiness_rows(root: Path) -> list[dict[str, Any]]:
    bot_source = read_text(root / "bot.py")
    module_source = read_text(root / "trading_bot" / "research" / "market_monitor_scheduling.py")
    runner_source = read_text(root / "trading_bot" / "runners" / "research_reports.py")
    inventory_source = read_text(root / "scripts" / "verify_command_inventory.py")
    docs_source = "\n".join(
        read_text(path)
        for path in [
            root / "README.md",
            root / "docs" / "CURRENT_STATE.md",
            root / "docs" / "VPS_SETUP_CHECKLIST.md",
            root / "docs" / "HERMES_TASK_BOARD.md",
        ]
    )
    return [
        scheduling_readiness_command_exists_row(bot_source, inventory_source),
        report_only_early_route_row(bot_source),
        assessed_command_set_row(),
        lockfile_coverage_row(runner_source),
        config_presence_only_row(root),
        saved_outputs_present_row(root, "promoted_saved_outputs_present", PROMOTED_SAVED_OUTPUTS),
        saved_outputs_present_row(root, "defensive_saved_outputs_present", DEFENSIVE_SAVED_OUTPUTS),
        generated_outputs_ignored_row(root),
        execution_capable_commands_excluded_row(docs_source),
        report_module_no_forbidden_calls_row(module_source),
        scheduling_not_approved_row(),
        execution_not_approved_row(),
        final_outcome_row(root),
    ]


def scheduling_readiness_command_exists_row(bot_source: str, inventory_source: str) -> dict[str, Any]:
    command_present = "--market-monitor-scheduling-readiness-report" in bot_source
    inventory_present = "--market-monitor-scheduling-readiness-report" in inventory_source
    return readiness_row(
        "scheduling_readiness_command_exists",
        "pass" if command_present and inventory_present else "error",
        "medium",
        f"bot_flag={command_present}; inventory={inventory_present}",
        "Keep the command registered as report-only.",
    )


def report_only_early_route_row(bot_source: str) -> dict[str, Any]:
    command_index = bot_source.find('sys.argv[1:] == ["--market-monitor-scheduling-readiness-report"]')
    alpaca_import_index = bot_source.find("from alpaca.trading.client import TradingClient")
    passed = command_index != -1 and alpaca_import_index != -1 and command_index < alpaca_import_index
    return readiness_row(
        "scheduling_readiness_routes_before_runtime_imports",
        "pass" if passed else "error",
        "high",
        f"early_route_index={command_index}; alpaca_import_index={alpaca_import_index}",
        "Keep this report-only route exact and before normal runtime imports.",
    )


def assessed_command_set_row() -> dict[str, Any]:
    expected = sorted(ASSESSED_SAFE_COMMANDS)
    actual = sorted(LOCK_WRAPPED_COMMAND_NAMES)
    return readiness_row(
        "assessed_command_set_limited_to_safe_vps_monitoring",
        "pass" if actual == expected else "error",
        "high",
        f"assessed={', '.join(expected)}; lock_wrapped={', '.join(actual)}",
        "Do not add execution-capable commands to the scheduling-readiness set.",
    )


def lockfile_coverage_row(runner_source: str) -> dict[str, Any]:
    missing = [command for command in ASSESSED_SAFE_COMMANDS if command not in runner_source]
    acquire_count = runner_source.count("acquire_monitor_lock(")
    release_count = runner_source.count("release_monitor_lock(")
    passed = not missing and acquire_count == len(ASSESSED_SAFE_COMMANDS) and release_count == len(ASSESSED_SAFE_COMMANDS)
    return readiness_row(
        "lockfile_protection_covers_safe_commands_only",
        "pass" if passed else "error",
        "high",
        (
            f"missing={', '.join(missing) if missing else 'none'}; "
            f"acquire_calls={acquire_count}; release_calls={release_count}"
        ),
        "Keep lockfile protection limited to safe report/preview/refresh commands.",
    )


def config_presence_only_row(root: Path) -> dict[str, Any]:
    exists = (root / "config.json").exists()
    return readiness_row(
        "config_presence_checked_without_reading_contents",
        "pass" if exists else "warning",
        "medium",
        f"config.json exists={exists}; contents were not read.",
        "Local config presence may be required for read-only paper-position preview, but secrets must never be printed.",
    )


def saved_outputs_present_row(root: Path, check_name: str, paths: list[str]) -> dict[str, Any]:
    missing = [path for path in paths if not (root / path).exists()]
    return readiness_row(
        check_name,
        "pass" if not missing else "warning",
        "medium",
        "Missing saved outputs: " + (", ".join(missing) if missing else "none"),
        "Run the relevant safe manual refresh command before a future scheduling review.",
    )


def generated_outputs_ignored_row(root: Path) -> dict[str, Any]:
    failures = [
        path
        for path in GENERATED_OUTPUT_PATHS
        if not is_git_ignored(root, path) or is_git_tracked(root, path)
    ]
    return readiness_row(
        "generated_outputs_remain_ignored_untracked",
        "pass" if not failures else "error",
        "medium",
        "Generated output policy failures: " + (", ".join(failures) if failures else "none"),
        "Keep generated CSV/chart/log/database outputs out of commits.",
    )


def execution_capable_commands_excluded_row(docs_source: str) -> dict[str, Any]:
    docs_lower = docs_source.lower()
    required_prose = [
        "execution-capable commands remain manual-only",
        "paper-order smoke tests",
        "slow-sma paper execution",
    ]
    missing = [phrase for phrase in required_prose if phrase not in docs_lower]
    return readiness_row(
        "execution_capable_commands_remain_excluded",
        "pass" if not missing else "warning",
        "high",
        "Missing documentation phrases: " + (", ".join(missing) if missing else "none"),
        "Keep execution-capable commands excluded from safe monitoring and scheduling review.",
    )


def report_module_no_forbidden_calls_row(module_source: str) -> dict[str, Any]:
    found = ["".join(parts) for parts in FORBIDDEN_REPORT_TOKEN_PARTS if "".join(parts) in module_source]
    return readiness_row(
        "scheduling_readiness_report_has_no_forbidden_calls",
        "pass" if not found else "error",
        "high",
        "Forbidden tokens in report module: " + (", ".join(found) if found else "none"),
        "Remove any runtime execution, market-data, alert, scheduling, or config-content access from this report.",
    )


def scheduling_not_approved_row() -> dict[str, Any]:
    return readiness_row(
        "scheduling_not_approved",
        "pass",
        "high",
        "This report is readiness-only and creates no schedules, services, cron jobs, or Task Scheduler entries.",
        "A separate explicit manual scheduling review is still required.",
    )


def execution_not_approved_row() -> dict[str, Any]:
    return readiness_row(
        "execution_not_approved",
        "pass",
        "high",
        "Report, preview, refresh, and lockfile outputs are not order or paper-execution approval.",
        "Do not connect these outputs to execution.",
    )


def final_outcome_row(root: Path) -> dict[str, Any]:
    config_exists = (root / "config.json").exists()
    saved_outputs_exist = all((root / path).exists() for path in PROMOTED_SAVED_OUTPUTS + DEFENSIVE_SAVED_OUTPUTS)
    generated_outputs_ok = all(
        is_git_ignored(root, path) and not is_git_tracked(root, path)
        for path in GENERATED_OUTPUT_PATHS
    )
    ready = config_exists and saved_outputs_exist and generated_outputs_ok
    reasons = []
    if not config_exists:
        reasons.append("config_presence_missing")
    if not saved_outputs_exist:
        reasons.append("saved_outputs_missing")
    if not generated_outputs_ok:
        reasons.append("generated_output_policy_failure")
    return readiness_row(
        "final_readiness_outcome",
        "pass" if ready else "warning",
        "high",
        (
            "ready_for_future_manual_scheduling_review"
            if ready
            else "not_ready_for_scheduling_review: " + ", ".join(reasons)
        ),
        "Even when ready, scheduling remains unapproved until a separate explicit review.",
    )


def readiness_row(
    check_name: str,
    status: str,
    risk_level: str,
    evidence: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "check_name": check_name,
        "status": status,
        "risk_level": risk_level,
        "scheduling_approved": False,
        "execution_approved": False,
        "evidence": evidence,
        "required_next_step": required_next_step,
    }


def write_market_monitor_scheduling_readiness_report(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MARKET_MONITOR_SCHEDULING_READINESS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_market_monitor_scheduling_readiness_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts = Counter(row.get("status", "unknown") for row in rows)
    scheduling_false = all(str(row.get("scheduling_approved")).lower() == "false" for row in rows)
    execution_false = all(str(row.get("execution_approved")).lower() == "false" for row in rows)
    outcome = next(
        (row["evidence"] for row in rows if row.get("check_name") == "final_readiness_outcome"),
        "not_ready_for_scheduling_review",
    )
    blocking_rows = [
        row["check_name"]
        for row in rows
        if row.get("status") in {"warning", "error"} and row.get("check_name") != "final_readiness_outcome"
    ]
    return [
        f"Market monitor scheduling readiness checks: {len(rows)}",
        f"Pass: {counts['pass']}, warning: {counts['warning']}, error: {counts['error']}",
        f"Outcome: {outcome}",
        "Assessed safe VPS commands: " + ", ".join(ASSESSED_SAFE_COMMANDS),
        "Blocking or review rows: " + (", ".join(blocking_rows) if blocking_rows else "none"),
        f"Scheduling approved false for all rows: {scheduling_false}",
        f"Execution approved false for all rows: {execution_false}",
        f"Saved market monitor scheduling readiness report to {output_path}",
        "Warning: this is report-only readiness for future manual review; it does not create or approve scheduling.",
        "Warning: report/preview/refresh monitoring is not execution approval.",
    ]


def print_market_monitor_scheduling_readiness_report(root: Path | str = ".") -> int:
    result = generate_market_monitor_scheduling_readiness_report(root)
    for line in result.summary_lines:
        print(line)
    return 0


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


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
