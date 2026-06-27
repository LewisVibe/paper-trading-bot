"""Report-only roadmap for volatility-targeted multi-sleeve paper-live work.

This checkpoint documents a future direction only. It does not implement
portfolio execution, call Alpaca, read positions, refresh market data, create
orders, write SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "report": Path("data/paper_live_multi_sleeve_roadmap.csv"),
    "summary": Path("data/paper_live_multi_sleeve_roadmap_summary.csv"),
    "blockers": Path("data/paper_live_multi_sleeve_roadmap_blockers.csv"),
    "evidence": Path("data/paper_live_multi_sleeve_roadmap_evidence.csv"),
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
    "roadmap_only": True,
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
    "sleeve_name",
    "current_status",
    "future_ladder_stage",
    "required_evidence_before_next_stage",
    "current_blocker",
    "research_only",
    "report_only",
    "roadmap_only",
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
class RoadmapSleeve:
    sleeve_name: str
    current_status: str
    future_ladder_stage: str
    required_evidence_before_next_stage: str
    current_blocker: str


@dataclass
class PaperLiveMultiSleeveRoadmapResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_multi_sleeve_roadmap(root_dir: Path | str = ".") -> PaperLiveMultiSleeveRoadmapResult:
    root = Path(root_dir)
    sleeves = build_roadmap_sleeves()
    report_rows = [sleeve_to_row(sleeve) for sleeve in sleeves]
    summary_rows = build_summary_rows(sleeves)
    blocker_rows = build_blocker_rows()
    evidence_rows = build_evidence_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveMultiSleeveRoadmapResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_multi_sleeve_roadmap(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live multi-sleeve roadmap is missing.",
            "Run `python bot.py --paper-live-multi-sleeve-roadmap` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live multi-sleeve roadmap saved display. Report only; no portfolio execution approved.",
        f"final_roadmap_status: {summary_value(rows, 'final_roadmap_status')}",
        f"roadmap_direction: {summary_value(rows, 'roadmap_direction')}",
        f"qqq100_core_status: {summary_value(rows, 'qqq100_core_status')}",
        f"defensive_sleeve_status: {summary_value(rows, 'defensive_sleeve_status')}",
        f"high_growth_sleeve_status: {summary_value(rows, 'high_growth_sleeve_status')}",
        f"crypto_sleeve_status: {summary_value(rows, 'crypto_sleeve_status')}",
        f"allocator_status: {summary_value(rows, 'allocator_status')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_roadmap_sleeves() -> list[RoadmapSleeve]:
    return [
        RoadmapSleeve(
            "qqq100_core_sleeve",
            "previous_seed_context_aligned_long_one_monitor_only_no_action_required",
            "previous_paper_live_candidate_monitor_only",
            "Saved QQQ100 monitoring, follow-up policy, evidence audit, and promotion ladder design remain clean as previous-seed context.",
            "no_repeat_followup_order_approved_current_phase_is_monitor_only",
        ),
        RoadmapSleeve(
            "defensive_sleeve",
            "future_review_only",
            "research_candidate_future_review",
            "Separate saved defensive evidence, F6/F7 targeted checks, and promotion ladder review.",
            "must_pass_promotion_ladder_separately_before_preview_or_paper_live_discussion",
        ),
        RoadmapSleeve(
            "high_growth_sleeve",
            "research_only",
            "research_candidate_blocked",
            "Concentration, drawdown, attribution, outlier, and survivorship-bias review must be complete first.",
            "concentration_drawdown_attribution_review_required_before_preview_or_paper_live_discussion",
        ),
        RoadmapSleeve(
            "crypto_sleeve",
            "research_only_capped_future_only_no_crypto_execution_approved",
            "research_candidate_blocked",
            "Capped allocation research, custody/execution boundary review, and separate non-execution promotion evidence.",
            "crypto_execution_not_approved_and_crypto_remains_future_only",
        ),
        RoadmapSleeve(
            "multi_sleeve_allocator",
            "current_report_status_seed_no_portfolio_execution_wiring_no_order_instructions_no_scheduling",
            "current_report_status_seed_manual_review_required",
            "Accounting consistency, position unknown handling, allocation caps, manual approval policy, and no scheduled execution before any preview or paper-live implementation.",
            "portfolio_execution_wiring_forbidden_until_separate_manual_review_and_tests",
        ),
    ]


def sleeve_to_row(sleeve: RoadmapSleeve) -> dict[str, Any]:
    return {
        "sleeve_name": sleeve.sleeve_name,
        "current_status": sleeve.current_status,
        "future_ladder_stage": sleeve.future_ladder_stage,
        "required_evidence_before_next_stage": sleeve.required_evidence_before_next_stage,
        "current_blocker": sleeve.current_blocker,
        **ROW_SAFETY,
    }


def build_summary_rows(sleeves: list[RoadmapSleeve]) -> list[dict[str, Any]]:
    items = [
        (
            "final_roadmap_status",
            "paper_live_multi_sleeve_roadmap_report_only",
            "The roadmap is documentation/report output only; no portfolio execution is implemented.",
        ),
        (
            "roadmap_direction",
            "vol_targeted_multi_sleeve_report_status_seed_from_research",
            "Volatility-targeted multi-sleeve is the current report/status seed; QQQ100 remains previous-seed monitor-only context.",
        ),
        (
            "qqq100_core_status",
            "previous_seed_context_aligned_long_one_monitor_only",
            "QQQ100 remains previous-seed context, aligned long one share, monitor-only, and no repeat/follow-up/flatten order is approved.",
        ),
        (
            "active_seed_status",
            "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x_report_status_seed",
            "The volatility-targeted multi-sleeve seed is active for reporting/status only, not execution.",
        ),
        (
            "defensive_sleeve_status",
            "future_review_only_must_pass_ladder_separately",
            "Defensive sleeve is future review only.",
        ),
        (
            "high_growth_sleeve_status",
            "research_only_concentration_drawdown_attribution_required",
            "High-growth sleeve must pass concentration, drawdown, and attribution review before next-stage discussion.",
        ),
        (
            "crypto_sleeve_status",
            "research_only_capped_future_only_no_execution_approved",
            "Crypto sleeve remains research-only with no crypto execution approved.",
        ),
        (
            "allocator_status",
            "current_report_status_seed_no_portfolio_execution_wiring",
            "Allocator remains report/status only with no order instructions, no portfolio execution wiring, and no scheduling.",
        ),
        (
            "excluded_strategy_status",
            "sma_slow_sma_not_paper_live_promotion_candidates",
            "SMA and slow-SMA remain excluded from paper-live promotion.",
        ),
        (
            "required_sleeve_count",
            str(len(sleeves)),
            "Roadmap includes QQQ100 core, defensive, high-growth, crypto, and allocator sleeves.",
        ),
        (
            "next_safe_development_step",
            "observe_enabled_status_cron_then_review_non_executable_action_preview_design",
            "Observe the enabled monitoring cron first, then review any non-executable action-preview design separately.",
        ),
    ]
    return [summary_row(name, value, details) for name, value, details in items]


def build_blocker_rows() -> list[dict[str, Any]]:
    blockers = [
        (
            "current_phase_vol_targeted_status_only_monitoring",
            "blocked",
            "high",
            "Current phase is volatility-targeted multi-sleeve status/report monitoring only; no multi-sleeve action is approved.",
            "Keep volatility seed monitoring report-only and QQQ100 previous-seed hold/no-action context until a separate implementation is approved.",
        ),
        (
            "portfolio_execution_wiring_forbidden",
            "blocked",
            "critical",
            "No portfolio execution wiring or order instructions are allowed by this roadmap.",
            "Do not connect allocator or sleeve outputs to execution.",
        ),
        (
            "high_growth_reviews_required",
            "blocked",
            "high",
            "High-growth sleeve requires concentration, drawdown, attribution, outlier, and survivorship-bias review.",
            "Complete saved-output review packs before any preview/paper-live discussion.",
        ),
        (
            "crypto_execution_not_approved",
            "blocked",
            "high",
            "Crypto remains research-only/capped/future-only with no execution approved.",
            "Keep crypto out of execution until separate design and approval exist.",
        ),
        (
            "scheduled_execution_forbidden",
            "blocked",
            "critical",
            "Order-capable commands and portfolio execution must never be scheduled.",
            "Keep Hermes/VPS scheduling monitoring-only.",
        ),
    ]
    return [
        blocker_row(name, status, severity, details, next_step)
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows() -> list[dict[str, Any]]:
    evidence = [
        (
            "current_checkpoint",
            "c35efc7",
            "Paper-live promotion ladder design exists and remains report-only.",
        ),
        (
            "active_seed_monitoring_state",
            "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x;MULTI_SLEEVE;report_status_only_no_execution",
            "Volatility-targeted multi-sleeve is the current report/status seed only.",
        ),
        (
            "previous_qqq100_state",
            "aligned_long_one_monitor_only_no_repeat_followup_order_approved",
            "QQQ100 remains previous-seed context, aligned long one share with no action required.",
        ),
        (
            "roadmap_sleeves",
            "qqq100_core_sleeve;defensive_sleeve;high_growth_sleeve;crypto_sleeve;multi_sleeve_allocator",
            "These are future roadmap components only, not executable allocations.",
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
        "Paper-live multi-sleeve roadmap complete. Report only; no portfolio execution, orders, or scheduling approved.",
        f"final_roadmap_status={summary_value(summary_rows, 'final_roadmap_status')}",
        f"roadmap_direction={summary_value(summary_rows, 'roadmap_direction')}",
        f"active_seed_status={summary_value(summary_rows, 'active_seed_status')}",
        f"qqq100_core_status={summary_value(summary_rows, 'qqq100_core_status')}",
        f"defensive_sleeve_status={summary_value(summary_rows, 'defensive_sleeve_status')}",
        f"high_growth_sleeve_status={summary_value(summary_rows, 'high_growth_sleeve_status')}",
        f"crypto_sleeve_status={summary_value(summary_rows, 'crypto_sleeve_status')}",
        f"allocator_status={summary_value(summary_rows, 'allocator_status')}",
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
