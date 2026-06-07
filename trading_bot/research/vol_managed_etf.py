"""Research-only volatility-managed ETF dual momentum lab.

This module models one fixed long-only ETF research hypothesis. It does not
create broker orders, read positions, write SQLite, send alerts, use margin or
leverage, or approve execution.
"""

from __future__ import annotations

import csv
import math
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
from trading_bot.strategies.rotation import buy_and_hold_equity_curve, equal_weight_buy_and_hold_equity_curve


VOL_MANAGED_STRATEGY_NAME = "volatility_managed_dual_momentum_etf"
VOL_MANAGED_ETF_UNIVERSE = [
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
VOL_MANAGED_REGIME_TICKER = "SPY"
VOL_MANAGED_TOP_N = 3
VOL_MANAGED_SMA_WINDOW = 200
VOL_MANAGED_VOL_WINDOW = 63
VOL_MANAGED_TARGET_VOLATILITY_PCT = Decimal("10")
VOL_MANAGED_GROSS_EXPOSURE_CAP = Decimal("1")
VOL_MANAGED_COST_MODEL_NAME = "stock_etf_research_cost_model"

VOL_MANAGED_RESULTS_COLUMNS = [
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
    "turnover",
    "target_volatility_pct",
    "realised_vol_window",
    "gross_exposure_cap",
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

VOL_MANAGED_TRADES_COLUMNS = [
    "created_at",
    "date",
    "strategy_name",
    "ticker",
    "side",
    "reason",
    "quantity",
    "price",
    "notional",
    "target_weight",
    "target_volatility_pct",
    "realised_vol_window",
    "gross_exposure_cap",
    "research_only",
    "preview_only",
    "execution_approved",
]

VOL_MANAGED_EQUITY_COLUMNS = [
    "date",
    "strategy_name",
    "ticker_or_portfolio",
    "period",
    "equity",
    "gross_exposure_pct",
    "cash_weight",
    "selected_tickers",
    "target_volatility_pct",
    "realised_vol_window",
    "gross_exposure_cap",
    "research_only",
    "preview_only",
    "execution_approved",
]

VOL_MANAGED_ITERATION_COLUMNS = [
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
class VolManagedEtfResult:
    results_path: Path
    trades_path: Path
    equity_curve_path: Path
    iteration_log_path: Path
    result_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    equity_rows: list[dict[str, Any]]
    iteration_rows: list[dict[str, Any]]
    summary_lines: list[str]


def run_vol_managed_etf_backtest_files(
    config: AppConfig,
    logger,
    data_dir: Path | str = "data",
) -> VolManagedEtfResult:
    configure_yfinance_cache(config, logger)
    price_by_ticker: dict[str, list[dict[str, Any]]] = {}
    for ticker in VOL_MANAGED_ETF_UNIVERSE:
        frame = download_backtest_prices(config, ticker)
        price_by_ticker[ticker] = [
            {"date": index.date().isoformat(), "close": float(row["close"])}
            for index, row in frame.iterrows()
            if float(row["close"]) > 0
        ]
    created_at = datetime.now(timezone.utc).isoformat()
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))
    return build_and_write_vol_managed_etf_outputs(
        price_by_ticker=price_by_ticker,
        starting_cash=config.backtest.starting_cash,
        cost_model=cost_model,
        data_dir=Path(data_dir),
        created_at=created_at,
    )


def build_and_write_vol_managed_etf_outputs(
    price_by_ticker: dict[str, list[dict[str, Any]]],
    starting_cash: float,
    cost_model: CostModel,
    data_dir: Path,
    created_at: str,
) -> VolManagedEtfResult:
    aligned_rows = align_price_rows(price_by_ticker)
    equity_rows, trade_rows = simulate_vol_managed_dual_momentum(
        aligned_rows=aligned_rows,
        starting_cash=starting_cash,
        cost_model=cost_model,
        created_at=created_at,
    )
    result_rows = build_vol_managed_result_rows(aligned_rows, equity_rows, trade_rows, starting_cash, cost_model, created_at)
    iteration_rows = build_iteration_rows(created_at, result_rows)
    results_path = data_dir / "vol_managed_etf_results.csv"
    trades_path = data_dir / "vol_managed_etf_trades.csv"
    equity_curve_path = data_dir / "vol_managed_etf_equity_curve.csv"
    iteration_log_path = data_dir / "vol_managed_etf_iteration_log.csv"
    write_rows(results_path, VOL_MANAGED_RESULTS_COLUMNS, result_rows)
    write_rows(trades_path, VOL_MANAGED_TRADES_COLUMNS, trade_rows)
    write_rows(equity_curve_path, VOL_MANAGED_EQUITY_COLUMNS, equity_rows)
    write_rows(iteration_log_path, VOL_MANAGED_ITERATION_COLUMNS, iteration_rows)
    return VolManagedEtfResult(
        results_path=results_path,
        trades_path=trades_path,
        equity_curve_path=equity_curve_path,
        iteration_log_path=iteration_log_path,
        result_rows=result_rows,
        trade_rows=trade_rows,
        equity_rows=equity_rows,
        iteration_rows=iteration_rows,
        summary_lines=build_summary(result_rows, results_path, trades_path, equity_curve_path, iteration_log_path),
    )


def align_price_rows(price_by_ticker: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    date_sets = [
        {str(row["date"]) for row in rows}
        for ticker, rows in price_by_ticker.items()
        if ticker in VOL_MANAGED_ETF_UNIVERSE and rows
    ]
    if not date_sets:
        return []
    dates = sorted(set.intersection(*date_sets))
    lookup = {
        ticker: {str(row["date"]): float(row["close"]) for row in rows}
        for ticker, rows in price_by_ticker.items()
        if ticker in VOL_MANAGED_ETF_UNIVERSE
    }
    return [
        {"date": date, "close": {ticker: lookup[ticker][date] for ticker in VOL_MANAGED_ETF_UNIVERSE if ticker in lookup}}
        for date in dates
    ]


def simulate_vol_managed_dual_momentum(
    aligned_rows: list[dict[str, Any]],
    starting_cash: float,
    cost_model: CostModel,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cash = starting_cash
    shares: dict[str, float] = {}
    closes_by_ticker = {ticker: [] for ticker in VOL_MANAGED_ETF_UNIVERSE}
    equity_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    current_month = ""

    for row in aligned_rows:
        date = str(row["date"])
        close_by_ticker = {ticker: float(price) for ticker, price in row["close"].items()}
        for ticker in VOL_MANAGED_ETF_UNIVERSE:
            closes_by_ticker[ticker].append(close_by_ticker[ticker])

        month = date[:7]
        if month != current_month:
            current_month = month
            equity = mark_to_market_equity(cash, close_by_ticker, shares)
            target_weights = target_weights_for_day(close_by_ticker, closes_by_ticker)
            cash = rebalance_to_weights(created_at, date, cash, shares, close_by_ticker, target_weights, equity, cost_model, trade_rows)

        ending_equity = mark_to_market_equity(cash, close_by_ticker, shares)
        exposure_value = sum(shares.get(ticker, 0.0) * close_by_ticker[ticker] for ticker in shares)
        gross_exposure = exposure_value / ending_equity if ending_equity > 0 else 0.0
        equity_rows.append(
            {
                "date": date,
                "strategy_name": VOL_MANAGED_STRATEGY_NAME,
                "ticker_or_portfolio": "portfolio",
                "period": "full_period",
                "equity": ending_equity,
                "gross_exposure_pct": gross_exposure * 100,
                "cash_weight": max(0.0, 1.0 - gross_exposure),
                "selected_tickers": ";".join(sorted(shares)),
                "target_volatility_pct": VOL_MANAGED_TARGET_VOLATILITY_PCT,
                "realised_vol_window": VOL_MANAGED_VOL_WINDOW,
                "gross_exposure_cap": VOL_MANAGED_GROSS_EXPOSURE_CAP,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
            }
        )

    return equity_rows, trade_rows


def target_weights_for_day(
    close_by_ticker: dict[str, float],
    closes_by_ticker: dict[str, list[float]],
) -> dict[str, float]:
    spy_sma = simple_moving_average(closes_by_ticker[VOL_MANAGED_REGIME_TICKER], VOL_MANAGED_SMA_WINDOW)
    if spy_sma is None or close_by_ticker[VOL_MANAGED_REGIME_TICKER] <= spy_sma:
        return {}

    candidates: list[tuple[float, str, float]] = []
    for ticker in VOL_MANAGED_ETF_UNIVERSE:
        sma = simple_moving_average(closes_by_ticker[ticker], VOL_MANAGED_SMA_WINDOW)
        score = composite_momentum_score(closes_by_ticker[ticker])
        vol = realised_volatility(closes_by_ticker[ticker], VOL_MANAGED_VOL_WINDOW)
        if sma is None or score is None or vol is None or vol <= 0:
            continue
        if close_by_ticker[ticker] > sma:
            candidates.append((score, ticker, vol))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    selected = candidates[:VOL_MANAGED_TOP_N]
    if not selected:
        return {}

    inv_vol = {ticker: 1.0 / vol for _, ticker, vol in selected}
    total_inv_vol = sum(inv_vol.values())
    base_weights = {ticker: value / total_inv_vol for ticker, value in inv_vol.items()}
    estimated_vol = estimate_portfolio_volatility(base_weights, closes_by_ticker)
    exposure_multiplier = min(1.0, (float(VOL_MANAGED_TARGET_VOLATILITY_PCT) / 100) / estimated_vol) if estimated_vol > 0 else 0.0
    return {ticker: weight * exposure_multiplier for ticker, weight in base_weights.items()}


def rebalance_to_weights(
    created_at: str,
    date: str,
    cash: float,
    shares: dict[str, float],
    close_by_ticker: dict[str, float],
    target_weights: dict[str, float],
    equity: float,
    cost_model: CostModel,
    trade_rows: list[dict[str, Any]],
) -> float:
    for ticker in sorted(set(shares) - set(target_weights)):
        quantity = shares.pop(ticker)
        fill_price = float(adjusted_sell_fill_price(close_by_ticker[ticker], cost_model))
        cash += quantity * fill_price
        trade_rows.append(trade_row(created_at, date, ticker, "sell", "removed_from_target_weights", quantity, fill_price, 0.0))

    for ticker, target_weight in sorted(target_weights.items()):
        current_value = shares.get(ticker, 0.0) * close_by_ticker[ticker]
        target_value = equity * target_weight
        delta_value = target_value - current_value
        if abs(delta_value) < 1e-9:
            continue
        if delta_value > 0:
            fill_price = float(adjusted_buy_fill_price(close_by_ticker[ticker], cost_model))
            quantity = delta_value / fill_price if fill_price > 0 else 0.0
            shares[ticker] = shares.get(ticker, 0.0) + quantity
            cash -= quantity * fill_price
            trade_rows.append(trade_row(created_at, date, ticker, "buy", "target_inverse_vol_weight", quantity, fill_price, target_weight))
        else:
            quantity = min(shares.get(ticker, 0.0), abs(delta_value) / close_by_ticker[ticker])
            fill_price = float(adjusted_sell_fill_price(close_by_ticker[ticker], cost_model))
            shares[ticker] = shares.get(ticker, 0.0) - quantity
            if shares[ticker] <= 1e-10:
                shares.pop(ticker, None)
            cash += quantity * fill_price
            trade_rows.append(trade_row(created_at, date, ticker, "sell", "reduce_to_target_weight", quantity, fill_price, target_weight))
    return cash


def trade_row(
    created_at: str,
    date: str,
    ticker: str,
    side: str,
    reason: str,
    quantity: float,
    price: float,
    target_weight: float,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "date": date,
        "strategy_name": VOL_MANAGED_STRATEGY_NAME,
        "ticker": ticker,
        "side": side,
        "reason": reason,
        "quantity": quantity,
        "price": price,
        "notional": quantity * price,
        "target_weight": target_weight,
        "target_volatility_pct": VOL_MANAGED_TARGET_VOLATILITY_PCT,
        "realised_vol_window": VOL_MANAGED_VOL_WINDOW,
        "gross_exposure_cap": VOL_MANAGED_GROSS_EXPOSURE_CAP,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_vol_managed_result_rows(
    aligned_rows: list[dict[str, Any]],
    equity_rows: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
    starting_cash: float,
    cost_model: CostModel,
    created_at: str,
) -> list[dict[str, Any]]:
    dates = [str(row["date"]) for row in aligned_rows]
    strategy_equity = [float(row["equity"]) for row in equity_rows]
    spy_curve = buy_and_hold_equity_curve([float(row["close"]["SPY"]) for row in aligned_rows], starting_cash) if aligned_rows else []
    equal_weight_curve = equal_weight_buy_and_hold_equity_curve(
        {ticker: [float(row["close"][ticker]) for row in aligned_rows] for ticker in VOL_MANAGED_ETF_UNIVERSE},
        starting_cash,
    ) if aligned_rows else []
    rows: list[dict[str, Any]] = []
    for strategy_name, curve in [
        (VOL_MANAGED_STRATEGY_NAME, strategy_equity),
        ("spy_buy_and_hold_baseline", spy_curve),
        ("equal_weight_buy_and_hold_baseline", equal_weight_curve),
        ("cash_flat_baseline", [starting_cash for _ in aligned_rows]),
    ]:
        for period, start_index, end_index in period_slices(curve):
            period_curve = curve[start_index:end_index]
            trades = trade_count_for_period(strategy_name, trade_rows, dates, start_index, end_index, len(period_curve))
            turnover = turnover_for_period(strategy_name, trade_rows, dates, start_index, end_index, starting_cash)
            rows.append(result_row(created_at, strategy_name, period, period_curve, trades, turnover, cost_model))
    apply_rotation_comparison(rows)
    return rows


def result_row(
    created_at: str,
    strategy_name: str,
    period: str,
    equity_curve: list[float],
    number_of_trades: int,
    turnover: float,
    cost_model: CostModel,
) -> dict[str, Any]:
    starting_equity = equity_curve[0] if equity_curve else 0.0
    final_equity = equity_curve[-1] if equity_curve else starting_equity
    total_return_pct = ((final_equity - starting_equity) / starting_equity) * 100 if starting_equity > 0 else 0.0
    cagr_pct = calculate_cagr_pct(starting_equity, final_equity, len(equity_curve))
    sharpe = calculate_sharpe_ratio(equity_curve)
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    calmar = cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct else 0.0
    status, conclusion, next_step = conclusion_for_result(strategy_name, cagr_pct, sharpe, calmar, max_drawdown_pct)
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_drawdown_pct,
        "calmar_ratio": calmar,
        "number_of_trades": number_of_trades,
        "turnover": turnover,
        "target_volatility_pct": VOL_MANAGED_TARGET_VOLATILITY_PCT,
        "realised_vol_window": VOL_MANAGED_VOL_WINDOW,
        "gross_exposure_cap": VOL_MANAGED_GROSS_EXPOSURE_CAP,
        "cost_model_name": VOL_MANAGED_COST_MODEL_NAME,
        "commission_per_trade": cost_model.commission_per_trade,
        "commission_bps": cost_model.commission_bps,
        "spread_bps": cost_model.spread_bps,
        "slippage_bps": cost_model.slippage_bps,
        "research_status": status,
        "research_conclusion": conclusion,
        "required_next_step": next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def apply_rotation_comparison(rows: list[dict[str, Any]]) -> None:
    rotation_oos = read_monthly_rotation_oos_row()
    candidate_oos = find_result(rows, VOL_MANAGED_STRATEGY_NAME, "out_of_sample")
    if not rotation_oos or not candidate_oos:
        return
    candidate_sharpe = float(candidate_oos["sharpe_ratio"])
    candidate_calmar = float(candidate_oos["calmar_ratio"])
    candidate_drawdown = float(candidate_oos["max_drawdown_pct"])
    rotation_sharpe = parse_float(rotation_oos.get("sharpe_ratio"))
    rotation_calmar = parse_float(rotation_oos.get("calmar_ratio"))
    rotation_drawdown = parse_float(rotation_oos.get("max_drawdown_pct"))
    if candidate_sharpe > rotation_sharpe and candidate_calmar > rotation_calmar:
        candidate_oos["research_status"] = "promising_research_candidate"
        candidate_oos["research_conclusion"] = "Out-of-sample Sharpe and Calmar improve versus saved monthly ETF rotation; still research-only."
        candidate_oos["required_next_step"] = "Review walk-forward, drawdown periods, turnover, and portfolio role before any preview discussion."
    elif candidate_drawdown < rotation_drawdown:
        candidate_oos["research_status"] = "defensive_candidate"
        candidate_oos["research_conclusion"] = "Out-of-sample drawdown is lower than saved monthly ETF rotation, but growth/risk-adjusted tradeoffs need review."
        candidate_oos["required_next_step"] = "Compare CAGR drag, turnover, and defensive role against ETF rotation."
    elif candidate_sharpe < rotation_sharpe and candidate_calmar < rotation_calmar and candidate_drawdown >= rotation_drawdown:
        candidate_oos["research_status"] = "secondary_candidate"
        candidate_oos["research_conclusion"] = "Out-of-sample Sharpe/Calmar and drawdown do not improve versus saved monthly ETF rotation."
        candidate_oos["required_next_step"] = "Keep research-only; do not promote without stronger out-of-sample evidence."


def read_monthly_rotation_oos_row(path: Path = Path("data/etf_rotation_results.csv")) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row.get("strategy_name") == "monthly_etf_momentum_rotation" and row.get("period") == "out_of_sample":
                return row
    return None


def conclusion_for_result(
    strategy_name: str,
    cagr_pct: float,
    sharpe_ratio: float,
    calmar_ratio: float,
    max_drawdown_pct: float,
) -> tuple[str, str, str]:
    if strategy_name != VOL_MANAGED_STRATEGY_NAME:
        return (
            "benchmark_context",
            "Benchmark row for context only; not a vol-managed strategy candidate.",
            "Use this row only to compare the research strategy against baseline alternatives.",
        )
    if cagr_pct < 0 or sharpe_ratio < 0 or calmar_ratio < 0:
        return (
            "not_useful",
            "CAGR, Sharpe, or Calmar is negative; do not continue to preview or execution.",
            "Pause this hypothesis unless future fixed research evidence changes the case.",
        )
    if max_drawdown_pct < 20:
        return (
            "defensive_candidate",
            "Positive metrics with controlled drawdown; compare against monthly ETF rotation before any next step.",
            "Review saved ETF rotation comparison, walk-forward stability, turnover, and drawdown periods.",
        )
    return (
        "research_only_observation",
        "Positive metrics, but benchmark comparison and robustness review are still required.",
        "Keep research-only and compare against ETF rotation before any preview discussion.",
    )


def build_iteration_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    full = find_result(rows, VOL_MANAGED_STRATEGY_NAME, "full_period")
    oos = find_result(rows, VOL_MANAGED_STRATEGY_NAME, "out_of_sample")
    result_summary = "full_period and out_of_sample rows unavailable"
    decision = "research_only_observation"
    next_question = "Compare against monthly ETF rotation when result rows are available."
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
            "iteration_id": "vol_managed_etf_001",
            "hypothesis": "Monthly ETF dual momentum may improve risk-adjusted returns by using inverse-volatility sizing and a 10% annual volatility cap.",
            "strategy_name": VOL_MANAGED_STRATEGY_NAME,
            "allowed_parameter_set": "monthly rebalance; top_N=3; 200-day SMA asset filter; SPY 200-day regime filter; 63-day realised volatility; 10% target volatility; gross exposure capped at 1.0",
            "reason_for_testing": "First advanced long-only ETF research idea from the deep research shortlist, tested with fixed parameters and no search.",
            "result_summary": result_summary,
            "decision": decision,
            "next_research_question": next_question,
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
        }
    ]


def build_summary(
    rows: list[dict[str, Any]],
    results_path: Path,
    trades_path: Path,
    equity_curve_path: Path,
    iteration_log_path: Path,
) -> list[str]:
    full = find_result(rows, VOL_MANAGED_STRATEGY_NAME, "full_period")
    oos = find_result(rows, VOL_MANAGED_STRATEGY_NAME, "out_of_sample")
    lines = [
        "VOL-MANAGED ETF BACKTEST. RESEARCH ONLY. NOT EXECUTION.",
        "Strategy: volatility_managed_dual_momentum_etf.",
        "Hypothesis: monthly ETF dual momentum with inverse-volatility sizing and a 10% annual volatility cap.",
        "Fixed parameters: top_N=3, SMA200 filters, 63-day realised volatility, gross exposure capped at 1.0.",
    ]
    if full:
        lines.append(metric_line("Full-period", full))
    if oos:
        lines.append(metric_line("Out-of-sample", oos))
        lines.append(f"Research conclusion: {oos['research_status']} - {oos['research_conclusion']}")
    if read_monthly_rotation_oos_row():
        lines.append("Comparison: monthly ETF rotation out-of-sample row was available for status context.")
    else:
        lines.append("Comparison: monthly ETF rotation out-of-sample row was not available; compare later.")
    lines.extend(
        [
            "Warning: this is research only and not execution approval.",
            f"Saved vol-managed ETF results to {results_path}",
            f"Saved vol-managed ETF trades to {trades_path}",
            f"Saved vol-managed ETF equity curve to {equity_curve_path}",
            f"Saved vol-managed ETF iteration log to {iteration_log_path}",
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


def composite_momentum_score(values: list[float]) -> float | None:
    windows = [21, 63, 126, 252]
    scores = [trailing_return(values, window) for window in windows]
    if any(score is None for score in scores):
        return None
    return sum(float(score) for score in scores) / len(scores)


def simple_moving_average(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def trailing_return(values: list[float], window: int) -> float | None:
    if len(values) <= window:
        return None
    start = values[-window - 1]
    end = values[-1]
    if start <= 0:
        return None
    return (end / start) - 1.0


def realised_volatility(values: list[float], window: int) -> float | None:
    if len(values) <= window:
        return None
    window_values = values[-window - 1:]
    returns = [
        (window_values[index] / window_values[index - 1]) - 1.0
        for index in range(1, len(window_values))
        if window_values[index - 1] > 0
    ]
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252)


def estimate_portfolio_volatility(weights: dict[str, float], closes_by_ticker: dict[str, list[float]]) -> float:
    if not weights:
        return 0.0
    vols = {
        ticker: realised_volatility(closes_by_ticker[ticker], VOL_MANAGED_VOL_WINDOW) or 0.0
        for ticker in weights
    }
    return math.sqrt(sum((weights[ticker] * vols[ticker]) ** 2 for ticker in weights))


def mark_to_market_equity(cash: float, close_by_ticker: dict[str, float], shares: dict[str, float]) -> float:
    return cash + sum(quantity * close_by_ticker[ticker] for ticker, quantity in shares.items())


def period_slices(equity_curve: list[float]) -> list[tuple[str, int, int]]:
    if not equity_curve:
        return [("full_period", 0, 0), ("in_sample", 0, 0), ("out_of_sample", 0, 0)]
    total = len(equity_curve)
    if total < 3:
        return [("full_period", 0, total), ("in_sample", 0, total), ("out_of_sample", 0, total)]
    split = max(1, min(total - 1, int(total * 0.7)))
    return [("full_period", 0, total), ("in_sample", 0, split), ("out_of_sample", split, total)]


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
    if strategy_name in {"spy_buy_and_hold_baseline", "equal_weight_buy_and_hold_baseline"}:
        return 1 if period_length >= 2 else 0
    if not dates or start_index >= len(dates) or end_index <= start_index:
        return 0
    if start_index == 0 and end_index == len(dates):
        return len(trade_rows)
    start_date = dates[start_index]
    end_date = dates[end_index - 1]
    return sum(1 for row in trade_rows if start_date <= str(row["date"]) <= end_date)


def turnover_for_period(
    strategy_name: str,
    trade_rows: list[dict[str, Any]],
    dates: list[str],
    start_index: int,
    end_index: int,
    starting_cash: float,
) -> float:
    if strategy_name != VOL_MANAGED_STRATEGY_NAME or starting_cash <= 0:
        return 0.0
    if not dates or start_index >= len(dates) or end_index <= start_index:
        return 0.0
    start_date = dates[start_index]
    end_date = dates[end_index - 1]
    return sum(float(row["notional"]) for row in trade_rows if start_date <= str(row["date"]) <= end_date) / starting_cash


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def find_result(rows: list[dict[str, Any]], strategy_name: str, period: str) -> dict[str, Any] | None:
    return next((row for row in rows if row["strategy_name"] == strategy_name and row["period"] == period), None)


def write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
