"""Saved-output evidence pack for a future volatility seed-change proposal.

This report lists the evidence required before QQQ100 displacement could even
be proposed. It does not request or approve displacement, change the seed, read
broker positions, create order instructions, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_seed_change_evidence_pack_incomplete_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_seed_change_evidence_pack_blocked_missing_seed_change_review"
NEXT_STEP = "fill_required_evidence_before_any_seed_change_proposal"

OUTPUT_FILES = {
    "pack": Path("data/vol_targeted_growth_seed_change_evidence_pack.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_evidence_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_evidence_sources.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_evidence_blockers.csv"),
}

INPUT_FILES = {
    "seed_change_review_summary": Path("data/vol_targeted_growth_seed_change_review_summary.csv"),
    "seed_change_review_blockers": Path("data/vol_targeted_growth_seed_change_review_blockers.csv"),
    "proposal_preview_summary": Path("data/vol_targeted_growth_proposal_preview_summary.csv"),
    "proposal_preview": Path("data/vol_targeted_growth_proposal_preview.csv"),
    "candidate_discussion_summary": Path("data/vol_targeted_growth_candidate_discussion_summary.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "risk_reward_summary": Path("data/vol_targeted_growth_seed_change_risk_reward_summary.csv"),
    "drawdown_stress_summary": Path("data/vol_targeted_growth_seed_change_drawdown_stress_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
    "paper_live_monitoring_summary": Path("data/paper_live_monitoring_status_summary.csv"),
}

REQUIRED_EVIDENCE = [
    ("qqq100_incumbent_state", "present_if_saved_qqq100_followup_exists", "QQQ100 current seed status and no-action policy must be saved and current."),
    ("volatility_proposal_preview", "present_if_saved_proposal_preview_exists", "Volatility proposal sleeve preview must exist and remain non-executable."),
    ("component_sleeve_approval_review", "missing_required", "High-growth, crypto, and defensive sleeves need separate research-only or promotion boundary review."),
    ("risk_reward_comparison", "missing_required", "QQQ100 vs volatility proposal risk/reward comparison must be summarized from saved research evidence."),
    ("drawdown_stress_review", "missing_required", "Drawdown and stress behavior must be reviewed before any displacement proposal."),
    ("cost_turnover_review", "missing_required", "Turnover and cost sensitivity must be reviewed before any displacement proposal."),
    ("split_stability_review", "missing_required", "Split stability and period robustness must be reviewed before any displacement proposal."),
    ("broker_exposure_context", "manual_review_required", "A separate explicitly confirmed read-only broker comparison is required before operational review."),
    ("action_preview_design", "missing_required", "A non-executable action-preview design would be required before any operational proposal."),
    ("seed_change_proposal_document", "not_created", "A formal seed-change proposal has not been created and is not approved here."),
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "evidence_pack_only": True,
    "proposal_only": True,
    "preview_only": True,
    "seed_changed": False,
    "seed_change_proposal_created": False,
    "qqq100_displacement_requested": False,
    "qqq100_displacement_approved": False,
    "vol_targeted_seed_approved": False,
    "action_preview_added": False,
    "order_instructions_created": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_read_now": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "paper_live_candidate_approved": False,
    "vol_targeted_paper_live_candidate_approved": False,
    "preview_implementation_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

PACK_COLUMNS = [
    "created_at",
    "evidence_item",
    "evidence_status",
    "risk_level",
    "evidence_requirement",
    "saved_source_status",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthSeedChangeEvidencePackResult:
    output_paths: dict[str, Path]
    pack_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_evidence_pack(root_dir: Path | str = ".") -> VolTargetedGrowthSeedChangeEvidencePackResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    final_status = determine_final_status(inputs)
    pack_rows = build_pack_rows(created_at, inputs, final_status)
    summary_rows = build_summary_rows(inputs, pack_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status, pack_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], PACK_COLUMNS, pack_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeEvidencePackResult(
        output_paths=output_paths,
        pack_rows=pack_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_evidence_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-evidence-pack` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change evidence pack saved display. Evidence checklist only; no seed change approved.",
        f"final_evidence_pack_status: {summary_value(rows, 'final_evidence_pack_status')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"candidate_under_review: {summary_value(rows, 'candidate_under_review')}",
        f"missing_required_evidence_count: {summary_value(rows, 'missing_required_evidence_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def determine_final_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    review_status = summary_value(inputs["seed_change_review_summary"], "final_seed_change_review_status")
    if review_status == "vol_targeted_growth_seed_change_review_created_manual_review_required":
        return FINAL_STATUS
    return BLOCKED_STATUS


def build_pack_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    source_statuses = source_status_map(inputs)
    rows: list[dict[str, Any]] = []
    for item, default_status, requirement in REQUIRED_EVIDENCE:
        status = resolve_evidence_status(item, default_status, source_statuses, final_status)
        rows.append(
            {
                "created_at": created_at,
                "evidence_item": item,
                "evidence_status": status,
                "risk_level": "critical" if status in {"missing_required", "not_created"} else "high",
                "evidence_requirement": requirement,
                "saved_source_status": source_statuses.get(item, "not_available"),
                "interpretation": interpretation_for(item, status),
                "required_next_step": next_step_for(item, status),
                **SAFETY_FLAGS,
            }
        )
    return rows


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], pack_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    missing_count = sum(1 for row in pack_rows if row.get("evidence_status") in {"missing_required", "not_created", "manual_review_required"})
    rows = [
        ("final_evidence_pack_status", final_status, "Whether saved seed-change review supports this evidence checklist."),
        ("incumbent_seed", INCUMBENT_SEED, "Current paper-live seed remains unchanged."),
        ("candidate_under_review", SELECTED_CANDIDATE, "Volatility-targeted candidate under manual review."),
        ("source_seed_change_review_status", summary_value(inputs["seed_change_review_summary"], "final_seed_change_review_status") or "missing_seed_change_review", "Saved seed-change review status."),
        ("required_evidence_count", str(len(pack_rows)), "Evidence items required before any seed-change proposal."),
        ("missing_required_evidence_count", str(missing_count), "Evidence items still missing or manual-review required."),
        ("seed_change_readiness", "not_ready_evidence_incomplete", "Evidence is incomplete; no seed-change proposal is created."),
        ("largest_blocker", "required_seed_change_evidence_incomplete" if final_status == FINAL_STATUS else "missing_seed_change_review", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if final_status == FINAL_STATUS else "run_seed_change_review_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This evidence pack reads saved outputs only and does not call Alpaca."))
    rows.append(("seed_change_proposal_created_now", "false", "This evidence pack does not create a seed-change proposal."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str, pack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent seed.", NEXT_STEP),
        ("seed_change_proposal_not_created", "blocked", "critical", "This evidence pack does not create or approve a seed-change proposal.", "complete_evidence_pack_first"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    for row in pack_rows:
        if row.get("evidence_status") in {"missing_required", "not_created", "manual_review_required"}:
            rows.append((f"missing_{row.get('evidence_item')}", "blocked", str(row.get("risk_level", "high")), str(row.get("interpretation", "")), str(row.get("required_next_step", NEXT_STEP))))
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("seed_change_review_missing", "blocked", "critical", "Saved seed-change review is missing or not ready.", "run_seed_change_review_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth seed-change evidence pack complete. Evidence checklist only; no seed change approved.",
        f"final_evidence_pack_status={summary_value(summary_rows, 'final_evidence_pack_status')}",
        f"incumbent_seed={summary_value(summary_rows, 'incumbent_seed')}",
        f"candidate_under_review={summary_value(summary_rows, 'candidate_under_review')}",
        f"missing_required_evidence_count={summary_value(summary_rows, 'missing_required_evidence_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_pack={output_paths['pack']}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def source_status_map(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "qqq100_incumbent_state": summary_value(inputs["qqq100_followup_policy_summary"], "final_followup_policy_status") or "missing",
        "volatility_proposal_preview": summary_value(inputs["proposal_preview_summary"], "final_proposal_preview_status") or "missing",
        "broker_exposure_context": summary_value(inputs["broker_comparison_summary"], "final_comparison_status") or "missing",
        "risk_reward_comparison": summary_value(inputs["risk_reward_summary"], "final_risk_reward_status") or "missing",
        "drawdown_stress_review": summary_value(inputs["drawdown_stress_summary"], "final_drawdown_stress_status") or "missing",
    }


def resolve_evidence_status(item: str, default_status: str, source_statuses: dict[str, str], final_status: str) -> str:
    if final_status == BLOCKED_STATUS:
        return "blocked_missing_seed_change_review"
    if item == "qqq100_incumbent_state" and source_statuses.get(item, "missing") != "missing":
        return "present_manual_review_required"
    if item == "volatility_proposal_preview" and source_statuses.get(item, "missing") == "vol_targeted_growth_proposal_preview_created_saved_output_only":
        return "present_manual_review_required"
    if item == "broker_exposure_context" and source_statuses.get(item, "missing") != "missing":
        return "manual_review_required"
    if item == "risk_reward_comparison" and source_statuses.get(item, "missing") == "vol_targeted_growth_risk_reward_evidence_created_manual_review_required":
        return "present_manual_review_required"
    if item == "drawdown_stress_review" and source_statuses.get(item, "missing") == "vol_targeted_growth_drawdown_stress_evidence_created_manual_review_required":
        return "present_manual_review_required"
    return default_status


def interpretation_for(item: str, status: str) -> str:
    if status == "present_manual_review_required":
        return f"{item} has saved evidence, but it does not approve displacement."
    if status == "manual_review_required":
        return f"{item} needs explicit manual review before any seed-change proposal."
    if status in {"missing_required", "not_created"}:
        return f"{item} is required before any QQQ100 displacement proposal."
    return "Seed-change evidence is blocked until the previous review exists."


def next_step_for(item: str, status: str) -> str:
    if status == "present_manual_review_required":
        return "manual_review_saved_evidence"
    if item == "broker_exposure_context":
        return "separate_confirmed_readonly_broker_comparison_review"
    if item == "seed_change_proposal_document":
        return "do_not_create_seed_change_proposal_until_evidence_complete"
    return "create_or_review_required_saved_evidence"


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
