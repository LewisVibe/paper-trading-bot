from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_calculated_order_values import (  # noqa: E402
    FINAL_DECISION,
    OUTPUT_FILES,
    generate_vol_targeted_growth_calculated_order_values,
    show_vol_targeted_growth_calculated_order_values,
)


COMMANDS = [
    "--vol-targeted-growth-calculated-order-values",
    "--show-vol-targeted-growth-calculated-order-values",
]

FALSE_FLAGS = [
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
        print("Volatility-targeted calculated order values verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted calculated order values verification passed.")
    print("Verified target-dollar math, blank quantities, false approvals, and no broker/order/scheduling calls.")
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
    source = (ROOT / "trading_bot/research/vol_targeted_growth_calculated_order_values.py").read_text(encoding="utf-8")
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
        "load_config(",
        "config.json",
    ]:
        if token in source:
            failures.append(f"source contains forbidden runtime token: {token}")


def verify_fixture_output(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_calculated_order_values(root)
        code, lines = show_vol_targeted_growth_calculated_order_values(root)
        if code != 0:
            failures.append("display failed after generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            FINAL_DECISION,
            "proposed_review_notional_usd=1000.00",
            "target_dollar_total=1000.00",
            "order_quantities_calculated=False",
            "order_values_populated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        expected = {"QQQ": "700.00", "MGK": "200.00", "IBIT": "50.00", "SGOV": "50.00"}
        actual = {row["broker_symbol"]: row["target_dollars"] for row in result.report_rows}
        if actual != expected:
            failures.append(f"target-dollar math mismatch: {actual}")
        for row in result.report_rows:
            if row.get("proposed_order_side") or row.get("proposed_order_quantity"):
                failures.append(f"side/quantity must stay blank for {row.get('broker_symbol')}")
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
    write_rows(
        data / "vol_targeted_growth_sleeve_symbol_mapping.csv",
        [
            ("qqq100_core_trend_sleeve", "0.70", "QQQ"),
            ("high_growth_stock_research_sleeve", "0.20", "MGK"),
            ("crypto_research_sleeve", "0.05", "IBIT"),
            ("defensive_cash_or_bond_sleeve", "0.05", "SGOV"),
        ],
    )
    write_rows(
        data / "vol_targeted_growth_broker_ready_action_proposal.csv",
        [
            ("qqq100_core_trend_sleeve", "0.70", "QQQ"),
            ("high_growth_stock_research_sleeve", "0.20", "MGK"),
            ("crypto_research_sleeve", "0.05", "IBIT"),
            ("defensive_cash_or_bond_sleeve", "0.05", "SGOV"),
        ],
    )
    write_summary(
        data / "vol_targeted_growth_broker_ready_action_proposal_summary.csv",
        {"final_broker_ready_action_proposal_decision": "BROKER_SYMBOL_ACTION_PROPOSAL_CREATED_NO_ORDER_INSTRUCTIONS"},
    )
    write_summary(
        data / "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv",
        {
            "final_pre_ticket_gate_run_status": "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_completed_readonly_manual_review_required",
            "qqq_position_quantity_if_readonly": "1",
        },
    )


def write_rows(path: Path, rows: list[tuple[str, str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sleeve_name", "target_weight", "broker_symbol"])
        writer.writeheader()
        for sleeve, weight, symbol in rows:
            writer.writerow({"sleeve_name": sleeve, "target_weight": weight, "broker_symbol": symbol})


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


if __name__ == "__main__":
    raise SystemExit(main())
