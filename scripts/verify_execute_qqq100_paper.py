from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.positions import Position  # noqa: E402
from trading_bot.safety.manual_paper_smoke_test_gate import (  # noqa: E402
    ManualSmokeTestRecentOrderMatch,
)
from trading_bot.safety.qqq100_paper_execution import (  # noqa: E402
    FIXED_QUANTITY,
    RESULT_PATH,
    STRATEGY_NAME,
    SUMMARY_PATH,
    TICKER,
    Qqq100SavedSignal,
    evaluate_qqq100_paper_execution_preflight,
)


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    helper_source = read_text(ROOT / "trading_bot" / "safety" / "qqq100_paper_execution.py")

    verify_helper_cases(failures)
    verify_command_registration(bot_source, failures)
    verify_runtime_scope(bot_source, failures)
    verify_helper_safety(helper_source, failures)
    verify_outputs_ignored(failures)
    verify_no_secrets_or_forbidden_wiring(bot_source, helper_source, failures)

    if failures:
        print("QQQ100 paper execution verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 paper execution verification passed.")
    print("Verified narrow confirmed QQQ/1-share command, blocked unsafe contexts, and unchanged broader execution paths.")
    return 0


def verify_helper_cases(failures: list[str]) -> None:
    signal = Qqq100SavedSignal(True, STRATEGY_NAME, TICKER, "long", "2026-06-15", "ok", "")
    allowed_buy = evaluate_qqq100_paper_execution_preflight(
        confirm_qqq100_paper=True,
        alpaca_paper=True,
        allow_shorting=False,
        credentials_present=True,
        market_status="open",
        signal=signal,
        current_position=Position(Decimal("0")),
        position_readable=True,
        open_order_count=0,
        recent_order_match=recent_order_pass(),
    )
    if not allowed_buy.allowed or allowed_buy.intended_action != "buy_1" or allowed_buy.order_side != "buy":
        failures.append("confirmed long signal with flat QQQ position should allow exactly one buy")
    if allowed_buy.quantity != "1" or FIXED_QUANTITY != Decimal("1"):
        failures.append("QQQ100 paper command must be fixed at one share")
    if not allowed_buy.strategy_execution_approved:
        failures.append("exact passing QQQ100 alignment should set strategy_execution_approved true")
    if allowed_buy.execution_approved or allowed_buy.paper_execution_approved or allowed_buy.scheduling_approved:
        failures.append("general execution, paper execution, and scheduling approvals must remain false")

    allowed_hold = evaluate_qqq100_paper_execution_preflight(
        confirm_qqq100_paper=True,
        alpaca_paper=True,
        allow_shorting=False,
        credentials_present=True,
        market_status="open",
        signal=signal,
        current_position=Position(Decimal("1")),
        position_readable=True,
        open_order_count=0,
    )
    if not allowed_hold.allowed or allowed_hold.intended_action != "hold_already_long":
        failures.append("long signal with exactly one existing QQQ paper share should hold")

    blocked_excess_long = evaluate_qqq100_paper_execution_preflight(
        confirm_qqq100_paper=True,
        alpaca_paper=True,
        allow_shorting=False,
        credentials_present=True,
        market_status="open",
        signal=signal,
        current_position=Position(Decimal("2")),
        position_readable=True,
        open_order_count=0,
        recent_order_match=recent_order_pass(),
    )
    if blocked_excess_long.allowed or blocked_excess_long.intended_action != "blocked_excess_long_position":
        failures.append("long signal with more than one QQQ paper share must block for manual review")

    flat_signal = Qqq100SavedSignal(True, STRATEGY_NAME, TICKER, "flat", "2026-06-15", "ok", "")
    allowed_sell = evaluate_qqq100_paper_execution_preflight(
        confirm_qqq100_paper=True,
        alpaca_paper=True,
        allow_shorting=False,
        credentials_present=True,
        market_status="open",
        signal=flat_signal,
        current_position=Position(Decimal("1")),
        position_readable=True,
        open_order_count=0,
        recent_order_match=recent_order_pass(),
    )
    if not allowed_sell.allowed or allowed_sell.intended_action != "sell_1" or allowed_sell.order_side != "sell":
        failures.append("flat signal with long QQQ position should allow exactly one sell")

    blocked_excess_flat = evaluate_qqq100_paper_execution_preflight(
        confirm_qqq100_paper=True,
        alpaca_paper=True,
        allow_shorting=False,
        credentials_present=True,
        market_status="open",
        signal=flat_signal,
        current_position=Position(Decimal("2")),
        position_readable=True,
        open_order_count=0,
        recent_order_match=recent_order_pass(),
    )
    if blocked_excess_flat.allowed or blocked_excess_flat.intended_action != "blocked_excess_long_position":
        failures.append("flat signal with more than one QQQ paper share must block for manual review")

    cases = [
        ("missing_confirmation", {"confirm_qqq100_paper": False}),
        ("live_mode", {"alpaca_paper": False}),
        ("shorting_enabled", {"allow_shorting": True}),
        ("missing_credentials", {"credentials_present": False}),
        ("market_closed", {"market_status": "closed"}),
        ("missing_signal", {"signal": Qqq100SavedSignal(False, "", "", "", "", "missing", "missing")}),
        ("wrong_strategy", {"signal": Qqq100SavedSignal(True, "other_strategy", TICKER, "long", "", "ok", "")}),
        ("wrong_ticker", {"signal": Qqq100SavedSignal(True, STRATEGY_NAME, "SPY", "long", "", "ok", "")}),
        ("unknown_desired_position", {"signal": Qqq100SavedSignal(True, STRATEGY_NAME, TICKER, "short", "", "ok", "")}),
        ("position_unreadable", {"current_position": None, "position_readable": False}),
        ("open_order_exists", {"open_order_count": 1}),
        ("recent_matching_order", {"recent_order_match": recent_order_blocked()}),
    ]
    defaults = {
        "confirm_qqq100_paper": True,
        "alpaca_paper": True,
        "allow_shorting": False,
        "credentials_present": True,
        "market_status": "open",
        "signal": signal,
        "current_position": Position(Decimal("0")),
        "position_readable": True,
        "open_order_count": 0,
        "recent_order_match": recent_order_pass(),
    }
    for name, override in cases:
        params = dict(defaults)
        params.update(override)
        result = evaluate_qqq100_paper_execution_preflight(**params)
        if result.allowed:
            failures.append(f"{name} should block QQQ100 paper execution")
        if result.strategy_execution_approved or result.qqq100_one_share_alignment_approved:
            failures.append(f"{name} should not approve QQQ100 paper alignment")

    short_position = evaluate_qqq100_paper_execution_preflight(
        **{**defaults, "current_position": Position(Decimal("-1"))}
    )
    if short_position.allowed or short_position.intended_action != "blocked_short_position":
        failures.append("short QQQ position must block; the command must not support short or leverage handling")


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--execute-qqq100-paper",
        "--confirm-qqq100-paper",
        "run_execute_qqq100_paper(",
        "confirm_qqq100_paper=args.confirm_qqq100_paper",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing QQQ100 paper command token: {token}")


