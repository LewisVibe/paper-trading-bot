"""Saved-output paper-live promotion ladder status scaffold.

This module turns the existing report-only ladder design into a repeatable
status table. It reads saved CSV outputs only. It does not promote strategies,
call Alpaca, read positions, refresh market data, create order instructions,
submit/cancel/replace orders, write SQLite, send alerts, schedule anything, or
approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

INPUT_FILES = {
    "ladder_design_summary": Path("data/paper_live_promotion_ladder_design_summary.csv"),
    "paper_live_monitoring_summary": Path("data/paper_live_monitoring_status.csv"),
    "daily_decision_summary": Path("data/qqq100_daily_decision_summary.csv"),
    "flatten_readiness_summary": Path("data/qqq100_manual_flatten_readiness_summary.csv"),
    "flatten_runbook_summary": Path("data/qqq100_manual_flatten_runbook_summary.csv"),
}

OUTPUT_FILES = {
    "status": Path("data/paper_live_promotion_ladder_status.csv"),
    "summary": Path("data/paper_live_promotion_ladder_status_summary.csv"),
    "blockers": Path("data/paper_live_promotion_ladder_status_blockers.csv"),
    "evidence": Path("data/paper_live_promotion_ladder_status_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "flatten_execution_approved": False,
    "manual_flatten_approved": False,
    "promotion_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "status_only": True,
    "saved_output_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

STATUS_COLUMNS = [
    "ladder_item",
    "ladder_stage",
    "strategy_or_branch",
    "ticker",
    "current_status",
    "promotion_path_status",
    "blocker",
    "required_next_step",
    "research_only",
    "report_only",
    "status_only",
    "saved_output_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "alpaca_called",
    "live_positions_read",
    "market_data_refreshed",
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass(frozen=True)
class LadderStatusContext:
    design_status: str
    qqq100_state: str
    daily_decision_status: str
    flatten_status: str
    flatten_runbook_status: str
    qqq100_monitoring_consistent: bool
    design_present: bool
    monitoring_present: bool


@dataclass
class PaperLivePromotionLadderStatusResult:
    output_paths: dict[str, Path]
    status_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_promotion_ladder_status(root_dir: Path | str = ".") -> PaperLivePromotionLadderStatusResult:
    root = Path(root_dir)
    context = build_ladder_status_context(root)
    status_rows = build_status_rows(context)
    summary_rows = build_summary_rows(context)
    blocker_rows = build_blocker_rows(context)
    evidence_rows = build_evidence_rows(context)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["status"], STATUS_COLUMNS, status_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLivePromotionLadderStatusResult(
        output_paths=output_paths,
        status_rows=status_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_promotion_ladder_status(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live promotion ladder status is missing.",
            "Run `python bot.py --paper-live-promotion-ladder-status` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live promotion ladder status saved display. Report only; no promotion or orders approved.",
        f"final_ladder_status: {summary_value(rows, 'final_ladder_status')}",
        f"current_seed: {summary_value(rows, 'current_seed')}",
        f"qqq100_ladder_status: {summary_value(rows, 'qqq100_ladder_status')}",
        f"qqq100_daily_decision_status: {summary_value(rows, 'qqq100_daily_decision_status')}",
        f"qqq100_flatten_status: {summary_value(rows, 'qqq100_flatten_status')}",
        f"qqq100_flatten_runbook_status: {summary_value(rows, 'qqq100_flatten_runbook_status')}",
        f"blocked_branches: {summary_value(rows, 'blocked_branches')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; flatten_execution_approved=false; manual_flatten_approved=false; promotion_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_ladder_status_context(root: Path) -> LadderStatusContext:
    design_rows = read_csv_rows(root / INPUT_FILES["ladder_design_summary"])
    monitoring_rows = read_csv_rows(root / INPUT_FILES["paper_live_monitoring_summary"])
    daily_rows = read_csv_rows(root / INPUT_FILES["daily_decision_summary"])
    flatten_rows = read_csv_rows(root / INPUT_FILES["flatten_readiness_summary"])
    runbook_rows = read_csv_rows(root / INPUT_FILES["flatten_runbook_summary"])

    qqq100_state = summary_value(monitoring_rows, "recommended_next_step")
    monitoring_consistent = (
        summary_value(monitoring_rows, "active_strategy") == STRATEGY_NAME
        and summary_value(monitoring_rows, "active_ticker") == TICKER
        and summary_value(monitoring_rows, "saved_position_quantity") == "1"
        and summary_value(monitoring_rows, "alignment_state") == "aligned_long"
        and summary_value(monitoring_rows, "recommended_next_step") == "hold_no_action_and_monitor_only"
        and summary_value(monitoring_rows, "execution_approved") == "False"
    )
    return LadderStatusContext(
        design_status=summary_value(design_rows, "final_design_status") or "missing_saved_ladder_design",
        qqq100_state=qqq100_state or "missing_saved_paper_live_monitoring",
        daily_decision_status=summary_value(daily_rows, "daily_decision_status") or "missing_saved_daily_decision",
        flatten_status=summary_value(flatten_rows, "flatten_readiness_status") or "missing_saved_flatten_readiness",
        flatten_runbook_status=summary_value(runbook_rows, "runbook_status") or "missing_saved_flatten_runbook",
        qqq100_monitoring_consistent=monitoring_consistent,
        design_present=bool(design_rows),
        monitoring_present=bool(monitoring_rows),
    )


def build_status_rows(context: LadderStatusContext) -> list[dict[str, Any]]:
    qqq_status = (
        "qqq100_seed_monitor_only_no_action"
        if context.qqq100_monitoring_consistent
        else "qqq100_seed_manual_review_required"
    )
    qqq_blocker = "none_monitor_only" if context.qqq100_monitoring_consistent else "missing_or_inconsistent_saved_qqq100_monitoring"
    return [
        status_row(
            "qqq100_research_candidate",
            "research_candidate",
            STRATEGY_NAME,
            TICKER,
            "passed_current_seed_only",
            "seed_only_not_generic_promotion",
            "portfolio_backtests_not_promotion_evidence_until_accounting_review",
            "keep QQQ100 as only seed; prove F7 accounting before adding portfolio evidence",
        ),
        status_row(
            "qqq100_preview_candidate",
            "preview_candidate",
            STRATEGY_NAME,
            TICKER,
            "manual_review_report_only",
            "preview_discussion_only_not_promotion",
            "unknown_positions_must_block_manual_review",
            "keep F6 unknown-position checks passing before preview implementation changes",
        ),
        status_row(
            "qqq100_paper_live_candidate",
            "paper_live_candidate",
            STRATEGY_NAME,
            TICKER,
            qqq_status,
            "monitor_only_aligned_long_one",
            qqq_blocker,
            "hold_no_action_and_monitor_only",
        ),
        status_row(
            "qqq100_manually_executable_candidate",
            "manually_executable_candidate",
            STRATEGY_NAME,
            TICKER,
            "blocked_not_implemented",
            "manual_execution_path_separate_and_not_repeat_approved",
            "manual_execution_not_approved_by_ladder_status",
            "do not implement generic execution without separate explicit design",
        ),
        status_row(
            "high_growth_branch",
            "blocked_branch",
            "high_growth",
            "multiple",
            "blocked_research_only",
            "not_promoted",
            "concentration_drawdown_attribution_and_f7_review_required",
            "keep high-growth research-only",
        ),
        status_row(
            "crypto_branch",
            "blocked_branch",
            "crypto",
            "multiple",
            "blocked_research_only",
            "not_promoted",
            "crypto_execution_not_approved",
            "keep crypto research-only",
        ),
        status_row(
            "defensive_sleeve_branch",
            "future_review_branch",
            "defensive_sleeve",
            "multiple",
            "future_review_only",
            "not_promoted",
            "separate_saved_evidence_and_ladder_review_required",
            "keep defensive sleeve future-review only",
        ),
        status_row(
            "sma_slow_sma_branch",
            "excluded_branch",
            "sma_and_slow_sma",
            "multiple",
            "excluded",
            "not_promoted",
            "sma_slow_sma_not_paper_live_candidates",
            "do not use SMA or slow-SMA for paper-live promotion",
        ),
    ]


def status_row(
    ladder_item: str,
    ladder_stage: str,
    strategy_or_branch: str,
    ticker: str,
    current_status: str,
    promotion_path_status: str,
    blocker: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "ladder_item": ladder_item,
        "ladder_stage": ladder_stage,
        "strategy_or_branch": strategy_or_branch,
        "ticker": ticker,
        "current_status": current_status,
        "promotion_path_status": promotion_path_status,
        "blocker": blocker,
        "required_next_step": required_next_step,
        **ROW_SAFETY,
    }


def build_summary_rows(context: LadderStatusContext) -> list[dict[str, Any]]:
    final_status = (
        "paper_live_promotion_ladder_status_report_only"
        if context.design_present and context.qqq100_monitoring_consistent
        else "paper_live_promotion_ladder_status_manual_review_required"
    )
    rows = [
        ("final_ladder_status", final_status, "Current saved-output promotion ladder status."),
        ("current_seed", f"{STRATEGY_NAME}:{TICKER}", "QQQ100 is the only current seed."),
        ("qqq100_ladder_status", "monitor_only_aligned_long_one" if context.qqq100_monitoring_consistent else "manual_review_required", "Current QQQ100 paper-live ladder status."),
        ("qqq100_daily_decision_status", context.daily_decision_status, "Saved QQQ100 daily decision status."),
        ("qqq100_flatten_status", context.flatten_status, "Saved QQQ100 manual flatten readiness status."),
        ("qqq100_flatten_runbook_status", context.flatten_runbook_status, "Saved QQQ100 manual flatten runbook status."),
        ("design_status", context.design_status, "Saved Step 12 design status."),
        ("blocked_branches", "high_growth;crypto;defensive_sleeve;sma;slow_sma", "Non-QQQ branches are not promoted."),
        ("portfolio_backtest_evidence_status", "blocked_until_accounting_consistency_proven", "F7 accounting proof is required before portfolio backtests become promotion evidence."),
        ("unknown_position_boundary", "unknown_position_blocks_manual_review", "F6 unknown positions must stay loud."),
        ("next_safe_development_step", "review_ladder_status_then_add_f7_accounting_proof_before_any_broader_promotion", "Next step remains report/test-only."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must not be scheduled."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("repeat_execution_approved", "False", "Repeat execution approval remains false."),
        ("flatten_execution_approved", "False", "Flatten execution approval remains false."),
        ("manual_flatten_approved", "False", "Manual flatten approval remains false."),
        ("promotion_approved", "False", "Promotion approval remains false."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(context: LadderStatusContext) -> list[dict[str, Any]]:
    blockers = [
        ("promotion_not_approved", "blocked", "critical", "This ladder status does not approve promotion.", "Do not wire strategies to execution."),
        ("execution_not_approved", "blocked", "critical", "Execution and paper execution remain unapproved.", "Do not run order-capable commands from this status."),
        ("portfolio_backtests_not_promotion_evidence", "blocked", "high", "Portfolio metrics require accounting proof before promotion use.", "Add F7 accounting proof before broader promotion work."),
        ("unknown_position_not_flat", "blocked", "high", "Unknown positions must block/manual-review.", "Keep F6 targeted checks passing."),
        ("non_qqq_branches_not_promoted", "blocked", "high", "High-growth, crypto, defensive, SMA, and slow-SMA are not promoted.", "Keep non-QQQ branches research-only or future-review."),
        ("scheduled_execution_forbidden", "blocked", "critical", "Order-capable commands must never be scheduled.", "Keep Hermes/VPS monitoring-only."),
    ]
    if not context.design_present:
        blockers.insert(0, ("missing_ladder_design", "manual_review_required", "high", "Saved ladder design summary is missing.", "Run the report-only ladder design command first."))
    if not context.monitoring_present or not context.qqq100_monitoring_consistent:
        blockers.insert(0, ("missing_or_inconsistent_qqq100_monitoring", "manual_review_required", "high", "Saved QQQ100 monitoring status is missing or inconsistent.", "Refresh report-only paper-live monitoring status first."))
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows(context: LadderStatusContext) -> list[dict[str, Any]]:
    rows = [
        ("ladder_design_present", str(context.design_present), "Saved ladder design summary presence."),
        ("paper_live_monitoring_present", str(context.monitoring_present), "Saved paper-live monitoring summary presence."),
        ("qqq100_monitoring_consistent", str(context.qqq100_monitoring_consistent), "Saved QQQ100 monitoring state consistency."),
        ("daily_decision_status", context.daily_decision_status, "Saved QQQ100 daily decision status."),
        ("flatten_readiness_status", context.flatten_status, "Saved QQQ100 flatten readiness status."),
        ("flatten_runbook_status", context.flatten_runbook_status, "Saved QQQ100 flatten runbook status."),
        ("approval_flags", "all_false", "Execution, paper execution, scheduling, live trading, follow-up, repeat, flatten, and promotion approvals remain false."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live promotion ladder status complete. Report only; no promotion, orders, or scheduling approved.",
        f"final_ladder_status={summary_value(summary_rows, 'final_ladder_status')}",
        f"current_seed={summary_value(summary_rows, 'current_seed')}",
        f"qqq100_ladder_status={summary_value(summary_rows, 'qqq100_ladder_status')}",
        f"qqq100_daily_decision_status={summary_value(summary_rows, 'qqq100_daily_decision_status')}",
        f"qqq100_flatten_status={summary_value(summary_rows, 'qqq100_flatten_status')}",
        f"qqq100_flatten_runbook_status={summary_value(summary_rows, 'qqq100_flatten_runbook_status')}",
        f"blocked_branches={summary_value(summary_rows, 'blocked_branches')}",
        f"next_safe_development_step={summary_value(summary_rows, 'next_safe_development_step')}",
        f"saved_report={output_paths['status']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; flatten_execution_approved=false; manual_flatten_approved=false; promotion_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
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
