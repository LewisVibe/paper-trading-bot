"""Non-submitting ticket-instance design for the volatility seed.

This report creates a saved design checkpoint for what a future ticket
instance record would need to contain. It intentionally does not create an
executable ticket, populate order values, call Alpaca, read positions, submit
orders, schedule anything, or approve execution.
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
FINAL_STATUS = "vol_targeted_growth_non_submitting_ticket_instance_design_created_manual_review_required"
FINAL_DECISION = "NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES"
NEXT_STEP = "manual_review_non_submitting_ticket_instance_before_any_fresh_broker_pre_ticket_gate"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"),
    "ticket": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_ticket.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_blockers.csv"),
}

INPUT_FILES = {
    "schema_design": Path("data/vol_targeted_growth_non_submitting_ticket_schema_design_summary.csv"),
    "approval_gate": Path("data/vol_targeted_growth_manual_execution_design_approval_gate_summary.csv"),
    "gap_list": Path("data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "ticket_instance_design_only": True,
    "non_submitting": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "ticket_instance_created": False,
    "ticket_instance_design_created": True,
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
TICKET_COLUMNS = [
    "ticket_field",
    "field_status",
    "draft_value",
    "why_blank_or_blocked",
    "future_requirement",
    "safety_note",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthNonSubmittingTicketInstanceDesignResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    ticket_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_non_submitting_ticket_instance_design(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthNonSubmittingTicketInstanceDesignResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(inputs)
    ticket_rows = build_ticket_rows(inputs)
    blocker_rows = build_blocker_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["ticket"], TICKET_COLUMNS, ticket_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthNonSubmittingTicketInstanceDesignResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        ticket_rows=ticket_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_non_submitting_ticket_instance_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted non-submitting ticket-instance design is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-ticket-instance-design` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted non-submitting ticket-instance design saved display. Design only; no executable ticket.",
        f"final_ticket_instance_design_status: {summary_value(rows, 'final_ticket_instance_design_status')}",
        f"final_ticket_instance_design_decision: {summary_value(rows, 'final_ticket_instance_design_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"ticket_field_count: {summary_value(rows, 'ticket_field_count')}",
        f"ticket_instance_created: {summary_value(rows, 'ticket_instance_created')}",
        f"executable_ticket_created: {summary_value(rows, 'executable_ticket_created')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "non_submitting=true; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: ticket-instance design only; no Alpaca, broker read, order values, order, live trading, or scheduling approval.",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    schema_decision = summary_value(inputs["schema_design"], "final_schema_design_decision") or "missing_schema_design_summary"
    approval_decision = summary_value(inputs["approval_gate"], "final_approval_gate_decision") or "missing_approval_gate_summary"
    gap_decision = summary_value(inputs["gap_list"], "final_ticket_design_decision") or "missing_gap_list_summary"
    go_no_go = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard"
    return [
        design_row("scope", "designed_for_review", "high", f"Draft ticket-instance shape is scoped only to {ACTIVE_SEED}.", "No other strategy or sleeve is made executable.", "manual_review_ticket_instance_scope"),
        design_row("schema_context", "manual_review_required", "high", schema_decision, "Schema design is input context only, not an executable ticket.", "review_schema_before_ticket_instance"),
        design_row("approval_gate_context", "manual_review_required", "high", approval_decision, "The saved approval gate still does not record execution approval.", "review_approval_gate_before_ticket_instance"),
        design_row("gap_list_context", "blocked", "critical", gap_decision, "Critical executable ticket gaps remain open.", "keep_ticket_non_submitting"),
        design_row("go_no_go_context", "blocked", "critical", go_no_go, "The paper-live go/no-go dashboard remains monitor-only/no-go.", "keep_go_no_go_blocking_execution"),
        design_row("order_value_boundary", "blocked", "critical", "Side, quantity, order type, time-in-force, account, broker order id, and submit-ready state remain blank.", "No executable order instructions are created.", "separate_fresh_broker_pre_ticket_gate_required"),
    ]


def build_ticket_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    schema_status = summary_value(inputs["schema_design"], "final_schema_design_status") or "missing_schema_design_summary"
    rows = [
        ("ticket_design_id", "draft_context", "vol_targeted_growth_ticket_design_v1", "Opaque local design id only.", "Future ticket instance needs an opaque local id.", "Not a broker order id."),
        ("strategy_name", "draft_context", ACTIVE_SEED, "Fixed research/status seed context.", f"Must equal {ACTIVE_SEED}.", "Does not approve the strategy for execution."),
        ("ticker_scope", "draft_context", ACTIVE_TICKER, "Portfolio label only.", f"Must equal {ACTIVE_TICKER}.", "Not a broker symbol."),
        ("previous_seed_context", "draft_context", f"{PREVIOUS_SEED}/{PREVIOUS_TICKER}", "Keeps QQQ100 as prior context.", "Manual review must consider existing QQQ exposure.", "No repeat/follow-up order is approved."),
        ("schema_design_reference", "draft_context", schema_status, "Saved schema output reference only.", "Schema must exist before future ticket instance.", "Reference only; no order values."),
        ("candidate_symbols", "blocked_blank", "", "No sleeve-to-symbol mapping is executable yet.", "Requires separate sleeve mapping and fresh broker review.", "Blank prevents order construction."),
        ("desired_target_state", "blocked_blank", "", "No desired buy/sell/hold state is approved.", "Requires separate ticket-instance approval.", "Blank prevents order construction."),
        ("order_side", "blocked_blank", "", "Side is not approved.", "Requires separate fresh broker pre-ticket gate and manual approval.", "No buy/sell instruction."),
        ("order_quantity", "blocked_blank", "", "Quantity is not approved.", "Requires exact sizing design and broker state.", "No quantity instruction."),
        ("order_type", "blocked_blank", "", "Order type is not approved.", "Requires separate order design.", "No order type instruction."),
        ("time_in_force", "blocked_blank", "", "Time-in-force is not approved.", "Requires separate order design.", "No order-routing instruction."),
        ("account_reference", "forbidden_blank", "", "Account identifiers are forbidden in saved outputs.", "Never store account ids in this report.", "No secrets/account ids."),
        ("broker_order_id", "forbidden_blank", "", "Broker order ids are forbidden in design outputs.", "Only post-order read-only reports may refer to redacted broker context later.", "No broker id."),
        ("ticket_status", "draft_non_submitting", "design_only_blocked", "Ticket remains non-submitting.", "Future statuses must remain blocked until separate approval.", "Not submit-ready."),
    ]
    return [ticket_row(*item) for item in rows]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    missing_inputs = [name for name, rows in inputs.items() if not rows]
    data = [
        ("final_ticket_instance_design_status", FINAL_STATUS, "Non-submitting ticket-instance design is created for manual review."),
        ("final_ticket_instance_design_decision", FINAL_DECISION, "No executable ticket or order values are created."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("ticket_field_count", str(len(build_ticket_rows(inputs))), "Number of draft ticket fields documented."),
        ("ticket_instance_design_created", "True", "A non-submitting design artifact was created."),
        ("ticket_instance_created", "False", "No executable ticket instance is created."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker order id is populated."),
        ("largest_blocker", "fresh_broker_pre_ticket_gate_not_created", "A future fresh broker pre-ticket gate is required before any ticket instance discussion."),
        ("missing_saved_input_count", str(len(missing_inputs)), "Missing saved input summaries."),
        ("missing_saved_inputs", ";".join(missing_inputs) or "none", "Saved inputs missing from this ticket-instance design."),
        ("recommended_next_step", NEXT_STEP, "Manual review this design before a future fresh broker pre-ticket gate."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("fresh_broker_pre_ticket_gate_not_created", "blocked", "critical", "A separate fresh read-only broker pre-ticket gate does not exist yet.", "design_fresh_broker_pre_ticket_gate_only_after_manual_review"),
        blocker_row("order_values_not_approved", "blocked", "critical", "No side, quantity, order type, time-in-force, account, or broker order id may be populated.", "keep_order_fields_blank"),
        blocker_row("executable_ticket_not_approved", "blocked", "critical", "This design cannot be submitted or converted to an order.", "separate_manual_approval_required"),
        blocker_row("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted non-submitting ticket-instance design complete. Design only; no executable ticket or execution approved.",
        f"final_ticket_instance_design_status={summary_value(summary_rows, 'final_ticket_instance_design_status')}",
        f"final_ticket_instance_design_decision={summary_value(summary_rows, 'final_ticket_instance_design_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"ticket_field_count={summary_value(summary_rows, 'ticket_field_count')}",
        f"ticket_instance_created={summary_value(summary_rows, 'ticket_instance_created')}",
        f"executable_ticket_created={summary_value(summary_rows, 'executable_ticket_created')}",
        f"order_values_populated={summary_value(summary_rows, 'order_values_populated')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "non_submitting=true; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def design_row(name: str, status: str, risk: str, detail: str, boundary: str, next_step: str) -> dict[str, Any]:
    return {
        "design_item": name,
        "status": status,
        "risk_level": risk,
        "design_detail": detail,
        "safety_boundary": boundary,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def ticket_row(field: str, status: str, value: str, why_blank: str, future_requirement: str, safety_note: str) -> dict[str, Any]:
    return {
        "ticket_field": field,
        "field_status": status,
        "draft_value": value,
        "why_blank_or_blocked": why_blank,
        "future_requirement": future_requirement,
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
