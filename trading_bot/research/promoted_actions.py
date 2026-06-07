"""Read-only action preview helpers for promoted strategies.

This module compares promoted-strategy desired positions with current position
state. It does not submit orders, cancel orders, mutate positions, write SQLite
trade logs, or send alerts.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from trading_bot.positions import POSITION_FLAT, POSITION_LONG, POSITION_SHORT, Position, format_decimal


PROMOTED_ACTION_COLUMNS = [
    "created_at",
    "strategy_name",
    "strategy_family",
    "ticker",
    "desired_position",
    "current_position",
    "current_quantity",
    "preview_action",
    "preview_quantity",
    "reason",
    "promotion_status",
    "required_next_step",
    "preview_only",
    "diagnostic_warning",
]

PROMOTED_ACTION_DISPLAY_COLUMNS = [
    "strategy_name",
    "ticker",
    "desired_position",
    "current_position",
    "current_quantity",
    "preview_action",
    "preview_quantity",
    "reason",
]

AVAILABLE_POSITION_SOURCES = {"alpaca_paper", "alpaca_paper_readonly"}


@dataclass
class PromotedActionPreviewResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def read_promoted_strategy_preview(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [
            row
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def read_promoted_action_preview(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [
            row
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def build_promoted_action_preview_rows(
    preview_rows: list[dict[str, str]],
    positions: dict[str, Position],
    position_source: str,
    default_quantity: Decimal,
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    rows = []
    for preview_row in preview_rows:
        ticker = str(preview_row.get("ticker", "")).upper()
        position = positions.get(ticker)
        current_available = position_source in AVAILABLE_POSITION_SOURCES and position is not None
        if position_source in AVAILABLE_POSITION_SOURCES and position is None:
            position = Position()
            current_available = True
        rows.append(
            build_promoted_action_preview_row(
                timestamp,
                preview_row,
                position,
                current_available,
                position_source,
                default_quantity,
            )
        )
    return rows


def build_promoted_action_preview_row(
    created_at: str,
    preview_row: dict[str, str],
    position: Position | None,
    current_available: bool,
    position_source: str,
    default_quantity: Decimal,
) -> dict[str, Any]:
    desired_position = str(preview_row.get("desired_position", "")).lower()
    if not current_available or position is None:
        preview_action = "position_unavailable"
        current_position = "unavailable"
        current_quantity = ""
        preview_quantity = ""
        reason = f"Current paper position unavailable: {position_source}."
        diagnostic_warning = reason
    else:
        current_position = position.state
        current_quantity = format_decimal(position.abs_quantity)
        preview_action, preview_quantity, reason, diagnostic_warning = decide_promoted_preview_action(
            desired_position,
            position,
            default_quantity,
        )

    return {
        "created_at": created_at,
        "strategy_name": preview_row.get("strategy_name", ""),
        "strategy_family": preview_row.get("strategy_family", ""),
        "ticker": preview_row.get("ticker", ""),
        "desired_position": desired_position,
        "current_position": current_position,
        "current_quantity": current_quantity,
        "preview_action": preview_action,
        "preview_quantity": preview_quantity,
        "reason": reason,
        "promotion_status": preview_row.get("promotion_status", ""),
        "required_next_step": preview_row.get("required_next_step", ""),
        "preview_only": True,
        "diagnostic_warning": diagnostic_warning,
    }


def decide_promoted_preview_action(
    desired_position: str,
    position: Position,
    default_quantity: Decimal,
) -> tuple[str, str, str, str]:
    if position.state == POSITION_SHORT:
        return (
            "unsupported_short_position_preview",
            "",
            "Current position is short; promoted strategy previews are long-only.",
            "Short position requires manual review.",
        )

    if desired_position == POSITION_LONG:
        if position.state == POSITION_FLAT:
            return (
                "would_open_long",
                format_decimal(default_quantity),
                "Desired long and current position is flat.",
                "",
            )
        if position.state == POSITION_LONG:
            return (
                "no_action_already_long",
                "0",
                "Desired long and current position is already long.",
                "",
            )

    if desired_position == POSITION_FLAT:
        if position.state == POSITION_LONG:
            return (
                "would_close_long",
                format_decimal(position.abs_quantity),
                "Desired flat and current position is long.",
                "",
            )
        if position.state == POSITION_FLAT:
            return (
                "no_action_already_flat",
                "0",
                "Desired flat and current position is already flat.",
                "",
            )

    return (
        "position_unavailable",
        "",
        f"Desired position is not actionable in preview: {desired_position or 'unknown'}.",
        "Desired position is unsupported or unavailable.",
    )


def write_promoted_action_preview(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PROMOTED_ACTION_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PROMOTED_ACTION_COLUMNS})


def build_promoted_action_summary(rows: list[dict[str, Any]], position_source: str) -> list[str]:
    actions = sorted({str(row.get("preview_action", "")) for row in rows if row.get("preview_action")})
    return [
        "Promoted strategy action preview summary",
        "WARNING: This command is preview-only and does not approve execution.",
        f"Position source: {position_source}",
        f"Rows: {len(rows)}",
        f"Preview actions: {', '.join(actions) if actions else 'none'}",
    ]


def build_show_promoted_actions_lines(input_path: Path, rows: list[dict[str, str]]) -> list[str]:
    action_counts = Counter(row.get("preview_action", "") or "blank" for row in rows)
    desired_counts = Counter(row.get("desired_position", "") or "blank" for row in rows)
    warning_rows = [row for row in rows if (row.get("diagnostic_warning") or "").strip()]

    lines = [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "This command only reads data/promoted_strategy_action_preview.csv and does not refresh positions or submit orders.",
        f"Input file: {input_path}",
        f"Rows: {len(rows)}",
        "",
        "Count by preview_action:",
        *_format_counts(action_counts),
        "",
        "Count by desired_position:",
        *_format_counts(desired_counts),
        "",
        f"Diagnostic warning rows: {len(warning_rows)}",
    ]

    if warning_rows:
        for row in warning_rows[:10]:
            warning = row.get("diagnostic_warning", "")
            lines.append(
                f"- {row.get('strategy_name', '')} {row.get('ticker', '')}: {warning}"
            )
        if len(warning_rows) > 10:
            lines.append(f"- ... {len(warning_rows) - 10} more warning row(s)")

    lines.extend(["", *_format_action_table(rows)])
    return lines


def build_missing_promoted_actions_lines(input_path: Path) -> list[str]:
    return [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "This command only reads data/promoted_strategy_action_preview.csv and does not refresh positions or submit orders.",
        f"Missing promoted action preview file: {input_path}",
        "Run this first:",
        "python bot.py --preview-promoted-actions",
    ]


def show_promoted_actions_file(input_path: Path) -> tuple[int, list[str]]:
    if not input_path.exists():
        return 1, build_missing_promoted_actions_lines(input_path)
    return 0, build_show_promoted_actions_lines(input_path, read_promoted_action_preview(input_path))


def _format_counts(counts: Counter[str]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {name}: {count}" for name, count in sorted(counts.items())]


def _format_action_table(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["No promoted action rows found."]

    display_rows = [
        {column: _truncate(str(row.get(column, "")), _column_width(column)) for column in PROMOTED_ACTION_DISPLAY_COLUMNS}
        for row in rows
    ]
    widths = {
        column: min(
            _column_width(column),
            max(len(column), *(len(row[column]) for row in display_rows)),
        )
        for column in PROMOTED_ACTION_DISPLAY_COLUMNS
    }
    header = " | ".join(column.ljust(widths[column]) for column in PROMOTED_ACTION_DISPLAY_COLUMNS)
    separator = "-+-".join("-" * widths[column] for column in PROMOTED_ACTION_DISPLAY_COLUMNS)
    lines = [header, separator]
    for row in display_rows:
        lines.append(" | ".join(row[column].ljust(widths[column]) for column in PROMOTED_ACTION_DISPLAY_COLUMNS))
    return lines


def _column_width(column: str) -> int:
    widths = {
        "strategy_name": 28,
        "ticker": 8,
        "desired_position": 16,
        "current_position": 16,
        "current_quantity": 16,
        "preview_action": 32,
        "preview_quantity": 16,
        "reason": 56,
    }
    return widths.get(column, 20)


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return f"{value[: width - 3]}..."
