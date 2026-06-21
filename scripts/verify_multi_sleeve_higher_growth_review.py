from __future__ import annotations

import csv
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_higher_growth_review import (  # noqa: E402
    COST_STRESSES,
    CRYPTO_SLEEVE,
    CURRENT_ALLOCATION,
    HIGHER_GROWTH_ALLOCATION,
    HIGH_GROWTH_SLEEVE,
    OUTPUT_FILES,
    RECOVERED_REFERENCE,
    SPLITS,
    STATUS_BLOCKED_MISSING,
    generate_multi_sleeve_higher_growth_review,
    show_multi_sleeve_higher_growth_review,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_higher_growth_review.csv",
    "data/multi_sleeve_higher_growth_summary.csv",
    "data/multi_sleeve_higher_growth_split_review.csv",
    "data/multi_sleeve_higher_growth_cost_review.csv",
    "data/multi_sleeve_higher_growth_drawdown_review.csv",
    "data/multi_sleeve_higher_growth_blockers.csv",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_higher_growth_review.py")
    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_streams(failures)
    if failures:
        print("Multi-sleeve higher-growth review verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Multi-sleeve higher-growth review verification passed.")
    print("Verified saved-stream-only headline, split, cost, drawdown, contribution, display, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-higher-growth-review",
        "--show-multi-sleeve-higher-growth-review",
        "generate_multi_sleeve_higher_growth_review",
        "show_multi_sleeve_higher_growth_review",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing higher-growth review token: {token}")


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
        "higher_growth_review_new_research_lead_candidate",
        "higher_growth_review_promising_but_drawdown_sensitive",
        "higher_growth_review_split_sensitive_challenger",
        "higher_growth_review_cost_sensitive_challenger",
        "higher_growth_review_rejected_drawdown_or_split_risk",
        "higher_growth_review_blocked_missing_saved_streams",
        CURRENT_ALLOCATION[0],
        HIGHER_GROWTH_ALLOCATION[0],
        "split_60_40",
        "split_70_30",
        "split_80_20",
        "plus_100bps_high_growth_turnover",
        "qqq100_contribution_delta",
        "high_growth_contribution_delta",
        "crypto_contribution_delta",
        "defensive_contribution_delta",
        RECOVERED_REFERENCE,
        HIGH_GROWTH_SLEEVE,
        CRYPTO_SLEEVE,
        "execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"higher-growth review module missing required token: {token}")
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
        "execution-ready",
        "order-ready",
        "scheduled",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"higher-growth review module must not contain forbidden token: {token}")
    show_slice = source_slice(module_source, "def show_multi_sleeve_higher_growth_review", "def build_review_rows")
    if "write_rows" in show_slice or "generate_multi_sleeve_higher_growth_review" in show_slice:
        failures.append("higher-growth display must be saved-read-only and must not regenerate outputs")
    route = source_slice(bot_source, 'if sys.argv[1:] == ["--multi-sleeve-higher-growth-review"]', 'if sys.argv[1:] == ["--paper-execution-state-summary"]')
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("higher-growth route must not call execution commands")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data")
        result = generate_multi_sleeve_higher_growth_review(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")
        if {row.get("allocation_name") for row in result.review_rows} != {CURRENT_ALLOCATION[0], HIGHER_GROWTH_ALLOCATION[0]}:
            failures.append("headline review should include current and higher-growth allocations")
        split_names = {row.get("split_name") for row in result.split_rows}
        for split, _ in SPLITS:
            if split not in split_names:
                failures.append(f"missing split row: {split}")
        cost_names = {row.get("cost_stress_name") for row in result.cost_rows}
        for cost, _ in COST_STRESSES:
            if cost not in cost_names:
                failures.append(f"missing cost row: {cost}")
        if not result.drawdown_rows:
            failures.append("drawdown rows should be generated")
        required_review_cols = ["qqq100_contribution_delta", "high_growth_contribution_delta", "crypto_contribution_delta", "defensive_contribution_delta", "contribution_status", "attribution_confidence"]
        for column in required_review_cols:
            if column not in result.review_rows[0]:
                failures.append(f"review missing contribution column: {column}")
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        for key in ["final_higher_growth_review_status", "split_win_count", "worst_split_result", "worst_cost_stress_result", "drawdown_comparison", "contribution_summary", "required_next_step"]:
            if key not in summary:
                failures.append(f"summary missing key: {key}")
        verify_safety_flags(result.review_rows + result.summary_rows + result.split_rows + result.cost_rows + result.drawdown_rows + result.blocker_rows, "generated", failures)
        code, lines = show_multi_sleeve_higher_growth_review(root)
        output = "\n".join(lines)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        for token in ["final higher-growth review status", "split win count", "worst split result", "worst cost stress result", "drawdown comparison", "contribution summary", "execution_approved=false", "crypto_execution_approved=false", "scheduling_approved=false"]:
            if token not in output:
                failures.append(f"display missing expected token: {token}")


def verify_missing_streams(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_multi_sleeve_higher_growth_review(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_higher_growth_review_status") != STATUS_BLOCKED_MISSING:
            failures.append("missing saved streams should block higher-growth review")
        if "missing_saved_streams" not in {row.get("blocker_name") for row in result.blocker_rows}:
            failures.append("missing-stream path should write missing_saved_streams blocker")
        verify_safety_flags(result.review_rows + result.summary_rows + result.split_rows + result.cost_rows + result.drawdown_rows + result.blocker_rows, "missing", failures)


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
    dates = [(date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(320)]
    write_stream(data / "qqq100_recovered_reference_stream.csv", RECOVERED_REFERENCE, dates, lambda i: -0.02 if i in {85, 86} else 0.00055, reference=True)
    write_stream(data / "high_growth_return_streams.csv", HIGH_GROWTH_SLEEVE, dates, lambda i: -0.035 if i in {95, 96, 97} else 0.0012)
    write_crypto_stream(data / "crypto_return_streams.csv", dates)


def write_stream(path: Path, candidate: str, dates: list[str], fn, reference: bool = False) -> None:
    rows = []
    for index, day in enumerate(dates):
        row = {"date": day, "candidate_name": candidate, "daily_strategy_return": str(fn(index)), **false_flags_as_strings()}
        if reference:
            row["reference_status"] = "qqq100_reconstruction_close_enough_for_research_review"
        rows.append(row)
    write_csv(path, rows)


def write_crypto_stream(path: Path, dates: list[str]) -> None:
    rows = [{"date": day, "sleeve_name": CRYPTO_SLEEVE, "daily_return": str(-0.08 if i in {60, 61, 140} else 0.0015), **false_flags_as_strings()} for i, day in enumerate(dates)]
    write_csv(path, rows)


def false_flags_as_strings() -> dict[str, str]:
    return {"orders_created": "false", "orders_submitted": "false", "orders_cancelled": "false", "orders_replaced": "false", "alpaca_called": "false", "live_position_read": "false", "sqlite_trade_log_written": "false", "discord_alert_sent": "false", "telegram_alert_sent": "false", "execution_approved": "false", "paper_execution_approved": "false", "crypto_execution_approved": "false", "scheduling_approved": "false", "live_trading_approved": "false"}


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
