"""Verify saved-price snapshot quality gate stays saved-output-only."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_saved_price_snapshot_quality_gate import (  # noqa: E402
    BLOCKED_DECISION,
    OUTPUT_FILES,
    PASS_DECISION,
    REQUIRED_SYMBOLS,
    generate_vol_targeted_growth_saved_price_snapshot_quality_gate,
    show_vol_targeted_growth_saved_price_snapshot_quality_gate,
)


COMMANDS = [
    "--vol-targeted-growth-saved-price-snapshot-quality-gate",
    "--show-vol-targeted-growth-saved-price-snapshot-quality-gate",
]

FALSE_FLAGS = [
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
    verify_blocked_fixture(failures)
    verify_passing_saved_price_fixture(failures)
    if failures:
        print("Saved-price snapshot quality gate verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Saved-price snapshot quality gate verification passed.")
    print("Verified saved-output price quality checks, no price fetches, no quantities, and false execution approvals.")
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
    source = (ROOT / "trading_bot/research/vol_targeted_growth_saved_price_snapshot_quality_gate.py").read_text(encoding="utf-8")
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


def verify_blocked_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_blocked_snapshot(root)
        result = generate_vol_targeted_growth_saved_price_snapshot_quality_gate(root)
        code, lines = show_vol_targeted_growth_saved_price_snapshot_quality_gate(root)
        if code != 0:
            failures.append("blocked fixture display failed after generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            BLOCKED_DECISION,
            "saved_price_snapshot_quality_gate_passed=False",
            "price_available_count=0",
            "order_quantities_calculated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"blocked fixture output missing phrase: {phrase}")
        verify_false_flags(result.summary_rows, failures)


def verify_passing_saved_price_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_passing_snapshot(root)
        result = generate_vol_targeted_growth_saved_price_snapshot_quality_gate(root)
        output = "\n".join(result.summary_lines)
        for phrase in [
            PASS_DECISION,
            "saved_price_snapshot_quality_gate_passed=True",
            f"price_available_count={len(REQUIRED_SYMBOLS)}",
            "missing_symbol_count=0",
            "price_error_count=0",
            "stale_price_count=0",
            "order_quantities_calculated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"passing fixture output missing phrase: {phrase}")
        if summary_value(result.summary_rows, "order_values_populated") != "False":
            failures.append("passing quality gate must not populate order values")
        verify_false_flags(result.summary_rows, failures)
        for path in result.output_paths.values():
            if not path.exists():
                failures.append(f"expected output missing: {path}")


def verify_false_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for flag in FALSE_FLAGS:
        value = summary_or_flag_value(rows, flag)
        if value != "False":
            failures.append(f"flag must be False: {flag}={value}")


def seed_blocked_snapshot(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_snapshot(data / "vol_targeted_growth_saved_price_snapshot.csv", "blocked_confirmation_required", "", "")
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_summary.csv",
        {
            "final_saved_price_snapshot_decision": "SAVED_PRICE_SNAPSHOT_NOT_RUN_CONFIRMATION_REQUIRED",
            "saved_price_snapshot_run_confirmed": "False",
            "saved_prices_fetched": "False",
        },
    )
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_run_approval_record_summary.csv",
        {"final_saved_price_snapshot_run_record_decision": "SAVED_PRICE_SNAPSHOT_RUN_APPROVED_PRICE_ONLY_QUANTITIES_BLOCKED"},
    )


def seed_passing_snapshot(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    timestamp = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    write_snapshot(data / "vol_targeted_growth_saved_price_snapshot.csv", "price_available", "123.45", timestamp)
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_summary.csv",
        {
            "final_saved_price_snapshot_decision": "SAVED_PRICE_SNAPSHOT_CREATED_QUANTITIES_STILL_BLOCKED",
            "saved_price_snapshot_run_confirmed": "True",
            "saved_prices_fetched": "True",
        },
    )
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_run_approval_record_summary.csv",
        {"final_saved_price_snapshot_run_record_decision": "SAVED_PRICE_SNAPSHOT_RUN_APPROVED_PRICE_ONLY_QUANTITIES_BLOCKED"},
    )


def write_snapshot(path: Path, status: str, price: str, timestamp: str) -> None:
    fieldnames = [
        "broker_symbol",
        "last_saved_price",
        "price_timestamp_utc",
        "price_source",
        "price_status",
        "price_error",
        "required_next_step",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for symbol in REQUIRED_SYMBOLS:
            writer.writerow(
                {
                    "broker_symbol": symbol,
                    "last_saved_price": price,
                    "price_timestamp_utc": timestamp,
                    "price_source": "fixture",
                    "price_status": status,
                    "price_error": "",
                    "required_next_step": "manual_review_saved_prices_before_any_quantity_calculation",
                }
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
