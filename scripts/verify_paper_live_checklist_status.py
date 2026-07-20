from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_ONLY = ROOT / "trading_bot" / "cli" / "report_only.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_live_checklist_status.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = ["--paper-live-checklist-status", "--show-paper-live-checklist-status"]
OUTPUTS = [
    "data/paper_live_checklist_status.csv",
    "data/paper_live_checklist_status_summary.csv",
    "data/paper_live_checklist_status_blockers.csv",
    "data/paper_live_checklist_status_evidence.csv",
]

REQUIRED_MODULE_TOKENS = [
    "active_strategy",
    "active_ticker",
    "saved_position_state",
    "saved_position_quantity",
    "alignment_state",
    "followup_policy_status",
    "no_action_required",
    "defensive_sleeve_manual_review_status",
    "defensive_sleeve_preview_readiness_status",
    "defensive_sleeve_preview_candidate_status",
    "defensive_preview_candidate_not_approved",
    "paper_live_monitoring_status",
    "checklist_phase_status",
    "paper_ticket_present",
    "paper_ticket_id",
    "paper_ticket_execution_ready",
    "paper_ticket_blockers",
    "paper_execution_status",
    "paper_postcheck_status",
    "paper_cycle_complete",
    "next_safe_development_step",
    "paper_live_checklist_code_complete_market_hours_confirmation_pending",
    "paper_live_checklist_complete_user_hermes_setup_pending",
    "complete_filled_and_postcheck_aligned",
    "vol_targeted_paper_cycle_filled_postcheck_aligned",
    "configure_user_owned_hermes_status_cron_and_monitor_only",
    "pending_market_hours_and_final_user_confirmation",
    "boundary_complete_user_hermes_setup_pending",
    "prepare_fresh_market_hours_ticket_then_request_final_user_confirmation",
    "qqq_100_trend_gate",
    "QQQ",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
    "MULTI_SLEEVE",
    "paper_position_long",
    "aligned_long",
    "no_action_required_already_aligned",
    "hold_no_action_and_monitor_only",
    "never_schedule_order_capable_commands",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
    '"alpaca_called": False',
    '"live_positions_read": False',
]

