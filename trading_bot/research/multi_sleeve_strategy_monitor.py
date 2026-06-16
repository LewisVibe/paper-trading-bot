"""Saved-output-only multi-sleeve strategy monitoring/design report.

This report lets the QQQ100 paper milestone sit beside research-only strategy
families without connecting those families to execution. It reads saved CSV
artefacts only and does not call Alpaca, refresh market data, read live
positions, create orders, write SQLite, send alerts, schedule anything, or
approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FINAL_MONITOR_STATUS = "multi_sleeve_monitor_created"
ACTIVE_PAPER_SLEEVE = "qqq100_core_trend_sleeve"
RESEARCH_ONLY_SLEEVES = [
    "defensive_etf_research_sleeve",
    "high_growth_stock_research_sleeve",
    "crypto_research_sleeve",
]
BIGGEST_BLOCKER = "sleeve_allocation_policy_requires_manual_review"
RECOMMENDED_NEXT_STEP = "build_research_scoreboard_for_candidate_sleeves_before_any_new_execution_wiring"

INPUT_FILES = {
    "paper_summary": Path("data/paper_execution_state_summary.csv"),
    "paper_positions": Path("data/paper_execution_state_positions.csv"),
    "qqq100_postcheck": Path("data/qqq100_paper_postcheck.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_repeat_design": Path("data/qqq100_repeat_alignment_workflow_design.csv"),
    "qqq100_repeat_states": Path("data/qqq100_repeat_alignment_workflow_states.csv"),
    "portfolio_preview": Path("data/multi_strategy_portfolio_preview.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "high_growth_branch": Path("data/high_growth_stock_branch_decision_checkpoint.csv"),
    "high_growth_final_validation": Path("data/high_growth_stock_final_validation_pack.csv"),
    "crypto_lab": Path("data/crypto_strategy_lab_results.csv"),
    "crypto_state": Path("data/crypto_research_state_report.csv"),
    "project_research_state": Path("data/project_research_state_summary.csv"),
    "current_research_state": Path("data/current_research_state.csv"),
}

OUTPUT_FILES = {
    "monitor": Path("data/multi_sleeve_strategy_monitor.csv"),
    "sleeves": Path("data/multi_sleeve_strategy_sleeves.csv"),
    "positions": Path("data/multi_sleeve_strategy_positions.csv"),
    "blockers": Path("data/multi_sleeve_strategy_blockers.csv"),
    "next_steps": Path("data/multi_sleeve_strategy_next_steps.csv"),
}

SAFETY_COLUMNS = [
    "report_only",
    "monitor_only",
    "design_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "general_execution_approved",
    "qqq100_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "high_growth_execution_approved",
    "crypto_execution_approved",
]

SAFETY_FLAGS = {
    "report_only": True,
    "monitor_only": True,
    "design_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "general_execution_approved": False,
    "qqq100_execution_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "high_growth_execution_approved": False,
    "crypto_execution_approved": False,
}

MONITOR_COLUMNS = [
    "created_at",
    "final_monitor_status",
    "active_paper_sleeve_count",
    "active_paper_sleeve",
    "research_only_sleeves",
    "blocked_sleeves",
    "qqq_current_saved_position",
    "qqq_current_saved_alignment",
    "biggest_blocker",
    "recommended_next_step",
    "details",
    *SAFETY_COLUMNS,
]

SLEEVE_COLUMNS = [
    "created_at",
    "sleeve_name",
    "sleeve_status",
    "strategy_name",
    "ticker_scope",
    "current_max_paper_position",
    "paper_position_status",
    "execution_boundary",
    "monitoring_role",
    "risk_warning",
    "required_next_step",
    *SAFETY_COLUMNS,
]

POSITION_COLUMNS = [
    "created_at",
    "sleeve_name",
    "ticker",
    "saved_position_status",
    "saved_position_quantity_abs",
    "saved_alignment_state",
    "evidence_source",
    "details",
    *SAFETY_COLUMNS,
]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_COLUMNS,
]

NEXT_STEP_COLUMNS = [
    "created_at",
    "step_name",
    "step_status",
    "details",
    "required_before_new_execution_wiring",
    *SAFETY_COLUMNS,
]


@dataclass
class MultiSleeveStrategyMonitorResult:
    output_paths: dict[str, Path]
    monitor_rows: list[dict[str, Any]]
    sleeve_rows: list[dict[str, Any]]
    position_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    next_step_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_strategy_monitor(root_dir: Path | str = ".") -> MultiSleeveStrategyMonitorResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    context = build_context(inputs)
    sleeve_rows = build_sleeve_rows(created_at, context)
    monitor_rows = build_monitor_rows(created_at, context, sleeve_rows)
    position_rows = build_position_rows(created_at, context)
    blocker_rows = build_blocker_rows(created_at)
    next_step_rows = build_next_step_rows(created_at)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["monitor"], MONITOR_COLUMNS, monitor_rows)
    write_rows(output_paths["sleeves"], SLEEVE_COLUMNS, sleeve_rows)
    write_rows(output_paths["positions"], POSITION_COLUMNS, position_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["next_steps"], NEXT_STEP_COLUMNS, next_step_rows)
    return MultiSleeveStrategyMonitorResult(
        output_paths=output_paths,
        monitor_rows=monitor_rows,
        sleeve_rows=sleeve_rows,
        position_rows=position_rows,
        blocker_rows=blocker_rows,
        next_step_rows=next_step_rows,
        summary_lines=build_summary_lines(monitor_rows[0], output_paths["monitor"]),
    )


def show_multi_sleeve_strategy_monitor(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    monitor_path = root / OUTPUT_FILES["monitor"]
    if not monitor_path.exists():
        return 1, [
            "Multi-sleeve strategy monitor is missing.",
            "Run `python bot.py --multi-sleeve-strategy-monitor` first.",
            "execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(monitor_path)
    row = rows[0] if rows else {}
    return 0, [
        "Multi-sleeve strategy monitor. Saved-output-only design; no new execution path approved.",
        f"final_monitor_status: {row.get('final_monitor_status', 'missing')}",
        f"active paper sleeve count: {row.get('active_paper_sleeve_count', 'missing')}",
        f"active paper sleeve: {row.get('active_paper_sleeve', 'missing')}",
        f"QQQ current saved position/alignment: {row.get('qqq_current_saved_position', 'missing')} / {row.get('qqq_current_saved_alignment', 'missing')}",
        f"research-only sleeves: {row.get('research_only_sleeves', 'missing')}",
        f"blocked sleeves: {row.get('blocked_sleeves', 'missing')}",
        f"biggest blocker: {row.get('biggest_blocker', BIGGEST_BLOCKER)}",
        f"recommended next step: {row.get('recommended_next_step', RECOMMENDED_NEXT_STEP)}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    qqq_position_status = first_nonempty(inputs["qqq100_postcheck"], ["position_status"]) or saved_position_value(inputs["paper_positions"], "QQQ", "saved_position_summary") or "saved_position_unavailable"
    qqq_quantity = first_nonempty(inputs["qqq100_postcheck"], ["position_quantity_abs"]) or quantity_from_position_summary(qqq_position_status) or "unavailable"
    qqq_alignment = saved_summary_value(inputs["paper_summary"], "qqq100_alignment_status", "") or first_nonempty(inputs["qqq100_postcheck"], ["alignment_state"]) or first_nonempty(inputs["qqq100_action_preview"], ["alignment_state"]) or "saved_alignment_unavailable"
    qqq_active = is_qqq_active_long_one(qqq_position_status, qqq_quantity, qqq_alignment)
    return {
        "qqq_position_status": qqq_position_status,
        "qqq_quantity": qqq_quantity,
        "qqq_alignment": qqq_alignment,
        "qqq_sleeve_status": "active_paper_position_observed" if qqq_active else "saved_paper_position_not_confirmed",
        "active_paper_sleeve_count": "1" if qqq_active else "0",
        "active_paper_sleeve": ACTIVE_PAPER_SLEEVE if qqq_active else "none",
    }


def build_monitor_rows(created_at: str, context: dict[str, str], sleeve_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocked = [str(row["sleeve_name"]) for row in sleeve_rows if row["sleeve_status"] != "active_paper_position_observed"]
    details = "Saved-output monitor for QQQ100 plus research-only defensive, high-growth, crypto, and cash/no-position sleeves."
    return [
        {
            "created_at": created_at,
            "final_monitor_status": FINAL_MONITOR_STATUS,
            "active_paper_sleeve_count": context["active_paper_sleeve_count"],
            "active_paper_sleeve": context["active_paper_sleeve"],
            "research_only_sleeves": ", ".join(RESEARCH_ONLY_SLEEVES),
            "blocked_sleeves": ", ".join(blocked),
            "qqq_current_saved_position": f"{context['qqq_position_status']}; quantity={context['qqq_quantity']}",
            "qqq_current_saved_alignment": context["qqq_alignment"],
            "biggest_blocker": BIGGEST_BLOCKER,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
            "details": details,
            **safety_flags(),
        }
    ]


def build_sleeve_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        sleeve_row(
            created_at,
            ACTIVE_PAPER_SLEEVE,
            context["qqq_sleeve_status"],
            "qqq_100_trend_gate",
            "QQQ only",
            "1 share",
            f"{context['qqq_position_status']}; quantity={context['qqq_quantity']}; alignment={context['qqq_alignment']}",
            "manual QQQ100 path only; duplicate buys blocked; repeat execution not approved; scheduling not approved",
            "current clean core trend paper-monitor sleeve",
            "qqq100_is_current_only_active_paper_sleeve",
            "Keep QQQ100 capped at one share unless a separate manual review changes the design.",
        ),
        sleeve_row(
            created_at,
            "defensive_etf_research_sleeve",
            "research_or_preview_only",
            "defensive ETF research family",
            "ETF defensive/risk-off candidates only",
            "none",
            "no paper/live execution",
            "execution blocked",
            "possible future drawdown reducer or cash/risk-off sleeve",
            "defensive_sleeve_not_validated_for_execution",
            "Build stronger saved validation before preview/action discussion.",
        ),
        sleeve_row(
            created_at,
            "high_growth_stock_research_sleeve",
            "research_only",
            "high-growth stock research family",
            "high-growth stocks only",
            "none",
            "no paper/live execution",
            "execution blocked",
            "high-risk/high-return research branch only",
            "high_growth_and_qqq_overlap_risk; concentration_drawdown_split_cost_review_required",
            "Keep blocked until manual validation, drawdown, split/cost, and concentration checks improve.",
        ),
        sleeve_row(
            created_at,
            "crypto_research_sleeve",
            "research_only",
            "crypto research family",
            "crypto research universe only",
            "none",
            "no paper/live execution",
            "execution blocked",
            "off-hours research/monitoring route only",
            "crypto_volatility_sleeve_not_ready",
            "Keep crypto research-only; do not wire to execution.",
        ),
        sleeve_row(
            created_at,
            "cash_or_no_position_sleeve",
            "design_only",
            "cash/risk-off allocation concept",
            "flat/cash state only",
            "none",
            "no order behaviour",
            "execution blocked",
            "represents flat/cash/risk-off allocation logic",
            "sleeve_allocation_policy_missing",
            "Define sleeve allocation policy before any new execution wiring.",
        ),
    ]


def build_position_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "sleeve_name": ACTIVE_PAPER_SLEEVE,
            "ticker": "QQQ",
            "saved_position_status": context["qqq_position_status"],
            "saved_position_quantity_abs": context["qqq_quantity"],
            "saved_alignment_state": context["qqq_alignment"],
            "evidence_source": "data/qqq100_paper_postcheck.csv or data/paper_execution_state_positions.csv",
            "details": "Saved QQQ100 paper context only; this monitor did not read live broker positions.",
            **safety_flags(),
        }
    ]


def build_blocker_rows(created_at: str) -> list[dict[str, Any]]:
    blockers = [
        ("qqq100_is_current_only_active_paper_sleeve", "warning", "medium", "Only QQQ100 is allowed to appear as an active paper sleeve.", "Do not generalise execution to other sleeves."),
        ("high_growth_and_qqq_overlap_risk", "blocked", "high", "High-growth stocks may overlap strongly with QQQ/growth beta.", "Build a research scoreboard and overlap review before preview discussion."),
        ("crypto_volatility_sleeve_not_ready", "blocked", "high", "Crypto remains high-volatility and research-only.", "Keep crypto disconnected from execution."),
        ("defensive_sleeve_not_validated_for_execution", "blocked", "high", "Defensive ETF sleeve is not validated for execution.", "Run separate validation before preview/action discussion."),
        ("sleeve_allocation_policy_missing", "blocked", "critical", "No allocation policy exists for multiple sleeves.", "Define allocation policy before any new execution wiring."),
        ("repeat_execution_not_approved", "blocked", "critical", "QQQ100 repeat execution remains unapproved.", "Review QQQ100 repeat/alignment design separately."),
        ("scheduling_not_approved", "blocked", "critical", "No scheduling, Hermes cron, loop, service, or Task Scheduler execution is approved.", "Keep execution commands manual-only."),
        ("portfolio_position_limit_not_generalised", "blocked", "critical", "The one-share QQQ cap is not a general portfolio position policy.", "Do not apply it to other sleeves without review."),
        ("future_manual_review_required", "blocked", "critical", "Any new sleeve movement toward preview/action-preview requires manual review.", RECOMMENDED_NEXT_STEP),
    ]
    return [blocker_row(created_at, *blocker) for blocker in blockers]


def build_next_step_rows(created_at: str) -> list[dict[str, Any]]:
    steps = [
        ("build_research_scoreboard_for_candidate_sleeves", "recommended", "Create saved-output scoreboard for defensive, high-growth, crypto, and QQQ100 evidence before any new execution wiring."),
        ("review_sleeve_allocation_policy", "required", "Define how sleeves would coexist conceptually before preview/action-preview."),
        ("keep_qqq100_as_only_active_paper_sleeve", "required", "Do not add another active paper sleeve from this monitor."),
        ("keep_repeat_execution_unapproved", "required", "Do not expand QQQ100 repeat execution from this monitor."),
        ("keep_scheduling_unapproved", "required", "Do not create Hermes, cron, Task Scheduler, loop, or service execution."),
    ]
    return [
        {
            "created_at": created_at,
            "step_name": name,
            "step_status": status,
            "details": details,
            "required_before_new_execution_wiring": True,
            **safety_flags(),
        }
        for name, status, details in steps
    ]


def sleeve_row(
    created_at: str,
    sleeve_name: str,
    sleeve_status: str,
    strategy_name: str,
    ticker_scope: str,
    max_position: str,
    paper_position_status: str,
    execution_boundary: str,
    monitoring_role: str,
    risk_warning: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "sleeve_name": sleeve_name,
        "sleeve_status": sleeve_status,
        "strategy_name": strategy_name,
        "ticker_scope": ticker_scope,
        "current_max_paper_position": max_position,
        "paper_position_status": paper_position_status,
        "execution_boundary": execution_boundary,
        "monitoring_role": monitoring_role,
        "risk_warning": risk_warning,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def blocker_row(
    created_at: str,
    blocker_name: str,
    status: str,
    severity: str,
    details: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": blocker_name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def build_summary_lines(row: dict[str, Any], output_path: Path) -> list[str]:
    return [
        "Multi-sleeve strategy monitor created. Saved-output monitor/design only; no new execution path approved.",
        f"final_monitor_status: {row['final_monitor_status']}",
        f"active paper sleeve count: {row['active_paper_sleeve_count']}",
        f"active paper sleeve: {row['active_paper_sleeve']}",
        f"QQQ current saved position/alignment: {row['qqq_current_saved_position']} / {row['qqq_current_saved_alignment']}",
        f"research-only sleeves: {row['research_only_sleeves']}",
        f"blocked sleeves: {row['blocked_sleeves']}",
        f"biggest blocker: {row['biggest_blocker']}",
        f"recommended next step: {row['recommended_next_step']}",
        f"Saved monitor: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def is_qqq_active_long_one(position_status: str, quantity: str, alignment: str) -> bool:
    combined = f"{position_status} {quantity} {alignment}".lower()
    return (
        ("paper_position_long" in combined or "long" in combined)
        and quantity.strip() in {"1", "1.0", "1.00"}
        and ("aligned_long" in combined or "qqq100_aligned_long_confirmed" in combined)
    )


def saved_summary_value(rows: list[dict[str, str]], summary_name: str, default: str) -> str:
    for row in rows:
        if row.get("summary_name") == summary_name:
            value = str(row.get("summary_value", "")).strip()
            if value:
                return value
    return default


def saved_position_value(rows: list[dict[str, str]], ticker: str, field_name: str) -> str:
    for row in rows:
        if str(row.get("ticker", "")).upper() == ticker:
            value = str(row.get(field_name, "")).strip()
            if value:
                return value
    return ""


def quantity_from_position_summary(summary: str) -> str:
    text = summary.lower()
    for token in ["quantity=1", "quantity_abs=1", "long 1"]:
        if token in text:
            return "1"
    return ""


def first_nonempty(rows: list[dict[str, str]], keys: list[str]) -> str:
    for row in rows:
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
    return ""


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
