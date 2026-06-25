"""Saved-output candidate selection decision for higher-growth preview review.

This module chooses which saved high-growth candidate should be taken into a
future preview-only design discussion. It reads saved CSV reports only and does
not refresh market data, call Alpaca, read positions, create order instructions,
schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_70_20_5_5"
BALANCED_CANDIDATE = "balanced_multi_sleeve_research_portfolio"
CRYPTO_BLEND_CANDIDATE = "qqq100_plus_high_growth_plus_crypto_research"
QQQ100_BASELINE = "qqq100_only_reference"

FINAL_STATUS = "higher_growth_candidate_selected_for_preview_design_review"
BLOCKED_STATUS = "higher_growth_candidate_selection_blocked_missing_saved_evidence"

OUTPUT_FILES = {
    "decision": Path("data/higher_growth_candidate_selection_decision.csv"),
    "summary": Path("data/higher_growth_candidate_selection_summary.csv"),
    "evidence": Path("data/higher_growth_candidate_selection_evidence.csv"),
    "blockers": Path("data/higher_growth_candidate_selection_blockers.csv"),
}

INPUT_FILES = {
    "preview_readiness_summary": Path("data/higher_growth_preview_readiness_summary.csv"),
    "preview_readiness_pack": Path("data/higher_growth_preview_readiness_pack.csv"),
    "discovery_report": Path("data/high_growth_strategy_discovery_sprint.csv"),
    "higher_growth_review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "higher_growth_summary": Path("data/multi_sleeve_higher_growth_summary.csv"),
    "multi_sleeve_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "preview_only": True,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "action_preview_created": False,
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

DECISION_COLUMNS = [
    "created_at",
    "candidate_name",
    "candidate_role",
    "selection_status",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "delta_cagr_vs_qqq100",
    "delta_sharpe_vs_qqq100",
    "delta_max_drawdown_vs_qqq100",
    "delta_calmar_vs_qqq100",
    "decision_reason",
    "largest_blocker",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class HigherGrowthCandidateSelectionResult:
    output_paths: dict[str, Path]
    decision_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_higher_growth_candidate_selection_decision(root_dir: Path | str = ".") -> HigherGrowthCandidateSelectionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}

    selected = find_row(inputs["higher_growth_review"], "allocation_name", SELECTED_CANDIDATE)
    qqq100 = find_row(inputs["multi_sleeve_backtest"], "portfolio_name", QQQ100_BASELINE)
    balanced = find_row(inputs["multi_sleeve_backtest"], "portfolio_name", BALANCED_CANDIDATE)
    crypto_blend = find_row(inputs["multi_sleeve_backtest"], "portfolio_name", CRYPTO_BLEND_CANDIDATE)
    discovery_selected = find_row(inputs["discovery_report"], "candidate_name", SELECTED_CANDIDATE)

    decision_rows = build_decision_rows(created_at, selected, qqq100, balanced, crypto_blend, discovery_selected, inputs)
    summary_rows = build_summary_rows(decision_rows, selected, qqq100, balanced, crypto_blend, inputs)
    evidence_rows = build_evidence_rows(inputs, selected, qqq100, balanced, crypto_blend, discovery_selected)
    blocker_rows = build_blocker_rows(summary_rows, selected, qqq100, balanced, crypto_blend)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decision"], DECISION_COLUMNS, decision_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HigherGrowthCandidateSelectionResult(
        output_paths=output_paths,
        decision_rows=decision_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_higher_growth_candidate_selection_decision(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Higher-growth candidate selection decision is missing.",
            "Run `python bot.py --higher-growth-candidate-selection-decision` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; preview_candidate_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Higher-growth candidate selection saved display. Research/report only; no execution approval.",
        f"final_selection_status: {summary_value(summary_rows, 'final_selection_status')}",
        f"selected_candidate: {summary_value(summary_rows, 'selected_candidate')}",
        f"selected_reason: {summary_value(summary_rows, 'selected_reason')}",
        f"runner_up: {summary_value(summary_rows, 'runner_up')}",
        f"crypto_blend_status: {summary_value(summary_rows, 'crypto_blend_status')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this decision selects a candidate for future preview-design review only; it does not implement preview mode or create order instructions.",
    ]


def build_decision_rows(
    created_at: str,
    selected: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    crypto_blend: dict[str, str],
    discovery_selected: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    return [
        decision_row(
            created_at,
            SELECTED_CANDIDATE,
            "selected_for_preview_design_review",
            "selected_manual_review_required",
            selected_metrics(selected),
            qqq100,
            "Best saved candidate for next preview-design review: strongest CAGR/Sharpe/Calmar mix, supportive split count, and cost stress remains promising.",
            "preview_implementation_not_added_and_manual_review_required",
            "design_preview_only_mode_in_separate_prompt_after_manual_review",
        ),
        decision_row(
            created_at,
            BALANCED_CANDIDATE,
            "runner_up_calmer_comparator",
            "not_selected_but_keep_as_safety_comparator",
            portfolio_metrics(balanced),
            qqq100,
            "Runner-up has slightly milder drawdown and similar Sharpe, but gives up CAGR and Calmar versus selected candidate.",
            "not_selected_for_first_preview_design_review",
            "keep_as_comparator_for_preview_design_and_risk_policy",
        ),
        decision_row(
            created_at,
            CRYPTO_BLEND_CANDIDATE,
            "strong_but_crypto_policy_blocked",
            "not_selected_crypto_policy_review_required",
            portfolio_metrics(crypto_blend),
            qqq100,
            "Strong saved metrics, but crypto sleeve policy and volatility review make it a later candidate, not the first preview design.",
            "crypto_policy_and_volatility_review_required",
            "keep_crypto_blend_research_only_until_separate_crypto_policy_review",
        ),
        decision_row(
            created_at,
            QQQ100_BASELINE,
            "clean_current_paper_live_baseline",
            "baseline_retained",
            portfolio_metrics(qqq100),
            qqq100,
            "QQQ100 remains the clean current paper-live monitor base while higher-growth stays preview-design review only.",
            "none_for_baseline",
            "do_not_replace_current_q q q100_paper_live_base_without_separate_review".replace(" ", ""),
        ),
        {
            "created_at": created_at,
            "candidate_name": "selection_context",
            "candidate_role": "saved_evidence_context",
            "selection_status": "context_recorded",
            "cagr": "not_applicable",
            "sharpe": "not_applicable",
            "max_drawdown": "not_applicable",
            "calmar": "not_applicable",
            "delta_cagr_vs_qqq100": "not_applicable",
            "delta_sharpe_vs_qqq100": "not_applicable",
            "delta_max_drawdown_vs_qqq100": "not_applicable",
            "delta_calmar_vs_qqq100": "not_applicable",
            "decision_reason": (
                f"discovery_status={discovery_selected.get('final_candidate_status', 'missing')}; "
                f"split_win_count={summary_value(inputs['higher_growth_summary'], 'split_win_count')}; "
                f"cost_stress={summary_value(inputs['higher_growth_summary'], 'worst_cost_stress_result')}; "
                f"readiness={summary_value(inputs['preview_readiness_summary'], 'final_readiness_status')}"
            ),
            "largest_blocker": "preview_implementation_not_added_and_manual_review_required",
            "required_next_step": "manual_review_then_separate_preview_only_design_prompt",
            **SAFETY_FLAGS,
        },
    ]


def build_summary_rows(
    decision_rows: list[dict[str, Any]],
    selected: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    crypto_blend: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    missing = [name for name, row in [("selected", selected), ("qqq100", qqq100), ("balanced", balanced), ("crypto_blend", crypto_blend)] if not row]
    final_status = BLOCKED_STATUS if missing else FINAL_STATUS
    selected_reason = (
        f"{SELECTED_CANDIDATE}: CAGR={selected.get('CAGR', 'missing')}; Sharpe={selected.get('Sharpe', 'missing')}; "
        f"MaxDD={selected.get('MaxDD', 'missing')}; Calmar={selected.get('Calmar', 'missing')}; "
        f"delta_CAGR_vs_QQQ100={delta(parse_float(selected.get('CAGR')), parse_float(qqq100.get('candidate_cagr')))}"
    )
    rows = [
        ("final_selection_status", final_status, "Candidate selected for future preview-design review only."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected candidate."),
        ("selected_reason", selected_reason, "Saved metric reason for selection."),
        ("runner_up", f"{BALANCED_CANDIDATE}: {metric_summary_from_decision(decision_rows, BALANCED_CANDIDATE)}", "Calmer comparator retained."),
        ("crypto_blend_status", f"{CRYPTO_BLEND_CANDIDATE}: not_selected_crypto_policy_review_required", "Crypto blend stays later/research-only."),
        ("qqq100_baseline_retained", f"{QQQ100_BASELINE}: {portfolio_line(qqq100)}", "QQQ100 remains current clean paper-live base."),
        ("readiness_status", summary_value(inputs["preview_readiness_summary"], "final_readiness_status") or "missing_saved_readiness_status", "Prior readiness pack status."),
        ("split_win_count", summary_value(inputs["higher_growth_summary"], "split_win_count") or "missing_saved_split_evidence", "Saved split evidence."),
        ("worst_cost_stress_result", summary_value(inputs["higher_growth_summary"], "worst_cost_stress_result") or "missing_saved_cost_stress_evidence", "Saved cost stress evidence."),
        ("largest_blocker", "preview_implementation_not_added_and_manual_review_required", "No preview implementation or execution approval exists."),
        ("recommended_next_step", "design_saved_output_preview_only_mode_for_higher_growth_70_20_5_5", "Next implementation should still be preview-only/report-only."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(
    inputs: dict[str, list[dict[str, str]]],
    selected: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    crypto_blend: dict[str, str],
    discovery_selected: dict[str, str],
) -> list[dict[str, Any]]:
    rows = [
        ("selected_metrics", selected_line(selected), "Saved higher-growth review target row."),
        ("qqq100_metrics", portfolio_line(qqq100), "Saved QQQ100 baseline row."),
        ("balanced_metrics", portfolio_line(balanced), "Saved balanced comparator row."),
        ("crypto_blend_metrics", portfolio_line(crypto_blend), "Saved crypto blend comparator row."),
        ("discovery_status", discovery_selected.get("final_candidate_status", "missing_saved_discovery_status"), "Saved discovery sprint status."),
    ]
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(
    summary_rows: list[dict[str, Any]],
    selected: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    crypto_blend: dict[str, str],
) -> list[dict[str, Any]]:
    blockers = [
        ("preview_implementation_not_added", "blocked", "critical", "No preview-only implementation exists for the selected candidate.", "Build a separate saved-output preview design before any paper discussion."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, order instructions, or scheduling are approved.", "Keep all approval flags false."),
        ("manual_review_required", "manual_review_required", "high", "Human review is required before turning the selected candidate into preview-only design.", "Review allocation policy, risk, split/cost evidence, and crypto exclusions."),
        ("crypto_blend_deferred", "manual_review_required", "medium", "Crypto blend remains research-only until separate crypto policy review.", "Do not select crypto blend as first preview candidate."),
    ]
    for name, row in [("selected", selected), ("qqq100", qqq100), ("balanced", balanced), ("crypto_blend", crypto_blend)]:
        if not row:
            blockers.insert(0, (f"missing_{name}_saved_evidence", "blocked", "high", f"Required saved evidence missing: {name}", "Regenerate or inspect saved research reports before selection."))
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Higher-growth candidate selection decision complete. Saved-output research only; no execution, orders, or scheduling approved.",
        f"final_selection_status={summary_value(summary_rows, 'final_selection_status')}",
        f"selected_candidate={summary_value(summary_rows, 'selected_candidate')}",
        f"selected_reason={summary_value(summary_rows, 'selected_reason')}",
        f"runner_up={summary_value(summary_rows, 'runner_up')}",
        f"crypto_blend_status={summary_value(summary_rows, 'crypto_blend_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['decision']}",
        "preview_candidate_approved=false; preview_implementation_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def decision_row(
    created_at: str,
    candidate_name: str,
    candidate_role: str,
    selection_status: str,
    metrics: dict[str, float | None],
    qqq100: dict[str, str],
    decision_reason: str,
    largest_blocker: str,
    required_next_step: str,
) -> dict[str, Any]:
    qqq_cagr = parse_float(qqq100.get("candidate_cagr"))
    qqq_sharpe = parse_float(qqq100.get("candidate_sharpe"))
    qqq_maxdd = parse_float(qqq100.get("candidate_max_drawdown"))
    qqq_calmar = parse_float(qqq100.get("candidate_calmar"))
    return {
        "created_at": created_at,
        "candidate_name": candidate_name,
        "candidate_role": candidate_role,
        "selection_status": selection_status,
        "cagr": format_metric(metrics["cagr"]),
        "sharpe": format_metric(metrics["sharpe"]),
        "max_drawdown": format_metric(metrics["max_drawdown"]),
        "calmar": format_metric(metrics["calmar"]),
        "delta_cagr_vs_qqq100": format_metric(delta_float(metrics["cagr"], qqq_cagr)),
        "delta_sharpe_vs_qqq100": format_metric(delta_float(metrics["sharpe"], qqq_sharpe)),
        "delta_max_drawdown_vs_qqq100": format_metric(delta_float(metrics["max_drawdown"], qqq_maxdd)),
        "delta_calmar_vs_qqq100": format_metric(delta_float(metrics["calmar"], qqq_calmar)),
        "decision_reason": decision_reason,
        "largest_blocker": largest_blocker,
        "required_next_step": required_next_step,
        **SAFETY_FLAGS,
    }


def selected_metrics(row: dict[str, str]) -> dict[str, float | None]:
    return {
        "cagr": parse_float(row.get("CAGR")),
        "sharpe": parse_float(row.get("Sharpe")),
        "max_drawdown": parse_float(row.get("MaxDD")),
        "calmar": parse_float(row.get("Calmar")),
    }


def portfolio_metrics(row: dict[str, str]) -> dict[str, float | None]:
    return {
        "cagr": parse_float(row.get("candidate_cagr")),
        "sharpe": parse_float(row.get("candidate_sharpe")),
        "max_drawdown": parse_float(row.get("candidate_max_drawdown")),
        "calmar": parse_float(row.get("candidate_calmar")),
    }


def selected_line(row: dict[str, str]) -> str:
    return f"CAGR={row.get('CAGR', 'missing')}; Sharpe={row.get('Sharpe', 'missing')}; MaxDD={row.get('MaxDD', 'missing')}; Calmar={row.get('Calmar', 'missing')}"


def portfolio_line(row: dict[str, str]) -> str:
    return f"CAGR={row.get('candidate_cagr', 'missing')}; Sharpe={row.get('candidate_sharpe', 'missing')}; MaxDD={row.get('candidate_max_drawdown', 'missing')}; Calmar={row.get('candidate_calmar', 'missing')}"


def metric_summary_from_decision(rows: list[dict[str, Any]], candidate_name: str) -> str:
    for row in rows:
        if row.get("candidate_name") == candidate_name:
            return f"CAGR={row.get('cagr')}; Sharpe={row.get('sharpe')}; MaxDD={row.get('max_drawdown')}; Calmar={row.get('calmar')}"
    return "missing_saved_metrics"


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


def parse_float(value: Any) -> float | None:
    try:
        text = str(value).strip().replace("%", "")
        if not text or "missing" in text.lower() or text.lower() == "nan":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def delta_float(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def delta(left: float | None, right: float | None) -> str:
    return format_metric(delta_float(left, right))


def format_metric(value: float | None) -> str:
    return "missing_saved_metrics" if value is None else str(round(value, 4))


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
