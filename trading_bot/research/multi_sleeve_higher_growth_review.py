"""Saved-output-only review of the higher-growth multi-sleeve challenger."""

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
CURRENT_ALLOCATION = ("current_75_15_5_5", 75, 15, 5, 5)
HIGHER_GROWTH_ALLOCATION = ("higher_growth_70_20_5_5", 70, 20, 5, 5)

STATUS_LEAD_CANDIDATE = "higher_growth_review_new_research_lead_candidate"
STATUS_DRAWDOWN_SENSITIVE = "higher_growth_review_promising_but_drawdown_sensitive"
STATUS_SPLIT_CHALLENGER = "higher_growth_review_split_sensitive_challenger"
STATUS_COST_CHALLENGER = "higher_growth_review_cost_sensitive_challenger"
STATUS_REJECTED = "higher_growth_review_rejected_drawdown_or_split_risk"
STATUS_BLOCKED_MISSING = "higher_growth_review_blocked_missing_saved_streams"

NEXT_MANUAL_REVIEW = "manual_review_before_higher_growth_candidate_label_change"
NEXT_COST_REVIEW = "manual_review_cost_stress_before_higher_growth_candidate_label_change"
NEXT_SPLIT_REVIEW = "manual_review_split_stability_before_higher_growth_candidate_label_change"
NEXT_MISSING = "missing_saved_streams_before_higher_growth_review"

INPUT_FILES = {
    "qqq100_recovered_reference_stream": Path("data/qqq100_recovered_reference_stream.csv"),
    "high_growth_return_streams": Path("data/high_growth_return_streams.csv"),
    "crypto_return_streams": Path("data/crypto_return_streams.csv"),
    "portfolio": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "weight_sensitivity": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "weight_summary": Path("data/multi_sleeve_weight_sensitivity_summary.csv"),
    "crypto_review": Path("data/multi_sleeve_crypto_review.csv"),
    "allocation_policy": Path("data/multi_sleeve_allocation_policy_review.csv"),
}

OUTPUT_FILES = {
    "review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "summary": Path("data/multi_sleeve_higher_growth_summary.csv"),
    "split": Path("data/multi_sleeve_higher_growth_split_review.csv"),
    "cost": Path("data/multi_sleeve_higher_growth_cost_review.csv"),
    "drawdown": Path("data/multi_sleeve_higher_growth_drawdown_review.csv"),
    "blockers": Path("data/multi_sleeve_higher_growth_blockers.csv"),
}

SPLITS = [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]
COST_STRESSES = [
    ("base_cost", 0.0),
    ("plus_25bps_high_growth_turnover", 25.0),
    ("plus_50bps_high_growth_turnover", 50.0),
    ("plus_100bps_high_growth_turnover", 100.0),
]

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
    "crypto_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

REVIEW_COLUMNS = [
    "created_at",
    "review_name",
    "allocation_name",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "annual_volatility",
    "delta_CAGR",
    "delta_Sharpe",
    "delta_MaxDD",
    "delta_Calmar",
    "risk_status",
    "research_status",
    "required_next_step",
    "qqq100_contribution_delta",
    "high_growth_contribution_delta",
    "crypto_contribution_delta",
    "defensive_contribution_delta",
    "contribution_status",
    "attribution_confidence",
    *SAFETY_COLUMNS,
]

SPLIT_COLUMNS = [
    "created_at",
    "split_name",
    "allocation_name",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "delta_CAGR_higher_growth_vs_current",
    "delta_Sharpe_higher_growth_vs_current",
    "delta_MaxDD_higher_growth_vs_current",
    "delta_Calmar_higher_growth_vs_current",
    "split_result_status",
    *SAFETY_COLUMNS,
]

COST_COLUMNS = [
    "created_at",
    "allocation_name",
    "cost_stress_name",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "delta_CAGR_vs_current_base",
    "cost_stress_status",
    "cost_model_status",
    *SAFETY_COLUMNS,
]

