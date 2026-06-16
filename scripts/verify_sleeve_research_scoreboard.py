from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.sleeve_research_scoreboard import (  # noqa: E402
    BEST_ACTIVE_PAPER_SLEEVE,
    BIGGEST_BLOCKER,
    CODEX_EXPERIMENTAL_CANDIDATE,
    FINAL_SCOREBOARD_STATUS,
    OUTPUT_FILES,
    RECOMMENDED_NEXT_STEP,
    TOP_RESEARCH_SLEEVE,
    generate_sleeve_research_scoreboard,
    show_sleeve_research_scoreboard,
)


EXPECTED_OUTPUTS = [
    "data/sleeve_research_scoreboard.csv",
    "data/sleeve_research_candidates.csv",
    "data/sleeve_research_rankings.csv",
    "data/sleeve_research_blockers.csv",
    "data/sleeve_research_next_steps.csv",
    "data/sleeve_research_codex_experimental_sleeve.csv",
]

REQUIRED_SCORE_COLUMNS = [
    "sleeve_name",
    "candidate_name",
    "strategy_family",
    "status",
    "current_role",
    "estimated_or_observed_cagr",
    "estimated_or_observed_sharpe",
    "estimated_or_observed_max_drawdown",
    "estimated_or_observed_calmar",
    "cost_sensitivity",
    "split_stability",
    "drawdown_risk",
    "concentration_risk",
    "overlap_risk_with_qqq",
    "data_quality",
    "execution_readiness",
    "research_priority_score",
    "ambition_score",
    "safety_blocker_score",
    "final_candidate_status",
    "recommended_next_step",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "sleeve_research_scoreboard.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)

    if failures:
        print("Sleeve research scoreboard verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Sleeve research scoreboard verification passed.")
    print("Verified saved-output-only scoring, Codex experimental research-only sleeve, missing-metric labels, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--sleeve-research-scoreboard",
        "--show-sleeve-research-scoreboard",
        "generate_sleeve_research_scoreboard",
        "show_sleeve_research_scoreboard",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing sleeve scoreboard command token: {token}")


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
        "codex_experimental_research_sleeve",
        CODEX_EXPERIMENTAL_CANDIDATE,
        "adaptive QQQ",
        "qqq_100_trend_gate",
        "codex_broad_growth_balanced_breakout_control",
        "broad Top1 remains rejected",
        "missing_saved_metrics",
        "ambition_score",
        "safety_blocker_score",
        "codex_experimental_execution_approved",
        "high_growth_execution_approved",
        "crypto_execution_approved",
        "false_research_only",
        "top_research_priority_research_only",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"scoreboard module missing required token: {token}")

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
            failures.append(f"scoreboard module must not contain runtime/scheduling token: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--sleeve-research-scoreboard"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("sleeve scoreboard route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--sleeve-research-scoreboard" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by the scoreboard command")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data" / "multi_sleeve_strategy_monitor.csv", ["active_paper_sleeve"], [[BEST_ACTIVE_PAPER_SLEEVE]])
        write_fixture(root / "data" / "qqq100_paper_postcheck.csv", ["position_status", "position_quantity_abs", "alignment_state"], [["paper_position_long", "1", "aligned_long"]])
        write_fixture(
            root / "data" / "paper_execution_state_summary.csv",
            ["summary_name", "summary_value"],
            [["final_state_summary_status", "paper_execution_milestone_recorded"], ["qqq100_alignment_status", "qqq100_aligned_long_confirmed"]],
        )
        result = generate_sleeve_research_scoreboard(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        scoreboard = result.scoreboard_rows[0]
        if scoreboard.get("final_scoreboard_status") != FINAL_SCOREBOARD_STATUS:
            failures.append("final scoreboard status should be sleeve_research_scoreboard_created")
        if scoreboard.get("current_best_active_paper_sleeve") != BEST_ACTIVE_PAPER_SLEEVE:
            failures.append("QQQ100 should remain best active paper sleeve")
        if scoreboard.get("current_best_research_priority") != TOP_RESEARCH_SLEEVE:
            failures.append("top research sleeve should be Codex experimental research sleeve")
        if scoreboard.get("codex_experimental_sleeve_candidate") != CODEX_EXPERIMENTAL_CANDIDATE:
            failures.append("Codex experimental sleeve candidate should be explicit")
        if scoreboard.get("biggest_blocker") != BIGGEST_BLOCKER:
            failures.append("biggest blocker should be missing sleeve allocation policy and validation")
        if scoreboard.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
            failures.append("recommended next step should be targeted research pack")

        for column in REQUIRED_SCORE_COLUMNS:
            if column not in result.candidate_rows[0]:
                failures.append(f"scoreboard candidates missing required score column: {column}")
        sleeve_names = {row["sleeve_name"] for row in result.candidate_rows}
        for expected in [
            BEST_ACTIVE_PAPER_SLEEVE,
            "defensive_etf_research_sleeve",
            "high_growth_stock_research_sleeve",
            "crypto_research_sleeve",
            "codex_experimental_research_sleeve",
        ]:
            if expected not in sleeve_names:
                failures.append(f"missing scored sleeve: {expected}")

        candidate_by_sleeve = {row["sleeve_name"]: row for row in result.candidate_rows}
        if candidate_by_sleeve[BEST_ACTIVE_PAPER_SLEEVE]["status"] != "active_paper_sleeve":
            failures.append("QQQ100 should be the only active paper sleeve")
        if candidate_by_sleeve["codex_experimental_research_sleeve"]["status"] != "research_only":
            failures.append("Codex experimental sleeve should be research-only")
        for sleeve in ["defensive_etf_research_sleeve", "high_growth_stock_research_sleeve", "crypto_research_sleeve"]:
            if "research" not in candidate_by_sleeve[sleeve]["status"]:
                failures.append(f"{sleeve} should remain research-only/research-or-preview-only")
        if not any("missing_saved_metrics" in str(value) for row in result.candidate_rows for value in row.values()):
            failures.append("missing metrics should be labelled rather than invented")

        for collection in [
            result.scoreboard_rows,
            result.candidate_rows,
            result.ranking_rows,
            result.blocker_rows,
            result.next_step_rows,
            result.codex_experimental_rows,
        ]:
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
                    "codex_experimental_execution_approved",
                ]:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false in scoreboard outputs")
        code, lines = show_sleeve_research_scoreboard(root)
        if code != 0 or not any(FINAL_SCOREBOARD_STATUS in line for line in lines):
            failures.append("saved display should show final scoreboard status")


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
