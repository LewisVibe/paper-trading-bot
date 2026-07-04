from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_sleeve_mapping_action_proposal import (  # noqa: E402
    ACTION_DECISION,
    ACTION_OUTPUTS,
    MAPPING_DECISION,
    MAPPING_OUTPUTS,
    generate_vol_targeted_growth_broker_ready_action_proposal,
    generate_vol_targeted_growth_sleeve_symbol_mapping,
    show_vol_targeted_growth_broker_ready_action_proposal,
    show_vol_targeted_growth_sleeve_symbol_mapping,
)


COMMANDS = [
    "--vol-targeted-growth-sleeve-symbol-mapping",
    "--show-vol-targeted-growth-sleeve-symbol-mapping",
    "--vol-targeted-growth-broker-ready-action-proposal",
    "--show-vol-targeted-growth-broker-ready-action-proposal",
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
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
]

ORDER_VALUE_FIELDS = ["order_side", "order_quantity", "order_type", "time_in_force", "account_reference", "broker_order_id"]


def main() -> int:
    failures: list[str] = []
    verify_commands_registered(failures)
    verify_outputs_ignored(failures)
    verify_source_safety(failures)
    verify_fixture_outputs(failures)
    if failures:
        print("Volatility-targeted sleeve mapping/action proposal verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted sleeve mapping/action proposal verification passed.")
    print("Verified real-symbol review mapping, blank order fields, false approvals, and no broker/order/scheduling calls.")
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
    for path in [*MAPPING_OUTPUTS.values(), *ACTION_OUTPUTS.values()]:
        result = subprocess.run(["git", "check-ignore", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_safety(failures: list[str]) -> None:
    source = (ROOT / "trading_bot/research/vol_targeted_growth_sleeve_mapping_action_proposal.py").read_text(encoding="utf-8")
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


def verify_fixture_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        mapping = generate_vol_targeted_growth_sleeve_symbol_mapping(root)
        action = generate_vol_targeted_growth_broker_ready_action_proposal(root)
        mapping_code, mapping_lines = show_vol_targeted_growth_sleeve_symbol_mapping(root)
        action_code, action_lines = show_vol_targeted_growth_broker_ready_action_proposal(root)
        if mapping_code != 0:
            failures.append("mapping display failed after generation")
        if action_code != 0:
            failures.append("action proposal display failed after generation")
        output = "\n".join(mapping.summary_lines + action.summary_lines + mapping_lines + action_lines)
        for phrase in [
            MAPPING_DECISION,
            ACTION_DECISION,
            "mapped_symbols=QQQ,MGK,IBIT,SGOV",
            "broker_symbols=QQQ,MGK,IBIT,SGOV",
            "broker_ready_action_proposal_created=True",
            "order_values_populated=False",
            "order_instructions_created=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        if len(mapping.report_rows) != 4:
            failures.append("expected four sleeve mapping rows")
        if len(action.report_rows) != 4:
            failures.append("expected four action proposal rows")
        for row in action.report_rows:
            for field in ORDER_VALUE_FIELDS:
                if str(row.get(field, "")).strip():
                    failures.append(f"order field must stay blank: {field}")
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).strip() != "False":
                    failures.append(f"action row flag must be False for {row.get('broker_symbol')}: {flag}")
        for row in mapping.summary_rows + action.summary_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).strip() != "False":
                    failures.append(f"summary flag must be False: {flag}")
        for path in [*mapping.output_paths.values(), *action.output_paths.values()]:
            if not path.exists():
                failures.append(f"expected output missing: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
