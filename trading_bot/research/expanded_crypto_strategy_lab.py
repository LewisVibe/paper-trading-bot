"""Expanded crypto strategy lab for research-only universe testing.

The lab uses the saved crypto universe readiness report where possible, excludes
POL/MATIC until transition review, downloads daily yfinance history, writes
generated research CSVs, and never touches broker, position, trade-log,
notification, config, scheduling, or execution paths.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location


STATIC_ELIGIBLE_SYMBOLS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "BNB-USD",
    "XRP-USD",
    "ADA-USD",
    "AVAX-USD",
    "LINK-USD",
    "DOT-USD",
    "LTC-USD",
    "BCH-USD",
    "DOGE-USD",
    "TRX-USD",
    "ATOM-USD",
]
TRANSITION_BLOCKED_SYMBOLS = {"POL-USD", "MATIC-USD"}
READINESS_FILE = Path("data/crypto_universe_readiness_report.csv")

PLANNED_STRATEGY = "crypto_risk_on_momentum_persistence"
CODEX_STRATEGY = "codex_ambitious_crypto_btc_eth_core_alt_accelerator"
STRATEGIES = [PLANNED_STRATEGY, CODEX_STRATEGY]
BENCHMARKS = [
    "btc_buy_and_hold_benchmark",
    "eth_buy_and_hold_benchmark",
    "btc_eth_50_50_monthly_rebalanced_benchmark",
    "equal_weight_eligible_crypto_benchmark",
    "cash_benchmark",
]
ALL_RESULT_NAMES = [*STRATEGIES, *BENCHMARKS]
COST_BPS = [0, 10, 25, 50, 100]
SPLITS = [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]

SUMMARY_LABELS = [
    "expanded_crypto_strategy_promising",
    "expanded_crypto_strategy_high_return_high_risk",
    "expanded_crypto_strategy_cost_sensitive",
    "expanded_crypto_strategy_split_sensitive",
    "expanded_crypto_strategy_drawdown_extreme_review",
    "expanded_crypto_strategy_not_useful",
    "codex_crypto_candidate_promising",
    "codex_crypto_candidate_cost_sensitive",
    "codex_crypto_candidate_not_useful",
    "insufficient_saved_inputs",
    "manual_review_required",
]

OUTPUT_FILES = {
    "results": Path("data/expanded_crypto_strategy_lab.csv"),
    "summary": Path("data/expanded_crypto_strategy_lab_summary.csv"),
    "trades": Path("data/expanded_crypto_strategy_lab_trades.csv"),
    "equity": Path("data/expanded_crypto_strategy_lab_equity_curves.csv"),
    "costs": Path("data/expanded_crypto_strategy_lab_costs.csv"),
    "splits": Path("data/expanded_crypto_strategy_lab_splits.csv"),
}

RESULT_COLUMNS = [
    "created_at",
    "strategy_name",
    "period",
    "cost_bps",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "cash_percentage",
    "trade_count",
    "turnover",
    "average_holding_period_days",
    "cagr_decay_vs_0_bps",
    "sharpe_decay_vs_0_bps",
    "calmar_decay_vs_0_bps",
    "survives_10_bps",
    "survives_25_bps",
    "summary_label",
    "reason",
    "research_only",
    "preview_only",
    "execution_approved",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "metric_name",
    "metric_value",
    "evidence",
    "research_only",
    "preview_only",
    "execution_approved",
]

TRADE_COLUMNS = [
    "created_at",
    "strategy_name",
    "date",
    "cost_bps",
    "rebalance_reason",
    "selected_symbols",
    "turnover",
    "research_only",
    "preview_only",
    "execution_approved",
]

EQUITY_COLUMNS = [
    "created_at",
    "strategy_name",
    "date",
    "cost_bps",
    "equity",
    "cash_weight",
    "holdings",
    "research_only",
    "preview_only",
    "execution_approved",
]

SPLIT_COLUMNS = [
    *RESULT_COLUMNS,
    "split_name",
    "split_status",
]


@dataclass
class ExpandedCryptoStrategyLabResult:
    results_path: Path
    summary_path: Path
    trades_path: Path
    equity_path: Path
    costs_path: Path
    splits_path: Path
    result_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    equity_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_expanded_crypto_strategy_lab(data_dir: Path | str = "data") -> ExpandedCryptoStrategyLabResult:
    data_path = Path(data_dir)
    configure_yfinance_cache_location(data_path / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    universe, universe_note = load_eligible_universe(data_path / READINESS_FILE.name)
    price_data, errors = download_price_data(universe)
    usable_universe = [symbol for symbol in universe if symbol in price_data]
    aligned = align_price_data(price_data)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}

    if len(aligned) < 253 or len(price_data) < 2 or "BTC-USD" not in price_data or "ETH-USD" not in price_data:
        result_rows, summary_rows, trade_rows, equity_rows, cost_rows, split_rows = insufficient_rows(
            created_at, universe, universe_note, errors
        )
    else:
        result_rows, trade_rows, equity_rows = run_full_cost_lab(created_at, aligned, usable_universe, universe_note)
        cost_rows = build_cost_rows(result_rows)
        split_rows = run_split_lab(created_at, aligned, usable_universe)
        summary_rows = build_summary_rows(created_at, usable_universe, universe_note, result_rows, cost_rows, split_rows, equity_rows)

    write_rows(output_paths["results"], RESULT_COLUMNS, result_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["trades"], TRADE_COLUMNS, trade_rows)
    write_rows(output_paths["equity"], EQUITY_COLUMNS, equity_rows)
    write_rows(output_paths["costs"], RESULT_COLUMNS, cost_rows)
    write_rows(output_paths["splits"], SPLIT_COLUMNS, split_rows)
    return ExpandedCryptoStrategyLabResult(
        results_path=output_paths["results"],
        summary_path=output_paths["summary"],
        trades_path=output_paths["trades"],
        equity_path=output_paths["equity"],
        costs_path=output_paths["costs"],
        splits_path=output_paths["splits"],
        result_rows=result_rows,
        summary_rows=summary_rows,
        trade_rows=trade_rows,
        equity_rows=equity_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        summary_lines=build_summary_lines(usable_universe or universe, universe_note, result_rows, cost_rows, split_rows, equity_rows, output_paths),
    )


def show_expanded_crypto_strategy_lab_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    results = read_csv(data_path / OUTPUT_FILES["results"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    costs = read_csv(data_path / OUTPUT_FILES["costs"].name)
    splits = read_csv(data_path / OUTPUT_FILES["splits"].name)
    equity = read_csv(data_path / OUTPUT_FILES["equity"].name)
    if not results or not summary:
        return 1, ["Run `python bot.py --expanded-crypto-strategy-lab` first."]
    approvals = {str(row.get("execution_approved", "")).lower() for row in results + summary + costs + splits + equity}
    full = [row for row in results if row.get("period") == "full_period" and str(row.get("cost_bps")) == "10"]
    return 0, [
        "Expanded crypto strategy lab. Display only; execution_approved=False.",
        f"Strategies tested: {', '.join(ALL_RESULT_NAMES)}",
        f"Eligible universe used: {summary_value(summary, 'eligible_universe_used')}",
        f"Best strategy by full-period Calmar: {best_by(full, 'calmar_ratio')}",
        f"Best strategy by full-period Sharpe: {best_by(full, 'sharpe_ratio')}",
        f"Best strategy by full-period CAGR: {best_by(full, 'cagr_pct')}",
        f"Best Codex-designed strategy result: {result_line(full, CODEX_STRATEGY)}",
        f"Cost survival summary: {cost_survival_summary(costs)}",
        f"Split summary: {split_summary(splits)}",
        f"Drawdown warning summary: {summary_value(summary, 'drawdown_warning_summary')}",
        f"Rejected/not-useful rows: {summary_value(summary, 'rejected_not_useful_rows')}",
        f"execution_approved values: {', '.join(sorted(approvals)) or 'false'}",
        "Warning: expanded crypto lab does not create order instructions, approve preview promotion, or approve crypto execution.",
    ]


def load_eligible_universe(readiness_path: Path) -> tuple[list[str], str]:
    rows = read_csv(readiness_path)
    if not rows:
        return STATIC_ELIGIBLE_SYMBOLS[:], "fallback_static_crypto_universe_used"
    eligible = [
        row.get("symbol", "")
        for row in rows
        if row.get("research_universe_status") == "crypto_strategy_research_eligible"
        or str(row.get("strategy_research_eligible", "")).lower() == "true"
    ]
    eligible = [symbol for symbol in eligible if symbol and symbol not in TRANSITION_BLOCKED_SYMBOLS]
    if eligible:
        return sorted(set(eligible), key=eligible.index), "saved_crypto_universe_readiness_used"
    return STATIC_ELIGIBLE_SYMBOLS[:], "fallback_static_crypto_universe_used_no_saved_eligible_rows"


def download_price_data(symbols: list[str]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    try:
        import yfinance as yf
    except Exception as exc:  # pragma: no cover - environment dependent
        return {}, {symbol: f"yfinance import failed: {exc}" for symbol in symbols}

    price_data: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, str] = {}
    for symbol in symbols:
        try:
            data = yf.download(symbol, period="10y", interval="1d", progress=False, auto_adjust=False, threads=False)
        except Exception as exc:
            errors[symbol] = str(exc)
            continue
        rows = normalize_history(data, symbol)
        if len(rows) < 253:
            errors[symbol] = f"insufficient daily history rows={len(rows)}"
        else:
            price_data[symbol] = rows
    return price_data, errors


def normalize_history(data: Any, symbol: str) -> list[dict[str, Any]]:
    if data is None or getattr(data, "empty", True):
        return []
    rows = []
    for index, row in data.iterrows():
        close = value_from_row(row, "Close", symbol)
        if close is None or close <= 0:
            continue
        rows.append({"date": index.date().isoformat(), "symbol": symbol, "close": float(close)})
    return rows


def align_price_data(price_data: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    if not price_data:
        return []
    common_dates = set.intersection(*(set(row["date"] for row in rows) for rows in price_data.values()))
    by_symbol = {symbol: {row["date"]: row["close"] for row in rows} for symbol, rows in price_data.items()}
    aligned = []
    for date in sorted(common_dates):
        closes = {symbol: by_date[date] for symbol, by_date in by_symbol.items()}
        aligned.append({"date": date, "closes": closes})
    return aligned


def run_full_cost_lab(
    created_at: str,
    rows: list[dict[str, Any]],
    universe: list[str],
    universe_note: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    result_rows = []
    trade_rows = []
    equity_rows = []
    zero_metrics: dict[str, dict[str, Any]] = {}
    for cost_bps in COST_BPS:
        for strategy in ALL_RESULT_NAMES:
            equity, trades = simulate_named_strategy(strategy, rows, universe, cost_bps, created_at, include_trades=cost_bps == 10)
            metrics = build_metrics(created_at, strategy, "full_period", cost_bps, equity, trades, universe_note)
            if cost_bps == 0:
                zero_metrics[strategy] = metrics
            metrics = add_cost_decays(metrics, zero_metrics.get(strategy, metrics))
            result_rows.append(metrics)
            if cost_bps == 10:
                trade_rows.extend(trades)
                equity_rows.extend(equity_rows_for_csv(created_at, strategy, cost_bps, equity))
    return result_rows, trade_rows, equity_rows


def run_split_lab(created_at: str, rows: list[dict[str, Any]], universe: list[str]) -> list[dict[str, Any]]:
    split_rows = []
    for split_name, split_pct in SPLITS:
        start = int(len(rows) * split_pct)
        oos_rows = rows[start:]
        for strategy in ALL_RESULT_NAMES:
            equity, trades = simulate_named_strategy(strategy, oos_rows, universe, 10, created_at, include_trades=False)
            metrics = build_metrics(created_at, strategy, "out_of_sample", 10, equity, trades, split_name)
            status = split_status(metrics)
            split_rows.append({**metrics, "split_name": split_name, "split_status": status, "summary_label": status})
    return split_rows


def simulate_named_strategy(
    strategy: str,
    rows: list[dict[str, Any]],
    universe: list[str],
    cost_bps: int,
    created_at: str,
    *,
    include_trades: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if strategy == "cash_benchmark":
        return simulate_static_weights(strategy, rows, {}, cost_bps, created_at, include_trades)
    if strategy == "btc_buy_and_hold_benchmark":
        return simulate_static_weights(strategy, rows, {"BTC-USD": 1.0}, cost_bps, created_at, include_trades)
    if strategy == "eth_buy_and_hold_benchmark":
        return simulate_static_weights(strategy, rows, {"ETH-USD": 1.0}, cost_bps, created_at, include_trades)
    if strategy == "btc_eth_50_50_monthly_rebalanced_benchmark":
        return simulate_monthly_static(strategy, rows, {"BTC-USD": 0.5, "ETH-USD": 0.5}, cost_bps, created_at, include_trades)
    if strategy == "equal_weight_eligible_crypto_benchmark":
        weight = 1.0 / len(universe)
        return simulate_monthly_static(strategy, rows, {symbol: weight for symbol in universe}, cost_bps, created_at, include_trades)
    if strategy == PLANNED_STRATEGY:
        return simulate_risk_on_momentum_persistence(strategy, rows, universe, cost_bps, created_at, include_trades)
    if strategy == CODEX_STRATEGY:
        return simulate_codex_core_alt_accelerator(strategy, rows, universe, cost_bps, created_at, include_trades)
    raise ValueError(f"Unsupported expanded crypto strategy: {strategy}")


def simulate_static_weights(
    strategy: str,
    rows: list[dict[str, Any]],
    weights: dict[str, float],
    cost_bps: int,
    created_at: str,
    include_trades: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return simulate_weight_schedule(strategy, rows, cost_bps, created_at, include_trades, lambda _i, _w: weights)


def simulate_monthly_static(
    strategy: str,
    rows: list[dict[str, Any]],
    weights: dict[str, float],
    cost_bps: int,
    created_at: str,
    include_trades: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return simulate_weight_schedule(strategy, rows, cost_bps, created_at, include_trades, lambda _i, _w: weights, monthly_only=True)


def simulate_risk_on_momentum_persistence(
    strategy: str,
    rows: list[dict[str, Any]],
    universe: list[str],
    cost_bps: int,
    created_at: str,
    include_trades: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    current: list[str] = []

    def target(index: int, _weights: dict[str, float]) -> dict[str, float]:
        nonlocal current
        if index < 252 or not risk_on(rows, universe, index, 0.40):
            current = []
            return {}
        ranked = ranked_momentum(rows, universe, index)
        eligible = [symbol for symbol, _score in ranked if above_sma(rows, symbol, index, 200)]
        selected: list[str] = []
        for held in current:
            challenger_score = dict(ranked).get(eligible[0], -999.0) if eligible else -999.0
            held_score = dict(ranked).get(held, -999.0)
            if held in eligible[:3] and challenger_score - held_score < 0.075:
                selected.append(held)
        for symbol in eligible:
            if symbol not in selected:
                selected.append(symbol)
            if len(selected) >= 2:
                break
        current = selected[:2]
        return equal_weights(current)

    return simulate_weight_schedule(strategy, rows, cost_bps, created_at, include_trades, target, monthly_only=True)


def simulate_codex_core_alt_accelerator(
    strategy: str,
    rows: list[dict[str, Any]],
    universe: list[str],
    cost_bps: int,
    created_at: str,
    include_trades: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    alt_universe = [symbol for symbol in universe if symbol not in {"BTC-USD", "ETH-USD"}]

    def target(index: int, _weights: dict[str, float]) -> dict[str, float]:
        if index < 252 or not risk_on(rows, universe, index, 0.50):
            return {}
        core_rank = ranked_momentum(rows, ["BTC-USD", "ETH-USD"], index)
        alt_rank = ranked_momentum(rows, alt_universe, index)
        weights: dict[str, float] = {}
        if core_rank:
            weights[core_rank[0][0]] = 0.50
        if alt_rank and above_sma(rows, alt_rank[0][0], index, 200):
            weights[alt_rank[0][0]] = weights.get(alt_rank[0][0], 0.0) + 0.50
        elif len(core_rank) > 1:
            weights[core_rank[1][0]] = weights.get(core_rank[1][0], 0.0) + 0.50
        return weights

    return simulate_weight_schedule(strategy, rows, cost_bps, created_at, include_trades, target, monthly_only=True)


def simulate_weight_schedule(
    strategy: str,
    rows: list[dict[str, Any]],
    cost_bps: int,
    created_at: str,
    include_trades: bool,
    target_func,
    *,
    monthly_only: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    equity = 1.0
    weights: dict[str, float] = {}
    equity_rows = []
    trades = []
    total_turnover = 0.0
    last_month = ""
    for index, row in enumerate(rows):
        date = row["date"]
        month = date[:7]
        if index > 0:
            previous = rows[index - 1]["closes"]
            current = row["closes"]
            daily_return = sum(weight * ((current[symbol] / previous[symbol]) - 1.0) for symbol, weight in weights.items())
            equity *= 1.0 + daily_return
        should_rebalance = not monthly_only or month != last_month or index == 0
        if should_rebalance:
            new_weights = target_func(index, weights)
            turnover = sum(abs(new_weights.get(symbol, 0.0) - weights.get(symbol, 0.0)) for symbol in set(new_weights) | set(weights))
            if turnover > 0:
                equity *= 1.0 - (turnover * cost_bps / 10_000)
                total_turnover += turnover
                if include_trades:
                    trades.append(trade_row(created_at, strategy, date, cost_bps, "monthly_rebalance", new_weights, turnover))
            weights = new_weights
            last_month = month
        equity_rows.append(
            {
                "date": date,
                "equity": equity,
                "cash_weight": round(1.0 - sum(weights.values()), 6),
                "holdings": ",".join(sorted(weights)),
                "turnover": total_turnover,
            }
        )
    return equity_rows, trades


def risk_on(rows: list[dict[str, Any]], universe: list[str], index: int, breadth_threshold: float) -> bool:
    btc_ok = above_sma(rows, "BTC-USD", index, 200)
    breadth = sum(1 for symbol in universe if above_sma(rows, symbol, index, 200)) / max(1, len(universe))
    return btc_ok or breadth >= breadth_threshold


def ranked_momentum(rows: list[dict[str, Any]], symbols: list[str], index: int) -> list[tuple[str, float]]:
    scores = []
    for symbol in symbols:
        if index < 252:
            continue
        close = rows[index]["closes"][symbol]
        close_126 = rows[index - 126]["closes"][symbol]
        close_252 = rows[index - 252]["closes"][symbol]
        score = 0.5 * ((close / close_126) - 1.0) + 0.5 * ((close / close_252) - 1.0)
        scores.append((symbol, score))
    return sorted(scores, key=lambda item: item[1], reverse=True)


def above_sma(rows: list[dict[str, Any]], symbol: str, index: int, window: int) -> bool:
    if index < window:
        return False
    closes = [rows[i]["closes"][symbol] for i in range(index - window + 1, index + 1)]
    return rows[index]["closes"][symbol] > sum(closes) / len(closes)


def equal_weights(symbols: list[str]) -> dict[str, float]:
    if not symbols:
        return {}
    weight = 1.0 / len(symbols)
    return {symbol: weight for symbol in symbols}


def build_metrics(
    created_at: str,
    strategy: str,
    period: str,
    cost_bps: int,
    equity: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    values = [float(row["equity"]) for row in equity]
    days = max(1, len(values))
    cagr = cagr_pct(values[0], values[-1], days) if values else 0.0
    sharpe = sharpe_ratio(values)
    max_dd = max_drawdown_pct(values)
    calmar = cagr / abs(max_dd) if max_dd else 0.0
    cash = statistics.mean(float(row.get("cash_weight", 0.0)) for row in equity) * 100 if equity else 100.0
    turnover = equity[-1].get("turnover", 0.0) if equity else 0.0
    trade_count = len(trades)
    avg_hold = days / trade_count if trade_count else ""
    return {
        "created_at": created_at,
        "strategy_name": strategy,
        "period": period,
        "cost_bps": cost_bps,
        "cagr_pct": round(cagr, 4),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown_pct": round(max_dd, 4),
        "calmar_ratio": round(calmar, 4),
        "cash_percentage": round(cash, 4),
        "trade_count": trade_count,
        "turnover": round(float(turnover), 4),
        "average_holding_period_days": round(avg_hold, 2) if avg_hold != "" else "",
        "cagr_decay_vs_0_bps": 0.0,
        "sharpe_decay_vs_0_bps": 0.0,
        "calmar_decay_vs_0_bps": 0.0,
        "survives_10_bps": "",
        "survives_25_bps": "",
        "summary_label": "manual_review_required",
        "reason": reason,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def add_cost_decays(row: dict[str, Any], zero: dict[str, Any]) -> dict[str, Any]:
    row["cagr_decay_vs_0_bps"] = round(float(row["cagr_pct"]) - float(zero["cagr_pct"]), 4)
    row["sharpe_decay_vs_0_bps"] = round(float(row["sharpe_ratio"]) - float(zero["sharpe_ratio"]), 4)
    row["calmar_decay_vs_0_bps"] = round(float(row["calmar_ratio"]) - float(zero["calmar_ratio"]), 4)
    row["survives_10_bps"] = row["cost_bps"] == 10 and float(row["cagr_pct"]) > 0 and float(row["calmar_ratio"]) > 0
    row["survives_25_bps"] = row["cost_bps"] == 25 and float(row["cagr_pct"]) > 0 and float(row["calmar_ratio"]) > 0
    row["summary_label"] = label_result(row)
    return row


def build_cost_rows(result_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in result_rows if row.get("period") == "full_period"]


def build_summary_rows(
    created_at: str,
    universe: list[str],
    universe_note: str,
    results: list[dict[str, Any]],
    costs: list[dict[str, Any]],
    splits: list[dict[str, Any]],
    equity_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full = [row for row in results if row.get("period") == "full_period" and row.get("cost_bps") == 10]
    labels = Counter(row.get("summary_label", "") for row in full)
    return [
        summary_row(created_at, "eligible_universe_used", ", ".join(universe), universe_note),
        summary_row(created_at, "strategies_tested", ", ".join(ALL_RESULT_NAMES), "Includes planned persistence and one Codex-designed fixed-rule candidate."),
        summary_row(created_at, "best_by_cagr", best_by(full, "cagr_pct"), "Full-period 10 bps cost assumption."),
        summary_row(created_at, "best_by_sharpe", best_by(full, "sharpe_ratio"), "Full-period 10 bps cost assumption."),
        summary_row(created_at, "best_by_calmar", best_by(full, "calmar_ratio"), "Full-period 10 bps cost assumption."),
        summary_row(created_at, "cost_survival_summary", cost_survival_summary(costs), "10/25 bps survival is research context only."),
        summary_row(created_at, "split_summary", split_summary(splits), "Fixed chronological OOS split results."),
        summary_row(created_at, "drawdown_warning_summary", drawdown_warning_summary(full, equity_rows), "Drawdown warnings are research risk flags only."),
        summary_row(created_at, "rejected_not_useful_rows", str(labels.get("expanded_crypto_strategy_not_useful", 0) + labels.get("codex_crypto_candidate_not_useful", 0)), "Not-useful labels do not remove rows."),
    ]


def insufficient_rows(
    created_at: str,
    universe: list[str],
    universe_note: str,
    errors: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    reason = f"{universe_note}; insufficient_saved_inputs; " + "; ".join(f"{k}: {v}" for k, v in sorted(errors.items())[:5])
    rows = [
        {
            **empty_result(created_at, strategy, reason),
            "summary_label": "insufficient_saved_inputs",
        }
        for strategy in ALL_RESULT_NAMES
    ]
    summary = [
        summary_row(created_at, "eligible_universe_used", ", ".join(universe), universe_note),
        summary_row(created_at, "insufficient_saved_inputs", "true", reason),
    ]
    return rows, summary, [], [], rows, []


def empty_result(created_at: str, strategy: str, reason: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": strategy,
        "period": "full_period",
        "cost_bps": 10,
        "cagr_pct": "",
        "sharpe_ratio": "",
        "max_drawdown_pct": "",
        "calmar_ratio": "",
        "cash_percentage": "",
        "trade_count": "",
        "turnover": "",
        "average_holding_period_days": "",
        "cagr_decay_vs_0_bps": "",
        "sharpe_decay_vs_0_bps": "",
        "calmar_decay_vs_0_bps": "",
        "survives_10_bps": False,
        "survives_25_bps": False,
        "summary_label": "insufficient_saved_inputs",
        "reason": reason,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def label_result(row: dict[str, Any]) -> str:
    cagr = float(row.get("cagr_pct") or 0)
    calmar = float(row.get("calmar_ratio") or 0)
    max_dd = float(row.get("max_drawdown_pct") or 0)
    if row["strategy_name"] == CODEX_STRATEGY:
        if cagr > 0 and calmar > 0 and max_dd > -90:
            return "codex_crypto_candidate_promising"
        if cagr > 0:
            return "codex_crypto_candidate_cost_sensitive"
        return "codex_crypto_candidate_not_useful"
    if cagr <= 0 or calmar <= 0:
        return "expanded_crypto_strategy_not_useful"
    if max_dd < -90:
        return "expanded_crypto_strategy_drawdown_extreme_review"
    if row.get("cost_bps") in {25, 50, 100} and cagr < 5:
        return "expanded_crypto_strategy_cost_sensitive"
    if max_dd < -70:
        return "expanded_crypto_strategy_high_return_high_risk"
    return "expanded_crypto_strategy_promising"


def split_status(row: dict[str, Any]) -> str:
    if not row.get("cagr_pct"):
        return "insufficient_saved_inputs"
    if float(row["cagr_pct"]) > 0 and float(row["calmar_ratio"]) > 0:
        return "split_credible"
    return "expanded_crypto_strategy_split_sensitive"


def summary_row(created_at: str, metric_name: str, metric_value: str, evidence: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "summary_name": "expanded_crypto_strategy_lab",
        "metric_name": metric_name,
        "metric_value": metric_value,
        "evidence": evidence,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def trade_row(created_at: str, strategy: str, date: str, cost_bps: int, reason: str, weights: dict[str, float], turnover: float) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": strategy,
        "date": date,
        "cost_bps": cost_bps,
        "rebalance_reason": reason,
        "selected_symbols": ",".join(sorted(weights)),
        "turnover": round(turnover, 4),
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def equity_rows_for_csv(created_at: str, strategy: str, cost_bps: int, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "strategy_name": strategy,
            "date": row["date"],
            "cost_bps": cost_bps,
            "equity": round(float(row["equity"]), 6),
            "cash_weight": row.get("cash_weight", ""),
            "holdings": row.get("holdings", ""),
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
        }
        for row in rows
    ]


def build_summary_lines(
    universe: list[str],
    universe_note: str,
    results: list[dict[str, Any]],
    costs: list[dict[str, Any]],
    splits: list[dict[str, Any]],
    equity_rows: list[dict[str, Any]],
    paths: dict[str, Path],
) -> list[str]:
    full = [row for row in results if row.get("period") == "full_period" and row.get("cost_bps") == 10]
    return [
        "Expanded crypto strategy lab complete. Research/report only; execution_approved=False.",
        f"Eligible universe used: {', '.join(universe)} ({universe_note})",
        f"Strategies tested: {', '.join(ALL_RESULT_NAMES)}",
        f"Best by CAGR: {best_by(full, 'cagr_pct')}",
        f"Best by Sharpe: {best_by(full, 'sharpe_ratio')}",
        f"Best by Calmar: {best_by(full, 'calmar_ratio')}",
        f"Codex-designed strategy: {CODEX_STRATEGY}; selected to test BTC/ETH core plus a concentrated altcoin accelerator sleeve under a breadth/trend gate.",
        f"Cost survival: {cost_survival_summary(costs)}",
        f"Split results: {split_summary(splits)}",
        f"Drawdown warnings: {drawdown_warning_summary(full, equity_rows)}",
        f"Saved results to {paths['results']}",
        f"Saved summary to {paths['summary']}",
        f"Saved trades to {paths['trades']}",
        f"Saved equity curves to {paths['equity']}",
        f"Saved costs to {paths['costs']}",
        f"Saved splits to {paths['splits']}",
        "Warning: expanded crypto lab does not approve crypto execution, paper execution, scheduling, or strategy-to-execution wiring.",
    ]


def best_by(rows: list[dict[str, Any]], field: str) -> str:
    candidates = [row for row in rows if row.get(field) not in {"", None}]
    if not candidates:
        return "unavailable"
    best = max(candidates, key=lambda row: float(row[field]))
    return f"{best['strategy_name']}={best[field]}"


def summary_value(rows: list[dict[str, Any]], metric_name: str) -> str:
    row = next((item for item in rows if item.get("metric_name") == metric_name), {})
    return str(row.get("metric_value", "unavailable"))


def result_line(rows: list[dict[str, Any]], strategy: str) -> str:
    row = next((item for item in rows if item.get("strategy_name") == strategy), None)
    if not row:
        return "unavailable"
    return f"CAGR={row.get('cagr_pct')}; Sharpe={row.get('sharpe_ratio')}; Calmar={row.get('calmar_ratio')}; MaxDD={row.get('max_drawdown_pct')}; label={row.get('summary_label')}"


def cost_survival_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "unavailable"
    parts = []
    for strategy in STRATEGIES:
        ten = next((row for row in rows if row.get("strategy_name") == strategy and str(row.get("cost_bps")) == "10"), {})
        twenty_five = next((row for row in rows if row.get("strategy_name") == strategy and str(row.get("cost_bps")) == "25"), {})
        parts.append(f"{strategy}:10={ten.get('survives_10_bps', False)},25={twenty_five.get('survives_25_bps', False)}")
    return "; ".join(parts)


def split_summary(rows: list[dict[str, Any]]) -> str:
    counts = Counter(row.get("split_status", "") for row in rows)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


def drawdown_warning_summary(full_rows: list[dict[str, Any]], equity_rows: list[dict[str, Any]]) -> str:
    warnings = [row["strategy_name"] for row in full_rows if row.get("max_drawdown_pct") not in {"", None} and float(row["max_drawdown_pct"]) < -80]
    return ", ".join(warnings) or "none"


def cagr_pct(start: float, end: float, days: int) -> float:
    years = days / 365
    if start <= 0 or end <= 0 or years <= 0:
        return 0.0
    return ((end / start) ** (1 / years) - 1) * 100


def sharpe_ratio(values: list[float]) -> float:
    returns = [(values[i] / values[i - 1]) - 1 for i in range(1, len(values)) if values[i - 1] > 0]
    if len(returns) < 2:
        return 0.0
    mean = statistics.mean(returns)
    stdev = statistics.stdev(returns)
    return (mean / stdev) * math.sqrt(365) if stdev else 0.0


def max_drawdown_pct(values: list[float]) -> float:
    peak = values[0] if values else 0.0
    worst = 0.0
    for value in values:
        if value > peak:
            peak = value
        if peak > 0:
            worst = min(worst, (value / peak) - 1.0)
    return worst * 100


def value_from_row(row: Any, column_name: str, symbol: str) -> float | None:
    for key in (column_name, (column_name, symbol), (symbol, column_name)):
        try:
            value = row[key]
        except Exception:
            continue
        try:
            if hasattr(value, "iloc"):
                value = value.iloc[0]
            return float(value)
        except (TypeError, ValueError):
            return None
    return None


def read_csv(path: Path) -> list[dict[str, Any]]:
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
            writer.writerow(row)
