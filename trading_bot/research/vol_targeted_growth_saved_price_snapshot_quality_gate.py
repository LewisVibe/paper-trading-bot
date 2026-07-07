"""Saved-price snapshot quality gate for the volatility seed.

This checkpoint reads the saved price snapshot only. It checks whether prices
look complete enough for manual review before any later quantity discussion. It
does not fetch prices, calculate quantities, create order instructions, call
Alpaca, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
REQUIRED_SYMBOLS = ["QQQ", "MGK", "IBIT", "SGOV"]
MAX_PRICE_AGE_HOURS = 96.0
FINAL_STATUS = "vol_targeted_growth_saved_price_snapshot_quality_gate_manual_review_required"
PASS_DECISION = "SAVED_PRICE_SNAPSHOT_QUALITY_GATE_PASSED_QUANTITIES_STILL_BLOCKED"
BLOCKED_DECISION = "SAVED_PRICE_SNAPSHOT_QUALITY_GATE_BLOCKED_MANUAL_REVIEW_REQUIRED"
NEXT_STEP_PASS = "manual_review_saved_prices_before_any_quantity_calculation"
NEXT_STEP_BLOCKED = "refresh_confirmed_saved_price_snapshot_before_quantity_discussion"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_saved_price_snapshot_quality_gate.csv"),
    "summary": Path("data/vol_targeted_growth_saved_price_snapshot_quality_gate_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_saved_price_snapshot_quality_gate_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_saved_price_snapshot_quality_gate_evidence.csv"),
}

INPUT_FILES = {
    "snapshot": Path("data/vol_targeted_growth_saved_price_snapshot.csv"),
    "snapshot_summary": Path("data/vol_targeted_growth_saved_price_snapshot_summary.csv"),
    "run_approval_record": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_record_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "saved_price_snapshot_quality_gate_passed": False,
    "saved_price_snapshot_present": False,
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
class SavedPriceSnapshotQualityResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_saved_price_snapshot_quality_gate(
    root_dir: Path | str = ".",
) -> SavedPriceSnapshotQualityResult:
    root = Path(root_dir)
    snapshot_rows = read_csv_rows(root / INPUT_FILES["snapshot"])
    snapshot_summary_rows = read_csv_rows(root / INPUT_FILES["snapshot_summary"])
    run_approval_rows = read_csv_rows(root / INPUT_FILES["run_approval_record"])
    assessment = assess_snapshot(snapshot_rows, snapshot_summary_rows, datetime.now(timezone.utc))
    report_rows = build_report_rows(assessment)
    summary_rows = build_summary_rows(assessment, snapshot_summary_rows, run_approval_rows)
    blocker_rows = build_blocker_rows(assessment)
    evidence_rows = build_evidence_rows(snapshot_rows, snapshot_summary_rows, run_approval_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return SavedPriceSnapshotQualityResult(
        output_paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(summary_rows, output_paths["report"]),
    )


def show_vol_targeted_growth_saved_price_snapshot_quality_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted saved-price snapshot quality gate is missing.",
            "Run `python bot.py --vol-targeted-growth-saved-price-snapshot-quality-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted saved-price snapshot quality gate display. Saved prices only; no quantities or orders.",
        f"final_saved_price_snapshot_quality_status: {summary_value(rows, 'final_saved_price_snapshot_quality_status')}",
        f"final_saved_price_snapshot_quality_decision: {summary_value(rows, 'final_saved_price_snapshot_quality_decision')}",
        f"saved_price_snapshot_quality_gate_passed: {summary_value(rows, 'saved_price_snapshot_quality_gate_passed')}",
        f"price_available_count: {summary_value(rows, 'price_available_count')}",
        f"missing_symbol_count: {summary_value(rows, 'missing_symbol_count')}",
        f"price_error_count: {summary_value(rows, 'price_error_count')}",
        f"stale_price_count: {summary_value(rows, 'stale_price_count')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def assess_snapshot(
    snapshot_rows: list[dict[str, str]],
    snapshot_summary_rows: list[dict[str, str]],
    now: datetime,
) -> dict[str, Any]:
    rows_by_symbol = {str(row.get("broker_symbol", "")).strip().upper(): row for row in snapshot_rows if str(row.get("broker_symbol", "")).strip()}
    missing_symbols = [symbol for symbol in REQUIRED_SYMBOLS if symbol not in rows_by_symbol]
    available_symbols: list[str] = []
    error_symbols: list[str] = []
    stale_symbols: list[str] = []
    invalid_price_symbols: list[str] = []
    blocked_symbols: list[str] = []
    ages: list[float] = []

    for symbol in REQUIRED_SYMBOLS:
        row = rows_by_symbol.get(symbol)
        if not row:
            continue
        status = str(row.get("price_status", "")).strip()
        if status == "blocked_confirmation_required":
            blocked_symbols.append(symbol)
            continue
        if status == "price_error":
            error_symbols.append(symbol)
            continue
        if status != "price_available":
            error_symbols.append(symbol)
            continue
        price = parse_float(row.get("last_saved_price", ""))
        if price is None or price <= 0:
            invalid_price_symbols.append(symbol)
            continue
        timestamp = parse_timestamp(row.get("price_timestamp_utc", ""))
        if timestamp is None:
            stale_symbols.append(symbol)
            continue
        age_hours = max((now - timestamp).total_seconds() / 3600.0, 0.0)
        ages.append(age_hours)
        if age_hours > MAX_PRICE_AGE_HOURS:
            stale_symbols.append(symbol)
            continue
        available_symbols.append(symbol)

    run_confirmed = summary_value(snapshot_summary_rows, "saved_price_snapshot_run_confirmed") == "True"
    saved_prices_fetched = summary_value(snapshot_summary_rows, "saved_prices_fetched") == "True"
    passed = (
        bool(snapshot_rows)
        and run_confirmed
        and saved_prices_fetched
        and not missing_symbols
        and not error_symbols
        and not stale_symbols
        and not invalid_price_symbols
        and not blocked_symbols
        and len(available_symbols) == len(REQUIRED_SYMBOLS)
    )
    return {
        "passed": passed,
        "snapshot_present": bool(snapshot_rows),
        "run_confirmed": run_confirmed,
        "saved_prices_fetched": saved_prices_fetched,
        "available_symbols": available_symbols,
        "missing_symbols": missing_symbols,
        "error_symbols": error_symbols,
        "stale_symbols": stale_symbols,
        "invalid_price_symbols": invalid_price_symbols,
        "blocked_symbols": blocked_symbols,
        "oldest_age_hours": round(max(ages), 2) if ages else "",
    }


def build_report_rows(assessment: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        report_row(
            "snapshot_file_present",
            "pass" if assessment["snapshot_present"] else "blocked_missing",
            "critical",
            str(assessment["snapshot_present"]),
            "The saved snapshot CSV must exist before quality review can pass.",
            NEXT_STEP_PASS if assessment["snapshot_present"] else NEXT_STEP_BLOCKED,
            assessment,
        ),
        report_row(
            "snapshot_run_confirmed",
            "pass" if assessment["run_confirmed"] else "blocked_not_confirmed",
            "critical",
            str(assessment["run_confirmed"]),
            "The quality gate needs a confirmed saved-price run, not the default blocked report.",
            NEXT_STEP_PASS if assessment["run_confirmed"] else NEXT_STEP_BLOCKED,
            assessment,
        ),
        report_row(
            "required_symbols_present",
            "pass" if not assessment["missing_symbols"] else "blocked_missing_symbols",
            "critical",
            ",".join(assessment["missing_symbols"]) or "none",
            "All required symbols must be present.",
            NEXT_STEP_PASS if not assessment["missing_symbols"] else NEXT_STEP_BLOCKED,
            assessment,
        ),
        report_row(
            "prices_available",
            "pass" if not assessment["error_symbols"] and not assessment["blocked_symbols"] else "blocked_price_unavailable",
            "critical",
            f"errors={','.join(assessment['error_symbols']) or 'none'}; blocked={','.join(assessment['blocked_symbols']) or 'none'}",
            "Every required symbol must have a saved available price.",
            NEXT_STEP_PASS if not assessment["error_symbols"] and not assessment["blocked_symbols"] else NEXT_STEP_BLOCKED,
            assessment,
        ),
        report_row(
            "prices_fresh",
            "pass" if not assessment["stale_symbols"] else "blocked_stale_prices",
            "high",
            f"stale={','.join(assessment['stale_symbols']) or 'none'}; oldest_age_hours={assessment['oldest_age_hours']}",
            f"Saved prices should be no older than {MAX_PRICE_AGE_HOURS:g} hours for this gate.",
            NEXT_STEP_PASS if not assessment["stale_symbols"] else NEXT_STEP_BLOCKED,
            assessment,
        ),
        report_row(
            "quantity_boundary",
            "blocked",
            "critical",
            "order_quantities_calculated=false",
            "A passing saved-price gate is still not quantity approval.",
            "manual_review_saved_prices_before_any_quantity_calculation",
            assessment,
        ),
        report_row(
            "execution_boundary",
            "blocked",
            "critical",
            "orders_submitted=false; execution_approved=false; paper_execution_approved=false",
            "Saved prices are not orders.",
            "keep_execution_blocked",
            assessment,
        ),
    ]


def build_summary_rows(
    assessment: dict[str, Any],
    snapshot_summary_rows: list[dict[str, str]],
    run_approval_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    decision = PASS_DECISION if assessment["passed"] else BLOCKED_DECISION
    largest_blocker_name = largest_blocker(assessment)
    next_step = NEXT_STEP_PASS if assessment["passed"] else NEXT_STEP_BLOCKED
    data = [
        ("final_saved_price_snapshot_quality_status", FINAL_STATUS, "Saved-price snapshot quality gate status."),
        ("final_saved_price_snapshot_quality_decision", decision, "No quantity, order, execution, or scheduling approval."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("run_approval_decision", summary_value(run_approval_rows, "final_saved_price_snapshot_run_record_decision") or "missing_run_approval_record", "Saved run approval context."),
        ("snapshot_decision", summary_value(snapshot_summary_rows, "final_saved_price_snapshot_decision") or "missing_snapshot_summary", "Saved snapshot context."),
        ("saved_price_snapshot_quality_gate_passed", str(assessment["passed"]), "True only when saved prices are complete and fresh."),
        ("saved_price_snapshot_present", str(assessment["snapshot_present"]), "Whether the snapshot CSV exists and has rows."),
        ("saved_price_snapshot_created", str(assessment["run_confirmed"]), "Mirrors confirmed saved snapshot state."),
        ("saved_prices_fetched", str(assessment["saved_prices_fetched"]), "Mirrors saved snapshot state."),
        ("prices_refreshed", str(assessment["saved_prices_fetched"]), "Saved state only; this gate does not refresh prices."),
        ("price_provider_called", "False", "This quality gate does not call any provider."),
        ("required_symbol_count", str(len(REQUIRED_SYMBOLS)), "Expected symbols."),
        ("price_available_count", str(len(assessment["available_symbols"])), "Required symbols with usable saved prices."),
        ("missing_symbol_count", str(len(assessment["missing_symbols"])), "Required symbols missing from snapshot."),
        ("price_error_count", str(len(assessment["error_symbols"]) + len(assessment["blocked_symbols"]) + len(assessment["invalid_price_symbols"])), "Required symbols without usable saved prices."),
        ("stale_price_count", str(len(assessment["stale_symbols"])), "Required symbols with stale or unparsable timestamps."),
        ("oldest_price_age_hours", str(assessment["oldest_age_hours"]), "Oldest usable saved price age."),
        ("order_quantities_calculated", "False", "No quantities are calculated."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No buy/sell instruction exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", largest_blocker_name, "Quality gate does not approve quantities or orders."),
        ("recommended_next_step", next_step, "Manual review remains required."),
    ]
    return [summary_row(name, value, details, assessment) for name, value, details in data]


def build_blocker_rows(assessment: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("quantity_calculation_not_approved", "blocked", "critical", "order_quantities_calculated=false", "manual_review_saved_prices_before_any_quantity_calculation", assessment),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", assessment),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", assessment),
    ]
    if not assessment["snapshot_present"]:
        rows.insert(0, blocker_row("snapshot_missing", "blocked", "critical", str(INPUT_FILES["snapshot"]), NEXT_STEP_BLOCKED, assessment))
    if assessment["blocked_symbols"]:
        rows.insert(0, blocker_row("snapshot_still_blocked", "blocked", "critical", ",".join(assessment["blocked_symbols"]), NEXT_STEP_BLOCKED, assessment))
    if assessment["missing_symbols"]:
        rows.insert(0, blocker_row("missing_required_symbols", "blocked", "critical", ",".join(assessment["missing_symbols"]), NEXT_STEP_BLOCKED, assessment))
    if assessment["error_symbols"] or assessment["invalid_price_symbols"]:
        rows.insert(0, blocker_row("price_errors_or_invalid_prices", "blocked", "critical", ",".join(assessment["error_symbols"] + assessment["invalid_price_symbols"]), NEXT_STEP_BLOCKED, assessment))
    if assessment["stale_symbols"]:
        rows.insert(0, blocker_row("stale_saved_prices", "blocked", "high", ",".join(assessment["stale_symbols"]), NEXT_STEP_BLOCKED, assessment))
    return rows


def build_evidence_rows(
    snapshot_rows: list[dict[str, str]],
    snapshot_summary_rows: list[dict[str, str]],
    run_approval_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    empty_assessment = {"passed": False, "snapshot_present": bool(snapshot_rows), "run_confirmed": False, "saved_prices_fetched": False}
    return [
        evidence_row("snapshot_input", f"{INPUT_FILES['snapshot']}; rows={len(snapshot_rows)}", "Saved snapshot row count.", empty_assessment),
        evidence_row("snapshot_summary_input", f"{INPUT_FILES['snapshot_summary']}; rows={len(snapshot_summary_rows)}", "Saved snapshot summary row count.", empty_assessment),
        evidence_row("run_approval_input", f"{INPUT_FILES['run_approval_record']}; rows={len(run_approval_rows)}", "Saved run approval row count.", empty_assessment),
        evidence_row("runtime_boundary", "saved_output_only_no_price_fetch_no_broker_no_orders", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", empty_assessment),
    ]


def flags(assessment: dict[str, Any]) -> dict[str, bool]:
    updated = dict(SAFETY_FLAGS)
    updated["saved_price_snapshot_quality_gate_passed"] = bool(assessment["passed"])
    updated["saved_price_snapshot_present"] = bool(assessment["snapshot_present"])
    updated["saved_price_snapshot_created"] = bool(assessment["run_confirmed"])
    updated["saved_prices_fetched"] = bool(assessment["saved_prices_fetched"])
    updated["prices_refreshed"] = bool(assessment["saved_prices_fetched"])
    return updated


def largest_blocker(assessment: dict[str, Any]) -> str:
    if not assessment["snapshot_present"]:
        return "saved_price_snapshot_missing"
    if not assessment["run_confirmed"]:
        return "saved_price_snapshot_not_confirmed"
    if assessment["missing_symbols"]:
        return "missing_required_symbols"
    if assessment["blocked_symbols"]:
        return "snapshot_still_blocked_confirmation_required"
    if assessment["error_symbols"] or assessment["invalid_price_symbols"]:
        return "price_errors_or_invalid_prices"
    if assessment["stale_symbols"]:
        return "stale_saved_prices"
    return "quantities_and_execution_still_blocked"


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, assessment: dict[str, Any]) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(assessment)}


def summary_row(name: str, value: str, details: str, assessment: dict[str, Any]) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(assessment)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, assessment: dict[str, Any]) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(assessment)}


def evidence_row(name: str, value: str, details: str, assessment: dict[str, Any]) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(assessment)}


def summary_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Saved-price snapshot quality gate complete. Saved prices only; quantities and orders remain blocked.",
        f"final_saved_price_snapshot_quality_status={summary_value(rows, 'final_saved_price_snapshot_quality_status')}",
        f"final_saved_price_snapshot_quality_decision={summary_value(rows, 'final_saved_price_snapshot_quality_decision')}",
        f"saved_price_snapshot_quality_gate_passed={summary_value(rows, 'saved_price_snapshot_quality_gate_passed')}",
        f"price_available_count={summary_value(rows, 'price_available_count')}",
        f"missing_symbol_count={summary_value(rows, 'missing_symbol_count')}",
        f"price_error_count={summary_value(rows, 'price_error_count')}",
        f"stale_price_count={summary_value(rows, 'stale_price_count')}",
        f"order_quantities_calculated={summary_value(rows, 'order_quantities_calculated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def parse_float(value: str) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def parse_timestamp(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
