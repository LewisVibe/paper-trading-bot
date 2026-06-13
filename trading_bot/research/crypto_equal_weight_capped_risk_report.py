"""Research-only crypto capped/equal-risk contribution report.

This module tests fixed capped and volatility-aware crypto allocation variants
around the high-drawdown equal-weight benchmark. It writes generated research
CSVs only and does not touch broker, position, database, alert, config,
scheduling, or execution paths.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location
from trading_bot.research.expanded_crypto_robustness_report import (
    simulate_variable_equal_weight,
    variable_universe_rows,
)
from trading_bot.research.expanded_crypto_strategy_lab import (
    CODEX_STRATEGY,
    PLANNED_STRATEGY,
    TRANSITION_BLOCKED_SYMBOLS,
    above_sma,
    align_price_data,
    build_metrics,
    download_price_data,
    load_eligible_universe,
    simulate_named_strategy,
    simulate_weight_schedule,
)
from trading_bot.research.crypto_equal_weight_volatility_scaling import (
    drawdown_window,
    extract_metric,
    lowest_drawdown,
    overlap_drawdown,
    reduction_text,
    status_counts,
    window_text,
)


READINESS_FILE = Path("data/crypto_universe_readiness_report.csv")
TOP_CONTRIBUTOR_PAIR = ["BNB-USD", "TRX-USD"]
CAPPED_RISK_VARIANTS = [
    "crypto_equal_weight_cap_10pct",
    "crypto_equal_weight_cap_15pct",
    "crypto_equal_weight_ex_highest_vol_2",
    "crypto_equal_weight_ex_top_contributor_pair",
    "crypto_inverse_volatility_weighted",
    "crypto_equal_risk_contribution_proxy",
]
BENCHMARKS = [
    "equal_weight_eligible_crypto_benchmark",
    "equal_weight_inception_aware",
    "crypto_risk_on_momentum_persistence",
    "codex_ambitious_crypto_btc_eth_core_alt_accelerator",
    "btc_buy_and_hold_benchmark",
    "eth_buy_and_hold_benchmark",
    "btc_eth_50_50_monthly_rebalanced_benchmark",
    "cash_benchmark",
]
ALL_NAMES = [*CAPPED_RISK_VARIANTS, *BENCHMARKS]
TRANSITION_BLOCKED_CONTRACT = ["POL-USD", "MATIC-USD"]
COST_BPS = [0, 10, 25, 50, 100]
SPLITS = [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]

SUMMARY_LABELS = [
    "crypto_capped_risk_promising",
    "crypto_capped_risk_concentration_improved",
    "crypto_capped_risk_drawdown_improved",
    "crypto_capped_risk_return_drag_too_high",
    "crypto_capped_risk_cost_sensitive",
    "crypto_capped_risk_split_sensitive",
    "crypto_capped_risk_not_useful",
    "equal_weight_still_best_high_drawdown",
    "equal_weight_outlier_dependence_reduced",
    "insufficient_saved_inputs",
    "manual_review_required",
]

OUTPUT_FILES = {
    "results": Path("data/crypto_equal_weight_capped_risk_report.csv"),
    "summary": Path("data/crypto_equal_weight_capped_risk_summary.csv"),
    "trades": Path("data/crypto_equal_weight_capped_risk_trades.csv"),
    "equity": Path("data/crypto_equal_weight_capped_risk_equity_curves.csv"),
    "costs": Path("data/crypto_equal_weight_capped_risk_costs.csv"),
    "splits": Path("data/crypto_equal_weight_capped_risk_splits.csv"),
    "drawdowns": Path("data/crypto_equal_weight_capped_risk_drawdowns.csv"),
    "contributions": Path("data/crypto_equal_weight_capped_risk_contributions.csv"),
}

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "section",
    "strategy_name",
    "period",
    "cost_bps",
    "metric_name",
    "metric_value",
    "reference_value",
    "status",
    "summary_label",
    "evidence",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoEqualWeightCappedRiskResult:
    results_path: Path
    summary_path: Path
    trades_path: Path
    equity_path: Path
    costs_path: Path
    splits_path: Path
    drawdowns_path: Path
    contributions_path: Path
    result_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    equity_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    contribution_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_equal_weight_capped_risk_report(data_dir: Path | str = "data") -> CryptoEqualWeightCappedRiskResult:
    data_path = Path(data_dir)
    configure_yfinance_cache_location(data_path / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    universe, universe_note = load_eligible_universe(data_path / READINESS_FILE.name)
    universe = [symbol for symbol in universe if symbol not in TRANSITION_BLOCKED_SYMBOLS]
    price_data, errors = download_price_data(universe)
    usable_universe = [symbol for symbol in universe if symbol in price_data]
    aligned = align_price_data(price_data)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}

    if len(aligned) < 253 or "BTC-USD" not in price_data or "ETH-USD" not in price_data:
        result_rows, summary_rows, trade_rows, equity_rows, cost_rows, split_rows, drawdown_rows, contribution_rows = insufficient_rows(
            created_at, universe, universe_note, errors
        )
    else:
        result_rows, trade_rows, equity_rows, raw_equity = run_cost_lab(created_at, aligned, price_data, usable_universe, universe_note)
        cost_rows = [row for row in result_rows if row.get("section") == "cost_stress"]
        split_rows = run_split_checks(created_at, aligned, price_data, usable_universe)
        drawdown_rows = build_drawdown_rows(created_at, result_rows, equity_rows)
        contribution_rows = build_contribution_rows(created_at, raw_equity, price_data, usable_universe)
        summary_rows = build_summary_rows(created_at, result_rows, cost_rows, split_rows, drawdown_rows, contribution_rows)

    write_rows(output_paths["results"], result_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["trades"], trade_rows)
    write_rows(output_paths["equity"], equity_rows)
    write_rows(output_paths["costs"], cost_rows)
    write_rows(output_paths["splits"], split_rows)
    write_rows(output_paths["drawdowns"], drawdown_rows)
    write_rows(output_paths["contributions"], contribution_rows)
    return CryptoEqualWeightCappedRiskResult(
        results_path=output_paths["results"],
        summary_path=output_paths["summary"],
        trades_path=output_paths["trades"],
        equity_path=output_paths["equity"],
        costs_path=output_paths["costs"],
        splits_path=output_paths["splits"],
        drawdowns_path=output_paths["drawdowns"],
        contributions_path=output_paths["contributions"],
        result_rows=result_rows,
        summary_rows=summary_rows,
        trade_rows=trade_rows,
        equity_rows=equity_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        drawdown_rows=drawdown_rows,
        contribution_rows=contribution_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_crypto_equal_weight_capped_risk_report_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    results = read_csv(data_path / OUTPUT_FILES["results"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    costs = read_csv(data_path / OUTPUT_FILES["costs"].name)
    splits = read_csv(data_path / OUTPUT_FILES["splits"].name)
    drawdowns = read_csv(data_path / OUTPUT_FILES["drawdowns"].name)
    contributions = read_csv(data_path / OUTPUT_FILES["contributions"].name)
    if not results or not summary:
        return 1, ["Run `python bot.py --crypto-equal-weight-capped-risk-report` first."]
    approvals = {str(row.get("execution_approved", "")).lower() for row in results + summary + costs + splits + drawdowns + contributions}
    return 0, [
        "Crypto equal-weight capped-risk report. Display only; execution_approved=False.",
        f"Variants tested: {summary_value(summary, 'variants_tested')}",
        f"Best by CAGR: {summary_value(summary, 'best_by_cagr')}",
        f"Best by Sharpe: {summary_value(summary, 'best_by_sharpe')}",
        f"Best by Calmar: {summary_value(summary, 'best_by_calmar')}",
        f"Lowest max drawdown: {summary_value(summary, 'lowest_max_drawdown')}",
        f"Static equal-weight comparison: {summary_value(summary, 'static_equal_weight_result')}",
        f"Best capped-risk variant: {summary_value(summary, 'best_capped_risk_variant')}",
        f"Concentration/top-contributor summary: {summary_value(summary, 'concentration_top_contributor_summary')}",
        f"Drawdown reduction versus equal-weight: {summary_value(summary, 'drawdown_reduction_vs_equal_weight')}",
        f"Return drag versus equal-weight: {summary_value(summary, 'return_drag_vs_equal_weight')}",
        f"Calmar improvement versus equal-weight: {summary_value(summary, 'calmar_improvement_vs_equal_weight')}",
        f"Cost survival summary: {status_counts(costs)}",
        f"Split summary: {status_counts(splits)}",
        f"Final summary label: {summary_value(summary, 'final_summary_label')}",
        f"execution_approved values: {', '.join(sorted(approvals)) or 'false'}",
        "Warning: capped-risk report does not create order instructions, approve preview promotion, or approve crypto execution.",
    ]


def run_cost_lab(
    created_at: str,
    aligned: list[dict[str, Any]],
    price_data: dict[str, list[dict[str, Any]]],
    universe: list[str],
    universe_note: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    result_rows = []
    trade_rows = []
    equity_rows = []
    raw_equity: dict[str, list[dict[str, Any]]] = {}
    zero_rows: dict[str, dict[str, Any]] = {}
    for cost_bps in COST_BPS:
        for name in ALL_NAMES:
            equity, trades = simulate_name(name, aligned, price_data, universe, cost_bps, created_at, include_trades=cost_bps == 10)
            metric = build_metrics(created_at, name, "full_period", cost_bps, equity, trades, universe_note)
            if cost_bps == 0:
                zero_rows[name] = metric
            metric = add_decays(metric, zero_rows.get(name, metric))
            result_rows.append(to_common(created_at, "cost_stress", metric, label_metric(metric)))
            if cost_bps == 10:
                raw_equity[name] = equity
                trade_rows.extend(to_trade_rows(created_at, name, trades))
                equity_rows.extend(to_equity_rows(created_at, name, cost_bps, equity))
    return result_rows, trade_rows, equity_rows, raw_equity


def run_split_checks(created_at: str, aligned: list[dict[str, Any]], price_data: dict[str, list[dict[str, Any]]], universe: list[str]) -> list[dict[str, Any]]:
    rows = []
    for split_name, split_pct in SPLITS:
        start = int(len(aligned) * split_pct)
        split_rows = aligned[start:]
        for name in ALL_NAMES:
            equity, trades = simulate_name(name, split_rows, price_data, universe, 10, created_at, include_trades=False)
            metric = add_decays(build_metrics(created_at, name, "out_of_sample", 10, equity, trades, split_name), build_metrics(created_at, name, "out_of_sample", 10, equity, trades, split_name))
            status = "split_credible" if float(metric.get("cagr_pct") or 0) > 0 and float(metric.get("calmar_ratio") or 0) > 0 else "crypto_capped_risk_split_sensitive"
            rows.append(to_common(created_at, "split_validation", metric, status, split_name))
    return rows


def simulate_name(name: str, aligned: list[dict[str, Any]], price_data: dict[str, list[dict[str, Any]]], universe: list[str], cost_bps: int, created_at: str, *, include_trades: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if name == "equal_weight_inception_aware":
        rows = variable_universe_rows(price_data, universe)
        if aligned:
            rows = [row for row in rows if row.get("date", "") >= aligned[0]["date"]]
        return simulate_variable_equal_weight(name, rows, cost_bps, created_at)
    if name in {
        "equal_weight_eligible_crypto_benchmark",
        PLANNED_STRATEGY,
        CODEX_STRATEGY,
        "btc_buy_and_hold_benchmark",
        "eth_buy_and_hold_benchmark",
        "btc_eth_50_50_monthly_rebalanced_benchmark",
        "cash_benchmark",
    }:
        return simulate_named_strategy(name, aligned, universe, cost_bps, created_at, include_trades=include_trades)
    if name == "crypto_equal_weight_cap_10pct":
        return simulate_monthly_target(name, aligned, cost_bps, created_at, include_trades, lambda index: capped_equal_weights(universe, 0.10))
    if name == "crypto_equal_weight_cap_15pct":
        return simulate_monthly_target(name, aligned, cost_bps, created_at, include_trades, lambda index: capped_equal_weights(universe, 0.15))
    if name == "crypto_equal_weight_ex_highest_vol_2":
        return simulate_monthly_target(name, aligned, cost_bps, created_at, include_trades, lambda index: equal_weight_ex_highest_vol(aligned, universe, index, 2))
    if name == "crypto_equal_weight_ex_top_contributor_pair":
        return simulate_monthly_target(name, aligned, cost_bps, created_at, include_trades, lambda index: equal_weights_without(universe, TOP_CONTRIBUTOR_PAIR))
    if name == "crypto_inverse_volatility_weighted":
        return simulate_monthly_target(name, aligned, cost_bps, created_at, include_trades, lambda index: inverse_vol_weights(aligned, universe, index, 63, 0.20))
    if name == "crypto_equal_risk_contribution_proxy":
        return simulate_monthly_target(name, aligned, cost_bps, created_at, include_trades, lambda index: equal_risk_proxy_weights(aligned, universe, index))
    raise ValueError(f"Unsupported crypto capped-risk variant: {name}")


def simulate_monthly_target(name: str, rows: list[dict[str, Any]], cost_bps: int, created_at: str, include_trades: bool, target_builder):
    return simulate_weight_schedule(name, rows, cost_bps, created_at, include_trades, lambda index, _weights: target_builder(index), monthly_only=True)


def capped_equal_weights(symbols: list[str], cap: float) -> dict[str, float]:
    if not symbols:
        return {}
    if len(symbols) * cap < 1.0:
        return {symbol: 1.0 / len(symbols) for symbol in symbols}
    weights = {symbol: 1.0 / len(symbols) for symbol in symbols}
    for _ in range(len(symbols)):
        excess = sum(max(0.0, weight - cap) for weight in weights.values())
        weights = {symbol: min(weight, cap) for symbol, weight in weights.items()}
        uncapped = [symbol for symbol, weight in weights.items() if weight < cap - 1e-12]
        if not excess or not uncapped:
            break
        add = excess / len(uncapped)
        for symbol in uncapped:
            weights[symbol] += add
    total = sum(weights.values())
    return {symbol: weight / total for symbol, weight in weights.items()} if total else {}


def equal_weights_without(symbols: list[str], excluded: list[str]) -> dict[str, float]:
    selected = [symbol for symbol in symbols if symbol not in excluded]
    return {symbol: 1.0 / len(selected) for symbol in selected} if selected else {}


def equal_weight_ex_highest_vol(rows: list[dict[str, Any]], universe: list[str], index: int, count: int) -> dict[str, float]:
    if index < 252:
        selected = universe
    else:
        vols = sorted(((trailing_vol(rows, symbol, index, 252), symbol) for symbol in universe), reverse=True)
        excluded = {symbol for _vol, symbol in vols[:count]}
        selected = [symbol for symbol in universe if symbol not in excluded]
    return {symbol: 1.0 / len(selected) for symbol in selected} if selected else {}


def inverse_vol_weights(rows: list[dict[str, Any]], universe: list[str], index: int, window: int, cap: float) -> dict[str, float]:
    if index < window:
        return {}
    scores = {symbol: 1.0 / max(trailing_vol(rows, symbol, index, window), 1e-9) for symbol in universe}
    return cap_and_normalize(scores, cap)


def equal_risk_proxy_weights(rows: list[dict[str, Any]], universe: list[str], index: int) -> dict[str, float]:
    if index < 63:
        return {}
    btc_ok = index >= 200 and above_sma(rows, "BTC-USD", index, 200)
    scores = {}
    for symbol in universe:
        score = 1.0 / max(trailing_vol(rows, symbol, index, 63), 1e-9)
        if index >= 200 and not (above_sma(rows, symbol, index, 200) or btc_ok):
            score *= 0.5
        scores[symbol] = score
    return cap_and_normalize(scores, 0.15)


def trailing_vol(rows: list[dict[str, Any]], symbol: str, index: int, window: int) -> float:
    returns = []
    for pos in range(index - window + 1, index + 1):
        prev = rows[pos - 1]["closes"][symbol]
        cur = rows[pos]["closes"][symbol]
        returns.append((cur / prev) - 1.0)
    return statistics.pstdev(returns) * math.sqrt(365) if len(returns) > 1 else 0.0


def cap_and_normalize(scores: dict[str, float], cap: float) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        return {}
    weights = {symbol: score / total for symbol, score in scores.items()}
    for _ in range(len(weights)):
        excess = sum(max(0.0, weight - cap) for weight in weights.values())
        weights = {symbol: min(weight, cap) for symbol, weight in weights.items()}
        uncapped = [symbol for symbol, weight in weights.items() if weight < cap - 1e-12]
        if not excess or not uncapped:
            break
        for symbol in uncapped:
            weights[symbol] += excess / len(uncapped)
    total = sum(weights.values())
    return {symbol: weight / total for symbol, weight in weights.items()} if total else {}


def build_contribution_rows(created_at: str, raw_equity: dict[str, list[dict[str, Any]]], price_data: dict[str, list[dict[str, Any]]], universe: list[str]) -> list[dict[str, Any]]:
    rows = []
    price_maps = {symbol: {row["date"]: float(row["close"]) for row in price_data.get(symbol, [])} for symbol in universe}
    for strategy, equity in raw_equity.items():
        avg_weights: dict[str, list[float]] = defaultdict(list)
        ending_weights: dict[str, float] = {}
        for row in equity:
            holdings = [symbol for symbol in str(row.get("holdings", "")).split(",") if symbol]
            exposure = 1.0 - float(row.get("cash_weight", 0.0) or 0.0)
            weight = exposure / len(holdings) if holdings else 0.0
            for symbol in holdings:
                avg_weights[symbol].append(weight)
                ending_weights[symbol] = weight
        contributions = {}
        for symbol, weights in avg_weights.items():
            prices = price_maps.get(symbol, {})
            first = prices.get(equity[0]["date"])
            last = prices.get(equity[-1]["date"])
            contribution = (statistics.mean(weights) * ((last / first) - 1.0) * 100) if first and last and first > 0 else 0.0
            contributions[symbol] = round(contribution, 4)
        top = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
        top_two = top[:2]
        positive_total = sum(max(0.0, value) for value in contributions.values())
        top_two_share = sum(max(0.0, value) for _symbol, value in top_two) / positive_total if positive_total else 0.0
        average_weight_by_asset = {symbol: round(statistics.mean(weights) * 100, 4) for symbol, weights in avg_weights.items()}
        herfindahl = round(sum((value / 100) ** 2 for value in average_weight_by_asset.values()), 6)
        max_avg = max(average_weight_by_asset.values(), default=0.0)
        rows.append(
            common_row(
                created_at,
                "contribution_diagnostics",
                strategy,
                "asset_contribution",
                f"top_contributor={top[0][0] if top else 'unavailable'}; top_2={','.join(symbol for symbol, _value in top_two) or 'unavailable'}; herfindahl={herfindahl}; max_single_asset_average_weight={max_avg}; top_two_positive_contribution_share={round(top_two_share * 100, 4)}",
                "approximate contribution from average held weights and asset total return",
                "top_contributor_dependent" if top_two_share > 0.60 else "concentration_review_available",
                "equal_weight_outlier_dependence_reduced" if strategy == "crypto_equal_weight_ex_top_contributor_pair" else "manual_review_required",
            f"ending_weight_by_asset={ending_weights}; average_weight_by_asset={average_weight_by_asset}; approximate_contribution_by_asset={contributions}; Herfindahl concentration score={herfindahl}; top_contributor_dependent={top_two_share > 0.60}",
            )
        )
    return rows


def build_drawdown_rows(created_at: str, result_rows: list[dict[str, Any]], equity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    equity_by_name = {name: sorted([row for row in equity_rows if row.get("strategy_name") == name and str(row.get("cost_bps")) == "10"], key=lambda row: row.get("period", "")) for name in ALL_NAMES}
    static = metric_for(result_rows, "equal_weight_eligible_crypto_benchmark")
    btc = metric_for(result_rows, "btc_buy_and_hold_benchmark")
    rows = []
    for name in ALL_NAMES:
        metric = metric_for(result_rows, name)
        window = drawdown_window(equity_by_name.get(name, []))
        dd = window.get("max_drawdown_pct") if window else extract_metric(metric.get("metric_value", ""), "MaxDD")
        cagr = extract_metric(metric.get("metric_value", ""), "CAGR")
        calmar = extract_metric(metric.get("metric_value", ""), "Calmar")
        static_dd = overlap_drawdown(equity_by_name.get("equal_weight_eligible_crypto_benchmark", []), window)
        btc_dd = overlap_drawdown(equity_by_name.get("btc_buy_and_hold_benchmark", []), window)
        static_full_dd = extract_metric(static.get("metric_value", ""), "MaxDD")
        static_cagr = extract_metric(static.get("metric_value", ""), "CAGR")
        static_calmar = extract_metric(static.get("metric_value", ""), "Calmar")
        evidence = (
            f"start={window_text(window, 'start_date')}; trough={window_text(window, 'trough_date')}; "
            f"recovery={window_text(window, 'recovery_date')}; recovery_rows={window_text(window, 'recovery_rows')}; "
            f"drawdown_reduction_vs_equal_weight_same_window={reduction_text(dd, static_dd)}; "
            f"drawdown_reduction_vs_btc_same_window={reduction_text(dd, btc_dd)}; "
            "drawdown_reduction_vs_best_volatility_scaling_variant=unavailable_in_standalone_report; "
            f"return_drag_vs_equal_weight={round(cagr - static_cagr, 4)}; calmar_improvement_vs_equal_weight={round(calmar - static_calmar, 4)}."
        )
        rows.append(common_row(created_at, "drawdown_review", name, "worst_drawdown_window", f"MaxDD={round(float(dd or 0), 4)}; start={window_text(window, 'start_date')}; trough={window_text(window, 'trough_date')}; recovery={window_text(window, 'recovery_date')}", "same-window overlap where available", "drawdown_review_available" if window else "drawdown_review_unavailable", label_drawdown(float(dd or 0), static_full_dd, cagr - static_cagr, calmar - static_calmar), evidence))
    return rows


def build_summary_rows(created_at: str, results: list[dict[str, Any]], costs: list[dict[str, Any]], splits: list[dict[str, Any]], drawdowns: list[dict[str, Any]], contributions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    full = [row for row in results if row.get("section") == "cost_stress" and str(row.get("cost_bps")) == "10"]
    static = metric_for(full, "equal_weight_eligible_crypto_benchmark")
    best = best_capped_risk(full)
    static_cagr = extract_metric(static.get("metric_value", ""), "CAGR")
    static_dd = extract_metric(static.get("metric_value", ""), "MaxDD")
    static_calmar = extract_metric(static.get("metric_value", ""), "Calmar")
    best_cagr = extract_metric(best.get("metric_value", ""), "CAGR")
    best_dd = extract_metric(best.get("metric_value", ""), "MaxDD")
    best_calmar = extract_metric(best.get("metric_value", ""), "Calmar")
    label = final_label(static, best, contributions)
    return [
        common_row(created_at, "summary", "variants_tested", "variants", ", ".join(CAPPED_RISK_VARIANTS), "", "manual_review_required", label, "Fixed capped/equal-risk variants only; no parameter search."),
        common_row(created_at, "summary", "best_by_cagr", "expanded_crypto", best_by(full, "CAGR"), "", "manual_review_required", label, "Full-period 10 bps comparison."),
        common_row(created_at, "summary", "best_by_sharpe", "expanded_crypto", best_by(full, "Sharpe"), "", "manual_review_required", label, "Full-period 10 bps comparison."),
        common_row(created_at, "summary", "best_by_calmar", "expanded_crypto", best_by(full, "Calmar"), "", "manual_review_required", label, "Full-period 10 bps comparison."),
        common_row(created_at, "summary", "lowest_max_drawdown", "expanded_crypto", lowest_drawdown(full), "", "manual_review_required", label, "Full-period 10 bps comparison."),
        common_row(created_at, "summary", "static_equal_weight_result", "equal_weight_eligible_crypto_benchmark", static.get("metric_value", "unavailable"), "", "manual_review_required", label, "Static equal-weight is high-return/high-drawdown benchmark."),
        common_row(created_at, "summary", "best_capped_risk_variant", best.get("strategy_name", "unavailable"), best.get("metric_value", "unavailable"), "", "manual_review_required", label, "Best capped-risk variant by Calmar."),
        common_row(created_at, "summary", "concentration_top_contributor_summary", "expanded_crypto", status_counts(contributions), "", "manual_review_required", label, "Contribution and concentration status counts."),
        common_row(created_at, "summary", "drawdown_reduction_vs_equal_weight", best.get("strategy_name", "unavailable"), round(best_dd - static_dd, 4), "", "manual_review_required", label, "Positive means max drawdown is less severe than static equal-weight."),
        common_row(created_at, "summary", "return_drag_vs_equal_weight", best.get("strategy_name", "unavailable"), round(best_cagr - static_cagr, 4), "", "manual_review_required", label, "Negative means lower CAGR than static equal-weight."),
        common_row(created_at, "summary", "calmar_improvement_vs_equal_weight", best.get("strategy_name", "unavailable"), round(best_calmar - static_calmar, 4), "", "manual_review_required", label, "Positive means Calmar improved versus static equal-weight."),
        common_row(created_at, "summary", "cost_survival_summary", "expanded_crypto", status_counts(costs), "", "manual_review_required", label, "Cost-stress status counts."),
        common_row(created_at, "summary", "split_summary", "expanded_crypto", status_counts(splits), "", "manual_review_required", label, "Split status counts."),
        common_row(created_at, "summary", "final_summary_label", "crypto_equal_weight_capped_risk_report", label, "", label, label, "Final label is research-only and does not approve execution."),
    ]


def insufficient_rows(created_at: str, universe: list[str], universe_note: str, errors: dict[str, str]):
    evidence = f"fallback_static_crypto_universe_used={universe_note.startswith('fallback')}; universe={','.join(universe)}; " + "; ".join(f"{key}:{value}" for key, value in sorted(errors.items())[:5])
    row = common_row(created_at, "summary", "insufficient_saved_inputs", "input_status", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence)
    summary = [common_row(created_at, "summary", key, "summary", value, "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence) for key, value in [
        ("variants_tested", ", ".join(CAPPED_RISK_VARIANTS)),
        ("best_by_cagr", "unavailable"),
        ("best_by_sharpe", "unavailable"),
        ("best_by_calmar", "unavailable"),
        ("lowest_max_drawdown", "unavailable"),
        ("static_equal_weight_result", "unavailable"),
        ("best_capped_risk_variant", "unavailable"),
        ("concentration_top_contributor_summary", "insufficient_saved_inputs"),
        ("drawdown_reduction_vs_equal_weight", "unavailable"),
        ("return_drag_vs_equal_weight", "unavailable"),
        ("calmar_improvement_vs_equal_weight", "unavailable"),
        ("cost_survival_summary", "insufficient_saved_inputs"),
        ("split_summary", "insufficient_saved_inputs"),
        ("final_summary_label", "insufficient_saved_inputs"),
    ]]
    return [row], summary, [], [], [row], [row], [row], [row]


def add_decays(metric: dict[str, Any], zero: dict[str, Any]) -> dict[str, Any]:
    metric["cagr_decay_vs_0_bps"] = round(float(metric["cagr_pct"]) - float(zero["cagr_pct"]), 4)
    metric["sharpe_decay_vs_0_bps"] = round(float(metric["sharpe_ratio"]) - float(zero["sharpe_ratio"]), 4)
    metric["calmar_decay_vs_0_bps"] = round(float(metric["calmar_ratio"]) - float(zero["calmar_ratio"]), 4)
    metric["survives_10_bps"] = metric["cost_bps"] == 10 and float(metric["cagr_pct"]) > 0 and float(metric["calmar_ratio"]) > 0
    metric["survives_25_bps"] = metric["cost_bps"] == 25 and float(metric["cagr_pct"]) > 0 and float(metric["calmar_ratio"]) > 0
    metric["average_exposure_pct"] = round(100 - float(metric.get("cash_percentage") or 100), 4)
    return metric


def to_common(created_at: str, section: str, metric: dict[str, Any], label: str, period: str | None = None) -> dict[str, Any]:
    metric_value = (
        f"CAGR={metric.get('cagr_pct', '')}; Sharpe={metric.get('sharpe_ratio', '')}; Calmar={metric.get('calmar_ratio', '')}; "
        f"MaxDD={metric.get('max_drawdown_pct', '')}; cash={metric.get('cash_percentage', '')}; avg_exposure={metric.get('average_exposure_pct', '')}; "
        f"trades={metric.get('trade_count', '')}; turnover={metric.get('turnover', '')}; avg_hold_days={metric.get('average_holding_period_days', '')}"
    )
    evidence = f"cost_bps={metric.get('cost_bps', '')}; cagr_decay={metric.get('cagr_decay_vs_0_bps', '')}; sharpe_decay={metric.get('sharpe_decay_vs_0_bps', '')}; calmar_decay={metric.get('calmar_decay_vs_0_bps', '')}; survives_10_bps={metric.get('survives_10_bps', '')}; survives_25_bps={metric.get('survives_25_bps', '')}; {metric.get('reason', '')}"
    return common_row(created_at, section, metric.get("strategy_name", ""), "metrics", metric_value, f"cost_bps={metric.get('cost_bps', '')}", label, label, evidence, period=period or metric.get("period", "full_period"), cost_bps=metric.get("cost_bps", ""))


def common_row(created_at: str, section: str, strategy_name: str, metric_name: str, metric_value: Any, reference_value: Any, status: str, summary_label: str, evidence: str, *, period: str = "", cost_bps: Any = "") -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "crypto_equal_weight_capped_risk_report",
        "section": section,
        "strategy_name": strategy_name,
        "period": period,
        "cost_bps": cost_bps,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "reference_value": reference_value,
        "status": status,
        "summary_label": summary_label,
        "evidence": evidence,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def label_metric(metric: dict[str, Any]) -> str:
    cagr = float(metric.get("cagr_pct") or 0)
    calmar = float(metric.get("calmar_ratio") or 0)
    maxdd = float(metric.get("max_drawdown_pct") or 0)
    if cagr <= 0 or calmar <= 0:
        return "crypto_capped_risk_not_useful"
    if metric.get("cost_bps") in {25, 50, 100} and cagr < 5:
        return "crypto_capped_risk_cost_sensitive"
    if maxdd > -70 and cagr > 20:
        return "crypto_capped_risk_promising"
    if maxdd > -75:
        return "crypto_capped_risk_drawdown_improved"
    return "manual_review_required"


def label_drawdown(dd: float, static_dd: float, return_drag: float, calmar_improvement: float) -> str:
    if not dd:
        return "manual_review_required"
    if dd - static_dd < 10:
        return "crypto_capped_risk_not_useful"
    if return_drag < -35:
        return "crypto_capped_risk_return_drag_too_high"
    if calmar_improvement > 0:
        return "crypto_capped_risk_drawdown_improved"
    return "manual_review_required"


def final_label(static: dict[str, Any], best: dict[str, Any], contributions: list[dict[str, Any]]) -> str:
    if not static or not best:
        return "insufficient_saved_inputs"
    static_cagr = extract_metric(static.get("metric_value", ""), "CAGR")
    static_dd = extract_metric(static.get("metric_value", ""), "MaxDD")
    static_calmar = extract_metric(static.get("metric_value", ""), "Calmar")
    best_cagr = extract_metric(best.get("metric_value", ""), "CAGR")
    best_dd = extract_metric(best.get("metric_value", ""), "MaxDD")
    best_calmar = extract_metric(best.get("metric_value", ""), "Calmar")
    concentration_helped = any(row.get("status") == "concentration_review_available" for row in contributions)
    if best_dd - static_dd < 10 and not concentration_helped:
        return "equal_weight_still_best_high_drawdown"
    if best_cagr - static_cagr < -35:
        return "crypto_capped_risk_return_drag_too_high"
    if concentration_helped and best_calmar >= static_calmar and best_cagr - static_cagr > -15:
        return "crypto_capped_risk_promising"
    if concentration_helped:
        return "crypto_capped_risk_concentration_improved"
    return "manual_review_required"


def best_capped_risk(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if row.get("strategy_name") in CAPPED_RISK_VARIANTS and row.get("metric_value")]
    return max(candidates, key=lambda row: extract_metric(row.get("metric_value", ""), "Calmar")) if candidates else {}


def metric_for(rows: list[dict[str, Any]], strategy: str) -> dict[str, Any]:
    return next((row for row in rows if row.get("strategy_name") == strategy and str(row.get("cost_bps")) == "10"), {})


def best_by(rows: list[dict[str, Any]], metric_name: str) -> str:
    candidates = [row for row in rows if row.get("metric_value")]
    if not candidates:
        return "unavailable"
    best = max(candidates, key=lambda row: extract_metric(row.get("metric_value", ""), metric_name))
    return f"{best.get('strategy_name')}={extract_metric(best.get('metric_value', ''), metric_name)}"


def summary_value(rows: list[dict[str, Any]], strategy_name: str) -> str:
    row = next((item for item in rows if item.get("strategy_name") == strategy_name), {})
    return str(row.get("metric_value", "unavailable"))


def to_trade_rows(created_at: str, name: str, trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [common_row(created_at, "trades", name, "rebalance", trade.get("selected_symbols", ""), f"turnover={trade.get('turnover', '')}", "trade_recorded", "manual_review_required", trade.get("rebalance_reason", ""), period=str(trade.get("date", "")), cost_bps=trade.get("cost_bps", "")) for trade in trades]


def to_equity_rows(created_at: str, name: str, cost_bps: int, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [common_row(created_at, "equity_curve", name, "equity", round(float(row.get("equity", 0)), 6), row.get("holdings", ""), "equity_row", "manual_review_required", f"cash_weight={row.get('cash_weight', '')}", period=row.get("date", ""), cost_bps=cost_bps) for row in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Crypto equal-weight capped-risk report complete. Research/report only; execution_approved=False.",
        f"Variants tested: {summary_value(summary_rows, 'variants_tested')}",
        f"Best by CAGR: {summary_value(summary_rows, 'best_by_cagr')}",
        f"Best by Sharpe: {summary_value(summary_rows, 'best_by_sharpe')}",
        f"Best by Calmar: {summary_value(summary_rows, 'best_by_calmar')}",
        f"Lowest max drawdown: {summary_value(summary_rows, 'lowest_max_drawdown')}",
        f"Static equal-weight comparison: {summary_value(summary_rows, 'static_equal_weight_result')}",
        f"Best capped-risk variant: {summary_value(summary_rows, 'best_capped_risk_variant')}",
        f"Concentration/top-contributor summary: {summary_value(summary_rows, 'concentration_top_contributor_summary')}",
        f"Drawdown reduction versus equal-weight: {summary_value(summary_rows, 'drawdown_reduction_vs_equal_weight')}",
        f"Return drag versus equal-weight: {summary_value(summary_rows, 'return_drag_vs_equal_weight')}",
        f"Calmar improvement versus equal-weight: {summary_value(summary_rows, 'calmar_improvement_vs_equal_weight')}",
        f"Final summary label: {summary_value(summary_rows, 'final_summary_label')}",
        f"Saved results to {paths['results']}",
        f"Saved summary to {paths['summary']}",
        f"Saved trades to {paths['trades']}",
        f"Saved equity curves to {paths['equity']}",
        f"Saved costs to {paths['costs']}",
        f"Saved splits to {paths['splits']}",
        f"Saved drawdowns to {paths['drawdowns']}",
        f"Saved contributions to {paths['contributions']}",
        "Warning: capped-risk report does not approve crypto execution, paper execution, scheduling, or strategy-to-execution wiring.",
    ]


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMMON_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
