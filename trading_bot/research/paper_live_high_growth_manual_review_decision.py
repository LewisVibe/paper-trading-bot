"""Saved-output high-growth manual-review decision checkpoint.

This checkpoint reads only the saved high-growth evidence-gap and
evidence-quality outputs. It does not rerun research, refresh market data, call
Alpaca, read positions, create action previews, create order instructions,
schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "decision": Path("data/paper_live_high_growth_manual_review_decision.csv"),
    "summary": Path("data/paper_live_high_growth_manual_review_decision_summary.csv"),
    "blockers": Path("data/paper_live_high_growth_manual_review_decision_blockers.csv"),
    "evidence": Path("data/paper_live_high_growth_manual_review_decision_evidence.csv"),
}

INPUT_FILES = {
    "evidence_gap_summary": Path("data/paper_live_high_growth_evidence_gap_summary.csv"),
    "evidence_gap_blockers": Path("data/paper_live_high_growth_evidence_gap_blockers.csv"),
    "evidence_quality_review": Path("data/paper_live_high_growth_evidence_quality.csv"),
    "evidence_quality_summary": Path("data/paper_live_high_growth_evidence_quality_summary.csv"),
    "evidence_quality_blockers": Path("data/paper_live_high_growth_evidence_quality_blockers.csv"),
    "evidence_quality_evidence": Path("data/paper_live_high_growth_evidence_quality_evidence.csv"),
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
    "saved_output_only": True,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "action_preview_created": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "portfolio_execution_wired": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

DECISION_COLUMNS = [
    "final_decision_status",
    "high_growth_preview_candidate",
    "high_growth_paper_live_candidate",
    "high_growth_promotion_approved",
    "current_manual_review_reason",
    "qqq100_relative_status",
    "future_reconsideration_requirements",
    "allowed_next_action",
    "forbidden_action",
    "research_only",
    "report_only",
    "saved_output_only",
    "market_data_refreshed",
    "yfinance_called",
    "alpaca_called",
    "live_positions_read",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "action_preview_created",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "portfolio_execution_wired",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]

FINAL_RESEARCH_ONLY_STATUS = "high_growth_remains_research_only_manual_review_required"
INCONCLUSIVE_STATUS = "high_growth_manual_review_required_saved_evidence_inconclusive"
QQQ100_RELATIVE_STATUS = "qqq100_remains_cleaner_current_paper_live_monitor_base"
ALLOWED_NEXT_ACTION = "continue_qqq100_monitoring_and_keep_high_growth_research_only"
FORBIDDEN_ACTION = (
    "approve_high_growth_preview;approve_high_growth_paper_live;approve_high_growth_promotion;"
    "create_action_preview;create_order_instructions;wire_execution;schedule_orders"
)
FUTURE_REQUIREMENTS = (
    "concentration_cap_or_concentration_control_evidence;"
    "component_drawdown_attribution_acceptable_dependency;"
    "split_robustness_and_cost_review;"
    "portfolio_accounting_consistency;"
    "f6_f7_compatibility;"
    "risk_policy_review;"
    "no_order_instructions_or_scheduling"
)
RISK_TOKENS = (
    "high_growth_stock_outlier_dependent",
    "max_single_name_concentration=1.0",
    "outlier_dependence_warning=true",
    "survivorship_bias_warning=true",
    "current_constituent_bias_warning=true",
    "worst_drawdown=-70",
    "drawdown",
    "concentration",
    "outlier",
)


@dataclass
class DecisionContext:
    rows_by_name: dict[str, list[dict[str, str]]]


@dataclass
class PaperLiveHighGrowthManualReviewDecisionResult:
    output_paths: dict[str, Path]
    decision_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_high_growth_manual_review_decision(
    root_dir: Path | str = ".",
) -> PaperLiveHighGrowthManualReviewDecisionResult:
    root = Path(root_dir)
    context = load_decision_context(root)
    decision_rows = build_decision_rows(context)
    summary_rows = build_summary_rows(context, decision_rows)
    blocker_rows = build_blocker_rows(context, decision_rows)
    evidence_rows = build_evidence_rows(context, decision_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decision"], DECISION_COLUMNS, decision_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveHighGrowthManualReviewDecisionResult(
        output_paths=output_paths,
        decision_rows=decision_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_high_growth_manual_review_decision(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live high-growth manual-review decision is missing.",
            "Run `python bot.py --paper-live-high-growth-manual-review-decision` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live high-growth manual-review decision. Saved-output/report-only; no high-growth preview, paper-live, execution, or scheduling approved.",
        f"final_decision_status: {summary_value(rows, 'final_decision_status')}",
        f"high_growth_preview_candidate: {summary_value(rows, 'high_growth_preview_candidate')}",
        f"high_growth_paper_live_candidate: {summary_value(rows, 'high_growth_paper_live_candidate')}",
        f"high_growth_promotion_approved: {summary_value(rows, 'high_growth_promotion_approved')}",
        f"current_manual_review_reason: {summary_value(rows, 'current_manual_review_reason')}",
        f"qqq100_relative_status: {summary_value(rows, 'qqq100_relative_status')}",
        f"future_reconsideration_requirements: {summary_value(rows, 'future_reconsideration_requirements')}",
        f"allowed_next_action: {summary_value(rows, 'allowed_next_action')}",
        f"forbidden_action: {summary_value(rows, 'forbidden_action')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def load_decision_context(root: Path) -> DecisionContext:
    return DecisionContext(rows_by_name={name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()})


def build_decision_rows(context: DecisionContext) -> list[dict[str, Any]]:
    manual_reason = manual_review_reason(context)
    risk_confirmed = high_growth_risk_confirmed(context)
    status = FINAL_RESEARCH_ONLY_STATUS if risk_confirmed else INCONCLUSIVE_STATUS
    return [
        {
            "final_decision_status": status,
            "high_growth_preview_candidate": False,
            "high_growth_paper_live_candidate": False,
            "high_growth_promotion_approved": False,
            "current_manual_review_reason": manual_reason,
            "qqq100_relative_status": QQQ100_RELATIVE_STATUS,
            "future_reconsideration_requirements": FUTURE_REQUIREMENTS,
            "allowed_next_action": ALLOWED_NEXT_ACTION,
            "forbidden_action": FORBIDDEN_ACTION,
            **ROW_SAFETY,
        }
    ]


def build_summary_rows(
    context: DecisionContext,
    decision_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decision = decision_rows[0]
    return [
        summary_row("final_decision_status", str(decision["final_decision_status"]), "High-growth remains manual-review only."),
        summary_row("high_growth_preview_candidate", "False", "High-growth is not a preview candidate."),
        summary_row("high_growth_paper_live_candidate", "False", "High-growth is not a paper-live candidate."),
        summary_row("high_growth_promotion_approved", "False", "No high-growth promotion is approved."),
        summary_row("current_manual_review_reason", str(decision["current_manual_review_reason"]), "Summarized from saved evidence-gap and evidence-quality outputs."),
        summary_row("qqq100_relative_status", QQQ100_RELATIVE_STATUS, "QQQ100 remains the cleaner current paper-live monitor base."),
        summary_row("future_reconsideration_requirements", FUTURE_REQUIREMENTS, "Minimum evidence requirements before any future high-growth reconsideration."),
        summary_row("allowed_next_action", ALLOWED_NEXT_ACTION, "Keep monitoring/reporting QQQ100 and keep high-growth research-only."),
        summary_row("forbidden_action", FORBIDDEN_ACTION, "No preview, paper-live, order, execution, or scheduling approval."),
        summary_row("saved_gap_quality_inputs_present", str(count_input_files_present(context)), "Count of saved gap/quality input files found."),
    ]


def build_blocker_rows(
    context: DecisionContext,
    decision_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decision = decision_rows[0]
    return [
        blocker_row(
            "high_growth_preview_candidate_false",
            "blocked",
            "critical",
            "Saved evidence quality keeps high-growth out of preview-candidate status.",
            "Complete concentration, attribution, split/cost, portfolio accounting, F6/F7, and risk-policy review first.",
        ),
        blocker_row(
            "high_growth_paper_live_candidate_false",
            "blocked",
            "critical",
            "High-growth is not a paper-live candidate and cannot be connected to execution.",
            "Keep high-growth research-only.",
        ),
        blocker_row(
            "high_growth_promotion_not_approved",
            "blocked",
            "critical",
            str(decision["current_manual_review_reason"]),
            "Do not approve high-growth promotion.",
        ),
        blocker_row(
            "qqq100_remains_cleaner_current_monitor_base",
            "confirmed",
            "high",
            QQQ100_RELATIVE_STATUS,
            "Continue QQQ100 monitor/report path; do not replace it with high-growth.",
        ),
        blocker_row(
            "future_reconsideration_requires_stronger_evidence",
            "manual_review_required",
            "high",
            FUTURE_REQUIREMENTS,
            "Address each requirement in separate saved-output checkpoints before any future label change.",
        ),
        blocker_row(
            "gap_quality_input_coverage",
            "manual_review_required",
            "medium",
            f"saved_gap_quality_inputs_present={count_input_files_present(context)}",
            "Missing saved gap/quality inputs should be regenerated only through safe report-only commands.",
        ),
    ]


def build_evidence_rows(
    context: DecisionContext,
    decision_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        evidence_row(
            "decision_method",
            "saved_gap_and_quality_outputs_only",
            "Only paper_live_high_growth_evidence_gap and paper_live_high_growth_evidence_quality outputs are read.",
        ),
        evidence_row(
            "full_csv_dumped",
            "false",
            "The decision pack summarizes key fields and row counts only.",
        ),
        evidence_row("manual_review_reason", str(decision_rows[0]["current_manual_review_reason"]), "Summarized quality concerns."),
    ]
    for name, rows_for_file in context.rows_by_name.items():
        rows.append(evidence_row(f"{name}_row_count", str(len(rows_for_file)), "Saved input row count only."))
    return rows


def high_growth_risk_confirmed(context: DecisionContext) -> bool:
    haystack = all_saved_text(context).lower()
    return any(token.lower() in haystack for token in RISK_TOKENS)


def manual_review_reason(context: DecisionContext) -> str:
    summary_rows = context.rows_by_name.get("evidence_quality_summary", [])
    parts = [
        summary_value(summary_rows, "final_quality_status"),
        summary_value(summary_rows, "top_outlier_dependency"),
        summary_value(summary_rows, "worst_drawdown_context"),
        summary_value(summary_rows, "largest_manual_review_blocker"),
    ]
    compact = "; ".join(part for part in parts if part and part != "unavailable")
    if compact:
        return compact
    gap_summary = context.rows_by_name.get("evidence_gap_summary", [])
    gap_status = summary_value(gap_summary, "final_high_growth_evidence_gap_status")
    return gap_status if gap_status != "unavailable" else "saved_gap_or_quality_evidence_missing_manual_review_required"


def count_input_files_present(context: DecisionContext) -> int:
    return sum(1 for rows in context.rows_by_name.values() if rows)


def all_saved_text(context: DecisionContext) -> str:
    values: list[str] = []
    for rows in context.rows_by_name.values():
        for row in rows:
            values.extend(str(value) for value in row.values())
    return "\n".join(values)


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live high-growth manual-review decision complete. Saved-output/report-only; no preview, paper-live, execution, orders, or scheduling approved.",
        f"final_decision_status={summary_value(summary_rows, 'final_decision_status')}",
        f"high_growth_preview_candidate={summary_value(summary_rows, 'high_growth_preview_candidate')}",
        f"high_growth_paper_live_candidate={summary_value(summary_rows, 'high_growth_paper_live_candidate')}",
        f"high_growth_promotion_approved={summary_value(summary_rows, 'high_growth_promotion_approved')}",
        f"current_manual_review_reason={summary_value(summary_rows, 'current_manual_review_reason')}",
        f"qqq100_relative_status={summary_value(summary_rows, 'qqq100_relative_status')}",
        f"future_reconsideration_requirements={summary_value(summary_rows, 'future_reconsideration_requirements')}",
        f"allowed_next_action={summary_value(summary_rows, 'allowed_next_action')}",
        f"forbidden_action={summary_value(summary_rows, 'forbidden_action')}",
        f"saved_report={output_paths['decision']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
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
