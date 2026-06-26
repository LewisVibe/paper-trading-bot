"""Saved-output formal proposal document for volatility seed-change review."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_formal_seed_change_proposal_created_manual_approval_required"
BLOCKED_STATUS = "vol_targeted_growth_formal_seed_change_proposal_blocked_manual_review_not_ready"
NEXT_STEP = "manual_approval_required_before_any_seed_change_implementation"

OUTPUT_FILES = {
    "proposal": Path("data/vol_targeted_growth_formal_seed_change_proposal.csv"),
    "summary": Path("data/vol_targeted_growth_formal_seed_change_proposal_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_formal_seed_change_proposal_evidence.csv"),
    "approvals": Path("data/vol_targeted_growth_formal_seed_change_proposal_approvals.csv"),
    "blockers": Path("data/vol_targeted_growth_formal_seed_change_proposal_blockers.csv"),
}

INPUT_FILES = {
    "manual_review_summary": Path("data/vol_targeted_growth_seed_change_manual_review_summary.csv"),
    "evidence_pack_summary": Path("data/vol_targeted_growth_seed_change_evidence_summary.csv"),
    "risk_reward_summary": Path("data/vol_targeted_growth_seed_change_risk_reward_summary.csv"),
    "drawdown_stress_summary": Path("data/vol_targeted_growth_seed_change_drawdown_stress_summary.csv"),
    "cost_turnover_summary": Path("data/vol_targeted_growth_seed_change_cost_turnover_summary.csv"),
    "split_stability_summary": Path("data/vol_targeted_growth_seed_change_split_stability_summary.csv"),
    "component_summary": Path("data/vol_targeted_growth_seed_change_component_sleeve_summary.csv"),
    "broker_exposure_summary": Path("data/vol_targeted_growth_seed_change_broker_exposure_summary.csv"),
    "proposal_document_summary": Path("data/vol_targeted_growth_seed_change_proposal_document_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "formal_proposal_document_only": True,
    "proposal_only": True,
    "preview_only": True,
    "seed_changed": False,
    "seed_change_proposal_created": True,
    "formal_seed_change_proposal_created": True,
    "manual_approval_recorded": False,
    "qqq100_displacement_requested": True,
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

PROPOSAL_COLUMNS = [
    "created_at",
    "proposal_section",
    "proposal_status",
    "proposal_text",
    "saved_evidence",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
APPROVAL_COLUMNS = ["approval_item", "approval_status", "details", "required_next_step", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthFormalSeedChangeProposalResult:
    output_paths: dict[str, Path]
    proposal_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    approval_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_formal_seed_change_proposal(root_dir: Path | str = ".") -> VolTargetedGrowthFormalSeedChangeProposalResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    ready = manual_review_ready(inputs)
    final_status = FINAL_STATUS if ready else BLOCKED_STATUS
    proposal_rows = build_proposal_rows(created_at, inputs, final_status)
    summary_rows = build_summary_rows(inputs, final_status)
    evidence_rows = build_evidence_rows(inputs)
    approval_rows = build_approval_rows()
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["proposal"], PROPOSAL_COLUMNS, proposal_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["approvals"], APPROVAL_COLUMNS, approval_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthFormalSeedChangeProposalResult(
        output_paths=output_paths,
        proposal_rows=proposal_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        approval_rows=approval_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_formal_seed_change_proposal(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-formal-seed-change-proposal` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth formal seed-change proposal saved display. Proposal only; no implementation approved.",
        f"final_proposal_status: {summary_value(rows, 'final_proposal_status')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"proposed_seed: {summary_value(rows, 'proposed_seed')}",
        f"proposal_decision: {summary_value(rows, 'proposal_decision')}",
        f"manual_approval_status: {summary_value(rows, 'manual_approval_status')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_changed=false; qqq100_displacement_approved=false; vol_targeted_seed_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def manual_review_ready(inputs: dict[str, list[dict[str, str]]]) -> bool:
    return (
        summary_value(inputs["manual_review_summary"], "final_manual_review_status")
        == "vol_targeted_growth_seed_change_ready_for_formal_proposal_manual_review"
        and summary_value(inputs["manual_review_summary"], "evidence_missing_count") == "0"
    )


def build_proposal_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    sections = [
        (
            "proposal_summary",
            final_status,
            f"Propose human review of replacing {INCUMBENT_SEED} with {SELECTED_CANDIDATE} as the future paper-live seed.",
            summary_value(inputs["manual_review_summary"], "manual_review_readiness"),
            NEXT_STEP,
        ),
        (
            "case_for_change",
            "saved_evidence_supports_human_review",
            "Saved risk/reward, drawdown, split-stability, component, broker-exposure, and proposal-document evidence is complete enough for manual review.",
            evidence_context(inputs),
            NEXT_STEP,
        ),
        (
            "case_against_automatic_change",
            "manual_approval_required",
            "The candidate is more complex than QQQ100 and includes high-growth, crypto, and defensive sleeve dependencies, so automatic seed replacement is blocked.",
            component_context(inputs),
            "human_review_complexity_before_approval",
        ),
        (
            "implementation_boundary",
            "implementation_not_added",
            "No action preview implementation, seed switch, order instruction, paper execution, live execution, repeat order, or schedule is created here.",
            "all_execution_flags_false",
            "separate_implementation_checkpoint_required_after_manual_approval",
        ),
    ]
    return [
        {
            "created_at": created_at,
            "proposal_section": section,
            "proposal_status": status,
            "proposal_text": text,
            "saved_evidence": evidence,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for section, status, text, evidence, next_step in sections
    ]


def build_summary_rows(inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("final_proposal_status", final_status, "Formal proposal document status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current seed remains unchanged."),
        ("proposed_seed", SELECTED_CANDIDATE, "Candidate proposed for human review only."),
        ("proposal_decision", "proposal_created_for_manual_review_not_approved" if final_status == FINAL_STATUS else "proposal_blocked_manual_review_not_ready", "Proposal document decision."),
        ("manual_approval_status", "manual_approval_not_recorded", "No human approval is recorded by this command."),
        ("seed_change_decision", "seed_not_changed_qqq100_retained", "No seed change is implemented."),
        ("source_manual_review_status", summary_value(inputs["manual_review_summary"], "final_manual_review_status") or "missing_manual_review_checkpoint", "Saved manual-review checkpoint status."),
        ("evidence_missing_count", summary_value(inputs["manual_review_summary"], "evidence_missing_count") or "unavailable", "Saved evidence missing count."),
        ("largest_blocker", "manual_approval_required_before_implementation" if final_status == FINAL_STATUS else "manual_review_checkpoint_not_ready", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if final_status == FINAL_STATUS else "complete_manual_review_checkpoint_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This proposal reads saved outputs only and does not call Alpaca."))
    rows.append(("seed_changed_now", "false", "This proposal does not change the seed."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_approval_rows() -> list[dict[str, Any]]:
    rows = [
        ("human_seed_change_approval", "not_recorded", "A separate explicit human approval is required before implementation.", NEXT_STEP),
        ("implementation_approval", "not_approved", "No implementation, action preview, or execution wiring is approved.", "separate_implementation_checkpoint_required"),
        ("execution_approval", "not_approved", "No paper execution, live trading, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    return [{"approval_item": n, "approval_status": s, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, d, ns in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("manual_approval_required", "blocked", "critical", "Human approval is required before any seed-change implementation.", NEXT_STEP),
        ("seed_not_changed", "blocked", "critical", "QQQ100 remains the active seed.", "separate_seed_change_implementation_required_after_approval"),
        ("implementation_not_added", "blocked", "critical", "No action preview or execution implementation is added.", "separate_implementation_checkpoint_required"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("manual_review_not_ready", "blocked", "critical", "Manual-review checkpoint is missing or not ready.", "complete_manual_review_checkpoint_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth formal seed-change proposal complete. Proposal only; no implementation approved.",
        f"final_proposal_status={summary_value(summary_rows, 'final_proposal_status')}",
        f"proposal_decision={summary_value(summary_rows, 'proposal_decision')}",
        f"manual_approval_status={summary_value(summary_rows, 'manual_approval_status')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_proposal={output_paths['proposal']}",
        "seed_changed=false; qqq100_displacement_approved=false; vol_targeted_seed_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def evidence_context(inputs: dict[str, list[dict[str, str]]]) -> str:
    return (
        f"risk_reward={summary_value(inputs['risk_reward_summary'], 'final_risk_reward_status') or 'missing'}; "
        f"drawdown={summary_value(inputs['drawdown_stress_summary'], 'final_drawdown_stress_status') or 'missing'}; "
        f"split={summary_value(inputs['split_stability_summary'], 'final_split_stability_status') or 'missing'}; "
        f"broker={summary_value(inputs['broker_exposure_summary'], 'final_broker_exposure_status') or 'missing'}"
    )


def component_context(inputs: dict[str, list[dict[str, str]]]) -> str:
    return summary_value(inputs["component_summary"], "final_component_sleeve_status") or "missing_component_sleeve_review"


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
