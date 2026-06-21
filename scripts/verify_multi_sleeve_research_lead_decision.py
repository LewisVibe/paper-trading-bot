from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_research_lead_decision import (  # noqa: E402
    CHALLENGER_ALLOCATION,
    CURRENT_ALLOCATION,
    OUTPUT_FILES,
    STATUS_BLOCKED_MISSING,
    STATUS_SELECTED,
    generate_multi_sleeve_research_lead_decision,
    show_multi_sleeve_research_lead_decision,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_research_lead_decision.csv",
    "data/multi_sleeve_research_lead_summary.csv",
    "data/multi_sleeve_research_lead_blockers.csv",
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
    "scheduling_approved",
    "live_trading_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]
TRUE_FLAGS = ["research_only", "preview_only", "saved_output_only"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_research_lead_decision.py")
    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_saved_outputs(failures)
    if failures:
        print("Multi-sleeve research lead decision verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Multi-sleeve research lead decision verification passed.")
    print("Verified saved-output-only decision rules, blockers, display, schemas, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-research-lead-decision",
        "--show-multi-sleeve-research-lead-decision",
        "generate_multi_sleeve_research_lead_decision",
        "show_multi_sleeve_research_lead_decision",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing research lead decision token: {token}")


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
        CURRENT_ALLOCATION,
        CHALLENGER_ALLOCATION,
        STATUS_SELECTED,
        STATUS_BLOCKED_MISSING,
        "split_validation",
        "cost_stress",
        "drawdown_sensitivity",
        "crypto_volatility_context",
        "high_growth_drawdown_context",
        "saved_output_completeness",
        "execution_boundary",
        "scheduling_boundary",
        "execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"decision module missing required token: {token}")
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
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"decision module must not contain forbidden token: {token}")
    for disallowed in ["scheduled"]:
        if disallowed in module_source.lower().replace("scheduling_approved", ""):
            failures.append(f"decision module should not use disallowed wording: {disallowed}")
    allowed_approved_context = module_source.lower()
    stripped = allowed_approved_context
    for token in [
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
        "live_trading_approved",
        "shorting_approved",
        "leverage_approved",
        "margin_approved",
    ]:
        stripped = stripped.replace(token, "")
    if "approved" in stripped:
        failures.append("word approved should appear only in explicit false approval fields")
    show_slice = source_slice(module_source, "def show_multi_sleeve_research_lead_decision", "def build_decision_row")
    if "write_rows" in show_slice or "generate_multi_sleeve_research_lead_decision" in show_slice:
        failures.append("decision display must be saved-read-only and must not regenerate outputs")
    route = source_slice(bot_source, 'if sys.argv[1:] == ["--multi-sleeve-research-lead-decision"]', 'if sys.argv[1:] == ["--paper-execution-state-summary"]')
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("research lead decision route must not call execution commands")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data")
        result = generate_multi_sleeve_research_lead_decision(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")
        decision = result.decision_rows[0]
        if decision.get("research_lead_decision") != STATUS_SELECTED:
            failures.append("fixture should select higher growth as research lead candidate with manual review")
        required_cols = [
            "current_allocation",
            "challenger_allocation",
            "current_CAGR",
            "challenger_CAGR",
            "delta_CAGR",
            "split_win_count",
            "worst_split_name",
            "worst_cost_stress_name",
            "drawdown_delta_vs_current",
            "research_lead_decision",
        ]
        for column in required_cols:
            if column not in decision:
                failures.append(f"decision row missing column: {column}")
        blocker_names = {row.get("blocker_name") for row in result.blocker_rows}
        for blocker in [
            "split_validation",
            "cost_stress",
            "drawdown_sensitivity",
            "crypto_volatility_context",
            "high_growth_drawdown_context",
            "saved_output_completeness",
            "execution_boundary",
            "scheduling_boundary",
        ]:
            if blocker not in blocker_names:
                failures.append(f"missing blocker row: {blocker}")
        verify_safety_flags(result.decision_rows + result.summary_rows, "generated", failures)
        for row in result.blocker_rows:
            for flag in ["execution_approved", "crypto_execution_approved", "scheduling_approved"]:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"blocker row should keep {flag}=false")
        code, lines = show_multi_sleeve_research_lead_decision(root)
        output = "\n".join(lines)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        for token in [
            "final research lead decision",
            "current allocation metrics",
            "challenger allocation metrics",
            "delta metrics",
            "split win count and worst split",
            "worst cost stress",
            "drawdown sensitivity",
            "key blockers",
            "execution_approved=false",
            "crypto_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if token not in output:
                failures.append(f"display missing expected token: {token}")


def verify_missing_saved_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_multi_sleeve_research_lead_decision(root)
        decision = result.decision_rows[0]
        if decision.get("research_lead_decision") != STATUS_BLOCKED_MISSING:
            failures.append("missing saved outputs should block decision")
        if "saved_output_completeness" not in {row.get("blocker_name") for row in result.blocker_rows}:
            failures.append("missing saved outputs should write saved_output_completeness blocker")
        verify_safety_flags(result.decision_rows + result.summary_rows, "missing", failures)


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
    false_flags = false_flags_as_strings()
    write_csv(
        data / "multi_sleeve_higher_growth_review.csv",
        [
            {
                "allocation_name": CURRENT_ALLOCATION,
                "CAGR": "21.7328",
                "Sharpe": "1.1852",
                "MaxDD": "-22.2489",
                "Calmar": "0.9768",
                "delta_CAGR": "0",
                "delta_Sharpe": "0",
                "delta_MaxDD": "0",
                "delta_Calmar": "0",
                **false_flags,
            },
            {
                "allocation_name": CHALLENGER_ALLOCATION,
                "CAGR": "23.6634",
                "Sharpe": "1.2232",
                "MaxDD": "-22.5209",
                "Calmar": "1.0507",
                "delta_CAGR": "1.9306",
                "delta_Sharpe": "0.038",
                "delta_MaxDD": "-0.272",
                "delta_Calmar": "0.0739",
                **false_flags,
            },
        ],
    )
    write_csv(
        data / "multi_sleeve_higher_growth_summary.csv",
        [{"summary_name": "final_higher_growth_review_status", "summary_value": "higher_growth_review_promising_but_drawdown_sensitive", **false_flags}],
    )
    write_csv(
        data / "multi_sleeve_higher_growth_split_review.csv",
        [
            split_row("split_60_40", "2.6817", "0.0284", "-0.8249", "0.0478", false_flags),
            split_row("split_70_30", "2.0", "0.04", "-0.4", "0.06", false_flags),
            split_row("split_80_20", "1.5", "0.03", "-0.2", "0.04", false_flags),
        ],
    )
    write_csv(
        data / "multi_sleeve_higher_growth_cost_review.csv",
        [
            {"allocation_name": CHALLENGER_ALLOCATION, "cost_stress_name": "base_cost", "CAGR": "23.6634", "delta_CAGR_vs_current_base": "1.9306", **false_flags},
            {"allocation_name": CHALLENGER_ALLOCATION, "cost_stress_name": "plus_100bps_high_growth_turnover", "CAGR": "23.2019", "delta_CAGR_vs_current_base": "1.4691", **false_flags},
        ],
    )
    write_csv(
        data / "multi_sleeve_higher_growth_drawdown_review.csv",
        [
            {"allocation_name": CURRENT_ALLOCATION, "drawdown_delta_vs_current": "0", **false_flags},
            {"allocation_name": CHALLENGER_ALLOCATION, "drawdown_delta_vs_current": "-0.272", **false_flags},
        ],
    )
    write_csv(data / "multi_sleeve_crypto_review.csv", [{"review_name": "crypto_context", **false_flags}])


def split_row(split: str, dcagr: str, dsharpe: str, dmaxdd: str, dcalmar: str, flags: dict[str, str]) -> dict[str, str]:
    return {
        "split_name": split,
        "allocation_name": CHALLENGER_ALLOCATION,
        "delta_CAGR_higher_growth_vs_current": dcagr,
        "delta_Sharpe_higher_growth_vs_current": dsharpe,
        "delta_MaxDD_higher_growth_vs_current": dmaxdd,
        "delta_Calmar_higher_growth_vs_current": dcalmar,
        **flags,
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
        "scheduling_approved": "false",
        "live_trading_approved": "false",
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
