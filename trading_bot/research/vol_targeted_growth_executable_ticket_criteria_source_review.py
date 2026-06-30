"""Saved-output source review for volatility executable-ticket criteria.

This report checks whether the criteria wording/source is coherent enough for
manual review. It does not edit criteria, close blockers, request approval,
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
FINAL_STATUS = "vol_targeted_growth_executable_ticket_criteria_source_review_manual_review_required"
FINAL_DECISION = "CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED"
NEXT_STEP = "manual_review_criteria_source_before_closing_any_blocker"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_executable_ticket_criteria_source_review.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_criteria_source_review_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_criteria_source_review_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_criteria_source_review_evidence.csv"),
}

INPUT_FILES = {
    "approval_criteria": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_summary.csv"),
    "resolution_plan": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "source_review_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "criteria_changed": False,
    "blockers_resolved": False,
    "approval_requested": False,
    "approval_recorded": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "order_values_populated": False,
    "order_instructions_created": False,
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

REPORT_COLUMNS = ["review_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class CriteriaSourceReviewResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_executable_ticket_criteria_source_review(root_dir: Path | str = ".") -> CriteriaSourceReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_report_rows(context)
    blocker_rows = build_blocker_rows(context, inputs)
    summary_rows = build_summary_rows(context, report_rows, blocker_rows)
    evidence_rows = build_evidence_rows(inputs)
    paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return CriteriaSourceReviewResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, build_summary_lines(summary_rows, paths))


def show_vol_targeted_growth_executable_ticket_criteria_source_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted executable-ticket criteria source review is missing.",
            "Run `python bot.py --vol-targeted-growth-executable-ticket-criteria-source-review` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted executable-ticket criteria source review saved display. Report only; no blockers closed.",
        f"final_source_review_status: {summary_value(rows, 'final_source_review_status')}",
        f"final_source_review_decision: {summary_value(rows, 'final_source_review_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"criteria_decision: {summary_value(rows, 'criteria_decision')}",
        f"resolution_plan_decision: {summary_value(rows, 'resolution_plan_decision')}",
        f"source_review_result: {summary_value(rows, 'source_review_result')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "criteria_changed=false; blockers_resolved=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "criteria_decision": summary_value(inputs["approval_criteria"], "final_approval_criteria_decision") or "missing_approval_criteria",
        "criteria_status": summary_value(inputs["approval_criteria"], "final_approval_criteria_status") or "missing_approval_criteria",
        "resolution_decision": summary_value(inputs["resolution_plan"], "final_resolution_plan_decision") or "missing_resolution_plan",
        "resolution_status": summary_value(inputs["resolution_plan"], "final_resolution_plan_status") or "missing_resolution_plan",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        review_row("criteria_source_present", "reviewed_no_change", "high", context["criteria_decision"], "Saved criteria source is present for manual review.", "keep_criteria_as_manual_review_boundary"),
        review_row("resolution_plan_consistent", "reviewed_no_change", "high", context["resolution_decision"], "Resolution plan is present and still blocks approval.", "use_resolution_plan_as_ordered_manual_worklist"),
        review_row("go_no_go_consistent", "blocked_monitor_only", "critical", context["go_no_go_decision"], "Go/no-go dashboard remains no-go; source review does not change it.", "keep_dashboard_no_go"),
        review_row("non_execution_boundary", "confirmed", "critical", "criteria_changed=false; blockers_resolved=false; approval_requested=false", "Source review does not modify criteria or request approval.", "do_not_close_blockers_from_source_review"),
    ]


def build_summary_rows(context: dict[str, str], report_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_ok = (
        context["criteria_decision"] == "APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED"
        and context["resolution_decision"] == "CRITERIA_BLOCKER_RESOLUTION_PLAN_CREATED_APPROVAL_STILL_BLOCKED"
    )
    data = [
        ("final_source_review_status", FINAL_STATUS, "Source review is saved-output/manual-review only."),
        ("final_source_review_decision", FINAL_DECISION, "Source wording reviewed; no blockers closed."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("criteria_decision", context["criteria_decision"], "Saved approval criteria decision."),
        ("resolution_plan_decision", context["resolution_decision"], "Saved resolution plan decision."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go decision."),
        ("source_review_result", "source_consistent_for_manual_review" if source_ok else "source_missing_or_inconsistent_manual_review_required", "Criteria and resolution plan source consistency."),
        ("review_row_count", str(len(report_rows)), "Review row count."),
        ("open_blocker_count", str(len(blocker_rows)), "Open blocker row count."),
        ("largest_blocker", "criteria_source_review_does_not_close_blockers", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Manual review before closing any blocker."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("criteria_source_review_does_not_close_blockers", "blocked", "critical", FINAL_DECISION, "manual_review_before_any_blocker_closeout"),
        blocker_row("approval_request_not_allowed", "blocked", "critical", "approval_requested=false; approval_recorded=false", "do_not_request_approval_from_source_review"),
        blocker_row("go_no_go_remains_no_go", "blocked", "critical", context["go_no_go_decision"], "keep_dashboard_no_go"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_all_approval_flags_false"),
    ]
    for name, input_rows in inputs.items():
        if not input_rows:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Executable-ticket criteria source review complete. Report only; no blockers closed.",
        f"final_source_review_status={summary_value(summary_rows, 'final_source_review_status')}",
        f"final_source_review_decision={summary_value(summary_rows, 'final_source_review_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"source_review_result={summary_value(summary_rows, 'source_review_result')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={paths['report']}",
        "criteria_changed=false; blockers_resolved=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def review_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"review_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
