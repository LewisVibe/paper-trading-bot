from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_saved_price_snapshot_readiness import (  # noqa: E402
    FINAL_DECISION,
    OUTPUT_FILES,
    generate_vol_targeted_growth_saved_price_snapshot_readiness,
    show_vol_targeted_growth_saved_price_snapshot_readiness,
)


COMMANDS = [
    "--vol-targeted-growth-saved-price-snapshot-readiness",
    "--show-vol-targeted-growth-saved-price-snapshot-readiness",
]

FALSE_FLAGS = [
    "saved_price_snapshot_approved",
    "saved_prices_fetched",
    "prices_refreshed",
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
        print("Volatility-targeted saved-price snapshot readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted saved-price snapshot readiness verification passed.")
    print("Verified price evidence readiness, no price fetches, blank quantities, false approvals, and no broker/order/scheduling calls.")
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
    source = (ROOT / "trading_bot/research/vol_targeted_growth_saved_price_snapshot_readiness.py").read_text(encoding="utf-8")
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
        result = generate_vol_targeted_growth_saved_price_snapshot_readiness(root)
        code, lines = show_vol_targeted_growth_saved_price_snapshot_readiness(root)
        if code != 0:
            failures.append("display failed after generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            FINAL_DECISION,
            "symbols_requiring_saved_prices=QQQ,MGK,IBIT,SGOV",
            "saved_price_snapshot_approved=False",
            "saved_prices_fetched=False",
            "order_quantities_calculated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        actual_symbols = [row["broker_symbol"] for row in result.report_rows]
        if actual_symbols != ["QQQ", "MGK", "IBIT", "SGOV"]:
            failures.append(f"unexpected symbols: {actual_symbols}")
        for row in result.report_rows:
            if row.get("readiness_status") != "saved_price_required_before_quantity_calculation":
                failures.append(f"unexpected readiness status for {row.get('broker_symbol')}")
            for field in ["required_price_field", "required_timestamp_field", "required_source_field"]:
                if not row.get(field):
                    failures.append(f"missing required price evidence field for {row.get('broker_symbol')}: {field}")
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).strip() != "False":
                    failures.append(f"report flag must be False for {row.get('broker_symbol')}: {flag}")
        for row in result.summary_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).strip() != "False":
                    failures.append(f"summary flag must be False: {flag}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_values(
        data / "vol_targeted_growth_calculated_order_values.csv",
        [
            ("qqq100_core_trend_sleeve", "QQQ", "700.00"),
            ("high_growth_stock_research_sleeve", "MGK", "200.00"),
            ("crypto_research_sleeve", "IBIT", "50.00"),
            ("defensive_cash_or_bond_sleeve", "SGOV", "50.00"),
        ],
    )
    write_values(
        data / "vol_targeted_growth_sleeve_symbol_mapping.csv",
        [
            ("qqq100_core_trend_sleeve", "QQQ", ""),
            ("high_growth_stock_research_sleeve", "MGK", ""),
            ("crypto_research_sleeve", "IBIT", ""),
            ("defensive_cash_or_bond_sleeve", "SGOV", ""),
        ],
    )
    write_summary(
        data / "vol_targeted_growth_calculated_order_values_summary.csv",
        {
            "final_calculated_order_values_status": "vol_targeted_growth_calculated_order_values_created_manual_review_required",
            "target_dollar_total": "1000.00",
        },
    )


def write_values(path: Path, rows: list[tuple[str, str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sleeve_name", "broker_symbol", "target_dollars"])
        writer.writeheader()
        for sleeve, symbol, dollars in rows:
            writer.writerow({"sleeve_name": sleeve, "broker_symbol": symbol, "target_dollars": dollars})


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


if __name__ == "__main__":
    raise SystemExit(main())
