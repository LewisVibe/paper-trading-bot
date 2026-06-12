from __future__ import annotations

import argparse
import csv
import logging
import math
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


def _early_report_only_route() -> None:
    if sys.argv[1:] == ["--vps-monitoring-status"]:
        from trading_bot.research.vps_monitoring_status import print_vps_monitoring_status

        raise SystemExit(print_vps_monitoring_status())
    if sys.argv[1:] == ["--vps-daily-monitoring-summary"]:
        from trading_bot.research.vps_daily_monitoring_summary import print_vps_daily_monitoring_summary

        raise SystemExit(print_vps_daily_monitoring_summary())
    if sys.argv[1:] == ["--market-monitor-scheduling-readiness-report"]:
        from trading_bot.research.market_monitor_scheduling import print_market_monitor_scheduling_readiness_report

        raise SystemExit(print_market_monitor_scheduling_readiness_report())


_early_report_only_route()

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from trading_bot.alpaca_client import (
    get_open_orders_for_ticker,
    normalize_order_side,
    normalize_order_status,
    pending_quantity_for_side,
    refresh_order_status,
    validate_alpaca_asset_for_order,
)
from trading_bot.config import AppConfig, ConfigError, default_research_universe_tickers, load_config
from trading_bot.database import init_database, insert_trade_log
from trading_bot.discord_alerts import send_discord_alert
from trading_bot.execution import decide_trade
from trading_bot.logging_setup import setup_logging
from trading_bot.market_data import (
    configure_yfinance_cache,
    download_backtest_prices,
    download_close_prices,
    download_slow_sma_preview_prices,
)
from trading_bot.output import (
    format_slow_sma_action_preview_error_row,
    format_slow_sma_action_preview_table_header,
    format_slow_sma_action_preview_table_row,
    format_slow_sma_execution_error_row,
    format_slow_sma_execution_table_header,
    format_slow_sma_execution_table_row,
    format_slow_sma_preview_error_row,
    format_slow_sma_preview_table_header,
    format_slow_sma_preview_table_row,
)
from trading_bot.positions import (
    POSITION_FLAT,
    POSITION_LONG,
    POSITION_SHORT,
    Position,
    decimal_from_any,
    format_decimal,
    get_alpaca_positions,
    get_simulated_positions,
)
from trading_bot.strategies.breakout import (
    adjusted_breakout_buy_fill,
    adjusted_breakout_sell_fill,
    atr_trailing_stop_exit,
    is_252_day_high_breakout,
    sma_100_exit,
    volume_confirmation,
)
from trading_bot.research.backtesting import (
    BacktestResult,
    BacktestTrade,
    StrategyPortfolioResult,
    build_comparison_result,
    build_period_comparison_results,
    build_strategy_portfolio_results,
    build_strategy_robustness_summary,
    calculate_annualised_volatility_pct,
    calculate_cagr_pct,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    format_backtest_result,
    print_portfolio_summary,
    print_ranked_portfolio_summary,
    print_ranked_robustness_summary,
    print_ranked_sma_sensitivity_summary,
    print_ranked_strategy_summary,
    print_ranked_trend_stress_test_summary,
    sma_sensitivity_strategy_name,
    trend_stress_strategy_name,
    write_backtest_results,
    write_backtest_trades,
    write_sma_sensitivity_portfolio,
    write_sma_sensitivity_results,
    write_strategy_comparison_results,
    write_strategy_comparison_trades,
    write_strategy_portfolio_comparison,
    write_strategy_portfolio_equity_curves,
    write_strategy_robustness_summary,
    write_strategy_ticker_equity_curves,
    write_trend_stress_test_portfolio,
    write_trend_stress_test_results,
)
from trading_bot.research.costs import CostModel, adjusted_buy_fill_price, adjusted_sell_fill_price
from trading_bot.research.crypto import run_crypto_research_preview_files
from trading_bot.research.crypto_cost_stress import generate_crypto_cost_stress_report
from trading_bot.research.crypto_lab import run_crypto_strategy_lab_files
from trading_bot.research.crypto_robustness import generate_crypto_robustness_report
from trading_bot.research.crypto_signal_preview import generate_crypto_signal_preview
from trading_bot.research.defensive import generate_defensive_strategy_report
from trading_bot.research.plotting import plot_strategy_results
from trading_bot.research.promoted_actions import (
    build_promoted_action_preview_rows,
    build_promoted_action_summary,
    read_promoted_strategy_preview,
    write_promoted_action_preview,
)
from trading_bot.research.promoted_preview import (
    build_promoted_preview_rows,
    build_promoted_preview_summary,
    read_preview_candidates,
    unsupported_preview_row,
    write_promoted_preview,
)
from trading_bot.research.promoted_consensus import run_promoted_consensus_preview_files
from trading_bot.research.promoted_decision import run_promoted_decision_preview_files
from trading_bot.research.promoted_risk import run_promoted_risk_preview_files
from trading_bot.research.promotion import generate_strategy_promotion_report
from trading_bot.research.reporting import generate_research_report
from trading_bot.research.strategy_improvement_lab import (
    run_strategy_improvement_lab_files,
    show_strategy_improvement_lab_file,
)
from trading_bot.research.strategy_improvement_robustness import (
    generate_strategy_improvement_robustness,
    show_strategy_improvement_robustness_file,
)
from trading_bot.research.strategy_improvement_diagnostics import (
    generate_strategy_improvement_diagnostics,
    show_strategy_improvement_diagnostics_file,
)
from trading_bot.research.growth_biased_stricter_validation import (
    generate_growth_biased_stricter_validation,
    show_growth_biased_stricter_validation_file,
)
from trading_bot.research.growth_biased_stricter_promotion_readiness import (
    generate_growth_biased_stricter_promotion_readiness,
    show_growth_biased_stricter_promotion_readiness_file,
)
from trading_bot.research.growth_biased_stricter_manual_review_pack import (
    generate_growth_biased_stricter_manual_review_pack,
    show_growth_biased_stricter_manual_review_pack_file,
)
from trading_bot.research.growth_biased_stricter_threshold_neighbourhood import (
    generate_growth_biased_stricter_threshold_neighbourhood,
    show_growth_biased_stricter_threshold_neighbourhood_file,
)
from trading_bot.research.growth_biased_stricter_cost_turnover_stress import (
    generate_growth_biased_stricter_cost_turnover_stress,
    show_growth_biased_stricter_cost_turnover_stress_file,
)
from trading_bot.research.growth_biased_stricter_persistence_filter import (
    generate_growth_biased_stricter_persistence_filter,
    show_growth_biased_stricter_persistence_filter_file,
)
from trading_bot.research.walk_forward import generate_walk_forward_report
from trading_bot.runners.research_reports import (
    run_build_etf_breadth_price_history_command,
    run_build_research_dashboard_command,
    run_crypto_period_diagnostics_command,
    run_crypto_research_state_report_command,
    run_crypto_strategy_decision_report_command,
    run_crypto_strategy_report_command,
    run_defensive_allocation_decision_report_command,
    run_defensive_allocation_preview_command,
    run_defensive_allocation_risk_preview_command,
    run_defensive_candidate_comparison_command,
    run_defensive_execution_readiness_report_command,
    run_defensive_research_state_report_command,
    run_deployment_readiness_report_command,
    run_drawdown_period_report_command,
    run_etf_breadth_regime_backtest_command,
    run_etf_breadth_regime_decision_report_command,
    run_etf_breadth_regime_robustness_command,
    run_etf_defensive_drawdown_comparison_command,
    run_etf_rotation_robustness_command,
    run_execution_eligibility_report_command,
    run_paper_execution_protection_report_command,
    run_paper_kill_switch_gate_report_command,
    run_paper_kill_switch_readiness_report_command,
    run_normal_bot_execution_policy_report_command,
    run_market_monitor_snapshot_command,
    run_market_monitor_scheduling_readiness_report_command,
    run_monitor_lockfile_readiness_report_command,
    run_market_monitor_quality_report_command,
    run_plot_etf_defensive_comparison_command,
    run_refresh_market_monitor_command,
    run_show_market_monitor_command,
    run_portfolio_risk_policy_report_command,
    run_refresh_promoted_review_command,
    run_refresh_defensive_research_command,
    run_show_promoted_decision_command,
    run_show_crypto_monitor_command,
    run_show_portfolio_risk_policy_command,
    run_show_promoted_actions_command,
    run_show_promoted_risk_command,
    run_short_hedge_backtest_command,
    run_short_selling_readiness_report_command,
    run_short_strategy_lab_command,
    run_ticker_universe_readiness_report_command,
    run_vol_managed_etf_backtest_command,
    run_vol_managed_etf_robustness_command,
    run_vps_operations_readiness_report_command,
)
from trading_bot.safety.paper_kill_switch import evaluate_paper_kill_switch_gate
from trading_bot.strategies.adaptive import select_adaptive_momentum_assets
from trading_bot.strategies.rotation import (
    buy_and_hold_equity_curve,
    equal_weight_buy_and_hold_equity_curve,
    select_top_momentum_etfs,
    should_skip_rebalance_trade,
)
from trading_bot.strategies.sma import (
    SIGNAL_BUY,
    SIGNAL_HOLD,
    SIGNAL_SELL,
    SMA_SENSITIVITY_PAIRS,
    TREND_STRESS_TEST_PAIRS,
    SignalResult,
    SlowSmaPreviewRow,
    calculate_signal,
    calculate_slow_sma_preview_row,
    comparison_entry_signal,
    comparison_exit_signal,
    crossed_above,
    crossed_below,
    detect_sma_signal,
    prepare_sma_sensitivity_data,
    prepare_strategy_comparison_data,
    prepare_trend_stress_test_data,
)

TREND_STRESS_TEST_SLIPPAGE_BPS = [0, 5, 10, 25, 50]
DEFAULT_ETF_ROTATION_UNIVERSE = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLY",
    "XLP",
    "XLI",
    "XLU",
    "TLT",
    "GLD",
]
ETF_ROTATION_TOP_N = 3
MIN_REBALANCE_NOTIONAL = 100.0
ADAPTIVE_RISK_ASSETS = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLY",
    "XLI",
]
ADAPTIVE_DEFENSIVE_ASSETS = ["TLT", "GLD", "XLP", "XLU"]
ADAPTIVE_TOP_N = 3


class ManualOrderError(RuntimeError):
    """Raised when the manual paper-order smoke test is not safe to submit."""


@dataclass
class RunStats:
    tickers_processed: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    skipped_trades: int = 0
    failed_tickers: int = 0
    submitted_trades: int = 0


@dataclass
class SlowSmaActionPreviewRow:
    ticker: str
    date: str
    trend_state: str
    signal: str
    desired_position: str
    current_position: str
    current_qty: Decimal
    proposed_action: str
    open_order_exists: bool
    open_order_side: str
    open_order_qty: Decimal
    close: float
    short_sma: float
    long_sma: float
    days_since_last_crossover: int | None
    reason: str
    position_source: str


@dataclass
class SlowSmaExecutionStats:
    tickers_processed: int = 0
    submitted_orders: int = 0
    skipped_actions: int = 0
    no_order_needed: int = 0
    failed_tickers: int = 0


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def decimal_to_float(value: Decimal) -> float:
    return float(value)


def parse_order_test_quantity(value: str) -> Decimal:
    try:
        quantity = Decimal(value)
    except InvalidOperation as exc:
        raise ManualOrderError(f"Order quantity must be a positive number, not {value!r}.") from exc

    if not quantity.is_finite() or quantity <= 0:
        raise ManualOrderError("Order quantity must be a finite positive number.")
    return quantity


def submit_alpaca_order(client: TradingClient, ticker: str, side: str, quantity: Decimal):
    order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
    order_request = MarketOrderRequest(
        symbol=ticker,
        qty=decimal_to_float(quantity),
        side=order_side,
        time_in_force=TimeInForce.DAY,
    )
    return client.submit_order(order_data=order_request)


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
) -> None:
    logger.info("Processing %s", ticker)
    stats.tickers_processed += 1

    close_prices = download_close_prices(config, ticker)
    result = calculate_signal(config, close_prices)
    update_signal_stats(stats, result.signal)

    position_before = positions.get(ticker, Position())
    decision = decide_trade(
        result.signal,
        position_before,
        config.allow_shorting,
        config.order_quantity,
    )

    if not decision.should_trade:
        if result.signal != SIGNAL_HOLD:
            stats.skipped_trades += 1
            logger.info("%s %s skipped: %s", ticker, result.signal, decision.reason)

        insert_trade_log(
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

    action_key = (ticker, decision.action)
    if action_key in completed_actions:
        stats.skipped_trades += 1
        reason = "Duplicate trade action already completed for this ticker during this run."
        logger.info("%s %s skipped: %s", ticker, result.signal, reason)
        insert_trade_log(
            conn=conn,
            config=config,
            ticker=ticker,
            signal=result.signal,
            position_before=position_before,
            position_after=position_before,
            quantity=0,
            last_close=result.last_close,
            short_ma=result.short_ma,
            long_ma=result.long_ma,
            order_status="skipped",
            error=reason,
        )
        return

    if not config.dry_run:
        if alpaca_client is None:
            raise RuntimeError("Alpaca client is not available.")

        is_valid_asset, asset_error = validate_alpaca_asset_for_order(
            alpaca_client,
            ticker,
            requires_shortable=decision.action == "open_short",
        )
        if not is_valid_asset:
            stats.skipped_trades += 1
            logger.warning("%s %s skipped: %s", ticker, result.signal, asset_error)
            insert_trade_log(
                conn=conn,
                config=config,
                ticker=ticker,
                signal=result.signal,
                position_before=position_before,
                position_after=position_before,
                quantity=0,
                last_close=result.last_close,
                short_ma=result.short_ma,
                long_ma=result.long_ma,
                order_status="skipped",
                error=asset_error,
            )
            return

        open_orders = get_open_orders_for_ticker(alpaca_client, ticker)
        if decision.action in ("close_long", "close_short"):
            reserved_side = "sell" if decision.action == "close_long" else "buy"
            reserved_quantity = pending_quantity_for_side(open_orders, reserved_side)
            remaining_closeable_quantity = position_before.abs_quantity - reserved_quantity
            if remaining_closeable_quantity <= 0:
                stats.skipped_trades += 1
                reason = (
                    f"Existing open {reserved_side} order(s) already reserve the closeable "
                    f"{ticker} position."
                )
                logger.warning("%s %s skipped: %s", ticker, result.signal, reason)
                insert_trade_log(
                    conn=conn,
                    config=config,
                    ticker=ticker,
                    signal=result.signal,
                    position_before=position_before,
                    position_after=position_before,
                    quantity=0,
                    last_close=result.last_close,
                    short_ma=result.short_ma,
                    long_ma=result.long_ma,
                    order_status="skipped",
                    error=reason,
                )
                send_discord_alert(config, logger, f"Warning: {ticker} skipped. {reason}")
                return

        if open_orders:
            stats.skipped_trades += 1
            reason = f"An open Alpaca order already exists for {ticker}; skipping new order."
            logger.warning("%s %s skipped: %s", ticker, result.signal, reason)
            insert_trade_log(
                conn=conn,
                config=config,
                ticker=ticker,
                signal=result.signal,
                position_before=position_before,
                position_after=position_before,
                quantity=0,
                last_close=result.last_close,
                short_ma=result.short_ma,
                long_ma=result.long_ma,
                order_status="skipped",
                error=reason,
            )
            send_discord_alert(config, logger, f"Warning: {ticker} skipped. {reason}")
            return

    if config.dry_run:
        order_id = ""
        order_status = "dry_run"
        logger.info(
            "Dry run trade: %s %s %s share(s), action=%s",
            decision.side,
            format_decimal(decision.trade_quantity),
            ticker,
            decision.action,
        )
    else:
        order = submit_alpaca_order(
            alpaca_client,
            ticker,
            decision.side,
            decision.trade_quantity,
        )
        order_id = str(getattr(order, "id", ""))
        order_status = normalize_order_status(getattr(order, "status", "submitted"))
        logger.info(
            "Submitted Alpaca paper order: %s %s %s share(s), status=%s, order_id=%s",
            decision.side,
            format_decimal(decision.trade_quantity),
            ticker,
            order_status,
            order_id,
        )

    completed_actions.add(action_key)
    positions[ticker] = decision.position_after
    stats.submitted_trades += 1

    insert_trade_log(
        conn=conn,
        config=config,
        ticker=ticker,
        signal=result.signal,
        side=decision.side,
        action=decision.action,
        position_before=position_before,
        position_after=decision.position_after,
        quantity=decimal_to_float(decision.trade_quantity),
        last_close=result.last_close,
        short_ma=result.short_ma,
        long_ma=result.long_ma,
        order_id=order_id,
        order_status=order_status,
    )

    send_discord_alert(
        config,
        logger,
        (
            f"Trade: {ticker} {decision.side.upper()} {format_decimal(decision.trade_quantity)} "
            f"({decision.action}, signal {result.signal}, status {order_status})"
        ),
    )


def run_bot(config: AppConfig, logger: logging.Logger) -> int:
    conn = init_database(config.database_path)
    stats = RunStats()

    logger.info("Starting bot. dry_run=%s allow_shorting=%s", config.dry_run, config.allow_shorting)
    configure_yfinance_cache(config, logger)
    send_discord_alert(
        config,
        logger,
        f"Bot started. dry_run={config.dry_run}, allow_shorting={config.allow_shorting}",
    )

    alpaca_client: TradingClient | None = None
    try:
        try:
            if config.dry_run:
                positions = get_simulated_positions(conn)
            else:
                alpaca_client = TradingClient(
                    config.alpaca_api_key,
                    config.alpaca_secret_key,
                    paper=True,
                )
                positions = get_alpaca_positions(alpaca_client)
        except Exception as exc:
            stats.failed_tickers = len(config.tickers)
            startup_area = "dry-run startup" if config.dry_run else "Alpaca startup"
            message = f"{startup_area} failed: {exc}"
            logger.error(message)
            send_discord_alert(config, logger, f"Error: {message}")
            summary = build_summary(config, stats)
            logger.info(summary)
            send_discord_alert(config, logger, summary)
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
                )
            except Exception as exc:
                stats.failed_tickers += 1
                message = f"{ticker} failed: {exc}"
                logger.exception(message)
                insert_trade_log(
                    conn=conn,
                    config=config,
                    ticker=ticker,
                    signal="ERROR",
                    order_status="error",
                    error=str(exc),
                )
                send_discord_alert(config, logger, f"Error: {message}")

        summary = build_summary(config, stats)
        logger.info(summary)
        send_discord_alert(config, logger, summary)
        return 0 if stats.failed_tickers == 0 else 1
    finally:
        conn.close()


