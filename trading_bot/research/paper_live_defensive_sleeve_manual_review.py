"""Saved-output manual review pack for the defensive sleeve.

This checkpoint reads saved defensive evidence only. It does not refresh market
data, call Alpaca, read positions, create order instructions, schedule
anything, or approve promotion/execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCOPE_SUMMARY = Path("data/paper_live_defensive_sleeve_ladder_scope_review_summary.csv")
DEFENSIVE_COMPARISON = Path("data/defensive_candidate_comparison.csv")
DEFENSIVE_RESEARCH_STATE = Path("data/defensive_research_state_report.csv")
DEFENSIVE_ALLOCATION_DECISION = Path("data/defensive_allocation_decision_report.csv")
DEFENSIVE_DRAWDOWN_COMPARISON = Path("data/etf_defensive_drawdown_comparison.csv")
VOL_MANAGED_ROBUSTNESS = Path("data/vol_managed_etf_robustness_report.csv")
REFRESH_SUMMARY = Path("data/defensive_research_refresh_summary.csv")

OUTPUT_FILES = {
    "report": Path("data/paper_live_defensive_sleeve_manual_review.csv"),
    "summary": Path("data/paper_live_defensive_sleeve_manual_review_summary.csv"),
    "blockers": Path("data/paper_live_defensive_sleeve_manual_review_blockers.csv"),
    "evidence": Path("data/paper_live_defensive_sleeve_manual_review_evidence.csv"),
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
    "saved_output_only": True,
    "manual_review_only": True,
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
    "review_item",
    "review_status",
    "risk_level",
    "evidence",
    "required_next_step",
    "research_only",
    "report_only",
    "saved_output_only",
    "manual_review_only",
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
class DefensiveManualReviewContext:
    scope_status: str
    saved_evidence_status: str
    preferred_candidate: str
    allocation_decision: str
    evidence_files_present: list[str]
    evidence_files_missing: list[str]
    final_status: str
    largest_blocker: str
    recommended_next_step: str


@dataclass
class DefensiveManualReviewResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_defensive_sleeve_manual_review(root_dir: Path | str = ".") -> DefensiveManualReviewResult:
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
    return DefensiveManualReviewResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_defensive_sleeve_manual_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live defensive sleeve manual review is missing.",
            "Run `python bot.py --paper-live-defensive-sleeve-manual-review` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live defensive sleeve manual review saved display. Report only; no promotion or orders approved.",
        f"final_manual_review_status: {summary_value(rows, 'final_manual_review_status')}",
        f"candidate_scope: {summary_value(rows, 'candidate_scope')}",
        f"preferred_defensive_candidate: {summary_value(rows, 'preferred_defensive_candidate')}",
        f"clean_paper_live_lead: {summary_value(rows, 'clean_paper_live_lead')}",
        f"saved_defensive_evidence_status: {summary_value(rows, 'saved_defensive_evidence_status')}",
        f"preview_discussion_status: {summary_value(rows, 'preview_discussion_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; promotion_approved=false; preview_candidate_approved=false; defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_context(root: Path) -> DefensiveManualReviewContext:
    scope_summary = read_csv_rows(root / SCOPE_SUMMARY)
    scope_status = summary_value(scope_summary, "final_defensive_scope_status") or "missing_scope_review"
    saved_status = summary_value(scope_summary, "saved_defensive_evidence_status") or "missing_saved_evidence"

    evidence_files = {
        "scope_summary": SCOPE_SUMMARY,
        "defensive_candidate_comparison": DEFENSIVE_COMPARISON,
        "defensive_research_state": DEFENSIVE_RESEARCH_STATE,
        "defensive_allocation_decision": DEFENSIVE_ALLOCATION_DECISION,
        "defensive_drawdown_comparison": DEFENSIVE_DRAWDOWN_COMPARISON,
        "vol_managed_robustness": VOL_MANAGED_ROBUSTNESS,
        "defensive_refresh_summary": REFRESH_SUMMARY,
    }
    present = [name for name, path in evidence_files.items() if (root / path).exists()]
    missing = [name for name, path in evidence_files.items() if not (root / path).exists()]
    preferred = find_preferred_candidate(root / DEFENSIVE_COMPARISON)
    allocation_decision = find_allocation_decision(root / DEFENSIVE_ALLOCATION_DECISION)

    if saved_status == "complete" and not missing:
        final_status = "defensive_sleeve_manual_review_required"
        largest_blocker = "manual_review_required_before_defensive_preview_discussion"
        recommended_next_step = "create_defensive_sleeve_preview_readiness_checkpoint"
    else:
        final_status = "defensive_sleeve_manual_review_blocked_missing_saved_evidence"
        largest_blocker = "missing_saved_defensive_evidence"
        recommended_next_step = "regenerate_defensive_saved_reports_before_manual_review"

    return DefensiveManualReviewContext(
        scope_status=scope_status,
        saved_evidence_status=saved_status,
        preferred_candidate=preferred,
        allocation_decision=allocation_decision,
        evidence_files_present=present,
        evidence_files_missing=missing,
        final_status=final_status,
        largest_blocker=largest_blocker,
        recommended_next_step=recommended_next_step,
    )


def build_report_rows(context: DefensiveManualReviewContext) -> list[dict[str, Any]]:
    rows = [
        (
            "qqq100_boundary",
            "clean_paper_live_lead_unchanged",
            "critical",
            "qqq_100_trend_gate remains the only current paper-live monitoring base.",
            "do not replace QQQ100 with a defensive sleeve without separate approval",
        ),
        (
            "defensive_branch_status",
            "defensive_sleeve_research_branch_manual_review_required",
            "high",
            f"scope_status={context.scope_status}; saved_evidence={context.saved_evidence_status}",
            context.recommended_next_step,
        ),
        (
            "candidate_context",
            "preferred_defensive_candidate_saved_context",
            "medium",
            f"preferred_candidate={context.preferred_candidate}; allocation_decision={context.allocation_decision}",
            "review return/drawdown role before any preview label",
        ),
        (
            "return_drawdown_tradeoff",
            "defensive_tradeoff_review_required",
            "high",
            "Defensive drawdown and robustness evidence is present only as saved research context.",
            "manual_review_return_drag_drawdown_benefit_and_portfolio_role",
        ),
        (
            "preview_boundary",
            "preview_discussion_not_approved_manual_review_required",
            "critical",
            "This manual review pack does not approve a preview candidate label.",
            "run preview readiness checkpoint after manual review pack",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "No execution, paper execution, repeat order, scheduling, or live trading is approved.",
            "keep order-capable commands separate and unscheduled",
        ),
    ]
    if context.evidence_files_missing:
        rows.insert(
            1,
            (
                "missing_saved_evidence",
                "missing_saved_defensive_evidence",
                "high",
                "missing=" + ";".join(context.evidence_files_missing),
                "regenerate_defensive_saved_reports_before_manual_review",
            ),
        )
    return [
        {
            "review_item": item,
            "review_status": status,
            "risk_level": risk,
            "evidence": evidence,
            "required_next_step": next_step,
            **ROW_SAFETY,
        }
        for item, status, risk, evidence, next_step in rows
    ]


def build_summary_rows(context: DefensiveManualReviewContext) -> list[dict[str, Any]]:
    rows = [
        ("final_manual_review_status", context.final_status, "Current defensive manual review status."),
        ("candidate_scope", "defensive_sleeve", "Defensive sleeve is under saved-output manual review."),
        ("clean_paper_live_lead", "qqq_100_trend_gate", "QQQ100 remains the clean paper-live monitoring base."),
        ("preferred_defensive_candidate", context.preferred_candidate, "Saved preferred defensive candidate context."),
        ("saved_defensive_evidence_status", context.saved_evidence_status, "Saved defensive evidence status from ladder-scope review."),
        ("present_evidence_files", ";".join(context.evidence_files_present) or "none", "Saved evidence inputs present."),
        ("missing_evidence_files", ";".join(context.evidence_files_missing) or "none", "Saved evidence inputs missing."),
        ("allocation_decision_status", context.allocation_decision, "Saved defensive allocation decision context."),
        ("preview_discussion_status", "preview_discussion_not_approved_manual_review_required", "Preview discussion is not approved by this pack."),
        ("execution_status", "execution_blocked", "Execution remains blocked."),
        ("largest_blocker", context.largest_blocker, "Largest blocker before preview discussion."),
        ("recommended_next_step", context.recommended_next_step, "Next step remains report-only."),
        ("promotion_approved", "False", "Promotion approval remains false."),
        ("preview_candidate_approved", "False", "Preview candidate approval remains false."),
        ("defensive_sleeve_promoted", "False", "Defensive sleeve is not promoted."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(context: DefensiveManualReviewContext) -> list[dict[str, Any]]:
    blockers = [
        ("manual_review_required_before_preview_discussion", "manual_review_required", "high", "Defensive sleeve evidence can be discussed, but not promoted.", "complete manual review before preview readiness can change labels"),
        ("preview_candidate_not_approved", "blocked", "critical", "No defensive preview candidate is approved by this pack.", "keep preview_candidate_approved false"),
        ("execution_not_approved", "blocked", "critical", "No paper/live execution is approved.", "do not run order-capable commands"),
        ("scheduling_not_approved", "blocked", "critical", "Order-capable commands must not be scheduled.", "keep Hermes/VPS monitoring-only"),
    ]
    if context.evidence_files_missing:
        blockers.insert(0, ("missing_saved_defensive_evidence", "manual_review_required", "high", "Missing saved evidence: " + ";".join(context.evidence_files_missing), "regenerate_defensive_saved_reports_before_manual_review"))
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows(context: DefensiveManualReviewContext) -> list[dict[str, Any]]:
    rows = [
        ("scope_review_status", context.scope_status, "Saved defensive ladder-scope status."),
        ("saved_evidence_status", context.saved_evidence_status, "Saved defensive evidence completeness status."),
        ("preferred_candidate", context.preferred_candidate, "Saved defensive candidate context, not a promotion."),
        ("allocation_decision_status", context.allocation_decision, "Saved defensive allocation decision context."),
        ("approval_flags", "all_false", "Execution, paper execution, scheduling, live trading, promotion, and preview approvals remain false."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live defensive sleeve manual review complete. Report only; no promotion, orders, or scheduling approved.",
        f"final_manual_review_status={summary_value(summary_rows, 'final_manual_review_status')}",
        f"candidate_scope={summary_value(summary_rows, 'candidate_scope')}",
        f"clean_paper_live_lead={summary_value(summary_rows, 'clean_paper_live_lead')}",
        f"preferred_defensive_candidate={summary_value(summary_rows, 'preferred_defensive_candidate')}",
        f"saved_defensive_evidence_status={summary_value(summary_rows, 'saved_defensive_evidence_status')}",
        f"preview_discussion_status={summary_value(summary_rows, 'preview_discussion_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; promotion_approved=false; preview_candidate_approved=false; defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]


def find_preferred_candidate(path: Path) -> str:
    rows = read_csv_rows(path)
    for row in rows:
        text = " ".join(str(value) for value in row.values())
        if "preferred_defensive_candidate" in text:
            for value in row.values():
                value_text = str(value).strip()
                if value_text and value_text not in {"preferred_defensive_candidate", "research_only"}:
                    if "volatility" in value_text or "momentum" in value_text or "rotation" in value_text:
                        return value_text
    if rows:
        text = " ".join(" ".join(str(value) for value in row.values()) for row in rows)
        if "volatility_managed_dual_momentum_etf" in text:
            return "volatility_managed_dual_momentum_etf"
        if "monthly_etf_momentum_rotation" in text:
            return "monthly_etf_momentum_rotation"
    return "missing_saved_candidate_context"


def find_allocation_decision(path: Path) -> str:
    rows = read_csv_rows(path)
    for row in rows:
        for value in row.values():
            value_text = str(value).strip()
            if value_text in {"missing_input", "blocked", "manual_review_required", "ready_for_manual_review"}:
                return value_text
    return "missing_saved_allocation_decision" if not rows else "saved_allocation_decision_present"


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
