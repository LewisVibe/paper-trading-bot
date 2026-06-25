from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT_PATH = ROOT / "bot.py"
MODULE_PATH = ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py"
COMMAND = "--vps-daily-monitoring-summary"

REQUIRED_OUTPUT_PHRASES = [
    "VPS DAILY MONITORING SUMMARY. REPORT ONLY. NOT EXECUTION.",
    "execution_approved=False",
    "scheduling_approved=False",
    "Safety reminders:",
    "Lock-wrapped safe commands:",
    "Promoted review summary:",
    "Defensive refresh summary:",
    "Paper-live monitoring status:",
    "QQQ100 daily decision:",
    "qqq100_daily_decision_present: True",
    "daily_decision_status: qqq100_daily_decision_hold_no_action_aligned_long",
    "manual_discussion_status: manual_trade_discussion_not_needed",
    "active_strategy: qqq_100_trend_gate",
    "active_ticker: QQQ",
    "alignment_state: aligned_long",
    "followup_policy_status: no_action_required_already_aligned",
    "recommended_next_step: hold_no_action_and_monitor_only",
    "followup_order_approved: False",
    "repeat_execution_approved: False",
    "never_schedule_order_capable_commands: True",
    "Saved-output freshness:",
    "final_status:",
    "action_required:",
    "action_reason:",
    "suggested_manual_action:",
]

REQUIRED_FINAL_STATES = [
    "healthy_monitoring_state",
    "monitoring_warning",
    "monitoring_stale_or_missing_inputs",
]

REQUIRED_ACTION_STATES = [
    "no_action_required",
    "refresh_stale_safe_reports",
    "manual_review_required",
    "all_status_inputs_fresh_or_acceptable",
    "one_or_more_saved_report_inputs_warning_stale",
    "one_or_more_saved_report_inputs_stale_or_missing",
    "manually_run_safe_refresh_reports",
    "refresh_or_investigate_saved_monitoring_inputs",
    "paper_live_monitoring_saved_status_missing_or_inconsistent",
    "refresh_report_only_paper_live_monitoring_status",
    "qqq100_daily_decision_saved_status_missing",
    "refresh_report_only_qqq100_daily_decision",
    "qqq100_daily_decision_approval_flags_need_review",
]

FORBIDDEN_CALLS = [
    "TradingClient(",
    "get_alpaca_positions(",
    "submit_order(",
    "cancel_order(",
    "create_order(",
    "send_discord_alert(",
    "sqlite3.connect(",
    "insert_trade_log(",
    "yf.download(",
    "download_close_prices(",
    "download_backtest_prices(",
    "load_config(",
    "open(\"config.json\"",
    "read_text(\"config.json\"",
]


def main() -> int:
    failures: list[str] = []
    verify_command_registered(failures)
    verify_module_source(failures)
    verify_command_output(failures)

    if failures:
        print("VPS daily monitoring summary verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("VPS daily monitoring summary verification passed.")
    print("Verified command registration, report-only output, false approval flags, compact saved-output summaries, and no forbidden calls.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    bot_source = read_text(BOT_PATH)
    if COMMAND not in bot_source:
        failures.append(f"{COMMAND} is missing from bot.py")
    if f'sys.argv[1:] == ["{COMMAND}"]' not in bot_source:
        failures.append(f"{COMMAND} should have an exact early report-only route")


def verify_module_source(failures: list[str]) -> None:
    source = read_text(MODULE_PATH)
    for token in REQUIRED_FINAL_STATES:
        if token not in source:
            failures.append(f"Daily summary missing final state: {token}")
    for token in REQUIRED_ACTION_STATES:
        if token not in source:
            failures.append(f"Daily summary missing action classifier token: {token}")
    for token in FORBIDDEN_CALLS:
        if token in source:
            failures.append(f"Daily summary contains forbidden token: {token}")
    for token in ["write_text(", "DictWriter", "with path.open(\"w\"", ".mkdir("]:
        if token in source:
            failures.append(f"Daily summary should not create generated files: {token}")
    for high_risk in ["python bot.py", "--paper-order-test", "--execute-slow-sma-paper", "--confirm-slow-sma-paper", "--confirm-paper-order"]:
        if high_risk in source:
            failures.append(f"Daily summary should not suggest high-risk command text: {high_risk}")


def verify_command_output(failures: list[str]) -> None:
    completed = subprocess.run(
        [sys.executable, "bot.py", COMMAND],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    if completed.returncode != 0:
        failures.append(f"{COMMAND} failed with exit code {completed.returncode}")
    for phrase in REQUIRED_OUTPUT_PHRASES:
        if phrase not in output:
            failures.append(f"Daily summary output missing phrase: {phrase}")
    if "ModuleNotFoundError: No module named 'alpaca'" in output:
        failures.append(f"{COMMAND} must not require top-level Alpaca import")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
