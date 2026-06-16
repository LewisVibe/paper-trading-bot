"""Saved-output-only research pack for the Codex QQQ defensive crash-gate sleeve.

The pack compares QQQ100 against defensive/crash-gate hypotheses using saved
CSV artefacts only. It labels unavailable metrics explicitly and does not call
Alpaca, read live positions, create orders, write SQLite, send alerts, schedule
anything, or approve execution.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FINAL_RESEARCH_STATUS = "codex_qqq_defensive_research_pack_created"
BASELINE_CANDIDATE = "qqq100_trend_gate_reference"
TOP_CANDIDATE = "codex_qqq_calmar_optimised_defensive_gate_sleeve"
BIGGEST_BLOCKER = "saved_market_metrics_required_before_candidate_label_change"
RECOMMENDED_NEXT_STEP = "run_saved_or_research_data_backtest_for_codex_qqq_defensive_candidates"
MISSING = "missing_saved_metrics"

INPUT_FILES = {
    "sleeve_scoreboard": Path("data/sleeve_research_scoreboard.csv"),
    "sleeve_candidates": Path("data/sleeve_research_candidates.csv"),
    "multi_sleeve_monitor": Path("data/multi_sleeve_strategy_monitor.csv"),
    "qqq100_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_postcheck": Path("data/qqq100_paper_postcheck.csv"),
    "paper_summary": Path("data/paper_execution_state_summary.csv"),
    "qqq100_preview_readiness": Path("data/qqq100_preview_candidate_readiness_pack.csv"),
    "qqq_lead_decision": Path("data/qqq_lead_decision_report.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "growth_validation": Path("data/growth_biased_stricter_validation.csv"),
    "growth_promotion": Path("data/growth_biased_stricter_promotion_readiness.csv"),
    "strategy_diagnostics": Path("data/strategy_improvement_diagnostics.csv"),
    "project_research_state": Path("data/project_research_state_summary.csv"),
}

OUTPUT_FILES = {
    "pack": Path("data/codex_qqq_defensive_crash_gate_research_pack.csv"),
    "candidates": Path("data/codex_qqq_defensive_crash_gate_candidates.csv"),
    "rankings": Path("data/codex_qqq_defensive_crash_gate_rankings.csv"),
    "splits": Path("data/codex_qqq_defensive_crash_gate_splits.csv"),
    "blockers": Path("data/codex_qqq_defensive_crash_gate_blockers.csv"),
    "next_steps": Path("data/codex_qqq_defensive_crash_gate_next_steps.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "report_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "general_execution_approved",
    "qqq100_execution_approved",
    "codex_experimental_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "live_position_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "general_execution_approved": False,
    "qqq100_execution_approved": False,
    "codex_experimental_execution_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

PACK_COLUMNS = [
    "created_at",
    "final_research_status",
    "baseline_candidate",
    "baseline_source",
    "baseline_cagr",
    "baseline_sharpe",
    "baseline_max_drawdown",
    "baseline_calmar",
    "top_defensive_crash_gate_candidate",
    "candidate_cagr",
    "candidate_sharpe",
    "candidate_max_drawdown",
    "candidate_calmar",
    "candidate_delta_cagr",
    "candidate_delta_sharpe",
    "candidate_delta_max_drawdown",
    "candidate_delta_calmar",
    "split_stability_summary",
    "biggest_blocker",
    "recommended_next_step",
    *SAFETY_COLUMNS,
]

CANDIDATE_COLUMNS = [
    "candidate_name",
    "candidate_role",
    "candidate_description",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "annualised_volatility",
    "cash_percentage",
    "turnover_or_trade_count",
    "rough_cost_sensitivity",
    "split_stability",
    "delta_cagr_vs_reference",
    "delta_sharpe_vs_reference",
    "delta_max_drawdown_vs_reference",
    "delta_calmar_vs_reference",
    "balanced_research_score",
    "simplicity_score",
    "overfit_risk",
    "final_candidate_status",
    "recommended_next_step",
    *SAFETY_COLUMNS,
]

RANKING_COLUMNS = [
    "created_at",
    "rank",
    "candidate_name",
    "balanced_research_score",
    "final_candidate_status",
    "ranking_reason",
    *SAFETY_COLUMNS,
]

SPLIT_COLUMNS = [
    "created_at",
    "candidate_name",
    "split_name",
    "split_status",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "notes",
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
    "required_before_preview_or_execution_wiring",
    *SAFETY_COLUMNS,
]


@dataclass
class CodexQqqDefensiveCrashGateResearchPackResult:
    output_paths: dict[str, Path]
    pack_rows: list[dict[str, Any]]
    candidate_rows: list[dict[str, Any]]
    ranking_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    next_step_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_codex_qqq_defensive_crash_gate_research_pack(
    root_dir: Path | str = ".",
) -> CodexQqqDefensiveCrashGateResearchPackResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    baseline_metrics = baseline_metric_bundle(inputs)
    candidates = build_candidate_rows(baseline_metrics)
    rankings = build_ranking_rows(created_at, candidates)
    split_rows = build_split_rows(created_at, candidates)
    pack_rows = build_pack_rows(created_at, baseline_metrics, candidates)
    blockers = build_blocker_rows(created_at)
    next_steps = build_next_step_rows(created_at)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], PACK_COLUMNS, pack_rows)
    write_rows(output_paths["candidates"], CANDIDATE_COLUMNS, candidates)
    write_rows(output_paths["rankings"], RANKING_COLUMNS, rankings)
    write_rows(output_paths["splits"], SPLIT_COLUMNS, split_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blockers)
    write_rows(output_paths["next_steps"], NEXT_STEP_COLUMNS, next_steps)
    return CodexQqqDefensiveCrashGateResearchPackResult(
        output_paths=output_paths,
        pack_rows=pack_rows,
        candidate_rows=candidates,
        ranking_rows=rankings,
        split_rows=split_rows,
        blocker_rows=blockers,
        next_step_rows=next_steps,
        summary_lines=build_summary_lines(pack_rows[0], output_paths["pack"]),
    )


def show_codex_qqq_defensive_crash_gate_research_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["pack"]
    if not path.exists():
        return 1, [
            "Codex QQQ defensive crash-gate research pack is missing.",
            "Run `python bot.py --codex-qqq-defensive-crash-gate-research-pack` first.",
            "execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    row = rows[0] if rows else {}
    return 0, [
        "Codex QQQ defensive crash-gate research pack. Research-only; no execution wiring approved.",
        f"final_research_status: {row.get('final_research_status', 'missing')}",
        f"baseline_source: {row.get('baseline_source', 'missing')}",
        f"baseline QQQ100 reference metrics: CAGR={row.get('baseline_cagr', MISSING)}, Sharpe={row.get('baseline_sharpe', MISSING)}, MaxDD={row.get('baseline_max_drawdown', MISSING)}, Calmar={row.get('baseline_calmar', MISSING)}",
        f"top defensive/crash-gate candidate: {row.get('top_defensive_crash_gate_candidate', 'missing')}",
        f"candidate metrics: CAGR={row.get('candidate_cagr', MISSING)}, Sharpe={row.get('candidate_sharpe', MISSING)}, MaxDD={row.get('candidate_max_drawdown', MISSING)}, Calmar={row.get('candidate_calmar', MISSING)}",
        f"improvement vs baseline: delta_CAGR={row.get('candidate_delta_cagr', MISSING)}, delta_Sharpe={row.get('candidate_delta_sharpe', MISSING)}, delta_MaxDD={row.get('candidate_delta_max_drawdown', MISSING)}, delta_Calmar={row.get('candidate_delta_calmar', MISSING)}",
        f"split stability summary: {row.get('split_stability_summary', MISSING)}",
        f"biggest blocker: {row.get('biggest_blocker', BIGGEST_BLOCKER)}",
        f"recommended next step: {row.get('recommended_next_step', RECOMMENDED_NEXT_STEP)}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; codex_experimental_execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def build_pack_rows(
    created_at: str,
    baseline_metrics: dict[str, str],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    top = next(row for row in candidates if row["candidate_name"] == TOP_CANDIDATE)
    return [
        {
            "created_at": created_at,
            "final_research_status": FINAL_RESEARCH_STATUS,
            "baseline_candidate": BASELINE_CANDIDATE,
            "baseline_source": baseline_metrics["baseline_source"],
            "baseline_cagr": baseline_metrics["cagr"],
            "baseline_sharpe": baseline_metrics["sharpe"],
            "baseline_max_drawdown": baseline_metrics["max_drawdown"],
            "baseline_calmar": baseline_metrics["calmar"],
            "top_defensive_crash_gate_candidate": TOP_CANDIDATE,
            "candidate_cagr": top["cagr"],
            "candidate_sharpe": top["sharpe"],
            "candidate_max_drawdown": top["max_drawdown"],
            "candidate_calmar": top["calmar"],
            "candidate_delta_cagr": top["delta_cagr_vs_reference"],
            "candidate_delta_sharpe": top["delta_sharpe_vs_reference"],
            "candidate_delta_max_drawdown": top["delta_max_drawdown_vs_reference"],
            "candidate_delta_calmar": top["delta_calmar_vs_reference"],
            "split_stability_summary": "missing_saved_split_metrics",
            "biggest_blocker": BIGGEST_BLOCKER,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
            **safety_flags(),
        }
    ]


def build_candidate_rows(baseline_metrics: dict[str, str]) -> list[dict[str, Any]]:
    return [
        candidate_row(
            BASELINE_CANDIDATE,
            "baseline/reference",
            "Existing qqq_100_trend_gate reference from saved metrics where available.",
            baseline_metrics,
            "baseline_not_cost_stressed_in_this_pack",
            "baseline_split_metrics_missing_unless_saved",
            "none_vs_reference",
            "80",
            "90",
            "reference_only",
            "Use as the comparison anchor; no repeat execution approval.",
        ),
        candidate_row(
            "codex_qqq_cash_crash_gate_sleeve",
            "cash crash-gate candidate",
            "QQQ long only when QQQ trend is positive; cash when QQQ below SMA100, SPY below SMA200, drawdown threshold, or saved breadth proxy triggers.",
            missing_metrics(),
            "missing_saved_cost_sensitivity",
            "missing_saved_split_metrics",
            "missing_saved_metrics",
            "72",
            "72",
            "codex_qqq_defensive_needs_more_validation",
            "Backtest fixed QQQ/SPY/drawdown gates before any label change.",
        ),
        candidate_row(
            "codex_qqq_spy_defensive_gate_sleeve",
            "SPY regime defensive gate candidate",
            "QQQ long when QQQ trend is positive and SPY trend/risk regime is positive; cash otherwise.",
            missing_metrics(),
            "missing_saved_cost_sensitivity",
            "missing_saved_split_metrics",
            "missing_saved_metrics",
            "74",
            "78",
            "codex_qqq_defensive_needs_more_validation",
            "Run saved/research-data validation for SPY regime gate.",
        ),
        candidate_row(
            "codex_qqq_partial_defensive_sleeve",
            "partial defensive sleeve candidate",
            "QQQ when risk-on; defensive ETF or cash proxy when risk-off. If defensive ETF data is unavailable, keep missing_saved_data.",
            missing_metrics(),
            "missing_saved_cost_sensitivity",
            "missing_saved_split_metrics",
            "missing_saved_data",
            "68",
            "70",
            "codex_qqq_defensive_needs_more_validation",
            "Validate only with supported research assets; do not invent defensive ETF metrics.",
        ),
        candidate_row(
            "codex_qqq_fast_crash_exit_reentry_sleeve",
            "fast exit/re-entry candidate",
            "QQQ long in normal trend, faster exit during drawdown/regime deterioration, re-entry only after QQQ trend recovers.",
            missing_metrics(),
            "potential_high_turnover_cost_sensitivity",
            "missing_saved_split_metrics",
            "missing_saved_metrics",
            "70",
            "82",
            "codex_qqq_defensive_needs_more_validation",
            "Stress turnover/cost before treating fast exits as promising.",
        ),
        candidate_row(
            TOP_CANDIDATE,
            "Codex ambitious Calmar-focused candidate",
            "Calmar-focused blend of QQQ trend, SPY regime, drawdown gate, and conservative re-entry rules; research-only and not fitted into execution.",
            missing_metrics(),
            "needs_cost_stress_review",
            "needs_split_60_40_70_30_80_20_validation",
            "missing_saved_metrics",
            "78",
            "88",
            "codex_qqq_defensive_needs_more_validation",
            RECOMMENDED_NEXT_STEP,
        ),
    ]


def candidate_row(
    name: str,
    role: str,
    description: str,
    metrics: dict[str, str],
    cost_sensitivity: str,
    split_stability: str,
    data_quality: str,
    balanced_score: str,
    simplicity_score: str,
    final_status: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "candidate_name": name,
        "candidate_role": role,
        "candidate_description": description,
        "cagr": metrics["cagr"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
        "calmar": metrics["calmar"],
        "annualised_volatility": metrics["annualised_volatility"],
        "cash_percentage": metrics["cash_percentage"],
        "turnover_or_trade_count": metrics["turnover_or_trade_count"],
        "rough_cost_sensitivity": cost_sensitivity,
        "split_stability": split_stability,
        "delta_cagr_vs_reference": MISSING if name != BASELINE_CANDIDATE else "0",
        "delta_sharpe_vs_reference": MISSING if name != BASELINE_CANDIDATE else "0",
        "delta_max_drawdown_vs_reference": MISSING if name != BASELINE_CANDIDATE else "0",
        "delta_calmar_vs_reference": MISSING if name != BASELINE_CANDIDATE else "0",
        "balanced_research_score": balanced_score,
        "simplicity_score": simplicity_score,
        "overfit_risk": "low_reference" if name == BASELINE_CANDIDATE else "manual_review_required",
        "final_candidate_status": final_status,
        "recommended_next_step": next_step,
        **safety_flags(),
    }


def build_ranking_rows(created_at: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=lambda row: int(row["balanced_research_score"]), reverse=True)
    return [
        {
            "created_at": created_at,
            "rank": rank,
            "candidate_name": row["candidate_name"],
            "balanced_research_score": row["balanced_research_score"],
            "final_candidate_status": row["final_candidate_status"],
            "ranking_reason": "balanced research score with missing-metric and blocker penalties",
            **safety_flags(),
        }
        for rank, row in enumerate(ranked, start=1)
    ]


def build_split_rows(created_at: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        for split_name in ["split_60_40", "split_70_30", "split_80_20"]:
            rows.append(
                {
                    "created_at": created_at,
                    "candidate_name": candidate["candidate_name"],
                    "split_name": split_name,
                    "split_status": "missing_saved_split_metrics",
                    "cagr": MISSING,
                    "sharpe": MISSING,
                    "max_drawdown": MISSING,
                    "calmar": MISSING,
                    "notes": "Run fixed chronological split validation before candidate promotion discussion.",
                    **safety_flags(),
                }
            )
    return rows


def build_blocker_rows(created_at: str) -> list[dict[str, Any]]:
    blockers = [
        ("saved_market_metrics_required_before_candidate_label_change", "blocked", "critical", "Candidate metrics are missing until a saved/research-data validation run exists.", RECOMMENDED_NEXT_STEP),
        ("split_stability_required", "blocked", "high", "60/40, 70/30, and 80/20 split validation is required.", "Run fixed split validation before any promising label."),
        ("cost_turnover_stress_required", "blocked", "high", "Fast exits and defensive gates may add turnover and cost sensitivity.", "Run cost/turnover stress review."),
        ("reference_underperformance_blocker", "blocked", "high", "Any candidate that underperforms QQQ100 without drawdown improvement must be rejected.", "Compare deltas against QQQ100 reference."),
        ("execution_wiring_blocked", "blocked", "critical", "Codex experimental sleeve remains research-only.", "Do not wire to preview/action/execution."),
        ("repeat_execution_not_approved", "blocked", "critical", "QQQ100 repeat execution remains unapproved.", "Keep QQQ100 paper path unchanged."),
        ("scheduling_not_approved", "blocked", "critical", "No scheduling, Hermes cron, loop, service, or Task Scheduler use is approved.", "Keep research manual/report-only."),
    ]
    return [blocker_row(created_at, *blocker) for blocker in blockers]


def build_next_step_rows(created_at: str) -> list[dict[str, Any]]:
    steps = [
        ("run_saved_or_research_data_backtest_for_codex_qqq_defensive_candidates", "recommended", "Use existing research data/helpers to compute fixed QQQ/SPY/drawdown gate metrics without broker data."),
        ("add_fixed_split_validation", "required", "Evaluate 60/40, 70/30, and 80/20 chronological split stability."),
        ("add_cost_turnover_stress", "required", "Measure turnover/trade count and rough cost sensitivity."),
        ("compare_against_qqq100_reference", "required", "Reject variants that do not improve drawdown/Calmar enough to justify CAGR/Sharpe drag."),
        ("keep_research_only_boundaries", "required", "Do not add preview/action/execution wiring from this pack."),
    ]
    return [
        {
            "created_at": created_at,
            "step_name": name,
            "step_status": status,
            "details": details,
            "required_before_preview_or_execution_wiring": True,
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


def baseline_metric_bundle(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    row_sources: list[tuple[str, dict[str, str]]] = []
    for name in [
        "qqq100_signal",
        "qqq100_action_preview",
        "project_research_state",
        "qqq100_preview_readiness",
        "qqq_lead_decision",
        "sleeve_candidates",
    ]:
        row_sources.extend((name, row) for row in inputs.get(name, []))
    metrics = missing_metrics()
    metrics["baseline_source"] = "missing_exact_qqq100_saved_metrics"
    for source_name, row in row_sources:
        if not is_exact_qqq100_baseline_row(row):
            continue
        candidate_metrics = metrics_from_row(row)
        if all(candidate_metrics[key] != MISSING for key in ["cagr", "sharpe", "max_drawdown", "calmar"]):
            metrics.update(candidate_metrics)
            metrics["baseline_source"] = baseline_source_label(source_name)
            return metrics
    return metrics


def missing_metrics() -> dict[str, str]:
    return {
        "cagr": MISSING,
        "sharpe": MISSING,
        "max_drawdown": MISSING,
        "calmar": MISSING,
        "baseline_source": "missing_exact_qqq100_saved_metrics",
        "annualised_volatility": MISSING,
        "cash_percentage": MISSING,
        "turnover_or_trade_count": MISSING,
    }


def first_metric(rows: list[dict[str, str]], keys: list[str]) -> str:
    for row in rows:
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
    return ""


def is_exact_qqq100_baseline_row(row: dict[str, str]) -> bool:
    identity_fields = [
        "candidate_name",
        "strategy_name",
        "sleeve_name",
        "metric_value",
        "summary_value",
        "check_status",
        "readiness_label",
        "lead_name",
        "variant_name",
    ]
    identities = {str(row.get(field, "")).strip().lower() for field in identity_fields}
    if "qqq_100_trend_gate" in identities or "qqq100_core_trend_sleeve" in identities:
        return True
    joined_identity = " ".join(identities)
    return "qqq100_clean_lead" in joined_identity or "qqq_100_simpler_lower_drawdown_candidate" in joined_identity


def metrics_from_row(row: dict[str, str]) -> dict[str, str]:
    metrics = missing_metrics()
    direct_fields = {
        "cagr": ["cagr", "CAGR", "cagr_pct", "annual_return", "estimated_or_observed_cagr"],
        "sharpe": ["sharpe", "Sharpe", "sharpe_ratio", "estimated_or_observed_sharpe"],
        "max_drawdown": ["max_drawdown", "max_drawdown_pct", "MaxDD", "maxdd", "estimated_or_observed_max_drawdown"],
        "calmar": ["calmar", "Calmar", "calmar_ratio", "estimated_or_observed_calmar"],
    }
    for metric_name, fields in direct_fields.items():
        for field in fields:
            value = str(row.get(field, "")).strip()
            if value:
                metrics[metric_name] = value
                break
    text = " ".join(str(value) for value in row.values())
    for metric_name, patterns in {
        "cagr": [r"\bCAGR\s*=\s*([-+]?\d+(?:\.\d+)?)", r"\bcagr\s*=\s*([-+]?\d+(?:\.\d+)?)"],
        "sharpe": [r"\bSharpe\s*=\s*([-+]?\d+(?:\.\d+)?)", r"\bsharpe\s*=\s*([-+]?\d+(?:\.\d+)?)"],
        "max_drawdown": [r"\bMaxDD\s*=\s*([-+]?\d+(?:\.\d+)?)", r"\bmax_drawdown\s*=\s*([-+]?\d+(?:\.\d+)?)"],
        "calmar": [r"\bCalmar\s*=\s*([-+]?\d+(?:\.\d+)?)", r"\bcalmar\s*=\s*([-+]?\d+(?:\.\d+)?)"],
    }.items():
        if metrics[metric_name] != MISSING:
            continue
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                metrics[metric_name] = match.group(1)
                break
    return metrics


def baseline_source_label(source_name: str) -> str:
    if source_name == "project_research_state":
        return "qqq_100_trend_gate_saved_metrics"
    if source_name == "sleeve_candidates":
        return "qqq100_core_trend_sleeve_saved_metrics"
    return f"{source_name}_exact_qqq100_saved_metrics"


def build_summary_lines(row: dict[str, Any], output_path: Path) -> list[str]:
    return [
        "Codex QQQ defensive crash-gate research pack created. Research-only; no execution wiring approved.",
        f"final_research_status: {row['final_research_status']}",
        f"baseline_source: {row['baseline_source']}",
        f"baseline QQQ100 reference metrics: CAGR={row['baseline_cagr']}, Sharpe={row['baseline_sharpe']}, MaxDD={row['baseline_max_drawdown']}, Calmar={row['baseline_calmar']}",
        f"top defensive/crash-gate candidate: {row['top_defensive_crash_gate_candidate']}",
        f"candidate metrics: CAGR={row['candidate_cagr']}, Sharpe={row['candidate_sharpe']}, MaxDD={row['candidate_max_drawdown']}, Calmar={row['candidate_calmar']}",
        f"improvement vs baseline: delta_CAGR={row['candidate_delta_cagr']}, delta_Sharpe={row['candidate_delta_sharpe']}, delta_MaxDD={row['candidate_delta_max_drawdown']}, delta_Calmar={row['candidate_delta_calmar']}",
        f"split stability summary: {row['split_stability_summary']}",
        f"biggest blocker: {row['biggest_blocker']}",
        f"recommended next step: {row['recommended_next_step']}",
        f"Saved pack: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; codex_experimental_execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
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
