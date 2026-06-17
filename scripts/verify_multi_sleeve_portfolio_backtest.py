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
    FINAL_STATUS_NOT_BETTER_THAN_GENERATED_QQQ100,
    FINAL_STATUS_PROMISING_NEEDS_RECONCILIATION,
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
    "saved_qqq100_benchmark_source",
    "saved_qqq100_benchmark_cagr",
    "saved_qqq100_benchmark_sharpe",
    "saved_qqq100_benchmark_max_drawdown",
    "saved_qqq100_benchmark_calmar",
    "generated_qqq100_reference_status",
    "generated_qqq100_reference_cagr",
    "generated_qqq100_reference_sharpe",
    "generated_qqq100_reference_max_drawdown",
    "generated_qqq100_reference_calmar",
    "qqq100_reference_source_used",
    "qqq100_reference_status",
    "recovered_reference_available",
    "old_generated_reference_retained",
    "old_generated_reference_status",
    "recovered_qqq100_reference_cagr",
    "recovered_qqq100_reference_sharpe",
    "recovered_qqq100_reference_max_drawdown",
    "recovered_qqq100_reference_calmar",
    "saved_benchmark_reconciliation_status",
    "saved_benchmark_delta_CAGR",
    "saved_benchmark_delta_Sharpe",
    "saved_benchmark_delta_MaxDD",
    "saved_benchmark_delta_Calmar",
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
    "delta_cagr_vs_generated_qqq100_reference",
    "delta_sharpe_vs_generated_qqq100_reference",
    "delta_max_drawdown_vs_generated_qqq100_reference",
    "delta_calmar_vs_generated_qqq100_reference",
    "delta_cagr_vs_recovered_qqq100_reference",
    "delta_sharpe_vs_recovered_qqq100_reference",
    "delta_max_drawdown_vs_recovered_qqq100_reference",
    "delta_calmar_vs_recovered_qqq100_reference",
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
    print("Verified saved-output-only portfolio rows, separated saved/generated QQQ100 baselines, stream-aware missing labels, and false execution/scheduling flags.")
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
        "qqq100_plus_spy_sma200_defensive_gate",
        "qqq100_plus_rolling_drawdown_defensive_gate",
        "qqq100_plus_combined_defensive_gate",
        "delta_vs_recovered_qqq100_reference",
        "diagnostic_delta_vs_old_generated_qqq100_reference",
        "delta_vs_recovered_qqq100_reference",
        "saved_benchmark_reconciliation_status",
        "generated_qqq100_reference_needs_reconciliation_with_saved_benchmark",
        "multi_sleeve_candidate_not_better_than_generated_qqq100",
        "multi_sleeve_candidate_promising_needs_reconciliation",
        "multi_sleeve_candidate_promising_recovered_reference_review",
        "multi_sleeve_candidate_promising_needs_crypto_and_policy_review",
        "qqq100_recovered_reference_stream",
        "qqq100_recovered_inputs_sma200_close_to_close_10bps",
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
        "saved_return_stream_metrics_available",
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
        write_stream_fixture(root / "data" / "sleeve_return_streams.csv")
        write_recovered_reference_fixture(root)
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
        if summary.get("final_backtest_status") not in {
            FINAL_BACKTEST_STATUS,
            FINAL_STATUS_NOT_BETTER_THAN_GENERATED_QQQ100,
            FINAL_STATUS_PROMISING_NEEDS_RECONCILIATION,
            "multi_sleeve_candidate_promising_recovered_reference_review",
            "multi_sleeve_candidate_promising_needs_crypto_and_policy_review",
        }:
            failures.append("final status should be one of the explicit generated-stream research statuses")
        if summary.get("top_multi_sleeve_portfolio_candidate") == QQQ100_REFERENCE:
            failures.append("top candidate should be a non-reference generated-stream portfolio")
        if summary.get("saved_qqq100_benchmark_cagr") != "16.8429":
            failures.append("QQQ100 reference CAGR should come from exact qqq_100_trend_gate saved metrics")
        if summary.get("generated_qqq100_reference_cagr") in {"16.8429", "", None}:
            failures.append("generated QQQ100 reference should be computed separately from saved benchmark metrics")
        if summary.get("qqq100_reference_source_used") != "qqq100_recovered_reference_stream":
            failures.append("valid recovered reference fixture should become the primary QQQ100 reference")
        if summary.get("recovered_reference_available") != "true":
            failures.append("valid recovered reference fixture should be marked available")
        if summary.get("old_generated_reference_retained") != "true":
            failures.append("old generated reference should be retained as diagnostic")
        if summary.get("old_generated_reference_status") != "diagnostic_only":
            failures.append("old generated reference should be diagnostic-only")
        if summary.get("recovered_qqq100_reference_cagr") == "missing_saved_metrics":
            failures.append("recovered QQQ100 reference metrics should be reported when valid")
        if summary.get("delta_cagr_vs_recovered_qqq100_reference") in {"", None, "missing_saved_metrics"}:
            failures.append("valid recovered reference should expose deltas vs recovered QQQ100 reference")
        stale_next_step = "reconcile_generated_qqq100_stream_against_saved_benchmark_before_candidate_label_change"
        if summary.get("recommended_next_step") == stale_next_step:
            failures.append("valid recovered reference should not use stale generated-stream reconciliation next step")
        reconciliation_status = summary.get("saved_benchmark_reconciliation_status", "")
        if "generated_qqq100_reference" not in reconciliation_status and "recovered_qqq100_reference" not in reconciliation_status:
            failures.append("summary should include generated or recovered benchmark reconciliation status")
        if old_ambitious_metrics_used(summary):
            failures.append("QQQ100 baseline must not use old codex ambitious metrics")
        missing_warning = summary.get("missing_sleeve_data_warnings", "")
        if "defensive_crash_gate" in missing_warning or "codex_experimental" in missing_warning:
            failures.append("defensive and Codex streams should not be labelled missing when generated streams exist")
        if "high_growth" not in missing_warning or "crypto" not in missing_warning:
            failures.append("high-growth and crypto streams should remain labelled missing")

        portfolio_names = {row["portfolio_name"] for row in result.backtest_rows}
        for expected in [
            QQQ100_REFERENCE,
            TOP_MULTI_SLEEVE_CANDIDATE,
            "qqq100_plus_spy_sma200_defensive_gate",
            "qqq100_plus_rolling_drawdown_defensive_gate",
            "qqq100_plus_combined_defensive_gate",
            "codex_defensive_qqq_research_portfolio",
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
        for sleeve in ["qqq_defensive_crash_gate_research_sleeve", "codex_experimental_research_sleeve"]:
            if sleeve not in sleeves:
                failures.append(f"{sleeve} should be present")
            elif sleeves[sleeve].get("return_stream_status") != "saved_return_stream_metrics_available":
                failures.append(f"{sleeve} should consume the generated return stream")
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
        for portfolio_name in [
            "qqq100_plus_spy_sma200_defensive_gate",
            "qqq100_plus_rolling_drawdown_defensive_gate",
            "qqq100_plus_combined_defensive_gate",
            "codex_defensive_qqq_research_portfolio",
        ]:
            row = next((item for item in result.backtest_rows if item.get("portfolio_name") == portfolio_name), None)
            if not row:
                continue
            if row.get("data_quality") != "saved_return_stream_metrics_available":
                failures.append(f"{portfolio_name} should be computed from saved return streams")
            if row.get("delta_cagr_vs_generated_qqq100_reference") == "missing_saved_metrics":
                failures.append(f"{portfolio_name} should have generated-reference deltas")

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
        if code != 0 or not any("final_backtest_status" in line for line in lines):
            failures.append("saved display should show final backtest status")
        if not any("saved QQQ100 benchmark metrics" in line for line in lines):
            failures.append("saved display should show saved QQQ100 benchmark metrics")
        if not any("old generated QQQ100 diagnostic reference metrics" in line for line in lines):
            failures.append("saved display should show old generated QQQ100 diagnostic reference metrics")
        if not any("delta_vs_recovered_qqq100_reference" in line for line in lines):
            failures.append("saved display should show deltas vs recovered QQQ100 reference")
        if any("recommended next step: reconcile_generated_qqq100_stream_against_saved_benchmark_before_candidate_label_change" in line for line in lines):
            failures.append("saved display should not show stale generated-stream reconciliation next step when recovered reference is valid")


def write_fixture(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def write_stream_fixture(path: Path) -> None:
    headers = ["date", "candidate_name", "daily_strategy_return", "signal_state"]
    candidates = {
        "qqq_100_trend_gate": [0.010, -0.004, 0.006, -0.002, 0.005, -0.003, 0.004, 0.002],
        "cash_default_defensive_sleeve": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "qqq100_spy_sma200_regime_filter": [0.006, -0.001, 0.004, 0.0, 0.003, -0.001, 0.003, 0.001],
        "qqq100_rolling_drawdown_15_filter": [0.005, 0.0, 0.004, 0.0, 0.003, 0.0, 0.002, 0.001],
        "qqq100_combined_trend_spy_regime_drawdown_gate": [0.004, 0.0, 0.003, 0.0, 0.003, 0.0, 0.002, 0.001],
        "codex_qqq_calmar_optimised_defensive_gate_sleeve": [0.005, -0.001, 0.003, 0.0, 0.002, 0.0, 0.002, 0.001],
    }
    rows: list[list[str]] = []
    for day_index in range(8):
        date = f"2024-01-{day_index + 2:02d}"
        for candidate, returns in candidates.items():
            state = "risk_on" if returns[day_index] != 0 else "cash"
            rows.append([date, candidate, str(returns[day_index]), state])
    write_fixture(path, headers, rows)


def write_recovered_reference_fixture(root: Path) -> None:
    metric_headers = [
        "reference_name",
        "source_candidate_name",
        "reference_status",
        "gap_threshold_status",
        "cagr",
        "sharpe",
        "max_drawdown",
        "calmar",
        "annual_volatility",
        "cash_percentage",
        "trade_signal_change_count",
        "saved_benchmark_delta_CAGR",
        "saved_benchmark_delta_Sharpe",
        "saved_benchmark_delta_MaxDD",
        "saved_benchmark_delta_Calmar",
        "execution_approved",
        "scheduling_approved",
        "orders_created",
        "orders_submitted",
        "orders_cancelled",
    ]
    write_fixture(
        root / "data" / "qqq100_recovered_reference_metrics.csv",
        metric_headers,
        [[
            "qqq100_recovered_reference_stream",
            "qqq100_recovered_inputs_sma200_close_to_close_10bps",
            "qqq100_reconstruction_close_enough_for_research_review",
            "all_metric_gaps_within_research_review_thresholds",
            "16.9832",
            "1.0073",
            "-23.4576",
            "0.724",
            "18.0",
            "35",
            "22",
            "0.1403",
            "0.0046",
            "0.0",
            "0.006",
            "false",
            "false",
            "false",
            "false",
            "false",
        ]],
    )
    stream_headers = [
        "date",
        "candidate_name",
        "source_candidate_name",
        "reference_status",
        "daily_strategy_return",
        "signal_state",
        "execution_approved",
        "scheduling_approved",
        "orders_created",
        "orders_submitted",
        "orders_cancelled",
    ]
    rows = []
    returns = [0.011, -0.003, 0.007, -0.001, 0.006, -0.002, 0.005, 0.003]
    for day_index, value in enumerate(returns):
        rows.append([
            f"2024-01-{day_index + 2:02d}",
            "qqq100_recovered_reference_stream",
            "qqq100_recovered_inputs_sma200_close_to_close_10bps",
            "qqq100_reconstruction_close_enough_for_research_review",
            str(value),
            "risk_on",
            "false",
            "false",
            "false",
            "false",
            "false",
        ])
    write_fixture(root / "data" / "qqq100_recovered_reference_stream.csv", stream_headers, rows)


def old_ambitious_metrics_used(summary: dict[str, str]) -> bool:
    return (
        summary.get("saved_qqq100_benchmark_cagr") == "14.1039"
        and summary.get("saved_qqq100_benchmark_sharpe") == "0.7192"
        and summary.get("saved_qqq100_benchmark_max_drawdown") == "-29.5357"
        and summary.get("saved_qqq100_benchmark_calmar") == "0.4775"
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
