"""Quantity-calculation readiness for the volatility seed.

This checkpoint reads saved target-dollar values and the saved-price snapshot
quality gate. It decides whether a future quantity-calculation approval request
is ready for manual review. It does not calculate share quantities, create
order instructions, call Alpaca, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
READY_STATUS = "vol_targeted_growth_quantity_calculation_readiness_ready_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_quantity_calculation_readiness_blocked_manual_review_required"
READY_DECISION = "READY_TO_REQUEST_QUANTITY_CALCULATION_APPROVAL_NOT_APPROVED"
BLOCKED_DECISION = "NOT_READY_FOR_QUANTITY_CALCULATION_APPROVAL"
NEXT_STEP_READY = "request_explicit_quantity_calculation_approval_record"
NEXT_STEP_BLOCKED = "refresh_saved_price_quality_and_target_dollar_context_before_quantity_request"
EXPECTED_SYMBOLS = ["QQQ", "MGK", "IBIT", "SGOV"]

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_quantity_calculation_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_quantity_calculation_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_quantity_calculation_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_quantity_calculation_readiness_evidence.csv"),
}

INPUT_FILES = {
    "calculated_order_values": Path("data/vol_targeted_growth_calculated_order_values.csv"),
    "calculated_order_values_summary": Path("data/vol_targeted_growth_calculated_order_values_summary.csv"),
    "saved_price_snapshot": Path("data/vol_targeted_growth_saved_price_snapshot.csv"),
    "saved_price_quality_gate": Path("data/vol_targeted_growth_saved_price_snapshot_quality_gate_summary.csv"),
    "run_approval_record": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_record_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "quantity_calculation_discussion_ready": False,
    "quantity_calculation_approved": False,
    "order_quantities_calculated": False,
    "broker_ready_order_values_populated": False,
    "order_values_populated": False,
    "order_instructions_created": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
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
class QuantityCalculationReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_quantity_calculation_readiness(
    root_dir: Path | str = ".",
) -> QuantityCalculationReadinessResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    state = readiness_state(inputs)
    report_rows = build_report_rows(state)
    summary_rows = build_summary_rows(inputs, state)
    blocker_rows = build_blocker_rows(inputs, state)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return QuantityCalculationReadinessResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_quantity_calculation_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted quantity-calculation readiness is missing.",
            "Run `python bot.py --vol-targeted-growth-quantity-calculation-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted quantity-calculation readiness display. Readiness only; no share quantities or orders.",
        f"final_quantity_calculation_readiness_status: {summary_value(rows, 'final_quantity_calculation_readiness_status')}",
        f"final_quantity_calculation_readiness_decision: {summary_value(rows, 'final_quantity_calculation_readiness_decision')}",
        f"quantity_calculation_discussion_ready: {summary_value(rows, 'quantity_calculation_discussion_ready')}",
        f"quantity_calculation_approved: {summary_value(rows, 'quantity_calculation_approved')}",
        f"saved_price_quality_gate_passed: {summary_value(rows, 'saved_price_quality_gate_passed')}",
        f"target_dollar_total: {summary_value(rows, 'target_dollar_total')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def readiness_state(inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    target_rows = inputs["calculated_order_values"]
    target_summary = inputs["calculated_order_values_summary"]
    price_rows = inputs["saved_price_snapshot"]
    quality_rows = inputs["saved_price_quality_gate"]
    symbols = sorted({row.get("broker_symbol", "").strip().upper() for row in target_rows if row.get("broker_symbol")})
    price_symbols = sorted({row.get("broker_symbol", "").strip().upper() for row in price_rows if row.get("broker_symbol")})
    target_context_ok = summary_value(target_summary, "final_calculated_order_values_decision") == "CALCULATED_TARGET_DOLLARS_CREATED_QUANTITIES_BLOCKED"
    target_rows_ok = all(symbol in symbols for symbol in EXPECTED_SYMBOLS)
    target_dollars_ok = all(safe_float(row.get("target_dollars", "")) > 0 for row in target_rows if row.get("broker_symbol", "").strip().upper() in EXPECTED_SYMBOLS)
    price_quality_ok = summary_value(quality_rows, "saved_price_snapshot_quality_gate_passed") == "True"
    price_rows_ok = all(symbol in price_symbols for symbol in EXPECTED_SYMBOLS)
    order_qty_blank = all(not row.get("proposed_order_quantity", "").strip() for row in target_rows)
    ready = target_context_ok and target_rows_ok and target_dollars_ok and price_quality_ok and price_rows_ok and order_qty_blank
    return {
        "ready": ready,
        "target_context_ok": target_context_ok,
        "target_rows_ok": target_rows_ok,
        "target_dollars_ok": target_dollars_ok,
        "price_quality_ok": price_quality_ok,
        "price_rows_ok": price_rows_ok,
        "order_qty_blank": order_qty_blank,
        "symbols": symbols,
        "price_symbols": price_symbols,
    }


def build_report_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        report_row("target_dollar_context", pass_fail(state["target_context_ok"]), "critical", str(state["target_context_ok"]), "Target-dollar review values must exist first.", "refresh_calculated_order_values", state),
        report_row("target_rows_present", pass_fail(state["target_rows_ok"]), "critical", ",".join(state["symbols"]), "Expected broker symbols must be present in target-dollar values.", "refresh_calculated_order_values", state),
        report_row("target_dollars_positive", pass_fail(state["target_dollars_ok"]), "critical", str(state["target_dollars_ok"]), "Each expected symbol needs a positive target-dollar value.", "refresh_calculated_order_values", state),
        report_row("saved_price_quality_gate", pass_fail(state["price_quality_ok"]), "critical", str(state["price_quality_ok"]), "Saved price quality gate must pass before quantity approval can be requested.", "refresh_saved_price_snapshot_quality_gate", state),
        report_row("saved_price_rows_present", pass_fail(state["price_rows_ok"]), "critical", ",".join(state["price_symbols"]), "Expected broker symbols must be present in saved prices.", "refresh_confirmed_saved_price_snapshot", state),
        report_row("quantity_boundary", pass_fail(state["order_qty_blank"]), "critical", str(state["order_qty_blank"]), "This readiness checkpoint must not contain calculated share quantities.", "keep_quantities_blank_until_explicit_approval", state),
        report_row("execution_boundary", "blocked", "critical", "orders_submitted=false; execution_approved=false; paper_execution_approved=false", "Readiness is not an execution approval.", "keep_execution_blocked", state),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], state: dict[str, Any]) -> list[dict[str, Any]]:
    decision = READY_DECISION if state["ready"] else BLOCKED_DECISION
    status = READY_STATUS if state["ready"] else BLOCKED_STATUS
    next_step = NEXT_STEP_READY if state["ready"] else NEXT_STEP_BLOCKED
    largest = "quantity_calculation_approval_not_recorded" if state["ready"] else largest_blocker(state)
    data = [
        ("final_quantity_calculation_readiness_status", status, "Quantity-calculation readiness status."),
        ("final_quantity_calculation_readiness_decision", decision, "No share quantity, order, execution, or scheduling approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("quantity_calculation_discussion_ready", str(state["ready"]), "True only means approval discussion can be requested."),
        ("quantity_calculation_approved", "False", "No quantity-calculation approval exists."),
        ("calculated_order_values_decision", summary_value(inputs["calculated_order_values_summary"], "final_calculated_order_values_decision") or "missing_calculated_order_values_summary", "Saved target-dollar context."),
        ("saved_price_quality_decision", summary_value(inputs["saved_price_quality_gate"], "final_saved_price_snapshot_quality_decision") or "missing_saved_price_quality_gate", "Saved price quality context."),
        ("saved_price_quality_gate_passed", summary_value(inputs["saved_price_quality_gate"], "saved_price_snapshot_quality_gate_passed") or "False", "Saved price quality gate result."),
        ("run_approval_decision", summary_value(inputs["run_approval_record"], "final_saved_price_snapshot_run_record_decision") or "missing_run_approval_record", "Saved price run approval context."),
        ("target_dollar_total", summary_value(inputs["calculated_order_values_summary"], "target_dollar_total") or "missing", "Target-dollar total from saved report."),
        ("target_symbol_count", str(len(state["symbols"])), "Symbols in target-dollar rows."),
        ("saved_price_symbol_count", str(len(state["price_symbols"])), "Symbols in saved price rows."),
        ("order_quantities_calculated", "False", "No share quantities are calculated."),
        ("broker_ready_order_values_populated", "False", "No broker-ready values are populated."),
        ("order_values_populated", "False", "No executable order values exist."),
        ("order_instructions_created", "False", "No buy/sell instructions exist."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", largest, "Readiness does not approve quantities or orders."),
        ("recommended_next_step", next_step, "Manual review remains required."),
    ]
    return [summary_row(*item, state) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]], state: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("quantity_calculation_not_approved", "blocked", "critical", "quantity_calculation_approved=false; order_quantities_calculated=false", NEXT_STEP_READY if state["ready"] else NEXT_STEP_BLOCKED, state),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", state),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", state),
    ]
    for name, value in inputs.items():
        if not value:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input missing: {INPUT_FILES[name]}", f"refresh_{name}_report_only", state))
    if not state["price_quality_ok"]:
        rows.insert(0, blocker_row("saved_price_quality_gate_not_passed", "blocked", "critical", "saved_price_snapshot_quality_gate_passed is not True", "refresh_saved_price_snapshot_quality_gate", state))
    if not state["target_context_ok"]:
        rows.insert(0, blocker_row("target_dollar_context_not_ready", "blocked", "critical", "calculated target-dollar context missing or unexpected", "refresh_calculated_order_values", state))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    state = {"ready": False}
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", state) for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_price_fetch_no_broker_no_orders", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", state))
    return rows


def flags(state: dict[str, Any]) -> dict[str, bool]:
    updated = dict(SAFETY_FLAGS)
    updated["quantity_calculation_discussion_ready"] = bool(state.get("ready"))
    return updated


def largest_blocker(state: dict[str, Any]) -> str:
    if not state["target_context_ok"]:
        return "target_dollar_context_not_ready"
    if not state["target_rows_ok"]:
        return "target_symbol_rows_missing"
    if not state["target_dollars_ok"]:
        return "target_dollars_missing_or_non_positive"
    if not state["price_quality_ok"]:
        return "saved_price_quality_gate_not_passed"
    if not state["price_rows_ok"]:
        return "saved_price_symbols_missing"
    if not state["order_qty_blank"]:
        return "unexpected_quantity_values_present"
    return "quantity_calculation_approval_not_recorded"


def pass_fail(value: bool) -> str:
    return "pass" if value else "blocked"


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, state: dict[str, Any]) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(state)}


def summary_row(name: str, value: str, details: str, state: dict[str, Any]) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(state)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, state: dict[str, Any]) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(state)}


def evidence_row(name: str, value: str, details: str, state: dict[str, Any]) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(state)}


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Quantity-calculation readiness complete. Readiness only; no share quantities or orders.",
        f"final_quantity_calculation_readiness_status={summary_value(rows, 'final_quantity_calculation_readiness_status')}",
        f"final_quantity_calculation_readiness_decision={summary_value(rows, 'final_quantity_calculation_readiness_decision')}",
        f"quantity_calculation_discussion_ready={summary_value(rows, 'quantity_calculation_discussion_ready')}",
        f"quantity_calculation_approved={summary_value(rows, 'quantity_calculation_approved')}",
        f"saved_price_quality_gate_passed={summary_value(rows, 'saved_price_quality_gate_passed')}",
        f"target_dollar_total={summary_value(rows, 'target_dollar_total')}",
        f"order_quantities_calculated={summary_value(rows, 'order_quantities_calculated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def safe_float(value: str) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


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
