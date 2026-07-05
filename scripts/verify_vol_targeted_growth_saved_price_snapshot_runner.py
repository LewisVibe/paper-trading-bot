"""Verify guarded saved-price snapshot runner defaults to blocked/no-fetch."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner import (  # noqa: E402
    CONFIRM_FLAG,
    FINAL_DECISION_BLOCKED,
    OUTPUT_FILES,
    generate_vol_targeted_growth_saved_price_snapshot,
    show_vol_targeted_growth_saved_price_snapshot,
)


COMMANDS = [
    "--vol-targeted-growth-saved-price-snapshot",
    "--show-vol-targeted-growth-saved-price-snapshot",
    "--confirm-saved-price-snapshot-run",
]

FALSE_FLAGS = [
    "saved_price_snapshot_created",
    "saved_price_snapshot_run_confirmed",
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
    verify_confirmation_gate(failures)
    verify_default_fixture_output(failures)
    if failures:
        print("Guarded saved-price snapshot runner verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Guarded saved-price snapshot runner verification passed.")
    print("Verified default no-fetch mode, explicit confirmation gate, false quantities/execution approvals, and no broker/order/scheduling calls.")
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


def verify_confirmation_gate(failures: list[str]) -> None:
    source = (ROOT / "trading_bot/research/vol_targeted_growth_saved_price_snapshot_runner.py").read_text(encoding="utf-8")
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    if CONFIRM_FLAG not in source or CONFIRM_FLAG not in bot_source:
        failures.append("confirmation flag missing from runner source or bot routing")
    if "confirm_saved_price_snapshot_run: bool = False" not in source:
        failures.append("runner must default confirmation to False")
    if "if confirm_saved_price_snapshot_run:" not in source:
        failures.append("runner must branch price fetch behind confirmation")
    fetch_index = source.find("yf.download")
    confirm_index = source.find("if confirm_saved_price_snapshot_run:")
    if fetch_index == -1:
        failures.append("runner should contain the future guarded yfinance fetch path")
    elif confirm_index == -1 or fetch_index < confirm_index:
        failures.append("yfinance fetch must appear only after confirmation branch")
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
        "load_config(",
        "config.json",
    ]:
        if token in source:
            failures.append(f"source contains forbidden runtime token: {token}")


def verify_default_fixture_output(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_saved_price_snapshot(root)
        code, lines = show_vol_targeted_growth_saved_price_snapshot(root)
        if code != 0:
            failures.append("display failed after blocked default generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            FINAL_DECISION_BLOCKED,
            "saved_price_snapshot_run_confirmed=False",
            "saved_prices_fetched=False",
            "price_success_count=0",
            "price_error_count=0",
            "order_quantities_calculated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"default output missing phrase: {phrase}")
        for row in result.report_rows:
            if row.get("price_status") != "blocked_confirmation_required":
                failures.append(f"default row should be blocked before fetch: {row.get('broker_symbol')}")
            if row.get("last_saved_price"):
                failures.append(f"default row must not include a price: {row.get('broker_symbol')}")
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).strip() != "False":
                    failures.append(f"default report flag must be False for {row.get('broker_symbol')}: {flag}")
        for row in result.summary_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).strip() != "False":
                    failures.append(f"default summary flag must be False: {flag}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_runner_approval_record_summary.csv",
        {"final_saved_price_snapshot_runner_record_decision": "SAVED_PRICE_SNAPSHOT_RUNNER_IMPLEMENTATION_APPROVED_NO_RUN_OR_PRICE_FETCH"},
    )
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_runner_readiness_summary.csv",
        {"final_saved_price_snapshot_runner_readiness_decision": "READY_TO_DISCUSS_SAVED_PRICE_SNAPSHOT_RUNNER_IMPLEMENTATION_NO_PRICE_FETCH"},
    )
    write_summary(
        data / "vol_targeted_growth_saved_price_snapshot_runner_design_summary.csv",
        {"final_saved_price_snapshot_runner_design_decision": "SAVED_PRICE_SNAPSHOT_RUNNER_DESIGNED_NO_PRICE_FETCH"},
    )


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


if __name__ == "__main__":
    raise SystemExit(main())
