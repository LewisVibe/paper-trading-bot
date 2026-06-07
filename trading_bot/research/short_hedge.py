"""Research-only SPY short hedge backtest.

This module models a synthetic SPY short hedge for research only. It does not
create broker orders, read positions, write SQLite, send alerts, or approve
execution.
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
    calculate_annualised_volatility_pct,
    calculate_cagr_pct,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
)
from trading_bot.research.costs import CostModel, adjusted_buy_fill_price, adjusted_sell_fill_price
from trading_bot.strategies.rotation import buy_and_hold_equity_curve


SHORT_HEDGE_STRATEGY_NAME = "research_spy_short_hedge"
SHORT_HEDGE_TICKER = "SPY"
SHORT_HEDGE_SMA_WINDOW = 200
SHORT_HEDGE_BORROW_FEE_STATUS = "not_modelled_initial_research"

SHORT_HEDGE_RESULTS_COLUMNS = [
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
    "cost_model_name",
    "commission_per_trade",
    "commission_bps",
    "spread_bps",
    "slippage_bps",
    "borrow_fee_model_status",
    "research_status",
    "research_conclusion",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]

SHORT_HEDGE_TRADES_COLUMNS = [
    "created_at",
    "date",
    "strategy_name",
    "ticker",
    "side",
    "reason",
    "quantity",
    "price",
    "notional",
    "borrow_fee_model_status",
    "research_only",
    "preview_only",
    "execution_approved",
]

SHORT_HEDGE_EQUITY_COLUMNS = [
    "date",
    "strategy_name",
    "period",
    "equity",
    "desired_position",
    "close",
    "sma_200",
    "borrow_fee_model_status",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class ShortHedgeBacktestResult:
    results_path: Path
    trades_path: Path
    equity_curve_path: Path
    result_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    equity_rows: list[dict[str, Any]]
    summary_lines: list[str]


def run_short_hedge_backtest_files(
    config: AppConfig,
    logger,
    data_dir: Path | str = "data",
) -> ShortHedgeBacktestResult:
    configure_yfinance_cache(config, logger)
    price_frame = download_backtest_prices(config, SHORT_HEDGE_TICKER)
    price_rows = [
        {"date": index.date().isoformat(), "close": float(row["close"])}
        for index, row in price_frame.iterrows()
        if float(row["close"]) > 0
    ]
    created_at = datetime.now(timezone.utc).isoformat()
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))
    return build_and_write_short_hedge_outputs(
        price_rows,
        config.backtest.starting_cash,
        cost_model,
        Path(data_dir),
        created_at,
    )


def build_and_write_short_hedge_outputs(
    price_rows: list[dict[str, Any]],
    starting_cash: float,
    cost_model: CostModel,
    data_dir: Path,
    created_at: str,
) -> ShortHedgeBacktestResult:
    hedge_equity_rows, trade_rows = simulate_spy_short_hedge(price_rows, starting_cash, cost_model, created_at)
    result_rows = build_short_hedge_result_rows(price_rows, hedge_equity_rows, trade_rows, starting_cash, cost_model, created_at)
    results_path = data_dir / "short_hedge_backtest_results.csv"
    trades_path = data_dir / "short_hedge_backtest_trades.csv"
    equity_curve_path = data_dir / "short_hedge_equity_curve.csv"
    write_rows(results_path, SHORT_HEDGE_RESULTS_COLUMNS, result_rows)
    write_rows(trades_path, SHORT_HEDGE_TRADES_COLUMNS, trade_rows)
    write_rows(equity_curve_path, SHORT_HEDGE_EQUITY_COLUMNS, hedge_equity_rows)
    return ShortHedgeBacktestResult(
        results_path=results_path,
        trades_path=trades_path,
        equity_curve_path=equity_curve_path,
        result_rows=result_rows,
        trade_rows=trade_rows,
        equity_rows=hedge_equity_rows,
        summary_lines=build_short_hedge_summary(result_rows, results_path, trades_path, equity_curve_path),
    )


def simulate_spy_short_hedge(
    price_rows: list[dict[str, Any]],
    starting_cash: float,
    cost_model: CostModel,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cash = starting_cash
    short_quantity = 0.0
    equity_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    closes: list[float] = []

    for row in price_rows:
        date = str(row["date"])
        close = float(row["close"])
        closes.append(close)
        sma_200 = simple_moving_average(closes, SHORT_HEDGE_SMA_WINDOW)
        current_equity = cash - (short_quantity * close)
        wants_short = sma_200 is not None and close < sma_200

        if wants_short and short_quantity <= 0:
            fill_price = float(adjusted_sell_fill_price(close, cost_model))
            notional = max(current_equity, 0.0)
            short_quantity = notional / fill_price if fill_price > 0 else 0.0
            cash += short_quantity * fill_price
            trade_rows.append(short_hedge_trade_row(created_at, date, "sell_short", "close_below_sma_200", short_quantity, fill_price))
        elif not wants_short and short_quantity > 0:
            fill_price = float(adjusted_buy_fill_price(close, cost_model))
            quantity = short_quantity
            cash -= quantity * fill_price
            short_quantity = 0.0
            trade_rows.append(short_hedge_trade_row(created_at, date, "buy_to_cover", "close_at_or_above_sma_200", quantity, fill_price))

        ending_equity = cash - (short_quantity * close)
        equity_rows.append(
            {
                "date": date,
                "strategy_name": SHORT_HEDGE_STRATEGY_NAME,
                "period": "full_period",
                "equity": ending_equity,
                "desired_position": "short" if wants_short else "flat",
                "close": close,
                "sma_200": sma_200 if sma_200 is not None else "",
                "borrow_fee_model_status": SHORT_HEDGE_BORROW_FEE_STATUS,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
            }
        )

    return equity_rows, trade_rows


def short_hedge_trade_row(
    created_at: str,
    date: str,
    side: str,
    reason: str,
    quantity: float,
    price: float,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "date": date,
        "strategy_name": SHORT_HEDGE_STRATEGY_NAME,
        "ticker": SHORT_HEDGE_TICKER,
        "side": side,
        "reason": reason,
        "quantity": quantity,
        "price": price,
        "notional": quantity * price,
        "borrow_fee_model_status": SHORT_HEDGE_BORROW_FEE_STATUS,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_short_hedge_result_rows(
    price_rows: list[dict[str, Any]],
    hedge_equity_rows: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
    starting_cash: float,
    cost_model: CostModel,
    created_at: str,
) -> list[dict[str, Any]]:
    closes = [float(row["close"]) for row in price_rows]
    hedge_equity = [float(row["equity"]) for row in hedge_equity_rows]
    spy_buy_hold = buy_and_hold_equity_curve(closes, starting_cash)
    cash_flat = [starting_cash for _ in closes]
    rows = []
    for strategy_name, equity_curve, trade_count in [
        (SHORT_HEDGE_STRATEGY_NAME, hedge_equity, len(trade_rows)),
        ("spy_buy_and_hold_baseline", spy_buy_hold, 1 if len(closes) >= 2 else 0),
        ("cash_flat_baseline", cash_flat, 0),
    ]:
        for period_name, start_index, end_index in period_slices(equity_curve):
            period_curve = equity_curve[start_index:end_index]
            period_trade_count = trade_count_for_period(
                strategy_name,
                trade_count,
                trade_rows,
                price_rows,
                start_index,
                end_index,
                len(period_curve),
            )
            rows.append(
                result_row(
                    created_at,
                    strategy_name,
                    period_name,
                    period_curve,
                    period_trade_count,
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
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    calmar_ratio = cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct else 0.0
    research_status, research_conclusion, required_next_step = research_conclusion_for_result(
        strategy_name,
        cagr_pct,
        calculate_sharpe_ratio(equity_curve),
        calmar_ratio,
    )
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "sharpe_ratio": calculate_sharpe_ratio(equity_curve),
        "max_drawdown_pct": max_drawdown_pct,
        "calmar_ratio": calmar_ratio,
        "number_of_trades": number_of_trades,
        "cost_model_name": "stock_etf_research_cost_model",
        "commission_per_trade": cost_model.commission_per_trade,
        "commission_bps": cost_model.commission_bps,
        "spread_bps": cost_model.spread_bps,
        "slippage_bps": cost_model.slippage_bps,
        "borrow_fee_model_status": SHORT_HEDGE_BORROW_FEE_STATUS,
        "research_status": research_status,
        "research_conclusion": research_conclusion,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def period_slices(equity_curve: list[float]) -> list[tuple[str, int, int]]:
    if not equity_curve:
        return [("full_period", 0, 0), ("in_sample", 0, 0), ("out_of_sample", 0, 0)]
    total = len(equity_curve)
    if total < 3:
        return [("full_period", 0, total), ("in_sample", 0, total), ("out_of_sample", 0, total)]
    split = max(1, min(total - 1, int(total * 0.7)))
    return [("full_period", 0, total), ("in_sample", 0, split), ("out_of_sample", split, total)]


def count_trades_in_period(trade_rows: list[dict[str, Any]], start_date: str, end_date: str) -> int:
    if not start_date or not end_date:
        return 0
    return sum(1 for row in trade_rows if start_date <= str(row["date"]) <= end_date)


def trade_count_for_period(
    strategy_name: str,
    full_period_trade_count: int,
    trade_rows: list[dict[str, Any]],
    price_rows: list[dict[str, Any]],
    start_index: int,
    end_index: int,
    period_length: int,
) -> int:
    if strategy_name == "cash_flat_baseline":
        return 0
    if strategy_name == "spy_buy_and_hold_baseline":
        return 1 if period_length >= 2 else 0
    if strategy_name == SHORT_HEDGE_STRATEGY_NAME:
        if start_index == 0 and end_index == len(price_rows):
            return full_period_trade_count
        return count_trades_in_period(
            trade_rows,
            price_rows[start_index]["date"] if start_index < len(price_rows) else "",
            price_rows[end_index - 1]["date"] if end_index > start_index and end_index <= len(price_rows) else "",
        )
    return full_period_trade_count


def research_conclusion_for_result(
    strategy_name: str,
    cagr_pct: float,
    sharpe_ratio: float,
    calmar_ratio: float,
) -> tuple[str, str, str]:
    if strategy_name != SHORT_HEDGE_STRATEGY_NAME:
        return (
            "benchmark_context",
            "Benchmark row for context only; not a short hedge candidate.",
            "Use this row only to compare the research hedge against baseline alternatives.",
        )
    if cagr_pct < 0 and sharpe_ratio < 0 and calmar_ratio < 0:
        return (
            "not_useful",
            "Negative CAGR, Sharpe, and Calmar; borrow fees are not modelled; do not continue to preview or execution.",
            "Pause short hedge research unless a better fixed hypothesis is proposed and tested research-only.",
        )
    return (
        "research_only_observation",
        "Synthetic short hedge metrics require further saved-data research; borrow fees are not modelled.",
        "Keep research-only and compare against benchmarks before considering any preview discussion.",
    )


def simple_moving_average(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def build_short_hedge_summary(
    result_rows: list[dict[str, Any]],
    results_path: Path,
    trades_path: Path,
    equity_curve_path: Path,
) -> list[str]:
    full = find_result(result_rows, SHORT_HEDGE_STRATEGY_NAME, "full_period")
    oos = find_result(result_rows, SHORT_HEDGE_STRATEGY_NAME, "out_of_sample")
    lines = [
        "SHORT HEDGE BACKTEST. RESEARCH ONLY. NOT EXECUTION.",
        "Strategy: research_spy_short_hedge on SPY only.",
        "Borrow fee model status: not_modelled_initial_research.",
    ]
    if full:
        lines.append(
            "Full-period: "
            f"CAGR={float(full['cagr_pct']):.4f}%, "
            f"Sharpe={float(full['sharpe_ratio']):.4f}, "
            f"max_drawdown={float(full['max_drawdown_pct']):.4f}%, "
            f"Calmar={float(full['calmar_ratio']):.4f}"
        )
    if oos:
        lines.append(
            "Out-of-sample: "
            f"CAGR={float(oos['cagr_pct']):.4f}%, "
            f"Sharpe={float(oos['sharpe_ratio']):.4f}, "
            f"max_drawdown={float(oos['max_drawdown_pct']):.4f}%, "
            f"Calmar={float(oos['calmar_ratio']):.4f}"
        )
    if full and full.get("research_status") == "not_useful":
        lines.append("Research conclusion: not useful / pause short hedge research.")
    elif full:
        lines.append(f"Research conclusion: {full.get('research_status', 'research_only_observation')}.")
    lines.extend(
        [
            "Warning: short borrow fees and real short constraints are not fully modelled.",
            "Warning: this is research only and not execution approval.",
            f"Saved short hedge results to {results_path}",
            f"Saved short hedge trades to {trades_path}",
            f"Saved short hedge equity curve to {equity_curve_path}",
        ]
    )
    return lines


def find_result(rows: list[dict[str, Any]], strategy_name: str, period: str) -> dict[str, Any] | None:
    return next((row for row in rows if row["strategy_name"] == strategy_name and row["period"] == period), None)


def write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
