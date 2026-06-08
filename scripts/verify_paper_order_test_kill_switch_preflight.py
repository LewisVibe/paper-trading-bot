from __future__ import annotations

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


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    help_text = bot_help_text()

    verify_help_gates(help_text, failures)
    verify_no_new_execution_commands(help_text, failures)
    verify_preflight_wiring(bot_source, failures)
    verify_blocked_helper_context(failures)

    if failures:
        print("Paper-order-test kill-switch preflight verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PAPER ORDER TEST KILL-SWITCH PREFLIGHT VERIFICATION")
    print("Command gates: pass")
    print("Preflight before Alpaca/database/order work: pass")
    print("Normal bot path unchanged by helper: pass")
    print("Blocked helper context: pass")
    print("Result: passed")
    return 0


def verify_help_gates(help_text: str, failures: list[str]) -> None:
    if "--paper-order-test" not in help_text:
        failures.append("--paper-order-test is missing from help output")
    if "--confirm-paper-order" not in help_text:
        failures.append("--confirm-paper-order is missing from help output")
    if "--execute-slow-sma-paper" not in help_text:
        failures.append("--execute-slow-sma-paper is missing from help output")
    if "--confirm-slow-sma-paper" not in help_text:
        failures.append("--confirm-slow-sma-paper is missing from help output")


def verify_no_new_execution_commands(help_text: str, failures: list[str]) -> None:
    for command in SUSPICIOUS_NEW_EXECUTION_COMMANDS:
        if command in help_text:
            failures.append(f"unexpected new execution command present: {command}")


def verify_preflight_wiring(bot_source: str, failures: list[str]) -> None:
    if "from trading_bot.safety.paper_kill_switch import evaluate_paper_kill_switch_gate" not in bot_source:
        failures.append("bot.py must import evaluate_paper_kill_switch_gate for manual paper-order preflight")

    manual_source = function_block(bot_source, "def run_paper_order_test(", "def estimate_manual_position_after(")
    if not manual_source:
        failures.append("could not locate run_paper_order_test block")
        return
    if "evaluate_paper_kill_switch_gate(" not in manual_source:
        failures.append("run_paper_order_test must call evaluate_paper_kill_switch_gate")
        return

    preflight_index = manual_source.index("evaluate_paper_kill_switch_gate(")
    for term in ["TradingClient(", "submit_alpaca_order(", "init_database("]:
        if term not in manual_source:
            failures.append(f"run_paper_order_test is missing expected term: {term}")
        elif preflight_index > manual_source.index(term):
            failures.append(f"kill-switch preflight must run before {term}")

    blocked_segment = segment_between(
        manual_source,
        "if not kill_switch_decision.allowed:",
        "if not config.alpaca_api_key",
    )
    required_messages = [
        "PAPER ORDER TEST BLOCKED BY PAPER KILL-SWITCH PREFLIGHT.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
    ]
    for message in required_messages:
        if message not in blocked_segment:
            failures.append(f"blocked preflight output is missing message: {message}")
    forbidden_blocked_terms = [
        "TradingClient(",
        "submit_alpaca_order(",
        "insert_trade_log(",
        "send_discord_alert(",
        "cancel_order",
        "init_database(",
    ]
    for term in forbidden_blocked_terms:
        if term in blocked_segment:
            failures.append(f"blocked preflight segment must not call {term}")

    normal_source = function_block(bot_source, "def run_bot(", "def run_paper_order_test(")
    if normal_source and "evaluate_paper_kill_switch_gate" in normal_source:
        failures.append("normal bot path must not use manual paper-order kill-switch preflight")


def verify_blocked_helper_context(failures: list[str]) -> None:
    result = evaluate_paper_kill_switch_gate(
        alpaca_paper=True,
        dry_run=True,
        explicit_paper_execution_requested=True,
        allow_shorting=False,
        paper_kill_switch_enabled=None,
        execution_eligibility_blocked=True,
        defensive_decision_blocked=True,
        explicit_confirmation=True,
        command_name="paper_order_test",
    )
    if result.allowed is not False or result.status != "blocked":
        failures.append("manual paper-order context with missing prerequisites should be blocked")
    expected_reasons = {
        "paper_kill_switch_enabled must be explicitly True",
        "execution eligibility is blocked",
        "defensive allocation decision is blocked",
    }
    missing = sorted(expected_reasons.difference(result.reasons))
    if missing:
        failures.append("blocked helper result is missing reasons: " + ", ".join(missing))


def bot_help_text() -> str:
    result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    return (result.stdout or "") + "\n" + (result.stderr or "")


def function_block(source: str, start_marker: str, end_marker: str) -> str:
    try:
        start = source.index(start_marker)
        end = source.index(end_marker, start)
    except ValueError:
        return ""
    return source[start:end]


def segment_between(source: str, start_marker: str, end_marker: str) -> str:
    try:
        start = source.index(start_marker)
        end = source.index(end_marker, start)
    except ValueError:
        return ""
    return source[start:end]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
