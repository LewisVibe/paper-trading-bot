"""Saved-output preview design for volatility-targeted growth 15/20.

This is a design/report checkpoint only. It documents a future preview-only
mode for the selected volatility-targeted growth candidate and never creates
executable order instructions, reads broker state, refreshes market data,
schedules anything, or approves execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_preview_design_ready_for_future_preview_implementation"
BLOCKED_STATUS = "vol_targeted_growth_preview_design_blocked_missing_readiness_evidence"
NEXT_STEP = "implement_saved_output_preview_signal_for_vol_targeted_growth_15_20_in_separate_prompt"

OUTPUT_FILES = {
    "design": Path("data/vol_targeted_growth_preview_design.csv"),
    "summary": Path("data/vol_targeted_growth_preview_design_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_preview_design_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_preview_design_blockers.csv"),
}

INPUT_FILES = {
    "readiness_summary": Path("data/vol_targeted_growth_preview_readiness_summary.csv"),
    "readiness_decision": Path("data/vol_targeted_growth_preview_readiness_decision.csv"),
    "nearby_review": Path("data/vol_targeted_growth_nearby_variants_review.csv"),
    "robustness_summary": Path("data/vol_targeted_growth_robustness_checkpoint_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "preview_design_only": True,
    "preview_signal_created": False,
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
class VolTargetedGrowthPreviewDesignResult:
    output_paths: dict[str, Path]
    design_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_preview_design(root_dir: Path | str = ".") -> VolTargetedGrowthPreviewDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    selected_candidate = extract_candidate_name(summary_value(inputs["readiness_summary"], "selected_candidate"))
    decision_status = summary_value(inputs["readiness_summary"], "final_decision_status")
    target = find_row(inputs["nearby_review"], "candidate_name", SELECTED_CANDIDATE)
    final_status = FINAL_STATUS if selected_candidate == SELECTED_CANDIDATE and decision_status else BLOCKED_STATUS

    design_rows = build_design_rows(created_at, final_status, target)
    summary_rows = build_summary_rows(final_status, decision_status, target, inputs)
    evidence_rows = build_evidence_rows(inputs, target)
    blocker_rows = build_blocker_rows(final_status, selected_candidate, decision_status)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["design"], DESIGN_COLUMNS, design_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthPreviewDesignResult(
        output_paths=output_paths,
        design_rows=design_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_preview_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted growth preview design is missing.",
            "Run `python bot.py --vol-targeted-growth-preview-design` first.",
            "preview_signal_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted growth preview design saved display. Design/report only; no execution approval.",
        f"final_design_status: {summary_value(summary_rows, 'final_design_status')}",
        f"selected_candidate: {summary_value(summary_rows, 'selected_candidate')}",
        f"target_variant: {summary_value(summary_rows, 'target_variant')}",
        f"future_preview_output_scope: {summary_value(summary_rows, 'future_preview_output_scope')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "preview_signal_created=false; action_preview_created=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this is a preview design checkpoint only; it does not create a preview signal or orders.",
    ]


def build_design_rows(created_at: str, final_status: str, target: dict[str, str]) -> list[dict[str, Any]]:
    return [
        design_row(
            created_at,
            "candidate_scope",
            final_status,
            "medium",
            SELECTED_CANDIDATE,
            "selected_candidate_only",
            "The future preview mode must cover only the 15% target / 20-day volatility-targeted growth candidate unless a separate decision changes scope.",
            NEXT_STEP,
        ),
        design_row(
            created_at,
            "target_variant",
            "design_recorded",
            "medium",
            SELECTED_CANDIDATE,
            "base_allocation=higher_growth_multi_sleeve; volatility_target=15%; volatility_window=20 trading days; exposure_cap=1x; no leverage",
            "Variant identity comes from saved nearby-variant and preview-readiness decision outputs.",
            "future_preview_signal_must_emit_variant_identity_only_not_orders",
        ),
        design_row(
            created_at,
            "future_preview_inputs",
            "design_recorded",
            "medium",
            SELECTED_CANDIDATE,
            "saved QQQ100 sleeve state; saved high-growth research sleeve state; saved crypto research sleeve state; saved defensive/cash context; saved volatility-targeted robustness and nearby-variant evidence",
            "Future preview must use saved/report-safe inputs first and label missing data as blockers.",
            "define_input_schema_before_any_preview_signal_command",
        ),
        design_row(
            created_at,
            "future_preview_outputs",
            "design_recorded",
            "medium",
            SELECTED_CANDIDATE,
            "candidate identity; volatility target/window; sleeve target weights; sleeve statuses; blockers; safety flags; no ticker-level order side/quantity/type/account fields",
            "Preview output should describe desired research exposure, not executable orders.",
            "implement_saved_output_preview_signal_without_order_instructions",
        ),
        design_row(
            created_at,
            "target_sleeve_weights",
            "design_recorded",
            "medium",
            SELECTED_CANDIDATE,
            "70% qqq100_core_trend_sleeve; 20% high_growth_stock_research_sleeve; 5% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve; scaled by 15% target volatility overlay where saved data supports it",
            "The source stream is the saved higher-growth multi-sleeve candidate with a 15% volatility target.",
            "future_preview_signal_must_mark_weights_as_preview_not_orders",
        ),
        design_row(
            created_at,
            "execution_boundary",
            "execution_blocked",
            "critical",
            SELECTED_CANDIDATE,
            metric_line(target),
            "Design does not create preview implementation, action preview, paper execution, portfolio execution, or scheduling.",
            "manual_review_then_separate_preview_signal_implementation_prompt",
        ),
    ]


def build_summary_rows(
    final_status: str,
    decision_status: str,
    target: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = [
        ("final_design_status", final_status, "Whether saved readiness evidence supports a future preview-only design."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected candidate for this design checkpoint."),
        ("decision_status", decision_status or "missing_saved_decision_status", "Saved preview-readiness decision status."),
        ("target_variant", "volatility_target=15%; volatility_window=20; exposure_cap=1x; no leverage", "Preview design target variant."),
        ("target_metrics", metric_line(target), "Saved selected candidate metrics."),
        ("future_preview_output_scope", "saved candidate identity, target weights, volatility target/window, sleeve statuses, blockers, safety flags; no order side/quantity/type/account fields", "Future preview output shape."),
        ("readiness_context", summary_value(inputs["readiness_summary"], "preview_design_readiness_status") or "missing_readiness_context", "Preview design discussion context."),
        ("largest_blocker", "preview_signal_not_implemented_and_no_order_instructions_allowed", "This command is only the design checkpoint."),
        ("recommended_next_step", NEXT_STEP, "Next prompt should implement saved-output preview signal only."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], target: dict[str, str]) -> list[dict[str, Any]]:
    rows = [("target_metrics", metric_line(target), "Saved selected candidate metrics.")]
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(final_status: str, selected_candidate: str, decision_status: str) -> list[dict[str, Any]]:
    blockers = [
        ("preview_signal_not_implemented", "blocked", "critical", "This checkpoint does not create the future preview signal command.", NEXT_STEP),
        ("order_instructions_not_allowed", "blocked", "critical", "Future preview output must not include executable order side/quantity/type/account fields.", "Keep preview outputs report-only."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "Keep all approval flags false."),
        ("component_contribution_review_not_final", "manual_review_required", "medium", "Future preview should keep sleeve-level contribution and crypto/high-growth role context visible.", "Add contribution fields to preview signal if implemented later."),
    ]
    if final_status == BLOCKED_STATUS:
        blockers.insert(0, ("missing_readiness_evidence", "blocked", "high", f"decision_status={decision_status}; selected_candidate={selected_candidate}", "Run preview-readiness decision before design."))
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth preview design complete. Saved-output design/report only; no execution, orders, or scheduling approved.",
        f"final_design_status={summary_value(summary_rows, 'final_design_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"target_variant={summary_value(summary_rows, 'target_variant')}",
        f"future_preview_output_scope={summary_value(summary_rows, 'future_preview_output_scope')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['design']}",
        "preview_signal_created=false; action_preview_created=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def design_row(
    created_at: str,
    design_item: str,
    status: str,
    risk_level: str,
    selected_candidate: str,
    design_value: str,
    rationale: str,
    required_next_step: str,
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


def extract_candidate_name(value: str) -> str:
    if ":" in value:
        return value.split(":", 1)[0].strip()
    return value.strip()


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""
