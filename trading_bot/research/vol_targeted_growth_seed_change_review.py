"""Saved-output seed-change review for volatility-targeted growth.

This report reviews whether the volatility-targeted proposal preview is ready
to be considered against QQQ100 as the paper-live seed. It does not change the
seed, read broker positions, create order instructions, schedule anything, or
approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_seed_change_review_created_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_seed_change_review_blocked_missing_proposal_preview"
NEXT_STEP = "manual_review_seed_change_review_before_any_seed_change_proposal"

OUTPUT_FILES = {
    "review": Path("data/vol_targeted_growth_seed_change_review.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_review_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_review_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_review_blockers.csv"),
}

INPUT_FILES = {
    "proposal_preview_summary": Path("data/vol_targeted_growth_proposal_preview_summary.csv"),
    "proposal_preview": Path("data/vol_targeted_growth_proposal_preview.csv"),
    "proposal_preview_blockers": Path("data/vol_targeted_growth_proposal_preview_blockers.csv"),
    "proposal_schema_summary": Path("data/vol_targeted_growth_proposal_preview_schema_summary.csv"),
    "candidate_discussion_summary": Path("data/vol_targeted_growth_candidate_discussion_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
    "paper_live_monitoring_summary": Path("data/paper_live_monitoring_status_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "seed_change_review_only": True,
    "proposal_only": True,
    "preview_only": True,
    "seed_changed": False,
    "qqq100_displacement_requested": False,
    "qqq100_displacement_approved": False,
    "vol_targeted_seed_approved": False,
    "action_preview_added": False,
    "order_instructions_created": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_read_now": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "paper_live_candidate_approved": False,
    "vol_targeted_paper_live_candidate_approved": False,
    "preview_implementation_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REVIEW_COLUMNS = [
    "created_at",
    "review_item",
    "review_status",
    "risk_level",
    "qqq100_context",
    "vol_targeted_context",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthSeedChangeReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_review(root_dir: Path | str = ".") -> VolTargetedGrowthSeedChangeReviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    review_rows = build_review_rows(created_at, inputs, final_status)
    summary_rows = build_summary_rows(inputs, review_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeReviewResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-review` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change review saved display. Review only; QQQ100 remains the seed.",
        f"final_seed_change_review_status: {summary_value(rows, 'final_seed_change_review_status')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"candidate_under_review: {summary_value(rows, 'candidate_under_review')}",
        f"seed_change_consideration_status: {summary_value(rows, 'seed_change_consideration_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_changed=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    preview_status = summary_value(inputs["proposal_preview_summary"], "final_proposal_preview_status")
    if preview_status == "vol_targeted_growth_proposal_preview_created_saved_output_only":
        return FINAL_STATUS
    return BLOCKED_STATUS


def build_review_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    qqq_status = summary_value(inputs["qqq100_followup_policy_summary"], "final_followup_policy_status") or "missing_qqq100_followup_policy"
    preview_status = summary_value(inputs["proposal_preview_summary"], "final_proposal_preview_status") or "missing_proposal_preview"
    sleeve_summary = summary_value(inputs["proposal_preview_summary"], "sleeve_weight_summary") or "missing_sleeve_weights"
    consideration = "manual_consideration_allowed_not_approved" if final_status == FINAL_STATUS else "blocked_missing_proposal_preview"
    return [
        review_row(created_at, "incumbent_seed_boundary", "qqq100_retained", "critical", qqq_status, preview_status, "QQQ100 remains the current paper-live seed and is not displaced by this review.", "keep_qqq100_as_seed"),
        review_row(created_at, "candidate_consideration", consideration, "high", qqq_status, sleeve_summary, "The volatility proposal can be reviewed as a possible future seed-change discussion, but no seed change is requested or approved.", NEXT_STEP if final_status == FINAL_STATUS else "run_proposal_preview_first"),
        review_row(created_at, "complexity_review", "manual_review_required", "high", "QQQ100 is a single clean stock/ETF seed.", "Volatility proposal has QQQ100, high-growth, crypto, and defensive sleeves.", "The candidate is broader and more complex than QQQ100, so complexity and component-risk review are required before any displacement discussion.", "review_component_complexity_before_seed_change"),
        review_row(created_at, "component_boundary", "component_sleeves_not_approved", "critical", "QQQ100 seed remains approved monitoring context only.", "High-growth and crypto sleeves remain research-only components.", "Research-only components block any immediate seed replacement.", "keep_component_sleeves_research_only"),
        review_row(created_at, "position_boundary", "current_exposure_not_verified", "critical", "QQQ100 saved state may be monitored separately.", "Proposal preview does not read current exposure.", "A seed change cannot be considered operationally without a separate confirmed read-only exposure comparison.", "separate_confirmed_readonly_comparison_required"),
        review_row(created_at, "execution_boundary", "execution_blocked", "critical", "No repeat/follow-up order approved.", "Candidate proposal only.", "No paper/live execution, seed change, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], review_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("final_seed_change_review_status", final_status, "Whether saved proposal preview supports a seed-change review checkpoint."),
        ("incumbent_seed", INCUMBENT_SEED, "Current paper-live seed remains unchanged."),
        ("candidate_under_review", SELECTED_CANDIDATE, "Volatility-targeted candidate under manual review."),
        ("source_proposal_preview_status", summary_value(inputs["proposal_preview_summary"], "final_proposal_preview_status") or "missing_proposal_preview", "Saved proposal preview status."),
        ("seed_change_consideration_status", "consideration_allowed_for_manual_review_not_approved" if final_status == FINAL_STATUS else "blocked_missing_proposal_preview", "Whether consideration can continue."),
        ("seed_change_decision", "keep_qqq100_seed_no_displacement_approved", "No seed change is requested or approved."),
        ("review_row_count", str(len(review_rows)), "Saved review row count."),
        ("largest_blocker", "seed_change_consideration_possible_but_displacement_not_approved" if final_status == FINAL_STATUS else "missing_proposal_preview", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if final_status == FINAL_STATUS else "run_proposal_preview_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This review reads saved outputs only and does not call Alpaca."))
    rows.append(("seed_changed_now", "false", "This review does not change the seed."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent seed.", NEXT_STEP),
        ("seed_change_not_requested", "blocked", "critical", "This checkpoint permits review only and does not request or approve seed replacement.", "separate_seed_change_proposal_required"),
        ("component_sleeves_not_approved", "blocked", "critical", "High-growth and crypto sleeves remain research-only.", "component_promotion_review_required"),
        ("current_exposure_not_verified", "blocked", "critical", "No current broker exposure is read or compared.", "separate_confirmed_readonly_comparison_required"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, repeat order, follow-up order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("proposal_preview_missing", "blocked", "critical", "Saved proposal preview is missing or not ready.", "run_proposal_preview_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth seed-change review complete. Review only; QQQ100 remains the seed.",
        f"final_seed_change_review_status={summary_value(summary_rows, 'final_seed_change_review_status')}",
        f"incumbent_seed={summary_value(summary_rows, 'incumbent_seed')}",
        f"candidate_under_review={summary_value(summary_rows, 'candidate_under_review')}",
        f"seed_change_consideration_status={summary_value(summary_rows, 'seed_change_consideration_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_review={output_paths['review']}",
        "seed_changed=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def review_row(created_at: str, item: str, status: str, risk: str, qqq100: str, vol_context: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "review_item": item, "review_status": status, "risk_level": risk, "qqq100_context": qqq100, "vol_targeted_context": vol_context, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


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


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""
