from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.positions import Position  # noqa: E402
from trading_bot.safety.manual_paper_smoke_test_gate import ManualSmokeTestRecentOrderMatch  # noqa: E402
from trading_bot.safety.qqq100_paper_execution import (  # noqa: E402
    STRATEGY_NAME,
    TICKER,
    Qqq100SavedSignal,
    evaluate_qqq100_paper_execution_preflight,
    qqq100_alignment_action,
)


def main() -> int:
    failures: list[str] = []
    verify_alignment_cases(failures)
    verify_preflight_blocks_excess_and_fractional_positions(failures)
    verify_docs_record_exact_boundary(failures)
    verify_source_does_not_auto_reduce_or_sell_all(failures)

    if failures:
        print("QQQ100 exact alignment verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 exact alignment verification passed.")
    print("Verified exact zero/one-share QQQ100 alignment and manual-review blocks for excess positions.")
    return 0


def verify_alignment_cases(failures: list[str]) -> None:
    cases = [
        ("long", "0", "buy_1", "buy"),
        ("long", "1", "hold_already_long", ""),
        ("long", "2", "blocked_excess_long_position", ""),
        ("flat", "0", "hold_flat", ""),
        ("flat", "1", "sell_1", "sell"),
        ("flat", "2", "blocked_excess_long_position", ""),
    ]
    for desired_position, quantity, expected_action, expected_side in cases:
        action, side = qqq100_alignment_action(desired_position, Position(Decimal(quantity)))
        if action != expected_action or side != expected_side:
            failures.append(
                f"{desired_position=} with QQQ quantity {quantity} returned {(action, side)}, "
                f"expected {(expected_action, expected_side)}"
            )


def verify_preflight_blocks_excess_and_fractional_positions(failures: list[str]) -> None:
    for desired_position, quantity, expected_action in [
        ("long", "2", "blocked_excess_long_position"),
        ("flat", "2", "blocked_excess_long_position"),
        ("long", "0.5", "blocked_non_one_share_long_position"),
        ("flat", "0.5", "blocked_non_one_share_long_position"),
    ]:
        decision = evaluate_qqq100_paper_execution_preflight(
            confirm_qqq100_paper=True,
            alpaca_paper=True,
            allow_shorting=False,
            credentials_present=True,
            market_status="open",
            signal=Qqq100SavedSignal(True, STRATEGY_NAME, TICKER, desired_position, "2026-06-15", "ok", ""),
            current_position=Position(Decimal(quantity)),
            position_readable=True,
            open_order_count=0,
            recent_order_match=recent_order_pass(),
        )
        if decision.allowed:
            failures.append(f"{desired_position=} with QQQ quantity {quantity} should block.")
        if decision.intended_action != expected_action:
            failures.append(
                f"{desired_position=} with QQQ quantity {quantity} returned {decision.intended_action}, "
                f"expected {expected_action}."
            )
        if decision.quantity != "0":
            failures.append(f"Blocked QQQ100 alignment for quantity {quantity} should not carry order quantity.")
        if decision.strategy_execution_approved or decision.qqq100_one_share_alignment_approved:
            failures.append(f"Blocked QQQ100 alignment for quantity {quantity} should not approve strategy execution.")
        if decision.execution_approved or decision.paper_execution_approved or decision.scheduling_approved:
            failures.append("General execution, paper execution, and scheduling approvals must remain false.")


def verify_docs_record_exact_boundary(failures: list[str]) -> None:
    docs = "\n".join(
        read_text(path)
        for path in [
            "README.md",
            "docs/CURRENT_STATE.md",
            "docs/CODEX_WORKFLOW.md",
            "docs/HERMES_TASK_BOARD.md",
            "docs/PAPER_LIVE_CHECKLIST.md",
        ]
    )
    required = [
        "exactly one QQQ",
        "more than one QQQ",
        "block/manual review",
        "must not be scheduled",
    ]
    for token in required:
        if token not in docs:
            failures.append(f"Documentation missing exact QQQ100 alignment token: {token}")


def verify_source_does_not_auto_reduce_or_sell_all(failures: list[str]) -> None:
    helper_source = read_text("trading_bot/safety/qqq100_paper_execution.py")
    for token in ["reduce_to_one", "sell_all", "close_all"]:
        if token in helper_source:
            failures.append(f"QQQ100 helper should not auto-reduce or sell-all in this step: {token}")
    for token in [
        "blocked_excess_long_position",
        "blocked_non_one_share_long_position",
        "current_position.abs_quantity == FIXED_QUANTITY",
    ]:
        if token not in helper_source:
            failures.append(f"QQQ100 helper missing exact alignment source token: {token}")


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


def read_text(path: str) -> str:
    full_path = ROOT / path
    if not full_path.exists():
        return ""
    return full_path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
