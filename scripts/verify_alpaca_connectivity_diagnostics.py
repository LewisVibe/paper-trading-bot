from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "alpaca_connectivity_diagnostics.py"
LIVE_PREFLIGHT = ROOT / "trading_bot" / "research" / "paper_order_smoke_test_live_preflight.py"
COMMAND = "--alpaca-connectivity-diagnostics"
SHOW_COMMAND = "--show-alpaca-connectivity-diagnostics"
OUTPUTS = [
    "data/alpaca_connectivity_diagnostics.csv",
    "data/alpaca_connectivity_diagnostics_summary.csv",
    "data/alpaca_connectivity_diagnostics_blockers.csv",
]

REQUIRED_SCHEMA = [
    "endpoint",
    "endpoint_role",
    "dns_status",
    "tcp_443_status",
    "error_type",
    "diagnostic_status",
    "execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
]

FORBIDDEN_MODULE_PATTERNS = [
    "TradingClient",
    "load_config(",
    "config.json",
    "submit_order",
    "cancel_order",
    "replace_order",
    "MarketOrderRequest",
    "LimitOrderRequest",
    "StopOrderRequest",
    "get_account(",
    "get_clock(",
    "get_asset(",
    "get_open_orders",
    "get_alpaca_positions",
    "get_position",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    preflight_source = read_text(LIVE_PREFLIGHT)

    verify_command_registered(bot_source, failures)
    verify_module_source(module_source, failures)
    verify_live_preflight_diagnostics(preflight_source, failures)
    verify_outputs_ignored(failures)
    verify_schema_and_false_flags(failures)

    if failures:
        print("Alpaca connectivity diagnostics verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Alpaca connectivity diagnostics verification passed.")
    print("Verified early commands, ignored outputs, socket-only diagnostics, clearer live-preflight error classification, and false execution/scheduling approvals.")
    return 0


def verify_command_registered(source: str, failures: list[str]) -> None:
    for token in [COMMAND, SHOW_COMMAND, "generate_alpaca_connectivity_diagnostics", "show_alpaca_connectivity_diagnostics"]:
        if token not in source:
            failures.append(f"bot.py missing command/wiring token: {token}")
    early_index = source.find(f'["{COMMAND}"]')
    broker_import_index = source.find("from alpaca.trading.client import TradingClient")
    if early_index == -1:
        failures.append("missing exact early route for connectivity diagnostics")
    elif broker_import_index != -1 and early_index > broker_import_index:
        failures.append("connectivity diagnostics must route before top-level Alpaca imports")


def verify_module_source(source: str, failures: list[str]) -> None:
    for token in [
        "socket.getaddrinfo",
        "socket.create_connection",
        "paper-api.alpaca.markets",
        "api.alpaca.markets",
        "github.com",
        "google.com",
        "pypi.org",
        "alpaca_api_unreachable_but_general_https_ok",
        "general_https_unreachable",
        "dns_failed",
        "alpaca_api_reachable",
        "diagnostics_manual_review_required",
        *REQUIRED_SCHEMA,
    ]:
        if token not in source:
            failures.append(f"diagnostics module missing required token: {token}")
    for pattern in FORBIDDEN_MODULE_PATTERNS:
        if pattern in source:
            failures.append(f"diagnostics module must not contain forbidden pattern: {pattern}")


def verify_live_preflight_diagnostics(source: str, failures: list[str]) -> None:
    for token in [
        "classify_readonly_alpaca_exception",
        "connection_timeout",
        "dns_resolution_failed",
        "tcp_connect_failed",
        "auth_or_api_rejected",
        "api_or_response_parsing_failed",
        "market_status",
        "unknown",
        "run_command_now",
        "execution_approved",
        "scheduling_approved",
    ]:
        if token not in source:
            failures.append(f"live preflight missing diagnostic/safety token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(["git", "check-ignore", output], cwd=ROOT, text=True, capture_output=True, timeout=10)
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_schema_and_false_flags(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        env_code = (
            "from trading_bot.research.alpaca_connectivity_diagnostics import "
            "REPORT_COLUMNS, generate_alpaca_connectivity_diagnostics; "
            "import trading_bot.research.alpaca_connectivity_diagnostics as m; "
            "m.ENDPOINTS=[('localhost','general_https_control')]; "
            "m.diagnose_endpoint=lambda created_at, endpoint, role, timeout_seconds: "
            "m.report_row(created_at, endpoint, role, '127.0.0.1', 'pass', 'failed', 'tcp_connect_failed', timeout_seconds, 'test'); "
            f"assert all(c in REPORT_COLUMNS for c in {REQUIRED_SCHEMA!r}); "
            f"r=generate_alpaca_connectivity_diagnostics(r'{tmp}', timeout_seconds=0.01); "
            "print(r.output_path)"
        )
        completed = subprocess.run(
            [sys.executable, "-c", env_code],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if completed.returncode != 0:
            failures.append(f"deterministic diagnostics generation failed: {completed.stderr.strip()}")
            return
        output = Path(tmp) / OUTPUTS[0]
        if not output.exists():
            failures.append("deterministic diagnostics did not write expected report")
            return
        with output.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            failures.append("deterministic diagnostics report wrote no rows")
            return
        for column in REQUIRED_SCHEMA:
            if column not in rows[0]:
                failures.append(f"report schema missing column: {column}")
        for flag in ["execution_approved", "scheduling_approved", "orders_created", "orders_submitted", "orders_cancelled"]:
            if not all(str(row.get(flag, "")).lower() == "false" for row in rows):
                failures.append(f"{flag} must remain false for every diagnostics row")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
