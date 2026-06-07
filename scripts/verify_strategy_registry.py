from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.strategies.base import StaticResearchStrategy, StrategyMetadata
from trading_bot.strategies.registry import (
    DEFAULT_RESEARCH_STRATEGIES,
    StrategyRegistry,
    build_default_strategy_registry,
    build_strategy_registry,
    default_strategy_names,
    get_strategy,
    list_registered_strategies,
    register_strategy,
)


EXPECTED_DEFAULT_NAMES = [
    "adaptive_risk_on_off_momentum",
    "buy_above_200_exit_below_200",
    "buy_and_hold_baseline",
    "fifty_two_week_high_breakout",
    "monthly_etf_momentum_rotation",
    "slow_sma_trend_stress",
    "sma_20_50_basic",
    "sma_20_50_regime",
    "sma_50_200_sensitivity",
    "sma_50_200_trend",
]


def main() -> int:
    failures: list[str] = []

    baseline = StaticResearchStrategy(
        StrategyMetadata(
            name="example_baseline",
            display_name="Example Baseline",
            description="Test-only registry strategy.",
            tags=("test",),
        )
    )
    trend = StaticResearchStrategy(
        StrategyMetadata(
            name="example_trend",
            display_name="Example Trend",
        )
    )

    registry = StrategyRegistry()
    register_strategy(registry, trend)
    register_strategy(registry, baseline)

    if registry.list_names() != ["example_baseline", "example_trend"]:
        failures.append(f"list_names returned {registry.list_names()!r}")

    if get_strategy(registry, "example_baseline") is not baseline:
        failures.append("get_strategy did not return the registered baseline strategy")

    listed = list_registered_strategies(registry)
    if [strategy.metadata.name for strategy in listed] != ["example_baseline", "example_trend"]:
        failures.append("list_registered_strategies did not return strategies sorted by name")

    try:
        register_strategy(registry, baseline)
        failures.append("duplicate registration did not fail")
    except ValueError:
        pass

    try:
        get_strategy(registry, "missing")
        failures.append("missing strategy lookup did not fail")
    except KeyError:
        pass

    built = build_strategy_registry([baseline])
    if built.get("example_baseline") is not baseline:
        failures.append("build_strategy_registry did not register supplied strategies")

    default_registry = build_default_strategy_registry()
    if default_registry.list_names() != EXPECTED_DEFAULT_NAMES:
        failures.append(f"default strategy names were {default_registry.list_names()!r}")

    if default_strategy_names() != EXPECTED_DEFAULT_NAMES:
        failures.append(f"default_strategy_names returned {default_strategy_names()!r}")

    if len(DEFAULT_RESEARCH_STRATEGIES) != len(EXPECTED_DEFAULT_NAMES):
        failures.append("DEFAULT_RESEARCH_STRATEGIES length does not match expected names")

    for strategy in default_registry.list_strategies():
        metadata = strategy.metadata
        if not metadata.name:
            failures.append("default strategy has blank name")
        if not metadata.description:
            failures.append(f"{metadata.name} has blank description")
        if not metadata.category:
            failures.append(f"{metadata.name} has blank category")
        if metadata.default_timeframe != "daily":
            failures.append(f"{metadata.name} default_timeframe is {metadata.default_timeframe!r}")
        if metadata.long_only is not True:
            failures.append(f"{metadata.name} is not marked long-only")
        if metadata.research_only is not True:
            failures.append(f"{metadata.name} is not marked research-only")

    if failures:
        print("Strategy-registry verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Strategy-registry verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
