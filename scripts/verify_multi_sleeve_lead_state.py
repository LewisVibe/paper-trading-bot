from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_lead_state import (  # noqa: E402
    CURRENT_RESEARCH_LEAD_CANDIDATE,
    LEAD_STATE_SELECTED,
    OUTPUT_FILES,
    PREVIOUS_RESEARCH_BASELINE,
    SELECTED_DECISION,
    generate_multi_sleeve_lead_state,
    show_multi_sleeve_lead_state,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_lead_state.csv",
    "data/multi_sleeve_lead_state_summary.csv",
    "data/multi_sleeve_lead_state_blockers.csv",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_lead_state.py")
    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_decision(failures)
    verify_optional_current_state_integration(failures)
    if failures:
        print("Multi-sleeve lead state verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Multi-sleeve lead state verification passed.")
    print("Verified canonical saved-output state, display, blockers, schemas, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-lead-state-refresh",
        "--show-multi-sleeve-lead-state",
        "generate_multi_sleeve_lead_state",
        "show_multi_sleeve_lead_state",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing lead-state token: {token}")


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
        CURRENT_RESEARCH_LEAD_CANDIDATE,
        PREVIOUS_RESEARCH_BASELINE,
        SELECTED_DECISION,
        LEAD_STATE_SELECTED,
        "selected_research_lead_candidate",
        "non_executable_research_only",
        "manual_review_required",
        "drawdown_sensitivity",
        "high_growth_drawdown_context",
        "crypto_volatility_context",
        "execution_boundary",
        "crypto_execution_boundary",
        "scheduling_boundary",
        "saved_output_completeness",
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "live_trading_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"lead-state module missing required token: {token}")
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
            failures.append(f"lead-state module must not contain forbidden token: {token}")
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
    show_slice = source_slice(module_source, "def show_multi_sleeve_lead_state", "def build_state_row")
    if "write_rows" in show_slice or "generate_multi_sleeve_lead_state" in show_slice:
        failures.append("lead-state display must be saved-read-only and must not regenerate outputs")
    route = source_slice(bot_source, 'if sys.argv[1:] == ["--multi-sleeve-lead-state-refresh"]', 'if sys.argv[1:] == ["--paper-execution-state-summary"]')
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("lead-state route must not call execution commands")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data")
        result = generate_multi_sleeve_lead_state(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")
        state = result.state_rows[0]
        if state.get("lead_state_status") != LEAD_STATE_SELECTED:
            failures.append("fixture should write selected manual-review lead state")
        if state.get("current_research_lead_candidate") != CURRENT_RESEARCH_LEAD_CANDIDATE:
            failures.append("lead state should name higher_growth_70_20_5_5 as current research lead candidate")
        if state.get("previous_research_baseline") != PREVIOUS_RESEARCH_BASELINE:
            failures.append("lead state should name current_75_15_5_5 as previous baseline")
        for column in [
            "candidate_CAGR",
            "candidate_Sharpe",
            "candidate_MaxDD",
            "candidate_Calmar",
            "baseline_CAGR",
            "baseline_Sharpe",
            "baseline_MaxDD",
            "baseline_Calmar",
            "delta_CAGR",
            "delta_Sharpe",
            "delta_MaxDD",
            "delta_Calmar",
            "split_win_count",
            "worst_split_name",
            "worst_cost_stress_name",
            "drawdown_delta_vs_current",
            "manual_review_required",
            "execution_state",
        ]:
            if column not in state:
                failures.append(f"state row missing column: {column}")
        blocker_names = {row.get("blocker_name") for row in result.blocker_rows}
        for blocker in [
            "manual_review_required",
            "drawdown_sensitivity",
            "high_growth_drawdown_context",
            "crypto_volatility_context",
            "execution_boundary",
            "crypto_execution_boundary",
            "scheduling_boundary",
            "saved_output_completeness",
        ]:
            if blocker not in blocker_names:
                failures.append(f"missing blocker row: {blocker}")
        verify_safety_flags(result.state_rows + result.summary_rows, "generated", failures)
        for row in result.blocker_rows:
            for flag in ["execution_approved", "crypto_execution_approved", "scheduling_approved"]:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"blocker row should keep {flag}=false")
        code, lines = show_multi_sleeve_lead_state(root)
        output = "\n".join(lines)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        for token in [
            "current research lead candidate",
            "previous research baseline",
            "lead state status",
            "selected candidate metrics",
            "previous baseline metrics",
            "deltas",
            "split win count",
            "worst split",
            "worst cost stress",
            "drawdown sensitivity",
            "manual review required",
            "execution_approved=false",
            "crypto_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if token not in output:
                failures.append(f"display missing expected token: {token}")


def verify_missing_decision(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_multi_sleeve_lead_state(root)
        state = result.state_rows[0]
        if state.get("lead_state_status") != "lead_state_blocked_missing_saved_decision":
            failures.append("missing decision should block lead-state refresh")
        if "saved_output_completeness" not in {row.get("blocker_name") for row in result.blocker_rows}:
            failures.append("missing decision should include saved_output_completeness blocker")
        verify_safety_flags(result.state_rows + result.summary_rows, "missing", failures)


def verify_optional_current_state_integration(failures: list[str]) -> None:
    source = read_text(ROOT / "trading_bot" / "research" / "current_research_state.py")
    if "multi_sleeve_lead_state.csv" not in source:
        return
    if "generate_multi_sleeve_lead_state" in source or "write_rows" in source:
        failures.append("current research state integration must remain saved-read-only")


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
    write_csv(
        data / "multi_sleeve_research_lead_decision.csv",
        [
            {
                "current_allocation": PREVIOUS_RESEARCH_BASELINE,
                "challenger_allocation": CURRENT_RESEARCH_LEAD_CANDIDATE,
                "current_CAGR": "21.7328",
                "current_Sharpe": "1.1852",
                "current_MaxDD": "-22.2489",
                "current_Calmar": "0.9768",
                "challenger_CAGR": "23.6634",
                "challenger_Sharpe": "1.2232",
                "challenger_MaxDD": "-22.5209",
                "challenger_Calmar": "1.0507",
                "delta_CAGR": "1.9306",
                "delta_Sharpe": "0.038",
                "delta_MaxDD": "-0.272",
                "delta_Calmar": "0.0739",
                "split_win_count": "3",
                "worst_split_name": "split_60_40",
                "worst_cost_stress_name": "plus_100bps_high_growth_turnover",
                "drawdown_delta_vs_current": "-0.272",
                "research_lead_decision": SELECTED_DECISION,
                "required_next_step": "manual_review_before_multi_sleeve_research_lead_label_change",
                **flags,
            }
        ],
    )
    write_csv(
        data / "multi_sleeve_research_lead_summary.csv",
        [{"summary_name": "final_research_lead_decision", "summary_value": SELECTED_DECISION, **flags}],
    )
    write_csv(data / "multi_sleeve_research_lead_blockers.csv", [{"blocker_name": "manual_review_required", **flags}])
    write_csv(data / "multi_sleeve_crypto_review.csv", [{"review_name": "crypto_context", **flags}])


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
