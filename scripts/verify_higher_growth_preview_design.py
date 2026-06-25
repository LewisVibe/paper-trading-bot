from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.higher_growth_preview_design import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    SELECTED_CANDIDATE,
    generate_higher_growth_preview_design,
    show_higher_growth_preview_design,
)


EXPECTED_OUTPUTS = [
    "data/higher_growth_preview_design.csv",
    "data/higher_growth_preview_design_summary.csv",
    "data/higher_growth_preview_design_evidence.csv",
    "data/higher_growth_preview_design_blockers.csv",
]

COMMANDS = ["--higher-growth-preview-design", "--show-higher-growth-preview-design"]

FALSE_FLAGS = [
    "preview_signal_created",
    "action_preview_created",
    "order_instructions_created",
    "market_data_refreshed",
    "yfinance_called",
    "alpaca_called",
    "live_positions_read",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "portfolio_execution_wired",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "preview_candidate_approved",
    "preview_implementation_approved",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "high_growth_promotion_approved",
    "crypto_execution_approved",
]

TRUE_FLAGS = ["research_only", "report_only", "saved_output_only", "preview_design_only", "never_schedule_order_capable_commands"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "higher_growth_preview_design.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_fixture_generation(failures)

    if failures:
        print("Higher-growth preview design verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Higher-growth preview design verification passed.")
    print("Verified saved-output design-only scope, target weights, no preview signal/orders, false approvals, and no broker/config/scheduling paths.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    if load_config_index < 0:
        failures.append("bot.py missing expected load_config marker")
        load_config_index = len(bot_source)
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"bot.py missing command: {command}")
        early_index = bot_source.find(f'sys.argv[1:] == ["{command}"]')
        if early_index < 0:
            failures.append(f"bot.py missing early report-only route for {command}")
        elif early_index > load_config_index:
            failures.append(f"early report-only route for {command} appears after config loading")
    for token in ["generate_higher_growth_preview_design", "show_higher_growth_preview_design"]:
        if token not in bot_source:
            failures.append(f"bot.py missing function token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        result = subprocess.run(["git", "check-ignore", expected], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"generated output is not ignored by git: {expected}")


def verify_source_boundaries(module_source: str, failures: list[str]) -> None:
    required = [
        SELECTED_CANDIDATE,
        FINAL_STATUS,
        "70% qqq100_core_trend_sleeve; 20% high_growth_stock_research_sleeve; 5% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve",
        "no ticker-level order side/quantity/type fields",
        "broker_fee_cost_boundary",
        "preview_signal_created",
        "action_preview_created",
        "order_instructions_created",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")

    for flag in FALSE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not False:
            failures.append(f"safety flag must be false: {flag}")
    for flag in TRUE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not True:
            failures.append(f"safety flag must be true: {flag}")

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
        "load_config(",
        "config.json",
        "Register-ScheduledTask",
        "schtasks /create",
        "crontab",
        "systemctl",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"module must not contain forbidden token: {token}")

    show_body = source_slice(module_source, "def show_higher_growth_preview_design", "def build_design_rows")
    if "write_rows" in show_body or "generate_higher_growth_preview_design" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "higher_growth_candidate_selection_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "final_selection_status", "summary_value": "higher_growth_candidate_selected_for_preview_design_review"},
                {"summary_name": "selected_candidate", "summary_value": SELECTED_CANDIDATE},
                {"summary_name": "worst_cost_stress_result", "summary_value": "plus_100bps_high_growth_turnover_still_promising"},
            ],
        )
        write_csv(data / "higher_growth_candidate_selection_decision.csv", ["candidate_name", "selection_status"], [{"candidate_name": SELECTED_CANDIDATE, "selection_status": "selected_manual_review_required"}])
        write_csv(data / "higher_growth_preview_readiness_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "final_readiness_status", "summary_value": "higher_growth_preview_discussion_ready_manual_review_required"}])
        write_csv(data / "multi_sleeve_higher_growth_review.csv", ["allocation_name", "CAGR", "Sharpe", "MaxDD", "Calmar"], [{"allocation_name": SELECTED_CANDIDATE, "CAGR": "23.6634", "Sharpe": "1.2232", "MaxDD": "-22.5209", "Calmar": "1.0507"}])
        write_csv(data / "multi_sleeve_portfolio_backtest.csv", ["portfolio_name", "candidate_cagr", "candidate_sharpe", "candidate_max_drawdown", "candidate_calmar"], [{"portfolio_name": "qqq100_only_reference", "candidate_cagr": "16.9832", "candidate_sharpe": "1.0073", "candidate_max_drawdown": "-23.4576", "candidate_calmar": "0.724"}])

        result = generate_higher_growth_preview_design(root)
        status = summary_value(result.summary_rows, "final_design_status")
        if status != FINAL_STATUS:
            failures.append(f"fixture should produce design-ready status, got {status}")
        text = "\n".join(str(row) for row in result.design_rows + result.summary_rows + result.blocker_rows)
        for token in [SELECTED_CANDIDATE, "70% qqq100_core_trend_sleeve", "preview_signal_not_implemented", "order_instructions_not_allowed"]:
            if token not in text:
                failures.append(f"fixture output missing token: {token}")
        for collection in [result.design_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
            for row in collection:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return
        code, lines = show_higher_growth_preview_design(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [FINAL_STATUS, SELECTED_CANDIDATE, "preview_signal_created=false", "execution_approved=false"]:
            if token not in display:
                failures.append(f"display output missing token: {token}")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index < 0:
        return ""
    end_index = source.find(end, start_index + len(start))
    return source[start_index:] if end_index < 0 else source[start_index:end_index]


def summary_value(rows: list[dict[str, object]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
