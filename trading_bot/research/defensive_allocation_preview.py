"""Saved-data-only defensive allocation posture preview."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFENSIVE_ALLOCATION_PREVIEW_COLUMNS = [
    "created_at",
    "component",
    "preview_category",
    "preview_label",
    "source",
    "desired_role",
    "current_state",
    "posture_signal",
    "confidence_label",
    "blocker_status",
    "interpretation",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


STATE_REPORT_PATH = Path("data") / "defensive_research_state_report.csv"
OUTPUT_PATH = Path("data") / "defensive_allocation_preview.csv"


PREVIEW_COMPONENTS = [
    {
        "component": "monthly_etf_momentum_rotation",
        "preview_category": "lead_defensive_candidate",
        "preview_label": "lead_reference",
        "desired_role": "primary_defensive_research_reference",
        "posture_signal": "lead_defensive_reference",
        "confidence_label": "highest_research_confidence",
        "blocker_status": "not_execution_approved",
        "interpretation": "Monthly ETF rotation is the lead defensive research reference, not an executable allocation.",
        "required_next_step": "Use as the defensive reference point; do not promote without a separate execution review.",
    },
    {
        "component": "volatility_managed_dual_momentum_etf",
        "preview_category": "secondary_defensive_check",
        "preview_label": "secondary_check_split_sensitive",
        "desired_role": "compare_against_rotation",
        "posture_signal": "supportive_secondary_check",
        "confidence_label": "medium_split_sensitive",
        "blocker_status": "split_sensitive_not_execution_approved",
        "interpretation": "Vol-managed ETF is a promising but split-sensitive comparison candidate.",
        "required_next_step": "Compare against ETF rotation before any strategy discussion.",
    },
    {
        "component": "etf_breadth_regime_allocation",
        "preview_category": "breadth_diagnostic_filter",
        "preview_label": "robust_diagnostic_filter_not_strategy",
        "desired_role": "market_state_filter_context",
        "posture_signal": "diagnostic_filter_context",
        "confidence_label": "diagnostic_confidence_only",
        "blocker_status": "diagnostic_only_not_execution_approved",
        "interpretation": "ETF breadth is useful as market-state context, not a standalone strategy.",
        "required_next_step": "Use breadth as a diagnostic/filter idea; compare against ETF rotation and vol-managed ETF.",
    },
    {
        "component": "adaptive_risk_on_off_momentum",
        "preview_category": "adaptive_candidate",
        "preview_label": "secondary_complex_candidate",
        "desired_role": "monitor_only",
        "posture_signal": "secondary_monitor_only",
        "confidence_label": "lower_complexity_burden",
        "blocker_status": "complexity_turnover_review_required",
        "interpretation": "Adaptive momentum remains secondary because complexity and turnover burden are higher.",
        "required_next_step": "Monitor only; compare turnover, cost burden, and portfolio role before reconsidering.",
    },
    {
        "component": "short_research",
        "preview_category": "short_research",
        "preview_label": "paused_not_useful",
        "desired_role": "excluded",
        "posture_signal": "excluded_paused",
        "confidence_label": "not_useful_paused",
        "blocker_status": "excluded",
        "interpretation": "Short research is paused/not useful and excluded from defensive allocation posture.",
        "required_next_step": "Do not add short preview or execution without a new fixed research hypothesis.",
    },
    {
        "component": "execution_state",
        "preview_category": "execution_gate",
        "preview_label": "blocked_no_execution_approval",
        "desired_role": "no_execution",
        "posture_signal": "blocked_no_execution",
        "confidence_label": "blocked",
        "blocker_status": "blocked_no_execution_approval",
        "interpretation": "Execution remains blocked; this preview does not grant approval.",
        "required_next_step": "Resolve preview, consensus, risk, kill-switch, and explicit confirmation requirements before any execution discussion.",
    },
]


@dataclass
class DefensiveAllocationPreviewResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_defensive_allocation_preview(
    data_dir: Path | str = "data",
    created_at: str | None = None,
) -> DefensiveAllocationPreviewResult:
    data_path = Path(data_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    source_path = data_path / "defensive_research_state_report.csv"
    state_rows = read_state_rows(source_path)
    rows = build_preview_rows(created, state_rows, source_path)
    output_path = data_path / "defensive_allocation_preview.csv"
    write_rows(output_path, rows)
    return DefensiveAllocationPreviewResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, source_path, output_path),
    )


def build_preview_rows(
    created_at: str,
    state_rows: list[dict[str, str]],
    source_path: Path,
) -> list[dict[str, Any]]:
    by_component = {row.get("component", ""): row for row in state_rows}
    return [
        build_component_row(created_at, config, by_component.get(config["component"]), source_path)
        for config in PREVIEW_COMPONENTS
    ]


def build_component_row(
    created_at: str,
    config: dict[str, str],
    state_row: dict[str, str] | None,
    source_path: Path,
) -> dict[str, Any]:
    if not state_row:
        return {
            "created_at": created_at,
            "component": config["component"],
            "preview_category": config["preview_category"],
            "preview_label": "missing_input",
            "source": str(source_path),
            "desired_role": config["desired_role"],
            "current_state": "missing_input",
            "posture_signal": "insufficient_data",
            "confidence_label": "not_available",
            "blocker_status": "missing_saved_state",
            "interpretation": "Saved defensive research state input was unavailable for this component.",
            "required_next_step": "Run python bot.py --defensive-research-state-report before relying on this preview.",
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
        }
    return {
        "created_at": created_at,
        "component": config["component"],
        "preview_category": config["preview_category"],
        "preview_label": config["preview_label"],
        "source": state_row.get("evidence_source") or str(source_path),
        "desired_role": config["desired_role"],
        "current_state": state_row.get("state_label") or "unknown",
        "posture_signal": config["posture_signal"],
        "confidence_label": config["confidence_label"],
        "blocker_status": config["blocker_status"],
        "interpretation": state_row.get("interpretation") or config["interpretation"],
        "required_next_step": state_row.get("required_next_step") or config["required_next_step"],
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def read_state_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEFENSIVE_ALLOCATION_PREVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEFENSIVE_ALLOCATION_PREVIEW_COLUMNS})


def build_summary(rows: list[dict[str, Any]], source_path: Path, output_path: Path) -> list[str]:
    labels = ", ".join(f"{row['component']}={row['preview_label']}" for row in rows)
    missing_count = sum(1 for row in rows if row.get("preview_label") == "missing_input")
    lines = [
        "DEFENSIVE ALLOCATION PREVIEW. PREVIEW ONLY. NOT EXECUTION.",
        f"Input file path: {source_path}",
        f"Rows: {len(rows)}",
        "Preview labels: " + labels,
    ]
    if missing_count:
        lines.append(
            "Missing saved defensive state input detected; run python bot.py --defensive-research-state-report first."
        )
    lines.extend(
        [
            f"Saved defensive allocation preview to {output_path}",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
        ]
    )
    return lines
