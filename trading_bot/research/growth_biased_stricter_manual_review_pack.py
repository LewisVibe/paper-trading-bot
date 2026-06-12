"""Manual review pack for the stricter growth-biased research lead.

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


ACTIVE_RESEARCH_LEAD = "growth_biased_rotation_breadth_stricter_gate"
PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"
MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"
SPY_BENCHMARK = "spy_buy_and_hold_benchmark"
EQUAL_WEIGHT_BENCHMARK = "equal_weight_etf_buy_and_hold_benchmark"

REQUIRED_INPUT_FILES = {
    "lab_summary": Path("data/strategy_improvement_lab_summary.csv"),
    "robustness": Path("data/strategy_improvement_robustness_report.csv"),
    "candidate_comparison": Path("data/strategy_improvement_candidate_comparison.csv"),
    "validation": Path("data/growth_biased_stricter_validation.csv"),
    "split": Path("data/growth_biased_stricter_split_validation.csv"),
    "cost": Path("data/growth_biased_stricter_cost_review.csv"),
    "drawdown": Path("data/growth_biased_stricter_drawdown_review.csv"),
    "benchmark": Path("data/growth_biased_stricter_benchmark_comparison.csv"),
    "promotion": Path("data/growth_biased_stricter_promotion_checkpoint.csv"),
}

OPTIONAL_INPUT_FILES = {
    "promotion_readiness": Path("data/growth_biased_stricter_promotion_readiness.csv"),
    "promotion_blockers": Path("data/growth_biased_stricter_promotion_blockers.csv"),
    "diagnostics": Path("data/strategy_improvement_diagnostics.csv"),
    "growth_diagnostics": Path("data/growth_biased_rotation_diagnostics.csv"),
}

OUTPUT_FILES = {
    "review_pack": Path("data/growth_biased_stricter_manual_review_pack.csv"),
    "regime_context": Path("data/growth_biased_stricter_regime_context.csv"),
}

REVIEW_COLUMNS = [
    "created_at",
    "report_name",
    "row_type",
    "context_name",
    "check_name",
    "strategy_name",
    "comparison_strategy",
    "status",
    "severity",
    "metric_name",
    "metric_value",
    "reference_value",
    "metric_delta",
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

MISSING_INPUT_STEP = (
    "Run `python bot.py --strategy-improvement-lab`, "
    "`python bot.py --strategy-improvement-robustness`, "
    "`python bot.py --strategy-improvement-diagnostics`, "
    "`python bot.py --growth-biased-stricter-validation`, and "
    "`python bot.py --growth-biased-stricter-promotion-readiness` first."
)


@dataclass
class ManualReviewPackResult:
    review_pack_path: Path
    regime_context_path: Path
    review_rows: list[dict[str, Any]]
    regime_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_growth_biased_stricter_manual_review_pack(
    root_dir: Path | str = ".",
) -> ManualReviewPackResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {
        name: read_csv(root / path)
        for name, path in {**REQUIRED_INPUT_FILES, **OPTIONAL_INPUT_FILES}.items()
    }
    missing_required = [
        str(path)
        for name, path in REQUIRED_INPUT_FILES.items()
        if not (root / path).exists() or not inputs[name]
    ]

    if missing_required:
        review_rows = build_missing_input_rows(created_at, missing_required)
        regime_rows = [
            review_row(
                created_at,
                "regime_context",
                "insufficient_data",
                "missing_saved_input",
                status="manual_review_pack_blocked_missing_inputs",
                severity="insufficient_data",
                evidence="Missing saved inputs: " + ", ".join(missing_required),
                interpretation="Regime context uses saved research outputs only and cannot infer missing data.",
                required_next_step=MISSING_INPUT_STEP,
            )
        ]
    else:
        review_rows = build_review_rows(created_at, inputs)
        regime_rows = build_regime_context_rows(created_at, inputs)

    write_rows(root / OUTPUT_FILES["review_pack"], review_rows)
    write_rows(root / OUTPUT_FILES["regime_context"], regime_rows)

    return ManualReviewPackResult(
        review_pack_path=root / OUTPUT_FILES["review_pack"],
        regime_context_path=root / OUTPUT_FILES["regime_context"],
        review_rows=review_rows,
        regime_rows=regime_rows,
        summary_lines=build_summary_lines(review_rows, regime_rows, root),
    )


def build_review_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        active_lead_row(created_at, inputs),
        benchmark_lag_row(created_at, inputs),
        improvement_vs_original_row(created_at, inputs),
        drawdown_context_row(created_at, inputs),
        split_validation_context_row(created_at, inputs),
        cost_sensitivity_context_row(created_at, inputs),
        cash_drag_context_row(created_at, inputs),
        turnover_context_row(created_at, inputs),
        manual_review_only_row(created_at),
    ]
    rows.append(final_preview_discussion_row(created_at, inputs, rows))
    return rows


def active_lead_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    candidates = [
        row
        for row in inputs["candidate_comparison"]
        if row.get("strategy_name") and not str(row.get("strategy_name")).endswith("_benchmark")
    ]
    best = max(candidates, key=lambda row: as_float(row.get("calmar_ratio")), default={})
    is_lead = best.get("strategy_name") == ACTIVE_RESEARCH_LEAD
    return review_row(
        created_at,
        "manual_review_pack",
        "full_period",
        "current_active_lead",
        status="manual_review_pack_pass" if is_lead else "manual_review_pack_needs_review",
        severity="pass" if is_lead else "review_required",
        metric_name="active_research_lead",
        metric_value=is_lead,
        evidence=f"Best saved active Calmar strategy={best.get('strategy_name', 'missing')}.",
        interpretation="Active research-lead status is manual review context only.",
        required_next_step="Confirm active-lead status remains true before any preview-candidate discussion.",
    )


def benchmark_lag_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    candidate = find_row(inputs["candidate_comparison"], ACTIVE_RESEARCH_LEAD)
    spy = first_row(inputs["benchmark"], "comparison_strategy", SPY_BENCHMARK)
    trails_spy = parse_bool(candidate.get("trails_spy_buy_and_hold")) if candidate else bool(spy)
    status = "manual_review_pack_needs_review" if trails_spy else "manual_review_pack_pass"
    return review_row(
        created_at,
        "manual_review_pack",
        "full_period",
        "benchmark_lag_vs_spy",
        comparison_strategy=SPY_BENCHMARK,
        status=status,
        severity="review_required" if trails_spy else "pass",
        metric_name="trails_spy_buy_and_hold",
        metric_value=trails_spy,
        evidence=spy.get("evidence", "Saved comparison indicates SPY lag context is unavailable."),
        interpretation="Trailing SPY is not automatic rejection, but it requires risk-role justification.",
        required_next_step="Document why an active strategy is useful despite SPY lag before preview-candidate discussion.",
    )


def improvement_vs_original_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    row = first_row(inputs["benchmark"], "comparison_strategy", PREVIOUS_RESEARCH_LEAD)
    status = "manual_review_pack_pass" if row.get("status") == "beats_active_reference" else "manual_review_pack_needs_review"
    return review_row(
        created_at,
        "manual_review_pack",
        "full_period",
        "improvement_vs_original_crash_gate",
        comparison_strategy=PREVIOUS_RESEARCH_LEAD,
        status=status,
        severity="pass" if status == "manual_review_pack_pass" else "review_required",
        metric_name="cagr_sharpe_calmar_maxdd_cash_delta",
        metric_delta=row.get("metric_delta", ""),
        evidence=row.get("evidence", "Saved improvement row is missing."),
        interpretation="Improvement versus the previous lead supports research credibility only.",
    )


def drawdown_context_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    conclusion = first_row(inputs["drawdown"], "check_name", "drawdown_conclusion")
    status_value = str(conclusion.get("status", ""))
    status = "manual_review_pack_pass" if status_value == "drawdown_acceptable_for_return" else "manual_review_pack_needs_review"
    return review_row(
        created_at,
        "manual_review_pack",
        "drawdown_period",
        "drawdown_context",
        status=status,
        severity="pass" if status == "manual_review_pack_pass" else "review_required",
        metric_name="drawdown_conclusion",
        metric_value=status_value,
        evidence=conclusion.get("evidence", "Saved drawdown conclusion is missing."),
        interpretation="Drawdown context is structural review only, not an execution gate.",
        required_next_step="Review worst drawdown and recovery context before preview-candidate discussion.",
    )


def split_validation_context_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary = first_row(inputs["validation"], "check_name", "split_validation")
    candidate = find_row(inputs["candidate_comparison"], ACTIVE_RESEARCH_LEAD)
    split_sensitive = parse_bool(candidate.get("split_sensitive")) if candidate else True
    status = "manual_review_pack_needs_review" if split_sensitive else "manual_review_pack_pass"
    return review_row(
        created_at,
        "manual_review_pack",
        "split_validation",
        "split_validation_context",
        status=status,
        severity="review_required" if split_sensitive else "pass",
        metric_name="split_validation_status",
        metric_value=summary.get("status", "insufficient_data"),
        evidence=(
            f"Validation summary={summary.get('status', 'missing')}; "
            f"split_sensitive={split_sensitive}."
        ),
        interpretation="Split validation supports the research lead, but sensitivity remains a manual-review topic when present.",
        required_next_step="Confirm split sensitivity is acceptable before preview-candidate discussion.",
    )


def cost_sensitivity_context_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    cost = first_row(inputs["cost"], "check_name", "cost_stress_conclusion")
    promotion = first_row(inputs["promotion"], "check_name", "preview_discussion_eligibility")
    status_value = str(cost.get("status", ""))
    promotion_status = str(promotion.get("status", ""))
    needs_review = promotion_status == "validation_cost_sensitive" or status_value != "stricter_cost_resilient"
    return review_row(
        created_at,
        "manual_review_pack",
        "cost_stress",
        "cost_sensitivity_context",
        status="manual_review_pack_needs_review" if needs_review else "manual_review_pack_pass",
        severity="review_required" if needs_review else "pass",
        metric_name="cost_status",
        metric_value=status_value,
        evidence=f"Cost conclusion={status_value}; promotion checkpoint={promotion_status}.",
        interpretation="Cost resilience helps, but any cost-sensitive flag remains a review item.",
        required_next_step="Resolve the cost-sensitive checkpoint before preview-candidate discussion.",
    )


def cash_drag_context_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    active = find_row(inputs["lab_summary"], ACTIVE_RESEARCH_LEAD)
    baseline = find_row(inputs["lab_summary"], PREVIOUS_RESEARCH_LEAD)
    delta = as_float(active.get("average_cash_weight_pct")) - as_float(baseline.get("average_cash_weight_pct"))
    return review_row(
        created_at,
        "manual_review_pack",
        "full_period",
        "cash_drag_context",
        comparison_strategy=PREVIOUS_RESEARCH_LEAD,
        status="manual_review_pack_pass" if abs(delta) <= 0.5 else "manual_review_pack_needs_review",
        severity="pass" if abs(delta) <= 0.5 else "review_required",
        metric_name="average_cash_weight_pct",
        metric_value=active.get("average_cash_weight_pct", ""),
        reference_value=baseline.get("average_cash_weight_pct", ""),
        metric_delta=round(delta, 4),
        evidence=f"Average cash weight delta versus previous lead={round(delta, 4)}.",
        interpretation="Cash drag context helps explain structural tradeoffs only.",
    )


def turnover_context_row(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    active = find_row(inputs["lab_summary"], ACTIVE_RESEARCH_LEAD)
    baseline = find_row(inputs["lab_summary"], PREVIOUS_RESEARCH_LEAD)
    trade_delta = as_float(active.get("trade_count")) - as_float(baseline.get("trade_count"))
    turnover_delta = as_float(active.get("average_turnover_pct")) - as_float(baseline.get("average_turnover_pct"))
    return review_row(
        created_at,
        "manual_review_pack",
        "full_period",
        "turnover_trade_count_context",
        comparison_strategy=PREVIOUS_RESEARCH_LEAD,
        status="manual_review_pack_pass" if trade_delta <= 0 and turnover_delta <= 0 else "manual_review_pack_needs_review",
        severity="pass" if trade_delta <= 0 and turnover_delta <= 0 else "review_required",
        metric_name="trade_count_and_turnover_delta",
        metric_value=active.get("trade_count", ""),
        reference_value=baseline.get("trade_count", ""),
        metric_delta=f"trade_delta={round(trade_delta, 4)}; turnover_delta={round(turnover_delta, 4)}",
        evidence=f"Trade delta={round(trade_delta, 4)}; turnover delta={round(turnover_delta, 4)} versus previous lead.",
        interpretation="Lower turnover/trade count can support structural credibility but does not approve execution.",
    )


def manual_review_only_row(created_at: str) -> dict[str, Any]:
    return review_row(
        created_at,
        "manual_review_pack",
        "approval_boundary",
        "manual_review_only_boundary",
        status="preview_candidate_discussion_not_approved",
        severity="review_required",
        metric_name="execution_approved",
        metric_value=False,
        evidence="execution_approved=False; paper_execution_approved=False; promotion_approved=False; scheduling_approved=False.",
        interpretation="This pack is manual review support only and creates no buy/sell/order instructions.",
        required_next_step="Run a separate manual checkpoint before any preview-candidate discussion.",
    )


def final_preview_discussion_row(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    review_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    readiness_final = first_row(inputs["promotion_blockers"], "check_name", "final_preview_readiness")
    readiness_status = str(readiness_final.get("status", ""))
    severities = {str(row.get("severity", "")) for row in review_rows}
    if "insufficient_data" in severities:
        status = "manual_review_pack_blocked_missing_inputs"
        severity = "insufficient_data"
        next_step = MISSING_INPUT_STEP
    elif readiness_status == "ready_for_future_preview_discussion":
        status = "preview_candidate_discussion_allowed_research_only"
        severity = "pass"
        next_step = "Perform separate manual preview-candidate review; do not approve execution."
    elif readiness_status == "nearly_ready_needs_manual_review" or "review_required" in severities:
        status = "preview_candidate_discussion_manual_review_required"
        severity = "review_required"
        next_step = "Resolve manual review rows before preview-candidate discussion."
    else:
        status = "preview_candidate_discussion_not_approved"
        severity = "review_required"
        next_step = "Run promotion-readiness blocker review and resolve blockers first."
    return review_row(
        created_at,
        "manual_review_pack",
        "final",
        "preview_candidate_discussion_status",
        status=status,
        severity=severity,
        metric_name="preview_candidate_discussion_allowed",
        metric_value=status == "preview_candidate_discussion_allowed_research_only",
        evidence=f"Promotion-readiness final status={readiness_status or 'missing'}; review severities={sorted(severities)}.",
        interpretation="The final state is conservative and never approves execution or preview promotion automatically.",
        required_next_step=next_step,
    )


def build_regime_context_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for strategy_name in [
        ACTIVE_RESEARCH_LEAD,
        PREVIOUS_RESEARCH_LEAD,
        MONTHLY_ROTATION_REFERENCE,
        EQUAL_WEIGHT_BENCHMARK,
        SPY_BENCHMARK,
    ]:
        full = find_row(inputs["lab_summary"], strategy_name)
        if full:
            rows.append(regime_row_from_summary(created_at, "full_period", full))
        for split_row in [row for row in inputs["robustness"] if row.get("strategy_name") == strategy_name]:
            rows.append(regime_row_from_summary(created_at, str(split_row.get("split_name", "split")), split_row))

    worst = first_row(inputs["drawdown"], "check_name", "worst_drawdown_window")
    if worst:
        rows.append(
            review_row(
                created_at,
                "regime_context",
                "worst_drawdown_window",
                "saved_worst_drawdown_context",
                status="manual_review_pack_needs_review",
                severity="review_required",
                metric_name=worst.get("metric_name", "worst_drawdown_pct"),
                metric_value=worst.get("metric_value", ""),
                evidence=worst.get("evidence", ""),
                interpretation="Worst drawdown context is saved-output review only.",
                required_next_step="Review drawdown window before preview-candidate discussion.",
            )
        )
    return rows or [
        review_row(
            created_at,
            "regime_context",
            "insufficient_data",
            "missing_regime_context",
            status="manual_review_pack_blocked_missing_inputs",
            severity="insufficient_data",
            evidence="No saved regime/context rows were available.",
            interpretation="Manual review pack did not download or infer market data.",
            required_next_step=MISSING_INPUT_STEP,
        )
    ]


def regime_row_from_summary(created_at: str, context_name: str, row: dict[str, Any]) -> dict[str, Any]:
    return review_row(
        created_at,
        "regime_context",
        context_name,
        "saved_performance_context",
        strategy_name=str(row.get("strategy_name", "")),
        status="manual_review_pack_pass" if row.get("strategy_name") == ACTIVE_RESEARCH_LEAD else "manual_review_pack_needs_review",
        severity="pass" if row.get("strategy_name") == ACTIVE_RESEARCH_LEAD else "warning",
        metric_name="cagr_sharpe_calmar_maxdd_cash",
        metric_value=(
            f"cagr={row.get('cagr_pct', '')}; sharpe={row.get('sharpe_ratio', '')}; "
            f"calmar={row.get('calmar_ratio', '')}; maxdd={row.get('max_drawdown_pct', '')}; "
            f"cash={row.get('average_cash_weight_pct', '')}"
        ),
        evidence=f"Saved {context_name} row for {row.get('strategy_name', '')}.",
        interpretation="Regime/context row is saved-output review context only.",
    )


def build_missing_input_rows(created_at: str, missing_required: list[str]) -> list[dict[str, Any]]:
    return [
        review_row(
            created_at,
            "manual_review_pack",
            "missing_inputs",
            "missing_saved_input",
            status="manual_review_pack_blocked_missing_inputs",
            severity="insufficient_data",
            evidence="Missing saved inputs: " + ", ".join(missing_required),
            interpretation="Manual review pack uses saved research outputs only and does not refresh data.",
            required_next_step=MISSING_INPUT_STEP,
        ),
        review_row(
            created_at,
            "manual_review_pack",
            "final",
            "preview_candidate_discussion_status",
            status="preview_candidate_discussion_not_approved",
            severity="insufficient_data",
            metric_name="preview_candidate_discussion_allowed",
            metric_value=False,
            evidence="Saved input blocker prevents review.",
            interpretation="Preview-candidate discussion is not approved.",
            required_next_step=MISSING_INPUT_STEP,
        ),
    ]


def build_summary_lines(review_rows: list[dict[str, Any]], regime_rows: list[dict[str, Any]], root: Path) -> list[str]:
    final = first_row(review_rows, "check_name", "preview_candidate_discussion_status")
    benchmark = first_row(review_rows, "check_name", "benchmark_lag_vs_spy")
    severity_counts = Counter(str(row.get("severity", "")) for row in review_rows)
    return [
        "Growth-biased stricter manual review pack complete. Research/report only; execution_approved=False.",
        f"Candidate compared: {ACTIVE_RESEARCH_LEAD}",
        f"Final review status: {final.get('status', 'manual_review_pack_blocked_missing_inputs')}",
        f"Benchmark comparison summary: {benchmark.get('status', 'insufficient_data')}",
        "Blocker/review counts: " + format_counts(severity_counts),
        f"Key next required review step: {final.get('required_next_step', MISSING_INPUT_STEP)}",
        f"Regime/context rows written: {len(regime_rows)}",
        f"Saved manual review pack to {root / OUTPUT_FILES['review_pack']}",
        f"Saved regime context to {root / OUTPUT_FILES['regime_context']}",
        "Warning: manual review pack does not approve orders, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def show_growth_biased_stricter_manual_review_pack_file(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    review = read_csv(root / OUTPUT_FILES["review_pack"])
    regime = read_csv(root / OUTPUT_FILES["regime_context"])
    if not review:
        return 1, ["Run `python bot.py --growth-biased-stricter-manual-review-pack` first."]

    final = first_row(review, "check_name", "preview_candidate_discussion_status")
    benchmark = first_row(review, "check_name", "benchmark_lag_vs_spy")
    severity_counts = Counter(str(row.get("severity", "")) for row in review)
    approval_values = {str(row.get("execution_approved", "")).lower() for row in review + regime}
    return 0, [
        "Growth-biased stricter manual review pack. Display only; execution_approved=False.",
        f"Final review status: {final.get('status', 'manual_review_pack_blocked_missing_inputs')}",
        f"Candidate compared: {ACTIVE_RESEARCH_LEAD}",
        f"Benchmark comparison summary: {benchmark.get('status', 'insufficient_data')}",
        "Blocker/review counts: " + format_counts(severity_counts),
        f"Key next required review step: {final.get('required_next_step', MISSING_INPUT_STEP)}",
        f"Regime/context rows available: {len(regime)}",
        f"execution_approved values: {', '.join(sorted(approval_values)) or 'false'}",
        "Warning: saved manual review pack does not approve orders, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def review_row(
    created_at: str,
    row_type: str,
    context_name: str,
    check_name: str,
    *,
    strategy_name: str = ACTIVE_RESEARCH_LEAD,
    comparison_strategy: str = "",
    status: str,
    severity: str,
    metric_name: Any = "",
    metric_value: Any = "",
    reference_value: Any = "",
    metric_delta: Any = "",
    evidence: str,
    interpretation: str,
    required_next_step: str = "Manual research review only; do not connect to execution.",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "growth_biased_stricter_manual_review_pack",
        "row_type": row_type,
        "context_name": context_name,
        "check_name": check_name,
        "strategy_name": strategy_name,
        "comparison_strategy": comparison_strategy,
        "status": status,
        "severity": severity,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "reference_value": reference_value,
        "metric_delta": metric_delta,
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


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def first_row(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    return next((row for row in rows if row.get(key) == value), {})


def find_row(rows: list[dict[str, Any]], strategy_name: str) -> dict[str, Any]:
    for row in rows:
        if row.get("strategy_name") == strategy_name and row.get("period", "full_period") == "full_period":
            return row
    for row in rows:
        if row.get("strategy_name") == strategy_name:
            return row
    return {}


def format_counts(counts: Counter[str]) -> str:
    if not counts:
        return "none"
    order = ["insufficient_data", "review_required", "warning", "pass"]
    return ", ".join(f"{name}={counts[name]}" for name in order if counts.get(name))


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}
