"""Narrow manual paper smoke-test gate.

This helper is intentionally limited to the existing ``--paper-order-test`` path.
It evaluates whether the exact AAPL buy 1 manual connectivity smoke test can
proceed past broad strategy-execution blockers. It does not call Alpaca, read
positions, submit orders, write SQLite, send alerts, or approve strategy
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


GATE_TYPE = "manual_connectivity_smoke_test_gate"
ALLOWED_TICKER = "AAPL"
ALLOWED_SIDE = "buy"
ALLOWED_QUANTITY = Decimal("1")
READY_PREFLIGHT_STATUS = "live_preflight_ready_for_manual_confirmation"
OPEN_MARKET_STATUS = "open"
BROKER_CONFIRMED_RECENT_ORDER_STATUSES = {
    "accepted",
    "accepted_for_bidding",
    "calculated",
    "done_for_day",
    "filled",
    "held",
    "new",
    "partially_filled",
    "pending_cancel",
    "pending_new",
    "pending_replace",
    "stopped",
    "suspended",
}
NON_BLOCKING_RECENT_ORDER_STATUSES = {
    "canceled",
    "cancelled",
    "expired",
    "rejected",
    "replaced",
}
UNCERTAIN_DUPLICATE_ORDER_CHECKS = {
    "blocked_duplicate_order_history_uncertain",
    "blocked_ambiguous_recent_matching_order_status",
}

GATE_REPORT_PATH = Path("data/paper_order_smoke_test_gate_report.csv")
GATE_SUMMARY_PATH = Path("data/paper_order_smoke_test_gate_summary.csv")
GATE_BLOCKERS_PATH = Path("data/paper_order_smoke_test_gate_blockers.csv")
LIVE_PREFLIGHT_PATH = Path("data/paper_order_smoke_test_live_preflight.csv")

REPORT_COLUMNS = [
    "gate_type",
    "ticker",
    "side",
    "quantity",
    "gate_status",
    "market_status",
    "live_preflight_status",
    "open_order_check",
    "duplicate_recent_order_check",
    "duplicate_recent_order_source",
    "duplicate_recent_order_status_if_any",
    "current_position_context_ignored_for_duplicate_check",
    "blocker",
    "required_next_step",
    "smoke_test_order_approved",
    "paper_execution_approved",
    "execution_approved",
    "strategy_execution_approved",
    "followup_order_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]
SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "smoke_test_order_approved",
    "paper_execution_approved",
    "execution_approved",
    "strategy_execution_approved",
    "followup_order_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]
BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    "smoke_test_order_approved",
    "paper_execution_approved",
    "execution_approved",
    "strategy_execution_approved",
    "followup_order_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]


@dataclass(frozen=True)
class SavedSmokeTestPreflightContext:
    live_preflight_status: str
    market_status: str
    ticker: str
    side: str
    quantity: str
    open_order_check: str


@dataclass(frozen=True)
class ManualPaperSmokeTestGateDecision:
    allowed: bool
    gate_status: str
    gate_type: str
    ticker: str
    side: str
    quantity: str
    market_status: str
    live_preflight_status: str
    open_order_check: str
    duplicate_recent_order_check: str
    duplicate_recent_order_source: str
    duplicate_recent_order_status_if_any: str
    current_position_context_ignored_for_duplicate_check: bool
    reasons: list[str]
    required_next_step: str
    smoke_test_order_approved: bool
    execution_approved: bool = False
    strategy_execution_approved: bool = False
    scheduling_approved: bool = False
    followup_order_approved: bool = False
    paper_execution_approved: bool = False


def read_saved_smoke_test_preflight_context(
    path: Path = LIVE_PREFLIGHT_PATH,
) -> SavedSmokeTestPreflightContext:
    rows = read_csv_rows(path)
    live_status = ""
    market_status = ""
    ticker = ""
    side = ""
    quantity = ""
    open_order_check = "saved_open_order_context_unavailable"
    for row in rows:
        ticker = ticker or str(row.get("ticker", "")).strip().upper()
        side = side or str(row.get("side", "")).strip().lower()
        quantity = quantity or str(row.get("quantity", "")).strip()
        row_market = str(row.get("market_status", "")).strip().lower()
        if row_market and row_market not in {"unknown", "not_checked"}:
            market_status = row_market
        row_live = str(row.get("live_preflight_status", "")).strip()
        if row_live:
            live_status = row_live
        if row.get("check_name") == "final_live_preflight_status":
            live_status = str(row.get("check_status") or row.get("live_preflight_status") or live_status)
        if row.get("check_name") == "readonly_open_orders_for_ticker":
            status = str(row.get("check_status", "")).strip()
            open_order_check = "pass" if status == "pass" else "open_order_review_required"
    return SavedSmokeTestPreflightContext(
        live_preflight_status=live_status or "saved_live_preflight_missing",
        market_status=market_status or "saved_market_status_missing",
        ticker=ticker,
        side=side,
        quantity=quantity,
        open_order_check=open_order_check,
    )


def evaluate_manual_paper_smoke_test_gate(
    *,
    ticker: str,
    side: str,
    quantity: Decimal,
    confirm_paper_order: bool,
    alpaca_paper: bool,
    allow_shorting: bool,
    credentials_present: bool,
    preflight: SavedSmokeTestPreflightContext,
    direct_open_order_count: int | None = None,
    duplicate_recent_order_check: str | None = None,
    duplicate_recent_order_source: str = "not_checked_yet",
    duplicate_recent_order_status_if_any: str = "",
) -> ManualPaperSmokeTestGateDecision:
    normalized_ticker = ticker.strip().upper()
    normalized_side = side.strip().lower()
    quantity_text = format_quantity(quantity)
    reasons: list[str] = []

    if normalized_ticker != ALLOWED_TICKER:
        reasons.append("ticker must be AAPL for the manual connectivity smoke test")
    if normalized_side != ALLOWED_SIDE:
        reasons.append("side must be buy for the manual connectivity smoke test")
    if quantity != ALLOWED_QUANTITY:
        reasons.append("quantity must be exactly 1 for the manual connectivity smoke test")
    if confirm_paper_order is not True:
        reasons.append("--confirm-paper-order is required")
    if alpaca_paper is not True:
        reasons.append("alpaca.paper must be true")
    if allow_shorting is True:
        reasons.append("allow_shorting must remain false")
    if credentials_present is not True:
        reasons.append("Alpaca paper credentials are required")
    if preflight.live_preflight_status != READY_PREFLIGHT_STATUS:
        reasons.append("saved live preflight status must be ready for manual confirmation")
    if preflight.market_status != OPEN_MARKET_STATUS:
        reasons.append("market_status must be open")
    if preflight.ticker and preflight.ticker != ALLOWED_TICKER:
        reasons.append("saved live preflight ticker must be AAPL")
    if preflight.side and preflight.side != ALLOWED_SIDE:
        reasons.append("saved live preflight side must be buy")
    if preflight.quantity and preflight.quantity != "1":
        reasons.append("saved live preflight quantity must be 1")
    if preflight.open_order_check not in {"pass", "saved_open_order_context_unavailable"}:
        reasons.append("saved live preflight open-order context is not clear")
    if direct_open_order_count is not None and direct_open_order_count > 0:
        reasons.append("an open AAPL order already exists")
    duplicate_check = duplicate_recent_order_check or "not_checked_yet"
    if duplicate_check == "blocked_recent_matching_order_exists":
        reasons.append("a recent matching AAPL buy 1 smoke-test order already exists")
    if duplicate_check == "blocked_duplicate_order_history_uncertain":
        reasons.append("recent matching-order history could not be read from Alpaca paper")
    if duplicate_check == "blocked_ambiguous_recent_matching_order_status":
        reasons.append("a recent matching AAPL buy 1 order has an ambiguous broker status")

    open_order_check = (
        "not_checked_yet"
        if direct_open_order_count is None
        else ("pass" if direct_open_order_count == 0 else "blocked_open_order_exists")
    )
    smoke_test_order_approved = open_order_check == "pass" and duplicate_check == "pass" and not reasons
    if reasons:
        return ManualPaperSmokeTestGateDecision(
            allowed=False,
            gate_status="blocked",
            gate_type=GATE_TYPE,
            ticker=normalized_ticker,
            side=normalized_side,
            quantity=quantity_text,
            market_status=preflight.market_status,
            live_preflight_status=preflight.live_preflight_status,
            open_order_check=open_order_check,
            duplicate_recent_order_check=duplicate_check,
            duplicate_recent_order_source=duplicate_recent_order_source,
            duplicate_recent_order_status_if_any=duplicate_recent_order_status_if_any,
            current_position_context_ignored_for_duplicate_check=True,
            reasons=reasons,
            required_next_step="Keep smoke test blocked until the dedicated manual connectivity gate is reviewed.",
            smoke_test_order_approved=False,
        )
    return ManualPaperSmokeTestGateDecision(
        allowed=True,
        gate_status="allowed",
        gate_type=GATE_TYPE,
        ticker=normalized_ticker,
        side=normalized_side,
        quantity=quantity_text,
        market_status=preflight.market_status,
        live_preflight_status=preflight.live_preflight_status,
        open_order_check=open_order_check,
        duplicate_recent_order_check=duplicate_check,
        duplicate_recent_order_source=duplicate_recent_order_source,
        duplicate_recent_order_status_if_any=duplicate_recent_order_status_if_any,
        current_position_context_ignored_for_duplicate_check=True,
        reasons=["exact AAPL buy 1 manual connectivity smoke-test gate passed"],
        required_next_step="Proceed only with the existing manual --paper-order-test path; this does not approve strategy execution.",
        smoke_test_order_approved=smoke_test_order_approved,
    )


def write_manual_paper_smoke_test_gate_report(
    decision: ManualPaperSmokeTestGateDecision,
    *,
    root_dir: Path | str = ".",
    order_event: str = "no_order_work_started",
) -> None:
    root = Path(root_dir)
    report_row = {
        "gate_type": decision.gate_type,
        "ticker": decision.ticker,
        "side": decision.side,
        "quantity": decision.quantity,
        "gate_status": decision.gate_status,
        "market_status": decision.market_status,
        "live_preflight_status": decision.live_preflight_status,
        "open_order_check": decision.open_order_check,
        "duplicate_recent_order_check": decision.duplicate_recent_order_check,
        "duplicate_recent_order_source": decision.duplicate_recent_order_source,
        "duplicate_recent_order_status_if_any": decision.duplicate_recent_order_status_if_any,
        "current_position_context_ignored_for_duplicate_check": (
            decision.current_position_context_ignored_for_duplicate_check
        ),
        "blocker": "; ".join(decision.reasons) if not decision.allowed else "none_for_manual_connectivity_smoke_test",
        "required_next_step": decision.required_next_step,
        **approval_flags(decision, order_event=order_event),
    }
    summary_rows = [
        summary_row("gate_type", decision.gate_type, "Dedicated gate for the manual AAPL buy 1 smoke test only.", decision, order_event),
        summary_row("gate_status", decision.gate_status, "Gate status for the narrow manual connectivity smoke test.", decision, order_event),
        summary_row("market_status", decision.market_status, "Market status from saved/read-only preflight context.", decision, order_event),
        summary_row("live_preflight_status", decision.live_preflight_status, "Saved live preflight status.", decision, order_event),
        summary_row("open_order_check", decision.open_order_check, "Open-order gate status.", decision, order_event),
        summary_row("duplicate_recent_order_check", decision.duplicate_recent_order_check, "Recent matching-order gate status.", decision, order_event),
        summary_row(
            "duplicate_recent_order_source",
            decision.duplicate_recent_order_source,
            "Source used for the duplicate-order gate.",
            decision,
            order_event,
        ),
        summary_row(
            "duplicate_recent_order_status_if_any",
            decision.duplicate_recent_order_status_if_any or "none",
            "Broker order status that triggered duplicate blocking, if any.",
            decision,
            order_event,
        ),
        summary_row(
            "current_position_context_ignored_for_duplicate_check",
            str(decision.current_position_context_ignored_for_duplicate_check),
            "Existing AAPL position context is not proof of a duplicate broker order.",
            decision,
            order_event,
        ),
        summary_row("smoke_test_order_approved", str(decision.smoke_test_order_approved), "True only for the exact manually confirmed AAPL buy 1 smoke test.", decision, order_event),
        summary_row("execution_approved", "False", "Strategy execution remains blocked.", decision, order_event),
        summary_row("strategy_execution_approved", "False", "No strategy-to-execution approval is granted.", decision, order_event),
        summary_row("scheduling_approved", "False", "Scheduling remains blocked.", decision, order_event),
        summary_row("order_event", order_event, "Order mechanics status for this gate report.", decision, order_event),
    ]
    blocker_rows = [
        blocker_row(reason, "blocked", "critical", reason, decision.required_next_step, decision, order_event)
        for reason in decision.reasons
        if not decision.allowed
    ]
    if decision.allowed:
        blocker_rows = [
            blocker_row(
                "strategy_execution_not_approved",
                "blocked_for_strategy_execution",
                "critical",
                "This gate approves only the exact manual connectivity smoke-test template.",
                "Do not use this gate for any strategy execution path.",
                decision,
                order_event,
            )
        ]
    write_rows(root / GATE_REPORT_PATH, REPORT_COLUMNS, [report_row])
    write_rows(root / GATE_SUMMARY_PATH, SUMMARY_COLUMNS, summary_rows)
    write_rows(root / GATE_BLOCKERS_PATH, BLOCKER_COLUMNS, blocker_rows)


def approval_flags(decision: ManualPaperSmokeTestGateDecision, *, order_event: str) -> dict[str, bool]:
    return {
        "smoke_test_order_approved": decision.smoke_test_order_approved,
        "paper_execution_approved": False,
        "execution_approved": False,
        "strategy_execution_approved": False,
        "followup_order_approved": False,
        "scheduling_approved": False,
        "orders_created": order_event in {"order_submitted"},
        "orders_submitted": order_event in {"order_submitted"},
        "orders_cancelled": False,
        "sqlite_trade_log_written": order_event in {"order_submitted", "order_skipped_after_broker_checks"},
        "discord_alert_sent": order_event in {"order_submitted", "order_skipped_after_broker_checks"},
        "telegram_alert_sent": False,
    }


def summary_row(
    name: str,
    value: str,
    details: str,
    decision: ManualPaperSmokeTestGateDecision,
    order_event: str,
) -> dict[str, Any]:
    return {
        "summary_name": name,
        "summary_value": value,
        "details": details,
        **approval_flags(decision, order_event=order_event),
    }


def blocker_row(
    name: str,
    status: str,
    severity: str,
    details: str,
    next_step: str,
    decision: ManualPaperSmokeTestGateDecision,
    order_event: str,
) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **approval_flags(decision, order_event=order_event),
    }


def format_quantity(quantity: Decimal) -> str:
    if quantity == quantity.to_integral_value():
        return str(int(quantity))
    return f"{quantity.normalize():f}"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
