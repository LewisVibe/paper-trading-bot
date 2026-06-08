"""Saved-data-only defensive allocation decision report."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFENSIVE_ALLOCATION_DECISION_COLUMNS = [
    "created_at",
    "decision_area",
    "decision_label",
    "decision_status",
    "severity",
    "source",
    "finding",
    "blocker_count",
    "warning_count",
    "pass_count",
    "can_progress_to_execution_design",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]

ORDER_INSTRUCTION_COLUMNS = {
    "side",
    "quantity",
    "order_type",
    "order_id",
    "target_order",
    "submit" + "_order",
}


@dataclass
class DefensiveAllocationDecisionReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_defensive_allocation_decision_report(
    data_dir: Path | str = "data",
    created_at: str | None = None,
) -> DefensiveAllocationDecisionReportResult:
    data_path = Path(data_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    preview_path = data_path / "defensive_allocation_preview.csv"
    risk_path = data_path / "defensive_allocation_risk_preview.csv"
    preview_fields, preview_rows = read_csv_with_fields(preview_path)
    risk_fields, risk_rows = read_csv_with_fields(risk_path)
    rows = build_decision_rows(created, preview_path, risk_path, preview_fields, preview_rows, risk_fields, risk_rows)
    output_path = data_path / "defensive_allocation_decision_report.csv"
    write_rows(output_path, rows)
    return DefensiveAllocationDecisionReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, preview_path, risk_path, output_path),
    )


def build_decision_rows(
    created_at: str,
    preview_path: Path,
    risk_path: Path,
    preview_fields: list[str],
    preview_rows: list[dict[str, str]],
    risk_fields: list[str],
    risk_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    preview_missing = not preview_path.exists()
    risk_missing = not risk_path.exists()
    preview_order_columns = sorted(ORDER_INSTRUCTION_COLUMNS.intersection(preview_fields))
    risk_order_columns = sorted(ORDER_INSTRUCTION_COLUMNS.intersection(risk_fields))
    preview_bad_approval = rows_with_non_false_execution(preview_rows, "component")
    risk_bad_approval = rows_with_non_false_execution(risk_rows, "risk_check")
    blockers = [row for row in risk_rows if row.get("risk_status") == "blocked" or bool_from_any(row.get("blocker"))]
    warnings = [row for row in risk_rows if row.get("risk_status") == "warning"]
    passes = [row for row in risk_rows if row.get("risk_status") == "pass"]
    lead = find_row(preview_rows, "component", "monthly_etf_momentum_rotation")

    hard_blockers = (
        preview_missing
        or risk_missing
        or bool(preview_order_columns)
        or bool(risk_order_columns)
        or bool(preview_bad_approval)
        or bool(risk_bad_approval)
        or bool(blockers)
    )
    progress = False if hard_blockers or warnings else False
    if preview_missing or risk_missing:
        overall_label = "missing_input"
        overall_status = "missing_input"
        overall_finding = "Required saved defensive allocation preview/risk CSV input is missing."
    elif hard_blockers:
        overall_label = "blocked_not_ready_for_execution_design"
        overall_status = "blocked"
        overall_finding = "Defensive allocation cannot move toward execution design because saved blockers remain."
    elif warnings:
        overall_label = "review_required_not_execution"
        overall_status = "warning"
        overall_finding = "No hard blockers were found, but warnings require review and this remains non-executable."
    else:
        overall_label = "research_only_ready_for_decision_review"
        overall_status = "warning"
        overall_finding = "Saved inputs are internally consistent, but any future decision remains research-only."

    rows = [
        decision_row(
            created_at,
            "overall_decision",
            overall_label,
            overall_status,
            "high" if hard_blockers else "medium",
            f"{preview_path}; {risk_path}",
            overall_finding,
            len(blockers) + int(preview_missing) + int(risk_missing) + len(preview_order_columns) + len(risk_order_columns) + len(preview_bad_approval) + len(risk_bad_approval),
            len(warnings),
            len(passes),
            progress,
            "Next gate is paper kill-switch enforcement design/tests and defensive execution-readiness review, not execution.",
        ),
        lead_reference_row(created_at, preview_path, lead, len(blockers), len(warnings), len(passes)),
        preview_safety_row(
            created_at,
            preview_path,
            risk_path,
            preview_missing,
            risk_missing,
            preview_order_columns + risk_order_columns,
            preview_bad_approval + risk_bad_approval,
            len(blockers),
            len(warnings),
            len(passes),
        ),
        risk_context_row(created_at, risk_path, warnings, len(blockers), len(passes)),
        blocker_context_row(created_at, risk_path, blockers, len(warnings), len(passes)),
        decision_row(
            created_at,
            "next_gate",
            "kill_switch_and_execution_readiness_required",
            "blocked" if hard_blockers else "warning",
            "high",
            f"{preview_path}; {risk_path}",
            "Future work must address kill-switch enforcement, risk gates, explicit confirmation, and execution-readiness review before any execution design discussion.",
            len(blockers),
            len(warnings),
            len(passes),
            False,
            "Keep this decision report non-executable; run paper kill-switch and execution eligibility reviews before any future design step.",
        ),
    ]
    return rows


def lead_reference_row(
    created_at: str,
    preview_path: Path,
    lead: dict[str, str] | None,
    blocker_count: int,
    warning_count: int,
    pass_count: int,
) -> dict[str, Any]:
    if not lead:
        return decision_row(
            created_at,
            "lead_reference",
            "missing_input",
            "missing_input",
            "high",
            str(preview_path),
            "Lead defensive reference row was missing.",
            blocker_count + 1,
            warning_count,
            pass_count,
            False,
            "Rebuild python bot.py --defensive-allocation-preview before relying on a decision report.",
        )
    if lead.get("preview_label") == "lead_reference":
        return decision_row(
            created_at,
            "lead_reference",
            "lead_defensive_reference_identified",
            "pass",
            "info",
            str(preview_path),
            "monthly_etf_momentum_rotation is identified as the lead defensive research reference.",
            blocker_count,
            warning_count,
            pass_count,
            False,
            "Keep the lead reference research-only; this is not a promotion or execution approval.",
        )
    return decision_row(
        created_at,
        "lead_reference",
        "lead_reference_requires_review",
        "blocked",
        "high",
        str(preview_path),
        f"Lead row had unexpected preview_label={lead.get('preview_label', 'blank')}.",
        blocker_count + 1,
        warning_count,
        pass_count,
        False,
        "Review the allocation preview before continuing.",
    )


def preview_safety_row(
    created_at: str,
    preview_path: Path,
    risk_path: Path,
    preview_missing: bool,
    risk_missing: bool,
    order_columns: list[str],
    bad_approval_rows: list[str],
    blocker_count: int,
    warning_count: int,
    pass_count: int,
) -> dict[str, Any]:
    if preview_missing or risk_missing:
        return decision_row(
            created_at,
            "preview_safety",
            "missing_input",
            "missing_input",
            "high",
            f"{preview_path}; {risk_path}",
            "Preview safety could not be confirmed because saved input is missing.",
            blocker_count + 1,
            warning_count,
            pass_count,
            False,
            "Run both allocation preview and allocation risk preview before this decision report.",
        )
    if order_columns or bad_approval_rows:
        findings = []
        if order_columns:
            findings.append("order-instruction columns: " + ", ".join(order_columns))
        if bad_approval_rows:
            findings.append("non-False execution approval rows: " + ", ".join(bad_approval_rows))
        return decision_row(
            created_at,
            "preview_safety",
            "preview_safety_blocked",
            "blocked",
            "critical",
            f"{preview_path}; {risk_path}",
            "; ".join(findings),
            blocker_count + 1,
            warning_count,
            pass_count,
            False,
            "Manually review saved preview/risk CSVs before any further decision report work.",
        )
    return decision_row(
        created_at,
        "preview_safety",
        "preview_safe_non_executable",
        "pass",
        "info",
        f"{preview_path}; {risk_path}",
        "Saved preview/risk CSVs have no order-instruction columns and all execution_approved values are False.",
        blocker_count,
        warning_count,
        pass_count,
        False,
        "Keep downstream decision reporting non-executable.",
    )


def risk_context_row(
    created_at: str,
    risk_path: Path,
    warnings: list[dict[str, str]],
    blocker_count: int,
    pass_count: int,
) -> dict[str, Any]:
    if warnings:
        checks = ", ".join(row.get("risk_check", "unknown") for row in warnings)
        return decision_row(
            created_at,
            "risk_context",
            "warnings_require_review",
            "warning",
            "medium",
            str(risk_path),
            "Warnings require review: " + checks,
            blocker_count,
            len(warnings),
            pass_count,
            False,
            "Review warnings before any future defensive allocation decision report is treated as useful.",
        )
    return decision_row(
        created_at,
        "risk_context",
        "no_warning_rows_detected",
        "pass",
        "info",
        str(risk_path),
        "No warning rows were found in saved risk preview.",
        blocker_count,
        0,
        pass_count,
        False,
        "Continue to blocker review; execution approval remains false.",
    )


def blocker_context_row(
    created_at: str,
    risk_path: Path,
    blockers: list[dict[str, str]],
    warning_count: int,
    pass_count: int,
) -> dict[str, Any]:
    if blockers:
        checks = ", ".join(row.get("risk_check", "unknown") for row in blockers)
        return decision_row(
            created_at,
            "blocker_context",
            "blockers_prevent_execution_design",
            "blocked",
            "high",
            str(risk_path),
            "Blocking risk checks remain: " + checks,
            len(blockers),
            warning_count,
            pass_count,
            False,
            "Resolve blockers before any future execution-design discussion; do not approve execution.",
        )
    return decision_row(
        created_at,
        "blocker_context",
        "no_blockers_detected_not_execution",
        "warning",
        "medium",
        str(risk_path),
        "No blocker rows were found, but this report remains research-only and non-executable.",
        0,
        warning_count,
        pass_count,
        False,
        "Continue research review only; no execution approval is granted.",
    )


def decision_row(
    created_at: str,
    decision_area: str,
    decision_label: str,
    decision_status: str,
    severity: str,
    source: str,
    finding: str,
    blocker_count: int,
    warning_count: int,
    pass_count: int,
    can_progress_to_execution_design: bool,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "decision_area": decision_area,
        "decision_label": decision_label,
        "decision_status": decision_status,
        "severity": severity,
        "source": source,
        "finding": finding,
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "pass_count": pass_count,
        "can_progress_to_execution_design": can_progress_to_execution_design,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def read_csv_with_fields(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEFENSIVE_ALLOCATION_DECISION_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEFENSIVE_ALLOCATION_DECISION_COLUMNS})


def build_summary(rows: list[dict[str, Any]], preview_path: Path, risk_path: Path, output_path: Path) -> list[str]:
    overall = find_row(rows, "decision_area", "overall_decision") or {}
    return [
        "DEFENSIVE ALLOCATION DECISION REPORT. SAVED-DATA ONLY. NOT EXECUTION.",
        f"Input file paths: {preview_path}; {risk_path}",
        f"Overall decision: {overall.get('decision_label', 'unknown')}",
        f"Can progress to execution design: {overall.get('can_progress_to_execution_design', False)}",
        f"Saved defensive allocation decision report to {output_path}",
        "No strategy was promoted.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
    ]


def find_row(rows: list[dict[str, Any]], key: str, expected: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get(key) == expected:
            return row
    return None


def rows_with_non_false_execution(rows: list[dict[str, str]], label_key: str) -> list[str]:
    return [
        row.get(label_key, "unknown")
        for row in rows
        if str(row.get("execution_approved", "")).strip().lower() != "false"
    ]


def bool_from_any(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
