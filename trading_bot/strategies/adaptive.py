"""Pure helpers for a research-only adaptive risk-on/off momentum strategy.

The helpers use in-memory daily prices only. They do not download data, read
config files, place orders, write files, use SQLite, or send alerts.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from trading_bot.strategies.rotation import simple_moving_average


PriceSeries = Sequence[float]
PriceMap = Mapping[str, PriceSeries]

ADAPTIVE_MOMENTUM_LOOKBACKS = (63, 126, 252)
ADAPTIVE_VOLATILITY_LOOKBACK = 63
ADAPTIVE_VOLATILITY_PENALTY = 0.25
ADAPTIVE_TREND_WINDOW = 200


@dataclass(frozen=True)
class AdaptiveSelection:
    ticker: str
    score: float
    sleeve: str


def lookback_return(prices: PriceSeries, lookback_days: int) -> float:
    if len(prices) <= lookback_days:
        raise ValueError(f"Need at least {lookback_days + 1} prices.")
    previous = float(prices[-lookback_days - 1])
    latest = float(prices[-1])
    if previous <= 0:
        raise ValueError("Previous price must be positive.")
    return (latest / previous) - 1.0


def composite_adaptive_momentum(prices: PriceSeries) -> float:
    returns = [lookback_return(prices, lookback) for lookback in ADAPTIVE_MOMENTUM_LOOKBACKS]
    return sum(returns) / len(returns)


def realised_volatility(prices: PriceSeries, lookback_days: int = ADAPTIVE_VOLATILITY_LOOKBACK) -> float:
    if len(prices) <= lookback_days:
        raise ValueError(f"Need at least {lookback_days + 1} prices.")
    daily_returns: list[float] = []
    start_index = len(prices) - lookback_days
    for index in range(start_index, len(prices)):
        previous = float(prices[index - 1])
        current = float(prices[index])
        if previous > 0:
            daily_returns.append((current / previous) - 1.0)
    if len(daily_returns) < 2:
        return 0.0
    mean_return = sum(daily_returns) / len(daily_returns)
    variance = sum((value - mean_return) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
    return math.sqrt(variance) * math.sqrt(252)


def adaptive_momentum_score(
    prices: PriceSeries,
    volatility_penalty: float = ADAPTIVE_VOLATILITY_PENALTY,
) -> float:
    return composite_adaptive_momentum(prices) - (realised_volatility(prices) * volatility_penalty)


def above_trend_filter(prices: PriceSeries, window: int = ADAPTIVE_TREND_WINDOW) -> bool:
    if len(prices) < window:
        raise ValueError(f"Need at least {window} prices.")
    return float(prices[-1]) > simple_moving_average(prices, window)


def risk_regime_is_strong(spy_prices: PriceSeries) -> bool:
    return above_trend_filter(spy_prices)


def select_adaptive_momentum_assets(
    risk_prices_by_ticker: PriceMap,
    defensive_prices_by_ticker: PriceMap,
    spy_prices: PriceSeries,
    top_n: int = 3,
) -> list[AdaptiveSelection]:
    """Select risk assets in strong regimes and defensive assets in weak regimes."""
    if top_n <= 0:
        return []

    risk_on = risk_regime_is_strong(spy_prices)
    source = risk_prices_by_ticker if risk_on else defensive_prices_by_ticker
    sleeve = "risk" if risk_on else "defensive"

    candidates: list[AdaptiveSelection] = []
    for ticker, prices in source.items():
        if not above_trend_filter(prices):
            continue
        candidates.append(
            AdaptiveSelection(
                ticker=ticker,
                score=adaptive_momentum_score(prices),
                sleeve=sleeve,
            )
        )

    ranked = sorted(candidates, key=lambda item: (-item.score, item.ticker))
    seen: set[str] = set()
    selections: list[AdaptiveSelection] = []
    for candidate in ranked:
        if candidate.ticker in seen:
            continue
        seen.add(candidate.ticker)
        selections.append(candidate)
        if len(selections) >= top_n:
            break
    return selections
