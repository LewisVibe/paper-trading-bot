"""Live read-only preflight for a future manual paper-order smoke test.

Default mode is static and does not call Alpaca. Confirmed mode may perform
read-only paper account/clock/asset/open-order checks, but it never creates,
submits, cancels, replaces, or previews executable orders.
"""

from __future__ import annotations

import csv
import socket
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("data/paper_order_smoke_test_live_preflight.csv")

READY_LABEL = "live_preflight_ready_for_manual_confirmation"
WAIT_LABEL = "live_preflight_wait_for_market_open"
MANUAL_REVIEW_LABEL = "live_preflight_manual_review_required"
BLOCKED_LABEL = "live_preflight_blocked"

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "ticker",
    "side",
    "quantity",
    "market_status",
    "evidence_source",
    "details",
    "blocker",
    "recommended_next_step",
    "alpaca_called",
    "order_execution_approved",
    "execution_approved",
    "scheduling_approved",
    "run_command_now",
    "live_preflight_status",
]


@dataclass
class PaperOrderSmokeTestLivePreflightResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_order_smoke_test_live_preflight(
    ticker: str,
    side: str,
    quantity: str | int | float | Decimal,
    confirm_readonly_alpaca_check: bool = False,
    root_dir: Path | str = ".",
) -> PaperOrderSmokeTestLivePreflightResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    normalised = normalise_inputs(ticker, side, quantity)
    market_status = "not_checked"
    rows = build_static_rows(root, created_at, normalised, confirm_readonly_alpaca_check, market_status)
    if confirm_readonly_alpaca_check and not has_blocker(rows):
        readonly_rows = build_confirmed_readonly_rows(root, created_at, normalised)
        rows.extend(readonly_rows)
        market_status = latest_market_status(readonly_rows)
        for row in rows:
            if row.get("market_status") == "not_checked":
                row["market_status"] = market_status
    final_status = choose_final_status(rows, confirm_readonly_alpaca_check, market_status)
    rows.append(
        preflight_row(
            created_at,
            "final_live_preflight_status",
            final_status,
            "blocked" if final_status == BLOCKED_LABEL else ("warning" if final_status != READY_LABEL else "info"),
            normalised["ticker"],
            normalised["side"],
            normalised["quantity"],
            market_status,
            "preflight rows",
            final_details(final_status, rows),
            final_status == BLOCKED_LABEL,
            final_next_step(final_status),
            any_alpaca_called(rows),
            final_status,
        )
    )
    output_path = root / OUTPUT_PATH
    write_rows(output_path, rows)
    return PaperOrderSmokeTestLivePreflightResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows),
    )


def build_static_rows(
    root: Path,
    created_at: str,
    inputs: dict[str, str],
    confirm_readonly_alpaca_check: bool,
    market_status: str,
) -> list[dict[str, Any]]:
    alpaca_readiness = read_csv(root / "data" / "alpaca_paper_readiness_report.csv", limit=80)
    smoke_pack = read_csv(root / "data" / "paper_order_smoke_test_readiness_pack.csv", limit=80)
    return [
        input_validation_row(created_at, inputs, market_status),
        readiness_context_row(created_at, inputs, market_status, "alpaca_paper_readiness_context", "data/alpaca_paper_readiness_report.csv", alpaca_readiness, "final_readiness_status"),
        readiness_context_row(created_at, inputs, market_status, "smoke_test_readiness_pack_context", "data/paper_order_smoke_test_readiness_pack.csv", smoke_pack, "final_smoke_test_discussion_status"),
        confirmation_boundary_row(created_at, inputs, confirm_readonly_alpaca_check, market_status),
        static_order_boundary_row(created_at, inputs, market_status),
    ]


