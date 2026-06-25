"""Saved-output preview-readiness checkpoint for the defensive sleeve.

This report reads saved manual-review evidence only. It does not promote the
defensive sleeve, create order instructions, call Alpaca, read positions,
refresh market data, write trade logs, send alerts, schedule anything, or
approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MANUAL_REVIEW_SUMMARY = Path("data/paper_live_defensive_sleeve_manual_review_summary.csv")
SCOPE_SUMMARY = Path("data/paper_live_defensive_sleeve_ladder_scope_review_summary.csv")

OUTPUT_FILES = {
    "report": Path("data/paper_live_defensive_sleeve_preview_readiness.csv"),
    "summary": Path("data/paper_live_defensive_sleeve_preview_readiness_summary.csv"),
    "blockers": Path("data/paper_live_defensive_sleeve_preview_readiness_blockers.csv"),
    "evidence": Path("data/paper_live_defensive_sleeve_preview_readiness_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "promotion_approved": False,
    "preview_candidate_approved": False,
    "defensive_sleeve_promoted": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "preview_readiness_only": True,
    "saved_output_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
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

REPORT_COLUMNS = [
    "readiness_item",
    "readiness_status",
    "risk_level",
    "evidence",
    "required_next_step",
    "research_only",
    "report_only",
    "preview_readiness_only",
    "saved_output_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
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


@dataclass(frozen=True)
class DefensivePreviewReadinessContext:
    manual_review_status: str
    scope_status: str
    preferred_candidate: str
    final_status: str
    largest_blocker: str
    recommended_next_step: str


@dataclass
class DefensivePreviewReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_defensive_sleeve_preview_readiness(root_dir: Path | str = ".") -> DefensivePreviewReadinessResult:
    root = Path(root_dir)
    context = build_context(root)
    report_rows = build_report_rows(context)
    summary_rows = build_summary_rows(context)
    blocker_rows = build_blocker_rows(context)
    evidence_rows = build_evidence_rows(context)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return DefensivePreviewReadinessResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_defensive_sleeve_preview_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live defensive sleeve preview readiness is missing.",
            "Run `python bot.py --paper-live-defensive-sleeve-preview-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live defensive sleeve preview readiness saved display. Report only; no promotion or orders approved.",
        f"final_preview_readiness_status: {summary_value(rows, 'final_preview_readiness_status')}",
        f"candidate_scope: {summary_value(rows, 'candidate_scope')}",
        f"preferred_defensive_candidate: {summary_value(rows, 'preferred_defensive_candidate')}",
        f"manual_review_status: {summary_value(rows, 'manual_review_status')}",
        f"preview_candidate_status: {summary_value(rows, 'preview_candidate_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; promotion_approved=false; preview_candidate_approved=false; defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_context(root: Path) -> DefensivePreviewReadinessContext:
    manual_rows = read_csv_rows(root / MANUAL_REVIEW_SUMMARY)
    scope_rows = read_csv_rows(root / SCOPE_SUMMARY)
    manual_status = summary_value(manual_rows, "final_manual_review_status") or "missing_manual_review"
    scope_status = summary_value(scope_rows, "final_defensive_scope_status") or "missing_scope_review"
    preferred = summary_value(manual_rows, "preferred_defensive_candidate") or "missing_saved_candidate_context"

    if manual_status == "defensive_sleeve_manual_review_required":
        final_status = "defensive_sleeve_preview_candidate_not_approved_manual_review_required"
        largest_blocker = "manual_decision_required_before_defensive_preview_candidate_label"
        recommended_next_step = "keep_defensive_sleeve_research_only_until_manual_candidate_decision"
    else:
        final_status = "defensive_sleeve_preview_readiness_blocked_missing_manual_review"
        largest_blocker = "missing_or_incomplete_defensive_manual_review"
        recommended_next_step = "run_defensive_sleeve_manual_review_before_preview_readiness"

    return DefensivePreviewReadinessContext(
        manual_review_status=manual_status,
        scope_status=scope_status,
        preferred_candidate=preferred,
        final_status=final_status,
        largest_blocker=largest_blocker,
        recommended_next_step=recommended_next_step,
    )


def build_report_rows(context: DefensivePreviewReadinessContext) -> list[dict[str, Any]]:
    rows = [
        (
            "clean_lead_boundary",
            "qqq100_clean_lead_retained",
            "critical",
            "qqq_100_trend_gate remains the only paper-live monitoring base.",
            "do not replace QQQ100 with a defensive sleeve",
        ),
        (
            "manual_review_dependency",
            context.manual_review_status,
            "high",
            f"scope_status={context.scope_status}; candidate={context.preferred_candidate}",
            "manual_review_required_before_preview_candidate_label",
        ),
        (
            "preview_candidate_status",
            "defensive_preview_candidate_not_approved",
            "critical",
            "Saved evidence can support discussion, but no preview candidate label is approved here.",
            context.recommended_next_step,
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "No execution, paper execution, repeat order, scheduling, or live trading is approved.",
            "keep all order-capable commands separate and unscheduled",
        ),
        (
            "portfolio_role",
            "defensive_sleeve_research_only",
            "high",
            "Defensive sleeve may be a future sleeve candidate only after manual review, not a main-strategy replacement.",
            "review sleeve role, return drag, drawdown benefit, and allocation policy separately",
        ),
    ]
    return [
        {
            "readiness_item": item,
            "readiness_status": status,
            "risk_level": risk,
            "evidence": evidence,
            "required_next_step": next_step,
            **ROW_SAFETY,
        }
        for item, status, risk, evidence, next_step in rows
    ]


def build_summary_rows(context: DefensivePreviewReadinessContext) -> list[dict[str, Any]]:
    rows = [
        ("final_preview_readiness_status", context.final_status, "Current defensive preview-readiness status."),
        ("candidate_scope", "defensive_sleeve", "Defensive sleeve is the reviewed branch."),
        ("preferred_defensive_candidate", context.preferred_candidate, "Saved preferred defensive candidate context."),
        ("manual_review_status", context.manual_review_status, "Manual review pack status."),
        ("scope_review_status", context.scope_status, "Saved ladder-scope status."),
        ("preview_candidate_status", "defensive_preview_candidate_not_approved", "No defensive preview candidate is approved."),
        ("clean_paper_live_lead", "qqq_100_trend_gate", "QQQ100 remains the clean paper-live monitoring base."),
        ("defensive_sleeve_research_status", "defensive_sleeve_research_only", "Defensive sleeve remains research-only."),
        ("largest_blocker", context.largest_blocker, "Largest blocker before any defensive preview label."),
        ("recommended_next_step", context.recommended_next_step, "Next step remains manual review/report-only."),
        ("promotion_approved", "False", "Promotion approval remains false."),
        ("preview_candidate_approved", "False", "Preview candidate approval remains false."),
        ("defensive_sleeve_promoted", "False", "Defensive sleeve is not promoted."),
        ("execution_approved", "False", "Execution approval remains false."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(context: DefensivePreviewReadinessContext) -> list[dict[str, Any]]:
    rows = [
        ("manual_decision_required_before_preview_label", "manual_review_required", "high", "A human review must decide whether this sleeve deserves preview-candidate work.", "keep_defensive_sleeve_research_only_until_manual_candidate_decision"),
        ("preview_candidate_not_approved", "blocked", "critical", "This checkpoint does not approve defensive preview implementation.", "do not add action previews or order instructions"),
        ("execution_not_approved", "blocked", "critical", "No paper/live execution is approved.", "do not run order-capable commands"),
        ("scheduling_not_approved", "blocked", "critical", "Order-capable commands must not be scheduled.", "keep Hermes/VPS monitoring-only"),
    ]
    if context.manual_review_status != "defensive_sleeve_manual_review_required":
        rows.insert(0, ("missing_manual_review", "manual_review_required", "high", "Defensive manual review summary is missing or incomplete.", "run_defensive_sleeve_manual_review_before_preview_readiness"))
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in rows
    ]


def build_evidence_rows(context: DefensivePreviewReadinessContext) -> list[dict[str, Any]]:
    rows = [
        ("manual_review_status", context.manual_review_status, "Saved manual review dependency."),
        ("scope_review_status", context.scope_status, "Saved defensive scope status."),
        ("preferred_candidate", context.preferred_candidate, "Saved candidate context only."),
        ("approval_flags", "all_false", "Execution, paper execution, scheduling, live trading, promotion, preview, and defensive promotion approvals remain false."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live defensive sleeve preview readiness complete. Report only; no promotion, orders, or scheduling approved.",
        f"final_preview_readiness_status={summary_value(summary_rows, 'final_preview_readiness_status')}",
        f"candidate_scope={summary_value(summary_rows, 'candidate_scope')}",
        f"preferred_defensive_candidate={summary_value(summary_rows, 'preferred_defensive_candidate')}",
        f"manual_review_status={summary_value(summary_rows, 'manual_review_status')}",
        f"preview_candidate_status={summary_value(summary_rows, 'preview_candidate_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; promotion_approved=false; preview_candidate_approved=false; defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
