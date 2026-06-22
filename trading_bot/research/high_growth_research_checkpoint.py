"""Saved-output-only high-growth research checkpoint consolidator."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MISSING = "missing_saved_output"
MISSING_OPTIONAL = "missing_optional_saved_output"

STATUS_MANUAL_REVIEW = "high_growth_research_checkpoint_manual_review_required"
STATUS_BLOCKED = "high_growth_research_checkpoint_blocked_missing_core_inputs"
STATUS_INCOMPLETE_OPTIONAL = "high_growth_research_checkpoint_incomplete_optional_context"
STATUS_RESEARCH_ONLY = "high_growth_research_checkpoint_research_only_no_execution"

NEXT_STEP = "manual_review_high_growth_concentration_drawdown_and_crypto_context_before_any_execution_or_scheduling_discussion"

INPUT_FILES = {
    "lead_state": Path("data/multi_sleeve_lead_state.csv"),
    "weight_sensitivity": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "higher_growth_review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "research_lead_decision": Path("data/multi_sleeve_research_lead_decision.csv"),
    "drawdown_decomposition": Path("data/multi_sleeve_high_growth_drawdown_decomposition.csv"),
    "drawdown_summary": Path("data/multi_sleeve_high_growth_drawdown_summary.csv"),
    "sleeve_quality_review": Path("data/high_growth_sleeve_quality_review.csv"),
    "sleeve_quality_summary": Path("data/high_growth_sleeve_quality_summary.csv"),
    "component_attribution": Path("data/high_growth_component_attribution.csv"),
    "component_streams_summary": Path("data/high_growth_component_streams_summary.csv"),
    "concentration_review": Path("data/high_growth_sleeve_concentration_review.csv"),
    "concentration_summary": Path("data/high_growth_sleeve_concentration_summary.csv"),
    "concentration_drawdown": Path("data/high_growth_sleeve_concentration_drawdown.csv"),
    "crypto_containment": Path("data/multi_sleeve_crypto_containment_review.csv"),
}

OUTPUT_FILES = {
    "checkpoint": Path("data/high_growth_research_checkpoint.csv"),
    "blockers": Path("data/high_growth_research_checkpoint_blockers.csv"),
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

CHECKPOINT_COLUMNS = [
    "created_at",
    "final_checkpoint_status",
    "selected_lead_candidate",
    "previous_baseline",
    "selected_candidate_CAGR",
    "selected_candidate_Sharpe",
    "selected_candidate_MaxDD",
    "selected_candidate_Calmar",
    "baseline_CAGR",
    "baseline_Sharpe",
    "baseline_MaxDD",
    "baseline_Calmar",
    "delta_CAGR",
    "delta_Sharpe",
    "delta_MaxDD",
    "delta_Calmar",
    "split_win_count",
    "worst_split",
    "worst_cost_stress",
    "high_growth_sleeve_status",
    "high_growth_concentration_status",
    "high_growth_dependency_status",
    "unique_ticker_count",
    "average_active_components",
    "max_component_weight",
    "top_contributor",
    "worst_contributor",
    "drawdown_decomposition_status",
    "drawdown_delta",
    "main_incremental_drawdown_contributor",
    "high_growth_drawdown_contribution",
    "crypto_drawdown_contribution",
    "drawdown_concentration_status",
    "top_drawdown_contributor",
    "top_drawdown_contribution",
    "crypto_containment_status",
    "manual_review_required",
    "required_next_step",
    *SAFETY_COLUMNS,
]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "blocker_severity",
    "blocker_detail",
    "required_next_step",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
]


@dataclass
class HighGrowthResearchCheckpointResult:
    output_paths: dict[str, Path]
    checkpoint_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_research_checkpoint(root_dir: Path | str = ".") -> HighGrowthResearchCheckpointResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    checkpoint = build_checkpoint_row(created_at, inputs)
    blockers = build_blocker_rows(created_at, checkpoint, inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["checkpoint"], CHECKPOINT_COLUMNS, [checkpoint])
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blockers)
    return HighGrowthResearchCheckpointResult(
        output_paths=output_paths,
        checkpoint_rows=[checkpoint],
        blocker_rows=blockers,
        summary_lines=summary_lines(checkpoint, output_paths["checkpoint"]),
    )


def show_high_growth_research_checkpoint(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["checkpoint"]
    if not path.exists():
        return 1, [
            "High-growth research checkpoint is missing.",
            "Run `python bot.py --high-growth-research-checkpoint` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    row = rows[0] if rows else {}
    return 0, [
        "High-growth research checkpoint. Saved-output-only review; no execution path.",
        f"final checkpoint status: {row.get('final_checkpoint_status', MISSING)}",
        f"selected lead candidate: {row.get('selected_lead_candidate', MISSING)} vs baseline {row.get('previous_baseline', MISSING)}",
        f"lead metrics: CAGR={row.get('selected_candidate_CAGR', MISSING)}; Sharpe={row.get('selected_candidate_Sharpe', MISSING)}; MaxDD={row.get('selected_candidate_MaxDD', MISSING)}; Calmar={row.get('selected_candidate_Calmar', MISSING)}",
        f"deltas: CAGR={row.get('delta_CAGR', MISSING)}; Sharpe={row.get('delta_Sharpe', MISSING)}; MaxDD={row.get('delta_MaxDD', MISSING)}; Calmar={row.get('delta_Calmar', MISSING)}",
        f"high-growth concentration: {row.get('high_growth_concentration_status', MISSING)}; dependency={row.get('high_growth_dependency_status', MISSING)}",
        f"contributors: top={row.get('top_contributor', MISSING)}; worst={row.get('worst_contributor', MISSING)}",
        f"drawdown: status={row.get('drawdown_decomposition_status', MISSING)}; delta={row.get('drawdown_delta', MISSING)}; contributor={row.get('main_incremental_drawdown_contributor', MISSING)}",
        f"drawdown concentration: status={row.get('drawdown_concentration_status', MISSING)}; top={row.get('top_drawdown_contributor', MISSING)}:{row.get('top_drawdown_contribution', MISSING)}",
        f"crypto containment: {row.get('crypto_containment_status', MISSING)}",
        f"required next step: {row.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def build_checkpoint_row(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    lead = first_row(inputs["lead_state"])
    concentration = first_row(inputs["concentration_review"])
    concentration_summary = summary_map(inputs["concentration_summary"])
    drawdown_summary = summary_map(inputs["drawdown_summary"])
    drawdown_incremental = first_matching_row(inputs["drawdown_decomposition"], "row_type", "incremental_high_growth_risk")
    concentration_drawdown = first_row(inputs["concentration_drawdown"])
    crypto = first_row(inputs["crypto_containment"])
    core_missing = [name for name in ["lead_state", "concentration_review"] if not inputs[name]]
    optional_missing = [name for name in ["crypto_containment"] if not inputs[name]]
    final_status = determine_final_status(core_missing, optional_missing)
    return {
        "created_at": created_at,
        "final_checkpoint_status": final_status,
        "selected_lead_candidate": value(lead, "current_research_lead_candidate"),
        "previous_baseline": value(lead, "previous_research_baseline"),
        "selected_candidate_CAGR": value(lead, "candidate_CAGR"),
        "selected_candidate_Sharpe": value(lead, "candidate_Sharpe"),
        "selected_candidate_MaxDD": value(lead, "candidate_MaxDD"),
        "selected_candidate_Calmar": value(lead, "candidate_Calmar"),
        "baseline_CAGR": value(lead, "baseline_CAGR"),
        "baseline_Sharpe": value(lead, "baseline_Sharpe"),
        "baseline_MaxDD": value(lead, "baseline_MaxDD"),
        "baseline_Calmar": value(lead, "baseline_Calmar"),
        "delta_CAGR": value(lead, "delta_CAGR"),
        "delta_Sharpe": value(lead, "delta_Sharpe"),
        "delta_MaxDD": value(lead, "delta_MaxDD"),
        "delta_Calmar": value(lead, "delta_Calmar"),
        "split_win_count": value(lead, "split_win_count"),
        "worst_split": value(lead, "worst_split_name"),
        "worst_cost_stress": value(lead, "worst_cost_stress_name"),
        "high_growth_sleeve_status": sleeve_quality_status(inputs),
        "high_growth_concentration_status": value(concentration, "concentration_review_status"),
        "high_growth_dependency_status": value(concentration, "concentration_status"),
        "unique_ticker_count": value(concentration, "unique_ticker_count"),
        "average_active_components": value(concentration, "average_active_components"),
        "max_component_weight": value(concentration, "max_component_weight"),
        "top_contributor": concentration_summary.get("top_contributor_summary", MISSING),
        "worst_contributor": concentration_summary.get("worst_contributor_summary", MISSING),
        "drawdown_decomposition_status": drawdown_summary.get("final_drawdown_decomposition_status", MISSING),
        "drawdown_delta": drawdown_summary.get("drawdown_delta", value(lead, "drawdown_delta_vs_current")),
        "main_incremental_drawdown_contributor": drawdown_summary.get("main_incremental_drawdown_contributor", value(drawdown_incremental, "main_incremental_drawdown_contributor")),
        "high_growth_drawdown_contribution": drawdown_summary.get("high_growth_contribution_during_worst_period", value(drawdown_incremental, "high_growth_weighted_contribution")),
        "crypto_drawdown_contribution": drawdown_summary.get("crypto_contribution_during_worst_period", value(drawdown_incremental, "crypto_weighted_contribution")),
        "drawdown_concentration_status": value(concentration_drawdown, "drawdown_concentration_status"),
        "top_drawdown_contributor": value(concentration_drawdown, "top_drawdown_contributor"),
        "top_drawdown_contribution": value(concentration_drawdown, "top_drawdown_contribution"),
        "crypto_containment_status": value(crypto, "crypto_containment_status", MISSING_OPTIONAL),
        "manual_review_required": str(final_status in {STATUS_MANUAL_REVIEW, STATUS_INCOMPLETE_OPTIONAL, STATUS_BLOCKED}).lower(),
        "required_next_step": NEXT_STEP,
        **safety_flags(),
    }


def determine_final_status(core_missing: list[str], optional_missing: list[str]) -> str:
    if core_missing:
        return STATUS_BLOCKED
    if optional_missing:
        return STATUS_INCOMPLETE_OPTIONAL
    return STATUS_MANUAL_REVIEW


def build_blocker_rows(
    created_at: str,
    checkpoint: dict[str, Any],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = []
    for name in ["lead_state", "concentration_review"]:
        if not inputs[name]:
            rows.append(blocker_row(created_at, f"{name}_missing", STATUS_BLOCKED, "high", f"missing core saved input {INPUT_FILES[name]}", NEXT_STEP))
    if not inputs["crypto_containment"]:
        rows.append(blocker_row(created_at, "crypto_containment_missing_optional", MISSING_OPTIONAL, "medium", "optional crypto containment context is unavailable", NEXT_STEP))
    rows.extend(
        [
            blocker_row(created_at, "manual_review_boundary", checkpoint["final_checkpoint_status"], "medium", "high-growth checkpoint is a manual-review research consolidation only", NEXT_STEP),
            blocker_row(created_at, "execution_boundary", "blocked_non_executable_research_only", "high", "checkpoint cannot approve or prepare orders", NEXT_STEP),
            blocker_row(created_at, "scheduling_boundary", "blocked_no_scheduling_change", "high", "checkpoint cannot approve scheduling", NEXT_STEP),
        ]
    )
    return rows


def blocker_row(created_at: str, name: str, status: str, severity: str, detail: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "blocker_status": status,
        "blocker_severity": severity,
        "blocker_detail": detail,
        "required_next_step": next_step,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "scheduling_approved": False,
    }


def sleeve_quality_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    review = first_row(inputs["sleeve_quality_review"])
    if review:
        return value(review, "sleeve_quality_status")
    summary = summary_map(inputs["sleeve_quality_summary"])
    return summary.get("final_high_growth_sleeve_quality_status", MISSING)


def summary_lines(row: dict[str, Any], output_path: Path) -> list[str]:
    return [
        "High-growth research checkpoint created. Saved-output-only review; no execution path.",
        f"final checkpoint status: {row.get('final_checkpoint_status', MISSING)}",
        f"selected lead candidate: {row.get('selected_lead_candidate', MISSING)} vs baseline {row.get('previous_baseline', MISSING)}",
        f"lead metrics: CAGR={row.get('selected_candidate_CAGR', MISSING)}; Sharpe={row.get('selected_candidate_Sharpe', MISSING)}; MaxDD={row.get('selected_candidate_MaxDD', MISSING)}; Calmar={row.get('selected_candidate_Calmar', MISSING)}",
        f"deltas: CAGR={row.get('delta_CAGR', MISSING)}; Sharpe={row.get('delta_Sharpe', MISSING)}; MaxDD={row.get('delta_MaxDD', MISSING)}; Calmar={row.get('delta_Calmar', MISSING)}",
        f"high-growth concentration: {row.get('high_growth_concentration_status', MISSING)}; dependency={row.get('high_growth_dependency_status', MISSING)}",
        f"contributors: top={row.get('top_contributor', MISSING)}; worst={row.get('worst_contributor', MISSING)}",
        f"drawdown: status={row.get('drawdown_decomposition_status', MISSING)}; delta={row.get('drawdown_delta', MISSING)}; contributor={row.get('main_incremental_drawdown_contributor', MISSING)}",
        f"drawdown concentration: status={row.get('drawdown_concentration_status', MISSING)}; top={row.get('top_drawdown_contributor', MISSING)}:{row.get('top_drawdown_contribution', MISSING)}",
        f"crypto containment: {row.get('crypto_containment_status', MISSING)}",
        f"required next step: {row.get('required_next_step', MISSING)}",
        f"Saved checkpoint: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def first_row(rows: list[dict[str, str]]) -> dict[str, str]:
    return rows[0] if rows else {}


def first_matching_row(rows: list[dict[str, str]], key: str, expected: str) -> dict[str, str]:
    return next((row for row in rows if row.get(key) == expected), {})


def value(row: dict[str, str], key: str, default: str = MISSING) -> str:
    raw = row.get(key)
    return str(raw) if raw not in {"", None} else default


def summary_map(rows: list[dict[str, str]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


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
