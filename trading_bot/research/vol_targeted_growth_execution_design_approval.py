"""Saved-output execution-design approval checkpoint for the volatility seed.

This module records approval to continue designing the next non-submitting
execution-ticket layer only. It does not create ticket values, create an
executable ticket, call a broker, submit orders, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve execution design only for the active volatility seed; do not create or submit orders."
WORDING_STATUS = "vol_targeted_growth_execution_design_approval_wording_manual_review_required"
WORDING_DECISION = "EXECUTION_DESIGN_APPROVAL_WORDING_DEFINED_NOT_APPROVED"
RECORD_STATUS = "vol_targeted_growth_execution_design_approval_recorded_manual_review_required"
RECORD_DECISION = "EXECUTION_DESIGN_APPROVED_NO_ORDER_OR_EXECUTION_APPROVAL"
NEXT_STEP = "design_non_submitting_executable_ticket_values_without_order_approval"

WORDING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_execution_design_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_execution_design_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_execution_design_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_execution_design_approval_wording_evidence.csv"),
}

RECORD_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_execution_design_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_execution_design_approval_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_execution_design_approval_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_execution_design_approval_record_evidence.csv"),
}

INPUT_FILES = {
    "execution_approval_request_readiness": Path("data/vol_targeted_growth_execution_approval_request_readiness_summary.csv"),
    "final_ticket_blockers_closeout": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_record_summary.csv"),
    "execution_blocker_rollup": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv"),
    "executable_ticket_gap_list": Path("data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

BASE_SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "execution_design_only": True,
    "approval_requested": False,
    "approval_recorded": False,
    "manual_execution_design_approved": False,
    "manual_execution_design_approval_recorded": False,
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

REPORT_COLUMNS = ["check_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *BASE_SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *BASE_SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *BASE_SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *BASE_SAFETY_FLAGS.keys()]


@dataclass
class ExecutionDesignApprovalResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_execution_design_approval_wording(root_dir: Path | str = ".") -> ExecutionDesignApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        row("execution_design_approval_phrase", "approval_wording_defined_not_recorded", "critical", APPROVAL_PHRASE, "Defines the exact narrow wording for design-only approval.", "wait_for_explicit_execution_design_only_approval", False),
        row("execution_boundary", "execution_not_approved", "critical", "execution_approved=false; order_values_populated=false; executable_ticket_created=false", "The wording does not create values, tickets, or orders.", "keep_execution_blocked", False),
    ]
    summary_rows = common_summary(inputs, WORDING_STATUS, WORDING_DECISION, "False", "False", "wait_for_explicit_execution_design_only_approval")
    blocker_rows = [
        blocker_row("execution_design_approval_not_recorded", "blocked", "critical", "manual_execution_design_approved=false", "wait_for_explicit_execution_design_only_approval", False),
        blocker_row("execution_not_approved", "blocked", "critical", "No order or paper execution approval exists.", "keep_execution_blocked", False),
    ]
    evidence_rows = evidence_for(inputs, False) + [evidence_row("future_approval_phrase", APPROVAL_PHRASE, "Simple design-only wording; not recorded approval.", False)]
    output_paths = write_all(root, WORDING_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return ExecutionDesignApprovalResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, lines("Execution design approval wording complete. Report only; no approval recorded.", summary_rows, output_paths["report"], "final_execution_design_wording_status", "final_execution_design_wording_decision"))


def show_vol_targeted_growth_execution_design_approval_wording(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / WORDING_OUTPUTS["summary"], "Volatility-targeted execution design approval wording saved display. Report only; no approval recorded.", "final_execution_design_wording_status", "final_execution_design_wording_decision")


def generate_vol_targeted_growth_execution_design_approval_record(root_dir: Path | str = ".") -> ExecutionDesignApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        row("execution_design_approval_record", "design_only_approval_recorded", "critical", APPROVAL_PHRASE, "Approval is limited to designing the next non-submitting ticket layer.", NEXT_STEP, True),
        row("order_boundary", "orders_not_approved", "critical", "orders_created=false; orders_submitted=false; order_values_populated=false", "No executable order values or order instructions are created.", NEXT_STEP, True),
        row("execution_boundary", "execution_not_approved", "critical", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false", "Execution approval remains separate and false.", NEXT_STEP, True),
    ]
    summary_rows = common_summary(inputs, RECORD_STATUS, RECORD_DECISION, "True", "True", NEXT_STEP)
    blocker_rows = [
        blocker_row("execution_not_approved", "blocked", "critical", "Design approval is not order approval.", NEXT_STEP, True),
        blocker_row("executable_ticket_not_created", "blocked", "critical", "executable_ticket_created=false; order_values_populated=false", "separate_future_non_submitting_ticket_design_checkpoint", True),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", True),
    ]
    evidence_rows = evidence_for(inputs, True) + [evidence_row("recorded_approval_phrase", APPROVAL_PHRASE, "Design-only approval recorded; order execution remains blocked.", True)]
    output_paths = write_all(root, RECORD_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return ExecutionDesignApprovalResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, lines("Execution design approval record complete. Design only; no execution approved.", summary_rows, output_paths["report"], "final_execution_design_record_status", "final_execution_design_record_decision"))


def show_vol_targeted_growth_execution_design_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / RECORD_OUTPUTS["summary"], "Volatility-targeted execution design approval record saved display. Design only; no execution approved.", "final_execution_design_record_status", "final_execution_design_record_decision")


def flags(design_approved: bool) -> dict[str, bool]:
    updated = dict(BASE_SAFETY_FLAGS)
    updated["approval_recorded"] = design_approved
    updated["manual_execution_design_approved"] = design_approved
    updated["manual_execution_design_approval_recorded"] = design_approved
    return updated


def common_summary(inputs: dict[str, list[dict[str, str]]], status: str, decision: str, design_approved: str, design_recorded: str, next_step: str) -> list[dict[str, Any]]:
    design_approved_bool = design_approved == "True"
    status_key = "final_execution_design_record_status" if design_approved_bool else "final_execution_design_wording_status"
    decision_key = "final_execution_design_record_decision" if design_approved_bool else "final_execution_design_wording_decision"
    data = [
        (status_key, status, "Saved-output execution-design checkpoint."),
        (decision_key, decision, "Design-only decision; no order or execution approval."),
        ("active_seed", ACTIVE_SEED, "Current paper-live seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_phrase", APPROVAL_PHRASE, "Narrow approval wording for execution design only."),
        ("execution_design_approved", design_approved, "True only for the design-only record command."),
        ("manual_execution_design_approved", design_approved, "Design approval only; not execution approval."),
        ("manual_execution_design_approval_recorded", design_recorded, "True only for the design-only record command."),
        ("approval_requested", "False", "No order/execution approval request is made by this command."),
        ("execution_approval_request_readiness_decision", summary_value(inputs["execution_approval_request_readiness"], "final_readiness_decision") or "missing_execution_approval_request_readiness", "Prior readiness-to-ask context."),
        ("final_ticket_blockers_closeout_decision", summary_value(inputs["final_ticket_blockers_closeout"], "final_closeout_record_decision") or "missing_final_ticket_blockers_closeout", "Saved checklist closeout context."),
        ("closed_blocker_count", summary_value(inputs["execution_blocker_rollup"], "closed_blocker_count") or "missing_closed_blocker_count", "Saved blocker rollup context."),
        ("remaining_known_blockers", summary_value(inputs["execution_blocker_rollup"], "remaining_known_blockers_after_closeout") or "missing_remaining_known_blockers", "Saved blocker rollup context."),
        ("gap_list_largest_gap", summary_value(inputs["executable_ticket_gap_list"], "largest_gap") or "missing_executable_ticket_gap_list", "Saved executable-ticket gap context."),
        ("go_no_go_decision", summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard", "Saved dashboard context."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker ID is populated."),
        ("order_instructions_created", "False", "No executable order instructions are created."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("orders_created", "False", "No orders are created."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "execution_not_approved", "Design approval does not remove the execution blocker."),
        ("recommended_next_step", next_step, "Next step remains non-submitting design/review only."),
    ]
    return [summary_row(name, value, details, design_approved_bool) for name, value, details in data]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def evidence_for(inputs: dict[str, list[dict[str, str]]], design_approved: bool) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", design_approved) for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", design_approved))
    return rows


def row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, design_approved: bool) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(design_approved)}


def summary_row(name: str, value: str, details: str, design_approved: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(design_approved)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, design_approved: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(design_approved)}


def evidence_row(name: str, value: str, details: str, design_approved: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(design_approved)}


def write_all(root: Path, outputs: dict[str, Path], report_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in outputs.items()}
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


def show_summary(path: Path, title: str, status_key: str, decision_key: str) -> tuple[int, list[str]]:
    if not path.exists():
        return 1, [f"{title} is missing.", "Run the matching report command first.", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false"]
    rows = read_csv_rows(path)
    return 0, [
        title,
        f"{status_key}: {summary_value(rows, status_key)}",
        f"{decision_key}: {summary_value(rows, decision_key)}",
        f"approval_phrase: {summary_value(rows, 'approval_phrase')}",
        f"execution_design_approved: {summary_value(rows, 'execution_design_approved')}",
        f"manual_execution_design_approval_recorded: {summary_value(rows, 'manual_execution_design_approval_recorded')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def lines(title: str, rows: list[dict[str, Any]], report_path: Path, status_key: str, decision_key: str) -> list[str]:
    return [
        title,
        f"{status_key}={summary_value(rows, status_key)}",
        f"{decision_key}={summary_value(rows, decision_key)}",
        f"approval_phrase={summary_value(rows, 'approval_phrase')}",
        f"execution_design_approved={summary_value(rows, 'execution_design_approved')}",
        f"manual_execution_design_approval_recorded={summary_value(rows, 'manual_execution_design_approval_recorded')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
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
