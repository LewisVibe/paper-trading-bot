from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.qqq100_repeat_alignment_workflow_design import (  # noqa: E402
    BIGGEST_BLOCKER,
    FINAL_DESIGN_STATUS,
    OUTPUT_FILES,
    RECOMMENDED_NEXT_STEP,
    generate_qqq100_repeat_alignment_workflow_design,
    show_qqq100_repeat_alignment_workflow_design,
)


EXPECTED_OUTPUTS = [
    "data/qqq100_repeat_alignment_workflow_design.csv",
    "data/qqq100_repeat_alignment_workflow_states.csv",
    "data/qqq100_repeat_alignment_workflow_blockers.csv",
    "data/qqq100_repeat_alignment_workflow_checklist.csv",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "qqq100_repeat_alignment_workflow_design.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_module_boundaries(module_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)

    if failures:
        print("QQQ100 repeat/alignment workflow design verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 repeat/alignment workflow design verification passed.")
    print("Verified saved-output-only design, QQQ-only scope, one-share cap, no duplicate-buy design, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--qqq100-repeat-alignment-workflow-design",
        "--show-qqq100-repeat-alignment-workflow-design",
        "generate_qqq100_repeat_alignment_workflow_design",
        "show_qqq100_repeat_alignment_workflow_design",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing command token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    for expected in EXPECTED_OUTPUTS:
        if expected not in [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_module_boundaries(module_source: str, failures: list[str]) -> None:
    required = [
        "STRATEGY_NAME = \"qqq_100_trend_gate\"",
        "TICKER = \"QQQ\"",
        "MAX_QQQ_PAPER_POSITION = \"1\"",
        "possible_manual_open_long_candidate",
        "aligned_long_no_action",
        "over_allocated_manual_review_required",
        "aligned_flat_no_action",
        "possible_manual_flatten_review",
        "block_repeat_workflow",
        "block_due_to_open_order",
        "block_due_to_recent_order_cooldown",
        "block_due_to_market_status",
        "block_due_to_broker_read_failure",
        "No extra buy allowed",
        "No automatic sell or flatten implementation yet",
        "high_growth_and_crypto_excluded",
        "repeat_execution_approved",
        "followup_order_approved",
        "scheduling_approved",
        "live_trading_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"design module missing required design token: {token}")

    forbidden = [
        "TradingClient",
        "GetOrdersRequest",
        "get_all_positions",
        "submit_order",
        "MarketOrderRequest",
        "cancel_order",
        "replace_order",
        "insert_trade_log",
        "send_discord_alert",
        "send_telegram",
        "import yfinance",
        "yf.download",
        "download(",
        "create_scheduled_task",
        "subprocess.run",
        "automation_update",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"design module must not contain runtime/scheduling token: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    design_route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--qqq100-repeat-alignment-workflow-design"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in design_route or "run_paper_order_test" in design_route:
        failures.append("repeat/alignment design route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--qqq100-repeat-alignment-workflow-design" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by the design command")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data" / "qqq100_preview_signal_pack.csv", ["strategy_name", "ticker", "desired_position"], [["qqq_100_trend_gate", "QQQ", "long"]])
        write_fixture(root / "data" / "qqq100_paper_postcheck.csv", ["position_status", "position_quantity_abs", "alignment_state"], [["paper_position_long", "1", "aligned_long"]])
        write_fixture(
            root / "data" / "paper_execution_state_summary.csv",
            ["summary_name", "summary_value"],
            [
                ["final_state_summary_status", "paper_execution_milestone_recorded"],
                ["qqq100_alignment_status", "qqq100_aligned_long_confirmed"],
            ],
        )
        result = generate_qqq100_repeat_alignment_workflow_design(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")
        if result.design_rows[0].get("final_design_status") != FINAL_DESIGN_STATUS:
            failures.append("final design status should be qqq100_repeat_alignment_design_created")
        if result.design_rows[0].get("biggest_blocker") != BIGGEST_BLOCKER:
            failures.append("biggest blocker should require separate manual approval")
        if result.design_rows[0].get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
            failures.append("recommended next step should require design review before command changes")

        labels = {row.get("workflow_label") for row in result.state_rows}
        for expected in [
            "possible_manual_open_long_candidate",
            "aligned_long_no_action",
            "over_allocated_manual_review_required",
            "aligned_flat_no_action",
            "possible_manual_flatten_review",
            "block_repeat_workflow",
            "block_due_to_open_order",
            "block_due_to_recent_order_cooldown",
            "block_due_to_market_status",
            "block_due_to_broker_read_failure",
        ]:
            if expected not in labels:
                failures.append(f"missing workflow state label: {expected}")

        aligned_row = next(row for row in result.state_rows if row.get("workflow_label") == "aligned_long_no_action")
        if str(aligned_row.get("blocked_state", "")).lower() != "false" or "No extra buy allowed" not in str(aligned_row.get("design_rule", "")):
            failures.append("already-long-one state should be no-action and explicitly block duplicate buy")
        flatten_row = next(row for row in result.state_rows if row.get("workflow_label") == "possible_manual_flatten_review")
        if str(flatten_row.get("allowed_future_state", "")).lower() != "false":
            failures.append("desired flat while long should be manual flatten review only, not allowed")

        for collection in [result.design_rows, result.state_rows, result.blocker_rows, result.checklist_rows]:
            for row in collection:
                for flag in [
                    "orders_created",
                    "orders_submitted",
                    "orders_cancelled",
                    "orders_replaced",
                    "alpaca_called",
                    "yfinance_called",
                    "sqlite_trade_log_written",
                    "discord_alert_sent",
                    "telegram_alert_sent",
                    "execution_approved",
                    "general_execution_approved",
                    "qqq100_execution_approved",
                    "followup_order_approved",
                    "repeat_execution_approved",
                    "scheduling_approved",
                    "live_trading_approved",
                ]:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false in design outputs")
        code, lines = show_qqq100_repeat_alignment_workflow_design(root)
        if code != 0 or not any(FINAL_DESIGN_STATUS in line for line in lines):
            failures.append("saved display should show final design status")


def write_fixture(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index == -1:
        return ""
    end_index = source.find(end, start_index + len(start))
    if end_index == -1:
        return source[start_index:]
    return source[start_index:end_index]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
