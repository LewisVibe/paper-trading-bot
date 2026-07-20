from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_checkpoint import (  # noqa: E402
    FINAL_DECISION,
    FINAL_STATUS,
    OUTPUT_FILES,
    QUALITY_BLOCKED_DECISION,
    QUALITY_OUTPUT_FILES,
    QUALITY_PASS_DECISION,
    QUALITY_PASS_STATUS,
    generate_vol_targeted_growth_non_submitting_ticket_instance_checkpoint,
    generate_vol_targeted_growth_non_submitting_ticket_instance_quality_gate,
    show_vol_targeted_growth_non_submitting_ticket_instance_checkpoint,
    show_vol_targeted_growth_non_submitting_ticket_instance_quality_gate,
)


COMMANDS = [
    "--vol-targeted-growth-non-submitting-ticket-instance-checkpoint",
    "--show-vol-targeted-growth-non-submitting-ticket-instance-checkpoint",
    "--vol-targeted-growth-non-submitting-ticket-instance-quality-gate",
    "--show-vol-targeted-growth-non-submitting-ticket-instance-quality-gate",
]

FALSE_FLAGS = [
    "ticket_instance_created",
    "ticket_creation_approved",
    "broker_ready_order_values_populated",
    "order_values_populated",
    "order_instructions_created",
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

FORBIDDEN_SOURCE_TOKENS = [
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
]

PROTECTED_FIELDS = {
    "order_side",
    "order_quantity",
    "order_type",
    "time_in_force",
    "account_reference",
    "broker_order_id",
    "submit_instruction",
}


def main() -> int:
    failures: list[str] = []
    verify_commands_registered(failures)
    verify_outputs_ignored(failures)
    verify_source_safety(failures)
    verify_fixture_output(failures)
    if failures:
        print("Volatility-targeted non-submitting ticket-instance checkpoint verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted non-submitting ticket-instance checkpoint verification passed.")
    print("Verified checkpoint output, blank order fields, false approvals, and no broker/order/scheduling calls.")
    return 0


def verify_commands_registered(failures: list[str]) -> None:
    parser_source = read_text(ROOT / "trading_bot" / "cli" / "parser.py")
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    for command in COMMANDS:
        if command not in parser_source:
            failures.append(f"CLI parser missing command: {command}")
        if command not in inventory_source:
            failures.append(f"command inventory missing command: {command}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for path in [*OUTPUT_FILES.values(), *QUALITY_OUTPUT_FILES.values()]:
        result = subprocess.run(["git", "check-ignore", str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            failures.append(f"expected output is not ignored by git: {path}")


def verify_source_safety(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot/research/vol_targeted_growth_non_submitting_ticket_instance_checkpoint.py")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"checkpoint source contains forbidden token: {token}")
    for phrase in [
        "NON_SUBMITTING_TICKET_INSTANCE_CHECKPOINT_CREATED_NO_ORDER_VALUES",
        "ticket_instance_checkpoint_created",
        "ticket_instance_created",
        "broker_ready_order_values_populated",
        "order_values_populated",
        "orders_submitted",
        "execution_approved",
        "scheduling_approved",
        "NON_SUBMITTING_TICKET_INSTANCE_QUALITY_GATE_PASSED_NO_ORDER_VALUES",
        "pre_ticket_quality_gate_passed",
        "protected_order_fields_blank",
    ]:
        if phrase not in source:
            failures.append(f"checkpoint source missing safety phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_non_submitting_ticket_instance_checkpoint(root)
        code, lines = show_vol_targeted_growth_non_submitting_ticket_instance_checkpoint(root)
        if code != 0:
            failures.append("show command failed after fixture generation")
        output = "\n".join(result.summary_lines + lines)
        for phrase in [
            FINAL_STATUS,
            FINAL_DECISION,
            "ticket_instance_checkpoint_created=True",
            "ticket_instance_created=False",
            "ticket_creation_approved=False",
            "review_quantities_created=True",
            "review_quantity_estimate_count=4",
            "review_quantity_quality_gate_passed=True",
            "broker_ready_order_values_populated=False",
            "order_values_populated=False",
            "order_instructions_created=False",
            "orders_submitted=false",
            "execution_approved=false",
            "paper_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if phrase not in output:
                failures.append(f"fixture output missing phrase: {phrase}")
        verify_summary_rows(result.summary_rows, failures)
        verify_ticket_rows(result.ticket_rows, failures)
        verify_quantity_context(result.ticket_rows, failures)
        verify_quality_gate_output(root, failures)
        verify_quality_gate_blocks_missing_inputs(failures)
        for path in result.output_paths.values():
            if not path.exists():
                failures.append(f"expected output missing: {path}")


def verify_summary_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    if summary_value(rows, "final_non_submitting_ticket_instance_checkpoint_status") != FINAL_STATUS:
        failures.append("summary final status is incorrect")
    if summary_value(rows, "final_non_submitting_ticket_instance_checkpoint_decision") != FINAL_DECISION:
        failures.append("summary final decision is incorrect")
    if summary_value(rows, "ticket_instance_checkpoint_created") != "True":
        failures.append("summary should create only a checkpoint artifact")
    if summary_value(rows, "review_quantities_created") != "True":
        failures.append("summary should carry review quantities when saved evidence exists")
    if summary_value(rows, "review_quantity_estimate_count") != "4":
        failures.append("summary should count four review quantity estimate rows")
    if summary_value(rows, "review_quantity_quality_gate_passed") != "True":
        failures.append("summary should carry the review quantity quality gate state")
    for flag in FALSE_FLAGS:
        if summary_or_flag_value(rows, flag) != "False":
            failures.append(f"summary flag must be False: {flag}")


def verify_ticket_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    fields = {str(row.get("ticket_field", "")) for row in rows}
    missing = PROTECTED_FIELDS - fields
    if missing:
        failures.append(f"ticket checkpoint missing protected fields: {sorted(missing)}")
    for row in rows:
        field = str(row.get("ticket_field", ""))
        if field in PROTECTED_FIELDS and str(row.get("field_value", "")).strip():
            failures.append(f"protected field must stay blank: {field}")
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).strip() != "False":
                failures.append(f"ticket row flag must be False for {field}: {flag}")


def verify_quantity_context(rows: list[dict[str, object]], failures: list[str]) -> None:
    fields = {str(row.get("ticket_field", "")): row for row in rows}
    for field in [
        "review_quantity_estimates_decision",
        "review_quantity_quality_gate_decision",
        "review_quantity_estimate_count",
        "review_quantity_symbols",
        "review_share_quantity_estimates",
    ]:
        if field not in fields:
            failures.append(f"ticket checkpoint missing review quantity context: {field}")
    estimates = str(fields.get("review_share_quantity_estimates", {}).get("field_value", ""))
    for symbol in ["QQQ", "MGK", "IBIT", "SGOV"]:
        if symbol not in estimates:
            failures.append(f"review share estimate context missing symbol: {symbol}")
    if fields.get("review_share_quantity_estimates", {}).get("field_status") != "review_context":
        failures.append("review share estimates must stay review_context, not an order field")


def verify_quality_gate_output(root: Path, failures: list[str]) -> None:
    result = generate_vol_targeted_growth_non_submitting_ticket_instance_quality_gate(root)
    code, lines = show_vol_targeted_growth_non_submitting_ticket_instance_quality_gate(root)
    if code != 0:
        failures.append("quality gate show command failed after fixture generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        QUALITY_PASS_STATUS,
        QUALITY_PASS_DECISION,
        "pre_ticket_quality_gate_passed=True",
        "review_inputs_complete=True",
        "protected_order_fields_blank=True",
        "broker_ready_order_values_populated=False",
        "order_values_populated=False",
        "order_instructions_created=False",
        "orders_submitted=false",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
    ]:
        if phrase not in output:
            failures.append(f"quality gate fixture output missing phrase: {phrase}")
    if summary_value(result.summary_rows, "largest_blocker") != "broker_ready_ticket_values_still_not_approved":
        failures.append("quality gate should keep broker-ready ticket values blocked even when quality passes")
    for flag in FALSE_FLAGS:
        if summary_or_flag_value(result.summary_rows, flag) != "False":
            failures.append(f"quality gate summary flag must be False: {flag}")
    for path in result.output_paths.values():
        if not path.exists():
            failures.append(f"expected quality gate output missing: {path}")


def verify_quality_gate_blocks_missing_inputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        generate_vol_targeted_growth_non_submitting_ticket_instance_checkpoint(root)
        (root / "data" / "vol_targeted_growth_review_quantity_quality_gate_summary.csv").unlink()
        generate_vol_targeted_growth_non_submitting_ticket_instance_checkpoint(root)
        result = generate_vol_targeted_growth_non_submitting_ticket_instance_quality_gate(root)
        if summary_value(result.summary_rows, "final_non_submitting_ticket_instance_quality_decision") != QUALITY_BLOCKED_DECISION:
            failures.append("quality gate should block when review quality input is missing")
        if summary_value(result.summary_rows, "pre_ticket_quality_gate_passed") != "False":
            failures.append("quality gate should not pass with missing review input")
        if summary_value(result.summary_rows, "missing_review_input_count") == "0":
            failures.append("quality gate should count missing review inputs")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_non_submitting_ticket_creation_readiness_summary.csv",
        {
            "final_non_submitting_ticket_creation_readiness_decision": "READY_TO_DISCUSS_NON_SUBMITTING_TICKET_CREATION_NOT_APPROVED",
            "ticket_creation_discussion_ready": "True",
            "ticket_creation_approved": "False",
        },
    )
    write_summary(
        data / "vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv",
        {
            "final_ticket_instance_design_decision": "NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES",
            "ticket_instance_created": "False",
        },
    )
    write_summary(
        data / "vol_targeted_growth_non_submitting_executable_ticket_values_summary.csv",
        {
            "final_non_submitting_executable_ticket_values_decision": "NON_SUBMITTING_EXECUTABLE_TICKET_VALUES_POPULATED_REVIEW_ONLY",
            "non_submitting_ticket_values_populated": "True",
            "order_values_populated": "False",
        },
    )
    write_summary(
        data / "vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_summary.csv",
        {
            "final_non_submitting_executable_ticket_values_quality_decision": "NON_SUBMITTING_EXECUTABLE_TICKET_VALUES_QUALITY_GATE_PASSED_NO_ORDER",
            "quality_gate_passed": "True",
        },
    )
    write_summary(
        data / "vol_targeted_growth_non_submitting_executable_ticket_values_manual_review_summary.csv",
        {
            "final_non_submitting_executable_ticket_values_manual_review_decision": "NON_SUBMITTING_EXECUTABLE_TICKET_VALUES_REVIEWED_NO_ORDER",
            "manual_review_completed": "True",
        },
    )
    write_summary(
        data / "vol_targeted_growth_review_quantity_estimates_summary.csv",
        {
            "final_review_quantity_estimates_decision": "REVIEW_QUANTITY_ESTIMATES_CREATED_NO_ORDER_INSTRUCTIONS",
            "review_quantities_created": "True",
            "review_quantity_row_count": "4",
        },
    )
    write_summary(
        data / "vol_targeted_growth_review_quantity_quality_gate_summary.csv",
        {
            "final_review_quantity_quality_decision": "REVIEW_QUANTITY_QUALITY_GATE_PASSED_NO_ORDER",
            "review_quantity_quality_gate_passed": "True",
        },
    )
    write_quantity_estimates(data / "vol_targeted_growth_review_quantity_estimates.csv")


def write_quantity_estimates(path: Path) -> None:
    fieldnames = [
        "sleeve_name",
        "broker_symbol",
        "target_dollars",
        "saved_price",
        "review_share_quantity_estimate",
        "quantity_estimate_status",
    ]
    rows = [
        ("qqq100_core", "QQQ", "70000.00", "500.00", "140", "review_quantity_estimate_created"),
        ("high_growth_research", "MGK", "20000.00", "300.00", "66.666666", "review_quantity_estimate_created"),
        ("crypto_research", "IBIT", "5000.00", "60.00", "83.333333", "review_quantity_estimate_created"),
        ("defensive_buffer", "SGOV", "5000.00", "100.00", "50", "review_quantity_estimate_created"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(zip(fieldnames, row, strict=True)))


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
