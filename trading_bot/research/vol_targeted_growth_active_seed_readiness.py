"""Saved-output readiness check for the active volatility-targeted seed.

This report checks whether the saved report/status evidence around the active
volatility-targeted seed is present and internally consistent. It does not read
broker positions, refresh market data, create order instructions, schedule
anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_SEED = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"
FINAL_STATUS = "vol_targeted_growth_active_seed_monitoring_ready_manual_review_required"
INCOMPLETE_STATUS = "vol_targeted_growth_active_seed_monitoring_incomplete_manual_review_required"
NEXT_STEP = "monitor_active_vol_targeted_seed_saved_evidence_before_any_action_preview_or_execution"

OUTPUT_FILES = {
    "readiness": Path("data/vol_targeted_growth_active_seed_readiness.csv"),
    "summary": Path("data/vol_targeted_growth_active_seed_readiness_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_active_seed_readiness_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_active_seed_readiness_blockers.csv"),
}

INPUT_FILES = {
    "paper_live_monitoring_status": Path("data/paper_live_monitoring_status.csv"),
    "paper_live_promotion_ladder_status": Path("data/paper_live_promotion_ladder_status_summary.csv"),
    "paper_live_checklist_status": Path("data/paper_live_checklist_status_summary.csv"),
    "vps_daily_monitoring_summary": Path("data/vps_daily_monitoring_summary.csv"),
    "proposal_preview_summary": Path("data/vol_targeted_growth_proposal_preview_summary.csv"),
    "risk_reward_summary": Path("data/vol_targeted_growth_seed_change_risk_reward_summary.csv"),
    "drawdown_stress_summary": Path("data/vol_targeted_growth_seed_change_drawdown_stress_summary.csv"),
    "cost_turnover_summary": Path("data/vol_targeted_growth_seed_change_cost_turnover_summary.csv"),
    "split_stability_summary": Path("data/vol_targeted_growth_seed_change_split_stability_summary.csv"),
    "component_sleeve_summary": Path("data/vol_targeted_growth_seed_change_component_sleeve_summary.csv"),
    "broker_exposure_summary": Path("data/vol_targeted_growth_seed_change_broker_exposure_summary.csv"),
    "manual_approval_summary": Path("data/vol_targeted_growth_seed_change_manual_approval_summary.csv"),
    "implementation_design_summary": Path("data/vol_targeted_growth_seed_change_implementation_design_summary.csv"),
    "dry_run_diff_summary": Path("data/vol_targeted_growth_seed_change_dry_run_diff_summary.csv"),
}

EXPECTED_STATUSES = {
    "proposal_preview_summary": ("final_proposal_preview_status", "vol_targeted_growth_proposal_preview_created_saved_output_only"),
    "risk_reward_summary": ("final_risk_reward_status", "vol_targeted_growth_risk_reward_evidence_created_manual_review_required"),
    "drawdown_stress_summary": ("final_drawdown_stress_status", "vol_targeted_growth_drawdown_stress_evidence_created_manual_review_required"),
    "cost_turnover_summary": ("final_cost_turnover_status", "vol_targeted_growth_cost_turnover_evidence_created_manual_review_required"),
    "split_stability_summary": ("final_split_stability_status", "vol_targeted_growth_split_stability_evidence_created_manual_review_required"),
    "component_sleeve_summary": ("final_component_sleeve_status", "vol_targeted_growth_component_sleeve_evidence_created_manual_review_required"),
    "broker_exposure_summary": ("final_broker_exposure_status", "vol_targeted_growth_broker_exposure_evidence_created_manual_review_required"),
    "manual_approval_summary": ("final_manual_approval_status", "vol_targeted_growth_seed_change_manual_approval_recorded_implementation_required"),
    "implementation_design_summary": ("final_design_status", "vol_targeted_growth_seed_change_implementation_design_created_manual_review_required"),
    "dry_run_diff_summary": ("final_dry_run_diff_status", "vol_targeted_growth_seed_change_dry_run_diff_created_manual_review_required"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "monitoring_only": True,
    "manual_review_only": True,
    "active_seed_readiness_only": True,
    "preview_only": True,
    "active_seed_status_changed": False,
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

READINESS_COLUMNS = [
    "created_at",
    "check_name",
    "status",
    "risk_level",
    "saved_source",
    "evidence_value",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthActiveSeedReadinessResult:
    output_paths: dict[str, Path]
    readiness_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_active_seed_readiness(root_dir: Path | str = ".") -> VolTargetedGrowthActiveSeedReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    readiness_rows = build_readiness_rows(created_at, inputs)
    final_status = determine_final_status(readiness_rows)
    summary_rows = build_summary_rows(readiness_rows, final_status)
    evidence_rows = build_evidence_rows(inputs)
    blocker_rows = build_blocker_rows(readiness_rows, final_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["readiness"], READINESS_COLUMNS, readiness_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthActiveSeedReadinessResult(
        output_paths=output_paths,
        readiness_rows=readiness_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_active_seed_readiness(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-active-seed-readiness` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth active-seed readiness saved display. Monitoring/report only; no orders approved.",
        f"final_active_seed_readiness_status: {summary_value(rows, 'final_active_seed_readiness_status')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"previous_seed: {summary_value(rows, 'previous_seed')}",
        f"readiness_pass_count: {summary_value(rows, 'readiness_pass_count')}",
        f"readiness_warning_count: {summary_value(rows, 'readiness_warning_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "action_preview_added=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false; followup_order_approved=false; repeat_execution_approved=false",
    ]


def build_readiness_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        check_row(
            created_at,
            "active_seed_status_label",
            "pass" if summary_value(inputs["paper_live_monitoring_status"], "active_strategy") == ACTIVE_SEED else "warning",
            "critical",
            str(INPUT_FILES["paper_live_monitoring_status"]),
            summary_value(inputs["paper_live_monitoring_status"], "active_strategy") or "missing_active_strategy",
            "Saved paper-live monitoring status should name the volatility-targeted seed as active.",
            "refresh_paper_live_monitoring_status" if summary_value(inputs["paper_live_monitoring_status"], "active_strategy") != ACTIVE_SEED else NEXT_STEP,
        ),
        check_row(
            created_at,
            "active_seed_ticker_label",
            "pass" if summary_value(inputs["paper_live_monitoring_status"], "active_ticker") == ACTIVE_TICKER else "warning",
            "critical",
            str(INPUT_FILES["paper_live_monitoring_status"]),
            summary_value(inputs["paper_live_monitoring_status"], "active_ticker") or "missing_active_ticker",
            "Saved paper-live monitoring status should use the multi-sleeve status ticker label.",
            "refresh_paper_live_monitoring_status" if summary_value(inputs["paper_live_monitoring_status"], "active_ticker") != ACTIVE_TICKER else NEXT_STEP,
        ),
        check_row(
            created_at,
            "previous_seed_context_retained",
            "pass" if previous_seed_context_ok(inputs["paper_live_monitoring_status"]) else "warning",
            "high",
            str(INPUT_FILES["paper_live_monitoring_status"]),
            previous_seed_value(inputs["paper_live_monitoring_status"]),
            "QQQ100 should remain visible as previous-seed context.",
            "refresh_paper_live_monitoring_status" if not previous_seed_context_ok(inputs["paper_live_monitoring_status"]) else NEXT_STEP,
        ),
        check_row(
            created_at,
            "promotion_ladder_status_consistent",
            "pass" if summary_value(inputs["paper_live_promotion_ladder_status"], "current_seed") == f"{ACTIVE_SEED}:{ACTIVE_TICKER}" else "warning",
            "high",
            str(INPUT_FILES["paper_live_promotion_ladder_status"]),
            summary_value(inputs["paper_live_promotion_ladder_status"], "current_seed") or "missing_current_seed",
            "Promotion ladder status should identify the active volatility seed.",
            "refresh_paper_live_promotion_ladder_status",
        ),
        check_row(
            created_at,
            "checklist_status_consistent",
            "pass" if summary_value(inputs["paper_live_checklist_status"], "active_strategy") == ACTIVE_SEED else "warning",
            "high",
            str(INPUT_FILES["paper_live_checklist_status"]),
            summary_value(inputs["paper_live_checklist_status"], "active_strategy") or "missing_checklist_active_strategy",
            "Paper-live checklist should identify the active volatility seed.",
            "refresh_paper_live_checklist_status",
        ),
    ]
    for source_name, (status_key, expected_status) in EXPECTED_STATUSES.items():
        value = summary_value(inputs[source_name], status_key) or f"missing_{status_key}"
        rows.append(
            check_row(
                created_at,
                source_name,
                "pass" if value == expected_status else "warning",
                "high",
                str(INPUT_FILES[source_name]),
                value,
                f"Saved evidence should contain {status_key}={expected_status}.",
                "refresh_or_review_saved_volatility_evidence" if value != expected_status else NEXT_STEP,
            )
        )
    rows.append(
        check_row(
            created_at,
            "execution_boundary",
            "pass",
            "critical",
            "static_safety_flags",
            "all_execution_and_scheduling_flags_false",
            "This readiness checkpoint does not approve action preview, orders, execution, or scheduling.",
            "keep_monitoring_only_until_separate_manual_approval",
        )
    )
    return rows


def determine_final_status(readiness_rows: list[dict[str, Any]]) -> str:
    return FINAL_STATUS if all(row.get("status") == "pass" for row in readiness_rows) else INCOMPLETE_STATUS


def build_summary_rows(readiness_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    pass_count = sum(1 for row in readiness_rows if row.get("status") == "pass")
    warning_count = sum(1 for row in readiness_rows if row.get("status") == "warning")
    largest_blocker = "none_monitor_saved_evidence_ready_for_review" if warning_count == 0 else first_warning(readiness_rows)
    next_step = NEXT_STEP if warning_count == 0 else "refresh_missing_or_stale_saved_volatility_seed_evidence"
    rows = [
        ("final_active_seed_readiness_status", final_status, "Saved-output readiness status for active volatility seed monitoring."),
        ("active_seed", ACTIVE_SEED, "Active paper-live status seed."),
        ("active_ticker", ACTIVE_TICKER, "Active paper-live status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed retained as context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker retained as context."),
        ("readiness_check_count", str(len(readiness_rows)), "Total checks."),
        ("readiness_pass_count", str(pass_count), "Passing checks."),
        ("readiness_warning_count", str(warning_count), "Warning checks."),
        ("largest_blocker", largest_blocker, "Largest missing or stale saved-evidence blocker."),
        ("recommended_next_step", next_step, "Next safe monitoring step, never an order instruction."),
        ("action_preview_added", "False", "No action preview is added by this checkpoint."),
        ("order_instructions_created", "False", "No order instructions are created."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.extend(
        [
            ("broker_read_now", "false", "This readiness check reads saved outputs only and does not call Alpaca."),
            ("market_data_refreshed_now", "false", "This readiness check does not refresh yfinance or other market data."),
            ("orders_or_schedules_created_now", "false", "This readiness check does not create orders, order instructions, or schedules."),
        ]
    )
    return [{"evidence_name": n, "evidence_value": v, "details": d, **SAFETY_FLAGS} for n, v, d in rows]


def build_blocker_rows(readiness_rows: list[dict[str, Any]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
        ("action_preview_not_added", "blocked", "critical", "This checkpoint does not add or approve action preview.", "separate_manual_action_preview_review_required"),
        ("order_capable_scheduling_not_approved", "blocked", "critical", "Order-capable commands must never be scheduled.", "never_schedule_order_capable_commands"),
    ]
    for row in readiness_rows:
        if row.get("status") != "pass":
            rows.append(
                (
                    f"warning_{row.get('check_name')}",
                    "manual_review_required",
                    str(row.get("risk_level", "high")),
                    str(row.get("interpretation", "")),
                    str(row.get("required_next_step", "manual_review_required")),
                )
            )
    if final_status == INCOMPLETE_STATUS:
        rows.insert(0, ("saved_evidence_incomplete", "manual_review_required", "high", "One or more saved active-seed evidence checks is missing or stale.", "refresh_missing_or_stale_saved_volatility_seed_evidence"))
    return [{"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **SAFETY_FLAGS} for n, s, sev, d, ns in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth active-seed readiness complete. Monitoring/report only; no orders or scheduling approved.",
        f"final_active_seed_readiness_status={summary_value(summary_rows, 'final_active_seed_readiness_status')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"active_ticker={summary_value(summary_rows, 'active_ticker')}",
        f"previous_seed={summary_value(summary_rows, 'previous_seed')}",
        f"readiness_pass_count={summary_value(summary_rows, 'readiness_pass_count')}",
        f"readiness_warning_count={summary_value(summary_rows, 'readiness_warning_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_readiness={output_paths['readiness']}",
        "action_preview_added=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def check_row(created_at: str, name: str, status: str, risk: str, source: str, value: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": name,
        "status": status,
        "risk_level": risk,
        "saved_source": source,
        "evidence_value": value,
        "interpretation": interpretation,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def previous_seed_context_ok(rows: list[dict[str, str]]) -> bool:
    return summary_value(rows, "previous_seed_strategy") == PREVIOUS_SEED and summary_value(rows, "previous_seed_ticker") == PREVIOUS_TICKER


def previous_seed_value(rows: list[dict[str, str]]) -> str:
    strategy = summary_value(rows, "previous_seed_strategy") or "missing_previous_seed_strategy"
    ticker = summary_value(rows, "previous_seed_ticker") or "missing_previous_seed_ticker"
    return f"{strategy}:{ticker}"


def first_warning(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("status") != "pass":
            return str(row.get("check_name", "manual_review_required"))
    return "none"


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
