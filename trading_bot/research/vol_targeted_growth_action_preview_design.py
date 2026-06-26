"""Saved-output action-preview design for volatility-targeted growth 15/20.

This is a design checkpoint only. It reviews the saved preview signal and
documents how a future action preview should behave, without reading broker
positions, creating action rows, creating order instructions, refreshing market
data, scheduling anything, or approving execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_action_preview_design_ready_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_action_preview_design_blocked_missing_preview_signal"
NEXT_STEP = "manual_review_action_preview_design_before_any_saved_action_preview_implementation"

OUTPUT_FILES = {
    "design": Path("data/vol_targeted_growth_action_preview_design.csv"),
    "summary": Path("data/vol_targeted_growth_action_preview_design_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_action_preview_design_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_action_preview_design_blockers.csv"),
}

INPUT_FILES = {
    "preview_signal": Path("data/vol_targeted_growth_preview_signal.csv"),
    "preview_signal_summary": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
    "preview_signal_blockers": Path("data/vol_targeted_growth_preview_signal_blockers.csv"),
    "preview_design_summary": Path("data/vol_targeted_growth_preview_design_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "preview_only": True,
    "action_preview_design_only": True,
    "action_preview_created": False,
    "order_instructions_created": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "broker_positions_compared": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "preview_candidate_approved": False,
    "preview_implementation_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "high_growth_promotion_approved": False,
    "crypto_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

DESIGN_COLUMNS = [
    "created_at",
    "design_item",
    "status",
    "risk_level",
    "selected_candidate",
    "design_value",
    "rationale",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthActionPreviewDesignResult:
    output_paths: dict[str, Path]
    design_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_action_preview_design(root_dir: Path | str = ".") -> VolTargetedGrowthActionPreviewDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    signal_status = summary_value(inputs["preview_signal_summary"], "final_signal_status")
    signal_candidate = summary_value(inputs["preview_signal_summary"], "selected_candidate")
    final_status = FINAL_STATUS if signal_status and signal_candidate == SELECTED_CANDIDATE else BLOCKED_STATUS

    design_rows = build_design_rows(created_at, final_status, signal_status)
    summary_rows = build_summary_rows(final_status, signal_status, inputs)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status, signal_status, signal_candidate)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["design"], DESIGN_COLUMNS, design_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthActionPreviewDesignResult(
        output_paths=output_paths,
        design_rows=design_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_action_preview_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted growth action-preview design is missing.",
            "Run `python bot.py --vol-targeted-growth-action-preview-design` first.",
            "action_preview_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted growth action-preview design saved display. Design/report only; no action preview or execution approval.",
        f"final_design_status: {summary_value(summary_rows, 'final_design_status')}",
        f"selected_candidate: {summary_value(summary_rows, 'selected_candidate')}",
        f"source_preview_signal_status: {summary_value(summary_rows, 'source_preview_signal_status')}",
        f"future_action_preview_scope: {summary_value(summary_rows, 'future_action_preview_scope')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "action_preview_created=false; order_instructions_created=false; broker_positions_compared=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this is an action-preview design checkpoint only; it does not create actions, orders, broker reads, or scheduling approval.",
    ]


def build_design_rows(created_at: str, final_status: str, signal_status: str) -> list[dict[str, Any]]:
    source_status = signal_status or "missing_saved_preview_signal_status"
    return [
        design_row(
            created_at,
            "source_signal_review",
            final_status,
            "medium",
            f"Use only the saved volatility-targeted growth preview signal as input; source_signal_status={source_status}.",
            "The action-preview design is allowed only after a saved preview signal exists and remains non-executable.",
            NEXT_STEP,
        ),
        design_row(
            created_at,
            "future_position_context",
            "design_recorded",
            "high",
            "Default future action preview must not read broker positions; any broker-position comparison would require a separate explicit read-only confirmation design.",
            "Unknown or unavailable position state must be loud and must not silently become flat, aligned, or eligible.",
            "design_saved_position_input_schema_before_any_action_preview",
        ),
        design_row(
            created_at,
            "future_action_language",
            "design_recorded",
            "high",
            "Future action preview may use manual-review labels only, not order instructions.",
            "Labels should help review exposure without implying an executable order.",
            "keep_future_labels_non_executable",
        ),
        design_row(
            created_at,
            "forbidden_future_fields",
            "design_recorded",
            "critical",
            "Future action preview output must not include order side, order quantity, order type, time-in-force, account ID, order ID, API key, webhook, or secret fields.",
            "The volatility-targeted sleeve weights are portfolio research targets, not order tickets.",
            "verify_future_action_preview_schema_before_implementation",
        ),
        design_row(
            created_at,
            "execution_boundary",
            "execution_blocked",
            "critical",
            "No execution, paper execution, live trading, repeat order, follow-up order, broker read, or scheduling is approved.",
            "This command is the design checkpoint only.",
            "manual_review_before_any_separate_action_preview_implementation",
        ),
    ]


def build_summary_rows(
    final_status: str,
    signal_status: str,
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = [
        ("final_design_status", final_status, "Whether the saved preview signal supports an action-preview design checkpoint."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("source_preview_signal_status", signal_status or "missing_saved_preview_signal_status", "Saved preview signal status."),
        ("source_target_weights", summary_value(inputs["preview_signal_summary"], "target_sleeve_weights") or "missing_saved_target_weights", "Saved target weights from the preview signal."),
        ("future_action_preview_scope", "saved-state comparison design only; manual-review labels only; no order side/quantity/type/account fields; no broker positions by default", "Future action-preview scope if implemented later."),
        ("largest_blocker", "actual_action_preview_not_implemented_and_broker_position_read_not_approved", "This checkpoint does not create action rows or read positions."),
        ("recommended_next_step", NEXT_STEP, "Manual review is required before any separate saved action-preview implementation."),
        ("execution_status", "execution_blocked", "Paper/live execution remains blocked."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = []
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    rows.append(("preview_signal_review_answer", "yes_design_checkpoint_is_reasonable", "The saved preview signal exists and remains non-executable when status evidence is present."))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(final_status: str, signal_status: str, signal_candidate: str) -> list[dict[str, Any]]:
    blockers = [
        ("actual_action_preview_not_implemented", "blocked", "critical", "This command designs a future action preview but does not create one.", NEXT_STEP),
        ("broker_position_read_not_approved", "blocked", "critical", "No broker positions are read or compared by this checkpoint.", "Separate explicit read-only design would be required before broker comparison."),
        ("order_instructions_not_allowed", "blocked", "critical", "Future action-preview output must not include executable order side/quantity/type/account fields.", "Keep future output manual-review only."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "Keep all approval flags false."),
    ]
    if final_status == BLOCKED_STATUS:
        blockers.insert(
            0,
            (
                "missing_preview_signal_evidence",
                "blocked",
                "high",
                f"signal_status={signal_status}; signal_candidate={signal_candidate}",
                "Run and review the saved preview signal first.",
            ),
        )
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth action-preview design complete. Design/report only; no action preview, broker reads, orders, or scheduling approved.",
        f"final_design_status={summary_value(summary_rows, 'final_design_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"source_preview_signal_status={summary_value(summary_rows, 'source_preview_signal_status')}",
        f"future_action_preview_scope={summary_value(summary_rows, 'future_action_preview_scope')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_design={output_paths['design']}",
        "action_preview_created=false; order_instructions_created=false; broker_positions_compared=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def design_row(
    created_at: str,
    design_item: str,
    status: str,
    risk_level: str,
    design_value: str,
    rationale: str,
    required_next_step: str,
    selected_candidate: str = SELECTED_CANDIDATE,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "design_item": design_item,
        "status": status,
        "risk_level": risk_level,
        "selected_candidate": selected_candidate,
        "design_value": design_value,
        "rationale": rationale,
        "required_next_step": required_next_step,
        **SAFETY_FLAGS,
    }


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
