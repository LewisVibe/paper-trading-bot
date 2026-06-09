"""Report-only scheduling readiness audit for market monitor refresh."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MARKET_MONITOR_SCHEDULING_READINESS_COLUMNS = [
    "check_name",
    "status",
    "risk_level",
    "scheduling_approved",
    "execution_approved",
    "evidence",
    "required_next_step",
]

MARKET_MONITOR_COMMANDS = [
    "--ticker-universe-readiness-report",
    "--market-monitor-snapshot",
    "--show-market-monitor",
    "--market-monitor-quality-report",
    "--refresh-market-monitor",
    "--market-monitor-scheduling-readiness-report",
]

FORBIDDEN_REFRESH_TOKENS = [
    "TradingClient(",
    "get_alpaca_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "init_database(",
    "load_config(",
    "Task Scheduler",
    "schtasks",
]

TARGETED_FORBIDDEN_CHECKS = [
    (
        "refresh_command_does_not_call_alpaca",
        ["TradingClient("],
        "Refresh runner has no TradingClient construction.",
        "Keep Alpaca clients out of market monitor refresh and any future scheduling review.",
    ),
    (
        "refresh_command_does_not_read_paper_positions",
        ["get_alpaca_positions("],
        "Refresh runner has no paper-position read calls.",
        "Keep paper positions out of market monitor refresh.",
    ),
    (
        "refresh_command_does_not_write_sqlite_trade_log",
        ["insert_trade_log(", "init_database("],
        "Refresh runner has no SQLite trade_log writes or database initialization.",
        "Keep SQLite trade_log writes out of monitoring refresh.",
    ),
    (
        "refresh_command_does_not_send_discord_alerts",
        ["send_discord_alert("],
        "Refresh runner has no Discord alert calls.",
        "Keep Discord alerts out of monitoring refresh until separately reviewed.",
    ),
    (
        "refresh_command_does_not_schedule",
        ["Task Scheduler", "schtasks"],
        "Refresh runner has no Windows Task Scheduler or schtasks calls.",
        "Do not add scheduled tasks or loops without a separate explicit scheduling task.",
    ),
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
    runner_source = read_text(root / "trading_bot" / "runners" / "research_reports.py")
    inventory_source = read_text(root / "scripts" / "verify_command_inventory.py")
    gitignore_source = read_text(root / ".gitignore")
    refresh_segment = source_segment(
        runner_source,
        "def run_refresh_market_monitor_command()",
        "def print_market_monitor_refresh_summary",
    )

    rows = [
        refresh_command_exists_row(bot_source, runner_source),
        refresh_report_only_row(bot_source, runner_source),
        refresh_no_forbidden_tokens_row(refresh_segment),
        refresh_dispatch_before_config_row(bot_source),
        *targeted_forbidden_token_rows(refresh_segment),
        generated_outputs_ignored_row(gitignore_source),
        repo_safety_verifier_exists_row(root),
        command_inventory_includes_market_monitor_rows(inventory_source),
        normal_bot_execution_separate_row(bot_source),
        scheduling_not_approved_row(),
        execution_not_approved_row(),
    ]
    return rows


def refresh_command_exists_row(bot_source: str, runner_source: str) -> dict[str, Any]:
    command_present = "--refresh-market-monitor" in bot_source
    runner_present = "def run_refresh_market_monitor_command()" in runner_source
    passed = command_present and runner_present
    return readiness_row(
        "refresh_command_exists",
        "pass" if passed else "error",
        "medium",
        f"cli_flag={command_present}; runner={runner_present}",
        "Keep the refresh command as a report/display wrapper only.",
    )


def refresh_report_only_row(bot_source: str, runner_source: str) -> dict[str, Any]:
    evidence_tokens = [
        "Refresh the safe market monitor report/display chain without execution.",
        "monitoring/report/display only and does not approve orders",
    ]
    passed = all(token in bot_source or token in runner_source for token in evidence_tokens)
    return readiness_row(
        "refresh_command_report_display_only",
        "pass" if passed else "warning",
        "high",
        "Help and runner warning describe monitoring/report/display only.",
        "Do not use refresh output as scheduling or execution approval.",
    )


def refresh_no_forbidden_tokens_row(refresh_segment: str) -> dict[str, Any]:
    found = [token for token in FORBIDDEN_REFRESH_TOKENS if token in refresh_segment]
    return readiness_row(
        "refresh_command_no_execution_side_effects",
        "pass" if not found else "error",
        "high",
        "Forbidden tokens in refresh runner: " + (", ".join(found) if found else "none"),
        "If any forbidden token appears, remove it before scheduling review.",
    )


def targeted_forbidden_token_rows(refresh_segment: str) -> list[dict[str, Any]]:
    rows = []
    for check_name, tokens, pass_evidence, required_next_step in TARGETED_FORBIDDEN_CHECKS:
        found = [token for token in tokens if token in refresh_segment]
        rows.append(
            readiness_row(
                check_name,
                "pass" if not found else "error",
                "high",
                pass_evidence if not found else "Forbidden tokens found: " + ", ".join(found),
                required_next_step,
            )
        )
    return rows


def refresh_dispatch_before_config_row(bot_source: str) -> dict[str, Any]:
    refresh_index = bot_source.find("if args.refresh_market_monitor:")
    config_index = bot_source.find("config_path = Path(args.config).resolve()")
    passed = refresh_index != -1 and config_index != -1 and refresh_index < config_index
    return readiness_row(
        "refresh_command_does_not_load_config",
        "pass" if passed else "error",
        "high",
        f"refresh_dispatch_index={refresh_index}; config_load_index={config_index}",
        "Keep refresh dispatch before config loading.",
    )


def generated_outputs_ignored_row(gitignore_source: str) -> dict[str, Any]:
    passed = "data/*" in gitignore_source
    return readiness_row(
        "generated_market_monitor_outputs_ignored",
        "pass" if passed else "error",
        "medium",
        "`.gitignore` contains data/*" if passed else "Could not find data/* in .gitignore.",
        "Keep generated market monitor CSVs out of commits.",
    )


def repo_safety_verifier_exists_row(root: Path) -> dict[str, Any]:
    verifier_path = root / "scripts" / "verify_repo_safety.py"
    passed = verifier_path.exists()
    return readiness_row(
        "repo_safety_verifier_exists",
        "pass" if passed else "error",
        "medium",
        str(verifier_path),
        "Run the repo safety verifier before commits and before any future scheduling review.",
    )


def command_inventory_includes_market_monitor_rows(inventory_source: str) -> dict[str, Any]:
    missing = [command for command in MARKET_MONITOR_COMMANDS if command not in inventory_source]
    return readiness_row(
        "command_inventory_includes_market_monitor_commands",
        "pass" if not missing else "error",
        "medium",
        "Missing commands: " + (", ".join(missing) if missing else "none"),
        "Keep command inventory verification covering all market monitor commands.",
    )


def normal_bot_execution_separate_row(bot_source: str) -> dict[str, Any]:
    refresh_index = bot_source.find("if args.refresh_market_monitor:")
    normal_config_index = bot_source.find("config_path = Path(args.config).resolve()")
    passed = refresh_index != -1 and normal_config_index != -1 and refresh_index < normal_config_index
    return readiness_row(
        "normal_bot_execution_remains_separate",
        "pass" if passed else "error",
        "high",
        "Refresh command returns before normal config/runtime path." if passed else "Could not confirm separation.",
        "Do not connect monitoring refresh to normal bot execution.",
    )


def scheduling_not_approved_row() -> dict[str, Any]:
    return readiness_row(
        "scheduling_not_approved",
        "pass",
        "high",
        "This report is readiness/audit only and does not create Windows Task Scheduler tasks.",
        "Future manual scheduling review must be explicitly requested and separately approved.",
    )


def execution_not_approved_row() -> dict[str, Any]:
    return readiness_row(
        "execution_not_approved",
        "pass",
        "high",
        "Market monitor outputs remain monitoring/report/display only.",
        "Do not treat monitoring output as order or paper-execution approval.",
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
    return [
        f"Market monitor scheduling readiness checks: {len(rows)}",
        f"Pass: {counts['pass']}, warning: {counts['warning']}, error: {counts['error']}",
        f"Scheduling approved false for all rows: {scheduling_false}",
        f"Execution approved false for all rows: {execution_false}",
        "Warning: this is readiness/audit only and does not create or approve scheduling.",
        f"Saved market monitor scheduling readiness report to {output_path}",
    ]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def source_segment(source: str, start_marker: str, end_marker: str) -> str:
    start = source.find(start_marker)
    if start == -1:
        return ""
    end = source.find(end_marker, start + len(start_marker))
    if end == -1:
        return source[start:]
    return source[start:end]
