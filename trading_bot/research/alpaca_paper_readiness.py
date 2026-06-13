"""Alpaca paper readiness/preflight report.

Default mode is static and no-network. The optional read-only Alpaca check is
available only behind an explicit confirmation flag and never submits, cancels,
replaces, or creates orders.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("data/alpaca_paper_readiness_report.csv")

STATIC_READY_LABEL = "alpaca_paper_static_ready_needs_readonly_check"
READONLY_PASSED_LABEL = "alpaca_paper_readonly_check_passed_manual_smoke_test_next"
BLOCKED_LABEL = "alpaca_paper_readiness_blocked"
MANUAL_REVIEW_LABEL = "alpaca_paper_readiness_manual_review_required"

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "mode",
    "evidence_source",
    "details",
    "recommended_next_step",
    "execution_approved",
    "scheduling_approved",
    "orders_possible",
    "alpaca_called",
]

SAFE_ENV_KEYS = ["ALPACA_API_KEY", "ALPACA_SECRET_KEY"]


@dataclass
class AlpacaPaperReadinessResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_alpaca_paper_readiness_report(
    root_dir: Path | str = ".",
    confirm_readonly_alpaca_check: bool = False,
) -> AlpacaPaperReadinessResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = build_static_rows(root, created_at)
    if confirm_readonly_alpaca_check:
        rows.extend(build_readonly_alpaca_rows(root, created_at))
    else:
        rows.append(
            report_row(
                created_at,
                "readonly_alpaca_check_confirmation",
                "not_run_confirmation_required",
                "warning",
                "static",
                "explicit confirmation flag",
                "Read-only Alpaca connectivity was not attempted because --confirm-readonly-alpaca-check was not provided.",
                "run_confirmed_readonly_check_only_after_manual_review",
                alpaca_called=False,
            )
        )

    final_label = choose_final_label(rows, confirm_readonly_alpaca_check)
    rows.append(
        report_row(
            created_at,
            "final_readiness_status",
            final_label,
            "blocked" if final_label == BLOCKED_LABEL else ("warning" if final_label != READONLY_PASSED_LABEL else "info"),
            "readonly" if confirm_readonly_alpaca_check else "static",
            "readiness rows",
            final_details(final_label, rows),
            final_next_step(final_label),
            alpaca_called=confirm_readonly_alpaca_check,
        )
    )
    output_path = root / OUTPUT_PATH
    write_rows(output_path, rows)
    return AlpacaPaperReadinessResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows),
    )


def build_static_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    config_example = root / "config.example.json"
    config_present = (root / "config.json").exists()
    bot_source = read_text(root / "bot.py")
    config_source = read_text(root / "trading_bot" / "config.py")
    hermes_docs = "\n".join(
        read_text(root / path)
        for path in [
            Path("docs/HERMES_CRON_JOB_DESIGN.md"),
            Path("docs/HERMES_TASK_BOARD.md"),
            Path("docs/CURRENT_STATE.md"),
        ]
    )
    readiness_rows = read_csv(root / "data" / "stock_etf_paper_execution_readiness_report.csv", limit=50)

    rows = [
        config_example_exists_row(created_at, config_example),
        config_example_defaults_row(created_at, config_example),
        config_presence_row(created_at, config_present),
        environment_presence_row(created_at),
        alpaca_package_row(created_at),
        paper_only_refusal_row(created_at, config_source),
        high_risk_confirmation_gates_row(created_at, bot_source),
        normal_bot_not_scheduled_row(created_at, hermes_docs),
        hermes_status_only_row(created_at, hermes_docs),
        stock_etf_readiness_exists_row(created_at, readiness_rows),
        stock_etf_readiness_status_row(created_at, readiness_rows),
        static_execution_boundary_row(created_at),
    ]
    return rows


def build_readonly_alpaca_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        from trading_bot.config import ConfigError, load_config

        config = load_config(root / "config.json", force_dry_run=True)
    except Exception as exc:  # noqa: BLE001 - report-only failure capture
        rows.append(
            report_row(
                created_at,
                "readonly_config_load",
                "blocked_config_load_failed",
                "blocked",
                "readonly",
                "local config loader",
                f"Config load failed safely without printing contents: {type(exc).__name__}.",
                "fix_local_paper_config_before_readonly_connectivity_check",
                alpaca_called=False,
            )
        )
        return rows

    rows.append(
        report_row(
            created_at,
            "readonly_config_load",
            "pass",
            "info",
            "readonly",
            "local config loader",
            "Config loaded successfully. Contents and credential values were not printed.",
            "continue_readonly_paper_checks",
            alpaca_called=False,
        )
    )
    paper = bool(getattr(config, "alpaca_paper", False))
    rows.append(
        report_row(
            created_at,
            "readonly_alpaca_paper_mode",
            "pass" if paper else "blocked_not_paper_mode",
            "info" if paper else "blocked",
            "readonly",
            "config object redacted",
            "alpaca.paper is true." if paper else "alpaca.paper is not true; live trading is out of scope.",
            "continue_readonly_check" if paper else "restore_alpaca_paper_true_before_any_connectivity_check",
            alpaca_called=False,
        )
    )
    key_available = bool(getattr(config, "alpaca_api_key", ""))
    secret_available = bool(getattr(config, "alpaca_secret_key", ""))
    rows.append(
        report_row(
            created_at,
            "readonly_alpaca_credentials_present",
            "pass" if key_available and secret_available else "blocked_missing_credentials",
            "info" if key_available and secret_available else "blocked",
            "readonly",
            "config object redacted",
            f"api_key_present={key_available}; secret_key_present={secret_available}; values redacted.",
            "continue_readonly_check" if key_available and secret_available else "configure_paper_credentials_without_exposing_values",
            alpaca_called=False,
        )
    )
    if not paper or not key_available or not secret_available:
        return rows

    try:
        from alpaca.trading.client import TradingClient

        client = TradingClient(
            getattr(config, "alpaca_api_key"),
            getattr(config, "alpaca_secret_key"),
            paper=True,
        )
        rows.append(
            report_row(
                created_at,
                "readonly_trading_client_created",
                "pass",
                "info",
                "readonly",
                "Alpaca TradingClient paper mode",
                "TradingClient was created with paper=True. Sensitive identifiers were not printed.",
                "continue_readonly_account_status_check",
                alpaca_called=True,
            )
        )
        account = client.get_account()
        rows.append(readonly_account_status_row(created_at, account))
    except Exception as exc:  # noqa: BLE001 - report-only failure capture
        rows.append(
            report_row(
                created_at,
                "readonly_alpaca_account_status",
                "manual_review_required_readonly_check_failed",
                "warning",
                "readonly",
                "Alpaca read-only account endpoint",
                f"Read-only account/status check failed safely: {type(exc).__name__}. Sensitive values were not printed.",
                "manual_review_readonly_connectivity_before_any_smoke_test_discussion",
                alpaca_called=True,
            )
        )
    return rows


def readonly_account_status_row(created_at: str, account: Any) -> dict[str, Any]:
    status = str(getattr(account, "status", "unknown"))
    account_blocked = bool(getattr(account, "account_blocked", False))
    trading_blocked = bool(getattr(account, "trading_blocked", False))
    blocked = account_blocked or trading_blocked
    return report_row(
        created_at,
        "readonly_alpaca_account_status",
        "manual_review_required_account_blocked" if blocked else "pass",
        "blocked" if blocked else "info",
        "readonly",
        "Alpaca read-only account endpoint",
        f"status={redact_account_status(status)}; account_blocked={account_blocked}; trading_blocked={trading_blocked}; identifiers redacted.",
        "manual_review_account_block_flags" if blocked else "manual_paper_smoke_test_design_review_can_be_considered_next",
        alpaca_called=True,
    )


def config_example_exists_row(created_at: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    return report_row(
        created_at,
        "config_example_exists",
        "pass" if exists else "blocked_missing_config_example",
        "info" if exists else "blocked",
        "static",
        "config.example.json",
        "config.example.json exists." if exists else "config.example.json is missing.",
        "none" if exists else "restore_safe_config_example",
        alpaca_called=False,
    )


def config_example_defaults_row(created_at: str, path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return report_row(
            created_at,
            "config_example_safe_defaults",
            "blocked_unreadable_config_example",
            "blocked",
            "static",
            "config.example.json",
            f"Could not parse config.example.json: {type(exc).__name__}.",
            "restore_parseable_safe_config_example",
            alpaca_called=False,
        )
    dry_run = data.get("dry_run") is True
    allow_shorting = data.get("allow_shorting") is False
    paper = isinstance(data.get("alpaca"), dict) and data["alpaca"].get("paper") is True
    passed = dry_run and allow_shorting and paper
    return report_row(
        created_at,
        "config_example_safe_defaults",
        "pass" if passed else "blocked_unsafe_example_defaults",
        "info" if passed else "blocked",
        "static",
        "config.example.json",
        f"dry_run_true={dry_run}; allow_shorting_false={allow_shorting}; alpaca_paper_true={paper}.",
        "none" if passed else "restore_dry_run_true_allow_shorting_false_alpaca_paper_true",
        alpaca_called=False,
    )


def config_presence_row(created_at: str, present: bool) -> dict[str, Any]:
    return report_row(
        created_at,
        "local_config_presence",
        "present_contents_not_read" if present else "missing_manual_setup_required_for_readonly_check",
        "info" if present else "warning",
        "static",
        "config.json presence only",
        f"config.json_present={present}; contents were not read or printed in static mode.",
        "none" if present else "create_local_config_only_when_ready_for_confirmed_readonly_check",
        alpaca_called=False,
    )


def environment_presence_row(created_at: str) -> dict[str, Any]:
    present = {key: bool(os.getenv(key)) for key in SAFE_ENV_KEYS}
    ok = all(present.values())
    return report_row(
        created_at,
        "environment_credential_presence",
        "present_values_redacted" if ok else "missing_or_partial_values_redacted",
        "info" if ok else "warning",
        "static",
        "environment variable presence only",
        "; ".join(f"{key}_present={value}" for key, value in present.items()),
        "none" if ok else "provide_paper_credentials_only_when_ready_for_confirmed_readonly_check",
        alpaca_called=False,
    )


def alpaca_package_row(created_at: str) -> dict[str, Any]:
    available = importlib.util.find_spec("alpaca") is not None
    return report_row(
        created_at,
        "alpaca_package_available",
        "pass" if available else "blocked_missing_alpaca_package",
        "info" if available else "blocked",
        "static",
        "importlib metadata",
        f"alpaca_package_available={available}; package was not used to call Alpaca in static mode.",
        "none" if available else "install_project_dependencies_before_readonly_check",
        alpaca_called=False,
    )


def paper_only_refusal_row(created_at: str, config_source: str) -> dict[str, Any]:
    present = "alpaca.paper must be true" in config_source and "refuses to use live trading mode" in config_source
    return report_row(
        created_at,
        "paper_only_refusal_logic",
        "pass" if present else "blocked_missing_paper_only_refusal",
        "info" if present else "blocked",
        "static",
        "trading_bot/config.py",
        "Config validation refuses live trading mode." if present else "Could not confirm live-trading refusal wording.",
        "none" if present else "restore_paper_only_refusal_before_any_paper_readiness_discussion",
        alpaca_called=False,
    )


def high_risk_confirmation_gates_row(created_at: str, bot_source: str) -> dict[str, Any]:
    checks = {
        "paper_order_confirm": "--confirm-paper-order" in bot_source and "confirm_paper_order" in bot_source,
        "slow_sma_confirm": "--confirm-slow-sma-paper" in bot_source and "confirm_slow_sma_paper" in bot_source,
        "paper_order_test": "--paper-order-test" in bot_source,
        "slow_sma_execution": "--execute-slow-sma-paper" in bot_source,
    }
    ok = all(checks.values())
    return report_row(
        created_at,
        "high_risk_commands_confirmation_gated",
        "pass" if ok else "blocked_missing_confirmation_gate",
        "info" if ok else "blocked",
        "static",
        "bot.py source text",
        "; ".join(f"{name}={value}" for name, value in checks.items()),
        "none" if ok else "restore_explicit_confirmation_gates_before_any_smoke_test_discussion",
        alpaca_called=False,
    )


def normal_bot_not_scheduled_row(created_at: str, docs_text: str) -> dict[str, Any]:
    status_only = "paper-bot-vps-status-check" in docs_text and "--vps-daily-monitoring-summary" in docs_text
    normal_not_scheduled = "does not run refresh commands" in docs_text and "normal bot" in docs_text.lower()
    ok = status_only and normal_not_scheduled
    return report_row(
        created_at,
        "normal_bot_not_scheduled",
        "pass" if ok else "manual_review_required_schedule_boundary",
        "info" if ok else "warning",
        "static",
        "Hermes docs",
        "Hermes docs describe status-only monitoring and keep normal bot/execution-capable workflows out of cron.",
        "none" if ok else "review_hermes_docs_before_any_scheduling_discussion",
        alpaca_called=False,
    )


def hermes_status_only_row(created_at: str, docs_text: str) -> dict[str, Any]:
    required = [
        "345188fbb60c",
        "10 10 * * *",
        "Telegram",
        "script-only / no-agent",
        "C:\\dev\\paper-trading-bot",
        "scheduling_approved false",
        "execution_approved false",
    ]
    missing = [phrase for phrase in required if phrase not in docs_text]
    return report_row(
        created_at,
        "hermes_status_display_only",
        "pass" if not missing else "manual_review_required_hermes_boundary",
        "info" if not missing else "warning",
        "static",
        "Hermes docs",
        "Current Hermes cron remains status/display only. missing=" + (", ".join(missing) if missing else "none"),
        "none" if not missing else "update_or_review_hermes_status_boundary_docs",
        alpaca_called=False,
    )


def stock_etf_readiness_exists_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    exists = bool(rows)
    return report_row(
        created_at,
        "stock_etf_paper_execution_readiness_report_exists",
        "present" if exists else "missing_optional_saved_readiness_report",
        "info" if exists else "warning",
        "static",
        "data/stock_etf_paper_execution_readiness_report.csv",
        "Saved stock/ETF paper execution discussion readiness report is available." if exists else "Saved stock/ETF readiness report is missing.",
        "none" if exists else "run_stock_etf_paper_execution_readiness_report_if_needed",
        alpaca_called=False,
    )


def stock_etf_readiness_status_row(created_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    final = next((row for row in rows if row.get("check_name") == "final_paper_execution_discussion_status"), {})
    status = str(final.get("check_status") or "unavailable")
    blocked = "blocked" in status or not final
    return report_row(
        created_at,
        "latest_stock_etf_paper_execution_readiness_status",
        "manual_review_required" if blocked else "saved_status_present",
        "warning" if blocked else "info",
        "static",
        "data/stock_etf_paper_execution_readiness_report.csv",
        f"latest_saved_status={status}; saved output was summarised without printing full CSV contents.",
        "resolve_stock_etf_readiness_blockers_before_alpaca_smoke_test_discussion" if blocked else "review_saved_status_before_readonly_check",
        alpaca_called=False,
    )


def static_execution_boundary_row(created_at: str) -> dict[str, Any]:
    return report_row(
        created_at,
        "static_execution_boundary",
        "execution_and_scheduling_not_approved",
        "info",
        "static",
        "policy boundary",
        "Research/report/preview/display commands do not approve execution. Live trading is out of scope. Execution-capable commands remain high-risk/manual-only.",
        "manual_review_required_before_any_confirmed_paper_smoke_test",
        alpaca_called=False,
    )


def report_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    mode: str,
    evidence_source: str,
    details: str,
    recommended_next_step: str,
    alpaca_called: bool,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "mode": mode,
        "evidence_source": evidence_source,
        "details": details,
        "recommended_next_step": recommended_next_step,
        "execution_approved": False,
        "scheduling_approved": False,
        "orders_possible": False,
        "alpaca_called": alpaca_called,
    }


def choose_final_label(rows: list[dict[str, Any]], readonly_confirmed: bool) -> str:
    statuses = {str(row.get("check_status", "")) for row in rows}
    severities = {str(row.get("severity", "")) for row in rows}
    if "blocked" in severities:
        return BLOCKED_LABEL
    if readonly_confirmed:
        if any(status.startswith("manual_review_required") for status in statuses):
            return MANUAL_REVIEW_LABEL
        return READONLY_PASSED_LABEL
    if statuses == {"pass"}:
        return STATIC_READY_LABEL
    if all(severity in {"info", "warning"} for severity in severities):
        return STATIC_READY_LABEL
    return MANUAL_REVIEW_LABEL


def final_details(final_label: str, rows: list[dict[str, Any]]) -> str:
    blockers = [row for row in rows if row.get("severity") == "blocked"]
    warnings = [row for row in rows if row.get("severity") == "warning"]
    key_blockers = ", ".join(str(row.get("check_name", "")) for row in blockers[:5]) or "none"
    return f"final_label={final_label}; blocker_count={len(blockers)}; warning_count={len(warnings)}; key_blockers={key_blockers}."


def final_next_step(final_label: str) -> str:
    if final_label == READONLY_PASSED_LABEL:
        return "manual_review_can_consider_a_separately_confirmed_paper_smoke_test_next"
    if final_label == STATIC_READY_LABEL:
        return "manual_review_then_run_confirmed_readonly_alpaca_check_if_appropriate"
    if final_label == BLOCKED_LABEL:
        return "resolve_blockers_before_readonly_or_smoke_test_discussion"
    return "manual_review_required_before_any_next_step"


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    final_row = next((row for row in rows if row.get("check_name") == "final_readiness_status"), {})
    status_counts = Counter(str(row.get("check_status", "")) for row in rows)
    blocker_rows = [row for row in rows if row.get("severity") == "blocked"]
    key_blockers = ", ".join(str(row.get("check_name", "")) for row in blocker_rows[:5]) or "none"
    alpaca_called = any(str(row.get("alpaca_called", "")).lower() == "true" for row in rows)
    return [
        "Alpaca paper readiness report complete. Report/preflight only; execution_approved=False; scheduling_approved=False.",
        f"final_readiness_status: {final_row.get('check_status', 'unavailable')}",
        f"check_counts: {format_counts(status_counts)}",
        f"key_blockers: {key_blockers}",
        f"recommended_next_step: {final_row.get('recommended_next_step', 'unavailable')}",
        f"alpaca_called: {str(alpaca_called).lower()}",
        "execution_approved=false",
        "scheduling_approved=false",
        f"Saved readiness report to {output_path}",
        "Warning: this report does not submit, cancel, replace, or create orders and does not approve paper execution.",
    ]


def redact_account_status(status: str) -> str:
    allowed = {"ACTIVE", "INACTIVE", "SUBMISSION_FAILED", "ONBOARDING", "APPROVAL_PENDING"}
    upper = status.upper()
    return upper if upper in allowed else "redacted_or_unknown"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_csv(path: Path, limit: int = 100) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = []
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
