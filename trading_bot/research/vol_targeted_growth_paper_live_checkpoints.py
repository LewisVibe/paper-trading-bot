"""Saved-output paper-live checkpoints for the active volatility seed.

These reports sit after the status-only seed switch. They do not call Alpaca,
read positions, refresh market data, create order instructions, schedule
anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_SEED = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"

GATE_STATUS = "vol_targeted_growth_paper_live_manual_gate_created_manual_review_required"
ACTION_PACK_STATUS = "vol_targeted_growth_paper_live_action_preview_pack_created_manual_review_required"
RECONCILIATION_STATUS = "vol_targeted_growth_broker_comparison_reconciliation_created_manual_review_required"
RECONCILIATION_INCOMPLETE_STATUS = "vol_targeted_growth_broker_comparison_reconciliation_incomplete_manual_review_required"
CANDIDATE_APPROVAL_STATUS = "vol_targeted_growth_paper_live_candidate_discussion_approval_recorded"
ALLOCATION_POLICY_STATUS = "vol_targeted_growth_allocation_cap_sleeve_mapping_policy_created_manual_review_required"
TARGET_POSITION_PLAN_STATUS = "vol_targeted_growth_non_executable_target_position_plan_created_manual_review_required"
ORDER_TICKET_BOUNDARY_STATUS = "vol_targeted_growth_order_ticket_boundary_design_created_manual_review_required"
ORDER_TICKET_PREREQUISITES_STATUS = "vol_targeted_growth_executable_ticket_prerequisites_review_created_manual_review_required"
EXECUTION_BLOCKER_ROLLUP_STATUS = "vol_targeted_growth_paper_live_execution_blocker_rollup_created_manual_review_required"

GATE_NEXT_STEP = "manual_review_gate_before_any_vol_targeted_paper_live_action_discussion"
ACTION_PACK_NEXT_STEP = "manual_review_action_preview_pack_before_any_broker_reconciliation_or_order_design"
RECONCILIATION_NEXT_STEP = "manual_review_saved_broker_comparison_before_any_paper_live_candidate_discussion"
CANDIDATE_APPROVAL_NEXT_STEP = "design_allocation_cap_and_sleeve_mapping_policy_before_any_order_design"
ALLOCATION_POLICY_NEXT_STEP = "design_non_executable_target_position_plan_before_any_order_ticket_design"
TARGET_POSITION_PLAN_NEXT_STEP = "manual_review_target_position_plan_before_any_order_ticket_design"
ORDER_TICKET_BOUNDARY_NEXT_STEP = "manual_review_order_ticket_boundary_before_any_executable_order_ticket_design"
ORDER_TICKET_PREREQUISITES_NEXT_STEP = "manual_review_prerequisites_before_any_executable_ticket_design_or_order_command"
EXECUTION_BLOCKER_ROLLUP_NEXT_STEP = "manual_review_execution_blocker_rollup_before_any_future_execution_design"

GATE_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_paper_live_manual_approval_gate.csv"),
    "summary": Path("data/vol_targeted_growth_paper_live_manual_approval_gate_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_paper_live_manual_approval_gate_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_paper_live_manual_approval_gate_blockers.csv"),
}

ACTION_PACK_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_paper_live_action_preview_pack.csv"),
    "summary": Path("data/vol_targeted_growth_paper_live_action_preview_pack_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_paper_live_action_preview_pack_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_paper_live_action_preview_pack_blockers.csv"),
}

RECONCILIATION_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_broker_comparison_reconciliation.csv"),
    "summary": Path("data/vol_targeted_growth_broker_comparison_reconciliation_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_broker_comparison_reconciliation_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_broker_comparison_reconciliation_blockers.csv"),
}

CANDIDATE_APPROVAL_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_paper_live_candidate_approval_record.csv"),
    "summary": Path("data/vol_targeted_growth_paper_live_candidate_approval_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_paper_live_candidate_approval_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_paper_live_candidate_approval_blockers.csv"),
}

ALLOCATION_POLICY_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_allocation_cap_sleeve_mapping_policy.csv"),
    "summary": Path("data/vol_targeted_growth_allocation_cap_sleeve_mapping_policy_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_allocation_cap_sleeve_mapping_policy_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_allocation_cap_sleeve_mapping_policy_blockers.csv"),
}

TARGET_POSITION_PLAN_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_non_executable_target_position_plan.csv"),
    "summary": Path("data/vol_targeted_growth_non_executable_target_position_plan_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_non_executable_target_position_plan_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_non_executable_target_position_plan_blockers.csv"),
}

ORDER_TICKET_BOUNDARY_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_order_ticket_boundary_design.csv"),
    "summary": Path("data/vol_targeted_growth_order_ticket_boundary_design_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_order_ticket_boundary_design_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_order_ticket_boundary_design_blockers.csv"),
}

ORDER_TICKET_PREREQUISITES_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_executable_ticket_prerequisites_review.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_prerequisites_review_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_prerequisites_review_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_prerequisites_review_blockers.csv"),
}

EXECUTION_BLOCKER_ROLLUP_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup.csv"),
    "summary": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_paper_live_execution_blocker_rollup_blockers.csv"),
}

INPUT_FILES = {
    "active_seed_readiness_summary": Path("data/vol_targeted_growth_active_seed_readiness_summary.csv"),
    "seed_switch_summary": Path("data/vol_targeted_growth_seed_switch_status_only_summary.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "action_preview": Path("data/vol_targeted_growth_action_preview.csv"),
    "action_preview_quality_gate_summary": Path("data/vol_targeted_growth_action_preview_quality_gate_summary.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "broker_comparison": Path("data/vol_targeted_growth_broker_position_comparison.csv"),
    "post_comparison_decision_summary": Path("data/vol_targeted_growth_post_comparison_decision_summary.csv"),
    "paper_live_monitoring_status": Path("data/paper_live_monitoring_status.csv"),
    "manual_gate_summary": Path("data/vol_targeted_growth_paper_live_manual_approval_gate_summary.csv"),
    "paper_live_action_preview_pack_summary": Path("data/vol_targeted_growth_paper_live_action_preview_pack_summary.csv"),
    "broker_reconciliation_summary": Path("data/vol_targeted_growth_broker_comparison_reconciliation_summary.csv"),
    "candidate_approval_summary": Path("data/vol_targeted_growth_paper_live_candidate_approval_summary.csv"),
    "allocation_policy_summary": Path("data/vol_targeted_growth_allocation_cap_sleeve_mapping_policy_summary.csv"),
    "target_position_plan_summary": Path("data/vol_targeted_growth_non_executable_target_position_plan_summary.csv"),
    "order_ticket_boundary_summary": Path("data/vol_targeted_growth_order_ticket_boundary_design_summary.csv"),
    "ticket_prerequisites_summary": Path("data/vol_targeted_growth_executable_ticket_prerequisites_review_summary.csv"),
    "criteria_source_closeout_record_summary": Path("data/vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv"),
    "criteria_resolution_plan_closeout_record_summary": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_record_summary.csv"),
    "approval_criteria_closeout_record_summary": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_summary.csv"),
    "final_ticket_blockers_closeout_record_summary": Path("data/vol_targeted_growth_final_ticket_blockers_closeout_record_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "active_seed": ACTIVE_SEED,
    "active_ticker": ACTIVE_TICKER,
    "previous_seed": PREVIOUS_SEED,
    "previous_ticker": PREVIOUS_TICKER,
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
    "order_instructions_created": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "paper_live_candidate_approved": False,
    "paper_live_candidate_discussion_approved": False,
    "allocation_cap_approved": False,
    "sleeve_mapping_approved": False,
    "target_position_design_approved": False,
    "executable_target_positions_created": False,
    "order_ticket_design_approved": False,
    "executable_order_ticket_created": False,
    "executable_ticket_prerequisites_met": False,
    "executable_ticket_design_allowed": False,
    "execution_blocker_rollup_cleared": False,
    "manual_paper_live_approval_recorded": False,
    "action_preview_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REPORT_COLUMNS = [
    "created_at",
    "checkpoint_name",
    "status",
    "risk_level",
    "evidence",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthCheckpointResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_paper_live_manual_approval_gate(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = gate_report_rows(created_at, inputs)
    summary_rows = gate_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs)
    blocker_rows = gate_blocker_rows()
    output_paths = write_checkpoint(root, GATE_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth paper-live manual gate", summary_rows, output_paths),
    )


def show_vol_targeted_growth_paper_live_manual_approval_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / GATE_OUTPUT_FILES["summary"],
        "Volatility-targeted growth paper-live manual gate saved display. Manual-review only; no execution approval.",
        "final_manual_gate_status",
        "Run `python bot.py --vol-targeted-growth-paper-live-manual-approval-gate` first.",
    )


def generate_vol_targeted_growth_paper_live_action_preview_pack(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = action_pack_report_rows(created_at, inputs)
    summary_rows = action_pack_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs)
    blocker_rows = action_pack_blocker_rows(inputs)
    output_paths = write_checkpoint(root, ACTION_PACK_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth paper-live action-preview pack", summary_rows, output_paths),
    )


def show_vol_targeted_growth_paper_live_action_preview_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / ACTION_PACK_OUTPUT_FILES["summary"],
        "Volatility-targeted growth paper-live action-preview pack saved display. Saved-output only; no order instructions.",
        "final_action_preview_pack_status",
        "Run `python bot.py --vol-targeted-growth-paper-live-action-preview-pack` first.",
    )


def generate_vol_targeted_growth_broker_comparison_reconciliation(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = reconciliation_report_rows(created_at, inputs)
    final_status = reconciliation_status(inputs)
    summary_rows = reconciliation_summary_rows(inputs, report_rows, final_status)
    evidence_rows = evidence_rows_for(inputs)
    blocker_rows = reconciliation_blocker_rows(inputs, final_status)
    output_paths = write_checkpoint(root, RECONCILIATION_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth broker-comparison reconciliation", summary_rows, output_paths),
    )


def show_vol_targeted_growth_broker_comparison_reconciliation(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / RECONCILIATION_OUTPUT_FILES["summary"],
        "Volatility-targeted growth broker-comparison reconciliation saved display. Saved broker output only; no Alpaca call.",
        "final_reconciliation_status",
        "Run `python bot.py --vol-targeted-growth-broker-comparison-reconciliation` first.",
    )


def generate_vol_targeted_growth_paper_live_candidate_approval_record(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = candidate_approval_report_rows(created_at, inputs)
    summary_rows = candidate_approval_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs, overrides={"paper_live_candidate_discussion_approved": True})
    blocker_rows = candidate_approval_blocker_rows(inputs)
    output_paths = write_checkpoint(root, CANDIDATE_APPROVAL_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth paper-live candidate approval record", summary_rows, output_paths),
    )


def show_vol_targeted_growth_paper_live_candidate_approval_record(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / CANDIDATE_APPROVAL_OUTPUT_FILES["summary"],
        "Volatility-targeted growth paper-live candidate approval record saved display. Discussion approval only; no execution approval.",
        "final_candidate_approval_status",
        "Run `python bot.py --vol-targeted-growth-paper-live-candidate-approval-record` first.",
    )


def generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = allocation_policy_report_rows(created_at, inputs)
    summary_rows = allocation_policy_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs, overrides={"paper_live_candidate_discussion_approved": True})
    blocker_rows = allocation_policy_blocker_rows(inputs)
    output_paths = write_checkpoint(root, ALLOCATION_POLICY_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth allocation cap and sleeve mapping policy", summary_rows, output_paths),
    )


def show_vol_targeted_growth_allocation_cap_sleeve_mapping_policy(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / ALLOCATION_POLICY_OUTPUT_FILES["summary"],
        "Volatility-targeted growth allocation cap and sleeve mapping policy saved display. Design only; no order approval.",
        "final_allocation_policy_status",
        "Run `python bot.py --vol-targeted-growth-allocation-cap-sleeve-mapping-policy` first.",
    )


def generate_vol_targeted_growth_non_executable_target_position_plan(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = target_position_plan_report_rows(created_at, inputs)
    summary_rows = target_position_plan_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs, overrides={"paper_live_candidate_discussion_approved": True})
    blocker_rows = target_position_plan_blocker_rows(inputs)
    output_paths = write_checkpoint(root, TARGET_POSITION_PLAN_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth non-executable target-position plan", summary_rows, output_paths),
    )


def show_vol_targeted_growth_non_executable_target_position_plan(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / TARGET_POSITION_PLAN_OUTPUT_FILES["summary"],
        "Volatility-targeted growth non-executable target-position plan saved display. Review only; no order ticket.",
        "final_target_position_plan_status",
        "Run `python bot.py --vol-targeted-growth-non-executable-target-position-plan` first.",
    )


def generate_vol_targeted_growth_order_ticket_boundary_design(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = order_ticket_boundary_report_rows(created_at, inputs)
    summary_rows = order_ticket_boundary_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs, overrides={"paper_live_candidate_discussion_approved": True})
    blocker_rows = order_ticket_boundary_blocker_rows(inputs)
    output_paths = write_checkpoint(root, ORDER_TICKET_BOUNDARY_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth order-ticket boundary design", summary_rows, output_paths),
    )


def show_vol_targeted_growth_order_ticket_boundary_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / ORDER_TICKET_BOUNDARY_OUTPUT_FILES["summary"],
        "Volatility-targeted growth order-ticket boundary design saved display. Boundary only; no executable order ticket.",
        "final_order_ticket_boundary_status",
        "Run `python bot.py --vol-targeted-growth-order-ticket-boundary-design` first.",
    )


def generate_vol_targeted_growth_executable_ticket_prerequisites_review(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = order_ticket_prerequisites_report_rows(created_at, inputs)
    summary_rows = order_ticket_prerequisites_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs, overrides={"paper_live_candidate_discussion_approved": True})
    blocker_rows = order_ticket_prerequisites_blocker_rows(inputs)
    output_paths = write_checkpoint(
        root,
        ORDER_TICKET_PREREQUISITES_OUTPUT_FILES,
        report_rows,
        summary_rows,
        evidence_rows,
        blocker_rows,
    )
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth executable ticket prerequisites review", summary_rows, output_paths),
    )


def show_vol_targeted_growth_executable_ticket_prerequisites_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / ORDER_TICKET_PREREQUISITES_OUTPUT_FILES["summary"],
        "Volatility-targeted growth executable ticket prerequisites saved display. Prerequisites only; no executable order ticket.",
        "final_executable_ticket_prerequisites_status",
        "Run `python bot.py --vol-targeted-growth-executable-ticket-prerequisites-review` first.",
    )


def generate_vol_targeted_growth_paper_live_execution_blocker_rollup(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = execution_blocker_rollup_report_rows(created_at, inputs)
    summary_rows = execution_blocker_rollup_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs, overrides={"paper_live_candidate_discussion_approved": True})
    blocker_rows = execution_blocker_rollup_blocker_rows(inputs)
    output_paths = write_checkpoint(
        root,
        EXECUTION_BLOCKER_ROLLUP_OUTPUT_FILES,
        report_rows,
        summary_rows,
        evidence_rows,
        blocker_rows,
    )
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth paper-live execution blocker rollup", summary_rows, output_paths),
    )


def show_vol_targeted_growth_paper_live_execution_blocker_rollup(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / EXECUTION_BLOCKER_ROLLUP_OUTPUT_FILES["summary"],
        "Volatility-targeted growth paper-live execution blocker rollup saved display. Rollup only; no execution design.",
        "final_execution_blocker_rollup_status",
        "Run `python bot.py --vol-targeted-growth-paper-live-execution-blocker-rollup` first.",
    )


def gate_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    active_status = summary_value(inputs["active_seed_readiness_summary"], "final_active_seed_readiness_status")
    gate_items = [
        (
            "active_seed_confirmed",
            "manual_review_required" if active_status else "missing_saved_evidence",
            "critical",
            active_status or "missing_active_seed_readiness",
            "The active seed can only be considered if saved active-seed readiness exists.",
            GATE_NEXT_STEP,
        ),
        (
            "manual_approval_required",
            "manual_approval_not_recorded",
            "critical",
            "manual_paper_live_approval_recorded=false",
            "No paper-live action discussion is approved by this checkpoint.",
            "record_separate_manual_approval_before_any_action_discussion",
        ),
        (
            "component_sleeve_boundary",
            "high_growth_and_crypto_remain_research_only",
            "critical",
            "multi_sleeve_candidate_contains research-only sleeves",
            "The high-growth and crypto components cannot piggyback into paper execution.",
            "separate_component_promotion_reviews_required",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "all approval flags false",
            "The gate is a review checkpoint, not an action or order approval.",
            "keep_all_execution_flags_false",
        ),
    ]
    return [report_row(created_at, *item) for item in gate_items]


def gate_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_manual_gate_status", GATE_STATUS, "Manual gate exists, but approval is not recorded."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("active_seed_readiness_status", summary_value(inputs["active_seed_readiness_summary"], "final_active_seed_readiness_status") or "missing_active_seed_readiness_status", "Saved active-seed readiness evidence."),
        ("paper_live_candidate_approved", "False", "No paper-live candidacy is approved."),
        ("manual_paper_live_approval_recorded", "False", "A separate explicit approval record would be required later."),
        ("largest_blocker", "manual_paper_live_approval_not_recorded", "Human approval is required before action discussion."),
        ("recommended_next_step", GATE_NEXT_STEP, "Review the gate before any action preview or broker reconciliation can be treated as candidate discussion."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item) for item in data]


def action_pack_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    action_status = summary_value(inputs["action_preview_summary"], "final_action_preview_status")
    quality_status = summary_value(inputs["action_preview_quality_gate_summary"], "final_quality_gate_status")
    rows = [
        (
            "saved_action_preview_present",
            "manual_review_required" if action_status else "missing_saved_action_preview",
            "critical",
            action_status or "missing_action_preview_status",
            "Saved sleeve preview context is required, but it is still not an order instruction.",
            ACTION_PACK_NEXT_STEP,
        ),
        (
            "quality_gate_present",
            "manual_review_required" if quality_status else "missing_saved_quality_gate",
            "high",
            quality_status or "missing_action_preview_quality_gate_status",
            "The action preview needs a saved quality gate before candidate discussion.",
            "refresh_saved_action_preview_quality_gate",
        ),
        (
            "current_exposure_boundary",
            "current_exposure_requires_saved_broker_reconciliation",
            "critical",
            "broker_positions_read_now=false",
            "This pack does not read positions and cannot decide alignment.",
            "use_saved_broker_comparison_reconciliation_only_after_manual_review",
        ),
        (
            "order_instruction_boundary",
            "order_instructions_forbidden",
            "critical",
            "no side, quantity, order type, account, key, webhook, token, or order id fields",
            "The action-preview pack is explanatory, not executable.",
            "keep_pack_non_executable",
        ),
    ]
    return [report_row(created_at, *item) for item in rows]


def action_pack_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action_rows = inputs["action_preview"]
    data = [
        ("final_action_preview_pack_status", ACTION_PACK_STATUS, "Saved action-preview context is packaged for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("saved_action_preview_status", summary_value(inputs["action_preview_summary"], "final_action_preview_status") or "missing_action_preview_status", "Saved action-preview status."),
        ("saved_action_preview_quality_gate_status", summary_value(inputs["action_preview_quality_gate_summary"], "final_quality_gate_status") or "missing_action_preview_quality_gate_status", "Saved quality-gate status."),
        ("sleeve_preview_row_count", str(len(action_rows)), "Saved sleeve preview row count."),
        ("order_instructions_created", "False", "No executable order instructions are created."),
        ("largest_blocker", "current_exposure_not_reconciled_and_manual_approval_missing", "Current exposure is unknown unless a saved broker comparison is reviewed."),
        ("recommended_next_step", ACTION_PACK_NEXT_STEP, "Manual review the saved pack before broker reconciliation or order-design discussion."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item) for item in data]


def reconciliation_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    broker_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status")
    post_status = summary_value(inputs["post_comparison_decision_summary"], "final_post_comparison_decision_status")
    rows = [
        (
            "saved_broker_comparison_present",
            "manual_review_required" if broker_status else "missing_saved_broker_comparison",
            "critical",
            broker_status or "missing_broker_comparison_status",
            "This reconciliation uses saved broker comparison output only and does not call Alpaca.",
            RECONCILIATION_NEXT_STEP,
        ),
        (
            "saved_post_comparison_decision_present",
            "manual_review_required" if post_status else "missing_post_comparison_decision",
            "high",
            post_status or "missing_post_comparison_decision_status",
            "Saved post-comparison interpretation should be reviewed before any candidate discussion.",
            "refresh_or_review_post_comparison_decision",
        ),
        (
            "broker_read_boundary",
            "broker_not_read_now",
            "critical",
            "alpaca_called=false; paper_positions_read=false",
            "The reconciliation is safe to run repeatedly because it does not query the broker.",
            "run_readonly_broker_comparison_only_with_separate_explicit_approval",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
            "Saved broker context is not approval to trade or repeat trades.",
            "keep_all_execution_flags_false",
        ),
    ]
    return [report_row(created_at, *item) for item in rows]


def reconciliation_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    return RECONCILIATION_STATUS if inputs["broker_comparison_summary"] else RECONCILIATION_INCOMPLETE_STATUS


def reconciliation_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    rows: list[dict[str, Any]],
    final_status: str,
) -> list[dict[str, Any]]:
    broker_rows = inputs["broker_comparison"]
    broker_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status")
    data = [
        ("final_reconciliation_status", final_status, "Saved broker-comparison evidence is reconciled for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("saved_broker_comparison_status", broker_status or "missing_broker_comparison_status", "Saved read-only broker comparison status."),
        ("saved_broker_comparison_row_count", str(len(broker_rows)), "Saved broker comparison row count."),
        ("broker_read_now", "False", "This command does not call Alpaca or read positions."),
        ("paper_live_candidate_approved", "False", "No paper-live candidacy is approved by reconciliation."),
        ("largest_blocker", "saved_broker_context_requires_manual_review_not_execution", "Broker context cannot become order instructions."),
        ("recommended_next_step", RECONCILIATION_NEXT_STEP, "Manual review saved broker comparison before any candidate discussion."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item) for item in data]


def candidate_approval_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    gate_status = summary_value(inputs["manual_gate_summary"], "final_manual_gate_status")
    action_status = summary_value(inputs["paper_live_action_preview_pack_summary"], "final_action_preview_pack_status")
    reconciliation_status_value = summary_value(inputs["broker_reconciliation_summary"], "final_reconciliation_status")
    rows = [
        (
            "candidate_discussion_scope",
            "candidate_discussion_approved_not_execution",
            "critical",
            CANDIDATE_APPROVAL_STATUS,
            "Manual approval is recorded only for discussing the volatility seed as a paper-live candidate.",
            CANDIDATE_APPROVAL_NEXT_STEP,
        ),
        (
            "manual_gate_evidence",
            "manual_review_required" if gate_status else "missing_saved_manual_gate",
            "high",
            gate_status or "missing_manual_gate_status",
            "The manual gate should exist before candidate discussion approval is useful.",
            "refresh_manual_gate_before_using_approval_record",
        ),
        (
            "action_preview_pack_evidence",
            "manual_review_required" if action_status else "missing_saved_action_preview_pack",
            "high",
            action_status or "missing_action_preview_pack_status",
            "Saved action-preview context remains non-executable.",
            "refresh_action_preview_pack_before_order_design",
        ),
        (
            "broker_reconciliation_evidence",
            "manual_review_required" if reconciliation_status_value else "missing_saved_broker_reconciliation",
            "critical",
            reconciliation_status_value or "missing_broker_reconciliation_status",
            "Saved broker context can inform review but cannot become an order instruction.",
            "refresh_broker_reconciliation_before_order_design",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
            "This approval record does not approve an order, follow-up order, repeat order, or schedule.",
            "keep_all_execution_flags_false",
        ),
    ]
    return [report_row(created_at, *item, overrides={"paper_live_candidate_discussion_approved": True}) for item in rows]


def candidate_approval_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_candidate_approval_status", CANDIDATE_APPROVAL_STATUS, "Candidate discussion approval is recorded; execution remains blocked."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("manual_gate_status", summary_value(inputs["manual_gate_summary"], "final_manual_gate_status") or "missing_manual_gate_status", "Saved manual gate status."),
        ("action_preview_pack_status", summary_value(inputs["paper_live_action_preview_pack_summary"], "final_action_preview_pack_status") or "missing_action_preview_pack_status", "Saved paper-live action-preview pack status."),
        ("broker_reconciliation_status", summary_value(inputs["broker_reconciliation_summary"], "final_reconciliation_status") or "missing_broker_reconciliation_status", "Saved broker reconciliation status."),
        ("paper_live_candidate_discussion_approved", "True", "Human approval is recorded only for candidate discussion."),
        ("paper_live_candidate_approved", "False", "Paper-live candidacy still requires later allocation/sleeve policy and action design."),
        ("execution_approved", "False", "No execution is approved."),
        ("largest_blocker", "allocation_cap_and_sleeve_mapping_policy_missing", "Next review must define allocation cap and sleeve mapping boundaries."),
        ("recommended_next_step", CANDIDATE_APPROVAL_NEXT_STEP, "Design policy before any order-design discussion."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item, overrides={"paper_live_candidate_discussion_approved": True}) for item in data]


def allocation_policy_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    approval_status = summary_value(inputs["candidate_approval_summary"], "final_candidate_approval_status")
    rows = [
        (
            "candidate_discussion_prerequisite",
            "manual_review_required" if approval_status else "missing_candidate_discussion_approval",
            "critical",
            approval_status or "missing_candidate_approval_status",
            "Allocation policy design should follow candidate-discussion approval, but still does not approve trading.",
            "refresh_candidate_approval_record_before_using_policy",
        ),
        (
            "total_allocation_cap_policy",
            "proposed_cap_manual_review_required",
            "critical",
            "default_total_paper_allocation_cap=0_until_separate_execution_design; discussion_cap_placeholder=manual_review_required",
            "No multi-sleeve exposure should become active by implication.",
            ALLOCATION_POLICY_NEXT_STEP,
        ),
        (
            "qqq100_core_sleeve_mapping",
            "single_symbol_mapping_allowed_for_future_design_only",
            "high",
            "sleeve=qqq100_core_trend_sleeve; proposed_symbol=QQQ; target_weight_context=0.70",
            "QQQ is the only sleeve with an obvious single-symbol paper proxy, but this still is not an order.",
            "review_saved_current_qqq_position_before_any_target_position_design",
        ),
        (
            "high_growth_sleeve_mapping",
            "blocked_research_only_unmapped",
            "critical",
            "sleeve=high_growth_stock_research_sleeve; target_weight_context=0.20; proposed_symbol=none",
            "High-growth remains research-only and cannot piggyback into paper execution.",
            "separate_high_growth_promotion_and_symbol_policy_required",
        ),
        (
            "crypto_sleeve_mapping",
            "blocked_research_only_unmapped",
            "critical",
            "sleeve=crypto_research_sleeve; target_weight_context=0.05; proposed_symbol=none",
            "Crypto remains research-only and no crypto execution venue or custody policy is approved.",
            "separate_crypto_execution_policy_required",
        ),
        (
            "defensive_sleeve_mapping",
            "manual_review_unmapped",
            "high",
            "sleeve=defensive_cash_or_bond_sleeve; target_weight_context=0.05; proposed_symbol=none",
            "The defensive sleeve is a buffer concept until a cash/bond proxy is separately chosen.",
            "separate_defensive_proxy_policy_required",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "no order side, quantity, order type, account, key, token, webhook, order id, or executable target position",
            "This policy is a design checkpoint, not a trade ticket.",
            "keep_all_execution_flags_false",
        ),
    ]
    return [report_row(created_at, *item, overrides={"paper_live_candidate_discussion_approved": True}) for item in rows]


def allocation_policy_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_allocation_policy_status", ALLOCATION_POLICY_STATUS, "Allocation cap and sleeve mapping policy is documented for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("candidate_approval_status", summary_value(inputs["candidate_approval_summary"], "final_candidate_approval_status") or "missing_candidate_approval_status", "Saved candidate-discussion approval status."),
        ("paper_live_candidate_discussion_approved", "True", "Discussion may continue from the saved approval record."),
        ("paper_live_candidate_approved", "False", "Policy design does not approve paper-live candidacy."),
        ("allocation_cap_approved", "False", "The cap is a design boundary, not an approved executable allocation."),
        ("sleeve_mapping_approved", "False", "Sleeve mappings require later review before any target-position design."),
        ("target_position_design_approved", "False", "No target-position design is approved."),
        ("proposed_default_total_allocation_cap", "0_until_separate_execution_design", "No active paper exposure is created by this policy."),
        ("qqq100_core_mapping", "future_design_only:QQQ", "QQQ can be reviewed as a future single-symbol proxy only."),
        ("high_growth_mapping", "blocked_research_only", "High-growth sleeve is not executable."),
        ("crypto_mapping", "blocked_research_only", "Crypto sleeve is not executable."),
        ("defensive_mapping", "manual_review_unmapped", "Defensive sleeve proxy is not selected."),
        ("largest_blocker", "non_executable_target_position_plan_missing", "Next step is still non-executable target-position design."),
        ("recommended_next_step", ALLOCATION_POLICY_NEXT_STEP, "Design non-executable target positions before any order-ticket design."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item, overrides={"paper_live_candidate_discussion_approved": True}) for item in data]


def target_position_plan_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    policy_status = summary_value(inputs["allocation_policy_summary"], "final_allocation_policy_status")
    rows = [
        (
            "allocation_policy_prerequisite",
            "manual_review_required" if policy_status else "missing_allocation_policy",
            "critical",
            policy_status or "missing_allocation_policy_status",
            "Target-position planning should follow allocation policy, but still must not become an order ticket.",
            "refresh_allocation_policy_before_using_target_plan",
        ),
        (
            "qqq100_core_position_context",
            "review_only_not_executable",
            "high",
            "sleeve=qqq100_core_trend_sleeve; symbol_context=QQQ; target_weight_context=0.70; proposed_action_label=review_only",
            "QQQ can be reviewed as a future single-symbol target context, but no side or order quantity is created.",
            TARGET_POSITION_PLAN_NEXT_STEP,
        ),
        (
            "high_growth_position_context",
            "blocked_research_only",
            "critical",
            "sleeve=high_growth_stock_research_sleeve; symbol_context=unmapped; target_weight_context=0.20; proposed_action_label=blocked",
            "High-growth remains research-only and cannot become a target position.",
            "separate_high_growth_promotion_required",
        ),
        (
            "crypto_position_context",
            "blocked_research_only",
            "critical",
            "sleeve=crypto_research_sleeve; symbol_context=unmapped; target_weight_context=0.05; proposed_action_label=blocked",
            "Crypto remains research-only and has no approved paper execution venue or target position.",
            "separate_crypto_execution_policy_required",
        ),
        (
            "defensive_position_context",
            "manual_review_unmapped",
            "high",
            "sleeve=defensive_cash_or_bond_sleeve; symbol_context=unmapped; target_weight_context=0.05; proposed_action_label=manual_review",
            "Defensive sleeve has no approved proxy and cannot become a target position.",
            "separate_defensive_proxy_review_required",
        ),
        (
            "order_ticket_boundary",
            "order_ticket_design_blocked",
            "critical",
            "no side; no quantity; no order_type; no account; no order_id; no executable target_position",
            "This plan intentionally stops before order-ticket design.",
            "keep_non_executable_until_separate_manual_execution_design",
        ),
    ]
    return [report_row(created_at, *item, overrides={"paper_live_candidate_discussion_approved": True}) for item in rows]


def target_position_plan_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_target_position_plan_status", TARGET_POSITION_PLAN_STATUS, "Non-executable target-position context is documented for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("allocation_policy_status", summary_value(inputs["allocation_policy_summary"], "final_allocation_policy_status") or "missing_allocation_policy_status", "Saved allocation policy status."),
        ("paper_live_candidate_discussion_approved", "True", "Discussion may continue from the saved approval record."),
        ("paper_live_candidate_approved", "False", "Target-position plan does not approve paper-live candidacy."),
        ("target_position_design_approved", "False", "No executable target-position design is approved."),
        ("executable_target_positions_created", "False", "The plan creates no executable target positions."),
        ("order_instructions_created", "False", "No order side, quantity, order type, or account fields are created."),
        ("qqq100_review_context", "QQQ_review_only_no_order_quantity", "QQQ is review context only."),
        ("high_growth_review_context", "blocked_research_only", "High-growth stays blocked."),
        ("crypto_review_context", "blocked_research_only", "Crypto stays blocked."),
        ("defensive_review_context", "manual_review_unmapped", "Defensive sleeve stays unmapped."),
        ("largest_blocker", "order_ticket_design_not_approved", "A later separate order-ticket design would be required before any execution discussion."),
        ("recommended_next_step", TARGET_POSITION_PLAN_NEXT_STEP, "Manual review before any order-ticket design."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item, overrides={"paper_live_candidate_discussion_approved": True}) for item in data]


def order_ticket_boundary_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    target_plan_status = summary_value(inputs["target_position_plan_summary"], "final_target_position_plan_status")
    rows = [
        (
            "target_position_plan_prerequisite",
            "manual_review_required" if target_plan_status else "missing_target_position_plan",
            "critical",
            target_plan_status or "missing_target_position_plan_status",
            "Order-ticket boundary review should follow the non-executable target-position plan.",
            "refresh_target_position_plan_before_using_order_ticket_boundary",
        ),
        (
            "order_ticket_schema_boundary",
            "executable_schema_blocked",
            "critical",
            "forbidden_fields=side,quantity,order_type,time_in_force,account_id,order_id,api_key,webhook,token",
            "This checkpoint documents fields that must remain absent until a separate execution design exists.",
            ORDER_TICKET_BOUNDARY_NEXT_STEP,
        ),
        (
            "qqq100_boundary",
            "review_context_only_no_trade_ticket",
            "critical",
            "sleeve=qqq100_core_trend_sleeve; symbol_context=QQQ; no side; no quantity; no action",
            "QQQ remains context for manual review only and cannot become a ticket here.",
            "separate_executable_ticket_design_required_if_ever_approved",
        ),
        (
            "research_sleeve_boundary",
            "research_sleeves_blocked_from_ticket",
            "critical",
            "high_growth=blocked; crypto=blocked; defensive=unmapped",
            "Research-only and unmapped sleeves cannot produce order tickets.",
            "separate_component_promotion_required",
        ),
        (
            "broker_boundary",
            "broker_not_contacted",
            "critical",
            "alpaca_called=false; broker_positions_read_now=false",
            "This report does not read positions or prepare broker actions.",
            "run_broker_checks_only_with_separate_explicit_approval",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "order_ticket_design_approved=false; executable_order_ticket_created=false; execution_approved=false",
            "Boundary design is not order approval, paper execution approval, or scheduling approval.",
            "keep_all_execution_flags_false",
        ),
    ]
    return [report_row(created_at, *item, overrides={"paper_live_candidate_discussion_approved": True}) for item in rows]


def order_ticket_boundary_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_order_ticket_boundary_status", ORDER_TICKET_BOUNDARY_STATUS, "Order-ticket boundary is documented for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("target_position_plan_status", summary_value(inputs["target_position_plan_summary"], "final_target_position_plan_status") or "missing_target_position_plan_status", "Saved target-position plan status."),
        ("paper_live_candidate_discussion_approved", "True", "Discussion may continue from the saved approval record."),
        ("paper_live_candidate_approved", "False", "Boundary design does not approve paper-live candidacy."),
        ("target_position_design_approved", "False", "No executable target-position design is approved."),
        ("executable_target_positions_created", "False", "No executable target positions are created."),
        ("order_ticket_design_approved", "False", "No executable order-ticket design is approved."),
        ("executable_order_ticket_created", "False", "No executable order ticket is created."),
        ("order_instructions_created", "False", "No broker-ready fields are created."),
        ("qqq100_order_ticket_context", "QQQ_review_only_no_side_no_quantity", "QQQ is context only, not a ticket."),
        ("research_sleeve_ticket_context", "high_growth_crypto_blocked_defensive_unmapped", "Non-core sleeves remain blocked or unmapped."),
        ("largest_blocker", "executable_order_ticket_design_not_approved", "A future separate design would be required before any ticket could exist."),
        ("recommended_next_step", ORDER_TICKET_BOUNDARY_NEXT_STEP, "Manual review the boundary before any executable order-ticket design."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item, overrides={"paper_live_candidate_discussion_approved": True}) for item in data]


def order_ticket_prerequisites_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    boundary_status = summary_value(inputs["order_ticket_boundary_summary"], "final_order_ticket_boundary_status")
    rows = [
        (
            "order_ticket_boundary_prerequisite",
            "manual_review_required" if boundary_status else "missing_order_ticket_boundary",
            "critical",
            boundary_status or "missing_order_ticket_boundary_status",
            "Prerequisite review should follow the order-ticket boundary design.",
            "refresh_order_ticket_boundary_before_using_prerequisite_review",
        ),
        (
            "human_approval_prerequisite",
            "missing_explicit_manual_execution_approval",
            "critical",
            "manual_paper_live_approval_recorded=false; paper_live_candidate_approved=false",
            "No executable design can proceed until a separate explicit approval step exists.",
            "record_separate_manual_execution_design_approval_if_ever_requested",
        ),
        (
            "broker_state_prerequisite",
            "fresh_readonly_broker_check_required_later",
            "critical",
            "broker_positions_read_now=false; saved broker context is not fresh broker state",
            "Any future executable design would need a separately approved read-only broker check.",
            "run_readonly_broker_check_only_with_explicit_approval",
        ),
        (
            "risk_control_prerequisite",
            "risk_controls_not_approved_for_ticket",
            "critical",
            "allocation_cap_approved=false; sleeve_mapping_approved=false; target_position_design_approved=false",
            "Allocation, sleeve mapping, and target-position controls are still review-only.",
            "approve_controls_separately_before_ticket_design",
        ),
        (
            "component_sleeve_prerequisite",
            "component_sleeves_block_execution",
            "critical",
            "high_growth=research_only; crypto=research_only; defensive=unmapped",
            "The multi-sleeve seed cannot become executable while component sleeves remain blocked or unmapped.",
            "separate_component_promotion_reviews_required",
        ),
        (
            "ticket_creation_boundary",
            "ticket_creation_blocked",
            "critical",
            "executable_ticket_prerequisites_met=false; executable_ticket_design_allowed=false; executable_order_ticket_created=false",
            "This report is a checklist of missing approvals, not a design that can trade.",
            ORDER_TICKET_PREREQUISITES_NEXT_STEP,
        ),
    ]
    return [report_row(created_at, *item, overrides={"paper_live_candidate_discussion_approved": True}) for item in rows]


def order_ticket_prerequisites_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_executable_ticket_prerequisites_status", ORDER_TICKET_PREREQUISITES_STATUS, "Executable ticket prerequisites are documented for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("order_ticket_boundary_status", summary_value(inputs["order_ticket_boundary_summary"], "final_order_ticket_boundary_status") or "missing_order_ticket_boundary_status", "Saved order-ticket boundary status."),
        ("paper_live_candidate_discussion_approved", "True", "Discussion may continue from the saved approval record."),
        ("paper_live_candidate_approved", "False", "Executable ticket prerequisites do not approve paper-live candidacy."),
        ("manual_paper_live_approval_recorded", "False", "No execution-design approval is recorded."),
        ("executable_ticket_prerequisites_met", "False", "Prerequisites remain incomplete."),
        ("executable_ticket_design_allowed", "False", "No executable ticket design is allowed by this report."),
        ("order_ticket_design_approved", "False", "No executable order-ticket design is approved."),
        ("executable_order_ticket_created", "False", "No executable order ticket is created."),
        ("order_instructions_created", "False", "No side, quantity, order type, time-in-force, or account fields are created."),
        ("fresh_broker_check_required_before_ticket_design", "True", "Any future executable design would need a separate explicit read-only broker check."),
        ("largest_blocker", "executable_ticket_prerequisites_not_met", "Manual approval, fresh broker state, and component controls remain missing."),
        ("recommended_next_step", ORDER_TICKET_PREREQUISITES_NEXT_STEP, "Manual review prerequisites before any executable ticket design or order command."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item, overrides={"paper_live_candidate_discussion_approved": True}) for item in data]


def execution_blocker_rollup_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    closed = closed_blockers(inputs)
    checkpoints = [
        ("manual_gate", "manual_gate_summary", "final_manual_gate_status", "manual_paper_live_approval_not_recorded"),
        ("action_preview_pack", "paper_live_action_preview_pack_summary", "final_action_preview_pack_status", "current_exposure_not_reconciled"),
        ("broker_reconciliation", "broker_reconciliation_summary", "final_reconciliation_status", "saved_broker_context_requires_manual_review_not_execution"),
        ("candidate_approval", "candidate_approval_summary", "final_candidate_approval_status", "paper_live_candidate_not_fully_approved"),
        ("allocation_policy", "allocation_policy_summary", "final_allocation_policy_status", "allocation_cap_not_executable"),
        ("target_position_plan", "target_position_plan_summary", "final_target_position_plan_status", "order_ticket_design_not_approved"),
        ("order_ticket_boundary", "order_ticket_boundary_summary", "final_order_ticket_boundary_status", "executable_order_ticket_design_not_approved"),
        ("ticket_prerequisites", "ticket_prerequisites_summary", "final_executable_ticket_prerequisites_status", "executable_ticket_prerequisites_not_met"),
    ]
    rows = []
    for checkpoint_name, input_name, status_key, blocker in checkpoints:
        status_value = summary_value(inputs[input_name], status_key)
        rows.append(
            (
                f"{checkpoint_name}_status",
                "manual_review_required" if status_value else "missing_saved_checkpoint",
                "critical" if not status_value else "high",
                status_value or f"missing_{status_key}",
                f"Saved {checkpoint_name} checkpoint remains review-only and cannot approve execution.",
                blocker,
            )
        )
    if "criteria_source_reviewed" in closed:
        rows.append(
            (
                "criteria_source_reviewed_closeout",
                "closed_saved_evidence",
                "info",
                summary_value(inputs["criteria_source_closeout_record_summary"], "final_closeout_record_decision"),
                "The criteria_source_reviewed blocker is closed by saved record only; this does not approve ticket values, execution, or scheduling.",
                "continue_reviewing_remaining_execution_ticket_blockers",
            )
        )
    if "criteria_resolution_plan_open" in closed:
        rows.append(
            (
                "criteria_resolution_plan_open_closeout",
                "closed_saved_evidence",
                "info",
                summary_value(inputs["criteria_resolution_plan_closeout_record_summary"], "final_closeout_record_decision"),
                "The criteria_resolution_plan_open blocker is closed by saved record only; this does not approve ticket values, execution, or scheduling.",
                "continue_reviewing_remaining_execution_ticket_blockers",
            )
        )
    if "approval_criteria_not_approval" in closed:
        rows.append(
            (
                "approval_criteria_not_approval_closeout",
                "closed_saved_evidence",
                "info",
                summary_value(inputs["approval_criteria_closeout_record_summary"], "final_closeout_record_decision"),
                "The approval_criteria_not_approval blocker is closed by saved record only; this does not approve ticket values, execution, or scheduling.",
                "continue_reviewing_remaining_ticket_value_blockers",
            )
        )
    rows.extend(
        [
            (
                "combined_execution_boundary",
                "execution_blocked",
                "critical",
                "paper_live_candidate_approved=false; executable_ticket_prerequisites_met=false; executable_ticket_design_allowed=false",
                "The full chain still blocks paper execution and ticket design.",
                EXECUTION_BLOCKER_ROLLUP_NEXT_STEP,
            ),
            (
                "scheduling_boundary",
                "scheduling_blocked",
                "critical",
                "scheduling_approved=false; never_schedule_order_capable_commands=true",
                "Monitoring schedules must not become order-capable schedules.",
                "keep_order_capable_commands_unscheduled",
            ),
        ]
    )
    return [report_row(created_at, *item, overrides={"paper_live_candidate_discussion_approved": True}) for item in rows]


def execution_blocker_rollup_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    closed = closed_blockers(inputs)
    closed_blocker_count = len(closed)
    missing = [
        name
        for name in [
            "manual_gate_summary",
            "paper_live_action_preview_pack_summary",
            "broker_reconciliation_summary",
            "candidate_approval_summary",
            "allocation_policy_summary",
            "target_position_plan_summary",
            "order_ticket_boundary_summary",
            "ticket_prerequisites_summary",
            "criteria_source_closeout_record_summary",
            "criteria_resolution_plan_closeout_record_summary",
            "approval_criteria_closeout_record_summary",
        ]
        if not inputs[name]
    ]
    blocker_count = sum(1 for row in rows if row.get("status") != "closed_saved_evidence")
    remaining_known_blockers = remaining_blockers_after_closeout(inputs)
    data = [
        ("final_execution_blocker_rollup_status", EXECUTION_BLOCKER_ROLLUP_STATUS, "Execution blockers are rolled up for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("missing_checkpoint_count", str(len(missing)), "Saved checkpoint summaries missing from the rollup."),
        ("missing_checkpoints", ";".join(missing) or "none", "Missing saved checkpoint names."),
        ("execution_blocker_count", str(blocker_count), "Open blocker/manual-review rows after applying saved blocker closeout evidence."),
        ("closed_blocker_count", str(closed_blocker_count), "Closed blockers recognised from saved closeout evidence."),
        ("criteria_source_reviewed_closed", str("criteria_source_reviewed" in closed), "True only when the saved criteria-source closeout record closes that blocker."),
        ("criteria_resolution_plan_open_closed", str("criteria_resolution_plan_open" in closed), "True only when the saved resolution-plan closeout record closes that blocker."),
        ("approval_criteria_not_approval_closed", str("approval_criteria_not_approval" in closed), "True only when the saved approval-criteria closeout record closes that blocker."),
        ("ticket_values_not_approved_closed", str("ticket_values_not_approved" in closed), "True only when the saved final-ticket-blockers closeout record closes that blocker."),
        ("executable_ticket_prerequisites_not_met_closed", str("executable_ticket_prerequisites_not_met" in closed), "True only when the saved final-ticket-blockers closeout record closes that blocker."),
        ("closed_blocker", ";".join(closed) or "none", "Closed blockers recognised by this recalculation."),
        ("remaining_known_blockers_after_closeout", remaining_known_blockers, "Known blockers that remain open after the criteria-source closeout record."),
        ("paper_live_candidate_discussion_approved", "True", "Discussion may continue from the saved approval record."),
        ("paper_live_candidate_approved", "False", "Rollup does not approve paper-live candidacy."),
        ("executable_ticket_prerequisites_met", "False", "Prerequisites remain incomplete."),
        ("executable_ticket_design_allowed", "False", "No executable ticket design is allowed."),
        ("order_ticket_design_approved", "False", "No executable order-ticket design is approved."),
        ("executable_order_ticket_created", "False", "No executable order ticket is created."),
        ("order_instructions_created", "False", "No side, quantity, order type, time-in-force, or account fields are created."),
        ("execution_blocker_rollup_cleared", "False", "The rollup is not cleared for execution."),
        ("largest_blocker", "execution_not_approved" if remaining_known_blockers == "none" else "executable_ticket_prerequisites_not_met", "Manual approval, fresh broker state, controls, and component promotion remain blockers until the saved final closeout exists."),
        ("recommended_next_step", EXECUTION_BLOCKER_ROLLUP_NEXT_STEP, "Manual review the blocker rollup before any future execution design."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item, overrides={"paper_live_candidate_discussion_approved": True}) for item in data]


def closed_blockers(inputs: dict[str, list[dict[str, str]]]) -> list[str]:
    closed = []
    source_rows = inputs.get("criteria_source_closeout_record_summary", [])
    if (
        summary_value(source_rows, "final_closeout_record_decision") == "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY"
        and summary_value(source_rows, "closed_blocker") == "criteria_source_reviewed"
    ):
        closed.append("criteria_source_reviewed")
    resolution_rows = inputs.get("criteria_resolution_plan_closeout_record_summary", [])
    if (
        summary_value(resolution_rows, "final_closeout_record_decision") == "CRITERIA_RESOLUTION_PLAN_OPEN_BLOCKER_CLOSED_ONLY"
        and summary_value(resolution_rows, "closed_blocker") == "criteria_resolution_plan_open"
    ):
        closed.append("criteria_resolution_plan_open")
    approval_rows = inputs.get("approval_criteria_closeout_record_summary", [])
    if (
        summary_value(approval_rows, "final_closeout_record_decision") == "APPROVAL_CRITERIA_NOT_APPROVAL_BLOCKER_CLOSED_ONLY"
        and summary_value(approval_rows, "closed_blocker") == "approval_criteria_not_approval"
    ):
        closed.append("approval_criteria_not_approval")
    final_rows = inputs.get("final_ticket_blockers_closeout_record_summary", [])
    if summary_value(final_rows, "final_closeout_record_decision") == "FINAL_TICKET_BLOCKERS_CLOSED_NO_EXECUTION_APPROVAL":
        closed.extend(["ticket_values_not_approved", "executable_ticket_prerequisites_not_met"])
    return closed


def remaining_blockers_after_closeout(inputs: dict[str, list[dict[str, str]]]) -> str:
    final_remaining = summary_value(inputs.get("final_ticket_blockers_closeout_record_summary", []), "remaining_known_blockers")
    if final_remaining:
        return final_remaining
    approval_remaining = summary_value(inputs.get("approval_criteria_closeout_record_summary", []), "remaining_known_blockers")
    if approval_remaining:
        return approval_remaining
    resolution_remaining = summary_value(
        inputs.get("criteria_resolution_plan_closeout_record_summary", []),
        "remaining_known_blockers",
    )
    if resolution_remaining:
        return resolution_remaining
    source_remaining = summary_value(inputs.get("criteria_source_closeout_record_summary", []), "remaining_known_blockers")
    return source_remaining or "criteria_closeout_records_missing"


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]], *, overrides: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = []
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    rows.append(("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return [evidence_row(*item, overrides=overrides) for item in rows]


def gate_blocker_rows() -> list[dict[str, Any]]:
    return blocker_rows(
        [
            ("manual_paper_live_approval_not_recorded", "blocked", "critical", "This checkpoint does not record approval.", "separate_manual_approval_record_required"),
            ("component_sleeves_not_promoted", "blocked", "critical", "High-growth and crypto sleeves remain research-only.", "separate_component_reviews_required"),
            ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, or scheduling are approved.", "keep_all_approval_flags_false"),
        ]
    )


def action_pack_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("current_exposure_not_reconciled", "blocked", "critical", "The pack does not read broker positions.", "review_saved_broker_reconciliation_separately"),
        ("order_instructions_forbidden", "blocked", "critical", "No order side, quantity, type, account, key, token, webhook, or order ID fields are allowed.", "keep_pack_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No execution, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if not inputs["action_preview_summary"]:
        rows.insert(0, ("missing_saved_action_preview", "blocked", "high", "Saved action preview summary is missing.", "refresh_saved_action_preview"))
    return blocker_rows(rows)


def reconciliation_blocker_rows(inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("broker_read_not_performed_now", "blocked", "critical", "This command does not call Alpaca.", "only_run_readonly_broker_comparison_with_separate_explicit_approval"),
        ("saved_broker_context_not_actionable", "blocked", "critical", "Saved broker context is manual-review evidence only.", "do_not_create_order_instructions"),
        ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, or scheduling are approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == RECONCILIATION_INCOMPLETE_STATUS:
        rows.insert(0, ("missing_saved_broker_comparison", "blocked", "high", "Saved broker comparison summary is missing.", "run_readonly_broker_comparison_only_after_explicit_approval"))
    if not inputs["post_comparison_decision_summary"]:
        rows.insert(1, ("missing_post_comparison_decision", "blocked", "high", "Saved post-comparison decision is missing.", "refresh_post_comparison_decision"))
    return blocker_rows(rows)


def candidate_approval_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("paper_live_candidate_not_fully_approved", "blocked", "critical", "Approval is for candidate discussion only, not paper-live deployment.", CANDIDATE_APPROVAL_NEXT_STEP),
        ("allocation_cap_missing", "blocked", "critical", "No allocation cap or sleeve mapping policy is approved yet.", "design_allocation_cap_and_sleeve_mapping_policy"),
        ("order_instructions_forbidden", "blocked", "critical", "No order side, quantity, type, account, key, token, webhook, or order ID fields are allowed.", "keep_record_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, follow-up order, repeat order, or scheduling are approved.", "keep_all_approval_flags_false"),
    ]
    if not inputs["manual_gate_summary"]:
        rows.insert(0, ("missing_manual_gate", "blocked", "high", "Saved manual gate summary is missing.", "refresh_manual_gate"))
    if not inputs["broker_reconciliation_summary"]:
        rows.insert(1, ("missing_broker_reconciliation", "blocked", "high", "Saved broker reconciliation summary is missing.", "refresh_broker_reconciliation"))
    return blocker_rows(rows, overrides={"paper_live_candidate_discussion_approved": True})


def allocation_policy_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("allocation_cap_not_executable", "blocked", "critical", "The default cap is zero until a separate execution design exists.", "design_non_executable_target_position_plan_first"),
        ("high_growth_sleeve_blocked", "blocked", "critical", "High-growth sleeve remains research-only and unmapped.", "separate_high_growth_promotion_required"),
        ("crypto_sleeve_blocked", "blocked", "critical", "Crypto sleeve remains research-only and unmapped.", "separate_crypto_execution_policy_required"),
        ("defensive_sleeve_unmapped", "blocked", "high", "Defensive sleeve has no approved paper proxy.", "separate_defensive_proxy_review_required"),
        ("order_instructions_forbidden", "blocked", "critical", "No order side, quantity, type, account, key, token, webhook, order ID, or executable target position is allowed.", "keep_policy_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, follow-up order, repeat order, or scheduling are approved.", "keep_all_approval_flags_false"),
    ]
    if not inputs["candidate_approval_summary"]:
        rows.insert(0, ("missing_candidate_approval_record", "blocked", "high", "Saved candidate approval summary is missing.", "refresh_candidate_approval_record"))
    return blocker_rows(rows, overrides={"paper_live_candidate_discussion_approved": True})


def target_position_plan_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("order_ticket_design_not_approved", "blocked", "critical", "No order ticket or executable target-position design is approved.", "separate_order_ticket_design_required"),
        ("qqq_context_not_order", "blocked", "critical", "QQQ is review context only; no side or quantity is created.", "manual_review_before_order_ticket_design"),
        ("high_growth_blocked", "blocked", "critical", "High-growth sleeve remains research-only.", "separate_high_growth_promotion_required"),
        ("crypto_blocked", "blocked", "critical", "Crypto sleeve remains research-only.", "separate_crypto_execution_policy_required"),
        ("defensive_unmapped", "blocked", "high", "Defensive sleeve has no approved paper proxy.", "separate_defensive_proxy_review_required"),
        ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, follow-up order, repeat order, or scheduling are approved.", "keep_all_approval_flags_false"),
    ]
    if not inputs["allocation_policy_summary"]:
        rows.insert(0, ("missing_allocation_policy", "blocked", "high", "Saved allocation policy summary is missing.", "refresh_allocation_policy"))
    return blocker_rows(rows, overrides={"paper_live_candidate_discussion_approved": True})


def order_ticket_boundary_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("executable_order_ticket_design_not_approved", "blocked", "critical", "No executable order-ticket design is approved.", "separate_order_ticket_design_review_required"),
        ("order_fields_forbidden", "blocked", "critical", "Side, quantity, order type, account, order id, keys, tokens, and webhook fields remain forbidden.", "keep_boundary_non_executable"),
        ("qqq_context_not_ticket", "blocked", "critical", "QQQ is review context only and cannot become a trade ticket in this checkpoint.", "manual_review_before_any_ticket_design"),
        ("research_sleeves_blocked", "blocked", "critical", "High-growth and crypto remain research-only; defensive remains unmapped.", "separate_component_promotion_required"),
        ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, follow-up order, repeat order, or scheduling are approved.", "keep_all_approval_flags_false"),
    ]
    if not inputs["target_position_plan_summary"]:
        rows.insert(0, ("missing_target_position_plan", "blocked", "high", "Saved non-executable target-position plan summary is missing.", "refresh_target_position_plan"))
    return blocker_rows(rows, overrides={"paper_live_candidate_discussion_approved": True})


def order_ticket_prerequisites_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("executable_ticket_prerequisites_not_met", "blocked", "critical", "Manual approval, fresh broker state, and component controls remain incomplete.", "manual_review_prerequisites"),
        ("manual_execution_design_approval_missing", "blocked", "critical", "No separate manual approval exists for executable ticket design.", "record_approval_only_if_explicitly_requested_later"),
        ("fresh_broker_state_missing", "blocked", "critical", "This report does not call Alpaca and cannot use stale saved broker context as execution evidence.", "run_readonly_broker_check_only_with_explicit_approval"),
        ("component_sleeves_not_executable", "blocked", "critical", "High-growth and crypto remain research-only; defensive remains unmapped.", "separate_component_promotion_required"),
        ("order_ticket_creation_blocked", "blocked", "critical", "No executable order ticket, side, quantity, order type, or account field is created.", "keep_prerequisites_review_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, follow-up order, repeat order, or scheduling are approved.", "keep_all_approval_flags_false"),
    ]
    if not inputs["order_ticket_boundary_summary"]:
        rows.insert(0, ("missing_order_ticket_boundary", "blocked", "high", "Saved order-ticket boundary summary is missing.", "refresh_order_ticket_boundary"))
    return blocker_rows(rows, overrides={"paper_live_candidate_discussion_approved": True})


def execution_blocker_rollup_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("execution_blocker_rollup_not_cleared", "blocked", "critical", "The rollup records blockers and does not clear execution.", "manual_review_rollup"),
        ("executable_ticket_prerequisites_not_met", "blocked", "critical", "Executable ticket prerequisites remain incomplete.", "complete_separate_prerequisite_review_if_ever_requested"),
        ("fresh_broker_state_missing", "blocked", "critical", "No fresh broker read was performed by this rollup.", "run_readonly_broker_check_only_with_explicit_approval"),
        ("component_sleeves_not_executable", "blocked", "critical", "High-growth and crypto remain research-only; defensive remains unmapped.", "separate_component_promotion_required"),
        ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, follow-up order, repeat order, or scheduling are approved.", "keep_all_approval_flags_false"),
    ]
    if not inputs["ticket_prerequisites_summary"]:
        rows.insert(0, ("missing_ticket_prerequisites", "blocked", "high", "Saved executable ticket prerequisites summary is missing.", "refresh_ticket_prerequisites_review"))
    return blocker_rows(rows, overrides={"paper_live_candidate_discussion_approved": True})


def write_checkpoint(
    root: Path,
    paths: dict[str, Path],
    report_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    blocker_rows_: list[dict[str, Any]],
) -> dict[str, Path]:
    output_paths = {name: root / path for name, path in paths.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows_)
    return output_paths


def show_summary(path: Path, title: str, status_key: str, missing_message: str) -> tuple[int, list[str]]:
    if not path.exists():
        return 1, [missing_message]
    rows = read_csv_rows(path)
    return 0, [
        title,
        f"{status_key}: {summary_value(rows, status_key)}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"previous_seed: {summary_value(rows, 'previous_seed') or PREVIOUS_SEED}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"closed_blocker_count: {summary_value(rows, 'closed_blocker_count')}",
        f"criteria_source_reviewed_closed: {summary_value(rows, 'criteria_source_reviewed_closed')}",
        f"criteria_resolution_plan_open_closed: {summary_value(rows, 'criteria_resolution_plan_open_closed')}",
        f"approval_criteria_not_approval_closed: {summary_value(rows, 'approval_criteria_not_approval_closed')}",
        f"ticket_values_not_approved_closed: {summary_value(rows, 'ticket_values_not_approved_closed')}",
        f"executable_ticket_prerequisites_not_met_closed: {summary_value(rows, 'executable_ticket_prerequisites_not_met_closed')}",
        f"remaining_known_blockers_after_closeout: {summary_value(rows, 'remaining_known_blockers_after_closeout')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "Warning: this is saved-output/manual-review only, not broker refresh, paper-live approval, order approval, live trading, or scheduling approval.",
    ]


def summary_lines(title: str, summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    status = (
        summary_value(summary_rows, "final_manual_gate_status")
        or summary_value(summary_rows, "final_action_preview_pack_status")
        or summary_value(summary_rows, "final_reconciliation_status")
        or summary_value(summary_rows, "final_candidate_approval_status")
        or summary_value(summary_rows, "final_allocation_policy_status")
        or summary_value(summary_rows, "final_target_position_plan_status")
        or summary_value(summary_rows, "final_order_ticket_boundary_status")
        or summary_value(summary_rows, "final_executable_ticket_prerequisites_status")
        or summary_value(summary_rows, "final_execution_blocker_rollup_status")
    )
    lines = [
        f"{title} complete. Saved-output/manual-review only; no execution or scheduling approved.",
        f"final_status={status}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "alpaca_called=false; broker_positions_read_now=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]
    for key in [
        "closed_blocker_count",
        "criteria_source_reviewed_closed",
        "criteria_resolution_plan_open_closed",
        "approval_criteria_not_approval_closed",
        "ticket_values_not_approved_closed",
        "executable_ticket_prerequisites_not_met_closed",
        "remaining_known_blockers_after_closeout",
    ]:
        value = summary_value(summary_rows, key)
        if value:
            lines.insert(-1, f"{key}={value}")
    return lines


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def report_row(
    created_at: str,
    name: str,
    status: str,
    risk: str,
    evidence: str,
    interpretation: str,
    next_step: str,
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "checkpoint_name": name,
        "status": status,
        "risk_level": risk,
        "evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": next_step,
        **flag_values(overrides),
    }


def summary_row(name: str, value: str, details: str, *, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **flag_values(overrides)}


def evidence_row(name: str, value: str, details: str, *, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **flag_values(overrides)}


def blocker_rows(rows: list[tuple[str, str, str, str, str]], *, overrides: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **flag_values(overrides)}
        for name, status, severity, details, next_step in rows
    ]


def flag_values(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    values = dict(SAFETY_FLAGS)
    if overrides:
        values.update(overrides)
    return values


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return ""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
