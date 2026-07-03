"""Review-only draft ticket values for the volatility seed.

This checkpoint uses the saved draft ticket-value approval record to populate
review-only labels for a future manual ticket discussion. The labels are not
broker-ready order values: there is no side, numeric quantity, order type,
time-in-force, account reference, broker id, or submit-ready instruction.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
DRAFT_STATUS = "vol_targeted_growth_review_only_draft_ticket_values_created_manual_review_required"
DRAFT_DECISION = "REVIEW_ONLY_DRAFT_TICKET_VALUES_POPULATED_NOT_EXECUTABLE"
QUALITY_STATUS = "vol_targeted_growth_review_only_draft_ticket_values_quality_gate_passed_manual_review_required"
QUALITY_DECISION = "REVIEW_ONLY_DRAFT_TICKET_VALUES_QUALITY_GATE_PASSED_NO_EXECUTION"
NEXT_STEP = "manual_review_draft_ticket_values_before_any_executable_ticket_values"

DRAFT_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_review_only_draft_ticket_values.csv"),
    "summary": Path("data/vol_targeted_growth_review_only_draft_ticket_values_summary.csv"),
    "values": Path("data/vol_targeted_growth_review_only_draft_ticket_values_values.csv"),
    "blockers": Path("data/vol_targeted_growth_review_only_draft_ticket_values_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_review_only_draft_ticket_values_evidence.csv"),
}

QUALITY_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_review_only_draft_ticket_values_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_review_only_draft_ticket_values_quality_gate_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_review_only_draft_ticket_values_quality_gate_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_review_only_draft_ticket_values_quality_gate_evidence.csv"),
}

INPUT_FILES = {
    "approval_record": Path("data/vol_targeted_growth_draft_ticket_value_approval_record_summary.csv"),
    "ticket_draft": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_summary.csv"),
    "ticket_draft_quality_gate": Path("data/vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "review_only": True,
    "draft_ticket_values_created": True,
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
    "draft_value_name",
    "draft_value_status",
    "draft_value",
    "source_context",
    "why_not_executable",
    "manual_review_requirement",
    "safety_boundary",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class ReviewOnlyDraftTicketValuesResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    value_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class ReviewOnlyDraftTicketValuesQualityResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_review_only_draft_ticket_values(root_dir: Path | str = ".") -> ReviewOnlyDraftTicketValuesResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    value_rows = build_value_rows(context)
    report_rows = build_report_rows(context, value_rows)
    summary_rows = build_summary_rows(context, value_rows)
    blocker_rows = common_blockers("draft_ticket_values_not_executable", "Review-only draft values are not executable order values.", NEXT_STEP)
    evidence_rows = evidence_rows_for(inputs)
    paths = write_draft_outputs(root, report_rows, summary_rows, value_rows, blocker_rows, evidence_rows)
    return ReviewOnlyDraftTicketValuesResult(paths, report_rows, summary_rows, value_rows, blocker_rows, evidence_rows, draft_lines(summary_rows, paths["report"]))


def show_vol_targeted_growth_review_only_draft_ticket_values(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / DRAFT_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted review-only draft ticket values are missing.",
            "Run `python bot.py --vol-targeted-growth-review-only-draft-ticket-values` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted review-only draft ticket values saved display. Not executable.",
        f"final_review_only_draft_ticket_values_status: {summary_value(rows, 'final_review_only_draft_ticket_values_status')}",
        f"final_review_only_draft_ticket_values_decision: {summary_value(rows, 'final_review_only_draft_ticket_values_decision')}",
        f"draft_ticket_values_created: {summary_value(rows, 'draft_ticket_values_created')}",
        f"review_value_count: {summary_value(rows, 'review_value_count')}",
        f"executable_order_field_count: {summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count: {summary_value(rows, 'forbidden_field_count')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_review_only_draft_ticket_values_quality_gate(root_dir: Path | str = ".") -> ReviewOnlyDraftTicketValuesQualityResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    value_rows = read_csv_rows(root / DRAFT_OUTPUTS["values"])
    checks = evaluate_quality(value_rows)
    report_rows = build_quality_report_rows(checks)
    summary_rows = build_quality_summary_rows(inputs, checks, value_rows)
    blocker_rows = common_blockers("draft_ticket_values_still_not_executable", "Quality gate passed for review-only values, not execution.", NEXT_STEP)
    evidence_rows = evidence_rows_for(inputs)
    evidence_rows.append(evidence_row("draft_values_input", f"{DRAFT_OUTPUTS['values']}; rows={len(value_rows)}", "Saved review-only draft values input row count."))
    paths = write_quality_outputs(root, report_rows, summary_rows, blocker_rows, evidence_rows)
    return ReviewOnlyDraftTicketValuesQualityResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, quality_lines(summary_rows, paths["report"]))


def show_vol_targeted_growth_review_only_draft_ticket_values_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / QUALITY_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted review-only draft ticket values quality gate is missing.",
            "Run `python bot.py --vol-targeted-growth-review-only-draft-ticket-values-quality-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted review-only draft ticket values quality gate saved display. No execution approved.",
        f"final_review_only_draft_ticket_values_quality_status: {summary_value(rows, 'final_review_only_draft_ticket_values_quality_status')}",
        f"final_review_only_draft_ticket_values_quality_decision: {summary_value(rows, 'final_review_only_draft_ticket_values_quality_decision')}",
        f"quality_gate_passed: {summary_value(rows, 'quality_gate_passed')}",
        f"review_value_count: {summary_value(rows, 'review_value_count')}",
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
        "approval_record_decision": summary_value(inputs["approval_record"], "final_draft_ticket_value_approval_record_decision") or "missing_approval_record",
        "ticket_value_population_approved": summary_value(inputs["approval_record"], "ticket_value_population_approved") or "False",
        "ticket_draft_decision": summary_value(inputs["ticket_draft"], "final_ticket_draft_decision") or "missing_ticket_draft",
        "ticket_draft_quality_gate_decision": summary_value(inputs["ticket_draft_quality_gate"], "final_ticket_draft_quality_decision") or "missing_ticket_draft_quality_gate",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_value_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("draft_strategy_name", "review_context", ACTIVE_SEED, "active_seed", "Strategy context only.", "Must match active report/status seed.", "Not a broker/order field."),
        ("draft_ticker_scope", "review_context", ACTIVE_TICKER, "active_ticker", "Portfolio label only.", "Component mapping review required before execution could ever be discussed.", "Not a broker symbol."),
        ("draft_sleeve_targets", "review_only", "qqq100_core=70%; high_growth_research=20%; crypto_research=5%; defensive_buffer=5%", "saved_volatility_seed_design", "Sleeve percentages are research context, not order quantities.", "Manual sleeve mapping and broker-state review required.", "No broker quantity or side."),
        ("draft_volatility_policy", "review_only", "target_vol=15%; window=20d; exposure_cap=1x; leverage=none", "saved_volatility_seed_design", "Risk-policy labels are not executable order values.", "Manual risk review required.", "No order instruction."),
        ("draft_action_label", "review_only", "review_alignment_to_saved_target_sleeves_only", "approval_record", "Action label is not an order side.", "Manual review required before any executable ticket values.", "Not a buy/sell instruction."),
        ("draft_side_label", "blocked_unpopulated", "component_side_not_populated", "approval_record", "No buy/sell side is populated.", "Future executable-ticket approval would be required.", "No side instruction."),
        ("draft_quantity_label", "blocked_unpopulated", "component_quantity_not_populated", "approval_record", "No numeric quantity is populated.", "Future sizing, buying-power, and broker-state review would be required.", "No quantity instruction."),
        ("draft_order_type_label", "blocked_unpopulated", "order_type_not_populated", "approval_record", "No executable order type is populated.", "Future executable-ticket approval would be required.", "No order-type instruction."),
        ("draft_time_in_force_label", "blocked_unpopulated", "time_in_force_not_populated", "approval_record", "No time-in-force is populated.", "Future executable-ticket approval would be required.", "No routing instruction."),
        ("draft_price_handling_label", "blocked_unpopulated", "price_handling_not_populated", "approval_record", "No price, limit, stop, or trigger is populated.", "Future executable-ticket approval would be required.", "No price instruction."),
        ("submit_ready", "blocked_false", "False", "submit_ready", "Draft values cannot be submitted.", "Separate future executable-ticket approval would be required.", "Not executable."),
    ]
    return [value_row(*item) for item in rows]


def build_report_rows(context: dict[str, str], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        report_row("approval_record", "present" if context["ticket_value_population_approved"] == "True" else "manual_review_required", "critical", context["approval_record_decision"], "Approval record permits review-only draft value labels, not executable values.", NEXT_STEP),
        report_row("draft_values", "review_only", "critical", f"review_value_count={len(rows)}", "Draft values are labels/context and cannot be submitted.", "run_review_only_draft_ticket_values_quality_gate"),
        report_row("go_no_go_boundary", "execution_blocked", "critical", context["go_no_go_decision"], "Dashboard remains no-go for execution.", "keep_execution_blocked"),
    ]


def build_summary_rows(context: dict[str, str], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_review_only_draft_ticket_values_status", DRAFT_STATUS, "Review-only draft ticket values checkpoint status."),
        ("final_review_only_draft_ticket_values_decision", DRAFT_DECISION, "Draft values are review labels, not executable order values."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_record_decision", context["approval_record_decision"], "Saved draft ticket-value approval record."),
        ("ticket_value_population_approved", context["ticket_value_population_approved"], "True means review-only draft value labels may be populated."),
        ("ticket_draft_decision", context["ticket_draft_decision"], "Saved non-submitting ticket draft context."),
        ("ticket_draft_quality_gate_decision", context["ticket_draft_quality_gate_decision"], "Saved non-submitting draft quality gate context."),
        ("review_value_count", str(len(rows)), "Number of review-only draft value rows."),
        ("executable_order_field_count", "0", "No executable order fields are created."),
        ("forbidden_field_count", "0", "No account, secret, API, webhook, or broker id fields are created."),
        ("draft_ticket_values_created", "True", "Review-only draft value labels exist."),
        ("ticket_values_approved", "False", "No concrete executable ticket values are approved."),
        ("order_values_populated", "False", "No broker-ready order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("largest_blocker", "draft_ticket_values_not_executable", "Draft values are not executable."),
        ("recommended_next_step", "run_review_only_draft_ticket_values_quality_gate", "Quality gate should verify draft values remain non-executable."),
    ]
    return [summary_row(*item) for item in data]


def evaluate_quality(rows: list[dict[str, str]]) -> dict[str, Any]:
    forbidden_names = {"order_side", "order_quantity", "order_type", "time_in_force", "account_id", "api_key", "secret", "token", "webhook", "broker_order_id"}
    executable_values = {"buy", "sell", "market", "limit", "day", "gtc"}
    forbidden_field_count = sum(1 for row in rows if str(row.get("draft_value_name", "")).strip().lower() in forbidden_names)
    executable_value_count = sum(1 for row in rows if str(row.get("draft_value", "")).strip().lower() in executable_values)
    missing_rows = 0 if rows else 1
    passed = missing_rows == 0 and forbidden_field_count == 0 and executable_value_count == 0
    return {
        "passed": passed,
        "review_value_count": len(rows),
        "forbidden_field_count": forbidden_field_count,
        "executable_order_field_count": executable_value_count,
        "missing_rows": missing_rows,
    }


def build_quality_report_rows(checks: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        report_row("draft_values_present", "pass" if checks["missing_rows"] == 0 else "error", "critical", f"review_value_count={checks['review_value_count']}", "Quality gate requires saved review-only rows.", "refresh_review_only_draft_ticket_values"),
        report_row("no_executable_order_values", "pass" if checks["executable_order_field_count"] == 0 else "error", "critical", f"executable_order_field_count={checks['executable_order_field_count']}", "Draft values must not be exact broker-ready values.", "remove_executable_values"),
        report_row("forbidden_fields_absent", "pass" if checks["forbidden_field_count"] == 0 else "error", "critical", f"forbidden_field_count={checks['forbidden_field_count']}", "No account, secret, API, webhook, or broker id fields may be present.", "remove_forbidden_fields"),
        report_row("execution_boundary", "pass", "critical", "execution_approved=false; paper_execution_approved=false", "Execution remains blocked.", "keep_execution_blocked"),
    ]


def build_quality_summary_rows(inputs: dict[str, list[dict[str, str]]], checks: dict[str, Any], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    data = [
        ("final_review_only_draft_ticket_values_quality_status", QUALITY_STATUS if checks["passed"] else "vol_targeted_growth_review_only_draft_ticket_values_quality_gate_failed_manual_review_required", "Quality gate checkpoint status."),
        ("final_review_only_draft_ticket_values_quality_decision", QUALITY_DECISION if checks["passed"] else "REVIEW_ONLY_DRAFT_TICKET_VALUES_QUALITY_GATE_FAILED", "Quality gate decision."),
        ("quality_gate_passed", str(checks["passed"]), "True only when values remain non-executable."),
        ("approval_record_decision", summary_value(inputs["approval_record"], "final_draft_ticket_value_approval_record_decision") or "missing_approval_record", "Saved approval record context."),
        ("review_value_count", str(checks["review_value_count"]), "Number of saved draft value rows."),
        ("executable_order_field_count", str(checks["executable_order_field_count"]), "Must remain 0."),
        ("forbidden_field_count", str(checks["forbidden_field_count"]), "Must remain 0."),
        ("draft_ticket_values_created", str(bool(rows)), "True when saved rows exist."),
        ("ticket_values_approved", "False", "No executable ticket values are approved."),
        ("order_values_populated", "False", "No broker-ready order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("largest_blocker", "draft_ticket_values_still_not_executable", "Quality gate is not execution approval."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any executable-ticket values."),
    ]
    return [summary_row(*item) for item in data]


def common_blockers(name: str, details: str, next_step: str) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step),
        blocker_row("ticket_values_not_approved", "blocked", "critical", "ticket_values_approved=false", "keep_values_unapproved_until_separate_executable_ticket_approval"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def value_row(name: str, status: str, value: str, source: str, why: str, review: str, boundary: str) -> dict[str, Any]:
    return {"draft_value_name": name, "draft_value_status": status, "draft_value": value, "source_context": source, "why_not_executable": why, "manual_review_requirement": review, "safety_boundary": boundary, **SAFETY_FLAGS}


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def write_draft_outputs(root: Path, report_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], value_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in DRAFT_OUTPUTS.items()}
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


def draft_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Review-only draft ticket values complete. Not executable and no orders approved.",
        f"final_review_only_draft_ticket_values_status={summary_value(rows, 'final_review_only_draft_ticket_values_status')}",
        f"final_review_only_draft_ticket_values_decision={summary_value(rows, 'final_review_only_draft_ticket_values_decision')}",
        f"draft_ticket_values_created={summary_value(rows, 'draft_ticket_values_created')}",
        f"review_value_count={summary_value(rows, 'review_value_count')}",
        f"executable_order_field_count={summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count={summary_value(rows, 'forbidden_field_count')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def quality_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Review-only draft ticket values quality gate complete. No execution approved.",
        f"final_review_only_draft_ticket_values_quality_status={summary_value(rows, 'final_review_only_draft_ticket_values_quality_status')}",
        f"final_review_only_draft_ticket_values_quality_decision={summary_value(rows, 'final_review_only_draft_ticket_values_quality_decision')}",
        f"quality_gate_passed={summary_value(rows, 'quality_gate_passed')}",
        f"review_value_count={summary_value(rows, 'review_value_count')}",
        f"executable_order_field_count={summary_value(rows, 'executable_order_field_count')}",
        f"forbidden_field_count={summary_value(rows, 'forbidden_field_count')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
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
