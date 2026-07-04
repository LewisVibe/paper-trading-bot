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

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_summary.csv"),
    "ticket": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_ticket.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_evidence.csv"),
}

INPUT_FILES = {
    "ticket_creation_readiness": Path("data/vol_targeted_growth_non_submitting_ticket_creation_readiness_summary.csv"),
    "ticket_instance_design": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"),
    "non_submitting_values": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_summary.csv"),
    "non_submitting_values_quality": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate_summary.csv"),
    "manual_review": Path("data/vol_targeted_growth_non_submitting_executable_ticket_values_manual_review_summary.csv"),
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
        f"broker_ready_order_values_populated: {summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created: {summary_value(rows, 'order_instructions_created')}",
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
    items = [
        ("checkpoint_id", "review_context", "vol_targeted_growth_non_submitting_ticket_instance_checkpoint_v1", "local checkpoint id", "Identifies the saved review artifact.", "Not a broker id.", NEXT_STEP),
        ("active_seed", "review_context", ACTIVE_SEED, "fixed active seed", "Connects the checkpoint to the current seed.", "Does not approve the seed for orders.", NEXT_STEP),
        ("active_ticker", "review_context", ACTIVE_TICKER, "portfolio label", "Keeps this as a multi-sleeve portfolio label.", "Not a broker symbol.", NEXT_STEP),
        ("ticket_creation_readiness", "review_context", readiness, "saved readiness summary", "Shows discussion readiness context.", "Not approval to create a ticket.", NEXT_STEP),
        ("non_submitting_values_decision", "review_context", values_decision, "saved values summary", "Shows reviewable non-submitting values exist.", "Not broker-ready values.", NEXT_STEP),
        ("non_submitting_values_quality", "review_context", quality_decision, "saved quality summary", "Shows quality gate context.", "Still no order fields.", NEXT_STEP),
        ("manual_review_decision", "review_context", manual_review, "saved manual review summary", "Shows values review context.", "Still no execution approval.", NEXT_STEP),
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
    data = [
        ("final_non_submitting_ticket_instance_checkpoint_status", FINAL_STATUS, "Saved non-submitting ticket-instance checkpoint status."),
        ("final_non_submitting_ticket_instance_checkpoint_decision", FINAL_DECISION, "Checkpoint created; no order values or executable ticket."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("ticket_creation_discussion_ready", discussion_ready, "Saved readiness context only."),
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


def summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Non-submitting ticket-instance checkpoint complete. No executable ticket or order approved.",
        f"final_non_submitting_ticket_instance_checkpoint_status={summary_value(rows, 'final_non_submitting_ticket_instance_checkpoint_status')}",
        f"final_non_submitting_ticket_instance_checkpoint_decision={summary_value(rows, 'final_non_submitting_ticket_instance_checkpoint_decision')}",
        f"ticket_instance_checkpoint_created={summary_value(rows, 'ticket_instance_checkpoint_created')}",
        f"ticket_instance_created={summary_value(rows, 'ticket_instance_created')}",
        f"ticket_creation_approved={summary_value(rows, 'ticket_creation_approved')}",
        f"broker_ready_order_values_populated={summary_value(rows, 'broker_ready_order_values_populated')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created={summary_value(rows, 'order_instructions_created')}",
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
