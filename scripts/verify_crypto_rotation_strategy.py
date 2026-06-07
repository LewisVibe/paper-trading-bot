from __future__ import annotations

import inspect
import sys
from tempfile import TemporaryDirectory
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto_lab as crypto_lab
import trading_bot.research.crypto_rotation as crypto_rotation


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


def synthetic_rows(start_price: float, slope: float, cycle: float) -> list[dict[str, object]]:
    start_date = date(2020, 1, 1)
    rows = []
    for index in range(430):
        cyclical_noise = ((index % 41) - 20) * cycle
        rows.append(
            {
                "date": (start_date + timedelta(days=index)).isoformat(),
                "close": round(start_price + (index * slope) + cyclical_noise, 4),
            }
        )
    return rows


def main() -> int:
    failures: list[str] = []

    price_data = {
        "BTC/USD": synthetic_rows(10_000, 40, 8),
        "ETH/USD": synthetic_rows(700, 7, 2),
    }
    result_rows, trade_rows = crypto_rotation.build_crypto_rotation_outputs(
        price_data,
        created_at="2026-01-01T00:00:00+00:00",
    )

    if {row["strategy_name"] for row in result_rows} != {"crypto_monthly_btc_eth_momentum_rotation"}:
        failures.append("rotation results should contain exactly the new rotation strategy")
    if "crypto_monthly_btc_eth_momentum_rotation" in set(crypto_lab.CRYPTO_STRATEGIES):
        failures.append("rotation strategy should stay separate from the existing per-symbol crypto strategy list")

    periods = {row["period"] for row in result_rows}
    if periods != {"full_period", "in_sample", "out_of_sample"}:
        failures.append(f"unexpected rotation periods: {sorted(periods)}")

    for row in result_rows:
        if row["symbol"] != "BTC_ETH_ROTATION":
            failures.append("rotation result symbol should be BTC_ETH_ROTATION")
        if row["data_symbol"] != "BTC-USD,ETH-USD":
            failures.append("rotation result data_symbol should identify BTC and ETH")
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append("rotation result safety flags failed")
        if row["crypto_total_one_way_cost_bps"] != 25.0:
            failures.append("rotation result should expose default 25 bps crypto cost assumption")
        for forbidden_key in ["shorting_enabled", "margin_enabled", "leverage_enabled"]:
            if row.get(forbidden_key) is True:
                failures.append(f"{forbidden_key} should not be enabled")

    if not trade_rows:
        failures.append("synthetic rotation data should create at least one research trade")
    for trade in trade_rows:
        if trade["strategy_name"] != "crypto_monthly_btc_eth_momentum_rotation":
            failures.append("rotation trade should use the rotation strategy name")
        if trade["side"] not in {"buy", "sell"}:
            failures.append(f"unexpected rotation trade side: {trade['side']}")
        if trade["research_only"] is not True or trade["preview_only"] is not True or trade["execution_approved"] is not False:
            failures.append("rotation trade safety flags failed")
        if trade["side"] == "buy" and trade["price"] <= trade["raw_price"]:
            failures.append("rotation buy fill should include one-way costs")
        if trade["side"] == "sell" and trade["price"] >= trade["raw_price"]:
            failures.append("rotation sell fill should include one-way costs")

    btc_values = [100.0 + index for index in range(220)]
    eth_values = [100.0 + (index * 0.5) for index in range(220)]
    btc_sma = crypto_lab.rolling_average(btc_values, 200)
    eth_sma = crypto_lab.rolling_average(eth_values, 200)
    selected = crypto_rotation.select_crypto_rotation_asset(219, btc_values, eth_values, btc_sma, eth_sma)
    if selected != "BTC/USD":
        failures.append(f"stronger eligible asset should be selected, got {selected}")

    cash_values = [200.0 - index for index in range(220)]
    cash_sma = crypto_lab.rolling_average(cash_values, 200)
    selected_cash = crypto_rotation.select_crypto_rotation_asset(219, cash_values, cash_values, cash_sma, cash_sma)
    if selected_cash != "CASH":
        failures.append("rotation should hold cash when neither asset is above SMA200")

    iteration_rows = crypto_lab.build_crypto_iteration_log_rows("2026-01-01T00:00:00+00:00")
    rotation_iterations = [
        row for row in iteration_rows if row["strategy_name"] == "crypto_monthly_btc_eth_momentum_rotation"
    ]
    if len(rotation_iterations) != 1:
        failures.append("iteration log should contain exactly one rotation entry")
    else:
        iteration = rotation_iterations[0]
        if "rank_return_days=126" not in iteration["allowed_parameter_set"]:
            failures.append("rotation iteration should record fixed 126-day momentum")
        if "trend_filter=SMA200" not in iteration["allowed_parameter_set"]:
            failures.append("rotation iteration should record fixed 200-day trend filter")
        if "monthly" not in iteration["allowed_parameter_set"]:
            failures.append("rotation iteration should record monthly rebalance")
        if "parameter search" not in iteration["reason_for_testing"]:
            failures.append("rotation iteration should explicitly avoid parameter search")

    source = inspect.getsource(crypto_rotation)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto rotation references forbidden term: {term}")

    original_downloader = crypto_lab.download_crypto_daily_history
    try:
        crypto_lab.download_crypto_daily_history = lambda data_symbol: (
            price_data["BTC/USD"] if data_symbol == "BTC-USD" else price_data["ETH/USD"]
        )
        with TemporaryDirectory() as tmp:
            result = crypto_lab.run_crypto_strategy_lab_files(Path(tmp))
            rotation_results_path = Path(tmp) / "crypto_rotation_results.csv"
            rotation_trades_path = Path(tmp) / "crypto_rotation_trades.csv"
            if not rotation_results_path.exists():
                failures.append("crypto lab should write crypto_rotation_results.csv")
            if not rotation_trades_path.exists():
                failures.append("crypto lab should write crypto_rotation_trades.csv")
            if not any("crypto rotation results" in line for line in result.summary_lines):
                failures.append("crypto lab summary should mention rotation results")
            iteration_text = (Path(tmp) / "crypto_strategy_iteration_log.csv").read_text(encoding="utf-8")
            if "crypto_monthly_btc_eth_momentum_rotation" not in iteration_text:
                failures.append("iteration log file should include the rotation strategy")
    finally:
        crypto_lab.download_crypto_daily_history = original_downloader

    if failures:
        print("Crypto rotation strategy verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto rotation strategy verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
