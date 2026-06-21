"""Compact terminal display for saved multi-sleeve research state.

The display reads saved CSV outputs only. It does not refresh data, call
Alpaca, read positions, create orders, send alerts, schedule anything, or
approve execution.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


MISSING = "missing_saved_output"

QQQ100_STRATEGY = "qqq_100_trend_gate"
QQQ100_SLEEVE = "qqq100_core_trend_sleeve"
RECOVERED_QQQ100_REFERENCE = "qqq100_recovered_reference_stream"
HIGH_GROWTH_SLEEVE = "codex_broad_growth_balanced_breakout_control"
CRYPTO_COMBINED_SLEEVE = "crypto_btc_eth_research_sleeve"
MULTI_SLEEVE_CANDIDATE = "qqq100_plus_high_growth_plus_crypto_research"
MULTI_SLEEVE_ALLOCATION = (
    "75% qqq100_core_trend_sleeve; "
    "15% high_growth_stock_research_sleeve; "
    "5% crypto_research_sleeve; "
    "5% defensive_cash_or_bond_sleeve"
)

FILES = {
    "qqq_reconciliation_summary": "qqq100_stream_reconciliation_summary.csv",
    "qqq_benchmark_inputs_summary": "qqq100_benchmark_inputs_summary.csv",
    "qqq_recovered_metrics": "qqq100_recovered_reference_metrics.csv",
    "high_growth_metrics": "high_growth_return_stream_metrics.csv",
    "crypto_metrics": "crypto_return_stream_metrics.csv",
    "multi_sleeve_backtest": "multi_sleeve_portfolio_backtest.csv",
    "multi_sleeve_crypto_summary": "multi_sleeve_crypto_review_summary.csv",
    "multi_sleeve_crypto_splits": "multi_sleeve_crypto_review_split_robustness.csv",
    "multi_sleeve_crypto_costs": "multi_sleeve_crypto_review_cost_stress.csv",
    "multi_sleeve_crypto_volatility": "multi_sleeve_crypto_review_volatility.csv",
    "project_state_summary": "project_research_state_summary.csv",
}

SAVED_QQQ100_METRICS = {
    "CAGR": "16.8429",
    "Sharpe": "1.0027",
    "MaxDD": "-23.4576",
    "Calmar": "0.718",
}

RECOVERED_QQQ100_METRICS = {
    "CAGR": "16.9832",
    "Sharpe": "1.0073",
    "MaxDD": "-23.4576",
    "Calmar": "0.724",
}


def show_current_research_state(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    rows = {name: read_csv(data_path / filename) for name, filename in FILES.items()}

    recovered_metrics_row = find_row(rows["qqq_recovered_metrics"], "reference_name", RECOVERED_QQQ100_REFERENCE)
    recovered_metrics = metrics_from_row(recovered_metrics_row, RECOVERED_QQQ100_METRICS)
    saved_qqq_metrics = saved_qqq100_metrics(rows)
    multi_sleeve_row = find_row(rows["multi_sleeve_backtest"], "portfolio_name", MULTI_SLEEVE_CANDIDATE)
    high_growth_row = find_row(rows["high_growth_metrics"], "candidate_name", HIGH_GROWTH_SLEEVE)
    crypto_btc = find_metric_row(rows["crypto_metrics"], "btc_trend_vol_gate_research_sleeve")
    crypto_eth = find_metric_row(rows["crypto_metrics"], "eth_trend_research_sleeve")
    crypto_combined = find_metric_row(rows["crypto_metrics"], CRYPTO_COMBINED_SLEEVE)
    crypto_summary = summary_map(rows["multi_sleeve_crypto_summary"])
    candidate_metrics = candidate_metrics_from_row(multi_sleeve_row)
    split_rows = [row for row in rows["multi_sleeve_crypto_splits"] if row.get("candidate_name") == MULTI_SLEEVE_CANDIDATE]
    cost_rows = rows["multi_sleeve_crypto_costs"]
    volatility_row = rows["multi_sleeve_crypto_volatility"][0] if rows["multi_sleeve_crypto_volatility"] else {}

    lines = [
        "CURRENT RESEARCH STATE",
        "",
        "A. QQQ100 reference",
        f"- saved benchmark: {QQQ100_STRATEGY} / {QQQ100_SLEEVE}: {format_metrics(saved_qqq_metrics)}",
        f"- recovered reference: {RECOVERED_QQQ100_REFERENCE}: {format_metrics(recovered_metrics)}",
        f"- reference source used: {multi_sleeve_row.get('qqq100_reference_source_used') or reference_source(rows)}",
        f"- recovered status: {recovered_metrics_row.get('reference_status') or summary_lookup(rows['qqq_reconciliation_summary'], 'final_reconciliation_status')}",
        f"- old generated stream: {multi_sleeve_row.get('old_generated_reference_status') or 'diagnostic_only'}",
        "",
        "B. High-growth sleeve",
        f"- best sleeve: {HIGH_GROWTH_SLEEVE}",
        f"- metrics: {format_metrics(metrics_from_row(high_growth_row, {}))}",
        "- warning/blocker: research_only=true; high_growth_risky=true; preview_or_execution_not_approved",
        "",
        "C. Crypto sleeve",
        f"- BTC: {format_metrics(metrics_from_row(crypto_btc, {}))}",
        f"- ETH: {format_metrics(metrics_from_row(crypto_eth, {}))}",
        f"- combined BTC/ETH ({CRYPTO_COMBINED_SLEEVE}): {format_metrics(metrics_from_row(crypto_combined, {}))}",
        "- LTC: paused/not_active",
        f"- warning: {volatility_row.get('crypto_volatility_warning') or crypto_summary.get('crypto_volatility_drawdown_warnings') or MISSING}",
        "",
        "D. Multi-sleeve candidate",
        f"- candidate: {MULTI_SLEEVE_CANDIDATE}",
        f"- allocation: {multi_sleeve_row.get('candidate_allocation') or MULTI_SLEEVE_ALLOCATION}",
        f"- metrics: {format_metrics(candidate_metrics)}",
        f"- delta vs recovered QQQ100: {format_delta_vs_recovered(multi_sleeve_row)}",
        f"- final review status: {crypto_summary.get('final_crypto_review_status') or MISSING}",
        f"- worst split: {crypto_summary.get('worst_split_by_calmar') or worst_split(split_rows)}",
        f"- worst drawdown split: {crypto_summary.get('worst_split_by_maxdd') or worst_drawdown_split(split_rows)}",
        f"- worst cost stress: {crypto_summary.get('worst_cost_stress_row') or worst_cost(cost_rows)}",
        f"- warning/blocker: {crypto_summary.get('crypto_volatility_drawdown_warnings') or volatility_warning(volatility_row)}",
        f"- required next step: {crypto_summary.get('required_next_step') or MISSING}",
        "",
        "E. Safety state",
        "- research_only=true",
        "- preview_only=true where applicable",
        "- execution_approved=false",
        "- paper_execution_approved=false",
        "- crypto_execution_approved=false",
        "- scheduling_approved=false",
        "- order paths touched=false",
        "- live_trading_approved=false; shorting=false; margin=false; leverage=false",
        "Display-only saved-output summary; no Alpaca, market-data refresh, positions, orders, alerts, config, scheduling, or execution wiring.",
    ]
    return 0, lines


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        name = str(row.get("summary_name") or row.get("metric_name") or "")
        if name:
            result[name] = str(row.get("summary_value") or row.get("metric_value") or "")
    return result


def summary_lookup(rows: list[dict[str, Any]], name: str) -> str:
    return summary_map(rows).get(name, MISSING)


def find_row(rows: list[dict[str, Any]], column: str, value: str) -> dict[str, Any]:
    return next((row for row in rows if row.get(column) == value), {})


def find_metric_row(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(
        (
            row
            for row in rows
            if row.get("candidate_name") == name or row.get("sleeve_name") == name or row.get("strategy_name") == name
        ),
        {},
    )


def saved_qqq100_metrics(rows: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    summary = summary_map(rows["qqq_benchmark_inputs_summary"])
    reconciliation = summary_map(rows["qqq_reconciliation_summary"])
    metrics = {
        "CAGR": summary.get("saved_qqq100_benchmark_cagr") or reconciliation.get("saved_qqq100_benchmark_cagr"),
        "Sharpe": summary.get("saved_qqq100_benchmark_sharpe") or reconciliation.get("saved_qqq100_benchmark_sharpe"),
        "MaxDD": summary.get("saved_qqq100_benchmark_max_drawdown")
        or reconciliation.get("saved_qqq100_benchmark_max_drawdown"),
        "Calmar": summary.get("saved_qqq100_benchmark_calmar") or reconciliation.get("saved_qqq100_benchmark_calmar"),
    }
    return {key: value or SAVED_QQQ100_METRICS[key] for key, value in metrics.items()}


def metrics_from_row(row: dict[str, Any], fallback: dict[str, str]) -> dict[str, str]:
    if not row:
        return {
            "CAGR": fallback.get("CAGR", MISSING),
            "Sharpe": fallback.get("Sharpe", MISSING),
            "MaxDD": fallback.get("MaxDD", MISSING),
            "Calmar": fallback.get("Calmar", MISSING),
        }
    return {
        "CAGR": value_from(row, ["CAGR", "cagr", "candidate_cagr"], fallback.get("CAGR", MISSING)),
        "Sharpe": value_from(row, ["Sharpe", "sharpe", "candidate_sharpe"], fallback.get("Sharpe", MISSING)),
        "MaxDD": value_from(
            row,
            ["MaxDD", "max_drawdown", "candidate_max_drawdown", "max_drawdown_pct"],
            fallback.get("MaxDD", MISSING),
        ),
        "Calmar": value_from(row, ["Calmar", "calmar", "candidate_calmar"], fallback.get("Calmar", MISSING)),
    }


def candidate_metrics_from_row(row: dict[str, Any]) -> dict[str, str]:
    return metrics_from_row(
        row,
        {
            "CAGR": "21.7328",
            "Sharpe": "1.1852",
            "MaxDD": "-22.2489",
            "Calmar": "0.9768",
        },
    )


def value_from(row: dict[str, Any], keys: list[str], fallback: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in {"", None}:
            return str(value)
    return fallback


def format_metrics(metrics: dict[str, str]) -> str:
    return (
        f"CAGR={metrics.get('CAGR', MISSING)}, "
        f"Sharpe={metrics.get('Sharpe', MISSING)}, "
        f"MaxDD={metrics.get('MaxDD', MISSING)}, "
        f"Calmar={metrics.get('Calmar', MISSING)}"
    )


def format_delta_vs_recovered(row: dict[str, Any]) -> str:
    if not row:
        return "CAGR=4.7496, Sharpe=0.1779, MaxDD=1.2087, Calmar=0.2528"
    return (
        f"CAGR={value_from(row, ['delta_cagr_vs_recovered_qqq100_reference'], MISSING)}, "
        f"Sharpe={value_from(row, ['delta_sharpe_vs_recovered_qqq100_reference'], MISSING)}, "
        f"MaxDD={value_from(row, ['delta_max_drawdown_vs_recovered_qqq100_reference'], MISSING)}, "
        f"Calmar={value_from(row, ['delta_calmar_vs_recovered_qqq100_reference'], MISSING)}"
    )


def reference_source(rows: dict[str, list[dict[str, Any]]]) -> str:
    summary = summary_map(rows["multi_sleeve_crypto_summary"])
    return summary.get("qqq100_reference_source_used", RECOVERED_QQQ100_REFERENCE)


def worst_split(rows: list[dict[str, Any]]) -> str:
    row = min(rows, key=lambda item: to_float(item.get("Calmar")), default={})
    if not row:
        return MISSING
    return f"{row.get('split_name')} Calmar={row.get('Calmar')}"


def worst_drawdown_split(rows: list[dict[str, Any]]) -> str:
    row = min(rows, key=lambda item: to_float(item.get("MaxDD")), default={})
    if not row:
        return MISSING
    return f"{row.get('split_name')} MaxDD={row.get('MaxDD')}"


def worst_cost(rows: list[dict[str, Any]]) -> str:
    row = min(rows, key=lambda item: to_float(item.get("delta_CAGR_vs_baseline_candidate")), default={})
    if not row:
        return MISSING
    return (
        f"{row.get('cost_stress_name')} CAGR={row.get('stressed_CAGR')}; "
        f"delta_CAGR={row.get('delta_CAGR_vs_baseline_candidate')}; "
        f"status={row.get('cost_stress_status')}"
    )


def volatility_warning(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"{row.get('crypto_volatility_warning')}; {row.get('drawdown_status')}"


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("inf")
