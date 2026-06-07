from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.strategies.adaptive import (
    adaptive_momentum_score,
    select_adaptive_momentum_assets,
)
from trading_bot.strategies.rotation import (
    buy_and_hold_equity_curve,
    should_skip_rebalance_trade,
)


def trending_prices(start: float, daily_step: float, days: int = 260) -> list[float]:
    return [start + (daily_step * index) for index in range(days)]


def choppy_prices(start: float, daily_step: float, noise: float, days: int = 260) -> list[float]:
    prices: list[float] = []
    for index in range(days):
        direction = 1 if index % 2 == 0 else -1
        prices.append(start + (daily_step * index) + (direction * noise))
    return prices


def main() -> int:
    failures: list[str] = []

    spy_ok = trending_prices(100.0, 0.20)
    strong = trending_prices(50.0, 0.40)
    weak = trending_prices(50.0, 0.10)
    selections = select_adaptive_momentum_assets(
        {"STRONG": strong, "WEAK": weak},
        {},
        spy_ok,
        top_n=2,
    )
    if [selection.ticker for selection in selections] != ["STRONG", "WEAK"]:
        failures.append(f"stronger risk asset should rank first, got {[selection.ticker for selection in selections]!r}")

    smooth = trending_prices(50.0, 0.20)
    volatile = choppy_prices(50.0, 0.20, 4.0)
    if adaptive_momentum_score(volatile) >= adaptive_momentum_score(smooth):
        failures.append("volatility penalty should lower the choppy asset ranking")

    below_trend = trending_prices(50.0, 0.20)
    below_trend[-1] = 40.0
    filtered = select_adaptive_momentum_assets(
        {"WEAK_TREND": below_trend, "STRONG": strong},
        {},
        spy_ok,
        top_n=3,
    )
    if "WEAK_TREND" in [selection.ticker for selection in filtered]:
        failures.append("absolute trend filter should exclude weak assets")

    spy_bad = trending_prices(100.0, 0.10)
    spy_bad[-1] = 70.0
    defensive = trending_prices(80.0, 0.15)
    bad_regime = select_adaptive_momentum_assets(
        {"STRONG": strong},
        {"DEF": defensive},
        spy_bad,
        top_n=2,
    )
    if [selection.ticker for selection in bad_regime] != ["DEF"]:
        failures.append(f"bad SPY regime should select defensive assets, got {[selection.ticker for selection in bad_regime]!r}")
    if any(selection.sleeve != "defensive" for selection in bad_regime):
        failures.append("bad regime selections should be marked defensive")

    duplicate_check = select_adaptive_momentum_assets(
        {"STRONG": strong},
        {},
        spy_ok,
        top_n=3,
    )
    if [selection.ticker for selection in duplicate_check] != ["STRONG"]:
        failures.append("adaptive selections should not contain duplicates")
    if any(selection.ticker.startswith("-") for selection in duplicate_check):
        failures.append("adaptive selections should be long-only with no short markers")

    if not should_skip_rebalance_trade(99.99, 100.0):
        failures.append("tiny rebalance trades below 100 should be skipped")
    if should_skip_rebalance_trade(100.0, 100.0):
        failures.append("rebalance trades at 100 should not be skipped")

    benchmark = buy_and_hold_equity_curve([100.0, 110.0, 121.0], 1000.0)
    if [round(value, 2) for value in benchmark] != [1000.0, 1100.0, 1210.0]:
        failures.append(f"benchmark metric input curve was not deterministic: {benchmark!r}")

    if failures:
        print("Adaptive strategy verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Adaptive strategy verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
