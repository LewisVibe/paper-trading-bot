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
MODULE = ROOT / "trading_bot" / "research" / "qqq100_daily_decision_report.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = ["--qqq100-daily-decision-report", "--show-qqq100-daily-decision-report"]
OUTPUTS = [
    "data/qqq100_daily_decision_report.csv",
    "data/qqq100_daily_decision_summary.csv",
    "data/qqq100_daily_decision_blockers.csv",
    "data/qqq100_daily_decision_evidence.csv",
]

REQUIRED_MODULE_TOKENS = [
    "qqq100_daily_decision_hold_no_action_aligned_long",
    "qqq100_daily_decision_hold_no_action_aligned_flat",
    "qqq100_daily_decision_manual_buy_discussion_possible_not_approved",
    "qqq100_daily_decision_manual_flatten_discussion_possible_not_approved",
    "qqq100_daily_decision_blocked_manual_review_required",
    "hold_no_action_and_monitor_only",
    "manual_buy_not_approved_by_daily_decision",
    "manual_flatten_not_approved_by_daily_decision",
    "order_instructions_created",
    "qqq_100_trend_gate",
    "QQQ",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
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
    "submit_alpaca_order(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_alpaca_positions(",
    "get_all_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "download_daily_price_data(",
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
        for path in [README, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST]
    )

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(failures)
    verify_fixture_output(failures)

    if failures:
        print("QQQ100 daily decision report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 daily decision report verification passed.")
    print("Verified saved-output daily decision, no-action aligned-long state, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    branches = {
        "--qqq100-daily-decision-report": 'if sys.argv[1:] == ["--qqq100-daily-decision-report"]:',
        "--show-qqq100-daily-decision-report": 'if sys.argv[1:] == ["--show-qqq100-daily-decision-report"]:',
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
        failures.append("QQQ100 daily decision module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    if "evaluate_paper_live_saved_evidence" not in module_source:
        failures.append("daily decision should use saved paper-live evidence helper")
    if "evaluate_followup_policy" not in module_source:
        failures.append("daily decision should use saved follow-up policy helper")
    display_start = module_source.find("def show_qqq100_daily_decision_report")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_qqq100_daily_decision_report" in module_source[display_start:]:
        failures.append("display command must not regenerate the report")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "QQQ100 daily decision",
        "qqq100_daily_decision_hold_no_action_aligned_long",
        "hold_no_action_and_monitor_only",
        "does not approve execution",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


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


def verify_fixture_output(failures: list[str]) -> None:
    from trading_bot.research.qqq100_daily_decision_report import (  # noqa: PLC0415
        generate_qqq100_daily_decision_report,
        show_qqq100_daily_decision_report,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_aligned_long_fixture(root)
        result = generate_qqq100_daily_decision_report(root)
        status_code, lines = show_qqq100_daily_decision_report(root)
        summary_rows = read_csv_rows(result.output_paths["summary"])
        report_rows = read_csv_rows(result.output_paths["report"])

    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "qqq100_daily_decision_hold_no_action_aligned_long",
        "active_strategy: qqq_100_trend_gate",
        "active_ticker: QQQ",
        "saved_position_quantity: 1",
        "alignment_state: aligned_long",
        "followup_policy_status: no_action_required_already_aligned",
        "no_action_required: True",
        "hold_no_action_and_monitor_only",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "live_trading_approved=false",
        "followup_order_approved=false",
        "repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")
    summary = {row.get("summary_name"): row.get("summary_value") for row in summary_rows}
    expected = {
        "daily_decision_status": "qqq100_daily_decision_hold_no_action_aligned_long",
        "active_strategy": "qqq_100_trend_gate",
        "active_ticker": "QQQ",
        "desired_state": "long",
        "saved_position_state": "paper_position_long",
        "saved_position_quantity": "1",
        "alignment_state": "aligned_long",
        "followup_policy_status": "no_action_required_already_aligned",
        "no_action_required": "True",
        "recommended_next_step": "hold_no_action_and_monitor_only",
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"{key} expected {value}, got {summary.get(key)}")
    for row in summary_rows + report_rows:
        assert_false_flags(row, failures)


def create_aligned_long_fixture(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(data / "qqq100_preview_signal_pack.csv", ["strategy_name", "ticker", "desired_position"], [["qqq_100_trend_gate", "QQQ", "long"]])
    write_csv(
        data / "qqq100_paper_postcheck.csv",
        ["final_postcheck_status", "position_status", "position_quantity_abs", "alignment_state"],
        [["qqq100_postcheck_no_matching_order_found", "paper_position_long", "1", "aligned_long"]],
    )
    write_csv(data / "qqq100_paper_execution_result.csv", ["order_status", "strategy_name", "ticker"], [["filled", "qqq_100_trend_gate", "QQQ"]])
    write_csv(data / "qqq100_paper_execution_summary.csv", ["summary_name", "summary_value"], [["order_status", "filled"]])


def assert_false_flags(row: dict[str, str], failures: list[str]) -> None:
    for field in [
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "live_trading_approved",
        "followup_order_approved",
        "repeat_execution_approved",
    ]:
        if str(row.get(field, "")).lower() != "false":
            failures.append(f"{field} must be false in output rows")
    if "never_schedule_order_capable_commands" in row and str(row.get("never_schedule_order_capable_commands", "")).lower() != "true":
        failures.append("never_schedule_order_capable_commands must be true in report rows")


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
