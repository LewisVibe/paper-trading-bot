"""Saved-output QQQ100 paper-live evidence audit.

This module reads saved CSV artefacts only. It does not call Alpaca, read live
positions, refresh market data, create order instructions, submit/cancel/replace
orders, write SQLite, send alerts, schedule anything, or upgrade approvals.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

INPUT_FILES = {
    "paper_live_promotion_gate_summary": Path("data/paper_live_promotion_gate_summary.csv"),
    "paper_live_readiness_summary": Path("data/paper_live_readiness_summary.csv"),
    "paper_live_state_summary": Path("data/paper_live_state_summary.csv"),
    "qqq100_preview_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_action_preview_summary": Path("data/qqq100_action_preview_summary.csv"),
    "qqq100_paper_execution_result": Path("data/qqq100_paper_execution_result.csv"),
    "qqq100_paper_execution_summary": Path("data/qqq100_paper_execution_summary.csv"),
    "qqq100_paper_postcheck": Path("data/qqq100_paper_postcheck.csv"),
    "qqq100_paper_postcheck_summary": Path("data/qqq100_paper_postcheck_summary.csv"),
    "paper_execution_state_summary": Path("data/paper_execution_state_summary.csv"),
    "paper_execution_state_positions": Path("data/paper_execution_state_positions.csv"),
    "paper_execution_state_milestones": Path("data/paper_execution_state_milestones.csv"),
}

OUTPUT_FILES = {
    "audit": Path("data/paper_live_evidence_audit.csv"),
    "summary": Path("data/paper_live_evidence_audit_summary.csv"),
    "blockers": Path("data/paper_live_evidence_audit_blockers.csv"),
    "evidence": Path("data/paper_live_evidence_audit_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "preview_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    **SAFETY_FLAGS,
}

AUDIT_COLUMNS = [
    "check_name",
    "check_status",
    "file_name",
    "file_path",
    "field_name",
    "field_value",
    "exact_missing_item",
    "finding",
    "required_next_step",
    "research_only",
    "report_only",
    "preview_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "order_instructions_created",
    "alpaca_called",
    "positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_FLAGS.keys(),
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_status",
    "evidence_source",
    "details",
    *SAFETY_FLAGS.keys(),
]


@dataclass(frozen=True)
class PaperLiveEvidenceSnapshot:
    desired_state: str
    saved_current_position_state: str
    saved_current_position_quantity: str
    last_saved_qqq100_order_result: str
    current_alignment_state: str
    promotion_gate_status: str
    readiness_status: str
    exact_missing_items: tuple[str, ...]
    present_files: tuple[str, ...]
    missing_files: tuple[str, ...]
    complete_for_state_reconciliation: bool
    aligned_long_after_saved_fill: bool


@dataclass
class PaperLiveEvidenceAuditResult:
    output_paths: dict[str, Path]
    audit_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def load_saved_inputs(root_dir: Path | str = ".") -> dict[str, list[dict[str, Any]]]:
    root = Path(root_dir)
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def evaluate_paper_live_saved_evidence(
    root_dir: Path | str = ".",
    inputs: dict[str, list[dict[str, Any]]] | None = None,
) -> PaperLiveEvidenceSnapshot:
    raw_inputs = inputs if inputs is not None else load_saved_inputs(root_dir)
    saved_inputs = {name: raw_inputs.get(name, []) for name in INPUT_FILES}
    present_files = tuple(name for name, rows in saved_inputs.items() if rows)
    missing_files = tuple(name for name, rows in saved_inputs.items() if not rows)
    desired_state = detect_desired_state(saved_inputs)
    saved_position_state = detect_saved_position_state(saved_inputs)
    saved_position_quantity = detect_saved_position_quantity(saved_inputs)
    order_result = detect_order_result(saved_inputs)
    raw_alignment_state = detect_alignment_state(saved_inputs)
    alignment_state = normalize_alignment_state(raw_alignment_state, saved_position_quantity)
    promotion_status = summary_value(saved_inputs["paper_live_promotion_gate_summary"], "final_promotion_gate_status")
    readiness_status = summary_value(saved_inputs["paper_live_readiness_summary"], "final_readiness_status")
    exact_missing = list_missing_items(
        saved_inputs,
        desired_state,
        saved_position_state,
        saved_position_quantity,
        order_result,
        alignment_state,
    )
    aligned_long_after_saved_fill = (
        desired_state == "long"
        and saved_position_state == "paper_position_long"
        and saved_position_quantity == "1"
        and order_result == "filled"
        and alignment_state == "aligned_long"
    )
    return PaperLiveEvidenceSnapshot(
        desired_state=desired_state,
        saved_current_position_state=saved_position_state,
        saved_current_position_quantity=saved_position_quantity,
        last_saved_qqq100_order_result=order_result,
        current_alignment_state=alignment_state,
        promotion_gate_status=promotion_status or "unavailable",
        readiness_status=readiness_status or "unavailable",
        exact_missing_items=tuple(exact_missing),
        present_files=present_files,
        missing_files=missing_files,
        complete_for_state_reconciliation=not exact_missing,
        aligned_long_after_saved_fill=aligned_long_after_saved_fill,
    )


def generate_paper_live_evidence_audit(root_dir: Path | str = ".") -> PaperLiveEvidenceAuditResult:
    root = Path(root_dir)
    inputs = load_saved_inputs(root)
    snapshot = evaluate_paper_live_saved_evidence(root, inputs)
    audit_rows = build_audit_rows(inputs, snapshot)
    summary_rows = build_summary_rows(snapshot)
    blocker_rows = build_blocker_rows(snapshot)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["audit"], AUDIT_COLUMNS, audit_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveEvidenceAuditResult(
        output_paths=output_paths,
        audit_rows=audit_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_evidence_audit(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live evidence audit is missing.",
            "Run `python bot.py --paper-live-evidence-audit` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live evidence audit saved display. Report only; no execution approved.",
        f"final_evidence_audit_status: {summary_value(rows, 'final_evidence_audit_status')}",
        f"desired_state: {summary_value(rows, 'desired_state')}",
        f"saved_current_position_state: {summary_value(rows, 'saved_current_position_state')}",
        f"saved_current_position_quantity: {summary_value(rows, 'saved_current_position_quantity')}",
        f"last_saved_qqq100_order_result: {summary_value(rows, 'last_saved_qqq100_order_result')}",
        f"current_alignment_state: {summary_value(rows, 'current_alignment_state')}",
        f"exact_missing_saved_evidence: {summary_value(rows, 'exact_missing_saved_evidence')}",
        f"aligned_long_after_saved_fill: {summary_value(rows, 'aligned_long_after_saved_fill')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        "Warning: evidence reconciliation does not approve follow-up or repeat orders.",
    ]


def list_missing_items(
    inputs: dict[str, list[dict[str, Any]]],
    desired_state: str,
    saved_position_state: str,
    saved_position_quantity: str,
    order_result: str,
    alignment_state: str,
) -> list[str]:
    missing: list[str] = []
    required_files = [
        "qqq100_preview_signal",
        "qqq100_action_preview",
        "qqq100_paper_postcheck",
    ]
    for name in required_files:
        if not inputs[name]:
            missing.append(f"missing_file:{INPUT_FILES[name]}")
    if not inputs["qqq100_paper_execution_result"] and not inputs["paper_execution_state_milestones"]:
        missing.append("missing_file:data/qqq100_paper_execution_result.csv_or_data/paper_execution_state_milestones.csv")
    if desired_state == "unavailable":
        missing.append("missing_field:desired_position")
    if saved_position_state == "unavailable":
        missing.append("missing_field:position_status_or_current_position_status")
    if saved_position_quantity == "unavailable":
        missing.append("missing_field:position_quantity_abs_or_current_position_quantity_abs")
    if order_result == "unavailable":
        missing.append("missing_field:order_status_or_historical_order_status")
    if alignment_state == "unavailable":
        missing.append("missing_field:alignment_state")
    return missing


def detect_desired_state(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        first_nonempty(inputs["qqq100_preview_signal"], ["desired_position"])
        or summary_value(inputs["qqq100_action_preview_summary"], "desired_position")
        or first_nonempty(inputs["qqq100_action_preview"], ["desired_position"])
        or summary_value(inputs["paper_live_state_summary"], "desired_state")
        or "unavailable"
    )


def detect_saved_position_state(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        first_nonempty(inputs["qqq100_paper_postcheck"], ["position_status", "current_position_status"])
        or first_nonempty(inputs["qqq100_action_preview"], ["current_position_status"])
        or state_summary_position_part(inputs, 0)
        or "unavailable"
    )


def detect_saved_position_quantity(inputs: dict[str, list[dict[str, Any]]]) -> str:
    quantity = (
        first_nonempty(inputs["qqq100_paper_postcheck"], ["position_quantity_abs", "current_position_quantity_abs"])
    )
    if quantity:
        return normalize_quantity(quantity)
    return "unavailable"


def detect_order_result(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        first_nonempty(inputs["qqq100_paper_execution_result"], ["order_status", "decision_status"])
        or summary_value(inputs["qqq100_paper_execution_summary"], "order_status")
        or first_nonempty(inputs["paper_execution_state_milestones"], ["historical_order_status", "milestone_status"])
        or summary_value(inputs["paper_live_state_summary"], "last_saved_qqq100_order_result")
        or "unavailable"
    )


def detect_alignment_state(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        first_nonempty(inputs["qqq100_paper_postcheck"], ["alignment_state"])
        or first_nonempty(inputs["paper_execution_state_positions"], ["alignment_state"])
        or first_nonempty(inputs["qqq100_action_preview"], ["alignment_state", "non_executable_preview_action"])
        or summary_value(inputs["paper_execution_state_summary"], "qqq100_alignment_status")
        or summary_value(inputs["paper_live_state_summary"], "current_alignment_state")
        or "unavailable"
    )


def normalize_alignment_state(alignment_state: str, saved_position_quantity: str) -> str:
    if saved_position_quantity == "unavailable":
        return "qqq100_alignment_unverified_missing_saved_quantity"
    return alignment_state


def state_summary_position_part(inputs: dict[str, list[dict[str, Any]]], index: int) -> str:
    value = summary_value(inputs["paper_live_state_summary"], "saved_current_position_state")
    if not value:
        return ""
    parts = [part.strip() for part in value.split(";")]
    if index == 0:
        return parts[0]
    for part in parts[1:]:
        if part.startswith("quantity="):
            return part.removeprefix("quantity=").strip()
    return ""


def build_audit_rows(
    inputs: dict[str, list[dict[str, Any]]],
    snapshot: PaperLiveEvidenceSnapshot,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, path in INPUT_FILES.items():
        present = bool(inputs[name])
        rows.append(
            audit_row(
                f"file_{name}",
                "present" if present else "missing",
                name,
                str(path),
                "rows",
                str(len(inputs[name])),
                "none" if present else f"missing_file:{path}",
                "Saved evidence file presence check.",
                "Regenerate only with the matching safe report command if this evidence is required.",
            )
        )
    value_checks = [
        ("desired_state", snapshot.desired_state, "desired_position"),
        ("saved_current_position_state", snapshot.saved_current_position_state, "position_status_or_current_position_status"),
        ("saved_current_position_quantity", snapshot.saved_current_position_quantity, "position_quantity_abs_or_current_position_quantity_abs"),
        ("last_saved_qqq100_order_result", snapshot.last_saved_qqq100_order_result, "order_status_or_historical_order_status"),
        ("current_alignment_state", snapshot.current_alignment_state, "alignment_state"),
    ]
    for name, value, field in value_checks:
        rows.append(
            audit_row(
                f"field_{name}",
                "present" if value != "unavailable" else "missing",
                "saved_qqq100_evidence",
                "saved CSV evidence inventory",
                field,
                value,
                "none" if value != "unavailable" else f"missing_field:{field}",
                f"Resolved {name} from saved evidence.",
                "Review the exact missing saved field before manual discussion.",
            )
        )
    rows.append(
        audit_row(
            "reconciled_aligned_long_after_saved_fill",
            "pass" if snapshot.aligned_long_after_saved_fill else "manual_review",
            "saved_qqq100_evidence",
            "saved CSV evidence inventory",
            "desired/position/order/alignment",
            str(snapshot.aligned_long_after_saved_fill),
            "none" if snapshot.aligned_long_after_saved_fill else "state_not_reconciled_as_aligned_long_after_saved_fill",
            "Checks whether saved evidence agrees with QQQ100 long 1 after a filled saved order.",
            "Keep follow-up order approval false; review manually before any separate prompt.",
        )
    )
    return rows


def build_summary_rows(snapshot: PaperLiveEvidenceSnapshot) -> list[dict[str, Any]]:
    final_status = (
        "paper_live_saved_evidence_reconciled_manual_review_required"
        if snapshot.complete_for_state_reconciliation
        else "paper_live_saved_evidence_incomplete_manual_review_required"
    )
    missing = "; ".join(snapshot.exact_missing_items) if snapshot.exact_missing_items else "none"
    next_step = (
        "review_reconciled_saved_state_before_any_separate_followup_order_design"
        if snapshot.complete_for_state_reconciliation
        else "regenerate_or_review_exact_missing_saved_evidence_before_readiness_label"
    )
    values = [
        ("final_evidence_audit_status", final_status, "Saved evidence reconciliation status; manual review remains required."),
        ("active_paper_live_candidate_strategy", STRATEGY_NAME, "Only QQQ100 is audited."),
        ("active_ticker", TICKER, "Only QQQ is audited."),
        ("desired_state", snapshot.desired_state, "Saved desired state from QQQ100 evidence."),
        ("saved_current_position_state", snapshot.saved_current_position_state, "Saved position state only; no live position read."),
        ("saved_current_position_quantity", snapshot.saved_current_position_quantity, "Saved position quantity only; no live position read."),
        ("last_saved_qqq100_order_result", snapshot.last_saved_qqq100_order_result, "Saved QQQ100 order status only."),
        ("current_alignment_state", snapshot.current_alignment_state, "Saved QQQ100 alignment state only."),
        ("promotion_gate_status", snapshot.promotion_gate_status, "Saved promotion gate status if available."),
        ("readiness_status", snapshot.readiness_status, "Saved readiness status if available."),
        ("exact_missing_saved_evidence", missing, "Exact missing saved file or field list."),
        ("complete_for_state_reconciliation", str(snapshot.complete_for_state_reconciliation), "Completeness for report reconciliation only."),
        ("aligned_long_after_saved_fill", str(snapshot.aligned_long_after_saved_fill), "Saved evidence agreement only; not order approval."),
        ("manual_qqq100_paper_action_discussion_allowed", "False", "No follow-up paper action discussion is approved by this audit."),
        ("followup_or_repeat_paper_order_allowed", "False", "Follow-up/repeat paper orders are not approved."),
        ("recommended_next_step", next_step, "Next step remains manual review, not execution."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in values]


def build_blocker_rows(snapshot: PaperLiveEvidenceSnapshot) -> list[dict[str, Any]]:
    rows = [
        ("execution_not_approved", "blocked", "critical", "This audit does not approve execution.", "Use a separate explicit manual prompt before any future paper action."),
        ("paper_execution_not_approved", "blocked", "critical", "This audit does not approve paper execution.", "Do not run QQQ100 paper execution from this audit."),
        ("followup_order_not_approved", "blocked", "critical", "Follow-up or repeat paper orders remain unapproved.", "Design and review any follow-up action separately."),
        ("scheduling_not_approved", "blocked", "critical", "Scheduling remains unapproved.", "Do not schedule order-capable commands."),
        ("live_trading_not_approved", "blocked", "critical", "Live trading remains unapproved.", "Keep Alpaca paper-only."),
    ]
    for missing in snapshot.exact_missing_items:
        rows.append((missing, "blocked", "high", missing, "Regenerate or review the exact saved evidence item."))
    return [
        {
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for name, status, severity, details, next_step in rows
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {
            "evidence_name": name,
            "evidence_status": "present" if rows else "missing",
            "evidence_source": str(INPUT_FILES[name]),
            "details": "Saved CSV evidence presence check.",
            **SAFETY_FLAGS,
        }
        for name, rows in inputs.items()
    ]


def audit_row(
    check_name: str,
    status: str,
    file_name: str,
    file_path: str,
    field_name: str,
    field_value: str,
    missing_item: str,
    finding: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "check_name": check_name,
        "check_status": status,
        "file_name": file_name,
        "file_path": file_path,
        "field_name": field_name,
        "field_value": field_value,
        "exact_missing_item": missing_item,
        "finding": finding,
        "required_next_step": next_step,
        **ROW_SAFETY,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live evidence audit complete. Saved-output report only; no execution approved.",
        f"Final evidence audit status: {summary_value(summary_rows, 'final_evidence_audit_status')}",
        f"Desired state: {summary_value(summary_rows, 'desired_state')}",
        f"Saved current position: {summary_value(summary_rows, 'saved_current_position_state')} quantity={summary_value(summary_rows, 'saved_current_position_quantity')}",
        f"Last saved QQQ100 order result: {summary_value(summary_rows, 'last_saved_qqq100_order_result')}",
        f"Current alignment state: {summary_value(summary_rows, 'current_alignment_state')}",
        f"Exact missing saved evidence: {summary_value(summary_rows, 'exact_missing_saved_evidence')}",
        f"Aligned long after saved fill: {summary_value(summary_rows, 'aligned_long_after_saved_fill')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved audit/summary/blockers/evidence to {output_paths['audit']}; {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        "Warning: evidence reconciliation does not approve follow-up or repeat orders.",
    ]


def normalize_quantity(value: str) -> str:
    text = str(value).strip()
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        return str(int(number))
    return text


def first_nonempty(rows: list[dict[str, Any]], keys: list[str]) -> str:
    for row in rows:
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
    return ""


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
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
