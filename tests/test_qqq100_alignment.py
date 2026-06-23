from decimal import Decimal

import pytest

from trading_bot.positions import Position
from trading_bot.safety.manual_paper_smoke_test_gate import ManualSmokeTestRecentOrderMatch
from trading_bot.safety.qqq100_paper_execution import (
    STRATEGY_NAME,
    TICKER,
    Qqq100SavedSignal,
    evaluate_qqq100_paper_execution_preflight,
    qqq100_alignment_action,
)


@pytest.mark.parametrize(
    ("desired_position", "current_quantity", "expected_action", "expected_side"),
    [
        ("long", "0", "buy_1", "buy"),
        ("long", "1", "hold_already_long", ""),
        ("long", "2", "blocked_excess_long_position", ""),
        ("flat", "0", "hold_flat", ""),
        ("flat", "1", "sell_1", "sell"),
        ("flat", "2", "blocked_excess_long_position", ""),
    ],
)
def test_qqq100_alignment_requires_exact_zero_or_one_share(
    desired_position,
    current_quantity,
    expected_action,
    expected_side,
):
    action, side = qqq100_alignment_action(
        desired_position,
        Position(Decimal(current_quantity)),
    )

    assert action == expected_action
    assert side == expected_side


@pytest.mark.parametrize("desired_position", ["long", "flat"])
def test_qqq100_preflight_blocks_excess_long_position(desired_position):
    decision = evaluate_qqq100_paper_execution_preflight(
        confirm_qqq100_paper=True,
        alpaca_paper=True,
        allow_shorting=False,
        credentials_present=True,
        market_status="open",
        signal=Qqq100SavedSignal(True, STRATEGY_NAME, TICKER, desired_position, "2026-06-15", "ok", ""),
        current_position=Position(Decimal("2")),
        position_readable=True,
        open_order_count=0,
        recent_order_match=recent_order_pass(),
    )

    assert decision.allowed is False
    assert decision.decision_status == "qqq100_paper_execution_blocked"
    assert decision.intended_action == "blocked_excess_long_position"
    assert decision.order_side == ""
    assert decision.quantity == "0"
    assert decision.strategy_execution_approved is False
    assert decision.qqq100_one_share_alignment_approved is False
    assert decision.execution_approved is False
    assert decision.paper_execution_approved is False
    assert decision.scheduling_approved is False


@pytest.mark.parametrize("desired_position", ["long", "flat"])
def test_qqq100_preflight_blocks_fractional_long_position(desired_position):
    decision = evaluate_qqq100_paper_execution_preflight(
        confirm_qqq100_paper=True,
        alpaca_paper=True,
        allow_shorting=False,
        credentials_present=True,
        market_status="open",
        signal=Qqq100SavedSignal(True, STRATEGY_NAME, TICKER, desired_position, "2026-06-15", "ok", ""),
        current_position=Position(Decimal("0.5")),
        position_readable=True,
        open_order_count=0,
        recent_order_match=recent_order_pass(),
    )

    assert decision.allowed is False
    assert decision.intended_action == "blocked_non_one_share_long_position"
    assert decision.quantity == "0"
    assert decision.execution_approved is False
    assert decision.paper_execution_approved is False
    assert decision.scheduling_approved is False


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
