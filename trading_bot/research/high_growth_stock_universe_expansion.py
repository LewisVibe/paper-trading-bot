"""Research-only high-growth stock universe expansion report.

This module compares fixed current-constituent stock universes to test whether
concentrated growth momentum depends on a narrow mega-cap winner set. It does
not call Alpaca, load config, read positions, create orders, write SQLite,
send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import high_growth_stock_lab as lab


OUTPUT_FILES = {
    "report": Path("data/high_growth_stock_universe_expansion_report.csv"),
    "summary": Path("data/high_growth_stock_universe_expansion_summary.csv"),
    "trades": Path("data/high_growth_stock_universe_expansion_trades.csv"),
    "costs": Path("data/high_growth_stock_universe_expansion_costs.csv"),
    "splits": Path("data/high_growth_stock_universe_expansion_splits.csv"),
    "drawdowns": Path("data/high_growth_stock_universe_expansion_drawdowns.csv"),
    "concentration": Path("data/high_growth_stock_universe_expansion_concentration.csv"),
}

UNIVERSES = {
    "mega_cap_growth_10": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "AMD", "TSLA", "NFLX"],
    "expanded_growth_30": [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "META",
        "GOOGL",
        "AVGO",
        "AMD",
        "TSLA",
        "NFLX",
        "ORCL",
        "CRM",
        "ADBE",
        "NOW",
        "INTU",
        "PANW",
        "CRWD",
        "SHOP",
        "UBER",
        "BKNG",
        "COST",
        "LLY",
        "NVO",
        "ASML",
        "TSM",
        "MU",
        "QCOM",
        "TXN",
        "ISRG",
        "PLTR",
    ],
    "broad_liquid_growth_50": [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "META",
        "GOOGL",
        "AVGO",
        "AMD",
        "TSLA",
        "NFLX",
        "ORCL",
        "CRM",
        "ADBE",
        "NOW",
        "INTU",
        "PANW",
        "CRWD",
        "SHOP",
        "UBER",
        "BKNG",
        "COST",
        "LLY",
        "NVO",
        "ASML",
        "TSM",
        "MU",
        "QCOM",
        "TXN",
        "ISRG",
        "PLTR",
        "JPM",
        "V",
        "MA",
        "HD",
        "UNH",
        "GE",
        "CAT",
        "BA",
        "LIN",
        "AMAT",
        "LRCX",
        "KLAC",
        "SNOW",
        "DDOG",
        "NET",
        "MDB",
        "ABNB",
        "MELI",
        "SE",
        "DASH",
    ],
}

STRATEGY_NAMES = [
    "concentrated_growth_momentum_top1",
    "concentrated_growth_momentum_top2",
    "concentrated_growth_momentum_top3",
    "codex_high_conviction_growth_persistence",
    "codex_growth_drawdown_reentry",
    "codex_high_growth_breakout_acceleration",
    "codex_high_growth_crash_rebound_leader",
]

BENCHMARK_STRATEGIES = ["equal_weight_universe_buy_and_hold", "qqq_buy_and_hold_benchmark", "spy_buy_and_hold_benchmark", "cash_benchmark"]
ORIGINAL_TOP3 = {"cagr_pct": 39.1498, "sharpe_ratio": 1.1042, "calmar_ratio": 0.8828, "max_drawdown_pct": -44.3476}
QQQ_TREND_GATE = {"cagr_pct": 16.8429, "sharpe_ratio": 1.0027, "calmar_ratio": 0.718, "max_drawdown_pct": -23.4576}
SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "leverage_execution_approved": False,
    "margin_approved": False,
    "short_execution_approved": False,
    "scheduling_approved": False,
    "alpaca_called": False,
    "orders_created": False,
}

REPORT_COLUMNS = [
    "created_at",
    "universe_name",
    "universe_size",
    "strategy_name",
    "period",
    "data_status",
    "usable_ticker_count",
    "missing_ticker_count",
    "missing_tickers",
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
    "universe_sensitivity_label",
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
    "universe_name",
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
class UniverseExpansionResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_universe_expansion_report(root_dir: Path | str = ".") -> UniverseExpansionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    all_tickers = sorted({ticker for tickers in UNIVERSES.values() for ticker in tickers} | set(lab.BENCHMARK_TICKERS))
    price_data, data_errors = lab.download_daily_price_data(all_tickers, root / "data" / "yfinance_cache")
    report_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []
    drawdown_rows: list[dict[str, Any]] = []
    concentration_rows: list[dict[str, Any]] = []

    for universe_name, tickers in UNIVERSES.items():
        simulations = build_universe_simulations(universe_name, tickers, price_data, data_errors)
        universe_report = [build_report_row(created_at, universe_name, tickers, simulation, "full_period", data_errors) for simulation in simulations]
        report_rows.extend(universe_report)
        cost_rows.extend(build_cost_rows(created_at, universe_name, tickers, simulations, data_errors))
        split_rows.extend(build_split_rows(created_at, universe_name, tickers, simulations, data_errors))
        drawdown_rows.extend(build_drawdown_rows(created_at, universe_name, tickers, simulations, data_errors))
        concentration_rows.extend(build_concentration_rows(created_at, universe_name, tickers, simulations, data_errors))
        for simulation in simulations:
            for trade in simulation.trades:
                trade_rows.append({"created_at": created_at, "universe_name": universe_name, **trade, **safety_flags()})

    apply_decision_labels(report_rows, cost_rows, split_rows, concentration_rows)
    summary_rows = build_summary_rows(created_at, report_rows, cost_rows, split_rows, concentration_rows, data_errors)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["trades"], TRADE_COLUMNS, trade_rows)
    write_rows(output_paths["costs"], COST_COLUMNS, cost_rows)
    write_rows(output_paths["splits"], SPLIT_COLUMNS, split_rows)
    write_rows(output_paths["drawdowns"], DRAWDOWN_COLUMNS, drawdown_rows)
    write_rows(output_paths["concentration"], CONCENTRATION_COLUMNS, concentration_rows)
    return UniverseExpansionResult(output_paths, report_rows, summary_rows, build_summary_lines(summary_rows, output_paths))


def show_high_growth_stock_universe_expansion_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    report_path = root / OUTPUT_FILES["report"]
    if not summary_path.exists() or not report_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-universe-expansion-report` first."]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock universe expansion saved display. Research only; execution_approved=False.",
        f"Best universe/strategy combination: {summary_value(summary_rows, 'best_universe_strategy_combination')}",
        f"Comparison versus original top3: {summary_value(summary_rows, 'comparison_vs_original_top3')}",
        f"Comparison versus qqq_100_trend_gate: {summary_value(summary_rows, 'comparison_vs_qqq_100_trend_gate')}",
        f"Universe breadth sensitivity: {summary_value(summary_rows, 'universe_breadth_sensitivity')}",
        f"Biggest concentration/outlier warning: {summary_value(summary_rows, 'biggest_concentration_outlier_warning')}",
        f"Worst drawdown warning: {summary_value(summary_rows, 'worst_drawdown_warning')}",
        f"Cost/split sensitivity warning: {summary_value(summary_rows, 'cost_split_sensitivity_warning')}",
        f"Final research conclusion: {summary_value(summary_rows, 'final_research_conclusion')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no Alpaca commands, order instructions, paper execution, or scheduling approval.",
    ]


def build_universe_simulations(universe_name: str, tickers: list[str], price_data: dict[str, list[dict[str, Any]]], data_errors: dict[str, str]) -> list[lab.StrategySimulation]:
    stock_data = {ticker: rows for ticker, rows in price_data.items() if ticker in tickers}
    if len(stock_data) < 3 or not any(ticker in price_data for ticker in lab.BENCHMARK_TICKERS):
        reason = f"Insufficient market data; universe={universe_name}; stock_rows={len(stock_data)}; errors={len(data_errors)}"
        return [lab.insufficient_simulation(name, reason) for name in STRATEGY_NAMES + BENCHMARK_STRATEGIES]
    dates = lab.common_dates(stock_data)
    return [
        simulate_momentum_strategy(universe_name, tickers, "concentrated_growth_momentum_top1", 1, price_data, dates),
        simulate_momentum_strategy(universe_name, tickers, "concentrated_growth_momentum_top2", 2, price_data, dates),
        simulate_momentum_strategy(universe_name, tickers, "concentrated_growth_momentum_top3", 3, price_data, dates),
        simulate_high_conviction_growth_persistence(universe_name, tickers, price_data, dates),
        simulate_growth_drawdown_reentry(universe_name, tickers, price_data, dates),
        simulate_high_growth_breakout_acceleration(universe_name, tickers, price_data, dates),
        simulate_high_growth_crash_rebound_leader(universe_name, tickers, price_data, dates),
        simulate_equal_weight_benchmark(universe_name, tickers, price_data, dates),
        simulate_buy_and_hold_if_available("qqq_buy_and_hold_benchmark", "QQQ", price_data),
        simulate_buy_and_hold_if_available("spy_buy_and_hold_benchmark", "SPY", price_data),
        simulate_cash_benchmark(dates),
    ]


def simulate_momentum_strategy(universe_name: str, tickers: list[str], name: str, top_n: int, price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        date = dates[index]
        if not lab.regime_ok(price_data, date):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        ranked = rank_growth_stocks(tickers, price_data, dates, index)
        selected = [ticker for ticker, _score in ranked if lab.above_sma(price_data[ticker], date, lab.TREND_WINDOW)][:top_n]
        if not selected:
            return {}, "No stock passes own SMA200 and momentum filter; holding cash.", "cash_no_stock_passes"
        return lab.equal_weights(selected), f"{universe_name}: monthly top {top_n} composite momentum stock(s) above SMA200 with QQQ/SPY regime gate.", "risk_on"

    return lab.simulate_strategy(name, price_data, dates, selector, "Universe expansion: fixed monthly 63/126/252-day momentum, own SMA200, QQQ/SPY SMA200 regime gate, no ETFs as traded holdings.")


def simulate_high_conviction_growth_persistence(universe_name: str, tickers: list[str], price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        date = dates[index]
        if not lab.regime_ok(price_data, date):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        scores = []
        for ticker in tickers:
            rows = price_data.get(ticker, [])
            if not lab.enough_history(rows, date, 252):
                continue
            close = lab.price_on(rows, date)
            high_252 = lab.rolling_high(rows, date, 252)
            proximity = close / high_252 if high_252 > 0 else 0.0
            vol = lab.realised_volatility(rows, date, lab.VOL_WINDOW)
            momentum = lab.composite_momentum(rows, date)
            if lab.above_sma(rows, date, lab.TREND_WINDOW) and proximity >= 0.85 and momentum > 0:
                scores.append((ticker, momentum + proximity - min(vol, 1.5) * 0.25))
        selected = [ticker for ticker, _score in sorted(scores, key=lambda item: item[1], reverse=True)[:2]]
        if not selected:
            return {}, "No persistent winner near highs passes fixed filters; holding cash.", "cash_no_persistence"
        return lab.equal_weights(selected), f"{universe_name}: high-conviction persistence top 1-2 stock selection.", "risk_on_persistent_winners"

    return lab.simulate_strategy("codex_high_conviction_growth_persistence", price_data, dates, selector, "Universe expansion persistence rules: own SMA200, near 252-day highs, positive momentum, volatility penalty, no leverage.")


def simulate_growth_drawdown_reentry(universe_name: str, tickers: list[str], price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        date = dates[index]
        if not lab.regime_ok(price_data, date):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        candidates = []
        for ticker, score in rank_growth_stocks(tickers, price_data, dates, index):
            rows = price_data[ticker]
            high_126 = lab.rolling_high(rows, date, 126)
            close = lab.price_on(rows, date)
            drawdown_from_high = close / high_126 - 1.0 if high_126 > 0 else -1.0
            if drawdown_from_high > -0.25 and lab.above_sma(rows, date, 50) and lab.above_sma(rows, date, lab.TREND_WINDOW):
                candidates.append((ticker, score))
        selected = [ticker for ticker, _score in candidates[:2]]
        if not selected:
            return {}, "Selected stocks lack drawdown/re-entry confirmation; holding cash.", "cash_drawdown_pause"
        return lab.equal_weights(selected), f"{universe_name}: drawdown/re-entry top 1-2 stock selection.", "risk_on_reentry_confirmed"

    return lab.simulate_strategy("codex_growth_drawdown_reentry", price_data, dates, selector, "Universe expansion re-entry rules: avoid >25% drawdown from 126-day high until SMA50/SMA200 recovery.")


def simulate_high_growth_breakout_acceleration(universe_name: str, tickers: list[str], price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        date = dates[index]
        if not lab.regime_ok(price_data, date):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        scores = []
        for ticker in tickers:
            rows = price_data.get(ticker, [])
            if not lab.enough_history(rows, date, 252):
                continue
            close = lab.price_on(rows, date)
            high_252 = lab.rolling_high(rows, date, 252)
            proximity = close / high_252 if high_252 > 0 else 0.0
            acceleration = lab.momentum_return(rows, date, 63) - lab.momentum_return(rows, date, 126)
            momentum = lab.composite_momentum(rows, date)
            if lab.above_sma(rows, date, 50) and lab.above_sma(rows, date, lab.TREND_WINDOW) and proximity >= 0.95 and momentum > 0 and acceleration > -0.05:
                scores.append((ticker, momentum + acceleration + proximity))
        selected = [ticker for ticker, _score in sorted(scores, key=lambda item: item[1], reverse=True)[:2]]
        if not selected:
            return {}, "No stock is close enough to a 52-week high with positive momentum acceleration; holding cash.", "cash_no_breakout"
        return lab.equal_weights(selected), f"{universe_name}: breakout acceleration top 1-2 stock selection.", "risk_on_breakout_acceleration"

    return lab.simulate_strategy("codex_high_growth_breakout_acceleration", price_data, dates, selector, "Universe expansion breakout rules: near 52-week highs, SMA50/SMA200, positive momentum acceleration.")


def simulate_high_growth_crash_rebound_leader(universe_name: str, tickers: list[str], price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        date = dates[index]
        if not lab.market_recovery_ok(price_data, date):
            return {}, "QQQ/SPY recovery regime is not confirmed; holding cash.", "risk_off_no_recovery"
        scores = []
        for ticker in tickers:
            rows = price_data.get(ticker, [])
            if not lab.enough_history(rows, date, 252):
                continue
            close = lab.price_on(rows, date)
            low_126 = lab.rolling_low(rows, date, 126)
            high_126 = lab.rolling_high(rows, date, 126)
            rebound_from_low = close / low_126 - 1.0 if low_126 > 0 else 0.0
            below_high = close / high_126 - 1.0 if high_126 > 0 else -1.0
            recovery_momentum = lab.momentum_return(rows, date, 63)
            if lab.above_sma(rows, date, 50) and lab.above_sma(rows, date, lab.TREND_WINDOW) and rebound_from_low >= 0.15 and recovery_momentum > 0.08 and below_high > -0.30:
                scores.append((ticker, recovery_momentum + rebound_from_low + lab.composite_momentum(rows, date) * 0.5))
        selected = [ticker for ticker, _score in sorted(scores, key=lambda item: item[1], reverse=True)[:2]]
        if not selected:
            return {}, "No stock has fixed rebound leadership confirmation; holding cash.", "cash_no_rebound_leader"
        return lab.equal_weights(selected), f"{universe_name}: crash-rebound leader top 1-2 stock selection.", "risk_on_rebound_leader"

    return lab.simulate_strategy("codex_high_growth_crash_rebound_leader", price_data, dates, selector, "Universe expansion rebound rules: QQQ/SPY recovery, rebound from 126-day low, SMA50/SMA200 recovery.")


def simulate_equal_weight_benchmark(universe_name: str, tickers: list[str], price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def selector(index: int, current_weights: dict[str, float]) -> tuple[dict[str, float], str, str]:
        available = [ticker for ticker in tickers if lab.enough_history(price_data.get(ticker, []), dates[index], 2)]
        return lab.equal_weights(available), f"{universe_name}: equal-weight buy-and-hold of fixed stock universe.", "benchmark"

    return lab.simulate_strategy("equal_weight_universe_buy_and_hold", price_data, dates, selector, "Equal-weight stock-universe buy-and-hold benchmark; not execution approval.")


def simulate_buy_and_hold_if_available(name: str, ticker: str, price_data: dict[str, list[dict[str, Any]]]) -> lab.StrategySimulation:
    if ticker not in price_data:
        return lab.insufficient_simulation(name, f"Missing {ticker} benchmark rows.")
    return lab.simulate_buy_and_hold(name, ticker, price_data[ticker])


def simulate_cash_benchmark(dates: list[str]) -> lab.StrategySimulation:
    curve = [{"date": date, "equity": lab.STARTING_EQUITY, "holdings": 0, "cash": 1.0, "max_weight": 0.0} for date in dates]
    return lab.StrategySimulation("cash_benchmark", curve, [], {}, {}, "ok" if curve else "insufficient_market_data", "Cash benchmark for context only.")


def rank_growth_stocks(tickers: list[str], price_data: dict[str, list[dict[str, Any]]], dates: list[str], index: int) -> list[tuple[str, float]]:
    date = dates[index]
    scores = []
    for ticker in tickers:
        rows = price_data.get(ticker, [])
        if not lab.enough_history(rows, date, max(lab.MOMENTUM_WINDOWS)):
            continue
        score = lab.composite_momentum(rows, date)
        if score > 0:
            scores.append((ticker, score))
    return sorted(scores, key=lambda item: item[1], reverse=True)


def build_report_row(created_at: str, universe_name: str, tickers: list[str], simulation: lab.StrategySimulation, period: str, data_errors: dict[str, str]) -> dict[str, Any]:
    row = lab.build_report_row(created_at, simulation, period)
    missing = [ticker for ticker in tickers if ticker not in data_errors and ticker not in []]
    missing_tickers = [ticker for ticker in tickers if ticker in data_errors]
    usable = max(0, len(tickers) - len(missing_tickers))
    row.update(
        {
            "universe_name": universe_name,
            "universe_size": len(tickers),
            "usable_ticker_count": usable,
            "missing_ticker_count": len(missing_tickers),
            "missing_tickers": ",".join(missing_tickers),
            "survivorship_bias_warning": "universe_expansion_survivorship_bias_warning: fixed current-constituent stock universes still suffer survivorship bias; broader breadth only tests sensitivity.",
            "universe_sensitivity_label": "",
            **safety_flags(),
        }
    )
    del missing
    return row


def build_cost_rows(created_at: str, universe_name: str, tickers: list[str], simulations: list[lab.StrategySimulation], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        base = build_report_row(created_at, universe_name, tickers, simulation, "cost_stress", data_errors)
        turnover = float(base.get("turnover", 0.0))
        for bps in lab.REBALANCE_COST_BPS:
            stressed = lab.metrics_for_curve(lab.stress_curve_for_cost(simulation.curve, turnover, bps))
            row = dict(base)
            row.update(stressed)
            row["cost_bps"] = bps
            row["cost_stress_cagr_pct"] = stressed["cagr_pct"]
            row["cost_stress_calmar_ratio"] = stressed["calmar_ratio"]
            row["cost_sensitivity_label"] = "universe_expansion_cost_sensitive" if bps == 50 and base.get("data_status") == "ok" and float(base.get("cagr_pct", 0.0)) - stressed["cagr_pct"] > 2.0 else "cost_context_only"
            rows.append(row)
    return rows


def build_split_rows(created_at: str, universe_name: str, tickers: list[str], simulations: list[lab.StrategySimulation], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        for name, fraction in lab.SPLITS:
            if not simulation.curve:
                row = build_report_row(created_at, universe_name, tickers, simulation, name, data_errors)
            else:
                split_index = max(1, int(len(simulation.curve) * fraction))
                segment = simulation.curve[split_index:]
                row = build_report_row(created_at, universe_name, tickers, lab.StrategySimulation(simulation.name, segment, [], {}, {}, simulation.data_status, simulation.notes), name, data_errors)
                row["split_start_date"] = segment[0]["date"] if segment else ""
                row["split_end_date"] = segment[-1]["date"] if segment else ""
            row["split_name"] = name
            row["split_fraction"] = fraction
            row["split_sensitivity_label"] = "universe_expansion_split_sensitive" if simulation.data_status == "ok" and float(row.get("cagr_pct", 0.0)) < 0 else "split_context_only"
            rows.append(row)
    return rows


def build_drawdown_rows(created_at: str, universe_name: str, tickers: list[str], simulations: list[lab.StrategySimulation], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        row = build_report_row(created_at, universe_name, tickers, simulation, "worst_drawdown_period", data_errors)
        row.update(lab.drawdown_window(simulation.curve))
        rows.append(row)
    return rows


def build_concentration_rows(created_at: str, universe_name: str, tickers: list[str], simulations: list[lab.StrategySimulation], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        base = build_report_row(created_at, universe_name, tickers, simulation, "concentration", data_errors)
        for ticker, weights in sorted(simulation.holding_weights.items()):
            row = dict(base)
            row["ticker"] = ticker
            row["average_weight"] = round(lab.average(weights), 4) if weights else 0.0
            row["max_weight"] = round(max(weights), 4) if weights else 0.0
            row["contribution_pct"] = round(simulation.contributions.get(ticker, 0.0) * 100.0, 4)
            row["holding_days"] = len(weights)
            rows.append(row)
        if not simulation.holding_weights:
            row = dict(base)
            row.update({"ticker": "", "average_weight": 0.0, "max_weight": 0.0, "contribution_pct": 0.0, "holding_days": 0})
            rows.append(row)
    return rows


def apply_decision_labels(report_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], concentration_rows: list[dict[str, Any]]) -> None:
    cost_sensitive = {(row["universe_name"], row["strategy_name"]) for row in cost_rows if row.get("cost_sensitivity_label") == "universe_expansion_cost_sensitive"}
    split_sensitive = {(row["universe_name"], row["strategy_name"]) for row in split_rows if row.get("split_sensitivity_label") == "universe_expansion_split_sensitive"}
    outlier_dependent = {
        (row["universe_name"], row["strategy_name"])
        for row in concentration_rows
        if str(row.get("ticker")) in {"NVDA", "TSLA", "AMD"} and float(row.get("contribution_pct", 0.0) or 0.0) > 50.0
    }
    breadth = top3_by_universe(report_rows)
    mega = breadth.get("mega_cap_growth_10", {})
    for row in report_rows:
        key = (row["universe_name"], row["strategy_name"])
        if row["data_status"] != "ok":
            row["decision_label"] = "insufficient_market_data"
        elif row["strategy_name"] not in STRATEGY_NAMES:
            row["decision_label"] = "benchmark_context_only"
        elif float(row["max_drawdown_pct"]) < -55.0:
            row["decision_label"] = "universe_expansion_drawdown_too_high"
        elif key in outlier_dependent:
            row["decision_label"] = "universe_expansion_outlier_dependent"
        elif key in cost_sensitive:
            row["decision_label"] = "universe_expansion_cost_sensitive"
        elif key in split_sensitive:
            row["decision_label"] = "universe_expansion_split_sensitive"
        elif row["strategy_name"] == "concentrated_growth_momentum_top3" and row["universe_name"] != "mega_cap_growth_10" and mega and float(row.get("cagr_pct", 0.0)) < float(mega.get("cagr_pct", 0.0)) - 5.0:
            row["decision_label"] = "universe_expansion_decays_with_breadth"
        elif float(row.get("cagr_pct", 0.0)) > QQQ_TREND_GATE["cagr_pct"] and float(row.get("max_drawdown_pct", 0.0)) < QQQ_TREND_GATE["max_drawdown_pct"] - 10.0:
            row["decision_label"] = "universe_expansion_high_growth_promising_but_concentrated"
        elif float(row.get("cagr_pct", 0.0)) > QQQ_TREND_GATE["cagr_pct"] and float(row.get("calmar_ratio", 0.0)) >= QQQ_TREND_GATE["calmar_ratio"]:
            row["decision_label"] = "universe_expansion_confirms_high_growth_edge"
        else:
            row["decision_label"] = "qqq_trend_gate_remains_cleaner_lead"
        row["cost_sensitivity_label"] = "universe_expansion_cost_sensitive" if key in cost_sensitive else "cost_context_only"
        row["split_sensitivity_label"] = "universe_expansion_split_sensitive" if key in split_sensitive else "split_context_only"
        row["universe_sensitivity_label"] = universe_sensitivity_label(row, breadth)


def top3_by_universe(report_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        row["universe_name"]: row
        for row in report_rows
        if row.get("strategy_name") == "concentrated_growth_momentum_top3" and row.get("data_status") == "ok"
    }


def universe_sensitivity_label(row: dict[str, Any], breadth: dict[str, dict[str, Any]]) -> str:
    if row.get("strategy_name") != "concentrated_growth_momentum_top3" or row.get("data_status") != "ok":
        return "context_only"
    mega = breadth.get("mega_cap_growth_10")
    if not mega or row.get("universe_name") == "mega_cap_growth_10":
        return "baseline_universe"
    cagr_delta = float(row.get("cagr_pct", 0.0)) - float(mega.get("cagr_pct", 0.0))
    if cagr_delta < -5.0:
        return "performance_decays_with_breadth"
    if cagr_delta > 5.0:
        return "performance_improves_with_breadth"
    return "performance_stable_with_breadth"


def build_summary_rows(created_at: str, report_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], concentration_rows: list[dict[str, Any]], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    candidates = [row for row in report_rows if row["strategy_name"] in STRATEGY_NAMES and row.get("data_status") == "ok"]
    best = max(candidates, key=lambda row: (float(row.get("cagr_pct", 0.0)), float(row.get("calmar_ratio", 0.0))), default={})
    worst = min(candidates, key=lambda row: float(row.get("max_drawdown_pct", 0.0)), default={})
    largest_concentration = max(candidates, key=lambda row: float(row.get("max_single_name_concentration", 0.0)), default={})
    cost_flags = sorted({f"{row['universe_name']}:{row['strategy_name']}" for row in cost_rows if row.get("cost_sensitivity_label") == "universe_expansion_cost_sensitive"})
    split_flags = sorted({f"{row['universe_name']}:{row['strategy_name']}" for row in split_rows if row.get("split_sensitivity_label") == "universe_expansion_split_sensitive"})
    top3_rows = top3_by_universe(report_rows)
    entries = [
        ("best_universe_strategy_combination", label_for(best), format_candidate(best)),
        ("comparison_vs_original_top3", comparison_against(best, ORIGINAL_TOP3, "original_top3_small_universe"), "Original top3 reference came from the small high-growth stock lab result."),
        ("comparison_vs_qqq_100_trend_gate", comparison_against(best, QQQ_TREND_GATE, "qqq_100_trend_gate"), "QQQ trend gate remains cleaner if drawdown/robustness are materially better."),
        ("universe_breadth_sensitivity", breadth_sensitivity_text(top3_rows), "Answers whether top3 improves, decays, or becomes unstable as universe breadth expands."),
        ("biggest_concentration_outlier_warning", concentration_warning_text(largest_concentration, concentration_rows), "Survivorship bias and single-name event risk remain explicit."),
        ("worst_drawdown_warning", f"{label_for(worst)} max_drawdown_pct={worst.get('max_drawdown_pct', '')}", "Drawdown is the main high-growth stock expansion risk."),
        ("cost_split_sensitivity_warning", f"cost_sensitive={','.join(cost_flags) or 'none'}; split_sensitive={','.join(split_flags) or 'none'}", "Cost and split warnings are research labels only."),
        ("final_research_conclusion", final_conclusion(best, top3_rows), "No execution approval."),
        ("data_issues", f"ticker_errors={len(data_errors)}", "; ".join(f"{k}={v}" for k, v in sorted(data_errors.items()))[:500]),
    ]
    return [summary_row(created_at, name, value, details) for name, value, details in entries]


def final_conclusion(best: dict[str, Any], top3_rows: dict[str, dict[str, Any]]) -> str:
    if not best:
        return "insufficient_market_data; research_only_not_execution_ready"
    sensitivity = breadth_sensitivity_text(top3_rows)
    if "decays" in sensitivity:
        return "universe_expansion_decays_with_breadth; qqq_trend_gate_remains_cleaner_lead; execution_approved=false"
    if best.get("decision_label") in {"universe_expansion_outlier_dependent", "universe_expansion_drawdown_too_high"}:
        return f"{best.get('decision_label')}; qqq_trend_gate_remains_cleaner_lead; execution_approved=false"
    if best.get("decision_label") == "universe_expansion_confirms_high_growth_edge":
        return "universe_expansion_confirms_high_growth_edge; still_research_only; qqq_trend_gate_remains_cleaner_on_simplicity_review"
    return f"{best.get('decision_label', 'research_only_not_execution_ready')}; qqq_trend_gate_remains_cleaner_lead"


def breadth_sensitivity_text(top3_rows: dict[str, dict[str, Any]]) -> str:
    if len(top3_rows) < 2:
        return "insufficient_market_data"
    mega = top3_rows.get("mega_cap_growth_10", {})
    pieces = []
    decays = False
    for universe_name in ["expanded_growth_30", "broad_liquid_growth_50"]:
        row = top3_rows.get(universe_name)
        if not row or not mega:
            pieces.append(f"{universe_name}=unavailable")
            continue
        delta = round(float(row.get("cagr_pct", 0.0)) - float(mega.get("cagr_pct", 0.0)), 4)
        label = row.get("universe_sensitivity_label", "context_only")
        decays = decays or label == "performance_decays_with_breadth"
        pieces.append(f"{universe_name}: CAGR_delta_vs_mega10={delta}; {label}")
    prefix = "performance_decays_with_breadth" if decays else "performance_not_confirmed_as_decay"
    return f"{prefix}; " + "; ".join(pieces)


def comparison_against(row: dict[str, Any], benchmark: dict[str, float], benchmark_name: str) -> str:
    if not row:
        return f"no candidate available versus {benchmark_name}"
    return (
        f"{label_for(row)}: CAGR_delta={round(float(row.get('cagr_pct', 0.0)) - benchmark['cagr_pct'], 4)}; "
        f"Sharpe_delta={round(float(row.get('sharpe_ratio', 0.0)) - benchmark['sharpe_ratio'], 4)}; "
        f"Calmar_delta={round(float(row.get('calmar_ratio', 0.0)) - benchmark['calmar_ratio'], 4)}; "
        f"MaxDD_delta={round(float(row.get('max_drawdown_pct', 0.0)) - benchmark['max_drawdown_pct'], 4)}"
    )


def concentration_warning_text(row: dict[str, Any], concentration_rows: list[dict[str, Any]]) -> str:
    if not row:
        return "unavailable"
    ticker_rows = [item for item in concentration_rows if item.get("universe_name") == row.get("universe_name") and item.get("strategy_name") == row.get("strategy_name")]
    largest = max(ticker_rows, key=lambda item: float(item.get("contribution_pct", 0.0) or 0.0), default={})
    return f"{label_for(row)}: max_single_name_concentration={row.get('max_single_name_concentration', '')}; largest_contributor={largest.get('ticker', '')}; survivorship_bias_warning=true; single_name_event_risk_warning=true"


def format_candidate(row: dict[str, Any]) -> str:
    if not row:
        return "unavailable"
    return f"CAGR={row.get('cagr_pct')}%; Sharpe={row.get('sharpe_ratio')}; MaxDD={row.get('max_drawdown_pct')}%; Calmar={row.get('calmar_ratio')}; decision={row.get('decision_label')}"


def label_for(row: dict[str, Any]) -> str:
    if not row:
        return "none"
    return f"{row.get('universe_name')}:{row.get('strategy_name')}"


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock universe expansion report complete. Research only; execution_approved=False.",
        f"Best universe/strategy combination: {summary_value(summary_rows, 'best_universe_strategy_combination')}",
        f"Comparison versus original top3: {summary_value(summary_rows, 'comparison_vs_original_top3')}",
        f"Comparison versus qqq_100_trend_gate: {summary_value(summary_rows, 'comparison_vs_qqq_100_trend_gate')}",
        f"Universe breadth sensitivity: {summary_value(summary_rows, 'universe_breadth_sensitivity')}",
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


def summary_row(created_at: str, name: str, value: str, details: str) -> dict[str, Any]:
    return {"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


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
