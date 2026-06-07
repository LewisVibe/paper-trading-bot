"""Pure backtesting, research metric, and CSV export helpers."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from trading_bot.config import AppConfig
from trading_bot.research.costs import CostModel


@dataclass
class BacktestResult:
    ticker: str
    period: str
    total_return_pct: float
    buy_and_hold_return_pct: float
    number_of_trades: int
    win_rate_pct: float
    average_trade_return_pct: float
    max_drawdown_pct: float
    final_equity: float
    time_in_market_pct: float
    pnl: float
    daily_pnl: list[tuple[str, float]]
    strategy_name: str = "regime_sma_vol_filter"
    cagr_pct: float = 0.0
    annualised_volatility_pct: float = 0.0
    sharpe_ratio: float = 0.0
    calmar_ratio: float = 0.0
    exposure_adjusted_return: float = 0.0
    average_holding_days: float = 0.0
    profit_factor: float = 0.0
    daily_exposure: list[tuple[str, bool]] | None = None
    short_window: int | None = None
    long_window: int | None = None
    slippage_bps: float | None = None


@dataclass
class StrategyPortfolioResult:
    strategy_name: str
    period: str
    starting_equity: float
    final_equity: float
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    annualised_volatility_pct: float
    sharpe_ratio: float
    calmar_ratio: float
    number_of_trades: int


@dataclass
class StrategyRobustnessResult:
    strategy_name: str
    average_out_of_sample_cagr_pct: float
    median_out_of_sample_cagr_pct: float
    average_out_of_sample_sharpe: float
    average_out_of_sample_max_drawdown_pct: float
    number_of_tickers_tested: int
    number_of_tickers_profitable: int
    pct_tickers_profitable: float
    average_number_of_trades: float


@dataclass
class BacktestTrade:
    ticker: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    quantity: float
    entry_reason: str
    exit_reason: str
    trade_return_pct: float
    pnl: float
    strategy_name: str = "regime_sma_vol_filter"


def calculate_max_drawdown(equity_curve: list[float]) -> float:
    peak = 0.0
    max_drawdown = 0.0

    for equity in equity_curve:
        if equity > peak:
            peak = equity
        if peak > 0:
            drawdown = (peak - equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

    return max_drawdown


def calculate_portfolio_max_drawdown(config: AppConfig, results: list[BacktestResult]) -> float:
    daily_totals: dict[str, float] = {}
    for result in results:
        for day, pnl in result.daily_pnl:
            daily_totals[day] = daily_totals.get(day, 0.0) + pnl

    equity_curve = [
        config.backtest.starting_cash + daily_totals[day]
        for day in sorted(daily_totals)
    ]
    return calculate_max_drawdown(equity_curve) * 100


def format_backtest_result(result: BacktestResult) -> str:
    return (
        f"{result.ticker},"
        f"{format_percent(result.total_return_pct)},"
        f"{format_percent(result.buy_and_hold_return_pct)},"
        f"{result.number_of_trades},"
        f"{format_percent(result.win_rate_pct)},"
        f"{format_percent(result.average_trade_return_pct)},"
        f"{format_percent(result.max_drawdown_pct)},"
        f"{format_percent(result.time_in_market_pct)}"
    )


def format_percent(value: float) -> str:
    return f"{value:.2f}%"


def write_backtest_results(
    config: AppConfig,
    results: list[BacktestResult],
    cost_model: CostModel | None = None,
) -> None:
    output_path = Path(config.backtest.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cost_model = cost_model or CostModel()

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "total_return_pct",
                "buy_and_hold_return_pct",
                "number_of_trades",
                "win_rate_pct",
                "average_trade_return_pct",
                "max_drawdown_pct",
                "final_equity",
                "time_in_market_pct",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.ticker,
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    round(result.slippage_bps if result.slippage_bps is not None else float(cost_model.slippage_bps), 4),
                    round(result.total_return_pct, 4),
                    round(result.buy_and_hold_return_pct, 4),
                    result.number_of_trades,
                    round(result.win_rate_pct, 4),
                    round(result.average_trade_return_pct, 4),
                    round(result.max_drawdown_pct, 4),
                    round(result.final_equity, 2),
                    round(result.time_in_market_pct, 4),
                ]
            )


def write_backtest_trades(
    config: AppConfig,
    trades: list[BacktestTrade],
    cost_model: CostModel | None = None,
) -> None:
    output_path = Path(config.backtest.trades_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cost_model = cost_model or CostModel()

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "entry_date",
                "entry_price",
                "exit_date",
                "exit_price",
                "quantity",
                "entry_reason",
                "exit_reason",
                "trade_return_pct",
                "pnl",
            ]
        )
        for trade in trades:
            writer.writerow(
                [
                    trade.ticker,
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    trade.entry_date,
                    round(trade.entry_price, 4),
                    trade.exit_date,
                    round(trade.exit_price, 4),
                    round(trade.quantity, 6),
                    trade.entry_reason,
                    trade.exit_reason,
                    round(trade.trade_return_pct, 4),
                    round(trade.pnl, 2),
                ]
            )


def print_portfolio_summary(
    config: AppConfig,
    results: list[BacktestResult],
    trades: list[BacktestTrade],
    errors: list[str],
) -> None:
    total_pnl = sum(result.pnl for result in results)
    final_equity = config.backtest.starting_cash + total_pnl
    total_return_pct = ((final_equity - config.backtest.starting_cash) / config.backtest.starting_cash) * 100
    max_drawdown_pct = calculate_portfolio_max_drawdown(config, results) if results else 0.0

    print("")
    print("Portfolio summary")
    print(f"Starting cash: {config.backtest.starting_cash:.2f}")
    print(f"Final equity: {final_equity:.2f}")
    print(f"Total return: {total_return_pct:.2f}%")
    print(f"Max drawdown: {max_drawdown_pct:.2f}%")
    print(f"Number of trades: {len(trades)}")
    print(f"Tickers tested: {len(results)}")
    print(f"Tickers with errors: {len(errors)}")


def trend_stress_strategy_name(
    short_window: int,
    long_window: int,
    slippage_bps: float,
) -> str:
    return f"trend_stress_sma_{short_window}_{long_window}_slip_{format_bps_token(slippage_bps)}"


def format_bps_token(slippage_bps: float) -> str:
    if float(slippage_bps).is_integer():
        return str(int(slippage_bps))
    return str(slippage_bps).replace(".", "p")


def parse_trend_stress_strategy_name(strategy_name: str) -> tuple[int, int, float]:
    parts = strategy_name.split("_")
    try:
        sma_index = parts.index("sma")
        slip_index = parts.index("slip")
        short_window = int(parts[sma_index + 1])
        long_window = int(parts[sma_index + 2])
        slippage_bps = float(parts[slip_index + 1].replace("p", "."))
        return short_window, long_window, slippage_bps
    except (ValueError, IndexError):
        return 0, 0, 0.0


def sma_sensitivity_strategy_name(short_window: int, long_window: int) -> str:
    return f"sma_{short_window}_{long_window}_sensitivity"


def parse_sma_sensitivity_strategy_name(strategy_name: str) -> tuple[int, int]:
    parts = strategy_name.split("_")
    if len(parts) >= 4 and parts[0] == "sma":
        try:
            return int(parts[1]), int(parts[2])
        except ValueError:
            pass
    return 0, 0


def build_comparison_result(
    config: AppConfig,
    ticker: str,
    strategy_name: str,
    data,
    trades: list[BacktestTrade],
    dated_equity_curve: list[tuple[str, float]],
    dated_exposure: list[tuple[str, bool]],
    final_equity: float,
    position_days: int,
) -> BacktestResult:
    equity_curve = [equity for _, equity in dated_equity_curve]
    closed_returns = [trade.trade_return_pct for trade in trades]
    wins = [value for value in closed_returns if value > 0]
    first_close = float(data.iloc[0]["close"])
    final_close = float(data.iloc[-1]["close"])
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    total_return_pct = ((final_equity - config.backtest.position_size_dollars) / config.backtest.position_size_dollars) * 100
    time_in_market_pct = (position_days / max(len(data), 1)) * 100
    cagr_pct = calculate_cagr_pct(config.backtest.position_size_dollars, final_equity, len(data))
    annualised_volatility_pct = calculate_annualised_volatility_pct(equity_curve)
    sharpe_ratio = calculate_sharpe_ratio(equity_curve)
    calmar_ratio = cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0.0
    exposure_adjusted_return = total_return_pct / time_in_market_pct if time_in_market_pct > 0 else 0.0
    average_holding_days = calculate_average_holding_days(trades)
    profit_factor = calculate_profit_factor(trades)

    return BacktestResult(
        ticker=ticker,
        period="full_period",
        total_return_pct=total_return_pct,
        buy_and_hold_return_pct=((final_close - first_close) / first_close) * 100,
        number_of_trades=len(trades),
        win_rate_pct=(len(wins) / len(closed_returns) * 100) if closed_returns else 0.0,
        average_trade_return_pct=sum(closed_returns) / len(closed_returns) if closed_returns else 0.0,
        max_drawdown_pct=max_drawdown_pct,
        final_equity=final_equity,
        time_in_market_pct=time_in_market_pct,
        pnl=final_equity - config.backtest.position_size_dollars,
        daily_pnl=[
            (day, equity - config.backtest.position_size_dollars)
            for day, equity in dated_equity_curve
        ],
        strategy_name=strategy_name,
        cagr_pct=cagr_pct,
        annualised_volatility_pct=annualised_volatility_pct,
        sharpe_ratio=sharpe_ratio,
        calmar_ratio=calmar_ratio,
        exposure_adjusted_return=exposure_adjusted_return,
        average_holding_days=average_holding_days,
        profit_factor=profit_factor,
        daily_exposure=dated_exposure,
    )


def build_period_comparison_results(
    config: AppConfig,
    full_result: BacktestResult,
    data,
    trades: list[BacktestTrade],
) -> list[BacktestResult]:
    split_date = config.backtest.split_date
    # Out-of-sample results matter because they show how a strategy behaves
    # after the period you might have used to choose or tune it.
    periods = [
        ("full_period", None, None),
        ("in_sample", None, split_date),
        ("out_of_sample", split_date, None),
    ]

    results: list[BacktestResult] = []
    for period_name, start_date, end_date in periods:
        if period_name == "full_period":
            full_result.period = "full_period"
            results.append(full_result)
            continue

        period_result = build_single_period_result(
            config,
            full_result,
            data,
            trades,
            period_name,
            start_date,
            end_date,
        )
        if period_result is not None:
            results.append(period_result)

    return results


def build_single_period_result(
    config: AppConfig,
    full_result: BacktestResult,
    data,
    trades: list[BacktestTrade],
    period_name: str,
    start_date: str | None,
    end_date: str | None,
) -> BacktestResult | None:
    daily_pnl = filter_period_rows(full_result.daily_pnl, start_date, end_date)
    if len(daily_pnl) < 2:
        return None

    daily_exposure = filter_period_rows(full_result.daily_exposure or [], start_date, end_date)
    period_dates = {day for day, _ in daily_pnl}
    period_trades = [
        trade
        for trade in trades
        if trade.exit_date in period_dates
    ]

    first_day = daily_pnl[0][0]
    last_day = daily_pnl[-1][0]
    first_equity = config.backtest.position_size_dollars + daily_pnl[0][1]
    final_equity = config.backtest.position_size_dollars + daily_pnl[-1][1]
    equity_curve = [config.backtest.position_size_dollars + pnl for _, pnl in daily_pnl]
    close_window = data.loc[first_day:last_day]
    if close_window.empty:
        return None

    closed_returns = [trade.trade_return_pct for trade in period_trades]
    wins = [value for value in closed_returns if value > 0]
    position_days = sum(1 for _, is_exposed in daily_exposure if is_exposed)
    time_in_market_pct = (position_days / len(daily_pnl)) * 100 if daily_pnl else 0.0
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    total_return_pct = ((final_equity - first_equity) / first_equity) * 100 if first_equity > 0 else 0.0
    cagr_pct = calculate_cagr_pct(first_equity, final_equity, len(equity_curve))

    return BacktestResult(
        ticker=full_result.ticker,
        period=period_name,
        total_return_pct=total_return_pct,
        buy_and_hold_return_pct=(
            (float(close_window.iloc[-1]["close"]) - float(close_window.iloc[0]["close"]))
            / float(close_window.iloc[0]["close"])
        ) * 100,
        number_of_trades=len(period_trades),
        win_rate_pct=(len(wins) / len(closed_returns) * 100) if closed_returns else 0.0,
        average_trade_return_pct=sum(closed_returns) / len(closed_returns) if closed_returns else 0.0,
        max_drawdown_pct=max_drawdown_pct,
        final_equity=final_equity,
        time_in_market_pct=time_in_market_pct,
        pnl=final_equity - first_equity,
        daily_pnl=[
            (day, (config.backtest.position_size_dollars + pnl) - first_equity)
            for day, pnl in daily_pnl
        ],
        strategy_name=full_result.strategy_name,
        cagr_pct=cagr_pct,
        annualised_volatility_pct=calculate_annualised_volatility_pct(equity_curve),
        sharpe_ratio=calculate_sharpe_ratio(equity_curve),
        calmar_ratio=cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0.0,
        exposure_adjusted_return=total_return_pct / time_in_market_pct if time_in_market_pct > 0 else 0.0,
        average_holding_days=calculate_average_holding_days(period_trades),
        profit_factor=calculate_profit_factor(period_trades),
        daily_exposure=daily_exposure,
        short_window=full_result.short_window,
        long_window=full_result.long_window,
        slippage_bps=full_result.slippage_bps,
    )


def filter_period_rows(rows: list[tuple[str, Any]], start_date: str | None, end_date: str | None) -> list[tuple[str, Any]]:
    filtered: list[tuple[str, Any]] = []
    for day, value in rows:
        if start_date is not None and day < start_date:
            continue
        if end_date is not None and day >= end_date:
            continue
        filtered.append((day, value))
    return filtered


def calculate_cagr_pct(starting_equity: float, final_equity: float, trading_days: int) -> float:
    if starting_equity <= 0 or final_equity <= 0 or trading_days <= 0:
        return 0.0
    years = trading_days / 252
    if years <= 0:
        return 0.0
    return ((final_equity / starting_equity) ** (1 / years) - 1) * 100


def calculate_daily_returns(equity_curve: list[float]) -> list[float]:
    returns: list[float] = []
    for index in range(1, len(equity_curve)):
        previous = equity_curve[index - 1]
        current = equity_curve[index]
        if previous > 0:
            returns.append((current / previous) - 1)
    return returns


def calculate_annualised_volatility_pct(equity_curve: list[float]) -> float:
    daily_returns = calculate_daily_returns(equity_curve)
    if len(daily_returns) < 2:
        return 0.0
    mean_return = sum(daily_returns) / len(daily_returns)
    variance = sum((value - mean_return) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
    return math.sqrt(variance) * math.sqrt(252) * 100


def calculate_sharpe_ratio(equity_curve: list[float]) -> float:
    daily_returns = calculate_daily_returns(equity_curve)
    if len(daily_returns) < 2:
        return 0.0
    mean_return = sum(daily_returns) / len(daily_returns)
    variance = sum((value - mean_return) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
    daily_volatility = math.sqrt(variance)
    if daily_volatility == 0:
        return 0.0
    return (mean_return / daily_volatility) * math.sqrt(252)


def calculate_average_holding_days(trades: list[BacktestTrade]) -> float:
    if not trades:
        return 0.0
    holding_days: list[int] = []
    for trade in trades:
        entry_date = datetime.fromisoformat(trade.entry_date)
        exit_date = datetime.fromisoformat(trade.exit_date)
        holding_days.append(max((exit_date - entry_date).days, 0))
    return sum(holding_days) / len(holding_days)


def calculate_profit_factor(trades: list[BacktestTrade]) -> float:
    gross_profit = sum(trade.pnl for trade in trades if trade.pnl > 0)
    gross_loss = abs(sum(trade.pnl for trade in trades if trade.pnl < 0))
    if gross_loss == 0:
        return 0.0
    return gross_profit / gross_loss


def write_strategy_comparison_results(
    results: list[BacktestResult],
    cost_model: CostModel | None = None,
) -> None:
    output_path = Path("data/strategy_comparison_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cost_model = cost_model or CostModel()

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "strategy_name",
                "period",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "total_return_pct",
                "buy_and_hold_return_pct",
                "number_of_trades",
                "win_rate_pct",
                "average_trade_return_pct",
                "max_drawdown_pct",
                "final_equity",
                "time_in_market_pct",
                "cagr_pct",
                "annualised_volatility_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "exposure_adjusted_return",
                "average_holding_days",
                "profit_factor",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.ticker,
                    result.strategy_name,
                    result.period,
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    round(result.slippage_bps if result.slippage_bps is not None else float(cost_model.slippage_bps), 4),
                    round(result.total_return_pct, 4),
                    round(result.buy_and_hold_return_pct, 4),
                    result.number_of_trades,
                    round(result.win_rate_pct, 4),
                    round(result.average_trade_return_pct, 4),
                    round(result.max_drawdown_pct, 4),
                    round(result.final_equity, 2),
                    round(result.time_in_market_pct, 4),
                    round(result.cagr_pct, 4),
                    round(result.annualised_volatility_pct, 4),
                    round(result.sharpe_ratio, 4),
                    round(result.calmar_ratio, 4),
                    round(result.exposure_adjusted_return, 4),
                    round(result.average_holding_days, 2),
                    round(result.profit_factor, 4),
                ]
            )


def write_strategy_comparison_trades(
    trades: list[BacktestTrade],
    cost_model: CostModel | None = None,
) -> None:
    output_path = Path("data/strategy_comparison_trades.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cost_model = cost_model or CostModel()

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "strategy_name",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "entry_date",
                "entry_price",
                "exit_date",
                "exit_price",
                "quantity",
                "entry_reason",
                "exit_reason",
                "trade_return_pct",
                "pnl",
            ]
        )
        for trade in trades:
            writer.writerow(
                [
                    trade.ticker,
                    trade.strategy_name,
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    trade.entry_date,
                    round(trade.entry_price, 4),
                    trade.exit_date,
                    round(trade.exit_price, 4),
                    round(trade.quantity, 6),
                    trade.entry_reason,
                    trade.exit_reason,
                    round(trade.trade_return_pct, 4),
                    round(trade.pnl, 2),
                ]
            )


def build_strategy_portfolio_results(
    config: AppConfig,
    results: list[BacktestResult],
) -> list[StrategyPortfolioResult]:
    portfolio_results: list[StrategyPortfolioResult] = []
    strategy_periods = sorted({(result.strategy_name, result.period) for result in results})

    for strategy_name, period in strategy_periods:
        strategy_results = [
            result
            for result in results
            if result.strategy_name == strategy_name and result.period == period
        ]
        if not strategy_results:
            continue

        starting_equity = config.backtest.position_size_dollars * len(strategy_results)
        final_equity = starting_equity + sum(result.pnl for result in strategy_results)
        all_days = sorted(
            {
                day
                for result in strategy_results
                for day, _ in result.daily_pnl
            }
        )

        latest_pnl_by_ticker = {result.ticker: 0.0 for result in strategy_results}
        pnl_lookup_by_ticker = {
            result.ticker: dict(result.daily_pnl)
            for result in strategy_results
        }
        equity_curve: list[float] = []

        for day in all_days:
            for ticker, pnl_lookup in pnl_lookup_by_ticker.items():
                if day in pnl_lookup:
                    latest_pnl_by_ticker[ticker] = pnl_lookup[day]
            equity_curve.append(starting_equity + sum(latest_pnl_by_ticker.values()))

        total_return_pct = ((final_equity - starting_equity) / starting_equity) * 100
        max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
        cagr_pct = calculate_cagr_pct(starting_equity, final_equity, len(equity_curve))
        annualised_volatility_pct = calculate_annualised_volatility_pct(equity_curve)
        sharpe_ratio = calculate_sharpe_ratio(equity_curve)
        calmar_ratio = cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0.0
        number_of_trades = sum(result.number_of_trades for result in strategy_results)

        portfolio_results.append(
            StrategyPortfolioResult(
                strategy_name=strategy_name,
                period=period,
                starting_equity=starting_equity,
                final_equity=final_equity,
                total_return_pct=total_return_pct,
                cagr_pct=cagr_pct,
                max_drawdown_pct=max_drawdown_pct,
                annualised_volatility_pct=annualised_volatility_pct,
                sharpe_ratio=sharpe_ratio,
                calmar_ratio=calmar_ratio,
                number_of_trades=number_of_trades,
            )
        )

    return portfolio_results


def write_strategy_portfolio_comparison(
    results: list[StrategyPortfolioResult],
    cost_model: CostModel | None = None,
) -> None:
    output_path = Path("data/strategy_portfolio_comparison.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cost_model = cost_model or CostModel()

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "strategy_name",
                "period",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "starting_equity",
                "final_equity",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "annualised_volatility_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.strategy_name,
                    result.period,
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    round(result.starting_equity, 2),
                    round(result.final_equity, 2),
                    round(result.total_return_pct, 4),
                    round(result.cagr_pct, 4),
                    round(result.max_drawdown_pct, 4),
                    round(result.annualised_volatility_pct, 4),
                    round(result.sharpe_ratio, 4),
                    round(result.calmar_ratio, 4),
                    result.number_of_trades,
                ]
            )


def write_sma_sensitivity_results(
    results: list[BacktestResult],
    cost_model: CostModel | None = None,
) -> None:
    output_path = Path("data/sma_sensitivity_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cost_model = cost_model or CostModel()

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "period",
                "short_window",
                "long_window",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
                "time_in_market_pct",
            ]
        )
        for result in results:
            short_window, long_window = result.short_window, result.long_window
            if short_window is None or long_window is None:
                short_window, long_window = parse_sma_sensitivity_strategy_name(result.strategy_name)
            writer.writerow(
                [
                    result.ticker,
                    result.period,
                    short_window,
                    long_window,
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    round(result.slippage_bps if result.slippage_bps is not None else float(cost_model.slippage_bps), 4),
                    round(result.total_return_pct, 4),
                    round(result.cagr_pct, 4),
                    round(result.max_drawdown_pct, 4),
                    round(result.sharpe_ratio, 4),
                    round(result.calmar_ratio, 4),
                    result.number_of_trades,
                    round(result.time_in_market_pct, 4),
                ]
            )


def write_sma_sensitivity_portfolio(
    results: list[StrategyPortfolioResult],
    cost_model: CostModel | None = None,
) -> None:
    output_path = Path("data/sma_sensitivity_portfolio.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cost_model = cost_model or CostModel()

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "period",
                "short_window",
                "long_window",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
            ]
        )
        for result in results:
            short_window, long_window = parse_sma_sensitivity_strategy_name(result.strategy_name)
            writer.writerow(
                [
                    result.period,
                    short_window,
                    long_window,
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    round(result.total_return_pct, 4),
                    round(result.cagr_pct, 4),
                    round(result.max_drawdown_pct, 4),
                    round(result.sharpe_ratio, 4),
                    round(result.calmar_ratio, 4),
                    result.number_of_trades,
                ]
            )


def write_trend_stress_test_results(
    results: list[BacktestResult],
    universe_name: str,
) -> None:
    output_path = Path("data/trend_stress_test_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "period",
                "universe_name",
                "short_window",
                "long_window",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
                "time_in_market_pct",
            ]
        )
        for result in results:
            short_window, long_window, slippage_bps = parse_trend_stress_strategy_name(
                result.strategy_name
            )
            writer.writerow(
                [
                    result.ticker,
                    result.period,
                    universe_name,
                    short_window,
                    long_window,
                    0,
                    0,
                    0,
                    round(slippage_bps, 4),
                    round(result.total_return_pct, 4),
                    round(result.cagr_pct, 4),
                    round(result.max_drawdown_pct, 4),
                    round(result.sharpe_ratio, 4),
                    round(result.calmar_ratio, 4),
                    result.number_of_trades,
                    round(result.time_in_market_pct, 4),
                ]
            )


def write_trend_stress_test_portfolio(
    results: list[StrategyPortfolioResult],
    universe_name: str,
) -> None:
    output_path = Path("data/trend_stress_test_portfolio.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "period",
                "universe_name",
                "short_window",
                "long_window",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
            ]
        )
        for result in results:
            short_window, long_window, slippage_bps = parse_trend_stress_strategy_name(
                result.strategy_name
            )
            writer.writerow(
                [
                    result.period,
                    universe_name,
                    short_window,
                    long_window,
                    0,
                    0,
                    0,
                    round(slippage_bps, 4),
                    round(result.total_return_pct, 4),
                    round(result.cagr_pct, 4),
                    round(result.max_drawdown_pct, 4),
                    round(result.sharpe_ratio, 4),
                    round(result.calmar_ratio, 4),
                    result.number_of_trades,
                ]
            )


def calculate_drawdown_series(equity_curve: list[float]) -> list[float]:
    peak = 0.0
    drawdowns: list[float] = []
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = ((peak - equity) / peak * 100) if peak > 0 else 0.0
        drawdowns.append(drawdown)
    return drawdowns


def write_strategy_ticker_equity_curves(
    results: list[BacktestResult],
    config: AppConfig,
) -> None:
    output_path = Path("data/strategy_ticker_equity_curves.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "period",
                "ticker",
                "strategy_name",
                "equity",
                "drawdown_pct",
                "in_position",
            ]
        )

        for result in results:
            equity_rows = [
                (day, config.backtest.position_size_dollars + pnl)
                for day, pnl in result.daily_pnl
            ]
            drawdowns = calculate_drawdown_series([equity for _, equity in equity_rows])
            exposure_lookup = dict(result.daily_exposure or [])

            for index, (day, equity) in enumerate(equity_rows):
                writer.writerow(
                    [
                        day,
                        result.period,
                        result.ticker,
                        result.strategy_name,
                        round(equity, 2),
                        round(drawdowns[index], 4),
                        1 if exposure_lookup.get(day, False) else 0,
                    ]
                )


def write_strategy_portfolio_equity_curves(
    config: AppConfig,
    results: list[BacktestResult],
) -> None:
    output_path = Path("data/strategy_portfolio_equity_curves.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "period", "strategy_name", "equity", "drawdown_pct"])

        for strategy_name, period in sorted({(r.strategy_name, r.period) for r in results}):
            strategy_results = [
                result
                for result in results
                if result.strategy_name == strategy_name and result.period == period
            ]
            curve = build_portfolio_equity_curve(config, strategy_results)
            drawdowns = calculate_drawdown_series([equity for _, equity in curve])
            for index, (day, equity) in enumerate(curve):
                writer.writerow(
                    [
                        day,
                        period,
                        strategy_name,
                        round(equity, 2),
                        round(drawdowns[index], 4),
                    ]
                )


def build_portfolio_equity_curve(
    config: AppConfig,
    results: list[BacktestResult],
) -> list[tuple[str, float]]:
    if not results:
        return []

    starting_equity = config.backtest.position_size_dollars * len(results)
    all_days = sorted({day for result in results for day, _ in result.daily_pnl})
    latest_pnl_by_ticker = {result.ticker: 0.0 for result in results}
    pnl_lookup_by_ticker = {result.ticker: dict(result.daily_pnl) for result in results}

    curve: list[tuple[str, float]] = []
    for day in all_days:
        for ticker, pnl_lookup in pnl_lookup_by_ticker.items():
            if day in pnl_lookup:
                latest_pnl_by_ticker[ticker] = pnl_lookup[day]
        curve.append((day, starting_equity + sum(latest_pnl_by_ticker.values())))

    return curve


def build_strategy_robustness_summary(
    results: list[BacktestResult],
) -> list[StrategyRobustnessResult]:
    robustness: list[StrategyRobustnessResult] = []
    out_of_sample_results = [
        result for result in results if result.period == "out_of_sample"
    ]
    strategy_names = sorted({result.strategy_name for result in out_of_sample_results})

    for strategy_name in strategy_names:
        strategy_results = [
            result for result in out_of_sample_results if result.strategy_name == strategy_name
        ]
        cagr_values = [result.cagr_pct for result in strategy_results]
        profitable = [result for result in strategy_results if result.total_return_pct > 0]
        ticker_count = len(strategy_results)
        robustness.append(
            StrategyRobustnessResult(
                strategy_name=strategy_name,
                average_out_of_sample_cagr_pct=average(cagr_values),
                median_out_of_sample_cagr_pct=median(cagr_values),
                average_out_of_sample_sharpe=average(
                    [result.sharpe_ratio for result in strategy_results]
                ),
                average_out_of_sample_max_drawdown_pct=average(
                    [result.max_drawdown_pct for result in strategy_results]
                ),
                number_of_tickers_tested=ticker_count,
                number_of_tickers_profitable=len(profitable),
                pct_tickers_profitable=(
                    len(profitable) / ticker_count * 100 if ticker_count else 0.0
                ),
                average_number_of_trades=average(
                    [float(result.number_of_trades) for result in strategy_results]
                ),
            )
        )

    return robustness


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    middle = len(sorted_values) // 2
    if len(sorted_values) % 2 == 1:
        return sorted_values[middle]
    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def write_strategy_robustness_summary(
    results: list[StrategyRobustnessResult],
    cost_model: CostModel | None = None,
) -> None:
    output_path = Path("data/strategy_robustness_summary.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cost_model = cost_model or CostModel()

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "strategy_name",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "average_out_of_sample_cagr_pct",
                "median_out_of_sample_cagr_pct",
                "average_out_of_sample_sharpe",
                "average_out_of_sample_max_drawdown_pct",
                "number_of_tickers_tested",
                "number_of_tickers_profitable",
                "pct_tickers_profitable",
                "average_number_of_trades",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result.strategy_name,
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    round(result.average_out_of_sample_cagr_pct, 4),
                    round(result.median_out_of_sample_cagr_pct, 4),
                    round(result.average_out_of_sample_sharpe, 4),
                    round(result.average_out_of_sample_max_drawdown_pct, 4),
                    result.number_of_tickers_tested,
                    result.number_of_tickers_profitable,
                    round(result.pct_tickers_profitable, 4),
                    round(result.average_number_of_trades, 2),
                ]
            )


def print_ranked_strategy_summary(results: list[BacktestResult]) -> None:
    ranked = sorted(
        results,
        key=lambda result: (
            -result.total_return_pct,
            result.max_drawdown_pct,
            result.number_of_trades,
        ),
    )

    print("")
    print("Ranked summary")
    print("ticker,strategy_name,period,total_return,max_drawdown,trades")
    for result in ranked:
        print(
            f"{result.ticker},{result.strategy_name},{result.period},"
            f"{format_percent(result.total_return_pct)},"
            f"{format_percent(result.max_drawdown_pct)},"
            f"{result.number_of_trades}"
        )


def print_ranked_portfolio_summary(results: list[StrategyPortfolioResult]) -> None:
    ranked = sorted(
        results,
        key=lambda result: (
            -result.total_return_pct,
            result.max_drawdown_pct,
            result.number_of_trades,
        ),
    )

    print("")
    print("Portfolio-level ranked summary")
    print("strategy_name,period,total_return,cagr,max_drawdown,sharpe,trades")
    for result in ranked:
        print(
            f"{result.strategy_name},{result.period},"
            f"{format_percent(result.total_return_pct)},"
            f"{format_percent(result.cagr_pct)},"
            f"{format_percent(result.max_drawdown_pct)},"
            f"{result.sharpe_ratio:.2f},"
            f"{result.number_of_trades}"
        )


def print_ranked_robustness_summary(results: list[StrategyRobustnessResult]) -> None:
    ranked = sorted(
        results,
        key=lambda result: (
            -result.average_out_of_sample_cagr_pct,
            result.average_out_of_sample_max_drawdown_pct,
            -result.pct_tickers_profitable,
        ),
    )

    print("")
    print("Out-of-sample robustness summary")
    print("strategy_name,avg_oos_cagr,median_oos_cagr,avg_oos_sharpe,pct_profitable,avg_trades")
    for result in ranked:
        print(
            f"{result.strategy_name},"
            f"{format_percent(result.average_out_of_sample_cagr_pct)},"
            f"{format_percent(result.median_out_of_sample_cagr_pct)},"
            f"{result.average_out_of_sample_sharpe:.2f},"
            f"{format_percent(result.pct_tickers_profitable)},"
            f"{result.average_number_of_trades:.2f}"
        )


def print_ranked_sma_sensitivity_summary(results: list[StrategyPortfolioResult]) -> None:
    out_of_sample_results = [
        result for result in results if result.period == "out_of_sample"
    ]
    ranked = sorted(
        out_of_sample_results,
        key=lambda result: (
            -result.total_return_pct,
            result.max_drawdown_pct,
            result.number_of_trades,
        ),
    )

    print("")
    print("Out-of-sample SMA sensitivity portfolio summary")
    print("short_window,long_window,total_return,cagr,max_drawdown,sharpe,trades")
    for result in ranked:
        short_window, long_window = parse_sma_sensitivity_strategy_name(result.strategy_name)
        print(
            f"{short_window},{long_window},"
            f"{format_percent(result.total_return_pct)},"
            f"{format_percent(result.cagr_pct)},"
            f"{format_percent(result.max_drawdown_pct)},"
            f"{result.sharpe_ratio:.2f},"
            f"{result.number_of_trades}"
        )


def print_ranked_trend_stress_test_summary(results: list[StrategyPortfolioResult]) -> None:
    out_of_sample_results = [
        result for result in results if result.period == "out_of_sample"
    ]
    ranked = sorted(
        out_of_sample_results,
        key=lambda result: (
            -result.total_return_pct,
            result.max_drawdown_pct,
            result.number_of_trades,
        ),
    )

    print("")
    print("Out-of-sample trend stress test portfolio summary")
    print("short_window,long_window,slippage_bps,total_return,cagr,max_drawdown,sharpe,trades")
    for result in ranked:
        short_window, long_window, slippage_bps = parse_trend_stress_strategy_name(
            result.strategy_name
        )
        print(
            f"{short_window},{long_window},{slippage_bps:g},"
            f"{format_percent(result.total_return_pct)},"
            f"{format_percent(result.cagr_pct)},"
            f"{format_percent(result.max_drawdown_pct)},"
            f"{result.sharpe_ratio:.2f},"
            f"{result.number_of_trades}"
        )
