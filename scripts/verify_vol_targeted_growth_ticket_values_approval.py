"""Verify ticket-values discussion approval remains non-executable."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_ticket_values_approval import (  # noqa: E402
    RECORD_DECISION,
    RECORD_OUTPUTS,
    generate_vol_targeted_growth_ticket_values_approval_readiness,
    generate_vol_targeted_growth_ticket_values_approval_record,
    generate_vol_targeted_growth_ticket_values_approval_wording,
    show_vol_targeted_growth_ticket_values_approval_record,
)


COMMANDS = [
    "--vol-targeted-growth-ticket-values-approval-readiness",
    "--show-vol-targeted-growth-ticket-values-approval-readiness",
    "--vol-targeted-growth-ticket-values-approval-wording",
    "--show-vol-targeted-growth-ticket-values-approval-wording",
    "--vol-targeted-growth-ticket-values-approval-record",
    "--show-vol-targeted-growth-ticket-values-approval-record",
]

FALSE_FLAGS = [
    "ticket_values_approved",
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
        print("Ticket-values approval verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Ticket-values approval verification passed.")
    print("Verified discussion approval only, false value/order/execution flags, and no broker/order/scheduling calls.")
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
    from trading_bot.research.vol_targeted_growth_ticket_values_approval import READINESS_OUTPUTS, WORDING_OUTPUTS  # noqa: PLC0415

    for path in [*READINESS_OUTPUTS.values(), *WORDING_OUTPUTS.values(), *RECORD_OUTPUTS.values()]:
        result = subprocess.run(["git", "check-ignore", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_safety(failures: list[str]) -> None:
    source = (ROOT / "trading_bot/research/vol_targeted_growth_ticket_values_approval.py").read_text(encoding="utf-8")
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
        readiness = generate_vol_targeted_growth_ticket_values_approval_readiness(root)
        wording = generate_vol_targeted_growth_ticket_values_approval_wording(root)
        record = generate_vol_targeted_growth_ticket_values_approval_record(root)
        code, lines = show_vol_targeted_growth_ticket_values_approval_record(root)
        if code != 0:
            failures.append("record display failed after generation")
        output = "\n".join(readiness.summary_lines + wording.summary_lines + record.summary_lines + lines)
        for phrase in [
            "READY_FOR_TICKET_VALUE_DESIGN_DISCUSSION_NOT_VALUES_APPROVED",
            "TICKET_VALUE_DISCUSSION_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
            RECORD_DECISION,
            "ticket_value_discussion_approved=True",
            "ticket_values_approved=False",
            "order_values_populated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        if summary_value(record.summary_rows, "ticket_value_discussion_approved") != "True":
            failures.append("record should mark discussion approved")
        if summary_value(record.summary_rows, "ticket_values_approved") != "False":
            failures.append("record must not approve ticket values")
        verify_false_flags(record.summary_rows, failures)
        for path in record.output_paths.values():
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
        {"final_execution_design_record_decision": "EXECUTION_DESIGN_APPROVED_NO_ORDER_OR_EXECUTION_APPROVAL", "execution_design_approved": "True"},
    )
    write_summary(
        data / "vol_targeted_growth_non_submitting_executable_ticket_design_summary.csv",
        {"final_executable_ticket_design_decision": "NON_SUBMITTING_EXECUTABLE_TICKET_DESIGNED_NO_ORDER_VALUES"},
    )
    write_summary(
        data / "vol_targeted_growth_manual_ticket_value_design_summary.csv",
        {"final_ticket_value_design_decision": "TICKET_VALUE_DESIGN_REVIEW_ONLY_VALUES_NOT_APPROVED"},
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
