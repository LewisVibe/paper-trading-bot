"""Approval, saved quantity estimates, and quality gate for volatility seed.

This module stays saved-output/report-only. The calculator creates review share
quantity estimates from saved target-dollar values and saved prices only after a
saved approval record exists. It does not create order instructions, call
Alpaca, submit orders, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
APPROVAL_PHRASE = (
    "I approve calculating saved review-only share quantity estimates from saved "
    "target dollars and saved prices only; do not create order instructions or submit orders."
)
WORDING_STATUS = "vol_targeted_growth_quantity_calculation_approval_wording_manual_review_required"
WORDING_DECISION = "QUANTITY_CALCULATION_APPROVAL_WORDING_DEFINED_NOT_RECORDED"
RECORD_STATUS = "vol_targeted_growth_quantity_calculation_approved_manual_review_required"
RECORD_DECISION = "QUANTITY_CALCULATION_APPROVED_REVIEW_ONLY_NO_ORDER"
CALC_STATUS = "vol_targeted_growth_review_quantity_estimates_created_manual_review_required"
CALC_DECISION = "REVIEW_QUANTITY_ESTIMATES_CREATED_NO_ORDER_INSTRUCTIONS"
QUALITY_STATUS = "vol_targeted_growth_review_quantity_quality_gate_manual_review_required"
QUALITY_DECISION = "REVIEW_QUANTITY_QUALITY_GATE_PASSED_NO_ORDER"
QUALITY_BLOCKED_DECISION = "REVIEW_QUANTITY_QUALITY_GATE_BLOCKED_MANUAL_REVIEW_REQUIRED"
NEXT_APPROVAL = "record_explicit_quantity_calculation_approval_before_estimates"
NEXT_CALC = "calculate_saved_review_quantity_estimates_after_approval"
NEXT_QUALITY = "manual_review_quantity_estimates_before_any_ticket_or_order_discussion"
EXPECTED_SYMBOLS = ["QQQ", "MGK", "IBIT", "SGOV"]

WORDING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_quantity_calculation_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_quantity_calculation_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_quantity_calculation_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_quantity_calculation_approval_wording_evidence.csv"),
}

RECORD_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_quantity_calculation_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_quantity_calculation_approval_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_quantity_calculation_approval_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_quantity_calculation_approval_record_evidence.csv"),
}

CALC_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_review_quantity_estimates.csv"),
    "summary": Path("data/vol_targeted_growth_review_quantity_estimates_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_review_quantity_estimates_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_review_quantity_estimates_evidence.csv"),
}

QUALITY_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_review_quantity_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_review_quantity_quality_gate_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_review_quantity_quality_gate_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_review_quantity_quality_gate_evidence.csv"),
}

INPUT_FILES = {
    "quantity_readiness": Path("data/vol_targeted_growth_quantity_calculation_readiness_summary.csv"),
    "calculated_order_values": Path("data/vol_targeted_growth_calculated_order_values.csv"),
    "calculated_order_values_summary": Path("data/vol_targeted_growth_calculated_order_values_summary.csv"),
    "saved_price_snapshot": Path("data/vol_targeted_growth_saved_price_snapshot.csv"),
    "saved_price_quality_gate": Path("data/vol_targeted_growth_saved_price_snapshot_quality_gate_summary.csv"),
}

CALC_INPUT_FILES = {
    **INPUT_FILES,
    "quantity_approval_record": Path("data/vol_targeted_growth_quantity_calculation_approval_record_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "quantity_calculation_approval_recorded": False,
    "quantity_calculation_approved": False,
    "review_quantities_created": False,
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
QUANTITY_COLUMNS = [
    "sleeve_name",
    "broker_symbol",
    "target_dollars",
    "saved_price",
    "review_share_quantity_estimate",
    "quantity_estimate_status",
    "why_not_order_quantity",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]


@dataclass
class QuantityCheckpointResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_quantity_calculation_approval_wording(root_dir: Path | str = ".") -> QuantityCheckpointResult:
    root = Path(root_dir)
    inputs = load_inputs(root, INPUT_FILES)
    rows = [
        report_row("quantity_calculation_approval_phrase", "approval_wording_defined_not_recorded", "critical", APPROVAL_PHRASE, "Defines wording for review-only quantity estimates.", NEXT_APPROVAL, False, False),
        report_row("execution_boundary", "execution_not_approved", "critical", "orders_submitted=false; execution_approved=false", "The wording cannot become an order.", "keep_execution_blocked", False, False),
    ]
    summary = common_summary(inputs, WORDING_STATUS, WORDING_DECISION, False, False, NEXT_APPROVAL)
    blockers = common_blockers("quantity_calculation_approval_not_recorded", "quantity_calculation_approved=false", NEXT_APPROVAL, False, False)
    evidence = evidence_rows_for(inputs, False, False) + [evidence_row("future_approval_phrase", APPROVAL_PHRASE, "Wording only; no quantities calculated.", False, False)]
    paths = write_checkpoint(root, WORDING_OUTPUTS, rows, summary, blockers, evidence)
    return QuantityCheckpointResult(paths, rows, summary, blockers, evidence, lines("Quantity-calculation approval wording complete. No quantities or orders.", summary, paths["report"], "final_quantity_calculation_wording_status", "final_quantity_calculation_wording_decision"))


def show_vol_targeted_growth_quantity_calculation_approval_wording(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / WORDING_OUTPUTS["summary"], "Volatility-targeted quantity-calculation approval wording display. No quantities or orders.", "final_quantity_calculation_wording_status", "final_quantity_calculation_wording_decision")


def generate_vol_targeted_growth_quantity_calculation_approval_record(root_dir: Path | str = ".") -> QuantityCheckpointResult:
    root = Path(root_dir)
    inputs = load_inputs(root, INPUT_FILES)
    rows = [
        report_row("quantity_calculation_approval_record", "review_quantity_calculation_approved", "critical", APPROVAL_PHRASE, "Approval is limited to saved review quantity estimates.", NEXT_CALC, True, False),
        report_row("order_boundary", "order_instructions_not_approved", "critical", "order_instructions_created=false; orders_submitted=false", "Quantity estimates are not orders.", NEXT_CALC, True, False),
    ]
    summary = common_summary(inputs, RECORD_STATUS, RECORD_DECISION, True, False, NEXT_CALC)
    blockers = common_blockers("order_instructions_not_approved", "quantity_calculation_approved=true; order_instructions_created=false", NEXT_CALC, True, False)
    evidence = evidence_rows_for(inputs, True, False) + [evidence_row("recorded_approval_phrase", APPROVAL_PHRASE, "Approval recorded for review-only estimates; no orders.", True, False)]
    paths = write_checkpoint(root, RECORD_OUTPUTS, rows, summary, blockers, evidence)
    return QuantityCheckpointResult(paths, rows, summary, blockers, evidence, lines("Quantity-calculation approval record complete. Review-only estimates approved; no orders.", summary, paths["report"], "final_quantity_calculation_record_status", "final_quantity_calculation_record_decision"))


def show_vol_targeted_growth_quantity_calculation_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / RECORD_OUTPUTS["summary"], "Volatility-targeted quantity-calculation approval record display. Estimates only; no order approved.", "final_quantity_calculation_record_status", "final_quantity_calculation_record_decision")


def generate_vol_targeted_growth_review_quantity_estimates(root_dir: Path | str = ".") -> QuantityCheckpointResult:
    root = Path(root_dir)
    inputs = load_inputs(root, CALC_INPUT_FILES)
    approved = summary_value(inputs["quantity_approval_record"], "final_quantity_calculation_record_decision") == RECORD_DECISION
    ready = summary_value(inputs["quantity_readiness"], "final_quantity_calculation_readiness_decision") == "READY_TO_REQUEST_QUANTITY_CALCULATION_APPROVAL_NOT_APPROVED"
    quantity_rows = build_quantity_rows(inputs, approved and ready)
    created = approved and ready and bool(quantity_rows) and all(row["quantity_estimate_status"] == "review_quantity_estimate_created" for row in quantity_rows)
    report = [
        report_row("approval_record_present", "pass" if approved else "blocked", "critical", str(approved), "Approval record must exist before estimates.", "record_quantity_calculation_approval", approved, created),
        report_row("readiness_present", "pass" if ready else "blocked", "critical", str(ready), "Readiness checkpoint must be ready.", "refresh_quantity_calculation_readiness", approved, created),
        report_row("order_boundary", "blocked", "critical", "order_instructions_created=false; orders_submitted=false", "Review quantity estimates are not order instructions.", NEXT_QUALITY, approved, created),
    ]
    summary = quantity_summary(inputs, quantity_rows, approved, ready, created)
    blockers = common_blockers("order_instructions_not_approved", "review quantities are not executable order quantities", NEXT_QUALITY, approved, created)
    evidence = evidence_rows_for(inputs, approved, created)
    paths = write_quantity_outputs(root, quantity_rows, report, summary, blockers, evidence)
    return QuantityCheckpointResult(paths, report, summary, blockers, evidence, lines("Review quantity estimates complete. Estimates only; no order instructions.", summary, paths["report"], "final_review_quantity_estimates_status", "final_review_quantity_estimates_decision"))


def show_vol_targeted_growth_review_quantity_estimates(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / CALC_OUTPUTS["summary"], "Volatility-targeted review quantity estimates display. Estimates only; no orders.", "final_review_quantity_estimates_status", "final_review_quantity_estimates_decision")


def generate_vol_targeted_growth_review_quantity_quality_gate(root_dir: Path | str = ".") -> QuantityCheckpointResult:
    root = Path(root_dir)
    inputs = {
        "quantity_estimates": read_csv_rows(root / CALC_OUTPUTS["report"]),
        "quantity_estimates_summary": read_csv_rows(root / CALC_OUTPUTS["summary"]),
    }
    rows = inputs["quantity_estimates"]
    pass_gate = bool(rows) and summary_value(inputs["quantity_estimates_summary"], "final_review_quantity_estimates_decision") == CALC_DECISION and all(
        row.get("quantity_estimate_status") == "review_quantity_estimate_created" and safe_decimal(row.get("review_share_quantity_estimate", "0")) > 0
        for row in rows
    )
    report = [
        report_row("quantity_estimates_present", "pass" if rows else "blocked", "critical", f"rows={len(rows)}", "Saved review quantity estimates must exist.", "refresh_review_quantity_estimates", True, pass_gate),
        report_row("quantity_estimates_positive", "pass" if pass_gate else "blocked", "critical", str(pass_gate), "Every review estimate must be positive.", "refresh_review_quantity_estimates", True, pass_gate),
        report_row("order_boundary", "blocked", "critical", "order_instructions_created=false; orders_submitted=false", "Quality gate does not approve orders.", "manual_review_quantities_before_any_ticket_discussion", True, pass_gate),
    ]
    summary = quantity_quality_summary(inputs, pass_gate)
    blockers = common_blockers("order_instructions_not_approved", "quantity quality gate is not an order approval", "manual_review_quantities_before_any_ticket_discussion", True, pass_gate)
    evidence = [evidence_row("quantity_estimates_input", f"{CALC_OUTPUTS['report']}; rows={len(rows)}", "Saved review quantity row count.", True, pass_gate)]
    paths = write_checkpoint(root, QUALITY_OUTPUTS, report, summary, blockers, evidence)
    return QuantityCheckpointResult(paths, report, summary, blockers, evidence, lines("Review quantity quality gate complete. Quantities remain non-executable.", summary, paths["report"], "final_review_quantity_quality_status", "final_review_quantity_quality_decision"))


def show_vol_targeted_growth_review_quantity_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(Path(root_dir) / QUALITY_OUTPUTS["summary"], "Volatility-targeted review quantity quality gate display. No order approved.", "final_review_quantity_quality_status", "final_review_quantity_quality_decision")


def build_quantity_rows(inputs: dict[str, list[dict[str, str]]], allowed: bool) -> list[dict[str, Any]]:
    prices = {row.get("broker_symbol", "").strip().upper(): safe_decimal(row.get("last_saved_price", "0")) for row in inputs["saved_price_snapshot"]}
    rows = []
    for row in inputs["calculated_order_values"]:
        symbol = row.get("broker_symbol", "").strip().upper()
        if symbol not in EXPECTED_SYMBOLS:
            continue
        target = safe_decimal(row.get("target_dollars", "0"))
        price = prices.get(symbol, Decimal("0"))
        estimate = Decimal("0")
        status = "blocked_missing_approval_or_inputs"
        if allowed and target > 0 and price > 0:
            estimate = (target / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
            status = "review_quantity_estimate_created" if estimate > 0 else "blocked_zero_quantity_estimate"
        rows.append(
            {
                "sleeve_name": row.get("sleeve_name", ""),
                "broker_symbol": symbol,
                "target_dollars": str(target),
                "saved_price": str(price),
                "review_share_quantity_estimate": str(estimate),
                "quantity_estimate_status": status,
                "why_not_order_quantity": "review estimate only; no side, order type, time in force, account, ticket, or submit instruction",
                "required_next_step": NEXT_QUALITY,
                **flags(allowed, allowed and status == "review_quantity_estimate_created"),
            }
        )
    return rows


def common_summary(inputs: dict[str, list[dict[str, str]]], status: str, decision: str, approved: bool, created: bool, next_step: str) -> list[dict[str, Any]]:
    status_key = "final_quantity_calculation_record_status" if approved else "final_quantity_calculation_wording_status"
    decision_key = "final_quantity_calculation_record_decision" if approved else "final_quantity_calculation_wording_decision"
    data = [
        (status_key, status, "Quantity-calculation checkpoint status."),
        (decision_key, decision, "No order, execution, or scheduling approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_phrase", APPROVAL_PHRASE, "Narrow review-quantity approval phrase."),
        ("quantity_readiness_decision", summary_value(inputs["quantity_readiness"], "final_quantity_calculation_readiness_decision") or "missing_quantity_readiness", "Saved readiness context."),
        ("saved_price_quality_gate_passed", summary_value(inputs["saved_price_quality_gate"], "saved_price_snapshot_quality_gate_passed") or "False", "Saved price quality context."),
        ("quantity_calculation_approval_recorded", str(approved), "True only for the approval record."),
        ("quantity_calculation_approved", str(approved), "Approval is limited to review quantity estimates."),
        ("review_quantities_created", str(created), "No estimates are created by approval wording/record."),
        ("order_quantities_calculated", str(created), "True only when the later estimate report creates review quantities."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No buy/sell instruction exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "order_instructions_not_approved", "Quantities are not orders."),
        ("recommended_next_step", next_step, "Manual review remains required."),
    ]
    return [summary_row(*item, approved, created) for item in data]


def quantity_summary(inputs: dict[str, list[dict[str, str]]], quantity_rows: list[dict[str, Any]], approved: bool, ready: bool, created: bool) -> list[dict[str, Any]]:
    total_estimate = sum(safe_decimal(row.get("review_share_quantity_estimate", "0")) for row in quantity_rows)
    data = [
        ("final_review_quantity_estimates_status", CALC_STATUS if created else "vol_targeted_growth_review_quantity_estimates_blocked_manual_review_required", "Review quantity estimate status."),
        ("final_review_quantity_estimates_decision", CALC_DECISION if created else "REVIEW_QUANTITY_ESTIMATES_BLOCKED_MANUAL_REVIEW_REQUIRED", "No order, execution, or scheduling approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("quantity_calculation_approved", str(approved), "Saved approval record present."),
        ("quantity_calculation_readiness_ready", str(ready), "Saved readiness record ready."),
        ("review_quantities_created", str(created), "Review quantities created from saved inputs only."),
        ("review_quantity_row_count", str(len(quantity_rows)), "Number of review quantity rows."),
        ("review_share_quantity_estimate_total", str(total_estimate), "Sum of review estimates only; not an order."),
        ("target_dollar_total", summary_value(inputs["calculated_order_values_summary"], "target_dollar_total") or "missing", "Saved target-dollar total."),
        ("order_quantities_calculated", str(created), "Review quantity estimates only; not broker order quantities."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No buy/sell instruction exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "order_instructions_not_approved", "Quantity estimates are not orders."),
        ("recommended_next_step", NEXT_QUALITY, "Manual review remains required."),
    ]
    return [summary_row(*item, approved, created) for item in data]


def quantity_quality_summary(inputs: dict[str, list[dict[str, str]]], pass_gate: bool) -> list[dict[str, Any]]:
    rows = inputs["quantity_estimates"]
    data = [
        ("final_review_quantity_quality_status", QUALITY_STATUS, "Review quantity quality gate status."),
        ("final_review_quantity_quality_decision", QUALITY_DECISION if pass_gate else QUALITY_BLOCKED_DECISION, "No order, execution, or scheduling approval."),
        ("quantity_calculation_approved", "True", "Quality gate can only run after the estimate chain."),
        ("review_quantities_created", str(pass_gate), "True only when saved review quantities are usable."),
        ("review_quantity_quality_gate_passed", str(pass_gate), "True only means estimates are reviewable."),
        ("review_quantity_row_count", str(len(rows)), "Saved review quantity row count."),
        ("order_quantities_calculated", str(pass_gate), "Review quantity estimates exist only when gate passes."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No buy/sell instruction exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "order_instructions_not_approved", "Quality gate is still not an order."),
        ("recommended_next_step", "manual_review_quantities_before_any_ticket_discussion", "Manual review remains required."),
    ]
    return [summary_row(*item, True, pass_gate) for item in data]


def flags(approved: bool, created: bool) -> dict[str, bool]:
    updated = dict(SAFETY_FLAGS)
    updated["quantity_calculation_approval_recorded"] = approved
    updated["quantity_calculation_approved"] = approved
    updated["review_quantities_created"] = created
    updated["order_quantities_calculated"] = created
    return updated


def common_blockers(name: str, details: str, next_step: str, approved: bool, created: bool) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step, approved, created),
        blocker_row("order_instructions_not_approved", "blocked", "critical", "order_instructions_created=false", "keep_order_instructions_blocked", approved, created),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", approved, created),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", approved, created),
    ]


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]], approved: bool, created: bool) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", approved, created) for name, path in inputs_to_paths(inputs).items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_no_orders", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", approved, created))
    return rows


def inputs_to_paths(inputs: dict[str, list[dict[str, str]]]) -> dict[str, Path]:
    merged = {**CALC_INPUT_FILES, "quantity_estimates": CALC_OUTPUTS["report"], "quantity_estimates_summary": CALC_OUTPUTS["summary"]}
    return {name: merged.get(name, Path(name)) for name in inputs}


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, approved: bool, created: bool) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(approved, created)}


def summary_row(name: str, value: str, details: str, approved: bool, created: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(approved, created)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, approved: bool, created: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(approved, created)}


def evidence_row(name: str, value: str, details: str, approved: bool, created: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(approved, created)}


def load_inputs(root: Path, files: dict[str, Path]) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in files.items()}


def write_checkpoint(root: Path, outputs: dict[str, Path], report: list[dict[str, Any]], summary: list[dict[str, Any]], blockers: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in outputs.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blockers)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence)
    return paths


def write_quantity_outputs(root: Path, quantity_rows: list[dict[str, Any]], report: list[dict[str, Any]], summary: list[dict[str, Any]], blockers: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> dict[str, Path]:
    paths = {name: root / path for name, path in CALC_OUTPUTS.items()}
    write_rows(paths["report"], QUANTITY_COLUMNS, quantity_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blockers)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence)
    return paths


def show_summary(path: Path, title: str, status_key: str, decision_key: str) -> tuple[int, list[str]]:
    if not path.exists():
        return 1, [f"{title} is missing.", "Run the matching report command first.", "execution_approved=false; paper_execution_approved=false; scheduling_approved=false"]
    rows = read_csv_rows(path)
    return 0, [
        title,
        f"{status_key}: {summary_value(rows, status_key)}",
        f"{decision_key}: {summary_value(rows, decision_key)}",
        f"quantity_calculation_approved: {summary_value(rows, 'quantity_calculation_approved')}",
        f"review_quantities_created: {summary_value(rows, 'review_quantities_created')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"order_instructions_created: {summary_value(rows, 'order_instructions_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def lines(title: str, rows: list[dict[str, Any]], path: Path, status_key: str, decision_key: str) -> list[str]:
    return [
        title,
        f"{status_key}={summary_value(rows, status_key)}",
        f"{decision_key}={summary_value(rows, decision_key)}",
        f"quantity_calculation_approved={summary_value(rows, 'quantity_calculation_approved')}",
        f"review_quantities_created={summary_value(rows, 'review_quantities_created')}",
        f"order_quantities_calculated={summary_value(rows, 'order_quantities_calculated')}",
        f"saved_report={path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def safe_decimal(value: str) -> Decimal:
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
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
