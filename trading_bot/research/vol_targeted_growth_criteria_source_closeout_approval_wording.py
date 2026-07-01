"""Saved-output approval wording checkpoint for criteria-source blocker closeout.

This report defines a simple future human approval phrase for closing only the
criteria_source_reviewed blocker. It does not record approval, close blockers,
create ticket values, create executable tickets, call Alpaca, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = "I approve closing the criteria_source_reviewed blocker only."
FINAL_STATUS = "vol_targeted_growth_criteria_source_closeout_approval_wording_manual_review_required"
FINAL_DECISION = "CRITERIA_SOURCE_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED"
NEXT_STEP = "wait_for_explicit_simple_criteria_source_closeout_approval"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_approval_wording_evidence.csv"),
}

INPUT_FILES = {
    "criteria_source_candidate": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_candidate_review_summary.csv"),
    "closeout_candidate_rollup": Path("data/vol_targeted_growth_executable_ticket_criteria_closeout_candidate_review_rollup_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "approval_wording_defined": True,
    "simple_approval_phrase_defined": True,
    "closeout_candidate_only": True,
    "blocker_closed": False,
    "blockers_closed": False,
    "approval_requested": False,
    "approval_recorded": False,
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
class CriteriaSourceCloseoutApprovalWordingResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_criteria_source_closeout_approval_wording(
    root_dir: Path | str = ".",
) -> CriteriaSourceCloseoutApprovalWordingResult:
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
    return CriteriaSourceCloseoutApprovalWordingResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_criteria_source_closeout_approval_wording(
    root_dir: Path | str = ".",
) -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted criteria-source closeout approval wording is missing.",
            "Run `python bot.py --vol-targeted-growth-criteria-source-closeout-approval-wording` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted criteria-source closeout approval wording saved display. Report only; no approval recorded.",
        f"final_approval_wording_status: {summary_value(rows, 'final_approval_wording_status')}",
        f"final_approval_wording_decision: {summary_value(rows, 'final_approval_wording_decision')}",
        f"target_blocker: {summary_value(rows, 'target_blocker')}",
        f"future_approval_phrase: {summary_value(rows, 'future_approval_phrase')}",
        f"candidate_review_decision: {summary_value(rows, 'candidate_review_decision')}",
        f"closeout_candidate_rollup_decision: {summary_value(rows, 'closeout_candidate_rollup_decision')}",
        f"go_no_go_decision: {summary_value(rows, 'go_no_go_decision')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "blocker_closed=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "candidate_review_decision": summary_value(inputs["criteria_source_candidate"], "final_candidate_review_decision") or "missing_criteria_source_closeout_candidate_review",
        "candidate_review_status": summary_value(inputs["criteria_source_candidate"], "final_candidate_review_status") or "missing_criteria_source_closeout_candidate_review",
        "closeout_candidate_rollup_decision": summary_value(inputs["closeout_candidate_rollup"], "final_candidate_review_decision") or "missing_closeout_candidate_rollup",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row(
            "criteria_source_closeout_phrase",
            "approval_wording_defined_not_approved",
            "high",
            APPROVAL_PHRASE,
            "A short future approval phrase is defined for only one blocker.",
            NEXT_STEP,
        ),
        report_row(
            "criteria_source_candidate_state",
            "candidate_ready_for_manual_review" if context["candidate_review_decision"] == "CLOSEOUT_CANDIDATE_READY_FOR_MANUAL_REVIEW" else "manual_review_required",
            "high",
            context["candidate_review_decision"],
            "The phrase is only meaningful after the candidate review is present.",
            "review_candidate_state_before_any_closeout",
        ),
        report_row(
            "approval_boundary",
            "approval_not_recorded",
            "critical",
            "approval_requested=false; approval_recorded=false; blockers_closed=false",
            "This wording checkpoint is not itself approval.",
            "do_not_close_blocker_without_future_explicit_phrase",
        ),
    ]


def build_summary_rows(context: dict[str, str], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("final_approval_wording_status", FINAL_STATUS, "Simple wording checkpoint is saved-output/manual-review only."),
        ("final_approval_wording_decision", FINAL_DECISION, "A future phrase is defined, but no approval has been recorded."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("target_blocker", "criteria_source_reviewed", "Only this blocker could be closed by the future phrase."),
        ("future_approval_phrase", APPROVAL_PHRASE, "Short phrase the user may use later if they choose."),
        ("candidate_review_status", context["candidate_review_status"], "Saved candidate-review status."),
        ("candidate_review_decision", context["candidate_review_decision"], "Saved candidate-review decision."),
        ("closeout_candidate_rollup_decision", context["closeout_candidate_rollup_decision"], "Saved closeout-candidate rollup decision."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go dashboard decision."),
        ("approval_wording_row_count", str(len(report_rows)), "Saved report row count."),
        ("largest_blocker", "approval_wording_defined_but_not_recorded", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Wait for future explicit approval phrase before closing the one blocker."),
    ]
    return [summary_row(*row) for row in rows]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]], context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("approval_wording_defined_but_not_recorded", "blocked", "critical", "approval_recorded=false", NEXT_STEP),
        blocker_row("criteria_source_blocker_not_closed", "blocked", "critical", "blocker_closed=false; blockers_closed=false", "future_explicit_approval_required"),
        blocker_row("ticket_values_not_approved", "blocked", "critical", "order_values_populated=false", "keep_ticket_values_blank"),
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
    rows.append(evidence_row("future_approval_phrase", APPROVAL_PHRASE, "Simple phrase only; not recorded approval."))
    rows.append(evidence_row("candidate_review_decision", context["candidate_review_decision"], "Saved candidate review context."))
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, order, alert, SQLite, or scheduling path is used."))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Executable-ticket criteria-source closeout approval wording complete. Report only; no approval recorded.",
        f"final_approval_wording_status={summary_value(summary_rows, 'final_approval_wording_status')}",
        f"final_approval_wording_decision={summary_value(summary_rows, 'final_approval_wording_decision')}",
        f"target_blocker={summary_value(summary_rows, 'target_blocker')}",
        f"future_approval_phrase={summary_value(summary_rows, 'future_approval_phrase')}",
        f"candidate_review_decision={summary_value(summary_rows, 'candidate_review_decision')}",
        f"closeout_candidate_rollup_decision={summary_value(summary_rows, 'closeout_candidate_rollup_decision')}",
        f"go_no_go_decision={summary_value(summary_rows, 'go_no_go_decision')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "blocker_closed=false; blockers_closed=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
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
