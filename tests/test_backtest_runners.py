from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from trading_bot.cli import application
from trading_bot.cli.report_only import dispatch_report_only
from trading_bot.runners import backtests


def test_application_uses_extracted_backtest_runners():
    assert application.run_backtest is backtests.run_backtest
    assert application.run_etf_rotation_backtest is backtests.run_etf_rotation_backtest
    assert application.run_adaptive_momentum_backtest is backtests.run_adaptive_momentum_backtest
    assert application.run_strategy_comparison is backtests.run_strategy_comparison
    assert application.run_sma_sensitivity is backtests.run_sma_sensitivity
    assert application.run_trend_stress_test is backtests.run_trend_stress_test


@pytest.mark.parametrize("command", sorted(backtests.MARKET_DATA_COMMANDS))
def test_market_data_backtests_are_not_saved_output_routes(command: str):
    assert dispatch_report_only([command]) is None


def test_backtest_runner_has_no_execution_dependencies():
    source = inspect.getsource(backtests)

    for forbidden in (
        "TradingClient",
        "submit_order",
        "send_discord_alert",
        "init_database",
        "insert_trade_log",
        "get_alpaca_positions",
    ):
        assert forbidden not in source


def test_run_backtest_uses_injected_market_data_without_external_calls(
    monkeypatch: pytest.MonkeyPatch,
):
    config = SimpleNamespace(
        backtest=SimpleNamespace(
            slippage_bps=5,
            output_csv="results.csv",
            trades_csv="trades.csv",
        ),
        strategy=SimpleNamespace(regime_ticker="SPY"),
        tickers=["AAPL"],
    )
    logger = SimpleNamespace(error=lambda *args: None)
    downloaded: list[str] = []
    written: list[str] = []
    result = object()
    trade = object()

    monkeypatch.setattr(backtests, "configure_yfinance_cache", lambda *_: None)
    monkeypatch.setattr(
        backtests,
        "download_backtest_prices",
        lambda _config, ticker: downloaded.append(ticker) or f"{ticker}-prices",
    )
    monkeypatch.setattr(
        backtests,
        "backtest_ticker",
        lambda *_: (result, [trade]),
    )
    monkeypatch.setattr(backtests, "format_backtest_result", lambda _: "result-row")
    monkeypatch.setattr(
        backtests,
        "write_backtest_results",
        lambda *_: written.append("results"),
    )
    monkeypatch.setattr(
        backtests,
        "write_backtest_trades",
        lambda *_: written.append("trades"),
    )
    monkeypatch.setattr(backtests, "print_portfolio_summary", lambda *_: None)

    assert backtests.run_backtest(config, logger) == 0
    assert downloaded == ["SPY", "AAPL"]
    assert written == ["results", "trades"]
