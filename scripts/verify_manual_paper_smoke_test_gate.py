from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.safety.manual_paper_smoke_test_gate import (  # noqa: E402
    GATE_TYPE,
    READY_PREFLIGHT_STATUS,
    SavedSmokeTestPreflightContext,
    evaluate_manual_paper_smoke_test_gate,
)


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    helper_source = read_text(ROOT / "trading_bot" / "safety" / "manual_paper_smoke_test_gate.py")

    verify_helper_cases(failures)
    verify_wiring_scope(bot_source, failures)
    verify_order_path_boundaries(bot_source, failures)
    verify_helper_safety(helper_source, failures)
    verify_outputs_ignored(failures)
    verify_no_scheduler_or_strategy_wiring(bot_source, failures)

    if failures:
        print("Manual paper smoke-test gate verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Manual paper smoke-test gate verification passed.")
    print("Verified exact AAPL buy 1 gate, blocked non-template cases, unchanged strategy execution boundaries, and ignored gate reports.")
    return 0


def verify_helper_cases(failures: list[str]) -> None:
    preflight = SavedSmokeTestPreflightContext(
        live_preflight_status=READY_PREFLIGHT_STATUS,
        market_status="open",
        ticker="AAPL",
        side="buy",
        quantity="1",
        open_order_check="pass",
    )
    allowed = evaluate_manual_paper_smoke_test_gate(
        ticker="AAPL",
        side="buy",
        quantity=Decimal("1"),
        confirm_paper_order=True,
        alpaca_paper=True,
        allow_shorting=False,
        credentials_present=True,
        preflight=preflight,
        direct_open_order_count=0,
        duplicate_recent_order_exists=False,
    )
    if not allowed.allowed or allowed.gate_type != GATE_TYPE:
        failures.append("exact AAPL buy 1 confirmed smoke-test context should pass the dedicated gate")
    if allowed.smoke_test_order_approved is not True:
        failures.append("smoke_test_order_approved should be true only for the exact passing smoke-test gate")
    if allowed.execution_approved or allowed.strategy_execution_approved or allowed.scheduling_approved:
        failures.append("passing smoke-test gate must not approve strategy execution or scheduling")

    cases = [
        ("wrong_ticker", {"ticker": "MSFT"}),
        ("wrong_side", {"side": "sell"}),
        ("wrong_quantity", {"quantity": Decimal("2")}),
        ("missing_confirmation", {"confirm_paper_order": False}),
        ("non_paper", {"alpaca_paper": False}),
        ("shorting_enabled", {"allow_shorting": True}),
        ("missing_credentials", {"credentials_present": False}),
        ("market_closed", {"preflight": SavedSmokeTestPreflightContext(READY_PREFLIGHT_STATUS, "closed", "AAPL", "buy", "1", "pass")}),
        ("preflight_not_ready", {"preflight": SavedSmokeTestPreflightContext("blocked", "open", "AAPL", "buy", "1", "pass")}),
        ("open_order_exists", {"direct_open_order_count": 1}),
        ("duplicate_recent_order", {"duplicate_recent_order_exists": True}),
    ]
    defaults = {
        "ticker": "AAPL",
        "side": "buy",
        "quantity": Decimal("1"),
        "confirm_paper_order": True,
        "alpaca_paper": True,
        "allow_shorting": False,
        "credentials_present": True,
        "preflight": preflight,
        "direct_open_order_count": 0,
        "duplicate_recent_order_exists": False,
    }
    for name, override in cases:
        params = dict(defaults)
        params.update(override)
        result = evaluate_manual_paper_smoke_test_gate(**params)
        if result.allowed:
            failures.append(f"{name} should remain blocked by the smoke-test gate")
        if result.smoke_test_order_approved:
            failures.append(f"{name} should not approve a smoke-test order")


