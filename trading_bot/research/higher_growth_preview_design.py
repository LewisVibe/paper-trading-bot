"""Saved-output preview design for higher_growth_70_20_5_5.

This is a design/report checkpoint only. It documents a future preview-only
mode for the selected higher-growth candidate and never creates executable
order instructions, reads broker state, refreshes market data, schedules
anything, or approves execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_70_20_5_5"
FINAL_STATUS = "higher_growth_preview_design_ready_for_future_preview_implementation"
BLOCKED_STATUS = "higher_growth_preview_design_blocked_missing_selection_evidence"
NEXT_STEP = "implement_saved_output_preview_signal_for_higher_growth_70_20_5_5_in_separate_prompt"

OUTPUT_FILES = {
    "design": Path("data/higher_growth_preview_design.csv"),
    "summary": Path("data/higher_growth_preview_design_summary.csv"),
    "evidence": Path("data/higher_growth_preview_design_evidence.csv"),
    "blockers": Path("data/higher_growth_preview_design_blockers.csv"),
}

INPUT_FILES = {
    "selection_summary": Path("data/higher_growth_candidate_selection_summary.csv"),
    "selection_decision": Path("data/higher_growth_candidate_selection_decision.csv"),
    "readiness_summary": Path("data/higher_growth_preview_readiness_summary.csv"),
    "higher_growth_review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "multi_sleeve_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
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
class HigherGrowthPreviewDesignResult:
    output_paths: dict[str, Path]
    design_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_higher_growth_preview_design(root_dir: Path | str = ".") -> HigherGrowthPreviewDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    selection_status = summary_value(inputs["selection_summary"], "final_selection_status")
    selected_candidate = summary_value(inputs["selection_summary"], "selected_candidate")
    target = find_row(inputs["higher_growth_review"], "allocation_name", SELECTED_CANDIDATE)
    qqq100 = find_row(inputs["multi_sleeve_backtest"], "portfolio_name", "qqq100_only_reference")

    final_status = FINAL_STATUS if selected_candidate == SELECTED_CANDIDATE and selection_status else BLOCKED_STATUS
    design_rows = build_design_rows(created_at, final_status, target)
    summary_rows = build_summary_rows(final_status, selection_status, target, qqq100, inputs)
    evidence_rows = build_evidence_rows(inputs, target, qqq100)
    blocker_rows = build_blocker_rows(final_status, selection_status, selected_candidate)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["design"], DESIGN_COLUMNS, design_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HigherGrowthPreviewDesignResult(
        output_paths=output_paths,
        design_rows=design_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_higher_growth_preview_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Higher-growth preview design is missing.",
            "Run `python bot.py --higher-growth-preview-design` first.",
            "preview_signal_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Higher-growth preview design saved display. Design/report only; no execution approval.",
        f"final_design_status: {summary_value(summary_rows, 'final_design_status')}",
        f"selected_candidate: {summary_value(summary_rows, 'selected_candidate')}",
        f"target_sleeve_weights: {summary_value(summary_rows, 'target_sleeve_weights')}",
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
            "The future preview mode must cover only higher_growth_70_20_5_5 unless a separate decision changes scope.",
            NEXT_STEP,
        ),
        design_row(
            created_at,
            "target_sleeve_weights",
            "design_recorded",
            "medium",
            SELECTED_CANDIDATE,
            "70% qqq100_core_trend_sleeve; 20% high_growth_stock_research_sleeve; 5% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve",
            "Weights mirror the selected higher-growth allocation name and saved review context.",
            "future_preview_signal_must_emit_saved_weights_only_not_orders",
        ),
        design_row(
            created_at,
            "future_preview_inputs",
            "design_recorded",
            "medium",
            SELECTED_CANDIDATE,
            "saved QQQ100 signal/state; saved high-growth sleeve state; saved crypto research state; saved defensive sleeve state; saved cost/split evidence",
            "Future preview must use saved/report-safe inputs first and label missing data as blockers.",
            "define_input_schema_before_any_preview_signal_command",
        ),
        design_row(
            created_at,
            "future_preview_outputs",
            "design_recorded",
            "medium",
            SELECTED_CANDIDATE,
            "target_weight rows; sleeve_status rows; blocker rows; no ticker-level order side/quantity/type fields",
            "Preview output should describe desired research exposure, not executable orders.",
            "implement_saved_output_preview_signal_without_order_instructions",
        ),
        design_row(
            created_at,
            "broker_fee_cost_boundary",
            "cost_model_requires_future_review",
            "high",
            SELECTED_CANDIDATE,
            "saved cost stress exists, but no live broker/slippage/fill model is approved",
            "Existing backtests use saved turnover/cost stress, not real broker execution costs.",
            "add_preview_cost_stress_fields_before_any_paper_execution_discussion",
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
    selection_status: str,
    target: dict[str, str],
    qqq100: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = [
        ("final_design_status", final_status, "Whether the saved selection evidence supports a future preview-only design."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected candidate for this design checkpoint."),
        ("selection_status", selection_status or "missing_saved_selection_status", "Saved candidate selection status."),
        ("target_metrics", metric_line(target), "Saved selected candidate metrics."),
        ("qqq100_baseline", portfolio_line(qqq100), "QQQ100 remains the current clean paper-live base."),
        ("target_sleeve_weights", "70% qqq100_core_trend_sleeve; 20% high_growth_stock_research_sleeve; 5% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve", "Preview design target weights."),
        ("future_preview_output_scope", "saved target weights, sleeve statuses, blockers, safety flags; no order side/quantity/type/account fields", "Future preview output shape."),
        ("saved_cost_context", summary_value(inputs["selection_summary"], "worst_cost_stress_result") or "missing_saved_cost_context", "Saved cost stress context."),
        ("largest_blocker", "preview_signal_not_implemented_and_no_order_instructions_allowed", "This command is only the design checkpoint."),
        ("recommended_next_step", NEXT_STEP, "Next prompt should implement saved-output preview signal only."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], target: dict[str, str], qqq100: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("target_metrics", metric_line(target), "Saved higher-growth target metrics."),
        ("qqq100_baseline", portfolio_line(qqq100), "Saved QQQ100 baseline metrics."),
    ]
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(final_status: str, selection_status: str, selected_candidate: str) -> list[dict[str, Any]]:
    blockers = [
        ("preview_signal_not_implemented", "blocked", "critical", "This checkpoint does not create the future preview signal command.", NEXT_STEP),
        ("order_instructions_not_allowed", "blocked", "critical", "Future preview output must not include executable order side/quantity/type/account fields.", "Keep preview outputs report-only."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "Keep all approval flags false."),
        ("broker_fee_cost_model_not_final", "manual_review_required", "medium", "Saved reports contain cost stress, not a real broker/slippage/fill model.", "Add stricter preview cost-stress fields before paper execution discussion."),
    ]
    if final_status == BLOCKED_STATUS:
        blockers.insert(0, ("missing_selection_evidence", "blocked", "high", f"selection_status={selection_status}; selected_candidate={selected_candidate}", "Run selection decision before design."))
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Higher-growth preview design complete. Saved-output design/report only; no execution, orders, or scheduling approved.",
        f"final_design_status={summary_value(summary_rows, 'final_design_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"target_sleeve_weights={summary_value(summary_rows, 'target_sleeve_weights')}",
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


def metric_line(row: dict[str, str]) -> str:
    return f"CAGR={row.get('CAGR', 'missing')}; Sharpe={row.get('Sharpe', 'missing')}; MaxDD={row.get('MaxDD', 'missing')}; Calmar={row.get('Calmar', 'missing')}"


def portfolio_line(row: dict[str, str]) -> str:
    return f"CAGR={row.get('candidate_cagr', 'missing')}; Sharpe={row.get('candidate_sharpe', 'missing')}; MaxDD={row.get('candidate_max_drawdown', 'missing')}; Calmar={row.get('candidate_calmar', 'missing')}"


def find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


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
