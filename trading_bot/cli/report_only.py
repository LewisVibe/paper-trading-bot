"""Early saved-output routing with explicit external-dependency classification."""

from __future__ import annotations


REPORT_ONLY = "report_only"
BROKER_READ = "broker_read"
NETWORK_DIAGNOSTIC = "network_diagnostic"

BROKER_READ_OPTIONS = frozenset(
    {
        "--alpaca-paper-readiness-report",
        "--paper-order-smoke-test-live-preflight",
        "--paper-order-smoke-test-postcheck",
        "--qqq100-paper-postcheck",
        "--vol-targeted-growth-broker-position-comparison",
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
    }
)
NETWORK_DIAGNOSTIC_OPTIONS = frozenset({"--alpaca-connectivity-diagnostics"})


def classify_early_route(argv: list[str]) -> str:
    options = set(argv)
    if options & NETWORK_DIAGNOSTIC_OPTIONS:
        return NETWORK_DIAGNOSTIC
    if options & BROKER_READ_OPTIONS:
        return BROKER_READ
    if "--qqq100-action-preview" in options and "--use-paper-positions-readonly" in options:
        return BROKER_READ
    return REPORT_ONLY


def dispatch_report_only(argv: list[str]) -> int | None:
    """Dispatch only routes that cannot read external broker or network state."""
    if classify_early_route(argv) != REPORT_ONLY:
        return None
    return _dispatch_early_command(argv)


def dispatch_early_command(argv: list[str]) -> int | None:
    """Compatibility dispatcher for all legacy early routes, including classified reads."""
    return _dispatch_early_command(argv)


