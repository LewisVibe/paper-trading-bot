"""Saved-output run-readiness checkpoint for volatility-targeted growth broker comparison.

This checkpoint reviews whether the selected 15/20 volatility-targeted growth
candidate is ready for explicit manual approval of a future read-only broker
position comparison. It does not call Alpaca, read positions, create orders,
schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_readonly_broker_comparison_ready_for_explicit_manual_approval_required"
BLOCKED_STATUS = "vol_targeted_growth_readonly_broker_comparison_blocked_missing_saved_decision"
NEXT_STEP = "request_explicit_manual_approval_before_readonly_broker_position_comparison"

OUTPUT_FILES = {
    "readiness": Path("data/vol_targeted_growth_broker_comparison_run_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_broker_comparison_run_readiness_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_broker_comparison_run_readiness_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_broker_comparison_run_readiness_blockers.csv"),
}

INPUT_FILES = {
    "paper_live_decision_summary": Path("data/vol_targeted_growth_paper_live_decision_summary.csv"),
    "paper_live_decision_blockers": Path("data/vol_targeted_growth_paper_live_decision_blockers.csv"),
    "broker_design_summary": Path("data/vol_targeted_growth_broker_position_comparison_design_summary.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "action_preview_quality_gate_summary": Path("data/vol_targeted_growth_action_preview_quality_gate_summary.csv"),
    "policy_design_summary": Path("data/vol_targeted_growth_portfolio_risk_policy_design_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "run_readiness_only": True,
    "preview_only": True,
    "readonly_broker_comparison_ready_for_manual_approval": True,
    "readonly_broker_comparison_run_approved": False,
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

READINESS_COLUMNS = [
    "created_at",
    "readiness_item",
    "readiness_status",
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
class VolTargetedGrowthBrokerComparisonRunReadinessResult:
    output_paths: dict[str, Path]
    readiness_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_broker_comparison_run_readiness(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthBrokerComparisonRunReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    readiness_rows = build_readiness_rows(created_at, inputs, final_status)
    summary_rows = build_summary_rows(inputs, readiness_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["readiness"], READINESS_COLUMNS, readiness_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthBrokerComparisonRunReadinessResult(
        output_paths=output_paths,
        readiness_rows=readiness_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_broker_comparison_run_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-broker-comparison-run-readiness` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth broker-comparison run-readiness saved display. Manual-review only; no broker read or execution approval.",
        f"final_run_readiness_status: {summary_value(rows, 'final_run_readiness_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"manual_approval_status: {summary_value(rows, 'manual_approval_status')}",
        f"readonly_broker_comparison_status: {summary_value(rows, 'readonly_broker_comparison_status')}",
        f"paper_live_discussion_status: {summary_value(rows, 'paper_live_discussion_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "readonly_broker_comparison_run_approved=false; broker_positions_compared=false; alpaca_called=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    decision_status = summary_value(inputs["paper_live_decision_summary"], "final_decision_status")
    quality_status = summary_value(inputs["action_preview_quality_gate_summary"], "final_quality_gate_status")
    if (
        decision_status == "vol_targeted_growth_research_only_broker_comparison_discussion_ready_manual_review_required"
        and quality_status == "vol_targeted_growth_action_preview_quality_gate_usable_manual_review_required"
    ):
        return FINAL_STATUS
    return BLOCKED_STATUS


def build_readiness_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    decision_status = summary_value(inputs["paper_live_decision_summary"], "final_decision_status")
    broker_design_status = summary_value(inputs["broker_design_summary"], "final_design_status")
    action_status = summary_value(inputs["action_preview_summary"], "final_action_preview_status")
    quality_status = summary_value(inputs["action_preview_quality_gate_summary"], "final_quality_gate_status")
    policy_status = summary_value(inputs["policy_design_summary"], "final_policy_design_status")
    return [
        readiness_row(
            created_at,
            "saved_decision_checkpoint",
            "ready_for_manual_approval_review" if final_status == FINAL_STATUS else "blocked_missing_saved_decision",
            "critical",
            decision_status or "missing_paper_live_decision_status",
            "A saved decision checkpoint is required before asking to run a read-only broker comparison.",
            NEXT_STEP if final_status == FINAL_STATUS else "run_saved_paper_live_decision_checkpoint_first",
        ),
        readiness_row(
            created_at,
            "broker_comparison_design",
            "design_available_manual_review_required" if broker_design_status else "blocked_missing_design",
            "critical",
            broker_design_status or "missing_broker_comparison_design_status",
            "The existing design describes the safe future read-only comparison boundary.",
            NEXT_STEP,
        ),
        readiness_row(
            created_at,
            "action_preview_input",
            "saved_action_preview_available_manual_review_required" if action_status else "blocked_missing_action_preview",
            "high",
            action_status or "missing_action_preview_status",
            "The future comparison must start from saved action-preview context only.",
            "verify_saved_action_preview_before_any_broker_read",
        ),
        readiness_row(
            created_at,
            "action_preview_quality_gate",
            "quality_gate_passed_manual_review_required"
            if quality_status == "vol_targeted_growth_action_preview_quality_gate_usable_manual_review_required"
            else "blocked_missing_or_failed_quality_gate",
            "critical",
            quality_status or "missing_action_preview_quality_gate_status",
            "Saved action-preview rows must pass the quality gate before requesting broker-position comparison approval.",
            NEXT_STEP
            if quality_status == "vol_targeted_growth_action_preview_quality_gate_usable_manual_review_required"
            else "run_vol_targeted_growth_action_preview_quality_gate_first",
        ),
        readiness_row(
            created_at,
            "portfolio_risk_policy_context",
            "policy_design_available_not_enforced" if policy_status else "blocked_missing_policy_design",
            "high",
            policy_status or "missing_policy_design_status",
            "Portfolio risk policy remains design-only and cannot be treated as an enforcement layer.",
            "keep_policy_design_non_enforcing",
        ),
        readiness_row(
            created_at,
            "future_readonly_broker_check_boundary",
            "explicit_manual_approval_required_before_run",
            "critical",
            "no broker read performed; no Alpaca call performed; approval flags remain false.",
            "This checkpoint may justify asking for explicit approval later, but does not grant it.",
            NEXT_STEP,
        ),
        readiness_row(
            created_at,
            "execution_boundary",
            "execution_blocked",
            "critical",
            "no orders; no order instructions; no scheduling; no paper-live approval.",
            "Read-only broker comparison, if later approved, would still not be order approval.",
            "keep_all_execution_flags_false",
        ),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], readiness_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("final_run_readiness_status", final_status, "Whether saved evidence supports asking for explicit approval to run a future read-only broker comparison."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("manual_approval_status", "explicit_manual_approval_required_before_any_broker_read", "No approval is granted by this report."),
        ("readonly_broker_comparison_status", "ready_to_request_manual_approval_not_run" if final_status == FINAL_STATUS else "blocked_missing_saved_decision", "The comparison is not run and not approved here."),
        ("paper_live_discussion_status", "paper_live_discussion_not_approved_research_only", "Paper-live discussion remains unapproved."),
        ("paper_live_decision_status", summary_value(inputs["paper_live_decision_summary"], "final_decision_status") or "missing_paper_live_decision_status", "Saved decision checkpoint status."),
        ("broker_design_status", summary_value(inputs["broker_design_summary"], "final_design_status") or "missing_broker_design_status", "Saved broker-position comparison design status."),
        ("action_preview_quality_gate_status", summary_value(inputs["action_preview_quality_gate_summary"], "final_quality_gate_status") or "missing_action_preview_quality_gate_status", "Saved action-preview quality gate status."),
        ("broker_positions_compared", "false", "No broker positions were read or compared."),
        ("readiness_row_count", str(len(readiness_rows)), "Saved readiness row count."),
        ("largest_blocker", "explicit_manual_approval_not_granted_and_broker_comparison_not_run", "Manual approval is still required before any read-only broker comparison."),
        ("recommended_next_step", NEXT_STEP, "Ask for explicit approval in a separate step before any read-only broker-position comparison command."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("explicit_manual_approval_not_granted", "blocked", "critical", "This checkpoint does not grant approval to run a broker read.", NEXT_STEP),
        ("broker_comparison_not_run", "blocked", "critical", "No Alpaca call or broker-position read has occurred.", NEXT_STEP),
        ("paper_live_candidate_not_approved", "blocked", "critical", "The 15/20 candidate remains research-only.", "do_not_promote_to_paper_live"),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("missing_saved_decision", "blocked", "critical", "Saved paper-live decision checkpoint is missing or not in the expected state.", "run_saved_paper_live_decision_checkpoint_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth broker-comparison run-readiness checkpoint complete. Manual approval still required; no broker read, execution, or scheduling approved.",
        f"final_run_readiness_status={summary_value(rows, 'final_run_readiness_status')}",
        f"manual_approval_status={summary_value(rows, 'manual_approval_status')}",
        f"readonly_broker_comparison_status={summary_value(rows, 'readonly_broker_comparison_status')}",
        f"paper_live_discussion_status={summary_value(rows, 'paper_live_discussion_status')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_readiness={output_paths['readiness']}",
        "readonly_broker_comparison_run_approved=false; broker_positions_compared=false; alpaca_called=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def readiness_row(created_at: str, item: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "readiness_item": item, "readiness_status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


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
