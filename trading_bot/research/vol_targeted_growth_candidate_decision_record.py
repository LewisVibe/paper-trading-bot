"""Saved-output candidate decision record for volatility-targeted growth.

This checkpoint records a formal non-executable decision: manual discussion may
continue, QQQ100 remains the incumbent paper-live seed, and implementation,
execution, repeat orders, and scheduling remain blocked.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
INCUMBENT_TICKER = "QQQ"
FINAL_STATUS = "vol_targeted_growth_candidate_decision_manual_discussion_only"
NEXT_STEP = "manual_review_before_any_vol_targeted_preview_or_action_implementation"

OUTPUT_FILES = {
    "record": Path("data/vol_targeted_growth_candidate_decision_record.csv"),
    "summary": Path("data/vol_targeted_growth_candidate_decision_record_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_candidate_decision_record_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_candidate_decision_record_blockers.csv"),
}

INPUT_FILES = {
    "blocker_checklist_summary": Path("data/vol_targeted_growth_candidate_discussion_blocker_checklist_summary.csv"),
    "blocker_checklist_blockers": Path("data/vol_targeted_growth_candidate_discussion_blocker_checklist_blockers.csv"),
    "candidate_discussion_summary": Path("data/vol_targeted_growth_candidate_discussion_summary.csv"),
    "gate_review_summary": Path("data/vol_targeted_growth_gate_review_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "decision_record_only": True,
    "preview_only": True,
    "candidate_discussion_may_continue": True,
    "qqq100_remains_incumbent_seed": True,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_read_now": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "implementation_approved": False,
    "preview_implementation_approved": False,
    "paper_live_candidate_approved": False,
    "vol_targeted_paper_live_candidate_approved": False,
    "seed_change_approved": False,
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
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

RECORD_COLUMNS = [
    "created_at",
    "decision_item",
    "decision_status",
    "risk_level",
    "decision",
    "evidence",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthCandidateDecisionRecordResult:
    output_paths: dict[str, Path]
    record_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_candidate_decision_record(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCandidateDecisionRecordResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    record_rows = build_record_rows(created_at, inputs)
    summary_rows = build_summary_rows(inputs, record_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["record"], RECORD_COLUMNS, record_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthCandidateDecisionRecordResult(
        output_paths=output_paths,
        record_rows=record_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_candidate_decision_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted growth candidate decision record is missing.",
            "Run `python bot.py --vol-targeted-growth-candidate-decision-record` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth candidate decision record saved display. Manual discussion only; no implementation or execution approved.",
        f"final_candidate_decision_status: {summary_value(rows, 'final_candidate_decision_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"decision: {summary_value(rows, 'decision')}",
        f"open_blocker_count: {summary_value(rows, 'open_blocker_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "implementation_approved=false; paper_live_candidate_approved=false; seed_change_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_record_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    checklist_status = summary_value(inputs["blocker_checklist_summary"], "final_blocker_checklist_status") or "missing_blocker_checklist"
    discussion_status = summary_value(inputs["candidate_discussion_summary"], "final_candidate_discussion_status") or "missing_candidate_discussion"
    gate_status = summary_value(inputs["gate_review_summary"], "final_gate_review_status") or "missing_gate_review"
    qqq100_status = summary_value(inputs["qqq100_followup_policy_summary"], "final_followup_policy_status") or "missing_qqq100_followup_policy"
    return [
        record_row(
            created_at,
            "candidate_discussion_decision",
            "manual_discussion_only",
            "high",
            "The volatility-targeted candidate may stay in manual discussion as a non-executable proposal only.",
            f"{discussion_status}; {checklist_status}",
            NEXT_STEP,
        ),
        record_row(
            created_at,
            "incumbent_seed_boundary",
            "qqq100_seed_retained",
            "critical",
            "QQQ100 remains the incumbent paper-live seed and is not displaced by this decision.",
            qqq100_status,
            "do_not_replace_qqq100_without_separate_manual_seed_change_approval",
        ),
        record_row(
            created_at,
            "implementation_boundary",
            "implementation_blocked",
            "critical",
            "No preview, action-preview, allocation, order-ticket, or execution implementation is approved.",
            gate_status,
            "review_open_blockers_before_any_implementation_work",
        ),
        record_row(
            created_at,
            "execution_boundary",
            "execution_blocked",
            "critical",
            "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.",
            "all_approval_flags_false",
            "keep_monitoring_and_reports_non_executable",
        ),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], record_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    open_blockers = len(inputs["blocker_checklist_blockers"])
    rows = [
        ("final_candidate_decision_status", FINAL_STATUS, "Formal decision record status."),
        ("selected_candidate", SELECTED_CANDIDATE, "Volatility-targeted candidate under manual discussion."),
        ("incumbent_seed", f"{INCUMBENT_SEED}/{INCUMBENT_TICKER}", "Current paper-live seed remains unchanged."),
        ("decision", "manual_discussion_only_no_implementation_approval", "Manual discussion may continue, but implementation is not approved."),
        ("candidate_discussion_status", summary_value(inputs["candidate_discussion_summary"], "final_candidate_discussion_status") or "missing_candidate_discussion", "Saved candidate discussion status."),
        ("blocker_checklist_status", summary_value(inputs["blocker_checklist_summary"], "final_blocker_checklist_status") or "missing_blocker_checklist", "Saved blocker checklist status."),
        ("open_blocker_count", str(open_blockers), "Open blocker rows copied from the blocker checklist."),
        ("largest_blocker", "implementation_not_approved_and_gate_not_enforced", "Primary blocker before implementation."),
        ("recommended_next_step", NEXT_STEP, "Next safe step."),
        ("record_row_count", str(len(record_rows)), "Decision rows written."),
    ]
    return [summary_row(name, value, details) for name, value, details in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This decision record reads saved outputs only and does not call Alpaca."))
    rows.append(("order_instruction_status", "not_created", "No order side, quantity, type, account, API key, webhook, token, or order ID fields are created."))
    return [evidence_row(name, value, details) for name, value, details in rows]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("implementation_not_approved", "blocked", "critical", "Manual discussion does not approve implementation.", NEXT_STEP),
        ("qqq100_not_displaced", "blocked", "critical", "QQQ100 remains the incumbent seed.", "separate_seed_change_approval_required"),
        ("order_instructions_not_allowed", "blocked", "critical", "No executable order fields or instructions are allowed.", "keep_decision_non_executable"),
        ("execution_and_scheduling_not_approved", "blocked", "critical", "Execution, repeat orders, follow-up orders, and scheduling remain false.", "keep_all_approval_flags_false"),
    ]
    if not inputs["blocker_checklist_summary"]:
        rows.insert(0, ("missing_blocker_checklist", "blocked", "critical", "Saved blocker checklist is missing.", "run_blocker_checklist_first"))
    if not inputs["candidate_discussion_summary"]:
        rows.insert(0, ("missing_candidate_discussion", "blocked", "critical", "Saved candidate discussion is missing.", "run_candidate_discussion_first"))
    return [blocker_row(*row) for row in rows]


def record_row(created_at: str, item: str, status: str, risk: str, decision: str, evidence: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "decision_item": item,
        "decision_status": status,
        "risk_level": risk,
        "decision": decision,
        "evidence": evidence,
        "required_next_step": next_step,
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
        "Volatility-targeted growth candidate decision record complete. Manual discussion only; no implementation, execution, or scheduling approved.",
        f"final_candidate_decision_status={summary_value(summary_rows, 'final_candidate_decision_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"incumbent_seed={summary_value(summary_rows, 'incumbent_seed')}",
        f"decision={summary_value(summary_rows, 'decision')}",
        f"open_blocker_count={summary_value(summary_rows, 'open_blocker_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_record={output_paths['record']}",
        "implementation_approved=false; paper_live_candidate_approved=false; seed_change_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
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
