"""Research-only ETF breadth regime data prep and backtest.

The backtest reads saved ETF close-history CSV data only. The explicit price
history builder uses the project's existing research market-data helper. This
module does not call a broker, create orders, write SQLite rows, send alerts,
or approve execution.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from trading_bot.config import AppConfig
from trading_bot.market_data import configure_yfinance_cache, download_backtest_prices
from trading_bot.research.backtesting import calculate_cagr_pct, calculate_max_drawdown, calculate_sharpe_ratio


ETF_BREADTH_STRATEGY_NAME = "etf_breadth_regime_allocation"
ETF_BREADTH_PRICE_INPUT = "etf_breadth_price_history.csv"
ETF_BREADTH_UNIVERSE = [
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
RISK_ON_BREADTH_PCT = 60.0
NEUTRAL_BREADTH_PCT = 40.0
DEFENSIVE_BREADTH_PCT = 25.0
SMA_WINDOW = 200
MOMENTUM_LOOKBACK_DAYS = 126
TOP_N = 3
STARTING_EQUITY = 100_000.0
FIXED_SPLITS = [
    ("full_period", Decimal("0")),
    ("split_70_30_out_of_sample", Decimal("0.70")),
]

ETF_BREADTH_RESULT_COLUMNS = [
    "created_at",
    "strategy_name",
    "ticker_or_portfolio",
    "period",
    "start_date",
    "end_date",
    "total_return_pct",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "exposure_pct",
    "turnover_count",
    "number_of_regime_changes",
    "risk_on_pct",
    "neutral_pct",
    "defensive_pct",
    "cash_protection_pct",
    "breadth_thresholds",
    "allocation_rule",
    "cost_model_name",
    "robustness_status",
    "research_only",
    "preview_only",
    "execution_approved",
]

ETF_BREADTH_SUMMARY_COLUMNS = [
    "created_at",
    "regime",
    "day_count",
    "pct_of_days",
    "average_breadth_pct",
    "research_only",
    "preview_only",
    "execution_approved",
]

ETF_BREADTH_PRICE_HISTORY_COLUMNS = ["date", "ticker", "close"]

ETF_BREADTH_DECISION_COLUMNS = [
    "created_at",
    "candidate_name",
    "comparison_status",
    "decision_label",
    "metric",
    "breadth_value",
    "benchmark_name",
    "benchmark_value",
    "winner",
    "finding",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class EtfBreadthRegimeResult:
    output_path: Path
    summary_path: Path
    rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class EtfBreadthPriceHistoryResult:
    output_path: Path
    rows: list[dict[str, Any]]
    tickers_attempted: list[str]
    tickers_saved: list[str]
    errors: list[str]
    summary_lines: list[str]


@dataclass
class EtfBreadthDecisionResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def build_etf_breadth_price_history(
    config: AppConfig,
    logger,
    data_dir: Path | str = "data",
    downloader=None,
) -> EtfBreadthPriceHistoryResult:
    data_path = Path(data_dir)
    output_path = data_path / ETF_BREADTH_PRICE_INPUT
    fetch = downloader or download_backtest_prices
    if downloader is None:
        configure_yfinance_cache(config, logger)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    tickers_saved: list[str] = []
    for ticker in ETF_BREADTH_UNIVERSE:
        try:
            frame = fetch(config, ticker)
        except Exception as exc:
            errors.append(f"{ticker}: {exc}")
            continue
        ticker_rows = price_rows_from_frame(ticker, frame)
        if ticker_rows:
            tickers_saved.append(ticker)
            rows.extend(ticker_rows)
        else:
            errors.append(f"{ticker}: no valid close rows")
    rows = sorted(rows, key=lambda row: (str(row["date"]), str(row["ticker"])))
    write_rows(output_path, ETF_BREADTH_PRICE_HISTORY_COLUMNS, rows)
    return EtfBreadthPriceHistoryResult(
        output_path=output_path,
        rows=rows,
        tickers_attempted=list(ETF_BREADTH_UNIVERSE),
        tickers_saved=tickers_saved,
        errors=errors,
        summary_lines=build_price_history_summary(output_path, rows, tickers_saved, errors),
    )


def price_rows_from_frame(ticker: str, frame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if frame is None:
        return rows
    for index, row in frame.iterrows():
        close = parse_float(row.get("close"))
        if close <= 0:
            continue
        date_value = index.date().isoformat() if hasattr(index, "date") else str(index)[:10]
        rows.append({"date": date_value, "ticker": ticker, "close": round(close, 6)})
    return rows


def generate_etf_breadth_regime_backtest(
    data_dir: Path | str = "data",
    created_at: str | None = None,
) -> EtfBreadthRegimeResult:
    data_path = Path(data_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    price_rows = read_price_history(data_path / ETF_BREADTH_PRICE_INPUT)
    rows, summary_rows, lines = build_etf_breadth_outputs(price_rows, created)
    output_path = data_path / "etf_breadth_regime_backtest.csv"
    summary_path = data_path / "etf_breadth_regime_summary.csv"
    write_rows(output_path, ETF_BREADTH_RESULT_COLUMNS, rows)
    write_rows(summary_path, ETF_BREADTH_SUMMARY_COLUMNS, summary_rows)
    lines.extend(
        [
            f"Saved ETF breadth regime backtest to {output_path}",
            f"Saved ETF breadth regime summary to {summary_path}",
        ]
    )
    return EtfBreadthRegimeResult(output_path, summary_path, rows, summary_rows, lines)


def generate_etf_breadth_regime_decision_report(
    data_dir: Path | str = "data",
    created_at: str | None = None,
) -> EtfBreadthDecisionResult:
    data_path = Path(data_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    breadth_rows = read_price_history(data_path / "etf_breadth_regime_backtest.csv")
    summary_rows = read_price_history(data_path / "etf_breadth_regime_summary.csv")
    benchmark_rows = load_benchmark_rows(data_path)
    rows = build_decision_rows(created, breadth_rows, summary_rows, benchmark_rows)
    output_path = data_path / "etf_breadth_regime_decision_report.csv"
    write_rows(output_path, ETF_BREADTH_DECISION_COLUMNS, rows)
    return EtfBreadthDecisionResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_decision_summary(rows, breadth_rows, output_path),
    )


def build_etf_breadth_outputs(
    price_rows: list[dict[str, Any]],
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    aligned_rows = align_price_rows(price_rows)
    if len(aligned_rows) < SMA_WINDOW + 2 or "SPY" not in {ticker for row in aligned_rows for ticker in row["close"]}:
        rows = [insufficient_result_row(created_at, "full_period", "Saved ETF breadth price history is missing or too short.")]
        summary_rows = [insufficient_summary_row(created_at)]
        lines = [
            "ETF BREADTH REGIME BACKTEST. RESEARCH ONLY. NOT EXECUTION.",
            f"Missing or insufficient saved input: data/{ETF_BREADTH_PRICE_INPUT}",
            "Create saved ETF close-history CSV rows with columns date,ticker,close, then rerun.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
        ]
        return rows, summary_rows, lines

    daily_rows = build_daily_regime_rows(aligned_rows)
    equity_rows = simulate_breadth_regime_equity(daily_rows)
    result_rows = build_result_rows(created_at, equity_rows)
    summary_rows = build_regime_summary_rows(created_at, daily_rows)
    lines = build_summary_lines(result_rows, summary_rows)
    return result_rows, summary_rows, lines


def read_price_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_benchmark_rows(data_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(read_price_history(data_path / "defensive_candidate_comparison.csv"))
    rows.extend(read_price_history(data_path / "etf_rotation_robustness_report.csv"))
    rows.extend(read_price_history(data_path / "vol_managed_etf_robustness_report.csv"))
    return rows


def build_decision_rows(
    created_at: str,
    breadth_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    benchmark_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full = row_for_period(breadth_rows, "full_period")
    oos = row_for_period(breadth_rows, "split_70_30_out_of_sample")
    if not full or not real_metric_row(full):
        return [
            decision_row(
                created_at,
                "overall",
                "",
                "",
                "insufficient_comparison_data",
                "insufficient_comparison_data",
                "ETF breadth regime saved metrics are unavailable.",
                "Run python bot.py --build-etf-breadth-price-history, python bot.py --etf-breadth-regime-backtest, then rerun this report.",
            )
        ]

    benchmarks = selected_benchmarks(benchmark_rows)
    if not benchmarks:
        return [
            decision_row(
                created_at,
                "overall",
                "",
                "",
                "insufficient_comparison_data",
                "useful_diagnostic_not_strategy",
                "Breadth regime has real metrics, but saved ETF rotation/vol-managed comparison rows are unavailable.",
                "Use breadth as a diagnostic/filter candidate only; generate defensive comparison and robustness reports before promotion discussion.",
            ),
            *regime_decision_rows(created_at, summary_rows),
        ]

    rows: list[dict[str, Any]] = []
    comparison_labels: list[str] = []
    for benchmark in benchmarks:
        for metric in ["sharpe_ratio", "calmar_ratio", "max_drawdown_pct"]:
            breadth_value = metric_value_for_comparison(oos, full, metric)
            benchmark_value = benchmark_metric_value(benchmark, metric)
            if breadth_value is None or benchmark_value is None:
                continue
            winner = metric_winner(metric, breadth_value, benchmark_value)
            winner_name = ETF_BREADTH_STRATEGY_NAME if winner == ETF_BREADTH_STRATEGY_NAME else benchmark["strategy_name"]
            comparison_labels.append(winner_name)
            rows.append(
                decision_row(
                    created_at,
                    metric,
                    breadth_value,
                    benchmark_value,
                    comparison_status_for_winner(winner),
                    "",
                    comparison_finding(metric, breadth_value, benchmark["strategy_name"], benchmark_value, winner),
                    "",
                    benchmark_name=benchmark["strategy_name"],
                    winner=winner_name,
                )
            )
    final_label, final_finding, next_step = final_decision(rows, full, oos, benchmarks)
    rows.insert(
        0,
        decision_row(
            created_at,
            "overall",
            "",
            "",
            "compared_to_saved_defensive_candidates",
            final_label,
            final_finding,
            next_step,
            benchmark_name=", ".join(benchmark["strategy_name"] for benchmark in benchmarks),
            winner="not promoted",
        ),
    )
    rows.extend(regime_decision_rows(created_at, summary_rows))
    return rows


def selected_benchmarks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row.get("strategy_name", ""))
        if name not in {"monthly_etf_momentum_rotation", "volatility_managed_dual_momentum_etf"}:
            continue
        if str(row.get("period", "")) not in {"", "out_of_sample"}:
            continue
        if str(row.get("split_name", "")) not in {"", "split_70_30"}:
            continue
        by_name.setdefault(name, row)
    return [by_name[name] for name in ["monthly_etf_momentum_rotation", "volatility_managed_dual_momentum_etf"] if name in by_name]


def final_decision(
    rows: list[dict[str, Any]],
    full: dict[str, Any],
    oos: dict[str, Any],
    benchmarks: list[dict[str, Any]],
) -> tuple[str, str, str]:
    losses = [row for row in rows if row.get("winner") == str(row.get("benchmark_name"))]
    drawdown_wins = [row for row in rows if row.get("metric") == "max_drawdown_pct" and row.get("winner") == ETF_BREADTH_STRATEGY_NAME]
    metric_wins = [row for row in rows if row.get("winner") == ETF_BREADTH_STRATEGY_NAME]
    if losses and not drawdown_wins:
        return (
            "not_promoted_underperforms",
            "Breadth regime underperforms saved defensive candidates on risk-adjusted comparison metrics and does not materially reduce drawdown.",
            "Do not promote; keep monthly ETF rotation as preferred and use breadth only for research context.",
        )
    if drawdown_wins and len(metric_wins) <= len(losses):
        return (
            "useful_diagnostic_not_strategy",
            "Breadth regime may reduce drawdown in some comparisons, but the return/risk-adjusted tradeoff is not strong enough for promotion.",
            "Use breadth as a diagnostic/filter idea; require fixed-split robustness before any strategy discussion.",
        )
    if metric_wins and not losses and len(benchmarks) >= 2:
        return (
            "promising_needs_robustness",
            "Breadth regime compares well against saved defensive candidates, but this report does not promote strategies automatically.",
            "Run fixed-split robustness and drawdown comparison before any promotion discussion.",
        )
    return (
        "useful_diagnostic_not_strategy",
        "Breadth regime has real saved metrics, but comparison evidence is incomplete or mixed.",
        "Keep research-only and use breadth as a diagnostic/filter candidate.",
    )


def decision_row(
    created_at: str,
    metric: str,
    breadth_value: Any,
    benchmark_value: Any,
    comparison_status: str,
    decision_label: str,
    finding: str,
    required_next_step: str,
    benchmark_name: str = "",
    winner: str = "",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "candidate_name": ETF_BREADTH_STRATEGY_NAME,
        "comparison_status": comparison_status,
        "decision_label": decision_label,
        "metric": metric,
        "breadth_value": breadth_value,
        "benchmark_name": benchmark_name,
        "benchmark_value": benchmark_value,
        "winner": winner,
        "finding": finding,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def regime_decision_rows(created_at: str, summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in summary_rows:
        regime = str(row.get("regime", ""))
        if not regime or regime == "insufficient_data":
            continue
        rows.append(
            decision_row(
                created_at,
                f"time_in_{regime}",
                row.get("pct_of_days", ""),
                "",
                "regime_context",
                "useful_diagnostic_not_strategy",
                f"ETF breadth regime spent {row.get('pct_of_days', '')}% of saved days in {regime}.",
                "Use regime mix as diagnostic context; do not treat it as execution approval.",
            )
        )
    return rows


def row_for_period(rows: list[dict[str, Any]], period: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("period") == period:
            return row
    return None


def real_metric_row(row: dict[str, Any]) -> bool:
    return parse_float(row.get("cagr_pct")) != 0 or parse_float(row.get("sharpe_ratio")) != 0 or parse_float(row.get("calmar_ratio")) != 0


def metric_value_for_comparison(oos: dict[str, Any] | None, full: dict[str, Any], metric: str) -> float | None:
    source = oos if oos and str(oos.get(metric, "")) != "" else full
    value = parse_float(source.get(metric) if source else None)
    return value if str(source.get(metric, "")) != "" else None


def benchmark_metric_value(row: dict[str, Any], metric: str) -> float | None:
    keys = {
        "sharpe_ratio": ["out_of_sample_sharpe", "out_of_sample_sharpe_ratio", "sharpe_ratio"],
        "calmar_ratio": ["out_of_sample_calmar", "out_of_sample_calmar_ratio", "calmar_ratio"],
        "max_drawdown_pct": ["out_of_sample_max_drawdown_pct", "max_drawdown_pct"],
    }[metric]
    for key in keys:
        if str(row.get(key, "")) != "":
            return parse_float(row.get(key))
    return None


def metric_winner(metric: str, breadth_value: float, benchmark_value: float) -> str:
    if metric == "max_drawdown_pct":
        return ETF_BREADTH_STRATEGY_NAME if abs(breadth_value) < abs(benchmark_value) else "benchmark"
    return ETF_BREADTH_STRATEGY_NAME if breadth_value > benchmark_value else "benchmark"


def comparison_status_for_winner(winner: str) -> str:
    return "breadth_leads_metric" if winner == ETF_BREADTH_STRATEGY_NAME else "benchmark_leads_metric"


def comparison_finding(metric: str, breadth_value: float, benchmark_name: str, benchmark_value: float, winner: str) -> str:
    winner_name = ETF_BREADTH_STRATEGY_NAME if winner == ETF_BREADTH_STRATEGY_NAME else benchmark_name
    return f"{metric}: breadth={round(breadth_value, 4)} versus {benchmark_name}={round(benchmark_value, 4)}; winner={winner_name}."


def build_decision_summary(rows: list[dict[str, Any]], breadth_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    full = row_for_period(breadth_rows, "full_period") or {}
    oos = row_for_period(breadth_rows, "split_70_30_out_of_sample") or {}
    overall = rows[0] if rows else {}
    return [
        "ETF BREADTH REGIME DECISION REPORT. RESEARCH ONLY. NOT EXECUTION.",
        "Breadth full period: " + metrics_label(full),
        "Breadth OOS 70/30: " + metrics_label(oos),
        f"Decision label: {overall.get('decision_label', 'insufficient_comparison_data')}",
        f"Next step: {overall.get('required_next_step', '')}",
        f"Saved ETF breadth regime decision report to {output_path}",
        "No strategy was promoted.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
    ]


def align_price_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_date: dict[str, dict[str, float]] = {}
    for row in rows:
        date = str(row.get("date", "")).strip()
        ticker = str(row.get("ticker", "")).strip().upper()
        close = parse_float(row.get("close"))
        if not date or ticker not in ETF_BREADTH_UNIVERSE or close <= 0:
            continue
        by_date.setdefault(date, {})[ticker] = close
    return [
        {"date": date, "close": by_date[date]}
        for date in sorted(by_date)
        if "SPY" in by_date[date]
    ]


def build_daily_regime_rows(aligned_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closes_by_ticker = {ticker: [] for ticker in ETF_BREADTH_UNIVERSE}
    daily_rows: list[dict[str, Any]] = []
    for row in aligned_rows:
        date = str(row["date"])
        close_by_ticker = {ticker: float(price) for ticker, price in row["close"].items()}
        for ticker in ETF_BREADTH_UNIVERSE:
            if ticker in close_by_ticker:
                closes_by_ticker[ticker].append(close_by_ticker[ticker])
            else:
                closes_by_ticker[ticker].append(0.0)
        index = len(closes_by_ticker["SPY"]) - 1
        breadth = calculate_breadth_pct(close_by_ticker, closes_by_ticker, index)
        spy_sma = rolling_average_for_index(closes_by_ticker["SPY"], index, SMA_WINDOW)
        spy_above_sma = spy_sma is not None and close_by_ticker["SPY"] > spy_sma
        regime = classify_regime(breadth, spy_above_sma)
        daily_rows.append(
            {
                "date": date,
                "close": close_by_ticker,
                "breadth_pct": breadth,
                "spy_above_sma200": spy_above_sma,
                "regime": regime,
                "index": index,
                "history": closes_by_ticker,
            }
        )
    return daily_rows


def calculate_breadth_pct(close_by_ticker: dict[str, float], closes_by_ticker: dict[str, list[float]], index: int) -> float:
    supported = 0
    above = 0
    for ticker in ETF_BREADTH_UNIVERSE:
        close = close_by_ticker.get(ticker, 0.0)
        sma = rolling_average_for_index(closes_by_ticker[ticker], index, SMA_WINDOW)
        if close <= 0 or sma is None:
            continue
        supported += 1
        if close > sma:
            above += 1
    return (above / supported * 100) if supported else 0.0


def classify_regime(breadth_pct: float, spy_above_sma200: bool) -> str:
    if breadth_pct < DEFENSIVE_BREADTH_PCT:
        return "cash_protection"
    if spy_above_sma200 and breadth_pct >= RISK_ON_BREADTH_PCT:
        return "risk_on"
    if spy_above_sma200 and breadth_pct >= NEUTRAL_BREADTH_PCT:
        return "neutral"
    return "defensive"


def simulate_breadth_regime_equity(daily_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    equity = STARTING_EQUITY
    weights: dict[str, float] = {}
    current_month = ""
    turnover_count = 0
    regime_changes = 0
    previous_regime = ""
    equity_rows: list[dict[str, Any]] = []
    previous_close: dict[str, float] | None = None

    for row in daily_rows:
        date = str(row["date"])
        close = {ticker: float(value) for ticker, value in row["close"].items()}
        regime = str(row["regime"])
        if previous_close:
            daily_return = sum(weights.get(ticker, 0.0) * ((close[ticker] / previous_close[ticker]) - 1.0) for ticker in weights if ticker in close and ticker in previous_close and previous_close[ticker] > 0)
            equity *= 1.0 + daily_return

        month = date[:7]
        if month != current_month:
            current_month = month
            target_weights = target_weights_for_row(row)
            if target_weights != weights:
                turnover_count += turnover_events(weights, target_weights)
            weights = target_weights

        if previous_regime and regime != previous_regime:
            regime_changes += 1
        previous_regime = regime
        previous_close = close
        equity_rows.append(
            {
                "date": date,
                "equity": equity,
                "regime": regime,
                "breadth_pct": row["breadth_pct"],
                "exposure_pct": sum(weights.values()) * 100,
                "turnover_count": turnover_count,
                "number_of_regime_changes": regime_changes,
            }
        )
    return equity_rows


def target_weights_for_row(row: dict[str, Any]) -> dict[str, float]:
    regime = str(row["regime"])
    if regime == "cash_protection":
        return {}
    close = row["close"]
    history = row["history"]
    index = int(row["index"])
    candidates = ranked_momentum_candidates(close, history, index)
    if regime == "risk_on":
        return equal_weights(candidates[:TOP_N], 1.0)
    if regime == "neutral":
        return equal_weights(candidates[:2], 0.5)
    defensive = [ticker for ticker in ["TLT", "GLD", "XLU", "XLP"] if ticker in candidates]
    return equal_weights(defensive[:1], 0.5)


def ranked_momentum_candidates(close: dict[str, float], history: dict[str, list[float]], index: int) -> list[str]:
    candidates: list[tuple[str, float]] = []
    for ticker in ETF_BREADTH_UNIVERSE:
        ticker_close = close.get(ticker, 0.0)
        sma = rolling_average_for_index(history[ticker], index, SMA_WINDOW)
        momentum = trailing_return(history[ticker], index, MOMENTUM_LOOKBACK_DAYS)
        if ticker_close > 0 and sma is not None and ticker_close > sma and momentum is not None:
            candidates.append((ticker, momentum))
    return [ticker for ticker, _ in sorted(candidates, key=lambda item: item[1], reverse=True)]


def equal_weights(tickers: list[str], exposure: float) -> dict[str, float]:
    if not tickers:
        return {}
    weight = exposure / len(tickers)
    return {ticker: weight for ticker in tickers}


def turnover_events(old: dict[str, float], new: dict[str, float]) -> int:
    tickers = set(old) | set(new)
    return sum(1 for ticker in tickers if round(old.get(ticker, 0.0), 8) != round(new.get(ticker, 0.0), 8))


def build_result_rows(created_at: str, equity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for period, fraction in FIXED_SPLITS:
        period_rows = slice_equity_rows(equity_rows, fraction)
        rows.append(result_row(created_at, period, period_rows, equity_rows))
    return rows


def result_row(
    created_at: str,
    period: str,
    period_rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(period_rows) < 2:
        return insufficient_result_row(created_at, period, "Insufficient period rows for ETF breadth regime metrics.")
    curve = [float(row["equity"]) for row in period_rows]
    cagr = calculate_cagr_pct(curve[0], curve[-1], len(curve))
    max_drawdown = calculate_max_drawdown(curve) * 100
    sharpe = calculate_sharpe_ratio(curve)
    calmar = cagr / abs(max_drawdown) if max_drawdown else 0.0
    counts = Counter(str(row["regime"]) for row in period_rows)
    exposure = sum(float(row["exposure_pct"]) for row in period_rows) / len(period_rows)
    return {
        "created_at": created_at,
        "strategy_name": ETF_BREADTH_STRATEGY_NAME,
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "start_date": period_rows[0]["date"],
        "end_date": period_rows[-1]["date"],
        "total_return_pct": round(((curve[-1] / curve[0]) - 1.0) * 100, 4),
        "cagr_pct": round(cagr, 4),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown_pct": round(max_drawdown, 4),
        "calmar_ratio": round(calmar, 4),
        "exposure_pct": round(exposure, 4),
        "turnover_count": int(period_rows[-1]["turnover_count"]) - int(period_rows[0]["turnover_count"]),
        "number_of_regime_changes": int(period_rows[-1]["number_of_regime_changes"]) - int(period_rows[0]["number_of_regime_changes"]),
        "risk_on_pct": regime_pct(counts, "risk_on", len(period_rows)),
        "neutral_pct": regime_pct(counts, "neutral", len(period_rows)),
        "defensive_pct": regime_pct(counts, "defensive", len(period_rows)),
        "cash_protection_pct": regime_pct(counts, "cash_protection", len(period_rows)),
        "breadth_thresholds": "risk_on>=60; neutral>=40; defensive>=25; cash_protection<25",
        "allocation_rule": "risk_on top3; neutral top2 at 50pct; defensive best of TLT/GLD/XLU/XLP at 50pct; cash_protection cash",
        "cost_model_name": "no_transaction_cost_initial_breadth_research",
        "robustness_status": "research_only_pending_comparison" if period == "full_period" else "single_oos_split_initial_research",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_regime_summary_rows(created_at: str, daily_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not daily_rows:
        return [insufficient_summary_row(created_at)]
    counts = Counter(str(row["regime"]) for row in daily_rows)
    rows: list[dict[str, Any]] = []
    for regime in ["risk_on", "neutral", "defensive", "cash_protection"]:
        regime_rows = [row for row in daily_rows if row["regime"] == regime]
        rows.append(
            {
                "created_at": created_at,
                "regime": regime,
                "day_count": counts.get(regime, 0),
                "pct_of_days": regime_pct(counts, regime, len(daily_rows)),
                "average_breadth_pct": round(sum(float(row["breadth_pct"]) for row in regime_rows) / len(regime_rows), 4) if regime_rows else 0.0,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
            }
        )
    return rows


def slice_equity_rows(rows: list[dict[str, Any]], fraction: Decimal) -> list[dict[str, Any]]:
    if fraction <= 0:
        return rows
    index = int(len(rows) * float(fraction))
    index = min(max(index, 1), len(rows) - 1)
    return rows[index:]


def insufficient_result_row(created_at: str, period: str, reason: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": ETF_BREADTH_STRATEGY_NAME,
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "robustness_status": "insufficient_data",
        "allocation_rule": reason,
        "cost_model_name": "no_transaction_cost_initial_breadth_research",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def insufficient_summary_row(created_at: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "regime": "insufficient_data",
        "day_count": 0,
        "pct_of_days": 0,
        "average_breadth_pct": 0,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_summary_lines(rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]]) -> list[str]:
    full = next((row for row in rows if row.get("period") == "full_period"), {})
    oos = next((row for row in rows if row.get("period") == "split_70_30_out_of_sample"), {})
    regime_summary = ", ".join(f"{row.get('regime')}={row.get('pct_of_days')}%" for row in summary_rows if row.get("regime") != "insufficient_data")
    return [
        "ETF BREADTH REGIME BACKTEST. RESEARCH ONLY. NOT EXECUTION.",
        f"Strategy: {ETF_BREADTH_STRATEGY_NAME}",
        "Full period: " + metrics_label(full),
        "OOS 70/30: " + metrics_label(oos),
        "Time in each regime: " + (regime_summary or "not available"),
        "Comparison: monthly ETF rotation comparison is deferred until saved breadth outputs are reviewed.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
    ]


def metrics_label(row: dict[str, Any]) -> str:
    if not row or row.get("robustness_status") == "insufficient_data":
        return "insufficient_data"
    return (
        f"CAGR={row.get('cagr_pct')}%, Sharpe={row.get('sharpe_ratio')}, "
        f"max DD={row.get('max_drawdown_pct')}%, Calmar={row.get('calmar_ratio')}"
    )


def rolling_average_for_index(values: list[float], index: int, window: int) -> float | None:
    if index + 1 < window:
        return None
    subset = [value for value in values[index + 1 - window:index + 1] if value > 0]
    if len(subset) < window:
        return None
    return sum(subset) / window


def trailing_return(values: list[float], index: int, lookback: int) -> float | None:
    if index < lookback:
        return None
    current = values[index]
    previous = values[index - lookback]
    if current <= 0 or previous <= 0:
        return None
    return (current / previous) - 1.0


def regime_pct(counts: Counter[str], regime: str, total: int) -> float:
    return round((counts.get(regime, 0) / total * 100) if total else 0.0, 4)


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def build_price_history_summary(
    output_path: Path,
    rows: list[dict[str, Any]],
    tickers_saved: list[str],
    errors: list[str],
) -> list[str]:
    date_range = "not available"
    if rows:
        date_range = f"{rows[0]['date']} to {rows[-1]['date']}"
    lines = [
        "ETF BREADTH PRICE HISTORY BUILDER. RESEARCH DATA ONLY. NOT EXECUTION.",
        f"Tickers attempted: {len(ETF_BREADTH_UNIVERSE)} ({', '.join(ETF_BREADTH_UNIVERSE)})",
        f"Tickers saved: {len(tickers_saved)} ({', '.join(tickers_saved) if tickers_saved else 'none'})",
        f"Rows saved: {len(rows)}",
        f"Date range saved: {date_range}",
        f"Saved ETF breadth price history to {output_path}",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
    ]
    if errors:
        lines.append("Warnings: " + " | ".join(errors[:5]))
        if len(errors) > 5:
            lines.append(f"Additional ticker warnings omitted: {len(errors) - 5}")
    if not rows:
        lines.append("No valid rows were downloaded; wrote an empty CSV with headers only.")
    return lines
