"""Narrow QQQ100 paper execution gate and saved-signal helpers.

This module is intentionally scoped to the manually confirmed
``--execute-qqq100-paper --confirm-qqq100-paper`` path. It does not call Alpaca,
submit orders, write SQLite, send alerts, or schedule anything.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from trading_bot.positions import POSITION_FLAT, POSITION_LONG, POSITION_SHORT, Position, format_decimal
from trading_bot.safety.manual_paper_smoke_test_gate import (
    ManualSmokeTestRecentOrderMatch,
    RECENT_ORDER_LOOKBACK_MINUTES,
)


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"
FIXED_QUANTITY = Decimal("1")
SIGNAL_SOURCE = "qqq100_preview_signal_pack"
SAVED_SIGNAL_PATH = Path("data/qqq100_preview_signal_pack.csv")
RESULT_PATH = Path("data/qqq100_paper_execution_result.csv")
SUMMARY_PATH = Path("data/qqq100_paper_execution_summary.csv")
BLOCKERS_PATH = Path("data/qqq100_paper_execution_blockers.csv")

VALID_DESIRED_POSITIONS = {"long", "flat"}

RESULT_COLUMNS = [
    "created_at",
    "strategy_name",
    "ticker",
    "signal_source",
    "desired_position",
    "signal_date",
    "preview_signal_status",
    "current_position_status",
    "current_position_quantity_abs",
    "market_status",
    "open_order_check",
    "recent_order_match_check",
    "recent_order_match_status",
    "recent_order_match_count",
    "recent_order_match_age_minutes",
    "recent_order_match_source",
    "intended_action",
    "order_side",
    "quantity",
    "decision_status",
    "blocker",
    "required_next_step",
    "order_status",
    "strategy_execution_approved",
    "qqq100_one_share_alignment_approved",
    "execution_approved",
    "paper_execution_approved",
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
    "strategy_execution_approved",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    "strategy_execution_approved",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]


@dataclass(frozen=True)
class Qqq100SavedSignal:
    available: bool
    strategy_name: str
    ticker: str
    desired_position: str
    signal_date: str
    data_status: str
    data_error: str


@dataclass(frozen=True)
class Qqq100PaperExecutionDecision:
    allowed: bool
    decision_status: str
    strategy_name: str
    ticker: str
    signal_source: str
    desired_position: str
    signal_date: str
    preview_signal_status: str
    current_position_status: str
    current_position_quantity_abs: str
    market_status: str
    open_order_check: str
    recent_order_match_check: str
    recent_order_match_status: str
    recent_order_match_count: int
    recent_order_match_age_minutes: str
    recent_order_match_source: str
    intended_action: str
    order_side: str
    quantity: str
    reasons: list[str]
    required_next_step: str
    strategy_execution_approved: bool
    qqq100_one_share_alignment_approved: bool
    execution_approved: bool = False
    paper_execution_approved: bool = False
    scheduling_approved: bool = False


def read_saved_qqq100_preview_signal(path: Path = SAVED_SIGNAL_PATH) -> Qqq100SavedSignal:
    rows = read_csv_rows(path)
    row = next(
        (
            candidate
            for candidate in rows
            if str(candidate.get("strategy_name", "")).strip() == STRATEGY_NAME
            and str(candidate.get("ticker", "")).strip().upper() == TICKER
        ),
        None,
    )
    if not row:
        return Qqq100SavedSignal(False, "", "", "", "", "missing", f"Missing saved signal: {path}")

    return Qqq100SavedSignal(
        available=True,
        strategy_name=str(row.get("strategy_name", "")).strip(),
        ticker=str(row.get("ticker", "")).strip().upper(),
        desired_position=str(row.get("desired_position", "")).strip().lower(),
        signal_date=str(row.get("signal_date", "")).strip(),
        data_status=str(row.get("data_status", "")).strip().lower(),
        data_error=str(row.get("data_error", "")).strip(),
    )


def evaluate_qqq100_paper_execution_preflight(
    *,
    confirm_qqq100_paper: bool,
    alpaca_paper: bool,
    allow_shorting: bool,
    credentials_present: bool,
    market_status: str,
    signal: Qqq100SavedSignal,
    current_position: Position | None,
    position_readable: bool,
    open_order_count: int | None,
    recent_order_match: ManualSmokeTestRecentOrderMatch | None = None,
    extra_blockers: list[str] | None = None,
) -> Qqq100PaperExecutionDecision:
    reasons: list[str] = []
    normalized_market_status = str(market_status or "").strip().lower() or "unknown"
    desired_position = signal.desired_position
    current_position_status = "unreadable"
    current_quantity_abs = ""

    if not confirm_qqq100_paper:
        reasons.append("--confirm-qqq100-paper is required")
    if alpaca_paper is not True:
        reasons.append("alpaca.paper must be true; live trading is refused")
    if allow_shorting is True:
        reasons.append("allow_shorting must remain false")
    if credentials_present is not True:
        reasons.append("Alpaca paper credentials are required")
    if normalized_market_status != "open":
        reasons.append("market_status must be open")
    if not signal.available:
        reasons.append("saved QQQ100 preview signal is missing")
    if signal.strategy_name and signal.strategy_name != STRATEGY_NAME:
        reasons.append("saved signal strategy must be qqq_100_trend_gate")
    if signal.ticker and signal.ticker != TICKER:
        reasons.append("saved signal ticker must be QQQ")
    if desired_position not in VALID_DESIRED_POSITIONS:
        reasons.append("saved desired_position must be long or flat")
    if signal.data_status not in {"", "ok"}:
        reasons.append("saved QQQ100 preview signal data_status must be ok")
    if signal.data_error:
        reasons.append("saved QQQ100 preview signal contains data_error")
    if not position_readable or current_position is None:
        reasons.append("current QQQ paper position could not be read")
    else:
        current_position_status = f"paper_position_{current_position.state}"
        current_quantity_abs = format_decimal(current_position.abs_quantity)

    open_order_check = "not_checked"
    if open_order_count is None:
        reasons.append("open QQQ orders could not be read")
        open_order_check = "open_order_check_unavailable"
    elif open_order_count > 0:
        reasons.append("an open QQQ order already exists")
        open_order_check = "blocked_open_order_exists"
    else:
        open_order_check = "pass"

    recent_order_check = "not_checked"
    recent_order_status = "none"
    recent_order_count = 0
    recent_order_age = ""
    recent_order_source = "alpaca_paper_recent_orders"
    if recent_order_match is not None:
        recent_order_check = recent_order_match.duplicate_recent_order_check
        recent_order_status = recent_order_match.recent_order_match_status or "none"
        recent_order_count = recent_order_match.recent_order_match_count
        recent_order_age = recent_order_match.recent_order_match_age_minutes
        recent_order_source = recent_order_match.recent_order_match_source
        if recent_order_check == "blocked_recent_matching_order_exists":
            reasons.append("a recent matching QQQ one-share paper order already exists")
        elif recent_order_check == "blocked_duplicate_order_history_uncertain":
            reasons.append("recent QQQ order history could not be read from Alpaca paper")
        elif recent_order_check == "blocked_ambiguous_recent_matching_order_status":
            reasons.append("a recent matching QQQ one-share order has an ambiguous broker status")

    if extra_blockers:
        reasons.extend(extra_blockers)

    intended_action, order_side = qqq100_alignment_action(desired_position, current_position)
    if intended_action == "blocked_short_position":
        reasons.append("current QQQ paper position is short; short handling is not supported")
    elif intended_action == "blocked_excess_long_position":
        reasons.append("current QQQ paper position exceeds one share; manual review is required before reducing exposure")
    elif intended_action == "blocked_non_one_share_long_position":
        reasons.append("current QQQ paper position is long but not exactly one share; manual review is required")
    elif intended_action == "blocked_close_quantity":
        reasons.append("flat alignment would oversell or close more than one QQQ share")

    allowed = not reasons
    if allowed:
        status = (
            "qqq100_paper_order_ready"
            if intended_action in {"buy_1", "sell_1"}
            else "qqq100_paper_no_order_needed"
        )
        required_next_step = (
            "Submit only the exact one-share QQQ paper alignment order through this manually confirmed command."
            if intended_action in {"buy_1", "sell_1"}
            else "No paper order is needed because QQQ is already aligned with the saved QQQ100 signal."
        )
    else:
        status = "qqq100_paper_execution_blocked"
        required_next_step = "Keep QQQ100 paper execution blocked until all manual preflight blockers are resolved."

    return Qqq100PaperExecutionDecision(
        allowed=allowed,
        decision_status=status,
        strategy_name=STRATEGY_NAME,
        ticker=TICKER,
        signal_source=SIGNAL_SOURCE,
        desired_position=desired_position or "unknown",
        signal_date=signal.signal_date,
        preview_signal_status="ok" if signal.available and signal.data_status in {"", "ok"} and not signal.data_error else "blocked",
        current_position_status=current_position_status,
        current_position_quantity_abs=current_quantity_abs,
        market_status=normalized_market_status,
        open_order_check=open_order_check,
        recent_order_match_check=recent_order_check,
        recent_order_match_status=recent_order_status,
        recent_order_match_count=recent_order_count,
        recent_order_match_age_minutes=recent_order_age,
        recent_order_match_source=recent_order_source,
        intended_action=intended_action,
        order_side=order_side,
        quantity=format_decimal(FIXED_QUANTITY) if intended_action in {"buy_1", "sell_1"} else "0",
        reasons=reasons or ["exact manually confirmed QQQ100 one-share paper alignment preflight passed"],
        required_next_step=required_next_step,
        strategy_execution_approved=allowed,
        qqq100_one_share_alignment_approved=allowed,
    )


def qqq100_alignment_action(desired_position: str, current_position: Position | None) -> tuple[str, str]:
    if current_position is None:
        return "blocked_position_unreadable", ""
    if current_position.state == POSITION_SHORT:
        return "blocked_short_position", ""
    if desired_position == POSITION_LONG:
        if current_position.state == POSITION_FLAT:
            return "buy_1", "buy"
        if current_position.abs_quantity == FIXED_QUANTITY:
            return "hold_already_long", ""
        if current_position.abs_quantity > FIXED_QUANTITY:
            return "blocked_excess_long_position", ""
        return "blocked_non_one_share_long_position", ""
    if desired_position == POSITION_FLAT:
        if current_position.state == POSITION_FLAT:
            return "hold_flat", ""
        if current_position.abs_quantity == FIXED_QUANTITY:
            return "sell_1", "sell"
        if current_position.abs_quantity > FIXED_QUANTITY:
            return "blocked_excess_long_position", ""
        return "blocked_non_one_share_long_position", ""
    return "blocked_unknown_desired_position", ""


def write_qqq100_paper_execution_report(
    decision: Qqq100PaperExecutionDecision,
    *,
    order_status: str = "",
    order_event: str = "no_order_work_started",
    root_dir: Path | str = ".",
) -> None:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result_row = {
        "created_at": created_at,
        "strategy_name": decision.strategy_name,
        "ticker": decision.ticker,
        "signal_source": decision.signal_source,
        "desired_position": decision.desired_position,
        "signal_date": decision.signal_date,
        "preview_signal_status": decision.preview_signal_status,
        "current_position_status": decision.current_position_status,
        "current_position_quantity_abs": decision.current_position_quantity_abs,
        "market_status": decision.market_status,
        "open_order_check": decision.open_order_check,
        "recent_order_match_check": decision.recent_order_match_check,
        "recent_order_match_status": decision.recent_order_match_status,
        "recent_order_match_count": decision.recent_order_match_count,
        "recent_order_match_age_minutes": decision.recent_order_match_age_minutes,
        "recent_order_match_source": decision.recent_order_match_source,
        "intended_action": decision.intended_action,
        "order_side": decision.order_side,
        "quantity": decision.quantity,
        "decision_status": decision.decision_status,
        "blocker": "; ".join(decision.reasons) if not decision.allowed else "none_for_exact_qqq100_manual_alignment",
        "required_next_step": decision.required_next_step,
        "order_status": order_status,
        **approval_flags(decision, order_event=order_event),
    }
    summary_rows = [
        summary_row("decision_status", decision.decision_status, "Final manually confirmed QQQ100 paper alignment decision.", decision),
        summary_row("strategy_name", decision.strategy_name, "Only qqq_100_trend_gate is eligible.", decision),
        summary_row("ticker", decision.ticker, "Only QQQ is eligible.", decision),
        summary_row("desired_position", decision.desired_position, "Saved desired position from qqq100_preview_signal_pack.", decision),
        summary_row("intended_action", decision.intended_action, "One-share QQQ paper alignment action, or no-order hold.", decision),
        summary_row("market_status", decision.market_status, "Broker market-clock status used by the command.", decision),
        summary_row("open_order_check", decision.open_order_check, "Open QQQ order check.", decision),
        summary_row("recent_order_match_check", decision.recent_order_match_check, "Recent matching QQQ order check.", decision),
        summary_row("order_event", order_event, "Whether this run submitted a paper order or wrote only a blocked/hold report.", decision),
        summary_row("execution_approved", "False", "General execution approval remains false.", decision),
        summary_row("scheduling_approved", "False", "Scheduling remains false.", decision),
    ]
    blocker_rows = [
        blocker_row(reason, "blocked", "critical", reason, decision.required_next_step, decision)
        for reason in decision.reasons
        if not decision.allowed
    ]
    if decision.allowed:
        blocker_rows = [
            blocker_row(
                "general_strategy_execution_not_approved",
                "blocked_for_general_execution",
                "critical",
                "This command allows only the exact manually confirmed QQQ100 one-share paper alignment path.",
                "Do not generalize this command to other strategies, tickers, quantities, or schedules.",
                decision,
            )
        ]
    write_rows(root / RESULT_PATH, RESULT_COLUMNS, [result_row])
    write_rows(root / SUMMARY_PATH, SUMMARY_COLUMNS, summary_rows)
    write_rows(root / BLOCKERS_PATH, BLOCKER_COLUMNS, blocker_rows)


def approval_flags(decision: Qqq100PaperExecutionDecision, *, order_event: str) -> dict[str, bool]:
    order_submitted = order_event == "order_submitted"
    return {
        "strategy_execution_approved": decision.strategy_execution_approved,
        "qqq100_one_share_alignment_approved": decision.qqq100_one_share_alignment_approved,
        "execution_approved": False,
        "paper_execution_approved": False,
        "scheduling_approved": False,
        "orders_created": order_submitted,
        "orders_submitted": order_submitted,
        "orders_cancelled": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
    }


def summary_row(
    name: str,
    value: str,
    details: str,
    decision: Qqq100PaperExecutionDecision,
) -> dict[str, Any]:
    return {
        "summary_name": name,
        "summary_value": value,
        "details": details,
        "strategy_execution_approved": decision.strategy_execution_approved,
        "execution_approved": False,
        "paper_execution_approved": False,
        "scheduling_approved": False,
    }


def blocker_row(
    name: str,
    status: str,
    severity: str,
    details: str,
    required_next_step: str,
    decision: Qqq100PaperExecutionDecision,
) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": required_next_step,
        "strategy_execution_approved": decision.strategy_execution_approved,
        "execution_approved": False,
        "paper_execution_approved": False,
        "scheduling_approved": False,
    }


def print_qqq100_paper_execution_decision(decision: Qqq100PaperExecutionDecision) -> None:
    print("QQQ100 MANUAL PAPER EXECUTION PREFLIGHT")
    print(f"strategy_name={decision.strategy_name}")
    print(f"ticker={decision.ticker}")
    print(f"signal_source={decision.signal_source}")
    print(f"desired_position={decision.desired_position}")
    print(f"current_position_status={decision.current_position_status}")
    print(f"current_position_quantity_abs={decision.current_position_quantity_abs or 'unknown'}")
    print(f"market_status={decision.market_status}")
    print(f"open_order_check={decision.open_order_check}")
    print(f"recent_order_match_check={decision.recent_order_match_check}")
    print(f"recent_order_match_status={decision.recent_order_match_status}")
    print(f"recent_order_match_count={decision.recent_order_match_count}")
    print(f"intended_action={decision.intended_action}")
    print(f"order_side={decision.order_side or 'none'}")
    print(f"quantity={decision.quantity}")
    print(f"decision_status={decision.decision_status}")
    print(f"strategy_execution_approved={decision.strategy_execution_approved}")
    print(f"execution_approved={decision.execution_approved}")
    print(f"paper_execution_approved={decision.paper_execution_approved}")
    print(f"scheduling_approved={decision.scheduling_approved}")
    if not decision.allowed:
        print("No QQQ100 paper order was created, submitted, or cancelled.")
        print("Reasons:")
        for reason in decision.reasons:
            print(f"- {reason}")
    else:
        print(decision.required_next_step)
    print("This does not approve live trading, scheduling, shorts, leverage, or any other strategy.")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
