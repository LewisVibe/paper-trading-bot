"""Saved-output broker-position comparison design for volatility-targeted growth.

This checkpoint designs a possible future read-only broker-position comparison
for the saved volatility-targeted growth action preview. It does not read broker
positions, call Alpaca, create order instructions, schedule anything, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_broker_position_comparison_design_ready_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_broker_position_comparison_design_blocked_missing_action_preview"
NEXT_STEP = "manual_review_broker_position_comparison_design_before_any_readonly_broker_check"

OUTPUT_FILES = {
    "design": Path("data/vol_targeted_growth_broker_position_comparison_design.csv"),
    "summary": Path("data/vol_targeted_growth_broker_position_comparison_design_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_broker_position_comparison_design_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_broker_position_comparison_design_blockers.csv"),
}

INPUT_FILES = {
    "action_preview": Path("data/vol_targeted_growth_action_preview.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "action_preview_blockers": Path("data/vol_targeted_growth_action_preview_blockers.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "preview_only": True,
    "design_only": True,
    "broker_position_comparison_design_only": True,
    "broker_positions_compared": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

DESIGN_COLUMNS = ["created_at", "design_item", "status", "risk_level", "design_value", "rationale", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthBrokerPositionComparisonDesignResult:
    output_paths: dict[str, Path]
    design_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_broker_position_comparison_design(root_dir: Path | str = ".") -> VolTargetedGrowthBrokerPositionComparisonDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    action_status = summary_value(inputs["action_preview_summary"], "final_action_preview_status")
    final_status = FINAL_STATUS if action_status else BLOCKED_STATUS
    design_rows = build_design_rows(created_at, final_status, action_status)
    summary_rows = build_summary_rows(final_status, action_status, inputs)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status, action_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["design"], DESIGN_COLUMNS, design_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthBrokerPositionComparisonDesignResult(
        output_paths=output_paths,
        design_rows=design_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_broker_position_comparison_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-broker-position-comparison-design` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted growth broker-position comparison design saved display. Design only; no broker read or execution approval.",
        f"final_design_status: {summary_value(rows, 'final_design_status')}",
        f"source_action_preview_status: {summary_value(rows, 'source_action_preview_status')}",
        f"future_comparison_scope: {summary_value(rows, 'future_comparison_scope')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "broker_positions_compared=false; alpaca_called=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_design_rows(created_at: str, final_status: str, action_status: str) -> list[dict[str, Any]]:
    return [
        design_row(created_at, "source_action_preview", final_status, "medium", f"source_action_preview_status={action_status or 'missing'}", "Future comparison may only start from the saved action preview.", NEXT_STEP),
        design_row(created_at, "future_broker_read_gate", "design_recorded", "critical", "Require explicit read-only confirmation before any future Alpaca paper position read.", "No broker reads are performed by this checkpoint.", "separate_prompt_required_for_readonly_position_comparison"),
        design_row(created_at, "unknown_position_policy", "design_recorded", "critical", "Unknown, unavailable, or ambiguous broker position state must block/manual-review loudly.", "Unknown state must never become flat, aligned, or eligible silently.", "verify_unknown_position_policy_before_implementation"),
        design_row(created_at, "forbidden_output_fields", "design_recorded", "critical", "No order side, quantity, order type, account ID, order ID, API key, webhook, token, or secret fields.", "Comparison output must remain review context, not an order ticket.", "verify_schema_before_any_comparison_command"),
        design_row(created_at, "execution_boundary", "execution_blocked", "critical", "No execution, paper execution, live trading, repeat/follow-up order, or scheduling is approved.", "Broker-position comparison would be read-only context only.", "keep_all_approval_flags_false"),
    ]


def build_summary_rows(final_status: str, action_status: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("final_design_status", final_status, "Whether saved action-preview evidence supports a future broker-position comparison design."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("source_action_preview_status", action_status or "missing_saved_action_preview_status", "Saved action-preview status."),
        ("action_preview_rows", str(len(inputs["action_preview"])), "Saved action-preview row count."),
        ("future_comparison_scope", "explicit-readonly-paper-position-comparison-design-only; no orders; unknown positions block/manual-review", "Future scope if separately implemented."),
        ("largest_blocker", "broker_read_not_approved_and_no_position_comparison_implemented", "This checkpoint performs no broker read."),
        ("recommended_next_step", NEXT_STEP, "Manual review required before any read-only broker comparison command."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(final_status: str, action_status: str) -> list[dict[str, Any]]:
    rows = [
        ("broker_read_not_approved", "blocked", "critical", "No broker read or position comparison is approved by this design.", NEXT_STEP),
        ("order_instructions_not_allowed", "blocked", "critical", "Comparison output must not include executable order fields.", "Keep future comparison manual-review-only."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "Keep all approval flags false."),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("missing_action_preview", "blocked", "high", f"action_status={action_status}", "Run saved action preview first."))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth broker-position comparison design complete. Design only; no broker reads, orders, or scheduling approved.",
        f"final_design_status={summary_value(rows, 'final_design_status')}",
        f"source_action_preview_status={summary_value(rows, 'source_action_preview_status')}",
        f"future_comparison_scope={summary_value(rows, 'future_comparison_scope')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_design={output_paths['design']}",
        "broker_positions_compared=false; alpaca_called=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def design_row(created_at: str, item: str, status: str, risk: str, value: str, rationale: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "design_item": item, "status": status, "risk_level": risk, "design_value": value, "rationale": rationale, "required_next_step": next_step, **SAFETY_FLAGS}


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
