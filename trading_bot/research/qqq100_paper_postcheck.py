"""Read-only QQQ100 paper execution postcheck.

Default mode is saved-output/static only. Confirmed mode may perform read-only
Alpaca paper order and position checks, but it never creates, submits, cancels,
replaces, or prepares orders.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from trading_bot.positions import Position, format_decimal
from trading_bot.safety.manual_paper_smoke_test_gate import (
    RECENT_ORDER_LOOKBACK_MINUTES,
    evaluate_recent_manual_smoke_test_order_match,
)


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"
SIDE = "buy"
QUANTITY = Decimal("1")

OUTPUT_PATH = Path("data/qqq100_paper_postcheck.csv")
SUMMARY_PATH = Path("data/qqq100_paper_postcheck_summary.csv")
BLOCKERS_PATH = Path("data/qqq100_paper_postcheck_blockers.csv")
SIGNAL_PATH = Path("data/qqq100_preview_signal_pack.csv")

FINAL_FILLED_ALIGNED = "qqq100_postcheck_order_observed_filled_aligned_long"
FINAL_NO_CONFIRM = "qqq100_postcheck_requires_confirmed_readonly_check"
FINAL_NO_MATCH = "qqq100_postcheck_no_matching_order_found"
FINAL_MANUAL_REVIEW = "qqq100_postcheck_manual_review_required"
FINAL_BLOCKED = "qqq100_postcheck_blocked"

SAFETY_COLUMNS = [
    "report_only",
    "alpaca_called",
    "alpaca_readonly",
    "paper_positions_read",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "qqq100_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
]

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "strategy_name",
    "ticker",
    "desired_position",
    "order_side",
    "quantity",
    "evidence_source",
    "details",
    "recent_order_match_found",
    "recent_order_match_status",
    "recent_order_match_submitted_at_or_created_at",
    "recent_order_match_age_minutes",
    "recent_order_match_source",
    "recent_order_match_count",
    "recent_order_match_lookback_minutes",
    "broker_order_history_status_filter_used",
    "broker_order_history_limit",
    "broker_order_history_rows_seen",
    "position_status",
    "position_quantity_abs",
    "alignment_state",
    "blocker",
    "recommended_next_step",
    "final_postcheck_status",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_COLUMNS,
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_COLUMNS,
]


@dataclass
class Qqq100PaperPostcheckResult:
    output_path: Path
    summary_path: Path
    blockers_path: Path
    rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_paper_postcheck(
    confirm_readonly_alpaca_check: bool = False,
    root_dir: Path | str = ".",
) -> Qqq100PaperPostcheckResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    desired_position = read_saved_desired_position(root / SIGNAL_PATH)
    rows = build_static_rows(created_at, desired_position, confirm_readonly_alpaca_check)
    if confirm_readonly_alpaca_check:
        rows.extend(build_confirmed_readonly_rows(root, created_at, desired_position))
    final_status = choose_final_status(rows, confirm_readonly_alpaca_check)
    rows.append(final_row(created_at, desired_position, rows, final_status))
    summary_rows = build_summary_rows(rows, final_status)
    blocker_rows = build_blocker_rows(rows, final_status)
    output_path = root / OUTPUT_PATH
    summary_path = root / SUMMARY_PATH
    blockers_path = root / BLOCKERS_PATH
    write_rows(output_path, REPORT_COLUMNS, rows)
    write_rows(summary_path, SUMMARY_COLUMNS, summary_rows)
    write_rows(blockers_path, BLOCKER_COLUMNS, blocker_rows)
    return Qqq100PaperPostcheckResult(
        output_path=output_path,
        summary_path=summary_path,
        blockers_path=blockers_path,
        rows=rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_path),
    )


def show_qqq100_paper_postcheck(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / SUMMARY_PATH
    if not summary_path.exists():
        return 1, [
            "QQQ100 paper postcheck is missing.",
            "Run `python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check` after a manually confirmed QQQ100 paper run.",
            "execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 paper postcheck saved display. Read-only report; no follow-up order approved.",
        f"final_postcheck_status: {summary_value(rows, 'final_postcheck_status')}",
        f"recent_order_match_found: {summary_value(rows, 'recent_order_match_found')}",
        f"recent_order_match_status: {summary_value(rows, 'recent_order_match_status')}",
        f"position_status: {summary_value(rows, 'position_status')}",
        f"position_quantity_abs: {summary_value(rows, 'position_quantity_abs')}",
        f"alignment_state: {summary_value(rows, 'alignment_state')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; qqq100_execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def build_static_rows(created_at: str, desired_position: str, confirmed: bool) -> list[dict[str, Any]]:
    status = "pass" if confirmed else "blocked_confirmation_required"
    return [
        report_row(
            created_at,
            "input_scope",
            "pass",
            "info",
            desired_position,
            "static",
            "Fixed read-only QQQ100 postcheck: qqq_100_trend_gate / QQQ / buy 1.",
            False,
            "continue_readonly_postcheck",
        ),
        report_row(
            created_at,
            "readonly_confirmation",
            status,
            "info" if confirmed else "blocked",
            desired_position,
            "CLI flag",
            "Read-only Alpaca check confirmed." if confirmed else "--confirm-readonly-alpaca-check is required before broker/order/position reads.",
            not confirmed,
            "rerun_with_confirm_readonly_alpaca_check" if not confirmed else "continue_readonly_postcheck",
        ),
        report_row(
            created_at,
            "saved_signal_context",
            "saved_signal_present" if desired_position in {"long", "flat"} else "saved_signal_missing_or_unknown",
            "info" if desired_position in {"long", "flat"} else "warning",
            desired_position,
            str(SIGNAL_PATH),
            f"Saved desired_position={desired_position}.",
            desired_position not in {"long", "flat"},
            "restore_qqq100_preview_signal_before_interpreting_alignment" if desired_position not in {"long", "flat"} else "continue_readonly_postcheck",
        ),
    ]


def build_confirmed_readonly_rows(root: Path, created_at: str, desired_position: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        from trading_bot.config import load_config

        config = load_config(root / "config.json", force_dry_run=True)
    except Exception as exc:  # noqa: BLE001
        return [
            report_row(
                created_at,
                "readonly_config_load",
                "blocked_config_load_failed",
                "blocked",
                desired_position,
                "local config loader",
                f"Config load failed safely without printing contents: {type(exc).__name__}.",
                True,
                "fix_local_paper_config_before_readonly_postcheck",
                final_status=FINAL_BLOCKED,
            )
        ]
    paper = bool(getattr(config, "alpaca_paper", False))
    key_available = bool(getattr(config, "alpaca_api_key", ""))
    secret_available = bool(getattr(config, "alpaca_secret_key", ""))
    rows.append(
        report_row(
            created_at,
            "readonly_config_load",
            "pass",
            "info",
            desired_position,
            "local config loader",
            "Config loaded successfully. Contents and credential values were not printed.",
            False,
            "continue_readonly_postcheck",
        )
    )
    rows.append(
        report_row(
            created_at,
            "readonly_paper_mode",
            "pass" if paper else "blocked_not_paper_mode",
            "info" if paper else "blocked",
            desired_position,
            "config object redacted",
            "alpaca.paper is true." if paper else "alpaca.paper is not true; live trading is out of scope.",
            not paper,
            "continue_readonly_postcheck" if paper else "restore_paper_mode_before_postcheck",
        )
    )
    rows.append(
        report_row(
            created_at,
            "readonly_credentials_present",
            "pass" if key_available and secret_available else "blocked_missing_credentials",
            "info" if key_available and secret_available else "blocked",
            desired_position,
            "config object redacted",
            f"api_key_present={key_available}; secret_key_present={secret_available}; values redacted.",
            not (key_available and secret_available),
            "continue_readonly_postcheck" if key_available and secret_available else "configure_paper_credentials_without_exposing_values",
        )
    )
    if not paper or not key_available or not secret_available:
        return rows

    try:
        from alpaca.common.enums import Sort
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import OrderSide, QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        client = TradingClient(getattr(config, "alpaca_api_key"), getattr(config, "alpaca_secret_key"), paper=True)
        after = datetime.now(timezone.utc) - timedelta(minutes=RECENT_ORDER_LOOKBACK_MINUTES)
        limit = 500
        request_args = {
            "symbols": [TICKER],
            "side": OrderSide.BUY,
            "limit": limit,
            "after": after,
            "direction": Sort.DESC,
        }
        closed_orders = list(client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.CLOSED, **request_args)))
        all_orders = list(client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.ALL, **request_args)))
        recent_orders = merge_order_history(closed_orders, all_orders)
        match = evaluate_recent_manual_smoke_test_order_match(
            recent_orders,
            ticker=TICKER,
            side=SIDE,
            quantity=QUANTITY,
        )
        rows.append(recent_order_row(created_at, desired_position, match, len(recent_orders), limit))
        position = read_position(client)
        rows.append(position_row(created_at, desired_position, position))
    except Exception as exc:  # noqa: BLE001
        rows.append(
            report_row(
                created_at,
                "readonly_alpaca_postcheck",
                "blocked_readonly_check_failed",
                "blocked",
                desired_position,
                "Alpaca paper read-only endpoints",
                f"Read-only postcheck failed safely: {type(exc).__name__}.",
                True,
                "manual_review_required_for_readonly_alpaca_failure",
                alpaca_called=True,
                alpaca_readonly=True,
                final_status=FINAL_BLOCKED,
            )
        )
    return rows


def recent_order_row(
    created_at: str,
    desired_position: str,
    match: Any,
    rows_seen: int,
    limit: int,
) -> dict[str, Any]:
    check_status = match.duplicate_recent_order_check
    found = bool(match.recent_order_match_found)
    return report_row(
        created_at,
        "readonly_recent_qqq_buy_1_order",
        check_status,
        "info" if found else "warning",
        desired_position,
        "alpaca_paper_recent_orders",
        "Read-only recent QQQ buy 1 order history checked. Order IDs were not printed.",
        False if found else True,
        "confirm_position_alignment_from_saved_or_readonly_context" if found else "manual_review_required_no_recent_qqq_buy_1_found",
        recent_order_match_found=found,
        recent_order_match_status=match.recent_order_match_status,
        recent_order_match_submitted_at_or_created_at=match.recent_order_match_submitted_at_or_created_at,
        recent_order_match_age_minutes=match.recent_order_match_age_minutes,
        recent_order_match_source=match.recent_order_match_source,
        recent_order_match_count=match.recent_order_match_count,
        recent_order_match_lookback_minutes=match.recent_order_match_lookback_minutes,
        broker_order_history_status_filter_used="closed,all",
        broker_order_history_limit=limit,
        broker_order_history_rows_seen=rows_seen,
        alpaca_called=True,
        alpaca_readonly=True,
    )


def position_row(created_at: str, desired_position: str, position: Position) -> dict[str, Any]:
    alignment_state = determine_alignment(desired_position, position)
    return report_row(
        created_at,
        "readonly_current_qqq_position",
        "pass",
        "info",
        desired_position,
        "alpaca_paper_positions_readonly",
        "Read-only QQQ paper position checked. Account identifiers were not printed.",
        alignment_state != "aligned_long",
        "keep_manual_review_before_any_repeat_execution" if alignment_state == "aligned_long" else "manual_review_required_position_not_aligned",
        position_status=f"paper_position_{position.state}",
        position_quantity_abs=format_decimal(position.abs_quantity),
        alignment_state=alignment_state,
        alpaca_called=True,
        alpaca_readonly=True,
        paper_positions_read=True,
    )


def final_row(created_at: str, desired_position: str, rows: list[dict[str, Any]], final_status: str) -> dict[str, Any]:
    return report_row(
        created_at,
        "final_postcheck_status",
        final_status,
        "info" if final_status == FINAL_FILLED_ALIGNED else ("blocked" if final_status in {FINAL_NO_CONFIRM, FINAL_BLOCKED} else "warning"),
        desired_position,
        "postcheck rows",
        final_details(final_status, rows),
        final_status != FINAL_FILLED_ALIGNED,
        final_next_step(final_status),
        recent_order_match_found=any_true(rows, "recent_order_match_found"),
        recent_order_match_status=first_nonempty(rows, ["recent_order_match_status"]) or "none",
        recent_order_match_count=max_int(rows, "recent_order_match_count"),
        position_status=first_nonempty(rows, ["position_status"]),
        position_quantity_abs=first_nonempty(rows, ["position_quantity_abs"]),
        alignment_state=first_nonempty(rows, ["alignment_state"]),
        alpaca_called=any_true(rows, "alpaca_called"),
        alpaca_readonly=any_true(rows, "alpaca_readonly"),
        paper_positions_read=any_true(rows, "paper_positions_read"),
        final_status=final_status,
    )


def choose_final_status(rows: list[dict[str, Any]], confirmed: bool) -> str:
    if not confirmed:
        return FINAL_NO_CONFIRM
    if any(str(row.get("check_status")) == "blocked_readonly_check_failed" for row in rows):
        return FINAL_BLOCKED
    order_found = any_true(rows, "recent_order_match_found")
    order_status = first_nonempty(rows, ["recent_order_match_status"]).lower()
    alignment = first_nonempty(rows, ["alignment_state"])
    if order_found and order_status == "filled" and alignment == "aligned_long":
        return FINAL_FILLED_ALIGNED
    if not order_found:
        return FINAL_NO_MATCH
    return FINAL_MANUAL_REVIEW


def build_summary_rows(rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    final = rows[-1]
    items = [
        ("final_postcheck_status", final_status, "Final read-only QQQ100 paper postcheck status."),
        ("recent_order_match_found", str(final.get("recent_order_match_found", False)), "Whether a recent QQQ buy 1 broker order was observed."),
        ("recent_order_match_status", str(final.get("recent_order_match_status") or "none"), "Redacted broker status for the matching recent order."),
        ("position_status", str(final.get("position_status") or "unknown"), "Read-only QQQ position status."),
        ("position_quantity_abs", str(final.get("position_quantity_abs") or "unknown"), "Read-only absolute QQQ position quantity."),
        ("alignment_state", str(final.get("alignment_state") or "unknown"), "Alignment versus saved QQQ100 desired_position."),
        ("recommended_next_step", final_next_step(final_status), "Conservative next step."),
    ]
    return [
        {
            "summary_name": name,
            "summary_value": value,
            "details": details,
            **safety_flags(),
        }
        for name, value, details in items
    ]


def build_blocker_rows(rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    blockers = []
    if final_status != FINAL_FILLED_ALIGNED:
        blockers.append(("qqq100_postcheck_not_fully_confirmed", "blocked", "critical", final_details(final_status, rows), final_next_step(final_status)))
    blockers.extend(
        [
            ("followup_order_not_approved", "blocked", "critical", "This postcheck approves no follow-up order.", "Do not place follow-up orders from postcheck output."),
            ("repeat_execution_not_approved", "blocked", "critical", "Repeat QQQ100 execution is not approved.", "Design a separate repeat/alignment workflow before any repeat use."),
            ("scheduling_not_approved", "blocked", "critical", "Scheduling remains unapproved.", "Do not schedule execution-capable commands."),
        ]
    )
    return [
        {
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **safety_flags(),
        }
        for name, status, severity, details, next_step in blockers
    ]


def report_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    desired_position: str,
    evidence_source: str,
    details: str,
    blocker: bool,
    recommended_next_step: str,
    *,
    recent_order_match_found: bool = False,
    recent_order_match_status: str = "",
    recent_order_match_submitted_at_or_created_at: str = "",
    recent_order_match_age_minutes: str = "",
    recent_order_match_source: str = "",
    recent_order_match_count: int = 0,
    recent_order_match_lookback_minutes: int = RECENT_ORDER_LOOKBACK_MINUTES,
    broker_order_history_status_filter_used: str = "",
    broker_order_history_limit: int | str = "",
    broker_order_history_rows_seen: int | str = "",
    position_status: str = "",
    position_quantity_abs: str = "",
    alignment_state: str = "",
    alpaca_called: bool = False,
    alpaca_readonly: bool = False,
    paper_positions_read: bool = False,
    final_status: str = FINAL_MANUAL_REVIEW,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "strategy_name": STRATEGY_NAME,
        "ticker": TICKER,
        "desired_position": desired_position,
        "order_side": SIDE,
        "quantity": "1",
        "evidence_source": evidence_source,
        "details": details,
        "recent_order_match_found": recent_order_match_found,
        "recent_order_match_status": recent_order_match_status,
        "recent_order_match_submitted_at_or_created_at": recent_order_match_submitted_at_or_created_at,
        "recent_order_match_age_minutes": recent_order_match_age_minutes,
        "recent_order_match_source": recent_order_match_source,
        "recent_order_match_count": recent_order_match_count,
        "recent_order_match_lookback_minutes": recent_order_match_lookback_minutes,
        "broker_order_history_status_filter_used": broker_order_history_status_filter_used,
        "broker_order_history_limit": broker_order_history_limit,
        "broker_order_history_rows_seen": broker_order_history_rows_seen,
        "position_status": position_status,
        "position_quantity_abs": position_quantity_abs,
        "alignment_state": alignment_state,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        "final_postcheck_status": final_status,
        **safety_flags(
            alpaca_called=alpaca_called,
            alpaca_readonly=alpaca_readonly,
            paper_positions_read=paper_positions_read,
        ),
    }


def read_position(client: Any) -> Position:
    for position in client.get_all_positions():
        if str(getattr(position, "symbol", "")).upper() != TICKER:
            continue
        qty = Decimal(str(getattr(position, "qty", "0")))
        side = str(getattr(position, "side", "")).lower()
        return Position(-abs(qty) if side == "short" else abs(qty))
    return Position()


def determine_alignment(desired_position: str, position: Position) -> str:
    if desired_position == "long" and position.state == "long":
        return "aligned_long"
    if desired_position == "flat" and position.state == "flat":
        return "aligned_flat"
    return "not_aligned"


def read_saved_desired_position(path: Path) -> str:
    rows = read_csv_rows(path)
    for row in rows:
        if str(row.get("strategy_name", "")).strip() == STRATEGY_NAME and str(row.get("ticker", "")).strip().upper() == TICKER:
            return str(row.get("desired_position", "")).strip().lower() or "unknown"
    return "unknown"


def merge_order_history(*groups: list[Any]) -> list[Any]:
    merged: list[Any] = []
    seen: set[str] = set()
    for group in groups:
        for order in group:
            key = str(getattr(order, "id", "")) or repr(order)
            if key in seen:
                continue
            seen.add(key)
            merged.append(order)
    return merged


def final_details(final_status: str, rows: list[dict[str, Any]]) -> str:
    if final_status == FINAL_FILLED_ALIGNED:
        return "Recent QQQ buy 1 filled order and aligned long QQQ paper position were observed read-only."
    if final_status == FINAL_NO_CONFIRM:
        return "Read-only broker/order/position checks require --confirm-readonly-alpaca-check."
    if final_status == FINAL_NO_MATCH:
        return "No recent QQQ buy 1 broker order was observed in the lookback window."
    if final_status == FINAL_BLOCKED:
        return "Read-only QQQ100 postcheck was blocked by a safe failure."
    return "Manual review required for QQQ100 postcheck."


def final_next_step(final_status: str) -> str:
    if final_status == FINAL_FILLED_ALIGNED:
        return "record_milestone_and_do_not_place_followup_order"
    if final_status == FINAL_NO_CONFIRM:
        return "rerun_with_confirm_readonly_alpaca_check_if_readonly_broker_verification_is_needed"
    return "manual_review_required_before_any_repeat_execution_discussion"


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    return [
        "QQQ100 paper postcheck generated.",
        f"final_postcheck_status: {summary_value(summary_rows, 'final_postcheck_status')}",
        f"recent_order_match_found: {summary_value(summary_rows, 'recent_order_match_found')}",
        f"recent_order_match_status: {summary_value(summary_rows, 'recent_order_match_status')}",
        f"position_status: {summary_value(summary_rows, 'position_status')}",
        f"position_quantity_abs: {summary_value(summary_rows, 'position_quantity_abs')}",
        f"alignment_state: {summary_value(summary_rows, 'alignment_state')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; qqq100_execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def safety_flags(
    *,
    alpaca_called: bool = False,
    alpaca_readonly: bool = False,
    paper_positions_read: bool = False,
) -> dict[str, bool]:
    return {
        "report_only": True,
        "alpaca_called": alpaca_called,
        "alpaca_readonly": alpaca_readonly,
        "paper_positions_read": paper_positions_read,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
        "orders_replaced": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
        "execution_approved": False,
        "paper_execution_approved": False,
        "qqq100_execution_approved": False,
        "followup_order_approved": False,
        "repeat_execution_approved": False,
        "scheduling_approved": False,
    }


def any_true(rows: list[dict[str, Any]], key: str) -> bool:
    return any(str(row.get(key, "")).strip().lower() == "true" for row in rows)


def first_nonempty(rows: list[dict[str, Any]], keys: list[str]) -> str:
    for row in reversed(rows):
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
    return ""


def max_int(rows: list[dict[str, Any]], key: str) -> int:
    values: list[int] = []
    for row in rows:
        try:
            values.append(int(str(row.get(key, "0") or "0")))
        except ValueError:
            continue
    return max(values) if values else 0


def summary_value(rows: list[dict[str, str]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return "missing"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
