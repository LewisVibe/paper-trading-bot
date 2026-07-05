"""Run approval wording/record for the guarded saved-price snapshot.

These checkpoints define and record approval to run the guarded saved-price
snapshot in a later explicit command. They do not fetch prices, calculate
quantities, create order instructions, call Alpaca, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
CONFIRM_FLAG = "--confirm-saved-price-snapshot-run"
APPROVAL_PHRASE = (
    "I approve one saved-price snapshot run only; fetch saved prices but do not "
    "calculate quantities, create order instructions, call Alpaca, or approve execution."
)
WORDING_STATUS = "vol_targeted_growth_saved_price_snapshot_run_approval_wording_manual_review_required"
WORDING_DECISION = "SAVED_PRICE_SNAPSHOT_RUN_APPROVAL_WORDING_DEFINED_NOT_RECORDED"
RECORD_STATUS = "vol_targeted_growth_saved_price_snapshot_run_approved_manual_review_required"
RECORD_DECISION = "SAVED_PRICE_SNAPSHOT_RUN_APPROVED_PRICE_ONLY_QUANTITIES_BLOCKED"
NEXT_STEP_WORDING = "wait_for_explicit_saved_price_snapshot_run_approval_record"
NEXT_STEP_RECORD = "run_guarded_saved_price_snapshot_with_confirm_flag_when_ready"

WORDING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_wording.csv"),
    "summary": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_wording_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_wording_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_wording_evidence.csv"),
}

RECORD_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_record_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_record_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_saved_price_snapshot_run_approval_record_evidence.csv"),
}

INPUT_FILES = {
    "runner_approval_record": Path("data/vol_targeted_growth_saved_price_snapshot_runner_approval_record_summary.csv"),
    "runner_default_snapshot": Path("data/vol_targeted_growth_saved_price_snapshot_summary.csv"),
    "runner_readiness": Path("data/vol_targeted_growth_saved_price_snapshot_runner_readiness_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "saved_price_snapshot_run_approval_recorded": False,
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
class SavedPriceSnapshotRunApprovalResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_saved_price_snapshot_run_approval_wording(
    root_dir: Path | str = ".",
) -> SavedPriceSnapshotRunApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        report_row(
            "snapshot_run_approval_phrase",
            "approval_wording_defined_not_recorded",
            "critical",
            APPROVAL_PHRASE,
            "Defines wording for a future saved-price snapshot run only.",
            NEXT_STEP_WORDING,
            False,
        ),
        report_row(
            "execution_boundary",
            "execution_not_approved",
            "critical",
            "order_quantities_calculated=false; execution_approved=false",
            "The wording cannot become an order instruction.",
            "keep_quantities_and_execution_blocked",
            False,
        ),
    ]
    summary_rows = common_summary(inputs, WORDING_STATUS, WORDING_DECISION, False, NEXT_STEP_WORDING)
    blocker_rows = common_blockers("saved_price_snapshot_run_approval_not_recorded", "saved_price_snapshot_run_approved=false", NEXT_STEP_WORDING, False)
    evidence_rows = evidence_rows_for(inputs, False) + [
        evidence_row("future_run_approval_phrase", APPROVAL_PHRASE, "Run approval wording only; no price fetch happens here.", False)
    ]
    paths = write_all(root, WORDING_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return SavedPriceSnapshotRunApprovalResult(
        paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(
            "Saved-price snapshot run approval wording complete. No prices fetched.",
            summary_rows,
            paths["report"],
            "final_saved_price_snapshot_run_wording_status",
            "final_saved_price_snapshot_run_wording_decision",
        ),
    )


def show_vol_targeted_growth_saved_price_snapshot_run_approval_wording(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / WORDING_OUTPUTS["summary"],
        "Volatility-targeted saved-price snapshot run approval wording display. No prices fetched.",
        "final_saved_price_snapshot_run_wording_status",
        "final_saved_price_snapshot_run_wording_decision",
    )


def generate_vol_targeted_growth_saved_price_snapshot_run_approval_record(
    root_dir: Path | str = ".",
) -> SavedPriceSnapshotRunApprovalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [
        report_row(
            "snapshot_run_approval_record",
            "price_snapshot_run_approved_for_future_confirmed_command",
            "critical",
            APPROVAL_PHRASE,
            "Approval is limited to one future saved-price snapshot run.",
            NEXT_STEP_RECORD,
            True,
        ),
        report_row(
            "quantity_boundary",
            "quantity_calculation_not_approved",
            "critical",
            "order_quantities_calculated=false; order_instructions_created=false",
            "Saved prices are not share quantities and are not orders.",
            "manual_review_saved_prices_before_any_quantity_calculation",
            True,
        ),
        report_row(
            "execution_boundary",
            "execution_not_approved",
            "critical",
            "orders_submitted=false; execution_approved=false; paper_execution_approved=false",
            "Execution approval remains separate and false.",
            "keep_execution_blocked",
            True,
        ),
    ]
    summary_rows = common_summary(inputs, RECORD_STATUS, RECORD_DECISION, True, NEXT_STEP_RECORD)
    blocker_rows = common_blockers("quantity_calculation_not_approved", "saved_price_snapshot_run_approved=true; order_quantities_calculated=false", NEXT_STEP_RECORD, True)
    evidence_rows = evidence_rows_for(inputs, True) + [
        evidence_row("recorded_run_approval_phrase", APPROVAL_PHRASE, "Price-only run approval recorded; no prices fetched by this checkpoint.", True),
        evidence_row("future_confirmed_command", f"python bot.py --vol-targeted-growth-saved-price-snapshot {CONFIRM_FLAG}", "This command is not run by the approval record.", True),
    ]
    paths = write_all(root, RECORD_OUTPUTS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return SavedPriceSnapshotRunApprovalResult(
        paths,
        report_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        summary_lines(
            "Saved-price snapshot run approval record complete. Price-only future run approved; no prices fetched here.",
            summary_rows,
            paths["report"],
            "final_saved_price_snapshot_run_record_status",
            "final_saved_price_snapshot_run_record_decision",
        ),
    )


def show_vol_targeted_growth_saved_price_snapshot_run_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / RECORD_OUTPUTS["summary"],
        "Volatility-targeted saved-price snapshot run approval record display. Future price-only run approved; no execution approved.",
        "final_saved_price_snapshot_run_record_status",
        "final_saved_price_snapshot_run_record_decision",
    )


def flags(recorded: bool) -> dict[str, bool]:
    updated = dict(SAFETY_FLAGS)
    updated["saved_price_snapshot_run_approval_recorded"] = recorded
    updated["saved_price_snapshot_run_approved"] = recorded
    return updated


def common_summary(
    inputs: dict[str, list[dict[str, str]]],
    status: str,
    decision: str,
    recorded: bool,
    next_step: str,
) -> list[dict[str, Any]]:
    status_key = "final_saved_price_snapshot_run_record_status" if recorded else "final_saved_price_snapshot_run_wording_status"
    decision_key = "final_saved_price_snapshot_run_record_decision" if recorded else "final_saved_price_snapshot_run_wording_decision"
    data = [
        (status_key, status, "Saved-output run approval checkpoint."),
        (decision_key, decision, "Run approval only; no quantity, order, execution, or scheduling approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Portfolio label only."),
        ("approval_phrase", APPROVAL_PHRASE, "Narrow price-only run phrase."),
        ("runner_approval_decision", summary_value(inputs["runner_approval_record"], "final_saved_price_snapshot_runner_record_decision") or "missing_runner_approval_record", "Saved runner implementation context."),
        ("default_snapshot_decision", summary_value(inputs["runner_default_snapshot"], "final_saved_price_snapshot_decision") or "missing_default_snapshot", "Guarded runner default/no-fetch context."),
        ("runner_readiness_decision", summary_value(inputs["runner_readiness"], "final_saved_price_snapshot_runner_readiness_decision") or "missing_runner_readiness", "Saved runner readiness context."),
        ("saved_price_snapshot_run_approval_recorded", str(recorded), "True only for the record command."),
        ("saved_price_snapshot_run_approved", str(recorded), "Approval is limited to a price-only snapshot run."),
        ("saved_price_snapshot_created", "False", "No saved price snapshot is created by this checkpoint."),
        ("saved_prices_fetched", "False", "No prices are fetched by this checkpoint."),
        ("prices_refreshed", "False", "No market data refresh occurs in this checkpoint."),
        ("price_provider_called", "False", "No external price provider is called by this checkpoint."),
        ("order_quantities_calculated", "False", "No quantities are calculated."),
        ("broker_ready_order_values_populated", "False", "No broker-ready order values are populated."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No buy/sell instruction exists."),
        ("orders_submitted", "False", "No orders are submitted."),
        ("execution_approved", "False", "No execution approval exists."),
        ("paper_execution_approved", "False", "No paper execution approval exists."),
        ("scheduling_approved", "False", "No scheduling approval exists."),
        ("largest_blocker", "quantities_and_execution_still_blocked", "Run approval does not approve quantities or orders."),
        ("recommended_next_step", next_step, "Manual review remains required."),
    ]
    return [summary_row(name, value, details, recorded) for name, value, details in data]


def common_blockers(name: str, details: str, next_step: str, recorded: bool) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", details, next_step, recorded),
        blocker_row("saved_prices_not_fetched_by_checkpoint", "blocked", "high", "saved_prices_fetched=false", next_step, recorded),
        blocker_row("quantity_calculation_not_approved", "blocked", "critical", "order_quantities_calculated=false", "keep_quantities_blocked", recorded),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked", recorded),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled", recorded),
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]], recorded: bool) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.", recorded)
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_no_price_fetch_no_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used.", recorded))
    rows.append(evidence_row("confirmation_boundary", CONFIRM_FLAG, "The actual guarded runner still requires the confirm flag in a separate command.", recorded))
    return rows


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str, recorded: bool) -> dict[str, Any]:
    return {"check_name": name, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **flags(recorded)}


def summary_row(name: str, value: str, details: str, recorded: bool) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flags(recorded)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, recorded: bool) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flags(recorded)}


def evidence_row(name: str, value: str, details: str, recorded: bool) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flags(recorded)}


def write_all(
    root: Path,
    outputs: dict[str, Path],
    report_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    paths = {name: root / path for name, path in outputs.items()}
    write_rows(paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def show_summary(path: Path, title: str, status_key: str, decision_key: str) -> tuple[int, list[str]]:
    if not path.exists():
        return 1, [
            f"{title} is missing.",
            "Run the matching report command first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        title,
        f"{status_key}: {summary_value(rows, status_key)}",
        f"{decision_key}: {summary_value(rows, decision_key)}",
        f"saved_price_snapshot_run_approved: {summary_value(rows, 'saved_price_snapshot_run_approved')}",
        f"saved_prices_fetched: {summary_value(rows, 'saved_prices_fetched')}",
        f"order_quantities_calculated: {summary_value(rows, 'order_quantities_calculated')}",
        f"order_instructions_created: {summary_value(rows, 'order_instructions_created')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def summary_lines(title: str, rows: list[dict[str, Any]], report_path: Path, status_key: str, decision_key: str) -> list[str]:
    return [
        title,
        f"{status_key}={summary_value(rows, status_key)}",
        f"{decision_key}={summary_value(rows, decision_key)}",
        f"saved_price_snapshot_run_approved={summary_value(rows, 'saved_price_snapshot_run_approved')}",
        f"saved_prices_fetched={summary_value(rows, 'saved_prices_fetched')}",
        f"price_provider_called={summary_value(rows, 'price_provider_called')}",
        f"order_quantities_calculated={summary_value(rows, 'order_quantities_calculated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
