"""Saved-output paper-live checkpoints for the active volatility seed.

These reports sit after the status-only seed switch. They do not call Alpaca,
read positions, refresh market data, create order instructions, schedule
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

GATE_STATUS = "vol_targeted_growth_paper_live_manual_gate_created_manual_review_required"
ACTION_PACK_STATUS = "vol_targeted_growth_paper_live_action_preview_pack_created_manual_review_required"
RECONCILIATION_STATUS = "vol_targeted_growth_broker_comparison_reconciliation_created_manual_review_required"
RECONCILIATION_INCOMPLETE_STATUS = "vol_targeted_growth_broker_comparison_reconciliation_incomplete_manual_review_required"

GATE_NEXT_STEP = "manual_review_gate_before_any_vol_targeted_paper_live_action_discussion"
ACTION_PACK_NEXT_STEP = "manual_review_action_preview_pack_before_any_broker_reconciliation_or_order_design"
RECONCILIATION_NEXT_STEP = "manual_review_saved_broker_comparison_before_any_paper_live_candidate_discussion"

GATE_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_paper_live_manual_approval_gate.csv"),
    "summary": Path("data/vol_targeted_growth_paper_live_manual_approval_gate_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_paper_live_manual_approval_gate_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_paper_live_manual_approval_gate_blockers.csv"),
}

ACTION_PACK_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_paper_live_action_preview_pack.csv"),
    "summary": Path("data/vol_targeted_growth_paper_live_action_preview_pack_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_paper_live_action_preview_pack_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_paper_live_action_preview_pack_blockers.csv"),
}

RECONCILIATION_OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_broker_comparison_reconciliation.csv"),
    "summary": Path("data/vol_targeted_growth_broker_comparison_reconciliation_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_broker_comparison_reconciliation_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_broker_comparison_reconciliation_blockers.csv"),
}

INPUT_FILES = {
    "active_seed_readiness_summary": Path("data/vol_targeted_growth_active_seed_readiness_summary.csv"),
    "seed_switch_summary": Path("data/vol_targeted_growth_seed_switch_status_only_summary.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "action_preview": Path("data/vol_targeted_growth_action_preview.csv"),
    "action_preview_quality_gate_summary": Path("data/vol_targeted_growth_action_preview_quality_gate_summary.csv"),
    "broker_comparison_summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "broker_comparison": Path("data/vol_targeted_growth_broker_position_comparison.csv"),
    "post_comparison_decision_summary": Path("data/vol_targeted_growth_post_comparison_decision_summary.csv"),
    "paper_live_monitoring_status": Path("data/paper_live_monitoring_status.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "active_seed": ACTIVE_SEED,
    "active_ticker": ACTIVE_TICKER,
    "previous_seed": PREVIOUS_SEED,
    "previous_ticker": PREVIOUS_TICKER,
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
    "order_instructions_created": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "paper_live_candidate_approved": False,
    "manual_paper_live_approval_recorded": False,
    "action_preview_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REPORT_COLUMNS = [
    "created_at",
    "checkpoint_name",
    "status",
    "risk_level",
    "evidence",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthCheckpointResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_paper_live_manual_approval_gate(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = gate_report_rows(created_at, inputs)
    summary_rows = gate_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs)
    blocker_rows = gate_blocker_rows()
    output_paths = write_checkpoint(root, GATE_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth paper-live manual gate", summary_rows, output_paths),
    )


def show_vol_targeted_growth_paper_live_manual_approval_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / GATE_OUTPUT_FILES["summary"],
        "Volatility-targeted growth paper-live manual gate saved display. Manual-review only; no execution approval.",
        "final_manual_gate_status",
        "Run `python bot.py --vol-targeted-growth-paper-live-manual-approval-gate` first.",
    )


def generate_vol_targeted_growth_paper_live_action_preview_pack(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = action_pack_report_rows(created_at, inputs)
    summary_rows = action_pack_summary_rows(inputs, report_rows)
    evidence_rows = evidence_rows_for(inputs)
    blocker_rows = action_pack_blocker_rows(inputs)
    output_paths = write_checkpoint(root, ACTION_PACK_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth paper-live action-preview pack", summary_rows, output_paths),
    )


def show_vol_targeted_growth_paper_live_action_preview_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / ACTION_PACK_OUTPUT_FILES["summary"],
        "Volatility-targeted growth paper-live action-preview pack saved display. Saved-output only; no order instructions.",
        "final_action_preview_pack_status",
        "Run `python bot.py --vol-targeted-growth-paper-live-action-preview-pack` first.",
    )


def generate_vol_targeted_growth_broker_comparison_reconciliation(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthCheckpointResult:
    root = Path(root_dir)
    created_at = now_utc()
    inputs = load_inputs(root)
    report_rows = reconciliation_report_rows(created_at, inputs)
    final_status = reconciliation_status(inputs)
    summary_rows = reconciliation_summary_rows(inputs, report_rows, final_status)
    evidence_rows = evidence_rows_for(inputs)
    blocker_rows = reconciliation_blocker_rows(inputs, final_status)
    output_paths = write_checkpoint(root, RECONCILIATION_OUTPUT_FILES, report_rows, summary_rows, evidence_rows, blocker_rows)
    return VolTargetedGrowthCheckpointResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines("Volatility-targeted growth broker-comparison reconciliation", summary_rows, output_paths),
    )


def show_vol_targeted_growth_broker_comparison_reconciliation(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_summary(
        Path(root_dir) / RECONCILIATION_OUTPUT_FILES["summary"],
        "Volatility-targeted growth broker-comparison reconciliation saved display. Saved broker output only; no Alpaca call.",
        "final_reconciliation_status",
        "Run `python bot.py --vol-targeted-growth-broker-comparison-reconciliation` first.",
    )


def gate_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    active_status = summary_value(inputs["active_seed_readiness_summary"], "final_active_seed_readiness_status")
    gate_items = [
        (
            "active_seed_confirmed",
            "manual_review_required" if active_status else "missing_saved_evidence",
            "critical",
            active_status or "missing_active_seed_readiness",
            "The active seed can only be considered if saved active-seed readiness exists.",
            GATE_NEXT_STEP,
        ),
        (
            "manual_approval_required",
            "manual_approval_not_recorded",
            "critical",
            "manual_paper_live_approval_recorded=false",
            "No paper-live action discussion is approved by this checkpoint.",
            "record_separate_manual_approval_before_any_action_discussion",
        ),
        (
            "component_sleeve_boundary",
            "high_growth_and_crypto_remain_research_only",
            "critical",
            "multi_sleeve_candidate_contains research-only sleeves",
            "The high-growth and crypto components cannot piggyback into paper execution.",
            "separate_component_promotion_reviews_required",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "all approval flags false",
            "The gate is a review checkpoint, not an action or order approval.",
            "keep_all_execution_flags_false",
        ),
    ]
    return [report_row(created_at, *item) for item in gate_items]


def gate_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_manual_gate_status", GATE_STATUS, "Manual gate exists, but approval is not recorded."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("active_seed_readiness_status", summary_value(inputs["active_seed_readiness_summary"], "final_active_seed_readiness_status") or "missing_active_seed_readiness_status", "Saved active-seed readiness evidence."),
        ("paper_live_candidate_approved", "False", "No paper-live candidacy is approved."),
        ("manual_paper_live_approval_recorded", "False", "A separate explicit approval record would be required later."),
        ("largest_blocker", "manual_paper_live_approval_not_recorded", "Human approval is required before action discussion."),
        ("recommended_next_step", GATE_NEXT_STEP, "Review the gate before any action preview or broker reconciliation can be treated as candidate discussion."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item) for item in data]


def action_pack_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    action_status = summary_value(inputs["action_preview_summary"], "final_action_preview_status")
    quality_status = summary_value(inputs["action_preview_quality_gate_summary"], "final_quality_gate_status")
    rows = [
        (
            "saved_action_preview_present",
            "manual_review_required" if action_status else "missing_saved_action_preview",
            "critical",
            action_status or "missing_action_preview_status",
            "Saved sleeve preview context is required, but it is still not an order instruction.",
            ACTION_PACK_NEXT_STEP,
        ),
        (
            "quality_gate_present",
            "manual_review_required" if quality_status else "missing_saved_quality_gate",
            "high",
            quality_status or "missing_action_preview_quality_gate_status",
            "The action preview needs a saved quality gate before candidate discussion.",
            "refresh_saved_action_preview_quality_gate",
        ),
        (
            "current_exposure_boundary",
            "current_exposure_requires_saved_broker_reconciliation",
            "critical",
            "broker_positions_read_now=false",
            "This pack does not read positions and cannot decide alignment.",
            "use_saved_broker_comparison_reconciliation_only_after_manual_review",
        ),
        (
            "order_instruction_boundary",
            "order_instructions_forbidden",
            "critical",
            "no side, quantity, order type, account, key, webhook, token, or order id fields",
            "The action-preview pack is explanatory, not executable.",
            "keep_pack_non_executable",
        ),
    ]
    return [report_row(created_at, *item) for item in rows]


def action_pack_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action_rows = inputs["action_preview"]
    data = [
        ("final_action_preview_pack_status", ACTION_PACK_STATUS, "Saved action-preview context is packaged for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("saved_action_preview_status", summary_value(inputs["action_preview_summary"], "final_action_preview_status") or "missing_action_preview_status", "Saved action-preview status."),
        ("saved_action_preview_quality_gate_status", summary_value(inputs["action_preview_quality_gate_summary"], "final_quality_gate_status") or "missing_action_preview_quality_gate_status", "Saved quality-gate status."),
        ("sleeve_preview_row_count", str(len(action_rows)), "Saved sleeve preview row count."),
        ("order_instructions_created", "False", "No executable order instructions are created."),
        ("largest_blocker", "current_exposure_not_reconciled_and_manual_approval_missing", "Current exposure is unknown unless a saved broker comparison is reviewed."),
        ("recommended_next_step", ACTION_PACK_NEXT_STEP, "Manual review the saved pack before broker reconciliation or order-design discussion."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item) for item in data]


def reconciliation_report_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    broker_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status")
    post_status = summary_value(inputs["post_comparison_decision_summary"], "final_post_comparison_decision_status")
    rows = [
        (
            "saved_broker_comparison_present",
            "manual_review_required" if broker_status else "missing_saved_broker_comparison",
            "critical",
            broker_status or "missing_broker_comparison_status",
            "This reconciliation uses saved broker comparison output only and does not call Alpaca.",
            RECONCILIATION_NEXT_STEP,
        ),
        (
            "saved_post_comparison_decision_present",
            "manual_review_required" if post_status else "missing_post_comparison_decision",
            "high",
            post_status or "missing_post_comparison_decision_status",
            "Saved post-comparison interpretation should be reviewed before any candidate discussion.",
            "refresh_or_review_post_comparison_decision",
        ),
        (
            "broker_read_boundary",
            "broker_not_read_now",
            "critical",
            "alpaca_called=false; paper_positions_read=false",
            "The reconciliation is safe to run repeatedly because it does not query the broker.",
            "run_readonly_broker_comparison_only_with_separate_explicit_approval",
        ),
        (
            "execution_boundary",
            "execution_blocked",
            "critical",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
            "Saved broker context is not approval to trade or repeat trades.",
            "keep_all_execution_flags_false",
        ),
    ]
    return [report_row(created_at, *item) for item in rows]


def reconciliation_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    return RECONCILIATION_STATUS if inputs["broker_comparison_summary"] else RECONCILIATION_INCOMPLETE_STATUS


def reconciliation_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    rows: list[dict[str, Any]],
    final_status: str,
) -> list[dict[str, Any]]:
    broker_rows = inputs["broker_comparison"]
    broker_status = summary_value(inputs["broker_comparison_summary"], "final_comparison_status")
    data = [
        ("final_reconciliation_status", final_status, "Saved broker-comparison evidence is reconciled for manual review only."),
        ("active_seed", ACTIVE_SEED, "Current status/report seed."),
        ("active_ticker", ACTIVE_TICKER, "Status ticker label for the multi-sleeve seed."),
        ("saved_broker_comparison_status", broker_status or "missing_broker_comparison_status", "Saved read-only broker comparison status."),
        ("saved_broker_comparison_row_count", str(len(broker_rows)), "Saved broker comparison row count."),
        ("broker_read_now", "False", "This command does not call Alpaca or read positions."),
        ("paper_live_candidate_approved", "False", "No paper-live candidacy is approved by reconciliation."),
        ("largest_blocker", "saved_broker_context_requires_manual_review_not_execution", "Broker context cannot become order instructions."),
        ("recommended_next_step", RECONCILIATION_NEXT_STEP, "Manual review saved broker comparison before any candidate discussion."),
        ("checkpoint_row_count", str(len(rows)), "Saved checkpoint row count."),
    ]
    return [summary_row(*item) for item in data]


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = []
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    rows.append(("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return [evidence_row(*item) for item in rows]


def gate_blocker_rows() -> list[dict[str, Any]]:
    return blocker_rows(
        [
            ("manual_paper_live_approval_not_recorded", "blocked", "critical", "This checkpoint does not record approval.", "separate_manual_approval_record_required"),
            ("component_sleeves_not_promoted", "blocked", "critical", "High-growth and crypto sleeves remain research-only.", "separate_component_reviews_required"),
            ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, or scheduling are approved.", "keep_all_approval_flags_false"),
        ]
    )


def action_pack_blocker_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("current_exposure_not_reconciled", "blocked", "critical", "The pack does not read broker positions.", "review_saved_broker_reconciliation_separately"),
        ("order_instructions_forbidden", "blocked", "critical", "No order side, quantity, type, account, key, token, webhook, or order ID fields are allowed.", "keep_pack_non_executable"),
        ("execution_not_approved", "blocked", "critical", "No execution, follow-up order, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if not inputs["action_preview_summary"]:
        rows.insert(0, ("missing_saved_action_preview", "blocked", "high", "Saved action preview summary is missing.", "refresh_saved_action_preview"))
    return blocker_rows(rows)


def reconciliation_blocker_rows(inputs: dict[str, list[dict[str, str]]], final_status: str) -> list[dict[str, Any]]:
    rows = [
        ("broker_read_not_performed_now", "blocked", "critical", "This command does not call Alpaca.", "only_run_readonly_broker_comparison_with_separate_explicit_approval"),
        ("saved_broker_context_not_actionable", "blocked", "critical", "Saved broker context is manual-review evidence only.", "do_not_create_order_instructions"),
        ("execution_not_approved", "blocked", "critical", "No orders, paper execution, live trading, or scheduling are approved.", "keep_all_approval_flags_false"),
    ]
    if final_status == RECONCILIATION_INCOMPLETE_STATUS:
        rows.insert(0, ("missing_saved_broker_comparison", "blocked", "high", "Saved broker comparison summary is missing.", "run_readonly_broker_comparison_only_after_explicit_approval"))
    if not inputs["post_comparison_decision_summary"]:
        rows.insert(1, ("missing_post_comparison_decision", "blocked", "high", "Saved post-comparison decision is missing.", "refresh_post_comparison_decision"))
    return blocker_rows(rows)


def write_checkpoint(
    root: Path,
    paths: dict[str, Path],
    report_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    blocker_rows_: list[dict[str, Any]],
) -> dict[str, Path]:
    output_paths = {name: root / path for name, path in paths.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows_)
    return output_paths


def show_summary(path: Path, title: str, status_key: str, missing_message: str) -> tuple[int, list[str]]:
    if not path.exists():
        return 1, [missing_message]
    rows = read_csv_rows(path)
    return 0, [
        title,
        f"{status_key}: {summary_value(rows, status_key)}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"active_ticker: {summary_value(rows, 'active_ticker')}",
        f"previous_seed: {summary_value(rows, 'previous_seed') or PREVIOUS_SEED}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "Warning: this is saved-output/manual-review only, not broker refresh, paper-live approval, order approval, live trading, or scheduling approval.",
    ]


def summary_lines(title: str, summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    status = (
        summary_value(summary_rows, "final_manual_gate_status")
        or summary_value(summary_rows, "final_action_preview_pack_status")
        or summary_value(summary_rows, "final_reconciliation_status")
    )
    return [
        f"{title} complete. Saved-output/manual-review only; no execution or scheduling approved.",
        f"final_status={status}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "alpaca_called=false; broker_positions_read_now=false; order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def report_row(created_at: str, name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "checkpoint_name": name,
        "status": status,
        "risk_level": risk,
        "evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def blocker_rows(rows: list[tuple[str, str, str, str, str]]) -> list[dict[str, Any]]:
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in rows
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return ""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
