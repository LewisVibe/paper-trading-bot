"""Research-only high-growth single-stock strategy lab.

This lab uses a fixed liquid large-cap stock universe and daily yfinance data.
It does not call Alpaca, load config, read positions, create orders, write
SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTPUT_FILES = {
    "report": Path("data/high_growth_stock_lab.csv"),
    "summary": Path("data/high_growth_stock_lab_summary.csv"),
    "trades": Path("data/high_growth_stock_lab_trades.csv"),
    "costs": Path("data/high_growth_stock_lab_costs.csv"),
    "splits": Path("data/high_growth_stock_lab_splits.csv"),
    "drawdowns": Path("data/high_growth_stock_lab_drawdowns.csv"),
    "concentration": Path("data/high_growth_stock_lab_concentration.csv"),
}

STOCK_UNIVERSE = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "AMD", "TSLA", "NFLX"]
BENCHMARK_TICKERS = ["QQQ", "SPY"]
NEW_CODEX_STRATEGIES = {
    "codex_high_growth_breakout_acceleration",
    "codex_high_growth_crash_rebound_leader",
}
HISTORY_PERIOD = "10y"
DAILY_INTERVAL = "1d"
STARTING_EQUITY = 10000.0
MOMENTUM_WINDOWS = [63, 126, 252]
TREND_WINDOW = 200
VOL_WINDOW = 63
REBALANCE_COST_BPS = [0, 10, 25, 50]
SPLITS = [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]
QQQ_BASELINE = {"cagr_pct": 16.8429, "sharpe_ratio": 1.0027, "max_drawdown_pct": -23.4576, "calmar_ratio": 0.718}

STRATEGIES = [
    "concentrated_growth_momentum_top1",
    "concentrated_growth_momentum_top2",
    "concentrated_growth_momentum_top3",
    "codex_high_conviction_growth_persistence",
    "codex_growth_drawdown_reentry",
    "codex_high_growth_breakout_acceleration",
    "codex_high_growth_crash_rebound_leader",
]

REPORT_COLUMNS = [
    "created_at",
    "strategy_name",
    "period",
    "data_status",
    "cagr_pct",
    "annualised_volatility_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "total_return_pct",
    "trade_count",
    "rebalance_count",
    "turnover",
    "average_holdings",
    "max_single_name_concentration",
    "time_in_cash_pct",
    "top_contributing_tickers",
    "cost_sensitivity_label",
    "split_sensitivity_label",
    "concentration_warning",
    "survivorship_bias_warning",
    "single_name_event_risk_warning",
    "stock_specific_gap_risk_warning",
    "decision_label",
    "notes",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

TRADE_COLUMNS = [
    "created_at",
    "strategy_name",
    "rebalance_date",
    "selected_tickers",
    "weights",
    "regime_status",
    "reason",
    "turnover",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

COST_COLUMNS = REPORT_COLUMNS + ["cost_bps", "cost_stress_cagr_pct", "cost_stress_calmar_ratio"]
SPLIT_COLUMNS = REPORT_COLUMNS + ["split_name", "split_fraction", "split_start_date", "split_end_date"]
DRAWDOWN_COLUMNS = REPORT_COLUMNS + ["drawdown_start", "drawdown_trough", "drawdown_recovery", "drawdown_recovered", "drawdown_days"]
CONCENTRATION_COLUMNS = REPORT_COLUMNS + ["ticker", "average_weight", "max_weight", "contribution_pct", "holding_days"]


@dataclass
class StrategySimulation:
    name: str
    curve: list[dict[str, Any]]
    trades: list[dict[str, Any]]
    contributions: dict[str, float]
    holding_weights: dict[str, list[float]]
    data_status: str
    notes: str


@dataclass
class HighGrowthStockLabResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    concentration_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_lab(root_dir: Path | str = ".") -> HighGrowthStockLabResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    price_data, data_errors = download_daily_price_data(STOCK_UNIVERSE + BENCHMARK_TICKERS, root / "data" / "yfinance_cache")
    simulations = build_simulations(price_data, data_errors)
    report_rows = [build_report_row(created_at, simulation, "full_period") for simulation in simulations]
    cost_rows = build_cost_rows(created_at, simulations)
    split_rows = build_split_rows(created_at, simulations)
    drawdown_rows = build_drawdown_rows(created_at, simulations)
    concentration_rows = build_concentration_rows(created_at, simulations)
    trade_rows = [trade_row(created_at, trade) for simulation in simulations for trade in simulation.trades]
    apply_decision_labels(report_rows, cost_rows, split_rows, concentration_rows)
    summary_rows = build_summary_rows(created_at, report_rows, cost_rows, split_rows, drawdown_rows, concentration_rows, data_errors)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["trades"], TRADE_COLUMNS, trade_rows)
    write_rows(output_paths["costs"], COST_COLUMNS, cost_rows)
    write_rows(output_paths["splits"], SPLIT_COLUMNS, split_rows)
    write_rows(output_paths["drawdowns"], DRAWDOWN_COLUMNS, drawdown_rows)
    write_rows(output_paths["concentration"], CONCENTRATION_COLUMNS, concentration_rows)
    return HighGrowthStockLabResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        trade_rows=trade_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        drawdown_rows=drawdown_rows,
        concentration_rows=concentration_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_high_growth_stock_lab(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    report_path = root / OUTPUT_FILES["report"]
    if not summary_path.exists() or not report_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-lab` first."]
    summary = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock lab saved display. Research only; execution_approved=False.",
        f"Best high-growth stock candidate: {summary_value(summary, 'best_high_growth_stock_candidate')}",
        f"Best new Codex-designed candidate: {summary_value(summary, 'best_new_codex_designed_candidate')}",
        f"Comparison versus qqq_100_trend_gate: {summary_value(summary, 'comparison_vs_qqq_100_trend_gate')}",
        f"Comparison versus concentrated_growth_momentum_top3: {summary_value(summary, 'comparison_vs_concentrated_growth_momentum_top3')}",
        f"Biggest concentration/outlier warning: {summary_value(summary, 'biggest_concentration_outlier_warning')}",
        f"Worst drawdown warning: {summary_value(summary, 'worst_drawdown_warning')}",
        f"Cost/split sensitivity warning: {summary_value(summary, 'cost_split_sensitivity_warning')}",
        f"Final research conclusion: {summary_value(summary, 'final_research_conclusion')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no Alpaca commands, order instructions, paper execution, or scheduling approval.",
    ]


def download_daily_price_data(tickers: list[str], cache_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    price_data: dict[str, list[dict[str, Any]]] = {}
    data_errors: dict[str, str] = {}
    try:
        import yfinance as yf

        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            yf.set_tz_cache_location(str(cache_dir))
        except AttributeError:
            pass
    except Exception as exc:
        return {}, {ticker: f"yfinance unavailable: {exc}" for ticker in tickers}
    for ticker in tickers:
        try:
            frame = yf.download(ticker, period=HISTORY_PERIOD, interval=DAILY_INTERVAL, auto_adjust=True, progress=False, threads=False)
            if frame is None or frame.empty:
                data_errors[ticker] = "No daily market data returned by yfinance."
                continue
            close = close_series(frame, ticker)
            rows = [{"date": index.date().isoformat(), "close": float(value)} for index, value in close.items() if value is not None and float(value) > 0]
            if len(rows) < max(MOMENTUM_WINDOWS) + 5:
                data_errors[ticker] = f"Not enough daily history; got {len(rows)} usable rows."
                continue
            price_data[ticker] = rows
        except Exception as exc:
            data_errors[ticker] = str(exc)
    return price_data, data_errors


def close_series(frame: Any, ticker: str) -> Any:
    columns = frame.columns
    has_multi_index = getattr(columns, "nlevels", 1) > 1
    if has_multi_index:
        for key in (("Close", ticker), (ticker, "Close")):
            if key in columns:
                value = frame[key]
                return value.iloc[:, 0].dropna() if getattr(value, "ndim", 1) == 2 else value.dropna()
        if "Close" in columns.get_level_values(0):
            value = frame.xs("Close", axis=1, level=0)
            return value.iloc[:, 0].dropna() if getattr(value, "ndim", 1) == 2 else value.dropna()
        if "Close" in columns.get_level_values(1):
            value = frame.xs("Close", axis=1, level=1)
            return value.iloc[:, 0].dropna() if getattr(value, "ndim", 1) == 2 else value.dropna()
    value = frame["Close"]
    return value.iloc[:, 0].dropna() if getattr(value, "ndim", 1) == 2 else value.dropna()


def build_simulations(price_data: dict[str, list[dict[str, Any]]], data_errors: dict[str, str]) -> list[StrategySimulation]:
    stock_data = {ticker: rows for ticker, rows in price_data.items() if ticker in STOCK_UNIVERSE}
    if len(stock_data) < 3 or not any(ticker in price_data for ticker in BENCHMARK_TICKERS):
        reason = f"Insufficient market data; stock_rows={len(stock_data)}; errors={len(data_errors)}"
        return [insufficient_simulation(name, reason) for name in STRATEGIES + ["equal_weight_stock_universe_buy_and_hold", "qqq_buy_and_hold_benchmark", "spy_buy_and_hold_benchmark"]]
    dates = common_dates(stock_data)
    simulations = [
        simulate_momentum_strategy("concentrated_growth_momentum_top1", 1, price_data, dates),
        simulate_momentum_strategy("concentrated_growth_momentum_top2", 2, price_data, dates),
        simulate_momentum_strategy("concentrated_growth_momentum_top3", 3, price_data, dates),
        simulate_high_conviction_growth_persistence(price_data, dates),
        simulate_growth_drawdown_reentry(price_data, dates),
        simulate_high_growth_breakout_acceleration(price_data, dates),
        simulate_high_growth_crash_rebound_leader(price_data, dates),
        simulate_equal_weight_benchmark(price_data, dates),
    ]
    if "QQQ" in price_data:
        simulations.append(simulate_buy_and_hold("qqq_buy_and_hold_benchmark", "QQQ", price_data["QQQ"]))
    if "SPY" in price_data:
        simulations.append(simulate_buy_and_hold("spy_buy_and_hold_benchmark", "SPY", price_data["SPY"]))
    return simulations


def insufficient_simulation(name: str, reason: str) -> StrategySimulation:
    return StrategySimulation(name=name, curve=[], trades=[], contributions={}, holding_weights={}, data_status="insufficient_market_data", notes=reason)


def common_dates(stock_data: dict[str, list[dict[str, Any]]]) -> list[str]:
    counts = Counter(date for rows in stock_data.values() for date in [row["date"] for row in rows])
    minimum = max(3, int(len(stock_data) * 0.7))
    return sorted(date for date, count in counts.items() if count >= minimum)


def simulate_momentum_strategy(name: str, top_n: int, price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        if not regime_ok(price_data, dates[index]):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        ranked = rank_growth_stocks(price_data, dates, index)
        eligible = [ticker for ticker, _score in ranked if above_sma(price_data[ticker], dates[index], TREND_WINDOW)]
        selected = eligible[:top_n]
        if not selected:
            return {}, "No stock passes own SMA200 and momentum filter; holding cash.", "cash_no_stock_passes"
        return equal_weights(selected), f"Monthly top {top_n} composite momentum stock(s) above SMA200 with QQQ/SPY regime gate.", "risk_on"

    return simulate_strategy(name, price_data, dates, selector, "Fixed monthly composite 63/126/252-day momentum; top N stocks; own SMA200 and QQQ/SPY SMA200 regime gate.")


def simulate_high_conviction_growth_persistence(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        if not regime_ok(price_data, dates[index]):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        scores = []
        for ticker in STOCK_UNIVERSE:
            rows = price_data.get(ticker, [])
            if not enough_history(rows, dates[index], 252):
                continue
            close = price_on(rows, dates[index])
            high_252 = rolling_high(rows, dates[index], 252)
            proximity = close / high_252 if high_252 > 0 else 0.0
            vol = realised_volatility(rows, dates[index], VOL_WINDOW)
            momentum = composite_momentum(rows, dates[index])
            if close > sma(rows, dates[index], TREND_WINDOW) and proximity >= 0.85 and momentum > 0:
                scores.append((ticker, momentum + proximity - min(vol, 1.5) * 0.25))
        selected = [ticker for ticker, _score in sorted(scores, key=lambda item: item[1], reverse=True)[:2]]
        if not selected:
            return {}, "No persistent winner near highs passes fixed filters; holding cash.", "cash_no_persistence"
        return equal_weights(selected), "Codex high-conviction persistence: top 1-2 stocks with positive 126/252 momentum, near 52-week highs, above SMA200, volatility penalty.", "risk_on_persistent_winners"

    return simulate_strategy(
        "codex_high_conviction_growth_persistence",
        price_data,
        dates,
        selector,
        "Fixed high-conviction rules: QQQ/SPY regime gate; own SMA200; positive momentum; within 15% of 252-day high; 63-day volatility penalty; hold top 1-2.",
    )


def simulate_growth_drawdown_reentry(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        if not regime_ok(price_data, dates[index]):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        candidates = []
        for ticker, score in rank_growth_stocks(price_data, dates, index):
            rows = price_data[ticker]
            close = price_on(rows, dates[index])
            high_126 = rolling_high(rows, dates[index], 126)
            drawdown_from_high = close / high_126 - 1.0 if high_126 > 0 else -1.0
            recovered = close > sma(rows, dates[index], 50) and close > sma(rows, dates[index], TREND_WINDOW)
            if drawdown_from_high > -0.25 and recovered:
                candidates.append((ticker, score))
        selected = [ticker for ticker, _score in candidates[:2]]
        if not selected:
            return {}, "Selected stocks are too far below recent highs or lack 50/200-day recovery confirmation; holding cash.", "cash_drawdown_pause"
        return equal_weights(selected), "Codex drawdown/reentry: top 1-2 momentum stocks, pause entries after >25% drawdown from 126-day high until 50/200-day recovery.", "risk_on_reentry_confirmed"

    return simulate_strategy(
        "codex_growth_drawdown_reentry",
        price_data,
        dates,
        selector,
        "Fixed re-entry rules: QQQ/SPY regime gate; avoid new entries after >25% fall from 126-day high; require close above SMA50 and SMA200; hold top 1-2.",
    )


def simulate_high_growth_breakout_acceleration(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        if not regime_ok(price_data, dates[index]):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        scores = []
        for ticker in STOCK_UNIVERSE:
            rows = price_data.get(ticker, [])
            if not enough_history(rows, dates[index], 252):
                continue
            close = price_on(rows, dates[index])
            high_252 = rolling_high(rows, dates[index], 252)
            proximity = close / high_252 if high_252 > 0 else 0.0
            acceleration = momentum_return(rows, dates[index], 63) - momentum_return(rows, dates[index], 126)
            momentum = composite_momentum(rows, dates[index])
            if above_sma(rows, dates[index], 50) and above_sma(rows, dates[index], 200) and proximity >= 0.95 and momentum > 0 and acceleration > -0.05:
                scores.append((ticker, momentum + acceleration + proximity))
        selected = [ticker for ticker, _score in sorted(scores, key=lambda item: item[1], reverse=True)[:2]]
        if not selected:
            return {}, "No stock is close enough to a 52-week high with positive momentum acceleration; holding cash.", "cash_no_breakout"
        return equal_weights(selected), "Codex breakout acceleration: top 1-2 stocks near 52-week highs, above SMA50/SMA200, positive composite momentum, fixed acceleration filter.", "risk_on_breakout_acceleration"

    return simulate_strategy(
        "codex_high_growth_breakout_acceleration",
        price_data,
        dates,
        selector,
        "Fixed breakout rules: QQQ/SPY SMA200 regime gate; stock above SMA50 and SMA200; within 5% of 252-day high; positive 63/126/252 momentum; 63-vs-126 acceleration not deeply negative; hold top 1-2.",
    )


def simulate_high_growth_crash_rebound_leader(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        if not market_recovery_ok(price_data, dates[index]):
            return {}, "QQQ/SPY recovery regime is not confirmed; holding cash.", "risk_off_no_recovery"
        scores = []
        for ticker in STOCK_UNIVERSE:
            rows = price_data.get(ticker, [])
            if not enough_history(rows, dates[index], 252):
                continue
            close = price_on(rows, dates[index])
            low_126 = rolling_low(rows, dates[index], 126)
            high_126 = rolling_high(rows, dates[index], 126)
            rebound_from_low = close / low_126 - 1.0 if low_126 > 0 else 0.0
            still_below_high = close / high_126 - 1.0 if high_126 > 0 else -1.0
            recovery_momentum = momentum_return(rows, dates[index], 63)
            if above_sma(rows, dates[index], 50) and above_sma(rows, dates[index], 200) and rebound_from_low >= 0.15 and recovery_momentum > 0.08 and still_below_high > -0.30:
                scores.append((ticker, recovery_momentum + rebound_from_low + composite_momentum(rows, dates[index]) * 0.5))
        selected = [ticker for ticker, _score in sorted(scores, key=lambda item: item[1], reverse=True)[:2]]
        if not selected:
            return {}, "No stock has reclaimed SMA50/SMA200 with fixed rebound leadership confirmation; holding cash.", "cash_no_rebound_leader"
        return equal_weights(selected), "Codex crash-rebound leader: top 1-2 stocks that reclaimed SMA50/SMA200, rebounded at least 15% from 126-day low, and show positive 63-day recovery momentum.", "risk_on_rebound_leader"

    return simulate_strategy(
        "codex_high_growth_crash_rebound_leader",
        price_data,
        dates,
        selector,
        "Fixed rebound rules: QQQ/SPY recovery regime; stock above SMA50 and SMA200; at least 15% rebound from 126-day low; positive 63-day recovery momentum; avoid stocks still more than 30% below 126-day high; hold top 1-2.",
    )


def simulate_strategy(
    name: str,
    price_data: dict[str, list[dict[str, Any]]],
    dates: list[str],
    selector: Any,
    notes: str,
) -> StrategySimulation:
    equity = STARTING_EQUITY
    current_weights: dict[str, float] = {}
    previous_prices: dict[str, float] = {}
    curve: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    contributions: dict[str, float] = defaultdict(float)
    holding_weights: dict[str, list[float]] = defaultdict(list)
    rebalance_month = ""
    start_index = max(MOMENTUM_WINDOWS) + 1
    for index, date in enumerate(dates):
        if index < start_index:
            continue
        if previous_prices:
            daily_return = 0.0
            for ticker, weight in current_weights.items():
                current_price = price_on(price_data[ticker], date)
                prior = previous_prices.get(ticker, current_price)
                ret = current_price / prior - 1.0 if prior > 0 else 0.0
                daily_return += weight * ret
                contributions[ticker] += weight * ret
            equity *= 1.0 + daily_return
        month = date[:7]
        if month != rebalance_month:
            rebalance_month = month
            new_weights, reason, regime = selector(index, current_weights)
            turnover = weight_turnover(current_weights, new_weights)
            if turnover > 0 or new_weights != current_weights:
                trades.append({"strategy_name": name, "rebalance_date": date, "selected_tickers": ",".join(new_weights), "weights": format_weights(new_weights), "regime_status": regime, "reason": reason, "turnover": round(turnover, 4)})
            current_weights = new_weights
        for ticker, weight in current_weights.items():
            holding_weights[ticker].append(weight)
        curve.append({"date": date, "equity": equity, "holdings": len(current_weights), "cash": 1.0 if not current_weights else 0.0, "max_weight": max(current_weights.values()) if current_weights else 0.0})
        previous_prices = {ticker: price_on(price_data[ticker], date) for ticker in current_weights}
    return StrategySimulation(name=name, curve=curve, trades=trades, contributions=dict(contributions), holding_weights=dict(holding_weights), data_status="ok" if curve else "insufficient_market_data", notes=notes)


def simulate_equal_weight_benchmark(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        available = [ticker for ticker in STOCK_UNIVERSE if enough_history(price_data.get(ticker, []), dates[index], 2)]
        return equal_weights(available), "Equal-weight buy-and-hold of fixed stock universe.", "benchmark"

    return simulate_strategy("equal_weight_stock_universe_buy_and_hold", price_data, dates, selector, "Equal-weight buy-and-hold benchmark for the fixed current mega-cap growth stock universe.")


def simulate_buy_and_hold(name: str, ticker: str, rows: list[dict[str, Any]]) -> StrategySimulation:
    if len(rows) < 2:
        return insufficient_simulation(name, f"Missing {ticker} benchmark rows.")
    start = rows[0]["close"]
    curve = [{"date": row["date"], "equity": STARTING_EQUITY * row["close"] / start, "holdings": 1, "cash": 0.0, "max_weight": 1.0} for row in rows]
    return StrategySimulation(name=name, curve=curve, trades=[], contributions={ticker: curve[-1]["equity"] / STARTING_EQUITY - 1.0}, holding_weights={ticker: [1.0] * len(curve)}, data_status="ok", notes=f"{ticker} buy-and-hold benchmark only; not a traded strategy in the stock lab.")


def rank_growth_stocks(price_data: dict[str, list[dict[str, Any]]], dates: list[str], index: int) -> list[tuple[str, float]]:
    date = dates[index]
    scores = []
    for ticker in STOCK_UNIVERSE:
        rows = price_data.get(ticker, [])
        if not enough_history(rows, date, max(MOMENTUM_WINDOWS)):
            continue
        score = composite_momentum(rows, date)
        if score > 0:
            scores.append((ticker, score))
    return sorted(scores, key=lambda item: item[1], reverse=True)


def composite_momentum(rows: list[dict[str, Any]], date: str) -> float:
    return sum(momentum_return(rows, date, window) for window in MOMENTUM_WINDOWS) / len(MOMENTUM_WINDOWS)


def momentum_return(rows: list[dict[str, Any]], date: str, window: int) -> float:
    index = row_index(rows, date)
    if index is None or index < window:
        return 0.0
    prior = rows[index - window]["close"]
    return rows[index]["close"] / prior - 1.0 if prior > 0 else 0.0


def regime_ok(price_data: dict[str, list[dict[str, Any]]], date: str) -> bool:
    for ticker in BENCHMARK_TICKERS:
        rows = price_data.get(ticker, [])
        if above_sma(rows, date, TREND_WINDOW):
            return True
    return False


def market_recovery_ok(price_data: dict[str, list[dict[str, Any]]], date: str) -> bool:
    for ticker in BENCHMARK_TICKERS:
        rows = price_data.get(ticker, [])
        if above_sma(rows, date, 50) and above_sma(rows, date, TREND_WINDOW) and momentum_return(rows, date, 63) > 0:
            return True
    return False


def above_sma(rows: list[dict[str, Any]], date: str, window: int) -> bool:
    if not enough_history(rows, date, window):
        return False
    current_price = price_on(rows, date)
    moving_average = sma(rows, date, window)
    return current_price > 0 and moving_average > 0 and current_price > moving_average


def enough_history(rows: list[dict[str, Any]], date: str, window: int) -> bool:
    index = row_index(rows, date)
    return index is not None and index >= window


def row_index(rows: list[dict[str, Any]], date: str) -> int | None:
    for index in range(len(rows) - 1, -1, -1):
        if rows[index]["date"] <= date:
            return index
    return None


def price_on(rows: list[dict[str, Any]], date: str) -> float:
    index = row_index(rows, date)
    return float(rows[index]["close"]) if index is not None else 0.0


def sma(rows: list[dict[str, Any]], date: str, window: int) -> float:
    index = row_index(rows, date)
    if index is None or index < window - 1:
        return 0.0
    values = [row["close"] for row in rows[index - window + 1 : index + 1]]
    return sum(values) / len(values)


def rolling_high(rows: list[dict[str, Any]], date: str, window: int) -> float:
    index = row_index(rows, date)
    if index is None:
        return 0.0
    values = [row["close"] for row in rows[max(0, index - window + 1) : index + 1]]
    return max(values) if values else 0.0


def rolling_low(rows: list[dict[str, Any]], date: str, window: int) -> float:
    index = row_index(rows, date)
    if index is None:
        return 0.0
    values = [row["close"] for row in rows[max(0, index - window + 1) : index + 1]]
    return min(values) if values else 0.0


def realised_volatility(rows: list[dict[str, Any]], date: str, window: int) -> float:
    index = row_index(rows, date)
    if index is None or index < window:
        return 0.0
    returns = []
    for offset in range(index - window + 1, index + 1):
        prior = rows[offset - 1]["close"]
        returns.append(rows[offset]["close"] / prior - 1.0 if prior > 0 else 0.0)
    return sample_stdev(returns) * math.sqrt(252.0) if len(returns) > 1 else 0.0


def equal_weights(tickers: list[str]) -> dict[str, float]:
    if not tickers:
        return {}
    weight = 1.0 / len(tickers)
    return {ticker: weight for ticker in tickers}


def weight_turnover(old: dict[str, float], new: dict[str, float]) -> float:
    keys = set(old) | set(new)
    return sum(abs(old.get(key, 0.0) - new.get(key, 0.0)) for key in keys) / 2.0


def format_weights(weights: dict[str, float]) -> str:
    return ";".join(f"{ticker}:{weight:.4f}" for ticker, weight in sorted(weights.items())) or "cash"


def build_report_row(created_at: str, simulation: StrategySimulation, period: str) -> dict[str, Any]:
    metrics = metrics_for_curve(simulation.curve)
    concentration = concentration_stats(simulation)
    return {
        "created_at": created_at,
        "strategy_name": simulation.name,
        "period": period,
        "data_status": simulation.data_status,
        **metrics,
        "trade_count": len(simulation.trades),
        "rebalance_count": len(simulation.trades),
        "turnover": round(sum(float(trade.get("turnover", 0.0)) for trade in simulation.trades), 4),
        "average_holdings": concentration["average_holdings"],
        "max_single_name_concentration": concentration["max_single_name_concentration"],
        "time_in_cash_pct": concentration["time_in_cash_pct"],
        "top_contributing_tickers": top_contributors(simulation),
        "cost_sensitivity_label": "",
        "split_sensitivity_label": "",
        "concentration_warning": concentration_warning(simulation),
        "survivorship_bias_warning": "high_growth_stock_survivorship_bias_warning: fixed current mega-cap growth universe may overstate historical opportunity.",
        "single_name_event_risk_warning": "single-name earnings, product, regulatory, and valuation shocks can dominate concentrated stock outcomes.",
        "stock_specific_gap_risk_warning": "individual stock overnight gap risk is materially higher than diversified ETF risk.",
        "decision_label": "research_only_not_execution_ready" if simulation.data_status != "ok" else "",
        "notes": simulation.notes,
        **safety_flags(),
    }


def build_cost_rows(created_at: str, simulations: list[StrategySimulation]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        base = build_report_row(created_at, simulation, "cost_stress")
        turnover = float(base.get("turnover", 0.0))
        for bps in REBALANCE_COST_BPS:
            stressed_curve = stress_curve_for_cost(simulation.curve, turnover, bps)
            stressed = metrics_for_curve(stressed_curve)
            row = dict(base)
            row.update(stressed)
            row["cost_bps"] = bps
            row["cost_stress_cagr_pct"] = stressed["cagr_pct"]
            row["cost_stress_calmar_ratio"] = stressed["calmar_ratio"]
            row["cost_sensitivity_label"] = "high_growth_stock_cost_sensitive" if bps == 50 and base.get("data_status") == "ok" and float(base.get("cagr_pct", 0.0)) - stressed["cagr_pct"] > 2.0 else "cost_context_only"
            rows.append(row)
    return rows


def stress_curve_for_cost(curve: list[dict[str, Any]], turnover: float, bps: int) -> list[dict[str, Any]]:
    if not curve or bps == 0:
        return curve
    years = max(1.0 / 252.0, len(curve) / 252.0)
    annual_drag = (turnover / years) * (bps / 10000.0)
    stressed = []
    for index, row in enumerate(curve):
        drag = max(0.0, 1.0 - annual_drag * (index / max(1, len(curve) - 1)))
        stressed.append({**row, "equity": float(row["equity"]) * drag})
    return stressed


def build_split_rows(created_at: str, simulations: list[StrategySimulation]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        for name, fraction in SPLITS:
            if not simulation.curve:
                row = build_report_row(created_at, simulation, name)
            else:
                split_index = max(1, int(len(simulation.curve) * fraction))
                segment = simulation.curve[split_index:]
                row = build_report_row(created_at, StrategySimulation(simulation.name, segment, [], {}, {}, simulation.data_status, simulation.notes), name)
                row["split_start_date"] = segment[0]["date"] if segment else ""
                row["split_end_date"] = segment[-1]["date"] if segment else ""
            row["split_name"] = name
            row["split_fraction"] = fraction
            row["split_sensitivity_label"] = "high_growth_stock_split_sensitive" if simulation.data_status == "ok" and float(row.get("cagr_pct", 0.0)) < 0 else "split_context_only"
            rows.append(row)
    return rows


def build_drawdown_rows(created_at: str, simulations: list[StrategySimulation]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        row = build_report_row(created_at, simulation, "worst_drawdown_period")
        row.update(drawdown_window(simulation.curve))
        rows.append(row)
    return rows


def build_concentration_rows(created_at: str, simulations: list[StrategySimulation]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        base = build_report_row(created_at, simulation, "concentration")
        for ticker, weights in sorted(simulation.holding_weights.items()):
            row = dict(base)
            row["ticker"] = ticker
            row["average_weight"] = round(average(weights), 4) if weights else 0.0
            row["max_weight"] = round(max(weights), 4) if weights else 0.0
            row["contribution_pct"] = round(simulation.contributions.get(ticker, 0.0) * 100.0, 4)
            row["holding_days"] = len(weights)
            rows.append(row)
        if not simulation.holding_weights:
            row = dict(base)
            row.update({"ticker": "", "average_weight": 0.0, "max_weight": 0.0, "contribution_pct": 0.0, "holding_days": 0})
            rows.append(row)
    return rows


def trade_row(created_at: str, trade: dict[str, Any]) -> dict[str, Any]:
    return {"created_at": created_at, **trade, **safety_flags()}


def apply_decision_labels(report_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], concentration_rows: list[dict[str, Any]]) -> None:
    cost_sensitive = {row["strategy_name"] for row in cost_rows if row.get("cost_sensitivity_label") == "high_growth_stock_cost_sensitive"}
    split_sensitive = {row["strategy_name"] for row in split_rows if row.get("split_sensitivity_label") == "high_growth_stock_split_sensitive"}
    outlier_dependent = {row["strategy_name"] for row in concentration_rows if str(row.get("ticker")) in {"NVDA", "TSLA", "AMD"} and float(row.get("contribution_pct", 0.0) or 0.0) > 50.0}
    top3 = next((row for row in report_rows if row.get("strategy_name") == "concentrated_growth_momentum_top3" and row.get("data_status") == "ok"), {})
    for row in report_rows:
        if row["data_status"] != "ok":
            row["decision_label"] = "insufficient_market_data"
        elif row["strategy_name"] not in STRATEGIES:
            row["decision_label"] = "benchmark_context_only"
        elif float(row["max_drawdown_pct"]) < -45.0:
            row["decision_label"] = "high_growth_stock_drawdown_too_high"
        elif row["strategy_name"] in outlier_dependent:
            row["decision_label"] = "high_growth_stock_outlier_dependent"
        elif row["strategy_name"] in cost_sensitive:
            row["decision_label"] = "high_growth_stock_cost_sensitive"
        elif row["strategy_name"] in split_sensitive:
            row["decision_label"] = "high_growth_stock_split_sensitive"
        elif row["strategy_name"] in NEW_CODEX_STRATEGIES and beats_top3_without_much_worse_drawdown(row, top3):
            row["decision_label"] = "high_growth_stock_research_lead"
        elif row["strategy_name"] in NEW_CODEX_STRATEGIES and float(row["cagr_pct"]) > QQQ_BASELINE["cagr_pct"] and float(row["sharpe_ratio"]) >= QQQ_BASELINE["sharpe_ratio"] * 0.7:
            row["decision_label"] = "high_growth_stock_ambitious_alternative"
        elif float(row["cagr_pct"]) > QQQ_BASELINE["cagr_pct"] + 3.0 and float(row["sharpe_ratio"]) >= QQQ_BASELINE["sharpe_ratio"] * 0.8 and float(row["calmar_ratio"]) >= QQQ_BASELINE["calmar_ratio"] * 0.7:
            row["decision_label"] = "high_growth_stock_promising_but_concentrated"
        else:
            row["decision_label"] = "qqq_trend_gate_remains_cleaner_lead"
        row["cost_sensitivity_label"] = "high_growth_stock_cost_sensitive" if row["strategy_name"] in cost_sensitive else "cost_context_only"
        row["split_sensitivity_label"] = "high_growth_stock_split_sensitive" if row["strategy_name"] in split_sensitive else "split_context_only"


def beats_top3_without_much_worse_drawdown(row: dict[str, Any], top3: dict[str, Any]) -> bool:
    if not top3:
        return False
    return (
        float(row.get("cagr_pct", 0.0)) > float(top3.get("cagr_pct", 0.0))
        and float(row.get("sharpe_ratio", 0.0)) > float(top3.get("sharpe_ratio", 0.0))
        and float(row.get("calmar_ratio", 0.0)) > float(top3.get("calmar_ratio", 0.0))
        and float(row.get("max_drawdown_pct", 0.0)) >= float(top3.get("max_drawdown_pct", 0.0)) - 5.0
    )


def build_summary_rows(
    created_at: str,
    report_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
    concentration_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
) -> list[dict[str, Any]]:
    candidates = [row for row in report_rows if row["strategy_name"] in STRATEGIES and row.get("data_status") == "ok"]
    best = max(candidates, key=lambda row: (float(row.get("cagr_pct", 0.0)), float(row.get("calmar_ratio", 0.0))), default={})
    new_candidates = [row for row in candidates if row["strategy_name"] in NEW_CODEX_STRATEGIES]
    best_new = max(new_candidates, key=lambda row: (float(row.get("cagr_pct", 0.0)), float(row.get("calmar_ratio", 0.0))), default={})
    top3 = next((row for row in report_rows if row.get("strategy_name") == "concentrated_growth_momentum_top3" and row.get("data_status") == "ok"), {})
    worst = min(candidates, key=lambda row: float(row.get("max_drawdown_pct", 0.0)), default={})
    largest_concentration = max(candidates, key=lambda row: float(row.get("max_single_name_concentration", 0.0)), default={})
    cost_flags = sorted({row["strategy_name"] for row in cost_rows if row.get("cost_sensitivity_label") == "high_growth_stock_cost_sensitive"})
    split_flags = sorted({row["strategy_name"] for row in split_rows if row.get("split_sensitivity_label") == "high_growth_stock_split_sensitive"})
    conclusion = final_conclusion(best)
    entries = [
        ("best_high_growth_stock_candidate", best.get("strategy_name", "none"), format_candidate(best)),
        ("best_new_codex_designed_candidate", best_new.get("strategy_name", "none"), format_candidate(best_new)),
        ("comparison_vs_qqq_100_trend_gate", comparison_vs_qqq(best), "QQQ trend gate remains the cleaner lead unless concentration/drawdown review accepts the extra risk."),
        ("comparison_vs_concentrated_growth_momentum_top3", comparison_between(best_new, top3, "concentrated_growth_momentum_top3"), "New Codex-designed candidates must beat top3 on CAGR, Sharpe, and Calmar without much worse drawdown before becoming the high-growth stock research lead."),
        ("biggest_concentration_outlier_warning", concentration_warning_text(largest_concentration, concentration_rows), "Survivorship and single-name event risk remain explicit."),
        ("worst_drawdown_warning", f"{worst.get('strategy_name', 'none')} max_drawdown_pct={worst.get('max_drawdown_pct', '')}", "Drawdown is the main high-growth stock lab risk."),
        ("cost_split_sensitivity_warning", f"cost_sensitive={','.join(cost_flags) or 'none'}; split_sensitive={','.join(split_flags) or 'none'}", "Cost and split warnings are research labels only."),
        ("final_research_conclusion", conclusion, "No execution approval."),
        ("data_issues", f"ticker_errors={len(data_errors)}", "; ".join(f"{k}={v}" for k, v in sorted(data_errors.items()))[:500]),
    ]
    return [summary_row(created_at, name, value, details) for name, value, details in entries]


def final_conclusion(best: dict[str, Any]) -> str:
    if not best:
        return "insufficient_market_data"
    if best.get("decision_label") == "high_growth_stock_research_lead":
        return "high_growth_stock_research_lead; qqq_trend_gate_remains_cleaner_lead_for_drawdown_and_diversification_review"
    if best.get("decision_label") == "high_growth_stock_ambitious_alternative":
        return "high_growth_stock_ambitious_alternative; qqq_trend_gate_remains_cleaner_lead"
    if best.get("decision_label") == "high_growth_stock_promising_but_concentrated":
        return "high_growth_stock_candidate_is_ambitious_high_risk_alternative; qqq_trend_gate_remains_cleaner_lead"
    return f"{best.get('decision_label', 'research_only_not_execution_ready')}; qqq_trend_gate_remains_cleaner_lead"


def metrics_for_curve(curve: list[dict[str, Any]]) -> dict[str, float]:
    if len(curve) < 2:
        return {"cagr_pct": 0.0, "annualised_volatility_pct": 0.0, "sharpe_ratio": 0.0, "max_drawdown_pct": 0.0, "calmar_ratio": 0.0, "total_return_pct": 0.0}
    values = [float(row["equity"]) for row in curve]
    returns = [values[index] / values[index - 1] - 1.0 for index in range(1, len(values)) if values[index - 1] > 0]
    years = max(1.0 / 252.0, (len(values) - 1) / 252.0)
    cagr = ((values[-1] / values[0]) ** (1.0 / years) - 1.0) * 100.0 if values[0] > 0 else 0.0
    vol = sample_stdev(returns) * math.sqrt(252.0) * 100.0 if returns else 0.0
    sharpe = (average(returns) / sample_stdev(returns) * math.sqrt(252.0)) if len(returns) > 1 and sample_stdev(returns) > 0 else 0.0
    max_dd = max_drawdown_pct(values)
    calmar = cagr / abs(max_dd) if max_dd < 0 else 0.0
    total = (values[-1] / values[0] - 1.0) * 100.0 if values[0] > 0 else 0.0
    return {"cagr_pct": round(cagr, 4), "annualised_volatility_pct": round(vol, 4), "sharpe_ratio": round(sharpe, 4), "max_drawdown_pct": round(max_dd, 4), "calmar_ratio": round(calmar, 4), "total_return_pct": round(total, 4)}


def max_drawdown_pct(values: list[float]) -> float:
    peak = values[0] if values else 0.0
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value / peak - 1.0) * 100.0)
    return worst


def drawdown_window(curve: list[dict[str, Any]]) -> dict[str, Any]:
    if not curve:
        return {"drawdown_start": "", "drawdown_trough": "", "drawdown_recovery": "", "drawdown_recovered": False, "drawdown_days": 0}
    peak_index = trough_index = start_index = 0
    peak_value = float(curve[0]["equity"])
    worst_dd = 0.0
    for index, row in enumerate(curve):
        value = float(row["equity"])
        if value > peak_value:
            peak_value = value
            peak_index = index
        drawdown = value / peak_value - 1.0 if peak_value > 0 else 0.0
        if drawdown < worst_dd:
            worst_dd = drawdown
            start_index = peak_index
            trough_index = index
    recovery_index = None
    peak_at_start = float(curve[start_index]["equity"])
    for index in range(trough_index + 1, len(curve)):
        if float(curve[index]["equity"]) >= peak_at_start:
            recovery_index = index
            break
    return {"drawdown_start": curve[start_index]["date"], "drawdown_trough": curve[trough_index]["date"], "drawdown_recovery": curve[recovery_index]["date"] if recovery_index is not None else "", "drawdown_recovered": recovery_index is not None, "drawdown_days": max(0, (recovery_index or trough_index) - start_index)}


def concentration_stats(simulation: StrategySimulation) -> dict[str, float]:
    if not simulation.curve:
        return {"average_holdings": 0.0, "max_single_name_concentration": 0.0, "time_in_cash_pct": 100.0}
    return {
        "average_holdings": round(average([float(row.get("holdings", 0.0)) for row in simulation.curve]), 4),
        "max_single_name_concentration": round(max(float(row.get("max_weight", 0.0)) for row in simulation.curve), 4),
        "time_in_cash_pct": round(average([float(row.get("cash", 0.0)) for row in simulation.curve]) * 100.0, 4),
    }


def concentration_warning(simulation: StrategySimulation) -> str:
    stats = concentration_stats(simulation)
    if stats["max_single_name_concentration"] >= 0.99:
        return "high_growth_stock_single_name_concentration_warning"
    if stats["max_single_name_concentration"] >= 0.5:
        return "high_growth_stock_concentration_warning"
    return "concentration_context_only"


def top_contributors(simulation: StrategySimulation) -> str:
    if not simulation.contributions:
        return ""
    items = sorted(simulation.contributions.items(), key=lambda item: item[1], reverse=True)[:3]
    return ";".join(f"{ticker}:{value * 100.0:.2f}%" for ticker, value in items)


def concentration_warning_text(row: dict[str, Any], concentration_rows: list[dict[str, Any]]) -> str:
    strategy = row.get("strategy_name", "none")
    ticker_rows = [item for item in concentration_rows if item.get("strategy_name") == strategy]
    largest = max(ticker_rows, key=lambda item: float(item.get("contribution_pct", 0.0) or 0.0), default={})
    return f"{strategy}: max_single_name_concentration={row.get('max_single_name_concentration', '')}; largest_contributor={largest.get('ticker', '')}; survivorship_bias_warning=true; single_name_event_risk_warning=true"


def comparison_vs_qqq(row: dict[str, Any]) -> str:
    if not row:
        return "no high-growth stock candidate available"
    return (
        f"{row.get('strategy_name')}: CAGR_delta={round(float(row.get('cagr_pct', 0.0)) - QQQ_BASELINE['cagr_pct'], 4)}; "
        f"Sharpe_delta={round(float(row.get('sharpe_ratio', 0.0)) - QQQ_BASELINE['sharpe_ratio'], 4)}; "
        f"Calmar_delta={round(float(row.get('calmar_ratio', 0.0)) - QQQ_BASELINE['calmar_ratio'], 4)}; "
        f"MaxDD_delta={round(float(row.get('max_drawdown_pct', 0.0)) - QQQ_BASELINE['max_drawdown_pct'], 4)}"
    )


def comparison_between(row: dict[str, Any], benchmark: dict[str, Any], benchmark_name: str) -> str:
    if not row:
        return "no new Codex-designed candidate available"
    if not benchmark:
        return f"{row.get('strategy_name')}: benchmark {benchmark_name} unavailable"
    return (
        f"{row.get('strategy_name')}: CAGR_delta={round(float(row.get('cagr_pct', 0.0)) - float(benchmark.get('cagr_pct', 0.0)), 4)}; "
        f"Sharpe_delta={round(float(row.get('sharpe_ratio', 0.0)) - float(benchmark.get('sharpe_ratio', 0.0)), 4)}; "
        f"Calmar_delta={round(float(row.get('calmar_ratio', 0.0)) - float(benchmark.get('calmar_ratio', 0.0)), 4)}; "
        f"MaxDD_delta={round(float(row.get('max_drawdown_pct', 0.0)) - float(benchmark.get('max_drawdown_pct', 0.0)), 4)}"
    )


def format_candidate(row: dict[str, Any]) -> str:
    if not row:
        return "unavailable"
    return f"CAGR={row.get('cagr_pct')}%; Sharpe={row.get('sharpe_ratio')}; MaxDD={row.get('max_drawdown_pct')}%; Calmar={row.get('calmar_ratio')}; decision={row.get('decision_label')}"


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sample_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = average(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def summary_row(created_at: str, name: str, value: str, details: str) -> dict[str, Any]:
    return {"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def safety_flags() -> dict[str, bool]:
    return {"research_only": True, "preview_only": False, "execution_approved": False, "paper_execution_approved": False, "leverage_execution_approved": False, "margin_approved": False, "short_execution_approved": False, "scheduling_approved": False, "alpaca_called": False, "orders_created": False}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock lab complete. Research only; execution_approved=False.",
        f"Best high-growth stock candidate: {summary_value(summary_rows, 'best_high_growth_stock_candidate')}",
        f"Best new Codex-designed candidate: {summary_value(summary_rows, 'best_new_codex_designed_candidate')}",
        f"Comparison versus qqq_100_trend_gate: {summary_value(summary_rows, 'comparison_vs_qqq_100_trend_gate')}",
        f"Comparison versus concentrated_growth_momentum_top3: {summary_value(summary_rows, 'comparison_vs_concentrated_growth_momentum_top3')}",
        f"Biggest concentration/outlier warning: {summary_value(summary_rows, 'biggest_concentration_outlier_warning')}",
        f"Worst drawdown warning: {summary_value(summary_rows, 'worst_drawdown_warning')}",
        f"Cost/split sensitivity warning: {summary_value(summary_rows, 'cost_split_sensitivity_warning')}",
        f"Final research conclusion: {summary_value(summary_rows, 'final_research_conclusion')}",
        f"Saved report to {output_paths['report']}",
        f"Saved summary to {output_paths['summary']}",
        f"Saved trades/costs/splits/drawdowns/concentration: {output_paths['trades']}; {output_paths['costs']}; {output_paths['splits']}; {output_paths['drawdowns']}; {output_paths['concentration']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: research-only; no Alpaca commands, order instructions, paper execution, live trading, or scheduling approval.",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
