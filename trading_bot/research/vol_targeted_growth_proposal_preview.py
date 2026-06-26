"""Saved-output proposal preview for volatility-targeted growth.

This report creates a non-executable proposal preview using only saved outputs
and the approved schema checkpoint. It does not read broker positions, refresh
market data, create order instructions, displace QQQ100, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_proposal_preview_created_saved_output_only"
BLOCKED_STATUS = "vol_targeted_growth_proposal_preview_blocked_missing_schema"
NEXT_STEP = "manual_review_proposal_preview_before_any_seed_change_or_action_design"

OUTPUT_FILES = {
    "preview": Path("data/vol_targeted_growth_proposal_preview.csv"),
    "summary": Path("data/vol_targeted_growth_proposal_preview_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_proposal_preview_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_proposal_preview_blockers.csv"),
}

INPUT_FILES = {
    "schema_summary": Path("data/vol_targeted_growth_proposal_preview_schema_summary.csv"),
    "schema": Path("data/vol_targeted_growth_proposal_preview_schema.csv"),
    "proposal_design_summary": Path("data/vol_targeted_growth_proposal_implementation_design_summary.csv"),
    "candidate_discussion_summary": Path("data/vol_targeted_growth_candidate_discussion_summary.csv"),
    "preview_signal": Path("data/vol_targeted_growth_preview_signal.csv"),
    "preview_signal_summary": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

FALLBACK_SLEEVES = [
    ("qqq100_core_trend_sleeve", "0.70", "incumbent_seed_component"),
    ("high_growth_stock_research_sleeve", "0.20", "research_only_component"),
    ("crypto_research_sleeve", "0.05", "research_only_component"),
    ("defensive_cash_or_bond_sleeve", "0.05", "research_only_component"),
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "proposal_only": True,
    "preview_only": True,
    "proposal_preview_created": True,
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
    "qqq100_displacement_approved": False,
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

PREVIEW_COLUMNS = [
    "created_at",
    "candidate_name",
    "incumbent_seed",
    "sleeve_name",
    "target_weight",
    "sleeve_status",
    "volatility_target_pct",
    "volatility_window_days",
    "exposure_cap",
    "current_exposure_status",
    "manual_review_label",
    "blocker",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthProposalPreviewResult:
    output_paths: dict[str, Path]
    preview_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_proposal_preview(root_dir: Path | str = ".") -> VolTargetedGrowthProposalPreviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    sleeves = sleeve_rows(inputs["preview_signal"])
    preview_rows = build_preview_rows(created_at, final_status, sleeves)
    summary_rows = build_summary_rows(inputs, preview_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["preview"], PREVIEW_COLUMNS, preview_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthProposalPreviewResult(
        output_paths=output_paths,
        preview_rows=preview_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_proposal_preview(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    preview_path = root / OUTPUT_FILES["preview"]
    if not summary_path.exists() or not preview_path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-proposal-preview` first."]
    summary_rows = read_csv_rows(summary_path)
    preview_rows = read_csv_rows(preview_path)
    return 0, [
        "Volatility-targeted growth proposal preview saved display. Proposal preview only; no execution approval.",
        f"final_proposal_preview_status: {summary_value(summary_rows, 'final_proposal_preview_status')}",
        f"selected_candidate: {summary_value(summary_rows, 'selected_candidate')}",
        f"incumbent_seed: {summary_value(summary_rows, 'incumbent_seed')}",
        f"proposal_preview_row_count: {len(preview_rows)}",
        f"sleeve_weight_summary: {summary_value(summary_rows, 'sleeve_weight_summary')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "order_instructions_created=false; qqq100_displacement_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    schema_status = summary_value(inputs["schema_summary"], "final_schema_status")
    if schema_status == "vol_targeted_growth_proposal_preview_schema_ready_manual_review_required":
        return FINAL_STATUS
    return BLOCKED_STATUS


def sleeve_rows(signal_rows: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    rows = [
        (row.get("sleeve_name", ""), row.get("target_weight", ""), row.get("sleeve_status", ""))
        for row in signal_rows
        if row.get("signal_item") == "target_sleeve_weight"
    ]
    clean = [(name, weight, status) for name, weight, status in rows if name and weight]
    return clean or FALLBACK_SLEEVES


def build_preview_rows(created_at: str, final_status: str, sleeves: list[tuple[str, str, str]]) -> list[dict[str, Any]]:
    manual_label = "manual_review_required_no_action_approved" if final_status == FINAL_STATUS else "blocked_missing_schema"
    return [
        {
            "created_at": created_at,
            "candidate_name": SELECTED_CANDIDATE,
            "incumbent_seed": INCUMBENT_SEED,
            "sleeve_name": sleeve_name,
            "target_weight": target_weight,
            "sleeve_status": sleeve_status,
            "volatility_target_pct": "15",
            "volatility_window_days": "20",
            "exposure_cap": "1x",
            "current_exposure_status": "not_read_saved_output_only",
            "manual_review_label": manual_label,
            "blocker": "proposal_preview_not_approved_for_action",
            "required_next_step": NEXT_STEP if final_status == FINAL_STATUS else "run_proposal_preview_schema_first",
            **SAFETY_FLAGS,
        }
        for sleeve_name, target_weight, sleeve_status in sleeves
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], preview_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("final_proposal_preview_status", final_status, "Whether saved schema supports this non-executable proposal preview."),
        ("selected_candidate", SELECTED_CANDIDATE, "Volatility-targeted candidate under discussion."),
        ("incumbent_seed", INCUMBENT_SEED, "QQQ100 remains the incumbent paper-live seed."),
        ("source_schema_status", summary_value(inputs["schema_summary"], "final_schema_status") or "missing_schema_status", "Saved proposal preview schema status."),
        ("source_design_status", summary_value(inputs["proposal_design_summary"], "final_design_status") or "missing_design_status", "Saved proposal design status."),
        ("proposal_preview_row_count", str(len(preview_rows)), "Sleeve-level proposal preview rows."),
        ("sleeve_weight_summary", sleeve_weight_summary(preview_rows), "Saved target weights only, not executable quantities."),
        ("current_exposure_policy", "not_read_saved_output_only", "This command does not call Alpaca or read broker positions."),
        ("largest_blocker", "proposal_preview_created_but_not_approved_for_action_or_seed_change" if final_status == FINAL_STATUS else "missing_proposal_preview_schema", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if final_status == FINAL_STATUS else "run_proposal_preview_schema_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This proposal preview does not call Alpaca or read positions."))
    rows.append(("proposal_preview_contains_executable_fields", "false", "The preview columns are limited to allowed review fields and safety flags."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("proposal_preview_not_approved_for_action", "blocked", "critical", "This preview is not an action preview and does not approve any portfolio change.", NEXT_STEP),
        ("current_exposure_not_read", "blocked", "critical", "Current exposure is not read or compared in this saved-output command.", "separate_confirmed_readonly_comparison_required"),
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent paper-live seed.", "separate_seed_change_review_required"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("proposal_preview_schema_missing", "blocked", "critical", "Saved proposal preview schema is missing or not ready.", "run_proposal_preview_schema_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth proposal preview complete. Saved-output proposal preview only; no orders or scheduling approved.",
        f"final_proposal_preview_status={summary_value(summary_rows, 'final_proposal_preview_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"incumbent_seed={summary_value(summary_rows, 'incumbent_seed')}",
        f"proposal_preview_row_count={summary_value(summary_rows, 'proposal_preview_row_count')}",
        f"sleeve_weight_summary={summary_value(summary_rows, 'sleeve_weight_summary')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_preview={output_paths['preview']}",
        "order_instructions_created=false; qqq100_displacement_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def sleeve_weight_summary(rows: list[dict[str, Any]]) -> str:
    return "; ".join(f"{row.get('sleeve_name')}={row.get('target_weight')}" for row in rows) if rows else "none"


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
