"""Read-only fresh broker pre-ticket gate run for the volatility seed.

This command may read Alpaca paper positions only when
--confirm-readonly-alpaca-check is provided. It does not create tickets,
populate order values, submit/cancel/replace orders, write trade logs, send
alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research.vol_targeted_growth_broker_position_comparison import (
    ReadonlyPositionSnapshot,
    load_readonly_broker_positions,
)


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_SEED = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"
CONFIRMED_STATUS = "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_completed_readonly_manual_review_required"
UNCONFIRMED_STATUS = "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_not_run_confirmation_required"
BLOCKED_STATUS = "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_blocked_missing_run_readiness"
FAILED_STATUS = "vol_targeted_growth_fresh_broker_pre_ticket_gate_run_manual_review_required_read_failed"
NEXT_STEP = "manual_review_fresh_broker_pre_ticket_gate_run_before_any_ticket_values_or_order_design"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run.csv"),
    "summary": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_blockers.csv"),
}

INPUT_FILES = {
    "run_readiness": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_summary.csv"),
    "gate_design": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_design_summary.csv"),
    "ticket_instance_design": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "manual_review_only": True,
    "readonly_broker_gate_only": True,
    "alpaca_called": False,
    "alpaca_readonly": False,
    "readonly_alpaca_check_run": False,
    "readonly_alpaca_run_approved": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "fresh_broker_pre_ticket_gate_run": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "order_instructions_created": False,
    "order_values_populated": False,
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
    "created_at",
    "gate_item",
    "status",
    "details",
    "broker_position_read_status",
    "manual_review_label",
    "blocker",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthFreshBrokerPreTicketGateRunResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run(
    root_dir: Path | str = ".",
    *,
    confirm_readonly_alpaca_check: bool = False,
) -> VolTargetedGrowthFreshBrokerPreTicketGateRunResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = load_inputs(root)
    can_run = can_attempt_readonly_run(inputs)
    snapshot = (
        load_readonly_broker_positions(root)
        if confirm_readonly_alpaca_check and can_run
        else unconfirmed_snapshot(confirm_readonly_alpaca_check, can_run)
    )
    final_status = determine_final_status(confirm_readonly_alpaca_check, can_run, snapshot)
    report_rows = build_report_rows(created_at, final_status, snapshot)
    summary_rows = build_summary_rows(inputs, final_status, snapshot, confirm_readonly_alpaca_check)
    evidence_rows = build_evidence_rows(inputs, snapshot, confirm_readonly_alpaca_check)
    blocker_rows = build_blocker_rows(final_status, snapshot, confirm_readonly_alpaca_check, can_run)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthFreshBrokerPreTicketGateRunResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted fresh broker pre-ticket gate run is missing.",
            "Run `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-run --confirm-readonly-alpaca-check` only after explicit approval.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted fresh broker pre-ticket gate run saved display. Read-only/manual-review only.",
        f"final_pre_ticket_gate_run_status: {summary_value(rows, 'final_pre_ticket_gate_run_status')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"readonly_confirmation_status: {summary_value(rows, 'readonly_confirmation_status')}",
        f"broker_position_read_status: {summary_value(rows, 'broker_position_read_status')}",
        f"position_symbol_count_if_readonly: {summary_value(rows, 'position_symbol_count_if_readonly')}",
        f"qqq_position_quantity_if_readonly: {summary_value(rows, 'qqq_position_quantity_if_readonly')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "ticket_instance_created=false; order_values_populated=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: read-only gate context only; no ticket values, orders, live trading, or scheduling approval.",
    ]


def can_attempt_readonly_run(inputs: dict[str, list[dict[str, str]]]) -> bool:
    return (
        summary_value(inputs["run_readiness"], "final_pre_ticket_gate_run_readiness_decision")
        == "READY_TO_REQUEST_EXPLICIT_READONLY_ALPACA_APPROVAL"
    )


def determine_final_status(confirm: bool, can_run: bool, snapshot: ReadonlyPositionSnapshot) -> str:
    if not can_run:
        return BLOCKED_STATUS
    if not confirm:
        return UNCONFIRMED_STATUS
    if snapshot.status != "paper_positions_read_readonly":
        return FAILED_STATUS
    return CONFIRMED_STATUS


def unconfirmed_snapshot(confirm: bool, can_run: bool) -> ReadonlyPositionSnapshot:
    if not can_run:
        return ReadonlyPositionSnapshot(status="blocked_missing_run_readiness", positions_by_symbol={})
    if not confirm:
        return ReadonlyPositionSnapshot(status="readonly_confirmation_missing", positions_by_symbol={})
    return ReadonlyPositionSnapshot(status="readonly_check_not_attempted", positions_by_symbol={})


def build_report_rows(created_at: str, final_status: str, snapshot: ReadonlyPositionSnapshot) -> list[dict[str, Any]]:
    qqq_quantity = snapshot.positions_by_symbol.get("QQQ", "") if snapshot.status == "paper_positions_read_readonly" else ""
    return [
        report_row(created_at, "readonly_broker_position_context", final_status, f"positions_seen={len(snapshot.positions_by_symbol)}; qqq_quantity={qqq_quantity or 'unavailable'}", snapshot),
        report_row(created_at, "ticket_population_boundary", "blocked", "Ticket values remain blank even after broker context is read.", snapshot),
        report_row(created_at, "execution_boundary", "blocked", "No execution, paper execution, repeat order, or scheduling is approved.", snapshot),
    ]


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    final_status: str,
    snapshot: ReadonlyPositionSnapshot,
    confirm: bool,
) -> list[dict[str, Any]]:
    qqq_quantity = snapshot.positions_by_symbol.get("QQQ", "") if snapshot.status == "paper_positions_read_readonly" else ""
    rows = [
        ("final_pre_ticket_gate_run_status", final_status, "Read-only pre-ticket gate run status."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("readonly_confirmation_status", "confirmed" if confirm else "missing", "Whether explicit read-only confirmation was provided."),
        ("broker_position_read_status", snapshot.status, "Broker-position read status."),
        ("source_run_readiness_decision", summary_value(inputs["run_readiness"], "final_pre_ticket_gate_run_readiness_decision") or "missing_run_readiness_decision", "Saved run-readiness decision."),
        ("position_symbol_count_if_readonly", str(len(snapshot.positions_by_symbol)), "Number of paper position symbols seen if read-only check completed."),
        ("qqq_position_quantity_if_readonly", qqq_quantity or "unavailable", "QQQ paper quantity if visible in read-only positions."),
        ("ticket_instance_created", "False", "No ticket instance is created."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("order_values_populated", "False", "No side, quantity, order type, time-in-force, account, or broker order id is populated."),
        ("largest_blocker", largest_blocker(final_status, snapshot), "Primary blocker or manual-review item."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any ticket values or order design."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **flags_for_snapshot(snapshot)} for n, v, d in rows]


def build_evidence_rows(
    inputs: dict[str, list[dict[str, str]]],
    snapshot: ReadonlyPositionSnapshot,
    confirm: bool,
) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("readonly_confirmation_flag", str(confirm).lower(), "Broker reads require explicit confirmation."))
    rows.append(("broker_read_error_type", snapshot.error_type or "none", snapshot.details or "No error details."))
    rows.append(("broker_position_symbols_seen", str(len(snapshot.positions_by_symbol)), "Count only; no account IDs or broker order IDs."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **flags_for_snapshot(snapshot)} for n, v, d in rows]


def build_blocker_rows(
    final_status: str,
    snapshot: ReadonlyPositionSnapshot,
    confirm: bool,
    can_run: bool,
) -> list[dict[str, Any]]:
    rows = [
        ("ticket_values_not_approved", "blocked", "critical", "No side, quantity, order type, time-in-force, account, or broker order id may be populated.", "separate_ticket_value_design_required"),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
        ("order_submission_not_allowed", "blocked", "critical", "This gate cannot create, submit, cancel, or replace orders.", "keep_order_gateway_disconnected"),
    ]
    if not can_run:
        rows.insert(0, ("missing_run_readiness", "blocked", "critical", "Saved run-readiness checkpoint is missing or not ready.", "run_readiness_checkpoint_first"))
    elif not confirm:
        rows.insert(0, ("readonly_confirmation_missing", "blocked", "critical", "--confirm-readonly-alpaca-check was not provided.", "rerun_only_after_explicit_manual_readonly_approval"))
    elif snapshot.status != "paper_positions_read_readonly":
        rows.insert(0, ("readonly_position_read_failed", "blocked", "critical", f"status={snapshot.status}; error_type={snapshot.error_type or 'none'}", "manual_review_required_for_readonly_broker_failure"))
    return [
        {"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **flags_for_snapshot(snapshot)}
        for n, s, sev, d, ns in rows
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted fresh broker pre-ticket gate run complete. Read-only/manual-review only; no ticket values or execution approved.",
        f"final_pre_ticket_gate_run_status={summary_value(summary_rows, 'final_pre_ticket_gate_run_status')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"readonly_confirmation_status={summary_value(summary_rows, 'readonly_confirmation_status')}",
        f"broker_position_read_status={summary_value(summary_rows, 'broker_position_read_status')}",
        f"position_symbol_count_if_readonly={summary_value(summary_rows, 'position_symbol_count_if_readonly')}",
        f"qqq_position_quantity_if_readonly={summary_value(summary_rows, 'qqq_position_quantity_if_readonly')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "ticket_instance_created=false; order_values_populated=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def report_row(created_at: str, item: str, status: str, details: str, snapshot: ReadonlyPositionSnapshot) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "gate_item": item,
        "status": status,
        "details": details,
        "broker_position_read_status": snapshot.status,
        "manual_review_label": "manual_review_required",
        "blocker": largest_blocker(status, snapshot) if status in {BLOCKED_STATUS, UNCONFIRMED_STATUS, FAILED_STATUS} else "ticket_values_not_approved",
        "required_next_step": NEXT_STEP,
        **flags_for_snapshot(snapshot),
    }


def flags_for_snapshot(snapshot: ReadonlyPositionSnapshot) -> dict[str, Any]:
    flags = dict(SAFETY_FLAGS)
    if snapshot.status == "paper_positions_read_readonly":
        flags["alpaca_called"] = True
        flags["alpaca_readonly"] = True
        flags["readonly_alpaca_check_run"] = True
        flags["broker_positions_read"] = True
        flags["paper_positions_read"] = True
        flags["fresh_broker_pre_ticket_gate_run"] = True
    elif snapshot.alpaca_called:
        flags["alpaca_called"] = True
        flags["alpaca_readonly"] = True
        flags["readonly_alpaca_check_run"] = True
    return flags


def largest_blocker(final_status: str, snapshot: ReadonlyPositionSnapshot) -> str:
    if final_status == BLOCKED_STATUS:
        return "missing_run_readiness"
    if final_status == UNCONFIRMED_STATUS:
        return "readonly_confirmation_missing"
    if final_status == FAILED_STATUS or snapshot.status not in {"paper_positions_read_readonly", "readonly_confirmation_missing", "blocked_missing_run_readiness"}:
        return "readonly_position_read_failed"
    return "ticket_values_not_approved_after_readonly_context"


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
