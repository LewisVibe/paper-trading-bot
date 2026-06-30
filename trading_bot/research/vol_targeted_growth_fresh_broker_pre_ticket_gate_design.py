"""Fresh broker pre-ticket gate design for the volatility seed.

This report documents the gate that must exist before any future ticket
instance can be populated from fresh broker context. It does not run the gate,
call Alpaca, read positions, populate order values, create tickets, submit
orders, schedule anything, or approve execution.
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
FINAL_STATUS = "vol_targeted_growth_fresh_broker_pre_ticket_gate_design_created_manual_review_required"
FINAL_DECISION = "FRESH_BROKER_PRE_TICKET_GATE_DESIGNED_NOT_RUN"
NEXT_STEP = "manual_review_fresh_broker_pre_ticket_gate_design_before_any_readonly_broker_run"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_design.csv"),
    "summary": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_design_summary.csv"),
    "checks": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_design_checks.csv"),
    "blockers": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_design_blockers.csv"),
}

INPUT_FILES = {
    "ticket_instance_design": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"),
    "schema_design": Path("data/vol_targeted_growth_non_submitting_ticket_schema_design_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
    "saved_broker_comparison": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "gate_design_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "readonly_alpaca_check_run": False,
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
    "design_item",
    "status",
    "risk_level",
    "design_detail",
    "safety_boundary",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
CHECK_COLUMNS = [
    "gate_check",
    "required_status",
    "current_design_status",
    "failure_behavior",
    "safety_note",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthFreshBrokerPreTicketGateDesignResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    check_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_design(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthFreshBrokerPreTicketGateDesignResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(inputs)
    check_rows = build_check_rows(inputs)
    blocker_rows = build_blocker_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["checks"], CHECK_COLUMNS, check_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthFreshBrokerPreTicketGateDesignResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        check_rows=check_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_fresh_broker_pre_ticket_gate_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted fresh broker pre-ticket gate design is missing.",
            "Run `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-design` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted fresh broker pre-ticket gate design saved display. Design only; broker check not run.",
        f"final_pre_ticket_gate_design_status: {summary_value(rows, 'final_pre_ticket_gate_design_status')}",
        f"final_pre_ticket_gate_design_decision: {summary_value(rows, 'final_pre_ticket_gate_design_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"gate_check_count: {summary_value(rows, 'gate_check_count')}",
        f"fresh_broker_pre_ticket_gate_run: {summary_value(rows, 'fresh_broker_pre_ticket_gate_run')}",
        f"readonly_alpaca_check_run: {summary_value(rows, 'readonly_alpaca_check_run')}",
        f"broker_positions_read: {summary_value(rows, 'broker_positions_read')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "alpaca_called=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: gate design only; no Alpaca, broker read, ticket population, order, live trading, or scheduling approval.",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    ticket_decision = summary_value(inputs["ticket_instance_design"], "final_ticket_instance_design_decision") or "missing_ticket_instance_design_summary"
    broker_status = summary_value(inputs["saved_broker_comparison"], "final_comparison_status") or "missing_saved_broker_comparison_summary"
    go_no_go = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard"
    return [
        design_row("scope", "designed_for_review", "high", f"Pre-ticket gate is scoped only to {ACTIVE_SEED}.", "No other strategy or sleeve is made executable.", "manual_review_gate_scope"),
        design_row("ticket_instance_context", "manual_review_required", "high", ticket_decision, "Ticket-instance design remains non-submitting and has no order values.", "review_ticket_instance_before_gate_run"),
        design_row("fresh_broker_check_boundary", "designed_not_run", "critical", "Future gate would require a separate explicit read-only Alpaca confirmation before broker positions are read.", "This design does not call Alpaca or read positions.", "separate_explicit_readonly_alpaca_prompt_required"),
        design_row("saved_broker_context", "manual_review_required", "high", broker_status, "Saved broker comparison may be stale and cannot populate tickets.", "require_fresh_broker_check_later"),
        design_row("go_no_go_context", "blocked", "critical", go_no_go, "Current go/no-go remains monitor-only/no-go.", "keep_execution_blocked"),
        design_row("failure_behavior", "designed_for_review", "critical", "Unknown, stale, mismatched, or unavailable broker state must block/manual-review.", "Never silently assume flat or aligned.", "add_future_gate_tests_before_running"),
    ]


def build_check_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    ticket_status = summary_value(inputs["ticket_instance_design"], "final_ticket_instance_design_status") or "missing_ticket_instance_design_summary"
    return [
        check_row("explicit_readonly_confirmation", "required_before_run", "not_run", "block_manual_review", "No broker read may happen without explicit future confirmation."),
        check_row("repo_safety_and_command_inventory", "pass_before_run", "design_only", "block_manual_review", "Run safety verifiers before any future read-only broker gate."),
        check_row("ticket_instance_design_present", "required_before_run", ticket_status, "block_manual_review", "Ticket-instance design must exist but stay non-executable."),
        check_row("fresh_broker_position_read", "required_when_run", "not_run", "block_manual_review", "Future run may read positions only after explicit read-only approval."),
        check_row("broker_state_age", "fresh_when_run", "not_evaluated", "block_manual_review", "Stale saved broker context cannot populate ticket fields."),
        check_row("qqq_existing_position_context", "review_required", "not_evaluated", "block_manual_review", "Existing QQQ exposure must remain separate from volatility target review."),
        check_row("sleeve_symbol_mapping", "review_required", "not_evaluated", "block_manual_review", "Sleeve-to-symbol mapping must be reviewed before any order field exists."),
        check_row("order_value_population", "forbidden_in_gate_design", "blocked_blank", "block_manual_review", "Gate design cannot create side, quantity, order type, or time-in-force."),
        check_row("execution_approval", "must_be_false", "false", "block_manual_review", "Gate design is not execution approval."),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    missing_inputs = [name for name, rows in inputs.items() if not rows]
    data = [
        ("final_pre_ticket_gate_design_status", FINAL_STATUS, "Fresh broker pre-ticket gate design is created for manual review."),
        ("final_pre_ticket_gate_design_decision", FINAL_DECISION, "The gate is designed but not run."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("gate_check_count", str(len(build_check_rows(inputs))), "Number of future gate checks documented."),
        ("fresh_broker_pre_ticket_gate_run", "False", "This report does not run the gate."),
        ("readonly_alpaca_check_run", "False", "No read-only Alpaca check is run by this design."),
        ("broker_positions_read", "False", "No broker positions are read by this design."),
        ("ticket_instance_created", "False", "No ticket instance is created."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("order_values_populated", "False", "No order values are populated."),
        ("largest_blocker", "future_explicit_readonly_broker_gate_run_not_approved", "Future read-only broker gate run needs separate approval."),
        ("missing_saved_input_count", str(len(missing_inputs)), "Missing saved input summaries."),
        ("missing_saved_inputs", ";".join(missing_inputs) or "none", "Saved inputs missing from this gate design."),
        ("recommended_next_step", NEXT_STEP, "Manual review this design before any future read-only broker run."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("future_explicit_readonly_broker_gate_run_not_approved", "blocked", "critical", "A future read-only Alpaca broker gate run has not been separately approved.", "separate_explicit_readonly_prompt_required"),
        blocker_row("fresh_broker_state_not_read", "blocked", "critical", "Fresh broker state has not been read by this report.", "run_only_after_explicit_readonly_approval"),
        blocker_row("order_values_not_approved", "blocked", "critical", "No side, quantity, order type, or time-in-force may be populated.", "keep_order_fields_blank"),
        blocker_row("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    for name, path in INPUT_FILES.items():
        if name != "saved_broker_comparison" and not inputs[name]:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted fresh broker pre-ticket gate design complete. Design only; broker check not run.",
        f"final_pre_ticket_gate_design_status={summary_value(summary_rows, 'final_pre_ticket_gate_design_status')}",
        f"final_pre_ticket_gate_design_decision={summary_value(summary_rows, 'final_pre_ticket_gate_design_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"gate_check_count={summary_value(summary_rows, 'gate_check_count')}",
        f"fresh_broker_pre_ticket_gate_run={summary_value(summary_rows, 'fresh_broker_pre_ticket_gate_run')}",
        f"readonly_alpaca_check_run={summary_value(summary_rows, 'readonly_alpaca_check_run')}",
        f"broker_positions_read={summary_value(summary_rows, 'broker_positions_read')}",
        f"order_values_populated={summary_value(summary_rows, 'order_values_populated')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "alpaca_called=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def design_row(name: str, status: str, risk: str, detail: str, boundary: str, next_step: str) -> dict[str, Any]:
    return {
        "design_item": name,
        "status": status,
        "risk_level": risk,
        "design_detail": detail,
        "safety_boundary": boundary,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def check_row(name: str, required: str, current: str, failure: str, note: str) -> dict[str, Any]:
    return {
        "gate_check": name,
        "required_status": required,
        "current_design_status": current,
        "failure_behavior": failure,
        "safety_note": note,
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
