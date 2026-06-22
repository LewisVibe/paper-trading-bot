"""Saved-output-only concentration review for the high-growth research sleeve."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MISSING = "missing_saved_output"

SELECTED_SLEEVE = "codex_broad_growth_balanced_breakout_control"
SELECTED_MULTI_SLEEVE_LEAD = "higher_growth_70_20_5_5"
HIGH_GROWTH_WEIGHT_IN_LEAD = "20"
QUALITY_STATUS = "high_growth_sleeve_quality_promising_but_drawdown_sensitive"

STATUS_PASS = "high_growth_concentration_review_pass_research_only"
STATUS_MANUAL_REVIEW = "high_growth_concentration_manual_review_required"
STATUS_HIGH_SINGLE_NAME = "high_growth_concentration_high_single_name_dependency"
STATUS_BLOCKED = "high_growth_concentration_blocked_missing_component_streams"

DEPENDENCY_LOW_MODERATE = "component_dependency_low_or_moderate"
DEPENDENCY_MANUAL_REVIEW = "component_dependency_manual_review_required"
DEPENDENCY_HIGH_SINGLE_NAME = "component_dependency_high_single_name_risk"
DEPENDENCY_BLOCKED = "component_dependency_blocked_missing_component_streams"

NEXT_MANUAL_REVIEW = "manual_review_high_growth_component_concentration_before_label_change"
NEXT_MISSING_STREAMS = "run_high_growth_component_streams_before_concentration_review"

INPUT_FILES = {
    "component_streams": Path("data/high_growth_component_streams.csv"),
    "component_streams_summary": Path("data/high_growth_component_streams_summary.csv"),
    "component_attribution": Path("data/high_growth_component_attribution.csv"),
    "sleeve_quality_review": Path("data/high_growth_sleeve_quality_review.csv"),
    "sleeve_quality_summary": Path("data/high_growth_sleeve_quality_summary.csv"),
    "sleeve_quality_drawdowns": Path("data/high_growth_sleeve_quality_drawdowns.csv"),
    "lead_state": Path("data/multi_sleeve_lead_state.csv"),
    "drawdown_decomposition": Path("data/multi_sleeve_high_growth_drawdown_decomposition.csv"),
}

OUTPUT_FILES = {
    "review": Path("data/high_growth_sleeve_concentration_review.csv"),
    "summary": Path("data/high_growth_sleeve_concentration_summary.csv"),
    "top_contributors": Path("data/high_growth_sleeve_concentration_top_contributors.csv"),
    "drawdown": Path("data/high_growth_sleeve_concentration_drawdown.csv"),
    "blockers": Path("data/high_growth_sleeve_concentration_blockers.csv"),
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

REVIEW_COLUMNS = [
    "created_at",
    "selected_sleeve",
    "selected_multi_sleeve_lead",
    "high_growth_weight_in_lead",
    "high_growth_quality_status",
    "unique_ticker_count",
    "component_rows",
    "first_date",
    "last_date",
    "average_active_components",
    "min_active_components",
    "max_active_components",
    "max_component_weight",
    "average_top_component_weight",
    "percent_rows_single_component",
    "percent_rows_two_or_fewer_components",
    "concentration_status",
    "concentration_review_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = ["created_at", "summary_name", "summary_value", "details", *SAFETY_COLUMNS]

CONTRIBUTOR_COLUMNS = [
    "created_at",
    "selected_sleeve",
    "component_ticker",
    "contribution_rank",
    "contributor_side",
    "total_weighted_contribution",
    "positive_contribution",
    "negative_contribution",
    "active_rows",
    "average_weight",
    "max_weight",
    "first_seen_date",
    "last_seen_date",
    "contribution_share_of_total_positive",
    "contribution_share_of_total_absolute",
    "contributor_status",
    *SAFETY_COLUMNS,
]

DRAWDOWN_COLUMNS = [
    "created_at",
    "selected_sleeve",
    "drawdown_start",
    "drawdown_trough",
    "high_growth_MaxDD",
    "component_ticker",
    "drawdown_contribution_rank",
    "component_drawdown_weighted_contribution",
    "component_drawdown_absolute_share",
    "top_drawdown_contributor",
    "top_drawdown_contribution",
    "top_3_drawdown_contribution",
    "top_5_drawdown_contribution",
    "drawdown_concentration_status",
    *SAFETY_COLUMNS,
]

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


@dataclass
class HighGrowthSleeveConcentrationResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    contributor_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_sleeve_concentration_review(root_dir: Path | str = ".") -> HighGrowthSleeveConcentrationResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    stream_rows = selected_stream_rows(inputs["component_streams"])
    drawdown_input = inputs["sleeve_quality_drawdowns"]
    if not stream_rows:
        review_rows = [blocked_review_row(created_at)]
        contributor_rows: list[dict[str, Any]] = []
        drawdown_rows: list[dict[str, Any]] = []
        final_status = STATUS_BLOCKED
        dependency = blocked_dependency_metrics()
    else:
        contributor_all = build_all_contributor_rows(created_at, stream_rows)
        dependency = dependency_metrics(contributor_all)
        final_status = final_concentration_status(stream_rows, dependency)
        review_rows = [build_review_row(created_at, stream_rows, dependency, final_status)]
        contributor_rows = top_and_bottom_contributors(contributor_all)
        drawdown_rows = build_drawdown_rows(created_at, stream_rows, drawdown_input)
    blocker_rows = build_blocker_rows(created_at, stream_rows, drawdown_rows, final_status)
    summary_rows = build_summary_rows(created_at, final_status, review_rows[0], contributor_rows, drawdown_rows, dependency)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["top_contributors"], CONTRIBUTOR_COLUMNS, contributor_rows)
    write_rows(output_paths["drawdown"], DRAWDOWN_COLUMNS, drawdown_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthSleeveConcentrationResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        contributor_rows=contributor_rows,
        drawdown_rows=drawdown_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["review"]),
    )


def show_high_growth_sleeve_concentration_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "High-growth sleeve concentration review is missing.",
            "Run `python bot.py --high-growth-sleeve-concentration-review` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "High-growth sleeve concentration review. Saved-output-only research; no execution path.",
        f"final concentration review status: {summary.get('final_concentration_review_status', MISSING)}",
        f"selected sleeve: {summary.get('selected_sleeve', MISSING)}",
        f"unique ticker count: {summary.get('unique_ticker_count', MISSING)}",
        f"average active components: {summary.get('average_active_components', MISSING)}",
        f"max component weight: {summary.get('max_component_weight', MISSING)}",
        f"top contributor: {summary.get('top_contributor_summary', MISSING)}",
        f"worst contributor: {summary.get('worst_contributor_summary', MISSING)}",
        f"dependency shares: {summary.get('dependency_share_summary', MISSING)}",
        f"drawdown concentration: {summary.get('drawdown_concentration_summary', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def selected_stream_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("selected_sleeve") == SELECTED_SLEEVE or row.get("sleeve_name") == SELECTED_SLEEVE
    ]


def build_review_row(
    created_at: str,
    rows: list[dict[str, str]],
    dependency: dict[str, Any],
    final_status: str,
) -> dict[str, Any]:
    by_date = rows_by_date(rows)
    active_counts = [len(items) for items in by_date.values()]
    top_weights = [max(parse_float(row.get("component_weight")) for row in items) for items in by_date.values()]
    dates = sorted(by_date)
    return {
        "created_at": created_at,
        "selected_sleeve": SELECTED_SLEEVE,
        "selected_multi_sleeve_lead": SELECTED_MULTI_SLEEVE_LEAD,
        "high_growth_weight_in_lead": HIGH_GROWTH_WEIGHT_IN_LEAD,
        "high_growth_quality_status": QUALITY_STATUS,
        "unique_ticker_count": len({row.get("component_ticker") for row in rows if row.get("component_ticker")}),
        "component_rows": len(rows),
        "first_date": dates[0] if dates else MISSING,
        "last_date": dates[-1] if dates else MISSING,
        "average_active_components": rounded(sum(active_counts) / len(active_counts) if active_counts else 0.0),
        "min_active_components": min(active_counts) if active_counts else MISSING,
        "max_active_components": max(active_counts) if active_counts else MISSING,
        "max_component_weight": rounded(max((parse_float(row.get("component_weight")) for row in rows), default=0.0)),
        "average_top_component_weight": rounded(sum(top_weights) / len(top_weights) if top_weights else 0.0),
        "percent_rows_single_component": rounded(percent_count(active_counts, lambda value: value == 1)),
        "percent_rows_two_or_fewer_components": rounded(percent_count(active_counts, lambda value: value <= 2)),
        "concentration_status": dependency["dependency_status"],
        "concentration_review_status": final_status,
        "required_next_step": NEXT_MANUAL_REVIEW,
        **safety_flags(),
    }


def blocked_review_row(created_at: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "selected_sleeve": SELECTED_SLEEVE,
        "selected_multi_sleeve_lead": SELECTED_MULTI_SLEEVE_LEAD,
        "high_growth_weight_in_lead": HIGH_GROWTH_WEIGHT_IN_LEAD,
        "high_growth_quality_status": QUALITY_STATUS,
        "unique_ticker_count": 0,
        "component_rows": 0,
        "first_date": MISSING,
        "last_date": MISSING,
        "average_active_components": MISSING,
        "min_active_components": MISSING,
        "max_active_components": MISSING,
        "max_component_weight": MISSING,
        "average_top_component_weight": MISSING,
        "percent_rows_single_component": MISSING,
        "percent_rows_two_or_fewer_components": MISSING,
        "concentration_status": DEPENDENCY_BLOCKED,
        "concentration_review_status": STATUS_BLOCKED,
        "required_next_step": NEXT_MISSING_STREAMS,
        **safety_flags(),
    }


def build_all_contributor_rows(created_at: str, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        ticker = row.get("component_ticker")
        if ticker:
            grouped.setdefault(ticker, []).append(row)
    totals = {ticker: sum(parse_float(row.get("weighted_contribution")) for row in items) for ticker, items in grouped.items()}
    positives = {ticker: sum(max(parse_float(row.get("weighted_contribution")), 0.0) for row in items) for ticker, items in grouped.items()}
    negatives = {ticker: sum(min(parse_float(row.get("weighted_contribution")), 0.0) for row in items) for ticker, items in grouped.items()}
    total_positive = sum(positives.values())
    total_absolute = sum(abs(value) for value in totals.values())
    ranked = sorted(grouped, key=lambda ticker: totals[ticker], reverse=True)
    rows_out = []
    for rank, ticker in enumerate(ranked, start=1):
        items = grouped[ticker]
        weights = [parse_float(row.get("component_weight")) for row in items]
        dates = sorted(row.get("date", "") for row in items if row.get("date"))
        total = totals[ticker]
        positive_share = positives[ticker] / total_positive * 100.0 if total_positive > 0 else 0.0
        absolute_share = abs(total) / total_absolute * 100.0 if total_absolute > 0 else 0.0
        rows_out.append(
            {
                "created_at": created_at,
                "selected_sleeve": SELECTED_SLEEVE,
                "component_ticker": ticker,
                "contribution_rank": rank,
                "contributor_side": "top_positive" if total >= 0 else "bottom_negative",
                "total_weighted_contribution": rounded(total),
                "positive_contribution": rounded(positives[ticker]),
                "negative_contribution": rounded(negatives[ticker]),
                "active_rows": len(items),
                "average_weight": rounded(sum(weights) / len(weights) if weights else 0.0),
                "max_weight": rounded(max(weights) if weights else 0.0),
                "first_seen_date": dates[0] if dates else MISSING,
                "last_seen_date": dates[-1] if dates else MISSING,
                "contribution_share_of_total_positive": rounded(positive_share),
                "contribution_share_of_total_absolute": rounded(absolute_share),
                "contributor_status": contributor_status(positive_share, absolute_share),
                **safety_flags(),
            }
        )
    return rows_out


def top_and_bottom_contributors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    top = rows[:10]
    bottom = sorted(rows, key=lambda row: parse_float(row.get("total_weighted_contribution")))[:10]
    seen = set()
    selected = []
    for row in top + bottom:
        ticker = row.get("component_ticker")
        if ticker not in seen:
            selected.append(row)
            seen.add(ticker)
    return selected


def dependency_metrics(contributor_rows: list[dict[str, Any]]) -> dict[str, Any]:
    positive_shares = sorted(
        [parse_float(row.get("contribution_share_of_total_positive")) for row in contributor_rows],
        reverse=True,
    )
    absolute_shares = sorted(
        [parse_float(row.get("contribution_share_of_total_absolute")) for row in contributor_rows],
        reverse=True,
    )
    top1 = sum(positive_shares[:1])
    top3 = sum(positive_shares[:3])
    top5 = sum(positive_shares[:5])
    top10 = sum(positive_shares[:10])
    top1_abs = sum(absolute_shares[:1])
    top3_abs = sum(absolute_shares[:3])
    top5_abs = sum(absolute_shares[:5])
    herfindahl = sum((share / 100.0) ** 2 for share in positive_shares)
    if top1 >= 50.0 or top1_abs >= 50.0:
        status = DEPENDENCY_HIGH_SINGLE_NAME
    elif top1 >= 25.0 or top3 >= 60.0 or top1_abs >= 25.0:
        status = DEPENDENCY_MANUAL_REVIEW
    else:
        status = DEPENDENCY_LOW_MODERATE
    return {
        "top_1_contribution_share": rounded(top1),
        "top_3_contribution_share": rounded(top3),
        "top_5_contribution_share": rounded(top5),
        "top_10_contribution_share": rounded(top10),
        "top_1_absolute_contribution_share": rounded(top1_abs),
        "top_3_absolute_contribution_share": rounded(top3_abs),
        "top_5_absolute_contribution_share": rounded(top5_abs),
        "herfindahl_index_by_positive_contribution": rounded(herfindahl),
        "dependency_status": status,
    }


def blocked_dependency_metrics() -> dict[str, Any]:
    return {
        "top_1_contribution_share": MISSING,
        "top_3_contribution_share": MISSING,
        "top_5_contribution_share": MISSING,
        "top_10_contribution_share": MISSING,
        "top_1_absolute_contribution_share": MISSING,
        "top_3_absolute_contribution_share": MISSING,
        "top_5_absolute_contribution_share": MISSING,
        "herfindahl_index_by_positive_contribution": MISSING,
        "dependency_status": DEPENDENCY_BLOCKED,
    }


def final_concentration_status(rows: list[dict[str, str]], dependency: dict[str, Any]) -> str:
    by_date = rows_by_date(rows)
    active_counts = [len(items) for items in by_date.values()]
    max_weight = max((parse_float(row.get("component_weight")) for row in rows), default=0.0)
    average_active = sum(active_counts) / len(active_counts) if active_counts else 0.0
    if dependency["dependency_status"] == DEPENDENCY_HIGH_SINGLE_NAME:
        return STATUS_HIGH_SINGLE_NAME
    if dependency["dependency_status"] == DEPENDENCY_MANUAL_REVIEW or average_active <= 2.25 or max_weight >= 1.0:
        return STATUS_MANUAL_REVIEW
    return STATUS_PASS


def build_drawdown_rows(
    created_at: str,
    stream_rows: list[dict[str, str]],
    drawdown_input: list[dict[str, str]],
) -> list[dict[str, Any]]:
    window = drawdown_input[0] if drawdown_input else {}
    start = window.get("drawdown_start")
    trough = window.get("drawdown_trough")
    if not start or not trough:
        return []
    period_rows = [row for row in stream_rows if start <= row.get("date", "") <= trough]
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in period_rows:
        ticker = row.get("component_ticker")
        if ticker:
            grouped.setdefault(ticker, []).append(row)
    if not grouped:
        return []
    totals = {ticker: sum(parse_float(row.get("weighted_contribution")) for row in items) for ticker, items in grouped.items()}
    total_abs = sum(abs(value) for value in totals.values())
    ranked = sorted(grouped, key=lambda ticker: totals[ticker])
    worst_ticker = ranked[0]
    worst_values = [totals[ticker] for ticker in ranked]
    top3 = sum(worst_values[:3])
    top5 = sum(worst_values[:5])
    status = "drawdown_concentration_manual_review_required" if total_abs and abs(totals[worst_ticker]) / total_abs * 100.0 >= 20.0 else "drawdown_concentration_available_research_only"
    output = []
    for rank, ticker in enumerate(ranked[:10], start=1):
        contribution = totals[ticker]
        output.append(
            {
                "created_at": created_at,
                "selected_sleeve": SELECTED_SLEEVE,
                "drawdown_start": start,
                "drawdown_trough": trough,
                "high_growth_MaxDD": window.get("max_drawdown", MISSING),
                "component_ticker": ticker,
                "drawdown_contribution_rank": rank,
                "component_drawdown_weighted_contribution": rounded(contribution),
                "component_drawdown_absolute_share": rounded(abs(contribution) / total_abs * 100.0 if total_abs else 0.0),
                "top_drawdown_contributor": worst_ticker,
                "top_drawdown_contribution": rounded(totals[worst_ticker]),
                "top_3_drawdown_contribution": rounded(top3),
                "top_5_drawdown_contribution": rounded(top5),
                "drawdown_concentration_status": status,
                **safety_flags(),
            }
        )
    return output


def build_blocker_rows(
    created_at: str,
    stream_rows: list[dict[str, str]],
    drawdown_rows: list[dict[str, Any]],
    final_status: str,
) -> list[dict[str, Any]]:
    rows = []
    if not stream_rows:
        rows.append(blocker_row(created_at, "component_streams_missing", STATUS_BLOCKED, "high", "saved high-growth component streams are required for concentration review", NEXT_MISSING_STREAMS))
    if stream_rows and not drawdown_rows:
        rows.append(blocker_row(created_at, "drawdown_concentration_missing", "manual_review_required", "medium", "saved drawdown window or component rows are unavailable for drawdown concentration review", NEXT_MANUAL_REVIEW))
    rows.extend(
        [
            blocker_row(created_at, "execution_boundary", "blocked_non_executable_research_only", "high", "concentration review is research-only and cannot create order instructions", NEXT_MANUAL_REVIEW if stream_rows else NEXT_MISSING_STREAMS),
            blocker_row(created_at, "concentration_review_boundary", final_status, "medium", "manual review is required before any further candidate label change", NEXT_MANUAL_REVIEW if stream_rows else NEXT_MISSING_STREAMS),
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


def build_summary_rows(
    created_at: str,
    final_status: str,
    review_row: dict[str, Any],
    contributor_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
    dependency: dict[str, Any],
) -> list[dict[str, Any]]:
    top = max(contributor_rows, key=lambda row: parse_float(row.get("total_weighted_contribution")), default={})
    worst = min(contributor_rows, key=lambda row: parse_float(row.get("total_weighted_contribution")), default={})
    drawdown = drawdown_rows[0] if drawdown_rows else {}
    required_next_step = NEXT_MANUAL_REVIEW if final_status != STATUS_BLOCKED else NEXT_MISSING_STREAMS
    items = [
        ("final_concentration_review_status", final_status, "Cautious saved-output concentration review status."),
        ("selected_sleeve", SELECTED_SLEEVE, "Selected high-growth sleeve."),
        ("selected_multi_sleeve_lead", SELECTED_MULTI_SLEEVE_LEAD, "Selected multi-sleeve research lead."),
        ("high_growth_weight_in_lead", HIGH_GROWTH_WEIGHT_IN_LEAD, "High-growth sleeve weight in selected lead."),
        ("unique_ticker_count", review_row.get("unique_ticker_count", MISSING), "Unique component tickers in saved stream."),
        ("component_rows", review_row.get("component_rows", MISSING), "Saved component stream rows."),
        ("first_date", review_row.get("first_date", MISSING), "First saved component row date."),
        ("last_date", review_row.get("last_date", MISSING), "Last saved component row date."),
        ("average_active_components", review_row.get("average_active_components", MISSING), "Average active components per component day."),
        ("max_component_weight", review_row.get("max_component_weight", MISSING), "Maximum saved component weight."),
        ("top_contributor_summary", contributor_summary(top), "Largest positive contributor."),
        ("worst_contributor_summary", contributor_summary(worst), "Most negative contributor."),
        ("top_1_contribution_share", dependency["top_1_contribution_share"], "Top one positive contribution share."),
        ("top_3_contribution_share", dependency["top_3_contribution_share"], "Top three positive contribution share."),
        ("top_5_contribution_share", dependency["top_5_contribution_share"], "Top five positive contribution share."),
        ("top_10_contribution_share", dependency["top_10_contribution_share"], "Top ten positive contribution share."),
        ("top_1_absolute_contribution_share", dependency["top_1_absolute_contribution_share"], "Top one absolute contribution share."),
        ("top_3_absolute_contribution_share", dependency["top_3_absolute_contribution_share"], "Top three absolute contribution share."),
        ("top_5_absolute_contribution_share", dependency["top_5_absolute_contribution_share"], "Top five absolute contribution share."),
        ("herfindahl_index_by_positive_contribution", dependency["herfindahl_index_by_positive_contribution"], "Positive contribution Herfindahl index."),
        ("dependency_status", dependency["dependency_status"], "Component dependency status."),
        ("dependency_share_summary", dependency_share_summary(dependency), "Compact dependency share summary."),
        ("drawdown_concentration_summary", drawdown_summary(drawdown), "Worst drawdown component concentration summary."),
        ("required_next_step", required_next_step, "Next research step only."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def contributor_status(positive_share: float, absolute_share: float) -> str:
    if positive_share >= 35.0 or absolute_share >= 35.0:
        return "component_contributor_manual_review_required"
    return "component_contributor_available_research_only"


def contributor_summary(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"{row.get('component_ticker')}: weighted_contribution={row.get('total_weighted_contribution')}; positive_share={row.get('contribution_share_of_total_positive')}; absolute_share={row.get('contribution_share_of_total_absolute')}"


def dependency_share_summary(dependency: dict[str, Any]) -> str:
    return (
        f"top1={dependency['top_1_contribution_share']}; "
        f"top3={dependency['top_3_contribution_share']}; "
        f"top5={dependency['top_5_contribution_share']}; "
        f"top1_abs={dependency['top_1_absolute_contribution_share']}; "
        f"status={dependency['dependency_status']}"
    )


def drawdown_summary(row: dict[str, Any]) -> str:
    if not row:
        return "drawdown_concentration_missing_saved_inputs"
    return (
        f"{row.get('drawdown_start')}->{row.get('drawdown_trough')}; "
        f"MaxDD={row.get('high_growth_MaxDD')}; "
        f"top={row.get('top_drawdown_contributor')}:{row.get('top_drawdown_contribution')}; "
        f"top3={row.get('top_3_drawdown_contribution')}; "
        f"status={row.get('drawdown_concentration_status')}"
    )


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return [
        "High-growth sleeve concentration review created. Saved-output-only research; no execution path.",
        f"final concentration review status: {summary.get('final_concentration_review_status', MISSING)}",
        f"selected sleeve: {summary.get('selected_sleeve', MISSING)}",
        f"unique ticker count: {summary.get('unique_ticker_count', MISSING)}",
        f"average active components: {summary.get('average_active_components', MISSING)}",
        f"max component weight: {summary.get('max_component_weight', MISSING)}",
        f"top contributor: {summary.get('top_contributor_summary', MISSING)}",
        f"worst contributor: {summary.get('worst_contributor_summary', MISSING)}",
        f"dependency shares: {summary.get('dependency_share_summary', MISSING)}",
        f"drawdown concentration: {summary.get('drawdown_concentration_summary', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        f"Saved review: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def rows_by_date(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        date = row.get("date")
        if date:
            grouped.setdefault(date, []).append(row)
    return grouped


def percent_count(values: list[int], predicate: Any) -> float:
    if not values:
        return 0.0
    return sum(1 for value in values if predicate(value)) / len(values) * 100.0


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


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