def run_paper_order_test(
    config: AppConfig,
    logger: logging.Logger,
    ticker: str,
    side: str,
    quantity_text: str,
    confirm_paper_order: bool,
) -> int:
    conn = None
    try:
        ticker = ticker.strip().upper()
        side = side.strip().lower()
        quantity = parse_order_test_quantity(quantity_text)

        logger.info(
            "Starting manual paper-order test: ticker=%s side=%s quantity=%s",
            ticker,
            side,
            format_decimal(quantity),
        )

        if side not in ("buy", "sell"):
            raise ManualOrderError("Order side must be 'buy' or 'sell'.")

        if ticker not in config.tickers:
            raise ManualOrderError(f"{ticker} is not listed in config.json tickers.")

        if not config.alpaca_paper:
            raise ManualOrderError("alpaca.paper must be true for manual paper-order tests.")

        if config.dry_run and not confirm_paper_order:
            raise ManualOrderError(
                "config.json has dry_run=true. Re-run with --confirm-paper-order to submit one paper order."
            )

        kill_switch_decision = evaluate_paper_kill_switch_gate(
            alpaca_paper=config.alpaca_paper,
            dry_run=config.dry_run,
            explicit_paper_execution_requested=confirm_paper_order,
            allow_shorting=config.allow_shorting,
            paper_kill_switch_enabled=getattr(config, "paper_kill_switch_enabled", None),
            execution_eligibility_blocked=manual_paper_order_execution_eligibility_blocked(),
            defensive_decision_blocked=manual_paper_order_defensive_decision_blocked(),
            explicit_confirmation=confirm_paper_order,
            command_name="paper_order_test",
        )
        if not kill_switch_decision.allowed:
            print("PAPER ORDER TEST BLOCKED BY PAPER KILL-SWITCH PREFLIGHT.")
            print("No orders were created, submitted, or cancelled.")
            print("Reasons:")
            for reason in kill_switch_decision.reasons:
                print(f"- {reason}")
            print(kill_switch_decision.required_next_step)
            print("No execution approval was granted.")
            logger.warning(
                "Manual paper-order test blocked by paper kill-switch preflight: %s",
                "; ".join(kill_switch_decision.reasons),
            )
            return 2

        if not config.alpaca_api_key or not config.alpaca_secret_key:
            raise ManualOrderError("Alpaca paper API key and secret key are required.")

        conn = init_database(config.database_path)
        order_config = replace(config, dry_run=False)

        alpaca_client = TradingClient(
            config.alpaca_api_key,
            config.alpaca_secret_key,
            paper=True,
        )

        positions = get_alpaca_positions(alpaca_client)
        position_before = positions.get(ticker, Position())

        is_valid_asset, asset_error = validate_alpaca_asset_for_order(
            alpaca_client,
            ticker,
            requires_shortable=False,
        )
        if not is_valid_asset:
            raise ManualOrderError(asset_error)

        open_orders = get_open_orders_for_ticker(alpaca_client, ticker)
        if open_orders:
            message = f"An open Alpaca order already exists for {ticker}; manual test order skipped."
            logger.warning(message)
            insert_trade_log(
                conn=conn,
                config=order_config,
                ticker=ticker,
                signal="MANUAL",
                side=side,
                action="manual_paper_order",
                position_before=position_before,
                position_after=position_before,
                quantity=0,
                order_status="skipped",
                error=message,
            )
            send_discord_alert(config, logger, f"Warning: {message}")
            return 1

        order = submit_alpaca_order(alpaca_client, ticker, side, quantity)
        order_id = str(getattr(order, "id", ""))
        order_status = normalize_order_status(getattr(order, "status", "submitted"))
        order_status = refresh_order_status(
            alpaca_client,
            logger,
            order_id,
            order_status,
            timeout_seconds=10,
        )
        position_after = estimate_manual_position_after(position_before, side, quantity, order_status)

        insert_trade_log(
            conn=conn,
            config=order_config,
            ticker=ticker,
            signal="MANUAL",
            side=side,
            action="manual_paper_order",
            position_before=position_before,
            position_after=position_after,
            quantity=decimal_to_float(quantity),
            order_id=order_id,
            order_status=order_status,
        )

        message = (
            f"Manual paper-order test submitted: {ticker} {side.upper()} "
            f"{format_decimal(quantity)} share(s), status {order_status}, order_id {order_id}"
        )
        logger.info(message)
        send_discord_alert(config, logger, message)
        return 0
    except ManualOrderError as exc:
        message = f"Manual paper-order test refused: {exc}"
        logger.error(message)
        send_discord_alert(config, logger, f"Error: {message}")
        return 2
    except Exception as exc:
        message = f"Manual paper-order test failed: {exc}"
        logger.error(message)
        send_discord_alert(config, logger, f"Error: {message}")
        return 1
    finally:
        if conn is not None:
            conn.close()


def manual_paper_order_execution_eligibility_blocked(
    path: Path = Path("data") / "execution_eligibility_report.csv",
) -> bool:
    rows = read_saved_csv_rows(path)
    final = next((row for row in rows if row.get("eligibility_check_name") == "final_execution_eligibility"), None)
    if not final:
        return True
    if any(str(row.get("execution_approved", "")).strip().lower() != "false" for row in rows):
        return True
    return final.get("eligibility_status") not in {"pass", "eligible", "not_blocked"}


def manual_paper_order_defensive_decision_blocked(
    path: Path = Path("data") / "defensive_allocation_decision_report.csv",
) -> bool:
    rows = read_saved_csv_rows(path)
    overall = next((row for row in rows if row.get("decision_area") == "overall_decision"), None)
    if not overall:
        return True
    if any(str(row.get("execution_approved", "")).strip().lower() != "false" for row in rows):
        return True
    return str(overall.get("can_progress_to_execution_design", "")).strip().lower() != "true"


def read_saved_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def estimate_manual_position_after(
    position_before: Position,
    side: str,
    quantity: Decimal,
    order_status: str,
) -> Position:
    if order_status != "filled":
        return position_before

    if side == "buy":
        return Position(position_before.quantity + quantity)
    return Position(position_before.quantity - quantity)


def run_backtest(config: AppConfig, logger: logging.Logger) -> int:
    configure_yfinance_cache(config, logger)
    results: list[BacktestResult] = []
    trades: list[BacktestTrade] = []
    portfolio_results: list[StrategyPortfolioResult] = []
    errors: list[str] = []
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))

    print("Backtest: regime_sma_vol_filter")
    print("ticker,total_return,buy_and_hold,trades,win_rate,avg_trade,max_drawdown,time_in_market")

    try:
        regime_data = download_backtest_prices(config, config.strategy.regime_ticker)
    except Exception as exc:
        logger.error("Backtest failed: could not download regime ticker %s: %s", config.strategy.regime_ticker, exc)
        write_backtest_results(config, results, cost_model)
        write_backtest_trades(config, trades, cost_model)
        print(f"Regime ticker error: {config.strategy.regime_ticker} - {exc}")
        return 1

    for ticker in config.tickers:
        try:
            ticker_data = download_backtest_prices(config, ticker)
            result, ticker_trades = backtest_ticker(config, ticker, ticker_data, regime_data, cost_model)
            results.append(result)
            trades.extend(ticker_trades)
            print(format_backtest_result(result))
        except Exception as exc:
            errors.append(ticker)
            logger.error("Backtest failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")

    write_backtest_results(config, results, cost_model)
    write_backtest_trades(config, trades, cost_model)
    print_portfolio_summary(config, results, trades, errors)
    print(f"Saved results to {config.backtest.output_csv}")
    print(f"Saved trades to {config.backtest.trades_csv}")
    return 0 if results else 1


