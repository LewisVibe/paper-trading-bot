"""Pure ticket planning and validation for volatility-targeted paper execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Any

from trading_bot.strategies.vol_targeted_growth import (
    MANAGED_SYMBOLS,
    PAPER_CAPITAL_USD,
    PRICE_FRESHNESS_MINUTES,
    QUANTITY_INCREMENT,
    SLEEVES,
    STRATEGY_NAME,
    VolatilitySnapshot,
)


TICKET_SCHEMA_VERSION = 2
TICKET_TTL_MINUTES = 15
MIN_ORDER_NOTIONAL_USD = Decimal("1.00")
BUY_CASH_BUFFER = Decimal("1.00")
SELL_PROCEEDS_HAIRCUT = Decimal("1.00")
NO_LEVERAGE_TOLERANCE = Decimal("1.0001")
MAX_PRICE_CLOCK_SKEW_MINUTES = Decimal("2")


@dataclass(frozen=True)
class AssetState:
    symbol: str
    asset_class: str
    tradable: bool
    fractionable: bool


@dataclass(frozen=True)
class BrokerState:
    captured_at: datetime
    market_open: bool
    account_status: str
    account_blocked: bool
    trading_blocked: bool
    trade_suspended_by_user: bool
    cash: Decimal
    equity: Decimal
    buying_power: Decimal
    positions: dict[str, Decimal]
    position_market_values: dict[str, Decimal]
    open_order_symbols: tuple[str, ...]
    recent_client_order_ids: tuple[str, ...]
    assets: dict[str, AssetState]


def build_ticket_document(
    volatility: VolatilitySnapshot,
    broker: BrokerState,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    generated_at = _aware_utc(now or datetime.now(timezone.utc))
    allocation_capital = _allocation_capital(broker)
    targets, orders, calculation_blockers = _build_targets_and_orders(
        volatility,
        broker,
        allocation_capital,
    )
    blockers = _broker_blockers(volatility, broker, targets, orders)
    blockers.extend(calculation_blockers)
    blockers = list(dict.fromkeys(blockers))
    execution_ready = not blockers and bool(orders)

    managed_positions = {
        symbol: decimal_text(broker.positions.get(symbol, Decimal("0")))
        for symbol in MANAGED_SYMBOLS
    }
    unrelated_symbols = sorted(
        symbol for symbol, quantity in broker.positions.items()
        if symbol not in MANAGED_SYMBOLS and quantity != 0
    )
    payload: dict[str, Any] = {
        "schema_version": TICKET_SCHEMA_VERSION,
        "strategy_name": STRATEGY_NAME,
        "paper_capital_usd": decimal_text(PAPER_CAPITAL_USD),
        "allocation_capital_usd": decimal_text(allocation_capital),
        "generated_at": generated_at.isoformat(),
        "expires_at": (generated_at + timedelta(minutes=TICKET_TTL_MINUTES)).isoformat(),
        "market_data_as_of": volatility.market_data_as_of,
        "price_timestamp": volatility.price_timestamp.isoformat(),
        "price_age_minutes": decimal_text(volatility.price_age_minutes),
        "prices_fresh": volatility.prices_fresh,
        "realized_volatility": decimal_text(volatility.realized_volatility),
        "target_volatility": "0.15",
        "volatility_window_days": 20,
        "exposure_multiplier": decimal_text(volatility.exposure_multiplier),
        "cash_weight": decimal_text(volatility.cash_weight),
        "broker_snapshot_at": _aware_utc(broker.captured_at).isoformat(),
        "market_open": broker.market_open,
        "account_status": normalized_account_status(broker.account_status),
        "account_cash": decimal_text(broker.cash),
        "account_equity": decimal_text(broker.equity),
        "account_buying_power": decimal_text(broker.buying_power),
        "managed_positions": managed_positions,
        "unrelated_positions": {
            symbol: decimal_text(quantity)
            for symbol, quantity in sorted(broker.positions.items())
            if symbol not in MANAGED_SYMBOLS and quantity != 0
        },
        "unrelated_position_symbols": unrelated_symbols,
        "unrelated_position_market_value": decimal_text(_unrelated_market_value(broker)),
        "open_order_count": len(broker.open_order_symbols),
        "open_order_symbols": sorted(set(broker.open_order_symbols)),
        "targets": targets,
        "orders": orders,
        "estimated_buy_notional": decimal_text(_order_notional(orders, "buy")),
        "estimated_sell_notional": decimal_text(_order_notional(orders, "sell")),
        "execution_ready": execution_ready,
        "blockers": blockers,
        "live_trading_approved": False,
        "scheduling_approved": False,
        "never_schedule_order_capable_commands": True,
    }
    return {"ticket_id": ticket_id_for_payload(payload), "payload": payload}


def ticket_id_for_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"vtg-{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:20]}"


def verify_ticket_document(document: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    ticket_id = str(document.get("ticket_id", ""))
    payload = document.get("payload")
    if not isinstance(payload, dict):
        return ["ticket payload is missing or invalid"]
    if payload.get("schema_version") != TICKET_SCHEMA_VERSION:
        reasons.append("ticket schema version is unsupported")
    if payload.get("strategy_name") != STRATEGY_NAME:
        reasons.append("ticket strategy does not match the approved volatility seed")
    if payload.get("paper_capital_usd") != decimal_text(PAPER_CAPITAL_USD):
        reasons.append("ticket paper capital is not the approved $100,000 cap")
    allocation_capital = safe_decimal(payload.get("allocation_capital_usd", "-1"))
    if allocation_capital < 0 or allocation_capital > PAPER_CAPITAL_USD:
        reasons.append("ticket allocation capital is outside the approved paper cap")
    if ticket_id != ticket_id_for_payload(payload):
        reasons.append("ticket hash does not match its saved payload")
    if payload.get("live_trading_approved") is not False:
        reasons.append("live trading must remain false")
    if payload.get("scheduling_approved") is not False:
        reasons.append("scheduling must remain false")
    reasons.extend(_ticket_semantic_reasons(payload))
    return reasons


def _ticket_semantic_reasons(payload: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    allocation_capital = strict_decimal(payload.get("allocation_capital_usd"))
    account_equity = strict_decimal(payload.get("account_equity"))
    unrelated_market_value = strict_decimal(payload.get("unrelated_position_market_value"))
    exposure = strict_decimal(payload.get("exposure_multiplier"))
    managed_positions = payload.get("managed_positions")
    unrelated_positions = payload.get("unrelated_positions")
    targets = payload.get("targets")
    orders = payload.get("orders")
    blockers = payload.get("blockers")

    if None in {allocation_capital, account_equity, unrelated_market_value, exposure}:
        return ["ticket contains invalid capital or exposure values"]
    assert allocation_capital is not None
    assert account_equity is not None
    assert unrelated_market_value is not None
    assert exposure is not None
    if not Decimal("0") <= exposure <= Decimal("1"):
        reasons.append("ticket exposure multiplier is outside the long-only 0x-to-1x range")
    expected_allocation = min(
        PAPER_CAPITAL_USD,
        max(Decimal("0"), account_equity - unrelated_market_value),
    ).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if allocation_capital != expected_allocation:
        reasons.append("ticket allocation capital does not match saved non-leveraged account capacity")
    if not isinstance(managed_positions, dict) or set(managed_positions) != set(MANAGED_SYMBOLS):
        reasons.append("ticket managed-position scope is not exactly QQQ, MGK, IBIT, and SGOV")
        return reasons
    if not isinstance(unrelated_positions, dict):
        reasons.append("ticket unrelated-position snapshot is invalid")
        return reasons
    if (
        not isinstance(targets, list)
        or not isinstance(orders, list)
        or not all(isinstance(row, dict) for row in [*targets, *orders])
    ):
        reasons.append("ticket targets or orders are invalid")
        return reasons
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        reasons.append("ticket blocker list is invalid")
        return reasons
    if payload.get("execution_ready") is True and (blockers or not orders):
        reasons.append("ticket cannot be execution-ready while blocked or empty")

    target_symbols = [str(row.get("symbol", "")) for row in targets]
    if target_symbols != list(MANAGED_SYMBOLS):
        reasons.append("ticket target scope or order is not exactly the approved four symbols")
        return reasons

    prices: dict[str, Decimal] = {}
    positions: dict[str, Decimal] = {}
    for row in targets:
        symbol = str(row["symbol"])
        price = strict_decimal(row.get("reference_price"))
        position = strict_decimal(managed_positions.get(symbol))
        if price is None or position is None:
            reasons.append("ticket target contains an invalid price or position quantity")
            return reasons
        prices[symbol] = price
        positions[symbol] = position
    for symbol, quantity in unrelated_positions.items():
        parsed = strict_decimal(quantity)
        if parsed is None:
            reasons.append("ticket unrelated-position quantity is invalid")
            return reasons
        if parsed != 0:
            positions[str(symbol)] = parsed

    effective_weights = {
        sleeve.symbol: (sleeve.base_weight * exposure).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        for sleeve in SLEEVES
    }
    snapshot = VolatilitySnapshot(
        calculated_at=datetime.now(timezone.utc),
        market_data_as_of=str(payload.get("market_data_as_of", "")),
        price_timestamp=datetime.now(timezone.utc),
        prices=prices,
        realized_volatility=Decimal("0"),
        exposure_multiplier=exposure,
        effective_weights=effective_weights,
        cash_weight=max(Decimal("0"), Decimal("1") - sum(effective_weights.values())),
        return_observation_count=20,
        price_age_minutes=Decimal("0"),
        prices_fresh=True,
    )
    broker = BrokerState(
        captured_at=datetime.now(timezone.utc),
        market_open=True,
        account_status="active",
        account_blocked=False,
        trading_blocked=False,
        trade_suspended_by_user=False,
        cash=Decimal("0"),
        equity=account_equity,
        buying_power=Decimal("0"),
        positions=positions,
        position_market_values={},
        open_order_symbols=(),
        recent_client_order_ids=(),
        assets={},
    )
    expected_targets, expected_orders, calculation_blockers = _build_targets_and_orders(
        snapshot,
        broker,
        allocation_capital,
    )
    if targets != expected_targets or orders != expected_orders:
        reasons.append("ticket targets or orders do not match the approved deterministic calculation")
    if payload.get("execution_ready") is True and calculation_blockers:
        reasons.append("ticket cannot be execution-ready with calculation blockers")
    return reasons


def execution_preflight_reasons(
    document: dict[str, Any],
    broker: BrokerState,
    *,
    supplied_ticket_id: str,
    confirmed: bool,
    now: datetime | None = None,
) -> list[str]:
    reasons = verify_ticket_document(document)
    payload = document.get("payload") if isinstance(document.get("payload"), dict) else {}
    ticket_id = str(document.get("ticket_id", ""))
    current_time = _aware_utc(now or datetime.now(timezone.utc))

    if not confirmed:
        reasons.append("--confirm-vol-targeted-growth-paper is required")
    if supplied_ticket_id != ticket_id:
        reasons.append("supplied ticket ID does not match the saved ticket")
    if payload.get("execution_ready") is not True:
        reasons.append("saved ticket is not execution-ready")
    try:
        expires_at = datetime.fromisoformat(str(payload.get("expires_at", "")))
    except ValueError:
        reasons.append("ticket expiry is missing or invalid")
    else:
        if current_time > _aware_utc(expires_at):
            reasons.append("ticket has expired; prepare and review a fresh ticket")
    try:
        price_timestamp = _aware_utc(datetime.fromisoformat(str(payload.get("price_timestamp", ""))))
    except ValueError:
        reasons.append("ticket price timestamp is missing or invalid")
    else:
        price_age = Decimal(str((current_time - price_timestamp).total_seconds())) / Decimal("60")
        if price_age > PRICE_FRESHNESS_MINUTES:
            reasons.append("ticket intraday prices are older than 15 minutes")
        if price_age < -MAX_PRICE_CLOCK_SKEW_MINUTES:
            reasons.append("ticket price timestamp is unexpectedly in the future")
    if payload.get("prices_fresh") is not True:
        reasons.append("ticket prices were not fresh when prepared")
    if not broker.market_open:
        reasons.append("Alpaca paper market is closed")
    reasons.extend(_account_and_asset_blockers(broker))
    if broker.open_order_symbols:
        reasons.append("one or more Alpaca paper orders are already open")
    if any(client_id.startswith(f"{ticket_id}-") for client_id in broker.recent_client_order_ids):
        reasons.append("this ticket already has a matching recent Alpaca client order ID")

    saved_positions = payload.get("managed_positions", {})
    if not isinstance(saved_positions, dict):
        reasons.append("saved managed-position snapshot is invalid")
    else:
        for symbol in MANAGED_SYMBOLS:
            saved = safe_decimal(saved_positions.get(symbol, "0"))
            current = broker.positions.get(symbol, Decimal("0"))
            if saved != current:
                reasons.append(f"{symbol} paper position changed after ticket preparation")
    saved_unrelated = payload.get("unrelated_positions")
    current_unrelated = {
        symbol: quantity
        for symbol, quantity in broker.positions.items()
        if symbol not in MANAGED_SYMBOLS and quantity != 0
    }
    if not isinstance(saved_unrelated, dict):
        reasons.append("saved unrelated-position snapshot is invalid")
    else:
        normalized_saved_unrelated = {
            str(symbol): safe_decimal(quantity)
            for symbol, quantity in saved_unrelated.items()
            if safe_decimal(quantity) != 0
        }
        if normalized_saved_unrelated != current_unrelated:
            reasons.append("unrelated paper positions changed after ticket preparation")

    targets = payload.get("targets")
    orders = payload.get("orders")
    if (
        not isinstance(targets, list)
        or not isinstance(orders, list)
        or not all(isinstance(row, dict) for row in [*targets, *orders])
    ):
        reasons.append("saved ticket targets or orders are invalid")
    else:
        reasons.extend(_capacity_blockers(broker, targets, orders))
    return list(dict.fromkeys(reasons))


def _build_targets_and_orders(
    volatility: VolatilitySnapshot,
    broker: BrokerState,
    allocation_capital: Decimal,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    targets: list[dict[str, str]] = []
    orders: list[dict[str, str]] = []
    blockers: list[str] = []
    for sleeve in SLEEVES:
        symbol = sleeve.symbol
        price = volatility.prices.get(symbol, Decimal("0"))
        weight = volatility.effective_weights.get(symbol, Decimal("0"))
        current_quantity = broker.positions.get(symbol, Decimal("0"))
        if price <= 0:
            blockers.append(f"{symbol} has no positive current price")
            target_dollars = Decimal("0")
            target_quantity = Decimal("0")
        else:
            target_dollars = (allocation_capital * weight).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            target_quantity = (target_dollars / price).quantize(QUANTITY_INCREMENT, rounding=ROUND_DOWN)
        delta = target_quantity - current_quantity
        side = "buy" if delta > 0 else "sell" if delta < 0 else "hold"
        order_quantity = abs(delta).quantize(QUANTITY_INCREMENT, rounding=ROUND_DOWN)
        estimated_notional = (order_quantity * price).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        if current_quantity < 0:
            blockers.append(f"{symbol} has a short position; manual review is required")
        if side == "sell" and order_quantity > max(current_quantity, Decimal("0")):
            blockers.append(f"{symbol} calculated sell would exceed the current long position")
        if order_quantity <= 0 or estimated_notional < MIN_ORDER_NOTIONAL_USD:
            side = "hold"
            order_quantity = Decimal("0")
            estimated_notional = Decimal("0")

        target = {
            "sleeve_name": sleeve.name,
            "symbol": symbol,
            "base_weight": decimal_text(sleeve.base_weight),
            "effective_weight": decimal_text(weight),
            "reference_price": decimal_text(price),
            "target_dollars": decimal_text(target_dollars),
            "current_quantity": decimal_text(current_quantity),
            "target_quantity": decimal_text(target_quantity),
            "action": side,
            "order_quantity": decimal_text(order_quantity),
            "estimated_notional": decimal_text(estimated_notional),
        }
        targets.append(target)
        if side in {"buy", "sell"}:
            orders.append(
                {
                    "sleeve_name": sleeve.name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": decimal_text(order_quantity),
                    "reference_price": decimal_text(price),
                    "estimated_notional": decimal_text(estimated_notional),
                    "target_quantity": decimal_text(target_quantity),
                }
            )
    orders.sort(key=lambda row: (0 if row["side"] == "sell" else 1, MANAGED_SYMBOLS.index(row["symbol"])))
    return targets, orders, blockers


def _broker_blockers(
    volatility: VolatilitySnapshot,
    broker: BrokerState,
    targets: list[dict[str, str]],
    orders: list[dict[str, str]],
) -> list[str]:
    blockers = _account_and_asset_blockers(broker)
    if not broker.market_open:
        blockers.append("Alpaca paper market is closed")
    if not volatility.prices_fresh:
        blockers.append("intraday prices are older than 15 minutes")
    if broker.open_order_symbols:
        blockers.append("one or more Alpaca paper orders are already open")
    if not orders:
        blockers.append("no paper orders are required for the current target")

    blockers.extend(_capacity_blockers(broker, targets, orders))
    return blockers


def _capacity_blockers(
    broker: BrokerState,
    targets: list[dict[str, Any]],
    orders: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    buys = _order_notional(orders, "buy")
    sells = _order_notional(orders, "sell")
    if broker.cash + (sells * SELL_PROCEEDS_HAIRCUT) < buys * BUY_CASH_BUFFER:
        blockers.append("cash plus estimated sell proceeds cannot fund buys without leverage")

    target_gross = sum(safe_decimal(row.get("target_dollars", "0")) for row in targets)
    final_gross = target_gross + _unrelated_market_value(broker)
    if broker.equity <= 0 or final_gross > broker.equity * NO_LEVERAGE_TOLERANCE:
        blockers.append("target plus unrelated positions would exceed account equity tolerance")
    return blockers


def _account_and_asset_blockers(broker: BrokerState) -> list[str]:
    blockers: list[str] = []
    if normalized_account_status(broker.account_status) != "active":
        blockers.append("Alpaca paper account status is not active")
    if broker.account_blocked or broker.trading_blocked or broker.trade_suspended_by_user:
        blockers.append("Alpaca paper account is blocked or trading-suspended")
    if broker.cash < 0:
        blockers.append("Alpaca paper account cash is negative")
    for symbol in MANAGED_SYMBOLS:
        asset = broker.assets.get(symbol)
        if asset is None:
            blockers.append(f"{symbol} asset status is unavailable")
            continue
        if asset.asset_class.lower() != "us_equity":
            blockers.append(f"{symbol} is not a U.S. equity asset")
        if not asset.tradable:
            blockers.append(f"{symbol} is not tradable")
        if not asset.fractionable:
            blockers.append(f"{symbol} is not fractionable")
    for symbol, quantity in broker.positions.items():
        if quantity < 0:
            blockers.append(f"short paper position detected in {symbol}")
    return blockers


def _order_notional(orders: list[dict[str, Any]], side: str) -> Decimal:
    return sum(
        (safe_decimal(row.get("estimated_notional", "0")) for row in orders if row.get("side") == side),
        Decimal("0"),
    )


def _unrelated_market_value(broker: BrokerState) -> Decimal:
    return sum(
        (
            abs(broker.position_market_values.get(symbol, Decimal("0")))
            for symbol, quantity in broker.positions.items()
            if symbol not in MANAGED_SYMBOLS and quantity != 0
        ),
        Decimal("0"),
    )


def _allocation_capital(broker: BrokerState) -> Decimal:
    non_leveraged_capacity = max(Decimal("0"), broker.equity - _unrelated_market_value(broker))
    return min(PAPER_CAPITAL_USD, non_leveraged_capacity).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def decimal_text(value: Decimal) -> str:
    normalized = Decimal(str(value)).normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")


def safe_decimal(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception:
        return Decimal("0")
    return result if result.is_finite() else Decimal("0")


def strict_decimal(value: Any) -> Decimal | None:
    try:
        result = Decimal(str(value))
    except Exception:
        return None
    return result if result.is_finite() else None


def normalized_account_status(value: Any) -> str:
    text = str(getattr(value, "value", value)).strip().lower()
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
