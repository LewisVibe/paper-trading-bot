from __future__ import annotations

import ast
import logging
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from alpaca.trading.enums import OrderSide, TimeInForce

from trading_bot.alpaca_client import refresh_order_status
from trading_bot.cli import application
from trading_bot.config import ConfigError
from trading_bot.paper_orders import (
    PaperOrderRefused,
    PaperOrderRequest,
    PaperOrderRoute,
    submit_paper_order,
)
from trading_bot.positions import Position
from trading_bot.safety.manual_paper_smoke_test_gate import ManualSmokeTestRecentOrderMatch
from trading_bot.safety.paper_kill_switch import evaluate_paper_kill_switch_gate
from trading_bot.safety.qqq100_paper_execution import (
    STRATEGY_NAME,
    TICKER,
    Qqq100SavedSignal,
    evaluate_qqq100_paper_execution_preflight,
)


ROOT = Path(__file__).resolve().parents[1]
APPLICATION_PATH = ROOT / "trading_bot" / "cli" / "application.py"
VOL_RUNNER_PATH = ROOT / "trading_bot" / "runners" / "vol_targeted_growth_paper.py"


class MockTradingClient:
    def __init__(self) -> None:
        self.submitted: list[object] = []

    def submit_order(self, *, order_data):
        self.submitted.append(order_data)
        return SimpleNamespace(id="paper-order-123", status="accepted")


@pytest.mark.parametrize(
    ("route", "side", "expected_side"),
    [
        (PaperOrderRoute.MANUAL_TEST, "buy", OrderSide.BUY),
        (PaperOrderRoute.QQQ100, "sell", OrderSide.SELL),
        (PaperOrderRoute.SLOW_SMA, "buy", OrderSide.BUY),
        (PaperOrderRoute.VOL_TARGETED_GROWTH, "buy", OrderSide.BUY),
    ],
)
def test_gateway_submits_confirmed_paper_day_market_order(route, side, expected_side):
    client = MockTradingClient()

    result = submit_paper_order(
        client,
        PaperOrderRequest(
            route=route,
            ticker=" aapl ",
            side=side,
            quantity=Decimal("2"),
            confirmed=True,
            alpaca_paper=True,
            client_order_id="paper-ticket-test",
        ),
    )

    assert result.order_id == "paper-order-123"
    assert result.initial_status == "accepted"
    assert result.raw_order.id == "paper-order-123"
    assert len(client.submitted) == 1
    submitted = client.submitted[0]
    assert submitted.symbol == "AAPL"
    assert submitted.qty == 2.0
    assert submitted.side == expected_side
    assert submitted.time_in_force == TimeInForce.DAY
    assert submitted.client_order_id == "paper-ticket-test"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"confirmed": False}, "Explicit confirmation"),
        ({"alpaca_paper": False}, "live trading is refused"),
        ({"route": "unknown"}, "known paper-order route"),
        ({"ticker": "   "}, "Ticker is required"),
        ({"side": "hold"}, "Order side"),
        ({"quantity": Decimal("0")}, "finite positive"),
        ({"quantity": Decimal("NaN")}, "finite positive"),
        ({"client_order_id": "x" * 129}, "128 characters"),
    ],
)
def test_gateway_refuses_unsafe_request_before_broker_call(overrides, message):
    client = MockTradingClient()
    values = {
        "route": PaperOrderRoute.MANUAL_TEST,
        "ticker": "AAPL",
        "side": "buy",
        "quantity": Decimal("1"),
        "confirmed": True,
        "alpaca_paper": True,
    }
    values.update(overrides)

    with pytest.raises(PaperOrderRefused, match=message):
        submit_paper_order(client, PaperOrderRequest(**values))

    assert client.submitted == []


def test_post_submit_status_refresh_preserves_order_id_and_final_broker_state():
    refreshed_ids: list[str] = []

    class Client:
        def get_order_by_id(self, order_id: str):
            refreshed_ids.append(order_id)
            return SimpleNamespace(status="filled")

    status = refresh_order_status(
        Client(),
        logging.getLogger("paper-order-gateway-test"),
        "paper-order-123",
        "accepted",
        timeout_seconds=1,
    )

    assert refreshed_ids == ["paper-order-123"]
    assert status == "filled"


