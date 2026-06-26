"""Saved-output paper-live decision checkpoint for volatility-targeted growth 15/20.

This checkpoint decides only whether the selected research candidate is ready
for a future manual discussion of read-only broker-position comparison. It does
not read broker state, create orders, enforce policy, schedule anything, or
approve paper-live candidacy.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_research_only_broker_comparison_discussion_ready_manual_review_required"
NEXT_STEP = "manual_review_before_any_readonly_broker_position_comparison"

OUTPUT_FILES = {
    "decision": Path("data/vol_targeted_growth_paper_live_decision.csv"),
    "summary": Path("data/vol_targeted_growth_paper_live_decision_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_paper_live_decision_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_paper_live_decision_blockers.csv"),
}

INPUT_FILES = {
    "policy_design_summary": Path("data/vol_targeted_growth_portfolio_risk_policy_design_summary.csv"),
    "portfolio_risk_review_summary": Path("data/vol_targeted_growth_portfolio_risk_review_summary.csv"),
    "broker_design_summary": Path("data/vol_targeted_growth_broker_position_comparison_design_summary.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "decision_only": True,
    "preview_only": True,
    "paper_live_candidate_approved": False,
    "paper_live_discussion_approved": False,
    "broker_position_comparison_approved": False,
    "broker_positions_compared": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "never_schedule_order_capable_commands": True,
}

DECISION_COLUMNS = [
    "created_at",
    "decision_item",
    "decision_status",
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
class VolTargetedGrowthPaperLiveDecisionResult:
    output_paths: dict[str, Path]
    decision_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_paper_live_decision(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthPaperLiveDecisionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    decision_rows = build_decision_rows(created_at, inputs)
    summary_rows = build_summary_rows(inputs, decision_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decision"], DECISION_COLUMNS, decision_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthPaperLiveDecisionResult(
        output_paths=output_paths,
        decision_rows=decision_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_paper_live_decision(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-paper-live-decision` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth paper-live decision saved display. Manual-review only; no broker read or execution approval.",
        f"final_decision_status: {summary_value(rows, 'final_decision_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"research_status: {summary_value(rows, 'research_status')}",
        f"broker_position_comparison_discussion_status: {summary_value(rows, 'broker_position_comparison_discussion_status')}",
        f"paper_live_discussion_status: {summary_value(rows, 'paper_live_discussion_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "broker_positions_compared=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_decision_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    policy_status = summary_value(inputs["policy_design_summary"], "final_policy_design_status")
    risk_status = summary_value(inputs["portfolio_risk_review_summary"], "final_risk_review_status")
    broker_design_status = summary_value(inputs["broker_design_summary"], "final_design_status")
    action_status = summary_value(inputs["action_preview_summary"], "final_action_preview_status")
    return [
        decision_row(
            created_at,
            "candidate_scope",
            "research_only_retained",
            "high",
            f"policy={policy_status or 'missing'}; risk_review={risk_status or 'missing'}",
            "The selected 15/20 candidate remains a research branch, not a paper-live candidate.",
            NEXT_STEP,
        ),
        decision_row(
            created_at,
            "broker_position_comparison_discussion",
            "broker_position_comparison_discussion_ready_manual_review_required",
            "critical",
            broker_design_status or "missing_broker_position_comparison_design",
            "A future read-only broker-position comparison may be discussed manually, but is not approved or run here.",
            NEXT_STEP,
        ),
        decision_row(
            created_at,
            "saved_action_preview_boundary",
            "unknown_exposure_requires_manual_review",
            "critical",
            action_status or "missing_action_preview_status",
            "Saved action preview rows cannot become current-position decisions without a separate approved broker comparison.",
            "keep_action_preview_saved_output_only",
        ),
        decision_row(
            created_at,
            "paper_live_boundary",
            "paper_live_candidate_not_approved",
            "critical",
            "policy not enforced; broker positions not compared; high-growth and crypto components remain research-only.",
            "Manual discussion readiness is not paper-live approval.",
            "do_not_promote_to_paper_live",
        ),
        decision_row(
            created_at,
            "execution_boundary",
            "execution_blocked",
            "critical",
            "no orders; no order instructions; no scheduling; all approval flags false.",
            "Lock the checkpoint to reporting only.",
            "keep_all_execution_flags_false",
        ),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], decision_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("final_decision_status", FINAL_STATUS, "Research-only candidate can be discussed for a future read-only broker comparison after manual review."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("research_status", "research_only_retained", "The candidate remains research-only."),
        ("broker_position_comparison_discussion_status", "broker_position_comparison_discussion_ready_manual_review_required", "This is discussion readiness only; no broker comparison is approved or run."),
        ("paper_live_discussion_status", "paper_live_discussion_not_approved_research_only", "Paper-live candidate discussion remains unapproved."),
        ("policy_design_status", summary_value(inputs["policy_design_summary"], "final_policy_design_status") or "missing_policy_design_status", "Saved portfolio-risk policy design status."),
        ("portfolio_risk_review_status", summary_value(inputs["portfolio_risk_review_summary"], "final_risk_review_status") or "missing_portfolio_risk_review_status", "Saved portfolio-risk review status."),
        ("broker_positions_compared", "false", "No broker positions were read or compared."),
        ("decision_row_count", str(len(decision_rows)), "Saved decision row count."),
        ("largest_blocker", "paper_live_policy_not_enforced_and_broker_comparison_not_run", "The risk policy is design-only and broker-position comparison has not been approved or run."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any separate read-only broker-position comparison command."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows() -> list[dict[str, Any]]:
    rows = [
        ("paper_live_candidate_not_approved", "blocked", "critical", "The 15/20 candidate remains research-only.", "Complete manual review before any paper-live candidate discussion."),
        ("broker_comparison_not_run", "blocked", "critical", "Broker positions have not been read or compared.", NEXT_STEP),
        ("policy_not_enforced", "blocked", "critical", "Portfolio risk policy exists as design only and is not enforced.", "Do not use policy design as execution guardrail."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "Keep all approval flags false."),
    ]
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth paper-live decision checkpoint complete. Research-only; no broker read, execution, or scheduling approved.",
        f"final_decision_status={summary_value(rows, 'final_decision_status')}",
        f"research_status={summary_value(rows, 'research_status')}",
        f"broker_position_comparison_discussion_status={summary_value(rows, 'broker_position_comparison_discussion_status')}",
        f"paper_live_discussion_status={summary_value(rows, 'paper_live_discussion_status')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_decision={output_paths['decision']}",
        "broker_positions_compared=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def decision_row(created_at: str, item: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "decision_item": item, "decision_status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


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
