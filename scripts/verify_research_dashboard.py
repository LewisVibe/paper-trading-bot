from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.research_dashboard as dashboard
from trading_bot.research.research_dashboard import build_research_dashboard
from trading_bot.runners import research_reports


FORBIDDEN_SOURCE_TOKENS = [
    "yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_open_orders_for_ticker",
    "decide_trade",
    "download_close_prices",
    "download_backtest_prices",
    "download_slow_sma_preview_prices",
    "configure_yfinance_cache",
    "sqlite3",
    "Flask",
    "Streamlit",
    "FastAPI",
    "Dash(",
    "HTTPServer",
]


def main() -> int:
    failures: list[str] = []
    verify_fixture_dashboard(failures)
    verify_missing_inputs(failures)
    verify_source_safety(failures)

    if failures:
        print("Research dashboard verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Research dashboard verification passed.")
    return 0


def verify_fixture_dashboard(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture_data(root)
        result = build_research_dashboard(root)
        if not result.output_path.exists():
            failures.append("research_dashboard.html was not created")
        html_text = result.output_path.read_text(encoding="utf-8")
        if result.missing_inputs:
            failures.append("fixture dashboard should not have missing inputs")

    for expected in [
        "RESEARCH DASHBOARD",
        "STATIC SAVED-CSV DISPLAY ONLY",
        "No execution approval",
        "No execution approval. No orders. No Alpaca calls. No market-data refresh.",
        "What This Means",
        "Project Research State",
        "codex_ambitious_concentrated_growth_persistence",
        "crypto_equal_weight_ex_highest_vol_2",
        "execution_approved",
        "scheduling_approved",
        "pause_strategy_iterations_and_improve_reporting",
        "Next Useful Commands",
        "Execution Safety State",
        "Paper Execution Protection",
        "Normal Bot Execution Policy",
        "Static saved-CSV display only. No execution approval, no order actions, and normal bot remains separate from defensive paper execution.",
        "Optional section: missing safety CSVs do not block dashboard generation.",
        "protected_by_kill_switch_preflight",
        "option_a_keep_normal_bot_dry_run_first",
        "separate_command_required",
        "Execution eligible",
        "Main blocker",
        "AAPL/SPY strategy disagreement",
        "Kill-switch status",
        "Missing inputs",
        "False",
        "monthly_etf_momentum_rotation",
        "volatility_managed_dual_momentum_etf",
        "adaptive_risk_on_off_momentum",
        "Defensive Research State",
        "robust_diagnostic_candidate_not_strategy",
        "paused_not_useful",
        "blocked_no_execution_approval",
        "blocked_strategy_disagreement",
        "AAPL",
        "SPY",
        "MSFT",
        "Crypto remains research/monitoring only. Crypto execution is disabled.",
        "ETF Breadth Regime",
        "useful_diagnostic_not_strategy",
        "No localhost server was started. No execution approval was granted.",
        "python bot.py --refresh-promoted-review",
        "python bot.py --project-research-state-refresh",
        "python bot.py --build-research-dashboard",
    ]:
        if expected not in html_text:
            failures.append(f"dashboard missing expected text: {expected}")
    if "http://" in html_text or "https://" in html_text or "cdn" in html_text.lower():
        failures.append("dashboard should not require external network links or CDNs")
    if "super-secret" in html_text:
        failures.append("dashboard must not include config.json or secret contents")


def verify_missing_inputs(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "data").mkdir(parents=True, exist_ok=True)
        result = build_research_dashboard(root)
        html_text = result.output_path.read_text(encoding="utf-8")
        if len(result.missing_inputs) != len(dashboard.DASHBOARD_INPUTS):
            failures.append("missing-input dashboard should report every absent saved CSV")
    for expected_command in [
        "python bot.py --research-report",
        "python bot.py --refresh-promoted-review",
        "python bot.py --execution-eligibility-report",
    ]:
        if expected_command not in html_text:
            failures.append(f"missing-input section should mention {expected_command}")
    if "No saved rows available." not in html_text:
        failures.append("dashboard should handle missing CSVs without crashing")
    for optional_path in [
        "data/paper_execution_protection_report.csv",
        "data/normal_bot_execution_policy_report.csv",
        "data/project_research_state_summary.csv",
        "data/project_research_state_refresh.csv",
        "data/project_research_state_next_steps.csv",
    ]:
        if optional_path in {path for path, _ in result.missing_inputs}:
            failures.append(f"{optional_path} should remain optional, not required")


def verify_source_safety(failures: list[str]) -> None:
    source = inspect.getsource(dashboard)
    runner_source = inspect.getsource(research_reports.run_build_research_dashboard_command)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"research dashboard should not reference {token}")
        if token in runner_source:
            failures.append(f"research dashboard runner should not reference {token}")
    if "config.json" in source:
        failures.append("research dashboard should not read or print config.json contents")
    for token in [
        "data/project_research_state_summary.csv",
        "data/project_research_state_refresh.csv",
        "data/project_research_state_next_steps.csv",
        "codex_ambitious_concentrated_growth_persistence",
        "crypto_equal_weight_ex_highest_vol_2",
        "execution_approved",
        "scheduling_approved",
    ]:
        if token not in source:
            failures.append(f"research dashboard project-state panel missing token: {token}")


