from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_strategy_monitor import (  # noqa: E402
    ACTIVE_PAPER_SLEEVE,
    BIGGEST_BLOCKER,
    FINAL_MONITOR_STATUS,
    OUTPUT_FILES,
    RECOMMENDED_NEXT_STEP,
    generate_multi_sleeve_strategy_monitor,
    show_multi_sleeve_strategy_monitor,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_strategy_monitor.csv",
    "data/multi_sleeve_strategy_sleeves.csv",
    "data/multi_sleeve_strategy_positions.csv",
    "data/multi_sleeve_strategy_blockers.csv",
    "data/multi_sleeve_strategy_next_steps.csv",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_strategy_monitor.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)

    if failures:
        print("Multi-sleeve strategy monitor verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Multi-sleeve strategy monitor verification passed.")
    print("Verified saved-output-only monitor, QQQ100-only active paper sleeve, research-only sleeves, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-strategy-monitor",
        "--show-multi-sleeve-strategy-monitor",
        "generate_multi_sleeve_strategy_monitor",
        "show_multi_sleeve_strategy_monitor",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing multi-sleeve command token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, failures: list[str]) -> None:
    required = [
        "qqq100_core_trend_sleeve",
        "defensive_etf_research_sleeve",
        "high_growth_stock_research_sleeve",
        "crypto_research_sleeve",
        "cash_or_no_position_sleeve",
        "qqq_100_trend_gate",
        "QQQ only",
        "1 share",
        "duplicate buys blocked",
        "repeat execution not approved",
        "scheduling not approved",
        "research_or_preview_only",
        "research_only",
        "design_only",
        "qqq100_is_current_only_active_paper_sleeve",
        "high_growth_and_qqq_overlap_risk",
        "crypto_volatility_sleeve_not_ready",
        "defensive_sleeve_not_validated_for_execution",
        "sleeve_allocation_policy_missing",
        "portfolio_position_limit_not_generalised",
        "future_manual_review_required",
        "high_growth_execution_approved",
        "crypto_execution_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"monitor module missing required design token: {token}")

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
        "subprocess.run",
        "create_scheduled_task",
        "automation_update",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"monitor module must not contain runtime/scheduling token: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    monitor_route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--multi-sleeve-strategy-monitor"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in monitor_route or "run_paper_order_test" in monitor_route:
        failures.append("multi-sleeve route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--multi-sleeve-strategy-monitor" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by the monitor command")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data" / "qqq100_paper_postcheck.csv", ["position_status", "position_quantity_abs", "alignment_state"], [["paper_position_long", "1", "aligned_long"]])
        write_fixture(
            root / "data" / "paper_execution_state_summary.csv",
            ["summary_name", "summary_value"],
            [
                ["final_state_summary_status", "paper_execution_milestone_recorded"],
                ["qqq100_alignment_status", "qqq100_aligned_long_confirmed"],
            ],
        )
        write_fixture(root / "data" / "qqq100_repeat_alignment_workflow_design.csv", ["final_design_status", "proposed_max_qqq_paper_position"], [["qqq100_repeat_alignment_design_created", "1"]])
        result = generate_multi_sleeve_strategy_monitor(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        monitor = result.monitor_rows[0]
        if monitor.get("final_monitor_status") != FINAL_MONITOR_STATUS:
            failures.append("final monitor status should be multi_sleeve_monitor_created")
        if monitor.get("active_paper_sleeve_count") != "1":
            failures.append("active paper sleeve count should be 1 when QQQ long 1 aligned_long is saved")
        if monitor.get("active_paper_sleeve") != ACTIVE_PAPER_SLEEVE:
            failures.append("active paper sleeve should be qqq100_core_trend_sleeve")
        if monitor.get("biggest_blocker") != BIGGEST_BLOCKER:
            failures.append("biggest blocker should require sleeve allocation manual review")
        if monitor.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
            failures.append("recommended next step should be research scoreboard before new execution wiring")

        sleeve_by_name = {row["sleeve_name"]: row for row in result.sleeve_rows}
        if sleeve_by_name[ACTIVE_PAPER_SLEEVE]["current_max_paper_position"] != "1 share":
            failures.append("QQQ100 max paper position should remain 1 share")
        for name in ["defensive_etf_research_sleeve", "high_growth_stock_research_sleeve", "crypto_research_sleeve"]:
            if name not in sleeve_by_name:
                failures.append(f"missing sleeve row: {name}")
            elif "execution blocked" not in sleeve_by_name[name]["execution_boundary"]:
                failures.append(f"{name} should remain execution blocked")
        if sleeve_by_name["cash_or_no_position_sleeve"]["sleeve_status"] != "design_only":
            failures.append("cash/no-position sleeve should be design_only")

        for collection in [result.monitor_rows, result.sleeve_rows, result.position_rows, result.blocker_rows, result.next_step_rows]:
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
                    "high_growth_execution_approved",
                    "crypto_execution_approved",
                ]:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false in multi-sleeve outputs")
        code, lines = show_multi_sleeve_strategy_monitor(root)
        if code != 0 or not any(FINAL_MONITOR_STATUS in line for line in lines):
            failures.append("saved display should show final monitor status")


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
