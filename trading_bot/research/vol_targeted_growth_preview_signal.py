"""Saved-output preview signal for volatility-targeted growth 15/20.

This module creates a report-only preview signal for the selected
volatility-targeted growth candidate. It reads saved report outputs only and
never refreshes market data, reads broker state, creates order instructions,
schedules anything, or approves execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_preview_signal_created_saved_output_only"
BLOCKED_STATUS = "vol_targeted_growth_preview_signal_blocked_missing_design_evidence"
NEXT_STEP = "manual_review_saved_preview_signal_before_any_action_preview_design"

OUTPUT_FILES = {
    "signal": Path("data/vol_targeted_growth_preview_signal.csv"),
    "summary": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_preview_signal_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_preview_signal_blockers.csv"),
}

INPUT_FILES = {
    "preview_design_summary": Path("data/vol_targeted_growth_preview_design_summary.csv"),
    "preview_design": Path("data/vol_targeted_growth_preview_design.csv"),
    "preview_design_evidence": Path("data/vol_targeted_growth_preview_design_evidence.csv"),
    "preview_readiness_summary": Path("data/vol_targeted_growth_preview_readiness_summary.csv"),
    "nearby_variants_review": Path("data/vol_targeted_growth_nearby_variants_review.csv"),
}

SLEEVE_WEIGHTS = [
    ("qqq100_core_trend_sleeve", "0.70", "clean_main_stock_etf_lead"),
    ("high_growth_stock_research_sleeve", "0.20", "high_growth_research_only"),
    ("crypto_research_sleeve", "0.05", "crypto_research_only"),
    ("defensive_cash_or_bond_sleeve", "0.05", "defensive_buffer_research_only"),
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "preview_only": True,
    "preview_signal_only": True,
    "preview_signal_saved": True,
    "action_preview_created": False,
    "order_instructions_created": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
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

SIGNAL_COLUMNS = [
    "created_at",
    "signal_item",
    "signal_status",
    "selected_candidate",
    "volatility_target_pct",
    "volatility_window_days",
    "exposure_cap",
    "leverage_allowed",
    "sleeve_name",
    "target_weight",
    "sleeve_status",
    "signal_value",
    "source_status",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthPreviewSignalResult:
    output_paths: dict[str, Path]
    signal_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_preview_signal(root_dir: Path | str = ".") -> VolTargetedGrowthPreviewSignalResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    design_status = summary_value(inputs["preview_design_summary"], "final_design_status")
    design_candidate = summary_value(inputs["preview_design_summary"], "selected_candidate")
    target = find_row(inputs["nearby_variants_review"], "candidate_name", SELECTED_CANDIDATE)
    final_status = FINAL_STATUS if design_status and design_candidate == SELECTED_CANDIDATE else BLOCKED_STATUS

    signal_rows = build_signal_rows(created_at, final_status, design_status)
    summary_rows = build_summary_rows(final_status, design_status, target, inputs)
    evidence_rows = build_evidence_rows(inputs, target)
    blocker_rows = build_blocker_rows(final_status, design_status, design_candidate)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["signal"], SIGNAL_COLUMNS, signal_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthPreviewSignalResult(
        output_paths=output_paths,
        signal_rows=signal_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_preview_signal(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    signal_path = root / OUTPUT_FILES["signal"]
    if not summary_path.exists() or not signal_path.exists():
        return 1, [
            "Volatility-targeted growth preview signal is missing.",
            "Run `python bot.py --vol-targeted-growth-preview-signal` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    signal_rows = read_csv_rows(signal_path)
    return 0, [
        "Volatility-targeted growth preview signal saved display. Saved-output preview signal only; no execution approval.",
        f"final_signal_status: {summary_value(summary_rows, 'final_signal_status')}",
        f"selected_candidate: {summary_value(summary_rows, 'selected_candidate')}",
        f"target_variant: {summary_value(summary_rows, 'target_variant')}",
        f"target_sleeve_weights: {sleeve_weight_line(signal_rows)}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "action_preview_created=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this preview signal is not an action preview, order instruction, paper execution, live trading, or scheduling approval.",
    ]


def build_signal_rows(created_at: str, final_status: str, design_status: str) -> list[dict[str, Any]]:
    rows = [
        signal_row(
            created_at,
            "candidate_identity",
            final_status,
            "",
            "",
            "",
            f"candidate={SELECTED_CANDIDATE}; base_allocation=higher_growth_multi_sleeve",
            design_status or "missing_saved_design_status",
            NEXT_STEP,
        ),
        signal_row(
            created_at,
            "volatility_overlay",
            "preview_signal_recorded",
            "",
            "",
            "",
            "volatility_target=15%; volatility_window=20 trading days; exposure_cap=1x; leverage_allowed=false",
            design_status or "missing_saved_design_status",
            "manual_review_volatility_overlay_before_any_action_preview",
        ),
    ]
    for sleeve_name, target_weight, sleeve_status in SLEEVE_WEIGHTS:
        rows.append(
            signal_row(
                created_at,
                "target_sleeve_weight",
                "preview_signal_recorded",
                sleeve_name,
                target_weight,
                sleeve_status,
                f"{sleeve_name} target_weight={target_weight}; preview_weight_only_not_order_quantity",
                design_status or "missing_saved_design_status",
                "manual_review_sleeve_weights_before_any_action_preview",
            )
        )
    rows.append(
        signal_row(
            created_at,
            "execution_boundary",
            "execution_blocked",
            "",
            "",
            "",
            "No action preview, executable order instruction, paper execution, live trading, or scheduling is approved.",
            design_status or "missing_saved_design_status",
            "keep_strategy_disconnected_from_execution",
        )
    )
    return rows


def build_summary_rows(
    final_status: str,
    design_status: str,
    target: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = [
        ("final_signal_status", final_status, "Whether the saved design supports this saved-output preview signal."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("target_variant", "volatility_target=15%; volatility_window=20; exposure_cap=1x; leverage_allowed=false", "Preview signal variant identity."),
        ("target_sleeve_weights", "70% qqq100_core_trend_sleeve; 20% high_growth_stock_research_sleeve; 5% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve", "Saved preview weights only, not order quantities."),
        ("design_status", design_status or "missing_saved_design_status", "Saved preview design status."),
        ("target_metrics", metric_line(target), "Saved selected candidate metrics where available."),
        ("readiness_context", summary_value(inputs["preview_readiness_summary"], "final_decision_status") or "missing_readiness_context", "Saved preview-readiness decision context."),
        ("largest_blocker", "action_preview_not_created_and_order_instructions_not_allowed", "This signal does not compare against positions or create executable instructions."),
        ("recommended_next_step", NEXT_STEP, "Manual review is required before any separate action-preview design discussion."),
        ("execution_status", "execution_blocked", "Paper/live execution remains blocked."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], target: dict[str, str]) -> list[dict[str, Any]]:
    rows = [("selected_candidate_metrics", metric_line(target), "Saved selected candidate metrics.")]
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(final_status: str, design_status: str, design_candidate: str) -> list[dict[str, Any]]:
    blockers = [
        ("action_preview_not_created", "blocked", "critical", "This command does not create an action preview or compare saved exposure with broker positions.", "Manual review before any separate action-preview design."),
        ("order_instructions_not_allowed", "blocked", "critical", "Saved target weights are not order quantities and must not be treated as executable orders.", "Keep order side/quantity/type/account fields out of this signal."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "Keep all approval flags false."),
        ("high_growth_and_crypto_remain_research_only", "blocked", "high", "The high-growth and crypto sleeves remain research-only components in this saved preview signal.", "Do not promote component sleeves to execution."),
    ]
    if final_status == BLOCKED_STATUS:
        blockers.insert(
            0,
            (
                "missing_preview_design_evidence",
                "blocked",
                "high",
                f"design_status={design_status}; design_candidate={design_candidate}",
                "Run and review the preview design checkpoint first.",
            ),
        )
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth preview signal complete. Saved-output preview signal only; no action preview, orders, or scheduling approved.",
        f"final_signal_status={summary_value(summary_rows, 'final_signal_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"target_variant={summary_value(summary_rows, 'target_variant')}",
        f"target_sleeve_weights={summary_value(summary_rows, 'target_sleeve_weights')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_signal={output_paths['signal']}",
        "action_preview_created=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def signal_row(
    created_at: str,
    signal_item: str,
    signal_status: str,
    sleeve_name: str,
    target_weight: str,
    sleeve_status: str,
    signal_value: str,
    source_status: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "signal_item": signal_item,
        "signal_status": signal_status,
        "selected_candidate": SELECTED_CANDIDATE,
        "volatility_target_pct": "15",
        "volatility_window_days": "20",
        "exposure_cap": "1x",
        "leverage_allowed": False,
        "sleeve_name": sleeve_name,
        "target_weight": target_weight,
        "sleeve_status": sleeve_status,
        "signal_value": signal_value,
        "source_status": source_status,
        "required_next_step": required_next_step,
        **SAFETY_FLAGS,
    }


def sleeve_weight_line(rows: list[dict[str, str]]) -> str:
    weights = [
        f"{row.get('sleeve_name')}={row.get('target_weight')}"
        for row in rows
        if row.get("signal_item") == "target_sleeve_weight"
    ]
    return "; ".join(weights) if weights else "missing_saved_sleeve_weights"


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


def find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def metric_line(row: dict[str, str]) -> str:
    if not row:
        return "missing_saved_metrics"
    return (
        f"CAGR={row.get('cagr', 'missing')}; "
        f"Sharpe={row.get('sharpe', 'missing')}; "
        f"MaxDD={row.get('max_drawdown', 'missing')}; "
        f"Calmar={row.get('calmar', 'missing')}"
    )


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""
