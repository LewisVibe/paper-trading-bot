"""Saved-output-only robustness validation for the high-growth multi-sleeve candidate.

This module reads existing saved daily return streams and portfolio backtest
outputs. It does not refresh market data, call Alpaca, read positions, create
orders, write SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import multi_sleeve_portfolio_backtest as backtest


FINAL_STATUS_PROMISING = "multi_sleeve_robustness_promising"
FINAL_STATUS_MIXED = "multi_sleeve_robustness_mixed"
FINAL_STATUS_WEAK = "multi_sleeve_robustness_weak"
FINAL_STATUS_BLOCKED_MISSING_STREAMS = "multi_sleeve_robustness_blocked_missing_streams"
FINAL_STATUS_BLOCKED_QQQ100_RECONCILIATION = "multi_sleeve_robustness_blocked_qqq100_reconciliation"

PORTFOLIO_CANDIDATE = "qqq100_plus_high_growth_research"
GENERATED_QQQ100 = "generated_qqq100_reference"
PREFERRED_QQQ100_REFERENCE = "preferred_qqq100_reference"
HIGH_GROWTH_SLEEVE = "codex_broad_growth_balanced_breakout_control"
SAVED_QQQ100_CONTEXT = "saved_qqq100_benchmark_context"
REQUIRED_NEXT_STEP_RECONCILE = "reconcile_generated_qqq100_stream_with_saved_benchmark_before_preview_discussion"
REQUIRED_NEXT_STEP_STREAMS = "create_real_saved_return_streams_before_robustness_validation"
REQUIRED_NEXT_STEP_REVIEW = "manual_review_split_robustness_before_any_candidate_label_change"

INPUT_FILES = {
    "sleeve_return_streams": Path("data/sleeve_return_streams.csv"),
    "high_growth_return_streams": Path("data/high_growth_return_streams.csv"),
    "qqq100_recovered_reference_stream": Path("data/qqq100_recovered_reference_stream.csv"),
    "multi_sleeve_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "multi_sleeve_summary": Path("data/multi_sleeve_portfolio_backtest_summary.csv"),
}

OUTPUT_FILES = {
    "report": Path("data/multi_sleeve_robustness_report.csv"),
    "summary": Path("data/multi_sleeve_robustness_summary.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "preview_only",
    "saved_output_only",
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
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": True,
    "saved_output_only": True,
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
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

REPORT_COLUMNS = [
    "created_at",
    "split_name",
    "candidate_name",
    "period_label",
    "first_date",
    "last_date",
    "row_count",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "delta_CAGR_vs_generated_qqq100",
    "delta_Sharpe_vs_generated_qqq100",
    "delta_MaxDD_vs_generated_qqq100",
    "delta_Calmar_vs_generated_qqq100",
    "qqq100_reference_source_used",
    "recovered_reference_available",
    "old_generated_reference_retained",
    "comparison_reference_name",
    "comparison_reference_status",
    "delta_CAGR_vs_qqq100_reference",
    "delta_Sharpe_vs_qqq100_reference",
    "delta_MaxDD_vs_qqq100_reference",
    "delta_Calmar_vs_qqq100_reference",
    "robustness_status",
    "blocker_status",
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

SPLITS = [
    ("split_60_40", 0.60),
    ("split_70_30", 0.70),
    ("split_80_20", 0.80),
]


@dataclass
class MultiSleeveRobustnessResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_robustness(root_dir: Path | str = ".") -> MultiSleeveRobustnessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    saved_streams = read_csv_rows(root / INPUT_FILES["sleeve_return_streams"])
    high_growth_streams = backtest.normalize_high_growth_stream_rows(
        read_csv_rows(root / INPUT_FILES["high_growth_return_streams"])
    )
    streams = saved_streams + high_growth_streams
    streams += backtest.normalize_recovered_reference_stream_rows(
        read_csv_rows(root / INPUT_FILES["qqq100_recovered_reference_stream"])
    )
    by_candidate = backtest.stream_returns_by_candidate(streams)
    backtest_summary = summary_dict(read_csv_rows(root / INPUT_FILES["multi_sleeve_summary"]))
    saved_benchmark = saved_qqq100_context(backtest_summary)
    report_rows = build_report_rows(created_at, by_candidate, saved_benchmark, backtest_summary)
    summary_rows = build_summary_rows(created_at, report_rows, by_candidate, backtest_summary)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    return MultiSleeveRobustnessResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["report"]),
    )


def show_multi_sleeve_robustness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve robustness report is missing.",
            "Run `python bot.py --multi-sleeve-robustness` first.",
            "execution_approved=false; scheduling_approved=false",
        ]
    rows = summary_dict(read_csv_rows(path))
    return 0, [
        "Multi-sleeve robustness. Saved-output-only research; no execution wiring approved.",
        f"final robustness status: {rows.get('final_robustness_status', 'missing')}",
        f"split count: {rows.get('split_count', 'missing')}",
        f"QQQ100 reference source used: {rows.get('qqq100_reference_source_used', 'missing')}",
        f"comparison reference status: {rows.get('comparison_reference_status', 'missing')}",
        f"Calmar wins vs preferred QQQ100 reference: {rows.get('calmar_win_count_vs_generated_qqq100', 'missing')}",
        f"Sharpe wins vs preferred QQQ100 reference: {rows.get('sharpe_win_count_vs_generated_qqq100', 'missing')}",
        f"worst split by Calmar: {rows.get('worst_split_by_calmar', 'missing')}",
        f"worst split by MaxDD: {rows.get('worst_split_by_maxdd', 'missing')}",
        f"key blockers: {rows.get('key_blockers', 'missing')}",
        f"required next step: {rows.get('required_next_step', 'missing')}",
        "execution_approved=false; scheduling_approved=false",
    ]


def build_report_rows(
    created_at: str,
    by_candidate: dict[str, dict[str, float]],
    saved_benchmark: dict[str, str],
    backtest_summary: dict[str, str],
) -> list[dict[str, Any]]:
    reference_candidate = backtest_summary.get("qqq100_reference_source_used") or "old_generated_qqq100_reference"
    preferred_reference = (
        backtest.RECOVERED_QQQ100_REFERENCE
        if reference_candidate == backtest.RECOVERED_QQQ100_REFERENCE
        and backtest.RECOVERED_QQQ100_REFERENCE in by_candidate
        else "qqq_100_trend_gate"
    )
    recovered_available = preferred_reference == backtest.RECOVERED_QQQ100_REFERENCE
    comparison_reference_status = (
        "recovered_reference_preferred"
        if recovered_available
        else "old_generated_reference_fallback"
    )
    required = [preferred_reference, HIGH_GROWTH_SLEEVE, "cash_default_defensive_sleeve"]
    diagnostic_required = ["qqq_100_trend_gate"] if recovered_available else []
    required_with_diagnostics = required + diagnostic_required
    missing = [candidate for candidate in required_with_diagnostics if candidate not in by_candidate]
    if missing:
        return [
            blocked_row(
                created_at,
                "missing_streams",
                FINAL_STATUS_BLOCKED_MISSING_STREAMS,
                f"missing_saved_return_streams={','.join(missing)}",
                REQUIRED_NEXT_STEP_STREAMS,
            )
        ]

    rows: list[dict[str, Any]] = []
    common_dates = sorted(set.intersection(*(set(by_candidate[candidate]) for candidate in required_with_diagnostics)))
    if len(common_dates) < 3:
        return [
            blocked_row(
                created_at,
                "insufficient_overlap",
                FINAL_STATUS_BLOCKED_MISSING_STREAMS,
                "not_enough_common_daily_rows_for_split_validation",
                REQUIRED_NEXT_STEP_STREAMS,
            )
        ]
    qqq_returns = {date: by_candidate[preferred_reference][date] for date in common_dates}
    old_generated_returns = {date: by_candidate["qqq_100_trend_gate"][date] for date in common_dates} if "qqq_100_trend_gate" in by_candidate else {}
    high_growth_returns = {date: by_candidate[HIGH_GROWTH_SLEEVE][date] for date in common_dates}
    combined_returns = {
        date: (
            by_candidate["qqq_100_trend_gate"][date] * 0.80
            + by_candidate[HIGH_GROWTH_SLEEVE][date] * 0.15
            + by_candidate["cash_default_defensive_sleeve"][date] * 0.05
        )
        for date in common_dates
    }
    blocker_status, next_step = blocker_status_for_backtest(backtest_summary)
    for split_name, train_fraction in SPLITS:
        start_index = max(1, int(len(common_dates) * train_fraction))
        oos_dates = common_dates[start_index:]
        if len(oos_dates) < 2:
            rows.append(blocked_row(created_at, split_name, FINAL_STATUS_BLOCKED_MISSING_STREAMS, "split_has_too_few_oos_rows", REQUIRED_NEXT_STEP_STREAMS))
            continue
        qqq_metrics = metrics_for_dates(oos_dates, qqq_returns)
        combined_metrics = metrics_for_dates(oos_dates, combined_returns)
        high_growth_metrics = metrics_for_dates(oos_dates, high_growth_returns)
        rows.append(
            report_row(
                created_at,
                split_name,
                PORTFOLIO_CANDIDATE,
                "out_of_sample",
                oos_dates,
                combined_metrics,
                qqq_metrics,
                row_robustness_status(combined_metrics, qqq_metrics),
                blocker_status,
                next_step,
                backtest.RECOVERED_QQQ100_REFERENCE if recovered_available else "old_generated_qqq100_reference",
                recovered_available,
                preferred_reference,
                comparison_reference_status,
            )
        )
        rows.append(
            report_row(
                created_at,
                split_name,
                PREFERRED_QQQ100_REFERENCE,
                "out_of_sample_reference",
                oos_dates,
                qqq_metrics,
                qqq_metrics,
                "preferred_qqq100_reference",
                blocker_status,
                next_step,
                backtest.RECOVERED_QQQ100_REFERENCE if recovered_available else "old_generated_qqq100_reference",
                recovered_available,
                preferred_reference,
                comparison_reference_status,
            )
        )
        if recovered_available and old_generated_returns:
            old_generated_metrics = metrics_for_dates(oos_dates, old_generated_returns)
            rows.append(
                report_row(
                    created_at,
                    split_name,
                    GENERATED_QQQ100,
                    "out_of_sample_diagnostic_reference",
                    oos_dates,
                    old_generated_metrics,
                    qqq_metrics,
                    "old_generated_qqq100_diagnostic_reference",
                    blocker_status,
                    next_step,
                    backtest.RECOVERED_QQQ100_REFERENCE,
                    True,
                    preferred_reference,
                    comparison_reference_status,
                )
            )
        rows.append(
            report_row(
                created_at,
                split_name,
                HIGH_GROWTH_SLEEVE,
                "out_of_sample_sleeve",
                oos_dates,
                high_growth_metrics,
                qqq_metrics,
                high_growth_drag_status(high_growth_metrics, qqq_metrics),
                blocker_status,
                next_step,
                backtest.RECOVERED_QQQ100_REFERENCE if recovered_available else "old_generated_qqq100_reference",
                recovered_available,
                preferred_reference,
                comparison_reference_status,
            )
        )
        if saved_benchmark:
            rows.append(saved_context_row(created_at, split_name, saved_benchmark, blocker_status, next_step))
    return rows


def build_summary_rows(
    created_at: str,
    rows: list[dict[str, Any]],
    by_candidate: dict[str, dict[str, float]],
    backtest_summary: dict[str, str],
) -> list[dict[str, Any]]:
    portfolio_rows = [row for row in rows if row.get("candidate_name") == PORTFOLIO_CANDIDATE]
    split_count = len(portfolio_rows)
    calmar_wins = sum(1 for row in portfolio_rows if parse_float(row.get("delta_Calmar_vs_qqq100_reference")) > 0)
    sharpe_wins = sum(1 for row in portfolio_rows if parse_float(row.get("delta_Sharpe_vs_qqq100_reference")) > 0)
    worst_calmar = min(portfolio_rows, key=lambda row: parse_float(row.get("Calmar")), default={})
    worst_maxdd = min(portfolio_rows, key=lambda row: parse_float(row.get("MaxDD")), default={})
    final_status = final_robustness_status(rows, split_count, calmar_wins, sharpe_wins, by_candidate, backtest_summary)
    next_step = required_next_step_for_final_status(final_status)
    blockers = key_blockers(final_status, backtest_summary)
    items = [
        ("final_robustness_status", final_status, "Report-only robustness label; never promotion-ready or execution-ready."),
        ("split_count", str(split_count), "Number of chronological out-of-sample split rows for the multi-sleeve candidate."),
        ("calmar_win_count_vs_generated_qqq100", str(calmar_wins), "Splits where the high-growth multi-sleeve candidate beats the preferred QQQ100 reference on Calmar."),
        ("sharpe_win_count_vs_generated_qqq100", str(sharpe_wins), "Splits where the high-growth multi-sleeve candidate beats the preferred QQQ100 reference on Sharpe."),
        ("qqq100_reference_source_used", portfolio_rows[0].get("qqq100_reference_source_used", "missing") if portfolio_rows else "missing", "Primary QQQ100 reference used for split deltas."),
        ("recovered_reference_available", str(portfolio_rows[0].get("recovered_reference_available", False)).lower() if portfolio_rows else "false", "Recovered QQQ100 reference is used only when saved validation exists."),
        ("old_generated_reference_retained", "true", "Old generated QQQ100 stream remains retained as diagnostic context."),
        ("comparison_reference_name", portfolio_rows[0].get("comparison_reference_name", "missing") if portfolio_rows else "missing", "Candidate-name key for the preferred comparison reference."),
        ("comparison_reference_status", portfolio_rows[0].get("comparison_reference_status", "missing") if portfolio_rows else "missing", "Whether split deltas use recovered reference or old generated fallback."),
        ("worst_split_by_calmar", format_worst(worst_calmar, "Calmar"), "Lowest candidate Calmar split."),
        ("worst_split_by_maxdd", format_worst(worst_maxdd, "MaxDD"), "Worst candidate drawdown split."),
        ("beats_generated_qqq100_on_most_splits", str(calmar_wins >= 2 and sharpe_wins >= 2), "Requires majority wins on both Calmar and Sharpe."),
        ("improvement_driver", improvement_driver(portfolio_rows), "Simple read on whether gains are mostly return, drawdown, Sharpe, or Calmar."),
        ("key_blockers", blockers, "Blocking issues before any candidate label change."),
        ("required_next_step", next_step, "Next review action; not execution approval."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def report_row(
    created_at: str,
    split_name: str,
    candidate_name: str,
    period_label: str,
    dates: list[str],
    metrics: dict[str, str],
    qqq_metrics: dict[str, str],
    robustness_status: str,
    blocker_status: str,
    required_next_step: str,
    qqq100_reference_source_used: str,
    recovered_reference_available: bool,
    comparison_reference_name: str,
    comparison_reference_status: str,
) -> dict[str, Any]:
    delta_cagr = backtest.metric_delta(metrics["cagr"], qqq_metrics["cagr"])
    delta_sharpe = backtest.metric_delta(metrics["sharpe"], qqq_metrics["sharpe"])
    delta_maxdd = backtest.metric_delta(metrics["max_drawdown"], qqq_metrics["max_drawdown"])
    delta_calmar = backtest.metric_delta(metrics["calmar"], qqq_metrics["calmar"])
    return {
        "created_at": created_at,
        "split_name": split_name,
        "candidate_name": candidate_name,
        "period_label": period_label,
        "first_date": dates[0] if dates else "",
        "last_date": dates[-1] if dates else "",
        "row_count": len(dates),
        "CAGR": metrics["cagr"],
        "Sharpe": metrics["sharpe"],
        "MaxDD": metrics["max_drawdown"],
        "Calmar": metrics["calmar"],
        "delta_CAGR_vs_generated_qqq100": delta_cagr,
        "delta_Sharpe_vs_generated_qqq100": delta_sharpe,
        "delta_MaxDD_vs_generated_qqq100": delta_maxdd,
        "delta_Calmar_vs_generated_qqq100": delta_calmar,
        "qqq100_reference_source_used": qqq100_reference_source_used,
        "recovered_reference_available": recovered_reference_available,
        "old_generated_reference_retained": True,
        "comparison_reference_name": comparison_reference_name,
        "comparison_reference_status": comparison_reference_status,
        "delta_CAGR_vs_qqq100_reference": delta_cagr,
        "delta_Sharpe_vs_qqq100_reference": delta_sharpe,
        "delta_MaxDD_vs_qqq100_reference": delta_maxdd,
        "delta_Calmar_vs_qqq100_reference": delta_calmar,
        "robustness_status": robustness_status,
        "blocker_status": blocker_status,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def blocked_row(created_at: str, split_name: str, status: str, blocker_status: str, required_next_step: str) -> dict[str, Any]:
    missing = backtest.MISSING
    return {
        "created_at": created_at,
        "split_name": split_name,
        "candidate_name": PORTFOLIO_CANDIDATE,
        "period_label": "blocked",
        "first_date": "",
        "last_date": "",
        "row_count": 0,
        "CAGR": missing,
        "Sharpe": missing,
        "MaxDD": missing,
        "Calmar": missing,
        "delta_CAGR_vs_generated_qqq100": missing,
        "delta_Sharpe_vs_generated_qqq100": missing,
        "delta_MaxDD_vs_generated_qqq100": missing,
        "delta_Calmar_vs_generated_qqq100": missing,
        "qqq100_reference_source_used": "missing_reference",
        "recovered_reference_available": False,
        "old_generated_reference_retained": True,
        "comparison_reference_name": "missing_reference",
        "comparison_reference_status": "missing_reference",
        "delta_CAGR_vs_qqq100_reference": missing,
        "delta_Sharpe_vs_qqq100_reference": missing,
        "delta_MaxDD_vs_qqq100_reference": missing,
        "delta_Calmar_vs_qqq100_reference": missing,
        "robustness_status": status,
        "blocker_status": blocker_status,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def saved_context_row(
    created_at: str,
    split_name: str,
    metrics: dict[str, str],
    blocker_status: str,
    required_next_step: str,
) -> dict[str, Any]:
    missing = backtest.MISSING
    return {
        "created_at": created_at,
        "split_name": split_name,
        "candidate_name": SAVED_QQQ100_CONTEXT,
        "period_label": "saved_metrics_context_only_not_daily_stream",
        "first_date": "",
        "last_date": "",
        "row_count": 0,
        "CAGR": metrics.get("cagr", missing),
        "Sharpe": metrics.get("sharpe", missing),
        "MaxDD": metrics.get("max_drawdown", missing),
        "Calmar": metrics.get("calmar", missing),
        "delta_CAGR_vs_generated_qqq100": missing,
        "delta_Sharpe_vs_generated_qqq100": missing,
        "delta_MaxDD_vs_generated_qqq100": missing,
        "delta_Calmar_vs_generated_qqq100": missing,
        "qqq100_reference_source_used": "saved_metrics_context_only",
        "recovered_reference_available": False,
        "old_generated_reference_retained": True,
        "comparison_reference_name": "saved_metrics_context_only",
        "comparison_reference_status": "saved_metrics_context_only",
        "delta_CAGR_vs_qqq100_reference": missing,
        "delta_Sharpe_vs_qqq100_reference": missing,
        "delta_MaxDD_vs_qqq100_reference": missing,
        "delta_Calmar_vs_qqq100_reference": missing,
        "robustness_status": "saved_qqq100_benchmark_context_only",
        "blocker_status": blocker_status,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def metrics_for_dates(dates: list[str], returns_by_date: dict[str, float]) -> dict[str, str]:
    returns = [returns_by_date[date] for date in dates]
    return backtest.metrics_for_returns(returns)


def blocker_status_for_backtest(summary: dict[str, str]) -> tuple[str, str]:
    reconciliation = summary.get("saved_benchmark_reconciliation_status", "")
    if "needs_reconciliation" in reconciliation:
        return FINAL_STATUS_BLOCKED_QQQ100_RECONCILIATION, REQUIRED_NEXT_STEP_RECONCILE
    return "no_blocker_from_saved_backtest_summary", REQUIRED_NEXT_STEP_REVIEW


def row_robustness_status(metrics: dict[str, str], qqq_metrics: dict[str, str]) -> str:
    calmar_delta = parse_float(backtest.metric_delta(metrics["calmar"], qqq_metrics["calmar"]))
    sharpe_delta = parse_float(backtest.metric_delta(metrics["sharpe"], qqq_metrics["sharpe"]))
    maxdd_delta = parse_float(backtest.metric_delta(metrics["max_drawdown"], qqq_metrics["max_drawdown"]))
    cagr_delta = parse_float(backtest.metric_delta(metrics["cagr"], qqq_metrics["cagr"]))
    if calmar_delta > 0 and sharpe_delta > 0 and maxdd_delta >= 0:
        return FINAL_STATUS_PROMISING
    if calmar_delta > 0 or sharpe_delta > 0 or cagr_delta > 0:
        return FINAL_STATUS_MIXED
    return FINAL_STATUS_WEAK


def high_growth_drag_status(metrics: dict[str, str], qqq_metrics: dict[str, str]) -> str:
    maxdd_delta = parse_float(backtest.metric_delta(metrics["max_drawdown"], qqq_metrics["max_drawdown"]))
    calmar_delta = parse_float(backtest.metric_delta(metrics["calmar"], qqq_metrics["calmar"]))
    if maxdd_delta < -5 or calmar_delta < -0.25:
        return "high_growth_drawdown_drag_warning"
    return "high_growth_sleeve_context_only"


def final_robustness_status(
    rows: list[dict[str, Any]],
    split_count: int,
    calmar_wins: int,
    sharpe_wins: int,
    by_candidate: dict[str, dict[str, float]],
    backtest_summary: dict[str, str],
) -> str:
    has_old = {"qqq_100_trend_gate", HIGH_GROWTH_SLEEVE, "cash_default_defensive_sleeve"}.issubset(by_candidate)
    has_recovered = {backtest.RECOVERED_QQQ100_REFERENCE, HIGH_GROWTH_SLEEVE, "cash_default_defensive_sleeve"}.issubset(by_candidate)
    if not (has_old or has_recovered):
        return FINAL_STATUS_BLOCKED_MISSING_STREAMS
    if "needs_reconciliation" in backtest_summary.get("saved_benchmark_reconciliation_status", ""):
        return FINAL_STATUS_BLOCKED_QQQ100_RECONCILIATION
    if split_count and calmar_wins >= 2 and sharpe_wins >= 2:
        return FINAL_STATUS_PROMISING
    if split_count and (calmar_wins or sharpe_wins):
        return FINAL_STATUS_MIXED
    return FINAL_STATUS_WEAK


def required_next_step_for_final_status(status: str) -> str:
    if status == FINAL_STATUS_BLOCKED_MISSING_STREAMS:
        return REQUIRED_NEXT_STEP_STREAMS
    if status == FINAL_STATUS_BLOCKED_QQQ100_RECONCILIATION:
        return REQUIRED_NEXT_STEP_RECONCILE
    return REQUIRED_NEXT_STEP_REVIEW


def key_blockers(status: str, backtest_summary: dict[str, str]) -> str:
    blockers = []
    if status == FINAL_STATUS_BLOCKED_MISSING_STREAMS:
        blockers.append("missing_saved_return_streams")
    if status == FINAL_STATUS_BLOCKED_QQQ100_RECONCILIATION:
        blockers.append(backtest_summary.get("saved_benchmark_reconciliation_status", status))
    if backtest_summary.get("missing_sleeve_data_warnings"):
        blockers.append(backtest_summary["missing_sleeve_data_warnings"])
    blockers.append("not_promotion_ready")
    blockers.append("execution_not_approved")
    return "; ".join(blockers)


def improvement_driver(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "missing_split_rows"
    cagr = sum(1 for row in rows if parse_float(row.get("delta_CAGR_vs_qqq100_reference")) > 0)
    sharpe = sum(1 for row in rows if parse_float(row.get("delta_Sharpe_vs_qqq100_reference")) > 0)
    maxdd = sum(1 for row in rows if parse_float(row.get("delta_MaxDD_vs_qqq100_reference")) > 0)
    calmar = sum(1 for row in rows if parse_float(row.get("delta_Calmar_vs_qqq100_reference")) > 0)
    scores = {"return": cagr, "sharpe": sharpe, "drawdown": maxdd, "calmar": calmar}
    best = max(scores, key=scores.get)
    return f"{best}_led; " + "; ".join(f"{name}_wins={value}" for name, value in scores.items())


def saved_qqq100_context(summary: dict[str, str]) -> dict[str, str]:
    fields = {
        "cagr": summary.get("saved_qqq100_benchmark_cagr", ""),
        "sharpe": summary.get("saved_qqq100_benchmark_sharpe", ""),
        "max_drawdown": summary.get("saved_qqq100_benchmark_max_drawdown", ""),
        "calmar": summary.get("saved_qqq100_benchmark_calmar", ""),
    }
    if all(value and value != backtest.MISSING for value in fields.values()):
        return fields
    return {}


def format_worst(row: dict[str, Any], metric: str) -> str:
    if not row:
        return "missing"
    return f"{row.get('split_name')} {metric}={row.get(metric)}; MaxDD={row.get('MaxDD')}; Calmar={row.get('Calmar')}"


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "Multi-sleeve robustness report created. Saved-output-only research; no execution wiring approved.",
        f"final robustness status: {summary['final_robustness_status']}",
        f"split count: {summary['split_count']}",
        f"QQQ100 reference source used: {summary['qqq100_reference_source_used']}",
        f"comparison reference status: {summary['comparison_reference_status']}",
        f"Calmar wins vs preferred QQQ100 reference: {summary['calmar_win_count_vs_generated_qqq100']}",
        f"Sharpe wins vs preferred QQQ100 reference: {summary['sharpe_win_count_vs_generated_qqq100']}",
        f"worst split by Calmar: {summary['worst_split_by_calmar']}",
        f"worst split by MaxDD: {summary['worst_split_by_maxdd']}",
        f"key blockers: {summary['key_blockers']}",
        f"required next step: {summary['required_next_step']}",
        f"Saved report: {output_path}",
        "execution_approved=false; scheduling_approved=false",
    ]


def summary_dict(rows: list[dict[str, str]]) -> dict[str, str]:
    return {row.get("summary_name", ""): row.get("summary_value", "") for row in rows}


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


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
