from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_live_promotion_ladder_status.py"
README = ROOT / "README.md"
COMMAND_REFERENCE = ROOT / "docs" / "COMMAND_REFERENCE.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-promotion-ladder-status",
    "--show-paper-live-promotion-ladder-status",
]

OUTPUTS = [
    "data/paper_live_promotion_ladder_status.csv",
    "data/paper_live_promotion_ladder_status_summary.csv",
    "data/paper_live_promotion_ladder_status_blockers.csv",
    "data/paper_live_promotion_ladder_status_evidence.csv",
]

REQUIRED_MODULE_TOKENS = [
    "paper_live_promotion_ladder_status_report_only",
    "qqq100_seed_monitor_only_no_action",
    "monitor_only_aligned_long_one",
    "blocked_research_only",
    "future_review_only",
    "sma_slow_sma_not_paper_live_candidates",
    "f7_accounting_proof_accepted_portfolio_backtests_still_not_promotion_evidence",
    "missing_saved_f7_accounting_proof",
    "unknown_position_blocks_manual_review",
    "manual_review_next_ladder_candidate_scope_without_execution",
    "promotion_approved",
    "order_instructions_created",
    "qqq_100_trend_gate",
    "QQQ",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"flatten_execution_approved": False',
    '"manual_flatten_approved": False',
    '"promotion_approved": False',
    '"alpaca_called": False',
    '"live_positions_read": False',
    '"market_data_refreshed": False',
    '"yfinance_called": False',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
]

FORBIDDEN_CALL_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_all_positions(",
    "get_alpaca_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "yf.",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(
        read_text(path)
        for path in [README, COMMAND_REFERENCE, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST]
    )

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_docs(docs_source, failures)
    verify_fixture_output(failures)

    if failures:
        print("Paper-live promotion ladder status verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live promotion ladder status verification passed.")
    print("Verified report-only ladder status scaffold, QQQ100-only seed, blocked non-QQQ branches, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    branches = {
        "--paper-live-promotion-ladder-status": 'if sys.argv[1:] == ["--paper-live-promotion-ladder-status"]:',
        "--show-paper-live-promotion-ladder-status": 'if sys.argv[1:] == ["--show-paper-live-promotion-ladder-status"]:',
    }
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live promotion ladder status module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(
            ["git", "check-ignore", output],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS[:3]:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "promotion ladder status",
        "QQQ100 is the only current seed",
        "high-growth and crypto remain research-only",
        "portfolio backtests",
        "not promotion evidence",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    from trading_bot.research.paper_live_promotion_ladder_status import (  # noqa: PLC0415
        generate_paper_live_promotion_ladder_status,
        show_paper_live_promotion_ladder_status,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture(root)
        result = generate_paper_live_promotion_ladder_status(root)
        status_code, lines = show_paper_live_promotion_ladder_status(root)
        status_rows = read_csv_rows(result.output_paths["status"])
        summary_rows = read_csv_rows(result.output_paths["summary"])

    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "paper_live_promotion_ladder_status_report_only",
        "current_seed=qqq_100_trend_gate:QQQ",
        "qqq100_ladder_status=monitor_only_aligned_long_one",
        "qqq100_daily_decision_status=qqq100_daily_decision_hold_no_action_aligned_long",
        "qqq100_flatten_status=flatten_not_needed_currently",
        "qqq100_flatten_runbook_status=manual_flatten_runbook_not_needed_currently",
        "f7_accounting_status=f7_accounting_static_proof_ready_for_manual_review",
        "portfolio_backtest_evidence_status=f7_accounting_proof_accepted_portfolio_backtests_still_not_promotion_evidence",
        "blocked_branches=high_growth;crypto;defensive_sleeve;sma;slow_sma",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "live_trading_approved=false",
        "followup_order_approved=false",
        "repeat_execution_approved=false",
        "flatten_execution_approved=false",
        "manual_flatten_approved=false",
        "promotion_approved=false",
        "never_schedule_order_capable_commands=true",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")

    expected_items = {
        "qqq100_research_candidate",
        "qqq100_preview_candidate",
        "qqq100_paper_live_candidate",
        "qqq100_manually_executable_candidate",
        "high_growth_branch",
        "crypto_branch",
        "defensive_sleeve_branch",
        "sma_slow_sma_branch",
    }
    actual_items = {row.get("ladder_item") for row in status_rows}
    missing = expected_items - actual_items
    if missing:
        failures.append(f"status output missing ladder items: {sorted(missing)}")
    summary = {row.get("summary_name"): row.get("summary_value") for row in summary_rows}
    if summary.get("final_ladder_status") != "paper_live_promotion_ladder_status_report_only":
        failures.append("final_ladder_status should be report-only when fixture evidence is present")
    if summary.get("portfolio_backtest_evidence_status") != "f7_accounting_proof_accepted_portfolio_backtests_still_not_promotion_evidence":
        failures.append("portfolio_backtest_evidence_status should reflect accepted F7 proof while blocking promotion evidence")
    for row in status_rows + summary_rows:
        assert_false_flags(row, failures)


def create_fixture(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(data / "paper_live_promotion_ladder_design_summary.csv", ["summary_name", "summary_value"], [["final_design_status", "paper_live_promotion_ladder_design_report_only"]])
    write_csv(
        data / "paper_live_monitoring_status.csv",
        ["summary_name", "summary_value"],
        [
            ["active_strategy", "qqq_100_trend_gate"],
            ["active_ticker", "QQQ"],
            ["saved_position_quantity", "1"],
            ["alignment_state", "aligned_long"],
            ["recommended_next_step", "hold_no_action_and_monitor_only"],
            ["execution_approved", "False"],
        ],
    )
    write_csv(data / "qqq100_daily_decision_summary.csv", ["summary_name", "summary_value"], [["daily_decision_status", "qqq100_daily_decision_hold_no_action_aligned_long"]])
    write_csv(data / "qqq100_manual_flatten_readiness_summary.csv", ["summary_name", "summary_value"], [["flatten_readiness_status", "flatten_not_needed_currently"]])
    write_csv(data / "qqq100_manual_flatten_runbook_summary.csv", ["summary_name", "summary_value"], [["runbook_status", "manual_flatten_runbook_not_needed_currently"]])
    write_csv(data / "paper_live_f7_accounting_proof_summary.csv", ["summary_name", "summary_value"], [["final_f7_accounting_status", "f7_accounting_static_proof_ready_for_manual_review"]])


def assert_false_flags(row: dict[str, str], failures: list[str]) -> None:
    for field in [
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "live_trading_approved",
        "followup_order_approved",
        "repeat_execution_approved",
        "flatten_execution_approved",
        "manual_flatten_approved",
        "promotion_approved",
    ]:
        if field in row and str(row.get(field, "")).lower() != "false":
            failures.append(f"{field} must be false in output rows")
    if "never_schedule_order_capable_commands" in row and str(row.get("never_schedule_order_capable_commands", "")).lower() != "true":
        failures.append("never_schedule_order_capable_commands must be true in status rows")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
