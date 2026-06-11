from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT_PATH = ROOT / "bot.py"
MODULE_PATH = ROOT / "trading_bot" / "research" / "market_monitor_scheduling.py"
INVENTORY_PATH = ROOT / "scripts" / "verify_command_inventory.py"

COMMAND = "--market-monitor-scheduling-readiness-report"
EXPECTED_SAFE_COMMANDS = {
    "--monitor-lockfile-readiness-report",
    "--refresh-promoted-review",
    "--refresh-defensive-research",
}
FORBIDDEN_MODULE_TOKEN_PARTS = [
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
    ("subprocess.run([", '"schtasks"'),
]


def main() -> int:
    failures: list[str] = []
    verify_command_registration(failures)
    verify_report_rows(failures)
    verify_source_safety(failures)

    if failures:
        print("Market monitor scheduling readiness verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Market monitor scheduling readiness verification passed.")
    print("Verified report-only command registration, safe assessed command set, false approval flags, and no scheduling/execution hooks.")
    return 0


def verify_command_registration(failures: list[str]) -> None:
    bot_source = read_text(BOT_PATH)
    inventory_source = read_text(INVENTORY_PATH)
    if COMMAND not in bot_source:
        failures.append(f"{COMMAND} is missing from bot.py")
    if COMMAND not in inventory_source:
        failures.append(f"{COMMAND} is missing from command inventory")
    if f'sys.argv[1:] == ["{COMMAND}"]' not in bot_source:
        failures.append(f"{COMMAND} should have an exact early report-only route")


def verify_report_rows(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.market_monitor_scheduling import (  # noqa: PLC0415
        ASSESSED_SAFE_COMMANDS,
        build_market_monitor_scheduling_readiness_rows,
        build_market_monitor_scheduling_readiness_summary,
    )

    if set(ASSESSED_SAFE_COMMANDS) != EXPECTED_SAFE_COMMANDS:
        failures.append(f"Assessed command set changed: {sorted(ASSESSED_SAFE_COMMANDS)}")

    rows = build_market_monitor_scheduling_readiness_rows(ROOT)
    if not rows:
        failures.append("Scheduling readiness report returned no rows")
        return

    row_names = {str(row.get("check_name")) for row in rows}
    required_rows = {
        "scheduling_readiness_command_exists",
        "scheduling_readiness_routes_before_runtime_imports",
        "assessed_command_set_limited_to_safe_vps_monitoring",
        "lockfile_protection_covers_safe_commands_only",
        "config_presence_checked_without_reading_contents",
        "promoted_saved_outputs_present",
        "defensive_saved_outputs_present",
        "generated_outputs_remain_ignored_untracked",
        "execution_capable_commands_remain_excluded",
        "scheduling_not_approved",
        "execution_not_approved",
        "final_readiness_outcome",
    }
    missing_rows = sorted(required_rows - row_names)
    if missing_rows:
        failures.append("Missing readiness rows: " + ", ".join(missing_rows))

    if any(str(row.get("execution_approved")).lower() != "false" for row in rows):
        failures.append("Every readiness row must keep execution_approved=False")
    if any(str(row.get("scheduling_approved")).lower() != "false" for row in rows):
        failures.append("Every readiness row must keep scheduling_approved=False")
    if any(row.get("status") == "error" for row in rows):
        error_rows = [str(row.get("check_name")) for row in rows if row.get("status") == "error"]
        failures.append("Scheduling readiness report has error rows: " + ", ".join(error_rows))

    output = "\n".join(build_market_monitor_scheduling_readiness_summary(rows, ROOT / "data" / "market_monitor_scheduling_readiness_report.csv"))
    for phrase in [
        "Market monitor scheduling readiness checks:",
        "Outcome:",
        "Assessed safe VPS commands:",
        "Scheduling approved false for all rows: True",
        "Execution approved false for all rows: True",
        "does not create or approve scheduling",
        "is not execution approval",
    ]:
        if phrase not in output:
            failures.append(f"Missing scheduling readiness summary phrase: {phrase}")


def verify_source_safety(failures: list[str]) -> None:
    source = read_text(MODULE_PATH)
    for token in ("".join(parts) for parts in FORBIDDEN_MODULE_TOKEN_PARTS):
        if token in source:
            failures.append(f"Scheduling readiness module must not contain forbidden token: {token}")
    if "write_market_monitor_scheduling_readiness_report" not in source:
        failures.append("Scheduling readiness module should keep its saved CSV report writer")
    if "scheduling_approved" not in source or "execution_approved" not in source:
        failures.append("Scheduling readiness module must preserve false approval columns")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
