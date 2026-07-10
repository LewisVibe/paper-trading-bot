"""Market-data-backed research and backtest command runners.

These commands may download price data. They do not submit orders, read broker
positions, send alerts, or write execution audit records.
"""

from __future__ import annotations

import csv
import logging
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

from trading_bot.config import AppConfig, ConfigError, default_research_universe_tickers
from trading_bot.market_data import configure_yfinance_cache, download_backtest_prices
from trading_bot.research.backtesting import (
    BacktestResult,
    BacktestTrade,
    StrategyPortfolioResult,
    build_comparison_result,
    build_period_comparison_results,
    build_strategy_portfolio_results,
    build_strategy_robustness_summary,
    calculate_annualised_volatility_pct,
    calculate_cagr_pct,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    format_backtest_result,
    print_portfolio_summary,
    print_ranked_portfolio_summary,
    print_ranked_robustness_summary,
    print_ranked_sma_sensitivity_summary,
    print_ranked_strategy_summary,
    print_ranked_trend_stress_test_summary,
    sma_sensitivity_strategy_name,
    trend_stress_strategy_name,
    write_backtest_results,
    write_backtest_trades,
    write_sma_sensitivity_portfolio,
    write_sma_sensitivity_results,
    write_strategy_comparison_results,
    write_strategy_comparison_trades,
    write_strategy_portfolio_comparison,
    write_strategy_portfolio_equity_curves,
    write_strategy_robustness_summary,
    write_strategy_ticker_equity_curves,
    write_trend_stress_test_portfolio,
    write_trend_stress_test_results,
)
from trading_bot.research.costs import CostModel, adjusted_buy_fill_price, adjusted_sell_fill_price
from trading_bot.strategies.adaptive import select_adaptive_momentum_assets
from trading_bot.strategies.breakout import (
    adjusted_breakout_buy_fill,
    adjusted_breakout_sell_fill,
    atr_trailing_stop_exit,
    is_252_day_high_breakout,
    sma_100_exit,
    volume_confirmation,
)
from trading_bot.strategies.rotation import (
    buy_and_hold_equity_curve,
    equal_weight_buy_and_hold_equity_curve,
    select_top_momentum_etfs,
    should_skip_rebalance_trade,
)
from trading_bot.strategies.sma import (
    SIGNAL_BUY,
    SIGNAL_SELL,
    SMA_SENSITIVITY_PAIRS,
    TREND_STRESS_TEST_PAIRS,
    comparison_entry_signal,
    comparison_exit_signal,
    crossed_above,
    crossed_below,
    detect_sma_signal,
    prepare_sma_sensitivity_data,
    prepare_strategy_comparison_data,
    prepare_trend_stress_test_data,
)


MARKET_DATA_COMMANDS = frozenset(
    {
        "--backtest",
        "--compare-strategies",
        "--sma-sensitivity",
        "--trend-stress-test",
        "--etf-rotation-backtest",
        "--adaptive-momentum-backtest",
    }
)

TREND_STRESS_TEST_SLIPPAGE_BPS = [0, 5, 10, 25, 50]
DEFAULT_ETF_ROTATION_UNIVERSE = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLY",
    "XLP",
    "XLI",
    "XLU",
    "TLT",
    "GLD",
]
ETF_ROTATION_TOP_N = 3
MIN_REBALANCE_NOTIONAL = 100.0
ADAPTIVE_RISK_ASSETS = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLY",
    "XLI",
]
ADAPTIVE_DEFENSIVE_ASSETS = ["TLT", "GLD", "XLP", "XLU"]
ADAPTIVE_TOP_N = 3


def run_backtest(config: AppConfig, logger: logging.Logger) -> int:
    configure_yfinance_cache(config, logger)
    results: list[BacktestResult] = []
    trades: list[BacktestTrade] = []
    portfolio_results: list[StrategyPortfolioResult] = []
    errors: list[str] = []
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))

    print("Backtest: regime_sma_vol_filter")
    print("ticker,total_return,buy_and_hold,trades,win_rate,avg_trade,max_drawdown,time_in_market")

    try:
        regime_data = download_backtest_prices(config, config.strategy.regime_ticker)
    except Exception as exc:
        logger.error("Backtest failed: could not download regime ticker %s: %s", config.strategy.regime_ticker, exc)
        write_backtest_results(config, results, cost_model)
        write_backtest_trades(config, trades, cost_model)
        print(f"Regime ticker error: {config.strategy.regime_ticker} - {exc}")
        return 1

    for ticker in config.tickers:
        try:
            ticker_data = download_backtest_prices(config, ticker)
            result, ticker_trades = backtest_ticker(config, ticker, ticker_data, regime_data, cost_model)
            results.append(result)
            trades.extend(ticker_trades)
            print(format_backtest_result(result))
        except Exception as exc:
            errors.append(ticker)
            logger.error("Backtest failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")

    write_backtest_results(config, results, cost_model)
    write_backtest_trades(config, trades, cost_model)
    print_portfolio_summary(config, results, trades, errors)
    print(f"Saved results to {config.backtest.output_csv}")
    print(f"Saved trades to {config.backtest.trades_csv}")
    return 0 if results else 1


