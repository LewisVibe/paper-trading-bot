from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.high_growth_sleeve_concentration import (  # noqa: E402
    NEXT_MANUAL_REVIEW,
    OUTPUT_FILES,
    SELECTED_SLEEVE,
    STATUS_HIGH_SINGLE_NAME,
    STATUS_MANUAL_REVIEW,
    generate_high_growth_sleeve_concentration_review,
    show_high_growth_sleeve_concentration_review,
)


EXPECTED_OUTPUTS = [
    "data/high_growth_sleeve_concentration_review.csv",
    "data/high_growth_sleeve_concentration_summary.csv",
    "data/high_growth_sleeve_concentration_top_contributors.csv",
    "data/high_growth_sleeve_concentration_drawdown.csv",
    "data/high_growth_sleeve_concentration_blockers.csv",
]

FALSE_FLAGS = [
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "yfinance_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "high_growth_sleeve_concentration.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_fixture_generation(failures)
    verify_blocked_generation(failures)

    if failures:
        print("High-growth sleeve concentration verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("High-growth sleeve concentration verification passed.")
    print("Verified saved-output concentration review, dependency metrics, drawdown rows, display safety, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--high-growth-sleeve-concentration-review",
        "--show-high-growth-sleeve-concentration-review",
        "generate_high_growth_sleeve_concentration_review",
        "show_high_growth_sleeve_concentration_review",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing high-growth sleeve concentration token: {token}")


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
        SELECTED_SLEEVE,
        "high_growth_concentration_manual_review_required",
        "high_growth_concentration_blocked_missing_component_streams",
        "component_dependency_manual_review_required",
        "component_dependency_high_single_name_risk",
        "top_1_contribution_share",
        "top_3_contribution_share",
        "top_5_contribution_share",
        "herfindahl_index_by_positive_contribution",
        "drawdown_concentration_status",
        NEXT_MANUAL_REVIEW,
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "live_trading_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"high-growth sleeve concentration module missing required token: {token}")

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
            failures.append(f"high-growth sleeve concentration module must not contain forbidden token: {token}")

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

    show_slice = source_slice(module_source, "def show_high_growth_sleeve_concentration_review", "def selected_stream_rows")
    if "write_rows" in show_slice or "generate_high_growth_sleeve_concentration_review" in show_slice:
        failures.append("display command must be saved-read-only and must not regenerate outputs")

    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--high-growth-sleeve-concentration-review"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("high-growth sleeve concentration route must not call execution commands")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_component_fixture(root)
        result = generate_high_growth_sleeve_concentration_review(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        review = result.review_rows[0]

        if summary.get("final_concentration_review_status") not in {STATUS_MANUAL_REVIEW, STATUS_HIGH_SINGLE_NAME}:
            failures.append(f"fixture should require cautious concentration review, got {summary.get('final_concentration_review_status')}")
        if summary.get("selected_sleeve") != SELECTED_SLEEVE:
            failures.append("summary should preserve selected sleeve")
        for key in [
            "unique_ticker_count",
            "average_active_components",
            "max_component_weight",
            "top_1_contribution_share",
            "top_3_contribution_share",
            "top_5_contribution_share",
            "dependency_status",
            "drawdown_concentration_summary",
        ]:
            if key not in summary:
                failures.append(f"summary missing concentration field: {key}")
        if not result.contributor_rows:
            failures.append("fixture should create top contributor rows")
        if not result.drawdown_rows:
            failures.append("fixture should create drawdown concentration rows")
        if review.get("selected_sleeve") != SELECTED_SLEEVE:
            failures.append("review row should preserve selected sleeve")
        if str(review.get("execution_approved", "")).lower() != "false":
            failures.append("review row should keep execution_approved=false")
        verify_safety_flags(result.review_rows + result.summary_rows + result.contributor_rows + result.drawdown_rows, "fixture", failures)

        code, lines = show_high_growth_sleeve_concentration_review(root)
        if code != 0:
            failures.append("display should succeed after fixture generation")
        display = "\n".join(lines)
        for token in ["final concentration review status", "selected sleeve", "dependency shares", "execution_approved=false"]:
            if token not in display:
                failures.append(f"display missing token: {token}")


def verify_blocked_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_high_growth_sleeve_concentration_review(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_concentration_review_status") != "high_growth_concentration_blocked_missing_component_streams":
            failures.append("missing component streams should block concentration review")
        if result.contributor_rows:
            failures.append("blocked path must not create fake contributor rows")
        if not any(row.get("blocker_name") == "component_streams_missing" for row in result.blocker_rows):
            failures.append("blocked path should include component_streams_missing blocker")
        verify_safety_flags(result.review_rows + result.summary_rows, "blocked", failures)


def verify_safety_flags(rows: list[dict[str, object]], label: str, failures: list[str]) -> None:
    for index, row in enumerate(rows):
        if str(row.get("research_only", "")).lower() != "true":
            failures.append(f"{label} row {index} should keep research_only=true")
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).lower() != "false":
                failures.append(f"{label} row {index} should keep {flag}=false")


def write_component_fixture(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    rows = []
    for day, aaa, bbb, ccc in [
        ("2021-02-09", -0.08, -0.02, -0.01),
        ("2021-02-10", -0.07, -0.01, -0.02),
        ("2021-02-11", 0.03, -0.02, 0.01),
        ("2021-02-12", 0.02, 0.01, 0.01),
    ]:
        rows.extend(
            [
                component_row(day, "AAA", "1.00", aaa),
                component_row(day, "BBB", "0.50", bbb),
                component_row(day, "CCC", "0.50", ccc),
            ]
        )
    write_csv(data / "high_growth_component_streams.csv", rows)
    write_csv(
        data / "high_growth_sleeve_quality_drawdowns.csv",
        [
            {
                "drawdown_start": "2021-02-09",
                "drawdown_trough": "2021-02-12",
                "max_drawdown": "-42.3324",
                **false_flags_as_strings(),
            }
        ],
    )


def component_row(day: str, ticker: str, weight: str, daily_return: float) -> dict[str, str]:
    weighted = float(weight) * daily_return
    return {
        "date": day,
        "sleeve_name": SELECTED_SLEEVE,
        "selected_sleeve": SELECTED_SLEEVE,
        "component_ticker": ticker,
        "component_weight": weight,
        "component_return": str(daily_return),
        "weighted_contribution": str(weighted),
        **false_flags_as_strings(),
    }


def false_flags_as_strings() -> dict[str, str]:
    return {
        "orders_created": "false",
        "orders_submitted": "false",
        "orders_cancelled": "false",
        "orders_replaced": "false",
        "alpaca_called": "false",
        "yfinance_called": "false",
        "live_position_read": "false",
        "sqlite_trade_log_written": "false",
        "discord_alert_sent": "false",
        "telegram_alert_sent": "false",
        "execution_approved": "false",
        "paper_execution_approved": "false",
        "crypto_execution_approved": "false",
        "live_trading_approved": "false",
        "scheduling_approved": "false",
        "shorting_approved": "false",
        "leverage_approved": "false",
        "margin_approved": "false",
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index == -1:
        return ""
    end_index = source.find(end, start_index + len(start))
    return source[start_index:] if end_index == -1 else source[start_index:end_index]


if __name__ == "__main__":
    raise SystemExit(main())
