"""Saved-output quality gate for the volatility-targeted action preview.

This checkpoint reads saved action-preview CSVs only. It does not call Alpaca,
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
READY_STATUS = "vol_targeted_growth_action_preview_quality_gate_usable_manual_review_required"
INCOMPLETE_STATUS = "vol_targeted_growth_action_preview_quality_gate_incomplete_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_action_preview_quality_gate_blocked_manual_review_required"
NEXT_STEP = "manual_review_quality_gate_then_decide_broker_position_comparison_design"

OUTPUT_FILES = {
    "gate": Path("data/vol_targeted_growth_action_preview_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_action_preview_quality_gate_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_action_preview_quality_gate_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_action_preview_quality_gate_blockers.csv"),
}

INPUT_FILES = {
    "action_preview": Path("data/vol_targeted_growth_action_preview.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "action_preview_blockers": Path("data/vol_targeted_growth_action_preview_blockers.csv"),
    "active_seed_readiness_summary": Path("data/vol_targeted_growth_active_seed_readiness_summary.csv"),
}

FORBIDDEN_COLUMNS = {
    "side",
    "quantity",
    "order_qty",
    "order_quantity",
    "order_side",
    "order_type",
    "time_in_force",
    "account_id",
    "api_key",
    "webhook",
    "secret",
    "token",
    "order_id",
    "execution_instruction",
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "preview_only": True,
    "quality_gate_only": True,
    "action_preview_usable_for_manual_review": False,
    "broker_positions_compared": False,
    "current_positions_read": False,
    "order_instructions_created": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "preview_candidate_approved": False,
    "preview_implementation_approved": False,
    "paper_live_candidate_approved": False,
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
    "check_name",
    "status",
    "risk_level",
    "evidence_value",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthActionPreviewQualityGateResult:
    output_paths: dict[str, Path]
    gate_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_action_preview_quality_gate(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthActionPreviewQualityGateResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    gate_rows = build_gate_rows(created_at, inputs)
    final_status = determine_final_status(gate_rows)
    summary_rows = build_summary_rows(final_status, inputs, gate_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status, gate_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["gate"], GATE_COLUMNS, gate_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthActionPreviewQualityGateResult(
        output_paths=output_paths,
        gate_rows=gate_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_action_preview_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted growth action-preview quality gate is missing.",
            "Run `python bot.py --vol-targeted-growth-action-preview-quality-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth action-preview quality gate saved display. Saved-output only; no broker reads or orders approved.",
        f"final_quality_gate_status: {summary_value(rows, 'final_quality_gate_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"action_preview_row_count: {summary_value(rows, 'action_preview_row_count')}",
        f"quality_pass_count: {summary_value(rows, 'quality_pass_count')}",
        f"quality_warning_count: {summary_value(rows, 'quality_warning_count')}",
        f"quality_error_count: {summary_value(rows, 'quality_error_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "broker_positions_compared=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_gate_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    preview_rows = inputs["action_preview"]
    summary_rows = inputs["action_preview_summary"]
    columns = set(preview_rows[0].keys()) if preview_rows else set()
    forbidden_columns = sorted(FORBIDDEN_COLUMNS.intersection(columns))
    labels = {str(row.get("manual_review_label", "")) for row in preview_rows}
    exposure_statuses = {str(row.get("current_exposure_status", "")) for row in preview_rows}
    flag_errors = false_flag_errors(preview_rows)
    active_status = summary_value(inputs["active_seed_readiness_summary"], "final_active_seed_readiness_status")
    return [
        gate_row(
            created_at,
            "saved_action_preview_exists",
            "pass" if preview_rows else "error",
            "critical",
            f"rows={len(preview_rows)}",
            "Saved action-preview rows must exist before quality review.",
            "run_vol_targeted_growth_action_preview",
        ),
        gate_row(
            created_at,
            "selected_candidate_consistent",
            "pass" if all(row.get("selected_candidate") == SELECTED_CANDIDATE for row in preview_rows) and preview_rows else "error",
            "critical",
            candidate_values(preview_rows),
            "Every preview row should refer to the active volatility seed.",
            "regenerate_action_preview_from_current_seed",
        ),
        gate_row(
            created_at,
            "forbidden_order_columns_absent",
            "pass" if not forbidden_columns else "error",
            "critical",
            ";".join(forbidden_columns) if forbidden_columns else "none",
            "Action preview must not contain executable order/security columns.",
            "remove_forbidden_order_or_secret_fields",
        ),
        gate_row(
            created_at,
            "current_exposure_loudly_unknown",
            "pass" if exposure_statuses == {"current_exposure_not_read"} and preview_rows else "error",
            "high",
            ";".join(sorted(exposure_statuses)) if exposure_statuses else "none",
            "Saved action preview must not assume flat/aligned when broker positions have not been compared.",
            "keep_current_exposure_unknown_until_confirmed_broker_comparison",
        ),
        gate_row(
            created_at,
            "manual_review_labels_present",
            "pass" if labels == {"current_exposure_not_read_manual_review_required"} and preview_rows else "warning",
            "medium",
            ";".join(sorted(labels)) if labels else "none",
            "Rows should carry manual-review labels while current exposure is unknown.",
            "review_manual_labels_before_broker_comparison",
        ),
        gate_row(
            created_at,
            "approval_flags_false",
            "pass" if not flag_errors and preview_rows else "error",
            "critical",
            ";".join(flag_errors) if flag_errors else "all_false",
            "Execution, paper execution, scheduling, broker comparison, and order flags must stay false.",
            "restore_false_approval_flags",
        ),
        gate_row(
            created_at,
            "active_seed_readiness_present",
            "pass" if active_status == "vol_targeted_growth_active_seed_monitoring_ready_manual_review_required" else "warning",
            "medium",
            active_status or "missing_active_seed_readiness",
            "Active-seed readiness should be clean before treating action-preview rows as usable for manual review.",
            "refresh_active_seed_readiness",
        ),
        gate_row(
            created_at,
            "source_action_preview_status",
            "pass" if summary_value(summary_rows, "final_action_preview_status") == "vol_targeted_growth_action_preview_created_saved_output_only" else "warning",
            "medium",
            summary_value(summary_rows, "final_action_preview_status") or "missing_action_preview_status",
            "Saved action-preview summary should show the saved-output-only status.",
            "rerun_action_preview_saved_output_only",
        ),
    ]


def build_summary_rows(
    final_status: str,
    inputs: dict[str, list[dict[str, str]]],
    gate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    preview_rows = inputs["action_preview"]
    rows = [
        ("final_quality_gate_status", final_status, "Whether the saved action preview is usable for manual review only."),
        ("selected_candidate", SELECTED_CANDIDATE, "Active volatility-targeted seed under review."),
        ("action_preview_row_count", str(len(preview_rows)), "Saved action-preview row count."),
        ("quality_pass_count", str(count_status(gate_rows, "pass")), "Quality checks passed."),
        ("quality_warning_count", str(count_status(gate_rows, "warning")), "Quality checks with manual-review warnings."),
        ("quality_error_count", str(count_status(gate_rows, "error")), "Quality checks with blocking errors."),
        ("largest_blocker", largest_blocker(final_status), "Largest blocker before the next step."),
        ("recommended_next_step", NEXT_STEP, "Manual review is required before any broker-position comparison design."),
        ("execution_status", "execution_blocked", "Paper/live execution remains blocked."),
    ]
    return [summary_row(name, value, details, final_status) for name, value, details in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        (f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(("position_context_policy", "broker_positions_compared=false", "This quality gate does not read or compare broker positions."))
    rows.append(("order_instruction_policy", "order_instructions_created=false", "The saved action preview is not an order ticket."))
    return [evidence_row(name, value, details) for name, value, details in rows]


def build_blocker_rows(final_status: str, gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = [
        ("broker_position_comparison_not_completed", "blocked", "critical", "Current exposure has not been read or compared.", "Do not treat action-preview rows as executable."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, repeat/follow-up order, or scheduling is approved.", "Keep all approval flags false."),
        ("order_instructions_forbidden", "blocked", "critical", "Action preview rows must not contain order instruction fields.", "Keep order fields out of saved preview outputs."),
    ]
    for row in gate_rows:
        if row.get("status") == "error":
            blockers.insert(
                0,
                (
                    str(row.get("check_name")),
                    "blocked",
                    str(row.get("risk_level")),
                    str(row.get("interpretation")),
                    str(row.get("required_next_step")),
                ),
            )
    if final_status == INCOMPLETE_STATUS:
        blockers.insert(0, ("quality_gate_warnings_present", "manual_review_required", "medium", "One or more quality checks produced warnings.", NEXT_STEP))
    return [blocker_row(name, status, severity, details, next_step) for name, status, severity, details, next_step in blockers]


def determine_final_status(gate_rows: list[dict[str, Any]]) -> str:
    if any(row.get("status") == "error" for row in gate_rows):
        return BLOCKED_STATUS
    if any(row.get("status") == "warning" for row in gate_rows):
        return INCOMPLETE_STATUS
    return READY_STATUS


def false_flag_errors(rows: list[dict[str, str]]) -> list[str]:
    false_fields = [
        "broker_positions_compared",
        "current_positions_read",
        "order_instructions_created",
        "alpaca_called",
        "orders_created",
        "orders_submitted",
        "orders_cancelled",
        "orders_replaced",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "live_trading_approved",
        "followup_order_approved",
        "repeat_execution_approved",
    ]
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in false_fields:
            if field in row and str(row.get(field, "")).lower() != "false":
                errors.append(f"row_{index}:{field}")
    return errors


def candidate_values(rows: list[dict[str, str]]) -> str:
    values = sorted({str(row.get("selected_candidate", "")) for row in rows})
    return ";".join(values) if values else "none"


def count_status(rows: list[dict[str, Any]], status: str) -> int:
    return sum(1 for row in rows if row.get("status") == status)


def largest_blocker(final_status: str) -> str:
    if final_status == READY_STATUS:
        return "broker_position_comparison_not_completed"
    if final_status == INCOMPLETE_STATUS:
        return "quality_gate_warnings_require_manual_review"
    return "quality_gate_errors_block_next_step"


def gate_row(
    created_at: str,
    check_name: str,
    status: str,
    risk_level: str,
    evidence_value: str,
    interpretation: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "status": status,
        "risk_level": risk_level,
        "evidence_value": evidence_value,
        "interpretation": interpretation,
        "required_next_step": required_next_step,
        **SAFETY_FLAGS,
        "action_preview_usable_for_manual_review": status == "pass",
    }


def summary_row(name: str, value: str, details: str, final_status: str) -> dict[str, Any]:
    return {
        "summary_name": name,
        "summary_value": value,
        "details": details,
        **SAFETY_FLAGS,
        "action_preview_usable_for_manual_review": final_status == READY_STATUS,
    }


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
        "Volatility-targeted growth action-preview quality gate complete. Saved-output only; no broker reads, orders, or scheduling approved.",
        f"final_quality_gate_status={summary_value(summary_rows, 'final_quality_gate_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"action_preview_row_count={summary_value(summary_rows, 'action_preview_row_count')}",
        f"quality_pass_count={summary_value(summary_rows, 'quality_pass_count')}",
        f"quality_warning_count={summary_value(summary_rows, 'quality_warning_count')}",
        f"quality_error_count={summary_value(summary_rows, 'quality_error_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_gate={output_paths['gate']}",
        "broker_positions_compared=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
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
