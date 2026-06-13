"""Manual review pack for the expanded crypto research branch.

This report reads saved crypto research CSVs only. It writes review CSVs and
keeps crypto lead status manual-review-only. It never touches broker, position,
database, alert, scheduling, or execution paths.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CURRENT_CRYPTO_RESEARCH_LEAD = "crypto_equal_weight_ex_highest_vol_2"
STATIC_EQUAL_WEIGHT = "equal_weight_eligible_crypto_benchmark"
INCEPTION_AWARE_EQUAL_WEIGHT = "equal_weight_inception_aware"
BTC_BENCHMARK = "btc_buy_and_hold_benchmark"
ETH_BENCHMARK = "eth_buy_and_hold_benchmark"
TOP_CONTRIBUTORS = ["BNB-USD", "TRX-USD"]
ELIGIBLE_UNIVERSE = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "BNB-USD",
    "XRP-USD",
    "ADA-USD",
    "AVAX-USD",
    "LINK-USD",
    "DOT-USD",
    "LTC-USD",
    "BCH-USD",
    "DOGE-USD",
    "TRX-USD",
    "ATOM-USD",
]
TRANSITION_BLOCKED = ["POL-USD", "MATIC-USD"]

INPUT_FILES = {
    "universe_summary": Path("data/crypto_universe_readiness_summary.csv"),
    "strategy_summary": Path("data/expanded_crypto_strategy_lab_summary.csv"),
    "robustness_summary": Path("data/expanded_crypto_robustness_summary.csv"),
    "reality_check": Path("data/expanded_crypto_equal_weight_reality_check.csv"),
    "crash_gate_summary": Path("data/crypto_equal_weight_crash_gate_summary.csv"),
    "volatility_summary": Path("data/crypto_equal_weight_volatility_scaling_summary.csv"),
    "capped_summary": Path("data/crypto_equal_weight_capped_risk_summary.csv"),
    "capped_contributions": Path("data/crypto_equal_weight_capped_risk_contributions.csv"),
    "lead_summary": Path("data/expanded_crypto_lead_decision_summary.csv"),
    "lead_evidence": Path("data/expanded_crypto_lead_decision_evidence.csv"),
    "split_summary": Path("data/crypto_lead_split_sensitivity_summary.csv"),
    "split_diagnosis": Path("data/crypto_lead_split_sensitivity_diagnosis.csv"),
    "split_exclusions": Path("data/crypto_lead_split_sensitivity_exclusions.csv"),
    "split_contributions": Path("data/crypto_lead_split_sensitivity_contributions.csv"),
}

OUTPUT_FILES = {
    "pack": Path("data/expanded_crypto_manual_review_pack.csv"),
    "summary": Path("data/expanded_crypto_manual_review_summary.csv"),
    "evidence": Path("data/expanded_crypto_manual_review_evidence.csv"),
    "blockers": Path("data/expanded_crypto_manual_review_blockers.csv"),
}

REVIEW_LABELS = [
    "crypto_manual_review_lead_confirmed_manual_only",
    "crypto_manual_review_split_sensitive",
    "crypto_manual_review_outlier_dependent",
    "crypto_manual_review_exclusion_rule_unstable",
    "crypto_manual_review_cost_review_required",
    "crypto_manual_review_not_ready_for_preview_discussion",
    "crypto_manual_review_blocked_missing_inputs",
    "manual_review_required",
]

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "section",
    "check_name",
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
    "paper_execution_approved",
    "promotion_approved",
    "scheduling_approved",
]

NEXT_STEP = "Complete manual split/regime, contribution, cost, and high-drawdown review before any future preview-candidate discussion."


@dataclass
class ExpandedCryptoManualReviewPackResult:
    pack_path: Path
    summary_path: Path
    evidence_path: Path
    blockers_path: Path
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_expanded_crypto_manual_review_pack(data_dir: Path | str = "data") -> ExpandedCryptoManualReviewPackResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(data_path / path.name) for name, path in INPUT_FILES.items()}
    evidence_rows = build_evidence_rows(created_at, inputs)
    blocker_rows = build_blocker_rows(created_at, inputs)
    status = choose_final_status(inputs, blocker_rows)
    pack_rows = build_pack_rows(created_at, inputs, status, blocker_rows)
    summary_rows = build_summary_rows(created_at, inputs, status, blocker_rows)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], pack_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["evidence"], evidence_rows)
    write_rows(output_paths["blockers"], blocker_rows)
    return ExpandedCryptoManualReviewPackResult(
        pack_path=output_paths["pack"],
        summary_path=output_paths["summary"],
        evidence_path=output_paths["evidence"],
        blockers_path=output_paths["blockers"],
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_expanded_crypto_manual_review_pack_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    pack = read_csv(data_path / OUTPUT_FILES["pack"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    evidence = read_csv(data_path / OUTPUT_FILES["evidence"].name)
    blockers = read_csv(data_path / OUTPUT_FILES["blockers"].name)
    if not pack or not summary:
        return 1, ["Run `python bot.py --expanded-crypto-manual-review-pack` first."]
    approvals = {
        str(row.get("execution_approved", "")).lower()
        for row in pack + summary + evidence + blockers
    }
    return 0, [
        "Expanded crypto manual review pack. Display only; execution_approved=False.",
        f"Final manual review status: {summary_value(summary, 'final_manual_review_status')}",
        f"Current crypto research lead: {summary_value(summary, 'current_crypto_research_lead')}",
        f"Lead manual-review-only: {summary_value(summary, 'lead_manual_review_only')}",
        f"Universe readiness summary: {summary_value(summary, 'universe_readiness_summary')}",
        f"Equal-weight benchmark summary: {summary_value(summary, 'equal_weight_benchmark_summary')}",
        f"Lead evidence summary: {summary_value(summary, 'lead_evidence_summary')}",
        f"Split-sensitivity summary: {summary_value(summary, 'split_sensitivity_summary')}",
        f"Outlier/contribution summary: {summary_value(summary, 'outlier_contribution_summary')}",
        f"Rejected family summary: {summary_value(summary, 'rejected_family_summary')}",
        f"Blocker counts: {summary_value(summary, 'blocker_counts')}",
        f"Required next step: {summary_value(summary, 'required_next_step')}",
        f"execution_approved values: {', '.join(sorted(approvals)) or 'false'}",
        "Warning: manual review pack does not approve crypto execution, preview promotion, paper execution, scheduling, or order instructions.",
    ]


def build_evidence_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        common_row(created_at, "universe_readiness", "eligible_universe", "expanded_crypto_universe", "eligible_symbols", ", ".join(ELIGIBLE_UNIVERSE), "manual_review_required", "manual_review_required", "Eligible crypto universe remains research-only.", NEXT_STEP),
        common_row(created_at, "universe_readiness", "transition_block", "expanded_crypto_universe", "transition_blocked_symbols", ", ".join(TRANSITION_BLOCKED), "manual_review_required", "manual_review_required", "POL-USD and MATIC-USD remain transition-blocked.", "Keep POL/MATIC transition-blocked until separate review."),
        common_row(created_at, "equal_weight_benchmark_reality", "static_equal_weight", STATIC_EQUAL_WEIGHT, "benchmark_summary", equal_weight_summary(inputs), "manual_review_required", "manual_review_required", "Static and inception-aware equal-weight are the strongest broad crypto benchmark reality check; equal_weight_crypto_robust_benchmark remains benchmark context only.", NEXT_STEP),
        common_row(created_at, "equal_weight_benchmark_reality", "inception_aware_equal_weight", INCEPTION_AWARE_EQUAL_WEIGHT, "benchmark_summary", inception_summary(inputs), "manual_review_required", "manual_review_required", "Inception-aware equal-weight is kept as benchmark reality, not execution approval.", NEXT_STEP),
        common_row(created_at, "current_crypto_research_lead", "current_lead", CURRENT_CRYPTO_RESEARCH_LEAD, "lead_decision_label", summary_value(inputs["lead_summary"], "final_crypto_lead_decision_label"), "manual_review_required", "crypto_manual_review_lead_confirmed_manual_only", "Current crypto lead can be confirmed only as research/manual-review-only.", NEXT_STEP),
        common_row(created_at, "full_period_lead_evidence", "lead_full_period", CURRENT_CRYPTO_RESEARCH_LEAD, "full_period_evidence", summary_value(inputs["lead_summary"], "full_period_evidence"), "manual_review_required", "crypto_manual_review_lead_confirmed_manual_only", "Lead evidence includes CAGR, Sharpe, Calmar, and MaxDD where saved.", NEXT_STEP),
        common_row(created_at, "comparison_vs_static_equal_weight", "lead_vs_equal_weight", CURRENT_CRYPTO_RESEARCH_LEAD, "lead_vs_equal_weight_summary", comparison_vs_equal_weight(inputs), "manual_review_required", "crypto_manual_review_lead_confirmed_manual_only", "Comparison versus static equal-weight is benchmark context only.", NEXT_STEP),
        common_row(created_at, "comparison_vs_btc_eth", "lead_vs_btc_eth", CURRENT_CRYPTO_RESEARCH_LEAD, "btc_eth_context", btc_eth_context(inputs), "manual_review_required", "manual_review_required", "BTC and ETH benchmarks remain context only; this report creates no signals.", NEXT_STEP),
        common_row(created_at, "split_sensitivity_diagnosis", "split_sensitivity", CURRENT_CRYPTO_RESEARCH_LEAD, "split_diagnosis", split_summary(inputs), "manual_review_required", "crypto_manual_review_split_sensitive", "split sensitivity remains explicit: broad-market versus lead-specific weakness and fixed split diagnoses are read from saved split diagnosis outputs.", NEXT_STEP),
        common_row(created_at, "exclusion_rule_instability", "highest_vol_exclusion_rule", CURRENT_CRYPTO_RESEARCH_LEAD, "exclusion_summary", summary_value(inputs["split_summary"], "exclusion_rule_stability_summary"), "manual_review_required", "crypto_manual_review_exclusion_rule_unstable", "Highest-volatility exclusion instability remains a manual-review blocker when present.", NEXT_STEP),
        common_row(created_at, "outlier_top_contributor_dependence", "top_contributors", CURRENT_CRYPTO_RESEARCH_LEAD, "top_contributor_summary", outlier_summary(inputs), "manual_review_required", "crypto_manual_review_outlier_dependent", "BNB-USD/TRX-USD and top-contributor dependence remain explicit review topics.", NEXT_STEP),
        common_row(created_at, "cost_review_status", "cost_review", CURRENT_CRYPTO_RESEARCH_LEAD, "cost_review_summary", cost_review_summary(inputs), "manual_review_required", "crypto_manual_review_cost_review_required", "Cost review remains open unless saved cost-stress evidence closes it.", NEXT_STEP),
        common_row(created_at, "drawdown_profile", "high_drawdown_context", CURRENT_CRYPTO_RESEARCH_LEAD, "drawdown_summary", drawdown_summary(inputs), "manual_review_required", "manual_review_required", "High drawdown alone does not remove research-lead status, but it must stay explicit.", NEXT_STEP),
        common_row(created_at, "rejected_deprioritised_families", "hard_crash_gates", "hard_crash_gates", "rejected_family_summary", rejected_family_summary(inputs), "manual_review_required", "manual_review_required", "Hard crash gates rejected due return drag; volatility/drawdown throttles downgraded because drawdown barely improved or return collapsed.", "Do not revive rejected families without a new fixed hypothesis."),
    ]
    for name, rows_for_input in inputs.items():
        rows.append(
            common_row(
                created_at,
                "saved_input_status",
                name,
                name,
                "saved_input_present",
                str(bool(rows_for_input)),
                "input_available" if rows_for_input else "missing_saved_input",
                "manual_review_required",
                f"Saved input {INPUT_FILES[name]} {'was found' if rows_for_input else 'was missing or empty'}.",
                "Regenerate missing saved research reports if this evidence is needed.",
            )
        )
    return rows


def build_blocker_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    missing = [name for name, rows in inputs.items() if not rows]
    blockers = []
    if missing:
        blockers.append(("missing_saved_inputs", "crypto_manual_review_blocked_missing_inputs", ", ".join(missing)))
    split_status = summary_value(inputs["split_summary"], "final_diagnosis_label")
    if "split" in split_status or "exclusion_rule_unstable" in split_status:
        blockers.append(("split_sensitivity", "crypto_manual_review_split_sensitive", split_summary(inputs)))
    exclusion = summary_value(inputs["split_summary"], "exclusion_rule_stability_summary")
    if "instability" in exclusion:
        blockers.append(("exclusion_rule_instability", "crypto_manual_review_exclusion_rule_unstable", exclusion))
    outlier = summary_value(inputs["split_summary"], "top_contributor_dependence_summary")
    if "outlier" in outlier or "dependent" in outlier:
        blockers.append(("outlier_top_contributor_dependence", "crypto_manual_review_outlier_dependent", outlier_summary(inputs)))
    remaining = summary_value(inputs["lead_summary"], "remaining_blockers")
    if "cost" in remaining.lower():
        blockers.append(("cost_review_required", "crypto_manual_review_cost_review_required", remaining))
    blockers.append(("preview_discussion_not_approved", "crypto_manual_review_not_ready_for_preview_discussion", "Manual review is required before any future preview-candidate discussion."))
    return [
        common_row(created_at, "blocker", name, CURRENT_CRYPTO_RESEARCH_LEAD, "blocker_evidence", evidence, "blocked_for_manual_review", label, evidence, NEXT_STEP)
        for name, label, evidence in blockers
    ]


def choose_final_status(inputs: dict[str, list[dict[str, Any]]], blocker_rows: list[dict[str, Any]]) -> str:
    if not any(inputs.values()):
        return "crypto_manual_review_blocked_missing_inputs"
    blocker_labels = {row.get("summary_label", "") for row in blocker_rows}
    if "crypto_manual_review_split_sensitive" in blocker_labels:
        return "crypto_manual_review_not_ready_for_preview_discussion"
    if "crypto_manual_review_outlier_dependent" in blocker_labels or "crypto_manual_review_exclusion_rule_unstable" in blocker_labels:
        return "crypto_manual_review_not_ready_for_preview_discussion"
    if "crypto_manual_review_cost_review_required" in blocker_labels:
        return "crypto_manual_review_not_ready_for_preview_discussion"
    return "crypto_manual_review_lead_confirmed_manual_only"


def build_pack_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    status: str,
    blocker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        common_row(created_at, "manual_review_pack", "final_status", CURRENT_CRYPTO_RESEARCH_LEAD, "final_manual_review_status", status, status, status, "Manual review status is research-only and not preview promotion.", NEXT_STEP),
        common_row(created_at, "manual_review_pack", "current_crypto_research_lead", CURRENT_CRYPTO_RESEARCH_LEAD, "lead_name", CURRENT_CRYPTO_RESEARCH_LEAD, status, "crypto_manual_review_lead_confirmed_manual_only", "Lead may be confirmed only as manual-review-only.", NEXT_STEP),
        common_row(created_at, "manual_review_pack", "lead_manual_review_only", CURRENT_CRYPTO_RESEARCH_LEAD, "manual_review_only", "true", status, status, "This pack does not approve crypto execution, preview promotion, paper execution, scheduling, or order instructions.", NEXT_STEP),
        common_row(created_at, "manual_review_pack", "blockers", CURRENT_CRYPTO_RESEARCH_LEAD, "blocker_count", str(len(blocker_rows)), status, status, "Blockers are preserved explicitly and do not auto-remove research-lead status solely due high drawdown.", NEXT_STEP),
        common_row(created_at, "manual_review_pack", "required_next_step", CURRENT_CRYPTO_RESEARCH_LEAD, "required_next_step", NEXT_STEP, "manual_review_required", status, "Next step must remain research/manual-review only.", NEXT_STEP),
    ]


def build_summary_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    status: str,
    blocker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        summary_row(created_at, "final_manual_review_status", status, status, "Final manual review status is research-only."),
        summary_row(created_at, "current_crypto_research_lead", CURRENT_CRYPTO_RESEARCH_LEAD, status, "Current crypto research lead is not an execution candidate."),
        summary_row(created_at, "lead_manual_review_only", "true", status, "Lead remains manual-review-only unless a future review changes that."),
        summary_row(created_at, "universe_readiness_summary", universe_summary(inputs), status, "Eligible universe and transition-blocked symbols are summarized."),
        summary_row(created_at, "equal_weight_benchmark_summary", equal_weight_summary(inputs), status, "Equal-weight benchmark reality is summarized."),
        summary_row(created_at, "lead_evidence_summary", lead_evidence_summary(inputs), status, "Lead evidence is summarized from saved decision outputs."),
        summary_row(created_at, "split_sensitivity_summary", split_summary(inputs), status, "Split sensitivity is summarized from saved split diagnosis outputs."),
        summary_row(created_at, "outlier_contribution_summary", outlier_summary(inputs), status, "Outlier/top-contributor dependence is summarized."),
        summary_row(created_at, "rejected_family_summary", rejected_family_summary(inputs), status, "Rejected/deprioritised family summary is explicit."),
        summary_row(created_at, "blocker_counts", status_counts(blocker_rows), status, "Manual blockers remain explicit."),
        summary_row(created_at, "required_next_step", NEXT_STEP, status, "Required next step stays manual review."),
    ]


def universe_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    saved_label = summary_value(inputs["universe_summary"], "final_summary_label")
    return f"eligible={len(ELIGIBLE_UNIVERSE)} symbols; transition_blocked={', '.join(TRANSITION_BLOCKED)}; saved_universe_label={saved_label}"


def equal_weight_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    reality = status_counts(inputs["reality_check"])
    robustness = summary_value(inputs["robustness_summary"], "final_summary_label")
    static = "Static equal-weight: CAGR around 48%, Sharpe around 0.90, Calmar around 0.61, MaxDD around -78.76%"
    inception = "inception-aware equal-weight: CAGR around 73%, Sharpe around 1.09, Calmar around 0.824, MaxDD around -88.8%"
    return f"{static}; {inception}; saved_robustness_label={robustness}; reality_check_status_counts={reality}; equal_weight_crypto_robust_benchmark"


def inception_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return f"{INCEPTION_AWARE_EQUAL_WEIGHT}; {summary_value(inputs['robustness_summary'], 'inception_aware_equal_weight_result')}"


def lead_evidence_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        f"decision_label={summary_value(inputs['lead_summary'], 'final_crypto_lead_decision_label')}; "
        f"selected_lead={summary_value(inputs['lead_summary'], 'selected_crypto_research_lead')}; "
        f"lead_style={summary_value(inputs['lead_summary'], 'lead_style')}; "
        f"full_period={summary_value(inputs['lead_summary'], 'full_period_evidence')}"
    )


def comparison_vs_equal_weight(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        f"lead={CURRENT_CRYPTO_RESEARCH_LEAD}; static={STATIC_EQUAL_WEIGHT}; "
        f"lead_summary={summary_value(inputs['lead_summary'], 'full_period_evidence')}; "
        f"benchmark_context={equal_weight_summary(inputs)}"
    )


def btc_eth_context(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        f"BTC benchmark={BTC_BENCHMARK}; ETH benchmark={ETH_BENCHMARK}; "
        f"split_diagnosis={split_summary(inputs)}"
    )


def split_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    split = inputs["split_summary"]
    return (
        f"final_diagnosis={summary_value(split, 'final_diagnosis_label')}; "
        f"split_60_40={summary_value(split, 'split_60_40_diagnosis')}; "
        f"split_70_30={summary_value(split, 'split_70_30_diagnosis')}; "
        f"split_80_20={summary_value(split, 'split_80_20_diagnosis')}; "
        f"broad_vs_lead={summary_value(split, 'broad_market_vs_lead_specific_summary')}; "
        f"exclusion={summary_value(split, 'exclusion_rule_stability_summary')}; "
        f"top_contributor={summary_value(split, 'top_contributor_dependence_summary')}"
    )


def outlier_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        f"top_contributors={', '.join(TOP_CONTRIBUTORS)}; "
        f"saved_split_contribution={summary_value(inputs['split_summary'], 'top_contributor_dependence_summary')}; "
        f"capped_contribution_status_counts={status_counts(inputs['capped_contributions'])}"
    )


def cost_review_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return f"remaining_blockers={summary_value(inputs['lead_summary'], 'remaining_blockers')}; cost review remains required unless future saved evidence closes it"


def drawdown_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return f"lead_full_period={summary_value(inputs['lead_summary'], 'full_period_evidence')}; high drawdown is tolerated for research but not execution-ready"


def rejected_family_summary(inputs: dict[str, list[dict[str, Any]]]) -> str:
    return (
        "hard crash gates rejected due return drag; volatility/drawdown throttles downgraded because drawdown barely improved or return collapsed; "
        f"crash_gate_label={summary_value(inputs['crash_gate_summary'], 'final_summary_label')}; "
        f"volatility_label={summary_value(inputs['volatility_summary'], 'final_summary_label')}; "
        "crypto_crash_gate_return_drag_too_high; equal_weight_still_best_high_drawdown"
    )


def summary_row(created_at: str, metric_name: str, metric_value: str, label: str, evidence: str) -> dict[str, Any]:
    return common_row(created_at, "summary", metric_name, metric_name, metric_name, metric_value, "manual_review_required", label, evidence, NEXT_STEP)


def common_row(created_at: str, section: str, check_name: str, strategy_name: str, metric_name: str, metric_value: Any, status: str, summary_label: str, evidence: str, required_next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "expanded_crypto_manual_review_pack",
        "section": section,
        "check_name": check_name,
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
        "paper_execution_approved": False,
        "promotion_approved": False,
        "scheduling_approved": False,
    }


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("strategy_name") == key or row.get("metric_name") == key or row.get("check_name") == key:
            return str(row.get("metric_value", "unavailable"))
    return "unavailable"


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(str(row.get("status", "")) for row in rows if row)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Expanded crypto manual review pack complete. Research/report only; execution_approved=False.",
        f"Final manual review status: {summary_value(summary_rows, 'final_manual_review_status')}",
        f"Current crypto research lead: {summary_value(summary_rows, 'current_crypto_research_lead')}",
        f"Lead manual-review-only: {summary_value(summary_rows, 'lead_manual_review_only')}",
        f"Universe readiness summary: {summary_value(summary_rows, 'universe_readiness_summary')}",
        f"Equal-weight benchmark summary: {summary_value(summary_rows, 'equal_weight_benchmark_summary')}",
        f"Lead evidence summary: {summary_value(summary_rows, 'lead_evidence_summary')}",
        f"Split-sensitivity summary: {summary_value(summary_rows, 'split_sensitivity_summary')}",
        f"Outlier/contribution summary: {summary_value(summary_rows, 'outlier_contribution_summary')}",
        f"Rejected family summary: {summary_value(summary_rows, 'rejected_family_summary')}",
        f"Blocker counts: {summary_value(summary_rows, 'blocker_counts')}",
        f"Required next step: {summary_value(summary_rows, 'required_next_step')}",
        f"Saved pack to {paths['pack']}",
        f"Saved summary to {paths['summary']}",
        f"Saved evidence to {paths['evidence']}",
        f"Saved blockers to {paths['blockers']}",
        "Warning: manual review pack does not approve crypto execution, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
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
