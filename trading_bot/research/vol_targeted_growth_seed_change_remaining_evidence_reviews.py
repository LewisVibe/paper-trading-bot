"""Saved-output remaining evidence reviews for volatility seed-change work."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"

COMPONENT_STATUS = "vol_targeted_growth_component_sleeve_evidence_created_manual_review_required"
ACTION_STATUS = "vol_targeted_growth_action_preview_design_evidence_created_manual_review_required"
PROPOSAL_STATUS = "vol_targeted_growth_seed_change_proposal_document_draft_created_manual_review_required"
BROKER_EXPOSURE_STATUS = "vol_targeted_growth_broker_exposure_evidence_created_manual_review_required"

OUTPUT_FILES = {
    "component_review": Path("data/vol_targeted_growth_seed_change_component_sleeve_review.csv"),
    "component_summary": Path("data/vol_targeted_growth_seed_change_component_sleeve_summary.csv"),
    "component_evidence": Path("data/vol_targeted_growth_seed_change_component_sleeve_evidence.csv"),
    "component_blockers": Path("data/vol_targeted_growth_seed_change_component_sleeve_blockers.csv"),
    "action_review": Path("data/vol_targeted_growth_seed_change_action_preview_design.csv"),
    "action_summary": Path("data/vol_targeted_growth_seed_change_action_preview_design_summary.csv"),
    "action_evidence": Path("data/vol_targeted_growth_seed_change_action_preview_design_evidence.csv"),
    "action_blockers": Path("data/vol_targeted_growth_seed_change_action_preview_design_blockers.csv"),
    "proposal_review": Path("data/vol_targeted_growth_seed_change_proposal_document.csv"),
    "proposal_summary": Path("data/vol_targeted_growth_seed_change_proposal_document_summary.csv"),
    "proposal_evidence": Path("data/vol_targeted_growth_seed_change_proposal_document_evidence.csv"),
    "proposal_blockers": Path("data/vol_targeted_growth_seed_change_proposal_document_blockers.csv"),
    "broker_review": Path("data/vol_targeted_growth_seed_change_broker_exposure_review.csv"),
    "broker_summary": Path("data/vol_targeted_growth_seed_change_broker_exposure_summary.csv"),
    "broker_evidence": Path("data/vol_targeted_growth_seed_change_broker_exposure_evidence.csv"),
    "broker_blockers": Path("data/vol_targeted_growth_seed_change_broker_exposure_blockers.csv"),
}

INPUT_FILES = {
    "proposal_preview_summary": Path("data/vol_targeted_growth_proposal_preview_summary.csv"),
    "candidate_discussion_summary": Path("data/vol_targeted_growth_candidate_discussion_summary.csv"),
    "gate_review_summary": Path("data/vol_targeted_growth_gate_review_summary.csv"),
    "portfolio_risk_review_summary": Path("data/vol_targeted_growth_portfolio_risk_review_summary.csv"),
    "seed_change_evidence_summary": Path("data/vol_targeted_growth_seed_change_evidence_summary.csv"),
    "risk_reward_summary": Path("data/vol_targeted_growth_seed_change_risk_reward_summary.csv"),
    "drawdown_stress_summary": Path("data/vol_targeted_growth_seed_change_drawdown_stress_summary.csv"),
    "cost_turnover_summary": Path("data/vol_targeted_growth_seed_change_cost_turnover_summary.csv"),
    "split_stability_summary": Path("data/vol_targeted_growth_seed_change_split_stability_summary.csv"),
    "qqq100_followup_policy_summary": Path("data/qqq100_followup_policy_summary.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "proposal_only": True,
    "preview_only": True,
    "component_sleeve_review_only": False,
    "action_preview_design_only": False,
    "proposal_document_draft_only": False,
    "broker_exposure_review_only": False,
    "seed_changed": False,
    "seed_change_proposal_created": False,
    "formal_seed_change_proposal_created": False,
    "proposal_document_draft_saved": False,
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

REVIEW_COLUMNS = [
    "created_at",
    "review_item",
    "review_status",
    "candidate_name",
    "saved_evidence",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class RemainingEvidenceReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_component_sleeve_review(root_dir: Path | str = ".") -> RemainingEvidenceReviewResult:
    return generate_review(
        root_dir,
        prefix="component",
        final_key="final_component_sleeve_status",
        final_status=COMPONENT_STATUS,
        true_flag="component_sleeve_review_only",
        largest_blocker="component_sleeves_research_only_and_not_approved_for_execution",
        next_step="manual_review_high_growth_crypto_defensive_sleeves_before_seed_change",
        rows=[
            ("high_growth_sleeve_boundary", "research_only_manual_review_required", "High-growth sleeve remains research-only and not approved for paper-live execution."),
            ("crypto_sleeve_boundary", "research_only_manual_review_required", "Crypto sleeve remains research-only and not approved for paper-live execution."),
            ("defensive_sleeve_boundary", "research_only_manual_review_required", "Defensive sleeve role needs manual review before seed displacement."),
        ],
    )


def generate_vol_targeted_growth_seed_change_action_preview_design(root_dir: Path | str = ".") -> RemainingEvidenceReviewResult:
    return generate_review(
        root_dir,
        prefix="action",
        final_key="final_action_preview_design_status",
        final_status=ACTION_STATUS,
        true_flag="action_preview_design_only",
        largest_blocker="action_preview_design_saved_but_not_implemented",
        next_step="manual_review_non_executable_action_preview_design_before_any_implementation",
        rows=[
            ("allowed_scope", "non_executable_design_only", "Future action preview may describe target sleeves, but must not include order side, quantity, type, account, API key, webhook, token, or order ID fields."),
            ("implementation_boundary", "preview_implementation_not_added", "This checkpoint does not add action-preview behavior or executable order instructions."),
            ("execution_boundary", "execution_blocked", "No paper execution, live trading, repeat order, or scheduling is approved."),
        ],
    )


def generate_vol_targeted_growth_seed_change_proposal_document(root_dir: Path | str = ".") -> RemainingEvidenceReviewResult:
    return generate_review(
        root_dir,
        prefix="proposal",
        final_key="final_proposal_document_status",
        final_status=PROPOSAL_STATUS,
        true_flag="proposal_document_draft_only",
        largest_blocker="proposal_document_draft_only_broker_exposure_context_still_manual_review",
        next_step="manual_review_broker_exposure_context_before_any_seed_change_proposal",
        rows=[
            ("proposal_document_scope", "draft_checkpoint_only", "This is a saved proposal-document checkpoint, not a formal seed-change proposal approval."),
            ("remaining_blocker", "broker_exposure_context_manual_review_required", "Read-only broker exposure context remains the key operational blocker."),
            ("seed_boundary", "qqq100_seed_retained", "QQQ100 remains the incumbent paper-live seed."),
        ],
        extra_flags={"proposal_document_draft_saved": True},
    )


def generate_vol_targeted_growth_seed_change_broker_exposure_review(root_dir: Path | str = ".") -> RemainingEvidenceReviewResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    comparison_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status") or "missing_broker_comparison"
    read_status = summary_value(inputs["broker_comparison_summary"], "broker_position_read_status") or "missing_broker_read_status"
    return generate_review(
        root_dir,
        prefix="broker",
        final_key="final_broker_exposure_status",
        final_status=BROKER_EXPOSURE_STATUS,
        true_flag="broker_exposure_review_only",
        largest_blocker="broker_exposure_review_present_but_seed_change_still_not_approved",
        next_step="manual_review_complete_evidence_before_formal_seed_change_proposal",
        rows=[
            ("saved_broker_comparison_status", "saved_readonly_broker_context_available_manual_review_required", f"comparison_status={comparison_status}; broker_position_read_status={read_status}"),
            ("fresh_broker_read_boundary", "no_fresh_broker_read_performed", "This checkpoint reads saved broker-comparison output only and does not call Alpaca or read positions now."),
            ("seed_boundary", "qqq100_seed_retained", "Broker exposure evidence does not displace QQQ100 or approve any order."),
        ],
    )


def show_vol_targeted_growth_seed_change_component_sleeve_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_review(root_dir, "component", "final_component_sleeve_status", "--vol-targeted-growth-seed-change-component-sleeve-review")


def show_vol_targeted_growth_seed_change_action_preview_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_review(root_dir, "action", "final_action_preview_design_status", "--vol-targeted-growth-seed-change-action-preview-design")


def show_vol_targeted_growth_seed_change_proposal_document(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_review(root_dir, "proposal", "final_proposal_document_status", "--vol-targeted-growth-seed-change-proposal-document")


def show_vol_targeted_growth_seed_change_broker_exposure_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_review(root_dir, "broker", "final_broker_exposure_status", "--vol-targeted-growth-seed-change-broker-exposure-review")


def generate_review(
    root_dir: Path | str,
    *,
    prefix: str,
    final_key: str,
    final_status: str,
    true_flag: str,
    largest_blocker: str,
    next_step: str,
    rows: list[tuple[str, str, str]],
    extra_flags: dict[str, bool] | None = None,
) -> RemainingEvidenceReviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    flags = review_flags(true_flag, extra_flags)
    review_rows = [
        {
            "created_at": created_at,
            "review_item": item,
            "review_status": status,
            "candidate_name": SELECTED_CANDIDATE,
            "saved_evidence": evidence,
            "interpretation": evidence,
            "required_next_step": next_step,
            **flags,
        }
        for item, status, evidence in rows
    ]
    summary_rows = build_summary_rows(final_key, final_status, largest_blocker, next_step, inputs, flags)
    evidence_rows = build_evidence_rows(inputs, flags)
    blocker_rows = build_blocker_rows(largest_blocker, next_step, flags)
    output_paths = output_paths_for(prefix, root)
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return RemainingEvidenceReviewResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(final_key, summary_rows, output_paths),
    )


def show_review(root_dir: Path | str, prefix: str, final_key: str, command: str) -> tuple[int, list[str]]:
    path = Path(root_dir) / OUTPUT_FILES[f"{prefix}_summary"]
    if not path.exists():
        return 1, [f"Run `python bot.py {command}` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change evidence saved display. Evidence only; no seed change approved.",
        f"{final_key}: {summary_value(rows, final_key)}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"candidate_under_review: {summary_value(rows, 'candidate_under_review')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_summary_rows(
    final_key: str,
    final_status: str,
    largest_blocker: str,
    next_step: str,
    inputs: dict[str, list[dict[str, str]]],
    flags: dict[str, bool],
) -> list[dict[str, Any]]:
    rows = [
        (final_key, final_status, "Saved evidence checkpoint status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current paper-live seed remains unchanged."),
        ("candidate_under_review", SELECTED_CANDIDATE, "Volatility-targeted candidate under manual review."),
        ("seed_change_evidence_context", summary_value(inputs["seed_change_evidence_summary"], "final_evidence_pack_status") or "missing_seed_change_evidence_pack", "Saved evidence-pack context."),
        ("proposal_preview_context", summary_value(inputs["proposal_preview_summary"], "final_proposal_preview_status") or "missing_proposal_preview_context", "Saved proposal-preview context."),
        ("largest_blocker", largest_blocker, "Primary blocker."),
        ("recommended_next_step", next_step, "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **flags} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]], flags: dict[str, bool]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("broker_read_now", "false", "This review reads saved outputs only and does not call Alpaca."))
    rows.append(("order_instruction_created_now", "false", "This review does not create executable order instructions."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **flags} for n, v, d in rows]


def build_blocker_rows(largest_blocker: str, next_step: str, flags: dict[str, bool]) -> list[dict[str, Any]]:
    rows = [
        (largest_blocker, "blocked", "high", "Manual review remains required before any seed-change proposal can advance.", next_step),
        ("qqq100_displacement_not_approved", "blocked", "critical", "QQQ100 remains the incumbent seed.", next_step),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **flags} for n, s, sev, d, ns in rows]


def build_summary_lines(final_key: str, summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth seed-change evidence checkpoint complete. Evidence only; no seed change approved.",
        f"{final_key}={summary_value(summary_rows, final_key)}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_review={output_paths['review']}",
        "seed_change_proposal_created=false; qqq100_displacement_approved=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def review_flags(true_flag: str, extra_flags: dict[str, bool] | None = None) -> dict[str, bool]:
    flags = dict(SAFETY_FLAGS)
    flags[true_flag] = True
    for key, value in (extra_flags or {}).items():
        flags[key] = value
    return flags


def output_paths_for(prefix: str, root: Path) -> dict[str, Path]:
    return {
        "review": root / OUTPUT_FILES[f"{prefix}_review"],
        "summary": root / OUTPUT_FILES[f"{prefix}_summary"],
        "evidence": root / OUTPUT_FILES[f"{prefix}_evidence"],
        "blockers": root / OUTPUT_FILES[f"{prefix}_blockers"],
    }


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
