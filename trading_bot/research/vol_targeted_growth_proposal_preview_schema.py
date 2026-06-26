"""Saved-output schema checkpoint for a volatility-targeted proposal preview.

This report defines the allowed shape of a future non-executable paper-live
proposal preview for the volatility-targeted growth candidate. It does not add
that preview implementation, call Alpaca, read positions, create order fields,
or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_proposal_preview_schema_ready_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_proposal_preview_schema_blocked_missing_design_checkpoint"
NEXT_STEP = "manual_review_schema_before_any_proposal_preview_implementation"

OUTPUT_FILES = {
    "schema": Path("data/vol_targeted_growth_proposal_preview_schema.csv"),
    "summary": Path("data/vol_targeted_growth_proposal_preview_schema_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_proposal_preview_schema_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_proposal_preview_schema_blockers.csv"),
}

INPUT_FILES = {
    "proposal_design_summary": Path("data/vol_targeted_growth_proposal_implementation_design_summary.csv"),
    "candidate_discussion_summary": Path("data/vol_targeted_growth_candidate_discussion_summary.csv"),
    "preview_signal_summary": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

ALLOWED_PREVIEW_FIELDS = [
    ("candidate_name", "strategy identity only"),
    ("incumbent_seed", "current QQQ100 seed boundary"),
    ("sleeve_name", "sleeve identity"),
    ("target_weight", "target allocation weight, not order quantity"),
    ("sleeve_status", "research or seed status"),
    ("volatility_target_pct", "volatility target setting"),
    ("volatility_window_days", "volatility lookback setting"),
    ("exposure_cap", "maximum preview exposure cap"),
    ("current_exposure_status", "unknown unless separately confirmed read-only"),
    ("manual_review_label", "human review label only"),
    ("blocker", "why no action is approved"),
    ("required_next_step", "next manual-review step"),
]

FORBIDDEN_PREVIEW_FIELDS = [
    "order_side",
    "order_quantity",
    "order_type",
    "limit_price",
    "time_in_force",
    "client_order_id",
    "order_id",
    "account_id",
    "api_key",
    "secret_key",
    "webhook",
    "token",
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "schema_only": True,
    "proposal_only": True,
    "preview_only": True,
    "proposal_preview_implementation_added": False,
    "action_preview_added": False,
    "order_instructions_created": False,
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
    "qqq100_displacement_approved": False,
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

SCHEMA_COLUMNS = [
    "created_at",
    "schema_item",
    "schema_status",
    "field_name",
    "field_policy",
    "field_purpose",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthProposalPreviewSchemaResult:
    output_paths: dict[str, Path]
    schema_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_proposal_preview_schema(root_dir: Path | str = ".") -> VolTargetedGrowthProposalPreviewSchemaResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    schema_rows = build_schema_rows(created_at, final_status)
    summary_rows = build_summary_rows(inputs, schema_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["schema"], SCHEMA_COLUMNS, schema_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthProposalPreviewSchemaResult(
        output_paths=output_paths,
        schema_rows=schema_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_proposal_preview_schema(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-proposal-preview-schema` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth proposal preview schema saved display. Schema only; no preview implementation or execution approval.",
        f"final_schema_status: {summary_value(rows, 'final_schema_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"allowed_field_count: {summary_value(rows, 'allowed_field_count')}",
        f"forbidden_field_count: {summary_value(rows, 'forbidden_field_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "proposal_preview_implementation_added=false; order_instructions_created=false; qqq100_displacement_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    design_status = summary_value(inputs["proposal_design_summary"], "final_design_status")
    if design_status == "vol_targeted_growth_proposal_implementation_design_ready_manual_review_required":
        return FINAL_STATUS
    return BLOCKED_STATUS


def build_schema_rows(created_at: str, final_status: str) -> list[dict[str, Any]]:
    rows = [
        schema_row(created_at, "schema_boundary", final_status, "schema_scope", "allowed", "Future preview may show review fields only; no executable order fields.", NEXT_STEP if final_status == FINAL_STATUS else "run_proposal_implementation_design_first"),
    ]
    for field_name, purpose in ALLOWED_PREVIEW_FIELDS:
        rows.append(schema_row(created_at, "allowed_preview_field", "allowed_non_executable_field", field_name, "allowed", purpose, "manual_review_field_before_implementation"))
    for field_name in FORBIDDEN_PREVIEW_FIELDS:
        rows.append(schema_row(created_at, "forbidden_preview_field", "forbidden_executable_or_secret_field", field_name, "forbidden", "Must not appear in a proposal preview output.", "keep_field_out_of_future_preview_schema"))
    rows.append(schema_row(created_at, "qqq100_boundary", "qqq100_displacement_not_approved", "qqq100_displacement_approved", "must_remain_false", "Future preview must not imply QQQ100 has been displaced.", "separate_seed_change_review_required"))
    return rows


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], schema_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("final_schema_status", final_status, "Whether saved design evidence supports this schema-only checkpoint."),
        ("selected_candidate", SELECTED_CANDIDATE, "Volatility-targeted candidate under discussion."),
        ("incumbent_seed", INCUMBENT_SEED, "QQQ100 remains the incumbent paper-live seed."),
        ("source_design_status", summary_value(inputs["proposal_design_summary"], "final_design_status") or "missing_proposal_design_status", "Saved proposal implementation design status."),
        ("allowed_field_count", str(len(ALLOWED_PREVIEW_FIELDS)), "Allowed non-executable future preview fields."),
        ("forbidden_field_count", str(len(FORBIDDEN_PREVIEW_FIELDS)), "Forbidden executable, account, or secret fields."),
        ("schema_row_count", str(len(schema_rows)), "Saved schema row count."),
        ("proposal_preview_implementation_status", "not_added", "This checkpoint defines schema only."),
        ("largest_blocker", "schema_ready_but_preview_implementation_not_added_or_approved" if final_status == FINAL_STATUS else "missing_proposal_implementation_design", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if final_status == FINAL_STATUS else "run_proposal_implementation_design_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("implementation_added_now", "false", "This checkpoint does not add proposal preview implementation."))
    rows.append(("broker_read_now", "false", "This checkpoint does not call Alpaca or read positions."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("proposal_preview_implementation_not_added", "blocked", "critical", "This command defines a schema only.", NEXT_STEP),
        ("order_fields_forbidden", "blocked", "critical", "Order side, quantity, order type, account, API key, webhook, token, and order ID fields are forbidden.", "keep_future_preview_non_executable"),
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent seed.", "separate_seed_change_review_required"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("proposal_implementation_design_missing", "blocked", "critical", "Saved proposal implementation design is missing or not ready.", "run_proposal_implementation_design_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth proposal preview schema complete. Schema only; no preview implementation, orders, or scheduling approved.",
        f"final_schema_status={summary_value(summary_rows, 'final_schema_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"incumbent_seed={summary_value(summary_rows, 'incumbent_seed')}",
        f"allowed_field_count={summary_value(summary_rows, 'allowed_field_count')}",
        f"forbidden_field_count={summary_value(summary_rows, 'forbidden_field_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_schema={output_paths['schema']}",
        "proposal_preview_implementation_added=false; order_instructions_created=false; qqq100_displacement_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def schema_row(created_at: str, item: str, status: str, field_name: str, policy: str, purpose: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "schema_item": item, "schema_status": status, "field_name": field_name, "field_policy": policy, "field_purpose": purpose, "required_next_step": next_step, **SAFETY_FLAGS}


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
