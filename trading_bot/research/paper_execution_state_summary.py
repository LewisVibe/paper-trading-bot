"""Saved-output-only paper execution milestone summary.

This report reads saved CSV artefacts only. It does not call Alpaca, refresh
market data, read live positions, submit/cancel/create orders, write SQLite,
send alerts, schedule anything, or approve follow-up execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INPUT_FILES = {
    "aapl_postcheck": Path("data/paper_order_smoke_test_postcheck.csv"),
    "aapl_gate": Path("data/paper_order_smoke_test_gate_report.csv"),
    "qqq100_execution_result": Path("data/qqq100_paper_execution_result.csv"),
    "qqq100_execution_summary": Path("data/qqq100_paper_execution_summary.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_readiness": Path("data/qqq100_paper_execution_readiness_report.csv"),
    "alpaca_connectivity": Path("data/alpaca_connectivity_diagnostics.csv"),
    "execution_eligibility": Path("data/execution_eligibility_report.csv"),
    "portfolio_preview": Path("data/multi_strategy_portfolio_preview.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
}

OUTPUT_FILES = {
    "summary": Path("data/paper_execution_state_summary.csv"),
    "positions": Path("data/paper_execution_state_positions.csv"),
    "milestones": Path("data/paper_execution_state_milestones.csv"),
    "blockers": Path("data/paper_execution_state_blockers.csv"),
}

SAFETY_COLUMNS = [
    "report_only",
    "execution_approved",
    "general_execution_approved",
    "qqq100_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "alpaca_called",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    "evidence_source",
    *SAFETY_COLUMNS,
]

POSITIONS_COLUMNS = [
    "created_at",
    "ticker",
    "position_context",
    "saved_position_summary",
    "alignment_state",
    "evidence_source",
    "details",
    *SAFETY_COLUMNS,
]

MILESTONE_COLUMNS = [
    "created_at",
    "milestone_name",
    "milestone_status",
    "strategy_name",
    "ticker",
    "historical_order_status",
    "saved_position_summary",
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

SAFETY_FLAGS = {
    "report_only": True,
    "execution_approved": False,
    "general_execution_approved": False,
    "qqq100_execution_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "scheduling_approved": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "alpaca_called": False,
}


@dataclass
class PaperExecutionStateSummaryResult:
    output_paths: dict[str, Path]
    summary_rows: list[dict[str, Any]]
    position_rows: list[dict[str, Any]]
    milestone_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_execution_state_summary(root_dir: Path | str = ".") -> PaperExecutionStateSummaryResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    context = build_context(inputs)
    summary_rows = build_summary_rows(created_at, context)
    position_rows = build_position_rows(created_at, context)
    milestone_rows = build_milestone_rows(created_at, context)
    blocker_rows = build_blocker_rows(created_at, context)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["positions"], POSITIONS_COLUMNS, position_rows)
    write_rows(output_paths["milestones"], MILESTONE_COLUMNS, milestone_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return PaperExecutionStateSummaryResult(
        output_paths=output_paths,
        summary_rows=summary_rows,
        position_rows=position_rows,
        milestone_rows=milestone_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["summary"]),
    )


def show_paper_execution_state_summary(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper execution state summary is missing.",
            "Run `python bot.py --paper-execution-state-summary` first.",
            "execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper execution state summary. Saved-output-only; no order or schedule approval.",
        f"final_state_summary_status: {summary_value(rows, 'final_state_summary_status')}",
        f"AAPL smoke-test result: {summary_value(rows, 'aapl_smoke_test_status')}",
        f"QQQ100 paper-execution result: {summary_value(rows, 'qqq100_manual_execution_status')}",
        f"current saved QQQ100 alignment: {summary_value(rows, 'qqq100_alignment_status')}",
        f"AAPL saved position summary: {summary_value(rows, 'aapl_position_summary')}",
        f"QQQ saved position summary: {summary_value(rows, 'qqq_position_summary')}",
        f"biggest_remaining_blocker: {summary_value(rows, 'biggest_remaining_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false",
        "execution_approved=false; general_execution_approved=false; qqq100_execution_approved=false",
        "followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    aapl_status = detect_aapl_smoke_status(inputs["aapl_postcheck"])
    aapl_position = detect_aapl_position(inputs["aapl_postcheck"])
    qqq_exec_status = detect_qqq_execution_status(inputs["qqq100_execution_result"], inputs["qqq100_execution_summary"])
    qqq_position = detect_qqq_position(inputs["qqq100_action_preview"])
    qqq_alignment = detect_qqq_alignment(inputs["qqq100_action_preview"])
    desired_position = first_nonempty(inputs["qqq100_signal"], ["desired_position"]) or "unknown"
    qqq_strategy = first_nonempty(inputs["qqq100_signal"], ["strategy_name"]) or first_nonempty(inputs["qqq100_execution_result"], ["strategy_name"]) or "qqq_100_trend_gate"

    if (
        aapl_status == "aapl_smoke_test_filled_confirmed"
        and qqq_exec_status == "qqq100_manual_paper_execution_filled_confirmed"
        and qqq_alignment == "qqq100_aligned_long_confirmed"
    ):
        final_status = "paper_execution_milestone_recorded"
    elif qqq_exec_status == "qqq100_manual_paper_execution_filled_confirmed" or aapl_status == "aapl_smoke_test_filled_confirmed":
        final_status = "paper_execution_partial_milestone_recorded"
    else:
        final_status = "paper_execution_state_saved_evidence_incomplete"

    return {
        "final_state_summary_status": final_status,
        "aapl_smoke_test_status": aapl_status,
        "aapl_position_summary": aapl_position,
        "qqq100_manual_execution_status": qqq_exec_status,
        "qqq100_alignment_status": qqq_alignment,
        "qqq_position_summary": qqq_position,
        "qqq100_strategy_state": f"{qqq_strategy}:{desired_position}",
        "desired_position": desired_position,
        "no_followup_order_status": "no_followup_order_approved",
        "repeat_execution_status": "repeat_execution_not_approved",
        "scheduling_status": "scheduling_not_approved",
        "general_execution_status": "general_execution_still_blocked",
        "biggest_remaining_blocker": "future_manual_review_required",
        "recommended_next_step": "design_repeat_or_alignment_workflow_only_after_separate_manual_review",
    }


def detect_aapl_smoke_status(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "aapl_smoke_test_saved_postcheck_missing"
    joined = " ".join(" ".join(str(value) for value in row.values()) for row in rows).lower()
    if "postcheck_order_observed_filled_manual_review" in joined and "recent_order_match_found" in joined:
        return "aapl_smoke_test_filled_confirmed"
    if "postcheck_order_observed_filled_manual_review" in joined:
        return "aapl_smoke_test_filled_confirmed"
    if "filled" in joined and "aapl" in joined:
        return "aapl_smoke_test_filled_confirmed"
    return "aapl_smoke_test_not_confirmed_from_saved_postcheck"


def detect_aapl_position(rows: list[dict[str, str]]) -> str:
    for row in reversed(rows):
        summary = str(row.get("position_summary", "")).strip()
        if summary:
            return summary
    joined = " ".join(" ".join(str(value) for value in row.values()) for row in rows).lower()
    if "long 2" in joined or "quantity_abs=2" in joined:
        return "long 2"
    return "unavailable"


def detect_qqq_execution_status(result_rows: list[dict[str, str]], summary_rows: list[dict[str, str]]) -> str:
    rows = result_rows + summary_rows
    if not rows:
        return "qqq100_manual_execution_saved_result_missing"
    joined = " ".join(" ".join(str(value) for value in row.values()) for row in rows).lower()
    if "qqq_100_trend_gate" in joined and "qqq" in joined and "filled" in joined:
        return "qqq100_manual_paper_execution_filled_confirmed"
    if "order_submitted" in joined:
        return "qqq100_manual_paper_execution_submitted_not_confirmed_filled"
    return "qqq100_manual_execution_not_confirmed_from_saved_result"


def detect_qqq_position(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "unavailable"
    row = rows[0]
    status = str(row.get("current_position_status", "")).strip()
    qty = str(row.get("current_position_quantity_if_readonly", "")).strip()
    if status and qty:
        return f"{status}; quantity={qty}"
    return status or "unavailable"


def detect_qqq_alignment(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "qqq100_alignment_saved_preview_missing"
    row = rows[0]
    status = str(row.get("current_position_status", "")).strip()
    alignment = str(row.get("alignment_state", "")).strip()
    action = str(row.get("non_executable_preview_action", "")).strip()
    if status == "paper_position_long" and alignment == "aligned_long":
        return "qqq100_aligned_long_confirmed"
    if action == "no_action_preview_only":
        return "qqq100_no_action_preview_only"
    if alignment:
        return alignment
    return "qqq100_alignment_unavailable"


def build_summary_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("final_state_summary_status", context["final_state_summary_status"], "Saved-output-only paper trading milestone state."),
        ("aapl_smoke_test_status", context["aapl_smoke_test_status"], "AAPL smoke-test status from saved postcheck."),
        ("aapl_position_summary", context["aapl_position_summary"], "AAPL saved/observed position summary from saved postcheck, if available."),
        ("qqq100_manual_execution_status", context["qqq100_manual_execution_status"], "QQQ100 historical manual paper execution status from saved result."),
        ("qqq100_alignment_status", context["qqq100_alignment_status"], "QQQ100 current saved action-preview alignment."),
        ("qqq_position_summary", context["qqq_position_summary"], "QQQ saved/observed action-preview position summary, if available."),
        ("qqq100_strategy_state", context["qqq100_strategy_state"], "Saved QQQ100 strategy/desired position state."),
        ("no_followup_order_status", context["no_followup_order_status"], "No follow-up order is approved by this summary."),
        ("repeat_execution_status", context["repeat_execution_status"], "Repeat execution requires separate design/review."),
        ("scheduling_status", context["scheduling_status"], "Scheduling remains unapproved."),
        ("general_execution_status", context["general_execution_status"], "General execution approval remains false."),
        ("biggest_remaining_blocker", context["biggest_remaining_blocker"], "Largest remaining blocker before any repeat/alignment workflow."),
        ("recommended_next_step", context["recommended_next_step"], "Next safe step after recording the milestone."),
    ]
    return [
        {
            "created_at": created_at,
            "summary_name": name,
            "summary_value": value,
            "details": details,
            "evidence_source": "saved_csv_outputs",
            **SAFETY_FLAGS,
        }
        for name, value, details in rows
    ]


def build_position_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "ticker": "AAPL",
            "position_context": "manual_smoke_test_saved_postcheck",
            "saved_position_summary": context["aapl_position_summary"],
            "alignment_state": "not_applicable",
            "evidence_source": "data/paper_order_smoke_test_postcheck.csv",
            "details": "Saved AAPL postcheck position context only; no live position read.",
            **SAFETY_FLAGS,
        },
        {
            "created_at": created_at,
            "ticker": "QQQ",
            "position_context": "qqq100_saved_action_preview",
            "saved_position_summary": context["qqq_position_summary"],
            "alignment_state": context["qqq100_alignment_status"],
            "evidence_source": "data/qqq100_action_preview.csv",
            "details": "Saved QQQ action-preview position context only; no live position read.",
            **SAFETY_FLAGS,
        },
    ]


def build_milestone_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        milestone_row(created_at, "aapl_smoke_test", context["aapl_smoke_test_status"], "manual_smoke_test", "AAPL", "filled" if context["aapl_smoke_test_status"] == "aapl_smoke_test_filled_confirmed" else "unconfirmed", context["aapl_position_summary"], "data/paper_order_smoke_test_postcheck.csv", "Historical AAPL smoke-test milestone only; this report did not submit the order."),
        milestone_row(created_at, "qqq100_manual_paper_execution", context["qqq100_manual_execution_status"], "qqq_100_trend_gate", "QQQ", "filled" if context["qqq100_manual_execution_status"] == "qqq100_manual_paper_execution_filled_confirmed" else "unconfirmed", context["qqq_position_summary"], "data/qqq100_paper_execution_result.csv", "Historical QQQ100 manual paper execution milestone only; this report did not submit the order."),
        milestone_row(created_at, "qqq100_alignment", context["qqq100_alignment_status"], "qqq_100_trend_gate", "QQQ", "not_applicable", context["qqq_position_summary"], "data/qqq100_action_preview.csv", "Saved action preview indicates current QQQ100 alignment where available."),
        milestone_row(created_at, "followup_boundary", "no_followup_order_approved", "boundary", "", "none", "not_applicable", "static_safety_boundary", "No follow-up order is approved by this saved summary."),
    ]


def milestone_row(
    created_at: str,
    name: str,
    status: str,
    strategy: str,
    ticker: str,
    historical_order_status: str,
    position: str,
    source: str,
    details: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "milestone_name": name,
        "milestone_status": status,
        "strategy_name": strategy,
        "ticker": ticker,
        "historical_order_status": historical_order_status,
        "saved_position_summary": position,
        "evidence_source": source,
        "details": details,
        **SAFETY_FLAGS,
    }


def build_blocker_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    blockers = [
        ("no_followup_order_approved", "blocked", "critical", "This report records historical milestones only and approves no follow-up order.", "Do not place follow-up orders from this summary."),
        ("repeat_execution_not_approved", "blocked", "critical", "Future repeat QQQ100 alignment is not approved by this report.", "Design a separate repeat/alignment workflow with manual review before any repeat use."),
        ("scheduling_not_approved", "blocked", "critical", "No scheduling, loop, cron, Task Scheduler, service, or Hermes job is approved.", "Keep execution commands manual-only unless a separate scheduling review explicitly changes that."),
        ("general_execution_still_blocked", "blocked", "critical", "General strategy execution remains blocked; this report is not strategy-to-execution approval.", "Keep normal bot, high-growth, crypto, slow-SMA, and smoke-test paths separate."),
        ("future_manual_review_required", "blocked", "critical", f"Final state is {context['final_state_summary_status']}; repeat workflow design still needs review.", context["recommended_next_step"]),
    ]
    return [
        {
            "created_at": created_at,
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for name, status, severity, details, next_step in blockers
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    return [
        "Paper execution state summary generated from saved CSV outputs only.",
        f"final_state_summary_status: {summary_value(summary_rows, 'final_state_summary_status')}",
        f"AAPL smoke-test result: {summary_value(summary_rows, 'aapl_smoke_test_status')}",
        f"QQQ100 paper-execution result: {summary_value(summary_rows, 'qqq100_manual_execution_status')}",
        f"current saved QQQ100 alignment: {summary_value(summary_rows, 'qqq100_alignment_status')}",
        f"AAPL saved position summary: {summary_value(summary_rows, 'aapl_position_summary')}",
        f"QQQ saved position summary: {summary_value(summary_rows, 'qqq_position_summary')}",
        f"biggest_remaining_blocker: {summary_value(summary_rows, 'biggest_remaining_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false",
        "execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def first_nonempty(rows: list[dict[str, str]], keys: list[str]) -> str:
    for row in rows:
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
    return ""


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return "missing"


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
