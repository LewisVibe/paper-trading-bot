from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.qqq100_stream_reconciliation import (  # noqa: E402
    OUTPUT_FILES,
    QQQ100_STRATEGY,
    generate_qqq100_stream_reconciliation,
    show_qqq100_stream_reconciliation,
)


EXPECTED_OUTPUTS = [
    "data/qqq100_stream_reconciliation.csv",
    "data/qqq100_stream_reconciliation_candidates.csv",
    "data/qqq100_stream_reconciliation_diagnostics.csv",
    "data/qqq100_stream_reconciliation_blockers.csv",
    "data/qqq100_stream_reconciliation_summary.csv",
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
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "qqq100_stream_reconciliation.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)

    if failures:
        print("QQQ100 stream reconciliation verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 stream reconciliation verification passed.")
    print("Verified saved/generated benchmark comparison, candidate diagnostics, labelled missing assumptions, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--qqq100-stream-reconciliation",
        "--show-qqq100-stream-reconciliation",
        "generate_qqq100_stream_reconciliation",
        "show_qqq100_stream_reconciliation",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing QQQ100 stream reconciliation token: {token}")


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
        "qqq100_stream_reconciliation.csv",
        "qqq100_stream_reconciliation_candidates.csv",
        "qqq100_stream_close_shift0",
        "qqq100_stream_close_shift1",
        "qqq100_stream_adjclose_shift0",
        "qqq100_stream_adjclose_shift1",
        "qqq100_stream_min_periods_100_shift1",
        "qqq100_stream_saved_benchmark_like_best_candidate",
        "missing_cost_assumption",
        "cash_or_risk_free_assumption_unknown",
        "price_adjustment_or_dividend_split_treatment_unknown",
        "execution_approved",
        "repeat_execution_approved",
        "scheduling_approved",
        QQQ100_STRATEGY,
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"QQQ100 stream reconciliation module missing required token: {token}")

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
        "create_scheduled_task",
        "automation_update",
        "run_execute_qqq100_paper",
        "run_paper_order_test",
        "load_config",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"QQQ100 stream reconciliation module must not contain execution/config/scheduling token: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--qqq100-stream-reconciliation"]',
        'if sys.argv[1:] == ["--multi-sleeve-portfolio-backtest"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("QQQ100 stream reconciliation route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--qqq100-stream-reconciliation" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by reconciliation command")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_saved_benchmark_fixture(root / "data" / "project_research_state_summary.csv")
        write_price_fixture(root / "data" / "sleeve_return_stream_price_fixture.csv")
        write_current_stream_fixture(root / "data" / "sleeve_return_streams.csv")
        result = generate_qqq100_stream_reconciliation(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.report_rows or not result.candidate_rows or not result.diagnostic_rows:
            failures.append("report, candidate, and diagnostic rows should be generated")
            return

        report = result.report_rows[0]
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if report.get("saved_benchmark_cagr") != "16.8429":
            failures.append("saved benchmark CAGR should come from exact QQQ100 saved metrics")
        if report.get("current_generated_cagr") in {"", "missing_saved_metrics", None}:
            failures.append("current generated stream metrics should be read from saved sleeve_return_streams.csv")
        if "qqq100_stream" not in report.get("best_aligned_candidate", ""):
            failures.append("best aligned candidate should be a QQQ100 stream candidate")
        if report.get("sleeve_return_streams_updated") not in {False, "False", "false"}:
            failures.append("reconciliation should not update sleeve_return_streams automatically")
        if "missing" not in report.get("likely_mismatch_cause", "") and "unknown" not in report.get("likely_mismatch_cause", "") and "mismatch" not in report.get("likely_mismatch_cause", ""):
            failures.append("likely mismatch cause should be labelled conservatively")
        if "saved QQQ100 benchmark metrics" not in " ".join(result.summary_lines):
            failures.append("terminal summary should include saved QQQ100 benchmark metrics")
        if summary.get("sleeve_return_streams_updated") != "false":
            failures.append("summary should state sleeve_return_streams was not updated")

        candidate_names = {row["candidate_name"] for row in result.candidate_rows}
        for expected in [
            "qqq100_stream_close_shift0",
            "qqq100_stream_close_shift1",
            "qqq100_stream_adjclose_shift0",
            "qqq100_stream_adjclose_shift1",
            "qqq100_stream_min_periods_100_shift1",
            "qqq100_stream_saved_benchmark_like_best_candidate",
        ]:
            if expected not in candidate_names:
                failures.append(f"missing reconciliation candidate: {expected}")

        diagnostic_text = " ".join(str(value) for row in result.diagnostic_rows for value in row.values())
        for expected in ["missing_cost_assumption", "cash_or_risk_free_assumption_unknown", "signal_timing_mismatch_possible"]:
            if expected not in diagnostic_text:
                failures.append(f"diagnostics should label missing assumption/cause: {expected}")

        for collection in [
            result.report_rows,
            result.candidate_rows,
            result.diagnostic_rows,
            result.blocker_rows,
            result.summary_rows,
        ]:
            for row in collection:
                if str(row.get("research_only", "")).lower() != "true":
                    failures.append("research_only should remain true")
                if str(row.get("report_only", "")).lower() != "true":
                    failures.append("report_only should remain true")
                if str(row.get("reconciliation_only", "")).lower() != "true":
                    failures.append("reconciliation_only should remain true")
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false")

        code, lines = show_qqq100_stream_reconciliation(root)
        if code != 0 or not any("final_reconciliation_status" in line for line in lines):
            failures.append("saved display should show final reconciliation status")


def write_saved_benchmark_fixture(path: Path) -> None:
    write_fixture(
        path,
        ["metric_name", "metric_value", "evidence"],
        [["stock_etf_clean_main_lead", "qqq_100_trend_gate", "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718"]],
    )


def write_current_stream_fixture(path: Path) -> None:
    rows = []
    returns = [0.004, -0.002, 0.005, 0.0, -0.001, 0.004, 0.002, -0.001]
    for index, value in enumerate(returns):
        rows.append([f"2024-06-{index + 1:02d}", "qqq100_core_trend_sleeve", "qqq_100_trend_gate", "QQQ", "long" if value else "flat", value, value, 1 if value else 0, 0 if value else 1])
    write_fixture(
        path,
        ["date", "sleeve_name", "candidate_name", "ticker_or_assets", "signal_state", "daily_asset_return", "daily_strategy_return", "exposure", "cash_weight"],
        rows,
    )


def write_price_fixture(path: Path) -> None:
    rows = []
    close = 100.0
    for index in range(180):
        close *= 1.002 if index % 35 else 0.985
        rows.append([f"2024-{(index // 22) % 12 + 1:02d}-{index % 22 + 1:02d}", "QQQ", round(close, 4), round(close * 0.998, 4)])
    write_fixture(path, ["date", "ticker", "close", "adj_close"], rows)


def write_fixture(path: Path, headers: list[str], rows: list[list[object]]) -> None:
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
