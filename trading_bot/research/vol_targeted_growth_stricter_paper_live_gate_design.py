"""Saved-output stricter paper-live discussion gate design for volatility-targeted growth.

This report defines hard blockers and manual-review requirements before the
volatility-targeted 15/20 candidate can be discussed alongside QQQ100. It does
not approve paper-live candidacy, create order instructions, call Alpaca, read
positions, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_stricter_paper_live_gate_design_ready_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_stricter_paper_live_gate_design_blocked_missing_post_comparison_decision"
NEXT_STEP = "manual_review_gate_requirements_before_any_vol_targeted_paper_live_candidate_discussion"

OUTPUT_FILES = {
    "gate": Path("data/vol_targeted_growth_stricter_paper_live_gate_design.csv"),
    "summary": Path("data/vol_targeted_growth_stricter_paper_live_gate_design_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_stricter_paper_live_gate_design_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_stricter_paper_live_gate_design_blockers.csv"),
}

INPUT_FILES = {
    "post_comparison_decision_summary": Path("data/vol_targeted_growth_post_comparison_decision_summary.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "portfolio_risk_policy_summary": Path("data/vol_targeted_growth_portfolio_risk_policy_design_summary.csv"),
    "preview_signal_summary": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "gate_design_only": True,
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

GATE_COLUMNS = [
    "created_at",
    "gate_item",
    "gate_status",
    "risk_level",
    "hard_requirement",
    "why_it_matters",
    "failure_action",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthStricterPaperLiveGateDesignResult:
    output_paths: dict[str, Path]
    gate_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_stricter_paper_live_gate_design(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthStricterPaperLiveGateDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    gate_rows = build_gate_rows(created_at)
    summary_rows = build_summary_rows(inputs, gate_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["gate"], GATE_COLUMNS, gate_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthStricterPaperLiveGateDesignResult(
        output_paths=output_paths,
        gate_rows=gate_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_stricter_paper_live_gate_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-stricter-paper-live-gate-design` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth stricter paper-live gate design saved display. Gate design only; no execution approval.",
        f"final_gate_design_status: {summary_value(rows, 'final_gate_design_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"qqq100_boundary_status: {summary_value(rows, 'qqq100_boundary_status')}",
        f"gate_enforcement_status: {summary_value(rows, 'gate_enforcement_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "gate_enforced=false; vol_targeted_paper_live_candidate_approved=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    status = summary_value(inputs["post_comparison_decision_summary"], "final_post_comparison_decision_status")
    if status == "vol_targeted_growth_stricter_paper_live_discussion_gate_ready_manual_review_required":
        return FINAL_STATUS
    return BLOCKED_STATUS


def build_gate_rows(created_at: str) -> list[dict[str, Any]]:
    return [
        gate_row(created_at, "qqq100_incumbent_boundary", "required", "critical", "QQQ100 remains the only current paper-live seed unless separately displaced.", "The volatility candidate must not overwrite or quietly replace the existing QQQ100 paper-live path.", "block_candidate_discussion", "compare_against_qqq100_without_displacing_it"),
        gate_row(created_at, "total_allocation_cap", "required", "critical", "A maximum total paper allocation must be chosen before any candidate discussion; default design cap remains 0%.", "No multi-sleeve portfolio should become exposure by implication.", "block_candidate_discussion", "define_total_allocation_cap_in_separate_review"),
        gate_row(created_at, "high_growth_sleeve_boundary", "required", "critical", "High-growth sleeve must remain research-only unless separately promoted with its own evidence.", "High-growth risk cannot piggyback on a volatility wrapper.", "block_candidate_discussion", "keep_high_growth_research_only_or_run_separate_promotion_review"),
        gate_row(created_at, "crypto_sleeve_boundary", "required", "critical", "Crypto sleeve must remain research-only; no crypto execution is approved.", "Crypto exposure has separate venue, custody, volatility, and policy risks.", "block_candidate_discussion", "keep_crypto_research_only_or_run_separate_crypto_policy_review"),
        gate_row(created_at, "drawdown_and_stress_review", "required", "high", "Saved drawdown/stress evidence must be reviewed against QQQ100 and the current paper position context.", "Volatility targeting can still fail during rapid crashes and regime shifts.", "block_candidate_discussion", "review_drawdown_stress_before_candidate_discussion"),
        gate_row(created_at, "broker_position_context", "required", "high", "Saved read-only broker comparison must remain current and must not become an order instruction.", "Current paper holdings affect any future discussion, but comparison is not execution.", "block_candidate_discussion", "refresh_readonly_comparison_only_if_explicitly_approved"),
        gate_row(created_at, "order_instruction_boundary", "required", "critical", "No order side, quantity, type, account ID, order ID, API key, webhook, or secret fields may appear.", "The gate is a policy discussion artifact, not a trade ticket.", "block_candidate_discussion", "keep_gate_non_executable"),
        gate_row(created_at, "execution_and_scheduling_boundary", "required", "critical", "No paper execution, live trading, follow-up orders, repeat execution, or scheduling is approved.", "Scheduling or execution would require a later separate implementation and approval chain.", "block_candidate_discussion", "keep_all_approval_flags_false"),
    ]


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    gate_rows: list[dict[str, Any]],
    final_status: str,
) -> list[dict[str, Any]]:
    rows = [
        ("final_gate_design_status", final_status, "Whether saved evidence supports this stricter gate design."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("strategy_plain_english", strategy_explanation(), "What the strategy is trying to do."),
        ("post_comparison_decision_status", summary_value(inputs["post_comparison_decision_summary"], "final_post_comparison_decision_status") or "missing_post_comparison_decision_status", "Saved post-comparison decision status."),
        ("broker_comparison_status", summary_value(inputs["broker_comparison_summary"], "final_comparison_status") or "missing_broker_comparison_status", "Saved read-only broker comparison status."),
        ("qqq100_boundary_status", "qqq100_remains_incumbent_paper_live_seed", "The volatility candidate must be reviewed alongside, not in place of, QQQ100."),
        ("gate_enforcement_status", "gate_not_enforced_design_only", "This report defines gate requirements but does not enforce them."),
        ("gate_row_count", str(len(gate_rows)), "Saved gate row count."),
        ("largest_blocker", "gate_not_enforced_and_candidate_not_approved", "The gate is design-only and no paper-live candidate approval exists."),
        ("recommended_next_step", NEXT_STEP, "Manual review the stricter gate before any candidate approval discussion."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This gate design reads saved outputs only and does not call Alpaca."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("gate_not_enforced", "blocked", "critical", "This report defines requirements only; it does not enforce them.", "manual_review_gate_requirements_first"),
        ("vol_targeted_candidate_not_approved", "blocked", "critical", "The volatility-targeted candidate is not approved for paper-live.", NEXT_STEP),
        ("high_growth_and_crypto_not_approved", "blocked", "critical", "High-growth and crypto sleeves remain research-only.", "do_not_promote_component_sleeves"),
        ("order_instructions_not_allowed", "blocked", "critical", "No executable order fields or instructions are allowed.", "keep_gate_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("missing_post_comparison_decision", "blocked", "critical", "Saved post-comparison decision is missing or not ready.", "run_post_comparison_decision_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth stricter paper-live gate design complete. Gate design only; no execution or scheduling approved.",
        f"final_gate_design_status={summary_value(summary_rows, 'final_gate_design_status')}",
        f"qqq100_boundary_status={summary_value(summary_rows, 'qqq100_boundary_status')}",
        f"gate_enforcement_status={summary_value(summary_rows, 'gate_enforcement_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_gate={output_paths['gate']}",
        "gate_enforced=false; vol_targeted_paper_live_candidate_approved=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def gate_row(created_at: str, item: str, status: str, risk: str, requirement: str, why: str, failure: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "gate_item": item, "gate_status": status, "risk_level": risk, "hard_requirement": requirement, "why_it_matters": why, "failure_action": failure, "required_next_step": next_step, **SAFETY_FLAGS}


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
