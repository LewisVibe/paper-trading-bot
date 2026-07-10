from __future__ import annotations

from decimal import Decimal
import inspect
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY

import pytest

from trading_bot.cli import application
from trading_bot.positions import Position
from trading_bot.runners import paper_execution


class FakeConnection:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeLogger:
    def __init__(self):
        self.info_messages: list[tuple[object, ...]] = []
        self.error_messages: list[tuple[object, ...]] = []
        self.exception_messages: list[tuple[object, ...]] = []

    def info(self, *args):
        self.info_messages.append(args)

    def error(self, *args):
        self.error_messages.append(args)

    def exception(self, *args):
        self.exception_messages.append(args)


def fail(message: str):
    def raise_failure(*_args, **_kwargs):
        raise AssertionError(message)

    return raise_failure


def make_config(*, dry_run: bool = True, tickers: list[str] | None = None):
    return SimpleNamespace(
        database_path=Path("test.db"),
        dry_run=dry_run,
        allow_shorting=False,
        tickers=tickers or ["AAPL"],
        order_quantity=1,
        alpaca_api_key="paper-key",
        alpaca_secret_key="paper-secret",
    )


def signal(signal_name: str):
    return SimpleNamespace(
        signal=signal_name,
        last_close=101.0,
        short_ma=100.0,
        long_ma=99.0,
    )


def decision(*, should_trade: bool, reason: str = ""):
    return SimpleNamespace(
        should_trade=should_trade,
        side="buy" if should_trade else "",
        action="open_long" if should_trade else "",
        trade_quantity=Decimal("1") if should_trade else Decimal("0"),
        reason=reason,
    )


def make_dependencies(**overrides):
    values = {
        "trading_client_factory": fail("broker client must not be created"),
        "initialize_database": fail("database must be injected by the test"),
        "write_trade_log": fail("trade log must be injected by the test"),
        "send_alert": fail("alert sender must be injected by the test"),
        "configure_market_data": lambda *_: None,
        "download_prices": fail("price loader must be injected by the test"),
        "calculate_strategy_signal": fail("signal calculator must be injected by the test"),
        "decide_trade_action": fail("decision helper must be injected by the test"),
        "read_alpaca_positions": fail("Alpaca positions must not be read"),
        "read_simulated_positions": fail("simulated positions must not be read"),
    }
    values.update(overrides)
    return paper_execution.NormalRunDependencies(**values)


def test_application_uses_extracted_normal_runner():
    assert application.run_bot is paper_execution.run_bot


def test_normal_runner_has_no_order_submission_or_clock_path():
    source = inspect.getsource(paper_execution)

    assert "submit_order" not in source
    assert "MarketOrderRequest" not in source
    assert "get_clock(" not in source


def test_skipped_decision_records_reason_without_alerting():
    logs: list[dict[str, object]] = []
    alerts: list[str] = []
    stats = paper_execution.RunStats()
    before = Position(Decimal("2"))
    dependencies = make_dependencies(
        download_prices=lambda *_: "prices",
        calculate_strategy_signal=lambda *_: signal("SELL"),
        decide_trade_action=lambda *_: decision(should_trade=False, reason="shorting disabled"),
        write_trade_log=lambda **kwargs: logs.append(kwargs),
        send_alert=lambda _config, _logger, message: alerts.append(message),
    )

    paper_execution.process_ticker(
        config=make_config(),
        conn=object(),
        logger=FakeLogger(),
        ticker="AAPL",
        positions={"AAPL": before},
        completed_actions=set(),
        alpaca_client=None,
        stats=stats,
        dependencies=dependencies,
    )

    assert stats.tickers_processed == 1
    assert stats.sell_signals == 1
    assert stats.skipped_trades == 1
    assert stats.submitted_trades == 0
    assert alerts == []
    assert logs[0]["order_status"] == "skipped"
    assert logs[0]["error"] == "shorting disabled"
    assert logs[0]["position_before"] == before
    assert logs[0]["position_after"] == before


