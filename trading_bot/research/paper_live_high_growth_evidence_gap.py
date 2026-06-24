"""Report-only evidence-gap audit for the future high-growth sleeve.

This checkpoint checks saved-output file presence only. It does not read
generated CSV contents, rerun research, refresh market data, call Alpaca, read
positions, create action previews, create order instructions, schedule
anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "report": Path("data/paper_live_high_growth_evidence_gap.csv"),
    "summary": Path("data/paper_live_high_growth_evidence_gap_summary.csv"),
    "blockers": Path("data/paper_live_high_growth_evidence_gap_blockers.csv"),
    "evidence": Path("data/paper_live_high_growth_evidence_gap_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "high_growth_promotion_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "audit_only": True,
    "saved_output_only": True,
    "preview_approved": False,
    "paper_live_candidate_approved": False,
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
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "research_rerun": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "evidence_area",
    "saved_evidence_present",
    "expected_saved_outputs",
    "key_missing_evidence",
    "current_status",
    "blocker",
    "allowed_next_action",
    "forbidden_action",
    "research_only",
    "report_only",
    "audit_only",
    "saved_output_only",
    "preview_approved",
    "paper_live_candidate_approved",
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
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "research_rerun",
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
class EvidenceAreaSpec:
    evidence_area: str
    expected_outputs: tuple[str, ...]
    missing_evidence_label: str
    current_status_present: str
    current_status_missing: str
    blocker_present: str
    blocker_missing: str
    allowed_next_action: str
    forbidden_action: str


@dataclass
class PaperLiveHighGrowthEvidenceGapResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_high_growth_evidence_gap(root_dir: Path | str = ".") -> PaperLiveHighGrowthEvidenceGapResult:
    root = Path(root_dir)
    specs = build_evidence_area_specs()
    report_rows = [spec_to_row(root, spec) for spec in specs]
    summary_rows = build_summary_rows(report_rows)
    blocker_rows = build_blocker_rows(report_rows)
    evidence_rows = build_evidence_rows(report_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveHighGrowthEvidenceGapResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_high_growth_evidence_gap(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    blockers_path = root / OUTPUT_FILES["blockers"]
    if not summary_path.exists():
        return 1, [
            "Paper-live high-growth evidence-gap audit is missing.",
            "Run `python bot.py --paper-live-high-growth-evidence-gap` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; high_growth_promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    lines = [
        "Paper-live high-growth evidence-gap saved display. Report only; no high-growth promotion or execution approved.",
        f"final_high_growth_evidence_gap_status: {summary_value(rows, 'final_high_growth_evidence_gap_status')}",
        f"areas_checked: {summary_value(rows, 'areas_checked')}",
        f"areas_with_saved_evidence: {summary_value(rows, 'areas_with_saved_evidence')}",
        f"areas_missing_evidence: {summary_value(rows, 'areas_missing_evidence')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"allowed_next_action: {summary_value(rows, 'allowed_next_action')}",
        f"forbidden_action_summary: {summary_value(rows, 'forbidden_action_summary')}",
        f"next_safe_development_step: {summary_value(rows, 'next_safe_development_step')}",
        "exact_missing_evidence_blockers:",
        *format_missing_blocker_lines(blockers_path),
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; high_growth_promotion_approved=false",
        "never_schedule_order_capable_commands=true",
    ]
    return 0, lines


def build_evidence_area_specs() -> list[EvidenceAreaSpec]:
    return [
        EvidenceAreaSpec(
            "high_growth_saved_lead_evidence",
            (
                "data/high_growth_stock_lead_decision_report.csv",
                "data/high_growth_stock_manual_review_pack.csv",
                "data/high_growth_stock_risk_review_pack.csv",
                "data/high_growth_return_stream_metrics.csv",
            ),
            "missing_high_growth_saved_lead_or_decision_evidence",
            "high_growth_saved_lead_evidence_present_research_only",
            "high_growth_saved_lead_evidence_incomplete_research_only",
            "high_growth_saved_lead_is_not_promotion_evidence",
            "high_growth_saved_lead_or_decision_evidence_missing",
            "review_saved_high_growth_lead_evidence_only",
            "infer_high_growth_candidate;promote_high_growth_sleeve;create_high_growth_order_instructions",
        ),
        EvidenceAreaSpec(
            "concentration_evidence",
            (
                "data/high_growth_component_streams.csv",
                "data/high_growth_component_attribution.csv",
                "data/high_growth_component_attribution_blockers.csv",
                "data/high_growth_sleeve_quality_review.csv",
            ),
            "missing_concentration_or_top_contributor_dependency_evidence",
            "concentration_saved_evidence_present_manual_review_required",
            "concentration_saved_evidence_incomplete_manual_review_required",
            "concentration_review_required_before_preview_or_paper_live",
            "concentration_top_contributor_dependency_evidence_missing",
            "complete_saved_output_concentration_dependency_review",
            "treat_high_growth_as_diversified;approve_preview_candidate;approve_paper_live_candidate",
        ),
        EvidenceAreaSpec(
            "drawdown_evidence",
            (
                "data/multi_sleeve_high_growth_drawdown_decomposition.csv",
                "data/multi_sleeve_high_growth_drawdown_summary.csv",
                "data/multi_sleeve_high_growth_drawdown_periods.csv",
                "data/high_growth_stock_drawdown_control_report.csv",
                "data/high_growth_stock_drawdown_control_summary.csv",
                "data/high_growth_stock_drawdown_control_drawdowns.csv",
            ),
            "missing_high_growth_drawdown_window_or_contribution_evidence",
            "drawdown_saved_evidence_present_manual_review_required",
            "drawdown_saved_evidence_incomplete_manual_review_required",
            "drawdown_review_required_before_preview_or_paper_live",
            "drawdown_window_or_contribution_evidence_missing",
            "complete_saved_output_high_growth_drawdown_review",
            "ignore_high_growth_tail_risk;approve_preview_candidate;approve_paper_live_candidate",
        ),
        EvidenceAreaSpec(
            "attribution_evidence",
            (
                "data/high_growth_component_attribution.csv",
                "data/high_growth_component_attribution_evidence.csv",
                "data/high_growth_component_streams.csv",
                "data/high_growth_component_streams_summary.csv",
            ),
            "missing_component_ticker_weight_or_contribution_attribution",
            "attribution_saved_evidence_present_manual_review_required",
            "attribution_saved_evidence_incomplete_manual_review_required",
            "component_attribution_review_required_before_preview_or_paper_live",
            "component_ticker_weight_or_contribution_evidence_missing_before_preview_or_paper_live",
            "complete_saved_output_component_attribution_review",
            "promote_without_component_attribution;create_action_preview;create_order_instructions",
        ),
        EvidenceAreaSpec(
            "bias_risk_warnings",
            (
                "data/high_growth_stock_manual_review_blockers.csv",
                "data/high_growth_stock_risk_review_blockers.csv",
                "data/high_growth_component_attribution_blockers.csv",
                "data/high_growth_sleeve_quality_blockers.csv",
            ),
            "missing_survivorship_concentration_or_outlier_warning_evidence",
            "bias_risk_saved_warnings_present_high_growth_research_only",
            "bias_risk_saved_warnings_incomplete_high_growth_research_only",
            "survivorship_concentration_outlier_warnings_must_remain_visible",
            "survivorship_concentration_or_outlier_warning_evidence_missing",
            "complete_saved_output_bias_and_risk_warning_review",
            "hide_bias_warning;hide_concentration_warning;label_high_growth_execution_ready",
        ),
        EvidenceAreaSpec(
            "promotion_readiness",
            (
                "data/paper_live_multi_sleeve_evidence_gap.csv",
                "data/paper_live_multi_sleeve_roadmap.csv",
                "data/paper_live_promotion_ladder_design.csv",
                "data/paper_live_f6_f7_audit.csv",
            ),
            "missing_promotion_ladder_f6_f7_or_portfolio_risk_review_evidence",
            "promotion_readiness_evidence_present_but_high_growth_still_not_approved",
            "promotion_readiness_evidence_incomplete_high_growth_not_approved",
            "high_growth_promotion_not_approved_until_all_blockers_reviewed",
            "promotion_readiness_or_f6_f7_portfolio_risk_evidence_missing",
            "complete_ladder_f6_f7_and_portfolio_risk_review_before_any_high_growth_discussion",
            "approve_high_growth_promotion;approve_execution;approve_scheduling;wire_portfolio_execution",
        ),
    ]


def spec_to_row(root: Path, spec: EvidenceAreaSpec) -> dict[str, Any]:
    found = [path for path in spec.expected_outputs if (root / path).exists()]
    missing = [path for path in spec.expected_outputs if path not in found]
    has_any = bool(found)
    return {
        "evidence_area": spec.evidence_area,
        "saved_evidence_present": has_any,
        "expected_saved_outputs": ";".join(spec.expected_outputs),
        "key_missing_evidence": ";".join(missing) if missing else "none",
        "current_status": spec.current_status_present if has_any else spec.current_status_missing,
        "blocker": spec.blocker_present if has_any and not missing else spec.blocker_missing,
        "allowed_next_action": spec.allowed_next_action,
        "forbidden_action": spec.forbidden_action,
        **ROW_SAFETY,
    }


def build_summary_rows(report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_count = sum(1 for row in report_rows if row.get("key_missing_evidence") != "none")
    present_count = sum(1 for row in report_rows if row.get("saved_evidence_present") is True)
    summary_items = [
        (
            "final_high_growth_evidence_gap_status",
            "paper_live_high_growth_evidence_gap_manual_review_required",
            "High-growth saved evidence remains review-only and does not approve sleeve promotion.",
        ),
        (
            "areas_checked",
            str(len(report_rows)),
            "Lead, concentration, drawdown, attribution, bias-risk, and promotion-readiness evidence were checked by file presence only.",
        ),
        (
            "areas_with_saved_evidence",
            str(present_count),
            "Count of evidence areas with at least one expected saved-output file present.",
        ),
        (
            "areas_missing_evidence",
            str(missing_count),
            "Count of evidence areas missing one or more expected saved-output files.",
        ),
        (
            "largest_blocker",
            "high_growth_missing_saved_evidence_blocks_promotion",
            "Missing concentration, drawdown, attribution, bias-risk, F6/F7, or portfolio-risk evidence blocks future ladder movement.",
        ),
        (
            "allowed_next_action",
            "saved_output_high_growth_evidence_review_only",
            "Only saved-output reviews, verifiers, and documentation updates are allowed next.",
        ),
        (
            "forbidden_action_summary",
            "no_research_rerun_no_market_refresh_no_action_preview_no_order_instructions_no_high_growth_promotion",
            "Do not rerun research, fetch market data, create action previews/order instructions, or promote high-growth.",
        ),
        (
            "next_safe_development_step",
            "choose_one_high_growth_missing_evidence_blocker_for_saved_output_review",
            "Pick one high-growth evidence blocker and address it with a separate saved-output checkpoint.",
        ),
    ]
    return [summary_row(name, value, details) for name, value, details in summary_items]


def build_blocker_rows(report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row(
            "high_growth_missing_saved_outputs_block_promotion",
            "blocked",
            "high",
            "Missing saved high-growth evidence is a manual-review blocker, not execution approval.",
            "Complete saved-output high-growth evidence reviews before any promotion-ladder discussion.",
        ),
        blocker_row(
            "high_growth_execution_wiring_forbidden",
            "blocked",
            "critical",
            "No high-growth action preview, order instructions, paper-live promotion, or scheduling are allowed.",
            "Keep all work report-only until a separate approved implementation task.",
        ),
    ]
    for row in report_rows:
        if row.get("key_missing_evidence") != "none":
            rows.append(
                blocker_row(
                    f"{row.get('evidence_area')}_missing_evidence",
                    "manual_review_required",
                    "high",
                    f"Missing evidence: {row.get('key_missing_evidence')}",
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
            "current_high_growth_boundary",
            "high_growth_sleeve_research_only_not_promoted",
            "High-growth can be reviewed as a future research sleeve only.",
        ),
        evidence_row(
            "promotion_boundary",
            "no_preview_no_paper_live_no_execution_no_scheduling",
            "High-growth cannot enter preview or paper-live discussion until evidence blockers are reviewed.",
        ),
    ]
    for row in report_rows:
        rows.append(
            evidence_row(
                f"{row.get('evidence_area')}_expected_saved_outputs",
                str(row.get("expected_saved_outputs", "")),
                "Expected saved outputs checked by file presence only.",
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
        "Paper-live high-growth evidence-gap audit complete. Report only; no research rerun, promotion, execution, orders, or scheduling approved.",
        f"final_high_growth_evidence_gap_status={summary_value(summary_rows, 'final_high_growth_evidence_gap_status')}",
        f"areas_checked={summary_value(summary_rows, 'areas_checked')}",
        f"areas_with_saved_evidence={summary_value(summary_rows, 'areas_with_saved_evidence')}",
        f"areas_missing_evidence={summary_value(summary_rows, 'areas_missing_evidence')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"allowed_next_action={summary_value(summary_rows, 'allowed_next_action')}",
        f"forbidden_action_summary={summary_value(summary_rows, 'forbidden_action_summary')}",
        f"next_safe_development_step={summary_value(summary_rows, 'next_safe_development_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; high_growth_promotion_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return "unavailable"


def format_missing_blocker_lines(blockers_path: Path) -> list[str]:
    if not blockers_path.exists():
        return ["- blocker_details_unavailable: blockers file missing"]
    rows = read_csv_rows(blockers_path)
    missing_rows = [
        row
        for row in rows
        if str(row.get("blocker_name", "")).endswith("_missing_evidence")
        and str(row.get("details", "")).startswith("Missing evidence:")
    ]
    if not missing_rows:
        return ["- none"]
    return [
        f"- {row.get('blocker_name')}: {row.get('details')}; required_next_step={row.get('required_next_step')}"
        for row in missing_rows
    ]


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
