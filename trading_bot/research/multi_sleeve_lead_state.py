"""Canonical saved-output-only lead state for multi-sleeve research."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MISSING = "missing_saved_output"

SELECTED_DECISION = "higher_growth_selected_as_research_lead_candidate_manual_review_required"
CURRENT_RESEARCH_LEAD_CANDIDATE = "higher_growth_70_20_5_5"
PREVIOUS_RESEARCH_BASELINE = "current_75_15_5_5"

LEAD_STATE_SELECTED = "higher_growth_selected_manual_review_required"
LEAD_STATE_BLOCKED_MISSING = "lead_state_blocked_missing_saved_decision"
LEAD_STATE_REVIEW_REQUIRED = "lead_state_manual_review_required"

CANDIDATE_LABEL_SELECTED = "selected_research_lead_candidate"
CANDIDATE_LABEL_UNRESOLVED = "research_lead_candidate_unresolved"
EXECUTION_STATE = "non_executable_research_only"

INPUT_FILES = {
    "decision": Path("data/multi_sleeve_research_lead_decision.csv"),
    "decision_summary": Path("data/multi_sleeve_research_lead_summary.csv"),
    "decision_blockers": Path("data/multi_sleeve_research_lead_blockers.csv"),
    "higher_growth_review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "weight_sensitivity": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "allocation_policy": Path("data/multi_sleeve_allocation_policy_review.csv"),
    "crypto_review": Path("data/multi_sleeve_crypto_review.csv"),
    "portfolio_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
}

OUTPUT_FILES = {
    "state": Path("data/multi_sleeve_lead_state.csv"),
    "summary": Path("data/multi_sleeve_lead_state_summary.csv"),
    "blockers": Path("data/multi_sleeve_lead_state_blockers.csv"),
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
    "live_trading_approved",
    "scheduling_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]

STATE_COLUMNS = [
    "created_at",
    "state_name",
    "lead_state_status",
    "current_research_lead_candidate",
    "previous_research_baseline",
    "candidate_label_status",
    "decision_source",
    "decision_status",
    "candidate_CAGR",
    "candidate_Sharpe",
    "candidate_MaxDD",
    "candidate_Calmar",
    "baseline_CAGR",
    "baseline_Sharpe",
    "baseline_MaxDD",
    "baseline_Calmar",
    "delta_CAGR",
    "delta_Sharpe",
    "delta_MaxDD",
    "delta_Calmar",
    "split_win_count",
    "worst_split_name",
    "worst_cost_stress_name",
    "drawdown_delta_vs_current",
    "blocker_summary",
    "manual_review_required",
    "required_next_step",
    "execution_state",
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
class MultiSleeveLeadStateResult:
    output_paths: dict[str, Path]
    state_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_lead_state(root_dir: Path | str = ".") -> MultiSleeveLeadStateResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    decision = inputs["decision"][0] if inputs["decision"] else {}
    state_rows = [build_state_row(created_at, decision, inputs)]
    summary_rows = build_summary_rows(created_at, state_rows[0])
    blocker_rows = build_blocker_rows(created_at, state_rows[0], inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["state"], STATE_COLUMNS, state_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return MultiSleeveLeadStateResult(
        output_paths=output_paths,
        state_rows=state_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["state"]),
    )


def show_multi_sleeve_lead_state(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve lead state is missing.",
            "Run `python bot.py --multi-sleeve-lead-state-refresh` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "Multi-sleeve lead state. Saved-output-only research state; no execution path.",
        f"current research lead candidate: {summary.get('current_research_lead_candidate', MISSING)}",
        f"previous research baseline: {summary.get('previous_research_baseline', MISSING)}",
        f"lead state status: {summary.get('lead_state_status', MISSING)}",
        f"selected candidate metrics: {summary.get('selected_candidate_metrics', MISSING)}",
        f"previous baseline metrics: {summary.get('previous_baseline_metrics', MISSING)}",
        f"deltas: {summary.get('delta_metrics', MISSING)}",
        f"split win count: {summary.get('split_win_count', MISSING)}",
        f"worst split: {summary.get('worst_split_name', MISSING)}",
        f"worst cost stress: {summary.get('worst_cost_stress_name', MISSING)}",
        f"drawdown sensitivity: {summary.get('drawdown_sensitivity', MISSING)}",
        f"manual review required: {summary.get('manual_review_required', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def build_state_row(created_at: str, decision: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    decision_status = decision.get("research_lead_decision") or MISSING
    selected = decision_status == SELECTED_DECISION
    lead_state_status = LEAD_STATE_SELECTED if selected else (LEAD_STATE_BLOCKED_MISSING if not decision else LEAD_STATE_REVIEW_REQUIRED)
    candidate = CURRENT_RESEARCH_LEAD_CANDIDATE if selected else decision.get("challenger_allocation", MISSING)
    baseline = PREVIOUS_RESEARCH_BASELINE if selected else decision.get("current_allocation", MISSING)
    return {
        "created_at": created_at,
        "state_name": "multi_sleeve_canonical_research_lead_state",
        "lead_state_status": lead_state_status,
        "current_research_lead_candidate": candidate,
        "previous_research_baseline": baseline,
        "candidate_label_status": CANDIDATE_LABEL_SELECTED if selected else CANDIDATE_LABEL_UNRESOLVED,
        "decision_source": "multi_sleeve_research_lead_decision_csv" if decision else MISSING,
        "decision_status": decision_status,
        "candidate_CAGR": decision.get("challenger_CAGR", MISSING),
        "candidate_Sharpe": decision.get("challenger_Sharpe", MISSING),
        "candidate_MaxDD": decision.get("challenger_MaxDD", MISSING),
        "candidate_Calmar": decision.get("challenger_Calmar", MISSING),
        "baseline_CAGR": decision.get("current_CAGR", MISSING),
        "baseline_Sharpe": decision.get("current_Sharpe", MISSING),
        "baseline_MaxDD": decision.get("current_MaxDD", MISSING),
        "baseline_Calmar": decision.get("current_Calmar", MISSING),
        "delta_CAGR": decision.get("delta_CAGR", MISSING),
        "delta_Sharpe": decision.get("delta_Sharpe", MISSING),
        "delta_MaxDD": decision.get("delta_MaxDD", MISSING),
        "delta_Calmar": decision.get("delta_Calmar", MISSING),
        "split_win_count": decision.get("split_win_count", MISSING),
        "worst_split_name": decision.get("worst_split_name", MISSING),
        "worst_cost_stress_name": decision.get("worst_cost_stress_name", MISSING),
        "drawdown_delta_vs_current": decision.get("drawdown_delta_vs_current", MISSING),
        "blocker_summary": blocker_summary(inputs, selected),
        "manual_review_required": True,
        "required_next_step": decision.get("required_next_step", "refresh_saved_research_lead_decision_before_state_refresh"),
        "execution_state": EXECUTION_STATE,
        **safety_flags(),
    }


def build_summary_rows(created_at: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        ("lead_state_status", state["lead_state_status"], "Canonical saved multi-sleeve state label."),
        ("current_research_lead_candidate", state["current_research_lead_candidate"], "Selected research lead candidate when saved decision supports it."),
        ("previous_research_baseline", state["previous_research_baseline"], "Previous baseline allocation."),
        ("candidate_label_status", state["candidate_label_status"], "Research label only."),
        ("decision_status", state["decision_status"], "Saved research-lead decision source status."),
        ("selected_candidate_metrics", format_candidate_metrics(state), "Selected candidate metrics copied from saved decision."),
        ("previous_baseline_metrics", format_baseline_metrics(state), "Baseline metrics copied from saved decision."),
        ("delta_metrics", format_delta_metrics(state), "Candidate minus baseline deltas copied from saved decision."),
        ("split_win_count", state["split_win_count"], "Fixed split wins copied from saved decision."),
        ("worst_split_name", state["worst_split_name"], "Worst split copied from saved decision."),
        ("worst_cost_stress_name", state["worst_cost_stress_name"], "Worst cost stress copied from saved decision."),
        ("drawdown_sensitivity", f"drawdown_delta_vs_current={state['drawdown_delta_vs_current']}", "Drawdown delta copied from saved decision."),
        ("manual_review_required", str(state["manual_review_required"]).lower(), "Manual review remains required."),
        ("blocker_summary", state["blocker_summary"], "Canonical blocker categories."),
        ("required_next_step", state["required_next_step"], "Next research step only."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(created_at: str, state: dict[str, Any], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    available = bool(inputs["decision"])
    checks = [
        ("manual_review_required", "manual_review_required", "high", "selected candidate remains manual-review-only", state["required_next_step"]),
        ("drawdown_sensitivity", "drawdown_review_required", "medium", f"drawdown_delta_vs_current={state['drawdown_delta_vs_current']}", state["required_next_step"]),
        ("high_growth_drawdown_context", "manual_review_required", "medium", "higher high-growth allocation increases tail-risk/outlier context", state["required_next_step"]),
        ("crypto_volatility_context", context_status(inputs["crypto_review"]), "medium", "crypto sleeve remains research-only context", state["required_next_step"]),
        ("execution_boundary", "blocked_non_executable_research_only", "high", "canonical state is not an order or paper/live execution path", state["required_next_step"]),
        ("crypto_execution_boundary", "blocked_non_executable_research_only", "high", "canonical state is not crypto execution", state["required_next_step"]),
        ("scheduling_boundary", "blocked_no_scheduling_change", "high", "canonical state is not a schedule or cron change", state["required_next_step"]),
        ("saved_output_completeness", "pass" if available else "blocked_missing_saved_decision", "high" if not available else "low", "saved research lead decision available" if available else "missing multi_sleeve_research_lead_decision.csv", state["required_next_step"]),
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


def blocker_summary(inputs: dict[str, list[dict[str, str]]], selected: bool) -> str:
    if not inputs["decision"]:
        return "saved_output_completeness"
    base = ["manual_review_required", "drawdown_sensitivity", "high_growth_drawdown_context", "crypto_volatility_context", "execution_boundary", "crypto_execution_boundary", "scheduling_boundary"]
    if not selected:
        base.insert(0, "lead_state_review_required")
    return ", ".join(base)


def context_status(rows: list[dict[str, str]]) -> str:
    return "context_available_research_only" if rows else "context_missing_review_required"


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return [
        "Multi-sleeve lead state refreshed. Saved-output-only research state; no execution path.",
        f"current research lead candidate: {summary.get('current_research_lead_candidate', MISSING)}",
        f"previous research baseline: {summary.get('previous_research_baseline', MISSING)}",
        f"lead state status: {summary.get('lead_state_status', MISSING)}",
        f"selected candidate metrics: {summary.get('selected_candidate_metrics', MISSING)}",
        f"previous baseline metrics: {summary.get('previous_baseline_metrics', MISSING)}",
        f"deltas: {summary.get('delta_metrics', MISSING)}",
        f"split win count: {summary.get('split_win_count', MISSING)}",
        f"worst split: {summary.get('worst_split_name', MISSING)}",
        f"worst cost stress: {summary.get('worst_cost_stress_name', MISSING)}",
        f"drawdown sensitivity: {summary.get('drawdown_sensitivity', MISSING)}",
        f"manual review required: {summary.get('manual_review_required', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        f"Saved lead state: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def format_candidate_metrics(state: dict[str, Any]) -> str:
    return f"{state.get('current_research_lead_candidate')}: CAGR={state.get('candidate_CAGR')}; Sharpe={state.get('candidate_Sharpe')}; MaxDD={state.get('candidate_MaxDD')}; Calmar={state.get('candidate_Calmar')}"


def format_baseline_metrics(state: dict[str, Any]) -> str:
    return f"{state.get('previous_research_baseline')}: CAGR={state.get('baseline_CAGR')}; Sharpe={state.get('baseline_Sharpe')}; MaxDD={state.get('baseline_MaxDD')}; Calmar={state.get('baseline_Calmar')}"


def format_delta_metrics(state: dict[str, Any]) -> str:
    return f"CAGR={state.get('delta_CAGR')}; Sharpe={state.get('delta_Sharpe')}; MaxDD={state.get('delta_MaxDD')}; Calmar={state.get('delta_Calmar')}"


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


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
        "live_trading_approved": False,
        "scheduling_approved": False,
        "shorting_approved": False,
        "leverage_approved": False,
        "margin_approved": False,
    }
