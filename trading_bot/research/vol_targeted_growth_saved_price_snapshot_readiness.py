"""Saved-price snapshot readiness for the volatility seed.

This report defines what a future saved price snapshot must provide before
target-dollar review values could become share quantities. It does not fetch
prices, call brokers, or create executable order instructions.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_saved_price_snapshot_readiness_manual_review_required"
FINAL_DECISION = "SAVED_PRICE_SNAPSHOT_NOT_APPROVED_QUANTITIES_BLOCKED"
NEXT_STEP = "manual_review_saved_price_snapshot_method_before_any_price_fetch_or_quantity_calculation"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_saved_price_snapshot_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_saved_price_snapshot_readiness_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_saved_price_snapshot_readiness_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_saved_price_snapshot_readiness_evidence.csv"),
}

INPUT_FILES = {
    "calculated_order_values": Path("data/vol_targeted_growth_calculated_order_values.csv"),
    "calculated_order_values_summary": Path("data/vol_targeted_growth_calculated_order_values_summary.csv"),
    "sleeve_mapping": Path("data/vol_targeted_growth_sleeve_symbol_mapping.csv"),
}

REQUIRED_SYMBOLS = ["QQQ", "MGK", "IBIT", "SGOV"]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "saved_price_snapshot_approved": False,
    "saved_prices_fetched": False,
    "prices_refreshed": False,
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
    "broker_symbol",
    "required_price_field",
    "required_timestamp_field",
    "required_source_field",
    "readiness_status",
    "blocker",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class SavedPriceSnapshotReadinessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_saved_price_snapshot_readiness(
    root_dir: Path | str = ".",
) -> SavedPriceSnapshotReadinessResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    symbols = symbols_from_inputs(inputs)
    report_rows = build_report_rows(symbols)
    summary_rows = build_summary_rows(inputs, report_rows)
    blocker_rows = build_blocker_rows(inputs)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return SavedPriceSnapshotReadinessResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_saved_price_snapshot_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted saved-price snapshot readiness is missing.",
            "Run `python bot.py --vol-targeted-growth-saved-price-snapshot-readiness` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted saved-price snapshot readiness display. No prices fetched; quantities blocked.",
        f"final_saved_price_snapshot_readiness_status: {summary_value(rows, 'final_saved_price_snapshot_readiness_status')}",
        f"final_saved_price_snapshot_readiness_decision: {summary_value(rows, 'final_saved_price_snapshot_readiness_decision')}",
        f"symbols_requiring_saved_prices: {summary_value(rows, 'symbols_requiring_saved_prices')}",
        f"saved_price_snapshot_approved: {summary_value(rows, 'saved_price_snapshot_approved')}",
        f"saved_prices_fetched: {summary_value(rows, 'saved_prices_fetched')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_report_rows(symbols: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "broker_symbol": symbol,
            "required_price_field": "last_saved_price",
            "required_timestamp_field": "price_timestamp_utc",
            "required_source_field": "price_source",
            "readiness_status": "saved_price_required_before_quantity_calculation",
            "blocker": "saved_price_snapshot_not_approved_or_created",
            "required_next_step": NEXT_STEP,
            **SAFETY_FLAGS,
        }
        for symbol in symbols
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    symbols = ",".join(row.get("broker_symbol", "") for row in rows)
    calculated_status = summary_value(
        inputs["calculated_order_values_summary"],
        "final_calculated_order_values_status",
    ) or "missing_calculated_order_values_summary"
    data = [
        ("final_saved_price_snapshot_readiness_status", FINAL_STATUS, "Saved-price snapshot design requires manual review."),
        ("final_saved_price_snapshot_readiness_decision", FINAL_DECISION, "No price fetch or quantity calculation is approved."),
        ("active_seed", ACTIVE_SEED, "Current paper-live candidate seed context."),
        ("symbols_requiring_saved_prices", symbols, "All review symbols need saved prices before quantities."),
        ("calculated_order_values_status", calculated_status, "Saved target-dollar checkpoint status."),
        ("saved_price_snapshot_approved", "False", "No approval exists to fetch or save prices."),
        ("saved_prices_fetched", "False", "This command does not call market data providers."),
        ("prices_refreshed", "False", "No price refresh is performed."),
        ("order_quantities_calculated", "False", "Quantities remain blocked until prices and approval exist."),
        ("broker_ready_order_values_populated", "False", "No executable order values exist."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker id exists."),
        ("order_instructions_created", "False", "No buy/sell instructions exist."),
        ("largest_blocker", "saved_price_snapshot_not_approved_or_created", "Saved prices are still a blocker."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any price fetch or quantity calculation."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row(
            "saved_price_snapshot_not_approved",
            "blocked",
            "critical",
            "No explicit approval exists for a price snapshot run.",
            NEXT_STEP,
        ),
        blocker_row(
            "saved_prices_missing",
            "blocked",
            "critical",
            "No saved last price/timestamp/source fields exist for every review symbol.",
            "design_or_approve_saved_price_snapshot_before_quantity_calculation",
        ),
        blocker_row(
            "final_execution_approval_missing",
            "blocked",
            "critical",
            "execution_approved=false; paper_execution_approved=false",
            "separate_explicit_execution_approval_required",
        ),
    ]
    for name, value in inputs.items():
        if not value:
            rows.insert(
                0,
                blocker_row(
                    f"missing_{name}",
                    "blocked",
                    "high",
                    f"Saved input missing: {INPUT_FILES[name]}",
                    f"refresh_{name}_report_only",
                ),
            )
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(
        evidence_row(
            "runtime_boundary",
            "saved_output_only_no_price_fetch_no_broker_no_market_refresh",
            "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.",
        )
    )
    return rows


def symbols_from_inputs(inputs: dict[str, list[dict[str, str]]]) -> list[str]:
    symbols: list[str] = []
    for row in inputs["calculated_order_values"] or inputs["sleeve_mapping"]:
        symbol = str(row.get("broker_symbol", "")).strip().upper()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols or REQUIRED_SYMBOLS.copy()


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Saved-price snapshot readiness complete. No prices fetched; quantities and orders blocked.",
        f"final_saved_price_snapshot_readiness_status={summary_value(rows, 'final_saved_price_snapshot_readiness_status')}",
        f"final_saved_price_snapshot_readiness_decision={summary_value(rows, 'final_saved_price_snapshot_readiness_decision')}",
        f"symbols_requiring_saved_prices={summary_value(rows, 'symbols_requiring_saved_prices')}",
        f"saved_price_snapshot_approved={summary_value(rows, 'saved_price_snapshot_approved')}",
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
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