def run_etf_rotation_backtest(config: AppConfig, logger: logging.Logger) -> int:
    configure_yfinance_cache(config, logger)
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))
    tickers = DEFAULT_ETF_ROTATION_UNIVERSE
    data_by_ticker = {}

    print("ETF rotation backtest")
    print(f"Tickers: {len(tickers)}")
    print(f"Top N: {ETF_ROTATION_TOP_N}")

    for ticker in tickers:
        try:
            data_by_ticker[ticker] = download_backtest_prices(config, ticker)
        except Exception as exc:
            logger.error("ETF rotation backtest failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")

    if "SPY" not in data_by_ticker:
        write_etf_rotation_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("SPY regime ticker is required for ETF rotation.")
        return 1

    tradable_tickers = [ticker for ticker in tickers if ticker in data_by_ticker]
    if len(tradable_tickers) < ETF_ROTATION_TOP_N:
        write_etf_rotation_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("Not enough ETF data for rotation backtest.")
        return 1

    common_index = None
    for ticker in tradable_tickers:
        index = data_by_ticker[ticker].index
        common_index = index if common_index is None else common_index.intersection(index)
    common_index = common_index.sort_values()

    if len(common_index) < 254:
        write_etf_rotation_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print(f"Not enough shared ETF history. Need at least 254 rows, got {len(common_index)}.")
        return 1

    aligned = {
        ticker: data_by_ticker[ticker].loc[common_index]
        for ticker in tradable_tickers
    }
    rebalance_indices = get_monthly_rebalance_indices(common_index)
    if not rebalance_indices:
        write_etf_rotation_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("No monthly rebalance dates found.")
        return 1

    cash = config.backtest.starting_cash
    positions: dict[str, float] = {}
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []

    for index, day in enumerate(common_index):
        equity = cash + sum(
            quantity * float(aligned[ticker].iloc[index]["close"])
            for ticker, quantity in positions.items()
        )
        equity_curve.append(
            {
                "date": day.date().isoformat(),
                "equity": equity,
            }
        )

        if index not in rebalance_indices or index >= len(common_index) - 1:
            continue

        price_history = {
            ticker: [float(value) for value in aligned[ticker].iloc[: index + 1]["close"]]
            for ticker in tradable_tickers
        }
        spy_prices = price_history["SPY"]
        try:
            selections = select_top_momentum_etfs(
                price_history,
                spy_prices,
                top_n=ETF_ROTATION_TOP_N,
            )
        except ValueError:
            continue

        target_tickers = [selection.ticker for selection in selections]
        next_index = index + 1
        next_day = common_index[next_index].date().isoformat()
        open_prices = {
            ticker: float(aligned[ticker].iloc[next_index]["open"])
            for ticker in tradable_tickers
        }
        portfolio_value = cash + sum(
            quantity * open_prices[ticker]
            for ticker, quantity in positions.items()
        )

        for ticker in sorted(set(positions) - set(target_tickers)):
            quantity = positions.pop(ticker)
            fill_price = float(adjusted_sell_fill_price(open_prices[ticker], cost_model))
            cash += quantity * fill_price
            trades.append(
                build_etf_rotation_trade_row(
                    next_day,
                    ticker,
                    "sell",
                    "removed_from_top_n",
                    quantity,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

        if not target_tickers:
            continue

        target_value = portfolio_value / len(target_tickers)

        for ticker in target_tickers:
            current_quantity = positions.get(ticker, 0.0)
            current_value = current_quantity * open_prices[ticker]
            if current_value <= target_value:
                continue
            sell_value = current_value - target_value
            fill_price = float(adjusted_sell_fill_price(open_prices[ticker], cost_model))
            if should_skip_rebalance_trade(sell_value, MIN_REBALANCE_NOTIONAL):
                continue
            quantity_to_sell = min(current_quantity, sell_value / fill_price)
            if quantity_to_sell <= 0:
                continue
            positions[ticker] = current_quantity - quantity_to_sell
            cash += quantity_to_sell * fill_price
            trades.append(
                build_etf_rotation_trade_row(
                    next_day,
                    ticker,
                    "sell",
                    "rebalance_reduce",
                    quantity_to_sell,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

        for ticker in target_tickers:
            current_quantity = positions.get(ticker, 0.0)
            current_value = current_quantity * open_prices[ticker]
            if current_value >= target_value:
                continue
            buy_value = min(target_value - current_value, cash)
            if current_quantity > 0 and should_skip_rebalance_trade(buy_value, MIN_REBALANCE_NOTIONAL):
                continue
            fill_price = float(adjusted_buy_fill_price(open_prices[ticker], cost_model))
            quantity_to_buy = buy_value / fill_price if fill_price > 0 else 0.0
            if quantity_to_buy <= 0:
                continue
            positions[ticker] = current_quantity + quantity_to_buy
            cash -= quantity_to_buy * fill_price
            trades.append(
                build_etf_rotation_trade_row(
                    next_day,
                    ticker,
                    "buy",
                    "target_top_n",
                    quantity_to_buy,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

    spy_benchmark_curve = buy_and_hold_equity_curve(
        [float(value) for value in aligned["SPY"]["close"]],
        config.backtest.starting_cash,
    )
    qqq_benchmark_curve = (
        buy_and_hold_equity_curve(
            [float(value) for value in aligned["QQQ"]["close"]],
            config.backtest.starting_cash,
        )
        if "QQQ" in aligned
        else []
    )
    equal_weight_benchmark_curve = equal_weight_buy_and_hold_equity_curve(
        {
            ticker: [float(value) for value in aligned[ticker]["close"]]
            for ticker in tradable_tickers
        },
        config.backtest.starting_cash,
    )
    results = build_etf_rotation_result_rows(
        equity_curve,
        trades,
        config.backtest.starting_cash,
        ETF_ROTATION_TOP_N,
        len(tradable_tickers),
        MIN_REBALANCE_NOTIONAL,
        {
            "spy": spy_benchmark_curve,
            "qqq": qqq_benchmark_curve,
            "equal_weight": equal_weight_benchmark_curve,
        },
    )

    write_etf_rotation_outputs(results, trades, equity_curve, cost_model, MIN_REBALANCE_NOTIONAL)
    full_period_result = next(
        (result for result in results if result.get("period") == "full_period"),
        results[0],
    )
    print(
        "monthly_etf_momentum_rotation,"
        f"{full_period_result['total_return_pct']:.2f}%,"
        f"{full_period_result['max_drawdown_pct']:.2f}%,"
        f"{len(trades)} trades"
    )
    print("Saved ETF rotation results to data/etf_rotation_results.csv")
    print("Saved ETF rotation trades to data/etf_rotation_trades.csv")
    print("Saved ETF rotation equity curve to data/etf_rotation_equity_curve.csv")
    return 0


def get_monthly_rebalance_indices(index) -> set[int]:
    rebalance_indices: set[int] = set()
    for position in range(len(index) - 1):
        current_month = (index[position].year, index[position].month)
        next_month = (index[position + 1].year, index[position + 1].month)
        if current_month != next_month:
            rebalance_indices.add(position)
    return rebalance_indices


def empty_etf_rotation_benchmark_metrics() -> dict[str, float]:
    return {
        "total_return_pct": 0.0,
        "cagr_pct": 0.0,
        "max_drawdown_pct": 0.0,
    }


def build_etf_rotation_result_rows(
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    starting_equity: float,
    top_n: int,
    universe_size: int,
    min_rebalance_notional: float,
    benchmark_curves: dict[str, list[float]] | None = None,
) -> list[dict[str, Any]]:
    """Build full/in/out period rows from one completed ETF rotation run.

    The strategy simulation still runs once. These period rows are reporting
    slices only, so walk-forward analysis can compare in-sample and
    out-of-sample behaviour without changing the rotation rules.
    """
    benchmark_curves = benchmark_curves or {}
    periods = etf_rotation_period_slices(equity_curve)
    rows = []
    for period_name, start_index, end_index in periods:
        period_curve = equity_curve[start_index:end_index]
        equity_values = [float(row["equity"]) for row in period_curve]
        period_starting_equity = equity_values[0] if equity_values else starting_equity
        period_trades = filter_etf_rotation_trades_for_period(
            trades,
            period_curve[0]["date"] if period_curve else None,
            period_curve[-1]["date"] if period_curve else None,
        )
        spy_benchmark = build_etf_rotation_period_benchmark_metrics(
            benchmark_curves.get("spy", []),
            start_index,
            end_index,
        )
        qqq_benchmark = build_etf_rotation_period_benchmark_metrics(
            benchmark_curves.get("qqq", []),
            start_index,
            end_index,
        )
        equal_weight_benchmark = build_etf_rotation_period_benchmark_metrics(
            benchmark_curves.get("equal_weight", []),
            start_index,
            end_index,
        )
        rows.append(
            build_etf_rotation_result_row(
                period_name,
                equity_values,
                len(period_trades),
                top_n,
                universe_size,
                min_rebalance_notional,
                spy_benchmark,
                qqq_benchmark,
                equal_weight_benchmark,
                period_starting_equity,
            )
        )
    return rows


def etf_rotation_period_slices(equity_curve: list[dict[str, Any]]) -> list[tuple[str, int, int]]:
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


def filter_etf_rotation_trades_for_period(
    trades: list[dict[str, Any]],
    start_date: str | None,
    end_date: str | None,
) -> list[dict[str, Any]]:
    if start_date is None or end_date is None:
        return []
    return [
        trade
        for trade in trades
        if start_date <= str(trade.get("date", "")) <= end_date
    ]


def build_etf_rotation_result_row(
    period: str,
    equity_values: list[float],
    number_of_trades: int,
    top_n: int,
    universe_size: int,
    min_rebalance_notional: float,
    spy_benchmark: dict[str, float],
    qqq_benchmark: dict[str, float],
    equal_weight_benchmark: dict[str, float],
    starting_equity: float | None = None,
) -> dict[str, Any]:
    period_starting_equity = starting_equity if starting_equity is not None else (equity_values[0] if equity_values else 0.0)
    final_equity = equity_values[-1] if equity_values else period_starting_equity
    total_return_pct = (
        ((final_equity - period_starting_equity) / period_starting_equity) * 100
        if period_starting_equity > 0
        else 0.0
    )
    cagr_pct = calculate_cagr_pct(period_starting_equity, final_equity, len(equity_values))
    max_drawdown_pct = calculate_max_drawdown(equity_values) * 100
    return {
        "source_file": "etf_rotation_results.csv",
        "strategy_name": "monthly_etf_momentum_rotation",
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "starting_equity": period_starting_equity,
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "annualised_volatility_pct": calculate_annualised_volatility_pct(equity_values),
        "sharpe_ratio": calculate_sharpe_ratio(equity_values),
        "calmar_ratio": cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0.0,
        "number_of_trades": number_of_trades,
        "turnover_proxy_trades": number_of_trades,
        "top_n": top_n,
        "universe_size": universe_size,
        "min_rebalance_notional": min_rebalance_notional,
        "spy_buy_hold_total_return_pct": spy_benchmark["total_return_pct"],
        "spy_buy_hold_cagr_pct": spy_benchmark["cagr_pct"],
        "spy_buy_hold_max_drawdown_pct": spy_benchmark["max_drawdown_pct"],
        "qqq_buy_hold_total_return_pct": qqq_benchmark["total_return_pct"],
        "qqq_buy_hold_cagr_pct": qqq_benchmark["cagr_pct"],
        "qqq_buy_hold_max_drawdown_pct": qqq_benchmark["max_drawdown_pct"],
        "equal_weight_buy_hold_total_return_pct": equal_weight_benchmark["total_return_pct"],
        "equal_weight_buy_hold_cagr_pct": equal_weight_benchmark["cagr_pct"],
        "equal_weight_buy_hold_max_drawdown_pct": equal_weight_benchmark["max_drawdown_pct"],
    }


def build_etf_rotation_period_benchmark_metrics(
    benchmark_curve: list[float],
    start_index: int,
    end_index: int,
) -> dict[str, float]:
    period_curve = benchmark_curve[start_index:end_index]
    if not period_curve:
        return empty_etf_rotation_benchmark_metrics()
    return build_etf_rotation_benchmark_metrics_from_curve(period_curve, period_curve[0])


def build_etf_rotation_benchmark_metrics(
    close_prices: list[float],
    starting_equity: float,
) -> dict[str, float]:
    return build_etf_rotation_benchmark_metrics_from_curve(
        buy_and_hold_equity_curve(close_prices, starting_equity),
        starting_equity,
    )


def build_etf_rotation_benchmark_metrics_from_curve(
    equity_curve: list[float],
    starting_equity: float,
) -> dict[str, float]:
    if not equity_curve:
        return empty_etf_rotation_benchmark_metrics()
    final_equity = equity_curve[-1]
    return {
        "total_return_pct": ((final_equity - starting_equity) / starting_equity) * 100,
        "cagr_pct": calculate_cagr_pct(starting_equity, final_equity, len(equity_curve)),
        "max_drawdown_pct": calculate_max_drawdown(equity_curve) * 100,
    }


def build_etf_rotation_trade_row(
    date: str,
    ticker: str,
    side: str,
    reason: str,
    quantity: float,
    price: float,
    cost_model: CostModel,
    min_rebalance_notional: float,
) -> dict[str, Any]:
    return {
        "date": date,
        "ticker": ticker,
        "side": side,
        "reason": reason,
        "quantity": quantity,
        "price": price,
        "commission_per_trade": cost_model.commission_per_trade,
        "commission_bps": cost_model.commission_bps,
        "spread_bps": cost_model.spread_bps,
        "slippage_bps": cost_model.slippage_bps,
        "min_rebalance_notional": min_rebalance_notional,
    }


def write_etf_rotation_outputs(
    results: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
    cost_model: CostModel,
    min_rebalance_notional: float,
) -> None:
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    with (data_dir / "etf_rotation_results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "source_file",
                "strategy_name",
                "ticker_or_portfolio",
                "period",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "starting_equity",
                "final_equity",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "annualised_volatility_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
                "turnover_proxy_trades",
                "top_n",
                "universe_size",
                "spy_buy_hold_total_return_pct",
                "spy_buy_hold_cagr_pct",
                "spy_buy_hold_max_drawdown_pct",
                "qqq_buy_hold_total_return_pct",
                "qqq_buy_hold_cagr_pct",
                "qqq_buy_hold_max_drawdown_pct",
                "equal_weight_buy_hold_total_return_pct",
                "equal_weight_buy_hold_cagr_pct",
                "equal_weight_buy_hold_max_drawdown_pct",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result["source_file"],
                    result["strategy_name"],
                    result["ticker_or_portfolio"],
                    result["period"],
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    result["min_rebalance_notional"],
                    round(result["starting_equity"], 2),
                    round(result["final_equity"], 2),
                    round(result["total_return_pct"], 4),
                    round(result["cagr_pct"], 4),
                    round(result["max_drawdown_pct"], 4),
                    round(result["annualised_volatility_pct"], 4),
                    round(result["sharpe_ratio"], 4),
                    round(result["calmar_ratio"], 4),
                    result["number_of_trades"],
                    result["turnover_proxy_trades"],
                    result["top_n"],
                    result["universe_size"],
                    round(result["spy_buy_hold_total_return_pct"], 4),
                    round(result["spy_buy_hold_cagr_pct"], 4),
                    round(result["spy_buy_hold_max_drawdown_pct"], 4),
                    round(result["qqq_buy_hold_total_return_pct"], 4),
                    round(result["qqq_buy_hold_cagr_pct"], 4),
                    round(result["qqq_buy_hold_max_drawdown_pct"], 4),
                    round(result["equal_weight_buy_hold_total_return_pct"], 4),
                    round(result["equal_weight_buy_hold_cagr_pct"], 4),
                    round(result["equal_weight_buy_hold_max_drawdown_pct"], 4),
                ]
            )

    with (data_dir / "etf_rotation_trades.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "ticker",
                "side",
                "reason",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "quantity",
                "price",
                "notional",
            ]
        )
        for trade in trades:
            writer.writerow(
                [
                    trade["date"],
                    trade["ticker"],
                    trade["side"],
                    trade["reason"],
                    trade["commission_per_trade"],
                    trade["commission_bps"],
                    trade["spread_bps"],
                    trade["slippage_bps"],
                    trade["min_rebalance_notional"],
                    round(trade["quantity"], 6),
                    round(trade["price"], 4),
                    round(trade["quantity"] * trade["price"], 2),
                ]
            )

    with (data_dir / "etf_rotation_equity_curve.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "equity",
            ]
        )
        for row in equity_curve:
            writer.writerow(
                [
                    row["date"],
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    round(row["equity"], 2),
                ]
            )


def run_adaptive_momentum_backtest(config: AppConfig, logger: logging.Logger) -> int:
    configure_yfinance_cache(config, logger)
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))
    tickers = list(dict.fromkeys([*ADAPTIVE_RISK_ASSETS, *ADAPTIVE_DEFENSIVE_ASSETS]))
    data_by_ticker = {}

    print("Adaptive risk-on/off momentum backtest")
    print(f"Tickers: {len(tickers)}")
    print(f"Top N: {ADAPTIVE_TOP_N}")

    for ticker in tickers:
        try:
            data_by_ticker[ticker] = download_backtest_prices(config, ticker)
        except Exception as exc:
            logger.error("Adaptive momentum backtest failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")

    if "SPY" not in data_by_ticker:
        write_adaptive_momentum_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("SPY regime ticker is required for adaptive momentum.")
        return 1

    tradable_tickers = [ticker for ticker in tickers if ticker in data_by_ticker]
    if len(tradable_tickers) < ADAPTIVE_TOP_N:
        write_adaptive_momentum_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("Not enough ETF data for adaptive momentum backtest.")
        return 1

    common_index = None
    for ticker in tradable_tickers:
        index = data_by_ticker[ticker].index
        common_index = index if common_index is None else common_index.intersection(index)
    common_index = common_index.sort_values()

    if len(common_index) < 254:
        write_adaptive_momentum_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print(f"Not enough shared ETF history. Need at least 254 rows, got {len(common_index)}.")
        return 1

    aligned = {
        ticker: data_by_ticker[ticker].loc[common_index]
        for ticker in tradable_tickers
    }
    rebalance_indices = get_monthly_rebalance_indices(common_index)
    if not rebalance_indices:
        write_adaptive_momentum_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("No monthly rebalance dates found.")
        return 1

    cash = config.backtest.starting_cash
    positions: dict[str, float] = {}
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []

    for index, day in enumerate(common_index):
        equity = cash + sum(
            quantity * float(aligned[ticker].iloc[index]["close"])
            for ticker, quantity in positions.items()
        )
        equity_curve.append({"date": day.date().isoformat(), "equity": equity})

        if index not in rebalance_indices or index >= len(common_index) - 1:
            continue

        price_history = {
            ticker: [float(value) for value in aligned[ticker].iloc[: index + 1]["close"]]
            for ticker in tradable_tickers
        }
        risk_prices = {
            ticker: price_history[ticker]
            for ticker in ADAPTIVE_RISK_ASSETS
            if ticker in price_history
        }
        defensive_prices = {
            ticker: price_history[ticker]
            for ticker in ADAPTIVE_DEFENSIVE_ASSETS
            if ticker in price_history
        }
        try:
            selections = select_adaptive_momentum_assets(
                risk_prices,
                defensive_prices,
                price_history["SPY"],
                top_n=ADAPTIVE_TOP_N,
            )
        except ValueError:
            continue

        target_tickers = [selection.ticker for selection in selections]
        next_index = index + 1
        next_day = common_index[next_index].date().isoformat()
        open_prices = {
            ticker: float(aligned[ticker].iloc[next_index]["open"])
            for ticker in tradable_tickers
        }
        portfolio_value = cash + sum(
            quantity * open_prices[ticker]
            for ticker, quantity in positions.items()
        )

        for ticker in sorted(set(positions) - set(target_tickers)):
            quantity = positions.pop(ticker)
            fill_price = float(adjusted_sell_fill_price(open_prices[ticker], cost_model))
            cash += quantity * fill_price
            trades.append(
                build_adaptive_momentum_trade_row(
                    next_day,
                    ticker,
                    "sell",
                    "removed_from_target_assets",
                    quantity,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

        if not target_tickers:
            continue

        target_value = portfolio_value / len(target_tickers)

        for ticker in target_tickers:
            current_quantity = positions.get(ticker, 0.0)
            current_value = current_quantity * open_prices[ticker]
            if current_value <= target_value:
                continue
            sell_value = current_value - target_value
            if should_skip_rebalance_trade(sell_value, MIN_REBALANCE_NOTIONAL):
                continue
            fill_price = float(adjusted_sell_fill_price(open_prices[ticker], cost_model))
            quantity_to_sell = min(current_quantity, sell_value / fill_price)
            if quantity_to_sell <= 0:
                continue
            positions[ticker] = current_quantity - quantity_to_sell
            cash += quantity_to_sell * fill_price
            trades.append(
                build_adaptive_momentum_trade_row(
                    next_day,
                    ticker,
                    "sell",
                    "rebalance_reduce",
                    quantity_to_sell,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

        for ticker in target_tickers:
            current_quantity = positions.get(ticker, 0.0)
            current_value = current_quantity * open_prices[ticker]
            if current_value >= target_value:
                continue
            buy_value = min(target_value - current_value, cash)
            if current_quantity > 0 and should_skip_rebalance_trade(buy_value, MIN_REBALANCE_NOTIONAL):
                continue
            fill_price = float(adjusted_buy_fill_price(open_prices[ticker], cost_model))
            quantity_to_buy = buy_value / fill_price if fill_price > 0 else 0.0
            if quantity_to_buy <= 0:
                continue
            positions[ticker] = current_quantity + quantity_to_buy
            cash -= quantity_to_buy * fill_price
            trades.append(
                build_adaptive_momentum_trade_row(
                    next_day,
                    ticker,
                    "buy",
                    "target_adaptive_asset",
                    quantity_to_buy,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

    results = build_adaptive_momentum_result_rows(
        equity_curve,
        trades,
        config.backtest.starting_cash,
        ADAPTIVE_TOP_N,
        len(tradable_tickers),
        MIN_REBALANCE_NOTIONAL,
        {
            "spy": buy_and_hold_equity_curve(
                [float(value) for value in aligned["SPY"]["close"]],
                config.backtest.starting_cash,
            ),
            "qqq": (
                buy_and_hold_equity_curve(
                    [float(value) for value in aligned["QQQ"]["close"]],
                    config.backtest.starting_cash,
                )
                if "QQQ" in aligned
                else []
            ),
            "equal_weight": equal_weight_buy_and_hold_equity_curve(
                {
                    ticker: [float(value) for value in aligned[ticker]["close"]]
                    for ticker in tradable_tickers
                },
                config.backtest.starting_cash,
            ),
        },
    )

    write_adaptive_momentum_outputs(results, trades, equity_curve, cost_model, MIN_REBALANCE_NOTIONAL)
    full_period_result = next(
        (result for result in results if result.get("period") == "full_period"),
        results[0],
    )
    print(
        "adaptive_risk_on_off_momentum,"
        f"{full_period_result['total_return_pct']:.2f}%,"
        f"{full_period_result['max_drawdown_pct']:.2f}%,"
        f"{len(trades)} trades"
    )
    print("Saved adaptive momentum results to data/adaptive_momentum_results.csv")
    print("Saved adaptive momentum trades to data/adaptive_momentum_trades.csv")
    print("Saved adaptive momentum equity curve to data/adaptive_momentum_equity_curve.csv")
    return 0


def empty_research_metrics() -> dict[str, float]:
    return {
        "final_equity": 0.0,
        "total_return_pct": 0.0,
        "cagr_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "annualised_volatility_pct": 0.0,
        "sharpe_ratio": 0.0,
        "calmar_ratio": 0.0,
    }


def build_adaptive_momentum_result_rows(
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    starting_equity: float,
    top_n: int,
    universe_size: int,
    min_rebalance_notional: float,
    benchmark_curves: dict[str, list[float]] | None = None,
) -> list[dict[str, Any]]:
    """Build reporting-only full/in/out rows from one adaptive backtest run."""
    benchmark_curves = benchmark_curves or {}
    rows = []
    for period_name, start_index, end_index in adaptive_momentum_period_slices(equity_curve):
        period_curve = equity_curve[start_index:end_index]
        equity_values = [float(row["equity"]) for row in period_curve]
        period_starting_equity = equity_values[0] if equity_values else starting_equity
        period_trades = filter_etf_rotation_trades_for_period(
            trades,
            period_curve[0]["date"] if period_curve else None,
            period_curve[-1]["date"] if period_curve else None,
        )
        rows.append(
            build_adaptive_momentum_result_row(
                period_name,
                equity_values,
                len(period_trades),
                top_n,
                universe_size,
                min_rebalance_notional,
                build_adaptive_momentum_period_benchmark_metrics(
                    benchmark_curves.get("spy", []),
                    start_index,
                    end_index,
                ),
                build_adaptive_momentum_period_benchmark_metrics(
                    benchmark_curves.get("qqq", []),
                    start_index,
                    end_index,
                ),
                build_adaptive_momentum_period_benchmark_metrics(
                    benchmark_curves.get("equal_weight", []),
                    start_index,
                    end_index,
                ),
                period_starting_equity,
            )
        )
    return rows


def adaptive_momentum_period_slices(equity_curve: list[dict[str, Any]]) -> list[tuple[str, int, int]]:
    return etf_rotation_period_slices(equity_curve)


def build_adaptive_momentum_period_benchmark_metrics(
    benchmark_curve: list[float],
    start_index: int,
    end_index: int,
) -> dict[str, float]:
    period_curve = benchmark_curve[start_index:end_index]
    if not period_curve:
        return empty_research_metrics()
    return build_research_equity_metrics(period_curve, period_curve[0])


def build_adaptive_momentum_result_row(
    period: str,
    equity_values: list[float],
    number_of_trades: int,
    top_n: int,
    universe_size: int,
    min_rebalance_notional: float,
    spy_benchmark: dict[str, float],
    qqq_benchmark: dict[str, float],
    equal_weight_benchmark: dict[str, float],
    starting_equity: float | None = None,
) -> dict[str, Any]:
    period_starting_equity = starting_equity if starting_equity is not None else (equity_values[0] if equity_values else 0.0)
    strategy_metrics = build_research_equity_metrics(equity_values, period_starting_equity)
    return {
        "source_file": "adaptive_momentum_results.csv",
        "strategy_name": "adaptive_risk_on_off_momentum",
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "starting_equity": period_starting_equity,
        "final_equity": strategy_metrics["final_equity"],
        "number_of_trades": number_of_trades,
        "turnover_proxy_trades": number_of_trades,
        "top_n": top_n,
        "universe_size": universe_size,
        "min_rebalance_notional": min_rebalance_notional,
        **strategy_metrics,
        "spy": spy_benchmark,
        "qqq": qqq_benchmark,
        "equal_weight": equal_weight_benchmark,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_research_equity_metrics(
    equity_curve: list[float],
    starting_equity: float,
) -> dict[str, float]:
    if not equity_curve:
        return empty_research_metrics()
    final_equity = equity_curve[-1]
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    cagr_pct = calculate_cagr_pct(starting_equity, final_equity, len(equity_curve))
    return {
        "final_equity": final_equity,
        "total_return_pct": ((final_equity - starting_equity) / starting_equity) * 100,
        "cagr_pct": cagr_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "annualised_volatility_pct": calculate_annualised_volatility_pct(equity_curve),
        "sharpe_ratio": calculate_sharpe_ratio(equity_curve),
        "calmar_ratio": cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0.0,
    }


def relative_metric(value: float, benchmark_value: float) -> float:
    return value - benchmark_value


def build_adaptive_momentum_trade_row(
    date: str,
    ticker: str,
    side: str,
    reason: str,
    quantity: float,
    price: float,
    cost_model: CostModel,
    min_rebalance_notional: float,
) -> dict[str, Any]:
    return {
        "date": date,
        "ticker": ticker,
        "side": side,
        "reason": reason,
        "quantity": quantity,
        "price": price,
        "commission_per_trade": cost_model.commission_per_trade,
        "commission_bps": cost_model.commission_bps,
        "spread_bps": cost_model.spread_bps,
        "slippage_bps": cost_model.slippage_bps,
        "min_rebalance_notional": min_rebalance_notional,
    }


def write_adaptive_momentum_outputs(
    results: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
    cost_model: CostModel,
    min_rebalance_notional: float,
) -> None:
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    with (data_dir / "adaptive_momentum_results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "source_file",
                "strategy_name",
                "ticker_or_portfolio",
                "period",
                "starting_equity",
                "final_equity",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "annualised_volatility_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
                "turnover_proxy_trades",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "spy_benchmark_total_return_pct",
                "spy_benchmark_cagr_pct",
                "spy_benchmark_max_drawdown_pct",
                "spy_benchmark_sharpe_ratio",
                "spy_benchmark_calmar_ratio",
                "qqq_benchmark_total_return_pct",
                "qqq_benchmark_cagr_pct",
                "qqq_benchmark_max_drawdown_pct",
                "qqq_benchmark_sharpe_ratio",
                "qqq_benchmark_calmar_ratio",
                "equal_weight_benchmark_total_return_pct",
                "equal_weight_benchmark_cagr_pct",
                "equal_weight_benchmark_max_drawdown_pct",
                "equal_weight_benchmark_sharpe_ratio",
                "equal_weight_benchmark_calmar_ratio",
                "relative_cagr_vs_spy_pct",
                "relative_max_drawdown_vs_spy_pct",
                "relative_calmar_vs_spy",
                "relative_cagr_vs_qqq_pct",
                "relative_max_drawdown_vs_qqq_pct",
                "relative_calmar_vs_qqq",
                "relative_cagr_vs_equal_weight_pct",
                "relative_max_drawdown_vs_equal_weight_pct",
                "relative_calmar_vs_equal_weight",
                "top_n",
                "universe_size",
                "research_only",
                "preview_only",
                "execution_approved",
            ]
        )
        for result in results:
            spy = result["spy"]
            qqq = result["qqq"]
            equal_weight = result["equal_weight"]
            writer.writerow(
                [
                    result["source_file"],
                    result["strategy_name"],
                    result["ticker_or_portfolio"],
                    result["period"],
                    round(result["starting_equity"], 2),
                    round(result["final_equity"], 2),
                    round(result["total_return_pct"], 4),
                    round(result["cagr_pct"], 4),
                    round(result["max_drawdown_pct"], 4),
                    round(result["annualised_volatility_pct"], 4),
                    round(result["sharpe_ratio"], 4),
                    round(result["calmar_ratio"], 4),
                    result["number_of_trades"],
                    result["turnover_proxy_trades"],
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    min_rebalance_notional,
                    round(spy["total_return_pct"], 4),
                    round(spy["cagr_pct"], 4),
                    round(spy["max_drawdown_pct"], 4),
                    round(spy["sharpe_ratio"], 4),
                    round(spy["calmar_ratio"], 4),
                    round(qqq["total_return_pct"], 4),
                    round(qqq["cagr_pct"], 4),
                    round(qqq["max_drawdown_pct"], 4),
                    round(qqq["sharpe_ratio"], 4),
                    round(qqq["calmar_ratio"], 4),
                    round(equal_weight["total_return_pct"], 4),
                    round(equal_weight["cagr_pct"], 4),
                    round(equal_weight["max_drawdown_pct"], 4),
                    round(equal_weight["sharpe_ratio"], 4),
                    round(equal_weight["calmar_ratio"], 4),
                    round(relative_metric(result["cagr_pct"], spy["cagr_pct"]), 4),
                    round(relative_metric(result["max_drawdown_pct"], spy["max_drawdown_pct"]), 4),
                    round(relative_metric(result["calmar_ratio"], spy["calmar_ratio"]), 4),
                    round(relative_metric(result["cagr_pct"], qqq["cagr_pct"]), 4),
                    round(relative_metric(result["max_drawdown_pct"], qqq["max_drawdown_pct"]), 4),
                    round(relative_metric(result["calmar_ratio"], qqq["calmar_ratio"]), 4),
                    round(relative_metric(result["cagr_pct"], equal_weight["cagr_pct"]), 4),
                    round(relative_metric(result["max_drawdown_pct"], equal_weight["max_drawdown_pct"]), 4),
                    round(relative_metric(result["calmar_ratio"], equal_weight["calmar_ratio"]), 4),
                    result["top_n"],
                    result["universe_size"],
                    result["research_only"],
                    result["preview_only"],
                    result["execution_approved"],
                ]
            )

    with (data_dir / "adaptive_momentum_trades.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "ticker",
                "side",
                "reason",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "quantity",
                "price",
                "notional",
            ]
        )
        for trade in trades:
            writer.writerow(
                [
                    trade["date"],
                    trade["ticker"],
                    trade["side"],
                    trade["reason"],
                    trade["commission_per_trade"],
                    trade["commission_bps"],
                    trade["spread_bps"],
                    trade["slippage_bps"],
                    trade["min_rebalance_notional"],
                    round(trade["quantity"], 6),
                    round(trade["price"], 4),
                    round(trade["quantity"] * trade["price"], 2),
                ]
            )

    with (data_dir / "adaptive_momentum_equity_curve.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "equity",
            ]
        )
        for row in equity_curve:
            writer.writerow(
                [
                    row["date"],
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    min_rebalance_notional,
                    round(row["equity"], 2),
                ]
            )


def backtest_ticker(
    config: AppConfig,
    ticker: str,
    ticker_data,
    regime_data,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    strategy = config.strategy
    actual_slippage_bps = config.backtest.slippage_bps if cost_model is None else float(cost_model.slippage_bps)
    slippage = actual_slippage_bps / 10000

    data = ticker_data.join(regime_data[["close"]].rename(columns={"close": "regime_close"}), how="inner")
    data["short_sma"] = data["close"].rolling(strategy.short_window).mean()
    data["long_sma"] = data["close"].rolling(strategy.long_window).mean()
    data["trend_sma"] = data["close"].rolling(strategy.trend_window).mean()
    data["regime_sma"] = data["regime_close"].rolling(strategy.trend_window).mean()
    data["realised_vol_20"] = data["close"].pct_change().rolling(strategy.vol_window).std() * math.sqrt(252)
    data["median_vol"] = data["realised_vol_20"].rolling(strategy.vol_median_window).median()
    data = data.dropna()

    if len(data) < 2:
        raise RuntimeError("Not enough aligned indicator data after calculating filters.")

    cash = config.backtest.position_size_dollars
    shares = 0.0
    entry_date = ""
    entry_price = 0.0
    entry_reason = ""
    position_days = 0
    daily_pnl: list[tuple[str, float]] = []
    equity_curve: list[float] = []
    trades: list[BacktestTrade] = []

    for index in range(1, len(data) - 1):
        today = data.iloc[index]
        yesterday = data.iloc[index - 1]
        next_day = data.iloc[index + 1]
        today_label = data.index[index].date().isoformat()
        next_label = data.index[index + 1].date().isoformat()

        if shares > 0:
            position_days += 1

        equity = cash + shares * float(today["close"])
        equity_curve.append(equity)
        daily_pnl.append((today_label, equity - config.backtest.position_size_dollars))

        # Market regime filter: only allow new longs when the broad market is above its 200-day trend.
        market_regime_ok = float(today["regime_close"]) > float(today["regime_sma"])

        # Ticker trend filter: avoid new longs when the ticker itself is below its 200-day trend.
        ticker_trend_ok = float(today["close"]) > float(today["trend_sma"])

        # Crossover trigger: require a true 20-day SMA cross above the 50-day SMA.
        signal = detect_sma_signal(
            float(yesterday["short_sma"]),
            float(yesterday["long_sma"]),
            float(today["short_sma"]),
            float(today["long_sma"]),
        )

        # Volatility gate: skip new entries when recent volatility is unusually high.
        volatility_ok = float(today["realised_vol_20"]) <= (
            strategy.vol_gate_multiple * float(today["median_vol"])
        )

        exit_signal = signal == SIGNAL_SELL
        exit_trend_break = float(today["close"]) < float(today["trend_sma"])

        # Signals use today's close, but trades execute at the next open. That delay is
        # what avoids look-ahead bias: the test never trades at a price from before the signal existed.
        if shares == 0 and market_regime_ok and ticker_trend_ok and signal == SIGNAL_BUY and volatility_ok:
            execution_price = (
                float(adjusted_buy_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 + slippage)
            )
            allocation = min(config.backtest.position_size_dollars, cash)
            if execution_price > 0 and allocation > 0:
                shares = allocation / execution_price
                cash -= allocation
                entry_date = next_label
                entry_price = execution_price
                entry_reason = "regime_ok,trending,crossover_up,vol_ok"
        elif shares > 0 and (exit_signal or exit_trend_break):
            execution_price = (
                float(adjusted_sell_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 - slippage)
            )
            proceeds = shares * execution_price
            pnl = proceeds - (shares * entry_price)
            trade_return_pct = ((execution_price - entry_price) / entry_price) * 100
            cash += proceeds
            trades.append(
                BacktestTrade(
                    ticker=ticker,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=next_label,
                    exit_price=execution_price,
                    quantity=shares,
                    entry_reason=entry_reason,
                    exit_reason="crossover_down" if exit_signal else "trend_break",
                    trade_return_pct=trade_return_pct,
                    pnl=pnl,
                )
            )
            shares = 0.0
            entry_date = ""
            entry_price = 0.0
            entry_reason = ""

    final_close = float(data.iloc[-1]["close"])
    final_equity = cash + shares * final_close
    equity_curve.append(final_equity)
    daily_pnl.append((data.index[-1].date().isoformat(), final_equity - config.backtest.position_size_dollars))

    closed_returns = [trade.trade_return_pct for trade in trades]
    wins = [value for value in closed_returns if value > 0]
    total_return_pct = ((final_equity - config.backtest.position_size_dollars) / config.backtest.position_size_dollars) * 100
    buy_and_hold_return_pct = ((final_close - float(data.iloc[0]["close"])) / float(data.iloc[0]["close"])) * 100
    win_rate_pct = (len(wins) / len(closed_returns) * 100) if closed_returns else 0.0
    average_trade_return_pct = sum(closed_returns) / len(closed_returns) if closed_returns else 0.0
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    time_in_market_pct = (position_days / max(len(data), 1)) * 100

    result = BacktestResult(
        ticker=ticker,
        period="full_period",
        total_return_pct=total_return_pct,
        buy_and_hold_return_pct=buy_and_hold_return_pct,
        number_of_trades=len(trades),
        win_rate_pct=win_rate_pct,
        average_trade_return_pct=average_trade_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        final_equity=final_equity,
        time_in_market_pct=time_in_market_pct,
        pnl=final_equity - config.backtest.position_size_dollars,
        daily_pnl=daily_pnl,
    )
    result.slippage_bps = actual_slippage_bps
    return result, trades


def run_strategy_comparison(
    config: AppConfig,
    logger: logging.Logger,
    force_research_universe: bool = False,
) -> int:
    configure_yfinance_cache(config, logger)
    strategy_names = [
        "buy_and_hold_baseline",
        "sma_20_50_basic",
        "sma_20_50_regime",
        "sma_50_200_trend",
        "buy_above_200_exit_below_200",
        "fifty_two_week_high_breakout",
    ]
    results: list[BacktestResult] = []
    trades: list[BacktestTrade] = []
    portfolio_results: list[StrategyPortfolioResult] = []
    errors: list[str] = []
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))

    comparison_tickers = get_strategy_comparison_tickers(config, force_research_universe)

    print("Strategy comparison backtest")
    print(f"Tickers: {len(comparison_tickers)}")

    try:
        regime_data = download_backtest_prices(config, config.strategy.regime_ticker)
    except Exception as exc:
        logger.error("Strategy comparison failed: could not download regime ticker %s: %s", config.strategy.regime_ticker, exc)
        write_strategy_comparison_results(results, cost_model)
        write_strategy_comparison_trades(trades, cost_model)
        write_strategy_portfolio_comparison(portfolio_results, cost_model)
        write_strategy_robustness_summary([], cost_model)
        write_strategy_ticker_equity_curves(results, config)
        write_strategy_portfolio_equity_curves(config, results)
        print(f"Regime ticker error: {config.strategy.regime_ticker} - {exc}")
        return 1

    for ticker in comparison_tickers:
        try:
            ticker_data = download_backtest_prices(config, ticker)
        except Exception as exc:
            errors.append(ticker)
            logger.error("Strategy comparison failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            continue

        try:
            comparison_data = prepare_strategy_comparison_data(ticker_data, regime_data)
        except Exception as exc:
            errors.append(ticker)
            logger.error("Strategy comparison setup failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            continue

        for strategy_name in strategy_names:
            try:
                full_result, strategy_trades = compare_strategy_ticker(
                    config,
                    ticker,
                    comparison_data,
                    strategy_name,
                    cost_model,
                )
                results.extend(
                    build_period_comparison_results(
                        config,
                        full_result,
                        comparison_data,
                        strategy_trades,
                    )
                )
                trades.extend(strategy_trades)
            except Exception as exc:
                errors.append(f"{ticker}:{strategy_name}")
                logger.error("Strategy comparison failed for %s %s: %s", ticker, strategy_name, exc)
                print(f"{ticker},{strategy_name},ERROR,{exc}")

    write_strategy_comparison_results(results, cost_model)
    write_strategy_comparison_trades(trades, cost_model)
    portfolio_results = build_strategy_portfolio_results(config, results)
    robustness_results = build_strategy_robustness_summary(results)
    write_strategy_portfolio_comparison(portfolio_results, cost_model)
    write_strategy_robustness_summary(robustness_results, cost_model)
    write_strategy_ticker_equity_curves(results, config)
    write_strategy_portfolio_equity_curves(config, results)
    print_ranked_strategy_summary(results)
    print_ranked_portfolio_summary(portfolio_results)
    print_ranked_robustness_summary(robustness_results)
    print("")
    print("Saved results to data/strategy_comparison_results.csv")
    print("Saved trades to data/strategy_comparison_trades.csv")
    print("Saved portfolio comparison to data/strategy_portfolio_comparison.csv")
    print("Saved robustness summary to data/strategy_robustness_summary.csv")
    print("Saved portfolio equity curves to data/strategy_portfolio_equity_curves.csv")
    print("Saved ticker equity curves to data/strategy_ticker_equity_curves.csv")
    print(f"Tickers with errors: {len(errors)}")
    return 0 if results else 1


def get_strategy_comparison_tickers(
    config: AppConfig,
    force_research_universe: bool,
) -> list[str]:
    # Testing only AAPL/MSFT/SPY is too narrow: a strategy can look good on a
    # handful of familiar names and still fail across sectors, styles, and ETFs.
    # This research universe is for backtesting only and must never change the
    # live/paper trading ticker list used by normal bot runs.
    if force_research_universe or config.research_universe.enabled:
        return config.research_universe.tickers or default_research_universe_tickers()
    return config.tickers


def run_sma_sensitivity(
    config: AppConfig,
    logger: logging.Logger,
    force_research_universe: bool = False,
) -> int:
    configure_yfinance_cache(config, logger)
    results: list[BacktestResult] = []
    errors: list[str] = []
    tickers = get_strategy_comparison_tickers(config, force_research_universe)

    # Parameter sensitivity matters because one SMA pair can win one historical
    # test by chance. We want nearby parameter choices to behave reasonably too.
    # Avoid choosing a single pair purely because it won one backtest; that can
    # be a sign of overfitting instead of a durable trading idea.
    print("SMA parameter sensitivity backtest")
    print(f"Tickers: {len(tickers)}")
    print("Pairs: " + ", ".join(f"{short}/{long}" for short, long in SMA_SENSITIVITY_PAIRS))

    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))

    for ticker in tickers:
        try:
            ticker_data = download_backtest_prices(config, ticker)
            sensitivity_data = prepare_sma_sensitivity_data(ticker_data)
        except Exception as exc:
            errors.append(ticker)
            logger.error("SMA sensitivity setup failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            continue

        for short_window, long_window in SMA_SENSITIVITY_PAIRS:
            try:
                full_result, trades = compare_sma_pair_ticker(
                    config,
                    ticker,
                    sensitivity_data,
                    short_window,
                    long_window,
                    cost_model=cost_model,
                )
                results.extend(
                    build_period_comparison_results(
                        config,
                        full_result,
                        sensitivity_data,
                        trades,
                    )
                )
            except Exception as exc:
                errors.append(f"{ticker}:{short_window}/{long_window}")
                logger.error(
                    "SMA sensitivity failed for %s %s/%s: %s",
                    ticker,
                    short_window,
                    long_window,
                    exc,
                )
                print(f"{ticker},{short_window}/{long_window},ERROR,{exc}")

    portfolio_results = build_strategy_portfolio_results(config, results)
    write_sma_sensitivity_results(results, cost_model)
    write_sma_sensitivity_portfolio(portfolio_results, cost_model)
    print_ranked_sma_sensitivity_summary(portfolio_results)
    print("")
    print("Saved SMA sensitivity results to data/sma_sensitivity_results.csv")
    print("Saved SMA sensitivity portfolio results to data/sma_sensitivity_portfolio.csv")
    print(f"Tickers with errors: {len(errors)}")
    return 0 if results else 1


def run_trend_stress_test(
    config: AppConfig,
    logger: logging.Logger,
    force_research_universe: bool = False,
    force_etf_universe: bool = False,
) -> int:
    configure_yfinance_cache(config, logger)
    universe_name, tickers = get_trend_stress_test_universe(
        config,
        force_research_universe,
        force_etf_universe,
    )
    results: list[BacktestResult] = []
    errors: list[str] = []

    print("Slow SMA trend stress test")
    print(f"Universe: {universe_name}")
    print(f"Tickers: {len(tickers)}")
    print("Pairs: " + ", ".join(f"{short}/{long}" for short, long in TREND_STRESS_TEST_PAIRS))
    print("Slippage bps: " + ", ".join(str(value) for value in TREND_STRESS_TEST_SLIPPAGE_BPS))

    for ticker in tickers:
        try:
            ticker_data = download_backtest_prices(config, ticker)
            stress_data = prepare_trend_stress_test_data(ticker_data)
        except Exception as exc:
            errors.append(ticker)
            logger.error("Trend stress test setup failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            continue

        # Prefer parameter clusters over one winning setting. If several nearby
        # slow SMA pairs behave well, the idea is more convincing than a single
        # best backtest row.
        for short_window, long_window in TREND_STRESS_TEST_PAIRS:
            # Slippage sensitivity matters because real fills are never perfect;
            # a strategy that only works at zero cost may be too fragile.
            for slippage_bps in TREND_STRESS_TEST_SLIPPAGE_BPS:
                try:
                    cost_model = CostModel(slippage_bps=Decimal(str(slippage_bps)))
                    strategy_name = trend_stress_strategy_name(
                        short_window,
                        long_window,
                        slippage_bps,
                    )
                    full_result, trades = compare_sma_pair_ticker(
                        config,
                        ticker,
                        stress_data,
                        short_window,
                        long_window,
                        slippage_bps=slippage_bps,
                        strategy_name=strategy_name,
                        cost_model=cost_model,
                    )
                    results.extend(
                        build_period_comparison_results(
                            config,
                            full_result,
                            stress_data,
                            trades,
                        )
                    )
                except Exception as exc:
                    errors.append(f"{ticker}:{short_window}/{long_window}:{slippage_bps}")
                    logger.error(
                        "Trend stress test failed for %s %s/%s %s bps: %s",
                        ticker,
                        short_window,
                        long_window,
                        slippage_bps,
                        exc,
                    )
                    print(f"{ticker},{short_window}/{long_window},{slippage_bps},ERROR,{exc}")

    portfolio_results = build_strategy_portfolio_results(config, results)
    write_trend_stress_test_results(results, universe_name)
    write_trend_stress_test_portfolio(portfolio_results, universe_name)
    print_ranked_trend_stress_test_summary(portfolio_results)
    print("")
    print("Saved trend stress test results to data/trend_stress_test_results.csv")
    print("Saved trend stress test portfolio results to data/trend_stress_test_portfolio.csv")
    print(f"Tickers with errors: {len(errors)}")
    return 0 if results else 1


def get_trend_stress_test_universe(
    config: AppConfig,
    force_research_universe: bool,
    force_etf_universe: bool,
) -> tuple[str, list[str]]:
    if force_research_universe and force_etf_universe:
        raise ConfigError("Choose either --research-universe or --etf-universe, not both.")

    if force_etf_universe:
        # ETF-only testing can reduce survivorship bias because broad index and
        # sector ETFs represent markets and asset classes, not just today's
        # surviving popular stocks.
        return "etf_research_universe", config.etf_research_universe.tickers or []

    if force_research_universe:
        return "research_universe", config.research_universe.tickers or []

    return "config_tickers", config.tickers


def compare_sma_pair_ticker(
    config: AppConfig,
    ticker: str,
    data,
    short_window: int,
    long_window: int,
    slippage_bps: float | None = None,
    strategy_name: str | None = None,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    actual_slippage_bps = config.backtest.slippage_bps if slippage_bps is None else slippage_bps
    slippage = actual_slippage_bps / 10000
    short_column = f"sma{short_window}"
    long_column = f"sma{long_window}"

    if len(data) < 3:
        raise RuntimeError("Not enough SMA sensitivity data.")

    cash = config.backtest.position_size_dollars
    shares = 0.0
    entry_date = ""
    entry_price = 0.0
    entry_reason = ""
    position_days = 0
    dated_equity_curve: list[tuple[str, float]] = []
    dated_exposure: list[tuple[str, bool]] = []
    trades: list[BacktestTrade] = []
    strategy_name = strategy_name or sma_sensitivity_strategy_name(short_window, long_window)

    for index in range(1, len(data) - 1):
        today = data.iloc[index]
        yesterday = data.iloc[index - 1]
        next_day = data.iloc[index + 1]
        next_label = data.index[index + 1].date().isoformat()

        if shares > 0:
            position_days += 1

        today_date = data.index[index].date().isoformat()
        dated_equity_curve.append((today_date, cash + shares * float(today["close"])))
        dated_exposure.append((today_date, shares > 0))

        entry_signal = crossed_above(
            float(yesterday[short_column]),
            float(yesterday[long_column]),
            float(today[short_column]),
            float(today[long_column]),
        )
        exit_signal = crossed_below(
            float(yesterday[short_column]),
            float(yesterday[long_column]),
            float(today[short_column]),
            float(today[long_column]),
        )

        # Sensitivity testing uses the same long-only, next-day open execution
        # assumption as the strategy comparison command.
        if shares == 0 and entry_signal:
            execution_price = (
                float(adjusted_buy_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 + slippage)
            )
            if execution_price > 0 and cash > 0:
                shares = cash / execution_price
                cash = 0.0
                entry_date = next_label
                entry_price = execution_price
                entry_reason = f"sma{short_window}_cross_above_sma{long_window}"
        elif shares > 0 and exit_signal:
            execution_price = (
                float(adjusted_sell_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 - slippage)
            )
            proceeds = shares * execution_price
            pnl = proceeds - (shares * entry_price)
            trade_return_pct = ((execution_price - entry_price) / entry_price) * 100
            cash += proceeds
            trades.append(
                BacktestTrade(
                    ticker=ticker,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=next_label,
                    exit_price=execution_price,
                    quantity=shares,
                    entry_reason=entry_reason,
                    exit_reason=f"sma{short_window}_cross_below_sma{long_window}",
                    trade_return_pct=trade_return_pct,
                    pnl=pnl,
                    strategy_name=strategy_name,
                )
            )
            shares = 0.0
            entry_date = ""
            entry_price = 0.0
            entry_reason = ""

    final_close = float(data.iloc[-1]["close"])
    final_equity = cash + shares * final_close
    final_date = data.index[-1].date().isoformat()
    dated_equity_curve.append((final_date, final_equity))
    dated_exposure.append((final_date, shares > 0))

    result = build_comparison_result(
        config,
        ticker,
        strategy_name,
        data,
        trades,
        dated_equity_curve,
        dated_exposure,
        final_equity,
        position_days,
    )
    result.short_window = short_window
    result.long_window = long_window
    result.slippage_bps = actual_slippage_bps
    return result, trades


def compare_strategy_ticker(
    config: AppConfig,
    ticker: str,
    data,
    strategy_name: str,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    if strategy_name == "buy_and_hold_baseline":
        return compare_buy_and_hold_ticker(config, ticker, data, strategy_name, cost_model)
    if strategy_name == "fifty_two_week_high_breakout":
        return compare_breakout_ticker(config, ticker, data, strategy_name, cost_model)

    actual_slippage_bps = config.backtest.slippage_bps if cost_model is None else float(cost_model.slippage_bps)
    slippage = actual_slippage_bps / 10000

    if len(data) < 3:
        raise RuntimeError("Not enough indicator data for strategy comparison.")

    cash = config.backtest.position_size_dollars
    shares = 0.0
    entry_date = ""
    entry_price = 0.0
    entry_reason = ""
    position_days = 0
    dated_equity_curve: list[tuple[str, float]] = []
    dated_exposure: list[tuple[str, bool]] = []
    trades: list[BacktestTrade] = []

    for index in range(1, len(data) - 1):
        today = data.iloc[index]
        yesterday = data.iloc[index - 1]
        next_day = data.iloc[index + 1]
        next_label = data.index[index + 1].date().isoformat()

        if shares > 0:
            position_days += 1
        today_date = data.index[index].date().isoformat()
        dated_equity_curve.append((today_date, cash + shares * float(today["close"])))
        dated_exposure.append((today_date, shares > 0))

        entry_signal, entry_reason_candidate = comparison_entry_signal(strategy_name, yesterday, today)
        exit_signal, exit_reason = comparison_exit_signal(strategy_name, yesterday, today)

        # All comparison strategies use next-day open execution. The signal is known
        # after today's close, so trading tomorrow's open avoids look-ahead bias.
        if shares == 0 and entry_signal:
            execution_price = (
                float(adjusted_buy_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 + slippage)
            )
            if execution_price > 0 and cash > 0:
                shares = cash / execution_price
                cash = 0.0
                entry_date = next_label
                entry_price = execution_price
                entry_reason = entry_reason_candidate
        elif shares > 0 and exit_signal:
            execution_price = (
                float(adjusted_sell_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 - slippage)
            )
            proceeds = shares * execution_price
            pnl = proceeds - (shares * entry_price)
            trade_return_pct = ((execution_price - entry_price) / entry_price) * 100
            cash += proceeds
            trades.append(
                BacktestTrade(
                    ticker=ticker,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=next_label,
                    exit_price=execution_price,
                    quantity=shares,
                    entry_reason=entry_reason,
                    exit_reason=exit_reason,
                    trade_return_pct=trade_return_pct,
                    pnl=pnl,
                    strategy_name=strategy_name,
                )
            )
            shares = 0.0
            entry_date = ""
            entry_price = 0.0
            entry_reason = ""

    final_close = float(data.iloc[-1]["close"])
    final_equity = cash + shares * final_close
    final_date = data.index[-1].date().isoformat()
    dated_equity_curve.append((final_date, final_equity))
    dated_exposure.append((final_date, shares > 0))

    result = build_comparison_result(
        config,
        ticker,
        strategy_name,
        data,
        trades,
        dated_equity_curve,
        dated_exposure,
        final_equity,
        position_days,
    )
    result.slippage_bps = actual_slippage_bps
    return result, trades


def compare_breakout_ticker(
    config: AppConfig,
    ticker: str,
    data,
    strategy_name: str,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    actual_slippage_bps = config.backtest.slippage_bps if cost_model is None else float(cost_model.slippage_bps)

    if len(data) < 253:
        raise RuntimeError("Not enough shared comparison data for 52-week breakout.")

    cash = config.backtest.position_size_dollars
    shares = 0.0
    entry_date = ""
    entry_price = 0.0
    entry_reason = ""
    highest_close_since_entry = 0.0
    position_days = 0
    dated_equity_curve: list[tuple[str, float]] = []
    dated_exposure: list[tuple[str, bool]] = []
    trades: list[BacktestTrade] = []

    ohlcv_rows = [
        {
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row.get("volume", 0.0)),
        }
        for _, row in data.iterrows()
    ]

    for index in range(1, len(data) - 1):
        today = data.iloc[index]
        next_day = data.iloc[index + 1]
        today_date = data.index[index].date().isoformat()
        next_label = data.index[index + 1].date().isoformat()
        history = ohlcv_rows[: index + 1]

        if shares > 0:
            position_days += 1
            highest_close_since_entry = max(highest_close_since_entry, float(today["close"]))

        dated_equity_curve.append((today_date, cash + shares * float(today["close"])))
        dated_exposure.append((today_date, shares > 0))

        entered_today = False
        if (
            shares == 0
            and len(history) >= 252
            and is_252_day_high_breakout(history)
            and volume_confirmation(history, multiplier=1.0)
        ):
            execution_price = adjusted_breakout_buy_fill(float(next_day["open"]), cost_model)
            if execution_price > 0 and cash > 0:
                shares = cash / execution_price
                cash = 0.0
                entry_date = next_label
                entry_price = execution_price
                entry_reason = "252_day_high_breakout,volume_confirmed"
                highest_close_since_entry = float(today["close"])
                entered_today = True

        # This candidate is long-only and does not pyramid. Once long, new
        # breakouts are ignored until an exit condition closes the position.
        if shares > 0 and not entered_today:
            exit_reason = ""
            if len(history) >= 100 and sma_100_exit(history):
                exit_reason = "close_below_100_sma"
            elif len(history) >= 20 and atr_trailing_stop_exit(history, highest_close_since_entry):
                exit_reason = "atr_trailing_stop"

            if exit_reason:
                execution_price = adjusted_breakout_sell_fill(float(next_day["open"]), cost_model)
                proceeds = shares * execution_price
                pnl = proceeds - (shares * entry_price)
                trade_return_pct = ((execution_price - entry_price) / entry_price) * 100
                cash += proceeds
                trades.append(
                    BacktestTrade(
                        ticker=ticker,
                        entry_date=entry_date,
                        entry_price=entry_price,
                        exit_date=next_label,
                        exit_price=execution_price,
                        quantity=shares,
                        entry_reason=entry_reason,
                        exit_reason=exit_reason,
                        trade_return_pct=trade_return_pct,
                        pnl=pnl,
                        strategy_name=strategy_name,
                    )
                )
                shares = 0.0
                entry_date = ""
                entry_price = 0.0
                entry_reason = ""
                highest_close_since_entry = 0.0

    final_close = float(data.iloc[-1]["close"])
    final_equity = cash + shares * final_close
    final_date = data.index[-1].date().isoformat()
    dated_equity_curve.append((final_date, final_equity))
    dated_exposure.append((final_date, shares > 0))

    result = build_comparison_result(
        config,
        ticker,
        strategy_name,
        data,
        trades,
        dated_equity_curve,
        dated_exposure,
        final_equity,
        position_days,
    )
    result.slippage_bps = actual_slippage_bps
    return result, trades


def compare_buy_and_hold_ticker(
    config: AppConfig,
    ticker: str,
    ticker_data,
    strategy_name: str,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    data = ticker_data.dropna()
    if len(data) < 2:
        raise RuntimeError("Not enough data for buy-and-hold baseline.")

    actual_slippage_bps = config.backtest.slippage_bps if cost_model is None else float(cost_model.slippage_bps)
    slippage = actual_slippage_bps / 10000

    # Buy-and-hold is included as a benchmark. If an active strategy cannot beat
    # simply buying once and holding, the extra trading complexity may not be worth it.
    entry_row = data.iloc[0]
    exit_row = data.iloc[-1]
    entry_price = (
        float(adjusted_buy_fill_price(float(entry_row["open"]), cost_model))
        if cost_model is not None
        else float(entry_row["open"]) * (1 + slippage)
    )
    exit_price = (
        float(adjusted_sell_fill_price(float(exit_row["open"]), cost_model))
        if cost_model is not None
        else float(exit_row["open"]) * (1 - slippage)
    )
    shares = config.backtest.position_size_dollars / entry_price
    final_equity = shares * exit_price
    pnl = final_equity - config.backtest.position_size_dollars
    trade_return_pct = ((exit_price - entry_price) / entry_price) * 100

    trade = BacktestTrade(
        ticker=ticker,
        entry_date=data.index[0].date().isoformat(),
        entry_price=entry_price,
        exit_date=data.index[-1].date().isoformat(),
        exit_price=exit_price,
        quantity=shares,
        entry_reason="buy_first_valid_day",
        exit_reason="sell_final_valid_day",
        trade_return_pct=trade_return_pct,
        pnl=pnl,
        strategy_name=strategy_name,
    )

    dated_equity_curve = [
        (index.date().isoformat(), shares * float(row["close"]))
        for index, row in data.iterrows()
    ]
    dated_exposure = [
        (index.date().isoformat(), True)
        for index, _ in data.iterrows()
    ]
    result = build_comparison_result(
        config,
        ticker,
        strategy_name,
        data,
        [trade],
        dated_equity_curve,
        dated_exposure,
        final_equity,
        len(data),
    )
    result.slippage_bps = actual_slippage_bps
    return result, [trade]
