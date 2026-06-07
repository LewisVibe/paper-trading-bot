"""Research report command runners.

These wrappers keep command orchestration out of bot.py while preserving the
underlying saved-data-only report behavior.
"""

from __future__ import annotations

import sys

from trading_bot.research.defensive_comparison import generate_defensive_candidate_comparison
from trading_bot.research.defensive_refresh import refresh_defensive_research
from trading_bot.research.drawdown_periods import generate_drawdown_period_report
from trading_bot.research.etf_defensive_charts import plot_etf_defensive_comparison_charts
from trading_bot.research.etf_defensive_drawdowns import generate_etf_defensive_drawdown_comparison
from trading_bot.research.etf_rotation_robustness import generate_etf_rotation_robustness_report
from trading_bot.research.short_hedge import run_short_hedge_backtest_files
from trading_bot.research.short_selling_readiness import generate_short_selling_readiness_report
from trading_bot.research.short_strategy_lab import run_short_strategy_lab_files
from trading_bot.research.vol_managed_etf import run_vol_managed_etf_backtest_files
from trading_bot.research.vol_managed_etf_robustness import generate_vol_managed_etf_robustness_report


def run_defensive_candidate_comparison_command() -> int:
    try:
        result = generate_defensive_candidate_comparison()
    except Exception as exc:
        print(f"Defensive candidate comparison failed: {exc}", file=sys.stderr)
        return 1
    for warning in result.warnings:
        print(f"Warning: {warning}")
    for line in result.summary_lines:
        print(line)
    print(f"Saved defensive candidate comparison to {result.output_path}")
    return 0


def run_refresh_defensive_research_command() -> int:
    try:
        result = refresh_defensive_research()
    except Exception as exc:
        print(f"Defensive research refresh failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_drawdown_period_report_command() -> int:
    try:
        result = generate_drawdown_period_report()
    except Exception as exc:
        print(f"Drawdown period report failed: {exc}", file=sys.stderr)
        return 1
    for warning in result.warnings:
        print(f"Warning: {warning}")
    for line in result.summary_lines:
        print(line)
    print(f"Saved drawdown period report to {result.output_path}")
    return 0


def run_etf_defensive_drawdown_comparison_command() -> int:
    try:
        result = generate_etf_defensive_drawdown_comparison()
    except Exception as exc:
        print(f"ETF defensive drawdown comparison failed: {exc}", file=sys.stderr)
        return 1
    for warning in result.warnings:
        print(f"Warning: {warning}")
    for line in result.summary_lines:
        print(line)
    print(f"Saved ETF defensive drawdown comparison to {result.output_path}")
    return 0


def run_plot_etf_defensive_comparison_command() -> int:
    try:
        result = plot_etf_defensive_comparison_charts()
    except Exception as exc:
        print(f"ETF defensive comparison charting failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_short_selling_readiness_report_command() -> int:
    try:
        result = generate_short_selling_readiness_report()
    except Exception as exc:
        print(f"Short-selling readiness report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_short_hedge_backtest_command(config, logger) -> int:
    try:
        result = run_short_hedge_backtest_files(config, logger)
    except Exception as exc:
        print(f"Short hedge backtest failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_short_strategy_lab_command(config, logger) -> int:
    try:
        result = run_short_strategy_lab_files(config, logger)
    except Exception as exc:
        print(f"Short strategy lab failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_vol_managed_etf_backtest_command(config, logger) -> int:
    try:
        result = run_vol_managed_etf_backtest_files(config, logger)
    except Exception as exc:
        print(f"Vol-managed ETF backtest failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_vol_managed_etf_robustness_command(config, logger) -> int:
    try:
        result = generate_vol_managed_etf_robustness_report(config, logger)
    except Exception as exc:
        print(f"Vol-managed ETF robustness report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_etf_rotation_robustness_command() -> int:
    try:
        result = generate_etf_rotation_robustness_report()
    except Exception as exc:
        print(f"ETF rotation robustness report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0
