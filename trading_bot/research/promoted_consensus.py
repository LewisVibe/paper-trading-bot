"""Research-only consensus preview for promoted strategy desired positions.

This module reads saved promoted strategy preview CSV files and summarizes
strategy agreement by ticker. It does not download market data, call Alpaca,
create orders, write SQLite trade logs, or send alerts.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROMOTED_CONSENSUS_COLUMNS = [
    "created_at",
    "ticker",
    "strategy_count",
    "long_votes",
    "flat_votes",
    "other_votes",
    "desired_positions",
    "strategies_long",
    "strategies_flat",
    "consensus_state",
    "execution_eligible",
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


def build_promoted_consensus_rows(
    preview_rows: list[dict[str, str]],
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    rows_by_ticker: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in preview_rows:
        ticker = row.get("ticker", "").upper()
        if ticker:
            rows_by_ticker[ticker].append(row)

    return [
        build_consensus_row(timestamp, ticker, ticker_rows)
        for ticker, ticker_rows in sorted(rows_by_ticker.items())
    ]


def build_consensus_row(
    created_at: str,
    ticker: str,
    ticker_rows: list[dict[str, str]],
) -> dict[str, Any]:
    strategy_count = len(ticker_rows)
    long_strategies = sorted(
        row.get("strategy_name", "")
        for row in ticker_rows
        if normalize_desired_position(row.get("desired_position", "")) == "long"
    )
    flat_strategies = sorted(
        row.get("strategy_name", "")
        for row in ticker_rows
        if normalize_desired_position(row.get("desired_position", "")) == "flat"
    )
    desired_positions = [
        normalize_desired_position(row.get("desired_position", ""))
        for row in ticker_rows
    ]
    long_votes = len(long_strategies)
    flat_votes = len(flat_strategies)
    other_votes = strategy_count - long_votes - flat_votes
    consensus_state, reason = classify_consensus_state(
        strategy_count,
        long_votes,
        flat_votes,
        other_votes,
    )

    return {
        "created_at": created_at,
        "ticker": ticker,
        "strategy_count": strategy_count,
        "long_votes": long_votes,
        "flat_votes": flat_votes,
        "other_votes": other_votes,
        "desired_positions": ",".join(desired_positions),
        "strategies_long": ",".join(long_strategies),
        "strategies_flat": ",".join(flat_strategies),
        "consensus_state": consensus_state,
        "execution_eligible": False,
        "reason": reason,
        "research_only": True,
        "preview_only": True,
    }


def normalize_desired_position(value: str) -> str:
    desired_position = str(value or "").strip().lower()
    if desired_position in {"long", "flat"}:
        return desired_position
    return desired_position or "missing"


def classify_consensus_state(
    strategy_count: int,
    long_votes: int,
    flat_votes: int,
    other_votes: int,
) -> tuple[str, str]:
    if strategy_count <= 0:
        return "no_supported_votes", "No promoted strategy rows were available."
    if other_votes == strategy_count:
        return "no_supported_votes", "No promoted strategy rows had supported desired positions."
    if other_votes > 0:
        return "unknown", "Unsupported or missing desired_position values require review."
    if long_votes == strategy_count:
        return "unanimous_long", "All promoted strategy rows desire long, but this remains research-only."
    if flat_votes == strategy_count:
        return "unanimous_flat", "All promoted strategy rows desire flat; no action is implied."
    if long_votes > 0 and flat_votes > 0:
        return "mixed_long_flat", "Promoted strategies disagree; review before any execution discussion."
    return "unknown", "Consensus state could not be classified."


def write_promoted_consensus_preview(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PROMOTED_CONSENSUS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PROMOTED_CONSENSUS_COLUMNS})


def build_promoted_consensus_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    states = Counter(str(row.get("consensus_state", "")) for row in rows)
    disagreement = [
        str(row.get("ticker", ""))
        for row in rows
        if row.get("consensus_state") == "mixed_long_flat"
    ]
    unanimous_long = [
        str(row.get("ticker", ""))
        for row in rows
        if row.get("consensus_state") == "unanimous_long"
    ]
    unanimous_flat = [
        str(row.get("ticker", ""))
        for row in rows
        if row.get("consensus_state") == "unanimous_flat"
    ]
    return [
        "Promoted strategy consensus preview",
        "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION.",
        "This report reads saved CSV files only and does not refresh market data, call Alpaca, or submit orders.",
        f"Rows: {len(rows)}",
        "Counts by consensus_state: " + format_counts(states),
        "Tickers with disagreement: " + format_tickers(disagreement),
        "Tickers unanimous long: " + format_tickers(unanimous_long),
        "Tickers unanimous flat: " + format_tickers(unanimous_flat),
        f"Saved promoted consensus preview to {output_path}",
    ]


def run_promoted_consensus_preview_files(
    preview_path: Path,
    output_path: Path,
) -> tuple[int, list[str]]:
    if not preview_path.exists():
        return (
            1,
            [
                "Promoted strategy consensus preview",
                "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION.",
                f"Missing promoted strategy preview file: {preview_path}",
                "Run this first:",
                "python bot.py --preview-promoted-strategies",
            ],
        )

    rows = build_promoted_consensus_rows(read_csv_rows(preview_path))
    write_promoted_consensus_preview(output_path, rows)
    return 0, build_promoted_consensus_summary(rows, output_path)


def format_counts(counts: Counter[str]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))


def format_tickers(tickers: list[str]) -> str:
    return ", ".join(sorted(ticker for ticker in tickers if ticker)) or "none"
