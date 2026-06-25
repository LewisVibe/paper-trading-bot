"""Report-only defensive sleeve ladder-scope review.

This checkpoint reviews whether the defensive sleeve has enough saved evidence
for a future paper-live ladder candidate discussion. It reads saved-output file
presence only. It does not rerun research, refresh market data, call Alpaca,
read positions, create order instructions, schedule anything, or approve
promotion/execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFENSIVE_EVIDENCE_FILES = {
    "defensive_strategy_report": Path("data/defensive_strategy_report.csv"),
    "defensive_candidate_comparison": Path("data/defensive_candidate_comparison.csv"),
    "defensive_research_state": Path("data/defensive_research_state_report.csv"),
    "defensive_allocation_preview": Path("data/defensive_allocation_preview.csv"),
    "defensive_allocation_risk_preview": Path("data/defensive_allocation_risk_preview.csv"),
    "defensive_allocation_decision": Path("data/defensive_allocation_decision_report.csv"),
    "etf_defensive_drawdown_comparison": Path("data/etf_defensive_drawdown_comparison.csv"),
    "vol_managed_robustness": Path("data/vol_managed_etf_robustness.csv"),
    "defensive_refresh_summary": Path("data/defensive_research_refresh_summary.csv"),
}

OUTPUT_FILES = {
    "report": Path("data/paper_live_defensive_sleeve_ladder_scope_review.csv"),
    "summary": Path("data/paper_live_defensive_sleeve_ladder_scope_review_summary.csv"),
    "blockers": Path("data/paper_live_defensive_sleeve_ladder_scope_review_blockers.csv"),
    "evidence": Path("data/paper_live_defensive_sleeve_ladder_scope_review_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "promotion_approved": False,
    "portfolio_backtest_promotion_evidence_approved": False,
    "defensive_sleeve_promoted": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "scope_review_only": True,
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
    "review_item",
    "review_status",
    "risk_level",
    "evidence",
    "required_next_step",
    "research_only",
    "report_only",
    "scope_review_only",
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
class DefensiveScopeContext:
    present_files: list[str]
    missing_files: list[str]
    evidence_file_count: int
    final_status: str
    largest_blocker: str
    recommended_next_step: str


@dataclass
class DefensiveScopeReviewResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_defensive_sleeve_ladder_scope_review(root_dir: Path | str = ".") -> DefensiveScopeReviewResult:
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
    return DefensiveScopeReviewResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_defensive_sleeve_ladder_scope_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live defensive sleeve ladder-scope review is missing.",
            "Run `python bot.py --paper-live-defensive-sleeve-ladder-scope-review` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live defensive sleeve ladder-scope review saved display. Report only; no promotion or orders approved.",
        f"final_defensive_scope_status: {summary_value(rows, 'final_defensive_scope_status')}",
        f"candidate_scope: {summary_value(rows, 'candidate_scope')}",
        f"saved_defensive_evidence_status: {summary_value(rows, 'saved_defensive_evidence_status')}",
        f"present_evidence_count: {summary_value(rows, 'present_evidence_count')}",
        f"missing_evidence_count: {summary_value(rows, 'missing_evidence_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; promotion_approved=false; defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_context(root: Path) -> DefensiveScopeContext:
    present = [name for name, path in DEFENSIVE_EVIDENCE_FILES.items() if (root / path).exists()]
    missing = [name for name, path in DEFENSIVE_EVIDENCE_FILES.items() if not (root / path).exists()]
    if missing:
        final_status = "defensive_sleeve_ladder_scope_missing_saved_evidence_manual_review_required"
        largest_blocker = "missing_saved_defensive_evidence"
        recommended_next_step = "refresh_or_create_missing_defensive_saved_reports_before_candidate_discussion"
    else:
        final_status = "defensive_sleeve_ladder_scope_review_ready_for_manual_review"
        largest_blocker = "manual_review_required_before_defensive_candidate_discussion"
        recommended_next_step = "manual_review_defensive_sleeve_scope_before_any_candidate_label_change"
    return DefensiveScopeContext(
        present_files=present,
        missing_files=missing,
        evidence_file_count=len(present),
        final_status=final_status,
        largest_blocker=largest_blocker,
        recommended_next_step=recommended_next_step,
    )


def build_report_rows(context: DefensiveScopeContext) -> list[dict[str, Any]]:
    rows = [
        (
            "defensive_scope_selection",
            "defensive_sleeve_selected_for_report_only_review",
            "medium",
            "Defensive sleeve is the next conservative review scope after QQQ100.",
            "review saved defensive evidence before candidate discussion",
        ),
        (
            "saved_defensive_evidence",
            "complete" if not context.missing_files else "missing_saved_evidence",
            "high" if context.missing_files else "medium",
            "present=" + ";".join(context.present_files) + " missing=" + ";".join(context.missing_files),
            context.recommended_next_step,
        ),
        (
            "promotion_boundary",
            "defensive_sleeve_not_promoted",
            "critical",
            "This report does not promote the defensive sleeve or create order instructions.",
            "keep promotion_approved false",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "No execution, paper execution, scheduling, or live trading is approved.",
            "do not run order-capable commands",
        ),
    ]
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


def build_summary_rows(context: DefensiveScopeContext) -> list[dict[str, Any]]:
    saved_status = "complete" if not context.missing_files else "missing_saved_evidence"
    rows = [
        ("final_defensive_scope_status", context.final_status, "Current defensive sleeve ladder-scope status."),
        ("candidate_scope", "defensive_sleeve", "Defensive sleeve is the scoped branch under report-only review."),
        ("saved_defensive_evidence_status", saved_status, "Saved defensive evidence file presence status."),
        ("present_evidence_count", str(len(context.present_files)), "Count of expected defensive evidence files present."),
        ("missing_evidence_count", str(len(context.missing_files)), "Count of expected defensive evidence files missing."),
        ("present_evidence_files", ";".join(context.present_files) or "none", "Expected defensive evidence files present."),
        ("missing_evidence_files", ";".join(context.missing_files) or "none", "Expected defensive evidence files missing."),
        ("largest_blocker", context.largest_blocker, "Largest blocker before candidate discussion."),
        ("recommended_next_step", context.recommended_next_step, "Next step remains report/manual review only."),
        ("promotion_approved", "False", "Promotion approval remains false."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("defensive_sleeve_promoted", "False", "Defensive sleeve is not promoted."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(context: DefensiveScopeContext) -> list[dict[str, Any]]:
    blockers = [
        ("promotion_not_approved", "blocked", "critical", "This review does not approve defensive sleeve promotion.", "Do not promote the defensive sleeve."),
        ("execution_not_approved", "blocked", "critical", "This review does not approve execution or paper execution.", "Do not run order-capable commands."),
        ("scheduling_not_approved", "blocked", "critical", "Order-capable commands must not be scheduled.", "Keep Hermes/VPS monitoring-only."),
    ]
    if context.missing_files:
        blockers.insert(
            0,
            (
                "missing_saved_defensive_evidence",
                "manual_review_required",
                "high",
                "Missing saved defensive evidence files: " + ";".join(context.missing_files),
                "refresh_or_create_missing_defensive_saved_reports_before_candidate_discussion",
            ),
        )
    else:
        blockers.insert(
            0,
            (
                "manual_review_required_before_candidate_discussion",
                "manual_review_required",
                "high",
                "Saved defensive evidence files are present, but candidate discussion still requires manual review.",
                "manual_review_defensive_sleeve_scope_before_any_candidate_label_change",
            ),
        )
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows(context: DefensiveScopeContext) -> list[dict[str, Any]]:
    rows = [
        ("evidence_files_present", str(len(context.present_files)), ";".join(context.present_files) or "none"),
        ("evidence_files_missing", str(len(context.missing_files)), ";".join(context.missing_files) or "none"),
        ("scope_boundary", "report_only", "Defensive sleeve scope review does not approve promotion."),
        ("approval_flags", "all_false", "Execution, paper execution, scheduling, live trading, promotion, and defensive promotion approvals remain false."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live defensive sleeve ladder-scope review complete. Report only; no promotion, orders, or scheduling approved.",
        f"final_defensive_scope_status={summary_value(summary_rows, 'final_defensive_scope_status')}",
        f"candidate_scope={summary_value(summary_rows, 'candidate_scope')}",
        f"saved_defensive_evidence_status={summary_value(summary_rows, 'saved_defensive_evidence_status')}",
        f"present_evidence_count={summary_value(summary_rows, 'present_evidence_count')}",
        f"missing_evidence_count={summary_value(summary_rows, 'missing_evidence_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; promotion_approved=false; defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return "unavailable"


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
