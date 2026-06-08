"""Reporting-only readiness audit for a future paper kill switch."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PAPER_KILL_SWITCH_READINESS_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "risk_level",
    "finding",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class PaperKillSwitchReadinessResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_kill_switch_readiness_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/paper_kill_switch_readiness_report.csv",
) -> PaperKillSwitchReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = build_paper_kill_switch_readiness_rows(root, created_at)
    output_path = root / output_filename
    write_paper_kill_switch_readiness_report(output_path, rows)
    return PaperKillSwitchReadinessResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_paper_kill_switch_readiness_summary(rows, output_path),
    )


def build_paper_kill_switch_readiness_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    config_source = read_text(root / "trading_bot" / "config.py")
    bot_source = read_text(root / "bot.py")
    readme_source = read_text(root / "README.md")
    vps_checklist_source = read_text(root / "docs" / "VPS_SETUP_CHECKLIST.md")
    help_text = bot_help_text(root)
    example_config = read_json(root / "config.example.json")
    promoted_decision_rows = read_csv_rows(root / "data" / "promoted_decision_preview.csv")
    portfolio_policy_rows = read_csv_rows(root / "data" / "portfolio_risk_policy_report.csv")

    decision_disagreements = sorted(
        {
            row.get("ticker", "")
            for row in promoted_decision_rows
            if row.get("decision_state") == "blocked_strategy_disagreement" and row.get("ticker")
        }
    )
    approved_sources = execution_approved_sources(
        [
            ("promoted_decision_preview", promoted_decision_rows),
            ("portfolio_risk_policy_report", portfolio_policy_rows),
        ]
    )
    portfolio_checks = {row.get("risk_policy_name", ""): row for row in portfolio_policy_rows}
    kill_switch_policy = portfolio_checks.get("kill_switch_policy", {})

    rows = [
        readiness_row(
            created_at,
            "paper_only_boundary",
            "pass" if paper_boundary_confirmed(config_source, example_config) else "blocked_for_review",
            "high",
            "Alpaca paper-only boundary is present in config validation/example config." if paper_boundary_confirmed(config_source, example_config) else "Could not confirm Alpaca paper-only boundary.",
            "Keep alpaca.paper true and live trading out of scope.",
        ),
        readiness_row(
            created_at,
            "dry_run_default_boundary",
            "pass" if dry_run_default_confirmed(config_source, example_config) else "blocked_for_review",
            "high",
            "dry_run defaults true in config loading/example config." if dry_run_default_confirmed(config_source, example_config) else "Could not confirm dry_run default true.",
            "Keep dry_run true unless a separately reviewed paper-execution workflow is explicitly tested.",
        ),
        readiness_row(
            created_at,
            "allow_shorting_boundary",
            "pass" if allow_shorting_default_confirmed(config_source, example_config) else "blocked_for_review",
            "high",
            "allow_shorting defaults false in config loading/example config." if allow_shorting_default_confirmed(config_source, example_config) else "Could not confirm allow_shorting default false.",
            "Keep shorting disabled by default.",
        ),
        high_risk_commands_row(created_at, help_text),
        readiness_row(
            created_at,
            "normal_execution_path_not_modified",
            "pass",
            "high",
            "This readiness report is isolated from normal order submission and does not modify the normal execution path.",
            "Keep future kill-switch enforcement work separate and explicitly reviewed before touching order paths.",
        ),
        readiness_row(
            created_at,
            "no_existing_kill_switch_enforcement",
            "not_implemented_future_work",
            "high",
            "No runtime paper kill-switch enforcement was added by this report.",
            "Design enforcement separately before any runtime order-path integration.",
        ),
        readiness_row(
            created_at,
            "future_config_design_needed",
            "not_implemented_future_work",
            "high",
            "A future reviewed design could define a safe setting such as paper_kill_switch_enabled=true by default; this report does not add it.",
            "Design config semantics separately without editing config.json in this report.",
        ),
        readiness_row(
            created_at,
            "future_execution_integration_needed",
            "not_implemented_future_work",
            "high",
            "Future enforcement would need to run before paper order creation or submission; this report does not implement that.",
            "Add no-network tests before any future order-path integration.",
        ),
        readiness_row(
            created_at,
            "future_preview_surface_needed",
            "not_implemented_future_work",
            "medium",
            "Future preview/report surfaces should show kill-switch status before execution discussion.",
            "Add display-only status first if a kill-switch design is approved later.",
        ),
        promoted_decision_state_row(created_at, promoted_decision_rows, decision_disagreements, approved_sources),
        portfolio_risk_policy_state_row(created_at, portfolio_policy_rows, kill_switch_policy, approved_sources),
        safe_scheduling_boundary_row(created_at, readme_source, vps_checklist_source),
        readiness_row(
            created_at,
            "required_future_tests",
            "not_implemented_future_work",
            "high",
            "Future kill-switch enforcement would need no-network tests proving paper order creation/submission is blocked when enabled.",
            "Write failing tests before implementing any runtime enforcement.",
        ),
    ]
    return rows


def high_risk_commands_row(created_at: str, help_text: str) -> dict[str, Any]:
    paper_gated = "--paper-order-test" in help_text and "--confirm-paper-order" in help_text
    slow_sma_gated = "--execute-slow-sma-paper" in help_text and "--confirm-slow-sma-paper" in help_text
    status = "pass" if paper_gated and slow_sma_gated else "blocked_for_review"
    finding = (
        "High-risk paper commands remain paired with explicit confirmation flags."
        if status == "pass"
        else "Could not confirm high-risk paper commands are explicitly gated in help output."
    )
    return readiness_row(
        created_at,
        "high_risk_commands_still_gated",
        status,
        "high",
        finding,
        "Keep paper order tests and slow SMA paper execution behind explicit confirmation.",
    )


def promoted_decision_state_row(
    created_at: str,
    promoted_decision_rows: list[dict[str, str]],
    decision_disagreements: list[str],
    approved_sources: list[str],
) -> dict[str, Any]:
    if approved_sources:
        return readiness_row(
            created_at,
            "promoted_decision_state",
            "blocked_for_review",
            "high",
            "Saved preview/report rows include execution_approved=True: " + ", ".join(approved_sources),
            "Do not discuss execution until saved previews/reports are non-approving.",
        )
    if not promoted_decision_rows:
        return readiness_row(
            created_at,
            "promoted_decision_state",
            "not_applicable",
            "medium",
            "Saved promoted decision preview is missing; no live refresh was attempted.",
            "Run promoted decision preview before future execution discussion.",
        )
    if decision_disagreements:
        return readiness_row(
            created_at,
            "promoted_decision_state",
            "blocked_for_review",
            "high",
            "Saved promoted decision preview has strategy disagreement for: " + ", ".join(decision_disagreements),
            "Resolve promoted strategy disagreement before execution discussion.",
        )
    return readiness_row(
        created_at,
        "promoted_decision_state",
        "pass",
        "medium",
        "Saved promoted decision preview has no execution approval and no strategy disagreement rows.",
        "Continue requiring decision preview review before execution discussion.",
    )


def portfolio_risk_policy_state_row(
    created_at: str,
    portfolio_policy_rows: list[dict[str, str]],
    kill_switch_policy: dict[str, str],
    approved_sources: list[str],
) -> dict[str, Any]:
    if approved_sources:
        return readiness_row(
            created_at,
            "portfolio_risk_policy_state",
            "blocked_for_review",
            "high",
            "Saved preview/report rows include execution_approved=True: " + ", ".join(approved_sources),
            "Do not discuss execution until saved risk policy rows are non-approving.",
        )
    if not portfolio_policy_rows:
        return readiness_row(
            created_at,
            "portfolio_risk_policy_state",
            "not_applicable",
            "medium",
            "Saved portfolio risk policy report is missing; no report was rerun.",
            "Run portfolio risk policy report before kill-switch design review.",
        )
    if kill_switch_policy.get("risk_policy_status") == "not_implemented_future_work":
        return readiness_row(
            created_at,
            "portfolio_risk_policy_state",
            "not_implemented_future_work",
            "high",
            "Portfolio risk policy report marks kill_switch_policy as not_implemented_future_work.",
            "Keep this as future design work; do not treat it as runtime enforcement.",
        )
    return readiness_row(
        created_at,
        "portfolio_risk_policy_state",
        "warning",
        "high",
        "Saved portfolio risk policy report exists, but kill_switch_policy is not clearly marked as future work.",
        "Review portfolio risk policy wording before kill-switch design work.",
    )


def safe_scheduling_boundary_row(created_at: str, readme_source: str, vps_checklist_source: str) -> dict[str, Any]:
    combined = readme_source + "\n" + vps_checklist_source
    has_never_schedule = "Commands Never To Schedule Automatically" in combined or "Do not schedule" in combined
    mentions_execution_commands = "--paper-order-test" in combined and "--execute-slow-sma-paper" in combined
    status = "pass" if has_never_schedule and mentions_execution_commands else "warning"
    return readiness_row(
        created_at,
        "safe_scheduling_boundary",
        status,
        "high",
        "Deployment/VPS docs warn against scheduling execution-capable commands." if status == "pass" else "Could not confirm deployment/VPS docs clearly block scheduling execution-capable commands.",
        "Keep scheduler documentation limited to manually verified report/display commands.",
    )


def readiness_row(
    created_at: str,
    check_name: str,
    check_status: str,
    risk_level: str,
    finding: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "risk_level": risk_level,
        "finding": finding,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_paper_kill_switch_readiness_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts = Counter(str(row.get("check_status", "unknown")) for row in rows)
    blocked = [row for row in rows if row.get("check_status") == "blocked_for_review"]
    lines = [
        "PAPER KILL-SWITCH READINESS REPORT. REPORTING ONLY. NOT EXECUTION.",
        format_status_counts(counts),
        "Key blocked items:",
    ]
    if blocked:
        for row in blocked:
            lines.append(f"  {row['check_name']}: {row['finding']}")
    else:
        lines.append("  none")
    lines.extend(
        [
            "No kill-switch enforcement was added.",
            "No order path was changed.",
            "No execution approval was granted.",
            f"Saved paper kill-switch readiness report to {output_path}",
        ]
    )
    return lines


def format_status_counts(counts: Counter[str]) -> str:
    ordered = ["pass", "warning", "blocked_for_review", "not_implemented_future_work", "not_applicable"]
    return ", ".join(f"{status}: {counts.get(status, 0)}" for status in ordered)


def write_paper_kill_switch_readiness_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PAPER_KILL_SWITCH_READINESS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def paper_boundary_confirmed(config_source: str, example_config: dict[str, Any]) -> bool:
    return "alpaca.paper must be true" in config_source or nested_value(example_config, ["alpaca", "paper"]) is True


def dry_run_default_confirmed(config_source: str, example_config: dict[str, Any]) -> bool:
    return 'parse_config_bool(raw, "dry_run", True)' in config_source or example_config.get("dry_run") is True


def allow_shorting_default_confirmed(config_source: str, example_config: dict[str, Any]) -> bool:
    return 'parse_config_bool(raw, "allow_shorting", False)' in config_source or example_config.get("allow_shorting") is False


def execution_approved_sources(sources: list[tuple[str, list[dict[str, str]]]]) -> list[str]:
    approved: list[str] = []
    for source_name, rows in sources:
        for index, row in enumerate(rows, start=1):
            if is_truthy(row.get("execution_approved")):
                label = row.get("ticker") or row.get("risk_policy_name") or row.get("check_name") or f"row_{index}"
                approved.append(f"{source_name}:{label}")
    return approved


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


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


def is_truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
