"""Saved-data paper execution discussion readiness review.

This checkpoint is report-only. It reads saved research/report CSVs and writes a
conservative readiness CSV for a future manually reviewed stock/ETF paper
execution design discussion. It never contacts broker, market-data, alert,
database, scheduling, or execution paths.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("data/stock_etf_paper_execution_readiness_report.csv")

STOCK_ETF_LEAD = "codex_ambitious_concentrated_growth_persistence"
STOCK_ETF_STATUS = "codex_ambitious_active_research_lead_cost_review_required"
FINAL_BLOCKED_LABEL = "paper_execution_discussion_blocked_by_cost_review_and_execution_gates"
FINAL_REVIEW_LABEL = "paper_execution_discussion_needs_manual_review"
FINAL_DESIGN_ONLY_LABEL = "paper_execution_discussion_ready_for_design_only"

INPUT_FILES = {
    "project_state_summary": Path("data/project_research_state_summary.csv"),
    "project_state_refresh": Path("data/project_research_state_refresh.csv"),
    "lead_decision_summary": Path("data/codex_ambitious_lead_decision_summary.csv"),
    "lead_decision_evidence": Path("data/codex_ambitious_lead_decision_evidence.csv"),
    "split_drawdown_validation": Path("data/codex_ambitious_split_drawdown_validation.csv"),
    "promoted_decision_preview": Path("data/promoted_decision_preview.csv"),
    "execution_eligibility": Path("data/execution_eligibility_report.csv"),
    "paper_execution_protection": Path("data/paper_execution_protection_report.csv"),
    "paper_kill_switch_readiness": Path("data/paper_kill_switch_readiness_report.csv"),
    "paper_kill_switch_gate": Path("data/paper_kill_switch_gate_report.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
}

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "evidence_source",
    "details",
    "blocker",
    "recommended_next_step",
    "execution_approved",
    "scheduling_approved",
    "paper_execution_discussion_status",
]


@dataclass
class StockEtfPaperExecutionReadinessResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_stock_etf_paper_execution_readiness_report(
    root_dir: Path | str = ".",
) -> StockEtfPaperExecutionReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(root / relative_path) for name, relative_path in INPUT_FILES.items()}
    rows = build_readiness_rows(created_at, inputs)
    final_label = choose_final_label(rows)
    rows.append(
        readiness_row(
            created_at,
            "final_paper_execution_discussion_status",
            final_label,
            "blocked" if "blocked" in final_label else ("warning" if "manual_review" in final_label else "info"),
            "saved readiness rows",
            final_details(final_label, rows),
            final_label != FINAL_DESIGN_ONLY_LABEL,
            final_next_step(final_label),
            final_label,
        )
    )
    output_path = root / OUTPUT_PATH
    write_rows(output_path, rows)
    return StockEtfPaperExecutionReadinessResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows),
    )


def build_readiness_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    project_summary = inputs["project_state_summary"]
    lead_summary = inputs["lead_decision_summary"]
    split_drawdown = inputs["split_drawdown_validation"]
    promoted_decision = inputs["promoted_decision_preview"]
    execution_eligibility = inputs["execution_eligibility"]
    paper_protection = inputs["paper_execution_protection"]
    kill_switch_readiness = inputs["paper_kill_switch_readiness"]
    kill_switch_gate = inputs["paper_kill_switch_gate"]
    portfolio_risk = inputs["portfolio_risk_policy"]

    rows: list[dict[str, Any]] = []
    rows.extend(saved_input_rows(created_at, inputs))
    rows.extend(
        [
            research_lead_presence_row(created_at, project_summary, lead_summary),
            research_lead_status_row(created_at, project_summary, lead_summary),
            cost_review_row(created_at, lead_summary),
            split_decay_row(created_at, lead_summary, split_drawdown),
            drawdown_context_row(created_at, lead_summary, split_drawdown),
            preview_readiness_row(created_at, promoted_decision),
            execution_eligibility_row(created_at, execution_eligibility),
            paper_execution_protection_row(created_at, paper_protection),
            kill_switch_readiness_row(created_at, kill_switch_readiness, kill_switch_gate),
            portfolio_risk_policy_row(created_at, portfolio_risk),
            credentials_connectivity_boundary_row(created_at),
            crypto_scope_row(created_at, project_summary),
            scheduling_boundary_row(created_at),
            high_risk_workflows_boundary_row(created_at),
        ]
    )
    return rows


def saved_input_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, relative_path in INPUT_FILES.items():
        present = bool(inputs[name])
        rows.append(
            readiness_row(
                created_at,
                f"saved_input_{name}",
                "present" if present else "missing_or_empty_saved_input",
                "info" if present else "warning",
                str(relative_path),
                f"Saved input {relative_path} {'is available' if present else 'is missing or empty'}.",
                not present and name in {"project_state_summary", "lead_decision_summary"},
                "regenerate_saved_report_if_this_evidence_is_required" if not present else "none",
                FINAL_REVIEW_LABEL,
            )
        )
    return rows


def research_lead_presence_row(
    created_at: str,
    project_summary: list[dict[str, Any]],
    lead_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    saved_lead = summary_value(project_summary, "stock_etf_active_research_lead")
    lead_found = saved_lead == STOCK_ETF_LEAD or any_value_contains(lead_summary, STOCK_ETF_LEAD)
    return readiness_row(
        created_at,
        "stock_etf_research_lead_presence",
        "lead_confirmed" if lead_found else "manual_review_required_missing_lead",
        "info" if lead_found else "blocked",
        "data/project_research_state_summary.csv; data/codex_ambitious_lead_decision_summary.csv",
        f"Expected stock/ETF lead: {STOCK_ETF_LEAD}; saved lead: {saved_lead or 'unavailable'}.",
        not lead_found,
        "run_project_research_state_refresh_and_codex_ambitious_lead_decision" if not lead_found else "none",
        FINAL_REVIEW_LABEL,
    )


def research_lead_status_row(
    created_at: str,
    project_summary: list[dict[str, Any]],
    lead_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    saved_status = summary_value(project_summary, "stock_etf_status_and_blocker")
    final_label = summary_value(lead_summary, "final_lead_decision_label")
    details = (
        f"Current stock/ETF context is research-only. status={saved_status or STOCK_ETF_STATUS}; "
        f"lead_decision_label={final_label or STOCK_ETF_STATUS}."
    )
    return readiness_row(
        created_at,
        "stock_etf_research_lead_status",
        "research_only_cost_review_required",
        "warning",
        "data/project_research_state_summary.csv; data/codex_ambitious_lead_decision_summary.csv",
        details,
        True,
        "complete_cost_review_before_any_paper_execution_design_discussion",
        FINAL_REVIEW_LABEL,
    )


def cost_review_row(created_at: str, lead_summary: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = summary_value(lead_summary, "remaining_blockers")
    evidence = summary_value(lead_summary, "cost_evidence")
    if not blockers:
        blockers = "survives_10_bps=True; survives_25_bps=False"
    if not evidence:
        evidence = "Main blocker: 25 bps cost review not survived."
    return readiness_row(
        created_at,
        "cost_review_blocker",
        "blocked_cost_review_required",
        "blocked",
        "data/codex_ambitious_lead_decision_summary.csv",
        f"{evidence}; blockers={blockers}. Strong backtest results are not execution readiness.",
        True,
        "review_25_bps_cost_sensitivity_before_preview_or_paper_execution_discussion",
        FINAL_BLOCKED_LABEL,
    )


def split_decay_row(
    created_at: str,
    lead_summary: list[dict[str, Any]],
    split_drawdown: list[dict[str, Any]],
) -> dict[str, Any]:
    split_evidence = summary_value(lead_summary, "split_evidence")
    if not split_evidence:
        split_evidence = first_matching_detail(split_drawdown, ["split", "decay"]) or "Fixed splits remain positive but decaying."
    return readiness_row(
        created_at,
        "split_decay_context",
        "manual_review_required_split_decay",
        "warning",
        "data/codex_ambitious_lead_decision_summary.csv; data/codex_ambitious_split_drawdown_validation.csv",
        split_evidence,
        True,
        "review_fixed_split_decay_before_any_paper_execution_design_discussion",
        FINAL_REVIEW_LABEL,
    )


def drawdown_context_row(
    created_at: str,
    lead_summary: list[dict[str, Any]],
    split_drawdown: list[dict[str, Any]],
) -> dict[str, Any]:
    full_period = summary_value(lead_summary, "full_period_evidence")
    drawdown_detail = first_matching_detail(split_drawdown, ["drawdown", "MaxDD"])
    details = (
        full_period
        or drawdown_detail
        or "Full-period context: CAGR=14.1039; Sharpe=0.7192; MaxDD=-29.5357; Calmar=0.4775; cash=9.9651; turnover=19.0."
    )
    return readiness_row(
        created_at,
        "drawdown_and_full_period_context",
        "research_context_only",
        "info",
        "data/codex_ambitious_lead_decision_summary.csv; data/codex_ambitious_split_drawdown_validation.csv",
        f"{details} The candidate beats saved stock/ETF baselines in full-period research context but remains non-executable.",
        False,
        "keep_drawdown_context_in_manual_review_pack",
        FINAL_REVIEW_LABEL,
    )


def preview_readiness_row(created_at: str, promoted_decision: list[dict[str, Any]]) -> dict[str, Any]:
    if not promoted_decision:
        return readiness_row(
            created_at,
            "preview_readiness",
            "preview_discussion_not_ready",
            "blocked",
            "data/promoted_decision_preview.csv",
            "No saved promoted decision preview is available for this stock/ETF lead. Backtest strength is not preview or execution approval.",
            True,
            "create_or_review_a_separate_preview_decision_checkpoint_before_execution_design",
            FINAL_BLOCKED_LABEL,
        )
    approved = rows_with_truthy(promoted_decision, "execution_approved")
    return readiness_row(
        created_at,
        "preview_readiness",
        "preview_requires_manual_review",
        "blocked" if approved else "warning",
        "data/promoted_decision_preview.csv",
        "Saved promoted decision preview exists, but this readiness report does not infer execution approval from it.",
        True,
        "manually_review_preview_decision_outputs_and_keep_approval_flags_false",
        FINAL_REVIEW_LABEL,
    )


def execution_eligibility_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return readiness_row(
            created_at,
            "execution_eligibility_gate",
            "execution_discussion_blocked_missing_saved_gate",
            "blocked",
            "data/execution_eligibility_report.csv",
            "Saved execution eligibility report is missing or empty.",
            True,
            "run_execution_eligibility_report_and_review_blockers_before_discussion",
            FINAL_BLOCKED_LABEL,
        )
    statuses = status_counts(rows, ["eligibility_status", "check_status", "status"])
    blocked = any_status_contains(rows, ["blocked", "missing_input", "manual_review"])
    return readiness_row(
        created_at,
        "execution_eligibility_gate",
        "execution_discussion_blocked" if blocked else "saved_gate_present_manual_review_required",
        "blocked" if blocked else "warning",
        "data/execution_eligibility_report.csv",
        f"Saved eligibility status counts: {statuses}.",
        blocked,
        "resolve_saved_execution_eligibility_blockers_before_paper_execution_design" if blocked else "manual_review_required_before_design",
        FINAL_BLOCKED_LABEL if blocked else FINAL_REVIEW_LABEL,
    )


def paper_execution_protection_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return readiness_row(
            created_at,
            "paper_execution_protection_gate",
            "execution_discussion_blocked_missing_saved_protection_report",
            "blocked",
            "data/paper_execution_protection_report.csv",
            "Saved paper execution protection report is missing or empty.",
            True,
            "run_paper_execution_protection_report_before_design_discussion",
            FINAL_BLOCKED_LABEL,
        )
    blocked = any_status_contains(rows, ["blocked", "critical"]) or any_truthy(rows, "execution_approved")
    return readiness_row(
        created_at,
        "paper_execution_protection_gate",
        "protection_report_blocks_discussion" if blocked else "protection_report_present_manual_review_required",
        "blocked" if blocked else "warning",
        "data/paper_execution_protection_report.csv",
        f"Saved paper-protection status counts: {status_counts(rows, ['protection_status', 'severity'])}.",
        blocked,
        "resolve_saved_protection_blockers_and_keep_execution_approval_false",
        FINAL_BLOCKED_LABEL if blocked else FINAL_REVIEW_LABEL,
    )


def kill_switch_readiness_row(
    created_at: str,
    readiness_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not readiness_rows and not gate_rows:
        return readiness_row(
            created_at,
            "paper_kill_switch_gate",
            "execution_discussion_blocked_missing_kill_switch_reports",
            "blocked",
            "data/paper_kill_switch_readiness_report.csv; data/paper_kill_switch_gate_report.csv",
            "Saved paper kill-switch readiness/gate reports are missing or empty.",
            True,
            "run_and_review_saved_kill_switch_reports_before_any_paper_execution_design",
            FINAL_BLOCKED_LABEL,
        )
    combined = readiness_rows + gate_rows
    blocked = any_status_contains(combined, ["blocked", "missing", "manual_review"]) or any_truthy(combined, "execution_approved")
    return readiness_row(
        created_at,
        "paper_kill_switch_gate",
        "kill_switch_blocks_discussion" if blocked else "kill_switch_reports_present_manual_review_required",
        "blocked" if blocked else "warning",
        "data/paper_kill_switch_readiness_report.csv; data/paper_kill_switch_gate_report.csv",
        f"Saved kill-switch status counts: {status_counts(combined, ['readiness_status', 'gate_status', 'check_status', 'status'])}.",
        blocked,
        "resolve_kill_switch_blockers_before_design_discussion",
        FINAL_BLOCKED_LABEL if blocked else FINAL_REVIEW_LABEL,
    )


def portfolio_risk_policy_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return readiness_row(
            created_at,
            "portfolio_risk_policy_prerequisites",
            "execution_discussion_blocked_missing_risk_policy",
            "blocked",
            "data/portfolio_risk_policy_report.csv",
            "Saved portfolio risk policy report is missing or empty. Max positions, notional limits, duplicate exposure, strategy disagreement, and kill-switch prerequisites need review.",
            True,
            "run_portfolio_risk_policy_report_and_resolve_blockers_before_design_discussion",
            FINAL_BLOCKED_LABEL,
        )
    blocked = any_status_contains(rows, ["blocked", "missing", "manual_review"]) or any_truthy(rows, "execution_approved")
    return readiness_row(
        created_at,
        "portfolio_risk_policy_prerequisites",
        "risk_policy_blocks_discussion" if blocked else "risk_policy_present_manual_review_required",
        "blocked" if blocked else "warning",
        "data/portfolio_risk_policy_report.csv",
        f"Saved risk-policy status counts: {status_counts(rows, ['policy_status', 'check_status', 'status', 'severity'])}.",
        blocked,
        "resolve_or_manually_review_risk_policy_prerequisites_before_execution_design",
        FINAL_BLOCKED_LABEL if blocked else FINAL_REVIEW_LABEL,
    )


def credentials_connectivity_boundary_row(created_at: str) -> dict[str, Any]:
    return readiness_row(
        created_at,
        "broker_configuration_boundary",
        "separate_manual_verification_required",
        "warning",
        "static boundary",
        "This report deliberately does not read local configuration, credentials, account identifiers, broker connectivity, or positions. Those require a separate manual verification before any paper smoke test is even discussed.",
        True,
        "perform_separate_manual_credential_and_connectivity_review_only_after_all_saved_gates_pass",
        FINAL_REVIEW_LABEL,
    )


def crypto_scope_row(created_at: str, project_summary: list[dict[str, Any]]) -> dict[str, Any]:
    crypto_status = summary_value(project_summary, "crypto_status_and_blockers") or "crypto_manual_review_not_ready_for_preview_discussion"
    crypto_lead = summary_value(project_summary, "crypto_research_lead") or "crypto lead unavailable"
    return readiness_row(
        created_at,
        "crypto_execution_scope",
        "crypto_execution_out_of_scope_not_approved",
        "blocked",
        "data/project_research_state_summary.csv",
        f"Crypto context: lead={crypto_lead}; status={crypto_status}. Crypto remains manual-review-only and not preview-ready.",
        True,
        "keep_crypto_execution_out_of_scope",
        FINAL_BLOCKED_LABEL,
    )


def scheduling_boundary_row(created_at: str) -> dict[str, Any]:
    return readiness_row(
        created_at,
        "scheduling_boundary",
        "execution_scheduling_not_approved",
        "blocked",
        "Hermes/VPS documentation",
        "Existing Hermes status automation is for status/display only. No execution-capable scheduling is approved by this report.",
        True,
        "do_not_schedule_execution_capable_workflows",
        FINAL_BLOCKED_LABEL,
    )


def high_risk_workflows_boundary_row(created_at: str) -> dict[str, Any]:
    return readiness_row(
        created_at,
        "high_risk_manual_only_workflows",
        "normal_and_paper_execution_workflows_excluded",
        "blocked",
        "static boundary",
        "Normal bot runs, manual paper-order smoke tests, and slow-SMA paper execution remain excluded from this readiness review.",
        True,
        "keep_high_risk_workflows_manual_only_and_out_of_scope",
        FINAL_BLOCKED_LABEL,
    )


def readiness_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    evidence_source: str,
    details: str,
    blocker: bool,
    recommended_next_step: str,
    paper_execution_discussion_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "evidence_source": evidence_source,
        "details": details,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        "execution_approved": False,
        "scheduling_approved": False,
        "paper_execution_discussion_status": paper_execution_discussion_status,
    }


def choose_final_label(rows: list[dict[str, Any]]) -> str:
    statuses = {str(row.get("check_status", "")) for row in rows}
    severities = {str(row.get("severity", "")) for row in rows}
    has_cost_blocker = "blocked_cost_review_required" in statuses
    has_execution_gate_blocker = any("execution_discussion_blocked" in status for status in statuses)
    if has_cost_blocker and has_execution_gate_blocker:
        return FINAL_BLOCKED_LABEL
    if "blocked" in severities:
        return "paper_execution_discussion_blocked"
    if "warning" in severities:
        return FINAL_REVIEW_LABEL
    return FINAL_DESIGN_ONLY_LABEL


def final_details(final_label: str, rows: list[dict[str, Any]]) -> str:
    blocker_rows = [row for row in rows if is_truthy(row.get("blocker"))]
    key_blockers = ", ".join(str(row.get("check_name", "")) for row in blocker_rows[:6]) or "none"
    return f"Final readiness label={final_label}; blocker_count={len(blocker_rows)}; key_blockers={key_blockers}."


def final_next_step(final_label: str) -> str:
    if final_label == FINAL_BLOCKED_LABEL:
        return "resolve_cost_review_and_saved_execution_gate_blockers_before_any_design_discussion"
    if "blocked" in final_label:
        return "resolve_blockers_before_any_paper_execution_discussion"
    if final_label == FINAL_REVIEW_LABEL:
        return "manual_review_required_before_design_only_discussion"
    return "manual_design_review_only_no_execution_approval"


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    final_row = next((row for row in rows if row.get("check_name") == "final_paper_execution_discussion_status"), {})
    blocker_rows = [row for row in rows if is_truthy(row.get("blocker"))]
    key_blockers = ", ".join(str(row.get("check_name", "")) for row in blocker_rows[:5]) or "none"
    status_counts = Counter(str(row.get("check_status", "")) for row in rows)
    return [
        "Stock/ETF paper execution readiness report complete. Report-only; execution_approved=False; scheduling_approved=False.",
        f"final_readiness_label: {final_row.get('check_status', 'unavailable')}",
        f"blocker_count: {len(blocker_rows)}",
        f"key_blockers: {key_blockers}",
        f"check_status_counts: {format_counts(status_counts)}",
        f"recommended_next_step: {final_row.get('recommended_next_step', 'unavailable')}",
        f"Saved readiness report to {output_path}",
        "Warning: this report does not approve orders, paper execution, scheduling, broker connectivity, or strategy-to-execution wiring.",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("metric_name") == key or row.get("check_name") == key or row.get("strategy_name") == key:
            value = row.get("metric_value") or row.get("summary_label") or row.get("status") or row.get("details")
            return str(value or "")
    return ""


def any_value_contains(rows: list[dict[str, Any]], needle: str) -> bool:
    return any(needle in str(value) for row in rows for value in row.values())


def first_matching_detail(rows: list[dict[str, Any]], needles: list[str]) -> str:
    lower_needles = [needle.lower() for needle in needles]
    for row in rows:
        text = " ".join(str(value) for value in row.values())
        if any(needle in text.lower() for needle in lower_needles):
            return text[:500]
    return ""


def rows_with_truthy(rows: list[dict[str, Any]], column: str) -> list[dict[str, Any]]:
    return [row for row in rows if is_truthy(row.get(column))]


def any_truthy(rows: list[dict[str, Any]], column: str) -> bool:
    return bool(rows_with_truthy(rows, column))


def any_status_contains(rows: list[dict[str, Any]], needles: list[str]) -> bool:
    lower_needles = [needle.lower() for needle in needles]
    for row in rows:
        for key, value in row.items():
            if not any(marker in key.lower() for marker in ["status", "severity", "reason", "block"]):
                continue
            text = str(value).lower()
            if any(needle in text for needle in lower_needles):
                return True
    return False


def status_counts(rows: list[dict[str, Any]], columns: list[str]) -> str:
    counts: Counter[str] = Counter()
    for row in rows:
        for column in columns:
            value = str(row.get(column, "")).strip()
            if value:
                counts[value] += 1
                break
    return format_counts(counts)


def format_counts(counts: Counter[str]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def is_truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
