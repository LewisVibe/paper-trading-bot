"""Saved-output dry-run diff for a future volatility seed switch."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
INCUMBENT_SEED = "qqq_100_trend_gate"
FINAL_STATUS = "vol_targeted_growth_seed_change_dry_run_diff_created_manual_review_required"
BLOCKED_STATUS = "vol_targeted_growth_seed_change_dry_run_diff_blocked_missing_implementation_design"
NEXT_STEP = "manual_review_dry_run_diff_before_seed_switch_code_change"

OUTPUT_FILES = {
    "diff": Path("data/vol_targeted_growth_seed_change_dry_run_diff.csv"),
    "summary": Path("data/vol_targeted_growth_seed_change_dry_run_diff_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_seed_change_dry_run_diff_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_seed_change_dry_run_diff_blockers.csv"),
}

INPUT_FILES = {
    "implementation_design_summary": Path("data/vol_targeted_growth_seed_change_implementation_design_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "dry_run_diff_only": True,
    "implementation_plan_only": True,
    "preview_only": True,
    "seed_changed": False,
    "seed_change_implemented": False,
    "active_seed_changed": False,
    "qqq100_displacement_implemented": False,
    "qqq100_displacement_approved": False,
    "vol_targeted_seed_approved": False,
    "files_modified_by_diff": False,
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

DIFF_COLUMNS = [
    "created_at",
    "target_file",
    "target_area",
    "current_reference",
    "future_reference",
    "proposed_change_type",
    "dry_run_status",
    "risk_level",
    "required_review",
    "implementation_boundary",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthSeedChangeDryRunDiffResult:
    output_paths: dict[str, Path]
    diff_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_seed_change_dry_run_diff(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthSeedChangeDryRunDiffResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    design_ready = implementation_design_ready(inputs)
    final_status = FINAL_STATUS if design_ready else BLOCKED_STATUS
    diff_rows = build_diff_rows(created_at, final_status)
    summary_rows = build_summary_rows(inputs, diff_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["diff"], DIFF_COLUMNS, diff_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthSeedChangeDryRunDiffResult(
        output_paths=output_paths,
        diff_rows=diff_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_seed_change_dry_run_diff(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-seed-change-dry-run-diff` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth seed-change dry-run diff saved display. Dry-run only; no files changed and no execution approved.",
        f"final_dry_run_diff_status: {summary_value(rows, 'final_dry_run_diff_status')}",
        f"incumbent_seed: {summary_value(rows, 'incumbent_seed')}",
        f"candidate_seed: {summary_value(rows, 'candidate_seed')}",
        f"dry_run_scope: {summary_value(rows, 'dry_run_scope')}",
        f"future_change_count: {summary_value(rows, 'future_change_count')}",
        f"seed_change_decision: {summary_value(rows, 'seed_change_decision')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "files_modified_by_diff=false; seed_changed=false; active_seed_changed=false; qqq100_displacement_approved=false; vol_targeted_seed_approved=false; action_preview_added=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def implementation_design_ready(inputs: dict[str, list[dict[str, str]]]) -> bool:
    rows = inputs["implementation_design_summary"]
    return (
        summary_value(rows, "final_design_status")
        == "vol_targeted_growth_seed_change_implementation_design_created_manual_review_required"
        and summary_value(rows, "implementation_scope") == "design_seed_change_implementation_without_execution"
        and summary_value(rows, "seed_change_decision") == "seed_not_changed_qqq100_retained_until_separate_implementation"
    )


def build_diff_rows(created_at: str, final_status: str) -> list[dict[str, Any]]:
    status = "future_change_identified_not_applied" if final_status == FINAL_STATUS else "blocked_missing_implementation_design"
    rows = [
        (
            "trading_bot/research/paper_live_monitoring_status.py",
            "active paper-live status labels",
            INCUMBENT_SEED,
            SELECTED_CANDIDATE,
            "replace_active_seed_reference_after_manual_review",
            "critical",
            "manual_review_active_seed_status_before_code_change",
            "This dry-run does not edit the monitoring status module.",
        ),
        (
            "trading_bot/research/vps_daily_monitoring_summary.py",
            "daily VPS/Hermes status summary",
            "QQQ100 current seed wording",
            "volatility-targeted seed wording plus retained QQQ100 prior-seed context",
            "update_status_summary_after_manual_review",
            "critical",
            "manual_review_monitoring_output_before_code_change",
            "This dry-run does not edit VPS monitoring output.",
        ),
        (
            "trading_bot/research/paper_live_promotion_ladder_status.py",
            "promotion ladder current-seed row",
            "QQQ100 as only current seed",
            "volatility candidate as proposed new seed with QQQ100 as previous seed",
            "replace_ladder_seed_label_after_manual_review",
            "critical",
            "manual_review_ladder_state_before_code_change",
            "This dry-run does not edit ladder state.",
        ),
        (
            "trading_bot/research/paper_live_checklist_status.py",
            "paper-live checklist status",
            "QQQ100-only paper-live seed",
            "volatility-targeted seed-change implemented status",
            "update_checklist_checkpoint_after_manual_review",
            "high",
            "manual_review_checklist_before_code_change",
            "This dry-run does not edit checklist status.",
        ),
        (
            "README.md and docs/CURRENT_STATE.md",
            "human-facing current-state docs",
            "QQQ100 remains active seed",
            "volatility candidate becomes active seed after separate implementation",
            "update_docs_after_code_change_only",
            "high",
            "manual_review_docs_before_code_change",
            "This dry-run does not edit docs beyond documenting the dry-run checkpoint.",
        ),
        (
            "scripts/verify_command_inventory.py and new focused verifier",
            "safety verification",
            "seed-change design commands only",
            "future seed-switch command/verifier if implementation is approved",
            "add_guardrail_verifier_before_any_switch",
            "critical",
            "manual_review_verifier_before_code_change",
            "This dry-run does not add a seed-switch implementation verifier.",
        ),
        (
            "execution and order modules",
            "explicit non-target",
            "no direct strategy execution wiring",
            "no direct strategy execution wiring",
            "must_not_change",
            "critical",
            "do_not_touch_execution_paths",
            "This dry-run forbids execution/order changes.",
        ),
    ]
    return [
        {
            "created_at": created_at,
            "target_file": target_file,
            "target_area": area,
            "current_reference": current,
            "future_reference": future,
            "proposed_change_type": change_type,
            "dry_run_status": status,
            "risk_level": risk,
            "required_review": review,
            "implementation_boundary": boundary,
            "required_next_step": NEXT_STEP if final_status == FINAL_STATUS else "run_implementation_design_first",
            **SAFETY_FLAGS,
        }
        for target_file, area, current, future, change_type, risk, review, boundary in rows
    ]


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    diff_rows: list[dict[str, Any]],
    final_status: str,
) -> list[dict[str, Any]]:
    ready = final_status == FINAL_STATUS
    rows = [
        ("final_dry_run_diff_status", final_status, "Dry-run diff checkpoint status."),
        ("incumbent_seed", INCUMBENT_SEED, "Current active paper-live seed remains unchanged."),
        ("candidate_seed", SELECTED_CANDIDATE, "Candidate named for a possible future separate seed-switch implementation."),
        ("dry_run_scope", "list_future_seed_switch_changes_without_applying_them" if ready else "blocked_missing_implementation_design", "Scope of this dry-run diff."),
        ("future_change_count", str(len(diff_rows)), "Number of proposed future change rows."),
        ("seed_change_decision", "seed_not_changed_dry_run_diff_only", "No seed switch is implemented by this command."),
        ("source_implementation_design_status", summary_value(inputs["implementation_design_summary"], "final_design_status") or "missing_implementation_design", "Saved implementation design status."),
        ("largest_blocker", "manual_review_required_before_seed_switch_code_change" if ready else "missing_implementation_design", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP if ready else "run_implementation_design_first", "Next safe step."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        (
            "implementation_design_summary_input",
            f"{INPUT_FILES['implementation_design_summary']}; rows={len(inputs['implementation_design_summary'])}",
            "Saved implementation design summary row count.",
        ),
        ("files_modified_by_dry_run", "false", "This checkpoint writes only its own ignored report outputs."),
        ("seed_changed_now", "false", "This dry-run does not change the seed."),
        ("broker_read_now", "false", "This dry-run reads saved outputs only and does not call Alpaca."),
    ]
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("seed_change_not_implemented", "blocked", "critical", "This is a dry-run diff only; QQQ100 remains active.", "separate_seed_switch_code_change_required"),
        ("files_not_modified", "blocked", "critical", "No target files are edited by this dry-run diff.", NEXT_STEP),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
        ("order_instructions_not_allowed", "blocked", "critical", "No side, quantity, order type, account, or secret fields are created.", "future_preview_schema_must_stay_non_executable"),
    ]
    if final_status == BLOCKED_STATUS:
        rows.insert(0, ("implementation_design_missing", "blocked", "critical", "Saved implementation design is missing or not ready.", "run_implementation_design_first"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth seed-change dry-run diff complete. Dry-run only; no files changed, no seed change, and no execution approved.",
        f"final_dry_run_diff_status={summary_value(summary_rows, 'final_dry_run_diff_status')}",
        f"dry_run_scope={summary_value(summary_rows, 'dry_run_scope')}",
        f"future_change_count={summary_value(summary_rows, 'future_change_count')}",
        f"seed_change_decision={summary_value(summary_rows, 'seed_change_decision')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_diff={output_paths['diff']}",
        "files_modified_by_diff=false; seed_changed=false; active_seed_changed=false; qqq100_displacement_approved=false; vol_targeted_seed_approved=false; action_preview_added=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


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
