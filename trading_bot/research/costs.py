"""Research-only cost model helpers.

This module is for backtesting and strategy research assumptions only.
It is connected to research output, but not to Alpaca paper execution,
live orders, or the normal bot run.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


BPS_DIVISOR = Decimal("10000")


@dataclass(frozen=True)
class CostModel:
    """Simple research cost assumptions for stock/ETF backtests.

    Crypto fee fields are present as dormant future research assumptions. The
    stock/ETF helper functions below intentionally do not use them.
    """

    commission_per_trade: Decimal = Decimal("0")
    commission_bps: Decimal = Decimal("0")
    spread_bps: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")
    crypto_maker_fee_bps: Decimal = Decimal("0")
    crypto_taker_fee_bps: Decimal = Decimal("0")


def decimal_from_number(value: int | float | str | Decimal) -> Decimal:
    return Decimal(str(value))


def calculate_notional_value(price: int | float | str | Decimal, quantity: int | float | str | Decimal) -> Decimal:
    """Return price times quantity for research cost calculations."""
    return decimal_from_number(price) * decimal_from_number(quantity)


def calculate_fixed_commission_cost(cost_model: CostModel) -> Decimal:
    """Return the per-trade fixed commission assumption."""
    return cost_model.commission_per_trade


def calculate_bps_cost(notional_value: int | float | str | Decimal, bps: int | float | str | Decimal) -> Decimal:
    """Return basis-point cost applied to a notional value."""
    return decimal_from_number(notional_value) * decimal_from_number(bps) / BPS_DIVISOR


def calculate_total_estimated_trade_cost(
    cost_model: CostModel,
    price: int | float | str | Decimal,
    quantity: int | float | str | Decimal,
) -> Decimal:
    """Estimate stock/ETF trade costs for research only.

    This combines fixed commission, commission bps, spread bps, and slippage
    bps. Dormant crypto maker/taker assumptions are intentionally ignored here.
    """
    notional = calculate_notional_value(price, quantity)
    variable_bps = cost_model.commission_bps + cost_model.spread_bps + cost_model.slippage_bps
    return calculate_fixed_commission_cost(cost_model) + calculate_bps_cost(notional, variable_bps)


def adjusted_buy_fill_price(
    raw_price: int | float | str | Decimal,
    cost_model: CostModel,
) -> Decimal:
    """Return a research buy fill price adjusted upward for spread/slippage."""
    price = decimal_from_number(raw_price)
    adjustment_bps = cost_model.spread_bps + cost_model.slippage_bps
    return price * (Decimal("1") + adjustment_bps / BPS_DIVISOR)


def adjusted_sell_fill_price(
    raw_price: int | float | str | Decimal,
    cost_model: CostModel,
) -> Decimal:
    """Return a research sell fill price adjusted downward for spread/slippage."""
    price = decimal_from_number(raw_price)
    adjustment_bps = cost_model.spread_bps + cost_model.slippage_bps
    return price * (Decimal("1") - adjustment_bps / BPS_DIVISOR)
