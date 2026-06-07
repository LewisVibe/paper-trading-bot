from __future__ import annotations

import inspect
import sys
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto_cost_stress as crypto_cost_stress
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
    start_date = date(2020, 1, 1)
    rows = []
    for index in range(430):
        cyclical_noise = ((index % 19) - 9) * 1.5
        rows.append(
            {
                "date": (start_date + timedelta(days=index)).isoformat(),
                "close": round(start_price + (index * slope) + cyclical_noise, 4),
            }
        )
    return rows


def expected_strategy_names() -> set[str]:
    return {
        "crypto_buy_and_hold_baseline",
        "crypto_sma_50_200_trend",
        "crypto_buy_above_200_exit_below_200",
        "crypto_buy_above_200_with_vol_gate",
    }


def assert_stress_status_helpers(failures: list[str]) -> None:
    robust_rows = [
        {"cost_scenario": "high_cost", "cagr_pct": 6.0, "calmar_ratio": 0.6},
        {"cost_scenario": "extreme_cost", "cagr_pct": 3.0, "calmar_ratio": 0.4},
    ]
    sensitive_rows = [
        {"cost_scenario": "high_cost", "cagr_pct": 6.0, "calmar_ratio": 0.6},
        {"cost_scenario": "extreme_cost", "cagr_pct": -1.0, "calmar_ratio": -0.1},
    ]
    failed_rows = [
        {"cost_scenario": "high_cost", "cagr_pct": -2.0, "calmar_ratio": -0.2},
        {"cost_scenario": "extreme_cost", "cagr_pct": -3.0, "calmar_ratio": -0.3},
    ]

    if crypto_cost_stress.classify_stress_status_from_rows(robust_rows) != "robust_to_costs":
        failures.append("robust high/extreme rows should be robust_to_costs")
    if crypto_cost_stress.classify_stress_status_from_rows(sensitive_rows) != "sensitive_to_costs":
        failures.append("high-only survival should be sensitive_to_costs")
    if crypto_cost_stress.classify_stress_status_from_rows(failed_rows) != "fails_high_costs":
        failures.append("failed high/extreme rows should be fails_high_costs")
    if crypto_cost_stress.classify_stress_status_from_rows([]) != "insufficient_data":
        failures.append("empty stress rows should be insufficient_data")


def main() -> int:
    failures: list[str] = []

    price_data = {
        "BTC/USD": synthetic_crypto_rows(10_000, 45),
        "ETH/USD": synthetic_crypto_rows(800, 6),
        "LTC/USD": synthetic_crypto_rows(90, 1.5),
    }
    rows = crypto_cost_stress.build_crypto_cost_stress_rows(
        price_data,
        created_at="2026-01-01T00:00:00+00:00",
    )

    scenarios = {row["cost_scenario"] for row in rows}
    expected_scenarios = {"zero_cost", "default_cost", "high_cost", "extreme_cost"}
    if scenarios != expected_scenarios:
        failures.append(f"unexpected cost scenarios: {sorted(scenarios)}")

    scenario_costs = {
        row["cost_scenario"]: row["crypto_total_one_way_cost_bps"]
        for row in rows
    }
    expected_costs = {
        "zero_cost": 0.0,
        "default_cost": 25.0,
        "high_cost": 50.0,
        "extreme_cost": 100.0,
    }
    for scenario, expected_cost in expected_costs.items():
        if scenario_costs.get(scenario) != expected_cost:
            failures.append(f"{scenario} should have {expected_cost} one-way cost bps")

    strategies = {row["strategy_name"] for row in rows}
    if strategies != expected_strategy_names():
        failures.append(f"unexpected crypto strategy set: {sorted(strategies)}")
    if strategies != set(crypto_lab.CRYPTO_STRATEGIES):
        failures.append("cost stress should use exactly the existing crypto lab strategies")

    periods = {row["period"] for row in rows}
    if periods != {"full_period", "in_sample", "out_of_sample"}:
        failures.append(f"unexpected period labels: {sorted(periods)}")

    symbols = {row["symbol"] for row in rows}
    if symbols != {"BTC/USD", "ETH/USD", "LTC/USD"}:
        failures.append(f"unexpected symbols: {sorted(symbols)}")
    if "SOL/USD" in symbols:
        failures.append("SOL/USD should not be added")

    status_values = {row["stress_status"] for row in rows}
    allowed_status_values = {
        "robust_to_costs",
        "sensitive_to_costs",
        "fails_high_costs",
        "insufficient_data",
    }
    if not status_values <= allowed_status_values:
        failures.append(f"unexpected stress statuses: {sorted(status_values)}")

    for row in rows:
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"safety flags failed for {row['symbol']} {row['strategy_name']} {row['cost_scenario']}")
        if row["cost_scenario"] == "default_cost":
            if row["cagr_change_vs_default"] != 0.0 or row["calmar_change_vs_default"] != 0.0:
                failures.append("default_cost rows should have zero change versus default")
        for forbidden_key in ["shorting_enabled", "margin_enabled", "leverage_enabled"]:
            if row.get(forbidden_key) is True:
                failures.append(f"{forbidden_key} should not be enabled")

    expected_row_count = len(expected_strategy_names()) * len(expected_scenarios) * 3 * 3
    if len(rows) != expected_row_count:
        failures.append(f"expected {expected_row_count} stress rows, got {len(rows)}")

    assert_stress_status_helpers(failures)

    summary_lines = crypto_cost_stress.build_crypto_cost_stress_summary(rows)
    if "CRYPTO COST STRESS REPORT. RESEARCH ONLY. NOT EXECUTION." not in summary_lines[0]:
        failures.append("summary should begin with the research-only warning")
    required_summary_fragments = [
        "Best BTC strategy under default cost by out-of-sample Calmar",
        "Best BTC strategy under high cost by out-of-sample Calmar",
        "Best ETH strategy under default cost by out-of-sample Calmar",
        "Best ETH strategy under high cost by out-of-sample Calmar",
        "Warning: crypto cost stress is not execution approval.",
    ]
    for fragment in required_summary_fragments:
        if not any(fragment in line for line in summary_lines):
            failures.append(f"summary missing: {fragment}")

    source = inspect.getsource(crypto_cost_stress)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto cost stress report references forbidden term: {term}")

    if failures:
        print("Crypto cost stress report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto cost stress report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
