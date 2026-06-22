from __future__ import annotations

import csv
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.high_growth_component_streams import (  # noqa: E402
    OUTPUT_FILES,
    SELECTED_SLEEVE,
    STATUS_BLOCKED_MARKET_DATA,
    STATUS_CREATED,
    generate_high_growth_component_streams,
    show_high_growth_component_streams,
)
from trading_bot.research.high_growth_stock_drawdown_control import BROAD_UNIVERSE  # noqa: E402


EXPECTED_OUTPUTS = [
    "data/high_growth_component_streams.csv",
    "data/high_growth_component_streams_summary.csv",
    "data/high_growth_component_streams_blockers.csv",
    "data/high_growth_component_drawdown_contributions.csv",
]

REQUIRED_STREAM_FIELDS = [
    "date",
    "sleeve_name",
    "component_ticker",
    "component_weight",
    "component_return",
    "weighted_contribution",
    "weighting_method",
    "attribution_confidence",
    "research_only",
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
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "high_growth_component_streams.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_fixture_generation(failures)
    verify_blocked_generation(failures)

    if failures:
        print("High-growth component streams verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("High-growth component streams verification passed.")
    print("Verified research-only component stream generation, blocked state, display safety, schemas, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--high-growth-component-streams",
        "--show-high-growth-component-streams",
        "generate_high_growth_component_streams",
        "show_high_growth_component_streams",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing high-growth component streams token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, bot_source: str, failures: list[str]) -> None:
    required = [
        "high_growth_component_streams_created_research_only",
        "high_growth_component_streams_partial_manual_review_required",
        "high_growth_component_streams_blocked_missing_reconstructable_holdings",
        "high_growth_component_streams_blocked_market_data_unavailable",
        SELECTED_SLEEVE,
        "equal_weight_component_sleeve",
        "approximate_from_reconstructed_research_stream",
        "component_ticker",
        "component_weight",
        "component_return",
        "weighted_contribution",
        "high_growth_component_drawdown_contributions.csv",
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"high-growth component streams module missing required token: {token}")

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
        "config.json",
        "promotion-ready",
        "promotion_ready",
        "execution-ready",
        "execution_ready",
        "order-ready",
        "order_ready",
        "crypto-execution-ready",
        "crypto_execution_ready",
        "scheduled",
        "approved_for_execution",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"high-growth component streams module must not contain forbidden token: {token}")

    approval_clean = module_source
    for allowed in [
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "live_trading_approved",
        "scheduling_approved",
        "shorting_approved",
        "leverage_approved",
        "margin_approved",
    ]:
        approval_clean = approval_clean.replace(allowed, "")
    if "approved" in approval_clean.lower():
        failures.append("approved wording should only appear in explicit false approval fields")

    show_slice = source_slice(module_source, "def show_high_growth_component_streams", "def selected_simulation")
    if "write_rows" in show_slice or "generate_high_growth_component_streams" in show_slice:
        failures.append("display command must be saved-read-only and must not regenerate outputs")

    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--high-growth-component-streams"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("high-growth component streams route must not call execution commands")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_price_fixture(root / "data" / "high_growth_return_stream_price_fixture.csv")
        result = generate_high_growth_component_streams(root)

        if not result.stream_rows:
            failures.append("fixture should create real component rows")
            return
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("component_stream_status") != STATUS_CREATED:
            failures.append(f"fixture should produce created status, got {summary.get('component_stream_status')}")
        if summary.get("selected_sleeve") != SELECTED_SLEEVE:
            failures.append("summary should preserve selected sleeve")
        if summary.get("concentration_data_available") != "true":
            failures.append("component rows should make concentration data available")
        for field in REQUIRED_STREAM_FIELDS:
            if field not in result.stream_rows[0]:
                failures.append(f"stream row missing field: {field}")
        if any(float(row.get("component_weight", 0.0)) < 0 for row in result.stream_rows):
            failures.append("component weights must not be negative")
        if any(float(row.get("component_weight", 0.0)) > 1.0 for row in result.stream_rows):
            failures.append("component weights should be fractions <= 1.0")
        if any(row.get("selected_sleeve") != SELECTED_SLEEVE for row in result.stream_rows):
            failures.append("component rows should preserve selected sleeve")
        if not result.drawdown_rows:
            failures.append("fixture should create drawdown contribution rows")
        verify_false_flags(result.stream_rows + result.drawdown_rows, "component", failures)

        code, lines = show_high_growth_component_streams(root)
        if code != 0:
            failures.append("display should succeed after fixture generation")
        display = "\n".join(lines)
        for token in ["component stream status", "selected sleeve", "row count", "execution_approved=false"]:
            if token not in display:
                failures.append(f"display missing token: {token}")


def verify_blocked_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_empty_price_fixture(root / "data" / "high_growth_return_stream_price_fixture.csv")
        result = generate_high_growth_component_streams(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("component_stream_status") != STATUS_BLOCKED_MARKET_DATA:
            failures.append("empty fixture should block as market data unavailable")
        if result.stream_rows:
            failures.append("blocked state must not create fake component rows")
        if not any(row.get("blocker_name") == "high_growth_component_streams_blocked_market_data_unavailable" for row in result.blocker_rows):
            failures.append("blocked state should include market-data blocker")


def verify_false_flags(rows: list[dict[str, object]], label: str, failures: list[str]) -> None:
    for index, row in enumerate(rows):
        if str(row.get("research_only", "")).lower() != "true":
            failures.append(f"{label} row {index} should keep research_only=true")
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).lower() != "false":
                failures.append(f"{label} row {index} should keep {flag}=false")


def write_price_fixture(path: Path) -> None:
    tickers = list(BROAD_UNIVERSE[:8]) + ["QQQ", "SPY"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "ticker", "close"])
        start = date(2020, 1, 2)
        for index in range(360):
            day = (start + timedelta(days=index)).isoformat()
            for ticker_index, ticker in enumerate(tickers):
                trend = 1.001 + ticker_index * 0.0001
                shock = 0.96 if index in {130, 131, 240} and ticker_index % 2 == 0 else 1.0
                close = 100.0 * (trend**index) * shock
                writer.writerow([day, ticker, round(close, 4)])


def write_empty_price_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "ticker", "close"])


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
