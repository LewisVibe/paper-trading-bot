"""Fixed neighbourhood check for the stricter growth-biased breadth gate.

This is research/report-only. It uses existing strategy-improvement lab helpers
for daily ETF history and fixed monthly simulation, writes generated research
CSVs, and never touches broker, position, SQLite, alert, scheduler, or
execution paths.
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
    BREADTH_STRICTER_GATE,
    DEFENSIVE_EXPOSURE_ETFS,
    RISK_EXPOSURE_ETFS,
    STARTING_EQUITY,
    align_price_rows,
    apply_benchmark_comparisons,
    build_result_rows_for_strategy,
    build_summary_rows,
    build_trade_rows,
    download_daily_price_data,
    growth_biased_breadth_gate_weights,
    simulate_strategy,
    sufficient_history,
    weighted_daily_return,
)


ACTIVE_RESEARCH_LEAD = "growth_biased_rotation_breadth_stricter_gate"
PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"
MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"
SPY_BENCHMARK = "spy_buy_and_hold_benchmark"
EQUAL_WEIGHT_BENCHMARK = "equal_weight_etf_buy_and_hold_benchmark"

THRESHOLDS = [0.40, 0.45, 0.50, 0.55, 0.60]
REFERENCE_STRATEGIES = [
    SPY_BENCHMARK,
    EQUAL_WEIGHT_BENCHMARK,
    MONTHLY_ROTATION_REFERENCE,
    PREVIOUS_RESEARCH_LEAD,
]

OUTPUT_FILES = {
    "detail": Path("data/growth_biased_stricter_threshold_neighbourhood.csv"),
    "summary": Path("data/growth_biased_stricter_threshold_neighbourhood_summary.csv"),
}

DETAIL_COLUMNS = [
    "created_at",
    "strategy_name",
    "threshold_pct",
    "threshold_fraction",
    "threshold_mapping",
    "period",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "average_cash_weight_pct",
    "trade_count",
    "turnover",
    "cost_assumption",
    "cagr_delta_vs_original",
    "sharpe_delta_vs_original",
    "calmar_delta_vs_original",
    "max_drawdown_delta_vs_original",
    "cagr_gap_vs_spy",
    "sharpe_gap_vs_spy",
    "calmar_gap_vs_spy",
    "rank_by_calmar",
    "rank_by_sharpe",
    "rank_by_cagr",
    "status",
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
    "active_research_lead",
    "tested_thresholds_pct",
    "current_gate_threshold_pct",
    "best_threshold_by_calmar_pct",
    "best_threshold_by_sharpe_pct",
    "best_threshold_by_cagr_pct",
    "summary_label",
    "cluster_thresholds_pct",
    "current_gate_inside_cluster",
    "benchmark_gap_vs_spy",
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
class ThresholdNeighbourhoodResult:
    detail_path: Path
    summary_path: Path
    detail_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_growth_biased_stricter_threshold_neighbourhood(
    data_dir: Path | str = "data",
) -> ThresholdNeighbourhoodResult:
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
        detail_rows, summary_rows = build_threshold_outputs(created_at, aligned_rows)

    write_rows(output_paths["detail"], DETAIL_COLUMNS, detail_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    return ThresholdNeighbourhoodResult(
        detail_path=output_paths["detail"],
        summary_path=output_paths["summary"],
        detail_rows=detail_rows,
        summary_rows=summary_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def build_threshold_outputs(
    created_at: str,
    aligned_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    result_rows: list[dict[str, Any]] = []
    for strategy_name in REFERENCE_STRATEGIES:
        equity_rows, trade_rows = simulate_strategy(strategy_name, aligned_rows, created_at)
        result_rows.extend(build_result_rows_for_strategy(created_at, strategy_name, equity_rows, trade_rows))

    for threshold in THRESHOLDS:
        strategy_name = threshold_strategy_name(threshold)
        equity_rows, trade_rows = simulate_threshold_strategy(strategy_name, threshold, aligned_rows, created_at)
        result_rows.extend(build_result_rows_for_strategy(created_at, strategy_name, equity_rows, trade_rows))

    apply_benchmark_comparisons(result_rows)
    summary_rows = build_summary_rows(result_rows)
    detail_rows = build_detail_rows(created_at, summary_rows, result_rows)
    summary = build_neighbourhood_summary(created_at, detail_rows)
    return detail_rows, [summary]


def simulate_threshold_strategy(
    strategy_name: str,
    threshold: float,
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
            target_weights, reason, regime = growth_biased_breadth_gate_weights(
                history,
                current_weights,
                threshold,
                f"neighbour_{int(round(threshold * 100))}",
            )
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


def build_detail_rows(
    created_at: str,
    summary_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full_rows = {row.get("strategy_name"): row for row in summary_rows if row.get("period") == "full_period"}
    original = full_rows.get(PREVIOUS_RESEARCH_LEAD, {})
    spy = full_rows.get(SPY_BENCHMARK, {})
    threshold_rows = [full_rows.get(threshold_strategy_name(threshold), {}) for threshold in THRESHOLDS]
    ranked_calmar = rank_by(threshold_rows, "calmar_ratio")
    ranked_sharpe = rank_by(threshold_rows, "sharpe_ratio")
    ranked_cagr = rank_by(threshold_rows, "cagr_pct")

    rows = []
    for threshold in THRESHOLDS:
        strategy_name = threshold_strategy_name(threshold)
        full = full_rows.get(strategy_name, {})
        oos = find_result_row(result_rows, strategy_name, "out_of_sample")
        status, warning = classify_threshold(full, original, spy, oos)
        rows.append(
            {
                "created_at": created_at,
                "strategy_name": strategy_name,
                "threshold_pct": int(round(threshold * 100)),
                "threshold_fraction": threshold,
                "threshold_mapping": (
                    "Threshold pct maps to growth_biased_breadth_gate_weights breadth_gate; "
                    f"current active stricter gate is {int(round(BREADTH_STRICTER_GATE * 100))}%."
                ),
                "period": "full_period",
                "cagr_pct": full.get("cagr_pct", ""),
                "sharpe_ratio": full.get("sharpe_ratio", ""),
                "max_drawdown_pct": full.get("max_drawdown_pct", ""),
                "calmar_ratio": full.get("calmar_ratio", ""),
                "average_cash_weight_pct": full.get("average_cash_weight_pct", ""),
                "trade_count": full.get("trade_count", ""),
                "turnover": full.get("turnover", ""),
                "cost_assumption": "strategy_improvement_lab_default_no_extra_cost_stress",
                "cagr_delta_vs_original": delta(full, original, "cagr_pct"),
                "sharpe_delta_vs_original": delta(full, original, "sharpe_ratio"),
                "calmar_delta_vs_original": delta(full, original, "calmar_ratio"),
                "max_drawdown_delta_vs_original": delta(full, original, "max_drawdown_pct"),
                "cagr_gap_vs_spy": delta(full, spy, "cagr_pct"),
                "sharpe_gap_vs_spy": delta(full, spy, "sharpe_ratio"),
                "calmar_gap_vs_spy": delta(full, spy, "calmar_ratio"),
                "rank_by_calmar": ranked_calmar.get(strategy_name, ""),
                "rank_by_sharpe": ranked_sharpe.get(strategy_name, ""),
                "rank_by_cagr": ranked_cagr.get(strategy_name, ""),
                "status": status,
                "review_warning": warning,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
                "paper_execution_approved": False,
                "promotion_approved": False,
                "scheduling_approved": False,
            }
        )
    return rows


def build_neighbourhood_summary(created_at: str, detail_rows: list[dict[str, Any]]) -> dict[str, Any]:
    credible = [
        row
        for row in detail_rows
        if row.get("status") in {"threshold_credible", "threshold_strong"} and as_float(row.get("calmar_delta_vs_original")) >= 0
    ]
    cluster_thresholds = [int(row["threshold_pct"]) for row in credible]
    current_inside_cluster = int(round(BREADTH_STRICTER_GATE * 100)) in cluster_thresholds
    best_calmar = best_row(detail_rows, "calmar_ratio")
    best_sharpe = best_row(detail_rows, "sharpe_ratio")
    best_cagr = best_row(detail_rows, "cagr_pct")
    warnings = sorted({str(row.get("review_warning", "")) for row in detail_rows if row.get("review_warning")})
    spy_gap = best_calmar.get("cagr_gap_vs_spy", "")

    if not detail_rows or any(row.get("status") == "insufficient_saved_inputs" for row in detail_rows):
        label = "insufficient_saved_inputs"
    elif current_inside_cluster and len(cluster_thresholds) >= 3:
        label = "robust_neighbourhood_cluster"
    elif current_inside_cluster and len(cluster_thresholds) >= 2:
        label = "promising_but_threshold_sensitive"
    elif len(cluster_thresholds) == 1:
        label = "one_threshold_dependency"
    elif as_float(spy_gap) < 0 and cluster_thresholds:
        label = "benchmark_lagging_but_active_cluster_improved"
    else:
        label = "manual_review_required"

    return {
        "created_at": created_at,
        "summary_name": "growth_biased_stricter_threshold_neighbourhood",
        "active_research_lead": ACTIVE_RESEARCH_LEAD,
        "tested_thresholds_pct": ",".join(str(int(threshold * 100)) for threshold in THRESHOLDS),
        "current_gate_threshold_pct": int(round(BREADTH_STRICTER_GATE * 100)),
        "best_threshold_by_calmar_pct": best_calmar.get("threshold_pct", ""),
        "best_threshold_by_sharpe_pct": best_sharpe.get("threshold_pct", ""),
        "best_threshold_by_cagr_pct": best_cagr.get("threshold_pct", ""),
        "summary_label": label,
        "cluster_thresholds_pct": ",".join(str(value) for value in cluster_thresholds),
        "current_gate_inside_cluster": current_inside_cluster,
        "benchmark_gap_vs_spy": spy_gap,
        "review_warnings": "; ".join(warnings) if warnings else "none",
        "interpretation": "Fixed neighbourhood check only; not a broad parameter search and not promotion approval.",
        "required_next_step": "Manual research review of threshold cluster before any preview-candidate discussion.",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "promotion_approved": False,
        "scheduling_approved": False,
    }


def classify_threshold(
    row: dict[str, Any],
    original: dict[str, Any],
    spy: dict[str, Any],
    oos: dict[str, Any] | None,
) -> tuple[str, str]:
    if not row:
        return "insufficient_saved_inputs", "missing_threshold_result"
    cagr_delta = delta_float(row, original, "cagr_pct")
    sharpe_delta = delta_float(row, original, "sharpe_ratio")
    calmar_delta = delta_float(row, original, "calmar_ratio")
    drawdown_delta = delta_float(row, original, "max_drawdown_pct")
    turnover = as_float(row.get("turnover"))
    spy_gap = delta_float(row, spy, "cagr_pct")
    oos_calmar = as_float(oos.get("calmar_ratio")) if oos else 0.0

    warnings = []
    if drawdown_delta < -5 and calmar_delta <= 0:
        warnings.append("severe_drawdown_expansion_without_calmar_gain")
    if turnover > 20:
        warnings.append("extreme_turnover_review")
    if oos and oos_calmar < as_float(row.get("calmar_ratio")) * 0.35:
        warnings.append("oos_decay_review")
    if spy_gap < 0:
        warnings.append("still_lags_spy")

    if cagr_delta > 0 and sharpe_delta >= 0 and calmar_delta >= 0:
        return "threshold_strong", "; ".join(warnings)
    if cagr_delta > 0 and (sharpe_delta >= -0.03 or calmar_delta >= -0.03):
        return "threshold_credible", "; ".join(warnings)
    return "manual_review_required", "; ".join(warnings or ["weak_vs_original"])


def insufficient_detail_rows(created_at: str, data_errors: dict[str, str]) -> list[dict[str, Any]]:
    evidence = "; ".join(f"{ticker}: {error}" for ticker, error in sorted(data_errors.items())[:8]) or "No aligned daily data."
    return [
        {
            "created_at": created_at,
            "strategy_name": threshold_strategy_name(threshold),
            "threshold_pct": int(round(threshold * 100)),
            "threshold_fraction": threshold,
            "threshold_mapping": "Threshold pct maps to breadth_gate.",
            "period": "full_period",
            "status": "insufficient_saved_inputs",
            "review_warning": evidence,
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
            "paper_execution_approved": False,
            "promotion_approved": False,
            "scheduling_approved": False,
        }
        for threshold in THRESHOLDS
    ]


def insufficient_summary_rows(created_at: str, data_errors: dict[str, str]) -> list[dict[str, Any]]:
    warnings = "; ".join(f"{ticker}: {error}" for ticker, error in sorted(data_errors.items())[:8]) or "No aligned daily data."
    return [
        {
            "created_at": created_at,
            "summary_name": "growth_biased_stricter_threshold_neighbourhood",
            "active_research_lead": ACTIVE_RESEARCH_LEAD,
            "tested_thresholds_pct": ",".join(str(int(threshold * 100)) for threshold in THRESHOLDS),
            "current_gate_threshold_pct": int(round(BREADTH_STRICTER_GATE * 100)),
            "summary_label": "insufficient_saved_inputs",
            "cluster_thresholds_pct": "",
            "current_gate_inside_cluster": False,
            "benchmark_gap_vs_spy": "",
            "review_warnings": warnings,
            "interpretation": "Could not build threshold neighbourhood because daily market data was unavailable.",
            "required_next_step": "Rerun after yfinance/cache data is available; do not approve execution.",
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
            "paper_execution_approved": False,
            "promotion_approved": False,
            "scheduling_approved": False,
        }
    ]


def show_growth_biased_stricter_threshold_neighbourhood_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    detail = read_csv(data_path / OUTPUT_FILES["detail"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    if not detail or not summary:
        return 1, ["Run `python bot.py --growth-biased-stricter-threshold-neighbourhood` first."]

    first_summary = summary[0]
    approval_values = {str(row.get("execution_approved", "")).lower() for row in detail + summary}
    return 0, [
        "Growth-biased stricter threshold neighbourhood. Display only; execution_approved=False.",
        f"Best threshold by Calmar: {format_threshold_pct(first_summary.get('best_threshold_by_calmar_pct', ''))}",
        f"Best threshold by Sharpe: {format_threshold_pct(first_summary.get('best_threshold_by_sharpe_pct', ''))}",
        f"Best threshold by CAGR: {format_threshold_pct(first_summary.get('best_threshold_by_cagr_pct', ''))}",
        f"Current stricter gate inside robust cluster: {first_summary.get('current_gate_inside_cluster', False)}",
        f"Summary label: {first_summary.get('summary_label', 'insufficient_saved_inputs')}",
        f"Benchmark gap versus SPY: {first_summary.get('benchmark_gap_vs_spy', '')}",
        f"Review warnings: {first_summary.get('review_warnings', '')}",
        f"execution_approved values: {', '.join(sorted(approval_values)) or 'false'}",
        "Warning: threshold neighbourhood is research-only and does not approve orders, preview promotion, scheduling, or execution.",
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    summary = summary_rows[0] if summary_rows else {}
    return [
        "Growth-biased stricter threshold neighbourhood complete. Research/report only; execution_approved=False.",
        f"Thresholds tested: {summary.get('tested_thresholds_pct', '')}",
        f"Best threshold by Calmar: {format_threshold_pct(summary.get('best_threshold_by_calmar_pct', ''))}",
        f"Best threshold by Sharpe: {format_threshold_pct(summary.get('best_threshold_by_sharpe_pct', ''))}",
        f"Best threshold by CAGR: {format_threshold_pct(summary.get('best_threshold_by_cagr_pct', ''))}",
        f"Current stricter gate inside robust cluster: {summary.get('current_gate_inside_cluster', False)}",
        f"Summary label: {summary.get('summary_label', 'insufficient_saved_inputs')}",
        f"Saved threshold detail to {output_paths['detail']}",
        f"Saved threshold summary to {output_paths['summary']}",
        "Warning: fixed neighbourhood check does not approve orders, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def threshold_strategy_name(threshold: float) -> str:
    if abs(threshold - BREADTH_STRICTER_GATE) < 0.000001:
        return ACTIVE_RESEARCH_LEAD
    return f"growth_biased_rotation_breadth_gate_{int(round(threshold * 100))}"


def format_threshold_pct(value: Any) -> str:
    text = str(value).strip()
    return f"{text}%" if text else "unavailable"


def rank_by(rows: list[dict[str, Any]], metric: str) -> dict[str, int]:
    ranked = sorted([row for row in rows if row], key=lambda row: as_float(row.get(metric)), reverse=True)
    return {str(row.get("strategy_name")): index for index, row in enumerate(ranked, start=1)}


def best_row(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    return max(rows, key=lambda row: as_float(row.get(metric)), default={})


def find_result_row(rows: list[dict[str, Any]], strategy_name: str, period: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("strategy_name") == strategy_name and row.get("period") == period:
            return row
    return None


def delta(row: dict[str, Any], reference: dict[str, Any], column: str) -> Any:
    if not row or not reference:
        return ""
    return round(delta_float(row, reference, column), 4)


def delta_float(row: dict[str, Any], reference: dict[str, Any], column: str) -> float:
    return as_float(row.get(column)) - as_float(reference.get(column))


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
