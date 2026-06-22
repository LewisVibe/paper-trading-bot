from decimal import Decimal

import pytest

from trading_bot.execution import decide_trade, manual_sell_would_oversell
from trading_bot.positions import Position


@pytest.mark.parametrize(
    (
        "signal",
        "position",
        "allow_shorting",
        "expected_should_trade",
        "expected_side",
        "expected_action",
        "expected_quantity",
        "expected_after",
    ),
    [
        ("HOLD", Position(Decimal("0")), False, False, "", "", Decimal("0"), Decimal("0")),
        ("HOLD", Position(Decimal("3")), False, False, "", "", Decimal("0"), Decimal("3")),
        ("HOLD", Position(Decimal("-3")), False, False, "", "", Decimal("0"), Decimal("-3")),
        ("BUY", Position(Decimal("0")), False, True, "buy", "open_long", Decimal("5"), Decimal("5")),
        ("BUY", Position(Decimal("3")), False, False, "", "", Decimal("0"), Decimal("3")),
        ("BUY", Position(Decimal("-3")), False, False, "", "", Decimal("0"), Decimal("-3")),
        ("SELL", Position(Decimal("0")), False, False, "", "", Decimal("0"), Decimal("0")),
        ("SELL", Position(Decimal("3")), False, True, "sell", "close_long", Decimal("3"), Decimal("0")),
        ("SELL", Position(Decimal("8")), False, True, "sell", "close_long", Decimal("5"), Decimal("3")),
        ("SELL", Position(Decimal("-3")), False, False, "", "", Decimal("0"), Decimal("-3")),
        ("HOLD", Position(Decimal("0")), True, False, "", "", Decimal("0"), Decimal("0")),
        ("HOLD", Position(Decimal("3")), True, False, "", "", Decimal("0"), Decimal("3")),
        ("HOLD", Position(Decimal("-3")), True, False, "", "", Decimal("0"), Decimal("-3")),
        ("BUY", Position(Decimal("0")), True, True, "buy", "open_long", Decimal("5"), Decimal("5")),
        ("BUY", Position(Decimal("3")), True, False, "", "", Decimal("0"), Decimal("3")),
        ("BUY", Position(Decimal("-3")), True, True, "buy", "close_short", Decimal("3"), Decimal("0")),
        ("BUY", Position(Decimal("-8")), True, True, "buy", "close_short", Decimal("5"), Decimal("-3")),
        ("SELL", Position(Decimal("0")), True, True, "sell", "open_short", Decimal("5"), Decimal("-5")),
        ("SELL", Position(Decimal("3")), True, True, "sell", "close_long", Decimal("3"), Decimal("0")),
        ("SELL", Position(Decimal("8")), True, True, "sell", "close_long", Decimal("5"), Decimal("3")),
        ("SELL", Position(Decimal("-3")), True, False, "", "", Decimal("0"), Decimal("-3")),
    ],
)
def test_decide_trade_cases(
    signal,
    position,
    allow_shorting,
    expected_should_trade,
    expected_side,
    expected_action,
    expected_quantity,
    expected_after,
):
    decision = decide_trade(signal, position, allow_shorting, configured_quantity=5)

    assert decision.should_trade is expected_should_trade
    assert decision.side == expected_side
    assert decision.action == expected_action
    assert decision.trade_quantity == expected_quantity
    assert decision.position_after.quantity == expected_after


def test_decide_trade_unknown_signal_holds_position():
    position = Position(Decimal("2"))

    decision = decide_trade("WAIT", position, allow_shorting=False, configured_quantity=5)

    assert decision.should_trade is False
    assert decision.position_after == position
    assert decision.reason == "Unknown signal."


@pytest.mark.parametrize(
    ("side", "quantity", "position", "allow_shorting", "expected"),
    [
        ("sell", Decimal("2"), Position(Decimal("1")), False, True),
        ("sell", Decimal("1"), Position(Decimal("1")), False, False),
        ("sell", Decimal("1"), Position(Decimal("0")), False, True),
        ("sell", Decimal("1"), Position(Decimal("-1")), False, True),
        ("sell", Decimal("2"), Position(Decimal("1")), True, False),
        ("buy", Decimal("2"), Position(Decimal("1")), False, False),
    ],
)
def test_manual_sell_would_oversell(side, quantity, position, allow_shorting, expected):
    assert manual_sell_would_oversell(side, quantity, position, allow_shorting) is expected
