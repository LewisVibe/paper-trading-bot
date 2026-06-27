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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_promotion_ladder_design.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-promotion-ladder-design",
    "--show-paper-live-promotion-ladder-design",
]

OUTPUTS = [
    "data/paper_live_promotion_ladder_design.csv",
    "data/paper_live_promotion_ladder_design_summary.csv",
    "data/paper_live_promotion_ladder_design_blockers.csv",
    "data/paper_live_promotion_ladder_design_evidence.csv",
]

REQUIRED_STAGES = [
    "research_candidate",
    "preview_candidate",
    "paper_live_candidate",
    "manually_executable_candidate",
]

REQUIRED_REPORT_COLUMNS = [
    "ladder_stage",
    "current_allowed_scope",
    "required_evidence",
    "current_status",
    "blocker",
    "future_action_required",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "never_schedule_order_capable_commands",
]

REQUIRED_MODULE_TOKENS = [
    "qqq_100_trend_gate",
    "QQQ",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
    "MULTI_SLEEVE",
    "research_candidate",
    "preview_candidate",
    "paper_live_candidate",
    "manually_executable_candidate",
    "previous_seed_monitor_only_aligned_long_one_no_action_required",
    "flatten_not_needed_currently_and_not_approved",
    "manual_flatten_runbook_not_needed_currently",
    "manual_flatten_not_approved",
    "repeat_followup_flatten_order_not_approved",
    "current_report_status_seed_not_execution",
    "research_only_not_promoted",
    "future_review_only",
    "not_paper_live_promotion_candidates",
    "blocked_until_accounting_consistency_proven",
    "unknown_position_blocks_manual_review",
    "portfolio_backtests_not_promotion_evidence",
    "scheduled_execution_forbidden",
    "observe_enabled_status_cron_then_review_non_executable_action_preview_design",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"never_schedule_order_capable_commands": True',
]

FORBIDDEN_CALL_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_all_positions(",
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
        for path in [README, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST]
    )

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_docs(docs_source, failures)
    verify_report_output_from_fixture(failures)

    if failures:
        print("Paper-live promotion ladder design verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live promotion ladder design verification passed.")
    print("Verified report-only ladder design, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-promotion-ladder-design": 'if sys.argv[1:] == ["--paper-live-promotion-ladder-design"]:',
        "--show-paper-live-promotion-ladder-design": 'if sys.argv[1:] == ["--show-paper-live-promotion-ladder-design"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live promotion ladder design module is missing")
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
        "generic promotion ladder",
        "volatility-targeted multi-sleeve candidate is the current report/status seed",
        "QQQ100 remains previous-seed context",
        "portfolio backtests",
        "not promotion evidence",
        "No scheduled execution",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_report_output_from_fixture(failures: list[str]) -> None:
    from trading_bot.research.paper_live_promotion_ladder_design import (  # noqa: PLC0415
        generate_paper_live_promotion_ladder_design,
        show_paper_live_promotion_ladder_design,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = generate_paper_live_promotion_ladder_design(root)
        status_code, lines = show_paper_live_promotion_ladder_design(root)
        report_rows = read_csv_rows(result.output_paths["report"])
        summary_rows = read_csv_rows(result.output_paths["summary"])

    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "paper_live_promotion_ladder_design_report_only",
        "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x:MULTI_SLEEVE",
        "qqq_100_trend_gate:QQQ",
        "previous_seed_monitor_only_aligned_long_one_no_action_required",
        "flatten_not_needed_currently_and_not_approved",
        "manual_flatten_runbook_not_needed_currently",
        "current_report_status_seed_not_execution",
        "blocked_until_accounting_consistency_proven",
        "unknown_position_blocks_manual_review",
        "observe_enabled_status_cron_then_review_non_executable_action_preview_design",
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

    stages = {row.get("ladder_stage") for row in report_rows}
    for stage in REQUIRED_STAGES:
        if stage not in stages:
            failures.append(f"report missing ladder stage: {stage}")
    for column in REQUIRED_REPORT_COLUMNS:
        if report_rows and column not in report_rows[0]:
            failures.append(f"report missing required column: {column}")
    for row in report_rows + summary_rows:
        assert_false_flags(row, failures)
    if any("high_growth" in row.get("current_allowed_scope", "").lower() and "excluded" not in row.get("current_allowed_scope", "").lower() for row in report_rows):
        failures.append("high-growth branch must remain excluded/research-only in ladder design")


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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