def build_confirmed_readonly_rows(root: Path, created_at: str, inputs: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        from trading_bot.config import load_config

        config = load_config(root / "config.json", force_dry_run=True)
    except Exception as exc:  # noqa: BLE001 - safe report capture
        return [
            preflight_row(
                created_at,
                "readonly_config_load",
                "blocked_config_load_failed",
                "blocked",
                inputs["ticker"],
                inputs["side"],
                inputs["quantity"],
                "unknown",
                "local config loader",
                f"Config load failed safely without printing contents: {type(exc).__name__}.",
                True,
                "fix_local_paper_config_before_live_preflight",
                False,
                BLOCKED_LABEL,
            )
        ]

    paper = bool(getattr(config, "alpaca_paper", False))
    key_available = bool(getattr(config, "alpaca_api_key", ""))
    secret_available = bool(getattr(config, "alpaca_secret_key", ""))
    rows.extend(
        [
            preflight_row(
                created_at,
                "readonly_config_load",
                "pass",
                "info",
                inputs["ticker"],
                inputs["side"],
                inputs["quantity"],
                "unknown",
                "local config loader",
                "Config loaded successfully. Contents and credential values were not printed.",
                False,
                "continue_readonly_checks",
                False,
                MANUAL_REVIEW_LABEL,
            ),
            preflight_row(
                created_at,
                "readonly_paper_mode",
                "pass" if paper else "blocked_not_paper_mode",
                "info" if paper else "blocked",
                inputs["ticker"],
                inputs["side"],
                inputs["quantity"],
                "unknown",
                "config object redacted",
                "alpaca.paper is true." if paper else "alpaca.paper is not true; live trading is out of scope.",
                not paper,
                "continue_readonly_checks" if paper else "restore_paper_mode_before_live_preflight",
                False,
                MANUAL_REVIEW_LABEL if paper else BLOCKED_LABEL,
            ),
            preflight_row(
                created_at,
                "readonly_credentials_present",
                "pass" if key_available and secret_available else "blocked_missing_credentials",
                "info" if key_available and secret_available else "blocked",
                inputs["ticker"],
                inputs["side"],
                inputs["quantity"],
                "unknown",
                "config object redacted",
                f"api_key_present={key_available}; secret_key_present={secret_available}; values redacted.",
                not (key_available and secret_available),
                "continue_readonly_checks" if key_available and secret_available else "configure_paper_credentials_without_exposing_values",
                False,
                MANUAL_REVIEW_LABEL if key_available and secret_available else BLOCKED_LABEL,
            ),
        ]
    )
    if not paper or not key_available or not secret_available:
        return rows

    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        client = TradingClient(getattr(config, "alpaca_api_key"), getattr(config, "alpaca_secret_key"), paper=True)
        rows.append(
            preflight_row(
                created_at,
                "readonly_trading_client_created",
                "pass",
                "info",
                inputs["ticker"],
                inputs["side"],
                inputs["quantity"],
                "unknown",
                "Alpaca TradingClient paper mode",
                "TradingClient created with paper=True. Sensitive identifiers were not printed.",
                False,
                "continue_readonly_checks",
                True,
                MANUAL_REVIEW_LABEL,
            )
        )
        account = client.get_account()
        rows.append(account_status_row(created_at, inputs, account))
        clock = client.get_clock()
        rows.append(clock_status_row(created_at, inputs, clock))
        rows.append(asset_status_row(created_at, inputs, client))
        request = GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[inputs["ticker"]])
        open_orders = list(client.get_orders(filter=request))
        rows.append(open_orders_row(created_at, inputs, len(open_orders), "open" if bool(getattr(clock, "is_open", False)) else "closed"))
    except Exception as exc:  # noqa: BLE001 - report-only failure capture
        error_type = classify_readonly_alpaca_exception(exc)
        rows.append(
            preflight_row(
                created_at,
                "readonly_alpaca_check",
                "manual_review_required_readonly_check_failed",
                "warning",
                inputs["ticker"],
                inputs["side"],
                inputs["quantity"],
                "unknown",
                "Alpaca read-only endpoints",
                (
                    "Read-only check failed safely: "
                    f"error_type={error_type}; exception_type={type(exc).__name__}. "
                    "Sensitive values were not printed."
                ),
                False,
                "manual_review_readonly_failure_before_any_smoke_test",
                True,
                MANUAL_REVIEW_LABEL,
            )
        )
    return rows


def input_validation_row(created_at: str, inputs: dict[str, str], market_status: str) -> dict[str, Any]:
    errors = []
    if not inputs["ticker"]:
        errors.append("ticker_missing")
    if inputs["side"] not in {"buy", "sell"}:
        errors.append("side_must_be_buy_or_sell")
    if not quantity_positive(inputs["quantity"]):
        errors.append("quantity_must_be_positive")
    ok = not errors
    return preflight_row(
        created_at,
        "input_validation",
        "pass" if ok else "blocked_invalid_input",
        "info" if ok else "blocked",
        inputs["ticker"],
        inputs["side"],
        inputs["quantity"],
        market_status,
        "CLI inputs",
        "Inputs are valid and manual-review-only." if ok else "Invalid inputs: " + ", ".join(errors),
        not ok,
        "continue_preflight" if ok else "fix_ticker_side_quantity_before_preflight",
        False,
        MANUAL_REVIEW_LABEL if ok else BLOCKED_LABEL,
    )


