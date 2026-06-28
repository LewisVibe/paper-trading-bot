"""Non-submitting executable ticket schema design for the volatility seed.

This report documents the shape and safety checks for a future ticket layer
only. It does not create a ticket instance, populate order fields, call Alpaca,
read positions, submit orders, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_SEED = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"
FINAL_STATUS = "vol_targeted_growth_non_submitting_ticket_schema_design_created_manual_review_required"
FINAL_DECISION = "NON_SUBMITTING_TICKET_SCHEMA_DESIGNED_NO_TICKET_CREATED"
NEXT_STEP = "manual_review_non_submitting_ticket_schema_before_any_ticket_instance_or_broker_refresh"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_non_submitting_ticket_schema_design.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_ticket_schema_design_summary.csv"),
    "schema": Path("data/vol_targeted_growth_non_submitting_ticket_schema_design_schema.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_ticket_schema_design_blockers.csv"),
}

INPUT_FILES = {
    "approval_gate": Path("data/vol_targeted_growth_manual_execution_design_approval_gate_summary.csv"),
    "gap_list": Path("data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "schema_design_only": True,
    "non_submitting": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "order_instructions_created": False,
    "order_values_populated": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "manual_execution_design_approved": True,
    "manual_execution_design_approval_recorded_by_gate": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REPORT_COLUMNS = [
    "design_item",
    "status",
    "risk_level",
    "design_detail",
    "safety_boundary",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
SCHEMA_COLUMNS = [
    "field_name",
    "field_role",
    "required_for_future_ticket",
    "current_value",
    "allowed_values_or_rule",
    "safety_note",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthNonSubmittingTicketSchemaDesignResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    schema_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_non_submitting_ticket_schema_design(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthNonSubmittingTicketSchemaDesignResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(inputs, report_rows)
    schema_rows = build_schema_rows()
    blocker_rows = build_blocker_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["schema"], SCHEMA_COLUMNS, schema_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthNonSubmittingTicketSchemaDesignResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        schema_rows=schema_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_non_submitting_ticket_schema_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted non-submitting ticket schema design is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-ticket-schema-design` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted non-submitting ticket schema design saved display. Design only; no ticket created.",
        f"final_schema_design_status: {summary_value(rows, 'final_schema_design_status')}",
        f"final_schema_design_decision: {summary_value(rows, 'final_schema_design_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"schema_field_count: {summary_value(rows, 'schema_field_count')}",
        f"ticket_instance_created: {summary_value(rows, 'ticket_instance_created')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "non_submitting=true; executable_ticket_created=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: schema design only; no Alpaca, broker read, ticket instance, order, live trading, or scheduling approval.",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    approval_decision = summary_value(inputs["approval_gate"], "final_approval_gate_decision") or "missing_approval_gate_summary"
    gap_decision = summary_value(inputs["gap_list"], "final_ticket_design_decision") or "missing_gap_list_summary"
    go_no_go = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard"
    rows = [
        design_row(
            "scope",
            "designed_for_review",
            "high",
            f"Schema is scoped only to {ACTIVE_SEED} / {ACTIVE_TICKER}.",
            "No other strategy, high-growth branch, crypto sleeve, SMA, or slow-SMA path is included.",
            "manual_review_schema_scope",
        ),
        design_row(
            "non_submitting_boundary",
            "designed_for_review",
            "critical",
            "Ticket schema may describe future fields but cannot submit, create, cancel, replace, or prepare orders.",
            "ticket_instance_created=false; orders_submitted=false",
            "keep_schema_non_submitting",
        ),
        design_row(
            "field_population_boundary",
            "designed_for_review",
            "critical",
            "Future order-related fields must remain blank until a separate ticket-instance command is approved.",
            "order_values_populated=false",
            "separate_ticket_instance_design_required",
        ),
        design_row(
            "approval_gate_context",
            "manual_review_required",
            "high",
            approval_decision,
            "User approved this design step in chat, but the saved approval gate itself still does not approve execution.",
            "review_approval_gate_before_ticket_instance",
        ),
        design_row(
            "gap_list_context",
            "manual_review_required",
            "high",
            gap_decision,
            "The gap list remains an input to review; this schema does not clear those gaps.",
            "review_gap_list_before_ticket_instance",
        ),
        design_row(
            "go_no_go_context",
            "blocked",
            "critical",
            go_no_go,
            "The current go/no-go dashboard remains monitor-only/no-go unless separately changed.",
            "review_go_no_go_before_ticket_instance",
        ),
    ]
    return rows


def build_schema_rows() -> list[dict[str, Any]]:
    rows = [
        ("ticket_id", "identifier", "future_required", "", "generated opaque local identifier only; no broker order id", "Must never contain broker order IDs or account IDs."),
        ("strategy_name", "scope", "future_required", ACTIVE_SEED, f"must equal {ACTIVE_SEED}", "Fixed to the approved design scope."),
        ("ticker_scope", "scope", "future_required", ACTIVE_TICKER, f"must equal {ACTIVE_TICKER}", "Portfolio label only, not a broker symbol."),
        ("candidate_symbols", "mapping_context", "future_required", "", "future reviewed mapping only; blank in schema design", "No tradable symbols are populated by this design."),
        ("desired_target_state", "target_context", "future_required", "", "review_only_target_state; blank in schema design", "No buy/sell instruction is created."),
        ("max_total_allocation_pct", "risk_limit", "future_required", "", "0 until separately approved; numeric cap required later", "No allocation cap is approved here."),
        ("per_symbol_cap_pct", "risk_limit", "future_required", "", "0 until separately approved; numeric cap required later", "No symbol cap is approved here."),
        ("fresh_broker_check_reference", "evidence_reference", "future_required", "", "must reference separately approved read-only broker check later", "This design does not read broker state."),
        ("manual_review_reference", "approval_reference", "future_required", "", "must reference future explicit ticket-instance approval", "Current design approval is not order approval."),
        ("ticket_status", "state", "future_required", "schema_only", "schema_only|draft_non_submitting|blocked|void", "Cannot be submit_ready in this design."),
        ("order_side", "forbidden_current_value", "future_conditional", "", "blank in schema design", "No side is populated."),
        ("order_quantity", "forbidden_current_value", "future_conditional", "", "blank in schema design", "No quantity is populated."),
        ("order_type", "forbidden_current_value", "future_conditional", "", "blank in schema design", "No order type is populated."),
        ("time_in_force", "forbidden_current_value", "future_conditional", "", "blank in schema design", "No time-in-force is populated."),
    ]
    return [schema_row(*item) for item in rows]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_inputs = [name for name, rows in inputs.items() if not rows]
    data = [
        ("final_schema_design_status", FINAL_STATUS, "Non-submitting schema design is created for manual review."),
        ("final_schema_design_decision", FINAL_DECISION, "No ticket instance or order instruction is created."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("schema_field_count", str(len(build_schema_rows())), "Number of schema rows documented."),
        ("design_scope_user_approved_current_prompt", "True", "User explicitly approved this non-submitting design step in chat."),
        ("ticket_instance_created", "False", "No actual ticket row is created."),
        ("order_values_populated", "False", "No side, quantity, order type, or time-in-force values are populated."),
        ("largest_blocker", "ticket_instance_not_approved", "Next step cannot create a ticket without separate approval."),
        ("missing_saved_input_count", str(len(missing_inputs)), "Missing saved input summaries."),
        ("missing_saved_inputs", ";".join(missing_inputs) or "none", "Saved inputs missing from this schema design."),
        ("recommended_next_step", NEXT_STEP, "Manual review the schema before any future ticket-instance design."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("ticket_instance_not_approved", "blocked", "critical", "No actual ticket instance may be created by this schema design.", "separate_ticket_instance_approval_required"),
        blocker_row("order_values_not_approved", "blocked", "critical", "No side, quantity, order type, or time-in-force values may be populated.", "separate_ticket_instance_approval_required"),
        blocker_row("broker_state_not_read", "blocked", "critical", "No fresh broker state is read by this report.", "separate_readonly_broker_check_required_before_ticket_instance"),
        blocker_row("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "keep_all_execution_flags_false"),
    ]
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted non-submitting ticket schema design complete. Design only; no ticket or execution approved.",
        f"final_schema_design_status={summary_value(summary_rows, 'final_schema_design_status')}",
        f"final_schema_design_decision={summary_value(summary_rows, 'final_schema_design_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"schema_field_count={summary_value(summary_rows, 'schema_field_count')}",
        f"ticket_instance_created={summary_value(summary_rows, 'ticket_instance_created')}",
        f"order_values_populated={summary_value(summary_rows, 'order_values_populated')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "non_submitting=true; executable_ticket_created=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def design_row(
    name: str,
    status: str,
    risk: str,
    detail: str,
    boundary: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "design_item": name,
        "status": status,
        "risk_level": risk,
        "design_detail": detail,
        "safety_boundary": boundary,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def schema_row(
    field_name: str,
    field_role: str,
    required: str,
    current_value: str,
    allowed_values: str,
    safety_note: str,
) -> dict[str, Any]:
    return {
        "field_name": field_name,
        "field_role": field_role,
        "required_for_future_ticket": required,
        "current_value": current_value,
        "allowed_values_or_rule": allowed_values,
        "safety_note": safety_note,
        **dict(SAFETY_FLAGS),
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **dict(SAFETY_FLAGS)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
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