DRAWDOWN_COLUMNS = [
    "created_at",
    "allocation_name",
    "worst_drawdown_start",
    "worst_drawdown_trough",
    "worst_drawdown_percent",
    "recovery_date",
    "drawdown_delta_vs_current",
    "drawdown_status",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = ["created_at", "summary_name", "summary_value", "details", *SAFETY_COLUMNS]
BLOCKER_COLUMNS = ["created_at", "blocker_name", "blocker_status", "evidence", "required_next_step", *SAFETY_COLUMNS]


@dataclass
class HigherGrowthReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_higher_growth_review(root_dir: Path | str = ".") -> HigherGrowthReviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    streams = (
        backtest.normalize_recovered_reference_stream_rows(inputs["qqq100_recovered_reference_stream"])
        + backtest.normalize_high_growth_stream_rows(inputs["high_growth_return_streams"])
        + backtest.normalize_crypto_stream_rows(inputs["crypto_return_streams"])
    )
    by_candidate = backtest.stream_returns_by_candidate(streams)
    missing = missing_streams(by_candidate)
    if missing:
        review_rows = blocked_review_rows(created_at, missing)
        split_rows = blocked_split_rows(created_at, missing)
        cost_rows = blocked_cost_rows(created_at, missing)
        drawdown_rows = blocked_drawdown_rows(created_at, missing)
        final_status = STATUS_BLOCKED_MISSING
    else:
        dates = common_dates(by_candidate)
        current_returns = allocation_returns(dates, by_candidate, CURRENT_ALLOCATION)
        higher_returns = allocation_returns(dates, by_candidate, HIGHER_GROWTH_ALLOCATION)
        review_rows = build_review_rows(created_at, dates, by_candidate, current_returns, higher_returns)
        split_rows = build_split_rows(created_at, dates, by_candidate)
        cost_rows = build_cost_rows(created_at, dates, by_candidate, current_returns, inputs)
        drawdown_rows = build_drawdown_rows(created_at, dates, current_returns, higher_returns)
        final_status = final_review_status(review_rows, split_rows, cost_rows, drawdown_rows)
    summary_rows = build_summary_rows(created_at, final_status, review_rows, split_rows, cost_rows, drawdown_rows, missing)
    blocker_rows = build_blocker_rows(created_at, final_status, missing, review_rows, split_rows, cost_rows, drawdown_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["split"], SPLIT_COLUMNS, split_rows)
    write_rows(output_paths["cost"], COST_COLUMNS, cost_rows)
    write_rows(output_paths["drawdown"], DRAWDOWN_COLUMNS, drawdown_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HigherGrowthReviewResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        split_rows=split_rows,
        cost_rows=cost_rows,
        drawdown_rows=drawdown_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["review"]),
    )


def show_multi_sleeve_higher_growth_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve higher-growth review is missing.",
            "Run `python bot.py --multi-sleeve-higher-growth-review` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "Multi-sleeve higher-growth review. Saved-output-only research; no execution approval.",
        f"final higher-growth review status: {summary.get('final_higher_growth_review_status', MISSING)}",
        f"current allocation metrics: {summary.get('current_allocation_metrics', MISSING)}",
        f"higher-growth allocation metrics: {summary.get('higher_growth_allocation_metrics', MISSING)}",
        f"deltas vs current: {summary.get('delta_vs_current', MISSING)}",
        f"split win count: {summary.get('split_win_count', MISSING)}",
        f"worst split result: {summary.get('worst_split_result', MISSING)}",
        f"worst cost stress result: {summary.get('worst_cost_stress_result', MISSING)}",
        f"drawdown comparison: {summary.get('drawdown_comparison', MISSING)}",
        f"contribution summary: {summary.get('contribution_summary', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def build_review_rows(created_at: str, dates: list[str], by_candidate: dict[str, dict[str, float]], current_returns: list[float], higher_returns: list[float]) -> list[dict[str, Any]]:
    current_metrics = backtest.metrics_for_returns(current_returns)
    higher_metrics = backtest.metrics_for_returns(higher_returns)
    contribution = contribution_deltas(dates, by_candidate)
    return [
        review_row(created_at, CURRENT_ALLOCATION[0], current_metrics, current_metrics, "current_allocation_reference", "research_only_current_baseline", contribution),
        review_row(created_at, HIGHER_GROWTH_ALLOCATION[0], higher_metrics, current_metrics, "higher_growth_drawdown_sensitive", "research_only_challenger", contribution),
    ]