def verify_wiring_scope(bot_source: str, failures: list[str]) -> None:
    manual_source = function_block(bot_source, "def run_paper_order_test(", "def manual_paper_order_execution_eligibility_blocked(")
    if not manual_source:
        failures.append("could not locate run_paper_order_test block")
        return
    required = [
        "evaluate_manual_paper_smoke_test_gate(",
        "is_aapl_buy_one_template = ticker == \"AAPL\" and side == \"buy\" and quantity == Decimal(\"1\")",
        "if smoke_test_gate_decision is None:",
        "evaluate_paper_kill_switch_gate(",
        "recent_matching_manual_smoke_test_order_exists(",
        "write_manual_paper_smoke_test_gate_report(",
        "print_manual_smoke_test_gate_decision(",
    ]
    for token in required:
        if token not in manual_source:
            failures.append(f"run_paper_order_test missing smoke-gate token: {token}")
    if manual_source.index("evaluate_manual_paper_smoke_test_gate(") > manual_source.index("TradingClient("):
        failures.append("manual smoke-test gate must run before TradingClient is created")
    if manual_source.index("evaluate_manual_paper_smoke_test_gate(") > manual_source.index("init_database("):
        failures.append("manual smoke-test gate must run before database initialization")


def verify_order_path_boundaries(bot_source: str, failures: list[str]) -> None:
    normal_source = function_block(bot_source, "def run_bot(", "def run_paper_order_test(")
    slow_source = function_block(bot_source, "def run_slow_sma_paper_execution(", "def parse_args(")
    if "evaluate_manual_paper_smoke_test_gate" in normal_source:
        failures.append("normal bot execution path must not use the smoke-test gate")
    if "evaluate_manual_paper_smoke_test_gate" in slow_source:
        failures.append("slow SMA paper execution path must not use the smoke-test gate")
    if "qqq100" in function_block(bot_source, "def run_paper_order_test(", "def manual_paper_order_execution_eligibility_blocked(").lower():
        failures.append("paper-order smoke-test gate must not mention or wire QQQ100 strategy execution")


def verify_helper_safety(helper_source: str, failures: list[str]) -> None:
    forbidden = [
        "TradingClient",
        "submit_order",
        "cancel_order",
        "replace_order",
        "insert_trade_log",
        "send_discord_alert",
        "send_telegram",
        "load_config(",
        "config.json",
        "sched.scheduler",
        "Register-ScheduledTask",
        "schtasks",
        "crontab",
        "systemctl",
        "alpaca_api_key",
        "webhook",
        "account_id",
    ]
    for token in forbidden:
        if token in helper_source:
            failures.append(f"helper must not contain forbidden token: {token}")
    required = [
        "smoke_test_order_approved",
        "execution_approved",
        "strategy_execution_approved",
        "scheduling_approved",
        "followup_order_approved",
        "paper_order_smoke_test_gate_report.csv",
        "paper_order_smoke_test_gate_summary.csv",
        "paper_order_smoke_test_gate_blockers.csv",
    ]
    for token in required:
        if token not in helper_source:
            failures.append(f"helper missing required report/safety token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in [
        "data/paper_order_smoke_test_gate_report.csv",
        "data/paper_order_smoke_test_gate_summary.csv",
        "data/paper_order_smoke_test_gate_blockers.csv",
    ]:
        completed = subprocess.run(["git", "check-ignore", output], cwd=ROOT, text=True, capture_output=True, timeout=10)
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_no_scheduler_or_strategy_wiring(bot_source: str, failures: list[str]) -> None:
    for token in ["Register-ScheduledTask", "schtasks /create", "crontab", "systemctl", "--execute-qqq100", "--qqq100-paper-execute"]:
        if token in bot_source:
            failures.append(f"unexpected scheduler or strategy execution token present: {token}")


def function_block(source: str, start_marker: str, end_marker: str) -> str:
    try:
        start = source.index(start_marker)
        end = source.index(end_marker, start)
    except ValueError:
        return ""
    return source[start:end]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


if __name__ == "__main__":
    raise SystemExit(main())
