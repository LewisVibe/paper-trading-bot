"""Saved-output-only high-growth component attribution readiness review."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MISSING = "missing_saved_output"

HIGH_GROWTH_SLEEVE = "codex_broad_growth_balanced_breakout_control"
SELECTED_LEAD = "higher_growth_70_20_5_5"
QUALITY_STATUS = "high_growth_sleeve_quality_promising_but_drawdown_sensitive"
CONCENTRATION_BLOCKER = "ticker_concentration_data_missing"

STATUS_CREATED = "component_attribution_created_research_only"
STATUS_PARTIAL = "component_attribution_partial_manual_review_required"
STATUS_BLOCKED = "component_attribution_blocked_missing_saved_component_data"
STATUS_FUTURE_BUILDER = "component_attribution_blocked_future_builder_required"

NEXT_COMPONENT_STREAMS = "build_saved_high_growth_component_streams_before_concentration_review"
NEXT_MANUAL_REVIEW = "manual_review_high_growth_component_concentration_before_label_change"

INPUT_FILES = {
    "high_growth_stream": Path("data/high_growth_return_streams.csv"),
    "sleeve_quality_review": Path("data/high_growth_sleeve_quality_review.csv"),
    "sleeve_quality_summary": Path("data/high_growth_sleeve_quality_summary.csv"),
    "sleeve_quality_drawdowns": Path("data/high_growth_sleeve_quality_drawdowns.csv"),
    "drawdown_decomposition": Path("data/multi_sleeve_high_growth_drawdown_decomposition.csv"),
    "lead_state": Path("data/multi_sleeve_lead_state.csv"),
    "weight_sensitivity": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "growth_biased_rotation_diagnostics": Path("data/growth_biased_rotation_diagnostics.csv"),
}

OPTIONAL_COMPONENT_PATTERNS = [
    "data/high_growth*component*.csv",
    "data/high_growth*ticker*.csv",
    "data/high_growth*holding*.csv",
    "data/high_growth*trade*.csv",
]

OUTPUT_FILES = {
    "attribution": Path("data/high_growth_component_attribution.csv"),
    "summary": Path("data/high_growth_component_attribution_summary.csv"),
    "blockers": Path("data/high_growth_component_attribution_blockers.csv"),
    "contributions": Path("data/high_growth_component_contributions.csv"),
    "drawdown_contributions": Path("data/high_growth_component_drawdown_contributions.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "preview_only",
    "saved_output_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "yfinance_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]

ATTRIBUTION_COLUMNS = [
    "created_at",
    "row_type",
    "data_requirement",
    "available",
    "source_file",
    "source_column_or_reason",
    "blocker_status",
    "component_attribution_status",
    "selected_sleeve",
    "high_growth_quality_status",
    "concentration_blocker",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = ["created_at", "summary_name", "summary_value", "details", *SAFETY_COLUMNS]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "blocker_severity",
    "blocker_detail",
    "required_next_step",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
]

CONTRIBUTION_COLUMNS = [
    "created_at",
    "sleeve_name",
    "component_ticker",
    "first_seen_date",
    "last_seen_date",
    "active_rows",
    "average_weight",
    "max_weight",
    "total_weighted_contribution",
    "contribution_share",
    "contribution_status",
    "concentration_status",
    *SAFETY_COLUMNS,
]

DRAWDOWN_CONTRIBUTION_COLUMNS = [
    "created_at",
    "drawdown_start",
    "drawdown_trough",
    "component_ticker",
    "component_period_return",
    "component_weighted_contribution",
    "contribution_share_of_high_growth_drawdown",
    "drawdown_contribution_status",
    *SAFETY_COLUMNS,
]

TICKER_COLUMNS = {"component_ticker", "ticker", "symbol", "holding_ticker", "selected_ticker"}
DATE_COLUMNS = {"date", "component_date", "holding_date"}
WEIGHT_COLUMNS = {"component_weight", "weight", "holding_weight", "selected_ticker_weight"}
RETURN_COLUMNS = {"component_daily_return", "daily_component_return", "ticker_daily_return", "component_return"}
WEIGHTED_COLUMNS = {
    "component_weighted_contribution",
    "ticker_weighted_contribution",
    "weighted_contribution",
    "ticker_contribution",
    "component_contribution",
}


@dataclass
class ComponentSource:
    path: Path
    rows: list[dict[str, str]]


@dataclass
class HighGrowthComponentAttributionResult:
    output_paths: dict[str, Path]
    attribution_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    contribution_rows: list[dict[str, Any]]
    drawdown_contribution_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_component_attribution(root_dir: Path | str = ".") -> HighGrowthComponentAttributionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sources = load_sources(root)
    availability = audit_saved_data(sources)
    component_sources = sources_with_component_data(sources)
    contribution_rows = build_component_contributions(created_at, component_sources)
    drawdown_rows = build_drawdown_contributions(created_at, sources, component_sources)
    final_status = final_status_for(availability, contribution_rows, drawdown_rows)
    attribution_rows = build_attribution_rows(created_at, availability, final_status)
    summary_rows = build_summary_rows(created_at, final_status, availability, contribution_rows, drawdown_rows)
    blocker_rows = build_blocker_rows(created_at, final_status, availability, contribution_rows, drawdown_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["attribution"], ATTRIBUTION_COLUMNS, attribution_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    if contribution_rows:
        write_rows(output_paths["contributions"], CONTRIBUTION_COLUMNS, contribution_rows)
    if drawdown_rows:
        write_rows(output_paths["drawdown_contributions"], DRAWDOWN_CONTRIBUTION_COLUMNS, drawdown_rows)
    return HighGrowthComponentAttributionResult(
        output_paths=output_paths,
        attribution_rows=attribution_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        contribution_rows=contribution_rows,
        drawdown_contribution_rows=drawdown_rows,
        summary_lines=summary_lines(summary_rows, output_paths["attribution"]),
    )


def show_high_growth_component_attribution(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "High-growth component attribution is missing.",
            "Run `python bot.py --high-growth-component-attribution` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "High-growth component attribution review. Saved-output-only research; no execution path.",
        f"final component attribution status: {summary.get('final_component_attribution_status', MISSING)}",
        f"selected high-growth sleeve: {summary.get('selected_high_growth_sleeve', MISSING)}",
        f"component ticker data exists: {summary.get('component_ticker_data_exists', MISSING)}",
        f"component weight data exists: {summary.get('component_weight_data_exists', MISSING)}",
        f"component contribution data exists: {summary.get('component_contribution_data_exists', MISSING)}",
        f"concentration blocker: {summary.get('concentration_blocker', MISSING)}",
        f"future builder recommendation: {summary.get('future_builder_recommendation', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def load_sources(root: Path) -> dict[str, ComponentSource]:
    sources: dict[str, ComponentSource] = {}
    for name, relative in INPUT_FILES.items():
        path = root / relative
        sources[name] = ComponentSource(relative, read_csv_rows(path))
    for pattern in OPTIONAL_COMPONENT_PATTERNS:
        for path in sorted(root.glob(pattern)):
            relative = path.relative_to(root)
            key = "optional_" + "_".join(relative.parts).replace(".csv", "")
            sources.setdefault(key, ComponentSource(relative, read_csv_rows(path)))
    return sources


def audit_saved_data(sources: dict[str, ComponentSource]) -> dict[str, dict[str, Any]]:
    high_growth_stream = sources.get("high_growth_stream", ComponentSource(Path(""), []))
    component_sources = {name: source for name, source in sources.items() if columns_in_rows(source.rows) & TICKER_COLUMNS}
    return {
        "high_growth_sleeve_daily_returns": availability(bool(high_growth_stream.rows), high_growth_stream.path, "daily_strategy_return" if high_growth_stream.rows else "missing high-growth sleeve return rows"),
        "selected_high_growth_sleeve_name": availability(bool(HIGH_GROWTH_SLEEVE), high_growth_stream.path, HIGH_GROWTH_SLEEVE),
        "component_ticker_identifiers": column_availability(component_sources, TICKER_COLUMNS, "component_attribution_blocked_missing_ticker_holdings"),
        "component_holding_dates": column_availability(component_sources, DATE_COLUMNS, "component_attribution_blocked_missing_ticker_holdings"),
        "component_weights": column_availability(component_sources, WEIGHT_COLUMNS, "component_attribution_blocked_missing_holding_weights"),
        "component_daily_returns": column_availability(component_sources, RETURN_COLUMNS, "component_attribution_blocked_missing_component_returns"),
        "component_weighted_contributions": column_availability(component_sources, WEIGHTED_COLUMNS, "component_attribution_blocked_missing_component_returns"),
        "component_drawdown_window_contributions": drawdown_component_availability(component_sources),
    }


def availability(available: bool, path: Path, source: str) -> dict[str, Any]:
    return {
        "available": available,
        "source_file": str(path) if path else MISSING,
        "source_column_or_reason": source,
        "blocker_status": "available" if available else "blocked",
        "required_next_step": NEXT_MANUAL_REVIEW if available else NEXT_COMPONENT_STREAMS,
    }


def column_availability(sources: dict[str, ComponentSource], columns: set[str], blocker: str) -> dict[str, Any]:
    for source in sources.values():
        found = columns_in_rows(source.rows) & columns
        if found:
            return availability(True, source.path, ",".join(sorted(found)))
    return {
        "available": False,
        "source_file": MISSING,
        "source_column_or_reason": blocker,
        "blocker_status": blocker,
        "required_next_step": NEXT_COMPONENT_STREAMS,
    }


def drawdown_component_availability(sources: dict[str, ComponentSource]) -> dict[str, Any]:
    for source in sources.values():
        columns = columns_in_rows(source.rows)
        if columns & DATE_COLUMNS and (columns & WEIGHTED_COLUMNS or (columns & WEIGHT_COLUMNS and columns & RETURN_COLUMNS)):
            found = (columns & DATE_COLUMNS) | (columns & WEIGHTED_COLUMNS) | (columns & WEIGHT_COLUMNS) | (columns & RETURN_COLUMNS)
            return availability(True, source.path, ",".join(sorted(found)))
    return {
        "available": False,
        "source_file": MISSING,
        "source_column_or_reason": "component_drawdown_contribution_blocked_missing_ticker_level_returns",
        "blocker_status": "component_drawdown_contribution_blocked_missing_ticker_level_returns",
        "required_next_step": NEXT_COMPONENT_STREAMS,
    }


def sources_with_component_data(sources: dict[str, ComponentSource]) -> list[ComponentSource]:
    usable = []
    for source in sources.values():
        columns = columns_in_rows(source.rows)
        if columns & TICKER_COLUMNS and columns & DATE_COLUMNS and (columns & WEIGHTED_COLUMNS or (columns & WEIGHT_COLUMNS and columns & RETURN_COLUMNS)):
            usable.append(source)
    return usable


def build_attribution_rows(created_at: str, availability_rows: dict[str, dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "row_type": "saved_data_availability_audit",
            "data_requirement": requirement,
            "available": info["available"],
            "source_file": info["source_file"],
            "source_column_or_reason": info["source_column_or_reason"],
            "blocker_status": info["blocker_status"],
            "component_attribution_status": final_status,
            "selected_sleeve": HIGH_GROWTH_SLEEVE,
            "high_growth_quality_status": QUALITY_STATUS,
            "concentration_blocker": CONCENTRATION_BLOCKER,
            "required_next_step": info["required_next_step"],
            **safety_flags(),
        }
        for requirement, info in availability_rows.items()
    ]


def build_component_contributions(created_at: str, component_sources: list[ComponentSource]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for source in component_sources:
        for row in source.rows:
            ticker = first_value(row, TICKER_COLUMNS)
            if ticker:
                grouped.setdefault(ticker, []).append(row)
    rows = []
    total_abs_contribution = sum(abs(total_weighted_contribution(items)) for items in grouped.values()) or 0.0
    for ticker, items in sorted(grouped.items()):
        weighted = total_weighted_contribution(items)
        weights = [parse_float(first_value(row, WEIGHT_COLUMNS)) for row in items if first_value(row, WEIGHT_COLUMNS)]
        dates = sorted(first_value(row, DATE_COLUMNS) for row in items if first_value(row, DATE_COLUMNS))
        share = abs(weighted) / total_abs_contribution * 100.0 if total_abs_contribution else 0.0
        rows.append(
            {
                "created_at": created_at,
                "sleeve_name": HIGH_GROWTH_SLEEVE,
                "component_ticker": ticker,
                "first_seen_date": dates[0] if dates else MISSING,
                "last_seen_date": dates[-1] if dates else MISSING,
                "active_rows": len(items),
                "average_weight": rounded(sum(weights) / len(weights)) if weights else MISSING,
                "max_weight": rounded(max(weights)) if weights else MISSING,
                "total_weighted_contribution": rounded(weighted),
                "contribution_share": rounded(share),
                "contribution_status": "component_contribution_available_research_only",
                "concentration_status": "component_concentration_manual_review_required" if share >= 35 else "component_concentration_available_research_only",
                **safety_flags(),
            }
        )
    return rows


def build_drawdown_contributions(
    created_at: str,
    sources: dict[str, ComponentSource],
    component_sources: list[ComponentSource],
) -> list[dict[str, Any]]:
    window = high_growth_drawdown_window(sources)
    if not window or not component_sources:
        return []
    start, trough = window
    period_rows: dict[str, list[dict[str, str]]] = {}
    for source in component_sources:
        for row in source.rows:
            ticker = first_value(row, TICKER_COLUMNS)
            row_date = first_value(row, DATE_COLUMNS)
            if ticker and start <= row_date <= trough:
                period_rows.setdefault(ticker, []).append(row)
    total_abs = sum(abs(total_weighted_contribution(rows)) for rows in period_rows.values()) or 0.0
    output = []
    for ticker, rows in sorted(period_rows.items()):
        weighted = total_weighted_contribution(rows)
        period_return = compounded_component_return(rows)
        share = abs(weighted) / total_abs * 100.0 if total_abs else 0.0
        output.append(
            {
                "created_at": created_at,
                "drawdown_start": start,
                "drawdown_trough": trough,
                "component_ticker": ticker,
                "component_period_return": rounded(period_return),
                "component_weighted_contribution": rounded(weighted),
                "contribution_share_of_high_growth_drawdown": rounded(share),
                "drawdown_contribution_status": "component_drawdown_contribution_available_research_only",
                **safety_flags(),
            }
        )
    return output


def final_status_for(
    availability_rows: dict[str, dict[str, Any]],
    contribution_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
) -> str:
    has_ticker = bool(availability_rows["component_ticker_identifiers"]["available"])
    has_weight = bool(availability_rows["component_weights"]["available"])
    has_weighted = bool(availability_rows["component_weighted_contributions"]["available"])
    has_return = bool(availability_rows["component_daily_returns"]["available"])
    if contribution_rows and drawdown_rows:
        return STATUS_CREATED
    if contribution_rows:
        return STATUS_PARTIAL
    if has_ticker and has_weight and (has_weighted or has_return):
        return STATUS_PARTIAL
    return STATUS_BLOCKED


def build_summary_rows(
    created_at: str,
    final_status: str,
    availability_rows: dict[str, dict[str, Any]],
    contribution_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    top_component = top_component_summary(contribution_rows)
    future_builder = future_builder_recommendation(final_status)
    items = [
        ("final_component_attribution_status", final_status, "Cautious saved-output component attribution label."),
        ("selected_high_growth_sleeve", HIGH_GROWTH_SLEEVE, "Selected high-growth research sleeve."),
        ("high_growth_quality_status", QUALITY_STATUS, "Current saved high-growth sleeve quality status."),
        ("component_ticker_data_exists", bool_text(availability_rows["component_ticker_identifiers"]["available"]), "Ticker identifier availability."),
        ("component_weight_data_exists", bool_text(availability_rows["component_weights"]["available"]), "Component weight availability."),
        ("component_contribution_data_exists", bool_text(availability_rows["component_weighted_contributions"]["available"]), "Weighted contribution availability."),
        ("component_drawdown_contribution_data_exists", bool_text(bool(drawdown_rows)), "Drawdown-window component contribution availability."),
        ("concentration_blocker", CONCENTRATION_BLOCKER, "Current concentration blocker from high-growth sleeve quality review."),
        ("top_component_summary", top_component, "Top component row when real attribution exists."),
        ("future_builder_recommendation", future_builder, "Future component stream builder recommendation."),
        ("required_next_step", NEXT_MANUAL_REVIEW if contribution_rows else NEXT_COMPONENT_STREAMS, "Next research step only."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(
    created_at: str,
    final_status: str,
    availability_rows: dict[str, dict[str, Any]],
    contribution_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    if final_status in {STATUS_BLOCKED, STATUS_FUTURE_BUILDER}:
        rows.extend(
            [
                blocker_row(created_at, "component_attribution_blocked_missing_ticker_holdings", availability_rows["component_ticker_identifiers"]["blocker_status"], "high", "saved outputs do not include component ticker identifiers", NEXT_COMPONENT_STREAMS),
                blocker_row(created_at, "component_attribution_blocked_missing_component_returns", availability_rows["component_daily_returns"]["blocker_status"], "high", "saved outputs do not include component daily returns", NEXT_COMPONENT_STREAMS),
                blocker_row(created_at, "future_component_stream_builder_required", STATUS_FUTURE_BUILDER, "medium", "future command may need to save high-growth component streams from original generation logic; this command does not call yfinance", NEXT_COMPONENT_STREAMS),
            ]
        )
    if not bool(availability_rows["component_weights"]["available"]):
        rows.append(blocker_row(created_at, "component_drawdown_contribution_blocked_missing_holding_weights", "blocked", "high", "component drawdown attribution needs saved holding weights", NEXT_COMPONENT_STREAMS))
    if not drawdown_rows:
        rows.append(blocker_row(created_at, "component_drawdown_contribution_blocked_missing_ticker_level_returns", "blocked", "high", "component drawdown attribution needs ticker-level return or weighted contribution rows", NEXT_COMPONENT_STREAMS))
    rows.extend(
        [
            blocker_row(created_at, "execution_boundary", "blocked_non_executable_research_only", "high", "component attribution is not an execution path", NEXT_COMPONENT_STREAMS if not contribution_rows else NEXT_MANUAL_REVIEW),
            blocker_row(created_at, "scheduling_boundary", "blocked_no_scheduling_change", "high", "component attribution is not a schedule or cron change", NEXT_COMPONENT_STREAMS if not contribution_rows else NEXT_MANUAL_REVIEW),
        ]
    )
    return rows


def blocker_row(created_at: str, name: str, status: str, severity: str, detail: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "blocker_status": status,
        "blocker_severity": severity,
        "blocker_detail": detail,
        "required_next_step": next_step,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "scheduling_approved": False,
    }


def high_growth_drawdown_window(sources: dict[str, ComponentSource]) -> tuple[str, str] | None:
    rows = sources.get("sleeve_quality_drawdowns", ComponentSource(Path(""), [])).rows
    row = rows[0] if rows else {}
    start = row.get("drawdown_start")
    trough = row.get("drawdown_trough")
    if start and trough:
        return start, trough
    return None


def total_weighted_contribution(rows: list[dict[str, str]]) -> float:
    total = 0.0
    for row in rows:
        weighted = first_value(row, WEIGHTED_COLUMNS)
        if weighted:
            total += parse_float(weighted)
            continue
        weight = first_value(row, WEIGHT_COLUMNS)
        daily_return = first_value(row, RETURN_COLUMNS)
        if weight and daily_return:
            total += parse_float(weight) * parse_float(daily_return)
    return total


def compounded_component_return(rows: list[dict[str, str]]) -> float:
    equity = 1.0
    for row in rows:
        value = first_value(row, RETURN_COLUMNS)
        if value:
            equity *= 1.0 + parse_float(value)
    return (equity - 1.0) * 100.0


def columns_in_rows(rows: list[dict[str, str]]) -> set[str]:
    columns: set[str] = set()
    for row in rows:
        columns.update(key for key, value in row.items() if value not in {"", None})
    return columns


def first_value(row: dict[str, str], columns: set[str]) -> str:
    for column in columns:
        value = row.get(column)
        if value not in {"", None}:
            return str(value)
    return ""


def top_component_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "missing_real_component_rows"
    top = max(rows, key=lambda row: parse_float(row.get("contribution_share")))
    return f"{top.get('component_ticker')}: contribution_share={top.get('contribution_share')}; max_weight={top.get('max_weight')}; status={top.get('concentration_status')}"


def future_builder_recommendation(status: str) -> str:
    if status in {STATUS_CREATED, STATUS_PARTIAL}:
        return "review_existing_saved_component_streams_before_label_change"
    return "future --high-growth-component-streams command may be needed; separate prompt required; this command does not call yfinance"


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return [
        "High-growth component attribution review created. Saved-output-only research; no execution path.",
        f"final component attribution status: {summary.get('final_component_attribution_status', MISSING)}",
        f"selected high-growth sleeve: {summary.get('selected_high_growth_sleeve', MISSING)}",
        f"component ticker data exists: {summary.get('component_ticker_data_exists', MISSING)}",
        f"component weight data exists: {summary.get('component_weight_data_exists', MISSING)}",
        f"component contribution data exists: {summary.get('component_contribution_data_exists', MISSING)}",
        f"concentration blocker: {summary.get('concentration_blocker', MISSING)}",
        f"future builder recommendation: {summary.get('future_builder_recommendation', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        f"Saved review: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


def bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rounded(value: Any) -> str:
    return str(round(parse_float(value), 4))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": True,
        "saved_output_only": True,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
        "orders_replaced": False,
        "alpaca_called": False,
        "yfinance_called": False,
        "live_position_read": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "live_trading_approved": False,
        "scheduling_approved": False,
        "shorting_approved": False,
        "leverage_approved": False,
        "margin_approved": False,
    }
