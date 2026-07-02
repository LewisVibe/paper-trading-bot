"""Non-submitting executable-ticket design checkpoint for the volatility seed.

This checkpoint exists after execution-design-only approval. It designs the
shape of a future executable-ticket review artifact, while intentionally
keeping every order value blank and every execution approval false.
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
FINAL_STATUS = "vol_targeted_growth_non_submitting_executable_ticket_design_created_manual_review_required"
FINAL_DECISION = "NON_SUBMITTING_EXECUTABLE_TICKET_DESIGNED_NO_ORDER_VALUES"
NEXT_STEP = "manual_review_non_submitting_executable_ticket_design_before_any_ticket_values_or_order_approval"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design_summary.csv"),
    "ticket": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design_ticket.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design_evidence.csv"),
}

INPUT_FILES = {
    "execution_design_approval_record": Path("data/vol_targeted_growth_execution_design_approval_record_summary.csv"),
    "manual_ticket_value_design": Path("data/vol_targeted_growth_manual_ticket_value_design_summary.csv"),
    "post_gate_review": Path("data/vol_targeted_growth_post_gate_review_summary.csv"),
    "executable_ticket_gap_list": Path("data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "non_submitting": True,
    "execution_design_only": True,
    "executable_ticket_design_created": True,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "order_values_populated": False,
    "order_instructions_created": False,
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
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class NonSubmittingExecutableTicketDesignResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    ticket_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_non_submitting_executable_ticket_design(
    root_dir: Path | str = ".",
) -> NonSubmittingExecutableTicketDesignResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_report_rows(context)
    ticket_rows = build_ticket_rows(context)
    summary_rows = build_summary_rows(context, ticket_rows)
    blocker_rows = build_blocker_rows(context, inputs)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["ticket"], TICKET_COLUMNS, ticket_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return NonSubmittingExecutableTicketDesignResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        ticket_rows=ticket_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_non_submitting_executable_ticket_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted non-submitting executable-ticket design is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-design` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted non-submitting executable-ticket design saved display. Design only; no executable ticket.",
        f"final_executable_ticket_design_status: {summary_value(rows, 'final_executable_ticket_design_status')}",
        f"final_executable_ticket_design_decision: {summary_value(rows, 'final_executable_ticket_design_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"execution_design_approval_record_decision: {summary_value(rows, 'execution_design_approval_record_decision')}",
        f"manual_ticket_value_design_decision: {summary_value(rows, 'manual_ticket_value_design_decision')}",
        f"ticket_field_count: {summary_value(rows, 'ticket_field_count')}",
        f"order_value_field_count: {summary_value(rows, 'order_value_field_count')}",
        f"populated_order_value_count: {summary_value(rows, 'populated_order_value_count')}",
        f"executable_ticket_design_created: {summary_value(rows, 'executable_ticket_design_created')}",
        f"executable_ticket_created: {summary_value(rows, 'executable_ticket_created')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "non_submitting=true; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: design only; no Alpaca, broker read, order values, order creation, live trading, or scheduling approval.",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "execution_design_approval_record_decision": summary_value(inputs["execution_design_approval_record"], "final_execution_design_record_decision") or "missing_execution_design_approval_record",
        "execution_design_approved": summary_value(inputs["execution_design_approval_record"], "execution_design_approved") or "False",
        "manual_ticket_value_design_decision": summary_value(inputs["manual_ticket_value_design"], "final_ticket_value_design_decision") or "missing_manual_ticket_value_design",
        "post_gate_review_decision": summary_value(inputs["post_gate_review"], "final_post_gate_review_decision") or "missing_post_gate_review",
        "saved_qqq_position_quantity_if_readonly": summary_value(inputs["post_gate_review"], "saved_qqq_position_quantity_if_readonly") or "unavailable",
        "gap_list_decision": summary_value(inputs["executable_ticket_gap_list"], "final_ticket_design_decision") or "missing_executable_ticket_gap_list",
        "gap_list_largest_gap": summary_value(inputs["executable_ticket_gap_list"], "largest_gap") or "missing_gap_list_largest_gap",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row("execution_design_approval_context", "design_allowed_not_execution", "critical", context["execution_design_approval_record_decision"], "Design-only approval can support this non-submitting artifact, but not an order.", NEXT_STEP),
        report_row("ticket_value_context", "values_still_unapproved", "critical", context["manual_ticket_value_design_decision"], "Manual ticket-value design remains review-only and does not populate values.", "keep_order_values_blank"),
        report_row("fresh_broker_context", "saved_context_only", "high", context["post_gate_review_decision"], "Saved read-only broker context is evidence only; no broker read is performed here.", "manual_review_saved_broker_context"),
        report_row("gap_list_context", "execution_blocked", "critical", context["gap_list_decision"], "Gap list remains blocked because execution approval is not present.", "keep_ticket_non_submitting"),
        report_row("go_no_go_boundary", "no_go_execution_blocked", "critical", context["go_no_go_decision"], "The dashboard remains no-go for execution.", "keep_go_no_go_blocking_execution"),
    ]


def build_ticket_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("ticket_design_id", "design_context", "vol_targeted_growth_non_submitting_executable_ticket_design_v1", "Local design id only.", "Future executable-ticket review needs an opaque local id.", "Not a broker/order id."),
        ("strategy_name", "design_context", ACTIVE_SEED, "Fixed active seed context.", f"Must equal {ACTIVE_SEED}.", "Context only."),
        ("ticker_scope", "design_context", ACTIVE_TICKER, "Portfolio label only.", f"Must equal {ACTIVE_TICKER}.", "Not a broker order symbol."),
        ("previous_seed_context", "design_context", f"{PREVIOUS_SEED}/{PREVIOUS_TICKER}", "Prior QQQ100 context only.", "Future review must preserve no-repeat QQQ100 boundary.", "No QQQ repeat order approved."),
        ("saved_qqq_position_quantity_if_readonly", "design_context", context["saved_qqq_position_quantity_if_readonly"], "Saved broker-read context only.", "Future review must consider existing QQQ exposure.", "No broker read occurs here."),
        ("execution_design_approval_record", "design_context", context["execution_design_approval_record_decision"], "Design-only approval context.", "Must remain design-only until separate order approval.", "Not execution approval."),
        ("order_side", "blocked_blank", "", "Side is not approved.", "Requires separate explicit ticket-value approval.", "No buy/sell instruction."),
        ("order_quantity", "blocked_blank", "", "Quantity is not approved.", "Requires separate sizing and broker-state review.", "No quantity instruction."),
        ("order_type", "blocked_blank", "", "Order type is not approved.", "Requires separate order design.", "No order type instruction."),
        ("time_in_force", "blocked_blank", "", "Time-in-force is not approved.", "Requires separate order design.", "No routing instruction."),
        ("limit_price_or_stop_price", "blocked_blank", "", "Price fields are not approved.", "Requires separate order design if ever needed.", "No price instruction."),
        ("account_reference", "forbidden_blank", "", "Account identifiers are forbidden in saved outputs.", "Never store account references in this report.", "No account identifiers."),
        ("submit_ready", "blocked_false", "False", "The ticket cannot be submitted.", "Requires a separate future execution approval and order gateway path.", "Not executable."),
        ("paper_execution_approved", "blocked_false", "False", "Paper execution is not approved.", "Requires separate explicit approval.", "No paper order approval."),
    ]
    return [ticket_row(*item) for item in rows]


def build_summary_rows(context: dict[str, str], ticket_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order_value_fields = {"order_side", "order_quantity", "order_type", "time_in_force", "limit_price_or_stop_price"}
    populated_order_values = [
        row
        for row in ticket_rows
        if row["ticket_field"] in order_value_fields and str(row.get("draft_value", "")).strip()
    ]
    data = [
        ("final_executable_ticket_design_status", FINAL_STATUS, "Non-submitting executable-ticket design checkpoint status."),
        ("final_executable_ticket_design_decision", FINAL_DECISION, "No executable ticket or order values are created."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("execution_design_approval_record_decision", context["execution_design_approval_record_decision"], "Saved design-only approval context."),
        ("execution_design_approved", context["execution_design_approved"], "Design-only approval flag from saved record."),
        ("manual_ticket_value_design_decision", context["manual_ticket_value_design_decision"], "Saved manual ticket-value design context."),
        ("post_gate_review_decision", context["post_gate_review_decision"], "Saved post-gate review context."),
        ("saved_qqq_position_quantity_if_readonly", context["saved_qqq_position_quantity_if_readonly"], "Saved QQQ quantity from prior read-only gate."),
        ("gap_list_decision", context["gap_list_decision"], "Saved gap-list context."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go dashboard decision."),
        ("ticket_field_count", str(len(ticket_rows)), "Number of ticket fields documented."),
        ("order_value_field_count", str(len(order_value_fields)), "Fields that would become executable only after separate approval."),
        ("populated_order_value_count", str(len(populated_order_values)), "Order value fields with populated values."),
        ("executable_ticket_design_created", "True", "A non-submitting design artifact was created."),
        ("ticket_instance_created", "False", "No executable ticket instance is created."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, or price value is populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("largest_blocker", "order_values_not_approved", "Primary blocker after design-only approval."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any ticket values or order approval."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("order_values_not_approved", "blocked", "critical", "Side, quantity, order type, time-in-force, price, account, and broker order id remain blank.", NEXT_STEP),
        blocker_row("executable_ticket_not_created", "blocked", "critical", "This is a design artifact only and cannot be submitted.", "separate_executable_ticket_record_would_be_required"),
        blocker_row("execution_not_approved", "blocked", "critical", "Execution, paper execution, live trading, repeat order, and scheduling approvals remain false.", "keep_all_approval_flags_false"),
    ]
    if context["execution_design_approved"] != "True":
        rows.insert(0, blocker_row("execution_design_approval_missing", "blocked", "critical", context["execution_design_approval_record_decision"], "refresh_execution_design_approval_record"))
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Volatility-targeted non-submitting executable-ticket design complete. Design only; no executable ticket or execution approved.",
        f"final_executable_ticket_design_status={summary_value(summary_rows, 'final_executable_ticket_design_status')}",
        f"final_executable_ticket_design_decision={summary_value(summary_rows, 'final_executable_ticket_design_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"execution_design_approved={summary_value(summary_rows, 'execution_design_approved')}",
        f"ticket_field_count={summary_value(summary_rows, 'ticket_field_count')}",
        f"order_value_field_count={summary_value(summary_rows, 'order_value_field_count')}",
        f"populated_order_value_count={summary_value(summary_rows, 'populated_order_value_count')}",
        f"executable_ticket_design_created={summary_value(summary_rows, 'executable_ticket_design_created')}",
        f"executable_ticket_created={summary_value(summary_rows, 'executable_ticket_created')}",
        f"order_values_populated={summary_value(summary_rows, 'order_values_populated')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "non_submitting=true; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def ticket_row(field: str, status: str, value: str, why_blank: str, future_requirement: str, safety_note: str) -> dict[str, Any]:
    return {"ticket_field": field, "field_status": status, "draft_value": value, "why_blank_or_blocked": why_blank, "future_requirement": future_requirement, "safety_note": safety_note, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
