"""CLI table and preview output formatting helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from trading_bot.positions import Position, format_decimal
from trading_bot.strategies.sma import SlowSmaPreviewRow


def format_slow_sma_preview_table_header() -> str:
    return (
        f"{'ticker':<8} {'close':>12} {'short_sma':>12} "
        f"{'long_sma':>12} {'trend_state':<11} {'signal':<6} "
        f"{'desired_position':<16} {'days_since_last_crossover':>27} reason"
    )


def format_slow_sma_preview_table_row(row: SlowSmaPreviewRow) -> str:
    days_text = (
        str(row.days_since_last_crossover)
        if row.days_since_last_crossover is not None
        else "n/a"
    )
    return (
        f"{row.ticker:<8} {row.close:>12.2f} {row.short_sma:>12.2f} "
        f"{row.long_sma:>12.2f} {row.trend_state:<11} {row.signal:<6} "
        f"{row.desired_position:<16} {days_text:>27} {row.reason}"
    )


def format_slow_sma_preview_error_row(ticker: str, error: str) -> str:
    return (
        f"{ticker:<8} {'ERROR':>12} {'':>12} {'':>12} {'':<11} "
        f"{'':<6} {'':<16} {'':>27} {error}"
    )


def format_slow_sma_action_preview_table_header() -> str:
    return (
        f"{'ticker':<8} {'trend_state':<11} {'signal':<6} {'desired_position':<16} "
        f"{'current_position':<16} {'current_qty':>12} {'proposed_action':<20} "
        f"{'open_order_exists':<17} reason"
    )


def format_slow_sma_action_preview_table_row(row: Any) -> str:
    return (
        f"{row.ticker:<8} {row.trend_state:<11} {row.signal:<6} "
        f"{row.desired_position:<16} {row.current_position:<16} "
        f"{format_decimal(row.current_qty):>12} {row.proposed_action:<20} "
        f"{str(row.open_order_exists).lower():<17} {row.reason}"
    )


def format_slow_sma_action_preview_error_row(ticker: str, error: str) -> str:
    return (
        f"{ticker:<8} {'ERROR':<11} {'':<6} {'':<16} {'':<16} "
        f"{'':>12} {'':<20} {'':<17} {error}"
    )


def format_slow_sma_execution_table_header() -> str:
    return (
        f"{'ticker':<8} {'desired_position':<16} {'position_before':<16} "
        f"{'side':<5} {'action':<18} {'quantity':>12} {'order_status':<14} message"
    )


def format_slow_sma_execution_table_row(
    ticker: str,
    desired_position: str,
    position_before: Position,
    side: str,
    action: str,
    quantity: Decimal,
    order_status: str,
    message: str,
) -> str:
    return (
        f"{ticker:<8} {desired_position:<16} {position_before.label():<16} "
        f"{side:<5} {action:<18} {format_decimal(quantity):>12} {order_status:<14} {message}"
    )


def format_slow_sma_execution_error_row(ticker: str, message: str) -> str:
    return (
        f"{ticker:<8} {'ERROR':<16} {'':<16} {'':<5} "
        f"{'review_manually':<18} {'0':>12} {'':<14} {message}"
    )
