from __future__ import annotations

import inspect
import csv
import sys
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto_lab as crypto_lab
import trading_bot.research.crypto_signal_preview as preview


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


def synthetic_rows(
    base: float,
    final_close: float,
    volatile_tail: bool = False,
) -> list[dict[str, object]]:
    start_date = date(2020, 1, 1)
    rows = []
    for index in range(280):
        close = base + ((index % 11) - 5) * 0.2
        if index >= 260 and volatile_tail:
            close = base + (80 if index % 2 == 0 else -80)
        rows.append(
            {
                "date": (start_date + timedelta(days=index)).isoformat(),
                "close": close,
            }
        )
    rows[-1]["close"] = final_close
    return rows


def row_for(rows: list[dict[str, object]], symbol: str) -> dict[str, object]:
    return next(row for row in rows if row["symbol"] == symbol)


def main() -> int:
    failures: list[str] = []

    if set(crypto_lab.CRYPTO_STRATEGIES) != {
        "crypto_buy_and_hold_baseline",
        "crypto_sma_50_200_trend",
        "crypto_buy_above_200_exit_below_200",
        "crypto_buy_above_200_with_vol_gate",
    }:
        failures.append("crypto signal preview should not add a new crypto strategy")

    long_rows = preview.build_crypto_signal_preview_rows(
        {
            "BTC/USD": synthetic_rows(100.0, 102.0),
            "ETH/USD": synthetic_rows(100.0, 110.0),
            "LTC/USD": synthetic_rows(50.0, 55.0),
        },
        created_at="2026-01-01T00:00:00+00:00",
    )
    btc_long = row_for(long_rows, "BTC/USD")
    eth_long = row_for(long_rows, "ETH/USD")
    ltc_row = row_for(long_rows, "LTC/USD")
    if btc_long["desired_position"] != "long":
        failures.append(f"BTC quiet above-SMA fixture should be long, got {btc_long['desired_position']}")
    if btc_long["vol_gate_passed"] is not True:
        failures.append("BTC quiet fixture should pass the volatility gate")
    if eth_long["desired_position"] != "long":
        failures.append(f"ETH above-SMA fixture should be long, got {eth_long['desired_position']}")
    if ltc_row["strategy_name"] != "no_decision_candidate_yet":
        failures.append("LTC should not have a fake best strategy candidate")
    if ltc_row["desired_position"] != "flat":
        failures.append("LTC no-decision row should remain flat")
    if ltc_row["data_symbol"] != "LTC-USD":
        failures.append("LTC/USD should map to LTC-USD")
    if ltc_row["research_status"] != "no_decision_candidate_yet_research_only":
        failures.append("LTC research status should say no decision candidate yet")
    if "run crypto lab/report/decision research" not in ltc_row["signal_reason"]:
        failures.append("LTC missing-decision reason should ask for decision research")

    decision_rows = [{"symbol": "LTC/USD", "decision_status": "not_useful"}]
    decision_rows_output = preview.build_crypto_signal_preview_rows(
        {
            "BTC/USD": synthetic_rows(100.0, 102.0),
            "ETH/USD": synthetic_rows(100.0, 110.0),
        },
        created_at="2026-01-01T00:00:00+00:00",
        decision_rows=decision_rows,
    )
    ltc_not_useful = row_for(decision_rows_output, "LTC/USD")
    if ltc_not_useful["desired_position"] != "flat":
        failures.append("LTC not_useful row should remain flat")
    if ltc_not_useful["research_status"] != "not_useful_research_only":
        failures.append("LTC not_useful decision should be reflected in research_status")
    if "decision status is not_useful" not in ltc_not_useful["signal_reason"]:
        failures.append("LTC not_useful reason should mention the saved decision status")

    flat_rows = preview.build_crypto_signal_preview_rows(
        {
            "BTC/USD": synthetic_rows(100.0, 90.0),
            "ETH/USD": synthetic_rows(100.0, 90.0),
        },
        created_at="2026-01-01T00:00:00+00:00",
    )
    if row_for(flat_rows, "BTC/USD")["desired_position"] != "flat":
        failures.append("BTC below-SMA fixture should be flat")
    if row_for(flat_rows, "ETH/USD")["desired_position"] != "flat":
        failures.append("ETH below-SMA fixture should be flat")

    volatile_rows = preview.build_crypto_signal_preview_rows(
        {
            "BTC/USD": synthetic_rows(100.0, 110.0, volatile_tail=True),
            "ETH/USD": synthetic_rows(100.0, 110.0),
        },
        created_at="2026-01-01T00:00:00+00:00",
    )
    btc_volatile = row_for(volatile_rows, "BTC/USD")
    if btc_volatile["desired_position"] != "flat":
        failures.append("BTC above-SMA high-vol fixture should be flat")
    if btc_volatile["vol_gate_passed"] is not False:
        failures.append("BTC high-vol fixture should fail the volatility gate")

    for row in long_rows + flat_rows + volatile_rows:
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"safety flags failed for {row['symbol']}")
        if row["symbol"] != "LTC/USD" and row.get("research_status") != "split_sensitive_research_candidate_not_execution_approved":
            failures.append("research_status should make split-sensitive non-approval explicit")
        if row["symbol"] == "LTC/USD" and row.get("research_status") != "no_decision_candidate_yet_research_only":
            failures.append("LTC research_status should not imply approval")
        for forbidden_key in ["shorting_enabled", "margin_enabled", "leverage_enabled"]:
            if row.get(forbidden_key) is True:
                failures.append(f"{forbidden_key} should not be enabled")

    summary = "\n".join(preview.build_crypto_signal_preview_summary(long_rows, Path("data/crypto_signal_preview.csv")))
    if "CRYPTO SIGNAL PREVIEW. RESEARCH ONLY. NOT EXECUTION." not in summary:
        failures.append("summary should include preview-only warning")
    if "split-sensitive research candidates" not in summary:
        failures.append("summary should warn that candidates are split-sensitive")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        decision_path = data_dir / "crypto_strategy_decision_report.csv"
        with decision_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["symbol", "decision_status"])
            writer.writeheader()
            writer.writerow({"symbol": "LTC/USD", "decision_status": "not_useful"})
        loaded = preview.read_optional_decision_rows(decision_path)
        if loaded[0]["decision_status"] != "not_useful":
            failures.append("decision rows should load from saved CSV when present")

    source = inspect.getsource(preview)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto signal preview references forbidden term: {term}")

    if failures:
        print("Crypto signal preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto signal preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
