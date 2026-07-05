"""Verify saved-price snapshot runner design remains design-only."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner_design import (  # noqa: E402
    FINAL_DECISION,
    OUTPUT_FILES,
    generate_vol_targeted_growth_saved_price_snapshot_runner_design,
    show_vol_targeted_growth_saved_price_snapshot_runner_design,
)


COMMANDS = [
    "--vol-targeted-growth-saved-price-snapshot-runner-design",
    "--show-vol-targeted-growth-saved-price-snapshot-runner-design",
]

FALSE_FLAGS = [
    "saved_price_snapshot_runner_approved",
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
    verify_fixture_output(failures)
    if failures:
        print("Saved-price snapshot runner design verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Saved-price snapshot runner design verification passed.")
    print("Verified runner design only, required fields, no price fetches, no quantities, false approvals, and no broker/order/scheduling calls.")
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
    source = (ROOT / "trading_bot/research/vol_targeted_growth_saved_price_snapshot_runner_design.py").read_text(encoding="utf-8")
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


def verify_fixture_output(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_saved_price_snapshot_runner_design(root)
        code, lines = show_vol_targeted_growth_saved_price_snapshot_runner_design(root)
        if code != 0:
            failures.append("display failed after generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            FINAL_DECISION,
            "required_symbols=QQQ,MGK,IBIT,SGOV",
            "runner_design_created=True",
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
        areas = {row["design_area"] for row in result.report_rows}
        for expected_area in [
            "allowed_output_fields",
            "required_symbols",
            "stale_price_policy",
            "provider_failure_policy",
            "execution_boundary",
            "approval_boundary",
        ]:
            if expected_area not in areas:
                failures.append(f"missing design area: {expected_area}")
        allowed_fields = next((row.get("allowed_future_field_or_rule", "") for row in result.report_rows if row.get("design_area") == "allowed_output_fields"), "")
        for required_field in ["broker_symbol", "last_saved_price", "price_timestamp_utc", "price_source", "price_status", "price_error"]:
            if required_field not in allowed_fields:
                failures.append(f"allowed output fields missing: {required_field}")
        for row in result.report_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).strip() != "False":
                    failures.append(f"report flag must be False for {row.get('design_area')}: {flag}")
        for row in result.summary_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).strip() != "False":
                    failures.append(f"summary flag must be False: {flag}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_approval_record_summary.csv",
        {"final_saved_price_snapshot_record_decision": "SAVED_PRICE_SNAPSHOT_METHOD_DISCUSSION_APPROVED_NO_PRICE_FETCH"},
    )
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_readiness_summary.csv",
        {"final_saved_price_snapshot_readiness_decision": "SAVED_PRICE_SNAPSHOT_NOT_APPROVED_QUANTITIES_BLOCKED"},
    )
    write_summary(
        data / "vol_targeted_growth_calculated_order_values_summary.csv",
        {"final_calculated_order_values_decision": "CALCULATED_TARGET_DOLLARS_CREATED_QUANTITIES_BLOCKED"},
    )


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


if __name__ == "__main__":
    raise SystemExit(main())
