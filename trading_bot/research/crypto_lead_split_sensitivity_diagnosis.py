"""Saved-output split-sensitivity diagnosis for the crypto research lead.

This report diagnoses why ``crypto_equal_weight_ex_highest_vol_2`` is split
sensitive. It reads saved research CSVs where available, writes generated
diagnostic CSVs, and never touches broker, position, database, alert, config,
scheduling, or execution paths.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FOCUS_CANDIDATE = "crypto_equal_weight_ex_highest_vol_2"
COMPARE_STRATEGIES = [
    FOCUS_CANDIDATE,
    "equal_weight_eligible_crypto_benchmark",
    "equal_weight_inception_aware",
    "btc_buy_and_hold_benchmark",
    "eth_buy_and_hold_benchmark",
    "btc_eth_50_50_monthly_rebalanced_benchmark",
    "crypto_risk_on_momentum_persistence",
    "codex_ambitious_crypto_btc_eth_core_alt_accelerator",
    "cash_benchmark",
]
SPLITS = ["split_60_40", "split_70_30", "split_80_20"]
OUTLIER_SYMBOLS = ["BNB-USD", "TRX-USD"]
UNIVERSE = [
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

INPUT_FILES = {
    "lead_summary": Path("data/expanded_crypto_lead_decision_summary.csv"),
    "lead_evidence": Path("data/expanded_crypto_lead_decision_evidence.csv"),
    "capped_summary": Path("data/crypto_equal_weight_capped_risk_summary.csv"),
    "capped_splits": Path("data/crypto_equal_weight_capped_risk_splits.csv"),
    "capped_contributions": Path("data/crypto_equal_weight_capped_risk_contributions.csv"),
    "capped_equity": Path("data/crypto_equal_weight_capped_risk_equity_curves.csv"),
    "robustness_summary": Path("data/expanded_crypto_robustness_summary.csv"),
    "robustness_splits": Path("data/expanded_crypto_robustness_splits.csv"),
    "asset_contribution": Path("data/expanded_crypto_asset_contribution.csv"),
    "strategy_splits": Path("data/expanded_crypto_strategy_lab_splits.csv"),
    "universe_summary": Path("data/crypto_universe_readiness_summary.csv"),
}

OUTPUT_FILES = {
    "diagnosis": Path("data/crypto_lead_split_sensitivity_diagnosis.csv"),
    "summary": Path("data/crypto_lead_split_sensitivity_summary.csv"),
    "periods": Path("data/crypto_lead_split_sensitivity_periods.csv"),
    "exclusions": Path("data/crypto_lead_split_sensitivity_exclusions.csv"),
    "contributions": Path("data/crypto_lead_split_sensitivity_contributions.csv"),
}

DIAGNOSIS_LABELS = [
    "crypto_lead_split_sensitivity_explained",
    "crypto_lead_split_sensitive_but_still_lead",
    "crypto_lead_outlier_dependent_review",
    "crypto_lead_exclusion_rule_unstable",
    "crypto_lead_late_period_decay",
    "crypto_lead_broad_market_decay",
    "crypto_lead_not_stable_enough",
    "insufficient_saved_inputs",
    "manual_review_required",
]

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "section",
    "strategy_name",
    "period",
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
class CryptoLeadSplitSensitivityDiagnosisResult:
    diagnosis_path: Path
    summary_path: Path
    periods_path: Path
    exclusions_path: Path
    contributions_path: Path
    diagnosis_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    period_rows: list[dict[str, Any]]
    exclusion_rows: list[dict[str, Any]]
    contribution_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_lead_split_sensitivity_diagnosis(data_dir: Path | str = "data") -> CryptoLeadSplitSensitivityDiagnosisResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(data_path / path.name) for name, path in INPUT_FILES.items()}
    split_rows = build_split_rows(created_at, inputs["capped_splits"])
    period_rows = build_period_rows(created_at, inputs)
    exclusion_rows = build_exclusion_rows(created_at, inputs["capped_equity"])
    contribution_rows = build_contribution_rows(created_at, inputs["capped_contributions"], inputs["asset_contribution"])
    diagnosis_rows, summary_rows = build_diagnosis_and_summary_rows(
        created_at,
        inputs,
        split_rows,
        period_rows,
        exclusion_rows,
        contribution_rows,
    )
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["diagnosis"], diagnosis_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["periods"], period_rows)
    write_rows(output_paths["exclusions"], exclusion_rows)
    write_rows(output_paths["contributions"], contribution_rows)
    return CryptoLeadSplitSensitivityDiagnosisResult(
        diagnosis_path=output_paths["diagnosis"],
        summary_path=output_paths["summary"],
        periods_path=output_paths["periods"],
        exclusions_path=output_paths["exclusions"],
        contributions_path=output_paths["contributions"],
        diagnosis_rows=diagnosis_rows,
        summary_rows=summary_rows,
        period_rows=period_rows,
        exclusion_rows=exclusion_rows,
        contribution_rows=contribution_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_crypto_lead_split_sensitivity_diagnosis_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    diagnosis = read_csv(data_path / OUTPUT_FILES["diagnosis"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    periods = read_csv(data_path / OUTPUT_FILES["periods"].name)
    exclusions = read_csv(data_path / OUTPUT_FILES["exclusions"].name)
    contributions = read_csv(data_path / OUTPUT_FILES["contributions"].name)
    if not diagnosis or not summary:
        return 1, ["Run `python bot.py --crypto-lead-split-sensitivity-diagnosis` first."]
    approvals = {str(row.get("execution_approved", "")).lower() for row in diagnosis + summary + periods + exclusions + contributions}
    return 0, [
        "Crypto lead split-sensitivity diagnosis. Display only; execution_approved=False.",
        f"Final diagnosis label: {summary_value(summary, 'final_diagnosis_label')}",
        f"{FOCUS_CANDIDATE} remains crypto research lead: {summary_value(summary, 'lead_remains_research_lead')}",
        f"split_60_40 diagnosis: {summary_value(summary, 'split_60_40_diagnosis')}",
        f"split_70_30 diagnosis: {summary_value(summary, 'split_70_30_diagnosis')}",
        f"split_80_20 diagnosis: {summary_value(summary, 'split_80_20_diagnosis')}",
        f"Broad-market versus lead-specific weakness: {summary_value(summary, 'broad_market_vs_lead_specific_summary')}",
        f"Exclusion rule stability: {summary_value(summary, 'exclusion_rule_stability_summary')}",
        f"Top-contributor dependence: {summary_value(summary, 'top_contributor_dependence_summary')}",
        f"Required next step: {summary_value(summary, 'required_next_step')}",
        f"execution_approved values: {', '.join(sorted(approvals)) or 'false'}",
        "Warning: diagnosis is research-only and does not approve preview promotion, crypto execution, or order instructions.",
    ]


def build_split_rows(created_at: str, capped_splits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for split in SPLITS:
        source = [row for row in capped_splits if row.get("period") == split and row.get("strategy_name") in COMPARE_STRATEGIES]
        metrics = {row["strategy_name"]: parse_metrics(row.get("metric_value", "")) for row in source}
        ranks = {
            "CAGR": rank_map(metrics, "CAGR"),
            "Sharpe": rank_map(metrics, "Sharpe"),
            "Calmar": rank_map(metrics, "Calmar"),
        }
        lead = metrics.get(FOCUS_CANDIDATE, {})
        static = metrics.get("equal_weight_eligible_crypto_benchmark", {})
        btc = metrics.get("btc_buy_and_hold_benchmark", {})
        eth = metrics.get("eth_buy_and_hold_benchmark", {})
        diagnosis = split_diagnosis_label(lead, static, btc, eth, metrics)
        evidence = (
            f"lead_metrics={format_metrics(lead)}; static_metrics={format_metrics(static)}; "
            f"btc_metrics={format_metrics(btc)}; eth_metrics={format_metrics(eth)}; "
            f"lead_rank_cagr={ranks['CAGR'].get(FOCUS_CANDIDATE, 'unavailable')}; "
            f"lead_rank_sharpe={ranks['Sharpe'].get(FOCUS_CANDIDATE, 'unavailable')}; "
            f"lead_rank_calmar={ranks['Calmar'].get(FOCUS_CANDIDATE, 'unavailable')}"
        )
        rows.append(
            common_row(
                created_at,
                "split_comparison",
                FOCUS_CANDIDATE,
                split,
                "split_diagnosis",
                (
                    f"CAGR={lead.get('CAGR', 'unavailable')}; Sharpe={lead.get('Sharpe', 'unavailable')}; "
                    f"MaxDD={lead.get('MaxDD', 'unavailable')}; Calmar={lead.get('Calmar', 'unavailable')}; "
                    f"relative_rank_by_CAGR={ranks['CAGR'].get(FOCUS_CANDIDATE, 'unavailable')}; "
                    f"relative_rank_by_Sharpe={ranks['Sharpe'].get(FOCUS_CANDIDATE, 'unavailable')}; "
                    f"relative_rank_by_Calmar={ranks['Calmar'].get(FOCUS_CANDIDATE, 'unavailable')}; "
                    f"beats_static_equal_weight={beats(lead, static, 'Calmar')}; beats_BTC={beats(lead, btc, 'Calmar')}; beats_ETH={beats(lead, eth, 'Calmar')}"
                ),
                diagnosis,
                diagnosis,
                evidence,
                "Review whether split decay is broad-market or lead-specific before any future preview discussion.",
            )
        )
    return rows


def build_period_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    split_rows = [row for row in inputs["capped_splits"] if row.get("strategy_name") in COMPARE_STRATEGIES]
    split_status = status_counts(split_rows)
    broad_negative = all(
        parse_metrics(row.get("metric_value", "")).get("CAGR", 0.0) <= 0.0
        for row in split_rows
        if row.get("period") == "split_60_40" and row.get("strategy_name") in {"equal_weight_eligible_crypto_benchmark", FOCUS_CANDIDATE, "btc_buy_and_hold_benchmark", "eth_buy_and_hold_benchmark"}
    )
    period_label = "broad_crypto_market_decay" if broad_negative else "manual_review_required"
    periods = [
        ("early_period", "Saved fixed splits do not expose exact early dates; use full-period and split rank context."),
        ("middle_period", "Middle-period diagnosis is approximated from fixed split comparisons where saved rows exist."),
        ("late_period", f"Latest OOS split status counts: {split_status}."),
        ("bear_shock_drawdown_period", "Use saved capped-risk drawdown rows for shock-period context where available."),
        ("post_crash_rebound_period", "Use saved equity and split rows for rebound participation review where available."),
    ]
    return [
        common_row(created_at, "period_regime_diagnosis", FOCUS_CANDIDATE, period, "period_diagnosis", note, period_label, period_label, f"broad_crypto_market_decay={broad_negative}; split_status_counts={split_status}", "Run deeper dated regime review before making a lead replacement.")
        for period, note in periods
    ]


def build_exclusion_rows(created_at: str, equity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lead_rows = [row for row in equity_rows if row.get("strategy_name") == FOCUS_CANDIDATE and str(row.get("cost_bps")) == "10"]
    if not lead_rows:
        return [
            common_row(created_at, "exclusion_diagnosis", FOCUS_CANDIDATE, "all_periods", "exclusion_status", "missing saved equity rows", "insufficient_saved_inputs", "insufficient_saved_inputs", "Cannot infer highest-volatility exclusions without saved lead equity holdings.", "Regenerate capped-risk report before diagnosing exclusions.")
        ]
    buckets = bucket_rows(lead_rows)
    rows = []
    previous_top: tuple[str, ...] | None = None
    changed = 0
    for period, bucket in buckets.items():
        excluded_counts: Counter[str] = Counter()
        included_bnb = 0
        included_trx = 0
        for row in bucket:
            holdings = {symbol for symbol in str(row.get("reference_value", "")).split(",") if symbol}
            excluded = [symbol for symbol in UNIVERSE if symbol not in holdings]
            excluded_counts.update(excluded)
            included_bnb += int("BNB-USD" in holdings)
            included_trx += int("TRX-USD" in holdings)
        top_excluded = tuple(symbol for symbol, _count in excluded_counts.most_common(2))
        if previous_top is not None and top_excluded != previous_top:
            changed += 1
        previous_top = top_excluded
        status = "exclusion_rule_instability" if changed else "manual_review_required"
        rows.append(
            common_row(
                created_at,
                "exclusion_diagnosis",
                FOCUS_CANDIDATE,
                period,
                "highest_volatility_exclusions",
                f"most_often_excluded={','.join(top_excluded) or 'unavailable'}; BNB_inclusion_rate={rate(included_bnb, len(bucket))}; TRX_inclusion_rate={rate(included_trx, len(bucket))}",
                status,
                "crypto_lead_exclusion_rule_unstable" if status == "exclusion_rule_instability" else "manual_review_required",
                f"BNB-USD/TRX-USD inclusion is estimated from saved holdings; excluded_counts={dict(excluded_counts)}; exclusion_set_changes_so_far={changed}",
                "Review whether exclusion changes correspond to split decay.",
            )
        )
    return rows


def build_contribution_rows(created_at: str, capped_contributions: list[dict[str, Any]], asset_contributions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lead = next((row for row in capped_contributions if row.get("strategy_name") == FOCUS_CANDIDATE), None)
    if not lead:
        return [
            common_row(created_at, "contribution_diagnosis", FOCUS_CANDIDATE, "full_period", "contribution_status", "missing saved contribution rows", "insufficient_saved_inputs", "insufficient_saved_inputs", "Cannot diagnose BNB-USD/TRX-USD or top-contributor dependence without saved contribution rows.", "Regenerate capped-risk report before diagnosing contributions.")
        ]
    text = f"{lead.get('metric_value', '')}; {lead.get('evidence', '')}"
    mentions_bnb = "BNB-USD" in text
    mentions_trx = "TRX-USD" in text
    top_dependent = "top_contributor_dependent=True" in text or lead.get("status") == "top_contributor_dependent"
    status = "outlier_contributor_dependence" if top_dependent or mentions_bnb or mentions_trx else "manual_review_required"
    return [
        common_row(
            created_at,
            "contribution_diagnosis",
            FOCUS_CANDIDATE,
            "full_period",
            "top_contributor_dependence",
            lead.get("metric_value", "unavailable"),
            status,
            "crypto_lead_outlier_dependent_review" if status == "outlier_contributor_dependence" else "manual_review_required",
            f"BNB-USD mentioned={mentions_bnb}; TRX-USD mentioned={mentions_trx}; top_contributor_dependent={top_dependent}; saved_asset_contribution_rows={len(asset_contributions)}",
            "Review BNB-USD/TRX-USD and other top-contributor dependence before any lead promotion discussion.",
        )
    ]


def build_diagnosis_and_summary_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    split_rows: list[dict[str, Any]],
    period_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    contribution_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    missing_inputs = [name for name, rows in inputs.items() if not rows]
    split_labels = {row["period"]: row["summary_label"] for row in split_rows}
    broad_market = any(row.get("status") == "broad_crypto_market_decay" for row in period_rows)
    exclusion_unstable = any(row.get("status") == "exclusion_rule_instability" for row in exclusion_rows)
    outlier_dependent = any(row.get("status") == "outlier_contributor_dependence" for row in contribution_rows)
    lead_rank_good = lead_near_best(split_rows)
    if len(missing_inputs) >= len(INPUT_FILES):
        final_label = "insufficient_saved_inputs"
        lead_remains = "false"
    elif exclusion_unstable:
        final_label = "crypto_lead_exclusion_rule_unstable"
        lead_remains = "manual_review_only"
    elif outlier_dependent:
        final_label = "crypto_lead_outlier_dependent_review"
        lead_remains = "manual_review_only"
    elif broad_market:
        final_label = "crypto_lead_broad_market_decay"
        lead_remains = "true_with_split_sensitivity_warning"
    elif lead_rank_good:
        final_label = "crypto_lead_split_sensitive_but_still_lead"
        lead_remains = "true_with_split_sensitivity_warning"
    else:
        final_label = "crypto_lead_not_stable_enough"
        lead_remains = "manual_review_required"
    next_step = "Run manual split/regime and contribution review before any future preview-candidate discussion."
    summary_rows = [
        summary_row(created_at, "final_diagnosis_label", final_label, final_label, "Final diagnosis label is research-only.", next_step),
        summary_row(created_at, "lead_remains_research_lead", lead_remains, final_label, f"Focus candidate is {FOCUS_CANDIDATE}; no automatic replacement is made.", next_step),
        summary_row(created_at, "split_60_40_diagnosis", split_labels.get("split_60_40", "unavailable"), final_label, "Fixed split diagnosis from saved capped-risk split rows.", next_step),
        summary_row(created_at, "split_70_30_diagnosis", split_labels.get("split_70_30", "unavailable"), final_label, "Fixed split diagnosis from saved capped-risk split rows.", next_step),
        summary_row(created_at, "split_80_20_diagnosis", split_labels.get("split_80_20", "unavailable"), final_label, "Fixed split diagnosis from saved capped-risk split rows.", next_step),
        summary_row(created_at, "broad_market_vs_lead_specific_summary", "broad_crypto_market_decay" if broad_market else "lead_specific_or_mixed_decay_review", final_label, "Broad-market decay is flagged only when core crypto benchmarks are also weak.", next_step),
        summary_row(created_at, "exclusion_rule_stability_summary", "exclusion_rule_instability" if exclusion_unstable else "manual_review_required", final_label, "Exclusion stability is estimated from saved holdings and inferred excluded assets.", next_step),
        summary_row(created_at, "top_contributor_dependence_summary", "outlier_contributor_dependence" if outlier_dependent else "manual_review_required", final_label, "BNB-USD and TRX-USD contribution/outlier wording is checked explicitly.", next_step),
        summary_row(created_at, "required_next_step", next_step, final_label, "Diagnosis does not approve execution or preview promotion.", next_step),
        summary_row(created_at, "missing_saved_inputs", ", ".join(missing_inputs) or "none", final_label, "Missing inputs create conservative diagnosis rows rather than unclear failure.", next_step),
    ]
    diagnosis_rows = [
        common_row(created_at, "diagnosis", FOCUS_CANDIDATE, "all_splits", "final_diagnosis_label", final_label, final_label, final_label, f"lead_rank_good={lead_rank_good}; broad_market_decay={broad_market}; exclusion_rule_instability={exclusion_unstable}; outlier_contributor_dependence={outlier_dependent}; missing_inputs={missing_inputs}", next_step)
    ]
    return diagnosis_rows, summary_rows


def split_diagnosis_label(lead: dict[str, float], static: dict[str, float], btc: dict[str, float], eth: dict[str, float], metrics: dict[str, dict[str, float]]) -> str:
    if not lead:
        return "insufficient_saved_inputs"
    lead_cagr = lead.get("CAGR", 0.0)
    benchmark_cagrs = [value.get("CAGR", 0.0) for key, value in metrics.items() if key != FOCUS_CANDIDATE and key != "cash_benchmark"]
    if lead_cagr <= 0 and benchmark_cagrs and sum(value <= 0 for value in benchmark_cagrs) >= max(1, len(benchmark_cagrs) // 2):
        return "benchmark_also_weak"
    if lead_cagr <= 0 and static.get("CAGR", 0.0) > 0:
        return "late_period_underperformance"
    if beats(lead, static, "Calmar") or beats(lead, btc, "Calmar") or beats(lead, eth, "Calmar"):
        return "crypto_lead_split_sensitive_but_still_lead"
    return "manual_review_required"


def rank_map(metrics: dict[str, dict[str, float]], metric: str) -> dict[str, int]:
    ranked = sorted(((values.get(metric, -999999.0), strategy) for strategy, values in metrics.items()), reverse=True)
    return {strategy: index + 1 for index, (_value, strategy) in enumerate(ranked)}


def lead_near_best(split_rows: list[dict[str, Any]]) -> bool:
    count = 0
    for row in split_rows:
        value = str(row.get("metric_value", ""))
        rank_text = "relative_rank_by_Calmar="
        if rank_text in value:
            rank = value.split(rank_text, 1)[1].split(";", 1)[0].strip()
            try:
                count += int(rank) <= 3
            except ValueError:
                pass
    return count >= 2


def bucket_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows = sorted(rows, key=lambda row: row.get("period", ""))
    if not rows:
        return {}
    n = len(rows)
    return {
        "early_period": rows[: max(1, n // 3)],
        "middle_period": rows[max(1, n // 3) : max(2, 2 * n // 3)],
        "late_period": rows[max(2, 2 * n // 3) :],
    }


def parse_metrics(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for part in str(text).split(";"):
        if "=" not in part:
            continue
        key, value = [item.strip() for item in part.split("=", 1)]
        try:
            values[key] = float(value)
        except ValueError:
            continue
    return values


def format_metrics(metrics: dict[str, float]) -> str:
    return ", ".join(f"{key}={value}" for key, value in metrics.items()) or "unavailable"


def beats(left: dict[str, float], right: dict[str, float], metric: str) -> str:
    if metric not in left or metric not in right:
        return "unavailable"
    return str(left[metric] > right[metric])


def rate(count: int, total: int) -> str:
    return "unavailable" if total <= 0 else str(round(count / total * 100, 4))


def summary_row(created_at: str, metric_name: str, metric_value: str, label: str, evidence: str, next_step: str) -> dict[str, Any]:
    return common_row(created_at, "summary", metric_name, "", metric_name, metric_value, "manual_review_required", label, evidence, next_step)


def common_row(created_at: str, section: str, strategy_name: str, period: str, metric_name: str, metric_value: Any, status: str, summary_label: str, evidence: str, required_next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "crypto_lead_split_sensitivity_diagnosis",
        "section": section,
        "strategy_name": strategy_name,
        "period": period,
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


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(str(row.get("status", "")) for row in rows if row)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Crypto lead split-sensitivity diagnosis complete. Research/report only; execution_approved=False.",
        f"Final diagnosis label: {summary_value(summary_rows, 'final_diagnosis_label')}",
        f"{FOCUS_CANDIDATE} remains crypto research lead: {summary_value(summary_rows, 'lead_remains_research_lead')}",
        f"split_60_40 diagnosis: {summary_value(summary_rows, 'split_60_40_diagnosis')}",
        f"split_70_30 diagnosis: {summary_value(summary_rows, 'split_70_30_diagnosis')}",
        f"split_80_20 diagnosis: {summary_value(summary_rows, 'split_80_20_diagnosis')}",
        f"Broad-market versus lead-specific weakness: {summary_value(summary_rows, 'broad_market_vs_lead_specific_summary')}",
        f"Exclusion rule stability: {summary_value(summary_rows, 'exclusion_rule_stability_summary')}",
        f"Top-contributor dependence: {summary_value(summary_rows, 'top_contributor_dependence_summary')}",
        f"Required next step: {summary_value(summary_rows, 'required_next_step')}",
        f"Saved diagnosis to {paths['diagnosis']}",
        f"Saved summary to {paths['summary']}",
        f"Saved periods to {paths['periods']}",
        f"Saved exclusions to {paths['exclusions']}",
        f"Saved contributions to {paths['contributions']}",
        "Warning: diagnosis does not approve crypto execution, preview promotion, scheduling, or strategy-to-execution wiring.",
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
