from __future__ import annotations

import csv
import logging
import sqlite3
import sys
from dataclasses import (
    dataclass,
    replace,
)
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from decimal import (
    Decimal,
    InvalidOperation,
)
from pathlib import (
    Path,
)
from typing import (
    Any,
)

from alpaca.trading.client import (
    TradingClient,
)

from trading_bot.alpaca_client import (
    get_open_orders_for_ticker,
    normalize_order_side,
    normalize_order_status,
    refresh_order_status,
    validate_alpaca_asset_for_order,
)
from trading_bot.cli.parser import (
    parse_args,
)
from trading_bot.cli.dispatch import (
    dispatch_config_command,
    dispatch_pre_config,
)
from trading_bot.config import (
    AppConfig,
    ConfigError,
    load_config,
)
from trading_bot.database import (
    init_database,
    insert_trade_log,
)
from trading_bot.discord_alerts import (
    send_discord_alert,
)
from trading_bot.execution import (
    manual_sell_would_oversell,
)
from trading_bot.logging_setup import (
    setup_logging,
)
from trading_bot.market_data import (
    configure_yfinance_cache,
    download_backtest_prices,
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
from trading_bot.paper_orders import (
    PaperOrderRequest,
    PaperOrderRoute,
    submit_paper_order,
)
from trading_bot.positions import (
    POSITION_FLAT,
    POSITION_LONG,
    POSITION_SHORT,
    Position,
    decimal_from_any,
    format_decimal,
    get_alpaca_positions,
)
from trading_bot.safety.qqq100_paper_execution import (
    FIXED_QUANTITY as QQQ100_FIXED_QUANTITY,
    TICKER as QQQ100_TICKER,
    evaluate_qqq100_paper_execution_preflight,
    print_qqq100_paper_execution_decision,
    read_saved_qqq100_preview_signal,
    write_qqq100_paper_execution_report,
)
from trading_bot.research.promoted_actions import (
    build_promoted_action_preview_rows,
    build_promoted_action_summary,
    read_promoted_strategy_preview,
    write_promoted_action_preview,
)
from trading_bot.research.promoted_preview import (
    append_qqq100_promoted_preview_candidate,
    build_promoted_preview_rows,
    build_promoted_preview_summary,
    read_preview_candidates,
    unsupported_preview_row,
    write_promoted_preview,
)
from trading_bot.runners.backtests import (
    get_strategy_comparison_tickers,
    run_adaptive_momentum_backtest,
    run_backtest,
    run_etf_rotation_backtest,
    run_sma_sensitivity,
    run_strategy_comparison,
    run_trend_stress_test,
)
from trading_bot.runners.previews import (
    run_promoted_consensus_preview,
    run_promoted_decision_preview,
    run_promoted_risk_preview,
)
from trading_bot.runners.paper_execution import (
    decimal_to_float,
    run_bot,
)
from trading_bot.runners.vol_targeted_growth_paper import (
    run_execute_vol_targeted_growth_paper,
    run_prepare_vol_targeted_growth_paper_ticket,
    run_vol_targeted_growth_paper_postcheck,
)
from trading_bot.runners.research_reports import (
    run_build_etf_breadth_price_history_command,
    run_refresh_promoted_review_command,
    run_short_hedge_backtest_command,
    run_short_strategy_lab_command,
    run_vol_managed_etf_backtest_command,
    run_vol_managed_etf_robustness_command,
)
from trading_bot.safety.paper_kill_switch import (
    evaluate_paper_kill_switch_gate,
)
from trading_bot.safety.manual_paper_smoke_test_gate import (
    RECENT_ORDER_LOOKBACK_MINUTES,
    evaluate_recent_manual_smoke_test_order_match,
    evaluate_manual_paper_smoke_test_gate,
    read_saved_smoke_test_preflight_context,
    write_manual_paper_smoke_test_gate_report,
)
from trading_bot.strategies.sma import (
    SlowSmaPreviewRow,
    calculate_slow_sma_preview_row,
)



class ManualOrderError(RuntimeError):
    """Raised when the manual paper-order smoke test is not safe to submit."""


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


def parse_order_test_quantity(value: str) -> Decimal:
    try:
        quantity = Decimal(value)
    except InvalidOperation as exc:
        raise ManualOrderError(f"Order quantity must be a positive number, not {value!r}.") from exc

    if not quantity.is_finite() or quantity <= 0:
        raise ManualOrderError("Order quantity must be a finite positive number.")
    return quantity


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

        smoke_test_gate_decision = None
        is_aapl_buy_one_template = ticker == "AAPL" and side == "buy" and quantity == Decimal("1")
        if is_aapl_buy_one_template:
            smoke_test_gate_decision = evaluate_manual_paper_smoke_test_gate(
                ticker=ticker,
                side=side,
                quantity=quantity,
                confirm_paper_order=confirm_paper_order,
                alpaca_paper=config.alpaca_paper,
                allow_shorting=config.allow_shorting,
                credentials_present=bool(config.alpaca_api_key and config.alpaca_secret_key),
                preflight=read_saved_smoke_test_preflight_context(),
            )
            if not smoke_test_gate_decision.allowed:
                print_manual_smoke_test_gate_decision(smoke_test_gate_decision)
                write_manual_paper_smoke_test_gate_report(smoke_test_gate_decision)
                logger.warning(
                    "Manual paper smoke-test gate blocked: %s",
                    "; ".join(smoke_test_gate_decision.reasons),
                )
                return 2

        if config.dry_run and not confirm_paper_order:
            raise ManualOrderError(
                "config.json has dry_run=true. Re-run with --confirm-paper-order to submit one paper order."
            )

        if smoke_test_gate_decision is None:
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

        alpaca_client = TradingClient(
            config.alpaca_api_key,
            config.alpaca_secret_key,
            paper=True,
        )

        positions = get_alpaca_positions(alpaca_client)
        position_before = positions.get(ticker, Position())
        if manual_sell_would_oversell(side, quantity, position_before, config.allow_shorting):
            message = (
                f"Manual paper-order test skipped: selling {format_decimal(quantity)} "
                f"{ticker} would exceed current long position of "
                f"{format_decimal(position_before.abs_quantity)} share(s)."
            )
            logger.warning(message)
            conn = init_database(config.database_path)
            order_config = replace(config, dry_run=False)
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

        open_orders = get_open_orders_for_ticker(alpaca_client, ticker)
        if smoke_test_gate_decision is not None:
            smoke_test_gate_decision = evaluate_manual_paper_smoke_test_gate(
                ticker=ticker,
                side=side,
                quantity=quantity,
                confirm_paper_order=confirm_paper_order,
                alpaca_paper=config.alpaca_paper,
                allow_shorting=config.allow_shorting,
                credentials_present=bool(config.alpaca_api_key and config.alpaca_secret_key),
                preflight=read_saved_smoke_test_preflight_context(),
                direct_open_order_count=len(open_orders),
            )
            if not smoke_test_gate_decision.allowed:
                print_manual_smoke_test_gate_decision(smoke_test_gate_decision)
                write_manual_paper_smoke_test_gate_report(smoke_test_gate_decision)
                logger.warning(
                    "Manual paper smoke-test gate blocked after open-order check: %s",
                    "; ".join(smoke_test_gate_decision.reasons),
                )
                return 2

            duplicate_recent_order = recent_matching_manual_smoke_test_order_check(
                alpaca_client,
                ticker,
                side,
                quantity,
            )
            smoke_test_gate_decision = evaluate_manual_paper_smoke_test_gate(
                ticker=ticker,
                side=side,
                quantity=quantity,
                confirm_paper_order=confirm_paper_order,
                alpaca_paper=config.alpaca_paper,
                allow_shorting=config.allow_shorting,
                credentials_present=bool(config.alpaca_api_key and config.alpaca_secret_key),
                preflight=read_saved_smoke_test_preflight_context(),
                direct_open_order_count=len(open_orders),
                duplicate_recent_order_check=duplicate_recent_order.duplicate_recent_order_check,
                duplicate_recent_order_source=duplicate_recent_order.duplicate_recent_order_source,
                duplicate_recent_order_status_if_any=duplicate_recent_order.duplicate_recent_order_status_if_any,
                recent_order_match_found=duplicate_recent_order.recent_order_match_found,
                recent_order_match_status=duplicate_recent_order.recent_order_match_status,
                recent_order_match_submitted_at_or_created_at=(
                    duplicate_recent_order.recent_order_match_submitted_at_or_created_at
                ),
                recent_order_match_age_minutes=duplicate_recent_order.recent_order_match_age_minutes,
                recent_order_match_source=duplicate_recent_order.recent_order_match_source,
                recent_order_match_count=duplicate_recent_order.recent_order_match_count,
                recent_order_match_lookback_minutes=duplicate_recent_order.recent_order_match_lookback_minutes,
            )
            print_manual_smoke_test_gate_decision(smoke_test_gate_decision)
            write_manual_paper_smoke_test_gate_report(smoke_test_gate_decision)
            if not smoke_test_gate_decision.allowed:
                logger.warning(
                    "Manual paper smoke-test gate blocked after duplicate-order check: %s",
                    "; ".join(smoke_test_gate_decision.reasons),
                )
                return 2

        is_valid_asset, asset_error = validate_alpaca_asset_for_order(
            alpaca_client,
            ticker,
            requires_shortable=False,
        )
        if not is_valid_asset:
            raise ManualOrderError(asset_error)

        if open_orders:
            message = f"An open Alpaca order already exists for {ticker}; manual test order skipped."
            logger.warning(message)
            conn = init_database(config.database_path)
            order_config = replace(config, dry_run=False)
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

        conn = init_database(config.database_path)
        order_config = replace(config, dry_run=False)
        submission = submit_paper_order(
            alpaca_client,
            PaperOrderRequest(
                route=PaperOrderRoute.MANUAL_TEST,
                ticker=ticker,
                side=side,
                quantity=quantity,
                confirmed=confirm_paper_order,
                alpaca_paper=config.alpaca_paper,
            ),
        )
        order_id = submission.order_id
        order_status = normalize_order_status(submission.initial_status)
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
        if smoke_test_gate_decision is not None:
            write_manual_paper_smoke_test_gate_report(smoke_test_gate_decision, order_event="order_submitted")
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


def run_execute_qqq100_paper(
    config: AppConfig,
    logger: logging.Logger,
    confirm_qqq100_paper: bool,
) -> int:
    signal = read_saved_qqq100_preview_signal()
    credentials_present = bool(config.alpaca_api_key and config.alpaca_secret_key)

    basic_decision = evaluate_qqq100_paper_execution_preflight(
        confirm_qqq100_paper=confirm_qqq100_paper,
        alpaca_paper=config.alpaca_paper,
        allow_shorting=config.allow_shorting,
        credentials_present=credentials_present,
        market_status="unknown",
        signal=signal,
        current_position=None,
        position_readable=False,
        open_order_count=None,
    )
    basic_blockers = [
        reason
        for reason in basic_decision.reasons
        if reason
        in {
            "--confirm-qqq100-paper is required",
            "alpaca.paper must be true; live trading is refused",
            "allow_shorting must remain false",
            "Alpaca paper credentials are required",
            "saved QQQ100 preview signal is missing",
            "saved signal strategy must be qqq_100_trend_gate",
            "saved signal ticker must be QQQ",
            "saved desired_position must be long or flat",
            "saved QQQ100 preview signal data_status must be ok",
            "saved QQQ100 preview signal contains data_error",
        }
    ]
    if basic_blockers:
        print_qqq100_paper_execution_decision(basic_decision)
        write_qqq100_paper_execution_report(basic_decision)
        return 2

    try:
        alpaca_client = TradingClient(
            config.alpaca_api_key,
            config.alpaca_secret_key,
            paper=True,
        )

        try:
            clock = alpaca_client.get_clock()
            market_status = "open" if bool(getattr(clock, "is_open", False)) else "closed"
        except Exception as exc:
            market_status = "unknown"
            market_error = f"Alpaca paper market clock check failed: {type(exc).__name__}"
        else:
            market_error = ""

        try:
            positions = get_alpaca_positions(alpaca_client)
            current_position = positions.get(QQQ100_TICKER, Position())
            position_readable = True
            position_error = ""
        except Exception as exc:
            current_position = None
            position_readable = False
            position_error = f"current QQQ paper position read failed: {type(exc).__name__}"

        try:
            open_orders = get_open_orders_for_ticker(alpaca_client, QQQ100_TICKER)
            open_order_count: int | None = len(open_orders)
            open_order_error = ""
        except Exception as exc:
            open_order_count = None
            open_order_error = f"open QQQ order read failed: {type(exc).__name__}"

        preliminary_decision = evaluate_qqq100_paper_execution_preflight(
            confirm_qqq100_paper=confirm_qqq100_paper,
            alpaca_paper=config.alpaca_paper,
            allow_shorting=config.allow_shorting,
            credentials_present=credentials_present,
            market_status=market_status,
            signal=signal,
            current_position=current_position,
            position_readable=position_readable,
            open_order_count=open_order_count,
            extra_blockers=[item for item in [market_error, position_error, open_order_error] if item],
        )

        recent_order_match = None
        if preliminary_decision.intended_action in {"buy_1", "sell_1"}:
            recent_order_match = recent_matching_manual_smoke_test_order_check(
                alpaca_client,
                QQQ100_TICKER,
                preliminary_decision.order_side,
                QQQ100_FIXED_QUANTITY,
            )

        decision = evaluate_qqq100_paper_execution_preflight(
            confirm_qqq100_paper=confirm_qqq100_paper,
            alpaca_paper=config.alpaca_paper,
            allow_shorting=config.allow_shorting,
            credentials_present=credentials_present,
            market_status=market_status,
            signal=signal,
            current_position=current_position,
            position_readable=position_readable,
            open_order_count=open_order_count,
            recent_order_match=recent_order_match,
            extra_blockers=[item for item in [market_error, position_error, open_order_error] if item],
        )
        print_qqq100_paper_execution_decision(decision)

        if not decision.allowed:
            write_qqq100_paper_execution_report(decision)
            logger.warning("QQQ100 paper execution blocked: %s", "; ".join(decision.reasons))
            return 2

        if decision.intended_action not in {"buy_1", "sell_1"}:
            write_qqq100_paper_execution_report(
                decision,
                order_status="skipped_no_order_needed",
                order_event="order_skipped_no_order_needed",
            )
            return 0

        is_valid_asset, asset_error = validate_alpaca_asset_for_order(
            alpaca_client,
            QQQ100_TICKER,
            requires_shortable=False,
        )
        if not is_valid_asset:
            blocked = evaluate_qqq100_paper_execution_preflight(
                confirm_qqq100_paper=confirm_qqq100_paper,
                alpaca_paper=config.alpaca_paper,
                allow_shorting=config.allow_shorting,
                credentials_present=credentials_present,
                market_status=market_status,
                signal=signal,
                current_position=current_position,
                position_readable=position_readable,
                open_order_count=open_order_count,
                recent_order_match=recent_order_match,
                extra_blockers=[asset_error],
            )
            print_qqq100_paper_execution_decision(blocked)
            write_qqq100_paper_execution_report(blocked)
            return 2

        submission = submit_paper_order(
            alpaca_client,
            PaperOrderRequest(
                route=PaperOrderRoute.QQQ100,
                ticker=QQQ100_TICKER,
                side=decision.order_side,
                quantity=QQQ100_FIXED_QUANTITY,
                confirmed=confirm_qqq100_paper,
                alpaca_paper=config.alpaca_paper,
            ),
        )
        order_id = submission.order_id
        order_status = normalize_order_status(submission.initial_status)
        order_status = refresh_order_status(
            alpaca_client,
            logger,
            order_id,
            order_status,
            timeout_seconds=10,
        )
        position_after = estimate_manual_position_after(
            current_position or Position(),
            decision.order_side,
            QQQ100_FIXED_QUANTITY,
            order_status,
        )
        write_qqq100_paper_execution_report(
            decision,
            order_status=order_status,
            order_event="order_submitted",
        )
        message = (
            f"QQQ100 manual paper order submitted: {QQQ100_TICKER} "
            f"{decision.order_side.upper()} {format_decimal(QQQ100_FIXED_QUANTITY)} share(s), "
            f"status {order_status}"
        )
        logger.info(message)
        return 0
    except Exception as exc:
        message = f"QQQ100 paper execution failed safely: {type(exc).__name__}"
        logger.error(message)
        blocked = evaluate_qqq100_paper_execution_preflight(
            confirm_qqq100_paper=confirm_qqq100_paper,
            alpaca_paper=config.alpaca_paper,
            allow_shorting=config.allow_shorting,
            credentials_present=credentials_present,
            market_status="unknown",
            signal=signal,
            current_position=None,
            position_readable=False,
            open_order_count=None,
            extra_blockers=[message],
        )
        write_qqq100_paper_execution_report(blocked)
        print(message)
        return 1


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


def print_manual_smoke_test_gate_decision(decision: Any) -> None:
    print("PAPER ORDER TEST MANUAL CONNECTIVITY SMOKE-TEST GATE.")
    print(f"gate_type={decision.gate_type}")
    print(f"ticker={decision.ticker}")
    print(f"side={decision.side}")
    print(f"quantity={decision.quantity}")
    print(f"market_status={decision.market_status}")
    print(f"live_preflight_status={decision.live_preflight_status}")
    print(f"open_order_check={decision.open_order_check}")
    print(f"duplicate_recent_order_check={decision.duplicate_recent_order_check}")
    print(f"duplicate_recent_order_source={decision.duplicate_recent_order_source}")
    print(f"duplicate_recent_order_status_if_any={decision.duplicate_recent_order_status_if_any or 'none'}")
    print(f"recent_order_match_found={decision.recent_order_match_found}")
    print(f"recent_order_match_status={decision.recent_order_match_status or 'none'}")
    print(
        "recent_order_match_submitted_at_or_created_at="
        f"{decision.recent_order_match_submitted_at_or_created_at or 'none'}"
    )
    print(f"recent_order_match_age_minutes={decision.recent_order_match_age_minutes or 'none'}")
    print(f"recent_order_match_source={decision.recent_order_match_source}")
    print(f"recent_order_match_count={decision.recent_order_match_count}")
    print(f"recent_order_match_lookback_minutes={decision.recent_order_match_lookback_minutes}")
    print(
        "current_position_context_ignored_for_duplicate_check="
        f"{decision.current_position_context_ignored_for_duplicate_check}"
    )
    print(f"smoke_test_order_approved={decision.smoke_test_order_approved}")
    print(f"execution_approved={decision.execution_approved}")
    print(f"scheduling_approved={decision.scheduling_approved}")
    print(f"strategy_execution_approved={decision.strategy_execution_approved}")
    if not decision.allowed:
        print("No orders were created, submitted, or cancelled.")
        print("Reasons:")
        for reason in decision.reasons:
            print(f"- {reason}")
        print(decision.required_next_step)
    else:
        print("Narrow smoke-test gate passed for the exact manual AAPL buy 1 connectivity test only.")
        print("Strategy execution remains blocked; this is not scheduling or strategy approval.")


@dataclass(frozen=True)
class ManualSmokeTestDuplicateOrderCheck:
    duplicate_recent_order_check: str
    duplicate_recent_order_source: str
    duplicate_recent_order_status_if_any: str
    recent_order_match_found: bool = False
    recent_order_match_status: str = ""
    recent_order_match_submitted_at_or_created_at: str = ""
    recent_order_match_age_minutes: str = ""
    recent_order_match_source: str = "alpaca_paper_recent_orders"
    recent_order_match_count: int = 0
    recent_order_match_lookback_minutes: int = RECENT_ORDER_LOOKBACK_MINUTES
    recent_order_match_time_field_used: str = ""


def recent_matching_manual_smoke_test_order_check(
    client: TradingClient,
    ticker: str,
    side: str,
    quantity: Decimal,
) -> ManualSmokeTestDuplicateOrderCheck:
    from alpaca.common.enums import Sort
    from alpaca.trading.enums import OrderSide
    from alpaca.trading.enums import QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest

    request = GetOrdersRequest(
        status=QueryOrderStatus.CLOSED,
        symbols=[ticker],
        side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
        limit=500,
        after=datetime.now(timezone.utc) - timedelta(minutes=RECENT_ORDER_LOOKBACK_MINUTES),
        direction=Sort.DESC,
    )
    try:
        recent_orders = list(client.get_orders(filter=request))
    except Exception as exc:
        return ManualSmokeTestDuplicateOrderCheck(
            duplicate_recent_order_check="blocked_duplicate_order_history_uncertain",
            duplicate_recent_order_source=f"alpaca_paper_recent_orders_read_failed:{type(exc).__name__}",
            duplicate_recent_order_status_if_any="",
            recent_order_match_time_field_used="unavailable",
        )

    result = evaluate_recent_manual_smoke_test_order_match(
        recent_orders,
        ticker=ticker,
        side=side,
        quantity=quantity,
    )
    return ManualSmokeTestDuplicateOrderCheck(**result.__dict__)


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






















































def run_promoted_strategy_preview(config: AppConfig, logger: logging.Logger) -> int:
    print("WARNING: This command is preview-only and does not approve execution.")
    configure_yfinance_cache(config, logger)
    promotion_path = Path("data") / "strategy_promotion_report.csv"
    if not promotion_path.exists():
        print(f"Missing legacy strategy promotion report: {promotion_path}")
        rows: list[dict[str, Any]] = []
        warnings: list[str] = []
        append_qqq100_promoted_preview_candidate(rows, warnings)
        output_path = Path("data") / "promoted_strategy_preview.csv"
        write_promoted_preview(output_path, rows)
        for warning in warnings:
            print(f"Warning: {warning}")
        for line in build_promoted_preview_summary(rows, warnings):
            print(line)
        print(f"Saved promoted strategy preview to {output_path}")
        qqq100_available = any(
            row.get("strategy_name") == "qqq_100_trend_gate"
            and row.get("ticker") == "QQQ"
            and row.get("promotion_status") == "preview_candidate"
            for row in rows
        )
        if qqq100_available:
            return 0
        print(
            "Missing both legacy strategy promotion report and usable QQQ100 preview signal input.",
            file=sys.stderr,
        )
        return 1

    candidates = read_preview_candidates(promotion_path)
    if not candidates:
        print("No legacy preview_candidate portfolio rows found.")
        rows: list[dict[str, Any]] = []
        warnings: list[str] = []
        append_qqq100_promoted_preview_candidate(rows, warnings)
        output_path = Path("data") / "promoted_strategy_preview.csv"
        write_promoted_preview(output_path, rows)
        for warning in warnings:
            print(f"Warning: {warning}")
        for line in build_promoted_preview_summary(rows, warnings):
            print(line)
        print(f"Saved promoted strategy preview to {output_path}")
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
    append_qqq100_promoted_preview_candidate(rows, warnings)

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
                    confirm_slow_sma_paper=confirm_slow_sma_paper,
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
    confirm_slow_sma_paper: bool,
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
        submission = submit_paper_order(
            alpaca_client,
            PaperOrderRequest(
                route=PaperOrderRoute.SLOW_SMA,
                ticker=ticker,
                side=side,
                quantity=quantity,
                confirmed=confirm_slow_sma_paper,
                alpaca_paper=config.alpaca_paper,
            ),
        )
        order_id = submission.order_id
        order_status = normalize_order_status(submission.initial_status)
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












def build_config_handlers():
    return {
        "prepare_vol_targeted_growth_paper_ticket": lambda command_args, command_config, command_logger: run_prepare_vol_targeted_growth_paper_ticket(
            command_config,
            command_logger,
            confirm_readonly_alpaca_check=command_args.confirm_readonly_alpaca_check,
        ),
        "execute_vol_targeted_growth_paper": lambda command_args, command_config, command_logger: run_execute_vol_targeted_growth_paper(
            command_config,
            command_logger,
            ticket_id=command_args.execute_vol_targeted_growth_paper,
            confirmed=command_args.confirm_vol_targeted_growth_paper,
        ),
        "vol_targeted_growth_paper_postcheck": lambda command_args, command_config, command_logger: run_vol_targeted_growth_paper_postcheck(
            command_config,
            command_logger,
            confirm_readonly_alpaca_check=command_args.confirm_readonly_alpaca_check,
        ),
        "execute_qqq100_paper": lambda command_args, command_config, command_logger: run_execute_qqq100_paper(
            config=command_config,
            logger=command_logger,
            confirm_qqq100_paper=command_args.confirm_qqq100_paper,
        ),
        "execute_slow_sma_paper": lambda command_args, command_config, command_logger: run_slow_sma_paper_execution(
            command_config,
            command_logger,
            confirm_slow_sma_paper=command_args.confirm_slow_sma_paper,
            force_research_universe=command_args.research_universe,
            force_etf_universe=command_args.etf_universe,
        ),
        "preview_slow_sma_actions": lambda command_args, command_config, command_logger: run_slow_sma_action_preview(
            command_config,
            command_logger,
            force_research_universe=command_args.research_universe,
            force_etf_universe=command_args.etf_universe,
        ),
        "preview_promoted_strategies": lambda command_args, command_config, command_logger: run_promoted_strategy_preview(
            command_config,
            command_logger,
        ),
        "preview_promoted_actions": lambda command_args, command_config, command_logger: run_promoted_action_preview(
            command_config,
            command_logger,
            use_paper_positions_readonly=command_args.use_paper_positions_readonly,
        ),
        "refresh_promoted_review": lambda command_args, command_config, command_logger: run_refresh_promoted_review_command(
            lambda: run_promoted_strategy_preview(command_config, command_logger),
            lambda: run_promoted_action_preview(
                command_config,
                command_logger,
                use_paper_positions_readonly=True,
            ),
            run_promoted_risk_preview,
            run_promoted_consensus_preview,
            run_promoted_decision_preview,
        ),
        "preview_slow_sma_signals": lambda command_args, command_config, command_logger: run_slow_sma_signal_preview(
            command_config,
            command_logger,
            force_research_universe=command_args.research_universe,
            force_etf_universe=command_args.etf_universe,
        ),
        "trend_stress_test": lambda command_args, command_config, command_logger: run_trend_stress_test(
            command_config,
            command_logger,
            force_research_universe=command_args.research_universe,
            force_etf_universe=command_args.etf_universe,
        ),
        "etf_rotation_backtest": lambda command_args, command_config, command_logger: run_etf_rotation_backtest(
            command_config,
            command_logger,
        ),
        "build_etf_breadth_price_history": lambda command_args, command_config, command_logger: run_build_etf_breadth_price_history_command(
            command_config,
            command_logger,
        ),
        "adaptive_momentum_backtest": lambda command_args, command_config, command_logger: run_adaptive_momentum_backtest(
            command_config,
            command_logger,
        ),
        "short_hedge_backtest": lambda command_args, command_config, command_logger: run_short_hedge_backtest_command(
            command_config,
            command_logger,
        ),
        "short_strategy_lab": lambda command_args, command_config, command_logger: run_short_strategy_lab_command(
            command_config,
            command_logger,
        ),
        "vol_managed_etf_backtest": lambda command_args, command_config, command_logger: run_vol_managed_etf_backtest_command(
            command_config,
            command_logger,
        ),
        "vol_managed_etf_robustness": lambda command_args, command_config, command_logger: run_vol_managed_etf_robustness_command(
            command_config,
            command_logger,
        ),
        "sma_sensitivity": lambda command_args, command_config, command_logger: run_sma_sensitivity(
            command_config,
            command_logger,
            force_research_universe=command_args.research_universe,
        ),
        "compare_strategies": lambda command_args, command_config, command_logger: run_strategy_comparison(
            command_config,
            command_logger,
            force_research_universe=command_args.research_universe,
        ),
        "backtest": lambda command_args, command_config, command_logger: run_backtest(
            command_config,
            command_logger,
        ),
        "paper_order_test": lambda command_args, command_config, command_logger: run_paper_order_test(
            config=command_config,
            logger=command_logger,
            ticker=command_args.paper_order_test[0],
            side=command_args.paper_order_test[1],
            quantity_text=command_args.paper_order_test[2],
            confirm_paper_order=command_args.confirm_paper_order,
        ),
    }


def run(argv: list[str]) -> int:
    """Run commands that require the configured application runtime."""
    args = parse_args(argv)
    if args.use_paper_positions_readonly and not (args.preview_promoted_actions or args.qqq100_action_preview):
        print("--use-paper-positions-readonly can only be used with --preview-promoted-actions or --qqq100-action-preview.", file=sys.stderr)
        return 2
    pre_config_dispatch = dispatch_pre_config(args)
    if pre_config_dispatch.handled:
        return pre_config_dispatch.exit_code

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
        config_handlers = build_config_handlers()
        config_dispatch = dispatch_config_command(args, config, logger, config_handlers)
        if config_dispatch.handled:
            return config_dispatch.exit_code
        return run_bot(config, logger)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1
