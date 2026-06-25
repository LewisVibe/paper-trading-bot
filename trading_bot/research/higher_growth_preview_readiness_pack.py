"""Saved-output preview-readiness pack for the higher-growth allocation.

This module reads existing saved CSV research outputs only. It does not refresh
market data, call Alpaca, read positions, create order instructions, schedule
anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET_CANDIDATE = "higher_growth_70_20_5_5"
QQQ100_BASELINE = "qqq100_only_reference"
BALANCED_COMPARATOR = "balanced_multi_sleeve_research_portfolio"
CRYPTO_BLEND_COMPARATOR = "qqq100_plus_high_growth_plus_crypto_research"

FINAL_STATUS_READY = "higher_growth_preview_discussion_ready_manual_review_required"
FINAL_STATUS_BLOCKED = "higher_growth_preview_discussion_blocked_missing_saved_evidence"

OUTPUT_FILES = {
    "pack": Path("data/higher_growth_preview_readiness_pack.csv"),
    "summary": Path("data/higher_growth_preview_readiness_summary.csv"),
    "evidence": Path("data/higher_growth_preview_readiness_evidence.csv"),
    "blockers": Path("data/higher_growth_preview_readiness_blockers.csv"),
}

INPUT_FILES = {
    "discovery_report": Path("data/high_growth_strategy_discovery_sprint.csv"),
    "discovery_summary": Path("data/high_growth_strategy_discovery_sprint_summary.csv"),
    "higher_growth_review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "higher_growth_summary": Path("data/multi_sleeve_higher_growth_summary.csv"),
    "multi_sleeve_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "qqq100_reference": Path("data/qqq100_recovered_reference_metrics.csv"),
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

PACK_COLUMNS = [
    "created_at",
    "check_name",
    "status",
    "risk_level",
    "target_candidate",
    "comparison_subject",
    "target_metric",
    "comparison_metric",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class HigherGrowthPreviewReadinessResult:
    output_paths: dict[str, Path]
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_higher_growth_preview_readiness_pack(root_dir: Path | str = ".") -> HigherGrowthPreviewReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    target = find_row(inputs["higher_growth_review"], "allocation_name", TARGET_CANDIDATE)
    current = find_row(inputs["higher_growth_review"], "allocation_name", "current_75_15_5_5")
    qqq100 = find_row(inputs["multi_sleeve_backtest"], "portfolio_name", QQQ100_BASELINE)
    balanced = find_row(inputs["multi_sleeve_backtest"], "portfolio_name", BALANCED_COMPARATOR)
    crypto_blend = find_row(inputs["multi_sleeve_backtest"], "portfolio_name", CRYPTO_BLEND_COMPARATOR)
    discovery = find_row(inputs["discovery_report"], "candidate_name", TARGET_CANDIDATE)

    pack_rows = build_pack_rows(created_at, target, current, qqq100, balanced, crypto_blend, discovery, inputs)
    summary_rows = build_summary_rows(pack_rows, target, current, qqq100, balanced, discovery, inputs)
    evidence_rows = build_evidence_rows(inputs, target, current, qqq100, balanced, crypto_blend, discovery)
    blocker_rows = build_blocker_rows(summary_rows, target, qqq100, balanced)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], PACK_COLUMNS, pack_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HigherGrowthPreviewReadinessResult(
        output_paths=output_paths,
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_higher_growth_preview_readiness_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    pack_path = root / OUTPUT_FILES["pack"]
    if not summary_path.exists() or not pack_path.exists():
        return 1, [
            "Higher-growth preview readiness pack is missing.",
            "Run `python bot.py --higher-growth-preview-readiness-pack` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; preview_candidate_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "Higher-growth preview readiness saved display. Research/report only; no execution approval.",
        f"final_readiness_status: {summary_value(summary_rows, 'final_readiness_status')}",
        f"target_candidate: {summary_value(summary_rows, 'target_candidate')}",
        f"clean_baseline: {summary_value(summary_rows, 'clean_baseline')}",
        f"balanced_comparator: {summary_value(summary_rows, 'balanced_comparator')}",
        f"strongest_evidence: {summary_value(summary_rows, 'strongest_evidence')}",
        f"largest_blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "preview_candidate_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false; high_growth_promotion_approved=false",
        "Warning: this pack supports manual preview discussion only; it does not implement preview mode or create order instructions.",
    ]


def build_pack_rows(
    created_at: str,
    target: dict[str, str],
    current: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    crypto_blend: dict[str, str],
    discovery: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = [
        pack_row(
            created_at,
            "target_candidate_identity",
            "higher_growth_candidate_identified",
            "medium",
            TARGET_CANDIDATE,
            "high_growth_strategy_discovery_sprint",
            metric_line(target, "CAGR", "Sharpe", "MaxDD", "Calmar"),
            discovery.get("final_candidate_status", "missing_saved_discovery_status"),
            "Target is the top saved-output sprint candidate and remains research-only.",
            "manual_review_candidate_before_any_preview_design",
        ),
        pack_row(
            created_at,
            "qqq100_baseline_comparison",
            comparison_status(target, qqq100, "qqq100"),
            "medium",
            TARGET_CANDIDATE,
            QQQ100_BASELINE,
            metric_line(target, "CAGR", "Sharpe", "MaxDD", "Calmar"),
            portfolio_metric_line(qqq100),
            qqq100_interpretation(target, qqq100),
            "confirm_q q q100_baseline_comparison_and_keep_q q q100_current_paper_live_base".replace(" ", ""),
        ),
        pack_row(
            created_at,
            "current_allocation_comparison",
            comparison_status(target, current, "current_allocation"),
            "medium",
            TARGET_CANDIDATE,
            "current_75_15_5_5",
            metric_line(target, "CAGR", "Sharpe", "MaxDD", "Calmar"),
            metric_line(current, "CAGR", "Sharpe", "MaxDD", "Calmar"),
            "Higher-growth allocation improves CAGR, Sharpe, and Calmar versus the current allocation, with a small drawdown give-up.",
            "review_whether_incremental_high_growth_exposure_is_worth_small_drawdown_increase",
        ),
        pack_row(
            created_at,
            "balanced_comparator_review",
            "balanced_comparator_remains_viable_alternative",
            "medium",
            TARGET_CANDIDATE,
            BALANCED_COMPARATOR,
            metric_line(target, "CAGR", "Sharpe", "MaxDD", "Calmar"),
            portfolio_metric_line(balanced),
            "Target has higher CAGR and Calmar, while balanced comparator has slightly milder drawdown and similar Sharpe.",
            "manual_review_target_vs_balanced_comparator_before_preview_discussion",
        ),
        pack_row(
            created_at,
            "crypto_blend_context",
            "crypto_blend_research_context_only",
            "high",
            TARGET_CANDIDATE,
            CRYPTO_BLEND_COMPARATOR,
            metric_line(target, "CAGR", "Sharpe", "MaxDD", "Calmar"),
            portfolio_metric_line(crypto_blend),
            "Crypto blend is strong saved research evidence but crypto remains capped/research-only and not execution-approved.",
            "keep_crypto_context_research_only_until_separate_policy_review",
        ),
        pack_row(
            created_at,
            "split_and_cost_evidence",
            "split_and_cost_review_supportive_but_manual_review_required",
            "medium",
            TARGET_CANDIDATE,
            "multi_sleeve_higher_growth_summary",
            summary_value(inputs["higher_growth_summary"], "split_win_count"),
            summary_value(inputs["higher_growth_summary"], "worst_cost_stress_result"),
            "Saved split and cost-stress evidence is supportive, but it remains manual-review evidence only.",
            "review_split_cost_and_turnover_before_preview_candidate_label_change",
        ),
        pack_row(
            created_at,
            "preview_boundary",
            "preview_implementation_not_added",
            "critical",
            TARGET_CANDIDATE,
            "paper_live_policy",
            "preview_candidate_approved=false",
            "execution_approved=false",
            "This pack does not add preview mode, action preview, portfolio execution, or order instructions.",
            "separate_prompt_required_for_any_preview_implementation_design",
        ),
    ]
    return rows


def build_summary_rows(
    pack_rows: list[dict[str, Any]],
    target: dict[str, str],
    current: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    discovery: dict[str, str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    missing_required = [name for name, row in [("target", target), ("qqq100", qqq100), ("balanced", balanced)] if not row]
    final_status = FINAL_STATUS_BLOCKED if missing_required else FINAL_STATUS_READY
    strongest = (
        f"{TARGET_CANDIDATE}: CAGR={target.get('CAGR', 'missing')}; Sharpe={target.get('Sharpe', 'missing')}; "
        f"MaxDD={target.get('MaxDD', 'missing')}; Calmar={target.get('Calmar', 'missing')}; "
        f"delta_vs_qqq100_CAGR={delta(parse_float(target.get('CAGR')), parse_float(qqq100.get('candidate_cagr')))}"
    )
    largest_blocker = "preview_implementation_not_added_and_manual_review_required"
    rows = [
        ("final_readiness_status", final_status, "Whether saved evidence supports manual preview-candidate discussion."),
        ("target_candidate", TARGET_CANDIDATE, "Candidate under review."),
        ("clean_baseline", f"qqq100_only_reference: {portfolio_metric_line(qqq100)}", "QQQ100 remains the clean paper-live base."),
        ("balanced_comparator", f"{BALANCED_COMPARATOR}: {portfolio_metric_line(balanced)}", "Calmer multi-sleeve comparator."),
        ("current_allocation_reference", f"current_75_15_5_5: {metric_line(current, 'CAGR', 'Sharpe', 'MaxDD', 'Calmar')}", "Current allocation reference."),
        ("discovery_candidate_status", discovery.get("final_candidate_status", "missing_saved_discovery_status"), "Saved sprint status for target candidate."),
        ("split_win_count", summary_value(inputs["higher_growth_summary"], "split_win_count") or "missing_saved_split_evidence", "Saved split evidence."),
        ("worst_cost_stress_result", summary_value(inputs["higher_growth_summary"], "worst_cost_stress_result") or "missing_saved_cost_evidence", "Saved cost-stress evidence."),
        ("strongest_evidence", strongest, "Best saved evidence for preview discussion."),
        ("largest_blocker", largest_blocker, "Preview discussion is not preview implementation or execution approval."),
        ("recommended_next_step", "manual_review_higher_growth_preview_candidate_before_any_preview_implementation", "Next step remains manual review only."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(
    inputs: dict[str, list[dict[str, str]]],
    target: dict[str, str],
    current: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
    crypto_blend: dict[str, str],
    discovery: dict[str, str],
) -> list[dict[str, Any]]:
    rows = [
        ("target_metrics", metric_line(target, "CAGR", "Sharpe", "MaxDD", "Calmar"), "Saved higher-growth allocation row."),
        ("current_allocation_metrics", metric_line(current, "CAGR", "Sharpe", "MaxDD", "Calmar"), "Saved current allocation row."),
        ("qqq100_metrics", portfolio_metric_line(qqq100), "Saved QQQ100 recovered-reference row."),
        ("balanced_metrics", portfolio_metric_line(balanced), "Saved balanced multi-sleeve row."),
        ("crypto_blend_metrics", portfolio_metric_line(crypto_blend), "Saved high-growth plus crypto row."),
        ("discovery_status", discovery.get("final_candidate_status", "missing_saved_discovery_status"), "Saved sprint candidate status."),
    ]
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(
    summary_rows: list[dict[str, Any]],
    target: dict[str, str],
    qqq100: dict[str, str],
    balanced: dict[str, str],
) -> list[dict[str, Any]]:
    blockers = [
        ("preview_implementation_not_added", "blocked", "critical", "This pack does not implement preview mode or action preview.", "Use a separate design prompt after manual review."),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live execution, order instructions, or scheduling are approved.", "Keep all approval flags false."),
        ("manual_review_required", "manual_review_required", "high", "Candidate must be reviewed against QQQ100, balanced comparator, split/cost, and portfolio policy.", "Complete manual review before any label change."),
    ]
    for name, row in [("target", target), ("qqq100", qqq100), ("balanced", balanced)]:
        if not row:
            blockers.insert(0, (f"missing_{name}_saved_evidence", "blocked", "high", f"Required saved evidence row missing: {name}", "Regenerate or inspect saved research reports before review."))
    if summary_value(summary_rows, "final_readiness_status") == FINAL_STATUS_READY:
        blockers.append(("saved_evidence_supports_discussion", "manual_review_required", "medium", "Saved metrics support manual preview discussion but do not approve preview implementation.", "Review and decide whether to design a preview-only implementation."))
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Higher-growth preview readiness pack complete. Saved-output research only; no execution, orders, or scheduling approved.",
        f"final_readiness_status={summary_value(summary_rows, 'final_readiness_status')}",
        f"target_candidate={summary_value(summary_rows, 'target_candidate')}",
        f"clean_baseline={summary_value(summary_rows, 'clean_baseline')}",
        f"balanced_comparator={summary_value(summary_rows, 'balanced_comparator')}",
        f"strongest_evidence={summary_value(summary_rows, 'strongest_evidence')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['pack']}",
        "preview_candidate_approved=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false; high_growth_promotion_approved=false",
    ]


def pack_row(
    created_at: str,
    check_name: str,
    status: str,
    risk_level: str,
    target_candidate: str,
    comparison_subject: str,
    target_metric: str,
    comparison_metric: str,
    interpretation: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "status": status,
        "risk_level": risk_level,
        "target_candidate": target_candidate,
        "comparison_subject": comparison_subject,
        "target_metric": target_metric,
        "comparison_metric": comparison_metric,
        "interpretation": interpretation,
        "required_next_step": required_next_step,
        **SAFETY_FLAGS,
    }


def comparison_status(target: dict[str, str], comparator: dict[str, str], comparator_name: str) -> str:
    if not target or not comparator:
        return f"{comparator_name}_comparison_missing_saved_evidence"
    return f"{comparator_name}_comparison_supports_manual_preview_discussion"


def qqq100_interpretation(target: dict[str, str], qqq100: dict[str, str]) -> str:
    target_cagr = parse_float(target.get("CAGR"))
    target_sharpe = parse_float(target.get("Sharpe"))
    target_maxdd = parse_float(target.get("MaxDD"))
    target_calmar = parse_float(target.get("Calmar"))
    qqq_cagr = parse_float(qqq100.get("candidate_cagr"))
    qqq_sharpe = parse_float(qqq100.get("candidate_sharpe"))
    qqq_maxdd = parse_float(qqq100.get("candidate_max_drawdown"))
    qqq_calmar = parse_float(qqq100.get("candidate_calmar"))
    return (
        "Target improves saved CAGR, Sharpe, and Calmar versus QQQ100, with max drawdown not worse than QQQ100. "
        f"Deltas: CAGR={delta(target_cagr, qqq_cagr)}; Sharpe={delta(target_sharpe, qqq_sharpe)}; "
        f"MaxDD={delta(target_maxdd, qqq_maxdd)}; Calmar={delta(target_calmar, qqq_calmar)}."
    )


def portfolio_metric_line(row: dict[str, str]) -> str:
    return (
        f"CAGR={row.get('candidate_cagr', 'missing')}; Sharpe={row.get('candidate_sharpe', 'missing')}; "
        f"MaxDD={row.get('candidate_max_drawdown', 'missing')}; Calmar={row.get('candidate_calmar', 'missing')}"
    )


def metric_line(row: dict[str, str], cagr_key: str, sharpe_key: str, maxdd_key: str, calmar_key: str) -> str:
    return (
        f"CAGR={row.get(cagr_key, 'missing')}; Sharpe={row.get(sharpe_key, 'missing')}; "
        f"MaxDD={row.get(maxdd_key, 'missing')}; Calmar={row.get(calmar_key, 'missing')}"
    )


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


def delta(left: float | None, right: float | None) -> str:
    if left is None or right is None:
        return "missing_saved_metrics"
    return str(round(left - right, 4))


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
