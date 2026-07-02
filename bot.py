from __future__ import annotations

import argparse
import csv
import logging
import math
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
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
    if sys.argv[1:] == ["--stock-etf-paper-execution-readiness-report"]:
        from trading_bot.research.stock_etf_paper_execution_readiness import (
            generate_stock_etf_paper_execution_readiness_report,
        )

        result = generate_stock_etf_paper_execution_readiness_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] in (
        ["--alpaca-paper-readiness-report"],
        ["--alpaca-paper-readiness-report", "--confirm-readonly-alpaca-check"],
    ):
        from trading_bot.research.alpaca_paper_readiness import generate_alpaca_paper_readiness_report

        result = generate_alpaca_paper_readiness_report(
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in sys.argv[1:]
        )
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--alpaca-connectivity-diagnostics"]:
        from trading_bot.research.alpaca_connectivity_diagnostics import generate_alpaca_connectivity_diagnostics

        result = generate_alpaca_connectivity_diagnostics()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-alpaca-connectivity-diagnostics"]:
        from trading_bot.research.alpaca_connectivity_diagnostics import show_alpaca_connectivity_diagnostics

        status_code, lines = show_alpaca_connectivity_diagnostics()
        for line in lines:
            print(line)
        raise SystemExit(status_code)
    if sys.argv[1:] == ["--paper-order-smoke-test-readiness-pack"]:
        from trading_bot.research.paper_order_smoke_test_readiness import (
            generate_paper_order_smoke_test_readiness_pack,
        )

        result = generate_paper_order_smoke_test_readiness_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if "--paper-order-smoke-test-live-preflight" in sys.argv[1:]:
        from trading_bot.research.paper_order_smoke_test_live_preflight import (
            generate_paper_order_smoke_test_live_preflight,
        )

        early_args = _parse_live_preflight_early_args(sys.argv[1:])
        result = generate_paper_order_smoke_test_live_preflight(
            ticker=early_args.get("ticker", ""),
            side=early_args.get("side", ""),
            quantity=early_args.get("quantity", ""),
            confirm_readonly_alpaca_check=early_args.get("confirm_readonly_alpaca_check", "") == "true",
        )
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if "--paper-order-smoke-test-postcheck" in sys.argv[1:]:
        from trading_bot.research.paper_order_smoke_test_postcheck import (
            generate_paper_order_smoke_test_postcheck,
        )

        early_args = _parse_live_preflight_early_args(sys.argv[1:])
        result = generate_paper_order_smoke_test_postcheck(
            ticker=early_args.get("ticker", ""),
            side=early_args.get("side", ""),
            quantity=early_args.get("quantity", ""),
            confirm_readonly_alpaca_check=early_args.get("confirm_readonly_alpaca_check", "") == "true",
        )
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--future-refresh-cron-readiness-pack"]:
        from trading_bot.research.future_refresh_cron_readiness import generate_future_refresh_cron_readiness_pack

        result = generate_future_refresh_cron_readiness_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--paper-order-smoke-test-runbook-check"]:
        from trading_bot.research.paper_order_smoke_test_runbook_check import (
            generate_paper_order_smoke_test_runbook_check,
        )

        result = generate_paper_order_smoke_test_runbook_check()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--paper-smoke-test-kill-switch-diagnosis"]:
        from trading_bot.research.paper_smoke_test_kill_switch_diagnosis import (
            generate_paper_smoke_test_kill_switch_diagnosis,
        )

        result = generate_paper_smoke_test_kill_switch_diagnosis()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-smoke-test-kill-switch-diagnosis"]:
        from trading_bot.research.paper_smoke_test_kill_switch_diagnosis import (
            show_paper_smoke_test_kill_switch_diagnosis,
        )

        code, lines = show_paper_smoke_test_kill_switch_diagnosis()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--short-leverage-research-lab"]:
        from trading_bot.research.short_leverage_research_lab import run_short_leverage_research_lab

        result = run_short_leverage_research_lab()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-short-leverage-research-lab"]:
        from trading_bot.research.short_leverage_research_lab import show_short_leverage_research_lab

        code, lines = show_short_leverage_research_lab()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq-leverage-validation-report"]:
        from trading_bot.research.qqq_leverage_validation import generate_qqq_leverage_validation_report

        result = generate_qqq_leverage_validation_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq-leverage-validation-report"]:
        from trading_bot.research.qqq_leverage_validation import show_qqq_leverage_validation_report

        code, lines = show_qqq_leverage_validation_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq-adaptive-leverage-lab"]:
        from trading_bot.research.qqq_adaptive_leverage_lab import generate_qqq_adaptive_leverage_lab

        result = generate_qqq_adaptive_leverage_lab()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq-adaptive-leverage-lab"]:
        from trading_bot.research.qqq_adaptive_leverage_lab import show_qqq_adaptive_leverage_lab

        code, lines = show_qqq_adaptive_leverage_lab()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq-lead-decision-report"]:
        from trading_bot.research.qqq_lead_decision import generate_qqq_lead_decision_report

        result = generate_qqq_lead_decision_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq-lead-decision-report"]:
        from trading_bot.research.qqq_lead_decision import show_qqq_lead_decision_report

        code, lines = show_qqq_lead_decision_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq-trend-gate-manual-review-pack"]:
        from trading_bot.research.qqq_trend_gate_manual_review import generate_qqq_trend_gate_manual_review_pack

        result = generate_qqq_trend_gate_manual_review_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq-trend-gate-manual-review-pack"]:
        from trading_bot.research.qqq_trend_gate_manual_review import show_qqq_trend_gate_manual_review_pack

        code, lines = show_qqq_trend_gate_manual_review_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq-preview-candidate-readiness-report"]:
        from trading_bot.research.qqq_preview_candidate_readiness import generate_qqq_preview_candidate_readiness_report

        result = generate_qqq_preview_candidate_readiness_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq-preview-candidate-readiness-report"]:
        from trading_bot.research.qqq_preview_candidate_readiness import show_qqq_preview_candidate_readiness_report

        code, lines = show_qqq_preview_candidate_readiness_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-preview-candidate-readiness-pack"]:
        from trading_bot.research.qqq100_preview_candidate_readiness_pack import (
            generate_qqq100_preview_candidate_readiness_pack,
        )

        result = generate_qqq100_preview_candidate_readiness_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-preview-candidate-readiness-pack"]:
        from trading_bot.research.qqq100_preview_candidate_readiness_pack import (
            show_qqq100_preview_candidate_readiness_pack,
        )

        code, lines = show_qqq100_preview_candidate_readiness_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-preview-signal-pack"]:
        from trading_bot.research.qqq100_preview_signal_pack import (
            generate_qqq100_preview_signal_pack,
        )

        result = generate_qqq100_preview_signal_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-preview-signal-pack"]:
        from trading_bot.research.qqq100_preview_signal_pack import (
            show_qqq100_preview_signal_pack,
        )

        code, lines = show_qqq100_preview_signal_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if _is_qqq100_action_preview_early_args(sys.argv[1:]):
        from trading_bot.research.qqq100_action_preview import (
            generate_qqq100_action_preview,
        )

        result = generate_qqq100_action_preview(
            use_paper_positions_readonly="--use-paper-positions-readonly" in sys.argv[1:],
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in sys.argv[1:],
        )
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-action-preview"]:
        from trading_bot.research.qqq100_action_preview import (
            show_qqq100_action_preview,
        )

        code, lines = show_qqq100_action_preview()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-strategy-portfolio-preview"]:
        from trading_bot.research.multi_strategy_portfolio_preview import generate_multi_strategy_portfolio_preview

        result = generate_multi_strategy_portfolio_preview()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-strategy-portfolio-preview"]:
        from trading_bot.research.multi_strategy_portfolio_preview import show_multi_strategy_portfolio_preview

        code, lines = show_multi_strategy_portfolio_preview()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-paper-readiness-blocker-report"]:
        from trading_bot.research.qqq100_paper_readiness_blocker_report import (
            generate_qqq100_paper_readiness_blocker_report,
        )

        result = generate_qqq100_paper_readiness_blocker_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-paper-readiness-blocker-report"]:
        from trading_bot.research.qqq100_paper_readiness_blocker_report import (
            show_qqq100_paper_readiness_blocker_report,
        )

        code, lines = show_qqq100_paper_readiness_blocker_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-paper-execution-readiness-report"]:
        from trading_bot.research.qqq100_paper_execution_readiness_report import (
            generate_qqq100_paper_execution_readiness_report,
        )

        result = generate_qqq100_paper_execution_readiness_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-paper-execution-readiness-report"]:
        from trading_bot.research.qqq100_paper_execution_readiness_report import (
            show_qqq100_paper_execution_readiness_report,
        )

        code, lines = show_qqq100_paper_execution_readiness_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-promotion-gate"]:
        from trading_bot.research.paper_live_promotion_gate import generate_paper_live_promotion_gate

        result = generate_paper_live_promotion_gate()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-promotion-gate"]:
        from trading_bot.research.paper_live_promotion_gate import show_paper_live_promotion_gate

        code, lines = show_paper_live_promotion_gate()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-readiness-report"]:
        from trading_bot.research.paper_live_readiness_report import generate_paper_live_readiness_report

        result = generate_paper_live_readiness_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-readiness-report"]:
        from trading_bot.research.paper_live_readiness_report import show_paper_live_readiness_report

        code, lines = show_paper_live_readiness_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-state-summary"]:
        from trading_bot.research.paper_live_state_summary import generate_paper_live_state_summary

        result = generate_paper_live_state_summary()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-state-summary"]:
        from trading_bot.research.paper_live_state_summary import show_paper_live_state_summary

        code, lines = show_paper_live_state_summary()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-evidence-audit"]:
        from trading_bot.research.paper_live_evidence_audit import generate_paper_live_evidence_audit

        result = generate_paper_live_evidence_audit()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-evidence-audit"]:
        from trading_bot.research.paper_live_evidence_audit import show_paper_live_evidence_audit

        code, lines = show_paper_live_evidence_audit()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-postcheck-readiness-report"]:
        from trading_bot.research.qqq100_postcheck_readiness_report import (
            generate_qqq100_postcheck_readiness_report,
        )

        result = generate_qqq100_postcheck_readiness_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-postcheck-readiness-report"]:
        from trading_bot.research.qqq100_postcheck_readiness_report import (
            show_qqq100_postcheck_readiness_report,
        )

        code, lines = show_qqq100_postcheck_readiness_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-followup-policy-report"]:
        from trading_bot.research.qqq100_followup_policy_report import (
            generate_qqq100_followup_policy_report,
        )

        result = generate_qqq100_followup_policy_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-followup-policy-report"]:
        from trading_bot.research.qqq100_followup_policy_report import (
            show_qqq100_followup_policy_report,
        )

        code, lines = show_qqq100_followup_policy_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-daily-decision-report"]:
        from trading_bot.research.qqq100_daily_decision_report import (
            generate_qqq100_daily_decision_report,
        )

        result = generate_qqq100_daily_decision_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-daily-decision-report"]:
        from trading_bot.research.qqq100_daily_decision_report import (
            show_qqq100_daily_decision_report,
        )

        code, lines = show_qqq100_daily_decision_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-manual-flatten-readiness-report"]:
        from trading_bot.research.qqq100_manual_flatten_readiness_report import (
            generate_qqq100_manual_flatten_readiness_report,
        )

        result = generate_qqq100_manual_flatten_readiness_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-manual-flatten-readiness-report"]:
        from trading_bot.research.qqq100_manual_flatten_readiness_report import (
            show_qqq100_manual_flatten_readiness_report,
        )

        code, lines = show_qqq100_manual_flatten_readiness_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-manual-flatten-runbook-report"]:
        from trading_bot.research.qqq100_manual_flatten_runbook_report import (
            generate_qqq100_manual_flatten_runbook_report,
        )

        result = generate_qqq100_manual_flatten_runbook_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-manual-flatten-runbook-report"]:
        from trading_bot.research.qqq100_manual_flatten_runbook_report import (
            show_qqq100_manual_flatten_runbook_report,
        )

        code, lines = show_qqq100_manual_flatten_runbook_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-monitoring-status"]:
        from trading_bot.research.paper_live_monitoring_status import (
            generate_paper_live_monitoring_status,
        )

        result = generate_paper_live_monitoring_status()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-monitoring-status"]:
        from trading_bot.research.paper_live_monitoring_status import (
            show_paper_live_monitoring_status,
        )

        code, lines = show_paper_live_monitoring_status()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-checklist-status"]:
        from trading_bot.research.paper_live_checklist_status import (
            generate_paper_live_checklist_status,
        )

        result = generate_paper_live_checklist_status()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-checklist-status"]:
        from trading_bot.research.paper_live_checklist_status import (
            show_paper_live_checklist_status,
        )

        code, lines = show_paper_live_checklist_status()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-go-no-go-dashboard"]:
        from trading_bot.research.paper_live_go_no_go_dashboard import (
            generate_paper_live_go_no_go_dashboard,
        )

        result = generate_paper_live_go_no_go_dashboard()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-go-no-go-dashboard"]:
        from trading_bot.research.paper_live_go_no_go_dashboard import (
            show_paper_live_go_no_go_dashboard,
        )

        code, lines = show_paper_live_go_no_go_dashboard()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-post-gate-review"]:
        from trading_bot.research.vol_targeted_growth_post_gate_review import (
            generate_vol_targeted_growth_post_gate_review,
        )

        result = generate_vol_targeted_growth_post_gate_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-post-gate-review"]:
        from trading_bot.research.vol_targeted_growth_post_gate_review import (
            show_vol_targeted_growth_post_gate_review,
        )

        code, lines = show_vol_targeted_growth_post_gate_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-manual-ticket-value-design"]:
        from trading_bot.research.vol_targeted_growth_manual_ticket_value_design import (
            generate_vol_targeted_growth_manual_ticket_value_design,
        )

        result = generate_vol_targeted_growth_manual_ticket_value_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-manual-ticket-value-design"]:
        from trading_bot.research.vol_targeted_growth_manual_ticket_value_design import (
            show_vol_targeted_growth_manual_ticket_value_design,
        )

        code, lines = show_vol_targeted_growth_manual_ticket_value_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-executable-ticket-prerequisites-closeout"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
            generate_vol_targeted_growth_executable_ticket_prerequisites_closeout,
        )

        result = generate_vol_targeted_growth_executable_ticket_prerequisites_closeout()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-executable-ticket-prerequisites-closeout"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
            show_vol_targeted_growth_executable_ticket_prerequisites_closeout,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_prerequisites_closeout()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-executable-ticket-approval-readiness"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
            generate_vol_targeted_growth_executable_ticket_approval_readiness,
        )

        result = generate_vol_targeted_growth_executable_ticket_approval_readiness()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-executable-ticket-approval-readiness"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_closeout import (
            show_vol_targeted_growth_executable_ticket_approval_readiness,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_approval_readiness()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-execution-approval-request-readiness"]:
        from trading_bot.research.vol_targeted_growth_execution_approval_request_readiness import (
            generate_vol_targeted_growth_execution_approval_request_readiness,
        )

        result = generate_vol_targeted_growth_execution_approval_request_readiness()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-execution-approval-request-readiness"]:
        from trading_bot.research.vol_targeted_growth_execution_approval_request_readiness import (
            show_vol_targeted_growth_execution_approval_request_readiness,
        )

        code, lines = show_vol_targeted_growth_execution_approval_request_readiness()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-execution-design-approval-wording"]:
        from trading_bot.research.vol_targeted_growth_execution_design_approval import (
            generate_vol_targeted_growth_execution_design_approval_wording,
        )

        result = generate_vol_targeted_growth_execution_design_approval_wording()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-execution-design-approval-wording"]:
        from trading_bot.research.vol_targeted_growth_execution_design_approval import (
            show_vol_targeted_growth_execution_design_approval_wording,
        )

        code, lines = show_vol_targeted_growth_execution_design_approval_wording()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-execution-design-approval-record"]:
        from trading_bot.research.vol_targeted_growth_execution_design_approval import (
            generate_vol_targeted_growth_execution_design_approval_record,
        )

        result = generate_vol_targeted_growth_execution_design_approval_record()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-execution-design-approval-record"]:
        from trading_bot.research.vol_targeted_growth_execution_design_approval import (
            show_vol_targeted_growth_execution_design_approval_record,
        )

        code, lines = show_vol_targeted_growth_execution_design_approval_record()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-non-submitting-executable-ticket-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_executable_ticket_design import (
            generate_vol_targeted_growth_non_submitting_executable_ticket_design,
        )

        result = generate_vol_targeted_growth_non_submitting_executable_ticket_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-non-submitting-executable-ticket-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_executable_ticket_design import (
            show_vol_targeted_growth_non_submitting_executable_ticket_design,
        )

        code, lines = show_vol_targeted_growth_non_submitting_executable_ticket_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    ticket_values_approval_routes = {
        "--vol-targeted-growth-ticket-values-approval-readiness": "generate_vol_targeted_growth_ticket_values_approval_readiness",
        "--show-vol-targeted-growth-ticket-values-approval-readiness": "show_vol_targeted_growth_ticket_values_approval_readiness",
        "--vol-targeted-growth-ticket-values-approval-wording": "generate_vol_targeted_growth_ticket_values_approval_wording",
        "--show-vol-targeted-growth-ticket-values-approval-wording": "show_vol_targeted_growth_ticket_values_approval_wording",
        "--vol-targeted-growth-ticket-values-approval-record": "generate_vol_targeted_growth_ticket_values_approval_record",
        "--show-vol-targeted-growth-ticket-values-approval-record": "show_vol_targeted_growth_ticket_values_approval_record",
    }
    if sys.argv[1:] and sys.argv[1] in ticket_values_approval_routes and len(sys.argv[1:]) == 1:
        from trading_bot.research import vol_targeted_growth_ticket_values_approval as ticket_values_approval

        result = getattr(ticket_values_approval, ticket_values_approval_routes[sys.argv[1]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    ticket_value_placeholder_routes = {
        "--vol-targeted-growth-ticket-value-placeholders": "generate_vol_targeted_growth_ticket_value_placeholders",
        "--show-vol-targeted-growth-ticket-value-placeholders": "show_vol_targeted_growth_ticket_value_placeholders",
        "--vol-targeted-growth-ticket-value-quality-gate": "generate_vol_targeted_growth_ticket_value_quality_gate",
        "--show-vol-targeted-growth-ticket-value-quality-gate": "show_vol_targeted_growth_ticket_value_quality_gate",
    }
    if sys.argv[1:] and sys.argv[1] in ticket_value_placeholder_routes and len(sys.argv[1:]) == 1:
        from trading_bot.research import vol_targeted_growth_ticket_value_placeholders as ticket_value_placeholders

        result = getattr(ticket_value_placeholders, ticket_value_placeholder_routes[sys.argv[1]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    ticket_value_proposal_approval_routes = {
        "--vol-targeted-growth-ticket-value-proposal-approval-wording": "generate_vol_targeted_growth_ticket_value_proposal_approval_wording",
        "--show-vol-targeted-growth-ticket-value-proposal-approval-wording": "show_vol_targeted_growth_ticket_value_proposal_approval_wording",
        "--vol-targeted-growth-ticket-value-proposal-approval-record": "generate_vol_targeted_growth_ticket_value_proposal_approval_record",
        "--show-vol-targeted-growth-ticket-value-proposal-approval-record": "show_vol_targeted_growth_ticket_value_proposal_approval_record",
    }
    if sys.argv[1:] and sys.argv[1] in ticket_value_proposal_approval_routes and len(sys.argv[1:]) == 1:
        from trading_bot.research import vol_targeted_growth_ticket_value_proposal_approval as ticket_value_proposal_approval

        result = getattr(ticket_value_proposal_approval, ticket_value_proposal_approval_routes[sys.argv[1]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    proposed_ticket_values_routes = {
        "--vol-targeted-growth-proposed-ticket-values": "generate_vol_targeted_growth_proposed_ticket_values",
        "--show-vol-targeted-growth-proposed-ticket-values": "show_vol_targeted_growth_proposed_ticket_values",
        "--vol-targeted-growth-proposed-ticket-values-quality-gate": "generate_vol_targeted_growth_proposed_ticket_values_quality_gate",
        "--show-vol-targeted-growth-proposed-ticket-values-quality-gate": "show_vol_targeted_growth_proposed_ticket_values_quality_gate",
    }
    if sys.argv[1:] and sys.argv[1] in proposed_ticket_values_routes and len(sys.argv[1:]) == 1:
        from trading_bot.research import vol_targeted_growth_proposed_ticket_values as proposed_ticket_values

        result = getattr(proposed_ticket_values, proposed_ticket_values_routes[sys.argv[1]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    executable_ticket_draft_readiness_routes = {
        "--vol-targeted-growth-executable-ticket-draft-readiness": "generate_vol_targeted_growth_executable_ticket_draft_readiness",
        "--show-vol-targeted-growth-executable-ticket-draft-readiness": "show_vol_targeted_growth_executable_ticket_draft_readiness",
    }
    if sys.argv[1:] and sys.argv[1] in executable_ticket_draft_readiness_routes and len(sys.argv[1:]) == 1:
        from trading_bot.research import vol_targeted_growth_executable_ticket_draft_readiness as executable_ticket_draft_readiness

        result = getattr(executable_ticket_draft_readiness, executable_ticket_draft_readiness_routes[sys.argv[1]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--vol-targeted-growth-executable-ticket-approval-criteria"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_approval_criteria import (
            generate_vol_targeted_growth_executable_ticket_approval_criteria,
        )

        result = generate_vol_targeted_growth_executable_ticket_approval_criteria()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-executable-ticket-approval-criteria"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_approval_criteria import (
            show_vol_targeted_growth_executable_ticket_approval_criteria,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_approval_criteria()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-executable-ticket-criteria-resolution-plan"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_resolution_plan import (
            generate_vol_targeted_growth_executable_ticket_criteria_resolution_plan,
        )

        result = generate_vol_targeted_growth_executable_ticket_criteria_resolution_plan()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-executable-ticket-criteria-resolution-plan"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_resolution_plan import (
            show_vol_targeted_growth_executable_ticket_criteria_resolution_plan,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_criteria_resolution_plan()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-executable-ticket-criteria-source-review"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_source_review import (
            generate_vol_targeted_growth_executable_ticket_criteria_source_review,
        )

        result = generate_vol_targeted_growth_executable_ticket_criteria_source_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-executable-ticket-criteria-source-review"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_source_review import (
            show_vol_targeted_growth_executable_ticket_criteria_source_review,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_criteria_source_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review import (
            generate_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review,
        )

        result = generate_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review import (
            show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
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
    if sys.argv[1:] and sys.argv[1] in blocker_specific_routes and len(sys.argv[1:]) == 1:
        from trading_bot.research import vol_targeted_growth_executable_ticket_blocker_specific_reviews as blocker_reviews

        function_name, label = blocker_specific_routes[sys.argv[1]]
        result = getattr(blocker_reviews, function_name)()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
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
    if sys.argv[1:] and sys.argv[1] in closeout_candidate_routes and len(sys.argv[1:]) == 1:
        from trading_bot.research import vol_targeted_growth_executable_ticket_closeout_candidate_reviews as candidate_reviews

        result = getattr(candidate_reviews, closeout_candidate_routes[sys.argv[1]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
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
    if sys.argv[1:] and sys.argv[1] in approval_wording_routes and len(sys.argv[1:]) == 1:
        if "final-ticket-blockers" in sys.argv[1]:
            from trading_bot.research import vol_targeted_growth_final_ticket_blockers_closeout as approval_wording
        elif "criteria-resolution-plan" in sys.argv[1]:
            from trading_bot.research import vol_targeted_growth_criteria_resolution_plan_closeout_approval_wording as approval_wording
        elif "approval-criteria" in sys.argv[1]:
            from trading_bot.research import vol_targeted_growth_approval_criteria_closeout_approval_wording as approval_wording
        else:
            from trading_bot.research import vol_targeted_growth_criteria_source_closeout_approval_wording as approval_wording

        result = getattr(approval_wording, approval_wording_routes[sys.argv[1]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
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
    if sys.argv[1:] and sys.argv[1] in closeout_record_routes and len(sys.argv[1:]) == 1:
        if "final-ticket-blockers" in sys.argv[1]:
            from trading_bot.research import vol_targeted_growth_final_ticket_blockers_closeout as closeout_record
        elif "criteria-resolution-plan" in sys.argv[1]:
            from trading_bot.research import vol_targeted_growth_criteria_resolution_plan_closeout_record as closeout_record
        elif "approval-criteria" in sys.argv[1]:
            from trading_bot.research import vol_targeted_growth_approval_criteria_closeout_record as closeout_record
        else:
            from trading_bot.research import vol_targeted_growth_criteria_source_closeout_record as closeout_record

        result = getattr(closeout_record, closeout_record_routes[sys.argv[1]])()
        if isinstance(result, tuple):
            code, lines = result
            for line in lines:
                print(line)
            raise SystemExit(code)
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--paper-live-f6-f7-audit"]:
        from trading_bot.research.paper_live_f6_f7_audit import generate_paper_live_f6_f7_audit

        result = generate_paper_live_f6_f7_audit()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-f6-f7-audit"]:
        from trading_bot.research.paper_live_f6_f7_audit import show_paper_live_f6_f7_audit

        code, lines = show_paper_live_f6_f7_audit()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-promotion-ladder-design"]:
        from trading_bot.research.paper_live_promotion_ladder_design import (
            generate_paper_live_promotion_ladder_design,
        )

        result = generate_paper_live_promotion_ladder_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-promotion-ladder-design"]:
        from trading_bot.research.paper_live_promotion_ladder_design import (
            show_paper_live_promotion_ladder_design,
        )

        code, lines = show_paper_live_promotion_ladder_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-promotion-ladder-status"]:
        from trading_bot.research.paper_live_promotion_ladder_status import (
            generate_paper_live_promotion_ladder_status,
        )

        result = generate_paper_live_promotion_ladder_status()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-promotion-ladder-status"]:
        from trading_bot.research.paper_live_promotion_ladder_status import (
            show_paper_live_promotion_ladder_status,
        )

        code, lines = show_paper_live_promotion_ladder_status()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-f7-accounting-proof"]:
        from trading_bot.research.paper_live_f7_accounting_proof import (
            generate_paper_live_f7_accounting_proof,
        )

        result = generate_paper_live_f7_accounting_proof()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-f7-accounting-proof"]:
        from trading_bot.research.paper_live_f7_accounting_proof import (
            show_paper_live_f7_accounting_proof,
        )

        code, lines = show_paper_live_f7_accounting_proof()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-next-ladder-candidate-scope"]:
        from trading_bot.research.paper_live_next_ladder_candidate_scope import (
            generate_paper_live_next_ladder_candidate_scope,
        )

        result = generate_paper_live_next_ladder_candidate_scope()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-next-ladder-candidate-scope"]:
        from trading_bot.research.paper_live_next_ladder_candidate_scope import (
            show_paper_live_next_ladder_candidate_scope,
        )

        code, lines = show_paper_live_next_ladder_candidate_scope()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-defensive-sleeve-ladder-scope-review"]:
        from trading_bot.research.paper_live_defensive_sleeve_ladder_scope_review import (
            generate_paper_live_defensive_sleeve_ladder_scope_review,
        )

        result = generate_paper_live_defensive_sleeve_ladder_scope_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-defensive-sleeve-ladder-scope-review"]:
        from trading_bot.research.paper_live_defensive_sleeve_ladder_scope_review import (
            show_paper_live_defensive_sleeve_ladder_scope_review,
        )

        code, lines = show_paper_live_defensive_sleeve_ladder_scope_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-defensive-sleeve-manual-review"]:
        from trading_bot.research.paper_live_defensive_sleeve_manual_review import (
            generate_paper_live_defensive_sleeve_manual_review,
        )

        result = generate_paper_live_defensive_sleeve_manual_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-defensive-sleeve-manual-review"]:
        from trading_bot.research.paper_live_defensive_sleeve_manual_review import (
            show_paper_live_defensive_sleeve_manual_review,
        )

        code, lines = show_paper_live_defensive_sleeve_manual_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-defensive-sleeve-preview-readiness"]:
        from trading_bot.research.paper_live_defensive_sleeve_preview_readiness import (
            generate_paper_live_defensive_sleeve_preview_readiness,
        )

        result = generate_paper_live_defensive_sleeve_preview_readiness()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-defensive-sleeve-preview-readiness"]:
        from trading_bot.research.paper_live_defensive_sleeve_preview_readiness import (
            show_paper_live_defensive_sleeve_preview_readiness,
        )

        code, lines = show_paper_live_defensive_sleeve_preview_readiness()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-defensive-sleeve-evidence-quality"]:
        from trading_bot.research.paper_live_defensive_sleeve_evidence_quality import (
            generate_paper_live_defensive_sleeve_evidence_quality,
        )

        result = generate_paper_live_defensive_sleeve_evidence_quality()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-defensive-sleeve-evidence-quality"]:
        from trading_bot.research.paper_live_defensive_sleeve_evidence_quality import (
            show_paper_live_defensive_sleeve_evidence_quality,
        )

        code, lines = show_paper_live_defensive_sleeve_evidence_quality()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-multi-sleeve-roadmap"]:
        from trading_bot.research.paper_live_multi_sleeve_roadmap import generate_paper_live_multi_sleeve_roadmap

        result = generate_paper_live_multi_sleeve_roadmap()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-multi-sleeve-roadmap"]:
        from trading_bot.research.paper_live_multi_sleeve_roadmap import show_paper_live_multi_sleeve_roadmap

        code, lines = show_paper_live_multi_sleeve_roadmap()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-next-phase-backlog"]:
        from trading_bot.research.paper_live_next_phase_backlog import generate_paper_live_next_phase_backlog

        result = generate_paper_live_next_phase_backlog()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-next-phase-backlog"]:
        from trading_bot.research.paper_live_next_phase_backlog import show_paper_live_next_phase_backlog

        code, lines = show_paper_live_next_phase_backlog()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-multi-sleeve-evidence-gap"]:
        from trading_bot.research.paper_live_multi_sleeve_evidence_gap import (
            generate_paper_live_multi_sleeve_evidence_gap,
        )

        result = generate_paper_live_multi_sleeve_evidence_gap()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-multi-sleeve-evidence-gap"]:
        from trading_bot.research.paper_live_multi_sleeve_evidence_gap import (
            show_paper_live_multi_sleeve_evidence_gap,
        )

        code, lines = show_paper_live_multi_sleeve_evidence_gap()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-high-growth-evidence-gap"]:
        from trading_bot.research.paper_live_high_growth_evidence_gap import (
            generate_paper_live_high_growth_evidence_gap,
        )

        result = generate_paper_live_high_growth_evidence_gap()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-high-growth-evidence-gap"]:
        from trading_bot.research.paper_live_high_growth_evidence_gap import (
            show_paper_live_high_growth_evidence_gap,
        )

        code, lines = show_paper_live_high_growth_evidence_gap()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-high-growth-evidence-quality"]:
        from trading_bot.research.paper_live_high_growth_evidence_quality import (
            generate_paper_live_high_growth_evidence_quality,
        )

        result = generate_paper_live_high_growth_evidence_quality()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-high-growth-evidence-quality"]:
        from trading_bot.research.paper_live_high_growth_evidence_quality import (
            show_paper_live_high_growth_evidence_quality,
        )

        code, lines = show_paper_live_high_growth_evidence_quality()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-live-high-growth-manual-review-decision"]:
        from trading_bot.research.paper_live_high_growth_manual_review_decision import (
            generate_paper_live_high_growth_manual_review_decision,
        )

        result = generate_paper_live_high_growth_manual_review_decision()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-live-high-growth-manual-review-decision"]:
        from trading_bot.research.paper_live_high_growth_manual_review_decision import (
            show_paper_live_high_growth_manual_review_decision,
        )

        code, lines = show_paper_live_high_growth_manual_review_decision()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if "--qqq100-paper-postcheck" in sys.argv[1:]:
        from trading_bot.research.qqq100_paper_postcheck import generate_qqq100_paper_postcheck

        allowed = {"--qqq100-paper-postcheck", "--confirm-readonly-alpaca-check"}
        if not set(sys.argv[1:]).issubset(allowed):
            print("--qqq100-paper-postcheck only accepts --confirm-readonly-alpaca-check.")
            raise SystemExit(2)
        result = generate_qqq100_paper_postcheck(
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in sys.argv[1:]
        )
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-paper-postcheck"]:
        from trading_bot.research.qqq100_paper_postcheck import show_qqq100_paper_postcheck

        code, lines = show_qqq100_paper_postcheck()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-repeat-alignment-workflow-design"]:
        from trading_bot.research.qqq100_repeat_alignment_workflow_design import (
            generate_qqq100_repeat_alignment_workflow_design,
        )

        result = generate_qqq100_repeat_alignment_workflow_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-repeat-alignment-workflow-design"]:
        from trading_bot.research.qqq100_repeat_alignment_workflow_design import (
            show_qqq100_repeat_alignment_workflow_design,
        )

        code, lines = show_qqq100_repeat_alignment_workflow_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-strategy-monitor"]:
        from trading_bot.research.multi_sleeve_strategy_monitor import generate_multi_sleeve_strategy_monitor

        result = generate_multi_sleeve_strategy_monitor()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-strategy-monitor"]:
        from trading_bot.research.multi_sleeve_strategy_monitor import show_multi_sleeve_strategy_monitor

        code, lines = show_multi_sleeve_strategy_monitor()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--sleeve-research-scoreboard"]:
        from trading_bot.research.sleeve_research_scoreboard import generate_sleeve_research_scoreboard

        result = generate_sleeve_research_scoreboard()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-sleeve-research-scoreboard"]:
        from trading_bot.research.sleeve_research_scoreboard import show_sleeve_research_scoreboard

        code, lines = show_sleeve_research_scoreboard()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--codex-qqq-defensive-crash-gate-research-pack"]:
        from trading_bot.research.codex_qqq_defensive_crash_gate_research_pack import (
            generate_codex_qqq_defensive_crash_gate_research_pack,
        )

        result = generate_codex_qqq_defensive_crash_gate_research_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-codex-qqq-defensive-crash-gate-research-pack"]:
        from trading_bot.research.codex_qqq_defensive_crash_gate_research_pack import (
            show_codex_qqq_defensive_crash_gate_research_pack,
        )

        code, lines = show_codex_qqq_defensive_crash_gate_research_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--sleeve-return-streams"]:
        from trading_bot.research.sleeve_return_streams import generate_sleeve_return_streams

        result = generate_sleeve_return_streams()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-sleeve-return-streams"]:
        from trading_bot.research.sleeve_return_streams import show_sleeve_return_streams

        code, lines = show_sleeve_return_streams()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-stream-reconciliation"]:
        from trading_bot.research.qqq100_stream_reconciliation import generate_qqq100_stream_reconciliation

        result = generate_qqq100_stream_reconciliation()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-stream-reconciliation"]:
        from trading_bot.research.qqq100_stream_reconciliation import show_qqq100_stream_reconciliation

        code, lines = show_qqq100_stream_reconciliation()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--qqq100-benchmark-inputs-report"]:
        from trading_bot.research.qqq100_benchmark_inputs import generate_qqq100_benchmark_inputs_report

        result = generate_qqq100_benchmark_inputs_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-qqq100-benchmark-inputs"]:
        from trading_bot.research.qqq100_benchmark_inputs import show_qqq100_benchmark_inputs

        code, lines = show_qqq100_benchmark_inputs()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-return-streams"]:
        from trading_bot.research.high_growth_return_streams import generate_high_growth_return_streams

        result = generate_high_growth_return_streams()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-return-streams"]:
        from trading_bot.research.high_growth_return_streams import show_high_growth_return_streams

        code, lines = show_high_growth_return_streams()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--crypto-return-streams"]:
        from trading_bot.research.crypto_return_streams import generate_crypto_return_streams

        result = generate_crypto_return_streams()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-crypto-return-streams"]:
        from trading_bot.research.crypto_return_streams import show_crypto_return_streams

        code, lines = show_crypto_return_streams()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-portfolio-backtest"]:
        from trading_bot.research.multi_sleeve_portfolio_backtest import generate_multi_sleeve_portfolio_backtest

        result = generate_multi_sleeve_portfolio_backtest()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-portfolio-backtest"]:
        from trading_bot.research.multi_sleeve_portfolio_backtest import show_multi_sleeve_portfolio_backtest

        code, lines = show_multi_sleeve_portfolio_backtest()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-robustness"]:
        from trading_bot.research.multi_sleeve_robustness import generate_multi_sleeve_robustness

        result = generate_multi_sleeve_robustness()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-robustness"]:
        from trading_bot.research.multi_sleeve_robustness import show_multi_sleeve_robustness

        code, lines = show_multi_sleeve_robustness()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-crypto-review"]:
        from trading_bot.research.multi_sleeve_crypto_review import generate_multi_sleeve_crypto_review

        result = generate_multi_sleeve_crypto_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-crypto-review"]:
        from trading_bot.research.multi_sleeve_crypto_review import show_multi_sleeve_crypto_review

        code, lines = show_multi_sleeve_crypto_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-crypto-containment-review"]:
        from trading_bot.research.multi_sleeve_crypto_containment import (
            generate_multi_sleeve_crypto_containment_review,
        )

        result = generate_multi_sleeve_crypto_containment_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-crypto-containment-review"]:
        from trading_bot.research.multi_sleeve_crypto_containment import (
            show_multi_sleeve_crypto_containment_review,
        )

        code, lines = show_multi_sleeve_crypto_containment_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--show-current-research-state"]:
        from trading_bot.research.current_research_state import show_current_research_state

        code, lines = show_current_research_state()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-allocation-policy-review"]:
        from trading_bot.research.multi_sleeve_allocation_policy import generate_multi_sleeve_allocation_policy_review

        result = generate_multi_sleeve_allocation_policy_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-allocation-policy-review"]:
        from trading_bot.research.multi_sleeve_allocation_policy import show_multi_sleeve_allocation_policy_review

        code, lines = show_multi_sleeve_allocation_policy_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-weight-sensitivity"]:
        from trading_bot.research.multi_sleeve_weight_sensitivity import generate_multi_sleeve_weight_sensitivity

        result = generate_multi_sleeve_weight_sensitivity()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-weight-sensitivity"]:
        from trading_bot.research.multi_sleeve_weight_sensitivity import show_multi_sleeve_weight_sensitivity

        code, lines = show_multi_sleeve_weight_sensitivity()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-higher-growth-review"]:
        from trading_bot.research.multi_sleeve_higher_growth_review import generate_multi_sleeve_higher_growth_review

        result = generate_multi_sleeve_higher_growth_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-higher-growth-review"]:
        from trading_bot.research.multi_sleeve_higher_growth_review import show_multi_sleeve_higher_growth_review

        code, lines = show_multi_sleeve_higher_growth_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-research-lead-decision"]:
        from trading_bot.research.multi_sleeve_research_lead_decision import (
            generate_multi_sleeve_research_lead_decision,
        )

        result = generate_multi_sleeve_research_lead_decision()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-research-lead-decision"]:
        from trading_bot.research.multi_sleeve_research_lead_decision import (
            show_multi_sleeve_research_lead_decision,
        )

        code, lines = show_multi_sleeve_research_lead_decision()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-lead-state-refresh"]:
        from trading_bot.research.multi_sleeve_lead_state import generate_multi_sleeve_lead_state

        result = generate_multi_sleeve_lead_state()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-lead-state"]:
        from trading_bot.research.multi_sleeve_lead_state import show_multi_sleeve_lead_state

        code, lines = show_multi_sleeve_lead_state()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--multi-sleeve-high-growth-drawdown-decomposition"]:
        from trading_bot.research.multi_sleeve_high_growth_drawdown import (
            generate_multi_sleeve_high_growth_drawdown_decomposition,
        )

        result = generate_multi_sleeve_high_growth_drawdown_decomposition()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-multi-sleeve-high-growth-drawdown-decomposition"]:
        from trading_bot.research.multi_sleeve_high_growth_drawdown import (
            show_multi_sleeve_high_growth_drawdown_decomposition,
        )

        code, lines = show_multi_sleeve_high_growth_drawdown_decomposition()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-sleeve-quality-review"]:
        from trading_bot.research.high_growth_sleeve_quality import generate_high_growth_sleeve_quality_review

        result = generate_high_growth_sleeve_quality_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-sleeve-quality-review"]:
        from trading_bot.research.high_growth_sleeve_quality import show_high_growth_sleeve_quality_review

        code, lines = show_high_growth_sleeve_quality_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-component-attribution"]:
        from trading_bot.research.high_growth_component_attribution import generate_high_growth_component_attribution

        result = generate_high_growth_component_attribution()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-component-attribution"]:
        from trading_bot.research.high_growth_component_attribution import show_high_growth_component_attribution

        code, lines = show_high_growth_component_attribution()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-component-streams"]:
        from trading_bot.research.high_growth_component_streams import generate_high_growth_component_streams

        result = generate_high_growth_component_streams()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-component-streams"]:
        from trading_bot.research.high_growth_component_streams import show_high_growth_component_streams

        code, lines = show_high_growth_component_streams()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-sleeve-concentration-review"]:
        from trading_bot.research.high_growth_sleeve_concentration import generate_high_growth_sleeve_concentration_review

        result = generate_high_growth_sleeve_concentration_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-sleeve-concentration-review"]:
        from trading_bot.research.high_growth_sleeve_concentration import show_high_growth_sleeve_concentration_review

        code, lines = show_high_growth_sleeve_concentration_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-research-checkpoint"]:
        from trading_bot.research.high_growth_research_checkpoint import generate_high_growth_research_checkpoint

        result = generate_high_growth_research_checkpoint()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-research-checkpoint"]:
        from trading_bot.research.high_growth_research_checkpoint import show_high_growth_research_checkpoint

        code, lines = show_high_growth_research_checkpoint()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--paper-execution-state-summary"]:
        from trading_bot.research.paper_execution_state_summary import generate_paper_execution_state_summary

        result = generate_paper_execution_state_summary()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-paper-execution-state-summary"]:
        from trading_bot.research.paper_execution_state_summary import show_paper_execution_state_summary

        code, lines = show_paper_execution_state_summary()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-lab"]:
        from trading_bot.research.high_growth_stock_lab import generate_high_growth_stock_lab

        result = generate_high_growth_stock_lab()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-lab"]:
        from trading_bot.research.high_growth_stock_lab import show_high_growth_stock_lab

        code, lines = show_high_growth_stock_lab()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-universe-expansion-report"]:
        from trading_bot.research.high_growth_stock_universe_expansion import (
            generate_high_growth_stock_universe_expansion_report,
        )

        result = generate_high_growth_stock_universe_expansion_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-universe-expansion-report"]:
        from trading_bot.research.high_growth_stock_universe_expansion import (
            show_high_growth_stock_universe_expansion_report,
        )

        code, lines = show_high_growth_stock_universe_expansion_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-drawdown-control-report"]:
        from trading_bot.research.high_growth_stock_drawdown_control import (
            generate_high_growth_stock_drawdown_control_report,
        )

        result = generate_high_growth_stock_drawdown_control_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-drawdown-control-report"]:
        from trading_bot.research.high_growth_stock_drawdown_control import (
            show_high_growth_stock_drawdown_control_report,
        )

        code, lines = show_high_growth_stock_drawdown_control_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-lead-decision-report"]:
        from trading_bot.research.high_growth_stock_lead_decision import (
            generate_high_growth_stock_lead_decision_report,
        )

        result = generate_high_growth_stock_lead_decision_report()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-lead-decision-report"]:
        from trading_bot.research.high_growth_stock_lead_decision import (
            show_high_growth_stock_lead_decision_report,
        )

        code, lines = show_high_growth_stock_lead_decision_report()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-manual-review-pack"]:
        from trading_bot.research.high_growth_stock_manual_review_pack import (
            generate_high_growth_stock_manual_review_pack,
        )

        result = generate_high_growth_stock_manual_review_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-manual-review-pack"]:
        from trading_bot.research.high_growth_stock_manual_review_pack import (
            show_high_growth_stock_manual_review_pack,
        )

        code, lines = show_high_growth_stock_manual_review_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-risk-review-pack"]:
        from trading_bot.research.high_growth_stock_risk_review_pack import (
            generate_high_growth_stock_risk_review_pack,
        )

        result = generate_high_growth_stock_risk_review_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-risk-review-pack"]:
        from trading_bot.research.high_growth_stock_risk_review_pack import (
            show_high_growth_stock_risk_review_pack,
        )

        code, lines = show_high_growth_stock_risk_review_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-risk-evidence-review"]:
        from trading_bot.research.high_growth_stock_risk_evidence_review import (
            generate_high_growth_stock_risk_evidence_review,
        )

        result = generate_high_growth_stock_risk_evidence_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-risk-evidence-review"]:
        from trading_bot.research.high_growth_stock_risk_evidence_review import (
            show_high_growth_stock_risk_evidence_review,
        )

        code, lines = show_high_growth_stock_risk_evidence_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-branch-decision-checkpoint"]:
        from trading_bot.research.high_growth_stock_branch_decision_checkpoint import (
            generate_high_growth_stock_branch_decision_checkpoint,
        )

        result = generate_high_growth_stock_branch_decision_checkpoint()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-branch-decision-checkpoint"]:
        from trading_bot.research.high_growth_stock_branch_decision_checkpoint import (
            show_high_growth_stock_branch_decision_checkpoint,
        )

        code, lines = show_high_growth_stock_branch_decision_checkpoint()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-stock-final-validation-pack"]:
        from trading_bot.research.high_growth_stock_final_validation_pack import (
            generate_high_growth_stock_final_validation_pack,
        )

        result = generate_high_growth_stock_final_validation_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-stock-final-validation-pack"]:
        from trading_bot.research.high_growth_stock_final_validation_pack import (
            show_high_growth_stock_final_validation_pack,
        )

        code, lines = show_high_growth_stock_final_validation_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--high-growth-strategy-discovery-sprint"]:
        from trading_bot.research.high_growth_strategy_discovery_sprint import (
            generate_high_growth_strategy_discovery_sprint,
        )

        result = generate_high_growth_strategy_discovery_sprint()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-high-growth-strategy-discovery-sprint"]:
        from trading_bot.research.high_growth_strategy_discovery_sprint import (
            show_high_growth_strategy_discovery_sprint,
        )

        code, lines = show_high_growth_strategy_discovery_sprint()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--higher-growth-preview-readiness-pack"]:
        from trading_bot.research.higher_growth_preview_readiness_pack import (
            generate_higher_growth_preview_readiness_pack,
        )

        result = generate_higher_growth_preview_readiness_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-higher-growth-preview-readiness-pack"]:
        from trading_bot.research.higher_growth_preview_readiness_pack import (
            show_higher_growth_preview_readiness_pack,
        )

        code, lines = show_higher_growth_preview_readiness_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--higher-growth-candidate-selection-decision"]:
        from trading_bot.research.higher_growth_candidate_selection_decision import (
            generate_higher_growth_candidate_selection_decision,
        )

        result = generate_higher_growth_candidate_selection_decision()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-higher-growth-candidate-selection-decision"]:
        from trading_bot.research.higher_growth_candidate_selection_decision import (
            show_higher_growth_candidate_selection_decision,
        )

        code, lines = show_higher_growth_candidate_selection_decision()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--higher-growth-preview-design"]:
        from trading_bot.research.higher_growth_preview_design import generate_higher_growth_preview_design

        result = generate_higher_growth_preview_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-higher-growth-preview-design"]:
        from trading_bot.research.higher_growth_preview_design import show_higher_growth_preview_design

        code, lines = show_higher_growth_preview_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-research-sprint"]:
        from trading_bot.research.vol_targeted_growth_research_sprint import (
            generate_vol_targeted_growth_research_sprint,
        )

        result = generate_vol_targeted_growth_research_sprint()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-research-sprint"]:
        from trading_bot.research.vol_targeted_growth_research_sprint import (
            show_vol_targeted_growth_research_sprint,
        )

        code, lines = show_vol_targeted_growth_research_sprint()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-manual-review-pack"]:
        from trading_bot.research.vol_targeted_growth_manual_review_pack import (
            generate_vol_targeted_growth_manual_review_pack,
        )

        result = generate_vol_targeted_growth_manual_review_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-manual-review-pack"]:
        from trading_bot.research.vol_targeted_growth_manual_review_pack import (
            show_vol_targeted_growth_manual_review_pack,
        )

        code, lines = show_vol_targeted_growth_manual_review_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-robustness-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_robustness_checkpoint import (
            generate_vol_targeted_growth_robustness_checkpoint,
        )

        result = generate_vol_targeted_growth_robustness_checkpoint()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-robustness-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_robustness_checkpoint import (
            show_vol_targeted_growth_robustness_checkpoint,
        )

        code, lines = show_vol_targeted_growth_robustness_checkpoint()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-nearby-variants-review"]:
        from trading_bot.research.vol_targeted_growth_nearby_variants_review import (
            generate_vol_targeted_growth_nearby_variants_review,
        )

        result = generate_vol_targeted_growth_nearby_variants_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-nearby-variants-review"]:
        from trading_bot.research.vol_targeted_growth_nearby_variants_review import (
            show_vol_targeted_growth_nearby_variants_review,
        )

        code, lines = show_vol_targeted_growth_nearby_variants_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-preview-readiness-decision"]:
        from trading_bot.research.vol_targeted_growth_preview_readiness_decision import (
            generate_vol_targeted_growth_preview_readiness_decision,
        )

        result = generate_vol_targeted_growth_preview_readiness_decision()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-preview-readiness-decision"]:
        from trading_bot.research.vol_targeted_growth_preview_readiness_decision import (
            show_vol_targeted_growth_preview_readiness_decision,
        )

        code, lines = show_vol_targeted_growth_preview_readiness_decision()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-preview-design"]:
        from trading_bot.research.vol_targeted_growth_preview_design import (
            generate_vol_targeted_growth_preview_design,
        )

        result = generate_vol_targeted_growth_preview_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-preview-design"]:
        from trading_bot.research.vol_targeted_growth_preview_design import (
            show_vol_targeted_growth_preview_design,
        )

        code, lines = show_vol_targeted_growth_preview_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-preview-signal"]:
        from trading_bot.research.vol_targeted_growth_preview_signal import (
            generate_vol_targeted_growth_preview_signal,
        )

        result = generate_vol_targeted_growth_preview_signal()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-preview-signal"]:
        from trading_bot.research.vol_targeted_growth_preview_signal import (
            show_vol_targeted_growth_preview_signal,
        )

        code, lines = show_vol_targeted_growth_preview_signal()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-action-preview-design"]:
        from trading_bot.research.vol_targeted_growth_action_preview_design import (
            generate_vol_targeted_growth_action_preview_design,
        )

        result = generate_vol_targeted_growth_action_preview_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-action-preview-design"]:
        from trading_bot.research.vol_targeted_growth_action_preview_design import (
            show_vol_targeted_growth_action_preview_design,
        )

        code, lines = show_vol_targeted_growth_action_preview_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-action-preview"]:
        from trading_bot.research.vol_targeted_growth_action_preview import (
            generate_vol_targeted_growth_action_preview,
        )

        result = generate_vol_targeted_growth_action_preview()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-action-preview"]:
        from trading_bot.research.vol_targeted_growth_action_preview import (
            show_vol_targeted_growth_action_preview,
        )

        code, lines = show_vol_targeted_growth_action_preview()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-action-preview-quality-gate"]:
        from trading_bot.research.vol_targeted_growth_action_preview_quality_gate import (
            generate_vol_targeted_growth_action_preview_quality_gate,
        )

        result = generate_vol_targeted_growth_action_preview_quality_gate()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-action-preview-quality-gate"]:
        from trading_bot.research.vol_targeted_growth_action_preview_quality_gate import (
            show_vol_targeted_growth_action_preview_quality_gate,
        )

        code, lines = show_vol_targeted_growth_action_preview_quality_gate()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-broker-position-comparison-design"]:
        from trading_bot.research.vol_targeted_growth_broker_position_comparison_design import (
            generate_vol_targeted_growth_broker_position_comparison_design,
        )

        result = generate_vol_targeted_growth_broker_position_comparison_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-broker-position-comparison-design"]:
        from trading_bot.research.vol_targeted_growth_broker_position_comparison_design import (
            show_vol_targeted_growth_broker_position_comparison_design,
        )

        code, lines = show_vol_targeted_growth_broker_position_comparison_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-portfolio-risk-review"]:
        from trading_bot.research.vol_targeted_growth_portfolio_risk_review import (
            generate_vol_targeted_growth_portfolio_risk_review,
        )

        result = generate_vol_targeted_growth_portfolio_risk_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-portfolio-risk-review"]:
        from trading_bot.research.vol_targeted_growth_portfolio_risk_review import (
            show_vol_targeted_growth_portfolio_risk_review,
        )

        code, lines = show_vol_targeted_growth_portfolio_risk_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-portfolio-risk-policy-design"]:
        from trading_bot.research.vol_targeted_growth_portfolio_risk_policy_design import (
            generate_vol_targeted_growth_portfolio_risk_policy_design,
        )

        result = generate_vol_targeted_growth_portfolio_risk_policy_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-portfolio-risk-policy-design"]:
        from trading_bot.research.vol_targeted_growth_portfolio_risk_policy_design import (
            show_vol_targeted_growth_portfolio_risk_policy_design,
        )

        code, lines = show_vol_targeted_growth_portfolio_risk_policy_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-paper-live-decision"]:
        from trading_bot.research.vol_targeted_growth_paper_live_decision import (
            generate_vol_targeted_growth_paper_live_decision,
        )

        result = generate_vol_targeted_growth_paper_live_decision()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-paper-live-decision"]:
        from trading_bot.research.vol_targeted_growth_paper_live_decision import (
            show_vol_targeted_growth_paper_live_decision,
        )

        code, lines = show_vol_targeted_growth_paper_live_decision()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-broker-comparison-run-readiness"]:
        from trading_bot.research.vol_targeted_growth_broker_comparison_run_readiness import (
            generate_vol_targeted_growth_broker_comparison_run_readiness,
        )

        result = generate_vol_targeted_growth_broker_comparison_run_readiness()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-broker-comparison-run-readiness"]:
        from trading_bot.research.vol_targeted_growth_broker_comparison_run_readiness import (
            show_vol_targeted_growth_broker_comparison_run_readiness,
        )

        code, lines = show_vol_targeted_growth_broker_comparison_run_readiness()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if "--vol-targeted-growth-broker-position-comparison" in sys.argv[1:]:
        from trading_bot.research.vol_targeted_growth_broker_position_comparison import (
            generate_vol_targeted_growth_broker_position_comparison,
        )

        allowed = {"--vol-targeted-growth-broker-position-comparison", "--confirm-readonly-alpaca-check"}
        if not set(sys.argv[1:]).issubset(allowed):
            print("--vol-targeted-growth-broker-position-comparison only accepts --confirm-readonly-alpaca-check.")
            raise SystemExit(2)
        result = generate_vol_targeted_growth_broker_position_comparison(
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in sys.argv[1:]
        )
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-broker-position-comparison"]:
        from trading_bot.research.vol_targeted_growth_broker_position_comparison import (
            show_vol_targeted_growth_broker_position_comparison,
        )

        code, lines = show_vol_targeted_growth_broker_position_comparison()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-post-comparison-decision"]:
        from trading_bot.research.vol_targeted_growth_post_comparison_decision import (
            generate_vol_targeted_growth_post_comparison_decision,
        )

        result = generate_vol_targeted_growth_post_comparison_decision()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-post-comparison-decision"]:
        from trading_bot.research.vol_targeted_growth_post_comparison_decision import (
            show_vol_targeted_growth_post_comparison_decision,
        )

        code, lines = show_vol_targeted_growth_post_comparison_decision()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-stricter-paper-live-gate-design"]:
        from trading_bot.research.vol_targeted_growth_stricter_paper_live_gate_design import (
            generate_vol_targeted_growth_stricter_paper_live_gate_design,
        )

        result = generate_vol_targeted_growth_stricter_paper_live_gate_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-stricter-paper-live-gate-design"]:
        from trading_bot.research.vol_targeted_growth_stricter_paper_live_gate_design import (
            show_vol_targeted_growth_stricter_paper_live_gate_design,
        )

        code, lines = show_vol_targeted_growth_stricter_paper_live_gate_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-gate-review"]:
        from trading_bot.research.vol_targeted_growth_gate_review import (
            generate_vol_targeted_growth_gate_review,
        )

        result = generate_vol_targeted_growth_gate_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-gate-review"]:
        from trading_bot.research.vol_targeted_growth_gate_review import (
            show_vol_targeted_growth_gate_review,
        )

        code, lines = show_vol_targeted_growth_gate_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-candidate-discussion-blocker-checklist"]:
        from trading_bot.research.vol_targeted_growth_candidate_discussion_blocker_checklist import (
            generate_vol_targeted_growth_candidate_discussion_blocker_checklist,
        )

        result = generate_vol_targeted_growth_candidate_discussion_blocker_checklist()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-candidate-discussion-blocker-checklist"]:
        from trading_bot.research.vol_targeted_growth_candidate_discussion_blocker_checklist import (
            show_vol_targeted_growth_candidate_discussion_blocker_checklist,
        )

        code, lines = show_vol_targeted_growth_candidate_discussion_blocker_checklist()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-candidate-decision-record"]:
        from trading_bot.research.vol_targeted_growth_candidate_decision_record import (
            generate_vol_targeted_growth_candidate_decision_record,
        )

        result = generate_vol_targeted_growth_candidate_decision_record()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-candidate-decision-record"]:
        from trading_bot.research.vol_targeted_growth_candidate_decision_record import (
            show_vol_targeted_growth_candidate_decision_record,
        )

        code, lines = show_vol_targeted_growth_candidate_decision_record()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-candidate-discussion"]:
        from trading_bot.research.vol_targeted_growth_candidate_discussion import (
            generate_vol_targeted_growth_candidate_discussion,
        )

        result = generate_vol_targeted_growth_candidate_discussion()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-candidate-discussion"]:
        from trading_bot.research.vol_targeted_growth_candidate_discussion import (
            show_vol_targeted_growth_candidate_discussion,
        )

        code, lines = show_vol_targeted_growth_candidate_discussion()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-proposal-implementation-design"]:
        from trading_bot.research.vol_targeted_growth_proposal_implementation_design import (
            generate_vol_targeted_growth_proposal_implementation_design,
        )

        result = generate_vol_targeted_growth_proposal_implementation_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-proposal-implementation-design"]:
        from trading_bot.research.vol_targeted_growth_proposal_implementation_design import (
            show_vol_targeted_growth_proposal_implementation_design,
        )

        code, lines = show_vol_targeted_growth_proposal_implementation_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-proposal-preview-schema"]:
        from trading_bot.research.vol_targeted_growth_proposal_preview_schema import (
            generate_vol_targeted_growth_proposal_preview_schema,
        )

        result = generate_vol_targeted_growth_proposal_preview_schema()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-proposal-preview-schema"]:
        from trading_bot.research.vol_targeted_growth_proposal_preview_schema import (
            show_vol_targeted_growth_proposal_preview_schema,
        )

        code, lines = show_vol_targeted_growth_proposal_preview_schema()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-proposal-preview"]:
        from trading_bot.research.vol_targeted_growth_proposal_preview import (
            generate_vol_targeted_growth_proposal_preview,
        )

        result = generate_vol_targeted_growth_proposal_preview()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-proposal-preview"]:
        from trading_bot.research.vol_targeted_growth_proposal_preview import (
            show_vol_targeted_growth_proposal_preview,
        )

        code, lines = show_vol_targeted_growth_proposal_preview()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_review import (
            generate_vol_targeted_growth_seed_change_review,
        )

        result = generate_vol_targeted_growth_seed_change_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_review import (
            show_vol_targeted_growth_seed_change_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-evidence-pack"]:
        from trading_bot.research.vol_targeted_growth_seed_change_evidence_pack import (
            generate_vol_targeted_growth_seed_change_evidence_pack,
        )

        result = generate_vol_targeted_growth_seed_change_evidence_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-evidence-pack"]:
        from trading_bot.research.vol_targeted_growth_seed_change_evidence_pack import (
            show_vol_targeted_growth_seed_change_evidence_pack,
        )

        code, lines = show_vol_targeted_growth_seed_change_evidence_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-risk-reward-comparison"]:
        from trading_bot.research.vol_targeted_growth_seed_change_risk_reward_comparison import (
            generate_vol_targeted_growth_seed_change_risk_reward_comparison,
        )

        result = generate_vol_targeted_growth_seed_change_risk_reward_comparison()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-risk-reward-comparison"]:
        from trading_bot.research.vol_targeted_growth_seed_change_risk_reward_comparison import (
            show_vol_targeted_growth_seed_change_risk_reward_comparison,
        )

        code, lines = show_vol_targeted_growth_seed_change_risk_reward_comparison()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-drawdown-stress-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_drawdown_stress_review import (
            generate_vol_targeted_growth_seed_change_drawdown_stress_review,
        )

        result = generate_vol_targeted_growth_seed_change_drawdown_stress_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-drawdown-stress-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_drawdown_stress_review import (
            show_vol_targeted_growth_seed_change_drawdown_stress_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_drawdown_stress_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-cost-turnover-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_cost_turnover_review import (
            generate_vol_targeted_growth_seed_change_cost_turnover_review,
        )

        result = generate_vol_targeted_growth_seed_change_cost_turnover_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-cost-turnover-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_cost_turnover_review import (
            show_vol_targeted_growth_seed_change_cost_turnover_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_cost_turnover_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-split-stability-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_split_stability_review import (
            generate_vol_targeted_growth_seed_change_split_stability_review,
        )

        result = generate_vol_targeted_growth_seed_change_split_stability_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-split-stability-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_split_stability_review import (
            show_vol_targeted_growth_seed_change_split_stability_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_split_stability_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-component-sleeve-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            generate_vol_targeted_growth_seed_change_component_sleeve_review,
        )

        result = generate_vol_targeted_growth_seed_change_component_sleeve_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-component-sleeve-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            show_vol_targeted_growth_seed_change_component_sleeve_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_component_sleeve_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-action-preview-design"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            generate_vol_targeted_growth_seed_change_action_preview_design,
        )

        result = generate_vol_targeted_growth_seed_change_action_preview_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-action-preview-design"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            show_vol_targeted_growth_seed_change_action_preview_design,
        )

        code, lines = show_vol_targeted_growth_seed_change_action_preview_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-proposal-document"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            generate_vol_targeted_growth_seed_change_proposal_document,
        )

        result = generate_vol_targeted_growth_seed_change_proposal_document()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-proposal-document"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            show_vol_targeted_growth_seed_change_proposal_document,
        )

        code, lines = show_vol_targeted_growth_seed_change_proposal_document()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-broker-exposure-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            generate_vol_targeted_growth_seed_change_broker_exposure_review,
        )

        result = generate_vol_targeted_growth_seed_change_broker_exposure_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-broker-exposure-review"]:
        from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (
            show_vol_targeted_growth_seed_change_broker_exposure_review,
        )

        code, lines = show_vol_targeted_growth_seed_change_broker_exposure_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-manual-review-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_seed_change_manual_review_checkpoint import (
            generate_vol_targeted_growth_seed_change_manual_review_checkpoint,
        )

        result = generate_vol_targeted_growth_seed_change_manual_review_checkpoint()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-manual-review-checkpoint"]:
        from trading_bot.research.vol_targeted_growth_seed_change_manual_review_checkpoint import (
            show_vol_targeted_growth_seed_change_manual_review_checkpoint,
        )

        code, lines = show_vol_targeted_growth_seed_change_manual_review_checkpoint()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-formal-seed-change-proposal"]:
        from trading_bot.research.vol_targeted_growth_formal_seed_change_proposal import (
            generate_vol_targeted_growth_formal_seed_change_proposal,
        )

        result = generate_vol_targeted_growth_formal_seed_change_proposal()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-formal-seed-change-proposal"]:
        from trading_bot.research.vol_targeted_growth_formal_seed_change_proposal import (
            show_vol_targeted_growth_formal_seed_change_proposal,
        )

        code, lines = show_vol_targeted_growth_formal_seed_change_proposal()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-manual-approval-record"]:
        from trading_bot.research.vol_targeted_growth_seed_change_manual_approval_record import (
            generate_vol_targeted_growth_seed_change_manual_approval_record,
        )

        result = generate_vol_targeted_growth_seed_change_manual_approval_record()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-manual-approval-record"]:
        from trading_bot.research.vol_targeted_growth_seed_change_manual_approval_record import (
            show_vol_targeted_growth_seed_change_manual_approval_record,
        )

        code, lines = show_vol_targeted_growth_seed_change_manual_approval_record()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-implementation-design"]:
        from trading_bot.research.vol_targeted_growth_seed_change_implementation_design import (
            generate_vol_targeted_growth_seed_change_implementation_design,
        )

        result = generate_vol_targeted_growth_seed_change_implementation_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-implementation-design"]:
        from trading_bot.research.vol_targeted_growth_seed_change_implementation_design import (
            show_vol_targeted_growth_seed_change_implementation_design,
        )

        code, lines = show_vol_targeted_growth_seed_change_implementation_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-seed-change-dry-run-diff"]:
        from trading_bot.research.vol_targeted_growth_seed_change_dry_run_diff import (
            generate_vol_targeted_growth_seed_change_dry_run_diff,
        )

        result = generate_vol_targeted_growth_seed_change_dry_run_diff()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-seed-change-dry-run-diff"]:
        from trading_bot.research.vol_targeted_growth_seed_change_dry_run_diff import (
            show_vol_targeted_growth_seed_change_dry_run_diff,
        )

        code, lines = show_vol_targeted_growth_seed_change_dry_run_diff()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-active-seed-readiness"]:
        from trading_bot.research.vol_targeted_growth_active_seed_readiness import (
            generate_vol_targeted_growth_active_seed_readiness,
        )

        result = generate_vol_targeted_growth_active_seed_readiness()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-active-seed-readiness"]:
        from trading_bot.research.vol_targeted_growth_active_seed_readiness import (
            show_vol_targeted_growth_active_seed_readiness,
        )

        code, lines = show_vol_targeted_growth_active_seed_readiness()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-paper-live-manual-approval-gate"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_paper_live_manual_approval_gate,
        )

        result = generate_vol_targeted_growth_paper_live_manual_approval_gate()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-paper-live-manual-approval-gate"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_paper_live_manual_approval_gate,
        )

        code, lines = show_vol_targeted_growth_paper_live_manual_approval_gate()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-paper-live-action-preview-pack"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_paper_live_action_preview_pack,
        )

        result = generate_vol_targeted_growth_paper_live_action_preview_pack()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-paper-live-action-preview-pack"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_paper_live_action_preview_pack,
        )

        code, lines = show_vol_targeted_growth_paper_live_action_preview_pack()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-broker-comparison-reconciliation"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_broker_comparison_reconciliation,
        )

        result = generate_vol_targeted_growth_broker_comparison_reconciliation()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-broker-comparison-reconciliation"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_broker_comparison_reconciliation,
        )

        code, lines = show_vol_targeted_growth_broker_comparison_reconciliation()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-paper-live-candidate-approval-record"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_paper_live_candidate_approval_record,
        )

        result = generate_vol_targeted_growth_paper_live_candidate_approval_record()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-paper-live-candidate-approval-record"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_paper_live_candidate_approval_record,
        )

        code, lines = show_vol_targeted_growth_paper_live_candidate_approval_record()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-allocation-cap-sleeve-mapping-policy"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy,
        )

        result = generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-allocation-cap-sleeve-mapping-policy"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_allocation_cap_sleeve_mapping_policy,
        )

        code, lines = show_vol_targeted_growth_allocation_cap_sleeve_mapping_policy()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-non-executable-target-position-plan"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_non_executable_target_position_plan,
        )

        result = generate_vol_targeted_growth_non_executable_target_position_plan()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-non-executable-target-position-plan"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_non_executable_target_position_plan,
        )

        code, lines = show_vol_targeted_growth_non_executable_target_position_plan()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-order-ticket-boundary-design"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_order_ticket_boundary_design,
        )

        result = generate_vol_targeted_growth_order_ticket_boundary_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-order-ticket-boundary-design"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_order_ticket_boundary_design,
        )

        code, lines = show_vol_targeted_growth_order_ticket_boundary_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-executable-ticket-prerequisites-review"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_executable_ticket_prerequisites_review,
        )

        result = generate_vol_targeted_growth_executable_ticket_prerequisites_review()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-executable-ticket-prerequisites-review"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_executable_ticket_prerequisites_review,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_prerequisites_review()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-executable-ticket-gap-list"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_gap_list import (
            generate_vol_targeted_growth_executable_ticket_gap_list,
        )

        result = generate_vol_targeted_growth_executable_ticket_gap_list()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-executable-ticket-gap-list"]:
        from trading_bot.research.vol_targeted_growth_executable_ticket_gap_list import (
            show_vol_targeted_growth_executable_ticket_gap_list,
        )

        code, lines = show_vol_targeted_growth_executable_ticket_gap_list()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-manual-execution-design-approval-gate"]:
        from trading_bot.research.vol_targeted_growth_manual_execution_design_approval_gate import (
            generate_vol_targeted_growth_manual_execution_design_approval_gate,
        )

        result = generate_vol_targeted_growth_manual_execution_design_approval_gate()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-manual-execution-design-approval-gate"]:
        from trading_bot.research.vol_targeted_growth_manual_execution_design_approval_gate import (
            show_vol_targeted_growth_manual_execution_design_approval_gate,
        )

        code, lines = show_vol_targeted_growth_manual_execution_design_approval_gate()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-non-submitting-ticket-schema-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_schema_design import (
            generate_vol_targeted_growth_non_submitting_ticket_schema_design,
        )

        result = generate_vol_targeted_growth_non_submitting_ticket_schema_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-non-submitting-ticket-schema-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_schema_design import (
            show_vol_targeted_growth_non_submitting_ticket_schema_design,
        )

        code, lines = show_vol_targeted_growth_non_submitting_ticket_schema_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-non-submitting-ticket-instance-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_design import (
            generate_vol_targeted_growth_non_submitting_ticket_instance_design,
        )

        result = generate_vol_targeted_growth_non_submitting_ticket_instance_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-non-submitting-ticket-instance-design"]:
        from trading_bot.research.vol_targeted_growth_non_submitting_ticket_instance_design import (
            show_vol_targeted_growth_non_submitting_ticket_instance_design,
        )

        code, lines = show_vol_targeted_growth_non_submitting_ticket_instance_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-fresh-broker-pre-ticket-gate-design"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_design import (
            generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_design,
        )

        result = generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_design()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-design"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_design import (
            show_vol_targeted_growth_fresh_broker_pre_ticket_gate_design,
        )

        code, lines = show_vol_targeted_growth_fresh_broker_pre_ticket_gate_design()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness import (
            generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness,
        )

        result = generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness import (
            show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness,
        )

        code, lines = show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run" in sys.argv[1:]:
        allowed_args = {
            "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
            "--confirm-readonly-alpaca-check",
        }
        if any(arg not in allowed_args for arg in sys.argv[1:]):
            print("--vol-targeted-growth-fresh-broker-pre-ticket-gate-run only accepts --confirm-readonly-alpaca-check.")
            raise SystemExit(2)
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run import (
            generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run,
        )

        result = generate_vol_targeted_growth_fresh_broker_pre_ticket_gate_run(
            confirm_readonly_alpaca_check="--confirm-readonly-alpaca-check" in sys.argv[1:]
        )
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run"]:
        from trading_bot.research.vol_targeted_growth_fresh_broker_pre_ticket_gate_run import (
            show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run,
        )

        code, lines = show_vol_targeted_growth_fresh_broker_pre_ticket_gate_run()
        for line in lines:
            print(line)
        raise SystemExit(code)
    if sys.argv[1:] == ["--vol-targeted-growth-paper-live-execution-blocker-rollup"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            generate_vol_targeted_growth_paper_live_execution_blocker_rollup,
        )

        result = generate_vol_targeted_growth_paper_live_execution_blocker_rollup()
        for line in result.summary_lines:
            print(line)
        raise SystemExit(0)
    if sys.argv[1:] == ["--show-vol-targeted-growth-paper-live-execution-blocker-rollup"]:
        from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (
            show_vol_targeted_growth_paper_live_execution_blocker_rollup,
        )

        code, lines = show_vol_targeted_growth_paper_live_execution_blocker_rollup()
        for line in lines:
            print(line)
        raise SystemExit(code)


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
        "--short-leverage-research-lab",
        action="store_true",
        help="Run a research-only synthetic short/leverage hypothesis lab without approving shorting, margin, leverage, or execution.",
    )
    parser.add_argument(
        "--show-short-leverage-research-lab",
        action="store_true",
        help="Display the saved short/leverage research lab summary without refreshing data.",
    )
    parser.add_argument(
        "--qqq-leverage-validation-report",
        action="store_true",
        help="Run a research-only fixed QQQ synthetic leverage validation report without approving leverage or execution.",
    )
    parser.add_argument(
        "--show-qqq-leverage-validation-report",
        action="store_true",
        help="Display the saved QQQ leverage validation report without refreshing data.",
    )
    parser.add_argument(
        "--qqq-adaptive-leverage-lab",
        action="store_true",
        help="Run a research-only fixed QQQ adaptive trend/leverage lab without approving leverage or execution.",
    )
    parser.add_argument(
        "--show-qqq-adaptive-leverage-lab",
        action="store_true",
        help="Display the saved QQQ adaptive leverage lab without refreshing data.",
    )
    parser.add_argument(
        "--qqq-lead-decision-report",
        action="store_true",
        help="Create a saved-output QQQ branch lead decision report without execution approval.",
    )
    parser.add_argument(
        "--show-qqq-lead-decision-report",
        action="store_true",
        help="Display the saved QQQ branch lead decision report without refreshing data.",
    )
    parser.add_argument(
        "--qqq-trend-gate-manual-review-pack",
        action="store_true",
        help="Create a saved-output manual review pack for the QQQ trend-gate research lead.",
    )
    parser.add_argument(
        "--show-qqq-trend-gate-manual-review-pack",
        action="store_true",
        help="Display the saved QQQ trend-gate manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--qqq-preview-candidate-readiness-report",
        action="store_true",
        help="Create a saved-output preview-candidate readiness report for the QQQ trend-gate research lead.",
    )
    parser.add_argument(
        "--show-qqq-preview-candidate-readiness-report",
        action="store_true",
        help="Display the saved QQQ preview-candidate readiness report without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-preview-candidate-readiness-pack",
        action="store_true",
        help="Create a saved-output QQQ100 preview-candidate readiness pack without refreshing data.",
    )
    parser.add_argument(
        "--show-qqq100-preview-candidate-readiness-pack",
        action="store_true",
        help="Display the saved QQQ100 preview-candidate readiness pack without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-preview-signal-pack",
        action="store_true",
        help="Create a non-execution QQQ100 preview signal pack.",
    )
    parser.add_argument(
        "--show-qqq100-preview-signal-pack",
        action="store_true",
        help="Display the saved QQQ100 preview signal pack without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-action-preview",
        action="store_true",
        help="Create a saved-signal-only QQQ100 action preview; optional paper positions require explicit read-only confirmation.",
    )
    parser.add_argument(
        "--show-qqq100-action-preview",
        action="store_true",
        help="Display the saved QQQ100 action preview without refreshing data or reading positions.",
    )
    parser.add_argument(
        "--multi-strategy-portfolio-preview",
        action="store_true",
        help="Create a saved-output-only combined strategy sleeve exposure/conflict preview.",
    )
    parser.add_argument(
        "--show-multi-strategy-portfolio-preview",
        action="store_true",
        help="Display the saved multi-strategy portfolio preview without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-paper-readiness-blocker-report",
        action="store_true",
        help="Create a saved-output QQQ100 paper-readiness blocker report without execution.",
    )
    parser.add_argument(
        "--show-qqq100-paper-readiness-blocker-report",
        action="store_true",
        help="Display the saved QQQ100 paper-readiness blocker report without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-paper-execution-readiness-report",
        action="store_true",
        help="Create a saved-output-only QQQ100 paper execution design-readiness report without approving execution.",
    )
    parser.add_argument(
        "--show-qqq100-paper-execution-readiness-report",
        action="store_true",
        help="Display the saved QQQ100 paper execution readiness report without refreshing data.",
    )
    parser.add_argument(
        "--paper-live-promotion-gate",
        action="store_true",
        help="Create a saved-output paper-live candidate promotion gate for qqq_100_trend_gate without approving execution.",
    )
    parser.add_argument(
        "--show-paper-live-promotion-gate",
        action="store_true",
        help="Display the saved paper-live promotion gate without refreshing data or reading broker state.",
    )
    parser.add_argument(
        "--paper-live-readiness-report",
        action="store_true",
        help="Create a saved-output paper-live readiness report for future manual QQQ100 paper action discussion.",
    )
    parser.add_argument(
        "--show-paper-live-readiness-report",
        action="store_true",
        help="Display the saved paper-live readiness report without refreshing data or reading broker state.",
    )
    parser.add_argument(
        "--paper-live-state-summary",
        action="store_true",
        help="Create a saved-output paper-live state summary before any future manual QQQ100 paper action discussion.",
    )
    parser.add_argument(
        "--show-paper-live-state-summary",
        action="store_true",
        help="Display the saved paper-live state summary without refreshing data or reading broker state.",
    )
    parser.add_argument(
        "--paper-live-evidence-audit",
        action="store_true",
        help="Create a saved-output paper-live evidence audit for QQQ100 saved-state reconciliation.",
    )
    parser.add_argument(
        "--show-paper-live-evidence-audit",
        action="store_true",
        help="Display the saved paper-live evidence audit without refreshing data or reading broker state.",
    )
    parser.add_argument(
        "--qqq100-postcheck-readiness-report",
        action="store_true",
        help="Create a saved-output runbook for the manual read-only QQQ100 postcheck evidence step.",
    )
    parser.add_argument(
        "--show-qqq100-postcheck-readiness-report",
        action="store_true",
        help="Display the saved QQQ100 postcheck readiness runbook without broker reads.",
    )
    parser.add_argument(
        "--qqq100-followup-policy-report",
        action="store_true",
        help="Create a saved-output QQQ100 follow-up/no-action policy report without broker reads.",
    )
    parser.add_argument(
        "--show-qqq100-followup-policy-report",
        action="store_true",
        help="Display the saved QQQ100 follow-up/no-action policy report without broker reads.",
    )
    parser.add_argument(
        "--qqq100-daily-decision-report",
        action="store_true",
        help="Create a saved-output QQQ100 daily decision report without broker reads.",
    )
    parser.add_argument(
        "--show-qqq100-daily-decision-report",
        action="store_true",
        help="Display the saved QQQ100 daily decision report without broker reads.",
    )
    parser.add_argument(
        "--qqq100-manual-flatten-readiness-report",
        action="store_true",
        help="Create a saved-output QQQ100 manual flatten readiness report without broker reads.",
    )
    parser.add_argument(
        "--show-qqq100-manual-flatten-readiness-report",
        action="store_true",
        help="Display the saved QQQ100 manual flatten readiness report without broker reads.",
    )
    parser.add_argument(
        "--qqq100-manual-flatten-runbook-report",
        action="store_true",
        help="Create a saved-output QQQ100 manual flatten runbook/design report without broker reads.",
    )
    parser.add_argument(
        "--show-qqq100-manual-flatten-runbook-report",
        action="store_true",
        help="Display the saved QQQ100 manual flatten runbook/design report without broker reads.",
    )
    parser.add_argument(
        "--paper-live-monitoring-status",
        action="store_true",
        help="Create a saved-output paper-live monitoring status for QQQ100 without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--show-paper-live-monitoring-status",
        action="store_true",
        help="Display the saved paper-live monitoring status without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--paper-live-checklist-status",
        action="store_true",
        help="Create a saved-output paper-live checklist closeout status without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--show-paper-live-checklist-status",
        action="store_true",
        help="Display the saved paper-live checklist status without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--paper-live-go-no-go-dashboard",
        action="store_true",
        help="Create a saved-output paper-live go/no-go dashboard without broker reads or execution approval.",
    )
    parser.add_argument(
        "--show-paper-live-go-no-go-dashboard",
        action="store_true",
        help="Display the saved paper-live go/no-go dashboard without broker reads or execution approval.",
    )
    parser.add_argument(
        "--vol-targeted-growth-post-gate-review",
        action="store_true",
        help="Create a saved-output post-gate review for the active volatility seed without broker reads or execution approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-post-gate-review",
        action="store_true",
        help="Display the saved volatility-targeted growth post-gate review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-manual-ticket-value-design",
        action="store_true",
        help="Create a saved-output manual ticket-value design checkpoint without populating executable order values.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-manual-ticket-value-design",
        action="store_true",
        help="Display the saved volatility-targeted growth manual ticket-value design checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-prerequisites-closeout",
        action="store_true",
        help="Create a saved-output executable-ticket prerequisites closeout without approving execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-prerequisites-closeout",
        action="store_true",
        help="Display the saved executable-ticket prerequisites closeout.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-approval-readiness",
        action="store_true",
        help="Create a saved-output executable-ticket approval-readiness checkpoint without requesting approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-approval-readiness",
        action="store_true",
        help="Display the saved executable-ticket approval-readiness checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-execution-approval-request-readiness",
        action="store_true",
        help="Create a saved-output readiness checkpoint for a future separate execution approval request.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-execution-approval-request-readiness",
        action="store_true",
        help="Display the saved execution approval request readiness checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-execution-design-approval-wording",
        action="store_true",
        help="Create saved wording for execution-design-only approval without approving orders.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-execution-design-approval-wording",
        action="store_true",
        help="Display saved wording for execution-design-only approval.",
    )
    parser.add_argument(
        "--vol-targeted-growth-execution-design-approval-record",
        action="store_true",
        help="Create a saved execution-design-only approval record without approving orders.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-execution-design-approval-record",
        action="store_true",
        help="Display the saved execution-design-only approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-submitting-executable-ticket-design",
        action="store_true",
        help="Create a saved non-submitting executable-ticket design without order values or execution approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-submitting-executable-ticket-design",
        action="store_true",
        help="Display the saved non-submitting executable-ticket design.",
    )
    parser.add_argument("--vol-targeted-growth-ticket-values-approval-readiness", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-values-approval-readiness", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-values-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-values-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-values-approval-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-values-approval-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-value-placeholders", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-value-placeholders", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-value-quality-gate", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-value-quality-gate", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-value-proposal-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-value-proposal-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-value-proposal-approval-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-value-proposal-approval-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-proposed-ticket-values", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-proposed-ticket-values", action="store_true")
    parser.add_argument("--vol-targeted-growth-proposed-ticket-values-quality-gate", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-proposed-ticket-values-quality-gate", action="store_true")
    parser.add_argument("--vol-targeted-growth-executable-ticket-draft-readiness", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-executable-ticket-draft-readiness", action="store_true")
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-approval-criteria",
        action="store_true",
        help="Create saved-output executable-ticket approval criteria without requesting approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-approval-criteria",
        action="store_true",
        help="Display saved executable-ticket approval criteria.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-criteria-resolution-plan",
        action="store_true",
        help="Create a saved-output resolution plan for executable-ticket approval criteria blockers.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-criteria-resolution-plan",
        action="store_true",
        help="Display the saved executable-ticket criteria resolution plan.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-criteria-source-review",
        action="store_true",
        help="Create a saved-output source review for executable-ticket approval criteria.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-criteria-source-review",
        action="store_true",
        help="Display the saved executable-ticket criteria source review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review",
        action="store_true",
        help="Create a saved-output blocker closeout review for executable-ticket criteria.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review",
        action="store_true",
        help="Display the saved executable-ticket criteria blocker closeout review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-criteria-source-blocker-review",
        action="store_true",
        help="Create a saved-output criteria source blocker review without closing blockers.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-criteria-source-blocker-review",
        action="store_true",
        help="Display the saved criteria source blocker review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-criteria-resolution-plan-blocker-review",
        action="store_true",
        help="Create a saved-output criteria resolution plan blocker review without closing blockers.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-criteria-resolution-plan-blocker-review",
        action="store_true",
        help="Display the saved criteria resolution plan blocker review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-approval-criteria-not-approval-blocker-review",
        action="store_true",
        help="Create a saved-output approval criteria blocker review without requesting approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-approval-criteria-not-approval-blocker-review",
        action="store_true",
        help="Display the saved approval criteria blocker review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-criteria-blocker-specific-review-rollup",
        action="store_true",
        help="Create a saved-output rollup of criteria blocker-specific reviews.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-criteria-blocker-specific-review-rollup",
        action="store_true",
        help="Display the saved criteria blocker-specific review rollup.",
    )
    parser.add_argument("--vol-targeted-growth-criteria-source-closeout-candidate-review", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-source-closeout-candidate-review", action="store_true")
    parser.add_argument("--vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review", action="store_true")
    parser.add_argument("--vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review", action="store_true")
    parser.add_argument("--vol-targeted-growth-criteria-closeout-candidate-review-rollup", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-closeout-candidate-review-rollup", action="store_true")
    parser.add_argument("--vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-criteria-resolution-plan-closeout-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-resolution-plan-closeout-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-approval-criteria-closeout-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-approval-criteria-closeout-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-approval-criteria-closeout-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-approval-criteria-closeout-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-final-ticket-blockers-closeout-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-final-ticket-blockers-closeout-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-final-ticket-blockers-closeout-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-final-ticket-blockers-closeout-record", action="store_true")
    parser.add_argument(
        "--paper-live-f6-f7-audit",
        action="store_true",
        help="Create a saved-output F6/F7 audit for paper-live promotion readiness without broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-f6-f7-audit",
        action="store_true",
        help="Display the saved paper-live F6/F7 audit without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--paper-live-promotion-ladder-design",
        action="store_true",
        help="Create a saved-output generic promotion ladder design checkpoint without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-promotion-ladder-design",
        action="store_true",
        help="Display the saved generic promotion ladder design checkpoint without broker reads.",
    )
    parser.add_argument(
        "--paper-live-promotion-ladder-status",
        action="store_true",
        help="Create a saved-output paper-live promotion ladder status scaffold without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-promotion-ladder-status",
        action="store_true",
        help="Display the saved paper-live promotion ladder status scaffold without broker reads.",
    )
    parser.add_argument(
        "--paper-live-f7-accounting-proof",
        action="store_true",
        help="Create a saved-output F7 accounting proof checkpoint without rerunning backtests or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-f7-accounting-proof",
        action="store_true",
        help="Display the saved F7 accounting proof checkpoint without broker reads.",
    )
    parser.add_argument(
        "--paper-live-next-ladder-candidate-scope",
        action="store_true",
        help="Create a saved-output next ladder candidate scope report without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-next-ladder-candidate-scope",
        action="store_true",
        help="Display the saved next ladder candidate scope report without broker reads.",
    )
    parser.add_argument(
        "--paper-live-defensive-sleeve-ladder-scope-review",
        action="store_true",
        help="Create a saved-output defensive sleeve ladder-scope review without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-defensive-sleeve-ladder-scope-review",
        action="store_true",
        help="Display the saved defensive sleeve ladder-scope review without broker reads.",
    )
    parser.add_argument(
        "--paper-live-defensive-sleeve-manual-review",
        action="store_true",
        help="Create a saved-output defensive sleeve manual review pack without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-defensive-sleeve-manual-review",
        action="store_true",
        help="Display the saved defensive sleeve manual review pack without broker reads.",
    )
    parser.add_argument(
        "--paper-live-defensive-sleeve-preview-readiness",
        action="store_true",
        help="Create a saved-output defensive sleeve preview-readiness checkpoint without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-defensive-sleeve-preview-readiness",
        action="store_true",
        help="Display the saved defensive sleeve preview-readiness checkpoint without broker reads.",
    )
    parser.add_argument(
        "--paper-live-defensive-sleeve-evidence-quality",
        action="store_true",
        help="Create a saved-output defensive sleeve evidence-quality review without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-defensive-sleeve-evidence-quality",
        action="store_true",
        help="Display the saved defensive sleeve evidence-quality review without broker reads.",
    )
    parser.add_argument(
        "--paper-live-multi-sleeve-roadmap",
        action="store_true",
        help="Create a saved-output QQQ-led multi-sleeve paper-live roadmap without portfolio execution.",
    )
    parser.add_argument(
        "--show-paper-live-multi-sleeve-roadmap",
        action="store_true",
        help="Display the saved QQQ-led multi-sleeve paper-live roadmap without broker reads.",
    )
    parser.add_argument(
        "--paper-live-next-phase-backlog",
        action="store_true",
        help="Create a saved-output paper-live next-phase backlog without promotion or execution wiring.",
    )
    parser.add_argument(
        "--show-paper-live-next-phase-backlog",
        action="store_true",
        help="Display the saved paper-live next-phase backlog without broker reads.",
    )
    parser.add_argument(
        "--paper-live-multi-sleeve-evidence-gap",
        action="store_true",
        help="Create a saved-output QQQ-led multi-sleeve evidence-gap audit without rerunning research.",
    )
    parser.add_argument(
        "--show-paper-live-multi-sleeve-evidence-gap",
        action="store_true",
        help="Display the saved QQQ-led multi-sleeve evidence-gap audit without broker reads.",
    )
    parser.add_argument(
        "--paper-live-high-growth-evidence-gap",
        action="store_true",
        help="Create a saved-output high-growth sleeve evidence-gap audit without rerunning research.",
    )
    parser.add_argument(
        "--show-paper-live-high-growth-evidence-gap",
        action="store_true",
        help="Display the saved high-growth sleeve evidence-gap audit without broker reads.",
    )
    parser.add_argument(
        "--paper-live-high-growth-evidence-quality",
        action="store_true",
        help="Create a saved-output high-growth evidence quality review without rerunning research.",
    )
    parser.add_argument(
        "--show-paper-live-high-growth-evidence-quality",
        action="store_true",
        help="Display the saved high-growth evidence quality review without broker reads.",
    )
    parser.add_argument(
        "--paper-live-high-growth-manual-review-decision",
        action="store_true",
        help="Create a saved-output high-growth manual-review decision without rerunning research.",
    )
    parser.add_argument(
        "--show-paper-live-high-growth-manual-review-decision",
        action="store_true",
        help="Display the saved high-growth manual-review decision without broker reads.",
    )
    parser.add_argument(
        "--qqq100-paper-postcheck",
        action="store_true",
        help="Create a read-only QQQ100 paper postcheck; broker reads require --confirm-readonly-alpaca-check.",
    )
    parser.add_argument(
        "--show-qqq100-paper-postcheck",
        action="store_true",
        help="Display the saved QQQ100 paper postcheck without broker reads.",
    )
    parser.add_argument(
        "--qqq100-repeat-alignment-workflow-design",
        action="store_true",
        help="Create a saved-output-only QQQ100 repeat/alignment workflow design report.",
    )
    parser.add_argument(
        "--show-qqq100-repeat-alignment-workflow-design",
        action="store_true",
        help="Display the saved QQQ100 repeat/alignment workflow design without broker reads.",
    )
    parser.add_argument(
        "--multi-sleeve-strategy-monitor",
        action="store_true",
        help="Create a saved-output-only multi-sleeve strategy monitoring/design report.",
    )
    parser.add_argument(
        "--show-multi-sleeve-strategy-monitor",
        action="store_true",
        help="Display the saved multi-sleeve strategy monitor without broker or market-data reads.",
    )
    parser.add_argument(
        "--sleeve-research-scoreboard",
        action="store_true",
        help="Create a saved-output-only research scoreboard for candidate strategy sleeves.",
    )
    parser.add_argument(
        "--show-sleeve-research-scoreboard",
        action="store_true",
        help="Display the saved sleeve research scoreboard without broker or market-data reads.",
    )
    parser.add_argument(
        "--codex-qqq-defensive-crash-gate-research-pack",
        action="store_true",
        help="Create a saved-output-only Codex QQQ defensive crash-gate research pack.",
    )
    parser.add_argument(
        "--show-codex-qqq-defensive-crash-gate-research-pack",
        action="store_true",
        help="Display the saved Codex QQQ defensive crash-gate research pack without broker reads.",
    )
    parser.add_argument(
        "--sleeve-return-streams",
        action="store_true",
        help="Create research-only saved daily return streams for portfolio sleeves.",
    )
    parser.add_argument(
        "--show-sleeve-return-streams",
        action="store_true",
        help="Display the saved sleeve return-stream summary without broker reads.",
    )
    parser.add_argument(
        "--qqq100-stream-reconciliation",
        action="store_true",
        help="Create a research-only QQQ100 generated-stream reconciliation report.",
    )
    parser.add_argument(
        "--show-qqq100-stream-reconciliation",
        action="store_true",
        help="Display the saved QQQ100 stream reconciliation summary without broker reads.",
    )
    parser.add_argument(
        "--qqq100-benchmark-inputs-report",
        action="store_true",
        help="Create a saved-output-only report documenting the likely original QQQ100 benchmark inputs.",
    )
    parser.add_argument(
        "--show-qqq100-benchmark-inputs",
        action="store_true",
        help="Display the saved QQQ100 benchmark-input reconstruction without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-return-streams",
        action="store_true",
        help="Create research-only saved daily return streams for high-growth stock candidates.",
    )
    parser.add_argument(
        "--show-high-growth-return-streams",
        action="store_true",
        help="Display saved high-growth return-stream metrics without refreshing broker state.",
    )
    parser.add_argument(
        "--crypto-return-streams",
        action="store_true",
        help="Create research-only saved daily return streams for BTC/ETH crypto sleeves.",
    )
    parser.add_argument(
        "--show-crypto-return-streams",
        action="store_true",
        help="Display saved crypto return-stream metrics without refreshing market or broker state.",
    )
    parser.add_argument(
        "--multi-sleeve-portfolio-backtest",
        action="store_true",
        help="Create a saved-output-only multi-sleeve portfolio research backtest checkpoint.",
    )
    parser.add_argument(
        "--show-multi-sleeve-portfolio-backtest",
        action="store_true",
        help="Display the saved multi-sleeve portfolio backtest without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-robustness",
        action="store_true",
        help="Create a saved-output-only split robustness report for the high-growth multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-robustness",
        action="store_true",
        help="Display the saved multi-sleeve robustness report without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-crypto-review",
        action="store_true",
        help="Create a saved-output-only crypto split/cost/volatility review for the multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-crypto-review",
        action="store_true",
        help="Display the saved multi-sleeve crypto review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-crypto-containment-review",
        action="store_true",
        help="Create a saved-output-only crypto containment review for the current multi-sleeve lead.",
    )
    parser.add_argument(
        "--show-multi-sleeve-crypto-containment-review",
        action="store_true",
        help="Display the saved multi-sleeve crypto containment review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-allocation-policy-review",
        action="store_true",
        help="Create a saved-output-only allocation policy review for the crypto multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-allocation-policy-review",
        action="store_true",
        help="Display the saved multi-sleeve allocation policy review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-weight-sensitivity",
        action="store_true",
        help="Create a saved-output-only fixed weight-sensitivity review for the multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-weight-sensitivity",
        action="store_true",
        help="Display the saved multi-sleeve weight sensitivity review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-higher-growth-review",
        action="store_true",
        help="Create a saved-output-only higher-growth challenger review for the multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-higher-growth-review",
        action="store_true",
        help="Display the saved multi-sleeve higher-growth challenger review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-research-lead-decision",
        action="store_true",
        help="Create a saved-output-only research lead decision checkpoint for the multi-sleeve allocation.",
    )
    parser.add_argument(
        "--show-multi-sleeve-research-lead-decision",
        action="store_true",
        help="Display the saved multi-sleeve research lead decision without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-lead-state-refresh",
        action="store_true",
        help="Create a saved-output-only canonical lead-state checkpoint for the multi-sleeve research lead.",
    )
    parser.add_argument(
        "--show-multi-sleeve-lead-state",
        action="store_true",
        help="Display the saved canonical multi-sleeve lead state without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-high-growth-drawdown-decomposition",
        action="store_true",
        help="Create a saved-output-only high-growth drawdown decomposition for the multi-sleeve lead.",
    )
    parser.add_argument(
        "--show-multi-sleeve-high-growth-drawdown-decomposition",
        action="store_true",
        help="Display the saved multi-sleeve high-growth drawdown decomposition without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-sleeve-quality-review",
        action="store_true",
        help="Create a saved-output-only quality review for the high-growth research sleeve.",
    )
    parser.add_argument(
        "--show-high-growth-sleeve-quality-review",
        action="store_true",
        help="Display the saved high-growth sleeve quality review without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-component-attribution",
        action="store_true",
        help="Create a saved-output-only component attribution readiness review for the high-growth sleeve.",
    )
    parser.add_argument(
        "--show-high-growth-component-attribution",
        action="store_true",
        help="Display the saved high-growth component attribution review without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-component-streams",
        action="store_true",
        help="Create research-only component streams for the selected high-growth sleeve.",
    )
    parser.add_argument(
        "--show-high-growth-component-streams",
        action="store_true",
        help="Display the saved high-growth component streams summary without broker reads.",
    )
    parser.add_argument(
        "--high-growth-sleeve-concentration-review",
        action="store_true",
        help="Create a saved-output-only concentration review for the high-growth research sleeve.",
    )
    parser.add_argument(
        "--show-high-growth-sleeve-concentration-review",
        action="store_true",
        help="Display the saved high-growth sleeve concentration review without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-research-checkpoint",
        action="store_true",
        help="Create a saved-output-only checkpoint for the completed high-growth research chain.",
    )
    parser.add_argument(
        "--show-high-growth-research-checkpoint",
        action="store_true",
        help="Display the saved high-growth research checkpoint without broker or market-data reads.",
    )
    parser.add_argument(
        "--paper-execution-state-summary",
        action="store_true",
        help="Create a saved-output-only paper execution milestone/state summary without broker calls.",
    )
    parser.add_argument(
        "--show-paper-execution-state-summary",
        action="store_true",
        help="Display the saved paper execution state summary without reading broker state.",
    )
    parser.add_argument(
        "--execute-qqq100-paper",
        action="store_true",
        help="Manually align the saved QQQ100 preview signal with exactly one QQQ paper share; requires --confirm-qqq100-paper.",
    )
    parser.add_argument(
        "--confirm-qqq100-paper",
        action="store_true",
        help="Required confirmation for --execute-qqq100-paper.",
    )
    parser.add_argument(
        "--high-growth-stock-lab",
        action="store_true",
        help="Run a research-only concentrated single-stock growth/momentum lab without execution.",
    )
    parser.add_argument(
        "--show-high-growth-stock-lab",
        action="store_true",
        help="Display the saved high-growth stock lab summary without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-universe-expansion-report",
        action="store_true",
        help="Run a research-only fixed stock universe breadth sensitivity report without execution.",
    )
    parser.add_argument(
        "--show-high-growth-stock-universe-expansion-report",
        action="store_true",
        help="Display the saved high-growth stock universe expansion summary without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-drawdown-control-report",
        action="store_true",
        help="Run a research-only broad high-growth stock drawdown-control report without execution.",
    )
    parser.add_argument(
        "--show-high-growth-stock-drawdown-control-report",
        action="store_true",
        help="Display the saved high-growth stock drawdown-control summary without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-lead-decision-report",
        action="store_true",
        help="Create a saved-output high-growth stock lead decision report without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-lead-decision-report",
        action="store_true",
        help="Display the saved high-growth stock lead decision summary without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-manual-review-pack",
        action="store_true",
        help="Create a saved-output high-growth stock manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-manual-review-pack",
        action="store_true",
        help="Display the saved high-growth stock manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-risk-review-pack",
        action="store_true",
        help="Create a saved-output high-growth stock risk review pack without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-risk-review-pack",
        action="store_true",
        help="Display the saved high-growth stock risk review pack without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-risk-evidence-review",
        action="store_true",
        help="Create a saved-output high-growth stock risk evidence review without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-risk-evidence-review",
        action="store_true",
        help="Display the saved high-growth stock risk evidence review without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-branch-decision-checkpoint",
        action="store_true",
        help="Create a saved-output high-growth stock branch decision checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-branch-decision-checkpoint",
        action="store_true",
        help="Display the saved high-growth stock branch decision checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-final-validation-pack",
        action="store_true",
        help="Create a saved-output high-growth stock final validation pack without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-final-validation-pack",
        action="store_true",
        help="Display the saved high-growth stock final validation pack without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-strategy-discovery-sprint",
        action="store_true",
        help="Create a saved-output-only high-growth strategy discovery sprint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--show-high-growth-strategy-discovery-sprint",
        action="store_true",
        help="Display the saved high-growth strategy discovery sprint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--higher-growth-preview-readiness-pack",
        action="store_true",
        help="Create a saved-output-only manual preview-readiness pack for higher_growth_70_20_5_5 without broker reads or execution.",
    )
    parser.add_argument(
        "--show-higher-growth-preview-readiness-pack",
        action="store_true",
        help="Display the saved higher-growth preview-readiness pack without broker reads or execution.",
    )
    parser.add_argument(
        "--higher-growth-candidate-selection-decision",
        action="store_true",
        help="Create a saved-output-only decision choosing the next higher-growth preview-design review candidate.",
    )
    parser.add_argument(
        "--show-higher-growth-candidate-selection-decision",
        action="store_true",
        help="Display the saved higher-growth candidate selection decision without broker reads or execution.",
    )
    parser.add_argument(
        "--higher-growth-preview-design",
        action="store_true",
        help="Create a saved-output-only preview design for higher_growth_70_20_5_5 without creating signals, orders, or execution.",
    )
    parser.add_argument(
        "--show-higher-growth-preview-design",
        action="store_true",
        help="Display the saved higher-growth preview design without broker reads or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-research-sprint",
        action="store_true",
        help="Create a saved-output-only volatility-targeted growth research sprint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-research-sprint",
        action="store_true",
        help="Display the saved volatility-targeted growth research sprint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-manual-review-pack",
        action="store_true",
        help="Create a saved-output-only manual review pack for volatility-targeted growth candidates.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-manual-review-pack",
        action="store_true",
        help="Display the saved volatility-targeted growth manual review pack without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-robustness-checkpoint",
        action="store_true",
        help="Create a saved-output-only robustness checkpoint for the preferred volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-robustness-checkpoint",
        action="store_true",
        help="Display the saved volatility-targeted growth robustness checkpoint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-nearby-variants-review",
        action="store_true",
        help="Create a saved-output-only nearby-variants review for the preferred volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-nearby-variants-review",
        action="store_true",
        help="Display the saved volatility-targeted growth nearby-variants review without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-preview-readiness-decision",
        action="store_true",
        help="Create a saved-output-only preview-readiness decision for the volatility-targeted growth 15/20 candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-preview-readiness-decision",
        action="store_true",
        help="Display the saved volatility-targeted growth preview-readiness decision without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-preview-design",
        action="store_true",
        help="Create a saved-output-only preview design checkpoint for the selected volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-preview-design",
        action="store_true",
        help="Display the saved volatility-targeted growth preview design without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-preview-signal",
        action="store_true",
        help="Create a saved-output-only preview signal for the selected volatility-targeted growth candidate without action preview, orders, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-preview-signal",
        action="store_true",
        help="Display the saved volatility-targeted growth preview signal without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-action-preview-design",
        action="store_true",
        help="Create a saved-output-only action-preview design for the selected volatility-targeted growth candidate without creating actions, broker reads, orders, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-action-preview-design",
        action="store_true",
        help="Display the saved volatility-targeted growth action-preview design without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-action-preview",
        action="store_true",
        help="Create a saved-output-only action preview for the selected volatility-targeted growth candidate without broker reads, orders, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-action-preview",
        action="store_true",
        help="Display the saved volatility-targeted growth action preview without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-action-preview-quality-gate",
        action="store_true",
        help="Create a saved-output-only quality gate for the volatility-targeted growth action preview without broker reads, orders, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-action-preview-quality-gate",
        action="store_true",
        help="Display the saved volatility-targeted growth action-preview quality gate without broker reads, orders, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-position-comparison-design",
        action="store_true",
        help="Create a saved-output-only broker-position comparison design for volatility-targeted growth without broker reads or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-position-comparison-design",
        action="store_true",
        help="Display the saved volatility-targeted growth broker-position comparison design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-portfolio-risk-review",
        action="store_true",
        help="Create a saved-output-only portfolio-risk/manual-review report for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-portfolio-risk-review",
        action="store_true",
        help="Display the saved volatility-targeted growth portfolio-risk review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-portfolio-risk-policy-design",
        action="store_true",
        help="Create a saved-output-only portfolio-risk policy design for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-portfolio-risk-policy-design",
        action="store_true",
        help="Display the saved volatility-targeted growth portfolio-risk policy design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-decision",
        action="store_true",
        help="Create a saved-output-only paper-live/manual-review decision checkpoint for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-decision",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live decision checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-comparison-run-readiness",
        action="store_true",
        help="Create a saved-output-only run-readiness checkpoint before any future read-only broker-position comparison for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-comparison-run-readiness",
        action="store_true",
        help="Display the saved volatility-targeted growth broker-comparison run-readiness checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-position-comparison",
        action="store_true",
        help="Create a read-only/manual-review broker-position comparison for volatility-targeted growth; broker reads require --confirm-readonly-alpaca-check.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-position-comparison",
        action="store_true",
        help="Display the saved volatility-targeted growth broker-position comparison.",
    )
    parser.add_argument(
        "--vol-targeted-growth-post-comparison-decision",
        action="store_true",
        help="Create a saved-output-only post-comparison decision checkpoint for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-post-comparison-decision",
        action="store_true",
        help="Display the saved volatility-targeted growth post-comparison decision checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-stricter-paper-live-gate-design",
        action="store_true",
        help="Create a saved-output-only stricter manual paper-live gate design for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-stricter-paper-live-gate-design",
        action="store_true",
        help="Display the saved volatility-targeted growth stricter paper-live gate design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-gate-review",
        action="store_true",
        help="Create a saved-output-only gate review for limited manual candidate discussion of the volatility-targeted growth strategy.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-gate-review",
        action="store_true",
        help="Display the saved volatility-targeted growth gate review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-candidate-discussion-blocker-checklist",
        action="store_true",
        help="Create a saved-output-only final blocker checklist before volatility-targeted implementation work.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-candidate-discussion-blocker-checklist",
        action="store_true",
        help="Display the saved volatility-targeted growth candidate discussion blocker checklist.",
    )
    parser.add_argument(
        "--vol-targeted-growth-candidate-decision-record",
        action="store_true",
        help="Create a saved-output-only formal decision record for volatility-targeted manual candidate discussion.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-candidate-decision-record",
        action="store_true",
        help="Display the saved volatility-targeted growth candidate decision record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-candidate-discussion",
        action="store_true",
        help="Create a saved-output-only limited manual candidate discussion report for the volatility-targeted growth strategy.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-candidate-discussion",
        action="store_true",
        help="Display the saved volatility-targeted growth candidate discussion report.",
    )
    parser.add_argument(
        "--vol-targeted-growth-proposal-implementation-design",
        action="store_true",
        help="Create a saved-output-only implementation design checkpoint for the volatility-targeted growth proposal.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-proposal-implementation-design",
        action="store_true",
        help="Display the saved volatility-targeted growth proposal implementation design checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-proposal-preview-schema",
        action="store_true",
        help="Create a saved-output-only schema checkpoint for a future volatility-targeted proposal preview.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-proposal-preview-schema",
        action="store_true",
        help="Display the saved volatility-targeted growth proposal preview schema checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-proposal-preview",
        action="store_true",
        help="Create a saved-output-only non-executable proposal preview for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-proposal-preview",
        action="store_true",
        help="Display the saved volatility-targeted growth proposal preview.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-review",
        action="store_true",
        help="Create a saved-output-only seed-change review for the volatility-targeted growth proposal.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-evidence-pack",
        action="store_true",
        help="Create a saved-output-only evidence pack for a future volatility-targeted growth seed-change proposal.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-evidence-pack",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change evidence pack.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-risk-reward-comparison",
        action="store_true",
        help="Create a saved-output-only QQQ100 versus volatility risk/reward comparison for seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-risk-reward-comparison",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change risk/reward comparison.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-drawdown-stress-review",
        action="store_true",
        help="Create a saved-output-only drawdown/stress review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-drawdown-stress-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change drawdown/stress review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-cost-turnover-review",
        action="store_true",
        help="Create a saved-output-only cost/turnover review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-cost-turnover-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change cost/turnover review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-split-stability-review",
        action="store_true",
        help="Create a saved-output-only split-stability review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-split-stability-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change split-stability review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-component-sleeve-review",
        action="store_true",
        help="Create a saved-output-only component-sleeve review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-component-sleeve-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change component-sleeve review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-action-preview-design",
        action="store_true",
        help="Create a saved-output-only action-preview design checkpoint for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-action-preview-design",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change action-preview design checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-proposal-document",
        action="store_true",
        help="Create a saved-output-only proposal-document draft checkpoint for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-proposal-document",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change proposal-document checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-broker-exposure-review",
        action="store_true",
        help="Create a saved-output-only broker-exposure review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-broker-exposure-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change broker-exposure review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-manual-review-checkpoint",
        action="store_true",
        help="Create a saved-output-only manual-review checkpoint for completed volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-manual-review-checkpoint",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change manual-review checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-formal-seed-change-proposal",
        action="store_true",
        help="Create a saved-output-only formal proposal document for volatility seed-change manual review.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-formal-seed-change-proposal",
        action="store_true",
        help="Display the saved volatility-targeted growth formal seed-change proposal.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-manual-approval-record",
        action="store_true",
        help="Create a saved-output-only manual approval record for volatility seed-change implementation design.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-manual-approval-record",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change manual approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-implementation-design",
        action="store_true",
        help="Create a saved-output-only implementation design for a future volatility seed change.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-implementation-design",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change implementation design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-dry-run-diff",
        action="store_true",
        help="Create a saved-output-only dry-run diff for a future volatility seed switch.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-dry-run-diff",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change dry-run diff.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-manual-approval-gate",
        action="store_true",
        help="Create a saved-output-only manual paper-live approval gate for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-manual-approval-gate",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live manual approval gate.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-action-preview-pack",
        action="store_true",
        help="Create a saved-output-only paper-live action-preview pack for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-action-preview-pack",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live action-preview pack.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-comparison-reconciliation",
        action="store_true",
        help="Create a saved-output-only broker-comparison reconciliation for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-comparison-reconciliation",
        action="store_true",
        help="Display the saved volatility-targeted growth broker-comparison reconciliation.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-candidate-approval-record",
        action="store_true",
        help="Create a saved-output-only candidate-discussion approval record for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-candidate-approval-record",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live candidate approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-allocation-cap-sleeve-mapping-policy",
        action="store_true",
        help="Create a saved-output-only allocation cap and sleeve mapping policy for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-allocation-cap-sleeve-mapping-policy",
        action="store_true",
        help="Display the saved volatility-targeted growth allocation cap and sleeve mapping policy.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-executable-target-position-plan",
        action="store_true",
        help="Create a saved-output-only non-executable target-position plan for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-executable-target-position-plan",
        action="store_true",
        help="Display the saved volatility-targeted growth non-executable target-position plan.",
    )
    parser.add_argument(
        "--vol-targeted-growth-order-ticket-boundary-design",
        action="store_true",
        help="Create a saved-output-only order-ticket boundary design for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-order-ticket-boundary-design",
        action="store_true",
        help="Display the saved volatility-targeted growth order-ticket boundary design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-prerequisites-review",
        action="store_true",
        help="Create a saved-output-only executable ticket prerequisites review for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-prerequisites-review",
        action="store_true",
        help="Display the saved volatility-targeted growth executable ticket prerequisites review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-gap-list",
        action="store_true",
        help="Create a saved-output-only executable ticket gap list for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-gap-list",
        action="store_true",
        help="Display the saved volatility-targeted growth executable ticket gap list.",
    )
    parser.add_argument(
        "--vol-targeted-growth-manual-execution-design-approval-gate",
        action="store_true",
        help="Create a saved-output-only manual execution-design approval gate for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-manual-execution-design-approval-gate",
        action="store_true",
        help="Display the saved volatility-targeted growth manual execution-design approval gate.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-submitting-ticket-schema-design",
        action="store_true",
        help="Create a saved-output-only non-submitting ticket schema design for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-submitting-ticket-schema-design",
        action="store_true",
        help="Display the saved volatility-targeted growth non-submitting ticket schema design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-submitting-ticket-instance-design",
        action="store_true",
        help="Create a saved-output-only non-submitting ticket-instance design for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-submitting-ticket-instance-design",
        action="store_true",
        help="Display the saved volatility-targeted growth non-submitting ticket-instance design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-design",
        action="store_true",
        help="Create a saved-output-only fresh broker pre-ticket gate design for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-design",
        action="store_true",
        help="Display the saved volatility-targeted growth fresh broker pre-ticket gate design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness",
        action="store_true",
        help="Create a saved-output-only run-readiness checkpoint for the future fresh broker pre-ticket gate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness",
        action="store_true",
        help="Display the saved volatility-targeted growth fresh broker pre-ticket gate run-readiness checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
        action="store_true",
        help="Run the explicitly confirmed read-only fresh broker pre-ticket gate for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
        action="store_true",
        help="Display the saved volatility-targeted growth fresh broker pre-ticket gate run.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-execution-blocker-rollup",
        action="store_true",
        help="Create a saved-output-only paper-live execution blocker rollup for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-execution-blocker-rollup",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live execution blocker rollup.",
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
        "--codex-ambitious-validation",
        action="store_true",
        help="Create a saved-output validation checkpoint for the Codex ambitious persistence candidate.",
    )
    parser.add_argument(
        "--show-codex-ambitious-validation",
        action="store_true",
        help="Display the saved Codex ambitious validation checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--codex-ambitious-split-drawdown-validation",
        action="store_true",
        help="Create a research-only split and drawdown-window validation for the Codex ambitious candidate.",
    )
    parser.add_argument(
        "--show-codex-ambitious-split-drawdown-validation",
        action="store_true",
        help="Display the saved Codex ambitious split/drawdown validation without refreshing data.",
    )
    parser.add_argument(
        "--codex-ambitious-lead-decision",
        action="store_true",
        help="Create a saved-output final research lead decision checkpoint for the Codex ambitious candidate.",
    )
    parser.add_argument(
        "--show-codex-ambitious-lead-decision",
        action="store_true",
        help="Display the saved Codex ambitious lead decision checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--crypto-research-preview",
        action="store_true",
        help="Create a research-only crypto scaffold preview without execution.",
    )
    parser.add_argument(
        "--crypto-universe-readiness-report",
        action="store_true",
        help="Create a research-only crypto universe data-readiness report without strategy signals.",
    )
    parser.add_argument(
        "--show-crypto-universe-readiness-report",
        action="store_true",
        help="Display the saved crypto universe readiness report without refreshing data.",
    )
    parser.add_argument(
        "--expanded-crypto-strategy-lab",
        action="store_true",
        help="Run a research-only expanded crypto strategy lab over readiness-eligible symbols.",
    )
    parser.add_argument(
        "--show-expanded-crypto-strategy-lab",
        action="store_true",
        help="Display the saved expanded crypto strategy lab without refreshing data.",
    )
    parser.add_argument(
        "--expanded-crypto-robustness-report",
        action="store_true",
        help="Create a research-only expanded crypto robustness and equal-weight reality-check report.",
    )
    parser.add_argument(
        "--show-expanded-crypto-robustness-report",
        action="store_true",
        help="Display the saved expanded crypto robustness report without refreshing data.",
    )
    parser.add_argument(
        "--crypto-equal-weight-crash-gate",
        action="store_true",
        help="Run a research-only equal-weight crypto crash-gate report without execution.",
    )
    parser.add_argument(
        "--show-crypto-equal-weight-crash-gate",
        action="store_true",
        help="Display the saved equal-weight crypto crash-gate report without refreshing data.",
    )
    parser.add_argument(
        "--crypto-equal-weight-volatility-scaling",
        action="store_true",
        help="Run a research-only equal-weight crypto volatility-scaling report without execution.",
    )
    parser.add_argument(
        "--show-crypto-equal-weight-volatility-scaling",
        action="store_true",
        help="Display the saved equal-weight crypto volatility-scaling report without refreshing data.",
    )
    parser.add_argument(
        "--crypto-equal-weight-capped-risk-report",
        action="store_true",
        help="Run a research-only equal-weight crypto capped/equal-risk contribution report without execution.",
    )
    parser.add_argument(
        "--show-crypto-equal-weight-capped-risk-report",
        action="store_true",
        help="Display the saved equal-weight crypto capped/equal-risk report without refreshing data.",
    )
    parser.add_argument(
        "--expanded-crypto-lead-decision",
        action="store_true",
        help="Create a saved-output research-only expanded crypto lead decision checkpoint.",
    )
    parser.add_argument(
        "--show-expanded-crypto-lead-decision",
        action="store_true",
        help="Display the saved expanded crypto lead decision checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--crypto-lead-split-sensitivity-diagnosis",
        action="store_true",
        help="Create a saved-output research-only split-sensitivity diagnosis for the current crypto research lead.",
    )
    parser.add_argument(
        "--show-crypto-lead-split-sensitivity-diagnosis",
        action="store_true",
        help="Display the saved crypto lead split-sensitivity diagnosis without refreshing data.",
    )
    parser.add_argument(
        "--expanded-crypto-manual-review-pack",
        action="store_true",
        help="Create a saved-output research-only manual review pack for the expanded crypto branch.",
    )
    parser.add_argument(
        "--show-expanded-crypto-manual-review-pack",
        action="store_true",
        help="Display the saved expanded crypto manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--project-research-state-refresh",
        action="store_true",
        help="Create a saved-output research-only project-wide stock/ETF and crypto state refresh.",
    )
    parser.add_argument(
        "--show-project-research-state-refresh",
        action="store_true",
        help="Display the saved project research state refresh without refreshing data.",
    )
    parser.add_argument(
        "--show-current-research-state",
        action="store_true",
        help="Display a concise saved-state summary of the current stock/ETF and crypto research branches.",
    )
    parser.add_argument(
        "--project-research-state-quality-report",
        action="store_true",
        help="Create a report-only quality check for saved project research state files.",
    )
    parser.add_argument(
        "--stock-etf-paper-execution-readiness-report",
        action="store_true",
        help="Create a saved-data report-only stock/ETF paper execution discussion readiness review.",
    )
    parser.add_argument(
        "--alpaca-paper-readiness-report",
        action="store_true",
        help="Create an Alpaca paper readiness/preflight report without approving execution.",
    )
    parser.add_argument(
        "--alpaca-connectivity-diagnostics",
        action="store_true",
        help="Create unauthenticated DNS/TCP 443 diagnostics for Alpaca API and general HTTPS endpoints.",
    )
    parser.add_argument(
        "--show-alpaca-connectivity-diagnostics",
        action="store_true",
        help="Display the saved Alpaca connectivity diagnostics summary without refreshing checks.",
    )
    parser.add_argument(
        "--confirm-readonly-alpaca-check",
        action="store_true",
        help="With --alpaca-paper-readiness-report only, explicitly allow a read-only Alpaca paper account/status check.",
    )
    parser.add_argument(
        "--paper-order-smoke-test-readiness-pack",
        action="store_true",
        help="Create a report-only readiness pack for discussing a future tiny manual paper-order smoke test.",
    )
    parser.add_argument(
        "--paper-order-smoke-test-live-preflight",
        action="store_true",
        help="Create a read-only/report-only live preflight for a future tiny manual paper-order smoke test.",
    )
    parser.add_argument(
        "--paper-order-smoke-test-postcheck",
        action="store_true",
        help="Create a read-only/report-only postcheck after a future tiny manual paper-order smoke test.",
    )
    parser.add_argument(
        "--future-refresh-cron-readiness-pack",
        action="store_true",
        help="Create a report-only readiness pack for a future safe refresh Hermes cron review.",
    )
    parser.add_argument(
        "--paper-order-smoke-test-runbook-check",
        action="store_true",
        help="Create a static report-only check for the manual paper-order smoke-test runbook.",
    )
    parser.add_argument(
        "--paper-smoke-test-kill-switch-diagnosis",
        action="store_true",
        help="Create a saved-output diagnosis for paper smoke-test kill-switch blockers without execution.",
    )
    parser.add_argument(
        "--show-paper-smoke-test-kill-switch-diagnosis",
        action="store_true",
        help="Display the saved paper smoke-test kill-switch diagnosis without refreshing data.",
    )
    parser.add_argument(
        "--ticker",
        default="",
        help="Ticker for read-only/report-only smoke-test preflight commands.",
    )
    parser.add_argument(
        "--side",
        default="",
        help="Side for read-only/report-only smoke-test preflight commands: buy or sell.",
    )
    parser.add_argument(
        "--quantity",
        default="",
        help="Quantity for read-only/report-only smoke-test preflight commands.",
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
        help="With --preview-promoted-actions or --qqq100-action-preview only, read Alpaca paper positions for preview context without trading.",
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