def write_fixture_data(root: Path) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "charts").mkdir(parents=True, exist_ok=True)
    (data_dir / "charts" / "etf_defensive_equity_comparison.png").write_bytes(b"png")
    (data_dir / "charts" / "etf_defensive_drawdown_comparison.png").write_bytes(b"png")
    write_csv(data_dir / "research_report.csv", [{"strategy_name": "buy_and_hold_baseline", "period": "full_period"}])
    write_csv(data_dir / "walk_forward_report.csv", [{"strategy_name": "monthly_etf_momentum_rotation", "robustness_label": "improved_out_of_sample"}])
    write_csv(
        data_dir / "defensive_candidate_comparison.csv",
        [
            defensive_row("monthly_etf_momentum_rotation", "2", "1", "preferred_defensive_candidate"),
            defensive_row("volatility_managed_dual_momentum_etf", "1", "2", "promising_but_split_sensitive"),
            defensive_row("adaptive_risk_on_off_momentum", "3", "3", "secondary_defensive_candidate"),
        ],
    )
    write_csv(
        data_dir / "defensive_research_state_report.csv",
        [
            {
                "component": "monthly_etf_momentum_rotation",
                "category": "defensive_candidate",
                "state_label": "preferred_defensive_candidate",
                "headline_metric": "policy_rank",
                "headline_value": "1",
                "interpretation": "ETF rotation remains preferred.",
                "required_next_step": "Keep research-only.",
                "execution_approved": "False",
            },
            {
                "component": "etf_breadth_regime_allocation",
                "category": "diagnostic_filter",
                "state_label": "robust_diagnostic_candidate_not_strategy",
                "headline_metric": "robustness_label",
                "headline_value": "robust_diagnostic_candidate",
                "interpretation": "Breadth is a diagnostic/filter idea.",
                "required_next_step": "Compare against ETF rotation and vol-managed ETF.",
                "execution_approved": "False",
            },
            {
                "component": "short_research",
                "category": "paused_research",
                "state_label": "paused_not_useful",
                "headline_metric": "research_status",
                "headline_value": "not_useful",
                "interpretation": "Short research remains paused.",
                "required_next_step": "Do not add short preview or execution.",
                "execution_approved": "False",
            },
            {
                "component": "execution_state",
                "category": "execution_boundary",
                "state_label": "blocked_no_execution_approval",
                "headline_metric": "eligibility_status",
                "headline_value": "blocked_for_review",
                "interpretation": "Execution remains blocked.",
                "required_next_step": "Resolve blockers before execution discussion.",
                "execution_approved": "False",
            },
        ],
    )
    write_csv(
        data_dir / "etf_defensive_drawdown_comparison.csv",
        [
            {
                "comparison_period": "split_80_20_out_of_sample",
                "strategy_name": "volatility_managed_dual_momentum_etf",
                "drawdown_depth_pct": "10.1051",
                "matching_other_strategy_drawdown_pct": "11.2666",
                "drawdown_advantage_pct": "1.1615",
                "split_80_20_oos_calmar": "0.50",
                "interpretation_label": "lower_drawdown_but_lower_return",
                "interpretation_reason": "Lower drawdown alone does not displace ETF rotation.",
            }
        ],
    )
    write_csv(
        data_dir / "portfolio_risk_policy_report.csv",
        [
            {"risk_policy_name": "strategy_disagreement_policy", "risk_policy_status": "blocked_for_review", "finding": "AAPL and SPY disagreement", "required_next_step": "Review.", "execution_approved": "False"},
            {"risk_policy_name": "kill_switch_policy", "risk_policy_status": "not_implemented_future_work", "finding": "Future work.", "required_next_step": "Design.", "execution_approved": "False"},
        ],
    )
    write_csv(
        data_dir / "execution_eligibility_report.csv",
        [
            {"eligibility_check_name": "promoted_strategy_disagreement", "eligibility_status": "blocked_for_review", "finding": "AAPL, SPY", "blocking_reason": "Strategy disagreement blocks execution discussion.", "required_next_step": "Resolve.", "execution_approved": "False"},
            {"eligibility_check_name": "kill_switch_readiness", "eligibility_status": "not_ready", "finding": "No runtime kill switch.", "blocking_reason": "No runtime paper kill-switch enforcement exists yet.", "required_next_step": "Design.", "execution_approved": "False"},
            {"eligibility_check_name": "final_execution_eligibility", "eligibility_status": "blocked_for_review", "finding": "Execution eligible: False.", "blocking_reason": "No execution approval.", "required_next_step": "Resolve.", "execution_approved": "False"},
        ],
    )
    write_csv(
        data_dir / "promoted_decision_preview.csv",
        [
            {"ticker": "AAPL", "consensus_state": "mixed_long_flat", "long_votes": "2", "flat_votes": "1", "decision_state": "blocked_strategy_disagreement", "execution_approved": "False", "reason": "Disagreement."},
            {"ticker": "MSFT", "consensus_state": "unanimous_flat", "long_votes": "0", "flat_votes": "3", "decision_state": "no_action_unanimous_flat", "execution_approved": "False", "reason": "No action."},
            {"ticker": "SPY", "consensus_state": "mixed_long_flat", "long_votes": "2", "flat_votes": "1", "decision_state": "blocked_strategy_disagreement", "execution_approved": "False", "reason": "Disagreement."},
        ],
    )
    write_csv(
        data_dir / "crypto_research_state_report.csv",
        [
            {"symbol": "BTC/USD", "best_research_candidate": "crypto_buy_above_200_with_vol_gate", "decision_status": "research_watchlist", "current_desired_position": "flat", "research_conclusion": "useful but split-sensitive", "next_research_step": "monitor", "execution_approved": "False"},
            {"symbol": "ETH/USD", "best_research_candidate": "crypto_buy_above_200_exit_below_200", "decision_status": "strongest_research_candidate", "current_desired_position": "flat", "research_conclusion": "useful but research-only", "next_research_step": "monitor", "execution_approved": "False"},
            {"symbol": "LTC/USD", "best_research_candidate": "", "decision_status": "not_useful", "current_desired_position": "flat", "research_conclusion": "researched but not useful", "next_research_step": "pause", "execution_approved": "False"},
        ],
    )
    write_csv(data_dir / "deployment_readiness_report.csv", [{"check_name": "repo_safety_verifier", "check_status": "pass", "execution_approved": "False"}])
    write_csv(data_dir / "paper_kill_switch_readiness_report.csv", [{"check_name": "no_existing_kill_switch_enforcement", "check_status": "not_implemented_future_work", "execution_approved": "False"}])
    write_csv(
        data_dir / "project_research_state_summary.csv",
        [
            {"metric_name": "stock_etf_active_research_lead", "metric_value": "codex_ambitious_concentrated_growth_persistence", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
            {"metric_name": "stock_etf_status_and_blocker", "metric_value": "codex_ambitious_active_research_lead_cost_review_required; blocker=25 bps cost review not survived", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
            {"metric_name": "crypto_research_lead", "metric_value": "crypto_equal_weight_ex_highest_vol_2", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
            {"metric_name": "crypto_status_and_blockers", "metric_value": "crypto_manual_review_not_ready_for_preview_discussion; blockers=fixed split sensitivity; exclusion-rule instability; BNB/TRX outlier dependence", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
            {"metric_name": "rejected_or_downgraded_families", "metric_value": "crypto hard crash gates rejected for return drag; crypto volatility/drawdown throttles downgraded because drawdown barely improved or return collapsed", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
            {"metric_name": "recommended_next_step", "metric_value": "pause_strategy_iterations_and_improve_reporting", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
        ],
    )
    write_csv(
        data_dir / "project_research_state_refresh.csv",
        [
            {"section": "execution_safety_state", "metric_name": "execution_approved", "metric_value": "false", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
            {"section": "scheduling_safety_state", "metric_name": "scheduling_approved", "metric_value": "false", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
        ],
    )
    write_csv(
        data_dir / "project_research_state_next_steps.csv",
        [
            {"check_name": "pause_strategy_iterations_and_improve_reporting", "metric_value": "Pause new variants and improve reporting.", "execution_approved": "False", "scheduling_approved": "False", "preview_promotion_approved": "False"},
        ],
    )
    write_csv(
        data_dir / "codex_ambitious_lead_decision_summary.csv",
        [{"metric_name": "selected_research_lead", "metric_value": "codex_ambitious_concentrated_growth_persistence", "execution_approved": "False"}],
    )
    write_csv(
        data_dir / "expanded_crypto_manual_review_summary.csv",
        [{"metric_name": "blocker_counts", "metric_value": "blocked_for_manual_review=5", "execution_approved": "False"}],
    )
    write_csv(
        data_dir / "expanded_crypto_lead_decision_summary.csv",
        [{"metric_name": "selected_crypto_research_lead", "metric_value": "crypto_equal_weight_ex_highest_vol_2", "execution_approved": "False"}],
    )
    write_csv(
        data_dir / "paper_execution_protection_report.csv",
        [
            {
                "execution_path": "manual_paper_order_test",
                "protection_status": "protected_by_kill_switch_preflight",
                "finding": "--paper-order-test has preflight and is blocked.",
                "currently_blocks_execution": "True",
                "required_next_step": "Keep blocked.",
                "execution_approved": "False",
            },
            {
                "execution_path": "slow_sma_paper_execution",
                "protection_status": "protected_by_kill_switch_preflight",
                "finding": "--execute-slow-sma-paper has preflight and is blocked.",
                "currently_blocks_execution": "True",
                "required_next_step": "Keep blocked.",
                "execution_approved": "False",
            },
            {
                "execution_path": "normal_bot_order_path",
                "protection_status": "deliberately_unchanged_future_work",
                "finding": "Normal bot remains separate.",
                "currently_blocks_execution": "True",
                "required_next_step": "Future scoped task only.",
                "execution_approved": "False",
            },
        ],
    )
    write_csv(
        data_dir / "normal_bot_execution_policy_report.csv",
        [
            {
                "policy_area": "normal_bot_path_policy",
                "policy_status": "deliberately_non_defensive_execution_path",
                "finding": "Normal bot remains separate from defensive paper execution.",
                "required_next_step": "Keep separate.",
                "execution_approved": "False",
            },
            {
                "policy_area": "future_defensive_execution_policy",
                "policy_status": "separate_command_required",
                "finding": "Future defensive execution must use a separate scoped command.",
                "required_next_step": "Do not use normal bot.",
                "execution_approved": "False",
            },
            {
                "policy_area": "overall_policy",
                "policy_status": "option_a_keep_normal_bot_dry_run_first",
                "finding": "Option A is active.",
                "required_next_step": "Keep dry-run-first.",
                "execution_approved": "False",
            },
        ],
    )
    write_csv(
        data_dir / "etf_breadth_regime_backtest.csv",
        [
            {"period": "full_period", "cagr_pct": "5.2231", "sharpe_ratio": "0.4274", "max_drawdown_pct": "25.5851", "calmar_ratio": "0.2041", "exposure_pct": "75.0", "robustness_status": "research_only_pending_comparison"},
            {"period": "split_70_30_out_of_sample", "cagr_pct": "10.8791", "sharpe_ratio": "0.8343", "max_drawdown_pct": "10.7156", "calmar_ratio": "1.0153", "exposure_pct": "80.0", "robustness_status": "single_oos_split_initial_research"},
        ],
    )
    write_csv(
        data_dir / "etf_breadth_regime_summary.csv",
        [
            {"regime": "risk_on", "pct_of_days": "71.8377", "average_breadth_pct": "80.0"},
            {"regime": "neutral", "pct_of_days": "3.7788", "average_breadth_pct": "50.0"},
            {"regime": "defensive", "pct_of_days": "10.2625", "average_breadth_pct": "35.0"},
            {"regime": "cash_protection", "pct_of_days": "14.1209", "average_breadth_pct": "15.0"},
        ],
    )
    write_csv(
        data_dir / "etf_breadth_regime_decision_report.csv",
        [
            {"decision_label": "useful_diagnostic_not_strategy", "comparison_status": "compared_to_saved_defensive_candidates", "finding": "Breadth is useful as a diagnostic.", "required_next_step": "Keep research-only."}
        ],
    )


def defensive_row(strategy_name: str, metric_rank: str, policy_rank: str, status: str) -> dict[str, str]:
    return {
        "strategy_name": strategy_name,
        "metric_rank": metric_rank,
        "policy_rank": policy_rank,
        "comparison_status": status,
        "out_of_sample_sharpe": "1.0",
        "out_of_sample_calmar": "1.1",
        "out_of_sample_max_drawdown_pct": "12.3",
        "comparison_reason": "fixture",
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
