from __future__ import annotations

import inspect
import sys
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto_lab as crypto_lab
import trading_bot.research.crypto_robustness as crypto_robustness


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


def synthetic_crypto_rows(start_price: float, slope: float, cycle: float) -> list[dict[str, object]]:
    start_date = date(2020, 1, 1)
    rows = []
    for index in range(430):
        cyclical_noise = ((index % 37) - 18) * cycle
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


def main() -> int:
    failures: list[str] = []

    price_data = {
        "BTC/USD": synthetic_crypto_rows(10_000, 42, 12),
        "ETH/USD": synthetic_crypto_rows(700, 6, 2),
        "LTC/USD": synthetic_crypto_rows(90, 1.4, 0.5),
    }
    rows = crypto_robustness.build_crypto_robustness_rows(
        price_data,
        created_at="2026-01-01T00:00:00+00:00",
    )

    split_names = {row["split_name"] for row in rows}
    if split_names != {"split_60_40", "split_70_30", "split_80_20"}:
        failures.append(f"unexpected split names: {sorted(split_names)}")

    fractions = {row["split_name"]: row["in_sample_fraction"] for row in rows}
    expected_fractions = {"split_60_40": 0.60, "split_70_30": 0.70, "split_80_20": 0.80}
    for split_name, expected_fraction in expected_fractions.items():
        if fractions.get(split_name) != expected_fraction:
            failures.append(f"{split_name} should use in-sample fraction {expected_fraction}")

    strategies = {row["strategy_name"] for row in rows}
    if strategies != expected_strategy_names():
        failures.append(f"unexpected strategy set: {sorted(strategies)}")
    if strategies != set(crypto_lab.CRYPTO_STRATEGIES):
        failures.append("robustness report should use exactly the existing per-symbol crypto strategies")
    if "crypto_monthly_btc_eth_momentum_rotation" in strategies:
        failures.append("portfolio rotation should not be folded into per-symbol robustness rows")

    symbols = {row["symbol"] for row in rows}
    if symbols != {"BTC/USD", "ETH/USD", "LTC/USD"}:
        failures.append(f"unexpected symbols: {sorted(symbols)}")
    if "SOL/USD" in symbols:
        failures.append("SOL/USD should not be added")

    expected_count = len(expected_strategy_names()) * 3 * 3
    if len(rows) != expected_count:
        failures.append(f"expected {expected_count} robustness rows, got {len(rows)}")

    allowed_statuses = {"robust_candidate", "split_sensitive", "weak_candidate", "insufficient_data"}
    statuses = {row["robustness_status"] for row in rows}
    if not statuses <= allowed_statuses:
        failures.append(f"unexpected robustness statuses: {sorted(statuses)}")

    for row in rows:
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"safety flags failed for {row['symbol']} {row['strategy_name']} {row['split_name']}")
        for field_name in [
            "split_start_date",
            "split_point_date",
            "out_of_sample_start_date",
            "out_of_sample_end_date",
            "benchmark_oos_cagr_pct",
            "benchmark_oos_sharpe",
            "benchmark_oos_max_drawdown_pct",
            "benchmark_oos_calmar",
            "cagr_gap_vs_benchmark_oos",
            "calmar_gap_vs_benchmark_oos",
        ]:
            if field_name not in row:
                failures.append(f"missing robustness diagnostic field: {field_name}")
        if row["split_start_date"] and row["out_of_sample_start_date"] and row["split_start_date"] > row["out_of_sample_start_date"]:
            failures.append("split_start_date should not be after out_of_sample_start_date")
        if row["strategy_name"] == "crypto_buy_and_hold_baseline" and row["beats_buy_and_hold_oos"] is not False:
            failures.append("buy-and-hold should not be marked as beating itself")
        if row["strategy_name"] != "crypto_buy_and_hold_baseline":
            expected_cagr_gap = round(
                float(row["out_of_sample_cagr_pct"]) - float(row["benchmark_oos_cagr_pct"]),
                4,
            )
            expected_calmar_gap = round(
                float(row["out_of_sample_calmar"]) - float(row["benchmark_oos_calmar"]),
                4,
            )
            if row["cagr_gap_vs_benchmark_oos"] != expected_cagr_gap:
                failures.append("cagr_gap_vs_benchmark_oos calculation is inconsistent")
            if row["calmar_gap_vs_benchmark_oos"] != expected_calmar_gap:
                failures.append("calmar_gap_vs_benchmark_oos calculation is inconsistent")
        if row["robustness_reason"] == "":
            failures.append("robustness reason should be populated")
        for forbidden_key in ["shorting_enabled", "margin_enabled", "leverage_enabled"]:
            if row.get(forbidden_key) is True:
                failures.append(f"{forbidden_key} should not be enabled")

    robust_status, robust_reason = crypto_robustness.classify_crypto_robustness(
        [
            {
                "out_of_sample_cagr_pct": 10.0,
                "out_of_sample_calmar": 0.6,
                "out_of_sample_max_drawdown_pct": 20.0,
                "beats_buy_and_hold_oos": True,
            },
            {
                "out_of_sample_cagr_pct": 8.0,
                "out_of_sample_calmar": 0.5,
                "out_of_sample_max_drawdown_pct": 25.0,
                "beats_buy_and_hold_oos": True,
            },
            {
                "out_of_sample_cagr_pct": 6.0,
                "out_of_sample_calmar": 0.4,
                "out_of_sample_max_drawdown_pct": 30.0,
                "beats_buy_and_hold_oos": False,
            },
        ]
    )
    if robust_status != "robust_candidate" or not robust_reason:
        failures.append("classification should identify multi-split robust candidates")

    sensitive_status, _reason = crypto_robustness.classify_crypto_robustness(
        [
            {
                "out_of_sample_cagr_pct": 10.0,
                "out_of_sample_calmar": 0.6,
                "out_of_sample_max_drawdown_pct": 20.0,
                "beats_buy_and_hold_oos": False,
            },
            {
                "out_of_sample_cagr_pct": 8.0,
                "out_of_sample_calmar": 0.5,
                "out_of_sample_max_drawdown_pct": 25.0,
                "beats_buy_and_hold_oos": False,
            },
            {
                "out_of_sample_cagr_pct": -2.0,
                "out_of_sample_calmar": -0.1,
                "out_of_sample_max_drawdown_pct": 40.0,
                "beats_buy_and_hold_oos": False,
            },
        ]
    )
    if sensitive_status != "split_sensitive":
        failures.append("two usable splits should classify as split_sensitive")

    weak_status, _reason = crypto_robustness.classify_crypto_robustness(
        [
            {
                "out_of_sample_cagr_pct": -1.0,
                "out_of_sample_calmar": -0.1,
                "out_of_sample_max_drawdown_pct": 40.0,
                "beats_buy_and_hold_oos": False,
            },
            {
                "out_of_sample_cagr_pct": -2.0,
                "out_of_sample_calmar": -0.2,
                "out_of_sample_max_drawdown_pct": 42.0,
                "beats_buy_and_hold_oos": False,
            },
            {
                "out_of_sample_cagr_pct": -3.0,
                "out_of_sample_calmar": -0.3,
                "out_of_sample_max_drawdown_pct": 44.0,
                "beats_buy_and_hold_oos": False,
            },
        ]
    )
    if weak_status != "weak_candidate":
        failures.append("negative splits should classify as weak_candidate")

    benchmark_row = {
        "symbol": "BTC/USD",
        "strategy_name": "crypto_buy_and_hold_baseline",
        "split_name": "split_80_20",
        "out_of_sample_cagr_pct": -20.0,
        "out_of_sample_sharpe": -0.5,
        "out_of_sample_max_drawdown_pct": 70.0,
        "out_of_sample_calmar": -0.4,
    }
    negative_winner_row = {
        "symbol": "BTC/USD",
        "strategy_name": "crypto_buy_above_200_with_vol_gate",
        "split_name": "split_80_20",
        "out_of_sample_cagr_pct": -5.0,
        "out_of_sample_sharpe": -0.1,
        "out_of_sample_max_drawdown_pct": 30.0,
        "out_of_sample_calmar": -0.05,
    }
    crypto_robustness.add_benchmark_metrics(negative_winner_row, benchmark_row)
    if crypto_robustness.beats_benchmark(negative_winner_row, benchmark_row) is not True:
        failures.append("a strategy can beat buy-and-hold while still having negative absolute CAGR")
    if negative_winner_row["cagr_gap_vs_benchmark_oos"] != 15.0:
        failures.append("negative winner CAGR gap should show improvement versus worse benchmark")
    if negative_winner_row["benchmark_oos_cagr_pct"] != -20.0:
        failures.append("benchmark OOS CAGR should be copied beside strategy row")
    note = crypto_robustness.negative_benchmark_note([
        {**negative_winner_row, "beats_buy_and_hold_oos": True}
    ])
    if "buy-and-hold was worse" not in note:
        failures.append("summary note should explain negative-CAGR benchmark wins")

    summary_lines = crypto_robustness.build_crypto_robustness_summary(rows)
    if "CRYPTO ROBUSTNESS REPORT. RESEARCH ONLY. NOT EXECUTION." not in summary_lines[0]:
        failures.append("summary should start with research-only warning")
    for fragment in [
        "Best BTC strategy across splits",
        "Best ETH strategy across splits",
        "Robust candidates:",
        "Split-sensitive candidates:",
        "Negative absolute CAGR benchmark wins:",
        "Warning: crypto robustness report is not execution approval.",
    ]:
        if not any(fragment in line for line in summary_lines):
            failures.append(f"summary missing: {fragment}")

    source = inspect.getsource(crypto_robustness)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto robustness report references forbidden term: {term}")

    if failures:
        print("Crypto robustness report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto robustness report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
