"""Research-only multi-ticker short strategy lab.

This module models one fixed synthetic ETF short-selling hypothesis for
research only. It does not create broker orders, read positions, write SQLite,
send alerts, enable shorting, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from trading_bot.config import AppConfig
from trading_bot.market_data import configure_yfinance_cache, download_backtest_prices
from trading_bot.research.backtesting import (
    calculate_cagr_pct,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
)
from trading_bot.research.costs import CostModel, adjusted_buy_fill_price, adjusted_sell_fill_price
from trading_bot.strategies.rotation import buy_and_hold_equity_curve


SHORT_STRATEGY_NAME = "research_weak_etf_short_momentum"
SHORT_STRATEGY_UNIVERSE = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLY", "XLE", "XLI", "XLU"]
SHORT_STRATEGY_REGIME_TICKER = "SPY"
SHORT_STRATEGY_SMA_WINDOW = 200
SHORT_STRATEGY_MOMENTUM_WINDOW = 126
SHORT_STRATEGY_TOP_N = 2
SHORT_STRATEGY_GROSS_EXPOSURE_LIMIT = Decimal("1")
SHORT_STRATEGY_BORROW_FEE_BPS_ANNUAL = Decimal("300")
SHORT_STRATEGY_BORROW_FEE_STATUS = "fixed_placeholder_300_bps_annual_initial_research"
SHORT_STRATEGY_COST_MODEL_NAME = "stock_etf_research_cost_model"

SHORT_STRATEGY_RESULTS_COLUMNS = [
    "created_at",
    "strategy_name",
    "ticker_or_portfolio",
    "period",
    "total_return_pct",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "number_of_trades",
    "gross_short_exposure_limit",
    "borrow_fee_bps_annual",
    "borrow_fee_model_status",
    "cost_model_name",
    "commission_per_trade",
    "commission_bps",
    "spread_bps",
    "slippage_bps",
    "research_status",
    "research_conclusion",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]

SHORT_STRATEGY_TRADES_COLUMNS = [
    "created_at",
    "date",
    "strategy_name",
    "ticker",
    "side",
    "reason",
    "quantity",
    "price",
    "notional",
    "spy_close",
    "spy_sma_200",
    "ticker_close",
    "ticker_sma_200",
    "momentum_126d_pct",
    "gross_short_exposure_limit",
    "borrow_fee_bps_annual",
    "borrow_fee_model_status",
    "research_only",
    "preview_only",
    "execution_approved",
]

SHORT_STRATEGY_EQUITY_COLUMNS = [
    "date",
    "strategy_name",
    "ticker_or_portfolio",
    "period",
    "equity",
    "gross_short_exposure_pct",
    "open_short_count",
    "active_short_tickers",
    "borrow_fee_bps_annual",
    "borrow_fee_model_status",
    "research_only",
    "preview_only",
    "execution_approved",
]

SHORT_STRATEGY_ITERATION_COLUMNS = [
    "created_at",
    "iteration_id",
    "hypothesis",
    "strategy_name",
    "allowed_parameter_set",
    "reason_for_testing",
    "result_summary",
    "decision",
    "next_research_question",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class ShortStrategyLabResult:
    results_path: Path
    trades_path: Path
    equity_curve_path: Path
    iteration_log_path: Path
    result_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    equity_rows: list[dict[str, Any]]
    iteration_rows: list[dict[str, Any]]
    summary_lines: list[str]


def run_short_strategy_lab_files(
    config: AppConfig,
    logger,
    data_dir: Path | str = "data",
) -> ShortStrategyLabResult:
    configure_yfinance_cache(config, logger)
    price_by_ticker: dict[str, list[dict[str, Any]]] = {}
    for ticker in SHORT_STRATEGY_UNIVERSE:
        frame = download_backtest_prices(config, ticker)
        price_by_ticker[ticker] = [
            {"date": index.date().isoformat(), "close": float(row["close"])}
            for index, row in frame.iterrows()
            if float(row["close"]) > 0
        ]
    created_at = datetime.now(timezone.utc).isoformat()
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))
    return build_and_write_short_strategy_lab_outputs(
        price_by_ticker=price_by_ticker,
        starting_cash=config.backtest.starting_cash,
        cost_model=cost_model,
        data_dir=Path(data_dir),
        created_at=created_at,
    )


def build_and_write_short_strategy_lab_outputs(
    price_by_ticker: dict[str, list[dict[str, Any]]],
    starting_cash: float,
    cost_model: CostModel,
    data_dir: Path,
    created_at: str,
) -> ShortStrategyLabResult:
    aligned_rows = align_price_rows(price_by_ticker)
    strategy_equity_rows, trade_rows = simulate_weak_etf_short_momentum(
        aligned_rows=aligned_rows,
        starting_cash=starting_cash,
        cost_model=cost_model,
        created_at=created_at,
    )
    result_rows = build_short_strategy_result_rows(
        aligned_rows=aligned_rows,
        strategy_equity_rows=strategy_equity_rows,
        trade_rows=trade_rows,
        starting_cash=starting_cash,
        cost_model=cost_model,
        created_at=created_at,
    )
    iteration_rows = build_iteration_rows(created_at, result_rows)

    results_path = data_dir / "short_strategy_lab_results.csv"
    trades_path = data_dir / "short_strategy_lab_trades.csv"
    equity_curve_path = data_dir / "short_strategy_lab_equity_curve.csv"
    iteration_log_path = data_dir / "short_strategy_iteration_log.csv"
    write_rows(results_path, SHORT_STRATEGY_RESULTS_COLUMNS, result_rows)
    write_rows(trades_path, SHORT_STRATEGY_TRADES_COLUMNS, trade_rows)
    write_rows(equity_curve_path, SHORT_STRATEGY_EQUITY_COLUMNS, strategy_equity_rows)
    write_rows(iteration_log_path, SHORT_STRATEGY_ITERATION_COLUMNS, iteration_rows)
    return ShortStrategyLabResult(
        results_path=results_path,
        trades_path=trades_path,
        equity_curve_path=equity_curve_path,
        iteration_log_path=iteration_log_path,
        result_rows=result_rows,
        trade_rows=trade_rows,
        equity_rows=strategy_equity_rows,
        iteration_rows=iteration_rows,
        summary_lines=build_short_strategy_summary(
            result_rows,
            results_path,
            trades_path,
            equity_curve_path,
            iteration_log_path,
        ),
    )


def align_price_rows(price_by_ticker: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    date_sets = [
        {str(row["date"]) for row in rows}
        for ticker, rows in price_by_ticker.items()
        if ticker in SHORT_STRATEGY_UNIVERSE and rows
    ]
    if not date_sets:
        return []
    common_dates = sorted(set.intersection(*date_sets))
    lookup = {
        ticker: {str(row["date"]): float(row["close"]) for row in rows}
        for ticker, rows in price_by_ticker.items()
        if ticker in SHORT_STRATEGY_UNIVERSE
    }
    return [
        {
            "date": date,
            "close": {ticker: lookup[ticker][date] for ticker in SHORT_STRATEGY_UNIVERSE if ticker in lookup},
        }
        for date in common_dates
    ]


def simulate_weak_etf_short_momentum(
    aligned_rows: list[dict[str, Any]],
    starting_cash: float,
    cost_model: CostModel,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cash = starting_cash
    short_quantities: dict[str, float] = {}
    closes_by_ticker = {ticker: [] for ticker in SHORT_STRATEGY_UNIVERSE}
    equity_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    current_month = ""

    for row in aligned_rows:
        date = str(row["date"])
        close_by_ticker = {ticker: float(price) for ticker, price in row["close"].items()}
        for ticker in SHORT_STRATEGY_UNIVERSE:
            closes_by_ticker[ticker].append(close_by_ticker[ticker])

        cash -= daily_borrow_fee(close_by_ticker, short_quantities)
        equity = mark_to_market_equity(cash, close_by_ticker, short_quantities)
        spy_sma = simple_moving_average(closes_by_ticker[SHORT_STRATEGY_REGIME_TICKER], SHORT_STRATEGY_SMA_WINDOW)
        spy_bearish = spy_sma is not None and close_by_ticker[SHORT_STRATEGY_REGIME_TICKER] < spy_sma

        for ticker in list(short_quantities):
            ticker_sma = simple_moving_average(closes_by_ticker[ticker], SHORT_STRATEGY_SMA_WINDOW)
            if not spy_bearish or ticker_sma is None or close_by_ticker[ticker] >= ticker_sma:
                cash = cover_short(
                    created_at,
                    date,
                    ticker,
                    "spy_or_ticker_close_at_or_above_sma_200",
                    cash,
                    short_quantities,
                    close_by_ticker,
                    closes_by_ticker,
                    cost_model,
                    trade_rows,
                )

        month = date[:7]
        if month != current_month:
            current_month = month
            for ticker in list(short_quantities):
                cash = cover_short(
                    created_at,
                    date,
                    ticker,
                    "monthly_rebalance_reset",
                    cash,
                    short_quantities,
                    close_by_ticker,
                    closes_by_ticker,
                    cost_model,
                    trade_rows,
                )
            if spy_bearish:
                equity = mark_to_market_equity(cash, close_by_ticker, short_quantities)
                targets = weakest_eligible_tickers(close_by_ticker, closes_by_ticker)
                if targets and equity > 0:
                    notional_per_ticker = equity * float(SHORT_STRATEGY_GROSS_EXPOSURE_LIMIT) / len(targets)
                    for ticker in targets:
                        fill_price = float(adjusted_sell_fill_price(close_by_ticker[ticker], cost_model))
                        quantity = notional_per_ticker / fill_price if fill_price > 0 else 0.0
                        short_quantities[ticker] = quantity
                        cash += quantity * fill_price
                        trade_rows.append(
                            short_trade_row(
                                created_at,
                                date,
                                ticker,
                                "sell_short",
                                "monthly_weak_etf_short_entry",
                                quantity,
                                fill_price,
                                close_by_ticker,
                                closes_by_ticker,
                            )
                        )

        ending_equity = mark_to_market_equity(cash, close_by_ticker, short_quantities)
        gross_exposure = gross_short_exposure(close_by_ticker, short_quantities, ending_equity)
        equity_rows.append(
            {
                "date": date,
                "strategy_name": SHORT_STRATEGY_NAME,
                "ticker_or_portfolio": "portfolio",
                "period": "full_period",
                "equity": ending_equity,
                "gross_short_exposure_pct": gross_exposure * 100,
                "open_short_count": len(short_quantities),
                "active_short_tickers": ";".join(sorted(short_quantities)),
                "borrow_fee_bps_annual": SHORT_STRATEGY_BORROW_FEE_BPS_ANNUAL,
                "borrow_fee_model_status": SHORT_STRATEGY_BORROW_FEE_STATUS,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
            }
        )

    return equity_rows, trade_rows


def cover_short(
    created_at: str,
    date: str,
    ticker: str,
    reason: str,
    cash: float,
    short_quantities: dict[str, float],
    close_by_ticker: dict[str, float],
    closes_by_ticker: dict[str, list[float]],
    cost_model: CostModel,
    trade_rows: list[dict[str, Any]],
) -> float:
    quantity = short_quantities.pop(ticker)
    fill_price = float(adjusted_buy_fill_price(close_by_ticker[ticker], cost_model))
    cash -= quantity * fill_price
    trade_rows.append(
        short_trade_row(
            created_at,
            date,
            ticker,
            "buy_to_cover",
            reason,
            quantity,
            fill_price,
            close_by_ticker,
            closes_by_ticker,
        )
    )
    return cash


def weakest_eligible_tickers(
    close_by_ticker: dict[str, float],
    closes_by_ticker: dict[str, list[float]],
) -> list[str]:
    ranked: list[tuple[float, str]] = []
    for ticker in SHORT_STRATEGY_UNIVERSE:
        if ticker == SHORT_STRATEGY_REGIME_TICKER:
            continue
        ticker_sma = simple_moving_average(closes_by_ticker[ticker], SHORT_STRATEGY_SMA_WINDOW)
        momentum = trailing_return_pct(closes_by_ticker[ticker], SHORT_STRATEGY_MOMENTUM_WINDOW)
        if ticker_sma is None or momentum is None:
            continue
        if close_by_ticker[ticker] < ticker_sma:
            ranked.append((momentum, ticker))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [ticker for _, ticker in ranked[:SHORT_STRATEGY_TOP_N]]


def short_trade_row(
    created_at: str,
    date: str,
    ticker: str,
    side: str,
    reason: str,
    quantity: float,
    price: float,
    close_by_ticker: dict[str, float],
    closes_by_ticker: dict[str, list[float]],
) -> dict[str, Any]:
    spy_close = close_by_ticker[SHORT_STRATEGY_REGIME_TICKER]
    ticker_close = close_by_ticker[ticker]
    return {
        "created_at": created_at,
        "date": date,
        "strategy_name": SHORT_STRATEGY_NAME,
        "ticker": ticker,
        "side": side,
        "reason": reason,
        "quantity": quantity,
        "price": price,
        "notional": quantity * price,
        "spy_close": spy_close,
        "spy_sma_200": simple_moving_average(closes_by_ticker[SHORT_STRATEGY_REGIME_TICKER], SHORT_STRATEGY_SMA_WINDOW) or "",
        "ticker_close": ticker_close,
        "ticker_sma_200": simple_moving_average(closes_by_ticker[ticker], SHORT_STRATEGY_SMA_WINDOW) or "",
        "momentum_126d_pct": trailing_return_pct(closes_by_ticker[ticker], SHORT_STRATEGY_MOMENTUM_WINDOW) or "",
        "gross_short_exposure_limit": SHORT_STRATEGY_GROSS_EXPOSURE_LIMIT,
        "borrow_fee_bps_annual": SHORT_STRATEGY_BORROW_FEE_BPS_ANNUAL,
        "borrow_fee_model_status": SHORT_STRATEGY_BORROW_FEE_STATUS,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_short_strategy_result_rows(
    aligned_rows: list[dict[str, Any]],
    strategy_equity_rows: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
    starting_cash: float,
    cost_model: CostModel,
    created_at: str,
) -> list[dict[str, Any]]:
    dates = [str(row["date"]) for row in aligned_rows]
    strategy_equity = [float(row["equity"]) for row in strategy_equity_rows]
    spy_closes = [float(row["close"][SHORT_STRATEGY_REGIME_TICKER]) for row in aligned_rows]
    spy_buy_hold = buy_and_hold_equity_curve(spy_closes, starting_cash)
    cash_flat = [starting_cash for _ in aligned_rows]
    rows: list[dict[str, Any]] = []
    for strategy_name, equity_curve in [
        (SHORT_STRATEGY_NAME, strategy_equity),
        ("spy_buy_and_hold_baseline", spy_buy_hold),
        ("cash_flat_baseline", cash_flat),
    ]:
        for period, start_index, end_index in period_slices(equity_curve):
            period_curve = equity_curve[start_index:end_index]
            number_of_trades = trade_count_for_period(strategy_name, trade_rows, dates, start_index, end_index, len(period_curve))
            rows.append(
                result_row(
                    created_at,
                    strategy_name,
                    period,
                    period_curve,
                    number_of_trades,
                    cost_model,
                )
            )
    return rows


def result_row(
    created_at: str,
    strategy_name: str,
    period: str,
    equity_curve: list[float],
    number_of_trades: int,
    cost_model: CostModel,
) -> dict[str, Any]:
    starting_equity = equity_curve[0] if equity_curve else 0.0
    final_equity = equity_curve[-1] if equity_curve else starting_equity
    total_return_pct = ((final_equity - starting_equity) / starting_equity) * 100 if starting_equity > 0 else 0.0
    cagr_pct = calculate_cagr_pct(starting_equity, final_equity, len(equity_curve))
    sharpe_ratio = calculate_sharpe_ratio(equity_curve)
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    calmar_ratio = cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct else 0.0
    research_status, research_conclusion, required_next_step = conclusion_for_result(
        strategy_name,
        period,
        cagr_pct,
        sharpe_ratio,
        calmar_ratio,
    )
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown_pct": max_drawdown_pct,
        "calmar_ratio": calmar_ratio,
        "number_of_trades": number_of_trades,
        "gross_short_exposure_limit": SHORT_STRATEGY_GROSS_EXPOSURE_LIMIT,
        "borrow_fee_bps_annual": SHORT_STRATEGY_BORROW_FEE_BPS_ANNUAL,
        "borrow_fee_model_status": SHORT_STRATEGY_BORROW_FEE_STATUS,
        "cost_model_name": SHORT_STRATEGY_COST_MODEL_NAME,
        "commission_per_trade": cost_model.commission_per_trade,
        "commission_bps": cost_model.commission_bps,
        "spread_bps": cost_model.spread_bps,
        "slippage_bps": cost_model.slippage_bps,
        "research_status": research_status,
        "research_conclusion": research_conclusion,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def conclusion_for_result(
    strategy_name: str,
    period: str,
    cagr_pct: float,
    sharpe_ratio: float,
    calmar_ratio: float,
) -> tuple[str, str, str]:
    if strategy_name != SHORT_STRATEGY_NAME:
        return (
            "benchmark_context",
            "Benchmark row for context only; not a short strategy candidate.",
            "Use this row only to compare the short strategy lab against baseline alternatives.",
        )
    if period == "out_of_sample" and (cagr_pct < 0 or sharpe_ratio < 0 or calmar_ratio < 0):
        return (
            "not_useful",
            "Out-of-sample CAGR, Sharpe, or Calmar is negative; do not call this robust or continue to preview/execution.",
            "Pause this short strategy unless a better fixed hypothesis is proposed and tested research-only.",
        )
    if cagr_pct < 0 or sharpe_ratio < 0 or calmar_ratio < 0:
        return (
            "weak_candidate",
            "Metrics are weak in this period; borrow fees and real short constraints remain simplified research assumptions.",
            "Keep research-only and require stronger out-of-sample evidence before any preview discussion.",
        )
    return (
        "research_only_observation",
        "Metrics are positive in this period, but short borrow availability, recalls, fees, and squeezes are simplified.",
        "Keep research-only and compare with benchmark and failed SPY hedge before any preview discussion.",
    )


def build_iteration_rows(created_at: str, result_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    full = find_result(result_rows, SHORT_STRATEGY_NAME, "full_period")
    oos = find_result(result_rows, SHORT_STRATEGY_NAME, "out_of_sample")
    result_summary = "full_period and out_of_sample rows unavailable"
    decision = "research_only_observation"
    next_question = "Compare against failed SPY hedge and benchmark rows before further short research."
    if full and oos:
        result_summary = (
            f"Full CAGR={float(full['cagr_pct']):.4f}%, Sharpe={float(full['sharpe_ratio']):.4f}, "
            f"Calmar={float(full['calmar_ratio']):.4f}; OOS CAGR={float(oos['cagr_pct']):.4f}%, "
            f"Sharpe={float(oos['sharpe_ratio']):.4f}, Calmar={float(oos['calmar_ratio']):.4f}."
        )
        decision = str(oos["research_status"])
        next_question = str(oos["required_next_step"])
    return [
        {
            "created_at": created_at,
            "iteration_id": "short_lab_001",
            "hypothesis": "In bearish SPY regimes, the weakest liquid ETFs below their own 200-day SMA may be better synthetic shorts than shorting SPY alone.",
            "strategy_name": SHORT_STRATEGY_NAME,
            "allowed_parameter_set": "monthly rebalance; SPY SMA200 regime; 126-day return ranking; weakest_N=2; ETF SMA200 filter; 1x gross short exposure; borrow_fee_bps_annual=300",
            "reason_for_testing": "The prior SPY-only short hedge failed, so this tests one fixed cross-sectional weakness hypothesis without parameter search.",
            "result_summary": result_summary,
            "decision": decision,
            "next_research_question": next_question,
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
        }
    ]


def build_short_strategy_summary(
    result_rows: list[dict[str, Any]],
    results_path: Path,
    trades_path: Path,
    equity_curve_path: Path,
    iteration_log_path: Path,
) -> list[str]:
    full = find_result(result_rows, SHORT_STRATEGY_NAME, "full_period")
    oos = find_result(result_rows, SHORT_STRATEGY_NAME, "out_of_sample")
    lines = [
        "SHORT STRATEGY LAB. RESEARCH ONLY. NOT EXECUTION.",
        "Strategy: research_weak_etf_short_momentum.",
        "Hypothesis: short the weakest liquid ETFs below their own 200-day SMA only when SPY is below its 200-day SMA.",
        "Fixed parameters: monthly rebalance, 126-day momentum rank, weakest_N=2, ETF SMA200 filter, 1x gross short exposure.",
        "Borrow fee model: fixed_placeholder_300_bps_annual_initial_research.",
    ]
    if full:
        lines.append(metric_line("Full-period", full))
    if oos:
        lines.append(metric_line("Out-of-sample", oos))
        lines.append(f"Research conclusion: {oos['research_status']} - {oos['research_conclusion']}")
    lines.extend(
        [
            "Warning: real borrow availability, borrow fees, recalls, and short squeezes are simplified or not fully modelled.",
            "Warning: this is research only and not execution approval.",
            f"Saved short strategy lab results to {results_path}",
            f"Saved short strategy lab trades to {trades_path}",
            f"Saved short strategy lab equity curve to {equity_curve_path}",
            f"Saved short strategy iteration log to {iteration_log_path}",
        ]
    )
    return lines


def metric_line(label: str, row: dict[str, Any]) -> str:
    return (
        f"{label}: "
        f"CAGR={float(row['cagr_pct']):.4f}%, "
        f"Sharpe={float(row['sharpe_ratio']):.4f}, "
        f"max_drawdown={float(row['max_drawdown_pct']):.4f}%, "
        f"Calmar={float(row['calmar_ratio']):.4f}"
    )


def trade_count_for_period(
    strategy_name: str,
    trade_rows: list[dict[str, Any]],
    dates: list[str],
    start_index: int,
    end_index: int,
    period_length: int,
) -> int:
    if strategy_name == "cash_flat_baseline":
        return 0
    if strategy_name == "spy_buy_and_hold_baseline":
        return 1 if period_length >= 2 else 0
    if strategy_name == SHORT_STRATEGY_NAME:
        if start_index == 0 and end_index == len(dates):
            return len(trade_rows)
        if not dates or start_index >= len(dates) or end_index <= start_index:
            return 0
        start_date = dates[start_index]
        end_date = dates[end_index - 1]
        return sum(1 for row in trade_rows if start_date <= str(row["date"]) <= end_date)
    return 0


def period_slices(equity_curve: list[float]) -> list[tuple[str, int, int]]:
    if not equity_curve:
        return [("full_period", 0, 0), ("in_sample", 0, 0), ("out_of_sample", 0, 0)]
    total = len(equity_curve)
    if total < 3:
        return [("full_period", 0, total), ("in_sample", 0, total), ("out_of_sample", 0, total)]
    split = max(1, min(total - 1, int(total * 0.7)))
    return [("full_period", 0, total), ("in_sample", 0, split), ("out_of_sample", split, total)]


def simple_moving_average(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def trailing_return_pct(values: list[float], window: int) -> float | None:
    if len(values) <= window:
        return None
    start = values[-window - 1]
    end = values[-1]
    if start <= 0:
        return None
    return ((end - start) / start) * 100


def daily_borrow_fee(close_by_ticker: dict[str, float], short_quantities: dict[str, float]) -> float:
    daily_rate = float(SHORT_STRATEGY_BORROW_FEE_BPS_ANNUAL) / 10000 / 252
    return sum(short_quantities[ticker] * close_by_ticker[ticker] * daily_rate for ticker in short_quantities)


def mark_to_market_equity(
    cash: float,
    close_by_ticker: dict[str, float],
    short_quantities: dict[str, float],
) -> float:
    return cash - sum(quantity * close_by_ticker[ticker] for ticker, quantity in short_quantities.items())


def gross_short_exposure(
    close_by_ticker: dict[str, float],
    short_quantities: dict[str, float],
    equity: float,
) -> float:
    if equity <= 0:
        return 0.0
    gross = sum(quantity * close_by_ticker[ticker] for ticker, quantity in short_quantities.items())
    return gross / equity


def find_result(rows: list[dict[str, Any]], strategy_name: str, period: str) -> dict[str, Any] | None:
    return next((row for row in rows if row["strategy_name"] == strategy_name and row["period"] == period), None)


def write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
