from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from trading_bot.runners import vol_targeted_growth_paper as runner
from trading_bot.safety.vol_targeted_growth_paper_execution import (
    AssetState,
    BrokerState,
    build_ticket_document,
    execution_preflight_reasons,
    ticket_id_for_payload,
    verify_ticket_document,
)
from trading_bot.strategies.vol_targeted_growth import (
    MANAGED_SYMBOLS,
    SLEEVES,
    VolatilitySnapshot,
    calculate_volatility_snapshot,
)


NOW = datetime(2026, 7, 10, 15, 0, tzinfo=timezone.utc)


def volatility_snapshot(*, exposure: Decimal = Decimal("0.8"), fresh: bool = True) -> VolatilitySnapshot:
    prices = {"QQQ": Decimal("700"), "MGK": Decimal("90"), "IBIT": Decimal("35"), "SGOV": Decimal("100")}
    weights = {
        sleeve.symbol: (sleeve.base_weight * exposure).quantize(Decimal("0.000001"))
        for sleeve in SLEEVES
    }
    return VolatilitySnapshot(
        calculated_at=NOW,
        market_data_as_of="2026-07-10",
        price_timestamp=NOW - timedelta(minutes=1 if fresh else 30),
        prices=prices,
        realized_volatility=Decimal("0.1875"),
        exposure_multiplier=exposure,
        effective_weights=weights,
        cash_weight=Decimal("1") - sum(weights.values()),
        return_observation_count=20,
        price_age_minutes=Decimal("1" if fresh else "30"),
        prices_fresh=fresh,
    )


def broker_state(
    *,
    market_open: bool = True,
    positions: dict[str, Decimal] | None = None,
    open_orders: tuple[str, ...] = (),
    cash: Decimal = Decimal("100000"),
    equity: Decimal = Decimal("100000"),
    position_market_values: dict[str, Decimal] | None = None,
    recent_client_order_ids: tuple[str, ...] = (),
) -> BrokerState:
    assets = {
        symbol: AssetState(symbol, "us_equity", tradable=True, fractionable=True)
        for symbol in MANAGED_SYMBOLS
    }
    return BrokerState(
        captured_at=NOW,
        market_open=market_open,
        account_status="ACTIVE",
        account_blocked=False,
        trading_blocked=False,
        trade_suspended_by_user=False,
        cash=cash,
        equity=equity,
        buying_power=equity,
        positions=positions or {},
        position_market_values=position_market_values or {},
        open_order_symbols=open_orders,
        recent_client_order_ids=recent_client_order_ids,
        assets=assets,
    )


def config(*, kill_switch: bool = True):
    return SimpleNamespace(
        alpaca_paper=True,
        allow_shorting=False,
        alpaca_api_key="paper-key",
        alpaca_secret_key="paper-secret",
        paper_kill_switch_enabled=kill_switch,
        dry_run=True,
    )


def test_volatility_overlay_scales_exposure_below_one_for_volatile_prices():
    rows = []
    prices = {symbol: Decimal("100") for symbol in MANAGED_SYMBOLS}
    rows.append(dict(prices))
    for index in range(25):
        multiplier = Decimal("1.05") if index % 2 == 0 else Decimal("0.95")
        prices = {symbol: value * multiplier for symbol, value in prices.items()}
        rows.append(dict(prices))

    snapshot = calculate_volatility_snapshot(
        rows,
        market_data_as_of="2026-07-10",
        price_timestamp=NOW,
        prices=rows[-1],
        now=NOW,
    )

    assert Decimal("0") < snapshot.exposure_multiplier < Decimal("1")
    assert sum(snapshot.effective_weights.values()) <= snapshot.exposure_multiplier
    assert snapshot.cash_weight == Decimal("1") - sum(snapshot.effective_weights.values())


def test_ticket_uses_100k_cap_scaled_weights_and_never_targets_unrelated_positions():
    document = build_ticket_document(
        volatility_snapshot(),
        broker_state(positions={"AAPL": Decimal("1")}),
        now=NOW,
    )
    payload = document["payload"]
    targets = {row["symbol"]: row for row in payload["targets"]}

    assert payload["paper_capital_usd"] == "100000"
    assert targets["QQQ"]["target_dollars"] == "56000"
    assert targets["MGK"]["target_dollars"] == "16000"
    assert targets["IBIT"]["target_dollars"] == "4000"
    assert targets["SGOV"]["target_dollars"] == "4000"
    assert payload["unrelated_position_symbols"] == ["AAPL"]
    assert all(order["symbol"] in MANAGED_SYMBOLS for order in payload["orders"])
    assert payload["execution_ready"] is True
    assert verify_ticket_document(document) == []


