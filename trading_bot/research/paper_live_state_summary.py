"""Saved-output paper-live state summary for the QQQ100 paper-live path.

This summary reads saved CSV artefacts only. It does not call Alpaca, read live
positions, refresh market data, create order instructions, submit/cancel/replace
orders, write SQLite, send alerts, schedule anything, or upgrade readiness.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

INPUT_FILES = {
    "paper_live_promotion_gate_summary": Path("data/paper_live_promotion_gate_summary.csv"),
    "paper_live_readiness_summary": Path("data/paper_live_readiness_summary.csv"),
    "paper_live_readiness_blockers": Path("data/paper_live_readiness_blockers.csv"),
    "qqq100_preview_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_action_preview_summary": Path("data/qqq100_action_preview_summary.csv"),
    "qqq100_paper_execution_result": Path("data/qqq100_paper_execution_result.csv"),
    "qqq100_paper_execution_summary": Path("data/qqq100_paper_execution_summary.csv"),
    "qqq100_paper_postcheck": Path("data/qqq100_paper_postcheck.csv"),
    "qqq100_paper_postcheck_summary": Path("data/qqq100_paper_postcheck_summary.csv"),
    "paper_execution_state_summary": Path("data/paper_execution_state_summary.csv"),
    "paper_execution_state_positions": Path("data/paper_execution_state_positions.csv"),
    "paper_execution_state_milestones": Path("data/paper_execution_state_milestones.csv"),
}

OUTPUT_FILES = {
    "summary": Path("data/paper_live_state_summary.csv"),
    "components": Path("data/paper_live_state_components.csv"),
    "blockers": Path("data/paper_live_state_blockers.csv"),
    "evidence": Path("data/paper_live_state_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "preview_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    **SAFETY_FLAGS,
}

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_FLAGS.keys(),
]

COMPONENT_COLUMNS = [
    "component_name",
    "component_status",
    "component_value",
    "evidence_source",
    "details",
    "research_only",
    "report_only",
    "preview_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "order_instructions_created",
    "alpaca_called",
    "positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
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
    "evidence_status",
    "evidence_source",
    "details",
    *SAFETY_FLAGS.keys(),
]


@dataclass
class PaperLiveStateSummaryResult:
    output_paths: dict[str, Path]
    summary_rows: list[dict[str, Any]]
    component_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_state_summary(root_dir: Path | str = ".") -> PaperLiveStateSummaryResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    context = build_context(inputs)
    summary_rows = build_summary_rows(context)
    component_rows = build_component_rows(context)
    blocker_rows = build_blocker_rows(context)
    evidence_rows = build_evidence_rows(inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["components"], COMPONENT_COLUMNS, component_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveStateSummaryResult(
        output_paths=output_paths,
        summary_rows=summary_rows,
        component_rows=component_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_state_summary(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live state summary is missing.",
            "Run `python bot.py --paper-live-state-summary` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live state summary saved display. Report only; no execution approved.",
        f"active_strategy: {summary_value(rows, 'active_paper_live_candidate_strategy')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"desired_state: {summary_value(rows, 'desired_state')}",
        f"saved_current_position_state: {summary_value(rows, 'saved_current_position_state')}",
        f"last_saved_qqq100_order_result: {summary_value(rows, 'last_saved_qqq100_order_result')}",
        f"current_alignment_state: {summary_value(rows, 'current_alignment_state')}",
        f"promotion_gate_status: {summary_value(rows, 'promotion_gate_status')}",
        f"readiness_status: {summary_value(rows, 'readiness_status')}",
        f"manual_qqq100_paper_action_discussion_allowed: {summary_value(rows, 'manual_qqq100_paper_action_discussion_allowed')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        "Warning: state summary is not a readiness upgrade or order approval.",
    ]


def build_context(inputs: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    missing = [name for name, rows in inputs.items() if not rows]
    desired_state = detect_desired_state(inputs)
    saved_position = detect_saved_position(inputs)
    order_result = detect_order_result(inputs)
    alignment_state = detect_alignment_state(inputs)
    promotion_status = summary_value(inputs["paper_live_promotion_gate_summary"], "final_promotion_gate_status")
    readiness_status = summary_value(inputs["paper_live_readiness_summary"], "final_readiness_status")
    missing_blockers = detect_missing_saved_evidence_blockers(inputs)
    manual_discussion_allowed = readiness_status == "paper_live_ready_for_manual_qqq100_paper_action_discussion"
    largest_blocker = (
        "readiness_not_ready_for_manual_discussion"
        if not manual_discussion_allowed
        else "explicit_human_approval_still_required"
    )
    if missing_blockers != "none":
        largest_blocker = "missing_saved_evidence"
    return {
        "active_strategy": STRATEGY_NAME,
        "active_ticker": TICKER,
        "desired_state": desired_state,
        "saved_current_position_state": saved_position,
        "last_saved_qqq100_order_result": order_result,
        "current_alignment_state": alignment_state,
        "promotion_gate_status": promotion_status or "unavailable",
        "readiness_status": readiness_status or "unavailable",
        "missing_saved_evidence_blockers": missing_blockers,
        "manual_qqq100_paper_action_discussion_allowed": str(manual_discussion_allowed),
        "followup_or_repeat_paper_order_allowed": "False",
        "scheduling_allowed": "False",
        "live_trading_allowed": "False",
        "largest_blocker": largest_blocker,
        "recommended_next_step": "review_saved_state_and_readiness_before_any_separate_manual_qqq100_paper_prompt",
        "missing_inputs": "; ".join(missing) if missing else "none",
    }


def detect_desired_state(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        first_nonempty(inputs["qqq100_preview_signal"], ["desired_position"])
        or summary_value(inputs["qqq100_action_preview_summary"], "desired_position")
        or first_nonempty(inputs["qqq100_action_preview"], ["desired_position"])
        or "unavailable"
    )


def detect_saved_position(inputs: dict[str, list[dict[str, Any]]]) -> str:
    from_postcheck = first_nonempty(inputs["qqq100_paper_postcheck"], ["position_status", "current_position_status"])
    postcheck_qty = first_nonempty(inputs["qqq100_paper_postcheck"], ["position_quantity_abs", "current_position_quantity_abs"])
    if from_postcheck and postcheck_qty:
        return f"{from_postcheck}; quantity={postcheck_qty}"
    if from_postcheck:
        return from_postcheck
    for row in inputs["paper_execution_state_positions"]:
        if str(row.get("ticker", "")).upper() == TICKER:
            return str(row.get("saved_position_summary") or row.get("position_context") or "unavailable")
    return first_nonempty(inputs["qqq100_action_preview"], ["current_position_status"]) or "unavailable"


def detect_order_result(inputs: dict[str, list[dict[str, Any]]]) -> str:
    status = first_nonempty(inputs["qqq100_paper_execution_result"], ["order_status", "decision_status"])
    if status:
        return status
    milestone = first_nonempty(inputs["paper_execution_state_milestones"], ["historical_order_status", "milestone_status"])
    if milestone:
        return milestone
    return "unavailable"


def detect_alignment_state(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        first_nonempty(inputs["qqq100_paper_postcheck"], ["alignment_state"])
        or first_nonempty(inputs["paper_execution_state_positions"], ["alignment_state"])
        or first_nonempty(inputs["qqq100_action_preview"], ["alignment_state", "non_executable_preview_action"])
        or summary_value(inputs["paper_execution_state_summary"], "qqq100_alignment_status")
        or "unavailable"
    )


def detect_missing_saved_evidence_blockers(inputs: dict[str, list[dict[str, Any]]]) -> str:
    explicit = []
    for row in inputs["paper_live_readiness_blockers"]:
        name = str(row.get("blocker_name", ""))
        if "missing" in name:
            explicit.append(name)
    if explicit:
        return "; ".join(explicit)
    missing = [
        name
        for name in [
            "qqq100_preview_signal",
            "qqq100_action_preview",
            "qqq100_paper_postcheck",
            "qqq100_paper_execution_result",
            "paper_live_promotion_gate_summary",
            "paper_live_readiness_summary",
        ]
        if not inputs[name]
    ]
    return "; ".join(missing) if missing else "none"


def build_summary_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("active_paper_live_candidate_strategy", context["active_strategy"], "First paper-live candidate strategy only."),
        ("active_ticker", context["active_ticker"], "First paper-live candidate ticker only."),
        ("desired_state", context["desired_state"], "Saved desired state from QQQ100 preview/action evidence if available."),
        ("saved_current_position_state", context["saved_current_position_state"], "Saved position state only; no live position read."),
        ("last_saved_qqq100_order_result", context["last_saved_qqq100_order_result"], "Saved QQQ100 paper order result if available."),
        ("current_alignment_state", context["current_alignment_state"], "Current saved alignment state if available."),
        ("promotion_gate_status", context["promotion_gate_status"], "Saved paper-live promotion gate status."),
        ("readiness_status", context["readiness_status"], "Saved paper-live readiness status."),
        ("missing_saved_evidence_blockers", context["missing_saved_evidence_blockers"], "Missing saved evidence blockers or unavailable inputs."),
        ("manual_qqq100_paper_action_discussion_allowed", context["manual_qqq100_paper_action_discussion_allowed"], "Manual discussion status only; not order approval."),
        ("followup_or_repeat_paper_order_allowed", context["followup_or_repeat_paper_order_allowed"], "Follow-up/repeat paper orders are not approved."),
        ("scheduling_allowed", context["scheduling_allowed"], "Scheduling is not approved."),
        ("live_trading_allowed", context["live_trading_allowed"], "Live trading is not approved."),
        ("largest_blocker", context["largest_blocker"], "Largest blocker in the saved state summary."),
        ("recommended_next_step", context["recommended_next_step"], "Next step remains manual review, not execution."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_component_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("candidate_strategy", "present", context["active_strategy"], "static QQQ100 boundary", "Only QQQ100 is summarized."),
        ("candidate_ticker", "present", context["active_ticker"], "static QQQ boundary", "Only QQQ is summarized."),
        ("desired_state", status_for_value(context["desired_state"]), context["desired_state"], "data/qqq100_preview_signal_pack.csv or action preview", "Saved desired state only."),
        ("saved_position_state", status_for_value(context["saved_current_position_state"]), context["saved_current_position_state"], "saved postcheck/state files", "No live position read."),
        ("last_order_result", status_for_value(context["last_saved_qqq100_order_result"]), context["last_saved_qqq100_order_result"], "saved QQQ100 execution/state files", "Historical saved result only."),
        ("alignment_state", status_for_value(context["current_alignment_state"]), context["current_alignment_state"], "saved postcheck/action/state files", "Saved alignment only."),
        ("promotion_gate_status", status_for_value(context["promotion_gate_status"]), context["promotion_gate_status"], "data/paper_live_promotion_gate_summary.csv", "Promotion gate status only."),
        ("readiness_status", status_for_value(context["readiness_status"]), context["readiness_status"], "data/paper_live_readiness_summary.csv", "Readiness status only."),
        ("manual_discussion_allowed", "blocked" if context["manual_qqq100_paper_action_discussion_allowed"] != "True" else "manual_review_only", context["manual_qqq100_paper_action_discussion_allowed"], "paper-live readiness summary", "Never order approval."),
    ]
    return [
        {
            "component_name": name,
            "component_status": status,
            "component_value": value,
            "evidence_source": source,
            "details": details,
            **ROW_SAFETY,
        }
        for name, status, value, source, details in rows
    ]


def build_blocker_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("execution_not_approved", "blocked", "critical", "This state summary does not approve execution.", "Use a separate explicit manual prompt before any future paper action."),
        ("paper_execution_not_approved", "blocked", "critical", "Paper execution remains unapproved by this summary.", "Do not run QQQ100 paper execution from this summary."),
        ("followup_order_not_approved", "blocked", "critical", "Follow-up or repeat paper orders remain unapproved.", "Do not place follow-up orders without separate review."),
        ("scheduling_not_approved", "blocked", "critical", "Scheduling remains unapproved.", "Do not schedule order-capable commands."),
        ("live_trading_not_approved", "blocked", "critical", "Live trading remains unapproved.", "Keep Alpaca paper-only."),
    ]
    if context["missing_saved_evidence_blockers"] != "none":
        rows.append(
            (
                "missing_saved_evidence",
                "blocked",
                "high",
                context["missing_saved_evidence_blockers"],
                "Regenerate or review safe saved reports before any manual QQQ100 paper action discussion.",
            )
        )
    if context["manual_qqq100_paper_action_discussion_allowed"] != "True":
        rows.append(
            (
                "manual_qqq100_paper_action_discussion_not_allowed",
                "blocked",
                "high",
                context["readiness_status"],
                "Resolve readiness blockers before any future manual QQQ100 paper action discussion.",
            )
        )
    return [
        {
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for name, status, severity, details, next_step in rows
    ]


def build_evidence_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {
            "evidence_name": name,
            "evidence_status": "present" if rows else "missing",
            "evidence_source": str(INPUT_FILES[name]),
            "details": "Saved CSV evidence presence check.",
            **SAFETY_FLAGS,
        }
        for name, rows in inputs.items()
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live state summary complete. Saved-output report only; no execution approved.",
        f"Active strategy: {summary_value(summary_rows, 'active_paper_live_candidate_strategy')}",
        f"Active ticker: {summary_value(summary_rows, 'active_ticker')}",
        f"Desired state: {summary_value(summary_rows, 'desired_state')}",
        f"Saved current position state: {summary_value(summary_rows, 'saved_current_position_state')}",
        f"Last saved QQQ100 order result: {summary_value(summary_rows, 'last_saved_qqq100_order_result')}",
        f"Current alignment state: {summary_value(summary_rows, 'current_alignment_state')}",
        f"Promotion gate status: {summary_value(summary_rows, 'promotion_gate_status')}",
        f"Readiness status: {summary_value(summary_rows, 'readiness_status')}",
        f"Manual QQQ100 paper action discussion allowed: {summary_value(summary_rows, 'manual_qqq100_paper_action_discussion_allowed')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Saved summary/components/blockers/evidence to {output_paths['summary']}; {output_paths['components']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false",
        "Warning: state summary is not a readiness upgrade or order approval.",
    ]


def status_for_value(value: str) -> str:
    return "unavailable" if value in {"", "unavailable"} else "present"


def first_nonempty(rows: list[dict[str, Any]], keys: list[str]) -> str:
    for row in rows:
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
    return ""


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", ""))
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
