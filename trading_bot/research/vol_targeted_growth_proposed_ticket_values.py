"""Review-only proposed ticket values for the volatility seed.

This report drafts proposed ticket-value concepts after proposal approval.
It intentionally does not create executable order fields or submit-ready
instructions. Values are proposal labels for manual review only.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PROPOSED_STATUS = "vol_targeted_growth_proposed_ticket_values_created_review_only_manual_review_required"
PROPOSED_DECISION = "PROPOSED_TICKET_VALUES_CREATED_REVIEW_ONLY_NOT_EXECUTABLE"
QUALITY_STATUS = "vol_targeted_growth_proposed_ticket_values_quality_gate_passed_review_only_manual_review_required"
QUALITY_DECISION = "PROPOSED_TICKET_VALUES_QUALITY_GATE_PASSED_NO_EXECUTION"
NEXT_STEP = "manual_review_proposed_ticket_values_before_any_executable_ticket"

PROPOSED_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_proposed_ticket_values.csv"),
    "summary": Path("data/vol_targeted_growth_proposed_ticket_values_summary.csv"),
    "values": Path("data/vol_targeted_growth_proposed_ticket_values_values.csv"),
    "blockers": Path("data/vol_targeted_growth_proposed_ticket_values_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_proposed_ticket_values_evidence.csv"),
}

QUALITY_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_proposed_ticket_values_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_proposed_ticket_values_quality_gate_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_proposed_ticket_values_quality_gate_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_proposed_ticket_values_quality_gate_evidence.csv"),
}

INPUT_FILES = {
    "proposal_approval_record": Path("data/vol_targeted_growth_ticket_value_proposal_approval_record_summary.csv"),
    "placeholder_quality_gate": Path("data/vol_targeted_growth_ticket_value_quality_gate_summary.csv"),
    "fresh_broker_pre_ticket_gate_run": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "review_only": True,
    "proposed_ticket_values_created": True,
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
VALUE_COLUMNS = [
    "proposal_field",
    "proposal_status",
    "proposal_value",
    "why_not_executable",
    "manual_review_requirement",
    "safety_boundary",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class ProposedTicketValuesResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    value_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class ProposedTicketValuesQualityResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_proposed_ticket_values(root_dir: Path | str = ".") -> ProposedTicketValuesResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    value_rows = build_value_rows(context)
    report_rows = build_report_rows(context, value_rows)
    summary_rows = build_summary_rows(context, value_rows)
    blocker_rows = common_blockers("proposed_values_not_executable", "Proposed values are labels for manual review only.", NEXT_STEP)
    evidence_rows = evidence_rows_for(inputs)
    paths = write_proposed_outputs(root, report_rows, summary_rows, value_rows, blocker_rows, evidence_rows)
    return ProposedTicketValuesResult(paths, report_rows, summary_rows, value_rows, blocker_rows, evidence_rows, proposed_lines(summary_rows, paths["report"]))


def show_vol_targeted_growth_proposed_ticket_values(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / PROPOSED_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted proposed ticket values are missing.",
            "Run `python bot.py --vol-targeted-growth-proposed-ticket-values` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted proposed ticket values saved display. Review only; not executable.",
        f"final_proposed_ticket_values_status: {summary_value(rows, 'final_proposed_ticket_values_status')}",
        f"final_proposed_ticket_values_decision: {summary_value(rows, 'final_proposed_ticket_values_decision')}",
        f"proposal_field_count: {summary_value(rows, 'proposal_field_count')}",
        f"executable_order_field_count: {summary_value(rows, 'executable_order_field_count')}",
        f"proposed_ticket_values_created: {summary_value(rows, 'proposed_ticket_values_created')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_proposed_ticket_values_quality_gate(root_dir: Path | str = ".") -> ProposedTicketValuesQualityResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    value_rows = read_csv_rows(root / PROPOSED_OUTPUTS["values"])
    checks = evaluate_quality(value_rows)
    report_rows = build_quality_report_rows(context, checks)
    summary_rows = build_quality_summary_rows(context, checks, value_rows)
    blocker_rows = common_blockers("proposed_values_still_not_executable", "Quality gate passed for review-only proposed values, not execution.", "manual_review_quality_gate_before_any_executable_ticket")
    evidence_rows = evidence_rows_for(inputs)
    evidence_rows.append(evidence_row("proposed_values_input", f"{PROPOSED_OUTPUTS['values']}; rows={len(value_rows)}", "Saved proposed values input row count."))
    paths = write_quality_outputs(root, report_rows, summary_rows, blocker_rows, evidence_rows)
    return ProposedTicketValuesQualityResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, quality_lines(summary_rows, paths["report"]))


def show_vol_targeted_growth_proposed_ticket_values_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / QUALITY_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted proposed ticket values quality gate is missing.",
            "Run `python bot.py --vol-targeted-growth-proposed-ticket-values-quality-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted proposed ticket values quality gate saved display. Review only; no execution approved.",
        f"final_proposed_ticket_values_quality_gate_status: {summary_value(rows, 'final_proposed_ticket_values_quality_gate_status')}",
        f"final_proposed_ticket_values_quality_gate_decision: {summary_value(rows, 'final_proposed_ticket_values_quality_gate_decision')}",
        f"quality_gate_passed: {summary_value(rows, 'quality_gate_passed')}",
        f"proposal_field_count: {summary_value(rows, 'proposal_field_count')}",
        f"executable_order_field_count: {summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count: {summary_value(rows, 'forbidden_field_count')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "proposal_record_decision": summary_value(inputs["proposal_approval_record"], "final_ticket_value_proposal_record_decision") or "missing_proposal_approval_record",
        "proposal_discussion_approved": summary_value(inputs["proposal_approval_record"], "ticket_value_proposal_discussion_approved") or "False",
        "placeholder_quality_decision": summary_value(inputs["placeholder_quality_gate"], "final_ticket_value_quality_gate_decision") or "missing_placeholder_quality_gate",
        "saved_qqq_quantity": summary_value(inputs["fresh_broker_pre_ticket_gate_run"], "qqq_position_quantity_if_readonly") or "unavailable",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_value_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("proposal_strategy", "context_only", ACTIVE_SEED, "Strategy context only.", "Must match active seed.", "Not a broker field."),
        ("proposal_ticker_scope", "context_only", ACTIVE_TICKER, "Portfolio label only.", "Manual review must map sleeves separately before any ticket.", "Not a broker symbol."),
        ("proposal_action", "review_only", "review_rebalance_to_saved_target_sleeves_only", "Action is a review label, not an order side.", "Manual review of sleeve targets and current paper positions.", "Not a buy/sell instruction."),
        ("proposal_side", "review_only", "multi_sleeve_mapping_required_not_single_side", "The active seed is not a single-symbol side.", "Separate component mapping would be required.", "Not a buy/sell instruction."),
        ("proposal_quantity", "review_only", "component_quantities_not_set", "No numeric quantity is provided.", "Requires separate sizing, buying-power, and broker-state review.", "No quantity instruction."),
        ("proposal_order_type", "review_only", "market_candidate_review_only", "Order type is a review candidate, not an instruction.", "Requires separate executable-ticket approval.", "No order-type instruction."),
        ("proposal_time_in_force", "review_only", "day_candidate_review_only", "Time-in-force is a review candidate, not an instruction.", "Requires separate executable-ticket approval.", "No routing instruction."),
        ("proposal_price_handling", "review_only", "no_limit_or_stop_price_proposed", "No price is populated.", "Manual review required if limit/stop logic is ever needed.", "No price instruction."),
        ("saved_qqq_position_context", "context_only", context["saved_qqq_quantity"], "Saved QQQ quantity is context only.", "Manual review must avoid repeat/follow-up QQQ orders.", "Not an order instruction."),
        ("submit_ready", "blocked_false", "False", "The proposal cannot be submitted.", "Requires a later executable-ticket approval chain.", "Not executable."),
    ]
    return [value_row(*item) for item in rows]


def build_report_rows(context: dict[str, str], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        report_row("proposal_approval_record", "present" if context["proposal_discussion_approved"] == "True" else "manual_review_required", "critical", context["proposal_record_decision"], "Proposal approval permits this review-only draft, not execution.", NEXT_STEP),
        report_row("review_only_values", "non_executable", "critical", f"proposal_field_count={len(rows)}", "Proposal values are labels and are not broker-ready fields.", "run_proposed_ticket_values_quality_gate"),
        report_row("go_no_go_boundary", "execution_blocked", "critical", context["go_no_go_decision"], "Dashboard remains no-go for execution.", "keep_execution_blocked"),
    ]


def build_summary_rows(context: dict[str, str], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_proposed_ticket_values_status", PROPOSED_STATUS, "Proposed values checkpoint status."),
        ("final_proposed_ticket_values_decision", PROPOSED_DECISION, "Review-only proposed values; no executable ticket."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("proposal_record_decision", context["proposal_record_decision"], "Saved proposal approval record."),
        ("proposal_discussion_approved", context["proposal_discussion_approved"], "True means review-only proposed values may be drafted."),
        ("placeholder_quality_decision", context["placeholder_quality_decision"], "Saved placeholder quality gate context."),
        ("proposal_field_count", str(len(rows)), "Number of proposal rows."),
        ("executable_order_field_count", "0", "No executable order fields are created."),
        ("forbidden_field_count", "0", "No account, secret, API, webhook, or broker id fields are created."),
        ("proposed_ticket_values_created", "True", "Review-only proposed values exist."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("order_values_populated", "False", "No executable order fields are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("largest_blocker", "proposed_values_not_executable", "Proposal values are not executable."),
        ("recommended_next_step", "run_proposed_ticket_values_quality_gate_before_any_executable_ticket", "Quality gate should verify proposal remains non-executable."),
    ]
    return [summary_row(*item) for item in data]


def evaluate_quality(rows: list[dict[str, str]]) -> dict[str, Any]:
    forbidden_names = {"order_side", "order_quantity", "order_type", "time_in_force", "account_id", "api_key", "secret", "token", "webhook", "broker_order_id"}
    executable_values = {"buy", "sell", "market", "limit", "day", "gtc"}
    forbidden_field_count = sum(1 for row in rows if str(row.get("proposal_field", "")).lower() in forbidden_names)
    executable_value_count = sum(1 for row in rows if str(row.get("proposal_value", "")).strip().lower() in executable_values)
    missing_rows = 0 if rows else 1
    passed = missing_rows == 0 and forbidden_field_count == 0 and executable_value_count == 0
    return {
        "passed": passed,
        "proposal_field_count": len(rows),
        "forbidden_field_count": forbidden_field_count,
        "executable_order_field_count": executable_value_count,
        "missing_rows": missing_rows,
    }


def build_quality_report_rows(context: dict[str, str], checks: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        report_row("proposal_values_present", "pass" if checks["missing_rows"] == 0 else "error", "critical", f"proposal_field_count={checks['proposal_field_count']}", "Quality gate requires saved proposal rows.", "refresh_proposed_ticket_values"),
        report_row("no_executable_order_fields", "pass" if checks["executable_order_field_count"] == 0 else "error", "critical", f"executable_order_field_count={checks['executable_order_field_count']}", "Proposal values must not be exact broker-ready values.", "remove_executable_values"),
        report_row("forbidden_fields_absent", "pass" if checks["forbidden_field_count"] == 0 else "error", "critical", f"forbidden_field_count={checks['forbidden_field_count']}", "No account, secret, API, webhook, or broker id fields may be present.", "remove_forbidden_fields"),
        report_row("execution_boundary", "pass", "critical", context["go_no_go_decision"], "Go/no-go remains no-go for execution.", "keep_execution_blocked"),
    ]


def build_quality_summary_rows(context: dict[str, str], checks: dict[str, Any], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    data = [
        ("final_proposed_ticket_values_quality_gate_status", QUALITY_STATUS if checks["passed"] else "vol_targeted_growth_proposed_ticket_values_quality_gate_manual_review_required", "Quality gate status."),
        ("final_proposed_ticket_values_quality_gate_decision", QUALITY_DECISION if checks["passed"] else "PROPOSED_TICKET_VALUES_QUALITY_GATE_BLOCKED", "Review-only proposal quality decision."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("quality_gate_passed", str(bool(checks["passed"])), "True only when proposed values remain non-executable."),
        ("proposal_record_decision", context["proposal_record_decision"], "Saved proposal approval record."),
        ("proposal_field_count", str(len(rows)), "Saved proposal rows reviewed."),
        ("executable_order_field_count", str(checks["executable_order_field_count"]), "Exact executable values found."),
        ("forbidden_field_count", str(checks["forbidden_field_count"]), "Forbidden fields found."),
        ("proposed_ticket_values_created", "True", "Review-only proposed values exist."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "proposed_values_not_executable", "Quality gate does not approve execution."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any future executable ticket."),
    ]
    return [summary_row(*item) for item in data]


def common_blockers(name: str, details: str, next_step: str) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def value_row(name: str, status: str, value: str, why_not_executable: str, review_requirement: str, boundary: str) -> dict[str, Any]:
    return {"proposal_field": name, "proposal_status": status, "proposal_value": value, "why_not_executable": why_not_executable, "manual_review_requirement": review_requirement, "safety_boundary": boundary, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def write_proposed_outputs(root: Path, report_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], value_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in PROPOSED_OUTPUTS.items()}
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


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def proposed_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Volatility-targeted proposed ticket values complete. Review only; not executable.",
        f"final_proposed_ticket_values_status={summary_value(rows, 'final_proposed_ticket_values_status')}",
        f"final_proposed_ticket_values_decision={summary_value(rows, 'final_proposed_ticket_values_decision')}",
        f"proposal_field_count={summary_value(rows, 'proposal_field_count')}",
        f"executable_order_field_count={summary_value(rows, 'executable_order_field_count')}",
        f"proposed_ticket_values_created={summary_value(rows, 'proposed_ticket_values_created')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def quality_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Volatility-targeted proposed ticket values quality gate complete. Review only; no execution approved.",
        f"final_proposed_ticket_values_quality_gate_status={summary_value(rows, 'final_proposed_ticket_values_quality_gate_status')}",
        f"final_proposed_ticket_values_quality_gate_decision={summary_value(rows, 'final_proposed_ticket_values_quality_gate_decision')}",
        f"quality_gate_passed={summary_value(rows, 'quality_gate_passed')}",
        f"proposal_field_count={summary_value(rows, 'proposal_field_count')}",
        f"executable_order_field_count={summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count={summary_value(rows, 'forbidden_field_count')}",
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