def test_only_gateway_calls_broker_submit_and_all_order_routes_use_gateway():
    direct_submitters: list[tuple[Path, str]] = []
    gateway_callers: list[tuple[str, str, str]] = []
    paper_client_owners: set[str] = set()
    order_client_owners = {
        "run_paper_order_test",
        "run_execute_qqq100_paper",
        "run_slow_sma_paper_execution",
        "_paper_client",
    }
    source_paths = [ROOT / "bot.py", *sorted((ROOT / "trading_bot").rglob("*.py"))]

    for path in source_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            owner = _enclosing_function(node, parents)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "submit_order":
                direct_submitters.append((path.relative_to(ROOT), owner))
            if (
                path in {APPLICATION_PATH, VOL_RUNNER_PATH}
                and isinstance(node.func, ast.Name)
                and node.func.id == "TradingClient"
                and owner in order_client_owners
            ):
                keywords = {keyword.arg: keyword.value for keyword in node.keywords}
                paper = keywords.get("paper")
                assert isinstance(paper, ast.Constant) and paper.value is True
                paper_client_owners.add(owner)
            if (
                path in {APPLICATION_PATH, VOL_RUNNER_PATH}
                and isinstance(node.func, ast.Name)
                and node.func.id == "submit_paper_order"
            ):
                request = node.args[1]
                assert isinstance(request, ast.Call)
                keywords = {keyword.arg: keyword.value for keyword in request.keywords}
                route = keywords["route"]
                confirmed = keywords["confirmed"]
                assert isinstance(route, ast.Attribute)
                assert isinstance(confirmed, ast.Name)
                gateway_callers.append((owner, route.attr, confirmed.id))

    assert direct_submitters == [(Path("trading_bot/paper_orders.py"), "submit_paper_order")]
    assert set(gateway_callers) == {
        ("run_paper_order_test", "MANUAL_TEST", "confirm_paper_order"),
        ("run_execute_qqq100_paper", "QQQ100", "confirm_qqq100_paper"),
        ("process_slow_sma_execution_ticker", "SLOW_SMA", "confirm_slow_sma_paper"),
        ("run_execute_vol_targeted_growth_paper", "VOL_TARGETED_GROWTH", "confirmed"),
    }
    assert paper_client_owners == order_client_owners


@pytest.mark.parametrize(
    "unsafe_value",
    [
        {"explicit_confirmation": False},
        {"alpaca_paper": False},
        {"allow_shorting": True},
        {"paper_kill_switch_enabled": False},
    ],
)
def test_paper_kill_switch_refuses_missing_safety_prerequisite(unsafe_value):
    inputs = {
        "alpaca_paper": True,
        "allow_shorting": False,
        "paper_kill_switch_enabled": True,
        "execution_eligibility_blocked": False,
        "defensive_decision_blocked": False,
        "explicit_confirmation": True,
        "command_name": "paper_order_test",
    }
    inputs.update(unsafe_value)

    decision = evaluate_paper_kill_switch_gate(**inputs)

    assert decision.allowed is False
    assert decision.status == "blocked"


@pytest.mark.parametrize(
    "unsafe_value",
    [
        {"confirm_qqq100_paper": False},
        {"alpaca_paper": False},
        {"open_order_count": 1},
        {
            "recent_order_match": SimpleNamespace(
                duplicate_recent_order_check="blocked_recent_matching_order_exists",
                recent_order_match_status="accepted",
                recent_order_match_count=1,
                recent_order_match_age_minutes="1",
                recent_order_match_source="alpaca_paper_recent_orders",
            )
        },
    ],
)
def test_qqq100_preflight_refuses_confirmation_live_open_or_duplicate(unsafe_value):
    inputs = {
        "confirm_qqq100_paper": True,
        "alpaca_paper": True,
        "allow_shorting": False,
        "credentials_present": True,
        "market_status": "open",
        "signal": Qqq100SavedSignal(
            True,
            STRATEGY_NAME,
            TICKER,
            "long",
            "2026-06-15",
            "ok",
            "",
        ),
        "current_position": Position(Decimal("0")),
        "position_readable": True,
        "open_order_count": 0,
        "recent_order_match": _recent_order_pass(),
    }
    inputs.update(unsafe_value)

    decision = evaluate_qqq100_paper_execution_preflight(**inputs)

    assert decision.allowed is False
    assert decision.order_side == "buy"
    assert decision.execution_approved is False
    assert decision.paper_execution_approved is False


@pytest.mark.parametrize(
    "config",
    [
        SimpleNamespace(alpaca_paper=False, allow_shorting=False),
        SimpleNamespace(alpaca_paper=True, allow_shorting=True),
    ],
)
def test_slow_sma_preflight_refuses_live_mode_or_shorting(config):
    with pytest.raises(ConfigError):
        application.validate_slow_sma_execution_preflight_safety(config)


def test_slow_sma_open_order_refusal_creates_no_order_quantity():
    position = Position(Decimal("0"))

    side, action, quantity, position_after, message = application.decide_slow_sma_execution_action(
        "long",
        position,
        Decimal("1"),
        open_order_exists=True,
    )

    assert side == ""
    assert action == "blocked_open_order"
    assert quantity == Decimal("0")
    assert position_after == position
    assert "Existing open Alpaca order" in message


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent.name
        parent = parents.get(parent)
    return "<module>"


def _recent_order_pass() -> ManualSmokeTestRecentOrderMatch:
    return ManualSmokeTestRecentOrderMatch(
        duplicate_recent_order_check="pass",
        duplicate_recent_order_source="alpaca_paper_recent_orders",
        duplicate_recent_order_status_if_any="none",
        recent_order_match_found=False,
        recent_order_match_status="none",
        recent_order_match_submitted_at_or_created_at="",
        recent_order_match_age_minutes="",
        recent_order_match_source="alpaca_paper_recent_orders",
        recent_order_match_count=0,
        recent_order_match_lookback_minutes=120,
        recent_order_match_time_field_used="none",
    )
