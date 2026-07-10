"""Single audited gateway for explicitly confirmed Alpaca paper orders."""

from __future__ import annotations

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


@dataclass(frozen=True)
class PaperOrderResult:
    order_id: str
    initial_status: Any
    raw_order: Any


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
    if not request.confirmed:
        raise PaperOrderRefused(f"Explicit confirmation is required for {request.route.value}.")
    if not request.alpaca_paper:
        raise PaperOrderRefused("alpaca.paper must be true; live trading is refused.")
    if not request.ticker.strip():
        raise PaperOrderRefused("Ticker is required.")
    if request.side not in {"buy", "sell"}:
        raise PaperOrderRefused("Order side must be 'buy' or 'sell'.")
    if not request.quantity.is_finite() or request.quantity <= 0:
        raise PaperOrderRefused("Order quantity must be a finite positive number.")
