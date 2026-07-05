"""Verify saved-price snapshot runner implementation approval stays non-running."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner_approval import (  # noqa: E402
    RECORD_DECISION,
    RECORD_OUTPUTS,
    WORDING_OUTPUTS,
    generate_vol_targeted_growth_saved_price_snapshot_runner_approval_record,
    generate_vol_targeted_growth_saved_price_snapshot_runner_approval_wording,
    show_vol_targeted_growth_saved_price_snapshot_runner_approval_record,
)


COMMANDS = [
    "--vol-targeted-growth-saved-price-snapshot-runner-approval-wording",
    "--show-vol-targeted-growth-saved-price-snapshot-runner-approval-wording",
    "--vol-targeted-growth-saved-price-snapshot-runner-approval-record",
    "--show-vol-targeted-growth-saved-price-snapshot-runner-approval-record",
]

FALSE_FLAGS = [
    "saved_price_snapshot_run_approved",
    "saved_price_snapshot_created",
    "saved_prices_fetched",
    "prices_refreshed",
    "price_provider_called",
    "order_quantities_calculated",
    "broker_ready_order_values_populated",
    "order_values_populated",
    "order_instructions_created",
    "ticket_instance_created",
    "executable_ticket_created",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "broker_positions_read",
    "paper_positions_read",
    "market_data_refreshed",
    "yfinance_called",
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
        print("Saved-price snapshot runner approval verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Saved-price snapshot runner approval verification passed.")
    print("Verified implementation approval only, no run, no price fetches, no quantities, false execution approvals, and no broker/order/scheduling calls.")
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
    for path in [*WORDING_OUTPUTS.values(), *RECORD_OUTPUTS.values()]:
        result = subprocess.run(["git", "check-ignore", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_safety(failures: list[str]) -> None:
    source = (ROOT / "trading_bot/research/vol_targeted_growth_saved_price_snapshot_runner_approval.py").read_text(encoding="utf-8")
    for token in [
        "TradingClient(",
        "MarketOrderRequest(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "get_all_positions",
        "get_open_position",
        "sqlite3.connect",
        "send_discord_alert",
        "send_telegram",
        "yf.",
        "import yfinance",
        "download(",
        "Ticker(",
        "requests.",
        "urllib",
        "socket.",
        "load_config(",
        "config.json",
    ]:
        if token in source:
            failures.append(f"source contains forbidden runtime token: {token}")


def verify_fixture_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        wording = generate_vol_targeted_growth_saved_price_snapshot_runner_approval_wording(root)
        record = generate_vol_targeted_growth_saved_price_snapshot_runner_approval_record(root)
        code, lines = show_vol_targeted_growth_saved_price_snapshot_runner_approval_record(root)
        if code != 0:
            failures.append("record display failed after generation")
        output = "\n".join(wording.summary_lines + record.summary_lines + lines)
        for phrase in [
            "SAVED_PRICE_SNAPSHOT_RUNNER_IMPLEMENTATION_APPROVAL_WORDING_DEFINED_NOT_APPROVED",
            RECORD_DECISION,
            "runner_implementation_approved=True",
            "saved_price_snapshot_run_approved=False",
            "saved_prices_fetched=False",
            "order_quantities_calculated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        if summary_value(record.summary_rows, "runner_implementation_approved") != "True":
            failures.append("record should approve implementation only")
        if summary_value(record.summary_rows, "saved_price_snapshot_runner_approved") != "True":
            failures.append("record should mark runner implementation approved")
        if summary_value(record.summary_rows, "saved_price_snapshot_run_approved") != "False":
            failures.append("record must not approve a price snapshot run")
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
        data / "vol_targeted_growth_saved_price_snapshot_runner_readiness_summary.csv",
        {
            "final_saved_price_snapshot_runner_readiness_decision": "READY_TO_DISCUSS_SAVED_PRICE_SNAPSHOT_RUNNER_IMPLEMENTATION_NO_PRICE_FETCH",
            "runner_implementation_discussion_ready": "True",
        },
    )
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_runner_design_summary.csv",
        {"final_saved_price_snapshot_runner_design_decision": "SAVED_PRICE_SNAPSHOT_RUNNER_DESIGNED_NO_PRICE_FETCH"},
    )
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_approval_record_summary.csv",
        {"final_saved_price_snapshot_record_decision": "SAVED_PRICE_SNAPSHOT_METHOD_DISCUSSION_APPROVED_NO_PRICE_FETCH"},
    )


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
