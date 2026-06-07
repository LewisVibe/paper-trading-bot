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
import trading_bot.research.crypto_period_diagnostics as diagnostics


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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def robustness_row(
    symbol: str,
    strategy_name: str,
    split_name: str,
    strategy_cagr: float,
    benchmark_cagr: float,
    trade_count: int,
    calmar: float = 0.2,
    benchmark_drawdown: float = 60.0,
    strategy_drawdown: float = 30.0,
) -> dict[str, object]:
    return {
        "created_at": "2026-01-01T00:00:00+00:00",
        "symbol": symbol,
        "strategy_name": strategy_name,
        "split_name": split_name,
        "in_sample_fraction": 0.8 if split_name == "split_80_20" else 0.7,
        "split_start_date": "2020-01-01",
        "split_point_date": "2021-01-01",
        "out_of_sample_start_date": "2021-01-02",
        "out_of_sample_end_date": "2021-04-30",
        "out_of_sample_cagr_pct": strategy_cagr,
        "out_of_sample_sharpe": 0.4,
        "out_of_sample_max_drawdown_pct": strategy_drawdown,
        "out_of_sample_calmar": calmar,
        "out_of_sample_trade_count": trade_count,
        "benchmark_oos_cagr_pct": benchmark_cagr,
        "benchmark_oos_sharpe": -0.2,
        "benchmark_oos_max_drawdown_pct": benchmark_drawdown,
        "benchmark_oos_calmar": -0.3,
        "cagr_gap_vs_benchmark_oos": round(strategy_cagr - benchmark_cagr, 4),
        "calmar_gap_vs_benchmark_oos": round(calmar - (-0.3), 4),
        "beats_buy_and_hold_oos": strategy_cagr > benchmark_cagr,
        "drawdown_reduction_oos_pct": round(benchmark_drawdown - strategy_drawdown, 4),
        "robustness_status": "split_sensitive",
        "robustness_reason": "fixture",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def main() -> int:
    failures: list[str] = []

    if "crypto_monthly_btc_eth_momentum_rotation" in set(crypto_lab.CRYPTO_STRATEGIES):
        failures.append("period diagnostics should not add a new crypto strategy")

    direct_cases = [
        (diagnostics.classify_period_diagnostic(-5.0, -20.0, 15.0, -0.1, 1, 55.0)[0], "benchmark_also_weak"),
        (diagnostics.classify_period_diagnostic(2.0, 5.0, -3.0, 0.1, 1, 20.0)[0], "cash_drag"),
        (diagnostics.classify_period_diagnostic(-1.0, 5.0, -6.0, -0.2, 5, 80.0)[0], "whipsaw_sensitive"),
        (diagnostics.classify_period_diagnostic(6.0, 8.0, -2.0, 0.2, 1, 70.0)[0], "profitable_but_weakening"),
    ]
    for actual, expected in direct_cases:
        if actual != expected:
            failures.append(f"expected diagnostic label {expected}, got {actual}")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        robustness_rows = [
            robustness_row("BTC/USD", "crypto_buy_above_200_with_vol_gate", "split_60_40", 20.0, 10.0, 1, 0.6),
            robustness_row("BTC/USD", "crypto_buy_above_200_with_vol_gate", "split_70_30", 12.0, 5.0, 1, 0.5),
            robustness_row("BTC/USD", "crypto_buy_above_200_with_vol_gate", "split_80_20", -5.0, -20.0, 1, -0.1),
            robustness_row("ETH/USD", "crypto_buy_above_200_exit_below_200", "split_60_40", 10.0, 6.0, 1, 0.5),
            robustness_row("ETH/USD", "crypto_buy_above_200_exit_below_200", "split_70_30", 7.0, 4.0, 1, 0.4),
            robustness_row("ETH/USD", "crypto_buy_above_200_exit_below_200", "split_80_20", 4.0, 3.0, 1, 0.2),
        ]
        write_csv(data_dir / "crypto_robustness_report.csv", robustness_rows)
        write_csv(
            data_dir / "crypto_strategy_lab_results.csv",
            [
                {
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "symbol": "BTC/USD",
                    "period": "out_of_sample",
                    "number_of_trades": 2,
                },
                {
                    "strategy_name": "crypto_buy_above_200_exit_below_200",
                    "symbol": "ETH/USD",
                    "period": "out_of_sample",
                    "number_of_trades": 2,
                },
            ],
        )
        write_csv(
            data_dir / "crypto_strategy_lab_trades.csv",
            [
                {
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "symbol": "BTC/USD",
                    "date": "2021-01-10",
                    "side": "buy",
                },
                {
                    "strategy_name": "crypto_buy_above_200_with_vol_gate",
                    "symbol": "BTC/USD",
                    "date": "2021-02-10",
                    "side": "sell",
                },
                {
                    "strategy_name": "crypto_buy_above_200_exit_below_200",
                    "symbol": "ETH/USD",
                    "date": "2021-01-10",
                    "side": "buy",
                },
                {
                    "strategy_name": "crypto_buy_above_200_exit_below_200",
                    "symbol": "ETH/USD",
                    "date": "2021-04-20",
                    "side": "sell",
                },
            ],
        )
        result = diagnostics.generate_crypto_period_diagnostics(data_dir)
        if not result.output_path.exists():
            failures.append("crypto_period_diagnostics.csv was not created")
        rows = read_csv(result.output_path)
        if len(rows) != 6:
            failures.append(f"expected 6 diagnostic rows, got {len(rows)}")
        btc_80 = next(row for row in rows if row["symbol"] == "BTC/USD" and row["split_name"] == "split_80_20")
        eth_80 = next(row for row in rows if row["symbol"] == "ETH/USD" and row["split_name"] == "split_80_20")
        if btc_80["diagnostic_label"] != "benchmark_also_weak":
            failures.append(f"BTC 80/20 should be benchmark_also_weak, got {btc_80['diagnostic_label']}")
        if "buy-and-hold was worse" not in btc_80["diagnostic_reason"]:
            failures.append("BTC 80/20 reason should explain worse buy-and-hold")
        if eth_80["diagnostic_label"] != "profitable_but_weakening":
            failures.append(f"ETH 80/20 should be profitable_but_weakening, got {eth_80['diagnostic_label']}")
        for row in rows:
            if row["research_only"] != "True" or row["preview_only"] != "True" or row["execution_approved"] != "False":
                failures.append("diagnostic safety flags should remain research-only and preview-only")
        summary = "\n".join(result.summary_lines)
        if "BTC 80/20" not in summary or "ETH 80/20" not in summary:
            failures.append("summary should include BTC and ETH 80/20 diagnostics")

    source = inspect.getsource(diagnostics)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto period diagnostics references forbidden term: {term}")

    if failures:
        print("Crypto period diagnostics verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto period diagnostics verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
