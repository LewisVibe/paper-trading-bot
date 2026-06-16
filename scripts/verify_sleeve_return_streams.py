from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_portfolio_backtest import (  # noqa: E402
    TOP_MULTI_SLEEVE_CANDIDATE,
    generate_multi_sleeve_portfolio_backtest,
)
from trading_bot.research.sleeve_return_streams import (  # noqa: E402
    BEST_DEFENSIVE_CANDIDATE,
    FINAL_STREAM_STATUS,
    OUTPUT_FILES,
    QQQ100_SLEEVE,
    QQQ100_STRATEGY,
    generate_sleeve_return_streams,
    show_sleeve_return_streams,
)


EXPECTED_OUTPUTS = [
    "data/sleeve_return_streams.csv",
    "data/sleeve_return_streams_summary.csv",
    "data/sleeve_return_streams_sleeves.csv",
    "data/sleeve_return_streams_quality.csv",
    "data/sleeve_return_streams_blockers.csv",
    "data/sleeve_return_streams_next_steps.csv",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "sleeve_return_streams.py")
    backtest_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_portfolio_backtest.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, backtest_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation_and_backtest_consumption(failures)

    if failures:
        print("Sleeve return streams verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Sleeve return streams verification passed.")
    print("Verified research-only stream generation, missing high-growth/crypto labels, QQQ100 baseline identity, and multi-sleeve backtest consumption.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--sleeve-return-streams",
        "--show-sleeve-return-streams",
        "generate_sleeve_return_streams",
        "show_sleeve_return_streams",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing sleeve return stream token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, backtest_source: str, failures: list[str]) -> None:
    required = [
        "sleeve_return_streams_partial_created",
        "qqq100_return_stream_created",
        "defensive_qqq_streams_created",
        "high_growth_stream_missing",
        "crypto_stream_missing",
        "missing_saved_return_stream",
        QQQ100_SLEEVE,
        QQQ100_STRATEGY,
        BEST_DEFENSIVE_CANDIDATE,
        "cash_default_defensive_sleeve",
        "codex_qqq_calmar_optimised_defensive_gate_sleeve",
        "approximate_or_needs_reconciliation",
        "daily_strategy_return",
        "set_tz_cache_location",
        "execution_approved",
        "repeat_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"sleeve return streams module missing required token: {token}")

    backtest_required = [
        "sleeve_return_streams.csv",
        "portfolio_metrics_from_streams",
        "codex_defensive_qqq_research_portfolio",
        "saved_return_stream_metrics_available",
    ]
    for token in backtest_required:
        if token not in backtest_source:
            failures.append(f"multi-sleeve backtest missing stream-consumption token: {token}")

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
        "load_config",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"sleeve return streams module must not contain execution/scheduling token: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--sleeve-return-streams"]',
        'if sys.argv[1:] == ["--multi-sleeve-portfolio-backtest"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("sleeve return stream route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--sleeve-return-streams" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by return streams command")


def verify_temp_generation_and_backtest_consumption(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_price_fixture(root / "data" / "sleeve_return_stream_price_fixture.csv")
        result = generate_sleeve_return_streams(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_stream_status") != FINAL_STREAM_STATUS:
            failures.append("final stream status should be partial created while high-growth/crypto are missing")
        if QQQ100_STRATEGY not in summary.get("generated_sleeve_streams", ""):
            failures.append("generated streams summary should include QQQ100 strategy")
        if "high_growth_stock_research_sleeve" not in summary.get("missing_sleeve_streams", ""):
            failures.append("high-growth stream should be labelled missing")
        if "crypto_research_sleeve" not in summary.get("missing_sleeve_streams", ""):
            failures.append("crypto stream should be labelled missing")
        if not result.stream_rows:
            failures.append("stream rows should be generated from fixture")

        quality_by_sleeve = {row["sleeve_name"]: row for row in result.quality_rows}
        qqq_quality = quality_by_sleeve.get(QQQ100_SLEEVE, {})
        if qqq_quality.get("candidate_name") != QQQ100_STRATEGY:
            failures.append("QQQ100 stream should use qqq_100_trend_gate")
        if qqq_quality.get("metric_alignment_status") != "approximate_or_needs_reconciliation":
            failures.append("QQQ100 metric alignment should be approximate_or_needs_reconciliation")
        if quality_by_sleeve.get("high_growth_stock_research_sleeve", {}).get("stream_status") != "missing_saved_return_stream":
            failures.append("high-growth should remain missing_saved_return_stream")
        if quality_by_sleeve.get("crypto_research_sleeve", {}).get("stream_status") != "missing_saved_return_stream":
            failures.append("crypto should remain missing_saved_return_stream")

        for collection in [
            result.stream_rows,
            result.summary_rows,
            result.sleeve_rows,
            result.quality_rows,
            result.blocker_rows,
            result.next_step_rows,
        ]:
            for row in collection:
                if str(row.get("research_only", "")).lower() != "true":
                    failures.append("research_only should remain true")
                if str(row.get("report_only", "")).lower() != "true":
                    failures.append("report_only should remain true")
                if str(row.get("return_stream_only", "")).lower() != "true":
                    failures.append("return_stream_only should remain true")
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false")

        code, lines = show_sleeve_return_streams(root)
        if code != 0 or not any(FINAL_STREAM_STATUS in line for line in lines):
            failures.append("saved display should show final stream status")

        backtest = generate_multi_sleeve_portfolio_backtest(root)
        backtest_by_name = {row["portfolio_name"]: row for row in backtest.backtest_rows}
        top = backtest_by_name.get(TOP_MULTI_SLEEVE_CANDIDATE, {})
        if top.get("candidate_cagr") in {"", "missing_saved_metrics", None}:
            failures.append("multi-sleeve backtest should compute real metrics from saved sleeve_return_streams.csv")
        if top.get("data_quality") != "saved_return_stream_metrics_available":
            failures.append("multi-sleeve backtest should mark feasible stream portfolios as saved_return_stream_metrics_available")


def write_price_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "ticker", "close"])
        qqq = 100.0
        spy = 100.0
        for index in range(260):
            date = f"2024-{(index // 22) % 12 + 1:02d}-{index % 22 + 1:02d}"
            qqq *= 1.0015 if index % 55 != 0 else 0.985
            spy *= 1.0010 if index % 70 != 0 else 0.99
            writer.writerow([date, "QQQ", round(qqq, 4)])
            writer.writerow([date, "SPY", round(spy, 4)])


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
