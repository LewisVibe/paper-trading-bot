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
import trading_bot.research.crypto_monitor as monitor
from trading_bot.runners import research_reports


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

    if set(crypto_lab.CRYPTO_STRATEGIES) != {
        "crypto_buy_and_hold_baseline",
        "crypto_sma_50_200_trend",
        "crypto_buy_above_200_exit_below_200",
        "crypto_buy_above_200_with_vol_gate",
    }:
        failures.append("show crypto monitor should not add a new crypto strategy")

    with TemporaryDirectory() as tmp:
        status_code, lines = monitor.show_crypto_monitor_file(Path(tmp))
        missing_output = "\n".join(lines)
        if status_code != 1:
            failures.append("missing signal preview should return status code 1")
        if "CRYPTO MONITOR. READ-ONLY. NOT EXECUTION." not in missing_output:
            failures.append("missing output should include read-only warning")
        if "python bot.py --preview-crypto-signals" not in missing_output:
            failures.append("missing output should instruct user to run preview-crypto-signals")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "crypto_signal_preview.csv",
            [
                {
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "symbol": "BTC/USD",
                    "data_symbol": "BTC-USD",
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "latest_close": "100000",
                    "sma_200": "90000",
                    "close_above_sma_200": "True",
                    "realised_vol_20": "0.5",
                    "median_realised_vol_252": "0.4",
                    "vol_gate_threshold": "0.6",
                    "vol_gate_passed": "True",
                    "desired_position": "long",
                    "signal_reason": "BTC close is above SMA200 and the fixed volatility gate passes.",
                    "research_status": "split_sensitive_research_candidate_not_execution_approved",
                    "research_only": "True",
                    "preview_only": "True",
                    "execution_approved": "False",
                },
                {
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "symbol": "ETH/USD",
                    "data_symbol": "ETH-USD",
                    "strategy_name": "crypto_buy_above_200_exit_below_200",
                    "latest_close": "3000",
                    "sma_200": "3500",
                    "close_above_sma_200": "False",
                    "realised_vol_20": "0.7",
                    "median_realised_vol_252": "0.6",
                    "vol_gate_threshold": "",
                    "vol_gate_passed": "",
                    "desired_position": "flat",
                    "signal_reason": "ETH close is at or below SMA200.",
                    "research_status": "split_sensitive_research_candidate_not_execution_approved",
                    "research_only": "True",
                    "preview_only": "True",
                    "execution_approved": "False",
                },
            ],
        )
        write_csv(
            data_dir / "crypto_strategy_decision_report.csv",
            [
                {
                    "symbol": "BTC/USD",
                    "decision_status": "research_watchlist",
                },
                {
                    "symbol": "ETH/USD",
                    "decision_status": "strongest_research_candidate",
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
                    "robustness_status": "split_sensitive",
                },
            ],
        )
        write_csv(
            data_dir / "crypto_period_diagnostics.csv",
            [
                {
                    "symbol": "BTC/USD",
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "diagnostic_label": "benchmark_also_weak",
                },
                {
                    "symbol": "ETH/USD",
                    "strategy_name": "crypto_buy_above_200_exit_below_200",
                    "diagnostic_label": "profitable_but_weakening",
                },
            ],
        )
        signal_path = data_dir / "crypto_signal_preview.csv"
        before = signal_path.read_text(encoding="utf-8")
        status_code, lines = monitor.show_crypto_monitor_file(data_dir)
        after = signal_path.read_text(encoding="utf-8")
        output = "\n".join(lines)
        if status_code != 0:
            failures.append("normal crypto monitor display should return status code 0")
        if before != after:
            failures.append("show crypto monitor should not modify the signal preview CSV")
        for expected in [
            "CRYPTO MONITOR. READ-ONLY. NOT EXECUTION.",
            "does not refresh data or submit orders",
            "BTC/USD",
            "crypto_buy_above_200_with_vol_gate",
            "long",
            "research_watchlist",
            "split_sensitive",
            "benchmark_also_weak",
            "ETH/USD",
            "crypto_buy_above_200_exit_below_200",
            "flat",
            "strongest_research_candidate",
            "profitable_but_weakening",
            "Execution approved: False for all rows.",
        ]:
            if expected not in output:
                failures.append(f"display output missing expected text: {expected}")

    for term in FORBIDDEN_TERMS:
        if term in inspect.getsource(monitor):
            failures.append(f"crypto monitor helper references forbidden term: {term}")
    if "generate_crypto_signal_preview" in inspect.getsource(monitor):
        failures.append("crypto monitor helper should not call preview refresh")

    command_source = inspect.getsource(research_reports.run_show_crypto_monitor_command)
    if "show_crypto_monitor_file" not in command_source:
        failures.append("crypto monitor command runner should call show_crypto_monitor_file")

    if failures:
        print("Show crypto monitor verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Show crypto monitor verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
