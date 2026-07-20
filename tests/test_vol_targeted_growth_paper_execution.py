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
AUTO_NOW = datetime(2026, 7, 10, 14, 5, tzinfo=timezone.utc)


def volatility_snapshot(
    *,
    exposure: Decimal = Decimal("0.8"),
    fresh: bool = True,
    snapshot_now: datetime = NOW,
) -> VolatilitySnapshot:
    prices = {"QQQ": Decimal("700"), "MGK": Decimal("90"), "IBIT": Decimal("35"), "SGOV": Decimal("100")}
    weights = {
        sleeve.symbol: (sleeve.base_weight * exposure).quantize(Decimal("0.000001"))
        for sleeve in SLEEVES
    }
    return VolatilitySnapshot(
        calculated_at=snapshot_now,
        market_data_as_of="2026-07-10",
        price_timestamp=snapshot_now - timedelta(minutes=1 if fresh else 30),
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


def config(*, kill_switch: bool = True, auto_enabled: bool = True):
    return SimpleNamespace(
        alpaca_paper=True,
        allow_shorting=False,
        alpaca_api_key="paper-key",
        alpaca_secret_key="paper-secret",
        paper_kill_switch_enabled=kill_switch,
        auto_paper_trading_enabled=auto_enabled,
        dry_run=True,
        discord_enabled=True,
        discord_webhook_url="https://discord.invalid/api/webhooks/test",
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


def test_auto_paper_requires_explicit_opt_in_and_quietly_skips_dst_probe(tmp_path, monkeypatch):
    broker_reads = []
    alerts = []
    monkeypatch.setattr(runner, "_paper_client", lambda _config: broker_reads.append(True))
    monkeypatch.setattr(runner, "send_discord_alert", lambda _config, _logger, message: alerts.append(message))

    disabled = runner.run_vol_targeted_growth_auto_paper(
        config(auto_enabled=False),
        SimpleNamespace(error=lambda *_args: None, warning=lambda *_args: None),
        root_dir=tmp_path,
        now=AUTO_NOW,
    )
    outside_window = runner.run_vol_targeted_growth_auto_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None, warning=lambda *_args: None),
        root_dir=tmp_path,
        now=AUTO_NOW + timedelta(hours=1),
    )

    assert disabled == 2
    assert outside_window == 0
    assert broker_reads == []
    assert len(alerts) == 1
    assert "orders_submitted=0" in alerts[0]


def test_auto_paper_fills_reconciles_and_blocks_same_session_retry(tmp_path, monkeypatch):
    snapshot = volatility_snapshot(snapshot_now=AUTO_NOW)
    initial_state = broker_state()
    document = build_ticket_document(snapshot, initial_state, now=AUTO_NOW)
    target_positions = {
        row["symbol"]: Decimal(row["target_quantity"])
        for row in document["payload"]["targets"]
    }
    final_state = broker_state(positions=target_positions)
    broker_states = iter([initial_state, final_state])
    submitted = []
    alerts = []

    monkeypatch.setattr(runner, "_paper_client", lambda _config: object())
    monkeypatch.setattr(runner, "collect_broker_state", lambda _client, **_kwargs: next(broker_states))
    monkeypatch.setattr(runner, "load_live_volatility_snapshot", lambda *_args, **_kwargs: snapshot)
    monkeypatch.setattr(
        runner,
        "submit_paper_order",
        lambda _client, request: submitted.append(request)
        or SimpleNamespace(order_id=f"order-{len(submitted)}", initial_status="filled"),
    )
    monkeypatch.setattr(runner, "refresh_order_status", lambda *_args, **_kwargs: "filled")
    monkeypatch.setattr(runner, "send_discord_alert", lambda _config, _logger, message: alerts.append(message))

    result = runner.run_vol_targeted_growth_auto_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None, warning=lambda *_args: None),
        root_dir=tmp_path,
        now=AUTO_NOW,
    )
    retry = runner.run_vol_targeted_growth_auto_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None, warning=lambda *_args: None),
        root_dir=tmp_path,
        now=AUTO_NOW,
    )

    assert result == 0
    assert retry == 2
    assert len(submitted) == len(document["payload"]["orders"])
    assert all(request.client_order_id.startswith("vtga-20260710-") for request in submitted)
    assert all(request.confirmed is True and request.alpaca_paper is True for request in submitted)
    state = runner.read_json(tmp_path / runner.AUTO_STATE_JSON)
    assert state["status"] == "filled_aligned"
    assert state["postcheck_aligned"] is True
    assert any("AUTO PAPER REBALANCE COMPLETE" in message for message in alerts)
    assert any("already recorded" in message for message in alerts)