def run_etf_rotation_backtest(config: AppConfig, logger: logging.Logger) -> int:
    configure_yfinance_cache(config, logger)
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))
    tickers = DEFAULT_ETF_ROTATION_UNIVERSE
    data_by_ticker = {}

    print("ETF rotation backtest")
    print(f"Tickers: {len(tickers)}")
    print(f"Top N: {ETF_ROTATION_TOP_N}")

    for ticker in tickers:
        try:
            data_by_ticker[ticker] = download_backtest_prices(config, ticker)
        except Exception as exc:
            logger.error("ETF rotation backtest failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")

    if "SPY" not in data_by_ticker:
        write_etf_rotation_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("SPY regime ticker is required for ETF rotation.")
        return 1

    tradable_tickers = [ticker for ticker in tickers if ticker in data_by_ticker]
    if len(tradable_tickers) < ETF_ROTATION_TOP_N:
        write_etf_rotation_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("Not enough ETF data for rotation backtest.")
        return 1

    common_index = None
    for ticker in tradable_tickers:
        index = data_by_ticker[ticker].index
        common_index = index if common_index is None else common_index.intersection(index)
    common_index = common_index.sort_values()

    if len(common_index) < 254:
        write_etf_rotation_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print(f"Not enough shared ETF history. Need at least 254 rows, got {len(common_index)}.")
        return 1

    aligned = {
        ticker: data_by_ticker[ticker].loc[common_index]
        for ticker in tradable_tickers
    }
    rebalance_indices = get_monthly_rebalance_indices(common_index)
    if not rebalance_indices:
        write_etf_rotation_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("No monthly rebalance dates found.")
        return 1

    cash = config.backtest.starting_cash
    positions: dict[str, float] = {}
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []

    for index, day in enumerate(common_index):
        equity = cash + sum(
            quantity * float(aligned[ticker].iloc[index]["close"])
            for ticker, quantity in positions.items()
        )
        equity_curve.append(
            {
                "date": day.date().isoformat(),
                "equity": equity,
            }
        )

        if index not in rebalance_indices or index >= len(common_index) - 1:
            continue

        price_history = {
            ticker: [float(value) for value in aligned[ticker].iloc[: index + 1]["close"]]
            for ticker in tradable_tickers
        }
        spy_prices = price_history["SPY"]
        try:
            selections = select_top_momentum_etfs(
                price_history,
                spy_prices,
                top_n=ETF_ROTATION_TOP_N,
            )
        except ValueError:
            continue

        target_tickers = [selection.ticker for selection in selections]
        next_index = index + 1
        next_day = common_index[next_index].date().isoformat()
        open_prices = {
            ticker: float(aligned[ticker].iloc[next_index]["open"])
            for ticker in tradable_tickers
        }
        portfolio_value = cash + sum(
            quantity * open_prices[ticker]
            for ticker, quantity in positions.items()
        )

        for ticker in sorted(set(positions) - set(target_tickers)):
            quantity = positions.pop(ticker)
            fill_price = float(adjusted_sell_fill_price(open_prices[ticker], cost_model))
            cash += quantity * fill_price
            trades.append(
                build_etf_rotation_trade_row(
                    next_day,
                    ticker,
                    "sell",
                    "removed_from_top_n",
                    quantity,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

        if not target_tickers:
            continue

        target_value = portfolio_value / len(target_tickers)

        for ticker in target_tickers:
            current_quantity = positions.get(ticker, 0.0)
            current_value = current_quantity * open_prices[ticker]
            if current_value <= target_value:
                continue
            sell_value = current_value - target_value
            fill_price = float(adjusted_sell_fill_price(open_prices[ticker], cost_model))
            if should_skip_rebalance_trade(sell_value, MIN_REBALANCE_NOTIONAL):
                continue
            quantity_to_sell = min(current_quantity, sell_value / fill_price)
            if quantity_to_sell <= 0:
                continue
            positions[ticker] = current_quantity - quantity_to_sell
            cash += quantity_to_sell * fill_price
            trades.append(
                build_etf_rotation_trade_row(
                    next_day,
                    ticker,
                    "sell",
                    "rebalance_reduce",
                    quantity_to_sell,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

        for ticker in target_tickers:
            current_quantity = positions.get(ticker, 0.0)
            current_value = current_quantity * open_prices[ticker]
            if current_value >= target_value:
                continue
            buy_value = min(target_value - current_value, cash)
            if current_quantity > 0 and should_skip_rebalance_trade(buy_value, MIN_REBALANCE_NOTIONAL):
                continue
            fill_price = float(adjusted_buy_fill_price(open_prices[ticker], cost_model))
            quantity_to_buy = buy_value / fill_price if fill_price > 0 else 0.0
            if quantity_to_buy <= 0:
                continue
            positions[ticker] = current_quantity + quantity_to_buy
            cash -= quantity_to_buy * fill_price
            trades.append(
                build_etf_rotation_trade_row(
                    next_day,
                    ticker,
                    "buy",
                    "target_top_n",
                    quantity_to_buy,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

    spy_benchmark_curve = buy_and_hold_equity_curve(
        [float(value) for value in aligned["SPY"]["close"]],
        config.backtest.starting_cash,
    )
    qqq_benchmark_curve = (
        buy_and_hold_equity_curve(
            [float(value) for value in aligned["QQQ"]["close"]],
            config.backtest.starting_cash,
        )
        if "QQQ" in aligned
        else []
    )
    equal_weight_benchmark_curve = equal_weight_buy_and_hold_equity_curve(
        {
            ticker: [float(value) for value in aligned[ticker]["close"]]
            for ticker in tradable_tickers
        },
        config.backtest.starting_cash,
    )
    results = build_etf_rotation_result_rows(
        equity_curve,
        trades,
        config.backtest.starting_cash,
        ETF_ROTATION_TOP_N,
        len(tradable_tickers),
        MIN_REBALANCE_NOTIONAL,
        {
            "spy": spy_benchmark_curve,
            "qqq": qqq_benchmark_curve,
            "equal_weight": equal_weight_benchmark_curve,
        },
    )

    write_etf_rotation_outputs(results, trades, equity_curve, cost_model, MIN_REBALANCE_NOTIONAL)
    full_period_result = next(
        (result for result in results if result.get("period") == "full_period"),
        results[0],
    )
    print(
        "monthly_etf_momentum_rotation,"
        f"{full_period_result['total_return_pct']:.2f}%,"
        f"{full_period_result['max_drawdown_pct']:.2f}%,"
        f"{len(trades)} trades"
    )
    print("Saved ETF rotation results to data/etf_rotation_results.csv")
    print("Saved ETF rotation trades to data/etf_rotation_trades.csv")
    print("Saved ETF rotation equity curve to data/etf_rotation_equity_curve.csv")
    return 0


def get_monthly_rebalance_indices(index) -> set[int]:
    rebalance_indices: set[int] = set()
    for position in range(len(index) - 1):
        current_month = (index[position].year, index[position].month)
        next_month = (index[position + 1].year, index[position + 1].month)
        if current_month != next_month:
            rebalance_indices.add(position)
    return rebalance_indices


def empty_etf_rotation_benchmark_metrics() -> dict[str, float]:
    return {
        "total_return_pct": 0.0,
        "cagr_pct": 0.0,
        "max_drawdown_pct": 0.0,
    }


def build_etf_rotation_result_rows(
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    starting_equity: float,
    top_n: int,
    universe_size: int,
    min_rebalance_notional: float,
    benchmark_curves: dict[str, list[float]] | None = None,
) -> list[dict[str, Any]]:
    """Build full/in/out period rows from one completed ETF rotation run.

    The strategy simulation still runs once. These period rows are reporting
    slices only, so walk-forward analysis can compare in-sample and
    out-of-sample behaviour without changing the rotation rules.
    """
    benchmark_curves = benchmark_curves or {}
    periods = etf_rotation_period_slices(equity_curve)
    rows = []
    for period_name, start_index, end_index in periods:
        period_curve = equity_curve[start_index:end_index]
        equity_values = [float(row["equity"]) for row in period_curve]
        period_starting_equity = equity_values[0] if equity_values else starting_equity
        period_trades = filter_etf_rotation_trades_for_period(
            trades,
            period_curve[0]["date"] if period_curve else None,
            period_curve[-1]["date"] if period_curve else None,
        )
        spy_benchmark = build_etf_rotation_period_benchmark_metrics(
            benchmark_curves.get("spy", []),
            start_index,
            end_index,
        )
        qqq_benchmark = build_etf_rotation_period_benchmark_metrics(
            benchmark_curves.get("qqq", []),
            start_index,
            end_index,
        )
        equal_weight_benchmark = build_etf_rotation_period_benchmark_metrics(
            benchmark_curves.get("equal_weight", []),
            start_index,
            end_index,
        )
        rows.append(
            build_etf_rotation_result_row(
                period_name,
                equity_values,
                len(period_trades),
                top_n,
                universe_size,
                min_rebalance_notional,
                spy_benchmark,
                qqq_benchmark,
                equal_weight_benchmark,
                period_starting_equity,
            )
        )
    return rows


def etf_rotation_period_slices(equity_curve: list[dict[str, Any]]) -> list[tuple[str, int, int]]:
    if not equity_curve:
        return [("full_period", 0, 0), ("in_sample", 0, 0), ("out_of_sample", 0, 0)]

    total_rows = len(equity_curve)
    if total_rows < 3:
        return [
            ("full_period", 0, total_rows),
            ("in_sample", 0, total_rows),
            ("out_of_sample", 0, total_rows),
        ]

    split_index = int(total_rows * 0.7)
    split_index = max(1, min(total_rows - 1, split_index))
    return [
        ("full_period", 0, total_rows),
        ("in_sample", 0, split_index),
        ("out_of_sample", split_index, total_rows),
    ]


def filter_etf_rotation_trades_for_period(
    trades: list[dict[str, Any]],
    start_date: str | None,
    end_date: str | None,
) -> list[dict[str, Any]]:
    if start_date is None or end_date is None:
        return []
    return [
        trade
        for trade in trades
        if start_date <= str(trade.get("date", "")) <= end_date
    ]


def build_etf_rotation_result_row(
    period: str,
    equity_values: list[float],
    number_of_trades: int,
    top_n: int,
    universe_size: int,
    min_rebalance_notional: float,
    spy_benchmark: dict[str, float],
    qqq_benchmark: dict[str, float],
    equal_weight_benchmark: dict[str, float],
    starting_equity: float | None = None,
) -> dict[str, Any]:
    period_starting_equity = starting_equity if starting_equity is not None else (equity_values[0] if equity_values else 0.0)
    final_equity = equity_values[-1] if equity_values else period_starting_equity
    total_return_pct = (
        ((final_equity - period_starting_equity) / period_starting_equity) * 100
        if period_starting_equity > 0
        else 0.0
    )
    cagr_pct = calculate_cagr_pct(period_starting_equity, final_equity, len(equity_values))
    max_drawdown_pct = calculate_max_drawdown(equity_values) * 100
    return {
        "source_file": "etf_rotation_results.csv",
        "strategy_name": "monthly_etf_momentum_rotation",
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "starting_equity": period_starting_equity,
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "annualised_volatility_pct": calculate_annualised_volatility_pct(equity_values),
        "sharpe_ratio": calculate_sharpe_ratio(equity_values),
        "calmar_ratio": cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0.0,
        "number_of_trades": number_of_trades,
        "turnover_proxy_trades": number_of_trades,
        "top_n": top_n,
        "universe_size": universe_size,
        "min_rebalance_notional": min_rebalance_notional,
        "spy_buy_hold_total_return_pct": spy_benchmark["total_return_pct"],
        "spy_buy_hold_cagr_pct": spy_benchmark["cagr_pct"],
        "spy_buy_hold_max_drawdown_pct": spy_benchmark["max_drawdown_pct"],
        "qqq_buy_hold_total_return_pct": qqq_benchmark["total_return_pct"],
        "qqq_buy_hold_cagr_pct": qqq_benchmark["cagr_pct"],
        "qqq_buy_hold_max_drawdown_pct": qqq_benchmark["max_drawdown_pct"],
        "equal_weight_buy_hold_total_return_pct": equal_weight_benchmark["total_return_pct"],
        "equal_weight_buy_hold_cagr_pct": equal_weight_benchmark["cagr_pct"],
        "equal_weight_buy_hold_max_drawdown_pct": equal_weight_benchmark["max_drawdown_pct"],
    }


def build_etf_rotation_period_benchmark_metrics(
    benchmark_curve: list[float],
    start_index: int,
    end_index: int,
) -> dict[str, float]:
    period_curve = benchmark_curve[start_index:end_index]
    if not period_curve:
        return empty_etf_rotation_benchmark_metrics()
    return build_etf_rotation_benchmark_metrics_from_curve(period_curve, period_curve[0])


def build_etf_rotation_benchmark_metrics(
    close_prices: list[float],
    starting_equity: float,
) -> dict[str, float]:
    return build_etf_rotation_benchmark_metrics_from_curve(
        buy_and_hold_equity_curve(close_prices, starting_equity),
        starting_equity,
    )


def build_etf_rotation_benchmark_metrics_from_curve(
    equity_curve: list[float],
    starting_equity: float,
) -> dict[str, float]:
    if not equity_curve:
        return empty_etf_rotation_benchmark_metrics()
    final_equity = equity_curve[-1]
    return {
        "total_return_pct": ((final_equity - starting_equity) / starting_equity) * 100,
        "cagr_pct": calculate_cagr_pct(starting_equity, final_equity, len(equity_curve)),
        "max_drawdown_pct": calculate_max_drawdown(equity_curve) * 100,
    }


def build_etf_rotation_trade_row(
    date: str,
    ticker: str,
    side: str,
    reason: str,
    quantity: float,
    price: float,
    cost_model: CostModel,
    min_rebalance_notional: float,
) -> dict[str, Any]:
    return {
        "date": date,
        "ticker": ticker,
        "side": side,
        "reason": reason,
        "quantity": quantity,
        "price": price,
        "commission_per_trade": cost_model.commission_per_trade,
        "commission_bps": cost_model.commission_bps,
        "spread_bps": cost_model.spread_bps,
        "slippage_bps": cost_model.slippage_bps,
        "min_rebalance_notional": min_rebalance_notional,
    }


def write_etf_rotation_outputs(
    results: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
    cost_model: CostModel,
    min_rebalance_notional: float,
) -> None:
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    with (data_dir / "etf_rotation_results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "source_file",
                "strategy_name",
                "ticker_or_portfolio",
                "period",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "starting_equity",
                "final_equity",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "annualised_volatility_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
                "turnover_proxy_trades",
                "top_n",
                "universe_size",
                "spy_buy_hold_total_return_pct",
                "spy_buy_hold_cagr_pct",
                "spy_buy_hold_max_drawdown_pct",
                "qqq_buy_hold_total_return_pct",
                "qqq_buy_hold_cagr_pct",
                "qqq_buy_hold_max_drawdown_pct",
                "equal_weight_buy_hold_total_return_pct",
                "equal_weight_buy_hold_cagr_pct",
                "equal_weight_buy_hold_max_drawdown_pct",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    result["source_file"],
                    result["strategy_name"],
                    result["ticker_or_portfolio"],
                    result["period"],
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    result["min_rebalance_notional"],
                    round(result["starting_equity"], 2),
                    round(result["final_equity"], 2),
                    round(result["total_return_pct"], 4),
                    round(result["cagr_pct"], 4),
                    round(result["max_drawdown_pct"], 4),
                    round(result["annualised_volatility_pct"], 4),
                    round(result["sharpe_ratio"], 4),
                    round(result["calmar_ratio"], 4),
                    result["number_of_trades"],
                    result["turnover_proxy_trades"],
                    result["top_n"],
                    result["universe_size"],
                    round(result["spy_buy_hold_total_return_pct"], 4),
                    round(result["spy_buy_hold_cagr_pct"], 4),
                    round(result["spy_buy_hold_max_drawdown_pct"], 4),
                    round(result["qqq_buy_hold_total_return_pct"], 4),
                    round(result["qqq_buy_hold_cagr_pct"], 4),
                    round(result["qqq_buy_hold_max_drawdown_pct"], 4),
                    round(result["equal_weight_buy_hold_total_return_pct"], 4),
                    round(result["equal_weight_buy_hold_cagr_pct"], 4),
                    round(result["equal_weight_buy_hold_max_drawdown_pct"], 4),
                ]
            )

    with (data_dir / "etf_rotation_trades.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "ticker",
                "side",
                "reason",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "quantity",
                "price",
                "notional",
            ]
        )
        for trade in trades:
            writer.writerow(
                [
                    trade["date"],
                    trade["ticker"],
                    trade["side"],
                    trade["reason"],
                    trade["commission_per_trade"],
                    trade["commission_bps"],
                    trade["spread_bps"],
                    trade["slippage_bps"],
                    trade["min_rebalance_notional"],
                    round(trade["quantity"], 6),
                    round(trade["price"], 4),
                    round(trade["quantity"] * trade["price"], 2),
                ]
            )

    with (data_dir / "etf_rotation_equity_curve.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "equity",
            ]
        )
        for row in equity_curve:
            writer.writerow(
                [
                    row["date"],
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    round(row["equity"], 2),
                ]
            )


def run_adaptive_momentum_backtest(config: AppConfig, logger: logging.Logger) -> int:
    configure_yfinance_cache(config, logger)
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))
    tickers = list(dict.fromkeys([*ADAPTIVE_RISK_ASSETS, *ADAPTIVE_DEFENSIVE_ASSETS]))
    data_by_ticker = {}

    print("Adaptive risk-on/off momentum backtest")
    print(f"Tickers: {len(tickers)}")
    print(f"Top N: {ADAPTIVE_TOP_N}")

    for ticker in tickers:
        try:
            data_by_ticker[ticker] = download_backtest_prices(config, ticker)
        except Exception as exc:
            logger.error("Adaptive momentum backtest failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")

    if "SPY" not in data_by_ticker:
        write_adaptive_momentum_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("SPY regime ticker is required for adaptive momentum.")
        return 1

    tradable_tickers = [ticker for ticker in tickers if ticker in data_by_ticker]
    if len(tradable_tickers) < ADAPTIVE_TOP_N:
        write_adaptive_momentum_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("Not enough ETF data for adaptive momentum backtest.")
        return 1

    common_index = None
    for ticker in tradable_tickers:
        index = data_by_ticker[ticker].index
        common_index = index if common_index is None else common_index.intersection(index)
    common_index = common_index.sort_values()

    if len(common_index) < 254:
        write_adaptive_momentum_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print(f"Not enough shared ETF history. Need at least 254 rows, got {len(common_index)}.")
        return 1

    aligned = {
        ticker: data_by_ticker[ticker].loc[common_index]
        for ticker in tradable_tickers
    }
    rebalance_indices = get_monthly_rebalance_indices(common_index)
    if not rebalance_indices:
        write_adaptive_momentum_outputs([], [], [], cost_model, MIN_REBALANCE_NOTIONAL)
        print("No monthly rebalance dates found.")
        return 1

    cash = config.backtest.starting_cash
    positions: dict[str, float] = {}
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []

    for index, day in enumerate(common_index):
        equity = cash + sum(
            quantity * float(aligned[ticker].iloc[index]["close"])
            for ticker, quantity in positions.items()
        )
        equity_curve.append({"date": day.date().isoformat(), "equity": equity})

        if index not in rebalance_indices or index >= len(common_index) - 1:
            continue

        price_history = {
            ticker: [float(value) for value in aligned[ticker].iloc[: index + 1]["close"]]
            for ticker in tradable_tickers
        }
        risk_prices = {
            ticker: price_history[ticker]
            for ticker in ADAPTIVE_RISK_ASSETS
            if ticker in price_history
        }
        defensive_prices = {
            ticker: price_history[ticker]
            for ticker in ADAPTIVE_DEFENSIVE_ASSETS
            if ticker in price_history
        }
        try:
            selections = select_adaptive_momentum_assets(
                risk_prices,
                defensive_prices,
                price_history["SPY"],
                top_n=ADAPTIVE_TOP_N,
            )
        except ValueError:
            continue

        target_tickers = [selection.ticker for selection in selections]
        next_index = index + 1
        next_day = common_index[next_index].date().isoformat()
        open_prices = {
            ticker: float(aligned[ticker].iloc[next_index]["open"])
            for ticker in tradable_tickers
        }
        portfolio_value = cash + sum(
            quantity * open_prices[ticker]
            for ticker, quantity in positions.items()
        )

        for ticker in sorted(set(positions) - set(target_tickers)):
            quantity = positions.pop(ticker)
            fill_price = float(adjusted_sell_fill_price(open_prices[ticker], cost_model))
            cash += quantity * fill_price
            trades.append(
                build_adaptive_momentum_trade_row(
                    next_day,
                    ticker,
                    "sell",
                    "removed_from_target_assets",
                    quantity,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

        if not target_tickers:
            continue

        target_value = portfolio_value / len(target_tickers)

        for ticker in target_tickers:
            current_quantity = positions.get(ticker, 0.0)
            current_value = current_quantity * open_prices[ticker]
            if current_value <= target_value:
                continue
            sell_value = current_value - target_value
            if should_skip_rebalance_trade(sell_value, MIN_REBALANCE_NOTIONAL):
                continue
            fill_price = float(adjusted_sell_fill_price(open_prices[ticker], cost_model))
            quantity_to_sell = min(current_quantity, sell_value / fill_price)
            if quantity_to_sell <= 0:
                continue
            positions[ticker] = current_quantity - quantity_to_sell
            cash += quantity_to_sell * fill_price
            trades.append(
                build_adaptive_momentum_trade_row(
                    next_day,
                    ticker,
                    "sell",
                    "rebalance_reduce",
                    quantity_to_sell,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

        for ticker in target_tickers:
            current_quantity = positions.get(ticker, 0.0)
            current_value = current_quantity * open_prices[ticker]
            if current_value >= target_value:
                continue
            buy_value = min(target_value - current_value, cash)
            if current_quantity > 0 and should_skip_rebalance_trade(buy_value, MIN_REBALANCE_NOTIONAL):
                continue
            fill_price = float(adjusted_buy_fill_price(open_prices[ticker], cost_model))
            quantity_to_buy = buy_value / fill_price if fill_price > 0 else 0.0
            if quantity_to_buy <= 0:
                continue
            positions[ticker] = current_quantity + quantity_to_buy
            cash -= quantity_to_buy * fill_price
            trades.append(
                build_adaptive_momentum_trade_row(
                    next_day,
                    ticker,
                    "buy",
                    "target_adaptive_asset",
                    quantity_to_buy,
                    fill_price,
                    cost_model,
                    MIN_REBALANCE_NOTIONAL,
                )
            )

    results = build_adaptive_momentum_result_rows(
        equity_curve,
        trades,
        config.backtest.starting_cash,
        ADAPTIVE_TOP_N,
        len(tradable_tickers),
        MIN_REBALANCE_NOTIONAL,
        {
            "spy": buy_and_hold_equity_curve(
                [float(value) for value in aligned["SPY"]["close"]],
                config.backtest.starting_cash,
            ),
            "qqq": (
                buy_and_hold_equity_curve(
                    [float(value) for value in aligned["QQQ"]["close"]],
                    config.backtest.starting_cash,
                )
                if "QQQ" in aligned
                else []
            ),
            "equal_weight": equal_weight_buy_and_hold_equity_curve(
                {
                    ticker: [float(value) for value in aligned[ticker]["close"]]
                    for ticker in tradable_tickers
                },
                config.backtest.starting_cash,
            ),
        },
    )

    write_adaptive_momentum_outputs(results, trades, equity_curve, cost_model, MIN_REBALANCE_NOTIONAL)
    full_period_result = next(
        (result for result in results if result.get("period") == "full_period"),
        results[0],
    )
    print(
        "adaptive_risk_on_off_momentum,"
        f"{full_period_result['total_return_pct']:.2f}%,"
        f"{full_period_result['max_drawdown_pct']:.2f}%,"
        f"{len(trades)} trades"
    )
    print("Saved adaptive momentum results to data/adaptive_momentum_results.csv")
    print("Saved adaptive momentum trades to data/adaptive_momentum_trades.csv")
    print("Saved adaptive momentum equity curve to data/adaptive_momentum_equity_curve.csv")
    return 0


def empty_research_metrics() -> dict[str, float]:
    return {
        "final_equity": 0.0,
        "total_return_pct": 0.0,
        "cagr_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "annualised_volatility_pct": 0.0,
        "sharpe_ratio": 0.0,
        "calmar_ratio": 0.0,
    }


def build_adaptive_momentum_result_rows(
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    starting_equity: float,
    top_n: int,
    universe_size: int,
    min_rebalance_notional: float,
    benchmark_curves: dict[str, list[float]] | None = None,
) -> list[dict[str, Any]]:
    """Build reporting-only full/in/out rows from one adaptive backtest run."""
    benchmark_curves = benchmark_curves or {}
    rows = []
    for period_name, start_index, end_index in adaptive_momentum_period_slices(equity_curve):
        period_curve = equity_curve[start_index:end_index]
        equity_values = [float(row["equity"]) for row in period_curve]
        period_starting_equity = equity_values[0] if equity_values else starting_equity
        period_trades = filter_etf_rotation_trades_for_period(
            trades,
            period_curve[0]["date"] if period_curve else None,
            period_curve[-1]["date"] if period_curve else None,
        )
        rows.append(
            build_adaptive_momentum_result_row(
                period_name,
                equity_values,
                len(period_trades),
                top_n,
                universe_size,
                min_rebalance_notional,
                build_adaptive_momentum_period_benchmark_metrics(
                    benchmark_curves.get("spy", []),
                    start_index,
                    end_index,
                ),
                build_adaptive_momentum_period_benchmark_metrics(
                    benchmark_curves.get("qqq", []),
                    start_index,
                    end_index,
                ),
                build_adaptive_momentum_period_benchmark_metrics(
                    benchmark_curves.get("equal_weight", []),
                    start_index,
                    end_index,
                ),
                period_starting_equity,
            )
        )
    return rows


def adaptive_momentum_period_slices(equity_curve: list[dict[str, Any]]) -> list[tuple[str, int, int]]:
    return etf_rotation_period_slices(equity_curve)


def build_adaptive_momentum_period_benchmark_metrics(
    benchmark_curve: list[float],
    start_index: int,
    end_index: int,
) -> dict[str, float]:
    period_curve = benchmark_curve[start_index:end_index]
    if not period_curve:
        return empty_research_metrics()
    return build_research_equity_metrics(period_curve, period_curve[0])


def build_adaptive_momentum_result_row(
    period: str,
    equity_values: list[float],
    number_of_trades: int,
    top_n: int,
    universe_size: int,
    min_rebalance_notional: float,
    spy_benchmark: dict[str, float],
    qqq_benchmark: dict[str, float],
    equal_weight_benchmark: dict[str, float],
    starting_equity: float | None = None,
) -> dict[str, Any]:
    period_starting_equity = starting_equity if starting_equity is not None else (equity_values[0] if equity_values else 0.0)
    strategy_metrics = build_research_equity_metrics(equity_values, period_starting_equity)
    return {
        "source_file": "adaptive_momentum_results.csv",
        "strategy_name": "adaptive_risk_on_off_momentum",
        "ticker_or_portfolio": "portfolio",
        "period": period,
        "starting_equity": period_starting_equity,
        "final_equity": strategy_metrics["final_equity"],
        "number_of_trades": number_of_trades,
        "turnover_proxy_trades": number_of_trades,
        "top_n": top_n,
        "universe_size": universe_size,
        "min_rebalance_notional": min_rebalance_notional,
        **strategy_metrics,
        "spy": spy_benchmark,
        "qqq": qqq_benchmark,
        "equal_weight": equal_weight_benchmark,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_research_equity_metrics(
    equity_curve: list[float],
    starting_equity: float,
) -> dict[str, float]:
    if not equity_curve:
        return empty_research_metrics()
    final_equity = equity_curve[-1]
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    cagr_pct = calculate_cagr_pct(starting_equity, final_equity, len(equity_curve))
    return {
        "final_equity": final_equity,
        "total_return_pct": ((final_equity - starting_equity) / starting_equity) * 100,
        "cagr_pct": cagr_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "annualised_volatility_pct": calculate_annualised_volatility_pct(equity_curve),
        "sharpe_ratio": calculate_sharpe_ratio(equity_curve),
        "calmar_ratio": cagr_pct / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0.0,
    }


def relative_metric(value: float, benchmark_value: float) -> float:
    return value - benchmark_value


def build_adaptive_momentum_trade_row(
    date: str,
    ticker: str,
    side: str,
    reason: str,
    quantity: float,
    price: float,
    cost_model: CostModel,
    min_rebalance_notional: float,
) -> dict[str, Any]:
    return {
        "date": date,
        "ticker": ticker,
        "side": side,
        "reason": reason,
        "quantity": quantity,
        "price": price,
        "commission_per_trade": cost_model.commission_per_trade,
        "commission_bps": cost_model.commission_bps,
        "spread_bps": cost_model.spread_bps,
        "slippage_bps": cost_model.slippage_bps,
        "min_rebalance_notional": min_rebalance_notional,
    }


def write_adaptive_momentum_outputs(
    results: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
    cost_model: CostModel,
    min_rebalance_notional: float,
) -> None:
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    with (data_dir / "adaptive_momentum_results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "source_file",
                "strategy_name",
                "ticker_or_portfolio",
                "period",
                "starting_equity",
                "final_equity",
                "total_return_pct",
                "cagr_pct",
                "max_drawdown_pct",
                "annualised_volatility_pct",
                "sharpe_ratio",
                "calmar_ratio",
                "number_of_trades",
                "turnover_proxy_trades",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "spy_benchmark_total_return_pct",
                "spy_benchmark_cagr_pct",
                "spy_benchmark_max_drawdown_pct",
                "spy_benchmark_sharpe_ratio",
                "spy_benchmark_calmar_ratio",
                "qqq_benchmark_total_return_pct",
                "qqq_benchmark_cagr_pct",
                "qqq_benchmark_max_drawdown_pct",
                "qqq_benchmark_sharpe_ratio",
                "qqq_benchmark_calmar_ratio",
                "equal_weight_benchmark_total_return_pct",
                "equal_weight_benchmark_cagr_pct",
                "equal_weight_benchmark_max_drawdown_pct",
                "equal_weight_benchmark_sharpe_ratio",
                "equal_weight_benchmark_calmar_ratio",
                "relative_cagr_vs_spy_pct",
                "relative_max_drawdown_vs_spy_pct",
                "relative_calmar_vs_spy",
                "relative_cagr_vs_qqq_pct",
                "relative_max_drawdown_vs_qqq_pct",
                "relative_calmar_vs_qqq",
                "relative_cagr_vs_equal_weight_pct",
                "relative_max_drawdown_vs_equal_weight_pct",
                "relative_calmar_vs_equal_weight",
                "top_n",
                "universe_size",
                "research_only",
                "preview_only",
                "execution_approved",
            ]
        )
        for result in results:
            spy = result["spy"]
            qqq = result["qqq"]
            equal_weight = result["equal_weight"]
            writer.writerow(
                [
                    result["source_file"],
                    result["strategy_name"],
                    result["ticker_or_portfolio"],
                    result["period"],
                    round(result["starting_equity"], 2),
                    round(result["final_equity"], 2),
                    round(result["total_return_pct"], 4),
                    round(result["cagr_pct"], 4),
                    round(result["max_drawdown_pct"], 4),
                    round(result["annualised_volatility_pct"], 4),
                    round(result["sharpe_ratio"], 4),
                    round(result["calmar_ratio"], 4),
                    result["number_of_trades"],
                    result["turnover_proxy_trades"],
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    min_rebalance_notional,
                    round(spy["total_return_pct"], 4),
                    round(spy["cagr_pct"], 4),
                    round(spy["max_drawdown_pct"], 4),
                    round(spy["sharpe_ratio"], 4),
                    round(spy["calmar_ratio"], 4),
                    round(qqq["total_return_pct"], 4),
                    round(qqq["cagr_pct"], 4),
                    round(qqq["max_drawdown_pct"], 4),
                    round(qqq["sharpe_ratio"], 4),
                    round(qqq["calmar_ratio"], 4),
                    round(equal_weight["total_return_pct"], 4),
                    round(equal_weight["cagr_pct"], 4),
                    round(equal_weight["max_drawdown_pct"], 4),
                    round(equal_weight["sharpe_ratio"], 4),
                    round(equal_weight["calmar_ratio"], 4),
                    round(relative_metric(result["cagr_pct"], spy["cagr_pct"]), 4),
                    round(relative_metric(result["max_drawdown_pct"], spy["max_drawdown_pct"]), 4),
                    round(relative_metric(result["calmar_ratio"], spy["calmar_ratio"]), 4),
                    round(relative_metric(result["cagr_pct"], qqq["cagr_pct"]), 4),
                    round(relative_metric(result["max_drawdown_pct"], qqq["max_drawdown_pct"]), 4),
                    round(relative_metric(result["calmar_ratio"], qqq["calmar_ratio"]), 4),
                    round(relative_metric(result["cagr_pct"], equal_weight["cagr_pct"]), 4),
                    round(relative_metric(result["max_drawdown_pct"], equal_weight["max_drawdown_pct"]), 4),
                    round(relative_metric(result["calmar_ratio"], equal_weight["calmar_ratio"]), 4),
                    result["top_n"],
                    result["universe_size"],
                    result["research_only"],
                    result["preview_only"],
                    result["execution_approved"],
                ]
            )

    with (data_dir / "adaptive_momentum_trades.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "ticker",
                "side",
                "reason",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "quantity",
                "price",
                "notional",
            ]
        )
        for trade in trades:
            writer.writerow(
                [
                    trade["date"],
                    trade["ticker"],
                    trade["side"],
                    trade["reason"],
                    trade["commission_per_trade"],
                    trade["commission_bps"],
                    trade["spread_bps"],
                    trade["slippage_bps"],
                    trade["min_rebalance_notional"],
                    round(trade["quantity"], 6),
                    round(trade["price"], 4),
                    round(trade["quantity"] * trade["price"], 2),
                ]
            )

    with (data_dir / "adaptive_momentum_equity_curve.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "date",
                "commission_per_trade",
                "commission_bps",
                "spread_bps",
                "slippage_bps",
                "min_rebalance_notional",
                "equity",
            ]
        )
        for row in equity_curve:
            writer.writerow(
                [
                    row["date"],
                    cost_model.commission_per_trade,
                    cost_model.commission_bps,
                    cost_model.spread_bps,
                    cost_model.slippage_bps,
                    min_rebalance_notional,
                    round(row["equity"], 2),
                ]
            )


def backtest_ticker(
    config: AppConfig,
    ticker: str,
    ticker_data,
    regime_data,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    strategy = config.strategy
    actual_slippage_bps = config.backtest.slippage_bps if cost_model is None else float(cost_model.slippage_bps)
    slippage = actual_slippage_bps / 10000

    data = ticker_data.join(regime_data[["close"]].rename(columns={"close": "regime_close"}), how="inner")
    data["short_sma"] = data["close"].rolling(strategy.short_window).mean()
    data["long_sma"] = data["close"].rolling(strategy.long_window).mean()
    data["trend_sma"] = data["close"].rolling(strategy.trend_window).mean()
    data["regime_sma"] = data["regime_close"].rolling(strategy.trend_window).mean()
    data["realised_vol_20"] = data["close"].pct_change().rolling(strategy.vol_window).std() * math.sqrt(252)
    data["median_vol"] = data["realised_vol_20"].rolling(strategy.vol_median_window).median()
    data = data.dropna()

    if len(data) < 2:
        raise RuntimeError("Not enough aligned indicator data after calculating filters.")

    cash = config.backtest.position_size_dollars
    shares = 0.0
    entry_date = ""
    entry_price = 0.0
    entry_reason = ""
    position_days = 0
    daily_pnl: list[tuple[str, float]] = []
    equity_curve: list[float] = []
    trades: list[BacktestTrade] = []

    for index in range(1, len(data) - 1):
        today = data.iloc[index]
        yesterday = data.iloc[index - 1]
        next_day = data.iloc[index + 1]
        today_label = data.index[index].date().isoformat()
        next_label = data.index[index + 1].date().isoformat()

        if shares > 0:
            position_days += 1

        equity = cash + shares * float(today["close"])
        equity_curve.append(equity)
        daily_pnl.append((today_label, equity - config.backtest.position_size_dollars))

        # Market regime filter: only allow new longs when the broad market is above its 200-day trend.
        market_regime_ok = float(today["regime_close"]) > float(today["regime_sma"])

        # Ticker trend filter: avoid new longs when the ticker itself is below its 200-day trend.
        ticker_trend_ok = float(today["close"]) > float(today["trend_sma"])

        # Crossover trigger: require a true 20-day SMA cross above the 50-day SMA.
        signal = detect_sma_signal(
            float(yesterday["short_sma"]),
            float(yesterday["long_sma"]),
            float(today["short_sma"]),
            float(today["long_sma"]),
        )

        # Volatility gate: skip new entries when recent volatility is unusually high.
        volatility_ok = float(today["realised_vol_20"]) <= (
            strategy.vol_gate_multiple * float(today["median_vol"])
        )

        exit_signal = signal == SIGNAL_SELL
        exit_trend_break = float(today["close"]) < float(today["trend_sma"])

        # Signals use today's close, but trades execute at the next open. That delay is
        # what avoids look-ahead bias: the test never trades at a price from before the signal existed.
        if shares == 0 and market_regime_ok and ticker_trend_ok and signal == SIGNAL_BUY and volatility_ok:
            execution_price = (
                float(adjusted_buy_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 + slippage)
            )
            allocation = min(config.backtest.position_size_dollars, cash)
            if execution_price > 0 and allocation > 0:
                shares = allocation / execution_price
                cash -= allocation
                entry_date = next_label
                entry_price = execution_price
                entry_reason = "regime_ok,trending,crossover_up,vol_ok"
        elif shares > 0 and (exit_signal or exit_trend_break):
            execution_price = (
                float(adjusted_sell_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 - slippage)
            )
            proceeds = shares * execution_price
            pnl = proceeds - (shares * entry_price)
            trade_return_pct = ((execution_price - entry_price) / entry_price) * 100
            cash += proceeds
            trades.append(
                BacktestTrade(
                    ticker=ticker,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=next_label,
                    exit_price=execution_price,
                    quantity=shares,
                    entry_reason=entry_reason,
                    exit_reason="crossover_down" if exit_signal else "trend_break",
                    trade_return_pct=trade_return_pct,
                    pnl=pnl,
                )
            )
            shares = 0.0
            entry_date = ""
            entry_price = 0.0
            entry_reason = ""

    final_close = float(data.iloc[-1]["close"])
    final_equity = cash + shares * final_close
    equity_curve.append(final_equity)
    daily_pnl.append((data.index[-1].date().isoformat(), final_equity - config.backtest.position_size_dollars))

    closed_returns = [trade.trade_return_pct for trade in trades]
    wins = [value for value in closed_returns if value > 0]
    total_return_pct = ((final_equity - config.backtest.position_size_dollars) / config.backtest.position_size_dollars) * 100
    buy_and_hold_return_pct = ((final_close - float(data.iloc[0]["close"])) / float(data.iloc[0]["close"])) * 100
    win_rate_pct = (len(wins) / len(closed_returns) * 100) if closed_returns else 0.0
    average_trade_return_pct = sum(closed_returns) / len(closed_returns) if closed_returns else 0.0
    max_drawdown_pct = calculate_max_drawdown(equity_curve) * 100
    time_in_market_pct = (position_days / max(len(data), 1)) * 100

    result = BacktestResult(
        ticker=ticker,
        period="full_period",
        total_return_pct=total_return_pct,
        buy_and_hold_return_pct=buy_and_hold_return_pct,
        number_of_trades=len(trades),
        win_rate_pct=win_rate_pct,
        average_trade_return_pct=average_trade_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        final_equity=final_equity,
        time_in_market_pct=time_in_market_pct,
        pnl=final_equity - config.backtest.position_size_dollars,
        daily_pnl=daily_pnl,
    )
    result.slippage_bps = actual_slippage_bps
    return result, trades


def run_strategy_comparison(
    config: AppConfig,
    logger: logging.Logger,
    force_research_universe: bool = False,
) -> int:
    configure_yfinance_cache(config, logger)
    strategy_names = [
        "buy_and_hold_baseline",
        "sma_20_50_basic",
        "sma_20_50_regime",
        "sma_50_200_trend",
        "buy_above_200_exit_below_200",
        "fifty_two_week_high_breakout",
    ]
    results: list[BacktestResult] = []
    trades: list[BacktestTrade] = []
    portfolio_results: list[StrategyPortfolioResult] = []
    errors: list[str] = []
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))

    comparison_tickers = get_strategy_comparison_tickers(config, force_research_universe)

    print("Strategy comparison backtest")
    print(f"Tickers: {len(comparison_tickers)}")

    try:
        regime_data = download_backtest_prices(config, config.strategy.regime_ticker)
    except Exception as exc:
        logger.error("Strategy comparison failed: could not download regime ticker %s: %s", config.strategy.regime_ticker, exc)
        write_strategy_comparison_results(results, cost_model)
        write_strategy_comparison_trades(trades, cost_model)
        write_strategy_portfolio_comparison(portfolio_results, cost_model)
        write_strategy_robustness_summary([], cost_model)
        write_strategy_ticker_equity_curves(results, config)
        write_strategy_portfolio_equity_curves(config, results)
        print(f"Regime ticker error: {config.strategy.regime_ticker} - {exc}")
        return 1

    for ticker in comparison_tickers:
        try:
            ticker_data = download_backtest_prices(config, ticker)
        except Exception as exc:
            errors.append(ticker)
            logger.error("Strategy comparison failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            continue

        try:
            comparison_data = prepare_strategy_comparison_data(ticker_data, regime_data)
        except Exception as exc:
            errors.append(ticker)
            logger.error("Strategy comparison setup failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            continue

        for strategy_name in strategy_names:
            try:
                full_result, strategy_trades = compare_strategy_ticker(
                    config,
                    ticker,
                    comparison_data,
                    strategy_name,
                    cost_model,
                )
                results.extend(
                    build_period_comparison_results(
                        config,
                        full_result,
                        comparison_data,
                        strategy_trades,
                    )
                )
                trades.extend(strategy_trades)
            except Exception as exc:
                errors.append(f"{ticker}:{strategy_name}")
                logger.error("Strategy comparison failed for %s %s: %s", ticker, strategy_name, exc)
                print(f"{ticker},{strategy_name},ERROR,{exc}")

    write_strategy_comparison_results(results, cost_model)
    write_strategy_comparison_trades(trades, cost_model)
    portfolio_results = build_strategy_portfolio_results(config, results)
    robustness_results = build_strategy_robustness_summary(results)
    write_strategy_portfolio_comparison(portfolio_results, cost_model)
    write_strategy_robustness_summary(robustness_results, cost_model)
    write_strategy_ticker_equity_curves(results, config)
    write_strategy_portfolio_equity_curves(config, results)
    print_ranked_strategy_summary(results)
    print_ranked_portfolio_summary(portfolio_results)
    print_ranked_robustness_summary(robustness_results)
    print("")
    print("Saved results to data/strategy_comparison_results.csv")
    print("Saved trades to data/strategy_comparison_trades.csv")
    print("Saved portfolio comparison to data/strategy_portfolio_comparison.csv")
    print("Saved robustness summary to data/strategy_robustness_summary.csv")
    print("Saved portfolio equity curves to data/strategy_portfolio_equity_curves.csv")
    print("Saved ticker equity curves to data/strategy_ticker_equity_curves.csv")
    print(f"Tickers with errors: {len(errors)}")
    return 0 if results else 1


def get_strategy_comparison_tickers(
    config: AppConfig,
    force_research_universe: bool,
) -> list[str]:
    # Testing only AAPL/MSFT/SPY is too narrow: a strategy can look good on a
    # handful of familiar names and still fail across sectors, styles, and ETFs.
    # This research universe is for backtesting only and must never change the
    # live/paper trading ticker list used by normal bot runs.
    if force_research_universe or config.research_universe.enabled:
        return config.research_universe.tickers or default_research_universe_tickers()
    return config.tickers


def run_promoted_strategy_preview(config: AppConfig, logger: logging.Logger) -> int:
    print("WARNING: This command is preview-only and does not approve execution.")
    configure_yfinance_cache(config, logger)
    promotion_path = Path("data") / "strategy_promotion_report.csv"
    if not promotion_path.exists():
        print(f"Missing strategy promotion report: {promotion_path}", file=sys.stderr)
        return 1

    candidates = read_preview_candidates(promotion_path)
    if not candidates:
        print("No preview_candidate portfolio rows found.")
        write_promoted_preview(Path("data") / "promoted_strategy_preview.csv", [])
        return 0

    tickers = get_strategy_comparison_tickers(config, force_research_universe=False)
    data_by_ticker = {}
    failed_tickers: dict[str, str] = {}
    regime_ticker = config.strategy.regime_ticker
    for ticker in tickers:
        try:
            data_by_ticker[ticker] = download_backtest_prices(config, ticker)
        except Exception as exc:
            logger.warning("Promoted strategy preview failed to download %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            failed_tickers[ticker] = str(exc)

    regime_price_data = data_by_ticker.get(regime_ticker)
    if regime_price_data is None:
        try:
            regime_price_data = download_backtest_prices(config, regime_ticker)
        except Exception as exc:
            logger.warning("Promoted strategy preview failed to download regime ticker %s: %s", regime_ticker, exc)

    rows, warnings = build_promoted_preview_rows(
        candidates,
        data_by_ticker,
        regime_ticker=regime_ticker,
        regime_price_data=regime_price_data,
    )
    error_created_at = datetime.now(timezone.utc).isoformat()
    for ticker, error in failed_tickers.items():
        for candidate in candidates:
            rows.append(
                unsupported_preview_row(
                    error_created_at,
                    candidate,
                    ticker,
                    reason=f"market_data_unavailable: {error}",
                    regime_ticker=regime_ticker,
                )
            )
    if not data_by_ticker:
        warnings.append("No market data available for promoted strategy preview.")

    output_path = Path("data") / "promoted_strategy_preview.csv"
    write_promoted_preview(output_path, rows)
    for warning in warnings:
        print(f"Warning: {warning}")
    for line in build_promoted_preview_summary(rows, warnings):
        print(line)
    print(f"Saved promoted strategy preview to {output_path}")
    return 0


def load_promoted_action_preview_positions(
    config: AppConfig,
    logger: logging.Logger,
    use_paper_positions_readonly: bool = False,
) -> tuple[dict[str, Position], str]:
    if config.dry_run and not use_paper_positions_readonly:
        return {}, "dry_run_position_unavailable"
    if not config.alpaca_api_key or not config.alpaca_secret_key:
        if use_paper_positions_readonly:
            logger.warning("Read-only paper position lookup requested, but Alpaca paper API keys are missing.")
        return {}, "alpaca_keys_missing"
    try:
        client = TradingClient(
            api_key=config.alpaca_api_key,
            secret_key=config.alpaca_secret_key,
            paper=True,
        )
        position_source = "alpaca_paper_readonly" if use_paper_positions_readonly else "alpaca_paper"
        return get_alpaca_positions(client), position_source
    except Exception as exc:
        logger.warning("Could not read Alpaca paper positions for promoted action preview: %s", exc)
        return {}, "alpaca_position_error"


def run_promoted_action_preview(
    config: AppConfig,
    logger: logging.Logger,
    use_paper_positions_readonly: bool = False,
) -> int:
    print("WARNING: This command is preview-only and does not approve execution.")
    if use_paper_positions_readonly:
        print("Read-only Alpaca paper position lookup requested. This does not approve execution.")
    preview_path = Path("data") / "promoted_strategy_preview.csv"
    if not preview_path.exists():
        print(f"Missing promoted strategy preview file: {preview_path}", file=sys.stderr)
        return 1

    preview_rows = read_promoted_strategy_preview(preview_path)
    positions, position_source = load_promoted_action_preview_positions(
        config,
        logger,
        use_paper_positions_readonly=use_paper_positions_readonly,
    )
    rows = build_promoted_action_preview_rows(
        preview_rows,
        positions,
        position_source,
        Decimal(str(config.order_quantity)),
    )
    output_path = Path("data") / "promoted_strategy_action_preview.csv"
    write_promoted_action_preview(output_path, rows)
    for line in build_promoted_action_summary(rows, position_source):
        print(line)
    print(f"Saved promoted strategy action preview to {output_path}")
    return 0


def run_promoted_risk_preview() -> int:
    status_code, lines = run_promoted_risk_preview_files(
        Path("data") / "promoted_strategy_preview.csv",
        Path("data") / "promoted_strategy_action_preview.csv",
        Path("data") / "promoted_risk_preview.csv",
    )
    for line in lines:
        print(line)
    return status_code


def run_promoted_consensus_preview() -> int:
    status_code, lines = run_promoted_consensus_preview_files(
        Path("data") / "promoted_strategy_preview.csv",
        Path("data") / "promoted_consensus_preview.csv",
    )
    for line in lines:
        print(line)
    return status_code


def run_promoted_decision_preview() -> int:
    status_code, lines = run_promoted_decision_preview_files(
        Path("data") / "promoted_consensus_preview.csv",
        Path("data") / "promoted_strategy_action_preview.csv",
        Path("data") / "promoted_risk_preview.csv",
        Path("data") / "promoted_decision_preview.csv",
    )
    for line in lines:
        print(line)
    return status_code


def run_sma_sensitivity(
    config: AppConfig,
    logger: logging.Logger,
    force_research_universe: bool = False,
) -> int:
    configure_yfinance_cache(config, logger)
    results: list[BacktestResult] = []
    errors: list[str] = []
    tickers = get_strategy_comparison_tickers(config, force_research_universe)

    # Parameter sensitivity matters because one SMA pair can win one historical
    # test by chance. We want nearby parameter choices to behave reasonably too.
    # Avoid choosing a single pair purely because it won one backtest; that can
    # be a sign of overfitting instead of a durable trading idea.
    print("SMA parameter sensitivity backtest")
    print(f"Tickers: {len(tickers)}")
    print("Pairs: " + ", ".join(f"{short}/{long}" for short, long in SMA_SENSITIVITY_PAIRS))

    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))

    for ticker in tickers:
        try:
            ticker_data = download_backtest_prices(config, ticker)
            sensitivity_data = prepare_sma_sensitivity_data(ticker_data)
        except Exception as exc:
            errors.append(ticker)
            logger.error("SMA sensitivity setup failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            continue

        for short_window, long_window in SMA_SENSITIVITY_PAIRS:
            try:
                full_result, trades = compare_sma_pair_ticker(
                    config,
                    ticker,
                    sensitivity_data,
                    short_window,
                    long_window,
                    cost_model=cost_model,
                )
                results.extend(
                    build_period_comparison_results(
                        config,
                        full_result,
                        sensitivity_data,
                        trades,
                    )
                )
            except Exception as exc:
                errors.append(f"{ticker}:{short_window}/{long_window}")
                logger.error(
                    "SMA sensitivity failed for %s %s/%s: %s",
                    ticker,
                    short_window,
                    long_window,
                    exc,
                )
                print(f"{ticker},{short_window}/{long_window},ERROR,{exc}")

    portfolio_results = build_strategy_portfolio_results(config, results)
    write_sma_sensitivity_results(results, cost_model)
    write_sma_sensitivity_portfolio(portfolio_results, cost_model)
    print_ranked_sma_sensitivity_summary(portfolio_results)
    print("")
    print("Saved SMA sensitivity results to data/sma_sensitivity_results.csv")
    print("Saved SMA sensitivity portfolio results to data/sma_sensitivity_portfolio.csv")
    print(f"Tickers with errors: {len(errors)}")
    return 0 if results else 1


def run_trend_stress_test(
    config: AppConfig,
    logger: logging.Logger,
    force_research_universe: bool = False,
    force_etf_universe: bool = False,
) -> int:
    configure_yfinance_cache(config, logger)
    universe_name, tickers = get_trend_stress_test_universe(
        config,
        force_research_universe,
        force_etf_universe,
    )
    results: list[BacktestResult] = []
    errors: list[str] = []

    print("Slow SMA trend stress test")
    print(f"Universe: {universe_name}")
    print(f"Tickers: {len(tickers)}")
    print("Pairs: " + ", ".join(f"{short}/{long}" for short, long in TREND_STRESS_TEST_PAIRS))
    print("Slippage bps: " + ", ".join(str(value) for value in TREND_STRESS_TEST_SLIPPAGE_BPS))

    for ticker in tickers:
        try:
            ticker_data = download_backtest_prices(config, ticker)
            stress_data = prepare_trend_stress_test_data(ticker_data)
        except Exception as exc:
            errors.append(ticker)
            logger.error("Trend stress test setup failed for %s: %s", ticker, exc)
            print(f"{ticker},ERROR,{exc}")
            continue

        # Prefer parameter clusters over one winning setting. If several nearby
        # slow SMA pairs behave well, the idea is more convincing than a single
        # best backtest row.
        for short_window, long_window in TREND_STRESS_TEST_PAIRS:
            # Slippage sensitivity matters because real fills are never perfect;
            # a strategy that only works at zero cost may be too fragile.
            for slippage_bps in TREND_STRESS_TEST_SLIPPAGE_BPS:
                try:
                    cost_model = CostModel(slippage_bps=Decimal(str(slippage_bps)))
                    strategy_name = trend_stress_strategy_name(
                        short_window,
                        long_window,
                        slippage_bps,
                    )
                    full_result, trades = compare_sma_pair_ticker(
                        config,
                        ticker,
                        stress_data,
                        short_window,
                        long_window,
                        slippage_bps=slippage_bps,
                        strategy_name=strategy_name,
                        cost_model=cost_model,
                    )
                    results.extend(
                        build_period_comparison_results(
                            config,
                            full_result,
                            stress_data,
                            trades,
                        )
                    )
                except Exception as exc:
                    errors.append(f"{ticker}:{short_window}/{long_window}:{slippage_bps}")
                    logger.error(
                        "Trend stress test failed for %s %s/%s %s bps: %s",
                        ticker,
                        short_window,
                        long_window,
                        slippage_bps,
                        exc,
                    )
                    print(f"{ticker},{short_window}/{long_window},{slippage_bps},ERROR,{exc}")

    portfolio_results = build_strategy_portfolio_results(config, results)
    write_trend_stress_test_results(results, universe_name)
    write_trend_stress_test_portfolio(portfolio_results, universe_name)
    print_ranked_trend_stress_test_summary(portfolio_results)
    print("")
    print("Saved trend stress test results to data/trend_stress_test_results.csv")
    print("Saved trend stress test portfolio results to data/trend_stress_test_portfolio.csv")
    print(f"Tickers with errors: {len(errors)}")
    return 0 if results else 1


def run_slow_sma_signal_preview(
    config: AppConfig,
    logger: logging.Logger,
    force_research_universe: bool = False,
    force_etf_universe: bool = False,
) -> int:
    configure_yfinance_cache(config, logger)
    universe_name, tickers, short_window, long_window = get_slow_sma_preview_settings(
        config,
        force_research_universe,
        force_etf_universe,
    )
    rows: list[SlowSmaPreviewRow] = []
    errors: list[str] = []

    print("Slow SMA signal preview")
    print(f"Universe: {universe_name}")
    print(f"Windows: {short_window}/{long_window}")
    print("")
    print(format_slow_sma_preview_table_header())

    for ticker in tickers:
        try:
            close_prices = download_slow_sma_preview_prices(
                ticker,
                config.backtest.history_period,
                short_window,
                long_window,
            )
            row = calculate_slow_sma_preview_row(
                ticker,
                close_prices,
                short_window,
                long_window,
            )
            rows.append(row)
            print(format_slow_sma_preview_table_row(row))
        except Exception as exc:
            errors.append(ticker)
            logger.warning("Slow SMA preview failed for %s: %s", ticker, exc)
            print(format_slow_sma_preview_error_row(ticker, str(exc)))

    write_slow_sma_signal_preview(rows)
    print("")
    print("Saved slow SMA signal preview to data/slow_sma_signal_preview.csv")
    print(f"Tickers with errors: {len(errors)}")
    return 0 if rows else 1


def get_slow_sma_preview_settings(
    config: AppConfig,
    force_research_universe: bool,
    force_etf_universe: bool,
) -> tuple[str, list[str], int, int]:
    if force_research_universe and force_etf_universe:
        raise ConfigError("Choose either --research-universe or --etf-universe, not both.")

    if force_etf_universe:
        return (
            "etf_research_universe",
            config.etf_research_universe.tickers or [],
            config.slow_sma_strategy.etf_short_window,
            config.slow_sma_strategy.etf_long_window,
        )

    if force_research_universe:
        return (
            "research_universe",
            config.research_universe.tickers or [],
            config.slow_sma_strategy.short_window,
            config.slow_sma_strategy.long_window,
        )

    return (
        "config_tickers",
        config.tickers,
        config.slow_sma_strategy.short_window,
        config.slow_sma_strategy.long_window,
    )


def write_slow_sma_signal_preview(rows: list[SlowSmaPreviewRow]) -> None:
    output_path = Path("data/slow_sma_signal_preview.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "date",
                "close",
                "short_sma",
                "long_sma",
                "previous_short_sma",
                "previous_long_sma",
                "signal",
                "reason",
                "trend_state",
                "desired_position",
                "distance_from_short_sma_pct",
                "distance_from_long_sma_pct",
                "days_since_last_crossover",
                "last_crossover_type",
                "last_crossover_date",
                "close_above_short_sma",
                "close_above_long_sma",
                "used_short_window",
                "used_long_window",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.ticker,
                    row.date,
                    round(row.close, 4),
                    round(row.short_sma, 4),
                    round(row.long_sma, 4),
                    round(row.previous_short_sma, 4),
                    round(row.previous_long_sma, 4),
                    row.signal,
                    row.reason,
                    row.trend_state,
                    row.desired_position,
                    round(row.distance_from_short_sma_pct, 4),
                    round(row.distance_from_long_sma_pct, 4),
                    "" if row.days_since_last_crossover is None else row.days_since_last_crossover,
                    row.last_crossover_type,
                    row.last_crossover_date,
                    "true" if row.close_above_short_sma else "false",
                    "true" if row.close_above_long_sma else "false",
                    row.used_short_window,
                    row.used_long_window,
                ]
            )


def run_slow_sma_action_preview(
    config: AppConfig,
    logger: logging.Logger,
    force_research_universe: bool = False,
    force_etf_universe: bool = False,
) -> int:
    configure_yfinance_cache(config, logger)
    universe_name, tickers, short_window, long_window = get_slow_sma_preview_settings(
        config,
        force_research_universe,
        force_etf_universe,
    )
    alpaca_client, positions, position_source = load_action_preview_positions(config, logger)
    rows: list[SlowSmaActionPreviewRow] = []
    errors: list[str] = []

    print("Slow SMA target-position action preview")
    print(f"Universe: {universe_name}")
    print(f"Windows: {short_window}/{long_window}")
    print(f"Position source: {position_source}")
    print("")
    print(format_slow_sma_action_preview_table_header())

    for ticker in tickers:
        try:
            close_prices = download_slow_sma_preview_prices(
                ticker,
                config.backtest.history_period,
                short_window,
                long_window,
            )
            signal_row = calculate_slow_sma_preview_row(
                ticker,
                close_prices,
                short_window,
                long_window,
            )
            open_orders, open_order_error = get_action_preview_open_orders(
                alpaca_client,
                logger,
                ticker,
            )
            action_row = build_slow_sma_action_preview_row(
                signal_row,
                positions.get(ticker, Position()),
                open_orders,
                open_order_error,
                position_source,
            )
            rows.append(action_row)
            print(format_slow_sma_action_preview_table_row(action_row))
        except Exception as exc:
            errors.append(ticker)
            logger.warning("Slow SMA action preview failed for %s: %s", ticker, exc)
            print(format_slow_sma_action_preview_error_row(ticker, str(exc)))

    write_slow_sma_action_preview(rows)
    print("")
    print("Saved slow SMA action preview to data/slow_sma_action_preview.csv")
    print(f"Tickers with errors: {len(errors)}")
    return 0 if rows else 1


def load_action_preview_positions(
    config: AppConfig,
    logger: logging.Logger,
) -> tuple[TradingClient | None, dict[str, Position], str]:
    if not config.alpaca_api_key or not config.alpaca_secret_key:
        return None, {}, "simulated_flat"

    try:
        client = TradingClient(
            config.alpaca_api_key,
            config.alpaca_secret_key,
            paper=True,
        )
        return client, get_alpaca_positions(client), "alpaca_paper"
    except Exception as exc:
        logger.warning("Could not read Alpaca paper positions for preview: %s", exc)
        return None, {}, "alpaca_error_flat"


def get_action_preview_open_orders(
    client: TradingClient | None,
    logger: logging.Logger,
    ticker: str,
) -> tuple[list[Any], str]:
    if client is None:
        return [], ""

    try:
        return get_open_orders_for_ticker(client, ticker), ""
    except Exception as exc:
        logger.warning("Could not read Alpaca open orders for %s preview: %s", ticker, exc)
        return [], f"open_order_check_failed: {exc}"


def build_slow_sma_action_preview_row(
    signal_row: SlowSmaPreviewRow,
    current_position: Position,
    open_orders: list[Any],
    open_order_error: str,
    position_source: str,
) -> SlowSmaActionPreviewRow:
    open_order_exists, open_order_side, open_order_qty = summarize_preview_open_orders(open_orders)
    proposed_action, reason = decide_slow_sma_preview_action(
        signal_row.desired_position,
        current_position,
        open_order_exists,
        open_order_error,
    )

    return SlowSmaActionPreviewRow(
        ticker=signal_row.ticker,
        date=signal_row.date,
        trend_state=signal_row.trend_state,
        signal=signal_row.signal,
        desired_position=signal_row.desired_position,
        current_position=current_position.state,
        current_qty=current_position.quantity,
        proposed_action=proposed_action,
        open_order_exists=open_order_exists,
        open_order_side=open_order_side,
        open_order_qty=open_order_qty,
        close=signal_row.close,
        short_sma=signal_row.short_sma,
        long_sma=signal_row.long_sma,
        days_since_last_crossover=signal_row.days_since_last_crossover,
        reason=reason,
        position_source=position_source,
    )


def decide_slow_sma_preview_action(
    desired_position: str,
    current_position: Position,
    open_order_exists: bool,
    open_order_error: str,
) -> tuple[str, str]:
    # Signal-only execution would trade only on a fresh BUY or SELL crossover.
    # Target-position alignment is different: it asks whether the account is
    # currently aligned with the strategy's desired state, even if today's
    # signal is HOLD. This preview reports that alignment gap only; it does not
    # place, cancel, or queue orders.
    if open_order_error:
        return "review_manually", open_order_error

    if open_order_exists:
        return "blocked_open_order", "Existing open Alpaca order must be reviewed first."

    if current_position.state == POSITION_SHORT:
        return "review_manually", "Current position is short, but the slow SMA strategy is long-only."

    if desired_position == "long" and current_position.state == POSITION_FLAT:
        return "open_long", "Desired position is long and current position is flat."

    if desired_position == "long" and current_position.state == POSITION_LONG:
        return "hold_long", "Desired position is long and current position is already long."

    if desired_position == "flat" and current_position.state == POSITION_LONG:
        return "close_long", "Desired position is flat and current position is long."

    if desired_position == "flat" and current_position.state == POSITION_FLAT:
        return "stay_flat", "Desired position is flat and current position is flat."

    return "review_manually", "Position state could not be matched to a preview action."


def summarize_preview_open_orders(open_orders: list[Any]) -> tuple[bool, str, Decimal]:
    if not open_orders:
        return False, "", Decimal("0")

    sides: list[str] = []
    total_quantity = Decimal("0")
    for order in open_orders:
        side = normalize_order_side(getattr(order, "side", ""))
        if side and side not in sides:
            sides.append(side)

        quantity = decimal_from_any(getattr(order, "qty", "0"))
        filled_quantity = decimal_from_any(getattr(order, "filled_qty", "0"))
        remaining_quantity = quantity - filled_quantity
        if remaining_quantity > 0:
            total_quantity += remaining_quantity

    return True, ",".join(sides), total_quantity


def write_slow_sma_action_preview(rows: list[SlowSmaActionPreviewRow]) -> None:
    output_path = Path("data/slow_sma_action_preview.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ticker",
                "date",
                "trend_state",
                "signal",
                "desired_position",
                "current_position",
                "current_qty",
                "proposed_action",
                "open_order_exists",
                "open_order_side",
                "open_order_qty",
                "close",
                "short_sma",
                "long_sma",
                "days_since_last_crossover",
                "reason",
                "position_source",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.ticker,
                    row.date,
                    row.trend_state,
                    row.signal,
                    row.desired_position,
                    row.current_position,
                    decimal_to_float(row.current_qty),
                    row.proposed_action,
                    "true" if row.open_order_exists else "false",
                    row.open_order_side,
                    decimal_to_float(row.open_order_qty),
                    round(row.close, 4),
                    round(row.short_sma, 4),
                    round(row.long_sma, 4),
                    "" if row.days_since_last_crossover is None else row.days_since_last_crossover,
                    row.reason,
                    row.position_source,
                ]
            )


def run_slow_sma_paper_execution(
    config: AppConfig,
    logger: logging.Logger,
    confirm_slow_sma_paper: bool,
    force_research_universe: bool = False,
    force_etf_universe: bool = False,
) -> int:
    if not confirm_slow_sma_paper:
        print(
            "Refusing to run slow SMA paper execution. "
            "Re-run with --confirm-slow-sma-paper to submit Alpaca paper orders."
        )
        return 2

    validate_slow_sma_execution_preflight_safety(config)
    kill_switch_decision = evaluate_paper_kill_switch_gate(
        alpaca_paper=config.alpaca_paper,
        dry_run=config.dry_run,
        explicit_paper_execution_requested=confirm_slow_sma_paper,
        allow_shorting=config.allow_shorting,
        paper_kill_switch_enabled=getattr(config, "paper_kill_switch_enabled", None),
        execution_eligibility_blocked=manual_paper_order_execution_eligibility_blocked(),
        defensive_decision_blocked=manual_paper_order_defensive_decision_blocked(),
        explicit_confirmation=confirm_slow_sma_paper,
        command_name="execute_slow_sma_paper",
    )
    if not kill_switch_decision.allowed:
        print("SLOW SMA PAPER EXECUTION BLOCKED BY PAPER KILL-SWITCH PREFLIGHT.")
        print("No orders were created, submitted, or cancelled.")
        print("No SQLite execution trade_log rows were written.")
        print("No Discord alerts were sent.")
        print("Reasons:")
        for reason in kill_switch_decision.reasons:
            print(f"- {reason}")
        print(kill_switch_decision.required_next_step)
        print("No execution approval was granted.")
        logger.warning(
            "Slow SMA paper execution blocked by paper kill-switch preflight: %s",
            "; ".join(kill_switch_decision.reasons),
        )
        return 2

    validate_slow_sma_execution_safety(config)
    configure_yfinance_cache(config, logger)
    universe_name, tickers, short_window, long_window = get_slow_sma_preview_settings(
        config,
        force_research_universe,
        force_etf_universe,
    )

    execution_config = replace(config, dry_run=False)
    conn = init_database(config.database_path)
    stats = SlowSmaExecutionStats()

    print("Slow SMA target-position paper execution")
    print("Mode: Alpaca paper trading only")
    print(f"Universe: {universe_name}")
    print(f"Windows: {short_window}/{long_window}")
    print(f"Target long quantity: {config.order_quantity}")
    print(f"Tickers: {len(tickers)}")
    print("This separate command is required because normal bot.py keeps running the original strategy.")
    print("")

    send_discord_alert(
        config,
        logger,
        (
            "Slow SMA paper execution started: "
            f"universe={universe_name}, tickers={len(tickers)}, target_qty={config.order_quantity}"
        ),
    )

    try:
        # Alpaca is created only after confirmation and all paper-only safety
        # checks pass. This command is intentionally separate from normal
        # bot.py so target-position alignment cannot run accidentally.
        alpaca_client = TradingClient(
            config.alpaca_api_key,
            config.alpaca_secret_key,
            paper=True,
        )
        positions = get_alpaca_positions(alpaca_client)

        print(format_slow_sma_execution_table_header())
        for ticker in tickers:
            stats.tickers_processed += 1
            try:
                process_slow_sma_execution_ticker(
                    config=config,
                    execution_config=execution_config,
                    conn=conn,
                    logger=logger,
                    alpaca_client=alpaca_client,
                    positions=positions,
                    ticker=ticker,
                    short_window=short_window,
                    long_window=long_window,
                    stats=stats,
                )
            except Exception as exc:
                stats.failed_tickers += 1
                message = f"Slow SMA paper execution failed for {ticker}: {exc}"
                logger.error(message)
                print(format_slow_sma_execution_error_row(ticker, str(exc)))
                insert_trade_log(
                    conn=conn,
                    config=execution_config,
                    ticker=ticker,
                    signal="SLOW_SMA_TARGET",
                    action="review_manually",
                    error=message,
                )
                send_discord_alert(config, logger, f"Error: {message}")

        summary = (
            "Slow SMA paper execution completed. "
            f"Processed: {stats.tickers_processed}, "
            f"submitted orders: {stats.submitted_orders}, "
            f"skipped actions: {stats.skipped_actions}, "
            f"no order needed: {stats.no_order_needed}, "
            f"failed tickers: {stats.failed_tickers}."
        )
        print("")
        print(summary)
        send_discord_alert(config, logger, summary)
        return 0 if stats.tickers_processed and stats.failed_tickers < stats.tickers_processed else 1
    finally:
        conn.close()


def validate_slow_sma_execution_safety(config: AppConfig) -> None:
    validate_slow_sma_execution_preflight_safety(config)

    if not config.alpaca_api_key or not config.alpaca_secret_key:
        raise ConfigError("Alpaca paper API key and secret key are required for slow SMA paper execution.")


def validate_slow_sma_execution_preflight_safety(config: AppConfig) -> None:
    if not config.alpaca_paper:
        raise ConfigError("alpaca.paper must be true for slow SMA paper execution.")

    if config.allow_shorting:
        raise ConfigError("allow_shorting must be false because the slow SMA strategy is long-only.")


def process_slow_sma_execution_ticker(
    config: AppConfig,
    execution_config: AppConfig,
    conn: sqlite3.Connection,
    logger: logging.Logger,
    alpaca_client: TradingClient,
    positions: dict[str, Position],
    ticker: str,
    short_window: int,
    long_window: int,
    stats: SlowSmaExecutionStats,
) -> None:
    close_prices = download_slow_sma_preview_prices(
        ticker,
        config.backtest.history_period,
        short_window,
        long_window,
    )
    signal_row = calculate_slow_sma_preview_row(
        ticker,
        close_prices,
        short_window,
        long_window,
    )
    position_before = positions.get(ticker, Position())
    open_orders = get_open_orders_for_ticker(alpaca_client, ticker)
    open_order_exists, _, _ = summarize_preview_open_orders(open_orders)

    side, action, quantity, position_after, message = decide_slow_sma_execution_action(
        signal_row.desired_position,
        position_before,
        decimal_from_any(config.order_quantity),
        open_order_exists,
    )
    order_id = ""
    order_status = ""
    error = ""

    if message:
        error = message

    if quantity > 0 and side:
        is_valid_asset, asset_error = validate_alpaca_asset_for_order(
            alpaca_client,
            ticker,
            requires_shortable=False,
        )
        if not is_valid_asset:
            action = "review_manually"
            side = ""
            quantity = Decimal("0")
            position_after = position_before
            error = asset_error

    if quantity > 0 and side:
        order = submit_alpaca_order(alpaca_client, ticker, side, quantity)
        order_id = str(getattr(order, "id", ""))
        order_status = normalize_order_status(getattr(order, "status", "submitted"))
        order_status = refresh_order_status(
            alpaca_client,
            logger,
            order_id,
            order_status,
            timeout_seconds=10,
        )
        position_after = estimate_slow_sma_execution_position_after(
            position_before,
            side,
            quantity,
            order_status,
        )
        if order_status == "filled":
            positions[ticker] = position_after
        stats.submitted_orders += 1
        send_discord_alert(
            config,
            logger,
            (
                f"Slow SMA paper order submitted: {ticker} {side.upper()} "
                f"{format_decimal(quantity)} share(s), action={action}, status={order_status}, order_id={order_id}"
            ),
        )
    elif action in {"hold_long", "stay_flat"}:
        stats.no_order_needed += 1
    else:
        stats.skipped_actions += 1
        if action in {"blocked_open_order", "review_manually"}:
            send_discord_alert(config, logger, f"Slow SMA paper action skipped for {ticker}: {error}")

    insert_trade_log(
        conn=conn,
        config=execution_config,
        ticker=ticker,
        signal="SLOW_SMA_TARGET",
        side=side,
        action=action,
        position_before=position_before,
        position_after=position_after,
        quantity=decimal_to_float(quantity) if quantity > 0 else 0,
        last_close=signal_row.close,
        short_ma=signal_row.short_sma,
        long_ma=signal_row.long_sma,
        order_id=order_id,
        order_status=order_status,
        error=error,
    )
    print(
        format_slow_sma_execution_table_row(
            ticker,
            signal_row.desired_position,
            position_before,
            side,
            action,
            quantity,
            order_status,
            error,
        )
    )


def decide_slow_sma_execution_action(
    desired_position: str,
    position_before: Position,
    target_quantity: Decimal,
    open_order_exists: bool,
) -> tuple[str, str, Decimal, Position, str]:
    if open_order_exists:
        return (
            "",
            "blocked_open_order",
            Decimal("0"),
            position_before,
            "Existing open Alpaca order blocks slow SMA paper execution for this ticker.",
        )

    if position_before.state == POSITION_SHORT:
        return (
            "",
            "review_manually",
            Decimal("0"),
            position_before,
            "Current position is short, but the slow SMA strategy is long-only.",
        )

    current_quantity = position_before.quantity
    target = target_quantity if desired_position == "long" else Decimal("0")
    order_delta = target - current_quantity

    if order_delta == 0:
        action = "hold_long" if desired_position == "long" else "stay_flat"
        return "", action, Decimal("0"), position_before, ""

    if order_delta > 0:
        side = "buy"
        quantity = order_delta
        action = "open_long" if current_quantity == 0 else "increase_long"
        return side, action, quantity, Position(position_before.quantity + quantity), ""

    quantity = abs(order_delta)
    side = "sell"
    action = "close_long" if target == 0 else "reduce_long"
    if quantity > position_before.abs_quantity:
        return (
            "",
            "review_manually",
            Decimal("0"),
            position_before,
            "Calculated sell quantity is larger than the current long position.",
        )
    return side, action, quantity, Position(position_before.quantity - quantity), ""


def estimate_slow_sma_execution_position_after(
    position_before: Position,
    side: str,
    quantity: Decimal,
    order_status: str,
) -> Position:
    if order_status != "filled":
        return position_before
    if side == "buy":
        return Position(position_before.quantity + quantity)
    return Position(position_before.quantity - quantity)


def get_trend_stress_test_universe(
    config: AppConfig,
    force_research_universe: bool,
    force_etf_universe: bool,
) -> tuple[str, list[str]]:
    if force_research_universe and force_etf_universe:
        raise ConfigError("Choose either --research-universe or --etf-universe, not both.")

    if force_etf_universe:
        # ETF-only testing can reduce survivorship bias because broad index and
        # sector ETFs represent markets and asset classes, not just today's
        # surviving popular stocks.
        return "etf_research_universe", config.etf_research_universe.tickers or []

    if force_research_universe:
        return "research_universe", config.research_universe.tickers or []

    return "config_tickers", config.tickers


def compare_sma_pair_ticker(
    config: AppConfig,
    ticker: str,
    data,
    short_window: int,
    long_window: int,
    slippage_bps: float | None = None,
    strategy_name: str | None = None,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    actual_slippage_bps = config.backtest.slippage_bps if slippage_bps is None else slippage_bps
    slippage = actual_slippage_bps / 10000
    short_column = f"sma{short_window}"
    long_column = f"sma{long_window}"

    if len(data) < 3:
        raise RuntimeError("Not enough SMA sensitivity data.")

    cash = config.backtest.position_size_dollars
    shares = 0.0
    entry_date = ""
    entry_price = 0.0
    entry_reason = ""
    position_days = 0
    dated_equity_curve: list[tuple[str, float]] = []
    dated_exposure: list[tuple[str, bool]] = []
    trades: list[BacktestTrade] = []
    strategy_name = strategy_name or sma_sensitivity_strategy_name(short_window, long_window)

    for index in range(1, len(data) - 1):
        today = data.iloc[index]
        yesterday = data.iloc[index - 1]
        next_day = data.iloc[index + 1]
        next_label = data.index[index + 1].date().isoformat()

        if shares > 0:
            position_days += 1

        today_date = data.index[index].date().isoformat()
        dated_equity_curve.append((today_date, cash + shares * float(today["close"])))
        dated_exposure.append((today_date, shares > 0))

        entry_signal = crossed_above(
            float(yesterday[short_column]),
            float(yesterday[long_column]),
            float(today[short_column]),
            float(today[long_column]),
        )
        exit_signal = crossed_below(
            float(yesterday[short_column]),
            float(yesterday[long_column]),
            float(today[short_column]),
            float(today[long_column]),
        )

        # Sensitivity testing uses the same long-only, next-day open execution
        # assumption as the strategy comparison command.
        if shares == 0 and entry_signal:
            execution_price = (
                float(adjusted_buy_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 + slippage)
            )
            if execution_price > 0 and cash > 0:
                shares = cash / execution_price
                cash = 0.0
                entry_date = next_label
                entry_price = execution_price
                entry_reason = f"sma{short_window}_cross_above_sma{long_window}"
        elif shares > 0 and exit_signal:
            execution_price = (
                float(adjusted_sell_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 - slippage)
            )
            proceeds = shares * execution_price
            pnl = proceeds - (shares * entry_price)
            trade_return_pct = ((execution_price - entry_price) / entry_price) * 100
            cash += proceeds
            trades.append(
                BacktestTrade(
                    ticker=ticker,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=next_label,
                    exit_price=execution_price,
                    quantity=shares,
                    entry_reason=entry_reason,
                    exit_reason=f"sma{short_window}_cross_below_sma{long_window}",
                    trade_return_pct=trade_return_pct,
                    pnl=pnl,
                    strategy_name=strategy_name,
                )
            )
            shares = 0.0
            entry_date = ""
            entry_price = 0.0
            entry_reason = ""

    final_close = float(data.iloc[-1]["close"])
    final_equity = cash + shares * final_close
    final_date = data.index[-1].date().isoformat()
    dated_equity_curve.append((final_date, final_equity))
    dated_exposure.append((final_date, shares > 0))

    result = build_comparison_result(
        config,
        ticker,
        strategy_name,
        data,
        trades,
        dated_equity_curve,
        dated_exposure,
        final_equity,
        position_days,
    )
    result.short_window = short_window
    result.long_window = long_window
    result.slippage_bps = actual_slippage_bps
    return result, trades


def compare_strategy_ticker(
    config: AppConfig,
    ticker: str,
    data,
    strategy_name: str,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    if strategy_name == "buy_and_hold_baseline":
        return compare_buy_and_hold_ticker(config, ticker, data, strategy_name, cost_model)
    if strategy_name == "fifty_two_week_high_breakout":
        return compare_breakout_ticker(config, ticker, data, strategy_name, cost_model)

    actual_slippage_bps = config.backtest.slippage_bps if cost_model is None else float(cost_model.slippage_bps)
    slippage = actual_slippage_bps / 10000

    if len(data) < 3:
        raise RuntimeError("Not enough indicator data for strategy comparison.")

    cash = config.backtest.position_size_dollars
    shares = 0.0
    entry_date = ""
    entry_price = 0.0
    entry_reason = ""
    position_days = 0
    dated_equity_curve: list[tuple[str, float]] = []
    dated_exposure: list[tuple[str, bool]] = []
    trades: list[BacktestTrade] = []

    for index in range(1, len(data) - 1):
        today = data.iloc[index]
        yesterday = data.iloc[index - 1]
        next_day = data.iloc[index + 1]
        next_label = data.index[index + 1].date().isoformat()

        if shares > 0:
            position_days += 1
        today_date = data.index[index].date().isoformat()
        dated_equity_curve.append((today_date, cash + shares * float(today["close"])))
        dated_exposure.append((today_date, shares > 0))

        entry_signal, entry_reason_candidate = comparison_entry_signal(strategy_name, yesterday, today)
        exit_signal, exit_reason = comparison_exit_signal(strategy_name, yesterday, today)

        # All comparison strategies use next-day open execution. The signal is known
        # after today's close, so trading tomorrow's open avoids look-ahead bias.
        if shares == 0 and entry_signal:
            execution_price = (
                float(adjusted_buy_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 + slippage)
            )
            if execution_price > 0 and cash > 0:
                shares = cash / execution_price
                cash = 0.0
                entry_date = next_label
                entry_price = execution_price
                entry_reason = entry_reason_candidate
        elif shares > 0 and exit_signal:
            execution_price = (
                float(adjusted_sell_fill_price(float(next_day["open"]), cost_model))
                if cost_model is not None
                else float(next_day["open"]) * (1 - slippage)
            )
            proceeds = shares * execution_price
            pnl = proceeds - (shares * entry_price)
            trade_return_pct = ((execution_price - entry_price) / entry_price) * 100
            cash += proceeds
            trades.append(
                BacktestTrade(
                    ticker=ticker,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=next_label,
                    exit_price=execution_price,
                    quantity=shares,
                    entry_reason=entry_reason,
                    exit_reason=exit_reason,
                    trade_return_pct=trade_return_pct,
                    pnl=pnl,
                    strategy_name=strategy_name,
                )
            )
            shares = 0.0
            entry_date = ""
            entry_price = 0.0
            entry_reason = ""

    final_close = float(data.iloc[-1]["close"])
    final_equity = cash + shares * final_close
    final_date = data.index[-1].date().isoformat()
    dated_equity_curve.append((final_date, final_equity))
    dated_exposure.append((final_date, shares > 0))

    result = build_comparison_result(
        config,
        ticker,
        strategy_name,
        data,
        trades,
        dated_equity_curve,
        dated_exposure,
        final_equity,
        position_days,
    )
    result.slippage_bps = actual_slippage_bps
    return result, trades


def compare_breakout_ticker(
    config: AppConfig,
    ticker: str,
    data,
    strategy_name: str,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    actual_slippage_bps = config.backtest.slippage_bps if cost_model is None else float(cost_model.slippage_bps)

    if len(data) < 253:
        raise RuntimeError("Not enough shared comparison data for 52-week breakout.")

    cash = config.backtest.position_size_dollars
    shares = 0.0
    entry_date = ""
    entry_price = 0.0
    entry_reason = ""
    highest_close_since_entry = 0.0
    position_days = 0
    dated_equity_curve: list[tuple[str, float]] = []
    dated_exposure: list[tuple[str, bool]] = []
    trades: list[BacktestTrade] = []

    ohlcv_rows = [
        {
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row.get("volume", 0.0)),
        }
        for _, row in data.iterrows()
    ]

    for index in range(1, len(data) - 1):
        today = data.iloc[index]
        next_day = data.iloc[index + 1]
        today_date = data.index[index].date().isoformat()
        next_label = data.index[index + 1].date().isoformat()
        history = ohlcv_rows[: index + 1]

        if shares > 0:
            position_days += 1
            highest_close_since_entry = max(highest_close_since_entry, float(today["close"]))

        dated_equity_curve.append((today_date, cash + shares * float(today["close"])))
        dated_exposure.append((today_date, shares > 0))

        entered_today = False
        if (
            shares == 0
            and len(history) >= 252
            and is_252_day_high_breakout(history)
            and volume_confirmation(history, multiplier=1.0)
        ):
            execution_price = adjusted_breakout_buy_fill(float(next_day["open"]), cost_model)
            if execution_price > 0 and cash > 0:
                shares = cash / execution_price
                cash = 0.0
                entry_date = next_label
                entry_price = execution_price
                entry_reason = "252_day_high_breakout,volume_confirmed"
                highest_close_since_entry = float(today["close"])
                entered_today = True

        # This candidate is long-only and does not pyramid. Once long, new
        # breakouts are ignored until an exit condition closes the position.
        if shares > 0 and not entered_today:
            exit_reason = ""
            if len(history) >= 100 and sma_100_exit(history):
                exit_reason = "close_below_100_sma"
            elif len(history) >= 20 and atr_trailing_stop_exit(history, highest_close_since_entry):
                exit_reason = "atr_trailing_stop"

            if exit_reason:
                execution_price = adjusted_breakout_sell_fill(float(next_day["open"]), cost_model)
                proceeds = shares * execution_price
                pnl = proceeds - (shares * entry_price)
                trade_return_pct = ((execution_price - entry_price) / entry_price) * 100
                cash += proceeds
                trades.append(
                    BacktestTrade(
                        ticker=ticker,
                        entry_date=entry_date,
                        entry_price=entry_price,
                        exit_date=next_label,
                        exit_price=execution_price,
                        quantity=shares,
                        entry_reason=entry_reason,
                        exit_reason=exit_reason,
                        trade_return_pct=trade_return_pct,
                        pnl=pnl,
                        strategy_name=strategy_name,
                    )
                )
                shares = 0.0
                entry_date = ""
                entry_price = 0.0
                entry_reason = ""
                highest_close_since_entry = 0.0

    final_close = float(data.iloc[-1]["close"])
    final_equity = cash + shares * final_close
    final_date = data.index[-1].date().isoformat()
    dated_equity_curve.append((final_date, final_equity))
    dated_exposure.append((final_date, shares > 0))

    result = build_comparison_result(
        config,
        ticker,
        strategy_name,
        data,
        trades,
        dated_equity_curve,
        dated_exposure,
        final_equity,
        position_days,
    )
    result.slippage_bps = actual_slippage_bps
    return result, trades


def compare_buy_and_hold_ticker(
    config: AppConfig,
    ticker: str,
    ticker_data,
    strategy_name: str,
    cost_model: CostModel | None = None,
) -> tuple[BacktestResult, list[BacktestTrade]]:
    data = ticker_data.dropna()
    if len(data) < 2:
        raise RuntimeError("Not enough data for buy-and-hold baseline.")

    actual_slippage_bps = config.backtest.slippage_bps if cost_model is None else float(cost_model.slippage_bps)
    slippage = actual_slippage_bps / 10000

    # Buy-and-hold is included as a benchmark. If an active strategy cannot beat
    # simply buying once and holding, the extra trading complexity may not be worth it.
    entry_row = data.iloc[0]
    exit_row = data.iloc[-1]
    entry_price = (
        float(adjusted_buy_fill_price(float(entry_row["open"]), cost_model))
        if cost_model is not None
        else float(entry_row["open"]) * (1 + slippage)
    )
    exit_price = (
        float(adjusted_sell_fill_price(float(exit_row["open"]), cost_model))
        if cost_model is not None
        else float(exit_row["open"]) * (1 - slippage)
    )
    shares = config.backtest.position_size_dollars / entry_price
    final_equity = shares * exit_price
    pnl = final_equity - config.backtest.position_size_dollars
    trade_return_pct = ((exit_price - entry_price) / entry_price) * 100

    trade = BacktestTrade(
        ticker=ticker,
        entry_date=data.index[0].date().isoformat(),
        entry_price=entry_price,
        exit_date=data.index[-1].date().isoformat(),
        exit_price=exit_price,
        quantity=shares,
        entry_reason="buy_first_valid_day",
        exit_reason="sell_final_valid_day",
        trade_return_pct=trade_return_pct,
        pnl=pnl,
        strategy_name=strategy_name,
    )

    dated_equity_curve = [
        (index.date().isoformat(), shares * float(row["close"]))
        for index, row in data.iterrows()
    ]
    dated_exposure = [
        (index.date().isoformat(), True)
        for index, _ in data.iterrows()
    ]
    result = build_comparison_result(
        config,
        ticker,
        strategy_name,
        data,
        [trade],
        dated_equity_curve,
        dated_exposure,
        final_equity,
        len(data),
    )
    result.slippage_bps = actual_slippage_bps
    return result, [trade]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market monitoring and Alpaca paper trading bot.")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json. Defaults to config.json in the current folder.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run mode, even if config.json has dry_run set to false.",
    )
    parser.add_argument(
        "--paper-order-test",
        nargs=3,
        metavar=("TICKER", "SIDE", "QTY"),
        help="Submit one manual Alpaca paper market DAY order, for example: --paper-order-test AAPL buy 1.",
    )
    parser.add_argument(
        "--confirm-paper-order",
        action="store_true",
        help="Required for --paper-order-test when config.json has dry_run set to true.",
    )
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run a simple long-only SMA backtest for the configured tickers.",
    )
    parser.add_argument(
        "--compare-strategies",
        action="store_true",
        help="Compare several long-only daily strategies for the configured tickers.",
    )
    parser.add_argument(
        "--sma-sensitivity",
        action="store_true",
        help="Test several long-only SMA trend parameter pairs.",
    )
    parser.add_argument(
        "--trend-stress-test",
        action="store_true",
        help="Stress test slow SMA trend pairs across several slippage assumptions.",
    )
    parser.add_argument(
        "--etf-rotation-backtest",
        action="store_true",
        help="Run a research-only monthly ETF momentum rotation backtest.",
    )
    parser.add_argument(
        "--etf-rotation-robustness",
        action="store_true",
        help="Create a saved-data-only fixed-split robustness report for ETF rotation.",
    )
    parser.add_argument(
        "--etf-breadth-regime-backtest",
        action="store_true",
        help="Run a research-only saved-data ETF breadth regime backtest without execution.",
    )
    parser.add_argument(
        "--etf-breadth-regime-decision-report",
        action="store_true",
        help="Create a saved-data-only decision report for ETF breadth regime research.",
    )
    parser.add_argument(
        "--etf-breadth-regime-robustness",
        action="store_true",
        help="Create a saved-data-only fixed-split robustness report for ETF breadth regime research.",
    )
    parser.add_argument(
        "--build-etf-breadth-price-history",
        action="store_true",
        help="Build saved ETF close-history input for the ETF breadth regime backtest.",
    )
    parser.add_argument(
        "--adaptive-momentum-backtest",
        action="store_true",
        help="Run a research-only adaptive risk-on/off momentum backtest.",
    )
    parser.add_argument(
        "--research-report",
        action="store_true",
        help="Create a consolidated research ranking report from saved CSV outputs.",
    )
    parser.add_argument(
        "--walk-forward-report",
        action="store_true",
        help="Create a walk-forward validation report from saved in/out-of-sample CSV outputs.",
    )
    parser.add_argument(
        "--strategy-promotion-report",
        action="store_true",
        help="Create a conservative strategy promotion checklist from saved research reports.",
    )
    parser.add_argument(
        "--defensive-strategy-report",
        action="store_true",
        help="Create a research-only defensive usefulness report from saved research reports.",
    )
    parser.add_argument(
        "--defensive-candidate-comparison",
        action="store_true",
        help="Compare ETF rotation and adaptive momentum as research-only defensive candidates.",
    )
    parser.add_argument(
        "--defensive-research-state-report",
        action="store_true",
        help="Create a saved-data-only defensive research state checkpoint report.",
    )
    parser.add_argument(
        "--defensive-allocation-preview",
        action="store_true",
        help="Create a saved-data-only defensive allocation posture preview without execution.",
    )
    parser.add_argument(
        "--defensive-allocation-risk-preview",
        action="store_true",
        help="Create a saved-data-only defensive allocation risk checkpoint without execution.",
    )
    parser.add_argument(
        "--defensive-allocation-decision-report",
        action="store_true",
        help="Create a saved-data-only defensive allocation decision report without execution.",
    )
    parser.add_argument(
        "--defensive-execution-readiness-report",
        action="store_true",
        help="Create a saved-data-only defensive execution readiness report without execution design.",
    )
    parser.add_argument(
        "--drawdown-period-report",
        action="store_true",
        help="Create a research-only drawdown period analysis report from saved equity curves.",
    )
    parser.add_argument(
        "--etf-defensive-drawdown-comparison",
        action="store_true",
        help="Compare saved ETF rotation and vol-managed ETF drawdown periods without execution.",
    )
    parser.add_argument(
        "--plot-etf-defensive-comparison",
        action="store_true",
        help="Create saved-CSV-only ETF rotation versus vol-managed ETF comparison charts.",
    )
    parser.add_argument(
        "--refresh-defensive-research",
        action="store_true",
        help="Refresh saved defensive research reports and charts without execution.",
    )
    parser.add_argument(
        "--short-selling-readiness-report",
        action="store_true",
        help="Create a research-only short-selling readiness audit without enabling shorting.",
    )
    parser.add_argument(
        "--short-hedge-backtest",
        action="store_true",
        help="Run a research-only synthetic SPY short hedge backtest without enabling short execution.",
    )
    parser.add_argument(
        "--short-strategy-lab",
        action="store_true",
        help="Run a research-only multi-ETF synthetic short strategy lab without enabling short execution.",
    )
    parser.add_argument(
        "--vol-managed-etf-backtest",
        action="store_true",
        help="Run a research-only volatility-managed ETF dual momentum backtest without execution.",
    )
    parser.add_argument(
        "--vol-managed-etf-robustness",
        action="store_true",
        help="Create a research-only fixed-split robustness report for the vol-managed ETF strategy.",
    )
    parser.add_argument(
        "--strategy-improvement-lab",
        action="store_true",
        help="Run a fixed research-only growth-aware ETF strategy improvement lab without execution.",
    )
    parser.add_argument(
        "--show-strategy-improvement-lab",
        action="store_true",
        help="Display the saved strategy improvement lab summary CSV without refreshing data.",
    )
    parser.add_argument(
        "--strategy-improvement-robustness",
        action="store_true",
        help="Create research-only robustness, cost, drawdown, and comparison reports for strategy improvement candidates.",
    )
    parser.add_argument(
        "--show-strategy-improvement-robustness",
        action="store_true",
        help="Display saved strategy improvement robustness comparison CSV without refreshing data.",
    )
    parser.add_argument(
        "--strategy-improvement-diagnostics",
        action="store_true",
        help="Create saved-CSV diagnostics explaining strategy improvement split sensitivity without execution.",
    )
    parser.add_argument(
        "--show-strategy-improvement-diagnostics",
        action="store_true",
        help="Display saved strategy improvement diagnostics CSV without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-validation",
        action="store_true",
        help="Create saved research-only validation for the stricter growth-biased breadth-gate lead.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-validation",
        action="store_true",
        help="Display saved stricter growth-biased validation CSVs without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-promotion-readiness",
        action="store_true",
        help="Create a research-only blocker report for stricter-gate preview promotion readiness.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-promotion-readiness",
        action="store_true",
        help="Display the saved stricter-gate promotion-readiness blocker report without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-manual-review-pack",
        action="store_true",
        help="Create a saved-output manual review pack for the stricter growth-biased research lead.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-manual-review-pack",
        action="store_true",
        help="Display the saved stricter-gate manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-threshold-neighbourhood",
        action="store_true",
        help="Run a fixed research-only threshold neighbourhood check for the stricter growth-biased breadth gate.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-threshold-neighbourhood",
        action="store_true",
        help="Display the saved stricter-gate threshold neighbourhood report without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-cost-turnover-stress",
        action="store_true",
        help="Create a saved-output turnover and cost stress report for the stricter 55%% breadth-gate cluster.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-cost-turnover-stress",
        action="store_true",
        help="Display the saved stricter-gate turnover and cost stress report without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-persistence-filter",
        action="store_true",
        help="Create a research-only persistence-filter report for the stricter 55%% breadth-gate cluster.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-persistence-filter",
        action="store_true",
        help="Display the saved stricter-gate persistence-filter report without refreshing data.",
    )
    parser.add_argument(
        "--crypto-research-preview",
        action="store_true",
        help="Create a research-only crypto scaffold preview without execution.",
    )
    parser.add_argument(
        "--crypto-strategy-lab",
        action="store_true",
        help="Run a research-only crypto strategy lab with daily yfinance-compatible history.",
    )
    parser.add_argument(
        "--crypto-strategy-report",
        action="store_true",
        help="Create a research-only crypto strategy summary report from saved lab results.",
    )
    parser.add_argument(
        "--crypto-strategy-decision-report",
        action="store_true",
        help="Create a research-only crypto strategy decision report from saved crypto reports.",
    )
    parser.add_argument(
        "--crypto-cost-stress-report",
        action="store_true",
        help="Create a research-only crypto strategy cost stress report.",
    )
    parser.add_argument(
        "--crypto-robustness-report",
        action="store_true",
        help="Create a research-only crypto robustness report across fixed chronological splits.",
    )
    parser.add_argument(
        "--crypto-period-diagnostics",
        action="store_true",
        help="Create a research-only diagnostic report for weak crypto robustness periods.",
    )
    parser.add_argument(
        "--preview-crypto-signals",
        action="store_true",
        help="Preview current crypto research candidate signals without execution.",
    )
    parser.add_argument(
        "--show-crypto-monitor",
        action="store_true",
        help="Display saved crypto signal and research status CSVs without refreshing data.",
    )
    parser.add_argument(
        "--crypto-research-state-report",
        action="store_true",
        help="Create a saved-data-only crypto research checkpoint report.",
    )
    parser.add_argument(
        "--ticker-universe-readiness-report",
        action="store_true",
        help="Create a research-only larger ticker universe readiness report without execution.",
    )
    parser.add_argument(
        "--market-monitor-snapshot",
        action="store_true",
        help="Create a research-only intraday market monitoring snapshot without execution.",
    )
    parser.add_argument(
        "--show-market-monitor",
        action="store_true",
        help="Display the saved market monitor snapshot CSV without refreshing data.",
    )
    parser.add_argument(
        "--market-monitor-quality-report",
        action="store_true",
        help="Create a saved-CSV quality report for the market monitor snapshot without refreshing data.",
    )
    parser.add_argument(
        "--refresh-market-monitor",
        action="store_true",
        help="Refresh the safe market monitor report/display chain without execution.",
    )
    parser.add_argument(
        "--market-monitor-scheduling-readiness-report",
        action="store_true",
        help="Create a report-only scheduling readiness audit for market monitor refresh.",
    )
    parser.add_argument(
        "--monitor-lockfile-readiness-report",
        action="store_true",
        help="Create a static report-only no-overlap/lockfile readiness design audit.",
    )
    parser.add_argument(
        "--preview-promoted-strategies",
        action="store_true",
        help="Preview current signals for promoted research candidates without trading.",
    )
    parser.add_argument(
        "--preview-promoted-actions",
        action="store_true",
        help="Compare promoted desired positions with paper positions without trading.",
    )
    parser.add_argument(
        "--use-paper-positions-readonly",
        action="store_true",
        help="With --preview-promoted-actions only, read Alpaca paper positions for preview context without trading.",
    )
    parser.add_argument(
        "--show-promoted-actions",
        action="store_true",
        help="Display the saved promoted action preview CSV without trading.",
    )
    parser.add_argument(
        "--promoted-risk-preview",
        action="store_true",
        help="Create a research-only risk preview from saved promoted strategy CSVs.",
    )
    parser.add_argument(
        "--promoted-consensus-preview",
        action="store_true",
        help="Create a research-only consensus preview from saved promoted strategy rows.",
    )
    parser.add_argument(
        "--promoted-decision-preview",
        action="store_true",
        help="Create a research-only decision policy preview from saved promoted reports.",
    )
    parser.add_argument(
        "--show-promoted-decision",
        action="store_true",
        help="Display the saved promoted decision preview CSV without trading.",
    )
    parser.add_argument(
        "--refresh-promoted-review",
        action="store_true",
        help="Refresh the promoted strategy review chain without execution.",
    )
    parser.add_argument(
        "--deployment-readiness-report",
        action="store_true",
        help="Create a local VPS/server deployment readiness audit without deploying or executing.",
    )
    parser.add_argument(
        "--vps-operations-readiness-report",
        action="store_true",
        help="Create a report-only VPS/Hermes operations readiness audit without scheduling or execution.",
    )
    parser.add_argument(
        "--vps-monitoring-status",
        action="store_true",
        help="Display a VPS-safe monitoring status summary without Alpaca, scheduling, or execution.",
    )
    parser.add_argument(
        "--vps-daily-monitoring-summary",
        action="store_true",
        help="Display a concise VPS-safe daily monitoring summary without refresh, scheduling, or execution.",
    )
    parser.add_argument(
        "--portfolio-risk-policy-report",
        action="store_true",
        help="Create a research-only portfolio risk policy audit without enforcing execution gates.",
    )
    parser.add_argument(
        "--show-portfolio-risk-policy",
        action="store_true",
        help="Display the saved portfolio risk policy report CSV without enforcing risk or trading.",
    )
    parser.add_argument(
        "--paper-kill-switch-readiness-report",
        action="store_true",
        help="Create a reporting-only readiness audit for future paper kill-switch design.",
    )
    parser.add_argument(
        "--paper-kill-switch-gate-report",
        action="store_true",
        help="Create a design/report-only paper kill-switch gate scaffold without execution.",
    )
    parser.add_argument(
        "--paper-execution-protection-report",
        action="store_true",
        help="Create a saved-data/static paper execution protection checkpoint without execution.",
    )
    parser.add_argument(
        "--normal-bot-execution-policy-report",
        action="store_true",
        help="Create a saved-data/static Option A normal bot execution policy report without execution.",
    )
    parser.add_argument(
        "--execution-eligibility-report",
        action="store_true",
        help="Create a saved-data-only execution eligibility report without approving execution.",
    )
    parser.add_argument(
        "--build-research-dashboard",
        action="store_true",
        help="Build a static saved-CSV research dashboard HTML file without running a server.",
    )
    parser.add_argument(
        "--show-promoted-risk",
        action="store_true",
        help="Display the saved promoted risk preview CSV without trading.",
    )
    parser.add_argument(
        "--preview-slow-sma-signals",
        action="store_true",
        help="Preview today's slow SMA crossover signals without trading.",
    )
    parser.add_argument(
        "--preview-slow-sma-actions",
        action="store_true",
        help="Preview target-position actions for the slow SMA strategy without trading.",
    )
    parser.add_argument(
        "--execute-slow-sma-paper",
        action="store_true",
        help="Align Alpaca paper positions with slow SMA target positions.",
    )
    parser.add_argument(
        "--confirm-slow-sma-paper",
        action="store_true",
        help="Required with --execute-slow-sma-paper before any paper orders can be submitted.",
    )
    parser.add_argument(
        "--research-universe",
        action="store_true",
        help="Use the broader research universe for research commands.",
    )
    parser.add_argument(
        "--etf-universe",
        action="store_true",
        help="Use the ETF-only research universe for supported research commands.",
    )
    parser.add_argument(
        "--plot-strategy-results",
        action="store_true",
        help="Create simple PNG charts from saved strategy comparison CSV files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.use_paper_positions_readonly and not args.preview_promoted_actions:
        print("--use-paper-positions-readonly can only be used with --preview-promoted-actions.", file=sys.stderr)
        return 2
    if args.plot_strategy_results:
        return plot_strategy_results()
    if args.research_report:
        try:
            result = generate_research_report()
        except Exception as exc:
            print(f"Research report failed: {exc}", file=sys.stderr)
            return 1
        for warning in result.warnings:
            print(f"Warning: {warning}")
        for line in result.summary_lines:
            print(line)
        print(f"Saved research report to {result.output_path}")
        return 0
    if args.walk_forward_report:
        try:
            result = generate_walk_forward_report()
        except Exception as exc:
            print(f"Walk-forward report failed: {exc}", file=sys.stderr)
            return 1
        for warning in result.warnings:
            print(f"Warning: {warning}")
        for line in result.summary_lines:
            print(line)
        print(f"Saved walk-forward report to {result.output_path}")
        return 0
    if args.strategy_promotion_report:
        try:
            result = generate_strategy_promotion_report()
        except Exception as exc:
            print(f"Strategy promotion report failed: {exc}", file=sys.stderr)
            return 1
        for warning in result.warnings:
            print(f"Warning: {warning}")
        for line in result.summary_lines:
            print(line)
        print(f"Saved strategy promotion report to {result.output_path}")
        return 0
    if args.defensive_strategy_report:
        try:
            result = generate_defensive_strategy_report()
        except Exception as exc:
            print(f"Defensive strategy report failed: {exc}", file=sys.stderr)
            return 1
        for warning in result.warnings:
            print(f"Warning: {warning}")
        for line in result.summary_lines:
            print(line)
        print(f"Saved defensive strategy report to {result.output_path}")
        return 0
    if args.defensive_candidate_comparison:
        return run_defensive_candidate_comparison_command()
    if args.defensive_research_state_report:
        return run_defensive_research_state_report_command()
    if args.defensive_allocation_preview:
        return run_defensive_allocation_preview_command()
    if args.defensive_allocation_risk_preview:
        return run_defensive_allocation_risk_preview_command()
    if args.defensive_allocation_decision_report:
        return run_defensive_allocation_decision_report_command()
    if args.defensive_execution_readiness_report:
        return run_defensive_execution_readiness_report_command()
    if args.drawdown_period_report:
        return run_drawdown_period_report_command()
    if args.etf_defensive_drawdown_comparison:
        return run_etf_defensive_drawdown_comparison_command()
    if args.plot_etf_defensive_comparison:
        return run_plot_etf_defensive_comparison_command()
    if args.refresh_defensive_research:
        return run_refresh_defensive_research_command()
    if args.short_selling_readiness_report:
        return run_short_selling_readiness_report_command()
    if args.etf_rotation_robustness:
        return run_etf_rotation_robustness_command()
    if args.etf_breadth_regime_backtest:
        return run_etf_breadth_regime_backtest_command()
    if args.etf_breadth_regime_decision_report:
        return run_etf_breadth_regime_decision_report_command()
    if args.etf_breadth_regime_robustness:
        return run_etf_breadth_regime_robustness_command()
    if args.strategy_improvement_lab:
        try:
            result = run_strategy_improvement_lab_files()
        except Exception as exc:
            print(f"Strategy improvement lab failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_strategy_improvement_lab:
        status_code, lines = show_strategy_improvement_lab_file()
        for line in lines:
            print(line)
        return status_code
    if args.strategy_improvement_robustness:
        try:
            result = generate_strategy_improvement_robustness()
        except Exception as exc:
            print(f"Strategy improvement robustness failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_strategy_improvement_robustness:
        status_code, lines = show_strategy_improvement_robustness_file()
        for line in lines:
            print(line)
        return status_code
    if args.strategy_improvement_diagnostics:
        try:
            result = generate_strategy_improvement_diagnostics()
        except Exception as exc:
            print(f"Strategy improvement diagnostics failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_strategy_improvement_diagnostics:
        status_code, lines = show_strategy_improvement_diagnostics_file()
        for line in lines:
            print(line)
        return status_code
    if args.growth_biased_stricter_validation:
        try:
            result = generate_growth_biased_stricter_validation()
        except Exception as exc:
            print(f"Growth-biased stricter validation failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_growth_biased_stricter_validation:
        status_code, lines = show_growth_biased_stricter_validation_file()
        for line in lines:
            print(line)
        return status_code
    if args.growth_biased_stricter_promotion_readiness:
        try:
            result = generate_growth_biased_stricter_promotion_readiness()
        except Exception as exc:
            print(f"Growth-biased stricter promotion readiness failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_growth_biased_stricter_promotion_readiness:
        status_code, lines = show_growth_biased_stricter_promotion_readiness_file()
        for line in lines:
            print(line)
        return status_code
    if args.growth_biased_stricter_manual_review_pack:
        try:
            result = generate_growth_biased_stricter_manual_review_pack()
        except Exception as exc:
            print(f"Growth-biased stricter manual review pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_growth_biased_stricter_manual_review_pack:
        status_code, lines = show_growth_biased_stricter_manual_review_pack_file()
        for line in lines:
            print(line)
        return status_code
    if args.growth_biased_stricter_threshold_neighbourhood:
        try:
            result = generate_growth_biased_stricter_threshold_neighbourhood()
        except Exception as exc:
            print(f"Growth-biased stricter threshold neighbourhood failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_growth_biased_stricter_threshold_neighbourhood:
        status_code, lines = show_growth_biased_stricter_threshold_neighbourhood_file()
        for line in lines:
            print(line)
        return status_code
    if args.growth_biased_stricter_cost_turnover_stress:
        try:
            result = generate_growth_biased_stricter_cost_turnover_stress()
        except Exception as exc:
            print(f"Growth-biased stricter cost/turnover stress failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_growth_biased_stricter_cost_turnover_stress:
        status_code, lines = show_growth_biased_stricter_cost_turnover_stress_file()
        for line in lines:
            print(line)
        return status_code
    if args.growth_biased_stricter_persistence_filter:
        try:
            result = generate_growth_biased_stricter_persistence_filter()
        except Exception as exc:
            print(f"Growth-biased stricter persistence filter failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_growth_biased_stricter_persistence_filter:
        status_code, lines = show_growth_biased_stricter_persistence_filter_file()
        for line in lines:
            print(line)
        return status_code
    if args.crypto_research_preview:
        result = run_crypto_research_preview_files()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.crypto_strategy_lab:
        try:
            result = run_crypto_strategy_lab_files()
        except Exception as exc:
            print(f"Crypto strategy lab failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.crypto_strategy_report:
        return run_crypto_strategy_report_command()
    if args.crypto_strategy_decision_report:
        return run_crypto_strategy_decision_report_command()
    if args.crypto_cost_stress_report:
        try:
            result = generate_crypto_cost_stress_report()
        except Exception as exc:
            print(f"Crypto cost stress report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        print(f"Saved crypto cost stress report to {result.output_path}")
        return 0
    if args.crypto_robustness_report:
        try:
            result = generate_crypto_robustness_report()
        except Exception as exc:
            print(f"Crypto robustness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        print(f"Saved crypto robustness report to {result.output_path}")
        return 0
    if args.crypto_period_diagnostics:
        return run_crypto_period_diagnostics_command()
    if args.preview_crypto_signals:
        try:
            result = generate_crypto_signal_preview()
        except Exception as exc:
            print(f"Crypto signal preview failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_crypto_monitor:
        return run_show_crypto_monitor_command()
    if args.crypto_research_state_report:
        return run_crypto_research_state_report_command()
    if args.ticker_universe_readiness_report:
        return run_ticker_universe_readiness_report_command()
    if args.market_monitor_snapshot:
        return run_market_monitor_snapshot_command()
    if args.show_market_monitor:
        return run_show_market_monitor_command()
    if args.market_monitor_quality_report:
        return run_market_monitor_quality_report_command()
    if args.refresh_market_monitor:
        return run_refresh_market_monitor_command()
    if args.market_monitor_scheduling_readiness_report:
        return run_market_monitor_scheduling_readiness_report_command()
    if args.monitor_lockfile_readiness_report:
        return run_monitor_lockfile_readiness_report_command()
    if args.show_promoted_actions:
        return run_show_promoted_actions_command()
    if args.promoted_risk_preview:
        return run_promoted_risk_preview()
    if args.promoted_consensus_preview:
        return run_promoted_consensus_preview()
    if args.promoted_decision_preview:
        return run_promoted_decision_preview()
    if args.show_promoted_decision:
        return run_show_promoted_decision_command()
    if args.deployment_readiness_report:
        return run_deployment_readiness_report_command()
    if args.vps_operations_readiness_report:
        return run_vps_operations_readiness_report_command()
    if args.vps_monitoring_status:
        from trading_bot.research.vps_monitoring_status import print_vps_monitoring_status

        return print_vps_monitoring_status()
    if args.vps_daily_monitoring_summary:
        from trading_bot.research.vps_daily_monitoring_summary import print_vps_daily_monitoring_summary

        return print_vps_daily_monitoring_summary()
    if args.portfolio_risk_policy_report:
        return run_portfolio_risk_policy_report_command()
    if args.show_portfolio_risk_policy:
        return run_show_portfolio_risk_policy_command()
    if args.paper_kill_switch_readiness_report:
        return run_paper_kill_switch_readiness_report_command()
    if args.paper_kill_switch_gate_report:
        return run_paper_kill_switch_gate_report_command()
    if args.paper_execution_protection_report:
        return run_paper_execution_protection_report_command()
    if args.normal_bot_execution_policy_report:
        return run_normal_bot_execution_policy_report_command()
    if args.execution_eligibility_report:
        return run_execution_eligibility_report_command()
    if args.build_research_dashboard:
        return run_build_research_dashboard_command()
    if args.show_promoted_risk:
        return run_show_promoted_risk_command()

    config_path = Path(args.config).resolve()

    try:
        config = load_config(
            config_path,
            force_dry_run=args.dry_run,
            allow_missing_alpaca_keys=(
                args.preview_slow_sma_actions
                or args.preview_promoted_strategies
                or args.preview_promoted_actions
                or args.build_etf_breadth_price_history
                or args.refresh_promoted_review
                or (args.execute_slow_sma_paper and not args.confirm_slow_sma_paper)
            ),
        )
        logger = setup_logging(config.log_file)
        if args.execute_slow_sma_paper:
            return run_slow_sma_paper_execution(
                config,
                logger,
                confirm_slow_sma_paper=args.confirm_slow_sma_paper,
                force_research_universe=args.research_universe,
                force_etf_universe=args.etf_universe,
            )
        if args.preview_slow_sma_actions:
            return run_slow_sma_action_preview(
                config,
                logger,
                force_research_universe=args.research_universe,
                force_etf_universe=args.etf_universe,
            )
        if args.preview_promoted_strategies:
            return run_promoted_strategy_preview(config, logger)
        if args.preview_promoted_actions:
            return run_promoted_action_preview(
                config,
                logger,
                use_paper_positions_readonly=args.use_paper_positions_readonly,
            )
        if args.refresh_promoted_review:
            return run_refresh_promoted_review_command(
                lambda: run_promoted_strategy_preview(config, logger),
                lambda: run_promoted_action_preview(
                    config,
                    logger,
                    use_paper_positions_readonly=True,
                ),
                run_promoted_risk_preview,
                run_promoted_consensus_preview,
                run_promoted_decision_preview,
            )
        if args.preview_slow_sma_signals:
            return run_slow_sma_signal_preview(
                config,
                logger,
                force_research_universe=args.research_universe,
                force_etf_universe=args.etf_universe,
            )
        if args.trend_stress_test:
            return run_trend_stress_test(
                config,
                logger,
                force_research_universe=args.research_universe,
                force_etf_universe=args.etf_universe,
            )
        if args.etf_rotation_backtest:
            return run_etf_rotation_backtest(config, logger)
        if args.build_etf_breadth_price_history:
            return run_build_etf_breadth_price_history_command(config, logger)
        if args.adaptive_momentum_backtest:
            return run_adaptive_momentum_backtest(config, logger)
        if args.short_hedge_backtest:
            return run_short_hedge_backtest_command(config, logger)
        if args.short_strategy_lab:
            return run_short_strategy_lab_command(config, logger)
        if args.vol_managed_etf_backtest:
            return run_vol_managed_etf_backtest_command(config, logger)
        if args.vol_managed_etf_robustness:
            return run_vol_managed_etf_robustness_command(config, logger)
        if args.sma_sensitivity:
            return run_sma_sensitivity(
                config,
                logger,
                force_research_universe=args.research_universe,
            )
        if args.compare_strategies:
            return run_strategy_comparison(
                config,
                logger,
                force_research_universe=args.research_universe,
            )
        if args.backtest:
            return run_backtest(config, logger)
        if args.paper_order_test:
            ticker, side, quantity = args.paper_order_test
            return run_paper_order_test(
                config=config,
                logger=logger,
                ticker=ticker,
                side=side,
                quantity_text=quantity,
                confirm_paper_order=args.confirm_paper_order,
            )
        return run_bot(config, logger)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