def test_ticket_reduces_allocation_capital_for_untouched_unrelated_positions():
    document = build_ticket_document(
        volatility_snapshot(),
        broker_state(
            positions={"AAPL": Decimal("10")},
            position_market_values={"AAPL": Decimal("5000")},
        ),
        now=NOW,
    )
    payload = document["payload"]
    targets = {row["symbol"]: row for row in payload["targets"]}

    assert payload["paper_capital_usd"] == "100000"
    assert payload["allocation_capital_usd"] == "95000"
    assert targets["QQQ"]["target_dollars"] == "53200"
    assert payload["unrelated_positions"] == {"AAPL": "10"}


def test_ticket_blocks_closed_market_stale_prices_open_orders_and_short_positions():
    state = broker_state(
        market_open=False,
        positions={"QQQ": Decimal("-1")},
        open_orders=("MGK",),
    )
    document = build_ticket_document(volatility_snapshot(fresh=False), state, now=NOW)
    blockers = document["payload"]["blockers"]

    assert document["payload"]["execution_ready"] is False
    assert "Alpaca paper market is closed" in blockers
    assert "intraday prices are older than 15 minutes" in blockers
    assert "one or more Alpaca paper orders are already open" in blockers
    assert any("short" in blocker for blocker in blockers)


def test_ticket_hash_detects_tampering_and_execution_rechecks_positions():
    state = broker_state()
    document = build_ticket_document(volatility_snapshot(), state, now=NOW)
    assert verify_ticket_document(document) == []

    tampered = {"ticket_id": document["ticket_id"], "payload": dict(document["payload"])}
    tampered["payload"]["paper_capital_usd"] = "200000"
    assert verify_ticket_document(tampered)

    self_consistent_tamper = deepcopy(document)
    self_consistent_tamper["payload"]["orders"][0]["symbol"] = "TSLA"
    self_consistent_tamper["ticket_id"] = ticket_id_for_payload(self_consistent_tamper["payload"])
    assert "ticket targets or orders do not match the approved deterministic calculation" in verify_ticket_document(
        self_consistent_tamper
    )

    changed_state = broker_state(positions={"QQQ": Decimal("1")})
    reasons = execution_preflight_reasons(
        document,
        changed_state,
        supplied_ticket_id=document["ticket_id"],
        confirmed=True,
        now=NOW + timedelta(minutes=1),
    )
    assert "QQQ paper position changed after ticket preparation" in reasons


def test_execution_rechecks_price_age_unrelated_positions_and_cash_capacity():
    initial = broker_state(
        positions={"AAPL": Decimal("1")},
        position_market_values={"AAPL": Decimal("1000")},
    )
    document = build_ticket_document(volatility_snapshot(), initial, now=NOW)
    current = broker_state(
        positions={"AAPL": Decimal("2")},
        position_market_values={"AAPL": Decimal("2000")},
        cash=Decimal("1"),
    )

    reasons = execution_preflight_reasons(
        document,
        current,
        supplied_ticket_id=document["ticket_id"],
        confirmed=True,
        now=NOW + timedelta(minutes=16),
    )

    assert "ticket intraday prices are older than 15 minutes" in reasons
    assert "unrelated paper positions changed after ticket preparation" in reasons
    assert "cash plus estimated sell proceeds cannot fund buys without leverage" in reasons


