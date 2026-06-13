"""Quality report for saved project research state outputs."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research.monitoring_freshness import freshness_for_path


OUTPUT_PATH = Path("data/project_research_state_quality_report.csv")
INPUT_FILES = {
    "summary": Path("data/project_research_state_summary.csv"),
    "refresh": Path("data/project_research_state_refresh.csv"),
    "next_steps": Path("data/project_research_state_next_steps.csv"),
}

REQUIRED_SUMMARY_FIELDS = [
    "stock_etf_active_research_lead",
    "stock_etf_status_and_blocker",
    "crypto_research_lead",
    "crypto_status_and_blockers",
    "recommended_next_step",
]

QUALITY_COLUMNS = [
    "check_name",
    "check_status",
    "severity",
    "details",
    "file_path",
    "freshness_label",
    "execution_approved",
    "scheduling_approved",
    "recommended_action",
]


@dataclass
class ProjectResearchStateQualityReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_project_research_state_quality_report(root_dir: Path | str = ".") -> ProjectResearchStateQualityReportResult:
    root = Path(root_dir)
    now = datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    saved = {name: read_csv(root / path) for name, path in INPUT_FILES.items()}

    for name, relative_path in INPUT_FILES.items():
        freshness = freshness_for_path(root, str(relative_path), now)
        exists = (root / relative_path).exists()
        if not exists:
            status = "blocked_missing"
            severity = "blocked"
            action = "run_project_research_state_refresh"
        elif freshness.label == "stale":
            status = "blocked_stale"
            severity = "blocked"
            action = "refresh_saved_project_research_state"
        elif freshness.label == "warning_stale":
            status = "warning_stale"
            severity = "warning"
            action = "consider_refreshing_saved_project_research_state"
        else:
            status = "pass"
            severity = "pass"
            action = "none"
        rows.append(
            quality_row(
                f"{name}_file_exists_and_freshness",
                status,
                severity,
                f"{relative_path} freshness={freshness.label}",
                str(relative_path),
                freshness.label,
                action,
            )
        )

    summary_rows = saved["summary"]
    for field in REQUIRED_SUMMARY_FIELDS:
        present = bool(summary_value(summary_rows, field))
        rows.append(
            quality_row(
                f"{field}_present",
                "pass" if present else "warning_missing_field",
                "pass" if present else "warning",
                f"{field} {'present' if present else 'missing'} in saved summary.",
                str(INPUT_FILES["summary"]),
                freshness_for_path(root, str(INPUT_FILES["summary"]), now).label,
                "none" if present else "rerun_project_research_state_refresh",
            )
        )

    all_rows = saved["summary"] + saved["refresh"] + saved["next_steps"]
    rows.append(approval_row("execution_approved_false", all_rows, "execution_approved"))
    rows.append(approval_row("scheduling_approved_false", all_rows, "scheduling_approved"))

    final_status = final_quality_status(rows)
    rows.append(
        quality_row(
            "final_quality_status",
            final_status,
            "blocked" if final_status == "blocked_manual_review" else ("warning" if final_status == "warning" else "pass"),
            "Final quality status for saved project research state. Report-only; no execution or scheduling approval.",
            "data/project_research_state_*.csv",
            "mixed",
            recommended_action(final_status),
        )
    )

    output_path = root / OUTPUT_PATH
    write_rows(output_path, rows)
    return ProjectResearchStateQualityReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows),
    )


def approval_row(check_name: str, rows: list[dict[str, Any]], column: str) -> dict[str, Any]:
    values = {str(row.get(column, "")).lower() for row in rows if str(row.get(column, "")) != ""}
    if not values:
        return quality_row(
            check_name,
            "warning_missing_approval_flags",
            "warning",
            f"{column} flags are missing from saved state rows.",
            "data/project_research_state_*.csv",
            "mixed",
            "rerun_project_research_state_refresh_and_review_flags",
        )
    if values == {"false"}:
        return quality_row(
            check_name,
            "pass",
            "pass",
            f"{column} is false for all saved state rows.",
            "data/project_research_state_*.csv",
            "mixed",
            "none",
        )
    return quality_row(
        check_name,
        "blocked_non_false_approval_flag",
        "blocked",
        f"{column} contains non-false values: {', '.join(sorted(values))}",
        "data/project_research_state_*.csv",
        "mixed",
        "manual_review_required",
    )


def final_quality_status(rows: list[dict[str, Any]]) -> str:
    statuses = {row.get("severity", "") for row in rows}
    if "blocked" in statuses:
        return "blocked_manual_review"
    if "warning" in statuses:
        return "warning"
    return "pass"


def recommended_action(status: str) -> str:
    if status == "blocked_manual_review":
        return "refresh_or_review_saved_project_research_state"
    if status == "warning":
        return "consider_refreshing_saved_project_research_state"
    return "none"


def quality_row(
    check_name: str,
    check_status: str,
    severity: str,
    details: str,
    file_path: str,
    freshness_label: str,
    recommended: str,
) -> dict[str, Any]:
    return {
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "details": details,
        "file_path": file_path,
        "freshness_label": freshness_label,
        "execution_approved": False,
        "scheduling_approved": False,
        "recommended_action": recommended,
    }


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    status_counts = Counter(str(row.get("check_status", "")) for row in rows)
    severity_counts = Counter(str(row.get("severity", "")) for row in rows)
    final_row = next((row for row in rows if row.get("check_name") == "final_quality_status"), {})
    return [
        "Project research-state quality report complete. Report-only; execution_approved=False; scheduling_approved=False.",
        f"check_status_counts: {format_counts(status_counts)}",
        f"severity_counts: {format_counts(severity_counts)}",
        f"final_quality_status: {final_row.get('check_status', 'unavailable')}",
        f"recommended_action: {final_row.get('recommended_action', 'unavailable')}",
        f"Saved quality report to {output_path}",
        "Warning: this quality report does not refresh market data, approve execution, approve scheduling, or connect strategies to orders.",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("metric_name") == key or row.get("check_name") == key or row.get("strategy_name") == key:
            return str(row.get("metric_value", ""))
    return ""


def format_counts(counts: Counter[str]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUALITY_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
