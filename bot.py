from __future__ import annotations

import csv
import logging
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


if __name__ == "__main__":
    from trading_bot.cli.entrypoint import run

    early_exit_code = run(sys.argv[1:])
    if early_exit_code is not None:
        raise SystemExit(early_exit_code)

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
from trading_bot.cli.parser import parse_args
from trading_bot.config import AppConfig, ConfigError, default_research_universe_tickers, load_config
from trading_bot.database import init_database, insert_trade_log
from trading_bot.discord_alerts import send_discord_alert
from trading_bot.execution import decide_trade, manual_sell_would_oversell
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
from trading_bot.research.crypto import run_crypto_research_preview_files
from trading_bot.research.crypto_universe_readiness import (
    generate_crypto_universe_readiness_report,
    show_crypto_universe_readiness_report_file,
)
from trading_bot.research.expanded_crypto_strategy_lab import (
    generate_expanded_crypto_strategy_lab,
    show_expanded_crypto_strategy_lab_file,
)
from trading_bot.research.expanded_crypto_robustness_report import (
    generate_expanded_crypto_robustness_report,
    show_expanded_crypto_robustness_report_file,
)
from trading_bot.research.crypto_equal_weight_crash_gate import (
    generate_crypto_equal_weight_crash_gate,
    show_crypto_equal_weight_crash_gate_file,
)
from trading_bot.research.crypto_equal_weight_volatility_scaling import (
    generate_crypto_equal_weight_volatility_scaling,
    show_crypto_equal_weight_volatility_scaling_file,
)
from trading_bot.research.crypto_equal_weight_capped_risk_report import (
    generate_crypto_equal_weight_capped_risk_report,
    show_crypto_equal_weight_capped_risk_report_file,
)
from trading_bot.research.expanded_crypto_lead_decision import (
    generate_expanded_crypto_lead_decision,
    show_expanded_crypto_lead_decision_file,
)
from trading_bot.research.crypto_lead_split_sensitivity_diagnosis import (
    generate_crypto_lead_split_sensitivity_diagnosis,
    show_crypto_lead_split_sensitivity_diagnosis_file,
)
from trading_bot.research.expanded_crypto_manual_review_pack import (
    generate_expanded_crypto_manual_review_pack,
    show_expanded_crypto_manual_review_pack_file,
)
from trading_bot.research.qqq_trend_gate_manual_review import (
    generate_qqq_trend_gate_manual_review_pack,
    show_qqq_trend_gate_manual_review_pack,
)
from trading_bot.research.qqq_preview_candidate_readiness import (
    generate_qqq_preview_candidate_readiness_report,
    show_qqq_preview_candidate_readiness_report,
)
from trading_bot.research.qqq100_preview_candidate_readiness_pack import (
    generate_qqq100_preview_candidate_readiness_pack,
    show_qqq100_preview_candidate_readiness_pack,
)
from trading_bot.research.qqq100_preview_signal_pack import (
    generate_qqq100_preview_signal_pack,
    show_qqq100_preview_signal_pack,
)
from trading_bot.research.qqq100_action_preview import (
    generate_qqq100_action_preview,
    show_qqq100_action_preview,
)
from trading_bot.research.multi_strategy_portfolio_preview import (
    generate_multi_strategy_portfolio_preview,
    show_multi_strategy_portfolio_preview,
)
from trading_bot.research.qqq100_paper_readiness_blocker_report import (
    generate_qqq100_paper_readiness_blocker_report,
    show_qqq100_paper_readiness_blocker_report,
)
from trading_bot.research.qqq100_paper_execution_readiness_report import (
    generate_qqq100_paper_execution_readiness_report,
    show_qqq100_paper_execution_readiness_report,
)
from trading_bot.research.paper_live_promotion_gate import (
    generate_paper_live_promotion_gate,
    show_paper_live_promotion_gate,
)
from trading_bot.research.paper_live_readiness_report import (
    generate_paper_live_readiness_report,
    show_paper_live_readiness_report,
)
from trading_bot.research.paper_live_state_summary import (
    generate_paper_live_state_summary,
    show_paper_live_state_summary,
)
from trading_bot.research.paper_live_evidence_audit import (
    generate_paper_live_evidence_audit,
    show_paper_live_evidence_audit,
)
from trading_bot.research.qqq100_postcheck_readiness_report import (
    generate_qqq100_postcheck_readiness_report,
    show_qqq100_postcheck_readiness_report,
)
from trading_bot.research.qqq100_followup_policy_report import (
    generate_qqq100_followup_policy_report,
    show_qqq100_followup_policy_report,
)
from trading_bot.research.qqq100_daily_decision_report import (
    generate_qqq100_daily_decision_report,
    show_qqq100_daily_decision_report,
)
from trading_bot.research.paper_live_monitoring_status import (
    generate_paper_live_monitoring_status,
    show_paper_live_monitoring_status,
)
from trading_bot.research.paper_live_checklist_status import (
    generate_paper_live_checklist_status,
    show_paper_live_checklist_status,
)
from trading_bot.research.paper_live_go_no_go_dashboard import (
    generate_paper_live_go_no_go_dashboard,
    show_paper_live_go_no_go_dashboard,
)
from trading_bot.research.vol_targeted_growth_post_gate_review import (
    generate_vol_targeted_growth_post_gate_review,
    show_vol_targeted_growth_post_gate_review,
)
from trading_bot.research.vol_targeted_growth_manual_ticket_value_design import (
    generate_vol_targeted_growth_manual_ticket_value_design,
    show_vol_targeted_growth_manual_ticket_value_design,
)
from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
    generate_vol_targeted_growth_executable_ticket_approval_readiness,
    generate_vol_targeted_growth_executable_ticket_prerequisites_closeout,
    show_vol_targeted_growth_executable_ticket_approval_readiness,
    show_vol_targeted_growth_executable_ticket_prerequisites_closeout,
)
from trading_bot.research.vol_targeted_growth_executable_ticket_approval_criteria import (
    generate_vol_targeted_growth_executable_ticket_approval_criteria,
    show_vol_targeted_growth_executable_ticket_approval_criteria,
)
from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_resolution_plan import (
    generate_vol_targeted_growth_executable_ticket_criteria_resolution_plan,
    show_vol_targeted_growth_executable_ticket_criteria_resolution_plan,
)
from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_source_review import (
    generate_vol_targeted_growth_executable_ticket_criteria_source_review,
    show_vol_targeted_growth_executable_ticket_criteria_source_review,
)
from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review import (
    generate_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review,
    show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review,
)
from trading_bot.research.vol_targeted_growth_executable_ticket_blocker_specific_reviews import (
    generate_vol_targeted_growth_approval_criteria_not_approval_blocker_review,
    generate_vol_targeted_growth_criteria_blocker_specific_review_rollup,
    generate_vol_targeted_growth_criteria_resolution_plan_blocker_review,
    generate_vol_targeted_growth_criteria_source_blocker_review,
    show_vol_targeted_growth_approval_criteria_not_approval_blocker_review,
    show_vol_targeted_growth_criteria_blocker_specific_review_rollup,
    show_vol_targeted_growth_criteria_resolution_plan_blocker_review,
    show_vol_targeted_growth_criteria_source_blocker_review,
)
from trading_bot.research.vol_targeted_growth_executable_ticket_closeout_candidate_reviews import (
    generate_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review,
    generate_vol_targeted_growth_criteria_closeout_candidate_review_rollup,
    generate_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review,
    generate_vol_targeted_growth_criteria_source_closeout_candidate_review,
    show_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review,
    show_vol_targeted_growth_criteria_closeout_candidate_review_rollup,
    show_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review,
    show_vol_targeted_growth_criteria_source_closeout_candidate_review,
)
from trading_bot.research.paper_live_f6_f7_audit import (
    generate_paper_live_f6_f7_audit,
    show_paper_live_f6_f7_audit,
)
from trading_bot.research.paper_live_promotion_ladder_design import (
    generate_paper_live_promotion_ladder_design,
    show_paper_live_promotion_ladder_design,
)
from trading_bot.research.paper_live_promotion_ladder_status import (
    generate_paper_live_promotion_ladder_status,
    show_paper_live_promotion_ladder_status,
)
from trading_bot.research.paper_live_f7_accounting_proof import (
    generate_paper_live_f7_accounting_proof,
    show_paper_live_f7_accounting_proof,
)
from trading_bot.research.paper_live_next_ladder_candidate_scope import (
    generate_paper_live_next_ladder_candidate_scope,
    show_paper_live_next_ladder_candidate_scope,
)
from trading_bot.research.paper_live_defensive_sleeve_ladder_scope_review import (
    generate_paper_live_defensive_sleeve_ladder_scope_review,
    show_paper_live_defensive_sleeve_ladder_scope_review,
)
from trading_bot.research.paper_live_defensive_sleeve_manual_review import (
    generate_paper_live_defensive_sleeve_manual_review,
    show_paper_live_defensive_sleeve_manual_review,
)
from trading_bot.research.paper_live_defensive_sleeve_preview_readiness import (
    generate_paper_live_defensive_sleeve_preview_readiness,
    show_paper_live_defensive_sleeve_preview_readiness,
)
from trading_bot.research.paper_live_defensive_sleeve_evidence_quality import (
    generate_paper_live_defensive_sleeve_evidence_quality,
    show_paper_live_defensive_sleeve_evidence_quality,
)
from trading_bot.research.paper_live_multi_sleeve_roadmap import (
    generate_paper_live_multi_sleeve_roadmap,
    show_paper_live_multi_sleeve_roadmap,
)
from trading_bot.research.paper_live_next_phase_backlog import (
    generate_paper_live_next_phase_backlog,
    show_paper_live_next_phase_backlog,
)
from trading_bot.research.paper_live_multi_sleeve_evidence_gap import (
    generate_paper_live_multi_sleeve_evidence_gap,
    show_paper_live_multi_sleeve_evidence_gap,
)
from trading_bot.research.paper_live_high_growth_evidence_gap import (
    generate_paper_live_high_growth_evidence_gap,
    show_paper_live_high_growth_evidence_gap,
)
from trading_bot.research.paper_live_high_growth_evidence_quality import (
    generate_paper_live_high_growth_evidence_quality,
    show_paper_live_high_growth_evidence_quality,
)
from trading_bot.research.paper_live_high_growth_manual_review_decision import (
    generate_paper_live_high_growth_manual_review_decision,
    show_paper_live_high_growth_manual_review_decision,
)
from trading_bot.research.qqq100_paper_postcheck import (
    generate_qqq100_paper_postcheck,
    show_qqq100_paper_postcheck,
)
from trading_bot.research.qqq100_repeat_alignment_workflow_design import (
    generate_qqq100_repeat_alignment_workflow_design,
    show_qqq100_repeat_alignment_workflow_design,
)
from trading_bot.research.multi_sleeve_strategy_monitor import (
    generate_multi_sleeve_strategy_monitor,
    show_multi_sleeve_strategy_monitor,
)
from trading_bot.research.sleeve_research_scoreboard import (
    generate_sleeve_research_scoreboard,
    show_sleeve_research_scoreboard,
)
from trading_bot.research.codex_qqq_defensive_crash_gate_research_pack import (
    generate_codex_qqq_defensive_crash_gate_research_pack,
    show_codex_qqq_defensive_crash_gate_research_pack,
)
from trading_bot.research.sleeve_return_streams import (
    generate_sleeve_return_streams,
    show_sleeve_return_streams,
)
from trading_bot.research.multi_sleeve_portfolio_backtest import (
    generate_multi_sleeve_portfolio_backtest,
    show_multi_sleeve_portfolio_backtest,
)
from trading_bot.research.crypto_return_streams import (
    generate_crypto_return_streams,
    show_crypto_return_streams,
)
from trading_bot.research.multi_sleeve_robustness import (
    generate_multi_sleeve_robustness,
    show_multi_sleeve_robustness,
)
from trading_bot.research.multi_sleeve_crypto_review import (
    generate_multi_sleeve_crypto_review,
    show_multi_sleeve_crypto_review,
)
from trading_bot.research.multi_sleeve_crypto_containment import (
    generate_multi_sleeve_crypto_containment_review,
    show_multi_sleeve_crypto_containment_review,
)
from trading_bot.research.multi_sleeve_allocation_policy import (
    generate_multi_sleeve_allocation_policy_review,
    show_multi_sleeve_allocation_policy_review,
)
from trading_bot.research.multi_sleeve_weight_sensitivity import (
    generate_multi_sleeve_weight_sensitivity,
    show_multi_sleeve_weight_sensitivity,
)
from trading_bot.research.multi_sleeve_higher_growth_review import (
    generate_multi_sleeve_higher_growth_review,
    show_multi_sleeve_higher_growth_review,
)
from trading_bot.research.multi_sleeve_research_lead_decision import (
    generate_multi_sleeve_research_lead_decision,
    show_multi_sleeve_research_lead_decision,
)
from trading_bot.research.multi_sleeve_lead_state import (
    generate_multi_sleeve_lead_state,
    show_multi_sleeve_lead_state,
)
from trading_bot.research.multi_sleeve_high_growth_drawdown import (
    generate_multi_sleeve_high_growth_drawdown_decomposition,
    show_multi_sleeve_high_growth_drawdown_decomposition,
)
from trading_bot.research.high_growth_sleeve_quality import (
    generate_high_growth_sleeve_quality_review,
    show_high_growth_sleeve_quality_review,
)
from trading_bot.research.high_growth_component_attribution import (
    generate_high_growth_component_attribution,
    show_high_growth_component_attribution,
)
from trading_bot.research.high_growth_component_streams import (
    generate_high_growth_component_streams,
    show_high_growth_component_streams,
)
from trading_bot.research.high_growth_sleeve_concentration import (
    generate_high_growth_sleeve_concentration_review,
    show_high_growth_sleeve_concentration_review,
)
from trading_bot.research.high_growth_research_checkpoint import (
    generate_high_growth_research_checkpoint,
    show_high_growth_research_checkpoint,
)
from trading_bot.research.paper_execution_state_summary import (
    generate_paper_execution_state_summary,
    show_paper_execution_state_summary,
)
from trading_bot.safety.qqq100_paper_execution import (
    FIXED_QUANTITY as QQQ100_FIXED_QUANTITY,
    TICKER as QQQ100_TICKER,
    evaluate_qqq100_paper_execution_preflight,
    print_qqq100_paper_execution_decision,
    read_saved_qqq100_preview_signal,
    write_qqq100_paper_execution_report,
)
from trading_bot.research.high_growth_stock_lab import (
    generate_high_growth_stock_lab,
    show_high_growth_stock_lab,
)
from trading_bot.research.high_growth_stock_universe_expansion import (
    generate_high_growth_stock_universe_expansion_report,
    show_high_growth_stock_universe_expansion_report,
)
from trading_bot.research.high_growth_stock_drawdown_control import (
    generate_high_growth_stock_drawdown_control_report,
    show_high_growth_stock_drawdown_control_report,
)
from trading_bot.research.high_growth_stock_lead_decision import (
    generate_high_growth_stock_lead_decision_report,
    show_high_growth_stock_lead_decision_report,
)
from trading_bot.research.high_growth_stock_manual_review_pack import (
    generate_high_growth_stock_manual_review_pack,
    show_high_growth_stock_manual_review_pack,
)
from trading_bot.research.high_growth_stock_risk_review_pack import (
    generate_high_growth_stock_risk_review_pack,
    show_high_growth_stock_risk_review_pack,
)
from trading_bot.research.high_growth_stock_risk_evidence_review import (
    generate_high_growth_stock_risk_evidence_review,
    show_high_growth_stock_risk_evidence_review,
)
from trading_bot.research.high_growth_stock_branch_decision_checkpoint import (
    generate_high_growth_stock_branch_decision_checkpoint,
    show_high_growth_stock_branch_decision_checkpoint,
)
from trading_bot.research.high_growth_stock_final_validation_pack import (
    generate_high_growth_stock_final_validation_pack,
    show_high_growth_stock_final_validation_pack,
)
from trading_bot.research.high_growth_strategy_discovery_sprint import (
    generate_high_growth_strategy_discovery_sprint,
    show_high_growth_strategy_discovery_sprint,
)
from trading_bot.research.higher_growth_preview_readiness_pack import (
    generate_higher_growth_preview_readiness_pack,
    show_higher_growth_preview_readiness_pack,
)
from trading_bot.research.higher_growth_candidate_selection_decision import (
    generate_higher_growth_candidate_selection_decision,
    show_higher_growth_candidate_selection_decision,
)
from trading_bot.research.higher_growth_preview_design import (
    generate_higher_growth_preview_design,
    show_higher_growth_preview_design,
)
from trading_bot.research.vol_targeted_growth_research_sprint import (
    generate_vol_targeted_growth_research_sprint,
    show_vol_targeted_growth_research_sprint,
)
from trading_bot.research.vol_targeted_growth_manual_review_pack import (
    generate_vol_targeted_growth_manual_review_pack,
    show_vol_targeted_growth_manual_review_pack,
)
from trading_bot.research.vol_targeted_growth_robustness_checkpoint import (
    generate_vol_targeted_growth_robustness_checkpoint,
    show_vol_targeted_growth_robustness_checkpoint,
)
from trading_bot.research.vol_targeted_growth_nearby_variants_review import (
    generate_vol_targeted_growth_nearby_variants_review,
    show_vol_targeted_growth_nearby_variants_review,
)
from trading_bot.research.vol_targeted_growth_preview_readiness_decision import (
    generate_vol_targeted_growth_preview_readiness_decision,
    show_vol_targeted_growth_preview_readiness_decision,
)
from trading_bot.research.vol_targeted_growth_preview_design import (
    generate_vol_targeted_growth_preview_design,
    show_vol_targeted_growth_preview_design,
)
from trading_bot.research.vol_targeted_growth_preview_signal import (
    generate_vol_targeted_growth_preview_signal,
    show_vol_targeted_growth_preview_signal,
)
from trading_bot.research.vol_targeted_growth_action_preview_design import (
    generate_vol_targeted_growth_action_preview_design,
    show_vol_targeted_growth_action_preview_design,
)
from trading_bot.research.vol_targeted_growth_action_preview import (
    generate_vol_targeted_growth_action_preview,
    show_vol_targeted_growth_action_preview,
)
from trading_bot.research.vol_targeted_growth_broker_position_comparison_design import (
    generate_vol_targeted_growth_broker_position_comparison_design,
    show_vol_targeted_growth_broker_position_comparison_design,
)
from trading_bot.research.vol_targeted_growth_portfolio_risk_review import (
    generate_vol_targeted_growth_portfolio_risk_review,
    show_vol_targeted_growth_portfolio_risk_review,
)
from trading_bot.research.vol_targeted_growth_portfolio_risk_policy_design import (
    generate_vol_targeted_growth_portfolio_risk_policy_design,
    show_vol_targeted_growth_portfolio_risk_policy_design,
)
from trading_bot.research.vol_targeted_growth_paper_live_decision import (
    generate_vol_targeted_growth_paper_live_decision,
    show_vol_targeted_growth_paper_live_decision,
)
from trading_bot.research.vol_targeted_growth_broker_comparison_run_readiness import (
    generate_vol_targeted_growth_broker_comparison_run_readiness,
    show_vol_targeted_growth_broker_comparison_run_readiness,
)
from trading_bot.research.vol_targeted_growth_broker_position_comparison import (
    generate_vol_targeted_growth_broker_position_comparison,
    show_vol_targeted_growth_broker_position_comparison,
)
from trading_bot.research.vol_targeted_growth_post_comparison_decision import (
    generate_vol_targeted_growth_post_comparison_decision,
    show_vol_targeted_growth_post_comparison_decision,
)
from trading_bot.research.vol_targeted_growth_stricter_paper_live_gate_design import (
    generate_vol_targeted_growth_stricter_paper_live_gate_design,
    show_vol_targeted_growth_stricter_paper_live_gate_design,
)
from trading_bot.research.vol_targeted_growth_gate_review import (
    generate_vol_targeted_growth_gate_review,
    show_vol_targeted_growth_gate_review,
)
from trading_bot.research.vol_targeted_growth_candidate_discussion import (
    generate_vol_targeted_growth_candidate_discussion,
    show_vol_targeted_growth_candidate_discussion,
)
from trading_bot.research.vol_targeted_growth_candidate_decision_record import (
    generate_vol_targeted_growth_candidate_decision_record,
    show_vol_targeted_growth_candidate_decision_record,
)
from trading_bot.research.vol_targeted_growth_proposal_implementation_design import (
    generate_vol_targeted_growth_proposal_implementation_design,
    show_vol_targeted_growth_proposal_implementation_design,
)
from trading_bot.research.vol_targeted_growth_proposal_preview_schema import (
    generate_vol_targeted_growth_proposal_preview_schema,
    show_vol_targeted_growth_proposal_preview_schema,
)
from trading_bot.research.vol_targeted_growth_proposal_preview import (
    generate_vol_targeted_growth_proposal_preview,
    show_vol_targeted_growth_proposal_preview,
)
from trading_bot.research.vol_targeted_growth_seed_change_review import (
    generate_vol_targeted_growth_seed_change_review,
    show_vol_targeted_growth_seed_change_review,
)
from trading_bot.research.vol_targeted_growth_seed_change_evidence_pack import (
    generate_vol_targeted_growth_seed_change_evidence_pack,
    show_vol_targeted_growth_seed_change_evidence_pack,
)
from trading_bot.research.vol_targeted_growth_seed_change_risk_reward_comparison import (
    generate_vol_targeted_growth_seed_change_risk_reward_comparison,
    show_vol_targeted_growth_seed_change_risk_reward_comparison,
)
from trading_bot.research.vol_targeted_growth_seed_change_drawdown_stress_review import (
    generate_vol_targeted_growth_seed_change_drawdown_stress_review,
    show_vol_targeted_growth_seed_change_drawdown_stress_review,
)
from trading_bot.research.vol_targeted_growth_seed_change_cost_turnover_review import (
    generate_vol_targeted_growth_seed_change_cost_turnover_review,
    show_vol_targeted_growth_seed_change_cost_turnover_review,
)
from trading_bot.research.vol_targeted_growth_seed_change_split_stability_review import (
    generate_vol_targeted_growth_seed_change_split_stability_review,
    show_vol_targeted_growth_seed_change_split_stability_review,
)
from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
    generate_vol_targeted_growth_seed_change_broker_exposure_review,
    generate_vol_targeted_growth_seed_change_action_preview_design,
    generate_vol_targeted_growth_seed_change_component_sleeve_review,
    generate_vol_targeted_growth_seed_change_proposal_document,
    show_vol_targeted_growth_seed_change_broker_exposure_review,
    show_vol_targeted_growth_seed_change_action_preview_design,
    show_vol_targeted_growth_seed_change_component_sleeve_review,
    show_vol_targeted_growth_seed_change_proposal_document,
)
from trading_bot.research.vol_targeted_growth_seed_change_manual_review_checkpoint import (
    generate_vol_targeted_growth_seed_change_manual_review_checkpoint,
    show_vol_targeted_growth_seed_change_manual_review_checkpoint,
)
from trading_bot.research.vol_targeted_growth_formal_seed_change_proposal import (
    generate_vol_targeted_growth_formal_seed_change_proposal,
    show_vol_targeted_growth_formal_seed_change_proposal,
)
from trading_bot.research.vol_targeted_growth_seed_change_manual_approval_record import (
    generate_vol_targeted_growth_seed_change_manual_approval_record,
    show_vol_targeted_growth_seed_change_manual_approval_record,
)
from trading_bot.research.vol_targeted_growth_seed_change_implementation_design import (
    generate_vol_targeted_growth_seed_change_implementation_design,
    show_vol_targeted_growth_seed_change_implementation_design,
)
from trading_bot.research.vol_targeted_growth_seed_change_dry_run_diff import (
    generate_vol_targeted_growth_seed_change_dry_run_diff,
    show_vol_targeted_growth_seed_change_dry_run_diff,
)
from trading_bot.research.project_research_state_refresh import (
    generate_project_research_state_refresh,
    show_project_research_state_refresh_file,
)
from trading_bot.research.current_research_state import show_current_research_state
from trading_bot.research.project_research_state_quality_report import generate_project_research_state_quality_report
from trading_bot.research.stock_etf_paper_execution_readiness import (
    generate_stock_etf_paper_execution_readiness_report,
)
from trading_bot.research.alpaca_paper_readiness import generate_alpaca_paper_readiness_report
from trading_bot.research.alpaca_connectivity_diagnostics import (
    generate_alpaca_connectivity_diagnostics,
    show_alpaca_connectivity_diagnostics,
)
from trading_bot.research.paper_order_smoke_test_readiness import (
    generate_paper_order_smoke_test_readiness_pack,
)
from trading_bot.research.paper_order_smoke_test_live_preflight import (
    generate_paper_order_smoke_test_live_preflight,
)
from trading_bot.research.paper_order_smoke_test_postcheck import (
    generate_paper_order_smoke_test_postcheck,
)
from trading_bot.research.future_refresh_cron_readiness import generate_future_refresh_cron_readiness_pack
from trading_bot.research.paper_order_smoke_test_runbook_check import (
    generate_paper_order_smoke_test_runbook_check,
)
from trading_bot.research.paper_smoke_test_kill_switch_diagnosis import (
    generate_paper_smoke_test_kill_switch_diagnosis,
    show_paper_smoke_test_kill_switch_diagnosis,
)
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
    append_qqq100_promoted_preview_candidate,
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
from trading_bot.research.codex_ambitious_validation import (
    generate_codex_ambitious_validation,
    show_codex_ambitious_validation_file,
)
from trading_bot.research.codex_ambitious_split_drawdown_validation import (
    generate_codex_ambitious_split_drawdown_validation,
    show_codex_ambitious_split_drawdown_validation_file,
)
from trading_bot.research.codex_ambitious_lead_decision import (
    generate_codex_ambitious_lead_decision,
    show_codex_ambitious_lead_decision_file,
)
from trading_bot.research.walk_forward import generate_walk_forward_report
from trading_bot.runners.backtests import (
    adaptive_momentum_period_slices,
    backtest_ticker,
    build_adaptive_momentum_period_benchmark_metrics,
    build_adaptive_momentum_result_row,
    build_adaptive_momentum_result_rows,
    build_adaptive_momentum_trade_row,
    build_etf_rotation_benchmark_metrics,
    build_etf_rotation_benchmark_metrics_from_curve,
    build_etf_rotation_period_benchmark_metrics,
    build_etf_rotation_result_row,
    build_etf_rotation_result_rows,
    build_etf_rotation_trade_row,
    build_research_equity_metrics,
    compare_breakout_ticker,
    compare_buy_and_hold_ticker,
    compare_sma_pair_ticker,
    compare_strategy_ticker,
    empty_etf_rotation_benchmark_metrics,
    empty_research_metrics,
    etf_rotation_period_slices,
    filter_etf_rotation_trades_for_period,
    get_monthly_rebalance_indices,
    get_strategy_comparison_tickers,
    get_trend_stress_test_universe,
    relative_metric,
    run_adaptive_momentum_backtest,
    run_backtest,
    run_etf_rotation_backtest,
    run_sma_sensitivity,
    run_strategy_comparison,
    run_trend_stress_test,
    write_adaptive_momentum_outputs,
    write_etf_rotation_outputs,
)
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
from trading_bot.safety.manual_paper_smoke_test_gate import (
    RECENT_ORDER_LOOKBACK_MINUTES,
    evaluate_recent_manual_smoke_test_order_match,
    evaluate_manual_paper_smoke_test_gate,
    read_saved_smoke_test_preflight_context,
    write_manual_paper_smoke_test_gate_report,
)
from trading_bot.strategies.sma import (
    SIGNAL_BUY,
    SIGNAL_HOLD,
    SIGNAL_SELL,
    SlowSmaPreviewRow,
    calculate_signal,
    calculate_slow_sma_preview_row,
)



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

    order_status = "monitor_only"
    logger.info(
        "Monitoring only: would %s %s %s share(s) (normal run does not place orders)",
        decision.action,
        format_decimal(decision.trade_quantity),
        ticker,
    )

    insert_trade_log(
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

    send_discord_alert(
        config,
        logger,
        (
            f"Monitoring only: {ticker} would {decision.side.upper()} "
            f"{format_decimal(decision.trade_quantity)} share(s) "
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

        order = submit_alpaca_order(
            alpaca_client,
            QQQ100_TICKER,
            decision.order_side,
            QQQ100_FIXED_QUANTITY,
        )
        order_id = str(getattr(order, "id", ""))
        order_status = normalize_order_status(getattr(order, "status", "submitted"))
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












def main() -> int:
    args = parse_args()
    if args.use_paper_positions_readonly and not (args.preview_promoted_actions or args.qqq100_action_preview):
        print("--use-paper-positions-readonly can only be used with --preview-promoted-actions or --qqq100-action-preview.", file=sys.stderr)
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
    if args.codex_ambitious_validation:
        try:
            result = generate_codex_ambitious_validation()
        except Exception as exc:
            print(f"Codex ambitious validation failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_codex_ambitious_validation:
        status_code, lines = show_codex_ambitious_validation_file()
        for line in lines:
            print(line)
        return status_code
    if args.codex_ambitious_split_drawdown_validation:
        try:
            result = generate_codex_ambitious_split_drawdown_validation()
        except Exception as exc:
            print(f"Codex ambitious split/drawdown validation failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_codex_ambitious_split_drawdown_validation:
        status_code, lines = show_codex_ambitious_split_drawdown_validation_file()
        for line in lines:
            print(line)
        return status_code
    if args.codex_ambitious_lead_decision:
        try:
            result = generate_codex_ambitious_lead_decision()
        except Exception as exc:
            print(f"Codex ambitious lead decision failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_codex_ambitious_lead_decision:
        status_code, lines = show_codex_ambitious_lead_decision_file()
        for line in lines:
            print(line)
        return status_code
    if args.crypto_research_preview:
        result = run_crypto_research_preview_files()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.crypto_universe_readiness_report:
        try:
            result = generate_crypto_universe_readiness_report()
        except Exception as exc:
            print(f"Crypto universe readiness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_crypto_universe_readiness_report:
        status_code, lines = show_crypto_universe_readiness_report_file()
        for line in lines:
            print(line)
        return status_code
    if args.expanded_crypto_strategy_lab:
        try:
            result = generate_expanded_crypto_strategy_lab()
        except Exception as exc:
            print(f"Expanded crypto strategy lab failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_expanded_crypto_strategy_lab:
        status_code, lines = show_expanded_crypto_strategy_lab_file()
        for line in lines:
            print(line)
        return status_code
    if args.expanded_crypto_robustness_report:
        try:
            result = generate_expanded_crypto_robustness_report()
        except Exception as exc:
            print(f"Expanded crypto robustness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_expanded_crypto_robustness_report:
        status_code, lines = show_expanded_crypto_robustness_report_file()
        for line in lines:
            print(line)
        return status_code
    if args.crypto_equal_weight_crash_gate:
        try:
            result = generate_crypto_equal_weight_crash_gate()
        except Exception as exc:
            print(f"Crypto equal-weight crash-gate report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_crypto_equal_weight_crash_gate:
        status_code, lines = show_crypto_equal_weight_crash_gate_file()
        for line in lines:
            print(line)
        return status_code
    if args.crypto_equal_weight_volatility_scaling:
        try:
            result = generate_crypto_equal_weight_volatility_scaling()
        except Exception as exc:
            print(f"Crypto equal-weight volatility-scaling report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_crypto_equal_weight_volatility_scaling:
        status_code, lines = show_crypto_equal_weight_volatility_scaling_file()
        for line in lines:
            print(line)
        return status_code
    if args.crypto_equal_weight_capped_risk_report:
        try:
            result = generate_crypto_equal_weight_capped_risk_report()
        except Exception as exc:
            print(f"Crypto equal-weight capped-risk report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_crypto_equal_weight_capped_risk_report:
        status_code, lines = show_crypto_equal_weight_capped_risk_report_file()
        for line in lines:
            print(line)
        return status_code
    if args.expanded_crypto_lead_decision:
        try:
            result = generate_expanded_crypto_lead_decision()
        except Exception as exc:
            print(f"Expanded crypto lead decision failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_expanded_crypto_lead_decision:
        status_code, lines = show_expanded_crypto_lead_decision_file()
        for line in lines:
            print(line)
        return status_code
    if args.crypto_lead_split_sensitivity_diagnosis:
        try:
            result = generate_crypto_lead_split_sensitivity_diagnosis()
        except Exception as exc:
            print(f"Crypto lead split-sensitivity diagnosis failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_crypto_lead_split_sensitivity_diagnosis:
        status_code, lines = show_crypto_lead_split_sensitivity_diagnosis_file()
        for line in lines:
            print(line)
        return status_code
    if args.expanded_crypto_manual_review_pack:
        try:
            result = generate_expanded_crypto_manual_review_pack()
        except Exception as exc:
            print(f"Expanded crypto manual review pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_expanded_crypto_manual_review_pack:
        status_code, lines = show_expanded_crypto_manual_review_pack_file()
        for line in lines:
            print(line)
        return status_code
    if args.qqq_trend_gate_manual_review_pack:
        try:
            result = generate_qqq_trend_gate_manual_review_pack()
        except Exception as exc:
            print(f"QQQ trend-gate manual review pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq_trend_gate_manual_review_pack:
        status_code, lines = show_qqq_trend_gate_manual_review_pack()
        for line in lines:
            print(line)
        return status_code
    if args.qqq_preview_candidate_readiness_report:
        try:
            result = generate_qqq_preview_candidate_readiness_report()
        except Exception as exc:
            print(f"QQQ preview-candidate readiness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq_preview_candidate_readiness_report:
        status_code, lines = show_qqq_preview_candidate_readiness_report()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_preview_candidate_readiness_pack:
        try:
            result = generate_qqq100_preview_candidate_readiness_pack()
        except Exception as exc:
            print(f"QQQ100 preview-candidate readiness pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_preview_candidate_readiness_pack:
        status_code, lines = show_qqq100_preview_candidate_readiness_pack()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_preview_signal_pack:
        try:
            result = generate_qqq100_preview_signal_pack()
        except Exception as exc:
            print(f"QQQ100 preview signal pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_preview_signal_pack:
        status_code, lines = show_qqq100_preview_signal_pack()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_action_preview:
        try:
            result = generate_qqq100_action_preview(
                use_paper_positions_readonly=args.use_paper_positions_readonly,
                confirm_readonly_alpaca_check=args.confirm_readonly_alpaca_check,
            )
        except Exception as exc:
            print(f"QQQ100 action preview failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_action_preview:
        status_code, lines = show_qqq100_action_preview()
        for line in lines:
            print(line)
        return status_code
    if args.multi_strategy_portfolio_preview:
        try:
            result = generate_multi_strategy_portfolio_preview()
        except Exception as exc:
            print(f"Multi-strategy portfolio preview failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_strategy_portfolio_preview:
        status_code, lines = show_multi_strategy_portfolio_preview()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_paper_readiness_blocker_report:
        try:
            result = generate_qqq100_paper_readiness_blocker_report()
        except Exception as exc:
            print(f"QQQ100 paper-readiness blocker report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_paper_readiness_blocker_report:
        status_code, lines = show_qqq100_paper_readiness_blocker_report()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_paper_execution_readiness_report:
        try:
            result = generate_qqq100_paper_execution_readiness_report()
        except Exception as exc:
            print(f"QQQ100 paper execution readiness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_paper_execution_readiness_report:
        status_code, lines = show_qqq100_paper_execution_readiness_report()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_promotion_gate:
        try:
            result = generate_paper_live_promotion_gate()
        except Exception as exc:
            print(f"Paper-live promotion gate failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_promotion_gate:
        status_code, lines = show_paper_live_promotion_gate()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_readiness_report:
        try:
            result = generate_paper_live_readiness_report()
        except Exception as exc:
            print(f"Paper-live readiness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_readiness_report:
        status_code, lines = show_paper_live_readiness_report()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_state_summary:
        try:
            result = generate_paper_live_state_summary()
        except Exception as exc:
            print(f"Paper-live state summary failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_state_summary:
        status_code, lines = show_paper_live_state_summary()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_evidence_audit:
        try:
            result = generate_paper_live_evidence_audit()
        except Exception as exc:
            print(f"Paper-live evidence audit failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_evidence_audit:
        status_code, lines = show_paper_live_evidence_audit()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_postcheck_readiness_report:
        try:
            result = generate_qqq100_postcheck_readiness_report()
        except Exception as exc:
            print(f"QQQ100 postcheck readiness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_postcheck_readiness_report:
        status_code, lines = show_qqq100_postcheck_readiness_report()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_followup_policy_report:
        try:
            result = generate_qqq100_followup_policy_report()
        except Exception as exc:
            print(f"QQQ100 follow-up policy report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_followup_policy_report:
        status_code, lines = show_qqq100_followup_policy_report()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_daily_decision_report:
        try:
            result = generate_qqq100_daily_decision_report()
        except Exception as exc:
            print(f"QQQ100 daily decision report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_daily_decision_report:
        status_code, lines = show_qqq100_daily_decision_report()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_monitoring_status:
        try:
            result = generate_paper_live_monitoring_status()
        except Exception as exc:
            print(f"Paper-live monitoring status failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_monitoring_status:
        status_code, lines = show_paper_live_monitoring_status()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_checklist_status:
        try:
            result = generate_paper_live_checklist_status()
        except Exception as exc:
            print(f"Paper-live checklist status failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_checklist_status:
        status_code, lines = show_paper_live_checklist_status()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_go_no_go_dashboard:
        try:
            result = generate_paper_live_go_no_go_dashboard()
        except Exception as exc:
            print(f"Paper-live go/no-go dashboard failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_go_no_go_dashboard:
        status_code, lines = show_paper_live_go_no_go_dashboard()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_post_gate_review:
        try:
            result = generate_vol_targeted_growth_post_gate_review()
        except Exception as exc:
            print(f"Volatility-targeted post-gate review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_post_gate_review:
        status_code, lines = show_vol_targeted_growth_post_gate_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_manual_ticket_value_design:
        try:
            result = generate_vol_targeted_growth_manual_ticket_value_design()
        except Exception as exc:
            print(f"Volatility-targeted manual ticket-value design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_manual_ticket_value_design:
        status_code, lines = show_vol_targeted_growth_manual_ticket_value_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_executable_ticket_prerequisites_closeout:
        try:
            result = generate_vol_targeted_growth_executable_ticket_prerequisites_closeout()
        except Exception as exc:
            print(f"Volatility-targeted executable-ticket prerequisites closeout failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_executable_ticket_prerequisites_closeout:
        status_code, lines = show_vol_targeted_growth_executable_ticket_prerequisites_closeout()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_executable_ticket_approval_readiness:
        try:
            result = generate_vol_targeted_growth_executable_ticket_approval_readiness()
        except Exception as exc:
            print(f"Volatility-targeted executable-ticket approval readiness failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_executable_ticket_approval_readiness:
        status_code, lines = show_vol_targeted_growth_executable_ticket_approval_readiness()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_executable_ticket_approval_criteria:
        try:
            result = generate_vol_targeted_growth_executable_ticket_approval_criteria()
        except Exception as exc:
            print(f"Volatility-targeted executable-ticket approval criteria failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_executable_ticket_approval_criteria:
        status_code, lines = show_vol_targeted_growth_executable_ticket_approval_criteria()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_executable_ticket_criteria_resolution_plan:
        try:
            result = generate_vol_targeted_growth_executable_ticket_criteria_resolution_plan()
        except Exception as exc:
            print(f"Volatility-targeted executable-ticket criteria resolution plan failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_executable_ticket_criteria_resolution_plan:
        status_code, lines = show_vol_targeted_growth_executable_ticket_criteria_resolution_plan()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_executable_ticket_criteria_source_review:
        try:
            result = generate_vol_targeted_growth_executable_ticket_criteria_source_review()
        except Exception as exc:
            print(f"Volatility-targeted executable-ticket criteria source review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_executable_ticket_criteria_source_review:
        status_code, lines = show_vol_targeted_growth_executable_ticket_criteria_source_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review:
        try:
            result = generate_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review()
        except Exception as exc:
            print(f"Volatility-targeted executable-ticket criteria blocker closeout review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review:
        status_code, lines = show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_criteria_source_blocker_review:
        result = generate_vol_targeted_growth_criteria_source_blocker_review()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_criteria_source_blocker_review:
        status_code, lines = show_vol_targeted_growth_criteria_source_blocker_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_criteria_resolution_plan_blocker_review:
        result = generate_vol_targeted_growth_criteria_resolution_plan_blocker_review()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_criteria_resolution_plan_blocker_review:
        status_code, lines = show_vol_targeted_growth_criteria_resolution_plan_blocker_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_approval_criteria_not_approval_blocker_review:
        result = generate_vol_targeted_growth_approval_criteria_not_approval_blocker_review()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_approval_criteria_not_approval_blocker_review:
        status_code, lines = show_vol_targeted_growth_approval_criteria_not_approval_blocker_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_criteria_blocker_specific_review_rollup:
        result = generate_vol_targeted_growth_criteria_blocker_specific_review_rollup()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_criteria_blocker_specific_review_rollup:
        status_code, lines = show_vol_targeted_growth_criteria_blocker_specific_review_rollup()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_criteria_source_closeout_candidate_review:
        result = generate_vol_targeted_growth_criteria_source_closeout_candidate_review()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_criteria_source_closeout_candidate_review:
        status_code, lines = show_vol_targeted_growth_criteria_source_closeout_candidate_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review:
        result = generate_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review:
        status_code, lines = show_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review:
        result = generate_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review:
        status_code, lines = show_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_criteria_closeout_candidate_review_rollup:
        result = generate_vol_targeted_growth_criteria_closeout_candidate_review_rollup()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_criteria_closeout_candidate_review_rollup:
        status_code, lines = show_vol_targeted_growth_criteria_closeout_candidate_review_rollup()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_f6_f7_audit:
        try:
            result = generate_paper_live_f6_f7_audit()
        except Exception as exc:
            print(f"Paper-live F6/F7 audit failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_f6_f7_audit:
        status_code, lines = show_paper_live_f6_f7_audit()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_promotion_ladder_design:
        try:
            result = generate_paper_live_promotion_ladder_design()
        except Exception as exc:
            print(f"Paper-live promotion ladder design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_promotion_ladder_design:
        status_code, lines = show_paper_live_promotion_ladder_design()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_promotion_ladder_status:
        try:
            result = generate_paper_live_promotion_ladder_status()
        except Exception as exc:
            print(f"Paper-live promotion ladder status failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_promotion_ladder_status:
        status_code, lines = show_paper_live_promotion_ladder_status()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_f7_accounting_proof:
        try:
            result = generate_paper_live_f7_accounting_proof()
        except Exception as exc:
            print(f"Paper-live F7 accounting proof failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_f7_accounting_proof:
        status_code, lines = show_paper_live_f7_accounting_proof()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_next_ladder_candidate_scope:
        try:
            result = generate_paper_live_next_ladder_candidate_scope()
        except Exception as exc:
            print(f"Paper-live next ladder candidate scope failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_next_ladder_candidate_scope:
        status_code, lines = show_paper_live_next_ladder_candidate_scope()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_defensive_sleeve_ladder_scope_review:
        try:
            result = generate_paper_live_defensive_sleeve_ladder_scope_review()
        except Exception as exc:
            print(f"Paper-live defensive sleeve ladder-scope review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_defensive_sleeve_ladder_scope_review:
        status_code, lines = show_paper_live_defensive_sleeve_ladder_scope_review()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_defensive_sleeve_manual_review:
        try:
            result = generate_paper_live_defensive_sleeve_manual_review()
        except Exception as exc:
            print(f"Paper-live defensive sleeve manual review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_defensive_sleeve_manual_review:
        status_code, lines = show_paper_live_defensive_sleeve_manual_review()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_defensive_sleeve_preview_readiness:
        try:
            result = generate_paper_live_defensive_sleeve_preview_readiness()
        except Exception as exc:
            print(f"Paper-live defensive sleeve preview readiness failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_defensive_sleeve_preview_readiness:
        status_code, lines = show_paper_live_defensive_sleeve_preview_readiness()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_defensive_sleeve_evidence_quality:
        try:
            result = generate_paper_live_defensive_sleeve_evidence_quality()
        except Exception as exc:
            print(f"Paper-live defensive sleeve evidence quality failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_defensive_sleeve_evidence_quality:
        status_code, lines = show_paper_live_defensive_sleeve_evidence_quality()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_multi_sleeve_roadmap:
        try:
            result = generate_paper_live_multi_sleeve_roadmap()
        except Exception as exc:
            print(f"Paper-live multi-sleeve roadmap failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_multi_sleeve_roadmap:
        status_code, lines = show_paper_live_multi_sleeve_roadmap()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_next_phase_backlog:
        try:
            result = generate_paper_live_next_phase_backlog()
        except Exception as exc:
            print(f"Paper-live next-phase backlog failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_next_phase_backlog:
        status_code, lines = show_paper_live_next_phase_backlog()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_multi_sleeve_evidence_gap:
        try:
            result = generate_paper_live_multi_sleeve_evidence_gap()
        except Exception as exc:
            print(f"Paper-live multi-sleeve evidence-gap audit failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_multi_sleeve_evidence_gap:
        status_code, lines = show_paper_live_multi_sleeve_evidence_gap()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_high_growth_evidence_gap:
        try:
            result = generate_paper_live_high_growth_evidence_gap()
        except Exception as exc:
            print(f"Paper-live high-growth evidence-gap audit failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_high_growth_evidence_gap:
        status_code, lines = show_paper_live_high_growth_evidence_gap()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_high_growth_evidence_quality:
        try:
            result = generate_paper_live_high_growth_evidence_quality()
        except Exception as exc:
            print(f"Paper-live high-growth evidence quality review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_high_growth_evidence_quality:
        status_code, lines = show_paper_live_high_growth_evidence_quality()
        for line in lines:
            print(line)
        return status_code
    if args.paper_live_high_growth_manual_review_decision:
        try:
            result = generate_paper_live_high_growth_manual_review_decision()
        except Exception as exc:
            print(f"Paper-live high-growth manual-review decision failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_live_high_growth_manual_review_decision:
        status_code, lines = show_paper_live_high_growth_manual_review_decision()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_paper_postcheck:
        try:
            result = generate_qqq100_paper_postcheck(
                confirm_readonly_alpaca_check=args.confirm_readonly_alpaca_check
            )
        except Exception as exc:
            print(f"QQQ100 paper postcheck failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_paper_postcheck:
        status_code, lines = show_qqq100_paper_postcheck()
        for line in lines:
            print(line)
        return status_code
    if args.qqq100_repeat_alignment_workflow_design:
        try:
            result = generate_qqq100_repeat_alignment_workflow_design()
        except Exception as exc:
            print(f"QQQ100 repeat/alignment workflow design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_qqq100_repeat_alignment_workflow_design:
        status_code, lines = show_qqq100_repeat_alignment_workflow_design()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_strategy_monitor:
        try:
            result = generate_multi_sleeve_strategy_monitor()
        except Exception as exc:
            print(f"Multi-sleeve strategy monitor failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_strategy_monitor:
        status_code, lines = show_multi_sleeve_strategy_monitor()
        for line in lines:
            print(line)
        return status_code
    if args.sleeve_research_scoreboard:
        try:
            result = generate_sleeve_research_scoreboard()
        except Exception as exc:
            print(f"Sleeve research scoreboard failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_sleeve_research_scoreboard:
        status_code, lines = show_sleeve_research_scoreboard()
        for line in lines:
            print(line)
        return status_code
    if args.codex_qqq_defensive_crash_gate_research_pack:
        try:
            result = generate_codex_qqq_defensive_crash_gate_research_pack()
        except Exception as exc:
            print(f"Codex QQQ defensive crash-gate research pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_codex_qqq_defensive_crash_gate_research_pack:
        status_code, lines = show_codex_qqq_defensive_crash_gate_research_pack()
        for line in lines:
            print(line)
        return status_code
    if args.sleeve_return_streams:
        try:
            result = generate_sleeve_return_streams()
        except Exception as exc:
            print(f"Sleeve return streams failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_sleeve_return_streams:
        status_code, lines = show_sleeve_return_streams()
        for line in lines:
            print(line)
        return status_code
    if args.crypto_return_streams:
        try:
            result = generate_crypto_return_streams()
        except Exception as exc:
            print(f"Crypto return streams failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_crypto_return_streams:
        status_code, lines = show_crypto_return_streams()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_portfolio_backtest:
        try:
            result = generate_multi_sleeve_portfolio_backtest()
        except Exception as exc:
            print(f"Multi-sleeve portfolio backtest failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_portfolio_backtest:
        status_code, lines = show_multi_sleeve_portfolio_backtest()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_robustness:
        try:
            result = generate_multi_sleeve_robustness()
        except Exception as exc:
            print(f"Multi-sleeve robustness failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_robustness:
        status_code, lines = show_multi_sleeve_robustness()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_crypto_review:
        try:
            result = generate_multi_sleeve_crypto_review()
        except Exception as exc:
            print(f"Multi-sleeve crypto review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_crypto_review:
        status_code, lines = show_multi_sleeve_crypto_review()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_crypto_containment_review:
        try:
            result = generate_multi_sleeve_crypto_containment_review()
        except Exception as exc:
            print(f"Multi-sleeve crypto containment review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_crypto_containment_review:
        status_code, lines = show_multi_sleeve_crypto_containment_review()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_allocation_policy_review:
        try:
            result = generate_multi_sleeve_allocation_policy_review()
        except Exception as exc:
            print(f"Multi-sleeve allocation policy review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_allocation_policy_review:
        status_code, lines = show_multi_sleeve_allocation_policy_review()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_weight_sensitivity:
        try:
            result = generate_multi_sleeve_weight_sensitivity()
        except Exception as exc:
            print(f"Multi-sleeve weight sensitivity failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_weight_sensitivity:
        status_code, lines = show_multi_sleeve_weight_sensitivity()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_higher_growth_review:
        try:
            result = generate_multi_sleeve_higher_growth_review()
        except Exception as exc:
            print(f"Multi-sleeve higher-growth review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_higher_growth_review:
        status_code, lines = show_multi_sleeve_higher_growth_review()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_research_lead_decision:
        try:
            result = generate_multi_sleeve_research_lead_decision()
        except Exception as exc:
            print(f"Multi-sleeve research lead decision failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_research_lead_decision:
        status_code, lines = show_multi_sleeve_research_lead_decision()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_lead_state_refresh:
        try:
            result = generate_multi_sleeve_lead_state()
        except Exception as exc:
            print(f"Multi-sleeve lead state refresh failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_lead_state:
        status_code, lines = show_multi_sleeve_lead_state()
        for line in lines:
            print(line)
        return status_code
    if args.multi_sleeve_high_growth_drawdown_decomposition:
        try:
            result = generate_multi_sleeve_high_growth_drawdown_decomposition()
        except Exception as exc:
            print(f"Multi-sleeve high-growth drawdown decomposition failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_multi_sleeve_high_growth_drawdown_decomposition:
        status_code, lines = show_multi_sleeve_high_growth_drawdown_decomposition()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_sleeve_quality_review:
        try:
            result = generate_high_growth_sleeve_quality_review()
        except Exception as exc:
            print(f"High-growth sleeve quality review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_sleeve_quality_review:
        status_code, lines = show_high_growth_sleeve_quality_review()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_component_attribution:
        try:
            result = generate_high_growth_component_attribution()
        except Exception as exc:
            print(f"High-growth component attribution failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_component_attribution:
        status_code, lines = show_high_growth_component_attribution()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_component_streams:
        try:
            result = generate_high_growth_component_streams()
        except Exception as exc:
            print(f"High-growth component streams failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_component_streams:
        status_code, lines = show_high_growth_component_streams()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_sleeve_concentration_review:
        try:
            result = generate_high_growth_sleeve_concentration_review()
        except Exception as exc:
            print(f"High-growth sleeve concentration review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_sleeve_concentration_review:
        status_code, lines = show_high_growth_sleeve_concentration_review()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_research_checkpoint:
        try:
            result = generate_high_growth_research_checkpoint()
        except Exception as exc:
            print(f"High-growth research checkpoint failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_research_checkpoint:
        status_code, lines = show_high_growth_research_checkpoint()
        for line in lines:
            print(line)
        return status_code
    if args.paper_execution_state_summary:
        try:
            result = generate_paper_execution_state_summary()
        except Exception as exc:
            print(f"Paper execution state summary failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_execution_state_summary:
        status_code, lines = show_paper_execution_state_summary()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_lab:
        try:
            result = generate_high_growth_stock_lab()
        except Exception as exc:
            print(f"High-growth stock lab failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_lab:
        status_code, lines = show_high_growth_stock_lab()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_universe_expansion_report:
        try:
            result = generate_high_growth_stock_universe_expansion_report()
        except Exception as exc:
            print(f"High-growth stock universe expansion report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_universe_expansion_report:
        status_code, lines = show_high_growth_stock_universe_expansion_report()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_drawdown_control_report:
        try:
            result = generate_high_growth_stock_drawdown_control_report()
        except Exception as exc:
            print(f"High-growth stock drawdown-control report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_drawdown_control_report:
        status_code, lines = show_high_growth_stock_drawdown_control_report()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_lead_decision_report:
        try:
            result = generate_high_growth_stock_lead_decision_report()
        except Exception as exc:
            print(f"High-growth stock lead decision report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_lead_decision_report:
        status_code, lines = show_high_growth_stock_lead_decision_report()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_manual_review_pack:
        try:
            result = generate_high_growth_stock_manual_review_pack()
        except Exception as exc:
            print(f"High-growth stock manual review pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_manual_review_pack:
        status_code, lines = show_high_growth_stock_manual_review_pack()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_risk_review_pack:
        try:
            result = generate_high_growth_stock_risk_review_pack()
        except Exception as exc:
            print(f"High-growth stock risk review pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_risk_review_pack:
        status_code, lines = show_high_growth_stock_risk_review_pack()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_risk_evidence_review:
        try:
            result = generate_high_growth_stock_risk_evidence_review()
        except Exception as exc:
            print(f"High-growth stock risk evidence review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_risk_evidence_review:
        status_code, lines = show_high_growth_stock_risk_evidence_review()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_branch_decision_checkpoint:
        try:
            result = generate_high_growth_stock_branch_decision_checkpoint()
        except Exception as exc:
            print(f"High-growth stock branch decision checkpoint failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_branch_decision_checkpoint:
        status_code, lines = show_high_growth_stock_branch_decision_checkpoint()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_stock_final_validation_pack:
        try:
            result = generate_high_growth_stock_final_validation_pack()
        except Exception as exc:
            print(f"High-growth stock final validation pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_stock_final_validation_pack:
        status_code, lines = show_high_growth_stock_final_validation_pack()
        for line in lines:
            print(line)
        return status_code
    if args.high_growth_strategy_discovery_sprint:
        try:
            result = generate_high_growth_strategy_discovery_sprint()
        except Exception as exc:
            print(f"High-growth strategy discovery sprint failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_high_growth_strategy_discovery_sprint:
        status_code, lines = show_high_growth_strategy_discovery_sprint()
        for line in lines:
            print(line)
        return status_code
    if args.higher_growth_preview_readiness_pack:
        try:
            result = generate_higher_growth_preview_readiness_pack()
        except Exception as exc:
            print(f"Higher-growth preview readiness pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_higher_growth_preview_readiness_pack:
        status_code, lines = show_higher_growth_preview_readiness_pack()
        for line in lines:
            print(line)
        return status_code
    if args.higher_growth_candidate_selection_decision:
        try:
            result = generate_higher_growth_candidate_selection_decision()
        except Exception as exc:
            print(f"Higher-growth candidate selection decision failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_higher_growth_candidate_selection_decision:
        status_code, lines = show_higher_growth_candidate_selection_decision()
        for line in lines:
            print(line)
        return status_code
    if args.higher_growth_preview_design:
        try:
            result = generate_higher_growth_preview_design()
        except Exception as exc:
            print(f"Higher-growth preview design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_higher_growth_preview_design:
        status_code, lines = show_higher_growth_preview_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_research_sprint:
        try:
            result = generate_vol_targeted_growth_research_sprint()
        except Exception as exc:
            print(f"Volatility-targeted growth research sprint failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_research_sprint:
        status_code, lines = show_vol_targeted_growth_research_sprint()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_manual_review_pack:
        try:
            result = generate_vol_targeted_growth_manual_review_pack()
        except Exception as exc:
            print(f"Volatility-targeted growth manual review pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_manual_review_pack:
        status_code, lines = show_vol_targeted_growth_manual_review_pack()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_robustness_checkpoint:
        try:
            result = generate_vol_targeted_growth_robustness_checkpoint()
        except Exception as exc:
            print(f"Volatility-targeted growth robustness checkpoint failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_robustness_checkpoint:
        status_code, lines = show_vol_targeted_growth_robustness_checkpoint()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_nearby_variants_review:
        try:
            result = generate_vol_targeted_growth_nearby_variants_review()
        except Exception as exc:
            print(f"Volatility-targeted growth nearby-variants review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_nearby_variants_review:
        status_code, lines = show_vol_targeted_growth_nearby_variants_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_preview_readiness_decision:
        try:
            result = generate_vol_targeted_growth_preview_readiness_decision()
        except Exception as exc:
            print(f"Volatility-targeted growth preview-readiness decision failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_preview_readiness_decision:
        status_code, lines = show_vol_targeted_growth_preview_readiness_decision()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_preview_design:
        try:
            result = generate_vol_targeted_growth_preview_design()
        except Exception as exc:
            print(f"Volatility-targeted growth preview design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_preview_design:
        status_code, lines = show_vol_targeted_growth_preview_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_preview_signal:
        try:
            result = generate_vol_targeted_growth_preview_signal()
        except Exception as exc:
            print(f"Volatility-targeted growth preview signal failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_preview_signal:
        status_code, lines = show_vol_targeted_growth_preview_signal()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_action_preview_design:
        try:
            result = generate_vol_targeted_growth_action_preview_design()
        except Exception as exc:
            print(f"Volatility-targeted growth action-preview design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_action_preview_design:
        status_code, lines = show_vol_targeted_growth_action_preview_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_action_preview:
        try:
            result = generate_vol_targeted_growth_action_preview()
        except Exception as exc:
            print(f"Volatility-targeted growth action preview failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_action_preview:
        status_code, lines = show_vol_targeted_growth_action_preview()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_broker_position_comparison_design:
        try:
            result = generate_vol_targeted_growth_broker_position_comparison_design()
        except Exception as exc:
            print(f"Volatility-targeted growth broker-position comparison design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_broker_position_comparison_design:
        status_code, lines = show_vol_targeted_growth_broker_position_comparison_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_portfolio_risk_review:
        try:
            result = generate_vol_targeted_growth_portfolio_risk_review()
        except Exception as exc:
            print(f"Volatility-targeted growth portfolio-risk review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_portfolio_risk_review:
        status_code, lines = show_vol_targeted_growth_portfolio_risk_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_portfolio_risk_policy_design:
        try:
            result = generate_vol_targeted_growth_portfolio_risk_policy_design()
        except Exception as exc:
            print(f"Volatility-targeted growth portfolio-risk policy design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_portfolio_risk_policy_design:
        status_code, lines = show_vol_targeted_growth_portfolio_risk_policy_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_paper_live_decision:
        try:
            result = generate_vol_targeted_growth_paper_live_decision()
        except Exception as exc:
            print(f"Volatility-targeted growth paper-live decision failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_paper_live_decision:
        status_code, lines = show_vol_targeted_growth_paper_live_decision()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_broker_comparison_run_readiness:
        try:
            result = generate_vol_targeted_growth_broker_comparison_run_readiness()
        except Exception as exc:
            print(f"Volatility-targeted growth broker-comparison run-readiness failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_broker_comparison_run_readiness:
        status_code, lines = show_vol_targeted_growth_broker_comparison_run_readiness()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_broker_position_comparison:
        try:
            result = generate_vol_targeted_growth_broker_position_comparison(
                confirm_readonly_alpaca_check=args.confirm_readonly_alpaca_check
            )
        except Exception as exc:
            print(f"Volatility-targeted growth broker-position comparison failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_broker_position_comparison:
        status_code, lines = show_vol_targeted_growth_broker_position_comparison()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_post_comparison_decision:
        try:
            result = generate_vol_targeted_growth_post_comparison_decision()
        except Exception as exc:
            print(f"Volatility-targeted growth post-comparison decision failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_post_comparison_decision:
        status_code, lines = show_vol_targeted_growth_post_comparison_decision()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_stricter_paper_live_gate_design:
        try:
            result = generate_vol_targeted_growth_stricter_paper_live_gate_design()
        except Exception as exc:
            print(f"Volatility-targeted growth stricter paper-live gate design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_stricter_paper_live_gate_design:
        status_code, lines = show_vol_targeted_growth_stricter_paper_live_gate_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_gate_review:
        try:
            result = generate_vol_targeted_growth_gate_review()
        except Exception as exc:
            print(f"Volatility-targeted growth gate review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_gate_review:
        status_code, lines = show_vol_targeted_growth_gate_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_candidate_decision_record:
        try:
            result = generate_vol_targeted_growth_candidate_decision_record()
        except Exception as exc:
            print(f"Volatility-targeted growth candidate decision record failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_candidate_decision_record:
        status_code, lines = show_vol_targeted_growth_candidate_decision_record()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_candidate_discussion:
        try:
            result = generate_vol_targeted_growth_candidate_discussion()
        except Exception as exc:
            print(f"Volatility-targeted growth candidate discussion failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_candidate_discussion:
        status_code, lines = show_vol_targeted_growth_candidate_discussion()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_proposal_implementation_design:
        try:
            result = generate_vol_targeted_growth_proposal_implementation_design()
        except Exception as exc:
            print(f"Volatility-targeted growth proposal implementation design failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_proposal_implementation_design:
        status_code, lines = show_vol_targeted_growth_proposal_implementation_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_proposal_preview_schema:
        try:
            result = generate_vol_targeted_growth_proposal_preview_schema()
        except Exception as exc:
            print(f"Volatility-targeted growth proposal preview schema failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_proposal_preview_schema:
        status_code, lines = show_vol_targeted_growth_proposal_preview_schema()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_proposal_preview:
        try:
            result = generate_vol_targeted_growth_proposal_preview()
        except Exception as exc:
            print(f"Volatility-targeted growth proposal preview failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_proposal_preview:
        status_code, lines = show_vol_targeted_growth_proposal_preview()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_review:
        try:
            result = generate_vol_targeted_growth_seed_change_review()
        except Exception as exc:
            print(f"Volatility-targeted growth seed-change review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_review:
        status_code, lines = show_vol_targeted_growth_seed_change_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_evidence_pack:
        try:
            result = generate_vol_targeted_growth_seed_change_evidence_pack()
        except Exception as exc:
            print(f"Volatility-targeted growth seed-change evidence pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_evidence_pack:
        status_code, lines = show_vol_targeted_growth_seed_change_evidence_pack()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_risk_reward_comparison:
        try:
            result = generate_vol_targeted_growth_seed_change_risk_reward_comparison()
        except Exception as exc:
            print(f"Volatility-targeted growth seed-change risk/reward comparison failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_risk_reward_comparison:
        status_code, lines = show_vol_targeted_growth_seed_change_risk_reward_comparison()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_drawdown_stress_review:
        try:
            result = generate_vol_targeted_growth_seed_change_drawdown_stress_review()
        except Exception as exc:
            print(f"Volatility-targeted growth seed-change drawdown/stress review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_drawdown_stress_review:
        status_code, lines = show_vol_targeted_growth_seed_change_drawdown_stress_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_cost_turnover_review:
        try:
            result = generate_vol_targeted_growth_seed_change_cost_turnover_review()
        except Exception as exc:
            print(f"Volatility-targeted growth seed-change cost/turnover review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_cost_turnover_review:
        status_code, lines = show_vol_targeted_growth_seed_change_cost_turnover_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_split_stability_review:
        try:
            result = generate_vol_targeted_growth_seed_change_split_stability_review()
        except Exception as exc:
            print(f"Volatility-targeted growth seed-change split-stability review failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_split_stability_review:
        status_code, lines = show_vol_targeted_growth_seed_change_split_stability_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_component_sleeve_review:
        result = generate_vol_targeted_growth_seed_change_component_sleeve_review()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_component_sleeve_review:
        status_code, lines = show_vol_targeted_growth_seed_change_component_sleeve_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_action_preview_design:
        result = generate_vol_targeted_growth_seed_change_action_preview_design()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_action_preview_design:
        status_code, lines = show_vol_targeted_growth_seed_change_action_preview_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_proposal_document:
        result = generate_vol_targeted_growth_seed_change_proposal_document()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_proposal_document:
        status_code, lines = show_vol_targeted_growth_seed_change_proposal_document()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_broker_exposure_review:
        result = generate_vol_targeted_growth_seed_change_broker_exposure_review()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_broker_exposure_review:
        status_code, lines = show_vol_targeted_growth_seed_change_broker_exposure_review()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_manual_review_checkpoint:
        result = generate_vol_targeted_growth_seed_change_manual_review_checkpoint()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_manual_review_checkpoint:
        status_code, lines = show_vol_targeted_growth_seed_change_manual_review_checkpoint()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_formal_seed_change_proposal:
        result = generate_vol_targeted_growth_formal_seed_change_proposal()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_formal_seed_change_proposal:
        status_code, lines = show_vol_targeted_growth_formal_seed_change_proposal()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_manual_approval_record:
        result = generate_vol_targeted_growth_seed_change_manual_approval_record()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_manual_approval_record:
        status_code, lines = show_vol_targeted_growth_seed_change_manual_approval_record()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_implementation_design:
        result = generate_vol_targeted_growth_seed_change_implementation_design()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_implementation_design:
        status_code, lines = show_vol_targeted_growth_seed_change_implementation_design()
        for line in lines:
            print(line)
        return status_code
    if args.vol_targeted_growth_seed_change_dry_run_diff:
        result = generate_vol_targeted_growth_seed_change_dry_run_diff()
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_vol_targeted_growth_seed_change_dry_run_diff:
        status_code, lines = show_vol_targeted_growth_seed_change_dry_run_diff()
        for line in lines:
            print(line)
        return status_code
    if args.project_research_state_refresh:
        try:
            result = generate_project_research_state_refresh()
        except Exception as exc:
            print(f"Project research state refresh failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_project_research_state_refresh:
        status_code, lines = show_project_research_state_refresh_file()
        for line in lines:
            print(line)
        return status_code
    if args.show_current_research_state:
        status_code, lines = show_current_research_state()
        for line in lines:
            print(line)
        return status_code
    if args.project_research_state_quality_report:
        try:
            result = generate_project_research_state_quality_report()
        except Exception as exc:
            print(f"Project research-state quality report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.stock_etf_paper_execution_readiness_report:
        try:
            result = generate_stock_etf_paper_execution_readiness_report()
        except Exception as exc:
            print(f"Stock/ETF paper execution readiness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.alpaca_paper_readiness_report:
        try:
            result = generate_alpaca_paper_readiness_report(
                confirm_readonly_alpaca_check=args.confirm_readonly_alpaca_check
            )
        except Exception as exc:
            print(f"Alpaca paper readiness report failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.alpaca_connectivity_diagnostics:
        try:
            result = generate_alpaca_connectivity_diagnostics()
        except Exception as exc:
            print(f"Alpaca connectivity diagnostics failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_alpaca_connectivity_diagnostics:
        status_code, lines = show_alpaca_connectivity_diagnostics()
        for line in lines:
            print(line)
        return status_code
    if args.paper_order_smoke_test_readiness_pack:
        try:
            result = generate_paper_order_smoke_test_readiness_pack()
        except Exception as exc:
            print(f"Paper-order smoke-test readiness pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.paper_order_smoke_test_live_preflight:
        try:
            result = generate_paper_order_smoke_test_live_preflight(
                ticker=args.ticker,
                side=args.side,
                quantity=args.quantity,
                confirm_readonly_alpaca_check=args.confirm_readonly_alpaca_check,
            )
        except Exception as exc:
            print(f"Paper-order smoke-test live preflight failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.paper_order_smoke_test_postcheck:
        try:
            result = generate_paper_order_smoke_test_postcheck(
                ticker=args.ticker,
                side=args.side,
                quantity=args.quantity,
                confirm_readonly_alpaca_check=args.confirm_readonly_alpaca_check,
            )
        except Exception as exc:
            print(f"Paper-order smoke-test postcheck failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.future_refresh_cron_readiness_pack:
        try:
            result = generate_future_refresh_cron_readiness_pack()
        except Exception as exc:
            print(f"Future refresh cron readiness pack failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.paper_order_smoke_test_runbook_check:
        try:
            result = generate_paper_order_smoke_test_runbook_check()
        except Exception as exc:
            print(f"Paper-order smoke-test runbook check failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.paper_smoke_test_kill_switch_diagnosis:
        try:
            result = generate_paper_smoke_test_kill_switch_diagnosis()
        except Exception as exc:
            print(f"Paper smoke-test kill-switch diagnosis failed: {exc}", file=sys.stderr)
            return 1
        for line in result.summary_lines:
            print(line)
        return 0
    if args.show_paper_smoke_test_kill_switch_diagnosis:
        status_code, lines = show_paper_smoke_test_kill_switch_diagnosis()
        for line in lines:
            print(line)
        return status_code
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
        if args.execute_qqq100_paper:
            return run_execute_qqq100_paper(
                config=config,
                logger=logger,
                confirm_qqq100_paper=args.confirm_qqq100_paper,
            )
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
