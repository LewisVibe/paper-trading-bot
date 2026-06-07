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
