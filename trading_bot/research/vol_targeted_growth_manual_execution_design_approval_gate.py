"""Saved-output manual execution-design approval gate for the volatility seed.

This gate defines what a future explicit human approval would need to say
before executable ticket design could be discussed. It does not record that
approval, create ticket fields, call Alpaca, schedule anything, or approve
execution.
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
FINAL_STATUS = "vol_targeted_growth_manual_execution_design_approval_gate_not_approved"
FINAL_DECISION = "MANUAL_EXECUTION_DESIGN_APPROVAL_NOT_RECORDED"
NEXT_STEP = "user_must_explicitly_approve_execution_design_in_future_prompt_before_ticket_design"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_manual_execution_design_approval_gate.csv"),
    "summary": Path("data/vol_targeted_growth_manual_execution_design_approval_gate_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_manual_execution_design_approval_gate_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_manual_execution_design_approval_gate_blockers.csv"),
}

INPUT_FILES = {
    "gap_list": Path("data/vol_targeted_growth_executable_ticket_gap_list_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
    "execution_blocker_rollup": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "order_side_created": False,
    "order_quantity_created": False,
    "order_type_created": False,
    "time_in_force_created": False,
    "executable_ticket_created": False,
    "executable_ticket_design_allowed": False,
    "manual_execution_design_approved": False,
    "manual_execution_design_approval_recorded": False,
    "paper_live_candidate_approved": False,
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
    "gate_item",
    "status",
    "severity",
    "requirement",
    "current_state",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthManualExecutionDesignApprovalGateResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_manual_execution_design_approval_gate(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthManualExecutionDesignApprovalGateResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(inputs, report_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(report_rows, inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthManualExecutionDesignApprovalGateResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_manual_execution_design_approval_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted manual execution-design approval gate is missing.",
            "Run `python bot.py --vol-targeted-growth-manual-execution-design-approval-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted manual execution-design approval gate saved display. Report only; approval not recorded.",
        f"final_approval_gate_status: {summary_value(rows, 'final_approval_gate_status')}",
        f"final_approval_gate_decision: {summary_value(rows, 'final_approval_gate_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"explicit_future_prompt_required: {summary_value(rows, 'explicit_future_prompt_required')}",
        f"required_phrase: {summary_value(rows, 'required_phrase')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "manual_execution_design_approved=false; executable_ticket_design_allowed=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this gate defines future approval wording only; it does not approve ticket design, orders, live trading, or scheduling.",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    gap_decision = summary_value(inputs["gap_list"], "final_ticket_design_decision") or "missing_gap_list_summary"
    go_no_go = summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard"
    rollup_status = summary_value(inputs["execution_blocker_rollup"], "final_execution_blocker_rollup_status") or "missing_execution_blocker_rollup"
    return [
        gate_row(
            "explicit_future_prompt_required",
            "not_satisfied",
            "critical",
            "Future prompt must explicitly approve designing an executable ticket for this exact active seed.",
            "No such approval is recorded by this report.",
            NEXT_STEP,
        ),
        gate_row(
            "scope_must_name_active_seed",
            "not_satisfied",
            "critical",
            f"Prompt must name {ACTIVE_SEED} / {ACTIVE_TICKER}.",
            f"Current report only documents the requirement; active_seed={ACTIVE_SEED}.",
            "future_approval_must_name_active_seed_and_ticker",
        ),
        gate_row(
            "approval_must_be_design_only",
            "not_satisfied",
            "critical",
            "Future approval may only allow design of a non-submitting ticket layer, not order submission.",
            "No design or order approval exists.",
            "keep_any_future_design_non_submitting_until_separate_order_approval",
        ),
        gate_row(
            "gap_list_must_be_reviewed",
            "not_satisfied",
            "critical",
            "Gap list must be reviewed and either accepted or superseded before ticket design.",
            gap_decision,
            "manual_review_gap_list_before_design_approval",
        ),
        gate_row(
            "go_no_go_must_change_from_no_go",
            "not_satisfied",
            "critical",
            "Go/no-go dashboard must not remain no-go if ticket design is to proceed.",
            go_no_go,
            "manual_review_go_no_go_dashboard_before_design_approval",
        ),
        gate_row(
            "blocker_rollup_must_be_reviewed",
            "not_satisfied",
            "critical",
            "Execution blocker rollup must be reviewed before design approval.",
            rollup_status,
            "manual_review_blocker_rollup_before_design_approval",
        ),
        gate_row(
            "fresh_readonly_broker_state_still_required",
            "not_satisfied",
            "critical",
            "Any future ticket design would need a fresh read-only broker comparison with explicit approval.",
            "broker_positions_read=false; alpaca_called=false",
            "run_readonly_broker_check_only_after_separate_user_approval",
        ),
        gate_row(
            "order_capable_scheduling_remains_forbidden",
            "satisfied_boundary",
            "critical",
            "Future approval must not schedule order-capable commands.",
            "scheduling_approved=false; never_schedule_order_capable_commands=true",
            "keep_order_capable_commands_unscheduled",
        ),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unsatisfied = sum(1 for row in report_rows if row.get("status") == "not_satisfied")
    missing_inputs = [name for name, rows in inputs.items() if not rows]
    data = [
        ("final_approval_gate_status", FINAL_STATUS, "Manual execution-design approval is not recorded."),
        ("final_approval_gate_decision", FINAL_DECISION, "Ticket design cannot proceed from this report."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("explicit_future_prompt_required", "True", "A future user prompt must explicitly approve execution-design work."),
        (
            "required_phrase",
            "I explicitly approve designing a non-submitting executable ticket layer for higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
            "Suggested minimum future approval phrase; this report does not provide it.",
        ),
        ("approval_gate_item_count", str(len(report_rows)), "Total gate rows."),
        ("unsatisfied_gate_item_count", str(unsatisfied), "Gate rows still not satisfied."),
        ("missing_saved_input_count", str(len(missing_inputs)), "Missing saved input summaries."),
        ("missing_saved_inputs", ";".join(missing_inputs) or "none", "Saved inputs missing from this gate."),
        ("largest_blocker", "explicit_future_prompt_required", "Primary blocker before executable ticket design."),
        ("recommended_next_step", NEXT_STEP, "Only a future explicit prompt can change this state."),
    ]
    return [summary_row(*item) for item in data]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        (f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return [evidence_row(*item) for item in rows]


def build_blocker_rows(
    report_rows: list[dict[str, Any]],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = [
        blocker_row(row["gate_item"], row["status"], row["severity"], row["current_state"], row["required_next_step"])
        for row in report_rows
    ]
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted manual execution-design approval gate complete. Report only; approval not recorded.",
        f"final_approval_gate_status={summary_value(summary_rows, 'final_approval_gate_status')}",
        f"final_approval_gate_decision={summary_value(summary_rows, 'final_approval_gate_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"explicit_future_prompt_required={summary_value(summary_rows, 'explicit_future_prompt_required')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "manual_execution_design_approved=false; executable_ticket_design_allowed=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def gate_row(
    name: str,
    status: str,
    severity: str,
    requirement: str,
    current_state: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "gate_item": name,
        "status": status,
        "severity": severity,
        "requirement": requirement,
        "current_state": current_state,
        "required_next_step": next_step,
        **dict(SAFETY_FLAGS),
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **dict(SAFETY_FLAGS)}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **dict(SAFETY_FLAGS)}


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