def readiness_context_row(
    created_at: str,
    inputs: dict[str, str],
    market_status: str,
    check_name: str,
    evidence_source: str,
    rows: list[dict[str, Any]],
    final_check_name: str,
) -> dict[str, Any]:
    if not rows:
        return preflight_row(
            created_at,
            check_name,
            "manual_review_required_missing_saved_report",
            "warning",
            inputs["ticker"],
            inputs["side"],
            inputs["quantity"],
            market_status,
            evidence_source,
            "Saved report is missing or empty. Full CSV contents were not printed.",
            False,
            "run_or_review_saved_readiness_report_before_live_preflight",
            False,
            MANUAL_REVIEW_LABEL,
        )
    final_status = final_status_from_rows(rows, final_check_name)
    blocking = any_status_contains(rows, ["blocked"]) or "blocked" in final_status
    return preflight_row(
        created_at,
        check_name,
        "manual_review_required_saved_blockers" if blocking else "saved_context_present",
        "warning" if blocking else "info",
        inputs["ticker"],
        inputs["side"],
        inputs["quantity"],
        market_status,
        evidence_source,
        f"saved_final_status={final_status or 'unavailable'}; saved report summarised without dumping full CSV contents.",
        False,
        "review_saved_blockers_before_manual_confirmation" if blocking else "continue_preflight",
        False,
        MANUAL_REVIEW_LABEL,
    )


def confirmation_boundary_row(
    created_at: str,
    inputs: dict[str, str],
    confirmed: bool,
    market_status: str,
) -> dict[str, Any]:
    return preflight_row(
        created_at,
        "readonly_alpaca_confirmation_boundary",
        "confirmed_readonly_check_allowed" if confirmed else "not_run_confirmation_required",
        "info" if confirmed else "warning",
        inputs["ticker"],
        inputs["side"],
        inputs["quantity"],
        market_status,
        "CLI confirmation flag",
        "Read-only Alpaca checks are explicitly confirmed." if confirmed else "Read-only Alpaca checks were not run because --confirm-readonly-alpaca-check was not provided.",
        False,
        "run_confirmed_readonly_preflight_only_after_review" if not confirmed else "continue_readonly_preflight",
        False,
        MANUAL_REVIEW_LABEL,
    )


def static_order_boundary_row(created_at: str, inputs: dict[str, str], market_status: str) -> dict[str, Any]:
    return preflight_row(
        created_at,
        "static_order_execution_boundary",
        "report_only_no_order_execution",
        "info",
        inputs["ticker"],
        inputs["side"],
        inputs["quantity"],
        market_status,
        "policy boundary",
        "This command does not run the paper-order smoke test and does not create, submit, cancel, replace, or preview executable orders.",
        False,
        "manual_confirmation_required_before_any_separate_smoke_test",
        False,
        MANUAL_REVIEW_LABEL,
    )


def account_status_row(created_at: str, inputs: dict[str, str], account: Any) -> dict[str, Any]:
    status = redact_account_status(str(getattr(account, "status", "unknown")))
    account_blocked = bool(getattr(account, "account_blocked", False))
    trading_blocked = bool(getattr(account, "trading_blocked", False))
    blocked = account_blocked or trading_blocked
    return preflight_row(
        created_at,
        "readonly_account_status",
        "manual_review_required_account_blocked" if blocked else "pass",
        "blocked" if blocked else "info",
        inputs["ticker"],
        inputs["side"],
        inputs["quantity"],
        "unknown",
        "Alpaca read-only account endpoint",
        f"status={status}; account_blocked={account_blocked}; trading_blocked={trading_blocked}; identifiers redacted.",
        blocked,
        "manual_review_account_flags" if blocked else "continue_readonly_checks",
        True,
        BLOCKED_LABEL if blocked else MANUAL_REVIEW_LABEL,
    )


