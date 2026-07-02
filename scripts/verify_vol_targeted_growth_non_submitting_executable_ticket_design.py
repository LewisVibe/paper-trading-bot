"""Verify the non-submitting executable-ticket design stays non-executable."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_non_submitting_executable_ticket_design import (  # noqa: E402
    FINAL_DECISION,
    FINAL_STATUS,
    OUTPUT_FILES,
    generate_vol_targeted_growth_non_submitting_executable_ticket_design,
    show_vol_targeted_growth_non_submitting_executable_ticket_design,
)


COMMANDS = [
    "--vol-targeted-growth-non-submitting-executable-ticket-design",
    "--show-vol-targeted-growth-non-submitting-executable-ticket-design",
]

FALSE_FLAGS = [
    "ticket_instance_created",
    "executable_ticket_created",
    "order_values_populated",
    "order_instructions_created",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "broker_positions_read",
    "paper_positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]


def main() -> int:
    failures: list[str] = []
    verify_commands_registered(failures)
    verify_outputs_ignored(failures)
    verify_source_safety(failures)
    verify_fixture_outputs(failures)
    if failures:
        print("Non-submitting executable-ticket design verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Non-submitting executable-ticket design verification passed.")
    print("Verified design-only ticket shape, blank order values, false approvals, and no broker/order/scheduling calls.")
    return 0


def verify_commands_registered(failures: list[str]) -> None:
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    inventory_source = (ROOT / "scripts/verify_command_inventory.py").read_text(encoding="utf-8")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"bot.py missing command: {command}")
        if command not in inventory_source:
            failures.append(f"command inventory missing command: {command}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for path in OUTPUT_FILES.values():
        result = subprocess.run(["git", "check-ignore", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_safety(failures: list[str]) -> None:
    source = (ROOT / "trading_bot/research/vol_targeted_growth_non_submitting_executable_ticket_design.py").read_text(encoding="utf-8")
    for phrase in [
        "TradingClient(",
        "MarketOrderRequest(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "get_all_positions",
        "sqlite3.connect",
        "send_discord_alert(",
        "send_telegram",
        "yf.",
        "import yfinance",
        "load_config(",
        "config.json",
    ]:
        if phrase in source:
            failures.append(f"source contains forbidden runtime phrase: {phrase}")


def verify_fixture_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_non_submitting_executable_ticket_design(root)
        code, lines = show_vol_targeted_growth_non_submitting_executable_ticket_design(root)
        if code != 0:
            failures.append("display failed after generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            FINAL_STATUS,
            FINAL_DECISION,
            "execution_design_approved=True",
            "order_value_field_count=5",
            "populated_order_value_count=0",
            "executable_ticket_design_created=True",
            "executable_ticket_created=False",
            "order_values_populated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        if summary_value(result.summary_rows, "populated_order_value_count") != "0":
            failures.append("order values must remain unpopulated")
        if summary_value(result.summary_rows, "executable_ticket_created") != "False":
            failures.append("executable_ticket_created must remain False")
        forbidden_ticket_fields = ["account_id", "api_key", "secret", "token", "webhook", "order_id"]
        ticket_text = "\n".join(str(value) for row in result.ticket_rows for value in row.values())
        for phrase in forbidden_ticket_fields:
            if phrase in ticket_text.lower():
                failures.append(f"ticket output contains forbidden field text: {phrase}")
        verify_false_flags(result.summary_rows, failures)
        for path in result.output_paths.values():
            if not path.exists():
                failures.append(f"expected output missing: {path}")


def verify_false_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for flag in FALSE_FLAGS:
        value = summary_or_flag_value(rows, flag)
        if value != "False":
            failures.append(f"flag must be False: {flag}={value}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_execution_design_approval_record_summary.csv",
        {
            "final_execution_design_record_decision": "EXECUTION_DESIGN_APPROVED_NO_ORDER_OR_EXECUTION_APPROVAL",
            "execution_design_approved": "True",
        },
    )
    write_summary(
        data / "vol_targeted_growth_manual_ticket_value_design_summary.csv",
        {"final_ticket_value_design_decision": "TICKET_VALUE_DESIGN_REVIEW_ONLY_VALUES_NOT_APPROVED"},
    )
    write_summary(
        data / "vol_targeted_growth_post_gate_review_summary.csv",
        {
            "final_post_gate_review_decision": "FRESH_BROKER_CONTEXT_SAVED_TICKET_VALUES_NOT_APPROVED",
            "saved_qqq_position_quantity_if_readonly": "1",
        },
    )
    write_summary(
        data / "vol_targeted_growth_executable_ticket_gap_list_summary.csv",
        {"final_ticket_design_decision": "EXECUTABLE_TICKET_DESIGN_NOT_READY", "largest_gap": "execution_not_approved"},
    )
    write_summary(data / "paper_live_go_no_go_dashboard_summary.csv", {"final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"})


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


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
