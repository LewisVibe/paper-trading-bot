"""Saved-output gate review for volatility-targeted growth paper-live discussion.

This report applies the stricter gate design to saved evidence and decides
whether the volatility-targeted 15/20 candidate remains blocked or can enter a
limited manual candidate discussion. It does not call Alpaca, read positions,
create order instructions, enforce the gate, schedule anything, or approve
paper-live execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_limited_manual_candidate_discussion_ready_gate_review_required"
BLOCKED_STATUS = "vol_targeted_growth_gate_review_blocked_missing_gate_design"
NEXT_STEP = "manual_review_limited_candidate_discussion_before_any_paper_live_candidate_approval"

OUTPUT_FILES = {
    "review": Path("data/vol_targeted_growth_gate_review.csv"),
    "summary": Path("data/vol_targeted_growth_gate_review_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_gate_review_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_gate_review_blockers.csv"),
}

INPUT_FILES = {
    "gate_design": Path("data/vol_targeted_growth_stricter_paper_live_gate_design.csv"),
    "gate_design_summary": Path("data/vol_targeted_growth_stricter_paper_live_gate_design_summary.csv"),
    "post_comparison_decision_summary": Path("data/vol_targeted_growth_post_comparison_decision_summary.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "gate_review_only": True,
    "preview_only": True,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_read_now": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "limited_manual_candidate_discussion_ready": True,
    "paper_live_candidate_approved": False,
    "vol_targeted_paper_live_candidate_approved": False,
    "paper_live_discussion_approved": False,
    "gate_enforced": False,
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
    "evidence",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthGateReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_gate_review(root_dir: Path | str = ".") -> VolTargetedGrowthGateReviewResult:
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
    return VolTargetedGrowthGateReviewResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_gate_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-gate-review` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth gate review saved display. Limited manual discussion only; no execution approval.",
        f"final_gate_review_status: {summary_value(rows, 'final_gate_review_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"limited_manual_candidate_discussion_status: {summary_value(rows, 'limited_manual_candidate_discussion_status')}",
        f"qqq100_boundary_status: {summary_value(rows, 'qqq100_boundary_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "limited_manual_candidate_discussion_ready=true; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    gate_status = summary_value(inputs["gate_design_summary"], "final_gate_design_status")
    if gate_status == "vol_targeted_growth_stricter_paper_live_gate_design_ready_manual_review_required":
        return FINAL_STATUS
    return BLOCKED_STATUS


def build_review_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    gate_status = summary_value(inputs["gate_design_summary"], "final_gate_design_status")
    comparison_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status")
    qqq100_status = summary_value(inputs["qqq100_followup_policy_summary"], "final_followup_policy_status")
    return [
        review_row(created_at, "gate_design_available", "pass" if final_status == FINAL_STATUS else "blocked", "critical", gate_status or "missing", "Stricter gate design must exist before candidate discussion.", "continue_limited_manual_review" if final_status == FINAL_STATUS else "run_gate_design_first"),
        review_row(created_at, "qqq100_incumbent_boundary", "pass_manual_review_required", "critical", qqq100_status or "missing_qqq100_followup_policy", "QQQ100 remains the incumbent paper-live seed; volatility candidate cannot displace it here.", "keep_qqq100_as_incumbent_seed"),
        review_row(created_at, "broker_comparison_context", "pass_manual_review_required" if comparison_status else "blocked_missing_comparison", "high", comparison_status or "missing_broker_comparison_status", "Saved broker comparison is context only and not an order instruction.", "do_not_convert_comparison_to_orders"),
        review_row(created_at, "component_sleeve_boundary", "pass_manual_review_required", "critical", "high-growth and crypto sleeves remain research-only.", "The candidate can be discussed only as a capped research portfolio, not as component promotion.", "keep_high_growth_and_crypto_research_only"),
        review_row(created_at, "gate_enforcement_boundary", "blocked_not_enforced", "critical", "gate_enforced=false", "The gate is reviewed but not enforced; paper-live candidate approval remains false.", "design_enforcement_only_in_later_separate_step"),
        review_row(created_at, "execution_boundary", "execution_blocked", "critical", "no orders; no order instructions; no scheduling.", "Limited manual discussion is not execution approval.", "keep_all_execution_flags_false"),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], review_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("final_gate_review_status", final_status, "Whether saved evidence passes enough blockers for limited manual candidate discussion."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("limited_manual_candidate_discussion_status", "limited_manual_candidate_discussion_ready_not_approved" if final_status == FINAL_STATUS else "blocked_missing_gate_design", "Discussion readiness only; no approval."),
        ("qqq100_boundary_status", "qqq100_remains_incumbent_paper_live_seed", "The volatility candidate must be reviewed alongside QQQ100, not in place of it."),
        ("gate_design_status", summary_value(inputs["gate_design_summary"], "final_gate_design_status") or "missing_gate_design_status", "Saved stricter gate design status."),
        ("broker_comparison_status", summary_value(inputs["broker_comparison_summary"], "final_comparison_status") or "missing_broker_comparison_status", "Saved broker comparison status."),
        ("gate_review_row_count", str(len(review_rows)), "Saved gate review row count."),
        ("largest_blocker", "candidate_discussion_ready_but_gate_not_enforced_and_not_approved" if final_status == FINAL_STATUS else "missing_gate_design", "Primary remaining blocker."),
        ("recommended_next_step", NEXT_STEP if final_status == FINAL_STATUS else "run_stricter_gate_design_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This gate review reads saved outputs only and does not call Alpaca."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("paper_live_candidate_not_approved", "blocked", "critical", "The candidate is ready only for limited manual discussion, not paper-live approval.", NEXT_STEP),
        ("gate_not_enforced", "blocked", "critical", "The stricter gate is not enforced.", "do_not_treat_gate_as_runtime_protection"),
        ("component_sleeves_not_approved", "blocked", "critical", "High-growth and crypto sleeves remain research-only.", "do_not_promote_component_sleeves"),
        ("order_instructions_not_allowed", "blocked", "critical", "No executable order fields or instructions are allowed.", "keep_review_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("gate_design_missing", "blocked", "critical", "Saved stricter gate design is missing or not ready.", "run_stricter_gate_design_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth gate review complete. Limited manual discussion only; no execution or scheduling approved.",
        f"final_gate_review_status={summary_value(summary_rows, 'final_gate_review_status')}",
        f"limited_manual_candidate_discussion_status={summary_value(summary_rows, 'limited_manual_candidate_discussion_status')}",
        f"qqq100_boundary_status={summary_value(summary_rows, 'qqq100_boundary_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_review={output_paths['review']}",
        "limited_manual_candidate_discussion_ready=true; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def review_row(created_at: str, item: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "review_item": item, "review_status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


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