def clock_status_row(created_at: str, inputs: dict[str, str], clock: Any) -> dict[str, Any]:
    is_open = bool(getattr(clock, "is_open", False))
    market_status = "open" if is_open else "closed"
    return preflight_row(
        created_at,
        "readonly_market_clock",
        "market_open" if is_open else "market_closed_wait",
        "info" if is_open else "warning",
        inputs["ticker"],
        inputs["side"],
        inputs["quantity"],
        market_status,
        "Alpaca read-only clock endpoint",
        f"market_status={market_status}. Market orders should not be discussed for immediate use while market is closed.",
        False,
        "manual_confirmation_discussion_can_continue" if is_open else "wait_for_market_open_before_discussing_market_order_smoke_test",
        True,
        READY_LABEL if is_open else WAIT_LABEL,
    )


def asset_status_row(created_at: str, inputs: dict[str, str], client: Any) -> dict[str, Any]:
    try:
        asset = client.get_asset(inputs["ticker"])
        tradable = bool(getattr(asset, "tradable", False))
        status = str(getattr(asset, "status", "unknown"))
        blocked = not tradable
        return preflight_row(
            created_at,
            "readonly_asset_metadata",
            "pass" if not blocked else "blocked_asset_not_tradable",
            "info" if not blocked else "blocked",
            inputs["ticker"],
            inputs["side"],
            inputs["quantity"],
            "unknown",
            "Alpaca read-only asset endpoint",
            f"asset_status={status}; tradable={tradable}; identifiers not printed.",
            blocked,
            "continue_readonly_checks" if not blocked else "choose_tradable_ticker_before_manual_confirmation",
            True,
            MANUAL_REVIEW_LABEL if not blocked else BLOCKED_LABEL,
        )
    except Exception as exc:  # noqa: BLE001
        return preflight_row(
            created_at,
            "readonly_asset_metadata",
            "manual_review_required_asset_check_failed",
            "warning",
            inputs["ticker"],
            inputs["side"],
            inputs["quantity"],
            "unknown",
            "Alpaca read-only asset endpoint",
            f"Asset metadata check failed safely: {type(exc).__name__}.",
            False,
            "manual_review_asset_check_before_any_smoke_test",
            True,
            MANUAL_REVIEW_LABEL,
        )


def open_orders_row(created_at: str, inputs: dict[str, str], count: int, market_status: str) -> dict[str, Any]:
    return preflight_row(
        created_at,
        "readonly_open_orders_for_ticker",
        "manual_review_required_open_orders_exist" if count else "pass",
        "warning" if count else "info",
        inputs["ticker"],
        inputs["side"],
        inputs["quantity"],
        market_status,
        "Alpaca read-only open orders endpoint",
        f"open_order_count_for_ticker={count}; order details were not printed.",
        False,
        "review_existing_open_orders_before_any_smoke_test" if count else "continue_manual_confirmation_discussion",
        True,
        MANUAL_REVIEW_LABEL,
    )


def classify_readonly_alpaca_exception(exc: BaseException) -> str:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "timeout" in name or "timeout" in text:
        return "connection_timeout"
    if isinstance(exc, socket.gaierror) or "name resolution" in text or "getaddrinfo" in text:
        return "dns_resolution_failed"
    if "connecterror" in name or "connectionerror" in name or "connection refused" in text:
        return "tcp_connect_failed"
    if "unauthorized" in text or "forbidden" in text or "401" in text or "403" in text:
        return "auth_or_api_rejected"
    if "api" in name or "pydantic" in name or "validation" in name:
        return "api_or_response_parsing_failed"
    return "readonly_alpaca_check_failed"


def preflight_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    ticker: str,
    side: str,
    quantity: str,
    market_status: str,
    evidence_source: str,
    details: str,
    blocker: bool,
    recommended_next_step: str,
    alpaca_called: bool,
    live_preflight_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "market_status": market_status,
        "evidence_source": evidence_source,
        "details": details,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        "alpaca_called": alpaca_called,
        "order_execution_approved": False,
        "execution_approved": False,
        "scheduling_approved": False,
        "run_command_now": False,
        "live_preflight_status": live_preflight_status,
    }


def choose_final_status(rows: list[dict[str, Any]], confirmed: bool, market_status: str) -> str:
    if has_blocker(rows):
        return BLOCKED_LABEL
    if confirmed and market_status == "open" and not any(row.get("severity") == "warning" for row in rows):
        return READY_LABEL
    if confirmed and market_status == "closed":
        return WAIT_LABEL
    return MANUAL_REVIEW_LABEL


