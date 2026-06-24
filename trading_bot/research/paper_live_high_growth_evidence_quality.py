"""Saved-output high-growth evidence quality review.

This report interprets existing high-growth saved outputs as manual-review
context only. It does not rerun research, refresh market data, call Alpaca,
read positions, create action previews, create order instructions, schedule
anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "review": Path("data/paper_live_high_growth_evidence_quality.csv"),
    "summary": Path("data/paper_live_high_growth_evidence_quality_summary.csv"),
    "blockers": Path("data/paper_live_high_growth_evidence_quality_blockers.csv"),
    "evidence": Path("data/paper_live_high_growth_evidence_quality_evidence.csv"),
}

INPUT_FILES = {
    "evidence_gap_summary": Path("data/paper_live_high_growth_evidence_gap_summary.csv"),
    "drawdown_control_report": Path("data/high_growth_stock_drawdown_control_report.csv"),
    "drawdown_control_summary": Path("data/high_growth_stock_drawdown_control_summary.csv"),
    "drawdown_control_drawdowns": Path("data/high_growth_stock_drawdown_control_drawdowns.csv"),
    "drawdown_control_concentration": Path("data/high_growth_stock_drawdown_control_concentration.csv"),
    "component_attribution": Path("data/high_growth_component_attribution.csv"),
    "component_attribution_summary": Path("data/high_growth_component_attribution_summary.csv"),
    "component_contributions": Path("data/high_growth_component_contributions.csv"),
    "component_drawdown_contributions": Path("data/high_growth_component_drawdown_contributions.csv"),
    "component_streams_summary": Path("data/high_growth_component_streams_summary.csv"),
    "manual_review_blockers": Path("data/high_growth_stock_manual_review_blockers.csv"),
    "risk_review_blockers": Path("data/high_growth_stock_risk_review_blockers.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "high_growth_promotion_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "preview_approved": False,
    "paper_live_candidate_approved": False,
    "action_preview_created": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "portfolio_execution_wired": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REVIEW_COLUMNS = [
    "review_area",
    "evidence_present",
    "quality_status",
    "key_manual_review_issue",
    "current_blocker",
    "allowed_next_action",
    "forbidden_action",
    "research_only",
    "report_only",
    "saved_output_only",
    "preview_approved",
    "paper_live_candidate_approved",
    "action_preview_created",
    "order_instructions_created",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "portfolio_execution_wired",
    "alpaca_called",
    "live_positions_read",
    "market_data_refreshed",
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]

QUALITY_STATUS = "high_growth_evidence_quality_manual_review_required"
NEXT_REVIEW = "manual_review_high_growth_evidence_quality_before_any_promotion_discussion"


@dataclass
class QualityContext:
    root: Path
    rows_by_name: dict[str, list[dict[str, str]]]


@dataclass
class PaperLiveHighGrowthEvidenceQualityResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_high_growth_evidence_quality(root_dir: Path | str = ".") -> PaperLiveHighGrowthEvidenceQualityResult:
    root = Path(root_dir)
    context = load_quality_context(root)
    review_rows = build_review_rows(context)
    summary_rows = build_summary_rows(review_rows)
    blocker_rows = build_blocker_rows(review_rows)
    evidence_rows = build_evidence_rows(context, review_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveHighGrowthEvidenceQualityResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_high_growth_evidence_quality(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live high-growth evidence quality review is missing.",
            "Run `python bot.py --paper-live-high-growth-evidence-quality` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; high_growth_promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live high-growth evidence quality review. Saved-output/manual-review only; no high-growth promotion approved.",
        f"final_quality_status: {summary_value(rows, 'final_quality_status')}",
        f"review_areas: {summary_value(rows, 'review_areas')}",
        f"evidence_areas_present: {summary_value(rows, 'evidence_areas_present')}",
        f"top_outlier_dependency: {summary_value(rows, 'top_outlier_dependency')}",
        f"worst_drawdown_context: {summary_value(rows, 'worst_drawdown_context')}",
        f"largest_manual_review_blocker: {summary_value(rows, 'largest_manual_review_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; high_growth_promotion_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def load_quality_context(root: Path) -> QualityContext:
    rows_by_name = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    return QualityContext(root=root, rows_by_name=rows_by_name)


def build_review_rows(context: QualityContext) -> list[dict[str, Any]]:
    return [
        review_row(
            "concentration_quality",
            evidence_present(context, "drawdown_control_concentration", "component_contributions"),
            "concentration_outlier_manual_review_required",
            concentration_issue(context),
            "concentration_and_outlier_dependence_remain_manual_review_blockers",
            "manual_review_top_contributors_and_concentration_before_any_label_change",
            "treat_high_growth_as_diversified;approve_high_growth_promotion;create_order_instructions",
        ),
        review_row(
            "drawdown_quality",
            evidence_present(context, "drawdown_control_drawdowns", "drawdown_control_summary"),
            "drawdown_quality_manual_review_required",
            drawdown_issue(context),
            "drawdown_tail_risk_remains_manual_review_blocker",
            "manual_review_drawdown_control_and_broad_top1_tail_risk",
            "ignore_drawdown_risk;approve_preview_candidate;approve_paper_live_candidate",
        ),
        review_row(
            "attribution_quality",
            evidence_present(context, "component_attribution", "component_contributions", "component_drawdown_contributions"),
            "component_attribution_manual_review_required",
            attribution_issue(context),
            "top_contributor_and_drawdown_contributor_dependency_remain_manual_review_blockers",
            "manual_review_component_contribution_and_drawdown_dependency",
            "promote_without_component_attribution;create_action_preview;wire_high_growth_execution",
        ),
        review_row(
            "bias_risk_warnings",
            evidence_present(context, "manual_review_blockers", "risk_review_blockers", "drawdown_control_report"),
            "bias_risk_warnings_must_remain_visible",
            bias_issue(context),
            "survivorship_current_constituent_and_outlier_warnings_remain_blockers",
            "keep_bias_and_outlier_warnings_visible_in_future_reviews",
            "hide_bias_warning;hide_outlier_warning;label_high_growth_execution_ready",
        ),
        review_row(
            "promotion_readiness",
            evidence_present(context, "evidence_gap_summary"),
            "high_growth_research_only_not_promotion_ready",
            "Saved evidence may be present, but quality review does not approve preview, paper-live, execution, order instructions, or scheduling.",
            "high_growth_promotion_not_approved",
            NEXT_REVIEW,
            "approve_high_growth_promotion;approve_execution;approve_scheduling;wire_portfolio_execution",
        ),
    ]


def review_row(
    area: str,
    present: bool,
    quality_status: str,
    issue: str,
    blocker: str,
    allowed_next_action: str,
    forbidden_action: str,
) -> dict[str, Any]:
    return {
        "review_area": area,
        "evidence_present": present,
        "quality_status": quality_status if present else f"{quality_status}_saved_evidence_missing",
        "key_manual_review_issue": issue,
        "current_blocker": blocker,
        "allowed_next_action": allowed_next_action,
        "forbidden_action": forbidden_action,
        **ROW_SAFETY,
    }


def build_summary_rows(review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    present_count = sum(1 for row in review_rows if row.get("evidence_present") is True)
    return [
        summary_row("final_quality_status", QUALITY_STATUS, "Saved high-growth evidence is manual-review context only."),
        summary_row("review_areas", str(len(review_rows)), "Concentration, drawdown, attribution, bias-risk, and promotion-readiness quality were reviewed."),
        summary_row("evidence_areas_present", str(present_count), "Count of quality areas with at least one supporting saved CSV."),
        summary_row("top_outlier_dependency", first_issue(review_rows, "concentration_quality"), "Top contributor/outlier dependency context."),
        summary_row("worst_drawdown_context", first_issue(review_rows, "drawdown_quality"), "Drawdown-control and broad Top1 tail-risk context."),
        summary_row("largest_manual_review_blocker", "high_growth_quality_manual_review_required", "Quality review replaces missing-file blockers, but does not approve promotion."),
        summary_row("recommended_next_step", NEXT_REVIEW, "Review concentration, drawdown, attribution, bias, and portfolio-risk before any future promotion discussion."),
    ]


def build_blocker_rows(review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row(
            "high_growth_quality_manual_review_required",
            "manual_review_required",
            "high",
            "Saved evidence is present but concentration, drawdown, attribution, and bias-risk quality still require manual review.",
            NEXT_REVIEW,
        ),
        blocker_row(
            "high_growth_promotion_not_approved",
            "blocked",
            "critical",
            "High-growth remains research-only; no preview, paper-live, action preview, order instruction, execution, or scheduling approval is granted.",
            "Keep high-growth out of execution and scheduling paths.",
        ),
    ]
    for row in review_rows:
        rows.append(
            blocker_row(
                str(row.get("current_blocker", "")),
                "manual_review_required",
                "high",
                str(row.get("key_manual_review_issue", "")),
                str(row.get("allowed_next_action", "")),
            )
        )
    return rows


def build_evidence_rows(context: QualityContext, review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(
            "canonical_inputs_checked",
            ";".join(str(path) for path in INPUT_FILES.values()),
            "Only these saved high-growth CSVs are read; no market-data refresh or broker call is made.",
        ),
        evidence_row("rows_summarized_only", "true", "The report summarizes counts/status fields and does not dump full generated CSV contents."),
    ]
    for row in review_rows:
        rows.append(evidence_row(f"{row['review_area']}_issue", str(row["key_manual_review_issue"]), "Manual-review issue surfaced from saved context."))
    for name, rows_for_file in context.rows_by_name.items():
        rows.append(evidence_row(f"{name}_row_count", str(len(rows_for_file)), "Saved CSV row count only."))
    return rows


def concentration_issue(context: QualityContext) -> str:
    max_concentration = first_nonempty_value(
        context,
        ["drawdown_control_concentration", "component_attribution_summary", "component_streams_summary"],
        ["max_single_name_concentration", "top_1_dependency_share", "top1_dependency_share", "herfindahl_concentration"],
    )
    contributor = find_value_containing(context, ["drawdown_control_concentration", "component_contributions"], "TSLA") or first_nonempty_value(
        context,
        ["drawdown_control_concentration", "component_contributions"],
        ["largest_contributor", "top_contributor_ticker", "component_ticker", "ticker"],
    )
    warning = warning_summary(context)
    return f"top_contributor={contributor}; max_single_name_concentration={max_concentration}; warnings={warning}"


def drawdown_issue(context: QualityContext) -> str:
    worst_drawdown = min_numeric_value(
        context,
        ["drawdown_control_drawdowns", "drawdown_control_report"],
        ["max_drawdown", "max_drawdown_pct", "drawdown_pct", "worst_drawdown"],
    )
    candidate = first_nonempty_value(context, ["drawdown_control_summary"], ["best_drawdown_control_candidate", "best_candidate", "summary_value"])
    conclusion = find_value_containing(context, ["drawdown_control_summary", "drawdown_control_report"], "high_growth_stock_outlier_dependent")
    return f"best_candidate={candidate}; worst_drawdown={worst_drawdown}; conclusion={conclusion or 'manual_review_required'}"


def attribution_issue(context: QualityContext) -> str:
    contributor = find_value_containing(context, ["component_contributions", "component_drawdown_contributions"], "TSLA") or first_nonempty_value(
        context,
        ["component_contributions", "component_drawdown_contributions"],
        ["component_ticker", "ticker", "top_contributor_ticker"],
    )
    contribution = first_nonempty_value(
        context,
        ["component_contributions", "component_drawdown_contributions"],
        ["weighted_contribution", "component_weighted_contribution", "contribution_share_of_high_growth_drawdown"],
    )
    return f"component_dependency={contributor}; contribution_context={contribution}; manual_review_required_before_label_change"


def bias_issue(context: QualityContext) -> str:
    return warning_summary(context)


def warning_summary(context: QualityContext) -> str:
    warnings = []
    for token in ["survivorship_bias_warning", "current_constituent_bias_warning", "outlier_dependence_warning", "concentration_risk"]:
        value = first_nonempty_value(context, list(context.rows_by_name), [token])
        if value:
            warnings.append(f"{token}={value}")
    if not warnings and find_value_containing(context, list(context.rows_by_name), "survivorship"):
        warnings.append("survivorship_warning_visible")
    if not warnings:
        warnings.append("bias_and_concentration_warnings_manual_review_required")
    return ";".join(warnings)


def evidence_present(context: QualityContext, *names: str) -> bool:
    return any(bool(context.rows_by_name.get(name)) for name in names)


def first_issue(rows: list[dict[str, Any]], area: str) -> str:
    for row in rows:
        if row.get("review_area") == area:
            return str(row.get("key_manual_review_issue", ""))
    return "unavailable"


def first_nonempty_value(context: QualityContext, source_names: list[str], columns: list[str]) -> str:
    for source_name in source_names:
        for row in context.rows_by_name.get(source_name, []):
            for column in columns:
                value = str(row.get(column, "")).strip()
                if value:
                    return value
    return "unavailable"


def find_value_containing(context: QualityContext, source_names: list[str], token: str) -> str:
    token_lower = token.lower()
    for source_name in source_names:
        for row in context.rows_by_name.get(source_name, []):
            for value in row.values():
                text = str(value).strip()
                if token_lower in text.lower():
                    return text
    return ""


def min_numeric_value(context: QualityContext, source_names: list[str], columns: list[str]) -> str:
    values: list[float] = []
    for source_name in source_names:
        for row in context.rows_by_name.get(source_name, []):
            for column in columns:
                value = parse_float(row.get(column, ""))
                if value is not None:
                    values.append(value)
    return str(round(min(values), 4)) if values else "unavailable"


def parse_float(value: str) -> float | None:
    try:
        return float(str(value).strip().replace("%", ""))
    except (TypeError, ValueError):
        return None


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live high-growth evidence quality review complete. Saved-output/manual-review only; no promotion, execution, orders, or scheduling approved.",
        f"final_quality_status={summary_value(summary_rows, 'final_quality_status')}",
        f"review_areas={summary_value(summary_rows, 'review_areas')}",
        f"evidence_areas_present={summary_value(summary_rows, 'evidence_areas_present')}",
        f"top_outlier_dependency={summary_value(summary_rows, 'top_outlier_dependency')}",
        f"worst_drawdown_context={summary_value(summary_rows, 'worst_drawdown_context')}",
        f"largest_manual_review_blocker={summary_value(summary_rows, 'largest_manual_review_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['review']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; high_growth_promotion_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return "unavailable"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
