"""Saved-output manual-review checkpoint for volatility seed-change evidence."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_seed_change_ready_for_formal_proposal_manual_review"
BLOCKED_STATUS = "vol_targeted_growth_seed_change_manual_review_blocked_incomplete_evidence"
NEXT_STEP = "manual_review_before_any_formal_seed_change_proposal_or_implementation"

OUTPUT_FILES = {
    "checkpoint": Path("data/vol_targeted_growth_seed_change_manual_review_checkpoint.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_manual_review_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_manual_review_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_manual_review_blockers.csv"),
}

INPUT_FILES = {
    "evidence_pack_summary": Path("data/vol_targeted_growth_seed_change_evidence_summary.csv"),
    "evidence_pack": Path("data/vol_targeted_growth_seed_change_evidence_pack.csv"),
    "proposal_document_summary": Path("data/vol_targeted_growth_seed_change_proposal_document_summary.csv"),
    "broker_exposure_summary": Path("data/vol_targeted_growth_seed_change_broker_exposure_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "manual_review_checkpoint_only": True,
    "proposal_only": True,
    "preview_only": True,
    "seed_changed": False,
    "seed_change_proposal_created": False,
    "formal_seed_change_proposal_created": False,
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

CHECKPOINT_COLUMNS = [
    "created_at",
    "checkpoint_item",
    "checkpoint_status",
    "saved_evidence_status",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthSeedChangeManualReviewCheckpointResult:
    output_paths: dict[str, Path]
    checkpoint_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_manual_review_checkpoint(root_dir: Path | str = ".") -> VolTargetedGrowthSeedChangeManualReviewCheckpointResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    missing_count = parse_int(summary_value(inputs["evidence_pack_summary"], "missing_required_evidence_count"))
    readiness = summary_value(inputs["evidence_pack_summary"], "seed_change_readiness")
    evidence_complete = missing_count == 0 and readiness == "all_evidence_present_manual_review_required"
    final_status = FINAL_STATUS if evidence_complete else BLOCKED_STATUS
    checkpoint_rows = build_checkpoint_rows(created_at, inputs, final_status)
    summary_rows = build_summary_rows(inputs, final_status, missing_count)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["checkpoint"], CHECKPOINT_COLUMNS, checkpoint_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeManualReviewCheckpointResult(
        output_paths=output_paths,
        checkpoint_rows=checkpoint_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_manual_review_checkpoint(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-manual-review-checkpoint` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change manual-review checkpoint saved display. No seed change approved.",
        f"final_manual_review_status: {summary_value(rows, 'final_manual_review_status')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"candidate_under_review: {summary_value(rows, 'candidate_under_review')}",
        f"evidence_missing_count: {summary_value(rows, 'evidence_missing_count')}",
        f"manual_review_readiness: {summary_value(rows, 'manual_review_readiness')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_checkpoint_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    evidence_status = summary_value(inputs["evidence_pack_summary"], "seed_change_readiness") or "missing_evidence_pack"
    rows = [
        ("evidence_pack_completeness", final_status, evidence_status, "Saved evidence is complete enough for human review only, not approval." if final_status == FINAL_STATUS else "Saved evidence is incomplete."),
        ("incumbent_seed_boundary", "qqq100_seed_retained", INCUMBENT_SEED, "QQQ100 remains the active seed until a separate explicit approval and implementation step."),
        ("proposal_boundary", "formal_proposal_not_created", proposal_context(inputs), "This checkpoint does not create a formal seed-change proposal."),
        ("execution_boundary", "execution_blocked", "all_execution_flags_false", "No order instructions, execution, repeat orders, or scheduling are approved."),
    ]
    return [
        {
            "created_at": created_at,
            "checkpoint_item": item,
            "checkpoint_status": status,
            "saved_evidence_status": evidence,
            "interpretation": interpretation,
            "required_next_step": NEXT_STEP,
            **SAFETY_FLAGS,
        }
        for item, status, evidence, interpretation in rows
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], final_status: str, missing_count: int | None) -> list[dict[str, Any]]:
    all_present = final_status == FINAL_STATUS
    rows = [
        ("final_manual_review_status", final_status, "Manual-review checkpoint status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current paper-live seed remains unchanged."),
        ("candidate_under_review", SELECTED_CANDIDATE, "Volatility-targeted candidate under manual review."),
        ("evidence_pack_status", summary_value(inputs["evidence_pack_summary"], "final_evidence_pack_status") or "missing_evidence_pack", "Saved evidence-pack status."),
        ("evidence_missing_count", str(missing_count) if missing_count is not None else "unavailable", "Missing/manual-review evidence item count from saved evidence pack."),
        ("manual_review_readiness", "ready_for_human_formal_proposal_review_not_approved" if all_present else "blocked_incomplete_evidence", "Readiness for a human review conversation only."),
        ("seed_change_decision", "qqq100_seed_retained_no_displacement_approved", "No seed change is requested or approved."),
        ("formal_proposal_status", "formal_seed_change_proposal_not_created", "This is not a formal proposal document."),
        ("largest_blocker", "human_manual_review_required_before_formal_seed_change_proposal" if all_present else "seed_change_evidence_incomplete", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if all_present else "complete_seed_change_evidence_pack_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This checkpoint reads saved outputs only and does not call Alpaca."))
    rows.append(("seed_changed_now", "false", "This checkpoint does not change the seed."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("manual_review_required", "blocked", "critical", "A human must review the completed evidence before any formal seed-change proposal.", NEXT_STEP),
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent seed.", NEXT_STEP),
        ("formal_proposal_not_created", "blocked", "critical", "This checkpoint does not create or approve a formal seed-change proposal.", "separate_formal_proposal_required_after_manual_review"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("evidence_pack_incomplete", "blocked", "critical", "Saved evidence pack is not complete.", "complete_seed_change_evidence_pack_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth seed-change manual-review checkpoint complete. No seed change approved.",
        f"final_manual_review_status={summary_value(summary_rows, 'final_manual_review_status')}",
        f"evidence_missing_count={summary_value(summary_rows, 'evidence_missing_count')}",
        f"manual_review_readiness={summary_value(summary_rows, 'manual_review_readiness')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_checkpoint={output_paths['checkpoint']}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def proposal_context(inputs: dict[str, list[dict[str, str]]]) -> str:
    return summary_value(inputs["proposal_document_summary"], "final_proposal_document_status") or "missing_proposal_document_checkpoint"


def parse_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