def final_details(final_status: str, rows: list[dict[str, Any]]) -> str:
    blockers = [row for row in rows if row.get("severity") == "blocked" or truthy(row.get("blocker"))]
    warnings = [row for row in rows if row.get("severity") == "warning"]
    key_items = blockers[:5] if blockers else warnings[:5]
    key_names = ", ".join(str(row.get("check_name", "")) for row in key_items) or "none"
    return f"final_status={final_status}; blocker_count={len(blockers)}; manual_review_count={len(warnings)}; key_items={key_names}."


def final_next_step(final_status: str) -> str:
    if final_status == READY_LABEL:
        return "manual_confirmation_discussion_can_continue_but_order_execution_is_not_approved"
    if final_status == WAIT_LABEL:
        return "wait_for_market_open_before_any_market_order_smoke_test_discussion"
    if final_status == BLOCKED_LABEL:
        return "resolve_blockers_before_live_preflight_or_smoke_test_discussion"
    return "manual_review_required_before_any_explicit_confirmation"


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    final_row = next((row for row in rows if row.get("check_name") == "final_live_preflight_status"), {})
    market_status = str(final_row.get("market_status") or "unknown")
    ticker = str(final_row.get("ticker") or "")
    side = str(final_row.get("side") or "")
    quantity = str(final_row.get("quantity") or "")
    blockers = [row for row in rows if row.get("severity") == "blocked" or truthy(row.get("blocker"))]
    warnings = [row for row in rows if row.get("severity") == "warning"]
    key_items = blockers[:5] if blockers else warnings[:5]
    key_names = ", ".join(str(row.get("check_name", "")) for row in key_items) or "none"
    return [
        "Paper-order smoke-test live preflight complete. Read-only/report-only; no order execution approved.",
        f"final_live_preflight_status: {final_row.get('check_status', 'unavailable')}",
        f"market_status: {market_status}",
        f"proposed_manual_test: ticker={ticker}; side={side}; quantity={quantity}; manual_review_only=true",
        f"key_blockers_or_manual_review_items: {key_names}",
        f"recommended_next_step: {final_row.get('recommended_next_step', 'unavailable')}",
        f"alpaca_called: {str(any_alpaca_called(rows)).lower()}",
        "order_execution_approved=false",
        "execution_approved=false",
        "scheduling_approved=false",
        "run_command_now=false",
        f"Saved live preflight to {output_path}",
        "Warning: this summary intentionally does not print a paper-order command.",
    ]


def normalise_inputs(ticker: str, side: str, quantity: str | int | float | Decimal) -> dict[str, str]:
    return {
        "ticker": str(ticker or "").strip().upper(),
        "side": str(side or "").strip().lower(),
        "quantity": str(quantity or "").strip(),
    }


def quantity_positive(value: str) -> bool:
    try:
        return Decimal(value) > 0
    except (InvalidOperation, ValueError):
        return False


def latest_market_status(rows: list[dict[str, Any]]) -> str:
    for row in reversed(rows):
        status = str(row.get("market_status") or "")
        if status in {"open", "closed"}:
            return status
    return "unknown"


def has_blocker(rows: list[dict[str, Any]]) -> bool:
    return any(row.get("severity") == "blocked" or truthy(row.get("blocker")) for row in rows)


def any_alpaca_called(rows: list[dict[str, Any]]) -> bool:
    return any(truthy(row.get("alpaca_called")) for row in rows)


def final_status_from_rows(rows: list[dict[str, Any]], final_check_name: str) -> str:
    final = next((row for row in rows if row.get("check_name") == final_check_name), {})
    return str(final.get("check_status") or "")


def any_status_contains(rows: list[dict[str, Any]], needles: list[str]) -> bool:
    lower_needles = [needle.lower() for needle in needles]
    for row in rows:
        for key, value in row.items():
            if "status" not in key.lower() and "severity" not in key.lower():
                continue
            text = str(value).lower()
            if any(needle in text for needle in lower_needles):
                return True
    return False


def redact_account_status(status: str) -> str:
    allowed = {"ACTIVE", "INACTIVE", "SUBMISSION_FAILED", "ONBOARDING", "APPROVAL_PENDING"}
    upper = status.upper()
    return upper if upper in allowed else "redacted_or_unknown"


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


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


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
