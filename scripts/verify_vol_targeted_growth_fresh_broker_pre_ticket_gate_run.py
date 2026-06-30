from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run as module  # noqa: E402
from trading_bot.research.vol_targeted_growth_broker_position_comparison import (  # noqa: E402
    ReadonlyPositionSnapshot,
)


FALSE_FLAGS = [
    "market_data_refreshed",
    "yfinance_called",
    "ticket_instance_created",
    "executable_ticket_created",
    "order_instructions_created",
    "order_values_populated",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
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

FORBIDDEN_SOURCE_TOKENS = [
    "submit_order(",
    "cancel_order(",
    "replace_order(",
    "MarketOrderRequest",
    "LimitOrderRequest",
    "StopOrderRequest",
    "sqlite3",
    "send_discord",
    "send_telegram",
    "TaskScheduler",
    "schedule_task",
    "cron",
]


def main() -> int:
    failures: list[str] = []
    verify_commands_registered(failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(failures)
    verify_vps_daily_summary_integration(failures)
    verify_unconfirmed_fixture(failures)
    verify_confirmed_readonly_fixture(failures)

    if failures:
        print("Volatility-targeted fresh broker pre-ticket gate run verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted fresh broker pre-ticket gate run verification passed.")
    print("Verified confirmation gate, mocked read-only broker context, no ticket values, false approvals, and daily summary integration.")
    return 0


def verify_commands_registered(failures: list[str]) -> None:
    bot_source = read_text(ROOT / "bot.py")
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    for command in [
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
        "--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
    ]:
        if command not in bot_source:
            failures.append(f"bot.py missing command: {command}")
        if command not in inventory_source:
            failures.append(f"command inventory missing command: {command}")
    if "--confirm-readonly-alpaca-check" not in bot_source:
        failures.append("bot.py missing explicit read-only confirmation flag for pre-ticket gate run")


def verify_outputs_ignored(failures: list[str]) -> None:
    for path in module.OUTPUT_FILES.values():
        result = subprocess.run(
            ["git", "check-ignore", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_boundaries(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_fresh_broker_pre_ticket_gate_run.py")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"pre-ticket gate run source contains forbidden token: {token}")
    for phrase in [
        "confirm_readonly_alpaca_check",
        "load_readonly_broker_positions",
        "paper_positions_read_readonly",
        "readonly_confirmation_missing",
        "ticket_values_not_approved_after_readonly_context",
        "order_values_populated",
        "orders_submitted",
        "execution_approved",
        "scheduling_approved",
    ]:
        if phrase not in source:
            failures.append(f"pre-ticket gate run source missing safety phrase: {phrase}")


def verify_vps_daily_summary_integration(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py")
    for phrase in [
        "VOL_FRESH_BROKER_PRE_TICKET_GATE_RUN_SUMMARY_PATH",
        "Volatility fresh broker pre-ticket gate run:",
        "vol_fresh_broker_pre_ticket_gate_run_status_lines",
        "vol_fresh_broker_pre_ticket_gate_run_warning: monitor only;",
    ]:
        if phrase not in source:
            failures.append(f"VPS daily summary missing fresh broker pre-ticket gate run phrase: {phrase}")


def verify_unconfirmed_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = module.generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run(
            root,
            confirm_readonly_alpaca_check=False,
        )
        code, lines = module.show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run(root)
        if code != 0:
            failures.append("show command failed after unconfirmed fixture generation")
        output = "\n".join(lines + result.summary_lines)
        for phrase in [
            module.UNCONFIRMED_STATUS,
            "readonly_confirmation_status=missing",
            "broker_position_read_status=readonly_confirmation_missing",
            "position_symbol_count_if_readonly=0",
            "qqq_position_quantity_if_readonly=unavailable",
            "ticket_instance_created=false",
            "order_values_populated=false",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"unconfirmed fixture output missing phrase: {phrase}")
        verify_false_flags(result.summary_rows, failures, context="unconfirmed summary")
        if flag_value(result.summary_rows, "fresh_broker_pre_ticket_gate_run") != "False":
            failures.append("unconfirmed fixture must not mark the broker gate as run")
        if flag_value(result.summary_rows, "broker_positions_read") != "False":
            failures.append("unconfirmed fixture must not read broker positions")
        assert_outputs_exist(result.output_paths, failures)


def verify_confirmed_readonly_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        original = module.load_readonly_broker_positions
        module.load_readonly_broker_positions = lambda _root: ReadonlyPositionSnapshot(
            status="paper_positions_read_readonly",
            positions_by_symbol={"QQQ": "1"},
            alpaca_called=True,
            paper_positions_read=True,
        )
        try:
            result = module.generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run(
                root,
                confirm_readonly_alpaca_check=True,
            )
        finally:
            module.load_readonly_broker_positions = original
        code, lines = module.show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run(root)
        if code != 0:
            failures.append("show command failed after confirmed fixture generation")
        output = "\n".join(lines + result.summary_lines)
        for phrase in [
            module.CONFIRMED_STATUS,
            "readonly_confirmation_status=confirmed",
            "broker_position_read_status=paper_positions_read_readonly",
            "position_symbol_count_if_readonly=1",
            "qqq_position_quantity_if_readonly=1",
            "largest_blocker=ticket_values_not_approved_after_readonly_context",
            "ticket_instance_created=false",
            "order_values_populated=false",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"confirmed fixture output missing phrase: {phrase}")
        verify_false_flags(result.summary_rows, failures, context="confirmed summary")
        for flag in ["alpaca_called", "alpaca_readonly", "readonly_alpaca_check_run", "broker_positions_read", "paper_positions_read", "fresh_broker_pre_ticket_gate_run"]:
            if flag_value(result.summary_rows, flag) != "True":
                failures.append(f"confirmed fixture should mark read-only flag true: {flag}")
        assert_outputs_exist(result.output_paths, failures)


def verify_false_flags(rows: list[dict[str, object]], failures: list[str], *, context: str) -> None:
    for flag in FALSE_FLAGS:
        if flag_value(rows, flag) != "False":
            failures.append(f"{context} flag must be False: {flag}")


def assert_outputs_exist(output_paths: dict[str, Path], failures: list[str]) -> None:
    for name, path in output_paths.items():
        if not path.exists():
            failures.append(f"fixture did not write {name}: {path}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_summary.csv",
        {
            "final_pre_ticket_gate_run_readiness_decision": "READY_TO_REQUEST_EXPLICIT_READONLY_ALPACA_APPROVAL",
        },
    )
    write_summary(
        data / "vol_targeted_growth_fresh_broker_pre_ticket_gate_design_summary.csv",
        {"final_pre_ticket_gate_design_decision": "FRESH_BROKER_PRE_TICKET_GATE_DESIGNED_NOT_RUN"},
    )
    write_summary(
        data / "vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv",
        {"final_ticket_instance_design_decision": "NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES"},
    )


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value", "details"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value, "details": "fixture"})


def flag_value(rows: list[dict[str, object]], flag: str) -> str:
    for row in rows:
        if flag in row:
            return str(row.get(flag, "")).strip()
    return ""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
