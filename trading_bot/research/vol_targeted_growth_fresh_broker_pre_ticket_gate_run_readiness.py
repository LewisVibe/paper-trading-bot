"""Run-readiness checkpoint for the volatility fresh broker pre-ticket gate.

This report checks whether the saved design chain is ready for a future prompt
that may explicitly approve a read-only Alpaca broker-position gate run. It
does not run that gate, call Alpaca, read positions, populate order values,
create tickets, submit orders, schedule anything, or approve execution.
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
FINAL_STATUS_READY = "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_ready_to_request_manual_readonly_approval"
FINAL_STATUS_BLOCKED = "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_blocked_manual_review_required"
FINAL_DECISION_READY = "READY_TO_REQUEST_EXPLICIT_READONLY_ALPACA_APPROVAL"
FINAL_DECISION_BLOCKED = "NOT_READY_TO_REQUEST_READONLY_ALPACA_APPROVAL"
NEXT_STEP_READY = "ask_user_for_explicit_readonly_alpaca_pre_ticket_gate_run_approval_in_separate_prompt"
NEXT_STEP_BLOCKED = "refresh_missing_saved_design_reports_before_requesting_readonly_broker_gate_run"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_summary.csv"),
    "checks": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_checks.csv"),
    "blockers": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_blockers.csv"),
}

INPUT_FILES = {
    "gate_design": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_design_summary.csv"),
    "ticket_instance_design": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"),
    "schema_design": Path("data/vol_targeted_growth_non_submitting_ticket_schema_design_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

EXPECTED_INPUTS = {
    "gate_design": ("final_pre_ticket_gate_design_decision", "FRESH_BROKER_PRE_TICKET_GATE_DESIGNED_NOT_RUN"),
    "ticket_instance_design": ("final_ticket_instance_design_decision", "NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES"),
    "schema_design": ("final_schema_design_decision", "NON_SUBMITTING_TICKET_SCHEMA_DESIGNED_NO_TICKET_CREATED"),
    "go_no_go_dashboard": ("final_go_no_go_decision", "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "run_readiness_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "readonly_alpaca_check_run": False,
    "readonly_alpaca_run_approved": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "fresh_broker_pre_ticket_gate_run": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "order_instructions_created": False,
    "order_values_populated": False,
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

REPORT_COLUMNS = [
    "readiness_item",
    "status",
    "risk_level",
    "details",
    "safety_boundary",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
CHECK_COLUMNS = [
    "readiness_check",
    "expected_value",
    "actual_value",
    "status",
    "failure_behavior",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthFreshBrokerPreTicketGateRunReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    check_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthFreshBrokerPreTicketGateRunReadinessResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    check_rows = build_check_rows(inputs)
    ready = all(row["status"] == "pass" for row in check_rows)
    report_rows = build_report_rows(ready, check_rows)
    summary_rows = build_summary_rows(ready, check_rows)
    blocker_rows = build_blocker_rows(check_rows, ready)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["checks"], CHECK_COLUMNS, check_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthFreshBrokerPreTicketGateRunReadinessResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        check_rows=check_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted fresh broker pre-ticket gate run-readiness report is missing.",
            "Run `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted fresh broker pre-ticket gate run-readiness saved display. Readiness only; broker check not run.",
        f"final_pre_ticket_gate_run_readiness_status: {summary_value(rows, 'final_pre_ticket_gate_run_readiness_status')}",
        f"final_pre_ticket_gate_run_readiness_decision: {summary_value(rows, 'final_pre_ticket_gate_run_readiness_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"readiness_pass_count: {summary_value(rows, 'readiness_pass_count')}",
        f"readiness_blocker_count: {summary_value(rows, 'readiness_blocker_count')}",
        f"ready_to_request_readonly_approval: {summary_value(rows, 'ready_to_request_readonly_approval')}",
        f"readonly_alpaca_run_approved: {summary_value(rows, 'readonly_alpaca_run_approved')}",
        f"fresh_broker_pre_ticket_gate_run: {summary_value(rows, 'fresh_broker_pre_ticket_gate_run')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "alpaca_called=false; broker_positions_read=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: readiness only; it may allow asking for explicit read-only approval later, but does not approve or run that broker check.",
    ]


def build_check_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, (field, expected) in EXPECTED_INPUTS.items():
        actual = summary_value(inputs[name], field)
        status = "pass" if actual == expected else "blocked"
        rows.append(
            check_row(
                f"{name}_{field}",
                expected,
                actual or "missing_saved_output",
                status,
                "block_manual_review",
            )
        )
    rows.extend(
        [
            check_row("future_prompt_must_explicitly_confirm_readonly_alpaca", "required", "required", "pass", "block_manual_review"),
            check_row("gate_run_must_not_create_orders", "required", "required", "pass", "block_manual_review"),
            check_row("gate_run_must_not_populate_order_values", "required", "required", "pass", "block_manual_review"),
            check_row("gate_run_must_not_approve_execution_or_scheduling", "required", "required", "pass", "block_manual_review"),
        ]
    )
    return rows


def build_report_rows(ready: bool, check_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    final_status = "ready_to_request_manual_readonly_approval" if ready else "blocked_manual_review_required"
    return [
        report_row("saved_design_chain", final_status, "high", f"{count_status(check_rows, 'pass')} checks passed; {count_status(check_rows, 'blocked')} blocked.", "Saved reports only; no broker read.", "review_readiness_before_future_prompt"),
        report_row("future_approval_boundary", "manual_review_required", "critical", "A separate future prompt must explicitly approve the read-only Alpaca pre-ticket gate run.", "This report does not approve or run Alpaca.", "ask_user_only_after_readiness_review"),
        report_row("order_boundary", "blocked", "critical", "No ticket values, order side, order quantity, order type, or execution command may be created by this readiness report.", "No order instructions exist.", "keep_order_values_blank"),
    ]


def build_summary_rows(ready: bool, check_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pass_count = count_status(check_rows, "pass")
    blocked_count = count_status(check_rows, "blocked")
    final_status = FINAL_STATUS_READY if ready else FINAL_STATUS_BLOCKED
    final_decision = FINAL_DECISION_READY if ready else FINAL_DECISION_BLOCKED
    next_step = NEXT_STEP_READY if ready else NEXT_STEP_BLOCKED
    largest_blocker = "none_ready_to_request_explicit_readonly_approval" if ready else first_blocker(check_rows)
    data = [
        ("final_pre_ticket_gate_run_readiness_status", final_status, "Readiness to request a future explicit read-only broker gate run."),
        ("final_pre_ticket_gate_run_readiness_decision", final_decision, "This decision is not broker-run approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("readiness_pass_count", str(pass_count), "Readiness checks passed."),
        ("readiness_blocker_count", str(blocked_count), "Readiness checks blocked."),
        ("ready_to_request_readonly_approval", str(ready), "Ready to ask user for separate explicit read-only approval."),
        ("readonly_alpaca_run_approved", "False", "This report does not approve the broker run."),
        ("fresh_broker_pre_ticket_gate_run", "False", "This report does not run the gate."),
        ("broker_positions_read", "False", "This report does not read positions."),
        ("order_values_populated", "False", "No order values are populated."),
        ("largest_blocker", largest_blocker, "Largest blocker or none-ready status."),
        ("recommended_next_step", next_step, "Next manual step."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(check_rows: list[dict[str, Any]], ready: bool) -> list[dict[str, Any]]:
    rows = [
        blocker_row("readonly_alpaca_run_not_approved", "blocked", "critical", "This readiness report does not approve the future read-only Alpaca gate run.", "separate_explicit_prompt_required"),
        blocker_row("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
        blocker_row("order_values_not_approved", "blocked", "critical", "No side, quantity, order type, time-in-force, account, or broker order id may be populated.", "keep_order_fields_blank"),
    ]
    if not ready:
        for row in check_rows:
            if row["status"] != "pass":
                rows.insert(
                    0,
                    blocker_row(
                        str(row["readiness_check"]),
                        "blocked",
                        "high",
                        f"Expected {row['expected_value']} but saw {row['actual_value']}.",
                        "refresh_missing_saved_design_reports",
                    ),
                )
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted fresh broker pre-ticket gate run-readiness complete. Readiness only; broker check not run.",
        f"final_pre_ticket_gate_run_readiness_status={summary_value(summary_rows, 'final_pre_ticket_gate_run_readiness_status')}",
        f"final_pre_ticket_gate_run_readiness_decision={summary_value(summary_rows, 'final_pre_ticket_gate_run_readiness_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"readiness_pass_count={summary_value(summary_rows, 'readiness_pass_count')}",
        f"readiness_blocker_count={summary_value(summary_rows, 'readiness_blocker_count')}",
        f"ready_to_request_readonly_approval={summary_value(summary_rows, 'ready_to_request_readonly_approval')}",
        f"readonly_alpaca_run_approved={summary_value(summary_rows, 'readonly_alpaca_run_approved')}",
        f"fresh_broker_pre_ticket_gate_run={summary_value(summary_rows, 'fresh_broker_pre_ticket_gate_run')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "alpaca_called=false; broker_positions_read=false; order_values_populated=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def check_row(name: str, expected: str, actual: str, status: str, failure: str) -> dict[str, Any]:
    return {
        "readiness_check": name,
        "expected_value": expected,
        "actual_value": actual,
        "status": status,
        "failure_behavior": failure,
        **dict(SAFETY_FLAGS),
    }


def report_row(item: str, status: str, risk: str, details: str, boundary: str, next_step: str) -> dict[str, Any]:
    return {
        "readiness_item": item,
        "status": status,
        "risk_level": risk,
        "details": details,
        "safety_boundary": boundary,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **dict(SAFETY_FLAGS)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def count_status(rows: list[dict[str, Any]], status: str) -> int:
    return sum(1 for row in rows if row.get("status") == status)


def first_blocker(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("status") != "pass":
            return str(row.get("readiness_check", "unknown_blocker"))
    return "none"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
