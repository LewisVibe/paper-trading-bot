"""Saved-output manual approval record for volatility seed-change design."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_seed_change_manual_approval_recorded_implementation_required"
BLOCKED_STATUS = "vol_targeted_growth_seed_change_manual_approval_blocked_missing_formal_proposal"
NEXT_STEP = "design_seed_change_implementation_without_execution"

OUTPUT_FILES = {
    "record": Path("data/vol_targeted_growth_seed_change_manual_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_manual_approval_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_manual_approval_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_manual_approval_blockers.csv"),
}

INPUT_FILES = {
    "formal_proposal_summary": Path("data/vol_targeted_growth_formal_seed_change_proposal_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "manual_approval_record_only": True,
    "proposal_only": True,
    "preview_only": True,
    "manual_approval_recorded": True,
    "seed_change_approved_for_implementation_design": True,
    "seed_changed": False,
    "seed_change_implemented": False,
    "qqq100_displacement_implemented": False,
    "qqq100_displacement_approved": False,
    "vol_targeted_seed_approved": False,
    "action_preview_added": False,
    "order_instructions_created": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_read_now": False,
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
    "record_section",
    "record_status",
    "record_text",
    "saved_evidence",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthSeedChangeManualApprovalRecordResult:
    output_paths: dict[str, Path]
    record_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_manual_approval_record(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthSeedChangeManualApprovalRecordResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    proposal_ready = formal_proposal_ready(inputs)
    final_status = FINAL_STATUS if proposal_ready else BLOCKED_STATUS
    record_rows = build_record_rows(created_at, inputs, final_status)
    summary_rows = build_summary_rows(inputs, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["record"], RECORD_COLUMNS, record_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeManualApprovalRecordResult(
        output_paths=output_paths,
        record_rows=record_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_manual_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-manual-approval-record` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change manual approval record saved display. Record only; no seed change or execution approved.",
        f"final_manual_approval_status: {summary_value(rows, 'final_manual_approval_status')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"candidate_for_implementation_design: {summary_value(rows, 'candidate_for_implementation_design')}",
        f"manual_approval_scope: {summary_value(rows, 'manual_approval_scope')}",
        f"seed_change_decision: {summary_value(rows, 'seed_change_decision')}",
        f"implementation_status: {summary_value(rows, 'implementation_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "manual_approval_recorded=true; seed_changed=false; qqq100_displacement_approved=false; vol_targeted_seed_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def formal_proposal_ready(inputs: dict[str, list[dict[str, str]]]) -> bool:
    proposal_rows = inputs["formal_proposal_summary"]
    return (
        summary_value(proposal_rows, "final_proposal_status")
        == "vol_targeted_growth_formal_seed_change_proposal_created_manual_approval_required"
        and summary_value(proposal_rows, "proposal_decision") == "proposal_created_for_manual_review_not_approved"
        and summary_value(proposal_rows, "seed_change_decision") == "seed_not_changed_qqq100_retained"
    )


def build_record_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, str]]],
    final_status: str,
) -> list[dict[str, Any]]:
    sections = [
        (
            "manual_approval_record",
            final_status,
            "Manual approval is recorded for a separate implementation-design step only.",
            proposal_context(inputs),
            NEXT_STEP if final_status == FINAL_STATUS else "create_formal_seed_change_proposal_first",
        ),
        (
            "active_seed_boundary",
            "qqq100_active_seed_retained_until_separate_implementation",
            f"{INCUMBENT_SEED} remains the active seed until a separate implementation checkpoint changes it.",
            f"incumbent_seed={INCUMBENT_SEED}; candidate={SELECTED_CANDIDATE}",
            "separate_seed_change_implementation_required",
        ),
        (
            "implementation_boundary",
            "implementation_not_added",
            "No seed switch, action preview implementation, order instruction, paper execution, live execution, repeat order, or schedule is created here.",
            "all_execution_and_scheduling_flags_false",
            NEXT_STEP,
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "Manual approval for design does not approve paper trading, live trading, follow-up orders, repeat orders, or scheduling.",
            "approval_scope_is_design_only",
            "keep_all_execution_flags_false",
        ),
    ]
    return [
        {
            "created_at": created_at,
            "record_section": section,
            "record_status": status,
            "record_text": text,
            "saved_evidence": evidence,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for section, status, text, evidence, next_step in sections
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    ready = final_status == FINAL_STATUS
    rows = [
        ("final_manual_approval_status", final_status, "Manual approval record checkpoint status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current active seed remains unchanged."),
        ("candidate_for_implementation_design", SELECTED_CANDIDATE, "Candidate approved for implementation-design work only."),
        (
            "manual_approval_scope",
            "approval_to_design_seed_change_implementation_not_to_execute" if ready else "approval_blocked_missing_formal_proposal",
            "Scope of this approval record.",
        ),
        (
            "seed_change_decision",
            "seed_not_changed_qqq100_retained_until_separate_implementation",
            "No seed change is implemented by this command.",
        ),
        ("implementation_status", "implementation_not_added", "No action preview or execution wiring is added."),
        ("source_formal_proposal_status", summary_value(inputs["formal_proposal_summary"], "final_proposal_status") or "missing_formal_proposal", "Saved formal proposal status."),
        ("source_proposal_decision", summary_value(inputs["formal_proposal_summary"], "proposal_decision") or "missing_proposal_decision", "Saved formal proposal decision."),
        ("largest_blocker", "seed_change_implementation_design_required" if ready else "missing_formal_seed_change_proposal", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if ready else "create_formal_seed_change_proposal_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        (
            "formal_proposal_summary_input",
            f"{INPUT_FILES['formal_proposal_summary']}; rows={len(inputs['formal_proposal_summary'])}",
            "Saved formal proposal summary row count.",
        ),
        ("manual_approval_recorded", "true", "Approval is recorded for implementation design only."),
        ("seed_changed_now", "false", "This record does not change the seed."),
        ("broker_read_now", "false", "This record reads saved outputs only and does not call Alpaca."),
    ]
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("seed_not_changed", "blocked", "critical", "QQQ100 remains active until a separate implementation checkpoint.", "separate_seed_change_implementation_required"),
        ("implementation_not_added", "blocked", "critical", "No action preview implementation, seed switch, or execution wiring is added.", NEXT_STEP),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("formal_proposal_missing", "blocked", "critical", "Saved formal proposal summary is missing or not ready.", "create_formal_seed_change_proposal_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth seed-change manual approval record complete. Approval is for implementation design only; no seed change or execution approved.",
        f"final_manual_approval_status={summary_value(summary_rows, 'final_manual_approval_status')}",
        f"manual_approval_scope={summary_value(summary_rows, 'manual_approval_scope')}",
        f"seed_change_decision={summary_value(summary_rows, 'seed_change_decision')}",
        f"implementation_status={summary_value(summary_rows, 'implementation_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_record={output_paths['record']}",
        "manual_approval_recorded=true; seed_changed=false; qqq100_displacement_approved=false; vol_targeted_seed_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def proposal_context(inputs: dict[str, list[dict[str, str]]]) -> str:
    rows = inputs["formal_proposal_summary"]
    return (
        f"final_proposal_status={summary_value(rows, 'final_proposal_status') or 'missing'}; "
        f"proposal_decision={summary_value(rows, 'proposal_decision') or 'missing'}; "
        f"seed_change_decision={summary_value(rows, 'seed_change_decision') or 'missing'}"
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
