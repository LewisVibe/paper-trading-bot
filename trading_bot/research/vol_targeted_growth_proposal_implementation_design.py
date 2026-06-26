"""Saved-output implementation design checkpoint for volatility-targeted growth.

This report turns the candidate-discussion result into a design checklist for a
future non-executable preview/action proposal. It does not implement preview
logic, create order instructions, call Alpaca, read positions, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
QQQ100_LEAD = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_proposal_implementation_design_ready_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_proposal_implementation_design_blocked_missing_candidate_discussion"
NEXT_STEP = "manual_review_design_before_any_preview_or_action_implementation"

OUTPUT_FILES = {
    "design": Path("data/vol_targeted_growth_proposal_implementation_design.csv"),
    "summary": Path("data/vol_targeted_growth_proposal_implementation_design_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_proposal_implementation_design_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_proposal_implementation_design_blockers.csv"),
}

INPUT_FILES = {
    "candidate_discussion_summary": Path("data/vol_targeted_growth_candidate_discussion_summary.csv"),
    "candidate_discussion_blockers": Path("data/vol_targeted_growth_candidate_discussion_blockers.csv"),
    "gate_review_summary": Path("data/vol_targeted_growth_gate_review_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "design_only": True,
    "proposal_only": True,
    "preview_only": True,
    "implementation_added": False,
    "preview_action_added": False,
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

DESIGN_COLUMNS = [
    "created_at",
    "design_item",
    "design_status",
    "risk_level",
    "requirement",
    "implementation_boundary",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthProposalImplementationDesignResult:
    output_paths: dict[str, Path]
    design_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_proposal_implementation_design(root_dir: Path | str = ".") -> VolTargetedGrowthProposalImplementationDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    design_rows = build_design_rows(created_at, final_status)
    summary_rows = build_summary_rows(inputs, design_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["design"], DESIGN_COLUMNS, design_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthProposalImplementationDesignResult(
        output_paths=output_paths,
        design_rows=design_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_proposal_implementation_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-proposal-implementation-design` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth proposal implementation design saved display. Design only; no implementation or execution approval.",
        f"final_design_status: {summary_value(rows, 'final_design_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"implementation_status: {summary_value(rows, 'implementation_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "implementation_added=false; preview_action_added=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    discussion_status = summary_value(inputs["candidate_discussion_summary"], "final_candidate_discussion_status")
    if discussion_status == "vol_targeted_growth_non_executable_candidate_proposal_ready_manual_review_required":
        return FINAL_STATUS
    return BLOCKED_STATUS


def build_design_rows(created_at: str, final_status: str) -> list[dict[str, Any]]:
    ready = final_status == FINAL_STATUS
    return [
        design_row(created_at, "scope_boundary", "design_ready_manual_review_required" if ready else "blocked_missing_candidate_discussion", "critical", "Future work must remain a separate non-executable preview/action proposal first.", "No implementation is added by this checkpoint.", NEXT_STEP if ready else "run_candidate_discussion_first"),
        design_row(created_at, "qqq100_boundary", "incumbent_seed_retained", "critical", "QQQ100 remains the only current paper-live seed.", "Volatility candidate must not displace QQQ100 without separate approval.", "keep_qqq100_as_incumbent_seed"),
        design_row(created_at, "input_contract", "saved_outputs_required", "high", "A future implementation must read saved target-sleeve evidence and current safe status outputs.", "This checkpoint reads summaries only and does not refresh market data.", "define_saved_input_schema_before_implementation"),
        design_row(created_at, "broker_boundary", "no_broker_read_in_design", "critical", "Any future broker comparison must remain separately confirmed read-only.", "This design does not call Alpaca or read positions.", "keep_broker_reads_separate_and_confirmed"),
        design_row(created_at, "preview_boundary", "preview_action_not_added", "critical", "Preview/action rows would require a later non-executable implementation step.", "No desired orders, side, quantity, or order type fields are created here.", "design_preview_schema_without_order_instructions"),
        design_row(created_at, "approval_boundary", "all_approvals_false", "critical", "Proposal design cannot approve paper-live candidacy, follow-up orders, execution, live trading, or scheduling.", "All approval flags stay false.", "manual_review_before_any_future_code_change"),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], design_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("final_design_status", final_status, "Whether saved candidate discussion supports a design-only implementation checkpoint."),
        ("selected_candidate", SELECTED_CANDIDATE, "Volatility-targeted candidate under discussion."),
        ("incumbent_seed", QQQ100_LEAD, "QQQ100 remains the incumbent paper-live seed."),
        ("candidate_discussion_status", summary_value(inputs["candidate_discussion_summary"], "final_candidate_discussion_status") or "missing_candidate_discussion", "Saved candidate discussion status."),
        ("implementation_status", "design_only_no_implementation_added", "No preview/action/execution implementation is added."),
        ("design_row_count", str(len(design_rows)), "Saved design row count."),
        ("largest_blocker", "implementation_not_added_and_not_approved" if final_status == FINAL_STATUS else "missing_candidate_discussion", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if final_status == FINAL_STATUS else "run_candidate_discussion_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This design report reads saved outputs only and does not call Alpaca."))
    rows.append(("implementation_added_now", "false", "This checkpoint does not add preview/action/execution implementation."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("implementation_not_added", "blocked", "critical", "No preview/action implementation has been added.", NEXT_STEP),
        ("paper_live_candidate_not_approved", "blocked", "critical", "The candidate remains an unapproved proposal.", "separate_manual_candidate_approval_required"),
        ("qqq100_not_displaced", "blocked", "critical", "QQQ100 remains the incumbent paper-live seed.", "separate_review_required_before_any_displacement"),
        ("order_instructions_not_allowed", "blocked", "critical", "No order side, quantity, order type, or executable instructions are allowed.", "future_preview_schema_must_stay_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, repeat order, follow-up order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("candidate_discussion_missing", "blocked", "critical", "Saved candidate discussion is missing or not ready.", "run_candidate_discussion_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth proposal implementation design complete. Design only; no implementation or execution approved.",
        f"final_design_status={summary_value(summary_rows, 'final_design_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"incumbent_seed={summary_value(summary_rows, 'incumbent_seed')}",
        f"implementation_status={summary_value(summary_rows, 'implementation_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_design={output_paths['design']}",
        "implementation_added=false; preview_action_added=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def design_row(created_at: str, item: str, status: str, risk: str, requirement: str, boundary: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "design_item": item, "design_status": status, "risk_level": risk, "requirement": requirement, "implementation_boundary": boundary, "required_next_step": next_step, **SAFETY_FLAGS}


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
