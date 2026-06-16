"""Research-only QQQ100 stream reconciliation checkpoint.

This report compares the generated QQQ100 sleeve return stream with the saved
QQQ100 benchmark metrics and tests a small set of plausible stream-construction
variants. It does not call Alpaca, read live positions, create orders, write
SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research.multi_sleeve_portfolio_backtest import (
    INPUT_FILES as MULTI_SLEEVE_INPUT_FILES,
    MISSING,
    QQQ100_REFERENCE,
    metric_delta,
    portfolio_metrics_from_streams,
    qqq100_metric_bundle,
    read_csv_rows,
)
from trading_bot.research.sleeve_return_streams import (
    PRICE_FIXTURE,
    QQQ100_SLEEVE,
    QQQ100_STRATEGY,
    above_sma,
    daily_return,
    load_research_price_series,
)


FINAL_STATUS = "qqq100_stream_reconciliation_needs_manual_review"
BEST_CANDIDATE_FALLBACK = "qqq100_stream_saved_benchmark_like_best_candidate"
QQQ100_STRATEGY_IDENTITY = "qqq_100_trend_gate"
BIGGEST_BLOCKER = "missing_original_benchmark_source_data_and_exact_backtest_parameters"
RECOMMENDED_NEXT_STEP = "document_original_qqq100_backtest_inputs_before_updating_stream_generation"

OUTPUT_FILES = {
    "report": Path("data/qqq100_stream_reconciliation.csv"),
    "candidates": Path("data/qqq100_stream_reconciliation_candidates.csv"),
    "diagnostics": Path("data/qqq100_stream_reconciliation_diagnostics.csv"),
    "blockers": Path("data/qqq100_stream_reconciliation_blockers.csv"),
    "summary": Path("data/qqq100_stream_reconciliation_summary.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "report_only",
    "reconciliation_only",
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
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "reconciliation_only": True,
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
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

REPORT_COLUMNS = [
    "created_at",
    "final_reconciliation_status",
    "saved_benchmark_source",
    "saved_benchmark_cagr",
    "saved_benchmark_sharpe",
    "saved_benchmark_max_drawdown",
    "saved_benchmark_calmar",
    "current_generated_source",
    "current_generated_cagr",
    "current_generated_sharpe",
    "current_generated_max_drawdown",
    "current_generated_calmar",
    "best_aligned_candidate",
    "best_candidate_cagr",
    "best_candidate_sharpe",
    "best_candidate_max_drawdown",
    "best_candidate_calmar",
    "delta_cagr_vs_saved_benchmark",
    "delta_sharpe_vs_saved_benchmark",
    "delta_max_drawdown_vs_saved_benchmark",
    "delta_calmar_vs_saved_benchmark",
    "reconciliation_distance_score",
    "likely_mismatch_cause",
    "sleeve_return_streams_updated",
    "biggest_blocker",
    "recommended_next_step",
    *SAFETY_COLUMNS,
]

CANDIDATE_COLUMNS = [
    "created_at",
    "candidate_name",
    "price_basis",
    "signal_shift_rows",
    "sma_window",
    "min_periods",
    "execution_timing",
    "start_date",
    "end_date",
    "row_count",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "annual_volatility",
    "cash_percentage",
    "trade_signal_change_count",
    "delta_CAGR_vs_saved_benchmark",
    "delta_Sharpe_vs_saved_benchmark",
    "delta_MaxDD_vs_saved_benchmark",
    "delta_Calmar_vs_saved_benchmark",
    "reconciliation_distance_score",
    "reconciliation_status",
    "mismatch_reason",
    *SAFETY_COLUMNS,
]

DIAGNOSTIC_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "evidence",
    "likely_mismatch_cause",
    "required_next_step",
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
class QQQ100StreamReconciliationResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    candidate_rows: list[dict[str, Any]]
    diagnostic_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_stream_reconciliation(root_dir: Path | str = ".") -> QQQ100StreamReconciliationResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    saved_metrics = saved_qqq100_metrics(root)
    current_metrics = portfolio_metrics_from_streams(QQQ100_REFERENCE, read_csv_rows(root / "data/sleeve_return_streams.csv")) or missing_metrics()
    price_rows, price_source, price_basis_status = load_qqq_price_rows(root)
    candidate_rows = build_candidate_rows(created_at, price_rows, saved_metrics, price_basis_status)
    best_candidate = choose_best_candidate(candidate_rows)
    diagnostic_rows = build_diagnostic_rows(created_at, saved_metrics, current_metrics, candidate_rows, price_source, price_basis_status)
    blocker_rows = build_blocker_rows(created_at, diagnostic_rows)
    report_rows = build_report_rows(created_at, saved_metrics, current_metrics, best_candidate, diagnostic_rows)
    summary_rows = build_summary_rows(created_at, report_rows[0], saved_metrics, current_metrics, best_candidate)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["candidates"], CANDIDATE_COLUMNS, candidate_rows)
    write_rows(output_paths["diagnostics"], DIAGNOSTIC_COLUMNS, diagnostic_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    return QQQ100StreamReconciliationResult(
        output_paths=output_paths,
        report_rows=report_rows,
        candidate_rows=candidate_rows,
        diagnostic_rows=diagnostic_rows,
        blocker_rows=blocker_rows,
        summary_rows=summary_rows,
        summary_lines=summary_lines(summary_rows, output_paths["summary"]),
    )


def show_qqq100_stream_reconciliation(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "QQQ100 stream reconciliation report is missing.",
            "Run `python bot.py --qqq100-stream-reconciliation` first.",
            "execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
        ]
    summary = {row.get("summary_name", ""): row.get("summary_value", "") for row in read_csv_rows(path)}
    return 0, [
        "QQQ100 stream reconciliation. Research/report-only; no execution wiring approved.",
        f"final_reconciliation_status: {summary.get('final_reconciliation_status', 'missing')}",
        f"saved QQQ100 benchmark metrics: {summary.get('saved_qqq100_benchmark_metrics', 'missing')}",
        f"current generated QQQ100 stream metrics: {summary.get('current_generated_qqq100_stream_metrics', 'missing')}",
        f"best aligned candidate: {summary.get('best_aligned_candidate', 'missing')}",
        f"best aligned candidate metrics: {summary.get('best_aligned_candidate_metrics', 'missing')}",
        f"deltas vs saved benchmark: {summary.get('deltas_vs_saved_benchmark', 'missing')}",
        f"likely mismatch cause: {summary.get('likely_mismatch_cause', 'missing')}",
        f"sleeve_return_streams updated: {summary.get('sleeve_return_streams_updated', 'false')}",
        f"biggest blocker: {summary.get('biggest_blocker', BIGGEST_BLOCKER)}",
        f"recommended next step: {summary.get('recommended_next_step', RECOMMENDED_NEXT_STEP)}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; general_execution_approved=false; qqq100_execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def saved_qqq100_metrics(root: Path) -> dict[str, str]:
    inputs = {name: read_csv_rows(root / path) for name, path in MULTI_SLEEVE_INPUT_FILES.items()}
    return qqq100_metric_bundle(inputs)


def load_qqq_price_rows(root: Path) -> tuple[list[dict[str, Any]], str, str]:
    fixture = root / PRICE_FIXTURE
    if fixture.exists():
        rows = []
        has_adjusted = False
        for row in read_csv_rows(fixture):
            if str(row.get("ticker", "")).upper() != "QQQ":
                continue
            close = parse_float(row.get("close"))
            adjusted = row.get("adj_close") or row.get("adjusted_close")
            has_adjusted = has_adjusted or bool(adjusted)
            rows.append({"date": row.get("date", ""), "close": close, "adj_close": parse_float(adjusted) if adjusted else close})
        rows.sort(key=lambda item: str(item["date"]))
        return rows, "saved_price_fixture", "close_and_adjusted_close_available" if has_adjusted else "close_only_adjusted_close_unavailable"
    prices, source, _errors = load_research_price_series(root)
    rows = [dict(row, adj_close=row.get("close")) for row in prices.get("QQQ", [])]
    return rows, source, "auto_adjusted_close_only_adjusted_close_unavailable"


def build_candidate_rows(
    created_at: str,
    price_rows: list[dict[str, Any]],
    saved_metrics: dict[str, str],
    price_basis_status: str,
) -> list[dict[str, Any]]:
    specs = [
        ("qqq100_stream_close_shift0", "close", 0, 100, 100, "same_day_signal_reference"),
        ("qqq100_stream_close_shift1", "close", 1, 100, 100, "next_day_signal_reference"),
        ("qqq100_stream_adjclose_shift0", "adj_close", 0, 100, 100, "same_day_signal_reference"),
        ("qqq100_stream_adjclose_shift1", "adj_close", 1, 100, 100, "next_day_signal_reference"),
        ("qqq100_stream_min_periods_100_shift1", "close", 1, 100, 100, "next_day_signal_reference"),
    ]
    rows = [
        candidate_row_from_spec(created_at, price_rows, saved_metrics, price_basis_status, *spec)
        for spec in specs
    ]
    best = choose_best_candidate(rows)
    if best:
        clone = dict(best)
        clone["candidate_name"] = BEST_CANDIDATE_FALLBACK
        rows.append(clone)
    else:
        rows.append(data_unavailable_candidate(created_at, BEST_CANDIDATE_FALLBACK, "data_unavailable", saved_metrics))
    return rows


def candidate_row_from_spec(
    created_at: str,
    price_rows: list[dict[str, Any]],
    saved_metrics: dict[str, str],
    price_basis_status: str,
    candidate_name: str,
    price_basis: str,
    signal_shift_rows: int,
    sma_window: int,
    min_periods: int,
    timing: str,
) -> dict[str, Any]:
    if not price_rows or len(price_rows) <= sma_window:
        return data_unavailable_candidate(created_at, candidate_name, "data_unavailable", saved_metrics)
    if price_basis == "adj_close" and "adjusted_close_unavailable" in price_basis_status:
        return data_unavailable_candidate(created_at, candidate_name, "data_unavailable", saved_metrics, price_basis=price_basis)
    streams = build_candidate_stream(price_rows, price_basis, signal_shift_rows, sma_window, min_periods)
    if len(streams) < 2:
        return data_unavailable_candidate(created_at, candidate_name, "data_unavailable", saved_metrics, price_basis=price_basis)
    metrics = metrics_for_returns([row["daily_strategy_return"] for row in streams], [row["cash_weight"] for row in streams])
    deltas = candidate_deltas(metrics, saved_metrics)
    distance = reconciliation_distance(deltas)
    status = reconciliation_status(distance)
    mismatch = mismatch_reason(status, price_basis_status)
    return {
        "created_at": created_at,
        "candidate_name": candidate_name,
        "price_basis": price_basis,
        "signal_shift_rows": signal_shift_rows,
        "sma_window": sma_window,
        "min_periods": min_periods,
        "execution_timing": timing,
        "start_date": streams[0]["date"],
        "end_date": streams[-1]["date"],
        "row_count": len(streams),
        "cagr": metrics["cagr"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
        "calmar": metrics["calmar"],
        "annual_volatility": metrics["annual_volatility"],
        "cash_percentage": metrics["cash_percentage"],
        "trade_signal_change_count": signal_changes(streams),
        "delta_CAGR_vs_saved_benchmark": deltas["cagr"],
        "delta_Sharpe_vs_saved_benchmark": deltas["sharpe"],
        "delta_MaxDD_vs_saved_benchmark": deltas["max_drawdown"],
        "delta_Calmar_vs_saved_benchmark": deltas["calmar"],
        "reconciliation_distance_score": distance,
        "reconciliation_status": status,
        "mismatch_reason": mismatch,
        **safety_flags(),
    }


def build_candidate_stream(
    price_rows: list[dict[str, Any]],
    price_basis: str,
    signal_shift_rows: int,
    sma_window: int,
    min_periods: int,
) -> list[dict[str, Any]]:
    normalized = [{"date": row["date"], "close": float(row[price_basis])} for row in price_rows if row.get(price_basis) not in {"", None}]
    rows = []
    for index in range(1, len(normalized)):
        signal_index = index - signal_shift_rows
        exposure = 1.0 if signal_index >= 0 and above_sma_with_min_periods(normalized, signal_index, sma_window, min_periods) else 0.0
        asset_return = daily_return(normalized, index)
        rows.append(
            {
                "date": normalized[index]["date"],
                "daily_strategy_return": asset_return * exposure,
                "signal_state": "long" if exposure else "flat",
                "cash_weight": 1.0 - exposure,
            }
        )
    return rows


def above_sma_with_min_periods(rows: list[dict[str, Any]], index: int, window: int, min_periods: int) -> bool:
    if index < min_periods - 1:
        return False
    start = max(0, index - window + 1)
    values = [float(row["close"]) for row in rows[start : index + 1]]
    if len(values) < min_periods:
        return False
    return float(rows[index]["close"]) > sum(values) / len(values)


def data_unavailable_candidate(
    created_at: str,
    candidate_name: str,
    status: str,
    saved_metrics: dict[str, str],
    price_basis: str = "missing_saved_data",
) -> dict[str, Any]:
    deltas = {"cagr": MISSING, "sharpe": MISSING, "max_drawdown": MISSING, "calmar": MISSING}
    return {
        "created_at": created_at,
        "candidate_name": candidate_name,
        "price_basis": price_basis,
        "signal_shift_rows": MISSING,
        "sma_window": "100",
        "min_periods": "100",
        "execution_timing": "data_unavailable",
        "start_date": "",
        "end_date": "",
        "row_count": 0,
        "cagr": MISSING,
        "sharpe": MISSING,
        "max_drawdown": MISSING,
        "calmar": MISSING,
        "annual_volatility": MISSING,
        "cash_percentage": MISSING,
        "trade_signal_change_count": MISSING,
        "delta_CAGR_vs_saved_benchmark": deltas["cagr"],
        "delta_Sharpe_vs_saved_benchmark": deltas["sharpe"],
        "delta_MaxDD_vs_saved_benchmark": deltas["max_drawdown"],
        "delta_Calmar_vs_saved_benchmark": deltas["calmar"],
        "reconciliation_distance_score": MISSING,
        "reconciliation_status": status,
        "mismatch_reason": "missing_saved_data_or_adjusted_close_unavailable",
        **safety_flags(),
    }


def choose_best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [row for row in rows if row.get("reconciliation_distance_score") not in {"", MISSING, None}]
    if not candidates:
        return None
    return min(candidates, key=lambda row: parse_float(row["reconciliation_distance_score"]))


def build_diagnostic_rows(
    created_at: str,
    saved_metrics: dict[str, str],
    current_metrics: dict[str, str],
    candidates: list[dict[str, Any]],
    price_source: str,
    price_basis_status: str,
) -> list[dict[str, Any]]:
    best = choose_best_candidate(candidates)
    current_deltas = candidate_deltas(current_metrics, saved_metrics)
    diagnostics = [
        ("saved_benchmark_metrics", "available" if not metrics_missing(saved_metrics) else "missing_saved_metrics", format_metrics(saved_metrics), "none" if not metrics_missing(saved_metrics) else "missing_original_benchmark_source_data", "Keep exact QQQ100 benchmark source labelled."),
        ("current_generated_stream_metrics", "available" if not metrics_missing(current_metrics) else "missing_saved_stream", format_metrics(current_metrics), "current_generated_stream_differs_from_saved_benchmark", "Use reconciliation candidate rows before changing labels."),
        ("current_generated_delta_vs_saved", "warning", format_deltas(current_deltas), "generated_stream_metrics_do_not_match_saved_benchmark", "Do not compare generated candidates against saved benchmark as if identical."),
        ("price_basis", price_basis_status, f"price_source={price_source}", "price_adjustment_or_dividend_split_treatment_unknown" if "adjusted_close_unavailable" in price_basis_status else "price_basis_tested", "Obtain exact benchmark price basis before replacing stream config."),
        ("signal_timing", "tested", "shift0 and shift1 variants tested where data exists", "signal_timing_mismatch_possible", "Retain best candidate as research-only unless close match is confirmed."),
        ("sma_window_threshold", "tested", "SMA100 with min_periods=100 tested", "warmup_or_threshold_mismatch_possible", "Document original warmup and threshold rules."),
        ("date_range", "warning", f"best_candidate_range={best.get('start_date', 'missing') if best else 'missing'} to {best.get('end_date', 'missing') if best else 'missing'}", "date_range_mismatch_possible", "Recover original benchmark start/end dates."),
        ("cash_flat_handling", "tested", "flat return equals 0; exposure equals 1 long and 0 flat", "cash_or_risk_free_assumption_unknown", "Confirm whether saved benchmark used cash/risk-free returns."),
        ("cost_slippage_assumptions", "warning", "missing_cost_assumption", "cost_or_slippage_assumption_unknown", "Confirm whether saved benchmark is gross or net of costs."),
        ("trade_construction", "passed", "long-only; no shorting; no leverage; no duplicate exposure", "none", "Keep construction research-only and execution approvals false."),
    ]
    return [
        {
            "created_at": created_at,
            "check_name": name,
            "check_status": status,
            "evidence": evidence,
            "likely_mismatch_cause": cause,
            "required_next_step": next_step,
            **safety_flags(),
        }
        for name, status, evidence, cause, next_step in diagnostics
    ]


def build_blocker_rows(created_at: str, diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = [
        (BIGGEST_BLOCKER, "blocked", "high", "The exact source data and parameters for the saved QQQ100 benchmark are not available in this checkpoint.", RECOMMENDED_NEXT_STEP),
        ("missing_cost_assumption", "blocked", "medium", "The reconciliation cannot tell whether the saved benchmark is gross or net of costs.", "Document saved benchmark cost/slippage assumptions."),
        ("price_adjustment_assumption_not_proven", "blocked", "medium", "Adjusted-close/dividend/split treatment cannot be proven unless exact source data is present.", "Preserve saved/generated metric separation."),
        ("execution_wiring_blocked", "blocked", "critical", "Reconciliation outputs are research-only and cannot approve orders or repeat execution.", "Keep execution approvals false."),
        ("scheduling_not_approved", "blocked", "critical", "No scheduling, Hermes cron, loop, service, or Task Scheduler use is approved.", "Keep this report manual/research-only."),
    ]
    return [
        {
            "created_at": created_at,
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **safety_flags(),
        }
        for name, status, severity, details, next_step in blockers
    ]


def build_report_rows(
    created_at: str,
    saved_metrics: dict[str, str],
    current_metrics: dict[str, str],
    best_candidate: dict[str, Any] | None,
    diagnostics: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    best = best_candidate or data_unavailable_candidate(created_at, "none", "cannot_reconcile_from_saved_inputs", saved_metrics)
    return [
        {
            "created_at": created_at,
            "final_reconciliation_status": final_status_for(best),
            "saved_benchmark_source": saved_metrics.get("baseline_source", MISSING),
            "saved_benchmark_cagr": saved_metrics["cagr"],
            "saved_benchmark_sharpe": saved_metrics["sharpe"],
            "saved_benchmark_max_drawdown": saved_metrics["max_drawdown"],
            "saved_benchmark_calmar": saved_metrics["calmar"],
            "current_generated_source": "data/sleeve_return_streams.csv",
            "current_generated_cagr": current_metrics["cagr"],
            "current_generated_sharpe": current_metrics["sharpe"],
            "current_generated_max_drawdown": current_metrics["max_drawdown"],
            "current_generated_calmar": current_metrics["calmar"],
            "best_aligned_candidate": best["candidate_name"],
            "best_candidate_cagr": best["cagr"],
            "best_candidate_sharpe": best["sharpe"],
            "best_candidate_max_drawdown": best["max_drawdown"],
            "best_candidate_calmar": best["calmar"],
            "delta_cagr_vs_saved_benchmark": best["delta_CAGR_vs_saved_benchmark"],
            "delta_sharpe_vs_saved_benchmark": best["delta_Sharpe_vs_saved_benchmark"],
            "delta_max_drawdown_vs_saved_benchmark": best["delta_MaxDD_vs_saved_benchmark"],
            "delta_calmar_vs_saved_benchmark": best["delta_Calmar_vs_saved_benchmark"],
            "reconciliation_distance_score": best["reconciliation_distance_score"],
            "likely_mismatch_cause": likely_mismatch_cause(diagnostics, best),
            "sleeve_return_streams_updated": False,
            "biggest_blocker": BIGGEST_BLOCKER,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
            **safety_flags(),
        }
    ]


def build_summary_rows(
    created_at: str,
    report: dict[str, Any],
    saved_metrics: dict[str, str],
    current_metrics: dict[str, str],
    best_candidate: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    best = best_candidate or {}
    items = [
        ("final_reconciliation_status", report["final_reconciliation_status"], "The reconciliation report does not approve execution or scheduling."),
        ("saved_qqq100_benchmark_metrics", format_metrics(saved_metrics), "Saved QQQ100 benchmark metrics remain the benchmark reference."),
        ("current_generated_qqq100_stream_metrics", format_metrics(current_metrics), "Current generated stream metrics from data/sleeve_return_streams.csv."),
        ("best_aligned_candidate", best.get("candidate_name", "none"), "Best candidate by reconciliation distance score."),
        ("best_aligned_candidate_metrics", format_candidate_metrics(best), "Candidate metrics remain research-only."),
        ("deltas_vs_saved_benchmark", format_candidate_deltas(best), "Deltas are against the saved QQQ100 benchmark."),
        ("likely_mismatch_cause", report["likely_mismatch_cause"], "Likely causes are labelled rather than forced into a match."),
        ("sleeve_return_streams_updated", "false", "The generator remains unchanged until exact source assumptions are confirmed."),
        ("biggest_blocker", BIGGEST_BLOCKER, "Exact original benchmark source data and assumptions are missing."),
        ("recommended_next_step", RECOMMENDED_NEXT_STEP, "Resolve benchmark source/date/cost/cash assumptions before candidate label changes."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def final_status_for(best: dict[str, Any]) -> str:
    status = str(best.get("reconciliation_status", ""))
    if status == "exact_or_close_match":
        return "qqq100_stream_reconciliation_close_match_found_manual_review_required"
    if status == "improved_but_still_mismatch":
        return "qqq100_stream_reconciliation_improved_but_still_mismatch"
    if status == "data_unavailable":
        return "qqq100_stream_reconciliation_data_unavailable"
    if status == "cannot_reconcile_from_saved_inputs":
        return "qqq100_stream_reconciliation_cannot_reconcile_from_saved_inputs"
    return FINAL_STATUS


def likely_mismatch_cause(diagnostics: list[dict[str, Any]], best: dict[str, Any]) -> str:
    if best.get("reconciliation_status") == "exact_or_close_match":
        return "candidate_close_to_saved_benchmark_manual_review_required"
    causes = [
        row["likely_mismatch_cause"]
        for row in diagnostics
        if row["likely_mismatch_cause"] not in {"none", "price_basis_tested"}
    ]
    return "; ".join(causes[:4]) if causes else "approximate_or_needs_reconciliation"


def metrics_for_returns(returns: list[float], cash_weights: list[float]) -> dict[str, str]:
    if len(returns) < 2:
        return missing_metrics()
    equity = 1.0
    curve = []
    for value in returns:
        equity *= 1.0 + value
        curve.append(equity)
    years = max(len(returns) / 252.0, 1 / 252.0)
    cagr = (equity ** (1.0 / years) - 1.0) * 100.0
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / max(1, len(returns) - 1)
    annual_vol = math.sqrt(variance) * math.sqrt(252.0) * 100.0
    sharpe = mean / math.sqrt(variance) * math.sqrt(252.0) if variance > 0 else 0.0
    maxdd = max_drawdown_pct(curve)
    calmar = cagr / abs(maxdd) if maxdd < 0 else 0.0
    cash = sum(cash_weights) / len(cash_weights) * 100.0
    return {
        "cagr": str(round(cagr, 4)),
        "sharpe": str(round(sharpe, 4)),
        "max_drawdown": str(round(maxdd, 4)),
        "calmar": str(round(calmar, 4)),
        "annual_volatility": str(round(annual_vol, 4)),
        "cash_percentage": str(round(cash, 4)),
    }


def candidate_deltas(metrics: dict[str, str], saved_metrics: dict[str, str]) -> dict[str, str]:
    return {
        "cagr": metric_delta(metrics["cagr"], saved_metrics["cagr"]),
        "sharpe": metric_delta(metrics["sharpe"], saved_metrics["sharpe"]),
        "max_drawdown": metric_delta(metrics["max_drawdown"], saved_metrics["max_drawdown"]),
        "calmar": metric_delta(metrics["calmar"], saved_metrics["calmar"]),
    }


def reconciliation_distance(deltas: dict[str, str]) -> str:
    try:
        score = (
            abs(float(deltas["cagr"])) / 5.0
            + abs(float(deltas["sharpe"])) / 0.5
            + abs(float(deltas["max_drawdown"])) / 5.0
            + abs(float(deltas["calmar"])) / 0.5
        )
    except (TypeError, ValueError):
        return MISSING
    return str(round(score, 4))


def reconciliation_status(distance_text: str) -> str:
    distance = parse_float(distance_text)
    if distance == float("inf"):
        return "cannot_reconcile_from_saved_inputs"
    if distance <= 0.25:
        return "exact_or_close_match"
    if distance <= 1.0:
        return "improved_but_still_mismatch"
    return "approximate_or_needs_reconciliation"


def mismatch_reason(status: str, price_basis_status: str) -> str:
    if status == "exact_or_close_match":
        return "candidate_close_to_saved_benchmark_manual_review_required"
    if "adjusted_close_unavailable" in price_basis_status:
        return "price_adjustment_or_dividend_split_treatment_unknown"
    if status == "improved_but_still_mismatch":
        return "date_range_cost_cash_or_signal_timing_mismatch_possible"
    return "missing_original_benchmark_source_data_or_exact_parameters"


def max_drawdown_pct(curve: list[float]) -> float:
    peak = curve[0]
    worst = 0.0
    for value in curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value / peak - 1.0) * 100.0)
    return worst


def signal_changes(rows: list[dict[str, Any]]) -> int:
    changes = 0
    previous = None
    for row in rows:
        state = row.get("signal_state")
        if previous is not None and state != previous:
            changes += 1
        previous = state
    return changes


def metrics_missing(metrics: dict[str, str]) -> bool:
    return any(metrics.get(key, MISSING) == MISSING for key in ["cagr", "sharpe", "max_drawdown", "calmar"])


def missing_metrics() -> dict[str, str]:
    return {
        "cagr": MISSING,
        "sharpe": MISSING,
        "max_drawdown": MISSING,
        "calmar": MISSING,
        "annual_volatility": MISSING,
        "cash_percentage": MISSING,
        "baseline_source": "missing_saved_metrics",
    }


def format_metrics(metrics: dict[str, str]) -> str:
    return f"CAGR={metrics.get('cagr', MISSING)}; Sharpe={metrics.get('sharpe', MISSING)}; MaxDD={metrics.get('max_drawdown', MISSING)}; Calmar={metrics.get('calmar', MISSING)}"


def format_candidate_metrics(row: dict[str, Any]) -> str:
    if not row:
        return "missing"
    return f"CAGR={row.get('cagr', MISSING)}; Sharpe={row.get('sharpe', MISSING)}; MaxDD={row.get('max_drawdown', MISSING)}; Calmar={row.get('calmar', MISSING)}"


def format_candidate_deltas(row: dict[str, Any]) -> str:
    if not row:
        return "missing"
    return f"delta_CAGR={row.get('delta_CAGR_vs_saved_benchmark', MISSING)}; delta_Sharpe={row.get('delta_Sharpe_vs_saved_benchmark', MISSING)}; delta_MaxDD={row.get('delta_MaxDD_vs_saved_benchmark', MISSING)}; delta_Calmar={row.get('delta_Calmar_vs_saved_benchmark', MISSING)}"


def format_deltas(deltas: dict[str, str]) -> str:
    return f"delta_CAGR={deltas['cagr']}; delta_Sharpe={deltas['sharpe']}; delta_MaxDD={deltas['max_drawdown']}; delta_Calmar={deltas['calmar']}"


def summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "QQQ100 stream reconciliation created. Research-only; no execution wiring approved.",
        f"final_reconciliation_status: {summary['final_reconciliation_status']}",
        f"saved QQQ100 benchmark metrics: {summary['saved_qqq100_benchmark_metrics']}",
        f"current generated QQQ100 stream metrics: {summary['current_generated_qqq100_stream_metrics']}",
        f"best aligned candidate: {summary['best_aligned_candidate']}",
        f"best aligned candidate metrics: {summary['best_aligned_candidate_metrics']}",
        f"deltas vs saved benchmark: {summary['deltas_vs_saved_benchmark']}",
        f"likely mismatch cause: {summary['likely_mismatch_cause']}",
        f"sleeve_return_streams updated: {summary['sleeve_return_streams_updated']}",
        f"biggest blocker: {summary['biggest_blocker']}",
        f"recommended next step: {summary['recommended_next_step']}",
        f"Saved summary: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; general_execution_approved=false; qqq100_execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("inf")


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
