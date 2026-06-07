from __future__ import annotations

import argparse
import importlib
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKS = [
    ["-m", "py_compile", "bot.py"],
    ["scripts/verify_command_inventory.py"],
    ["scripts/verify_promoted_decision_preview.py"],
    ["scripts/verify_promoted_consensus_preview.py"],
    ["scripts/verify_show_promoted_risk.py"],
    ["scripts/verify_promoted_risk_preview.py"],
    ["scripts/verify_show_promoted_actions.py"],
    ["scripts/verify_promoted_action_preview.py"],
    ["scripts/verify_promoted_strategy_preview.py"],
    ["scripts/verify_strategy_promotion_report.py"],
    ["scripts/verify_etf_rotation_walk_forward.py"],
    ["scripts/verify_walk_forward_report.py"],
    ["scripts/verify_research_report.py"],
    ["scripts/verify_adaptive_strategy.py"],
    ["scripts/verify_breakout_strategy.py"],
    ["scripts/verify_rotation_strategy.py"],
    ["scripts/verify_strategy_registry.py"],
    ["scripts/verify_cost_model.py"],
    ["scripts/verify_position_rules.py"],
    ["bot.py", "--dry-run"],
    ["bot.py", "--backtest"],
    ["bot.py", "--compare-strategies"],
    ["bot.py", "--sma-sensitivity"],
    ["bot.py", "--trend-stress-test"],
    ["bot.py", "--preview-slow-sma-signals"],
    ["bot.py", "--preview-slow-sma-actions"],
    ["bot.py", "--plot-strategy-results"],
]

MODULE_IMPORT_CHECKS = [
    "bot",
    "trading_bot.alpaca_client",
    "trading_bot.config",
    "trading_bot.database",
    "trading_bot.market_data",
    "trading_bot.discord_alerts",
    "trading_bot.execution",
    "trading_bot.logging_setup",
    "trading_bot.output",
    "trading_bot.positions",
    "trading_bot.strategies.adaptive",
    "trading_bot.strategies.breakout",
    "trading_bot.strategies.base",
    "trading_bot.strategies.registry",
    "trading_bot.strategies.rotation",
    "trading_bot.strategies.sma",
    "trading_bot.research.backtesting",
    "trading_bot.research.costs",
    "trading_bot.research.crypto",
    "trading_bot.research.crypto_cost_stress",
    "trading_bot.research.crypto_decision",
    "trading_bot.research.crypto_lab",
    "trading_bot.research.crypto_monitor",
    "trading_bot.research.crypto_period_diagnostics",
    "trading_bot.research.crypto_report",
    "trading_bot.research.crypto_robustness",
    "trading_bot.research.crypto_rotation",
    "trading_bot.research.crypto_signal_preview",
    "trading_bot.research.crypto_state",
    "trading_bot.research.defensive",
    "trading_bot.research.plotting",
    "trading_bot.research.promoted_actions",
    "trading_bot.research.promoted_consensus",
    "trading_bot.research.promoted_decision",
    "trading_bot.research.promoted_preview",
    "trading_bot.research.promoted_risk",
    "trading_bot.research.promotion",
    "trading_bot.research.reporting",
    "trading_bot.research.walk_forward",
]

