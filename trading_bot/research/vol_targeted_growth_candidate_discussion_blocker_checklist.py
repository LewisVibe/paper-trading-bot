"""Final blocker checklist before volatility-targeted implementation work.

This saved-output checkpoint reads prior reports only. It does not call Alpaca,
read positions, refresh market data, create order instructions, schedule
anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_candidate_discussion_blocker_checklist_manual_review_required"
NEXT_STEP = "manual_review_blocker_checklist_before_any_vol_targeted_implementation_work"

OUTPUT_FILES = {
    "checklist": Path("data/vol_targeted_growth_candidate_discussion_blocker_checklist.csv"),
    "summary": Path("data/vol_targeted_growth_candidate_discussion_blocker_checklist_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_candidate_discussion_blocker_checklist_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_candidate_discussion_blocker_checklist_blockers.csv"),
}

INPUT_FILES = {
    "gate_review_summary": Path("data/vol_targeted_growth_gate_review_summary.csv"),
    "stricter_gate_summary": Path("data/vol_targeted_growth_stricter_paper_live_gate_design_summary.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "action_preview_quality_gate_summary": Path("data/vol_targeted_growth_action_preview_quality_gate_summary.csv"),
    "active_seed_readiness_summary": Path("data/vol_targeted_growth_active_seed_readiness_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "checklist_only": True,
    "preview_only": True,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_read_now": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "implementation_approved": False,
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

CHECKLIST_COLUMNS = [
    "created_at",
    "blocker_name",
    "status",
    "severity",
    "evidence",
    "why_it_blocks_implementation",
    "required_resolution",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthCandidateDiscussionBlockerChecklistResult:
    output_paths: dict[str, Path]
    checklist_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_candidate_discussion_blocker_checklist(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCandidateDiscussionBlockerChecklistResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    checklist_rows = build_checklist_rows(created_at, inputs)
    summary_rows = build_summary_rows(inputs, checklist_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(checklist_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["checklist"], CHECKLIST_COLUMNS, checklist_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthCandidateDiscussionBlockerChecklistResult(
        output_paths=output_paths,
        checklist_rows=checklist_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_candidate_discussion_blocker_checklist(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted growth candidate discussion blocker checklist is missing.",
            "Run `python bot.py --vol-targeted-growth-candidate-discussion-blocker-checklist` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth candidate discussion blocker checklist saved display. Report only; no implementation or execution approved.",
        f"final_blocker_checklist_status: {summary_value(rows, 'final_blocker_checklist_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"limited_manual_discussion_status: {summary_value(rows, 'limited_manual_discussion_status')}",
        f"open_blocker_count: {summary_value(rows, 'open_blocker_count')}",
        f"critical_blocker_count: {summary_value(rows, 'critical_blocker_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "implementation_approved=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_checklist_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    gate_status = summary_value(inputs["gate_review_summary"], "final_gate_review_status")
    broker_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status")
    quality_status = summary_value(inputs["action_preview_quality_gate_summary"], "final_quality_gate_status")
    return [
        checklist_row(
            created_at,
            "limited_discussion_only_not_approval",
            "open",
            "critical",
            gate_status or "missing_gate_review_status",
            "Gate review allows limited manual discussion only; it does not approve implementation.",
            "record_separate_manual_candidate_decision_before_any_code_work",
        ),
        checklist_row(
            created_at,
            "gate_not_enforced",
            "open",
            "critical",
            summary_value(inputs["stricter_gate_summary"], "gate_enforcement_status") or "missing_gate_enforcement_status",
            "The stricter gate is design-only and cannot protect runtime behaviour.",
            "design_enforcement_and_tests_in_a_later_separate_step",
        ),
        checklist_row(
            created_at,
            "unmapped_sleeves_not_actionable",
            "open",
            "critical",
            summary_value(inputs["stricter_gate_summary"], "unmapped_sleeve_status") or "missing_unmapped_sleeve_status",
            "High-growth, crypto, and defensive sleeves are not direct broker-symbol actions.",
            "create_symbol_mapping_policy_before_any_action_implementation",
        ),
        checklist_row(
            created_at,
            "component_sleeves_research_only",
            "open",
            "critical",
            "high_growth_and_crypto_remain_research_only",
            "Component sleeves cannot piggyback into paper-live execution through the volatility wrapper.",
            "separate_component_promotion_reviews_required",
        ),
        checklist_row(
            created_at,
            "broker_comparison_context_only",
            "open",
            "high",
            broker_status or "missing_broker_comparison_status",
            "Read-only broker comparison is context only and not a trade plan.",
            "manual_review_comparison_before_any_candidate_decision",
        ),
        checklist_row(
            created_at,
            "action_preview_quality_context_only",
            "open",
            "high",
            quality_status or "missing_action_preview_quality_gate_status",
            "The action preview is usable for manual review only and still lacks executable position policy.",
            "define_non_executable_candidate_decision_before_implementation",
        ),
        checklist_row(
            created_at,
            "order_instruction_fields_forbidden",
            "open",
            "critical",
            "order_side;order_quantity;order_type;account_id;order_id;api_key;webhook;secret_fields_forbidden",
            "Implementation must not introduce order-ticket fields at this stage.",
            "schema_verifier_required_before_any_new_preview_output",
        ),
        checklist_row(
            created_at,
            "execution_and_scheduling_not_approved",
            "open",
            "critical",
            "execution=false;paper_execution=false;scheduling=false",
            "No implementation work may create execution, repeat-order, follow-up-order, or scheduling paths.",
            "keep_all_execution_and_scheduling_flags_false",
        ),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    open_rows = [row for row in rows if row.get("status") == "open"]
    critical_rows = [row for row in open_rows if row.get("severity") == "critical"]
    summary = [
        ("final_blocker_checklist_status", FINAL_STATUS, "Candidate discussion blocker checklist status."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("limited_manual_discussion_status", summary_value(inputs["gate_review_summary"], "limited_manual_candidate_discussion_status") or "missing_gate_review_discussion_status", "Gate review discussion status."),
        ("open_blocker_count", str(len(open_rows)), "Open blockers before implementation work."),
        ("critical_blocker_count", str(len(critical_rows)), "Critical blockers before implementation work."),
        ("largest_blocker", "implementation_not_approved_and_gate_not_enforced", "Primary reason not to implement runtime behaviour yet."),
        ("recommended_next_step", NEXT_STEP, "Manual review this checklist before any implementation work."),
        ("execution_status", "execution_blocked", "Execution remains blocked."),
    ]
    return [summary_row(name, value, details) for name, value, details in summary]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This checklist reads saved outputs only and does not call Alpaca."))
    rows.append(("implementation_status", "not_approved", "No implementation work is approved by this checklist."))
    return [evidence_row(name, value, details) for name, value, details in rows]


def build_blocker_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = [
        (str(row["blocker_name"]), str(row["status"]), str(row["severity"]), str(row["why_it_blocks_implementation"]), str(row["required_resolution"]))
        for row in rows
    ]
    return [blocker_row(name, status, severity, details, next_step) for name, status, severity, details, next_step in blockers]


def checklist_row(
    created_at: str,
    name: str,
    status: str,
    severity: str,
    evidence: str,
    why: str,
    resolution: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "evidence": evidence,
        "why_it_blocks_implementation": why,
        "required_resolution": resolution,
        **SAFETY_FLAGS,
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth candidate discussion blocker checklist complete. Report only; no implementation, execution, or scheduling approved.",
        f"final_blocker_checklist_status={summary_value(summary_rows, 'final_blocker_checklist_status')}",
        f"limited_manual_discussion_status={summary_value(summary_rows, 'limited_manual_discussion_status')}",
        f"open_blocker_count={summary_value(summary_rows, 'open_blocker_count')}",
        f"critical_blocker_count={summary_value(summary_rows, 'critical_blocker_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_checklist={output_paths['checklist']}",
        "implementation_approved=false; paper_live_candidate_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


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
