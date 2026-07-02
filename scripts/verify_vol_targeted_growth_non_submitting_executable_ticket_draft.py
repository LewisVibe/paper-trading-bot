"""Verify non-submitting executable-ticket draft remains non-executable."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_non_submitting_executable_ticket_draft import (  # noqa: E402
    DRAFT_DECISION,
    DRAFT_OUTPUTS,
    QUALITY_DECISION,
    QUALITY_OUTPUTS,
    generate_vol_targeted_growth_non_submitting_executable_ticket_draft,
    generate_vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate,
    show_vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate,
)


COMMANDS = [
    "--vol-targeted-growth-non-submitting-executable-ticket-draft",
    "--show-vol-targeted-growth-non-submitting-executable-ticket-draft",
    "--vol-targeted-growth-non-submitting-executable-ticket-draft-quality-gate",
    "--show-vol-targeted-growth-non-submitting-executable-ticket-draft-quality-gate",
]

FALSE_FLAGS = [
    "ticket_values_approved",
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
    verify_source_safety(failures)
    verify_fixture_outputs(failures)
    if failures:
        print("Non-submitting executable-ticket draft verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Non-submitting executable-ticket draft verification passed.")
    print("Verified draft artifact, quality gate, false order/execution flags, and no broker/order/scheduling calls.")
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
    for path in [*DRAFT_OUTPUTS.values(), *QUALITY_OUTPUTS.values()]:
        result = subprocess.run(["git", "check-ignore", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_safety(failures: list[str]) -> None:
    source = (ROOT / "trading_bot/research/vol_targeted_growth_non_submitting_executable_ticket_draft.py").read_text(encoding="utf-8")
    for phrase in [
        "TradingClient(",
        "MarketOrderRequest(",
        "submit_order(",
        "cancel_order(",
        "replace_order(",
        "get_all_positions",
        "sqlite3.connect",
        "send_discord_alert(",
        "send_telegram",
        "yf.",
        "import yfinance",
        "load_config(",
        "config.json",
    ]:
        if phrase in source:
            failures.append(f"source contains forbidden runtime phrase: {phrase}")


def verify_fixture_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        draft = generate_vol_targeted_growth_non_submitting_executable_ticket_draft(root)
        quality = generate_vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate(root)
        code, lines = show_vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate(root)
        if code != 0:
            failures.append("draft quality gate display failed after generation")
        output = "\n".join(draft.summary_lines + quality.summary_lines + lines)
        for phrase in [
            DRAFT_DECISION,
            QUALITY_DECISION,
            "draft_ticket_created=True",
            "quality_gate_passed=True",
            "executable_order_field_count=0",
            "forbidden_field_count=0",
            "order_instruction_field_count=0",
            "ticket_values_approved=False",
            "order_values_populated=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        if summary_value(quality.summary_rows, "quality_gate_passed") != "True":
            failures.append("quality gate should pass for non-executable draft")
        verify_false_flags(quality.summary_rows, failures)
        verify_ticket_rows(draft.ticket_rows, failures)
        for path in [*draft.output_paths.values(), *quality.output_paths.values()]:
            if not path.exists():
                failures.append(f"expected output missing: {path}")


def verify_ticket_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    fields = {str(row.get("draft_field", "")).strip().lower(): str(row.get("draft_value", "")).strip().lower() for row in rows}
    for required in ["draft_action_label", "draft_side_label", "draft_quantity_label", "draft_order_type_label", "draft_time_in_force_label", "submit_ready"]:
        if required not in fields:
            failures.append(f"missing draft field: {required}")
    for forbidden_field in ["order_side", "order_quantity", "order_type", "time_in_force", "account_id", "api_key", "secret", "token", "webhook", "broker_order_id"]:
        if forbidden_field in fields:
            failures.append(f"forbidden executable field present: {forbidden_field}")
    for forbidden_value in ["buy", "sell", "market", "limit", "day", "gtc"]:
        if forbidden_value in fields.values():
            failures.append(f"forbidden executable value present: {forbidden_value}")
    if fields.get("submit_ready") != "false":
        failures.append("submit_ready must remain False")


def verify_false_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for flag in FALSE_FLAGS:
        value = summary_or_flag_value(rows, flag)
        if value != "False":
            failures.append(f"flag must be False: {flag}={value}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_executable_ticket_draft_readiness_summary.csv",
        {
            "final_executable_ticket_draft_readiness_decision": "READY_TO_DISCUSS_NON_SUBMITTING_DRAFT_VALUES_NOT_EXECUTABLE",
            "draft_discussion_ready": "True",
        },
    )
    write_summary(
        data / "vol_targeted_growth_proposed_ticket_values_summary.csv",
        {"final_proposed_ticket_values_decision": "PROPOSED_TICKET_VALUES_CREATED_REVIEW_ONLY_NOT_EXECUTABLE"},
    )
    write_summary(
        data / "vol_targeted_growth_proposed_ticket_values_quality_gate_summary.csv",
        {
            "final_proposed_ticket_values_quality_gate_decision": "PROPOSED_TICKET_VALUES_QUALITY_GATE_PASSED_NO_EXECUTION",
            "quality_gate_passed": "True",
        },
    )
    write_summary(data / "paper_live_go_no_go_dashboard_summary.csv", {"final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"})
    write_proposed_values(data / "vol_targeted_growth_proposed_ticket_values_values.csv")


def write_proposed_values(path: Path) -> None:
    rows = [
        ("proposal_strategy", "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"),
        ("proposal_ticker_scope", "MULTI_SLEEVE"),
        ("proposal_action", "review_rebalance_to_saved_target_sleeves_only"),
        ("proposal_side", "multi_sleeve_mapping_required_not_single_side"),
        ("proposal_quantity", "component_quantities_not_set"),
        ("proposal_order_type", "market_candidate_review_only"),
        ("proposal_time_in_force", "day_candidate_review_only"),
        ("proposal_price_handling", "no_limit_or_stop_price_proposed"),
        ("saved_qqq_position_context", "1"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["proposal_field", "proposal_value"])
        writer.writeheader()
        for field, value in rows:
            writer.writerow({"proposal_field": field, "proposal_value": value})


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
