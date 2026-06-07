from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.strategies.rotation import (
    buy_and_hold_equity_curve,
    composite_momentum_score,
    equal_weight_buy_and_hold_equity_curve,
    monthly_rebalance_decision,
    select_top_momentum_etfs,
    should_skip_rebalance_trade,
)


def trending_prices(start: float, daily_step: float, days: int = 260) -> list[float]:
    return [start + (daily_step * index) for index in range(days)]


def main() -> int:
    failures: list[str] = []

    strong = trending_prices(50.0, 0.50)
    weak = trending_prices(50.0, 0.10)
    if composite_momentum_score(strong) <= composite_momentum_score(weak):
        failures.append("composite score should rank stronger ETF above weaker ETF")

    spy_ok = trending_prices(100.0, 0.20)
    below_sma = trending_prices(100.0, 0.10)
    below_sma[-1] = 80.0
    selections = select_top_momentum_etfs(
        {
            "STRONG": strong,
            "BELOW": below_sma,
        },
        spy_ok,
        top_n=2,
    )
    selected_names = [selection.ticker for selection in selections]
    if "BELOW" in selected_names:
        failures.append("ETF below its 200-day SMA should be excluded")

    spy_bad = trending_prices(100.0, 0.10)
    spy_bad[-1] = 80.0
    if select_top_momentum_etfs({"STRONG": strong}, spy_bad, top_n=1):
        failures.append("SPY regime filter should block all new positions")

    medium = trending_prices(50.0, 0.25)
    top_two = select_top_momentum_etfs(
        {
            "WEAK": weak,
            "STRONG": strong,
            "MEDIUM": medium,
        },
        spy_ok,
        top_n=2,
    )
    if [selection.ticker for selection in top_two] != ["STRONG", "MEDIUM"]:
        failures.append(f"top N selection returned {[selection.ticker for selection in top_two]!r}")

    rebalance = monthly_rebalance_decision(
        current_positions=["WEAK", "STRONG"],
        prices_by_ticker={
            "WEAK": weak,
            "STRONG": strong,
            "MEDIUM": medium,
        },
        spy_prices=spy_ok,
        top_n=2,
    )
    if rebalance.sells != ["WEAK"]:
        failures.append(f"rebalance should sell assets outside top N, got {rebalance.sells!r}")
    if rebalance.buys != ["MEDIUM"]:
        failures.append(f"rebalance should buy new top-N assets, got {rebalance.buys!r}")
    if rebalance.holds != ["STRONG"]:
        failures.append(f"rebalance should hold retained top-N assets, got {rebalance.holds!r}")
    if rebalance.target_positions != ["STRONG", "MEDIUM"]:
        failures.append(f"rebalance target positions should be top-N only, got {rebalance.target_positions!r}")

    if any(ticker.startswith("-") for ticker in rebalance.target_positions):
        failures.append("rotation output should be long-only with no short markers")

    duplicate_check = monthly_rebalance_decision(
        current_positions=["STRONG", "STRONG"],
        prices_by_ticker={"STRONG": strong},
        spy_prices=spy_ok,
        top_n=3,
    )
    if duplicate_check.target_positions != ["STRONG"]:
        failures.append(f"duplicate selections should not occur, got {duplicate_check.target_positions!r}")

    try:
        composite_momentum_score([100.0] * 100)
        failures.append("insufficient history should fail clearly")
    except ValueError as exc:
        if "Need at least" not in str(exc):
            failures.append(f"insufficient history error was unclear: {exc}")

    buy_hold_curve = buy_and_hold_equity_curve([100.0, 110.0, 120.0], 1000.0)
    if [round(value, 2) for value in buy_hold_curve] != [1000.0, 1100.0, 1200.0]:
        failures.append(f"buy-and-hold equity curve was {buy_hold_curve!r}")

    equal_weight_curve = equal_weight_buy_and_hold_equity_curve(
        {
            "A": [100.0, 110.0],
            "B": [50.0, 50.0],
        },
        1000.0,
    )
    if [round(value, 2) for value in equal_weight_curve] != [1000.0, 1050.0]:
        failures.append(f"equal-weight benchmark curve was {equal_weight_curve!r}")

    if not should_skip_rebalance_trade(0.01, 100.0):
        failures.append("ETF rotation tiny rebalance trade below 100 should be skipped")
    if should_skip_rebalance_trade(100.0, 100.0):
        failures.append("ETF rotation rebalance trade at 100 should be allowed")

    if failures:
        print("Rotation strategy verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Rotation strategy verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
