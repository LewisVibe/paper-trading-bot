"""Report-only design checkpoint for a future paper-live promotion ladder.

This module documents a future ladder shape only. It does not promote
strategies, call Alpaca, read positions, refresh market data, create orders,
write SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

OUTPUT_FILES = {
    "report": Path("data/paper_live_promotion_ladder_design.csv"),
    "summary": Path("data/paper_live_promotion_ladder_design_summary.csv"),
    "blockers": Path("data/paper_live_promotion_ladder_design_blockers.csv"),
    "evidence": Path("data/paper_live_promotion_ladder_design_evidence.csv"),
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
    "design_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "ladder_stage",
    "current_allowed_scope",
    "required_evidence",
    "current_status",
    "blocker",
    "future_action_required",
    "research_only",
    "report_only",
    "design_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
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
class LadderStage:
    ladder_stage: str
    current_allowed_scope: str
    required_evidence: str
    current_status: str
    blocker: str
    future_action_required: str


@dataclass
class PaperLivePromotionLadderDesignResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_promotion_ladder_design(
    root_dir: Path | str = ".",
) -> PaperLivePromotionLadderDesignResult:
    root = Path(root_dir)
    stages = build_ladder_stages()
    report_rows = [stage_to_row(stage) for stage in stages]
    summary_rows = build_summary_rows(stages)
    blocker_rows = build_blocker_rows()
    evidence_rows = build_evidence_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLivePromotionLadderDesignResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_promotion_ladder_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live promotion ladder design is missing.",
            "Run `python bot.py --paper-live-promotion-ladder-design` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live promotion ladder design saved display. Report only; no promotion or orders approved.",
        f"final_design_status: {summary_value(rows, 'final_design_status')}",
        f"only_current_ladder_seed: {summary_value(rows, 'only_current_ladder_seed')}",
        f"current_qqq100_state: {summary_value(rows, 'current_qqq100_state')}",
        f"qqq100_manual_flatten_status: {summary_value(rows, 'qqq100_manual_flatten_status')}",
        f"qqq100_manual_flatten_runbook_status: {summary_value(rows, 'qqq100_manual_flatten_runbook_status')}",
        f"future_multi_sleeve_status: {summary_value(rows, 'future_multi_sleeve_status')}",
        f"portfolio_backtest_evidence_status: {summary_value(rows, 'portfolio_backtest_evidence_status')}",
        f"unknown_position_boundary: {summary_value(rows, 'unknown_position_boundary')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_ladder_stages() -> list[LadderStage]:
    return [
        LadderStage(
            "research_candidate",
            "QQQ100 only as current seed; multi-sleeve, high-growth, crypto, defensive, SMA, and slow-SMA remain excluded.",
            "Saved research evidence plus F6/F7 targeted checks; portfolio backtests require accounting consistency before promotion-evidence use.",
            "qqq100_research_seed_only",
            "portfolio_backtests_not_promotion_evidence_until_accounting_review",
            "keep QQQ100 as the only seed; add accounting verifier before future candidates use portfolio evidence",
        ),
        LadderStage(
            "preview_candidate",
            "QQQ100 saved preview/review only; no preview promotion is created by this design checkpoint.",
            "Saved QQQ100 signal/review evidence, exact position-unknown handling, and explicit human review.",
            "design_only_no_preview_promotion",
            "unknown_position_must_block_manual_review_not_assume_flat",
            "design a separate non-execution preview step later, starting QQQ100 only",
        ),
        LadderStage(
            "paper_live_candidate",
            "QQQ100 monitoring state only: aligned long 1, no action required, no repeat, follow-up, or flatten order approved.",
            "Saved paper-live monitoring, follow-up policy, evidence audit, manual flatten readiness/runbook, and manual review before any action discussion.",
            "qqq100_monitor_only_aligned_long_one",
            "repeat_followup_flatten_order_not_approved",
            "hold_no_action_and_monitor_only; do not add candidates without separate review",
        ),
        LadderStage(
            "manually_executable_candidate",
            "No generic manually executable candidates; QQQ100 remains separate, explicit, confirmation-gated, and not repeat-approved.",
            "Separate manual confirmation, broker/readiness gates, exact one-share/zero-share design, and human approval per action.",
            "generic_manual_execution_not_implemented",
            "scheduled_or_automatic_execution_forbidden",
            "do not implement generic execution until QQQ100-only design review is complete",
        ),
    ]


def stage_to_row(stage: LadderStage) -> dict[str, Any]:
    return {
        "ladder_stage": stage.ladder_stage,
        "current_allowed_scope": stage.current_allowed_scope,
        "required_evidence": stage.required_evidence,
        "current_status": stage.current_status,
        "blocker": stage.blocker,
        "future_action_required": stage.future_action_required,
        **ROW_SAFETY,
    }


def build_summary_rows(stages: list[LadderStage]) -> list[dict[str, Any]]:
    items = [
        (
            "final_design_status",
            "paper_live_promotion_ladder_design_report_only",
            "The generic ladder is documented only; no promotion or execution logic is implemented.",
        ),
        (
            "only_current_ladder_seed",
            f"{STRATEGY_NAME}:{TICKER}",
            "QQQ100 is the only current ladder seed.",
        ),
        (
            "current_qqq100_state",
            "monitor_only_aligned_long_one_no_action_required",
            "Saved state remains QQQ100 aligned long one share with no repeat/follow-up order approved.",
        ),
        (
            "qqq100_manual_flatten_status",
            "flatten_not_needed_currently_and_not_approved",
            "Saved flatten readiness says flatten is not currently needed, and flatten execution remains unapproved.",
        ),
        (
            "qqq100_manual_flatten_runbook_status",
            "manual_flatten_runbook_not_needed_currently",
            "Saved flatten runbook says the current aligned-long state does not need a flatten discussion.",
        ),
        (
            "future_multi_sleeve_status",
            "future_only_not_promoted",
            "Eventual paper-live direction may be QQQ-led multi-sleeve from research, but not in this checkpoint.",
        ),
        (
            "high_growth_status",
            "research_only_not_promoted",
            "High-growth remains research-only.",
        ),
        (
            "crypto_status",
            "research_only_not_promoted",
            "Crypto remains research-only.",
        ),
        (
            "defensive_sleeve_status",
            "future_review_only",
            "Defensive sleeves remain future-review only.",
        ),
        (
            "sma_slow_sma_status",
            "not_paper_live_promotion_candidates",
            "No SMA or slow-SMA paper-live promotion is allowed by this design.",
        ),
        (
            "portfolio_backtest_evidence_status",
            "blocked_until_accounting_consistency_proven",
            "F7 keeps portfolio backtests out of promotion evidence until starting-cash/accounting consistency is proven.",
        ),
        (
            "unknown_position_boundary",
            "unknown_position_blocks_manual_review",
            "F6 requires unknown position state to block/manual-review rather than assume flat.",
        ),
        (
            "required_stage_count",
            str(len(stages)),
            "The design includes research_candidate, preview_candidate, paper_live_candidate, and manually_executable_candidate.",
        ),
        (
            "next_safe_development_step",
            "review_step12_design_with_f6_f7_and_flatten_boundaries_before_any_implementation",
            "Review this report before any future ladder implementation; do not add execution or scheduling.",
        ),
    ]
    return [summary_row(name, value, details) for name, value, details in items]


def build_blocker_rows() -> list[dict[str, Any]]:
    blockers = [
        (
            "multi_sleeve_future_only",
            "blocked",
            "high",
            "Multi-sleeve paper-live direction is future-only and must not change current QQQ100-only monitoring.",
            "Complete separate accounting, evidence, and manual-review checkpoints before any candidate discussion.",
        ),
        (
            "portfolio_backtests_not_promotion_evidence",
            "blocked",
            "high",
            "Portfolio backtests must not become promotion evidence until starting-cash/accounting consistency is proven.",
            "Add accounting consistency proof before using portfolio metrics in promotion decisions.",
        ),
        (
            "unknown_position_not_flat",
            "blocked",
            "high",
            "Unknown position state must block/manual-review and must not be treated as flat or aligned.",
            "Keep F6 targeted checks passing before any future ladder work.",
        ),
        (
            "manual_flatten_not_approved",
            "blocked",
            "high",
            "The saved manual flatten readiness/runbook checkpoints show flatten is not currently needed and not approved.",
            "Keep flatten as a separate manual review path if a future saved flat signal appears.",
        ),
        (
            "high_growth_crypto_defensive_research_only",
            "blocked",
            "medium",
            "High-growth and crypto remain research-only; defensive sleeves remain future-review only.",
            "Do not promote these branches without separate saved-output review and human approval.",
        ),
        (
            "sma_slow_sma_not_candidates",
            "blocked",
            "high",
            "SMA and slow-SMA are not paper-live promotion candidates.",
            "Keep SMA and slow-SMA outside the future ladder unless a separate approved design changes that.",
        ),
        (
            "scheduled_execution_forbidden",
            "blocked",
            "critical",
            "Order-capable commands must never be scheduled.",
            "Keep Hermes/VPS scheduling monitoring-only; do not schedule execution.",
        ),
    ]
    return [
        blocker_row(name, status, severity, details, next_step)
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows() -> list[dict[str, Any]]:
    evidence = [
        (
            "current_pushed_checkpoints",
            "5d4ea15;1fd1217;2d951f6",
            "Checklist closeout, F6/F7 audit, and F6/F7 targeted checks are established checkpoints.",
        ),
        (
            "qqq100_current_monitoring_state",
            "aligned_long_one_no_action_required",
            "QQQ100 is the only current seed and remains monitor-only with no repeat/follow-up order approved.",
        ),
        (
            "qqq100_manual_flatten_checkpoints",
            "flatten_not_needed_currently;manual_flatten_runbook_not_needed_currently",
            "Flatten readiness and runbook checkpoints exist and do not approve flatten execution.",
        ),
        (
            "required_ladder_stages",
            "research_candidate;preview_candidate;paper_live_candidate;manually_executable_candidate",
            "These are design labels only and do not implement promotion logic.",
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
        "Paper-live promotion ladder design complete. Report only; no promotion, orders, or scheduling approved.",
        f"final_design_status={summary_value(summary_rows, 'final_design_status')}",
        f"only_current_ladder_seed={summary_value(summary_rows, 'only_current_ladder_seed')}",
        f"current_qqq100_state={summary_value(summary_rows, 'current_qqq100_state')}",
        f"qqq100_manual_flatten_status={summary_value(summary_rows, 'qqq100_manual_flatten_status')}",
        f"qqq100_manual_flatten_runbook_status={summary_value(summary_rows, 'qqq100_manual_flatten_runbook_status')}",
        f"future_multi_sleeve_status={summary_value(summary_rows, 'future_multi_sleeve_status')}",
        f"portfolio_backtest_evidence_status={summary_value(summary_rows, 'portfolio_backtest_evidence_status')}",
        f"unknown_position_boundary={summary_value(summary_rows, 'unknown_position_boundary')}",
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
