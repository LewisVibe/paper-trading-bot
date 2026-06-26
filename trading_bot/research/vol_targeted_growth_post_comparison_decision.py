"""Saved-output post-comparison decision for volatility-targeted growth 15/20.

This report interprets the saved read-only broker-position comparison and
decides whether the research candidate remains research-only or can move to a
stricter manual paper-live discussion gate. It never calls Alpaca, reads
positions, creates order instructions, schedules anything, or approves
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
READY_STATUS = "vol_targeted_growth_stricter_paper_live_discussion_gate_ready_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_stays_research_only_missing_confirmed_broker_comparison"
NEXT_STEP = "manual_review_stricter_paper_live_discussion_gate_design_before_any_candidate_approval"

OUTPUT_FILES = {
    "decision": Path("data/vol_targeted_growth_post_comparison_decision.csv"),
    "summary": Path("data/vol_targeted_growth_post_comparison_decision_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_post_comparison_decision_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_post_comparison_decision_blockers.csv"),
}

INPUT_FILES = {
    "broker_comparison": Path("data/vol_targeted_growth_broker_position_comparison.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "broker_comparison_blockers": Path("data/vol_targeted_growth_broker_position_comparison_blockers.csv"),
    "paper_live_decision_summary": Path("data/vol_targeted_growth_paper_live_decision_summary.csv"),
    "portfolio_risk_policy_summary": Path("data/vol_targeted_growth_portfolio_risk_policy_design_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "decision_only": True,
    "preview_only": True,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_read_now": False,
    "broker_positions_compared_now": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "paper_live_candidate_approved": False,
    "paper_live_discussion_approved": False,
    "stricter_paper_live_gate_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
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
class VolTargetedGrowthPostComparisonDecisionResult:
    output_paths: dict[str, Path]
    decision_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_post_comparison_decision(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthPostComparisonDecisionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    decision_rows = build_decision_rows(created_at, inputs, final_status)
    summary_rows = build_summary_rows(inputs, decision_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status, inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decision"], DECISION_COLUMNS, decision_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthPostComparisonDecisionResult(
        output_paths=output_paths,
        decision_rows=decision_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_post_comparison_decision(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-post-comparison-decision` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth post-comparison decision saved display. Manual-review only; no execution approval.",
        f"final_post_comparison_decision_status: {summary_value(rows, 'final_post_comparison_decision_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"broker_comparison_status: {summary_value(rows, 'broker_comparison_status')}",
        f"paper_live_discussion_gate_status: {summary_value(rows, 'paper_live_discussion_gate_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "stricter_paper_live_gate_approved=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    comparison_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status")
    read_status = summary_value(inputs["broker_comparison_summary"], "broker_position_read_status")
    if (
        comparison_status == "vol_targeted_growth_broker_position_comparison_completed_readonly_manual_review_required"
        and read_status == "paper_positions_read_readonly"
    ):
        return READY_STATUS
    return BLOCKED_STATUS


def build_decision_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    comparison_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status")
    read_status = summary_value(inputs["broker_comparison_summary"], "broker_position_read_status")
    policy_status = summary_value(inputs["portfolio_risk_policy_summary"], "final_policy_design_status")
    return [
        decision_row(
            created_at,
            "saved_broker_position_comparison",
            "confirmed_readonly_comparison_available" if final_status == READY_STATUS else "blocked_missing_confirmed_readonly_comparison",
            "critical",
            f"comparison_status={comparison_status or 'missing'}; broker_position_read_status={read_status or 'missing'}",
            "Saved broker-position context is enough to discuss a stricter manual gate, but not enough to approve trading.",
            NEXT_STEP if final_status == READY_STATUS else "run_confirmed_readonly_broker_position_comparison_first",
        ),
        decision_row(
            created_at,
            "paper_live_discussion_gate",
            "stricter_gate_design_ready_manual_review_required" if final_status == READY_STATUS else "paper_live_discussion_gate_blocked",
            "critical",
            "comparison context exists; order instructions are still forbidden." if final_status == READY_STATUS else "confirmed comparison context missing.",
            "The next step is a stricter gate design, not paper-live approval.",
            NEXT_STEP,
        ),
        decision_row(
            created_at,
            "portfolio_risk_policy_context",
            "policy_design_available_not_enforced" if policy_status else "policy_design_missing_or_unavailable",
            "high",
            policy_status or "missing_policy_design_status",
            "The risk policy is still design-only and must not be treated as enforcement.",
            "define_enforced_policy_only_in_a_later_separate_step",
        ),
        decision_row(
            created_at,
            "component_boundary",
            "high_growth_and_crypto_remain_research_only",
            "critical",
            "The candidate includes high-growth and crypto research sleeves.",
            "Component sleeves cannot piggyback into execution approval.",
            "keep_component_sleeves_research_only",
        ),
        decision_row(
            created_at,
            "execution_boundary",
            "execution_blocked",
            "critical",
            "no orders; no order instructions; no scheduling; all approval flags false.",
            "This decision report is manual-review context only.",
            "keep_all_execution_flags_false",
        ),
    ]


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    decision_rows: list[dict[str, Any]],
    final_status: str,
) -> list[dict[str, Any]]:
    gate_status = (
        "stricter_paper_live_discussion_gate_design_ready_manual_review_required"
        if final_status == READY_STATUS
        else "stricter_paper_live_discussion_gate_blocked_missing_confirmed_comparison"
    )
    rows = [
        ("final_post_comparison_decision_status", final_status, "Post-comparison decision status."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("broker_comparison_status", summary_value(inputs["broker_comparison_summary"], "final_comparison_status") or "missing_broker_comparison_status", "Saved broker comparison status."),
        ("broker_position_read_status", summary_value(inputs["broker_comparison_summary"], "broker_position_read_status") or "missing_broker_position_read_status", "Saved broker read status from the prior comparison output."),
        ("paper_live_discussion_gate_status", gate_status, "Whether a stricter manual paper-live discussion gate can be designed next."),
        ("strategy_plain_english", strategy_explanation(), "What the strategy is trying to do."),
        ("decision_row_count", str(len(decision_rows)), "Saved decision row count."),
        ("largest_blocker", largest_blocker(final_status), "Primary blocker after saved broker comparison."),
        ("recommended_next_step", NEXT_STEP if final_status == READY_STATUS else "complete_confirmed_readonly_broker_comparison_before_gate_design", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This decision report reads saved CSV output only and does not call Alpaca."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("paper_live_candidate_not_approved", "blocked", "critical", "The candidate is not approved for paper-live trading.", NEXT_STEP),
        ("stricter_gate_not_approved", "blocked", "critical", "The next gate is not implemented or approved by this report.", NEXT_STEP),
        ("order_instructions_not_allowed", "blocked", "critical", "No order side, quantity, type, account, order ID, API key, webhook, or secret fields are allowed.", "keep_decision_manual_review_only"),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(
            0,
            (
                "confirmed_broker_comparison_missing",
                "blocked",
                "critical",
                f"comparison_status={summary_value(inputs['broker_comparison_summary'], 'final_comparison_status') or 'missing'}",
                "complete_confirmed_readonly_broker_position_comparison_first",
            ),
        )
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth post-comparison decision complete. Saved-output/manual-review only; no execution or scheduling approved.",
        f"final_post_comparison_decision_status={summary_value(summary_rows, 'final_post_comparison_decision_status')}",
        f"broker_comparison_status={summary_value(summary_rows, 'broker_comparison_status')}",
        f"paper_live_discussion_gate_status={summary_value(summary_rows, 'paper_live_discussion_gate_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_decision={output_paths['decision']}",
        "stricter_paper_live_gate_approved=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def decision_row(created_at: str, item: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "decision_item": item, "decision_status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def largest_blocker(final_status: str) -> str:
    if final_status == READY_STATUS:
        return "stricter_manual_gate_not_designed_or_approved"
    return "confirmed_readonly_broker_comparison_missing"


def strategy_explanation() -> str:
    return (
        "Research-only 70% QQQ100 core trend, 20% high-growth, 5% crypto, and 5% defensive sleeve mix; "
        "a 15% volatility target over a 20-day window scales exposure within a 1x cap."
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
