"""Saved-output-only high-growth drawdown decomposition for the multi-sleeve lead."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import multi_sleeve_portfolio_backtest as backtest


MISSING = "missing_saved_output"

RECOVERED_REFERENCE = backtest.RECOVERED_QQQ100_REFERENCE
HIGH_GROWTH_SLEEVE = "codex_broad_growth_balanced_breakout_control"
CRYPTO_SLEEVE = "crypto_btc_eth_research_sleeve"
CURRENT_ALLOCATION = ("current_75_15_5_5", 75.0, 15.0, 5.0, 5.0)
HIGHER_GROWTH_ALLOCATION = ("higher_growth_70_20_5_5", 70.0, 20.0, 5.0, 5.0)

STATUS_ACCEPTABLE = "high_growth_drawdown_acceptable_for_research_lead"
STATUS_WATCH = "high_growth_drawdown_watch_manual_review_required"
STATUS_TOO_SENSITIVE = "high_growth_drawdown_too_sensitive_keep_as_challenger"
STATUS_BLOCKED_MISSING = "high_growth_drawdown_decomposition_blocked_missing_saved_streams"

NEXT_MANUAL_REVIEW = "manual_review_high_growth_drawdown_watch_before_execution_or_preview_discussion"
NEXT_MISSING = "refresh_saved_lead_state_and_return_streams_before_drawdown_decomposition"
NEXT_CHALLENGER = "keep_higher_growth_as_challenger_until_drawdown_sensitivity_review"

INPUT_FILES = {
    "lead_state": Path("data/multi_sleeve_lead_state.csv"),
    "research_lead_decision": Path("data/multi_sleeve_research_lead_decision.csv"),
    "higher_growth_drawdown": Path("data/multi_sleeve_higher_growth_drawdown_review.csv"),
    "higher_growth_review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "higher_growth_split": Path("data/multi_sleeve_higher_growth_split_review.csv"),
    "weight_sensitivity": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "qqq100_stream": Path("data/qqq100_recovered_reference_stream.csv"),
    "high_growth_stream": Path("data/high_growth_return_streams.csv"),
    "crypto_stream": Path("data/crypto_return_streams.csv"),
    "portfolio_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
}

OUTPUT_FILES = {
    "decomposition": Path("data/multi_sleeve_high_growth_drawdown_decomposition.csv"),
    "summary": Path("data/multi_sleeve_high_growth_drawdown_summary.csv"),
    "periods": Path("data/multi_sleeve_high_growth_drawdown_periods.csv"),
    "blockers": Path("data/multi_sleeve_high_growth_drawdown_blockers.csv"),
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
    "yfinance_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]

DECOMPOSITION_COLUMNS = [
    "created_at",
    "row_type",
    "period_start",
    "period_trough",
    "allocation_name",
    "qqq100_weight",
    "high_growth_weight",
    "crypto_weight",
    "defensive_weight",
    "qqq100_period_return",
    "high_growth_period_return",
    "crypto_period_return",
    "defensive_period_return",
    "qqq100_weighted_contribution",
    "high_growth_weighted_contribution",
    "crypto_weighted_contribution",
    "defensive_weighted_contribution",
    "total_period_return",
    "delta_high_growth_weight",
    "delta_qqq100_weight",
    "delta_crypto_weight",
    "delta_defensive_weight",
    "incremental_high_growth_contribution",
    "reduced_qqq100_contribution",
    "net_incremental_drawdown_effect",
    "main_incremental_drawdown_contributor",
    "incremental_drawdown_status",
    "contribution_status",
    "attribution_confidence",
    *SAFETY_COLUMNS,
]

PERIOD_COLUMNS = [
    "created_at",
    "allocation_name",
    "worst_drawdown_start",
    "worst_drawdown_trough",
    "worst_drawdown_percent",
    "recovery_date",
    "recovery_rows",
    "recovery_days",
    "drawdown_period_status",
    "post_trough_63d_return",
    "post_trough_126d_return",
    "bounce_back_status",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = ["created_at", "summary_name", "summary_value", "details", *SAFETY_COLUMNS]
BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "blocker_severity",
    "blocker_detail",
    "required_next_step",
    "execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
]


@dataclass
class HighGrowthDrawdownResult:
    output_paths: dict[str, Path]
    decomposition_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    period_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_high_growth_drawdown_decomposition(root_dir: Path | str = ".") -> HighGrowthDrawdownResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    streams = (
        backtest.normalize_recovered_reference_stream_rows(inputs["qqq100_stream"])
        + backtest.normalize_high_growth_stream_rows(inputs["high_growth_stream"])
        + backtest.normalize_crypto_stream_rows(inputs["crypto_stream"])
    )
    by_candidate = backtest.stream_returns_by_candidate(streams)
    missing = missing_inputs(inputs, by_candidate)
    if missing:
        period_rows = blocked_period_rows(created_at, missing)
        decomposition_rows = blocked_decomposition_rows(created_at, missing)
        final_status = STATUS_BLOCKED_MISSING
    else:
        dates = common_dates(by_candidate)
        current_returns = allocation_returns(dates, by_candidate, CURRENT_ALLOCATION)
        higher_returns = allocation_returns(dates, by_candidate, HIGHER_GROWTH_ALLOCATION)
        current_window = drawdown_window(dates, current_returns)
        higher_window = drawdown_window(dates, higher_returns)
        period_rows = build_period_rows(created_at, dates, current_returns, higher_returns, current_window, higher_window)
        decomposition_rows = build_decomposition_rows(created_at, dates, by_candidate, higher_window)
        final_status = final_drawdown_status(current_window, higher_window)
    summary_rows = build_summary_rows(created_at, final_status, period_rows, decomposition_rows, missing)
    blocker_rows = build_blocker_rows(created_at, final_status, missing, summary_map(summary_rows))
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decomposition"], DECOMPOSITION_COLUMNS, decomposition_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["periods"], PERIOD_COLUMNS, period_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthDrawdownResult(
        output_paths=output_paths,
        decomposition_rows=decomposition_rows,
        summary_rows=summary_rows,
        period_rows=period_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["decomposition"]),
    )


def show_multi_sleeve_high_growth_drawdown_decomposition(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve high-growth drawdown decomposition is missing.",
            "Run `python bot.py --multi-sleeve-high-growth-drawdown-decomposition` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "Multi-sleeve high-growth drawdown decomposition. Saved-output-only research; no execution path.",
        f"final drawdown decomposition status: {summary.get('final_drawdown_decomposition_status', MISSING)}",
        f"selected lead candidate: {summary.get('selected_lead_candidate', MISSING)}",
        f"previous baseline: {summary.get('previous_baseline', MISSING)}",
        f"candidate worst drawdown period: {summary.get('candidate_worst_drawdown_period', MISSING)}",
        f"baseline worst drawdown period: {summary.get('baseline_worst_drawdown_period', MISSING)}",
        f"drawdown delta: {summary.get('drawdown_delta', MISSING)}",
        f"main incremental drawdown contributor: {summary.get('main_incremental_drawdown_contributor', MISSING)}",
        f"high-growth contribution during worst period: {summary.get('high_growth_contribution_during_worst_period', MISSING)}",
        f"QQQ100 contribution change: {summary.get('qqq100_contribution_change', MISSING)}",
        f"crypto contribution during worst period: {summary.get('crypto_contribution_during_worst_period', MISSING)}",
        f"recovery/bounce-back summary: {summary.get('recovery_bounce_back_summary', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def missing_inputs(inputs: dict[str, list[dict[str, str]]], by_candidate: dict[str, dict[str, float]]) -> list[str]:
    missing = []
    if not inputs["lead_state"]:
        missing.append("multi_sleeve_lead_state")
    if not inputs["research_lead_decision"]:
        missing.append("multi_sleeve_research_lead_decision")
    for name in [RECOVERED_REFERENCE, HIGH_GROWTH_SLEEVE, CRYPTO_SLEEVE]:
        if name not in by_candidate:
            missing.append(name)
    return missing


def common_dates(by_candidate: dict[str, dict[str, float]]) -> list[str]:
    return sorted(set(by_candidate[RECOVERED_REFERENCE]) & set(by_candidate[HIGH_GROWTH_SLEEVE]) & set(by_candidate[CRYPTO_SLEEVE]))


def allocation_returns(dates: list[str], by_candidate: dict[str, dict[str, float]], allocation: tuple[str, float, float, float, float]) -> list[float]:
    _name, qqq, high_growth, crypto, _defensive = allocation
    return [
        by_candidate[RECOVERED_REFERENCE][date] * qqq / 100.0
        + by_candidate[HIGH_GROWTH_SLEEVE][date] * high_growth / 100.0
        + by_candidate[CRYPTO_SLEEVE][date] * crypto / 100.0
        for date in dates
    ]


def drawdown_window(dates: list[str], returns: list[float]) -> dict[str, Any]:
    equity = 1.0
    peak = 1.0
    peak_index = 0
    curve: list[float] = []
    worst = {
        "start": dates[0] if dates else "",
        "trough": dates[0] if dates else "",
        "maxdd": 0.0,
        "start_index": 0,
        "trough_index": 0,
        "peak": 1.0,
        "recovery": "unrecovered_or_not_available",
        "recovery_index": None,
    }
    for index, value in enumerate(returns):
        equity *= 1 + value
        curve.append(equity)
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = (equity / peak - 1.0) * 100.0 if peak else 0.0
        if drawdown < worst["maxdd"]:
            worst = {
                "start": dates[peak_index],
                "trough": dates[index],
                "maxdd": drawdown,
                "start_index": peak_index,
                "trough_index": index,
                "peak": peak,
                "recovery": "unrecovered_or_not_available",
                "recovery_index": None,
            }
    for index in range(int(worst["trough_index"]) + 1, len(curve)):
        if curve[index] >= float(worst["peak"]):
            worst["recovery"] = dates[index]
            worst["recovery_index"] = index
            break
    return worst


def build_period_rows(
    created_at: str,
    dates: list[str],
    current_returns: list[float],
    higher_returns: list[float],
    current_window: dict[str, Any],
    higher_window: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        period_row(created_at, CURRENT_ALLOCATION[0], dates, current_returns, current_window),
        period_row(created_at, HIGHER_GROWTH_ALLOCATION[0], dates, higher_returns, higher_window),
    ]


def period_row(created_at: str, name: str, dates: list[str], returns: list[float], window: dict[str, Any]) -> dict[str, Any]:
    trough_index = int(window["trough_index"])
    recovery_index = window.get("recovery_index")
    recovery_rows = int(recovery_index) - trough_index if recovery_index is not None else -1
    recovery_days = days_between(window["trough"], window["recovery"]) if recovery_index is not None else -1
    post_63 = window_return(dates, returns, trough_index + 1, min(len(dates) - 1, trough_index + 63))
    post_126 = window_return(dates, returns, trough_index + 1, min(len(dates) - 1, trough_index + 126))
    return {
        "created_at": created_at,
        "allocation_name": name,
        "worst_drawdown_start": window["start"],
        "worst_drawdown_trough": window["trough"],
        "worst_drawdown_percent": rounded(window["maxdd"]),
        "recovery_date": window["recovery"],
        "recovery_rows": str(recovery_rows) if recovery_rows >= 0 else "unrecovered_or_not_available",
        "recovery_days": str(recovery_days) if recovery_days >= 0 else "unrecovered_or_not_available",
        "drawdown_period_status": "recovered" if recovery_index is not None else "unrecovered_or_not_available",
        "post_trough_63d_return": rounded(post_63),
        "post_trough_126d_return": rounded(post_126),
        "bounce_back_status": bounce_back_status(post_63, post_126, recovery_index is not None),
        **safety_flags(),
    }


def build_decomposition_rows(created_at: str, dates: list[str], by_candidate: dict[str, dict[str, float]], higher_window: dict[str, Any]) -> list[dict[str, Any]]:
    start_index = int(higher_window["start_index"])
    trough_index = int(higher_window["trough_index"])
    period_dates = dates[start_index : trough_index + 1]
    current = contribution_row(created_at, period_dates, by_candidate, CURRENT_ALLOCATION)
    higher = contribution_row(created_at, period_dates, by_candidate, HIGHER_GROWTH_ALLOCATION)
    incremental = incremental_row(created_at, current, higher, higher_window)
    return [current, higher, incremental]


def contribution_row(created_at: str, dates: list[str], by_candidate: dict[str, dict[str, float]], allocation: tuple[str, float, float, float, float]) -> dict[str, Any]:
    name, qqq_weight, high_weight, crypto_weight, defensive_weight = allocation
    qqq_return = compound([by_candidate[RECOVERED_REFERENCE][date] for date in dates])
    high_return = compound([by_candidate[HIGH_GROWTH_SLEEVE][date] for date in dates])
    crypto_return = compound([by_candidate[CRYPTO_SLEEVE][date] for date in dates])
    defensive_return = 0.0
    qqq_contribution = qqq_return * qqq_weight / 100.0
    high_contribution = high_return * high_weight / 100.0
    crypto_contribution = crypto_return * crypto_weight / 100.0
    defensive_contribution = defensive_return * defensive_weight / 100.0
    total = qqq_contribution + high_contribution + crypto_contribution + defensive_contribution
    return {
        "created_at": created_at,
        "row_type": "period_contribution",
        "period_start": dates[0] if dates else "",
        "period_trough": dates[-1] if dates else "",
        "allocation_name": name,
        "qqq100_weight": rounded(qqq_weight),
        "high_growth_weight": rounded(high_weight),
        "crypto_weight": rounded(crypto_weight),
        "defensive_weight": rounded(defensive_weight),
        "qqq100_period_return": rounded(qqq_return * 100.0),
        "high_growth_period_return": rounded(high_return * 100.0),
        "crypto_period_return": rounded(crypto_return * 100.0),
        "defensive_period_return": rounded(defensive_return * 100.0),
        "qqq100_weighted_contribution": rounded(qqq_contribution * 100.0),
        "high_growth_weighted_contribution": rounded(high_contribution * 100.0),
        "crypto_weighted_contribution": rounded(crypto_contribution * 100.0),
        "defensive_weighted_contribution": rounded(defensive_contribution * 100.0),
        "total_period_return": rounded(total * 100.0),
        "delta_high_growth_weight": "",
        "delta_qqq100_weight": "",
        "delta_crypto_weight": "",
        "delta_defensive_weight": "",
        "incremental_high_growth_contribution": "",
        "reduced_qqq100_contribution": "",
        "net_incremental_drawdown_effect": "",
        "main_incremental_drawdown_contributor": "",
        "incremental_drawdown_status": "",
        "contribution_status": "saved_stream_period_decomposition_research_only",
        "attribution_confidence": "approximate_weighted_compounded_sleeve_returns",
        **safety_flags(),
    }


def incremental_row(created_at: str, current: dict[str, Any], higher: dict[str, Any], higher_window: dict[str, Any]) -> dict[str, Any]:
    high_delta = parse_float(higher["high_growth_weighted_contribution"]) - parse_float(current["high_growth_weighted_contribution"])
    qqq_delta = parse_float(higher["qqq100_weighted_contribution"]) - parse_float(current["qqq100_weighted_contribution"])
    crypto_delta = parse_float(higher["crypto_weighted_contribution"]) - parse_float(current["crypto_weighted_contribution"])
    defensive_delta = parse_float(higher["defensive_weighted_contribution"]) - parse_float(current["defensive_weighted_contribution"])
    net = parse_float(higher["total_period_return"]) - parse_float(current["total_period_return"])
    contributor = main_contributor(high_delta, qqq_delta, crypto_delta, defensive_delta)
    return {
        "created_at": created_at,
        "row_type": "incremental_high_growth_risk",
        "period_start": higher_window["start"],
        "period_trough": higher_window["trough"],
        "allocation_name": f"{HIGHER_GROWTH_ALLOCATION[0]}_vs_{CURRENT_ALLOCATION[0]}",
        "qqq100_weight": "",
        "high_growth_weight": "",
        "crypto_weight": "",
        "defensive_weight": "",
        "qqq100_period_return": higher["qqq100_period_return"],
        "high_growth_period_return": higher["high_growth_period_return"],
        "crypto_period_return": higher["crypto_period_return"],
        "defensive_period_return": "0",
        "qqq100_weighted_contribution": higher["qqq100_weighted_contribution"],
        "high_growth_weighted_contribution": higher["high_growth_weighted_contribution"],
        "crypto_weighted_contribution": higher["crypto_weighted_contribution"],
        "defensive_weighted_contribution": higher["defensive_weighted_contribution"],
        "total_period_return": rounded(net),
        "delta_high_growth_weight": rounded(HIGHER_GROWTH_ALLOCATION[2] - CURRENT_ALLOCATION[2]),
        "delta_qqq100_weight": rounded(HIGHER_GROWTH_ALLOCATION[1] - CURRENT_ALLOCATION[1]),
        "delta_crypto_weight": rounded(HIGHER_GROWTH_ALLOCATION[3] - CURRENT_ALLOCATION[3]),
        "delta_defensive_weight": rounded(HIGHER_GROWTH_ALLOCATION[4] - CURRENT_ALLOCATION[4]),
        "incremental_high_growth_contribution": rounded(high_delta),
        "reduced_qqq100_contribution": rounded(qqq_delta),
        "net_incremental_drawdown_effect": rounded(net),
        "main_incremental_drawdown_contributor": contributor,
        "incremental_drawdown_status": incremental_status(net),
        "contribution_status": "incremental_weight_shift_decomposition_research_only",
        "attribution_confidence": "approximate_same_window_weight_delta",
        **safety_flags(),
    }


def final_drawdown_status(current_window: dict[str, Any], higher_window: dict[str, Any]) -> str:
    delta = float(higher_window["maxdd"]) - float(current_window["maxdd"])
    if delta < -1.0:
        return STATUS_TOO_SENSITIVE
    if delta < 0:
        return STATUS_WATCH
    return STATUS_ACCEPTABLE


def build_summary_rows(
    created_at: str,
    final_status: str,
    period_rows: list[dict[str, Any]],
    decomposition_rows: list[dict[str, Any]],
    missing: list[str],
) -> list[dict[str, Any]]:
    current_period = row_named(period_rows, "allocation_name", CURRENT_ALLOCATION[0])
    higher_period = row_named(period_rows, "allocation_name", HIGHER_GROWTH_ALLOCATION[0])
    higher_contribution = row_named(decomposition_rows, "allocation_name", HIGHER_GROWTH_ALLOCATION[0])
    incremental = next((row for row in decomposition_rows if row.get("row_type") == "incremental_high_growth_risk"), {})
    drawdown_delta = metric_delta(higher_period.get("worst_drawdown_percent"), current_period.get("worst_drawdown_percent"))
    items = [
        ("final_drawdown_decomposition_status", final_status, "Cautious research-only drawdown status."),
        ("selected_lead_candidate", HIGHER_GROWTH_ALLOCATION[0], "Current multi-sleeve research lead candidate."),
        ("previous_baseline", CURRENT_ALLOCATION[0], "Previous baseline allocation."),
        ("candidate_worst_drawdown_period", format_period(higher_period), "Higher-growth worst drawdown window."),
        ("baseline_worst_drawdown_period", format_period(current_period), "Baseline worst drawdown window."),
        ("drawdown_delta", drawdown_delta, "Higher-growth minus baseline MaxDD."),
        ("main_incremental_drawdown_contributor", incremental.get("main_incremental_drawdown_contributor", MISSING), "Largest same-window incremental contribution."),
        ("high_growth_contribution_during_worst_period", higher_contribution.get("high_growth_weighted_contribution", MISSING), "Weighted high-growth contribution in candidate worst window."),
        ("qqq100_contribution_change", incremental.get("reduced_qqq100_contribution", MISSING), "QQQ100 contribution change from 75% to 70%."),
        ("crypto_contribution_during_worst_period", higher_contribution.get("crypto_weighted_contribution", MISSING), "Weighted crypto contribution in candidate worst window."),
        ("contribution_summary_by_sleeve", format_contribution_summary(higher_contribution), "Candidate weighted sleeve contributions."),
        ("incremental_high_growth_risk_summary", format_incremental(incremental), "Weight-shift effect versus baseline."),
        ("recovery_bounce_back_summary", format_recovery(higher_period), "Candidate recovery and post-trough returns."),
        ("missing_saved_inputs", ",".join(missing) or "none", "Missing saved inputs."),
        ("required_next_step", next_step_for(final_status), "Next research step only."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(created_at: str, final_status: str, missing: list[str], summary: dict[str, str]) -> list[dict[str, Any]]:
    if missing:
        return [
            blocker_row(
                created_at,
                "saved_output_completeness",
                STATUS_BLOCKED_MISSING,
                "high",
                ",".join(missing),
                NEXT_MISSING,
            )
        ]
    checks = [
        ("manual_review_required", "manual_review_required", "high", "higher-growth drawdown remains manual-review-only", next_step_for(final_status)),
        ("drawdown_sensitivity", final_status, "medium", summary.get("drawdown_delta", MISSING), next_step_for(final_status)),
        ("high_growth_incremental_risk", "manual_review_required", "medium", summary.get("incremental_high_growth_risk_summary", MISSING), next_step_for(final_status)),
        ("recovery_bounce_back", "manual_review_required", "medium", summary.get("recovery_bounce_back_summary", MISSING), next_step_for(final_status)),
        ("execution_boundary", "blocked_non_executable_research_only", "high", "report is not paper/live execution", next_step_for(final_status)),
        ("crypto_execution_boundary", "blocked_non_executable_research_only", "high", "report is not crypto execution", next_step_for(final_status)),
        ("scheduling_boundary", "blocked_no_scheduling_change", "high", "report is not a schedule or cron change", next_step_for(final_status)),
    ]
    return [blocker_row(created_at, *check) for check in checks]


def blocker_row(created_at: str, name: str, status: str, severity: str, detail: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "blocker_status": status,
        "blocker_severity": severity,
        "blocker_detail": detail,
        "required_next_step": next_step,
        "execution_approved": False,
        "crypto_execution_approved": False,
        "scheduling_approved": False,
    }


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return [
        "Multi-sleeve high-growth drawdown decomposition created. Saved-output-only research; no execution path.",
        f"final drawdown decomposition status: {summary.get('final_drawdown_decomposition_status', MISSING)}",
        f"selected lead candidate: {summary.get('selected_lead_candidate', MISSING)}",
        f"previous baseline: {summary.get('previous_baseline', MISSING)}",
        f"candidate worst drawdown period: {summary.get('candidate_worst_drawdown_period', MISSING)}",
        f"baseline worst drawdown period: {summary.get('baseline_worst_drawdown_period', MISSING)}",
        f"drawdown delta: {summary.get('drawdown_delta', MISSING)}",
        f"main incremental drawdown contributor: {summary.get('main_incremental_drawdown_contributor', MISSING)}",
        f"contribution summary by sleeve: {summary.get('contribution_summary_by_sleeve', MISSING)}",
        f"incremental high-growth risk summary: {summary.get('incremental_high_growth_risk_summary', MISSING)}",
        f"recovery/bounce-back summary: {summary.get('recovery_bounce_back_summary', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        f"Saved decomposition: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def blocked_period_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "allocation_name": name,
            "worst_drawdown_start": "",
            "worst_drawdown_trough": "",
            "worst_drawdown_percent": MISSING,
            "recovery_date": "unrecovered_or_not_available",
            "recovery_rows": "unrecovered_or_not_available",
            "recovery_days": "unrecovered_or_not_available",
            "drawdown_period_status": "missing_saved_inputs=" + ",".join(missing),
            "post_trough_63d_return": MISSING,
            "post_trough_126d_return": MISSING,
            "bounce_back_status": "blocked_missing_saved_inputs",
            **safety_flags(),
        }
        for name in [CURRENT_ALLOCATION[0], HIGHER_GROWTH_ALLOCATION[0]]
    ]


def blocked_decomposition_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    base = {
        "created_at": created_at,
        "row_type": "blocked_missing_saved_inputs",
        "period_start": "",
        "period_trough": "",
        "allocation_name": HIGHER_GROWTH_ALLOCATION[0],
        "qqq100_weight": MISSING,
        "high_growth_weight": MISSING,
        "crypto_weight": MISSING,
        "defensive_weight": MISSING,
        "qqq100_period_return": MISSING,
        "high_growth_period_return": MISSING,
        "crypto_period_return": MISSING,
        "defensive_period_return": MISSING,
        "qqq100_weighted_contribution": MISSING,
        "high_growth_weighted_contribution": MISSING,
        "crypto_weighted_contribution": MISSING,
        "defensive_weighted_contribution": MISSING,
        "total_period_return": MISSING,
        "delta_high_growth_weight": MISSING,
        "delta_qqq100_weight": MISSING,
        "delta_crypto_weight": MISSING,
        "delta_defensive_weight": MISSING,
        "incremental_high_growth_contribution": MISSING,
        "reduced_qqq100_contribution": MISSING,
        "net_incremental_drawdown_effect": MISSING,
        "main_incremental_drawdown_contributor": MISSING,
        "incremental_drawdown_status": "missing_saved_inputs=" + ",".join(missing),
        "contribution_status": "blocked_missing_saved_inputs",
        "attribution_confidence": "blocked_missing_saved_inputs",
        **safety_flags(),
    }
    return [base]


def compound(values: list[float]) -> float:
    equity = 1.0
    for value in values:
        equity *= 1.0 + value
    return equity - 1.0


def window_return(dates: list[str], returns: list[float], start: int, end: int) -> float:
    if not dates or start >= len(dates) or start > end:
        return 0.0
    return compound(returns[max(0, start) : min(len(returns), end + 1)]) * 100.0


def days_between(start: str, end: str) -> int:
    try:
        from datetime import date

        return (date.fromisoformat(end) - date.fromisoformat(start)).days
    except (TypeError, ValueError):
        return -1


def bounce_back_status(post_63: float, post_126: float, recovered: bool) -> str:
    if recovered:
        return "recovered_in_saved_window"
    if post_126 > 0 or post_63 > 0:
        return "positive_post_trough_bounce_unrecovered_window"
    return "weak_post_trough_bounce_manual_review_required"


def main_contributor(high_delta: float, qqq_delta: float, crypto_delta: float, defensive_delta: float) -> str:
    items = {
        "extra_high_growth_weight": high_delta,
        "reduced_qqq100_weight": qqq_delta,
        "crypto_weight_unchanged": crypto_delta,
        "defensive_weight_unchanged": defensive_delta,
    }
    negative = {name: value for name, value in items.items() if value < 0}
    if negative:
        return min(negative.items(), key=lambda item: item[1])[0]
    return max(items.items(), key=lambda item: abs(item[1]))[0]


def incremental_status(net: float) -> str:
    if net < -1.0:
        return "incremental_drawdown_too_sensitive"
    if net < 0:
        return "incremental_drawdown_watch_manual_review_required"
    return "incremental_drawdown_not_worse_same_window"


def next_step_for(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING:
        return NEXT_MISSING
    if status == STATUS_TOO_SENSITIVE:
        return NEXT_CHALLENGER
    return NEXT_MANUAL_REVIEW


def format_period(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"{row.get('allocation_name')}: start={row.get('worst_drawdown_start')}; trough={row.get('worst_drawdown_trough')}; MaxDD={row.get('worst_drawdown_percent')}; recovery={row.get('recovery_date')}"


def format_contribution_summary(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"qqq100={row.get('qqq100_weighted_contribution')}; high_growth={row.get('high_growth_weighted_contribution')}; crypto={row.get('crypto_weighted_contribution')}; defensive={row.get('defensive_weighted_contribution')}; total={row.get('total_period_return')}"


def format_incremental(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"high_growth={row.get('incremental_high_growth_contribution')}; qqq100={row.get('reduced_qqq100_contribution')}; net={row.get('net_incremental_drawdown_effect')}; contributor={row.get('main_incremental_drawdown_contributor')}; status={row.get('incremental_drawdown_status')}"


def format_recovery(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"recovery={row.get('recovery_date')}; rows={row.get('recovery_rows')}; 63d={row.get('post_trough_63d_return')}; 126d={row.get('post_trough_126d_return')}; status={row.get('bounce_back_status')}"


def metric_delta(left: Any, right: Any) -> str:
    return rounded(parse_float(left) - parse_float(right))


def row_named(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    return next((row for row in rows if row.get(key) == value), {})


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rounded(value: Any) -> str:
    return str(round(parse_float(value), 4))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": True,
        "saved_output_only": True,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
        "orders_replaced": False,
        "alpaca_called": False,
        "yfinance_called": False,
        "live_position_read": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "live_trading_approved": False,
        "scheduling_approved": False,
        "shorting_approved": False,
        "leverage_approved": False,
        "margin_approved": False,
    }
