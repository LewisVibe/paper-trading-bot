"""Non-submitting ticket-instance checkpoint for the volatility seed.

This checkpoint records a saved review artifact after ticket-creation
readiness. It is still not executable: broker-ready order fields stay blank,
no Alpaca or market-data calls happen, and no order approval is created.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
FINAL_STATUS = "vol_targeted_growth_non_submitting_ticket_instance_checkpoint_created_manual_review_required"
FINAL_DECISION = "NON_SUBMITTING_TICKET_INSTANCE_CHECKPOINT_CREATED_NO_ORDER_VALUES"
NEXT_STEP = "manual_review_non_submitting_ticket_instance_checkpoint_before_any_broker_ready_ticket_values"
QUALITY_PASS_STATUS = "vol_targeted_growth_non_submitting_ticket_instance_quality_gate_passed_manual_review_required"
QUALITY_BLOCKED_STATUS = "vol_targeted_growth_non_submitting_ticket_instance_quality_gate_blocked_manual_review_required"
QUALITY_PASS_DECISION = "NON_SUBMITTING_TICKET_INSTANCE_QUALITY_GATE_PASSED_NO_ORDER_VALUES"
QUALITY_BLOCKED_DECISION = "NON_SUBMITTING_TICKET_INSTANCE_QUALITY_GATE_BLOCKED_MANUAL_REVIEW_REQUIRED"
QUALITY_NEXT_STEP = "manual_review_pre_ticket_quality_gate_before_any_broker_ready_ticket_design"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_summary.csv"),
    "ticket": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_ticket.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_evidence.csv"),
}

QUALITY_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_non_submitting_ticket_instance_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_ticket_instance_quality_gate_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_ticket_instance_quality_gate_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_ticket_instance_quality_gate_evidence.csv"),
}

INPUT_FILES = {
    "ticket_creation_readiness": Path("data/vol_targeted_growth_non_submitting_ticket_creation_readiness_summary.csv"),
    "ticket_instance_design": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"),
    "non_submitting_values": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_summary.csv"),
    "non_submitting_values_quality": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_summary.csv"),
    "manual_review": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_manual_review_summary.csv"),
    "review_quantity_estimates": Path("data/vol_targeted_growth_review_quantity_estimates.csv"),
    "review_quantity_estimates_summary": Path("data/vol_targeted_growth_review_quantity_estimates_summary.csv"),
    "review_quantity_quality_gate": Path("data/vol_targeted_growth_review_quantity_quality_gate_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "non_submitting_only": True,
    "ticket_instance_checkpoint_created": True,
    "ticket_instance_created": False,
    "ticket_creation_approved": False,
    "broker_ready_order_values_populated": False,
    "order_values_populated": False,
    "order_instructions_created": False,
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

PROTECTED_ORDER_FIELDS = {
    "order_side",
    "order_quantity",
    "order_type",
    "time_in_force",
    "account_reference",
    "broker_order_id",
    "submit_instruction",
}

REVIEW_INPUT_FIELDS = {
    "review_quantity_estimates_decision",
    "review_quantity_quality_gate_decision",
    "review_quantity_estimate_count",
    "review_quantity_symbols",
    "review_share_quantity_estimates",
}

FORBIDDEN_VALUE_MARKERS = (
    "api_key",
    "secret",
    "token",
    "webhook",
    "account_id",
    "order_id",
)

REPORT_COLUMNS = ["check_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
TICKET_COLUMNS = ["ticket_field", "field_status", "field_value", "source_context", "why_reviewable", "why_not_broker_ready", "required_next_step", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class NonSubmittingTicketInstanceCheckpointResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    ticket_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class NonSubmittingTicketInstanceQualityGateResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_non_submitting_ticket_instance_checkpoint(
    root_dir: Path | str = ".",
) -> NonSubmittingTicketInstanceCheckpointResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    ticket_rows = build_ticket_rows(inputs)
    summary_rows = build_summary_rows(inputs, report_rows, ticket_rows)
    blocker_rows = build_blocker_rows(inputs)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = write_outputs(root, report_rows, summary_rows, ticket_rows, blocker_rows, evidence_rows)
    return NonSubmittingTicketInstanceCheckpointResult(
        output_paths,
        report_rows,
        summary_rows,
        ticket_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_non_submitting_ticket_instance_checkpoint(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted non-submitting ticket-instance checkpoint is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-ticket-instance-checkpoint` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted non-submitting ticket-instance checkpoint saved display. No executable ticket or order approved.",
        f"final_non_submitting_ticket_instance_checkpoint_status: {summary_value(rows, 'final_non_submitting_ticket_instance_checkpoint_status')}",
        f"final_non_submitting_ticket_instance_checkpoint_decision: {summary_value(rows, 'final_non_submitting_ticket_instance_checkpoint_decision')}",
        f"ticket_instance_checkpoint_created: {summary_value(rows, 'ticket_instance_checkpoint_created')}",
        f"ticket_instance_created: {summary_value(rows, 'ticket_instance_created')}",
        f"ticket_creation_approved: {summary_value(rows, 'ticket_creation_approved')}",
        f"review_quantities_created: {summary_value(rows, 'review_quantities_created')}",
        f"review_quantity_estimate_count: {summary_value(rows, 'review_quantity_estimate_count')}",
        f"review_quantity_quality_gate_passed: {summary_value(rows, 'review_quantity_quality_gate_passed')}",
        f"broker_ready_order_values_populated: {summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created: {summary_value(rows, 'order_instructions_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_non_submitting_ticket_instance_quality_gate(
    root_dir: Path | str = ".",
) -> NonSubmittingTicketInstanceQualityGateResult:
    root = Path(root_dir)
    checkpoint_summary = read_csv_rows(root / OUTPUT_FILES["summary"])
    checkpoint_ticket = read_csv_rows(root / OUTPUT_FILES["ticket"])
    checks = evaluate_quality_gate(checkpoint_summary, checkpoint_ticket)
    passed = all(check["status"] == "pass" for check in checks)
    report_rows = [quality_report_row(check) for check in checks]
    summary_rows = build_quality_summary_rows(checks, checkpoint_summary, checkpoint_ticket, passed)
    blocker_rows = build_quality_blocker_rows(checks)
    evidence_rows = build_quality_evidence_rows(checkpoint_summary, checkpoint_ticket)
    output_paths = write_quality_outputs(root, report_rows, summary_rows, blocker_rows, evidence_rows)
    return NonSubmittingTicketInstanceQualityGateResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        quality_summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_non_submitting_ticket_instance_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / QUALITY_OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted non-submitting ticket-instance quality gate is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-ticket-instance-quality-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted non-submitting ticket-instance quality gate display. Pre-ticket review only; no broker-ready order values.",
        f"final_non_submitting_ticket_instance_quality_status: {summary_value(rows, 'final_non_submitting_ticket_instance_quality_status')}",
        f"final_non_submitting_ticket_instance_quality_decision: {summary_value(rows, 'final_non_submitting_ticket_instance_quality_decision')}",
        f"pre_ticket_quality_gate_passed: {summary_value(rows, 'pre_ticket_quality_gate_passed')}",
        f"ticket_instance_checkpoint_present: {summary_value(rows, 'ticket_instance_checkpoint_present')}",
        f"ticket_instance_ticket_rows_present: {summary_value(rows, 'ticket_instance_ticket_rows_present')}",
        f"review_inputs_complete: {summary_value(rows, 'review_inputs_complete')}",
        f"protected_order_fields_blank: {summary_value(rows, 'protected_order_fields_blank')}",
        f"broker_ready_order_values_populated: {summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created: {summary_value(rows, 'order_instructions_created')}",
        f"broker_ready_field_violation_count: {summary_value(rows, 'broker_ready_field_violation_count')}",
        f"missing_review_input_count: {summary_value(rows, 'missing_review_input_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    readiness = summary_value(inputs["ticket_creation_readiness"], "final_non_submitting_ticket_creation_readiness_decision") or "missing_ticket_creation_readiness"
    discussion_ready = summary_value(inputs["ticket_creation_readiness"], "ticket_creation_discussion_ready") or "False"
    design = summary_value(inputs["ticket_instance_design"], "final_ticket_instance_design_decision") or "missing_ticket_instance_design"
    return [
        report_row("ticket_creation_readiness_present", "pass" if discussion_ready == "True" else "manual_review_required", "critical", readiness, "Readiness can allow discussion, but not ticket creation approval.", NEXT_STEP),
        report_row("ticket_instance_design_present", "pass" if design else "manual_review_required", "high", design, "Design context exists for a non-executable ticket shape.", NEXT_STEP),
        report_row("ticket_instance_boundary", "non_submitting_checkpoint_created", "critical", "ticket_instance_checkpoint_created=true; ticket_instance_created=false", "This is a checkpoint artifact only, not an executable ticket.", NEXT_STEP),
        report_row("order_value_boundary", "blocked", "critical", "side/quantity/type/time-in-force/account/broker fields blank", "No broker-ready order values or instructions are created.", "keep_order_values_blocked"),
        report_row("execution_boundary", "execution_blocked", "critical", "orders_submitted=false; execution_approved=false", "No order, execution, or scheduling is approved.", "keep_execution_blocked"),
    ]


def build_ticket_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    readiness = summary_value(inputs["ticket_creation_readiness"], "final_non_submitting_ticket_creation_readiness_decision") or "missing_ticket_creation_readiness"
    values_decision = summary_value(inputs["non_submitting_values"], "final_non_submitting_executable_ticket_values_decision") or "missing_non_submitting_values"
    quality_decision = summary_value(inputs["non_submitting_values_quality"], "final_non_submitting_executable_ticket_values_quality_decision") or "missing_quality_gate"
    manual_review = summary_value(inputs["manual_review"], "final_non_submitting_executable_ticket_values_manual_review_decision") or "missing_manual_review"
    quantity_context = build_review_quantity_context(inputs)
    items = [
        ("checkpoint_id", "review_context", "vol_targeted_growth_non_submitting_ticket_instance_checkpoint_v1", "local checkpoint id", "Identifies the saved review artifact.", "Not a broker id.", NEXT_STEP),
        ("active_seed", "review_context", ACTIVE_SEED, "fixed active seed", "Connects the checkpoint to the current seed.", "Does not approve the seed for orders.", NEXT_STEP),
        ("active_ticker", "review_context", ACTIVE_TICKER, "portfolio label", "Keeps this as a multi-sleeve portfolio label.", "Not a broker symbol.", NEXT_STEP),
        ("ticket_creation_readiness", "review_context", readiness, "saved readiness summary", "Shows discussion readiness context.", "Not approval to create a ticket.", NEXT_STEP),
        ("non_submitting_values_decision", "review_context", values_decision, "saved values summary", "Shows reviewable non-submitting values exist.", "Not broker-ready values.", NEXT_STEP),
        ("non_submitting_values_quality", "review_context", quality_decision, "saved quality summary", "Shows quality gate context.", "Still no order fields.", NEXT_STEP),
        ("manual_review_decision", "review_context", manual_review, "saved manual review summary", "Shows values review context.", "Still no execution approval.", NEXT_STEP),
        ("review_quantity_estimates_decision", "review_context", quantity_context["review_quantity_estimates_decision"], "saved review quantity summary", "Shows review-only quantity estimate status.", "Not an order quantity approval.", NEXT_STEP),
        ("review_quantity_quality_gate_decision", "review_context", quantity_context["review_quantity_quality_decision"], "saved review quantity quality gate", "Shows estimate quality context.", "Quality gate does not create orders.", NEXT_STEP),
        ("review_quantity_estimate_count", "review_context", quantity_context["review_quantity_estimate_count"], "saved review quantity rows", "Counts saved review estimate rows.", "A count is not a broker-ready quantity.", NEXT_STEP),
        ("review_quantity_symbols", "review_context", quantity_context["review_quantity_symbols"], "saved review quantity rows", "Lists symbols with saved review estimates.", "Symbols are context only and not routing instructions.", NEXT_STEP),
        ("review_share_quantity_estimates", "review_context", quantity_context["review_quantity_estimates"], "saved review quantity rows", "Carries review-only estimates into the checkpoint.", "These are not executable order quantities.", NEXT_STEP),
        ("order_side", "blocked_blank", "", "forbidden order field", "Requires a later separate approval if ever designed.", "Blank prevents buy/sell instruction.", "keep_blank"),
        ("order_quantity", "blocked_blank", "", "forbidden order field", "Requires a later separate approval if ever designed.", "Blank prevents quantity instruction.", "keep_blank"),
        ("order_type", "blocked_blank", "", "forbidden order field", "Requires a later separate approval if ever designed.", "Blank prevents order routing.", "keep_blank"),
        ("time_in_force", "blocked_blank", "", "forbidden order field", "Requires a later separate approval if ever designed.", "Blank prevents order routing.", "keep_blank"),
        ("account_reference", "forbidden_blank", "", "secret/account boundary", "Account ids must not be stored.", "No secrets or account ids.", "keep_blank"),
        ("broker_order_id", "forbidden_blank", "", "broker id boundary", "Broker ids must not be stored in this checkpoint.", "No order exists.", "keep_blank"),
        ("submit_instruction", "blocked_blank", "", "execution boundary", "Submission instructions require a future explicit execution step.", "No submit instruction.", "keep_blank"),
    ]
    return [ticket_row(*item) for item in items]


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    report_rows: list[dict[str, Any]],
    ticket_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    missing_inputs = [name for name, rows in inputs.items() if not rows]
    discussion_ready = summary_value(inputs["ticket_creation_readiness"], "ticket_creation_discussion_ready") or "False"
    quantity_context = build_review_quantity_context(inputs)
    data = [
        ("final_non_submitting_ticket_instance_checkpoint_status", FINAL_STATUS, "Saved non-submitting ticket-instance checkpoint status."),
        ("final_non_submitting_ticket_instance_checkpoint_decision", FINAL_DECISION, "Checkpoint created; no order values or executable ticket."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("ticket_creation_discussion_ready", discussion_ready, "Saved readiness context only."),
        ("review_quantity_estimates_decision", quantity_context["review_quantity_estimates_decision"], "Saved review quantity estimates decision."),
        ("review_quantities_created", quantity_context["review_quantities_created"], "True means review estimates exist; not order instructions."),
        ("review_quantity_estimate_count", quantity_context["review_quantity_estimate_count"], "Number of review-only quantity estimate rows carried into this checkpoint."),
        ("review_quantity_quality_gate_decision", quantity_context["review_quantity_quality_decision"], "Saved review quantity quality-gate decision."),
        ("review_quantity_quality_gate_passed", quantity_context["review_quantity_quality_gate_passed"], "True only means saved estimates are reviewable."),
        ("ticket_instance_checkpoint_created", "True", "A saved checkpoint artifact exists."),
        ("ticket_instance_created", "False", "No executable ticket instance exists."),
        ("ticket_creation_approved", "False", "No ticket creation approval exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("broker_ready_order_values_populated", "False", "No broker-ready values exist."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker id exists."),
        ("order_instructions_created", "False", "No order instructions exist."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("ticket_field_count", str(len(ticket_rows)), "Saved ticket checkpoint row count."),
        ("checkpoint_row_count", str(len(report_rows)), "Saved report row count."),
        ("missing_saved_input_count", str(len(missing_inputs)), "Missing saved inputs."),
        ("missing_saved_inputs", ";".join(missing_inputs) or "none", "Missing saved input names."),
        ("largest_blocker", "broker_ready_ticket_values_not_approved", "The checkpoint is not broker-ready and cannot create orders."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any broker-ready ticket values."),
    ]
    return [summary_row(*item) for item in data]


def build_review_quantity_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    quantity_rows = [
        row
        for row in inputs["review_quantity_estimates"]
        if row.get("quantity_estimate_status") == "review_quantity_estimate_created"
    ]
    symbols = ",".join(row.get("broker_symbol", "") for row in quantity_rows if row.get("broker_symbol")) or "none"
    estimates = "; ".join(
        f"{row.get('broker_symbol', 'UNKNOWN')}={row.get('review_share_quantity_estimate', 'missing')}"
        for row in quantity_rows
    ) or "missing_review_quantity_estimates"
    return {
        "review_quantity_estimates_decision": summary_value(inputs["review_quantity_estimates_summary"], "final_review_quantity_estimates_decision")
        or "missing_review_quantity_estimates",
        "review_quantities_created": summary_value(inputs["review_quantity_estimates_summary"], "review_quantities_created") or "False",
        "review_quantity_quality_decision": summary_value(inputs["review_quantity_quality_gate"], "final_review_quantity_quality_decision")
        or "missing_review_quantity_quality_gate",
        "review_quantity_quality_gate_passed": summary_value(inputs["review_quantity_quality_gate"], "review_quantity_quality_gate_passed")
        or "False",
        "review_quantity_estimate_count": str(len(quantity_rows)),
        "review_quantity_symbols": symbols,
        "review_quantity_estimates": estimates,
    }


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("broker_ready_ticket_values_not_approved", "blocked", "critical", "No side, quantity, order type, time-in-force, account, or broker id is populated.", NEXT_STEP),
        blocker_row("ticket_creation_not_approved", "blocked", "critical", "ticket_creation_approved=false", "separate_future_approval_required"),
        blocker_row("ticket_instance_not_created", "blocked", "critical", "ticket_instance_created=false", "keep_checkpoint_non_executable"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
    ]
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def evaluate_quality_gate(
    checkpoint_summary: list[dict[str, str]],
    checkpoint_ticket: list[dict[str, str]],
) -> list[dict[str, str]]:
    ticket_fields = {row.get("ticket_field", ""): row for row in checkpoint_ticket}
    missing_protected = sorted(PROTECTED_ORDER_FIELDS - set(ticket_fields))
    protected_violations = [
        field
        for field in sorted(PROTECTED_ORDER_FIELDS & set(ticket_fields))
        if str(ticket_fields[field].get("field_value", "")).strip()
    ]
    missing_review_inputs = [
        field
        for field in sorted(REVIEW_INPUT_FIELDS)
        if not str(ticket_fields.get(field, {}).get("field_value", "")).strip()
        or str(ticket_fields.get(field, {}).get("field_value", "")).strip().startswith("missing_")
    ]
    forbidden_value_hits = find_forbidden_value_hits(checkpoint_ticket)
    approval_violations = {
        key: summary_value(checkpoint_summary, key)
        for key in [
            "ticket_instance_created",
            "ticket_creation_approved",
            "broker_ready_order_values_populated",
            "order_values_populated",
            "order_instructions_created",
            "executable_ticket_created",
            "orders_submitted",
            "execution_approved",
            "paper_execution_approved",
            "scheduling_approved",
        ]
        if (summary_value(checkpoint_summary, key) or "False") != "False"
    }
    review_quantity_count = parse_int(summary_value(checkpoint_summary, "review_quantity_estimate_count"))
    checks = [
        quality_check(
            "checkpoint_summary_present",
            bool(checkpoint_summary),
            f"rows={len(checkpoint_summary)}",
            "Refresh the non-submitting ticket-instance checkpoint first.",
        ),
        quality_check(
            "checkpoint_ticket_rows_present",
            bool(checkpoint_ticket),
            f"rows={len(checkpoint_ticket)}",
            "Refresh the non-submitting ticket-instance checkpoint ticket rows first.",
        ),
        quality_check(
            "review_quantity_estimates_present",
            (summary_value(checkpoint_summary, "review_quantities_created") == "True" and review_quantity_count > 0),
            f"review_quantities_created={summary_value(checkpoint_summary, 'review_quantities_created') or 'False'}; review_quantity_estimate_count={review_quantity_count}",
            "Refresh saved review quantity estimates before broker-ready ticket design discussion.",
        ),
        quality_check(
            "review_quantity_quality_gate_passed",
            summary_value(checkpoint_summary, "review_quantity_quality_gate_passed") == "True",
            f"review_quantity_quality_gate_passed={summary_value(checkpoint_summary, 'review_quantity_quality_gate_passed') or 'False'}",
            "Pass the saved review quantity quality gate first.",
        ),
        quality_check(
            "review_inputs_complete",
            not missing_review_inputs,
            f"missing_review_inputs={';'.join(missing_review_inputs) or 'none'}",
            "Refresh missing review inputs before broker-ready ticket design discussion.",
        ),
        quality_check(
            "protected_order_fields_present",
            not missing_protected,
            f"missing_protected_fields={';'.join(missing_protected) or 'none'}",
            "Regenerate checkpoint with explicit protected blank order fields.",
        ),
        quality_check(
            "protected_order_fields_blank",
            not protected_violations,
            f"populated_protected_fields={';'.join(protected_violations) or 'none'}",
            "Remove broker-ready order values from the checkpoint.",
        ),
        quality_check(
            "forbidden_secret_or_broker_values_absent",
            not forbidden_value_hits,
            f"forbidden_value_hits={';'.join(forbidden_value_hits) or 'none'}",
            "Remove secret, account, webhook, token, or broker-id-like values.",
        ),
        quality_check(
            "approval_flags_false",
            not approval_violations,
            f"approval_violations={format_mapping(approval_violations)}",
            "Reset any approval-like value to false before continuing.",
        ),
    ]
    return checks


def build_quality_summary_rows(
    checks: list[dict[str, str]],
    checkpoint_summary: list[dict[str, str]],
    checkpoint_ticket: list[dict[str, str]],
    passed: bool,
) -> list[dict[str, Any]]:
    failed = [check for check in checks if check["status"] != "pass"]
    protected_fields = {row.get("ticket_field", ""): row for row in checkpoint_ticket if row.get("ticket_field", "") in PROTECTED_ORDER_FIELDS}
    protected_violations = [
        field for field, row in protected_fields.items() if str(row.get("field_value", "")).strip()
    ]
    missing_review_inputs = [
        check["check_name"]
        for check in checks
        if check["check_name"] in {"review_quantity_estimates_present", "review_quantity_quality_gate_passed", "review_inputs_complete"}
        and check["status"] != "pass"
    ]
    status = QUALITY_PASS_STATUS if passed else QUALITY_BLOCKED_STATUS
    decision = QUALITY_PASS_DECISION if passed else QUALITY_BLOCKED_DECISION
    largest_blocker = "broker_ready_ticket_values_still_not_approved" if passed else failed[0]["check_name"]
    data = [
        ("final_non_submitting_ticket_instance_quality_status", status, "Saved pre-ticket quality-gate status."),
        ("final_non_submitting_ticket_instance_quality_decision", decision, "Gate result; no broker-ready order values are created."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("pre_ticket_quality_gate_passed", str(passed), "True only when saved review context is complete and protected fields are blank."),
        ("ticket_instance_checkpoint_present", str(bool(checkpoint_summary)), "Checkpoint summary availability."),
        ("ticket_instance_ticket_rows_present", str(bool(checkpoint_ticket)), "Checkpoint ticket rows availability."),
        ("review_inputs_complete", str(not missing_review_inputs), "Review quantity context must be present and quality-gated."),
        ("protected_order_fields_blank", str(not protected_violations), "Protected broker-ready fields must stay blank."),
        ("broker_ready_field_violation_count", str(len(protected_violations)), "Protected fields with populated values."),
        ("missing_review_input_count", str(len(missing_review_inputs)), "Missing or failed review-input checks."),
        ("ticket_instance_checkpoint_created", summary_value(checkpoint_summary, "ticket_instance_checkpoint_created") or "False", "Saved checkpoint artifact state."),
        ("ticket_instance_created", "False", "No executable ticket instance exists."),
        ("ticket_creation_approved", "False", "No ticket creation approval exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("broker_ready_order_values_populated", "False", "No broker-ready values exist."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker id exists."),
        ("order_instructions_created", "False", "No order instructions exist."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("check_count", str(len(checks)), "Quality checks evaluated."),
        ("pass_count", str(sum(1 for check in checks if check["status"] == "pass")), "Passing quality checks."),
        ("blocked_count", str(len(failed)), "Blocked quality checks."),
        ("largest_blocker", largest_blocker, "Primary blocker. Passing still does not approve broker-ready tickets."),
        ("recommended_next_step", QUALITY_NEXT_STEP, "Manual review before any broker-ready ticket design."),
    ]
    return [summary_row(*item) for item in data]


def build_quality_blocker_rows(checks: list[dict[str, str]]) -> list[dict[str, Any]]:
    blocked = [check for check in checks if check["status"] != "pass"]
    rows = [
        blocker_row(
            "broker_ready_ticket_values_still_not_approved",
            "blocked",
            "critical",
            "Quality gate is pre-ticket only and never approves broker-ready values.",
            QUALITY_NEXT_STEP,
        )
    ]
    rows.extend(
        blocker_row(check["check_name"], "blocked", "high", check["evidence"], check["required_next_step"])
        for check in blocked
    )
    return rows


def build_quality_evidence_rows(
    checkpoint_summary: list[dict[str, str]],
    checkpoint_ticket: list[dict[str, str]],
) -> list[dict[str, Any]]:
    protected_blank_count = sum(
        1
        for row in checkpoint_ticket
        if row.get("ticket_field", "") in PROTECTED_ORDER_FIELDS and not str(row.get("field_value", "")).strip()
    )
    return [
        evidence_row("checkpoint_summary_rows", str(len(checkpoint_summary)), "Saved checkpoint summary rows read."),
        evidence_row("checkpoint_ticket_rows", str(len(checkpoint_ticket)), "Saved checkpoint ticket rows read."),
        evidence_row("protected_blank_field_count", str(protected_blank_count), "Protected order fields that remain blank."),
        evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."),
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def write_outputs(
    root: Path,
    report_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    ticket_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["ticket"], TICKET_COLUMNS, ticket_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def write_quality_outputs(
    root: Path,
    report_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    paths = {name: root / path for name, path in QUALITY_OUTPUT_FILES.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Non-submitting ticket-instance checkpoint complete. No executable ticket or order approved.",
        f"final_non_submitting_ticket_instance_checkpoint_status={summary_value(rows, 'final_non_submitting_ticket_instance_checkpoint_status')}",
        f"final_non_submitting_ticket_instance_checkpoint_decision={summary_value(rows, 'final_non_submitting_ticket_instance_checkpoint_decision')}",
        f"ticket_instance_checkpoint_created={summary_value(rows, 'ticket_instance_checkpoint_created')}",
        f"ticket_instance_created={summary_value(rows, 'ticket_instance_created')}",
        f"ticket_creation_approved={summary_value(rows, 'ticket_creation_approved')}",
        f"review_quantities_created={summary_value(rows, 'review_quantities_created')}",
        f"review_quantity_estimate_count={summary_value(rows, 'review_quantity_estimate_count')}",
        f"review_quantity_quality_gate_passed={summary_value(rows, 'review_quantity_quality_gate_passed')}",
        f"broker_ready_order_values_populated={summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created={summary_value(rows, 'order_instructions_created')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def quality_summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Non-submitting ticket-instance quality gate complete. Pre-ticket review only; no executable ticket or order approved.",
        f"final_non_submitting_ticket_instance_quality_status={summary_value(rows, 'final_non_submitting_ticket_instance_quality_status')}",
        f"final_non_submitting_ticket_instance_quality_decision={summary_value(rows, 'final_non_submitting_ticket_instance_quality_decision')}",
        f"pre_ticket_quality_gate_passed={summary_value(rows, 'pre_ticket_quality_gate_passed')}",
        f"ticket_instance_checkpoint_present={summary_value(rows, 'ticket_instance_checkpoint_present')}",
        f"ticket_instance_ticket_rows_present={summary_value(rows, 'ticket_instance_ticket_rows_present')}",
        f"review_inputs_complete={summary_value(rows, 'review_inputs_complete')}",
        f"protected_order_fields_blank={summary_value(rows, 'protected_order_fields_blank')}",
        f"broker_ready_order_values_populated={summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created={summary_value(rows, 'order_instructions_created')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def ticket_row(field: str, status: str, value: str, source: str, why: str, boundary: str, next_step: str) -> dict[str, Any]:
    return {"ticket_field": field, "field_status": status, "field_value": value, "source_context": source, "why_reviewable": why, "why_not_broker_ready": boundary, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def quality_check(name: str, passed: bool, evidence: str, next_step: str) -> dict[str, str]:
    return {
        "check_name": name,
        "status": "pass" if passed else "blocked",
        "risk_level": "low" if passed else "high",
        "evidence": evidence,
        "interpretation": "Pre-ticket quality requirement satisfied." if passed else "Manual review required before any broker-ready ticket design.",
        "required_next_step": "continue_manual_review_only" if passed else next_step,
    }


def quality_report_row(check: dict[str, str]) -> dict[str, Any]:
    return {
        "check_name": check["check_name"],
        "status": check["status"],
        "risk_level": check["risk_level"],
        "evidence": check["evidence"],
        "interpretation": check["interpretation"],
        "required_next_step": check["required_next_step"],
        **SAFETY_FLAGS,
    }


def find_forbidden_value_hits(rows: list[dict[str, str]]) -> list[str]:
    hits: list[str] = []
    for row in rows:
        field = row.get("ticket_field", "")
        value = str(row.get("field_value", "")).lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in value:
                hits.append(f"{field}:{marker}")
    return hits


def parse_int(value: str) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 0


def format_mapping(values: dict[str, str]) -> str:
    if not values:
        return "none"
    return ";".join(f"{key}={value}" for key, value in sorted(values.items()))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
