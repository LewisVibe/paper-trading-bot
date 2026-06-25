"""Saved-output nearby-variants review for volatility-targeted growth.

This module reads existing saved volatility-targeted sprint outputs only. It
does not refresh market data, call Alpaca, read positions, create order
instructions, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PREFERRED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
PREFERRED_FAMILY = "multi_sleeve_vol_targeted_growth"
FINAL_STATUS = "vol_targeted_growth_nearby_variants_manual_review_required"
PREVIEW_STATUS = "preview_design_still_blocked_pending_variant_review"

OUTPUT_FILES = {
    "review": Path("data/vol_targeted_growth_nearby_variants_review.csv"),
    "summary": Path("data/vol_targeted_growth_nearby_variants_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_nearby_variants_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_nearby_variants_blockers.csv"),
}

INPUT_FILES = {
    "sprint": Path("data/vol_targeted_growth_research_sprint.csv"),
    "robustness": Path("data/vol_targeted_growth_robustness_checkpoint_summary.csv"),
    "sensitivity": Path("data/vol_targeted_growth_parameter_sensitivity.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "action_preview_created": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "preview_candidate_approved": False,
    "preview_implementation_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "high_growth_promotion_approved": False,
    "crypto_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REVIEW_COLUMNS = [
    "created_at",
    "candidate_name",
    "target_volatility",
    "volatility_window",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "out_of_sample_cagr",
    "out_of_sample_sharpe",
    "out_of_sample_calmar",
    "rank_by_cagr",
    "rank_by_sharpe",
    "rank_by_calmar",
    "rank_by_drawdown",
    "variant_status",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedNearbyVariantsResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_nearby_variants_review(root_dir: Path | str = ".") -> VolTargetedNearbyVariantsResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    variants = [row for row in inputs["sprint"] if row.get("candidate_family") == PREFERRED_FAMILY]
    review_rows = build_review_rows(created_at, variants)
    summary_rows = build_summary_rows(review_rows, inputs)
    evidence_rows = build_evidence_rows(inputs, review_rows)
    blocker_rows = build_blocker_rows(summary_rows)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedNearbyVariantsResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_nearby_variants_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    review_path = root / OUTPUT_FILES["review"]
    if not summary_path.exists() or not review_path.exists():
        return 1, [
            "Volatility-targeted growth nearby-variants review is missing.",
            "Run `python bot.py --vol-targeted-growth-nearby-variants-review` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted growth nearby-variants saved display. Research/report only; no preview or execution approval.",
        f"final_nearby_review_status: {summary_value(summary_rows, 'final_nearby_review_status')}",
        f"preferred_candidate: {summary_value(summary_rows, 'preferred_candidate')}",
        f"best_calmar_variant: {summary_value(summary_rows, 'best_calmar_variant')}",
        f"best_sharpe_variant: {summary_value(summary_rows, 'best_sharpe_variant')}",
        f"best_cagr_variant: {summary_value(summary_rows, 'best_cagr_variant')}",
        f"variant_interpretation: {summary_value(summary_rows, 'variant_interpretation')}",
        f"preview_status: {summary_value(summary_rows, 'preview_status')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this review reads saved research outputs only; it does not create preview signals, order instructions, or scheduling approval.",
    ]


def build_review_rows(created_at: str, variants: list[dict[str, str]]) -> list[dict[str, Any]]:
    ranked_cagr = rank_map(variants, "cagr", reverse=True)
    ranked_sharpe = rank_map(variants, "sharpe", reverse=True)
    ranked_calmar = rank_map(variants, "calmar", reverse=True)
    ranked_drawdown = rank_map(variants, "max_drawdown", reverse=True)
    rows: list[dict[str, Any]] = []
    for variant in sorted(variants, key=lambda row: (safe_float(row.get("target_volatility")), safe_float(row.get("volatility_window")))):
        status = variant_status(variant, ranked_calmar.get(variant.get("candidate_name", ""), 99), ranked_sharpe.get(variant.get("candidate_name", ""), 99))
        rows.append(
            with_flags(
                {
                    "created_at": created_at,
                    "candidate_name": variant.get("candidate_name", ""),
                    "target_volatility": variant.get("target_volatility", ""),
                    "volatility_window": variant.get("volatility_window", ""),
                    "cagr": metric_value(variant, "cagr"),
                    "sharpe": metric_value(variant, "sharpe"),
                    "max_drawdown": metric_value(variant, "max_drawdown"),
                    "calmar": metric_value(variant, "calmar"),
                    "out_of_sample_cagr": metric_value(variant, "out_of_sample_cagr"),
                    "out_of_sample_sharpe": metric_value(variant, "out_of_sample_sharpe"),
                    "out_of_sample_calmar": metric_value(variant, "out_of_sample_calmar"),
                    "rank_by_cagr": str(ranked_cagr.get(variant.get("candidate_name", ""), "")),
                    "rank_by_sharpe": str(ranked_sharpe.get(variant.get("candidate_name", ""), "")),
                    "rank_by_calmar": str(ranked_calmar.get(variant.get("candidate_name", ""), "")),
                    "rank_by_drawdown": str(ranked_drawdown.get(variant.get("candidate_name", ""), "")),
                    "variant_status": status,
                    "interpretation": variant_interpretation(variant, status),
                    "required_next_step": "manual_review_nearby_variants_before_preview_design",
                }
            )
        )
    return rows


def build_summary_rows(review_rows: list[dict[str, Any]], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    preferred = find_row(review_rows, "candidate_name", PREFERRED_CANDIDATE)
    best_calmar = best_row(review_rows, "calmar")
    best_sharpe = best_row(review_rows, "sharpe")
    best_cagr = best_row(review_rows, "cagr")
    interpretation = "preferred_15_20_retains_best_calmar_and_sharpe_but_requires_manual_review" if best_calmar.get("candidate_name") == PREFERRED_CANDIDATE and best_sharpe.get("candidate_name") == PREFERRED_CANDIDATE else "nearby_variant_may_challenge_preferred_candidate_manual_review_required"
    return [
        summary_row("final_nearby_review_status", FINAL_STATUS, "Final status remains manual-review-only."),
        summary_row("preferred_candidate", candidate_summary(preferred), "Preferred variant from the previous checkpoint."),
        summary_row("best_calmar_variant", candidate_summary(best_calmar), "Best Calmar variant in the preferred family."),
        summary_row("best_sharpe_variant", candidate_summary(best_sharpe), "Best Sharpe variant in the preferred family."),
        summary_row("best_cagr_variant", candidate_summary(best_cagr), "Highest CAGR variant in the preferred family."),
        summary_row("variant_count", str(len(review_rows)), "Nearby preferred-family variants reviewed."),
        summary_row("robustness_input_status", summary_value(inputs["robustness"], "final_robustness_status") or "missing_robustness_checkpoint", "Saved robustness checkpoint input status."),
        summary_row("variant_interpretation", interpretation, "Manual interpretation of nearby-variant grid."),
        summary_row("preview_status", PREVIEW_STATUS, "Preview design remains blocked."),
        summary_row("recommended_next_step", "manual_review_15_20_vs_20_20_and_25_20_before_preview_design_decision", "Next step remains manual review, not implementation."),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        evidence_row("saved_sprint_rows_available", str(len(inputs["sprint"])), "Rows read from data/vol_targeted_growth_research_sprint.csv."),
        evidence_row("preferred_family_variant_count", str(len(review_rows)), "Multi-sleeve vol-targeted variants reviewed."),
        evidence_row("saved_robustness_rows_available", str(len(inputs["robustness"])), "Rows read from data/vol_targeted_growth_robustness_checkpoint_summary.csv."),
        evidence_row("saved_sensitivity_rows_available", str(len(inputs["sensitivity"])), "Rows read from data/vol_targeted_growth_parameter_sensitivity.csv."),
        evidence_row("top_calmar_context", candidate_summary(best_row(review_rows, "calmar")), "Best Calmar context."),
        evidence_row("top_cagr_context", candidate_summary(best_row(review_rows, "cagr")), "Highest CAGR context."),
    ]


def build_blocker_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        blocker_row("preview_design_not_approved", "blocked", "critical", "Nearby-variants review does not implement preview mode or preview signals.", summary_value(summary_rows, "recommended_next_step")),
        blocker_row("execution_blocked", "blocked", "critical", "No order instructions, paper execution, live execution, or scheduling are approved.", "keep_all_order_paths_separate_and_unmodified"),
        blocker_row("variant_choice_manual_review", "manual_review_required", "medium", "15/20 is best on risk-adjusted metrics, while 20/20 is the nearest higher-vol step and 25/20 is the highest-CAGR challenger.", "manual_review_15_20_vs_20_20_and_25_20_before_preview_design_decision"),
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth nearby-variants review complete. Saved-output research only; no preview, execution, orders, or scheduling approved.",
        f"final_nearby_review_status={summary_value(summary_rows, 'final_nearby_review_status')}",
        f"preferred_candidate={summary_value(summary_rows, 'preferred_candidate')}",
        f"best_calmar_variant={summary_value(summary_rows, 'best_calmar_variant')}",
        f"best_sharpe_variant={summary_value(summary_rows, 'best_sharpe_variant')}",
        f"best_cagr_variant={summary_value(summary_rows, 'best_cagr_variant')}",
        f"variant_interpretation={summary_value(summary_rows, 'variant_interpretation')}",
        f"preview_status={summary_value(summary_rows, 'preview_status')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['review']}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def variant_status(row: dict[str, str], calmar_rank: int, sharpe_rank: int) -> str:
    if row.get("candidate_name") == PREFERRED_CANDIDATE and calmar_rank == 1 and sharpe_rank == 1:
        return "preferred_variant_retained_manual_review_required"
    if safe_float(row.get("target_volatility")) > 0.15:
        return "higher_return_higher_drawdown_variant_manual_review_required"
    if safe_float(row.get("target_volatility")) < 0.15:
        return "lower_drawdown_lower_return_variant_manual_review_required"
    return "nearby_window_variant_manual_review_required"


def variant_interpretation(row: dict[str, str], status: str) -> str:
    if status == "preferred_variant_retained_manual_review_required":
        return "15% target / 20-day window remains best on Calmar and Sharpe in saved outputs."
    if status == "higher_return_higher_drawdown_variant_manual_review_required":
        return "Higher target volatility improves CAGR but raises drawdown; do not promote without manual risk review."
    if status == "lower_drawdown_lower_return_variant_manual_review_required":
        return "Lower target volatility cuts drawdown but gives up too much return for the current growth objective."
    return "Same target with a different window is useful context but does not beat the preferred risk-adjusted profile."


def rank_map(rows: list[dict[str, str]], metric: str, reverse: bool) -> dict[str, int]:
    ranked = sorted(rows, key=lambda row: safe_float(row.get(metric)), reverse=reverse)
    return {row.get("candidate_name", ""): index + 1 for index, row in enumerate(ranked)}


def best_row(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    if not rows:
        return {}
    return max(rows, key=lambda row: safe_float(row.get(metric)))


def summary_row(summary_name: str, summary_value_text: str, details: str) -> dict[str, Any]:
    return with_flags({"summary_name": summary_name, "summary_value": summary_value_text, "details": details})


def evidence_row(evidence_name: str, evidence_value: str, details: str) -> dict[str, Any]:
    return with_flags({"evidence_name": evidence_name, "evidence_value": evidence_value, "details": details})


def blocker_row(blocker_name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return with_flags({"blocker_name": blocker_name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step})


def with_flags(row: dict[str, Any]) -> dict[str, Any]:
    return {**row, **SAFETY_FLAGS}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def find_row(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def candidate_summary(row: dict[str, Any]) -> str:
    if not row:
        return "missing_saved_candidate"
    return (
        f"{row.get('candidate_name', 'unknown_candidate')}: "
        f"CAGR={row.get('cagr', 'missing')}; Sharpe={row.get('sharpe', 'missing')}; "
        f"MaxDD={row.get('max_drawdown', 'missing')}; Calmar={row.get('calmar', 'missing')}"
    )


def metric_value(row: dict[str, str], key: str) -> str:
    value = row.get(key, "")
    if value == "":
        return "missing_saved_metric"
    return str(round(safe_float(value), 4))


def safe_float(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""
