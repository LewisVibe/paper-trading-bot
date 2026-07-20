"""Guarded paper-ticket preparation, execution, and read-only postcheck."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from alpaca.common.enums import Sort
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest

from trading_bot.alpaca_client import normalize_order_status, refresh_order_status
from trading_bot.config import AppConfig
from trading_bot.discord_alerts import send_discord_alert
from trading_bot.paper_orders import PaperOrderRequest, PaperOrderRoute, submit_paper_order
from trading_bot.safety.paper_kill_switch import evaluate_paper_kill_switch_gate
from trading_bot.safety.vol_targeted_growth_paper_execution import (
    AssetState,
    BrokerState,
    MIN_ORDER_NOTIONAL_USD,
    build_ticket_document,
    decimal_text,
    execution_preflight_reasons,
    safe_decimal,
    verify_ticket_document,
)
from trading_bot.strategies.vol_targeted_growth import (
    MANAGED_SYMBOLS,
    load_live_volatility_snapshot,
)


TICKET_JSON = Path("data/vol_targeted_growth_paper_ticket.json")
TICKET_CSV = Path("data/vol_targeted_growth_paper_ticket.csv")
TICKET_SUMMARY = Path("data/vol_targeted_growth_paper_ticket_summary.csv")
EXECUTION_JSON = Path("data/vol_targeted_growth_paper_execution.json")
EXECUTION_CSV = Path("data/vol_targeted_growth_paper_execution.csv")
EXECUTION_SUMMARY = Path("data/vol_targeted_growth_paper_execution_summary.csv")
POSTCHECK_JSON = Path("data/vol_targeted_growth_paper_postcheck.json")
POSTCHECK_CSV = Path("data/vol_targeted_growth_paper_postcheck.csv")
POSTCHECK_SUMMARY = Path("data/vol_targeted_growth_paper_postcheck_summary.csv")
AUTO_STATE_JSON = Path("data/vol_targeted_growth_auto_paper_state.json")
AUTO_SUMMARY = Path("data/vol_targeted_growth_auto_paper_summary.csv")
AUTO_TIMEZONE = ZoneInfo("America/New_York")
AUTO_WINDOW_START_MINUTE = 10 * 60
AUTO_WINDOW_END_MINUTE = 10 * 60 + 20
NO_ORDERS_REQUIRED = "no paper orders are required for the current target"


def run_prepare_vol_targeted_growth_paper_ticket(
    config: AppConfig,
    logger: logging.Logger,
    *,
    confirm_readonly_alpaca_check: bool,
    root_dir: Path | str = ".",
) -> int:
    root = Path(root_dir)
    reasons = _config_reasons(config)
    if not confirm_readonly_alpaca_check:
        reasons.append("--confirm-readonly-alpaca-check is required")
    if reasons:
        _print_blocked("Paper-ticket preparation blocked", reasons)
        return 2

    try:
        client = _paper_client(config)
        now = datetime.now(timezone.utc)
        broker = collect_broker_state(client, now=now)
        volatility = load_live_volatility_snapshot(root, now=now)
        document = build_ticket_document(volatility, broker, now=now)
        write_ticket_outputs(root, document)
    except Exception as exc:  # noqa: BLE001 - fail closed without sensitive details
        logger.error("Volatility-targeted paper-ticket preparation failed safely: %s", type(exc).__name__)
        print(f"Paper-ticket preparation failed safely: {type(exc).__name__}")
        print("No orders were created, submitted, cancelled, or replaced.")
        return 1

    _print_ticket(document)
    return 0


def run_execute_vol_targeted_growth_paper(
    config: AppConfig,
    logger: logging.Logger,
    *,
    ticket_id: str,
    confirmed: bool,
    root_dir: Path | str = ".",
) -> int:
    root = Path(root_dir)
    document = read_json(root / TICKET_JSON)
    reasons = _config_reasons(config)
    if not document:
        reasons.append("saved paper ticket is missing")
    else:
        reasons.extend(verify_ticket_document(document))
        if not confirmed:
            reasons.append("--confirm-vol-targeted-growth-paper is required")
        if ticket_id != str(document.get("ticket_id", "")):
            reasons.append("supplied ticket ID does not match the saved ticket")
        payload = document.get("payload", {})
        if not isinstance(payload, dict) or payload.get("execution_ready") is not True:
            reasons.append("saved ticket is not execution-ready")
    if ticket_already_recorded(root, ticket_id):
        reasons.append("this ticket already has a local execution record")

    broker: BrokerState | None = None
    client: TradingClient | None = None
    if not reasons and document:
        try:
            runtime_now = datetime.now(timezone.utc)
            client = _paper_client(config)
            broker = collect_broker_state(client, now=runtime_now)
            reasons.extend(
                execution_preflight_reasons(
                    document,
                    broker,
                    supplied_ticket_id=ticket_id,
                    confirmed=confirmed,
                    now=runtime_now,
                )
            )
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"fresh Alpaca paper preflight failed safely: {type(exc).__name__}")

    kill_switch = evaluate_paper_kill_switch_gate(
        alpaca_paper=config.alpaca_paper,
        allow_shorting=config.allow_shorting,
        paper_kill_switch_enabled=config.paper_kill_switch_enabled,
        execution_eligibility_blocked=bool(reasons),
        defensive_decision_blocked=bool(reasons),
        explicit_confirmation=confirmed,
        command_name="execute_vol_targeted_growth_paper",
        dry_run=config.dry_run,
        explicit_paper_execution_requested=confirmed,
    )
    if not kill_switch.allowed:
        reasons.extend(kill_switch.reasons)
    reasons = list(dict.fromkeys(reasons))
    if reasons or not document or broker is None or client is None:
        write_execution_outputs(root, ticket_id, "blocked", [], reasons)
        _print_blocked("Volatility-targeted paper execution blocked", reasons)
        return 2

    payload = document["payload"]
    results: list[dict[str, str]] = []
    for index, order in enumerate(payload.get("orders", []), start=1):
        try:
            submission = submit_paper_order(
                client,
                PaperOrderRequest(
                    route=PaperOrderRoute.VOL_TARGETED_GROWTH,
                    ticker=str(order["symbol"]),
                    side=str(order["side"]),
                    quantity=safe_decimal(order["quantity"]),
                    confirmed=confirmed,
                    alpaca_paper=config.alpaca_paper,
                    client_order_id=_client_order_id(ticket_id, index, str(order["symbol"])),
                ),
            )
            status = refresh_order_status(
                client,
                logger,
                submission.order_id,
                normalize_order_status(submission.initial_status),
                timeout_seconds=15,
            )
            results.append(
                execution_row(
                    index,
                    order,
                    order_id=submission.order_id,
                    client_order_id=_client_order_id(ticket_id, index, str(order["symbol"])),
                    status=status,
                )
            )
            if status != "filled":
                reasons.append(
                    f"{order['symbol']} order did not reach filled status; remaining ticket orders were stopped"
                )
                break
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"{order.get('symbol', 'unknown')} submission failed safely: {type(exc).__name__}")
            break

    final_status = "filled" if results and len(results) == len(payload.get("orders", [])) and not reasons else "partial_or_failed"
    write_execution_outputs(root, ticket_id, final_status, results, reasons)
    if final_status != "filled":
        _print_blocked("Paper basket did not complete", reasons)
        return 1

    print(f"Paper ticket {ticket_id} completed with {len(results)} filled order(s).")
    print("Run the explicitly confirmed read-only postcheck next.")
    return 0


def run_vol_targeted_growth_paper_postcheck(
    config: AppConfig,
    logger: logging.Logger,
    *,
    confirm_readonly_alpaca_check: bool,
    root_dir: Path | str = ".",
) -> int:
    root = Path(root_dir)
    document = read_json(root / TICKET_JSON)
    reasons = _config_reasons(config)
    if not confirm_readonly_alpaca_check:
        reasons.append("--confirm-readonly-alpaca-check is required")
    if not document:
        reasons.append("saved paper ticket is missing")
    else:
        reasons.extend(verify_ticket_document(document))
    if reasons:
        _print_blocked("Paper postcheck blocked", reasons)
        return 2

    try:
        broker = collect_broker_state(_paper_client(config))
        payload = document["payload"]
        rows: list[dict[str, str]] = []
        aligned = True
        for target in payload.get("targets", []):
            symbol = str(target["symbol"])
            target_quantity = safe_decimal(target["target_quantity"])
            actual_quantity = broker.positions.get(symbol, Decimal("0"))
            difference = actual_quantity - target_quantity
            reference_price = safe_decimal(target.get("reference_price", "0"))
            residual_notional = abs(difference) * reference_price
            symbol_aligned = (
                abs(difference) <= Decimal("0.00001")
                or residual_notional < MIN_ORDER_NOTIONAL_USD
            )
            aligned = aligned and symbol_aligned
            rows.append(
                {
                    "symbol": symbol,
                    "target_quantity": decimal_text(target_quantity),
                    "actual_quantity": decimal_text(actual_quantity),
                    "difference": decimal_text(difference),
                    "residual_notional": decimal_text(residual_notional),
                    "aligned": str(symbol_aligned),
                }
            )
        if broker.open_order_symbols:
            aligned = False
            reasons.append("open Alpaca paper orders remain after execution")
        execution = read_json(root / EXECUTION_JSON)
        if not execution or execution.get("ticket_id") != document.get("ticket_id"):
            aligned = False
            reasons.append("matching execution record is missing")
        elif execution.get("status") != "filled":
            aligned = False
            reasons.append("matching execution record is not fully filled")
        write_postcheck_outputs(root, str(document["ticket_id"]), aligned, rows, reasons)
    except Exception as exc:  # noqa: BLE001
        logger.error("Volatility-targeted paper postcheck failed safely: %s", type(exc).__name__)
        print(f"Paper postcheck failed safely: {type(exc).__name__}")
        return 1

    print(f"Paper postcheck status: {'aligned' if aligned else 'manual review required'}")
    for row in rows:
        print(
            f"{row['symbol']}: target={row['target_quantity']} actual={row['actual_quantity']} "
            f"aligned={row['aligned']}"
        )
    return 0 if aligned else 2


def run_vol_targeted_growth_auto_paper(
    config: AppConfig,
    logger: logging.Logger,
    *,
    root_dir: Path | str = ".",
    now: datetime | None = None,
) -> int:
    """Run one explicitly enabled, fail-closed paper rebalance per U.S. session."""

    root = Path(root_dir)
    run_now = _aware_utc(now or datetime.now(timezone.utc))
    market_now = run_now.astimezone(AUTO_TIMEZONE)
    session_date = market_now.date().isoformat()
    cycle_id = f"vtga-{market_now:%Y%m%d}"
    reasons = _config_reasons(config)
    auto_execution_authorized = getattr(config, "auto_paper_trading_enabled", False) is True
    if not auto_execution_authorized:
        reasons.append("auto_paper_trading_enabled must be explicitly true")
    if not _inside_auto_window(market_now):
        reasons.append("automatic paper execution is allowed only from 10:00 through 10:20 America/New_York")

    existing_state = read_json(root / AUTO_STATE_JSON)
    if existing_state.get("session_date") == session_date:
        reasons.append(
            f"automatic paper cycle already recorded for {session_date} with status "
            f"{existing_state.get('status', 'unknown')}"
        )
    if reasons:
        return _finish_auto_blocked(config, logger, session_date, cycle_id, reasons)

    if not acquire_auto_lease(root, session_date, cycle_id, run_now):
        write_auto_state(root, session_date, cycle_id, "blocked_existing_lease", "none", 0, False)
        return _finish_auto_blocked(
            config,
            logger,
            session_date,
            cycle_id,
            ["automatic paper cycle lease already exists; manual review is required before any retry"],
        )

    try:
        client = _paper_client(config)
        broker = collect_broker_state(client, now=run_now)
    except Exception as exc:  # noqa: BLE001 - fail closed without sensitive details
        write_auto_state(root, session_date, cycle_id, "blocked_broker_preflight", "none", 0, False)
        return _finish_auto_blocked(
            config,
            logger,
            session_date,
            cycle_id,
            [f"fresh Alpaca paper preflight failed safely: {type(exc).__name__}"],
        )

    if not broker.market_open:
        write_auto_state(root, session_date, cycle_id, "skipped_market_closed", "none", 0, False)
        message = f"AUTO PAPER REBALANCE SKIPPED\nsession={session_date}\nreason=Alpaca paper market is closed"
        send_discord_alert(config, logger, message)
        print(message)
        return 0

    try:
        volatility = load_live_volatility_snapshot(root, now=run_now)
        document = build_ticket_document(volatility, broker, now=run_now)
        write_ticket_outputs(root, document)
    except Exception as exc:  # noqa: BLE001
        write_auto_state(root, session_date, cycle_id, "blocked_ticket_preparation", "none", 0, False)
        return _finish_auto_blocked(
            config,
            logger,
            session_date,
            cycle_id,
            [f"automatic paper ticket preparation failed safely: {type(exc).__name__}"],
        )

    payload = document["payload"]
    blockers = list(payload.get("blockers", []))
    if not payload.get("orders") and blockers == [NO_ORDERS_REQUIRED]:
        rows, aligned, postcheck_reasons = _position_reconciliation(document, broker)
        write_execution_outputs(root, str(document["ticket_id"]), "no_action", [], [NO_ORDERS_REQUIRED])
        write_postcheck_outputs(root, str(document["ticket_id"]), aligned, rows, postcheck_reasons)
        status = "no_action_aligned" if aligned else "no_action_manual_review_required"
        write_auto_state(root, session_date, cycle_id, status, str(document["ticket_id"]), 0, aligned)
        message = (
            f"AUTO PAPER REBALANCE {'NO ACTION' if aligned else 'REVIEW REQUIRED'}\n"
            f"session={session_date}\norders=0\npostcheck={'aligned' if aligned else 'manual_review_required'}"
        )
        send_discord_alert(config, logger, message)
        print(message)
        return 0 if aligned else 2

    reasons = execution_preflight_reasons(
        document,
        broker,
        supplied_ticket_id=str(document["ticket_id"]),
        confirmed=True,
        now=run_now,
    )
    if any(client_id.startswith(f"{cycle_id}-") for client_id in broker.recent_client_order_ids):
        reasons.append("this session already has a matching automatic Alpaca client order ID")
    kill_switch = evaluate_paper_kill_switch_gate(
        alpaca_paper=config.alpaca_paper,
        allow_shorting=config.allow_shorting,
        paper_kill_switch_enabled=config.paper_kill_switch_enabled,
        execution_eligibility_blocked=bool(reasons),
        defensive_decision_blocked=bool(reasons),
        explicit_confirmation=auto_execution_authorized,
        command_name="run_vol_targeted_growth_auto_paper",
        dry_run=config.dry_run,
        explicit_paper_execution_requested=auto_execution_authorized,
    )
    if not kill_switch.allowed:
        reasons.extend(kill_switch.reasons)
    reasons = list(dict.fromkeys(reasons))
    if reasons:
        write_auto_state(
            root,
            session_date,
            cycle_id,
            "blocked_preflight",
            str(document["ticket_id"]),
            0,
            False,
        )
        return _finish_auto_blocked(config, logger, session_date, cycle_id, reasons)

    # The durable lease is written before the first broker submission. Any crash
    # after this point blocks automatic retries for the session.
    write_auto_state(
        root,
        session_date,
        cycle_id,
        "submission_started",
        str(document["ticket_id"]),
        0,
        False,
    )
    results: list[dict[str, str]] = []
    execution_reasons: list[str] = []
    for index, order in enumerate(payload.get("orders", []), start=1):
        try:
            client_order_id = _client_order_id(cycle_id, index, str(order["symbol"]))
            submission = submit_paper_order(
                client,
                PaperOrderRequest(
                    route=PaperOrderRoute.VOL_TARGETED_GROWTH,
                    ticker=str(order["symbol"]),
                    side=str(order["side"]),
                    quantity=safe_decimal(order["quantity"]),
                    confirmed=auto_execution_authorized,
                    alpaca_paper=config.alpaca_paper,
                    client_order_id=client_order_id,
                ),
            )
            order_status = refresh_order_status(
                client,
                logger,
                submission.order_id,
                normalize_order_status(submission.initial_status),
                timeout_seconds=15,
            )
            results.append(
                execution_row(
                    index,
                    order,
                    order_id=submission.order_id,
                    client_order_id=client_order_id,
                    status=order_status,
                )
            )
            if order_status != "filled":
                execution_reasons.append(
                    f"{order['symbol']} order did not reach filled status; remaining automatic orders were stopped"
                )
                break
        except Exception as exc:  # noqa: BLE001
            execution_reasons.append(
                f"{order.get('symbol', 'unknown')} automatic submission failed safely: {type(exc).__name__}"
            )
            break

    filled = bool(results) and len(results) == len(payload.get("orders", [])) and not execution_reasons
    execution_status = "filled" if filled else "partial_or_failed"
    write_execution_outputs(root, str(document["ticket_id"]), execution_status, results, execution_reasons)
    if not filled:
        write_auto_state(
            root,
            session_date,
            cycle_id,
            "partial_or_failed_manual_review_required",
            str(document["ticket_id"]),
            len(results),
            False,
        )
        message = (
            f"AUTO PAPER REBALANCE FAILED\nsession={session_date}\n"
            f"submitted={len(results)}\nmanual_review_required=true"
        )
        send_discord_alert(config, logger, message)
        print(message)
        return 1

    try:
        final_broker = collect_broker_state(client)
        postcheck_rows, aligned, postcheck_reasons = _position_reconciliation(document, final_broker)
        write_postcheck_outputs(
            root,
            str(document["ticket_id"]),
            aligned,
            postcheck_rows,
            postcheck_reasons,
        )
    except Exception as exc:  # noqa: BLE001
        aligned = False
        postcheck_reasons = [f"automatic postcheck failed safely: {type(exc).__name__}"]

    final_status = "filled_aligned" if aligned else "filled_postcheck_manual_review_required"
    write_auto_state(
        root,
        session_date,
        cycle_id,
        final_status,
        str(document["ticket_id"]),
        len(results),
        aligned,
    )
    message = (
        f"AUTO PAPER REBALANCE {'COMPLETE' if aligned else 'REVIEW REQUIRED'}\n"
        f"session={session_date}\norders={len(results)}\n"
        f"postcheck={'aligned' if aligned else 'manual_review_required'}"
    )
    send_discord_alert(config, logger, message)
    print(message)
    return 0 if aligned else 2


def collect_broker_state(client: TradingClient, *, now: datetime | None = None) -> BrokerState:
    captured_at = now or datetime.now(timezone.utc)
    account = client.get_account()
    clock = client.get_clock()
    raw_positions = list(client.get_all_positions())
    open_orders = list(client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN)))
    recent_orders = list(
        client.get_orders(
            filter=GetOrdersRequest(
                status=QueryOrderStatus.CLOSED,
                limit=500,
                after=captured_at - timedelta(days=1),
                direction=Sort.DESC,
            )
        )
    )
    positions: dict[str, Decimal] = {}
    market_values: dict[str, Decimal] = {}
    for position in raw_positions:
        symbol = str(getattr(position, "symbol", "")).strip().upper()
        if not symbol:
            continue
        quantity = safe_decimal(getattr(position, "qty", "0"))
        side = _enum_text(getattr(position, "side", "")).lower()
        positions[symbol] = -abs(quantity) if side == "short" else quantity
        market_values[symbol] = safe_decimal(getattr(position, "market_value", "0"))

    assets: dict[str, AssetState] = {}
    for symbol in MANAGED_SYMBOLS:
        asset = client.get_asset(symbol)
        assets[symbol] = AssetState(
            symbol=symbol,
            asset_class=_enum_text(getattr(asset, "asset_class", "")),
            tradable=getattr(asset, "tradable", False) is True,
            fractionable=getattr(asset, "fractionable", False) is True,
        )

    return BrokerState(
        captured_at=captured_at,
        market_open=bool(getattr(clock, "is_open", False)),
        account_status=_enum_text(getattr(account, "status", "")),
        account_blocked=bool(getattr(account, "account_blocked", False)),
        trading_blocked=bool(getattr(account, "trading_blocked", False)),
        trade_suspended_by_user=bool(getattr(account, "trade_suspended_by_user", False)),
        cash=safe_decimal(getattr(account, "cash", "0")),
        equity=safe_decimal(getattr(account, "equity", "0")),
        buying_power=safe_decimal(getattr(account, "buying_power", "0")),
        positions=positions,
        position_market_values=market_values,
        open_order_symbols=tuple(
            str(getattr(order, "symbol", "")).strip().upper() or "UNKNOWN" for order in open_orders
        ),
        recent_client_order_ids=tuple(
            str(getattr(order, "client_order_id", "")) for order in [*open_orders, *recent_orders]
            if getattr(order, "client_order_id", "")
        ),
        assets=assets,
    )


def _position_reconciliation(
    document: dict[str, Any],
    broker: BrokerState,
) -> tuple[list[dict[str, str]], bool, list[str]]:
    payload = document.get("payload", {})
    rows: list[dict[str, str]] = []
    reasons: list[str] = []
    aligned = True
    for target in payload.get("targets", []):
        symbol = str(target["symbol"])
        target_quantity = safe_decimal(target["target_quantity"])
        actual_quantity = broker.positions.get(symbol, Decimal("0"))
        difference = actual_quantity - target_quantity
        reference_price = safe_decimal(target.get("reference_price", "0"))
        residual_notional = abs(difference) * reference_price
        symbol_aligned = (
            abs(difference) <= Decimal("0.00001")
            or residual_notional < MIN_ORDER_NOTIONAL_USD
        )
        aligned = aligned and symbol_aligned
        rows.append(
            {
                "symbol": symbol,
                "target_quantity": decimal_text(target_quantity),
                "actual_quantity": decimal_text(actual_quantity),
                "difference": decimal_text(difference),
                "residual_notional": decimal_text(residual_notional),
                "aligned": str(symbol_aligned),
            }
        )
    if broker.open_order_symbols:
        aligned = False
        reasons.append("open Alpaca paper orders remain after automatic execution")
    if not aligned and not reasons:
        reasons.append("one or more managed paper positions are not aligned")
    return rows, aligned, reasons


def acquire_auto_lease(
    root: Path,
    session_date: str,
    cycle_id: str,
    started_at: datetime,
) -> bool:
    lease_path = root / "data" / f"vol_targeted_growth_auto_paper_{session_date}.lock"
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    lease = {
        "session_date": session_date,
        "cycle_id": cycle_id,
        "started_at": _aware_utc(started_at).isoformat(),
        "purpose": "single-session automatic Alpaca paper execution lease",
    }
    try:
        with lease_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(lease, sort_keys=True) + "\n")
    except FileExistsError:
        return False
    return True


def write_auto_state(
    root: Path,
    session_date: str,
    cycle_id: str,
    status: str,
    ticket_id: str,
    submitted_order_count: int,
    postcheck_aligned: bool,
) -> None:
    state = {
        "session_date": session_date,
        "cycle_id": cycle_id,
        "status": status,
        "ticket_id": ticket_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "submitted_order_count": submitted_order_count,
        "postcheck_aligned": postcheck_aligned,
        "paper_only": True,
        "auto_paper_trading_enabled": True,
        "live_trading_approved": False,
    }
    write_json_atomic(root / AUTO_STATE_JSON, state)
    write_summary(
        root / AUTO_SUMMARY,
        {
            "session_date": session_date,
            "cycle_id": cycle_id,
            "status": status,
            "ticket_id": ticket_id,
            "submitted_order_count": submitted_order_count,
            "postcheck_aligned": postcheck_aligned,
            "paper_only": True,
            "auto_paper_scheduling_approved": True,
            "live_trading_approved": False,
        },
    )


def _finish_auto_blocked(
    config: AppConfig,
    logger: logging.Logger,
    session_date: str,
    cycle_id: str,
    reasons: list[str],
) -> int:
    safe_reasons = list(dict.fromkeys(str(reason) for reason in reasons))
    message = (
        f"AUTO PAPER REBALANCE BLOCKED\nsession={session_date}\ncycle={cycle_id}\n"
        f"reason={' | '.join(safe_reasons[:3])}\norders_submitted=0"
    )
    send_discord_alert(config, logger, message)
    print(message)
    return 2


def _inside_auto_window(value: datetime) -> bool:
    minute = value.hour * 60 + value.minute
    return AUTO_WINDOW_START_MINUTE <= minute <= AUTO_WINDOW_END_MINUTE


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def write_ticket_outputs(root: Path, document: dict[str, Any]) -> None:
    payload = document["payload"]
    write_json(root / TICKET_JSON, document)
    rows = [
        {
            "ticket_id": document["ticket_id"],
            **target,
            "execution_ready": str(payload["execution_ready"]),
        }
        for target in payload.get("targets", [])
    ]
    write_csv(root / TICKET_CSV, rows)
    write_summary(
        root / TICKET_SUMMARY,
        {
            "ticket_id": document["ticket_id"],
            "strategy_name": payload["strategy_name"],
            "paper_capital_usd": payload["paper_capital_usd"],
            "allocation_capital_usd": payload["allocation_capital_usd"],
            "realized_volatility": payload["realized_volatility"],
            "exposure_multiplier": payload["exposure_multiplier"],
            "cash_weight": payload["cash_weight"],
            "market_open": payload["market_open"],
            "prices_fresh": payload["prices_fresh"],
            "order_count": len(payload.get("orders", [])),
            "execution_ready": payload["execution_ready"],
            "blockers": ";".join(payload.get("blockers", [])) or "none",
            "live_trading_approved": False,
            "scheduling_approved": False,
        },
    )


def write_execution_outputs(
    root: Path,
    ticket_id: str,
    status: str,
    rows: list[dict[str, str]],
    reasons: list[str],
) -> None:
    document = {
        "ticket_id": ticket_id,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "orders": rows,
        "reasons": reasons,
        "live_trading_approved": False,
        "scheduling_approved": False,
    }
    write_json(root / EXECUTION_JSON, document)
    write_csv(root / EXECUTION_CSV, rows)
    write_summary(
        root / EXECUTION_SUMMARY,
        {
            "ticket_id": ticket_id,
            "execution_status": status,
            "submitted_order_count": len(rows),
            "filled_order_count": sum(1 for row in rows if row.get("status") == "filled"),
            "reasons": ";".join(reasons) or "none",
            "paper_execution_command_confirmed": status in {"filled", "partial_or_failed"},
            "live_trading_approved": False,
            "scheduling_approved": False,
        },
    )


def write_postcheck_outputs(
    root: Path,
    ticket_id: str,
    aligned: bool,
    rows: list[dict[str, str]],
    reasons: list[str],
) -> None:
    document = {
        "ticket_id": ticket_id,
        "status": "aligned" if aligned else "manual_review_required",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "positions": rows,
        "reasons": reasons,
        "orders_submitted": False,
    }
    write_json(root / POSTCHECK_JSON, document)
    write_csv(root / POSTCHECK_CSV, rows)
    write_summary(
        root / POSTCHECK_SUMMARY,
        {
            "ticket_id": ticket_id,
            "postcheck_status": document["status"],
            "aligned_symbol_count": sum(1 for row in rows if row.get("aligned") == "True"),
            "symbol_count": len(rows),
            "orders_submitted": False,
            "live_trading_approved": False,
            "scheduling_approved": False,
        },
    )


def execution_row(
    index: int,
    order: dict[str, Any],
    *,
    order_id: str,
    client_order_id: str,
    status: str,
) -> dict[str, str]:
    return {
        "sequence": str(index),
        "symbol": str(order["symbol"]),
        "side": str(order["side"]),
        "quantity": str(order["quantity"]),
        "reference_price": str(order["reference_price"]),
        "estimated_notional": str(order["estimated_notional"]),
        "client_order_id": client_order_id,
        "broker_order_id": order_id,
        "status": status,
    }


def ticket_already_recorded(root: Path, ticket_id: str) -> bool:
    execution = read_json(root / EXECUTION_JSON)
    return bool(execution and execution.get("ticket_id") == ticket_id and execution.get("orders"))


def _paper_client(config: AppConfig) -> TradingClient:
    return TradingClient(config.alpaca_api_key, config.alpaca_secret_key, paper=True)


def _config_reasons(config: AppConfig) -> list[str]:
    reasons: list[str] = []
    if config.alpaca_paper is not True:
        reasons.append("alpaca.paper must be true")
    if config.allow_shorting is not False:
        reasons.append("allow_shorting must remain false")
    if not config.alpaca_api_key or not config.alpaca_secret_key:
        reasons.append("Alpaca paper credentials are required")
    return reasons


def _client_order_id(ticket_id: str, index: int, symbol: str) -> str:
    return f"{ticket_id}-{index}-{symbol.lower()}"


def _enum_text(value: Any) -> str:
    text = str(getattr(value, "value", value))
    return text.rsplit(".", 1)[-1] if "." in text else text


def _print_ticket(document: dict[str, Any]) -> None:
    payload = document["payload"]
    print("Volatility-targeted Alpaca paper ticket prepared. No orders were submitted.")
    print(f"ticket_id={document['ticket_id']}")
    print(f"paper_capital_usd={payload['paper_capital_usd']}")
    print(f"allocation_capital_usd={payload['allocation_capital_usd']}")
    print(f"realized_volatility={payload['realized_volatility']}")
    print(f"exposure_multiplier={payload['exposure_multiplier']}")
    print(f"cash_weight={payload['cash_weight']}")
    print(f"market_open={payload['market_open']}")
    print(f"prices_fresh={payload['prices_fresh']}")
    print(f"execution_ready={payload['execution_ready']}")
    for order in payload.get("orders", []):
        print(
            f"{order['symbol']} {order['side'].upper()} {order['quantity']} "
            f"(~${order['estimated_notional']} at ${order['reference_price']})"
        )
    if payload.get("blockers"):
        print("Blockers:")
        for reason in payload["blockers"]:
            print(f"- {reason}")
    print("live_trading_approved=false; scheduling_approved=false")


def _print_blocked(title: str, reasons: list[str]) -> None:
    print(title)
    for reason in reasons:
        print(f"- {reason}")
    print("No orders were created, submitted, cancelled, or replaced.")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else ["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows or [{"status": "no_rows"}])


def write_summary(path: Path, values: dict[str, Any]) -> None:
    rows = [
        {"summary_name": name, "summary_value": str(value), "details": "volatility-targeted paper workflow"}
        for name, value in values.items()
    ]
    write_csv(path, rows)