def _dispatch_early_command(argv: list[str]) -> int | None:
    if argv == ["--vps-monitoring-status"]:
        from trading_bot.research.vps_monitoring_status import print_vps_monitoring_status

        return (print_vps_monitoring_status())
    if argv == ["--vps-daily-monitoring-summary"]:
        from trading_bot.research.vps_daily_monitoring_summary import print_vps_daily_monitoring_summary

        return (print_vps_daily_monitoring_summary())
    if argv == ["--market-monitor-scheduling-readiness-report"]:
        from trading_bot.research.market_monitor_scheduling import print_market_monitor_scheduling_readiness_report

        return (print_market_monitor_scheduling_readiness_report())
    if argv == ["--stock-etf-paper-execution-readiness-report"]:
        from trading_bot.research.stock_etf_paper_execution_readiness import (
            generate_stock_etf_paper_execution_readiness_report,
        )

        result = generate_stock_etf_paper_execution_readiness_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv in (
        ["--alpaca-paper-readiness-report"],
        ["--alpaca-paper-readiness-report", "--confirm-readonly-alpaca-check"],
    ):
        from trading_bot.research.alpaca_paper_readiness import generate_alpaca_paper_readiness_report

        result = generate_alpaca_paper_readiness_report(
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in argv
        )
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--alpaca-connectivity-diagnostics"]:
        from trading_bot.research.alpaca_connectivity_diagnostics import generate_alpaca_connectivity_diagnostics

        result = generate_alpaca_connectivity_diagnostics()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-alpaca-connectivity-diagnostics"]:
        from trading_bot.research.alpaca_connectivity_diagnostics import show_alpaca_connectivity_diagnostics

        status_code, lines = show_alpaca_connectivity_diagnostics()
        for line in lines:
            print(line)
        return (status_code)
    if argv == ["--paper-order-smoke-test-readiness-pack"]:
        from trading_bot.research.paper_order_smoke_test_readiness import (
            generate_paper_order_smoke_test_readiness_pack,
        )

        result = generate_paper_order_smoke_test_readiness_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if "--paper-order-smoke-test-live-preflight" in argv:
        from trading_bot.research.paper_order_smoke_test_live_preflight import (
            generate_paper_order_smoke_test_live_preflight,
        )

        early_args = _parse_live_preflight_early_args(argv)
        result = generate_paper_order_smoke_test_live_preflight(
            ticker=early_args.get("ticker", ""),
            side=early_args.get("side", ""),
            quantity=early_args.get("quantity", ""),
            confirm_readonly_alpaca_check=early_args.get("confirm_readonly_alpaca_check", "") == "true",
        )
        for line in result.summary_lines:
            print(line)
        return (0)
    if "--paper-order-smoke-test-postcheck" in argv:
        from trading_bot.research.paper_order_smoke_test_postcheck import (
            generate_paper_order_smoke_test_postcheck,
        )

        early_args = _parse_live_preflight_early_args(argv)
        result = generate_paper_order_smoke_test_postcheck(
            ticker=early_args.get("ticker", ""),
            side=early_args.get("side", ""),
            quantity=early_args.get("quantity", ""),
            confirm_readonly_alpaca_check=early_args.get("confirm_readonly_alpaca_check", "") == "true",
        )
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--future-refresh-cron-readiness-pack"]:
        from trading_bot.research.future_refresh_cron_readiness import generate_future_refresh_cron_readiness_pack

        result = generate_future_refresh_cron_readiness_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--paper-order-smoke-test-runbook-check"]:
        from trading_bot.research.paper_order_smoke_test_runbook_check import (
            generate_paper_order_smoke_test_runbook_check,
        )

        result = generate_paper_order_smoke_test_runbook_check()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--paper-smoke-test-kill-switch-diagnosis"]:
        from trading_bot.research.paper_smoke_test_kill_switch_diagnosis import (
            generate_paper_smoke_test_kill_switch_diagnosis,
        )

        result = generate_paper_smoke_test_kill_switch_diagnosis()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-smoke-test-kill-switch-diagnosis"]:
        from trading_bot.research.paper_smoke_test_kill_switch_diagnosis import (
            show_paper_smoke_test_kill_switch_diagnosis,
        )

        code, lines = show_paper_smoke_test_kill_switch_diagnosis()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--short-leverage-research-lab"]:
        from trading_bot.research.short_leverage_research_lab import run_short_leverage_research_lab

        result = run_short_leverage_research_lab()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-short-leverage-research-lab"]:
        from trading_bot.research.short_leverage_research_lab import show_short_leverage_research_lab

        code, lines = show_short_leverage_research_lab()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq-leverage-validation-report"]:
        from trading_bot.research.qqq_leverage_validation import generate_qqq_leverage_validation_report

        result = generate_qqq_leverage_validation_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq-leverage-validation-report"]:
        from trading_bot.research.qqq_leverage_validation import show_qqq_leverage_validation_report

        code, lines = show_qqq_leverage_validation_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq-adaptive-leverage-lab"]:
        from trading_bot.research.qqq_adaptive_leverage_lab import generate_qqq_adaptive_leverage_lab

        result = generate_qqq_adaptive_leverage_lab()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq-adaptive-leverage-lab"]:
        from trading_bot.research.qqq_adaptive_leverage_lab import show_qqq_adaptive_leverage_lab

        code, lines = show_qqq_adaptive_leverage_lab()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq-lead-decision-report"]:
        from trading_bot.research.qqq_lead_decision import generate_qqq_lead_decision_report

        result = generate_qqq_lead_decision_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq-lead-decision-report"]:
        from trading_bot.research.qqq_lead_decision import show_qqq_lead_decision_report

        code, lines = show_qqq_lead_decision_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq-trend-gate-manual-review-pack"]:
        from trading_bot.research.qqq_trend_gate_manual_review import generate_qqq_trend_gate_manual_review_pack

        result = generate_qqq_trend_gate_manual_review_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq-trend-gate-manual-review-pack"]:
        from trading_bot.research.qqq_trend_gate_manual_review import show_qqq_trend_gate_manual_review_pack

        code, lines = show_qqq_trend_gate_manual_review_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq-preview-candidate-readiness-report"]:
        from trading_bot.research.qqq_preview_candidate_readiness import generate_qqq_preview_candidate_readiness_report

        result = generate_qqq_preview_candidate_readiness_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq-preview-candidate-readiness-report"]:
        from trading_bot.research.qqq_preview_candidate_readiness import show_qqq_preview_candidate_readiness_report

        code, lines = show_qqq_preview_candidate_readiness_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-preview-candidate-readiness-pack"]:
        from trading_bot.research.qqq100_preview_candidate_readiness_pack import (
            generate_qqq100_preview_candidate_readiness_pack,
        )

        result = generate_qqq100_preview_candidate_readiness_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-preview-candidate-readiness-pack"]:
        from trading_bot.research.qqq100_preview_candidate_readiness_pack import (
            show_qqq100_preview_candidate_readiness_pack,
        )

        code, lines = show_qqq100_preview_candidate_readiness_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-preview-signal-pack"]:
        from trading_bot.research.qqq100_preview_signal_pack import (
            generate_qqq100_preview_signal_pack,
        )

        result = generate_qqq100_preview_signal_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-preview-signal-pack"]:
        from trading_bot.research.qqq100_preview_signal_pack import (
            show_qqq100_preview_signal_pack,
        )

        code, lines = show_qqq100_preview_signal_pack()
        for line in lines:
            print(line)
        return (code)
    if _is_qqq100_action_preview_early_args(argv):
        from trading_bot.research.qqq100_action_preview import (
            generate_qqq100_action_preview,
        )

        result = generate_qqq100_action_preview(
            use_paper_positions_readonly="--use-paper-positions-readonly" in argv,
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in argv,
        )
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-action-preview"]:
        from trading_bot.research.qqq100_action_preview import (
            show_qqq100_action_preview,
        )

        code, lines = show_qqq100_action_preview()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-strategy-portfolio-preview"]:
        from trading_bot.research.multi_strategy_portfolio_preview import generate_multi_strategy_portfolio_preview

        result = generate_multi_strategy_portfolio_preview()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-strategy-portfolio-preview"]:
        from trading_bot.research.multi_strategy_portfolio_preview import show_multi_strategy_portfolio_preview

        code, lines = show_multi_strategy_portfolio_preview()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-paper-readiness-blocker-report"]:
        from trading_bot.research.qqq100_paper_readiness_blocker_report import (
            generate_qqq100_paper_readiness_blocker_report,
        )

        result = generate_qqq100_paper_readiness_blocker_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-paper-readiness-blocker-report"]:
        from trading_bot.research.qqq100_paper_readiness_blocker_report import (
            show_qqq100_paper_readiness_blocker_report,
        )

        code, lines = show_qqq100_paper_readiness_blocker_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-paper-execution-readiness-report"]:
        from trading_bot.research.qqq100_paper_execution_readiness_report import (
            generate_qqq100_paper_execution_readiness_report,
        )

        result = generate_qqq100_paper_execution_readiness_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-paper-execution-readiness-report"]:
        from trading_bot.research.qqq100_paper_execution_readiness_report import (
            show_qqq100_paper_execution_readiness_report,
        )

        code, lines = show_qqq100_paper_execution_readiness_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-promotion-gate"]:
        from trading_bot.research.paper_live_promotion_gate import generate_paper_live_promotion_gate

        result = generate_paper_live_promotion_gate()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-promotion-gate"]:
        from trading_bot.research.paper_live_promotion_gate import show_paper_live_promotion_gate

        code, lines = show_paper_live_promotion_gate()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-readiness-report"]:
        from trading_bot.research.paper_live_readiness_report import generate_paper_live_readiness_report

        result = generate_paper_live_readiness_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-readiness-report"]:
        from trading_bot.research.paper_live_readiness_report import show_paper_live_readiness_report

        code, lines = show_paper_live_readiness_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-state-summary"]:
        from trading_bot.research.paper_live_state_summary import generate_paper_live_state_summary

        result = generate_paper_live_state_summary()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-state-summary"]:
        from trading_bot.research.paper_live_state_summary import show_paper_live_state_summary

        code, lines = show_paper_live_state_summary()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-evidence-audit"]:
        from trading_bot.research.paper_live_evidence_audit import generate_paper_live_evidence_audit

        result = generate_paper_live_evidence_audit()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-evidence-audit"]:
        from trading_bot.research.paper_live_evidence_audit import show_paper_live_evidence_audit

        code, lines = show_paper_live_evidence_audit()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-postcheck-readiness-report"]:
        from trading_bot.research.qqq100_postcheck_readiness_report import (
            generate_qqq100_postcheck_readiness_report,
        )

        result = generate_qqq100_postcheck_readiness_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-postcheck-readiness-report"]:
        from trading_bot.research.qqq100_postcheck_readiness_report import (
            show_qqq100_postcheck_readiness_report,
        )

        code, lines = show_qqq100_postcheck_readiness_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-followup-policy-report"]:
        from trading_bot.research.qqq100_followup_policy_report import (
            generate_qqq100_followup_policy_report,
        )

        result = generate_qqq100_followup_policy_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-followup-policy-report"]:
        from trading_bot.research.qqq100_followup_policy_report import (
            show_qqq100_followup_policy_report,
        )

        code, lines = show_qqq100_followup_policy_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-daily-decision-report"]:
        from trading_bot.research.qqq100_daily_decision_report import (
            generate_qqq100_daily_decision_report,
        )

        result = generate_qqq100_daily_decision_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-daily-decision-report"]:
        from trading_bot.research.qqq100_daily_decision_report import (
            show_qqq100_daily_decision_report,
        )

        code, lines = show_qqq100_daily_decision_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-manual-flatten-readiness-report"]:
        from trading_bot.research.qqq100_manual_flatten_readiness_report import (
            generate_qqq100_manual_flatten_readiness_report,
        )

        result = generate_qqq100_manual_flatten_readiness_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-manual-flatten-readiness-report"]:
        from trading_bot.research.qqq100_manual_flatten_readiness_report import (
            show_qqq100_manual_flatten_readiness_report,
        )

        code, lines = show_qqq100_manual_flatten_readiness_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-manual-flatten-runbook-report"]:
        from trading_bot.research.qqq100_manual_flatten_runbook_report import (
            generate_qqq100_manual_flatten_runbook_report,
        )

        result = generate_qqq100_manual_flatten_runbook_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-manual-flatten-runbook-report"]:
        from trading_bot.research.qqq100_manual_flatten_runbook_report import (
            show_qqq100_manual_flatten_runbook_report,
        )

        code, lines = show_qqq100_manual_flatten_runbook_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-monitoring-status"]:
        from trading_bot.research.paper_live_monitoring_status import (
            generate_paper_live_monitoring_status,
        )

        result = generate_paper_live_monitoring_status()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-monitoring-status"]:
        from trading_bot.research.paper_live_monitoring_status import (
            show_paper_live_monitoring_status,
        )

        code, lines = show_paper_live_monitoring_status()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-checklist-status"]:
        from trading_bot.research.paper_live_checklist_status import (
            generate_paper_live_checklist_status,
        )

        result = generate_paper_live_checklist_status()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-checklist-status"]:
        from trading_bot.research.paper_live_checklist_status import (
            show_paper_live_checklist_status,
        )

        code, lines = show_paper_live_checklist_status()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-go-no-go-dashboard"]:
        from trading_bot.research.paper_live_go_no_go_dashboard import (
            generate_paper_live_go_no_go_dashboard,
        )

        result = generate_paper_live_go_no_go_dashboard()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-go-no-go-dashboard"]:
        from trading_bot.research.paper_live_go_no_go_dashboard import (
            show_paper_live_go_no_go_dashboard,
        )

        code, lines = show_paper_live_go_no_go_dashboard()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-post-gate-review"]:
        from trading_bot.research.vol_targeted_growth_post_gate_review import (
            generate_vol_targeted_growth_post_gate_review,
        )

        result = generate_vol_targeted_growth_post_gate_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-post-gate-review"]:
        from trading_bot.research.vol_targeted_growth_post_gate_review import (
            show_vol_targeted_growth_post_gate_review,
        )

        code, lines = show_vol_targeted_growth_post_gate_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-manual-ticket-value-design"]:
        from trading_bot.research.vol_targeted_growth_manual_ticket_value_design import (
            generate_vol_targeted_growth_manual_ticket_value_design,
        )

        result = generate_vol_targeted_growth_manual_ticket_value_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-manual-ticket-value-design"]:
        from trading_bot.research.vol_targeted_growth_manual_ticket_value_design import (
            show_vol_targeted_growth_manual_ticket_value_design,
        )

        code, lines = show_vol_targeted_growth_manual_ticket_value_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-executable-ticket-prerequisites-closeout"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
            generate_vol_targeted_growth_executable_ticket_prerequisites_closeout,
        )

        result = generate_vol_targeted_growth_executable_ticket_prerequisites_closeout()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-executable-ticket-prerequisites-closeout"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
            show_vol_targeted_growth_executable_ticket_prerequisites_closeout,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_prerequisites_closeout()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-executable-ticket-approval-readiness"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
            generate_vol_targeted_growth_executable_ticket_approval_readiness,
        )

        result = generate_vol_targeted_growth_executable_ticket_approval_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-executable-ticket-approval-readiness"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
            show_vol_targeted_growth_executable_ticket_approval_readiness,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_approval_readiness()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-execution-approval-request-readiness"]:
        from trading_bot.research.vol_targeted_growth_execution_approval_request_readiness import (
            generate_vol_targeted_growth_execution_approval_request_readiness,
        )

        result = generate_vol_targeted_growth_execution_approval_request_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-execution-approval-request-readiness"]:
        from trading_bot.research.vol_targeted_growth_execution_approval_request_readiness import (
            show_vol_targeted_growth_execution_approval_request_readiness,
        )

        code, lines = show_vol_targeted_growth_execution_approval_request_readiness()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-execution-design-approval-wording"]:
        from trading_bot.research.vol_targeted_growth_execution_design_approval import (
            generate_vol_targeted_growth_execution_design_approval_wording,
        )

        result = generate_vol_targeted_growth_execution_design_approval_wording()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-execution-design-approval-wording"]:
        from trading_bot.research.vol_targeted_growth_execution_design_approval import (
            show_vol_targeted_growth_execution_design_approval_wording,
        )

        code, lines = show_vol_targeted_growth_execution_design_approval_wording()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-execution-design-approval-record"]:
        from trading_bot.research.vol_targeted_growth_execution_design_approval import (
            generate_vol_targeted_growth_execution_design_approval_record,
        )

        result = generate_vol_targeted_growth_execution_design_approval_record()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-execution-design-approval-record"]:
        from trading_bot.research.vol_targeted_growth_execution_design_approval import (
            show_vol_targeted_growth_execution_design_approval_record,
        )

        code, lines = show_vol_targeted_growth_execution_design_approval_record()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-non-submitting-executable-ticket-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_executable_ticket_design import (
            generate_vol_targeted_growth_non_submitting_executable_ticket_design,
        )

        result = generate_vol_targeted_growth_non_submitting_executable_ticket_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-non-submitting-executable-ticket-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_executable_ticket_design import (
            show_vol_targeted_growth_non_submitting_executable_ticket_design,
        )

        code, lines = show_vol_targeted_growth_non_submitting_executable_ticket_design()
        for line in lines:
            print(line)
        return (code)
    ticket_values_approval_routes = {
        "--vol-targeted-growth-ticket-values-approval-readiness": "generate_vol_targeted_growth_ticket_values_approval_readiness",
        "--show-vol-targeted-growth-ticket-values-approval-readiness": "show_vol_targeted_growth_ticket_values_approval_readiness",
        "--vol-targeted-growth-ticket-values-approval-wording": "generate_vol_targeted_growth_ticket_values_approval_wording",
        "--show-vol-targeted-growth-ticket-values-approval-wording": "show_vol_targeted_growth_ticket_values_approval_wording",
        "--vol-targeted-growth-ticket-values-approval-record": "generate_vol_targeted_growth_ticket_values_approval_record",
        "--show-vol-targeted-growth-ticket-values-approval-record": "show_vol_targeted_growth_ticket_values_approval_record",
    }
    if argv and argv[0] in ticket_values_approval_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_ticket_values_approval as ticket_values_approval

        result = getattr(ticket_values_approval, ticket_values_approval_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    ticket_value_placeholder_routes = {
        "--vol-targeted-growth-ticket-value-placeholders": "generate_vol_targeted_growth_ticket_value_placeholders",
        "--show-vol-targeted-growth-ticket-value-placeholders": "show_vol_targeted_growth_ticket_value_placeholders",
        "--vol-targeted-growth-ticket-value-quality-gate": "generate_vol_targeted_growth_ticket_value_quality_gate",
        "--show-vol-targeted-growth-ticket-value-quality-gate": "show_vol_targeted_growth_ticket_value_quality_gate",
    }
    if argv and argv[0] in ticket_value_placeholder_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_ticket_value_placeholders as ticket_value_placeholders

        result = getattr(ticket_value_placeholders, ticket_value_placeholder_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    ticket_value_proposal_approval_routes = {
        "--vol-targeted-growth-ticket-value-proposal-approval-wording": "generate_vol_targeted_growth_ticket_value_proposal_approval_wording",
        "--show-vol-targeted-growth-ticket-value-proposal-approval-wording": "show_vol_targeted_growth_ticket_value_proposal_approval_wording",
        "--vol-targeted-growth-ticket-value-proposal-approval-record": "generate_vol_targeted_growth_ticket_value_proposal_approval_record",
        "--show-vol-targeted-growth-ticket-value-proposal-approval-record": "show_vol_targeted_growth_ticket_value_proposal_approval_record",
    }
    if argv and argv[0] in ticket_value_proposal_approval_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_ticket_value_proposal_approval as ticket_value_proposal_approval

        result = getattr(ticket_value_proposal_approval, ticket_value_proposal_approval_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    proposed_ticket_values_routes = {
        "--vol-targeted-growth-proposed-ticket-values": "generate_vol_targeted_growth_proposed_ticket_values",
        "--show-vol-targeted-growth-proposed-ticket-values": "show_vol_targeted_growth_proposed_ticket_values",
        "--vol-targeted-growth-proposed-ticket-values-quality-gate": "generate_vol_targeted_growth_proposed_ticket_values_quality_gate",
        "--show-vol-targeted-growth-proposed-ticket-values-quality-gate": "show_vol_targeted_growth_proposed_ticket_values_quality_gate",
    }
    if argv and argv[0] in proposed_ticket_values_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_proposed_ticket_values as proposed_ticket_values

        result = getattr(proposed_ticket_values, proposed_ticket_values_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    executable_ticket_draft_readiness_routes = {
        "--vol-targeted-growth-executable-ticket-draft-readiness": "generate_vol_targeted_growth_executable_ticket_draft_readiness",
        "--show-vol-targeted-growth-executable-ticket-draft-readiness": "show_vol_targeted_growth_executable_ticket_draft_readiness",
    }
    if argv and argv[0] in executable_ticket_draft_readiness_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_executable_ticket_draft_readiness as executable_ticket_draft_readiness

        result = getattr(executable_ticket_draft_readiness, executable_ticket_draft_readiness_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    non_submitting_executable_ticket_draft_routes = {
        "--vol-targeted-growth-non-submitting-executable-ticket-draft": "generate_vol_targeted_growth_non_submitting_executable_ticket_draft",
        "--show-vol-targeted-growth-non-submitting-executable-ticket-draft": "show_vol_targeted_growth_non_submitting_executable_ticket_draft",
        "--vol-targeted-growth-non-submitting-executable-ticket-draft-quality-gate": "generate_vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate",
        "--show-vol-targeted-growth-non-submitting-executable-ticket-draft-quality-gate": "show_vol_targeted_growth_non_submitting_executable_ticket_draft_quality_gate",
    }
    if argv and argv[0] in non_submitting_executable_ticket_draft_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_non_submitting_executable_ticket_draft as non_submitting_ticket_draft

        result = getattr(non_submitting_ticket_draft, non_submitting_executable_ticket_draft_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    draft_ticket_value_approval_readiness_routes = {
        "--vol-targeted-growth-draft-ticket-value-approval-readiness": "generate_vol_targeted_growth_draft_ticket_value_approval_readiness",
        "--show-vol-targeted-growth-draft-ticket-value-approval-readiness": "show_vol_targeted_growth_draft_ticket_value_approval_readiness",
    }
    if argv and argv[0] in draft_ticket_value_approval_readiness_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_draft_ticket_value_approval_readiness as draft_value_approval_readiness

        result = getattr(draft_value_approval_readiness, draft_ticket_value_approval_readiness_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    draft_ticket_value_approval_routes = {
        "--vol-targeted-growth-draft-ticket-value-approval-wording": "generate_vol_targeted_growth_draft_ticket_value_approval_wording",
        "--show-vol-targeted-growth-draft-ticket-value-approval-wording": "show_vol_targeted_growth_draft_ticket_value_approval_wording",
        "--vol-targeted-growth-draft-ticket-value-approval-record": "generate_vol_targeted_growth_draft_ticket_value_approval_record",
        "--show-vol-targeted-growth-draft-ticket-value-approval-record": "show_vol_targeted_growth_draft_ticket_value_approval_record",
    }
    if argv and argv[0] in draft_ticket_value_approval_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_draft_ticket_value_approval as draft_value_approval

        result = getattr(draft_value_approval, draft_ticket_value_approval_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    review_only_draft_ticket_values_routes = {
        "--vol-targeted-growth-review-only-draft-ticket-values": "generate_vol_targeted_growth_review_only_draft_ticket_values",
        "--show-vol-targeted-growth-review-only-draft-ticket-values": "show_vol_targeted_growth_review_only_draft_ticket_values",
        "--vol-targeted-growth-review-only-draft-ticket-values-quality-gate": "generate_vol_targeted_growth_review_only_draft_ticket_values_quality_gate",
        "--show-vol-targeted-growth-review-only-draft-ticket-values-quality-gate": "show_vol_targeted_growth_review_only_draft_ticket_values_quality_gate",
    }
    if argv and argv[0] in review_only_draft_ticket_values_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_review_only_draft_ticket_values as review_only_draft_values

        result = getattr(review_only_draft_values, review_only_draft_ticket_values_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    draft_ticket_values_manual_review_routes = {
        "--vol-targeted-growth-draft-ticket-values-manual-review": "generate_vol_targeted_growth_draft_ticket_values_manual_review",
        "--show-vol-targeted-growth-draft-ticket-values-manual-review": "show_vol_targeted_growth_draft_ticket_values_manual_review",
        "--vol-targeted-growth-executable-ticket-values-readiness": "generate_vol_targeted_growth_executable_ticket_values_readiness",
        "--show-vol-targeted-growth-executable-ticket-values-readiness": "show_vol_targeted_growth_executable_ticket_values_readiness",
    }
    if argv and argv[0] in draft_ticket_values_manual_review_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_draft_ticket_values_manual_review as draft_values_manual_review

        result = getattr(draft_values_manual_review, draft_ticket_values_manual_review_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    executable_ticket_values_approval_routes = {
        "--vol-targeted-growth-executable-ticket-values-approval-wording": "generate_vol_targeted_growth_executable_ticket_values_approval_wording",
        "--show-vol-targeted-growth-executable-ticket-values-approval-wording": "show_vol_targeted_growth_executable_ticket_values_approval_wording",
        "--vol-targeted-growth-executable-ticket-values-approval-record": "generate_vol_targeted_growth_executable_ticket_values_approval_record",
        "--show-vol-targeted-growth-executable-ticket-values-approval-record": "show_vol_targeted_growth_executable_ticket_values_approval_record",
    }
    if argv and argv[0] in executable_ticket_values_approval_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_executable_ticket_values_approval as executable_values_approval

        result = getattr(executable_values_approval, executable_ticket_values_approval_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    non_submitting_executable_ticket_values_routes = {
        "--vol-targeted-growth-non-submitting-executable-ticket-values": "generate_vol_targeted_growth_non_submitting_executable_ticket_values",
        "--show-vol-targeted-growth-non-submitting-executable-ticket-values": "show_vol_targeted_growth_non_submitting_executable_ticket_values",
        "--vol-targeted-growth-non-submitting-executable-ticket-values-quality-gate": "generate_vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate",
        "--show-vol-targeted-growth-non-submitting-executable-ticket-values-quality-gate": "show_vol_targeted_growth_non_submitting_executable_ticket_values_quality_gate",
        "--vol-targeted-growth-non-submitting-executable-ticket-values-manual-review": "generate_vol_targeted_growth_non_submitting_executable_ticket_values_manual_review",
        "--show-vol-targeted-growth-non-submitting-executable-ticket-values-manual-review": "show_vol_targeted_growth_non_submitting_executable_ticket_values_manual_review",
        "--vol-targeted-growth-non-submitting-ticket-creation-readiness": "generate_vol_targeted_growth_non_submitting_ticket_creation_readiness",
        "--show-vol-targeted-growth-non-submitting-ticket-creation-readiness": "show_vol_targeted_growth_non_submitting_ticket_creation_readiness",
    }
    if argv and argv[0] in non_submitting_executable_ticket_values_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_non_submitting_executable_ticket_values as non_submitting_values

        result = getattr(non_submitting_values, non_submitting_executable_ticket_values_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--vol-targeted-growth-executable-ticket-approval-criteria"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_approval_criteria import (
            generate_vol_targeted_growth_executable_ticket_approval_criteria,
        )

        result = generate_vol_targeted_growth_executable_ticket_approval_criteria()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-executable-ticket-approval-criteria"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_approval_criteria import (
            show_vol_targeted_growth_executable_ticket_approval_criteria,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_approval_criteria()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-executable-ticket-criteria-resolution-plan"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_resolution_plan import (
            generate_vol_targeted_growth_executable_ticket_criteria_resolution_plan,
        )

        result = generate_vol_targeted_growth_executable_ticket_criteria_resolution_plan()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-executable-ticket-criteria-resolution-plan"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_resolution_plan import (
            show_vol_targeted_growth_executable_ticket_criteria_resolution_plan,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_criteria_resolution_plan()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-executable-ticket-criteria-source-review"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_source_review import (
            generate_vol_targeted_growth_executable_ticket_criteria_source_review,
        )

        result = generate_vol_targeted_growth_executable_ticket_criteria_source_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-executable-ticket-criteria-source-review"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_source_review import (
            show_vol_targeted_growth_executable_ticket_criteria_source_review,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_criteria_source_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review import (
            generate_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review,
        )

        result = generate_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review import (
            show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review()
        for line in lines:
            print(line)
        return (code)
    blocker_specific_routes = {
        "--vol-targeted-growth-criteria-source-blocker-review": (
            "generate_vol_targeted_growth_criteria_source_blocker_review",
            "Executable-ticket criteria source blocker review",
        ),
        "--show-vol-targeted-growth-criteria-source-blocker-review": (
            "show_vol_targeted_growth_criteria_source_blocker_review",
            "Executable-ticket criteria source blocker review",
        ),
        "--vol-targeted-growth-criteria-resolution-plan-blocker-review": (
            "generate_vol_targeted_growth_criteria_resolution_plan_blocker_review",
            "Executable-ticket criteria resolution plan blocker review",
        ),
        "--show-vol-targeted-growth-criteria-resolution-plan-blocker-review": (
            "show_vol_targeted_growth_criteria_resolution_plan_blocker_review",
            "Executable-ticket criteria resolution plan blocker review",
        ),
        "--vol-targeted-growth-approval-criteria-not-approval-blocker-review": (
            "generate_vol_targeted_growth_approval_criteria_not_approval_blocker_review",
            "Executable-ticket approval criteria blocker review",
        ),
        "--show-vol-targeted-growth-approval-criteria-not-approval-blocker-review": (
            "show_vol_targeted_growth_approval_criteria_not_approval_blocker_review",
            "Executable-ticket approval criteria blocker review",
        ),
        "--vol-targeted-growth-criteria-blocker-specific-review-rollup": (
            "generate_vol_targeted_growth_criteria_blocker_specific_review_rollup",
            "Executable-ticket criteria blocker specific review rollup",
        ),
        "--show-vol-targeted-growth-criteria-blocker-specific-review-rollup": (
            "show_vol_targeted_growth_criteria_blocker_specific_review_rollup",
            "Executable-ticket criteria blocker specific review rollup",
        ),
    }
    if argv and argv[0] in blocker_specific_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_executable_ticket_blocker_specific_reviews as blocker_reviews

        function_name, label = blocker_specific_routes[argv[0]]
        result = getattr(blocker_reviews, function_name)()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    closeout_candidate_routes = {
        "--vol-targeted-growth-criteria-source-closeout-candidate-review": "generate_vol_targeted_growth_criteria_source_closeout_candidate_review",
        "--show-vol-targeted-growth-criteria-source-closeout-candidate-review": "show_vol_targeted_growth_criteria_source_closeout_candidate_review",
        "--vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review": "generate_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review",
        "--show-vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review": "show_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review",
        "--vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review": "generate_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review",
        "--show-vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review": "show_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review",
        "--vol-targeted-growth-criteria-closeout-candidate-review-rollup": "generate_vol_targeted_growth_criteria_closeout_candidate_review_rollup",
        "--show-vol-targeted-growth-criteria-closeout-candidate-review-rollup": "show_vol_targeted_growth_criteria_closeout_candidate_review_rollup",
    }
    if argv and argv[0] in closeout_candidate_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_executable_ticket_closeout_candidate_reviews as candidate_reviews

        result = getattr(candidate_reviews, closeout_candidate_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    approval_wording_routes = {
        "--vol-targeted-growth-criteria-source-closeout-approval-wording": "generate_vol_targeted_growth_criteria_source_closeout_approval_wording",
        "--show-vol-targeted-growth-criteria-source-closeout-approval-wording": "show_vol_targeted_growth_criteria_source_closeout_approval_wording",
        "--vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording": "generate_vol_targeted_growth_criteria_resolution_plan_closeout_approval_wording",
        "--show-vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording": "show_vol_targeted_growth_criteria_resolution_plan_closeout_approval_wording",
        "--vol-targeted-growth-approval-criteria-closeout-approval-wording": "generate_vol_targeted_growth_approval_criteria_closeout_approval_wording",
        "--show-vol-targeted-growth-approval-criteria-closeout-approval-wording": "show_vol_targeted_growth_approval_criteria_closeout_approval_wording",
        "--vol-targeted-growth-final-ticket-blockers-closeout-approval-wording": "generate_vol_targeted_growth_final_ticket_blockers_closeout_approval_wording",
        "--show-vol-targeted-growth-final-ticket-blockers-closeout-approval-wording": "show_vol_targeted_growth_final_ticket_blockers_closeout_approval_wording",
    }
    if argv and argv[0] in approval_wording_routes and len(argv) == 1:
        if "final-ticket-blockers" in argv[0]:
            from trading_bot.research import vol_targeted_growth_final_ticket_blockers_closeout as approval_wording
        elif "criteria-resolution-plan" in argv[0]:
            from trading_bot.research import vol_targeted_growth_criteria_resolution_plan_closeout_approval_wording as approval_wording
        elif "approval-criteria" in argv[0]:
            from trading_bot.research import vol_targeted_growth_approval_criteria_closeout_approval_wording as approval_wording
        else:
            from trading_bot.research import vol_targeted_growth_criteria_source_closeout_approval_wording as approval_wording

        result = getattr(approval_wording, approval_wording_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    closeout_record_routes = {
        "--vol-targeted-growth-criteria-source-closeout-record": "generate_vol_targeted_growth_criteria_source_closeout_record",
        "--show-vol-targeted-growth-criteria-source-closeout-record": "show_vol_targeted_growth_criteria_source_closeout_record",
        "--vol-targeted-growth-criteria-resolution-plan-closeout-record": "generate_vol_targeted_growth_criteria_resolution_plan_closeout_record",
        "--show-vol-targeted-growth-criteria-resolution-plan-closeout-record": "show_vol_targeted_growth_criteria_resolution_plan_closeout_record",
        "--vol-targeted-growth-approval-criteria-closeout-record": "generate_vol_targeted_growth_approval_criteria_closeout_record",
        "--show-vol-targeted-growth-approval-criteria-closeout-record": "show_vol_targeted_growth_approval_criteria_closeout_record",
        "--vol-targeted-growth-final-ticket-blockers-closeout-record": "generate_vol_targeted_growth_final_ticket_blockers_closeout_record",
        "--show-vol-targeted-growth-final-ticket-blockers-closeout-record": "show_vol_targeted_growth_final_ticket_blockers_closeout_record",
    }
    if argv and argv[0] in closeout_record_routes and len(argv) == 1:
        if "final-ticket-blockers" in argv[0]:
            from trading_bot.research import vol_targeted_growth_final_ticket_blockers_closeout as closeout_record
        elif "criteria-resolution-plan" in argv[0]:
            from trading_bot.research import vol_targeted_growth_criteria_resolution_plan_closeout_record as closeout_record
        elif "approval-criteria" in argv[0]:
            from trading_bot.research import vol_targeted_growth_approval_criteria_closeout_record as closeout_record
        else:
            from trading_bot.research import vol_targeted_growth_criteria_source_closeout_record as closeout_record

        result = getattr(closeout_record, closeout_record_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--paper-live-f6-f7-audit"]:
        from trading_bot.research.paper_live_f6_f7_audit import generate_paper_live_f6_f7_audit

        result = generate_paper_live_f6_f7_audit()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-f6-f7-audit"]:
        from trading_bot.research.paper_live_f6_f7_audit import show_paper_live_f6_f7_audit

        code, lines = show_paper_live_f6_f7_audit()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-promotion-ladder-design"]:
        from trading_bot.research.paper_live_promotion_ladder_design import (
            generate_paper_live_promotion_ladder_design,
        )

        result = generate_paper_live_promotion_ladder_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-promotion-ladder-design"]:
        from trading_bot.research.paper_live_promotion_ladder_design import (
            show_paper_live_promotion_ladder_design,
        )

        code, lines = show_paper_live_promotion_ladder_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-promotion-ladder-status"]:
        from trading_bot.research.paper_live_promotion_ladder_status import (
            generate_paper_live_promotion_ladder_status,
        )

        result = generate_paper_live_promotion_ladder_status()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-promotion-ladder-status"]:
        from trading_bot.research.paper_live_promotion_ladder_status import (
            show_paper_live_promotion_ladder_status,
        )

        code, lines = show_paper_live_promotion_ladder_status()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-f7-accounting-proof"]:
        from trading_bot.research.paper_live_f7_accounting_proof import (
            generate_paper_live_f7_accounting_proof,
        )

        result = generate_paper_live_f7_accounting_proof()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-f7-accounting-proof"]:
        from trading_bot.research.paper_live_f7_accounting_proof import (
            show_paper_live_f7_accounting_proof,
        )

        code, lines = show_paper_live_f7_accounting_proof()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-next-ladder-candidate-scope"]:
        from trading_bot.research.paper_live_next_ladder_candidate_scope import (
            generate_paper_live_next_ladder_candidate_scope,
        )

        result = generate_paper_live_next_ladder_candidate_scope()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-next-ladder-candidate-scope"]:
        from trading_bot.research.paper_live_next_ladder_candidate_scope import (
            show_paper_live_next_ladder_candidate_scope,
        )

        code, lines = show_paper_live_next_ladder_candidate_scope()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-defensive-sleeve-ladder-scope-review"]:
        from trading_bot.research.paper_live_defensive_sleeve_ladder_scope_review import (
            generate_paper_live_defensive_sleeve_ladder_scope_review,
        )

        result = generate_paper_live_defensive_sleeve_ladder_scope_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-defensive-sleeve-ladder-scope-review"]:
        from trading_bot.research.paper_live_defensive_sleeve_ladder_scope_review import (
            show_paper_live_defensive_sleeve_ladder_scope_review,
        )

        code, lines = show_paper_live_defensive_sleeve_ladder_scope_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-defensive-sleeve-manual-review"]:
        from trading_bot.research.paper_live_defensive_sleeve_manual_review import (
            generate_paper_live_defensive_sleeve_manual_review,
        )

        result = generate_paper_live_defensive_sleeve_manual_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-defensive-sleeve-manual-review"]:
        from trading_bot.research.paper_live_defensive_sleeve_manual_review import (
            show_paper_live_defensive_sleeve_manual_review,
        )

        code, lines = show_paper_live_defensive_sleeve_manual_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-defensive-sleeve-preview-readiness"]:
        from trading_bot.research.paper_live_defensive_sleeve_preview_readiness import (
            generate_paper_live_defensive_sleeve_preview_readiness,
        )

        result = generate_paper_live_defensive_sleeve_preview_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-defensive-sleeve-preview-readiness"]:
        from trading_bot.research.paper_live_defensive_sleeve_preview_readiness import (
            show_paper_live_defensive_sleeve_preview_readiness,
        )

        code, lines = show_paper_live_defensive_sleeve_preview_readiness()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-defensive-sleeve-evidence-quality"]:
        from trading_bot.research.paper_live_defensive_sleeve_evidence_quality import (
            generate_paper_live_defensive_sleeve_evidence_quality,
        )

        result = generate_paper_live_defensive_sleeve_evidence_quality()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-defensive-sleeve-evidence-quality"]:
        from trading_bot.research.paper_live_defensive_sleeve_evidence_quality import (
            show_paper_live_defensive_sleeve_evidence_quality,
        )

        code, lines = show_paper_live_defensive_sleeve_evidence_quality()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-multi-sleeve-roadmap"]:
        from trading_bot.research.paper_live_multi_sleeve_roadmap import generate_paper_live_multi_sleeve_roadmap

        result = generate_paper_live_multi_sleeve_roadmap()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-multi-sleeve-roadmap"]:
        from trading_bot.research.paper_live_multi_sleeve_roadmap import show_paper_live_multi_sleeve_roadmap

        code, lines = show_paper_live_multi_sleeve_roadmap()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-next-phase-backlog"]:
        from trading_bot.research.paper_live_next_phase_backlog import generate_paper_live_next_phase_backlog

        result = generate_paper_live_next_phase_backlog()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-next-phase-backlog"]:
        from trading_bot.research.paper_live_next_phase_backlog import show_paper_live_next_phase_backlog

        code, lines = show_paper_live_next_phase_backlog()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-multi-sleeve-evidence-gap"]:
        from trading_bot.research.paper_live_multi_sleeve_evidence_gap import (
            generate_paper_live_multi_sleeve_evidence_gap,
        )

        result = generate_paper_live_multi_sleeve_evidence_gap()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-multi-sleeve-evidence-gap"]:
        from trading_bot.research.paper_live_multi_sleeve_evidence_gap import (
            show_paper_live_multi_sleeve_evidence_gap,
        )

        code, lines = show_paper_live_multi_sleeve_evidence_gap()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-high-growth-evidence-gap"]:
        from trading_bot.research.paper_live_high_growth_evidence_gap import (
            generate_paper_live_high_growth_evidence_gap,
        )

        result = generate_paper_live_high_growth_evidence_gap()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-high-growth-evidence-gap"]:
        from trading_bot.research.paper_live_high_growth_evidence_gap import (
            show_paper_live_high_growth_evidence_gap,
        )

        code, lines = show_paper_live_high_growth_evidence_gap()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-high-growth-evidence-quality"]:
        from trading_bot.research.paper_live_high_growth_evidence_quality import (
            generate_paper_live_high_growth_evidence_quality,
        )

        result = generate_paper_live_high_growth_evidence_quality()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-high-growth-evidence-quality"]:
        from trading_bot.research.paper_live_high_growth_evidence_quality import (
            show_paper_live_high_growth_evidence_quality,
        )

        code, lines = show_paper_live_high_growth_evidence_quality()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-live-high-growth-manual-review-decision"]:
        from trading_bot.research.paper_live_high_growth_manual_review_decision import (
            generate_paper_live_high_growth_manual_review_decision,
        )

        result = generate_paper_live_high_growth_manual_review_decision()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-live-high-growth-manual-review-decision"]:
        from trading_bot.research.paper_live_high_growth_manual_review_decision import (
            show_paper_live_high_growth_manual_review_decision,
        )

        code, lines = show_paper_live_high_growth_manual_review_decision()
        for line in lines:
            print(line)
        return (code)
    if "--qqq100-paper-postcheck" in argv:
        from trading_bot.research.qqq100_paper_postcheck import generate_qqq100_paper_postcheck

        allowed = {"--qqq100-paper-postcheck", "--confirm-readonly-alpaca-check"}
        if not set(argv).issubset(allowed):
            print("--qqq100-paper-postcheck only accepts --confirm-readonly-alpaca-check.")
            return (2)
        result = generate_qqq100_paper_postcheck(
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in argv
        )
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-paper-postcheck"]:
        from trading_bot.research.qqq100_paper_postcheck import show_qqq100_paper_postcheck

        code, lines = show_qqq100_paper_postcheck()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-repeat-alignment-workflow-design"]:
        from trading_bot.research.qqq100_repeat_alignment_workflow_design import (
            generate_qqq100_repeat_alignment_workflow_design,
        )

        result = generate_qqq100_repeat_alignment_workflow_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-repeat-alignment-workflow-design"]:
        from trading_bot.research.qqq100_repeat_alignment_workflow_design import (
            show_qqq100_repeat_alignment_workflow_design,
        )

        code, lines = show_qqq100_repeat_alignment_workflow_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-strategy-monitor"]:
        from trading_bot.research.multi_sleeve_strategy_monitor import generate_multi_sleeve_strategy_monitor

        result = generate_multi_sleeve_strategy_monitor()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-strategy-monitor"]:
        from trading_bot.research.multi_sleeve_strategy_monitor import show_multi_sleeve_strategy_monitor

        code, lines = show_multi_sleeve_strategy_monitor()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--sleeve-research-scoreboard"]:
        from trading_bot.research.sleeve_research_scoreboard import generate_sleeve_research_scoreboard

        result = generate_sleeve_research_scoreboard()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-sleeve-research-scoreboard"]:
        from trading_bot.research.sleeve_research_scoreboard import show_sleeve_research_scoreboard

        code, lines = show_sleeve_research_scoreboard()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--codex-qqq-defensive-crash-gate-research-pack"]:
        from trading_bot.research.codex_qqq_defensive_crash_gate_research_pack import (
            generate_codex_qqq_defensive_crash_gate_research_pack,
        )

        result = generate_codex_qqq_defensive_crash_gate_research_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-codex-qqq-defensive-crash-gate-research-pack"]:
        from trading_bot.research.codex_qqq_defensive_crash_gate_research_pack import (
            show_codex_qqq_defensive_crash_gate_research_pack,
        )

        code, lines = show_codex_qqq_defensive_crash_gate_research_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--sleeve-return-streams"]:
        from trading_bot.research.sleeve_return_streams import generate_sleeve_return_streams

        result = generate_sleeve_return_streams()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-sleeve-return-streams"]:
        from trading_bot.research.sleeve_return_streams import show_sleeve_return_streams

        code, lines = show_sleeve_return_streams()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-stream-reconciliation"]:
        from trading_bot.research.qqq100_stream_reconciliation import generate_qqq100_stream_reconciliation

        result = generate_qqq100_stream_reconciliation()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-stream-reconciliation"]:
        from trading_bot.research.qqq100_stream_reconciliation import show_qqq100_stream_reconciliation

        code, lines = show_qqq100_stream_reconciliation()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--qqq100-benchmark-inputs-report"]:
        from trading_bot.research.qqq100_benchmark_inputs import generate_qqq100_benchmark_inputs_report

        result = generate_qqq100_benchmark_inputs_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-qqq100-benchmark-inputs"]:
        from trading_bot.research.qqq100_benchmark_inputs import show_qqq100_benchmark_inputs

        code, lines = show_qqq100_benchmark_inputs()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-return-streams"]:
        from trading_bot.research.high_growth_return_streams import generate_high_growth_return_streams

        result = generate_high_growth_return_streams()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-return-streams"]:
        from trading_bot.research.high_growth_return_streams import show_high_growth_return_streams

        code, lines = show_high_growth_return_streams()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--crypto-return-streams"]:
        from trading_bot.research.crypto_return_streams import generate_crypto_return_streams

        result = generate_crypto_return_streams()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-crypto-return-streams"]:
        from trading_bot.research.crypto_return_streams import show_crypto_return_streams

        code, lines = show_crypto_return_streams()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-portfolio-backtest"]:
        from trading_bot.research.multi_sleeve_portfolio_backtest import generate_multi_sleeve_portfolio_backtest

        result = generate_multi_sleeve_portfolio_backtest()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-portfolio-backtest"]:
        from trading_bot.research.multi_sleeve_portfolio_backtest import show_multi_sleeve_portfolio_backtest

        code, lines = show_multi_sleeve_portfolio_backtest()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-robustness"]:
        from trading_bot.research.multi_sleeve_robustness import generate_multi_sleeve_robustness

        result = generate_multi_sleeve_robustness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-robustness"]:
        from trading_bot.research.multi_sleeve_robustness import show_multi_sleeve_robustness

        code, lines = show_multi_sleeve_robustness()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-crypto-review"]:
        from trading_bot.research.multi_sleeve_crypto_review import generate_multi_sleeve_crypto_review

        result = generate_multi_sleeve_crypto_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-crypto-review"]:
        from trading_bot.research.multi_sleeve_crypto_review import show_multi_sleeve_crypto_review

        code, lines = show_multi_sleeve_crypto_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-crypto-containment-review"]:
        from trading_bot.research.multi_sleeve_crypto_containment import (
            generate_multi_sleeve_crypto_containment_review,
        )

        result = generate_multi_sleeve_crypto_containment_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-crypto-containment-review"]:
        from trading_bot.research.multi_sleeve_crypto_containment import (
            show_multi_sleeve_crypto_containment_review,
        )

        code, lines = show_multi_sleeve_crypto_containment_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--show-current-research-state"]:
        from trading_bot.research.current_research_state import show_current_research_state

        code, lines = show_current_research_state()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-allocation-policy-review"]:
        from trading_bot.research.multi_sleeve_allocation_policy import generate_multi_sleeve_allocation_policy_review

        result = generate_multi_sleeve_allocation_policy_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-allocation-policy-review"]:
        from trading_bot.research.multi_sleeve_allocation_policy import show_multi_sleeve_allocation_policy_review

        code, lines = show_multi_sleeve_allocation_policy_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-weight-sensitivity"]:
        from trading_bot.research.multi_sleeve_weight_sensitivity import generate_multi_sleeve_weight_sensitivity

        result = generate_multi_sleeve_weight_sensitivity()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-weight-sensitivity"]:
        from trading_bot.research.multi_sleeve_weight_sensitivity import show_multi_sleeve_weight_sensitivity

        code, lines = show_multi_sleeve_weight_sensitivity()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-higher-growth-review"]:
        from trading_bot.research.multi_sleeve_higher_growth_review import generate_multi_sleeve_higher_growth_review

        result = generate_multi_sleeve_higher_growth_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-higher-growth-review"]:
        from trading_bot.research.multi_sleeve_higher_growth_review import show_multi_sleeve_higher_growth_review

        code, lines = show_multi_sleeve_higher_growth_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-research-lead-decision"]:
        from trading_bot.research.multi_sleeve_research_lead_decision import (
            generate_multi_sleeve_research_lead_decision,
        )

        result = generate_multi_sleeve_research_lead_decision()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-research-lead-decision"]:
        from trading_bot.research.multi_sleeve_research_lead_decision import (
            show_multi_sleeve_research_lead_decision,
        )

        code, lines = show_multi_sleeve_research_lead_decision()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-lead-state-refresh"]:
        from trading_bot.research.multi_sleeve_lead_state import generate_multi_sleeve_lead_state

        result = generate_multi_sleeve_lead_state()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-lead-state"]:
        from trading_bot.research.multi_sleeve_lead_state import show_multi_sleeve_lead_state

        code, lines = show_multi_sleeve_lead_state()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--multi-sleeve-high-growth-drawdown-decomposition"]:
        from trading_bot.research.multi_sleeve_high_growth_drawdown import (
            generate_multi_sleeve_high_growth_drawdown_decomposition,
        )

        result = generate_multi_sleeve_high_growth_drawdown_decomposition()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-multi-sleeve-high-growth-drawdown-decomposition"]:
        from trading_bot.research.multi_sleeve_high_growth_drawdown import (
            show_multi_sleeve_high_growth_drawdown_decomposition,
        )

        code, lines = show_multi_sleeve_high_growth_drawdown_decomposition()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-sleeve-quality-review"]:
        from trading_bot.research.high_growth_sleeve_quality import generate_high_growth_sleeve_quality_review

        result = generate_high_growth_sleeve_quality_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-sleeve-quality-review"]:
        from trading_bot.research.high_growth_sleeve_quality import show_high_growth_sleeve_quality_review

        code, lines = show_high_growth_sleeve_quality_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-component-attribution"]:
        from trading_bot.research.high_growth_component_attribution import generate_high_growth_component_attribution

        result = generate_high_growth_component_attribution()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-component-attribution"]:
        from trading_bot.research.high_growth_component_attribution import show_high_growth_component_attribution

        code, lines = show_high_growth_component_attribution()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-component-streams"]:
        from trading_bot.research.high_growth_component_streams import generate_high_growth_component_streams

        result = generate_high_growth_component_streams()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-component-streams"]:
        from trading_bot.research.high_growth_component_streams import show_high_growth_component_streams

        code, lines = show_high_growth_component_streams()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-sleeve-concentration-review"]:
        from trading_bot.research.high_growth_sleeve_concentration import generate_high_growth_sleeve_concentration_review

        result = generate_high_growth_sleeve_concentration_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-sleeve-concentration-review"]:
        from trading_bot.research.high_growth_sleeve_concentration import show_high_growth_sleeve_concentration_review

        code, lines = show_high_growth_sleeve_concentration_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-research-checkpoint"]:
        from trading_bot.research.high_growth_research_checkpoint import generate_high_growth_research_checkpoint

        result = generate_high_growth_research_checkpoint()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-research-checkpoint"]:
        from trading_bot.research.high_growth_research_checkpoint import show_high_growth_research_checkpoint

        code, lines = show_high_growth_research_checkpoint()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--paper-execution-state-summary"]:
        from trading_bot.research.paper_execution_state_summary import generate_paper_execution_state_summary

        result = generate_paper_execution_state_summary()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-paper-execution-state-summary"]:
        from trading_bot.research.paper_execution_state_summary import show_paper_execution_state_summary

        code, lines = show_paper_execution_state_summary()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-lab"]:
        from trading_bot.research.high_growth_stock_lab import generate_high_growth_stock_lab

        result = generate_high_growth_stock_lab()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-lab"]:
        from trading_bot.research.high_growth_stock_lab import show_high_growth_stock_lab

        code, lines = show_high_growth_stock_lab()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-universe-expansion-report"]:
        from trading_bot.research.high_growth_stock_universe_expansion import (
            generate_high_growth_stock_universe_expansion_report,
        )

        result = generate_high_growth_stock_universe_expansion_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-universe-expansion-report"]:
        from trading_bot.research.high_growth_stock_universe_expansion import (
            show_high_growth_stock_universe_expansion_report,
        )

        code, lines = show_high_growth_stock_universe_expansion_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-drawdown-control-report"]:
        from trading_bot.research.high_growth_stock_drawdown_control import (
            generate_high_growth_stock_drawdown_control_report,
        )

        result = generate_high_growth_stock_drawdown_control_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-drawdown-control-report"]:
        from trading_bot.research.high_growth_stock_drawdown_control import (
            show_high_growth_stock_drawdown_control_report,
        )

        code, lines = show_high_growth_stock_drawdown_control_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-lead-decision-report"]:
        from trading_bot.research.high_growth_stock_lead_decision import (
            generate_high_growth_stock_lead_decision_report,
        )

        result = generate_high_growth_stock_lead_decision_report()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-lead-decision-report"]:
        from trading_bot.research.high_growth_stock_lead_decision import (
            show_high_growth_stock_lead_decision_report,
        )

        code, lines = show_high_growth_stock_lead_decision_report()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-manual-review-pack"]:
        from trading_bot.research.high_growth_stock_manual_review_pack import (
            generate_high_growth_stock_manual_review_pack,
        )

        result = generate_high_growth_stock_manual_review_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-manual-review-pack"]:
        from trading_bot.research.high_growth_stock_manual_review_pack import (
            show_high_growth_stock_manual_review_pack,
        )

        code, lines = show_high_growth_stock_manual_review_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-risk-review-pack"]:
        from trading_bot.research.high_growth_stock_risk_review_pack import (
            generate_high_growth_stock_risk_review_pack,
        )

        result = generate_high_growth_stock_risk_review_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-risk-review-pack"]:
        from trading_bot.research.high_growth_stock_risk_review_pack import (
            show_high_growth_stock_risk_review_pack,
        )

        code, lines = show_high_growth_stock_risk_review_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-risk-evidence-review"]:
        from trading_bot.research.high_growth_stock_risk_evidence_review import (
            generate_high_growth_stock_risk_evidence_review,
        )

        result = generate_high_growth_stock_risk_evidence_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-risk-evidence-review"]:
        from trading_bot.research.high_growth_stock_risk_evidence_review import (
            show_high_growth_stock_risk_evidence_review,
        )

        code, lines = show_high_growth_stock_risk_evidence_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-branch-decision-checkpoint"]:
        from trading_bot.research.high_growth_stock_branch_decision_checkpoint import (
            generate_high_growth_stock_branch_decision_checkpoint,
        )

        result = generate_high_growth_stock_branch_decision_checkpoint()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-branch-decision-checkpoint"]:
        from trading_bot.research.high_growth_stock_branch_decision_checkpoint import (
            show_high_growth_stock_branch_decision_checkpoint,
        )

        code, lines = show_high_growth_stock_branch_decision_checkpoint()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-stock-final-validation-pack"]:
        from trading_bot.research.high_growth_stock_final_validation_pack import (
            generate_high_growth_stock_final_validation_pack,
        )

        result = generate_high_growth_stock_final_validation_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-stock-final-validation-pack"]:
        from trading_bot.research.high_growth_stock_final_validation_pack import (
            show_high_growth_stock_final_validation_pack,
        )

        code, lines = show_high_growth_stock_final_validation_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--high-growth-strategy-discovery-sprint"]:
        from trading_bot.research.high_growth_strategy_discovery_sprint import (
            generate_high_growth_strategy_discovery_sprint,
        )

        result = generate_high_growth_strategy_discovery_sprint()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-high-growth-strategy-discovery-sprint"]:
        from trading_bot.research.high_growth_strategy_discovery_sprint import (
            show_high_growth_strategy_discovery_sprint,
        )

        code, lines = show_high_growth_strategy_discovery_sprint()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--higher-growth-preview-readiness-pack"]:
        from trading_bot.research.higher_growth_preview_readiness_pack import (
            generate_higher_growth_preview_readiness_pack,
        )

        result = generate_higher_growth_preview_readiness_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-higher-growth-preview-readiness-pack"]:
        from trading_bot.research.higher_growth_preview_readiness_pack import (
            show_higher_growth_preview_readiness_pack,
        )

        code, lines = show_higher_growth_preview_readiness_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--higher-growth-candidate-selection-decision"]:
        from trading_bot.research.higher_growth_candidate_selection_decision import (
            generate_higher_growth_candidate_selection_decision,
        )

        result = generate_higher_growth_candidate_selection_decision()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-higher-growth-candidate-selection-decision"]:
        from trading_bot.research.higher_growth_candidate_selection_decision import (
            show_higher_growth_candidate_selection_decision,
        )

        code, lines = show_higher_growth_candidate_selection_decision()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--higher-growth-preview-design"]:
        from trading_bot.research.higher_growth_preview_design import generate_higher_growth_preview_design

        result = generate_higher_growth_preview_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-higher-growth-preview-design"]:
        from trading_bot.research.higher_growth_preview_design import show_higher_growth_preview_design

        code, lines = show_higher_growth_preview_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-research-sprint"]:
        from trading_bot.research.vol_targeted_growth_research_sprint import (
            generate_vol_targeted_growth_research_sprint,
        )

        result = generate_vol_targeted_growth_research_sprint()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-research-sprint"]:
        from trading_bot.research.vol_targeted_growth_research_sprint import (
            show_vol_targeted_growth_research_sprint,
        )

        code, lines = show_vol_targeted_growth_research_sprint()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-manual-review-pack"]:
        from trading_bot.research.vol_targeted_growth_manual_review_pack import (
            generate_vol_targeted_growth_manual_review_pack,
        )

        result = generate_vol_targeted_growth_manual_review_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-manual-review-pack"]:
        from trading_bot.research.vol_targeted_growth_manual_review_pack import (
            show_vol_targeted_growth_manual_review_pack,
        )

        code, lines = show_vol_targeted_growth_manual_review_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-robustness-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_robustness_checkpoint import (
            generate_vol_targeted_growth_robustness_checkpoint,
        )

        result = generate_vol_targeted_growth_robustness_checkpoint()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-robustness-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_robustness_checkpoint import (
            show_vol_targeted_growth_robustness_checkpoint,
        )

        code, lines = show_vol_targeted_growth_robustness_checkpoint()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-nearby-variants-review"]:
        from trading_bot.research.vol_targeted_growth_nearby_variants_review import (
            generate_vol_targeted_growth_nearby_variants_review,
        )

        result = generate_vol_targeted_growth_nearby_variants_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-nearby-variants-review"]:
        from trading_bot.research.vol_targeted_growth_nearby_variants_review import (
            show_vol_targeted_growth_nearby_variants_review,
        )

        code, lines = show_vol_targeted_growth_nearby_variants_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-preview-readiness-decision"]:
        from trading_bot.research.vol_targeted_growth_preview_readiness_decision import (
            generate_vol_targeted_growth_preview_readiness_decision,
        )

        result = generate_vol_targeted_growth_preview_readiness_decision()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-preview-readiness-decision"]:
        from trading_bot.research.vol_targeted_growth_preview_readiness_decision import (
            show_vol_targeted_growth_preview_readiness_decision,
        )

        code, lines = show_vol_targeted_growth_preview_readiness_decision()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-preview-design"]:
        from trading_bot.research.vol_targeted_growth_preview_design import (
            generate_vol_targeted_growth_preview_design,
        )

        result = generate_vol_targeted_growth_preview_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-preview-design"]:
        from trading_bot.research.vol_targeted_growth_preview_design import (
            show_vol_targeted_growth_preview_design,
        )

        code, lines = show_vol_targeted_growth_preview_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-preview-signal"]:
        from trading_bot.research.vol_targeted_growth_preview_signal import (
            generate_vol_targeted_growth_preview_signal,
        )

        result = generate_vol_targeted_growth_preview_signal()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-preview-signal"]:
        from trading_bot.research.vol_targeted_growth_preview_signal import (
            show_vol_targeted_growth_preview_signal,
        )

        code, lines = show_vol_targeted_growth_preview_signal()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-action-preview-design"]:
        from trading_bot.research.vol_targeted_growth_action_preview_design import (
            generate_vol_targeted_growth_action_preview_design,
        )

        result = generate_vol_targeted_growth_action_preview_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-action-preview-design"]:
        from trading_bot.research.vol_targeted_growth_action_preview_design import (
            show_vol_targeted_growth_action_preview_design,
        )

        code, lines = show_vol_targeted_growth_action_preview_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-action-preview"]:
        from trading_bot.research.vol_targeted_growth_action_preview import (
            generate_vol_targeted_growth_action_preview,
        )

        result = generate_vol_targeted_growth_action_preview()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-action-preview"]:
        from trading_bot.research.vol_targeted_growth_action_preview import (
            show_vol_targeted_growth_action_preview,
        )

        code, lines = show_vol_targeted_growth_action_preview()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-action-preview-quality-gate"]:
        from trading_bot.research.vol_targeted_growth_action_preview_quality_gate import (
            generate_vol_targeted_growth_action_preview_quality_gate,
        )

        result = generate_vol_targeted_growth_action_preview_quality_gate()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-action-preview-quality-gate"]:
        from trading_bot.research.vol_targeted_growth_action_preview_quality_gate import (
            show_vol_targeted_growth_action_preview_quality_gate,
        )

        code, lines = show_vol_targeted_growth_action_preview_quality_gate()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-broker-position-comparison-design"]:
        from trading_bot.research.vol_targeted_growth_broker_position_comparison_design import (
            generate_vol_targeted_growth_broker_position_comparison_design,
        )

        result = generate_vol_targeted_growth_broker_position_comparison_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-broker-position-comparison-design"]:
        from trading_bot.research.vol_targeted_growth_broker_position_comparison_design import (
            show_vol_targeted_growth_broker_position_comparison_design,
        )

        code, lines = show_vol_targeted_growth_broker_position_comparison_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-portfolio-risk-review"]:
        from trading_bot.research.vol_targeted_growth_portfolio_risk_review import (
            generate_vol_targeted_growth_portfolio_risk_review,
        )

        result = generate_vol_targeted_growth_portfolio_risk_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-portfolio-risk-review"]:
        from trading_bot.research.vol_targeted_growth_portfolio_risk_review import (
            show_vol_targeted_growth_portfolio_risk_review,
        )

        code, lines = show_vol_targeted_growth_portfolio_risk_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-portfolio-risk-policy-design"]:
        from trading_bot.research.vol_targeted_growth_portfolio_risk_policy_design import (
            generate_vol_targeted_growth_portfolio_risk_policy_design,
        )

        result = generate_vol_targeted_growth_portfolio_risk_policy_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-portfolio-risk-policy-design"]:
        from trading_bot.research.vol_targeted_growth_portfolio_risk_policy_design import (
            show_vol_targeted_growth_portfolio_risk_policy_design,
        )

        code, lines = show_vol_targeted_growth_portfolio_risk_policy_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-paper-live-decision"]:
        from trading_bot.research.vol_targeted_growth_paper_live_decision import (
            generate_vol_targeted_growth_paper_live_decision,
        )

        result = generate_vol_targeted_growth_paper_live_decision()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-paper-live-decision"]:
        from trading_bot.research.vol_targeted_growth_paper_live_decision import (
            show_vol_targeted_growth_paper_live_decision,
        )

        code, lines = show_vol_targeted_growth_paper_live_decision()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-broker-comparison-run-readiness"]:
        from trading_bot.research.vol_targeted_growth_broker_comparison_run_readiness import (
            generate_vol_targeted_growth_broker_comparison_run_readiness,
        )

        result = generate_vol_targeted_growth_broker_comparison_run_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-broker-comparison-run-readiness"]:
        from trading_bot.research.vol_targeted_growth_broker_comparison_run_readiness import (
            show_vol_targeted_growth_broker_comparison_run_readiness,
        )

        code, lines = show_vol_targeted_growth_broker_comparison_run_readiness()
        for line in lines:
            print(line)
        return (code)
    if "--vol-targeted-growth-broker-position-comparison" in argv:
        from trading_bot.research.vol_targeted_growth_broker_position_comparison import (
            generate_vol_targeted_growth_broker_position_comparison,
        )

        allowed = {"--vol-targeted-growth-broker-position-comparison", "--confirm-readonly-alpaca-check"}
        if not set(argv).issubset(allowed):
            print("--vol-targeted-growth-broker-position-comparison only accepts --confirm-readonly-alpaca-check.")
            return (2)
        result = generate_vol_targeted_growth_broker_position_comparison(
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in argv
        )
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-broker-position-comparison"]:
        from trading_bot.research.vol_targeted_growth_broker_position_comparison import (
            show_vol_targeted_growth_broker_position_comparison,
        )

        code, lines = show_vol_targeted_growth_broker_position_comparison()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-post-comparison-decision"]:
        from trading_bot.research.vol_targeted_growth_post_comparison_decision import (
            generate_vol_targeted_growth_post_comparison_decision,
        )

        result = generate_vol_targeted_growth_post_comparison_decision()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-post-comparison-decision"]:
        from trading_bot.research.vol_targeted_growth_post_comparison_decision import (
            show_vol_targeted_growth_post_comparison_decision,
        )

        code, lines = show_vol_targeted_growth_post_comparison_decision()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-stricter-paper-live-gate-design"]:
        from trading_bot.research.vol_targeted_growth_stricter_paper_live_gate_design import (
            generate_vol_targeted_growth_stricter_paper_live_gate_design,
        )

        result = generate_vol_targeted_growth_stricter_paper_live_gate_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-stricter-paper-live-gate-design"]:
        from trading_bot.research.vol_targeted_growth_stricter_paper_live_gate_design import (
            show_vol_targeted_growth_stricter_paper_live_gate_design,
        )

        code, lines = show_vol_targeted_growth_stricter_paper_live_gate_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-gate-review"]:
        from trading_bot.research.vol_targeted_growth_gate_review import (
            generate_vol_targeted_growth_gate_review,
        )

        result = generate_vol_targeted_growth_gate_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-gate-review"]:
        from trading_bot.research.vol_targeted_growth_gate_review import (
            show_vol_targeted_growth_gate_review,
        )

        code, lines = show_vol_targeted_growth_gate_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-candidate-discussion-blocker-checklist"]:
        from trading_bot.research.vol_targeted_growth_candidate_discussion_blocker_checklist import (
            generate_vol_targeted_growth_candidate_discussion_blocker_checklist,
        )

        result = generate_vol_targeted_growth_candidate_discussion_blocker_checklist()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-candidate-discussion-blocker-checklist"]:
        from trading_bot.research.vol_targeted_growth_candidate_discussion_blocker_checklist import (
            show_vol_targeted_growth_candidate_discussion_blocker_checklist,
        )

        code, lines = show_vol_targeted_growth_candidate_discussion_blocker_checklist()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-candidate-decision-record"]:
        from trading_bot.research.vol_targeted_growth_candidate_decision_record import (
            generate_vol_targeted_growth_candidate_decision_record,
        )

        result = generate_vol_targeted_growth_candidate_decision_record()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-candidate-decision-record"]:
        from trading_bot.research.vol_targeted_growth_candidate_decision_record import (
            show_vol_targeted_growth_candidate_decision_record,
        )

        code, lines = show_vol_targeted_growth_candidate_decision_record()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-candidate-discussion"]:
        from trading_bot.research.vol_targeted_growth_candidate_discussion import (
            generate_vol_targeted_growth_candidate_discussion,
        )

        result = generate_vol_targeted_growth_candidate_discussion()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-candidate-discussion"]:
        from trading_bot.research.vol_targeted_growth_candidate_discussion import (
            show_vol_targeted_growth_candidate_discussion,
        )

        code, lines = show_vol_targeted_growth_candidate_discussion()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-proposal-implementation-design"]:
        from trading_bot.research.vol_targeted_growth_proposal_implementation_design import (
            generate_vol_targeted_growth_proposal_implementation_design,
        )

        result = generate_vol_targeted_growth_proposal_implementation_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-proposal-implementation-design"]:
        from trading_bot.research.vol_targeted_growth_proposal_implementation_design import (
            show_vol_targeted_growth_proposal_implementation_design,
        )

        code, lines = show_vol_targeted_growth_proposal_implementation_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-proposal-preview-schema"]:
        from trading_bot.research.vol_targeted_growth_proposal_preview_schema import (
            generate_vol_targeted_growth_proposal_preview_schema,
        )

        result = generate_vol_targeted_growth_proposal_preview_schema()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-proposal-preview-schema"]:
        from trading_bot.research.vol_targeted_growth_proposal_preview_schema import (
            show_vol_targeted_growth_proposal_preview_schema,
        )

        code, lines = show_vol_targeted_growth_proposal_preview_schema()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-proposal-preview"]:
        from trading_bot.research.vol_targeted_growth_proposal_preview import (
            generate_vol_targeted_growth_proposal_preview,
        )

        result = generate_vol_targeted_growth_proposal_preview()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-proposal-preview"]:
        from trading_bot.research.vol_targeted_growth_proposal_preview import (
            show_vol_targeted_growth_proposal_preview,
        )

        code, lines = show_vol_targeted_growth_proposal_preview()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_review import (
            generate_vol_targeted_growth_seed_change_review,
        )

        result = generate_vol_targeted_growth_seed_change_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_review import (
            show_vol_targeted_growth_seed_change_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-evidence-pack"]:
        from trading_bot.research.vol_targeted_growth_seed_change_evidence_pack import (
            generate_vol_targeted_growth_seed_change_evidence_pack,
        )

        result = generate_vol_targeted_growth_seed_change_evidence_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-evidence-pack"]:
        from trading_bot.research.vol_targeted_growth_seed_change_evidence_pack import (
            show_vol_targeted_growth_seed_change_evidence_pack,
        )

        code, lines = show_vol_targeted_growth_seed_change_evidence_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-risk-reward-comparison"]:
        from trading_bot.research.vol_targeted_growth_seed_change_risk_reward_comparison import (
            generate_vol_targeted_growth_seed_change_risk_reward_comparison,
        )

        result = generate_vol_targeted_growth_seed_change_risk_reward_comparison()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-risk-reward-comparison"]:
        from trading_bot.research.vol_targeted_growth_seed_change_risk_reward_comparison import (
            show_vol_targeted_growth_seed_change_risk_reward_comparison,
        )

        code, lines = show_vol_targeted_growth_seed_change_risk_reward_comparison()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-drawdown-stress-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_drawdown_stress_review import (
            generate_vol_targeted_growth_seed_change_drawdown_stress_review,
        )

        result = generate_vol_targeted_growth_seed_change_drawdown_stress_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-drawdown-stress-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_drawdown_stress_review import (
            show_vol_targeted_growth_seed_change_drawdown_stress_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_drawdown_stress_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-cost-turnover-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_cost_turnover_review import (
            generate_vol_targeted_growth_seed_change_cost_turnover_review,
        )

        result = generate_vol_targeted_growth_seed_change_cost_turnover_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-cost-turnover-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_cost_turnover_review import (
            show_vol_targeted_growth_seed_change_cost_turnover_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_cost_turnover_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-split-stability-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_split_stability_review import (
            generate_vol_targeted_growth_seed_change_split_stability_review,
        )

        result = generate_vol_targeted_growth_seed_change_split_stability_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-split-stability-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_split_stability_review import (
            show_vol_targeted_growth_seed_change_split_stability_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_split_stability_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-component-sleeve-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            generate_vol_targeted_growth_seed_change_component_sleeve_review,
        )

        result = generate_vol_targeted_growth_seed_change_component_sleeve_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-component-sleeve-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            show_vol_targeted_growth_seed_change_component_sleeve_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_component_sleeve_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-action-preview-design"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            generate_vol_targeted_growth_seed_change_action_preview_design,
        )

        result = generate_vol_targeted_growth_seed_change_action_preview_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-action-preview-design"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            show_vol_targeted_growth_seed_change_action_preview_design,
        )

        code, lines = show_vol_targeted_growth_seed_change_action_preview_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-proposal-document"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            generate_vol_targeted_growth_seed_change_proposal_document,
        )

        result = generate_vol_targeted_growth_seed_change_proposal_document()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-proposal-document"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            show_vol_targeted_growth_seed_change_proposal_document,
        )

        code, lines = show_vol_targeted_growth_seed_change_proposal_document()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-broker-exposure-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            generate_vol_targeted_growth_seed_change_broker_exposure_review,
        )

        result = generate_vol_targeted_growth_seed_change_broker_exposure_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-broker-exposure-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            show_vol_targeted_growth_seed_change_broker_exposure_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_broker_exposure_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-manual-review-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_seed_change_manual_review_checkpoint import (
            generate_vol_targeted_growth_seed_change_manual_review_checkpoint,
        )

        result = generate_vol_targeted_growth_seed_change_manual_review_checkpoint()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-manual-review-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_seed_change_manual_review_checkpoint import (
            show_vol_targeted_growth_seed_change_manual_review_checkpoint,
        )

        code, lines = show_vol_targeted_growth_seed_change_manual_review_checkpoint()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-formal-seed-change-proposal"]:
        from trading_bot.research.vol_targeted_growth_formal_seed_change_proposal import (
            generate_vol_targeted_growth_formal_seed_change_proposal,
        )

        result = generate_vol_targeted_growth_formal_seed_change_proposal()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-formal-seed-change-proposal"]:
        from trading_bot.research.vol_targeted_growth_formal_seed_change_proposal import (
            show_vol_targeted_growth_formal_seed_change_proposal,
        )

        code, lines = show_vol_targeted_growth_formal_seed_change_proposal()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-manual-approval-record"]:
        from trading_bot.research.vol_targeted_growth_seed_change_manual_approval_record import (
            generate_vol_targeted_growth_seed_change_manual_approval_record,
        )

        result = generate_vol_targeted_growth_seed_change_manual_approval_record()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-manual-approval-record"]:
        from trading_bot.research.vol_targeted_growth_seed_change_manual_approval_record import (
            show_vol_targeted_growth_seed_change_manual_approval_record,
        )

        code, lines = show_vol_targeted_growth_seed_change_manual_approval_record()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-implementation-design"]:
        from trading_bot.research.vol_targeted_growth_seed_change_implementation_design import (
            generate_vol_targeted_growth_seed_change_implementation_design,
        )

        result = generate_vol_targeted_growth_seed_change_implementation_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-implementation-design"]:
        from trading_bot.research.vol_targeted_growth_seed_change_implementation_design import (
            show_vol_targeted_growth_seed_change_implementation_design,
        )

        code, lines = show_vol_targeted_growth_seed_change_implementation_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-seed-change-dry-run-diff"]:
        from trading_bot.research.vol_targeted_growth_seed_change_dry_run_diff import (
            generate_vol_targeted_growth_seed_change_dry_run_diff,
        )

        result = generate_vol_targeted_growth_seed_change_dry_run_diff()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-seed-change-dry-run-diff"]:
        from trading_bot.research.vol_targeted_growth_seed_change_dry_run_diff import (
            show_vol_targeted_growth_seed_change_dry_run_diff,
        )

        code, lines = show_vol_targeted_growth_seed_change_dry_run_diff()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-active-seed-readiness"]:
        from trading_bot.research.vol_targeted_growth_active_seed_readiness import (
            generate_vol_targeted_growth_active_seed_readiness,
        )

        result = generate_vol_targeted_growth_active_seed_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-active-seed-readiness"]:
        from trading_bot.research.vol_targeted_growth_active_seed_readiness import (
            show_vol_targeted_growth_active_seed_readiness,
        )

        code, lines = show_vol_targeted_growth_active_seed_readiness()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-paper-live-manual-approval-gate"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_paper_live_manual_approval_gate,
        )

        result = generate_vol_targeted_growth_paper_live_manual_approval_gate()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-paper-live-manual-approval-gate"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_paper_live_manual_approval_gate,
        )

        code, lines = show_vol_targeted_growth_paper_live_manual_approval_gate()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-paper-live-action-preview-pack"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_paper_live_action_preview_pack,
        )

        result = generate_vol_targeted_growth_paper_live_action_preview_pack()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-paper-live-action-preview-pack"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_paper_live_action_preview_pack,
        )

        code, lines = show_vol_targeted_growth_paper_live_action_preview_pack()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-broker-comparison-reconciliation"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_broker_comparison_reconciliation,
        )

        result = generate_vol_targeted_growth_broker_comparison_reconciliation()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-broker-comparison-reconciliation"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_broker_comparison_reconciliation,
        )

        code, lines = show_vol_targeted_growth_broker_comparison_reconciliation()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-paper-live-candidate-approval-record"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_paper_live_candidate_approval_record,
        )

        result = generate_vol_targeted_growth_paper_live_candidate_approval_record()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-paper-live-candidate-approval-record"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_paper_live_candidate_approval_record,
        )

        code, lines = show_vol_targeted_growth_paper_live_candidate_approval_record()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-allocation-cap-sleeve-mapping-policy"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy,
        )

        result = generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-allocation-cap-sleeve-mapping-policy"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_allocation_cap_sleeve_mapping_policy,
        )

        code, lines = show_vol_targeted_growth_allocation_cap_sleeve_mapping_policy()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-non-executable-target-position-plan"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_non_executable_target_position_plan,
        )

        result = generate_vol_targeted_growth_non_executable_target_position_plan()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-non-executable-target-position-plan"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_non_executable_target_position_plan,
        )

        code, lines = show_vol_targeted_growth_non_executable_target_position_plan()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-order-ticket-boundary-design"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_order_ticket_boundary_design,
        )

        result = generate_vol_targeted_growth_order_ticket_boundary_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-order-ticket-boundary-design"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_order_ticket_boundary_design,
        )

        code, lines = show_vol_targeted_growth_order_ticket_boundary_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-executable-ticket-prerequisites-review"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_executable_ticket_prerequisites_review,
        )

        result = generate_vol_targeted_growth_executable_ticket_prerequisites_review()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-executable-ticket-prerequisites-review"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_executable_ticket_prerequisites_review,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_prerequisites_review()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-executable-ticket-gap-list"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_gap_list import (
            generate_vol_targeted_growth_executable_ticket_gap_list,
        )

        result = generate_vol_targeted_growth_executable_ticket_gap_list()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-executable-ticket-gap-list"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_gap_list import (
            show_vol_targeted_growth_executable_ticket_gap_list,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_gap_list()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-manual-execution-design-approval-gate"]:
        from trading_bot.research.vol_targeted_growth_manual_execution_design_approval_gate import (
            generate_vol_targeted_growth_manual_execution_design_approval_gate,
        )

        result = generate_vol_targeted_growth_manual_execution_design_approval_gate()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-manual-execution-design-approval-gate"]:
        from trading_bot.research.vol_targeted_growth_manual_execution_design_approval_gate import (
            show_vol_targeted_growth_manual_execution_design_approval_gate,
        )

        code, lines = show_vol_targeted_growth_manual_execution_design_approval_gate()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-non-submitting-ticket-schema-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_schema_design import (
            generate_vol_targeted_growth_non_submitting_ticket_schema_design,
        )

        result = generate_vol_targeted_growth_non_submitting_ticket_schema_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-non-submitting-ticket-schema-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_schema_design import (
            show_vol_targeted_growth_non_submitting_ticket_schema_design,
        )

        code, lines = show_vol_targeted_growth_non_submitting_ticket_schema_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-non-submitting-ticket-instance-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_design import (
            generate_vol_targeted_growth_non_submitting_ticket_instance_design,
        )

        result = generate_vol_targeted_growth_non_submitting_ticket_instance_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-non-submitting-ticket-instance-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_design import (
            show_vol_targeted_growth_non_submitting_ticket_instance_design,
        )

        code, lines = show_vol_targeted_growth_non_submitting_ticket_instance_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-non-submitting-ticket-instance-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_checkpoint import (
            generate_vol_targeted_growth_non_submitting_ticket_instance_checkpoint,
        )

        result = generate_vol_targeted_growth_non_submitting_ticket_instance_checkpoint()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-non-submitting-ticket-instance-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_checkpoint import (
            show_vol_targeted_growth_non_submitting_ticket_instance_checkpoint,
        )

        code, lines = show_vol_targeted_growth_non_submitting_ticket_instance_checkpoint()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-non-submitting-ticket-instance-quality-gate"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_checkpoint import (
            generate_vol_targeted_growth_non_submitting_ticket_instance_quality_gate,
        )

        result = generate_vol_targeted_growth_non_submitting_ticket_instance_quality_gate()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-non-submitting-ticket-instance-quality-gate"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_checkpoint import (
            show_vol_targeted_growth_non_submitting_ticket_instance_quality_gate,
        )

        code, lines = show_vol_targeted_growth_non_submitting_ticket_instance_quality_gate()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-sleeve-symbol-mapping"]:
        from trading_bot.research.vol_targeted_growth_sleeve_mapping_action_proposal import (
            generate_vol_targeted_growth_sleeve_symbol_mapping,
        )

        result = generate_vol_targeted_growth_sleeve_symbol_mapping()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-sleeve-symbol-mapping"]:
        from trading_bot.research.vol_targeted_growth_sleeve_mapping_action_proposal import (
            show_vol_targeted_growth_sleeve_symbol_mapping,
        )

        code, lines = show_vol_targeted_growth_sleeve_symbol_mapping()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-broker-ready-action-proposal"]:
        from trading_bot.research.vol_targeted_growth_sleeve_mapping_action_proposal import (
            generate_vol_targeted_growth_broker_ready_action_proposal,
        )

        result = generate_vol_targeted_growth_broker_ready_action_proposal()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-broker-ready-action-proposal"]:
        from trading_bot.research.vol_targeted_growth_sleeve_mapping_action_proposal import (
            show_vol_targeted_growth_broker_ready_action_proposal,
        )

        code, lines = show_vol_targeted_growth_broker_ready_action_proposal()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-calculated-order-values"]:
        from trading_bot.research.vol_targeted_growth_calculated_order_values import (
            generate_vol_targeted_growth_calculated_order_values,
        )

        result = generate_vol_targeted_growth_calculated_order_values()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-calculated-order-values"]:
        from trading_bot.research.vol_targeted_growth_calculated_order_values import (
            show_vol_targeted_growth_calculated_order_values,
        )

        code, lines = show_vol_targeted_growth_calculated_order_values()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-saved-price-snapshot-readiness"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_readiness import (
            generate_vol_targeted_growth_saved_price_snapshot_readiness,
        )

        result = generate_vol_targeted_growth_saved_price_snapshot_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-saved-price-snapshot-readiness"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_readiness import (
            show_vol_targeted_growth_saved_price_snapshot_readiness,
        )

        code, lines = show_vol_targeted_growth_saved_price_snapshot_readiness()
        for line in lines:
            print(line)
        return (code)
    saved_price_snapshot_approval_routes = {
        "--vol-targeted-growth-saved-price-snapshot-approval-wording": "generate_vol_targeted_growth_saved_price_snapshot_approval_wording",
        "--show-vol-targeted-growth-saved-price-snapshot-approval-wording": "show_vol_targeted_growth_saved_price_snapshot_approval_wording",
        "--vol-targeted-growth-saved-price-snapshot-approval-record": "generate_vol_targeted_growth_saved_price_snapshot_approval_record",
        "--show-vol-targeted-growth-saved-price-snapshot-approval-record": "show_vol_targeted_growth_saved_price_snapshot_approval_record",
    }
    if argv and argv[0] in saved_price_snapshot_approval_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_saved_price_snapshot_approval as saved_price_snapshot_approval

        result = getattr(saved_price_snapshot_approval, saved_price_snapshot_approval_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--vol-targeted-growth-saved-price-snapshot-runner-design"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner_design import (
            generate_vol_targeted_growth_saved_price_snapshot_runner_design,
        )

        result = generate_vol_targeted_growth_saved_price_snapshot_runner_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-saved-price-snapshot-runner-design"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner_design import (
            show_vol_targeted_growth_saved_price_snapshot_runner_design,
        )

        code, lines = show_vol_targeted_growth_saved_price_snapshot_runner_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-saved-price-snapshot-runner-readiness"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner_readiness import (
            generate_vol_targeted_growth_saved_price_snapshot_runner_readiness,
        )

        result = generate_vol_targeted_growth_saved_price_snapshot_runner_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-saved-price-snapshot-runner-readiness"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner_readiness import (
            show_vol_targeted_growth_saved_price_snapshot_runner_readiness,
        )

        code, lines = show_vol_targeted_growth_saved_price_snapshot_runner_readiness()
        for line in lines:
            print(line)
        return (code)
    saved_price_snapshot_runner_approval_routes = {
        "--vol-targeted-growth-saved-price-snapshot-runner-approval-wording": "generate_vol_targeted_growth_saved_price_snapshot_runner_approval_wording",
        "--show-vol-targeted-growth-saved-price-snapshot-runner-approval-wording": "show_vol_targeted_growth_saved_price_snapshot_runner_approval_wording",
        "--vol-targeted-growth-saved-price-snapshot-runner-approval-record": "generate_vol_targeted_growth_saved_price_snapshot_runner_approval_record",
        "--show-vol-targeted-growth-saved-price-snapshot-runner-approval-record": "show_vol_targeted_growth_saved_price_snapshot_runner_approval_record",
    }
    if argv and argv[0] in saved_price_snapshot_runner_approval_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_saved_price_snapshot_runner_approval as snapshot_runner_approval

        result = getattr(snapshot_runner_approval, saved_price_snapshot_runner_approval_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv and argv[0] == "--vol-targeted-growth-saved-price-snapshot":
        allowed = {"--vol-targeted-growth-saved-price-snapshot", "--confirm-saved-price-snapshot-run"}
        if any(item not in allowed for item in argv) or len(argv) > 2:
            print("--vol-targeted-growth-saved-price-snapshot only accepts --confirm-saved-price-snapshot-run.")
            return (2)
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner import (
            generate_vol_targeted_growth_saved_price_snapshot,
        )

        result = generate_vol_targeted_growth_saved_price_snapshot(
            confirm_saved_price_snapshot_run="--confirm-saved-price-snapshot-run" in argv
        )
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-saved-price-snapshot"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_runner import (
            show_vol_targeted_growth_saved_price_snapshot,
        )

        code, lines = show_vol_targeted_growth_saved_price_snapshot()
        for line in lines:
            print(line)
        return (code)
    saved_price_snapshot_run_approval_routes = {
        "--vol-targeted-growth-saved-price-snapshot-run-approval-wording": "generate_vol_targeted_growth_saved_price_snapshot_run_approval_wording",
        "--show-vol-targeted-growth-saved-price-snapshot-run-approval-wording": "show_vol_targeted_growth_saved_price_snapshot_run_approval_wording",
        "--vol-targeted-growth-saved-price-snapshot-run-approval-record": "generate_vol_targeted_growth_saved_price_snapshot_run_approval_record",
        "--show-vol-targeted-growth-saved-price-snapshot-run-approval-record": "show_vol_targeted_growth_saved_price_snapshot_run_approval_record",
    }
    if argv and argv[0] in saved_price_snapshot_run_approval_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_saved_price_snapshot_run_approval as snapshot_run_approval

        result = getattr(snapshot_run_approval, saved_price_snapshot_run_approval_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--vol-targeted-growth-saved-price-snapshot-quality-gate"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_quality_gate import (
            generate_vol_targeted_growth_saved_price_snapshot_quality_gate,
        )

        result = generate_vol_targeted_growth_saved_price_snapshot_quality_gate()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-saved-price-snapshot-quality-gate"]:
        from trading_bot.research.vol_targeted_growth_saved_price_snapshot_quality_gate import (
            show_vol_targeted_growth_saved_price_snapshot_quality_gate,
        )

        code, lines = show_vol_targeted_growth_saved_price_snapshot_quality_gate()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-quantity-calculation-readiness"]:
        from trading_bot.research.vol_targeted_growth_quantity_calculation_readiness import (
            generate_vol_targeted_growth_quantity_calculation_readiness,
        )

        result = generate_vol_targeted_growth_quantity_calculation_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-quantity-calculation-readiness"]:
        from trading_bot.research.vol_targeted_growth_quantity_calculation_readiness import (
            show_vol_targeted_growth_quantity_calculation_readiness,
        )

        code, lines = show_vol_targeted_growth_quantity_calculation_readiness()
        for line in lines:
            print(line)
        return (code)
    quantity_calculation_routes = {
        "--vol-targeted-growth-quantity-calculation-approval-wording": "generate_vol_targeted_growth_quantity_calculation_approval_wording",
        "--show-vol-targeted-growth-quantity-calculation-approval-wording": "show_vol_targeted_growth_quantity_calculation_approval_wording",
        "--vol-targeted-growth-quantity-calculation-approval-record": "generate_vol_targeted_growth_quantity_calculation_approval_record",
        "--show-vol-targeted-growth-quantity-calculation-approval-record": "show_vol_targeted_growth_quantity_calculation_approval_record",
        "--vol-targeted-growth-review-quantity-estimates": "generate_vol_targeted_growth_review_quantity_estimates",
        "--show-vol-targeted-growth-review-quantity-estimates": "show_vol_targeted_growth_review_quantity_estimates",
        "--vol-targeted-growth-review-quantity-quality-gate": "generate_vol_targeted_growth_review_quantity_quality_gate",
        "--show-vol-targeted-growth-review-quantity-quality-gate": "show_vol_targeted_growth_review_quantity_quality_gate",
    }
    if argv and argv[0] in quantity_calculation_routes and len(argv) == 1:
        from trading_bot.research import vol_targeted_growth_quantity_calculation as quantity_calculation

        result = getattr(quantity_calculation, quantity_calculation_routes[argv[0]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            return (code)
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--vol-targeted-growth-fresh-broker-pre-ticket-gate-design"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_design import (
            generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_design,
        )

        result = generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_design()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-design"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_design import (
            show_vol_targeted_growth_fresh_broker_pre_ticket_gate_design,
        )

        code, lines = show_vol_targeted_growth_fresh_broker_pre_ticket_gate_design()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness import (
            generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness,
        )

        result = generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness import (
            show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness,
        )

        code, lines = show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness()
        for line in lines:
            print(line)
        return (code)
    if "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run" in argv:
        allowed_args = {
            "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
            "--confirm-readonly-alpaca-check",
        }
        if any(arg not in allowed_args for arg in argv):
            print("--vol-targeted-growth-fresh-broker-pre-ticket-gate-run only accepts --confirm-readonly-alpaca-check.")
            return (2)
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run import (
            generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run,
        )

        result = generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run(
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in argv
        )
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run import (
            show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run,
        )

        code, lines = show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run()
        for line in lines:
            print(line)
        return (code)
    if argv == ["--vol-targeted-growth-paper-live-execution-blocker-rollup"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_paper_live_execution_blocker_rollup,
        )

        result = generate_vol_targeted_growth_paper_live_execution_blocker_rollup()
        for line in result.summary_lines:
            print(line)
        return (0)
    if argv == ["--show-vol-targeted-growth-paper-live-execution-blocker-rollup"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_paper_live_execution_blocker_rollup,
        )

        code, lines = show_vol_targeted_growth_paper_live_execution_blocker_rollup()
        for line in lines:
            print(line)
        return (code)


def _parse_live_preflight_early_args(argv: list[str]) -> dict[str, str]:
    values = {
        "ticker": "",
        "side": "",
        "quantity": "",
        "confirm_readonly_alpaca_check": "false",
    }
    index = 0
    while index < len(argv):
        item = argv[index]
        if item in {"--ticker", "--side", "--quantity"} and index + 1 < len(argv):
            values[item.removeprefix("--")] = argv[index + 1]
            index += 2
            continue
        if item == "--confirm-readonly-alpaca-check":
            values["confirm_readonly_alpaca_check"] = "true"
        index += 1
    return values


def _is_qqq100_action_preview_early_args(argv: list[str]) -> bool:
    allowed = {
        "--qqq100-action-preview",
        "--use-paper-positions-readonly",
        "--confirm-readonly-alpaca-check",
    }
    return "--qqq100-action-preview" in argv and set(argv).issubset(allowed)
