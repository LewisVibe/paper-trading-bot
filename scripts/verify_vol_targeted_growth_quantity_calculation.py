"""Verify review quantity calculation chain remains non-submitting."""

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

from trading_bot.research.vol_targeted_growth_quantity_calculation import (  # noqa: E402
    CALC_DECISION,
    CALC_OUTPUTS,
    QUALITY_DECISION,
    QUALITY_OUTPUTS,
    RECORD_DECISION,
    RECORD_OUTPUTS,
    WORDING_OUTPUTS,
    generate_vol_targeted_growth_quantity_calculation_approval_record,
    generate_vol_targeted_growth_quantity_calculation_approval_wording,
    generate_vol_targeted_growth_review_quantity_estimates,
    generate_vol_targeted_growth_review_quantity_quality_gate,
    show_vol_targeted_growth_review_quantity_quality_gate,
)


COMMANDS = [
    "--vol-targeted-growth-quantity-calculation-approval-wording",
    "--show-vol-targeted-growth-quantity-calculation-approval-wording",
    "--vol-targeted-growth-quantity-calculation-approval-record",
    "--show-vol-targeted-growth-quantity-calculation-approval-record",
    "--vol-targeted-growth-review-quantity-estimates",
    "--show-vol-targeted-growth-review-quantity-estimates",
    "--vol-targeted-growth-review-quantity-quality-gate",
    "--show-vol-targeted-growth-review-quantity-quality-gate",
]

FALSE_FLAGS = [
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
        print("Review quantity calculation verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Review quantity calculation verification passed.")
    print("Verified approval record, saved review quantities, quality gate, false order/execution flags, and no broker/order/scheduling calls.")
    return 0


def verify_commands_registered(failures: list[str]) -> None:
    parser_source = (ROOT / "trading_bot/cli/parser.py").read_text(encoding="utf-8")
    inventory_source = (ROOT / "scripts/verify_command_inventory.py").read_text(encoding="utf-8")
    for command in COMMANDS:
        if command not in parser_source:
            failures.append(f"CLI parser missing command: {command}")
        if command not in inventory_source:
            failures.append(f"command inventory missing command: {command}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for path in [*WORDING_OUTPUTS.values(), *RECORD_OUTPUTS.values(), *CALC_OUTPUTS.values(), *QUALITY_OUTPUTS.values()]:
        result = subprocess.run(["git", "check-ignore", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_safety(failures: list[str]) -> None:
    source = (ROOT / "trading_bot/research/vol_targeted_growth_quantity_calculation.py").read_text(encoding="utf-8")
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
    for forbidden in ["order_side", "order_type", "time_in_force", "account_id", "api_key", "webhook", "secret_key", "broker_order_id"]:
        if forbidden in source:
            failures.append(f"source contains forbidden executable field name: {forbidden}")


def verify_fixture_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        wording = generate_vol_targeted_growth_quantity_calculation_approval_wording(root)
        record = generate_vol_targeted_growth_quantity_calculation_approval_record(root)
        estimates = generate_vol_targeted_growth_review_quantity_estimates(root)
        quality = generate_vol_targeted_growth_review_quantity_quality_gate(root)
        code, lines = show_vol_targeted_growth_review_quantity_quality_gate(root)
        if code != 0:
            failures.append("quality display failed after generation")
        output = "\n".join(wording.summary_lines + record.summary_lines + estimates.summary_lines + quality.summary_lines + lines)
        for phrase in [
            RECORD_DECISION,
            CALC_DECISION,
            QUALITY_DECISION,
            "quantity_calculation_approved=True",
            "review_quantities_created=True",
            "order_quantities_calculated=True",
            "order_instructions_created: False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        if len(estimates.report_rows) != 3:
            # The result dataclass report_rows is the checkpoint rows; quantity rows live in the CSV.
            pass
        quantity_rows = read_csv_rows(root / CALC_OUTPUTS["report"])
        if len(quantity_rows) != 4:
            failures.append(f"expected 4 review quantity rows, found {len(quantity_rows)}")
        for row in quantity_rows:
            if row.get("quantity_estimate_status") != "review_quantity_estimate_created":
                failures.append(f"quantity estimate row not created: {row}")
            if float(row.get("review_share_quantity_estimate") or 0) <= 0:
                failures.append(f"quantity estimate must be positive: {row}")
            for forbidden in ["order_side", "order_type", "time_in_force", "account_id", "api_key", "webhook", "secret_key", "broker_order_id"]:
                if forbidden in row:
                    failures.append(f"quantity output contains forbidden field: {forbidden}")
        verify_false_flags(record.summary_rows + estimates.summary_rows + quality.summary_rows, failures)
        for path in [*wording.output_paths.values(), *record.output_paths.values(), *estimates.output_paths.values(), *quality.output_paths.values()]:
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
        data / "vol_targeted_growth_quantity_calculation_readiness_summary.csv",
        {
            "final_quantity_calculation_readiness_decision": "READY_TO_REQUEST_QUANTITY_CALCULATION_APPROVAL_NOT_APPROVED",
            "target_dollar_total": "100000.00",
        },
    )
    write_target_values(data / "vol_targeted_growth_calculated_order_values.csv")
    write_summary(
        data / "vol_targeted_growth_calculated_order_values_summary.csv",
        {
            "final_calculated_order_values_decision": "CALCULATED_TARGET_DOLLARS_CREATED_QUANTITIES_BLOCKED",
            "target_dollar_total": "100000.00",
        },
    )
    write_prices(data / "vol_targeted_growth_saved_price_snapshot.csv")
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_quality_gate_summary.csv",
        {
            "final_saved_price_snapshot_quality_decision": "SAVED_PRICE_SNAPSHOT_QUALITY_GATE_PASSED_QUANTITIES_STILL_BLOCKED",
            "saved_price_snapshot_quality_gate_passed": "True",
        },
    )


def write_target_values(path: Path) -> None:
    rows = [
        ("qqq100_core_trend_sleeve", "QQQ", "70000.00"),
        ("high_growth_stock_research_sleeve", "MGK", "20000.00"),
        ("crypto_research_sleeve", "IBIT", "5000.00"),
        ("defensive_cash_or_bond_sleeve", "SGOV", "5000.00"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sleeve_name", "broker_symbol", "target_dollars", "proposed_order_quantity"])
        writer.writeheader()
        for sleeve, symbol, dollars in rows:
            writer.writerow({"sleeve_name": sleeve, "broker_symbol": symbol, "target_dollars": dollars, "proposed_order_quantity": ""})


def write_prices(path: Path) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    prices = {"QQQ": "350.00", "MGK": "100.00", "IBIT": "50.00", "SGOV": "100.00"}
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["broker_symbol", "last_saved_price", "price_timestamp_utc", "price_status"])
        writer.writeheader()
        for symbol, price in prices.items():
            writer.writerow({"broker_symbol": symbol, "last_saved_price": price, "price_timestamp_utc": timestamp, "price_status": "price_available"})


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
