"""Saved-output implementation design checkpoint for a volatility seed change."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_seed_change_implementation_design_created_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_seed_change_implementation_design_blocked_missing_manual_approval_record"
NEXT_STEP = "manual_review_seed_change_implementation_design_before_code_change"

OUTPUT_FILES = {
    "design": Path("data/vol_targeted_growth_seed_change_implementation_design.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_implementation_design_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_implementation_design_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_implementation_design_blockers.csv"),
}

INPUT_FILES = {
    "manual_approval_summary": Path("data/vol_targeted_growth_seed_change_manual_approval_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "design_only": True,
    "implementation_plan_only": True,
    "preview_only": True,
    "manual_approval_recorded": True,
    "seed_change_approved_for_implementation_design": True,
    "seed_changed": False,
    "seed_change_implemented": False,
    "qqq100_displacement_implemented": False,
    "qqq100_displacement_approved": False,
    "vol_targeted_seed_approved": False,
    "active_seed_changed": False,
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
class VolTargetedGrowthSeedChangeImplementationDesignResult:
    output_paths: dict[str, Path]
    design_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_implementation_design(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthSeedChangeImplementationDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    approval_ready = manual_approval_ready(inputs)
    final_status = FINAL_STATUS if approval_ready else BLOCKED_STATUS
    design_rows = build_design_rows(created_at, final_status)
    summary_rows = build_summary_rows(inputs, design_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["design"], DESIGN_COLUMNS, design_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeImplementationDesignResult(
        output_paths=output_paths,
        design_rows=design_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_implementation_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-implementation-design` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change implementation design saved display. Design only; no seed change or execution approved.",
        f"final_design_status: {summary_value(rows, 'final_design_status')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"candidate_seed: {summary_value(rows, 'candidate_seed')}",
        f"implementation_scope: {summary_value(rows, 'implementation_scope')}",
        f"seed_change_decision: {summary_value(rows, 'seed_change_decision')}",
        f"implementation_status: {summary_value(rows, 'implementation_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_changed=false; active_seed_changed=false; qqq100_displacement_approved=false; vol_targeted_seed_approved=false; action_preview_added=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def manual_approval_ready(inputs: dict[str, list[dict[str, str]]]) -> bool:
    rows = inputs["manual_approval_summary"]
    return (
        summary_value(rows, "final_manual_approval_status")
        == "vol_targeted_growth_seed_change_manual_approval_recorded_implementation_required"
        and summary_value(rows, "manual_approval_scope") == "approval_to_design_seed_change_implementation_not_to_execute"
        and summary_value(rows, "seed_change_decision") == "seed_not_changed_qqq100_retained_until_separate_implementation"
    )


def build_design_rows(created_at: str, final_status: str) -> list[dict[str, Any]]:
    ready = final_status == FINAL_STATUS
    return [
        design_row(
            created_at,
            "scope_boundary",
            "implementation_design_ready_manual_review_required" if ready else "blocked_missing_manual_approval_record",
            "critical",
            "Future seed-change code must be a separate reviewed change after this design.",
            "This checkpoint does not change the active seed.",
            NEXT_STEP if ready else "record_manual_approval_first",
        ),
        design_row(
            created_at,
            "active_seed_constant",
            "future_change_identified_not_applied",
            "critical",
            f"A future implementation may replace the active paper-live seed reference from {INCUMBENT_SEED} to {SELECTED_CANDIDATE}.",
            f"{INCUMBENT_SEED} remains active in this checkpoint.",
            "separate_code_change_required_to_switch_seed",
        ),
        design_row(
            created_at,
            "saved_output_contract",
            "future_saved_outputs_required",
            "high",
            "Future seed-change implementation must update saved monitoring/state summaries to show the new seed and retain prior QQQ100 context.",
            "No saved-output schema is changed beyond this design report.",
            "define_seed_state_summary_update_before_implementation",
        ),
        design_row(
            created_at,
            "preview_boundary",
            "action_preview_not_added",
            "critical",
            "Future action preview work must remain non-executable and must not include order side, quantity, type, account, or secret fields.",
            "No preview/action implementation is added here.",
            "separate_preview_schema_review_after_seed_switch_design",
        ),
        design_row(
            created_at,
            "broker_boundary",
            "no_broker_read_in_design",
            "critical",
            "Any later broker comparison must stay explicit, read-only, and separately confirmed.",
            "This checkpoint does not call Alpaca or read positions.",
            "keep_broker_reads_separate_and_confirmed",
        ),
        design_row(
            created_at,
            "execution_boundary",
            "all_execution_approvals_false",
            "critical",
            "The design cannot approve paper execution, live trading, follow-up orders, repeat orders, or scheduling.",
            "All execution and scheduling flags stay false.",
            "manual_review_before_any_seed_change_code_change",
        ),
    ]


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    design_rows: list[dict[str, Any]],
    final_status: str,
) -> list[dict[str, Any]]:
    ready = final_status == FINAL_STATUS
    rows = [
        ("final_design_status", final_status, "Seed-change implementation design checkpoint status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current active paper-live seed remains unchanged."),
        ("candidate_seed", SELECTED_CANDIDATE, "Candidate named for a future separate seed-change implementation."),
        (
            "implementation_scope",
            "design_seed_change_implementation_without_execution" if ready else "blocked_missing_manual_approval_record",
            "Scope of this design checkpoint.",
        ),
        (
            "seed_change_decision",
            "seed_not_changed_qqq100_retained_until_separate_implementation",
            "No seed switch is implemented by this command.",
        ),
        ("implementation_status", "implementation_design_created_no_code_change_applied" if ready else "implementation_design_blocked", "No runtime seed-switch implementation is added."),
        ("source_manual_approval_status", summary_value(inputs["manual_approval_summary"], "final_manual_approval_status") or "missing_manual_approval_record", "Saved manual approval status."),
        ("source_manual_approval_scope", summary_value(inputs["manual_approval_summary"], "manual_approval_scope") or "missing_manual_approval_scope", "Saved manual approval scope."),
        ("design_row_count", str(len(design_rows)), "Saved design row count."),
        ("largest_blocker", "separate_seed_change_code_change_required" if ready else "missing_manual_approval_record", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if ready else "record_manual_approval_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        (
            "manual_approval_summary_input",
            f"{INPUT_FILES['manual_approval_summary']}; rows={len(inputs['manual_approval_summary'])}",
            "Saved manual approval summary row count.",
        ),
        ("seed_changed_now", "false", "This design report does not change the seed."),
        ("implementation_added_now", "false", "This checkpoint does not add preview/action/execution implementation."),
        ("broker_read_now", "false", "This checkpoint reads saved outputs only and does not call Alpaca."),
    ]
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("seed_change_not_implemented", "blocked", "critical", "QQQ100 remains active until a separate implementation code change.", "separate_seed_change_code_change_required"),
        ("preview_implementation_not_added", "blocked", "critical", "No action preview implementation is added.", "separate_preview_schema_review_required"),
        ("order_instructions_not_allowed", "blocked", "critical", "No executable order instructions are created.", "future_preview_schema_must_stay_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("manual_approval_record_missing", "blocked", "critical", "Saved manual approval record is missing or not ready.", "record_manual_approval_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth seed-change implementation design complete. Design only; no seed change or execution approved.",
        f"final_design_status={summary_value(summary_rows, 'final_design_status')}",
        f"implementation_scope={summary_value(summary_rows, 'implementation_scope')}",
        f"seed_change_decision={summary_value(summary_rows, 'seed_change_decision')}",
        f"implementation_status={summary_value(summary_rows, 'implementation_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_design={output_paths['design']}",
        "seed_changed=false; active_seed_changed=false; qqq100_displacement_approved=false; vol_targeted_seed_approved=false; action_preview_added=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def design_row(
    created_at: str,
    item: str,
    status: str,
    risk: str,
    requirement: str,
    boundary: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "design_item": item,
        "design_status": status,
        "risk_level": risk,
        "requirement": requirement,
        "implementation_boundary": boundary,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


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
