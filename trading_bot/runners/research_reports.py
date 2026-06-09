"""Research report command runners.

These wrappers keep command orchestration out of bot.py while preserving the
underlying saved-data-only report behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from trading_bot.research.crypto_decision import generate_crypto_strategy_decision_report
from trading_bot.research.crypto_monitor import show_crypto_monitor_file
from trading_bot.research.crypto_period_diagnostics import generate_crypto_period_diagnostics
from trading_bot.research.crypto_report import generate_crypto_strategy_report
from trading_bot.research.crypto_state import generate_crypto_research_state_report
from trading_bot.research.defensive_allocation_decision import generate_defensive_allocation_decision_report
from trading_bot.research.defensive_allocation_risk import generate_defensive_allocation_risk_preview
from trading_bot.research.defensive_allocation_preview import generate_defensive_allocation_preview
from trading_bot.research.defensive_comparison import generate_defensive_candidate_comparison
from trading_bot.research.defensive_execution_readiness import generate_defensive_execution_readiness_report
from trading_bot.research.defensive_refresh import refresh_defensive_research
from trading_bot.research.defensive_state import generate_defensive_research_state_report
from trading_bot.research.deployment_readiness import generate_deployment_readiness_report
from trading_bot.research.drawdown_periods import generate_drawdown_period_report
from trading_bot.research.execution_eligibility import generate_execution_eligibility_report
from trading_bot.research.etf_breadth_regime import (
    build_etf_breadth_price_history,
    generate_etf_breadth_regime_backtest,
    generate_etf_breadth_regime_decision_report,
    generate_etf_breadth_regime_robustness_report,
)
from trading_bot.research.etf_defensive_charts import plot_etf_defensive_comparison_charts
from trading_bot.research.etf_defensive_drawdowns import generate_etf_defensive_drawdown_comparison
from trading_bot.research.etf_rotation_robustness import generate_etf_rotation_robustness_report
from trading_bot.research.market_monitor_snapshot import (
    generate_market_monitor_snapshot,
    show_market_monitor_file,
)
from trading_bot.research.paper_kill_switch_gate import generate_paper_kill_switch_gate_report
from trading_bot.research.paper_kill_switch import generate_paper_kill_switch_readiness_report
from trading_bot.research.paper_execution_protection import generate_paper_execution_protection_report
from trading_bot.research.normal_bot_execution_policy import generate_normal_bot_execution_policy_report
from trading_bot.research.portfolio_risk_policy import (
    generate_portfolio_risk_policy_report,
    show_portfolio_risk_policy_file,
)
from trading_bot.research.promoted_decision import show_promoted_decision_file
from trading_bot.research.promoted_actions import show_promoted_actions_file
from trading_bot.research.promoted_risk import show_promoted_risk_file
from trading_bot.research.promoted_review_refresh import PromotedReviewStep, refresh_promoted_review
from trading_bot.research.research_dashboard import build_research_dashboard
from trading_bot.research.short_hedge import run_short_hedge_backtest_files
from trading_bot.research.short_selling_readiness import generate_short_selling_readiness_report
from trading_bot.research.short_strategy_lab import run_short_strategy_lab_files
from trading_bot.research.ticker_universe_readiness import generate_ticker_universe_readiness_report
from trading_bot.research.vol_managed_etf import run_vol_managed_etf_backtest_files
from trading_bot.research.vol_managed_etf_robustness import generate_vol_managed_etf_robustness_report

CommandCallback = Callable[[], int]


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


def run_defensive_research_state_report_command() -> int:
    try:
        result = generate_defensive_research_state_report()
    except Exception as exc:
        print(f"Defensive research state report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_defensive_allocation_preview_command() -> int:
    try:
        result = generate_defensive_allocation_preview()
    except Exception as exc:
        print(f"Defensive allocation preview failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_defensive_allocation_risk_preview_command() -> int:
    try:
        result = generate_defensive_allocation_risk_preview()
    except Exception as exc:
        print(f"Defensive allocation risk preview failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_defensive_allocation_decision_report_command() -> int:
    try:
        result = generate_defensive_allocation_decision_report()
    except Exception as exc:
        print(f"Defensive allocation decision report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_defensive_execution_readiness_report_command() -> int:
    try:
        result = generate_defensive_execution_readiness_report()
    except Exception as exc:
        print(f"Defensive execution readiness report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
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


def run_show_promoted_decision_command() -> int:
    status_code, lines = show_promoted_decision_file(Path("data") / "promoted_decision_preview.csv")
    for line in lines:
        print(line)
    return status_code


def run_show_promoted_actions_command() -> int:
    status_code, lines = show_promoted_actions_file(Path("data") / "promoted_strategy_action_preview.csv")
    for line in lines:
        print(line)
    return status_code


def run_show_promoted_risk_command() -> int:
    status_code, lines = show_promoted_risk_file(Path("data") / "promoted_risk_preview.csv")
    for line in lines:
        print(line)
    return status_code


def run_show_crypto_monitor_command() -> int:
    status_code, lines = show_crypto_monitor_file()
    for line in lines:
        print(line)
    return status_code


def run_crypto_research_state_report_command() -> int:
    try:
        result = generate_crypto_research_state_report()
    except Exception as exc:
        print(f"Crypto research state report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_crypto_strategy_report_command() -> int:
    try:
        result = generate_crypto_strategy_report()
    except Exception as exc:
        print(f"Crypto strategy report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    print(f"Saved crypto strategy report to {result.output_path}")
    return 0


def run_crypto_strategy_decision_report_command() -> int:
    try:
        result = generate_crypto_strategy_decision_report()
    except Exception as exc:
        print(f"Crypto strategy decision report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    print(f"Saved crypto strategy decision report to {result.output_path}")
    return 0


def run_crypto_period_diagnostics_command() -> int:
    try:
        result = generate_crypto_period_diagnostics()
    except Exception as exc:
        print(f"Crypto period diagnostics failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    print(f"Saved crypto period diagnostics to {result.output_path}")
    return 0


def run_portfolio_risk_policy_report_command() -> int:
    try:
        result = generate_portfolio_risk_policy_report()
    except Exception as exc:
        print(f"Portfolio risk policy report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_show_portfolio_risk_policy_command() -> int:
    status_code, lines = show_portfolio_risk_policy_file(Path("data") / "portfolio_risk_policy_report.csv")
    for line in lines:
        print(line)
    return status_code


def run_paper_kill_switch_readiness_report_command() -> int:
    try:
        result = generate_paper_kill_switch_readiness_report()
    except Exception as exc:
        print(f"Paper kill-switch readiness report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_paper_kill_switch_gate_report_command() -> int:
    try:
        result = generate_paper_kill_switch_gate_report()
    except Exception as exc:
        print(f"Paper kill-switch gate report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_paper_execution_protection_report_command() -> int:
    try:
        result = generate_paper_execution_protection_report()
    except Exception as exc:
        print(f"Paper execution protection report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_normal_bot_execution_policy_report_command() -> int:
    try:
        result = generate_normal_bot_execution_policy_report()
    except Exception as exc:
        print(f"Normal bot execution policy report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_execution_eligibility_report_command() -> int:
    try:
        result = generate_execution_eligibility_report()
    except Exception as exc:
        print(f"Execution eligibility report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_ticker_universe_readiness_report_command() -> int:
    try:
        result = generate_ticker_universe_readiness_report()
    except Exception as exc:
        print(f"Ticker universe readiness report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_market_monitor_snapshot_command() -> int:
    try:
        result = generate_market_monitor_snapshot()
    except Exception as exc:
        print(f"Market monitor snapshot failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_show_market_monitor_command() -> int:
    status_code, lines = show_market_monitor_file()
    for line in lines:
        print(line)
    return status_code


def run_build_research_dashboard_command() -> int:
    try:
        result = build_research_dashboard()
    except Exception as exc:
        print(f"Research dashboard build failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_refresh_promoted_review_command(
    run_promoted_strategy_preview: CommandCallback,
    run_promoted_action_preview_readonly: CommandCallback,
    run_promoted_risk_preview: CommandCallback,
    run_promoted_consensus_preview: CommandCallback,
    run_promoted_decision_preview: CommandCallback,
) -> int:
    result = refresh_promoted_review(
        steps=[
            PromotedReviewStep(
                "preview_promoted_strategies",
                "python bot.py --preview-promoted-strategies",
                Path("data") / "promoted_strategy_preview.csv",
                run_promoted_strategy_preview,
            ),
            PromotedReviewStep(
                "preview_promoted_actions_readonly",
                "python bot.py --preview-promoted-actions --use-paper-positions-readonly",
                Path("data") / "promoted_strategy_action_preview.csv",
                run_promoted_action_preview_readonly,
            ),
            PromotedReviewStep(
                "promoted_risk_preview",
                "python bot.py --promoted-risk-preview",
                Path("data") / "promoted_risk_preview.csv",
                run_promoted_risk_preview,
            ),
            PromotedReviewStep(
                "promoted_consensus_preview",
                "python bot.py --promoted-consensus-preview",
                Path("data") / "promoted_consensus_preview.csv",
                run_promoted_consensus_preview,
            ),
            PromotedReviewStep(
                "promoted_decision_preview",
                "python bot.py --promoted-decision-preview",
                Path("data") / "promoted_decision_preview.csv",
                run_promoted_decision_preview,
            ),
            PromotedReviewStep(
                "show_promoted_decision",
                "python bot.py --show-promoted-decision",
                Path("data") / "promoted_decision_preview.csv",
                run_show_promoted_decision_command,
            ),
        ],
        decision_path=Path("data") / "promoted_decision_preview.csv",
        output_path=Path("data") / "promoted_review_refresh_summary.csv",
    )
    for line in result.summary_lines:
        print(line)
    return result.status_code


def run_deployment_readiness_report_command() -> int:
    try:
        result = generate_deployment_readiness_report()
    except Exception as exc:
        print(f"Deployment readiness report failed: {exc}", file=sys.stderr)
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


def run_etf_breadth_regime_backtest_command() -> int:
    try:
        result = generate_etf_breadth_regime_backtest()
    except Exception as exc:
        print(f"ETF breadth regime backtest failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_etf_breadth_regime_decision_report_command() -> int:
    try:
        result = generate_etf_breadth_regime_decision_report()
    except Exception as exc:
        print(f"ETF breadth regime decision report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_etf_breadth_regime_robustness_command() -> int:
    try:
        result = generate_etf_breadth_regime_robustness_report()
    except Exception as exc:
        print(f"ETF breadth regime robustness report failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0


def run_build_etf_breadth_price_history_command(config, logger) -> int:
    try:
        result = build_etf_breadth_price_history(config, logger)
    except Exception as exc:
        print(f"ETF breadth price history builder failed: {exc}", file=sys.stderr)
        return 1
    for line in result.summary_lines:
        print(line)
    return 0
