"""Pure helpers for a research-only monthly ETF momentum rotation strategy.

This module uses in-memory daily price data only. It does not download data,
read config files, place orders, write files, use SQLite, or send alerts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


PriceSeries = Sequence[float]
PriceMap = Mapping[str, PriceSeries]


@dataclass(frozen=True)
class RotationSelection:
    """One selected ETF and its research momentum score."""

    ticker: str
    score: float


@dataclass(frozen=True)
class RotationRebalanceDecision:
    """Synthetic long-only monthly rebalance decision."""

    target_positions: list[str]
    buys: list[str]
    sells: list[str]
    holds: list[str]


def _require_history(prices: PriceSeries, lookback_days: int) -> None:
    if lookback_days <= 0:
        raise ValueError("Lookback days must be positive.")
    if len(prices) <= lookback_days:
        raise ValueError(f"Need at least {lookback_days + 1} prices.")


def lookback_return(prices: PriceSeries, lookback_days: int) -> float:
    """Return percentage return over a lookback window, as a decimal."""
    _require_history(prices, lookback_days)
    previous_price = float(prices[-lookback_days - 1])
    latest_price = float(prices[-1])
    if previous_price <= 0:
        raise ValueError("Previous price must be positive.")
    return (latest_price / previous_price) - 1.0


def return_21_day(prices: PriceSeries) -> float:
    return lookback_return(prices, 21)


def return_63_day(prices: PriceSeries) -> float:
    return lookback_return(prices, 63)


def return_126_day(prices: PriceSeries) -> float:
    return lookback_return(prices, 126)


def return_252_day(prices: PriceSeries) -> float:
    return lookback_return(prices, 252)


def composite_momentum_score(prices: PriceSeries) -> float:
    """Return the average of 21, 63, 126, and 252-day returns."""
    returns = [
        return_21_day(prices),
        return_63_day(prices),
        return_126_day(prices),
        return_252_day(prices),
    ]
    return sum(returns) / len(returns)


def simple_moving_average(prices: PriceSeries, window: int) -> float:
    if len(prices) < window:
        raise ValueError(f"Need at least {window} prices.")
    values = [float(price) for price in prices[-window:]]
    return sum(values) / len(values)


def above_200_day_sma(prices: PriceSeries) -> bool:
    """Return true when the latest price is above its 200-day SMA."""
    return float(prices[-1]) > simple_moving_average(prices, 200)


def spy_regime_allows_new_positions(spy_prices: PriceSeries) -> bool:
    """Return true when SPY is above its 200-day SMA."""
    return above_200_day_sma(spy_prices)


def select_top_momentum_etfs(
    prices_by_ticker: PriceMap,
    spy_prices: PriceSeries,
    top_n: int = 3,
) -> list[RotationSelection]:
    """Return top-N eligible ETFs by composite momentum score.

    Eligibility requires the SPY regime filter to be positive and each ETF to
    be above its own 200-day SMA. The function is long-only and returns unique
    ticker selections.
    """
    if top_n <= 0:
        return []
    if not spy_regime_allows_new_positions(spy_prices):
        return []

    selections: list[RotationSelection] = []
    for ticker, prices in prices_by_ticker.items():
        if not above_200_day_sma(prices):
            continue
        selections.append(
            RotationSelection(
                ticker=ticker,
                score=composite_momentum_score(prices),
            )
        )

    ranked = sorted(selections, key=lambda item: (-item.score, item.ticker))
    seen: set[str] = set()
    unique: list[RotationSelection] = []
    for selection in ranked:
        if selection.ticker in seen:
            continue
        seen.add(selection.ticker)
        unique.append(selection)
        if len(unique) >= top_n:
            break
    return unique


def monthly_rebalance_decision(
    current_positions: Sequence[str],
    prices_by_ticker: PriceMap,
    spy_prices: PriceSeries,
    top_n: int = 3,
) -> RotationRebalanceDecision:
    """Return a synthetic target-position rebalance decision.

    This returns names only. It never submits orders and never opens shorts.
    """
    target_positions = [selection.ticker for selection in select_top_momentum_etfs(prices_by_ticker, spy_prices, top_n)]
    current_unique = sorted(set(current_positions))
    target_set = set(target_positions)
    current_set = set(current_unique)

    return RotationRebalanceDecision(
        target_positions=target_positions,
        buys=sorted(target_set - current_set),
        sells=sorted(current_set - target_set),
        holds=sorted(current_set & target_set),
    )


def buy_and_hold_equity_curve(prices: PriceSeries, starting_equity: float = 10000.0) -> list[float]:
    """Return an equity curve for buying the first price and holding."""
    if not prices:
        raise ValueError("Need at least one price.")
    first_price = float(prices[0])
    if first_price <= 0:
        raise ValueError("First price must be positive.")
    shares = float(starting_equity) / first_price
    return [shares * float(price) for price in prices]


def equal_weight_buy_and_hold_equity_curve(
    prices_by_ticker: PriceMap,
    starting_equity: float = 10000.0,
) -> list[float]:
    """Return an equal-weight buy-and-hold equity curve for aligned prices."""
    if not prices_by_ticker:
        raise ValueError("Need at least one ticker.")
    lengths = {len(prices) for prices in prices_by_ticker.values()}
    if len(lengths) != 1:
        raise ValueError("All price series must have the same length.")

    allocation = float(starting_equity) / len(prices_by_ticker)
    curves = [
        buy_and_hold_equity_curve(prices, allocation)
        for prices in prices_by_ticker.values()
    ]
    return [sum(curve[index] for curve in curves) for index in range(next(iter(lengths)))]


def should_skip_rebalance_trade(
    notional: float,
    min_rebalance_notional: float = 100.0,
) -> bool:
    """Return true for tiny partial rebalance trades that should be ignored."""
    return abs(float(notional)) < float(min_rebalance_notional)
