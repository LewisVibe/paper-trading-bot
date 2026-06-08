"""Design/report-only paper kill-switch gate scaffold."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PAPER_KILL_SWITCH_GATE_COLUMNS = [
    "created_at",
    "gate_check",
    "gate_status",
    "severity",
    "source",
    "finding",
    "blocks_future_execution_design",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class PaperKillSwitchGateReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_kill_switch_gate_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/paper_kill_switch_gate_report.csv",
    created_at: str | None = None,
) -> PaperKillSwitchGateReportResult:
    root = Path(root_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    rows = build_gate_rows(root, created)
    output_path = root / output_filename
    write_rows(output_path, rows)
    return PaperKillSwitchGateReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, output_path),
    )


def build_gate_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    example_config_path = root / "config.example.json"
    example_config = read_json(example_config_path)
    help_text = bot_help_text(root)
    readiness_path = root / "data" / "paper_kill_switch_readiness_report.csv"
    decision_path = root / "data" / "defensive_allocation_decision_report.csv"
    eligibility_path = root / "data" / "execution_eligibility_report.csv"
    helper_path = root / "trading_bot" / "safety" / "paper_kill_switch.py"
    readiness_rows = read_csv_rows(readiness_path)
    decision_rows = read_csv_rows(decision_path)
    eligibility_rows = read_csv_rows(eligibility_path)

    return [
        config_bool_row(
            created_at,
            "config_example_dry_run_default_true",
            example_config_path,
            example_config.get("dry_run") is True,
            "config.example.json keeps dry_run=true.",
            "config.example.json does not clearly keep dry_run=true.",
            "Keep dry_run true by default.",
        ),
        config_bool_row(
            created_at,
            "config_example_alpaca_paper_default_true",
            example_config_path,
            nested_value(example_config, ["alpaca", "paper"]) is True,
            "config.example.json keeps alpaca.paper=true.",
            "config.example.json does not clearly keep alpaca.paper=true.",
            "Keep Alpaca paper mode true by default.",
        ),
        config_bool_row(
            created_at,
            "config_example_allow_shorting_default_false",
            example_config_path,
            example_config.get("allow_shorting") is False,
            "config.example.json keeps allow_shorting=false.",
            "config.example.json does not clearly keep allow_shorting=false.",
            "Keep shorting disabled by default.",
        ),
        high_risk_commands_confirmation_gated_row(created_at, help_text),
        existing_readiness_available_row(created_at, readiness_path, readiness_rows),
        isolated_kill_switch_helper_available_row(created_at, helper_path),
        gate_row(
            created_at,
            "kill_switch_enforcement_not_implemented",
            "future_work_required",
            "high",
            "source inspection",
            "Runtime paper kill-switch enforcement is intentionally not implemented by this design/report scaffold.",
            True,
            "Design a real kill-switch setting and no-network tests before touching any order path.",
        ),
        kill_switch_enforcement_not_wired_row(created_at, root, helper_path),
        defensive_allocation_decision_row(created_at, decision_path, decision_rows),
        execution_eligibility_row(created_at, eligibility_path, eligibility_rows),
        gate_row(
            created_at,
            "future_execution_requires_kill_switch_gate",
            "blocked",
            "critical",
            "paper kill-switch gate design",
            "Any future execution design remains blocked until real kill-switch enforcement and tests exist.",
            True,
            "Keep this as future work; do not connect strategies to orders from this scaffold.",
        ),
    ]


def config_bool_row(
    created_at: str,
    gate_check: str,
    source: Path,
    passed: bool,
    pass_finding: str,
    fail_finding: str,
    required_next_step: str,
) -> dict[str, Any]:
    return gate_row(
        created_at,
        gate_check,
        "pass" if passed else "fail",
        "high",
        str(source),
        pass_finding if passed else fail_finding,
        not passed,
        required_next_step if passed else "Fix config.example.json defaults before any execution design discussion.",
    )


def high_risk_commands_confirmation_gated_row(created_at: str, help_text: str) -> dict[str, Any]:
    paper_gated = "--paper-order-test" in help_text and "--confirm-paper-order" in help_text
    slow_sma_gated = "--execute-slow-sma-paper" in help_text and "--confirm-slow-sma-paper" in help_text
    passed = paper_gated and slow_sma_gated
    return gate_row(
        created_at,
        "high_risk_commands_confirmation_gated",
        "pass" if passed else "fail",
        "critical",
        "python bot.py --help",
        "High-risk paper commands remain paired with explicit confirmation flags."
        if passed
        else "Could not confirm high-risk paper commands are explicitly confirmation-gated.",
        not passed,
        "Keep high-risk paper commands behind explicit confirmation.",
    )


def isolated_kill_switch_helper_available_row(created_at: str, helper_path: Path) -> dict[str, Any]:
    helper_source = read_text(helper_path)
    available = helper_path.exists() and "evaluate_paper_kill_switch_gate" in helper_source
    return gate_row(
        created_at,
        "isolated_kill_switch_helper_available",
        "pass" if available else "missing_input",
        "info" if available else "high",
        str(helper_path),
        "Isolated paper kill-switch helper exists but is not wired into order paths."
        if available
        else "Isolated paper kill-switch helper is missing.",
        False if available else True,
        "Keep helper isolated until a future scoped enforcement task."
        if available
        else "Add isolated no-order helper logic before enforcement design continues.",
    )


def kill_switch_enforcement_not_wired_row(created_at: str, root: Path, helper_path: Path) -> dict[str, Any]:
    high_risk_paths = [
        root / "bot.py",
        root / "trading_bot" / "execution.py",
        root / "trading_bot" / "alpaca_client.py",
        root / "trading_bot" / "database.py",
        root / "trading_bot" / "discord_alerts.py",
    ]
    helper_import = "trading_bot.safety.paper_kill_switch"
    helper_call = "evaluate_paper_kill_switch_gate"
    wired_paths = [
        str(path)
        for path in high_risk_paths
        if helper_import in read_text(path) or helper_call in read_text(path)
    ]
    if wired_paths:
        return gate_row(
            created_at,
            "kill_switch_enforcement_not_wired_to_order_paths",
            "fail",
            "critical",
            str(helper_path),
            "Isolated paper kill-switch helper appears wired into high-risk paths: " + ", ".join(wired_paths),
            True,
            "Remove unexpected wiring and review before continuing.",
        )
    return gate_row(
        created_at,
        "kill_switch_enforcement_not_wired_to_order_paths",
        "blocked",
        "high",
        str(helper_path),
        "Isolated paper kill-switch helper is not wired into order paths; execution design remains blocked.",
        True,
        "Future scoped work must add reviewed enforcement tests before any order-path integration.",
    )


def existing_readiness_available_row(
    created_at: str,
    source: Path,
    readiness_rows: list[dict[str, str]],
) -> dict[str, Any]:
    if not readiness_rows:
        return gate_row(
            created_at,
            "existing_kill_switch_readiness_available",
            "missing_input",
            "medium",
            str(source),
            "Saved paper kill-switch readiness report is missing.",
            False,
            "Run python bot.py --paper-kill-switch-readiness-report for readiness context.",
        )
    approved = rows_with_true_execution(readiness_rows, "check_name")
    if approved:
        return gate_row(
            created_at,
            "existing_kill_switch_readiness_available",
            "fail",
            "critical",
            str(source),
            "Readiness report unexpectedly has execution_approved=True rows: " + ", ".join(approved),
            True,
            "Review saved readiness report before any gate discussion.",
        )
    return gate_row(
        created_at,
        "existing_kill_switch_readiness_available",
        "pass",
        "info",
        str(source),
        "Saved paper kill-switch readiness report is available and non-approving.",
        False,
        "Use readiness context, but do not treat it as runtime enforcement.",
    )


def defensive_allocation_decision_row(
    created_at: str,
    source: Path,
    decision_rows: list[dict[str, str]],
) -> dict[str, Any]:
    if not decision_rows:
        return gate_row(
            created_at,
            "defensive_allocation_decision_blocks_execution_design",
            "missing_input",
            "high",
            str(source),
            "Saved defensive allocation decision report is missing.",
            True,
            "Run python bot.py --defensive-allocation-decision-report before any execution-design discussion.",
        )
    approved = rows_with_true_execution(decision_rows, "decision_area")
    if approved:
        return gate_row(
            created_at,
            "defensive_allocation_decision_blocks_execution_design",
            "fail",
            "critical",
            str(source),
            "Decision report unexpectedly has execution_approved=True rows: " + ", ".join(approved),
            True,
            "Review saved decision report before any further work.",
        )
    overall = first_by_key(decision_rows, "decision_area", "overall_decision") or {}
    if str(overall.get("can_progress_to_execution_design", "")).strip().lower() == "true":
        return gate_row(
            created_at,
            "defensive_allocation_decision_blocks_execution_design",
            "warning",
            "high",
            str(source),
            "Defensive allocation decision report says execution-design progress may be possible, but kill-switch enforcement is still missing.",
            True,
            "Do not proceed until kill-switch enforcement design/tests exist.",
        )
    return gate_row(
        created_at,
        "defensive_allocation_decision_blocks_execution_design",
        "blocked",
        "high",
        str(source),
        "Defensive allocation decision report blocks execution design.",
        True,
        "Keep defensive allocation research/reporting only until blockers and kill-switch work are resolved.",
    )


def execution_eligibility_row(
    created_at: str,
    source: Path,
    eligibility_rows: list[dict[str, str]],
) -> dict[str, Any]:
    if not eligibility_rows:
        return gate_row(
            created_at,
            "execution_eligibility_blocks_execution",
            "missing_input",
            "high",
            str(source),
            "Saved execution eligibility report is missing.",
            True,
            "Run python bot.py --execution-eligibility-report before execution-design discussion.",
        )
    approved = rows_with_true_execution(eligibility_rows, "eligibility_check_name")
    if approved:
        return gate_row(
            created_at,
            "execution_eligibility_blocks_execution",
            "fail",
            "critical",
            str(source),
            "Execution eligibility report unexpectedly has execution_approved=True rows: " + ", ".join(approved),
            True,
            "Review saved execution eligibility report immediately.",
        )
    final = first_by_key(eligibility_rows, "eligibility_check_name", "final_execution_eligibility") or {}
    status = final.get("eligibility_status", "")
    if status in {"blocked_for_review", "blocked", "not_eligible"}:
        return gate_row(
            created_at,
            "execution_eligibility_blocks_execution",
            "blocked",
            "high",
            str(source),
            f"Execution eligibility remains blocked ({status}).",
            True,
            "Resolve execution eligibility blockers before any execution-design discussion.",
        )
    return gate_row(
        created_at,
        "execution_eligibility_blocks_execution",
        "warning",
        "high",
        str(source),
        "Execution eligibility report exists and is non-approving, but final blocked status was not clear.",
        True,
        "Review execution eligibility manually before any future design step.",
    )


def gate_row(
    created_at: str,
    gate_check: str,
    gate_status: str,
    severity: str,
    source: str,
    finding: str,
    blocks_future_execution_design: bool,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "gate_check": gate_check,
        "gate_status": gate_status,
        "severity": severity,
        "source": source,
        "finding": finding,
        "blocks_future_execution_design": blocks_future_execution_design,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PAPER_KILL_SWITCH_GATE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PAPER_KILL_SWITCH_GATE_COLUMNS})


def build_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts: dict[str, int] = {}
    blockers = 0
    for row in rows:
        status = str(row.get("gate_status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
        if bool_from_any(row.get("blocks_future_execution_design")):
            blockers += 1
    status_counts = ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))
    conclusion = "blocked_future_work_required" if blockers else "review_required_not_execution"
    return [
        "PAPER KILL-SWITCH GATE REPORT. DESIGN/REPORT ONLY. NOT EXECUTION.",
        f"Gate status counts: {status_counts}",
        f"Current gate conclusion: {conclusion}",
        f"Future execution-design blockers: {blockers}",
        "No enforcement was added to order paths.",
        "No strategy was promoted.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
        f"Saved paper kill-switch gate report to {output_path}",
    ]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def bot_help_text(root: Path) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "bot.py", "--help"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return ""
    return (result.stdout or "") + "\n" + (result.stderr or "")


def nested_value(data: dict[str, Any], keys: list[str]) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def rows_with_true_execution(rows: list[dict[str, str]], label_key: str) -> list[str]:
    return [
        row.get(label_key, "unknown")
        for row in rows
        if str(row.get("execution_approved", "")).strip().lower() == "true"
    ]


def first_by_key(rows: list[dict[str, str]], key: str, expected: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == expected:
            return row
    return None


def bool_from_any(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
