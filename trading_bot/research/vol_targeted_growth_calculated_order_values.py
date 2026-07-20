"""Calculated paper order-value proposal for the volatility seed.

This report turns the real-symbol sleeve proposal into target-dollar review
values. It intentionally does not create executable order values because saved
prices, account value/cash, and final execution approval are not present.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
PROPOSED_REVIEW_NOTIONAL_USD = Decimal("100000.00")
FINAL_STATUS = "vol_targeted_growth_calculated_order_values_created_manual_review_required"
FINAL_DECISION = "CALCULATED_TARGET_DOLLARS_CREATED_QUANTITIES_BLOCKED"
NEXT_STEP = "manual_review_calculated_order_values_before_any_quantity_or_order_approval"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_calculated_order_values.csv"),
    "summary": Path("data/vol_targeted_growth_calculated_order_values_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_calculated_order_values_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_calculated_order_values_evidence.csv"),
}

INPUT_FILES = {
    "sleeve_mapping": Path("data/vol_targeted_growth_sleeve_symbol_mapping.csv"),
    "action_proposal": Path("data/vol_targeted_growth_broker_ready_action_proposal.csv"),
    "action_proposal_summary": Path("data/vol_targeted_growth_broker_ready_action_proposal_summary.csv"),
    "fresh_broker_gate": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "calculated_target_dollars_created": True,
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

REPORT_COLUMNS = [
    "sleeve_name",
    "broker_symbol",
    "target_weight",
    "proposed_review_notional_usd",
    "target_dollars",
    "current_position_quantity_from_saved_broker_context",
    "saved_price_status",
    "proposed_order_side",
    "proposed_order_quantity",
    "order_value_status",
    "blocker",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class CalculatedOrderValuesResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_calculated_order_values(root_dir: Path | str = ".") -> CalculatedOrderValuesResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(inputs, report_rows)
    blocker_rows = build_blocker_rows(inputs)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return CalculatedOrderValuesResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_calculated_order_values(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted calculated order values are missing.",
            "Run `python bot.py --vol-targeted-growth-calculated-order-values` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted calculated order values saved display. Target-dollar math only; no executable quantities.",
        f"final_calculated_order_values_status: {summary_value(rows, 'final_calculated_order_values_status')}",
        f"final_calculated_order_values_decision: {summary_value(rows, 'final_calculated_order_values_decision')}",
        f"proposed_review_notional_usd: {summary_value(rows, 'proposed_review_notional_usd')}",
        f"target_dollar_total: {summary_value(rows, 'target_dollar_total')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    mapping_rows = inputs["sleeve_mapping"]
    if not mapping_rows:
        return [
            report_row(
                "missing_sleeve_mapping",
                "",
                Decimal("0"),
                "",
                "missing_saved_sleeve_mapping",
            )
        ]
    qqq_quantity = summary_value(inputs["fresh_broker_gate"], "qqq_position_quantity_if_readonly") or "unavailable"
    rows = []
    for row in mapping_rows:
        weight = safe_decimal(row.get("target_weight", "0"))
        target_dollars = (PROPOSED_REVIEW_NOTIONAL_USD * weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        current_quantity = qqq_quantity if row.get("broker_symbol") == "QQQ" else "unavailable"
        rows.append(report_row(row.get("sleeve_name", ""), row.get("broker_symbol", ""), weight, current_quantity, "missing_saved_price"))
        rows[-1]["target_dollars"] = str(target_dollars)
    return rows


def report_row(sleeve: str, symbol: str, weight: Decimal, current_quantity: str, price_status: str) -> dict[str, Any]:
    return {
        "sleeve_name": sleeve,
        "broker_symbol": symbol,
        "target_weight": str(weight),
        "proposed_review_notional_usd": str(PROPOSED_REVIEW_NOTIONAL_USD),
        "target_dollars": "0.00",
        "current_position_quantity_from_saved_broker_context": current_quantity,
        "saved_price_status": price_status,
        "proposed_order_side": "",
        "proposed_order_quantity": "",
        "order_value_status": "quantity_blocked_missing_saved_price_and_final_approval",
        "blocker": "saved_price_and_final_approval_required_before_quantity",
        "required_next_step": NEXT_STEP,
        **SAFETY_FLAGS,
    }


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = sum(safe_decimal(row.get("target_dollars", "0")) for row in rows).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    data = [
        ("final_calculated_order_values_status", FINAL_STATUS, "Calculated target-dollar values are available for review."),
        ("final_calculated_order_values_decision", FINAL_DECISION, "Quantities and order instructions remain blocked."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("proposed_review_notional_usd", str(PROPOSED_REVIEW_NOTIONAL_USD), "Conservative review notional only; not approved allocation."),
        ("target_dollar_total", str(total), "Sum of target-dollar review values."),
        ("proposal_row_count", str(len(rows)), "Number of calculated rows."),
        ("broker_symbols", ",".join(row.get("broker_symbol", "") for row in rows), "Symbols from saved mapping."),
        ("fresh_broker_gate_status", summary_value(inputs["fresh_broker_gate"], "final_pre_ticket_gate_run_status") or "missing_fresh_broker_gate", "Saved broker context status."),
        ("qqq_saved_quantity", summary_value(inputs["fresh_broker_gate"], "qqq_position_quantity_if_readonly") or "unavailable", "Saved QQQ quantity if present."),
        ("order_quantities_calculated", "False", "No prices/final approval, so share quantities stay blank."),
        ("broker_ready_order_values_populated", "False", "No executable order values exist."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker id exists."),
        ("order_instructions_created", "False", "No buy/sell instructions exist."),
        ("largest_blocker", "saved_prices_and_final_execution_approval_missing", "Quantities cannot be calculated safely yet."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any quantity or order approval."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("saved_prices_missing", "blocked", "critical", "No saved price evidence exists for all proposal symbols.", "add_saved_price_snapshot_only_after_approval"),
        blocker_row("final_execution_approval_missing", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "separate_explicit_execution_approval_required"),
        blocker_row("order_quantities_not_calculated", "blocked", "critical", "proposed_order_quantity is blank for every row.", "calculate_quantities_only_after_prices_and_approval"),
    ]
    for name, value in inputs.items():
        if not value:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input missing: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Calculated order values complete. Target-dollar math only; quantities and orders blocked.",
        f"final_calculated_order_values_status={summary_value(rows, 'final_calculated_order_values_status')}",
        f"final_calculated_order_values_decision={summary_value(rows, 'final_calculated_order_values_decision')}",
        f"proposed_review_notional_usd={summary_value(rows, 'proposed_review_notional_usd')}",
        f"target_dollar_total={summary_value(rows, 'target_dollar_total')}",
        f"order_quantities_calculated={summary_value(rows, 'order_quantities_calculated')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def safe_decimal(value: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


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
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
