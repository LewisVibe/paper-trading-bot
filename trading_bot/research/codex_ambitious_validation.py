"""Validation checkpoint for the Codex ambitious persistence candidate.

This module reads saved research CSVs only. It does not refresh market data,
load config, call brokers, read positions, write SQLite, send alerts, schedule
anything, create order instructions, approve preview promotion, or approve
execution.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET_STRATEGY = "codex_ambitious_concentrated_growth_persistence"
SPY_BENCHMARK = "spy_buy_and_hold_benchmark"
EQUAL_WEIGHT_BENCHMARK = "equal_weight_etf_buy_and_hold_benchmark"
MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"
PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"
STRICTER_GATE = "growth_biased_rotation_breadth_stricter_gate"
STRICTER_55_REFERENCE = "stricter_55_reference"

INPUT_FILES = {
    "persistence_detail": Path("data/growth_biased_stricter_persistence_filter.csv"),
    "persistence_summary": Path("data/growth_biased_stricter_persistence_filter_summary.csv"),
}

OUTPUT_FILES = {
    "validation": Path("data/codex_ambitious_validation.csv"),
    "summary": Path("data/codex_ambitious_validation_summary.csv"),
    "splits": Path("data/codex_ambitious_validation_splits.csv"),
    "costs": Path("data/codex_ambitious_validation_costs.csv"),
    "drawdowns": Path("data/codex_ambitious_validation_drawdowns.csv"),
}

VALIDATION_LABELS = [
    "codex_ambitious_new_active_research_lead",
    "codex_ambitious_promising_needs_cost_review",
    "codex_ambitious_promising_but_split_sensitive",
    "codex_ambitious_high_return_high_risk",
    "codex_ambitious_cost_fragile",
    "codex_ambitious_not_validated",
    "insufficient_saved_inputs",
    "manual_review_required",
]

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "validation_area",
    "check_name",
    "strategy_name",
    "comparison_strategy",
    "period",
    "cost_level_bps",
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
    "promotion_approved",
    "scheduling_approved",
]


@dataclass
class CodexAmbitiousValidationResult:
    validation_path: Path
    summary_path: Path
    splits_path: Path
    costs_path: Path
    drawdowns_path: Path
    validation_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_codex_ambitious_validation(data_dir: Path | str = "data") -> CodexAmbitiousValidationResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    detail = read_csv(data_path / INPUT_FILES["persistence_detail"].name)
    persistence_summary = read_csv(data_path / INPUT_FILES["persistence_summary"].name)
    target_rows = [row for row in detail if row.get("strategy_name") == TARGET_STRATEGY]

    if not target_rows or any(row.get("status") == "insufficient_saved_inputs" for row in target_rows):
        validation_rows, summary_rows, split_rows, cost_rows, drawdown_rows = insufficient_outputs(created_at, detail)
    else:
        cost_rows = build_cost_rows(created_at, target_rows)
        split_rows = build_split_rows(created_at)
        drawdown_rows = build_drawdown_rows(created_at, target_rows)
        validation_rows = build_validation_rows(created_at, target_rows, cost_rows, split_rows, drawdown_rows)
        summary_rows = [build_summary_row(created_at, target_rows, cost_rows, split_rows, drawdown_rows, persistence_summary)]

    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["validation"], validation_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["splits"], split_rows)
    write_rows(output_paths["costs"], cost_rows)
    write_rows(output_paths["drawdowns"], drawdown_rows)
    return CodexAmbitiousValidationResult(
        validation_path=output_paths["validation"],
        summary_path=output_paths["summary"],
        splits_path=output_paths["splits"],
        costs_path=output_paths["costs"],
        drawdowns_path=output_paths["drawdowns"],
        validation_rows=validation_rows,
        summary_rows=summary_rows,
        split_rows=split_rows,
        cost_rows=cost_rows,
        drawdown_rows=drawdown_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def build_cost_rows(created_at: str, target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base = find_cost_row(target_rows, 0)
    rows = []
    for source in sorted(target_rows, key=lambda row: as_float(row.get("cost_level_bps"))):
        cost_bps = int(as_float(source.get("cost_level_bps")))
        survives = source.get("status") == "credible_after_cost"
        rows.append(
            validation_row(
                created_at,
                "cost_stress",
                f"cost_{cost_bps}_bps",
                cost_level_bps=cost_bps,
                metric_name="cost_adjusted_cagr_sharpe_calmar",
                metric_value=format_metrics(source),
                reference_value=format_metrics(base),
                metric_delta=(
                    f"cagr_decay={source.get('cagr_decay_vs_0_bps', '')}; "
                    f"sharpe_decay={source.get('sharpe_decay_vs_0_bps', '')}; "
                    f"calmar_decay={source.get('calmar_decay_vs_0_bps', '')}"
                ),
                status="cost_survives" if survives else "cost_review_required",
                severity="pass" if survives else "review_required",
                evidence=(
                    f"Cost {cost_bps} bps: {format_metrics(source)}; "
                    f"label={source.get('research_conclusion_label', '')}."
                ),
                interpretation="Cost survival is research-only and does not approve execution.",
                required_next_step="Review whether cost decay is acceptable before active-lead discussion.",
            )
        )
    return rows


def build_split_rows(created_at: str) -> list[dict[str, Any]]:
    return [
        validation_row(
            created_at,
            "split_validation",
            split_name,
            period=split_name,
            status="insufficient_saved_inputs",
            severity="insufficient_data",
            evidence=(
                "Saved persistence-filter output currently contains full-period cost rows only; "
                "no fixed chronological split rows exist for this Codex candidate."
            ),
            interpretation="Split validation remains required before active research-lead change.",
            required_next_step="Add or rerun a split-capable Codex ambitious validation if this remains promising.",
        )
        for split_name in ["split_60_40", "split_70_30", "split_80_20"]
    ]


def build_drawdown_rows(created_at: str, target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base = find_cost_row(target_rows, 0)
    return [
        validation_row(
            created_at,
            "drawdown_review",
            "max_drawdown",
            metric_name="max_drawdown_pct",
            metric_value=base.get("max_drawdown_pct", ""),
            status="drawdown_review_available",
            severity="review_required",
            evidence=f"Saved full-period max drawdown={base.get('max_drawdown_pct', '')}; start/end/recovery are not available in persistence summary.",
            interpretation="Higher drawdown may be acceptable if return/risk compensates, but drawdown windows still need review.",
            required_next_step="Add saved equity-curve drawdown-window validation before preview-candidate discussion.",
        ),
        validation_row(
            created_at,
            "drawdown_review",
            "recovery_duration",
            metric_name="recovery_duration_days",
            status="insufficient_saved_inputs",
            severity="insufficient_data",
            evidence="Saved persistence-filter output does not include equity-curve drawdown recovery data.",
            interpretation="Recovery duration cannot be inferred without saved equity curve rows.",
            required_next_step="Generate a drawdown-window report with equity curve context if this candidate remains strongest.",
        ),
    ]


def build_validation_rows(
    created_at: str,
    target_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base = find_cost_row(target_rows, 0)
    rows = [
        validation_row(
            created_at,
            "full_period",
            "full_period_result",
            metric_name="cagr_sharpe_calmar_maxdd_turnover",
            metric_value=format_full_result(base),
            status="full_period_strong" if beats_core_references(base) else "full_period_review_required",
            severity="pass" if beats_core_references(base) else "review_required",
            evidence=(
                f"SPY gap={base.get('cagr_gap_vs_spy', '')}; stricter gap={base.get('cagr_delta_vs_stricter_reference', '')}; "
                f"original gap={base.get('cagr_delta_vs_original', '')}."
            ),
            interpretation="Full-period strength can support active-lead discussion only after split/cost/drawdown checks.",
        ),
        validation_row(
            created_at,
            "turnover_review",
            "turnover_holding_period",
            metric_name="turnover_and_holding_period",
            metric_value=f"turnover={base.get('turnover', '')}; avg_holding_days={base.get('average_holding_period_days', '')}",
            status="turnover_review_required" if as_float(base.get("turnover")) >= 10 else "turnover_acceptable",
            severity="review_required" if as_float(base.get("turnover")) >= 10 else "pass",
            evidence=f"Trade count={base.get('trade_count', '')}; turnover={base.get('turnover', '')}.",
            interpretation="Turnover does not reject the candidate by itself, but it must be reviewed with cost survival.",
        ),
    ]
    rows.append(
        validation_row(
            created_at,
            "summary",
            "validation_inputs",
            status="manual_review_required" if any(row.get("severity") in {"review_required", "insufficient_data"} for row in cost_rows + split_rows + drawdown_rows) else "codex_ambitious_new_active_research_lead",
            severity="review_required",
            evidence="Validation includes full-period, cost, split, drawdown, and turnover review rows.",
            interpretation="This checkpoint does not automatically promote or approve execution.",
            required_next_step="Resolve split/drawdown/cost review rows before any active research-lead change.",
        )
    )
    return rows


def build_summary_row(
    created_at: str,
    target_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
    persistence_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    base = find_cost_row(target_rows, 0)
    survives_10 = find_cost_row(target_rows, 10).get("status") == "credible_after_cost"
    survives_25 = find_cost_row(target_rows, 25).get("status") == "credible_after_cost"
    beats_spy = as_float(base.get("cagr_gap_vs_spy")) > 0
    beats_stricter = as_float(base.get("cagr_delta_vs_stricter_reference")) > 0
    beats_original = as_float(base.get("cagr_delta_vs_original")) > 0
    split_missing = any(row.get("status") == "insufficient_saved_inputs" for row in split_rows)
    if beats_spy and beats_stricter and beats_original and survives_10 and not split_missing:
        label = "codex_ambitious_new_active_research_lead"
    elif beats_spy and beats_stricter and beats_original and survives_10 and not survives_25:
        label = "codex_ambitious_promising_needs_cost_review"
    elif split_missing:
        label = "codex_ambitious_promising_but_split_sensitive" if beats_spy and beats_stricter else "manual_review_required"
    elif not survives_10:
        label = "codex_ambitious_cost_fragile"
    else:
        label = "codex_ambitious_high_return_high_risk" if beats_original else "codex_ambitious_not_validated"
    severity_counts = Counter(row.get("severity", "") for row in cost_rows + split_rows + drawdown_rows)
    return validation_row(
        created_at,
        "validation_summary",
        "final_validation_label",
        metric_name="final_validation_label",
        metric_value=label,
        status=label,
        severity="review_required" if label != "codex_ambitious_new_active_research_lead" else "pass",
        evidence=(
            f"beats_spy={beats_spy}; beats_stricter_gate={beats_stricter}; beats_original={beats_original}; "
            f"survives_10_bps={survives_10}; survives_25_bps={survives_25}; split_missing={split_missing}; "
            f"severity_counts={dict(severity_counts)}; persistence_label={(persistence_summary[0] if persistence_summary else {}).get('summary_label', '')}."
        ),
        interpretation="Final validation is research-only and does not approve preview promotion or execution.",
        required_next_step=required_next_step(label),
    )


def insufficient_outputs(created_at: str, detail: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    warning = next((row.get("review_warning", "") for row in detail if row.get("review_warning")), "missing persistence-filter output")
    row = validation_row(
        created_at,
        "validation_summary",
        "missing_saved_inputs",
        status="insufficient_saved_inputs",
        severity="insufficient_data",
        evidence=warning,
        interpretation="Run the persistence-filter report with usable market data before validating the Codex ambitious candidate.",
        required_next_step="Run `python bot.py --growth-biased-stricter-persistence-filter` with market data available first.",
    )
    return [row], [row], [row], [row], [row]


def show_codex_ambitious_validation_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    validation = read_csv(data_path / OUTPUT_FILES["validation"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    splits = read_csv(data_path / OUTPUT_FILES["splits"].name)
    costs = read_csv(data_path / OUTPUT_FILES["costs"].name)
    drawdowns = read_csv(data_path / OUTPUT_FILES["drawdowns"].name)
    if not validation or not summary:
        return 1, ["Run `python bot.py --codex-ambitious-validation` first."]
    final = summary[0]
    full = next((row for row in validation if row.get("check_name") == "full_period_result"), {})
    turnover = next((row for row in validation if row.get("check_name") == "turnover_holding_period"), {})
    approval_values = {str(row.get("execution_approved", "")).lower() for row in validation + summary + splits + costs + drawdowns}
    evidence = str(final.get("evidence", ""))
    return 0, [
        "Codex ambitious validation. Display only; execution_approved=False.",
        f"Final validation label: {final.get('status', 'insufficient_saved_inputs')}",
        f"Full-period result: {full.get('metric_value', 'unavailable')}",
        f"Split summary: {status_counts(splits)}",
        f"Cost summary: {status_counts(costs)}",
        f"Worst drawdown summary: {drawdowns[0].get('evidence', 'unavailable') if drawdowns else 'unavailable'}",
        f"Turnover summary: {turnover.get('metric_value', 'unavailable')}",
        f"Beats SPY: {'beats_spy=True' in evidence}",
        f"Beats stricter gate: {'beats_stricter_gate=True' in evidence}",
        f"Beats original crash gate: {'beats_original=True' in evidence}",
        f"Required next review step: {final.get('required_next_step', '')}",
        f"execution_approved values: {', '.join(sorted(approval_values)) or 'false'}",
        "Warning: saved Codex ambitious validation does not approve orders, preview promotion, scheduling, or execution.",
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    summary = summary_rows[0] if summary_rows else {}
    return [
        "Codex ambitious validation complete. Research/report only; execution_approved=False.",
        f"Final validation label: {summary.get('status', 'insufficient_saved_inputs')}",
        f"Evidence: {summary.get('evidence', '')}",
        f"Required next review step: {summary.get('required_next_step', '')}",
        f"Saved validation to {output_paths['validation']}",
        f"Saved summary to {output_paths['summary']}",
        f"Saved splits to {output_paths['splits']}",
        f"Saved costs to {output_paths['costs']}",
        f"Saved drawdowns to {output_paths['drawdowns']}",
        "Warning: validation does not approve orders, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def validation_row(
    created_at: str,
    validation_area: str,
    check_name: str,
    *,
    comparison_strategy: str = "",
    period: str = "",
    cost_level_bps: Any = "",
    metric_name: Any = "",
    metric_value: Any = "",
    reference_value: Any = "",
    metric_delta: Any = "",
    status: str,
    severity: str,
    evidence: str,
    interpretation: str,
    required_next_step: str = "Manual research review only; do not connect to execution.",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "codex_ambitious_validation",
        "validation_area": validation_area,
        "check_name": check_name,
        "strategy_name": TARGET_STRATEGY,
        "comparison_strategy": comparison_strategy,
        "period": period,
        "cost_level_bps": cost_level_bps,
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
        "promotion_approved": False,
        "scheduling_approved": False,
    }


def find_cost_row(rows: list[dict[str, Any]], cost_bps: int) -> dict[str, Any]:
    return next((row for row in rows if str(row.get("cost_level_bps")) == str(cost_bps)), {})


def beats_core_references(row: dict[str, Any]) -> bool:
    return (
        as_float(row.get("cagr_gap_vs_spy")) > 0
        and as_float(row.get("cagr_delta_vs_stricter_reference")) > 0
        and as_float(row.get("cagr_delta_vs_original")) > 0
    )


def format_metrics(row: dict[str, Any]) -> str:
    if not row:
        return "unavailable"
    return f"CAGR={row.get('cost_adjusted_cagr_pct', '')}, Sharpe={row.get('cost_adjusted_sharpe_ratio', '')}, Calmar={row.get('cost_adjusted_calmar_ratio', '')}"


def format_full_result(row: dict[str, Any]) -> str:
    return (
        f"CAGR={row.get('cagr_pct', '')}, Sharpe={row.get('sharpe_ratio', '')}, "
        f"MaxDD={row.get('max_drawdown_pct', '')}, Calmar={row.get('calmar_ratio', '')}, "
        f"cash={row.get('average_cash_weight_pct', '')}, turnover={row.get('turnover', '')}"
    )


def required_next_step(label: str) -> str:
    if label == "codex_ambitious_new_active_research_lead":
        return "Manual active-research-lead review may proceed; execution and preview promotion remain unapproved."
    if label == "codex_ambitious_promising_needs_cost_review":
        return "Review cost survival beyond 10 bps and add split/drawdown-window validation before lead change."
    if label == "codex_ambitious_promising_but_split_sensitive":
        return "Add fixed chronological split validation before active research-lead change."
    if label == "codex_ambitious_cost_fragile":
        return "Review turnover/cost controls before further promotion discussion."
    return "Manual research review required; do not connect to execution."


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(row.get("status", "") for row in rows)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


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


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMMON_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
