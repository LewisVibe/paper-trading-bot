"""Saved-output robustness checkpoint for volatility-targeted growth.

This module reads existing saved volatility-targeted growth reports only. It
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
HIGH_RETURN_CANDIDATE = "high_growth_balanced_target_vol_25_win_20_cap_1x"
QQQ100_FAMILY = "qqq100_vol_targeted_growth"
BALANCED_FAMILY = "balanced_multi_sleeve_vol_targeted_growth"
PREFERRED_FAMILY = "multi_sleeve_vol_targeted_growth"

FINAL_STATUS_REVIEW = "vol_targeted_growth_robustness_manual_review_required"
FINAL_STATUS_BLOCKED = "vol_targeted_growth_robustness_blocked_missing_saved_evidence"
PREVIEW_READY_STATUS = "vol_targeted_growth_preview_design_not_ready_robustness_review_required"

OUTPUT_FILES = {
    "checkpoint": Path("data/vol_targeted_growth_robustness_checkpoint.csv"),
    "summary": Path("data/vol_targeted_growth_robustness_checkpoint_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_robustness_checkpoint_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_robustness_checkpoint_blockers.csv"),
}

INPUT_FILES = {
    "sprint": Path("data/vol_targeted_growth_research_sprint.csv"),
    "summary": Path("data/vol_targeted_growth_candidate_summary.csv"),
    "manual_review": Path("data/vol_targeted_growth_manual_review_summary.csv"),
    "rejected": Path("data/vol_targeted_growth_rejected_candidates.csv"),
    "audit": Path("data/vol_targeted_growth_robustness_audit.csv"),
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

CHECKPOINT_COLUMNS = [
    "created_at",
    "check_name",
    "status",
    "risk_level",
    "candidate_name",
    "comparison_subject",
    "candidate_metrics",
    "comparison_metrics",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthRobustnessResult:
    output_paths: dict[str, Path]
    checkpoint_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_robustness_checkpoint(root_dir: Path | str = ".") -> VolTargetedGrowthRobustnessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    sprint_rows = inputs["sprint"]
    preferred = find_row(sprint_rows, "candidate_name", PREFERRED_CANDIDATE)
    high_return = find_row(sprint_rows, "candidate_name", HIGH_RETURN_CANDIDATE)
    qqq100 = best_family_row(sprint_rows, QQQ100_FAMILY)
    balanced = best_family_row(sprint_rows, BALANCED_FAMILY)
    preferred_family_rows = [row for row in sprint_rows if row.get("candidate_family") == PREFERRED_FAMILY]

    checkpoint_rows = build_checkpoint_rows(created_at, preferred, high_return, qqq100, balanced, preferred_family_rows, inputs)
    summary_rows = build_summary_rows(preferred, high_return, qqq100, balanced, preferred_family_rows, inputs)
    evidence_rows = build_evidence_rows(inputs, preferred, high_return, qqq100, balanced, preferred_family_rows)
    blocker_rows = build_blocker_rows(summary_rows, preferred, preferred_family_rows)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["checkpoint"], CHECKPOINT_COLUMNS, checkpoint_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthRobustnessResult(
        output_paths=output_paths,
        checkpoint_rows=checkpoint_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_robustness_checkpoint(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    checkpoint_path = root / OUTPUT_FILES["checkpoint"]
    if not summary_path.exists() or not checkpoint_path.exists():
        return 1, [
            "Volatility-targeted growth robustness checkpoint is missing.",
            "Run `python bot.py --vol-targeted-growth-robustness-checkpoint` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted growth robustness checkpoint saved display. Research/report only; no preview or execution approval.",
        f"final_robustness_status: {summary_value(summary_rows, 'final_robustness_status')}",
        f"preferred_candidate: {summary_value(summary_rows, 'preferred_candidate')}",
        f"parameter_sensitivity_status: {summary_value(summary_rows, 'parameter_sensitivity_status')}",
        f"split_stability_status: {summary_value(summary_rows, 'split_stability_status')}",
        f"drawdown_tradeoff_status: {summary_value(summary_rows, 'drawdown_tradeoff_status')}",
        f"preview_readiness_status: {summary_value(summary_rows, 'preview_readiness_status')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this checkpoint does not create preview signals, order instructions, or scheduling approval.",
    ]


def build_checkpoint_rows(
    created_at: str,
    preferred: dict[str, str],
    high_return: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    preferred_family_rows: list[dict[str, str]],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    return [
        checkpoint_row(
            created_at,
            "preferred_candidate_identity",
            "preferred_vol_targeted_candidate_confirmed" if preferred else "missing_preferred_candidate_saved_evidence",
            "medium",
            PREFERRED_CANDIDATE,
            "manual_review_pack",
            metric_line(preferred),
            summary_value(inputs["manual_review"], "preferred_research_path") or "missing_manual_review_summary",
            "The preferred candidate is the multi-sleeve volatility-targeted branch selected for robustness review.",
            "keep_candidate_research_only_until_robustness_review_is_accepted",
        ),
        checkpoint_row(
            created_at,
            "parameter_sensitivity_review",
            parameter_sensitivity_status(preferred_family_rows),
            "medium",
            PREFERRED_CANDIDATE,
            "nearby_target_vol_and_window_variants",
            variant_summary(preferred_family_rows),
            sensitivity_row_summary(inputs["sensitivity"], PREFERRED_FAMILY),
            "Nearby variants exist, but the exact 15% target / 20-day window still needs manual review before any preview design.",
            "review_nearby_10_15_20_target_vol_and_20_60_120_window_variants",
        ),
        checkpoint_row(
            created_at,
            "split_stability_review",
            split_stability_status(preferred),
            "medium",
            PREFERRED_CANDIDATE,
            "in_sample_out_of_sample",
            split_metric_line(preferred),
            "manual_review_required",
            "Saved split metrics are supportive only if out-of-sample CAGR, Sharpe, and Calmar remain positive.",
            "manual_review_split_stability_before_preview_design",
        ),
        checkpoint_row(
            created_at,
            "drawdown_tradeoff_review",
            drawdown_tradeoff_status(preferred, high_return),
            "medium",
            PREFERRED_CANDIDATE,
            HIGH_RETURN_CANDIDATE,
            metric_line(preferred),
            metric_line(high_return),
            "The preferred candidate sacrifices CAGR but has materially lower drawdown than the high-return candidate.",
            "confirm_drawdown_tradeoff_is_worth_lower_return_before_preview_design",
        ),
        checkpoint_row(
            created_at,
            "qqq100_and_balanced_context",
            "baseline_context_manual_review_required",
            "medium",
            PREFERRED_CANDIDATE,
            "qqq100_and_balanced_baselines",
            metric_line(preferred),
            f"qqq100={metric_line(qqq100)} | balanced={metric_line(balanced)}",
            "QQQ100 remains the current paper-live base; balanced multi-sleeve remains a calmer comparator.",
            "keep_current_paper_live_base_unchanged_until_separate_manual_review",
        ),
        checkpoint_row(
            created_at,
            "preview_boundary",
            PREVIEW_READY_STATUS,
            "critical",
            PREFERRED_CANDIDATE,
            "paper_live_policy",
            "preview_candidate_approved=false",
            "execution_approved=false",
            "Robustness checkpoint does not approve preview design, preview signals, order instructions, paper execution, or scheduling.",
            "manual_review_checkpoint_before_any_preview_design_prompt",
        ),
    ]


def build_summary_rows(
    preferred: dict[str, str],
    high_return: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    preferred_family_rows: list[dict[str, str]],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    has_required = bool(preferred and high_return and qqq100)
    final_status = FINAL_STATUS_REVIEW if has_required else FINAL_STATUS_BLOCKED
    return [
        summary_row("final_robustness_status", final_status, "Final status remains manual-review-only."),
        summary_row("preferred_candidate", candidate_summary(preferred), "Preferred candidate under robustness review."),
        summary_row("high_return_comparator", candidate_summary(high_return), "Higher-return/higher-risk comparator."),
        summary_row("qqq100_context", candidate_summary(qqq100), "Current clean paper-live base remains unchanged."),
        summary_row("balanced_context", candidate_summary(balanced), "Balanced comparator context where available."),
        summary_row("parameter_sensitivity_status", parameter_sensitivity_status(preferred_family_rows), "Target-vol/window robustness status."),
        summary_row("split_stability_status", split_stability_status(preferred), "Saved split stability status."),
        summary_row("drawdown_tradeoff_status", drawdown_tradeoff_status(preferred, high_return), "Drawdown versus high-return candidate."),
        summary_row("preview_readiness_status", PREVIEW_READY_STATUS, "Preview design remains blocked pending manual review."),
        summary_row("preferred_family_candidate_count", str(len(preferred_family_rows)), "Nearby preferred-family saved variants reviewed."),
        summary_row("manual_review_status_input", summary_value(inputs["manual_review"], "final_manual_review_status") or "missing_manual_review_summary", "Manual review input status."),
        summary_row("largest_blocker", largest_blocker(preferred, preferred_family_rows), "Largest blocker before preview design."),
        summary_row("recommended_next_step", "manual_review_vol_targeted_robustness_then_decide_preview_design_or_more_research", "Next step remains manual review, not implementation."),
    ]


def build_evidence_rows(
    inputs: dict[str, list[dict[str, str]]],
    preferred: dict[str, str],
    high_return: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    preferred_family_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    return [
        evidence_row("saved_sprint_rows_available", str(len(inputs["sprint"])), "Rows read from data/vol_targeted_growth_research_sprint.csv."),
        evidence_row("saved_manual_review_rows_available", str(len(inputs["manual_review"])), "Rows read from data/vol_targeted_growth_manual_review_summary.csv."),
        evidence_row("preferred_candidate_metrics", metric_line(preferred), "Preferred multi-sleeve candidate metrics."),
        evidence_row("high_return_candidate_metrics", metric_line(high_return), "High-return candidate metrics."),
        evidence_row("qqq100_context_metrics", metric_line(qqq100), "QQQ100 current-base context."),
        evidence_row("balanced_context_metrics", metric_line(balanced), "Balanced comparator context."),
        evidence_row("preferred_family_variants", variant_summary(preferred_family_rows), "Nearby target-vol/window variants in the preferred family."),
        evidence_row("parameter_sensitivity_saved_summary", sensitivity_row_summary(inputs["sensitivity"], PREFERRED_FAMILY), "Saved family-level sensitivity summary."),
    ]


def build_blocker_rows(summary_rows: list[dict[str, Any]], preferred: dict[str, str], preferred_family_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("preview_design_not_approved", "blocked", "critical", "No preview design or preview signal is implemented by this checkpoint.", summary_value(summary_rows, "recommended_next_step")),
        blocker_row("execution_blocked", "blocked", "critical", "No order instructions, paper execution, live execution, or scheduling are approved.", "keep_all_order_paths_separate_and_unmodified"),
        blocker_row("parameter_sensitivity_manual_review", "manual_review_required", "medium", "The preferred 15%/20-day setting must be reviewed against nearby target-vol/window variants.", "review_nearby_parameter_grid_before_preview_design"),
        blocker_row("portfolio_component_contribution_unknown", "manual_review_required", "medium", "This saved checkpoint does not decompose sleeve-level contribution for the preferred candidate.", "add_component_contribution_review_if_preview_design_remains_interesting"),
    ]
    if not preferred:
        rows.append(blocker_row("missing_preferred_candidate", "blocked", "high", "Preferred saved candidate row is missing.", "regenerate_vol_targeted_growth_research_sprint"))
    if len(preferred_family_rows) < 3:
        rows.append(blocker_row("limited_parameter_neighborhood", "blocked", "medium", "Too few nearby preferred-family variants are available.", "regenerate_or_review_parameter_sensitivity_outputs"))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth robustness checkpoint complete. Saved-output research only; no preview, execution, orders, or scheduling approved.",
        f"final_robustness_status={summary_value(summary_rows, 'final_robustness_status')}",
        f"preferred_candidate={summary_value(summary_rows, 'preferred_candidate')}",
        f"parameter_sensitivity_status={summary_value(summary_rows, 'parameter_sensitivity_status')}",
        f"split_stability_status={summary_value(summary_rows, 'split_stability_status')}",
        f"drawdown_tradeoff_status={summary_value(summary_rows, 'drawdown_tradeoff_status')}",
        f"preview_readiness_status={summary_value(summary_rows, 'preview_readiness_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['checkpoint']}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def checkpoint_row(
    created_at: str,
    check_name: str,
    status: str,
    risk_level: str,
    candidate_name: str,
    comparison_subject: str,
    candidate_metrics: str,
    comparison_metrics: str,
    interpretation: str,
    required_next_step: str,
) -> dict[str, Any]:
    return with_flags(
        {
            "created_at": created_at,
            "check_name": check_name,
            "status": status,
            "risk_level": risk_level,
            "candidate_name": candidate_name,
            "comparison_subject": comparison_subject,
            "candidate_metrics": candidate_metrics,
            "comparison_metrics": comparison_metrics,
            "interpretation": interpretation,
            "required_next_step": required_next_step,
        }
    )


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


def find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def best_family_row(rows: list[dict[str, str]], family: str) -> dict[str, str]:
    family_rows = [row for row in rows if row.get("candidate_family") == family]
    if not family_rows:
        return {}
    return max(family_rows, key=lambda row: safe_float(row.get("calmar")))


def parameter_sensitivity_status(rows: list[dict[str, str]]) -> str:
    strong_count = sum(1 for row in rows if row.get("final_candidate_status") == "strong_vol_targeted_growth_candidate_research_only")
    if strong_count >= 2:
        return "parameter_neighborhood_supportive_manual_review_required"
    if rows:
        return "parameter_neighborhood_fragile_manual_review_required"
    return "parameter_neighborhood_missing_saved_evidence"


def split_stability_status(row: dict[str, str]) -> str:
    if not row:
        return "split_stability_missing_saved_evidence"
    if safe_float(row.get("out_of_sample_cagr")) > 0 and safe_float(row.get("out_of_sample_sharpe")) > 0 and safe_float(row.get("out_of_sample_calmar")) > 0:
        return "split_stability_supportive_manual_review_required"
    return "split_stability_fragile_manual_review_required"


def drawdown_tradeoff_status(preferred: dict[str, str], high_return: dict[str, str]) -> str:
    if not preferred or not high_return:
        return "drawdown_tradeoff_missing_saved_evidence"
    preferred_dd = abs(safe_float(preferred.get("max_drawdown")))
    high_return_dd = abs(safe_float(high_return.get("max_drawdown")))
    if preferred_dd < high_return_dd:
        return "drawdown_tradeoff_supportive_lower_drawdown_manual_review_required"
    return "drawdown_tradeoff_not_supportive_manual_review_required"


def largest_blocker(preferred: dict[str, str], preferred_family_rows: list[dict[str, str]]) -> str:
    if not preferred:
        return "missing_preferred_candidate_saved_evidence"
    if len(preferred_family_rows) < 3:
        return "limited_parameter_neighborhood_saved_evidence"
    return "manual_review_required_before_preview_design"


def variant_summary(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "missing_saved_variants"
    strong = sum(1 for row in rows if row.get("final_candidate_status") == "strong_vol_targeted_growth_candidate_research_only")
    best = max(rows, key=lambda row: safe_float(row.get("calmar")))
    return f"variants={len(rows)}; strong={strong}; best_by_calmar={best.get('candidate_name', 'unknown')}; best_calmar={metric_value(best, 'calmar')}"


def sensitivity_row_summary(rows: list[dict[str, str]], family: str) -> str:
    row = find_row(rows, "candidate_family", family)
    if not row:
        return "missing_saved_sensitivity_summary"
    return (
        f"candidate_count={row.get('candidate_count', 'missing')}; "
        f"best_candidate={row.get('best_candidate', 'missing')}; "
        f"strong_candidate_count={row.get('strong_candidate_count', 'missing')}; "
        f"fragile_candidate_count={row.get('fragile_candidate_count', 'missing')}"
    )


def metric_line(row: dict[str, str]) -> str:
    if not row:
        return "missing_saved_metrics"
    return (
        f"CAGR={metric_value(row, 'cagr')}; "
        f"Sharpe={metric_value(row, 'sharpe')}; "
        f"MaxDD={metric_value(row, 'max_drawdown')}; "
        f"Calmar={metric_value(row, 'calmar')}; "
        f"Vol={metric_value(row, 'realized_volatility')}"
    )


def split_metric_line(row: dict[str, str]) -> str:
    if not row:
        return "missing_saved_split_metrics"
    return (
        f"in_sample_cagr={metric_value(row, 'in_sample_cagr')}; "
        f"out_of_sample_cagr={metric_value(row, 'out_of_sample_cagr')}; "
        f"out_of_sample_sharpe={metric_value(row, 'out_of_sample_sharpe')}; "
        f"out_of_sample_calmar={metric_value(row, 'out_of_sample_calmar')}"
    )


def candidate_summary(row: dict[str, str]) -> str:
    if not row:
        return "missing_saved_candidate"
    return f"{row.get('candidate_name', 'unknown_candidate')}: {metric_line(row)}"


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
