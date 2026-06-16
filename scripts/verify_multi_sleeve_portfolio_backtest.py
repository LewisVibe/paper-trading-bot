from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_portfolio_backtest import (  # noqa: E402
    BIGGEST_BLOCKER,
    FINAL_BACKTEST_STATUS,
    OUTPUT_FILES,
    QQQ100_REFERENCE,
    QQQ100_SLEEVE,
    RECOMMENDED_NEXT_STEP,
    TOP_MULTI_SLEEVE_CANDIDATE,
    generate_multi_sleeve_portfolio_backtest,
    show_multi_sleeve_portfolio_backtest,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_portfolio_backtest.csv",
    "data/multi_sleeve_portfolio_backtest_sleeves.csv",
    "data/multi_sleeve_portfolio_backtest_allocations.csv",
    "data/multi_sleeve_portfolio_backtest_rankings.csv",
    "data/multi_sleeve_portfolio_backtest_splits.csv",
    "data/multi_sleeve_portfolio_backtest_trades.csv",
    "data/multi_sleeve_portfolio_backtest_blockers.csv",
    "data/multi_sleeve_portfolio_backtest_summary.csv",
]

REQUIRED_BACKTEST_COLUMNS = [
    "portfolio_name",
    "final_backtest_status",
    "baseline_source",
    "qqq100_reference_cagr",
    "qqq100_reference_sharpe",
    "qqq100_reference_max_drawdown",
    "qqq100_reference_calmar",
    "candidate_allocation",
    "candidate_cagr",
    "candidate_sharpe",
    "candidate_max_drawdown",
    "candidate_calmar",
    "candidate_annualised_volatility",
    "candidate_cash_percentage",
    "candidate_sleeve_exposure_percentages",
    "candidate_turnover_or_trade_count",
    "delta_cagr_vs_qqq100",
    "delta_sharpe_vs_qqq100",
    "delta_max_drawdown_vs_qqq100",
    "delta_calmar_vs_qqq100",
    "split_stability_label",
    "balanced_research_score",
    "data_quality",
    "missing_sleeve_data_warnings",
    "biggest_blocker",
    "recommended_next_step",
]

