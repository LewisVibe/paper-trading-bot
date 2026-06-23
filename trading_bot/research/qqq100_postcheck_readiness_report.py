"""Saved-output QQQ100 postcheck readiness runbook.

This report documents the manual read-only postcheck needed to fill missing
QQQ100 saved quantity evidence. It does not call Alpaca, read live positions,
create order instructions, submit/cancel/replace orders, write SQLite, send
alerts, schedule anything, or approve follow-up orders.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"
READONLY_POSTCHECK_COMMAND = "python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check"
MISSING_POSTCHECK_FILE = r"data\qqq100_paper_postcheck.csv"
MISSING_QUANTITY_FIELD = "position_quantity_abs_or_current_position_quantity_abs"

OUTPUT_FILES = {
    "report": Path("data/qqq100_postcheck_readiness_report.csv"),
    "summary": Path("data/qqq100_postcheck_readiness_summary.csv"),
    "blockers": Path("data/qqq100_postcheck_readiness_blockers.csv"),
    "runbook": Path("data/qqq100_postcheck_readiness_runbook.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "check_name",
    "check_status",
    "finding",
    "missing_saved_file",
    "missing_saved_field",
    "future_evidence_command",
    "required_manual_approval",
    "required_next_step",
    "research_only",
    "report_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "alpaca_called",
    "live_positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_FLAGS.keys(),
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

RUNBOOK_COLUMNS = [
    "step_number",
    "step_name",
    "step_status",
    "instruction",
    "command_to_review",
    "must_not_do",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]


@dataclass
class Qqq100PostcheckReadinessReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    runbook_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_postcheck_readiness_report(
    root_dir: Path | str = ".",
) -> Qqq100PostcheckReadinessReportResult:
    root = Path(root_dir)
    report_rows = build_report_rows()
    summary_rows = build_summary_rows()
    blocker_rows = build_blocker_rows()
    runbook_rows = build_runbook_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["runbook"], RUNBOOK_COLUMNS, runbook_rows)
    return Qqq100PostcheckReadinessReportResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        runbook_rows=runbook_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_qqq100_postcheck_readiness_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "QQQ100 postcheck readiness report is missing.",
            "Run `python bot.py --qqq100-postcheck-readiness-report` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 postcheck readiness saved display. Report only; no broker read performed.",
        f"final_postcheck_readiness_status: {summary_value(rows, 'final_postcheck_readiness_status')}",
        f"missing_saved_file: {summary_value(rows, 'missing_saved_file')}",
        f"missing_saved_field: {summary_value(rows, 'missing_saved_field')}",
        f"future_evidence_command: {summary_value(rows, 'future_evidence_command')}",
        f"manual_approval_required_before_running_postcheck: {summary_value(rows, 'manual_approval_required_before_running_postcheck')}",
        f"postcheck_creates_orders: {summary_value(rows, 'postcheck_creates_orders')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        "Warning: this report does not run postcheck and does not approve follow-up orders.",
    ]


def build_report_rows() -> list[dict[str, Any]]:
    return [
        report_row(
            "vps_missing_saved_quantity_evidence",
            "blocked_manual_review_required",
            "VPS saved evidence is blocked until the QQQ100 read-only postcheck output contains exact quantity evidence.",
            "Do not treat a saved position label alone as exact one-share alignment.",
        ),
        report_row(
            "future_evidence_command_identified",
            "manual_approval_required",
            "The only relevant future evidence command is the existing read-only QQQ100 postcheck command.",
            "Ask for explicit user approval before running the read-only postcheck.",
        ),
        report_row(
            "postcheck_boundary",
            "pass",
            "The postcheck may read broker order and position state after confirmation, but it must not create, submit, cancel, replace, or prepare orders.",
            "Keep postcheck separate from paper execution and follow-up order decisions.",
        ),
        report_row(
            "approval_flags_false",
            "pass",
            "This readiness runbook keeps execution, paper execution, scheduling, live trading, and follow-up order approvals false.",
            "Use a separate explicit approval prompt before any read-only broker check.",
        ),
    ]


def build_summary_rows() -> list[dict[str, Any]]:
    rows = [
        ("final_postcheck_readiness_status", "qqq100_postcheck_manual_approval_required", "Runbook status only; postcheck has not been run."),
        ("candidate_strategy", STRATEGY_NAME, "Only QQQ100 is in scope."),
        ("candidate_ticker", TICKER, "Only QQQ is in scope."),
        ("missing_saved_file", MISSING_POSTCHECK_FILE, "Exact missing saved evidence file on VPS."),
        ("missing_saved_field", MISSING_QUANTITY_FIELD, "Exact missing saved quantity field."),
        ("future_evidence_command", READONLY_POSTCHECK_COMMAND, "Read-only postcheck command to review later."),
        ("manual_approval_required_before_running_postcheck", "True", "This task does not approve running postcheck."),
        ("postcheck_creates_orders", "False", "Postcheck must never create, submit, cancel, replace, or prepare orders."),
        ("postcheck_reads_broker_state_after_confirmation", "True", "Postcheck may read broker order/position state only after explicit confirmation."),
        ("followup_order_approved", "False", "Postcheck output does not approve follow-up or repeat paper orders."),
        ("recommended_next_step", "request_explicit_manual_approval_before_readonly_qqq100_postcheck", "Next step is approval review, not execution."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows() -> list[dict[str, Any]]:
    blockers = [
        ("missing_saved_postcheck_file", "blocked", "high", f"Missing saved file: {MISSING_POSTCHECK_FILE}.", "Run only the explicitly approved read-only postcheck later."),
        ("missing_saved_quantity_field", "blocked", "high", f"Missing saved field: {MISSING_QUANTITY_FIELD}.", "Do not mark QQQ100 alignment verified without saved quantity evidence."),
        ("manual_approval_required", "blocked", "critical", "The read-only postcheck command must not be run without explicit user approval.", "Ask the user before running postcheck."),
        ("followup_order_not_approved", "blocked", "critical", "Postcheck output does not approve follow-up or repeat paper orders.", "Keep follow-up order approval false."),
        ("execution_not_approved", "blocked", "critical", "This runbook does not approve execution or paper execution.", "Do not run paper execution commands."),
        ("scheduling_not_approved", "blocked", "critical", "This runbook does not approve scheduling.", "Do not schedule broker-read or order-capable commands."),
    ]
    return [
        {
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for name, status, severity, details, next_step in blockers
    ]


def build_runbook_rows() -> list[dict[str, Any]]:
    steps = [
        (
            "1",
            "review_missing_saved_evidence",
            "required",
            f"Confirm the missing evidence is {MISSING_POSTCHECK_FILE} and {MISSING_QUANTITY_FIELD}.",
            "",
            "Do not infer exact alignment from a saved position label alone.",
            "Keep paper-live evidence incomplete until quantity is saved.",
        ),
        (
            "2",
            "request_manual_approval",
            "required",
            "Ask the user before running the read-only broker-state postcheck.",
            READONLY_POSTCHECK_COMMAND,
            "Do not run postcheck automatically from this report.",
            "Wait for explicit user approval.",
        ),
        (
            "3",
            "run_readonly_postcheck_later_if_approved",
            "future_manual_step",
            "If explicitly approved later, run only the read-only QQQ100 postcheck command.",
            READONLY_POSTCHECK_COMMAND,
            "Do not run QQQ100 paper execution, paper-order tests, slow-SMA execution, or normal bot execution.",
            "Refresh evidence audit and state summary after postcheck.",
        ),
        (
            "4",
            "preserve_no_followup_approval",
            "required",
            "Even after postcheck, follow-up or repeat paper orders remain unapproved.",
            "",
            "Do not create order instructions or approve scheduling.",
            "Use a separate future design/review prompt for any follow-up action.",
        ),
    ]
    return [
        {
            "step_number": number,
            "step_name": name,
            "step_status": status,
            "instruction": instruction,
            "command_to_review": command,
            "must_not_do": must_not_do,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for number, name, status, instruction, command, must_not_do, next_step in steps
    ]


def report_row(name: str, status: str, finding: str, next_step: str) -> dict[str, Any]:
    return {
        "check_name": name,
        "check_status": status,
        "finding": finding,
        "missing_saved_file": MISSING_POSTCHECK_FILE,
        "missing_saved_field": MISSING_QUANTITY_FIELD,
        "future_evidence_command": READONLY_POSTCHECK_COMMAND,
        "required_manual_approval": True,
        "required_next_step": next_step,
        **ROW_SAFETY,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ100 postcheck readiness report complete. Runbook only; postcheck was not run.",
        f"Final status: {summary_value(summary_rows, 'final_postcheck_readiness_status')}",
        f"Missing saved file: {summary_value(summary_rows, 'missing_saved_file')}",
        f"Missing saved field: {summary_value(summary_rows, 'missing_saved_field')}",
        f"Future evidence command: {summary_value(summary_rows, 'future_evidence_command')}",
        f"Manual approval required before running postcheck: {summary_value(summary_rows, 'manual_approval_required_before_running_postcheck')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report/summary/blockers/runbook to {output_paths['report']}; {output_paths['summary']}; {output_paths['blockers']}; {output_paths['runbook']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        "Warning: this report does not run postcheck and does not approve follow-up orders.",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