def review_row(created_at: str, name: str, metrics: dict[str, str], current_metrics: dict[str, str], risk_status: str, research_status: str, contribution: dict[str, str]) -> dict[str, Any]:
    is_current = name == CURRENT_ALLOCATION[0]
    return {
        "created_at": created_at,
        "review_name": "higher_growth_headline_comparison",
        "allocation_name": name,
        "CAGR": metrics["cagr"],
        "Sharpe": metrics["sharpe"],
        "MaxDD": metrics["max_drawdown"],
        "Calmar": metrics["calmar"],
        "annual_volatility": metrics["annualised_volatility"],
        "delta_CAGR": "0" if is_current else backtest.metric_delta(metrics["cagr"], current_metrics["cagr"]),
        "delta_Sharpe": "0" if is_current else backtest.metric_delta(metrics["sharpe"], current_metrics["sharpe"]),
        "delta_MaxDD": "0" if is_current else backtest.metric_delta(metrics["max_drawdown"], current_metrics["max_drawdown"]),
        "delta_Calmar": "0" if is_current else backtest.metric_delta(metrics["calmar"], current_metrics["calmar"]),
        "risk_status": risk_status,
        "research_status": research_status,
        "required_next_step": NEXT_MANUAL_REVIEW,
        "qqq100_contribution_delta": "0" if is_current else contribution["qqq100"],
        "high_growth_contribution_delta": "0" if is_current else contribution["high_growth"],
        "crypto_contribution_delta": "0" if is_current else contribution["crypto"],
        "defensive_contribution_delta": "0",
        "contribution_status": "approximate_more_high_growth_less_qqq100_exposure" if not is_current else "current_baseline",
        "attribution_confidence": "approximate_saved_stream_weight_delta",
        **safety_flags(),
    }


