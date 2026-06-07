"""Read-only position models, reconstruction, and position math."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


POSITION_FLAT = "flat"
POSITION_LONG = "long"
POSITION_SHORT = "short"


def format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")


@dataclass
class Position:
    # Positive quantity means long, negative means short, and zero means flat.
    # Keeping the quantity here prevents close orders from being larger than the position.
    quantity: Decimal = Decimal("0")

    @property
    def state(self) -> str:
        if self.quantity > 0:
            return POSITION_LONG
        if self.quantity < 0:
            return POSITION_SHORT
        return POSITION_FLAT

    @property
    def abs_quantity(self) -> Decimal:
        return abs(self.quantity)

    def label(self) -> str:
        return f"{self.state} {format_decimal(self.abs_quantity)}"


def decimal_from_any(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def get_simulated_positions(conn: sqlite3.Connection) -> dict[str, Position]:
    net_quantities: dict[str, Decimal] = {}
    rows = conn.execute(
        """
        SELECT ticker, action, quantity
        FROM trade_log
        WHERE action != ''
          AND error = ''
          AND order_status IN ('dry_run', 'filled')
        ORDER BY id
        """
    ).fetchall()

    for ticker, action, quantity in rows:
        # Dry-run positions are rebuilt from the trade log: buys add shares,
        # sells subtract shares, and the final signed quantity gives the state.
        trade_quantity = decimal_from_any(quantity)
        current_quantity = net_quantities.get(ticker, Decimal("0"))
        if action == "open_long":
            current_quantity += trade_quantity
        elif action == "close_long":
            current_quantity -= trade_quantity
        elif action == "open_short":
            current_quantity -= trade_quantity
        elif action == "close_short":
            current_quantity += trade_quantity
        net_quantities[ticker] = current_quantity

    return {ticker: Position(quantity) for ticker, quantity in net_quantities.items()}


def get_alpaca_positions(client: Any) -> dict[str, Position]:
    positions: dict[str, Position] = {}
    for position in client.get_all_positions():
        symbol = str(getattr(position, "symbol", "")).upper()
        if not symbol:
            continue

        side = str(getattr(position, "side", "")).lower()
        qty = decimal_from_any(getattr(position, "qty", "0"))

        if side == "short":
            positions[symbol] = Position(-abs(qty))
        elif side == "long":
            positions[symbol] = Position(abs(qty))
        elif qty < 0:
            positions[symbol] = Position(qty)
        elif qty > 0:
            positions[symbol] = Position(qty)
        else:
            positions[symbol] = Position()

    return positions
