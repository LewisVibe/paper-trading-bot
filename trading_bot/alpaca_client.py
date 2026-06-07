"""Read-only Alpaca paper client helpers and broker API lookups."""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Any

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest

from trading_bot.positions import decimal_from_any


def get_open_orders_for_ticker(client: TradingClient, ticker: str) -> list[Any]:
    request = GetOrdersRequest(
        status=QueryOrderStatus.OPEN,
        symbols=[ticker],
    )
    return list(client.get_orders(filter=request))


def pending_quantity_for_side(open_orders: list[Any], side: str) -> Decimal:
    total = Decimal("0")
    for order in open_orders:
        order_side = normalize_order_side(getattr(order, "side", ""))
        if order_side != side:
            continue

        quantity = decimal_from_any(getattr(order, "qty", "0"))
        filled_quantity = decimal_from_any(getattr(order, "filled_qty", "0"))
        remaining_quantity = quantity - filled_quantity
        if remaining_quantity > 0:
            total += remaining_quantity
    return total


def normalize_order_side(value: Any) -> str:
    return enum_value(value).lower()


def normalize_order_status(value: Any) -> str:
    text = enum_value(value).lower()
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text


def refresh_order_status(
    client: TradingClient,
    logger: logging.Logger,
    order_id: str,
    current_status: str,
    timeout_seconds: int = 10,
) -> str:
    if not order_id:
        return current_status

    latest_status = current_status
    final_statuses = {"filled", "cancelled", "canceled", "expired", "rejected"}
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        try:
            refreshed_order = client.get_order_by_id(order_id)
            latest_status = normalize_order_status(
                getattr(refreshed_order, "status", latest_status)
            )
            if latest_status in final_statuses:
                break
        except Exception as exc:
            logger.warning("Could not refresh Alpaca order status for %s: %s", order_id, exc)
            break

        time.sleep(1)

    return latest_status


def validate_alpaca_asset_for_order(
    client: TradingClient,
    ticker: str,
    requires_shortable: bool,
) -> tuple[bool, str]:
    try:
        asset = client.get_asset(ticker)
    except Exception as exc:
        return False, f"Alpaca asset lookup failed: {exc}"

    asset_class = enum_value(getattr(asset, "asset_class", "")).lower()
    tradable = getattr(asset, "tradable", False) is True
    shortable = getattr(asset, "shortable", False) is True

    if asset_class != "us_equity":
        return False, f"Alpaca asset is not a U.S. equity: {asset_class or 'unknown'}."

    if not tradable:
        return False, "Alpaca asset exists but is not tradable."

    if requires_shortable and not shortable:
        return False, "Alpaca asset is not shortable, so the bot will not open a short."

    return True, ""


def enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))
