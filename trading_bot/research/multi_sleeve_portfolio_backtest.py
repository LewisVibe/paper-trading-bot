"""Saved-output-only multi-sleeve portfolio research backtest checkpoint.

This report compares QQQ100 against feasible and proposed sleeve combinations
using saved CSV artefacts only. It labels missing return streams explicitly and
does not call Alpaca, refresh market data, read live positions, create orders,
write SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FINAL_BACKTEST_STATUS = "multi_sleeve_candidate_needs_more_data"
FINAL_STATUS_NOT_BETTER_THAN_GENERATED_QQQ100 = "multi_sleeve_candidate_not_better_than_generated_qqq100"
FINAL_STATUS_PROMISING_NEEDS_RECONCILIATION = "multi_sleeve_candidate_promising_needs_reconciliation"
FINAL_STATUS_PROMISING_RECOVERED_REFERENCE = "multi_sleeve_candidate_promising_recovered_reference_review"
FINAL_STATUS_PROMISING_NEEDS_CRYPTO_POLICY_REVIEW = "multi_sleeve_candidate_promising_needs_crypto_and_policy_review"
QQQ100_REFERENCE = "qqq100_only_reference"
QQQ100_SLEEVE = "qqq100_core_trend_sleeve"
QQQ100_STRATEGY = "qqq_100_trend_gate"
RECOVERED_QQQ100_REFERENCE = "qqq100_recovered_reference_stream"
RECOVERED_QQQ100_SOURCE_CANDIDATE = "qqq100_recovered_inputs_sma200_close_to_close_10bps"
RECOVERED_REFERENCE_READY_STATUS = "qqq100_reconstruction_close_enough_for_research_review"
TOP_MULTI_SLEEVE_CANDIDATE = "qqq100_plus_cash_defensive_reference"
BIGGEST_BLOCKER = "missing_saved_return_streams_for_non_qqq_sleeves"
RECOMMENDED_NEXT_STEP = "collect_saved_daily_return_streams_before_candidate_label_change"
MISSING = "missing_saved_metrics"
MISSING_RETURN_STREAM = "missing_saved_return_stream"

INPUT_FILES = {
    "project_research_state": Path("data/project_research_state_summary.csv"),
    "qqq100_preview_readiness": Path("data/qqq100_preview_candidate_readiness_pack.csv"),
    "qqq100_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq_lead_decision": Path("data/qqq_lead_decision_report.csv"),
    "sleeve_scoreboard": Path("data/sleeve_research_scoreboard.csv"),
    "sleeve_candidates": Path("data/sleeve_research_candidates.csv"),
    "codex_defensive_pack": Path("data/codex_qqq_defensive_crash_gate_research_pack.csv"),
    "codex_defensive_candidates": Path("data/codex_qqq_defensive_crash_gate_candidates.csv"),
    "high_growth_lab": Path("data/high_growth_stock_lab_results.csv"),
    "high_growth_final_validation": Path("data/high_growth_stock_final_validation_pack.csv"),
    "high_growth_branch": Path("data/high_growth_stock_branch_decision_checkpoint.csv"),
    "crypto_lab": Path("data/crypto_strategy_lab_results.csv"),
    "crypto_state": Path("data/crypto_research_state_report.csv"),
    "crypto_lead": Path("data/expanded_crypto_lead_decision.csv"),
    "multi_sleeve_monitor": Path("data/multi_sleeve_strategy_monitor.csv"),
    "sleeve_return_streams": Path("data/sleeve_return_streams.csv"),
    "high_growth_return_streams": Path("data/high_growth_return_streams.csv"),
    "qqq100_recovered_reference_stream": Path("data/qqq100_recovered_reference_stream.csv"),
    "qqq100_recovered_reference_metrics": Path("data/qqq100_recovered_reference_metrics.csv"),
}

OUTPUT_FILES = {
    "backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "sleeves": Path("data/multi_sleeve_portfolio_backtest_sleeves.csv"),
    "allocations": Path("data/multi_sleeve_portfolio_backtest_allocations.csv"),
    "rankings": Path("data/multi_sleeve_portfolio_backtest_rankings.csv"),
    "splits": Path("data/multi_sleeve_portfolio_backtest_splits.csv"),
    "trades": Path("data/multi_sleeve_portfolio_backtest_trades.csv"),
    "blockers": Path("data/multi_sleeve_portfolio_backtest_blockers.csv"),
    "summary": Path("data/multi_sleeve_portfolio_backtest_summary.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "report_only",
    "backtest_only",
    "multi_sleeve_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "general_execution_approved",
    "qqq100_execution_approved",
    "codex_experimental_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "high_growth_execution_approved",
    "crypto_execution_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "backtest_only": True,
    "multi_sleeve_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "live_position_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "general_execution_approved": False,
    "qqq100_execution_approved": False,
    "codex_experimental_execution_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "high_growth_execution_approved": False,
    "crypto_execution_approved": False,
}

BACKTEST_COLUMNS = [
    "created_at",
    "portfolio_name",
    "portfolio_role",
    "final_backtest_status",
    "baseline_source",
    "qqq100_reference_cagr",
    "qqq100_reference_sharpe",
    "qqq100_reference_max_drawdown",
    "qqq100_reference_calmar",
    "saved_qqq100_benchmark_source",
    "saved_qqq100_benchmark_cagr",
    "saved_qqq100_benchmark_sharpe",
    "saved_qqq100_benchmark_max_drawdown",
    "saved_qqq100_benchmark_calmar",
    "generated_qqq100_reference_status",
    "generated_qqq100_reference_cagr",
    "generated_qqq100_reference_sharpe",
    "generated_qqq100_reference_max_drawdown",
    "generated_qqq100_reference_calmar",
    "qqq100_reference_source_used",
    "qqq100_reference_status",
    "recovered_reference_available",
    "old_generated_reference_retained",
    "old_generated_reference_status",
    "recovered_qqq100_reference_cagr",
    "recovered_qqq100_reference_sharpe",
    "recovered_qqq100_reference_max_drawdown",
    "recovered_qqq100_reference_calmar",
    "saved_benchmark_reconciliation_status",
    "saved_benchmark_delta_cagr_reconciliation",
    "saved_benchmark_delta_sharpe_reconciliation",
    "saved_benchmark_delta_max_drawdown_reconciliation",
    "saved_benchmark_delta_calmar_reconciliation",
    "saved_benchmark_delta_CAGR",
    "saved_benchmark_delta_Sharpe",
    "saved_benchmark_delta_MaxDD",
    "saved_benchmark_delta_Calmar",
    "candidate_allocation",
    "candidate_cagr",
    "candidate_sharpe",
    "candidate_max_drawdown",
    "candidate_calmar",
    "candidate_annualised_volatility",
    "candidate_cash_percentage",
    "candidate_sleeve_exposure_percentages",
    "candidate_turnover_or_trade_count",
    "rough_cost_sensitivity",
    "delta_cagr_vs_qqq100",
    "delta_sharpe_vs_qqq100",
    "delta_max_drawdown_vs_qqq100",
    "delta_calmar_vs_qqq100",
    "delta_cagr_vs_generated_qqq100_reference",
    "delta_sharpe_vs_generated_qqq100_reference",
    "delta_max_drawdown_vs_generated_qqq100_reference",
    "delta_calmar_vs_generated_qqq100_reference",
    "delta_cagr_vs_recovered_qqq100_reference",
    "delta_sharpe_vs_recovered_qqq100_reference",
    "delta_max_drawdown_vs_recovered_qqq100_reference",
    "delta_calmar_vs_recovered_qqq100_reference",
    "split_stability_label",
    "balanced_research_score",
    "data_quality",
    "missing_sleeve_data_warnings",
    "biggest_blocker",
    "recommended_next_step",
    *SAFETY_COLUMNS,
]

SLEEVE_COLUMNS = [
    "created_at",
    "sleeve_name",
    "strategy_name",
    "ticker_or_scope",
    "sleeve_role",
    "return_stream_status",
    "metrics_source",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "cost_sensitivity",
    "split_stability",
    "concentration_risk",
    "overlap_risk",
    "final_sleeve_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

ALLOCATION_COLUMNS = [
    "created_at",
    "portfolio_name",
    "sleeve_name",
    "target_weight_pct",
    "actual_weight_pct",
    "allocation_status",
    "allocation_notes",
    *SAFETY_COLUMNS,
]

RANKING_COLUMNS = [
    "created_at",
    "rank",
    "portfolio_name",
    "balanced_research_score",
    "final_backtest_status",
    "ranking_reason",
    "data_quality",
    *SAFETY_COLUMNS,
]

SPLIT_COLUMNS = [
    "created_at",
    "portfolio_name",
    "split_name",
    "split_status",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "split_stability_label",
    "notes",
    *SAFETY_COLUMNS,
]

TRADE_COLUMNS = [
    "created_at",
    "portfolio_name",
    "sleeve_name",
    "trade_count",
    "turnover_estimate",
    "trade_stream_status",
    "cost_sensitivity",
    "notes",
    *SAFETY_COLUMNS,
]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_COLUMNS,
]


@dataclass
class MultiSleevePortfolioBacktestResult:
    output_paths: dict[str, Path]
    backtest_rows: list[dict[str, Any]]
    sleeve_rows: list[dict[str, Any]]
    allocation_rows: list[dict[str, Any]]
    ranking_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    trade_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_portfolio_backtest(root_dir: Path | str = ".") -> MultiSleevePortfolioBacktestResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    qqq_metrics = qqq100_metric_bundle(inputs)
    return_streams = (
        inputs["sleeve_return_streams"]
        + normalize_high_growth_stream_rows(inputs["high_growth_return_streams"])
        + normalize_recovered_reference_stream_rows(inputs["qqq100_recovered_reference_stream"])
    )
    sleeve_rows = build_sleeve_rows(created_at, inputs, qqq_metrics, return_streams)
    portfolios = build_portfolio_rows(created_at, qqq_metrics, sleeve_rows, return_streams, inputs)
    allocations = build_allocation_rows(created_at, sleeve_rows)
    rankings = build_ranking_rows(created_at, portfolios)
    splits = build_split_rows(created_at, portfolios, qqq_metrics)
    trades = build_trade_rows(created_at, portfolios)
    blockers = build_blocker_rows(created_at)
    summary = build_summary_rows(created_at, portfolios, qqq_metrics, return_streams)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["backtest"], BACKTEST_COLUMNS, portfolios)
    write_rows(output_paths["sleeves"], SLEEVE_COLUMNS, sleeve_rows)
    write_rows(output_paths["allocations"], ALLOCATION_COLUMNS, allocations)
    write_rows(output_paths["rankings"], RANKING_COLUMNS, rankings)
    write_rows(output_paths["splits"], SPLIT_COLUMNS, splits)
    write_rows(output_paths["trades"], TRADE_COLUMNS, trades)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blockers)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary)
    return MultiSleevePortfolioBacktestResult(
        output_paths=output_paths,
        backtest_rows=portfolios,
        sleeve_rows=sleeve_rows,
        allocation_rows=allocations,
        ranking_rows=rankings,
        split_rows=splits,
        trade_rows=trades,
        blocker_rows=blockers,
        summary_rows=summary,
        summary_lines=build_summary_lines(summary, output_paths["backtest"]),
    )


def show_multi_sleeve_portfolio_backtest(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve portfolio backtest is missing.",
            "Run `python bot.py --multi-sleeve-portfolio-backtest` first.",
            "execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
        ]
    summary = {row.get("summary_name", ""): row.get("summary_value", "") for row in read_csv_rows(path)}
    return 0, [
        "Multi-sleeve portfolio backtest. Saved-output-only research checkpoint; no execution wiring approved.",
        f"final_backtest_status: {summary.get('final_backtest_status', 'missing')}",
        f"saved QQQ100 benchmark metrics: CAGR={summary.get('saved_qqq100_benchmark_cagr', MISSING)}, Sharpe={summary.get('saved_qqq100_benchmark_sharpe', MISSING)}, MaxDD={summary.get('saved_qqq100_benchmark_max_drawdown', MISSING)}, Calmar={summary.get('saved_qqq100_benchmark_calmar', MISSING)}",
        f"QQQ100 reference source used: {summary.get('qqq100_reference_source_used', 'missing')}",
        f"old generated QQQ100 diagnostic reference metrics: CAGR={summary.get('generated_qqq100_reference_cagr', MISSING)}, Sharpe={summary.get('generated_qqq100_reference_sharpe', MISSING)}, MaxDD={summary.get('generated_qqq100_reference_max_drawdown', MISSING)}, Calmar={summary.get('generated_qqq100_reference_calmar', MISSING)}",
        f"old generated QQQ100 diagnostic reference status: {summary.get('old_generated_reference_status', 'missing')}",
        f"recovered QQQ100 preferred reference metrics: CAGR={summary.get('recovered_qqq100_reference_cagr', MISSING)}, Sharpe={summary.get('recovered_qqq100_reference_sharpe', MISSING)}, MaxDD={summary.get('recovered_qqq100_reference_max_drawdown', MISSING)}, Calmar={summary.get('recovered_qqq100_reference_calmar', MISSING)}",
        f"saved benchmark reconciliation status: {summary.get('saved_benchmark_reconciliation_status', 'missing')}",
        f"top multi-sleeve portfolio candidate: {summary.get('top_multi_sleeve_portfolio_candidate', 'missing')}",
        f"candidate allocation: {summary.get('candidate_allocation', 'missing')}",
        f"candidate metrics: CAGR={summary.get('candidate_cagr', MISSING)}, Sharpe={summary.get('candidate_sharpe', MISSING)}, MaxDD={summary.get('candidate_max_drawdown', MISSING)}, Calmar={summary.get('candidate_calmar', MISSING)}",
        f"delta_vs_recovered_qqq100_reference: delta_CAGR={summary.get('delta_cagr_vs_recovered_qqq100_reference', MISSING)}, delta_Sharpe={summary.get('delta_sharpe_vs_recovered_qqq100_reference', MISSING)}, delta_MaxDD={summary.get('delta_max_drawdown_vs_recovered_qqq100_reference', MISSING)}, delta_Calmar={summary.get('delta_calmar_vs_recovered_qqq100_reference', MISSING)}",
        f"diagnostic_delta_vs_old_generated_qqq100_reference: delta_CAGR={summary.get('delta_cagr_vs_generated_qqq100_reference', MISSING)}, delta_Sharpe={summary.get('delta_sharpe_vs_generated_qqq100_reference', MISSING)}, delta_MaxDD={summary.get('delta_max_drawdown_vs_generated_qqq100_reference', MISSING)}, delta_Calmar={summary.get('delta_calmar_vs_generated_qqq100_reference', MISSING)}",
        f"split stability summary: {summary.get('split_stability_summary', 'missing')}",
        f"missing sleeve data warnings: {summary.get('missing_sleeve_data_warnings', 'missing')}",
        f"biggest blocker: {summary.get('biggest_blocker', BIGGEST_BLOCKER)}",
        f"recommended next step: {summary.get('recommended_next_step', RECOMMENDED_NEXT_STEP)}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; qqq100_execution_approved=false; codex_experimental_execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def build_sleeve_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, str]]],
    qqq_metrics: dict[str, str],
    return_streams: list[dict[str, str]],
) -> list[dict[str, Any]]:
    defensive_metrics = defensive_metric_bundle(inputs)
    high_growth_metrics = saved_metric_bundle(
        inputs["high_growth_final_validation"] + inputs["high_growth_branch"] + inputs["high_growth_lab"]
    )
    crypto_metrics = saved_metric_bundle(inputs["crypto_lab"] + inputs["crypto_state"] + inputs["crypto_lead"])
    codex_metrics = codex_metric_bundle(inputs)
    stream_candidates = set(stream_returns_by_candidate(return_streams))
    defensive_stream_status = (
        "saved_return_stream_metrics_available"
        if "qqq100_combined_trend_spy_regime_drawdown_gate" in stream_candidates
        else ("missing_saved_return_stream" if metrics_missing(defensive_metrics) else "saved_metric_reference_only")
    )
    codex_stream_status = (
        "saved_return_stream_metrics_available"
        if "codex_qqq_calmar_optimised_defensive_gate_sleeve" in stream_candidates
        else ("missing_saved_return_stream" if metrics_missing(codex_metrics) else "saved_metric_reference_only")
    )
    high_growth_stream_status = (
        "saved_return_stream_metrics_available"
        if "codex_broad_growth_balanced_breakout_control" in stream_candidates
        else "missing_saved_return_stream"
    )
    return [
        sleeve_row(
            created_at,
            QQQ100_SLEEVE,
            QQQ100_STRATEGY,
            "QQQ",
            "baseline active paper sleeve",
            "saved_metric_reference_only",
            qqq_metrics["baseline_source"],
            qqq_metrics,
            "not_material_in_saved_signal",
            "missing_split_metrics",
            "single_etf_concentration",
            "self_overlap",
            "active_paper_sleeve_reference_only",
            "Keep as the only active paper sleeve; no repeat execution approval.",
        ),
        sleeve_row(
            created_at,
            "qqq_defensive_crash_gate_research_sleeve",
            "QQQ trend plus defensive crash gate",
            "QQQ/SPY/cash",
            "research crash-gate sleeve",
            defensive_stream_status,
            defensive_metrics["baseline_source"],
            defensive_metrics,
            "needs_cost_turnover_stress",
            "missing_split_metrics",
            "single_etf_with_regime_gate",
            "high_overlap_with_qqq_by_design",
            "research_only_needs_daily_return_stream",
            "Use generated return-stream metrics for portfolio comparison; keep candidate research-only.",
        ),
        sleeve_row(
            created_at,
            "high_growth_stock_research_sleeve",
            "codex_broad_growth_balanced_breakout_control",
            "high-growth stocks",
            "high-risk research sleeve",
            high_growth_stream_status,
            "summary_metrics_only_or_unavailable",
            high_growth_metrics,
            "cost_review_required",
            "split_review_required",
            "high_concentration_and_outlier_risk",
            "high_growth_overlap_with_qqq",
            "research_only_missing_return_stream",
            "Use saved high-growth daily returns for research metrics only; do not approve preview or execution.",
        ),
        sleeve_row(
            created_at,
            "crypto_research_sleeve",
            "crypto_off_hours_research_route",
            "crypto research universe",
            "off-hours research sleeve",
            "missing_saved_return_stream",
            "summary_metrics_only_or_unavailable",
            crypto_metrics,
            "crypto_cost_review_required",
            "crypto_split_review_required",
            "very_high_volatility",
            "low_direct_qqq_overlap_but_high_portfolio_volatility",
            "research_only_missing_return_stream",
            "Do not include in portfolio metrics until reliable saved daily returns exist.",
        ),
        sleeve_row(
            created_at,
            "defensive_cash_or_bond_sleeve",
            "cash_default_defensive_sleeve",
            "cash; defensive ETF unavailable",
            "cash/risk-off sleeve",
            "cash_available_bond_etf_data_unavailable",
            "cash_default_no_bond_metrics",
            {
                "cagr": "0",
                "sharpe": MISSING,
                "max_drawdown": "0",
                "calmar": MISSING,
                "annualised_volatility": "0",
                "cash_percentage": "100",
                "turnover_or_trade_count": "0",
                "baseline_source": "cash_default_bond_or_defensive_etf_data_unavailable",
            },
            "low_cash_cost",
            "cash_not_split_sensitive",
            "cash_drag_risk",
            "low_overlap",
            "cash_proxy_only_bond_etf_data_unavailable",
            "Use only as an explicit cash placeholder until defensive ETF data exists.",
        ),
        sleeve_row(
            created_at,
            "codex_experimental_research_sleeve",
            "codex_qqq_calmar_optimised_defensive_gate_sleeve",
            "QQQ/SPY/cash; optional future sleeves blocked",
            "Codex ambitious research sleeve",
            codex_stream_status,
            codex_metrics["baseline_source"],
            codex_metrics,
            "needs_cost_stress_review",
            "needs_split_validation",
            "moderate_overlap_and_parameter_risk",
            "high_overlap_with_qqq_by_design",
            "research_only_needs_market_metrics",
            "Use generated return-stream metrics for portfolio comparison; keep candidate research-only.",
        ),
    ]


def build_portfolio_rows(
    created_at: str,
    qqq_metrics: dict[str, str],
    sleeve_rows: list[dict[str, Any]],
    return_streams: list[dict[str, str]],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    generated_qqq_metrics = portfolio_metrics_from_streams(QQQ100_REFERENCE, return_streams, QQQ100_STRATEGY) or missing_portfolio_metrics()
    generated_status = "generated_qqq100_reference_available" if not metrics_missing(generated_qqq_metrics) else "missing_generated_qqq100_reference"
    recovered_reference = recovered_reference_info(inputs, return_streams)
    reference_candidate = RECOVERED_QQQ100_REFERENCE if recovered_reference["available"] else QQQ100_STRATEGY
    reference_metrics = recovered_reference["metrics"] if recovered_reference["available"] else generated_qqq_metrics
    reference_source = RECOVERED_QQQ100_REFERENCE if recovered_reference["available"] else "old_generated_qqq100_reference"
    reference_status = recovered_reference["status"] if recovered_reference["available"] else generated_status
    reconciliation_status = (
        "recovered_qqq100_reference_aligned_with_saved_benchmark"
        if recovered_reference["available"]
        else saved_benchmark_reconciliation_status(qqq_metrics, generated_qqq_metrics)
    )
    missing_warnings = missing_stream_warnings_from_streams(return_streams)
    portfolio_specs = [
        (QQQ100_REFERENCE, "reference", "100% qqq100_core_trend_sleeve", 82, "reference_only", reference_metrics),
        (TOP_MULTI_SLEEVE_CANDIDATE, "cash defensive reference", "95% qqq100_core_trend_sleeve; 5% defensive_cash_or_bond_sleeve", 63, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("qqq100_plus_spy_sma200_defensive_gate", "SPY SMA200 defensive gate research", "70% qqq100_core_trend_sleeve; 25% qqq100_spy_sma200_regime_filter; 5% defensive_cash_or_bond_sleeve", 58, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("qqq100_plus_rolling_drawdown_defensive_gate", "rolling drawdown defensive gate research", "70% qqq100_core_trend_sleeve; 25% qqq100_rolling_drawdown_15_filter; 5% defensive_cash_or_bond_sleeve", 58, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("qqq100_plus_combined_defensive_gate", "combined defensive gate research", "70% qqq100_core_trend_sleeve; 25% qqq100_combined_trend_spy_regime_drawdown_gate; 5% defensive_cash_or_bond_sleeve", 58, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("codex_defensive_qqq_research_portfolio", "Codex defensive QQQ reduced portfolio", "65% qqq100_core_trend_sleeve; 30% codex_experimental_research_sleeve; 5% defensive_cash_or_bond_sleeve", 57, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("qqq100_plus_high_growth_research", "high-growth research blend", "80% qqq100_core_trend_sleeve; 15% high_growth_stock_research_sleeve; 5% defensive_cash_or_bond_sleeve", 42, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("qqq100_plus_crypto_research", "crypto research blend", "85% qqq100_core_trend_sleeve; 10% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve", 40, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("balanced_multi_sleeve_research_portfolio", "balanced reduced research portfolio", "50% qqq100_core_trend_sleeve; 20% qqq_defensive_crash_gate_research_sleeve; 15% high_growth_stock_research_sleeve; 10% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve", 45, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("codex_ambitious_multi_sleeve_candidate", "Codex ambitious transparent allocation", "60% qqq100_core_trend_sleeve; 25% codex_experimental_research_sleeve; 10% defensive_cash_or_bond_sleeve; 5% research optionality reserve", 52, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
    ]
    rows = []
    for name, role, allocation, score, status, metrics in portfolio_specs:
        stream_metrics = portfolio_metrics_from_streams(name, return_streams, reference_candidate)
        if stream_metrics:
            metrics = stream_metrics
            status = "multi_sleeve_portfolio_backtest_created"
        final_status = status
        if stream_metrics and name != QQQ100_REFERENCE:
            final_status = candidate_backtest_status(metrics, reference_metrics, recovered_reference["available"])
        delta_cagr_generated = metric_delta(metrics["cagr"], generated_qqq_metrics["cagr"]) if stream_metrics else ("0" if name == QQQ100_REFERENCE and not metrics_missing(generated_qqq_metrics) else MISSING)
        delta_sharpe_generated = metric_delta(metrics["sharpe"], generated_qqq_metrics["sharpe"]) if stream_metrics else ("0" if name == QQQ100_REFERENCE and not metrics_missing(generated_qqq_metrics) else MISSING)
        delta_maxdd_generated = metric_delta(metrics["max_drawdown"], generated_qqq_metrics["max_drawdown"]) if stream_metrics else ("0" if name == QQQ100_REFERENCE and not metrics_missing(generated_qqq_metrics) else MISSING)
        delta_calmar_generated = metric_delta(metrics["calmar"], generated_qqq_metrics["calmar"]) if stream_metrics else ("0" if name == QQQ100_REFERENCE and not metrics_missing(generated_qqq_metrics) else MISSING)
        delta_cagr_reference = metric_delta(metrics["cagr"], reference_metrics["cagr"]) if stream_metrics else ("0" if name == QQQ100_REFERENCE and not metrics_missing(reference_metrics) else MISSING)
        delta_sharpe_reference = metric_delta(metrics["sharpe"], reference_metrics["sharpe"]) if stream_metrics else ("0" if name == QQQ100_REFERENCE and not metrics_missing(reference_metrics) else MISSING)
        delta_maxdd_reference = metric_delta(metrics["max_drawdown"], reference_metrics["max_drawdown"]) if stream_metrics else ("0" if name == QQQ100_REFERENCE and not metrics_missing(reference_metrics) else MISSING)
        delta_calmar_reference = metric_delta(metrics["calmar"], reference_metrics["calmar"]) if stream_metrics else ("0" if name == QQQ100_REFERENCE and not metrics_missing(reference_metrics) else MISSING)
        delta_cagr_recovered = delta_cagr_reference if recovered_reference["available"] else MISSING
        delta_sharpe_recovered = delta_sharpe_reference if recovered_reference["available"] else MISSING
        delta_maxdd_recovered = delta_maxdd_reference if recovered_reference["available"] else MISSING
        delta_calmar_recovered = delta_calmar_reference if recovered_reference["available"] else MISSING
        recommended_next_step = (
            "review_recovered_reference_multi_sleeve_candidate_and_add_crypto_streams_before_label_change"
            if recovered_reference["available"]
            else RECOMMENDED_NEXT_STEP
        )
        rows.append(
            {
                "created_at": created_at,
                "portfolio_name": name,
                "portfolio_role": role,
                "final_backtest_status": "multi_sleeve_portfolio_backtest_created" if name == QQQ100_REFERENCE else final_status,
                "baseline_source": qqq_metrics["baseline_source"],
                "qqq100_reference_cagr": qqq_metrics["cagr"],
                "qqq100_reference_sharpe": qqq_metrics["sharpe"],
                "qqq100_reference_max_drawdown": qqq_metrics["max_drawdown"],
                "qqq100_reference_calmar": qqq_metrics["calmar"],
                "saved_qqq100_benchmark_source": qqq_metrics["baseline_source"],
                "saved_qqq100_benchmark_cagr": qqq_metrics["cagr"],
                "saved_qqq100_benchmark_sharpe": qqq_metrics["sharpe"],
                "saved_qqq100_benchmark_max_drawdown": qqq_metrics["max_drawdown"],
                "saved_qqq100_benchmark_calmar": qqq_metrics["calmar"],
                "generated_qqq100_reference_status": generated_status,
                "generated_qqq100_reference_cagr": generated_qqq_metrics["cagr"],
                "generated_qqq100_reference_sharpe": generated_qqq_metrics["sharpe"],
                "generated_qqq100_reference_max_drawdown": generated_qqq_metrics["max_drawdown"],
                "generated_qqq100_reference_calmar": generated_qqq_metrics["calmar"],
                "qqq100_reference_source_used": reference_source,
                "qqq100_reference_status": reference_status,
                "recovered_reference_available": recovered_reference["available"],
                "old_generated_reference_retained": True,
                "old_generated_reference_status": "diagnostic_only",
                "recovered_qqq100_reference_cagr": recovered_reference["metrics"]["cagr"],
                "recovered_qqq100_reference_sharpe": recovered_reference["metrics"]["sharpe"],
                "recovered_qqq100_reference_max_drawdown": recovered_reference["metrics"]["max_drawdown"],
                "recovered_qqq100_reference_calmar": recovered_reference["metrics"]["calmar"],
                "saved_benchmark_reconciliation_status": reconciliation_status,
                "saved_benchmark_delta_cagr_reconciliation": metric_delta(generated_qqq_metrics["cagr"], qqq_metrics["cagr"]),
                "saved_benchmark_delta_sharpe_reconciliation": metric_delta(generated_qqq_metrics["sharpe"], qqq_metrics["sharpe"]),
                "saved_benchmark_delta_max_drawdown_reconciliation": metric_delta(generated_qqq_metrics["max_drawdown"], qqq_metrics["max_drawdown"]),
                "saved_benchmark_delta_calmar_reconciliation": metric_delta(generated_qqq_metrics["calmar"], qqq_metrics["calmar"]),
                "saved_benchmark_delta_CAGR": metric_delta(reference_metrics["cagr"], qqq_metrics["cagr"]),
                "saved_benchmark_delta_Sharpe": metric_delta(reference_metrics["sharpe"], qqq_metrics["sharpe"]),
                "saved_benchmark_delta_MaxDD": metric_delta(reference_metrics["max_drawdown"], qqq_metrics["max_drawdown"]),
                "saved_benchmark_delta_Calmar": metric_delta(reference_metrics["calmar"], qqq_metrics["calmar"]),
                "candidate_allocation": allocation,
                "candidate_cagr": metrics["cagr"],
                "candidate_sharpe": metrics["sharpe"],
                "candidate_max_drawdown": metrics["max_drawdown"],
                "candidate_calmar": metrics["calmar"],
                "candidate_annualised_volatility": metrics["annualised_volatility"],
                "candidate_cash_percentage": metrics["cash_percentage"] if stream_metrics else ("0" if name == QQQ100_REFERENCE else ("5" if "5%" in allocation else MISSING)),
                "candidate_sleeve_exposure_percentages": allocation,
                "candidate_turnover_or_trade_count": metrics["turnover_or_trade_count"],
                "rough_cost_sensitivity": "saved_stream_turnover_proxy_available" if stream_metrics else ("reference_not_recomputed" if name == QQQ100_REFERENCE else "missing_cost_turnover_stream"),
                "delta_cagr_vs_qqq100": delta_cagr_reference,
                "delta_sharpe_vs_qqq100": delta_sharpe_reference,
                "delta_max_drawdown_vs_qqq100": delta_maxdd_reference,
                "delta_calmar_vs_qqq100": delta_calmar_reference,
                "delta_cagr_vs_generated_qqq100_reference": delta_cagr_generated,
                "delta_sharpe_vs_generated_qqq100_reference": delta_sharpe_generated,
                "delta_max_drawdown_vs_generated_qqq100_reference": delta_maxdd_generated,
                "delta_calmar_vs_generated_qqq100_reference": delta_calmar_generated,
                "delta_cagr_vs_recovered_qqq100_reference": delta_cagr_recovered,
                "delta_sharpe_vs_recovered_qqq100_reference": delta_sharpe_recovered,
                "delta_max_drawdown_vs_recovered_qqq100_reference": delta_maxdd_recovered,
                "delta_calmar_vs_recovered_qqq100_reference": delta_calmar_recovered,
                "split_stability_label": "missing_split_metrics",
                "balanced_research_score": str(score),
                "data_quality": "saved_return_stream_metrics_available" if stream_metrics else ("saved_qqq100_metrics_only" if name == QQQ100_REFERENCE else "missing_return_stream_for_combined_metrics"),
                "missing_sleeve_data_warnings": missing_warnings if missing_warnings != "none" else "none_for_feasible_stream_portfolio",
                "biggest_blocker": "missing_high_growth_crypto_streams_for_full_multi_sleeve" if stream_metrics else BIGGEST_BLOCKER,
                "recommended_next_step": recommended_next_step,
                **safety_flags(),
            }
        )
    return rows


def build_allocation_rows(created_at: str, sleeve_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = {
        QQQ100_REFERENCE: [(QQQ100_SLEEVE, "100")],
        TOP_MULTI_SLEEVE_CANDIDATE: [(QQQ100_SLEEVE, "95"), ("defensive_cash_or_bond_sleeve", "5")],
        "qqq100_plus_spy_sma200_defensive_gate": [(QQQ100_SLEEVE, "70"), ("qqq_defensive_crash_gate_research_sleeve", "25"), ("defensive_cash_or_bond_sleeve", "5")],
        "qqq100_plus_rolling_drawdown_defensive_gate": [(QQQ100_SLEEVE, "70"), ("qqq_defensive_crash_gate_research_sleeve", "25"), ("defensive_cash_or_bond_sleeve", "5")],
        "qqq100_plus_combined_defensive_gate": [(QQQ100_SLEEVE, "70"), ("qqq_defensive_crash_gate_research_sleeve", "25"), ("defensive_cash_or_bond_sleeve", "5")],
        "codex_defensive_qqq_research_portfolio": [(QQQ100_SLEEVE, "65"), ("codex_experimental_research_sleeve", "30"), ("defensive_cash_or_bond_sleeve", "5")],
        "qqq100_plus_high_growth_research": [(QQQ100_SLEEVE, "80"), ("high_growth_stock_research_sleeve", "15"), ("defensive_cash_or_bond_sleeve", "5")],
        "qqq100_plus_crypto_research": [(QQQ100_SLEEVE, "85"), ("crypto_research_sleeve", "10"), ("defensive_cash_or_bond_sleeve", "5")],
        "balanced_multi_sleeve_research_portfolio": [(QQQ100_SLEEVE, "50"), ("qqq_defensive_crash_gate_research_sleeve", "20"), ("high_growth_stock_research_sleeve", "15"), ("crypto_research_sleeve", "10"), ("defensive_cash_or_bond_sleeve", "5")],
        "codex_ambitious_multi_sleeve_candidate": [(QQQ100_SLEEVE, "60"), ("codex_experimental_research_sleeve", "25"), ("defensive_cash_or_bond_sleeve", "10"), ("research_optionality_reserve", "5")],
    }
    status_by_sleeve = {row["sleeve_name"]: row["return_stream_status"] for row in sleeve_rows}
    rows = []
    for portfolio_name, allocations in specs.items():
        for sleeve_name, weight in allocations:
            stream_status = status_by_sleeve.get(sleeve_name, "design_placeholder")
            rows.append(
                {
                    "created_at": created_at,
                    "portfolio_name": portfolio_name,
                    "sleeve_name": sleeve_name,
                    "target_weight_pct": weight,
                    "actual_weight_pct": weight if stream_status in {"saved_metric_reference_only", "cash_available_bond_etf_data_unavailable", "saved_return_stream_metrics_available"} else "not_modelled",
                    "allocation_status": "modelled_reference_only" if portfolio_name == QQQ100_REFERENCE else ("allocation_defined_metrics_blocked" if "missing" in stream_status or sleeve_name == "research_optionality_reserve" else "allocation_defined"),
                    "allocation_notes": "Weights are research design weights only and do not create order instructions.",
                    **safety_flags(),
                }
            )
    return rows


def build_ranking_rows(created_at: str, portfolios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(portfolios, key=lambda row: int(row["balanced_research_score"]), reverse=True)
    return [
        {
            "created_at": created_at,
            "rank": rank,
            "portfolio_name": row["portfolio_name"],
            "balanced_research_score": row["balanced_research_score"],
            "final_backtest_status": row["final_backtest_status"],
            "ranking_reason": "balanced research score with missing-return-stream, simplicity, and execution-boundary penalties",
            "data_quality": row["data_quality"],
            **safety_flags(),
        }
        for rank, row in enumerate(ranked, start=1)
    ]


def build_split_rows(
    created_at: str,
    portfolios: list[dict[str, Any]],
    qqq_metrics: dict[str, str],
) -> list[dict[str, Any]]:
    rows = []
    for portfolio in portfolios:
        for split_name in ["full_period", "split_60_40", "split_70_30", "split_80_20"]:
            is_reference_full = portfolio["portfolio_name"] == QQQ100_REFERENCE and split_name == "full_period"
            rows.append(
                {
                    "created_at": created_at,
                    "portfolio_name": portfolio["portfolio_name"],
                    "split_name": split_name,
                    "split_status": "saved_reference_metrics_available" if is_reference_full else "missing_split_metrics",
                    "cagr": qqq_metrics["cagr"] if is_reference_full else MISSING,
                    "sharpe": qqq_metrics["sharpe"] if is_reference_full else MISSING,
                    "max_drawdown": qqq_metrics["max_drawdown"] if is_reference_full else MISSING,
                    "calmar": qqq_metrics["calmar"] if is_reference_full else MISSING,
                    "split_stability_label": "missing_split_metrics",
                    "notes": "Fixed chronological split metrics require saved daily return streams.",
                    **safety_flags(),
                }
            )
    return rows


def build_trade_rows(created_at: str, portfolios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for portfolio in portfolios:
        sleeves = [part.strip().split(" ", 1)[1] for part in portfolio["candidate_allocation"].split(";") if " " in part]
        for sleeve_name in sleeves:
            rows.append(
                {
                    "created_at": created_at,
                    "portfolio_name": portfolio["portfolio_name"],
                    "sleeve_name": sleeve_name,
                    "trade_count": MISSING,
                    "turnover_estimate": MISSING,
                    "trade_stream_status": "missing_saved_trade_stream",
                    "cost_sensitivity": "missing_cost_turnover_stream",
                    "notes": "No trade stream is used or invented by this saved-output checkpoint.",
                    **safety_flags(),
                }
            )
    return rows


def build_blocker_rows(created_at: str) -> list[dict[str, Any]]:
    blockers = [
        ("missing_saved_return_streams_for_non_qqq_sleeves", "blocked", "critical", "High-growth, crypto, defensive crash-gate, and Codex experimental sleeves do not have reliable saved daily return streams for combined portfolio metrics.", RECOMMENDED_NEXT_STEP),
        ("exact_qqq100_baseline_required", "passed", "high", "QQQ100 baseline must be qqq_100_trend_gate / qqq100_core_trend_sleeve, never codex_ambitious_concentrated_growth_persistence.", "Keep exact baseline selection in all downstream reports."),
        ("split_metrics_required", "blocked", "high", "60/40, 70/30, and 80/20 split metrics require daily returns.", "Add saved split validation only after return streams exist."),
        ("cost_turnover_stream_required", "blocked", "high", "Portfolio cost sensitivity cannot be estimated without trade/turnover streams.", "Add saved trade streams before cost-sensitive ranking."),
        ("high_growth_and_crypto_blocked", "blocked", "high", "High-growth and crypto sleeves remain research-only and must not be included in execution or preview promotion.", "Keep them as blocked research sleeves."),
        ("codex_experimental_execution_blocked", "blocked", "critical", "Codex experimental sleeve is research-only and cannot approve execution.", "Do not wire to preview/action/execution."),
        ("qqq100_repeat_execution_not_approved", "blocked", "critical", "QQQ100 repeat execution remains unapproved.", "Keep QQQ100 paper path unchanged."),
        ("scheduling_not_approved", "blocked", "critical", "No scheduling, Hermes cron, loop, service, or Task Scheduler use is approved.", "Keep this report manual/research-only."),
    ]
    return [blocker_row(created_at, *blocker) for blocker in blockers]


def build_summary_rows(
    created_at: str,
    portfolios: list[dict[str, Any]],
    qqq_metrics: dict[str, str],
    return_streams: list[dict[str, str]],
) -> list[dict[str, Any]]:
    candidate = top_generated_candidate(portfolios)
    generated_qqq = next(row for row in portfolios if row["portfolio_name"] == QQQ100_REFERENCE)
    final_status = candidate["final_backtest_status"] if candidate else FINAL_BACKTEST_STATUS
    candidate = candidate or next(row for row in portfolios if row["portfolio_name"] == TOP_MULTI_SLEEVE_CANDIDATE)
    missing_warnings = missing_stream_warnings_from_streams(return_streams)
    summary_items = [
        ("final_backtest_status", final_status, "Candidates are compared against the preferred QQQ100 research reference, not the saved benchmark."),
        ("baseline_source", qqq_metrics["baseline_source"], "Exact QQQ100 saved metrics source."),
        ("qqq100_reference_cagr", qqq_metrics["cagr"], "QQQ100 clean lead CAGR."),
        ("qqq100_reference_sharpe", qqq_metrics["sharpe"], "QQQ100 clean lead Sharpe."),
        ("qqq100_reference_max_drawdown", qqq_metrics["max_drawdown"], "QQQ100 clean lead max drawdown."),
        ("qqq100_reference_calmar", qqq_metrics["calmar"], "QQQ100 clean lead Calmar."),
        ("saved_qqq100_benchmark_source", qqq_metrics["baseline_source"], "Saved benchmark metrics remain reconciliation-only when generated streams are present."),
        ("saved_qqq100_benchmark_cagr", qqq_metrics["cagr"], "Saved QQQ100 benchmark CAGR."),
        ("saved_qqq100_benchmark_sharpe", qqq_metrics["sharpe"], "Saved QQQ100 benchmark Sharpe."),
        ("saved_qqq100_benchmark_max_drawdown", qqq_metrics["max_drawdown"], "Saved QQQ100 benchmark max drawdown."),
        ("saved_qqq100_benchmark_calmar", qqq_metrics["calmar"], "Saved QQQ100 benchmark Calmar."),
        ("generated_qqq100_reference_status", generated_qqq["generated_qqq100_reference_status"], "Generated QQQ100 stream reference availability."),
        ("generated_qqq100_reference_cagr", generated_qqq["generated_qqq100_reference_cagr"], "Generated QQQ100 stream CAGR."),
        ("generated_qqq100_reference_sharpe", generated_qqq["generated_qqq100_reference_sharpe"], "Generated QQQ100 stream Sharpe."),
        ("generated_qqq100_reference_max_drawdown", generated_qqq["generated_qqq100_reference_max_drawdown"], "Generated QQQ100 stream max drawdown."),
        ("generated_qqq100_reference_calmar", generated_qqq["generated_qqq100_reference_calmar"], "Generated QQQ100 stream Calmar."),
        ("qqq100_reference_source_used", generated_qqq["qqq100_reference_source_used"], "Primary QQQ100 reference used for portfolio deltas."),
        ("qqq100_reference_status", generated_qqq["qqq100_reference_status"], "Primary QQQ100 reference status."),
        ("recovered_reference_available", str(generated_qqq["recovered_reference_available"]).lower(), "Recovered reference is used only after threshold-pass validation."),
        ("old_generated_reference_retained", str(generated_qqq["old_generated_reference_retained"]).lower(), "Old generated QQQ100 stream remains available as diagnostic context."),
        ("old_generated_reference_status", generated_qqq["old_generated_reference_status"], "Old generated QQQ100 stream is diagnostic-only when the recovered reference is valid."),
        ("recovered_qqq100_reference_cagr", generated_qqq["recovered_qqq100_reference_cagr"], "Recovered QQQ100 reference CAGR when available."),
        ("recovered_qqq100_reference_sharpe", generated_qqq["recovered_qqq100_reference_sharpe"], "Recovered QQQ100 reference Sharpe when available."),
        ("recovered_qqq100_reference_max_drawdown", generated_qqq["recovered_qqq100_reference_max_drawdown"], "Recovered QQQ100 reference max drawdown when available."),
        ("recovered_qqq100_reference_calmar", generated_qqq["recovered_qqq100_reference_calmar"], "Recovered QQQ100 reference Calmar when available."),
        ("saved_benchmark_reconciliation_status", generated_qqq["saved_benchmark_reconciliation_status"], "Saved benchmark and generated stream metrics are intentionally separated."),
        ("top_multi_sleeve_portfolio_candidate", candidate["portfolio_name"], "Top generated-stream candidate by Calmar/Sharpe/CAGR among feasible non-reference portfolios."),
        ("candidate_allocation", candidate["candidate_allocation"], "Allocation is a research design only; it is not an order plan."),
        ("candidate_cagr", candidate["candidate_cagr"], "Candidate metric from saved/generated return stream where available."),
        ("candidate_sharpe", candidate["candidate_sharpe"], "Candidate metric from saved/generated return stream where available."),
        ("candidate_max_drawdown", candidate["candidate_max_drawdown"], "Candidate metric from saved/generated return stream where available."),
        ("candidate_calmar", candidate["candidate_calmar"], "Candidate metric from saved/generated return stream where available."),
        ("delta_cagr_vs_qqq100", candidate["delta_cagr_vs_qqq100"], "Saved-benchmark reconciliation delta only."),
        ("delta_sharpe_vs_qqq100", candidate["delta_sharpe_vs_qqq100"], "Saved-benchmark reconciliation delta only."),
        ("delta_max_drawdown_vs_qqq100", candidate["delta_max_drawdown_vs_qqq100"], "Saved-benchmark reconciliation delta only."),
        ("delta_calmar_vs_qqq100", candidate["delta_calmar_vs_qqq100"], "Saved-benchmark reconciliation delta only."),
        ("delta_cagr_vs_generated_qqq100_reference", candidate["delta_cagr_vs_generated_qqq100_reference"], "Diagnostic comparison against the old generated stream."),
        ("delta_sharpe_vs_generated_qqq100_reference", candidate["delta_sharpe_vs_generated_qqq100_reference"], "Diagnostic comparison against the old generated stream."),
        ("delta_max_drawdown_vs_generated_qqq100_reference", candidate["delta_max_drawdown_vs_generated_qqq100_reference"], "Diagnostic comparison against the old generated stream."),
        ("delta_calmar_vs_generated_qqq100_reference", candidate["delta_calmar_vs_generated_qqq100_reference"], "Diagnostic comparison against the old generated stream."),
        ("delta_cagr_vs_recovered_qqq100_reference", candidate["delta_cagr_vs_recovered_qqq100_reference"], "Primary comparison when recovered reference is valid."),
        ("delta_sharpe_vs_recovered_qqq100_reference", candidate["delta_sharpe_vs_recovered_qqq100_reference"], "Primary comparison when recovered reference is valid."),
        ("delta_max_drawdown_vs_recovered_qqq100_reference", candidate["delta_max_drawdown_vs_recovered_qqq100_reference"], "Primary comparison when recovered reference is valid."),
        ("delta_calmar_vs_recovered_qqq100_reference", candidate["delta_calmar_vs_recovered_qqq100_reference"], "Primary comparison when recovered reference is valid."),
        ("split_stability_summary", "missing_split_metrics", "Fixed chronological split metrics are unavailable."),
        ("missing_sleeve_data_warnings", missing_warnings, "Missing streams are labelled rather than invented."),
        ("biggest_blocker", "missing_high_growth_crypto_streams_for_full_multi_sleeve", "High-growth and crypto streams remain unavailable for full portfolio testing."),
        ("recommended_next_step", candidate["recommended_next_step"], "Next review step; keep status research-only."),
    ]
    return [
        {
            "created_at": created_at,
            "summary_name": name,
            "summary_value": value,
            "details": details,
            **safety_flags(),
        }
        for name, value, details in summary_items
    ]


def sleeve_row(
    created_at: str,
    sleeve_name: str,
    strategy_name: str,
    ticker_or_scope: str,
    sleeve_role: str,
    return_stream_status: str,
    metrics_source: str,
    metrics: dict[str, str],
    cost_sensitivity: str,
    split_stability: str,
    concentration_risk: str,
    overlap_risk: str,
    final_status: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "sleeve_name": sleeve_name,
        "strategy_name": strategy_name,
        "ticker_or_scope": ticker_or_scope,
        "sleeve_role": sleeve_role,
        "return_stream_status": return_stream_status,
        "metrics_source": metrics_source,
        "cagr": metrics["cagr"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
        "calmar": metrics["calmar"],
        "cost_sensitivity": cost_sensitivity,
        "split_stability": split_stability,
        "concentration_risk": concentration_risk,
        "overlap_risk": overlap_risk,
        "final_sleeve_status": final_status,
        "required_next_step": next_step,
        **safety_flags(),
    }


def blocker_row(created_at: str, name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **safety_flags(),
    }


def portfolio_metrics_from_streams(
    portfolio_name: str,
    rows: list[dict[str, str]],
    qqq_reference_candidate: str = QQQ100_STRATEGY,
) -> dict[str, str] | None:
    specs: dict[str, dict[str, float]] = {
        QQQ100_REFERENCE: {qqq_reference_candidate: 1.0},
        TOP_MULTI_SLEEVE_CANDIDATE: {qqq_reference_candidate: 0.95, "cash_default_defensive_sleeve": 0.05},
        "qqq100_plus_spy_sma200_defensive_gate": {
            qqq_reference_candidate: 0.70,
            "qqq100_spy_sma200_regime_filter": 0.25,
            "cash_default_defensive_sleeve": 0.05,
        },
        "qqq100_plus_rolling_drawdown_defensive_gate": {
            qqq_reference_candidate: 0.70,
            "qqq100_rolling_drawdown_15_filter": 0.25,
            "cash_default_defensive_sleeve": 0.05,
        },
        "qqq100_plus_combined_defensive_gate": {
            qqq_reference_candidate: 0.70,
            "qqq100_combined_trend_spy_regime_drawdown_gate": 0.25,
            "cash_default_defensive_sleeve": 0.05,
        },
        "codex_defensive_qqq_research_portfolio": {
            qqq_reference_candidate: 0.65,
            "codex_qqq_calmar_optimised_defensive_gate_sleeve": 0.30,
            "cash_default_defensive_sleeve": 0.05,
        },
        "qqq100_plus_high_growth_research": {
            qqq_reference_candidate: 0.80,
            "codex_broad_growth_balanced_breakout_control": 0.15,
            "cash_default_defensive_sleeve": 0.05,
        },
    }
    weights = specs.get(portfolio_name)
    if not weights:
        return None
    by_candidate = stream_returns_by_candidate(rows)
    if any(candidate not in by_candidate for candidate in weights):
        return None
    common_dates = sorted(set.intersection(*(set(by_candidate[candidate]) for candidate in weights)))
    if len(common_dates) < 2:
        return None
    returns = [
        sum(by_candidate[candidate][date] * weight for candidate, weight in weights.items())
        for date in common_dates
    ]
    metrics = metrics_for_returns(returns)
    metrics["turnover_or_trade_count"] = str(stream_signal_change_count(rows, set(weights)))
    return metrics


def top_generated_candidate(portfolios: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        row
        for row in portfolios
        if row["portfolio_name"] != QQQ100_REFERENCE and row.get("data_quality") == "saved_return_stream_metrics_available"
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: metric_rank_key(row), reverse=True)[0]


def metric_rank_key(row: dict[str, Any]) -> tuple[float, float, float]:
    return (
        parse_float(row.get("candidate_calmar", MISSING)),
        parse_float(row.get("candidate_sharpe", MISSING)),
        parse_float(row.get("candidate_cagr", MISSING)),
    )


def candidate_backtest_status(metrics: dict[str, str], qqq_reference_metrics: dict[str, str], recovered_reference_available: bool = False) -> str:
    delta_calmar = parse_float(metric_delta(metrics["calmar"], qqq_reference_metrics["calmar"]))
    delta_maxdd = parse_float(metric_delta(metrics["max_drawdown"], qqq_reference_metrics["max_drawdown"]))
    delta_sharpe = parse_float(metric_delta(metrics["sharpe"], qqq_reference_metrics["sharpe"]))
    delta_cagr = parse_float(metric_delta(metrics["cagr"], qqq_reference_metrics["cagr"]))
    if delta_calmar > 0 and delta_maxdd >= 0 and (delta_sharpe >= 0 or delta_cagr >= 0):
        if recovered_reference_available:
            return FINAL_STATUS_PROMISING_RECOVERED_REFERENCE
        return FINAL_STATUS_PROMISING_NEEDS_RECONCILIATION
    if recovered_reference_available and (delta_calmar > 0 or delta_sharpe > 0 or delta_cagr > 0):
        return FINAL_STATUS_PROMISING_NEEDS_CRYPTO_POLICY_REVIEW
    return FINAL_STATUS_NOT_BETTER_THAN_GENERATED_QQQ100


def saved_benchmark_reconciliation_status(saved_metrics: dict[str, str], generated_metrics: dict[str, str]) -> str:
    if metrics_missing(saved_metrics):
        return "missing_saved_qqq100_benchmark_metrics"
    if metrics_missing(generated_metrics):
        return "missing_generated_qqq100_reference_metrics"
    deltas = [
        abs(parse_float(metric_delta(generated_metrics["cagr"], saved_metrics["cagr"]))),
        abs(parse_float(metric_delta(generated_metrics["sharpe"], saved_metrics["sharpe"]))),
        abs(parse_float(metric_delta(generated_metrics["max_drawdown"], saved_metrics["max_drawdown"]))),
        abs(parse_float(metric_delta(generated_metrics["calmar"], saved_metrics["calmar"]))),
    ]
    if any(value > threshold for value, threshold in zip(deltas, [0.5, 0.05, 0.5, 0.05])):
        return "generated_qqq100_reference_needs_reconciliation_with_saved_benchmark"
    return "generated_qqq100_reference_aligned_with_saved_benchmark"


def missing_stream_warnings_from_streams(rows: list[dict[str, str]]) -> str:
    present = set(stream_returns_by_candidate(rows))
    missing = []
    if "high_growth_stock_research_sleeve" not in present and "codex_broad_growth_balanced_breakout_control" not in present:
        missing.append("high_growth")
    if "crypto_research_sleeve" not in present and "crypto_off_hours_research_route" not in present:
        missing.append("crypto")
    if "qqq100_combined_trend_spy_regime_drawdown_gate" not in present:
        missing.append("defensive_crash_gate")
    if "codex_qqq_calmar_optimised_defensive_gate_sleeve" not in present:
        missing.append("codex_experimental")
    return ", ".join(missing) + " return streams missing" if missing else "none"


def normalize_high_growth_stream_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized = []
    for row in rows:
        candidate = row.get("candidate_name") or row.get("strategy_name")
        date = row.get("date")
        daily_return = row.get("daily_strategy_return") or row.get("daily_return")
        if not candidate or not date or daily_return in {"", None}:
            continue
        new_row = dict(row)
        new_row["candidate_name"] = str(candidate)
        new_row["daily_strategy_return"] = str(daily_return)
        normalized.append(new_row)
    return normalized


def normalize_recovered_reference_stream_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized = []
    for row in rows:
        if row.get("candidate_name") != RECOVERED_QQQ100_REFERENCE:
            continue
        if row.get("reference_status") != RECOVERED_REFERENCE_READY_STATUS:
            continue
        if not false_safety_flags(row):
            continue
        date = row.get("date")
        daily_return = row.get("daily_strategy_return")
        if not date or daily_return in {"", None}:
            continue
        normalized.append(dict(row))
    return normalized


def recovered_reference_info(inputs: dict[str, list[dict[str, str]]], return_streams: list[dict[str, str]]) -> dict[str, Any]:
    metrics_row = next((row for row in inputs.get("qqq100_recovered_reference_metrics", []) if row.get("reference_name") == RECOVERED_QQQ100_REFERENCE), {})
    metrics = recovered_metrics_from_row(metrics_row)
    by_candidate = stream_returns_by_candidate(return_streams)
    status = metrics_row.get("reference_status", "missing_recovered_reference")
    available = (
        status == RECOVERED_REFERENCE_READY_STATUS
        and metrics_row.get("gap_threshold_status") == "all_metric_gaps_within_research_review_thresholds"
        and false_safety_flags(metrics_row)
        and RECOVERED_QQQ100_REFERENCE in by_candidate
        and not metrics_missing(metrics)
    )
    return {
        "available": available,
        "status": status if status else "missing_recovered_reference",
        "metrics": metrics,
    }


def recovered_metrics_from_row(row: dict[str, str]) -> dict[str, str]:
    metrics = missing_metrics()
    if not row:
        metrics["baseline_source"] = "missing_recovered_qqq100_reference"
        return metrics
    metrics.update(
        {
            "cagr": row.get("cagr", MISSING) or MISSING,
            "sharpe": row.get("sharpe", MISSING) or MISSING,
            "max_drawdown": row.get("max_drawdown", MISSING) or MISSING,
            "calmar": row.get("calmar", MISSING) or MISSING,
            "annualised_volatility": row.get("annual_volatility", MISSING) or MISSING,
            "cash_percentage": row.get("cash_percentage", MISSING) or MISSING,
            "turnover_or_trade_count": row.get("trade_signal_change_count", MISSING) or MISSING,
            "baseline_source": "qqq100_recovered_reference_stream",
        }
    )
    return metrics


def false_safety_flags(row: dict[str, str]) -> bool:
    return (
        str(row.get("execution_approved", "false")).lower() == "false"
        and str(row.get("scheduling_approved", "false")).lower() == "false"
        and str(row.get("orders_created", "false")).lower() == "false"
        and str(row.get("orders_submitted", "false")).lower() == "false"
        and str(row.get("orders_cancelled", "false")).lower() == "false"
    )


def stream_returns_by_candidate(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    by_candidate: dict[str, dict[str, float]] = {}
    for row in rows:
        candidate = str(row.get("candidate_name", ""))
        date = str(row.get("date", ""))
        if not candidate or not date:
            continue
        try:
            value = float(row.get("daily_strategy_return", ""))
        except (TypeError, ValueError):
            continue
        by_candidate.setdefault(candidate, {})[date] = value
    return by_candidate


def metrics_for_returns(returns: list[float]) -> dict[str, str]:
    equity = 1.0
    curve = []
    for value in returns:
        equity *= 1.0 + value
        curve.append(equity)
    years = max(len(returns) / 252.0, 1 / 252.0)
    cagr = (equity ** (1.0 / years) - 1.0) * 100.0
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / max(1, len(returns) - 1)
    annual_vol = (variance ** 0.5) * (252.0 ** 0.5) * 100.0
    sharpe = mean / (variance ** 0.5) * (252.0 ** 0.5) if variance > 0 else 0.0
    maxdd = max_drawdown_pct(curve)
    calmar = cagr / abs(maxdd) if maxdd < 0 else 0.0
    cash_pct = 100.0 * sum(1 for value in returns if abs(value) < 1e-12) / len(returns)
    return {
        "cagr": str(round(cagr, 4)),
        "sharpe": str(round(sharpe, 4)),
        "max_drawdown": str(round(maxdd, 4)),
        "calmar": str(round(calmar, 4)),
        "annualised_volatility": str(round(annual_vol, 4)),
        "cash_percentage": str(round(cash_pct, 4)),
        "turnover_or_trade_count": MISSING,
        "baseline_source": "sleeve_return_streams_saved_metrics",
    }


def max_drawdown_pct(curve: list[float]) -> float:
    if not curve:
        return 0.0
    peak = curve[0]
    worst = 0.0
    for value in curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value / peak - 1.0) * 100.0)
    return worst


def stream_signal_change_count(rows: list[dict[str, str]], candidates: set[str]) -> int:
    changes = 0
    previous_by_candidate: dict[str, str] = {}
    for row in sorted(rows, key=lambda item: (item.get("candidate_name", ""), item.get("date", ""))):
        candidate = str(row.get("candidate_name", ""))
        if candidate not in candidates:
            continue
        state = str(row.get("signal_state", ""))
        previous = previous_by_candidate.get(candidate)
        if previous is not None and previous != state:
            changes += 1
        previous_by_candidate[candidate] = state
    return changes


def metric_delta(value: str, reference: str) -> str:
    try:
        return str(round(float(value) - float(reference), 4))
    except (TypeError, ValueError):
        return MISSING


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


def qqq100_metric_bundle(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    rows: list[tuple[str, dict[str, str]]] = []
    for source_name in [
        "project_research_state",
        "qqq100_preview_readiness",
        "qqq100_signal",
        "qqq100_action_preview",
        "qqq_lead_decision",
        "sleeve_candidates",
    ]:
        rows.extend((source_name, row) for row in inputs.get(source_name, []))
    metrics = missing_metrics()
    metrics["baseline_source"] = "missing_exact_qqq100_saved_metrics"
    for source_name, row in rows:
        if not is_exact_qqq100_row(row):
            continue
        candidate = metrics_from_row(row)
        if all(candidate[key] != MISSING for key in ["cagr", "sharpe", "max_drawdown", "calmar"]):
            candidate["baseline_source"] = baseline_source_label(source_name)
            return candidate
    return metrics


def defensive_metric_bundle(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    rows = inputs["codex_defensive_pack"] + inputs["codex_defensive_candidates"]
    for row in rows:
        if "codex_qqq_calmar_optimised_defensive_gate_sleeve" in row_identity(row):
            metrics = metrics_from_row(row)
            metrics["baseline_source"] = "codex_defensive_crash_gate_saved_metrics"
            return metrics
    metrics = missing_metrics()
    metrics["baseline_source"] = "missing_saved_defensive_crash_gate_metrics"
    return metrics


def codex_metric_bundle(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return defensive_metric_bundle(inputs)


def saved_metric_bundle(rows: list[dict[str, str]]) -> dict[str, str]:
    for row in rows:
        metrics = metrics_from_row(row)
        if not metrics_missing(metrics):
            metrics["baseline_source"] = "saved_summary_metrics"
            return metrics
    metrics = missing_metrics()
    metrics["baseline_source"] = "missing_saved_summary_metrics"
    return metrics


def metrics_from_row(row: dict[str, str]) -> dict[str, str]:
    metrics = missing_metrics()
    direct_fields = {
        "cagr": ["cagr", "CAGR", "cagr_pct", "annual_return", "estimated_or_observed_cagr", "baseline_cagr", "qqq100_reference_cagr", "candidate_cagr"],
        "sharpe": ["sharpe", "Sharpe", "sharpe_ratio", "estimated_or_observed_sharpe", "baseline_sharpe", "qqq100_reference_sharpe", "candidate_sharpe"],
        "max_drawdown": ["max_drawdown", "max_drawdown_pct", "MaxDD", "maxdd", "estimated_or_observed_max_drawdown", "baseline_max_drawdown", "qqq100_reference_max_drawdown", "candidate_max_drawdown"],
        "calmar": ["calmar", "Calmar", "calmar_ratio", "estimated_or_observed_calmar", "baseline_calmar", "qqq100_reference_calmar", "candidate_calmar"],
        "annualised_volatility": ["annualised_volatility", "volatility"],
        "cash_percentage": ["cash_percentage", "cash_pct"],
        "turnover_or_trade_count": ["turnover_or_trade_count", "trade_count", "turnover"],
    }
    for metric_name, fields in direct_fields.items():
        for field in fields:
            value = str(row.get(field, "")).strip()
            if value:
                metrics[metric_name] = value
                break
    text = " ".join(str(value) for value in row.values())
    patterns = {
        "cagr": [r"\bCAGR\s*=\s*([-+]?\d+(?:\.\d+)?)", r"\bcagr\s*=\s*([-+]?\d+(?:\.\d+)?)"],
        "sharpe": [r"\bSharpe\s*=\s*([-+]?\d+(?:\.\d+)?)", r"\bsharpe\s*=\s*([-+]?\d+(?:\.\d+)?)"],
        "max_drawdown": [r"\bMaxDD\s*=\s*([-+]?\d+(?:\.\d+)?)", r"\bmax_drawdown\s*=\s*([-+]?\d+(?:\.\d+)?)"],
        "calmar": [r"\bCalmar\s*=\s*([-+]?\d+(?:\.\d+)?)", r"\bcalmar\s*=\s*([-+]?\d+(?:\.\d+)?)"],
    }
    for metric_name, metric_patterns in patterns.items():
        if metrics[metric_name] != MISSING:
            continue
        for pattern in metric_patterns:
            match = re.search(pattern, text)
            if match:
                metrics[metric_name] = match.group(1)
                break
    return metrics


def missing_portfolio_metrics() -> dict[str, str]:
    metrics = missing_metrics()
    metrics["baseline_source"] = "missing_combined_portfolio_return_stream"
    return metrics


def missing_metrics() -> dict[str, str]:
    return {
        "cagr": MISSING,
        "sharpe": MISSING,
        "max_drawdown": MISSING,
        "calmar": MISSING,
        "annualised_volatility": MISSING,
        "cash_percentage": MISSING,
        "turnover_or_trade_count": MISSING,
        "baseline_source": "missing_saved_metrics",
    }


def metrics_missing(metrics: dict[str, str]) -> bool:
    return any(metrics.get(key, MISSING) == MISSING for key in ["cagr", "sharpe", "max_drawdown", "calmar"])


def is_exact_qqq100_row(row: dict[str, str]) -> bool:
    identity = row_identity(row)
    if "codex_ambitious_concentrated_growth_persistence" in identity:
        return False
    return (
        "qqq_100_trend_gate" in identity
        or "qqq100_core_trend_sleeve" in identity
        or "qqq100_clean_lead" in identity
        or "qqq_100_simpler_lower_drawdown_candidate" in identity
    )


def row_identity(row: dict[str, str]) -> str:
    identity_fields = [
        "candidate_name",
        "strategy_name",
        "sleeve_name",
        "metric_value",
        "summary_value",
        "check_status",
        "readiness_label",
        "lead_name",
        "variant_name",
        "portfolio_name",
    ]
    return " ".join(str(row.get(field, "")).strip().lower() for field in identity_fields)


def baseline_source_label(source_name: str) -> str:
    if source_name == "project_research_state":
        return "qqq_100_trend_gate_saved_metrics"
    if source_name == "sleeve_candidates":
        return "qqq100_core_trend_sleeve_saved_metrics"
    return f"{source_name}_exact_qqq100_saved_metrics"


def missing_data_warning(sleeve_rows: list[dict[str, Any]]) -> str:
    missing = [
        str(row["sleeve_name"])
        for row in sleeve_rows
        if str(row["return_stream_status"]) in {MISSING_RETURN_STREAM, "missing_saved_return_stream"}
    ]
    return ", ".join(missing) if missing else "none"


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "Multi-sleeve portfolio backtest created. Saved-output-only research; no execution wiring approved.",
        f"final_backtest_status: {summary['final_backtest_status']}",
        f"saved QQQ100 benchmark metrics: CAGR={summary['saved_qqq100_benchmark_cagr']}, Sharpe={summary['saved_qqq100_benchmark_sharpe']}, MaxDD={summary['saved_qqq100_benchmark_max_drawdown']}, Calmar={summary['saved_qqq100_benchmark_calmar']}",
        f"QQQ100 reference source used: {summary['qqq100_reference_source_used']}",
        f"old generated QQQ100 diagnostic reference metrics: CAGR={summary['generated_qqq100_reference_cagr']}, Sharpe={summary['generated_qqq100_reference_sharpe']}, MaxDD={summary['generated_qqq100_reference_max_drawdown']}, Calmar={summary['generated_qqq100_reference_calmar']}",
        f"old generated QQQ100 diagnostic reference status: {summary['old_generated_reference_status']}",
        f"recovered QQQ100 preferred reference metrics: CAGR={summary['recovered_qqq100_reference_cagr']}, Sharpe={summary['recovered_qqq100_reference_sharpe']}, MaxDD={summary['recovered_qqq100_reference_max_drawdown']}, Calmar={summary['recovered_qqq100_reference_calmar']}",
        f"saved benchmark reconciliation status: {summary['saved_benchmark_reconciliation_status']}",
        f"top multi-sleeve portfolio candidate: {summary['top_multi_sleeve_portfolio_candidate']}",
        f"candidate allocation: {summary['candidate_allocation']}",
        f"candidate metrics: CAGR={summary['candidate_cagr']}, Sharpe={summary['candidate_sharpe']}, MaxDD={summary['candidate_max_drawdown']}, Calmar={summary['candidate_calmar']}",
        f"delta_vs_recovered_qqq100_reference: delta_CAGR={summary['delta_cagr_vs_recovered_qqq100_reference']}, delta_Sharpe={summary['delta_sharpe_vs_recovered_qqq100_reference']}, delta_MaxDD={summary['delta_max_drawdown_vs_recovered_qqq100_reference']}, delta_Calmar={summary['delta_calmar_vs_recovered_qqq100_reference']}",
        f"diagnostic_delta_vs_old_generated_qqq100_reference: delta_CAGR={summary['delta_cagr_vs_generated_qqq100_reference']}, delta_Sharpe={summary['delta_sharpe_vs_generated_qqq100_reference']}, delta_MaxDD={summary['delta_max_drawdown_vs_generated_qqq100_reference']}, delta_Calmar={summary['delta_calmar_vs_generated_qqq100_reference']}",
        f"split stability summary: {summary['split_stability_summary']}",
        f"missing sleeve data warnings: {summary['missing_sleeve_data_warnings']}",
        f"biggest blocker: {summary['biggest_blocker']}",
        f"recommended next step: {summary['recommended_next_step']}",
        f"Saved backtest: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; qqq100_execution_approved=false; codex_experimental_execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
