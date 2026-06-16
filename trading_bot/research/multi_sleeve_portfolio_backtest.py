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
QQQ100_REFERENCE = "qqq100_only_reference"
QQQ100_SLEEVE = "qqq100_core_trend_sleeve"
QQQ100_STRATEGY = "qqq_100_trend_gate"
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
    sleeve_rows = build_sleeve_rows(created_at, inputs, qqq_metrics)
    portfolios = build_portfolio_rows(created_at, qqq_metrics, sleeve_rows)
    allocations = build_allocation_rows(created_at, sleeve_rows)
    rankings = build_ranking_rows(created_at, portfolios)
    splits = build_split_rows(created_at, portfolios, qqq_metrics)
    trades = build_trade_rows(created_at, portfolios)
    blockers = build_blocker_rows(created_at)
    summary = build_summary_rows(created_at, portfolios, qqq_metrics)
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
        f"QQQ100 reference metrics: CAGR={summary.get('qqq100_reference_cagr', MISSING)}, Sharpe={summary.get('qqq100_reference_sharpe', MISSING)}, MaxDD={summary.get('qqq100_reference_max_drawdown', MISSING)}, Calmar={summary.get('qqq100_reference_calmar', MISSING)}",
        f"top multi-sleeve portfolio candidate: {summary.get('top_multi_sleeve_portfolio_candidate', 'missing')}",
        f"candidate allocation: {summary.get('candidate_allocation', 'missing')}",
        f"candidate metrics: CAGR={summary.get('candidate_cagr', MISSING)}, Sharpe={summary.get('candidate_sharpe', MISSING)}, MaxDD={summary.get('candidate_max_drawdown', MISSING)}, Calmar={summary.get('candidate_calmar', MISSING)}",
        f"improvement vs QQQ100 reference: delta_CAGR={summary.get('delta_cagr_vs_qqq100', MISSING)}, delta_Sharpe={summary.get('delta_sharpe_vs_qqq100', MISSING)}, delta_MaxDD={summary.get('delta_max_drawdown_vs_qqq100', MISSING)}, delta_Calmar={summary.get('delta_calmar_vs_qqq100', MISSING)}",
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
) -> list[dict[str, Any]]:
    defensive_metrics = defensive_metric_bundle(inputs)
    high_growth_metrics = saved_metric_bundle(
        inputs["high_growth_final_validation"] + inputs["high_growth_branch"] + inputs["high_growth_lab"]
    )
    crypto_metrics = saved_metric_bundle(inputs["crypto_lab"] + inputs["crypto_state"] + inputs["crypto_lead"])
    codex_metrics = codex_metric_bundle(inputs)
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
            "missing_saved_return_stream" if metrics_missing(defensive_metrics) else "saved_metric_reference_only",
            defensive_metrics["baseline_source"],
            defensive_metrics,
            "needs_cost_turnover_stress",
            "missing_split_metrics",
            "single_etf_with_regime_gate",
            "high_overlap_with_qqq_by_design",
            "research_only_needs_daily_return_stream",
            "Backtest QQQ/SPY/drawdown gates before candidate label change.",
        ),
        sleeve_row(
            created_at,
            "high_growth_stock_research_sleeve",
            "codex_broad_growth_balanced_breakout_control",
            "high-growth stocks",
            "high-risk research sleeve",
            "missing_saved_return_stream",
            "summary_metrics_only_or_unavailable",
            high_growth_metrics,
            "cost_review_required",
            "split_review_required",
            "high_concentration_and_outlier_risk",
            "high_growth_overlap_with_qqq",
            "research_only_missing_return_stream",
            "Do not include in portfolio metrics until saved daily returns exist.",
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
            "missing_saved_return_stream" if metrics_missing(codex_metrics) else "saved_metric_reference_only",
            codex_metrics["baseline_source"],
            codex_metrics,
            "needs_cost_stress_review",
            "needs_split_validation",
            "moderate_overlap_and_parameter_risk",
            "high_overlap_with_qqq_by_design",
            "research_only_needs_market_metrics",
            "Run transparent saved/research-data validation before any candidate label change.",
        ),
    ]