def test_trade_decision_is_monitor_only_and_never_submits():
    logs: list[dict[str, object]] = []
    alerts: list[str] = []
    stats = paper_execution.RunStats()
    dependencies = make_dependencies(
        download_prices=lambda *_: "prices",
        calculate_strategy_signal=lambda *_: signal("BUY"),
        decide_trade_action=lambda *_: decision(should_trade=True),
        write_trade_log=lambda **kwargs: logs.append(kwargs),
        send_alert=lambda _config, _logger, message: alerts.append(message),
    )

    paper_execution.process_ticker(
        config=make_config(),
        conn=object(),
        logger=FakeLogger(),
        ticker="AAPL",
        positions={},
        completed_actions=set(),
        alpaca_client=None,
        stats=stats,
        dependencies=dependencies,
    )

    assert logs[0]["order_status"] == "monitor_only"
    assert logs[0]["position_after"] == Position()
    assert stats.submitted_trades == 0
    assert len(alerts) == 1
    assert "Monitoring only" in alerts[0]
    assert "submit" not in paper_execution.NormalRunDependencies.__dataclass_fields__


def test_dry_run_uses_simulated_positions_and_closes_database():
    connection = FakeConnection()
    alerts: list[str] = []
    logs: list[dict[str, object]] = []
    simulated_reads: list[object] = []
    dependencies = make_dependencies(
        initialize_database=lambda _path: connection,
        write_trade_log=lambda **kwargs: logs.append(kwargs),
        send_alert=lambda _config, _logger, message: alerts.append(message),
        read_simulated_positions=lambda conn: simulated_reads.append(conn) or {},
        download_prices=lambda *_: "prices",
        calculate_strategy_signal=lambda *_: signal("HOLD"),
        decide_trade_action=lambda *_: decision(should_trade=False),
    )

    result = paper_execution.run_bot(make_config(dry_run=True), FakeLogger(), dependencies)

    assert result == 0
    assert simulated_reads == [connection]
    assert connection.closed is True
    assert logs[0]["signal"] == "HOLD"
    assert logs[0]["order_status"] == ""
    assert alerts[0].startswith("Bot started. dry_run=True")
    assert alerts[-1].startswith("Bot completed in dry run.")


def test_paper_mode_creates_paper_client_and_reads_positions():
    connection = FakeConnection()
    clients: list[object] = []
    position_reads: list[object] = []
    client = object()

    def client_factory(api_key, secret_key, *, paper):
        assert (api_key, secret_key, paper) == ("paper-key", "paper-secret", True)
        clients.append(client)
        return client

    dependencies = make_dependencies(
        trading_client_factory=client_factory,
        initialize_database=lambda _path: connection,
        write_trade_log=lambda **_kwargs: None,
        send_alert=lambda *_: None,
        read_alpaca_positions=lambda actual_client: position_reads.append(actual_client) or {},
        download_prices=lambda *_: "prices",
        calculate_strategy_signal=lambda *_: signal("HOLD"),
        decide_trade_action=lambda *_: decision(should_trade=False),
    )

    result = paper_execution.run_bot(make_config(dry_run=False), FakeLogger(), dependencies)

    assert result == 0
    assert clients == [client]
    assert position_reads == [client]
    assert connection.closed is True


def test_startup_failure_alerts_and_closes_database():
    connection = FakeConnection()
    alerts: list[str] = []
    dependencies = make_dependencies(
        initialize_database=lambda _path: connection,
        write_trade_log=lambda **_kwargs: None,
        send_alert=lambda _config, _logger, message: alerts.append(message),
        read_simulated_positions=fail("position store unavailable"),
    )

    result = paper_execution.run_bot(
        make_config(dry_run=True, tickers=["AAPL", "MSFT"]),
        FakeLogger(),
        dependencies,
    )

    assert result == 1
    assert connection.closed is True
    assert any("dry-run startup failed" in message for message in alerts)
    assert alerts[-1].startswith("Bot completed in dry run. Processed: 0")
    assert "failed tickers: 2" in alerts[-1]


def test_ticker_failure_writes_error_row_and_alerts():
    connection = FakeConnection()
    alerts: list[str] = []
    logs: list[dict[str, object]] = []
    dependencies = make_dependencies(
        initialize_database=lambda _path: connection,
        write_trade_log=lambda **kwargs: logs.append(kwargs),
        send_alert=lambda _config, _logger, message: alerts.append(message),
        read_simulated_positions=lambda _conn: {},
        download_prices=fail("price download failed"),
    )

    result = paper_execution.run_bot(make_config(dry_run=True), FakeLogger(), dependencies)

    assert result == 1
    assert connection.closed is True
    assert logs == [
        {
            "conn": connection,
            "config": ANY,
            "ticker": "AAPL",
            "signal": "ERROR",
            "order_status": "error",
            "error": "price download failed",
        }
    ]
    assert any("AAPL failed: price download failed" in message for message in alerts)
