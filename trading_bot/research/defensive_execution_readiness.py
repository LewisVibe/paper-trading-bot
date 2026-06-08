"""Saved-data-only defensive execution readiness report."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFENSIVE_EXECUTION_READINESS_COLUMNS = [
    "created_at",
    "readiness_area",
    "readiness_status",
    "severity",
    "source",
    "finding",
    "blocker",
    "can_progress_to_execution_design",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class DefensiveExecutionReadinessReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_defensive_execution_readiness_report(
    data_dir: Path | str = "data",
    script_dir: Path | str = "scripts",
    created_at: str | None = None,
) -> DefensiveExecutionReadinessReportResult:
    data_path = Path(data_dir)
    script_path = Path(script_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    inputs = {
        "allocation_preview": read_csv_rows(data_path / "defensive_allocation_preview.csv"),
        "allocation_risk": read_csv_rows(data_path / "defensive_allocation_risk_preview.csv"),
        "allocation_decision": read_csv_rows(data_path / "defensive_allocation_decision_report.csv"),
        "kill_switch_gate": read_csv_rows(data_path / "paper_kill_switch_gate_report.csv"),
        "execution_eligibility": read_csv_rows(data_path / "execution_eligibility_report.csv"),
        "portfolio_policy": read_csv_rows(data_path / "portfolio_risk_policy_report.csv"),
    }
    rows = build_readiness_rows(created, data_path, script_path, inputs)
    output_path = data_path / "defensive_execution_readiness_report.csv"
    write_rows(output_path, rows)
    return DefensiveExecutionReadinessReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, output_path),
    )


def build_readiness_rows(
    created_at: str,
    data_path: Path,
    script_path: Path,
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows = [
        defensive_lead_reference_row(created_at, data_path, inputs["allocation_preview"]),
        allocation_preview_safety_row(created_at, data_path, inputs["allocation_decision"]),
        allocation_risk_blockers_row(created_at, data_path, inputs["allocation_risk"]),
        defensive_allocation_decision_row(created_at, data_path, inputs["allocation_decision"]),
        paper_kill_switch_gate_row(created_at, data_path, inputs["kill_switch_gate"]),
        kill_switch_contract_verifier_row(created_at, script_path),
        execution_eligibility_row(created_at, data_path, inputs["execution_eligibility"]),
        portfolio_risk_policy_row(created_at, data_path, inputs["portfolio_policy"]),
    ]
    rows.append(overall_readiness_row(created_at, data_path, rows))
    rows.append(next_gate_row(created_at, data_path, rows))
    return rows


def defensive_lead_reference_row(
    created_at: str,
    data_path: Path,
    preview_rows: list[dict[str, str]],
) -> dict[str, Any]:
    source = data_path / "defensive_allocation_preview.csv"
    if not preview_rows:
        return readiness_row(
            created_at,
            "defensive_lead_reference",
            "missing_input",
            "high",
            source,
            "Saved defensive allocation preview is missing.",
            True,
            False,
            "Run python bot.py --defensive-allocation-preview.",
        )
    lead = first_by_key(preview_rows, "component", "monthly_etf_momentum_rotation") or {}
    if lead.get("preview_label") == "lead_reference" and all_execution_false(preview_rows):
        return readiness_row(
            created_at,
            "defensive_lead_reference",
            "pass",
            "info",
            source,
            "Lead defensive research reference is monthly_etf_momentum_rotation.",
            False,
            False,
            "Keep the lead reference research-only; this does not promote a strategy.",
        )
    return readiness_row(
        created_at,
        "defensive_lead_reference",
        "blocked",
        "high",
        source,
        "Lead reference is missing, unexpected, or a saved row is not execution_approved=False.",
        True,
        False,
        "Review defensive allocation preview before execution-readiness discussion.",
    )


def allocation_preview_safety_row(
    created_at: str,
    data_path: Path,
    decision_rows: list[dict[str, str]],
) -> dict[str, Any]:
    source = data_path / "defensive_allocation_decision_report.csv"
    if not decision_rows:
        return readiness_row(
            created_at,
            "allocation_preview_safety",
            "missing_input",
            "high",
            source,
            "Saved defensive allocation decision report is missing.",
            True,
            False,
            "Run python bot.py --defensive-allocation-decision-report.",
        )
    safety = first_by_key(decision_rows, "decision_area", "preview_safety") or {}
    if safety.get("decision_label") == "preview_safe_non_executable" and all_execution_false(decision_rows):
        return readiness_row(
            created_at,
            "allocation_preview_safety",
            "pass",
            "info",
            source,
            "Allocation preview is marked safe/non-executable in the saved decision report.",
            False,
            False,
            "Keep preview safety non-executable in future reports.",
        )
    return readiness_row(
        created_at,
        "allocation_preview_safety",
        "blocked",
        "critical",
        source,
        "Allocation preview safety is not confirmed as non-executable.",
        True,
        False,
        "Review saved allocation preview/decision outputs before any further design work.",
    )


def allocation_risk_blockers_row(
    created_at: str,
    data_path: Path,
    risk_rows: list[dict[str, str]],
) -> dict[str, Any]:
    source = data_path / "defensive_allocation_risk_preview.csv"
    if not risk_rows:
        return readiness_row(
            created_at,
            "allocation_risk_blockers",
            "missing_input",
            "high",
            source,
            "Saved defensive allocation risk preview is missing.",
            True,
            False,
            "Run python bot.py --defensive-allocation-risk-preview.",
        )
    if not all_execution_false(risk_rows):
        return readiness_row(
            created_at,
            "allocation_risk_blockers",
            "fail",
            "critical",
            source,
            "At least one allocation risk row is not execution_approved=False.",
            True,
            False,
            "Manually review saved risk rows before continuing.",
        )
    blockers = [row.get("risk_check", "unknown") for row in risk_rows if row.get("risk_status") == "blocked" or bool_from_any(row.get("blocker"))]
    if blockers:
        return readiness_row(
            created_at,
            "allocation_risk_blockers",
            "blocked",
            "high",
            source,
            "Allocation risk blockers remain: " + ", ".join(blockers),
            True,
            False,
            "Resolve or explicitly keep blockers documented before any future design step.",
        )
    return readiness_row(
        created_at,
        "allocation_risk_blockers",
        "warning",
        "medium",
        source,
        "No allocation risk blockers were found, but readiness remains non-executable.",
        False,
        False,
        "Continue saved-report review only.",
    )


def defensive_allocation_decision_row(
    created_at: str,
    data_path: Path,
    decision_rows: list[dict[str, str]],
) -> dict[str, Any]:
    source = data_path / "defensive_allocation_decision_report.csv"
    if not decision_rows:
        return readiness_row(
            created_at,
            "defensive_allocation_decision",
            "missing_input",
            "high",
            source,
            "Saved defensive allocation decision report is missing.",
            True,
            False,
            "Run python bot.py --defensive-allocation-decision-report.",
        )
    if not all_execution_false(decision_rows):
        return readiness_row(
            created_at,
            "defensive_allocation_decision",
            "fail",
            "critical",
            source,
            "At least one defensive allocation decision row is not execution_approved=False.",
            True,
            False,
            "Manually review saved decision rows before continuing.",
        )
    overall = first_by_key(decision_rows, "decision_area", "overall_decision") or {}
    if str(overall.get("can_progress_to_execution_design", "")).strip().lower() == "false":
        return readiness_row(
            created_at,
            "defensive_allocation_decision",
            "blocked",
            "high",
            source,
            "Defensive allocation decision blocks execution design.",
            True,
            False,
            "Keep defensive allocation research/reporting only until this decision changes in a future scoped task.",
        )
    return readiness_row(
        created_at,
        "defensive_allocation_decision",
        "warning",
        "high",
        source,
        "Defensive allocation decision does not block progression, but this readiness report still cannot approve execution.",
        True,
        False,
        "Require a future explicit execution-design task before any order-path work.",
    )


def paper_kill_switch_gate_row(
    created_at: str,
    data_path: Path,
    gate_rows: list[dict[str, str]],
) -> dict[str, Any]:
    source = data_path / "paper_kill_switch_gate_report.csv"
    if not gate_rows:
        return readiness_row(
            created_at,
            "paper_kill_switch_gate",
            "missing_input",
            "high",
            source,
            "Saved paper kill-switch gate report is missing.",
            True,
            False,
            "Run python bot.py --paper-kill-switch-gate-report.",
        )
    if not all_execution_false(gate_rows):
        return readiness_row(
            created_at,
            "paper_kill_switch_gate",
            "fail",
            "critical",
            source,
            "At least one paper kill-switch gate row is not execution_approved=False.",
            True,
            False,
            "Manually review saved gate rows before continuing.",
        )
    blockers = [
        row.get("gate_check", "unknown")
        for row in gate_rows
        if row.get("gate_status") in {"blocked", "future_work_required", "fail"} or bool_from_any(row.get("blocks_future_execution_design"))
    ]
    if blockers:
        return readiness_row(
            created_at,
            "paper_kill_switch_gate",
            "future_work_required",
            "critical",
            source,
            "Paper kill-switch gate still blocks execution design: " + ", ".join(blockers),
            True,
            False,
            "Implement/test real paper kill-switch enforcement as isolated no-order safety logic before any execution design.",
        )
    return readiness_row(
        created_at,
        "paper_kill_switch_gate",
        "warning",
        "high",
        source,
        "Paper kill-switch gate has no saved blockers, but this report still does not add enforcement.",
        True,
        False,
        "Review gate status in a future scoped execution-design task.",
    )


def kill_switch_contract_verifier_row(
    created_at: str,
    script_path: Path,
) -> dict[str, Any]:
    source = script_path / "verify_paper_kill_switch_enforcement_contract.py"
    if source.exists():
        return readiness_row(
            created_at,
            "kill_switch_contract_verifier",
            "pass",
            "info",
            source,
            "Paper kill-switch enforcement contract verifier exists as spec/test coverage only.",
            False,
            False,
            "Keep contract verification separate from runtime enforcement until a future scoped task.",
        )
    return readiness_row(
        created_at,
        "kill_switch_contract_verifier",
        "missing_input",
        "high",
        source,
        "Paper kill-switch enforcement contract verifier is missing.",
        True,
        False,
        "Add no-network contract verification before execution design discussion.",
    )


def execution_eligibility_row(
    created_at: str,
    data_path: Path,
    eligibility_rows: list[dict[str, str]],
) -> dict[str, Any]:
    source = data_path / "execution_eligibility_report.csv"
    if not eligibility_rows:
        return readiness_row(
            created_at,
            "execution_eligibility",
            "missing_input",
            "high",
            source,
            "Saved execution eligibility report is missing.",
            True,
            False,
            "Run python bot.py --execution-eligibility-report.",
        )
    if not all_execution_false(eligibility_rows):
        return readiness_row(
            created_at,
            "execution_eligibility",
            "fail",
            "critical",
            source,
            "At least one execution eligibility row is not execution_approved=False.",
            True,
            False,
            "Manually review saved execution eligibility rows before continuing.",
        )
    final = first_by_key(eligibility_rows, "eligibility_check_name", "final_execution_eligibility") or {}
    status = final.get("eligibility_status", "")
    if status in {"blocked_for_review", "blocked", "not_eligible"}:
        return readiness_row(
            created_at,
            "execution_eligibility",
            "blocked",
            "high",
            source,
            f"Execution eligibility remains blocked ({status}).",
            True,
            False,
            "Resolve eligibility blockers in saved reports before any execution design discussion.",
        )
    return readiness_row(
        created_at,
        "execution_eligibility",
        "warning",
        "high",
        source,
        "Execution eligibility is present and non-approving, but final blocked status was not clear.",
        True,
        False,
        "Review execution eligibility manually before future design work.",
    )


def portfolio_risk_policy_row(
    created_at: str,
    data_path: Path,
    policy_rows: list[dict[str, str]],
) -> dict[str, Any]:
    source = data_path / "portfolio_risk_policy_report.csv"
    if not policy_rows:
        return readiness_row(
            created_at,
            "portfolio_risk_policy",
            "missing_input",
            "medium",
            source,
            "Saved portfolio risk policy report is missing.",
            True,
            False,
            "Run python bot.py --portfolio-risk-policy-report.",
        )
    if not all_execution_false(policy_rows):
        return readiness_row(
            created_at,
            "portfolio_risk_policy",
            "fail",
            "critical",
            source,
            "At least one portfolio risk policy row is not execution_approved=False.",
            True,
            False,
            "Manually review saved portfolio risk policy rows before continuing.",
        )
    blockers = [
        row.get("risk_policy_name", "unknown")
        for row in policy_rows
        if row.get("risk_policy_status") == "blocked_for_review"
    ]
    if blockers:
        return readiness_row(
            created_at,
            "portfolio_risk_policy",
            "blocked",
            "high",
            source,
            "Portfolio risk policy blockers remain: " + ", ".join(blockers),
            True,
            False,
            "Resolve risk policy blockers before future execution design discussion.",
        )
    return readiness_row(
        created_at,
        "portfolio_risk_policy",
        "warning",
        "medium",
        source,
        "Portfolio risk policy report exists and remains non-approving.",
        False,
        False,
        "Continue saved policy review only.",
    )


def overall_readiness_row(
    created_at: str,
    data_path: Path,
    prior_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    blockers = [row for row in prior_rows if bool_from_any(row.get("blocker"))]
    if blockers:
        return readiness_row(
            created_at,
            "overall_readiness",
            "blocked",
            "critical",
            data_path,
            "Defensive paper execution design is not ready; blockers/future-work gates remain.",
            True,
            False,
            "Do not begin execution design. Address kill-switch enforcement, eligibility, risk policy, and allocation decision blockers first.",
        )
    return readiness_row(
        created_at,
        "overall_readiness",
        "warning",
        "high",
        data_path,
        "No saved blockers were detected, but this report remains non-executable and cannot approve execution design.",
        False,
        False,
        "Require a separately scoped future execution-design task before any order-path work.",
    )


def next_gate_row(
    created_at: str,
    data_path: Path,
    prior_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    blockers = [row for row in prior_rows if bool_from_any(row.get("blocker"))]
    return readiness_row(
        created_at,
        "next_gate",
        "future_work_required" if blockers else "warning",
        "high",
        data_path,
        "Next gate: implement/test real paper kill-switch enforcement as isolated no-order safety logic, then rerun readiness.",
        True,
        False,
        "Add isolated kill-switch enforcement tests before touching any execution-capable command.",
    )


def readiness_row(
    created_at: str,
    readiness_area: str,
    readiness_status: str,
    severity: str,
    source: Path,
    finding: str,
    blocker: bool,
    can_progress_to_execution_design: bool,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "readiness_area": readiness_area,
        "readiness_status": readiness_status,
        "severity": severity,
        "source": str(source),
        "finding": finding,
        "blocker": blocker,
        "can_progress_to_execution_design": can_progress_to_execution_design,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEFENSIVE_EXECUTION_READINESS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEFENSIVE_EXECUTION_READINESS_COLUMNS})


def build_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    overall = first_by_key(rows, "readiness_area", "overall_readiness") or {}
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("readiness_status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    status_counts = ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))
    return [
        "DEFENSIVE EXECUTION READINESS REPORT. SAVED-DATA ONLY. NOT EXECUTION.",
        "Readiness status counts: " + status_counts,
        f"Overall readiness status: {overall.get('readiness_status', 'unknown')}",
        f"Can progress to execution design: {overall.get('can_progress_to_execution_design', False)}",
        f"Saved defensive execution readiness report to {output_path}",
        "No execution design was added.",
        "No enforcement was added to order paths.",
        "No strategy was promoted.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
    ]


def first_by_key(rows: list[dict[str, Any]], key: str, expected: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get(key) == expected:
            return row
    return None


def all_execution_false(rows: list[dict[str, str]]) -> bool:
    return all(str(row.get("execution_approved", "")).strip().lower() == "false" for row in rows)


def bool_from_any(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
