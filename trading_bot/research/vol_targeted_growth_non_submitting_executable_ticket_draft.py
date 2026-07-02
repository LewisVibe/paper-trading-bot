"""Non-submitting executable-ticket draft artifact for the volatility seed.

This module creates a saved review draft from the prior proposed ticket-value
labels. The draft is intentionally not executable: it does not populate side,
quantity, order type, time-in-force, account, broker order id, or submit-ready
instructions, and it never calls broker, market-data, alert, config, or
scheduling paths.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
DRAFT_STATUS = "vol_targeted_growth_non_submitting_executable_ticket_draft_created_manual_review_required"
DRAFT_DECISION = "NON_SUBMITTING_EXECUTABLE_TICKET_DRAFT_CREATED_NOT_EXECUTABLE"
QUALITY_STATUS = "vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_passed_manual_review_required"
QUALITY_DECISION = "NON_SUBMITTING_EXECUTABLE_TICKET_DRAFT_QUALITY_GATE_PASSED_NO_EXECUTION"
NEXT_STEP = "manual_review_non_submitting_ticket_draft_before_any_ticket_value_approval"

DRAFT_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_summary.csv"),
    "ticket": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_ticket.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_evidence.csv"),
}

QUALITY_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_evidence.csv"),
}

INPUT_FILES = {
    "draft_readiness": Path("data/vol_targeted_growth_executable_ticket_draft_readiness_summary.csv"),
    "proposed_ticket_values": Path("data/vol_targeted_growth_proposed_ticket_values_summary.csv"),
    "proposed_ticket_values_values": Path("data/vol_targeted_growth_proposed_ticket_values_values.csv"),
    "proposed_ticket_values_quality_gate": Path("data/vol_targeted_growth_proposed_ticket_values_quality_gate_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "non_submitting": True,
    "draft_ticket_created": True,
    "ticket_values_approved": False,
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
TICKET_COLUMNS = [
    "draft_field",
    "field_status",
    "draft_value",
    "source_field",
    "why_not_executable",
    "manual_review_requirement",
    "safety_boundary",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class NonSubmittingExecutableTicketDraftResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    ticket_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class NonSubmittingExecutableTicketDraftQualityResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_non_submitting_executable_ticket_draft(
    root_dir: Path | str = ".",
) -> NonSubmittingExecutableTicketDraftResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    ticket_rows = build_ticket_rows(inputs, context)
    report_rows = build_report_rows(context, ticket_rows)
    summary_rows = build_summary_rows(context, ticket_rows)
    blocker_rows = build_blocker_rows(context)
    evidence_rows = build_evidence_rows(inputs)
    paths = write_draft_outputs(root, report_rows, summary_rows, ticket_rows, blocker_rows, evidence_rows)
    return NonSubmittingExecutableTicketDraftResult(
        paths,
        report_rows,
        summary_rows,
        ticket_rows,
        blocker_rows,
        evidence_rows,
        draft_lines(summary_rows, paths["report"]),
    )


def show_vol_targeted_growth_non_submitting_executable_ticket_draft(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / DRAFT_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted non-submitting executable-ticket draft is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-draft` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted non-submitting executable-ticket draft saved display. Draft only; not executable.",
        f"final_ticket_draft_status: {summary_value(rows, 'final_ticket_draft_status')}",
        f"final_ticket_draft_decision: {summary_value(rows, 'final_ticket_draft_decision')}",
        f"draft_ticket_created: {summary_value(rows, 'draft_ticket_created')}",
        f"ticket_field_count: {summary_value(rows, 'ticket_field_count')}",
        f"executable_order_field_count: {summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count: {summary_value(rows, 'forbidden_field_count')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"executable_ticket_created: {summary_value(rows, 'executable_ticket_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate(
    root_dir: Path | str = ".",
) -> NonSubmittingExecutableTicketDraftQualityResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    ticket_rows = read_csv_rows(root / DRAFT_OUTPUTS["ticket"])
    checks = evaluate_ticket_rows(ticket_rows)
    report_rows = build_quality_report_rows(checks)
    summary_rows = build_quality_summary_rows(checks, ticket_rows)
    blocker_rows = [
        blocker_row("draft_ticket_not_executable", "blocked", "critical", "Quality gate passed for a non-submitting draft only.", NEXT_STEP),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]
    evidence_rows = build_evidence_rows(inputs)
    evidence_rows.append(evidence_row("draft_ticket_input", f"{DRAFT_OUTPUTS['ticket']}; rows={len(ticket_rows)}", "Saved draft ticket input row count."))
    paths = write_quality_outputs(root, report_rows, summary_rows, blocker_rows, evidence_rows)
    return NonSubmittingExecutableTicketDraftQualityResult(
        paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        quality_lines(summary_rows, paths["report"]),
    )


def show_vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / QUALITY_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted non-submitting executable-ticket draft quality gate is missing.",
            "Run `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-draft-quality-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted non-submitting executable-ticket draft quality gate saved display. No execution approved.",
        f"final_ticket_draft_quality_status: {summary_value(rows, 'final_ticket_draft_quality_status')}",
        f"final_ticket_draft_quality_decision: {summary_value(rows, 'final_ticket_draft_quality_decision')}",
        f"quality_gate_passed: {summary_value(rows, 'quality_gate_passed')}",
        f"ticket_field_count: {summary_value(rows, 'ticket_field_count')}",
        f"executable_order_field_count: {summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count: {summary_value(rows, 'forbidden_field_count')}",
        f"order_instruction_field_count: {summary_value(rows, 'order_instruction_field_count')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"executable_ticket_created: {summary_value(rows, 'executable_ticket_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    readiness_decision = summary_value(inputs["draft_readiness"], "final_executable_ticket_draft_readiness_decision")
    discussion_ready = summary_value(inputs["draft_readiness"], "draft_discussion_ready")
    quality_decision = summary_value(inputs["proposed_ticket_values_quality_gate"], "final_proposed_ticket_values_quality_gate_decision")
    go_no_go_decision = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision")
    ready = discussion_ready == "True" and quality_decision == "PROPOSED_TICKET_VALUES_QUALITY_GATE_PASSED_NO_EXECUTION"
    return {
        "draft_readiness_decision": readiness_decision or "missing_draft_readiness",
        "draft_discussion_ready": discussion_ready or "False",
        "proposed_ticket_values_quality_gate_decision": quality_decision or "missing_proposed_ticket_values_quality_gate",
        "go_no_go_decision": go_no_go_decision or "missing_go_no_go_dashboard",
        "draft_allowed": str(ready),
    }


def build_ticket_rows(inputs: dict[str, list[dict[str, str]]], context: dict[str, str]) -> list[dict[str, Any]]:
    proposed = {row.get("proposal_field", ""): row for row in inputs["proposed_ticket_values_values"]}
    rows = [
        ticket_row("draft_ticket_id", "review_context", "vol_targeted_growth_non_submitting_draft_v1", "local_draft_id", "Local review id only.", "Manual review can trace this draft.", "Not a broker/order id."),
        ticket_row("strategy_name", "review_context", ACTIVE_SEED, "proposal_strategy", "Strategy context only.", "Must match active seed.", "Not an order field."),
        ticket_row("ticker_scope", "review_context", ACTIVE_TICKER, "proposal_ticker_scope", "Portfolio label only.", "Component mapping review required before any future execution.", "Not a broker symbol."),
        ticket_row("draft_action_label", "review_only", proposed_value(proposed, "proposal_action"), "proposal_action", "Action label is not an order side.", "Manual sleeve rebalance review required.", "Not a buy/sell instruction."),
        ticket_row("draft_side_label", "review_only", proposed_value(proposed, "proposal_side"), "proposal_side", "Side label is not executable.", "Separate component-level mapping would be required.", "Not a buy/sell instruction."),
        ticket_row("draft_quantity_label", "review_only", proposed_value(proposed, "proposal_quantity"), "proposal_quantity", "Quantity label is not numeric.", "Sizing and broker-state review required.", "No quantity instruction."),
        ticket_row("draft_order_type_label", "review_only", proposed_value(proposed, "proposal_order_type"), "proposal_order_type", "Order type label is not executable.", "Separate explicit approval required.", "No order-type instruction."),
        ticket_row("draft_time_in_force_label", "review_only", proposed_value(proposed, "proposal_time_in_force"), "proposal_time_in_force", "Time-in-force label is not executable.", "Separate explicit approval required.", "No routing instruction."),
        ticket_row("draft_price_handling_label", "review_only", proposed_value(proposed, "proposal_price_handling"), "proposal_price_handling", "Price label is not executable.", "Limit/stop review required if ever needed.", "No price instruction."),
        ticket_row("saved_qqq_position_context", "context_only", proposed_value(proposed, "saved_qqq_position_context"), "saved_qqq_position_context", "Saved QQQ context only.", "Avoid repeat/follow-up QQQ orders.", "Not an order instruction."),
        ticket_row("draft_readiness_context", "context_only", context["draft_readiness_decision"], "draft_readiness", "Readiness is not approval.", "Manual review required before any next artifact.", "Not execution approval."),
        ticket_row("submit_ready", "blocked_false", "False", "submit_ready", "Draft cannot be submitted.", "Separate future execution approval would be required.", "Not executable."),
    ]
    return rows


def proposed_value(rows: dict[str, dict[str, str]], field: str) -> str:
    return rows.get(field, {}).get("proposal_value", "missing_saved_proposed_value")


def build_report_rows(context: dict[str, str], ticket_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        report_row("draft_readiness", "pass" if context["draft_allowed"] == "True" else "manual_review_required", "critical", context["draft_readiness_decision"], "Readiness can support this non-submitting draft only.", NEXT_STEP),
        report_row("draft_ticket_created", "review_only", "critical", f"ticket_field_count={len(ticket_rows)}", "A saved review draft exists, but it cannot be submitted.", "run_draft_quality_gate"),
        report_row("go_no_go_boundary", "execution_blocked", "critical", context["go_no_go_decision"], "Dashboard remains no-go for execution.", "keep_execution_blocked"),
    ]


def build_summary_rows(context: dict[str, str], ticket_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = evaluate_ticket_rows(ticket_rows)
    data = [
        ("final_ticket_draft_status", DRAFT_STATUS, "Non-submitting draft checkpoint status."),
        ("final_ticket_draft_decision", DRAFT_DECISION, "Draft exists for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("draft_readiness_decision", context["draft_readiness_decision"], "Saved readiness decision."),
        ("draft_discussion_ready", context["draft_discussion_ready"], "True means prior readiness allowed discussion."),
        ("proposed_ticket_values_quality_gate_decision", context["proposed_ticket_values_quality_gate_decision"], "Saved proposed-values quality gate."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved dashboard decision."),
        ("draft_ticket_created", "True", "A non-submitting review draft was created."),
        ("ticket_field_count", str(len(ticket_rows)), "Number of draft fields."),
        ("executable_order_field_count", str(checks["executable_order_field_count"]), "Executable order fields present."),
        ("forbidden_field_count", str(checks["forbidden_field_count"]), "Forbidden secret/account/broker fields present."),
        ("order_instruction_field_count", str(checks["order_instruction_field_count"]), "Submit-ready/order instruction fields present."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "draft_ticket_not_executable", "Draft is for manual review only."),
        ("recommended_next_step", "run_non_submitting_ticket_draft_quality_gate_before_any_value_approval", "Quality gate should verify draft remains non-executable."),
    ]
    return [summary_row(*item) for item in data]


def evaluate_ticket_rows(rows: list[dict[str, Any]]) -> dict[str, int | bool]:
    forbidden_fields = {"account_id", "account_reference", "api_key", "secret", "token", "webhook", "broker_order_id", "client_order_id"}
    executable_fields = {"order_side", "order_quantity", "order_type", "time_in_force", "limit_price", "stop_price", "symbol", "side", "qty", "quantity"}
    order_instruction_fields = {"submit_order", "cancel_order", "replace_order", "submit_ready_true", "order_instruction"}
    executable_values = {"buy", "sell", "market", "limit", "day", "gtc"}
    field_names = {str(row.get("draft_field", "")).strip().lower() for row in rows}
    values = {str(row.get("draft_value", "")).strip().lower() for row in rows}
    executable_order_field_count = len(field_names & executable_fields) + len(values & executable_values)
    forbidden_field_count = len(field_names & forbidden_fields)
    order_instruction_field_count = len(field_names & order_instruction_fields)
    missing_rows = 0 if rows else 1
    passed = missing_rows == 0 and executable_order_field_count == 0 and forbidden_field_count == 0 and order_instruction_field_count == 0
    return {
        "passed": passed,
        "ticket_field_count": len(rows),
        "missing_rows": missing_rows,
        "executable_order_field_count": executable_order_field_count,
        "forbidden_field_count": forbidden_field_count,
        "order_instruction_field_count": order_instruction_field_count,
    }


def build_blocker_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("draft_ticket_not_executable", "blocked", "critical", "Draft is not an executable ticket and has no order values.", NEXT_STEP),
        blocker_row("ticket_values_not_approved", "blocked", "critical", "Ticket values remain unapproved.", "keep_order_values_unapproved"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]
    if context["draft_allowed"] != "True":
        rows.insert(0, blocker_row("draft_readiness_missing_or_blocked", "blocked", "critical", context["draft_readiness_decision"], "refresh_draft_readiness_report"))
    return rows


def build_quality_report_rows(checks: dict[str, int | bool]) -> list[dict[str, Any]]:
    return [
        report_row("draft_rows_present", "pass" if checks["missing_rows"] == 0 else "error", "critical", f"ticket_field_count={checks['ticket_field_count']}", "Quality gate requires saved draft rows.", "refresh_draft_ticket"),
        report_row("no_executable_order_fields", "pass" if checks["executable_order_field_count"] == 0 else "error", "critical", f"executable_order_field_count={checks['executable_order_field_count']}", "Draft must not contain exact executable order fields or values.", "remove_executable_order_fields"),
        report_row("no_forbidden_fields", "pass" if checks["forbidden_field_count"] == 0 else "error", "critical", f"forbidden_field_count={checks['forbidden_field_count']}", "Draft must not contain account, secret, API, webhook, or broker id fields.", "remove_forbidden_fields"),
        report_row("no_order_instruction_fields", "pass" if checks["order_instruction_field_count"] == 0 else "error", "critical", f"order_instruction_field_count={checks['order_instruction_field_count']}", "Draft must not contain order instruction fields.", "remove_order_instruction_fields"),
    ]


def build_quality_summary_rows(checks: dict[str, int | bool], ticket_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    passed = bool(checks["passed"])
    data = [
        ("final_ticket_draft_quality_status", QUALITY_STATUS if passed else "vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_blocked_manual_review_required", "Draft quality gate status."),
        ("final_ticket_draft_quality_decision", QUALITY_DECISION if passed else "NON_SUBMITTING_EXECUTABLE_TICKET_DRAFT_QUALITY_GATE_BLOCKED", "Draft quality decision."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("quality_gate_passed", str(passed), "True only when draft remains non-executable."),
        ("draft_ticket_created", "True" if ticket_rows else "False", "Saved draft ticket rows exist."),
        ("ticket_field_count", str(checks["ticket_field_count"]), "Saved draft rows reviewed."),
        ("executable_order_field_count", str(checks["executable_order_field_count"]), "Executable order fields or values found."),
        ("forbidden_field_count", str(checks["forbidden_field_count"]), "Forbidden fields found."),
        ("order_instruction_field_count", str(checks["order_instruction_field_count"]), "Order instruction fields found."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "draft_ticket_not_executable", "Quality gate does not approve execution."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any ticket value approval."),
    ]
    return [summary_row(*item) for item in data]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def ticket_row(name: str, status: str, value: str, source: str, why_not_executable: str, review_requirement: str, boundary: str) -> dict[str, Any]:
    return {"draft_field": name, "field_status": status, "draft_value": value, "source_field": source, "why_not_executable": why_not_executable, "manual_review_requirement": review_requirement, "safety_boundary": boundary, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def write_draft_outputs(root: Path, report_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], ticket_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in DRAFT_OUTPUTS.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["ticket"], TICKET_COLUMNS, ticket_rows)
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


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def draft_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Volatility-targeted non-submitting executable-ticket draft complete. Draft only; not executable.",
        f"final_ticket_draft_status={summary_value(rows, 'final_ticket_draft_status')}",
        f"final_ticket_draft_decision={summary_value(rows, 'final_ticket_draft_decision')}",
        f"draft_ticket_created={summary_value(rows, 'draft_ticket_created')}",
        f"ticket_field_count={summary_value(rows, 'ticket_field_count')}",
        f"executable_order_field_count={summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count={summary_value(rows, 'forbidden_field_count')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def quality_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Volatility-targeted non-submitting executable-ticket draft quality gate complete. No execution approved.",
        f"final_ticket_draft_quality_status={summary_value(rows, 'final_ticket_draft_quality_status')}",
        f"final_ticket_draft_quality_decision={summary_value(rows, 'final_ticket_draft_quality_decision')}",
        f"quality_gate_passed={summary_value(rows, 'quality_gate_passed')}",
        f"ticket_field_count={summary_value(rows, 'ticket_field_count')}",
        f"executable_order_field_count={summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count={summary_value(rows, 'forbidden_field_count')}",
        f"order_instruction_field_count={summary_value(rows, 'order_instruction_field_count')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
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
