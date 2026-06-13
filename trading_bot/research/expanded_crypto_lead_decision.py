"""Saved-output crypto research lead decision checkpoint.

This report consolidates the expanded crypto research branch into a research
lead label only. It reads saved research CSVs where available and never touches
broker, position, database, alert, config, scheduling, or execution paths.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CANDIDATES = [
    "equal_weight_eligible_crypto_benchmark",
    "equal_weight_inception_aware",
    "crypto_equal_weight_ex_highest_vol_2",
    "crypto_risk_on_momentum_persistence",
    "codex_ambitious_crypto_btc_eth_core_alt_accelerator",
    "btc_buy_and_hold_benchmark",
    "eth_buy_and_hold_benchmark",
    "btc_eth_50_50_monthly_rebalanced_benchmark",
    "cash_benchmark",
]

INPUT_FILES = {
    "universe_summary": Path("data/crypto_universe_readiness_summary.csv"),
    "strategy_summary": Path("data/expanded_crypto_strategy_lab_summary.csv"),
    "robustness_summary": Path("data/expanded_crypto_robustness_summary.csv"),
    "reality_check": Path("data/expanded_crypto_equal_weight_reality_check.csv"),
    "crash_gate_summary": Path("data/crypto_equal_weight_crash_gate_summary.csv"),
    "volatility_summary": Path("data/crypto_equal_weight_volatility_scaling_summary.csv"),
    "capped_summary": Path("data/crypto_equal_weight_capped_risk_summary.csv"),
    "capped_contributions": Path("data/crypto_equal_weight_capped_risk_contributions.csv"),
    "strategy_splits": Path("data/expanded_crypto_strategy_lab_splits.csv"),
    "robustness_splits": Path("data/expanded_crypto_robustness_splits.csv"),
    "capped_splits": Path("data/crypto_equal_weight_capped_risk_splits.csv"),
    "capped_costs": Path("data/crypto_equal_weight_capped_risk_costs.csv"),
    "capped_drawdowns": Path("data/crypto_equal_weight_capped_risk_drawdowns.csv"),
}

OUTPUT_FILES = {
    "decision": Path("data/expanded_crypto_lead_decision.csv"),
    "summary": Path("data/expanded_crypto_lead_decision_summary.csv"),
    "evidence": Path("data/expanded_crypto_lead_decision_evidence.csv"),
}

DECISION_LABELS = [
    "crypto_equal_weight_ex_highest_vol_2_research_lead",
    "crypto_equal_weight_benchmark_lead_high_drawdown",
    "crypto_risk_on_momentum_persistence_lead_candidate",
    "codex_crypto_accelerator_lead_candidate",
    "crypto_research_lead_split_sensitive",
    "crypto_research_lead_outlier_dependent",
    "crypto_research_lead_cost_review_required",
    "crypto_research_not_ready_for_lead_decision",
    "insufficient_saved_inputs",
    "manual_review_required",
]

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "section",
    "strategy_name",
    "metric_name",
    "metric_value",
    "status",
    "summary_label",
    "evidence",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class ExpandedCryptoLeadDecisionResult:
    decision_path: Path
    summary_path: Path
    evidence_path: Path
    decision_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_expanded_crypto_lead_decision(data_dir: Path | str = "data") -> ExpandedCryptoLeadDecisionResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(data_path / path.name) for name, path in INPUT_FILES.items()}
    input_status = {name: bool(rows) for name, rows in inputs.items()}
    evidence_rows = build_evidence_rows(created_at, inputs, input_status)
    decision_label, selected_lead, lead_style, blockers, next_step = decide_lead(inputs, input_status)
    decision_rows = build_decision_rows(created_at, decision_label, selected_lead, lead_style, blockers, next_step)
    summary_rows = build_summary_rows(created_at, inputs, input_status, decision_label, selected_lead, lead_style, blockers, next_step)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["decision"], decision_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["evidence"], evidence_rows)
    return ExpandedCryptoLeadDecisionResult(
        decision_path=output_paths["decision"],
        summary_path=output_paths["summary"],
        evidence_path=output_paths["evidence"],
        decision_rows=decision_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_expanded_crypto_lead_decision_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    decision = read_csv(data_path / OUTPUT_FILES["decision"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    evidence = read_csv(data_path / OUTPUT_FILES["evidence"].name)
    if not decision or not summary:
        return 1, ["Run `python bot.py --expanded-crypto-lead-decision` first."]
    approvals = {str(row.get("execution_approved", "")).lower() for row in decision + summary + evidence}
    return 0, [
        "Expanded crypto lead decision. Display only; execution_approved=False.",
        f"Final crypto lead decision label: {summary_value(summary, 'final_crypto_lead_decision_label')}",
        f"Selected crypto research lead: {summary_value(summary, 'selected_crypto_research_lead')}",
        f"Lead style: {summary_value(summary, 'lead_style')}",
        f"Full-period evidence: {summary_value(summary, 'full_period_evidence')}",
        f"Split evidence: {summary_value(summary, 'split_evidence')}",
        f"Cost evidence: {summary_value(summary, 'cost_evidence')}",
        f"Drawdown evidence: {summary_value(summary, 'drawdown_evidence')}",
        f"Outlier/contribution evidence: {summary_value(summary, 'outlier_contribution_evidence')}",
        f"Rejected family summary: {summary_value(summary, 'rejected_family_summary')}",
        f"Remaining blockers: {summary_value(summary, 'remaining_blockers')}",
        f"Required next step: {summary_value(summary, 'required_next_step')}",
        f"execution_approved values: {', '.join(sorted(approvals)) or 'false'}",
        "Warning: crypto lead labels are research-only and do not approve crypto execution, preview promotion, or order instructions.",
    ]


def build_evidence_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]], input_status: dict[str, bool]) -> list[dict[str, Any]]:
    rows = []
    for name, present in input_status.items():
        rows.append(
            common_row(
                created_at,
                "input_status",
                name,
                "saved_input_present",
                str(present),
                "input_available" if present else "missing_saved_input",
                "manual_review_required",
                f"Saved input {INPUT_FILES[name]} {'was found' if present else 'was missing or empty'}.",
                "Regenerate the missing research report if this evidence is required.",
            )
        )
    rows.extend(category_rows(created_at, inputs))
    return rows


def category_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    capped_summary = inputs["capped_summary"]
    capped_contributions = inputs["capped_contributions"]
    capped_costs = inputs["capped_costs"]
    capped_splits = inputs["capped_splits"]
    capped_drawdowns = inputs["capped_drawdowns"]
    crash_label = summary_value(inputs["crash_gate_summary"], "final_summary_label")
    volatility_label = summary_value(inputs["volatility_summary"], "final_summary_label")
    robustness_label = summary_value(inputs["robustness_summary"], "final_summary_label")
    rows = [
        common_row(created_at, "universe_readiness", "expanded_crypto_universe", "eligible_symbols", "BTC-USD, ETH-USD, SOL-USD, BNB-USD, XRP-USD, ADA-USD, AVAX-USD, LINK-USD, DOT-USD, LTC-USD, BCH-USD, DOGE-USD, TRX-USD, ATOM-USD", "universe_ready_review", "manual_review_required", "POL-USD and MATIC-USD remain transition/manual-review symbols.", "Keep POL/MATIC transition-blocked until a separate review."),
        common_row(created_at, "full_period_performance", "crypto_equal_weight_ex_highest_vol_2", "candidate_evidence", summary_value(capped_summary, "best_capped_risk_variant"), "candidate_review", "manual_review_required", "Capped-risk best variant is read from saved capped-risk summary where available.", "Confirm full-period metrics with current saved report before any future promotion discussion."),
        common_row(created_at, "equal_weight_reality_review", "equal_weight_eligible_crypto_benchmark", "robustness_label", robustness_label, "benchmark_high_drawdown_review", "manual_review_required", "Equal-weight remains the key benchmark but carries severe drawdown and outlier-dependence review.", "Keep equal-weight as benchmark context, not execution approval."),
        common_row(created_at, "outlier_top_contributor_dependence", "crypto_equal_weight_ex_highest_vol_2", "contribution_status_counts", status_counts(capped_contributions), "outlier_review", "crypto_research_lead_outlier_dependent", "Contribution rows include top_contributor, top_2 contributors, Herfindahl concentration, max single asset average weight, and top-contributor dependency where available.", "Run contribution review manually before treating the lead as robust."),
        common_row(created_at, "cost_survival", "crypto_equal_weight_ex_highest_vol_2", "cost_status_counts", status_counts(capped_costs), "cost_review", "crypto_research_lead_cost_review_required", "Cost survival comes from saved capped-risk cost stress rows where available.", "Confirm 10 bps and 25 bps survival before any future preview discussion."),
        common_row(created_at, "fixed_split_sensitivity", "crypto_equal_weight_ex_highest_vol_2", "split_status_counts", status_counts(capped_splits), "split_review", "crypto_research_lead_split_sensitive", "Split sensitivity comes from fixed 60/40, 70/30, and 80/20 saved split rows where available.", "Treat split sensitivity as a blocker/review warning, not hidden evidence."),
        common_row(created_at, "drawdown_recovery_context", "crypto_equal_weight_ex_highest_vol_2", "drawdown_status_counts", status_counts(capped_drawdowns), "drawdown_review", "manual_review_required", "Drawdown context is read from saved capped-risk drawdown rows where available; high drawdown alone does not block research-lead status.", "Review worst drawdown and recovery before any promotion discussion."),
        common_row(created_at, "comparison_vs_equal_weight", "crypto_equal_weight_ex_highest_vol_2", "summary_delta", comparison_text(capped_summary), "candidate_vs_benchmark", "manual_review_required", "Compares capped-risk candidate against static equal-weight where saved summary rows exist.", "Keep benchmark-relative evidence explicit."),
        common_row(created_at, "comparison_vs_btc", "btc_buy_and_hold_benchmark", "comparison", "saved comparison available in detailed result reports when regenerated", "benchmark_context", "manual_review_required", "BTC comparison remains context only; this checkpoint does not create signals.", "Review BTC benchmark deltas in underlying research report."),
        common_row(created_at, "comparison_vs_eth", "eth_buy_and_hold_benchmark", "comparison", "saved comparison available in detailed result reports when regenerated", "benchmark_context", "manual_review_required", "ETH comparison remains context only; this checkpoint does not create signals.", "Review ETH benchmark deltas in underlying research report."),
        common_row(created_at, "comparison_vs_active_candidates", "crypto_risk_on_momentum_persistence", "candidate_set", ", ".join(CANDIDATES), "candidate_context", "manual_review_required", "Momentum persistence and Codex accelerator remain candidate context, not execution routes.", "Keep active-strategy comparisons research-only."),
        common_row(created_at, "rejected_strategy_families", "hard_crash_gates", "rejected_family_summary", f"hard crash gates rejected for return drag; defensive throttles downgraded or rejected for return drag / weak drawdown improvement; crash_gate_label={crash_label}; volatility_scaling_label={volatility_label}", "rejected_family_review", "manual_review_required", "Hard crash gates and blunt defensive throttles should not be promoted from this branch.", "Do not revive rejected families without a new fixed hypothesis."),
    ]
    return rows


def decide_lead(inputs: dict[str, list[dict[str, Any]]], input_status: dict[str, bool]) -> tuple[str, str, str, str, str]:
    if not any(input_status.values()):
        return (
            "insufficient_saved_inputs",
            "unavailable",
            "unavailable",
            "All saved crypto research inputs are missing or empty.",
            "Regenerate the crypto research reports, then rerun this saved-output checkpoint.",
        )
    capped_label = summary_value(inputs["capped_summary"], "final_summary_label")
    best_capped = summary_metric_name(inputs["capped_summary"], "best_capped_risk_variant")
    split_counts = status_counts(inputs["capped_splits"])
    contribution_counts = status_counts(inputs["capped_contributions"])
    cost_counts = status_counts(inputs["capped_costs"])
    blockers = []
    if "split_sensitive" in split_counts:
        blockers.append("fixed split sensitivity remains")
    if "top_contributor_dependent" in contribution_counts:
        blockers.append("outlier/top-contributor dependence remains")
    if "cost_sensitive" in cost_counts:
        blockers.append("cost review remains")
    if best_capped == "unavailable" or capped_label == "insufficient_saved_inputs":
        return (
            "crypto_research_not_ready_for_lead_decision",
            "unavailable",
            "unavailable",
            "Capped-risk saved summary is missing or insufficient.",
            "Regenerate `python bot.py --crypto-equal-weight-capped-risk-report`, then rerun this checkpoint.",
        )
    if "crypto_equal_weight_ex_highest_vol_2" in best_capped and capped_label in {"crypto_capped_risk_promising", "crypto_capped_risk_concentration_improved"}:
        label = "crypto_equal_weight_ex_highest_vol_2_research_lead"
        if blockers:
            label = "crypto_research_lead_split_sensitive" if any("split" in item for item in blockers) else "crypto_research_lead_outlier_dependent"
        return (
            label,
            "crypto_equal_weight_ex_highest_vol_2",
            "active-strategy-style",
            "; ".join(blockers) or "High drawdown remains, but current saved evidence supports research-lead status only.",
            "Run a manual high-drawdown/split/outlier review before any future preview-candidate discussion.",
        )
    if "equal_weight" in best_capped:
        return (
            "crypto_equal_weight_benchmark_lead_high_drawdown",
            "equal_weight_eligible_crypto_benchmark",
            "benchmark-style",
            "Equal-weight remains the cleanest benchmark, but drawdown is severe.",
            "Keep equal-weight as benchmark lead and continue fixed outlier-dependence research.",
        )
    return (
        "manual_review_required",
        best_capped.split("=")[0] if "=" in best_capped else best_capped,
        "active-strategy-style",
        "; ".join(blockers) or "Saved evidence requires manual interpretation.",
        "Review saved full-period, split, cost, drawdown, and contribution rows manually.",
    )


def build_decision_rows(created_at: str, label: str, selected_lead: str, lead_style: str, blockers: str, next_step: str) -> list[dict[str, Any]]:
    return [
        common_row(created_at, "decision", selected_lead, "final_crypto_lead_decision_label", label, label, label, "Research lead label only; not preview promotion, crypto execution, or order instruction.", next_step),
        common_row(created_at, "decision", selected_lead, "selected_crypto_research_lead", selected_lead, label, label, f"lead_style={lead_style}; blockers={blockers}", next_step),
        common_row(created_at, "decision", selected_lead, "lead_style", lead_style, label, label, "Benchmark-style leads are comparison anchors; active-strategy-style leads are still research-only.", next_step),
    ]


def build_summary_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]], input_status: dict[str, bool], label: str, selected_lead: str, lead_style: str, blockers: str, next_step: str) -> list[dict[str, Any]]:
    capped_summary = inputs["capped_summary"]
    return [
        common_row(created_at, "summary", "final_crypto_lead_decision_label", "label", label, label, label, "Final crypto lead decision label is research-only.", next_step),
        common_row(created_at, "summary", "selected_crypto_research_lead", "lead", selected_lead, label, label, "Selected lead is not an execution candidate.", next_step),
        common_row(created_at, "summary", "lead_style", "style", lead_style, label, label, "Lead may be benchmark-style or active-strategy-style, but both remain manual-review only.", next_step),
        common_row(created_at, "summary", "full_period_evidence", "evidence", summary_value(capped_summary, "best_capped_risk_variant"), "manual_review_required", label, "Full-period evidence comes from saved capped-risk summary when available.", next_step),
        common_row(created_at, "summary", "split_evidence", "evidence", status_counts(inputs["capped_splits"]), "manual_review_required", "crypto_research_lead_split_sensitive", "Fixed split evidence comes from saved capped-risk split rows.", next_step),
        common_row(created_at, "summary", "cost_evidence", "evidence", status_counts(inputs["capped_costs"]), "manual_review_required", "crypto_research_lead_cost_review_required", "Cost evidence comes from saved capped-risk cost rows.", next_step),
        common_row(created_at, "summary", "drawdown_evidence", "evidence", status_counts(inputs["capped_drawdowns"]), "manual_review_required", label, "Drawdown evidence comes from saved capped-risk drawdown rows.", next_step),
        common_row(created_at, "summary", "outlier_contribution_evidence", "evidence", status_counts(inputs["capped_contributions"]), "manual_review_required", "crypto_research_lead_outlier_dependent", "Contribution evidence includes top-contributor and concentration diagnostics where available.", next_step),
        common_row(created_at, "summary", "rejected_family_summary", "evidence", "hard crash gates rejected for return drag; defensive throttles rejected or downgraded for return drag / weak drawdown improvement", "manual_review_required", label, "Rejected family summary is research context only.", next_step),
        common_row(created_at, "summary", "remaining_blockers", "blockers", blockers, "manual_review_required", label, "Blockers are warnings, not hidden disqualifiers or execution approvals.", next_step),
        common_row(created_at, "summary", "required_next_step", "next_step", next_step, "manual_review_required", label, "Next step must remain research/manual-review only.", next_step),
        common_row(created_at, "summary", "input_coverage", "inputs", status_counts([{"status": "present" if present else "missing"} for present in input_status.values()]), "manual_review_required", label, "Saved input coverage for the checkpoint.", next_step),
    ]


def comparison_text(summary_rows: list[dict[str, Any]]) -> str:
    return (
        f"best_capped_risk_variant={summary_value(summary_rows, 'best_capped_risk_variant')}; "
        f"static_equal_weight_result={summary_value(summary_rows, 'static_equal_weight_result')}; "
        f"drawdown_reduction_vs_equal_weight={summary_value(summary_rows, 'drawdown_reduction_vs_equal_weight')}; "
        f"return_drag_vs_equal_weight={summary_value(summary_rows, 'return_drag_vs_equal_weight')}; "
        f"calmar_improvement_vs_equal_weight={summary_value(summary_rows, 'calmar_improvement_vs_equal_weight')}"
    )


def common_row(created_at: str, section: str, strategy_name: str, metric_name: str, metric_value: Any, status: str, summary_label: str, evidence: str, required_next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "expanded_crypto_lead_decision",
        "section": section,
        "strategy_name": strategy_name,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "status": status,
        "summary_label": summary_label,
        "evidence": evidence,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("strategy_name") == key or row.get("metric_name") == key:
            return str(row.get("metric_value", "unavailable"))
    return "unavailable"


def summary_metric_name(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("strategy_name") == key:
            return str(row.get("metric_name", "unavailable"))
    return "unavailable"


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(str(row.get("status", "")) for row in rows if row)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Expanded crypto lead decision complete. Research/report only; execution_approved=False.",
        f"Final crypto lead decision label: {summary_value(summary_rows, 'final_crypto_lead_decision_label')}",
        f"Selected crypto research lead: {summary_value(summary_rows, 'selected_crypto_research_lead')}",
        f"Lead style: {summary_value(summary_rows, 'lead_style')}",
        f"Full-period evidence: {summary_value(summary_rows, 'full_period_evidence')}",
        f"Split evidence: {summary_value(summary_rows, 'split_evidence')}",
        f"Cost evidence: {summary_value(summary_rows, 'cost_evidence')}",
        f"Drawdown evidence: {summary_value(summary_rows, 'drawdown_evidence')}",
        f"Outlier/contribution evidence: {summary_value(summary_rows, 'outlier_contribution_evidence')}",
        f"Rejected family summary: {summary_value(summary_rows, 'rejected_family_summary')}",
        f"Remaining blockers: {summary_value(summary_rows, 'remaining_blockers')}",
        f"Required next step: {summary_value(summary_rows, 'required_next_step')}",
        f"Saved decision to {paths['decision']}",
        f"Saved summary to {paths['summary']}",
        f"Saved evidence to {paths['evidence']}",
        "Warning: crypto lead decision does not approve crypto execution, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMMON_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
