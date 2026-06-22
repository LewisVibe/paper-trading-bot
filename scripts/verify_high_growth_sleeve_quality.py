from __future__ import annotations

import csv
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.high_growth_sleeve_quality import (  # noqa: E402
    HIGH_GROWTH_SLEEVE,
    OUTPUT_FILES,
    STATUS_BLOCKED,
    generate_high_growth_sleeve_quality_review,
    show_high_growth_sleeve_quality_review,
)


EXPECTED_OUTPUTS = [
    "data/high_growth_sleeve_quality_review.csv",
    "data/high_growth_sleeve_quality_summary.csv",
    "data/high_growth_sleeve_quality_splits.csv",
    "data/high_growth_sleeve_quality_drawdowns.csv",
    "data/high_growth_sleeve_quality_blockers.csv",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "high_growth_sleeve_quality.py")
    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_streams(failures)
    if failures:
        print("High-growth sleeve quality verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("High-growth sleeve quality verification passed.")
    print("Verified saved-stream-only metrics, splits, drawdown/recovery, concentration blocker, display, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--high-growth-sleeve-quality-review",
        "--show-high-growth-sleeve-quality-review",
        "generate_high_growth_sleeve_quality_review",
        "show_high_growth_sleeve_quality_review",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing high-growth sleeve quality token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, bot_source: str, failures: list[str]) -> None:
    required = [
        HIGH_GROWTH_SLEEVE,
        "split_60_40",
        "split_70_30",
        "split_80_20",
        "ticker_concentration_data_missing",
        "incremental_drawdown_contributor",
        "net_incremental_drawdown_effect",
        "post_trough_63d_return",
        "post_trough_126d_return",
        "high_growth_sleeve_quality_promising_but_drawdown_sensitive",
        "high_growth_sleeve_quality_split_sensitive_manual_review",
        "high_growth_sleeve_quality_blocked_missing_saved_streams",
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "live_trading_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"quality module missing required token: {token}")
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
        "Register-ScheduledTask",
        "create_scheduled_task",
        "automation_update",
        "load_config",
        "config.json",
        "execution-ready",
        "promotion-ready",
        "order-ready",
        "crypto-execution-ready",
        "scheduled",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"quality module must not contain forbidden token: {token}")
    stripped = module_source.lower()
    for token in [
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "live_trading_approved",
        "scheduling_approved",
        "shorting_approved",
        "leverage_approved",
        "margin_approved",
    ]:
        stripped = stripped.replace(token, "")
    if "approved" in stripped:
        failures.append("word approved should appear only in explicit false approval fields")
    show_slice = source_slice(module_source, "def show_high_growth_sleeve_quality_review", "def build_review_row")
    if "write_rows" in show_slice or "generate_high_growth_sleeve_quality_review" in show_slice:
        failures.append("quality display must be saved-read-only and must not regenerate outputs")
    route = source_slice(bot_source, 'if sys.argv[1:] == ["--high-growth-sleeve-quality-review"]', 'if sys.argv[1:] == ["--paper-execution-state-summary"]')
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("quality route must not call execution commands")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data")
        result = generate_high_growth_sleeve_quality_review(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("selected_high_growth_sleeve") != HIGH_GROWTH_SLEEVE:
            failures.append("selected high-growth sleeve should be included")
        if "high_growth_sleeve_quality_" not in summary.get("final_high_growth_sleeve_quality_status", ""):
            failures.append("final status should be cautious high-growth sleeve quality label")
        split_names = {row.get("split_name") for row in result.split_rows}
        for split in ["split_60_40", "split_70_30", "split_80_20"]:
            if split not in split_names:
                failures.append(f"missing split row: {split}")
        for column in ["drawdown_start", "drawdown_trough", "max_drawdown", "recovery_date", "post_trough_63d_return", "post_trough_126d_return", "drawdown_recovery_status"]:
            if column not in result.drawdown_rows[0]:
                failures.append(f"drawdown row missing column: {column}")
        for column in ["selected_lead_candidate", "high_growth_weight_in_lead", "delta_high_growth_weight", "incremental_drawdown_contributor", "net_incremental_drawdown_effect", "portfolio_CAGR_delta"]:
            if column not in result.review_rows[0]:
                failures.append(f"review row missing contribution column: {column}")
        if result.review_rows[0].get("concentration_dependency_status") != "ticker_concentration_data_missing":
            failures.append("fixture without component attribution should label ticker concentration data missing")
        if "ticker_concentration_data_missing" not in {row.get("blocker_name") for row in result.blocker_rows}:
            failures.append("missing ticker attribution should create blocker row")
        verify_safety_flags(result.review_rows + result.summary_rows + result.split_rows + result.drawdown_rows, "generated", failures)
        for row in result.blocker_rows:
            for flag in ["execution_approved", "crypto_execution_approved", "scheduling_approved"]:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"blocker row should keep {flag}=false")
        code, lines = show_high_growth_sleeve_quality_review(root)
        output = "\n".join(lines)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        for token in [
            "final high-growth sleeve quality status",
            "selected high-growth sleeve",
            "sleeve metrics",
            "split summary and worst split",
            "worst drawdown and recovery",
            "contribution to selected lead",
            "concentration/dependency finding",
            "execution_approved=false",
            "crypto_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if token not in output:
                failures.append(f"display missing expected token: {token}")


def verify_missing_streams(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_high_growth_sleeve_quality_review(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_high_growth_sleeve_quality_status") != STATUS_BLOCKED:
            failures.append("missing stream should block quality review")
        if "saved_output_completeness" not in {row.get("blocker_name") for row in result.blocker_rows}:
            failures.append("missing stream should write saved_output_completeness blocker")
        verify_safety_flags(result.review_rows + result.summary_rows + result.split_rows + result.drawdown_rows, "missing", failures)


def verify_safety_flags(rows: list[dict[str, object]], label: str, failures: list[str]) -> None:
    for index, row in enumerate(rows):
        for flag in TRUE_FLAGS:
            if str(row.get(flag, "")).lower() != "true":
                failures.append(f"{label} row {index} should keep {flag}=true")
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).lower() != "false":
                failures.append(f"{label} row {index} should keep {flag}=false")


def write_fixture(data: Path) -> None:
    data.mkdir(parents=True, exist_ok=True)
    flags = false_flags_as_strings()
    dates = [(date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(260)]
    stream_rows = []
    for index, day in enumerate(dates):
        daily = -0.045 if 55 <= index <= 62 else 0.0022
        stream_rows.append({"date": day, "candidate_name": HIGH_GROWTH_SLEEVE, "daily_strategy_return": str(daily), "daily_return": str(daily), **flags})
    write_csv(data / "high_growth_return_streams.csv", stream_rows)
    write_csv(
        data / "multi_sleeve_lead_state.csv",
        [
            {
                "current_research_lead_candidate": "higher_growth_70_20_5_5",
                "delta_CAGR": "1.9306",
                "delta_Sharpe": "0.038",
                "delta_MaxDD": "-0.272",
                "delta_Calmar": "0.0739",
                **flags,
            }
        ],
    )
    write_csv(
        data / "multi_sleeve_research_lead_decision.csv",
        [{"delta_CAGR": "1.9306", "delta_Sharpe": "0.038", "delta_MaxDD": "-0.272", "delta_Calmar": "0.0739", **flags}],
    )
    write_csv(
        data / "multi_sleeve_high_growth_drawdown_summary.csv",
        [
            summary_row("main_incremental_drawdown_contributor", "extra_high_growth_weight"),
            summary_row("incremental_high_growth_risk_summary", "high_growth=-1.4069; qqq100=1.0684; net=-0.3386; contributor=extra_high_growth_weight"),
        ],
    )


def summary_row(name: str, value: str) -> dict[str, str]:
    return {"summary_name": name, "summary_value": value}


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
