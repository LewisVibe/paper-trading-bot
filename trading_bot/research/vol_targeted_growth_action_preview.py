"""Saved-output action preview for volatility-targeted growth 15/20.

This preview reads the saved volatility-targeted preview signal only. It does
not read broker positions, refresh market data, create order instructions,
write SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_action_preview_created_saved_output_only"
BLOCKED_STATUS = "vol_targeted_growth_action_preview_blocked_missing_preview_signal"
NEXT_STEP = "manual_review_saved_action_preview_before_any_broker_position_comparison_design"

OUTPUT_FILES = {
    "preview": Path("data/vol_targeted_growth_action_preview.csv"),
    "summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_action_preview_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_action_preview_blockers.csv"),
}

INPUT_FILES = {
    "preview_signal": Path("data/vol_targeted_growth_preview_signal.csv"),
    "preview_signal_summary": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
    "action_preview_design_summary": Path("data/vol_targeted_growth_action_preview_design_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "preview_only": True,
    "action_preview_only": True,
    "action_preview_created": True,
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

PREVIEW_COLUMNS = [
    "created_at",
    "selected_candidate",
    "sleeve_name",
    "target_weight",
    "sleeve_status",
    "source_signal_status",
    "current_exposure_status",
    "current_exposure_source",
    "alignment_state",
    "manual_review_label",
    "blocker",
    "next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthActionPreviewResult:
    output_paths: dict[str, Path]
    preview_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_action_preview(root_dir: Path | str = ".") -> VolTargetedGrowthActionPreviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    signal_status = summary_value(inputs["preview_signal_summary"], "final_signal_status")
    signal_candidate = summary_value(inputs["preview_signal_summary"], "selected_candidate")
    design_status = summary_value(inputs["action_preview_design_summary"], "final_design_status")
    final_status = FINAL_STATUS if signal_status and signal_candidate == SELECTED_CANDIDATE else BLOCKED_STATUS

    preview_rows = build_preview_rows(created_at, final_status, signal_status, inputs["preview_signal"])
    summary_rows = build_summary_rows(final_status, signal_status, design_status, preview_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status, signal_status, signal_candidate)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["preview"], PREVIEW_COLUMNS, preview_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthActionPreviewResult(
        output_paths=output_paths,
        preview_rows=preview_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_action_preview(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    preview_path = root / OUTPUT_FILES["preview"]
    if not summary_path.exists() or not preview_path.exists():
        return 1, [
            "Volatility-targeted growth action preview is missing.",
            "Run `python bot.py --vol-targeted-growth-action-preview` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    preview_rows = read_csv_rows(preview_path)
    return 0, [
        "Volatility-targeted growth action preview saved display. Action-preview only; no broker reads or execution approval.",
        f"final_action_preview_status: {summary_value(summary_rows, 'final_action_preview_status')}",
        f"selected_candidate: {summary_value(summary_rows, 'selected_candidate')}",
        f"source_preview_signal_status: {summary_value(summary_rows, 'source_preview_signal_status')}",
        f"preview_row_count: {len(preview_rows)}",
        f"manual_review_label_summary: {summary_value(summary_rows, 'manual_review_label_summary')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "broker_positions_compared=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this is saved action-preview context only, not an order instruction, broker position comparison, paper execution, live trading, or scheduling approval.",
    ]


def build_preview_rows(
    created_at: str,
    final_status: str,
    signal_status: str,
    signal_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    source_status = signal_status or "missing_saved_preview_signal_status"
    sleeves = [row for row in signal_rows if row.get("signal_item") == "target_sleeve_weight"]
    if not sleeves:
        return [
            preview_row(
                created_at,
                "",
                "",
                "missing_saved_sleeve_signal",
                source_status,
                "saved_signal_missing",
                "missing_saved_preview_signal",
                "Restore or regenerate the saved preview signal before action-preview review.",
            )
        ]
    return [
        preview_row(
            created_at,
            row.get("sleeve_name", ""),
            row.get("target_weight", ""),
            row.get("sleeve_status", ""),
            source_status,
            final_status,
            "current_exposure_not_read_manual_review_required",
            NEXT_STEP,
        )
        for row in sleeves
    ]


def build_summary_rows(
    final_status: str,
    signal_status: str,
    design_status: str,
    preview_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    label_counts = count_values(preview_rows, "manual_review_label")
    rows = [
        ("final_action_preview_status", final_status, "Whether saved preview signal evidence supports this saved-output action preview."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("source_preview_signal_status", signal_status or "missing_saved_preview_signal_status", "Saved preview signal status."),
        ("source_action_preview_design_status", design_status or "missing_saved_action_preview_design_status", "Saved action-preview design status."),
        ("preview_row_count", str(len(preview_rows)), "Sleeve-level action-preview row count."),
        ("manual_review_label_summary", label_counts, "Manual-review labels produced by this saved action preview."),
        ("largest_blocker", "broker_position_comparison_not_approved_and_current_exposure_unknown", "Current exposure is not read or compared in this command."),
        ("recommended_next_step", NEXT_STEP, "Manual review is required before any broker-position comparison design."),
        ("execution_status", "execution_blocked", "Paper/live execution remains blocked."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = []
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    rows.append(("position_context_policy", "broker_positions_compared=false", "This action preview intentionally does not read broker positions."))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(final_status: str, signal_status: str, signal_candidate: str) -> list[dict[str, Any]]:
    blockers = [
        ("broker_position_comparison_not_approved", "blocked", "critical", "No broker positions are read or compared; current exposure remains unknown.", "Separate manual-review design required before any broker-position comparison."),
        ("order_instructions_not_allowed", "blocked", "critical", "This action preview uses manual-review labels only and includes no executable order fields.", "Do not add order side, order quantity, order type, account, order ID, API key, webhook, or secret fields."),
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
                "Run and review the saved preview signal before action-preview review.",
            ),
        )
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth action preview complete. Saved-output action-preview only; no broker reads, orders, or scheduling approved.",
        f"final_action_preview_status={summary_value(summary_rows, 'final_action_preview_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"source_preview_signal_status={summary_value(summary_rows, 'source_preview_signal_status')}",
        f"preview_row_count={summary_value(summary_rows, 'preview_row_count')}",
        f"manual_review_label_summary={summary_value(summary_rows, 'manual_review_label_summary')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_preview={output_paths['preview']}",
        "broker_positions_compared=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def preview_row(
    created_at: str,
    sleeve_name: str,
    target_weight: str,
    sleeve_status: str,
    source_signal_status: str,
    alignment_state: str,
    manual_review_label: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "selected_candidate": SELECTED_CANDIDATE,
        "sleeve_name": sleeve_name,
        "target_weight": target_weight,
        "sleeve_status": sleeve_status,
        "source_signal_status": source_signal_status,
        "current_exposure_status": "current_exposure_not_read",
        "current_exposure_source": "saved_preview_signal_only",
        "alignment_state": alignment_state,
        "manual_review_label": manual_review_label,
        "blocker": "broker_position_comparison_not_approved",
        "next_step": next_step,
        **SAFETY_FLAGS,
    }


def count_values(rows: list[dict[str, Any]], key: str) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return "; ".join(f"{key}={value}" for key, value in sorted(counts.items())) if counts else "none"


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