FORBIDDEN_CALL_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_alpaca_positions(",
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
    report_only_source = read_text(REPORT_ONLY)
    module_source = read_text(MODULE)
    docs_source = "\n".join(
        read_text(path)
        for path in [README, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST]
    )

    verify_commands(report_only_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_docs(docs_source, failures)
    verify_report_output_from_fixture(failures)

    if failures:
        print("Paper-live checklist status verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live checklist status verification passed.")
    print("Verified saved-output closeout status, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(report_only_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in report_only_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-checklist-status": 'if argv == ["--paper-live-checklist-status"]:',
        "--show-paper-live-checklist-status": 'if argv == ["--show-paper-live-checklist-status"]:',
    }
    for command, branch in branches.items():
        if branch not in report_only_source:
            failures.append(f"missing early report-only route for {command}")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live checklist status module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    if "PAPER_LIVE_MONITORING_SUMMARY" not in module_source:
        failures.append("checklist closeout should read the saved paper-live monitoring summary")
    if "VOL_TARGETED_PAPER_TICKET_SUMMARY" not in module_source:
        failures.append("checklist closeout should read the latest saved volatility paper ticket summary")
    if "VOL_TARGETED_PAPER_EXECUTION_SUMMARY" not in module_source:
        failures.append("checklist closeout should read the saved volatility paper execution summary")
    if "VOL_TARGETED_PAPER_POSTCHECK_SUMMARY" not in module_source:
        failures.append("checklist closeout should read the saved volatility paper postcheck summary")


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
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "paper-live checklist status",
        "paper_live_checklist_code_complete_market_hours_confirmation_pending",
        "paper_live_checklist_complete_user_hermes_setup_pending",
        "Step 12",
        "Hermes",
        "does not approve execution",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_report_output_from_fixture(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.paper_live_checklist_status import (  # noqa: PLC0415
        generate_paper_live_checklist_status,
        show_paper_live_checklist_status,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        data_dir.mkdir()
        write_monitoring_fixture(data_dir / "paper_live_monitoring_status.csv")
        write_defensive_manual_fixture(data_dir / "paper_live_defensive_sleeve_manual_review_summary.csv")
        write_defensive_preview_fixture(data_dir / "paper_live_defensive_sleeve_preview_readiness_summary.csv")
        write_ticket_fixture(data_dir / "vol_targeted_growth_paper_ticket_summary.csv")
        result = generate_paper_live_checklist_status(root)
        status_code, lines = show_paper_live_checklist_status(root)

    output = "\n".join(result.summary_lines + lines)
    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    for phrase in [
        "paper_live_checklist_code_complete_market_hours_confirmation_pending",
        "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
        "MULTI_SLEEVE",
        "qqq_100_trend_gate",
        "QQQ",
        "paper_position_long",
        "aligned_long",
        "no_action_required_already_aligned",
        "hold_no_action_and_monitor_only",
        "defensive_sleeve_manual_review_required",
        "defensive_sleeve_preview_candidate_not_approved_manual_review_required",
        "defensive_preview_candidate_not_approved",
        "paper_ticket_present: True",
        "paper_ticket_id: vtg-fixture",
        "paper_ticket_execution_ready: False",
        "Alpaca paper market is closed",
        "prepare_fresh_market_hours_ticket_then_request_final_user_confirmation",
        "pending_market_hours_and_final_user_confirmation",
        "boundary_complete_user_hermes_setup_pending",
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

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        data_dir.mkdir()
        write_monitoring_fixture(data_dir / "paper_live_monitoring_status.csv")
        write_defensive_manual_fixture(data_dir / "paper_live_defensive_sleeve_manual_review_summary.csv")
        write_defensive_preview_fixture(data_dir / "paper_live_defensive_sleeve_preview_readiness_summary.csv")
        write_ticket_fixture(data_dir / "vol_targeted_growth_paper_ticket_summary.csv", execution_ready=True)
        write_execution_fixture(data_dir / "vol_targeted_growth_paper_execution_summary.csv")
        write_postcheck_fixture(data_dir / "vol_targeted_growth_paper_postcheck_summary.csv")
        completed_result = generate_paper_live_checklist_status(root)
        completed_status_code, completed_lines = show_paper_live_checklist_status(root)

    completed_output = "\n".join(completed_result.summary_lines + completed_lines)
    if completed_status_code != 0:
        failures.append("completed saved display should return 0 after report generation")
    for phrase in [
        "paper_live_checklist_complete_user_hermes_setup_pending",
        "vol_targeted_paper_cycle_filled_postcheck_aligned",
        "complete_filled_and_postcheck_aligned",
        "paper_execution_status: filled",
        "paper_postcheck_status: aligned",
        "paper_cycle_complete: True",
        "configure_user_owned_hermes_status_cron_and_monitor_only",
    ]:
        if phrase not in completed_output:
            failures.append(f"completed fixture output missing phrase: {phrase}")


def write_monitoring_fixture(path: Path) -> None:
    path.write_text(
        "summary_name,summary_value,details,execution_approved,paper_execution_approved,scheduling_approved,live_trading_approved,followup_order_approved,repeat_execution_approved\n"
        "active_strategy,higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x,Active paper-live monitoring seed strategy.,False,False,False,False,False,False\n"
        "active_ticker,MULTI_SLEEVE,Active paper-live monitoring seed group.,False,False,False,False,False,False\n"
        "previous_seed_strategy,qqq_100_trend_gate,Previous paper-live seed.,False,False,False,False,False,False\n"
        "previous_seed_ticker,QQQ,Previous paper-live seed ticker.,False,False,False,False,False,False\n"
        "saved_position_state,paper_position_long,Saved QQQ paper position state.,False,False,False,False,False,False\n"
        "saved_position_quantity,1,Saved QQQ paper position quantity.,False,False,False,False,False,False\n"
        "alignment_state,aligned_long,Saved QQQ alignment state.,False,False,False,False,False,False\n"
        "followup_policy_status,no_action_required_already_aligned,Saved policy.,False,False,False,False,False,False\n"
        "no_action_required,True,No paper action is needed.,False,False,False,False,False,False\n"
        "recommended_next_step,hold_no_action_and_monitor_only,Monitor only.,False,False,False,False,False,False\n",
        encoding="utf-8",
    )


def write_defensive_manual_fixture(path: Path) -> None:
    path.write_text(
        "summary_name,summary_value,details,execution_approved,paper_execution_approved,scheduling_approved,live_trading_approved,followup_order_approved,repeat_execution_approved,promotion_approved,preview_candidate_approved,defensive_sleeve_promoted\n"
        "final_manual_review_status,defensive_sleeve_manual_review_required,Manual review required,False,False,False,False,False,False,False,False,False\n",
        encoding="utf-8",
    )


def write_defensive_preview_fixture(path: Path) -> None:
    path.write_text(
        "summary_name,summary_value,details,execution_approved,paper_execution_approved,scheduling_approved,live_trading_approved,followup_order_approved,repeat_execution_approved,promotion_approved,preview_candidate_approved,defensive_sleeve_promoted\n"
        "final_preview_readiness_status,defensive_sleeve_preview_candidate_not_approved_manual_review_required,Preview not approved,False,False,False,False,False,False,False,False,False\n"
        "preview_candidate_status,defensive_preview_candidate_not_approved,Not approved,False,False,False,False,False,False,False,False,False\n",
        encoding="utf-8",
    )


def write_ticket_fixture(path: Path, *, execution_ready: bool = False) -> None:
    blockers = "none" if execution_ready else "Alpaca paper market is closed"
    path.write_text(
        "summary_name,summary_value,details\n"
        "ticket_id,vtg-fixture,Exact saved ticket ID\n"
        f"execution_ready,{execution_ready},Ticket readiness\n"
        f"blockers,{blockers},Current ticket blocker\n",
        encoding="utf-8",
    )


def write_execution_fixture(path: Path) -> None:
    path.write_text(
        "summary_name,summary_value,details\n"
        "ticket_id,vtg-fixture,Exact saved ticket ID\n"
        "execution_status,filled,All submitted orders filled\n"
        "submitted_order_count,4,Submitted order count\n"
        "filled_order_count,4,Filled order count\n",
        encoding="utf-8",
    )


def write_postcheck_fixture(path: Path) -> None:
    path.write_text(
        "summary_name,summary_value,details\n"
        "ticket_id,vtg-fixture,Exact saved ticket ID\n"
        "postcheck_status,aligned,All symbols aligned\n"
        "aligned_symbol_count,4,Aligned symbol count\n"
        "symbol_count,4,Managed symbol count\n",
        encoding="utf-8",
    )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
