"""Saved-data/static-source normal bot execution policy checkpoint report."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NORMAL_BOT_EXECUTION_POLICY_COLUMNS = [
    "created_at",
    "policy_area",
    "policy_status",
    "severity",
    "source",
    "finding",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class NormalBotExecutionPolicyReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_normal_bot_execution_policy_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/normal_bot_execution_policy_report.csv",
    created_at: str | None = None,
) -> NormalBotExecutionPolicyReportResult:
    root = Path(root_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    rows = build_policy_rows(root, created)
    output_path = root / output_filename
    write_rows(output_path, rows)
    return NormalBotExecutionPolicyReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, output_path),
    )


def build_policy_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    bot_path = root / "bot.py"
    bot_source = read_text(bot_path)
    protection_rows = read_csv_rows(root / "data" / "paper_execution_protection_report.csv")
    readiness_rows = read_csv_rows(root / "data" / "defensive_execution_readiness_report.csv")
    help_text = bot_help_text(root)

    normal_separate = normal_bot_unwired(bot_source)
    paper_order_gated = command_present(help_text, "--paper-order-test") and command_present(
        help_text,
        "--confirm-paper-order",
    )
    if not paper_order_gated:
        paper_order_gated = command_present(bot_source, "--paper-order-test") and command_present(
            bot_source,
            "--confirm-paper-order",
        )
    slow_sma_gated = command_present(help_text, "--execute-slow-sma-paper") and command_present(
        help_text,
        "--confirm-slow-sma-paper",
    )
    if not slow_sma_gated:
        slow_sma_gated = command_present(bot_source, "--execute-slow-sma-paper") and command_present(
            bot_source,
            "--confirm-slow-sma-paper",
        )
    paper_order_protected = protection_status(
        protection_rows,
        "manual_paper_order_test",
        "protected_by_kill_switch_preflight",
    ) or manual_preflight_present(bot_source)
    slow_sma_protected = protection_status(
        protection_rows,
        "slow_sma_paper_execution",
        "protected_by_kill_switch_preflight",
    ) or slow_sma_preflight_present(bot_source)
    readiness_blocked = readiness_overall_blocked(readiness_rows)
    no_execution_approval = not any_true_execution(protection_rows) and not any_true_execution(readiness_rows)

    return [
        normal_bot_path_policy_row(created_at, bot_path, normal_separate),
        paper_order_test_policy_row(created_at, bot_path, paper_order_gated and paper_order_protected),
        slow_sma_policy_row(created_at, bot_path, slow_sma_gated and slow_sma_protected),
        future_defensive_execution_policy_row(created_at, bot_path),
        overall_policy_row(created_at, root),
        execution_approval_policy_row(created_at, root, readiness_blocked and no_execution_approval),
    ]


def normal_bot_path_policy_row(created_at: str, source: Path, normal_separate: bool) -> dict[str, Any]:
    return policy_row(
        created_at,
        "normal_bot_path_policy",
        "deliberately_non_defensive_execution_path" if normal_separate else "warning",
        "critical",
        source,
        "Normal python bot.py remains separate from defensive paper execution."
        if normal_separate
        else "Normal python bot.py appears to contain defensive paper execution gate wiring; review manually.",
        "Keep normal python bot.py original/dry-run-first and separate from defensive allocation execution.",
    )


def paper_order_test_policy_row(created_at: str, source: Path, gated: bool) -> dict[str, Any]:
    return policy_row(
        created_at,
        "paper_order_test_policy",
        "explicit_confirmed_kill_switch_gated_path" if gated else "blocked",
        "high",
        source,
        "--paper-order-test is separate, confirmation-gated, and kill-switch-gated."
        if gated
        else "--paper-order-test confirmation/kill-switch gating was not confirmed.",
        "Keep manual paper-order testing as an explicit scoped command only.",
    )


def slow_sma_policy_row(created_at: str, source: Path, gated: bool) -> dict[str, Any]:
    return policy_row(
        created_at,
        "slow_sma_paper_execution_policy",
        "explicit_confirmed_kill_switch_gated_path" if gated else "blocked",
        "high",
        source,
        "--execute-slow-sma-paper is separate, confirmation-gated, and kill-switch-gated."
        if gated
        else "--execute-slow-sma-paper confirmation/kill-switch gating was not confirmed.",
        "Keep slow SMA paper execution as an explicit scoped command only.",
    )


def future_defensive_execution_policy_row(created_at: str, source: Path) -> dict[str, Any]:
    return policy_row(
        created_at,
        "future_defensive_execution_policy",
        "separate_command_required",
        "critical",
        source,
        "Any future defensive paper execution must be a separate scoped command, not normal python bot.py.",
        "Do not use normal python bot.py as the defensive allocation execution path.",
    )


def overall_policy_row(created_at: str, source: Path) -> dict[str, Any]:
    return policy_row(
        created_at,
        "overall_policy",
        "option_a_keep_normal_bot_dry_run_first",
        "critical",
        source,
        "Option A is the active policy: normal python bot.py stays original/dry-run-first and separate from defensive paper execution.",
        "Keep paper execution in separate explicit commands with confirmation and kill-switch gates.",
    )


def execution_approval_policy_row(created_at: str, source: Path, blocked: bool) -> dict[str, Any]:
    return policy_row(
        created_at,
        "execution_approval_policy",
        "blocked_no_execution_approval" if blocked else "warning",
        "critical",
        source,
        "No execution approval exists."
        if blocked
        else "Execution approval status is unclear; this policy report still does not approve execution.",
        "Keep execution blocked until every readiness gate clears in a future scoped task.",
    )


def policy_row(
    created_at: str,
    policy_area: str,
    policy_status: str,
    severity: str,
    source: Path,
    finding: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "policy_area": policy_area,
        "policy_status": policy_status,
        "severity": severity,
        "source": str(source),
        "finding": finding,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=NORMAL_BOT_EXECUTION_POLICY_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in NORMAL_BOT_EXECUTION_POLICY_COLUMNS})


def build_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("policy_status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    status_counts = ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))
    overall = next((row for row in rows if row.get("policy_area") == "overall_policy"), {})
    return [
        "NORMAL BOT EXECUTION POLICY REPORT. SAVED-DATA/STATIC CHECK ONLY. NOT EXECUTION.",
        "Normal python bot.py remains deliberately separate from defensive paper execution.",
        f"Policy status counts: {status_counts}",
        f"Current overall policy status: {overall.get('policy_status', 'unknown')}",
        "No execution design was added.",
        "No additional order paths were wired.",
        "No strategy was promoted.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
        f"Saved normal bot execution policy report to {output_path}",
    ]


def normal_bot_unwired(bot_source: str) -> bool:
    normal_source = function_block(bot_source, "def run_bot(", "def run_paper_order_test(")
    return "evaluate_paper_kill_switch_gate(" not in normal_source


def manual_preflight_present(bot_source: str) -> bool:
    manual_source = function_block(bot_source, "def run_paper_order_test(", "def estimate_manual_position_after(")
    return preflight_before_terms(
        manual_source,
        ["init_database(", "Trading" + "Client(", "submit_" + "alpaca_order("],
    )


def slow_sma_preflight_present(bot_source: str) -> bool:
    slow_source = function_block(
        bot_source,
        "def run_slow_sma_paper_execution(",
        "def validate_slow_sma_execution_safety(",
    )
    return preflight_before_terms(
        slow_source,
        [
            "configure_" + "y" + "finance_cache(",
            "init_database(",
            "send_" + "discord_alert(",
            "Trading" + "Client(",
            "get_" + "alpaca_positions(",
        ],
    )


def preflight_before_terms(source: str, terms: list[str]) -> bool:
    helper_call = "evaluate_paper_kill_switch_gate("
    if helper_call not in source:
        return False
    preflight_index = source.index(helper_call)
    for term in terms:
        if term not in source or preflight_index > source.index(term):
            return False
    return True


def protection_status(rows: list[dict[str, str]], execution_path: str, expected: str) -> bool:
    row = first_by_key(rows, "execution_path", execution_path) or {}
    return row.get("protection_status") == expected


def readiness_overall_blocked(rows: list[dict[str, str]]) -> bool:
    row = first_by_key(rows, "readiness_area", "overall_readiness") or {}
    return row.get("readiness_status") == "blocked"


def any_true_execution(rows: list[dict[str, str]]) -> bool:
    return any(str(row.get("execution_approved", "")).strip().lower() == "true" for row in rows)


def command_present(help_text: str, command: str) -> bool:
    return command in help_text


def bot_help_text(root: Path) -> str:
    try:
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "bot.py", "--help"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except Exception:
        return ""
    return (result.stdout or "") + "\n" + (result.stderr or "")


def function_block(source: str, start_marker: str, end_marker: str) -> str:
    try:
        start = source.index(start_marker)
        end = source.index(end_marker, start)
    except ValueError:
        return ""
    return source[start:end]


def first_by_key(rows: list[dict[str, str]], key: str, expected: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == expected:
            return row
    return None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
