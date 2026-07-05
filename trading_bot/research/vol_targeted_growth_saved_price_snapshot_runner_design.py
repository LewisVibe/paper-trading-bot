"""Saved-price snapshot runner design for the volatility seed.

This checkpoint designs the shape and safety checks for a future saved-price
snapshot command. It does not fetch prices, call market data providers, call
brokers, calculate quantities, or create order instructions.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
FINAL_STATUS = "vol_targeted_growth_saved_price_snapshot_runner_design_created_manual_review_required"
FINAL_DECISION = "SAVED_PRICE_SNAPSHOT_RUNNER_DESIGNED_NO_PRICE_FETCH"
NEXT_STEP = "manual_review_saved_price_snapshot_runner_design_before_any_price_snapshot_run"
REQUIRED_SYMBOLS = ["QQQ", "MGK", "IBIT", "SGOV"]

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_saved_price_snapshot_runner_design.csv"),
    "summary": Path("data/vol_targeted_growth_saved_price_snapshot_runner_design_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_saved_price_snapshot_runner_design_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_saved_price_snapshot_runner_design_evidence.csv"),
}

INPUT_FILES = {
    "approval_record": Path("data/vol_targeted_growth_saved_price_snapshot_approval_record_summary.csv"),
    "readiness": Path("data/vol_targeted_growth_saved_price_snapshot_readiness_summary.csv"),
    "calculated_order_values": Path("data/vol_targeted_growth_calculated_order_values_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "runner_design_created": True,
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

REPORT_COLUMNS = [
    "design_area",
    "status",
    "allowed_future_field_or_rule",
    "forbidden_behavior",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class SavedPriceSnapshotRunnerDesignResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_saved_price_snapshot_runner_design(
    root_dir: Path | str = ".",
) -> SavedPriceSnapshotRunnerDesignResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = build_report_rows()
    summary_rows = build_summary_rows(inputs)
    blocker_rows = build_blocker_rows(inputs)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return SavedPriceSnapshotRunnerDesignResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_saved_price_snapshot_runner_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted saved-price snapshot runner design is missing.",
            "Run `python bot.py --vol-targeted-growth-saved-price-snapshot-runner-design` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted saved-price snapshot runner design display. Design only; no prices fetched.",
        f"final_saved_price_snapshot_runner_design_status: {summary_value(rows, 'final_saved_price_snapshot_runner_design_status')}",
        f"final_saved_price_snapshot_runner_design_decision: {summary_value(rows, 'final_saved_price_snapshot_runner_design_decision')}",
        f"required_symbols: {summary_value(rows, 'required_symbols')}",
        f"runner_design_created: {summary_value(rows, 'runner_design_created')}",
        f"saved_price_snapshot_run_approved: {summary_value(rows, 'saved_price_snapshot_run_approved')}",
        f"saved_prices_fetched: {summary_value(rows, 'saved_prices_fetched')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_report_rows() -> list[dict[str, Any]]:
    rows = [
        design_row("allowed_output_fields", "designed", "broker_symbol,last_saved_price,price_timestamp_utc,price_source,price_status,price_error", "side,quantity,order_type,time_in_force,account_id,order_id,api_key,webhook"),
        design_row("required_symbols", "designed", ",".join(REQUIRED_SYMBOLS), "unknown_symbols_without_manual_review"),
        design_row("stale_price_policy", "designed", "stale_or_missing_prices_block_quantity_calculation", "auto_accept_stale_prices"),
        design_row("provider_failure_policy", "designed", "record_per_symbol_error_and_block_quantities", "silently_default_missing_prices_to_zero"),
        design_row("execution_boundary", "designed", "snapshot_output_is_not_order_instruction", "submit_cancel_replace_or_prepare_orders"),
        design_row("approval_boundary", "designed", "runner_design_only", "treat_design_as_price_fetch_approval"),
    ]
    return rows


def design_row(area: str, status: str, allowed: str, forbidden: str) -> dict[str, Any]:
    return {
        "design_area": area,
        "status": status,
        "allowed_future_field_or_rule": allowed,
        "forbidden_behavior": forbidden,
        "required_next_step": NEXT_STEP,
        **SAFETY_FLAGS,
    }


def build_summary_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    approval_decision = summary_value(inputs["approval_record"], "final_saved_price_snapshot_record_decision") or "missing_saved_price_snapshot_approval_record"
    data = [
        ("final_saved_price_snapshot_runner_design_status", FINAL_STATUS, "Runner design exists for review only."),
        ("final_saved_price_snapshot_runner_design_decision", FINAL_DECISION, "No price fetch, quantity, order, execution, or scheduling approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("required_symbols", ",".join(REQUIRED_SYMBOLS), "Symbols expected for the future snapshot design."),
        ("approval_record_decision", approval_decision, "Method-discussion approval context."),
        ("readiness_decision", summary_value(inputs["readiness"], "final_saved_price_snapshot_readiness_decision") or "missing_saved_price_snapshot_readiness", "Saved-price readiness context."),
        ("calculated_order_values_decision", summary_value(inputs["calculated_order_values"], "final_calculated_order_values_decision") or "missing_calculated_order_values", "Target-dollar context."),
        ("runner_design_created", "True", "A design artifact exists only."),
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
        ("largest_blocker", "saved_price_snapshot_runner_not_approved_or_run", "Runner design does not approve a price fetch."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any snapshot runner implementation or run."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("saved_price_snapshot_runner_not_approved", "blocked", "critical", "saved_price_snapshot_runner_approved=false", NEXT_STEP),
        blocker_row("saved_price_snapshot_run_not_approved", "blocked", "critical", "saved_price_snapshot_run_approved=false; saved_prices_fetched=false", "separate_explicit_price_snapshot_run_approval_required"),
        blocker_row("quantity_calculation_not_approved", "blocked", "critical", "order_quantities_calculated=false", "keep_quantities_blocked_until_saved_prices_and_approval"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
    ]
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
        "Saved-price snapshot runner design complete. Design only; no prices, quantities, or orders.",
        f"final_saved_price_snapshot_runner_design_status={summary_value(rows, 'final_saved_price_snapshot_runner_design_status')}",
        f"final_saved_price_snapshot_runner_design_decision={summary_value(rows, 'final_saved_price_snapshot_runner_design_decision')}",
        f"required_symbols={summary_value(rows, 'required_symbols')}",
        f"runner_design_created={summary_value(rows, 'runner_design_created')}",
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
