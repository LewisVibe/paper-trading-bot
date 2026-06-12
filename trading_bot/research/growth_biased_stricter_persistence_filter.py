"""Persistence-filter research for the 55% stricter growth-biased gate.

This module runs fixed research-only strategy variants. It downloads daily
yfinance history through the existing strategy-improvement lab helper, writes
generated research CSVs, and never touches broker, position, SQLite, alert,
scheduler, config, or execution paths.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location
from trading_bot.research.strategy_improvement_lab import (
    ALL_ETFS,
    DEFENSIVE_EXPOSURE_ETFS,
    MOMENTUM_LOOKBACK_DAYS,
    RISK_ETFS,
    RISK_EXPOSURE_ETFS,
    STARTING_EQUITY,
    TOP_N,
    TREND_WINDOW_DAYS,
    align_price_rows,
    build_result_rows_for_strategy,
    build_trade_rows,
    breadth_ratio,
    defensive_sleeve_weights,
    download_daily_price_data,
    equal_weights,
    growth_biased_breadth_gate_weights,
    is_above_sma,
    momentum,
    rank_by_momentum,
    simulate_strategy,
    sufficient_history,
    weighted_daily_return,
)


ACTIVE_RESEARCH_LEAD = "growth_biased_rotation_breadth_stricter_gate"
PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"
MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"
SPY_BENCHMARK = "spy_buy_and_hold_benchmark"
EQUAL_WEIGHT_BENCHMARK = "equal_weight_etf_buy_and_hold_benchmark"
CODEX_AMBITIOUS_STRATEGY = "codex_ambitious_concentrated_growth_persistence"
BREADTH_GATE = 0.55
COST_LEVELS_BPS = [0, 10, 25, 50]
SUMMARY_LABELS = [
    "persistence_filter_improved_cost_survival",
    "persistence_filter_promising_but_cost_sensitive",
    "persistence_filter_return_drag",
    "persistence_filter_turnover_reduced_but_edge_lost",
    "persistence_filter_not_useful",
    "insufficient_saved_inputs",
    "manual_review_required",
]
AMBITIOUS_LABELS = [
    "ambitious_candidate_promising",
    "ambitious_candidate_high_return_high_risk",
    "ambitious_candidate_cost_sensitive",
    "ambitious_candidate_not_useful",
    "ambitious_candidate_needs_manual_review",
]

PERSISTENCE_VARIANTS = {
    "stricter_55_reference": {"min_hold_months": 0, "momentum_gap": 0.0, "near_top_n": 0, "top_n": TOP_N},
    "stricter_55_min_hold_2m": {"min_hold_months": 2, "momentum_gap": 0.0, "near_top_n": 0, "top_n": TOP_N},
    "stricter_55_min_hold_3m": {"min_hold_months": 3, "momentum_gap": 0.0, "near_top_n": 0, "top_n": TOP_N},
    "stricter_55_momentum_gap_5pp": {"min_hold_months": 0, "momentum_gap": 0.05, "near_top_n": 0, "top_n": TOP_N},
    "stricter_55_near_top2_hold": {"min_hold_months": 0, "momentum_gap": 0.0, "near_top_n": 2, "top_n": TOP_N},
    "stricter_55_combined_persistence": {"min_hold_months": 2, "momentum_gap": 0.05, "near_top_n": 2, "top_n": TOP_N},
    CODEX_AMBITIOUS_STRATEGY: {"min_hold_months": 2, "momentum_gap": 0.075, "near_top_n": 2, "top_n": 2},
}

REFERENCE_STRATEGIES = [
    SPY_BENCHMARK,
    EQUAL_WEIGHT_BENCHMARK,
    MONTHLY_ROTATION_REFERENCE,
    PREVIOUS_RESEARCH_LEAD,
    ACTIVE_RESEARCH_LEAD,
]

OUTPUT_FILES = {
    "detail": Path("data/growth_biased_stricter_persistence_filter.csv"),
    "summary": Path("data/growth_biased_stricter_persistence_filter_summary.csv"),
}

DETAIL_COLUMNS = [
    "created_at",
    "strategy_name",
    "variant_type",
    "cost_level_bps",
    "rule_mapping",
    "cagr_pct",
    "cost_adjusted_cagr_pct",
    "cagr_decay_vs_0_bps",
    "sharpe_ratio",
    "cost_adjusted_sharpe_ratio",
    "sharpe_decay_vs_0_bps",
    "max_drawdown_pct",
    "calmar_ratio",
    "cost_adjusted_calmar_ratio",
    "calmar_decay_vs_0_bps",
    "trade_count",
    "turnover",
    "turnover_reduction_vs_reference",
    "average_holding_period_days",
    "average_cash_weight_pct",
    "cagr_delta_vs_original",
    "calmar_delta_vs_original",
    "cagr_delta_vs_stricter_reference",
    "calmar_delta_vs_stricter_reference",
    "cagr_gap_vs_spy",
    "calmar_gap_vs_spy",
    "survives_10_bps",
    "survives_25_bps",
    "status",
    "research_conclusion_label",
    "review_warning",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "promotion_approved",
    "scheduling_approved",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "best_variant_0_bps",
    "best_variant_10_bps",
    "best_variant_25_bps",
    "any_variant_survives_10_bps",
    "any_variant_survives_25_bps",
    "best_turnover_reduction_vs_reference",
    "summary_label",
    "comparison_vs_original_crash_gate",
    "comparison_vs_spy",
    "codex_ambitious_strategy",
    "codex_strategy_reason",
    "codex_strategy_label",
    "codex_beats_spy",
    "codex_beats_stricter_gate",
    "review_warnings",
    "interpretation",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "promotion_approved",
    "scheduling_approved",
]


@dataclass
class PersistenceFilterResult:
    detail_path: Path
    summary_path: Path
    detail_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_growth_biased_stricter_persistence_filter(data_dir: Path | str = "data") -> PersistenceFilterResult:
    root = Path(".")
    data_path = Path(data_dir)
    configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    price_data, data_errors = download_daily_price_data(ALL_ETFS)
    aligned_rows = align_price_rows(price_data)
    if not aligned_rows:
        detail_rows = insufficient_detail_rows(created_at, data_errors)
        summary_rows = insufficient_summary_rows(created_at, data_errors)
    else:
        detail_rows, summary_rows = build_persistence_outputs(created_at, aligned_rows)
    write_rows(output_paths["detail"], DETAIL_COLUMNS, detail_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    return PersistenceFilterResult(
        detail_path=output_paths["detail"],
        summary_path=output_paths["summary"],
        detail_rows=detail_rows,
        summary_rows=summary_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def build_persistence_outputs(created_at: str, aligned_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    result_rows: list[dict[str, Any]] = []
    for strategy_name in REFERENCE_STRATEGIES:
        equity_rows, trade_rows = simulate_strategy(strategy_name, aligned_rows, created_at)
        result_rows.extend(build_result_rows_for_strategy(created_at, strategy_name, equity_rows, trade_rows))
    for strategy_name, rules in PERSISTENCE_VARIANTS.items():
        equity_rows, trade_rows = simulate_persistence_strategy(strategy_name, rules, aligned_rows, created_at)
        result_rows.extend(build_result_rows_for_strategy(created_at, strategy_name, equity_rows, trade_rows))
    full_rows = {row["strategy_name"]: row for row in result_rows if row.get("period") == "full_period"}
    detail_rows = build_detail_rows(created_at, full_rows)
    summary_row = build_summary_row(created_at, detail_rows)
    return detail_rows, [summary_row]


def simulate_persistence_strategy(
    strategy_name: str,
    rules: dict[str, Any],
    aligned_rows: list[dict[str, Any]],
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    equity = STARTING_EQUITY
    current_weights: dict[str, float] = {}
    holding_months: dict[str, int] = {}
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
            target_weights, reason, regime = persistence_weights(history, current_weights, holding_months, rules, strategy_name)
            trade_rows.extend(build_trade_rows(created_at, date, strategy_name, current_weights, target_weights, reason))
            holding_months = update_holding_months(current_weights, target_weights, holding_months)
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


def persistence_weights(
    history: dict[str, list[float]],
    current_weights: dict[str, float],
    holding_months: dict[str, int],
    rules: dict[str, Any],
    strategy_name: str,
) -> tuple[dict[str, float], str, str]:
    base_weights, base_reason, base_regime = growth_biased_breadth_gate_weights(history, current_weights, BREADTH_GATE, "55_persistence")
    if not base_weights or "risk_on" not in base_regime:
        return base_weights, base_reason + " Persistence inactive outside risk-on posture.", base_regime
    ranked = rank_by_momentum(RISK_ETFS, history, MOMENTUM_LOOKBACK_DAYS)
    eligible = [ticker for ticker in ranked if is_above_sma(history[ticker], TREND_WINDOW_DAYS)]
    if not eligible:
        defensive = defensive_sleeve_weights(history)
        return defensive, "No eligible risk ETFs; defensive fallback.", "persistence_defensive"
    top_n = int(rules["top_n"])
    target = eligible[:top_n]
    retained = []
    near_top_n = int(rules["near_top_n"])
    for ticker in current_weights:
        if ticker not in eligible:
            continue
        if holding_months.get(ticker, 0) < int(rules["min_hold_months"]):
            retained.append(ticker)
            continue
        if near_top_n and ticker in eligible[:near_top_n]:
            retained.append(ticker)
            continue
        if float(rules["momentum_gap"]) > 0 and target:
            current_score = momentum(history[ticker], MOMENTUM_LOOKBACK_DAYS)
            best_new_score = max(momentum(history[item], MOMENTUM_LOOKBACK_DAYS) for item in target)
            if best_new_score - current_score < float(rules["momentum_gap"]):
                retained.append(ticker)
    final = []
    for ticker in retained + target:
        if ticker not in final:
            final.append(ticker)
        if len(final) >= top_n:
            break
    if strategy_name == CODEX_AMBITIOUS_STRATEGY:
        reason = "Codex ambitious concentrated growth persistence: top-two eligible risk ETFs, 55% breadth gate, 2-month hold, 7.5pp momentum gap, near-top2 retention."
        return equal_weights(final), reason, "codex_ambitious_growth_persistence"
    return equal_weights(final), f"{base_reason} Fixed persistence rules retained {','.join(retained) or 'none'} before top candidates.", "persistence_risk_on"


def update_holding_months(
    old_weights: dict[str, float],
    new_weights: dict[str, float],
    holding_months: dict[str, int],
) -> dict[str, int]:
    updated = {}
    for ticker in new_weights:
        updated[ticker] = holding_months.get(ticker, 0) + 1 if ticker in old_weights else 1
    return updated


def build_detail_rows(created_at: str, full_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    reference = full_rows.get("stricter_55_reference", full_rows.get(ACTIVE_RESEARCH_LEAD, {}))
    original = full_rows.get(PREVIOUS_RESEARCH_LEAD, {})
    spy = full_rows.get(SPY_BENCHMARK, {})
    rows = []
    for strategy_name in PERSISTENCE_VARIANTS:
        source = full_rows.get(strategy_name, {})
        for cost_bps in COST_LEVELS_BPS:
            rows.append(cost_row(created_at, strategy_name, source, reference, original, spy, cost_bps))
    annotate_survival(rows)
    return rows


def cost_row(
    created_at: str,
    strategy_name: str,
    source: dict[str, Any],
    reference: dict[str, Any],
    original: dict[str, Any],
    spy: dict[str, Any],
    cost_bps: int,
) -> dict[str, Any]:
    if not source:
        return base_detail_row(created_at, strategy_name, cost_bps, "insufficient_saved_inputs", "missing_result_row")
    cagr = as_float(source.get("cagr_pct"))
    sharpe = as_float(source.get("sharpe_ratio"))
    calmar = as_float(source.get("calmar_ratio"))
    maxdd = as_float(source.get("max_drawdown_pct"))
    turnover = as_float(source.get("turnover"))
    adjusted_cagr = cagr - turnover * cost_bps / 100.0
    adjusted_calmar = adjusted_cagr / abs(maxdd) if maxdd < 0 else 0.0
    adjusted_sharpe = adjusted_sharpe_for_cost(sharpe, cagr, cagr - adjusted_cagr)
    ref_turnover = as_float(reference.get("turnover"))
    cagr_vs_original = adjusted_cagr - as_float(original.get("cagr_pct"))
    calmar_vs_original = adjusted_calmar - as_float(original.get("calmar_ratio"))
    cagr_vs_reference = adjusted_cagr - as_float(reference.get("cagr_pct"))
    calmar_vs_reference = adjusted_calmar - as_float(reference.get("calmar_ratio"))
    cagr_vs_spy = adjusted_cagr - as_float(spy.get("cagr_pct"))
    calmar_vs_spy = adjusted_calmar - as_float(spy.get("calmar_ratio"))
    status, label, warning = classify_row(strategy_name, cost_bps, adjusted_cagr, adjusted_calmar, cagr_vs_original, calmar_vs_original, cagr_vs_reference, turnover, ref_turnover)
    row = base_detail_row(created_at, strategy_name, cost_bps, status, warning)
    row.update(
        {
            "variant_type": "codex_ambitious" if strategy_name == CODEX_AMBITIOUS_STRATEGY else "persistence_filter",
            "rule_mapping": rule_mapping(strategy_name),
            "cagr_pct": round(cagr, 4),
            "cost_adjusted_cagr_pct": round(adjusted_cagr, 4),
            "cagr_decay_vs_0_bps": round(adjusted_cagr - cagr, 4),
            "sharpe_ratio": round(sharpe, 4),
            "cost_adjusted_sharpe_ratio": round(adjusted_sharpe, 4),
            "sharpe_decay_vs_0_bps": round(adjusted_sharpe - sharpe, 4),
            "max_drawdown_pct": round(maxdd, 4),
            "calmar_ratio": round(calmar, 4),
            "cost_adjusted_calmar_ratio": round(adjusted_calmar, 4),
            "calmar_decay_vs_0_bps": round(adjusted_calmar - calmar, 4),
            "trade_count": int(as_float(source.get("trade_count"))),
            "turnover": round(turnover, 4),
            "turnover_reduction_vs_reference": round(ref_turnover - turnover, 4),
            "average_holding_period_days": round(252.0 / turnover, 2) if turnover > 0 else "",
            "average_cash_weight_pct": source.get("average_cash_weight_pct", ""),
            "cagr_delta_vs_original": round(cagr_vs_original, 4),
            "calmar_delta_vs_original": round(calmar_vs_original, 4),
            "cagr_delta_vs_stricter_reference": round(cagr_vs_reference, 4),
            "calmar_delta_vs_stricter_reference": round(calmar_vs_reference, 4),
            "cagr_gap_vs_spy": round(cagr_vs_spy, 4),
            "calmar_gap_vs_spy": round(calmar_vs_spy, 4),
            "research_conclusion_label": label,
        }
    )
    return row


def classify_row(
    strategy_name: str,
    cost_bps: int,
    adjusted_cagr: float,
    adjusted_calmar: float,
    cagr_vs_original: float,
    calmar_vs_original: float,
    cagr_vs_reference: float,
    turnover: float,
    ref_turnover: float,
) -> tuple[str, str, str]:
    turnover_reduced = turnover < ref_turnover
    credible = adjusted_cagr > 0 and adjusted_calmar > 0.20 and cagr_vs_original > 0
    warnings = []
    if turnover > 20:
        warnings.append("turnover_extreme_review")
    if cost_bps >= 10 and not credible:
        warnings.append("cost_survival_failed")
    if strategy_name == CODEX_AMBITIOUS_STRATEGY:
        if credible and cagr_vs_reference > 0:
            return "credible_after_cost", "ambitious_candidate_promising", "; ".join(warnings)
        if adjusted_cagr > 0 and adjusted_calmar > 0:
            return "manual_review_required", "ambitious_candidate_high_return_high_risk", "; ".join(warnings)
        return "not_credible_after_cost", "ambitious_candidate_cost_sensitive", "; ".join(warnings or ["not_useful"])
    if credible and turnover_reduced and cost_bps in {10, 25}:
        return "credible_after_cost", "persistence_filter_improved_cost_survival", "; ".join(warnings)
    if credible:
        return "credible_after_cost", "persistence_filter_promising_but_cost_sensitive", "; ".join(warnings)
    if turnover_reduced and adjusted_cagr <= 0:
        return "not_credible_after_cost", "persistence_filter_turnover_reduced_but_edge_lost", "; ".join(warnings)
    if adjusted_cagr < 0 or adjusted_calmar < 0:
        return "not_credible_after_cost", "persistence_filter_not_useful", "; ".join(warnings)
    return "manual_review_required", "manual_review_required", "; ".join(warnings)


def annotate_survival(rows: list[dict[str, Any]]) -> None:
    by_strategy = {}
    for row in rows:
        by_strategy.setdefault(row["strategy_name"], {})[int(row["cost_level_bps"])] = row
    for strategy_rows in by_strategy.values():
        survives_10 = strategy_rows.get(10, {}).get("status") == "credible_after_cost"
        survives_25 = strategy_rows.get(25, {}).get("status") == "credible_after_cost"
        for row in strategy_rows.values():
            row["survives_10_bps"] = survives_10
            row["survives_25_bps"] = survives_25


def build_summary_row(created_at: str, detail_rows: list[dict[str, Any]]) -> dict[str, Any]:
    best0 = best_variant(detail_rows, 0)
    best10 = best_variant(detail_rows, 10)
    best25 = best_variant(detail_rows, 25)
    any10 = any(row["cost_level_bps"] == 10 and row["status"] == "credible_after_cost" for row in detail_rows)
    any25 = any(row["cost_level_bps"] == 25 and row["status"] == "credible_after_cost" for row in detail_rows)
    reference0 = next((row for row in detail_rows if row["strategy_name"] == "stricter_55_reference" and row["cost_level_bps"] == 0), {})
    best_reduction = max((as_float(row.get("turnover_reduction_vs_reference")) for row in detail_rows if row["cost_level_bps"] == 0), default=0.0)
    codex0 = next((row for row in detail_rows if row["strategy_name"] == CODEX_AMBITIOUS_STRATEGY and row["cost_level_bps"] == 0), {})
    labels = {str(row.get("research_conclusion_label", "")) for row in detail_rows}
    if any25:
        summary_label = "persistence_filter_improved_cost_survival"
    elif any10:
        summary_label = "persistence_filter_promising_but_cost_sensitive"
    elif best_reduction > 0 and as_float(best10.get("cost_adjusted_cagr_pct")) <= 0:
        summary_label = "persistence_filter_turnover_reduced_but_edge_lost"
    elif "persistence_filter_not_useful" in labels:
        summary_label = "persistence_filter_not_useful"
    else:
        summary_label = "manual_review_required"
    warnings = sorted({str(row.get("review_warning", "")) for row in detail_rows if row.get("review_warning")})
    return {
        "created_at": created_at,
        "summary_name": "growth_biased_stricter_persistence_filter",
        "best_variant_0_bps": best0.get("strategy_name", ""),
        "best_variant_10_bps": best10.get("strategy_name", ""),
        "best_variant_25_bps": best25.get("strategy_name", ""),
        "any_variant_survives_10_bps": any10,
        "any_variant_survives_25_bps": any25,
        "best_turnover_reduction_vs_reference": round(best_reduction, 4),
        "summary_label": summary_label,
        "comparison_vs_original_crash_gate": "beats_original_under_some_costs" if any10 else "cost_survival_not_confirmed",
        "comparison_vs_spy": f"reference_gap_vs_spy={reference0.get('cagr_gap_vs_spy', '')}",
        "codex_ambitious_strategy": CODEX_AMBITIOUS_STRATEGY,
        "codex_strategy_reason": "Selected because concentrated top-two growth momentum plus 55% breadth gate and persistence directly targets turnover while staying auditable.",
        "codex_strategy_label": codex0.get("research_conclusion_label", "ambitious_candidate_needs_manual_review"),
        "codex_beats_spy": as_float(codex0.get("cagr_gap_vs_spy")) > 0,
        "codex_beats_stricter_gate": as_float(codex0.get("cagr_delta_vs_stricter_reference")) > 0,
        "review_warnings": "; ".join(warnings) if warnings else "none",
        "interpretation": "Persistence filter is research-only and does not approve preview promotion or execution.",
        "required_next_step": "Manual review cost survival, turnover reduction, and benchmark gaps before any preview discussion.",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "promotion_approved": False,
        "scheduling_approved": False,
    }


def best_variant(rows: list[dict[str, Any]], cost_bps: int) -> dict[str, Any]:
    candidates = [row for row in rows if row["cost_level_bps"] == cost_bps]
    return max(candidates, key=lambda row: (as_float(row.get("cost_adjusted_calmar_ratio")), as_float(row.get("cost_adjusted_cagr_pct"))), default={})


def insufficient_detail_rows(created_at: str, data_errors: dict[str, str]) -> list[dict[str, Any]]:
    warning = "; ".join(f"{ticker}: {error}" for ticker, error in sorted(data_errors.items())[:8]) or "No aligned daily data."
    return [
        base_detail_row(created_at, strategy_name, cost_bps, "insufficient_saved_inputs", warning)
        for strategy_name in PERSISTENCE_VARIANTS
        for cost_bps in COST_LEVELS_BPS
    ]


def insufficient_summary_rows(created_at: str, data_errors: dict[str, str]) -> list[dict[str, Any]]:
    warning = "; ".join(f"{ticker}: {error}" for ticker, error in sorted(data_errors.items())[:8]) or "No aligned daily data."
    return [
        {
            "created_at": created_at,
            "summary_name": "growth_biased_stricter_persistence_filter",
            "summary_label": "insufficient_saved_inputs",
            "codex_ambitious_strategy": CODEX_AMBITIOUS_STRATEGY,
            "codex_strategy_reason": "Selected because concentrated top-two growth momentum plus 55% breadth gate and persistence directly targets turnover while staying auditable.",
            "codex_strategy_label": "ambitious_candidate_needs_manual_review",
            "review_warnings": warning,
            "interpretation": "Could not build persistence filter because daily market data was unavailable.",
            "required_next_step": "Rerun after yfinance/cache data is available; do not approve execution.",
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
            "paper_execution_approved": False,
            "promotion_approved": False,
            "scheduling_approved": False,
        }
    ]


def base_detail_row(created_at: str, strategy_name: str, cost_bps: int, status: str, warning: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "variant_type": "codex_ambitious" if strategy_name == CODEX_AMBITIOUS_STRATEGY else "persistence_filter",
        "cost_level_bps": cost_bps,
        "rule_mapping": rule_mapping(strategy_name),
        "status": status,
        "research_conclusion_label": "insufficient_saved_inputs" if status == "insufficient_saved_inputs" else "manual_review_required",
        "review_warning": warning,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "promotion_approved": False,
        "scheduling_approved": False,
    }


def rule_mapping(strategy_name: str) -> str:
    rules = PERSISTENCE_VARIANTS.get(strategy_name, {})
    return (
        f"55% breadth gate; top_n={rules.get('top_n')}; min_hold_months={rules.get('min_hold_months')}; "
        f"momentum_gap={rules.get('momentum_gap')}; near_top_n={rules.get('near_top_n')}; force exit if eligibility fails."
    )


def show_growth_biased_stricter_persistence_filter_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    detail = read_csv(data_path / OUTPUT_FILES["detail"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    if not detail or not summary:
        return 1, ["Run `python bot.py --growth-biased-stricter-persistence-filter` first."]
    summary_row = summary[0]
    approval_values = {str(row.get("execution_approved", "")).lower() for row in detail + summary}
    return 0, [
        "Growth-biased stricter persistence filter. Display only; execution_approved=False.",
        f"Best persistence variant at 0 bps: {summary_row.get('best_variant_0_bps', '')}",
        f"Best persistence variant at 10 bps: {summary_row.get('best_variant_10_bps', '')}",
        f"Best persistence variant at 25 bps: {summary_row.get('best_variant_25_bps', '')}",
        f"Best turnover reduction versus 55% reference: {summary_row.get('best_turnover_reduction_vs_reference', '')}",
        f"Any variant survives 10 bps: {summary_row.get('any_variant_survives_10_bps', False)}",
        f"Any variant survives 25 bps: {summary_row.get('any_variant_survives_25_bps', False)}",
        f"Summary label: {summary_row.get('summary_label', 'insufficient_saved_inputs')}",
        f"Comparison versus original crash gate: {summary_row.get('comparison_vs_original_crash_gate', '')}",
        f"Comparison versus SPY: {summary_row.get('comparison_vs_spy', '')}",
        f"Codex ambitious strategy: {summary_row.get('codex_ambitious_strategy', CODEX_AMBITIOUS_STRATEGY)}",
        f"Codex beats SPY: {summary_row.get('codex_beats_spy', False)}",
        f"Codex beats stricter gate: {summary_row.get('codex_beats_stricter_gate', False)}",
        f"Review warnings: {summary_row.get('review_warnings', '')}",
        f"execution_approved values: {', '.join(sorted(approval_values)) or 'false'}",
        "Warning: saved persistence report does not approve orders, preview promotion, scheduling, or execution.",
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    summary = summary_rows[0] if summary_rows else {}
    return [
        "Growth-biased stricter persistence filter complete. Research/report only; execution_approved=False.",
        f"Best persistence variant at 0 bps: {summary.get('best_variant_0_bps', '')}",
        f"Best persistence variant at 10 bps: {summary.get('best_variant_10_bps', '')}",
        f"Best persistence variant at 25 bps: {summary.get('best_variant_25_bps', '')}",
        f"Any variant survives 10 bps: {summary.get('any_variant_survives_10_bps', False)}",
        f"Any variant survives 25 bps: {summary.get('any_variant_survives_25_bps', False)}",
        f"Summary label: {summary.get('summary_label', 'insufficient_saved_inputs')}",
        f"Codex ambitious strategy: {summary.get('codex_ambitious_strategy', CODEX_AMBITIOUS_STRATEGY)}",
        f"Saved persistence detail to {output_paths['detail']}",
        f"Saved persistence summary to {output_paths['summary']}",
        "Warning: persistence filter does not approve orders, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def adjusted_sharpe_for_cost(base_sharpe: float, base_cagr: float, cost_drag: float) -> float:
    if abs(base_cagr) < 0.000001:
        return base_sharpe
    return base_sharpe - (cost_drag / abs(base_cagr)) * max(abs(base_sharpe), 0.25)


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
