"""Saved-output volatility-targeted growth research sprint.

This module researches volatility-targeted growth candidates using existing
saved return streams only. It does not refresh market data, call Alpaca, read
positions, create order instructions, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "sprint": Path("data/vol_targeted_growth_research_sprint.csv"),
    "summary": Path("data/vol_targeted_growth_candidate_summary.csv"),
    "rejected": Path("data/vol_targeted_growth_rejected_candidates.csv"),
    "audit": Path("data/vol_targeted_growth_robustness_audit.csv"),
    "sensitivity": Path("data/vol_targeted_growth_parameter_sensitivity.csv"),
}

INPUT_FILES = {
    "qqq100_stream": Path("data/qqq100_recovered_reference_stream.csv"),
    "high_growth_streams": Path("data/high_growth_return_streams.csv"),
    "crypto_streams": Path("data/crypto_return_streams.csv"),
    "sleeve_streams": Path("data/sleeve_return_streams.csv"),
    "qqq100_metrics": Path("data/qqq100_recovered_reference_metrics.csv"),
    "high_growth_metrics": Path("data/high_growth_return_stream_metrics.csv"),
    "higher_growth_selection": Path("data/higher_growth_candidate_selection_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "backtest_only": True,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "action_preview_created": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "preview_candidate_approved": False,
    "preview_implementation_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "high_growth_promotion_approved": False,
    "crypto_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

SPRINT_COLUMNS = [
    "created_at",
    "workstream",
    "candidate_family",
    "candidate_name",
    "source_streams",
    "method",
    "target_volatility",
    "volatility_window",
    "exposure_cap",
    "exposure_floor",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "realized_volatility",
    "average_exposure",
    "max_exposure",
    "turnover_proxy",
    "delta_cagr_vs_qqq100",
    "delta_sharpe_vs_qqq100",
    "delta_max_drawdown_vs_qqq100",
    "delta_calmar_vs_qqq100",
    "delta_max_drawdown_vs_raw_high_growth",
    "in_sample_cagr",
    "out_of_sample_cagr",
    "out_of_sample_sharpe",
    "out_of_sample_calmar",
    "robustness_status",
    "final_candidate_status",
    "pass_fail_reason",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
REJECTED_COLUMNS = [
    "created_at",
    "candidate_name",
    "candidate_family",
    "rejection_status",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "rejection_reason",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
AUDIT_COLUMNS = ["audit_name", "audit_value", "details", *SAFETY_FLAGS.keys()]
SENSITIVITY_COLUMNS = [
    "created_at",
    "candidate_family",
    "source_stream",
    "target_volatility",
    "volatility_window",
    "exposure_cap",
    "candidate_count",
    "best_candidate",
    "best_cagr",
    "best_sharpe",
    "best_max_drawdown",
    "best_calmar",
    "strong_candidate_count",
    "fragile_candidate_count",
    *SAFETY_FLAGS.keys(),
]

STRONG_STATUS = "strong_vol_targeted_growth_candidate_research_only"
WATCH_STATUS = "vol_targeted_growth_watchlist_manual_review_required"
FRAGILE_STATUS = "vol_targeted_growth_fragile_or_low_return_rejected"
INCOMPLETE_STATUS = "vol_targeted_growth_research_incomplete_fewer_than_two_strong_candidates"
COMPLETE_STATUS = "vol_targeted_growth_research_two_or_more_strong_candidates_found"


@dataclass(frozen=True)
class ReturnPoint:
    date: str
    value: float


@dataclass(frozen=True)
class QQQReference:
    cagr: float
    sharpe: float
    max_drawdown: float
    calmar: float


@dataclass
class VolTargetedGrowthResult:
    output_paths: dict[str, Path]
    sprint_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    rejected_rows: list[dict[str, Any]]
    audit_rows: list[dict[str, Any]]
    sensitivity_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_research_sprint(root_dir: Path | str = ".") -> VolTargetedGrowthResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    streams = build_source_streams(inputs)
    qqq = qqq_reference(inputs["qqq100_metrics"], streams.get("qqq100"))
    raw_high_growth = metrics(streams.get("high_growth_balanced", []))
    candidate_rows = build_candidate_rows(created_at, streams, qqq, raw_high_growth)
    enforce_distinct_family_selection(candidate_rows)
    summary_rows = build_summary_rows(candidate_rows, qqq, inputs)
    rejected_rows = build_rejected_rows(candidate_rows)
    audit_rows = build_audit_rows(inputs, candidate_rows, qqq, raw_high_growth)
    sensitivity_rows = build_sensitivity_rows(created_at, candidate_rows)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["sprint"], SPRINT_COLUMNS, candidate_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["rejected"], REJECTED_COLUMNS, rejected_rows)
    write_rows(output_paths["audit"], AUDIT_COLUMNS, audit_rows)
    write_rows(output_paths["sensitivity"], SENSITIVITY_COLUMNS, sensitivity_rows)
    return VolTargetedGrowthResult(
        output_paths=output_paths,
        sprint_rows=candidate_rows,
        summary_rows=summary_rows,
        rejected_rows=rejected_rows,
        audit_rows=audit_rows,
        sensitivity_rows=sensitivity_rows,
        summary_lines=build_summary_lines(summary_rows, candidate_rows, output_paths),
    )


def show_vol_targeted_growth_research_sprint(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    sprint_path = root / OUTPUT_FILES["sprint"]
    if not summary_path.exists() or not sprint_path.exists():
        return 1, [
            "Volatility-targeted growth research sprint is missing.",
            "Run `python bot.py --vol-targeted-growth-research-sprint` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    sprint_rows = read_csv_rows(sprint_path)
    return 0, [
        "Volatility-targeted growth research sprint saved display. Research/report only; no execution approval.",
        f"final_research_status: {summary_value(summary_rows, 'final_research_status')}",
        f"strategies_tested: {summary_value(summary_rows, 'strategies_tested')}",
        f"candidate_families_tested: {summary_value(summary_rows, 'candidate_families_tested')}",
        f"strong_candidate_count: {summary_value(summary_rows, 'strong_candidate_count')}",
        f"final_candidate_1: {summary_value(summary_rows, 'final_candidate_1')}",
        f"final_candidate_2: {summary_value(summary_rows, 'final_candidate_2')}",
        "top_10_by_cagr: " + top_list(sprint_rows, "cagr", 10),
        "top_10_by_sharpe_calmar_balance: " + top_balance_list(sprint_rows, 10),
        "top_10_by_drawdown_improvement: " + top_list(sprint_rows, "delta_max_drawdown_vs_raw_high_growth", 10),
        f"rejected_or_fragile_summary: {summary_value(summary_rows, 'rejected_or_fragile_summary')}",
        f"blockers_if_fewer_than_two: {summary_value(summary_rows, 'blockers_if_fewer_than_two')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; high_growth_promotion_approved=false",
        "Warning: this sprint is saved-output research only; it does not create preview signals, order instructions, or scheduling approval.",
    ]


def build_source_streams(inputs: dict[str, list[dict[str, str]]]) -> dict[str, list[ReturnPoint]]:
    qqq = stream_from_rows(inputs["qqq100_stream"], "qqq100_recovered_reference_stream")
    high_growth_balanced = stream_from_rows(inputs["high_growth_streams"], "codex_broad_growth_balanced_breakout_control")
    high_growth_top1 = stream_from_rows(inputs["high_growth_streams"], "broad_growth_top1_reference")
    crypto_equal = stream_from_rows(inputs["crypto_streams"], "crypto_btc_eth_research_sleeve")
    defensive = stream_from_rows(inputs["sleeve_streams"], "qqq100_spy_sma200_regime_filter")
    multi = combine_streams([qqq, high_growth_balanced, crypto_equal], [0.70, 0.20, 0.05])
    balanced = combine_streams([qqq, defensive, high_growth_balanced, crypto_equal], [0.50, 0.20, 0.15, 0.10])
    return {
        "qqq100": qqq,
        "high_growth_balanced": high_growth_balanced,
        "high_growth_top1": high_growth_top1,
        "crypto_equal": crypto_equal,
        "defensive_qqq": defensive,
        "higher_growth_multi_sleeve": multi,
        "balanced_multi_sleeve": balanced,
        "vol_weighted_sleeves": dynamic_vol_weighted_stream(qqq, high_growth_balanced, crypto_equal),
    }


def build_candidate_rows(
    created_at: str,
    streams: dict[str, list[ReturnPoint]],
    qqq: QQQReference,
    raw_high_growth: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target_vols = [0.10, 0.15, 0.20, 0.25]
    windows = [20, 60, 120]
    for source_key, family, workstream, source_name in [
        ("qqq100", "qqq100_vol_targeted_growth", "Volatility Targeting Subagent", "QQQ100 recovered reference"),
        ("high_growth_balanced", "high_growth_balanced_vol_targeted", "Growth Momentum + Risk Overlay Subagent", "balanced high-growth sleeve"),
        ("high_growth_top1", "high_growth_concentrated_vol_targeted", "Growth Momentum + Risk Overlay Subagent", "broad Top1 high-growth reference"),
        ("higher_growth_multi_sleeve", "multi_sleeve_vol_targeted_growth", "Multi-Sleeve Risk Allocation Subagent", "70/20/5 higher-growth multi-sleeve"),
        ("balanced_multi_sleeve", "balanced_multi_sleeve_vol_targeted_growth", "Multi-Sleeve Risk Allocation Subagent", "balanced multi-sleeve research portfolio"),
    ]:
        for target in target_vols:
            for window in windows:
                series, exposures = volatility_target_stream(streams[source_key], target, window, exposure_cap=1.0, exposure_floor=0.0)
                rows.append(candidate_row(created_at, workstream, family, f"{source_key}_target_vol_{int(target*100)}_win_{window}_cap_1x", source_name, "volatility_targeting", target, window, 1.0, 0.0, series, exposures, qqq, raw_high_growth))
    for trigger in [-0.08, -0.12, -0.16]:
        series, exposures = drawdown_control_stream(streams["higher_growth_multi_sleeve"], trigger, reduced_exposure=0.50, recover_drawdown=-0.03)
        rows.append(candidate_row(created_at, "Drawdown Control Subagent", "multi_sleeve_drawdown_control_growth", f"higher_growth_multi_sleeve_drawdown_control_{int(abs(trigger)*100)}", "70/20/5 higher-growth multi-sleeve", "drawdown_control", None, None, 1.0, 0.5, series, exposures, qqq, raw_high_growth))
    rows.append(candidate_row(created_at, "Multi-Sleeve Risk Allocation Subagent", "volatility_weighted_sleeve_allocation", "qqq_high_growth_crypto_inverse_vol_weighted", "QQQ100 + high-growth + capped crypto saved streams", "inverse_volatility_sleeve_weighting", None, 60, 1.0, 0.0, streams["vol_weighted_sleeves"], [], qqq, raw_high_growth))
    return rows


def candidate_row(
    created_at: str,
    workstream: str,
    family: str,
    name: str,
    source: str,
    method: str,
    target_vol: float | None,
    window: int | None,
    cap: float,
    floor: float,
    series: list[ReturnPoint],
    exposures: list[float],
    qqq: QQQReference,
    raw_high_growth: dict[str, float],
) -> dict[str, Any]:
    full = metrics(series)
    split = split_metrics(series)
    avg_exposure = sum(exposures) / len(exposures) if exposures else 1.0
    max_exposure = max(exposures) if exposures else 1.0
    turnover_proxy = sum(abs(exposures[index] - exposures[index - 1]) for index in range(1, len(exposures))) if exposures else 0.0
    status, reason, robustness = classify_candidate(full, split, family, qqq, raw_high_growth, max_exposure)
    return {
        "created_at": created_at,
        "workstream": workstream,
        "candidate_family": family,
        "candidate_name": name,
        "source_streams": source,
        "method": method,
        "target_volatility": format_optional(target_vol),
        "volatility_window": format_optional(window),
        "exposure_cap": cap,
        "exposure_floor": floor,
        "cagr": format_metric(full["cagr"]),
        "sharpe": format_metric(full["sharpe"]),
        "max_drawdown": format_metric(full["max_drawdown"]),
        "calmar": format_metric(full["calmar"]),
        "realized_volatility": format_metric(full["realized_volatility"]),
        "average_exposure": format_metric(avg_exposure),
        "max_exposure": format_metric(max_exposure),
        "turnover_proxy": format_metric(turnover_proxy),
        "delta_cagr_vs_qqq100": format_metric(full["cagr"] - qqq.cagr),
        "delta_sharpe_vs_qqq100": format_metric(full["sharpe"] - qqq.sharpe),
        "delta_max_drawdown_vs_qqq100": format_metric(full["max_drawdown"] - qqq.max_drawdown),
        "delta_calmar_vs_qqq100": format_metric(full["calmar"] - qqq.calmar),
        "delta_max_drawdown_vs_raw_high_growth": format_metric(full["max_drawdown"] - raw_high_growth["max_drawdown"]),
        "in_sample_cagr": format_metric(split["in_sample"]["cagr"]),
        "out_of_sample_cagr": format_metric(split["out_of_sample"]["cagr"]),
        "out_of_sample_sharpe": format_metric(split["out_of_sample"]["sharpe"]),
        "out_of_sample_calmar": format_metric(split["out_of_sample"]["calmar"]),
        "robustness_status": robustness,
        "final_candidate_status": status,
        "pass_fail_reason": reason,
        "required_next_step": next_step_for_status(status),
        **SAFETY_FLAGS,
    }


def classify_candidate(
    full: dict[str, float],
    split: dict[str, dict[str, float]],
    family: str,
    qqq: QQQReference,
    raw_high_growth: dict[str, float],
    max_exposure: float,
) -> tuple[str, str, str]:
    if max_exposure > 1.0001:
        return FRAGILE_STATUS, "Rejected: hidden leverage/exposure above 1x is not allowed for this sprint.", "hidden_leverage_rejected"
    if "concentrated" in family:
        return FRAGILE_STATUS, "Rejected: concentrated Top1 source remains single-name/outlier fragile even after volatility targeting.", "single_name_concentration_rejected"
    if full["cagr"] < qqq.cagr + 2.0:
        return FRAGILE_STATUS, "Rejected: safer profile does not preserve enough growth versus QQQ100.", "smooth_low_return_rejected"
    if full["sharpe"] < qqq.sharpe + 0.10 or full["calmar"] < qqq.calmar + 0.15:
        return WATCH_STATUS, "Watchlist: growth is attractive, but risk-adjusted improvement is not strong enough.", "risk_adjusted_improvement_incomplete"
    if full["max_drawdown"] < raw_high_growth["max_drawdown"] + 10.0:
        return WATCH_STATUS, "Watchlist: drawdown improvement versus raw high-growth is too small.", "drawdown_control_incomplete"
    if split["out_of_sample"]["cagr"] < qqq.cagr * 0.75:
        return WATCH_STATUS, "Watchlist: out-of-sample CAGR is too weak versus QQQ100 reference.", "out_of_sample_growth_review_required"
    return STRONG_STATUS, "Passed saved-evidence screen: preserved growth while improving drawdown/risk-adjusted behavior without leverage.", "full_and_split_saved_evidence_supportive"


def enforce_distinct_family_selection(rows: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    ranked = sorted(rows, key=balance_score, reverse=True)
    for row in ranked:
        if row["final_candidate_status"] != STRONG_STATUS:
            continue
        family = row["candidate_family"]
        if family in seen:
            row["final_candidate_status"] = WATCH_STATUS
            row["pass_fail_reason"] = "Distinct-family rule: stronger variant from same family already selected."
            row["robustness_status"] = "duplicate_family_watchlist"
            row["required_next_step"] = next_step_for_status(WATCH_STATUS)
        else:
            seen.add(family)


def build_summary_rows(
    rows: list[dict[str, Any]],
    qqq: QQQReference,
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    strong = [row for row in rows if row["final_candidate_status"] == STRONG_STATUS]
    final_status = COMPLETE_STATUS if len(strong) >= 2 else INCOMPLETE_STATUS
    concrete = [row for row in rows if parse_float(row.get("cagr")) is not None]
    summary = [
        ("final_research_status", final_status, "Whether at least two distinct strong volatility-targeted growth families were found."),
        ("strategies_tested", str(len(concrete)), "Count of volatility-targeted or drawdown-controlled variants tested."),
        ("candidate_families_tested", str(len({row['candidate_family'] for row in concrete})), "Distinct candidate families represented."),
        ("strong_candidate_count", str(len(strong)), "Distinct strong candidates after family gating."),
        ("final_candidate_1", candidate_summary(strong, 0), "Top final strong candidate."),
        ("final_candidate_2", candidate_summary(strong, 1), "Second final strong candidate."),
        ("qqq100_reference", f"CAGR={qqq.cagr}; Sharpe={qqq.sharpe}; MaxDD={qqq.max_drawdown}; Calmar={qqq.calmar}", "Recovered QQQ100 reference used for deltas."),
        ("top_10_by_cagr", top_list(rows, "cagr", 10), "Top variants by CAGR."),
        ("top_10_by_sharpe_calmar_balance", top_balance_list(rows, 10), "Top variants by Sharpe/Calmar balance."),
        ("top_10_by_drawdown_improvement", top_list(rows, "delta_max_drawdown_vs_raw_high_growth", 10), "Top variants by drawdown improvement versus raw high-growth."),
        ("rejected_or_fragile_summary", rejected_summary(rows), "Rejected or fragile candidates."),
        ("blockers_if_fewer_than_two", "none" if len(strong) >= 2 else "need_more_distinct_vol_targeted_growth_families", "Exact blocker if fewer than two strong candidates are found."),
        ("recommended_next_step", "manual_review_vol_targeted_growth_candidates_before_any_preview_design", "Next step remains manual review and report-only."),
        ("saved_input_files_present", str(sum(1 for value in inputs.values() if value)), "Count of saved input CSVs found."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in summary]


def build_rejected_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rejected = [row for row in rows if row["final_candidate_status"] in {FRAGILE_STATUS, WATCH_STATUS}]
    return [
        {
            "created_at": row["created_at"],
            "candidate_name": row["candidate_name"],
            "candidate_family": row["candidate_family"],
            "rejection_status": row["final_candidate_status"],
            "cagr": row["cagr"],
            "sharpe": row["sharpe"],
            "max_drawdown": row["max_drawdown"],
            "calmar": row["calmar"],
            "rejection_reason": row["pass_fail_reason"],
            "required_next_step": row["required_next_step"],
            **SAFETY_FLAGS,
        }
        for row in rejected
    ]


def build_audit_rows(
    inputs: dict[str, list[dict[str, str]]],
    rows: list[dict[str, Any]],
    qqq: QQQReference,
    raw_high_growth: dict[str, float],
) -> list[dict[str, Any]]:
    audit = [
        ("subagent_workstreams", "7", "Volatility Targeting Subagent, Drawdown Control Subagent, Growth Momentum + Risk Overlay Subagent, Multi-Sleeve Risk Allocation Subagent, Backtest Engineering Subagent, Robustness/Audit Subagent, Evidence/Reporting Subagent."),
        ("saved_data_only", "true", "All candidates are generated from existing saved return streams."),
        ("qqq100_reference", f"{qqq}", "Recovered QQQ100 reference used for comparison."),
        ("raw_high_growth_reference", f"{raw_high_growth}", "Raw balanced high-growth sleeve reference used for drawdown improvement."),
        ("hidden_leverage_policy", "max_exposure_above_1x_rejected", "This sprint does not allow hidden leverage dependency."),
        ("single_name_policy", "concentrated_top1_fragile_even_if_vol_targeted", "Single-name/outlier dependency is excluded from strong status."),
    ]
    for status in sorted({row["final_candidate_status"] for row in rows}):
        audit.append((f"status_count_{status}", str(sum(1 for row in rows if row["final_candidate_status"] == status)), "Candidate status count."))
    for name, path in INPUT_FILES.items():
        audit.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    return [{"audit_name": name, "audit_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in audit]


def build_sensitivity_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["candidate_family"]), str(row["source_streams"]), str(row["method"]))
        groups.setdefault(key, []).append(row)
    sensitivity = []
    for (family, source, method), group in sorted(groups.items()):
        best = sorted(group, key=balance_score, reverse=True)[0]
        sensitivity.append(
            {
                "created_at": created_at,
                "candidate_family": family,
                "source_stream": source,
                "target_volatility": "varied",
                "volatility_window": "varied",
                "exposure_cap": "1.0",
                "candidate_count": len(group),
                "best_candidate": best["candidate_name"],
                "best_cagr": best["cagr"],
                "best_sharpe": best["sharpe"],
                "best_max_drawdown": best["max_drawdown"],
                "best_calmar": best["calmar"],
                "strong_candidate_count": sum(1 for row in group if row["final_candidate_status"] == STRONG_STATUS),
                "fragile_candidate_count": sum(1 for row in group if row["final_candidate_status"] == FRAGILE_STATUS),
                **SAFETY_FLAGS,
            }
        )
    return sensitivity


def qqq_reference(rows: list[dict[str, str]], fallback_stream: list[ReturnPoint] | None) -> QQQReference:
    row = rows[0] if rows else {}
    fallback = metrics(fallback_stream or [])
    return QQQReference(
        cagr=parse_float(row.get("cagr")) or fallback["cagr"],
        sharpe=parse_float(row.get("sharpe")) or fallback["sharpe"],
        max_drawdown=parse_float(row.get("max_drawdown")) or fallback["max_drawdown"],
        calmar=parse_float(row.get("calmar")) or fallback["calmar"],
    )


def stream_from_rows(rows: list[dict[str, str]], candidate_name: str) -> list[ReturnPoint]:
    stream = []
    for row in rows:
        if row.get("candidate_name") != candidate_name:
            continue
        value = parse_float(row.get("daily_strategy_return")) or parse_float(row.get("daily_return")) or 0.0
        stream.append(ReturnPoint(row.get("date", ""), value))
    return sorted([point for point in stream if point.date], key=lambda item: item.date)


def combine_streams(streams: list[list[ReturnPoint]], weights: list[float]) -> list[ReturnPoint]:
    maps = [{point.date: point.value for point in stream} for stream in streams if stream]
    if not maps:
        return []
    dates = sorted(set.intersection(*(set(mapping) for mapping in maps)))
    return [ReturnPoint(date, sum(weight * mapping[date] for weight, mapping in zip(weights, maps))) for date in dates]


def dynamic_vol_weighted_stream(
    qqq: list[ReturnPoint],
    high_growth: list[ReturnPoint],
    crypto: list[ReturnPoint],
    window: int = 60,
) -> list[ReturnPoint]:
    maps = [{point.date: point.value for point in stream} for stream in [qqq, high_growth, crypto]]
    dates = sorted(set.intersection(*(set(mapping) for mapping in maps)))
    out = []
    history = [[], [], []]
    base_caps = [0.80, 0.35, 0.10]
    total_risk_budget = 0.95
    for date in dates:
        weights = [0.70, 0.20, 0.05]
        if all(len(values) >= window for values in history):
            inv_vol = []
            for values in history:
                vol = realized_volatility(values[-window:])
                inv_vol.append(0.0 if vol <= 0 else 1.0 / vol)
            total = sum(inv_vol)
            if total > 0:
                weights = [min(cap, total_risk_budget * value / total) for cap, value in zip(base_caps, inv_vol)]
        out.append(ReturnPoint(date, sum(weight * mapping[date] for weight, mapping in zip(weights, maps))))
        for index, mapping in enumerate(maps):
            history[index].append(mapping[date])
    return out


def volatility_target_stream(
    stream: list[ReturnPoint],
    target_volatility: float,
    window: int,
    exposure_cap: float,
    exposure_floor: float,
) -> tuple[list[ReturnPoint], list[float]]:
    out = []
    exposures = []
    history: list[float] = []
    for point in stream:
        exposure = 1.0
        if len(history) >= window:
            vol = realized_volatility(history[-window:])
            exposure = exposure_cap if vol <= 0 else target_volatility / vol
            exposure = max(exposure_floor, min(exposure_cap, exposure))
        out.append(ReturnPoint(point.date, point.value * exposure))
        exposures.append(exposure)
        history.append(point.value)
    return out, exposures


def drawdown_control_stream(
    stream: list[ReturnPoint],
    trigger_drawdown: float,
    reduced_exposure: float,
    recover_drawdown: float,
) -> tuple[list[ReturnPoint], list[float]]:
    out = []
    exposures = []
    equity = 1.0
    peak = 1.0
    exposure = 1.0
    for point in stream:
        current_drawdown = equity / peak - 1.0
        if current_drawdown <= trigger_drawdown:
            exposure = reduced_exposure
        elif current_drawdown >= recover_drawdown:
            exposure = 1.0
        out.append(ReturnPoint(point.date, point.value * exposure))
        exposures.append(exposure)
        equity *= 1.0 + point.value * exposure
        peak = max(peak, equity)
    return out, exposures


def metrics(stream: list[ReturnPoint]) -> dict[str, float]:
    if not stream:
        return {"cagr": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "calmar": 0.0, "realized_volatility": 0.0}
    returns = [point.value for point in stream]
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1.0)
    years = len(returns) / 252.0
    cagr = ((equity ** (1.0 / years)) - 1.0) * 100.0 if years > 0 and equity > 0 else -100.0
    vol = realized_volatility(returns) * 100.0
    daily_vol = standard_deviation(returns)
    daily_mean = sum(returns) / len(returns)
    sharpe = (daily_mean / daily_vol) * math.sqrt(252.0) if daily_vol > 0 else 0.0
    maxdd_pct = max_drawdown * 100.0
    calmar = cagr / abs(maxdd_pct) if maxdd_pct < 0 else 0.0
    return {"cagr": cagr, "sharpe": sharpe, "max_drawdown": maxdd_pct, "calmar": calmar, "realized_volatility": vol}


def split_metrics(stream: list[ReturnPoint]) -> dict[str, dict[str, float]]:
    if len(stream) < 20:
        empty = metrics(stream)
        return {"in_sample": empty, "out_of_sample": empty}
    split_index = int(len(stream) * 0.60)
    return {"in_sample": metrics(stream[:split_index]), "out_of_sample": metrics(stream[split_index:])}


def realized_volatility(values: list[float]) -> float:
    return standard_deviation(values) * math.sqrt(252.0)


def standard_deviation(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def next_step_for_status(status: str) -> str:
    if status == STRONG_STATUS:
        return "manual_review_vol_targeted_growth_candidate_before_any_preview_design"
    if status == WATCH_STATUS:
        return "review_parameter_sensitivity_and_oos_robustness_before_label_change"
    return "keep_rejected_or_fragile_research_only"


def build_summary_lines(
    summary_rows: list[dict[str, Any]],
    sprint_rows: list[dict[str, Any]],
    output_paths: dict[str, Path],
) -> list[str]:
    return [
        "Volatility-targeted growth research sprint complete. Saved-output research only; no execution, orders, or scheduling approved.",
        f"final_research_status={summary_value(summary_rows, 'final_research_status')}",
        f"strategies_tested={summary_value(summary_rows, 'strategies_tested')}",
        f"candidate_families_tested={summary_value(summary_rows, 'candidate_families_tested')}",
        f"strong_candidate_count={summary_value(summary_rows, 'strong_candidate_count')}",
        f"final_candidate_1={summary_value(summary_rows, 'final_candidate_1')}",
        f"final_candidate_2={summary_value(summary_rows, 'final_candidate_2')}",
        "top_10_by_cagr=" + top_list(sprint_rows, "cagr", 10),
        "top_10_by_sharpe_calmar_balance=" + top_balance_list(sprint_rows, 10),
        "top_10_by_drawdown_improvement=" + top_list(sprint_rows, "delta_max_drawdown_vs_raw_high_growth", 10),
        f"rejected_or_fragile_summary={summary_value(summary_rows, 'rejected_or_fragile_summary')}",
        f"blockers_if_fewer_than_two={summary_value(summary_rows, 'blockers_if_fewer_than_two')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['sprint']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; high_growth_promotion_approved=false",
    ]


def candidate_summary(rows: list[dict[str, Any]], index: int) -> str:
    ranked = sorted(rows, key=balance_score, reverse=True)
    if index >= len(ranked):
        return "unavailable"
    row = ranked[index]
    return f"{row['candidate_name']} ({row['candidate_family']}): CAGR={row['cagr']}; Sharpe={row['sharpe']}; MaxDD={row['max_drawdown']}; Calmar={row['calmar']}; Vol={row['realized_volatility']}"


def rejected_summary(rows: list[dict[str, Any]]) -> str:
    rejected = [row for row in rows if row["final_candidate_status"] in {FRAGILE_STATUS, WATCH_STATUS}]
    if not rejected:
        return "none"
    return "; ".join(f"{row['candidate_name']}={row['final_candidate_status']}" for row in rejected[:10])


def top_list(rows: list[dict[str, Any]], field: str, limit: int) -> str:
    ranked = sorted([row for row in rows if parse_float(row.get(field)) is not None], key=lambda row: parse_float(row.get(field)) or -9999.0, reverse=True)
    return "; ".join(f"{row['candidate_name']}={row[field]}" for row in ranked[:limit]) or "unavailable"


def top_balance_list(rows: list[dict[str, Any]], limit: int) -> str:
    ranked = sorted(rows, key=balance_score, reverse=True)
    return "; ".join(f"{row['candidate_name']}={round(balance_score(row), 4)}" for row in ranked[:limit] if balance_score(row) > -1000.0) or "unavailable"


def balance_score(row: dict[str, Any]) -> float:
    cagr = parse_float(row.get("cagr"))
    sharpe = parse_float(row.get("sharpe"))
    calmar = parse_float(row.get("calmar"))
    maxdd = parse_float(row.get("max_drawdown"))
    if cagr is None or sharpe is None or calmar is None or maxdd is None:
        return -9999.0
    drawdown_penalty = max(0.0, abs(maxdd) - 30.0) * 0.05
    return sharpe + calmar + cagr / 100.0 - drawdown_penalty


def parse_float(value: Any) -> float | None:
    try:
        text = str(value).strip().replace("%", "")
        if not text or "missing" in text.lower() or text.lower() == "nan":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def format_metric(value: float | None) -> str:
    return "missing_saved_metrics" if value is None else str(round(value, 4))


def format_optional(value: float | int | None) -> str:
    return "not_applicable" if value is None else str(value)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
