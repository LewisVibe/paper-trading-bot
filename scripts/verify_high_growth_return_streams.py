from __future__ import annotations

import csv
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.high_growth_return_streams import (  # noqa: E402
    NEXT_STEP_FIX_MARKET_DATA,
    OUTPUT_FILES,
    PRIMARY_CANDIDATE,
    REFERENCE_CANDIDATE,
    STATUS_BLOCKED_NO_VALID_MARKET_DATA,
    STATUS_CREATED,
    generate_high_growth_return_streams,
    show_high_growth_return_streams,
)
from trading_bot.research.high_growth_stock_drawdown_control import BROAD_UNIVERSE  # noqa: E402
from trading_bot.research.multi_sleeve_portfolio_backtest import generate_multi_sleeve_portfolio_backtest  # noqa: E402


EXPECTED_OUTPUTS = [
    "data/high_growth_return_streams.csv",
    "data/high_growth_return_stream_metrics.csv",
    "data/high_growth_return_stream_summary.csv",
    "data/high_growth_return_stream_blockers.csv",
]

REQUIRED_STREAM_COLUMNS = [
    "date",
    "sleeve_name",
    "sleeve_family",
    "daily_return",
    "daily_strategy_return",
    "equity",
    "invested_flag",
    "exposure",
    "source_status",
    "research_only",
    "preview_only",
    "execution_approved",
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
    "paper_execution_approved",
    "general_execution_approved",
    "high_growth_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "high_growth_return_streams.py")
    backtest_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_portfolio_backtest.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, backtest_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)

    if failures:
        print("High-growth return streams verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("High-growth return streams verification passed.")
    print("Verified research-only saved high-growth streams, schemas, display safety, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--high-growth-return-streams",
        "--show-high-growth-return-streams",
        "generate_high_growth_return_streams",
        "show_high_growth_return_streams",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing high-growth return stream token: {token}")


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
        "high_growth_return_streams.csv",
        "high_growth_return_stream_metrics.csv",
        "codex_broad_growth_balanced_breakout_control",
        "broad_growth_top1_reference",
        "high_growth_stock_research_sleeve",
        "daily_strategy_return",
        "return_stream_only",
        "high_growth_research_only_not_preview_or_execution",
        "high_growth_return_streams_blocked_no_valid_market_data",
        "fix_high_growth_market_data_or_candidate_universe_before_multi_sleeve_backtest",
        "failure_reason_counts",
        "example_failed_tickers",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"high-growth return stream module missing required token: {token}")

    backtest_required = [
        "high_growth_return_streams.csv",
        "normalize_high_growth_stream_rows",
        "codex_broad_growth_balanced_breakout_control",
        "qqq100_plus_high_growth_research",
    ]
    for token in backtest_required:
        if token not in backtest_source:
            failures.append(f"multi-sleeve backtest missing high-growth stream token: {token}")

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
        "run_execute_qqq100_paper",
        "run_paper_order_test",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"high-growth return streams module must not contain execution/config/scheduling token: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--high-growth-return-streams"]',
        'if sys.argv[1:] == ["--multi-sleeve-portfolio-backtest"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("high-growth return stream route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--high-growth-return-streams" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by high-growth streams")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_price_fixture(root / "data" / "high_growth_return_stream_price_fixture.csv")
        write_saved_benchmark_fixture(root / "data" / "project_research_state_summary.csv")
        write_sleeve_stream_fixture(root / "data" / "sleeve_return_streams.csv")
        result = generate_high_growth_return_streams(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.stream_rows:
            failures.append("stream rows should be generated from fixture")
            return
        if not result.metric_rows:
            failures.append("metric rows should be generated from fixture")
            return

        for column in REQUIRED_STREAM_COLUMNS:
            if column not in result.stream_rows[0]:
                failures.append(f"stream output missing required column: {column}")

        candidates = {row["candidate_name"] for row in result.metric_rows}
        if PRIMARY_CANDIDATE not in candidates:
            failures.append("primary high-growth candidate stream should be generated")
        if REFERENCE_CANDIDATE not in candidates:
            failures.append("broad top1 reference stream should be generated")

        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_stream_status") != STATUS_CREATED:
            failures.append("fixture should produce created stream status")
        if "high_growth_research_only" not in " ".join(str(value) for row in result.stream_rows for value in row.values()):
            failures.append("streams should label high-growth research-only status")

        for collection in [result.stream_rows, result.metric_rows, result.summary_rows, result.blocker_rows]:
            for row in collection:
                if str(row.get("research_only", "")).lower() != "true":
                    failures.append("research_only should remain true")
                if str(row.get("return_stream_only", "")).lower() != "true":
                    failures.append("return_stream_only should remain true")
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false")

        code, lines = show_high_growth_return_streams(root)
        if code != 0 or not any("final_stream_status" in line for line in lines):
            failures.append("saved display should show final stream status")
        if not any("execution_approved=false" in line for line in lines):
            failures.append("saved display should preserve false execution flag")

        backtest = generate_multi_sleeve_portfolio_backtest(root)
        high_growth_row = next((row for row in backtest.backtest_rows if row["portfolio_name"] == "qqq100_plus_high_growth_research"), {})
        if high_growth_row.get("data_quality") != "saved_return_stream_metrics_available":
            failures.append("multi-sleeve backtest should consume saved high-growth return streams")
        summary = {row["summary_name"]: row["summary_value"] for row in backtest.summary_rows}
        warnings = summary.get("missing_sleeve_data_warnings", "")
        if "high_growth" in warnings:
            failures.append("multi-sleeve backtest should not label high-growth missing when stream exists")
        if "crypto" not in warnings:
            failures.append("crypto should remain missing until a separate real stream exists")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_empty_price_fixture(root / "data" / "high_growth_return_stream_price_fixture.csv")
        blocked = generate_high_growth_return_streams(root)
        blocked_summary = {row["summary_name"]: row["summary_value"] for row in blocked.summary_rows}
        if blocked.stream_rows:
            failures.append("empty fixture should not generate stream rows")
        if blocked_summary.get("final_stream_status") != STATUS_BLOCKED_NO_VALID_MARKET_DATA:
            failures.append("zero usable market data should be blocked as no valid market data")
        if blocked_summary.get("generated_stream_count") != "0":
            failures.append("zero usable market data should report generated_stream_count=0")
        if blocked_summary.get("recommended_next_step") != NEXT_STEP_FIX_MARKET_DATA:
            failures.append("zero-row outputs should recommend fixing market data before multi-sleeve backtest")
        for key in [
            "total_ticker_count",
            "successful_ticker_count",
            "failed_ticker_count",
            "failure_reason_counts",
            "example_failed_tickers",
            "candidate_status",
        ]:
            if key not in blocked_summary:
                failures.append(f"blocked summary missing diagnostic row: {key}")
        blockers_text = " ".join(str(value) for row in blocked.blocker_rows for value in row.values())
        for token in ["market_data_errors", "reason_counts", "examples", NEXT_STEP_FIX_MARKET_DATA]:
            if token not in blockers_text:
                failures.append(f"blocked output missing blocker diagnostic token: {token}")
        if any(row.get("source_status", "").startswith("generated") for row in blocked.metric_rows):
            failures.append("zero-row outputs must not be labelled generated")
        if any(str(row.get("CAGR")) == "0.0" for row in blocked.metric_rows):
            failures.append("zero-row blocked metrics should be missing_saved_metrics, not fake zero metrics")


def write_price_fixture(path: Path) -> None:
    tickers = list(BROAD_UNIVERSE[:6]) + ["QQQ", "SPY"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "ticker", "close"])
        start = date(2020, 1, 2)
        for index in range(320):
            day = (start + timedelta(days=index)).isoformat()
            for ticker_index, ticker in enumerate(tickers):
                trend = 1.001 + ticker_index * 0.00008
                shock = 0.98 if index in {120, 240} and ticker_index % 3 == 0 else 1.0
                close = 100.0 * ((trend ** index) * shock)
                writer.writerow([day, ticker, round(close, 4)])


def write_empty_price_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "ticker", "close"])


def write_saved_benchmark_fixture(path: Path) -> None:
    write_fixture(
        path,
        ["metric_name", "metric_value", "evidence"],
        [["stock_etf_clean_main_lead", "qqq_100_trend_gate", "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718"]],
    )


def write_sleeve_stream_fixture(path: Path) -> None:
    rows = []
    start = date(2020, 1, 2)
    for index in range(320):
        day = (start + timedelta(days=index)).isoformat()
        qqq_return = 0.002 if index % 10 else -0.004
        rows.append([day, "qqq100_core_trend_sleeve", "qqq_100_trend_gate", "QQQ", "long", qqq_return, qqq_return, 1, 0])
        rows.append([day, "defensive_cash_or_bond_sleeve", "cash_default_defensive_sleeve", "cash", "cash", 0, 0, 0, 1])
    write_fixture(
        path,
        ["date", "sleeve_name", "candidate_name", "ticker_or_assets", "signal_state", "daily_asset_return", "daily_strategy_return", "exposure", "cash_weight"],
        rows,
    )


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
