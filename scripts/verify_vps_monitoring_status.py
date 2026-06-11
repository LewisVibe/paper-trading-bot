from __future__ import annotations

import sys
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
    "config_missing_for_readonly_promoted_review",
    "missing_saved_research_inputs",
    "python bot.py --monitor-lockfile-readiness-report",
    "python bot.py --refresh-promoted-review",
    "python bot.py --refresh-defensive-research",
    "python bot.py --paper-order-test ... --confirm-paper-order",
    "python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper",
    "--paper-order-test",
    "--confirm-paper-order",
    "--execute-slow-sma-paper",
    "--confirm-slow-sma-paper",
    "does not call Alpaca, yfinance, Discord, SQLite trade_log, or read config.json contents",
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


def verify_source_has_no_forbidden_calls(failures: list[str]) -> None:
    source = read_text(STATUS_MODULE)
    for token in FORBIDDEN_CALL_TOKENS:
        if token in source:
            failures.append(f"VPS status module must not contain forbidden call token: {token}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
