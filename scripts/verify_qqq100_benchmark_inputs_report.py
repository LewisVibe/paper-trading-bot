from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.qqq100_benchmark_inputs import (  # noqa: E402
    OUTPUT_FILES,
    generate_qqq100_benchmark_inputs_report,
    show_qqq100_benchmark_inputs,
)


EXPECTED_OUTPUTS = [
    "data/qqq100_benchmark_inputs_report.csv",
    "data/qqq100_benchmark_inputs_summary.csv",
    "data/qqq100_benchmark_input_gaps.csv",
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
    "scheduling_approved",
    "live_trading_approved",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "qqq100_benchmark_inputs.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_saved_display_only(module_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)

    if failures:
        print("QQQ100 benchmark inputs report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 benchmark inputs report verification passed.")
    print("Verified partial source reconstruction, unresolved gaps, saved-output-only display, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--qqq100-benchmark-inputs-report",
        "--show-qqq100-benchmark-inputs",
        "generate_qqq100_benchmark_inputs_report",
        "show_qqq100_benchmark_inputs",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing QQQ100 benchmark-input token: {token}")


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
        "source_partially_recovered",
        "source_not_recovered_constants_only",
        "benchmark_definition_unknown",
        "original_daily_stream_missing",
        "fa1d63d:trading_bot/research/qqq_leverage_validation.py",
        "ae0ab7f:trading_bot/research/qqq_lead_decision.py",
        "4aebc22:trading_bot/research/project_research_state_refresh.py",
        "TREND_WINDOW=200",
        "auto_adjust=True",
        "period='10y'",
        "interval='1d'",
        "SMA200 trend gate",
        "prior-close signal",
        "next-bar close-to-close returns",
        "10 bps exposure-change cost",
        "recover_or_regenerate_original_qqq_leverage_validation_daily_stream_before_updating_stream_generation",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"QQQ100 benchmark-input module missing required token: {token}")

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
        "import yfinance",
        "yf.download",
        "subprocess.run",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"QQQ100 benchmark-input module must not contain execution/config/network token: {token}")


def verify_saved_display_only(module_source: str, failures: list[str]) -> None:
    display_block = source_slice(module_source, "def show_qqq100_benchmark_inputs", "def build_report_row")
    for token in ["write_rows(", "generate_qqq100_benchmark_inputs_report(", "yf.download", "TradingClient"]:
        if token in display_block:
            failures.append(f"saved display should not regenerate or call external services: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--qqq100-benchmark-inputs-report"]',
        'if sys.argv[1:] == ["--high-growth-return-streams"]',
    )
    for token in ["run_execute_qqq100_paper", "run_paper_order_test", "submit_order", "TradingClient"]:
        if token in route:
            failures.append(f"QQQ100 benchmark-input route must not call execution/broker token: {token}")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--qqq100-benchmark-inputs-report" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by benchmark-input command")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_qqq100_benchmark_inputs_report(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.report_rows or not result.summary_rows or not result.gap_rows:
            failures.append("report, summary, and gap rows should be generated")
            return

        report = result.report_rows[0]
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        gaps = {row["gap_name"]: row for row in result.gap_rows}

        expected_columns = [
            "benchmark_name",
            "saved_CAGR",
            "saved_Sharpe",
            "saved_MaxDD",
            "saved_Calmar",
            "recovered_source_status",
            "likely_strategy_source",
            "likely_data_source",
            "likely_date_range",
            "likely_signal_timing",
            "likely_price_field",
            "likely_adjustment_status",
            "likely_warmup_rule",
            "likely_cost_assumption",
            "likely_cash_handling",
            "likely_metric_method",
            "likely_annualisation",
            "confidence_level",
            "unresolved_gap",
            "required_next_step",
        ]
        for column in expected_columns:
            if column not in report:
                failures.append(f"report row missing expected column: {column}")

        if report.get("benchmark_name") != "qqq_100_trend_gate":
            failures.append("benchmark name should remain qqq_100_trend_gate")
        if report.get("saved_CAGR") != "16.8429" or report.get("saved_Sharpe") != "1.0027":
            failures.append("saved benchmark metrics should preserve the known QQQ100 values")
        if report.get("saved_MaxDD") != "-23.4576" or report.get("saved_Calmar") != "0.718":
            failures.append("saved drawdown/Calmar metrics should preserve the known QQQ100 values")
        if report.get("recovered_source_status") in {"fully_reconciled", "stream_generation_updated"}:
            failures.append("source status must not claim full reconciliation")
        if "original_daily_stream_missing" not in report.get("unresolved_gap", ""):
            failures.append("report must explicitly keep the original daily stream gap open")
        if "qqq_leverage_validation.py" not in report.get("likely_strategy_source", ""):
            failures.append("report should identify the likely original QQQ leverage validation source")
        if "yfinance QQQ daily data" not in report.get("likely_data_source", ""):
            failures.append("report should identify the likely QQQ yfinance data source")
        if "10y" not in report.get("likely_date_range", ""):
            failures.append("report should state likely 10y date-range source")
        if "prior close" not in report.get("likely_signal_timing", "").replace("-", " "):
            failures.append("report should state prior-close signal timing")
        if "200" not in report.get("likely_warmup_rule", ""):
            failures.append("report should state SMA200/warmup handling")
        if "10 bps" not in report.get("likely_cost_assumption", ""):
            failures.append("report should state likely cost assumption")
        if "zero return" not in report.get("likely_cash_handling", ""):
            failures.append("report should state likely cash handling")
        if summary.get("recovered_source_status") != "source_partially_recovered":
            failures.append("summary should preserve partial source-recovery status")
        if "original_daily_stream_missing" not in summary.get("unresolved_gaps", ""):
            failures.append("summary should keep unresolved daily stream gap")
        if "original_daily_stream_missing" not in gaps:
            failures.append("gap output should include original_daily_stream_missing")
        if gaps.get("original_daily_stream_missing", {}).get("gap_status") != "blocked":
            failures.append("original daily stream gap should remain blocked")
        if "stream generation" not in summary.get("required_next_step", "").replace("_", " "):
            failures.append("required next step should block stream-generation changes until recovery/regeneration")

        for collection in [result.report_rows, result.summary_rows, result.gap_rows]:
            for row in collection:
                if str(row.get("research_only", "")).lower() != "true":
                    failures.append("research_only should remain true")
                if str(row.get("report_only", "")).lower() != "true":
                    failures.append("report_only should remain true")
                if str(row.get("saved_output_only", "")).lower() != "true":
                    failures.append("saved_output_only should remain true")
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false")

        code, lines = show_qqq100_benchmark_inputs(root)
        if code != 0:
            failures.append("saved display should succeed after report generation")
        display_text = "\n".join(lines)
        for token in ["source_partially_recovered", "original_daily_stream_missing", "execution_approved=false"]:
            if token not in display_text:
                failures.append(f"saved display missing expected token: {token}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index == -1:
        return ""
    end_index = source.find(end, start_index + len(start))
    if end_index == -1:
        return source[start_index:]
    return source[start_index:end_index]


if __name__ == "__main__":
    raise SystemExit(main())
