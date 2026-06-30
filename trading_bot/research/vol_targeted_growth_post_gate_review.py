"""Saved-output post-gate review for the volatility seed.

This report interprets the saved fresh broker pre-ticket gate output. It does
not call Alpaca, refresh market data, create ticket values, submit orders, or
approve execution.
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
READY_STATUS = "vol_targeted_growth_post_gate_review_manual_review_required"
MISSING_STATUS = "vol_targeted_growth_post_gate_review_missing_fresh_broker_context"
READY_DECISION = "FRESH_BROKER_CONTEXT_SAVED_TICKET_VALUES_NOT_APPROVED"
MISSING_DECISION = "FRESH_BROKER_CONTEXT_MISSING_MANUAL_REVIEW_REQUIRED"
NEXT_STEP = "manual_review_post_gate_context_before_any_ticket_values_or_order_design"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_post_gate_review.csv"),
    "summary": Path("data/vol_targeted_growth_post_gate_review_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_post_gate_review_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_post_gate_review_evidence.csv"),
}

INPUT_FILES = {
    "fresh_broker_gate_run": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv"),
    "fresh_broker_gate_readiness": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_summary.csv"),
    "ticket_instance_design": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
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

REPORT_COLUMNS = [
    "check_name",
    "status",
    "risk_level",
    "evidence",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthPostGateReviewResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_post_gate_review(root_dir: Path | str = ".") -> VolTargetedGrowthPostGateReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_report_rows(context)
    summary_rows = build_summary_rows(context, report_rows)
    blocker_rows = build_blocker_rows(context, inputs)
    evidence_rows = build_evidence_rows(inputs, context)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return VolTargetedGrowthPostGateReviewResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_post_gate_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted post-gate review is missing.",
            "Run `python bot.py --vol-targeted-growth-post-gate-review` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted post-gate review saved display. Saved-output only; no execution approved.",
        f"final_post_gate_review_status: {summary_value(rows, 'final_post_gate_review_status')}",
        f"final_post_gate_review_decision: {summary_value(rows, 'final_post_gate_review_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"fresh_broker_context_status: {summary_value(rows, 'fresh_broker_context_status')}",
        f"saved_broker_position_read_status: {summary_value(rows, 'saved_broker_position_read_status')}",
        f"saved_position_symbol_count_if_readonly: {summary_value(rows, 'saved_position_symbol_count_if_readonly')}",
        f"saved_qqq_position_quantity_if_readonly: {summary_value(rows, 'saved_qqq_position_quantity_if_readonly')}",
        f"ticket_values_review_status: {summary_value(rows, 'ticket_values_review_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_values_populated=false; order_instructions_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: saved broker context is review evidence only; it is not a ticket or order approval.",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    gate_rows = inputs["fresh_broker_gate_run"]
    gate_status = summary_value(gate_rows, "final_pre_ticket_gate_run_status")
    read_status = summary_value(gate_rows, "broker_position_read_status")
    qqq_quantity = summary_value(gate_rows, "qqq_position_quantity_if_readonly")
    symbol_count = summary_value(gate_rows, "position_symbol_count_if_readonly")
    context_present = (
        gate_status == "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_completed_readonly_manual_review_required"
        and read_status == "paper_positions_read_readonly"
    )
    return {
        "context_present": str(context_present),
        "final_status": READY_STATUS if context_present else MISSING_STATUS,
        "final_decision": READY_DECISION if context_present else MISSING_DECISION,
        "fresh_broker_context_status": "fresh_broker_context_saved_for_manual_review" if context_present else "fresh_broker_context_missing_or_incomplete",
        "saved_broker_position_read_status": read_status or "missing_saved_broker_position_read_status",
        "saved_position_symbol_count_if_readonly": symbol_count or "unavailable",
        "saved_qqq_position_quantity_if_readonly": qqq_quantity or "unavailable",
        "ticket_values_review_status": "ticket_values_not_approved_after_readonly_context",
        "largest_blocker": "ticket_values_not_approved_after_readonly_context" if context_present else "missing_fresh_broker_pre_ticket_gate_run",
        "recommended_next_step": NEXT_STEP if context_present else "run_fresh_broker_pre_ticket_gate_only_after_explicit_readonly_approval",
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    context_present = context["context_present"] == "True"
    return [
        report_row(
            "saved_fresh_broker_context",
            "present_manual_review_required" if context_present else "missing_manual_review_required",
            "high",
            context["saved_broker_position_read_status"],
            "Saved broker context may inform review but cannot approve ticket values.",
            context["recommended_next_step"],
        ),
        report_row(
            "saved_qqq_position_context",
            "qqq_quantity_saved" if context["saved_qqq_position_quantity_if_readonly"] != "unavailable" else "qqq_quantity_unavailable",
            "high",
            context["saved_qqq_position_quantity_if_readonly"],
            "QQQ context remains previous-seed/reference context, not a repeat-order approval.",
            context["recommended_next_step"],
        ),
        report_row(
            "ticket_values_boundary",
            "blocked",
            "critical",
            context["ticket_values_review_status"],
            "No side, quantity, order type, time-in-force, account field, broker order id, or executable ticket exists.",
            "separate_manual_ticket_value_design_required",
        ),
        report_row(
            "execution_boundary",
            "blocked",
            "critical",
            "all_approval_flags_false",
            "No execution, paper execution, live trading, repeat order, or scheduling is approved.",
            "keep_all_approval_flags_false",
        ),
    ]


def build_summary_rows(context: dict[str, str], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_post_gate_review_status", context["final_status"], "Saved-output post-gate review status."),
        ("final_post_gate_review_decision", context["final_decision"], "Decision remains review-only."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("fresh_broker_context_status", context["fresh_broker_context_status"], "Fresh broker context availability from saved gate output."),
        ("saved_broker_position_read_status", context["saved_broker_position_read_status"], "Saved broker-position read status from prior approved gate run."),
        ("saved_position_symbol_count_if_readonly", context["saved_position_symbol_count_if_readonly"], "Saved paper-position symbol count from prior approved gate run."),
        ("saved_qqq_position_quantity_if_readonly", context["saved_qqq_position_quantity_if_readonly"], "Saved QQQ quantity from prior approved gate run."),
        ("ticket_values_review_status", context["ticket_values_review_status"], "Ticket values remain blocked."),
        ("ticket_instance_created", "False", "No ticket instance is created."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("order_values_populated", "False", "No order values are populated."),
        ("largest_blocker", context["largest_blocker"], "Primary blocker after saved broker context review."),
        ("recommended_next_step", context["recommended_next_step"], "Manual review before any future ticket values or order design."),
        ("post_gate_review_row_count", str(len(report_rows)), "Saved report row count."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("ticket_values_not_approved", "blocked", "critical", "Fresh broker context does not approve side/quantity/order fields.", "separate_manual_ticket_value_design_required"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if context["context_present"] != "True":
        rows.insert(0, ("missing_fresh_broker_context", "blocked", "critical", "Saved fresh broker pre-ticket gate run is missing or incomplete.", "run_fresh_broker_pre_ticket_gate_only_after_explicit_readonly_approval"))
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(0, (f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return [blocker_row(*item) for item in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        (f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.extend(
        [
            ("saved_broker_position_read_status", context["saved_broker_position_read_status"], "Read from saved gate-run summary only."),
            ("saved_qqq_position_quantity_if_readonly", context["saved_qqq_position_quantity_if_readonly"], "Read from saved gate-run summary only."),
            ("runtime_boundary", "saved_output_only_no_broker_read", "This review does not call Alpaca or read live positions."),
        ]
    )
    return [evidence_row(*item) for item in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted post-gate review complete. Saved-output only; no ticket values or execution approved.",
        f"final_post_gate_review_status={summary_value(summary_rows, 'final_post_gate_review_status')}",
        f"final_post_gate_review_decision={summary_value(summary_rows, 'final_post_gate_review_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"fresh_broker_context_status={summary_value(summary_rows, 'fresh_broker_context_status')}",
        f"saved_broker_position_read_status={summary_value(summary_rows, 'saved_broker_position_read_status')}",
        f"saved_qqq_position_quantity_if_readonly={summary_value(summary_rows, 'saved_qqq_position_quantity_if_readonly')}",
        f"ticket_values_review_status={summary_value(summary_rows, 'ticket_values_review_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "order_values_populated=false; order_instructions_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
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
