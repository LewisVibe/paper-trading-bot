from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto_report as crypto_report
from trading_bot.research.crypto_report import generate_crypto_strategy_report


FORBIDDEN_TERMS = [
    "yfinance",
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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def lab_row(strategy: str, symbol: str, period: str, cagr: float, sharpe: float, drawdown: float, calmar: float, trades: int) -> dict[str, object]:
    return {
        "created_at": "2026-01-01T00:00:00+00:00",
        "strategy_name": strategy,
        "symbol": symbol,
        "data_symbol": symbol.replace("/", "-"),
        "period": period,
        "total_return_pct": cagr,
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": drawdown,
        "calmar_ratio": calmar,
        "number_of_trades": trades,
        "cost_model_name": "crypto_research_default_taker_spread_slippage",
        "crypto_taker_fee_bps": 10,
        "crypto_spread_bps": 5,
        "crypto_slippage_bps": 10,
        "crypto_total_one_way_cost_bps": 25,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        rows = [
            lab_row("crypto_buy_and_hold_baseline", "BTC/USD", "full_period", 20, 0.8, 55, 0.36, 2),
            lab_row("crypto_sma_50_200_trend", "BTC/USD", "full_period", 15, 0.9, 30, 0.5, 4),
            lab_row("crypto_buy_above_200_exit_below_200", "BTC/USD", "full_period", 25, 1.0, 35, 0.71, 5),
            lab_row("crypto_buy_and_hold_baseline", "BTC/USD", "out_of_sample", 10, 0.7, 45, 0.22, 1),
            lab_row("crypto_sma_50_200_trend", "BTC/USD", "out_of_sample", 12, 0.9, 25, 0.48, 2),
            lab_row("crypto_buy_and_hold_baseline", "ETH/USD", "full_period", 18, 0.75, 60, 0.3, 2),
            lab_row("crypto_sma_50_200_trend", "ETH/USD", "full_period", 12, 0.7, 35, 0.34, 3),
            lab_row("crypto_buy_and_hold_baseline", "ETH/USD", "out_of_sample", 7, 0.5, 50, 0.14, 1),
            lab_row("crypto_buy_above_200_exit_below_200", "ETH/USD", "out_of_sample", 6, 0.6, 28, 0.21, 2),
            lab_row("crypto_buy_and_hold_baseline", "LTC/USD", "full_period", 11, 0.4, 62, 0.18, 2),
            lab_row("crypto_sma_50_200_trend", "LTC/USD", "full_period", 9, 0.5, 40, 0.225, 4),
            lab_row("crypto_buy_and_hold_baseline", "LTC/USD", "out_of_sample", 4, 0.2, 45, 0.0889, 1),
            lab_row("crypto_buy_above_200_with_vol_gate", "LTC/USD", "out_of_sample", 5, 0.3, 30, 0.1667, 2),
        ]
        write_csv(data_dir / "crypto_strategy_lab_results.csv", rows)

        result = generate_crypto_strategy_report(data_dir)
        if not result.output_path.exists():
            failures.append("crypto_strategy_report.csv was not created")

        report_rows = {
            (row["strategy_name"], row["symbol"], row["period"]): row
            for row in result.rows
        }
        btc_trend = report_rows[("crypto_sma_50_200_trend", "BTC/USD", "full_period")]
        if btc_trend["beats_buy_and_hold"] is not False:
            failures.append("BTC trend should not beat buy-and-hold when CAGR is lower")
        if btc_trend["drawdown_reduction_vs_buy_and_hold_pct"] != 25.0:
            failures.append("drawdown reduction should compare against matching BTC full-period benchmark")
        if btc_trend["cagr_gap_vs_buy_and_hold_pct"] != -5.0:
            failures.append("CAGR gap should compare against matching BTC full-period benchmark")

        btc_above = report_rows[("crypto_buy_above_200_exit_below_200", "BTC/USD", "full_period")]
        if btc_above["beats_buy_and_hold"] is not True:
            failures.append("BTC above-200 strategy should beat buy-and-hold in fixture")

        eth_above_oos = report_rows[("crypto_buy_above_200_exit_below_200", "ETH/USD", "out_of_sample")]
        if eth_above_oos["drawdown_reduction_vs_buy_and_hold_pct"] != 22.0:
            failures.append("ETH OOS row should compare against matching ETH OOS benchmark")
        ltc_vol_oos = report_rows[("crypto_buy_above_200_with_vol_gate", "LTC/USD", "out_of_sample")]
        if ltc_vol_oos["data_symbol"] != "LTC-USD":
            failures.append("LTC report row should preserve LTC-USD mapping")
        if ltc_vol_oos["drawdown_reduction_vs_buy_and_hold_pct"] != 15.0:
            failures.append("LTC OOS row should compare against matching LTC OOS benchmark")

        for row in result.rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"crypto report safety flags failed for {row['strategy_name']} {row['symbol']} {row['period']}")

        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != crypto_report.CRYPTO_REPORT_COLUMNS:
                failures.append("crypto report columns changed unexpectedly")

        summary = "\n".join(result.summary_lines)
        for expected in [
            "best BTC strategy by full-period Calmar",
            "best ETH strategy by full-period Calmar",
            "best BTC strategy by out-of-sample Calmar",
            "best ETH strategy by out-of-sample Calmar",
            "crypto research is not execution approval",
        ]:
            if expected not in summary:
                failures.append(f"summary missing: {expected}")

    with tempfile.TemporaryDirectory() as tmp:
        try:
            generate_crypto_strategy_report(Path(tmp))
            failures.append("missing crypto lab results should fail clearly")
        except RuntimeError as exc:
            if "Missing required crypto strategy lab results" not in str(exc):
                failures.append(f"missing input error was unclear: {exc}")

    source = inspect.getsource(crypto_report)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto strategy report references forbidden term: {term}")

    if failures:
        print("Crypto strategy report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto strategy report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
