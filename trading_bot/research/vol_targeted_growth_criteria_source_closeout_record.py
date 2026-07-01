"""Saved-output closeout record for the criteria_source_reviewed blocker.

This records Lewis's approval to close only the criteria_source_reviewed blocker.
It does not close any other blocker, change ticket values, create executable
tickets, call Alpaca, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve closing the criteria_source_reviewed blocker only."
FINAL_STATUS = "vol_targeted_growth_criteria_source_closeout_recorded_manual_review_required"
FINAL_DECISION = "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY"
NEXT_STEP = "refresh_execution_blocker_chain_after_single_criteria_source_closeout"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_evidence.csv"),
}

INPUT_FILES = {
    "approval_wording": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording_summary.csv"),
    "criteria_source_candidate": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_candidate_review_summary.csv"),
    "closeout_candidate_rollup": Path("data/vol_targeted_growth_executable_ticket_criteria_closeout_candidate_review_rollup_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "criteria_source_reviewed_closed": True,
    "single_blocker_closeout_only": True,
    "criteria_resolution_plan_closed": False,
    "approval_criteria_not_approval_closed": False,
    "other_blockers_closed": False,
    "executable_ticket_approval_recorded": False,
    "approval_readiness_changed": False,
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
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class CriteriaSourceCloseoutRecordResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_criteria_source_closeout_record(root_dir: Path | str = ".") -> CriteriaSourceCloseoutRecordResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_report_rows(context)
    summary_rows = build_summary_rows(context, report_rows)
    blocker_rows = build_blocker_rows(inputs, context)
    evidence_rows = build_evidence_rows(inputs, context)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return CriteriaSourceCloseoutRecordResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_criteria_source_closeout_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted criteria-source closeout record is missing.",
            "Run `python bot.py --vol-targeted-growth-criteria-source-closeout-record` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted criteria-source closeout record saved display. Report only; no execution approved.",
        f"final_closeout_record_status: {summary_value(rows, 'final_closeout_record_status')}",
        f"final_closeout_record_decision: {summary_value(rows, 'final_closeout_record_decision')}",
        f"closed_blocker: {summary_value(rows, 'closed_blocker')}",
        f"closed_blocker_count: {summary_value(rows, 'closed_blocker_count')}",
        f"remaining_known_blockers: {summary_value(rows, 'remaining_known_blockers')}",
        f"approval_phrase_used: {summary_value(rows, 'approval_phrase_used')}",
        f"go_no_go_decision: {summary_value(rows, 'go_no_go_decision')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "criteria_source_reviewed_closed=true; other_blockers_closed=false; executable_ticket_approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "approval_wording_decision": summary_value(inputs["approval_wording"], "final_approval_wording_decision") or "missing_approval_wording",
        "future_approval_phrase": summary_value(inputs["approval_wording"], "future_approval_phrase") or "missing_future_approval_phrase",
        "candidate_review_decision": summary_value(inputs["criteria_source_candidate"], "final_candidate_review_decision") or "missing_criteria_source_candidate",
        "closeout_candidate_rollup_decision": summary_value(inputs["closeout_candidate_rollup"], "final_candidate_review_decision") or "missing_closeout_candidate_rollup",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row(
            "criteria_source_reviewed_closeout",
            "closed_for_criteria_source_only",
            "high",
            APPROVAL_PHRASE,
            "The criteria source has been reviewed and the single source blocker is closed.",
            NEXT_STEP,
        ),
        report_row(
            "remaining_blockers",
            "manual_review_required",
            "critical",
            "criteria_resolution_plan_open; approval_criteria_not_approval; ticket_values_not_approved",
            "Other execution-ticket blockers remain open and prevent ticket/execution approval.",
            "continue_blocker_chain_without_ticket_creation",
        ),
        report_row(
            "execution_boundary",
            "execution_blocked",
            "critical",
            context["go_no_go_decision"],
            "Closing this single blocker is not executable-ticket approval.",
            "keep_go_no_go_dashboard_no_go",
        ),
    ]


def build_summary_rows(context: dict[str, str], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("final_closeout_record_status", FINAL_STATUS, "Single-blocker closeout record is saved-output/manual-review only."),
        ("final_closeout_record_decision", FINAL_DECISION, "Only criteria_source_reviewed is closed."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("closed_blocker", "criteria_source_reviewed", "The only blocker closed by this record."),
        ("closed_blocker_count", "1", "Exactly one blocker was closed."),
        ("remaining_known_blockers", "criteria_resolution_plan_open;approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met", "Known blockers still preventing execution-ticket approval."),
        ("approval_phrase_used", APPROVAL_PHRASE, "User-approved closeout scope for this one blocker."),
        ("approval_wording_decision", context["approval_wording_decision"], "Saved approval wording decision."),
        ("candidate_review_decision", context["candidate_review_decision"], "Saved candidate review decision."),
        ("closeout_candidate_rollup_decision", context["closeout_candidate_rollup_decision"], "Saved closeout candidate rollup decision."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go dashboard decision."),
        ("closeout_record_row_count", str(len(report_rows)), "Saved report row count."),
        ("largest_blocker", "other_execution_ticket_blockers_remain_open", "Primary remaining blocker."),
        ("recommended_next_step", NEXT_STEP, "Refresh the report-only blocker chain after this one closeout."),
    ]
    return [summary_row(*row) for row in rows]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]], context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("criteria_resolution_plan_open", "blocked", "critical", "Still open after criteria-source closeout.", "resolve_resolution_plan_in_separate_review"),
        blocker_row("approval_criteria_not_approval", "blocked", "critical", "Approval criteria are not executable-ticket approval.", "keep_approval_blocked"),
        blocker_row("ticket_values_not_approved", "blocked", "critical", "No side, quantity, order type, or time-in-force is approved.", "do_not_populate_ticket_values"),
        blocker_row("executable_ticket_not_created", "blocked", "critical", "executable_ticket_created=false", "do_not_create_executable_ticket"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("go_no_go_remains_no_go", "blocked", "critical", context["go_no_go_decision"], "keep_dashboard_no_go"),
    ]
    for name, input_rows in inputs.items():
        if not input_rows:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("approval_phrase_used", APPROVAL_PHRASE, "Scope is exactly one blocker."))
    rows.append(evidence_row("approval_wording_decision", context["approval_wording_decision"], "Saved wording checkpoint context."))
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, order, alert, SQLite, or scheduling path is used."))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Executable-ticket criteria-source closeout record complete. Report only; one blocker closed.",
        f"final_closeout_record_status={summary_value(summary_rows, 'final_closeout_record_status')}",
        f"final_closeout_record_decision={summary_value(summary_rows, 'final_closeout_record_decision')}",
        f"closed_blocker={summary_value(summary_rows, 'closed_blocker')}",
        f"closed_blocker_count={summary_value(summary_rows, 'closed_blocker_count')}",
        f"remaining_known_blockers={summary_value(summary_rows, 'remaining_known_blockers')}",
        f"approval_phrase_used={summary_value(summary_rows, 'approval_phrase_used')}",
        f"go_no_go_decision={summary_value(summary_rows, 'go_no_go_decision')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "criteria_source_reviewed_closed=true; other_blockers_closed=false; executable_ticket_approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {
        "check_name": name,
        "status": status,
        "risk_level": risk,
        "evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


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
