from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_design import (  # noqa: E402
    FINAL_DECISION,
    FINAL_STATUS,
    OUTPUT_FILES,
    generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_design,
    show_vol_targeted_growth_fresh_broker_pre_ticket_gate_design,
)


FALSE_FLAGS = [
    "alpaca_called",
    "readonly_alpaca_check_run",
    "broker_positions_read",
    "paper_positions_read",
    "market_data_refreshed",
    "yfinance_called",
    "fresh_broker_pre_ticket_gate_run",
    "ticket_instance_created",
    "executable_ticket_created",
    "order_instructions_created",
    "order_values_populated",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
]

FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient",
    "submit_order(",
    "cancel_order(",
    "replace_order(",
    "get_all_positions",
    "get_open_position",
    "get_account",
    "sqlite3",
    "Discord",
    "Telegram",
    "TaskScheduler",
    "cron",
]


def main() -> int:
    failures: list[str] = []
    verify_commands_registered(failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(failures)
    verify_vps_daily_summary_integration(failures)
    verify_fixture_output(failures)

    if failures:
        print("Volatility-targeted fresh broker pre-ticket gate design verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted fresh broker pre-ticket gate design verification passed.")
    print("Verified gate-design-only output, no Alpaca call, no broker read, no order values, false approvals, and daily summary integration.")
    return 0


def verify_commands_registered(failures: list[str]) -> None:
    bot_source = read_text(ROOT / "bot.py")
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    for command in [
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-design",
        "--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-design",
    ]:
        if command not in bot_source:
            failures.append(f"bot.py missing command: {command}")
        if command not in inventory_source:
            failures.append(f"command inventory missing command: {command}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for path in OUTPUT_FILES.values():
        result = subprocess.run(
            ["git", "check-ignore", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_boundaries(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_fresh_broker_pre_ticket_gate_design.py")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"pre-ticket gate design source contains forbidden token: {token}")
    for phrase in [
        "gate_design_only",
        "FRESH_BROKER_PRE_TICKET_GATE_DESIGNED_NOT_RUN",
        "readonly_alpaca_check_run",
        "broker_positions_read",
        "fresh_broker_pre_ticket_gate_run",
        "order_values_populated",
        "orders_submitted",
        "execution_approved",
        "scheduling_approved",
    ]:
        if phrase not in source:
            failures.append(f"pre-ticket gate design source missing safety phrase: {phrase}")


def verify_vps_daily_summary_integration(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py")
    for phrase in [
        "VOL_FRESH_BROKER_PRE_TICKET_GATE_DESIGN_SUMMARY_PATH",
        "Volatility fresh broker pre-ticket gate design:",
        "vol_fresh_broker_pre_ticket_gate_design_status_lines",
        "FRESH_BROKER_PRE_TICKET_GATE_DESIGNED_NOT_RUN",
        "vol_fresh_broker_pre_ticket_gate_design_warning: monitor only;",
    ]:
        if phrase not in source:
            failures.append(f"VPS daily summary missing fresh broker pre-ticket gate phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_design(root)
        code, lines = show_vol_targeted_growth_fresh_broker_pre_ticket_gate_design(root)
        if code != 0:
            failures.append("show command failed after fixture generation")
        output = "\n".join(lines + result.summary_lines)
        for phrase in [
            FINAL_STATUS,
            FINAL_DECISION,
            "fresh_broker_pre_ticket_gate_run=False",
            "readonly_alpaca_check_run=False",
            "broker_positions_read=False",
            "order_values_populated=False",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        verify_summary_rows(result.summary_rows, failures)
        verify_check_rows(result.check_rows, failures)
        for name, path in result.output_paths.items():
            if not path.exists():
                failures.append(f"fixture did not write {name}: {path}")


def verify_summary_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    if summary_value(rows, "final_pre_ticket_gate_design_status") != FINAL_STATUS:
        failures.append("summary final status is incorrect")
    if summary_value(rows, "final_pre_ticket_gate_design_decision") != FINAL_DECISION:
        failures.append("summary final decision is incorrect")
    for flag in FALSE_FLAGS:
        if summary_or_flag_value(rows, flag) != "False":
            failures.append(f"summary flag must be False: {flag}")


def verify_check_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    required_checks = {
        "explicit_readonly_confirmation",
        "fresh_broker_position_read",
        "broker_state_age",
        "order_value_population",
        "execution_approval",
    }
    check_names = {str(row.get("gate_check", "")) for row in rows}
    missing = required_checks - check_names
    if missing:
        failures.append(f"gate checks missing required rows: {sorted(missing)}")
    for row in rows:
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).strip() != "False":
                failures.append(f"gate check flag must be False for {row.get('gate_check')}: {flag}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv",
        {
            "final_ticket_instance_design_status": "vol_targeted_growth_non_submitting_ticket_instance_design_created_manual_review_required",
            "final_ticket_instance_design_decision": "NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES",
        },
    )
    write_summary(
        data / "vol_targeted_growth_non_submitting_ticket_schema_design_summary.csv",
        {
            "final_schema_design_status": "vol_targeted_growth_non_submitting_ticket_schema_design_created_manual_review_required",
            "final_schema_design_decision": "NON_SUBMITTING_TICKET_SCHEMA_DESIGNED_NO_TICKET_CREATED",
        },
    )
    write_summary(
        data / "paper_live_go_no_go_dashboard_summary.csv",
        {
            "final_go_no_go_status": "paper_live_go_no_go_dashboard_execution_blocked_monitor_only",
            "final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY",
        },
    )


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def summary_value(rows: list[dict[str, object]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def summary_or_flag_value(rows: list[dict[str, object]], key: str) -> str:
    value = summary_value(rows, key)
    if value:
        return value
    for row in rows:
        if key in row:
            return str(row.get(key, "")).strip()
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
