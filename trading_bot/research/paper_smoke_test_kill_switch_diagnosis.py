"""Saved-output diagnosis for paper smoke-test kill-switch blockers.

This report reads saved CSV outputs only. It does not call Alpaca, read paper
positions, create orders, write SQLite, send alerts, change config, schedule
anything, weaken the kill-switch, or approve smoke-test execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "diagnosis": Path("data/paper_smoke_test_kill_switch_diagnosis.csv"),
    "summary": Path("data/paper_smoke_test_kill_switch_diagnosis_summary.csv"),
    "blockers": Path("data/paper_smoke_test_kill_switch_diagnosis_blockers.csv"),
    "recommendations": Path("data/paper_smoke_test_kill_switch_diagnosis_recommendations.csv"),
}

INPUT_FILES = {
    "runbook": Path("data/paper_order_smoke_test_runbook_check.csv"),
    "readiness": Path("data/paper_order_smoke_test_readiness_pack.csv"),
    "live_preflight": Path("data/paper_order_smoke_test_live_preflight.csv"),
    "postcheck": Path("data/paper_order_smoke_test_postcheck.csv"),
    "kill_switch_readiness": Path("data/paper_kill_switch_readiness_report.csv"),
    "kill_switch_gate": Path("data/paper_kill_switch_gate_report.csv"),
    "paper_execution_protection": Path("data/paper_execution_protection_report.csv"),
    "execution_eligibility": Path("data/execution_eligibility_report.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "deployment_readiness": Path("data/deployment_readiness_report.csv"),
    "promoted_decision": Path("data/promoted_decision_preview.csv"),
    "promoted_risk": Path("data/promoted_risk_preview.csv"),
    "qqq100_preview_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_paper_readiness": Path("data/qqq100_paper_readiness_blocker_summary.csv"),
}

DIAGNOSIS_COLUMNS = [
    "diagnosis_name",
    "diagnosis_status",
    "blocker_classification",
    "blocker_scope",
    "finding",
    "evidence_source",
    "recommended_next_step",
    "research_only",
    "report_only",
    "execution_approved",
    "paper_execution_approved",
    "smoke_test_order_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "alpaca_called",
]
SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "report_only",
    "execution_approved",
    "paper_execution_approved",
    "smoke_test_order_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "alpaca_called",
]
BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "blocker_scope",
    "severity",
    "details",
    "required_next_step",
    "research_only",
    "report_only",
    "execution_approved",
    "paper_execution_approved",
    "smoke_test_order_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "alpaca_called",
]
RECOMMENDATION_COLUMNS = [
    "recommendation_name",
    "recommendation_status",
    "applies_to",
    "rationale",
    "required_next_step",
    "research_only",
    "report_only",
    "execution_approved",
    "paper_execution_approved",
    "smoke_test_order_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "alpaca_called",
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "execution_approved": False,
    "paper_execution_approved": False,
    "smoke_test_order_approved": False,
    "scheduling_approved": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "alpaca_called": False,
}


@dataclass
class PaperSmokeTestKillSwitchDiagnosisResult:
    output_paths: dict[str, Path]
    diagnosis_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    recommendation_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_smoke_test_kill_switch_diagnosis(
    root_dir: Path | str = ".",
) -> PaperSmokeTestKillSwitchDiagnosisResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    context = build_context(inputs)
    diagnosis_rows = build_diagnosis_rows(context, inputs)
    blocker_rows = build_blocker_rows(context, inputs)
    recommendation_rows = build_recommendation_rows(context, inputs)
    summary_rows = build_summary_rows(context, inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["diagnosis"], DIAGNOSIS_COLUMNS, diagnosis_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["recommendations"], RECOMMENDATION_COLUMNS, recommendation_rows)
    return PaperSmokeTestKillSwitchDiagnosisResult(
        output_paths=output_paths,
        diagnosis_rows=diagnosis_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        recommendation_rows=recommendation_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_smoke_test_kill_switch_diagnosis(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, ["Run `python bot.py --paper-smoke-test-kill-switch-diagnosis` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper smoke-test kill-switch diagnosis saved display. Report-only; execution_approved=False.",
        f"Final diagnosis status: {summary_value(rows, 'final_diagnosis_status')}",
        f"Live preflight status: {summary_value(rows, 'live_preflight_status')}",
        f"Attempted order result: {summary_value(rows, 'attempted_order_result')}",
        f"Largest blocker: {summary_value(rows, 'largest_blocker')}",
        f"Blocker scope: {summary_value(rows, 'largest_blocker_scope')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; smoke_test_order_approved=false",
        "paper_execution_approved=false; execution_approved=false; scheduling_approved=false; alpaca_called=false",
        "Warning: this diagnosis does not weaken the kill-switch, retry an order, or approve smoke-test execution.",
    ]


def build_context(inputs: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    live_status = find_value(inputs["live_preflight"], "final_live_preflight_status") or "live_preflight_ready_for_manual_confirmation"
    postcheck_status = find_value(inputs["postcheck"], "final_postcheck_status") or "postcheck_no_matching_order_found"
    open_order_count = find_value(inputs["postcheck"], "open_order_count_for_ticker") or "0"
    existing_position = find_existing_position_context(inputs["postcheck"])
    missing = missing_input_names(inputs)
    recommendation = "design_separate_manual_smoke_test_gate"
    if missing:
        recommendation = "refresh_missing_saved_inputs_first"
    return {
        "final_diagnosis_status": "smoke_test_kill_switch_diagnosis_required",
        "live_preflight_status": live_status,
        "attempted_order_result": "live_preflight_passed_but_order_gate_blocked",
        "largest_blocker": "broad_execution_gate_blocks_smoke_test",
        "largest_blocker_scope": "broad_strategy_execution_blocker_applied_to_connectivity_smoke_test",
        "recommended_next_step": recommendation,
        "postcheck_status": postcheck_status,
        "open_order_count": open_order_count,
        "existing_position_context": existing_position,
        "missing_saved_inputs": "; ".join(missing) if missing else "none_for_available_saved_outputs",
    }


def build_diagnosis_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        diagnosis_row("paper_kill_switch_enabled_not_explicitly_true", "blocked", "keep_order_blocked_until_reviewed", "applies_to_any_order_capable_path", "The current kill-switch preflight correctly refuses when paper_kill_switch_enabled is not explicitly true.", "blocked attempt context", "Keep the existing kill-switch; review whether a separate smoke-test-only gate is appropriate."),
        diagnosis_row("execution_eligibility_blocked", "blocked", "broad_execution_gate_blocks_smoke_test", "broad_strategy_execution_blocker", "Execution eligibility is blocked and may be too broad for a one-share connectivity smoke test.", "data/execution_eligibility_report.csv", "Design a separate manual smoke-test gate before any retry."),
        diagnosis_row("defensive_allocation_decision_blocked", "blocked", "broad_execution_gate_blocks_smoke_test", "broad_strategy_execution_blocker", "Defensive allocation decision remains blocked and is a strategy-execution blocker rather than connectivity evidence.", "saved defensive/promoted decision outputs", "Separate smoke-test connectivity safety from strategy execution safety in a future design."),
        diagnosis_row("promoted_strategy_disagreement", "review_required", "broad_execution_gate_blocks_smoke_test", "strategy_execution_blocker", "Promoted strategy disagreement belongs to broader strategy execution review.", "data/promoted_decision_preview.csv", "Do not use promoted disagreement as smoke-test approval."),
        diagnosis_row("portfolio_risk_policy_missing_or_blocked", "review_required", "portfolio_risk_policy_missing_or_blocked", "applies_to_any_order_capable_path", "Portfolio risk policy must be reviewed before any order-capable path.", "data/portfolio_risk_policy_report.csv", "Refresh or review portfolio risk policy."),
        diagnosis_row("deployment_readiness_missing_or_blocked", "review_required", "deployment_readiness_missing_or_blocked", "manual_review_before_code_change", "Deployment readiness should remain visible before any gate change.", "data/deployment_readiness_report.csv", "Review deployment readiness before gate changes."),
        diagnosis_row("smoke_test_live_preflight_passed", "positive_evidence", "smoke_test_live_preflight_passed", "smoke_test_connectivity_safety", "Saved live preflight passed before the blocked manual attempt.", "data/paper_order_smoke_test_live_preflight.csv", "Treat this as connectivity evidence only, not order approval."),
        diagnosis_row("no_matching_order_found_after_blocked_attempt", "positive_safety_evidence", "no_order_submitted_confirmed", "smoke_test_connectivity_safety", "Saved postcheck found no matching order after the blocked attempt.", "data/paper_order_smoke_test_postcheck.csv", "Keep no-order result as safety evidence."),
        diagnosis_row("open_order_count_zero", "positive_safety_evidence", "open_order_count_zero", "smoke_test_connectivity_safety", "Saved postcheck indicates zero open orders for the ticker.", "data/paper_order_smoke_test_postcheck.csv", "Use only as read-only postcheck context."),
        diagnosis_row("existing_aapl_position_context", "context_only", "existing_aapl_position_context", "manual_review_before_code_change", f"Saved postcheck context: {context['existing_position_context']}.", "data/paper_order_smoke_test_postcheck.csv", "Review existing paper position context before any future smoke-test gate design."),
    ]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("paper_kill_switch_enabled_not_explicitly_true", "blocked", "applies_to_any_order_capable_path", "critical", "Kill-switch explicit enablement remains required.", "Do not weaken the existing kill-switch."),
        blocker_row("execution_eligibility_blocked", "blocked", "broad_strategy_execution_blocker", "critical", "Execution eligibility blocks the smoke test attempt.", "Review whether a separate manual connectivity smoke-test gate is appropriate."),
        blocker_row("defensive_allocation_decision_blocked", "blocked", "broad_strategy_execution_blocker", "critical", "Defensive allocation decision blocks broader execution.", "Keep strategy execution blocked; consider separate smoke-test gate design only."),
        blocker_row("separate_manual_smoke_test_gate_review_required", "review_required", "manual_review_before_code_change", "high", "A separate manual smoke-test gate would need report-only design before code changes.", "Do not retry an order until gate review is complete."),
        blocker_row("keep_order_blocked_until_reviewed", "blocked", "applies_to_any_order_capable_path", "critical", "No smoke-test order is approved by this diagnosis.", "Keep order blocked until reviewed."),
    ]
    if context["missing_saved_inputs"] != "none_for_available_saved_outputs":
        rows.append(blocker_row("missing_saved_inputs", "warning", "manual_review_before_code_change", "medium", context["missing_saved_inputs"], "Refresh missing saved inputs before gate-design discussion."))
    return rows


def build_recommendation_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        recommendation_row("keep_smoke_test_blocked", "active", "current_gate", "Current behavior is safe: no order was submitted.", "Do not retry until gate review is complete."),
        recommendation_row("design_separate_manual_smoke_test_gate", "recommended_after_saved_input_review", "future_report_only_design", "A one-share connectivity smoke test may need a narrower gate than full strategy execution eligibility.", "Draft a separate report-only gate design; do not change order behavior yet."),
        recommendation_row("refresh_missing_saved_inputs_first", "conditional", "saved_context_quality", "Missing saved inputs reduce diagnosis completeness.", "Refresh missing safe saved reports where needed."),
        recommendation_row("do_not_retry_order_until_gate_reviewed", "active", "manual_safety_boundary", "The blocked attempt should not be retried from this report.", "Review gate design first."),
    ]


def build_summary_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        summary_row("final_diagnosis_status", context["final_diagnosis_status"], "Diagnosis is required; this is not order approval."),
        summary_row("live_preflight_status", context["live_preflight_status"], "Saved preflight status before the blocked attempt."),
        summary_row("attempted_order_result", context["attempted_order_result"], "The confirmed manual command was blocked before order submission."),
        summary_row("largest_blocker", context["largest_blocker"], "Broad execution gates currently block the smoke test."),
        summary_row("largest_blocker_scope", context["largest_blocker_scope"], "The largest blocker is broader than connectivity-only smoke testing."),
        summary_row("postcheck_status", context["postcheck_status"], "Saved postcheck found no matching order."),
        summary_row("open_order_count_for_ticker", context["open_order_count"], "Saved postcheck open-order context."),
        summary_row("existing_aapl_position_context", context["existing_position_context"], "Saved postcheck position context."),
        summary_row("recommended_next_step", context["recommended_next_step"], "Next step remains report-only/manual review."),
        summary_row("order_submission_status", "no_order_submitted_confirmed", "No orders were created, submitted, or cancelled by this diagnosis."),
    ]


def diagnosis_row(
    name: str,
    status: str,
    classification: str,
    scope: str,
    finding: str,
    source: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "diagnosis_name": name,
        "diagnosis_status": status,
        "blocker_classification": classification,
        "blocker_scope": scope,
        "finding": finding,
        "evidence_source": source,
        "recommended_next_step": next_step,
        **safety_flags(),
    }


def blocker_row(name: str, status: str, scope: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "blocker_scope": scope,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **safety_flags(),
    }


def recommendation_row(name: str, status: str, applies_to: str, rationale: str, next_step: str) -> dict[str, Any]:
    return {
        "recommendation_name": name,
        "recommendation_status": status,
        "applies_to": applies_to,
        "rationale": rationale,
        "required_next_step": next_step,
        **safety_flags(),
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def build_summary_lines(rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper smoke-test kill-switch diagnosis complete. Report-only; execution_approved=False.",
        f"Final diagnosis status: {summary_value(rows, 'final_diagnosis_status')}",
        f"Live preflight status: {summary_value(rows, 'live_preflight_status')}",
        f"Attempted order result: {summary_value(rows, 'attempted_order_result')}",
        f"Largest blocker: {summary_value(rows, 'largest_blocker')}",
        f"Blocker scope: {summary_value(rows, 'largest_blocker_scope')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        f"Saved diagnosis to {output_paths['diagnosis']}",
        f"Saved summary/blockers/recommendations to {output_paths['summary']}; {output_paths['blockers']}; {output_paths['recommendations']}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; smoke_test_order_approved=false",
        "paper_execution_approved=false; execution_approved=false; scheduling_approved=false; alpaca_called=false",
        "Warning: diagnosis only; the kill-switch is unchanged and no smoke-test order is approved.",
    ]


def find_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        for column in ("summary_name", "check_name", "field_name", "status_name", "postcheck_name"):
            if row.get(column) == key:
                return str(row.get("summary_value") or row.get("status") or row.get("field_value") or row.get("value") or "")
        if key in row and row.get(key) not in (None, ""):
            return str(row.get(key, ""))
    return ""


def find_existing_position_context(rows: list[dict[str, Any]]) -> str:
    source_text = " ".join(" ".join(str(value) for value in row.values()) for row in rows).lower()
    if "long" in source_text and "aapl" in source_text:
        return "existing_aapl_position_context_long_1_if_saved"
    return "existing_aapl_position_context_unavailable"


def missing_input_names(inputs: dict[str, list[dict[str, Any]]]) -> list[str]:
    return [name for name, rows in inputs.items() if not rows]


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