def build_split_rows(created_at: str, dates: list[str], by_candidate: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split_name, fraction in SPLITS:
        start = max(1, int(len(dates) * fraction))
        split_dates = dates[start:]
        current_returns = allocation_returns(split_dates, by_candidate, CURRENT_ALLOCATION)
        higher_returns = allocation_returns(split_dates, by_candidate, HIGHER_GROWTH_ALLOCATION)
        current_metrics = backtest.metrics_for_returns(current_returns)
        higher_metrics = backtest.metrics_for_returns(higher_returns)
        for name, metrics in [(CURRENT_ALLOCATION[0], current_metrics), (HIGHER_GROWTH_ALLOCATION[0], higher_metrics)]:
            rows.append(
                {
                    "created_at": created_at,
                    "split_name": split_name,
                    "allocation_name": name,
                    "CAGR": metrics["cagr"],
                    "Sharpe": metrics["sharpe"],
                    "MaxDD": metrics["max_drawdown"],
                    "Calmar": metrics["calmar"],
                    "delta_CAGR_higher_growth_vs_current": "0" if name == CURRENT_ALLOCATION[0] else backtest.metric_delta(higher_metrics["cagr"], current_metrics["cagr"]),
                    "delta_Sharpe_higher_growth_vs_current": "0" if name == CURRENT_ALLOCATION[0] else backtest.metric_delta(higher_metrics["sharpe"], current_metrics["sharpe"]),
                    "delta_MaxDD_higher_growth_vs_current": "0" if name == CURRENT_ALLOCATION[0] else backtest.metric_delta(higher_metrics["max_drawdown"], current_metrics["max_drawdown"]),
                    "delta_Calmar_higher_growth_vs_current": "0" if name == CURRENT_ALLOCATION[0] else backtest.metric_delta(higher_metrics["calmar"], current_metrics["calmar"]),
                    "split_result_status": split_status(higher_metrics, current_metrics) if name == HIGHER_GROWTH_ALLOCATION[0] else "current_split_reference",
                    **safety_flags(),
                }
            )
    return rows


def build_cost_rows(created_at: str, dates: list[str], by_candidate: dict[str, dict[str, float]], current_returns: list[float], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    current_metrics = backtest.metrics_for_returns(current_returns)
    high_growth_change_dates, cost_model_status = high_growth_turnover_dates(inputs["high_growth_return_streams"], dates)
    rows = []
    for stress_name, bps in COST_STRESSES:
        returns = allocation_returns(dates, by_candidate, HIGHER_GROWTH_ALLOCATION)
        if bps:
            daily_cost = (bps / 10_000.0) * (HIGHER_GROWTH_ALLOCATION[2] / 100.0)
            returns = [value - daily_cost if date in high_growth_change_dates else value for date, value in zip(dates, returns)]
        metrics = backtest.metrics_for_returns(returns)
        rows.append(
            {
                "created_at": created_at,
                "allocation_name": HIGHER_GROWTH_ALLOCATION[0],
                "cost_stress_name": stress_name,
                "CAGR": metrics["cagr"],
                "Sharpe": metrics["sharpe"],
                "MaxDD": metrics["max_drawdown"],
                "Calmar": metrics["calmar"],
                "delta_CAGR_vs_current_base": backtest.metric_delta(metrics["cagr"], current_metrics["cagr"]),
                "cost_stress_status": "cost_sensitive_challenger" if parse_float(backtest.metric_delta(metrics["cagr"], current_metrics["cagr"])) < 0 else "cost_stress_still_beats_current_research_only",
                "cost_model_status": cost_model_status,
                **safety_flags(),
            }
        )
    return rows


def build_drawdown_rows(created_at: str, dates: list[str], current_returns: list[float], higher_returns: list[float]) -> list[dict[str, Any]]:
    current = drawdown_window(dates, current_returns)
    higher = drawdown_window(dates, higher_returns)
    return [
        drawdown_row(created_at, CURRENT_ALLOCATION[0], current, "0", "current_drawdown_reference"),
        drawdown_row(created_at, HIGHER_GROWTH_ALLOCATION[0], higher, str(round(higher["maxdd"] - current["maxdd"], 4)), "higher_growth_drawdown_worse_than_current" if higher["maxdd"] < current["maxdd"] else "higher_growth_drawdown_not_worse_than_current"),
    ]


def final_review_status(review_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]], drawdown_rows: list[dict[str, Any]]) -> str:
    higher = row_named(review_rows, "allocation_name", HIGHER_GROWTH_ALLOCATION[0])
    split_wins = sum(1 for row in split_rows if row.get("allocation_name") == HIGHER_GROWTH_ALLOCATION[0] and parse_float(row.get("delta_Calmar_higher_growth_vs_current")) > 0 and parse_float(row.get("delta_Sharpe_higher_growth_vs_current")) > 0)
    worst_cost = min((parse_float(row.get("delta_CAGR_vs_current_base")) for row in cost_rows), default=0)
    higher_dd = row_named(drawdown_rows, "allocation_name", HIGHER_GROWTH_ALLOCATION[0])
    if split_wins < 2:
        return STATUS_SPLIT_CHALLENGER
    if worst_cost < 0:
        return STATUS_COST_CHALLENGER
    if parse_float(higher_dd.get("drawdown_delta_vs_current")) < -1.0:
        return STATUS_REJECTED
    if parse_float(higher.get("delta_MaxDD")) < 0:
        return STATUS_DRAWDOWN_SENSITIVE
    return STATUS_LEAD_CANDIDATE


