"""Trade-decision and action-translation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_bot.positions import (
    POSITION_FLAT,
    POSITION_LONG,
    POSITION_SHORT,
    Position,
    decimal_from_any,
)
from trading_bot.strategies.sma import SIGNAL_BUY, SIGNAL_HOLD, SIGNAL_SELL


@dataclass
class TradeDecision:
    should_trade: bool
    side: str
    action: str
    trade_quantity: Decimal
    position_after: Position
    reason: str


def decide_trade(
    signal: str,
    position_before: Position,
    allow_shorting: bool,
    configured_quantity: float,
) -> TradeDecision:
    order_quantity = decimal_from_any(configured_quantity)

    if signal == SIGNAL_HOLD:
        return TradeDecision(False, "", "", Decimal("0"), position_before, "Signal is HOLD.")

    if not allow_shorting:
        if signal == SIGNAL_BUY:
            if position_before.state == POSITION_FLAT:
                return TradeDecision(
                    True, "buy", "open_long", order_quantity, Position(order_quantity), ""
                )
            return TradeDecision(
                False,
                "",
                "",
                Decimal("0"),
                position_before,
                "Long-only mode will not add to a position.",
            )

        if signal == SIGNAL_SELL:
            if position_before.state == POSITION_LONG:
                close_quantity = min(order_quantity, position_before.abs_quantity)
                if close_quantity <= 0:
                    return TradeDecision(
                        False,
                        "",
                        "",
                        Decimal("0"),
                        position_before,
                        "Close quantity is zero; no long position can be closed.",
                    )
                position_after = Position(position_before.quantity - close_quantity)
                return TradeDecision(
                    True, "sell", "close_long", close_quantity, position_after, ""
                )
            return TradeDecision(
                False,
                "",
                "",
                Decimal("0"),
                position_before,
                "Long-only mode will not open a short position.",
            )

    if signal == SIGNAL_BUY:
        if position_before.state == POSITION_FLAT:
            return TradeDecision(
                True, "buy", "open_long", order_quantity, Position(order_quantity), ""
            )
        if position_before.state == POSITION_SHORT:
            close_quantity = min(order_quantity, position_before.abs_quantity)
            if close_quantity <= 0:
                return TradeDecision(
                    False,
                    "",
                    "",
                    Decimal("0"),
                    position_before,
                    "Close quantity is zero; no short position can be closed.",
                )
            position_after = Position(position_before.quantity + close_quantity)
            return TradeDecision(True, "buy", "close_short", close_quantity, position_after, "")
        return TradeDecision(
            False,
            "",
            "",
            Decimal("0"),
            position_before,
            "Shorting mode will not add to an existing long.",
        )

    if signal == SIGNAL_SELL:
        if position_before.state == POSITION_LONG:
            close_quantity = min(order_quantity, position_before.abs_quantity)
            if close_quantity <= 0:
                return TradeDecision(
                    False,
                    "",
                    "",
                    Decimal("0"),
                    position_before,
                    "Close quantity is zero; no long position can be closed.",
                )
            position_after = Position(position_before.quantity - close_quantity)
            return TradeDecision(True, "sell", "close_long", close_quantity, position_after, "")
        if position_before.state == POSITION_FLAT:
            return TradeDecision(
                True, "sell", "open_short", order_quantity, Position(-order_quantity), ""
            )
        return TradeDecision(
            False,
            "",
            "",
            Decimal("0"),
            position_before,
            "Shorting mode will not add to an existing short.",
        )

    return TradeDecision(False, "", "", Decimal("0"), position_before, "Unknown signal.")


def manual_sell_would_oversell(
    side: str,
    quantity: Decimal,
    position_before: Position,
    allow_shorting: bool,
) -> bool:
    if side != "sell" or allow_shorting:
        return False
    return quantity > max(position_before.quantity, Decimal("0"))