EXPORT_CHECKS = {
    "trading_bot.alpaca_client": [
        "get_open_orders_for_ticker",
        "normalize_order_side",
        "normalize_order_status",
        "pending_quantity_for_side",
        "refresh_order_status",
        "validate_alpaca_asset_for_order",
    ],
    "trading_bot.config": [
        "load_config",
        "default_research_universe_tickers",
        "AppConfig",
        "ConfigError",
    ],
    "trading_bot.database": [
        "init_database",
        "insert_trade_log",
    ],
    "trading_bot.market_data": [
        "configure_yfinance_cache",
        "download_close_prices",
        "download_backtest_prices",
        "download_slow_sma_preview_prices",
    ],
    "trading_bot.discord_alerts": [
        "send_discord_alert",
    ],
    "trading_bot.execution": [
        "TradeDecision",
        "decide_trade",
    ],
    "trading_bot.logging_setup": [
        "setup_logging",
    ],
    "trading_bot.output": [
        "format_slow_sma_action_preview_error_row",
        "format_slow_sma_action_preview_table_header",
        "format_slow_sma_action_preview_table_row",
        "format_slow_sma_execution_error_row",
        "format_slow_sma_execution_table_header",
        "format_slow_sma_execution_table_row",
        "format_slow_sma_preview_error_row",
        "format_slow_sma_preview_table_header",
        "format_slow_sma_preview_table_row",
    ],
    "trading_bot.positions": [
        "Position",
        "decimal_from_any",
        "format_decimal",
        "get_alpaca_positions",
        "get_simulated_positions",
    ],
    "trading_bot.strategies.base": [
        "ResearchStrategy",
        "StaticResearchStrategy",
        "StrategyMetadata",
    ],
    "trading_bot.strategies.registry": [
        "StrategyRegistry",
        "build_default_strategy_registry",
        "build_strategy_registry",
        "default_strategy_names",
        "get_strategy",
        "list_registered_strategies",
        "register_strategy",
    ],
    "trading_bot.strategies.adaptive": [
        "AdaptiveSelection",
        "adaptive_momentum_score",
        "above_trend_filter",
        "composite_adaptive_momentum",
        "realised_volatility",
        "risk_regime_is_strong",
        "select_adaptive_momentum_assets",
    ],
    "trading_bot.strategies.breakout": [
        "BreakoutSimulationResult",
        "BreakoutTradeEvent",
        "adjusted_breakout_buy_fill",
        "adjusted_breakout_sell_fill",
        "average_true_range",
        "average_volume",
        "atr_trailing_stop_exit",
        "is_252_day_high_breakout",
        "rolling_high",
        "simulate_52_week_high_breakout",
        "simple_moving_average",
        "sma_100_exit",
        "trailing_stop_price",
        "true_range",
        "volume_confirmation",
    ],
    "trading_bot.strategies.rotation": [
        "RotationRebalanceDecision",
        "RotationSelection",
        "above_200_day_sma",
        "buy_and_hold_equity_curve",
        "composite_momentum_score",
        "equal_weight_buy_and_hold_equity_curve",
        "lookback_return",
        "monthly_rebalance_decision",
        "return_21_day",
        "return_63_day",
        "return_126_day",
        "return_252_day",
        "select_top_momentum_etfs",
        "simple_moving_average",
        "should_skip_rebalance_trade",
        "spy_regime_allows_new_positions",
    ],
    "trading_bot.strategies.sma": [
        "detect_sma_signal",
        "calculate_signal",
        "calculate_slow_sma_preview_row",
        "comparison_entry_signal",
        "comparison_exit_signal",
        "prepare_sma_sensitivity_data",
        "prepare_strategy_comparison_data",
        "prepare_trend_stress_test_data",
    ],
    "trading_bot.research.backtesting": [
        "BacktestResult",
        "BacktestTrade",
        "StrategyPortfolioResult",
        "build_comparison_result",
        "build_period_comparison_results",
        "build_strategy_portfolio_results",
        "build_strategy_robustness_summary",
        "format_backtest_result",
        "print_portfolio_summary",
        "print_ranked_strategy_summary",
        "sma_sensitivity_strategy_name",
        "trend_stress_strategy_name",
        "write_backtest_results",
        "write_strategy_comparison_results",
        "write_strategy_comparison_trades",
        "write_strategy_portfolio_comparison",
    ],
    "trading_bot.research.costs": [
        "CostModel",
        "adjusted_buy_fill_price",
        "adjusted_sell_fill_price",
        "calculate_bps_cost",
        "calculate_fixed_commission_cost",
        "calculate_notional_value",
        "calculate_total_estimated_trade_cost",
    ],
    "trading_bot.research.crypto": [
        "CryptoResearchPreviewResult",
        "build_crypto_research_preview_rows",
        "build_crypto_research_preview_summary",
        "run_crypto_research_preview_files",
        "write_crypto_research_preview",
    ],
    "trading_bot.research.crypto_cost_stress": [
        "CryptoCostStressReportResult",
        "build_crypto_cost_stress_rows",
        "build_crypto_cost_stress_summary",
        "classify_stress_status_from_rows",
        "generate_crypto_cost_stress_report",
        "write_crypto_cost_stress_report",
    ],
    "trading_bot.research.crypto_decision": [
        "CryptoStrategyDecisionReportResult",
        "build_crypto_strategy_decision_rows",
        "build_crypto_strategy_decision_summary",
        "classify_crypto_decision",
        "generate_crypto_strategy_decision_report",
        "write_crypto_strategy_decision_report",
    ],
    "trading_bot.research.crypto_lab": [
        "CryptoStrategyLabResult",
        "CryptoResearchCostModel",
        "CRYPTO_STRATEGIES",
        "build_crypto_strategy_lab_outputs",
        "crypto_data_symbol",
        "run_crypto_strategy_lab_files",
        "simulate_crypto_strategy",
    ],
    "trading_bot.research.crypto_monitor": [
        "build_crypto_monitor_lines",
        "build_missing_crypto_monitor_lines",
        "read_csv_rows",
        "show_crypto_monitor_file",
        "summarize_robustness",
    ],
    "trading_bot.research.crypto_period_diagnostics": [
        "CryptoPeriodDiagnosticsResult",
        "build_crypto_period_diagnostic_rows",
        "build_crypto_period_diagnostics_summary",
        "classify_period_diagnostic",
        "generate_crypto_period_diagnostics",
        "write_crypto_period_diagnostics",
    ],
    "trading_bot.research.crypto_report": [
        "CryptoStrategyReportResult",
        "build_crypto_strategy_report_rows",
        "build_crypto_strategy_report_summary",
        "generate_crypto_strategy_report",
        "write_crypto_strategy_report",
    ],
    "trading_bot.research.crypto_robustness": [
        "CryptoRobustnessReportResult",
        "build_crypto_robustness_rows",
        "build_crypto_robustness_summary",
        "classify_crypto_robustness",
        "generate_crypto_robustness_report",
        "write_crypto_robustness_report",
    ],
    "trading_bot.research.crypto_rotation": [
        "CRYPTO_ROTATION_STRATEGY_NAME",
        "build_crypto_rotation_outputs",
        "select_crypto_rotation_asset",
        "simulate_crypto_monthly_btc_eth_momentum_rotation",
        "trailing_return",
    ],
    "trading_bot.research.crypto_signal_preview": [
        "CryptoSignalPreviewResult",
        "build_crypto_signal_preview_row",
        "build_crypto_signal_preview_rows",
        "generate_crypto_signal_preview",
        "write_crypto_signal_preview",
    ],
    "trading_bot.research.crypto_state": [
        "CryptoResearchStateReportResult",
        "build_crypto_research_state_rows",
        "build_crypto_research_state_summary",
        "crypto_research_conclusion",
        "generate_crypto_research_state_report",
        "write_crypto_research_state_report",
    ],
    "trading_bot.research.defensive": [
        "DefensiveStrategyReportResult",
        "build_defensive_strategy_rows",
        "build_defensive_strategy_summary",
        "defensive_score_status_and_reason",
        "generate_defensive_strategy_report",
        "write_defensive_strategy_report",
    ],
    "trading_bot.research.plotting": [
        "load_portfolio_equity_curve_rows",
        "plot_strategy_results",
        "safe_chart_filename",
    ],
    "trading_bot.research.promoted_actions": [
        "PromotedActionPreviewResult",
        "build_missing_promoted_actions_lines",
        "build_promoted_action_preview_rows",
        "build_promoted_action_summary",
        "build_show_promoted_actions_lines",
        "decide_promoted_preview_action",
        "read_promoted_action_preview",
        "read_promoted_strategy_preview",
        "show_promoted_actions_file",
        "write_promoted_action_preview",
    ],
    "trading_bot.research.promoted_consensus": [
        "build_consensus_row",
        "build_promoted_consensus_rows",
        "build_promoted_consensus_summary",
        "classify_consensus_state",
        "run_promoted_consensus_preview_files",
        "write_promoted_consensus_preview",
    ],
    "trading_bot.research.promoted_decision": [
        "build_decision_row",
        "build_promoted_decision_rows",
        "build_promoted_decision_summary",
        "classify_decision_state",
        "run_promoted_decision_preview_files",
        "write_promoted_decision_preview",
    ],
    "trading_bot.research.promoted_preview": [
        "PromotedStrategyPreviewResult",
        "build_promoted_preview_rows",
        "build_promoted_preview_summary",
        "pct_distance",
        "preview_strategy_for_ticker",
        "regime_diagnostics",
        "read_preview_candidates",
        "write_promoted_preview",
    ],
    "trading_bot.research.promoted_risk": [
        "build_action_context",
        "build_missing_promoted_risk_lines",
        "build_promoted_risk_rows",
        "build_promoted_risk_summary",
        "build_show_promoted_risk_lines",
        "run_promoted_risk_preview_files",
        "show_promoted_risk_file",
        "write_promoted_risk_preview",
    ],
    "trading_bot.research.promotion": [
        "StrategyPromotionReportResult",
        "build_strategy_promotion_rows",
        "build_strategy_promotion_summary",
        "classify_promotion_status",
        "generate_strategy_promotion_report",
        "preview_candidate_names",
        "select_research_rows",
        "write_strategy_promotion_report",
    ],
    "trading_bot.research.reporting": [
        "ResearchReportResult",
        "apply_research_ranks",
        "active_decision_rows",
        "active_trade_penalty_note",
        "active_vs_benchmark_warning",
        "apply_benchmark_comparisons",
        "benchmark_decision_rows",
        "best_benchmark_row",
        "build_research_report_summary",
        "classify_report_view",
        "classify_strategy_role",
        "decision_view_rows",
        "generate_research_report",
        "research_conclusion_lines",
        "read_research_file",
        "underperformance_reason",
        "write_research_report",
    ],
    "trading_bot.research.walk_forward": [
        "WalkForwardReportResult",
        "apply_walk_forward_active_ranks",
        "build_walk_forward_rows",
        "build_walk_forward_summary",
        "classify_portfolio_level",
        "classify_robustness",
        "generate_walk_forward_report",
        "walk_forward_view",
        "write_walk_forward_report",
    ],
}


