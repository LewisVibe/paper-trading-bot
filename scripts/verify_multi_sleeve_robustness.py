from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_robustness import (  # noqa: E402
    FINAL_STATUS_BLOCKED_MISSING_STREAMS,
    FINAL_STATUS_BLOCKED_QQQ100_RECONCILIATION,
    OUTPUT_FILES,
    PORTFOLIO_CANDIDATE,
    generate_multi_sleeve_robustness,
    show_multi_sleeve_robustness,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_robustness_report.csv",
    "data/multi_sleeve_robustness_summary.csv",
]

REQUIRED_REPORT_COLUMNS = [
    "split_name",
    "candidate_name",
    "period_label",
    "first_date",
    "last_date",
    "row_count",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "delta_CAGR_vs_generated_qqq100",
    "delta_Sharpe_vs_generated_qqq100",
    "delta_MaxDD_vs_generated_qqq100",
    "delta_Calmar_vs_generated_qqq100",
    "qqq100_reference_source_used",
    "recovered_reference_available",
    "old_generated_reference_retained",
    "comparison_reference_name",
    "comparison_reference_status",
    "delta_CAGR_vs_qqq100_reference",
    "delta_Sharpe_vs_qqq100_reference",
    "delta_MaxDD_vs_qqq100_reference",
    "delta_Calmar_vs_qqq100_reference",
    "robustness_status",
    "blocker_status",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "scheduling_approved",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_robustness.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_streams_blocked(failures)

    if failures:
        print("Multi-sleeve robustness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Multi-sleeve robustness verification passed.")
    print("Verified saved-output-only split robustness, blockers, display safety, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-robustness",
        "--show-multi-sleeve-robustness",
        "generate_multi_sleeve_robustness",
        "show_multi_sleeve_robustness",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing multi-sleeve robustness token: {token}")


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
        "multi_sleeve_robustness_promising",
        "multi_sleeve_robustness_mixed",
        "multi_sleeve_robustness_weak",
        "multi_sleeve_robustness_blocked_missing_streams",
        "multi_sleeve_robustness_blocked_qqq100_reconciliation",
        "qqq100_plus_high_growth_research",
        "generated_qqq100_reference",
        "codex_broad_growth_balanced_breakout_control",
        "split_60_40",
        "split_70_30",
        "split_80_20",
        "saved_metrics_context_only_not_daily_stream",
        "comparison_reference_name",
        "comparison_reference_status",
        "Calmar wins vs preferred QQQ100 reference",
        "Sharpe wins vs preferred QQQ100 reference",
        "execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"multi-sleeve robustness module missing required token: {token}")

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
        "execution_ready",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"multi-sleeve robustness module must not contain forbidden token: {token}")

    show_slice = source_slice(module_source, "def show_multi_sleeve_robustness", "def build_report_rows")
    if "write_rows" in show_slice or "generate_multi_sleeve_robustness" in show_slice:
        failures.append("display command must be saved-read-only and must not regenerate outputs")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--multi-sleeve-robustness"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("multi-sleeve robustness route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--multi-sleeve-robustness" in execute_block:
        failures.append("existing paper execution behavior should not be expanded by robustness command")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_sleeve_stream_fixture(root / "data" / "sleeve_return_streams.csv")
        write_high_growth_stream_fixture(root / "data" / "high_growth_return_streams.csv")
        write_backtest_summary_fixture(root / "data" / "multi_sleeve_portfolio_backtest_summary.csv", needs_reconciliation=True)
        result = generate_multi_sleeve_robustness(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.report_rows:
            failures.append("robustness report rows should be generated")
            return

        for column in REQUIRED_REPORT_COLUMNS:
            if column not in result.report_rows[0]:
                failures.append(f"robustness report missing required column: {column}")

        split_names = {row.get("split_name") for row in result.report_rows}
        for expected in ["split_60_40", "split_70_30", "split_80_20"]:
            if expected not in split_names:
                failures.append(f"missing split output: {expected}")

        candidates = {row.get("candidate_name") for row in result.report_rows}
        for expected in [PORTFOLIO_CANDIDATE, "preferred_qqq100_reference", "codex_broad_growth_balanced_breakout_control"]:
            if expected not in candidates:
                failures.append(f"missing candidate row: {expected}")

        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_robustness_status") != FINAL_STATUS_BLOCKED_QQQ100_RECONCILIATION:
            failures.append("reconciliation gap should block final robustness status")
        if "reconcile_generated_qqq100_stream" not in summary.get("required_next_step", ""):
            failures.append("reconciliation gap should drive required next step")
        if summary.get("split_count") != "3":
            failures.append("complete fixture should produce three candidate split rows")
        if "not_promotion_ready" not in summary.get("key_blockers", ""):
            failures.append("summary should explicitly avoid promotion-ready labels")
        if summary.get("key_blockers", "").startswith("none;"):
            failures.append("key blockers should not start with none before real blockers")
        if summary.get("qqq100_reference_source_used") != "old_generated_qqq100_reference":
            failures.append("fallback fixture should use old generated QQQ100 reference")
        if summary.get("old_generated_reference_retained") != "true":
            failures.append("old generated reference should remain retained")
        if summary.get("comparison_reference_name") in {"", None, "missing"}:
            failures.append("summary should include comparison reference name")
        if summary.get("comparison_reference_status") in {"", None, "missing"}:
            failures.append("summary should include comparison reference status")

        for collection in [result.report_rows, result.summary_rows]:
            for row in collection:
                if str(row.get("research_only", "")).lower() != "true":
                    failures.append("research_only should remain true")
                if str(row.get("preview_only", "")).lower() != "true":
                    failures.append("preview_only should remain true")
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false")

        code, lines = show_multi_sleeve_robustness(root)
        if code != 0 or not any("final robustness status" in line for line in lines):
            failures.append("saved display should show final robustness status")
        if not any("execution_approved=false" in line for line in lines):
            failures.append("saved display should preserve false execution flag")
        if not any("Calmar wins vs preferred QQQ100 reference" in line for line in lines):
            failures.append("saved display should use preferred-reference wording for Calmar wins")
        if any("Calmar wins vs generated QQQ100" in line or "Sharpe wins vs generated QQQ100" in line for line in lines):
            failures.append("saved display should not use stale generated-Q label for win counts")
        if any("key blockers: none;" in line for line in lines):
            failures.append("saved display should not show none before real blockers")


def verify_missing_streams_blocked(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_sleeve_stream_fixture(root / "data" / "sleeve_return_streams.csv")
        write_backtest_summary_fixture(root / "data" / "multi_sleeve_portfolio_backtest_summary.csv", needs_reconciliation=False)
        result = generate_multi_sleeve_robustness(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_robustness_status") != FINAL_STATUS_BLOCKED_MISSING_STREAMS:
            failures.append("missing high-growth stream should be labelled blocked_missing_streams")
        if "create_real_saved_return_streams" not in summary.get("required_next_step", ""):
            failures.append("missing streams should require real saved return streams")


def write_sleeve_stream_fixture(path: Path) -> None:
    headers = ["date", "candidate_name", "daily_strategy_return", "signal_state"]
    rows: list[list[str]] = []
    for index in range(120):
        day = f"2024-01-{(index % 28) + 1:02d}"
        month = 1 + index // 28
        date = f"2024-{month:02d}-{(index % 28) + 1:02d}"
        qqq = 0.0018 if index % 9 else -0.0045
        cash = 0.0
        rows.append([date, "qqq_100_trend_gate", str(qqq), "risk_on"])
        rows.append([date, "cash_default_defensive_sleeve", str(cash), "cash"])
        if day == "":
            rows.append([date, "unused", "0", "unused"])
    write_fixture(path, headers, rows)


def write_high_growth_stream_fixture(path: Path) -> None:
    headers = ["date", "candidate_name", "daily_strategy_return", "signal_state"]
    rows: list[list[str]] = []
    for index in range(120):
        month = 1 + index // 28
        date = f"2024-{month:02d}-{(index % 28) + 1:02d}"
        value = 0.0035 if index % 11 else -0.009
        rows.append([date, "codex_broad_growth_balanced_breakout_control", str(value), "risk_on"])
    write_fixture(path, headers, rows)


def write_backtest_summary_fixture(path: Path, needs_reconciliation: bool) -> None:
    reconciliation = (
        "generated_qqq100_reference_needs_reconciliation_with_saved_benchmark"
        if needs_reconciliation
        else "generated_qqq100_reference_aligned_with_saved_benchmark"
    )
    rows = [
        ["saved_benchmark_reconciliation_status", reconciliation, "fixture"],
        ["saved_qqq100_benchmark_cagr", "16.8429", "fixture"],
        ["saved_qqq100_benchmark_sharpe", "1.0027", "fixture"],
        ["saved_qqq100_benchmark_max_drawdown", "-23.4576", "fixture"],
        ["saved_qqq100_benchmark_calmar", "0.718", "fixture"],
        ["missing_sleeve_data_warnings", "crypto return streams missing", "fixture"],
    ]
    write_fixture(path, ["summary_name", "summary_value", "details"], rows)


def write_fixture(path: Path, headers: list[str], rows: list[list[str]]) -> None:
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
