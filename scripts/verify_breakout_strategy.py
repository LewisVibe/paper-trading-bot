from __future__ import annotations

import sys
from pathlib import Path
from decimal import Decimal


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.strategies.breakout import (
    adjusted_breakout_buy_fill,
    adjusted_breakout_sell_fill,
    average_true_range,
    atr_trailing_stop_exit,
    is_252_day_high_breakout,
    simulate_52_week_high_breakout,
    sma_100_exit,
    trailing_stop_price,
    volume_confirmation,
)
from trading_bot.research.costs import CostModel


def make_rows(count: int, close: float = 100.0, volume: float = 1000.0) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for index in range(count):
        value = close + (index * 0.01)
        rows.append(
            {
                "open": value - 0.25,
                "high": value + 1.0,
                "low": value - 1.0,
                "close": value,
                "volume": volume,
            }
        )
    return rows


def make_flat_rows(count: int, close: float = 100.0, volume: float = 1000.0) -> list[dict[str, float]]:
    return [
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": volume,
        }
        for _ in range(count)
    ]


def main() -> int:
    failures: list[str] = []

    breakout_rows = make_rows(252)
    breakout_rows[-1]["close"] = 150.0
    if not is_252_day_high_breakout(breakout_rows):
        failures.append("breakout should be true when latest close reaches the 252-day high")

    below_high_rows = make_rows(252)
    below_high_rows[-2]["close"] = 150.0
    below_high_rows[-1]["close"] = 149.0
    if is_252_day_high_breakout(below_high_rows):
        failures.append("breakout should be false when latest close is below the 252-day high")

    volume_rows = make_rows(20, volume=1000.0)
    volume_rows[-1]["volume"] = 1500.0
    if not volume_confirmation(volume_rows, multiplier=1.2):
        failures.append("volume confirmation should pass when latest volume exceeds threshold")

    volume_rows[-1]["volume"] = 900.0
    if volume_confirmation(volume_rows, multiplier=1.2):
        failures.append("volume confirmation should fail when latest volume is below threshold")

    sma_exit_rows = make_rows(100, close=100.0)
    sma_exit_rows[-1]["close"] = 90.0
    if not sma_100_exit(sma_exit_rows):
        failures.append("100-day SMA exit should trigger below the SMA")

    atr_rows = make_rows(21, close=100.0)
    atr = average_true_range(atr_rows, 20)
    if round(atr, 4) != 2.0:
        failures.append(f"ATR should be deterministic at 2.0, got {atr!r}")

    stop = trailing_stop_price(120.0, atr, 2.0)
    if round(stop, 4) != 116.0:
        failures.append(f"trailing stop should be 116.0, got {stop!r}")

    atr_rows[-1]["close"] = 116.0
    if not atr_trailing_stop_exit(atr_rows, highest_close_since_entry=120.0):
        failures.append("ATR trailing stop should trigger at the stop price")

    atr_rows[-1]["close"] = 117.0
    if atr_trailing_stop_exit(atr_rows, highest_close_since_entry=120.0):
        failures.append("ATR trailing stop should not trigger above the stop price")

    no_entry_rows = make_flat_rows(252, close=100.0)
    no_entry_rows[-2]["close"] = 130.0
    no_entry_rows[-1]["close"] = 120.0
    no_entry_result = simulate_52_week_high_breakout(no_entry_rows)
    if no_entry_result.events:
        failures.append("synthetic simulator should not enter before a valid 252-day breakout")

    entry_rows = make_flat_rows(252, close=100.0)
    entry_rows[-1]["close"] = 130.0
    entry_result = simulate_52_week_high_breakout(entry_rows)
    buy_events = [event for event in entry_result.events if event.action == "buy"]
    if len(buy_events) != 1:
        failures.append(f"breakout simulator should create one entry, got {len(buy_events)}")

    blocked_volume_rows = make_flat_rows(252, close=100.0, volume=1000.0)
    blocked_volume_rows[-1]["close"] = 130.0
    blocked_volume_rows[-1]["volume"] = 500.0
    blocked_volume_result = simulate_52_week_high_breakout(
        blocked_volume_rows,
        volume_multiplier=1.2,
    )
    if blocked_volume_result.events:
        failures.append("volume confirmation should block synthetic breakout entry")

    sma_sim_rows = make_flat_rows(252, close=100.0)
    sma_sim_rows[-1]["close"] = 130.0
    sma_sim_rows.extend(make_flat_rows(99, close=130.0))
    sma_sim_rows.append(
        {
            "open": 90.0,
            "high": 91.0,
            "low": 89.0,
            "close": 90.0,
            "volume": 1000.0,
        }
    )
    sma_exit_result = simulate_52_week_high_breakout(
        sma_sim_rows,
        use_atr_trailing_stop=False,
    )
    if not any(event.action == "sell" and event.reason == "close_below_100_sma" for event in sma_exit_result.events):
        failures.append("100-day SMA exit should close the synthetic position")

    atr_sim_rows = make_flat_rows(252, close=100.0)
    atr_sim_rows[-1]["close"] = 130.0
    atr_sim_rows.extend(make_flat_rows(20, close=130.0))
    atr_sim_rows.append(
        {
            "open": 125.0,
            "high": 126.0,
            "low": 124.0,
            "close": 125.0,
            "volume": 1000.0,
        }
    )
    atr_exit_result = simulate_52_week_high_breakout(
        atr_sim_rows,
        use_sma_exit=False,
    )
    if not any(event.action == "sell" and event.reason == "atr_trailing_stop" for event in atr_exit_result.events):
        failures.append("ATR trailing stop should close the synthetic position")

    pyramid_rows = make_flat_rows(252, close=100.0)
    pyramid_rows[-1]["close"] = 130.0
    pyramid_rows.extend(make_flat_rows(5, close=140.0))
    pyramid_result = simulate_52_week_high_breakout(
        pyramid_rows,
        use_sma_exit=False,
        use_atr_trailing_stop=False,
    )
    pyramid_buys = [event for event in pyramid_result.events if event.action == "buy"]
    if len(pyramid_buys) != 1:
        failures.append(f"no pyramiding expected one buy, got {len(pyramid_buys)}")

    cost_model = CostModel(slippage_bps=Decimal("100"))
    buy_fill = adjusted_breakout_buy_fill(100.0, cost_model)
    sell_fill = adjusted_breakout_sell_fill(100.0, cost_model)
    if round(buy_fill, 4) != 101.0:
        failures.append(f"cost-adjusted buy fill should be 101.0, got {buy_fill!r}")
    if round(sell_fill, 4) != 99.0:
        failures.append(f"cost-adjusted sell fill should be 99.0, got {sell_fill!r}")

    if failures:
        print("Breakout strategy verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Breakout strategy verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
