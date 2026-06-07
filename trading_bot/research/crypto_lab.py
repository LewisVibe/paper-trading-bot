"""Research-only crypto strategy lab helpers.

This module backtests a tiny fixed crypto strategy set with daily bars. It is
not connected to Alpaca, order submission, position reads, SQLite, or Discord.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CRYPTO_SYMBOL_MAP = {
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "LTC/USD": "LTC-USD",
}

CRYPTO_STRATEGIES = [
    "crypto_buy_and_hold_baseline",
    "crypto_sma_50_200_trend",
    "crypto_buy_above_200_exit_below_200",
    "crypto_buy_above_200_with_vol_gate",
]

CRYPTO_COST_MODEL_NAME = "crypto_research_default_taker_spread_slippage"
DEFAULT_CRYPTO_TAKER_FEE_BPS = 10.0
DEFAULT_CRYPTO_SPREAD_BPS = 5.0
DEFAULT_CRYPTO_SLIPPAGE_BPS = 10.0

CRYPTO_RESULTS_COLUMNS = [
    "created_at",
    "strategy_name",
    "symbol",
    "data_symbol",
    "period",
    "total_return_pct",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "number_of_trades",
    "cost_model_name",
    "crypto_taker_fee_bps",
    "crypto_spread_bps",
    "crypto_slippage_bps",
    "crypto_total_one_way_cost_bps",
    "research_only",
    "preview_only",
    "execution_approved",
]

CRYPTO_TRADES_COLUMNS = [
    "created_at",
    "strategy_name",
    "symbol",
    "data_symbol",
    "date",
    "side",
    "price",
    "raw_price",
    "reason",
    "cost_model_name",
    "crypto_taker_fee_bps",
    "crypto_spread_bps",
    "crypto_slippage_bps",
    "crypto_total_one_way_cost_bps",
    "research_only",
    "preview_only",
    "execution_approved",
]

CRYPTO_ITERATION_COLUMNS = [
    "created_at",
    "iteration_id",
    "hypothesis",
    "strategy_name",
    "allowed_parameter_set",
    "reason_for_testing",
    "result_summary",
    "decision",
    "next_research_question",
]


@dataclass
class CryptoStrategyLabResult:
    results_path: Path
    trades_path: Path
    iteration_log_path: Path
    result_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    iteration_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass(frozen=True)
class CryptoResearchCostModel:
    taker_fee_bps: float = DEFAULT_CRYPTO_TAKER_FEE_BPS
    spread_bps: float = DEFAULT_CRYPTO_SPREAD_BPS
    slippage_bps: float = DEFAULT_CRYPTO_SLIPPAGE_BPS
    name: str = CRYPTO_COST_MODEL_NAME

    @property
    def total_one_way_cost_bps(self) -> float:
        return self.taker_fee_bps + self.spread_bps + self.slippage_bps


def run_crypto_strategy_lab_files(
    data_dir: Path | str = "data",
) -> CryptoStrategyLabResult:
    from trading_bot.research.crypto_rotation import build_crypto_rotation_outputs

    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    price_data = {
        symbol: download_crypto_daily_history(data_symbol)
        for symbol, data_symbol in CRYPTO_SYMBOL_MAP.items()
    }
    result_rows, trade_rows, iteration_rows = build_crypto_strategy_lab_outputs(price_data, created_at)
    rotation_result_rows, rotation_trade_rows = build_crypto_rotation_outputs(price_data, created_at)

    results_path = data_path / "crypto_strategy_lab_results.csv"
    trades_path = data_path / "crypto_strategy_lab_trades.csv"
    iteration_log_path = data_path / "crypto_strategy_iteration_log.csv"
    rotation_results_path = data_path / "crypto_rotation_results.csv"
    rotation_trades_path = data_path / "crypto_rotation_trades.csv"
    write_rows(results_path, CRYPTO_RESULTS_COLUMNS, result_rows)
    write_rows(trades_path, CRYPTO_TRADES_COLUMNS, trade_rows)
    write_rows(iteration_log_path, CRYPTO_ITERATION_COLUMNS, iteration_rows)
    write_rows(rotation_results_path, CRYPTO_RESULTS_COLUMNS, rotation_result_rows)
    write_rows(rotation_trades_path, CRYPTO_TRADES_COLUMNS, rotation_trade_rows)

    return CryptoStrategyLabResult(
        results_path=results_path,
        trades_path=trades_path,
        iteration_log_path=iteration_log_path,
        result_rows=result_rows,
        trade_rows=trade_rows,
        iteration_rows=iteration_rows,
        summary_lines=build_crypto_strategy_lab_summary(
            result_rows,
            results_path,
            trades_path,
            iteration_log_path,
            rotation_results_path,
            rotation_trades_path,
        ),
    )


def download_crypto_daily_history(data_symbol: str) -> list[dict[str, Any]]:
    import yfinance as yf

    data = yf.download(data_symbol, period="10y", interval="1d", progress=False, auto_adjust=False)
    if data is None or data.empty:
        raise RuntimeError(f"No crypto daily history returned by yfinance for {data_symbol}.")

    rows: list[dict[str, Any]] = []
    for index, row in data.iterrows():
        close = value_from_row(row, "Close")
        if close is None or close <= 0:
            continue
        rows.append(
            {
                "date": index.date().isoformat(),
                "close": float(close),
            }
        )
    if len(rows) < 205:
        raise RuntimeError(f"Not enough crypto daily history for {data_symbol}. Need at least 205 rows.")
    return rows


def value_from_row(row: Any, column_name: str) -> float | None:
    try:
        value = row[column_name]
    except Exception:
        return None
    try:
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        return float(value)
    except (TypeError, ValueError):
        return None


def build_crypto_strategy_lab_outputs(
    price_data: dict[str, list[dict[str, Any]]],
    created_at: str | None = None,
    cost_model: CryptoResearchCostModel | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    crypto_cost_model = cost_model or CryptoResearchCostModel()
    result_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []

    for symbol, rows in price_data.items():
        data_symbol = crypto_data_symbol(symbol)
        normalized_rows = normalize_crypto_price_rows(rows)
        if len(normalized_rows) < 205:
            result_rows.extend(build_insufficient_crypto_rows(timestamp, symbol, data_symbol, crypto_cost_model))
            continue
        for strategy_name in CRYPTO_STRATEGIES:
            equity_curve, trades = simulate_crypto_strategy(strategy_name, normalized_rows, timestamp, symbol, data_symbol, crypto_cost_model)
            result_rows.extend(build_crypto_result_rows(timestamp, strategy_name, symbol, data_symbol, equity_curve, trades, crypto_cost_model))
            trade_rows.extend(trades)

    iteration_rows = build_crypto_iteration_log_rows(timestamp)
    return result_rows, trade_rows, iteration_rows


def crypto_data_symbol(symbol: str) -> str:
    return CRYPTO_SYMBOL_MAP.get(symbol, symbol.replace("/", "-"))


def normalize_crypto_price_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        try:
            close = float(row["close"])
        except (KeyError, TypeError, ValueError):
            continue
        if close <= 0:
            continue
        normalized.append({"date": str(row["date"]), "close": close})
    normalized.sort(key=lambda row: row["date"])
    return normalized


def simulate_crypto_strategy(
    strategy_name: str,
    rows: list[dict[str, Any]],
    created_at: str,
    symbol: str,
    data_symbol: str,
    cost_model: CryptoResearchCostModel,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if strategy_name == "crypto_buy_and_hold_baseline":
        return simulate_crypto_buy_and_hold(rows, created_at, strategy_name, symbol, data_symbol, cost_model)
    if strategy_name == "crypto_sma_50_200_trend":
        return simulate_crypto_signal_strategy(rows, created_at, strategy_name, symbol, data_symbol, "sma_50_above_200", cost_model)
    if strategy_name == "crypto_buy_above_200_exit_below_200":
        return simulate_crypto_signal_strategy(rows, created_at, strategy_name, symbol, data_symbol, "close_above_200", cost_model)
    if strategy_name == "crypto_buy_above_200_with_vol_gate":
        return simulate_crypto_signal_strategy(rows, created_at, strategy_name, symbol, data_symbol, "close_above_200_vol_gate", cost_model)
    raise ValueError(f"Unsupported crypto strategy: {strategy_name}")


def simulate_crypto_buy_and_hold(
    rows: list[dict[str, Any]],
    created_at: str,
    strategy_name: str,
    symbol: str,
    data_symbol: str,
    cost_model: CryptoResearchCostModel,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    starting_cash = 10_000.0
    first_close = rows[0]["close"]
    entry_price = adjusted_crypto_buy_price(first_close, cost_model)
    quantity = starting_cash / entry_price
    equity_curve = [
        {"date": row["date"], "equity": quantity * adjusted_crypto_sell_price(row["close"], cost_model)}
        for row in rows
    ]
    exit_price = adjusted_crypto_sell_price(rows[-1]["close"], cost_model)
    trades = [
        crypto_trade_row(created_at, strategy_name, symbol, data_symbol, rows[0]["date"], "buy", entry_price, first_close, "buy_first_valid_day", cost_model),
        crypto_trade_row(created_at, strategy_name, symbol, data_symbol, rows[-1]["date"], "sell", exit_price, rows[-1]["close"], "sell_final_valid_day", cost_model),
    ]
    return equity_curve, trades


def simulate_crypto_signal_strategy(
    rows: list[dict[str, Any]],
    created_at: str,
    strategy_name: str,
    symbol: str,
    data_symbol: str,
    rule_name: str,
    cost_model: CryptoResearchCostModel,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    closes = [row["close"] for row in rows]
    sma_50 = rolling_average(closes, 50)
    sma_200 = rolling_average(closes, 200)
    realized_vol_20 = rolling_realized_volatility(closes, 20)
    realized_vol_20_median_252 = rolling_median(realized_vol_20, 252)
    cash = 10_000.0
    quantity = 0.0
    in_position = False
    equity_curve: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []

    for index, row in enumerate(rows):
        close = row["close"]
        exit_value_price = adjusted_crypto_sell_price(close, cost_model)
        desired_long = crypto_desired_long(
            rule_name,
            close,
            sma_50[index],
            sma_200[index],
            realized_vol_20[index],
            realized_vol_20_median_252[index],
            in_position,
        )
        if desired_long and not in_position:
            entry_price = adjusted_crypto_buy_price(close, cost_model)
            quantity = cash / entry_price if entry_price > 0 else 0.0
            cash = 0.0
            in_position = True
            trades.append(crypto_trade_row(created_at, strategy_name, symbol, data_symbol, row["date"], "buy", entry_price, close, rule_name, cost_model))
        elif not desired_long and in_position:
            cash = quantity * exit_value_price
            quantity = 0.0
            in_position = False
            trades.append(crypto_trade_row(created_at, strategy_name, symbol, data_symbol, row["date"], "sell", exit_value_price, close, rule_name, cost_model))

        equity = cash + (quantity * exit_value_price if in_position else 0.0)
        equity_curve.append({"date": row["date"], "equity": equity})

    if in_position:
        final_row = rows[-1]
        exit_price = adjusted_crypto_sell_price(final_row["close"], cost_model)
        trades.append(
            crypto_trade_row(
                created_at,
                strategy_name,
                symbol,
                data_symbol,
                final_row["date"],
                "sell",
                exit_price,
                final_row["close"],
                "research_period_end",
                cost_model,
            )
        )
    return equity_curve, trades


def crypto_desired_long(
    rule_name: str,
    close: float,
    sma_50: float | None,
    sma_200: float | None,
    realized_vol_20: float | None = None,
    realized_vol_20_median_252: float | None = None,
    already_long: bool = False,
) -> bool:
    if sma_200 is None:
        return False
    if rule_name == "close_above_200":
        return close > sma_200
    if rule_name == "close_above_200_vol_gate":
        if close <= sma_200:
            return False
        # The volatility gate controls new entries only. Once already long, the
        # strategy exits on the same close <= SMA200 rule as the base strategy.
        if already_long:
            return True
        return volatility_gate_allows_entry(realized_vol_20, realized_vol_20_median_252)
    if rule_name == "sma_50_above_200":
        return sma_50 is not None and sma_50 > sma_200
    return False


def rolling_average(values: list[float], window: int) -> list[float | None]:
    averages: list[float | None] = []
    running_sum = 0.0
    for index, value in enumerate(values):
        running_sum += value
        if index >= window:
            running_sum -= values[index - window]
        if index >= window - 1:
            averages.append(running_sum / window)
        else:
            averages.append(None)
    return averages


def rolling_realized_volatility(values: list[float], window: int) -> list[float | None]:
    returns: list[float] = []
    for index in range(1, len(values)):
        previous = values[index - 1]
        returns.append((values[index] / previous) - 1 if previous > 0 else 0.0)

    volatility: list[float | None] = [None]
    for index in range(len(returns)):
        if index < window - 1:
            volatility.append(None)
            continue
        window_returns = returns[index - window + 1 : index + 1]
        mean_return = sum(window_returns) / len(window_returns)
        variance = sum((value - mean_return) ** 2 for value in window_returns) / len(window_returns)
        volatility.append(math.sqrt(variance) * math.sqrt(365))
    return volatility[: len(values)]


def rolling_median(values: list[float | None], window: int) -> list[float | None]:
    medians: list[float | None] = []
    for index in range(len(values)):
        if index < window - 1:
            medians.append(None)
            continue
        window_values = [
            value
            for value in values[index - window + 1 : index + 1]
            if value is not None
        ]
        if len(window_values) < window:
            medians.append(None)
            continue
        medians.append(median(window_values))
    return medians


def median(values: list[float]) -> float:
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2 == 1:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2


def volatility_gate_allows_entry(
    realized_vol_20: float | None,
    realized_vol_20_median_252: float | None,
) -> bool:
    if realized_vol_20 is None or realized_vol_20_median_252 is None or realized_vol_20_median_252 <= 0:
        return False
    return realized_vol_20 <= (1.5 * realized_vol_20_median_252)


def build_crypto_result_rows(
    created_at: str,
    strategy_name: str,
    symbol: str,
    data_symbol: str,
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
                strategy_name,
                symbol,
                data_symbol,
                period,
                [float(row["equity"]) for row in period_curve],
                len(period_trades),
                cost_model,
            )
        )
    return rows


def crypto_period_slices(equity_curve: list[dict[str, Any]]) -> list[tuple[str, int, int]]:
    if not equity_curve:
        return [("full_period", 0, 0), ("in_sample", 0, 0), ("out_of_sample", 0, 0)]
    total_rows = len(equity_curve)
    if total_rows < 3:
        return [
            ("full_period", 0, total_rows),
            ("in_sample", 0, total_rows),
            ("out_of_sample", 0, total_rows),
        ]
    split_index = int(total_rows * 0.7)
    split_index = max(1, min(total_rows - 1, split_index))
    return [
        ("full_period", 0, total_rows),
        ("in_sample", 0, split_index),
        ("out_of_sample", split_index, total_rows),
    ]


def filter_crypto_trades_for_period(
    trades: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not equity_curve:
        return []
    start_date = str(equity_curve[0]["date"])
    end_date = str(equity_curve[-1]["date"])
    return [
        trade
        for trade in trades
        if start_date <= str(trade.get("date", "")) <= end_date
    ]


def crypto_result_row(
    created_at: str,
    strategy_name: str,
    symbol: str,
    data_symbol: str,
    period: str,
    equity_values: list[float],
    number_of_trades: int,
    cost_model: CryptoResearchCostModel,
) -> dict[str, Any]:
    starting_equity = equity_values[0] if equity_values else 0.0
    final_equity = equity_values[-1] if equity_values else 0.0
    total_return_pct = ((final_equity - starting_equity) / starting_equity * 100) if starting_equity > 0 else 0.0
    cagr_pct = calculate_crypto_cagr_pct(starting_equity, final_equity, len(equity_values))
    max_drawdown_pct = calculate_crypto_max_drawdown_pct(equity_values)
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "symbol": symbol,
        "data_symbol": data_symbol,
        "period": period,
        "total_return_pct": round(total_return_pct, 4),
        "cagr_pct": round(cagr_pct, 4),
        "sharpe_ratio": round(calculate_crypto_sharpe_ratio(equity_values), 4),
        "max_drawdown_pct": round(max_drawdown_pct, 4),
        "calmar_ratio": round(cagr_pct / abs(max_drawdown_pct), 4) if max_drawdown_pct != 0 else 0.0,
        "number_of_trades": number_of_trades,
        "cost_model_name": cost_model.name,
        "crypto_taker_fee_bps": cost_model.taker_fee_bps,
        "crypto_spread_bps": cost_model.spread_bps,
        "crypto_slippage_bps": cost_model.slippage_bps,
        "crypto_total_one_way_cost_bps": cost_model.total_one_way_cost_bps,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_insufficient_crypto_rows(
    created_at: str,
    symbol: str,
    data_symbol: str,
    cost_model: CryptoResearchCostModel,
) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "strategy_name": strategy_name,
            "symbol": symbol,
            "data_symbol": data_symbol,
            "period": "full_period",
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
        for strategy_name in CRYPTO_STRATEGIES
    ]


def crypto_trade_row(
    created_at: str,
    strategy_name: str,
    symbol: str,
    data_symbol: str,
    date: str,
    side: str,
    price: float,
    raw_price: float,
    reason: str,
    cost_model: CryptoResearchCostModel,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "symbol": symbol,
        "data_symbol": data_symbol,
        "date": date,
        "side": side,
        "price": round(price, 4),
        "raw_price": round(raw_price, 4),
        "reason": reason,
        "cost_model_name": cost_model.name,
        "crypto_taker_fee_bps": cost_model.taker_fee_bps,
        "crypto_spread_bps": cost_model.spread_bps,
        "crypto_slippage_bps": cost_model.slippage_bps,
        "crypto_total_one_way_cost_bps": cost_model.total_one_way_cost_bps,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_crypto_iteration_log_rows(created_at: str) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "iteration_id": f"crypto_lab_initial_{index}",
            "hypothesis": hypothesis,
            "strategy_name": strategy_name,
            "allowed_parameter_set": parameter_set,
            "reason_for_testing": reason,
            "result_summary": "Recorded in crypto_strategy_lab_results.csv without tuning after seeing results.",
            "decision": "research_only_recorded",
            "next_research_question": "Compare fixed simple rules against buy-and-hold before adding any new crypto strategy.",
        }
        for index, (strategy_name, hypothesis, parameter_set, reason) in enumerate(
            [
                (
                    "crypto_buy_and_hold_baseline",
                    "A simple benchmark is needed before judging active crypto rules.",
                    "buy first valid daily close; sell final valid daily close",
                    "Benchmark inclusion prevents active strategies from being judged in isolation.",
                ),
                (
                    "crypto_sma_50_200_trend",
                    "A slow fixed SMA trend rule may reduce crypto drawdowns.",
                    "short_window=50; long_window=200",
                    "Fixed parameters avoid tuning after seeing results.",
                ),
                (
                    "crypto_buy_above_200_exit_below_200",
                    "A simple 200-day trend threshold may capture major crypto regimes.",
                    "long when close > SMA200; flat when close <= SMA200",
                    "Single fixed threshold keeps the first crypto lab intentionally small.",
                ),
                (
                    "crypto_buy_above_200_with_vol_gate",
                    "The 200-day trend rule may improve survivability by avoiding new long exposure during unusually high volatility regimes.",
                    "SMA200 trend; realized_vol_window=20; trailing_median_window=252; gate_multiplier=1.5; gate applies to new entries only",
                    "One controlled fixed-rule iteration tests a volatility gate without a parameter search.",
                ),
                (
                    "crypto_monthly_btc_eth_momentum_rotation",
                    "A simple monthly rotation between BTC, ETH, and cash may improve defensive crypto exposure by holding the stronger coin during risk-on periods.",
                    "universe=BTC/USD,ETH/USD; rebalance=monthly; rank_return_days=126; trend_filter=SMA200; hold_top=1; cash_when_no_asset_above_SMA200",
                    "One controlled fixed-rule rotation iteration tests BTC/ETH momentum without a parameter search.",
                ),
            ],
            start=1,
        )
    ]


def adjusted_crypto_buy_price(raw_price: float, cost_model: CryptoResearchCostModel) -> float:
    return raw_price * (1 + (cost_model.total_one_way_cost_bps / 10_000))


def adjusted_crypto_sell_price(raw_price: float, cost_model: CryptoResearchCostModel) -> float:
    return raw_price * (1 - (cost_model.total_one_way_cost_bps / 10_000))


def calculate_crypto_cagr_pct(starting_equity: float, final_equity: float, days: int) -> float:
    if starting_equity <= 0 or final_equity <= 0 or days <= 0:
        return 0.0
    years = days / 365
    if years <= 0:
        return 0.0
    return ((final_equity / starting_equity) ** (1 / years) - 1) * 100


def calculate_crypto_daily_returns(equity_values: list[float]) -> list[float]:
    returns: list[float] = []
    for index in range(1, len(equity_values)):
        previous = equity_values[index - 1]
        current = equity_values[index]
        if previous > 0:
            returns.append((current / previous) - 1)
    return returns


def calculate_crypto_sharpe_ratio(equity_values: list[float]) -> float:
    daily_returns = calculate_crypto_daily_returns(equity_values)
    if len(daily_returns) < 2:
        return 0.0
    mean_return = sum(daily_returns) / len(daily_returns)
    variance = sum((value - mean_return) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
    daily_volatility = math.sqrt(variance)
    if daily_volatility == 0:
        return 0.0
    return (mean_return / daily_volatility) * math.sqrt(365)


def calculate_crypto_max_drawdown_pct(equity_values: list[float]) -> float:
    peak = 0.0
    max_drawdown = 0.0
    for equity in equity_values:
        if equity > peak:
            peak = equity
        if peak > 0:
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)
    return max_drawdown * 100


def write_rows(output_path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def build_crypto_strategy_lab_summary(
    result_rows: list[dict[str, Any]],
    results_path: Path,
    trades_path: Path,
    iteration_log_path: Path,
    rotation_results_path: Path | None = None,
    rotation_trades_path: Path | None = None,
) -> list[str]:
    full_period_rows = [row for row in result_rows if row.get("period") == "full_period"]
    symbols = ", ".join(sorted({str(row["symbol"]) for row in full_period_rows}))
    strategies = ", ".join(CRYPTO_STRATEGIES)
    summary = [
        "CRYPTO STRATEGY LAB. RESEARCH ONLY. NOT EXECUTION.",
        f"Symbols tested: {symbols}",
        f"Strategies tested: {strategies}",
        "Rotation strategy tested separately: crypto_monthly_btc_eth_momentum_rotation",
        "Shorting enabled: false",
        "Margin enabled: false",
        "Leverage enabled: false",
        f"Saved crypto strategy results to {results_path}",
        f"Saved crypto strategy trades to {trades_path}",
        f"Saved crypto iteration log to {iteration_log_path}",
    ]
    if rotation_results_path is not None:
        summary.append(f"Saved crypto rotation results to {rotation_results_path}")
    if rotation_trades_path is not None:
        summary.append(f"Saved crypto rotation trades to {rotation_trades_path}")
    return summary
