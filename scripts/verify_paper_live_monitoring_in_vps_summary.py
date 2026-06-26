from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VPS_STATUS_MODULE = ROOT / "trading_bot" / "research" / "vps_monitoring_status.py"
VPS_DAILY_MODULE = ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py"

REQUIRED_SOURCE_TOKENS = [
    "PAPER_LIVE_MONITORING_STATUS_PATH",
    "QQQ100_DAILY_DECISION_SUMMARY_PATH",
    "build_paper_live_monitoring_context",
    "paper_live_monitoring_status_lines",
    "qqq100_daily_decision_status_lines",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
    "MULTI_SLEEVE",
    "qqq_100_trend_gate",
    "paper_position_long",
    "aligned_long",
    "no_action_required_already_aligned",
    "hold_no_action_and_monitor_only",
    "followup_order_approved",
    "repeat_execution_approved",
    "never_schedule_order_capable_commands",
    "paper_live_monitoring_saved_status_missing_or_inconsistent",
    "refresh_report_only_paper_live_monitoring_status",
    "qqq100_daily_decision_saved_status_missing",
    "refresh_report_only_qqq100_daily_decision",
]

REQUIRED_OUTPUT_PHRASES = [
    "Paper-live monitoring status:",
    "paper_live_monitoring_status_present: True",
    "paper_live_monitoring_status_consistent: True",
    "paper_live_monitoring_approval_flags_false: True",
    "active_strategy: higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
    "active_ticker: MULTI_SLEEVE",
    "previous_seed_strategy: qqq_100_trend_gate",
    "previous_seed_ticker: QQQ",
    "saved_position_state: paper_position_long",
    "saved_position_quantity: 1",
    "alignment_state: aligned_long",
    "followup_policy_status: no_action_required_already_aligned",
    "no_action_required: True",
    "recommended_next_step: hold_no_action_and_monitor_only",
    "followup_order_approved: False",
    "repeat_execution_approved: False",
    "never_schedule_order_capable_commands: True",
    "paper_live_monitoring_warning: monitor only; repeat/follow-up orders are not approved.",
    "QQQ100 daily decision:",
    "qqq100_daily_decision_present: True",
    "daily_decision_status: qqq100_daily_decision_hold_no_action_aligned_long",
    "manual_discussion_status: manual_trade_discussion_not_needed",
    "qqq100_daily_decision_warning: monitor only; this is not order approval.",
]

FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    "submit_order(",
    "cancel_order(",
    "replace_order(",
    "get_alpaca_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "yf.",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab -e",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    verify_source(failures)
    verify_output_with_saved_status(failures)
    verify_missing_saved_status_stays_blocked(failures)

    if failures:
        print("Paper-live monitoring VPS summary verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live monitoring VPS summary verification passed.")
    print("Verified volatility active seed and previous QQQ100 saved status appear in VPS summaries without broker/order/scheduling calls.")
    return 0


def verify_source(failures: list[str]) -> None:
    source = read_text(VPS_STATUS_MODULE) + "\n" + read_text(VPS_DAILY_MODULE)
    for token in REQUIRED_SOURCE_TOKENS:
        if token not in source:
            failures.append(f"missing source token: {token}")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"forbidden broker/order/config/market/scheduling token found: {token}")


