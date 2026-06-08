"""Saved-data-only execution eligibility view.

This report summarizes readiness blockers without creating order instructions,
enforcing policy, refreshing data, or approving execution.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXECUTION_ELIGIBILITY_COLUMNS = [
    "created_at",
    "eligibility_check_name",
    "eligibility_status",
    "risk_level",
    "finding",
    "blocking_reason",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]

REQUIRED_INPUT_COMMANDS = [
    "python bot.py --refresh-promoted-review",
    "python bot.py --portfolio-risk-policy-report",
    "python bot.py --paper-kill-switch-readiness-report",
    "python bot.py --deployment-readiness-report",
]


@dataclass
class ExecutionEligibilityReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_execution_eligibility_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/execution_eligibility_report.csv",
) -> ExecutionEligibilityReportResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = read_eligibility_inputs(root)
    rows = build_execution_eligibility_rows(root, inputs, created_at)
    output_path = root / output_filename
    write_execution_eligibility_report(output_path, rows)
    return ExecutionEligibilityReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_execution_eligibility_summary(rows, output_path),
    )


def read_eligibility_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "promoted_decision": read_csv_rows(root / "data" / "promoted_decision_preview.csv"),
        "portfolio_risk_policy": read_csv_rows(root / "data" / "portfolio_risk_policy_report.csv"),
        "paper_kill_switch": read_csv_rows(root / "data" / "paper_kill_switch_readiness_report.csv"),
        "deployment_readiness": read_csv_rows(root / "data" / "deployment_readiness_report.csv"),
        "promoted_risk": read_csv_rows(root / "data" / "promoted_risk_preview.csv"),
        "promoted_actions": read_csv_rows(root / "data" / "promoted_strategy_action_preview.csv"),
    }


def build_execution_eligibility_rows(
    root: Path,
    inputs: dict[str, list[dict[str, str]]],
    created_at: str,
) -> list[dict[str, Any]]:
    promoted_decision = inputs["promoted_decision"]
    portfolio_policy = inputs["portfolio_risk_policy"]
    kill_switch = inputs["paper_kill_switch"]
    deployment = inputs["deployment_readiness"]

    rows = [
        promoted_decision_approval_row(created_at, promoted_decision),
        promoted_strategy_disagreement_row(created_at, promoted_decision),
        no_action_flat_tickers_row(created_at, promoted_decision),
        portfolio_risk_policy_blockers_row(created_at, portfolio_policy),
        kill_switch_readiness_row(created_at, kill_switch),
        deployment_readiness_row(created_at, deployment),
        high_risk_commands_gated_row(created_at, root, kill_switch),
    ]
    rows.append(final_execution_eligibility_row(created_at, rows))
    return rows


def promoted_decision_approval_row(created_at: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return eligibility_row(
            created_at,
            "promoted_decision_approval",
            "missing_input",
            "high",
            "Saved promoted decision preview is missing.",
            "Promoted decision approval could not be audited.",
            "Run python bot.py --refresh-promoted-review.",
        )
    approved = [
        row.get("ticker") or f"row_{index}"
        for index, row in enumerate(rows, start=1)
        if is_truthy(row.get("execution_approved"))
    ]
    if approved:
        return eligibility_row(
            created_at,
            "promoted_decision_approval",
            "blocked_for_review",
            "high",
            "Saved promoted decision rows include execution_approved=True: " + ", ".join(approved),
            "Manual review required because saved decision rows must not approve execution.",
            "Regenerate and review promoted decision outputs before any execution discussion.",
        )
    return eligibility_row(
        created_at,
        "promoted_decision_approval",
        "pass",
        "high",
        "Saved promoted decision rows have execution_approved=False.",
        "",
        "Keep execution approval false unless a future explicit workflow changes policy.",
    )


def promoted_strategy_disagreement_row(created_at: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return eligibility_row(
            created_at,
            "promoted_strategy_disagreement",
            "missing_input",
            "high",
            "Saved promoted decision preview is missing.",
            "Strategy disagreement could not be audited.",
            "Run python bot.py --refresh-promoted-review.",
        )
    tickers = sorted(
        {
            row.get("ticker", "")
            for row in rows
            if row.get("decision_state") == "blocked_strategy_disagreement" and row.get("ticker")
        }
    )
    if tickers:
        return eligibility_row(
            created_at,
            "promoted_strategy_disagreement",
            "blocked_for_review",
            "high",
            "Saved promoted decision preview has strategy disagreement for: " + ", ".join(tickers),
            "Strategy disagreement blocks execution discussion.",
            "Resolve promoted strategy disagreement before any execution workflow is considered.",
        )
    return eligibility_row(
        created_at,
        "promoted_strategy_disagreement",
        "pass",
        "high",
        "No blocked_strategy_disagreement rows were found in saved promoted decision preview.",
        "",
        "Continue requiring consensus/decision review before execution discussion.",
    )


def no_action_flat_tickers_row(created_at: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return eligibility_row(
            created_at,
            "no_action_flat_tickers",
            "missing_input",
            "medium",
            "Saved promoted decision preview is missing.",
            "No-action flat tickers could not be audited.",
            "Run python bot.py --refresh-promoted-review.",
        )
    flat_tickers = sorted(
        {
            row.get("ticker", "")
            for row in rows
            if row.get("decision_state") == "no_action_unanimous_flat" and row.get("ticker")
        }
    )
    if flat_tickers:
        return eligibility_row(
            created_at,
            "no_action_flat_tickers",
            "pass",
            "medium",
            "Saved promoted decision preview has no-action/unanimous-flat ticker(s): " + ", ".join(flat_tickers),
            "",
            "Treat unanimous-flat/no-action rows as no execution required, not as an error.",
        )
    return eligibility_row(
        created_at,
        "no_action_flat_tickers",
        "warning",
        "medium",
        "No no_action_unanimous_flat rows were found in saved promoted decision preview.",
        "",
        "Review promoted decision rows manually if expected flat/no-action tickers are absent.",
    )


def portfolio_risk_policy_blockers_row(created_at: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return eligibility_row(
            created_at,
            "portfolio_risk_policy_blockers",
            "missing_input",
            "high",
            "Saved portfolio risk policy report is missing.",
            "Portfolio risk policy blockers could not be audited.",
            "Run python bot.py --portfolio-risk-policy-report.",
        )
    approved = execution_approved_labels(rows, "risk_policy_name")
    if approved:
        return eligibility_row(
            created_at,
            "portfolio_risk_policy_blockers",
            "blocked_for_review",
            "high",
            "Saved portfolio risk policy rows include execution_approved=True: " + ", ".join(approved),
            "Manual review required because policy rows must not approve execution.",
            "Regenerate and review portfolio risk policy before execution discussion.",
        )
    blockers = [
        row.get("risk_policy_name", "")
        for row in rows
        if row.get("risk_policy_status") == "blocked_for_review"
    ]
    if blockers:
        return eligibility_row(
            created_at,
            "portfolio_risk_policy_blockers",
            "blocked_for_review",
            "high",
            "Saved portfolio risk policy blocked rows: " + ", ".join(sorted(blockers)),
            "Portfolio risk policy has blocked-for-review rows.",
            "Resolve portfolio policy blockers before execution discussion.",
        )
    return eligibility_row(
        created_at,
        "portfolio_risk_policy_blockers",
        "pass",
        "high",
        "No blocked_for_review rows were found in saved portfolio risk policy report.",
        "",
        "Keep portfolio risk policy as report-only until a separate enforcement design exists.",
    )


def kill_switch_readiness_row(created_at: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return eligibility_row(
            created_at,
            "kill_switch_readiness",
            "missing_input",
            "high",
            "Saved paper kill-switch readiness report is missing.",
            "Paper kill-switch readiness could not be audited.",
            "Run python bot.py --paper-kill-switch-readiness-report.",
        )
    approved = execution_approved_labels(rows, "check_name")
    if approved:
        return eligibility_row(
            created_at,
            "kill_switch_readiness",
            "blocked_for_review",
            "high",
            "Saved kill-switch readiness rows include execution_approved=True: " + ", ".join(approved),
            "Manual review required because readiness rows must not approve execution.",
            "Regenerate and review kill-switch readiness before execution discussion.",
        )
    not_implemented = [
        row.get("check_name", "")
        for row in rows
        if row.get("check_status") == "not_implemented_future_work"
        and row.get("check_name") in {
            "no_existing_kill_switch_enforcement",
            "future_execution_integration_needed",
            "required_future_tests",
            "portfolio_risk_policy_state",
        }
    ]
    if not_implemented:
        return eligibility_row(
            created_at,
            "kill_switch_readiness",
            "not_ready",
            "high",
            "Saved paper kill-switch readiness report shows future work remains: " + ", ".join(sorted(not_implemented)),
            "No runtime paper kill-switch enforcement exists yet.",
            "Design and test a paper-only kill switch before broader execution discussion.",
        )
    blockers = [
        row.get("check_name", "")
        for row in rows
        if row.get("check_status") == "blocked_for_review"
    ]
    if blockers:
        return eligibility_row(
            created_at,
            "kill_switch_readiness",
            "blocked_for_review",
            "high",
            "Saved paper kill-switch readiness blocked rows: " + ", ".join(sorted(blockers)),
            "Kill-switch readiness has blocked-for-review rows.",
            "Resolve kill-switch readiness blockers before execution discussion.",
        )
    return eligibility_row(
        created_at,
        "kill_switch_readiness",
        "pass",
        "high",
        "Saved paper kill-switch readiness report has no blockers or future enforcement gaps.",
        "",
        "Keep kill-switch status visible before execution discussion.",
    )


def deployment_readiness_row(created_at: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return eligibility_row(
            created_at,
            "deployment_readiness",
            "missing_input",
            "medium",
            "Saved deployment readiness report is missing.",
            "Deployment readiness could not be audited.",
            "Run python bot.py --deployment-readiness-report.",
        )
    approved = execution_approved_labels(rows, "check_name")
    if approved:
        return eligibility_row(
            created_at,
            "deployment_readiness",
            "blocked_for_review",
            "high",
            "Saved deployment readiness rows include execution_approved=True: " + ", ".join(approved),
            "Manual review required because readiness rows must not approve execution.",
            "Regenerate and review deployment readiness before execution discussion.",
        )
    blockers = [
        row.get("check_name", "")
        for row in rows
        if row.get("check_status") == "blocked_for_review"
    ]
    warnings = [
        row.get("check_name", "")
        for row in rows
        if row.get("check_status") == "warning"
    ]
    if blockers:
        return eligibility_row(
            created_at,
            "deployment_readiness",
            "blocked_for_review",
            "medium",
            "Saved deployment readiness blocked rows: " + ", ".join(sorted(blockers)),
            "Deployment readiness has blocked-for-review rows.",
            "Resolve deployment readiness blockers before VPS/scheduler discussion.",
        )
    if warnings:
        return eligibility_row(
            created_at,
            "deployment_readiness",
            "warning",
            "medium",
            "Saved deployment readiness warning rows: " + ", ".join(sorted(warnings)),
            "",
            "Review deployment warnings manually; deployment readiness is not scheduling approval.",
        )
    return eligibility_row(
        created_at,
        "deployment_readiness",
        "pass",
        "medium",
        "Saved deployment readiness report has no blocked or warning rows.",
        "",
        "Remember deployment readiness is an audit only, not scheduling approval.",
    )


def high_risk_commands_gated_row(
    created_at: str,
    root: Path,
    kill_switch_rows: list[dict[str, str]],
) -> dict[str, Any]:
    gated_from_saved = any(
        row.get("check_name") == "high_risk_commands_still_gated" and row.get("check_status") == "pass"
        for row in kill_switch_rows
    )
    help_text = bot_help_text(root)
    gated_from_help = all(
        command in help_text
        for command in [
            "--paper-order-test",
            "--confirm-paper-order",
            "--execute-slow-sma-paper",
            "--confirm-slow-sma-paper",
        ]
    )
    if gated_from_saved or gated_from_help:
        return eligibility_row(
            created_at,
            "high_risk_commands_gated",
            "pass",
            "high",
            "High-risk paper commands remain paired with explicit confirmation flags.",
            "",
            "Keep paper execution commands manually gated and out of automatic scheduling.",
        )
    return eligibility_row(
        created_at,
        "high_risk_commands_gated",
        "blocked_for_review",
        "high",
        "Could not confirm high-risk paper commands are explicitly gated.",
        "Command gating could not be confirmed.",
        "Review command inventory before any execution discussion.",
    )


def final_execution_eligibility_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = [
        row for row in rows
        if row.get("eligibility_status") in {"blocked_for_review", "not_ready", "missing_input"}
    ]
    warnings = [row for row in rows if row.get("eligibility_status") == "warning"]
    if blockers:
        reason = "; ".join(
            str(row.get("blocking_reason") or row.get("finding"))
            for row in blockers
            if row.get("blocking_reason") or row.get("finding")
        )
        return eligibility_row(
            created_at,
            "final_execution_eligibility",
            "blocked_for_review",
            "high",
            "Execution eligible: False.",
            reason,
            "Resolve blockers, complete future kill-switch work, and rerun saved eligibility reports before any execution discussion.",
        )
    if warnings:
        return eligibility_row(
            created_at,
            "final_execution_eligibility",
            "warning",
            "high",
            "Execution eligible: False.",
            "Warnings remain; execution is not approved.",
            "Review warnings and remember this report is not an execution gate.",
        )
    return eligibility_row(
        created_at,
        "final_execution_eligibility",
        "eligible_for_discussion",
        "high",
        "Execution eligible: False; no blockers were found, but this report cannot approve execution.",
        "No execution approval exists.",
        "A separate explicit paper-execution review would still be required.",
    )


def eligibility_row(
    created_at: str,
    eligibility_check_name: str,
    eligibility_status: str,
    risk_level: str,
    finding: str,
    blocking_reason: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "eligibility_check_name": eligibility_check_name,
        "eligibility_status": eligibility_status,
        "risk_level": risk_level,
        "finding": finding,
        "blocking_reason": blocking_reason,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_execution_eligibility_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts = Counter(str(row.get("eligibility_status", "unknown")) for row in rows)
    final = next(
        (row for row in rows if row.get("eligibility_check_name") == "final_execution_eligibility"),
        {},
    )
    blockers = [
        row for row in rows
        if row.get("eligibility_status") in {"blocked_for_review", "not_ready", "missing_input"}
        and row.get("eligibility_check_name") != "final_execution_eligibility"
    ]
    lines = [
        "EXECUTION ELIGIBILITY REPORT. RESEARCH ONLY. NOT EXECUTION.",
        "Count by eligibility_status:",
    ]
    for status, count in sorted(counts.items()):
        lines.append(f"  {status}: {count}")
    lines.extend(
        [
            "Final eligibility:",
            "  Execution eligible: False",
            "Blocking reasons:",
        ]
    )
    if blockers:
        for row in blockers:
            reason = row.get("blocking_reason") or row.get("finding") or ""
            lines.append(f"  {row['eligibility_check_name']}: {reason}")
    else:
        lines.append("  none")
    if final.get("blocking_reason"):
        lines.append(f"Final reason: {final['blocking_reason']}")
    lines.extend(
        [
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "This report is not an execution gate and does not make order instructions.",
            "If inputs are missing, run:",
            *[f"  {command}" for command in REQUIRED_INPUT_COMMANDS],
            f"Saved execution eligibility report to {output_path}",
        ]
    )
    return lines


def write_execution_eligibility_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=EXECUTION_ELIGIBILITY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def execution_approved_labels(rows: list[dict[str, str]], label_column: str) -> list[str]:
    labels: list[str] = []
    for index, row in enumerate(rows, start=1):
        if is_truthy(row.get("execution_approved")):
            labels.append(row.get(label_column) or row.get("ticker") or f"row_{index}")
    return labels


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


def is_truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
