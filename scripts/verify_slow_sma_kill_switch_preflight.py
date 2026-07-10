from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPLICATION = ROOT / "trading_bot" / "cli" / "application.py"
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
    bot_source = read_text(APPLICATION)
    help_text = bot_help_text()

    verify_help_gates(help_text, failures)
    verify_no_new_execution_commands(help_text, failures)
    verify_slow_sma_preflight_wiring(bot_source, failures)
    verify_paper_order_preflight_still_intact(bot_source, failures)
    verify_normal_bot_not_wired(bot_source, failures)
    verify_blocked_helper_context(failures)

    if failures:
        print("Slow SMA kill-switch preflight verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("SLOW SMA KILL-SWITCH PREFLIGHT VERIFICATION")
    print("Command gates: pass")
    print("Slow SMA preflight before Alpaca/database/order/alert work: pass")
    print("Paper-order-test preflight remains intact: pass")
    print("Normal bot path unchanged by helper: pass")
    print("Blocked helper context: pass")
    print("Result: passed")
    return 0


def verify_help_gates(help_text: str, failures: list[str]) -> None:
    if "--execute-slow-sma-paper" not in help_text:
        failures.append("--execute-slow-sma-paper is missing from help output")
    if "--confirm-slow-sma-paper" not in help_text:
        failures.append("--confirm-slow-sma-paper is missing from help output")
    confirm_context = help_line_for(help_text, "--confirm-slow-sma-paper").lower()
    if "required" not in confirm_context:
        failures.append("--confirm-slow-sma-paper help should remain explicitly required")


def verify_no_new_execution_commands(help_text: str, failures: list[str]) -> None:
    for command in SUSPICIOUS_NEW_EXECUTION_COMMANDS:
        if command in help_text:
            failures.append(f"unexpected new execution command present: {command}")


def verify_slow_sma_preflight_wiring(bot_source: str, failures: list[str]) -> None:
    if "evaluate_paper_kill_switch_gate" not in bot_source:
        failures.append("configured application must import evaluate_paper_kill_switch_gate")

    slow_source = function_block(
        bot_source,
        "def run_slow_sma_paper_execution(",
        "def validate_slow_sma_execution_safety(",
    )
    ticker_source = function_block(
        bot_source,
        "def process_slow_sma_execution_ticker(",
        "def decide_slow_sma_execution_action(",
    )
    if not slow_source:
        failures.append("could not locate run_slow_sma_paper_execution block")
        return
    helper_call = "evaluate_paper_kill_switch_gate("
    if helper_call not in slow_source:
        failures.append("run_slow_sma_paper_execution must call evaluate_paper_kill_switch_gate")
        return

    required_messages = [
        "SLOW SMA PAPER EXECUTION BLOCKED BY PAPER KILL-SWITCH PREFLIGHT.",
        "No orders were created, submitted, or cancelled.",
        "No SQLite execution trade_log rows were written.",
        "No Discord alerts were sent.",
        "No execution approval was granted.",
    ]
    for message in required_messages:
        if message not in slow_source:
            failures.append(f"blocked slow SMA output is missing message: {message}")

    preflight_index = slow_source.index(helper_call)
    for term in [
        "configure_yfinance_cache(",
        "get_slow_sma_preview_settings(",
        "init_database(",
        "send_discord_alert(",
        "TradingClient(",
        "get_alpaca_positions(",
        "process_slow_sma_execution_ticker(",
    ]:
        if term not in slow_source:
            failures.append(f"run_slow_sma_paper_execution is missing expected term: {term}")
        elif preflight_index > slow_source.index(term):
            failures.append(f"slow SMA kill-switch preflight must run before {term}")

    blocked_segment = segment_between(
        slow_source,
        "if not kill_switch_decision.allowed:",
        "validate_slow_sma_execution_safety(config)",
    )
    for term in [
        "configure_yfinance_cache(",
        "init_database(",
        "TradingClient(",
        "get_alpaca_positions(",
        "process_slow_sma_execution_ticker(",
        "insert_trade_log(",
        "send_discord_alert(",
        "submit_paper_order(",
        "get_open_orders_for_ticker(",
    ]:
        if term in blocked_segment:
            failures.append(f"blocked slow SMA segment must not call {term}")

    if ticker_source:
        for term in ["get_open_orders_for_ticker(", "submit_paper_order(", "insert_trade_log(", "send_discord_alert("]:
            if term not in ticker_source:
                failures.append(f"slow SMA ticker execution block should still contain existing term: {term}")


def verify_paper_order_preflight_still_intact(bot_source: str, failures: list[str]) -> None:
    manual_source = function_block(bot_source, "def run_paper_order_test(", "def estimate_manual_position_after(")
    if not manual_source:
        failures.append("could not locate run_paper_order_test block")
        return
    if not preflight_before_terms(manual_source, ["TradingClient(", "submit_paper_order(", "init_database("]):
        failures.append("paper-order-test preflight should remain before Alpaca/database/order work")


def verify_normal_bot_not_wired(bot_source: str, failures: list[str]) -> None:
    normal_source = function_block(bot_source, "def run_bot(", "def run_paper_order_test(")
    if normal_source and "evaluate_paper_kill_switch_gate(" in normal_source:
        failures.append("normal bot path must not use paper kill-switch helper in this task")


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
        command_name="execute_slow_sma_paper",
    )
    if result.allowed is not False or result.status != "blocked":
        failures.append("slow SMA context with missing prerequisites should be blocked")
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


def help_line_for(output: str, command: str) -> str:
    lines = output.splitlines()
    for index, line in enumerate(lines):
        if line.lstrip().startswith(command):
            context = [line]
            for next_line in lines[index + 1:]:
                stripped = next_line.strip()
                if stripped.startswith("--"):
                    break
                if stripped:
                    context.append(next_line)
            return " ".join(context)
    return ""


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