def verify_runtime_scope(bot_source: str, failures: list[str]) -> None:
    qqq_source = function_block(bot_source, "def run_execute_qqq100_paper(", "def manual_paper_order_execution_eligibility_blocked(")
    if not qqq_source:
        failures.append("could not locate run_execute_qqq100_paper block")
        return
    required = [
        "read_saved_qqq100_preview_signal()",
        "QQQ100_TICKER",
        "QQQ100_FIXED_QUANTITY",
        "confirm_qqq100_paper",
        "config.alpaca_paper",
        "get_alpaca_positions(alpaca_client)",
        "get_open_orders_for_ticker(alpaca_client, QQQ100_TICKER)",
        "recent_matching_manual_smoke_test_order_check(",
        "validate_alpaca_asset_for_order(",
        "submit_alpaca_order(",
        "write_qqq100_paper_execution_report(",
    ]
    for token in required:
        if token not in qqq_source:
            failures.append(f"QQQ100 execution block missing required token: {token}")
    forbidden = [
        "config.tickers",
        "default_research_universe_tickers",
        "codex_broad_growth_balanced_breakout_control",
        "qqq_150_trend_gate",
        "codex_qqq_adaptive_trend_exposure",
        "crypto",
    ]
    for token in forbidden:
        if token in qqq_source:
            failures.append(f"QQQ100 execution block must not use forbidden/generalized token: {token}")

    normal_source = function_block(bot_source, "def run_bot(", "def run_paper_order_test(")
    manual_source = function_block(bot_source, "def run_paper_order_test(", "def run_execute_qqq100_paper(")
    slow_source = function_block(bot_source, "def run_slow_sma_paper_execution(", "def validate_slow_sma_execution_safety(")
    if "run_execute_qqq100_paper" in normal_source:
        failures.append("normal bot path must not call the QQQ100 paper command")
    if "run_execute_qqq100_paper" in manual_source:
        failures.append("manual paper-order smoke test path must not call the QQQ100 paper command")
    if "run_execute_qqq100_paper" in slow_source:
        failures.append("slow-SMA paper path must not call the QQQ100 paper command")


