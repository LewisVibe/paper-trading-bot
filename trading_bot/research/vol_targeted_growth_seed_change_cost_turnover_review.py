"""Saved-output cost/turnover review for volatility seed-change evidence."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_cost_turnover_evidence_created_manual_review_required"
NEXT_STEP = "manual_review_cost_turnover_source_limits_before_seed_change_evidence_update"

OUTPUT_FILES = {
    "review": Path("data/vol_targeted_growth_seed_change_cost_turnover_review.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_cost_turnover_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_cost_turnover_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_cost_turnover_blockers.csv"),
}

INPUT_FILES = {
    "robustness_summary": Path("data/vol_targeted_growth_robustness_checkpoint_summary.csv"),
    "robustness_checkpoint": Path("data/vol_targeted_growth_robustness_checkpoint.csv"),
    "nearby_variants_summary": Path("data/vol_targeted_growth_nearby_variants_summary.csv"),
    "manual_review_summary": Path("data/vol_targeted_growth_manual_review_summary.csv"),
    "seed_change_evidence_summary": Path("data/vol_targeted_growth_seed_change_evidence_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "cost_turnover_review_only": True,
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
    "candidate_name",
    "saved_evidence",
    "source_warning",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthSeedChangeCostTurnoverReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_cost_turnover_review(root_dir: Path | str = ".") -> VolTargetedGrowthSeedChangeCostTurnoverReviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    review_rows = build_review_rows(created_at, inputs)
    summary_rows = build_summary_rows(inputs)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeCostTurnoverReviewResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_cost_turnover_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-cost-turnover-review` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change cost/turnover review saved display. Evidence only; no seed change approved.",
        f"final_cost_turnover_status: {summary_value(rows, 'final_cost_turnover_status')}",
        f"cost_turnover_review_status: {summary_value(rows, 'cost_turnover_review_status')}",
        f"source_warning: {summary_value(rows, 'source_warning')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_review_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        (
            "saved_cost_turnover_metric_availability",
            "cost_turnover_exact_metrics_missing_manual_review_required",
            saved_cost_turnover_context(inputs),
            source_warning(),
            "Saved volatility branch summaries do not provide a fresh apples-to-apples turnover/cost stress row for the seed-change proposal.",
            NEXT_STEP,
        ),
        (
            "cost_turnover_boundary",
            "cost_turnover_review_required",
            "volatility targeting may rebalance exposure; exact implementation turnover needs separate proof",
            source_warning(),
            "Metric advantage is not enough until turnover, transaction-cost, and sleeve-rebalance assumptions are reviewed.",
            NEXT_STEP,
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "no execution context",
            "none",
            "Cost/turnover evidence does not approve seed change, order instructions, execution, or scheduling.",
            "keep_all_approval_flags_false",
        ),
    ]
    return [
        {
            "created_at": created_at,
            "review_item": item,
            "review_status": status,
            "candidate_name": SELECTED_CANDIDATE,
            "saved_evidence": evidence,
            "source_warning": warning,
            "interpretation": interpretation,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for item, status, evidence, warning, interpretation, next_step in rows
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("final_cost_turnover_status", FINAL_STATUS, "Saved cost/turnover evidence status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current paper-live seed remains unchanged."),
        ("candidate_under_review", SELECTED_CANDIDATE, "Volatility-targeted candidate under manual review."),
        ("cost_turnover_review_status", "cost_turnover_exact_metrics_missing_manual_review_required", "Exact saved turnover/cost stress is not available in the current saved summaries."),
        ("saved_context", saved_cost_turnover_context(inputs), "Saved context where available."),
        ("source_warning", source_warning(), "Metric sources are saved outputs, not a fresh cost/turnover stress run."),
        ("evidence_pack_context", summary_value(inputs["seed_change_evidence_summary"], "final_evidence_pack_status") or "missing_seed_change_evidence_pack", "Saved evidence-pack context."),
        ("largest_blocker", "exact_cost_turnover_stress_missing_for_seed_change_proposal", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This review reads saved outputs only and does not call Alpaca."))
    rows.append(("market_data_refresh_now", "false", "This review does not refresh market data or recompute turnover."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows() -> list[dict[str, Any]]:
    rows = [
        ("exact_cost_turnover_stress_missing", "blocked", "high", "A seed-change proposal needs explicit turnover and cost sensitivity evidence.", NEXT_STEP),
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent seed.", NEXT_STEP),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth cost/turnover review complete. Evidence only; no seed change approved.",
        f"final_cost_turnover_status={summary_value(summary_rows, 'final_cost_turnover_status')}",
        f"cost_turnover_review_status={summary_value(summary_rows, 'cost_turnover_review_status')}",
        f"source_warning={summary_value(summary_rows, 'source_warning')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_review={output_paths['review']}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def saved_cost_turnover_context(inputs: dict[str, list[dict[str, str]]]) -> str:
    status = summary_value(inputs["robustness_summary"], "parameter_sensitivity_status")
    preferred = summary_value(inputs["nearby_variants_summary"], "preferred_candidate")
    return f"parameter_sensitivity={status or 'missing'}; preferred_candidate={preferred or 'missing'}"


def source_warning() -> str:
    return "saved_outputs_do_not_include_fresh_cost_turnover_stress_manual_review_required"


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
