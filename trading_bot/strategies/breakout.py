"""Pure helpers for a research-only 52-week high breakout strategy.

This module does not download data, read config files, submit orders, write
files, or send alerts. It is not wired into existing runtime commands.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from trading_bot.research.costs import CostModel, adjusted_buy_fill_price, adjusted_sell_fill_price


OHLCVRow = dict[str, Any]


@dataclass(frozen=True)
class BreakoutTradeEvent:
    """One synthetic research-only breakout entry or exit event."""

    index: int
    action: str
    price: float
    quantity: float
    reason: str


@dataclass(frozen=True)
class BreakoutSimulationResult:
    """Synthetic long-only breakout simulation output."""

    final_cash: float
    final_position_qty: float
    highest_close_since_entry: float
    events: list[BreakoutTradeEvent]


def _value(row: OHLCVRow, key: str) -> float:
    return float(row[key])


def _window(rows: Sequence[OHLCVRow], length: int) -> Sequence[OHLCVRow]:
    if length <= 0:
        raise ValueError("Window length must be positive.")
    if len(rows) < length:
        raise ValueError(f"Need at least {length} rows.")
    return rows[-length:]


def rolling_high(rows: Sequence[OHLCVRow], window: int = 252, price_key: str = "close") -> float:
    """Return the highest price in the trailing window, including the latest row."""
    return max(_value(row, price_key) for row in _window(rows, window))


def is_252_day_high_breakout(rows: Sequence[OHLCVRow], price_key: str = "close") -> bool:
    """Return true when the latest close reaches the trailing 252-day high."""
    latest_close = _value(rows[-1], price_key)
    return latest_close >= rolling_high(rows, 252, price_key)


def average_volume(rows: Sequence[OHLCVRow], window: int = 20, volume_key: str = "volume") -> float:
    """Return the simple average volume over the trailing window."""
    values = [_value(row, volume_key) for row in _window(rows, window)]
    return sum(values) / len(values)


def volume_confirmation(
    rows: Sequence[OHLCVRow],
    window: int = 20,
    multiplier: float = 1.0,
    volume_key: str = "volume",
) -> bool:
    """Return true when latest volume is at least average volume times multiplier."""
    latest_volume = _value(rows[-1], volume_key)
    return latest_volume >= average_volume(rows, window, volume_key) * multiplier


def simple_moving_average(rows: Sequence[OHLCVRow], window: int, price_key: str = "close") -> float:
    """Return the simple moving average for the trailing window."""
    values = [_value(row, price_key) for row in _window(rows, window)]
    return sum(values) / len(values)


def sma_100_exit(rows: Sequence[OHLCVRow], price_key: str = "close") -> bool:
    """Return true when the latest close is below the trailing 100-day SMA."""
    latest_close = _value(rows[-1], price_key)
    return latest_close < simple_moving_average(rows, 100, price_key)


def true_range(current: OHLCVRow, previous: OHLCVRow | None = None) -> float:
    """Return true range for one daily OHLC row."""
    high = _value(current, "high")
    low = _value(current, "low")
    if previous is None:
        return high - low

    previous_close = _value(previous, "close")
    return max(
        high - low,
        abs(high - previous_close),
        abs(low - previous_close),
    )


def average_true_range(rows: Sequence[OHLCVRow], window: int = 20) -> float:
    """Return simple ATR over the trailing window."""
    _window(rows, window)
    start_index = len(rows) - window
    ranges = [
        true_range(rows[index], rows[index - 1] if index > 0 else None)
        for index in range(start_index, len(rows))
    ]
    return sum(ranges) / len(ranges)


def trailing_stop_price(highest_close_since_entry: float, atr_value: float, atr_multiple: float = 2.0) -> float:
    """Return a 2 ATR trailing-stop level by default."""
    return float(highest_close_since_entry) - (float(atr_value) * float(atr_multiple))


def atr_trailing_stop_exit(
    rows: Sequence[OHLCVRow],
    highest_close_since_entry: float,
    atr_window: int = 20,
    atr_multiple: float = 2.0,
    price_key: str = "close",
) -> bool:
    """Return true when latest close is at or below the ATR trailing stop."""
    latest_close = _value(rows[-1], price_key)
    stop_price = trailing_stop_price(
        highest_close_since_entry,
        average_true_range(rows, atr_window),
        atr_multiple,
    )
    return latest_close <= stop_price


def adjusted_breakout_buy_fill(raw_price: float, cost_model: CostModel | None = None) -> float:
    """Return a synthetic research buy fill, optionally adjusted by CostModel."""
    if cost_model is None:
        return float(raw_price)
    return float(adjusted_buy_fill_price(raw_price, cost_model))


def adjusted_breakout_sell_fill(raw_price: float, cost_model: CostModel | None = None) -> float:
    """Return a synthetic research sell fill, optionally adjusted by CostModel."""
    if cost_model is None:
        return float(raw_price)
    return float(adjusted_sell_fill_price(raw_price, cost_model))


def simulate_52_week_high_breakout(
    rows: Sequence[OHLCVRow],
    starting_cash: float = 10000.0,
    cost_model: CostModel | None = None,
    require_volume_confirmation: bool = True,
    volume_multiplier: float = 1.0,
    use_sma_exit: bool = True,
    use_atr_trailing_stop: bool = True,
) -> BreakoutSimulationResult:
    """Run a simple in-memory long-only breakout simulation.

    This helper is for no-network research verification only. It does not place
    orders, write files, read config, or connect to any external service.
    """
    cash = float(starting_cash)
    quantity = 0.0
    highest_close_since_entry = 0.0
    events: list[BreakoutTradeEvent] = []

    for index in range(len(rows)):
        history = rows[: index + 1]
        latest_close = _value(history[-1], "close")
        entered_today = False

        if quantity <= 0 and len(history) >= 252 and is_252_day_high_breakout(history):
            volume_ok = (
                volume_confirmation(history, multiplier=volume_multiplier)
                if require_volume_confirmation
                else True
            )
            if volume_ok:
                fill_price = adjusted_breakout_buy_fill(latest_close, cost_model)
                if fill_price > 0 and cash > 0:
                    quantity = cash / fill_price
                    cash = 0.0
                    highest_close_since_entry = latest_close
                    entered_today = True
                    events.append(
                        BreakoutTradeEvent(
                            index=index,
                            action="buy",
                            price=fill_price,
                            quantity=quantity,
                            reason="252_day_high_breakout",
                        )
                    )

        if quantity > 0:
            highest_close_since_entry = max(highest_close_since_entry, latest_close)

        # No pyramiding: while long, a fresh breakout is ignored. Exits are
        # evaluated after entry days so a trade cannot enter and exit at once.
        if quantity > 0 and not entered_today:
            exit_reason = ""
            if use_sma_exit and len(history) >= 100 and sma_100_exit(history):
                exit_reason = "close_below_100_sma"
            elif use_atr_trailing_stop and len(history) >= 20 and atr_trailing_stop_exit(
                history,
                highest_close_since_entry,
            ):
                exit_reason = "atr_trailing_stop"

            if exit_reason:
                fill_price = adjusted_breakout_sell_fill(latest_close, cost_model)
                cash = quantity * fill_price
                events.append(
                    BreakoutTradeEvent(
                        index=index,
                        action="sell",
                        price=fill_price,
                        quantity=quantity,
                        reason=exit_reason,
                    )
                )
                quantity = 0.0

    return BreakoutSimulationResult(
        final_cash=cash,
        final_position_qty=quantity,
        highest_close_since_entry=highest_close_since_entry,
        events=events,
    )
