"""Saved-CSV diagnostics for the strategy improvement research lab.

This module reads generated strategy-improvement CSVs only. It does not refresh
market data, load config, call brokers, read positions, write SQLite, send
alerts, add strategies, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET_STRATEGY = "growth_biased_rotation_crash_gate"
COST_AWARE_STRATEGY = "growth_biased_rotation_cost_aware_rebalance"
PARTIAL_DEFENSIVE_STRATEGY = "growth_biased_rotation_partial_defensive_sleeve"
REENTRY_FILTER_STRATEGY = "growth_biased_rotation_reentry_filter"
RECOVERY_FILTER_STRATEGY = "growth_biased_rotation_regime_recovery_filter"
BREADTH_LOOSER_STRATEGY = "growth_biased_rotation_breadth_looser_gate"
BREADTH_STRICTER_STRATEGY = "growth_biased_rotation_breadth_stricter_gate"
ACTIVE_RESEARCH_LEAD = BREADTH_STRICTER_STRATEGY
PREVIOUS_RESEARCH_LEAD = TARGET_STRATEGY
REMAINING_REFINEMENT_STRATEGIES = [
    REENTRY_FILTER_STRATEGY,
    RECOVERY_FILTER_STRATEGY,
    BREADTH_LOOSER_STRATEGY,
    BREADTH_STRICTER_STRATEGY,
]
ACTIVE_REFERENCE = "monthly_etf_momentum_rotation_reference"
COMPARISON_STRATEGIES = [
    "spy_buy_and_hold_benchmark",
    "equal_weight_etf_buy_and_hold_benchmark",
    ACTIVE_REFERENCE,
    "breadth_aware_risk_on_rotation",
    "adaptive_multi_sleeve_growth_allocator",
    COST_AWARE_STRATEGY,
    PARTIAL_DEFENSIVE_STRATEGY,
    REENTRY_FILTER_STRATEGY,
    RECOVERY_FILTER_STRATEGY,
    BREADTH_LOOSER_STRATEGY,
    BREADTH_STRICTER_STRATEGY,
]

INPUT_FILES = {
    "lab_results": Path("data/strategy_improvement_lab_results.csv"),
    "lab_trades": Path("data/strategy_improvement_lab_trades.csv"),
    "lab_equity": Path("data/strategy_improvement_lab_equity_curve.csv"),
    "lab_summary": Path("data/strategy_improvement_lab_summary.csv"),
    "robustness": Path("data/strategy_improvement_robustness_report.csv"),
    "cost": Path("data/strategy_improvement_cost_stress_report.csv"),
    "drawdown": Path("data/strategy_improvement_drawdown_report.csv"),
    "comparison": Path("data/strategy_improvement_candidate_comparison.csv"),
}

OUTPUT_FILES = {
    "diagnostics": Path("data/strategy_improvement_diagnostics.csv"),
    "growth": Path("data/growth_biased_rotation_diagnostics.csv"),
}

DIAGNOSTIC_COLUMNS = [
    "created_at",
    "strategy_name",
    "diagnostic_type",
    "diagnostic_name",
    "period",
    "split_name",
    "comparison_strategy",
    "metric_name",
    "metric_value",
    "reference_value",
    "metric_delta",
    "status",
    "severity",
    "evidence",
    "interpretation",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
]


@dataclass
class StrategyImprovementDiagnosticsResult:
    diagnostics_path: Path
    growth_diagnostics_path: Path
    diagnostic_rows: list[dict[str, Any]]
    growth_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_strategy_improvement_diagnostics(
    root_dir: Path | str = ".",
) -> StrategyImprovementDiagnosticsResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(root / path) for name, path in INPUT_FILES.items()}
    missing = [str(path) for name, path in INPUT_FILES.items() if not inputs[name]]

    if missing:
        rows = build_insufficient_rows(created_at, missing)
    else:
        rows = build_diagnostic_rows(created_at, inputs)

    growth_rows = [
        row
        for row in rows
        if row["strategy_name"] in {TARGET_STRATEGY, COST_AWARE_STRATEGY, PARTIAL_DEFENSIVE_STRATEGY, *REMAINING_REFINEMENT_STRATEGIES}
    ]
    diagnostics_path = root / OUTPUT_FILES["diagnostics"]
    growth_path = root / OUTPUT_FILES["growth"]
    write_rows(diagnostics_path, rows)
    write_rows(growth_path, growth_rows)
    return StrategyImprovementDiagnosticsResult(
        diagnostics_path=diagnostics_path,
        growth_diagnostics_path=growth_path,
        diagnostic_rows=rows,
        growth_rows=growth_rows,
        summary_lines=build_summary_lines(rows, diagnostics_path, growth_path),
    )


def build_diagnostic_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target_full = find_row(inputs["lab_summary"], TARGET_STRATEGY)
    comparison_rows = inputs["comparison"]
    robustness_rows = [row for row in inputs["robustness"] if row.get("strategy_name") == TARGET_STRATEGY]
    cost_rows = [row for row in inputs["cost"] if row.get("strategy_name") == TARGET_STRATEGY]
    drawdown_row = find_row(inputs["drawdown"], TARGET_STRATEGY)
    equity_rows = [row for row in inputs["lab_equity"] if row.get("strategy_name") == TARGET_STRATEGY]

    if not target_full:
        return build_insufficient_rows(created_at, ["growth_biased row missing from data/strategy_improvement_lab_summary.csv"])

    rows.extend(split_sensitivity_rows(created_at, target_full, robustness_rows))
    rows.extend(benchmark_relative_rows(created_at, target_full, inputs["lab_summary"]))
    rows.extend(cost_sensitivity_rows(created_at, cost_rows, inputs["cost"]))
    rows.extend(drawdown_rows(created_at, target_full, drawdown_row, equity_rows, inputs["drawdown"]))
    rows.extend(cash_drag_rows(created_at, target_full, inputs["lab_summary"]))
    rows.extend(candidate_status_rows(created_at, target_full, comparison_rows, robustness_rows, cost_rows, drawdown_row))
    rows.extend(cost_refinement_rows(created_at, target_full, inputs))
    rows.extend(defensive_sleeve_refinement_rows(created_at, target_full, inputs))
    rows.extend(remaining_refinement_rows(created_at, target_full, inputs))
    rows.extend(split_stability_check_rows(created_at, target_full, inputs))
    rows.extend(next_hypothesis_rows(created_at))
    return rows


def split_sensitivity_rows(
    created_at: str,
    target_full: dict[str, Any],
    robustness_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for metric in ["cagr_pct", "sharpe_ratio", "calmar_ratio", "max_drawdown_pct"]:
        worst = worst_split_row(robustness_rows, metric)
        if not worst:
            continue
        full_value = as_float(target_full.get(metric))
        split_value = as_float(worst.get(metric))
        delta = split_value - full_value
        rows.append(
            diagnostic_row(
                created_at,
                "split_sensitivity",
                f"worst_split_by_{metric}",
                metric,
                split_value,
                full_value,
                delta,
                status_for_split_metric(metric, delta),
                "warning" if metric in {"cagr_pct", "sharpe_ratio", "calmar_ratio"} and delta < 0 else "info",
                f"{worst.get('split_name')} out-of-sample {metric}={split_value}; full-period {metric}={full_value}.",
                split_interpretation(metric, delta),
                "Review whether weakness is concentrated around this chronological split before adding new variants.",
                period="out_of_sample",
                split_name=worst.get("split_name", ""),
            )
        )
    for split in sorted(robustness_rows, key=lambda row: row.get("split_name", "")):
        rows.append(
            diagnostic_row(
                created_at,
                "split_sensitivity",
                "split_metric_snapshot",
                "calmar_ratio",
                as_float(split.get("calmar_ratio")),
                as_float(target_full.get("calmar_ratio")),
                as_float(split.get("calmar_ratio")) - as_float(target_full.get("calmar_ratio")),
                "split_diagnostic",
                "info",
                (
                    f"{split.get('split_name')} CAGR={split.get('cagr_pct')}, Sharpe={split.get('sharpe_ratio')}, "
                    f"MaxDD={split.get('max_drawdown_pct')}, Calmar={split.get('calmar_ratio')}."
                ),
                "Split rows show whether the active lead persists across different out-of-sample windows.",
                "Keep this as a diagnostic input, not an execution gate.",
                period="out_of_sample",
                split_name=split.get("split_name", ""),
            )
        )
    return rows


def benchmark_relative_rows(
    created_at: str,
    target_full: dict[str, Any],
    summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for comparison_strategy in COMPARISON_STRATEGIES:
        reference = find_row(summary_rows, comparison_strategy)
        if not reference:
            rows.append(
                diagnostic_row(
                    created_at,
                    "benchmark_relative",
                    "missing_comparison_row",
                    "availability",
                    "",
                    "",
                    "",
                    "insufficient_data",
                    "warning",
                    f"Missing comparison strategy row: {comparison_strategy}.",
                    "Benchmark-relative diagnostics need the saved lab summary row.",
                    "Run `python bot.py --strategy-improvement-lab`.",
                    comparison_strategy=comparison_strategy,
                )
            )
            continue
        for metric in ["cagr_pct", "sharpe_ratio", "calmar_ratio", "max_drawdown_pct", "average_cash_weight_pct"]:
            target_value = as_float(target_full.get(metric))
            reference_value = as_float(reference.get(metric))
            rows.append(
                diagnostic_row(
                    created_at,
                    "benchmark_relative",
                    f"vs_{comparison_strategy}",
                    metric,
                    target_value,
                    reference_value,
                    target_value - reference_value,
                    benchmark_status(comparison_strategy, metric, target_value, reference_value),
                    "info",
                    f"{TARGET_STRATEGY} {metric}={target_value}; {comparison_strategy} {metric}={reference_value}.",
                    benchmark_interpretation(comparison_strategy, metric, target_value, reference_value),
                    "Use benchmark gaps to refine the next fixed hypothesis; do not treat them as order instructions.",
                    comparison_strategy=comparison_strategy,
                )
            )
    return rows


def cost_sensitivity_rows(
    created_at: str,
    target_cost_rows: list[dict[str, Any]],
    all_cost_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for cost_row in sorted(target_cost_rows, key=lambda row: row.get("cost_label", "")):
        cost_label = cost_row.get("cost_label", "")
        same_cost = [row for row in all_cost_rows if row.get("cost_label") == cost_label and not is_benchmark(row)]
        best = max(same_cost, key=lambda row: as_float(row.get("cost_adjusted_calmar_ratio")), default=None)
        rank = rank_for_strategy(same_cost, TARGET_STRATEGY, "cost_adjusted_calmar_ratio")
        remains_best = bool(best and best.get("strategy_name") == TARGET_STRATEGY)
        rows.append(
            diagnostic_row(
                created_at,
                "cost_sensitivity",
                f"{cost_label}_ranking",
                "cost_adjusted_calmar_ratio",
                as_float(cost_row.get("cost_adjusted_calmar_ratio")),
                as_float(best.get("cost_adjusted_calmar_ratio")) if best else "",
                rank,
                "cost_resilient" if remains_best else "cost_rank_changed",
                "warning" if not remains_best and cost_label == "high_cost" else "info",
                (
                    f"{cost_label}: target cost-adjusted Calmar={cost_row.get('cost_adjusted_calmar_ratio')}; "
                    f"rank={rank}; best active={best.get('strategy_name') if best else 'unavailable'}."
                ),
                "Cost stress is a turnover-burden diagnostic, not a live cost model.",
                "If high-cost rank drops, consider a future fixed turnover threshold hypothesis.",
                comparison_strategy=best.get("strategy_name") if best else "",
            )
        )
    worst = min(target_cost_rows, key=lambda row: as_float(row.get("cost_adjusted_calmar_ratio")), default=None)
    if worst:
        rows.append(
            diagnostic_row(
                created_at,
                "cost_sensitivity",
                "worst_cost_scenario",
                "cost_adjusted_calmar_ratio",
                as_float(worst.get("cost_adjusted_calmar_ratio")),
                as_float(worst.get("calmar_ratio")),
                as_float(worst.get("cost_adjusted_calmar_ratio")) - as_float(worst.get("calmar_ratio")),
                "cost_burden_review",
                "info",
                f"Worst fixed cost scenario is {worst.get('cost_label')}.",
                "Cost burden explains split sensitivity only if rank or adjusted Calmar decays materially.",
                "Use fixed cost diagnostics before any future promotion discussion.",
            )
        )
    return rows


def drawdown_rows(
    created_at: str,
    target_full: dict[str, Any],
    drawdown_row: dict[str, Any] | None,
    equity_rows: list[dict[str, Any]],
    all_drawdown_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    reference = find_row(all_drawdown_rows, ACTIVE_REFERENCE)
    target_dd = as_float(target_full.get("max_drawdown_pct"))
    reference_dd = as_float(reference.get("max_drawdown_pct")) if reference else 0.0
    recovery_days = recovery_duration_days(equity_rows, drawdown_row)
    rows.append(
        diagnostic_row(
            created_at,
            "drawdown_behavior",
            "worst_drawdown_window",
            "max_drawdown_pct",
            target_dd,
            reference_dd,
            target_dd - reference_dd,
            drawdown_status(target_full, reference),
            "warning" if target_dd < reference_dd - 5 else "info",
            (
                f"Worst drawdown {drawdown_row.get('worst_drawdown_pct') if drawdown_row else target_dd}% "
                f"from {drawdown_row.get('worst_drawdown_start') if drawdown_row else ''} "
                f"to {drawdown_row.get('worst_drawdown_end') if drawdown_row else ''}; recovery_days={recovery_days}."
            ),
            drawdown_interpretation(target_full, reference),
            "If drawdown is concentrated in one crisis/rebound period, test re-entry refinement later.",
        )
    )
    return rows


def cash_drag_rows(
    created_at: str,
    target_full: dict[str, Any],
    summary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reference = find_row(summary_rows, ACTIVE_REFERENCE)
    target_cash = as_float(target_full.get("average_cash_weight_pct"))
    reference_cash = as_float(reference.get("average_cash_weight_pct")) if reference else 0.0
    delta = target_cash - reference_cash
    return [
        diagnostic_row(
            created_at,
            "cash_drag",
            "cash_drag_vs_rotation_reference",
            "average_cash_weight_pct",
            target_cash,
            reference_cash,
            delta,
            "cash_drag_reduced" if delta < 0 else "cash_drag_not_reduced",
            "info",
            f"Target average cash={target_cash}%; rotation reference average cash={reference_cash}%.",
            "Lower cash likely explains part of the stronger CAGR, while increasing participation during drawdowns.",
            "Consider only precise future refinements that preserve reduced cash drag.",
            comparison_strategy=ACTIVE_REFERENCE,
        )
    ]


def candidate_status_rows(
    created_at: str,
    target_full: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
    robustness_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    drawdown_row: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    lead_full = find_row(comparison_rows, ACTIVE_RESEARCH_LEAD) or target_full
    target_comparison = find_row(comparison_rows, ACTIVE_RESEARCH_LEAD) or find_row(comparison_rows, TARGET_STRATEGY)
    active_rows = [row for row in comparison_rows if not is_benchmark(row)]
    best_calmar = max(active_rows, key=lambda row: as_float(row.get("calmar_ratio")), default=None)
    active_lead = bool(best_calmar and best_calmar.get("strategy_name") == ACTIVE_RESEARCH_LEAD)
    split_sensitive = parse_bool(target_comparison.get("split_sensitive")) if target_comparison else split_sensitive_from_rows(robustness_rows)
    cost_sensitive = parse_bool(target_comparison.get("cost_sensitive")) if target_comparison else any(parse_bool(row.get("cost_sensitive")) for row in cost_rows)
    cagr_delta = as_float(lead_full.get("cagr_delta_vs_benchmark"))
    calmar_delta = as_float(lead_full.get("calmar_delta_vs_benchmark"))
    dd_delta = as_float(lead_full.get("max_drawdown_delta_vs_benchmark"))

    statuses = []
    if active_lead and ACTIVE_RESEARCH_LEAD != PREVIOUS_RESEARCH_LEAD:
        statuses.append("new_active_research_lead")
    if active_lead and split_sensitive:
        statuses.append("promising_but_split_sensitive")
    if active_lead:
        statuses.append("benchmark_lagging_but_active_leader")
    if cagr_delta > 0 and calmar_delta > 0 and dd_delta > -5:
        statuses.append("return_improved_drawdown_acceptable")
    if cost_sensitive:
        statuses.append("cost_sensitive_candidate")
    if dd_delta < -5:
        statuses.append("drawdown_heavy_candidate")
    cash_delta = as_float(target_comparison.get("cash_drag_delta_vs_benchmark")) if target_comparison else 0.0
    if cash_delta < 0:
        statuses.append("cash_drag_reduced")
    if not statuses:
        statuses.append("insufficient_data")

    return [
        diagnostic_row(
            created_at,
            "candidate_status",
            status,
            "status",
            status,
            "",
            "",
            status,
            "warning" if status in {"promising_but_split_sensitive", "cost_sensitive_candidate", "drawdown_heavy_candidate"} else "info",
            status_evidence(status, lead_full, target_comparison, drawdown_row),
            status_interpretation(status),
            "Use the diagnostic statuses to choose one fixed next hypothesis; do not add random tuning.",
            strategy_name=ACTIVE_RESEARCH_LEAD,
        )
        for status in statuses
    ]


def cost_refinement_rows(
    created_at: str,
    original_full: dict[str, Any],
    inputs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    cost_full = find_row(inputs["lab_summary"], COST_AWARE_STRATEGY)
    if not cost_full:
        return [
            diagnostic_row(
                created_at,
                "cost_refinement",
                "cost_aware_variant_missing",
                "availability",
                "",
                "",
                "",
                "insufficient_data",
                "warning",
                f"{COST_AWARE_STRATEGY} is missing from saved lab summary.",
                "The direct refinement comparison cannot run without the saved cost-aware row.",
                "Run `python bot.py --strategy-improvement-lab` after adding the cost-aware variant.",
                strategy_name=COST_AWARE_STRATEGY,
                comparison_strategy=TARGET_STRATEGY,
            )
        ]

    original_comparison = find_row(inputs["comparison"], TARGET_STRATEGY)
    cost_comparison = find_row(inputs["comparison"], COST_AWARE_STRATEGY)
    rows = []
    for metric in ["cagr_pct", "sharpe_ratio", "calmar_ratio", "max_drawdown_pct", "average_cash_weight_pct", "trade_count", "turnover"]:
        cost_value = as_float(cost_full.get(metric))
        original_value = as_float(original_full.get(metric))
        rows.append(
            diagnostic_row(
                created_at,
                "cost_refinement",
                f"cost_aware_vs_original_{metric}",
                metric,
                cost_value,
                original_value,
                cost_value - original_value,
                cost_refinement_metric_status(metric, cost_value, original_value),
                "info",
                f"{COST_AWARE_STRATEGY} {metric}={cost_value}; {TARGET_STRATEGY} {metric}={original_value}.",
                cost_refinement_metric_interpretation(metric, cost_value, original_value),
                "Judge the cost-aware refinement against the original growth-biased strategy before considering any new variant.",
                strategy_name=COST_AWARE_STRATEGY,
                comparison_strategy=TARGET_STRATEGY,
            )
        )

    original_cost_sensitive = parse_bool(original_comparison.get("cost_sensitive")) if original_comparison else False
    cost_cost_sensitive = parse_bool(cost_comparison.get("cost_sensitive")) if cost_comparison else False
    original_split_sensitive = parse_bool(original_comparison.get("split_sensitive")) if original_comparison else False
    cost_split_sensitive = parse_bool(cost_comparison.get("split_sensitive")) if cost_comparison else False
    rows.append(
        diagnostic_row(
            created_at,
            "cost_refinement",
            "cost_sensitivity_change",
            "cost_sensitive",
            cost_cost_sensitive,
            original_cost_sensitive,
            bool_delta(cost_cost_sensitive, original_cost_sensitive),
            "cost_refinement_improved" if original_cost_sensitive and not cost_cost_sensitive else "cost_refinement_no_material_change",
            "info",
            f"Original cost_sensitive={original_cost_sensitive}; cost-aware cost_sensitive={cost_cost_sensitive}.",
            "This checks whether the fixed rebalance threshold directly improves the diagnosed cost sensitivity.",
            "If cost sensitivity improves without large return drag, consider it as the next active research lead.",
            strategy_name=COST_AWARE_STRATEGY,
            comparison_strategy=TARGET_STRATEGY,
        )
    )
    rows.append(
        diagnostic_row(
            created_at,
            "cost_refinement",
            "split_sensitivity_change",
            "split_sensitive",
            cost_split_sensitive,
            original_split_sensitive,
            bool_delta(cost_split_sensitive, original_split_sensitive),
            "cost_refinement_improved" if original_split_sensitive and not cost_split_sensitive else "cost_refinement_no_material_change",
            "info",
            f"Original split_sensitive={original_split_sensitive}; cost-aware split_sensitive={cost_split_sensitive}.",
            "This checks whether reduced rebalance churn also improves split stability.",
            "Use fixed split diagnostics before any future promotion discussion.",
            strategy_name=COST_AWARE_STRATEGY,
            comparison_strategy=TARGET_STRATEGY,
        )
    )
    rows.append(cost_refinement_decision_row(created_at, original_full, cost_full, original_comparison, cost_comparison))
    return rows


def cost_refinement_decision_row(
    created_at: str,
    original_full: dict[str, Any],
    cost_full: dict[str, Any],
    original_comparison: dict[str, Any] | None,
    cost_comparison: dict[str, Any] | None,
) -> dict[str, Any]:
    cagr_delta = as_float(cost_full.get("cagr_pct")) - as_float(original_full.get("cagr_pct"))
    sharpe_delta = as_float(cost_full.get("sharpe_ratio")) - as_float(original_full.get("sharpe_ratio"))
    calmar_delta = as_float(cost_full.get("calmar_ratio")) - as_float(original_full.get("calmar_ratio"))
    turnover_delta = as_float(cost_full.get("turnover")) - as_float(original_full.get("turnover"))
    cost_improved = bool_improved(cost_comparison.get("cost_sensitive") if cost_comparison else False, original_comparison.get("cost_sensitive") if original_comparison else False)
    split_improved = bool_improved(cost_comparison.get("split_sensitive") if cost_comparison else False, original_comparison.get("split_sensitive") if original_comparison else False)
    diagnostic_improved = cost_improved or split_improved
    turnover_reduced = turnover_delta < 0
    performance_drag = cagr_delta <= -0.50 or sharpe_delta <= -0.03 or calmar_delta <= -0.05
    if diagnostic_improved and not performance_drag:
        status = "cost_refinement_promising"
        interpretation = "The cost-aware refinement improves the diagnosed cost issue without large return drag."
    elif diagnostic_improved and turnover_reduced:
        status = "cost_refinement_improved"
        interpretation = "The refinement improves a diagnosed sensitivity issue and reduces turnover, but still needs review before any promotion."
    elif performance_drag:
        status = "cost_refinement_return_drag"
        if turnover_reduced and not diagnostic_improved:
            interpretation = (
                "Reduced turnover, but did not improve cost/split sensitivity and sacrificed too much performance. "
                f"Do not displace active research lead {ACTIVE_RESEARCH_LEAD}."
            )
        else:
            interpretation = "The refinement appears to sacrifice too much return or risk-adjusted performance."
    elif not cost_improved and not split_improved:
        status = "cost_refinement_no_material_change"
        if turnover_reduced:
            interpretation = (
                "The refinement reduces turnover but does not materially improve the diagnosed cost or split-sensitivity weakness."
            )
        else:
            interpretation = "The refinement does not materially improve the diagnosed weakness."
    else:
        status = "cost_refinement_not_useful"
        interpretation = "The refinement is not useful enough versus the original growth-biased strategy."
    return diagnostic_row(
        created_at,
        "cost_refinement",
        "cost_aware_refinement_decision",
        "status",
        status,
        "",
        "",
        status,
        "warning" if status in {"cost_refinement_return_drag", "cost_refinement_not_useful"} else "info",
        f"CAGR delta={round(cagr_delta, 4)}, Sharpe delta={round(sharpe_delta, 4)}, Calmar delta={round(calmar_delta, 4)}, turnover delta={round(turnover_delta, 4)}, cost_improved={cost_improved}, split_improved={split_improved}.",
        interpretation,
        "Keep both variants research-only; choose the active research lead only after reviewing saved robustness and diagnostics.",
        strategy_name=COST_AWARE_STRATEGY,
        comparison_strategy=TARGET_STRATEGY,
    )


def defensive_sleeve_refinement_rows(
    created_at: str,
    original_full: dict[str, Any],
    inputs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    sleeve_full = find_row(inputs["lab_summary"], PARTIAL_DEFENSIVE_STRATEGY)
    if not sleeve_full:
        return [
            diagnostic_row(
                created_at,
                "defensive_sleeve_refinement",
                "partial_defensive_sleeve_missing",
                "status",
                "missing",
                "",
                "",
                "insufficient_data",
                "warning",
                f"{PARTIAL_DEFENSIVE_STRATEGY} is missing from saved lab summary.",
                "The direct defensive-sleeve refinement comparison cannot run without the saved partial-sleeve row.",
                "Run `python bot.py --strategy-improvement-lab` after adding the partial defensive sleeve variant.",
                strategy_name=PARTIAL_DEFENSIVE_STRATEGY,
                comparison_strategy=TARGET_STRATEGY,
            )
        ]

    rows = []
    original_comparison = find_row(inputs["comparison"], TARGET_STRATEGY)
    sleeve_comparison = find_row(inputs["comparison"], PARTIAL_DEFENSIVE_STRATEGY)
    for metric in [
        "cagr_pct",
        "sharpe_ratio",
        "max_drawdown_pct",
        "calmar_ratio",
        "average_cash_weight_pct",
        "trade_count",
        "turnover",
    ]:
        sleeve_value = as_float(sleeve_full.get(metric))
        original_value = as_float(original_full.get(metric))
        rows.append(
            diagnostic_row(
                created_at,
                "defensive_sleeve_refinement",
                f"partial_defensive_vs_original_{metric}",
                "delta_vs_original_growth_biased",
                sleeve_value,
                original_value,
                round(sleeve_value - original_value, 4),
                defensive_sleeve_metric_status(metric, sleeve_value, original_value),
                "info",
                f"{PARTIAL_DEFENSIVE_STRATEGY} {metric}={sleeve_value}; {TARGET_STRATEGY} {metric}={original_value}.",
                defensive_sleeve_metric_interpretation(metric, sleeve_value, original_value),
                "Judge the partial defensive sleeve against the original growth-biased strategy before considering any promotion.",
                strategy_name=PARTIAL_DEFENSIVE_STRATEGY,
                comparison_strategy=TARGET_STRATEGY,
            )
        )
    for diagnostic_name, field_name in [
        ("partial_defensive_cost_sensitivity", "cost_sensitive"),
        ("partial_defensive_split_sensitivity", "split_sensitive"),
    ]:
        original_value = original_comparison.get(field_name) if original_comparison else False
        sleeve_value = sleeve_comparison.get(field_name) if sleeve_comparison else False
        delta = bool_delta(sleeve_value, original_value)
        status = "defensive_sleeve_improved_stability" if delta == "improved" else "defensive_sleeve_no_material_improvement"
        rows.append(
            diagnostic_row(
                created_at,
                "defensive_sleeve_refinement",
                diagnostic_name,
                field_name,
                parse_bool(sleeve_value),
                parse_bool(original_value),
                delta,
                status,
                "info",
                f"Original {field_name}={parse_bool(original_value)}; partial defensive sleeve {field_name}={parse_bool(sleeve_value)}.",
                "The partial defensive sleeve improves this diagnostic only when the original was sensitive and the sleeve is not.",
                "Use saved robustness diagnostics before any future promotion discussion.",
                strategy_name=PARTIAL_DEFENSIVE_STRATEGY,
                comparison_strategy=TARGET_STRATEGY,
            )
        )
    rows.append(defensive_sleeve_decision_row(created_at, original_full, sleeve_full, original_comparison, sleeve_comparison))
    return rows


def defensive_sleeve_decision_row(
    created_at: str,
    original_full: dict[str, Any],
    sleeve_full: dict[str, Any],
    original_comparison: dict[str, Any] | None,
    sleeve_comparison: dict[str, Any] | None,
) -> dict[str, Any]:
    cagr_delta = as_float(sleeve_full.get("cagr_pct")) - as_float(original_full.get("cagr_pct"))
    sharpe_delta = as_float(sleeve_full.get("sharpe_ratio")) - as_float(original_full.get("sharpe_ratio"))
    calmar_delta = as_float(sleeve_full.get("calmar_ratio")) - as_float(original_full.get("calmar_ratio"))
    max_drawdown_delta = as_float(sleeve_full.get("max_drawdown_pct")) - as_float(original_full.get("max_drawdown_pct"))
    cash_delta = as_float(sleeve_full.get("average_cash_weight_pct")) - as_float(original_full.get("average_cash_weight_pct"))
    turnover_delta = as_float(sleeve_full.get("turnover")) - as_float(original_full.get("turnover"))
    cost_improved = bool_improved(sleeve_comparison.get("cost_sensitive") if sleeve_comparison else False, original_comparison.get("cost_sensitive") if original_comparison else False)
    split_improved = bool_improved(sleeve_comparison.get("split_sensitive") if sleeve_comparison else False, original_comparison.get("split_sensitive") if original_comparison else False)
    drawdown_improved = max_drawdown_delta > 0.50
    risk_adjusted_improved = sharpe_delta > 0.03 or calmar_delta > 0.03
    stability_improved = split_improved or drawdown_improved or cost_improved
    excessive_return_drag = cagr_delta <= -1.00 or sharpe_delta <= -0.05 or calmar_delta <= -0.05

    if (risk_adjusted_improved or split_improved) and not excessive_return_drag:
        status = "defensive_sleeve_promising"
        interpretation = (
            "The partial defensive sleeve improves risk-adjusted performance or split stability without excessive return drag; "
            "review manually before changing the active research lead."
        )
    elif stability_improved and not excessive_return_drag:
        status = "defensive_sleeve_improved_stability"
        interpretation = "The partial defensive sleeve improves stability or drawdown behaviour while preserving most of the growth profile."
    elif excessive_return_drag:
        status = "defensive_sleeve_return_drag"
        interpretation = "The partial defensive sleeve sacrifices too much CAGR, Sharpe, or Calmar versus the original growth-biased strategy."
    elif not stability_improved:
        status = "defensive_sleeve_no_material_improvement"
        interpretation = "The partial defensive sleeve does not materially improve split stability, drawdown, or cost sensitivity."
    else:
        status = "defensive_sleeve_not_useful"
        interpretation = "The partial defensive sleeve is not useful enough versus the original growth-biased strategy."

    if status not in {"defensive_sleeve_promising", "defensive_sleeve_improved_stability"}:
        interpretation += f" Do not displace active research lead {ACTIVE_RESEARCH_LEAD}."
    return diagnostic_row(
        created_at,
        "defensive_sleeve_refinement",
        "partial_defensive_sleeve_decision",
        "status",
        status,
        "",
        "",
        status,
        "warning" if status in {"defensive_sleeve_return_drag", "defensive_sleeve_not_useful"} else "info",
        (
            f"CAGR delta={round(cagr_delta, 4)}, Sharpe delta={round(sharpe_delta, 4)}, "
            f"Calmar delta={round(calmar_delta, 4)}, MaxDD delta={round(max_drawdown_delta, 4)}, "
            f"cash delta={round(cash_delta, 4)}, turnover delta={round(turnover_delta, 4)}, "
            f"cost_improved={cost_improved}, split_improved={split_improved}."
        ),
        interpretation,
        "Keep both variants research-only; choose the active research lead only after reviewing saved robustness and diagnostics.",
        strategy_name=PARTIAL_DEFENSIVE_STRATEGY,
        comparison_strategy=TARGET_STRATEGY,
    )


def remaining_refinement_rows(
    created_at: str,
    original_full: dict[str, Any],
    inputs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    original_comparison = find_row(inputs["comparison"], TARGET_STRATEGY)
    for strategy_name in REMAINING_REFINEMENT_STRATEGIES:
        candidate_full = find_row(inputs["lab_summary"], strategy_name)
        candidate_comparison = find_row(inputs["comparison"], strategy_name)
        if not candidate_full:
            rows.append(
                diagnostic_row(
                    created_at,
                    "remaining_refinement_batch",
                    f"{strategy_name}_missing",
                    "status",
                    "missing",
                    "",
                    "",
                    "insufficient_data",
                    "warning",
                    f"{strategy_name} is missing from saved lab summary.",
                    "The remaining-refinement batch comparison cannot run without the saved strategy row.",
                    "Run `python bot.py --strategy-improvement-lab` and robustness before reviewing this hypothesis.",
                    strategy_name=strategy_name,
                    comparison_strategy=TARGET_STRATEGY,
                )
            )
            continue
        rows.append(remaining_refinement_decision_row(created_at, original_full, candidate_full, original_comparison, candidate_comparison))
    return rows


def remaining_refinement_decision_row(
    created_at: str,
    original_full: dict[str, Any],
    candidate_full: dict[str, Any],
    original_comparison: dict[str, Any] | None,
    candidate_comparison: dict[str, Any] | None,
) -> dict[str, Any]:
    strategy_name = str(candidate_full.get("strategy_name"))
    cagr_delta = as_float(candidate_full.get("cagr_pct")) - as_float(original_full.get("cagr_pct"))
    sharpe_delta = as_float(candidate_full.get("sharpe_ratio")) - as_float(original_full.get("sharpe_ratio"))
    calmar_delta = as_float(candidate_full.get("calmar_ratio")) - as_float(original_full.get("calmar_ratio"))
    max_drawdown_delta = as_float(candidate_full.get("max_drawdown_pct")) - as_float(original_full.get("max_drawdown_pct"))
    cash_delta = as_float(candidate_full.get("average_cash_weight_pct")) - as_float(original_full.get("average_cash_weight_pct"))
    turnover_delta = as_float(candidate_full.get("turnover")) - as_float(original_full.get("turnover"))
    cost_improved = bool_improved(candidate_comparison.get("cost_sensitive") if candidate_comparison else False, original_comparison.get("cost_sensitive") if original_comparison else False)
    split_improved = bool_improved(candidate_comparison.get("split_sensitive") if candidate_comparison else False, original_comparison.get("split_sensitive") if original_comparison else False)
    risk_adjusted_improved = sharpe_delta > 0.03 or calmar_delta > 0.03
    excessive_return_drag = cagr_delta <= -1.00 or sharpe_delta <= -0.05 or calmar_delta <= -0.05
    status_prefix = remaining_refinement_status_prefix(strategy_name)

    if (risk_adjusted_improved or split_improved or cost_improved) and not excessive_return_drag:
        status = f"{status_prefix}_improved"
        if strategy_name == ACTIVE_RESEARCH_LEAD:
            interpretation = (
                "This fixed refinement is the new active research lead because it improves the previous growth-biased baseline "
                "without worsening drawdown, cash drag, cost sensitivity, or split sensitivity."
            )
        else:
            interpretation = "This fixed refinement improves risk-adjusted performance, cost sensitivity, or split stability without excessive return drag."
    elif excessive_return_drag:
        status = f"{status_prefix}_return_drag"
        interpretation = "This fixed refinement sacrifices too much CAGR, Sharpe, or Calmar versus the original growth-biased strategy."
    else:
        status = f"{status_prefix}_no_material_improvement"
        interpretation = "This fixed refinement does not materially improve the diagnosed growth-biased weakness."

    if (status.endswith("_return_drag") or status.endswith("_no_material_improvement")) and strategy_name != ACTIVE_RESEARCH_LEAD:
        interpretation += f" Do not displace active research lead {ACTIVE_RESEARCH_LEAD}."
    return diagnostic_row(
        created_at,
        "remaining_refinement_batch",
        f"{strategy_name}_decision",
        "status",
        status,
        "",
        "",
        status,
        "warning" if status.endswith("_return_drag") else "info",
        (
            f"CAGR delta={round(cagr_delta, 4)}, Sharpe delta={round(sharpe_delta, 4)}, "
            f"Calmar delta={round(calmar_delta, 4)}, MaxDD delta={round(max_drawdown_delta, 4)}, "
            f"cash delta={round(cash_delta, 4)}, turnover delta={round(turnover_delta, 4)}, "
            f"cost_improved={cost_improved}, split_improved={split_improved}."
        ),
        interpretation,
        "Keep this research-only; do not connect the refinement to execution or scheduling.",
        strategy_name=strategy_name,
        comparison_strategy=TARGET_STRATEGY,
    )


def split_stability_check_rows(
    created_at: str,
    original_full: dict[str, Any],
    inputs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    original_comparison = find_row(inputs["comparison"], TARGET_STRATEGY)
    candidate_rows = [
        row
        for row in inputs["comparison"]
        if row.get("strategy_name") in REMAINING_REFINEMENT_STRATEGIES
    ]
    improved = []
    for row in candidate_rows:
        cagr_delta = as_float(row.get("cagr_delta_vs_growth_biased"))
        sharpe_delta = as_float(row.get("sharpe_delta_vs_growth_biased"))
        calmar_delta = as_float(row.get("calmar_delta_vs_growth_biased"))
        excessive_return_drag = cagr_delta <= -1.00 or sharpe_delta <= -0.05 or calmar_delta <= -0.05
        if bool_improved(row.get("split_sensitive"), original_comparison.get("split_sensitive") if original_comparison else False) and not excessive_return_drag:
            improved.append(str(row.get("strategy_name")))
    status = "split_stability_improved" if improved else "split_stability_no_material_improvement"
    return [
        diagnostic_row(
            created_at,
            "split_stability_check",
            "growth_biased_rotation_split_stability_check",
            "status",
            status,
            "",
            "",
            status,
            "info",
            f"Variants improving split sensitivity without excessive return drag: {', '.join(improved) if improved else 'none'}.",
            "The split-stability checkpoint is a diagnostic layer, not a separate trading strategy.",
            "Keep original growth-biased strategy unless a fixed refinement improves stability without excess drag.",
            strategy_name=TARGET_STRATEGY,
            comparison_strategy="remaining_growth_biased_refinement_batch",
        )
    ]


def remaining_refinement_status_prefix(strategy_name: str) -> str:
    if strategy_name == REENTRY_FILTER_STRATEGY:
        return "reentry_filter"
    if strategy_name == RECOVERY_FILTER_STRATEGY:
        return "recovery_filter"
    return "breadth_threshold"


def next_hypothesis_rows(created_at: str) -> list[dict[str, Any]]:
    hypotheses = [
        (
            "growth_biased_rotation_breadth_stricter_split_validation",
            "Validate the stricter breadth-gate lead across fixed chronological splits before any promotion discussion.",
        ),
        (
            "growth_biased_rotation_breadth_stricter_cost_stress_review",
            "Review fixed low/default/high cost stress for the stricter breadth-gate lead.",
        ),
        (
            "growth_biased_rotation_breadth_stricter_drawdown_period_review",
            "Review drawdown windows and recovery duration for the stricter breadth-gate lead.",
        ),
        (
            "growth_biased_rotation_breadth_stricter_promotion_checkpoint",
            "Run a research-only promotion checkpoint for the stricter breadth-gate lead without execution approval.",
        ),
    ]
    return [
        diagnostic_row(
            created_at,
            "next_fixed_hypothesis",
            name,
            "future_research_suggestion",
            name,
            "",
            "",
            "suggestion_only",
            "info",
            description,
            "This is a future fixed-hypothesis suggestion, not an implemented strategy.",
            "Do not implement until diagnostics are reviewed manually.",
        )
        for name, description in hypotheses
    ]


def build_insufficient_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [
        diagnostic_row(
            created_at,
            "input_readiness",
            "missing_or_empty_saved_input",
            "missing_input",
            missing_item,
            "",
            "",
            "insufficient_data",
            "warning",
            f"Missing or empty prerequisite: {missing_item}.",
            "Diagnostics read saved CSVs only and do not refresh market data.",
            "Run `python bot.py --strategy-improvement-lab` and `python bot.py --strategy-improvement-robustness` first.",
        )
        for missing_item in missing
    ]


def diagnostic_row(
    created_at: str,
    diagnostic_type: str,
    diagnostic_name: str,
    metric_name: str,
    metric_value: Any,
    reference_value: Any,
    metric_delta: Any,
    status: str,
    severity: str,
    evidence: str,
    interpretation: str,
    recommended_next_step: str,
    period: str = "full_period",
    split_name: str = "",
    comparison_strategy: str = "",
    strategy_name: str = TARGET_STRATEGY,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "diagnostic_type": diagnostic_type,
        "diagnostic_name": diagnostic_name,
        "period": period,
        "split_name": split_name,
        "comparison_strategy": comparison_strategy,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "reference_value": reference_value,
        "metric_delta": metric_delta,
        "status": status,
        "severity": severity,
        "evidence": evidence,
        "interpretation": interpretation,
        "recommended_next_step": recommended_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
    }


def worst_split_row(rows: list[dict[str, Any]], metric: str) -> dict[str, Any] | None:
    if not rows:
        return None
    if metric == "max_drawdown_pct":
        return min(rows, key=lambda row: as_float(row.get(metric)))
    return min(rows, key=lambda row: as_float(row.get(metric)))


def status_for_split_metric(metric: str, delta: float) -> str:
    if metric == "max_drawdown_pct":
        return "drawdown_worse_in_split" if delta < 0 else "drawdown_not_worse_in_split"
    return "split_decay" if delta < 0 else "split_holds_up"


def split_interpretation(metric: str, delta: float) -> str:
    if delta < 0 and metric != "max_drawdown_pct":
        return "This split is weaker than the full-period profile and contributes to the split-sensitive label."
    if metric == "max_drawdown_pct" and delta < 0:
        return "This split has a deeper drawdown than the full-period metric."
    return "This split does not appear worse than the full-period metric for this measure."


def benchmark_status(strategy: str, metric: str, target: float, reference: float) -> str:
    if metric == "max_drawdown_pct":
        return "target_better" if target > reference else "target_worse"
    if metric == "average_cash_weight_pct":
        return "target_lower_cash" if target < reference else "target_higher_cash"
    return "target_leads" if target > reference else "target_trails"


def benchmark_interpretation(strategy: str, metric: str, target: float, reference: float) -> str:
    if strategy == "spy_buy_and_hold_benchmark" and metric in {"cagr_pct", "sharpe_ratio", "calmar_ratio"} and target < reference:
        return "The candidate trails SPY on this benchmark metric, but that alone is not a research rejection."
    if strategy == ACTIVE_REFERENCE and target > reference and metric in {"cagr_pct", "sharpe_ratio", "calmar_ratio"}:
        return "The candidate improves versus the active ETF rotation reference on this metric."
    if metric == "average_cash_weight_pct" and target < reference:
        return "Lower cash drag likely contributes to stronger growth."
    return "Use this gap as context for the next fixed research hypothesis."


def drawdown_status(row: dict[str, Any], reference: dict[str, Any] | None) -> str:
    if not reference:
        return "drawdown_reference_missing"
    cagr_delta = as_float(row.get("cagr_delta_vs_benchmark"))
    dd_delta = as_float(row.get("max_drawdown_delta_vs_benchmark"))
    if cagr_delta > 0 and dd_delta > -5:
        return "return_improved_drawdown_acceptable"
    if cagr_delta > 0 and dd_delta <= -5:
        return "promising_but_drawdown_heavy"
    return "drawdown_not_compensated"


def drawdown_interpretation(row: dict[str, Any], reference: dict[str, Any] | None) -> str:
    status = drawdown_status(row, reference)
    if status == "return_improved_drawdown_acceptable":
        return "Drawdown is not the lowest, but appears acceptable relative to improved active-reference return."
    if status == "promising_but_drawdown_heavy":
        return "The return improvement may come with a drawdown penalty that needs targeted refinement."
    return "Drawdown does not clearly justify the return tradeoff from saved metrics."


def recovery_duration_days(equity_rows: list[dict[str, Any]], drawdown_row: dict[str, Any] | None) -> int | str:
    if not drawdown_row:
        return ""
    start = drawdown_row.get("worst_drawdown_start", "")
    end = drawdown_row.get("worst_drawdown_end", "")
    if not start or not end:
        return ""
    peak_equity = None
    recovery_date = ""
    for row in equity_rows:
        if row.get("date") == start:
            peak_equity = as_float(row.get("equity"))
        if peak_equity is not None and row.get("date", "") >= end and as_float(row.get("equity")) >= peak_equity:
            recovery_date = row.get("date", "")
            break
    if not recovery_date:
        return "not_recovered_in_saved_curve"
    return business_day_distance(end, recovery_date, equity_rows)


def business_day_distance(start: str, end: str, rows: list[dict[str, Any]]) -> int:
    dates = [row.get("date", "") for row in rows]
    try:
        return max(0, dates.index(end) - dates.index(start))
    except ValueError:
        return 0


def split_sensitive_from_rows(rows: list[dict[str, Any]]) -> bool:
    promising = [
        row
        for row in rows
        if as_float(row.get("cagr_delta_vs_benchmark")) > 0 and as_float(row.get("calmar_delta_vs_benchmark")) > 0
    ]
    return len(promising) <= 1


def cost_refinement_metric_status(metric: str, value: float, reference: float) -> str:
    if metric in {"trade_count", "turnover", "average_cash_weight_pct"}:
        return "cost_refinement_improved" if value < reference else "cost_refinement_no_material_change"
    if metric == "max_drawdown_pct":
        return "cost_refinement_improved" if value > reference else "cost_refinement_return_drag"
    return "cost_refinement_improved" if value >= reference else "cost_refinement_return_drag"


def cost_refinement_metric_interpretation(metric: str, value: float, reference: float) -> str:
    if metric in {"trade_count", "turnover"} and value < reference:
        return "The cost-aware rule reduced churn versus the original strategy."
    if metric in {"cagr_pct", "sharpe_ratio", "calmar_ratio"} and value < reference:
        return "The refinement reduced a headline performance metric; check whether turnover savings justify the drag."
    if metric == "max_drawdown_pct" and value > reference:
        return "The refinement reduced drawdown versus the original strategy."
    return "This metric is broadly similar to the original growth-biased strategy."


def defensive_sleeve_metric_status(metric: str, value: float, reference: float) -> str:
    if metric in {"average_cash_weight_pct", "trade_count", "turnover"}:
        return "defensive_sleeve_improved_stability" if value < reference else "defensive_sleeve_no_material_improvement"
    if metric == "max_drawdown_pct":
        return "defensive_sleeve_improved_stability" if value > reference else "defensive_sleeve_no_material_improvement"
    return "defensive_sleeve_improved_stability" if value >= reference else "defensive_sleeve_return_drag"


def defensive_sleeve_metric_interpretation(metric: str, value: float, reference: float) -> str:
    if metric == "max_drawdown_pct" and value > reference:
        return "The partial defensive sleeve reduced drawdown versus the original growth-biased strategy."
    if metric in {"sharpe_ratio", "calmar_ratio"} and value > reference:
        return "The partial defensive sleeve improved a risk-adjusted performance metric."
    if metric == "cagr_pct" and value < reference:
        return "The partial defensive sleeve reduced CAGR; check whether stability benefits justify the drag."
    if metric == "average_cash_weight_pct" and value > reference:
        return "The partial defensive sleeve increased cash drag versus the original strategy."
    if metric in {"trade_count", "turnover"} and value < reference:
        return "The partial defensive sleeve reduced churn versus the original strategy."
    return "This metric is broadly similar to the original growth-biased strategy."


def bool_delta(value: Any, reference: Any) -> str:
    value_bool = parse_bool(value)
    reference_bool = parse_bool(reference)
    if value_bool == reference_bool:
        return "no_change"
    if reference_bool and not value_bool:
        return "improved"
    return "worse"


def bool_improved(value: Any, reference: Any) -> bool:
    return parse_bool(reference) and not parse_bool(value)


def status_evidence(
    status: str,
    target_full: dict[str, Any],
    target_comparison: dict[str, Any] | None,
    drawdown_row: dict[str, Any] | None,
) -> str:
    if status == "benchmark_lagging_but_active_leader":
        return f"Comparison label={target_comparison.get('comparison_label') if target_comparison else ''}; trails_spy={target_comparison.get('trails_spy_buy_and_hold') if target_comparison else ''}."
    if status == "cash_drag_reduced":
        return f"Average cash={target_full.get('average_cash_weight_pct')}%; cash delta vs rotation={target_comparison.get('cash_drag_delta_vs_benchmark') if target_comparison else target_full.get('cash_drag_delta_vs_benchmark')}."
    if status == "drawdown_heavy_candidate":
        return f"Max drawdown={target_full.get('max_drawdown_pct')}%; worst window={drawdown_row.get('worst_drawdown_start') if drawdown_row else ''} to {drawdown_row.get('worst_drawdown_end') if drawdown_row else ''}."
    return (
        f"CAGR delta={target_full.get('cagr_delta_vs_benchmark')}; "
        f"Sharpe delta={target_full.get('sharpe_delta_vs_benchmark')}; "
        f"Calmar delta={target_full.get('calmar_delta_vs_benchmark')}."
    )


def status_interpretation(status: str) -> str:
    interpretations = {
        "promising_but_split_sensitive": "Split-sensitive means promising but not stable enough for promotion; it does not mean automatically discard.",
        "new_active_research_lead": "The stricter breadth gate is now the active research lead versus the previous growth-biased baseline; this is still research-only.",
        "benchmark_lagging_but_active_leader": "The major issue may be SPY benchmark lag rather than active-strategy underperformance.",
        "return_improved_drawdown_acceptable": "The active-reference improvement appears meaningful without an obviously unacceptable drawdown penalty.",
        "cost_sensitive_candidate": "Cost burden may matter and should be checked before future promotion.",
        "drawdown_heavy_candidate": "Drawdown needs focused refinement, not random tuning.",
        "cash_drag_reduced": "Lower cash drag is a useful research feature to preserve.",
        "defensive_sleeve_improved_stability": "The partial defensive sleeve improved a stability metric, but remains research-only.",
        "defensive_sleeve_return_drag": "The partial defensive sleeve sacrificed too much performance versus the original growth-biased strategy.",
        "defensive_sleeve_no_material_improvement": "The partial defensive sleeve did not materially improve the diagnosed weakness.",
        "defensive_sleeve_promising": "The partial defensive sleeve may be promising if manual review confirms stability gains without excess drag.",
        "defensive_sleeve_not_useful": "The partial defensive sleeve is not useful enough versus the original growth-biased strategy.",
        "reentry_filter_improved": "The fixed re-entry filter improved a key diagnostic without excessive drag.",
        "reentry_filter_return_drag": "The fixed re-entry filter sacrificed too much performance versus the original growth-biased strategy.",
        "reentry_filter_no_material_improvement": "The fixed re-entry filter did not materially improve the diagnosed weakness.",
        "recovery_filter_improved": "The fixed recovery filter improved a key diagnostic without excessive drag.",
        "recovery_filter_return_drag": "The fixed recovery filter sacrificed too much performance versus the original growth-biased strategy.",
        "recovery_filter_no_material_improvement": "The fixed recovery filter did not materially improve the diagnosed weakness.",
        "breadth_threshold_improved": "The fixed breadth-threshold review improved a key diagnostic without excessive drag.",
        "breadth_threshold_return_drag": "The fixed breadth-threshold review sacrificed too much performance versus the original growth-biased strategy.",
        "breadth_threshold_no_material_improvement": "The fixed breadth-threshold review did not materially improve the diagnosed weakness.",
        "split_stability_improved": "At least one fixed refinement improved split stability without excessive return drag.",
        "split_stability_no_material_improvement": "No fixed refinement materially improved split stability without excessive return drag.",
        "insufficient_data": "Saved inputs are insufficient for this diagnostic.",
    }
    return interpretations.get(status, "Research-only diagnostic status.")


def rank_for_strategy(rows: list[dict[str, Any]], strategy_name: str, metric: str) -> int | str:
    ranked = sorted(rows, key=lambda row: as_float(row.get(metric)), reverse=True)
    for index, row in enumerate(ranked, start=1):
        if row.get("strategy_name") == strategy_name:
            return index
    return ""


def is_benchmark(row: dict[str, Any]) -> bool:
    return str(row.get("strategy_name", "")).endswith("_benchmark")


def find_row(rows: list[dict[str, Any]], strategy_name: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("strategy_name") == strategy_name and row.get("period", "full_period") == "full_period":
            return row
    for row in rows:
        if row.get("strategy_name") == strategy_name:
            return row
    return None


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DIAGNOSTIC_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_summary_lines(rows: list[dict[str, Any]], diagnostics_path: Path, growth_path: Path) -> list[str]:
    statuses = [row["status"] for row in rows if row["diagnostic_type"] == "candidate_status"]
    worst_split = next((row for row in rows if row["diagnostic_name"] == "worst_split_by_calmar_ratio"), None)
    cost_warning = any(row["status"] in {"cost_rank_changed", "cost_sensitive_candidate"} for row in rows)
    drawdown = next((row for row in rows if row["diagnostic_type"] == "drawdown_behavior"), None)
    cash = next((row for row in rows if row["diagnostic_type"] == "cash_drag"), None)
    hypotheses = [row["diagnostic_name"] for row in rows if row["diagnostic_type"] == "next_fixed_hypothesis"]
    refinement = next((row for row in rows if row["diagnostic_name"] == "cost_aware_refinement_decision"), None)
    defensive_refinement = next((row for row in rows if row["diagnostic_name"] == "partial_defensive_sleeve_decision"), None)
    remaining_refinements = [row for row in rows if row["diagnostic_type"] == "remaining_refinement_batch" and row["diagnostic_name"].endswith("_decision")]
    split_stability = next((row for row in rows if row["diagnostic_name"] == "growth_biased_rotation_split_stability_check"), None)
    lines = [
        "Strategy improvement diagnostics complete. Research/preview only; execution_approved=False.",
        f"Active research lead: {ACTIVE_RESEARCH_LEAD}",
        f"Previous growth-biased baseline: {PREVIOUS_RESEARCH_LEAD}",
        f"Main statuses: {', '.join(statuses) if statuses else 'insufficient_data'}",
    ]
    if worst_split:
        lines.append(f"Worst Calmar split: {worst_split['split_name']} ({worst_split['evidence']})")
    if drawdown:
        lines.append(f"Drawdown: {drawdown['status']} ({drawdown['evidence']})")
    if cash:
        lines.append(f"Cash drag: {cash['status']} ({cash['evidence']})")
    lines.append(f"Cost sensitivity matters: {cost_warning}")
    if hypotheses:
        lines.append("Next fixed hypotheses: " + ", ".join(hypotheses))
    if refinement:
        lines.append(f"Cost-aware refinement decision: {refinement['status']} ({refinement['evidence']})")
    if defensive_refinement:
        lines.append(f"Partial defensive sleeve decision: {defensive_refinement['status']} ({defensive_refinement['evidence']})")
    for row in remaining_refinements:
        lines.append(f"{row['strategy_name']} decision: {row['status']} ({row['evidence']})")
    if split_stability:
        lines.append(f"Split stability check: {split_stability['status']} ({split_stability['evidence']})")
    lines.append(f"Saved diagnostics to {diagnostics_path}")
    lines.append(f"Saved growth-biased diagnostics to {growth_path}")
    lines.append("Warning: diagnostics are research guidance only and do not approve orders.")
    return lines


def show_strategy_improvement_diagnostics_file(
    growth_path: Path | str = OUTPUT_FILES["growth"],
) -> tuple[int, list[str]]:
    path = Path(growth_path)
    if not path.exists():
        return 1, ["Run `python bot.py --strategy-improvement-diagnostics` first."]
    rows = read_csv(path)
    if not rows:
        return 1, [f"No rows found in {path}. Run `python bot.py --strategy-improvement-diagnostics` first."]

    statuses = [row["status"] for row in rows if row["diagnostic_type"] == "candidate_status"]
    worst_split = next((row for row in rows if row["diagnostic_name"] == "worst_split_by_calmar_ratio"), None)
    cost_warning = any(row["status"] in {"cost_rank_changed", "cost_sensitive_candidate"} for row in rows)
    drawdown = next((row for row in rows if row["diagnostic_type"] == "drawdown_behavior"), None)
    cash = next((row for row in rows if row["diagnostic_type"] == "cash_drag"), None)
    active_lead = any(row["status"] == "new_active_research_lead" for row in rows)
    hypotheses = [row["diagnostic_name"] for row in rows if row["diagnostic_type"] == "next_fixed_hypothesis"]
    refinement = next((row for row in rows if row["diagnostic_name"] == "cost_aware_refinement_decision"), None)
    defensive_refinement = next((row for row in rows if row["diagnostic_name"] == "partial_defensive_sleeve_decision"), None)
    remaining_refinements = [row for row in rows if row["diagnostic_type"] == "remaining_refinement_batch" and row["diagnostic_name"].endswith("_decision")]
    split_stability = next((row for row in rows if row["diagnostic_name"] == "growth_biased_rotation_split_stability_check"), None)
    lines = [
        "Growth-biased strategy diagnostics. Display only; execution_approved=False.",
        f"Active research lead: {ACTIVE_RESEARCH_LEAD}",
        f"Previous growth-biased baseline: {PREVIOUS_RESEARCH_LEAD}",
        f"Main diagnostic status: {', '.join(statuses) if statuses else 'insufficient_data'}",
    ]
    if worst_split:
        lines.append(f"Worst split: {worst_split['split_name']} - {worst_split['interpretation']}")
    lines.append(f"Cost sensitivity matters: {cost_warning}")
    if drawdown:
        lines.append(f"Drawdown: {drawdown['status']} - {drawdown['interpretation']}")
    if cash:
        lines.append(f"Cash drag: {cash['status']} - {cash['interpretation']}")
    lines.append(f"Stricter breadth gate is active research lead: {active_lead}")
    if refinement:
        lines.append(f"Cost-aware refinement: {refinement['status']} - {refinement['interpretation']}")
    if defensive_refinement:
        lines.append(f"Partial defensive sleeve: {defensive_refinement['status']} - {defensive_refinement['interpretation']}")
    for row in remaining_refinements:
        lines.append(f"{row['strategy_name']}: {row['status']} - {row['interpretation']}")
    if split_stability:
        lines.append(f"Split stability check: {split_stability['status']} - {split_stability['interpretation']}")
    if hypotheses:
        lines.append("Recommended next fixed hypotheses: " + ", ".join(hypotheses[:4]))
    lines.append("Warning: saved diagnostics do not approve orders or paper execution.")
    return 0, lines
