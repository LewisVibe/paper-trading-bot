"""Non-executable ticket-value placeholders for the volatility seed.

This checkpoint creates blank placeholders for future order values after the
discussion-only approval record. The placeholders are deliberately not
executable: side, quantity, order type, time-in-force, price, account, and
broker identifiers stay blank or false.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PLACEHOLDER_STATUS = "vol_targeted_growth_ticket_value_placeholders_created_non_executable_manual_review_required"
PLACEHOLDER_DECISION = "NON_EXECUTABLE_TICKET_VALUE_PLACEHOLDERS_CREATED_NO_VALUES"
QUALITY_STATUS = "vol_targeted_growth_ticket_value_quality_gate_passed_non_executable_manual_review_required"
QUALITY_DECISION = "TICKET_VALUE_PLACEHOLDERS_QUALITY_GATE_PASSED_NO_EXECUTION"
NEXT_STEP = "manual_review_ticket_value_placeholders_before_any_value_approval"

PLACEHOLDER_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_ticket_value_placeholders.csv"),
    "summary": Path("data/vol_targeted_growth_ticket_value_placeholders_summary.csv"),
    "placeholders": Path("data/vol_targeted_growth_ticket_value_placeholders_values.csv"),
    "blockers": Path("data/vol_targeted_growth_ticket_value_placeholders_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_ticket_value_placeholders_evidence.csv"),
}

QUALITY_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_ticket_value_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_ticket_value_quality_gate_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_ticket_value_quality_gate_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_ticket_value_quality_gate_evidence.csv"),
}

INPUT_FILES = {
    "ticket_values_approval_record": Path("data/vol_targeted_growth_ticket_values_approval_record_summary.csv"),
    "non_submitting_executable_ticket_design": Path("data/vol_targeted_growth_non_submitting_executable_ticket_design_summary.csv"),
    "manual_ticket_value_design": Path("data/vol_targeted_growth_manual_ticket_value_design_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "non_executable": True,
    "ticket_value_placeholder_only": True,
    "ticket_value_discussion_approved": False,
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
PLACEHOLDER_COLUMNS = [
    "placeholder_name",
    "placeholder_status",
    "placeholder_value",
    "approval_required_before_value",
    "safety_boundary",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class TicketValuePlaceholderResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    placeholder_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class TicketValueQualityGateResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_ticket_value_placeholders(root_dir: Path | str = ".") -> TicketValuePlaceholderResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    placeholder_rows = build_placeholder_rows(context)
    report_rows = build_placeholder_report_rows(context, placeholder_rows)
    summary_rows = build_placeholder_summary_rows(context, placeholder_rows)
    blocker_rows = build_common_blockers("ticket_values_not_approved", "Values are placeholders only and remain blank.", NEXT_STEP, True)
    evidence_rows = build_evidence_rows(inputs, True)
    paths = write_placeholder_outputs(root, report_rows, summary_rows, placeholder_rows, blocker_rows, evidence_rows)
    return TicketValuePlaceholderResult(paths, report_rows, summary_rows, placeholder_rows, blocker_rows, evidence_rows, build_placeholder_lines(summary_rows, paths["report"]))


def show_vol_targeted_growth_ticket_value_placeholders(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / PLACEHOLDER_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted ticket-value placeholders are missing.",
            "Run `python bot.py --vol-targeted-growth-ticket-value-placeholders` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted ticket-value placeholders saved display. Non-executable; no values approved.",
        f"final_ticket_value_placeholder_status: {summary_value(rows, 'final_ticket_value_placeholder_status')}",
        f"final_ticket_value_placeholder_decision: {summary_value(rows, 'final_ticket_value_placeholder_decision')}",
        f"ticket_value_discussion_approved: {summary_value(rows, 'ticket_value_discussion_approved')}",
        f"placeholder_count: {summary_value(rows, 'placeholder_count')}",
        f"blank_or_false_placeholder_count: {summary_value(rows, 'blank_or_false_placeholder_count')}",
        f"populated_order_value_count: {summary_value(rows, 'populated_order_value_count')}",
        f"ticket_values_approved: {summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_ticket_value_quality_gate(root_dir: Path | str = ".") -> TicketValueQualityGateResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    placeholder_rows = read_csv_rows(root / PLACEHOLDER_OUTPUTS["placeholders"])
    checks = evaluate_quality(context, placeholder_rows)
    report_rows = build_quality_report_rows(context, checks)
    summary_rows = build_quality_summary_rows(context, checks, placeholder_rows)
    blocker_rows = build_common_blockers("executable_ticket_not_created", "Quality gate passed for non-executable placeholders only.", "manual_review_quality_gate_before_any_value_approval", True)
    evidence_rows = build_evidence_rows(inputs, True)
    evidence_rows.append(evidence_row("placeholder_input", f"{PLACEHOLDER_OUTPUTS['placeholders']}; rows={len(placeholder_rows)}", "Saved placeholder input row count.", True))
    paths = write_quality_outputs(root, report_rows, summary_rows, blocker_rows, evidence_rows)
    return TicketValueQualityGateResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, build_quality_lines(summary_rows, paths["report"]))


def show_vol_targeted_growth_ticket_value_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / QUALITY_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted ticket-value quality gate is missing.",
            "Run `python bot.py --vol-targeted-growth-ticket-value-quality-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted ticket-value quality gate saved display. Non-executable; no execution approved.",
        f"final_ticket_value_quality_gate_status: {summary_value(rows, 'final_ticket_value_quality_gate_status')}",
        f"final_ticket_value_quality_gate_decision: {summary_value(rows, 'final_ticket_value_quality_gate_decision')}",
        f"quality_gate_passed: {summary_value(rows, 'quality_gate_passed')}",
        f"placeholder_count: {summary_value(rows, 'placeholder_count')}",
        f"populated_order_value_count: {summary_value(rows, 'populated_order_value_count')}",
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
    approval_rows = inputs["ticket_values_approval_record"]
    return {
        "ticket_values_record_decision": summary_value(approval_rows, "final_ticket_values_record_decision") or "missing_ticket_values_approval_record",
        "ticket_value_discussion_approved": summary_value(approval_rows, "ticket_value_discussion_approved") or "False",
        "ticket_values_approved": summary_value(approval_rows, "ticket_values_approved") or "False",
        "non_submitting_ticket_design_decision": summary_value(inputs["non_submitting_executable_ticket_design"], "final_executable_ticket_design_decision") or "missing_non_submitting_executable_ticket_design",
        "manual_ticket_value_design_decision": summary_value(inputs["manual_ticket_value_design"], "final_ticket_value_design_decision") or "missing_manual_ticket_value_design",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def flags(discussion_approved: bool = True) -> dict[str, bool]:
    updated = dict(SAFETY_FLAGS)
    updated["ticket_value_discussion_approved"] = discussion_approved
    return updated


def build_placeholder_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("strategy_name", "context_only", ACTIVE_SEED, "not_an_order_value", "Context only; not executable."),
        ("ticker_scope", "context_only", ACTIVE_TICKER, "not_a_broker_order_symbol", "Portfolio label only; not executable."),
        ("order_side", "placeholder_blank", "", "separate_explicit_value_approval_required", "No buy/sell instruction."),
        ("order_quantity", "placeholder_blank", "", "separate_explicit_value_approval_required", "No quantity instruction."),
        ("order_type", "placeholder_blank", "", "separate_explicit_value_approval_required", "No order-type instruction."),
        ("time_in_force", "placeholder_blank", "", "separate_explicit_value_approval_required", "No routing instruction."),
        ("limit_price", "placeholder_blank", "", "separate_explicit_value_approval_required", "No price instruction."),
        ("stop_price", "placeholder_blank", "", "separate_explicit_value_approval_required", "No price instruction."),
        ("account_reference", "forbidden_blank", "", "never_store_account_reference", "No account identifiers."),
        ("submit_ready", "placeholder_false", "False", "separate_execution_approval_required", "Not submit-ready."),
        ("paper_execution_approved", "placeholder_false", "False", "separate_execution_approval_required", "No paper execution approval."),
    ]
    return [placeholder_row(*item, discussion_approved=context["ticket_value_discussion_approved"] == "True") for item in rows]


def build_placeholder_report_rows(context: dict[str, str], placeholder_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    populated_count = populated_order_value_count(placeholder_rows)
    return [
        report_row("ticket_value_discussion_record", "present" if context["ticket_value_discussion_approved"] == "True" else "manual_review_required", "critical", context["ticket_values_record_decision"], "Discussion approval can support placeholders only.", NEXT_STEP),
        report_row("placeholder_boundary", "non_executable_placeholders_only", "critical", f"populated_order_value_count={populated_count}", "Placeholders must stay blank or false.", "run_ticket_value_quality_gate"),
        report_row("go_no_go_boundary", "execution_blocked", "critical", context["go_no_go_decision"], "Go/no-go dashboard remains blocked for execution.", "keep_execution_blocked"),
    ]


def build_placeholder_summary_rows(context: dict[str, str], placeholder_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blank_or_false_count = sum(1 for row in placeholder_rows if str(row.get("placeholder_value", "")).strip() in {"", "False"})
    populated_count = populated_order_value_count(placeholder_rows)
    data = [
        ("final_ticket_value_placeholder_status", PLACEHOLDER_STATUS, "Placeholder checkpoint status."),
        ("final_ticket_value_placeholder_decision", PLACEHOLDER_DECISION, "No executable values are populated."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("ticket_values_record_decision", context["ticket_values_record_decision"], "Saved discussion approval record."),
        ("ticket_value_discussion_approved", context["ticket_value_discussion_approved"], "Discussion only; not value approval."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("placeholder_count", str(len(placeholder_rows)), "Number of placeholder rows."),
        ("blank_or_false_placeholder_count", str(blank_or_false_count), "Rows with blank or False value."),
        ("populated_order_value_count", str(populated_count), "Executable order value fields populated."),
        ("order_values_populated", "False", "No order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("largest_blocker", "ticket_values_not_approved", "Values are placeholders only."),
        ("recommended_next_step", "run_ticket_value_quality_gate_before_any_value_approval", "Quality gate should verify placeholders remain non-executable."),
    ]
    return [summary_row(*item, discussion_approved=context["ticket_value_discussion_approved"] == "True") for item in data]


def evaluate_quality(context: dict[str, str], placeholder_rows: list[dict[str, str]]) -> dict[str, Any]:
    forbidden_names = {"account_id", "api_key", "secret", "token", "webhook", "broker_order_id"}
    forbidden_field_count = sum(1 for row in placeholder_rows if str(row.get("placeholder_name", "")).lower() in forbidden_names)
    populated_count = populated_order_value_count(placeholder_rows)
    missing_placeholders = 0 if placeholder_rows else 1
    passed = context["ticket_value_discussion_approved"] == "True" and populated_count == 0 and forbidden_field_count == 0 and missing_placeholders == 0
    return {
        "passed": passed,
        "populated_order_value_count": populated_count,
        "forbidden_field_count": forbidden_field_count,
        "placeholder_count": len(placeholder_rows),
        "missing_placeholders": missing_placeholders,
    }


def build_quality_report_rows(context: dict[str, str], checks: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        report_row("placeholder_file_present", "pass" if checks["missing_placeholders"] == 0 else "error", "critical", f"placeholder_count={checks['placeholder_count']}", "Quality gate requires saved placeholder rows.", "refresh_ticket_value_placeholders"),
        report_row("order_values_blank", "pass" if checks["populated_order_value_count"] == 0 else "error", "critical", f"populated_order_value_count={checks['populated_order_value_count']}", "Executable order values must remain blank.", "clear_order_values_and_review"),
        report_row("forbidden_fields_absent", "pass" if checks["forbidden_field_count"] == 0 else "error", "critical", f"forbidden_field_count={checks['forbidden_field_count']}", "No account, secret, API, webhook, or broker id fields may be present.", "remove_forbidden_fields"),
        report_row("approval_boundary", "pass" if context["ticket_value_discussion_approved"] == "True" else "warning", "critical", context["ticket_values_record_decision"], "Discussion approval is not value or execution approval.", "keep_execution_blocked"),
    ]


def build_quality_summary_rows(context: dict[str, str], checks: dict[str, Any], placeholder_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    data = [
        ("final_ticket_value_quality_gate_status", QUALITY_STATUS if checks["passed"] else "vol_targeted_growth_ticket_value_quality_gate_manual_review_required", "Quality gate status."),
        ("final_ticket_value_quality_gate_decision", QUALITY_DECISION if checks["passed"] else "TICKET_VALUE_PLACEHOLDERS_QUALITY_GATE_BLOCKED", "Non-executable placeholder quality decision."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("quality_gate_passed", str(bool(checks["passed"])), "True only when placeholders exist and no executable values are present."),
        ("ticket_value_discussion_approved", context["ticket_value_discussion_approved"], "Discussion only; not value approval."),
        ("ticket_values_approved", "False", "No ticket values are approved."),
        ("placeholder_count", str(len(placeholder_rows)), "Saved placeholder rows reviewed."),
        ("populated_order_value_count", str(checks["populated_order_value_count"]), "Executable order value fields populated."),
        ("forbidden_field_count", str(checks["forbidden_field_count"]), "Forbidden fields found."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "ticket_values_not_approved", "Quality gate does not approve values."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any future value approval."),
    ]
    return [summary_row(*item, discussion_approved=context["ticket_value_discussion_approved"] == "True") for item in data]


def populated_order_value_count(rows: list[dict[str, Any]]) -> int:
    order_fields = {"order_side", "order_quantity", "order_type", "time_in_force", "limit_price", "stop_price"}
    return sum(1 for row in rows if row.get("placeholder_name") in order_fields and str(row.get("placeholder_value", "")).strip())


def build_common_blockers(name: str, details: str, next_step: str, discussion_approved: bool) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step, discussion_approved),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", discussion_approved),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", discussion_approved),
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], discussion_approved: bool) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", discussion_approved) for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", discussion_approved))
    return rows


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(True)}


def summary_row(name: str, value: str, details: str, discussion_approved: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(discussion_approved)}


def placeholder_row(name: str, status: str, value: str, approval_required: str, boundary: str, discussion_approved: bool) -> dict[str, Any]:
    return {"placeholder_name": name, "placeholder_status": status, "placeholder_value": value, "approval_required_before_value": approval_required, "safety_boundary": boundary, **flags(discussion_approved)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, discussion_approved: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(discussion_approved)}


def evidence_row(name: str, value: str, details: str, discussion_approved: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(discussion_approved)}


def write_placeholder_outputs(root: Path, report_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], placeholder_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in PLACEHOLDER_OUTPUTS.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["placeholders"], PLACEHOLDER_COLUMNS, placeholder_rows)
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


def build_placeholder_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Volatility-targeted ticket-value placeholders complete. Non-executable; no values approved.",
        f"final_ticket_value_placeholder_status={summary_value(rows, 'final_ticket_value_placeholder_status')}",
        f"final_ticket_value_placeholder_decision={summary_value(rows, 'final_ticket_value_placeholder_decision')}",
        f"ticket_value_discussion_approved={summary_value(rows, 'ticket_value_discussion_approved')}",
        f"placeholder_count={summary_value(rows, 'placeholder_count')}",
        f"populated_order_value_count={summary_value(rows, 'populated_order_value_count')}",
        f"ticket_values_approved={summary_value(rows, 'ticket_values_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_quality_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Volatility-targeted ticket-value quality gate complete. Non-executable; no execution approved.",
        f"final_ticket_value_quality_gate_status={summary_value(rows, 'final_ticket_value_quality_gate_status')}",
        f"final_ticket_value_quality_gate_decision={summary_value(rows, 'final_ticket_value_quality_gate_decision')}",
        f"quality_gate_passed={summary_value(rows, 'quality_gate_passed')}",
        f"placeholder_count={summary_value(rows, 'placeholder_count')}",
        f"populated_order_value_count={summary_value(rows, 'populated_order_value_count')}",
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