def verify_output_with_saved_status(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.vps_daily_monitoring_summary import build_vps_daily_monitoring_summary_lines  # noqa: PLC0415
    from trading_bot.research.vps_monitoring_status import build_vps_monitoring_status_lines  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        data_dir.mkdir()
        write_saved_paper_live_status(data_dir / "paper_live_monitoring_status.csv")
        write_saved_qqq100_daily_decision(data_dir / "qqq100_daily_decision_summary.csv")
        write_promoted_decision(data_dir / "promoted_decision_preview.csv")
        output = "\n".join(build_vps_monitoring_status_lines(root))
        output += "\n" + "\n".join(build_vps_daily_monitoring_summary_lines(root))

    for phrase in REQUIRED_OUTPUT_PHRASES:
        if phrase not in output:
            failures.append(f"saved-status output missing phrase: {phrase}")
    if "execution_approved=False" not in output or "scheduling_approved=False" not in output:
        failures.append("VPS summaries must preserve false execution/scheduling approval wording")


def verify_missing_saved_status_stays_blocked(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.vps_daily_monitoring_summary import build_vps_daily_monitoring_summary_lines  # noqa: PLC0415
    from trading_bot.research.vps_monitoring_status import build_vps_monitoring_status_lines  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        output = "\n".join(build_vps_monitoring_status_lines(root))
        output += "\n" + "\n".join(build_vps_daily_monitoring_summary_lines(root))

    for phrase in [
        "paper_live_monitoring_status_present: False",
        "paper_live_monitoring_missing_saved_output: data/paper_live_monitoring_status.csv",
        "paper_live_monitoring_manual_review_items: missing_file:data/paper_live_monitoring_status.csv",
        "final_status: monitoring_stale_or_missing_inputs",
        "action_required: manual_review_required",
        "action_reason: paper_live_monitoring_saved_status_missing_or_inconsistent",
        "suggested_manual_action: refresh_report_only_paper_live_monitoring_status",
    ]:
        if phrase not in output:
            failures.append(f"missing-status output missing phrase: {phrase}")


def write_saved_paper_live_status(path: Path) -> None:
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
        "recommended_next_step,hold_no_action_and_monitor_only,Monitor only.,False,False,False,False,False,False\n"
        "never_schedule_order_capable_commands,True,Do not schedule order-capable commands.,False,False,False,False,False,False\n"
        "execution_approved,False,Execution approval remains false.,False,False,False,False,False,False\n"
        "paper_execution_approved,False,Paper execution approval remains false.,False,False,False,False,False,False\n"
        "scheduling_approved,False,Scheduling approval remains false.,False,False,False,False,False,False\n"
        "live_trading_approved,False,Live trading approval remains false.,False,False,False,False,False,False\n"
        "followup_order_approved,False,Follow-up order approval remains false.,False,False,False,False,False,False\n"
        "repeat_execution_approved,False,Repeat execution approval remains false.,False,False,False,False,False,False\n",
        encoding="utf-8",
    )


def write_saved_qqq100_daily_decision(path: Path) -> None:
    path.write_text(
        "summary_name,summary_value,details,execution_approved,paper_execution_approved,scheduling_approved,live_trading_approved,followup_order_approved,repeat_execution_approved\n"
        "daily_decision_status,qqq100_daily_decision_hold_no_action_aligned_long,Saved daily decision.,False,False,False,False,False,False\n"
        "active_strategy,qqq_100_trend_gate,Only QQQ100 in scope.,False,False,False,False,False,False\n"
        "active_ticker,QQQ,Only QQQ in scope.,False,False,False,False,False,False\n"
        "desired_state,long,Saved desired state.,False,False,False,False,False,False\n"
        "saved_position_state,paper_position_long,Saved QQQ paper position state.,False,False,False,False,False,False\n"
        "saved_position_quantity,1,Saved QQQ quantity.,False,False,False,False,False,False\n"
        "alignment_state,aligned_long,Saved alignment state.,False,False,False,False,False,False\n"
        "followup_policy_status,no_action_required_already_aligned,Saved policy.,False,False,False,False,False,False\n"
        "no_action_required,True,No action needed.,False,False,False,False,False,False\n"
        "manual_discussion_status,manual_trade_discussion_not_needed,No trade discussion needed.,False,False,False,False,False,False\n"
        "recommended_next_step,hold_no_action_and_monitor_only,Monitor only.,False,False,False,False,False,False\n"
        "never_schedule_order_capable_commands,True,Do not schedule order-capable commands.,False,False,False,False,False,False\n"
        "execution_approved,False,Execution approval remains false.,False,False,False,False,False,False\n"
        "paper_execution_approved,False,Paper execution approval remains false.,False,False,False,False,False,False\n"
        "scheduling_approved,False,Scheduling approval remains false.,False,False,False,False,False,False\n"
        "live_trading_approved,False,Live trading approval remains false.,False,False,False,False,False,False\n"
        "followup_order_approved,False,Follow-up order approval remains false.,False,False,False,False,False,False\n"
        "repeat_execution_approved,False,Repeat execution approval remains false.,False,False,False,False,False,False\n",
        encoding="utf-8",
    )


def write_promoted_decision(path: Path) -> None:
    path.write_text(
        "ticker,decision_state,execution_approved\n"
        "QQQ,no_action_unanimous_flat,False\n",
        encoding="utf-8",
    )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
