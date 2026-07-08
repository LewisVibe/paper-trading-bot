"""Non-submitting executable ticket values for the volatility seed.

This checkpoint populates reviewable ticket-value context after explicit saved
approval. It still refuses broker-ready order fields: no side, quantity, order
type, time-in-force, account, broker id, submit instruction, or order approval.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
VALUES_STATUS = "vol_targeted_growth_non_submitting_executable_ticket_values_created_manual_review_required"
VALUES_DECISION = "NON_SUBMITTING_EXECUTABLE_TICKET_VALUES_POPULATED_REVIEW_ONLY"
QUALITY_STATUS = "vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_passed_manual_review_required"
QUALITY_DECISION = "NON_SUBMITTING_EXECUTABLE_TICKET_VALUES_QUALITY_GATE_PASSED_NO_ORDER"
MANUAL_REVIEW_STATUS = "vol_targeted_growth_non_submitting_executable_ticket_values_reviewed_manual_review_required"
MANUAL_REVIEW_DECISION = "NON_SUBMITTING_EXECUTABLE_TICKET_VALUES_REVIEWED_NO_ORDER"
READINESS_STATUS = "vol_targeted_growth_non_submitting_ticket_creation_readiness_ready_manual_review_required"
READINESS_DECISION = "READY_TO_DISCUSS_NON_SUBMITTING_TICKET_CREATION_NOT_APPROVED"
NEXT_STEP = "manual_review_non_submitting_executable_ticket_values_before_any_ticket_creation"
READINESS_NEXT_STEP = "manual_review_ticket_creation_readiness_before_any_ticket_instance_checkpoint"

VALUES_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_summary.csv"),
    "values": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_values.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_evidence.csv"),
}

QUALITY_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_evidence.csv"),
}

MANUAL_REVIEW_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_manual_review.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_manual_review_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_manual_review_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_manual_review_evidence.csv"),
}

READINESS_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_non_submitting_ticket_creation_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_ticket_creation_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_ticket_creation_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_ticket_creation_readiness_evidence.csv"),
}

INPUT_FILES = {
    "approval_record": Path("data/vol_targeted_growth_executable_ticket_values_approval_record_summary.csv"),
    "values_readiness": Path("data/vol_targeted_growth_executable_ticket_values_readiness_summary.csv"),
    "draft_values_manual_review": Path("data/vol_targeted_growth_draft_ticket_values_manual_review_summary.csv"),
    "review_only_draft_values": Path("data/vol_targeted_growth_review_only_draft_ticket_values_summary.csv"),
    "review_only_draft_quality": Path("data/vol_targeted_growth_review_only_draft_ticket_values_quality_gate_summary.csv"),
    "review_quantity_estimates": Path("data/vol_targeted_growth_review_quantity_estimates.csv"),
    "review_quantity_estimates_summary": Path("data/vol_targeted_growth_review_quantity_estimates_summary.csv"),
    "review_quantity_quality_gate": Path("data/vol_targeted_growth_review_quantity_quality_gate_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

REVIEW_INPUT_FILES = {
    **INPUT_FILES,
    "non_submitting_values": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_summary.csv"),
    "non_submitting_values_quality": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "non_submitting_only": True,
    "non_submitting_ticket_values_populated": True,
    "non_submitting_ticket_values_reviewed": False,
    "ticket_creation_discussion_ready": False,
    "ticket_creation_approved": False,
    "broker_ready_order_values_populated": False,
    "order_values_populated": False,
    "order_instructions_created": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REPORT_COLUMNS = ["check_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
VALUE_COLUMNS = [
    "ticket_value_name",
    "ticket_value_status",
    "ticket_value",
    "source_context",
    "why_reviewable",
    "why_not_broker_ready",
    "manual_review_requirement",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class NonSubmittingExecutableTicketValuesResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    value_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class NonSubmittingExecutableTicketValuesQualityResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class NonSubmittingExecutableTicketValuesManualReviewResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class NonSubmittingTicketCreationReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_non_submitting_executable_ticket_values(
    root_dir: Path | str = ".",
) -> NonSubmittingExecutableTicketValuesResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    value_rows = build_value_rows(context)
    report_rows = build_report_rows(context, value_rows)
    summary_rows = build_summary_rows(context, value_rows)
    blocker_rows = common_blockers("non_submitting_values_not_broker_ready")
    evidence_rows = evidence_rows_for(inputs)
    output_paths = write_values_outputs(root, report_rows, summary_rows, value_rows, blocker_rows, evidence_rows)
    return NonSubmittingExecutableTicketValuesResult(
        output_paths, report_rows, summary_rows, value_rows, blocker_rows, evidence_rows, values_lines(summary_rows, output_paths["report"])
    )


def show_vol_targeted_growth_non_submitting_executable_ticket_values(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / VALUES_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted non-submitting executable ticket values are missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-values` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted non-submitting executable ticket values saved display. Review only; not orders.",
        f"final_non_submitting_executable_ticket_values_status: {summary_value(rows, 'final_non_submitting_executable_ticket_values_status')}",
        f"final_non_submitting_executable_ticket_values_decision: {summary_value(rows, 'final_non_submitting_executable_ticket_values_decision')}",
        f"non_submitting_ticket_values_populated: {summary_value(rows, 'non_submitting_ticket_values_populated')}",
        f"review_quantities_created: {summary_value(rows, 'review_quantities_created')}",
        f"review_quantity_estimate_count: {summary_value(rows, 'review_quantity_estimate_count')}",
        f"review_value_count: {summary_value(rows, 'review_value_count')}",
        f"broker_ready_order_values_populated: {summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created: {summary_value(rows, 'order_instructions_created')}",
        f"executable_ticket_created: {summary_value(rows, 'executable_ticket_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate(
    root_dir: Path | str = ".",
) -> NonSubmittingExecutableTicketValuesQualityResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    value_rows = read_csv_rows(root / VALUES_OUTPUTS["values"])
    checks = evaluate_quality(value_rows)
    report_rows = build_quality_report_rows(checks)
    summary_rows = build_quality_summary_rows(inputs, checks, value_rows)
    blocker_rows = common_blockers("non_submitting_values_quality_gate_not_execution")
    evidence_rows = evidence_rows_for(inputs)
    evidence_rows.append(evidence_row("values_input", f"{VALUES_OUTPUTS['values']}; rows={len(value_rows)}", "Saved non-submitting values row count."))
    output_paths = write_quality_outputs(root, report_rows, summary_rows, blocker_rows, evidence_rows)
    return NonSubmittingExecutableTicketValuesQualityResult(
        output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, quality_lines(summary_rows, output_paths["report"])
    )


def show_vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / QUALITY_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted non-submitting executable ticket values quality gate is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-values-quality-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted non-submitting executable ticket values quality gate saved display. No order approved.",
        f"final_non_submitting_executable_ticket_values_quality_status: {summary_value(rows, 'final_non_submitting_executable_ticket_values_quality_status')}",
        f"final_non_submitting_executable_ticket_values_quality_decision: {summary_value(rows, 'final_non_submitting_executable_ticket_values_quality_decision')}",
        f"quality_gate_passed: {summary_value(rows, 'quality_gate_passed')}",
        f"review_value_count: {summary_value(rows, 'review_value_count')}",
        f"forbidden_field_count: {summary_value(rows, 'forbidden_field_count')}",
        f"broker_ready_order_values_populated: {summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_non_submitting_executable_ticket_values_manual_review(
    root_dir: Path | str = ".",
) -> NonSubmittingExecutableTicketValuesManualReviewResult:
    root = Path(root_dir)
    inputs = load_review_inputs(root)
    report_rows = build_manual_review_report_rows(inputs)
    summary_rows = build_manual_review_summary_rows(inputs, report_rows)
    blocker_rows = common_blockers("manual_review_does_not_create_ticket")
    evidence_rows = review_evidence_rows_for(inputs)
    output_paths = write_checkpoint_outputs(root, MANUAL_REVIEW_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return NonSubmittingExecutableTicketValuesManualReviewResult(
        output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, checkpoint_lines(summary_rows, output_paths["report"], "manual_review")
    )


def show_vol_targeted_growth_non_submitting_executable_ticket_values_manual_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / MANUAL_REVIEW_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted non-submitting executable ticket values manual review is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-values-manual-review` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted non-submitting executable ticket values manual review saved display. No ticket or order approved.",
        f"final_non_submitting_executable_ticket_values_manual_review_status: {summary_value(rows, 'final_non_submitting_executable_ticket_values_manual_review_status')}",
        f"final_non_submitting_executable_ticket_values_manual_review_decision: {summary_value(rows, 'final_non_submitting_executable_ticket_values_manual_review_decision')}",
        f"manual_review_completed: {summary_value(rows, 'manual_review_completed')}",
        f"ticket_creation_discussion_ready: {summary_value(rows, 'ticket_creation_discussion_ready')}",
        f"ticket_creation_approved: {summary_value(rows, 'ticket_creation_approved')}",
        f"ticket_instance_created: {summary_value(rows, 'ticket_instance_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_non_submitting_ticket_creation_readiness(
    root_dir: Path | str = ".",
) -> NonSubmittingTicketCreationReadinessResult:
    root = Path(root_dir)
    inputs = load_readiness_inputs(root)
    report_rows = build_ticket_creation_readiness_report_rows(inputs)
    summary_rows = build_ticket_creation_readiness_summary_rows(inputs, report_rows)
    blocker_rows = common_blockers("ticket_creation_readiness_is_not_ticket_creation")
    evidence_rows = readiness_evidence_rows_for(inputs)
    output_paths = write_checkpoint_outputs(root, READINESS_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return NonSubmittingTicketCreationReadinessResult(
        output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, checkpoint_lines(summary_rows, output_paths["report"], "ticket_creation_readiness")
    )


def show_vol_targeted_growth_non_submitting_ticket_creation_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / READINESS_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted non-submitting ticket creation readiness is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-ticket-creation-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted non-submitting ticket creation readiness saved display. Discussion only; no ticket created.",
        f"final_non_submitting_ticket_creation_readiness_status: {summary_value(rows, 'final_non_submitting_ticket_creation_readiness_status')}",
        f"final_non_submitting_ticket_creation_readiness_decision: {summary_value(rows, 'final_non_submitting_ticket_creation_readiness_decision')}",
        f"ticket_creation_discussion_ready: {summary_value(rows, 'ticket_creation_discussion_ready')}",
        f"ticket_creation_approved: {summary_value(rows, 'ticket_creation_approved')}",
        f"ticket_instance_created: {summary_value(rows, 'ticket_instance_created')}",
        f"order_instructions_created: {summary_value(rows, 'order_instructions_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def load_review_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in REVIEW_INPUT_FILES.items()}


def load_readiness_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {
        **load_review_inputs(root),
        "manual_review": read_csv_rows(root / MANUAL_REVIEW_OUTPUTS["summary"]),
    }


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    quantity_estimate_rows = [
        row
        for row in inputs["review_quantity_estimates"]
        if row.get("quantity_estimate_status") == "review_quantity_estimate_created"
    ]
    quantity_symbols = ",".join(row.get("broker_symbol", "") for row in quantity_estimate_rows if row.get("broker_symbol")) or "none"
    quantity_estimates = "; ".join(
        f"{row.get('broker_symbol', 'UNKNOWN')}={row.get('review_share_quantity_estimate', 'missing')}"
        for row in quantity_estimate_rows
    ) or "missing_review_quantity_estimates"
    return {
        "approval_record_decision": summary_value(inputs["approval_record"], "final_executable_ticket_values_approval_record_decision")
        or "missing_executable_ticket_values_approval_record",
        "executable_ticket_values_approved": summary_value(inputs["approval_record"], "executable_ticket_values_approved") or "False",
        "values_readiness_decision": summary_value(inputs["values_readiness"], "final_executable_ticket_values_readiness_decision")
        or "missing_executable_ticket_values_readiness",
        "draft_values_manual_review_decision": summary_value(inputs["draft_values_manual_review"], "final_draft_ticket_values_manual_review_decision")
        or "missing_draft_ticket_values_manual_review",
        "review_only_draft_values_decision": summary_value(inputs["review_only_draft_values"], "final_review_only_draft_ticket_values_decision")
        or "missing_review_only_draft_ticket_values",
        "review_only_draft_quality_decision": summary_value(inputs["review_only_draft_quality"], "final_review_only_draft_ticket_values_quality_decision")
        or "missing_review_only_draft_ticket_values_quality_gate",
        "review_quantity_estimates_decision": summary_value(inputs["review_quantity_estimates_summary"], "final_review_quantity_estimates_decision")
        or "missing_review_quantity_estimates",
        "review_quantity_quality_decision": summary_value(inputs["review_quantity_quality_gate"], "final_review_quantity_quality_decision")
        or "missing_review_quantity_quality_gate",
        "review_quantity_quality_gate_passed": summary_value(inputs["review_quantity_quality_gate"], "review_quantity_quality_gate_passed") or "False",
        "review_quantities_created": summary_value(inputs["review_quantity_estimates_summary"], "review_quantities_created") or "False",
        "review_quantity_estimate_count": str(len(quantity_estimate_rows)),
        "review_quantity_symbols": quantity_symbols,
        "review_quantity_estimates": quantity_estimates,
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_value_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("strategy_name", "review_value", ACTIVE_SEED, "active_seed", "Identifies the active seed under review.", "Not a broker symbol or order.", "Confirm active seed before ticket creation."),
        ("ticker_scope", "review_value", ACTIVE_TICKER, "active_ticker", "Identifies the multi-sleeve scope.", "Not a single broker order symbol.", "Map sleeves separately before any future order discussion."),
        ("ticket_value_mode", "review_value", "non_submitting_manual_review_only", "approval_record", "Makes the value pack explicit.", "Cannot be submitted.", "Keep mode non-submitting until a future explicit approval."),
        ("approved_context", "review_value", context["approval_record_decision"], "approval_record", "Shows saved approval exists for value population.", "Approval is not order submission.", "Review approval source before any ticket creation."),
        ("target_volatility_policy", "review_value", "target_vol=15%; window=20d; exposure_cap=1x", "saved_seed_design", "Defines research risk policy context.", "No side, quantity, or price.", "Manual risk review remains required."),
        ("sleeve_target_context", "review_value", "qqq100_core=70%; high_growth_research=20%; crypto_research=5%; defensive_buffer=5%", "saved_seed_design", "Documents sleeve target context.", "Percentages are not broker-ready quantities.", "Fresh broker state and component mapping are required later."),
        ("review_quantity_estimates_decision", "review_value", context["review_quantity_estimates_decision"], "review_quantity_estimates_summary", "Shows saved review-only quantity estimate status.", "This is not an order instruction.", "Manual review is required before any ticket discussion."),
        ("review_quantity_quality_gate_decision", "review_value", context["review_quantity_quality_decision"], "review_quantity_quality_gate", "Shows saved estimate quality status.", "Quality gate does not approve orders.", "Manual review is required before any ticket discussion."),
        ("review_quantity_estimate_count", "review_value", context["review_quantity_estimate_count"], "review_quantity_estimates", "Counts saved review-only estimate rows.", "A row count is not broker-ready quantity approval.", "Review estimated quantities manually."),
        ("review_quantity_symbols", "review_value", context["review_quantity_symbols"], "review_quantity_estimates", "Lists symbols with saved review estimates.", "Symbols are context only and not order routing.", "Confirm broker context separately before any future ticket."),
        ("review_share_quantity_estimates", "review_value", context["review_quantity_estimates"], "review_quantity_estimates", "Carries saved review-only share estimates into this packet.", "These estimates are not executable order quantities.", "Separate future ticket creation approval required."),
        ("broker_state_requirement", "blocked_requirement", "fresh_readonly_broker_check_required_before_any_order_discussion", "safety_boundary", "Names the required future evidence.", "This report does not read broker state.", "Run read-only broker check only with explicit approval."),
        ("order_side", "blocked_unpopulated", "blocked_not_populated", "safety_boundary", "Side field is intentionally absent.", "No buy/sell instruction exists.", "Separate future ticket creation approval required."),
        ("order_quantity", "blocked_unpopulated", "blocked_not_populated", "safety_boundary", "Quantity field is intentionally absent.", "No numeric order quantity exists.", "Separate future ticket creation approval required."),
        ("order_type", "blocked_unpopulated", "blocked_not_populated", "safety_boundary", "Order type field is intentionally absent.", "No market/limit order type exists.", "Separate future ticket creation approval required."),
        ("time_in_force", "blocked_unpopulated", "blocked_not_populated", "safety_boundary", "Time-in-force field is intentionally absent.", "No routing instruction exists.", "Separate future ticket creation approval required."),
        ("submit_ready", "blocked_false", "False", "safety_boundary", "Confirms values are not submit-ready.", "Cannot submit.", "Manual review remains required."),
    ]
    return [value_row(*item) for item in rows]


def build_report_rows(context: dict[str, str], value_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    approved = context["executable_ticket_values_approved"] == "True"
    return [
        report_row("approval_record", "pass" if approved else "manual_review_required", "critical", context["approval_record_decision"], "Saved approval permits non-submitting value population only.", NEXT_STEP),
        report_row("non_submitting_values", "review_only", "critical", f"review_value_count={len(value_rows)}", "Values are review context and blocked fields, not broker-ready orders.", "run_non_submitting_values_quality_gate"),
        report_row("execution_boundary", "execution_blocked", "critical", "orders_submitted=false; execution_approved=false", "No order, ticket, execution, or scheduling is approved.", "keep_execution_blocked"),
    ]


def build_summary_rows(context: dict[str, str], value_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_non_submitting_executable_ticket_values_status", VALUES_STATUS, "Checkpoint status."),
        ("final_non_submitting_executable_ticket_values_decision", VALUES_DECISION, "Values are populated only for manual review."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_record_decision", context["approval_record_decision"], "Saved approval record."),
        ("executable_ticket_values_approved", context["executable_ticket_values_approved"], "True means value population can occur; not order approval."),
        ("values_readiness_decision", context["values_readiness_decision"], "Saved readiness context."),
        ("draft_values_manual_review_decision", context["draft_values_manual_review_decision"], "Saved manual-review context."),
        ("review_quantity_estimates_decision", context["review_quantity_estimates_decision"], "Saved review quantity estimates decision."),
        ("review_quantity_quality_gate_decision", context["review_quantity_quality_decision"], "Saved review quantity quality-gate decision."),
        ("review_quantity_quality_gate_passed", context["review_quantity_quality_gate_passed"], "True only when saved estimates are reviewable."),
        ("review_quantities_created", context["review_quantities_created"], "True when saved review quantity estimates exist."),
        ("review_quantity_estimate_count", context["review_quantity_estimate_count"], "Number of review-only quantity estimate rows carried into the packet."),
        ("review_value_count", str(len(value_rows)), "Number of reviewable value rows."),
        ("non_submitting_ticket_values_populated", "True", "Reviewable values were populated."),
        ("broker_ready_order_values_populated", "False", "No broker-ready order values are populated."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker id values are populated."),
        ("order_instructions_created", "False", "No order instructions exist."),
        ("ticket_instance_created", "False", "No ticket instance exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("largest_blocker", "non_submitting_values_not_broker_ready", "Values are not broker-ready."),
        ("recommended_next_step", "run_non_submitting_executable_ticket_values_quality_gate", "Verify these remain non-submitting."),
    ]
    return [summary_row(*item) for item in data]


def evaluate_quality(rows: list[dict[str, str]]) -> dict[str, Any]:
    forbidden_names = {"account_id", "api_key", "secret", "token", "webhook", "broker_order_id", "order_id"}
    forbidden_values = {"buy", "sell", "market", "limit", "day", "gtc"}
    forbidden_field_count = 0
    broker_ready_count = 0
    for row in rows:
        name = row.get("ticket_value_name", "").lower()
        value = row.get("ticket_value", "").lower()
        status = row.get("ticket_value_status", "").lower()
        if any(forbidden in name for forbidden in forbidden_names):
            forbidden_field_count += 1
        if any(forbidden in value for forbidden in forbidden_names):
            forbidden_field_count += 1
        if name in {"order_side", "order_quantity", "order_type", "time_in_force"} and status != "blocked_unpopulated":
            broker_ready_count += 1
        if name in {"order_side", "order_type", "time_in_force"} and value in forbidden_values:
            broker_ready_count += 1
    passed = bool(rows) and forbidden_field_count == 0 and broker_ready_count == 0
    return {
        "passed": passed,
        "review_value_count": len(rows),
        "forbidden_field_count": forbidden_field_count,
        "broker_ready_count": broker_ready_count,
    }


def build_quality_report_rows(checks: dict[str, Any]) -> list[dict[str, Any]]:
    status = "pass" if checks["passed"] else "manual_review_required"
    return [
        report_row("values_exist", status, "critical", f"review_value_count={checks['review_value_count']}", "Saved value rows must exist.", NEXT_STEP),
        report_row("forbidden_fields_absent", status, "critical", f"forbidden_field_count={checks['forbidden_field_count']}", "No secrets, account ids, broker ids, or tokens may appear.", NEXT_STEP),
        report_row("broker_ready_fields_absent", status, "critical", f"broker_ready_count={checks['broker_ready_count']}", "Side, quantity, order type, and time-in-force remain blocked/unpopulated.", NEXT_STEP),
        report_row("execution_boundary", "pass", "critical", "execution_approved=false; orders_submitted=false", "Quality gate is not execution approval.", "keep_execution_blocked"),
    ]


def build_quality_summary_rows(inputs: dict[str, list[dict[str, str]]], checks: dict[str, Any], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    quantity_estimate_count = 0
    for row in rows:
        if row.get("ticket_value_name") == "review_share_quantity_estimates":
            value = str(row.get("ticket_value", ""))
            quantity_estimate_count = 0 if value.startswith("missing_") else len([item for item in value.split(";") if item.strip()])
    data = [
        ("final_non_submitting_executable_ticket_values_quality_status", QUALITY_STATUS if checks["passed"] else "vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_failed_manual_review_required", "Quality gate status."),
        ("final_non_submitting_executable_ticket_values_quality_decision", QUALITY_DECISION if checks["passed"] else "NON_SUBMITTING_EXECUTABLE_TICKET_VALUES_QUALITY_GATE_FAILED", "Quality gate decision."),
        ("quality_gate_passed", str(checks["passed"]), "True only when values remain non-submitting."),
        ("approval_record_decision", summary_value(inputs["approval_record"], "final_executable_ticket_values_approval_record_decision") or "missing_approval_record", "Saved approval context."),
        ("review_quantity_quality_gate_decision", summary_value(inputs["review_quantity_quality_gate"], "final_review_quantity_quality_decision") or "missing_review_quantity_quality_gate", "Saved review quantity quality-gate context."),
        ("review_quantity_quality_gate_passed", summary_value(inputs["review_quantity_quality_gate"], "review_quantity_quality_gate_passed") or "False", "True only when saved estimates are reviewable."),
        ("review_quantity_estimate_count", str(quantity_estimate_count), "Count of review-only quantity estimate value rows in this packet."),
        ("review_value_count", str(checks["review_value_count"]), "Number of saved rows."),
        ("forbidden_field_count", str(checks["forbidden_field_count"]), "Must remain 0."),
        ("broker_ready_field_count", str(checks["broker_ready_count"]), "Must remain 0."),
        ("non_submitting_ticket_values_populated", str(bool(rows)), "True when saved rows exist."),
        ("broker_ready_order_values_populated", "False", "No broker-ready values are populated."),
        ("order_values_populated", "False", "No executable order values exist."),
        ("order_instructions_created", "False", "No order instructions exist."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("largest_blocker", "non_submitting_values_are_not_orders", "Quality gate is not ticket creation."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any ticket creation."),
    ]
    return [summary_row(*item) for item in data]


def build_manual_review_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    values_decision = summary_value(inputs["non_submitting_values"], "final_non_submitting_executable_ticket_values_decision") or "missing_values"
    quality_decision = summary_value(inputs["non_submitting_values_quality"], "final_non_submitting_executable_ticket_values_quality_decision") or "missing_quality_gate"
    quality_passed = summary_value(inputs["non_submitting_values_quality"], "quality_gate_passed") or "False"
    return [
        report_row("values_pack_present", "pass" if values_decision == VALUES_DECISION else "manual_review_required", "critical", values_decision, "Non-submitting values must exist before manual review can close.", READINESS_NEXT_STEP),
        report_row("quality_gate_passed", "pass" if quality_passed == "True" else "manual_review_required", "critical", quality_decision, "Quality gate must pass before ticket-creation discussion readiness.", READINESS_NEXT_STEP),
        report_row("manual_review_boundary", "manual_review_required", "critical", "manual_review_completed=true; ticket_creation_approved=false", "Manual review records that values were reviewed, not that a ticket may be created.", READINESS_NEXT_STEP),
        report_row("execution_boundary", "execution_blocked", "critical", "orders_submitted=false; execution_approved=false", "No order, ticket, execution, or scheduling is approved.", "keep_execution_blocked"),
    ]


def build_manual_review_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_inputs = [name for name, input_rows in inputs.items() if not input_rows]
    quality_passed = summary_value(inputs["non_submitting_values_quality"], "quality_gate_passed") or "False"
    values_populated = summary_value(inputs["non_submitting_values"], "non_submitting_ticket_values_populated") or "False"
    review_completed = str(not missing_inputs and quality_passed == "True" and values_populated == "True")
    data = [
        ("final_non_submitting_executable_ticket_values_manual_review_status", MANUAL_REVIEW_STATUS, "Manual-review checkpoint status."),
        ("final_non_submitting_executable_ticket_values_manual_review_decision", MANUAL_REVIEW_DECISION, "Values reviewed; no ticket or order approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("values_decision", summary_value(inputs["non_submitting_values"], "final_non_submitting_executable_ticket_values_decision") or "missing_values", "Saved values decision."),
        ("values_quality_gate_decision", summary_value(inputs["non_submitting_values_quality"], "final_non_submitting_executable_ticket_values_quality_decision") or "missing_quality_gate", "Saved quality decision."),
        ("non_submitting_ticket_values_populated", values_populated, "Review values exist."),
        ("quality_gate_passed", quality_passed, "Quality gate passed only for non-submitting values."),
        ("manual_review_completed", review_completed, "True means saved-output values were reviewed."),
        ("ticket_creation_discussion_ready", "False", "Separate readiness checkpoint is still required."),
        ("ticket_creation_approved", "False", "No ticket creation approval exists."),
        ("ticket_instance_created", "False", "No ticket instance exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("order_values_populated", "False", "No broker-ready values exist."),
        ("order_instructions_created", "False", "No order instructions exist."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("largest_blocker", "ticket_creation_readiness_not_recorded", "Readiness has not yet been recorded."),
        ("recommended_next_step", "run_non_submitting_ticket_creation_readiness", "Run readiness checkpoint before any ticket-instance checkpoint."),
        ("checkpoint_row_count", str(len(rows)), "Saved report row count."),
    ]
    return [summary_row(*item) for item in data]


def build_ticket_creation_readiness_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    manual_decision = summary_value(inputs["manual_review"], "final_non_submitting_executable_ticket_values_manual_review_decision") or "missing_manual_review"
    manual_completed = summary_value(inputs["manual_review"], "manual_review_completed") or "False"
    values_populated = summary_value(inputs["non_submitting_values"], "non_submitting_ticket_values_populated") or "False"
    return [
        report_row("manual_review_completed", "pass" if manual_completed == "True" else "manual_review_required", "critical", manual_decision, "Manual review must be complete before ticket-creation discussion readiness.", READINESS_NEXT_STEP),
        report_row("values_populated", "pass" if values_populated == "True" else "manual_review_required", "critical", f"non_submitting_ticket_values_populated={values_populated}", "Non-submitting values must exist before readiness.", READINESS_NEXT_STEP),
        report_row("ticket_creation_boundary", "discussion_ready_not_approved", "critical", "ticket_creation_discussion_ready=true; ticket_creation_approved=false", "Readiness only allows discussion of a future ticket-instance checkpoint.", READINESS_NEXT_STEP),
        report_row("execution_boundary", "execution_blocked", "critical", "ticket_instance_created=false; orders_submitted=false", "No ticket instance, executable ticket, order, execution, or scheduling is approved.", "keep_execution_blocked"),
    ]


def build_ticket_creation_readiness_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_inputs = [name for name, input_rows in inputs.items() if not input_rows]
    manual_completed = summary_value(inputs["manual_review"], "manual_review_completed") or "False"
    values_populated = summary_value(inputs["non_submitting_values"], "non_submitting_ticket_values_populated") or "False"
    quality_passed = summary_value(inputs["non_submitting_values_quality"], "quality_gate_passed") or "False"
    discussion_ready = str(not missing_inputs and manual_completed == "True" and values_populated == "True" and quality_passed == "True")
    data = [
        ("final_non_submitting_ticket_creation_readiness_status", READINESS_STATUS, "Ticket-creation readiness checkpoint status."),
        ("final_non_submitting_ticket_creation_readiness_decision", READINESS_DECISION, "Ready to discuss future non-submitting ticket creation only."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("manual_review_decision", summary_value(inputs["manual_review"], "final_non_submitting_executable_ticket_values_manual_review_decision") or "missing_manual_review", "Saved manual-review decision."),
        ("manual_review_completed", manual_completed, "Saved manual-review completion flag."),
        ("non_submitting_ticket_values_populated", values_populated, "Review values exist."),
        ("quality_gate_passed", quality_passed, "Quality gate passed only for non-submitting values."),
        ("ticket_creation_discussion_ready", discussion_ready, "True means future ticket-instance discussion can be considered."),
        ("ticket_creation_approved", "False", "No ticket creation approval exists."),
        ("ticket_instance_created", "False", "No ticket instance exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("broker_ready_order_values_populated", "False", "No broker-ready order values exist."),
        ("order_values_populated", "False", "No side, quantity, type, time-in-force, account, or broker id values are populated."),
        ("order_instructions_created", "False", "No order instructions exist."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("largest_blocker", "ticket_instance_not_created_or_approved", "Readiness is not ticket creation."),
        ("recommended_next_step", READINESS_NEXT_STEP, "Manual review before any ticket-instance checkpoint."),
        ("checkpoint_row_count", str(len(rows)), "Saved report row count."),
    ]
    return [summary_row(*item) for item in data]


def common_blockers(name: str) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", "Values are non-submitting and not broker-ready.", NEXT_STEP),
        blocker_row("ticket_instance_not_created", "blocked", "critical", "ticket_instance_created=false", "separate_future_ticket_creation_checkpoint_required"),
        blocker_row("order_instructions_not_created", "blocked", "critical", "order_instructions_created=false", "keep_order_instructions_blocked"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def review_evidence_rows_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in REVIEW_INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def readiness_evidence_rows_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = review_evidence_rows_for({key: value for key, value in inputs.items() if key in REVIEW_INPUT_FILES})
    rows.append(evidence_row("manual_review_input", f"{MANUAL_REVIEW_OUTPUTS['summary']}; rows={len(inputs.get('manual_review', []))}", "Saved manual-review input row count."))
    return rows


def value_row(name: str, status: str, value: str, source: str, why: str, boundary: str, review: str) -> dict[str, Any]:
    return {"ticket_value_name": name, "ticket_value_status": status, "ticket_value": value, "source_context": source, "why_reviewable": why, "why_not_broker_ready": boundary, "manual_review_requirement": review, **SAFETY_FLAGS}


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def write_values_outputs(
    root: Path,
    report_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    value_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    paths = {name: root / path for name, path in VALUES_OUTPUTS.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["values"], VALUE_COLUMNS, value_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def write_quality_outputs(root: Path, report_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in QUALITY_OUTPUTS.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def write_checkpoint_outputs(
    root: Path,
    paths_: dict[str, Path],
    report_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    paths = {name: root / path for name, path in paths_.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def values_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Non-submitting executable ticket values complete. Review only; no orders approved.",
        f"final_non_submitting_executable_ticket_values_status={summary_value(rows, 'final_non_submitting_executable_ticket_values_status')}",
        f"final_non_submitting_executable_ticket_values_decision={summary_value(rows, 'final_non_submitting_executable_ticket_values_decision')}",
        f"non_submitting_ticket_values_populated={summary_value(rows, 'non_submitting_ticket_values_populated')}",
        f"review_quantities_created={summary_value(rows, 'review_quantities_created')}",
        f"review_quantity_estimate_count={summary_value(rows, 'review_quantity_estimate_count')}",
        f"review_value_count={summary_value(rows, 'review_value_count')}",
        f"broker_ready_order_values_populated={summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def quality_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Non-submitting executable ticket values quality gate complete. No order approved.",
        f"final_non_submitting_executable_ticket_values_quality_status={summary_value(rows, 'final_non_submitting_executable_ticket_values_quality_status')}",
        f"final_non_submitting_executable_ticket_values_quality_decision={summary_value(rows, 'final_non_submitting_executable_ticket_values_quality_decision')}",
        f"quality_gate_passed={summary_value(rows, 'quality_gate_passed')}",
        f"review_quantity_quality_gate_passed={summary_value(rows, 'review_quantity_quality_gate_passed')}",
        f"review_quantity_estimate_count={summary_value(rows, 'review_quantity_estimate_count')}",
        f"review_value_count={summary_value(rows, 'review_value_count')}",
        f"forbidden_field_count={summary_value(rows, 'forbidden_field_count')}",
        f"broker_ready_order_values_populated={summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def checkpoint_lines(rows: list[dict[str, Any]], report_path: Path, mode: str) -> list[str]:
    if mode == "manual_review":
        return [
            "Non-submitting executable ticket values manual review complete. No ticket or order approved.",
            f"final_non_submitting_executable_ticket_values_manual_review_status={summary_value(rows, 'final_non_submitting_executable_ticket_values_manual_review_status')}",
            f"final_non_submitting_executable_ticket_values_manual_review_decision={summary_value(rows, 'final_non_submitting_executable_ticket_values_manual_review_decision')}",
            f"manual_review_completed={summary_value(rows, 'manual_review_completed')}",
            f"ticket_creation_discussion_ready={summary_value(rows, 'ticket_creation_discussion_ready')}",
            f"ticket_creation_approved={summary_value(rows, 'ticket_creation_approved')}",
            f"ticket_instance_created={summary_value(rows, 'ticket_instance_created')}",
            f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
            f"saved_report={report_path}",
            "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    return [
        "Non-submitting ticket creation readiness complete. Discussion only; no ticket created.",
        f"final_non_submitting_ticket_creation_readiness_status={summary_value(rows, 'final_non_submitting_ticket_creation_readiness_status')}",
        f"final_non_submitting_ticket_creation_readiness_decision={summary_value(rows, 'final_non_submitting_ticket_creation_readiness_decision')}",
        f"ticket_creation_discussion_ready={summary_value(rows, 'ticket_creation_discussion_ready')}",
        f"ticket_creation_approved={summary_value(rows, 'ticket_creation_approved')}",
        f"ticket_instance_created={summary_value(rows, 'ticket_instance_created')}",
        f"order_instructions_created={summary_value(rows, 'order_instructions_created')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