def verify_helper_safety(helper_source: str, failures: list[str]) -> None:
    required = [
        'STRATEGY_NAME = "qqq_100_trend_gate"',
        'TICKER = "QQQ"',
        'FIXED_QUANTITY = Decimal("1")',
        'SAVED_SIGNAL_PATH = Path("data/qqq100_preview_signal_pack.csv")',
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "orders_created",
        "orders_submitted",
        "orders_cancelled",
    ]
    for token in required:
        if token not in helper_source:
            failures.append(f"QQQ100 helper missing safety/schema token: {token}")
    forbidden = [
        "TradingClient",
        "submit_order",
        "get_all_positions",
        "get_orders",
        "insert_trade_log",
        "send_discord_alert",
        "load_config",
        "api_key",
        "secret_key",
        "webhook",
        "account_id",
    ]
    for token in forbidden:
        if token in helper_source:
            failures.append(f"pure QQQ100 helper must not contain broker/secret/runtime token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    ignored = read_text(ROOT / ".gitignore")
    for path in [RESULT_PATH, SUMMARY_PATH, Path("data/qqq100_paper_execution_blockers.csv")]:
        if not is_ignored_by_data_glob(path, ignored):
            failures.append(f"generated output should remain ignored: {path}")


def verify_no_secrets_or_forbidden_wiring(bot_source: str, helper_source: str, failures: list[str]) -> None:
    combined = bot_source + "\n" + helper_source
    qqq_source = function_block(bot_source, "def run_execute_qqq100_paper(", "def manual_paper_order_execution_eligibility_blocked(")
    for token in [
        "paper-order-test AAPL",
        "execute_slow_sma_paper",
        "--paper-order-test AAPL buy 1",
        "insert_trade_log(",
        "send_discord_alert(",
    ]:
        if token in qqq_source:
            failures.append(f"QQQ100 command must not invoke forbidden runtime command: {token}")
    for token in ["order_id {order_id}", "account_id", "webhook_url"]:
        if token in qqq_source:
            failures.append(f"QQQ100 command must not print or expose secret/order identifier token: {token}")
    if qqq_source.count("write_qqq100_paper_execution_report(") < 5:
        failures.append("QQQ100 command should write result/summary/blocker CSVs on blocked, skipped, submitted, and error paths")
    if combined.count("--execute-qqq100-paper") < 1:
        failures.append("command should be visible to static command inventory")


def recent_order_pass() -> ManualSmokeTestRecentOrderMatch:
    return ManualSmokeTestRecentOrderMatch(
        duplicate_recent_order_check="pass",
        duplicate_recent_order_source="alpaca_paper_recent_orders",
        duplicate_recent_order_status_if_any="none",
        recent_order_match_found=False,
        recent_order_match_status="none",
        recent_order_match_submitted_at_or_created_at="",
        recent_order_match_age_minutes="",
        recent_order_match_source="alpaca_paper_recent_orders",
        recent_order_match_count=0,
        recent_order_match_lookback_minutes=120,
        recent_order_match_time_field_used="none",
    )


def recent_order_blocked() -> ManualSmokeTestRecentOrderMatch:
    return ManualSmokeTestRecentOrderMatch(
        duplicate_recent_order_check="blocked_recent_matching_order_exists",
        duplicate_recent_order_source="alpaca_paper_recent_orders",
        duplicate_recent_order_status_if_any="filled",
        recent_order_match_found=True,
        recent_order_match_status="filled",
        recent_order_match_submitted_at_or_created_at="2026-06-16T09:00:00+00:00",
        recent_order_match_age_minutes="10.0",
        recent_order_match_source="alpaca_paper_recent_orders",
        recent_order_match_count=1,
        recent_order_match_lookback_minutes=120,
        recent_order_match_time_field_used="submitted_at",
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def function_block(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index == -1:
        return ""
    end_index = source.find(end, start_index + len(start))
    if end_index == -1:
        return source[start_index:]
    return source[start_index:end_index]


def is_ignored_by_data_glob(path: Path, gitignore: str) -> bool:
    normalized = str(path).replace("\\", "/")
    return normalized.startswith("data/") and "data/*" in gitignore


if __name__ == "__main__":
    raise SystemExit(main())
