"""Saved-output limited candidate discussion for volatility-targeted growth.

This report compares QQQ100 and the volatility-targeted 15/20 candidate in
plain terms and decides whether the volatility candidate remains research-only
or can become a non-executable paper-live candidate proposal. It does not call
Alpaca, read positions, create order instructions, implement the proposal,
schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
QQQ100_LEAD = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_non_executable_candidate_proposal_ready_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_candidate_discussion_blocked_missing_gate_review"
NEXT_STEP = "manual_review_candidate_proposal_before_any_preview_or_paper_live_implementation"

OUTPUT_FILES = {
    "discussion": Path("data/vol_targeted_growth_candidate_discussion.csv"),
    "summary": Path("data/vol_targeted_growth_candidate_discussion_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_candidate_discussion_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_candidate_discussion_blockers.csv"),
}

INPUT_FILES = {
    "gate_review_summary": Path("data/vol_targeted_growth_gate_review_summary.csv"),
    "gate_review_blockers": Path("data/vol_targeted_growth_gate_review_blockers.csv"),
    "stricter_gate_design_summary": Path("data/vol_targeted_growth_stricter_paper_live_gate_design_summary.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "preview_signal_summary": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "candidate_discussion_only": True,
    "proposal_only": True,
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
    "vol_targeted_candidate_proposal_ready": True,
    "paper_live_candidate_approved": False,
    "vol_targeted_paper_live_candidate_approved": False,
    "paper_live_discussion_approved": False,
    "preview_implementation_approved": False,
    "gate_enforced": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

DISCUSSION_COLUMNS = [
    "created_at",
    "discussion_item",
    "discussion_status",
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
class VolTargetedGrowthCandidateDiscussionResult:
    output_paths: dict[str, Path]
    discussion_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_candidate_discussion(root_dir: Path | str = ".") -> VolTargetedGrowthCandidateDiscussionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    discussion_rows = build_discussion_rows(created_at, inputs, final_status)
    summary_rows = build_summary_rows(inputs, discussion_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["discussion"], DISCUSSION_COLUMNS, discussion_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthCandidateDiscussionResult(
        output_paths=output_paths,
        discussion_rows=discussion_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_candidate_discussion(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-candidate-discussion` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth candidate discussion saved display. Proposal only; no execution approval.",
        f"final_candidate_discussion_status: {summary_value(rows, 'final_candidate_discussion_status')}",
        f"qqq100_status: {summary_value(rows, 'qqq100_status')}",
        f"vol_targeted_candidate_status: {summary_value(rows, 'vol_targeted_candidate_status')}",
        f"proposal_status: {summary_value(rows, 'proposal_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "vol_targeted_candidate_proposal_ready=true; paper_live_candidate_approved=false; preview_implementation_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    gate_review_status = summary_value(inputs["gate_review_summary"], "final_gate_review_status")
    if gate_review_status == "vol_targeted_growth_limited_manual_candidate_discussion_ready_gate_review_required":
        return FINAL_STATUS
    return BLOCKED_STATUS


def build_discussion_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    qqq100_status = summary_value(inputs["qqq100_followup_policy_summary"], "final_followup_policy_status") or "missing_qqq100_followup_policy"
    gate_status = summary_value(inputs["gate_review_summary"], "final_gate_review_status") or "missing_gate_review"
    broker_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status") or "missing_broker_comparison"
    return [
        discussion_row(created_at, "incumbent_lead", "qqq100_retained", "critical", qqq100_status, gate_status, "QQQ100 remains the current paper-live seed; volatility is not replacing it.", "keep_qqq100_as_incumbent_seed"),
        discussion_row(created_at, "candidate_proposal", "proposal_ready_manual_review_required" if final_status == FINAL_STATUS else "blocked_missing_gate_review", "high", qqq100_status, gate_status, "The volatility candidate can be discussed as a non-executable proposal only.", NEXT_STEP if final_status == FINAL_STATUS else "run_gate_review_first"),
        discussion_row(created_at, "risk_tradeoff", "manual_review_required", "high", "QQQ100 is simpler and already aligned; volatility has broader sleeve complexity.", "Volatility adds high-growth and crypto sleeves plus volatility scaling.", "Potential upside/risk diversification must be weighed against added complexity and component risk.", "compare_risk_tradeoff_before_any_candidate_approval"),
        discussion_row(created_at, "broker_context", "context_available_manual_review_required" if broker_status else "blocked_missing_broker_context", "high", qqq100_status, broker_status, "Saved broker context is not an order instruction and does not approve current exposure changes.", "keep_broker_context_non_executable"),
        discussion_row(created_at, "implementation_boundary", "implementation_not_added", "critical", "QQQ100 remains active seed.", "No volatility implementation exists.", "A proposal would still need separate preview/action implementation and approvals.", "separate_implementation_design_required"),
        discussion_row(created_at, "execution_boundary", "execution_blocked", "critical", "no orders; no scheduling.", "candidate proposal only.", "No paper/live execution is approved.", "keep_all_execution_flags_false"),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], discussion_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    proposal_status = "non_executable_paper_live_candidate_proposal_ready_manual_review_required" if final_status == FINAL_STATUS else "proposal_blocked_missing_gate_review"
    rows = [
        ("final_candidate_discussion_status", final_status, "Whether saved evidence supports a non-executable candidate proposal."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("qqq100_status", "qqq100_retained_as_incumbent_paper_live_seed", "QQQ100 remains the current paper-live seed."),
        ("vol_targeted_candidate_status", "limited_manual_candidate_discussion_ready_not_approved" if final_status == FINAL_STATUS else "blocked_missing_gate_review", "Volatility candidate discussion status."),
        ("proposal_status", proposal_status, "Proposal readiness only; no approval."),
        ("plain_english_comparison", plain_english_comparison(), "Plain-English comparison of QQQ100 and volatility candidate."),
        ("gate_review_status", summary_value(inputs["gate_review_summary"], "final_gate_review_status") or "missing_gate_review_status", "Saved gate review status."),
        ("discussion_row_count", str(len(discussion_rows)), "Saved discussion row count."),
        ("largest_blocker", "proposal_ready_but_not_implemented_or_approved" if final_status == FINAL_STATUS else "missing_gate_review", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if final_status == FINAL_STATUS else "run_gate_review_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This discussion report reads saved outputs only and does not call Alpaca."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("paper_live_candidate_not_approved", "blocked", "critical", "The volatility candidate is a proposal only, not an approved paper-live candidate.", NEXT_STEP),
        ("implementation_not_added", "blocked", "critical", "No preview/action/execution implementation is added by this report.", "design_implementation_in_later_separate_step"),
        ("qqq100_not_displaced", "blocked", "critical", "QQQ100 remains the incumbent paper-live seed.", "do_not_replace_qqq100_without_separate_approval"),
        ("component_sleeves_not_approved", "blocked", "critical", "High-growth and crypto sleeves remain research-only.", "do_not_promote_component_sleeves"),
        ("order_instructions_not_allowed", "blocked", "critical", "No executable order fields or instructions are allowed.", "keep_discussion_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("gate_review_missing", "blocked", "critical", "Saved gate review is missing or not ready.", "run_gate_review_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth candidate discussion complete. Proposal only; no execution or scheduling approved.",
        f"final_candidate_discussion_status={summary_value(summary_rows, 'final_candidate_discussion_status')}",
        f"qqq100_status={summary_value(summary_rows, 'qqq100_status')}",
        f"vol_targeted_candidate_status={summary_value(summary_rows, 'vol_targeted_candidate_status')}",
        f"proposal_status={summary_value(summary_rows, 'proposal_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_discussion={output_paths['discussion']}",
        "vol_targeted_candidate_proposal_ready=true; paper_live_candidate_approved=false; preview_implementation_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def discussion_row(created_at: str, item: str, status: str, risk: str, qqq100: str, vol_context: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "discussion_item": item, "discussion_status": status, "risk_level": risk, "qqq100_context": qqq100, "vol_targeted_context": vol_context, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def plain_english_comparison() -> str:
    return (
        "QQQ100 is simpler and remains the current paper-live seed. "
        "The volatility-targeted candidate is broader and more complex: it blends QQQ100, high-growth, crypto, and defensive sleeves, then scales exposure using a 15% volatility target over 20 days. "
        "It may be worth discussing as a proposal, but complexity and component risk mean it is not approved."
    )


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
