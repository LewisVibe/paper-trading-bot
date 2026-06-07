"""Simple registry for future research strategy-lab strategies.

The registry is not connected to current CLI commands yet. It exists so future
strategy candidates can be added and tested behind explicit research tooling.
"""

from __future__ import annotations

from collections.abc import Iterable

from trading_bot.strategies.base import ResearchStrategy, StaticResearchStrategy, StrategyMetadata


DEFAULT_RESEARCH_STRATEGIES: tuple[StaticResearchStrategy, ...] = (
    StaticResearchStrategy(
        StrategyMetadata(
            name="buy_and_hold_baseline",
            display_name="Buy And Hold Baseline",
            description="Benchmark that buys on the first valid trading day and sells on the final valid trading day.",
            category="benchmark",
            tags=("benchmark", "baseline"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="sma_20_50_basic",
            display_name="SMA 20/50 Basic",
            description="Long-only 20-day/50-day SMA crossover without market regime or volatility filters.",
            category="trend",
            tags=("sma", "crossover", "trend"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="sma_20_50_regime",
            display_name="SMA 20/50 Regime",
            description="Long-only 20-day/50-day SMA crossover with an SPY 200-day regime filter.",
            category="regime-filtered trend",
            tags=("sma", "crossover", "regime"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="sma_50_200_trend",
            display_name="SMA 50/200 Trend",
            description="Long-only 50-day/200-day SMA trend-following crossover benchmark.",
            category="trend",
            tags=("sma", "slow-trend"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="buy_above_200_exit_below_200",
            display_name="Buy Above 200 / Exit Below 200",
            description="Long-only price-above-200-day-SMA strategy with an SPY 200-day regime filter.",
            category="regime-filtered trend",
            tags=("sma", "regime", "price-trend"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="sma_50_200_sensitivity",
            display_name="SMA Sensitivity Family",
            description="Research family for testing nearby slow SMA trend parameter pairs.",
            category="parameter sensitivity",
            tags=("sma", "sensitivity", "research-family"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="slow_sma_trend_stress",
            display_name="Slow SMA Trend Stress",
            description="Research family for stress-testing slow SMA trend pairs across slippage assumptions.",
            category="stress test",
            tags=("sma", "stress-test", "slippage"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="fifty_two_week_high_breakout",
            display_name="52-Week High Breakout",
            description="Research-only long breakout candidate using a 252-day high, volume confirmation, and trend exits.",
            category="breakout",
            tags=("breakout", "momentum", "research-candidate"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="monthly_etf_momentum_rotation",
            display_name="Monthly ETF Momentum Rotation",
            description="Research-only long ETF rotation candidate using multi-horizon momentum and trend filters.",
            category="momentum rotation",
            tags=("etf", "momentum", "rotation", "research-candidate"),
        )
    ),
    StaticResearchStrategy(
        StrategyMetadata(
            name="adaptive_risk_on_off_momentum",
            display_name="Adaptive Risk-On/Off Momentum",
            description="Research-only ETF strategy that rotates between volatility-penalised risk momentum and defensive assets.",
            category="adaptive momentum",
            tags=("etf", "momentum", "defensive", "research-candidate"),
        )
    ),
)


class StrategyRegistry:
    """In-memory registry keyed by each strategy's metadata name."""

    def __init__(self) -> None:
        self._strategies: dict[str, ResearchStrategy] = {}

    def register(self, strategy: ResearchStrategy) -> None:
        name = strategy.metadata.name
        if not name:
            raise ValueError("Strategy name cannot be blank.")
        if name in self._strategies:
            raise ValueError(f"Strategy already registered: {name}")
        self._strategies[name] = strategy

    def get(self, name: str) -> ResearchStrategy:
        try:
            return self._strategies[name]
        except KeyError as exc:
            raise KeyError(f"Strategy is not registered: {name}") from exc

    def list_names(self) -> list[str]:
        return sorted(self._strategies)

    def list_strategies(self) -> list[ResearchStrategy]:
        return [self._strategies[name] for name in self.list_names()]


def register_strategy(registry: StrategyRegistry, strategy: ResearchStrategy) -> None:
    registry.register(strategy)


def get_strategy(registry: StrategyRegistry, name: str) -> ResearchStrategy:
    return registry.get(name)


def list_registered_strategies(registry: StrategyRegistry) -> list[ResearchStrategy]:
    return registry.list_strategies()


def build_strategy_registry(strategies: Iterable[ResearchStrategy] | None = None) -> StrategyRegistry:
    registry = StrategyRegistry()
    for strategy in strategies or []:
        registry.register(strategy)
    return registry


def build_default_strategy_registry() -> StrategyRegistry:
    return build_strategy_registry(DEFAULT_RESEARCH_STRATEGIES)


def default_strategy_names() -> list[str]:
    return build_default_strategy_registry().list_names()
