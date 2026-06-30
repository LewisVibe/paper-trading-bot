from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "vol_targeted_growth_post_gate_review.py"

COMMANDS = ["--vol-targeted-growth-post-gate-review", "--show-vol-targeted-growth-post-gate-review"]
OUTPUTS = [
    "data/vol_targeted_growth_post_gate_review.csv",
    "data/vol_targeted_growth_post_gate_review_summary.csv",
    "data/vol_targeted_growth_post_gate_review_blockers.csv",
    "data/vol_targeted_growth_post_gate_review_evidence.csv",
]

REQUIRED_TOKENS = [
    "vol_targeted_growth_post_gate_review_manual_review_required",
    "FRESH_BROKER_CONTEXT_SAVED_TICKET_VALUES_NOT_APPROVED",
    "ticket_values_not_approved_after_readonly_context",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"order_values_populated": False',
    '"order_instructions_created": False',
]

FORBIDDEN_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    "submit_order(",
    "cancel_order(",
    "replace_order(",
    "get_all_positions(",
    "get_alpaca_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "config.json",
    "yf.",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_fixture_output(failures)
    verify_dashboard_integration(failures)

    if failures:
        print("Volatility-targeted post-gate review verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted post-gate review verification passed.")
    print("Verified saved-output post-gate interpretation, false approvals, ignored outputs, and dashboard integration.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command in bot.py: {command}")
        if command not in inventory_source:
            failures.append(f"missing command in inventory verifier: {command}")
        branch = f'sys.argv[1:] == ["{command}"]'
        branch_index = bot_source.find(branch)
        if branch_index < 0:
            failures.append(f"missing early route for {command}")
        elif load_config_index >= 0 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("post-gate review module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"module missing output path: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"module contains forbidden token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(
            ["git", "check-ignore", output],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_fixture_output(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.vol_targeted_growth_post_gate_review import (  # noqa: PLC0415
        generate_vol_targeted_growth_post_gate_review,
        show_vol_targeted_growth_post_gate_review,
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_summary(
            data / "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv",
            {
                "final_pre_ticket_gate_run_status": "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_completed_readonly_manual_review_required",
                "broker_position_read_status": "paper_positions_read_readonly",
                "position_symbol_count_if_readonly": "3",
                "qqq_position_quantity_if_readonly": "1",
                "largest_blocker": "ticket_values_not_approved_after_readonly_context",
                "execution_approved": "False",
                "paper_execution_approved": "False",
                "scheduling_approved": "False",
            },
        )
        write_summary(
            data / "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_summary.csv",
            {"final_pre_ticket_gate_run_readiness_decision": "READY_TO_REQUEST_EXPLICIT_READONLY_ALPACA_APPROVAL"},
        )
        write_summary(
            data / "vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv",
            {"final_ticket_instance_design_decision": "NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES"},
        )
        result = generate_vol_targeted_growth_post_gate_review(root)
        status_code, lines = show_vol_targeted_growth_post_gate_review(root)

    output = "\n".join(result.summary_lines + lines)
    if status_code != 0:
        failures.append("post-gate display should return 0 after generation")
    for phrase in [
        "vol_targeted_growth_post_gate_review_manual_review_required",
        "FRESH_BROKER_CONTEXT_SAVED_TICKET_VALUES_NOT_APPROVED",
        "fresh_broker_context_saved_for_manual_review",
        "paper_positions_read_readonly",
        "saved_qqq_position_quantity_if_readonly=1",
        "ticket_values_not_approved_after_readonly_context",
        "order_values_populated=false",
        "order_instructions_created=false",
        "orders_submitted=false",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")


def verify_dashboard_integration(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "paper_live_go_no_go_dashboard.py")
    for phrase in [
        "vol_post_gate_review",
        "vol_targeted_growth_post_gate_review_summary.csv",
        "vol_post_gate_review_status",
        "vol_post_gate_largest_blocker",
        "vol_post_gate_saved_qqq_quantity",
        "post_gate_ticket_values_not_approved",
    ]:
        if phrase not in source:
            failures.append(f"go/no-go dashboard missing post-gate integration phrase: {phrase}")


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
