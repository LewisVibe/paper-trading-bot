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
MODULE = ROOT / "trading_bot" / "research" / "qqq100_manual_flatten_runbook_report.py"
README = ROOT / "README.md"
COMMAND_REFERENCE = ROOT / "docs" / "COMMAND_REFERENCE.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = ["--qqq100-manual-flatten-runbook-report", "--show-qqq100-manual-flatten-runbook-report"]
OUTPUTS = [
    "data/qqq100_manual_flatten_runbook_report.csv",
    "data/qqq100_manual_flatten_runbook_summary.csv",
    "data/qqq100_manual_flatten_runbook_blockers.csv",
    "data/qqq100_manual_flatten_runbook_evidence.csv",
]

REQUIRED_MODULE_TOKENS = [
    "manual_flatten_runbook_not_needed_currently",
    "manual_flatten_runbook_manual_review_required_not_approved",
    "manual_flatten_runbook_blocked_missing_or_contradictory_evidence",
    "manual_flatten_requires_separate_explicit_approval",
    "separate_manual_flatten_review_required_before_any_order_capable_workflow",
    "order_instructions_created",
    "manual_flatten_approved",
    "flatten_execution_approved",
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
        for path in [README, COMMAND_REFERENCE, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST]
    )

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(failures)
    verify_fixture_output(failures)

    if failures:
        print("QQQ100 manual flatten runbook report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 manual flatten runbook report verification passed.")
    print("Verified saved-output flatten runbook, current not-needed state, future flat-plus-one manual-review state, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    branches = {
        "--qqq100-manual-flatten-runbook-report": 'if sys.argv[1:] == ["--qqq100-manual-flatten-runbook-report"]:',
        "--show-qqq100-manual-flatten-runbook-report": 'if sys.argv[1:] == ["--show-qqq100-manual-flatten-runbook-report"]:',
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
        failures.append("QQQ100 manual flatten runbook module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    if "evaluate_manual_flatten_readiness" not in module_source:
        failures.append("runbook should use saved manual flatten readiness helper")
    display_start = module_source.find("def show_qqq100_manual_flatten_runbook_report")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_qqq100_manual_flatten_runbook_report" in module_source[display_start:]:
        failures.append("display command must not regenerate the report")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "QQQ100 manual flatten runbook",
        "manual_flatten_runbook_not_needed_currently",
        "manual_flatten_runbook_manual_review_required_not_approved",
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
    from trading_bot.research.qqq100_manual_flatten_runbook_report import (  # noqa: PLC0415
        generate_qqq100_manual_flatten_runbook_report,
        show_qqq100_manual_flatten_runbook_report,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture(root, desired_position="long", position_status="paper_position_long", quantity="1", alignment="aligned_long")
        result = generate_qqq100_manual_flatten_runbook_report(root)
        status_code, lines = show_qqq100_manual_flatten_runbook_report(root)
        summary_rows = read_csv_rows(result.output_paths["summary"])
        report_rows = read_csv_rows(result.output_paths["report"])

    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "manual_flatten_runbook_not_needed_currently",
        "active_strategy: qqq_100_trend_gate",
        "active_ticker: QQQ",
        "desired_state: long",
        "saved_position_quantity: 1",
        "alignment_state: aligned_long",
        "flatten_readiness_status: flatten_not_needed_currently",
        "manual_flatten_discussion_status: manual_flatten_discussion_not_needed_currently",
        "hold_no_action_and_monitor_only",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "live_trading_approved=false",
        "followup_order_approved=false",
        "repeat_execution_approved=false",
        "flatten_execution_approved=false",
        "manual_flatten_approved=false",
    ]:
        if phrase not in output:
            failures.append(f"aligned-long fixture output missing phrase: {phrase}")
    summary = {row.get("summary_name"): row.get("summary_value") for row in summary_rows}
    expected = {
        "runbook_status": "manual_flatten_runbook_not_needed_currently",
        "active_strategy": "qqq_100_trend_gate",
        "active_ticker": "QQQ",
        "desired_state": "long",
        "saved_position_state": "paper_position_long",
        "saved_position_quantity": "1",
        "alignment_state": "aligned_long",
        "flatten_readiness_status": "flatten_not_needed_currently",
        "manual_flatten_discussion_status": "manual_flatten_discussion_not_needed_currently",
        "recommended_next_step": "hold_no_action_and_monitor_only",
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"{key} expected {value}, got {summary.get(key)}")
    for row in summary_rows + report_rows:
        assert_false_flags(row, failures)

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture(root, desired_position="flat", position_status="paper_position_long", quantity="1", alignment="misaligned_should_be_flat")
        result = generate_qqq100_manual_flatten_runbook_report(root)
        summary_rows = read_csv_rows(result.output_paths["summary"])
        report_rows = read_csv_rows(result.output_paths["report"])

    summary = {row.get("summary_name"): row.get("summary_value") for row in summary_rows}
    expected_flat = {
        "runbook_status": "manual_flatten_runbook_manual_review_required_not_approved",
        "desired_state": "flat",
        "saved_position_state": "paper_position_long",
        "saved_position_quantity": "1",
        "flatten_readiness_status": "future_manual_flatten_discussion_possible_not_approved",
        "manual_flatten_discussion_status": "manual_flatten_discussion_possible_after_separate_approval",
        "primary_blocker": "manual_flatten_requires_separate_explicit_approval",
        "recommended_next_step": "separate_manual_flatten_review_required_before_any_order_capable_workflow",
    }
    for key, value in expected_flat.items():
        if summary.get(key) != value:
            failures.append(f"flat-plus-one {key} expected {value}, got {summary.get(key)}")
    for row in summary_rows + report_rows:
        assert_false_flags(row, failures)


def create_fixture(root: Path, desired_position: str, position_status: str, quantity: str, alignment: str) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(data / "qqq100_preview_signal_pack.csv", ["strategy_name", "ticker", "desired_position"], [["qqq_100_trend_gate", "QQQ", desired_position]])
    write_csv(
        data / "qqq100_paper_postcheck.csv",
        ["final_postcheck_status", "position_status", "position_quantity_abs", "alignment_state"],
        [["qqq100_postcheck_no_matching_order_found", position_status, quantity, alignment]],
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
        "flatten_execution_approved",
        "manual_flatten_approved",
    ]:
        if str(row.get(field, "")).lower() != "false":
            failures.append(f"{field} must be false in output rows")
    if "never_schedule_order_capable_commands" in row and str(row.get("never_schedule_order_capable_commands", "")).lower() != "true":
        failures.append("never_schedule_order_capable_commands must be true in report rows")


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
