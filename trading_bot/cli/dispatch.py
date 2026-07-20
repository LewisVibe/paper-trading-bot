"""Ordered, auditable command descriptors for the compatibility CLI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping

from trading_bot.cli.report_only import dispatch_early_command


class SideEffect(str, Enum):
    REPORT_ONLY = "report_only"
    RESEARCH = "research"
    MARKET_DATA = "market_data"
    NETWORK_DIAGNOSTIC = "network_diagnostic"
    BROKER_READ = "broker_read"
    PAPER_EXECUTION = "paper_execution"


@dataclass(frozen=True)
class ForwardedArgument:
    source: str
    option: str
    takes_value: bool = False


@dataclass(frozen=True)
class CommandDescriptor:
    dest: str
    side_effect: SideEffect
    handler: str | None = None
    forwarded: tuple[ForwardedArgument, ...] = ()

    @property
    def option(self) -> str:
        return "--" + self.dest.replace("_", "-")


@dataclass(frozen=True)
class DispatchResult:
    handled: bool
    exit_code: int | None = None
    descriptor: CommandDescriptor | None = None


READONLY_CONFIRM = (
    ForwardedArgument("confirm_readonly_alpaca_check", "--confirm-readonly-alpaca-check"),
)
SAVED_SNAPSHOT_CONFIRM = (
    ForwardedArgument("confirm_saved_price_snapshot_run", "--confirm-saved-price-snapshot-run"),
)
SMOKE_TEST_CONTEXT = (
    ForwardedArgument("ticker", "--ticker", takes_value=True),
    ForwardedArgument("side", "--side", takes_value=True),
    ForwardedArgument("quantity", "--quantity", takes_value=True),
    *READONLY_CONFIRM,
)
QQQ100_ACTION_CONTEXT = (
    ForwardedArgument("use_paper_positions_readonly", "--use-paper-positions-readonly"),
    *READONLY_CONFIRM,
)


PRE_CONFIG_COMMANDS = (
    CommandDescriptor('plot_strategy_results', SideEffect.REPORT_ONLY),
    CommandDescriptor('research_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('walk_forward_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('strategy_promotion_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('defensive_strategy_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('defensive_candidate_comparison', SideEffect.REPORT_ONLY),
    CommandDescriptor('defensive_research_state_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('defensive_allocation_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('defensive_allocation_risk_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('defensive_allocation_decision_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('defensive_execution_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('drawdown_period_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('etf_defensive_drawdown_comparison', SideEffect.REPORT_ONLY),
    CommandDescriptor('plot_etf_defensive_comparison', SideEffect.REPORT_ONLY),
    CommandDescriptor('refresh_defensive_research', SideEffect.REPORT_ONLY),
    CommandDescriptor('short_selling_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('etf_rotation_robustness', SideEffect.RESEARCH),
    CommandDescriptor('etf_breadth_regime_backtest', SideEffect.RESEARCH),
    CommandDescriptor('etf_breadth_regime_decision_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('etf_breadth_regime_robustness', SideEffect.RESEARCH),
    CommandDescriptor('strategy_improvement_lab', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_strategy_improvement_lab', SideEffect.REPORT_ONLY),
    CommandDescriptor('strategy_improvement_robustness', SideEffect.RESEARCH),
    CommandDescriptor('show_strategy_improvement_robustness', SideEffect.REPORT_ONLY),
    CommandDescriptor('strategy_improvement_diagnostics', SideEffect.RESEARCH),
    CommandDescriptor('show_strategy_improvement_diagnostics', SideEffect.REPORT_ONLY),
    CommandDescriptor('growth_biased_stricter_validation', SideEffect.RESEARCH),
    CommandDescriptor('show_growth_biased_stricter_validation', SideEffect.REPORT_ONLY),
    CommandDescriptor('growth_biased_stricter_promotion_readiness', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_growth_biased_stricter_promotion_readiness', SideEffect.REPORT_ONLY),
    CommandDescriptor('growth_biased_stricter_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_growth_biased_stricter_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('growth_biased_stricter_threshold_neighbourhood', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_growth_biased_stricter_threshold_neighbourhood', SideEffect.REPORT_ONLY),
    CommandDescriptor('growth_biased_stricter_cost_turnover_stress', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_growth_biased_stricter_cost_turnover_stress', SideEffect.REPORT_ONLY),
    CommandDescriptor('growth_biased_stricter_persistence_filter', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_growth_biased_stricter_persistence_filter', SideEffect.REPORT_ONLY),
    CommandDescriptor('codex_ambitious_validation', SideEffect.RESEARCH),
    CommandDescriptor('show_codex_ambitious_validation', SideEffect.REPORT_ONLY),
    CommandDescriptor('codex_ambitious_split_drawdown_validation', SideEffect.RESEARCH),
    CommandDescriptor('show_codex_ambitious_split_drawdown_validation', SideEffect.REPORT_ONLY),
    CommandDescriptor('codex_ambitious_lead_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_codex_ambitious_lead_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_research_preview', SideEffect.RESEARCH),
    CommandDescriptor('crypto_universe_readiness_report', SideEffect.RESEARCH),
    CommandDescriptor('show_crypto_universe_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('expanded_crypto_strategy_lab', SideEffect.RESEARCH),
    CommandDescriptor('show_expanded_crypto_strategy_lab', SideEffect.REPORT_ONLY),
    CommandDescriptor('expanded_crypto_robustness_report', SideEffect.RESEARCH),
    CommandDescriptor('show_expanded_crypto_robustness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_equal_weight_crash_gate', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_crypto_equal_weight_crash_gate', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_equal_weight_volatility_scaling', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_crypto_equal_weight_volatility_scaling', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_equal_weight_capped_risk_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_crypto_equal_weight_capped_risk_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('expanded_crypto_lead_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_expanded_crypto_lead_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_lead_split_sensitivity_diagnosis', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_crypto_lead_split_sensitivity_diagnosis', SideEffect.REPORT_ONLY),
    CommandDescriptor('expanded_crypto_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_expanded_crypto_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq_trend_gate_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq_trend_gate_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq_preview_candidate_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq_preview_candidate_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_preview_candidate_readiness_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq100_preview_candidate_readiness_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_preview_signal_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq100_preview_signal_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_action_preview', SideEffect.BROKER_READ, forwarded=QQQ100_ACTION_CONTEXT),
    CommandDescriptor('show_qqq100_action_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_strategy_portfolio_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_strategy_portfolio_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_paper_readiness_blocker_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq100_paper_readiness_blocker_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_paper_execution_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq100_paper_execution_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_promotion_gate', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_promotion_gate', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_state_summary', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_state_summary', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_evidence_audit', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_evidence_audit', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_postcheck_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq100_postcheck_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_followup_policy_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq100_followup_policy_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_daily_decision_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq100_daily_decision_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_monitoring_status', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_monitoring_status', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_checklist_status', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_checklist_status', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_go_no_go_dashboard', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_go_no_go_dashboard', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_post_gate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_post_gate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_manual_ticket_value_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_manual_ticket_value_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_executable_ticket_prerequisites_closeout', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_executable_ticket_prerequisites_closeout', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_executable_ticket_approval_readiness', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_executable_ticket_approval_readiness', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_executable_ticket_approval_criteria', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_executable_ticket_approval_criteria', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_executable_ticket_criteria_resolution_plan', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_executable_ticket_criteria_resolution_plan', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_executable_ticket_criteria_source_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_executable_ticket_criteria_source_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_criteria_source_blocker_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_criteria_source_blocker_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_criteria_resolution_plan_blocker_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_criteria_resolution_plan_blocker_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_approval_criteria_not_approval_blocker_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_approval_criteria_not_approval_blocker_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_criteria_blocker_specific_review_rollup', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_criteria_blocker_specific_review_rollup', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_criteria_source_closeout_candidate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_criteria_source_closeout_candidate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_criteria_closeout_candidate_review_rollup', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_criteria_closeout_candidate_review_rollup', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_f6_f7_audit', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_f6_f7_audit', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_promotion_ladder_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_promotion_ladder_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_promotion_ladder_status', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_promotion_ladder_status', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_f7_accounting_proof', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_f7_accounting_proof', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_next_ladder_candidate_scope', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_next_ladder_candidate_scope', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_defensive_sleeve_ladder_scope_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_defensive_sleeve_ladder_scope_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_defensive_sleeve_manual_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_defensive_sleeve_manual_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_defensive_sleeve_preview_readiness', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_defensive_sleeve_preview_readiness', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_defensive_sleeve_evidence_quality', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_defensive_sleeve_evidence_quality', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_multi_sleeve_roadmap', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_multi_sleeve_roadmap', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_next_phase_backlog', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_next_phase_backlog', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_multi_sleeve_evidence_gap', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_multi_sleeve_evidence_gap', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_high_growth_evidence_gap', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_high_growth_evidence_gap', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_high_growth_evidence_quality', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_high_growth_evidence_quality', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_live_high_growth_manual_review_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_live_high_growth_manual_review_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_paper_postcheck', SideEffect.BROKER_READ, forwarded=READONLY_CONFIRM),
    CommandDescriptor('show_qqq100_paper_postcheck', SideEffect.REPORT_ONLY),
    CommandDescriptor('qqq100_repeat_alignment_workflow_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_qqq100_repeat_alignment_workflow_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_strategy_monitor', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_strategy_monitor', SideEffect.REPORT_ONLY),
    CommandDescriptor('sleeve_research_scoreboard', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_sleeve_research_scoreboard', SideEffect.REPORT_ONLY),
    CommandDescriptor('codex_qqq_defensive_crash_gate_research_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_codex_qqq_defensive_crash_gate_research_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('sleeve_return_streams', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_sleeve_return_streams', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_return_streams', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_crypto_return_streams', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_portfolio_backtest', SideEffect.RESEARCH),
    CommandDescriptor('show_multi_sleeve_portfolio_backtest', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_robustness', SideEffect.RESEARCH),
    CommandDescriptor('show_multi_sleeve_robustness', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_crypto_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_crypto_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_crypto_containment_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_crypto_containment_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_allocation_policy_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_allocation_policy_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_weight_sensitivity', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_weight_sensitivity', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_higher_growth_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_higher_growth_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_research_lead_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_research_lead_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_lead_state_refresh', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_lead_state', SideEffect.REPORT_ONLY),
    CommandDescriptor('multi_sleeve_high_growth_drawdown_decomposition', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_multi_sleeve_high_growth_drawdown_decomposition', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_sleeve_quality_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_sleeve_quality_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_component_attribution', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_component_attribution', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_component_streams', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_component_streams', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_sleeve_concentration_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_sleeve_concentration_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_research_checkpoint', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_research_checkpoint', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_execution_state_summary', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_execution_state_summary', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_lab', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_stock_lab', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_universe_expansion_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_stock_universe_expansion_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_drawdown_control_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_stock_drawdown_control_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_lead_decision_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_stock_lead_decision_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_stock_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_risk_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_stock_risk_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_risk_evidence_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_stock_risk_evidence_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_branch_decision_checkpoint', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_stock_branch_decision_checkpoint', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_stock_final_validation_pack', SideEffect.RESEARCH),
    CommandDescriptor('show_high_growth_stock_final_validation_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('high_growth_strategy_discovery_sprint', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_high_growth_strategy_discovery_sprint', SideEffect.REPORT_ONLY),
    CommandDescriptor('higher_growth_preview_readiness_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_higher_growth_preview_readiness_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('higher_growth_candidate_selection_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_higher_growth_candidate_selection_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('higher_growth_preview_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_higher_growth_preview_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_research_sprint', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_research_sprint', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_manual_review_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_robustness_checkpoint', SideEffect.RESEARCH),
    CommandDescriptor('show_vol_targeted_growth_robustness_checkpoint', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_nearby_variants_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_nearby_variants_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_preview_readiness_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_preview_readiness_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_preview_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_preview_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_preview_signal', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_preview_signal', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_action_preview_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_action_preview_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_action_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_action_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_broker_position_comparison_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_broker_position_comparison_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_portfolio_risk_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_portfolio_risk_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_portfolio_risk_policy_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_portfolio_risk_policy_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_paper_live_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_paper_live_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_broker_comparison_run_readiness', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_broker_comparison_run_readiness', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_broker_position_comparison', SideEffect.BROKER_READ, forwarded=READONLY_CONFIRM),
    CommandDescriptor('show_vol_targeted_growth_broker_position_comparison', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_post_comparison_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_post_comparison_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_stricter_paper_live_gate_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_stricter_paper_live_gate_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_gate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_gate_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_candidate_decision_record', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_candidate_decision_record', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_candidate_discussion', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_candidate_discussion', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_proposal_implementation_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_proposal_implementation_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_proposal_preview_schema', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_proposal_preview_schema', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_proposal_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_proposal_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_evidence_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_evidence_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_risk_reward_comparison', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_risk_reward_comparison', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_drawdown_stress_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_drawdown_stress_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_cost_turnover_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_cost_turnover_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_split_stability_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_split_stability_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_component_sleeve_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_component_sleeve_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_action_preview_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_action_preview_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_proposal_document', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_proposal_document', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_broker_exposure_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_broker_exposure_review', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_manual_review_checkpoint', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_manual_review_checkpoint', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_formal_seed_change_proposal', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_formal_seed_change_proposal', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_manual_approval_record', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_manual_approval_record', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_implementation_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_implementation_design', SideEffect.REPORT_ONLY),
    CommandDescriptor('vol_targeted_growth_seed_change_dry_run_diff', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_vol_targeted_growth_seed_change_dry_run_diff', SideEffect.REPORT_ONLY),
    CommandDescriptor('project_research_state_refresh', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_project_research_state_refresh', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_current_research_state', SideEffect.REPORT_ONLY),
    CommandDescriptor('project_research_state_quality_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('stock_etf_paper_execution_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('alpaca_paper_readiness_report', SideEffect.BROKER_READ, forwarded=READONLY_CONFIRM),
    CommandDescriptor('alpaca_connectivity_diagnostics', SideEffect.NETWORK_DIAGNOSTIC),
    CommandDescriptor('show_alpaca_connectivity_diagnostics', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_order_smoke_test_readiness_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_order_smoke_test_live_preflight', SideEffect.BROKER_READ, forwarded=SMOKE_TEST_CONTEXT),
    CommandDescriptor('paper_order_smoke_test_postcheck', SideEffect.BROKER_READ, forwarded=SMOKE_TEST_CONTEXT),
    CommandDescriptor('future_refresh_cron_readiness_pack', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_order_smoke_test_runbook_check', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_smoke_test_kill_switch_diagnosis', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_paper_smoke_test_kill_switch_diagnosis', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_strategy_lab', SideEffect.MARKET_DATA),
    CommandDescriptor('crypto_strategy_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_strategy_decision_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_cost_stress_report', SideEffect.RESEARCH),
    CommandDescriptor('crypto_robustness_report', SideEffect.RESEARCH),
    CommandDescriptor('crypto_period_diagnostics', SideEffect.RESEARCH),
    CommandDescriptor('preview_crypto_signals', SideEffect.MARKET_DATA),
    CommandDescriptor('show_crypto_monitor', SideEffect.REPORT_ONLY),
    CommandDescriptor('crypto_research_state_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('ticker_universe_readiness_report', SideEffect.MARKET_DATA),
    CommandDescriptor('market_monitor_snapshot', SideEffect.MARKET_DATA),
    CommandDescriptor('show_market_monitor', SideEffect.REPORT_ONLY),
    CommandDescriptor('market_monitor_quality_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('refresh_market_monitor', SideEffect.MARKET_DATA),
    CommandDescriptor('market_monitor_scheduling_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('monitor_lockfile_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_promoted_actions', SideEffect.REPORT_ONLY),
    CommandDescriptor('promoted_risk_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('promoted_consensus_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('promoted_decision_preview', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_promoted_decision', SideEffect.REPORT_ONLY),
    CommandDescriptor('deployment_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('vps_operations_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('vps_monitoring_status', SideEffect.REPORT_ONLY),
    CommandDescriptor('vps_daily_monitoring_summary', SideEffect.REPORT_ONLY),
    CommandDescriptor('portfolio_risk_policy_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_portfolio_risk_policy', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_kill_switch_readiness_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_kill_switch_gate_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('paper_execution_protection_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('normal_bot_execution_policy_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('execution_eligibility_report', SideEffect.REPORT_ONLY),
    CommandDescriptor('build_research_dashboard', SideEffect.REPORT_ONLY),
    CommandDescriptor('show_promoted_risk', SideEffect.REPORT_ONLY),
)


PRE_CONFIG_BY_OPTION = {descriptor.option: descriptor for descriptor in PRE_CONFIG_COMMANDS}


CONFIG_COMMANDS = (
    CommandDescriptor("prepare_vol_targeted_growth_paper_ticket", SideEffect.BROKER_READ),
    CommandDescriptor("execute_vol_targeted_growth_paper", SideEffect.PAPER_EXECUTION),
    CommandDescriptor("vol_targeted_growth_paper_postcheck", SideEffect.BROKER_READ),
    CommandDescriptor("run_vol_targeted_growth_auto_paper", SideEffect.PAPER_EXECUTION),
    CommandDescriptor("execute_qqq100_paper", SideEffect.PAPER_EXECUTION),
    CommandDescriptor("execute_slow_sma_paper", SideEffect.PAPER_EXECUTION),
    CommandDescriptor("preview_slow_sma_actions", SideEffect.BROKER_READ),
    CommandDescriptor("preview_promoted_strategies", SideEffect.MARKET_DATA),
    CommandDescriptor("preview_promoted_actions", SideEffect.BROKER_READ),
    CommandDescriptor("refresh_promoted_review", SideEffect.BROKER_READ),
    CommandDescriptor("preview_slow_sma_signals", SideEffect.MARKET_DATA),
    CommandDescriptor("trend_stress_test", SideEffect.MARKET_DATA),
    CommandDescriptor("etf_rotation_backtest", SideEffect.MARKET_DATA),
    CommandDescriptor("build_etf_breadth_price_history", SideEffect.MARKET_DATA),
    CommandDescriptor("adaptive_momentum_backtest", SideEffect.MARKET_DATA),
    CommandDescriptor("short_hedge_backtest", SideEffect.RESEARCH),
    CommandDescriptor("short_strategy_lab", SideEffect.RESEARCH),
    CommandDescriptor("vol_managed_etf_backtest", SideEffect.MARKET_DATA),
    CommandDescriptor("vol_managed_etf_robustness", SideEffect.RESEARCH),
    CommandDescriptor("sma_sensitivity", SideEffect.MARKET_DATA),
    CommandDescriptor("compare_strategies", SideEffect.MARKET_DATA),
    CommandDescriptor("backtest", SideEffect.MARKET_DATA),
    CommandDescriptor("paper_order_test", SideEffect.PAPER_EXECUTION),
)
NORMAL_RUN = CommandDescriptor("normal_run", SideEffect.PAPER_EXECUTION, handler="run_bot")


ConfigHandler = Callable[[Any, Any, Any], int]


def _build_argv(descriptor: CommandDescriptor, args: Any) -> list[str]:
    argv = [descriptor.option]
    for forwarded in descriptor.forwarded:
        value = getattr(args, forwarded.source)
        if forwarded.takes_value:
            if value:
                argv.extend((forwarded.option, str(value)))
        elif value:
            argv.append(forwarded.option)
    return argv


def dispatch_pre_config(args: Any) -> DispatchResult:
    for descriptor in PRE_CONFIG_COMMANDS:
        if not getattr(args, descriptor.dest):
            continue
        exit_code = dispatch_early_command(_build_argv(descriptor, args))
        if exit_code is None:
            raise RuntimeError(f"Registered command was not handled: {descriptor.option}")
        return DispatchResult(True, exit_code, descriptor)
    return DispatchResult(False)


def dispatch_config_command(
    args: Any,
    config: Any,
    logger: Any,
    handlers: Mapping[str, ConfigHandler],
) -> DispatchResult:
    for descriptor in CONFIG_COMMANDS:
        if not getattr(args, descriptor.dest):
            continue
        handler = handlers[descriptor.handler or descriptor.dest]
        return DispatchResult(True, handler(args, config, logger), descriptor)
    return DispatchResult(False, descriptor=NORMAL_RUN)
