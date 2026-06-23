"""Report-only F6/F7 audit for future paper-live promotion work.

This checkpoint statically reviews saved-output/report code for two remaining
external-review items. It does not call Alpaca, read live positions, refresh
market data, write SQLite, send alerts, schedule anything, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "report": Path("data/paper_live_f6_f7_audit.csv"),
    "summary": Path("data/paper_live_f6_f7_audit_summary.csv"),
    "blockers": Path("data/paper_live_f6_f7_audit_blockers.csv"),
    "evidence": Path("data/paper_live_f6_f7_audit_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "audit_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "audit_item",
    "review_finding",
    "severity",
    "affected_area",
    "current_status",
    "future_action_required",
    "evidence",
    "research_only",
    "report_only",
    "audit_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "alpaca_called",
    "live_positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_FLAGS.keys(),
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_value",
    "details",
    *SAFETY_FLAGS.keys(),
]


@dataclass(frozen=True)
class AuditRow:
    audit_item: str
    review_finding: str
    severity: str
    affected_area: str
    current_status: str
    future_action_required: str
    evidence: str


@dataclass
class PaperLiveF6F7AuditResult:
    output_paths: dict[str, Path]
    audit_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_f6_f7_audit(root_dir: Path | str = ".") -> PaperLiveF6F7AuditResult:
    root = Path(root_dir)
    audit = build_audit_rows(root)
    audit_rows = [row_to_dict(row) for row in audit]
    summary_rows = build_summary_rows(audit)
    blocker_rows = build_blocker_rows(audit)
    evidence_rows = build_evidence_rows(audit)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, audit_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveF6F7AuditResult(
        output_paths=output_paths,
        audit_rows=audit_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_f6_f7_audit(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live F6/F7 audit is missing.",
            "Run `python bot.py --paper-live-f6-f7-audit` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live F6/F7 audit saved display. Report only; no orders approved.",
        f"final_audit_status: {summary_value(rows, 'final_audit_status')}",
        f"f6_position_unknown_status: {summary_value(rows, 'f6_position_unknown_status')}",
        f"f7_accounting_status: {summary_value(rows, 'f7_accounting_status')}",
        f"needs_manual_review_count: {summary_value(rows, 'needs_manual_review_count')}",
        f"future_fix_required_count: {summary_value(rows, 'future_fix_required_count')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_audit_rows(root: Path) -> list[AuditRow]:
    source = SourceBundle(root)
    rows = [
        audit_qqq100_action_preview(source),
        audit_promoted_actions(source),
        audit_promoted_risk(source),
        audit_multi_strategy_preview(source),
        audit_multi_sleeve_backtest_accounting(source),
        audit_sleeve_return_stream_accounting(source),
        audit_portfolio_promotion_boundary(source),
    ]
    return rows


def audit_qqq100_action_preview(source: "SourceBundle") -> AuditRow:
    text = source.read("trading_bot/research/qqq100_action_preview.py")
    if all(token in text for token in ["position_not_read", "position_context_unavailable", "manual_review_required_position_unavailable"]):
        return AuditRow(
            "F6_position_unknown_not_assumed_flat",
            "no_issue_found",
            "medium",
            "qqq100_action_preview",
            "position_unknown_or_position_unavailable_is_loud_not_assumed_flat",
            "keep_verifier_coverage_before_future_preview_or_execution_changes",
            "qqq100_action_preview uses position_not_read / position_context_unavailable and manual_review_required_position_unavailable.",
        )
    return AuditRow(
        "F6_position_unknown_not_assumed_flat",
        "needs_manual_review",
        "high",
        "qqq100_action_preview",
        "insufficient_static_evidence",
        "review QQQ100 action preview before future promotion work",
        "Expected loud unknown-position labels were not all found.",
    )


def audit_promoted_actions(source: "SourceBundle") -> AuditRow:
    text = source.read("trading_bot/research/promoted_actions.py")
    if "position_unavailable" in text and "current_position" in text:
        return AuditRow(
            "F6_promoted_actions_position_unavailable",
            "no_issue_found",
            "medium",
            "promoted_actions_preview",
            "position_unavailable_is_preserved_not_assumed_flat",
            "keep position_unavailable rows loud in any future promotion ladder",
            "promoted_actions contains position_unavailable handling for unavailable position context.",
        )
    return AuditRow(
        "F6_promoted_actions_position_unavailable",
        "needs_manual_review",
        "high",
        "promoted_actions_preview",
        "insufficient_static_evidence",
        "review promoted actions before generic promotion ladder work",
        "Could not confirm position_unavailable preservation statically.",
    )


def audit_promoted_risk(source: "SourceBundle") -> AuditRow:
    text = source.read("trading_bot/research/promoted_risk.py")
    if "do not assume flat" in text.lower() and "position_unavailable" in text:
        return AuditRow(
            "F6_promoted_risk_unknown_position_boundary",
            "no_issue_found",
            "medium",
            "promoted_risk_preview",
            "unknown_position_not_assumed_flat",
            "preserve this wording before future promotion evidence use",
            "promoted_risk explicitly says current position data is unavailable; do not assume flat.",
        )
    return AuditRow(
        "F6_promoted_risk_unknown_position_boundary",
        "needs_manual_review",
        "high",
        "promoted_risk_preview",
        "insufficient_static_evidence",
        "add or verify loud unknown-position wording before generic promotion ladder",
        "Could not confirm do-not-assume-flat wording statically.",
    )


def audit_multi_strategy_preview(source: "SourceBundle") -> AuditRow:
    text = source.read("trading_bot/research/multi_strategy_portfolio_preview.py")
    if "portfolio_preview_only" in text and "desired_position" in text:
        return AuditRow(
            "F6_multi_strategy_preview_position_scope",
            "needs_manual_review",
            "medium",
            "multi_strategy_portfolio_preview",
            "saved_desired_positions_only",
            "ensure future generic promotion ladder does not treat missing current positions as flat",
            "multi_strategy_portfolio_preview is preview-only and combines desired positions, but future current-position semantics need explicit review.",
        )
    return AuditRow(
        "F6_multi_strategy_preview_position_scope",
        "insufficient_static_evidence",
        "medium",
        "multi_strategy_portfolio_preview",
        "source_not_confirmed",
        "review before future generic promotion ladder",
        "Could not confirm saved desired-position preview scope.",
    )


def audit_multi_sleeve_backtest_accounting(source: "SourceBundle") -> AuditRow:
    text = source.read("trading_bot/research/multi_sleeve_portfolio_backtest.py")
    has_weighted_streams = "sum(by_candidate[candidate][date] * weight" in text
    has_allocations = "target_weight_pct" in text and "actual_weight_pct" in text
    if has_weighted_streams and has_allocations:
        return AuditRow(
            "F7_multi_sleeve_portfolio_accounting",
            "needs_manual_review",
            "high",
            "multi_sleeve_portfolio_backtest",
            "weighted_return_stream_accounting_detected",
            "add focused accounting consistency verifier before using portfolio backtest as promotion evidence",
            "Static source shows weighted return-stream aggregation and allocation rows; starting-cash/capital reuse assumptions need review.",
        )
    return AuditRow(
        "F7_multi_sleeve_portfolio_accounting",
        "insufficient_static_evidence",
        "high",
        "multi_sleeve_portfolio_backtest",
        "accounting_path_not_confirmed",
        "manual review required before promotion evidence use",
        "Could not confirm portfolio aggregation accounting path statically.",
    )


def audit_sleeve_return_stream_accounting(source: "SourceBundle") -> AuditRow:
    text = source.read("trading_bot/research/sleeve_return_streams.py")
    if "daily_strategy_return" in text and "cash_weight" in text:
        return AuditRow(
            "F7_sleeve_return_stream_inputs",
            "needs_manual_review",
            "medium",
            "sleeve_return_streams",
            "daily_streams_available_for_research_only",
            "verify stream normalization and cash handling before portfolio promotion evidence",
            "Sleeve streams include daily_strategy_return and cash_weight fields; normalization needs future accounting review.",
        )
    return AuditRow(
        "F7_sleeve_return_stream_inputs",
        "insufficient_static_evidence",
        "medium",
        "sleeve_return_streams",
        "stream_fields_not_confirmed",
        "review return-stream generation before portfolio backtest evidence use",
        "Could not confirm stream fields statically.",
    )


def audit_portfolio_promotion_boundary(source: "SourceBundle") -> AuditRow:
    checklist = source.read("docs/PAPER_LIVE_CHECKLIST.md")
    if "generic promotion ladder" in checklist and "Do not generalize too early" in checklist:
        return AuditRow(
            "F7_promotion_evidence_boundary",
            "future_fix_required",
            "medium",
            "paper_live_checklist_step_12",
            "generic_promotion_ladder_future_only",
            "build F7 accounting verifier before any multi-sleeve paper-live promotion discussion",
            "PAPER_LIVE_CHECKLIST keeps generic promotion ladder future-only and warns not to generalize too early.",
        )
    return AuditRow(
        "F7_promotion_evidence_boundary",
        "needs_manual_review",
        "medium",
        "paper_live_checklist_step_12",
        "future_boundary_needs_review",
        "document F7 accounting blocker before generic promotion ladder",
        "Could not confirm Step 12 future-only boundary statically.",
    )


def row_to_dict(row: AuditRow) -> dict[str, Any]:
    return {
        "audit_item": row.audit_item,
        "review_finding": row.review_finding,
        "severity": row.severity,
        "affected_area": row.affected_area,
        "current_status": row.current_status,
        "future_action_required": row.future_action_required,
        "evidence": row.evidence,
        **ROW_SAFETY,
    }


def build_summary_rows(rows: list[AuditRow]) -> list[dict[str, Any]]:
    finding_counts = count_by(rows, "review_finding")
    final_status = (
        "paper_live_f6_f7_audit_manual_review_required"
        if any(row.review_finding in {"needs_manual_review", "future_fix_required", "insufficient_static_evidence"} for row in rows)
        else "paper_live_f6_f7_audit_no_issue_found"
    )
    f6_status = "f6_loud_unknown_position_boundaries_partially_confirmed_manual_review_required"
    f7_status = "f7_accounting_consistency_manual_review_required"
    summary = [
        ("final_audit_status", final_status, "F6/F7 closeout audit status."),
        ("f6_position_unknown_status", f6_status, "F6 requires previews not to assume flat when positions are unknown."),
        ("f7_accounting_status", f7_status, "F7 requires starting-cash/accounting consistency review before promotion evidence use."),
        ("no_issue_found_count", str(finding_counts.get("no_issue_found", 0)), "Rows with no issue found from static evidence."),
        ("needs_manual_review_count", str(finding_counts.get("needs_manual_review", 0)), "Rows that need manual review."),
        ("future_fix_required_count", str(finding_counts.get("future_fix_required", 0)), "Rows requiring future fixes or verifier work."),
        ("insufficient_static_evidence_count", str(finding_counts.get("insufficient_static_evidence", 0)), "Rows where static source evidence was insufficient."),
        ("next_safe_development_step", "add_targeted_f6_f7_tests_or_verifiers_before_generic_promotion_ladder", "Next step is tests/verifiers, not execution."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("repeat_execution_approved", "False", "Repeat execution approval remains false."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must never be scheduled."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in summary]


def build_blocker_rows(rows: list[AuditRow]) -> list[dict[str, Any]]:
    blockers = [
        ("f6_generic_promotion_position_unknown_review", "manual_review_required", "high", "Before a generic promotion ladder, every preview/action path must loudly label unknown positions and never assume flat.", "Add focused F6 tests/verifiers before promotion ladder work."),
        ("f7_portfolio_accounting_consistency_review", "manual_review_required", "high", "Multi-sleeve portfolio backtest/accounting must be checked before backtest results become promotion evidence.", "Add starting-cash/accounting consistency verifier before multi-sleeve paper-live work."),
        ("execution_not_approved", "blocked", "critical", "This audit does not approve execution or paper execution.", "Continue monitoring/report-only work."),
        ("scheduling_not_approved", "blocked", "critical", "This audit does not approve scheduling or Hermes cron changes.", "Keep order-capable commands unscheduled."),
    ]
    return [
        {
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows(rows: list[AuditRow]) -> list[dict[str, Any]]:
    return [
        {
            "evidence_name": row.audit_item,
            "evidence_value": row.current_status,
            "details": row.evidence,
            **SAFETY_FLAGS,
        }
        for row in rows
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live F6/F7 audit complete. Report only; no orders approved.",
        f"final_audit_status: {summary_value(summary_rows, 'final_audit_status')}",
        f"f6_position_unknown_status: {summary_value(summary_rows, 'f6_position_unknown_status')}",
        f"f7_accounting_status: {summary_value(summary_rows, 'f7_accounting_status')}",
        f"no_issue_found_count: {summary_value(summary_rows, 'no_issue_found_count')}",
        f"needs_manual_review_count: {summary_value(summary_rows, 'needs_manual_review_count')}",
        f"future_fix_required_count: {summary_value(summary_rows, 'future_fix_required_count')}",
        f"insufficient_static_evidence_count: {summary_value(summary_rows, 'insufficient_static_evidence_count')}",
        f"next_safe_development_step: {summary_value(summary_rows, 'next_safe_development_step')}",
        f"Saved report/summary/blockers/evidence to {output_paths['report']}; {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def count_by(rows: list[AuditRow], attribute: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(getattr(row, attribute))
        counts[value] = counts.get(value, 0) + 1
    return counts


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


class SourceBundle:
    def __init__(self, root: Path):
        self.root = root

    def read(self, relative_path: str) -> str:
        try:
            return (self.root / relative_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
