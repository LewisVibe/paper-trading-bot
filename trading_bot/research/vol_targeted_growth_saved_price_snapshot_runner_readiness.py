"""Implementation readiness for the future saved-price snapshot runner.

This checkpoint decides whether the saved design evidence is complete enough to
consider implementing a future saved-price snapshot command. It does not
implement or run that command, fetch prices, calculate quantities, or create
order instructions.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
FINAL_STATUS = "vol_targeted_growth_saved_price_snapshot_runner_readiness_manual_review_required"
READY_DECISION = "READY_TO_DISCUSS_SAVED_PRICE_SNAPSHOT_RUNNER_IMPLEMENTATION_NO_PRICE_FETCH"
NOT_READY_DECISION = "NOT_READY_FOR_SAVED_PRICE_SNAPSHOT_RUNNER_IMPLEMENTATION"
NEXT_STEP = "implement_saved_price_snapshot_runner_only_after_explicit_manual_approval"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_saved_price_snapshot_runner_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_saved_price_snapshot_runner_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_saved_price_snapshot_runner_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_saved_price_snapshot_runner_readiness_evidence.csv"),
}

INPUT_FILES = {
    "runner_design": Path("data/vol_targeted_growth_saved_price_snapshot_runner_design_summary.csv"),
    "approval_record": Path("data/vol_targeted_growth_saved_price_snapshot_approval_record_summary.csv"),
    "readiness": Path("data/vol_targeted_growth_saved_price_snapshot_readiness_summary.csv"),
    "calculated_order_values": Path("data/vol_targeted_growth_calculated_order_values_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "runner_implementation_discussion_ready": False,
    "runner_implementation_approved": False,
    "saved_price_snapshot_runner_approved": False,
    "saved_price_snapshot_run_approved": False,
    "saved_price_snapshot_created": False,
    "saved_prices_fetched": False,
    "prices_refreshed": False,
    "price_provider_called": False,
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
class SavedPriceSnapshotRunnerReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_saved_price_snapshot_runner_readiness(
    root_dir: Path | str = ".",
) -> SavedPriceSnapshotRunnerReadinessResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    ready = readiness_state(inputs)
    report_rows = build_report_rows(ready)
    summary_rows = build_summary_rows(inputs, ready)
    blocker_rows = build_blocker_rows(inputs, ready)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return SavedPriceSnapshotRunnerReadinessResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_saved_price_snapshot_runner_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted saved-price snapshot runner readiness is missing.",
            "Run `python bot.py --vol-targeted-growth-saved-price-snapshot-runner-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted saved-price snapshot runner readiness display. Readiness only; no prices fetched.",
        f"final_saved_price_snapshot_runner_readiness_status: {summary_value(rows, 'final_saved_price_snapshot_runner_readiness_status')}",
        f"final_saved_price_snapshot_runner_readiness_decision: {summary_value(rows, 'final_saved_price_snapshot_runner_readiness_decision')}",
        f"runner_implementation_discussion_ready: {summary_value(rows, 'runner_implementation_discussion_ready')}",
        f"runner_implementation_approved: {summary_value(rows, 'runner_implementation_approved')}",
        f"saved_price_snapshot_run_approved: {summary_value(rows, 'saved_price_snapshot_run_approved')}",
        f"saved_prices_fetched: {summary_value(rows, 'saved_prices_fetched')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def readiness_state(inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    design_ok = summary_value(inputs["runner_design"], "final_saved_price_snapshot_runner_design_decision") == "SAVED_PRICE_SNAPSHOT_RUNNER_DESIGNED_NO_PRICE_FETCH"
    approval_ok = summary_value(inputs["approval_record"], "final_saved_price_snapshot_record_decision") == "SAVED_PRICE_SNAPSHOT_METHOD_DISCUSSION_APPROVED_NO_PRICE_FETCH"
    readiness_ok = summary_value(inputs["readiness"], "final_saved_price_snapshot_readiness_decision") == "SAVED_PRICE_SNAPSHOT_NOT_APPROVED_QUANTITIES_BLOCKED"
    calculated_ok = summary_value(inputs["calculated_order_values"], "final_calculated_order_values_decision") == "CALCULATED_TARGET_DOLLARS_CREATED_QUANTITIES_BLOCKED"
    return {
        "ready": design_ok and approval_ok and readiness_ok and calculated_ok,
        "design_ok": design_ok,
        "approval_ok": approval_ok,
        "readiness_ok": readiness_ok,
        "calculated_ok": calculated_ok,
    }


def build_report_rows(ready: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        report_row("runner_design_present", "pass" if ready["design_ok"] else "missing_or_unexpected", "critical", str(ready["design_ok"]), "Runner design must exist before implementation discussion.", "refresh_runner_design"),
        report_row("method_discussion_record_present", "pass" if ready["approval_ok"] else "missing_or_unexpected", "critical", str(ready["approval_ok"]), "Method-discussion record must exist before implementation discussion.", "refresh_saved_price_snapshot_approval_record"),
        report_row("price_readiness_present", "pass" if ready["readiness_ok"] else "missing_or_unexpected", "critical", str(ready["readiness_ok"]), "Saved-price readiness must define required evidence.", "refresh_saved_price_snapshot_readiness"),
        report_row("target_dollars_present", "pass" if ready["calculated_ok"] else "missing_or_unexpected", "critical", str(ready["calculated_ok"]), "Target-dollar checkpoint must exist before price snapshot implementation discussion.", "refresh_calculated_order_values"),
        report_row("implementation_boundary", "blocked", "critical", "runner_implementation_approved=false", "Readiness does not implement or approve the runner.", NEXT_STEP),
        report_row("execution_boundary", "blocked", "critical", "orders_submitted=false; execution_approved=false", "No trading approval exists.", "keep_execution_blocked"),
    ]


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], ready: dict[str, Any]) -> list[dict[str, Any]]:
    decision = READY_DECISION if ready["ready"] else NOT_READY_DECISION
    largest_blocker = "runner_implementation_not_approved" if ready["ready"] else "missing_saved_price_snapshot_prerequisites"
    data = [
        ("final_saved_price_snapshot_runner_readiness_status", FINAL_STATUS, "Implementation readiness review only."),
        ("final_saved_price_snapshot_runner_readiness_decision", decision, "No runner implementation, price fetch, quantity, or order approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("runner_design_decision", summary_value(inputs["runner_design"], "final_saved_price_snapshot_runner_design_decision") or "missing_runner_design", "Saved runner design context."),
        ("approval_record_decision", summary_value(inputs["approval_record"], "final_saved_price_snapshot_record_decision") or "missing_approval_record", "Saved method-discussion context."),
        ("readiness_decision", summary_value(inputs["readiness"], "final_saved_price_snapshot_readiness_decision") or "missing_readiness", "Saved price evidence context."),
        ("calculated_order_values_decision", summary_value(inputs["calculated_order_values"], "final_calculated_order_values_decision") or "missing_calculated_order_values", "Saved target-dollar context."),
        ("runner_implementation_discussion_ready", str(ready["ready"]), "True only means implementation discussion may be considered."),
        ("runner_implementation_approved", "False", "Implementation is not approved."),
        ("saved_price_snapshot_runner_approved", "False", "Runner implementation is not approved."),
        ("saved_price_snapshot_run_approved", "False", "No price snapshot run is approved."),
        ("saved_price_snapshot_created", "False", "No saved price snapshot is created."),
        ("saved_prices_fetched", "False", "No prices are fetched."),
        ("prices_refreshed", "False", "No market data refresh occurs."),
        ("price_provider_called", "False", "No external price provider is called."),
        ("order_quantities_calculated", "False", "No quantities are calculated."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No buy/sell instruction exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", largest_blocker, "Readiness does not approve implementation or a run."),
        ("recommended_next_step", NEXT_STEP, "Separate explicit approval is required before implementation."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]], ready: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("runner_implementation_not_approved", "blocked", "critical", "runner_implementation_approved=false", NEXT_STEP),
        blocker_row("saved_price_snapshot_run_not_approved", "blocked", "critical", "saved_price_snapshot_run_approved=false; saved_prices_fetched=false", "separate_explicit_price_snapshot_run_approval_required"),
        blocker_row("quantity_calculation_not_approved", "blocked", "critical", "order_quantities_calculated=false", "keep_quantities_blocked"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
    ]
    if not ready["ready"]:
        rows.insert(0, blocker_row("saved_price_snapshot_prerequisites_incomplete", "blocked", "high", "One or more saved prerequisite reports are missing or unexpected.", "refresh_saved_prerequisites"))
    for name, value in inputs.items():
        if not value:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input missing: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_no_price_fetch_no_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Saved-price snapshot runner readiness complete. Readiness only; no prices, quantities, or orders.",
        f"final_saved_price_snapshot_runner_readiness_status={summary_value(rows, 'final_saved_price_snapshot_runner_readiness_status')}",
        f"final_saved_price_snapshot_runner_readiness_decision={summary_value(rows, 'final_saved_price_snapshot_runner_readiness_decision')}",
        f"runner_implementation_discussion_ready={summary_value(rows, 'runner_implementation_discussion_ready')}",
        f"runner_implementation_approved={summary_value(rows, 'runner_implementation_approved')}",
        f"saved_price_snapshot_run_approved={summary_value(rows, 'saved_price_snapshot_run_approved')}",
        f"saved_prices_fetched={summary_value(rows, 'saved_prices_fetched')}",
        f"order_quantities_calculated={summary_value(rows, 'order_quantities_calculated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


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
