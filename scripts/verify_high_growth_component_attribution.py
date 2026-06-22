from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.high_growth_component_attribution import (  # noqa: E402
    HIGH_GROWTH_SLEEVE,
    OUTPUT_FILES,
    STATUS_BLOCKED,
    STATUS_CREATED,
    generate_high_growth_component_attribution,
    show_high_growth_component_attribution,
)


EXPECTED_OUTPUTS = [
    "data/high_growth_component_attribution.csv",
    "data/high_growth_component_attribution_summary.csv",
    "data/high_growth_component_attribution_blockers.csv",
]

OPTIONAL_OUTPUTS = [
    "data/high_growth_component_contributions.csv",
    "data/high_growth_component_drawdown_contributions.csv",
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

TRUE_FLAGS = ["research_only", "preview_only", "saved_output_only"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "high_growth_component_attribution.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_blocked_generation(failures)
    verify_component_generation(failures)

    if failures:
        print("High-growth component attribution verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("High-growth component attribution verification passed.")
    print("Verified saved-output audit, missing-data blockers, optional component rows, display safety, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--high-growth-component-attribution",
        "--show-high-growth-component-attribution",
        "generate_high_growth_component_attribution",
        "show_high_growth_component_attribution",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing high-growth component attribution token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS + OPTIONAL_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, bot_source: str, failures: list[str]) -> None:
    required = [
        "component_attribution_created_research_only",
        "component_attribution_partial_manual_review_required",
        "component_attribution_blocked_missing_saved_component_data",
        "component_attribution_blocked_future_builder_required",
        "component_attribution_blocked_missing_ticker_holdings",
        "component_attribution_blocked_missing_component_returns",
        "component_drawdown_contribution_blocked_missing_ticker_level_returns",
        "component_drawdown_contribution_blocked_missing_holding_weights",
        "future_component_stream_builder_required",
        "future --high-growth-component-streams command may be needed",
        HIGH_GROWTH_SLEEVE,
        "ticker_concentration_data_missing",
        "component_concentration_manual_review_required",
        "concentration review status",
        "component_ticker",
        "average_weight",
        "total_weighted_contribution",
        "contribution_share_of_high_growth_drawdown",
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"high-growth component attribution module missing required token: {token}")

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
            failures.append(f"high-growth component attribution module must not contain forbidden token: {token}")

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

    show_slice = source_slice(module_source, "def show_high_growth_component_attribution", "def load_sources")
    if "write_rows" in show_slice or "generate_high_growth_component_attribution" in show_slice:
        failures.append("display command must be saved-read-only and must not regenerate outputs")

    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--high-growth-component-attribution"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("high-growth component attribution route must not call execution commands")


def verify_blocked_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_sleeve_only_fixture(root)
        result = generate_high_growth_component_attribution(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_component_attribution_status") != STATUS_BLOCKED:
            failures.append("sleeve-only saved data should block component attribution")
        if result.contribution_rows:
            failures.append("blocked path must not create fake component contribution rows")
        if not any(row.get("blocker_name") == "component_attribution_blocked_missing_ticker_holdings" for row in result.blocker_rows):
            failures.append("blocked path should include missing ticker holdings blocker")
        if not any(row.get("blocker_name") == "future_component_stream_builder_required" for row in result.blocker_rows):
            failures.append("blocked path should include future builder blocker")
        requirements = {row.get("data_requirement") for row in result.attribution_rows}
        for expected in {
            "high_growth_sleeve_daily_returns",
            "selected_high_growth_sleeve_name",
            "component_ticker_identifiers",
            "component_holding_dates",
            "component_weights",
            "component_daily_returns",
            "component_weighted_contributions",
            "component_drawdown_window_contributions",
        }:
            if expected not in requirements:
                failures.append(f"availability audit missing requirement: {expected}")
        verify_safety_flags(result.attribution_rows + result.summary_rows, "blocked", failures)
        for row in result.blocker_rows:
            for flag in ["execution_approved", "paper_execution_approved", "crypto_execution_approved", "scheduling_approved"]:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"blocker row should keep {flag}=false")
        code, lines = show_high_growth_component_attribution(root)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        display = "\n".join(lines)
        for token in ["final component attribution status", "component ticker data exists", "concentration review status", "future builder recommendation", "execution_approved=false"]:
            if token not in display:
                failures.append(f"display missing expected token: {token}")


def verify_component_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_component_fixture(root)
        result = generate_high_growth_component_attribution(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_component_attribution_status") != STATUS_CREATED:
            failures.append(f"component fixture should create attribution, got {summary.get('final_component_attribution_status')}")
        if summary.get("concentration_blocker") == "ticker_concentration_data_missing":
            failures.append("component fixture should not report ticker_concentration_data_missing once component data exists")
        if summary.get("concentration_blocker") != "component_concentration_manual_review_required":
            failures.append(f"component fixture should require concentration review, got {summary.get('concentration_blocker')}")
        if not result.contribution_rows:
            failures.append("component fixture should create contribution rows")
        if not result.drawdown_contribution_rows:
            failures.append("component fixture should create drawdown contribution rows")
        first = result.contribution_rows[0] if result.contribution_rows else {}
        for field in ["component_ticker", "average_weight", "max_weight", "total_weighted_contribution", "contribution_share"]:
            if field not in first:
                failures.append(f"component contribution row missing field: {field}")
        drawdown = result.drawdown_contribution_rows[0] if result.drawdown_contribution_rows else {}
        for field in ["drawdown_start", "drawdown_trough", "component_ticker", "component_period_return", "component_weighted_contribution", "contribution_share_of_high_growth_drawdown"]:
            if field not in drawdown:
                failures.append(f"drawdown contribution row missing field: {field}")
        verify_safety_flags(result.contribution_rows + result.drawdown_contribution_rows, "component", failures)


def verify_safety_flags(rows: list[dict[str, object]], label: str, failures: list[str]) -> None:
    for index, row in enumerate(rows):
        for flag in TRUE_FLAGS:
            if str(row.get(flag, "")).lower() != "true":
                failures.append(f"{label} row {index} should keep {flag}=true")
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).lower() != "false":
                failures.append(f"{label} row {index} should keep {flag}=false")


def write_sleeve_only_fixture(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(
        data / "high_growth_return_streams.csv",
        [
            {
                "date": "2021-02-09",
                "candidate_name": HIGH_GROWTH_SLEEVE,
                "daily_strategy_return": "0.01",
                **false_flags_as_strings(),
            }
        ],
    )
    write_csv(
        data / "high_growth_sleeve_quality_summary.csv",
        [
            {"summary_name": "final_high_growth_sleeve_quality_status", "summary_value": "high_growth_sleeve_quality_promising_but_drawdown_sensitive", **false_flags_as_strings()},
            {"summary_name": "concentration_dependency_finding", "summary_value": "ticker_concentration_data_missing", **false_flags_as_strings()},
        ],
    )
    write_csv(
        data / "high_growth_sleeve_quality_drawdowns.csv",
        [
            {
                "drawdown_start": "2021-02-09",
                "drawdown_trough": "2021-02-12",
                **false_flags_as_strings(),
            }
        ],
    )


def write_component_fixture(root: Path) -> None:
    write_sleeve_only_fixture(root)
    rows = []
    for day, aaa_return, bbb_return in [
        ("2021-02-09", -0.05, -0.01),
        ("2021-02-10", -0.04, -0.02),
        ("2021-02-11", 0.02, -0.01),
        ("2021-02-12", 0.01, 0.02),
    ]:
        rows.extend(
            [
                component_row(day, "AAA", "0.60", aaa_return),
                component_row(day, "BBB", "0.40", bbb_return),
            ]
        )
    write_csv(root / "data" / "high_growth_component_streams.csv", rows)


def component_row(day: str, ticker: str, weight: str, daily_return: float) -> dict[str, str]:
    weighted = float(weight) * daily_return
    return {
        "date": day,
        "component_ticker": ticker,
        "component_weight": weight,
        "component_daily_return": str(daily_return),
        "component_weighted_contribution": str(weighted),
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
