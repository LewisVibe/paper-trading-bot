"""Guarded saved-price snapshot runner for the volatility seed.

Default mode writes a blocked report and does not fetch prices. A future
confirmed run can fetch yfinance prices for the approved review symbols, but it
still does not calculate quantities, create order instructions, call Alpaca, or
approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
CONFIRM_FLAG = "--confirm-saved-price-snapshot-run"
FINAL_STATUS_BLOCKED = "vol_targeted_growth_saved_price_snapshot_blocked_confirmation_required"
FINAL_STATUS_CREATED = "vol_targeted_growth_saved_price_snapshot_created_manual_review_required"
FINAL_DECISION_BLOCKED = "SAVED_PRICE_SNAPSHOT_NOT_RUN_CONFIRMATION_REQUIRED"
FINAL_DECISION_CREATED = "SAVED_PRICE_SNAPSHOT_CREATED_QUANTITIES_STILL_BLOCKED"
NEXT_STEP_BLOCKED = "explicitly_approve_saved_price_snapshot_run_before_fetching_prices"
NEXT_STEP_CREATED = "manual_review_saved_prices_before_any_quantity_calculation"
REQUIRED_SYMBOLS = ["QQQ", "MGK", "IBIT", "SGOV"]

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_saved_price_snapshot.csv"),
    "summary": Path("data/vol_targeted_growth_saved_price_snapshot_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_saved_price_snapshot_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_saved_price_snapshot_evidence.csv"),
}

INPUT_FILES = {
    "runner_approval_record": Path("data/vol_targeted_growth_saved_price_snapshot_runner_approval_record_summary.csv"),
    "runner_readiness": Path("data/vol_targeted_growth_saved_price_snapshot_runner_readiness_summary.csv"),
    "runner_design": Path("data/vol_targeted_growth_saved_price_snapshot_runner_design_summary.csv"),
}

BASE_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "saved_price_snapshot_created": False,
    "saved_price_snapshot_run_confirmed": False,
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
    "last_saved_price",
    "price_timestamp_utc",
    "price_source",
    "price_status",
    "price_error",
    "required_next_step",
    *BASE_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *BASE_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *BASE_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *BASE_FLAGS.keys()]


@dataclass
class SavedPriceSnapshotResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_saved_price_snapshot(
    root_dir: Path | str = ".",
    *,
    confirm_saved_price_snapshot_run: bool = False,
) -> SavedPriceSnapshotResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    created_at = datetime.now(timezone.utc).isoformat()
    if confirm_saved_price_snapshot_run:
        report_rows = fetch_price_snapshot_rows(root, created_at)
    else:
        report_rows = blocked_report_rows()
    summary_rows = build_summary_rows(inputs, report_rows, confirm_saved_price_snapshot_run)
    blocker_rows = build_blocker_rows(inputs, report_rows, confirm_saved_price_snapshot_run)
    evidence_rows = build_evidence_rows(inputs, confirm_saved_price_snapshot_run)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return SavedPriceSnapshotResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_saved_price_snapshot(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted saved-price snapshot is missing.",
            "Run `python bot.py --vol-targeted-growth-saved-price-snapshot` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted saved-price snapshot display. Prices only if explicitly confirmed; no quantities or orders.",
        f"final_saved_price_snapshot_status: {summary_value(rows, 'final_saved_price_snapshot_status')}",
        f"final_saved_price_snapshot_decision: {summary_value(rows, 'final_saved_price_snapshot_decision')}",
        f"saved_price_snapshot_run_confirmed: {summary_value(rows, 'saved_price_snapshot_run_confirmed')}",
        f"saved_prices_fetched: {summary_value(rows, 'saved_prices_fetched')}",
        f"price_success_count: {summary_value(rows, 'price_success_count')}",
        f"price_error_count: {summary_value(rows, 'price_error_count')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def blocked_report_rows() -> list[dict[str, Any]]:
    return [report_row(symbol, "", "", "not_run", "blocked_confirmation_required", "", NEXT_STEP_BLOCKED, False) for symbol in REQUIRED_SYMBOLS]


def fetch_price_snapshot_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    try:
        from trading_bot.market_data import configure_yfinance_cache_location

        configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    except Exception:
        pass
    try:
        import yfinance as yf
    except Exception as exc:
        return [report_row(symbol, "", "", "yfinance", "price_error", f"yfinance import failed: {type(exc).__name__}", NEXT_STEP_CREATED, True) for symbol in REQUIRED_SYMBOLS]

    rows = []
    for symbol in REQUIRED_SYMBOLS:
        try:
            data = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=False, threads=False)
            price, timestamp = latest_close(data)
            rows.append(report_row(symbol, price, timestamp or created_at, "yfinance_daily_5d", "price_available", "", NEXT_STEP_CREATED, True))
        except Exception as exc:
            rows.append(report_row(symbol, "", "", "yfinance_daily_5d", "price_error", type(exc).__name__, NEXT_STEP_CREATED, True))
    return rows


def latest_close(data: Any) -> tuple[str, str]:
    if data is None or getattr(data, "empty", True):
        raise RuntimeError("no_data_returned")
    close_data = data["Close"]
    if hasattr(close_data, "dropna"):
        close_data = close_data.dropna()
    if getattr(close_data, "empty", True):
        raise RuntimeError("missing_close")
    last_value = close_data.iloc[-1]
    if hasattr(last_value, "iloc"):
        last_value = last_value.iloc[0]
    timestamp = close_data.index[-1]
    return str(round(float(last_value), 6)), str(timestamp)


def report_row(
    symbol: str,
    price: str,
    timestamp: str,
    source: str,
    status: str,
    error: str,
    next_step: str,
    confirmed: bool,
) -> dict[str, Any]:
    return {
        "broker_symbol": symbol,
        "last_saved_price": price,
        "price_timestamp_utc": timestamp,
        "price_source": source,
        "price_status": status,
        "price_error": error,
        "required_next_step": next_step,
        **flags(confirmed),
    }


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    rows: list[dict[str, Any]],
    confirmed: bool,
) -> list[dict[str, Any]]:
    success_count = sum(1 for row in rows if row.get("price_status") == "price_available")
    error_count = sum(1 for row in rows if row.get("price_status") == "price_error")
    blocked_count = sum(1 for row in rows if row.get("price_status") == "blocked_confirmation_required")
    final_status = FINAL_STATUS_CREATED if confirmed else FINAL_STATUS_BLOCKED
    final_decision = FINAL_DECISION_CREATED if confirmed else FINAL_DECISION_BLOCKED
    largest_blocker = "manual_review_saved_prices_before_quantities" if confirmed else "confirmation_required_before_price_fetch"
    next_step = NEXT_STEP_CREATED if confirmed else NEXT_STEP_BLOCKED
    data = [
        ("final_saved_price_snapshot_status", final_status, "Saved price snapshot command status."),
        ("final_saved_price_snapshot_decision", final_decision, "No quantities, order instructions, execution, or scheduling approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("required_symbols", ",".join(REQUIRED_SYMBOLS), "Snapshot symbols."),
        ("runner_approval_decision", summary_value(inputs["runner_approval_record"], "final_saved_price_snapshot_runner_record_decision") or "missing_runner_approval_record", "Saved implementation approval context."),
        ("runner_readiness_decision", summary_value(inputs["runner_readiness"], "final_saved_price_snapshot_runner_readiness_decision") or "missing_runner_readiness", "Saved readiness context."),
        ("runner_design_decision", summary_value(inputs["runner_design"], "final_saved_price_snapshot_runner_design_decision") or "missing_runner_design", "Saved design context."),
        ("saved_price_snapshot_created", str(confirmed), "True only when the explicit confirmation flag is supplied."),
        ("saved_price_snapshot_run_confirmed", str(confirmed), "Requires --confirm-saved-price-snapshot-run."),
        ("saved_prices_fetched", str(confirmed), "True only for a confirmed price snapshot run."),
        ("prices_refreshed", str(confirmed), "True only for a confirmed price snapshot run."),
        ("price_provider_called", str(confirmed), "True only for a confirmed price snapshot run."),
        ("price_success_count", str(success_count), "Rows with price_available."),
        ("price_error_count", str(error_count), "Rows with price_error."),
        ("price_blocked_count", str(blocked_count), "Rows blocked before price fetch."),
        ("order_quantities_calculated", "False", "No quantities are calculated."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No buy/sell instruction exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", largest_blocker, "Snapshot output is still not a quantity or order instruction."),
        ("recommended_next_step", next_step, "Manual review remains required."),
    ]
    return [summary_row(*item, confirmed) for item in data]


def build_blocker_rows(
    inputs: dict[str, list[dict[str, str]]],
    rows: list[dict[str, Any]],
    confirmed: bool,
) -> list[dict[str, Any]]:
    blockers = [
        blocker_row("quantity_calculation_not_approved", "blocked", "critical", "order_quantities_calculated=false", "manual_review_saved_prices_before_quantities", confirmed),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", confirmed),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", confirmed),
    ]
    if not confirmed:
        blockers.insert(0, blocker_row("confirmation_required", "blocked", "critical", f"{CONFIRM_FLAG} not supplied", NEXT_STEP_BLOCKED, confirmed))
    if any(row.get("price_status") == "price_error" for row in rows):
        blockers.insert(0, blocker_row("price_errors_present", "blocked", "critical", "One or more symbols failed price lookup.", "manual_review_price_errors_before_quantities", confirmed))
    for name, value in inputs.items():
        if not value:
            blockers.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Saved input missing: {INPUT_FILES[name]}", f"refresh_{name}_report_only", confirmed))
    return blockers


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], confirmed: bool) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", confirmed)
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("runtime_boundary", "guarded_price_snapshot_no_broker_no_orders_no_quantities", "No Alpaca, config, positions, order, alert, SQLite, or scheduling path is used.", confirmed))
    rows.append(evidence_row("confirmation_flag", CONFIRM_FLAG if confirmed else "not supplied", "Explicit flag required before any price provider call.", confirmed))
    return rows


def flags(confirmed: bool) -> dict[str, bool]:
    updated = dict(BASE_FLAGS)
    updated["saved_price_snapshot_created"] = confirmed
    updated["saved_price_snapshot_run_confirmed"] = confirmed
    updated["saved_prices_fetched"] = confirmed
    updated["prices_refreshed"] = confirmed
    updated["price_provider_called"] = confirmed
    return updated


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Saved-price snapshot command complete. Quantities and orders remain blocked.",
        f"final_saved_price_snapshot_status={summary_value(rows, 'final_saved_price_snapshot_status')}",
        f"final_saved_price_snapshot_decision={summary_value(rows, 'final_saved_price_snapshot_decision')}",
        f"saved_price_snapshot_run_confirmed={summary_value(rows, 'saved_price_snapshot_run_confirmed')}",
        f"saved_prices_fetched={summary_value(rows, 'saved_prices_fetched')}",
        f"price_success_count={summary_value(rows, 'price_success_count')}",
        f"price_error_count={summary_value(rows, 'price_error_count')}",
        f"order_quantities_calculated={summary_value(rows, 'order_quantities_calculated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def summary_row(name: str, value: str, details: str, confirmed: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(confirmed)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, confirmed: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(confirmed)}


def evidence_row(name: str, value: str, details: str, confirmed: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(confirmed)}


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
