"""Manual paper-order smoke-test readiness pack.

This report is a saved-data/static readiness review only. It never calls
Alpaca, reads positions, creates orders, writes trade logs, sends alerts, or
schedules anything.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("data/paper_order_smoke_test_readiness_pack.csv")

FINAL_BLOCKED = "smoke_test_discussion_blocked"
FINAL_MANUAL_REVIEW = "smoke_test_discussion_needs_manual_review"
FINAL_READY_FOR_CONFIRMATION = "smoke_test_discussion_ready_for_explicit_manual_confirmation"

PROPOSED_TICKER = "AAPL"
PROPOSED_SIDE = "buy"
PROPOSED_QUANTITY = "1"
PROPOSED_PURPOSE = "tiny_connectivity_and_order_path_smoke_test_manual_review_only"

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "evidence_source",
    "details",
    "proposed_ticker",
    "proposed_side",
    "proposed_quantity",
    "proposed_purpose",
    "blocker",
    "recommended_next_step",
    "alpaca_called",
    "order_execution_approved",
    "execution_approved",
    "scheduling_approved",
    "run_command_now",
    "smoke_test_discussion_status",
]


@dataclass
class PaperOrderSmokeTestReadinessResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_order_smoke_test_readiness_pack(
    root_dir: Path | str = ".",
) -> PaperOrderSmokeTestReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows(root, created_at)
    final_status = choose_final_status(rows)
    rows.append(
        readiness_row(
            created_at,
            "final_smoke_test_discussion_status",
            final_status,
            "blocked" if final_status == FINAL_BLOCKED else ("info" if final_status == FINAL_READY_FOR_CONFIRMATION else "warning"),
            "readiness rows",
            final_details(final_status, rows),
            "",
            "",
            "",
            "",
            final_status == FINAL_BLOCKED,
            final_next_step(final_status),
            final_status,
        )
    )
    output_path = root / OUTPUT_PATH
    write_rows(output_path, rows)
    return PaperOrderSmokeTestReadinessResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows),
    )


def build_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    bot_source = read_text(root / "bot.py")
    hermes_docs = "\n".join(
        read_text(root / path)
        for path in [
            Path("docs/HERMES_CRON_JOB_DESIGN.md"),
            Path("docs/HERMES_TASK_BOARD.md"),
            Path("docs/CURRENT_STATE.md"),
        ]
    )
    alpaca_readiness = read_csv(root / "data" / "alpaca_paper_readiness_report.csv", limit=80)
    stock_readiness = read_csv(root / "data" / "stock_etf_paper_execution_readiness_report.csv", limit=80)
    project_summary = read_csv(root / "data" / "project_research_state_summary.csv", limit=50)
    project_next_steps = read_csv(root / "data" / "project_research_state_next_steps.csv", limit=50)
    execution_eligibility = read_csv(root / "data" / "execution_eligibility_report.csv", limit=80)
    paper_protection = read_csv(root / "data" / "paper_execution_protection_report.csv", limit=80)
    kill_switch_gate = read_csv(root / "data" / "paper_kill_switch_gate_report.csv", limit=80)

    return [
        alpaca_readiness_prerequisite_row(created_at, alpaca_readiness),
        alpaca_readonly_prerequisite_row(created_at, alpaca_readiness),
        config_example_defaults_row(created_at, root / "config.example.json"),
        config_presence_row(created_at, (root / "config.json").exists()),
        manual_smoke_test_command_boundary_row(created_at, bot_source),
        smoke_test_not_scheduled_row(created_at, hermes_docs),
        proposed_future_template_row(created_at),
        stock_research_boundary_row(created_at, project_summary, project_next_steps),
        stock_execution_gate_context_row(created_at, stock_readiness),
        kill_switch_and_protection_context_row(created_at, execution_eligibility, paper_protection, kill_switch_gate),
        crypto_out_of_scope_row(created_at, project_summary),
        static_safety_boundary_row(created_at),
    ]


def alpaca_readiness_prerequisite_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return readiness_row(
            created_at,
            "alpaca_readiness_report_present",
            "manual_review_required_missing_alpaca_readiness_report",
            "warning",
            "data/alpaca_paper_readiness_report.csv",
            "Saved Alpaca paper readiness report is missing or empty. This pack did not call Alpaca.",
            "",
            "",
            "",
            "",
            False,
            "run_alpaca_paper_readiness_report_before_smoke_test_discussion",
            FINAL_MANUAL_REVIEW,
        )
    final_status = final_status_from_rows(rows, "final_readiness_status")
    static_ready = "alpaca_paper_static_ready_needs_readonly_check" in final_status or row_status_exists(
        rows, "alpaca_paper_static_ready_needs_readonly_check"
    )
    return readiness_row(
        created_at,
        "alpaca_static_readiness_prerequisite",
        "pass" if static_ready else "manual_review_required_static_readiness_unclear",
        "info" if static_ready else "warning",
        "data/alpaca_paper_readiness_report.csv",
        f"latest_alpaca_readiness_status={final_status or 'unavailable'}; saved report summarised only.",
        "",
        "",
        "",
        "",
        False,
        "review_saved_alpaca_readiness_report",
        FINAL_MANUAL_REVIEW,
    )


def alpaca_readonly_prerequisite_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        status = "manual_review_required_readonly_check_not_recorded"
        details = "No saved Alpaca readiness report is available, so read-only connectivity evidence is not recorded."
    else:
        final_status = final_status_from_rows(rows, "final_readiness_status")
        readonly_passed = "alpaca_paper_readonly_check_passed_manual_smoke_test_next" in final_status or row_status_exists(
            rows, "alpaca_paper_readonly_check_passed_manual_smoke_test_next"
        )
        status = "pass" if readonly_passed else "manual_review_required_readonly_check_not_recorded"
        details = (
            "Saved Alpaca readiness indicates read-only account/status check passed."
            if readonly_passed
            else f"Read-only Alpaca check pass is not recorded in the saved report; latest_status={final_status or 'unavailable'}."
        )
    return readiness_row(
        created_at,
        "alpaca_readonly_connectivity_prerequisite",
        status,
        "info" if status == "pass" else "warning",
        "data/alpaca_paper_readiness_report.csv",
        details + " This pack did not call Alpaca.",
        "",
        "",
        "",
        "",
        False,
        "record_or_review_confirmed_readonly_alpaca_check_before_any_smoke_test",
        FINAL_MANUAL_REVIEW,
    )


def config_example_defaults_row(created_at: str, path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report-only failure capture
        return readiness_row(
            created_at,
            "config_example_safe_defaults",
            "blocked_unreadable_config_example",
            "blocked",
            "config.example.json",
            f"Could not parse config.example.json: {type(exc).__name__}.",
            "",
            "",
            "",
            "",
            True,
            "restore_parseable_safe_config_example",
            FINAL_BLOCKED,
        )
    dry_run = data.get("dry_run") is True
    allow_shorting = data.get("allow_shorting") is False
    paper = isinstance(data.get("alpaca"), dict) and data["alpaca"].get("paper") is True
    ok = dry_run and allow_shorting and paper
    return readiness_row(
        created_at,
        "config_example_safe_defaults",
        "pass" if ok else "blocked_unsafe_config_example_defaults",
        "info" if ok else "blocked",
        "config.example.json",
        f"dry_run_true={dry_run}; allow_shorting_false={allow_shorting}; alpaca_paper_true={paper}.",
        "",
        "",
        "",
        "",
        not ok,
        "restore_safe_paper_only_defaults_before_smoke_test_discussion" if not ok else "none",
        FINAL_MANUAL_REVIEW,
    )


def config_presence_row(created_at: str, present: bool) -> dict[str, Any]:
    return readiness_row(
        created_at,
        "local_config_presence_boolean_only",
        "present_contents_not_read" if present else "missing_manual_setup_required",
        "info" if present else "warning",
        "config.json presence only",
        f"config.json_present={present}; contents were not read or printed.",
        "",
        "",
        "",
        "",
        False,
        "manual_review_local_paper_config_before_any_smoke_test" if present else "create_local_config_only_after_manual_review",
        FINAL_MANUAL_REVIEW,
    )


def manual_smoke_test_command_boundary_row(created_at: str, bot_source: str) -> dict[str, Any]:
    checks = {
        "paper_order_flag_present": "--paper-order-test" in bot_source,
        "confirm_flag_present": "--confirm-paper-order" in bot_source,
        "confirm_variable_present": "confirm_paper_order" in bot_source,
        "dry_run_refusal_message_present": "Re-run with --confirm-paper-order" in bot_source,
    }
    ok = all(checks.values())
    return readiness_row(
        created_at,
        "existing_manual_smoke_test_command_boundary",
        "pass" if ok else "blocked_confirmation_gate_unclear",
        "info" if ok else "blocked",
        "bot.py source text",
        "; ".join(f"{name}={value}" for name, value in checks.items()) + ". Command remains high-risk/manual-only and was not run.",
        "",
        "",
        "",
        "",
        not ok,
        "restore_or_review_confirmation_gate_before_any_smoke_test_discussion" if not ok else "none",
        FINAL_MANUAL_REVIEW,
    )


def smoke_test_not_scheduled_row(created_at: str, docs_text: str) -> dict[str, Any]:
    status_only = "paper-bot-vps-status-check" in docs_text and "--vps-daily-monitoring-summary" in docs_text
    no_execution = "does not run refresh commands" in docs_text and "paper-order" in docs_text.lower()
    ok = status_only and no_execution
    return readiness_row(
        created_at,
        "manual_smoke_test_not_scheduled",
        "pass" if ok else "manual_review_required_schedule_boundary",
        "info" if ok else "warning",
        "Hermes/status docs",
        "Docs keep Hermes status/display only and execution-capable workflows out of scheduling.",
        "",
        "",
        "",
        "",
        False,
        "do_not_schedule_paper_order_smoke_tests",
        FINAL_MANUAL_REVIEW,
    )


def proposed_future_template_row(created_at: str) -> dict[str, Any]:
    return readiness_row(
        created_at,
        "proposed_future_manual_smoke_test_template",
        "proposed_manual_review_only",
        "warning",
        "static conservative template",
        "A tiny future paper-order smoke test template is recorded for manual review only. The terminal summary does not print an execution command.",
        PROPOSED_TICKER,
        PROPOSED_SIDE,
        PROPOSED_QUANTITY,
        PROPOSED_PURPOSE,
        False,
        "manual_review_required_before_any_explicit_confirmation",
        FINAL_MANUAL_REVIEW,
    )


def stock_research_boundary_row(
    created_at: str,
    project_summary: list[dict[str, Any]],
    project_next_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    lead = summary_value(project_summary, "stock_etf_active_research_lead") or "unavailable"
    status = summary_value(project_summary, "stock_etf_status_and_blocker") or "unavailable"
    next_steps = ", ".join(row.get("check_name", "") for row in project_next_steps[:4]) or "unavailable"
    return readiness_row(
        created_at,
        "current_strategy_research_boundary",
        "research_only_connectivity_test_boundary",
        "warning",
        "data/project_research_state_summary.csv; data/project_research_state_next_steps.csv",
        f"stock_etf_lead={lead}; status={status}; next_step_context={next_steps}. A smoke test would be connectivity/order-path only, not strategy execution.",
        "",
        "",
        "",
        "",
        False,
        "keep_strategy_research_separate_from_any_manual_smoke_test",
        FINAL_MANUAL_REVIEW,
    )


def stock_execution_gate_context_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return readiness_row(
            created_at,
            "stock_etf_execution_gate_context",
            "manual_review_required_missing_stock_etf_readiness",
            "warning",
            "data/stock_etf_paper_execution_readiness_report.csv",
            "Saved stock/ETF paper execution readiness report is missing. This does not block static discussion by itself, but it requires review.",
            "",
            "",
            "",
            "",
            False,
            "run_or_review_stock_etf_paper_execution_readiness_report",
            FINAL_MANUAL_REVIEW,
        )
    final_status = final_status_from_rows(rows, "final_paper_execution_discussion_status")
    return readiness_row(
        created_at,
        "stock_etf_execution_gate_context",
        "manual_review_required_execution_gates_block_strategy_execution" if "blocked" in final_status else "saved_gate_context_present",
        "warning",
        "data/stock_etf_paper_execution_readiness_report.csv",
        f"saved_stock_etf_status={final_status or 'unavailable'}; smoke test discussion must not be treated as strategy execution approval.",
        "",
        "",
        "",
        "",
        False,
        "separate_tiny_connectivity_test_from_strategy_execution_approval",
        FINAL_MANUAL_REVIEW,
    )


def kill_switch_and_protection_context_row(
    created_at: str,
    execution_rows: list[dict[str, Any]],
    protection_rows: list[dict[str, Any]],
    kill_switch_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    missing = []
    if not execution_rows:
        missing.append("execution_eligibility")
    if not protection_rows:
        missing.append("paper_execution_protection")
    if not kill_switch_rows:
        missing.append("paper_kill_switch_gate")
    combined = execution_rows + protection_rows + kill_switch_rows
    blocking = any_status_contains(combined, ["blocked", "missing", "manual_review"])
    if missing:
        status = "manual_review_required_missing_protection_reports"
    elif blocking:
        status = "manual_review_required_saved_protection_blockers"
    else:
        status = "saved_protection_context_present"
    return readiness_row(
        created_at,
        "kill_switch_protection_execution_gate_context",
        status,
        "warning" if status != "saved_protection_context_present" else "info",
        "data/execution_eligibility_report.csv; data/paper_execution_protection_report.csv; data/paper_kill_switch_gate_report.csv",
        f"missing={', '.join(missing) if missing else 'none'}; saved_gate_counts={status_counts(combined)}. This pack does not enforce a kill switch.",
        "",
        "",
        "",
        "",
        False,
        "review_saved_protection_and_kill_switch_reports_before_any_manual_smoke_test",
        FINAL_MANUAL_REVIEW,
    )


def crypto_out_of_scope_row(created_at: str, project_summary: list[dict[str, Any]]) -> dict[str, Any]:
    crypto_status = summary_value(project_summary, "crypto_status_and_blockers") or "unavailable"
    return readiness_row(
        created_at,
        "crypto_execution_scope",
        "crypto_execution_out_of_scope",
        "info",
        "data/project_research_state_summary.csv",
        f"crypto_status={crypto_status}. Crypto execution remains out of scope for this stock/ETF paper-order smoke-test discussion.",
        "",
        "",
        "",
        "",
        False,
        "keep_crypto_execution_out_of_scope",
        FINAL_MANUAL_REVIEW,
    )


def static_safety_boundary_row(created_at: str) -> dict[str, Any]:
    return readiness_row(
        created_at,
        "static_report_only_boundary",
        "report_only_no_execution_approval",
        "info",
        "policy boundary",
        "This pack did not call Alpaca, read positions, load config contents, create orders, write trade logs, send alerts, schedule anything, or connect strategies to execution.",
        "",
        "",
        "",
        "",
        False,
        "manual_review_required_before_any_next_step",
        FINAL_MANUAL_REVIEW,
    )


def readiness_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    evidence_source: str,
    details: str,
    proposed_ticker: str,
    proposed_side: str,
    proposed_quantity: str,
    proposed_purpose: str,
    blocker: bool,
    recommended_next_step: str,
    smoke_test_discussion_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "evidence_source": evidence_source,
        "details": details,
        "proposed_ticker": proposed_ticker,
        "proposed_side": proposed_side,
        "proposed_quantity": proposed_quantity,
        "proposed_purpose": proposed_purpose,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        "alpaca_called": False,
        "order_execution_approved": False,
        "execution_approved": False,
        "scheduling_approved": False,
        "run_command_now": False,
        "smoke_test_discussion_status": smoke_test_discussion_status,
    }


def choose_final_status(rows: list[dict[str, Any]]) -> str:
    if any(str(row.get("severity", "")) == "blocked" or truthy(row.get("blocker")) for row in rows):
        return FINAL_BLOCKED
    if any(str(row.get("severity", "")) == "warning" for row in rows):
        return FINAL_MANUAL_REVIEW
    return FINAL_READY_FOR_CONFIRMATION


def final_details(final_status: str, rows: list[dict[str, Any]]) -> str:
    blockers = [row for row in rows if str(row.get("severity", "")) == "blocked" or truthy(row.get("blocker"))]
    warnings = [row for row in rows if str(row.get("severity", "")) == "warning"]
    key_items = blockers[:5] if blockers else warnings[:5]
    key_names = ", ".join(str(row.get("check_name", "")) for row in key_items) or "none"
    return f"final_status={final_status}; blocker_count={len(blockers)}; manual_review_count={len(warnings)}; key_items={key_names}."


def final_next_step(final_status: str) -> str:
    if final_status == FINAL_READY_FOR_CONFIRMATION:
        return "manual_review_can_consider_explicit_confirmation_for_one_tiny_paper_smoke_test"
    if final_status == FINAL_BLOCKED:
        return "resolve_blockers_before_smoke_test_discussion"
    return "manual_review_required_before_any_explicit_confirmation"


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    final_row = next((row for row in rows if row.get("check_name") == "final_smoke_test_discussion_status"), {})
    blockers = [row for row in rows if str(row.get("severity", "")) == "blocked" or truthy(row.get("blocker"))]
    warnings = [row for row in rows if str(row.get("severity", "")) == "warning"]
    key_items = blockers[:5] if blockers else warnings[:5]
    key_names = ", ".join(str(row.get("check_name", "")) for row in key_items) or "none"
    counts = Counter(str(row.get("check_status", "")) for row in rows)
    template = next((row for row in rows if row.get("check_name") == "proposed_future_manual_smoke_test_template"), {})
    return [
        "Paper-order smoke-test readiness pack complete. Report-only; no order execution approved.",
        f"final_smoke_test_discussion_status: {final_row.get('check_status', 'unavailable')}",
        f"blocker_count: {len(blockers)}",
        f"manual_review_item_count: {len(warnings)}",
        "proposed_future_manual_test: "
        f"ticker={template.get('proposed_ticker', '')}; side={template.get('proposed_side', '')}; quantity={template.get('proposed_quantity', '')}; manual_review_only=true",
        f"key_blockers_or_manual_review_items: {key_names}",
        f"check_counts: {format_counts(counts)}",
        f"recommended_next_step: {final_row.get('recommended_next_step', 'unavailable')}",
        "alpaca_called=false",
        "order_execution_approved=false",
        "execution_approved=false",
        "scheduling_approved=false",
        f"Saved readiness pack to {output_path}",
        "Warning: this summary intentionally does not print a paper-order command.",
    ]


def final_status_from_rows(rows: list[dict[str, Any]], final_check_name: str) -> str:
    final = next((row for row in rows if row.get("check_name") == final_check_name), {})
    return str(final.get("check_status") or final.get("smoke_test_discussion_status") or "")


def row_status_exists(rows: list[dict[str, Any]], status: str) -> bool:
    return any(status in str(row.get("check_status", "")) for row in rows)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("metric_name") == key or row.get("check_name") == key:
            return str(row.get("metric_value") or row.get("details") or row.get("status") or "")
    return ""


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


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts: Counter[str] = Counter()
    for row in rows:
        for key, value in row.items():
            if "status" in key.lower() and str(value).strip():
                counts[str(value).strip()] += 1
                break
    return format_counts(counts)


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_csv(path: Path, limit: int = 100) -> list[dict[str, Any]]:
    try:
        rows: list[dict[str, Any]] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for index, row in enumerate(csv.DictReader(handle)):
                if index >= limit:
                    break
                rows.append(row)
        return rows
    except FileNotFoundError:
        return []


def format_counts(counts: Counter[str]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
