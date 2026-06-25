"""Saved-output evidence-quality review for the defensive sleeve.

This checkpoint reviews the saved defensive sleeve evidence that already
exists. It does not rerun research, refresh market data, call Alpaca, read
positions, create order instructions, schedule anything, or approve
preview/promotion/execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


INPUT_FILES = {
    "manual_review_summary": Path("data/paper_live_defensive_sleeve_manual_review_summary.csv"),
    "preview_readiness_summary": Path("data/paper_live_defensive_sleeve_preview_readiness_summary.csv"),
    "candidate_comparison": Path("data/defensive_candidate_comparison.csv"),
    "vol_managed_robustness": Path("data/vol_managed_etf_robustness_report.csv"),
    "drawdown_comparison": Path("data/etf_defensive_drawdown_comparison.csv"),
    "allocation_preview": Path("data/defensive_allocation_preview.csv"),
    "allocation_risk_preview": Path("data/defensive_allocation_risk_preview.csv"),
    "allocation_decision": Path("data/defensive_allocation_decision_report.csv"),
}

OUTPUT_FILES = {
    "review": Path("data/paper_live_defensive_sleeve_evidence_quality.csv"),
    "summary": Path("data/paper_live_defensive_sleeve_evidence_quality_summary.csv"),
    "blockers": Path("data/paper_live_defensive_sleeve_evidence_quality_blockers.csv"),
    "evidence": Path("data/paper_live_defensive_sleeve_evidence_quality_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "promotion_approved": False,
    "preview_candidate_approved": False,
    "defensive_sleeve_promoted": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "evidence_quality_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "action_preview_created": False,
    "portfolio_execution_wired": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REVIEW_COLUMNS = [
    "review_area",
    "evidence_present",
    "quality_status",
    "risk_level",
    "saved_evidence",
    "manual_review_interpretation",
    "required_next_step",
    "research_only",
    "report_only",
    "saved_output_only",
    "evidence_quality_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "action_preview_created",
    "portfolio_execution_wired",
    "alpaca_called",
    "live_positions_read",
    "market_data_refreshed",
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]

FINAL_STATUS = "defensive_sleeve_evidence_quality_manual_review_required"
NEXT_STEP = "manual_review_split_drawdown_and_allocation_blockers_before_defensive_preview_design"


@dataclass
class DefensiveEvidenceQualityContext:
    root: Path
    rows_by_name: dict[str, list[dict[str, str]]]
    manual_review_status: str
    preview_readiness_status: str
    preview_candidate_status: str
    preferred_candidate: str
    allocation_decision: str


@dataclass
class DefensiveEvidenceQualityResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_defensive_sleeve_evidence_quality(root_dir: Path | str = ".") -> DefensiveEvidenceQualityResult:
    root = Path(root_dir)
    context = load_context(root)
    review_rows = build_review_rows(context)
    summary_rows = build_summary_rows(context, review_rows)
    blocker_rows = build_blocker_rows(context, review_rows)
    evidence_rows = build_evidence_rows(context, review_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return DefensiveEvidenceQualityResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_defensive_sleeve_evidence_quality(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live defensive sleeve evidence-quality review is missing.",
            "Run `python bot.py --paper-live-defensive-sleeve-evidence-quality` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live defensive sleeve evidence-quality review saved display. Report only; no promotion or orders approved.",
        f"final_quality_status: {summary_value(rows, 'final_quality_status')}",
        f"preferred_defensive_candidate: {summary_value(rows, 'preferred_defensive_candidate')}",
        f"manual_review_status: {summary_value(rows, 'manual_review_status')}",
        f"preview_candidate_status: {summary_value(rows, 'preview_candidate_status')}",
        f"split_sensitivity_status: {summary_value(rows, 'split_sensitivity_status')}",
        f"drawdown_quality_status: {summary_value(rows, 'drawdown_quality_status')}",
        f"allocation_decision_status: {summary_value(rows, 'allocation_decision_status')}",
        f"largest_quality_blocker: {summary_value(rows, 'largest_quality_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; promotion_approved=false; preview_candidate_approved=false; defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]


def load_context(root: Path) -> DefensiveEvidenceQualityContext:
    rows_by_name = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    manual_rows = rows_by_name["manual_review_summary"]
    preview_rows = rows_by_name["preview_readiness_summary"]
    return DefensiveEvidenceQualityContext(
        root=root,
        rows_by_name=rows_by_name,
        manual_review_status=summary_value(manual_rows, "final_manual_review_status") or "missing_manual_review",
        preview_readiness_status=summary_value(preview_rows, "final_preview_readiness_status") or "missing_preview_readiness",
        preview_candidate_status=summary_value(preview_rows, "preview_candidate_status") or "defensive_preview_candidate_not_approved",
        preferred_candidate=summary_value(manual_rows, "preferred_defensive_candidate") or find_preferred_candidate(rows_by_name["candidate_comparison"]),
        allocation_decision=find_decision(rows_by_name["allocation_decision"]),
    )


def build_review_rows(context: DefensiveEvidenceQualityContext) -> list[dict[str, Any]]:
    return [
        review_row(
            "candidate_strength",
            bool(context.rows_by_name["candidate_comparison"]),
            "promising_research_context_not_promotion",
            "medium",
            candidate_strength_evidence(context),
            "The saved comparison supports continued defensive research, not preview approval.",
            "Keep QQQ100 as clean paper-live lead and review defensive as a sleeve only.",
        ),
        review_row(
            "split_sensitivity",
            bool(context.rows_by_name["vol_managed_robustness"]),
            "split_sensitivity_manual_review_required",
            "high",
            split_evidence(context),
            "Fixed-split results are strong, but the candidate is still explicitly treated as split-sensitive.",
            "Manual review split robustness before any defensive preview design.",
        ),
        review_row(
            "full_period_drawdown",
            bool(context.rows_by_name["drawdown_comparison"]),
            "full_period_drawdown_manual_review_required",
            "high",
            drawdown_evidence(context),
            "Vol-managed ETF improved split-80/20 drawdown but had worse full-period worst drawdown than monthly ETF rotation.",
            "Manual review full-period drawdown window and recovery before any preview label.",
        ),
        review_row(
            "allocation_decision",
            bool(context.rows_by_name["allocation_decision"]),
            context.allocation_decision,
            "critical",
            allocation_evidence(context),
            "The allocation decision remains blocked for execution design and must not be treated as approval.",
            "Resolve allocation blockers separately before preview or execution design.",
        ),
        review_row(
            "qqq100_role_boundary",
            bool(context.rows_by_name["manual_review_summary"]),
            "qqq100_clean_lead_retained",
            "critical",
            f"manual_review_status={context.manual_review_status}; preview_candidate_status={context.preview_candidate_status}",
            "QQQ100 remains the clean paper-live lead; defensive is at most a future sleeve discussion.",
            "Do not replace QQQ100 or create defensive order instructions.",
        ),
        review_row(
            "preview_execution_boundary",
            bool(context.rows_by_name["preview_readiness_summary"]),
            "defensive_preview_candidate_not_approved",
            "critical",
            f"preview_readiness_status={context.preview_readiness_status}; candidate_status={context.preview_candidate_status}",
            "Preview candidacy, promotion, paper execution, repeat execution, live trading, and scheduling remain false.",
            NEXT_STEP,
        ),
    ]


def review_row(
    area: str,
    present: bool,
    status: str,
    risk: str,
    evidence: str,
    interpretation: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "review_area": area,
        "evidence_present": present,
        "quality_status": status if present else f"{status}_saved_evidence_missing",
        "risk_level": risk,
        "saved_evidence": evidence,
        "manual_review_interpretation": interpretation,
        "required_next_step": next_step,
        **ROW_SAFETY,
    }


def build_summary_rows(context: DefensiveEvidenceQualityContext, review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("final_quality_status", FINAL_STATUS, "Defensive sleeve saved evidence quality remains manual-review only."),
        ("preferred_defensive_candidate", context.preferred_candidate, "Saved preferred defensive research candidate."),
        ("manual_review_status", context.manual_review_status, "Saved defensive manual-review status."),
        ("preview_readiness_status", context.preview_readiness_status, "Saved defensive preview-readiness status."),
        ("preview_candidate_status", context.preview_candidate_status, "Defensive preview candidate remains not approved."),
        ("split_sensitivity_status", review_status(review_rows, "split_sensitivity"), "Split sensitivity requires manual review."),
        ("drawdown_quality_status", review_status(review_rows, "full_period_drawdown"), "Full-period drawdown requires manual review."),
        ("allocation_decision_status", context.allocation_decision, "Saved allocation decision remains blocked/not execution-ready."),
        ("largest_quality_blocker", "split_drawdown_and_allocation_blockers", "Main blockers before defensive preview design."),
        ("recommended_next_step", NEXT_STEP, "Next step remains manual review/report-only."),
        ("promotion_approved", "False", "Promotion approval remains false."),
        ("preview_candidate_approved", "False", "Preview candidate approval remains false."),
        ("defensive_sleeve_promoted", "False", "Defensive sleeve is not promoted."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(context: DefensiveEvidenceQualityContext, review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = [
        ("split_sensitivity_manual_review_required", "manual_review_required", "high", split_evidence(context), "Review fixed split robustness and production allocation policy."),
        ("full_period_drawdown_manual_review_required", "manual_review_required", "high", drawdown_evidence(context), "Review full-period worst drawdown and recovery before preview design."),
        ("allocation_decision_blocked", "blocked", "critical", allocation_evidence(context), "Resolve allocation decision blockers separately."),
        ("preview_candidate_not_approved", "blocked", "critical", "Defensive sleeve preview candidate remains not approved.", NEXT_STEP),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or order instructions are approved.", "Keep order-capable commands separate and unscheduled."),
    ]
    for row in review_rows:
        if not row.get("evidence_present"):
            blockers.insert(
                0,
                (
                    f"{row['review_area']}_saved_evidence_missing",
                    "manual_review_required",
                    "high",
                    str(row.get("saved_evidence", "")),
                    "Regenerate missing defensive saved reports before relying on this review.",
                ),
            )
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows(context: DefensiveEvidenceQualityContext, review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("input_files_checked", ";".join(str(path) for path in INPUT_FILES.values()), "Saved CSV inputs only."),
        ("approval_flags", "all_false", "Execution, preview, promotion, and scheduling approvals remain false."),
    ]
    for name, saved_rows in context.rows_by_name.items():
        rows.append((f"{name}_row_count", str(len(saved_rows)), "Saved row count only."))
    for row in review_rows:
        rows.append((f"{row['review_area']}_evidence", str(row["saved_evidence"]), str(row["manual_review_interpretation"])))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def candidate_strength_evidence(context: DefensiveEvidenceQualityContext) -> str:
    row = first_row_with(context.rows_by_name["candidate_comparison"], "volatility_managed_dual_momentum_etf")
    return (
        "candidate=volatility_managed_dual_momentum_etf; "
        f"cagr={row.get('out_of_sample_cagr_pct', 'unavailable')}; "
        f"sharpe={row.get('out_of_sample_sharpe', 'unavailable')}; "
        f"calmar={row.get('out_of_sample_calmar', 'unavailable')}; "
        f"max_drawdown={row.get('out_of_sample_max_drawdown_pct', 'unavailable')}; "
        f"score={row.get('defensive_score', 'unavailable')}"
    )


def split_evidence(context: DefensiveEvidenceQualityContext) -> str:
    rows = context.rows_by_name["vol_managed_robustness"]
    split_names = [row.get("split_name", "") for row in rows if row.get("split_name")]
    calmars = [parse_float(row.get("out_of_sample_calmar", "")) for row in rows]
    valid_calmars = [value for value in calmars if value is not None]
    return (
        f"splits={';'.join(split_names) or 'unavailable'}; "
        f"best_calmar={round(max(valid_calmars), 4) if valid_calmars else 'unavailable'}; "
        f"worst_calmar={round(min(valid_calmars), 4) if valid_calmars else 'unavailable'}"
    )


def drawdown_evidence(context: DefensiveEvidenceQualityContext) -> str:
    rows = context.rows_by_name["drawdown_comparison"]
    full_rotation = first_row_matching(rows, "full_period_worst_drawdown", "monthly_etf_momentum_rotation")
    full_vol = first_row_matching(rows, "full_period_worst_drawdown", "volatility_managed_dual_momentum_etf")
    split_rotation = first_row_matching(rows, "split_80_20_out_of_sample", "monthly_etf_momentum_rotation")
    split_vol = first_row_matching(rows, "split_80_20_out_of_sample", "volatility_managed_dual_momentum_etf")
    return (
        "full_period_rotation_drawdown="
        f"{full_rotation.get('drawdown_depth_pct', 'unavailable')}; "
        "full_period_vol_managed_drawdown="
        f"{full_vol.get('drawdown_depth_pct', 'unavailable')}; "
        "split80_rotation_drawdown="
        f"{split_rotation.get('drawdown_depth_pct', 'unavailable')}; "
        "split80_vol_managed_drawdown="
        f"{split_vol.get('drawdown_depth_pct', 'unavailable')}"
    )


def allocation_evidence(context: DefensiveEvidenceQualityContext) -> str:
    risk_rows = context.rows_by_name["allocation_risk_preview"]
    blockers = [row.get("risk_check", "") for row in risk_rows if row.get("risk_status") == "blocked"]
    warnings = [row.get("risk_check", "") for row in risk_rows if row.get("risk_status") == "warning"]
    return f"decision={context.allocation_decision}; blockers={';'.join(blockers) or 'none'}; warnings={';'.join(warnings) or 'none'}"


def find_preferred_candidate(rows: list[dict[str, str]]) -> str:
    if first_row_with(rows, "volatility_managed_dual_momentum_etf"):
        return "volatility_managed_dual_momentum_etf"
    if first_row_with(rows, "monthly_etf_momentum_rotation"):
        return "monthly_etf_momentum_rotation"
    return "missing_saved_candidate_context"


def find_decision(rows: list[dict[str, str]]) -> str:
    for row in rows:
        if row.get("decision_area") == "overall_decision":
            return row.get("decision_label") or row.get("decision_status") or "unavailable"
    return "missing_allocation_decision"


def review_status(rows: list[dict[str, Any]], area: str) -> str:
    for row in rows:
        if row.get("review_area") == area:
            return str(row.get("quality_status", "unavailable"))
    return "unavailable"


def first_row_with(rows: list[dict[str, str]], token: str) -> dict[str, str]:
    token_lower = token.lower()
    for row in rows:
        if token_lower in " ".join(str(value).lower() for value in row.values()):
            return row
    return {}


def first_row_matching(rows: list[dict[str, str]], period: str, strategy: str) -> dict[str, str]:
    for row in rows:
        if row.get("comparison_period") == period and row.get("strategy_name") == strategy:
            return row
    return {}


def parse_float(value: str) -> float | None:
    try:
        return float(str(value).strip().replace("%", ""))
    except (TypeError, ValueError):
        return None


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live defensive sleeve evidence-quality review complete. Report only; no promotion, orders, or scheduling approved.",
        f"final_quality_status={summary_value(summary_rows, 'final_quality_status')}",
        f"preferred_defensive_candidate={summary_value(summary_rows, 'preferred_defensive_candidate')}",
        f"manual_review_status={summary_value(summary_rows, 'manual_review_status')}",
        f"preview_candidate_status={summary_value(summary_rows, 'preview_candidate_status')}",
        f"split_sensitivity_status={summary_value(summary_rows, 'split_sensitivity_status')}",
        f"drawdown_quality_status={summary_value(summary_rows, 'drawdown_quality_status')}",
        f"allocation_decision_status={summary_value(summary_rows, 'allocation_decision_status')}",
        f"largest_quality_blocker={summary_value(summary_rows, 'largest_quality_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['review']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; promotion_approved=false; preview_candidate_approved=false; defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]


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