def display_command(args: list[str]) -> str:
    return "python " + " ".join(args)


def redact_secrets(text: str) -> str:
    text = re.sub(
        r"https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/[^\s)\"']+",
        "https://discord.com/api/webhooks/[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"/api/webhooks/[^\s)\"']+",
        "/api/webhooks/[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(api[_-]?key|secret[_-]?key|webhook[_-]?url)(\s*[:=]\s*)[^\s,}]+",
        r"\1\2[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    return text


def tail_output(text: str, max_lines: int = 20) -> str:
    lines = redact_secrets(text).splitlines()
    return "\n".join(lines[-max_lines:])


def run_check(args: list[str], timeout_seconds: int) -> bool:
    command = [PYTHON, *args]
    label = display_command(args)
    print(f"Running: {label}")

    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        print(f"FAILED: {label}")
        print(f"Timed out after {timeout_seconds} seconds.")
        output = (exc.stdout or "") + "\n" + (exc.stderr or "")
        if output.strip():
            print(tail_output(output))
        return False

    if result.returncode == 0:
        print(f"PASS: {label}")
        return True

    print(f"FAILED: {label}")
    print(f"Exit code: {result.returncode}")
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    if output.strip():
        print(tail_output(output))
    return False


def run_import_export_checks() -> bool:
    print("Running: import/export preflight")
    imported_modules = {}

    for module_name in MODULE_IMPORT_CHECKS:
        try:
            imported_modules[module_name] = importlib.import_module(module_name)
        except Exception as exc:
            print(f"FAILED: import {module_name}")
            print(redact_secrets(f"{type(exc).__name__}: {exc}"))
            return False

    for module_name, export_names in EXPORT_CHECKS.items():
        module = imported_modules[module_name]
        for export_name in export_names:
            value = getattr(module, export_name, None)
            if value is None:
                print(f"FAILED: {module_name}.{export_name} missing")
                return False
            if is_constant_export(export_name):
                continue
            if not callable(value):
                print(f"FAILED: {module_name}.{export_name} is not callable")
                return False

    print(
        "PASS: import/export preflight "
        f"({len(MODULE_IMPORT_CHECKS)} modules, "
        f"{sum(len(names) for names in EXPORT_CHECKS.values())} exports)"
    )
    return True


def is_constant_export(export_name: str) -> bool:
    return export_name.isupper()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run safe baseline checks before V2 refactors."
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Per-command timeout. Defaults to 180 seconds.",
    )
    args = parser.parse_args()

    print("V2 baseline verification")
    print("This script does not run paper-order-test or slow SMA paper execution.")
    print("")

    if not run_import_export_checks():
        print("")
        print("Baseline verification failed.")
        return 1
    print("")

    for check in CHECKS:
        if not run_check(check, args.timeout_seconds):
            print("")
            print("Baseline verification failed.")
            return 1
        print("")

    print("Baseline verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
