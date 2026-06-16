"""Saved-output-only research scoreboard for candidate strategy sleeves.

The scoreboard compares current and candidate sleeves from saved CSV artefacts
only. It does not call Alpaca, refresh market data, read live positions, create
orders, write SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FINAL_SCOREBOARD_STATUS = "sleeve_research_scoreboard_created"
BEST_ACTIVE_PAPER_SLEEVE = "qqq100_core_trend_sleeve"
CODEX_EXPERIMENTAL_CANDIDATE = "codex_qqq_defensive_crash_gate_research_sleeve"
TOP_RESEARCH_SLEEVE = "codex_experimental_research_sleeve"
BIGGEST_BLOCKER = "missing_sleeve_allocation_policy_and_validation"
RECOMMENDED_NEXT_STEP = "run_targeted_research_pack_for_top_ranked_research_sleeve"
MISSING = "missing_saved_metrics"

INPUT_FILES = {
    "multi_sleeve_monitor": Path("data/multi_sleeve_strategy_monitor.csv"),
    "qqq100_repeat_design": Path("data/qqq100_repeat_alignment_workflow_design.csv"),
    "paper_summary": Path("data/paper_execution_state_summary.csv"),
    "qqq100_postcheck": Path("data/qqq100_paper_postcheck.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "portfolio_preview": Path("data/multi_strategy_portfolio_preview.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "current_research_state": Path("data/current_research_state.csv"),
    "project_research_state": Path("data/project_research_state_summary.csv"),
    "high_growth_branch": Path("data/high_growth_stock_branch_decision_checkpoint.csv"),
    "high_growth_final_validation": Path("data/high_growth_stock_final_validation_pack.csv"),
    "high_growth_risk_review": Path("data/high_growth_stock_risk_review_pack.csv"),
    "high_growth_risk_evidence": Path("data/high_growth_stock_risk_evidence_review.csv"),
    "growth_validation": Path("data/growth_biased_stricter_validation.csv"),
    "growth_promotion": Path("data/growth_biased_stricter_promotion_readiness.csv"),
    "growth_promotion_blockers": Path("data/growth_biased_stricter_promotion_blockers.csv"),
    "strategy_diagnostics": Path("data/strategy_improvement_diagnostics.csv"),
    "crypto_lab": Path("data/crypto_strategy_lab_results.csv"),
    "crypto_state": Path("data/crypto_research_state_report.csv"),
    "crypto_lead": Path("data/expanded_crypto_lead_decision.csv"),
    "defensive_state": Path("data/defensive_research_state_report.csv"),
}

OUTPUT_FILES = {
    "scoreboard": Path("data/sleeve_research_scoreboard.csv"),
    "candidates": Path("data/sleeve_research_candidates.csv"),
    "rankings": Path("data/sleeve_research_rankings.csv"),
    "blockers": Path("data/sleeve_research_blockers.csv"),
    "next_steps": Path("data/sleeve_research_next_steps.csv"),
    "codex_experimental": Path("data/sleeve_research_codex_experimental_sleeve.csv"),
}

SAFETY_COLUMNS = [
    "report_only",
    "research_only",
    "scoreboard_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "general_execution_approved",
    "qqq100_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "high_growth_execution_approved",
    "crypto_execution_approved",
    "codex_experimental_execution_approved",
]

SAFETY_FLAGS = {
    "report_only": True,
    "research_only": True,
    "scoreboard_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "general_execution_approved": False,
    "qqq100_execution_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "high_growth_execution_approved": False,
    "crypto_execution_approved": False,
    "codex_experimental_execution_approved": False,
}

SCORE_COLUMNS = [
    "sleeve_name",
    "candidate_name",
    "strategy_family",
    "status",
    "current_role",
    "estimated_or_observed_cagr",
    "estimated_or_observed_sharpe",
    "estimated_or_observed_max_drawdown",
    "estimated_or_observed_calmar",
    "cost_sensitivity",
    "split_stability",
    "drawdown_risk",
    "concentration_risk",
    "overlap_risk_with_qqq",
    "data_quality",
    "execution_readiness",
    "research_priority_score",
    "ambition_score",
    "safety_blocker_score",
    "final_candidate_status",
    "recommended_next_step",
    *SAFETY_COLUMNS,
]

SCOREBOARD_COLUMNS = [
    "created_at",
    "final_scoreboard_status",
    "current_best_active_paper_sleeve",
    "current_best_research_priority",
    "codex_experimental_sleeve_candidate",
    "biggest_blocker",
    "recommended_next_step",
    *SAFETY_COLUMNS,
]

RANKING_COLUMNS = [
    "created_at",
    "rank",
    "sleeve_name",
    "candidate_name",
    "research_priority_score",
    "ambition_score",
    "safety_blocker_score",
    "ranking_reason",
    *SAFETY_COLUMNS,
]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_COLUMNS,
]

NEXT_STEP_COLUMNS = [
    "created_at",
    "step_name",
    "step_status",
    "details",
    "required_before_new_preview_or_execution_wiring",
    *SAFETY_COLUMNS,
]


@dataclass
class SleeveResearchScoreboardResult:
    output_paths: dict[str, Path]
    scoreboard_rows: list[dict[str, Any]]
    candidate_rows: list[dict[str, Any]]
    ranking_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    next_step_rows: list[dict[str, Any]]
    codex_experimental_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_sleeve_research_scoreboard(root_dir: Path | str = ".") -> SleeveResearchScoreboardResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    candidates = build_candidate_rows(inputs)
    rankings = build_ranking_rows(created_at, candidates)
    scoreboard = build_scoreboard_rows(created_at)
    blockers = build_blocker_rows(created_at)
    next_steps = build_next_step_rows(created_at)
    codex_rows = [row for row in candidates if row["sleeve_name"] == "codex_experimental_research_sleeve"]
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["scoreboard"], SCOREBOARD_COLUMNS, scoreboard)
    write_rows(output_paths["candidates"], SCORE_COLUMNS, candidates)
    write_rows(output_paths["rankings"], RANKING_COLUMNS, rankings)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blockers)
    write_rows(output_paths["next_steps"], NEXT_STEP_COLUMNS, next_steps)
    write_rows(output_paths["codex_experimental"], SCORE_COLUMNS, codex_rows)
    return SleeveResearchScoreboardResult(
        output_paths=output_paths,
        scoreboard_rows=scoreboard,
        candidate_rows=candidates,
        ranking_rows=rankings,
        blocker_rows=blockers,
        next_step_rows=next_steps,
        codex_experimental_rows=codex_rows,
        summary_lines=build_summary_lines(scoreboard[0], output_paths["scoreboard"]),
    )


def show_sleeve_research_scoreboard(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["scoreboard"]
    if not path.exists():
        return 1, [
            "Sleeve research scoreboard is missing.",
            "Run `python bot.py --sleeve-research-scoreboard` first.",
            "execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    row = rows[0] if rows else {}
    return 0, [
        "Sleeve research scoreboard. Saved-output-only research report; no execution wiring approved.",
        f"final_scoreboard_status: {row.get('final_scoreboard_status', 'missing')}",
        f"best active paper sleeve: {row.get('current_best_active_paper_sleeve', 'missing')}",
        f"top research sleeve: {row.get('current_best_research_priority', 'missing')}",
        f"Codex experimental sleeve candidate: {row.get('codex_experimental_sleeve_candidate', 'missing')}",
        f"biggest blocker: {row.get('biggest_blocker', BIGGEST_BLOCKER)}",
        f"recommended next step: {row.get('recommended_next_step', RECOMMENDED_NEXT_STEP)}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def build_scoreboard_rows(created_at: str) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "final_scoreboard_status": FINAL_SCOREBOARD_STATUS,
            "current_best_active_paper_sleeve": BEST_ACTIVE_PAPER_SLEEVE,
            "current_best_research_priority": TOP_RESEARCH_SLEEVE,
            "codex_experimental_sleeve_candidate": CODEX_EXPERIMENTAL_CANDIDATE,
            "biggest_blocker": BIGGEST_BLOCKER,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
            **safety_flags(),
        }
    ]


def build_candidate_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    qqq_metrics = metric_bundle(inputs["qqq100_signal"] + inputs["qqq100_action_preview"])
    high_growth_metrics = metric_bundle(
        inputs["high_growth_final_validation"]
        + inputs["high_growth_risk_review"]
        + inputs["high_growth_risk_evidence"]
        + inputs["high_growth_branch"]
    )
    defensive_metrics = metric_bundle(inputs["growth_validation"] + inputs["growth_promotion"] + inputs["strategy_diagnostics"] + inputs["defensive_state"])
    crypto_metrics = metric_bundle(inputs["crypto_lab"] + inputs["crypto_state"] + inputs["crypto_lead"])
    codex_metrics = metric_bundle(inputs["growth_validation"] + inputs["growth_promotion"] + inputs["strategy_diagnostics"])
    qqq_active = qqq_active_from_saved(inputs)

    return [
        score_row(
            "qqq100_core_trend_sleeve",
            "qqq_100_trend_gate",
            "stock_etf_core_trend",
            "active_paper_sleeve" if qqq_active else "saved_active_state_unconfirmed",
            "clean main QQQ trend lead; manual one-share paper milestone complete where saved evidence confirms it",
            qqq_metrics,
            "not_material_in_saved_signal",
            "validated_enough_for_manual_milestone_but_repeat_blocked",
            "moderate",
            "single_etf_concentration",
            "self_overlap",
            "saved_evidence_present" if qqq_active else "missing_saved_metrics",
            "manual_one_share_milestone_complete_repeat_blocked",
            78,
            55,
            45,
            "best_active_paper_sleeve_repeat_blocked",
            "Keep as only active paper sleeve; do not approve repeat execution from scoreboard.",
        ),
        score_row(
            "defensive_etf_research_sleeve",
            "growth_biased_rotation_breadth_stricter_gate",
            "defensive_etf_research",
            "research_or_preview_only",
            "potential drawdown reducer / risk-off / cash alternative",
            defensive_metrics,
            "needs_saved_cost_review",
            "needs_saved_split_validation" if metrics_missing(defensive_metrics) else "saved_split_context_available",
            "potentially_lower_drawdown_but_validation_incomplete",
            "low_to_moderate",
            "moderate_growth_overlap",
            "missing_saved_metrics" if metrics_missing(defensive_metrics) else "saved_metrics_available",
            "not_execution_ready",
            67,
            60,
            72,
            "research_priority_candidate_needs_validation",
            "Build targeted defensive validation and allocation review before preview/action discussion.",
        ),
        score_row(
            "high_growth_stock_research_sleeve",
            "codex_broad_growth_balanced_breakout_control",
            "high_growth_stock_research",
            "research_only",
            "ambitious high-risk stock branch; QQQ100 remains clean main lead; broad Top1 remains rejected",
            high_growth_metrics,
            "cost_review_required",
            "split_review_required",
            "high",
            "high",
            "high_growth_and_qqq_overlap_risk",
            "missing_saved_metrics" if metrics_missing(high_growth_metrics) else "saved_metrics_available_with_blockers",
            "blocked",
            70,
            82,
            88,
            "ambitious_but_blocked_by_drawdown_concentration_split_cost",
            "Keep research-only; resolve validation blockers before preview discussion.",
        ),
        score_row(
            "crypto_research_sleeve",
            "crypto_off_hours_momentum_monitor",
            "crypto_research",
            "research_only",
            "off-hours monitoring/research route only",
            crypto_metrics,
            "crypto_cost_review_required",
            "crypto_split_stability_required",
            "very_high",
            "asset_contribution_and_volatility_concentration",
            "low_direct_overlap_but_high_portfolio_volatility",
            "missing_saved_metrics" if metrics_missing(crypto_metrics) else "saved_metrics_available_with_volatility_blockers",
            "blocked",
            58,
            76,
            92,
            "strategically_useful_but_not_execution_ready",
            "Keep crypto as off-hours research/monitoring only.",
        ),
        score_row(
            "codex_experimental_research_sleeve",
            CODEX_EXPERIMENTAL_CANDIDATE,
            "codex_experimental_research",
            "research_only",
            "Codex-nominated adaptive QQQ plus defensive crash-gate hypothesis aiming for higher Calmar without new execution wiring",
            codex_metrics,
            "needs_cost_stress_review",
            "needs_split_and_drawdown_window_validation",
            "target_lower_than_high_growth_but_unproven",
            "moderate",
            "moderate_overlap_with_qqq_by_design",
            "missing_saved_metrics" if metrics_missing(codex_metrics) else "saved_research_context_available",
            "false_research_only",
            82,
            88,
            80,
            "top_research_priority_research_only",
            "Run targeted research pack for QQQ plus defensive crash-gate sleeve before any preview/action wiring.",
        ),
    ]


def score_row(
    sleeve_name: str,
    candidate_name: str,
    strategy_family: str,
    status: str,
    current_role: str,
    metrics: dict[str, str],
    cost_sensitivity: str,
    split_stability: str,
    drawdown_risk: str,
    concentration_risk: str,
    overlap_risk: str,
    data_quality: str,
    execution_readiness: str,
    research_score: int,
    ambition_score: int,
    blocker_score: int,
    final_status: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "sleeve_name": sleeve_name,
        "candidate_name": candidate_name,
        "strategy_family": strategy_family,
        "status": status,
        "current_role": current_role,
        "estimated_or_observed_cagr": metrics["cagr"],
        "estimated_or_observed_sharpe": metrics["sharpe"],
        "estimated_or_observed_max_drawdown": metrics["max_drawdown"],
        "estimated_or_observed_calmar": metrics["calmar"],
        "cost_sensitivity": cost_sensitivity,
        "split_stability": split_stability,
        "drawdown_risk": drawdown_risk,
        "concentration_risk": concentration_risk,
        "overlap_risk_with_qqq": overlap_risk,
        "data_quality": data_quality,
        "execution_readiness": execution_readiness,
        "research_priority_score": research_score,
        "ambition_score": ambition_score,
        "safety_blocker_score": blocker_score,
        "final_candidate_status": final_status,
        "recommended_next_step": next_step,
        **safety_flags(),
    }


def build_ranking_rows(created_at: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_rows = sorted(candidates, key=lambda row: int(row["research_priority_score"]), reverse=True)
    rows = []
    for rank, candidate in enumerate(sorted_rows, start=1):
        rows.append(
            {
                "created_at": created_at,
                "rank": rank,
                "sleeve_name": candidate["sleeve_name"],
                "candidate_name": candidate["candidate_name"],
                "research_priority_score": candidate["research_priority_score"],
                "ambition_score": candidate["ambition_score"],
                "safety_blocker_score": candidate["safety_blocker_score"],
                "ranking_reason": candidate["final_candidate_status"],
                **safety_flags(),
            }
        )
    return rows


def build_blocker_rows(created_at: str) -> list[dict[str, Any]]:
    blockers = [
        ("missing_sleeve_allocation_policy_and_validation", "blocked", "critical", "Sleeve allocation policy and validation are missing.", RECOMMENDED_NEXT_STEP),
        ("qqq100_repeat_execution_not_approved", "blocked", "critical", "QQQ100 repeat execution remains blocked.", "Use the repeat/alignment design only for review."),
        ("high_growth_drawdown_concentration_split_cost_blockers", "blocked", "high", "High-growth remains blocked by drawdown, concentration, split, and cost review.", "Keep high-growth research-only."),
        ("crypto_volatility_and_execution_readiness_blockers", "blocked", "high", "Crypto remains volatile and not execution-ready.", "Keep crypto research-only."),
        ("defensive_validation_incomplete", "blocked", "high", "Defensive sleeve needs stronger saved validation.", "Build targeted defensive research pack."),
        ("codex_experimental_execution_blocked", "blocked", "critical", "Codex experimental sleeve is a research hypothesis only.", "Do not wire experimental sleeve to preview/action/execution."),
        ("scheduling_not_approved", "blocked", "critical", "No scheduling, Hermes cron, loop, service, or Task Scheduler execution is approved.", "Keep all execution-capable commands manual-only."),
    ]
    return [blocker_row(created_at, *blocker) for blocker in blockers]


def build_next_step_rows(created_at: str) -> list[dict[str, Any]]:
    steps = [
        ("run_targeted_research_pack_for_top_ranked_research_sleeve", "recommended", "Design a saved-output research pack for the Codex experimental QQQ plus defensive crash-gate hypothesis."),
        ("define_sleeve_allocation_policy", "required", "Define how sleeves would coexist conceptually before preview/action-preview."),
        ("keep_qqq100_as_only_active_paper_sleeve", "required", "Do not add another active paper sleeve from this scoreboard."),
        ("keep_high_growth_crypto_defensive_research_only", "required", "Do not wire candidate sleeves to execution."),
        ("keep_repeat_and_scheduling_unapproved", "required", "Do not approve repeat execution or scheduling from this scoreboard."),
    ]
    return [
        {
            "created_at": created_at,
            "step_name": name,
            "step_status": status,
            "details": details,
            "required_before_new_preview_or_execution_wiring": True,
            **safety_flags(),
        }
        for name, status, details in steps
    ]


def blocker_row(created_at: str, name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **safety_flags(),
    }


def metric_bundle(rows: list[dict[str, str]]) -> dict[str, str]:
    return {
        "cagr": first_metric(rows, ["cagr", "CAGR", "cagr_pct", "annual_return"]) or MISSING,
        "sharpe": first_metric(rows, ["sharpe", "Sharpe", "sharpe_ratio"]) or MISSING,
        "max_drawdown": first_metric(rows, ["max_drawdown", "max_drawdown_pct", "MaxDD", "maxdd"]) or MISSING,
        "calmar": first_metric(rows, ["calmar", "Calmar", "calmar_ratio"]) or MISSING,
    }


def first_metric(rows: list[dict[str, str]], keys: list[str]) -> str:
    for row in rows:
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
    return ""


def metrics_missing(metrics: dict[str, str]) -> bool:
    return any(value == MISSING for value in metrics.values())


def qqq_active_from_saved(inputs: dict[str, list[dict[str, str]]]) -> bool:
    monitor_status = first_metric(inputs["multi_sleeve_monitor"], ["active_paper_sleeve"])
    if monitor_status == BEST_ACTIVE_PAPER_SLEEVE:
        return True
    joined = " ".join(" ".join(str(value) for value in row.values()) for row in inputs["paper_summary"] + inputs["qqq100_postcheck"]).lower()
    return "paper_execution_milestone_recorded" in joined and "aligned_long" in joined


def build_summary_lines(row: dict[str, Any], output_path: Path) -> list[str]:
    return [
        "Sleeve research scoreboard created. Saved-output research only; no execution wiring approved.",
        f"final_scoreboard_status: {row['final_scoreboard_status']}",
        f"best active paper sleeve: {row['current_best_active_paper_sleeve']}",
        f"top research sleeve: {row['current_best_research_priority']}",
        f"Codex experimental sleeve candidate: {row['codex_experimental_sleeve_candidate']}",
        f"biggest blocker: {row['biggest_blocker']}",
        f"recommended next step: {row['recommended_next_step']}",
        f"Saved scoreboard: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
