"""Report-only evidence-gap audit for future QQQ-led multi-sleeve work.

This checkpoint checks saved-output file presence only. It does not rerun
research, refresh market data, call Alpaca, read positions, create action
previews, create order instructions, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "report": Path("data/paper_live_multi_sleeve_evidence_gap.csv"),
    "summary": Path("data/paper_live_multi_sleeve_evidence_gap_summary.csv"),
    "blockers": Path("data/paper_live_multi_sleeve_evidence_gap_blockers.csv"),
    "evidence": Path("data/paper_live_multi_sleeve_evidence_gap_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "audit_only": True,
    "saved_output_only": True,
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
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "sleeve_name",
    "saved_evidence_present",
    "key_saved_outputs_found",
    "missing_evidence",
    "current_status",
    "blocker",
    "allowed_next_action",
    "forbidden_action",
    "research_only",
    "report_only",
    "audit_only",
    "saved_output_only",
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
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_FLAGS.keys(),
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_value",
    "details",
    *SAFETY_FLAGS.keys(),
]


@dataclass(frozen=True)
class EvidenceSpec:
    sleeve_name: str
    expected_outputs: tuple[str, ...]
    missing_evidence_label: str
    current_status_present: str
    current_status_missing: str
    blocker_present: str
    blocker_missing: str
    allowed_next_action: str
    forbidden_action: str


@dataclass
class PaperLiveMultiSleeveEvidenceGapResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_multi_sleeve_evidence_gap(root_dir: Path | str = ".") -> PaperLiveMultiSleeveEvidenceGapResult:
    root = Path(root_dir)
    specs = build_evidence_specs()
    report_rows = [spec_to_row(root, spec) for spec in specs]
    summary_rows = build_summary_rows(report_rows)
    blocker_rows = build_blocker_rows(report_rows)
    evidence_rows = build_evidence_rows(report_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveMultiSleeveEvidenceGapResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_multi_sleeve_evidence_gap(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live multi-sleeve evidence-gap audit is missing.",
            "Run `python bot.py --paper-live-multi-sleeve-evidence-gap` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live multi-sleeve evidence-gap saved display. Report only; no promotion or portfolio execution approved.",
        f"final_evidence_gap_status: {summary_value(rows, 'final_evidence_gap_status')}",
        f"sleeves_checked: {summary_value(rows, 'sleeves_checked')}",
        f"sleeves_with_saved_evidence: {summary_value(rows, 'sleeves_with_saved_evidence')}",
        f"sleeves_missing_evidence: {summary_value(rows, 'sleeves_missing_evidence')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"allowed_next_action: {summary_value(rows, 'allowed_next_action')}",
        f"forbidden_action_summary: {summary_value(rows, 'forbidden_action_summary')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_evidence_specs() -> list[EvidenceSpec]:
    return [
        EvidenceSpec(
            "qqq100_core",
            (
                "data/paper_live_monitoring_status.csv",
                "data/qqq100_followup_policy_report.csv",
                "data/paper_live_checklist_status.csv",
            ),
            "missing_qqq100_monitoring_or_followup_evidence",
            "previous_seed_context_aligned_long_one_no_action_required",
            "qqq100_core_saved_monitoring_evidence_incomplete_manual_review_required",
            "qqq100_monitor_only_no_action_required",
            "qqq100_saved_monitoring_evidence_missing",
            "continue_saved_monitoring_only",
            "repeat_followup_qqq_order;change_current_qqq100_only_monitoring",
        ),
        EvidenceSpec(
            "defensive_sleeve",
            (
                "data/defensive_research_state_report.csv",
                "data/defensive_allocation_risk_preview.csv",
                "data/etf_defensive_drawdown_comparison.csv",
            ),
            "missing_defensive_promotion_evidence",
            "defensive_saved_research_evidence_present_future_review_only",
            "defensive_saved_research_evidence_incomplete_future_review_only",
            "defensive_future_review_only",
            "defensive_missing_saved_research_preview_risk_or_drawdown_evidence",
            "create_saved_output_defensive_sleeve_gap_review",
            "promote_defensive_sleeve_to_preview_or_paper_live",
        ),
        EvidenceSpec(
            "high_growth_sleeve",
            (
                "data/high_growth_component_attribution.csv",
                "data/high_growth_drawdown_review.csv",
                "data/high_growth_stock_risk_review_pack.csv",
            ),
            "missing_high_growth_blocker_evidence",
            "high_growth_concentration_drawdown_attribution_evidence_present_research_only",
            "high_growth_concentration_drawdown_attribution_evidence_incomplete_research_only",
            "high_growth_research_only",
            "high_growth_missing_concentration_drawdown_attribution_survivorship_or_risk_limit_evidence",
            "complete_saved_output_high_growth_evidence_gap_review",
            "promote_high_growth_to_preview_or_paper_live",
        ),
        EvidenceSpec(
            "crypto_sleeve",
            (
                "data/crypto_containment_review.csv",
                "data/crypto_daily_research_report.csv",
                "data/crypto_equal_weight_capped_risk_report.csv",
            ),
            "missing_crypto_containment_volatility_cost_evidence",
            "crypto_containment_volatility_cost_evidence_present_research_only_capped_future_only",
            "crypto_containment_volatility_cost_evidence_incomplete_research_only_capped_future_only_no_crypto_execution_approved",
            "crypto_research_only_no_crypto_execution_approved",
            "crypto_missing_containment_volatility_drawdown_cost_or_execution_boundary_evidence",
            "complete_saved_output_crypto_evidence_gap_review",
            "approve_crypto_execution;wire_crypto_orders",
        ),
        EvidenceSpec(
            "multi_sleeve_allocator",
            (
                "data/paper_live_multi_sleeve_roadmap.csv",
                "data/paper_live_next_phase_backlog.csv",
                "data/multi_sleeve_weight_sensitivity.csv",
                "data/current_research_state_summary.csv",
            ),
            "missing_allocator_accounting_risk_execution_readiness_evidence",
            "allocator_saved_policy_or_lead_state_evidence_present_current_report_status_seed_no_portfolio_execution_wiring",
            "allocator_saved_policy_or_lead_state_evidence_incomplete_current_report_status_seed_no_portfolio_execution_wiring",
            "allocator_current_report_status_seed_no_portfolio_execution_wiring",
            "allocator_missing_allocation_policy_weight_sensitivity_lead_state_accounting_risk_or_execution_readiness_evidence",
            "complete_saved_output_allocator_evidence_gap_review",
            "create_portfolio_order_instructions;wire_allocator_to_execution;schedule_allocator",
        ),
    ]


def spec_to_row(root: Path, spec: EvidenceSpec) -> dict[str, Any]:
    found = [path for path in spec.expected_outputs if (root / path).exists()]
    missing = [path for path in spec.expected_outputs if path not in found]
    has_any = bool(found)
    return {
        "sleeve_name": spec.sleeve_name,
        "saved_evidence_present": has_any,
        "key_saved_outputs_found": ";".join(found) if found else "none",
        "missing_evidence": ";".join(missing) if missing else "none",
        "current_status": spec.current_status_present if has_any else spec.current_status_missing,
        "blocker": spec.blocker_present if has_any and not missing else spec.blocker_missing,
        "allowed_next_action": spec.allowed_next_action,
        "forbidden_action": spec.forbidden_action,
        **ROW_SAFETY,
    }


def build_summary_rows(report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_count = sum(1 for row in report_rows if row.get("missing_evidence") != "none")
    present_count = sum(1 for row in report_rows if row.get("saved_evidence_present") is True)
    summary_items = [
        (
            "final_evidence_gap_status",
            "paper_live_multi_sleeve_evidence_gap_manual_review_required",
            "Evidence gaps are blockers/manual-review items, not promotion or execution approval.",
        ),
        (
            "sleeves_checked",
            str(len(report_rows)),
            "QQQ100 core, defensive, high-growth, crypto, and allocator evidence were checked by file presence only.",
        ),
        (
            "sleeves_with_saved_evidence",
            str(present_count),
            "Count of sleeves with at least one expected saved-output file present.",
        ),
        (
            "sleeves_missing_evidence",
            str(missing_count),
            "Count of sleeves missing one or more expected saved-output evidence files.",
        ),
        (
            "largest_blocker",
            "missing_saved_outputs_are_manual_review_blockers",
            "Missing saved outputs block future ladder movement and do not approve execution.",
        ),
        (
            "allowed_next_action",
            "saved_output_evidence_gap_review_only",
            "Only saved-output reviews, verifiers, and documentation updates are allowed next.",
        ),
        (
            "forbidden_action_summary",
            "no_research_rerun_no_market_refresh_no_action_preview_no_order_instructions_no_sleeve_promotion",
            "Do not rerun research, fetch market data, create action previews/order instructions, or promote sleeves.",
        ),
        (
            "next_safe_development_step",
            "choose_one_missing_evidence_blocker_for_saved_output_review",
            "Pick one missing evidence blocker and address it with a separate report-only checkpoint.",
        ),
    ]
    return [summary_row(name, value, details) for name, value, details in summary_items]


def build_blocker_rows(report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row(
            "missing_saved_outputs_block_promotion",
            "blocked",
            "high",
            "Missing saved outputs are manual-review blockers, not execution approval.",
            "Complete missing saved-output reviews before any ladder movement.",
        ),
        blocker_row(
            "portfolio_execution_wiring_forbidden",
            "blocked",
            "critical",
            "No portfolio execution wiring, action previews, order instructions, or scheduling are allowed.",
            "Keep all work report-only until a separate approved implementation task.",
        ),
    ]
    for row in report_rows:
        if row.get("missing_evidence") != "none":
            rows.append(
                blocker_row(
                    f"{row.get('sleeve_name')}_missing_evidence",
                    "manual_review_required",
                    "high",
                    f"Missing evidence: {row.get('missing_evidence')}",
                    str(row.get("allowed_next_action", "")),
                )
            )
    return rows


def build_evidence_rows(report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(
            "audit_method",
            "saved_output_file_presence_only",
            "This audit checks expected output file existence and does not read generated report contents.",
        ),
        evidence_row(
            "current_phase",
            "qqq100_monitor_only_aligned_long_one_no_action_required",
            "QQQ100 remains the only existing paper-live monitor base.",
        ),
        evidence_row(
            "future_direction",
            "qqq_led_multi_sleeve_from_research_future_only",
            "The roadmap remains future-only and non-executable.",
        ),
    ]
    for row in report_rows:
        rows.append(
            evidence_row(
                f"{row.get('sleeve_name')}_saved_outputs_found",
                str(row.get("key_saved_outputs_found", "")),
                "Saved evidence found by file presence only.",
            )
        )
    return rows


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {
        "summary_name": name,
        "summary_value": value,
        "details": details,
        **SAFETY_FLAGS,
    }


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {
        "evidence_name": name,
        "evidence_value": value,
        "details": details,
        **SAFETY_FLAGS,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live multi-sleeve evidence-gap audit complete. Report only; no research rerun, promotion, portfolio execution, orders, or scheduling approved.",
        f"final_evidence_gap_status={summary_value(summary_rows, 'final_evidence_gap_status')}",
        f"sleeves_checked={summary_value(summary_rows, 'sleeves_checked')}",
        f"sleeves_with_saved_evidence={summary_value(summary_rows, 'sleeves_with_saved_evidence')}",
        f"sleeves_missing_evidence={summary_value(summary_rows, 'sleeves_missing_evidence')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"allowed_next_action={summary_value(summary_rows, 'allowed_next_action')}",
        f"forbidden_action_summary={summary_value(summary_rows, 'forbidden_action_summary')}",
        f"next_safe_development_step={summary_value(summary_rows, 'next_safe_development_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return "unavailable"


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