def build_summary_rows(created_at: str, final_status: str, review_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]], drawdown_rows: list[dict[str, Any]], missing: list[str]) -> list[dict[str, Any]]:
    current = row_named(review_rows, "allocation_name", CURRENT_ALLOCATION[0])
    higher = row_named(review_rows, "allocation_name", HIGHER_GROWTH_ALLOCATION[0])
    split_wins = sum(1 for row in split_rows if row.get("allocation_name") == HIGHER_GROWTH_ALLOCATION[0] and parse_float(row.get("delta_Calmar_higher_growth_vs_current")) > 0 and parse_float(row.get("delta_Sharpe_higher_growth_vs_current")) > 0)
    worst_split = min([row for row in split_rows if row.get("allocation_name") == HIGHER_GROWTH_ALLOCATION[0]], key=lambda row: parse_float(row.get("delta_Calmar_higher_growth_vs_current")), default={})
    worst_cost = min(cost_rows, key=lambda row: parse_float(row.get("delta_CAGR_vs_current_base")), default={})
    higher_dd = row_named(drawdown_rows, "allocation_name", HIGHER_GROWTH_ALLOCATION[0])
    items = [
        ("final_higher_growth_review_status", final_status, "Research-only final status."),
        ("current_allocation_metrics", format_review_metrics(current), "Current allocation metrics."),
        ("higher_growth_allocation_metrics", format_review_metrics(higher), "Higher-growth allocation metrics."),
        ("delta_vs_current", format_deltas(higher), "Higher-growth minus current full-period deltas."),
        ("split_win_count", str(split_wins), "Number of fixed splits where higher growth wins on Sharpe and Calmar."),
        ("worst_split_result", format_split(worst_split), "Worst fixed split for higher growth by Calmar delta."),
        ("worst_cost_stress_result", format_cost(worst_cost), "Worst fixed high-growth turnover cost stress."),
        ("drawdown_comparison", format_drawdown(higher_dd), "Higher-growth drawdown versus current."),
        ("contribution_summary", format_contribution(higher), "Approximate saved-stream contribution/interaction summary."),
        ("missing_saved_streams", ",".join(missing) or "none", "Missing saved stream blockers."),
        ("required_next_step", next_step_for(final_status), "Next research step, not execution approval."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(created_at: str, final_status: str, missing: list[str], review_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]], drawdown_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if missing:
        return [{"created_at": created_at, "blocker_name": "missing_saved_streams", "blocker_status": STATUS_BLOCKED_MISSING, "evidence": ",".join(missing), "required_next_step": NEXT_MISSING, **safety_flags()}]
    return [
        {"created_at": created_at, "blocker_name": "manual_review_required", "blocker_status": final_status, "evidence": "higher-growth challenger needs split/cost/drawdown review before label change", "required_next_step": next_step_for(final_status), **safety_flags()},
        {"created_at": created_at, "blocker_name": "execution_boundary", "blocker_status": "execution_blocked", "evidence": "research output is not paper, crypto, or live execution approval", "required_next_step": NEXT_MANUAL_REVIEW, **safety_flags()},
    ]


def common_dates(by_candidate: dict[str, dict[str, float]]) -> list[str]:
    return sorted(set(by_candidate[RECOVERED_REFERENCE]) & set(by_candidate[HIGH_GROWTH_SLEEVE]) & set(by_candidate[CRYPTO_SLEEVE]))


def missing_streams(by_candidate: dict[str, dict[str, float]]) -> list[str]:
    return [name for name in [RECOVERED_REFERENCE, HIGH_GROWTH_SLEEVE, CRYPTO_SLEEVE] if name not in by_candidate]


def allocation_returns(dates: list[str], by_candidate: dict[str, dict[str, float]], allocation: tuple[str, int, int, int, int]) -> list[float]:
    _name, qqq, high_growth, crypto, _defensive = allocation
    return [by_candidate[RECOVERED_REFERENCE][date] * qqq / 100 + by_candidate[HIGH_GROWTH_SLEEVE][date] * high_growth / 100 + by_candidate[CRYPTO_SLEEVE][date] * crypto / 100 for date in dates]


def contribution_deltas(dates: list[str], by_candidate: dict[str, dict[str, float]]) -> dict[str, str]:
    qqq_delta = -5 / 100 * annualized_sum(dates, by_candidate[RECOVERED_REFERENCE])
    high_delta = 5 / 100 * annualized_sum(dates, by_candidate[HIGH_GROWTH_SLEEVE])
    return {"qqq100": str(round(qqq_delta, 4)), "high_growth": str(round(high_delta, 4)), "crypto": "0", "defensive": "0"}


def annualized_sum(dates: list[str], returns_by_date: dict[str, float]) -> float:
    return sum(returns_by_date[date] for date in dates) * 252 / max(1, len(dates)) * 100


def split_status(higher: dict[str, str], current: dict[str, str]) -> str:
    if parse_float(backtest.metric_delta(higher["calmar"], current["calmar"])) > 0 and parse_float(backtest.metric_delta(higher["sharpe"], current["sharpe"])) > 0:
        return "higher_growth_split_win_research_only"
    return "higher_growth_split_needs_review"


def high_growth_turnover_dates(rows: list[dict[str, str]], dates: list[str]) -> tuple[set[str], str]:
    states = []
    for row in sorted(rows, key=lambda item: item.get("date", "")):
        state = row.get("signal_state") or row.get("invested_flag") or row.get("exposure")
        if row.get("date") and state not in {"", None}:
            states.append((row["date"], str(state)))
    if states:
        changes = {date for (date, state), (_prev_date, prev_state) in zip(states[1:], states[:-1]) if state != prev_state}
        return changes, "saved_high_growth_exposure_change_proxy"
    return set(dates[::21]), "conservative_placeholder_monthly_turnover"


def drawdown_window(dates: list[str], returns: list[float]) -> dict[str, Any]:
    equity = 1.0
    peak = 1.0
    peak_index = 0
    worst = {"start": dates[0] if dates else "", "trough": dates[0] if dates else "", "maxdd": 0.0, "trough_index": 0}
    curve = []
    for index, value in enumerate(returns):
        equity *= 1 + value
        curve.append(equity)
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = (equity / peak - 1) * 100 if peak else 0.0
        if drawdown < worst["maxdd"]:
            worst = {"start": dates[peak_index], "trough": dates[index], "maxdd": drawdown, "trough_index": index, "peak": peak}
    recovery = ""
    for index in range(int(worst["trough_index"]) + 1, len(curve)):
        if curve[index] >= worst.get("peak", float("inf")):
            recovery = dates[index]
            break
    worst["recovery"] = recovery or "not_recovered_in_saved_window"
    return worst


def drawdown_row(created_at: str, name: str, row: dict[str, Any], delta: str, status: str) -> dict[str, Any]:
    return {"created_at": created_at, "allocation_name": name, "worst_drawdown_start": row["start"], "worst_drawdown_trough": row["trough"], "worst_drawdown_percent": str(round(row["maxdd"], 4)), "recovery_date": row["recovery"], "drawdown_delta_vs_current": delta, "drawdown_status": status, **safety_flags()}


def blocked_review_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [blocked_review_row(created_at, CURRENT_ALLOCATION[0], missing), blocked_review_row(created_at, HIGHER_GROWTH_ALLOCATION[0], missing)]


def blocked_review_row(created_at: str, name: str, missing: list[str]) -> dict[str, Any]:
    return {"created_at": created_at, "review_name": "higher_growth_headline_comparison", "allocation_name": name, "CAGR": MISSING, "Sharpe": MISSING, "MaxDD": MISSING, "Calmar": MISSING, "annual_volatility": MISSING, "delta_CAGR": MISSING, "delta_Sharpe": MISSING, "delta_MaxDD": MISSING, "delta_Calmar": MISSING, "risk_status": "blocked_missing_saved_streams", "research_status": STATUS_BLOCKED_MISSING, "required_next_step": NEXT_MISSING, "qqq100_contribution_delta": MISSING, "high_growth_contribution_delta": MISSING, "crypto_contribution_delta": MISSING, "defensive_contribution_delta": MISSING, "contribution_status": "missing_saved_streams=" + ",".join(missing), "attribution_confidence": "blocked_missing_saved_streams", **safety_flags()}


def blocked_split_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [{"created_at": created_at, "split_name": split, "allocation_name": name, "CAGR": MISSING, "Sharpe": MISSING, "MaxDD": MISSING, "Calmar": MISSING, "delta_CAGR_higher_growth_vs_current": MISSING, "delta_Sharpe_higher_growth_vs_current": MISSING, "delta_MaxDD_higher_growth_vs_current": MISSING, "delta_Calmar_higher_growth_vs_current": MISSING, "split_result_status": "missing_saved_streams=" + ",".join(missing), **safety_flags()} for split, _ in SPLITS for name in [CURRENT_ALLOCATION[0], HIGHER_GROWTH_ALLOCATION[0]]]


def blocked_cost_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [{"created_at": created_at, "allocation_name": HIGHER_GROWTH_ALLOCATION[0], "cost_stress_name": name, "CAGR": MISSING, "Sharpe": MISSING, "MaxDD": MISSING, "Calmar": MISSING, "delta_CAGR_vs_current_base": MISSING, "cost_stress_status": "missing_saved_streams=" + ",".join(missing), "cost_model_status": "blocked_missing_saved_streams", **safety_flags()} for name, _ in COST_STRESSES]


def blocked_drawdown_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [{"created_at": created_at, "allocation_name": name, "worst_drawdown_start": "", "worst_drawdown_trough": "", "worst_drawdown_percent": MISSING, "recovery_date": "", "drawdown_delta_vs_current": MISSING, "drawdown_status": "missing_saved_streams=" + ",".join(missing), **safety_flags()} for name in [CURRENT_ALLOCATION[0], HIGHER_GROWTH_ALLOCATION[0]]]


def next_step_for(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING:
        return NEXT_MISSING
    if status == STATUS_COST_CHALLENGER:
        return NEXT_COST_REVIEW
    if status == STATUS_SPLIT_CHALLENGER:
        return NEXT_SPLIT_REVIEW
    return NEXT_MANUAL_REVIEW


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return ["Multi-sleeve higher-growth review created. Saved-output-only research; no execution approval.", f"final higher-growth review status: {summary['final_higher_growth_review_status']}", f"current allocation metrics: {summary['current_allocation_metrics']}", f"higher-growth allocation metrics: {summary['higher_growth_allocation_metrics']}", f"deltas vs current: {summary['delta_vs_current']}", f"split win count: {summary['split_win_count']}", f"worst split result: {summary['worst_split_result']}", f"worst cost stress result: {summary['worst_cost_stress_result']}", f"drawdown comparison: {summary['drawdown_comparison']}", f"contribution summary: {summary['contribution_summary']}", f"required next step: {summary['required_next_step']}", f"Saved review: {output_path}", "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false"]


def format_review_metrics(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"{row.get('allocation_name')}: CAGR={row.get('CAGR')}; Sharpe={row.get('Sharpe')}; MaxDD={row.get('MaxDD')}; Calmar={row.get('Calmar')}"


def format_deltas(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"CAGR={row.get('delta_CAGR')}; Sharpe={row.get('delta_Sharpe')}; MaxDD={row.get('delta_MaxDD')}; Calmar={row.get('delta_Calmar')}"


def format_split(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"{row.get('split_name')}: dCAGR={row.get('delta_CAGR_higher_growth_vs_current')}; dSharpe={row.get('delta_Sharpe_higher_growth_vs_current')}; dMaxDD={row.get('delta_MaxDD_higher_growth_vs_current')}; dCalmar={row.get('delta_Calmar_higher_growth_vs_current')}; status={row.get('split_result_status')}"


def format_cost(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"{row.get('cost_stress_name')}: CAGR={row.get('CAGR')}; dCAGR_vs_current={row.get('delta_CAGR_vs_current_base')}; status={row.get('cost_stress_status')}; model={row.get('cost_model_status')}"


def format_drawdown(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"{row.get('allocation_name')}: start={row.get('worst_drawdown_start')}; trough={row.get('worst_drawdown_trough')}; MaxDD={row.get('worst_drawdown_percent')}; delta_vs_current={row.get('drawdown_delta_vs_current')}; status={row.get('drawdown_status')}"


def format_contribution(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return f"qqq100={row.get('qqq100_contribution_delta')}; high_growth={row.get('high_growth_contribution_delta')}; crypto={row.get('crypto_contribution_delta')}; defensive={row.get('defensive_contribution_delta')}; status={row.get('contribution_status')}; confidence={row.get('attribution_confidence')}"


def row_named(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    return next((row for row in rows if row.get(key) == value), {})


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


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
    return {"research_only": True, "preview_only": True, "saved_output_only": True, "orders_created": False, "orders_submitted": False, "orders_cancelled": False, "orders_replaced": False, "alpaca_called": False, "live_position_read": False, "sqlite_trade_log_written": False, "discord_alert_sent": False, "telegram_alert_sent": False, "execution_approved": False, "paper_execution_approved": False, "crypto_execution_approved": False, "scheduling_approved": False, "live_trading_approved": False}
