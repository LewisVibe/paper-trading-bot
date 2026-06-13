"""Static check for the manual paper-order smoke-test runbook."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNBOOK_PATH = Path("docs/PAPER_ORDER_SMOKE_TEST_RUNBOOK.md")
OUTPUT_PATH = Path("data/paper_order_smoke_test_runbook_check.csv")

FINAL_PASS = "runbook_check_ready_for_manual_review"
FINAL_REVIEW = "runbook_check_needs_manual_review"
FINAL_BLOCKED = "runbook_check_blocked"

REQUIRED_PHRASES = [
    "AAPL buy 1",
    "Before Market Open",
    "Near Or During US Regular Market Hours",
    "After A Separately Approved Tiny Manual Paper Order",
    "market_status=open",
    "live_preflight_ready_for_manual_confirmation",
    "Do not run an order outside market hours",
    "Do not submit any follow-up order without manual review",
    "execution_approved=false",
    "scheduling_approved=false",
    "followup_order_approved=false",
    "This is not strategy execution",
    "This is not automation",
    "This is not cron",
    "This is not live trading",
]

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "evidence_source",
    "details",
    "smoke_test_order_approved",
    "execution_approved",
    "scheduling_approved",
    "followup_order_approved",
    "runbook_check_status",
]


@dataclass
class PaperOrderSmokeTestRunbookCheckResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_order_smoke_test_runbook_check(root_dir: Path | str = ".") -> PaperOrderSmokeTestRunbookCheckResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    text = read_text(root / RUNBOOK_PATH)
    rows = [
        check_row(
            created_at,
            "runbook_exists",
            "pass" if text else "blocked_missing_runbook",
            "info" if text else "blocked",
            str(RUNBOOK_PATH),
            "Runbook exists." if text else "Runbook is missing.",
            FINAL_REVIEW,
        )
    ]
    for phrase in REQUIRED_PHRASES:
        present = phrase in text
        rows.append(
            check_row(
                created_at,
                "required_runbook_phrase",
                "pass" if present else "manual_review_required_missing_phrase",
                "info" if present else "warning",
                str(RUNBOOK_PATH),
                f"phrase={phrase}; present={present}",
                FINAL_REVIEW,
            )
        )
    final_status = choose_final_status(rows)
    rows.append(
        check_row(
            created_at,
            "final_runbook_check_status",
            final_status,
            "blocked" if final_status == FINAL_BLOCKED else ("warning" if final_status == FINAL_REVIEW else "info"),
            str(RUNBOOK_PATH),
            final_details(final_status, rows),
            final_status,
        )
    )
    output_path = root / OUTPUT_PATH
    write_rows(output_path, rows)
    return PaperOrderSmokeTestRunbookCheckResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows),
    )


def check_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    evidence_source: str,
    details: str,
    runbook_check_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "evidence_source": evidence_source,
        "details": details,
        "smoke_test_order_approved": False,
        "execution_approved": False,
        "scheduling_approved": False,
        "followup_order_approved": False,
        "runbook_check_status": runbook_check_status,
    }


def choose_final_status(rows: list[dict[str, Any]]) -> str:
    if any(row.get("severity") == "blocked" for row in rows):
        return FINAL_BLOCKED
    if any(row.get("severity") == "warning" for row in rows):
        return FINAL_REVIEW
    return FINAL_PASS


def final_details(final_status: str, rows: list[dict[str, Any]]) -> str:
    warnings = [row for row in rows if row.get("severity") == "warning"]
    return f"final_status={final_status}; manual_review_count={len(warnings)}."


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    final = next((row for row in rows if row.get("check_name") == "final_runbook_check_status"), {})
    counts = Counter(str(row.get("check_status")) for row in rows)
    return [
        "Paper-order smoke-test runbook check complete. Report-only; no order approved.",
        f"final_runbook_check_status: {final.get('check_status', 'unavailable')}",
        f"check_counts: {format_counts(counts)}",
        "smoke_test_order_approved=false",
        "execution_approved=false",
        "scheduling_approved=false",
        "followup_order_approved=false",
        f"Saved runbook check to {output_path}",
        "Warning: this summary does not print a pasteable paper-order command.",
    ]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def format_counts(counts: Counter[str]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
