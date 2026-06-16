"""Unauthenticated Alpaca endpoint connectivity diagnostics.

This report uses DNS and raw TCP 443 socket checks only. It does not load
config, use Alpaca credentials, call authenticated Alpaca APIs, read positions,
submit orders, write trade logs, send alerts, or approve execution.
"""

from __future__ import annotations

import csv
import socket
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_PATH = Path("data/alpaca_connectivity_diagnostics.csv")
SUMMARY_PATH = Path("data/alpaca_connectivity_diagnostics_summary.csv")
BLOCKERS_PATH = Path("data/alpaca_connectivity_diagnostics_blockers.csv")
TIMEOUT_SECONDS = 3.0

ENDPOINTS = [
    ("paper-api.alpaca.markets", "alpaca_paper_api"),
    ("api.alpaca.markets", "alpaca_live_api"),
    ("alpaca.markets", "alpaca_public_site"),
    ("github.com", "general_https_control"),
    ("google.com", "general_https_control"),
    ("pypi.org", "general_https_control"),
]

REPORT_COLUMNS = [
    "created_at",
    "endpoint",
    "endpoint_role",
    "resolved_ip",
    "dns_status",
    "tcp_443_status",
    "error_type",
    "timeout_seconds",
    "diagnostic_status",
    "diagnostic_conclusion",
    "details",
    "recommended_next_step",
    "execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "positions_read",
    "alpaca_authenticated_api_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    "execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
]


@dataclass
class AlpacaConnectivityDiagnosticsResult:
    output_path: Path
    summary_path: Path
    blockers_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_alpaca_connectivity_diagnostics(
    root_dir: Path | str = ".",
    timeout_seconds: float = TIMEOUT_SECONDS,
) -> AlpacaConnectivityDiagnosticsResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = [diagnose_endpoint(created_at, endpoint, role, timeout_seconds) for endpoint, role in ENDPOINTS]
    conclusion = choose_conclusion(rows)
    summary_rows = build_summary_rows(rows, conclusion)
    blocker_rows = build_blocker_rows(rows, conclusion)

    output_path = root / REPORT_PATH
    summary_path = root / SUMMARY_PATH
    blockers_path = root / BLOCKERS_PATH
    write_rows(output_path, REPORT_COLUMNS, rows)
    write_rows(summary_path, SUMMARY_COLUMNS, summary_rows)
    write_rows(blockers_path, BLOCKER_COLUMNS, blocker_rows)
    return AlpacaConnectivityDiagnosticsResult(
        output_path=output_path,
        summary_path=summary_path,
        blockers_path=blockers_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows, conclusion),
    )


