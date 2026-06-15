"""Saved-output paper-readiness blocker report for qqq_100_trend_gate.

This report reads saved CSV outputs only. It does not refresh market data, call
yfinance or Alpaca, read positions, create orders, write SQLite, send alerts,
schedule anything, change config defaults, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

INPUT_FILES = {
    "preview_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "preview_signal_summary": Path("data/qqq100_preview_signal_summary.csv"),
    "action_preview": Path("data/qqq100_action_preview.csv"),
    "action_preview_summary": Path("data/qqq100_action_preview_summary.csv"),
    "action_preview_blockers": Path("data/qqq100_action_preview_blockers.csv"),
    "qqq100_readiness_pack": Path("data/qqq100_preview_candidate_readiness_pack.csv"),
    "qqq100_readiness_summary": Path("data/qqq100_preview_candidate_readiness_summary.csv"),
    "qqq_readiness_report": Path("data/qqq_preview_candidate_readiness_report.csv"),
    "qqq_readiness_summary": Path("data/qqq_preview_candidate_readiness_summary.csv"),
    "qqq_lead_decision": Path("data/qqq_lead_decision_report.csv"),
    "qqq_lead_summary": Path("data/qqq_lead_decision_summary.csv"),
    "qqq_manual_review": Path("data/qqq_trend_gate_manual_review_pack.csv"),
    "qqq_manual_summary": Path("data/qqq_trend_gate_manual_review_summary.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "execution_eligibility": Path("data/execution_eligibility_report.csv"),
    "paper_kill_switch_readiness": Path("data/paper_kill_switch_readiness_report.csv"),
    "paper_kill_switch_gate": Path("data/paper_kill_switch_gate_report.csv"),
    "paper_execution_protection": Path("data/paper_execution_protection_report.csv"),
    "paper_order_smoke_test_readiness": Path("data/paper_order_smoke_test_readiness_pack.csv"),
    "paper_order_smoke_test_preflight": Path("data/paper_order_smoke_test_live_preflight.csv"),
    "paper_order_smoke_test_postcheck": Path("data/paper_order_smoke_test_postcheck.csv"),
    "project_research_state_summary": Path("data/project_research_state_summary.csv"),
    "project_research_state_next_steps": Path("data/project_research_state_next_steps.csv"),
    "high_growth_final_validation": Path("data/high_growth_stock_final_validation_pack.csv"),
    "high_growth_final_validation_summary": Path("data/high_growth_stock_final_validation_summary.csv"),
}

OUTPUT_FILES = {
    "report": Path("data/qqq100_paper_readiness_blocker_report.csv"),
    "summary": Path("data/qqq100_paper_readiness_blocker_summary.csv"),
    "evidence": Path("data/qqq100_paper_readiness_blocker_evidence.csv"),
    "blockers": Path("data/qqq100_paper_readiness_blocker_blockers.csv"),
}

REPORT_COLUMNS = [
    "strategy_name",
    "ticker",
    "check_name",
    "status",
    "risk_label",
    "finding",
    "evidence_source",
    "blocker",
    "required_next_step",
    "research_only",
    "preview_only",
    "action_preview_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "action_preview_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
EVIDENCE_COLUMNS = [
    "strategy_name",
    "ticker",
    "evidence_name",
    "evidence_value",
    "evidence_source",
    "details",
    "research_only",
    "preview_only",
    "action_preview_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
BLOCKER_COLUMNS = [
    "strategy_name",
    "ticker",
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    "research_only",
    "preview_only",
    "action_preview_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": True,
    "action_preview_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
}


@dataclass
class Qqq100PaperReadinessBlockerReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_paper_readiness_blocker_report(
    root_dir: Path | str = ".",
) -> Qqq100PaperReadinessBlockerReportResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    context = build_context(inputs)
    report_rows = build_report_rows(context, inputs)
    evidence_rows = build_evidence_rows(context, inputs)
    blocker_rows = build_blocker_rows(context, inputs)
    summary_rows = build_summary_rows(context, inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return Qqq100PaperReadinessBlockerReportResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, context, output_paths),
    )


def show_qqq100_paper_readiness_blocker_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, ["Run `python bot.py --qqq100-paper-readiness-blocker-report` first."]
    summary_rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 paper-readiness blocker report saved display. Saved-output only; execution_approved=False.",
        f"Final paper-readiness status: {summary_value(summary_rows, 'final_paper_readiness_status')}",
        f"Strategy: {summary_value(summary_rows, 'strategy_name')}",
        f"Ticker: {summary_value(summary_rows, 'ticker')}",
        f"Latest desired position: {summary_value(summary_rows, 'latest_desired_position')}",
        f"Latest current position status: {summary_value(summary_rows, 'latest_current_position_status')}",
        f"Strongest positive readiness evidence: {summary_value(summary_rows, 'strongest_positive_readiness_evidence')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; sqlite_trade_log_written=false; discord_alert_sent=false; telegram_alert_sent=false",
        "paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: this report explains blockers only. It does not approve paper execution, create order instructions, or schedule anything.",
    ]


def build_context(inputs: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    action = first_row(inputs.get("action_preview", []))
    signal = first_row(inputs.get("preview_signal", []))
    desired = action.get("desired_position") or signal.get("desired_position") or "unknown"
    current_status = action.get("current_position_status") or "position_not_read"
    alignment = action.get("alignment_state") or "position_context_unavailable"
    non_executable_preview_action = action.get("non_executable_preview_action") or "manual_review_required_position_unavailable"
    signal_status = action.get("preview_signal_status") or signal.get("data_status") or "saved_signal_unknown"
    action_preview_status = summary_value(inputs.get("action_preview_summary", []), "final_action_preview_status") or "qqq100_action_preview_missing"
    strongest = strongest_positive_evidence(signal_status, action_preview_status, desired, current_status, alignment)
    return {
        "desired_position": desired,
        "current_position_status": current_status,
        "current_position_source": action.get("current_position_source") or "saved_output_unavailable",
        "alignment_state": alignment,
        "non_executable_preview_action": non_executable_preview_action,
        "preview_signal_status": signal_status,
        "action_preview_status": action_preview_status,
        "strongest_positive_evidence": strongest,
        "largest_blocker": "smoke_test_required_first",
        "recommended_next_step": "complete_separate_aapl_smoke_test_and_design_qqq100_paper_execution_readiness_before_any_manual_confirmation",
    }


def strongest_positive_evidence(
    signal_status: str,
    action_preview_status: str,
    desired_position: str,
    current_position_status: str,
    alignment_state: str,
) -> str:
    if (
        signal_status == "ok"
        and action_preview_status == "qqq100_action_preview_created"
        and desired_position == "long"
        and current_position_status == "paper_position_flat"
        and alignment_state == "review_required_not_aligned"
    ):
        return "preview_signal_and_readonly_action_preview_exist_desired_long_paper_flat_non_executable"
    if action_preview_status == "qqq100_action_preview_created":
        return "read_only_action_preview_exists_and_stayed_non_executable"
    if signal_status == "ok":
        return "preview_signal_exists"
    return "saved_preview_chain_needs_refresh_before_paper_design_review"


def build_report_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        report_row("preview_chain", "ready_for_blocker_review", "qqq100_preview_chain_ready", "Saved preview signal/action-preview chain exists where available and remains non-executable.", "data/qqq100_action_preview.csv", "none_for_preview_chain", "Use this only as blocker context."),
        report_row("aapl_smoke_test", "blocked", "smoke_test_required_first", "The separate tiny AAPL smoke test is not completed in saved outputs and remains a prerequisite before QQQ100 paper execution design.", "data/paper_order_smoke_test_postcheck.csv", "smoke_test_required_first", "Complete the separate smoke-test readiness, preflight, manual run, and postcheck flow first."),
        report_row("qqq100_execution_design", "blocked", "execution_design_not_added", "No QQQ100 paper execution command or execution design has been added.", "saved code/report inventory", "execution_design_not_added", "Design a separate manually confirmed paper-execution proposal only after blockers are cleared."),
        report_row("sizing", "blocked", "sizing_not_approved", "Paper sizing for QQQ100 is not approved.", "saved paper-readiness outputs", "sizing_not_approved", "Define fixed sizing, max notional, and loss limits in a future report-only design."),
        report_row("portfolio_risk", "blocked", "portfolio_risk_review_required", "Portfolio risk limits are not confirmed as enforced for this path.", "data/portfolio_risk_policy_report.csv", "portfolio_risk_review_required", "Review saved portfolio risk policy and enforcement checkpoints."),
        report_row("kill_switch", "blocked", "kill_switch_review_required", "Paper kill-switch enforcement is not confirmed for this path.", "data/paper_kill_switch_gate_report.csv", "kill_switch_review_required", "Confirm kill-switch readiness, gate, and protection reports before any paper design."),
        report_row("execution_eligibility", "blocked", "execution_blocked", "Execution eligibility is not approved for QQQ100 paper execution.", "data/execution_eligibility_report.csv", "execution_blocked", "Keep paper execution blocked until eligibility explicitly passes in a separate review."),
        report_row("open_order_handling", "blocked", "execution_design_not_added", "Open-order handling has not been reviewed for a QQQ100 path.", "saved paper-order preflight/postcheck outputs", "open_order_handling_not_reviewed", "Define read-only open-order checks in a future design."),
        report_row("duplicate_exposure", "blocked", "portfolio_risk_review_required", "Duplicate exposure handling has not been reviewed for QQQ100 versus any existing exposure.", "saved action-preview context", "duplicate_exposure_not_reviewed", "Review duplicate exposure and concentration rules before paper design."),
        report_row("manual_confirmation", "blocked", "manual_confirmation_required", "Manual confirmation wording is not designed.", "saved paper runbook/check outputs", "manual_confirmation_required", "Draft explicit confirmation wording in a future report-only checkpoint."),
        report_row("postcheck", "blocked", "postcheck_required", "QQQ100-specific postcheck/read-only status check is not designed.", "saved paper-order postcheck outputs", "postcheck_required", "Design postcheck/read-only status rows before any paper execution discussion."),
        report_row("scheduling", "blocked", "scheduling_not_approved", "Scheduling is explicitly not approved.", "project scheduling boundaries", "scheduling_not_approved", "Do not schedule QQQ100 paper execution or action preview."),
        report_row("strategy_to_execution", "blocked", "execution_blocked", "Strategy-to-execution integration is not approved.", "project execution boundaries", "execution_blocked", "Keep preview/action-preview outputs disconnected from execution."),
        report_row("high_growth_contrast", "excluded", "high_growth_branch_excluded", "High-growth stock branch remains excluded from QQQ100 paper-readiness discussion except as contrast.", "data/high_growth_stock_final_validation_summary.csv", "none_for_qqq100", "Keep QQQ100 as the only represented strategy in this report."),
    ]


def build_evidence_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    missing = missing_input_names(inputs)
    return [
        evidence_row("clean_main_lead", STRATEGY_NAME, "saved QQQ lead/readiness outputs", "qqq_100_trend_gate remains the clean main lead."),
        evidence_row("preview_signal_status", context["preview_signal_status"], "data/qqq100_preview_signal_pack.csv", "Saved preview signal status."),
        evidence_row("action_preview_status", context["action_preview_status"], "data/qqq100_action_preview_summary.csv", "Saved action preview exists where available and remains non-executable."),
        evidence_row("latest_desired_position", context["desired_position"], "data/qqq100_action_preview.csv", "Desired position from saved action preview."),
        evidence_row("latest_current_position_status", context["current_position_status"], "data/qqq100_action_preview.csv", "Read-only/current position context from saved action preview."),
        evidence_row("alignment_state", context["alignment_state"], "data/qqq100_action_preview.csv", "Alignment state from saved action preview."),
        evidence_row("non_executable_preview_action", context["non_executable_preview_action"], "data/qqq100_action_preview.csv", "Action preview wording is non-executable manual review context."),
        evidence_row("high_growth_branch", "excluded_for_contrast_only", "data/high_growth_stock_final_validation_summary.csv", "High-growth branch remains outside QQQ100 paper-readiness scope."),
        evidence_row("missing_saved_inputs", "; ".join(missing) if missing else "none_for_available_saved_outputs", "saved CSV inventory", "Missing saved inputs reduce audit completeness but do not approve execution."),
    ]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("smoke_test_required_first", "blocked", "critical", "The separate Monday AAPL buy 1 smoke test is still required before QQQ100 paper execution design.", "Complete the separate smoke-test flow first."),
        blocker_row("execution_design_not_added", "blocked", "critical", "No QQQ100 paper execution command/design has been added.", "Create a future report-only design only after prerequisites pass."),
        blocker_row("sizing_not_approved", "blocked", "critical", "Order sizing is not approved.", "Define sizing limits in a future blocker-clearing report."),
        blocker_row("kill_switch_review_required", "blocked", "critical", "Paper kill-switch enforcement is not confirmed for QQQ100.", "Review kill-switch readiness/gate/protection outputs."),
        blocker_row("portfolio_risk_review_required", "blocked", "critical", "Portfolio risk limits are not confirmed as enforced for QQQ100.", "Review portfolio policy and duplicate exposure handling."),
        blocker_row("manual_confirmation_required", "blocked", "high", "Manual confirmation wording is not designed.", "Draft manual confirmation wording before any paper design."),
        blocker_row("postcheck_required", "blocked", "high", "QQQ100 postcheck/read-only status check is not designed.", "Design a QQQ100 postcheck before any paper execution discussion."),
        blocker_row("scheduling_not_approved", "blocked", "critical", "Scheduling is not approved.", "Do not schedule this path."),
        blocker_row("execution_blocked", "blocked", "critical", "Paper/live execution remains blocked.", "Keep QQQ100 disconnected from execution."),
    ]
    missing = missing_input_names(inputs)
    if missing:
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", "; ".join(missing), "Regenerate missing safe saved reports only if needed."))
    return rows


def build_summary_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        summary_row("final_paper_readiness_status", "qqq100_paper_readiness_blocked", "QQQ100 paper execution design remains blocked."),
        summary_row("strategy_name", STRATEGY_NAME, "Only qqq_100_trend_gate is represented."),
        summary_row("ticker", TICKER, "Only QQQ is represented."),
        summary_row("latest_desired_position", context["desired_position"], "From saved action preview where available."),
        summary_row("latest_current_position_status", context["current_position_status"], "From saved action preview where available."),
        summary_row("strongest_positive_readiness_evidence", context["strongest_positive_evidence"], "Positive evidence is still non-executable."),
        summary_row("largest_blocker", context["largest_blocker"], "Separate smoke test and execution design blockers remain."),
        summary_row("recommended_next_step", context["recommended_next_step"], "Next step remains manual review/report-only."),
        summary_row("preview_chain_status", "qqq100_preview_chain_ready", "Preview signal and action preview are useful blocker evidence, not execution approval."),
        summary_row("execution_status", "execution_blocked", "Paper/live execution is not approved."),
        summary_row("scheduling_status", "scheduling_not_approved", "Scheduling is not approved."),
    ]


def report_row(
    check_name: str,
    status: str,
    risk_label: str,
    finding: str,
    evidence_source: str,
    blocker: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "strategy_name": STRATEGY_NAME,
        "ticker": TICKER,
        "check_name": check_name,
        "status": status,
        "risk_label": risk_label,
        "finding": finding,
        "evidence_source": evidence_source,
        "blocker": blocker,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def evidence_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {
        "strategy_name": STRATEGY_NAME,
        "ticker": TICKER,
        "evidence_name": name,
        "evidence_value": value,
        "evidence_source": source,
        "details": details,
        **safety_flags(),
    }


def blocker_row(name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return {
        "strategy_name": STRATEGY_NAME,
        "ticker": TICKER,
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def build_summary_lines(
    summary_rows: list[dict[str, Any]],
    context: dict[str, str],
    output_paths: dict[str, Path],
) -> list[str]:
    return [
        "QQQ100 paper-readiness blocker report complete. Saved-output only; execution_approved=False.",
        f"Final paper-readiness status: {summary_value(summary_rows, 'final_paper_readiness_status')}",
        f"Strategy: {summary_value(summary_rows, 'strategy_name')}",
        f"Ticker: {summary_value(summary_rows, 'ticker')}",
        f"Latest desired position: {context['desired_position']}",
        f"Latest current position status: {context['current_position_status']}",
        f"Strongest positive readiness evidence: {summary_value(summary_rows, 'strongest_positive_readiness_evidence')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report to {output_paths['report']}",
        f"Saved summary/evidence/blockers to {output_paths['summary']}; {output_paths['evidence']}; {output_paths['blockers']}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; sqlite_trade_log_written=false; discord_alert_sent=false; telegram_alert_sent=false",
        "paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: this is a blocker report only, not paper execution design, order instruction, or scheduling approval.",
    ]


def missing_input_names(inputs: dict[str, list[dict[str, Any]]]) -> list[str]:
    return [name for name, rows in inputs.items() if not rows]


def first_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
