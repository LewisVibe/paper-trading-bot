"""Saved-output QQQ100 versus volatility risk/reward comparison.

This report fills one evidence item for the volatility seed-change evidence
pack. It compares saved QQQ100 benchmark metrics against the saved
volatility-targeted 15/20 candidate metrics. It does not refresh market data,
read broker positions, change the seed, create order instructions, or approve
execution.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_risk_reward_evidence_created_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_risk_reward_evidence_blocked_missing_saved_metrics"
NEXT_STEP = "manual_review_risk_reward_source_mismatch_before_seed_change_evidence_update"

OUTPUT_FILES = {
    "comparison": Path("data/vol_targeted_growth_seed_change_risk_reward_comparison.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_risk_reward_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_risk_reward_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_risk_reward_blockers.csv"),
}

INPUT_FILES = {
    "qqq100_benchmark_inputs_summary": Path("data/qqq100_benchmark_inputs_summary.csv"),
    "qqq100_preview_candidate_readiness_summary": Path("data/qqq100_preview_candidate_readiness_summary.csv"),
    "vol_targeted_growth_nearby_variants_summary": Path("data/vol_targeted_growth_nearby_variants_summary.csv"),
    "vol_targeted_growth_manual_review_summary": Path("data/vol_targeted_growth_manual_review_summary.csv"),
    "seed_change_evidence_summary": Path("data/vol_targeted_growth_seed_change_evidence_summary.csv"),
}

METRICS = ["CAGR", "Sharpe", "MaxDD", "Calmar"]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "risk_reward_comparison_only": True,
    "proposal_only": True,
    "preview_only": True,
    "seed_changed": False,
    "seed_change_proposal_created": False,
    "qqq100_displacement_requested": False,
    "qqq100_displacement_approved": False,
    "vol_targeted_seed_approved": False,
    "action_preview_added": False,
    "order_instructions_created": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_read_now": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "paper_live_candidate_approved": False,
    "vol_targeted_paper_live_candidate_approved": False,
    "preview_implementation_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

COMPARISON_COLUMNS = [
    "created_at",
    "metric_name",
    "qqq100_value",
    "vol_targeted_value",
    "delta_vol_minus_qqq100",
    "metric_winner",
    "comparison_status",
    "source_warning",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthSeedChangeRiskRewardComparisonResult:
    output_paths: dict[str, Path]
    comparison_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_risk_reward_comparison(root_dir: Path | str = ".") -> VolTargetedGrowthSeedChangeRiskRewardComparisonResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    qqq_metrics = qqq100_metrics(inputs)
    vol_metrics = volatility_metrics(inputs)
    final_status = FINAL_STATUS if has_metrics(qqq_metrics) and has_metrics(vol_metrics) else BLOCKED_STATUS
    comparison_rows = build_comparison_rows(created_at, qqq_metrics, vol_metrics, final_status)
    summary_rows = build_summary_rows(inputs, comparison_rows, qqq_metrics, vol_metrics, final_status)
    evidence_rows = build_evidence_rows(inputs, qqq_metrics, vol_metrics)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["comparison"], COMPARISON_COLUMNS, comparison_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeRiskRewardComparisonResult(
        output_paths=output_paths,
        comparison_rows=comparison_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_risk_reward_comparison(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-risk-reward-comparison` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change risk/reward comparison saved display. Evidence only; no seed change approved.",
        f"final_risk_reward_status: {summary_value(rows, 'final_risk_reward_status')}",
        f"metric_win_summary: {summary_value(rows, 'metric_win_summary')}",
        f"qqq100_metrics: {summary_value(rows, 'qqq100_metrics')}",
        f"vol_targeted_metrics: {summary_value(rows, 'vol_targeted_metrics')}",
        f"source_warning: {summary_value(rows, 'source_warning')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def qqq100_metrics(inputs: dict[str, list[dict[str, str]]]) -> dict[str, float]:
    value = summary_value(inputs["qqq100_benchmark_inputs_summary"], "saved_benchmark_metrics")
    if not value:
        value = extract_metric_text(summary_value(inputs["qqq100_preview_candidate_readiness_summary"], "strongest_evidence_for_preview_discussion"))
    return parse_metrics(value)


def volatility_metrics(inputs: dict[str, list[dict[str, str]]]) -> dict[str, float]:
    value = summary_value(inputs["vol_targeted_growth_nearby_variants_summary"], "preferred_candidate")
    if not value:
        value = summary_value(inputs["vol_targeted_growth_manual_review_summary"], "multi_sleeve_candidate")
    return parse_metrics(value)


def build_comparison_rows(created_at: str, qqq: dict[str, float], vol: dict[str, float], final_status: str) -> list[dict[str, Any]]:
    rows = []
    for metric in METRICS:
        q_value = qqq.get(metric)
        v_value = vol.get(metric)
        delta = None if q_value is None or v_value is None else v_value - q_value
        winner = metric_winner(metric, q_value, v_value)
        rows.append(
            {
                "created_at": created_at,
                "metric_name": metric,
                "qqq100_value": format_metric(q_value),
                "vol_targeted_value": format_metric(v_value),
                "delta_vol_minus_qqq100": format_metric(delta),
                "metric_winner": winner,
                "comparison_status": "saved_metric_comparison_available" if final_status == FINAL_STATUS else "missing_saved_metric",
                "source_warning": source_warning(),
                "interpretation": interpretation_for(metric, winner, delta),
                "required_next_step": NEXT_STEP,
                **SAFETY_FLAGS,
            }
        )
    return rows


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    comparison_rows: list[dict[str, Any]],
    qqq: dict[str, float],
    vol: dict[str, float],
    final_status: str,
) -> list[dict[str, Any]]:
    vol_wins = sum(1 for row in comparison_rows if row.get("metric_winner") == "vol_targeted_growth")
    rows = [
        ("final_risk_reward_status", final_status, "Saved risk/reward comparison status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current paper-live seed remains unchanged."),
        ("candidate_under_review", SELECTED_CANDIDATE, "Volatility-targeted candidate under manual review."),
        ("qqq100_metrics", metric_line(qqq), "Saved QQQ100 benchmark metrics."),
        ("vol_targeted_metrics", metric_line(vol), "Saved volatility-targeted candidate metrics."),
        ("metric_win_summary", f"vol_targeted_wins={vol_wins}; total_metrics={len(comparison_rows)}", "Winner count across CAGR, Sharpe, MaxDD, and Calmar."),
        ("source_warning", source_warning(), "Metric sources are saved outputs but not a fresh apples-to-apples regeneration."),
        ("evidence_pack_context", summary_value(inputs["seed_change_evidence_summary"], "final_evidence_pack_status") or "missing_seed_change_evidence_pack", "Saved evidence-pack context."),
        ("seed_change_readiness", "not_ready_metric_advantage_requires_source_review", "Metric advantage alone does not approve seed displacement."),
        ("largest_blocker", "risk_reward_source_mismatch_and_missing_seed_change_evidence", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], qqq: dict[str, float], vol: dict[str, float]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("qqq100_metric_source", metric_line(qqq), "Saved QQQ100 benchmark source."))
    rows.append(("vol_targeted_metric_source", metric_line(vol), "Saved volatility-targeted candidate source."))
    rows.append(("broker_read_now", "false", "This comparison reads saved outputs only and does not call Alpaca."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent seed.", NEXT_STEP),
        ("source_mismatch_manual_review_required", "blocked", "high", source_warning(), NEXT_STEP),
        ("metric_advantage_not_sufficient", "blocked", "critical", "Saved metric advantage does not replace component, stress, cost, split, exposure, and proposal evidence.", "complete_seed_change_evidence_pack"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("saved_metrics_missing", "blocked", "critical", "Required saved QQQ100 or volatility metrics are missing.", "restore_saved_metrics_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth risk/reward comparison complete. Evidence only; no seed change approved.",
        f"final_risk_reward_status={summary_value(summary_rows, 'final_risk_reward_status')}",
        f"metric_win_summary={summary_value(summary_rows, 'metric_win_summary')}",
        f"qqq100_metrics={summary_value(summary_rows, 'qqq100_metrics')}",
        f"vol_targeted_metrics={summary_value(summary_rows, 'vol_targeted_metrics')}",
        f"source_warning={summary_value(summary_rows, 'source_warning')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_comparison={output_paths['comparison']}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def metric_winner(metric: str, qqq: float | None, vol: float | None) -> str:
    if qqq is None or vol is None:
        return "unavailable"
    if metric == "MaxDD":
        return "vol_targeted_growth" if vol > qqq else "qqq100" if qqq > vol else "tie"
    return "vol_targeted_growth" if vol > qqq else "qqq100" if qqq > vol else "tie"


def interpretation_for(metric: str, winner: str, delta: float | None) -> str:
    if winner == "unavailable" or delta is None:
        return f"{metric} comparison unavailable from saved evidence."
    if winner == "vol_targeted_growth":
        return f"Volatility candidate leads on saved {metric}, but source review is required before seed-change evidence can be complete."
    if winner == "qqq100":
        return f"QQQ100 leads on saved {metric}; this weighs against displacement."
    return f"Saved {metric} is tied."


def source_warning() -> str:
    return "saved_metric_sources_not_fresh_apples_to_apples_regeneration_manual_review_required"


def parse_metrics(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for metric in METRICS:
        match = re.search(rf"{metric}=(-?\d+(?:\.\d+)?)", text or "")
        if match:
            metrics[metric] = float(match.group(1))
    return metrics


def extract_metric_text(text: str) -> str:
    return (text or "").replace("_", " ")


def has_metrics(metrics: dict[str, float]) -> bool:
    return all(metric in metrics for metric in METRICS)


def metric_line(metrics: dict[str, float]) -> str:
    return "; ".join(f"{metric}={format_metric(metrics.get(metric))}" for metric in METRICS)


def format_metric(value: float | None) -> str:
    return "unavailable" if value is None else str(round(value, 4))


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


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""
