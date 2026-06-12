"""Research-only equal-weight crypto crash-gate strategy report.

This module tests fixed, auditable crash-gate variants around the robust but
high-drawdown equal-weight crypto benchmark. It writes generated research CSVs
only and does not touch broker, position, database, alert, config, scheduling,
or execution paths.
"""

from __future__ import annotations

import csv
from collections import Counter
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
    equal_weights,
    load_eligible_universe,
    simulate_monthly_static,
    simulate_named_strategy,
    simulate_weight_schedule,
)


READINESS_FILE = Path("data/crypto_universe_readiness_report.csv")
CRASH_GATE_VARIANTS = [
    "crypto_equal_weight_trend_crash_gate",
    "crypto_equal_weight_btc_trend_gate",
    "crypto_equal_weight_breadth_gate",
    "crypto_equal_weight_drawdown_brake",
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
ALL_NAMES = [*CRASH_GATE_VARIANTS, *BENCHMARKS]
TRANSITION_BLOCKED_CONTRACT = ["POL-USD", "MATIC-USD"]
COST_BPS = [0, 10, 25, 50, 100]
SPLITS = [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]

SUMMARY_LABELS = [
    "crypto_crash_gate_promising",
    "crypto_crash_gate_drawdown_improved",
    "crypto_crash_gate_return_drag_too_high",
    "crypto_crash_gate_cost_sensitive",
    "crypto_crash_gate_split_sensitive",
    "crypto_crash_gate_new_defensive_crypto_candidate",
    "crypto_crash_gate_not_useful",
    "equal_weight_still_best_high_drawdown",
    "insufficient_saved_inputs",
    "manual_review_required",
]

OUTPUT_FILES = {
    "results": Path("data/crypto_equal_weight_crash_gate.csv"),
    "summary": Path("data/crypto_equal_weight_crash_gate_summary.csv"),
    "trades": Path("data/crypto_equal_weight_crash_gate_trades.csv"),
    "equity": Path("data/crypto_equal_weight_crash_gate_equity_curves.csv"),
    "costs": Path("data/crypto_equal_weight_crash_gate_costs.csv"),
    "splits": Path("data/crypto_equal_weight_crash_gate_splits.csv"),
    "drawdowns": Path("data/crypto_equal_weight_crash_gate_drawdowns.csv"),
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
class CryptoEqualWeightCrashGateResult:
    results_path: Path
    summary_path: Path
    trades_path: Path
    equity_path: Path
    costs_path: Path
    splits_path: Path
    drawdowns_path: Path
    result_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    equity_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_equal_weight_crash_gate(data_dir: Path | str = "data") -> CryptoEqualWeightCrashGateResult:
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
        result_rows, summary_rows, trade_rows, equity_rows, cost_rows, split_rows, drawdown_rows = insufficient_rows(
            created_at, universe, universe_note, errors
        )
    else:
        result_rows, trade_rows, equity_rows = run_cost_lab(created_at, aligned, price_data, usable_universe, universe_note)
        cost_rows = [row for row in result_rows if row.get("section") == "cost_stress"]
        split_rows = run_split_checks(created_at, aligned, price_data, usable_universe)
        drawdown_rows = build_drawdown_rows(created_at, result_rows, equity_rows)
        summary_rows = build_summary_rows(created_at, result_rows, cost_rows, split_rows, drawdown_rows)

    write_rows(output_paths["results"], result_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["trades"], trade_rows)
    write_rows(output_paths["equity"], equity_rows)
    write_rows(output_paths["costs"], cost_rows)
    write_rows(output_paths["splits"], split_rows)
    write_rows(output_paths["drawdowns"], drawdown_rows)
    return CryptoEqualWeightCrashGateResult(
        results_path=output_paths["results"],
        summary_path=output_paths["summary"],
        trades_path=output_paths["trades"],
        equity_path=output_paths["equity"],
        costs_path=output_paths["costs"],
        splits_path=output_paths["splits"],
        drawdowns_path=output_paths["drawdowns"],
        result_rows=result_rows,
        summary_rows=summary_rows,
        trade_rows=trade_rows,
        equity_rows=equity_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        drawdown_rows=drawdown_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_crypto_equal_weight_crash_gate_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    results = read_csv(data_path / OUTPUT_FILES["results"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    costs = read_csv(data_path / OUTPUT_FILES["costs"].name)
    splits = read_csv(data_path / OUTPUT_FILES["splits"].name)
    drawdowns = read_csv(data_path / OUTPUT_FILES["drawdowns"].name)
    equity = read_csv(data_path / OUTPUT_FILES["equity"].name)
    if not results or not summary:
        return 1, ["Run `python bot.py --crypto-equal-weight-crash-gate` first."]
    approvals = {str(row.get("execution_approved", "")).lower() for row in results + summary + costs + splits + drawdowns + equity}
    return 0, [
        "Crypto equal-weight crash gate report. Display only; execution_approved=False.",
        f"Variants tested: {', '.join(CRASH_GATE_VARIANTS)}",
        f"Best by CAGR: {summary_value(summary, 'best_by_cagr')}",
        f"Best by Sharpe: {summary_value(summary, 'best_by_sharpe')}",
        f"Best by Calmar: {summary_value(summary, 'best_by_calmar')}",
        f"Lowest max drawdown: {summary_value(summary, 'lowest_max_drawdown')}",
        f"Static equal-weight comparison: {summary_value(summary, 'static_equal_weight_result')}",
        f"Best crash-gate variant: {summary_value(summary, 'best_crash_gate_variant')}",
        f"Drawdown reduction versus equal-weight: {summary_value(summary, 'drawdown_reduction_vs_equal_weight')}",
        f"Return drag versus equal-weight: {summary_value(summary, 'return_drag_vs_equal_weight')}",
        f"Cost survival summary: {status_counts(costs)}",
        f"Split summary: {status_counts(splits)}",
        f"Final summary label: {summary_value(summary, 'final_summary_label')}",
        f"execution_approved values: {', '.join(sorted(approvals)) or 'false'}",
        "Warning: crash-gate report does not create order instructions, approve preview promotion, or approve crypto execution.",
    ]


def run_cost_lab(
    created_at: str,
    aligned: list[dict[str, Any]],
    price_data: dict[str, list[dict[str, Any]]],
    universe: list[str],
    universe_note: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    result_rows = []
    trade_rows = []
    equity_rows = []
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
                trade_rows.extend(to_trade_rows(created_at, name, trades))
                equity_rows.extend(to_equity_rows(created_at, name, cost_bps, equity))
    return result_rows, trade_rows, equity_rows


def run_split_checks(
    created_at: str,
    aligned: list[dict[str, Any]],
    price_data: dict[str, list[dict[str, Any]]],
    universe: list[str],
) -> list[dict[str, Any]]:
    rows = []
    for split_name, split_pct in SPLITS:
        start = int(len(aligned) * split_pct)
        split_rows = aligned[start:]
        for name in ALL_NAMES:
            equity, trades = simulate_name(name, split_rows, price_data, universe, 10, created_at, include_trades=False)
            metric = build_metrics(created_at, name, "out_of_sample", 10, equity, trades, split_name)
            status = "split_credible" if float(metric.get("cagr_pct") or 0) > 0 and float(metric.get("calmar_ratio") or 0) > 0 else "crypto_crash_gate_split_sensitive"
            rows.append(to_common(created_at, "split_validation", metric, status, split_name))
    return rows


def simulate_name(
    name: str,
    aligned: list[dict[str, Any]],
    price_data: dict[str, list[dict[str, Any]]],
    universe: list[str],
    cost_bps: int,
    created_at: str,
    *,
    include_trades: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if name == "equal_weight_inception_aware":
        rows = variable_universe_rows(price_data, universe)
        if aligned:
            first_date = aligned[0]["date"]
            rows = [row for row in rows if row.get("date", "") >= first_date]
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
    if name == "crypto_equal_weight_trend_crash_gate":
        return simulate_trend_crash_gate(name, aligned, universe, cost_bps, created_at, include_trades)
    if name == "crypto_equal_weight_btc_trend_gate":
        return simulate_btc_trend_gate(name, aligned, universe, cost_bps, created_at, include_trades)
    if name == "crypto_equal_weight_breadth_gate":
        return simulate_breadth_gate(name, aligned, universe, cost_bps, created_at, include_trades)
    if name == "crypto_equal_weight_drawdown_brake":
        return simulate_drawdown_brake(name, aligned, universe, cost_bps, created_at, include_trades)
    raise ValueError(f"Unsupported crypto equal-weight crash-gate variant: {name}")


def simulate_trend_crash_gate(name: str, rows: list[dict[str, Any]], universe: list[str], cost_bps: int, created_at: str, include_trades: bool):
    def target(index: int, _weights: dict[str, float]) -> dict[str, float]:
        if index < 200:
            return {}
        breadth_symbols = [symbol for symbol in universe if above_sma(rows, symbol, index, 200)]
        breadth = len(breadth_symbols) / max(1, len(universe))
        if breadth < 0.30:
            return {}
        weights = equal_weights(breadth_symbols)
        if not above_sma(rows, "BTC-USD", index, 200):
            weights = {symbol: weight * 0.5 for symbol, weight in weights.items()}
        return weights

    return simulate_weight_schedule(name, rows, cost_bps, created_at, include_trades, target, monthly_only=True)


def simulate_btc_trend_gate(name: str, rows: list[dict[str, Any]], universe: list[str], cost_bps: int, created_at: str, include_trades: bool):
    def target(index: int, _weights: dict[str, float]) -> dict[str, float]:
        if index < 200 or not above_sma(rows, "BTC-USD", index, 200):
            return {}
        return equal_weights(universe)

    return simulate_weight_schedule(name, rows, cost_bps, created_at, include_trades, target, monthly_only=True)


def simulate_breadth_gate(name: str, rows: list[dict[str, Any]], universe: list[str], cost_bps: int, created_at: str, include_trades: bool):
    def target(index: int, _weights: dict[str, float]) -> dict[str, float]:
        if index < 200:
            return {}
        breadth = sum(1 for symbol in universe if above_sma(rows, symbol, index, 200)) / max(1, len(universe))
        return equal_weights(universe) if breadth >= 0.40 else {}

    return simulate_weight_schedule(name, rows, cost_bps, created_at, include_trades, target, monthly_only=True)


def simulate_drawdown_brake(name: str, rows: list[dict[str, Any]], universe: list[str], cost_bps: int, created_at: str, include_trades: bool):
    first_closes = rows[0]["closes"]
    peak = 1.0

    def target(index: int, _weights: dict[str, float]) -> dict[str, float]:
        nonlocal peak
        if index < 200:
            return {}
        equal_weight_index = sum(rows[index]["closes"][symbol] / first_closes[symbol] for symbol in universe) / max(1, len(universe))
        peak = max(peak, equal_weight_index)
        drawdown = (equal_weight_index / peak) - 1.0
        if drawdown < -0.50 and not above_sma(rows, "BTC-USD", index, 200):
            return {}
        weights = equal_weights(universe)
        if drawdown < -0.35:
            return {symbol: weight * 0.5 for symbol, weight in weights.items()}
        return weights

    return simulate_weight_schedule(name, rows, cost_bps, created_at, include_trades, target, monthly_only=True)


def build_drawdown_rows(created_at: str, result_rows: list[dict[str, Any]], equity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    equity_by_name = {
        name: sorted(
            [row for row in equity_rows if row.get("strategy_name") == name and str(row.get("cost_bps")) == "10"],
            key=lambda row: row.get("period", ""),
        )
        for name in ALL_NAMES
    }
    static = metric_for(result_rows, "equal_weight_eligible_crypto_benchmark")
    btc = metric_for(result_rows, "btc_buy_and_hold_benchmark")
    codex = metric_for(result_rows, CODEX_STRATEGY)
    rows = []
    for name in ALL_NAMES:
        metric = metric_for(result_rows, name)
        window = drawdown_window(equity_by_name.get(name, []))
        dd = window.get("max_drawdown_pct") if window else extract_metric(metric.get("metric_value", ""), "MaxDD")
        static_dd = overlap_drawdown(equity_by_name.get("equal_weight_eligible_crypto_benchmark", []), window)
        btc_dd = overlap_drawdown(equity_by_name.get("btc_buy_and_hold_benchmark", []), window)
        codex_dd = overlap_drawdown(equity_by_name.get(CODEX_STRATEGY, []), window)
        static_reference = static_dd if static_dd is not None else extract_metric(static.get("metric_value", ""), "MaxDD")
        btc_reference = btc_dd if btc_dd is not None else extract_metric(btc.get("metric_value", ""), "MaxDD")
        codex_reference = codex_dd if codex_dd is not None else extract_metric(codex.get("metric_value", ""), "MaxDD")
        evidence = (
            "Worst drawdown window review is based on generated 10 bps equity curves where available; "
            f"start={window_text(window, 'start_date')}; trough={window_text(window, 'trough_date')}; "
            f"recovery={window_text(window, 'recovery_date')}; recovery_rows={window_text(window, 'recovery_rows')}; "
            f"drawdown_reduction_vs_equal_weight_same_window={reduction_text(dd, static_dd)}; "
            f"drawdown_reduction_vs_btc_same_window={reduction_text(dd, btc_dd)}; "
            f"drawdown_reduction_vs_codex_same_window={reduction_text(dd, codex_dd)}; "
            f"fallback_full_period_equal_weight_reference={round(dd - static_reference, 4) if static_reference else 'unavailable'}; "
            f"fallback_full_period_btc_reference={round(dd - btc_reference, 4) if btc_reference else 'unavailable'}; "
            f"fallback_full_period_codex_reference={round(dd - codex_reference, 4) if codex_reference else 'unavailable'}."
        )
        metric_value = (
            f"MaxDD={round(float(dd or 0), 4)}; start={window_text(window, 'start_date')}; "
            f"trough={window_text(window, 'trough_date')}; recovery={window_text(window, 'recovery_date')}; "
            f"recovery_rows={window_text(window, 'recovery_rows')}"
        )
        rows.append(
            common_row(
                created_at,
                "drawdown_review",
                name,
                "worst_drawdown_window",
                metric_value,
                "same-window overlap where available",
                "drawdown_review_available" if window else "drawdown_review_unavailable",
                label_drawdown(float(dd or 0), static_reference),
                evidence,
            )
        )
    return rows


def drawdown_window(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    peak = float(rows[0].get("metric_value", 0) or rows[0].get("equity", 0) or 0)
    peak_index = 0
    worst = {
        "max_drawdown_pct": 0.0,
        "start_index": 0,
        "trough_index": 0,
        "start_date": rows[0].get("period", ""),
        "trough_date": rows[0].get("period", ""),
        "recovery_date": "",
        "recovery_rows": "",
    }
    for index, row in enumerate(rows):
        equity = float(row.get("metric_value", 0) or row.get("equity", 0) or 0)
        if equity <= 0:
            continue
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = (equity / peak - 1.0) * 100
        if drawdown < float(worst["max_drawdown_pct"]):
            worst.update(
                {
                    "max_drawdown_pct": round(drawdown, 4),
                    "start_index": peak_index,
                    "trough_index": index,
                    "start_date": rows[peak_index].get("period", ""),
                    "trough_date": row.get("period", ""),
                    "recovery_date": "",
                    "recovery_rows": "",
                }
            )
    if worst["trough_index"] > worst["start_index"]:
        start_equity = float(rows[worst["start_index"]].get("metric_value", 0) or rows[worst["start_index"]].get("equity", 0) or 0)
        for recovery_index in range(int(worst["trough_index"]) + 1, len(rows)):
            equity = float(rows[recovery_index].get("metric_value", 0) or rows[recovery_index].get("equity", 0) or 0)
            if start_equity > 0 and equity >= start_equity:
                worst["recovery_date"] = rows[recovery_index].get("period", "")
                worst["recovery_rows"] = recovery_index - int(worst["trough_index"])
                break
    return worst


def overlap_drawdown(rows: list[dict[str, Any]], window: dict[str, Any]) -> float | None:
    if not rows or not window:
        return None
    by_date = {row.get("period", ""): row for row in rows}
    start_date = window.get("start_date", "")
    trough_date = window.get("trough_date", "")
    if start_date not in by_date or trough_date not in by_date:
        return None
    in_window = [row for row in rows if start_date <= row.get("period", "") <= trough_date]
    if not in_window:
        return None
    start_equity = float(by_date[start_date].get("metric_value", 0) or by_date[start_date].get("equity", 0) or 0)
    if start_equity <= 0:
        return None
    return round(min((float(row.get("metric_value", 0) or row.get("equity", 0) or 0) / start_equity - 1.0) * 100 for row in in_window), 4)


def window_text(window: dict[str, Any], key: str) -> str:
    if not window:
        return "unavailable"
    value = window.get(key, "")
    return str(value) if value != "" else "unrecovered"


def reduction_text(strategy_dd: float | None, reference_dd: float | None) -> str:
    if strategy_dd is None or reference_dd is None:
        return "unavailable"
    return str(round(float(strategy_dd) - float(reference_dd), 4))


def build_summary_rows(
    created_at: str,
    results: list[dict[str, Any]],
    costs: list[dict[str, Any]],
    splits: list[dict[str, Any]],
    drawdowns: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full = [row for row in results if row.get("section") == "cost_stress" and str(row.get("cost_bps")) == "10"]
    static = metric_for(full, "equal_weight_eligible_crypto_benchmark")
    crash = best_crash_gate(full)
    static_cagr = extract_metric(static.get("metric_value", ""), "CAGR")
    static_dd = extract_metric(static.get("metric_value", ""), "MaxDD")
    crash_cagr = extract_metric(crash.get("metric_value", ""), "CAGR")
    crash_dd = extract_metric(crash.get("metric_value", ""), "MaxDD")
    dd_reduction = crash_dd - static_dd
    return_drag = crash_cagr - static_cagr
    label = final_label(static, crash)
    return [
        common_row(created_at, "summary", "variants_tested", "variants", ", ".join(CRASH_GATE_VARIANTS), "", "manual_review_required", label, "Fixed variants only; no parameter search."),
        common_row(created_at, "summary", "best_by_cagr", "expanded_crypto", best_by(full, "CAGR"), "", "manual_review_required", label, "Full-period 10 bps comparison."),
        common_row(created_at, "summary", "best_by_sharpe", "expanded_crypto", best_by(full, "Sharpe"), "", "manual_review_required", label, "Full-period 10 bps comparison."),
        common_row(created_at, "summary", "best_by_calmar", "expanded_crypto", best_by(full, "Calmar"), "", "manual_review_required", label, "Full-period 10 bps comparison."),
        common_row(created_at, "summary", "lowest_max_drawdown", "expanded_crypto", lowest_drawdown(full), "", "manual_review_required", label, "Full-period 10 bps comparison."),
        common_row(created_at, "summary", "static_equal_weight_result", "equal_weight_eligible_crypto_benchmark", static.get("metric_value", "unavailable"), "", "manual_review_required", label, "Static equal-weight is high-return/high-drawdown benchmark."),
        common_row(created_at, "summary", "best_crash_gate_variant", crash.get("strategy_name", "unavailable"), crash.get("metric_value", "unavailable"), "", "manual_review_required", label, "Best crash-gate variant by Calmar."),
        common_row(created_at, "summary", "drawdown_reduction_vs_equal_weight", crash.get("strategy_name", "unavailable"), round(dd_reduction, 4), "", "manual_review_required", label, "Positive means max drawdown is less severe than static equal-weight."),
        common_row(created_at, "summary", "return_drag_vs_equal_weight", crash.get("strategy_name", "unavailable"), round(return_drag, 4), "", "manual_review_required", label, "Negative means lower CAGR than static equal-weight."),
        common_row(created_at, "summary", "cost_survival_summary", "expanded_crypto", status_counts(costs), "", "manual_review_required", label, "Cost-stress status counts."),
        common_row(created_at, "summary", "split_summary", "expanded_crypto", status_counts(splits), "", "manual_review_required", label, "Split status counts."),
        common_row(created_at, "summary", "final_summary_label", "crypto_equal_weight_crash_gate", label, "", label, label, "Final label is research-only and does not approve execution."),
    ]


def insufficient_rows(created_at: str, universe: list[str], universe_note: str, errors: dict[str, str]):
    evidence = f"fallback_static_crypto_universe_used={universe_note.startswith('fallback')}; universe={','.join(universe)}; " + "; ".join(f"{key}:{value}" for key, value in sorted(errors.items())[:5])
    row = common_row(
        created_at,
        "summary",
        "insufficient_saved_inputs",
        "input_status",
        "insufficient_saved_inputs",
        "",
        "insufficient_saved_inputs",
        "insufficient_saved_inputs",
        evidence,
    )
    summary = [
        common_row(created_at, "summary", "variants_tested", "variants", ", ".join(CRASH_GATE_VARIANTS), "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "best_by_cagr", "expanded_crypto", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "best_by_sharpe", "expanded_crypto", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "best_by_calmar", "expanded_crypto", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "lowest_max_drawdown", "expanded_crypto", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "static_equal_weight_result", "equal_weight_eligible_crypto_benchmark", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "best_crash_gate_variant", "crypto_equal_weight_crash_gate", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "drawdown_reduction_vs_equal_weight", "crypto_equal_weight_crash_gate", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "return_drag_vs_equal_weight", "crypto_equal_weight_crash_gate", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "cost_survival_summary", "expanded_crypto", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "split_summary", "expanded_crypto", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "final_summary_label", "crypto_equal_weight_crash_gate", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
    ]
    return [row], summary, [], [], [row], [row], [row]


def add_decays(metric: dict[str, Any], zero: dict[str, Any]) -> dict[str, Any]:
    metric["cagr_decay_vs_0_bps"] = round(float(metric["cagr_pct"]) - float(zero["cagr_pct"]), 4)
    metric["sharpe_decay_vs_0_bps"] = round(float(metric["sharpe_ratio"]) - float(zero["sharpe_ratio"]), 4)
    metric["calmar_decay_vs_0_bps"] = round(float(metric["calmar_ratio"]) - float(zero["calmar_ratio"]), 4)
    metric["survives_10_bps"] = metric["cost_bps"] == 10 and float(metric["cagr_pct"]) > 0 and float(metric["calmar_ratio"]) > 0
    metric["survives_25_bps"] = metric["cost_bps"] == 25 and float(metric["cagr_pct"]) > 0 and float(metric["calmar_ratio"]) > 0
    return metric


def to_common(created_at: str, section: str, metric: dict[str, Any], label: str, period: str | None = None) -> dict[str, Any]:
    metric_value = (
        f"CAGR={metric.get('cagr_pct', '')}; Sharpe={metric.get('sharpe_ratio', '')}; "
        f"Calmar={metric.get('calmar_ratio', '')}; MaxDD={metric.get('max_drawdown_pct', '')}; "
        f"cash={metric.get('cash_percentage', '')}; trades={metric.get('trade_count', '')}; turnover={metric.get('turnover', '')}"
    )
    evidence = (
        f"cost_bps={metric.get('cost_bps', '')}; cagr_decay={metric.get('cagr_decay_vs_0_bps', '')}; "
        f"sharpe_decay={metric.get('sharpe_decay_vs_0_bps', '')}; calmar_decay={metric.get('calmar_decay_vs_0_bps', '')}; "
        f"survives_10_bps={metric.get('survives_10_bps', '')}; survives_25_bps={metric.get('survives_25_bps', '')}; "
        f"{metric.get('reason', '')}"
    )
    return common_row(created_at, section, metric.get("strategy_name", ""), "metrics", metric_value, f"cost_bps={metric.get('cost_bps', '')}", label, label, evidence, period=period or metric.get("period", "full_period"), cost_bps=metric.get("cost_bps", ""))


def common_row(
    created_at: str,
    section: str,
    strategy_name: str,
    metric_name: str,
    metric_value: Any,
    reference_value: Any,
    status: str,
    summary_label: str,
    evidence: str,
    *,
    period: str = "",
    cost_bps: Any = "",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "crypto_equal_weight_crash_gate",
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
        return "crypto_crash_gate_not_useful"
    if metric.get("cost_bps") in {25, 50, 100} and cagr < 5:
        return "crypto_crash_gate_cost_sensitive"
    if maxdd > -65 and cagr > 15:
        return "crypto_crash_gate_promising"
    if maxdd > -70:
        return "crypto_crash_gate_drawdown_improved"
    return "manual_review_required"


def label_drawdown(dd: float, static_dd: float) -> str:
    if not dd:
        return "manual_review_required"
    if dd - static_dd < 10:
        return "crypto_crash_gate_not_useful"
    if dd > static_dd and dd > -70:
        return "crypto_crash_gate_drawdown_improved"
    return "manual_review_required"


def final_label(static: dict[str, Any], crash: dict[str, Any]) -> str:
    if not static or not crash:
        return "insufficient_saved_inputs"
    static_cagr = extract_metric(static.get("metric_value", ""), "CAGR")
    static_dd = extract_metric(static.get("metric_value", ""), "MaxDD")
    crash_cagr = extract_metric(crash.get("metric_value", ""), "CAGR")
    crash_dd = extract_metric(crash.get("metric_value", ""), "MaxDD")
    dd_improvement = crash_dd - static_dd
    cagr_drag = crash_cagr - static_cagr
    if dd_improvement < 10:
        return "equal_weight_still_best_high_drawdown"
    if cagr_drag < -35:
        return "crypto_crash_gate_return_drag_too_high"
    if dd_improvement >= 10 and crash_cagr > 15:
        return "crypto_crash_gate_new_defensive_crypto_candidate"
    return "manual_review_required"


def best_crash_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if row.get("strategy_name") in CRASH_GATE_VARIANTS and row.get("metric_value")]
    if not candidates:
        return {}
    return max(candidates, key=lambda row: extract_metric(row.get("metric_value", ""), "Calmar"))


def metric_for(rows: list[dict[str, Any]], strategy: str) -> dict[str, Any]:
    return next((row for row in rows if row.get("strategy_name") == strategy and str(row.get("cost_bps")) == "10"), {})


def summary_value(rows: list[dict[str, Any]], strategy_name: str) -> str:
    row = next((item for item in rows if item.get("strategy_name") == strategy_name), {})
    return str(row.get("metric_value", "unavailable"))


def best_by(rows: list[dict[str, Any]], metric_name: str) -> str:
    candidates = [row for row in rows if row.get("metric_value")]
    if not candidates:
        return "unavailable"
    best = max(candidates, key=lambda row: extract_metric(row.get("metric_value", ""), metric_name))
    return f"{best.get('strategy_name')}={extract_metric(best.get('metric_value', ''), metric_name)}"


def lowest_drawdown(rows: list[dict[str, Any]]) -> str:
    candidates = [row for row in rows if row.get("metric_value")]
    if not candidates:
        return "unavailable"
    best = max(candidates, key=lambda row: extract_metric(row.get("metric_value", ""), "MaxDD"))
    return f"{best.get('strategy_name')}={extract_metric(best.get('metric_value', ''), 'MaxDD')}"


def extract_metric(text: str, name: str) -> float:
    for part in text.split(";"):
        part = part.strip()
        prefix = f"{name}="
        if part.startswith(prefix):
            try:
                return float(part[len(prefix):])
            except ValueError:
                return 0.0
    return 0.0


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(row.get("status", "") for row in rows)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


def to_trade_rows(created_at: str, name: str, trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        common_row(created_at, "trades", name, "rebalance", trade.get("selected_symbols", ""), f"turnover={trade.get('turnover', '')}", "trade_recorded", "manual_review_required", trade.get("rebalance_reason", ""), period=str(trade.get("date", "")), cost_bps=trade.get("cost_bps", ""))
        for trade in trades
    ]


def to_equity_rows(created_at: str, name: str, cost_bps: int, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        common_row(created_at, "equity_curve", name, "equity", round(float(row.get("equity", 0)), 6), row.get("holdings", ""), "equity_row", "manual_review_required", f"cash_weight={row.get('cash_weight', '')}", period=row.get("date", ""), cost_bps=cost_bps)
        for row in rows
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Crypto equal-weight crash-gate report complete. Research/report only; execution_approved=False.",
        f"Variants tested: {summary_value(summary_rows, 'variants_tested')}",
        f"Best by CAGR: {summary_value(summary_rows, 'best_by_cagr')}",
        f"Best by Sharpe: {summary_value(summary_rows, 'best_by_sharpe')}",
        f"Best by Calmar: {summary_value(summary_rows, 'best_by_calmar')}",
        f"Lowest max drawdown: {summary_value(summary_rows, 'lowest_max_drawdown')}",
        f"Static equal-weight comparison: {summary_value(summary_rows, 'static_equal_weight_result')}",
        f"Best crash-gate variant: {summary_value(summary_rows, 'best_crash_gate_variant')}",
        f"Drawdown reduction versus equal-weight: {summary_value(summary_rows, 'drawdown_reduction_vs_equal_weight')}",
        f"Return drag versus equal-weight: {summary_value(summary_rows, 'return_drag_vs_equal_weight')}",
        f"Final summary label: {summary_value(summary_rows, 'final_summary_label')}",
        f"Saved results to {paths['results']}",
        f"Saved summary to {paths['summary']}",
        f"Saved trades to {paths['trades']}",
        f"Saved equity curves to {paths['equity']}",
        f"Saved costs to {paths['costs']}",
        f"Saved splits to {paths['splits']}",
        f"Saved drawdowns to {paths['drawdowns']}",
        "Warning: crash-gate report does not approve crypto execution, paper execution, scheduling, or strategy-to-execution wiring.",
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
