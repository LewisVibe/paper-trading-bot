"""Report-only next-phase backlog for future paper-live sleeve promotion work.

This checkpoint lists prerequisite work only. It does not implement promotion,
portfolio execution, broker reads, order instructions, scheduling, or execution
approval.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "report": Path("data/paper_live_next_phase_backlog.csv"),
    "summary": Path("data/paper_live_next_phase_backlog_summary.csv"),
    "blockers": Path("data/paper_live_next_phase_backlog_blockers.csv"),
    "evidence": Path("data/paper_live_next_phase_backlog_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "backlog_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "portfolio_execution_wired": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "backlog_item",
    "current_status",
    "required_before_next_stage",
    "blocker",
    "allowed_next_action",
    "forbidden_action",
    "research_only",
    "report_only",
    "backlog_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "portfolio_execution_wired",
    "alpaca_called",
    "live_positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_FLAGS.keys(),
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_value",
    "details",
    *SAFETY_FLAGS.keys(),
]


@dataclass(frozen=True)
class BacklogItem:
    backlog_item: str
    current_status: str
    required_before_next_stage: str
    blocker: str
    allowed_next_action: str
    forbidden_action: str


@dataclass
class PaperLiveNextPhaseBacklogResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_next_phase_backlog(root_dir: Path | str = ".") -> PaperLiveNextPhaseBacklogResult:
    root = Path(root_dir)
    items = build_backlog_items()
    report_rows = [item_to_row(item) for item in items]
    summary_rows = build_summary_rows(items)
    blocker_rows = build_blocker_rows()
    evidence_rows = build_evidence_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveNextPhaseBacklogResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_next_phase_backlog(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live next-phase backlog is missing.",
            "Run `python bot.py --paper-live-next-phase-backlog` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live next-phase backlog saved display. Report only; no promotion or portfolio execution approved.",
        f"final_backlog_status: {summary_value(rows, 'final_backlog_status')}",
        f"current_phase_status: {summary_value(rows, 'current_phase_status')}",
        f"next_phase_direction: {summary_value(rows, 'next_phase_direction')}",
        f"required_backlog_item_count: {summary_value(rows, 'required_backlog_item_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"allowed_next_action: {summary_value(rows, 'allowed_next_action')}",
        f"forbidden_action_summary: {summary_value(rows, 'forbidden_action_summary')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_backlog_items() -> list[BacklogItem]:
    return [
        BacklogItem(
            "qqq100_core",
            "previous_seed_context_aligned_long_one_no_action_required",
            "Continue saved previous-seed monitoring only; keep no repeat/follow-up order approved.",
            "previous_seed_no_repeat_followup_order_approved",
            "hold_no_action_and_monitor_only",
            "repeat_or_followup_qqq_order;change_current_qqq100_only_monitoring",
        ),
        BacklogItem(
            "generic_promotion_ladder",
            "design_exists_implementation_future_only_no_execution_wiring",
            "Manual review of report-only ladder design plus separate implementation plan before any ladder code.",
            "generic_ladder_not_implemented",
            "review_ladder_design_and_write_future_implementation_plan",
            "implement_execution_wiring;promote_any_sleeve_automatically",
        ),
        BacklogItem(
            "f6_f7",
            "targeted_checks_exist_accounting_proof_still_required",
            "Unknown positions must stay loud; portfolio accounting must be proven before portfolio metrics become promotion evidence.",
            "portfolio_backtest_accounting_not_yet_promotion_evidence",
            "add_accounting_consistency_verifier_before_using_portfolio_metrics",
            "assume_unknown_position_flat;use_portfolio_backtest_as_promotion_evidence",
        ),
        BacklogItem(
            "defensive_sleeve",
            "future_review_only",
            "Saved research, preview, risk review, drawdown behaviour, and F6/F7 compatibility evidence.",
            "defensive_sleeve_has_not_passed_ladder_separately",
            "create_saved_output_defensive_sleeve_review_pack",
            "promote_defensive_sleeve_to_preview_or_paper_live",
        ),
        BacklogItem(
            "high_growth_sleeve",
            "research_only",
            "Concentration, drawdown, attribution, survivorship/current-constituent warnings, and risk limits.",
            "high_growth_concentration_drawdown_attribution_reviews_incomplete",
            "complete_saved_output_high_growth_risk_and_attribution_reviews",
            "promote_high_growth_to_preview_or_paper_live",
        ),
        BacklogItem(
            "crypto_sleeve",
            "research_only_capped_future_only",
            "Containment, volatility/drawdown contribution, crypto-specific costs, and no crypto execution approval.",
            "crypto_execution_not_approved",
            "complete_saved_output_crypto_containment_and_cost_review",
            "approve_crypto_execution;wire_crypto_orders",
        ),
        BacklogItem(
            "multi_sleeve_allocator",
            "current_report_status_seed_no_portfolio_execution_wiring_no_order_instructions_no_scheduling",
            "Allocation policy, sleeve conflicts, portfolio accounting consistency, no order instructions, and no scheduling.",
            "allocator_execution_wiring_forbidden",
            "observe_enabled_status_cron_then_review_non_executable_action_preview_design",
            "create_portfolio_order_instructions;wire_allocator_to_execution;schedule_allocator",
        ),
        BacklogItem(
            "monitoring_hermes",
            "monitoring_only_status_exists_existing_cron_sequence_unchanged",
            "Keep status-only Hermes sequence unchanged and never schedule order-capable commands.",
            "order_capable_commands_must_never_be_scheduled",
            "continue_monitoring_only_status_and_document_any_future_schedule_review",
            "create_or_edit_execution_cron;trigger_order_capable_command_from_schedule",
        ),
    ]


def item_to_row(item: BacklogItem) -> dict[str, Any]:
    return {
        "backlog_item": item.backlog_item,
        "current_status": item.current_status,
        "required_before_next_stage": item.required_before_next_stage,
        "blocker": item.blocker,
        "allowed_next_action": item.allowed_next_action,
        "forbidden_action": item.forbidden_action,
        **ROW_SAFETY,
    }


def build_summary_rows(items: list[BacklogItem]) -> list[dict[str, Any]]:
    summary_items = [
        (
            "final_backlog_status",
            "paper_live_next_phase_backlog_report_only",
            "The backlog lists future prerequisites only; no promotion or execution is implemented.",
        ),
        (
            "current_phase_status",
            "vol_targeted_multi_sleeve_report_status_seed_qqq100_previous_aligned_long_one_no_action_required",
            "Volatility-targeted multi-sleeve is the current report/status seed; QQQ100 remains previous-seed context with no repeat/follow-up order approved.",
        ),
        (
            "next_phase_direction",
            "vol_targeted_multi_sleeve_seed_from_research_status_only",
            "Next work should validate monitoring and review non-executable action-preview design, not approve execution.",
        ),
        (
            "required_backlog_item_count",
            str(len(items)),
            "Backlog covers QQQ100 core, ladder, F6/F7, defensive, high-growth, crypto, allocator, and monitoring/Hermes.",
        ),
        (
            "largest_blocker",
            "portfolio_execution_and_promotion_evidence_not_ready",
            "No sleeve can move forward until evidence, accounting, and human review gates are complete.",
        ),
        (
            "allowed_next_action",
            "monitoring_observation_saved_output_reviews_and_verifiers_only",
            "Only monitoring observation, report-only review packs, verifiers, and documentation updates are allowed next.",
        ),
        (
            "forbidden_action_summary",
            "no_execution_wiring_no_order_instructions_no_scheduling_no_sleeve_promotion",
            "Do not connect strategies to execution, schedule order-capable commands, or promote sleeves.",
        ),
        (
            "next_safe_development_step",
            "observe_enabled_status_cron_then_review_non_executable_action_preview_design",
            "First observe the enabled status cron; then review a non-executable action-preview design separately.",
        ),
    ]
    return [summary_row(name, value, details) for name, value, details in summary_items]


def build_blocker_rows() -> list[dict[str, Any]]:
    blockers = [
        (
            "current_qqq100_monitoring_only",
            "blocked",
            "high",
            "Current state is QQQ100 monitor-only, aligned long one, no action required.",
            "Do not repeat/follow up QQQ paper orders; monitor only.",
        ),
        (
            "portfolio_backtest_accounting_not_proven",
            "blocked",
            "high",
            "Portfolio metrics are not promotion evidence until starting-cash/accounting consistency is proven.",
            "Add accounting consistency verifier before using portfolio evidence.",
        ),
        (
            "sleeve_reviews_incomplete",
            "blocked",
            "high",
            "Defensive, high-growth, crypto, and allocator sleeves have not passed next-stage evidence review.",
            "Complete sleeve-specific saved-output reviews before preview or paper-live discussion.",
        ),
        (
            "execution_and_scheduling_forbidden",
            "blocked",
            "critical",
            "No execution wiring, order instructions, crypto execution, or scheduled order-capable commands are approved.",
            "Keep all next steps report-only until a separate human-approved implementation task.",
        ),
    ]
    return [
        blocker_row(name, status, severity, details, next_step)
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows() -> list[dict[str, Any]]:
    evidence = [
        (
            "current_checkpoints",
            "5d4ea15;1fd1217;2d951f6;c35efc7;81253a9",
            "Checklist closeout, F6/F7 audit, targeted checks, ladder design, and multi-sleeve roadmap exist.",
        ),
        (
            "active_seed_monitoring_state",
            "active_strategy=higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x;active_ticker=MULTI_SLEEVE;report_status_only",
            "Volatility-targeted multi-sleeve is the current report/status seed only.",
        ),
        (
            "previous_qqq100_state",
            "previous_strategy=qqq_100_trend_gate;previous_ticker=QQQ;aligned_long_one;no_action_required",
            "QQQ100 remains previous-seed context, aligned long one share with no action required.",
        ),
        (
            "future_direction",
            "vol_targeted_multi_sleeve_from_research_status_only",
            "Current direction is report/status only and is not execution or scheduling approval.",
        ),
        (
            "approval_flags",
            "all_false",
            "Execution, paper execution, scheduling, live trading, follow-up order, and repeat execution approvals remain false.",
        ),
    ]
    return [evidence_row(name, value, details) for name, value, details in evidence]


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {
        "summary_name": name,
        "summary_value": value,
        "details": details,
        **SAFETY_FLAGS,
    }


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {
        "evidence_name": name,
        "evidence_value": value,
        "details": details,
        **SAFETY_FLAGS,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live next-phase backlog complete. Report only; no promotion, portfolio execution, orders, or scheduling approved.",
        f"final_backlog_status={summary_value(summary_rows, 'final_backlog_status')}",
        f"current_phase_status={summary_value(summary_rows, 'current_phase_status')}",
        f"next_phase_direction={summary_value(summary_rows, 'next_phase_direction')}",
        f"required_backlog_item_count={summary_value(summary_rows, 'required_backlog_item_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"allowed_next_action={summary_value(summary_rows, 'allowed_next_action')}",
        f"forbidden_action_summary={summary_value(summary_rows, 'forbidden_action_summary')}",
        f"next_safe_development_step={summary_value(summary_rows, 'next_safe_development_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return "unavailable"


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
