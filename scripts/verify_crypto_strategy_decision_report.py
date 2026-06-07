from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto_decision as crypto_decision
from trading_bot.research.crypto_decision import generate_crypto_strategy_decision_report


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


def lab_row(strategy: str, symbol: str, period: str) -> dict[str, object]:
    return {
        "created_at": "2026-01-01T00:00:00+00:00",
        "strategy_name": strategy,
        "symbol": symbol,
        "data_symbol": symbol.replace("/", "-"),
        "period": period,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def report_row(
    strategy: str,
    symbol: str,
    period: str,
    cagr: float,
    sharpe: float,
    drawdown: float,
    calmar: float,
    beats: bool,
    drawdown_reduction: float,
    cagr_gap: float,
) -> dict[str, object]:
    return {
        "created_at": "2026-01-01T00:00:00+00:00",
        "strategy_name": strategy,
        "symbol": symbol,
        "data_symbol": symbol.replace("/", "-"),
        "period": period,
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": drawdown,
        "calmar_ratio": calmar,
        "trade_count": 4,
        "beats_buy_and_hold": beats,
        "drawdown_reduction_vs_buy_and_hold_pct": drawdown_reduction,
        "cagr_gap_vs_buy_and_hold_pct": cagr_gap,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "crypto_strategy_lab_results.csv",
            [
                lab_row("crypto_buy_and_hold_baseline", "BTC/USD", "full_period"),
                lab_row("crypto_buy_above_200_exit_below_200", "BTC/USD", "full_period"),
                lab_row("crypto_buy_and_hold_baseline", "BTC/USD", "out_of_sample"),
                lab_row("crypto_buy_above_200_exit_below_200", "BTC/USD", "out_of_sample"),
                lab_row("crypto_buy_and_hold_baseline", "ETH/USD", "full_period"),
                lab_row("crypto_sma_50_200_trend", "ETH/USD", "full_period"),
                lab_row("crypto_buy_and_hold_baseline", "ETH/USD", "out_of_sample"),
                lab_row("crypto_sma_50_200_trend", "ETH/USD", "out_of_sample"),
                lab_row("crypto_buy_and_hold_baseline", "LTC/USD", "full_period"),
                lab_row("crypto_buy_above_200_with_vol_gate", "LTC/USD", "full_period"),
                lab_row("crypto_buy_and_hold_baseline", "LTC/USD", "out_of_sample"),
                lab_row("crypto_buy_above_200_with_vol_gate", "LTC/USD", "out_of_sample"),
                lab_row("crypto_buy_and_hold_baseline", "DOGE/USD", "full_period"),
            ],
        )
        write_csv(
            data_dir / "crypto_strategy_report.csv",
            [
                report_row("crypto_buy_and_hold_baseline", "BTC/USD", "full_period", 30, 1.0, 50, 0.6, False, 0, 0),
                report_row("crypto_buy_above_200_exit_below_200", "BTC/USD", "full_period", 28, 1.1, 30, 0.9, False, 20, -2),
                report_row("crypto_buy_and_hold_baseline", "BTC/USD", "out_of_sample", 8, 0.7, 45, 0.18, False, 0, 0),
                report_row("crypto_buy_above_200_exit_below_200", "BTC/USD", "out_of_sample", 12, 1.0, 25, 0.48, True, 20, 4),
                report_row("crypto_buy_and_hold_baseline", "ETH/USD", "full_period", 25, 0.9, 55, 0.45, False, 0, 0),
                report_row("crypto_sma_50_200_trend", "ETH/USD", "full_period", 22, 0.8, 35, 0.63, False, 20, -3),
                report_row("crypto_buy_and_hold_baseline", "ETH/USD", "out_of_sample", 14, 0.8, 40, 0.35, False, 0, 0),
                report_row("crypto_sma_50_200_trend", "ETH/USD", "out_of_sample", 5, 0.7, 25, 0.2, False, 15, -9),
                report_row("crypto_buy_and_hold_baseline", "LTC/USD", "full_period", 16, 0.6, 55, 0.29, False, 0, 0),
                report_row("crypto_buy_above_200_with_vol_gate", "LTC/USD", "full_period", 12, 0.7, 35, 0.34, False, 20, -4),
                report_row("crypto_buy_and_hold_baseline", "LTC/USD", "out_of_sample", 4, 0.2, 45, 0.09, False, 0, 0),
                report_row("crypto_buy_above_200_with_vol_gate", "LTC/USD", "out_of_sample", 5, 0.3, 30, 0.17, False, 15, 1),
            ],
        )

        result = generate_crypto_strategy_decision_report(data_dir)
        if not result.output_path.exists():
            failures.append("crypto_strategy_decision_report.csv was not created")

        rows = {row["symbol"]: row for row in result.rows}
        btc = rows["BTC/USD"]
        if btc["decision_status"] != "strongest_research_candidate":
            failures.append("BTC fixture should become strongest_research_candidate")
        if btc["best_oos_strategy"] != "crypto_buy_above_200_exit_below_200":
            failures.append("BTC best OOS strategy selection failed")
        if btc["beats_buy_and_hold_oos"] is not True:
            failures.append("BTC should beat buy-and-hold OOS in fixture")

        eth = rows["ETH/USD"]
        if eth["decision_status"] == "strongest_research_candidate":
            failures.append("ETH weaker OOS fixture should not become strongest")
        if eth["decision_status"] not in {"research_watchlist", "inconclusive", "not_useful"}:
            failures.append(f"ETH got unexpected decision status: {eth['decision_status']}")

        doge = rows["DOGE/USD"]
        if doge["decision_status"] != "insufficient_data":
            failures.append("missing OOS rows should become insufficient_data")
        ltc = rows["LTC/USD"]
        if ltc["best_oos_strategy"] != "crypto_buy_above_200_with_vol_gate":
            failures.append("LTC best OOS strategy selection failed")
        if ltc["execution_approved"] is not False:
            failures.append("LTC decision row must not approve execution")

        for row in result.rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"decision safety flags failed for {row['symbol']}")

        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != crypto_decision.CRYPTO_DECISION_COLUMNS:
                failures.append("crypto decision report columns changed unexpectedly")

        summary = "\n".join(result.summary_lines)
        for expected in [
            "Best BTC research candidate",
            "Best ETH research candidate",
            "Decision status by symbol",
            "crypto research is not execution approval",
        ]:
            if expected not in summary:
                failures.append(f"summary missing: {expected}")

    with tempfile.TemporaryDirectory() as tmp:
        try:
            generate_crypto_strategy_decision_report(Path(tmp))
            failures.append("missing crypto inputs should fail clearly")
        except RuntimeError as exc:
            if "Missing required crypto strategy lab results" not in str(exc):
                failures.append(f"missing input error was unclear: {exc}")

    source = inspect.getsource(crypto_decision)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto decision report references forbidden term: {term}")

    if failures:
        print("Crypto strategy decision report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto strategy decision report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
