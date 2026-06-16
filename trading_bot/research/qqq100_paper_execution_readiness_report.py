"""Saved-output-only QQQ100 paper execution readiness report.

This report reads saved CSV artefacts only. It does not call Alpaca, refresh
market data, read positions, create orders, write SQLite, send alerts, schedule
anything, change config defaults, or add a QQQ100 execution command.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

INPUT_FILES = {
    "smoke_postcheck": Path("data/paper_order_smoke_test_postcheck.csv"),
    "smoke_gate": Path("data/paper_order_smoke_test_gate_report.csv"),
    "smoke_preflight": Path("data/paper_order_smoke_test_live_preflight.csv"),
    "alpaca_connectivity": Path("data/alpaca_connectivity_diagnostics.csv"),
    "qqq100_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action": Path("data/qqq100_action_preview.csv"),
    "promoted_preview": Path("data/promoted_strategy_preview.csv"),
    "promoted_decision": Path("data/promoted_decision_preview.csv"),
    "portfolio_preview": Path("data/multi_strategy_portfolio_preview.csv"),
    "portfolio_conflicts": Path("data/multi_strategy_portfolio_preview_conflicts.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "execution_eligibility": Path("data/execution_eligibility_report.csv"),
    "paper_kill_switch_readiness": Path("data/paper_kill_switch_readiness_report.csv"),
    "paper_kill_switch_gate": Path("data/paper_kill_switch_gate_report.csv"),
    "paper_execution_protection": Path("data/paper_execution_protection_report.csv"),
    "project_research_state": Path("data/project_research_state_summary.csv"),
}

OUTPUT_FILES = {
    "report": Path("data/qqq100_paper_execution_readiness_report.csv"),
    "summary": Path("data/qqq100_paper_execution_readiness_summary.csv"),
    "evidence": Path("data/qqq100_paper_execution_readiness_evidence.csv"),
    "blockers": Path("data/qqq100_paper_execution_readiness_blockers.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "report_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "qqq100_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "alpaca_called",
]

REPORT_COLUMNS = [
    "created_at",
    "strategy_name",
    "ticker",
    "check_name",
    "check_status",
    "readiness_label",
    "finding",
    "evidence_source",
    "blocker",
    "recommended_next_step",
    *SAFETY_COLUMNS,
]
SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_COLUMNS,
]
EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_value",
    "evidence_source",
    "details",
    *SAFETY_COLUMNS,
]
BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "preview_only": True,
    "execution_approved": False,
    "paper_execution_approved": False,
    "qqq100_execution_approved": False,
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
class Qqq100PaperExecutionReadinessReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_paper_execution_readiness_report(
    root_dir: Path | str = ".",
) -> Qqq100PaperExecutionReadinessReportResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    context = build_context(inputs)
    report_rows = build_report_rows(created_at, context)
    evidence_rows = build_evidence_rows(context, inputs)
    blocker_rows = build_blocker_rows(context, inputs)
    summary_rows = build_summary_rows(context)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return Qqq100PaperExecutionReadinessReportResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["report"]),
    )


def show_qqq100_paper_execution_readiness_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "QQQ100 paper execution readiness report is missing.",
            "Run `python bot.py --qqq100-paper-execution-readiness-report` first.",
            "execution_approved=false; paper_execution_approved=false; qqq100_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 paper execution readiness saved display. Saved-output report only; no execution approved.",
        f"final_readiness_status: {summary_value(rows, 'final_readiness_status')}",
        f"smoke_test_status: {summary_value(rows, 'smoke_test_status')}",
        f"qqq100_preview_status: {summary_value(rows, 'qqq100_preview_status')}",
        f"qqq100_action_preview_status: {summary_value(rows, 'qqq100_action_preview_status')}",
        f"promoted_preview_status: {summary_value(rows, 'promoted_preview_status')}",
        f"portfolio_overlap_warning_status: {summary_value(rows, 'portfolio_overlap_warning_status')}",
        f"biggest_blocker: {summary_value(rows, 'biggest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false",
        "execution_approved=false; paper_execution_approved=false; qqq100_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    smoke_status = detect_smoke_test_status(inputs["smoke_postcheck"])
    preview_status = detect_preview_status(inputs["qqq100_signal"])
    action_status = "qqq100_action_preview_present" if inputs["qqq100_action"] else "qqq100_action_preview_missing"
    promoted_status = detect_promoted_preview_status(inputs["promoted_preview"])
    overlap_status = detect_overlap_status(inputs["portfolio_conflicts"])
    connectivity_status = detect_connectivity_status(inputs["alpaca_connectivity"])
    desired_position = first_nonempty(inputs["qqq100_signal"], ["desired_position"]) or first_nonempty(inputs["qqq100_action"], ["desired_position"]) or "unavailable"
    missing = missing_input_names(inputs)
    blockers = static_blockers()

    positive_ready = (
        smoke_status == "smoke_test_success_confirmed"
        and preview_status == "qqq100_preview_chain_ready"
        and action_status == "qqq100_action_preview_present"
        and promoted_status == "qqq100_promoted_preview_present"
        and bool(inputs["portfolio_preview"])
    )
    if positive_ready:
        final_status = "qqq100_ready_for_manual_execution_design_review"
    elif any(name in missing for name in ["smoke_postcheck", "qqq100_signal", "qqq100_action", "promoted_preview"]):
        final_status = "qqq100_insufficient_saved_evidence"
    elif missing:
        final_status = "qqq100_needs_more_readiness_inputs"
    else:
        final_status = "qqq100_execution_design_blocked"

    return {
        "final_readiness_status": final_status,
        "smoke_test_status": smoke_status,
        "alpaca_connectivity_status": connectivity_status,
        "qqq100_preview_status": preview_status,
        "qqq100_action_preview_status": action_status,
        "promoted_preview_status": promoted_status,
        "portfolio_overlap_warning_status": overlap_status,
        "desired_position": desired_position,
        "high_growth_status": "high_growth_branch_research_only_excluded",
        "crypto_status": "crypto_research_only_excluded",
        "biggest_blocker": blockers[0][0],
        "recommended_next_step": "manual_design_review_for_qqq100_execution_command_only_after_blockers_are_resolved",
        "missing_saved_inputs": "; ".join(missing) if missing else "none_for_required_review_inputs",
    }


def build_report_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row(created_at, "aapl_smoke_test", context["smoke_test_status"], "smoke_test_success_confirmed", "Saved AAPL smoke-test postcheck is recognised as evidence only.", "data/paper_order_smoke_test_postcheck.csv", "none_for_smoke_test_evidence", "Use as prerequisite evidence only; do not submit follow-up orders."),
        report_row(created_at, "alpaca_connectivity", context["alpaca_connectivity_status"], "saved_connectivity_context", "Saved connectivity diagnostics are context only.", "data/alpaca_connectivity_diagnostics.csv", "none_for_saved_connectivity_context", "Keep broker checks read-only unless separately reviewed."),
        report_row(created_at, "qqq100_preview_signal", context["qqq100_preview_status"], "qqq100_preview_chain_ready", f"Saved QQQ100 desired_position={context['desired_position']}.", "data/qqq100_preview_signal_pack.csv", "none_for_preview_signal", "Use saved signal only as design evidence."),
        report_row(created_at, "qqq100_action_preview", context["qqq100_action_preview_status"], "qqq100_preview_chain_ready", "Saved QQQ100 action preview exists where available.", "data/qqq100_action_preview.csv", "none_for_action_preview", "Do not treat action preview as order instruction."),
        report_row(created_at, "promoted_preview", context["promoted_preview_status"], "qqq100_promoted_preview_present", "QQQ100 promoted preview row is recognised from saved output where present.", "data/promoted_strategy_preview.csv", "none_for_promoted_preview", "Keep promoted preview non-executable."),
        report_row(created_at, "portfolio_overlap", context["portfolio_overlap_warning_status"], "portfolio_overlap_review_required", "Saved portfolio combiner overlap warnings are surfaced.", "data/multi_strategy_portfolio_preview_conflicts.csv", "portfolio_overlap_review_required", "Review growth/tech/high-beta overlap before any design discussion."),
        report_row(created_at, "high_growth_branch", context["high_growth_status"], "execution_blocked", "High-growth branch remains research-only and excluded.", "data/multi_strategy_portfolio_preview.csv", "high_growth_excluded", "Do not include high-growth in QQQ100 execution design."),
        report_row(created_at, "crypto_branch", context["crypto_status"], "execution_blocked", "Crypto remains research-only and excluded.", "data/multi_strategy_portfolio_preview.csv", "crypto_excluded", "Do not include crypto in QQQ100 execution design."),
        report_row(created_at, "sizing_policy", "blocked", "sizing_policy_not_approved", "Order sizing policy for QQQ100 is not approved.", "data/portfolio_risk_policy_report.csv", "sizing_policy_not_approved", "Define sizing policy in a separate review."),
        report_row(created_at, "qqq100_execution_command", "blocked", "qqq100_execution_command_not_added", "No QQQ100 execution command was added.", "code inventory", "qqq100_execution_command_not_added", "Create only a future report-only design unless separately approved."),
        report_row(created_at, "kill_switch", "blocked", "qqq100_kill_switch_required", "QQQ100-specific kill-switch preflight is not implemented.", "data/paper_kill_switch_gate_report.csv", "qqq100_kill_switch_required", "Design QQQ100 kill-switch preflight before any paper command."),
        report_row(created_at, "open_duplicate_checks", "blocked", "qqq100_duplicate_open_order_checks_required", "QQQ100-specific open-order and duplicate checks are not implemented.", "saved paper-order smoke-test gate", "qqq100_duplicate_open_order_checks_required", "Design QQQ100 broker-history checks separately."),
        report_row(created_at, "postcheck", "blocked", "qqq100_postcheck_required", "QQQ100-specific postcheck is not implemented.", "data/paper_order_smoke_test_postcheck.csv", "qqq100_postcheck_required", "Design QQQ100 postcheck before paper execution discussion."),
        report_row(created_at, "manual_confirmation", "blocked", "qqq100_manual_confirmation_required", "QQQ100 manual confirmation wording is not implemented.", "manual runbook boundary", "qqq100_manual_confirmation_required", "Draft manual confirmation wording separately."),
        report_row(created_at, "execution", "blocked", "execution_blocked", "Execution eligibility remains false.", "data/execution_eligibility_report.csv", "execution_blocked", "Keep QQQ100 disconnected from execution."),
        report_row(created_at, "scheduling", "blocked", "scheduling_not_approved", "Scheduling remains false.", "project scheduling boundary", "scheduling_not_approved", "Do not schedule QQQ100 execution workflows."),
    ]


def build_evidence_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        evidence_row("smoke_test_evidence", context["smoke_test_status"], "data/paper_order_smoke_test_postcheck.csv", "Recognises successful AAPL postcheck only from saved CSV."),
        evidence_row("recent_order_match_status", find_saved_value(inputs["smoke_postcheck"], "recent_order_match_status") or "unavailable", "data/paper_order_smoke_test_postcheck.csv", "Redacted broker-history match status from saved postcheck."),
        evidence_row("qqq100_desired_position", context["desired_position"], "data/qqq100_preview_signal_pack.csv", "Saved QQQ100 desired position."),
        evidence_row("qqq100_preview_status", context["qqq100_preview_status"], "data/qqq100_preview_signal_pack.csv", "Saved QQQ100 preview signal status."),
        evidence_row("qqq100_action_preview_status", context["qqq100_action_preview_status"], "data/qqq100_action_preview.csv", "Saved action-preview status."),
        evidence_row("promoted_preview_status", context["promoted_preview_status"], "data/promoted_strategy_preview.csv", "Saved promoted preview row status."),
        evidence_row("portfolio_overlap_warning_status", context["portfolio_overlap_warning_status"], "data/multi_strategy_portfolio_preview_conflicts.csv", "Saved portfolio overlap warnings."),
        evidence_row("high_growth_branch", context["high_growth_status"], "saved portfolio/research context", "High-growth branch remains excluded from execution."),
        evidence_row("crypto_branch", context["crypto_status"], "saved portfolio/research context", "Crypto remains excluded from execution."),
        evidence_row("missing_saved_inputs", context["missing_saved_inputs"], "saved CSV inventory", "Missing inputs reduce completeness but do not approve execution."),
    ]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:  # noqa: ARG001
    rows = [
        blocker_row("sizing_policy_not_approved", "blocked", "critical", "QQQ100 order sizing policy is not approved.", "Define sizing separately before any paper execution command design."),
        blocker_row("qqq100_execution_command_not_added", "blocked", "critical", "No QQQ100 execution command was added.", "Keep this report as readiness review only."),
        blocker_row("qqq100_kill_switch_required", "blocked", "critical", "QQQ100-specific kill-switch preflight is not implemented.", "Design kill-switch preflight separately."),
        blocker_row("qqq100_duplicate_open_order_checks_required", "blocked", "critical", "QQQ100-specific duplicate/open-order checks are not implemented.", "Design read-only broker checks separately."),
        blocker_row("qqq100_postcheck_required", "blocked", "critical", "QQQ100-specific postcheck is not implemented.", "Design postcheck separately."),
        blocker_row("qqq100_manual_confirmation_required", "blocked", "high", "QQQ100 manual confirmation wording is not implemented.", "Draft confirmation wording separately."),
        blocker_row("portfolio_overlap_review_required", "blocked", "high", "Growth/tech/high-beta overlap warnings require review.", "Resolve overlap review before any paper command design."),
        blocker_row("execution_blocked", "blocked", "critical", "Execution remains blocked.", "Do not connect QQQ100 to orders."),
        blocker_row("scheduling_not_approved", "blocked", "critical", "Scheduling remains blocked.", "Do not schedule QQQ100 execution."),
    ]
    if context["missing_saved_inputs"] != "none_for_required_review_inputs":
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", context["missing_saved_inputs"], "Regenerate missing safe saved reports if needed."))
    return rows


def build_summary_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        summary_row("final_readiness_status", context["final_readiness_status"], "This may allow manual execution-design review only, not paper execution."),
        summary_row("smoke_test_status", context["smoke_test_status"], "Saved AAPL smoke-test postcheck status."),
        summary_row("alpaca_connectivity_status", context["alpaca_connectivity_status"], "Saved connectivity diagnostic status."),
        summary_row("qqq100_preview_status", context["qqq100_preview_status"], "Saved QQQ100 preview signal status."),
        summary_row("qqq100_action_preview_status", context["qqq100_action_preview_status"], "Saved action-preview status."),
        summary_row("promoted_preview_status", context["promoted_preview_status"], "Saved promoted preview status."),
        summary_row("portfolio_overlap_warning_status", context["portfolio_overlap_warning_status"], "Saved portfolio overlap warning status."),
        summary_row("desired_position", context["desired_position"], "Saved QQQ100 desired position."),
        summary_row("biggest_blocker", context["biggest_blocker"], "Largest static blocker before any execution design."),
        summary_row("recommended_next_step", context["recommended_next_step"], "Manual design review only."),
        summary_row("execution_status", "execution_blocked", "No QQQ100 paper execution is approved."),
        summary_row("scheduling_status", "scheduling_not_approved", "Scheduling is not approved."),
    ]


def report_row(created_at: str, name: str, status: str, label: str, finding: str, source: str, blocker: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": STRATEGY_NAME,
        "ticker": TICKER,
        "check_name": name,
        "check_status": status,
        "readiness_label": label,
        "finding": finding,
        "evidence_source": source,
        "blocker": blocker,
        "recommended_next_step": next_step,
        **safety_flags(),
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def evidence_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "evidence_source": source, "details": details, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **safety_flags()}


def detect_smoke_test_status(rows: list[dict[str, Any]]) -> str:
    final_status = find_final_status(rows)
    match_found = any(str(row.get("recent_order_match_found", "")).lower() == "true" for row in rows)
    match_status = find_saved_value(rows, "recent_order_match_status")
    if final_status == "postcheck_order_observed_filled_manual_review" or (match_found and match_status == "filled"):
        return "smoke_test_success_confirmed"
    if not rows:
        return "smoke_test_saved_postcheck_missing"
    return "smoke_test_not_confirmed_in_saved_postcheck"


def detect_preview_status(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "qqq100_preview_signal_missing"
    desired = first_nonempty(rows, ["desired_position"])
    data_status = first_nonempty(rows, ["data_status"])
    ticker = first_nonempty(rows, ["ticker", "symbol"])
    if (ticker in {"", TICKER}) and desired and data_status == "ok":
        return "qqq100_preview_chain_ready"
    return "qqq100_preview_needs_review"


def detect_promoted_preview_status(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("strategy_name") == STRATEGY_NAME or row.get("ticker") == TICKER:
            return "qqq100_promoted_preview_present"
    return "qqq100_promoted_preview_missing"


def detect_overlap_status(rows: list[dict[str, Any]]) -> str:
    warnings = {
        str(row.get("conflict_name", ""))
        for row in rows
        if str(row.get("severity", "")).lower() == "warning" or "warning" in str(row.get("conflict_status", "")).lower()
    }
    if {"growth_tech_overlap_warning", "high_beta_stack_warning"}.intersection(warnings):
        return "portfolio_overlap_review_required"
    if rows:
        return "portfolio_preview_present_no_major_warning_detected"
    return "portfolio_preview_missing"


def detect_connectivity_status(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "saved_connectivity_diagnostics_missing"
    statuses = {str(row.get("diagnostic_status", "")).strip() for row in rows}
    if "alpaca_api_reachable" in statuses:
        return "alpaca_api_reachable_in_saved_diagnostics"
    if any("unreachable" in status or "manual_review" in status for status in statuses):
        return "saved_connectivity_manual_review_required"
    return "saved_connectivity_context_present"


def static_blockers() -> list[tuple[str, str]]:
    return [
        ("sizing_policy_not_approved", "Define QQQ100 sizing before any paper execution command design."),
        ("qqq100_kill_switch_required", "Implement QQQ100-specific kill-switch preflight before any paper command."),
        ("qqq100_postcheck_required", "Implement QQQ100-specific postcheck before any paper command."),
        ("execution_blocked", "Execution remains blocked."),
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "QQQ100 paper execution readiness report complete. Saved-output report only; no execution approved.",
        f"final_readiness_status: {summary_value(summary_rows, 'final_readiness_status')}",
        f"smoke_test_status: {summary_value(summary_rows, 'smoke_test_status')}",
        f"qqq100_preview_status: {summary_value(summary_rows, 'qqq100_preview_status')}",
        f"qqq100_action_preview_status: {summary_value(summary_rows, 'qqq100_action_preview_status')}",
        f"promoted_preview_status: {summary_value(summary_rows, 'promoted_preview_status')}",
        f"portfolio_overlap_warning_status: {summary_value(summary_rows, 'portfolio_overlap_warning_status')}",
        f"biggest_blocker: {summary_value(summary_rows, 'biggest_blocker')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false",
        "execution_approved=false; paper_execution_approved=false; qqq100_execution_approved=false; scheduling_approved=false",
        f"Saved report to {report_path}",
    ]


def find_final_status(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("check_name") == "final_postcheck_status":
            return str(row.get("check_status") or row.get("final_postcheck_status") or "")
    return ""


def find_saved_value(rows: list[dict[str, Any]], field_name: str) -> str:
    for row in rows:
        value = str(row.get(field_name, "")).strip()
        if value:
            return value
    return ""


def first_nonempty(rows: list[dict[str, Any]], names: list[str]) -> str:
    for row in rows:
        for name in names:
            value = str(row.get(name, "")).strip()
            if value:
                return value
    return ""


def missing_input_names(inputs: dict[str, list[dict[str, Any]]]) -> list[str]:
    return [name for name, rows in inputs.items() if not rows]


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return "unavailable"


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
