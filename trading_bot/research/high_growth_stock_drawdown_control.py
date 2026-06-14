"""Research-only high-growth stock drawdown-control report.

This report tests fixed drawdown-control variants for the broad liquid growth
stock universe. It does not call Alpaca, load config, read positions, create
orders, write SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from trading_bot.research import high_growth_stock_lab as lab
from trading_bot.research.high_growth_stock_universe_expansion import UNIVERSES


OUTPUT_FILES = {
    "report": Path("data/high_growth_stock_drawdown_control_report.csv"),
    "summary": Path("data/high_growth_stock_drawdown_control_summary.csv"),
    "trades": Path("data/high_growth_stock_drawdown_control_trades.csv"),
    "costs": Path("data/high_growth_stock_drawdown_control_costs.csv"),
    "splits": Path("data/high_growth_stock_drawdown_control_splits.csv"),
    "drawdowns": Path("data/high_growth_stock_drawdown_control_drawdowns.csv"),
    "concentration": Path("data/high_growth_stock_drawdown_control_concentration.csv"),
}

BROAD_UNIVERSE_NAME = "broad_liquid_growth_50"
BROAD_UNIVERSE = UNIVERSES[BROAD_UNIVERSE_NAME]
STRATEGY_NAMES = [
    "broad_growth_top1_reference",
    "broad_growth_top2_reference",
    "broad_growth_top3_reference",
    "broad_growth_top1_drawdown_brake",
    "broad_growth_top1_volatility_gate",
    "broad_growth_top1_cooldown_after_crash",
    "codex_broad_growth_balanced_breakout_control",
]
BENCHMARK_STRATEGIES = ["qqq_buy_and_hold_benchmark", "spy_buy_and_hold_benchmark", "cash_benchmark"]
TOP1_REFERENCE = {"cagr_pct": 60.3606, "sharpe_ratio": 1.1129, "calmar_ratio": 0.8603, "max_drawdown_pct": -70.1642}
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
    "current_constituent_bias_warning",
    "single_name_event_risk_warning",
    "outlier_dependence_warning",
    "stock_specific_gap_risk_warning",
    "drawdown_warning",
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
class DrawdownControlResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_drawdown_control_report(root_dir: Path | str = ".") -> DrawdownControlResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    tickers = BROAD_UNIVERSE + lab.BENCHMARK_TICKERS
    price_data, data_errors = lab.download_daily_price_data(tickers, root / "data" / "yfinance_cache")
    simulations = build_simulations(price_data, data_errors)
    report_rows = [build_report_row(created_at, simulation, "full_period", price_data, data_errors) for simulation in simulations]
    cost_rows = build_cost_rows(created_at, simulations, price_data, data_errors)
    split_rows = build_split_rows(created_at, simulations, price_data, data_errors)
    drawdown_rows = build_drawdown_rows(created_at, simulations, price_data, data_errors)
    concentration_rows = build_concentration_rows(created_at, simulations, price_data, data_errors)
    trade_rows = [trade_row(created_at, trade) for simulation in simulations for trade in simulation.trades]
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
    return DrawdownControlResult(output_paths, report_rows, summary_rows, build_summary_lines(summary_rows, output_paths))


def show_high_growth_stock_drawdown_control_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    report_path = root / OUTPUT_FILES["report"]
    if not summary_path.exists() or not report_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-drawdown-control-report` first."]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock drawdown-control saved display. Research only; execution_approved=False.",
        f"Best drawdown-control candidate: {summary_value(summary_rows, 'best_drawdown_control_candidate')}",
        f"Comparison versus broad_liquid_growth_50 top1: {summary_value(summary_rows, 'comparison_vs_broad_top1')}",
        f"Comparison versus qqq_100_trend_gate: {summary_value(summary_rows, 'comparison_vs_qqq_100_trend_gate')}",
        f"Drawdown reduction achieved: {summary_value(summary_rows, 'drawdown_reduction_achieved')}",
        f"Return drag: {summary_value(summary_rows, 'return_drag')}",
        f"Biggest concentration/outlier warning: {summary_value(summary_rows, 'biggest_concentration_outlier_warning')}",
        f"Worst drawdown warning: {summary_value(summary_rows, 'worst_drawdown_warning')}",
        f"Cost/split sensitivity warning: {summary_value(summary_rows, 'cost_split_sensitivity_warning')}",
        f"Final research conclusion: {summary_value(summary_rows, 'final_research_conclusion')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no Alpaca commands, order instructions, paper execution, or scheduling approval.",
    ]


def build_simulations(price_data: dict[str, list[dict[str, Any]]], data_errors: dict[str, str]) -> list[lab.StrategySimulation]:
    stock_data = {ticker: rows for ticker, rows in price_data.items() if ticker in BROAD_UNIVERSE}
    if len(stock_data) < 3 or not any(ticker in price_data for ticker in lab.BENCHMARK_TICKERS):
        reason = f"Insufficient market data; universe={BROAD_UNIVERSE_NAME}; stock_rows={len(stock_data)}; errors={len(data_errors)}"
        return [lab.insufficient_simulation(name, reason) for name in STRATEGY_NAMES + BENCHMARK_STRATEGIES]
    dates = lab.common_dates(stock_data)
    return [
        simulate_top_n_reference("broad_growth_top1_reference", 1, price_data, dates),
        simulate_top_n_reference("broad_growth_top2_reference", 2, price_data, dates),
        simulate_top_n_reference("broad_growth_top3_reference", 3, price_data, dates),
        simulate_top1_drawdown_brake(price_data, dates),
        simulate_top1_volatility_gate(price_data, dates),
        simulate_top1_cooldown_after_crash(price_data, dates),
        simulate_balanced_breakout_control(price_data, dates),
        simulate_buy_and_hold_if_available("qqq_buy_and_hold_benchmark", "QQQ", price_data),
        simulate_buy_and_hold_if_available("spy_buy_and_hold_benchmark", "SPY", price_data),
        simulate_cash_benchmark(dates),
    ]


def simulate_top_n_reference(name: str, top_n: int, price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def policy(index: int, current_weights: dict[str, float], equity: float, high: float, curve: list[dict[str, Any]]) -> tuple[dict[str, float], str, str]:
        selected = top_momentum_eligible(price_data, dates[index], top_n)
        if not selected:
            return {}, "No stock passes own SMA200 and QQQ/SPY regime gate; holding cash.", "cash_no_stock_passes"
        return lab.equal_weights(selected), f"Broad growth top {top_n} reference: equal-weight top momentum stock(s).", "risk_on"

    return simulate_control_strategy(name, price_data, dates, policy, "Broad 50-stock fixed monthly momentum reference; own SMA200; QQQ/SPY SMA200 regime gate.")


def simulate_top1_drawdown_brake(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def policy(index: int, current_weights: dict[str, float], equity: float, high: float, curve: list[dict[str, Any]]) -> tuple[dict[str, float], str, str]:
        drawdown = equity / high - 1.0 if high > 0 else 0.0
        equity_recovering = len(curve) >= 50 and equity > average_equity(curve[-50:])
        if drawdown <= -0.25 and not equity_recovering:
            selected = top_momentum_eligible(price_data, dates[index], 3)
            if selected:
                return lab.equal_weights(selected), "Drawdown brake active after 25% portfolio drawdown; fallback to Top3 until equity recovery confirmation.", "drawdown_brake_top3"
            return {}, "Drawdown brake active after 25% portfolio drawdown; no Top3 fallback available.", "drawdown_brake_cash"
        selected = top_momentum_eligible(price_data, dates[index], 1)
        return (lab.equal_weights(selected), "Top1 with 25% drawdown brake and equity SMA50-style recovery confirmation.", "risk_on_top1") if selected else ({}, "No eligible Top1 holding.", "cash_no_stock_passes")

    return simulate_control_strategy("broad_growth_top1_drawdown_brake", price_data, dates, policy, "Top1 momentum with fixed 25% portfolio drawdown brake; fallback to Top3/cash until equity recovery confirmation.")


def simulate_top1_volatility_gate(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def policy(index: int, current_weights: dict[str, float], equity: float, high: float, curve: list[dict[str, Any]]) -> tuple[dict[str, float], str, str]:
        selected = top_momentum_eligible(price_data, dates[index], 1)
        if not selected:
            return {}, "No eligible Top1 holding.", "cash_no_stock_passes"
        ticker = selected[0]
        if volatility_gate_ok(price_data[ticker], dates[index]):
            return lab.equal_weights(selected), "Top1 volatility gate passed: 20-day realised volatility below 1.25x 252-day median.", "risk_on_vol_gate"
        fallback = top_momentum_eligible(price_data, dates[index], 3)
        if fallback:
            return lab.equal_weights(fallback), "Top1 volatility gate failed; fallback to Top3.", "vol_gate_top3"
        return {}, "Top1 volatility gate failed; no Top3 fallback available.", "vol_gate_cash"

    return simulate_control_strategy("broad_growth_top1_volatility_gate", price_data, dates, policy, "Top1 momentum with fixed 20-day volatility gate versus 252-day median; fallback to Top3/cash.")


def simulate_top1_cooldown_after_crash(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def policy(index: int, current_weights: dict[str, float], equity: float, high: float, curve: list[dict[str, Any]]) -> tuple[dict[str, float], str, str]:
        selected = top_momentum_eligible(price_data, dates[index], 1)
        if not selected:
            return {}, "No eligible Top1 holding.", "cash_no_stock_passes"
        ticker = selected[0]
        rows = price_data[ticker]
        close = lab.price_on(rows, dates[index])
        high_126 = lab.rolling_high(rows, dates[index], 126)
        crash = close / high_126 - 1.0 if high_126 > 0 else -1.0
        recovered = lab.above_sma(rows, dates[index], 50) and lab.above_sma(rows, dates[index], lab.TREND_WINDOW)
        if crash <= -0.25 and not recovered:
            return {}, "Selected Top1 stock is more than 25% below its 126-day high and has not reclaimed SMA50/SMA200; cooldown cash.", "cooldown_cash"
        return lab.equal_weights(selected), "Top1 cooldown passed: no unresolved 25% crash from 126-day high.", "risk_on_cooldown"

    return simulate_control_strategy("broad_growth_top1_cooldown_after_crash", price_data, dates, policy, "Top1 momentum with fixed cooldown after >25% fall from 126-day high until SMA50/SMA200 recovery.")


def simulate_balanced_breakout_control(price_data: dict[str, list[dict[str, Any]]], dates: list[str]) -> lab.StrategySimulation:
    def policy(index: int, current_weights: dict[str, float], equity: float, high: float, curve: list[dict[str, Any]]) -> tuple[dict[str, float], str, str]:
        date = dates[index]
        if not lab.regime_ok(price_data, date):
            return {}, "QQQ/SPY regime below 200-day SMA; holding cash.", "risk_off_cash"
        scores = []
        for ticker in BROAD_UNIVERSE:
            rows = price_data.get(ticker, [])
            if not lab.enough_history(rows, date, 252):
                continue
            close = lab.price_on(rows, date)
            high_252 = lab.rolling_high(rows, date, 252)
            proximity = close / high_252 if high_252 > 0 else 0.0
            momentum = lab.composite_momentum(rows, date)
            if proximity >= 0.90 and momentum > 0 and lab.above_sma(rows, date, lab.TREND_WINDOW) and volatility_gate_ok(rows, date):
                scores.append((ticker, momentum + proximity))
        selected = [ticker for ticker, _score in sorted(scores, key=lambda item: item[1], reverse=True)[:2]]
        if selected:
            return lab.equal_weights(selected), "Codex balanced breakout control: Top2 near highs with SMA200 and volatility gate.", "risk_on_balanced_breakout"
        fallback = top_momentum_eligible(price_data, date, 3)
        if fallback:
            return lab.equal_weights(fallback), "Balanced breakout filter found no near-high leaders; fallback to Top3.", "balanced_breakout_top3"
        return {}, "Balanced breakout filter found no eligible holdings; holding cash.", "balanced_breakout_cash"

    return simulate_control_strategy("codex_broad_growth_balanced_breakout_control", price_data, dates, policy, "Codex fixed ambitious rule: near 52-week highs, SMA200, volatility gate, Top2 primary with Top3 fallback; no leverage or shorting.")


ControlPolicy = Callable[[int, dict[str, float], float, float, list[dict[str, Any]]], tuple[dict[str, float], str, str]]


def simulate_control_strategy(name: str, price_data: dict[str, list[dict[str, Any]]], dates: list[str], policy: ControlPolicy, notes: str) -> lab.StrategySimulation:
    equity = lab.STARTING_EQUITY
    equity_high = equity
    current_weights: dict[str, float] = {}
    previous_prices: dict[str, float] = {}
    curve: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    contributions: dict[str, float] = {}
    holding_weights: dict[str, list[float]] = {}
    rebalance_month = ""
    start_index = max(lab.MOMENTUM_WINDOWS) + 1
    for index, date in enumerate(dates):
        if index < start_index:
            continue
        if previous_prices:
            daily_return = 0.0
            for ticker, weight in current_weights.items():
                current_price = lab.price_on(price_data[ticker], date)
                prior = previous_prices.get(ticker, current_price)
                ret = current_price / prior - 1.0 if prior > 0 else 0.0
                daily_return += weight * ret
                contributions[ticker] = contributions.get(ticker, 0.0) + weight * ret
            equity *= 1.0 + daily_return
            equity_high = max(equity_high, equity)
        month = date[:7]
        if month != rebalance_month:
            rebalance_month = month
            new_weights, reason, regime = policy(index, current_weights, equity, equity_high, curve)
            turnover = lab.weight_turnover(current_weights, new_weights)
            if turnover > 0 or new_weights != current_weights:
                trades.append({"strategy_name": name, "rebalance_date": date, "selected_tickers": ",".join(new_weights), "weights": lab.format_weights(new_weights), "regime_status": regime, "reason": reason, "turnover": round(turnover, 4)})
            current_weights = new_weights
        for ticker, weight in current_weights.items():
            holding_weights.setdefault(ticker, []).append(weight)
        curve.append({"date": date, "equity": equity, "holdings": len(current_weights), "cash": 1.0 if not current_weights else 0.0, "max_weight": max(current_weights.values()) if current_weights else 0.0})
        previous_prices = {ticker: lab.price_on(price_data[ticker], date) for ticker in current_weights}
    return lab.StrategySimulation(name, curve, trades, contributions, holding_weights, "ok" if curve else "insufficient_market_data", notes)


def top_momentum_eligible(price_data: dict[str, list[dict[str, Any]]], date: str, top_n: int) -> list[str]:
    if not lab.regime_ok(price_data, date):
        return []
    scores = []
    for ticker in BROAD_UNIVERSE:
        rows = price_data.get(ticker, [])
        if not lab.enough_history(rows, date, max(lab.MOMENTUM_WINDOWS)):
            continue
        score = lab.composite_momentum(rows, date)
        if score > 0 and lab.above_sma(rows, date, lab.TREND_WINDOW):
            scores.append((ticker, score))
    return [ticker for ticker, _score in sorted(scores, key=lambda item: item[1], reverse=True)[:top_n]]


def volatility_gate_ok(rows: list[dict[str, Any]], date: str) -> bool:
    current = lab.realised_volatility(rows, date, 20)
    median = median_realised_volatility(rows, date, 20, 252)
    return current > 0 and median > 0 and current <= median * 1.25


def median_realised_volatility(rows: list[dict[str, Any]], date: str, vol_window: int, lookback: int) -> float:
    index = lab.row_index(rows, date)
    if index is None or index < lookback:
        return 0.0
    values = []
    for offset in range(index - lookback + 1, index + 1):
        values.append(lab.realised_volatility(rows, rows[offset]["date"], vol_window))
    values = [value for value in values if value > 0]
    return statistics.median(values) if values else 0.0


def average_equity(curve: list[dict[str, Any]]) -> float:
    return sum(float(row["equity"]) for row in curve) / len(curve) if curve else 0.0


def simulate_buy_and_hold_if_available(name: str, ticker: str, price_data: dict[str, list[dict[str, Any]]]) -> lab.StrategySimulation:
    if ticker not in price_data:
        return lab.insufficient_simulation(name, f"Missing {ticker} benchmark rows.")
    return lab.simulate_buy_and_hold(name, ticker, price_data[ticker])


def simulate_cash_benchmark(dates: list[str]) -> lab.StrategySimulation:
    curve = [{"date": date, "equity": lab.STARTING_EQUITY, "holdings": 0, "cash": 1.0, "max_weight": 0.0} for date in dates]
    return lab.StrategySimulation("cash_benchmark", curve, [], {}, {}, "ok" if curve else "insufficient_market_data", "Cash benchmark for context only.")


def build_report_row(created_at: str, simulation: lab.StrategySimulation, period: str, price_data: dict[str, list[dict[str, Any]]], data_errors: dict[str, str]) -> dict[str, Any]:
    row = lab.build_report_row(created_at, simulation, period)
    missing_tickers = [ticker for ticker in BROAD_UNIVERSE if ticker in data_errors]
    row.update(
        {
            "universe_name": BROAD_UNIVERSE_NAME,
            "usable_ticker_count": len([ticker for ticker in BROAD_UNIVERSE if ticker in price_data]),
            "missing_ticker_count": len(missing_tickers),
            "missing_tickers": ",".join(missing_tickers),
            "survivorship_bias_warning": "high_growth_stock_survivorship_bias_warning: fixed current broad universe may overstate historical opportunity.",
            "current_constituent_bias_warning": "current_constituent_bias_warning: this uses today's broad liquid growth universe, not historical constituents.",
            "outlier_dependence_warning": "outlier_dependence_warning: NVDA, TSLA, AMD, or another small group may dominate results.",
            "drawdown_warning": "drawdown_warning: high-growth stock drawdowns may remain much deeper than qqq_100_trend_gate.",
            **safety_flags(),
        }
    )
    return row


def build_cost_rows(created_at: str, simulations: list[lab.StrategySimulation], price_data: dict[str, list[dict[str, Any]]], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        base = build_report_row(created_at, simulation, "cost_stress", price_data, data_errors)
        turnover = float(base.get("turnover", 0.0))
        for bps in lab.REBALANCE_COST_BPS:
            stressed = lab.metrics_for_curve(lab.stress_curve_for_cost(simulation.curve, turnover, bps))
            row = dict(base)
            row.update(stressed)
            row["cost_bps"] = bps
            row["cost_stress_cagr_pct"] = stressed["cagr_pct"]
            row["cost_stress_calmar_ratio"] = stressed["calmar_ratio"]
            row["cost_sensitivity_label"] = "high_growth_stock_cost_sensitive" if bps == 50 and base.get("data_status") == "ok" and float(base.get("cagr_pct", 0.0)) - stressed["cagr_pct"] > 2.0 else "cost_context_only"
            rows.append(row)
    return rows


def build_split_rows(created_at: str, simulations: list[lab.StrategySimulation], price_data: dict[str, list[dict[str, Any]]], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        for name, fraction in lab.SPLITS:
            if not simulation.curve:
                row = build_report_row(created_at, simulation, name, price_data, data_errors)
            else:
                split_index = max(1, int(len(simulation.curve) * fraction))
                segment = simulation.curve[split_index:]
                row = build_report_row(created_at, lab.StrategySimulation(simulation.name, segment, [], {}, {}, simulation.data_status, simulation.notes), name, price_data, data_errors)
                row["split_start_date"] = segment[0]["date"] if segment else ""
                row["split_end_date"] = segment[-1]["date"] if segment else ""
            row["split_name"] = name
            row["split_fraction"] = fraction
            row["split_sensitivity_label"] = "high_growth_stock_split_sensitive" if simulation.data_status == "ok" and float(row.get("cagr_pct", 0.0)) < 0 else "split_context_only"
            rows.append(row)
    return rows


def build_drawdown_rows(created_at: str, simulations: list[lab.StrategySimulation], price_data: dict[str, list[dict[str, Any]]], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        row = build_report_row(created_at, simulation, "worst_drawdown_period", price_data, data_errors)
        row.update(lab.drawdown_window(simulation.curve))
        rows.append(row)
    return rows


def build_concentration_rows(created_at: str, simulations: list[lab.StrategySimulation], price_data: dict[str, list[dict[str, Any]]], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for simulation in simulations:
        base = build_report_row(created_at, simulation, "concentration", price_data, data_errors)
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


def trade_row(created_at: str, trade: dict[str, Any]) -> dict[str, Any]:
    return {"created_at": created_at, **trade, **safety_flags()}


def apply_decision_labels(report_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], concentration_rows: list[dict[str, Any]]) -> None:
    cost_sensitive = {row["strategy_name"] for row in cost_rows if row.get("cost_sensitivity_label") == "high_growth_stock_cost_sensitive"}
    split_sensitive = {row["strategy_name"] for row in split_rows if row.get("split_sensitivity_label") == "high_growth_stock_split_sensitive"}
    outlier_dependent = {row["strategy_name"] for row in concentration_rows if str(row.get("ticker")) in {"NVDA", "TSLA", "AMD"} and float(row.get("contribution_pct", 0.0) or 0.0) > 50.0}
    for row in report_rows:
        if row["data_status"] != "ok":
            row["decision_label"] = "insufficient_market_data"
        elif row["strategy_name"] not in STRATEGY_NAMES:
            row["decision_label"] = "benchmark_context_only"
        elif float(row["max_drawdown_pct"]) < -55.0:
            row["decision_label"] = "drawdown_control_still_too_deep"
        elif row["strategy_name"] in outlier_dependent:
            row["decision_label"] = "high_growth_stock_outlier_dependent"
        elif row["strategy_name"] in split_sensitive:
            row["decision_label"] = "high_growth_stock_split_sensitive"
        elif row["strategy_name"] in cost_sensitive:
            row["decision_label"] = "high_growth_stock_cost_sensitive"
        else:
            row["decision_label"] = classify_drawdown_control(row)
        row["cost_sensitivity_label"] = "high_growth_stock_cost_sensitive" if row["strategy_name"] in cost_sensitive else "cost_context_only"
        row["split_sensitivity_label"] = "high_growth_stock_split_sensitive" if row["strategy_name"] in split_sensitive else "split_context_only"


def classify_drawdown_control(row: dict[str, Any]) -> str:
    dd_reduction = float(row.get("max_drawdown_pct", 0.0)) - TOP1_REFERENCE["max_drawdown_pct"]
    cagr_drag = float(row.get("cagr_pct", 0.0)) - TOP1_REFERENCE["cagr_pct"]
    if dd_reduction >= 25.0 and float(row.get("cagr_pct", 0.0)) >= QQQ_TREND_GATE["cagr_pct"] + 10.0 and float(row.get("calmar_ratio", 0.0)) >= QQQ_TREND_GATE["calmar_ratio"]:
        return "drawdown_control_high_growth_research_lead"
    if dd_reduction >= 15.0 and cagr_drag > -25.0:
        return "drawdown_control_promising_but_concentrated"
    if dd_reduction >= 15.0:
        return "drawdown_control_reduces_drawdown_with_return_drag"
    if cagr_drag < -30.0:
        return "drawdown_control_rejected_return_drag"
    return "qqq_trend_gate_remains_cleaner_lead"


def build_summary_rows(created_at: str, report_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], concentration_rows: list[dict[str, Any]], data_errors: dict[str, str]) -> list[dict[str, Any]]:
    candidates = [row for row in report_rows if row["strategy_name"] in STRATEGY_NAMES and row.get("data_status") == "ok"]
    best = max(candidates, key=lambda row: (float(row.get("calmar_ratio", 0.0)), float(row.get("cagr_pct", 0.0))), default={})
    worst = min(candidates, key=lambda row: float(row.get("max_drawdown_pct", 0.0)), default={})
    largest_concentration = max(candidates, key=lambda row: float(row.get("max_single_name_concentration", 0.0)), default={})
    cost_flags = sorted({row["strategy_name"] for row in cost_rows if row.get("cost_sensitivity_label") == "high_growth_stock_cost_sensitive"})
    split_flags = sorted({row["strategy_name"] for row in split_rows if row.get("split_sensitivity_label") == "high_growth_stock_split_sensitive"})
    entries = [
        ("best_drawdown_control_candidate", best.get("strategy_name", "none"), format_candidate(best)),
        ("comparison_vs_broad_top1", comparison_against(best, TOP1_REFERENCE, "broad_liquid_growth_50_top1"), "Top1 reference is the saved universe-expansion result."),
        ("comparison_vs_qqq_100_trend_gate", comparison_against(best, QQQ_TREND_GATE, "qqq_100_trend_gate"), "QQQ trend gate remains cleaner if drawdown/robustness are materially better."),
        ("drawdown_reduction_achieved", drawdown_reduction_text(best), "Positive value means max drawdown improved versus broad_liquid_growth_50 Top1."),
        ("return_drag", return_drag_text(best), "Negative value means CAGR was sacrificed versus broad_liquid_growth_50 Top1."),
        ("biggest_concentration_outlier_warning", concentration_warning_text(largest_concentration, concentration_rows), "Survivorship, current-constituent, and single-name event risk remain explicit."),
        ("worst_drawdown_warning", f"{worst.get('strategy_name', 'none')} max_drawdown_pct={worst.get('max_drawdown_pct', '')}", "Drawdown is the main high-growth stock risk."),
        ("cost_split_sensitivity_warning", f"cost_sensitive={','.join(cost_flags) or 'none'}; split_sensitive={','.join(split_flags) or 'none'}", "Cost and split warnings are research labels only."),
        ("final_research_conclusion", final_conclusion(best), "No execution approval."),
        ("data_issues", f"ticker_errors={len(data_errors)}", "; ".join(f"{k}={v}" for k, v in sorted(data_errors.items()))[:500]),
    ]
    return [summary_row(created_at, name, value, details) for name, value, details in entries]


def final_conclusion(best: dict[str, Any]) -> str:
    if not best:
        return "insufficient_market_data; research_only_not_execution_ready"
    if best.get("decision_label") == "drawdown_control_high_growth_research_lead":
        return "drawdown_control_high_growth_research_lead; still_research_only; qqq_trend_gate_remains_cleaner_on_drawdown_review"
    if best.get("decision_label") in {"drawdown_control_promising_but_concentrated", "drawdown_control_reduces_drawdown_with_return_drag"}:
        return f"{best.get('decision_label')}; qqq_trend_gate_remains_cleaner_lead"
    return f"{best.get('decision_label', 'research_only_not_execution_ready')}; qqq_trend_gate_remains_cleaner_lead"


def comparison_against(row: dict[str, Any], benchmark: dict[str, float], benchmark_name: str) -> str:
    if not row:
        return f"no candidate available versus {benchmark_name}"
    return (
        f"{row.get('strategy_name')}: CAGR_delta={round(float(row.get('cagr_pct', 0.0)) - benchmark['cagr_pct'], 4)}; "
        f"Sharpe_delta={round(float(row.get('sharpe_ratio', 0.0)) - benchmark['sharpe_ratio'], 4)}; "
        f"Calmar_delta={round(float(row.get('calmar_ratio', 0.0)) - benchmark['calmar_ratio'], 4)}; "
        f"MaxDD_delta={round(float(row.get('max_drawdown_pct', 0.0)) - benchmark['max_drawdown_pct'], 4)}"
    )


def drawdown_reduction_text(row: dict[str, Any]) -> str:
    if not row:
        return "unavailable"
    return f"{row.get('strategy_name')}: MaxDD_improvement_vs_top1={round(float(row.get('max_drawdown_pct', 0.0)) - TOP1_REFERENCE['max_drawdown_pct'], 4)}"


def return_drag_text(row: dict[str, Any]) -> str:
    if not row:
        return "unavailable"
    return f"{row.get('strategy_name')}: CAGR_delta_vs_top1={round(float(row.get('cagr_pct', 0.0)) - TOP1_REFERENCE['cagr_pct'], 4)}"


def concentration_warning_text(row: dict[str, Any], concentration_rows: list[dict[str, Any]]) -> str:
    if not row:
        return "unavailable"
    ticker_rows = [item for item in concentration_rows if item.get("strategy_name") == row.get("strategy_name")]
    largest = max(ticker_rows, key=lambda item: float(item.get("contribution_pct", 0.0) or 0.0), default={})
    return f"{row.get('strategy_name')}: max_single_name_concentration={row.get('max_single_name_concentration', '')}; largest_contributor={largest.get('ticker', '')}; survivorship_bias_warning=true; current_constituent_bias_warning=true; outlier_dependence_warning=true"


def format_candidate(row: dict[str, Any]) -> str:
    if not row:
        return "unavailable"
    return f"CAGR={row.get('cagr_pct')}%; Sharpe={row.get('sharpe_ratio')}; MaxDD={row.get('max_drawdown_pct')}%; Calmar={row.get('calmar_ratio')}; decision={row.get('decision_label')}"


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock drawdown-control report complete. Research only; execution_approved=False.",
        f"Best drawdown-control candidate: {summary_value(summary_rows, 'best_drawdown_control_candidate')}",
        f"Comparison versus broad_liquid_growth_50 top1: {summary_value(summary_rows, 'comparison_vs_broad_top1')}",
        f"Comparison versus qqq_100_trend_gate: {summary_value(summary_rows, 'comparison_vs_qqq_100_trend_gate')}",
        f"Drawdown reduction achieved: {summary_value(summary_rows, 'drawdown_reduction_achieved')}",
        f"Return drag: {summary_value(summary_rows, 'return_drag')}",
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
