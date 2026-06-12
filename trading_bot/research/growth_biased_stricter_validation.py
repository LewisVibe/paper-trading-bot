"""Saved-output validation for the growth-biased stricter breadth-gate lead.

This module reads saved research CSVs only. It does not refresh market data,
load config, call brokers, read positions, write SQLite, send alerts, schedule
anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTIVE_RESEARCH_LEAD = "growth_biased_rotation_breadth_stricter_gate"
PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"
MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"
SPY_BENCHMARK = "spy_buy_and_hold_benchmark"
REJECTED_REFINEMENTS = [
    "growth_biased_rotation_cost_aware_rebalance",
    "growth_biased_rotation_partial_defensive_sleeve",
    "growth_biased_rotation_reentry_filter",
    "growth_biased_rotation_regime_recovery_filter",
    "growth_biased_rotation_breadth_looser_gate",
]

INPUT_FILES = {
    "lab_results": Path("data/strategy_improvement_lab_results.csv"),
    "lab_summary": Path("data/strategy_improvement_lab_summary.csv"),
    "robustness": Path("data/strategy_improvement_robustness_report.csv"),
    "cost": Path("data/strategy_improvement_cost_stress_report.csv"),
    "drawdown": Path("data/strategy_improvement_drawdown_report.csv"),
    "comparison": Path("data/strategy_improvement_candidate_comparison.csv"),
    "diagnostics": Path("data/strategy_improvement_diagnostics.csv"),
    "growth_diagnostics": Path("data/growth_biased_rotation_diagnostics.csv"),
}

OUTPUT_FILES = {
    "validation": Path("data/growth_biased_stricter_validation.csv"),
    "split": Path("data/growth_biased_stricter_split_validation.csv"),
    "cost": Path("data/growth_biased_stricter_cost_review.csv"),
    "drawdown": Path("data/growth_biased_stricter_drawdown_review.csv"),
    "promotion": Path("data/growth_biased_stricter_promotion_checkpoint.csv"),
}

VALIDATION_COLUMNS = [
    "created_at",
    "validation_area",
    "check_name",
    "strategy_name",
    "comparison_strategy",
    "period",
    "split_name",
    "cost_label",
    "metric_name",
    "metric_value",
    "reference_value",
    "metric_delta",
    "status",
    "severity",
    "evidence",
    "interpretation",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
]


@dataclass
class GrowthBiasedStricterValidationResult:
    validation_path: Path
    split_path: Path
    cost_path: Path
    drawdown_path: Path
    promotion_path: Path
    validation_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_growth_biased_stricter_validation(
    root_dir: Path | str = ".",
) -> GrowthBiasedStricterValidationResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(root / path) for name, path in INPUT_FILES.items()}
    missing = [str(path) for name, path in INPUT_FILES.items() if not inputs[name]]

    if missing:
        rows_by_output = insufficient_output_rows(created_at, missing)
    else:
        rows_by_output = build_validation_outputs(created_at, inputs)

    for key, path in OUTPUT_FILES.items():
        write_rows(root / path, rows_by_output[key])

    validation_rows = rows_by_output["validation"]
    return GrowthBiasedStricterValidationResult(
        validation_path=root / OUTPUT_FILES["validation"],
        split_path=root / OUTPUT_FILES["split"],
        cost_path=root / OUTPUT_FILES["cost"],
        drawdown_path=root / OUTPUT_FILES["drawdown"],
        promotion_path=root / OUTPUT_FILES["promotion"],
        validation_rows=validation_rows,
        summary_lines=build_summary_lines(rows_by_output, root),
    )


def build_validation_outputs(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    split_rows = build_split_validation_rows(created_at, inputs)
    cost_rows = build_cost_review_rows(created_at, inputs)
    drawdown_rows = build_drawdown_review_rows(created_at, inputs)
    promotion_rows = build_promotion_checkpoint_rows(created_at, inputs, split_rows, cost_rows, drawdown_rows)
    validation_rows = [
        summary_row(created_at, "split_validation", split_rows),
        summary_row(created_at, "cost_stress_review", cost_rows),
        summary_row(created_at, "drawdown_period_review", drawdown_rows),
        summary_row(created_at, "promotion_checkpoint", promotion_rows),
    ]
    return {
        "validation": validation_rows,
        "split": split_rows,
        "cost": cost_rows,
        "drawdown": drawdown_rows,
        "promotion": promotion_rows,
    }


def build_split_validation_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    robustness = inputs["robustness"]
    comparison = inputs["comparison"]
    active_splits = [row for row in robustness if row.get("strategy_name") == ACTIVE_RESEARCH_LEAD]
    baseline_splits = [row for row in robustness if row.get("strategy_name") == PREVIOUS_RESEARCH_LEAD]
    active_full = find_row(inputs["lab_summary"], ACTIVE_RESEARCH_LEAD)
    baseline_full = find_row(inputs["lab_summary"], PREVIOUS_RESEARCH_LEAD)
    active_comparison = find_row(comparison, ACTIVE_RESEARCH_LEAD)
    baseline_comparison = find_row(comparison, PREVIOUS_RESEARCH_LEAD)

    if not active_splits or not baseline_splits or not active_full or not baseline_full:
        return [validation_row(created_at, "split_validation", "saved_split_inputs", status="insufficient_data", evidence="Missing saved split or full-period rows.")]

    full_delta = as_float(active_full.get("calmar_ratio")) - as_float(baseline_full.get("calmar_ratio"))
    rows.append(
        validation_row(
            created_at,
            "split_validation",
            "full_period_calmar_delta",
            metric_name="calmar_ratio",
            metric_value=active_full.get("calmar_ratio"),
            reference_value=baseline_full.get("calmar_ratio"),
            metric_delta=round(full_delta, 4),
            status="validation_pass_research_lead" if full_delta > 0 else "validation_not_ready_for_preview",
            evidence=f"Full-period Calmar delta vs previous baseline={round(full_delta, 4)}.",
        )
    )

    for metric in ["cagr_pct", "sharpe_ratio", "calmar_ratio", "max_drawdown_pct"]:
        worst = worst_split(active_splits, metric)
        rows.append(
            validation_row(
                created_at,
                "split_validation",
                f"worst_split_by_{metric}",
                period=worst.get("period", ""),
                split_name=worst.get("split_name", ""),
                metric_name=metric,
                metric_value=worst.get(metric, ""),
                status="validation_promising_needs_more_splits",
                evidence=f"Worst saved split for {metric}: {worst.get('split_name', '')}={worst.get(metric, '')}.",
                interpretation="Worst split is a validation checkpoint, not execution approval.",
            )
        )

    split_wins = count_split_wins(active_splits, baseline_splits)
    status = "validation_pass_research_lead" if split_wins["wins"] >= split_wins["total"] / 2 else "validation_promising_needs_more_splits"
    rows.append(
        validation_row(
            created_at,
            "split_validation",
            "split_wins_vs_previous_baseline",
            metric_name="cagr_sharpe_calmar_split_wins",
            metric_value=split_wins["wins"],
            reference_value=split_wins["total"],
            status=status,
            evidence=f"Stricter gate beats previous baseline on {split_wins['wins']} of {split_wins['total']} saved split metric checks.",
            interpretation="A majority split win supports research-lead status, but still requires checkpoint review.",
        )
    )
    rows.append(
        validation_row(
            created_at,
            "split_validation",
            "split_sensitivity_delta",
            metric_name="split_sensitive",
            metric_value=active_comparison.get("split_sensitive") if active_comparison else "",
            reference_value=baseline_comparison.get("split_sensitive") if baseline_comparison else "",
            metric_delta=bool_delta(active_comparison.get("split_sensitive") if active_comparison else "", baseline_comparison.get("split_sensitive") if baseline_comparison else ""),
            status="validation_promising_needs_more_splits",
            evidence=f"Split sensitivity delta vs previous baseline={bool_delta(active_comparison.get('split_sensitive') if active_comparison else '', baseline_comparison.get('split_sensitive') if baseline_comparison else '')}.",
            interpretation="Unchanged split sensitivity means validation continues before preview discussion.",
        )
    )
    return rows


def build_cost_review_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    cost_rows = inputs["cost"]
    active_rows = {row.get("cost_label"): row for row in cost_rows if row.get("strategy_name") == ACTIVE_RESEARCH_LEAD}
    baseline_rows = {row.get("cost_label"): row for row in cost_rows if row.get("strategy_name") == PREVIOUS_RESEARCH_LEAD}
    if not active_rows or not baseline_rows:
        return [validation_row(created_at, "cost_stress_review", "saved_cost_inputs", status="insufficient_data", evidence="Missing saved cost stress rows.")]

    lost_any = False
    for cost_label in ["low_cost", "default_cost", "high_cost"]:
        active = active_rows.get(cost_label)
        baseline = baseline_rows.get(cost_label)
        if not active or not baseline:
            rows.append(validation_row(created_at, "cost_stress_review", f"{cost_label}_cost_row", cost_label=cost_label, status="insufficient_data", evidence="Missing cost row."))
            continue
        delta = as_float(active.get("cost_adjusted_calmar_ratio")) - as_float(baseline.get("cost_adjusted_calmar_ratio"))
        lost = delta <= 0
        lost_any = lost_any or lost
        rows.append(
            validation_row(
                created_at,
                "cost_stress_review",
                f"{cost_label}_calmar_advantage",
                cost_label=cost_label,
                metric_name="cost_adjusted_calmar_ratio",
                metric_value=active.get("cost_adjusted_calmar_ratio"),
                reference_value=baseline.get("cost_adjusted_calmar_ratio"),
                metric_delta=round(delta, 4),
                status="stricter_cost_advantage_lost" if lost else "stricter_cost_resilient",
                evidence=f"{cost_label}: stricter cost-adjusted Calmar delta={round(delta, 4)}.",
                interpretation="Cost review is research-only and does not approve execution.",
            )
        )

    high_cost = next((row for row in rows if row.get("cost_label") == "high_cost"), None)
    summary_status = "stricter_cost_advantage_lost" if lost_any else "stricter_cost_resilient"
    if high_cost and high_cost.get("status") == "stricter_cost_advantage_lost":
        summary_status = "stricter_cost_sensitive"
    rows.append(
        validation_row(
            created_at,
            "cost_stress_review",
            "cost_stress_conclusion",
            status=summary_status,
            evidence=f"High-cost status={high_cost.get('status') if high_cost else 'missing'}.",
            interpretation="Turnover reduction helps only if the stricter gate retains its advantage after saved cost stress.",
        )
    )
    return rows


def build_drawdown_review_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    drawdown = inputs["drawdown"]
    active = find_row(drawdown, ACTIVE_RESEARCH_LEAD)
    baseline = find_row(drawdown, PREVIOUS_RESEARCH_LEAD)
    rotation = find_row(drawdown, MONTHLY_ROTATION_REFERENCE)
    spy = find_row(drawdown, SPY_BENCHMARK)
    if not active:
        return [validation_row(created_at, "drawdown_period_review", "saved_drawdown_inputs", status="insufficient_data", evidence="Missing active-lead drawdown row.")]

    rows.append(
        validation_row(
            created_at,
            "drawdown_period_review",
            "worst_drawdown_window",
            metric_name="worst_drawdown_pct",
            metric_value=active.get("worst_drawdown_pct"),
            status="validation_drawdown_watch",
            evidence=f"Worst drawdown {active.get('worst_drawdown_pct')}% from {active.get('worst_drawdown_start')} to {active.get('worst_drawdown_end')}.",
            interpretation="Worst drawdown remains a research watch item before preview discussion.",
        )
    )
    for name, reference in [
        (PREVIOUS_RESEARCH_LEAD, baseline),
        (MONTHLY_ROTATION_REFERENCE, rotation),
        (SPY_BENCHMARK, spy),
    ]:
        if not reference:
            rows.append(validation_row(created_at, "drawdown_period_review", f"drawdown_vs_{name}", comparison_strategy=name, status="insufficient_data", evidence="Missing reference drawdown row."))
            continue
        delta = as_float(active.get("worst_drawdown_pct")) - as_float(reference.get("worst_drawdown_pct"))
        rows.append(
            validation_row(
                created_at,
                "drawdown_period_review",
                f"drawdown_vs_{name}",
                comparison_strategy=name,
                metric_name="worst_drawdown_pct",
                metric_value=active.get("worst_drawdown_pct"),
                reference_value=reference.get("worst_drawdown_pct"),
                metric_delta=round(delta, 4),
                status="validation_pass_research_lead" if delta >= -0.5 else "validation_drawdown_watch",
                evidence=f"Drawdown delta vs {name}={round(delta, 4)}.",
                interpretation="Drawdown comparison is research-only context.",
            )
        )
    rows.append(
        validation_row(
            created_at,
            "drawdown_period_review",
            "drawdown_conclusion",
            status="validation_drawdown_watch",
            evidence="Drawdown remained acceptable in diagnostics, but still needs period review before preview.",
            interpretation="Acceptable drawdown does not approve orders or preview integration.",
        )
    )
    return rows


def build_promotion_checkpoint_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    split_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    comparison = inputs["comparison"]
    active = find_row(comparison, ACTIVE_RESEARCH_LEAD)
    active_rows = [row for row in comparison if row.get("strategy_name") and not str(row.get("strategy_name")).endswith("_benchmark")]
    best_calmar = max(active_rows, key=lambda row: as_float(row.get("calmar_ratio")), default=None)
    is_lead = bool(best_calmar and best_calmar.get("strategy_name") == ACTIVE_RESEARCH_LEAD)
    trails_spy = parse_bool(active.get("trails_spy_buy_and_hold")) if active else True
    split_sensitive = parse_bool(active.get("split_sensitive")) if active else True
    cost_sensitive = parse_bool(active.get("cost_sensitive")) if active else True
    blockers = []
    if trails_spy:
        blockers.append("trails_spy_buy_and_hold")
    if split_sensitive:
        blockers.append("split_sensitive")
    if cost_sensitive:
        blockers.append("cost_sensitive")
    if any(row.get("status") in {"insufficient_data", "validation_drawdown_watch"} for row in drawdown_rows):
        blockers.append("drawdown_period_review_needed")

    ready_for_preview_discussion = is_lead and not cost_sensitive
    status = "validation_pass_research_lead" if is_lead else "validation_not_ready_for_preview"
    if trails_spy:
        status = "validation_benchmark_lagging"
    if split_sensitive:
        status = "validation_promising_needs_more_splits"
    if cost_sensitive:
        status = "validation_cost_sensitive"

    return [
        validation_row(
            created_at,
            "promotion_checkpoint",
            "active_research_lead_check",
            metric_name="active_research_lead",
            metric_value=is_lead,
            status="validation_pass_research_lead" if is_lead else "validation_not_ready_for_preview",
            evidence=f"Best active Calmar strategy={best_calmar.get('strategy_name') if best_calmar else ''}.",
            interpretation="Research lead status is not execution approval.",
        ),
        validation_row(
            created_at,
            "promotion_checkpoint",
            "preview_discussion_eligibility",
            metric_name="ready_for_future_preview_candidate_discussion",
            metric_value=ready_for_preview_discussion,
            status=status,
            evidence=f"Blockers: {', '.join(blockers) if blockers else 'none'}.",
            interpretation="Future preview-candidate discussion still requires a separate manual checkpoint.",
            required_next_step="Run stricter-gate validation reviews before any promoted-review pipeline integration.",
        ),
        validation_row(
            created_at,
            "promotion_checkpoint",
            "execution_approval_boundary",
            metric_name="execution_approved",
            metric_value=False,
            status="validation_not_ready_for_preview" if not ready_for_preview_discussion else "validation_pass_research_lead",
            evidence="Validation pass means research lead or future preview discussion only.",
            interpretation="This checkpoint does not approve execution, paper execution, scheduling, or promoted execution.",
        ),
    ]


def insufficient_output_rows(created_at: str, missing: list[str]) -> dict[str, list[dict[str, Any]]]:
    evidence = "Missing saved inputs: " + ", ".join(missing)
    next_step = (
        "Run `python bot.py --strategy-improvement-lab`, "
        "`python bot.py --strategy-improvement-robustness`, and "
        "`python bot.py --strategy-improvement-diagnostics` first."
    )
    return {
        key: [
            validation_row(
                created_at,
                key,
                "missing_saved_inputs",
                status="insufficient_data",
                evidence=evidence,
                interpretation="Validation reads saved CSV outputs only and does not refresh market data.",
                required_next_step=next_step,
            )
        ]
        for key in OUTPUT_FILES
    }


def summary_row(created_at: str, area: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return validation_row(created_at, "validation_summary", area, status="insufficient_data", evidence="No rows generated.")
    statuses = [str(row.get("status", "")) for row in rows]
    if "insufficient_data" in statuses:
        status = "insufficient_data"
    elif any(status in statuses for status in ["validation_cost_sensitive", "stricter_cost_sensitive", "stricter_cost_advantage_lost"]):
        status = "validation_cost_sensitive"
    elif any(status in statuses for status in ["validation_drawdown_watch", "validation_benchmark_lagging"]):
        status = "validation_drawdown_watch"
    elif any(status in statuses for status in ["validation_promising_needs_more_splits"]):
        status = "validation_promising_needs_more_splits"
    else:
        status = "validation_pass_research_lead"
    return validation_row(
        created_at,
        "validation_summary",
        area,
        status=status,
        evidence="; ".join(statuses[:8]),
        interpretation="Summary row for the saved stricter-gate validation checkpoint.",
    )


def validation_row(
    created_at: str,
    validation_area: str,
    check_name: str,
    *,
    strategy_name: str = ACTIVE_RESEARCH_LEAD,
    comparison_strategy: str = PREVIOUS_RESEARCH_LEAD,
    period: Any = "",
    split_name: Any = "",
    cost_label: Any = "",
    metric_name: Any = "",
    metric_value: Any = "",
    reference_value: Any = "",
    metric_delta: Any = "",
    status: str = "insufficient_data",
    severity: str = "info",
    evidence: str = "",
    interpretation: str = "",
    required_next_step: str = "Manual research review only; do not connect to execution.",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "validation_area": validation_area,
        "check_name": check_name,
        "strategy_name": strategy_name,
        "comparison_strategy": comparison_strategy,
        "period": period,
        "split_name": split_name,
        "cost_label": cost_label,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "reference_value": reference_value,
        "metric_delta": metric_delta,
        "status": status,
        "severity": severity,
        "evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
    }


def build_summary_lines(rows_by_output: dict[str, list[dict[str, Any]]], root: Path) -> list[str]:
    validation = rows_by_output["validation"]
    split = rows_by_output["split"]
    cost = rows_by_output["cost"]
    drawdown = rows_by_output["drawdown"]
    promotion = rows_by_output["promotion"]
    promotion_conclusion = next((row for row in promotion if row.get("check_name") == "preview_discussion_eligibility"), promotion[0])
    return [
        "Growth-biased stricter validation complete. Research/preview only; execution_approved=False.",
        f"Active research lead: {ACTIVE_RESEARCH_LEAD}",
        f"Previous growth-biased baseline: {PREVIOUS_RESEARCH_LEAD}",
        f"Validation status: {validation[0].get('status') if validation else 'insufficient_data'}",
        f"Split validation: {first_status(split)}",
        f"Cost stress review: {first_named_status(cost, 'cost_stress_conclusion')}",
        f"Drawdown review: {first_named_status(drawdown, 'drawdown_conclusion')}",
        f"Promotion checkpoint: {promotion_conclusion.get('status')}",
        f"Ready for future preview-candidate discussion: {promotion_conclusion.get('metric_value')}",
        f"Saved validation to {root / OUTPUT_FILES['validation']}",
        "Warning: validation is research-only and does not approve orders, paper execution, scheduling, or promoted execution.",
    ]


def show_growth_biased_stricter_validation_file(
    root_dir: Path | str = ".",
) -> tuple[int, list[str]]:
    root = Path(root_dir)
    validation = read_csv(root / OUTPUT_FILES["validation"])
    split = read_csv(root / OUTPUT_FILES["split"])
    cost = read_csv(root / OUTPUT_FILES["cost"])
    drawdown = read_csv(root / OUTPUT_FILES["drawdown"])
    promotion = read_csv(root / OUTPUT_FILES["promotion"])
    if not validation:
        return 1, ["Run `python bot.py --growth-biased-stricter-validation` first."]

    promotion_conclusion = next((row for row in promotion if row.get("check_name") == "preview_discussion_eligibility"), promotion[0] if promotion else {})
    trails_spy = "unknown"
    split_sensitive = "unknown"
    if promotion_conclusion:
        evidence = str(promotion_conclusion.get("evidence", ""))
        trails_spy = str("trails_spy_buy_and_hold" in evidence)
        split_sensitive = str("split_sensitive" in evidence)
    return 0, [
        "Growth-biased stricter validation. Display only; execution_approved=False.",
        f"Active research lead: {ACTIVE_RESEARCH_LEAD}",
        f"Validation status: {validation[0].get('status')}",
        f"Worst split: {worst_split_line(split)}",
        f"Cost stress conclusion: {first_named_status(cost, 'cost_stress_conclusion')}",
        f"Drawdown conclusion: {first_named_status(drawdown, 'drawdown_conclusion')}",
        f"Promotion checkpoint conclusion: {promotion_conclusion.get('status', 'insufficient_data')}",
        f"Still trails SPY: {trails_spy}",
        f"Still split sensitive: {split_sensitive}",
        f"Ready for future preview-candidate discussion: {promotion_conclusion.get('metric_value', False)}",
        "Warning: saved validation does not approve orders, paper execution, scheduling, or promoted execution.",
    ]


def first_status(rows: list[dict[str, Any]]) -> str:
    return rows[0].get("status", "insufficient_data") if rows else "insufficient_data"


def first_named_status(rows: list[dict[str, Any]], check_name: str) -> str:
    row = next((item for item in rows if item.get("check_name") == check_name), None)
    return row.get("status", "insufficient_data") if row else first_status(rows)


def worst_split_line(rows: list[dict[str, Any]]) -> str:
    worst = next((row for row in rows if str(row.get("check_name", "")).startswith("worst_split_by_calmar")), None)
    if not worst:
        return "insufficient_data"
    return f"{worst.get('split_name')} ({worst.get('metric_name')}={worst.get('metric_value')})"


def count_split_wins(active_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> dict[str, int]:
    baseline_by_split = {row.get("split_name"): row for row in baseline_rows}
    wins = 0
    total = 0
    for active in active_rows:
        baseline = baseline_by_split.get(active.get("split_name"))
        if not baseline:
            continue
        for metric in ["cagr_pct", "sharpe_ratio", "calmar_ratio"]:
            total += 1
            if as_float(active.get(metric)) > as_float(baseline.get(metric)):
                wins += 1
    return {"wins": wins, "total": total}


def worst_split(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    if metric == "max_drawdown_pct":
        return min(rows, key=lambda row: as_float(row.get(metric)))
    return min(rows, key=lambda row: as_float(row.get(metric)))


def find_row(rows: list[dict[str, Any]], strategy_name: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("strategy_name") == strategy_name and row.get("period", "full_period") == "full_period":
            return row
    for row in rows:
        if row.get("strategy_name") == strategy_name:
            return row
    return None


def bool_delta(value: Any, reference: Any) -> str:
    value_bool = parse_bool(value)
    reference_bool = parse_bool(reference)
    if value_bool == reference_bool:
        return "unchanged"
    if reference_bool and not value_bool:
        return "improved"
    return "worse"


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
        writer = csv.DictWriter(handle, fieldnames=VALIDATION_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
