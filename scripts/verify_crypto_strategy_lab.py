from __future__ import annotations

import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto_lab as crypto_lab


FORBIDDEN_TERMS = [
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_simulated_positions",
    "decide_trade",
    "TimeInForce",
]


def synthetic_crypto_rows(start_price: float, slope: float) -> list[dict[str, object]]:
    rows = []
    for index in range(320):
        rows.append(
            {
                "date": f"2020-{(index // 28) + 1:02d}-{(index % 28) + 1:02d}",
                "close": start_price + (index * slope) + ((index % 17) * 2),
            }
        )
    return rows


def main() -> int:
    failures: list[str] = []

    price_data = {
        "BTC/USD": synthetic_crypto_rows(10_000, 35),
        "ETH/USD": synthetic_crypto_rows(500, 4),
        "LTC/USD": synthetic_crypto_rows(80, 1),
    }
    result_rows, trade_rows, iteration_rows = crypto_lab.build_crypto_strategy_lab_outputs(
        price_data,
        created_at="2026-01-01T00:00:00+00:00",
    )

    expected_strategies = {
        "crypto_buy_and_hold_baseline",
        "crypto_sma_50_200_trend",
        "crypto_buy_above_200_exit_below_200",
        "crypto_buy_above_200_with_vol_gate",
    }
    strategies = {row["strategy_name"] for row in result_rows}
    if strategies != expected_strategies:
        failures.append(f"unexpected crypto strategy set: {sorted(strategies)}")
    newly_added = strategies - {
        "crypto_buy_and_hold_baseline",
        "crypto_sma_50_200_trend",
        "crypto_buy_above_200_exit_below_200",
    }
    if newly_added != {"crypto_buy_above_200_with_vol_gate"}:
        failures.append(f"expected exactly one new crypto strategy, got: {sorted(newly_added)}")

    symbols = {row["symbol"] for row in result_rows}
    if symbols != {"BTC/USD", "ETH/USD", "LTC/USD"}:
        failures.append(f"unexpected symbols: {sorted(symbols)}")
    if "SOL/USD" in symbols:
        failures.append("SOL/USD should not be added")
    data_symbols = {(row["symbol"], row["data_symbol"]) for row in result_rows}
    if (
        ("BTC/USD", "BTC-USD") not in data_symbols
        or ("ETH/USD", "ETH-USD") not in data_symbols
        or ("LTC/USD", "LTC-USD") not in data_symbols
    ):
        failures.append("BTC/USD, ETH/USD, and LTC/USD yfinance-compatible mapping failed")

    periods = {row["period"] for row in result_rows}
    if periods != {"full_period", "in_sample", "out_of_sample"}:
        failures.append(f"unexpected period labels: {sorted(periods)}")

    for row in result_rows:
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"result safety flags failed for {row['strategy_name']} {row['symbol']} {row['period']}")
        if row["cost_model_name"] != "crypto_research_default_taker_spread_slippage":
            failures.append("crypto result row should use the default research cost model")
        if row["crypto_taker_fee_bps"] != 10.0 or row["crypto_spread_bps"] != 5.0 or row["crypto_slippage_bps"] != 10.0:
            failures.append("crypto result row cost assumptions are incorrect")
        if row["crypto_total_one_way_cost_bps"] != 25.0:
            failures.append("crypto one-way cost should be visible as 25 bps")
        for forbidden_key in ["shorting_enabled", "margin_enabled", "leverage_enabled"]:
            if row.get(forbidden_key) is True:
                failures.append(f"{forbidden_key} should not be enabled")

    for trade in trade_rows:
        if trade["side"] not in {"buy", "sell"}:
            failures.append(f"unexpected trade side: {trade['side']}")
        if trade["research_only"] is not True or trade["preview_only"] is not True or trade["execution_approved"] is not False:
            failures.append(f"trade safety flags failed for {trade['strategy_name']} {trade['symbol']}")
        if trade["cost_model_name"] != "crypto_research_default_taker_spread_slippage":
            failures.append("crypto trade row should include the default research cost model")
        if trade["side"] == "buy" and trade["price"] <= trade["raw_price"]:
            failures.append("crypto buy fill should be above raw price when costs are positive")
        if trade["side"] == "sell" and trade["price"] >= trade["raw_price"]:
            failures.append("crypto sell fill should be below raw price when costs are positive")

    benchmark_rows = [
        row
        for row in result_rows
        if row["strategy_name"] == "crypto_buy_and_hold_baseline" and row["period"] == "full_period"
    ]
    if len(benchmark_rows) != 3:
        failures.append("buy-and-hold benchmark should exist for BTC/USD, ETH/USD, and LTC/USD")

    if len(iteration_rows) != 5:
        failures.append("iteration log should record exactly five fixed research entries")
    for row in iteration_rows:
        if row["strategy_name"] not in expected_strategies | {"crypto_monthly_btc_eth_momentum_rotation"}:
            failures.append(f"unexpected iteration strategy: {row['strategy_name']}")
        if "tuning" not in row["result_summary"]:
            failures.append("iteration log should mention no tuning after seeing results")
    vol_gate_iteration = next(
        row for row in iteration_rows if row["strategy_name"] == "crypto_buy_above_200_with_vol_gate"
    )
    if "realized_vol_window=20" not in vol_gate_iteration["allowed_parameter_set"]:
        failures.append("vol gate iteration should record the fixed 20-day volatility window")
    if "trailing_median_window=252" not in vol_gate_iteration["allowed_parameter_set"]:
        failures.append("vol gate iteration should record the fixed 252-day median window")
    if "gate_multiplier=1.5" not in vol_gate_iteration["allowed_parameter_set"]:
        failures.append("vol gate iteration should record the fixed 1.5 multiplier")
    if "parameter search" not in vol_gate_iteration["reason_for_testing"]:
        failures.append("vol gate iteration should say this is not a parameter search")
    rotation_iteration = next(
        (row for row in iteration_rows if row["strategy_name"] == "crypto_monthly_btc_eth_momentum_rotation"),
        None,
    )
    if rotation_iteration is None:
        failures.append("iteration log should include the crypto rotation strategy")
    else:
        if "rank_return_days=126" not in rotation_iteration["allowed_parameter_set"]:
            failures.append("rotation iteration should record the fixed 126-day momentum lookback")
        if "trend_filter=SMA200" not in rotation_iteration["allowed_parameter_set"]:
            failures.append("rotation iteration should record the fixed 200-day trend filter")
        if "monthly" not in rotation_iteration["allowed_parameter_set"]:
            failures.append("rotation iteration should record monthly rebalance")
        if "parameter search" not in rotation_iteration["reason_for_testing"]:
            failures.append("rotation iteration should say this is not a parameter search")

    if crypto_lab.volatility_gate_allows_entry(0.30, 0.20) is not True:
        failures.append("volatility gate should allow entries at or below 1.5x median")
    if crypto_lab.volatility_gate_allows_entry(0.31, 0.20) is not False:
        failures.append("volatility gate should block entries above 1.5x median")
    if crypto_lab.crypto_desired_long("close_above_200_vol_gate", 110, None, 100, 0.9, 0.2, already_long=True) is not True:
        failures.append("volatility gate should not force an immediate exit once already long")

    source = inspect.getsource(crypto_lab)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto strategy lab references forbidden term: {term}")

    if failures:
        print("Crypto strategy lab verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto strategy lab verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
