"""Verify quantity-calculation readiness stays report-only."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_quantity_calculation_readiness import (  # noqa: E402
    OUTPUT_FILES,
    READY_DECISION,
    generate_vol_targeted_growth_quantity_calculation_readiness,
    show_vol_targeted_growth_quantity_calculation_readiness,
)


COMMANDS = [
    "--vol-targeted-growth-quantity-calculation-readiness",
    "--show-vol-targeted-growth-quantity-calculation-readiness",
]

FALSE_FLAGS = [
    "quantity_calculation_approved",
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
    verify_ready_fixture(failures)
    if failures:
        print("Quantity-calculation readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Quantity-calculation readiness verification passed.")
    print("Verified saved target dollars plus saved prices can request approval discussion, with quantities/execution still false.")
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
    source = (ROOT / "trading_bot/research/vol_targeted_growth_quantity_calculation_readiness.py").read_text(encoding="utf-8")
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


def verify_ready_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_ready_inputs(root)
        result = generate_vol_targeted_growth_quantity_calculation_readiness(root)
        code, lines = show_vol_targeted_growth_quantity_calculation_readiness(root)
        if code != 0:
            failures.append("display failed after generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            READY_DECISION,
            "quantity_calculation_discussion_ready=True",
            "quantity_calculation_approved=False",
            "saved_price_quality_gate_passed=True",
            "target_dollar_total=1000.00",
            "order_quantities_calculated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"ready fixture output missing phrase: {phrase}")
        verify_false_flags(result.summary_rows, failures)
        for path in result.output_paths.values():
            if not path.exists():
                failures.append(f"expected output missing: {path}")


def verify_false_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for flag in FALSE_FLAGS:
        value = summary_or_flag_value(rows, flag)
        if value != "False":
            failures.append(f"flag must be False: {flag}={value}")


def seed_ready_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_target_values(data / "vol_targeted_growth_calculated_order_values.csv")
    write_summary(
        data / "vol_targeted_growth_calculated_order_values_summary.csv",
        {
            "final_calculated_order_values_decision": "CALCULATED_TARGET_DOLLARS_CREATED_QUANTITIES_BLOCKED",
            "target_dollar_total": "1000.00",
        },
    )
    write_snapshot(data / "vol_targeted_growth_saved_price_snapshot.csv")
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_quality_gate_summary.csv",
        {
            "final_saved_price_snapshot_quality_decision": "SAVED_PRICE_SNAPSHOT_QUALITY_GATE_PASSED_QUANTITIES_STILL_BLOCKED",
            "saved_price_snapshot_quality_gate_passed": "True",
        },
    )
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_run_approval_record_summary.csv",
        {"final_saved_price_snapshot_run_record_decision": "SAVED_PRICE_SNAPSHOT_RUN_APPROVED_PRICE_ONLY_QUANTITIES_BLOCKED"},
    )


def write_target_values(path: Path) -> None:
    rows = [
        ("qqq100_core_trend_sleeve", "QQQ", "700.00"),
        ("high_growth_stock_research_sleeve", "MGK", "200.00"),
        ("crypto_research_sleeve", "IBIT", "50.00"),
        ("defensive_cash_or_bond_sleeve", "SGOV", "50.00"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sleeve_name", "broker_symbol", "target_dollars", "proposed_order_quantity"])
        writer.writeheader()
        for sleeve, symbol, dollars in rows:
            writer.writerow({"sleeve_name": sleeve, "broker_symbol": symbol, "target_dollars": dollars, "proposed_order_quantity": ""})


def write_snapshot(path: Path) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["broker_symbol", "last_saved_price", "price_timestamp_utc", "price_status"])
        writer.writeheader()
        for symbol in ["QQQ", "MGK", "IBIT", "SGOV"]:
            writer.writerow({"broker_symbol": symbol, "last_saved_price": "100.00", "price_timestamp_utc": timestamp, "price_status": "price_available"})


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
