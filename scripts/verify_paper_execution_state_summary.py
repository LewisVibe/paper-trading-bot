from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.paper_execution_state_summary import (  # noqa: E402
    OUTPUT_FILES,
    generate_paper_execution_state_summary,
    show_paper_execution_state_summary,
)


EXPECTED_OUTPUTS = [
    "data/paper_execution_state_summary.csv",
    "data/paper_execution_state_positions.csv",
    "data/paper_execution_state_milestones.csv",
    "data/paper_execution_state_blockers.csv",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "paper_execution_state_summary.py")

    verify_command_registration(bot_source, failures)
    verify_saved_output_only_source(module_source, failures)
    verify_outputs_ignored(failures)
    verify_fixture_recognition(failures)
    verify_no_new_execution_command(bot_source, failures)
    verify_docs_mentions(failures)

    if failures:
        print("Paper execution state summary verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper execution state summary verification passed.")
    print("Verified saved-output-only AAPL/QQQ milestone recognition and false follow-up/repeat/scheduling approvals.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--paper-execution-state-summary",
        "--show-paper-execution-state-summary",
        "generate_paper_execution_state_summary",
        "show_paper_execution_state_summary",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing command registration token: {token}")


def verify_saved_output_only_source(module_source: str, failures: list[str]) -> None:
    required = [
        "data/paper_order_smoke_test_postcheck.csv",
        "data/qqq100_paper_execution_result.csv",
        "data/qqq100_paper_postcheck.csv",
        "data/qqq100_action_preview.csv",
        "report_only",
        "followup_order_approved",
        "repeat_execution_approved",
        "scheduling_approved",
        "alpaca_called",
        "high-growth",
        "crypto",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"summary module missing required token: {token}")

    forbidden = [
        "TradingClient",
        "alpaca.trading",
        "yfinance",
        "download_",
        "get_alpaca_positions",
        "get_all_positions",
        "get_open_orders",
        "submit_order",
        "submit_alpaca_order",
        "MarketOrderRequest",
        "insert_trade_log",
        "send_discord_alert",
        "send_telegram",
        "load_config",
        "schtasks",
        "CronTrigger",
        "subprocess",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"summary module must remain saved-output-only; found token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    for output in EXPECTED_OUTPUTS:
        if not output.startswith("data/") or "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored by data/*: {output}")


def verify_fixture_recognition(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "paper_order_smoke_test_postcheck.csv",
            [
                {
                    "check_name": "final_postcheck_status",
                    "final_postcheck_status": "postcheck_order_observed_filled_manual_review",
                    "ticker": "AAPL",
                    "recent_order_match_found": "true",
                    "recent_order_match_status": "filled",
                    "open_order_summary": "open_order_count_for_ticker=0",
                    "position_summary": "position_direction=long; quantity_abs=2",
                    "followup_order_approved": "False",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                }
            ],
        )
        write_csv(
            data / "qqq100_paper_execution_result.csv",
            [
                {
                    "strategy_name": "qqq_100_trend_gate",
                    "ticker": "QQQ",
                    "desired_position": "long",
                    "current_position_status": "paper_position_flat",
                    "intended_action": "buy_1",
                    "order_side": "buy",
                    "quantity": "1",
                    "order_status": "filled",
                    "decision_status": "qqq100_paper_order_ready",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                }
            ],
        )
        write_csv(
            data / "qqq100_paper_execution_summary.csv",
            [{"summary_name": "order_event", "summary_value": "order_submitted"}],
        )
        write_csv(
            data / "qqq100_action_preview.csv",
            [
                {
                    "strategy_name": "qqq_100_trend_gate",
                    "ticker": "QQQ",
                    "desired_position": "long",
                    "current_position_status": "paper_position_long",
                    "current_position_quantity_if_readonly": "1",
                    "alignment_state": "aligned_long",
                    "non_executable_preview_action": "no_action_preview_only",
                    "orders_created": "False",
                    "orders_submitted": "False",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                }
            ],
        )
        write_csv(
            data / "qqq100_preview_signal_pack.csv",
            [
                {
                    "strategy_name": "qqq_100_trend_gate",
                    "ticker": "QQQ",
                    "desired_position": "long",
                    "data_status": "ok",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                }
            ],
        )
        result = generate_paper_execution_state_summary(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_state_summary_status") != "paper_execution_milestone_recorded":
            failures.append("fixture should produce paper_execution_milestone_recorded")
        if summary.get("aapl_smoke_test_status") != "aapl_smoke_test_filled_confirmed":
            failures.append("fixture should recognise filled AAPL smoke-test postcheck")
        if summary.get("qqq100_manual_execution_status") != "qqq100_manual_paper_execution_filled_confirmed":
            failures.append("fixture should recognise filled QQQ100 manual execution")
        if summary.get("qqq100_alignment_status") != "qqq100_aligned_long_confirmed":
            failures.append("fixture should recognise QQQ100 aligned_long action preview")
        for collection in [result.summary_rows, result.position_rows, result.milestone_rows, result.blocker_rows]:
            for row in collection:
                for flag in [
                    "execution_approved",
                    "general_execution_approved",
                    "qqq100_execution_approved",
                    "followup_order_approved",
                    "repeat_execution_approved",
                    "scheduling_approved",
                    "orders_created",
                    "orders_submitted",
                    "orders_cancelled",
                    "sqlite_trade_log_written",
                    "discord_alert_sent",
                    "telegram_alert_sent",
                    "alpaca_called",
                ]:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false in all output rows")
        code, lines = show_paper_execution_state_summary(root)
        if code != 0 or not any("paper_execution_milestone_recorded" in line for line in lines):
            failures.append("saved display should show generated milestone summary")
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected output missing in fixture run: {path}")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "paper_order_smoke_test_postcheck.csv",
            [
                {
                    "final_postcheck_status": "postcheck_order_observed_filled_manual_review",
                    "ticker": "AAPL",
                    "recent_order_match_found": "true",
                    "recent_order_match_status": "filled",
                    "position_summary": "position_direction=long; quantity_abs=2",
                }
            ],
        )
        write_csv(
            data / "qqq100_paper_postcheck.csv",
            [
                {
                    "final_postcheck_status": "qqq100_postcheck_order_observed_filled_aligned_long",
                    "strategy_name": "qqq_100_trend_gate",
                    "ticker": "QQQ",
                    "desired_position": "long",
                    "recent_order_match_found": "true",
                    "recent_order_match_status": "filled",
                    "position_status": "paper_position_long",
                    "position_quantity_abs": "1",
                    "alignment_state": "aligned_long",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                }
            ],
        )
        write_csv(
            data / "qqq100_preview_signal_pack.csv",
            [{"strategy_name": "qqq_100_trend_gate", "ticker": "QQQ", "desired_position": "long"}],
        )
        result = generate_paper_execution_state_summary(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_state_summary_status") != "paper_execution_milestone_recorded":
            failures.append("postcheck fallback should produce paper_execution_milestone_recorded")
        if summary.get("qqq100_manual_execution_status") != "qqq100_manual_paper_execution_filled_confirmed":
            failures.append("postcheck fallback should recognise filled QQQ100 execution")
        if summary.get("qqq100_alignment_status") != "qqq100_aligned_long_confirmed":
            failures.append("postcheck fallback should recognise aligned_long")


def verify_no_new_execution_command(bot_source: str, failures: list[str]) -> None:
    new_order_capable = [
        "--execute-qqq100-paper",
        "--paper-order-test",
        "--execute-slow-sma-paper",
    ]
    # This verifier is for a display/report command only. It should add no new
    # order-capable flag beyond the ones already present in the codebase.
    for token in ["--paper-execution-state-summary", "--show-paper-execution-state-summary"]:
        if token not in bot_source:
            failures.append(f"missing state summary token: {token}")
    state_blocks = bot_source.count("--paper-execution-state-summary")
    if state_blocks < 2:
        failures.append("paper execution state summary should be registered in early route and argparse")
    if "--execute-qqq100-paper" not in bot_source:
        failures.append("existing QQQ100 execution command registration should remain present")
    for token in ["high_growth", "crypto"]:
        block = function_block(bot_source, "if args.paper_execution_state_summary:", "if args.high_growth_stock_lab:")
        if token in block:
            failures.append(f"state summary command must not wire {token} to execution")


def verify_docs_mentions(failures: list[str]) -> None:
    docs = "\n".join(
        read_text(ROOT / path)
        for path in [
            "README.md",
            "docs/CURRENT_STATE.md",
            "docs/V2_RESEARCH_CHECKPOINT.md",
            "docs/HERMES_TASK_BOARD.md",
        ]
    )
    for token in [
        "--paper-execution-state-summary",
        "--show-paper-execution-state-summary",
        "paper_execution_state_summary.csv",
    ]:
        if token not in docs:
            failures.append(f"docs missing paper execution state summary token: {token}")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def function_block(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index == -1:
        return ""
    end_index = source.find(end, start_index + len(start))
    if end_index == -1:
        return source[start_index:]
    return source[start_index:end_index]


if __name__ == "__main__":
    raise SystemExit(main())
