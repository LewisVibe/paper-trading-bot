"""Saved-output portfolio-risk policy design for volatility-targeted growth 15/20.

This checkpoint defines review guardrails for the selected volatility-targeted
growth candidate. It does not enforce policy, read broker state, create orders,
schedule anything, or approve paper-live candidacy.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_portfolio_risk_policy_design_ready_manual_review_required"
NEXT_STEP = "manual_review_portfolio_risk_policy_before_any_paper_live_candidate_discussion"

OUTPUT_FILES = {
    "policy": Path("data/vol_targeted_growth_portfolio_risk_policy_design.csv"),
    "summary": Path("data/vol_targeted_growth_portfolio_risk_policy_design_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_portfolio_risk_policy_design_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_portfolio_risk_policy_design_blockers.csv"),
}

INPUT_FILES = {
    "portfolio_risk_review_summary": Path("data/vol_targeted_growth_portfolio_risk_review_summary.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "broker_design_summary": Path("data/vol_targeted_growth_broker_position_comparison_design_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "policy_design_only": True,
    "policy_enforced": False,
    "paper_live_candidate_approved": False,
    "paper_live_discussion_approved": False,
    "broker_positions_compared": False,
    "alpaca_called": False,
    "live_positions_read": False,
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

POLICY_COLUMNS = [
    "created_at",
    "policy_item",
    "policy_status",
    "risk_level",
    "proposed_limit",
    "rationale",
    "stop_condition",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthPortfolioRiskPolicyDesignResult:
    output_paths: dict[str, Path]
    policy_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_portfolio_risk_policy_design(root_dir: Path | str = ".") -> VolTargetedGrowthPortfolioRiskPolicyDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    policy_rows = build_policy_rows(created_at)
    summary_rows = build_summary_rows(inputs, policy_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["policy"], POLICY_COLUMNS, policy_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthPortfolioRiskPolicyDesignResult(
        output_paths=output_paths,
        policy_rows=policy_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_portfolio_risk_policy_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-portfolio-risk-policy-design` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth portfolio-risk policy design saved display. Policy design only; no enforcement or execution approval.",
        f"final_policy_design_status: {summary_value(rows, 'final_policy_design_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"policy_enforcement_status: {summary_value(rows, 'policy_enforcement_status')}",
        f"paper_live_discussion_status: {summary_value(rows, 'paper_live_discussion_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "policy_enforced=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_policy_rows(created_at: str) -> list[dict[str, Any]]:
    return [
        policy_row(created_at, "total_strategy_allocation", "proposed_manual_review_limit", "critical", "0% until explicitly approved; future cap must be set before any paper-live discussion", "A multi-sleeve growth branch should not become active exposure by implication.", "Any missing allocation cap blocks paper-live discussion.", "define_total_allocation_cap_before_candidate_discussion"),
        policy_row(created_at, "qqq100_core_sleeve", "proposed_manual_review_limit", "medium", "target_weight=70%; must remain tied to clean QQQ100 lead evidence", "QQQ100 is the current clean seed but this combined portfolio is separate research.", "If QQQ100 evidence is missing or stale, block.", "verify_qqq100_evidence_before_any_policy_acceptance"),
        policy_row(created_at, "high_growth_sleeve", "proposed_manual_review_limit", "high", "target_weight=20%; no standalone promotion; concentration/outlier warnings must remain visible", "High-growth remains research-only and must not piggyback into paper-live approval.", "If concentration/outlier review is unresolved, block.", "review_high_growth_component_risk_before_policy_acceptance"),
        policy_row(created_at, "crypto_sleeve", "proposed_manual_review_limit", "critical", "target_weight=5%; no crypto execution approved; cap must not be raised without separate crypto policy", "Crypto remains capped research-only exposure in this branch.", "If crypto execution or higher crypto cap is implied, block.", "review_crypto_policy_before_any_candidate_discussion"),
        policy_row(created_at, "defensive_buffer_sleeve", "proposed_manual_review_limit", "medium", "target_weight=5%; define whether cash/bond proxy is available from saved evidence", "The defensive sleeve is a buffer concept, not an execution instruction.", "If defensive input is missing or ambiguous, block.", "define_defensive_sleeve_input_before_policy_acceptance"),
        policy_row(created_at, "drawdown_guardrail", "manual_review_required", "critical", "no paper-live discussion until max drawdown, stress periods, and stop/review thresholds are documented", "Volatility targeting does not remove drawdown risk.", "If drawdown review is missing, block.", "define_drawdown_review_thresholds"),
        policy_row(created_at, "broker_position_guardrail", "manual_review_required", "critical", "broker comparison must be explicitly read-only and approved separately before any current-exposure interpretation", "Saved action preview currently has unknown exposure.", "If current exposure is unknown, block.", "complete_readonly_broker_comparison_review_first"),
        policy_row(created_at, "execution_boundary", "execution_blocked", "critical", "no orders, no scheduling, no runtime enforcement, no paper-live approval", "This is a policy design report only.", "Any execution approval flag must remain false.", "keep_candidate_research_only"),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("final_policy_design_status", FINAL_STATUS, "Risk policy design is ready for manual review only."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("policy_enforcement_status", "policy_not_enforced_design_only", "This report defines guardrails but does not enforce them."),
        ("paper_live_discussion_status", "paper_live_discussion_not_approved_research_only", "Paper-live discussion remains blocked."),
        ("portfolio_risk_review_status", summary_value(inputs["portfolio_risk_review_summary"], "final_risk_review_status") or "missing_portfolio_risk_review", "Saved portfolio-risk review status."),
        ("policy_row_count", str(len(policy_rows)), "Saved policy design row count."),
        ("largest_blocker", "policy_not_enforced_and_broker_comparison_not_complete", "Policy design and broker comparison are not implemented safeguards."),
        ("recommended_next_step", NEXT_STEP, "Manual review policy before any paper-live candidate discussion."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows() -> list[dict[str, Any]]:
    rows = [
        ("policy_not_enforced", "blocked", "critical", "This report defines a policy design but does not enforce it.", "Implement enforcement only in a separate reviewed step."),
        ("broker_comparison_not_complete", "blocked", "critical", "Current exposure remains unknown until a separate read-only broker comparison is approved and run.", "Complete broker comparison review first."),
        ("paper_live_not_approved", "blocked", "critical", "Paper-live candidacy remains unapproved.", NEXT_STEP),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "Keep all approval flags false."),
    ]
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth portfolio-risk policy design complete. Policy design only; no enforcement, execution, or scheduling approved.",
        f"final_policy_design_status={summary_value(rows, 'final_policy_design_status')}",
        f"paper_live_discussion_status={summary_value(rows, 'paper_live_discussion_status')}",
        f"policy_enforcement_status={summary_value(rows, 'policy_enforcement_status')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_policy={output_paths['policy']}",
        "policy_enforced=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def policy_row(created_at: str, item: str, status: str, risk: str, limit: str, rationale: str, stop: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "policy_item": item, "policy_status": status, "risk_level": risk, "proposed_limit": limit, "rationale": rationale, "stop_condition": stop, "required_next_step": next_step, **SAFETY_FLAGS}


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
