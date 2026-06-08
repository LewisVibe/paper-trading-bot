"""Preview-only promoted review refresh orchestration."""

from __future__ import annotations

import csv
import io
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from trading_bot.research.promoted_decision import read_csv_rows


PROMOTED_REVIEW_REFRESH_COLUMNS = [
    "created_at",
    "step_name",
    "command_or_report",
    "status",
    "output_path",
    "message",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class PromotedReviewRefreshResult:
    output_path: Path
    rows: list[dict[str, object]]
    summary_lines: list[str]
    status_code: int


@dataclass
class PromotedReviewStep:
    step_name: str
    command_or_report: str
    output_path: Path
    run: Callable[[], int]


def refresh_promoted_review(
    steps: list[PromotedReviewStep],
    decision_path: Path,
    output_path: Path = Path("data/promoted_review_refresh_summary.csv"),
    created_at: str | None = None,
) -> PromotedReviewRefreshResult:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for step in steps:
        rows.append(run_refresh_step(timestamp, step))
    write_promoted_review_refresh_summary(output_path, rows)
    status_code = 0 if all(row["status"] == "passed" for row in rows) else 1
    return PromotedReviewRefreshResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_promoted_review_refresh_summary(rows, decision_path, output_path),
        status_code=status_code,
    )


def run_refresh_step(created_at: str, step: PromotedReviewStep) -> dict[str, object]:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            status_code = step.run()
    except Exception as exc:
        return refresh_row(
            created_at,
            step,
            "failed",
            f"{type(exc).__name__}: {exc}",
        )
    captured_output = "\n".join(
        part.strip()
        for part in [stdout_buffer.getvalue(), stderr_buffer.getvalue()]
        if part.strip()
    )
    if status_code == 0:
        return refresh_row(created_at, step, "passed", "Step completed.")
    return refresh_row(
        created_at,
        step,
        "failed",
        clear_failure_message(captured_output or f"Step returned status code {status_code}."),
    )


def refresh_row(
    created_at: str,
    step: PromotedReviewStep,
    status: str,
    message: str,
) -> dict[str, object]:
    return {
        "created_at": created_at,
        "step_name": step.step_name,
        "command_or_report": step.command_or_report,
        "status": status,
        "output_path": str(step.output_path) if step.output_path else "",
        "message": single_line(message),
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_promoted_review_refresh_summary(
    rows: list[dict[str, object]],
    decision_path: Path,
    output_path: Path,
) -> list[str]:
    decision_rows = read_csv_rows(decision_path) if decision_path.exists() else []
    decision_counts = Counter(row.get("decision_state", "") or "blank" for row in decision_rows)
    execution_approved = any(is_truthy(row.get("execution_approved", "")) for row in decision_rows)
    lines = [
        "PROMOTED REVIEW REFRESH. PREVIEW ONLY. NOT EXECUTION.",
        "This command refreshes promoted review CSVs/displays only and does not approve execution.",
    ]
    for row in rows:
        suffix = f" -> {row['output_path']}" if row.get("output_path") else ""
        lines.append(f"{row['step_name']}: {row['status']}{suffix}")
        if row["status"] != "passed":
            lines.append(f"  {row['message']}")
    lines.extend(
        [
            "Decision-state counts: " + format_counts(decision_counts),
            (
                "WARNING: at least one row has execution_approved=True; manual review required."
                if execution_approved
                else "Execution approved: False for all rows."
            ),
            f"Saved promoted review refresh summary to {output_path}",
            "Warning: research_only=True, preview_only=True, and execution_approved=False for every summary row.",
        ]
    )
    return lines


def clear_failure_message(message: str) -> str:
    if "strategy_promotion_report.csv" in message:
        return (
            "Missing data/strategy_promotion_report.csv. Run these first: "
            "python bot.py --research-report; python bot.py --walk-forward-report; "
            "python bot.py --strategy-promotion-report."
        )
    return message


def write_promoted_review_refresh_summary(output_path: Path, rows: list[dict[str, object]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PROMOTED_REVIEW_REFRESH_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PROMOTED_REVIEW_REFRESH_COLUMNS})


def format_counts(counts: Counter[str]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))


def is_truthy(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def single_line(value: str) -> str:
    return " ".join(str(value).split())