def show_alpaca_connectivity_diagnostics(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / SUMMARY_PATH
    report_path = root / REPORT_PATH
    if not summary_path.exists():
        return 1, [
            "Alpaca connectivity diagnostics summary is missing.",
            "Run `python bot.py --alpaca-connectivity-diagnostics` first.",
            "execution_approved=false",
            "scheduling_approved=false",
        ]
    summary = read_csv(summary_path)
    report = read_csv(report_path)
    value = {row.get("summary_name", ""): row.get("summary_value", "") for row in summary}
    rows = [
        "Alpaca connectivity diagnostics saved summary.",
        f"diagnostic_conclusion: {value.get('diagnostic_conclusion', 'unavailable')}",
        f"alpaca_api_tcp_status: {value.get('alpaca_api_tcp_status', 'unavailable')}",
        f"general_https_tcp_status: {value.get('general_https_tcp_status', 'unavailable')}",
        f"endpoint_status_counts: {value.get('endpoint_status_counts', 'unavailable')}",
        f"saved_report: {report_path}",
        "execution_approved=false",
        "scheduling_approved=false",
        "Warning: this display is unauthenticated diagnostics only and does not approve orders.",
    ]
    failed = [row for row in report if row.get("tcp_443_status") != "pass"]
    if failed:
        rows.append("failed_or_warning_endpoints:")
        for row in failed[:8]:
            rows.append(
                "- "
                f"{row.get('endpoint')} "
                f"dns={row.get('dns_status')} "
                f"tcp={row.get('tcp_443_status')} "
                f"error={row.get('error_type')}"
            )
    return 0, rows


def diagnose_endpoint(created_at: str, endpoint: str, role: str, timeout_seconds: float) -> dict[str, Any]:
    resolved_ip = ""
    dns_status = "pass"
    tcp_status = "not_checked"
    error_type = "none"
    details = ""

    try:
        infos = socket.getaddrinfo(endpoint, 443, type=socket.SOCK_STREAM)
        if infos:
            resolved_ip = str(infos[0][4][0])
    except socket.gaierror as exc:
        dns_status = "dns_resolution_failed"
        tcp_status = "not_checked_dns_failed"
        error_type = "dns_resolution_failed"
        details = f"DNS resolution failed safely: {type(exc).__name__}."
        return report_row(created_at, endpoint, role, resolved_ip, dns_status, tcp_status, error_type, timeout_seconds, details)
    except Exception as exc:  # noqa: BLE001 - diagnostics capture only
        dns_status = "dns_resolution_uncertain"
        tcp_status = "not_checked_dns_uncertain"
        error_type = classify_socket_exception(exc)
        details = f"DNS resolution returned an unexpected safe diagnostics error: {type(exc).__name__}."
        return report_row(created_at, endpoint, role, resolved_ip, dns_status, tcp_status, error_type, timeout_seconds, details)

    try:
        with socket.create_connection((endpoint, 443), timeout=timeout_seconds):
            tcp_status = "pass"
            details = "TCP 443 connection succeeded. No HTTP request or authenticated API call was made."
    except Exception as exc:  # noqa: BLE001 - diagnostics capture only
        tcp_status = "failed"
        error_type = classify_socket_exception(exc)
        details = f"TCP 443 connection failed safely: {type(exc).__name__}."

    return report_row(created_at, endpoint, role, resolved_ip, dns_status, tcp_status, error_type, timeout_seconds, details)


def classify_socket_exception(exc: BaseException) -> str:
    if isinstance(exc, TimeoutError | socket.timeout):
        return "connection_timeout"
    if isinstance(exc, socket.gaierror):
        return "dns_resolution_failed"
    if isinstance(exc, ConnectionRefusedError):
        return "tcp_connect_refused"
    if isinstance(exc, OSError):
        return "tcp_connect_failed"
    return type(exc).__name__


def report_row(
    created_at: str,
    endpoint: str,
    role: str,
    resolved_ip: str,
    dns_status: str,
    tcp_status: str,
    error_type: str,
    timeout_seconds: float,
    details: str,
) -> dict[str, Any]:
    diagnostic_status = "pass" if dns_status == "pass" and tcp_status == "pass" else "manual_review_required"
    return {
        "created_at": created_at,
        "endpoint": endpoint,
        "endpoint_role": role,
        "resolved_ip": resolved_ip,
        "dns_status": dns_status,
        "tcp_443_status": tcp_status,
        "error_type": error_type,
        "timeout_seconds": timeout_seconds,
        "diagnostic_status": diagnostic_status,
        "diagnostic_conclusion": "endpoint_reachable" if diagnostic_status == "pass" else "endpoint_connectivity_manual_review_required",
        "details": details,
        "recommended_next_step": "none" if diagnostic_status == "pass" else "review_vps_network_dns_firewall_or_provider_routing",
        **safety_flags(),
    }


def choose_conclusion(rows: list[dict[str, Any]]) -> str:
    alpaca_api = [row for row in rows if row.get("endpoint_role") in {"alpaca_paper_api", "alpaca_live_api"}]
    general = [row for row in rows if row.get("endpoint_role") == "general_https_control"]
    alpaca_ok = all(row.get("tcp_443_status") == "pass" for row in alpaca_api)
    general_ok = any(row.get("tcp_443_status") == "pass" for row in general)
    alpaca_dns_failed = any(row.get("dns_status") == "dns_resolution_failed" for row in alpaca_api)
    if alpaca_ok:
        return "alpaca_api_reachable"
    if alpaca_dns_failed:
        return "dns_failed"
    if general_ok:
        return "alpaca_api_unreachable_but_general_https_ok"
    if general:
        return "general_https_unreachable"
    return "diagnostics_manual_review_required"


def build_summary_rows(rows: list[dict[str, Any]], conclusion: str) -> list[dict[str, Any]]:
    status_counts = Counter(str(row.get("diagnostic_status", "")) for row in rows)
    alpaca_api = [row for row in rows if row.get("endpoint_role") in {"alpaca_paper_api", "alpaca_live_api"}]
    general = [row for row in rows if row.get("endpoint_role") == "general_https_control"]
    return [
        summary_row("diagnostic_conclusion", conclusion, "Overall unauthenticated endpoint connectivity conclusion."),
        summary_row("alpaca_api_tcp_status", compact_endpoint_status(alpaca_api), "TCP 443 status for Alpaca API endpoints."),
        summary_row("general_https_tcp_status", compact_endpoint_status(general), "TCP 443 status for general HTTPS control endpoints."),
        summary_row("endpoint_status_counts", format_counts(status_counts), "Endpoint diagnostic status counts."),
        summary_row("execution_approved", "False", "Connectivity diagnostics do not approve execution."),
        summary_row("scheduling_approved", "False", "Connectivity diagnostics do not approve scheduling."),
    ]


def build_blocker_rows(rows: list[dict[str, Any]], conclusion: str) -> list[dict[str, Any]]:
    blockers = [
        blocker_row(
            row.get("endpoint", ""),
            row.get("diagnostic_status", ""),
            "warning",
            f"dns={row.get('dns_status')}; tcp_443={row.get('tcp_443_status')}; error={row.get('error_type')}",
            row.get("recommended_next_step", ""),
        )
        for row in rows
        if row.get("diagnostic_status") != "pass"
    ]
    if not blockers:
        blockers.append(blocker_row("none", "pass", "info", f"diagnostic_conclusion={conclusion}", "none"))
    return blockers


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]], conclusion: str) -> list[str]:
    status_counts = Counter(str(row.get("diagnostic_status", "")) for row in rows)
    failed = [row for row in rows if row.get("diagnostic_status") != "pass"]
    return [
        "Alpaca connectivity diagnostics complete. DNS/TCP only; no credentials or authenticated Alpaca APIs used.",
        f"diagnostic_conclusion: {conclusion}",
        f"endpoint_status_counts: {format_counts(status_counts)}",
        f"failed_or_warning_endpoints: {', '.join(str(row.get('endpoint')) for row in failed[:6]) or 'none'}",
        "execution_approved=false",
        "scheduling_approved=false",
        f"Saved diagnostics report to {output_path}",
        "Warning: this does not submit, cancel, create, replace orders, read positions, or approve paper execution.",
    ]


def safety_flags() -> dict[str, bool]:
    return {
        "execution_approved": False,
        "scheduling_approved": False,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
        "positions_read": False,
        "alpaca_authenticated_api_called": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **minimal_safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **minimal_safety_flags(),
    }


def minimal_safety_flags() -> dict[str, bool]:
    return {
        "execution_approved": False,
        "scheduling_approved": False,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
    }


def compact_endpoint_status(rows: list[dict[str, Any]]) -> str:
    return ", ".join(f"{row.get('endpoint')}={row.get('tcp_443_status')}" for row in rows) or "none"


def format_counts(counts: Counter[str]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def read_csv(path: Path) -> list[dict[str, str]]:
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
