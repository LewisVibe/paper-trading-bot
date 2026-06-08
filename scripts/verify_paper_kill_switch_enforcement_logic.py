from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.safety.paper_kill_switch import evaluate_paper_kill_switch_gate


SUSPICIOUS_NEW_EXECUTION_COMMANDS = [
    "--defensive-allocation-execute",
    "--execute-defensive-allocation",
    "--paper-defensive-allocation",
    "--confirm-defensive-allocation",
    "--defensive-paper-execution",
]

ORDER_TERMS_FOR_HELPER = [
    "MarketOrderRequest",
    "TradingClient",
    "submit" + "_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "download_close_prices",
    "download_backtest_prices",
    "sqlite3",
]

ORDER_INSTRUCTION_COLUMNS = {
    "side",
    "quantity",
    "order_type",
    "order_id",
    "target_order",
    "submit" + "_order",
}


def main() -> int:
    failures: list[str] = []
    verify_gate_cases(failures)
    verify_helper_is_pure(failures)
    verify_wiring_limited_to_manual_paper_order_test(failures)
    verify_no_new_execution_command(failures)
    verify_high_risk_commands_still_gated(failures)
    verify_no_order_instruction_schema(failures)

    if failures:
        print("Paper kill-switch enforcement logic verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper kill-switch enforcement logic verification passed.")
    return 0


def safe_context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "alpaca_paper": True,
        "dry_run": True,
        "explicit_paper_execution_requested": True,
        "allow_shorting": False,
        "paper_kill_switch_enabled": True,
        "execution_eligibility_blocked": False,
        "defensive_decision_blocked": False,
        "explicit_confirmation": True,
        "command_name": "future_dedicated_defensive_paper_execution",
    }
    context.update(overrides)
    return context


def verify_gate_cases(failures: list[str]) -> None:
    allowed = evaluate_paper_kill_switch_gate(**safe_context())
    if allowed.allowed is not True or allowed.status != "allowed":
        failures.append("safe all-true paper context should be allowed in isolated helper tests")

    blocked_cases = [
        ("alpaca_paper_false", {"alpaca_paper": False}),
        ("allow_shorting_true", {"allow_shorting": True}),
        ("kill_switch_false", {"paper_kill_switch_enabled": False}),
        ("kill_switch_none", {"paper_kill_switch_enabled": None}),
        ("execution_eligibility_blocked", {"execution_eligibility_blocked": True}),
        ("defensive_decision_blocked", {"defensive_decision_blocked": True}),
        ("explicit_confirmation_false", {"explicit_confirmation": False}),
        ("command_name_missing", {"command_name": ""}),
        ("command_name_normal_bot", {"command_name": "python bot.py"}),
        ("dry_run_false_without_explicit_request", {"dry_run": False, "explicit_paper_execution_requested": False}),
    ]
    for name, overrides in blocked_cases:
        result = evaluate_paper_kill_switch_gate(**safe_context(**overrides))
        if result.allowed is not False or result.status != "blocked" or not result.reasons:
            failures.append(f"{name} should block with at least one reason")


def verify_helper_is_pure(failures: list[str]) -> None:
    import trading_bot.safety.paper_kill_switch as helper_module

    source = inspect.getsource(helper_module)
    for term in ORDER_TERMS_FOR_HELPER:
        if term in source:
            failures.append(f"isolated helper references forbidden execution term: {term}")


def verify_wiring_limited_to_manual_paper_order_test(failures: list[str]) -> None:
    bot_source = read_text(ROOT / "bot.py")
    if "evaluate_paper_kill_switch_gate" not in bot_source:
        failures.append("manual paper-order test should use isolated paper kill-switch helper")
    elif not helper_call_is_limited_to_scoped_paper_commands(bot_source):
        failures.append("helper wiring should be limited to manual and slow SMA paper preflights before Alpaca/database/order work")

    high_risk_paths = [
        ROOT / "trading_bot" / "execution.py",
        ROOT / "trading_bot" / "alpaca_client.py",
        ROOT / "trading_bot" / "database.py",
        ROOT / "trading_bot" / "discord_alerts.py",
    ]
    for path in high_risk_paths:
        text = read_text(path)
        if "trading_bot.safety.paper_kill_switch" in text or "evaluate_paper_kill_switch_gate" in text:
            failures.append(f"helper should not be wired into high-risk path: {path.relative_to(ROOT)}")


def verify_no_new_execution_command(failures: list[str]) -> None:
    help_text = bot_help_text()
    for command in SUSPICIOUS_NEW_EXECUTION_COMMANDS:
        if command in help_text:
            failures.append(f"unexpected defensive execution command present: {command}")


def verify_high_risk_commands_still_gated(failures: list[str]) -> None:
    help_text = bot_help_text()
    if "--paper-order-test" not in help_text or "--confirm-paper-order" not in help_text:
        failures.append("--paper-order-test must remain paired with --confirm-paper-order")
    if "--execute-slow-sma-paper" not in help_text or "--confirm-slow-sma-paper" not in help_text:
        failures.append("--execute-slow-sma-paper must remain paired with --confirm-slow-sma-paper")


def verify_no_order_instruction_schema(failures: list[str]) -> None:
    helper_fields = {"allowed", "status", "reasons", "required_next_step"}
    found = sorted(ORDER_INSTRUCTION_COLUMNS.intersection(helper_fields))
    if found:
        failures.append("helper result schema includes order-instruction fields: " + ", ".join(found))


def bot_help_text() -> str:
    result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    return (result.stdout or "") + "\n" + (result.stderr or "")


def helper_call_is_limited_to_scoped_paper_commands(bot_source: str) -> bool:
    try:
        manual_start = bot_source.index("def run_paper_order_test(")
        manual_end = bot_source.index("def estimate_manual_position_after(", manual_start)
        slow_start = bot_source.index("def run_slow_sma_paper_execution(")
        slow_end = bot_source.index("def validate_slow_sma_execution_safety(", slow_start)
    except ValueError:
        return False
    manual_source = bot_source[manual_start:manual_end]
    slow_source = bot_source[slow_start:slow_end]
    outside_source = (
        bot_source[:manual_start]
        + bot_source[manual_end:slow_start]
        + bot_source[slow_end:]
    )
    if "evaluate_paper_kill_switch_gate(" in outside_source:
        return False
    if not preflight_before_terms(manual_source, ["TradingClient(", "submit_alpaca_order(", "init_database("]):
        return False
    return preflight_before_terms(
        slow_source,
        ["configure_yfinance_cache(", "init_database(", "send_discord_alert(", "TradingClient(", "get_alpaca_positions("],
    )


def preflight_before_terms(source: str, terms: list[str]) -> bool:
    helper_call = "evaluate_paper_kill_switch_gate("
    if helper_call not in source:
        return False
    preflight_index = source.index(helper_call)
    for term in terms:
        if term not in source or preflight_index > source.index(term):
            return False
    return True


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
