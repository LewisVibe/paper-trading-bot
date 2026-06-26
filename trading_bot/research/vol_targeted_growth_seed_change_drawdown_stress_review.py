"""Saved-output drawdown/stress review for volatility seed-change evidence.

This report fills the drawdown/stress evidence item using saved QQQ100 and
volatility-targeted metrics only. It does not refresh market data, read broker
positions, change the seed, create order instructions, or approve execution.
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
FINAL_STATUS = "vol_targeted_growth_drawdown_stress_evidence_created_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_drawdown_stress_evidence_blocked_missing_saved_drawdown_metrics"
NEXT_STEP = "manual_review_drawdown_stress_source_limits_before_seed_change_evidence_update"

OUTPUT_FILES = {
    "review": Path("data/vol_targeted_growth_seed_change_drawdown_stress_review.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_drawdown_stress_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_drawdown_stress_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_drawdown_stress_blockers.csv"),
}

INPUT_FILES = {
    "qqq100_benchmark_inputs_summary": Path("data/qqq100_benchmark_inputs_summary.csv"),
    "qqq100_preview_candidate_readiness_summary": Path("data/qqq100_preview_candidate_readiness_summary.csv"),
    "vol_targeted_growth_nearby_variants_summary": Path("data/vol_targeted_growth_nearby_variants_summary.csv"),
    "vol_targeted_growth_manual_review_summary": Path("data/vol_targeted_growth_manual_review_summary.csv"),
    "vol_targeted_growth_robustness_checkpoint_summary": Path("data/vol_targeted_growth_robustness_checkpoint_summary.csv"),
    "seed_change_evidence_summary": Path("data/vol_targeted_growth_seed_change_evidence_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "drawdown_stress_review_only": True,
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

REVIEW_COLUMNS = [
    "created_at",
    "review_item",
    "review_status",
    "qqq100_max_drawdown",
    "vol_targeted_max_drawdown",
    "drawdown_delta_vol_minus_qqq100",
    "drawdown_winner",
    "stress_context",
    "source_warning",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthSeedChangeDrawdownStressReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_drawdown_stress_review(root_dir: Path | str = ".") -> VolTargetedGrowthSeedChangeDrawdownStressReviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    qqq_dd = qqq100_maxdd(inputs)
    vol_dd = volatility_maxdd(inputs)
    final_status = FINAL_STATUS if qqq_dd is not None and vol_dd is not None else BLOCKED_STATUS
    review_rows = build_review_rows(created_at, inputs, qqq_dd, vol_dd, final_status)
    summary_rows = build_summary_rows(inputs, review_rows, qqq_dd, vol_dd, final_status)
    evidence_rows = build_evidence_rows(inputs, qqq_dd, vol_dd)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeDrawdownStressReviewResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_drawdown_stress_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-drawdown-stress-review` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change drawdown/stress review saved display. Evidence only; no seed change approved.",
        f"final_drawdown_stress_status: {summary_value(rows, 'final_drawdown_stress_status')}",
        f"drawdown_comparison: {summary_value(rows, 'drawdown_comparison')}",
        f"drawdown_winner: {summary_value(rows, 'drawdown_winner')}",
        f"stress_review_status: {summary_value(rows, 'stress_review_status')}",
        f"source_warning: {summary_value(rows, 'source_warning')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_review_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, str]]],
    qqq_dd: float | None,
    vol_dd: float | None,
    final_status: str,
) -> list[dict[str, Any]]:
    delta = None if qqq_dd is None or vol_dd is None else vol_dd - qqq_dd
    winner = drawdown_winner(qqq_dd, vol_dd)
    status = "saved_drawdown_metric_comparison_available" if final_status == FINAL_STATUS else "missing_saved_drawdown_metric"
    return [
        review_row(created_at, "max_drawdown_metric", status, qqq_dd, vol_dd, delta, winner, robustness_context(inputs), source_warning(), interpretation_for_drawdown(winner, delta), NEXT_STEP),
        review_row(created_at, "stress_context", "stress_review_manual_review_required", qqq_dd, vol_dd, delta, winner, robustness_context(inputs), source_warning(), "Saved robustness context exists, but this is not a fresh stress regeneration or full drawdown-window analysis.", NEXT_STEP),
        review_row(created_at, "execution_boundary", "execution_blocked", qqq_dd, vol_dd, delta, winner, "no execution context", "none", "Drawdown evidence does not approve seed change, order instructions, execution, or scheduling.", "keep_all_approval_flags_false"),
    ]


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    review_rows: list[dict[str, Any]],
    qqq_dd: float | None,
    vol_dd: float | None,
    final_status: str,
) -> list[dict[str, Any]]:
    delta = None if qqq_dd is None or vol_dd is None else vol_dd - qqq_dd
    winner = drawdown_winner(qqq_dd, vol_dd)
    rows = [
        ("final_drawdown_stress_status", final_status, "Saved drawdown/stress comparison status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current paper-live seed remains unchanged."),
        ("candidate_under_review", SELECTED_CANDIDATE, "Volatility-targeted candidate under manual review."),
        ("drawdown_comparison", f"qqq100_MaxDD={format_metric(qqq_dd)}; vol_targeted_MaxDD={format_metric(vol_dd)}; delta={format_metric(delta)}", "Less negative max drawdown is better."),
        ("drawdown_winner", winner, "Winner by saved max drawdown metric."),
        ("stress_review_status", "manual_review_required_not_fresh_stress_regeneration", "Saved robustness context exists but stress evidence is not complete."),
        ("robustness_context", robustness_context(inputs), "Saved robustness context where available."),
        ("source_warning", source_warning(), "Metric sources are saved outputs, not a fresh apples-to-apples stress run."),
        ("evidence_pack_context", summary_value(inputs["seed_change_evidence_summary"], "final_evidence_pack_status") or "missing_seed_change_evidence_pack", "Saved evidence-pack context."),
        ("largest_blocker", "drawdown_metric_favorable_but_stress_window_evidence_incomplete" if winner == "vol_targeted_growth" else "drawdown_stress_evidence_incomplete", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], qqq_dd: float | None, vol_dd: float | None) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("qqq100_saved_max_drawdown", format_metric(qqq_dd), "Saved QQQ100 MaxDD source."))
    rows.append(("vol_targeted_saved_max_drawdown", format_metric(vol_dd), "Saved volatility candidate MaxDD source."))
    rows.append(("broker_read_now", "false", "This review reads saved outputs only and does not call Alpaca."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent seed.", NEXT_STEP),
        ("stress_window_evidence_incomplete", "blocked", "high", "Saved MaxDD comparison is not a full fresh drawdown-window/stress regeneration.", NEXT_STEP),
        ("metric_advantage_not_sufficient", "blocked", "critical", "Drawdown evidence alone does not replace component, cost, split, exposure, and proposal evidence.", "complete_seed_change_evidence_pack"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("saved_drawdown_metrics_missing", "blocked", "critical", "Required saved QQQ100 or volatility drawdown metrics are missing.", "restore_saved_drawdown_metrics_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth drawdown/stress review complete. Evidence only; no seed change approved.",
        f"final_drawdown_stress_status={summary_value(summary_rows, 'final_drawdown_stress_status')}",
        f"drawdown_comparison={summary_value(summary_rows, 'drawdown_comparison')}",
        f"drawdown_winner={summary_value(summary_rows, 'drawdown_winner')}",
        f"stress_review_status={summary_value(summary_rows, 'stress_review_status')}",
        f"source_warning={summary_value(summary_rows, 'source_warning')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_review={output_paths['review']}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def qqq100_maxdd(inputs: dict[str, list[dict[str, str]]]) -> float | None:
    value = summary_value(inputs["qqq100_benchmark_inputs_summary"], "saved_benchmark_metrics")
    if not value:
        value = (summary_value(inputs["qqq100_preview_candidate_readiness_summary"], "strongest_evidence_for_preview_discussion") or "").replace("_", " ")
    return parse_metric(value, "MaxDD")


def volatility_maxdd(inputs: dict[str, list[dict[str, str]]]) -> float | None:
    value = summary_value(inputs["vol_targeted_growth_nearby_variants_summary"], "preferred_candidate")
    if not value:
        value = summary_value(inputs["vol_targeted_growth_manual_review_summary"], "multi_sleeve_candidate")
    return parse_metric(value, "MaxDD")


def robustness_context(inputs: dict[str, list[dict[str, str]]]) -> str:
    status = summary_value(inputs["vol_targeted_growth_robustness_checkpoint_summary"], "final_robustness_status")
    if not status:
        status = summary_value(inputs["vol_targeted_growth_robustness_checkpoint_summary"], "final_checkpoint_status")
    return status or "missing_saved_robustness_context"


def drawdown_winner(qqq_dd: float | None, vol_dd: float | None) -> str:
    if qqq_dd is None or vol_dd is None:
        return "unavailable"
    if vol_dd > qqq_dd:
        return "vol_targeted_growth"
    if qqq_dd > vol_dd:
        return "qqq100"
    return "tie"


def interpretation_for_drawdown(winner: str, delta: float | None) -> str:
    if winner == "vol_targeted_growth":
        return f"Volatility candidate has less severe saved MaxDD by {format_metric(delta)} percentage points, but full stress-window evidence remains incomplete."
    if winner == "qqq100":
        return "QQQ100 has less severe saved MaxDD; this weighs against displacement."
    if winner == "tie":
        return "Saved MaxDD is tied."
    return "Saved drawdown comparison is unavailable."


def source_warning() -> str:
    return "saved_drawdown_metric_not_fresh_apples_to_apples_stress_regeneration_manual_review_required"


def review_row(
    created_at: str,
    item: str,
    status: str,
    qqq_dd: float | None,
    vol_dd: float | None,
    delta: float | None,
    winner: str,
    stress_context: str,
    warning: str,
    interpretation: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "review_item": item,
        "review_status": status,
        "qqq100_max_drawdown": format_metric(qqq_dd),
        "vol_targeted_max_drawdown": format_metric(vol_dd),
        "drawdown_delta_vol_minus_qqq100": format_metric(delta),
        "drawdown_winner": winner,
        "stress_context": stress_context,
        "source_warning": warning,
        "interpretation": interpretation,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def parse_metric(text: str, metric: str) -> float | None:
    match = re.search(rf"{metric}=(-?\d+(?:\.\d+)?)", text or "")
    return float(match.group(1)) if match else None


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
