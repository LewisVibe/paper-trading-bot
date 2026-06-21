from __future__ import annotations

import csv
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_weight_sensitivity import (  # noqa: E402
    ALLOCATIONS,
    CRYPTO_SLEEVE,
    CURRENT_ALLOCATION,
    HIGH_GROWTH_SLEEVE,
    OUTPUT_FILES,
    RECOVERED_REFERENCE,
    STATUS_BLOCKED_MISSING,
    generate_multi_sleeve_weight_sensitivity,
    show_multi_sleeve_weight_sensitivity,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_weight_sensitivity.csv",
    "data/multi_sleeve_weight_sensitivity_summary.csv",
    "data/multi_sleeve_weight_sensitivity_blockers.csv",
]

REQUIRED_REVIEW_COLUMNS = [
    "candidate_name",
    "qqq100_weight",
    "high_growth_weight",
    "crypto_weight",
    "defensive_weight",
    "weight_sum",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "delta_CAGR_vs_recovered_qqq100",
    "delta_Sharpe_vs_recovered_qqq100",
    "delta_MaxDD_vs_recovered_qqq100",
    "delta_Calmar_vs_recovered_qqq100",
    "delta_CAGR_vs_current_75_15_5_5",
    "delta_Sharpe_vs_current_75_15_5_5",
    "delta_MaxDD_vs_current_75_15_5_5",
    "delta_Calmar_vs_current_75_15_5_5",
    "risk_status",
    "allocation_policy_status",
    "warning_status",
    "required_next_step",
    "execution_approved",
    "crypto_execution_approved",
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
    "crypto_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

TRUE_FLAGS = ["research_only", "preview_only", "saved_output_only"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_weight_sensitivity.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_allocation_specs(failures)
    verify_temp_generation(failures)
    verify_missing_streams(failures)

    if failures:
        print("Multi-sleeve weight sensitivity verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Multi-sleeve weight sensitivity verification passed.")
    print("Verified fixed allocations, saved-stream-only metrics, blockers, display safety, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-weight-sensitivity",
        "--show-multi-sleeve-weight-sensitivity",
        "generate_multi_sleeve_weight_sensitivity",
        "show_multi_sleeve_weight_sensitivity",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing weight sensitivity token: {token}")


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
        "weight_sensitivity_current_allocation_promising",
        "weight_sensitivity_current_allocation_mixed",
        "weight_sensitivity_crypto_adds_return_but_vol_sensitive",
        "weight_sensitivity_high_growth_drives_return_and_drawdown",
        "weight_sensitivity_needs_manual_review",
        "weight_sensitivity_blocked_missing_saved_streams",
        CURRENT_ALLOCATION,
        "lower_crypto_77_15_3_5",
        "no_crypto_80_15_0_5",
        "higher_crypto_73_15_7_5",
        "higher_growth_70_20_5_5",
        RECOVERED_REFERENCE,
        HIGH_GROWTH_SLEEVE,
        CRYPTO_SLEEVE,
        "execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"weight sensitivity module missing required token: {token}")

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
        "promotion-ready",
        "promotion_ready",
        "execution-ready",
        "execution_ready",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"weight sensitivity module must not contain forbidden token: {token}")

    show_slice = source_slice(module_source, "def show_multi_sleeve_weight_sensitivity", "def missing_streams")
    if "write_rows" in show_slice or "generate_multi_sleeve_weight_sensitivity" in show_slice:
        failures.append("weight sensitivity display command must be saved-read-only and must not regenerate outputs")

    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--multi-sleeve-weight-sensitivity"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("weight sensitivity route must not call execution commands")


def verify_allocation_specs(failures: list[str]) -> None:
    names = {name for name, *_weights in ALLOCATIONS}
    for expected in [
        "current_75_15_5_5",
        "lower_crypto_77_15_3_5",
        "no_crypto_80_15_0_5",
        "lower_growth_80_10_5_5",
        "balanced_lower_risk_85_10_0_5",
        "higher_crypto_73_15_7_5",
        "higher_growth_70_20_5_5",
    ]:
        if expected not in names:
            failures.append(f"missing fixed allocation: {expected}")
    for name, qqq_weight, high_growth_weight, crypto_weight, defensive_weight in ALLOCATIONS:
        if qqq_weight + high_growth_weight + crypto_weight + defensive_weight != 100:
            failures.append(f"allocation does not sum to 100: {name}")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data")
        result = generate_multi_sleeve_weight_sensitivity(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if len(result.review_rows) != len(ALLOCATIONS):
            failures.append("review should include every fixed allocation exactly once")
            return

        for column in REQUIRED_REVIEW_COLUMNS:
            if column not in result.review_rows[0]:
                failures.append(f"review row missing required column: {column}")

        rows_by_name = {row["candidate_name"]: row for row in result.review_rows}
        for expected in ["current_75_15_5_5", "no_crypto_80_15_0_5", "lower_crypto_77_15_3_5", "higher_crypto_73_15_7_5", "higher_growth_70_20_5_5"]:
            if expected not in rows_by_name:
                failures.append(f"missing generated row: {expected}")

        for row in result.review_rows:
            if str(row.get("weight_sum")) != "100":
                failures.append(f"generated weight sum should be 100 for {row.get('candidate_name')}")

        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        for key in [
            "final_weight_sensitivity_status",
            "fixed_allocations_tested",
            "current_allocation_metrics",
            "best_calmar_allocation",
            "best_sharpe_allocation",
            "lowest_maxdd_allocation",
            "no_crypto_result",
            "higher_crypto_interpretation",
            "higher_growth_interpretation",
            "required_next_step",
        ]:
            if key not in summary:
                failures.append(f"summary missing required key: {key}")
        if summary.get("fixed_allocations_tested") != str(len(ALLOCATIONS)):
            failures.append("summary allocation count should match fixed allocation set")

        verify_safety_flags(result.review_rows + result.summary_rows + result.blocker_rows, "generated", failures)

        code, lines = show_multi_sleeve_weight_sensitivity(root)
        output = "\n".join(lines)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        for token in [
            "final weight-sensitivity status",
            "fixed allocations tested",
            "best Calmar allocation",
            "best Sharpe allocation",
            "lowest MaxDD allocation",
            "no-crypto result",
            "higher-crypto interpretation",
            "higher-growth interpretation",
            "execution_approved=false",
            "crypto_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if token not in output:
                failures.append(f"display missing expected token: {token}")


def verify_missing_streams(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_multi_sleeve_weight_sensitivity(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_weight_sensitivity_status") != STATUS_BLOCKED_MISSING:
            failures.append("missing saved streams should block weight sensitivity review")
        if "missing_saved_streams" not in {row.get("blocker_name") for row in result.blocker_rows}:
            failures.append("missing-stream path should write missing_saved_streams blocker")
        verify_safety_flags(result.review_rows + result.summary_rows + result.blocker_rows, "missing", failures)


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
    dates = [(date(2020, 1, 1) + timedelta(days=index)).isoformat() for index in range(300)]
    write_recovered_stream(data / "qqq100_recovered_reference_stream.csv", dates)
    write_high_growth_stream(data / "high_growth_return_streams.csv", dates)
    write_crypto_stream(data / "crypto_return_streams.csv", dates)
    write_csv(
        data / "multi_sleeve_allocation_policy_summary.csv",
        [summary_row("final_allocation_policy_status", "allocation_policy_promising_but_crypto_sensitive")],
    )
    write_csv(
        data / "multi_sleeve_crypto_review_summary.csv",
        [summary_row("final_crypto_review_status", "multi_sleeve_crypto_review_promising_research_only")],
    )


def write_recovered_stream(path: Path, dates: list[str]) -> None:
    rows = [
        {
            "date": day,
            "candidate_name": RECOVERED_REFERENCE,
            "daily_strategy_return": str(-0.02 if index in {80, 81} else 0.00055),
            "reference_status": "qqq100_reconstruction_close_enough_for_research_review",
            **false_flags_as_strings(),
        }
        for index, day in enumerate(dates)
    ]
    write_csv(path, rows)


def write_high_growth_stream(path: Path, dates: list[str]) -> None:
    rows = [
        {
            "date": day,
            "candidate_name": HIGH_GROWTH_SLEEVE,
            "daily_strategy_return": str(-0.035 if index in {90, 91, 92} else 0.0012),
            **false_flags_as_strings(),
        }
        for index, day in enumerate(dates)
    ]
    write_csv(path, rows)


def write_crypto_stream(path: Path, dates: list[str]) -> None:
    rows = []
    for index, day in enumerate(dates):
        rows.append(
            {
                "date": day,
                "sleeve_name": CRYPTO_SLEEVE,
                "daily_return": str(-0.08 if index in {60, 61, 140} else 0.0015),
                **false_flags_as_strings(),
            }
        )
    write_csv(path, rows)


def summary_row(name: str, value: str) -> dict[str, str]:
    return {"summary_name": name, "summary_value": value}


def false_flags_as_strings() -> dict[str, str]:
    return {
        "orders_created": "false",
        "orders_submitted": "false",
        "orders_cancelled": "false",
        "orders_replaced": "false",
        "alpaca_called": "false",
        "live_position_read": "false",
        "sqlite_trade_log_written": "false",
        "discord_alert_sent": "false",
        "telegram_alert_sent": "false",
        "execution_approved": "false",
        "paper_execution_approved": "false",
        "crypto_execution_approved": "false",
        "scheduling_approved": "false",
        "live_trading_approved": "false",
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