def test_auto_paper_existing_crash_lease_blocks_without_broker_read(tmp_path, monkeypatch):
    assert runner.acquire_auto_lease(tmp_path, "2026-07-10", "vtga-20260710", AUTO_NOW) is True
    broker_reads = []
    alerts = []
    monkeypatch.setattr(runner, "_paper_client", lambda _config: broker_reads.append(True))
    monkeypatch.setattr(runner, "send_discord_alert", lambda _config, _logger, message: alerts.append(message))

    result = runner.run_vol_targeted_growth_auto_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None, warning=lambda *_args: None),
        root_dir=tmp_path,
        now=AUTO_NOW,
    )

    assert result == 2
    assert broker_reads == []
    assert "lease already exists" in alerts[0]


def test_auto_paper_weekday_market_holiday_skips_without_market_data_or_orders(tmp_path, monkeypatch):
    closed_state = broker_state(market_open=False)
    alerts = []
    monkeypatch.setattr(runner, "_paper_client", lambda _config: object())
    monkeypatch.setattr(runner, "collect_broker_state", lambda _client, **_kwargs: closed_state)
    monkeypatch.setattr(
        runner,
        "load_live_volatility_snapshot",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("market data should not load")),
    )
    monkeypatch.setattr(
        runner,
        "submit_paper_order",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("order should not submit")),
    )
    monkeypatch.setattr(runner, "send_discord_alert", lambda _config, _logger, message: alerts.append(message))

    result = runner.run_vol_targeted_growth_auto_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None, warning=lambda *_args: None),
        root_dir=tmp_path,
        now=AUTO_NOW,
    )

    assert result == 0
    assert runner.read_json(tmp_path / runner.AUTO_STATE_JSON)["status"] == "skipped_market_closed"
    assert "AUTO PAPER REBALANCE SKIPPED" in alerts[0]


def test_auto_paper_records_no_action_when_positions_are_aligned(tmp_path, monkeypatch):
    snapshot = volatility_snapshot(snapshot_now=AUTO_NOW)
    initial_document = build_ticket_document(snapshot, broker_state(), now=AUTO_NOW)
    aligned_positions = {
        row["symbol"]: Decimal(row["target_quantity"])
        for row in initial_document["payload"]["targets"]
    }
    aligned_state = broker_state(positions=aligned_positions)
    no_action_document = build_ticket_document(snapshot, aligned_state, now=AUTO_NOW)
    assert no_action_document["payload"]["orders"] == []
    assert no_action_document["payload"]["blockers"] == [runner.NO_ORDERS_REQUIRED]
    alerts = []

    monkeypatch.setattr(runner, "_paper_client", lambda _config: object())
    monkeypatch.setattr(runner, "collect_broker_state", lambda _client, **_kwargs: aligned_state)
    monkeypatch.setattr(runner, "load_live_volatility_snapshot", lambda *_args, **_kwargs: snapshot)
    monkeypatch.setattr(runner, "submit_paper_order", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no order expected")))
    monkeypatch.setattr(runner, "send_discord_alert", lambda _config, _logger, message: alerts.append(message))

    result = runner.run_vol_targeted_growth_auto_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None, warning=lambda *_args: None),
        root_dir=tmp_path,
        now=AUTO_NOW,
    )

    assert result == 0
    state = runner.read_json(tmp_path / runner.AUTO_STATE_JSON)
    assert state["status"] == "no_action_aligned"
    assert runner.read_json(tmp_path / runner.EXECUTION_JSON)["status"] == "no_action"
    assert runner.read_json(tmp_path / runner.POSTCHECK_JSON)["status"] == "aligned"
    assert "orders=0" in alerts[0]


def test_auto_paper_stops_after_first_nonfilled_order_and_requires_review(tmp_path, monkeypatch):
    snapshot = volatility_snapshot(snapshot_now=AUTO_NOW)
    state = broker_state()
    submitted = []
    alerts = []
    monkeypatch.setattr(runner, "_paper_client", lambda _config: object())
    monkeypatch.setattr(runner, "collect_broker_state", lambda _client, **_kwargs: state)
    monkeypatch.setattr(runner, "load_live_volatility_snapshot", lambda *_args, **_kwargs: snapshot)
    monkeypatch.setattr(
        runner,
        "submit_paper_order",
        lambda _client, request: submitted.append(request)
        or SimpleNamespace(order_id="order-1", initial_status="accepted"),
    )
    monkeypatch.setattr(runner, "refresh_order_status", lambda *_args, **_kwargs: "partially_filled")
    monkeypatch.setattr(runner, "send_discord_alert", lambda _config, _logger, message: alerts.append(message))

    result = runner.run_vol_targeted_growth_auto_paper(
        config(),
        SimpleNamespace(error=lambda *_args: None, warning=lambda *_args: None),
        root_dir=tmp_path,
        now=AUTO_NOW,
    )

    assert result == 1
    assert len(submitted) == 1
    auto_state = runner.read_json(tmp_path / runner.AUTO_STATE_JSON)
    assert auto_state["status"] == "partial_or_failed_manual_review_required"
    assert "manual_review_required=true" in alerts[0]
