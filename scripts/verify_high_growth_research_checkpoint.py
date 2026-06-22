from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.high_growth_research_checkpoint import (  # noqa: E402
    NEXT_STEP,
    OUTPUT_FILES,
    STATUS_BLOCKED,
    STATUS_INCOMPLETE_OPTIONAL,
    STATUS_MANUAL_REVIEW,
    generate_high_growth_research_checkpoint,
    show_high_growth_research_checkpoint,
)


EXPECTED_OUTPUTS = [
    "data/high_growth_research_checkpoint.csv",
    "data/high_growth_research_checkpoint_blockers.csv",
]

REQUIRED_FIELDS = [
    "final_checkpoint_status",
    "selected_lead_candidate",
    "previous_baseline",
    "selected_candidate_CAGR",
    "selected_candidate_Sharpe",
    "selected_candidate_MaxDD",
    "selected_candidate_Calmar",
    "baseline_CAGR",
    "baseline_Sharpe",
    "baseline_MaxDD",
    "baseline_Calmar",
    "delta_CAGR",
    "delta_Sharpe",
    "delta_MaxDD",
    "delta_Calmar",
    "split_win_count",
    "worst_split",
    "worst_cost_stress",
    "high_growth_sleeve_status",
    "high_growth_concentration_status",
    "high_growth_dependency_status",
    "unique_ticker_count",
    "average_active_components",
    "max_component_weight",
    "top_contributor",
    "worst_contributor",
    "drawdown_decomposition_status",
    "drawdown_delta",
    "main_incremental_drawdown_contributor",
    "high_growth_drawdown_contribution",
    "crypto_drawdown_contribution",
    "drawdown_concentration_status",
    "top_drawdown_contributor",
    "crypto_containment_status",
    "manual_review_required",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
    "required_next_step",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "high_growth_research_checkpoint.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_complete_generation(failures)
    verify_missing_core_generation(failures)
    verify_missing_optional_crypto_context(failures)

    if failures:
        print("High-growth research checkpoint verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("High-growth research checkpoint verification passed.")
    print("Verified saved-output consolidation, blocked core inputs, optional crypto context, display safety, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--high-growth-research-checkpoint",
        "--show-high-growth-research-checkpoint",
        "generate_high_growth_research_checkpoint",
        "show_high_growth_research_checkpoint",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing high-growth research checkpoint token: {token}")


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
        "high_growth_research_checkpoint_manual_review_required",
        "high_growth_research_checkpoint_blocked_missing_core_inputs",
        "high_growth_research_checkpoint_incomplete_optional_context",
        "high_growth_research_checkpoint_research_only_no_execution",
        "multi_sleeve_lead_state.csv",
        "high_growth_sleeve_concentration_review.csv",
        "multi_sleeve_crypto_containment_review.csv",
        "missing_optional_saved_output",
        NEXT_STEP,
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "live_trading_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"high-growth research checkpoint module missing required token: {token}")

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
        "execution-ready",
        "execution_ready",
        "promotion-ready",
        "promotion_ready",
        "order-ready",
        "order_ready",
        "scheduling-ready",
        "scheduling_ready",
        "crypto-execution-ready",
        "crypto_execution_ready",
        "approved_for_execution",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"high-growth research checkpoint module must not contain forbidden token: {token}")

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

    show_slice = source_slice(module_source, "def show_high_growth_research_checkpoint", "def build_checkpoint_row")
    if "write_rows" in show_slice or "generate_high_growth_research_checkpoint" in show_slice:
        failures.append("display command must be saved-read-only and must not regenerate outputs")

    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--high-growth-research-checkpoint"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("high-growth research checkpoint route must not call execution commands")


def verify_complete_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_core_fixture(root, include_crypto=True)
        result = generate_high_growth_research_checkpoint(root)
        row = result.checkpoint_rows[0]
        if row.get("final_checkpoint_status") != STATUS_MANUAL_REVIEW:
            failures.append(f"complete fixture should require manual review, got {row.get('final_checkpoint_status')}")
        for field in REQUIRED_FIELDS:
            if field not in row:
                failures.append(f"checkpoint row missing field: {field}")
        if row.get("selected_lead_candidate") != "higher_growth_70_20_5_5":
            failures.append("checkpoint should preserve selected lead candidate")
        if row.get("high_growth_concentration_status") != "high_growth_concentration_manual_review_required":
            failures.append("checkpoint should preserve high-growth concentration status")
        if row.get("crypto_containment_status") == "missing_optional_saved_output":
            failures.append("complete fixture should preserve crypto containment status")
        verify_safety_flags([row], "complete", failures)
        code, lines = show_high_growth_research_checkpoint(root)
        if code != 0:
            failures.append("display should succeed after checkpoint generation")
        display = "\n".join(lines)
        for token in ["final checkpoint status", "selected lead candidate", "high-growth concentration", "execution_approved=false"]:
            if token not in display:
                failures.append(f"display missing token: {token}")


def verify_missing_core_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_high_growth_research_checkpoint(root)
        row = result.checkpoint_rows[0]
        if row.get("final_checkpoint_status") != STATUS_BLOCKED:
            failures.append("missing core inputs should block checkpoint")
        if row.get("selected_candidate_CAGR") != "missing_saved_output":
            failures.append("missing core inputs must not create fake metrics")
        if not any(item.get("blocker_name") == "lead_state_missing" for item in result.blocker_rows):
            failures.append("missing core path should include lead_state_missing blocker")
        verify_safety_flags([row], "blocked", failures)


def verify_missing_optional_crypto_context(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_core_fixture(root, include_crypto=False)
        result = generate_high_growth_research_checkpoint(root)
        row = result.checkpoint_rows[0]
        if row.get("final_checkpoint_status") != STATUS_INCOMPLETE_OPTIONAL:
            failures.append("missing optional crypto context should be incomplete optional, not fake complete")
        if row.get("crypto_containment_status") != "missing_optional_saved_output":
            failures.append("missing optional crypto context should be labelled missing_optional_saved_output")


def verify_safety_flags(rows: list[dict[str, object]], label: str, failures: list[str]) -> None:
    for index, row in enumerate(rows):
        if str(row.get("research_only", "")).lower() != "true":
            failures.append(f"{label} row {index} should keep research_only=true")
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).lower() != "false":
                failures.append(f"{label} row {index} should keep {flag}=false")


def write_core_fixture(root: Path, include_crypto: bool) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(
        data / "multi_sleeve_lead_state.csv",
        [
            {
                "current_research_lead_candidate": "higher_growth_70_20_5_5",
                "previous_research_baseline": "current_75_15_5_5",
                "candidate_CAGR": "24.0686",
                "candidate_Sharpe": "1.2402",
                "candidate_MaxDD": "-22.5209",
                "candidate_Calmar": "1.0687",
                "baseline_CAGR": "22.0866",
                "baseline_Sharpe": "1.2009",
                "baseline_MaxDD": "-22.2489",
                "baseline_Calmar": "0.9927",
                "delta_CAGR": "1.982",
                "delta_Sharpe": "0.0393",
                "delta_MaxDD": "-0.272",
                "delta_Calmar": "0.076",
                "split_win_count": "3",
                "worst_split_name": "split_60_40",
                "worst_cost_stress_name": "plus_100bps_high_growth_turnover",
                "drawdown_delta_vs_current": "-0.272",
                **false_flags_as_strings(),
            }
        ],
    )
    write_csv(
        data / "high_growth_sleeve_concentration_review.csv",
        [
            {
                "concentration_review_status": "high_growth_concentration_manual_review_required",
                "concentration_status": "component_dependency_low_or_moderate",
                "unique_ticker_count": "39",
                "average_active_components": "2.0114",
                "max_component_weight": "1.0",
                **false_flags_as_strings(),
            }
        ],
    )
    write_summary(data / "high_growth_sleeve_concentration_summary.csv", {
        "top_contributor_summary": "SE: weighted_contribution=0.6854",
        "worst_contributor_summary": "DASH: weighted_contribution=-0.1546",
    })
    write_summary(data / "multi_sleeve_high_growth_drawdown_summary.csv", {
        "final_drawdown_decomposition_status": "high_growth_drawdown_watch_manual_review_required",
        "drawdown_delta": "-0.272",
        "main_incremental_drawdown_contributor": "extra_high_growth_weight",
        "high_growth_contribution_during_worst_period": "-5.6276",
        "crypto_contribution_during_worst_period": "-1.6298",
    })
    write_csv(
        data / "high_growth_sleeve_concentration_drawdown.csv",
        [
            {
                "drawdown_concentration_status": "drawdown_concentration_available_research_only",
                "top_drawdown_contributor": "MDB",
                "top_drawdown_contribution": "-0.1383",
                **false_flags_as_strings(),
            }
        ],
    )
    if include_crypto:
        write_csv(
            data / "multi_sleeve_crypto_containment_review.csv",
            [{"crypto_containment_status": "crypto_containment_5pct_promising_but_vol_sensitive", **false_flags_as_strings()}],
        )


def write_summary(path: Path, values: dict[str, str]) -> None:
    rows = [{"summary_name": name, "summary_value": value, **false_flags_as_strings()} for name, value in values.items()]
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
