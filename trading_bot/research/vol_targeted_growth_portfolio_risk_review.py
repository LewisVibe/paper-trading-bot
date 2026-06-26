"""Saved-output portfolio-risk review for volatility-targeted growth 15/20."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
FINAL_STATUS = "vol_targeted_growth_portfolio_risk_manual_review_required"
NEXT_STEP = "keep_research_only_until_broker_comparison_and_portfolio_risk_policy_are_reviewed"

OUTPUT_FILES = {
    "review": Path("data/vol_targeted_growth_portfolio_risk_review.csv"),
    "summary": Path("data/vol_targeted_growth_portfolio_risk_review_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_portfolio_risk_review_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_portfolio_risk_review_blockers.csv"),
}

INPUT_FILES = {
    "action_preview": Path("data/vol_targeted_growth_action_preview.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "broker_design_summary": Path("data/vol_targeted_growth_broker_position_comparison_design_summary.csv"),
    "robustness_summary": Path("data/vol_targeted_growth_robustness_checkpoint_summary.csv"),
    "nearby_summary": Path("data/vol_targeted_growth_nearby_variants_summary.csv"),
    "paper_live_ladder_status": Path("data/paper_live_promotion_ladder_status.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "paper_live_candidate_approved": False,
    "paper_live_discussion_approved": False,
    "broker_positions_compared": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "never_schedule_order_capable_commands": True,
}

REVIEW_COLUMNS = ["created_at", "review_item", "status", "risk_level", "evidence", "interpretation", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthPortfolioRiskReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_portfolio_risk_review(root_dir: Path | str = ".") -> VolTargetedGrowthPortfolioRiskReviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    review_rows = build_review_rows(created_at, inputs)
    summary_rows = build_summary_rows(inputs, review_rows)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthPortfolioRiskReviewResult(output_paths, review_rows, summary_rows, evidence_rows, blocker_rows, build_summary_lines(summary_rows, output_paths))


def show_vol_targeted_growth_portfolio_risk_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-portfolio-risk-review` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth portfolio-risk review saved display. Manual-review only; no execution approval.",
        f"final_risk_review_status: {summary_value(rows, 'final_risk_review_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"paper_live_discussion_status: {summary_value(rows, 'paper_live_discussion_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "paper_live_candidate_approved=false; broker_positions_compared=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_review_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    action_status = summary_value(inputs["action_preview_summary"], "final_action_preview_status")
    broker_design_status = summary_value(inputs["broker_design_summary"], "final_design_status")
    robustness = summary_value(inputs["robustness_summary"], "final_robustness_status")
    return [
        review_row(created_at, "saved_action_preview", "manual_review_required", "medium", action_status or "missing", "Saved action preview exists only as unknown-exposure review context.", NEXT_STEP),
        review_row(created_at, "broker_position_context", "blocked", "critical", broker_design_status or "missing", "Broker comparison has not been implemented or approved.", "review_broker_comparison_design_first"),
        review_row(created_at, "portfolio_risk_policy", "manual_review_required", "high", robustness or "missing", "Volatility targeting is promising research, but portfolio risk policy is not paper-live approval.", "define_portfolio_risk_limits_before_paper_live_discussion"),
        review_row(
            created_at,
            "paper_live_boundary",
            "paper_live_discussion_not_approved",
            "critical",
            "QQQ100 remains current paper-live seed; high-growth/crypto components remain research-only.",
            "Do not move this candidate to paper-live until separate manual policy review.",
            "keep_vol_targeted_growth_research_only",
        ),
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("final_risk_review_status", FINAL_STATUS, "Volatility-targeted growth remains manual-review/research-only."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("action_preview_status", summary_value(inputs["action_preview_summary"], "final_action_preview_status") or "missing_action_preview_status", "Saved action-preview status."),
        ("broker_design_status", summary_value(inputs["broker_design_summary"], "final_design_status") or "missing_broker_design_status", "Saved broker-position comparison design status."),
        ("paper_live_discussion_status", "paper_live_discussion_not_approved_research_only", "This report does not approve paper-live candidate discussion yet."),
        ("largest_blocker", "broker_position_comparison_and_portfolio_risk_policy_not_reviewed", "Broker comparison and portfolio risk policy remain unresolved."),
        ("recommended_next_step", NEXT_STEP, "Keep this candidate research-only until those reviews are complete."),
        ("review_row_count", str(len(review_rows)), "Saved review row count."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows() -> list[dict[str, Any]]:
    rows = [
        ("broker_position_comparison_missing", "blocked", "critical", "No approved broker-position comparison exists.", "Review comparison design before any broker read."),
        ("portfolio_risk_policy_missing", "blocked", "high", "No paper-live risk policy exists for this multi-sleeve candidate.", "Define exposure, drawdown, component, and crypto caps before paper-live discussion."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, or scheduling is approved.", "Keep all approval flags false."),
    ]
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth portfolio-risk review complete. Manual-review only; no execution or scheduling approved.",
        f"final_risk_review_status={summary_value(rows, 'final_risk_review_status')}",
        f"paper_live_discussion_status={summary_value(rows, 'paper_live_discussion_status')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_review={output_paths['review']}",
        "paper_live_candidate_approved=false; broker_positions_compared=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def review_row(created_at: str, item: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"created_at": created_at, "review_item": item, "status": status, "risk_level": risk, "evidence": evidence, "interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


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


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""