def build_portfolio_rows(
    created_at: str,
    qqq_metrics: dict[str, str],
    sleeve_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    portfolio_specs = [
        (QQQ100_REFERENCE, "reference", "100% qqq100_core_trend_sleeve", 82, "reference_only", qqq_metrics),
        (TOP_MULTI_SLEEVE_CANDIDATE, "cash defensive reference", "95% qqq100_core_trend_sleeve; 5% defensive_cash_or_bond_sleeve", 63, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("qqq100_plus_defensive_crash_gate", "defensive crash-gate research", "70% qqq100_core_trend_sleeve; 25% qqq_defensive_crash_gate_research_sleeve; 5% defensive_cash_or_bond_sleeve", 58, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("qqq100_plus_high_growth_research", "high-growth research blend", "80% qqq100_core_trend_sleeve; 15% high_growth_stock_research_sleeve; 5% defensive_cash_or_bond_sleeve", 42, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("qqq100_plus_crypto_research", "crypto research blend", "85% qqq100_core_trend_sleeve; 10% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve", 40, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("balanced_multi_sleeve_research_portfolio", "balanced reduced research portfolio", "50% qqq100_core_trend_sleeve; 20% qqq_defensive_crash_gate_research_sleeve; 15% high_growth_stock_research_sleeve; 10% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve", 45, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
        ("codex_ambitious_multi_sleeve_candidate", "Codex ambitious transparent allocation", "60% qqq100_core_trend_sleeve; 25% codex_experimental_research_sleeve; 10% defensive_cash_or_bond_sleeve; 5% research optionality reserve", 52, "multi_sleeve_candidate_needs_more_data", missing_portfolio_metrics()),
    ]
    missing_warnings = missing_data_warning(sleeve_rows)
    rows = []
    for name, role, allocation, score, status, metrics in portfolio_specs:
        rows.append(
            {
                "created_at": created_at,
                "portfolio_name": name,
                "portfolio_role": role,
                "final_backtest_status": "multi_sleeve_portfolio_backtest_created" if name == QQQ100_REFERENCE else status,
                "baseline_source": qqq_metrics["baseline_source"],
                "qqq100_reference_cagr": qqq_metrics["cagr"],
                "qqq100_reference_sharpe": qqq_metrics["sharpe"],
                "qqq100_reference_max_drawdown": qqq_metrics["max_drawdown"],
                "qqq100_reference_calmar": qqq_metrics["calmar"],
                "candidate_allocation": allocation,
                "candidate_cagr": metrics["cagr"],
                "candidate_sharpe": metrics["sharpe"],
                "candidate_max_drawdown": metrics["max_drawdown"],
                "candidate_calmar": metrics["calmar"],
                "candidate_annualised_volatility": metrics["annualised_volatility"],
                "candidate_cash_percentage": "0" if name == QQQ100_REFERENCE else ("5" if "5%" in allocation else MISSING),
                "candidate_sleeve_exposure_percentages": allocation,
                "candidate_turnover_or_trade_count": metrics["turnover_or_trade_count"],
                "rough_cost_sensitivity": "reference_not_recomputed" if name == QQQ100_REFERENCE else "missing_cost_turnover_stream",
                "delta_cagr_vs_qqq100": "0" if name == QQQ100_REFERENCE else MISSING,
                "delta_sharpe_vs_qqq100": "0" if name == QQQ100_REFERENCE else MISSING,
                "delta_max_drawdown_vs_qqq100": "0" if name == QQQ100_REFERENCE else MISSING,
                "delta_calmar_vs_qqq100": "0" if name == QQQ100_REFERENCE else MISSING,
                "split_stability_label": "missing_split_metrics",
                "balanced_research_score": str(score),
                "data_quality": "saved_qqq100_metrics_only" if name == QQQ100_REFERENCE else "missing_return_stream_for_combined_metrics",
                "missing_sleeve_data_warnings": "none_for_reference" if name == QQQ100_REFERENCE else missing_warnings,
                "biggest_blocker": BIGGEST_BLOCKER,
                "recommended_next_step": RECOMMENDED_NEXT_STEP,
                **safety_flags(),
            }
        )
    return rows


def build_allocation_rows(created_at: str, sleeve_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = {
        QQQ100_REFERENCE: [(QQQ100_SLEEVE, "100")],
        TOP_MULTI_SLEEVE_CANDIDATE: [(QQQ100_SLEEVE, "95"), ("defensive_cash_or_bond_sleeve", "5")],
        "qqq100_plus_defensive_crash_gate": [(QQQ100_SLEEVE, "70"), ("qqq_defensive_crash_gate_research_sleeve", "25"), ("defensive_cash_or_bond_sleeve", "5")],
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
                    "actual_weight_pct": weight if stream_status in {"saved_metric_reference_only", "cash_available_bond_etf_data_unavailable"} else "not_modelled",
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
) -> list[dict[str, Any]]:
    candidate = next(row for row in portfolios if row["portfolio_name"] == TOP_MULTI_SLEEVE_CANDIDATE)
    summary_items = [
        ("final_backtest_status", FINAL_BACKTEST_STATUS, "Missing return streams block multi-sleeve candidate label changes."),
        ("baseline_source", qqq_metrics["baseline_source"], "Exact QQQ100 saved metrics source."),
        ("qqq100_reference_cagr", qqq_metrics["cagr"], "QQQ100 clean lead CAGR."),
        ("qqq100_reference_sharpe", qqq_metrics["sharpe"], "QQQ100 clean lead Sharpe."),
        ("qqq100_reference_max_drawdown", qqq_metrics["max_drawdown"], "QQQ100 clean lead max drawdown."),
        ("qqq100_reference_calmar", qqq_metrics["calmar"], "QQQ100 clean lead Calmar."),
        ("top_multi_sleeve_portfolio_candidate", TOP_MULTI_SLEEVE_CANDIDATE, "Conservative cash-reference candidate is the top multi-sleeve design, but metrics are blocked."),
        ("candidate_allocation", candidate["candidate_allocation"], "Allocation is a research design only; it is not an order plan."),
        ("candidate_cagr", candidate["candidate_cagr"], "Combined portfolio metric unavailable without saved return streams."),
        ("candidate_sharpe", candidate["candidate_sharpe"], "Combined portfolio metric unavailable without saved return streams."),
        ("candidate_max_drawdown", candidate["candidate_max_drawdown"], "Combined portfolio metric unavailable without saved return streams."),
        ("candidate_calmar", candidate["candidate_calmar"], "Combined portfolio metric unavailable without saved return streams."),
        ("delta_cagr_vs_qqq100", candidate["delta_cagr_vs_qqq100"], "Improvement unavailable without combined metrics."),
        ("delta_sharpe_vs_qqq100", candidate["delta_sharpe_vs_qqq100"], "Improvement unavailable without combined metrics."),
        ("delta_max_drawdown_vs_qqq100", candidate["delta_max_drawdown_vs_qqq100"], "Improvement unavailable without combined metrics."),
        ("delta_calmar_vs_qqq100", candidate["delta_calmar_vs_qqq100"], "Improvement unavailable without combined metrics."),
        ("split_stability_summary", "missing_split_metrics", "Fixed chronological split metrics are unavailable."),
        ("missing_sleeve_data_warnings", "defensive_crash_gate, high_growth, crypto, and codex_experimental return streams missing", "Missing streams are labelled rather than invented."),
        ("biggest_blocker", BIGGEST_BLOCKER, "Daily return streams are needed before multi-sleeve metrics can be trusted."),
        ("recommended_next_step", RECOMMENDED_NEXT_STEP, "Build saved return streams/split metrics before any candidate status change."),
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
        f"QQQ100 reference metrics: CAGR={summary['qqq100_reference_cagr']}, Sharpe={summary['qqq100_reference_sharpe']}, MaxDD={summary['qqq100_reference_max_drawdown']}, Calmar={summary['qqq100_reference_calmar']}",
        f"top multi-sleeve portfolio candidate: {summary['top_multi_sleeve_portfolio_candidate']}",
        f"candidate allocation: {summary['candidate_allocation']}",
        f"candidate metrics: CAGR={summary['candidate_cagr']}, Sharpe={summary['candidate_sharpe']}, MaxDD={summary['candidate_max_drawdown']}, Calmar={summary['candidate_calmar']}",
        f"improvement vs QQQ100 reference: delta_CAGR={summary['delta_cagr_vs_qqq100']}, delta_Sharpe={summary['delta_sharpe_vs_qqq100']}, delta_MaxDD={summary['delta_max_drawdown_vs_qqq100']}, delta_Calmar={summary['delta_calmar_vs_qqq100']}",
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