def test_execution_requires_confirmation_and_uses_gateway_client_ids(tmp_path, monkeypatch):
    state = broker_state()
    document = build_ticket_document(volatility_snapshot(), state, now=NOW)
    runner.write_ticket_outputs(tmp_path, document)
    submitted = []

    monkeypatch.setattr(runner, "_paper_client", lambda _config: object())
    monkeypatch.setattr(runner, "collect_broker_state", lambda _client, **_kwargs: state)
    monkeypatch.setattr(
        runner,
        "submit_paper_order",
        lambda _client, request: submitted.append(request)
        or SimpleNamespace(order_id=f"order-{len(submitted)}", initial_status="filled"),
    )
    monkeypatch.setattr(runner, "refresh_order_status", lambda *_args, **_kwargs: "filled")
    monkeypatch.setattr(runner, "datetime", SimpleNamespace(now=lambda _tz: NOW + timedelta(minutes=1)))

    blocked = runner.run_execute_vol_targeted_growth_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None),
        ticket_id=document["ticket_id"],
        confirmed=False,
        root_dir=tmp_path,
    )
    assert blocked == 2
    assert submitted == []

    # Remove the blocked local record; it contains no orders and is safe to retry.
    submitted.clear()
    result = runner.run_execute_vol_targeted_growth_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None),
        ticket_id=document["ticket_id"],
        confirmed=True,
        root_dir=tmp_path,
    )

    assert result == 0
    assert len(submitted) == len(document["payload"]["orders"])
    assert all(request.client_order_id.startswith(f"{document['ticket_id']}-") for request in submitted)
    assert all(request.alpaca_paper is True and request.confirmed is True for request in submitted)


def test_execution_kill_switch_blocks_before_gateway(tmp_path, monkeypatch):
    state = broker_state()
    document = build_ticket_document(volatility_snapshot(), state, now=NOW)
    runner.write_ticket_outputs(tmp_path, document)
    submitted = []
    monkeypatch.setattr(runner, "_paper_client", lambda _config: object())
    monkeypatch.setattr(runner, "collect_broker_state", lambda _client, **_kwargs: state)
    monkeypatch.setattr(runner, "submit_paper_order", lambda *_args: submitted.append(True))
    monkeypatch.setattr(runner, "datetime", SimpleNamespace(now=lambda _tz: NOW + timedelta(minutes=1)))

    result = runner.run_execute_vol_targeted_growth_paper(
        config(kill_switch=False),
        SimpleNamespace(error=lambda *_args: None),
        ticket_id=document["ticket_id"],
        confirmed=True,
        root_dir=tmp_path,
    )

    assert result == 2
    assert submitted == []


def test_postcheck_accepts_only_sub_dollar_residuals_after_filled_execution(tmp_path, monkeypatch):
    state = broker_state()
    document = build_ticket_document(volatility_snapshot(), state, now=NOW)
    runner.write_ticket_outputs(tmp_path, document)
    target_positions = {
        row["symbol"]: Decimal(row["target_quantity"])
        for row in document["payload"]["targets"]
    }
    target_positions["QQQ"] += Decimal("0.001")
    actual_state = broker_state(positions=target_positions)
    runner.write_json(
        tmp_path / runner.EXECUTION_JSON,
        {"ticket_id": document["ticket_id"], "status": "filled", "orders": [{"status": "filled"}]},
    )
    monkeypatch.setattr(runner, "_paper_client", lambda _config: object())
    monkeypatch.setattr(runner, "collect_broker_state", lambda _client, **_kwargs: actual_state)

    result = runner.run_vol_targeted_growth_paper_postcheck(
        config(),
        SimpleNamespace(error=lambda *_args: None),
        confirm_readonly_alpaca_check=True,
        root_dir=tmp_path,
    )

    assert result == 0
    postcheck = runner.read_json(tmp_path / runner.POSTCHECK_JSON)
    assert postcheck["status"] == "aligned"


def test_postcheck_rejects_partial_execution_record(tmp_path, monkeypatch):
    state = broker_state()
    document = build_ticket_document(volatility_snapshot(), state, now=NOW)
    runner.write_ticket_outputs(tmp_path, document)
    target_positions = {
        row["symbol"]: Decimal(row["target_quantity"])
        for row in document["payload"]["targets"]
    }
    actual_state = broker_state(positions=target_positions)
    runner.write_json(
        tmp_path / runner.EXECUTION_JSON,
        {"ticket_id": document["ticket_id"], "status": "partial_or_failed", "orders": [{"status": "filled"}]},
    )
    monkeypatch.setattr(runner, "_paper_client", lambda _config: object())
    monkeypatch.setattr(runner, "collect_broker_state", lambda _client, **_kwargs: actual_state)

    result = runner.run_vol_targeted_growth_paper_postcheck(
        config(),
        SimpleNamespace(error=lambda *_args: None),
        confirm_readonly_alpaca_check=True,
        root_dir=tmp_path,
    )

    assert result == 2
    postcheck = runner.read_json(tmp_path / runner.POSTCHECK_JSON)
    assert "matching execution record is not fully filled" in postcheck["reasons"]
