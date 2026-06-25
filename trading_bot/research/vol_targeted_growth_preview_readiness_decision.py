"""Saved-output preview-readiness decision for volatility-targeted growth.

This module reads existing saved volatility-targeted growth reports only. It
does not refresh market data, call Alpaca, read positions, create order
instructions, schedule anything, implement preview mode, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
NEAREST_HIGHER_VOL_CHALLENGER = "higher_growth_multi_sleeve_target_vol_20_win_20_cap_1x"
AGGRESSIVE_CHALLENGER = "higher_growth_multi_sleeve_target_vol_25_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_15_20_selected_for_preview_design_review"
READINESS_STATUS = "preview_design_discussion_ready_manual_review_required"
PREVIEW_IMPLEMENTATION_STATUS = "preview_implementation_not_added"

OUTPUT_FILES = {
    "decision": Path("data/vol_targeted_growth_preview_readiness_decision.csv"),
    "summary": Path("data/vol_targeted_growth_preview_readiness_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_preview_readiness_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_preview_readiness_blockers.csv"),
}

INPUT_FILES = {
    "nearby": Path("data/vol_targeted_growth_nearby_variants_summary.csv"),
    "nearby_review": Path("data/vol_targeted_growth_nearby_variants_review.csv"),
    "robustness": Path("data/vol_targeted_growth_robustness_checkpoint_summary.csv"),
    "manual_review": Path("data/vol_targeted_growth_manual_review_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
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

DECISION_COLUMNS = [
    "created_at",
    "check_name",
    "status",
    "risk_level",
    "selected_candidate",
    "comparison_subject",
    "selected_metrics",
    "comparison_metrics",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedPreviewReadinessDecisionResult:
    output_paths: dict[str, Path]
    decision_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_preview_readiness_decision(root_dir: Path | str = ".") -> VolTargetedPreviewReadinessDecisionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    selected = find_row(inputs["nearby_review"], "candidate_name", SELECTED_CANDIDATE)
    nearest = find_row(inputs["nearby_review"], "candidate_name", NEAREST_HIGHER_VOL_CHALLENGER)
    aggressive = find_row(inputs["nearby_review"], "candidate_name", AGGRESSIVE_CHALLENGER)

    decision_rows = build_decision_rows(created_at, selected, nearest, aggressive, inputs)
    summary_rows = build_summary_rows(selected, nearest, aggressive, inputs)
    evidence_rows = build_evidence_rows(inputs, selected, nearest, aggressive)
    blocker_rows = build_blocker_rows(summary_rows)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decision"], DECISION_COLUMNS, decision_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedPreviewReadinessDecisionResult(
        output_paths=output_paths,
        decision_rows=decision_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_preview_readiness_decision(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    decision_path = root / OUTPUT_FILES["decision"]
    if not summary_path.exists() or not decision_path.exists():
        return 1, [
            "Volatility-targeted growth preview-readiness decision is missing.",
            "Run `python bot.py --vol-targeted-growth-preview-readiness-decision` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted growth preview-readiness decision saved display. Research/report only; no preview implementation or execution approval.",
        f"final_decision_status: {summary_value(summary_rows, 'final_decision_status')}",
        f"selected_candidate: {summary_value(summary_rows, 'selected_candidate')}",
        f"nearest_higher_vol_challenger: {summary_value(summary_rows, 'nearest_higher_vol_challenger')}",
        f"aggressive_challenger: {summary_value(summary_rows, 'aggressive_challenger')}",
        f"preview_design_readiness_status: {summary_value(summary_rows, 'preview_design_readiness_status')}",
        f"preview_implementation_status: {summary_value(summary_rows, 'preview_implementation_status')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this decision only allows a future preview-design discussion; it does not create preview signals, order instructions, or scheduling approval.",
    ]


def build_decision_rows(
    created_at: str,
    selected: dict[str, str],
    nearest: dict[str, str],
    aggressive: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    return [
        decision_row(
            created_at,
            "selected_variant",
            "disciplined_15_20_variant_selected",
            "medium",
            SELECTED_CANDIDATE,
            "nearby_variant_grid",
            metric_line(selected),
            summary_value(inputs["nearby"], "variant_interpretation") or "missing_nearby_variant_interpretation",
            "The 15% target / 20-day variant keeps the best saved Sharpe and Calmar balance.",
            "design_saved_output_preview_only_checkpoint_for_vol_targeted_growth_15_20",
        ),
        decision_row(
            created_at,
            "nearest_higher_vol_challenger",
            "higher_vol_challenger_not_selected",
            "medium",
            SELECTED_CANDIDATE,
            NEAREST_HIGHER_VOL_CHALLENGER,
            metric_line(selected),
            metric_line(nearest),
            "The 20% target / 20-day variant improves CAGR but gives up drawdown and risk-adjusted score.",
            "keep_20_20_as_manual_review_context_not_preview_lead",
        ),
        decision_row(
            created_at,
            "aggressive_challenger",
            "aggressive_25_20_challenger_not_selected",
            "high",
            SELECTED_CANDIDATE,
            AGGRESSIVE_CHALLENGER,
            metric_line(selected),
            metric_line(aggressive),
            "The 25% target / 20-day variant has the highest CAGR but materially higher drawdown.",
            "keep_25_20_as_aggressive_research_challenger_not_preview_lead",
        ),
        decision_row(
            created_at,
            "preview_design_readiness",
            READINESS_STATUS,
            "medium",
            SELECTED_CANDIDATE,
            "future_preview_design_checkpoint",
            "preview_design_discussion_only",
            PREVIEW_IMPLEMENTATION_STATUS,
            "A future preview-only design checkpoint is reasonable, but no preview signal or action preview is implemented here.",
            "create_saved_output_preview_design_for_vol_targeted_growth_15_20_in_separate_prompt",
        ),
        decision_row(
            created_at,
            "execution_boundary",
            "execution_blocked",
            "critical",
            SELECTED_CANDIDATE,
            "paper_live_policy",
            "execution_approved=false",
            "scheduling_approved=false",
            "This decision does not approve paper execution, repeat orders, portfolio execution, or scheduling.",
            "keep_all_order_capable_paths_separate_and_unmodified",
        ),
    ]


def build_summary_rows(
    selected: dict[str, str],
    nearest: dict[str, str],
    aggressive: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    has_required = bool(selected and nearest and aggressive)
    final_status = FINAL_STATUS if has_required else "vol_targeted_growth_preview_readiness_blocked_missing_saved_evidence"
    return [
        summary_row("final_decision_status", final_status, "Final decision is report-only and manual-review-scoped."),
        summary_row("selected_candidate", candidate_summary(selected), "Disciplined volatility-targeted lead."),
        summary_row("nearest_higher_vol_challenger", candidate_summary(nearest), "Nearest higher-volatility challenger."),
        summary_row("aggressive_challenger", candidate_summary(aggressive), "Highest-CAGR challenger."),
        summary_row("nearby_review_status", summary_value(inputs["nearby"], "final_nearby_review_status") or "missing_nearby_review", "Nearby variants review input status."),
        summary_row("robustness_status", summary_value(inputs["robustness"], "final_robustness_status") or "missing_robustness_checkpoint", "Robustness checkpoint input status."),
        summary_row("manual_review_status", summary_value(inputs["manual_review"], "final_manual_review_status") or "missing_manual_review_pack", "Manual review input status."),
        summary_row("preview_design_readiness_status", READINESS_STATUS, "Future preview-design discussion status; not implementation."),
        summary_row("preview_implementation_status", PREVIEW_IMPLEMENTATION_STATUS, "No preview implementation was added."),
        summary_row("largest_blocker", "preview_design_not_implemented_and_no_order_instructions_allowed", "Largest blocker before any runnable preview."),
        summary_row("recommended_next_step", "create_saved_output_preview_design_for_vol_targeted_growth_15_20_in_separate_prompt", "Next step is a separate preview-design checkpoint, not execution."),
    ]


def build_evidence_rows(
    inputs: dict[str, list[dict[str, str]]],
    selected: dict[str, str],
    nearest: dict[str, str],
    aggressive: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        evidence_row("nearby_review_rows_available", str(len(inputs["nearby"])), "Rows read from data/vol_targeted_growth_nearby_variants_summary.csv."),
        evidence_row("nearby_variant_rows_available", str(len(inputs["nearby_review"])), "Rows read from data/vol_targeted_growth_nearby_variants_review.csv."),
        evidence_row("selected_candidate_metrics", metric_line(selected), "15/20 selected for disciplined risk-adjusted profile."),
        evidence_row("nearest_higher_vol_challenger_metrics", metric_line(nearest), "20/20 retained as manual-review context."),
        evidence_row("aggressive_challenger_metrics", metric_line(aggressive), "25/20 retained as aggressive higher-drawdown context."),
    ]


def build_blocker_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        blocker_row("preview_implementation_not_added", "blocked", "critical", "No preview signal, action preview, or target-weight preview file is implemented by this decision.", summary_value(summary_rows, "recommended_next_step")),
        blocker_row("execution_blocked", "blocked", "critical", "No paper execution, live execution, order instructions, portfolio execution, or scheduling are approved.", "keep_all_order_paths_separate_and_unmodified"),
        blocker_row("manual_review_required", "manual_review_required", "medium", "Manual review must accept the 15/20 versus 20/20 and 25/20 tradeoff before preview design.", "manual_review_before_any_preview_design_prompt"),
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth preview-readiness decision complete. Saved-output research only; no preview implementation, execution, orders, or scheduling approved.",
        f"final_decision_status={summary_value(summary_rows, 'final_decision_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"nearest_higher_vol_challenger={summary_value(summary_rows, 'nearest_higher_vol_challenger')}",
        f"aggressive_challenger={summary_value(summary_rows, 'aggressive_challenger')}",
        f"preview_design_readiness_status={summary_value(summary_rows, 'preview_design_readiness_status')}",
        f"preview_implementation_status={summary_value(summary_rows, 'preview_implementation_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['decision']}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def decision_row(
    created_at: str,
    check_name: str,
    status: str,
    risk_level: str,
    selected_candidate: str,
    comparison_subject: str,
    selected_metrics: str,
    comparison_metrics: str,
    interpretation: str,
    required_next_step: str,
) -> dict[str, Any]:
    return with_flags(
        {
            "created_at": created_at,
            "check_name": check_name,
            "status": status,
            "risk_level": risk_level,
            "selected_candidate": selected_candidate,
            "comparison_subject": comparison_subject,
            "selected_metrics": selected_metrics,
            "comparison_metrics": comparison_metrics,
            "interpretation": interpretation,
            "required_next_step": required_next_step,
        }
    )


def summary_row(summary_name: str, summary_value_text: str, details: str) -> dict[str, Any]:
    return with_flags({"summary_name": summary_name, "summary_value": summary_value_text, "details": details})


def evidence_row(evidence_name: str, evidence_value: str, details: str) -> dict[str, Any]:
    return with_flags({"evidence_name": evidence_name, "evidence_value": evidence_value, "details": details})


def blocker_row(blocker_name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return with_flags({"blocker_name": blocker_name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step})


def with_flags(row: dict[str, Any]) -> dict[str, Any]:
    return {**row, **SAFETY_FLAGS}


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


def find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def metric_line(row: dict[str, str]) -> str:
    if not row:
        return "missing_saved_metrics"
    return (
        f"CAGR={row.get('cagr', 'missing')}; "
        f"Sharpe={row.get('sharpe', 'missing')}; "
        f"MaxDD={row.get('max_drawdown', 'missing')}; "
        f"Calmar={row.get('calmar', 'missing')}"
    )


def candidate_summary(row: dict[str, str]) -> str:
    if not row:
        return "missing_saved_candidate"
    return f"{row.get('candidate_name', 'unknown_candidate')}: {metric_line(row)}"


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""
