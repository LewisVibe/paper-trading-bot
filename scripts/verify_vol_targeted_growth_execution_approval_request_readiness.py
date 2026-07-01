"""Verify execution approval request readiness stays report-only."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_execution_approval_request_readiness import (  # noqa: E402
    FINAL_DECISION,
    FINAL_STATUS,
    OUTPUT_FILES,
    generate_vol_targeted_growth_execution_approval_request_readiness,
    show_vol_targeted_growth_execution_approval_request_readiness,
)


FALSE_FLAGS = [
    "approval_requested",
    "approval_recorded",
    "manual_execution_design_approved",
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
        print("Execution approval request readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Execution approval request readiness verification passed.")
    print("Verified readiness-to-ask only, false approvals, and no broker/order/scheduling calls.")
    return 0


def verify_commands_registered(failures: list[str]) -> None:
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    inventory_source = (ROOT / "scripts/verify_command_inventory.py").read_text(encoding="utf-8")
    for command in [
        "--vol-targeted-growth-execution-approval-request-readiness",
        "--show-vol-targeted-growth-execution-approval-request-readiness",
    ]:
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
    source = (ROOT / "trading_bot/research/vol_targeted_growth_execution_approval_request_readiness.py").read_text(encoding="utf-8")
    for phrase in [
        "TradingClient(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "get_all_positions",
        "sqlite3.connect",
        "send_discord_alert(",
        "send_telegram",
        "yf.",
        "import yfinance",
    ]:
        if phrase in source:
            failures.append(f"source contains forbidden runtime phrase: {phrase}")


def verify_fixture_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_execution_approval_request_readiness(root)
        code, lines = show_vol_targeted_growth_execution_approval_request_readiness(root)
        if code != 0:
            failures.append("display failed after generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            FINAL_STATUS,
            FINAL_DECISION,
            "checklist_blockers_closed=True",
            "approval_request_ready=True",
            "approval_requested=False",
            "approval_recorded=False",
            "largest_blocker=explicit_human_execution_approval_not_recorded",
            "order_values_populated=false",
            "executable_ticket_created=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        if summary_value(result.summary_rows, "approval_request_ready") != "True":
            failures.append("approval_request_ready should be True when saved checklist blockers are closed")
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
        data / "vol_targeted_growth_final_ticket_blockers_closeout_record_summary.csv",
        {
            "final_closeout_record_decision": "FINAL_TICKET_BLOCKERS_CLOSED_NO_EXECUTION_APPROVAL",
            "remaining_known_blockers": "none",
        },
    )
    write_summary(
        data / "vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv",
        {
            "closed_blocker_count": "5",
            "remaining_known_blockers_after_closeout": "none",
            "largest_blocker": "execution_not_approved",
        },
    )
    write_summary(data / "vol_targeted_growth_executable_ticket_gap_list_summary.csv", {"largest_gap": "execution_not_approved"})
    write_summary(data / "paper_live_go_no_go_dashboard_summary.csv", {"final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"})
    write_summary(data / "vol_targeted_growth_manual_execution_design_approval_gate_summary.csv", {"final_approval_gate_decision": "MANUAL_EXECUTION_DESIGN_APPROVAL_NOT_RECORDED"})


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
