"""Saved-output manual review pack for volatility-targeted growth candidates.

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


PRIMARY_HIGH_RETURN_CANDIDATE = "high_growth_balanced_target_vol_25_win_20_cap_1x"
PRIMARY_MULTI_SLEEVE_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
QQQ100_BASELINE_FAMILY = "qqq100_vol_targeted_growth"

FINAL_STATUS_READY = "vol_targeted_growth_manual_review_required"
FINAL_STATUS_BLOCKED = "vol_targeted_growth_manual_review_blocked_missing_saved_evidence"
MULTI_SLEEVE_STATUS = "multi_sleeve_vol_targeted_growth_more_credible_research_path"
HIGH_RETURN_STATUS = "high_return_vol_targeted_growth_high_risk_manual_review_required"

OUTPUT_FILES = {
    "pack": Path("data/vol_targeted_growth_manual_review_pack.csv"),
    "summary": Path("data/vol_targeted_growth_manual_review_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_manual_review_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_manual_review_blockers.csv"),
}

INPUT_FILES = {
    "sprint": Path("data/vol_targeted_growth_research_sprint.csv"),
    "summary": Path("data/vol_targeted_growth_candidate_summary.csv"),
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

PACK_COLUMNS = [
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
class VolTargetedGrowthManualReviewResult:
    output_paths: dict[str, Path]
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_manual_review_pack(root_dir: Path | str = ".") -> VolTargetedGrowthManualReviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    sprint_rows = inputs["sprint"]
    sprint_summary = inputs["summary"]
    high_return = find_row(sprint_rows, "candidate_name", PRIMARY_HIGH_RETURN_CANDIDATE)
    multi_sleeve = find_row(sprint_rows, "candidate_name", PRIMARY_MULTI_SLEEVE_CANDIDATE)
    qqq100 = best_family_row(sprint_rows, QQQ100_BASELINE_FAMILY)

    pack_rows = build_pack_rows(created_at, high_return, multi_sleeve, qqq100, sprint_summary)
    summary_rows = build_summary_rows(pack_rows, high_return, multi_sleeve, qqq100, inputs)
    evidence_rows = build_evidence_rows(inputs, high_return, multi_sleeve, qqq100)
    blocker_rows = build_blocker_rows(summary_rows, high_return, multi_sleeve)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], PACK_COLUMNS, pack_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthManualReviewResult(
        output_paths=output_paths,
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_manual_review_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    pack_path = root / OUTPUT_FILES["pack"]
    if not summary_path.exists() or not pack_path.exists():
        return 1, [
            "Volatility-targeted growth manual review pack is missing.",
            "Run `python bot.py --vol-targeted-growth-manual-review-pack` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted growth manual review saved display. Research/report only; no preview or execution approval.",
        f"final_manual_review_status: {summary_value(summary_rows, 'final_manual_review_status')}",
        f"high_return_candidate: {summary_value(summary_rows, 'high_return_candidate')}",
        f"multi_sleeve_candidate: {summary_value(summary_rows, 'multi_sleeve_candidate')}",
        f"preferred_research_path: {summary_value(summary_rows, 'preferred_research_path')}",
        f"strongest_evidence: {summary_value(summary_rows, 'strongest_evidence')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this review compares saved research candidates only; it does not create preview signals, order instructions, or scheduling approval.",
    ]


def build_pack_rows(
    created_at: str,
    high_return: dict[str, str],
    multi_sleeve: dict[str, str],
    qqq100: dict[str, str],
    sprint_summary: list[dict[str, str]],
) -> list[dict[str, Any]]:
    return [
        pack_row(
            created_at,
            "saved_sprint_status",
            summary_value(sprint_summary, "final_research_status") or "missing_saved_sprint_status",
            "medium",
            "vol_targeted_growth_sprint",
            "saved_output_stack",
            summary_value(sprint_summary, "strong_candidate_count"),
            summary_value(sprint_summary, "candidate_families_tested"),
            "The volatility-targeted sprint found multiple saved-output research candidates, but none are preview or execution approvals.",
            "manual_review_vol_targeted_growth_candidates_before_any_preview_design",
        ),
        pack_row(
            created_at,
            "high_return_candidate_review",
            HIGH_RETURN_STATUS if high_return else "missing_high_return_candidate_saved_evidence",
            "high",
            PRIMARY_HIGH_RETURN_CANDIDATE,
            PRIMARY_MULTI_SLEEVE_CANDIDATE,
            metric_line(high_return),
            metric_line(multi_sleeve),
            "The high-return candidate has the strongest CAGR but carries materially larger drawdown and high-growth branch risk.",
            "review_drawdown_concentration_and_outlier_dependence_before_label_change",
        ),
        pack_row(
            created_at,
            "multi_sleeve_candidate_review",
            MULTI_SLEEVE_STATUS if multi_sleeve else "missing_multi_sleeve_candidate_saved_evidence",
            "medium",
            PRIMARY_MULTI_SLEEVE_CANDIDATE,
            PRIMARY_HIGH_RETURN_CANDIDATE,
            metric_line(multi_sleeve),
            metric_line(high_return),
            "The multi-sleeve candidate gives up raw CAGR but has cleaner Sharpe/Calmar balance and lower drawdown, making it the more credible next research path.",
            "run_saved_output_robustness_checkpoint_before_preview_design",
        ),
        pack_row(
            created_at,
            "qqq100_baseline_context",
            "qqq100_clean_paper_live_base_unchanged",
            "medium",
            PRIMARY_MULTI_SLEEVE_CANDIDATE,
            "qqq100_best_vol_targeted_baseline",
            metric_line(multi_sleeve),
            metric_line(qqq100),
            "QQQ100 remains the clean current paper-live base; volatility-targeted growth is a research branch only.",
            "keep_qqq100_as_current_monitor_base_until_separate_manual_review",
        ),
        pack_row(
            created_at,
            "preview_boundary",
            "preview_design_not_approved",
            "critical",
            "vol_targeted_growth_candidates",
            "paper_live_policy",
            "preview_candidate_approved=false",
            "execution_approved=false",
            "This review does not add preview signals, action previews, order instructions, paper execution, or scheduling.",
            "separate_prompt_required_for_any_preview_design_after_robustness_review",
        ),
    ]


def build_summary_rows(
    pack_rows: list[dict[str, Any]],
    high_return: dict[str, str],
    multi_sleeve: dict[str, str],
    qqq100: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    has_required = bool(high_return and multi_sleeve)
    final_status = FINAL_STATUS_READY if has_required else FINAL_STATUS_BLOCKED
    preferred = PRIMARY_MULTI_SLEEVE_CANDIDATE if multi_sleeve else "missing_saved_candidate"
    strongest = strongest_evidence(high_return, multi_sleeve)
    blocker = largest_blocker(high_return, multi_sleeve, qqq100)
    rows = [
        summary_row("final_manual_review_status", final_status, "Final status remains manual-review-only."),
        summary_row("high_return_candidate", candidate_summary(high_return), "High-return volatility-targeted candidate."),
        summary_row("multi_sleeve_candidate", candidate_summary(multi_sleeve), "More credible volatility-targeted multi-sleeve candidate."),
        summary_row("preferred_research_path", preferred, "Candidate to scrutinize first before any preview design."),
        summary_row("qqq100_baseline_context", candidate_summary(qqq100), "QQQ100 remains the clean current monitor base."),
        summary_row("strongest_evidence", strongest, "Best saved-output evidence from the review."),
        summary_row("largest_blocker", blocker, "Largest blocker before preview discussion."),
        summary_row("input_sprint_rows", str(len(inputs["sprint"])), "Saved sprint candidate rows read."),
        summary_row("input_rejected_rows", str(len(inputs["rejected"])), "Saved rejected/fragile rows read."),
        summary_row("recommended_next_step", "run_saved_output_vol_targeted_growth_robustness_checkpoint_before_preview_design", "Next step remains report-only robustness review."),
    ]
    return rows


def build_evidence_rows(
    inputs: dict[str, list[dict[str, str]]],
    high_return: dict[str, str],
    multi_sleeve: dict[str, str],
    qqq100: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        evidence_row("saved_sprint_rows_available", str(len(inputs["sprint"])), "Rows read from data/vol_targeted_growth_research_sprint.csv."),
        evidence_row("saved_summary_rows_available", str(len(inputs["summary"])), "Rows read from data/vol_targeted_growth_candidate_summary.csv."),
        evidence_row("saved_rejected_rows_available", str(len(inputs["rejected"])), "Rows read from data/vol_targeted_growth_rejected_candidates.csv."),
        evidence_row("saved_audit_rows_available", str(len(inputs["audit"])), "Rows read from data/vol_targeted_growth_robustness_audit.csv."),
        evidence_row("saved_sensitivity_rows_available", str(len(inputs["sensitivity"])), "Rows read from data/vol_targeted_growth_parameter_sensitivity.csv."),
        evidence_row("high_return_candidate_metrics", metric_line(high_return), "High-CAGR candidate remains high-risk/manual-review-only."),
        evidence_row("multi_sleeve_candidate_metrics", metric_line(multi_sleeve), "Multi-sleeve candidate is the more credible research path."),
        evidence_row("qqq100_baseline_metrics", metric_line(qqq100), "QQQ100 baseline context for not changing the current paper-live base."),
    ]


def build_blocker_rows(
    summary_rows: list[dict[str, Any]],
    high_return: dict[str, str],
    multi_sleeve: dict[str, str],
) -> list[dict[str, Any]]:
    rows = [
        blocker_row(
            "preview_design_not_approved",
            "blocked",
            "critical",
            "The manual review pack does not add preview signals or action previews.",
            "run_saved_output_robustness_checkpoint_before_preview_design",
        ),
        blocker_row(
            "execution_blocked",
            "blocked",
            "critical",
            "No paper execution, live execution, order instructions, or scheduling are approved.",
            "keep_all_order_paths_separate_and_unmodified",
        ),
        blocker_row(
            "high_return_candidate_tail_risk",
            "manual_review_required",
            "high",
            "The highest-CAGR candidate still has materially larger drawdown and high-growth branch risk.",
            "review_drawdown_concentration_and_outlier_dependence",
        ),
        blocker_row(
            "multi_sleeve_robustness_not_yet_checkpointed",
            "manual_review_required",
            "medium",
            "The multi-sleeve candidate looks cleaner, but needs a separate saved-output robustness checkpoint.",
            summary_value(summary_rows, "recommended_next_step"),
        ),
    ]
    if not high_return:
        rows.append(blocker_row("missing_high_return_candidate", "blocked", "high", "Saved high-return candidate row is missing.", "regenerate_vol_targeted_growth_research_sprint"))
    if not multi_sleeve:
        rows.append(blocker_row("missing_multi_sleeve_candidate", "blocked", "high", "Saved multi-sleeve candidate row is missing.", "regenerate_vol_targeted_growth_research_sprint"))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth manual review pack complete. Saved-output research only; no preview, execution, orders, or scheduling approved.",
        f"final_manual_review_status={summary_value(summary_rows, 'final_manual_review_status')}",
        f"high_return_candidate={summary_value(summary_rows, 'high_return_candidate')}",
        f"multi_sleeve_candidate={summary_value(summary_rows, 'multi_sleeve_candidate')}",
        f"preferred_research_path={summary_value(summary_rows, 'preferred_research_path')}",
        f"strongest_evidence={summary_value(summary_rows, 'strongest_evidence')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['pack']}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def pack_row(
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


def candidate_summary(row: dict[str, str]) -> str:
    if not row:
        return "missing_saved_candidate"
    return f"{row.get('candidate_name', 'unknown_candidate')}: {metric_line(row)}"


def strongest_evidence(high_return: dict[str, str], multi_sleeve: dict[str, str]) -> str:
    if high_return and multi_sleeve:
        return "multi_sleeve_candidate_has_cleaner_risk_adjusted_profile_while_high_return_candidate_preserves_upside_context"
    return "missing_saved_candidate_evidence"


def largest_blocker(high_return: dict[str, str], multi_sleeve: dict[str, str], qqq100: dict[str, str]) -> str:
    if not high_return or not multi_sleeve:
        return "missing_saved_vol_targeted_candidate_evidence"
    if not qqq100:
        return "missing_saved_qqq100_baseline_context"
    return "robustness_checkpoint_required_before_preview_design"


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
