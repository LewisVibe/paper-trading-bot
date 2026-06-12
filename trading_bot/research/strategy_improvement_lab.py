"""Research-only growth-aware ETF strategy improvement lab.

This module runs a fixed, small ETF allocation lab. It downloads daily yfinance
history only, writes generated research CSVs, and never touches broker,
position, SQLite, Discord, scheduler, or execution paths.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location


STARTING_EQUITY = 10000.0
HISTORY_PERIOD = "10y"
DAILY_INTERVAL = "1d"
MOMENTUM_LOOKBACK_DAYS = 126
TREND_WINDOW_DAYS = 200
TOP_N = 3
IN_SAMPLE_FRACTION = 0.70
STRONG_BREADTH_THRESHOLD = 0.60
MIXED_BREADTH_THRESHOLD = 0.40
WEAK_BREADTH_THRESHOLD = 0.30
VOLATILITY_WINDOW_DAYS = 20
VOLATILITY_MEDIAN_WINDOW_DAYS = 252
EXTREME_VOLATILITY_MULTIPLE = 1.75
COST_AWARE_REBALANCE_THRESHOLD = 0.05
COST_AWARE_CLOSE_RANK_BUFFER = 2

RISK_ETFS = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLK",
    "XLF",
    "XLY",
    "XLE",
    "XLI",
    "XLV",
    "XLP",
    "XLU",
]
DEFENSIVE_ETFS = ["SHY", "IEF", "TLT", "GLD"]
FACTOR_STYLE_ETFS = ["MTUM", "QUAL", "USMV", "VLUE", "VTV", "VUG", "RSP", "IWM", "SPY", "QQQ"]
SECTOR_52_WEEK_ETFS = ["XLK", "XLY", "XLF", "XLI", "XLE", "XLP", "XLU", "XLV", "XLB", "XLRE", "XLC"]
MULTI_SLEEVE_GROWTH_ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLY", "XLF", "XLI", "XLE"]
MULTI_SLEEVE_FACTOR_ETFS = ["MTUM", "QUAL", "USMV", "VLUE", "VUG", "VTV", "RSP"]
MULTI_SLEEVE_DEFENSIVE_ETFS = ["SHY", "IEF", "TLT", "GLD", "XLU", "XLP", "USMV"]
MULTI_SLEEVE_RISK_ETFS = sorted(set(MULTI_SLEEVE_GROWTH_ETFS + MULTI_SLEEVE_FACTOR_ETFS))
ALL_ETFS = sorted(
    set(
        RISK_ETFS
        + DEFENSIVE_ETFS
        + FACTOR_STYLE_ETFS
        + SECTOR_52_WEEK_ETFS
        + MULTI_SLEEVE_GROWTH_ETFS
        + MULTI_SLEEVE_FACTOR_ETFS
        + MULTI_SLEEVE_DEFENSIVE_ETFS
    )
)

STRATEGY_NAMES = [
    "spy_buy_and_hold_benchmark",
    "equal_weight_etf_buy_and_hold_benchmark",
    "monthly_etf_momentum_rotation_reference",
    "balanced_dual_momentum_defensive_sleeve",
    "breadth_aware_risk_on_rotation",
    "growth_biased_rotation_crash_gate",
    "growth_biased_rotation_cost_aware_rebalance",
    "factor_style_rotation_absolute_gate",
    "sector_52_week_high_continuation",
    "adaptive_multi_sleeve_growth_allocator",
]
DEFENSIVE_EXPOSURE_ETFS = sorted(set(DEFENSIVE_ETFS + MULTI_SLEEVE_DEFENSIVE_ETFS))
RISK_EXPOSURE_ETFS = sorted(set(ALL_ETFS) - set(DEFENSIVE_EXPOSURE_ETFS))

OUTPUT_FILES = {
    "results": Path("data/strategy_improvement_lab_results.csv"),
    "trades": Path("data/strategy_improvement_lab_trades.csv"),
    "equity": Path("data/strategy_improvement_lab_equity_curve.csv"),
    "summary": Path("data/strategy_improvement_lab_summary.csv"),
    "iteration": Path("data/strategy_improvement_lab_iteration_log.csv"),
}

COMMON_COLUMNS = [
    "created_at",
    "strategy_name",
    "period",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "trade_count",
    "turnover",
    "benchmark_strategy_name",
    "benchmark_cagr_pct",
    "benchmark_sharpe_ratio",
    "benchmark_max_drawdown_pct",
    "benchmark_calmar_ratio",
    "cagr_delta_vs_benchmark",
    "sharpe_delta_vs_benchmark",
    "max_drawdown_delta_vs_benchmark",
    "calmar_delta_vs_benchmark",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
]

RESULT_COLUMNS = COMMON_COLUMNS + [
    "total_return_pct",
    "average_cash_weight_pct",
    "average_risk_weight_pct",
    "average_defensive_weight_pct",
    "decision_label",
    "notes",
]

TRADE_COLUMNS = COMMON_COLUMNS + [
    "date",
    "ticker",
    "old_weight",
    "new_weight",
    "weight_change",
    "reason",
    "notes",
]

EQUITY_COLUMNS = COMMON_COLUMNS + [
    "date",
    "equity",
    "cash_weight",
    "risk_weight",
    "defensive_weight",
    "selected_tickers",
    "regime",
    "notes",
]

SUMMARY_COLUMNS = COMMON_COLUMNS + [
    "total_return_pct",
    "average_cash_weight_pct",
    "average_risk_weight_pct",
    "average_defensive_weight_pct",
    "decision_label",
    "rank_by_calmar",
    "rank_by_sharpe",
    "rank_by_cagr",
    "is_benchmark",
    "notes",
]

ITERATION_COLUMNS = COMMON_COLUMNS + [
    "iteration_id",
    "hypothesis",
    "allowed_parameter_set",
    "reason_for_testing",
    "result_summary",
    "decision_label",
    "required_next_step",
    "notes",
]


@dataclass
class StrategyImprovementLabResult:
    results_path: Path
    trades_path: Path
    equity_curve_path: Path
    summary_path: Path
    iteration_log_path: Path
    result_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    equity_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    iteration_rows: list[dict[str, Any]]
    summary_lines: list[str]


def run_strategy_improvement_lab_files(data_dir: Path | str = "data") -> StrategyImprovementLabResult:
    root = Path(".")
    data_path = Path(data_dir)
    configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    price_data, data_errors = download_daily_price_data(ALL_ETFS)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}

    result_rows, trade_rows, equity_rows, summary_rows, iteration_rows = build_strategy_improvement_outputs(
        created_at=created_at,
        price_data=price_data,
        data_errors=data_errors,
    )
    write_rows(output_paths["results"], RESULT_COLUMNS, result_rows)
    write_rows(output_paths["trades"], TRADE_COLUMNS, trade_rows)
    write_rows(output_paths["equity"], EQUITY_COLUMNS, equity_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["iteration"], ITERATION_COLUMNS, iteration_rows)
    return StrategyImprovementLabResult(
        results_path=output_paths["results"],
        trades_path=output_paths["trades"],
        equity_curve_path=output_paths["equity"],
        summary_path=output_paths["summary"],
        iteration_log_path=output_paths["iteration"],
        result_rows=result_rows,
        trade_rows=trade_rows,
        equity_rows=equity_rows,
        summary_rows=summary_rows,
        iteration_rows=iteration_rows,
        summary_lines=build_summary_lines(summary_rows, data_errors, output_paths),
    )


def download_daily_price_data(tickers: list[str]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    import yfinance as yf

    price_data: dict[str, list[dict[str, Any]]] = {}
    data_errors: dict[str, str] = {}
    for ticker in tickers:
        try:
            data = yf.download(
                ticker,
                period=HISTORY_PERIOD,
                interval=DAILY_INTERVAL,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if data is None or data.empty:
                data_errors[ticker] = "No daily market data returned by yfinance."
                continue
            rows = []
            for index, row in data.iterrows():
                close = value_from_row(row, "Close")
                if close is None or close <= 0:
                    continue
                rows.append({"date": index.date().isoformat(), "close": float(close)})
            if len(rows) < TREND_WINDOW_DAYS + 2:
                data_errors[ticker] = f"Not enough daily history; got {len(rows)} usable rows."
                continue
            price_data[ticker] = rows
        except Exception as exc:
            data_errors[ticker] = str(exc)
    return price_data, data_errors


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


def build_strategy_improvement_outputs(
    created_at: str,
    price_data: dict[str, list[dict[str, Any]]],
    data_errors: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    data_errors = data_errors or {}
    aligned_rows = align_price_rows(price_data)
    if not aligned_rows:
        result_rows = build_insufficient_data_rows(created_at, data_errors)
        summary_rows = build_summary_rows(result_rows)
        iteration_rows = build_iteration_rows(created_at, result_rows, data_errors)
        return result_rows, [], [], summary_rows, iteration_rows

    all_trade_rows: list[dict[str, Any]] = []
    all_equity_rows: list[dict[str, Any]] = []
    per_strategy_trades: dict[str, list[dict[str, Any]]] = {}
    per_strategy_equity: dict[str, list[dict[str, Any]]] = {}

    for strategy_name in STRATEGY_NAMES:
        equity_rows, trade_rows = simulate_strategy(strategy_name, aligned_rows, created_at)
        per_strategy_equity[strategy_name] = equity_rows
        per_strategy_trades[strategy_name] = trade_rows

    result_rows = []
    for strategy_name in STRATEGY_NAMES:
        result_rows.extend(
            build_result_rows_for_strategy(
                created_at,
                strategy_name,
                per_strategy_equity[strategy_name],
                per_strategy_trades[strategy_name],
            )
        )

    apply_benchmark_comparisons(result_rows)
    for strategy_name in STRATEGY_NAMES:
        full_metrics = full_period_metrics(result_rows, strategy_name)
        all_trade_rows.extend(enrich_trade_rows(per_strategy_trades[strategy_name], full_metrics))
        all_equity_rows.extend(enrich_equity_rows(per_strategy_equity[strategy_name], full_metrics))

    summary_rows = build_summary_rows(result_rows)
    iteration_rows = build_iteration_rows(created_at, result_rows, data_errors)
    return result_rows, all_trade_rows, all_equity_rows, summary_rows, iteration_rows


def align_price_rows(price_data: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    required = [ticker for ticker in ALL_ETFS if ticker in price_data]
    if "SPY" not in required or len([ticker for ticker in RISK_ETFS if ticker in required]) < TOP_N:
        return []
    date_sets = [{str(row["date"]) for row in price_data[ticker]} for ticker in required]
    dates = sorted(set.intersection(*date_sets))
    lookup = {
        ticker: {str(row["date"]): float(row["close"]) for row in rows}
        for ticker, rows in price_data.items()
        if ticker in required
    }
    return [
        {"date": date, "close": {ticker: lookup[ticker][date] for ticker in required}}
        for date in dates
    ]


def simulate_strategy(
    strategy_name: str,
    aligned_rows: list[dict[str, Any]],
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    equity = STARTING_EQUITY
    current_weights: dict[str, float] = {}
    history: dict[str, list[float]] = {ticker: [] for ticker in ALL_ETFS}
    equity_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    current_month = ""
    previous_close: dict[str, float] | None = None

    for row in aligned_rows:
        date = str(row["date"])
        close_by_ticker = {ticker: float(price) for ticker, price in row["close"].items()}
        for ticker, close in close_by_ticker.items():
            history.setdefault(ticker, []).append(close)

        if previous_close is not None:
            equity *= weighted_daily_return(current_weights, previous_close, close_by_ticker)

        month = date[:7]
        reason = ""
        regime = "hold_previous_weights"
        if month != current_month and sufficient_history(history):
            current_month = month
            target_weights, reason, regime = target_weights_for_strategy(strategy_name, history, current_weights)
            trade_rows.extend(build_trade_rows(created_at, date, strategy_name, current_weights, target_weights, reason))
            current_weights = target_weights

        cash_weight = max(0.0, 1.0 - sum(current_weights.values()))
        defensive_weight = sum(weight for ticker, weight in current_weights.items() if ticker in DEFENSIVE_EXPOSURE_ETFS)
        risk_weight = sum(weight for ticker, weight in current_weights.items() if ticker in RISK_EXPOSURE_ETFS)
        equity_rows.append(
            {
                "created_at": created_at,
                "strategy_name": strategy_name,
                "period": "full_period",
                "date": date,
                "equity": round(equity, 4),
                "cash_weight": round(cash_weight, 6),
                "risk_weight": round(risk_weight, 6),
                "defensive_weight": round(defensive_weight, 6),
                "selected_tickers": ",".join(sorted(current_weights)),
                "regime": regime,
                "notes": reason,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
                "paper_execution_approved": False,
            }
        )
        previous_close = close_by_ticker

    return equity_rows, trade_rows


def weighted_daily_return(
    weights: dict[str, float],
    previous_close: dict[str, float],
    close_by_ticker: dict[str, float],
) -> float:
    if not weights:
        return 1.0
    weighted_return = 0.0
    for ticker, weight in weights.items():
        previous = previous_close.get(ticker)
        latest = close_by_ticker.get(ticker)
        if previous is None or latest is None or previous <= 0:
            continue
        weighted_return += weight * ((latest / previous) - 1.0)
    return 1.0 + weighted_return


def sufficient_history(history: dict[str, list[float]]) -> bool:
    return len(history.get("SPY", [])) >= TREND_WINDOW_DAYS + 1


def target_weights_for_strategy(
    strategy_name: str,
    history: dict[str, list[float]],
    current_weights: dict[str, float],
) -> tuple[dict[str, float], str, str]:
    if strategy_name == "spy_buy_and_hold_benchmark":
        return {"SPY": 1.0}, "SPY buy-and-hold benchmark.", "benchmark"
    if strategy_name == "equal_weight_etf_buy_and_hold_benchmark":
        available = [ticker for ticker in RISK_ETFS if ticker in history and len(history[ticker]) >= 2]
        return equal_weights(available), "Equal-weight risk ETF buy-and-hold benchmark.", "benchmark"
    if strategy_name == "monthly_etf_momentum_rotation_reference":
        return reference_rotation_weights(history)
    if strategy_name == "balanced_dual_momentum_defensive_sleeve":
        return balanced_dual_momentum_weights(history)
    if strategy_name == "breadth_aware_risk_on_rotation":
        return breadth_aware_weights(history)
    if strategy_name == "growth_biased_rotation_crash_gate":
        return growth_biased_weights(history, current_weights)
    if strategy_name == "growth_biased_rotation_cost_aware_rebalance":
        return growth_biased_cost_aware_weights(history, current_weights)
    if strategy_name == "factor_style_rotation_absolute_gate":
        return factor_style_rotation_weights(history)
    if strategy_name == "sector_52_week_high_continuation":
        return sector_52_week_high_weights(history)
    if strategy_name == "adaptive_multi_sleeve_growth_allocator":
        return adaptive_multi_sleeve_weights(history)
    raise ValueError(f"Unknown strategy_name: {strategy_name}")


def reference_rotation_weights(history: dict[str, list[float]]) -> tuple[dict[str, float], str, str]:
    if not is_above_sma(history["SPY"], TREND_WINDOW_DAYS):
        return {}, "SPY below 200-day SMA; reference rotation holds cash.", "risk_off_cash"
    selections = [
        ticker
        for ticker in rank_by_composite_momentum(RISK_ETFS, history)
        if is_above_sma(history[ticker], TREND_WINDOW_DAYS)
    ][:TOP_N]
    return equal_weights(selections), "Reference monthly ETF rotation: SPY regime and ETF trend filters.", "risk_on"


def balanced_dual_momentum_weights(history: dict[str, list[float]]) -> tuple[dict[str, float], str, str]:
    if is_above_sma(history["SPY"], TREND_WINDOW_DAYS):
        selections = [
            ticker
            for ticker in rank_by_momentum(RISK_ETFS, history, MOMENTUM_LOOKBACK_DAYS)
            if momentum(history[ticker], MOMENTUM_LOOKBACK_DAYS) > 0
        ][:TOP_N]
        if selections:
            return equal_weights(selections), "Broad regime healthy; holding top 3 risk ETFs by 126-day momentum.", "risk_on"
    defensive = defensive_sleeve_weights(history)
    if defensive:
        return defensive, "Broad regime weak or no positive risk momentum; using defensive sleeve.", "defensive"
    return {}, "No acceptable defensive trend; holding cash.", "cash"


def breadth_aware_weights(history: dict[str, list[float]]) -> tuple[dict[str, float], str, str]:
    breadth = breadth_ratio(history)
    top_risk = rank_by_momentum(RISK_ETFS, history, MOMENTUM_LOOKBACK_DAYS)[:TOP_N]
    defensive = defensive_sleeve_weights(history)
    if breadth >= STRONG_BREADTH_THRESHOLD:
        return equal_weights(top_risk), f"Breadth {breadth:.2f}; full risk-on top 3.", "strong_breadth_risk_on"
    if breadth >= MIXED_BREADTH_THRESHOLD:
        weights = scaled_weights(equal_weights(top_risk), 0.50)
        weights.update(add_weights(weights, scaled_weights(defensive, 0.50)))
        return weights, f"Breadth {breadth:.2f}; mixed risk and defensive/cash posture.", "mixed_breadth"
    if defensive:
        return defensive, f"Breadth {breadth:.2f}; weak breadth defensive sleeve.", "weak_breadth_defensive"
    return {}, f"Breadth {breadth:.2f}; weak breadth cash.", "weak_breadth_cash"


def growth_biased_weights(
    history: dict[str, list[float]],
    current_weights: dict[str, float],
) -> tuple[dict[str, float], str, str]:
    breadth = breadth_ratio(history)
    spy_healthy = is_above_sma(history["SPY"], TREND_WINDOW_DAYS)
    ranked = rank_by_momentum(RISK_ETFS, history, MOMENTUM_LOOKBACK_DAYS)
    eligible = [ticker for ticker in ranked if is_above_sma(history[ticker], TREND_WINDOW_DAYS)]
    if not spy_healthy and breadth < MIXED_BREADTH_THRESHOLD:
        held = [ticker for ticker in current_weights if ticker in eligible][:TOP_N]
        if held:
            return equal_weights(held), "SPY weak and breadth weak; permits only existing eligible risk holdings.", "crash_gate_hold_only"
        defensive = defensive_sleeve_weights(history)
        if defensive:
            return defensive, "SPY weak and breadth weak; no existing eligible risk holdings, using defensive sleeve.", "crash_gate_defensive"
        return {}, "SPY weak and breadth weak; no eligible risk or defensive trend, holding cash.", "crash_gate_cash"
    selections = eligible[:TOP_N]
    if selections:
        return equal_weights(selections), "Growth-biased top 3 above own 200-day SMA; SPY filter softened unless breadth weak.", "growth_risk_on"
    defensive = defensive_sleeve_weights(history)
    if defensive:
        return defensive, "No risk ETF above own trend; using defensive sleeve.", "growth_defensive"
    return {}, "No eligible risk or defensive trend; holding cash.", "growth_cash"


def growth_biased_cost_aware_weights(
    history: dict[str, list[float]],
    current_weights: dict[str, float],
) -> tuple[dict[str, float], str, str]:
    base_weights, base_reason, regime = growth_biased_weights(history, current_weights)
    if not base_weights or regime not in {"growth_risk_on", "crash_gate_hold_only"}:
        return base_weights, base_reason + " Cost-aware threshold inactive outside eligible growth-risk posture.", regime

    ranked = rank_by_momentum(RISK_ETFS, history, MOMENTUM_LOOKBACK_DAYS)
    eligible = [ticker for ticker in ranked if is_above_sma(history[ticker], TREND_WINDOW_DAYS)]
    close_group = set(eligible[: TOP_N + COST_AWARE_CLOSE_RANK_BUFFER])
    retained = [
        ticker
        for ticker in current_weights
        if ticker in close_group
    ]
    target_tickers = retained[:]
    for ticker in list(base_weights):
        if ticker not in target_tickers:
            target_tickers.append(ticker)
    target_tickers = target_tickers[:TOP_N]
    adjusted = equal_weights(target_tickers)
    for ticker, current_weight in current_weights.items():
        intended_weight = adjusted.get(ticker, 0.0)
        if ticker in adjusted and abs(intended_weight - current_weight) < COST_AWARE_REBALANCE_THRESHOLD:
            adjusted[ticker] = current_weight
    adjusted = normalize_weights(adjusted)
    return (
        adjusted,
        (
            base_reason
            + f" Cost-aware refinement preserves eligible near-top holdings and skips weight changes below {COST_AWARE_REBALANCE_THRESHOLD:.0%}."
        ),
        "growth_cost_aware",
    )


def factor_style_rotation_weights(history: dict[str, list[float]]) -> tuple[dict[str, float], str, str]:
    spy_healthy = is_above_sma(history["SPY"], TREND_WINDOW_DAYS)
    breadth = breadth_ratio_for(FACTOR_STYLE_ETFS, history)
    eligible = [
        ticker
        for ticker in rank_by_momentum(FACTOR_STYLE_ETFS, history, MOMENTUM_LOOKBACK_DAYS)
        if is_above_sma(history[ticker], TREND_WINDOW_DAYS)
    ][:TOP_N]
    if not eligible:
        return {}, "No factor/style ETF qualifies above its 200-day SMA; holding cash.", "factor_cash"
    if spy_healthy:
        return equal_weights(eligible), "SPY above 200-day SMA; factor/style top 3 absolute-gate allocation.", "factor_risk_on"
    if breadth >= 0.50:
        return (
            scaled_weights(equal_weights(eligible), 0.60),
            f"SPY below 200-day SMA but factor breadth {breadth:.2f}; reduced allocation to eligible factor/style ETFs.",
            "factor_reduced_risk",
        )
    return {}, f"SPY below 200-day SMA and factor breadth {breadth:.2f}; holding cash.", "factor_risk_off_cash"


def sector_52_week_high_weights(history: dict[str, list[float]]) -> tuple[dict[str, float], str, str]:
    spy_healthy = is_above_sma(history["SPY"], TREND_WINDOW_DAYS)
    breadth = breadth_ratio_for(SECTOR_52_WEEK_ETFS, history)
    eligible = [
        ticker
        for ticker in rank_by_sector_continuation(SECTOR_52_WEEK_ETFS, history)
        if is_above_sma(history[ticker], TREND_WINDOW_DAYS) and not is_extreme_volatility(history[ticker])
    ][:TOP_N]
    if not eligible:
        return {}, "No sector ETF qualifies by trend and volatility screen; holding cash.", "sector_cash"
    if spy_healthy:
        return equal_weights(eligible), "SPY above 200-day SMA; sector 52-week-high continuation top 3.", "sector_risk_on"
    if breadth >= 0.50:
        return (
            scaled_weights(equal_weights(eligible), 0.60),
            f"SPY below 200-day SMA but sector breadth {breadth:.2f}; reduced sector continuation allocation.",
            "sector_reduced_risk",
        )
    return {}, f"SPY below 200-day SMA and sector breadth {breadth:.2f}; holding cash.", "sector_risk_off_cash"


def adaptive_multi_sleeve_weights(history: dict[str, list[float]]) -> tuple[dict[str, float], str, str]:
    spy_healthy = is_above_sma(history["SPY"], TREND_WINDOW_DAYS)
    breadth = breadth_ratio_for(MULTI_SLEEVE_RISK_ETFS, history)
    vol_extreme = is_extreme_volatility(history["SPY"])
    top_risk = rank_by_multi_sleeve_score(MULTI_SLEEVE_RISK_ETFS, history)[:4]
    defensive = defensive_sleeve_weights_for(MULTI_SLEEVE_DEFENSIVE_ETFS, history)

    if breadth < WEAK_BREADTH_THRESHOLD or vol_extreme:
        if defensive:
            return defensive, f"Stress regime: breadth {breadth:.2f}, extreme volatility={vol_extreme}; defensive sleeve only.", "multi_stress_defensive"
        return {}, f"Stress regime: breadth {breadth:.2f}, extreme volatility={vol_extreme}; holding cash.", "multi_stress_cash"

    if spy_healthy and breadth >= STRONG_BREADTH_THRESHOLD:
        return equal_weights(top_risk), f"Healthy regime: SPY trend positive, breadth {breadth:.2f}; full growth/factor sleeve.", "multi_healthy_growth"

    if (spy_healthy and breadth >= MIXED_BREADTH_THRESHOLD) or ((not spy_healthy) and breadth >= 0.50):
        risk_weights = scaled_weights(equal_weights(top_risk), 0.65)
        defensive_weights = scaled_weights(defensive, 0.35)
        weights = add_weights(risk_weights, defensive_weights)
        return weights, f"Mixed regime: SPY trend={spy_healthy}, breadth {breadth:.2f}; 65/35 risk and defensive sleeves.", "multi_mixed"

    if defensive:
        return scaled_weights(defensive, 0.85), f"Weak regime: breadth {breadth:.2f}; mostly defensive sleeve with cash buffer.", "multi_weak_defensive"
    return {}, f"Weak regime: breadth {breadth:.2f}; holding cash.", "multi_weak_cash"


def defensive_sleeve_weights(history: dict[str, list[float]]) -> dict[str, float]:
    return defensive_sleeve_weights_for(DEFENSIVE_ETFS, history)


def defensive_sleeve_weights_for(tickers: list[str], history: dict[str, list[float]]) -> dict[str, float]:
    selections = [
        ticker
        for ticker in rank_by_momentum(tickers, history, MOMENTUM_LOOKBACK_DAYS)
        if momentum(history[ticker], MOMENTUM_LOOKBACK_DAYS) >= 0 and is_above_sma(history[ticker], TREND_WINDOW_DAYS)
    ][:2]
    return equal_weights(selections)


def rank_by_momentum(tickers: list[str], history: dict[str, list[float]], lookback_days: int) -> list[str]:
    candidates = [
        (ticker, momentum(history[ticker], lookback_days))
        for ticker in tickers
        if ticker in history and len(history[ticker]) > lookback_days
    ]
    return [ticker for ticker, _score in sorted(candidates, key=lambda item: (-item[1], item[0]))]


def rank_by_composite_momentum(tickers: list[str], history: dict[str, list[float]]) -> list[str]:
    candidates = [
        (ticker, composite_momentum(history[ticker]))
        for ticker in tickers
        if ticker in history and len(history[ticker]) > 252
    ]
    return [ticker for ticker, _score in sorted(candidates, key=lambda item: (-item[1], item[0]))]


def rank_by_sector_continuation(tickers: list[str], history: dict[str, list[float]]) -> list[str]:
    candidates = [
        (ticker, momentum(history[ticker], MOMENTUM_LOOKBACK_DAYS) + high_closeness_score(history[ticker]))
        for ticker in tickers
        if ticker in history and len(history[ticker]) > 252
    ]
    return [ticker for ticker, _score in sorted(candidates, key=lambda item: (-item[1], item[0]))]


def rank_by_multi_sleeve_score(tickers: list[str], history: dict[str, list[float]]) -> list[str]:
    candidates = [
        (ticker, multi_sleeve_score(history[ticker]))
        for ticker in tickers
        if ticker in history and len(history[ticker]) > 252 and is_above_sma(history[ticker], TREND_WINDOW_DAYS)
    ]
    return [ticker for ticker, _score in sorted(candidates, key=lambda item: (-item[1], item[0]))]


def momentum(prices: list[float], lookback_days: int) -> float:
    if len(prices) <= lookback_days or prices[-lookback_days - 1] <= 0:
        return -999.0
    return (prices[-1] / prices[-lookback_days - 1]) - 1.0


def composite_momentum(prices: list[float]) -> float:
    return sum(momentum(prices, lookback) for lookback in [21, 63, 126, 252]) / 4.0


def high_closeness_score(prices: list[float]) -> float:
    if len(prices) < 252:
        return -1.0
    high = max(prices[-252:])
    if high <= 0:
        return -1.0
    return (prices[-1] / high) - 1.0


def multi_sleeve_score(prices: list[float]) -> float:
    vol_penalty = realised_volatility(prices, VOLATILITY_WINDOW_DAYS)
    return (
        0.50 * momentum(prices, MOMENTUM_LOOKBACK_DAYS)
        + 0.25 * momentum(prices, 63)
        + 0.25 * high_closeness_score(prices)
        - 0.10 * vol_penalty
    )


def is_above_sma(prices: list[float], window: int) -> bool:
    if len(prices) < window:
        return False
    return prices[-1] > (sum(prices[-window:]) / window)


def breadth_ratio(history: dict[str, list[float]]) -> float:
    return breadth_ratio_for(RISK_ETFS, history)


def breadth_ratio_for(tickers: list[str], history: dict[str, list[float]]) -> float:
    eligible = [ticker for ticker in tickers if ticker in history and len(history[ticker]) >= TREND_WINDOW_DAYS]
    if not eligible:
        return 0.0
    above = [ticker for ticker in eligible if is_above_sma(history[ticker], TREND_WINDOW_DAYS)]
    return len(above) / len(eligible)


def is_extreme_volatility(prices: list[float]) -> bool:
    if len(prices) < VOLATILITY_MEDIAN_WINDOW_DAYS + VOLATILITY_WINDOW_DAYS:
        return False
    current = realised_volatility(prices, VOLATILITY_WINDOW_DAYS)
    samples = [
        realised_volatility(prices[index - VOLATILITY_WINDOW_DAYS : index], VOLATILITY_WINDOW_DAYS)
        for index in range(len(prices) - VOLATILITY_MEDIAN_WINDOW_DAYS, len(prices) + 1)
        if index >= VOLATILITY_WINDOW_DAYS
    ]
    median = median_value([value for value in samples if value > 0])
    return median > 0 and current > median * EXTREME_VOLATILITY_MULTIPLE


def realised_volatility(prices: list[float], window: int) -> float:
    if len(prices) <= window:
        return 0.0
    returns = []
    for index in range(len(prices) - window + 1, len(prices)):
        previous = prices[index - 1]
        current = prices[index]
        if previous > 0:
            returns.append((current / previous) - 1.0)
    if len(returns) < 2:
        return 0.0
    mean_return = sum(returns) / len(returns)
    variance = sum((value - mean_return) ** 2 for value in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252.0)


def median_value(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2.0


def equal_weights(tickers: list[str]) -> dict[str, float]:
    unique = sorted(set(tickers))
    if not unique:
        return {}
    weight = 1.0 / len(unique)
    return {ticker: weight for ticker in unique}


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weight for weight in weights.values() if weight > 0)
    if total <= 0:
        return {}
    return {ticker: weight / total for ticker, weight in weights.items() if weight > 0}


def scaled_weights(weights: dict[str, float], scale: float) -> dict[str, float]:
    return {ticker: weight * scale for ticker, weight in weights.items()}


def add_weights(base: dict[str, float], additional: dict[str, float]) -> dict[str, float]:
    return {ticker: base.get(ticker, 0.0) + weight for ticker, weight in additional.items()}


def build_trade_rows(
    created_at: str,
    date: str,
    strategy_name: str,
    old_weights: dict[str, float],
    new_weights: dict[str, float],
    reason: str,
) -> list[dict[str, Any]]:
    rows = []
    for ticker in sorted(set(old_weights) | set(new_weights)):
        old_weight = old_weights.get(ticker, 0.0)
        new_weight = new_weights.get(ticker, 0.0)
        weight_change = new_weight - old_weight
        if abs(weight_change) < 0.000001:
            continue
        rows.append(
            {
                "created_at": created_at,
                "strategy_name": strategy_name,
                "period": "full_period",
                "date": date,
                "ticker": ticker,
                "old_weight": round(old_weight, 6),
                "new_weight": round(new_weight, 6),
                "weight_change": round(weight_change, 6),
                "reason": reason,
                "notes": "Synthetic research rebalance row; not an order instruction.",
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
                "paper_execution_approved": False,
            }
        )
    return rows


def build_result_rows_for_strategy(
    created_at: str,
    strategy_name: str,
    equity_rows: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    periods = period_slices(equity_rows)
    return [
        build_result_row(created_at, strategy_name, period_name, period_equity, trade_rows)
        for period_name, period_equity in periods
    ]


def period_slices(equity_rows: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    if len(equity_rows) < 4:
        return [("full_period", equity_rows), ("in_sample", []), ("out_of_sample", [])]
    split_index = max(2, int(len(equity_rows) * IN_SAMPLE_FRACTION))
    return [
        ("full_period", equity_rows),
        ("in_sample", equity_rows[:split_index]),
        ("out_of_sample", equity_rows[split_index - 1 :]),
    ]


def build_result_row(
    created_at: str,
    strategy_name: str,
    period: str,
    equity_rows: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(equity_rows) < 2:
        return base_metrics_row(created_at, strategy_name, period, "insufficient_data", "Not enough aligned daily rows.")
    equity_curve = [float(row["equity"]) for row in equity_rows]
    start_equity = equity_curve[0]
    final_equity = equity_curve[-1]
    max_drawdown = calculate_max_drawdown_pct(equity_curve)
    cagr = calculate_cagr_pct(start_equity, final_equity, len(equity_curve) - 1)
    sharpe = calculate_sharpe_ratio(equity_curve)
    calmar = cagr / abs(max_drawdown) if max_drawdown < 0 else 0.0
    start_date = str(equity_rows[0]["date"])
    end_date = str(equity_rows[-1]["date"])
    period_trades = [row for row in trade_rows if start_date <= str(row.get("date", "")) <= end_date]
    turnover = sum(abs(float(row.get("weight_change", 0))) for row in period_trades) / 2.0
    cash_weight = average_float(equity_rows, "cash_weight") * 100.0
    risk_weight = average_float(equity_rows, "risk_weight") * 100.0
    defensive_weight = average_float(equity_rows, "defensive_weight") * 100.0
    row = base_metrics_row(created_at, strategy_name, period, "", "")
    row.update(
        {
            "total_return_pct": round(((final_equity / start_equity) - 1.0) * 100.0, 4) if start_equity > 0 else 0.0,
            "cagr_pct": round(cagr, 4),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown_pct": round(max_drawdown, 4),
            "calmar_ratio": round(calmar, 4),
            "trade_count": len(period_trades),
            "turnover": round(turnover, 4),
            "average_cash_weight_pct": round(cash_weight, 4),
            "average_risk_weight_pct": round(risk_weight, 4),
            "average_defensive_weight_pct": round(defensive_weight, 4),
            "notes": "Fixed research-only daily-data ETF allocation lab.",
        }
    )
    return row


def base_metrics_row(
    created_at: str,
    strategy_name: str,
    period: str,
    decision_label: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "period": period,
        "total_return_pct": 0.0,
        "cagr_pct": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown_pct": 0.0,
        "calmar_ratio": 0.0,
        "trade_count": 0,
        "turnover": 0.0,
        "benchmark_strategy_name": "monthly_etf_momentum_rotation_reference",
        "benchmark_cagr_pct": "",
        "benchmark_sharpe_ratio": "",
        "benchmark_max_drawdown_pct": "",
        "benchmark_calmar_ratio": "",
        "cagr_delta_vs_benchmark": "",
        "sharpe_delta_vs_benchmark": "",
        "max_drawdown_delta_vs_benchmark": "",
        "calmar_delta_vs_benchmark": "",
        "average_cash_weight_pct": 0.0,
        "average_risk_weight_pct": 0.0,
        "average_defensive_weight_pct": 0.0,
        "decision_label": decision_label,
        "notes": notes,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
    }


def apply_benchmark_comparisons(result_rows: list[dict[str, Any]]) -> None:
    benchmark_rows = {
        row["period"]: row
        for row in result_rows
        if row["strategy_name"] == "monthly_etf_momentum_rotation_reference"
    }
    for row in result_rows:
        benchmark = benchmark_rows.get(row["period"])
        if not benchmark:
            continue
        row["benchmark_strategy_name"] = "monthly_etf_momentum_rotation_reference"
        row["benchmark_cagr_pct"] = benchmark["cagr_pct"]
        row["benchmark_sharpe_ratio"] = benchmark["sharpe_ratio"]
        row["benchmark_max_drawdown_pct"] = benchmark["max_drawdown_pct"]
        row["benchmark_calmar_ratio"] = benchmark["calmar_ratio"]
        row["cagr_delta_vs_benchmark"] = round(float(row["cagr_pct"]) - float(benchmark["cagr_pct"]), 4)
        row["sharpe_delta_vs_benchmark"] = round(float(row["sharpe_ratio"]) - float(benchmark["sharpe_ratio"]), 4)
        row["max_drawdown_delta_vs_benchmark"] = round(
            float(row["max_drawdown_pct"]) - float(benchmark["max_drawdown_pct"]),
            4,
        )
        row["calmar_delta_vs_benchmark"] = round(float(row["calmar_ratio"]) - float(benchmark["calmar_ratio"]), 4)
    for row in result_rows:
        row["decision_label"] = classify_decision(row, result_rows)


def classify_decision(row: dict[str, Any], result_rows: list[dict[str, Any]]) -> str:
    if float(row.get("trade_count", 0) or 0) == 0 and row["strategy_name"] not in {
        "spy_buy_and_hold_benchmark",
        "equal_weight_etf_buy_and_hold_benchmark",
    }:
        return "insufficient_data"
    if row["strategy_name"].endswith("_benchmark"):
        return "benchmark_reference"
    if row["period"] != "full_period":
        return row.get("decision_label") or "period_diagnostic"
    cagr_delta = float(row.get("cagr_delta_vs_benchmark") or 0.0)
    sharpe_delta = float(row.get("sharpe_delta_vs_benchmark") or 0.0)
    calmar_delta = float(row.get("calmar_delta_vs_benchmark") or 0.0)
    drawdown_delta = float(row.get("max_drawdown_delta_vs_benchmark") or 0.0)
    oos = find_result_row(result_rows, row["strategy_name"], "out_of_sample")
    if oos and float(oos.get("calmar_ratio", 0) or 0) < float(row.get("calmar_ratio", 0) or 0) * 0.40:
        return "split_sensitive"
    if cagr_delta > 0 and sharpe_delta >= 0 and calmar_delta >= 0:
        return "promising_growth_candidate"
    if cagr_delta > 0 and drawdown_delta < -5:
        return "promising_but_drawdown_heavy"
    if cagr_delta < 0 and drawdown_delta > 0:
        return "defensive_but_return_drag"
    return "not_useful"


def find_result_row(result_rows: list[dict[str, Any]], strategy_name: str, period: str) -> dict[str, Any] | None:
    for row in result_rows:
        if row["strategy_name"] == strategy_name and row["period"] == period:
            return row
    return None


def full_period_metrics(result_rows: list[dict[str, Any]], strategy_name: str) -> dict[str, Any]:
    row = find_result_row(result_rows, strategy_name, "full_period") or {}
    return {column: row.get(column, "") for column in COMMON_COLUMNS}


def enrich_trade_rows(trade_rows: list[dict[str, Any]], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    return [{**metrics, **row} for row in trade_rows]


def enrich_equity_rows(equity_rows: list[dict[str, Any]], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    return [{**metrics, **row} for row in equity_rows]


def build_summary_rows(result_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    full_rows = [dict(row) for row in result_rows if row["period"] == "full_period"]
    rank_column(full_rows, "calmar_ratio", "rank_by_calmar")
    rank_column(full_rows, "sharpe_ratio", "rank_by_sharpe")
    rank_column(full_rows, "cagr_pct", "rank_by_cagr")
    for row in full_rows:
        row["is_benchmark"] = str(row["strategy_name"]).endswith("_benchmark")
    return full_rows


def rank_column(rows: list[dict[str, Any]], metric: str, output_column: str) -> None:
    ranked = sorted(rows, key=lambda row: float(row.get(metric, 0) or 0), reverse=True)
    for rank, row in enumerate(ranked, start=1):
        row[output_column] = rank


def build_iteration_rows(
    created_at: str,
    result_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
) -> list[dict[str, Any]]:
    rows = []
    descriptions = {
        "monthly_etf_momentum_rotation_reference": "Existing defensive monthly ETF rotation reference.",
        "balanced_dual_momentum_defensive_sleeve": "Risk-on top-three momentum with defensive sleeve when broad trend is weak.",
        "breadth_aware_risk_on_rotation": "Breadth-threshold allocation that reduces cash drag in mixed regimes.",
        "growth_biased_rotation_crash_gate": "Growth-biased own-trend rotation with a crash gate for weak breadth.",
        "growth_biased_rotation_cost_aware_rebalance": "Fixed-threshold cost-aware refinement of the growth-biased crash-gate strategy.",
        "factor_style_rotation_absolute_gate": "Factor/style ETF rotation using absolute trend gates and reduced weak-market exposure.",
        "sector_52_week_high_continuation": "Sector ETF continuation using fixed momentum plus 252-day-high closeness.",
        "adaptive_multi_sleeve_growth_allocator": "Fixed-rule multi-sleeve allocator blending growth, factor/style, defensive sleeve, breadth, and volatility diagnostics.",
    }
    for index, strategy_name in enumerate(descriptions, start=1):
        metrics = full_period_metrics(result_rows, strategy_name)
        result = find_result_row(result_rows, strategy_name, "full_period") or {}
        rows.append(
            {
                **metrics,
                "created_at": created_at,
                "strategy_name": strategy_name,
                "period": "full_period",
                "iteration_id": f"strategy_improvement_lab_{index:03d}",
                "hypothesis": descriptions[strategy_name],
                "allowed_parameter_set": (
                    "monthly rebalance; 126-day momentum; 200-day trend; fixed 252-day high score; fixed breadth thresholds 60/40/30; fixed volatility window 20/252; fixed cost-aware rebalance threshold 5%."
                ),
                "reason_for_testing": "Explore growth-aware ETF allocation variants without execution approval.",
                "result_summary": result_summary_text(result),
                "decision_label": result.get("decision_label", "insufficient_data"),
                "required_next_step": "Manual research review only; do not connect to execution.",
                "notes": "Data errors: " + "; ".join(f"{ticker}: {error}" for ticker, error in sorted(data_errors.items()))[:500],
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
                "paper_execution_approved": False,
            }
        )
    return rows


def result_summary_text(row: dict[str, Any]) -> str:
    if not row:
        return "Insufficient data."
    return (
        f"CAGR {row.get('cagr_pct')}%, Sharpe {row.get('sharpe_ratio')}, "
        f"max drawdown {row.get('max_drawdown_pct')}%, Calmar {row.get('calmar_ratio')}."
    )


def build_insufficient_data_rows(created_at: str, data_errors: dict[str, str]) -> list[dict[str, Any]]:
    notes = "Insufficient yfinance daily history. " + "; ".join(
        f"{ticker}: {error}" for ticker, error in sorted(data_errors.items())
    )
    return [
        base_metrics_row(created_at, strategy_name, period, "insufficient_data", notes[:1000])
        for strategy_name in STRATEGY_NAMES
        for period in ["full_period", "in_sample", "out_of_sample"]
    ]


def calculate_cagr_pct(starting_equity: float, final_equity: float, trading_days: int) -> float:
    if starting_equity <= 0 or final_equity <= 0 or trading_days <= 0:
        return 0.0
    years = trading_days / 252.0
    if years <= 0:
        return 0.0
    return ((final_equity / starting_equity) ** (1.0 / years) - 1.0) * 100.0


def calculate_sharpe_ratio(equity_curve: list[float]) -> float:
    returns = daily_returns(equity_curve)
    if len(returns) < 2:
        return 0.0
    mean_return = sum(returns) / len(returns)
    variance = sum((value - mean_return) ** 2 for value in returns) / (len(returns) - 1)
    volatility = math.sqrt(variance)
    if volatility == 0:
        return 0.0
    return (mean_return / volatility) * math.sqrt(252.0)


def calculate_max_drawdown_pct(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value / peak) - 1.0)
    return worst * 100.0


def daily_returns(equity_curve: list[float]) -> list[float]:
    returns = []
    for index in range(1, len(equity_curve)):
        previous = equity_curve[index - 1]
        current = equity_curve[index]
        if previous > 0:
            returns.append((current / previous) - 1.0)
    return returns


def average_float(rows: list[dict[str, Any]], column: str) -> float:
    values = [float(row.get(column, 0.0) or 0.0) for row in rows]
    return sum(values) / len(values) if values else 0.0


def build_summary_lines(
    summary_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
    output_paths: dict[str, Path],
) -> list[str]:
    rows = [row for row in summary_rows if row.get("period") == "full_period"]
    benchmarks = [row for row in rows if str(row.get("strategy_name", "")).endswith("_benchmark")]
    active = [row for row in rows if row not in benchmarks]
    best_benchmark = best_row(benchmarks, "calmar_ratio")
    best_active = best_row(active, "calmar_ratio")
    best_cagr = best_row(active, "cagr_pct")
    lowest_drawdown = min(active, key=lambda row: abs(float(row.get("max_drawdown_pct", 0) or 0)), default=None)
    lines = [
        "Strategy improvement lab complete. Research/preview only; execution_approved=False.",
        f"Strategies tested: {len(rows)} full-period rows.",
        f"Tickers with data errors: {len(data_errors)}.",
    ]
    if best_benchmark:
        lines.append(
            f"Best benchmark by Calmar: {best_benchmark['strategy_name']} "
            f"(CAGR {best_benchmark['cagr_pct']}%, Sharpe {best_benchmark['sharpe_ratio']}, "
            f"Calmar {best_benchmark['calmar_ratio']})."
        )
    if best_active:
        lines.append(
            f"Best active candidate by Calmar: {best_active['strategy_name']} "
            f"({best_active['decision_label']}; CAGR {best_active['cagr_pct']}%, "
            f"Sharpe {best_active['sharpe_ratio']}, Calmar {best_active['calmar_ratio']})."
        )
    if best_cagr:
        lines.append(f"Best active CAGR: {best_cagr['strategy_name']} at {best_cagr['cagr_pct']}%.")
    if lowest_drawdown:
        lines.append(
            f"Lowest active drawdown: {lowest_drawdown['strategy_name']} at "
            f"{lowest_drawdown['max_drawdown_pct']}%."
        )
    lines.extend(
        [
            f"Saved results to {output_paths['results']}",
            f"Saved trades to {output_paths['trades']}",
            f"Saved equity curve to {output_paths['equity']}",
            f"Saved summary to {output_paths['summary']}",
            f"Saved iteration log to {output_paths['iteration']}",
            "Warning: promising labels are future research labels only and do not approve orders or paper execution.",
        ]
    )
    return lines


def best_row(rows: list[dict[str, Any]], metric: str) -> dict[str, Any] | None:
    return max(rows, key=lambda row: float(row.get(metric, 0) or 0), default=None)


def show_strategy_improvement_lab_file(
    summary_path: Path | str = OUTPUT_FILES["summary"],
) -> tuple[int, list[str]]:
    path = Path(summary_path)
    if not path.exists():
        return 1, ["Run `python bot.py --strategy-improvement-lab` first."]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return 1, [f"No rows found in {path}. Run `python bot.py --strategy-improvement-lab` first."]

    benchmarks = [row for row in rows if parse_bool(row.get("is_benchmark"))]
    active = [row for row in rows if not parse_bool(row.get("is_benchmark"))]
    lines = [
        "Strategy improvement lab saved summary. Display only; execution_approved=False.",
        f"Rows: {len(rows)}",
    ]
    for label, row in [
        ("Best benchmark", best_row(benchmarks, "calmar_ratio")),
        ("Best active by Calmar", best_row(active, "calmar_ratio")),
        ("Best active CAGR", best_row(active, "cagr_pct")),
        ("Lowest active drawdown", min(active, key=lambda item: abs(float(item.get("max_drawdown_pct", 0) or 0)), default=None)),
    ]:
        if row:
            lines.append(
                f"{label}: {row['strategy_name']} | label={row.get('decision_label')} | "
                f"CAGR={row.get('cagr_pct')}% | Sharpe={row.get('sharpe_ratio')} | "
                f"MaxDD={row.get('max_drawdown_pct')}% | Calmar={row.get('calmar_ratio')}"
            )
    sensitive = [row["strategy_name"] for row in active if row.get("decision_label") in {"split_sensitive", "defensive_but_return_drag"}]
    if sensitive:
        lines.append("Warnings: " + ", ".join(sorted(sensitive)))
    unsafe = [
        row["strategy_name"]
        for row in rows
        if parse_bool(row.get("execution_approved")) or parse_bool(row.get("paper_execution_approved"))
    ]
    if unsafe:
        lines.append("WARNING: execution approval flag was not false for: " + ", ".join(sorted(unsafe)))
    lines.append("Warning: this display reads saved CSV only and does not approve orders.")
    return 0, lines


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
