"""Single audited gateway for explicitly confirmed Alpaca paper orders."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


class PaperOrderRoute(str, Enum):
    MANUAL_TEST = "paper_order_test"
    QQQ100 = "execute_qqq100_paper"
    SLOW_SMA = "execute_slow_sma_paper"
    VOL_TARGETED_GROWTH = "execute_vol_targeted_growth_paper"


class PaperOrderRefused(RuntimeError):
    """Raised before broker submission when the paper-order contract is not met."""


@dataclass(frozen=True)
class PaperOrderRequest:
    route: PaperOrderRoute
    ticker: str
    side: str
    quantity: Decimal
    confirmed: bool
    alpaca_paper: bool
    client_order_id: str = ""


@dataclass(frozen=True)
class PaperOrderResult:
    order_id: str
    initial_status: Any
    raw_order: Any


CLIENT_ORDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def build_paper_order_client_order_id(
    *,
    route: PaperOrderRoute,
    intent_key: str,
    ticker: str,
    side: str,
    quantity: Decimal,
) -> str:
    """Build a deterministic, non-secret broker ID for one canonical order intent."""
    if not isinstance(route, PaperOrderRoute):
        raise PaperOrderRefused("A known paper-order route is required for client order ID generation.")
    if not isinstance(intent_key, str):
        raise PaperOrderRefused("Order intent key must be text.")
    if not isinstance(ticker, str):
        raise PaperOrderRefused("Ticker must be text for client order ID generation.")
    if not isinstance(side, str):
        raise PaperOrderRefused("Order side must be text for client order ID generation.")
    if not isinstance(quantity, Decimal):
        raise PaperOrderRefused("Order quantity must be a Decimal.")

    normalized_intent = intent_key.strip()
    normalized_ticker = ticker.strip().upper()
    normalized_side = side.strip().lower()
    if not normalized_intent:
        raise PaperOrderRefused("A non-empty order intent key is required.")
    if not normalized_ticker:
        raise PaperOrderRefused("Ticker is required for client order ID generation.")
    if normalized_side not in {"buy", "sell"}:
        raise PaperOrderRefused("Order side must be 'buy' or 'sell' for client order ID generation.")
    if not quantity.is_finite() or quantity <= 0:
        raise PaperOrderRefused("Order quantity must be a finite positive number.")

    canonical_quantity = str(quantity.normalize())
    canonical_intent = json.dumps(
        [
            route.value,
            normalized_intent,
            normalized_ticker,
            normalized_side,
            canonical_quantity,
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical_intent.encode("utf-8")).hexdigest()[:24]
    ticker_label = re.sub(r"[^a-z0-9]+", "-", normalized_ticker.lower()).strip("-")[:16] or "asset"
    return f"{route.value}-{ticker_label}-{normalized_side}-{digest}"


def submit_paper_order(
    client: TradingClient,
    request: PaperOrderRequest,
) -> PaperOrderResult:
    """Submit one market DAY order only after explicit paper-only authorization."""
    _validate_request(request)
    order_request = MarketOrderRequest(
        symbol=request.ticker.strip().upper(),
        qty=float(request.quantity),
        side=OrderSide.BUY if request.side == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        client_order_id=request.client_order_id,
    )
    raw_order = client.submit_order(order_data=order_request)
    return PaperOrderResult(
        order_id=str(getattr(raw_order, "id", "")),
        initial_status=getattr(raw_order, "status", "submitted"),
        raw_order=raw_order,
    )


def _validate_request(request: PaperOrderRequest) -> None:
    if not isinstance(request.route, PaperOrderRoute):
        raise PaperOrderRefused("A known paper-order route is required.")
    if request.confirmed is not True:
        raise PaperOrderRefused(f"Explicit confirmation is required for {request.route.value}.")
    if request.alpaca_paper is not True:
        raise PaperOrderRefused("alpaca.paper must be true; live trading is refused.")
    if not isinstance(request.ticker, str):
        raise PaperOrderRefused("Ticker must be text.")
    if not request.ticker.strip():
        raise PaperOrderRefused("Ticker is required.")
    if not isinstance(request.side, str):
        raise PaperOrderRefused("Order side must be text.")
    if request.side not in {"buy", "sell"}:
        raise PaperOrderRefused("Order side must be 'buy' or 'sell'.")
    if not isinstance(request.quantity, Decimal):
        raise PaperOrderRefused("Order quantity must be a Decimal.")
    if not request.quantity.is_finite() or request.quantity <= 0:
        raise PaperOrderRefused("Order quantity must be a finite positive number.")
    if not isinstance(request.client_order_id, str) or not request.client_order_id:
        raise PaperOrderRefused("Client order ID is required.")
    if request.client_order_id != request.client_order_id.strip():
        raise PaperOrderRefused("Client order ID must not have leading or trailing whitespace.")
    if len(request.client_order_id) > 128:
        raise PaperOrderRefused("Client order ID must be 128 characters or fewer.")
    if not CLIENT_ORDER_ID_PATTERN.fullmatch(request.client_order_id):
        raise PaperOrderRefused(
            "Client order ID may contain only ASCII letters, numbers, periods, underscores, and hyphens."
        )
    if not any(character.isalnum() for character in request.client_order_id):
        raise PaperOrderRefused("Client order ID must contain at least one ASCII letter or number.")
