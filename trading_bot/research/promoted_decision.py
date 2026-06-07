"""Research-only decision policy preview for promoted strategy reports.

This module combines saved promoted consensus, action, and risk CSV outputs into
a ticker-level policy judgement. It does not download market data, call Alpaca,
create orders, write SQLite trade logs, or send alerts.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROMOTED_DECISION_COLUMNS = [
    "created_at",
    "ticker",
    "consensus_state",
    "long_votes",
    "flat_votes",
    "risk_status_summary",
    "action_summary",
    "decision_state",
    "execution_approved",
    "reason",
    "research_only",
    "preview_only",
]

PROMOTED_DECISION_DISPLAY_COLUMNS = [
    "ticker",
    "consensus_state",
    "long_votes",
    "flat_votes",
    "risk_status_summary",
    "action_summary",
    "decision_state",
    "execution_approved",
    "reason",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [
            row
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def build_promoted_decision_rows(
    consensus_rows: list[dict[str, str]],
    action_rows: list[dict[str, str]],
    risk_rows: list[dict[str, str]],
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    actions_by_ticker = group_rows_by_ticker(action_rows)
    risks_by_ticker = group_rows_by_ticker(risk_rows)
    return [
        build_decision_row(
            timestamp,
            consensus_row,
            actions_by_ticker.get(consensus_row.get("ticker", "").upper(), []),
            risks_by_ticker.get(consensus_row.get("ticker", "").upper(), []),
        )
        for consensus_row in consensus_rows
        if consensus_row.get("ticker", "").strip()
    ]


def group_rows_by_ticker(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        ticker = row.get("ticker", "").upper()
        if ticker:
            grouped[ticker].append(row)
    return grouped


def build_decision_row(
    created_at: str,
    consensus_row: dict[str, str],
    action_rows: list[dict[str, str]],
    risk_rows: list[dict[str, str]],
) -> dict[str, Any]:
    ticker = consensus_row.get("ticker", "").upper()
    consensus_state = consensus_row.get("consensus_state", "")
    long_votes = consensus_row.get("long_votes", "")
    flat_votes = consensus_row.get("flat_votes", "")
    risk_statuses = sorted({row.get("risk_status", "") for row in risk_rows if row.get("risk_status", "")})
    actions = sorted({row.get("preview_action", "") for row in action_rows if row.get("preview_action", "")})
    risk_status_summary = ",".join(risk_statuses) if risk_statuses else "missing"
    action_summary = ",".join(actions) if actions else "missing"
    decision_state, reason = classify_decision_state(consensus_state, risk_statuses, actions)

    return {
        "created_at": created_at,
        "ticker": ticker,
        "consensus_state": consensus_state,
        "long_votes": long_votes,
        "flat_votes": flat_votes,
        "risk_status_summary": risk_status_summary,
        "action_summary": action_summary,
        "decision_state": decision_state,
        "execution_approved": False,
        "reason": reason,
        "research_only": True,
        "preview_only": True,
    }


def classify_decision_state(
    consensus_state: str,
    risk_statuses: list[str],
    actions: list[str],
) -> tuple[str, str]:
    if not consensus_state or consensus_state in {"unknown", "no_supported_votes"} or not risk_statuses or not actions:
        return "unknown", "Missing or unsupported saved preview inputs require review."
    if consensus_state == "mixed_long_flat":
        return "blocked_strategy_disagreement", "Promoted strategies disagree; do not discuss execution yet."
    if "blocked_for_review" in risk_statuses:
        return "blocked_risk_review", "Risk preview contains blocked_for_review rows."
    if consensus_state == "unanimous_flat":
        return "no_action_unanimous_flat", "All promoted strategies desire flat; no action is implied."
    if "warning" in risk_statuses:
        return "review_warning", "Risk preview contains warning rows; review before any execution discussion."
    if consensus_state == "unanimous_long":
        return "research_only_unanimous_long", "All promoted strategies desire long, but execution is not approved."
    return "unknown", "Saved preview inputs could not be classified."


def write_promoted_decision_preview(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PROMOTED_DECISION_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PROMOTED_DECISION_COLUMNS})


def build_promoted_decision_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    states = Counter(str(row.get("decision_state", "")) for row in rows)
    return [
        "Promoted strategy decision policy preview",
        "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION.",
        "This report reads saved CSV files only and does not refresh market data, call Alpaca, or submit orders.",
        f"Rows: {len(rows)}",
        "Counts by decision_state: " + format_counts(states),
        f"Saved promoted decision preview to {output_path}",
    ]


def build_show_promoted_decision_lines(input_path: Path, rows: list[dict[str, str]]) -> list[str]:
    decision_counts = Counter(row.get("decision_state", "") or "blank" for row in rows)
    execution_counts = Counter(row.get("execution_approved", "") or "blank" for row in rows)
    has_execution_approved = any(is_truthy(row.get("execution_approved", "")) for row in rows)
    final_line = (
        "WARNING: at least one row has execution_approved=True; manual review required."
        if has_execution_approved
        else "Execution approved: False for all rows."
    )
    return [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "This command only reads data/promoted_decision_preview.csv and does not refresh data, read positions, or submit orders.",
        f"Input file: {input_path}",
        f"Rows: {len(rows)}",
        "",
        "Count by decision_state:",
        *_format_display_counts(decision_counts),
        "",
        "Count by execution_approved:",
        *_format_display_counts(execution_counts),
        "",
        *_format_promoted_decision_table(rows),
        "",
        final_line,
    ]


def build_missing_promoted_decision_lines(input_path: Path) -> list[str]:
    return [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "This command only reads data/promoted_decision_preview.csv and does not refresh data, read positions, or submit orders.",
        f"Missing promoted decision preview file: {input_path}",
        "Run these first:",
        "python bot.py --promoted-consensus-preview",
        "python bot.py --promoted-risk-preview",
        "python bot.py --promoted-decision-preview",
        "Then rerun: python bot.py --show-promoted-decision",
    ]


def show_promoted_decision_file(input_path: Path) -> tuple[int, list[str]]:
    if not input_path.exists():
        return 1, build_missing_promoted_decision_lines(input_path)
    return 0, build_show_promoted_decision_lines(input_path, read_csv_rows(input_path))


def run_promoted_decision_preview_files(
    consensus_path: Path,
    action_path: Path,
    risk_path: Path,
    output_path: Path,
) -> tuple[int, list[str]]:
    missing = [
        path
        for path in [consensus_path, action_path, risk_path]
        if not path.exists()
    ]
    if missing:
        return (
            1,
            [
                "Promoted strategy decision policy preview",
                "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION.",
                "Missing required saved CSV file(s): " + ", ".join(str(path) for path in missing),
                "Run these first:",
                "python bot.py --promoted-consensus-preview",
                "python bot.py --preview-promoted-actions",
                "python bot.py --promoted-risk-preview",
            ],
        )

    rows = build_promoted_decision_rows(
        read_csv_rows(consensus_path),
        read_csv_rows(action_path),
        read_csv_rows(risk_path),
    )
    write_promoted_decision_preview(output_path, rows)
    return 0, build_promoted_decision_summary(rows, output_path)


def format_counts(counts: Counter[str]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))


def _format_display_counts(counts: Counter[str]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {name}: {count}" for name, count in sorted(counts.items())]


def _format_promoted_decision_table(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["No promoted decision rows found."]
    display_rows = [
        {
            column: _truncate(str(row.get(column, "")), _column_width(column))
            for column in PROMOTED_DECISION_DISPLAY_COLUMNS
        }
        for row in rows
    ]
    widths = {
        column: min(
            _column_width(column),
            max(len(column), *(len(row[column]) for row in display_rows)),
        )
        for column in PROMOTED_DECISION_DISPLAY_COLUMNS
    }
    header = " | ".join(column.ljust(widths[column]) for column in PROMOTED_DECISION_DISPLAY_COLUMNS)
    separator = "-+-".join("-" * widths[column] for column in PROMOTED_DECISION_DISPLAY_COLUMNS)
    lines = [header, separator]
    for row in display_rows:
        lines.append(" | ".join(row[column].ljust(widths[column]) for column in PROMOTED_DECISION_DISPLAY_COLUMNS))
    return lines


def _column_width(column: str) -> int:
    widths = {
        "ticker": 8,
        "consensus_state": 22,
        "long_votes": 10,
        "flat_votes": 10,
        "risk_status_summary": 28,
        "action_summary": 34,
        "decision_state": 34,
        "execution_approved": 18,
        "reason": 64,
    }
    return widths.get(column, 20)


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return f"{value[: width - 3]}..."


def is_truthy(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}
