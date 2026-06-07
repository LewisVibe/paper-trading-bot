"""Research-only BTC/ETH monthly momentum rotation helpers.

This module simulates one fixed crypto rotation strategy for research. It does
not call Alpaca, read positions, create orders, write SQLite, send Discord
alerts, enable shorting, enable margin, enable leverage, or approve execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from trading_bot.research.crypto_lab import (
    CRYPTO_RESULTS_COLUMNS,
    CRYPTO_TRADES_COLUMNS,
    CryptoResearchCostModel,
    adjusted_crypto_buy_price,
    adjusted_crypto_sell_price,
    crypto_period_slices,
    crypto_result_row,
    crypto_trade_row,
    filter_crypto_trades_for_period,
    normalize_crypto_price_rows,
    rolling_average,
)


CRYPTO_ROTATION_STRATEGY_NAME = "crypto_monthly_btc_eth_momentum_rotation"
CRYPTO_ROTATION_SYMBOL = "BTC_ETH_ROTATION"
CRYPTO_ROTATION_DATA_SYMBOL = "BTC-USD,ETH-USD"
CRYPTO_ROTATION_LOOKBACK_DAYS = 126
CRYPTO_ROTATION_TREND_SMA_DAYS = 200


def build_crypto_rotation_outputs(
    price_data: dict[str, list[dict[str, Any]]],
    created_at: str | None = None,
    cost_model: CryptoResearchCostModel | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    crypto_cost_model = cost_model or CryptoResearchCostModel()
    btc_rows = normalize_crypto_price_rows(price_data.get("BTC/USD", []))
    eth_rows = normalize_crypto_price_rows(price_data.get("ETH/USD", []))
    if len(btc_rows) < CRYPTO_ROTATION_TREND_SMA_DAYS + 1 or len(eth_rows) < CRYPTO_ROTATION_TREND_SMA_DAYS + 1:
        return build_insufficient_rotation_rows(timestamp, crypto_cost_model), []

    equity_curve, trades = simulate_crypto_monthly_btc_eth_momentum_rotation(
        btc_rows,
        eth_rows,
        timestamp,
        crypto_cost_model,
    )
    return build_crypto_rotation_result_rows(timestamp, equity_curve, trades, crypto_cost_model), trades


def simulate_crypto_monthly_btc_eth_momentum_rotation(
    btc_rows: list[dict[str, Any]],
    eth_rows: list[dict[str, Any]],
    created_at: str,
    cost_model: CryptoResearchCostModel,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    aligned_rows = align_btc_eth_rows(btc_rows, eth_rows)
    if not aligned_rows:
        return [], []

    btc_closes = [float(row["BTC/USD"]) for row in aligned_rows]
    eth_closes = [float(row["ETH/USD"]) for row in aligned_rows]
    btc_sma_200 = rolling_average(btc_closes, CRYPTO_ROTATION_TREND_SMA_DAYS)
    eth_sma_200 = rolling_average(eth_closes, CRYPTO_ROTATION_TREND_SMA_DAYS)

    cash = 10_000.0
    quantity = 0.0
    holding_symbol = "CASH"
    last_rebalance_month = ""
    equity_curve: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []

    for index, row in enumerate(aligned_rows):
        date_value = str(row["date"])
        month_key = date_value[:7]
        closes = {"BTC/USD": float(row["BTC/USD"]), "ETH/USD": float(row["ETH/USD"])}

        if month_key != last_rebalance_month and index >= CRYPTO_ROTATION_TREND_SMA_DAYS:
            target_symbol = select_crypto_rotation_asset(
                index,
                btc_closes,
                eth_closes,
                btc_sma_200,
                eth_sma_200,
            )
            if target_symbol != holding_symbol:
                if holding_symbol != "CASH":
                    raw_exit_price = closes[holding_symbol]
                    exit_price = adjusted_crypto_sell_price(raw_exit_price, cost_model)
                    cash = quantity * exit_price
                    trades.append(
                        crypto_trade_row(
                            created_at,
                            CRYPTO_ROTATION_STRATEGY_NAME,
                            CRYPTO_ROTATION_SYMBOL,
                            CRYPTO_ROTATION_DATA_SYMBOL,
                            date_value,
                            "sell",
                            exit_price,
                            raw_exit_price,
                            f"monthly_rotation_exit_{holding_symbol}",
                            cost_model,
                        )
                    )
                    quantity = 0.0
                    holding_symbol = "CASH"
                if target_symbol != "CASH":
                    raw_entry_price = closes[target_symbol]
                    entry_price = adjusted_crypto_buy_price(raw_entry_price, cost_model)
                    quantity = cash / entry_price if entry_price > 0 else 0.0
                    cash = 0.0
                    holding_symbol = target_symbol
                    trades.append(
                        crypto_trade_row(
                            created_at,
                            CRYPTO_ROTATION_STRATEGY_NAME,
                            CRYPTO_ROTATION_SYMBOL,
                            CRYPTO_ROTATION_DATA_SYMBOL,
                            date_value,
                            "buy",
                            entry_price,
                            raw_entry_price,
                            f"monthly_rotation_enter_{holding_symbol}",
                            cost_model,
                        )
                    )
            last_rebalance_month = month_key

        equity = cash
        if holding_symbol != "CASH":
            equity = quantity * adjusted_crypto_sell_price(closes[holding_symbol], cost_model)
        equity_curve.append({"date": date_value, "equity": equity})

    if holding_symbol != "CASH" and aligned_rows:
        final_row = aligned_rows[-1]
        final_close = float(final_row[holding_symbol])
        exit_price = adjusted_crypto_sell_price(final_close, cost_model)
        trades.append(
            crypto_trade_row(
                created_at,
                CRYPTO_ROTATION_STRATEGY_NAME,
                CRYPTO_ROTATION_SYMBOL,
                CRYPTO_ROTATION_DATA_SYMBOL,
                str(final_row["date"]),
                "sell",
                exit_price,
                final_close,
                "research_period_end",
                cost_model,
            )
        )
    return equity_curve, trades


def align_btc_eth_rows(
    btc_rows: list[dict[str, Any]],
    eth_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    btc_by_date = {str(row["date"]): float(row["close"]) for row in btc_rows}
    eth_by_date = {str(row["date"]): float(row["close"]) for row in eth_rows}
    dates = sorted(set(btc_by_date) & set(eth_by_date))
    return [
        {"date": date_value, "BTC/USD": btc_by_date[date_value], "ETH/USD": eth_by_date[date_value]}
        for date_value in dates
    ]


def select_crypto_rotation_asset(
    index: int,
    btc_closes: list[float],
    eth_closes: list[float],
    btc_sma_200: list[float | None],
    eth_sma_200: list[float | None],
) -> str:
    candidates = []
    for symbol, closes, sma_values in [
        ("BTC/USD", btc_closes, btc_sma_200),
        ("ETH/USD", eth_closes, eth_sma_200),
    ]:
        sma_200 = sma_values[index]
        if sma_200 is None or closes[index] <= sma_200:
            continue
        momentum = trailing_return(closes, index, CRYPTO_ROTATION_LOOKBACK_DAYS)
        if momentum is None:
            continue
        candidates.append((symbol, momentum))
    if not candidates:
        return "CASH"
    return sorted(candidates, key=lambda item: (-item[1], item[0]))[0][0]


def trailing_return(values: list[float], index: int, lookback_days: int) -> float | None:
    if index < lookback_days:
        return None
    previous = values[index - lookback_days]
    if previous <= 0:
        return None
    return (values[index] / previous) - 1


def build_crypto_rotation_result_rows(
    created_at: str,
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    cost_model: CryptoResearchCostModel,
) -> list[dict[str, Any]]:
    rows = []
    for period, start, end in crypto_period_slices(equity_curve):
        period_curve = equity_curve[start:end]
        period_trades = filter_crypto_trades_for_period(trades, period_curve)
        rows.append(
            crypto_result_row(
                created_at,
                CRYPTO_ROTATION_STRATEGY_NAME,
                CRYPTO_ROTATION_SYMBOL,
                CRYPTO_ROTATION_DATA_SYMBOL,
                period,
                [float(row["equity"]) for row in period_curve],
                len(period_trades),
                cost_model,
            )
        )
    return rows


def build_insufficient_rotation_rows(
    created_at: str,
    cost_model: CryptoResearchCostModel,
) -> list[dict[str, Any]]:
    rows = []
    for period in ["full_period", "in_sample", "out_of_sample"]:
        rows.append(
            {
                "created_at": created_at,
                "strategy_name": CRYPTO_ROTATION_STRATEGY_NAME,
                "symbol": CRYPTO_ROTATION_SYMBOL,
                "data_symbol": CRYPTO_ROTATION_DATA_SYMBOL,
                "period": period,
                "total_return_pct": 0.0,
                "cagr_pct": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "calmar_ratio": 0.0,
                "number_of_trades": 0,
                "cost_model_name": "insufficient_data",
                "crypto_taker_fee_bps": cost_model.taker_fee_bps,
                "crypto_spread_bps": cost_model.spread_bps,
                "crypto_slippage_bps": cost_model.slippage_bps,
                "crypto_total_one_way_cost_bps": cost_model.total_one_way_cost_bps,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
            }
        )
    return rows


def crypto_rotation_columns() -> tuple[list[str], list[str]]:
    return CRYPTO_RESULTS_COLUMNS, CRYPTO_TRADES_COLUMNS
