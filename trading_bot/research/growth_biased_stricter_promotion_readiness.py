"""Promotion-readiness blockers for the stricter growth-biased research lead.

This module reads saved research CSVs only. It does not refresh market data,
load config, call brokers, read positions, write SQLite, send alerts, schedule
anything, approve preview promotion, or approve execution.
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

INPUT_FILES = {
    "validation": Path("data/growth_biased_stricter_validation.csv"),
    "split": Path("data/growth_biased_stricter_split_validation.csv"),
    "cost": Path("data/growth_biased_stricter_cost_review.csv"),
    "drawdown": Path("data/growth_biased_stricter_drawdown_review.csv"),
    "benchmark": Path("data/growth_biased_stricter_benchmark_comparison.csv"),
    "promotion": Path("data/growth_biased_stricter_promotion_checkpoint.csv"),
    "candidate_comparison": Path("data/strategy_improvement_candidate_comparison.csv"),
    "diagnostics": Path("data/strategy_improvement_diagnostics.csv"),
    "growth_diagnostics": Path("data/growth_biased_rotation_diagnostics.csv"),
}

OUTPUT_FILES = {
    "readiness": Path("data/growth_biased_stricter_promotion_readiness.csv"),
    "blockers": Path("data/growth_biased_stricter_promotion_blockers.csv"),
}

READINESS_COLUMNS = [
    "created_at",
    "report_name",
    "blocker_category",
    "check_name",
    "strategy_name",
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

REQUIRED_GENERATION_STEPS = (
    "Run `python bot.py --strategy-improvement-lab`, "
    "`python bot.py --strategy-improvement-robustness`, "
    "`python bot.py --strategy-improvement-diagnostics`, and "
    "`python bot.py --growth-biased-stricter-validation` first."
)


@dataclass
class PromotionReadinessResult:
    readiness_path: Path
    blockers_path: Path
    readiness_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_growth_biased_stricter_promotion_readiness(
    root_dir: Path | str = ".",
) -> PromotionReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(root / path) for name, path in INPUT_FILES.items()}
    missing = [str(path) for name, path in INPUT_FILES.items() if not (root / path).exists()]

    blocker_rows = build_blocker_rows(created_at, root, inputs, missing)
    readiness_rows = build_readiness_rows(created_at, blocker_rows)

    write_rows(root / OUTPUT_FILES["blockers"], blocker_rows)
    write_rows(root / OUTPUT_FILES["readiness"], readiness_rows)

    return PromotionReadinessResult(
        readiness_path=root / OUTPUT_FILES["readiness"],
        blockers_path=root / OUTPUT_FILES["blockers"],
        readiness_rows=readiness_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(readiness_rows, blocker_rows, root),
    )


def build_blocker_rows(
    created_at: str,
    root: Path,
    inputs: dict[str, list[dict[str, Any]]],
    missing: list[str],
) -> list[dict[str, Any]]:
    if missing:
        return [
            readiness_row(
                created_at,
                "saved_outputs",
                "required_saved_outputs_present",
                status="saved_outputs_missing",
                severity="blocker",
                evidence="Missing saved inputs: " + ", ".join(missing),
                interpretation="Promotion-readiness review reads saved outputs only and cannot infer missing evidence.",
                required_next_step=REQUIRED_GENERATION_STEPS,
            ),
            readiness_row(
                created_at,
                "preview_readiness",
                "final_preview_readiness",
                status="insufficient_data",
                severity="insufficient_data",
                evidence="Required saved outputs are missing.",
                interpretation="Future preview-candidate discussion remains blocked until saved research outputs exist.",
                required_next_step=REQUIRED_GENERATION_STEPS,
            ),
        ]

    rows = [
        build_benchmark_blocker(created_at, inputs),
        build_split_blocker(created_at, inputs),
        build_cost_blocker(created_at, inputs),
        build_drawdown_blocker(created_at, inputs),
        build_saved_output_blocker(created_at, root),
    ]
    rows.append(build_preview_readiness_blocker(created_at, inputs, rows))
    return rows


def build_benchmark_blocker(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    benchmark = inputs["benchmark"]
    candidate = find_row(inputs["candidate_comparison"], ACTIVE_RESEARCH_LEAD)
    spy_row = first_row(benchmark, "comparison_strategy", SPY_BENCHMARK)
    beats_previous = benchmark_pass(benchmark, PREVIOUS_RESEARCH_LEAD)
    beats_rotation = benchmark_pass(benchmark, MONTHLY_ROTATION_REFERENCE)
    beats_equal_weight = benchmark_pass(benchmark, EQUAL_WEIGHT_BENCHMARK)
    trails_spy = parse_bool(candidate.get("trails_spy_buy_and_hold")) if candidate else bool(spy_row)

    if not benchmark or not candidate:
        status = "insufficient_data"
        severity = "insufficient_data"
        evidence = "Missing benchmark comparison or candidate comparison rows."
    elif trails_spy and beats_previous and beats_rotation and beats_equal_weight:
        status = "benchmark_lagging_but_acceptable_for_active_candidate"
        severity = "review_required"
        evidence = (
            "Still trails SPY, but beats the previous growth-biased baseline, "
            "monthly ETF rotation reference, and equal-weight ETF benchmark."
        )
    elif trails_spy:
        status = "benchmark_gap_requires_review"
        severity = "review_required"
        evidence = "Still trails SPY and one or more active/reference comparisons need review."
    else:
        status = "benchmark_comparison_pass"
        severity = "pass"
        evidence = "Saved benchmark comparison does not show an SPY lag blocker."

    return readiness_row(
        created_at,
        "benchmark",
        "benchmark_blocker",
        status=status,
        severity=severity,
        evidence=evidence,
        interpretation=(
            "Trailing SPY is not automatically fatal, but preview discussion needs a clear "
            "risk-role justification for using an active strategy instead of buy-and-hold."
        ),
        required_next_step="Document benchmark/risk-role rationale before any future preview-candidate discussion.",
    )


def build_split_blocker(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    split = inputs["split"]
    validation = inputs["validation"]
    candidate = find_row(inputs["candidate_comparison"], ACTIVE_RESEARCH_LEAD)
    split_sensitive = parse_bool(candidate.get("split_sensitive")) if candidate else True
    split_summary = first_row(validation, "check_name", "split_validation")
    split_summary_status = str(split_summary.get("status", ""))

    if not split or not validation or not candidate:
        status = "insufficient_data"
        severity = "insufficient_data"
        evidence = "Missing split validation summary, split rows, or candidate comparison rows."
    elif split_summary_status == "validation_not_ready_for_preview":
        status = "split_validation_fail"
        severity = "blocker"
        evidence = "Saved split-validation summary is not ready for preview discussion."
    elif split_sensitive:
        status = "split_validation_mixed_requires_review"
        severity = "review_required"
        evidence = "Split validation passes as research lead, but saved comparison still flags split sensitivity."
    else:
        status = "split_validation_pass"
        severity = "pass"
        evidence = "Split validation supports the stricter gate as research lead."

    return readiness_row(
        created_at,
        "split",
        "split_robustness_blocker",
        status=status,
        severity=severity,
        evidence=evidence,
        interpretation="Split robustness remains a preview-readiness checkpoint, not execution approval.",
        required_next_step="Review split sensitivity and confirm it is acceptable before preview-candidate discussion.",
    )


def build_cost_blocker(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    cost = inputs["cost"]
    promotion = inputs["promotion"]
    cost_conclusion = first_row(cost, "check_name", "cost_stress_conclusion")
    promotion_eligibility = first_row(promotion, "check_name", "preview_discussion_eligibility")
    promotion_status = str(promotion_eligibility.get("status", ""))
    cost_status = str(cost_conclusion.get("status", ""))

    if not cost or not promotion:
        status = "insufficient_data"
        severity = "insufficient_data"
        evidence = "Missing cost review or promotion checkpoint rows."
    elif cost_status == "stricter_cost_advantage_lost":
        status = "cost_advantage_lost"
        severity = "blocker"
        evidence = "Saved cost review says the stricter gate lost its cost-adjusted advantage."
    elif cost_status == "stricter_cost_resilient" and promotion_status == "validation_cost_sensitive":
        status = "cost_sensitive_requires_review"
        severity = "review_required"
        evidence = "Cost stress is resilient, but the promotion checkpoint still flags cost sensitivity."
    elif cost_status in {"stricter_cost_resilient", "stricter_cost_sensitive"}:
        status = "cost_resilient"
        severity = "pass" if cost_status == "stricter_cost_resilient" else "review_required"
        evidence = f"Saved cost review conclusion={cost_status}."
    else:
        status = "cost_sensitive_requires_review"
        severity = "review_required"
        evidence = f"Saved cost status requires review: {cost_status or 'missing'}."

    return readiness_row(
        created_at,
        "cost",
        "cost_blocker",
        status=status,
        severity=severity,
        evidence=evidence,
        interpretation="Cost resilience is necessary for review, but it does not approve execution or promotion.",
        required_next_step="Resolve cost-sensitive promotion flag before any future preview-candidate discussion.",
    )


def build_drawdown_blocker(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    drawdown = inputs["drawdown"]
    conclusion = first_row(drawdown, "check_name", "drawdown_conclusion")
    status_value = str(conclusion.get("status", ""))

    if not drawdown:
        status = "insufficient_data"
        severity = "insufficient_data"
        evidence = "Missing drawdown review rows."
    elif status_value == "drawdown_worse_than_reference":
        status = "drawdown_unacceptable"
        severity = "blocker"
        evidence = "Saved drawdown review shows material deterioration versus reference."
    elif status_value == "drawdown_acceptable_for_return":
        status = "drawdown_acceptable_for_return"
        severity = "pass"
        evidence = "Drawdown is acceptable for return, but the strategy does not minimise drawdown."
    else:
        status = "drawdown_watch_requires_review"
        severity = "review_required"
        evidence = f"Saved drawdown conclusion requires review: {status_value or 'missing'}."

    return readiness_row(
        created_at,
        "drawdown",
        "drawdown_blocker",
        status=status,
        severity=severity,
        evidence=evidence,
        interpretation="Acceptable drawdown supports research-lead status only.",
        required_next_step="Review drawdown periods and recovery context before preview-candidate discussion.",
    )


def build_saved_output_blocker(created_at: str, root: Path) -> dict[str, Any]:
    existing_paths = [root / path for path in INPUT_FILES.values() if (root / path).exists()]
    missing_paths = [str(path) for path in INPUT_FILES.values() if not (root / path).exists()]
    if missing_paths:
        return readiness_row(
            created_at,
            "saved_outputs",
            "saved_output_freshness",
            status="saved_outputs_missing",
            severity="blocker",
            evidence="Missing saved outputs: " + ", ".join(missing_paths),
            interpretation="All required saved outputs must exist before promotion-readiness review.",
            required_next_step=REQUIRED_GENERATION_STEPS,
        )

    now = datetime.now(timezone.utc).timestamp()
    oldest_age_hours = max(((now - path.stat().st_mtime) / 3600 for path in existing_paths), default=0.0)
    status = "saved_outputs_current" if oldest_age_hours <= 72 else "saved_outputs_stale"
    severity = "pass" if status == "saved_outputs_current" else "warning"
    return readiness_row(
        created_at,
        "saved_outputs",
        "saved_output_freshness",
        status=status,
        severity=severity,
        evidence=f"All required saved outputs exist; oldest mtime age is about {oldest_age_hours:.1f} hours.",
        interpretation="File mtime is a lightweight freshness check; no generated CSV contents are printed.",
        required_next_step="Regenerate saved research outputs if the saved-output checkpoint is stale.",
    )


def build_preview_readiness_blocker(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    blocker_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate = find_row(inputs["candidate_comparison"], ACTIVE_RESEARCH_LEAD)
    strategy_rows = [
        row
        for row in inputs["candidate_comparison"]
        if row.get("strategy_name") and not str(row.get("strategy_name")).endswith("_benchmark")
    ]
    best = max(strategy_rows, key=lambda row: as_float(row.get("calmar_ratio")), default=None)
    is_active_lead = bool(best and best.get("strategy_name") == ACTIVE_RESEARCH_LEAD)
    statuses = {row.get("blocker_category"): row.get("status") for row in blocker_rows}
    severities = {str(row.get("severity", "")) for row in blocker_rows}

    ready = (
        is_active_lead
        and statuses.get("split") == "split_validation_pass"
        and statuses.get("cost") == "cost_resilient"
        and statuses.get("drawdown") == "drawdown_acceptable_for_return"
        and statuses.get("benchmark") in {"benchmark_lagging_but_acceptable_for_active_candidate", "benchmark_comparison_pass"}
        and statuses.get("saved_outputs") == "saved_outputs_current"
        and not {"blocker", "insufficient_data"} & severities
    )
    if not candidate or not is_active_lead:
        status = "not_ready_for_preview"
        severity = "blocker"
        evidence = f"Best saved active strategy is {best.get('strategy_name') if best else 'missing'}."
    elif ready and "review_required" not in severities:
        status = "ready_for_future_preview_discussion"
        severity = "pass"
        evidence = "Saved blockers pass without review-required items."
    elif "blocker" not in severities and "insufficient_data" not in severities:
        status = "nearly_ready_needs_manual_review"
        severity = "review_required"
        evidence = "The stricter gate is still active lead, but manual review items remain."
    else:
        status = "not_ready_for_preview"
        severity = "review_required" if "review_required" in severities else "blocker"
        evidence = "One or more blocker categories prevents preview-candidate discussion."

    return readiness_row(
        created_at,
        "preview_readiness",
        "final_preview_readiness",
        status=status,
        severity=severity,
        evidence=evidence,
        interpretation="This final status is conservative and never approves promotion or execution.",
        required_next_step="Resolve blocker/review rows before any separate manual preview-promotion checkpoint.",
    )


def build_readiness_rows(created_at: str, blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_counts = Counter(str(row.get("severity", "")) for row in blocker_rows)
    final = first_row(blocker_rows, "check_name", "final_preview_readiness")
    return [
        readiness_row(
            created_at,
            "readiness_summary",
            "active_research_lead",
            status="active_research_lead",
            severity="pass",
            evidence=f"Current active research lead is {ACTIVE_RESEARCH_LEAD}.",
            interpretation="Active research lead is still research-only.",
        ),
        readiness_row(
            created_at,
            "readiness_summary",
            "final_readiness_status",
            status=str(final.get("status", "insufficient_data")),
            severity=str(final.get("severity", "insufficient_data")),
            evidence="; ".join(f"{name}={count}" for name, count in sorted(severity_counts.items())),
            interpretation="Promotion-readiness summary; no preview promotion is approved.",
            required_next_step=str(final.get("required_next_step", REQUIRED_GENERATION_STEPS)),
        ),
        readiness_row(
            created_at,
            "readiness_summary",
            "approval_boundary",
            status="execution_and_promotion_not_approved",
            severity="pass",
            evidence="execution_approved=False; paper_execution_approved=False; promotion_approved=False; scheduling_approved=False.",
            interpretation="The report only explains blockers for future manual review.",
        ),
    ]


def build_summary_lines(readiness_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], root: Path) -> list[str]:
    final = first_row(blocker_rows, "check_name", "final_preview_readiness")
    severity_counts = Counter(str(row.get("severity", "")) for row in blocker_rows)
    return [
        "Growth-biased stricter promotion-readiness complete. Research/preview only; execution_approved=False; promotion_approved=False.",
        f"Active research lead: {ACTIVE_RESEARCH_LEAD}",
        f"Final readiness status: {final.get('status', 'insufficient_data')}",
        "Blocker count by severity: " + format_counts(severity_counts),
        f"Benchmark blocker: {category_status(blocker_rows, 'benchmark')}",
        f"Split blocker: {category_status(blocker_rows, 'split')}",
        f"Cost blocker: {category_status(blocker_rows, 'cost')}",
        f"Drawdown blocker: {category_status(blocker_rows, 'drawdown')}",
        f"Saved-output blocker: {category_status(blocker_rows, 'saved_outputs')}",
        f"Saved readiness report to {root / OUTPUT_FILES['readiness']}",
        f"Saved blocker report to {root / OUTPUT_FILES['blockers']}",
        "Warning: this blocker report does not approve orders, paper execution, preview promotion, scheduling, or promoted execution.",
    ]


def show_growth_biased_stricter_promotion_readiness_file(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    readiness = read_csv(root / OUTPUT_FILES["readiness"])
    blockers = read_csv(root / OUTPUT_FILES["blockers"])
    if not readiness or not blockers:
        return 1, ["Run `python bot.py --growth-biased-stricter-promotion-readiness` first."]

    final = first_row(blockers, "check_name", "final_preview_readiness")
    severity_counts = Counter(str(row.get("severity", "")) for row in blockers)
    return 0, [
        "Growth-biased stricter promotion-readiness. Display only; execution_approved=False; promotion_approved=False.",
        f"Active research lead: {ACTIVE_RESEARCH_LEAD}",
        f"Final readiness status: {final.get('status', 'insufficient_data')}",
        "Blocker count by severity: " + format_counts(severity_counts),
        f"Benchmark blocker status: {category_status(blockers, 'benchmark')}",
        f"Split blocker status: {category_status(blockers, 'split')}",
        f"Cost blocker status: {category_status(blockers, 'cost')}",
        f"Drawdown blocker status: {category_status(blockers, 'drawdown')}",
        f"Saved-output freshness status: {category_status(blockers, 'saved_outputs')}",
        f"What must happen next: {final.get('required_next_step', REQUIRED_GENERATION_STEPS)}",
        "execution_approved=False; paper_execution_approved=False; promotion_approved=False; scheduling_approved=False",
        "Warning: saved blocker review does not approve orders, paper execution, preview promotion, scheduling, or promoted execution.",
    ]


def readiness_row(
    created_at: str,
    blocker_category: str,
    check_name: str,
    *,
    status: str,
    severity: str,
    evidence: str,
    interpretation: str,
    required_next_step: str = "Manual research review only; do not connect to execution.",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "growth_biased_stricter_promotion_readiness",
        "blocker_category": blocker_category,
        "check_name": check_name,
        "strategy_name": ACTIVE_RESEARCH_LEAD,
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


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=READINESS_COLUMNS, extrasaction="ignore")
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


def benchmark_pass(rows: list[dict[str, Any]], reference_name: str) -> bool:
    row = first_row(rows, "comparison_strategy", reference_name)
    return str(row.get("status", "")) in {
        "beats_active_reference",
        "benchmark_tradeoff_acceptable",
        "equal_weight_comparison_pass",
    }


def category_status(rows: list[dict[str, Any]], category: str) -> str:
    row = first_row(rows, "blocker_category", category)
    return str(row.get("status", "insufficient_data"))


def format_counts(counts: Counter[str]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{name}={counts[name]}" for name in ["blocker", "review_required", "warning", "pass", "insufficient_data"] if counts.get(name))


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}