FALSE_FLAGS = [
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "general_execution_approved",
    "qqq100_execution_approved",
    "codex_experimental_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "high_growth_execution_approved",
    "crypto_execution_approved",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_portfolio_backtest.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)

    if failures:
        print("Multi-sleeve portfolio backtest verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Multi-sleeve portfolio backtest verification passed.")
    print("Verified saved-output-only portfolio rows, QQQ100 baseline selection, missing-return-stream labels, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-portfolio-backtest",
        "--show-multi-sleeve-portfolio-backtest",
        "generate_multi_sleeve_portfolio_backtest",
        "show_multi_sleeve_portfolio_backtest",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing multi-sleeve backtest token: {token}")


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
        "multi_sleeve_candidate_needs_more_data",
        "multi_sleeve_portfolio_backtest_created",
        "qqq100_only_reference",
        "qqq100_core_trend_sleeve",
        "qqq_100_trend_gate",
        "qqq100_plus_cash_defensive_reference",
        "qqq100_plus_defensive_crash_gate",
        "qqq100_plus_high_growth_research",
        "qqq100_plus_crypto_research",
        "balanced_multi_sleeve_research_portfolio",
        "codex_ambitious_multi_sleeve_candidate",
        "high_growth_stock_research_sleeve",
        "crypto_research_sleeve",
        "defensive_cash_or_bond_sleeve",
        "codex_experimental_research_sleeve",
        "missing_saved_return_stream",
        "missing_split_metrics",
        "missing_cost_turnover_stream",
        "saved_qqq100_metrics_only",
        "qqq_100_trend_gate_saved_metrics",
        "codex_ambitious_concentrated_growth_persistence",
        "execution_approved",
        "codex_experimental_execution_approved",
        "repeat_execution_approved",
        "scheduling_approved",
        "high_growth_execution_approved",
        "crypto_execution_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"multi-sleeve backtest module missing required token: {token}")

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
        "subprocess.run",
        "create_scheduled_task",
        "automation_update",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"multi-sleeve backtest module must not contain runtime/scheduling token: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--multi-sleeve-portfolio-backtest"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("multi-sleeve backtest route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--multi-sleeve-portfolio-backtest" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by the backtest command")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(
            root / "data" / "project_research_state_summary.csv",
            ["metric_name", "metric_value", "evidence"],
            [["stock_etf_clean_main_lead", "qqq_100_trend_gate", "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718"]],
        )
        write_fixture(
            root / "data" / "qqq_lead_decision_report.csv",
            ["candidate_name", "CAGR", "Sharpe", "MaxDD", "Calmar"],
            [["codex_ambitious_concentrated_growth_persistence", "14.1039", "0.7192", "-29.5357", "0.4775"]],
        )
        result = generate_multi_sleeve_portfolio_backtest(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.backtest_rows:
            failures.append("backtest rows should be generated")
            return

        for column in REQUIRED_BACKTEST_COLUMNS:
            if column not in result.backtest_rows[0]:
                failures.append(f"backtest output missing required column: {column}")

        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_backtest_status") != FINAL_BACKTEST_STATUS:
            failures.append("final status should require more data for multi-sleeve candidate changes")
        if summary.get("top_multi_sleeve_portfolio_candidate") != TOP_MULTI_SLEEVE_CANDIDATE:
            failures.append("top multi-sleeve candidate should be the conservative cash defensive reference")
        if summary.get("qqq100_reference_cagr") != "16.8429":
            failures.append("QQQ100 reference CAGR should come from exact qqq_100_trend_gate saved metrics")
        if old_ambitious_metrics_used(summary):
            failures.append("QQQ100 baseline must not use old codex ambitious metrics")
        if summary.get("biggest_blocker") != BIGGEST_BLOCKER:
            failures.append("summary should preserve missing saved return streams blocker")
        if summary.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
            failures.append("summary should recommend collecting saved daily return streams")

        portfolio_names = {row["portfolio_name"] for row in result.backtest_rows}
        for expected in [
            QQQ100_REFERENCE,
            TOP_MULTI_SLEEVE_CANDIDATE,
            "qqq100_plus_defensive_crash_gate",
            "qqq100_plus_high_growth_research",
            "qqq100_plus_crypto_research",
            "balanced_multi_sleeve_research_portfolio",
            "codex_ambitious_multi_sleeve_candidate",
        ]:
            if expected not in portfolio_names:
                failures.append(f"missing portfolio combination: {expected}")

        sleeves = {row["sleeve_name"]: row for row in result.sleeve_rows}
        if QQQ100_SLEEVE not in sleeves:
            failures.append("QQQ100 sleeve should be present")
        elif sleeves[QQQ100_SLEEVE].get("strategy_name") != "qqq_100_trend_gate":
            failures.append("QQQ100 sleeve should use qqq_100_trend_gate")
        for sleeve in ["high_growth_stock_research_sleeve", "crypto_research_sleeve"]:
            if sleeve not in sleeves:
                failures.append(f"{sleeve} should be present")
            elif sleeves[sleeve].get("return_stream_status") != "missing_saved_return_stream":
                failures.append(f"{sleeve} should be labelled missing_saved_return_stream")

        if not any(row.get("split_name") == "split_60_40" for row in result.split_rows):
            failures.append("split output should include split_60_40")
        if not any(row.get("trade_stream_status") == "missing_saved_trade_stream" for row in result.trade_rows):
            failures.append("trade output should label missing trade stream")
        if not any(row.get("portfolio_name") == TOP_MULTI_SLEEVE_CANDIDATE for row in result.allocation_rows):
            failures.append("allocation output should include top multi-sleeve candidate")
        if not any(row.get("blocker_name") == BIGGEST_BLOCKER for row in result.blocker_rows):
            failures.append("blockers should include missing saved return streams")

        for collection in [
            result.backtest_rows,
            result.sleeve_rows,
            result.allocation_rows,
            result.ranking_rows,
            result.split_rows,
            result.trade_rows,
            result.blocker_rows,
            result.summary_rows,
        ]:
            for row in collection:
                if str(row.get("research_only", "")).lower() != "true":
                    failures.append("research_only should remain true")
                if str(row.get("report_only", "")).lower() != "true":
                    failures.append("report_only should remain true")
                if str(row.get("backtest_only", "")).lower() != "true":
                    failures.append("backtest_only should remain true")
                if str(row.get("multi_sleeve_only", "")).lower() != "true":
                    failures.append("multi_sleeve_only should remain true")
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false in backtest outputs")

        code, lines = show_multi_sleeve_portfolio_backtest(root)
        if code != 0 or not any(FINAL_BACKTEST_STATUS in line for line in lines):
            failures.append("saved display should show final backtest status")
        if not any("QQQ100 reference metrics" in line for line in lines):
            failures.append("saved display should show QQQ100 reference metrics")


def write_fixture(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def old_ambitious_metrics_used(summary: dict[str, str]) -> bool:
    return (
        summary.get("qqq100_reference_cagr") == "14.1039"
        and summary.get("qqq100_reference_sharpe") == "0.7192"
        and summary.get("qqq100_reference_max_drawdown") == "-29.5357"
        and summary.get("qqq100_reference_calmar") == "0.4775"
    )


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
