from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto_lab as crypto_lab
import trading_bot.research.crypto_state as crypto_state


FORBIDDEN_TERMS = [
    "yfinance",
    "download_crypto_daily_history",
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
    "sqlite3",
]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    failures: list[str] = []

    if set(crypto_state.CRYPTO_RESEARCH_STATE_SYMBOLS) != {"BTC/USD", "ETH/USD", "LTC/USD"}:
        failures.append("state report should contain exactly BTC/USD, ETH/USD, and LTC/USD")
    if "SOL/USD" in crypto_state.CRYPTO_RESEARCH_STATE_SYMBOLS:
        failures.append("SOL/USD should not be added")
    if set(crypto_lab.CRYPTO_STRATEGIES) != {
        "crypto_buy_and_hold_baseline",
        "crypto_sma_50_200_trend",
        "crypto_buy_above_200_exit_below_200",
        "crypto_buy_above_200_with_vol_gate",
    }:
        failures.append("state report should not add a new crypto strategy")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "crypto_research_preview.csv",
            [
                {"symbol": "BTC/USD", "research_status": "research_candidate"},
                {"symbol": "ETH/USD", "research_status": "research_candidate"},
                {"symbol": "LTC/USD", "research_status": "research_candidate"},
            ],
        )
        write_csv(
            data_dir / "crypto_strategy_decision_report.csv",
            [
                {
                    "symbol": "BTC/USD",
                    "best_oos_strategy": "crypto_buy_above_200_with_vol_gate",
                    "decision_status": "research_watchlist",
                    "next_research_step": "Keep monitoring, no execution.",
                },
                {
                    "symbol": "ETH/USD",
                    "best_oos_strategy": "crypto_buy_above_200_exit_below_200",
                    "decision_status": "strongest_research_candidate",
                    "next_research_step": "Keep monitoring, no execution.",
                },
                {
                    "symbol": "LTC/USD",
                    "best_oos_strategy": "crypto_buy_above_200_with_vol_gate",
                    "decision_status": "not_useful",
                    "next_research_step": "Do not continue this crypto strategy without new evidence.",
                },
            ],
        )
        write_csv(
            data_dir / "crypto_signal_preview.csv",
            [
                {
                    "symbol": "BTC/USD",
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "desired_position": "flat",
                    "signal_reason": "BTC close is at or below SMA200.",
                },
                {
                    "symbol": "ETH/USD",
                    "strategy_name": "crypto_buy_above_200_exit_below_200",
                    "desired_position": "flat",
                    "signal_reason": "ETH close is at or below SMA200.",
                },
                {
                    "symbol": "LTC/USD",
                    "strategy_name": "no_decision_candidate_yet",
                    "desired_position": "flat",
                    "signal_reason": "LTC decision status is not_useful; no signal candidate is selected.",
                },
            ],
        )
        write_csv(
            data_dir / "crypto_robustness_report.csv",
            [
                {
                    "symbol": "BTC/USD",
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "robustness_status": "split_sensitive",
                },
                {
                    "symbol": "ETH/USD",
                    "strategy_name": "crypto_buy_above_200_exit_below_200",
                    "robustness_status": "robust_candidate",
                },
                {
                    "symbol": "ETH/USD",
                    "strategy_name": "crypto_sma_50_200_trend",
                    "robustness_status": "split_sensitive",
                },
                {
                    "symbol": "LTC/USD",
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "robustness_status": "weak_candidate",
                },
            ],
        )
        write_csv(
            data_dir / "crypto_cost_stress_report.csv",
            [
                {
                    "symbol": "BTC/USD",
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "stress_status": "sensitive_to_costs",
                },
                {
                    "symbol": "ETH/USD",
                    "strategy_name": "crypto_buy_above_200_exit_below_200",
                    "stress_status": "robust_to_costs",
                },
                {
                    "symbol": "ETH/USD",
                    "strategy_name": "crypto_sma_50_200_trend",
                    "stress_status": "fails_high_costs",
                },
                {
                    "symbol": "LTC/USD",
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "stress_status": "fails_high_costs",
                },
            ],
        )
        write_csv(
            data_dir / "crypto_period_diagnostics.csv",
            [
                {"symbol": "BTC/USD", "diagnostic_label": "benchmark_also_weak"},
                {"symbol": "ETH/USD", "diagnostic_label": "profitable_but_weakening"},
                {"symbol": "LTC/USD", "diagnostic_label": "insufficient_data"},
            ],
        )

        result = crypto_state.generate_crypto_research_state_report(data_dir)
        if not result.output_path.exists():
            failures.append("crypto_research_state_report.csv was not created")
        rows = {row["symbol"]: row for row in result.rows}
        if set(rows) != {"BTC/USD", "ETH/USD", "LTC/USD"}:
            failures.append(f"unexpected state report symbols: {sorted(rows)}")
        if rows["BTC/USD"]["research_conclusion"] != "useful_but_split_sensitive_keep_monitoring":
            failures.append("BTC should be summarized as useful but split-sensitive")
        if rows["ETH/USD"]["research_conclusion"] != "useful_but_research_only_keep_monitoring":
            failures.append("ETH strongest candidate should remain research-only")
        if rows["LTC/USD"]["research_conclusion"] != "researched_but_not_useful_pause":
            failures.append("LTC not_useful should be summarized as paused/not useful")
        if rows["LTC/USD"]["next_research_step"] != "Do not continue this crypto strategy without new evidence.":
            failures.append("LTC next step should preserve saved decision report wording")
        if rows["ETH/USD"]["cost_stress_summary"] != "robust_to_costs":
            failures.append("ETH candidate cost summary should use only the selected best candidate")
        if rows["ETH/USD"]["all_strategy_cost_statuses"] != "fails_high_costs, robust_to_costs":
            failures.append("ETH all-strategy cost statuses should preserve mixed statuses separately")
        if rows["ETH/USD"]["robustness_summary"] != "robust_candidate":
            failures.append("ETH candidate robustness summary should use only the selected best candidate")
        if rows["ETH/USD"]["all_strategy_robustness_statuses"] != "robust_candidate, split_sensitive":
            failures.append("ETH all-strategy robustness statuses should preserve mixed statuses separately")
        if rows["BTC/USD"]["cost_stress_summary"] != "sensitive_to_costs":
            failures.append("BTC candidate cost summary should match the selected candidate")
        if rows["LTC/USD"]["cost_stress_summary"] != "fails_high_costs":
            failures.append("LTC candidate cost summary should remain available while LTC stays paused")
        for row in result.rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"state report safety flags failed for {row['symbol']}")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != crypto_state.CRYPTO_RESEARCH_STATE_COLUMNS:
                failures.append("state report CSV columns should match the declared schema")
        summary = "\n".join(result.summary_lines)
        for expected in [
            "CRYPTO RESEARCH STATE REPORT. RESEARCH ONLY. NOT EXECUTION.",
            "BTC/USD",
            "ETH/USD",
            "LTC/USD",
            "Symbols paused or not useful: LTC/USD",
            "Warning: no crypto execution approval.",
        ]:
            if expected not in summary:
                failures.append(f"summary missing: {expected}")

    missing_rows = crypto_state.build_crypto_research_state_rows({}, created_at="2026-01-01T00:00:00+00:00")
    if any(row["current_desired_position"] != "not_available" for row in missing_rows):
        failures.append("missing optional files should produce not_available signal fields")
    for row in missing_rows:
        if row["cost_stress_summary"] != "not_available" or row["all_strategy_cost_statuses"] != "not_available":
            failures.append("missing cost files should produce not_available cost summaries")
        if row["robustness_summary"] != "not_available" or row["all_strategy_robustness_statuses"] != "not_available":
            failures.append("missing robustness files should produce not_available robustness summaries")
    missing_summary = "\n".join(
        crypto_state.build_crypto_research_state_summary(
            missing_rows,
            Path("data/crypto_signal_preview.csv"),
            Path("data/crypto_research_state_report.csv"),
        )
    )
    if "python bot.py --preview-crypto-signals" not in missing_summary:
        failures.append("missing signal preview should recommend preview-crypto-signals")

    source = inspect.getsource(crypto_state)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto research state report references forbidden term: {term}")

    if failures:
        print("Crypto research state report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto research state report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
