"""Saved-output-only research lead decision for the multi-sleeve allocation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MISSING = "missing_saved_output"

CURRENT_ALLOCATION = "current_75_15_5_5"
CHALLENGER_ALLOCATION = "higher_growth_70_20_5_5"

STATUS_SELECTED = "higher_growth_selected_as_research_lead_candidate_manual_review_required"
STATUS_CHALLENGER = "higher_growth_remains_challenger_drawdown_review_required"
STATUS_BLOCKED_MISSING = "research_lead_decision_blocked_missing_saved_outputs"

NEXT_MANUAL_REVIEW = "manual_review_before_multi_sleeve_research_lead_label_change"
NEXT_SAVED_OUTPUTS = "refresh_saved_higher_growth_review_before_research_lead_decision"
NEXT_BLOCKER_REVIEW = "manual_review_drawdown_split_cost_blockers_before_label_change"

INPUT_FILES = {
    "higher_growth_review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "higher_growth_summary": Path("data/multi_sleeve_higher_growth_summary.csv"),
    "higher_growth_split": Path("data/multi_sleeve_higher_growth_split_review.csv"),
    "higher_growth_cost": Path("data/multi_sleeve_higher_growth_cost_review.csv"),
    "higher_growth_drawdown": Path("data/multi_sleeve_higher_growth_drawdown_review.csv"),
    "higher_growth_blockers": Path("data/multi_sleeve_higher_growth_blockers.csv"),
    "weight_sensitivity": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "weight_summary": Path("data/multi_sleeve_weight_sensitivity_summary.csv"),
    "allocation_policy": Path("data/multi_sleeve_allocation_policy_review.csv"),
    "crypto_review": Path("data/multi_sleeve_crypto_review.csv"),
    "portfolio_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "qqq100_metrics": Path("data/qqq100_recovered_reference_metrics.csv"),
}

OUTPUT_FILES = {
    "decision": Path("data/multi_sleeve_research_lead_decision.csv"),
    "summary": Path("data/multi_sleeve_research_lead_summary.csv"),
    "blockers": Path("data/multi_sleeve_research_lead_blockers.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "preview_only",
    "saved_output_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "yfinance_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]

DECISION_COLUMNS = [
    "created_at",
    "decision_subject",
    "current_allocation",
    "challenger_allocation",
    "current_CAGR",
    "current_Sharpe",
    "current_MaxDD",
    "current_Calmar",
    "challenger_CAGR",
    "challenger_Sharpe",
    "challenger_MaxDD",
    "challenger_Calmar",
    "delta_CAGR",
    "delta_Sharpe",
    "delta_MaxDD",
    "delta_Calmar",
    "split_win_count",
    "worst_split_name",
    "worst_split_delta_CAGR",
    "worst_split_delta_Sharpe",
    "worst_split_delta_MaxDD",
    "worst_split_delta_Calmar",
    "worst_cost_stress_name",
    "worst_cost_stress_CAGR",
    "worst_cost_stress_delta_CAGR_vs_current",
    "drawdown_delta_vs_current",
    "research_lead_decision",
    "decision_confidence",
    "blocker_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = ["created_at", "summary_name", "summary_value", "details", *SAFETY_COLUMNS]
BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "blocker_severity",
    "blocker_detail",
    "required_next_step",
    "execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
]


@dataclass
class ResearchLeadDecisionResult:
    output_paths: dict[str, Path]
    decision_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_research_lead_decision(root_dir: Path | str = ".") -> ResearchLeadDecisionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    missing_required = [name for name in ["higher_growth_review", "higher_growth_summary", "higher_growth_split", "higher_growth_cost", "higher_growth_drawdown"] if not inputs[name]]

    if missing_required:
        decision_rows = [blocked_decision_row(created_at, missing_required)]
    else:
        decision_rows = [build_decision_row(created_at, inputs)]
    summary_rows = build_summary_rows(created_at, decision_rows[0], inputs, missing_required)
    blocker_rows = build_blocker_rows(created_at, decision_rows[0], inputs, missing_required)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decision"], DECISION_COLUMNS, decision_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return ResearchLeadDecisionResult(
        output_paths=output_paths,
        decision_rows=decision_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["decision"]),
    )


def show_multi_sleeve_research_lead_decision(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve research lead decision is missing.",
            "Run `python bot.py --multi-sleeve-research-lead-decision` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "Multi-sleeve research lead decision. Saved-output-only research; no execution approval.",
        f"final research lead decision: {summary.get('final_research_lead_decision', MISSING)}",
        f"current allocation metrics: {summary.get('current_allocation_metrics', MISSING)}",
        f"challenger allocation metrics: {summary.get('challenger_allocation_metrics', MISSING)}",
        f"delta metrics: {summary.get('delta_metrics', MISSING)}",
        f"split win count and worst split: {summary.get('split_summary', MISSING)}",
        f"worst cost stress: {summary.get('worst_cost_stress', MISSING)}",
        f"drawdown sensitivity: {summary.get('drawdown_sensitivity', MISSING)}",
        f"key blockers: {summary.get('key_blockers', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def build_decision_row(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    review_rows = inputs["higher_growth_review"]
    split_rows = inputs["higher_growth_split"]
    cost_rows = inputs["higher_growth_cost"]
    drawdown_rows = inputs["higher_growth_drawdown"]
    current = row_named(review_rows, "allocation_name", CURRENT_ALLOCATION)
    challenger = row_named(review_rows, "allocation_name", CHALLENGER_ALLOCATION)
    split_win_count = split_wins(split_rows)
    worst_split = worst_split_row(split_rows)
    worst_cost = worst_cost_row(cost_rows)
    challenger_drawdown = row_named(drawdown_rows, "allocation_name", CHALLENGER_ALLOCATION)
    decision = decision_status(current, challenger, split_win_count, worst_split, worst_cost, challenger_drawdown)
    return {
        "created_at": created_at,
        "decision_subject": "multi_sleeve_research_lead_decision",
        "current_allocation": CURRENT_ALLOCATION,
        "challenger_allocation": CHALLENGER_ALLOCATION,
        "current_CAGR": current.get("CAGR", MISSING),
        "current_Sharpe": current.get("Sharpe", MISSING),
        "current_MaxDD": current.get("MaxDD", MISSING),
        "current_Calmar": current.get("Calmar", MISSING),
        "challenger_CAGR": challenger.get("CAGR", MISSING),
        "challenger_Sharpe": challenger.get("Sharpe", MISSING),
        "challenger_MaxDD": challenger.get("MaxDD", MISSING),
        "challenger_Calmar": challenger.get("Calmar", MISSING),
        "delta_CAGR": challenger.get("delta_CAGR", MISSING),
        "delta_Sharpe": challenger.get("delta_Sharpe", MISSING),
        "delta_MaxDD": challenger.get("delta_MaxDD", MISSING),
        "delta_Calmar": challenger.get("delta_Calmar", MISSING),
        "split_win_count": str(split_win_count),
        "worst_split_name": worst_split.get("split_name", MISSING),
        "worst_split_delta_CAGR": worst_split.get("delta_CAGR_higher_growth_vs_current", MISSING),
        "worst_split_delta_Sharpe": worst_split.get("delta_Sharpe_higher_growth_vs_current", MISSING),
        "worst_split_delta_MaxDD": worst_split.get("delta_MaxDD_higher_growth_vs_current", MISSING),
        "worst_split_delta_Calmar": worst_split.get("delta_Calmar_higher_growth_vs_current", MISSING),
        "worst_cost_stress_name": worst_cost.get("cost_stress_name", MISSING),
        "worst_cost_stress_CAGR": worst_cost.get("CAGR", MISSING),
        "worst_cost_stress_delta_CAGR_vs_current": worst_cost.get("delta_CAGR_vs_current_base", MISSING),
        "drawdown_delta_vs_current": challenger_drawdown.get("drawdown_delta_vs_current", MISSING),
        "research_lead_decision": decision,
        "decision_confidence": decision_confidence(decision),
        "blocker_status": blocker_status_for(decision),
        "required_next_step": next_step_for(decision),
        **safety_flags(),
    }


def blocked_decision_row(created_at: str, missing_required: list[str]) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "decision_subject": "multi_sleeve_research_lead_decision",
        "current_allocation": CURRENT_ALLOCATION,
        "challenger_allocation": CHALLENGER_ALLOCATION,
        "current_CAGR": MISSING,
        "current_Sharpe": MISSING,
        "current_MaxDD": MISSING,
        "current_Calmar": MISSING,
        "challenger_CAGR": MISSING,
        "challenger_Sharpe": MISSING,
        "challenger_MaxDD": MISSING,
        "challenger_Calmar": MISSING,
        "delta_CAGR": MISSING,
        "delta_Sharpe": MISSING,
        "delta_MaxDD": MISSING,
        "delta_Calmar": MISSING,
        "split_win_count": MISSING,
        "worst_split_name": MISSING,
        "worst_split_delta_CAGR": MISSING,
        "worst_split_delta_Sharpe": MISSING,
        "worst_split_delta_MaxDD": MISSING,
        "worst_split_delta_Calmar": MISSING,
        "worst_cost_stress_name": MISSING,
        "worst_cost_stress_CAGR": MISSING,
        "worst_cost_stress_delta_CAGR_vs_current": MISSING,
        "drawdown_delta_vs_current": MISSING,
        "research_lead_decision": STATUS_BLOCKED_MISSING,
        "decision_confidence": "blocked_missing_saved_outputs=" + ",".join(missing_required),
        "blocker_status": "blocked_missing_saved_outputs",
        "required_next_step": NEXT_SAVED_OUTPUTS,
        **safety_flags(),
    }


def decision_status(
    current: dict[str, str],
    challenger: dict[str, str],
    split_win_count: int,
    worst_split: dict[str, str],
    worst_cost: dict[str, str],
    challenger_drawdown: dict[str, str],
) -> str:
    rules_pass = [
        parse_float(challenger.get("delta_CAGR")) > 0,
        parse_float(challenger.get("delta_Sharpe")) > 0,
        parse_float(challenger.get("delta_Calmar")) > 0,
        parse_float(challenger.get("delta_MaxDD")) >= -1.0,
        split_win_count >= 2,
        parse_float(worst_split.get("delta_Calmar_higher_growth_vs_current")) > 0
        or parse_float(worst_split.get("delta_Sharpe_higher_growth_vs_current")) > 0,
        parse_float(worst_cost.get("delta_CAGR_vs_current_base")) > 0,
        parse_float(challenger_drawdown.get("drawdown_delta_vs_current")) >= -1.0,
        all_false_approvals(current),
        all_false_approvals(challenger),
    ]
    return STATUS_SELECTED if all(rules_pass) else STATUS_CHALLENGER


def build_summary_rows(
    created_at: str,
    decision: dict[str, Any],
    inputs: dict[str, list[dict[str, str]]],
    missing_required: list[str],
) -> list[dict[str, Any]]:
    key_blockers = key_blocker_names(decision, inputs, missing_required)
    items = [
        ("final_research_lead_decision", decision["research_lead_decision"], "Saved-output-only decision label."),
        ("current_allocation_metrics", format_current_metrics(decision), "Current allocation reference metrics."),
        ("challenger_allocation_metrics", format_challenger_metrics(decision), "Higher-growth challenger metrics."),
        ("delta_metrics", format_delta_metrics(decision), "Challenger minus current metrics."),
        ("split_summary", format_split_summary(decision), "Split win count and worst fixed split."),
        ("worst_cost_stress", format_cost_summary(decision), "Worst fixed high-growth turnover cost stress."),
        ("drawdown_sensitivity", format_drawdown_summary(decision), "Drawdown change versus current allocation."),
        ("key_blockers", ", ".join(key_blockers) or "none", "Remaining blocker categories."),
        ("required_next_step", decision["required_next_step"], "Next research step only."),
        ("saved_output_completeness", "blocked=" + ",".join(missing_required) if missing_required else "available", "Required saved outputs."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(
    created_at: str,
    decision: dict[str, Any],
    inputs: dict[str, list[dict[str, str]]],
    missing_required: list[str],
) -> list[dict[str, Any]]:
    if missing_required:
        return [
            blocker_row(
                created_at,
                "saved_output_completeness",
                "blocked_missing_saved_outputs",
                "high",
                ",".join(missing_required),
                NEXT_SAVED_OUTPUTS,
            )
        ]
    checks = [
        ("split_validation", split_blocker_status(decision), "medium", format_split_summary(decision), NEXT_MANUAL_REVIEW),
        ("cost_stress", cost_blocker_status(decision), "medium", format_cost_summary(decision), NEXT_MANUAL_REVIEW),
        ("drawdown_sensitivity", drawdown_blocker_status(decision), "medium", format_drawdown_summary(decision), NEXT_BLOCKER_REVIEW),
        ("crypto_volatility_context", context_status(inputs["crypto_review"]), "medium", "crypto sleeve remains research-only context", NEXT_MANUAL_REVIEW),
        ("high_growth_drawdown_context", "manual_review_required", "medium", "higher high-growth sleeve weight increases outlier/tail-risk dependence", NEXT_MANUAL_REVIEW),
        ("saved_output_completeness", "pass", "low", "required higher-growth saved outputs are available", NEXT_MANUAL_REVIEW),
        ("execution_boundary", "blocked_false_execution_flags", "high", "research decision is not paper or live execution", NEXT_MANUAL_REVIEW),
        ("scheduling_boundary", "blocked_false_scheduling_flags", "high", "research decision is not a scheduling change", NEXT_MANUAL_REVIEW),
    ]
    return [blocker_row(created_at, *check) for check in checks]


def blocker_row(created_at: str, name: str, status: str, severity: str, detail: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "blocker_status": status,
        "blocker_severity": severity,
        "blocker_detail": detail,
        "required_next_step": next_step,
        "execution_approved": False,
        "crypto_execution_approved": False,
        "scheduling_approved": False,
    }


def split_wins(rows: list[dict[str, str]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("allocation_name") == CHALLENGER_ALLOCATION
        and parse_float(row.get("delta_Calmar_higher_growth_vs_current")) > 0
        and parse_float(row.get("delta_Sharpe_higher_growth_vs_current")) > 0
    )


def worst_split_row(rows: list[dict[str, str]]) -> dict[str, str]:
    candidates = [row for row in rows if row.get("allocation_name") == CHALLENGER_ALLOCATION]
    return min(candidates, key=lambda row: parse_float(row.get("delta_Calmar_higher_growth_vs_current")), default={})


def worst_cost_row(rows: list[dict[str, str]]) -> dict[str, str]:
    candidates = [row for row in rows if row.get("allocation_name") == CHALLENGER_ALLOCATION]
    return min(candidates, key=lambda row: parse_float(row.get("delta_CAGR_vs_current_base")), default={})


def all_false_approvals(row: dict[str, str]) -> bool:
    for key in ["execution_approved", "paper_execution_approved", "crypto_execution_approved", "scheduling_approved"]:
        if str(row.get(key, "false")).lower() != "false":
            return False
    return True


def key_blocker_names(decision: dict[str, Any], _inputs: dict[str, list[dict[str, str]]], missing_required: list[str]) -> list[str]:
    if missing_required:
        return ["saved_output_completeness"]
    names = ["drawdown_sensitivity", "high_growth_drawdown_context", "crypto_volatility_context", "execution_boundary", "scheduling_boundary"]
    if parse_float(decision.get("worst_split_delta_Calmar")) <= 0 or parse_float(decision.get("worst_split_delta_Sharpe")) <= 0:
        names.insert(0, "split_validation")
    if parse_float(decision.get("worst_cost_stress_delta_CAGR_vs_current")) <= 0:
        names.insert(0, "cost_stress")
    return names


def split_blocker_status(decision: dict[str, Any]) -> str:
    return "pass_manual_review_still_required" if int_or_zero(decision.get("split_win_count")) >= 2 else "split_review_required"


def cost_blocker_status(decision: dict[str, Any]) -> str:
    return "pass_manual_review_still_required" if parse_float(decision.get("worst_cost_stress_delta_CAGR_vs_current")) > 0 else "cost_review_required"


def drawdown_blocker_status(decision: dict[str, Any]) -> str:
    return "drawdown_review_required" if parse_float(decision.get("drawdown_delta_vs_current")) < 0 else "pass_manual_review_still_required"


def context_status(rows: list[dict[str, str]]) -> str:
    return "context_available_research_only" if rows else "context_missing_review_required"


def decision_confidence(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING:
        return "blocked"
    if status == STATUS_SELECTED:
        return "medium_saved_output_cautious_rules"
    return "low_drawdown_or_split_review_required"


def blocker_status_for(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING:
        return "blocked_missing_saved_outputs"
    if status == STATUS_SELECTED:
        return "manual_review_required_before_label_change"
    return "drawdown_review_required_before_label_change"


def next_step_for(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING:
        return NEXT_SAVED_OUTPUTS
    if status == STATUS_SELECTED:
        return NEXT_MANUAL_REVIEW
    return NEXT_BLOCKER_REVIEW


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return [
        "Multi-sleeve research lead decision created. Saved-output-only research; no execution approval.",
        f"final research lead decision: {summary.get('final_research_lead_decision', MISSING)}",
        f"current allocation metrics: {summary.get('current_allocation_metrics', MISSING)}",
        f"challenger allocation metrics: {summary.get('challenger_allocation_metrics', MISSING)}",
        f"delta metrics: {summary.get('delta_metrics', MISSING)}",
        f"split win count and worst split: {summary.get('split_summary', MISSING)}",
        f"worst cost stress: {summary.get('worst_cost_stress', MISSING)}",
        f"drawdown sensitivity: {summary.get('drawdown_sensitivity', MISSING)}",
        f"key blockers: {summary.get('key_blockers', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        f"Saved decision: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def format_current_metrics(row: dict[str, Any]) -> str:
    return f"{row.get('current_allocation')}: CAGR={row.get('current_CAGR')}; Sharpe={row.get('current_Sharpe')}; MaxDD={row.get('current_MaxDD')}; Calmar={row.get('current_Calmar')}"


def format_challenger_metrics(row: dict[str, Any]) -> str:
    return f"{row.get('challenger_allocation')}: CAGR={row.get('challenger_CAGR')}; Sharpe={row.get('challenger_Sharpe')}; MaxDD={row.get('challenger_MaxDD')}; Calmar={row.get('challenger_Calmar')}"


def format_delta_metrics(row: dict[str, Any]) -> str:
    return f"CAGR={row.get('delta_CAGR')}; Sharpe={row.get('delta_Sharpe')}; MaxDD={row.get('delta_MaxDD')}; Calmar={row.get('delta_Calmar')}"


def format_split_summary(row: dict[str, Any]) -> str:
    return f"wins={row.get('split_win_count')}; worst={row.get('worst_split_name')}; dCAGR={row.get('worst_split_delta_CAGR')}; dSharpe={row.get('worst_split_delta_Sharpe')}; dMaxDD={row.get('worst_split_delta_MaxDD')}; dCalmar={row.get('worst_split_delta_Calmar')}"


def format_cost_summary(row: dict[str, Any]) -> str:
    return f"{row.get('worst_cost_stress_name')}: CAGR={row.get('worst_cost_stress_CAGR')}; dCAGR_vs_current={row.get('worst_cost_stress_delta_CAGR_vs_current')}"


def format_drawdown_summary(row: dict[str, Any]) -> str:
    return f"drawdown_delta_vs_current={row.get('drawdown_delta_vs_current')}; full_period_delta_MaxDD={row.get('delta_MaxDD')}"


def row_named(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    return next((row for row in rows if row.get(key) == value), {})


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


def int_or_zero(value: Any) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": True,
        "saved_output_only": True,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
        "orders_replaced": False,
        "alpaca_called": False,
        "yfinance_called": False,
        "live_position_read": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "scheduling_approved": False,
        "live_trading_approved": False,
        "shorting_approved": False,
        "leverage_approved": False,
        "margin_approved": False,
    }
