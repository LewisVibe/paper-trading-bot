"""Saved-data-only defensive allocation risk preview."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFENSIVE_ALLOCATION_RISK_COLUMNS = [
    "created_at",
    "risk_check",
    "component",
    "risk_status",
    "severity",
    "source",
    "finding",
    "blocker",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]

EXPECTED_COMPONENT_LABELS = {
    "monthly_etf_momentum_rotation": "lead_reference",
    "volatility_managed_dual_momentum_etf": "secondary_check_split_sensitive",
    "etf_breadth_regime_allocation": "robust_diagnostic_filter_not_strategy",
    "adaptive_risk_on_off_momentum": "secondary_complex_candidate",
    "short_research": "paused_not_useful",
    "execution_state": "blocked_no_execution_approval",
}

ORDER_INSTRUCTION_COLUMNS = {
    "side",
    "quantity",
    "order_type",
    "order_id",
    "target_order",
    "submit" + "_order",
}


@dataclass
class DefensiveAllocationRiskPreviewResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_defensive_allocation_risk_preview(
    data_dir: Path | str = "data",
    created_at: str | None = None,
) -> DefensiveAllocationRiskPreviewResult:
    data_path = Path(data_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    input_path = data_path / "defensive_allocation_preview.csv"
    fieldnames, allocation_rows = read_allocation_preview(input_path)
    rows = build_risk_rows(created, input_path, fieldnames, allocation_rows)
    output_path = data_path / "defensive_allocation_risk_preview.csv"
    write_rows(output_path, rows)
    return DefensiveAllocationRiskPreviewResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, input_path, output_path),
    )


def build_risk_rows(
    created_at: str,
    input_path: Path,
    fieldnames: list[str],
    allocation_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    if not input_path.exists():
        return [
            risk_row(
                created_at,
                "input_file_available",
                "defensive_allocation_preview",
                "missing_input",
                "blocked",
                input_path,
                "Saved defensive allocation preview input is missing.",
                True,
                "Run python bot.py --defensive-allocation-preview before this risk preview.",
            )
        ]

    by_component = {row.get("component", ""): row for row in allocation_rows}
    rows = [
        risk_row(
            created_at,
            "input_file_available",
            "defensive_allocation_preview",
            "pass",
            "info",
            input_path,
            f"Saved input file was read with {len(allocation_rows)} rows.",
            False,
            "Continue reviewing saved-data-only risk checks.",
        ),
        expected_components_present_row(created_at, input_path, by_component),
        no_execution_approved_rows(created_at, input_path, allocation_rows),
        no_order_instruction_columns(created_at, input_path, fieldnames),
        component_label_row(
            created_at,
            input_path,
            by_component,
            "lead_candidate_research_only",
            "monthly_etf_momentum_rotation",
            "lead_reference",
            "pass",
            "info",
            "Lead defensive candidate is a research reference only, not execution-ready.",
            "Keep as research reference; a separate decision report would still be non-execution.",
        ),
        component_label_row(
            created_at,
            input_path,
            by_component,
            "vol_managed_split_sensitive",
            "volatility_managed_dual_momentum_etf",
            "secondary_check_split_sensitive",
            "warning",
            "medium",
            "Vol-managed ETF remains split-sensitive and should be compared against ETF rotation.",
            "Require comparison context before any defensive allocation decision report.",
        ),
        component_label_row(
            created_at,
            input_path,
            by_component,
            "breadth_diagnostic_only",
            "etf_breadth_regime_allocation",
            "robust_diagnostic_filter_not_strategy",
            "warning",
            "medium",
            "ETF breadth is diagnostic/filter context only, not a standalone allocation strategy.",
            "Use as context only; do not treat it as a strategy allocation.",
        ),
        component_label_row(
            created_at,
            input_path,
            by_component,
            "adaptive_secondary_complex",
            "adaptive_risk_on_off_momentum",
            "secondary_complex_candidate",
            "warning",
            "medium",
            "Adaptive momentum remains secondary/complex and should be monitored only.",
            "Compare turnover, cost burden, and portfolio role before reconsidering.",
        ),
        component_label_row(
            created_at,
            input_path,
            by_component,
            "short_research_excluded",
            "short_research",
            "paused_not_useful",
            "pass",
            "info",
            "Short research is excluded and remains paused/not useful.",
            "Do not reopen short research without a new fixed research hypothesis.",
        ),
        component_label_row(
            created_at,
            input_path,
            by_component,
            "execution_gate_blocked",
            "execution_state",
            "blocked_no_execution_approval",
            "blocked",
            "high",
            "Execution state remains blocked with no execution approval.",
            "Resolve all preview, consensus, risk, kill-switch, and explicit confirmation requirements before any execution discussion.",
        ),
    ]
    rows.append(decision_report_prerequisites_row(created_at, input_path, rows))
    return rows


def expected_components_present_row(
    created_at: str,
    input_path: Path,
    by_component: dict[str, dict[str, str]],
) -> dict[str, Any]:
    missing = [component for component in EXPECTED_COMPONENT_LABELS if component not in by_component]
    if missing:
        return risk_row(
            created_at,
            "expected_components_present",
            "defensive_allocation_preview",
            "blocked",
            "high",
            input_path,
            "Missing expected components: " + ", ".join(missing),
            True,
            "Rebuild python bot.py --defensive-allocation-preview from a complete defensive research state report.",
        )
    return risk_row(
        created_at,
        "expected_components_present",
        "defensive_allocation_preview",
        "pass",
        "info",
        input_path,
        "All expected defensive allocation preview components are present.",
        False,
        "Continue reviewing component-specific risk checks.",
    )


def no_execution_approved_rows(
    created_at: str,
    input_path: Path,
    allocation_rows: list[dict[str, str]],
) -> dict[str, Any]:
    approved = [
        row.get("component", "unknown")
        for row in allocation_rows
        if normalize_bool_text(row.get("execution_approved")) != "false"
    ]
    if approved:
        return risk_row(
            created_at,
            "no_execution_approved_rows",
            "defensive_allocation_preview",
            "fail",
            "critical",
            input_path,
            "Rows with execution_approved not equal to False: " + ", ".join(approved),
            True,
            "Manually review the saved CSV before any further decision report work.",
        )
    return risk_row(
        created_at,
        "no_execution_approved_rows",
        "defensive_allocation_preview",
        "pass",
        "info",
        input_path,
        "All rows have execution_approved=False.",
        False,
        "Keep execution approval false in all downstream previews.",
    )


def no_order_instruction_columns(
    created_at: str,
    input_path: Path,
    fieldnames: list[str],
) -> dict[str, Any]:
    found = sorted(ORDER_INSTRUCTION_COLUMNS.intersection(fieldnames))
    if found:
        return risk_row(
            created_at,
            "no_order_instruction_columns",
            "defensive_allocation_preview",
            "fail",
            "critical",
            input_path,
            "Order-instruction style columns found: " + ", ".join(found),
            True,
            "Remove order-instruction fields from the saved preview before continuing.",
        )
    return risk_row(
        created_at,
        "no_order_instruction_columns",
        "defensive_allocation_preview",
        "pass",
        "info",
        input_path,
        "No order-instruction style columns were found.",
        False,
        "Keep this preview free of order instructions.",
    )


def component_label_row(
    created_at: str,
    input_path: Path,
    by_component: dict[str, dict[str, str]],
    risk_check: str,
    component: str,
    expected_label: str,
    ok_status: str,
    ok_severity: str,
    ok_finding: str,
    required_next_step: str,
) -> dict[str, Any]:
    row = by_component.get(component)
    if not row:
        return risk_row(
            created_at,
            risk_check,
            component,
            "missing_input",
            "high",
            input_path,
            f"Expected component {component} was missing.",
            True,
            "Rebuild python bot.py --defensive-allocation-preview from complete saved inputs.",
        )
    actual_label = row.get("preview_label", "")
    if actual_label != expected_label:
        return risk_row(
            created_at,
            risk_check,
            component,
            "blocked",
            "high",
            input_path,
            f"Expected preview_label={expected_label}, got {actual_label or 'blank'}.",
            True,
            "Review defensive allocation preview before building a decision report.",
        )
    return risk_row(
        created_at,
        risk_check,
        component,
        ok_status,
        ok_severity,
        input_path,
        ok_finding,
        ok_status == "blocked",
        required_next_step,
    )


def decision_report_prerequisites_row(
    created_at: str,
    input_path: Path,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    blocking = [row for row in rows if bool_from_any(row.get("blocker"))]
    if blocking:
        return risk_row(
            created_at,
            "decision_report_prerequisites",
            "defensive_allocation_decision_report",
            "blocked",
            "high",
            input_path,
            "A future decision report would need to preserve no-execution status and address blockers/context first.",
            True,
            "Use this as a risk checkpoint only; do not proceed toward execution or promotion.",
        )
    return risk_row(
        created_at,
        "decision_report_prerequisites",
        "defensive_allocation_decision_report",
        "warning",
        "medium",
        input_path,
        "Saved preview is internally consistent, but a future decision report would still be research-only.",
        False,
        "A future decision report may summarize posture, but must not approve execution.",
    )


def risk_row(
    created_at: str,
    risk_check: str,
    component: str,
    risk_status: str,
    severity: str,
    source: Path,
    finding: str,
    blocker: bool,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "risk_check": risk_check,
        "component": component,
        "risk_status": risk_status,
        "severity": severity,
        "source": str(source),
        "finding": finding,
        "blocker": blocker,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def read_allocation_preview(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEFENSIVE_ALLOCATION_RISK_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEFENSIVE_ALLOCATION_RISK_COLUMNS})


def build_summary(rows: list[dict[str, Any]], input_path: Path, output_path: Path) -> list[str]:
    status_counts: dict[str, int] = {}
    blockers = 0
    for row in rows:
        status = str(row.get("risk_status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        if bool_from_any(row.get("blocker")):
            blockers += 1
    counts = ", ".join(f"{status}: {count}" for status, count in sorted(status_counts.items()))
    return [
        "DEFENSIVE ALLOCATION RISK PREVIEW. SAVED-DATA ONLY. NOT EXECUTION.",
        f"Input file path: {input_path}",
        f"Rows: {len(rows)}",
        "Risk status counts: " + counts,
        f"Blockers: {blockers}",
        f"Saved defensive allocation risk preview to {output_path}",
        "No strategy was promoted.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
    ]


def normalize_bool_text(value: Any) -> str:
    return str(value).strip().lower()


def bool_from_any(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return normalize_bool_text(value) == "true"
