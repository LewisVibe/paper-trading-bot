"""Normal monitoring and Alpaca paper-position runner.

The normal path records decisions and alerts but does not submit orders.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable

from alpaca.trading.client import TradingClient

from trading_bot.config import AppConfig
from trading_bot.database import init_database, insert_trade_log
from trading_bot.discord_alerts import send_discord_alert
from trading_bot.execution import decide_trade
from trading_bot.market_data import configure_yfinance_cache, download_close_prices
from trading_bot.positions import Position, format_decimal, get_alpaca_positions, get_simulated_positions
from trading_bot.strategies.sma import SIGNAL_BUY, SIGNAL_HOLD, SIGNAL_SELL, calculate_signal


@dataclass
class RunStats:
    tickers_processed: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    skipped_trades: int = 0
    failed_tickers: int = 0
    submitted_trades: int = 0


@dataclass(frozen=True)
class NormalRunDependencies:
    """External boundaries used by the normal monitoring runner."""

    trading_client_factory: Callable[..., Any] = TradingClient
    initialize_database: Callable[..., Any] = init_database
    write_trade_log: Callable[..., Any] = insert_trade_log
    send_alert: Callable[..., Any] = send_discord_alert
    configure_market_data: Callable[..., Any] = configure_yfinance_cache
    download_prices: Callable[..., Any] = download_close_prices
    calculate_strategy_signal: Callable[..., Any] = calculate_signal
    decide_trade_action: Callable[..., Any] = decide_trade
    read_alpaca_positions: Callable[..., Any] = get_alpaca_positions
    read_simulated_positions: Callable[..., Any] = get_simulated_positions


DEFAULT_NORMAL_RUN_DEPENDENCIES = NormalRunDependencies()


def decimal_to_float(value: Decimal) -> float:
    return float(value)


def update_signal_stats(stats: RunStats, signal: str) -> None:
    if signal == SIGNAL_BUY:
        stats.buy_signals += 1
    elif signal == SIGNAL_SELL:
        stats.sell_signals += 1
    elif signal == SIGNAL_HOLD:
        stats.hold_signals += 1


def build_summary(config: AppConfig, stats: RunStats) -> str:
    mode = "dry run" if config.dry_run else "Alpaca paper trading"
    return (
        f"Bot completed in {mode}. "
        f"Processed: {stats.tickers_processed}, "
        f"BUY: {stats.buy_signals}, "
        f"SELL: {stats.sell_signals}, "
        f"HOLD: {stats.hold_signals}, "
        f"skipped trades: {stats.skipped_trades}, "
        f"failed tickers: {stats.failed_tickers}, "
        f"trades: {stats.submitted_trades}."
    )


def process_ticker(
    config: AppConfig,
    conn: sqlite3.Connection,
    logger: logging.Logger,
    ticker: str,
    positions: dict[str, Position],
    completed_actions: set[tuple[str, str]],
    alpaca_client: TradingClient | None,
    stats: RunStats,
    dependencies: NormalRunDependencies = DEFAULT_NORMAL_RUN_DEPENDENCIES,
) -> None:
    logger.info("Processing %s", ticker)
    stats.tickers_processed += 1

    close_prices = dependencies.download_prices(config, ticker)
    result = dependencies.calculate_strategy_signal(config, close_prices)
    update_signal_stats(stats, result.signal)

    position_before = positions.get(ticker, Position())
    decision = dependencies.decide_trade_action(
        result.signal,
        position_before,
        config.allow_shorting,
        config.order_quantity,
    )

    if not decision.should_trade:
        if result.signal != SIGNAL_HOLD:
            stats.skipped_trades += 1
            logger.info("%s %s skipped: %s", ticker, result.signal, decision.reason)

        dependencies.write_trade_log(
            conn=conn,
            config=config,
            ticker=ticker,
            signal=result.signal,
            position_before=position_before,
            position_after=position_before,
            quantity=0 if result.signal != SIGNAL_HOLD else None,
            last_close=result.last_close,
            short_ma=result.short_ma,
            long_ma=result.long_ma,
            order_status="skipped" if result.signal != SIGNAL_HOLD else "",
            error=decision.reason if result.signal != SIGNAL_HOLD else "",
        )
        return

    order_status = "monitor_only"
    logger.info(
        "Monitoring only: would %s %s %s share(s) (normal run does not place orders)",
        decision.action,
        format_decimal(decision.trade_quantity),
        ticker,
    )

    dependencies.write_trade_log(
        conn=conn,
        config=config,
        ticker=ticker,
        signal=result.signal,
        side=decision.side,
        action=decision.action,
        position_before=position_before,
        position_after=position_before,
        quantity=decimal_to_float(decision.trade_quantity),
        last_close=result.last_close,
        short_ma=result.short_ma,
        long_ma=result.long_ma,
        order_status=order_status,
    )

    dependencies.send_alert(
        config,
        logger,
        (
            f"Monitoring only: {ticker} would {decision.side.upper()} "
            f"{format_decimal(decision.trade_quantity)} share(s) "
            f"({decision.action}, signal {result.signal}, status {order_status})"
        ),
    )


def run_bot(
    config: AppConfig,
    logger: logging.Logger,
    dependencies: NormalRunDependencies = DEFAULT_NORMAL_RUN_DEPENDENCIES,
) -> int:
    conn = dependencies.initialize_database(config.database_path)
    stats = RunStats()

    logger.info("Starting bot. dry_run=%s allow_shorting=%s", config.dry_run, config.allow_shorting)
    dependencies.configure_market_data(config, logger)
    dependencies.send_alert(
        config,
        logger,
        f"Bot started. dry_run={config.dry_run}, allow_shorting={config.allow_shorting}",
    )

    alpaca_client: TradingClient | None = None
    try:
        try:
            if config.dry_run:
                positions = dependencies.read_simulated_positions(conn)
            else:
                alpaca_client = dependencies.trading_client_factory(
                    config.alpaca_api_key,
                    config.alpaca_secret_key,
                    paper=True,
                )
                positions = dependencies.read_alpaca_positions(alpaca_client)
        except Exception as exc:
            stats.failed_tickers = len(config.tickers)
            startup_area = "dry-run startup" if config.dry_run else "Alpaca startup"
            message = f"{startup_area} failed: {exc}"
            logger.error(message)
            dependencies.send_alert(config, logger, f"Error: {message}")
            summary = build_summary(config, stats)
            logger.info(summary)
            dependencies.send_alert(config, logger, summary)
            return 1

        completed_actions: set[tuple[str, str]] = set()
        for ticker in config.tickers:
            try:
                process_ticker(
                    config=config,
                    conn=conn,
                    logger=logger,
                    ticker=ticker,
                    positions=positions,
                    completed_actions=completed_actions,
                    alpaca_client=alpaca_client,
                    stats=stats,
                    dependencies=dependencies,
                )
            except Exception as exc:
                stats.failed_tickers += 1
                message = f"{ticker} failed: {exc}"
                logger.exception(message)
                dependencies.write_trade_log(
                    conn=conn,
                    config=config,
                    ticker=ticker,
                    signal="ERROR",
                    order_status="error",
                    error=str(exc),
                )
                dependencies.send_alert(config, logger, f"Error: {message}")

        summary = build_summary(config, stats)
        logger.info(summary)
        dependencies.send_alert(config, logger, summary)
        return 0 if stats.failed_tickers == 0 else 1
    finally:
        conn.close()
