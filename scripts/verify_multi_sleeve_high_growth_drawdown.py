from __future__ import annotations

import csv
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_high_growth_drawdown import (  # noqa: E402
    CURRENT_ALLOCATION,
    HIGHER_GROWTH_ALLOCATION,
    HIGH_GROWTH_SLEEVE,
    OUTPUT_FILES,
    RECOVERED_REFERENCE,
    STATUS_WATCH,
    generate_multi_sleeve_high_growth_drawdown_decomposition,
    show_multi_sleeve_high_growth_drawdown_decomposition,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_high_growth_drawdown_decomposition.csv",
    "data/multi_sleeve_high_growth_drawdown_summary.csv",
    "data/multi_sleeve_high_growth_drawdown_periods.csv",
    "data/multi_sleeve_high_growth_drawdown_blockers.csv",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_high_growth_drawdown.py")
    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_inputs(failures)
    if failures:
        print("Multi-sleeve high-growth drawdown verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Multi-sleeve high-growth drawdown verification passed.")
    print("Verified saved-stream-only drawdown, contribution, incremental risk, recovery, display, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-high-growth-drawdown-decomposition",
        "--show-multi-sleeve-high-growth-drawdown-decomposition",
        "generate_multi_sleeve_high_growth_drawdown_decomposition",
        "show_multi_sleeve_high_growth_drawdown_decomposition",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing high-growth drawdown token: {token}")


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
        HIGHER_GROWTH_ALLOCATION[0],
        CURRENT_ALLOCATION[0],
        HIGH_GROWTH_SLEEVE,
        RECOVERED_REFERENCE,
        "high_growth_drawdown_watch_manual_review_required",
        "high_growth_drawdown_acceptable_for_research_lead",
        "high_growth_drawdown_too_sensitive_keep_as_challenger",
        "incremental_high_growth_contribution",
        "reduced_qqq100_contribution",
        "net_incremental_drawdown_effect",
        "main_incremental_drawdown_contributor",
        "post_trough_63d_return",
        "post_trough_126d_return",
        "bounce_back_status",
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "live_trading_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"drawdown module missing required token: {token}")
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
            failures.append(f"drawdown module must not contain forbidden token: {token}")
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
    show_slice = source_slice(module_source, "def show_multi_sleeve_high_growth_drawdown_decomposition", "def missing_inputs")
    if "write_rows" in show_slice or "generate_multi_sleeve_high_growth_drawdown_decomposition" in show_slice:
        failures.append("drawdown display must be saved-read-only and must not regenerate outputs")
    route = source_slice(bot_source, 'if sys.argv[1:] == ["--multi-sleeve-high-growth-drawdown-decomposition"]', 'if sys.argv[1:] == ["--paper-execution-state-summary"]')
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("drawdown route must not call execution commands")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data")
        result = generate_multi_sleeve_high_growth_drawdown_decomposition(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_drawdown_decomposition_status") != STATUS_WATCH:
            failures.append("fixture should produce manual-review watch status")
        if summary.get("selected_lead_candidate") != HIGHER_GROWTH_ALLOCATION[0]:
            failures.append("selected lead candidate should be higher_growth_70_20_5_5")
        if summary.get("previous_baseline") != CURRENT_ALLOCATION[0]:
            failures.append("previous baseline should be current_75_15_5_5")
        if not result.period_rows:
            failures.append("period rows should exist")
        if not any(row.get("row_type") == "incremental_high_growth_risk" for row in result.decomposition_rows):
            failures.append("incremental high-growth risk row should exist")
        for column in [
            "qqq100_weighted_contribution",
            "high_growth_weighted_contribution",
            "crypto_weighted_contribution",
            "incremental_high_growth_contribution",
            "reduced_qqq100_contribution",
            "net_incremental_drawdown_effect",
            "main_incremental_drawdown_contributor",
        ]:
            if column not in result.decomposition_rows[-1]:
                failures.append(f"decomposition row missing column: {column}")
        for column in ["recovery_rows", "post_trough_63d_return", "post_trough_126d_return", "bounce_back_status"]:
            if column not in result.period_rows[0]:
                failures.append(f"period row missing recovery column: {column}")
        blocker_names = {row.get("blocker_name") for row in result.blocker_rows}
        for blocker in [
            "manual_review_required",
            "drawdown_sensitivity",
            "high_growth_incremental_risk",
            "recovery_bounce_back",
            "execution_boundary",
            "crypto_execution_boundary",
            "scheduling_boundary",
        ]:
            if blocker not in blocker_names:
                failures.append(f"missing blocker row: {blocker}")
        verify_safety_flags(result.decomposition_rows + result.period_rows + result.summary_rows, "generated", failures)
        for row in result.blocker_rows:
            for flag in ["execution_approved", "crypto_execution_approved", "scheduling_approved"]:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"blocker row should keep {flag}=false")
        code, lines = show_multi_sleeve_high_growth_drawdown_decomposition(root)
        output = "\n".join(lines)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        for token in [
            "final drawdown decomposition status",
            "selected lead candidate",
            "previous baseline",
            "candidate worst drawdown period",
            "baseline worst drawdown period",
            "drawdown delta",
            "main incremental drawdown contributor",
            "high-growth contribution during worst period",
            "QQQ100 contribution change",
            "crypto contribution during worst period",
            "recovery/bounce-back summary",
            "execution_approved=false",
            "crypto_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if token not in output:
                failures.append(f"display missing expected token: {token}")


def verify_missing_inputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_multi_sleeve_high_growth_drawdown_decomposition(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_drawdown_decomposition_status") != "high_growth_drawdown_decomposition_blocked_missing_saved_streams":
            failures.append("missing inputs should block drawdown decomposition")
        if "saved_output_completeness" not in {row.get("blocker_name") for row in result.blocker_rows}:
            failures.append("missing inputs should include saved_output_completeness blocker")
        verify_safety_flags(result.decomposition_rows + result.period_rows + result.summary_rows, "missing", failures)


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
    write_csv(data / "multi_sleeve_lead_state.csv", [{"current_research_lead_candidate": HIGHER_GROWTH_ALLOCATION[0], **flags}])
    write_csv(data / "multi_sleeve_research_lead_decision.csv", [{"research_lead_decision": "higher_growth_selected_as_research_lead_candidate_manual_review_required", **flags}])
    dates = [(date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(220)]
    write_stream(
        data / "qqq100_recovered_reference_stream.csv",
        RECOVERED_REFERENCE,
        dates,
        lambda i: -0.025 if 45 <= i <= 50 else 0.001,
        reference=True,
    )
    write_stream(data / "high_growth_return_streams.csv", HIGH_GROWTH_SLEEVE, dates, lambda i: -0.04 if 45 <= i <= 50 else 0.0018)
    write_crypto_stream(data / "crypto_return_streams.csv", dates, flags)


def write_stream(path: Path, candidate: str, dates: list[str], fn, reference: bool = False) -> None:
    rows = []
    for index, day in enumerate(dates):
        row = {"date": day, "candidate_name": candidate, "daily_strategy_return": str(fn(index)), **false_flags_as_strings()}
        if reference:
            row["reference_status"] = "qqq100_reconstruction_close_enough_for_research_review"
        rows.append(row)
    write_csv(path, rows)


def write_crypto_stream(path: Path, dates: list[str], flags: dict[str, str]) -> None:
    rows = [{"date": day, "sleeve_name": "crypto_btc_eth_research_sleeve", "daily_return": str(-0.03 if 45 <= index <= 50 else 0.0012), **flags} for index, day in enumerate(dates)]
    write_csv(path, rows)


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
