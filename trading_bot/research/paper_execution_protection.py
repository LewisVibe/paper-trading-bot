"""Saved-data/static-source paper execution protection checkpoint report."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PAPER_EXECUTION_PROTECTION_COLUMNS = [
    "created_at",
    "execution_path",
    "protection_status",
    "severity",
    "source",
    "finding",
    "currently_blocks_execution",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class PaperExecutionProtectionReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_execution_protection_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/paper_execution_protection_report.csv",
    created_at: str | None = None,
) -> PaperExecutionProtectionReportResult:
    root = Path(root_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    rows = build_protection_rows(root, created)
    output_path = root / output_filename
    write_rows(output_path, rows)
    return PaperExecutionProtectionReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, output_path),
    )


def build_protection_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    bot_path = root / "bot.py"
    bot_source = read_text(bot_path)
    gate_rows = read_csv_rows(root / "data" / "paper_kill_switch_gate_report.csv")
    readiness_rows = read_csv_rows(root / "data" / "defensive_execution_readiness_report.csv")

    manual_protected = manual_preflight_present(bot_source)
    slow_sma_protected = slow_sma_preflight_present(bot_source)
    normal_unchanged = normal_bot_unwired(bot_source)
    readiness_blocked = readiness_overall_blocked(readiness_rows)
    any_execution_approved = any_true_execution(gate_rows) or any_true_execution(readiness_rows)
    current_blockers = readiness_blocked or gate_has_blockers(gate_rows) or any_execution_approved

    rows = [
        manual_paper_order_row(created_at, bot_path, manual_protected, current_blockers),
        slow_sma_row(created_at, bot_path, slow_sma_protected, current_blockers),
        normal_bot_row(created_at, bot_path, normal_unchanged),
        execution_readiness_row(created_at, root / "data" / "defensive_execution_readiness_report.csv", readiness_blocked),
    ]
    rows.append(overall_row(created_at, root, rows, any_execution_approved))
    return rows


def manual_paper_order_row(
    created_at: str,
    source: Path,
    protected: bool,
    current_blockers: bool,
) -> dict[str, Any]:
    if protected:
        return protection_row(
            created_at,
            "manual_paper_order_test",
            "protected_by_kill_switch_preflight",
            "info",
            source,
            "--paper-order-test has kill-switch preflight and currently refuses under blocked prerequisites.",
            current_blockers,
            "Keep manual paper-order testing blocked until every saved prerequisite explicitly passes.",
        )
    return protection_row(
        created_at,
        "manual_paper_order_test",
        "blocked",
        "critical",
        source,
        "--paper-order-test preflight was not confirmed before execution-capable work.",
        True,
        "Restore manual paper-order kill-switch preflight before any manual paper-order smoke test.",
    )


def slow_sma_row(
    created_at: str,
    source: Path,
    protected: bool,
    current_blockers: bool,
) -> dict[str, Any]:
    if protected:
        return protection_row(
            created_at,
            "slow_sma_paper_execution",
            "protected_by_kill_switch_preflight",
            "info",
            source,
            "--execute-slow-sma-paper has kill-switch preflight and currently refuses under blocked prerequisites.",
            current_blockers,
            "Keep slow SMA paper execution blocked until every saved prerequisite explicitly passes.",
        )
    return protection_row(
        created_at,
        "slow_sma_paper_execution",
        "blocked",
        "critical",
        source,
        "--execute-slow-sma-paper preflight was not confirmed before execution-capable work.",
        True,
        "Restore slow SMA kill-switch preflight before any slow SMA paper execution.",
    )


def normal_bot_row(created_at: str, source: Path, normal_unchanged: bool) -> dict[str, Any]:
    return protection_row(
        created_at,
        "normal_bot_order_path",
        "deliberately_unchanged_future_work" if normal_unchanged else "warning",
        "high",
        source,
        "Normal python bot.py order path remains deliberately unchanged and must not be treated as execution-approved."
        if normal_unchanged
        else "Normal python bot.py order path appears to contain paper kill-switch helper wiring; review manually.",
        True,
        "Do not wire normal bot behavior without a future scoped safety task and no-network verifier.",
    )


def execution_readiness_row(
    created_at: str,
    source: Path,
    readiness_blocked: bool,
) -> dict[str, Any]:
    return protection_row(
        created_at,
        "execution_readiness",
        "blocked" if readiness_blocked else "warning",
        "critical",
        source,
        "Defensive execution readiness remains blocked."
        if readiness_blocked
        else "Defensive execution readiness is missing or unclear; this report still cannot approve execution.",
        True,
        "Keep execution blocked until readiness reports explicitly allow progress in a future scoped task.",
    )


def overall_row(
    created_at: str,
    root: Path,
    prior_rows: list[dict[str, Any]],
    any_execution_approved: bool,
) -> dict[str, Any]:
    protected = {
        row["execution_path"]
        for row in prior_rows
        if row.get("protection_status") == "protected_by_kill_switch_preflight"
    }
    normal = next((row for row in prior_rows if row.get("execution_path") == "normal_bot_order_path"), {})
    expected_state = (
        {"manual_paper_order_test", "slow_sma_paper_execution"}.issubset(protected)
        and normal.get("protection_status") == "deliberately_unchanged_future_work"
        and not any_execution_approved
    )
    return protection_row(
        created_at,
        "overall_protection_state",
        "explicit_paper_paths_protected_but_execution_blocked" if expected_state else "blocked",
        "critical",
        root,
        "Explicit paper execution commands have kill-switch preflight, normal bot remains unchanged/future work, and no execution approval exists."
        if expected_state
        else "Paper execution protection state needs manual review before any further execution discussion.",
        True,
        "Next safe gate: keep normal bot unwired and blocked until a future scoped safety design is explicitly requested.",
    )


def protection_row(
    created_at: str,
    execution_path: str,
    protection_status: str,
    severity: str,
    source: Path,
    finding: str,
    currently_blocks_execution: bool,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "execution_path": execution_path,
        "protection_status": protection_status,
        "severity": severity,
        "source": str(source),
        "finding": finding,
        "currently_blocks_execution": currently_blocks_execution,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PAPER_EXECUTION_PROTECTION_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PAPER_EXECUTION_PROTECTION_COLUMNS})


def build_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("protection_status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    status_counts = ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))
    overall = next((row for row in rows if row.get("execution_path") == "overall_protection_state"), {})
    return [
        "PAPER EXECUTION PROTECTION REPORT. SAVED-DATA/STATIC CHECK ONLY. NOT EXECUTION.",
        f"Protection status counts: {status_counts}",
        f"Current overall protection status: {overall.get('protection_status', 'unknown')}",
        "No execution design was added.",
        "No additional order paths were wired.",
        "No strategy was promoted.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
        f"Saved paper execution protection report to {output_path}",
    ]


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
            "process_slow_sma_execution_ticker(",
        ],
    )


def normal_bot_unwired(bot_source: str) -> bool:
    normal_source = function_block(bot_source, "def run_bot(", "def run_paper_order_test(")
    return "evaluate_paper_kill_switch_gate(" not in normal_source


def preflight_before_terms(source: str, terms: list[str]) -> bool:
    helper_call = "evaluate_paper_kill_switch_gate("
    if helper_call not in source:
        return False
    preflight_index = source.index(helper_call)
    for term in terms:
        if term not in source or preflight_index > source.index(term):
            return False
    return True


def readiness_overall_blocked(rows: list[dict[str, str]]) -> bool:
    overall = first_by_key(rows, "readiness_area", "overall_readiness") or {}
    return overall.get("readiness_status") == "blocked"


def gate_has_blockers(rows: list[dict[str, str]]) -> bool:
    return any(
        row.get("gate_status") in {"blocked", "future_work_required", "fail"}
        or bool_from_any(row.get("blocks_future_execution_design"))
        for row in rows
    )


def any_true_execution(rows: list[dict[str, str]]) -> bool:
    return any(str(row.get("execution_approved", "")).strip().lower() == "true" for row in rows)


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


def bool_from_any(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"
