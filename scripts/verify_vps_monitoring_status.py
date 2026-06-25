from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS_MODULE = ROOT / "trading_bot" / "research" / "vps_monitoring_status.py"
BOT_PATH = ROOT / "bot.py"

REQUIRED_OUTPUT_PHRASES = [
    "VPS MONITORING STATUS. REPORT ONLY. NOT EXECUTION.",
    "execution_approved=False",
    "scheduling_approved=False",
    "lock-wrapped safe command: --monitor-lockfile-readiness-report",
    "lock-wrapped safe command: --refresh-promoted-review",
    "lock-wrapped safe command: --refresh-defensive-research",
    "missing_saved_research_inputs",
    "Next safe manual report actions:",
    "Monitor lockfile readiness report flag: --monitor-lockfile-readiness-report",
    "Promoted review refresh flag: --refresh-promoted-review",
    "Defensive research refresh flag: --refresh-defensive-research",
    "High-risk/manual-only boundaries:",
    "Normal bot runs remain high-risk/manual-only and are outside safe VPS monitoring.",
    "Paper-order smoke tests remain excluded from safe monitoring and scheduling readiness.",
    "Slow-SMA paper execution remains excluded from safe monitoring and scheduling readiness.",
    "No execution-capable paper-trading command is approved for scheduling or automation.",
    "does not call Alpaca, yfinance, Discord, SQLite trade_log, or read config.json contents",
    "Promoted review state:",
    "Saved-output freshness:",
    "QQQ100 daily decision:",
    "qqq100_daily_decision_present:",
    "daily_decision_status:",
    "manual_discussion_status:",
    "qqq100_daily_decision_warning: monitor only; this is not order approval.",
    "data/promoted_review_refresh_summary.csv",
    "data/promoted_decision_preview.csv",
    "data/defensive_research_refresh_summary.csv",
    "data/market_monitor_scheduling_readiness_report.csv",
    "data/monitor_lockfile_readiness_report.csv",
    "Promoted review saved-output summaries are compact counts only and do not approve execution.",
]

FORBIDDEN_OUTPUT_PHRASES = [
    "python bot.py --paper-order-test",
    "python bot.py --execute-slow-sma-paper",
    "--paper-order-test",
    "--confirm-paper-order",
    "--execute-slow-sma-paper",
    "--confirm-slow-sma-paper",
]

FORBIDDEN_CALL_TOKENS = [
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
    verify_status_output_text(failures)
    verify_missing_promoted_outputs_do_not_fail(failures)
    verify_saved_promoted_outputs_are_summarized(failures)
    verify_source_has_no_forbidden_calls(failures)

    if failures:
        print("VPS monitoring status verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("VPS monitoring status verification passed.")
    print("Verified command registration, report-only output, blocked command wording, false approval flags, and no forbidden calls.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    bot_source = read_text(BOT_PATH)
    if "--vps-monitoring-status" not in bot_source:
        failures.append("--vps-monitoring-status is missing from bot.py")
    if "print_vps_monitoring_status" not in bot_source:
        failures.append("bot.py should route --vps-monitoring-status to the report-only status printer")


def verify_status_output_text(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.vps_monitoring_status import build_vps_monitoring_status_lines  # noqa: PLC0415

    output = "\n".join(build_vps_monitoring_status_lines(ROOT))
    for phrase in REQUIRED_OUTPUT_PHRASES:
        if phrase not in output:
            failures.append(f"Missing status output phrase: {phrase}")
    for phrase in FORBIDDEN_OUTPUT_PHRASES:
        if phrase in output:
            failures.append(f"Status output should avoid pasteable high-risk command string: {phrase}")


def verify_missing_promoted_outputs_do_not_fail(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.vps_monitoring_status import build_vps_monitoring_status_lines  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmpdir:
        output = "\n".join(build_vps_monitoring_status_lines(Path(tmpdir)))
    if "promoted_review_missing_saved_outputs" not in output:
        failures.append("Status command should label missing promoted review outputs without failing")
    if "execution_approved=False" not in output or "scheduling_approved=False" not in output:
        failures.append("Missing-output status should preserve false approval wording")


def verify_saved_promoted_outputs_are_summarized(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.vps_monitoring_status import build_vps_monitoring_status_lines  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        data_dir.mkdir()
        (data_dir / "promoted_review_refresh_summary.csv").write_text(
            "step_name,status,execution_approved\n"
            "preview_promoted_strategies,passed,False\n"
            "show_promoted_decision,failed,False\n",
            encoding="utf-8",
        )
        (data_dir / "promoted_decision_preview.csv").write_text(
            "ticker,decision_state,execution_approved\n"
            "AAPL,blocked_strategy_disagreement,False\n"
            "MSFT,no_action_unanimous_flat,False\n"
            "SPY,blocked_strategy_disagreement,False\n",
            encoding="utf-8",
        )
        output = "\n".join(build_vps_monitoring_status_lines(root))

    for phrase in [
        "promoted_review_summary_present: True",
        "promoted_review_step_counts: failed=1, passed=1",
        "promoted_decision_state_counts: blocked_strategy_disagreement=2, no_action_unanimous_flat=1",
        "execution_approved_false_for_all_rows=True",
    ]:
        if phrase not in output:
            failures.append(f"Saved promoted output summary missing phrase: {phrase}")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        data_dir.mkdir()
        (data_dir / "promoted_decision_preview.csv").write_text(
            "ticker,decision_state,execution_approved\n"
            "AAPL,review_required,True\n",
            encoding="utf-8",
        )
        output = "\n".join(build_vps_monitoring_status_lines(root))

    if "decision_execution_approval_warning: execution_approved_false_for_all_rows=False" not in output:
        failures.append("Saved promoted decision preview should warn if any execution_approved value is not false")


def verify_source_has_no_forbidden_calls(failures: list[str]) -> None:
    source = read_text(STATUS_MODULE)
    for token in FORBIDDEN_CALL_TOKENS:
        if token in source:
            failures.append(f"VPS status module must not contain forbidden call token: {token}")
    for required_path in ["data/promoted_review_refresh_summary.csv", "data/promoted_decision_preview.csv"]:
        if required_path not in source:
            failures.append(f"VPS status module should reference allowed promoted saved output: {required_path}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
