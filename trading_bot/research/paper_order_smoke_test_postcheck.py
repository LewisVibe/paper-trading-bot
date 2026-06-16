"""Post-smoke-test read-only verification report.

Default mode is saved-data/static only. Confirmed mode may perform read-only
paper account/order/position checks, but it never creates, submits, cancels,
replaces, or modifies orders.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trading_bot.safety.manual_paper_smoke_test_gate import (
    evaluate_recent_manual_smoke_test_order_match,
)


OUTPUT_PATH = Path("data/paper_order_smoke_test_postcheck.csv")

REQUIRES_CONFIRM_LABEL = "postcheck_requires_confirmed_readonly_check"
FILLED_LABEL = "postcheck_order_observed_filled_manual_review"
OPEN_LABEL = "postcheck_order_observed_open_or_queued"
NOT_FILLED_LABEL = "postcheck_order_observed_not_filled_manual_review"
NO_MATCH_LABEL = "postcheck_no_matching_order_found"
MANUAL_REVIEW_LABEL = "postcheck_manual_review_required"
BLOCKED_LABEL = "postcheck_blocked"

REPORT_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "severity",
    "ticker",
    "side",
    "quantity",
    "evidence_source",
    "details",
    "matching_recent_order_status_summary",
    "recent_order_match_found",
    "recent_order_match_status",
    "recent_order_match_submitted_at_or_created_at",
    "recent_order_match_age_minutes",
    "recent_order_match_source",
    "recent_order_match_count",
    "recent_order_match_lookback_minutes",
    "open_order_summary",
    "position_summary",
    "blocker",
    "recommended_next_step",
    "alpaca_called",
    "order_execution_approved",
    "execution_approved",
    "scheduling_approved",
    "followup_order_approved",
    "final_postcheck_status",
]


@dataclass
class PaperOrderSmokeTestPostcheckResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_order_smoke_test_postcheck(
    ticker: str,
    side: str,
    quantity: str | int | float | Decimal,
    confirm_readonly_alpaca_check: bool = False,
    root_dir: Path | str = ".",
) -> PaperOrderSmokeTestPostcheckResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = normalise_inputs(ticker, side, quantity)
    rows = build_static_rows(root, created_at, inputs, confirm_readonly_alpaca_check)
    if confirm_readonly_alpaca_check and not has_blocker(rows):
        rows.extend(build_confirmed_readonly_rows(root, created_at, inputs))
    final_status = choose_final_status(rows, confirm_readonly_alpaca_check)
    rows.append(
        postcheck_row(
            created_at,
            "final_postcheck_status",
            final_status,
            "blocked" if final_status == BLOCKED_LABEL else ("warning" if final_status != FILLED_LABEL else "info"),
            inputs,
            "postcheck rows",
            final_details(final_status, rows),
            matching_summary(rows),
            open_summary(rows),
            position_summary(rows),
            final_status == BLOCKED_LABEL,
            final_next_step(final_status),
            any_alpaca_called(rows),
            final_status,
        )
    )
    output_path = root / OUTPUT_PATH
    write_rows(output_path, rows)
    return PaperOrderSmokeTestPostcheckResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary_lines(output_path, rows),
    )


def build_static_rows(
    root: Path,
    created_at: str,
    inputs: dict[str, str],
    confirm_readonly_alpaca_check: bool,
) -> list[dict[str, Any]]:
    live_preflight = read_csv(root / "data" / "paper_order_smoke_test_live_preflight.csv", limit=80)
    readiness_pack = read_csv(root / "data" / "paper_order_smoke_test_readiness_pack.csv", limit=80)
    alpaca_readiness = read_csv(root / "data" / "alpaca_paper_readiness_report.csv", limit=80)
    stock_readiness = read_csv(root / "data" / "stock_etf_paper_execution_readiness_report.csv", limit=80)
    return [
        input_validation_row(created_at, inputs),
        saved_context_row(created_at, inputs, "saved_live_preflight_context", "data/paper_order_smoke_test_live_preflight.csv", live_preflight, "final_live_preflight_status"),
        saved_context_row(created_at, inputs, "saved_smoke_test_readiness_pack_context", "data/paper_order_smoke_test_readiness_pack.csv", readiness_pack, "final_smoke_test_discussion_status"),
        saved_context_row(created_at, inputs, "saved_alpaca_paper_readiness_context", "data/alpaca_paper_readiness_report.csv", alpaca_readiness, "final_readiness_status"),
        saved_context_row(created_at, inputs, "saved_stock_etf_execution_readiness_context", "data/stock_etf_paper_execution_readiness_report.csv", stock_readiness, "final_paper_execution_discussion_status"),
        confirmation_boundary_row(created_at, inputs, confirm_readonly_alpaca_check),
        static_safety_boundary_row(created_at, inputs),
    ]


def build_confirmed_readonly_rows(root: Path, created_at: str, inputs: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        from trading_bot.config import load_config

        config = load_config(root / "config.json", force_dry_run=True)
    except Exception as exc:  # noqa: BLE001
        return [
            postcheck_row(
                created_at,
                "readonly_config_load",
                "blocked_config_load_failed",
                "blocked",
                inputs,
                "local config loader",
                f"Config load failed safely without printing contents: {type(exc).__name__}.",
                "",
                "",
                "",
                True,
                "fix_local_paper_config_before_readonly_postcheck",
                False,
                BLOCKED_LABEL,
            )
        ]
    paper = bool(getattr(config, "alpaca_paper", False))
    key_available = bool(getattr(config, "alpaca_api_key", ""))
    secret_available = bool(getattr(config, "alpaca_secret_key", ""))
    rows.extend(
        [
            postcheck_row(created_at, "readonly_config_load", "pass", "info", inputs, "local config loader", "Config loaded successfully. Contents and credential values were not printed.", "", "", "", False, "continue_readonly_postcheck", False, MANUAL_REVIEW_LABEL),
            postcheck_row(created_at, "readonly_paper_mode", "pass" if paper else "blocked_not_paper_mode", "info" if paper else "blocked", inputs, "config object redacted", "alpaca.paper is true." if paper else "alpaca.paper is not true; live trading is out of scope.", "", "", "", not paper, "continue_readonly_postcheck" if paper else "restore_paper_mode_before_postcheck", False, MANUAL_REVIEW_LABEL if paper else BLOCKED_LABEL),
            postcheck_row(created_at, "readonly_credentials_present", "pass" if key_available and secret_available else "blocked_missing_credentials", "info" if key_available and secret_available else "blocked", inputs, "config object redacted", f"api_key_present={key_available}; secret_key_present={secret_available}; values redacted.", "", "", "", not (key_available and secret_available), "continue_readonly_postcheck" if key_available and secret_available else "configure_paper_credentials_without_exposing_values", False, MANUAL_REVIEW_LABEL if key_available and secret_available else BLOCKED_LABEL),
        ]
    )
    if not paper or not key_available or not secret_available:
        return rows

    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        client = TradingClient(getattr(config, "alpaca_api_key"), getattr(config, "alpaca_secret_key"), paper=True)
        rows.append(postcheck_row(created_at, "readonly_trading_client_created", "pass", "info", inputs, "Alpaca TradingClient paper mode", "TradingClient created with paper=True. Sensitive identifiers were not printed.", "", "", "", False, "continue_readonly_postcheck", True, MANUAL_REVIEW_LABEL))
        account = client.get_account()
        rows.append(account_status_row(created_at, inputs, account))
        request = GetOrdersRequest(status=QueryOrderStatus.ALL, symbols=[inputs["ticker"]], limit=50)
        recent_orders = list(client.get_orders(filter=request))
        rows.append(recent_orders_row(created_at, inputs, recent_orders))
        open_request = GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[inputs["ticker"]], limit=50)
        open_orders = list(client.get_orders(filter=open_request))
        rows.append(open_orders_row(created_at, inputs, open_orders))
        rows.append(position_row(created_at, inputs, client))
    except Exception as exc:  # noqa: BLE001
        rows.append(
            postcheck_row(
                created_at,
                "readonly_alpaca_postcheck",
                "postcheck_manual_review_required",
                "warning",
                inputs,
                "Alpaca read-only endpoints",
                f"Read-only postcheck failed safely: {type(exc).__name__}. Sensitive values were not printed.",
                "",
                "",
                "",
                False,
                "manual_review_readonly_postcheck_failure",
                True,
                MANUAL_REVIEW_LABEL,
            )
        )
    return rows


def input_validation_row(created_at: str, inputs: dict[str, str]) -> dict[str, Any]:
    errors = []
    if not inputs["ticker"]:
        errors.append("ticker_missing")
    if inputs["side"] not in {"buy", "sell"}:
        errors.append("side_must_be_buy_or_sell")
    if not quantity_positive(inputs["quantity"]):
        errors.append("quantity_must_be_positive")
    ok = not errors
    return postcheck_row(
        created_at,
        "input_validation",
        "pass" if ok else "blocked_invalid_input",
        "info" if ok else "blocked",
        inputs,
        "CLI inputs",
        "Inputs are valid and manual-review context only." if ok else "Invalid inputs: " + ", ".join(errors),
        "",
        "",
        "",
        not ok,
        "continue_postcheck" if ok else "fix_ticker_side_quantity_before_postcheck",
        False,
        MANUAL_REVIEW_LABEL if ok else BLOCKED_LABEL,
    )


def saved_context_row(
    created_at: str,
    inputs: dict[str, str],
    check_name: str,
    evidence_source: str,
    rows: list[dict[str, Any]],
    final_check_name: str,
) -> dict[str, Any]:
    if not rows:
        return postcheck_row(
            created_at,
            check_name,
            "manual_review_required_missing_saved_report",
            "warning",
            inputs,
            evidence_source,
            "Saved report is missing or empty. Full CSV contents were not printed.",
            "",
            "",
            "",
            False,
            "review_or_regenerate_saved_context_if_needed",
            False,
            MANUAL_REVIEW_LABEL,
        )
    status = final_status_from_rows(rows, final_check_name)
    return postcheck_row(
        created_at,
        check_name,
        "saved_context_present",
        "warning" if "blocked" in status or "manual_review" in status or "wait" in status else "info",
        inputs,
        evidence_source,
        f"saved_final_status={status or 'unavailable'}; saved report summarised without dumping full CSV contents.",
        "",
        "",
        "",
        False,
        "do_not_treat_saved_context_as_execution_approval",
        False,
        MANUAL_REVIEW_LABEL,
    )


def confirmation_boundary_row(created_at: str, inputs: dict[str, str], confirmed: bool) -> dict[str, Any]:
    return postcheck_row(
        created_at,
        "readonly_alpaca_confirmation_boundary",
        "confirmed_readonly_postcheck_allowed" if confirmed else "postcheck_requires_confirmed_readonly_check",
        "info" if confirmed else "warning",
        inputs,
        "CLI confirmation flag",
        "Read-only Alpaca postcheck is explicitly confirmed." if confirmed else "Read-only Alpaca postcheck was not run because --confirm-readonly-alpaca-check was not provided.",
        "",
        "",
        "",
        False,
        "run_confirmed_readonly_postcheck_after_manual_smoke_test" if not confirmed else "continue_readonly_postcheck",
        False,
        MANUAL_REVIEW_LABEL,
    )


def static_safety_boundary_row(created_at: str, inputs: dict[str, str]) -> dict[str, Any]:
    return postcheck_row(
        created_at,
        "static_postcheck_safety_boundary",
        "report_only_no_followup_order_approval",
        "info",
        inputs,
        "policy boundary",
        "This command does not run a paper-order smoke test, create follow-up orders, write trade logs, send alerts, or approve execution.",
        "",
        "",
        "",
        False,
        "no_followup_order_without_manual_review",
        False,
        MANUAL_REVIEW_LABEL,
    )


def account_status_row(created_at: str, inputs: dict[str, str], account: Any) -> dict[str, Any]:
    account_blocked = bool(getattr(account, "account_blocked", False))
    trading_blocked = bool(getattr(account, "trading_blocked", False))
    status = redact_account_status(str(getattr(account, "status", "unknown")))
    blocked = account_blocked or trading_blocked
    return postcheck_row(
        created_at,
        "readonly_account_status",
        "postcheck_manual_review_required" if blocked else "pass",
        "blocked" if blocked else "info",
        inputs,
        "Alpaca read-only account endpoint",
        f"status={status}; account_blocked={account_blocked}; trading_blocked={trading_blocked}; identifiers redacted.",
        "",
        "",
        "",
        blocked,
        "manual_review_account_flags" if blocked else "continue_readonly_postcheck",
        True,
        BLOCKED_LABEL if blocked else MANUAL_REVIEW_LABEL,
    )


def recent_orders_row(created_at: str, inputs: dict[str, str], orders: list[Any]) -> dict[str, Any]:
    match = evaluate_recent_manual_smoke_test_order_match(
        orders,
        ticker=inputs["ticker"],
        side=inputs["side"],
        quantity=Decimal(inputs["quantity"]),
    )
    summary = format_match_summary(match)
    if match.duplicate_recent_order_check == "pass":
        status = NO_MATCH_LABEL
        next_step = "review_whether_manual_smoke_test_was_submitted_or_use_confirmed_postcheck_later"
    elif match.duplicate_recent_order_check == "blocked_recent_matching_order_exists" and match.recent_order_match_status == "filled":
        status = FILLED_LABEL
        next_step = "review_terminal_output_and_saved_postcheck"
    elif match.duplicate_recent_order_check == "blocked_recent_matching_order_exists":
        status = OPEN_LABEL
        next_step = "investigate_open_or_queued_order"
    else:
        status = MANUAL_REVIEW_LABEL
        next_step = "manual_review_recent_order_history_uncertain"
    row = postcheck_row(
        created_at,
        "readonly_recent_matching_orders",
        status,
        "warning" if status != FILLED_LABEL else "info",
        inputs,
        "Alpaca read-only recent orders endpoint",
        "Broker recent-order matching used the shared manual smoke-test helper; order identifiers omitted.",
        summary,
        "",
        "",
        False,
        next_step,
        True,
        status,
    )
    row.update(
        {
            "recent_order_match_found": match.recent_order_match_found,
            "recent_order_match_status": match.recent_order_match_status,
            "recent_order_match_submitted_at_or_created_at": match.recent_order_match_submitted_at_or_created_at,
            "recent_order_match_age_minutes": match.recent_order_match_age_minutes,
            "recent_order_match_source": match.recent_order_match_source,
            "recent_order_match_count": match.recent_order_match_count,
            "recent_order_match_lookback_minutes": match.recent_order_match_lookback_minutes,
        }
    )
    return row


def open_orders_row(created_at: str, inputs: dict[str, str], open_orders: list[Any]) -> dict[str, Any]:
    summary = f"open_order_count_for_ticker={len(open_orders)}"
    return postcheck_row(
        created_at,
        "readonly_open_orders_for_ticker",
        "postcheck_order_observed_open_or_queued" if open_orders else "pass",
        "warning" if open_orders else "info",
        inputs,
        "Alpaca read-only open orders endpoint",
        "Open order details and identifiers were not printed.",
        "",
        summary,
        "",
        False,
        "investigate_open_or_queued_order" if open_orders else "no_action_required_for_open_orders",
        True,
        OPEN_LABEL if open_orders else MANUAL_REVIEW_LABEL,
    )


def position_row(created_at: str, inputs: dict[str, str], client: Any) -> dict[str, Any]:
    try:
        position = client.get_open_position(inputs["ticker"])
        qty = Decimal(str(getattr(position, "qty", "0")))
        direction = "long" if qty > 0 else ("short" if qty < 0 else "flat")
        summary = f"position_direction={direction}; quantity_abs={abs(qty)}"
        status = "position_observed_manual_review"
    except Exception:
        summary = "position_unavailable_or_flat"
        status = "position_not_observed_or_unavailable"
    return postcheck_row(
        created_at,
        "readonly_position_summary",
        status,
        "info",
        inputs,
        "Alpaca read-only position endpoint",
        "Position summary is direction/quantity only; account identifiers are not printed.",
        "",
        "",
        summary,
        False,
        "review_position_summary_if_relevant",
        True,
        MANUAL_REVIEW_LABEL,
    )


def postcheck_row(
    created_at: str,
    check_name: str,
    check_status: str,
    severity: str,
    inputs: dict[str, str],
    evidence_source: str,
    details: str,
    matching_recent_order_status_summary: str,
    open_order_summary: str,
    position_summary: str,
    blocker: bool,
    recommended_next_step: str,
    alpaca_called: bool,
    final_postcheck_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "severity": severity,
        "ticker": inputs["ticker"],
        "side": inputs["side"],
        "quantity": inputs["quantity"],
        "evidence_source": evidence_source,
        "details": details,
        "matching_recent_order_status_summary": matching_recent_order_status_summary,
        "recent_order_match_found": "",
        "recent_order_match_status": "",
        "recent_order_match_submitted_at_or_created_at": "",
        "recent_order_match_age_minutes": "",
        "recent_order_match_source": "",
        "recent_order_match_count": "",
        "recent_order_match_lookback_minutes": "",
        "open_order_summary": open_order_summary,
        "position_summary": position_summary,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        "alpaca_called": alpaca_called,
        "order_execution_approved": False,
        "execution_approved": False,
        "scheduling_approved": False,
        "followup_order_approved": False,
        "final_postcheck_status": final_postcheck_status,
    }


def choose_final_status(rows: list[dict[str, Any]], confirmed: bool) -> str:
    if has_blocker(rows):
        return BLOCKED_LABEL
    if not confirmed:
        return REQUIRES_CONFIRM_LABEL
    statuses = {str(row.get("check_status", "")) for row in rows}
    for preferred in [FILLED_LABEL, OPEN_LABEL, NOT_FILLED_LABEL, NO_MATCH_LABEL]:
        if preferred in statuses:
            return preferred
    return MANUAL_REVIEW_LABEL


def final_details(final_status: str, rows: list[dict[str, Any]]) -> str:
    blockers = [row for row in rows if row.get("severity") == "blocked" or truthy(row.get("blocker"))]
    warnings = [row for row in rows if row.get("severity") == "warning"]
    key_items = blockers[:5] if blockers else warnings[:5]
    key_names = ", ".join(str(row.get("check_name", "")) for row in key_items) or "none"
    return f"final_status={final_status}; blocker_count={len(blockers)}; manual_review_count={len(warnings)}; key_items={key_names}."


def final_next_step(final_status: str) -> str:
    if final_status == REQUIRES_CONFIRM_LABEL:
        return "run_confirmed_readonly_postcheck_after_manual_smoke_test"
    if final_status == FILLED_LABEL:
        return "review_terminal_output_and_saved_postcheck"
    if final_status == OPEN_LABEL:
        return "investigate_open_or_queued_order"
    if final_status == NOT_FILLED_LABEL:
        return "investigate_open_or_rejected_order"
    if final_status == NO_MATCH_LABEL:
        return "review_whether_manual_smoke_test_was_submitted"
    return "no_followup_order_without_manual_review"


def build_summary_lines(output_path: Path, rows: list[dict[str, Any]]) -> list[str]:
    final_row = next((row for row in rows if row.get("check_name") == "final_postcheck_status"), {})
    blockers = [row for row in rows if row.get("severity") == "blocked" or truthy(row.get("blocker"))]
    warnings = [row for row in rows if row.get("severity") == "warning"]
    key_items = blockers[:5] if blockers else warnings[:5]
    key_names = ", ".join(str(row.get("check_name", "")) for row in key_items) or "none"
    return [
        "Paper-order smoke-test postcheck complete. Read-only/report-only; no follow-up order approved.",
        f"final_postcheck_status: {final_row.get('check_status', 'unavailable')}",
        f"ticker_side_quantity: {final_row.get('ticker', '')}; {final_row.get('side', '')}; {final_row.get('quantity', '')}",
        f"matching_recent_order_status_summary: {final_row.get('matching_recent_order_status_summary', '') or 'not_checked'}",
        f"open_order_summary: {final_row.get('open_order_summary', '') or 'not_checked'}",
        f"position_summary: {final_row.get('position_summary', '') or 'not_checked'}",
        f"key_blockers_or_manual_review_items: {key_names}",
        f"recommended_next_step: {final_row.get('recommended_next_step', 'unavailable')}",
        f"alpaca_called: {str(any_alpaca_called(rows)).lower()}",
        "order_execution_approved=false",
        "execution_approved=false",
        "scheduling_approved=false",
        "followup_order_approved=false",
        f"Saved postcheck to {output_path}",
        "Warning: this summary intentionally does not print a paper-order command, full order IDs, account IDs, secrets, or config contents.",
    ]


def format_match_summary(match: Any) -> str:
    parts = [
        f"recent_order_match_found={str(match.recent_order_match_found).lower()}",
        f"recent_order_match_status={match.recent_order_match_status or 'none'}",
        f"recent_order_match_count={match.recent_order_match_count}",
        f"lookback_minutes={match.recent_order_match_lookback_minutes}",
    ]
    if match.recent_order_match_age_minutes:
        parts.append(f"age_minutes={match.recent_order_match_age_minutes}")
    return "; ".join(parts)


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


def final_status_from_rows(rows: list[dict[str, Any]], final_check_name: str) -> str:
    final = next((row for row in rows if row.get("check_name") == final_check_name), {})
    return str(final.get("check_status") or "")


def matching_summary(rows: list[dict[str, Any]]) -> str:
    for row in reversed(rows):
        value = str(row.get("matching_recent_order_status_summary") or "")
        if value:
            return value
    return ""


def open_summary(rows: list[dict[str, Any]]) -> str:
    for row in reversed(rows):
        value = str(row.get("open_order_summary") or "")
        if value:
            return value
    return ""


def position_summary(rows: list[dict[str, Any]]) -> str:
    for row in reversed(rows):
        value = str(row.get("position_summary") or "")
        if value:
            return value
    return ""


def has_blocker(rows: list[dict[str, Any]]) -> bool:
    return any(row.get("severity") == "blocked" or truthy(row.get("blocker")) for row in rows)


def any_alpaca_called(rows: list[dict[str, Any]]) -> bool:
    return any(truthy(row.get("alpaca_called")) for row in rows)


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
