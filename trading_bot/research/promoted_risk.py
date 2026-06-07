"""Research-only risk preview for promoted strategy desired positions.

This module reads saved promoted preview CSV files and creates a conservative
risk inspection report. It does not download market data, call Alpaca, create
orders, write SQLite trade logs, or send alerts.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


DEFAULT_MAX_OPEN_POSITIONS = 2

PROMOTED_RISK_COLUMNS = [
    "created_at",
    "strategy_name",
    "ticker",
    "desired_position",
    "current_position",
    "preview_action",
    "latest_close",
    "assumed_quantity",
    "estimated_desired_notional",
    "risk_check",
    "risk_status",
    "risk_reason",
    "research_only",
    "preview_only",
]

PROMOTED_RISK_DISPLAY_COLUMNS = [
    "strategy_name",
    "ticker",
    "desired_position",
    "current_position",
    "preview_action",
    "latest_close",
    "assumed_quantity",
    "estimated_desired_notional",
    "risk_check",
    "risk_status",
    "risk_reason",
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


def build_action_context(action_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    context: dict[tuple[str, str], dict[str, str]] = {}
    for row in action_rows:
        strategy_name = row.get("strategy_name", "")
        ticker = row.get("ticker", "").upper()
        if strategy_name and ticker:
            context[(strategy_name, ticker)] = row
    return context


def build_promoted_risk_rows(
    preview_rows: list[dict[str, str]],
    action_rows: list[dict[str, str]] | None = None,
    max_open_positions: int = DEFAULT_MAX_OPEN_POSITIONS,
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    action_context = build_action_context(action_rows or [])
    desired_long_counts_by_strategy = Counter(
        row.get("strategy_name", "")
        for row in preview_rows
        if row.get("desired_position", "").lower() == "long"
    )
    desired_long_counts_by_ticker = Counter(
        row.get("ticker", "").upper()
        for row in preview_rows
        if row.get("desired_position", "").lower() == "long"
    )

    rows: list[dict[str, Any]] = []
    for preview_row in preview_rows:
        strategy_name = preview_row.get("strategy_name", "")
        ticker = preview_row.get("ticker", "").upper()
        desired_position = preview_row.get("desired_position", "").lower()
        latest_close_text = preview_row.get("latest_close", "")
        latest_close = parse_decimal(latest_close_text)
        assumed_quantity = Decimal("1")
        estimated_desired_notional = estimate_desired_notional(
            desired_position,
            latest_close,
            assumed_quantity,
        )
        action_row = action_context.get((strategy_name, ticker), {})
        current_position = action_row.get("current_position", "")
        preview_action = action_row.get("preview_action", "")

        checks = build_risk_checks_for_row(
            strategy_name,
            ticker,
            desired_position,
            current_position,
            preview_action,
            desired_long_counts_by_strategy,
            desired_long_counts_by_ticker,
            max_open_positions,
            latest_close,
            latest_close_text,
        )
        for risk_check, risk_status, risk_reason in checks:
            rows.append(
                {
                    "created_at": timestamp,
                    "strategy_name": strategy_name,
                    "ticker": ticker,
                    "desired_position": desired_position,
                    "current_position": current_position,
                    "preview_action": preview_action,
                    "latest_close": format_decimal_or_blank(latest_close),
                    "assumed_quantity": format_decimal_or_blank(assumed_quantity),
                    "estimated_desired_notional": format_decimal_or_blank(estimated_desired_notional),
                    "risk_check": risk_check,
                    "risk_status": risk_status,
                    "risk_reason": risk_reason,
                    "research_only": True,
                    "preview_only": True,
                }
            )
    return rows


def build_risk_checks_for_row(
    strategy_name: str,
    ticker: str,
    desired_position: str,
    current_position: str,
    preview_action: str,
    desired_long_counts_by_strategy: Counter[str],
    desired_long_counts_by_ticker: Counter[str],
    max_open_positions: int,
    latest_close: Decimal | None,
    latest_close_text: str,
) -> list[tuple[str, str, str]]:
    checks = [
        desired_long_count_check(strategy_name, desired_position, desired_long_counts_by_strategy, max_open_positions),
        duplicate_ticker_exposure_check(ticker, desired_position, desired_long_counts_by_ticker),
        concentration_risk_check(ticker, desired_position, desired_long_counts_by_ticker),
        unavailable_position_check(current_position, preview_action),
        notional_data_quality_check(desired_position, latest_close, latest_close_text),
    ]
    return checks


def parse_decimal(value: str) -> Decimal | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        decimal_value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not decimal_value.is_finite() or decimal_value < 0:
        return None
    return decimal_value


def estimate_desired_notional(
    desired_position: str,
    latest_close: Decimal | None,
    assumed_quantity: Decimal,
) -> Decimal | None:
    if desired_position != "long":
        return Decimal("0")
    if latest_close is None:
        return None
    return latest_close * assumed_quantity


def format_decimal_or_blank(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value.normalize(), "f")


def desired_long_count_check(
    strategy_name: str,
    desired_position: str,
    desired_long_counts_by_strategy: Counter[str],
    max_open_positions: int,
) -> tuple[str, str, str]:
    desired_longs = desired_long_counts_by_strategy.get(strategy_name, 0)
    if desired_position != "long":
        return (
            "max_open_positions",
            "ok",
            f"Strategy has {desired_longs} desired long position(s); limit is {max_open_positions}.",
        )
    if desired_longs > max_open_positions:
        return (
            "max_open_positions",
            "blocked_for_review",
            f"Strategy wants {desired_longs} long position(s), above the conservative limit of {max_open_positions}.",
        )
    return (
        "max_open_positions",
        "ok",
        f"Strategy wants {desired_longs} long position(s), within the conservative limit of {max_open_positions}.",
    )


def duplicate_ticker_exposure_check(
    ticker: str,
    desired_position: str,
    desired_long_counts_by_ticker: Counter[str],
) -> tuple[str, str, str]:
    ticker_longs = desired_long_counts_by_ticker.get(ticker, 0)
    if desired_position == "long" and ticker_longs > 1:
        return (
            "duplicate_ticker_exposure",
            "warning",
            f"{ticker} is desired long by {ticker_longs} promoted strategy rows.",
        )
    return (
        "duplicate_ticker_exposure",
        "ok",
        f"{ticker} does not have duplicate desired-long exposure.",
    )


def concentration_risk_check(
    ticker: str,
    desired_position: str,
    desired_long_counts_by_ticker: Counter[str],
) -> tuple[str, str, str]:
    ticker_longs = desired_long_counts_by_ticker.get(ticker, 0)
    if desired_position == "long" and ticker_longs > 1:
        return (
            "concentration_risk",
            "warning",
            f"Multiple promoted strategies want {ticker} long; review concentration before any execution discussion.",
        )
    return (
        "concentration_risk",
        "ok",
        f"No promoted-strategy concentration warning for {ticker}.",
    )


def unavailable_position_check(current_position: str, preview_action: str) -> tuple[str, str, str]:
    if current_position == "unavailable" or preview_action == "position_unavailable":
        return (
            "position_availability",
            "blocked_for_review",
            "Current position data is unavailable; do not assume flat.",
        )
    if not current_position and not preview_action:
        return (
            "position_availability",
            "warning",
            "Action preview context was not available for this row.",
        )
    return (
        "position_availability",
        "ok",
        "Current position context is available from the saved action preview.",
    )


def notional_data_quality_check(
    desired_position: str,
    latest_close: Decimal | None,
    latest_close_text: str,
) -> tuple[str, str, str]:
    if desired_position != "long":
        return (
            "notional_data_quality",
            "ok",
            "Desired position is flat; estimated desired notional is 0.",
        )
    if latest_close is None:
        raw_value = str(latest_close_text or "").strip() or "missing"
        return (
            "notional_data_quality",
            "blocked_for_review",
            f"Saved latest_close is not usable for desired-long notional estimate: {raw_value}.",
        )
    return (
        "notional_data_quality",
        "ok",
        "Saved latest_close was used for rough desired-notional estimate.",
    )


def write_promoted_risk_preview(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PROMOTED_RISK_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PROMOTED_RISK_COLUMNS})


def build_promoted_risk_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    statuses = Counter(str(row.get("risk_status", "")) for row in rows)
    checks = Counter(str(row.get("risk_check", "")) for row in rows)
    blocked = statuses.get("blocked_for_review", 0)
    warnings = statuses.get("warning", 0)
    strategy_notional = aggregate_notional_by(rows, "strategy_name")
    duplicated_ticker_notional = aggregate_notional_by(rows, "ticker")
    unique_ticker_notional = aggregate_unique_notional_by_ticker(rows)
    unique_total = sum(unique_ticker_notional.values(), Decimal("0"))
    lines = [
        "Promoted strategy risk preview",
        "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION.",
        "This report reads saved CSV files only and does not refresh market data, call Alpaca, or submit orders.",
        f"Rows: {len(rows)}",
        f"Warnings: {warnings}",
        f"Blocked for review: {blocked}",
        "Risk checks: " + (", ".join(f"{name}={count}" for name, count in sorted(checks.items())) if checks else "none"),
        "Estimated desired notional by strategy: " + format_notional_summary(strategy_notional),
        "Estimated duplicated desired notional by ticker: " + format_notional_summary(duplicated_ticker_notional),
        "Estimated unique desired notional by ticker: " + format_notional_summary(unique_ticker_notional),
        f"Estimated unique account-style desired notional total: {format_money(unique_total)}",
        f"Saved promoted risk preview to {output_path}",
    ]
    return lines


def build_show_promoted_risk_lines(input_path: Path, rows: list[dict[str, str]]) -> list[str]:
    status_counts = Counter(row.get("risk_status", "") or "blank" for row in rows)
    check_counts = Counter(row.get("risk_check", "") or "blank" for row in rows)
    desired_counts = Counter(row.get("desired_position", "") or "blank" for row in rows)
    blocked_rows = [row for row in rows if row.get("risk_status") == "blocked_for_review"]
    warning_rows = [row for row in rows if row.get("risk_status") == "warning"]
    strategy_notional = aggregate_notional_by(rows, "strategy_name")
    duplicated_ticker_notional = aggregate_notional_by(rows, "ticker")
    unique_ticker_notional = aggregate_unique_notional_by_ticker(rows)
    unique_total = sum(unique_ticker_notional.values(), Decimal("0"))

    lines = [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "This command only reads data/promoted_risk_preview.csv and does not refresh market data, read positions, or submit orders.",
        f"Input file: {input_path}",
        f"Rows: {len(rows)}",
        "",
        "Count by risk_status:",
        *_format_counts(status_counts),
        "",
        "Count by risk_check:",
        *_format_counts(check_counts),
        "",
        "Count by desired_position:",
        *_format_counts(desired_counts),
        "",
        "Estimated desired notional by strategy:",
        *_format_notional_counts(strategy_notional),
        "",
        "Estimated duplicated desired notional by ticker:",
        *_format_notional_counts(duplicated_ticker_notional),
        "",
        "Estimated unique desired notional by ticker:",
        *_format_notional_counts(unique_ticker_notional),
        "",
        f"Estimated unique account-style desired notional total: {format_money(unique_total)}",
        "",
        f"Blocked-for-review rows: {len(blocked_rows)}",
        *_format_risk_row_summaries(blocked_rows),
        "",
        f"Warning rows: {len(warning_rows)}",
        *_format_risk_row_summaries(warning_rows),
        "",
        *_format_risk_table(rows),
    ]
    return lines


def build_missing_promoted_risk_lines(input_path: Path) -> list[str]:
    return [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "This command only reads data/promoted_risk_preview.csv and does not refresh market data, read positions, or submit orders.",
        f"Missing promoted risk preview file: {input_path}",
        "Run this first:",
        "python bot.py --promoted-risk-preview",
    ]


def show_promoted_risk_file(input_path: Path) -> tuple[int, list[str]]:
    if not input_path.exists():
        return 1, build_missing_promoted_risk_lines(input_path)
    return 0, build_show_promoted_risk_lines(input_path, read_csv_rows(input_path))


def aggregate_notional_by(rows: list[dict[str, Any]], key_field: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    seen: set[tuple[str, str, str, str, str]] = set()
    for row in rows:
        key = str(row.get(key_field, "") or "blank")
        row_key = (
            str(row.get("strategy_name", "")),
            str(row.get("ticker", "")),
            str(row.get("desired_position", "")),
            str(row.get("latest_close", "")),
            str(row.get("assumed_quantity", "")),
        )
        if row_key in seen:
            continue
        seen.add(row_key)
        notional = parse_decimal(str(row.get("estimated_desired_notional", "")))
        if notional is None:
            continue
        totals[key] = totals.get(key, Decimal("0")) + notional
    return totals


def aggregate_unique_notional_by_ticker(rows: list[dict[str, Any]]) -> dict[str, Decimal]:
    ticker_values: dict[str, Decimal] = {}
    seen_rows: set[tuple[str, str, str, str, str]] = set()
    for row in rows:
        if str(row.get("desired_position", "")) != "long":
            continue
        row_key = (
            str(row.get("strategy_name", "")),
            str(row.get("ticker", "")),
            str(row.get("desired_position", "")),
            str(row.get("latest_close", "")),
            str(row.get("assumed_quantity", "")),
        )
        if row_key in seen_rows:
            continue
        seen_rows.add(row_key)
        ticker = str(row.get("ticker", "") or "blank")
        notional = parse_decimal(str(row.get("estimated_desired_notional", "")))
        if notional is None:
            continue
        current = ticker_values.get(ticker)
        if current is None or notional > current:
            ticker_values[ticker] = notional
    return ticker_values


def format_notional_summary(totals: dict[str, Decimal]) -> str:
    if not totals:
        return "none"
    return ", ".join(f"{name}={format_money(value)}" for name, value in sorted(totals.items()))


def _format_notional_counts(totals: dict[str, Decimal]) -> list[str]:
    if not totals:
        return ["- none"]
    return [f"- {name}: {format_money(value)}" for name, value in sorted(totals.items())]


def format_money(value: Decimal) -> str:
    return f"${value.quantize(Decimal('0.01'))}"


def run_promoted_risk_preview_files(
    preview_path: Path,
    action_path: Path,
    output_path: Path,
    max_open_positions: int = DEFAULT_MAX_OPEN_POSITIONS,
) -> tuple[int, list[str]]:
    if not preview_path.exists():
        return (
            1,
            [
                "Promoted strategy risk preview",
                "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION.",
                f"Missing promoted strategy preview file: {preview_path}",
                "Run this first:",
                "python bot.py --preview-promoted-strategies",
            ],
        )

    preview_rows = read_csv_rows(preview_path)
    action_rows = read_csv_rows(action_path) if action_path.exists() else []
    rows = build_promoted_risk_rows(preview_rows, action_rows, max_open_positions)
    write_promoted_risk_preview(output_path, rows)
    return 0, build_promoted_risk_summary(rows, output_path)


def _format_counts(counts: Counter[str]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {name}: {count}" for name, count in sorted(counts.items())]


def _format_risk_row_summaries(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["- none"]
    lines = []
    for row in rows[:10]:
        lines.append(
            f"- {row.get('strategy_name', '')} {row.get('ticker', '')} "
            f"{row.get('risk_check', '')}: {row.get('risk_reason', '')}"
        )
    if len(rows) > 10:
        lines.append(f"- ... {len(rows) - 10} more row(s)")
    return lines


def _format_risk_table(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["No promoted risk rows found."]

    display_rows = [
        {column: _truncate(str(row.get(column, "")), _column_width(column)) for column in PROMOTED_RISK_DISPLAY_COLUMNS}
        for row in rows
    ]
    widths = {
        column: min(
            _column_width(column),
            max(len(column), *(len(row[column]) for row in display_rows)),
        )
        for column in PROMOTED_RISK_DISPLAY_COLUMNS
    }
    header = " | ".join(column.ljust(widths[column]) for column in PROMOTED_RISK_DISPLAY_COLUMNS)
    separator = "-+-".join("-" * widths[column] for column in PROMOTED_RISK_DISPLAY_COLUMNS)
    lines = [header, separator]
    for row in display_rows:
        lines.append(" | ".join(row[column].ljust(widths[column]) for column in PROMOTED_RISK_DISPLAY_COLUMNS))
    return lines


def _column_width(column: str) -> int:
    widths = {
        "strategy_name": 28,
        "ticker": 8,
        "desired_position": 16,
        "current_position": 16,
        "preview_action": 28,
        "latest_close": 12,
        "assumed_quantity": 16,
        "estimated_desired_notional": 28,
        "risk_check": 28,
        "risk_status": 20,
        "risk_reason": 64,
    }
    return widths.get(column, 20)


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return f"{value[: width - 3]}..."
