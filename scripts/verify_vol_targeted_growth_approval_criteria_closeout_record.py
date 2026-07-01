"""Verify report-only approval_criteria_not_approval closeout checkpoints."""

from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_approval_criteria_closeout_approval_wording import (  # noqa: E402
    APPROVAL_PHRASE,
    FINAL_DECISION as WORDING_DECISION,
    generate_vol_targeted_growth_approval_criteria_closeout_approval_wording,
    show_vol_targeted_growth_approval_criteria_closeout_approval_wording,
)
from trading_bot.research.vol_targeted_growth_approval_criteria_closeout_record import (  # noqa: E402
    FINAL_DECISION as RECORD_DECISION,
    generate_vol_targeted_growth_approval_criteria_closeout_record,
    show_vol_targeted_growth_approval_criteria_closeout_record,
)


FALSE_FLAGS = [
    "approval_readiness_changed",
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
    verify_source_safety(failures)
    verify_fixture_outputs(failures)
    if failures:
        print("Approval-criteria closeout verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Approval-criteria closeout verification passed.")
    print("Verified wording, saved closeout record, false approvals, and no broker/order/scheduling calls.")
    return 0


def verify_source_safety(failures: list[str]) -> None:
    for rel in [
        "trading_bot/research/vol_targeted_growth_approval_criteria_closeout_approval_wording.py",
        "trading_bot/research/vol_targeted_growth_approval_criteria_closeout_record.py",
    ]:
        source = (ROOT / rel).read_text(encoding="utf-8")
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
                failures.append(f"{rel} contains forbidden runtime phrase: {phrase}")
        for required in ["saved_output_only", "execution_approved", "paper_execution_approved", "scheduling_approved", "order_values_populated"]:
            if required not in source:
                failures.append(f"{rel} missing safety phrase: {required}")


def verify_fixture_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        wording = generate_vol_targeted_growth_approval_criteria_closeout_approval_wording(root)
        wording_code, wording_lines = show_vol_targeted_growth_approval_criteria_closeout_approval_wording(root)
        record = generate_vol_targeted_growth_approval_criteria_closeout_record(root)
        record_code, record_lines = show_vol_targeted_growth_approval_criteria_closeout_record(root)
        if wording_code != 0:
            failures.append("wording display failed after generation")
        if record_code != 0:
            failures.append("record display failed after generation")
        output = "\n".join(wording.summary_lines + wording_lines + record.summary_lines + record_lines)
        for phrase in [
            APPROVAL_PHRASE,
            WORDING_DECISION,
            RECORD_DECISION,
            "approval_criteria_not_approval",
            "closed_blocker_count=3",
            "remaining_known_blockers=ticket_values_not_approved;executable_ticket_prerequisites_not_met",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        verify_false_flags(wording.summary_rows, failures, "wording")
        verify_false_flags(record.summary_rows, failures, "record")
        if summary_value(record.summary_rows, "approval_criteria_not_approval_closed") != "True":
            failures.append("record should mark approval_criteria_not_approval_closed=True")
        if summary_value(record.summary_rows, "closed_blocker_count") != "3":
            failures.append("record should count three closed blockers")
        for path in [*wording.output_paths.values(), *record.output_paths.values()]:
            if not path.exists():
                failures.append(f"expected output missing: {path}")


def verify_false_flags(rows: list[dict[str, object]], failures: list[str], label: str) -> None:
    for flag in FALSE_FLAGS:
        value = summary_or_flag_value(rows, flag)
        if value != "False":
            failures.append(f"{label} flag must be False: {flag}={value}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_executable_ticket_approval_criteria_not_approval_closeout_candidate_review_summary.csv",
        {"final_candidate_review_decision": "CLOSEOUT_CANDIDATE_NOT_READY_NO_APPROVAL"},
    )
    write_summary(
        data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_record_summary.csv",
        {
            "final_closeout_record_decision": "CRITERIA_RESOLUTION_PLAN_OPEN_BLOCKER_CLOSED_ONLY",
            "closed_blocker": "criteria_resolution_plan_open",
            "remaining_known_blockers": "approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met",
        },
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
