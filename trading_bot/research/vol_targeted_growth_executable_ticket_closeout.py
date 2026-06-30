"""Saved-output executable-ticket closeout checkpoints for the volatility seed.

These reports read saved CSV summaries only. They do not call Alpaca, read
positions, refresh market data, populate order values, create executable
tickets, submit orders, or approve execution.
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
CLOSEOUT_STATUS = "vol_targeted_growth_executable_ticket_prerequisites_closeout_manual_review_required"
CLOSEOUT_DECISION = "EXECUTABLE_TICKET_PREREQUISITES_NOT_CLOSED"
APPROVAL_STATUS = "vol_targeted_growth_executable_ticket_approval_readiness_not_ready"
APPROVAL_DECISION = "NOT_READY_TO_REQUEST_EXECUTABLE_TICKET_APPROVAL"

COMMON_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
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

CLOSEOUT_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_executable_ticket_prerequisites_closeout.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_prerequisites_closeout_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_prerequisites_closeout_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_prerequisites_closeout_evidence.csv"),
}

APPROVAL_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_executable_ticket_approval_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_approval_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_approval_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_approval_readiness_evidence.csv"),
}

INPUT_FILES = {
    "post_gate_review": Path("data/vol_targeted_growth_post_gate_review_summary.csv"),
    "ticket_value_design": Path("data/vol_targeted_growth_manual_ticket_value_design_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
    "gap_list": Path("data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"),
    "manual_approval_gate": Path("data/vol_targeted_growth_manual_execution_design_approval_gate_summary.csv"),
}

REPORT_COLUMNS = ["check_name", "status", "risk_level", "evidence", "interpretation", "required_next_step", *COMMON_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *COMMON_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *COMMON_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *COMMON_FLAGS.keys()]


@dataclass
class SavedReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_executable_ticket_prerequisites_closeout(root_dir: Path | str = ".") -> SavedReportResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = closeout_report_rows(context)
    summary_rows = closeout_summary_rows(context, report_rows, inputs)
    blocker_rows = closeout_blocker_rows(context, inputs)
    evidence_rows = evidence_rows_for(inputs)
    paths = write_all(root, CLOSEOUT_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return SavedReportResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, closeout_lines(summary_rows, paths))


def show_vol_targeted_growth_executable_ticket_prerequisites_closeout(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / CLOSEOUT_OUTPUTS["summary"],
        "Volatility-targeted executable-ticket prerequisites closeout saved display. Report only; no execution approved.",
        [
            "final_prerequisites_closeout_status",
            "final_prerequisites_closeout_decision",
            "active_seed",
            "post_gate_review_status",
            "ticket_value_design_decision",
            "go_no_go_decision",
            "remaining_blocker_count",
            "largest_blocker",
            "recommended_next_step",
        ],
    )


def generate_vol_targeted_growth_executable_ticket_approval_readiness(root_dir: Path | str = ".") -> SavedReportResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    closeout_rows = read_csv_rows(root / CLOSEOUT_OUTPUTS["summary"])
    context = build_context(inputs)
    report_rows = approval_report_rows(context, closeout_rows)
    summary_rows = approval_summary_rows(context, closeout_rows, report_rows)
    blocker_rows = approval_blocker_rows(context, closeout_rows, inputs)
    evidence_rows = evidence_rows_for(inputs) + [
        evidence_row("closeout_summary_input", f"{CLOSEOUT_OUTPUTS['summary']}; rows={len(closeout_rows)}", "Saved closeout summary row count.")
    ]
    paths = write_all(root, APPROVAL_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return SavedReportResult(paths, report_rows, summary_rows, blocker_rows, evidence_rows, approval_lines(summary_rows, paths))


def show_vol_targeted_growth_executable_ticket_approval_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / APPROVAL_OUTPUTS["summary"],
        "Volatility-targeted executable-ticket approval readiness saved display. Report only; approval not ready.",
        [
            "final_approval_readiness_status",
            "final_approval_readiness_decision",
            "active_seed",
            "closeout_decision",
            "approval_prompt_allowed",
            "executable_ticket_created",
            "order_values_populated",
            "largest_blocker",
            "recommended_next_step",
        ],
    )


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "post_gate_review_status": summary_value(inputs["post_gate_review"], "final_post_gate_review_status") or "missing_post_gate_review",
        "post_gate_review_decision": summary_value(inputs["post_gate_review"], "final_post_gate_review_decision") or "missing_post_gate_review_decision",
        "ticket_value_design_status": summary_value(inputs["ticket_value_design"], "final_ticket_value_design_status") or "missing_ticket_value_design",
        "ticket_value_design_decision": summary_value(inputs["ticket_value_design"], "final_ticket_value_design_decision") or "missing_ticket_value_design_decision",
        "populated_ticket_value_count": summary_value(inputs["ticket_value_design"], "populated_ticket_value_count") or "missing_populated_ticket_value_count",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
        "gap_list_decision": summary_value(inputs["gap_list"], "final_ticket_design_decision") or "missing_gap_list",
        "manual_approval_decision": summary_value(inputs["manual_approval_gate"], "final_approval_gate_decision") or "missing_manual_approval_gate",
    }


def closeout_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row("fresh_broker_context_reviewed", "present_review_only", "high", context["post_gate_review_decision"], "Broker context exists as saved review evidence only.", "keep_context_non_executable"),
        report_row("ticket_values_reviewed", "values_not_approved", "critical", context["ticket_value_design_decision"], "Ticket-value fields were reviewed but executable values remain unapproved.", "separate_explicit_value_approval_required"),
        report_row("go_no_go_blocks_execution", "blocked", "critical", context["go_no_go_decision"], "The dashboard remains no-go/monitor-only.", "keep_go_no_go_blocking_execution"),
        report_row("manual_execution_approval_missing", "blocked", "critical", context["manual_approval_decision"], "No separate executable-ticket approval is recorded.", "future_explicit_approval_prompt_required"),
    ]


def closeout_summary_rows(context: dict[str, str], report_rows: list[dict[str, Any]], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    missing = [name for name, rows in inputs.items() if not rows]
    data = [
        ("final_prerequisites_closeout_status", CLOSEOUT_STATUS, "Closeout remains manual-review only."),
        ("final_prerequisites_closeout_decision", CLOSEOUT_DECISION, "Executable ticket prerequisites remain open."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("post_gate_review_status", context["post_gate_review_status"], "Saved post-gate review status."),
        ("ticket_value_design_decision", context["ticket_value_design_decision"], "Saved manual ticket-value design decision."),
        ("populated_ticket_value_count", context["populated_ticket_value_count"], "Executable value count from saved design."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go decision."),
        ("manual_approval_decision", context["manual_approval_decision"], "Saved manual approval gate decision."),
        ("remaining_blocker_count", str(len(report_rows) + len(missing)), "Closeout blocker count."),
        ("largest_blocker", "executable_ticket_values_and_approval_not_approved", "Primary remaining blocker."),
        ("recommended_next_step", "manual_review_closeout_before_any_executable_ticket_approval_request", "Review before any future approval request."),
    ]
    return [summary_row(*item) for item in data]


def closeout_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("ticket_values_not_approved", "blocked", "critical", context["ticket_value_design_decision"], "do_not_populate_executable_values"),
        blocker_row("manual_execution_approval_missing", "blocked", "critical", context["manual_approval_decision"], "future_explicit_approval_prompt_required"),
        blocker_row("go_no_go_is_no_go", "blocked", "critical", context["go_no_go_decision"], "keep_monitor_only"),
        blocker_row("execution_not_approved", "blocked", "critical", "All execution flags remain false.", "keep_all_approval_flags_false"),
    ]
    for name, rows_for_input in inputs.items():
        if not rows_for_input:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def approval_report_rows(context: dict[str, str], closeout_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    closeout_decision = summary_value(closeout_rows, "final_prerequisites_closeout_decision") or "missing_closeout"
    return [
        report_row("closeout_state", "not_ready", "critical", closeout_decision, "Prerequisites are not closed.", "review_closeout_first"),
        report_row("approval_prompt_boundary", "not_allowed", "critical", APPROVAL_DECISION, "This report does not request or record approval.", "do_not_request_executable_ticket_approval_yet"),
        report_row("ticket_value_boundary", "blocked", "critical", context["ticket_value_design_decision"], "Values remain review-only.", "keep_values_blank"),
        report_row("execution_boundary", "blocked", "critical", "execution_approved=false", "No execution approval exists.", "keep_all_approval_flags_false"),
    ]


def approval_summary_rows(context: dict[str, str], closeout_rows: list[dict[str, str]], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_approval_readiness_status", APPROVAL_STATUS, "Executable-ticket approval readiness remains not ready."),
        ("final_approval_readiness_decision", APPROVAL_DECISION, "Do not request approval yet."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("closeout_decision", summary_value(closeout_rows, "final_prerequisites_closeout_decision") or "missing_closeout", "Saved closeout decision."),
        ("ticket_value_design_decision", context["ticket_value_design_decision"], "Saved ticket-value design decision."),
        ("approval_prompt_allowed", "False", "No approval prompt is allowed by this checkpoint."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("order_values_populated", "False", "No executable values are populated."),
        ("remaining_blocker_count", str(len(report_rows)), "Readiness blocker count."),
        ("largest_blocker", "approval_request_not_ready_prerequisites_open", "Primary readiness blocker."),
        ("recommended_next_step", "manual_review_approval_readiness_after_prerequisites_closeout", "Review readiness before any future explicit approval request."),
    ]
    return [summary_row(*item) for item in data]


def approval_blocker_rows(context: dict[str, str], closeout_rows: list[dict[str, str]], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("approval_request_not_ready", "blocked", "critical", summary_value(closeout_rows, "final_prerequisites_closeout_decision") or "missing_closeout", "do_not_request_approval_yet"),
        blocker_row("ticket_values_not_approved", "blocked", "critical", context["ticket_value_design_decision"], "keep_values_blank"),
        blocker_row("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if not closeout_rows:
        rows.insert(0, blocker_row("missing_prerequisites_closeout", "blocked", "high", f"Missing saved input: {CLOSEOUT_OUTPUTS['summary']}", "run_prerequisites_closeout_first"))
    for name, rows_for_input in inputs.items():
        if not rows_for_input:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return [evidence_row(*item) for item in rows]


def closeout_lines(rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return lines_for("Executable-ticket prerequisites closeout complete. Report only; no execution approved.", rows, paths["report"], "final_prerequisites_closeout_status", "final_prerequisites_closeout_decision")


def approval_lines(rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return lines_for("Executable-ticket approval readiness complete. Not ready; no approval requested.", rows, paths["report"], "final_approval_readiness_status", "final_approval_readiness_decision")


def lines_for(title: str, rows: list[dict[str, Any]], report_path: Path, status_key: str, decision_key: str) -> list[str]:
    return [
        title,
        f"{status_key}={summary_value(rows, status_key)}",
        f"{decision_key}={summary_value(rows, decision_key)}",
        f"active_seed={summary_value(rows, 'active_seed')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={report_path}",
        "order_values_populated=false; order_instructions_created=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def show_summary(path: Path, title: str, keys: list[str]) -> tuple[int, list[str]]:
    if not path.exists():
        return 1, [f"{title} is missing.", "Run the matching report command first.", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false"]
    rows = read_csv_rows(path)
    lines = [title]
    lines.extend(f"{key}: {summary_value(rows, key)}" for key in keys)
    lines.append("order_values_populated=false; order_instructions_created=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false")
    return 0, lines


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def write_all(root: Path, outputs: dict[str, Path], report_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in outputs.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **COMMON_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **COMMON_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **COMMON_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **COMMON_FLAGS}


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
