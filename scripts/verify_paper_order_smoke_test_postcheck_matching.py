from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.paper_order_smoke_test_postcheck import (  # noqa: E402
    FILLED_LABEL,
    MANUAL_REVIEW_LABEL,
    NO_MATCH_LABEL,
    OPEN_LABEL,
    recent_orders_row,
)
from trading_bot.safety.manual_paper_smoke_test_gate import (  # noqa: E402
    RECENT_ORDER_LOOKBACK_MINUTES,
    evaluate_recent_manual_smoke_test_order_match,
)


def main() -> int:
    failures: list[str] = []
    verify_shared_helper_cases(failures)
    verify_postcheck_uses_shared_helper(failures)
    verify_order_history_request_design(failures)
    verify_source_boundaries(failures)

    if failures:
        print("Paper-order smoke-test postcheck matching verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-order smoke-test postcheck matching verification passed.")
    print("Verified shared broker-order matching logic, position/CSV non-duplicates, uncertainty blocking, redacted diagnostics, and false execution/scheduling boundaries.")
    return 0


def verify_shared_helper_cases(failures: list[str]) -> None:
    now = datetime(2026, 6, 16, 10, 0, tzinfo=timezone.utc)
    recent = order("AAPL", "buy", "1", "filled", now - timedelta(minutes=5))
    helper = evaluate_recent_manual_smoke_test_order_match(
        [recent],
        ticker="AAPL",
        side="buy",
        quantity=Decimal("1"),
        now=now,
    )
    if helper.duplicate_recent_order_check != "blocked_recent_matching_order_exists":
        failures.append("filled broker order inside lookback should be a duplicate")
    if helper.recent_order_match_status != "filled" or helper.recent_order_match_count != 1:
        failures.append("filled broker order diagnostics should include status and count")
    if helper.recent_order_match_time_field_used != "submitted_at":
        failures.append("submitted_at fixture should report submitted_at as match time field")
    if helper.recent_order_match_lookback_minutes != RECENT_ORDER_LOOKBACK_MINUTES:
        failures.append("helper should expose the shared lookback window")

    old = order("AAPL", "buy", "1", "filled", now - timedelta(minutes=RECENT_ORDER_LOOKBACK_MINUTES + 1))
    if evaluate_recent_manual_smoke_test_order_match([old], ticker="AAPL", side="buy", quantity=Decimal("1"), now=now).duplicate_recent_order_check != "pass":
        failures.append("broker order outside lookback should not count as duplicate")

    wrong_side = order("AAPL", "sell", "1", "filled", now - timedelta(minutes=5))
    if evaluate_recent_manual_smoke_test_order_match([wrong_side], ticker="AAPL", side="buy", quantity=Decimal("1"), now=now).duplicate_recent_order_check != "pass":
        failures.append("wrong-side broker order should not count as duplicate")

    if evaluate_recent_manual_smoke_test_order_match([], ticker="AAPL", side="buy", quantity=Decimal("1"), now=now).duplicate_recent_order_check != "pass":
        failures.append("existing position alone should not count because no broker order was supplied")

    saved_csv_context = [{"ticker": "AAPL", "side": "buy", "quantity": "1", "status": "filled"}]
    if evaluate_recent_manual_smoke_test_order_match([], ticker=saved_csv_context[0]["ticker"], side=saved_csv_context[0]["side"], quantity=Decimal("1"), now=now).duplicate_recent_order_check != "pass":
        failures.append("saved CSV context alone should not count because no broker order was supplied")

    missing_time = SimpleNamespace(symbol="AAPL", side="buy", qty="1", status="filled")
    if evaluate_recent_manual_smoke_test_order_match([missing_time], ticker="AAPL", side="buy", quantity=Decimal("1"), now=now).duplicate_recent_order_check != "blocked_duplicate_order_history_uncertain":
        failures.append("matching broker order with no timestamp should block/manual-review as uncertain")

    filled_at_order = SimpleNamespace(
        symbol="AAPL",
        side=enum_value("buy"),
        qty="1",
        status=enum_value("filled"),
        filled_at=now - timedelta(minutes=3),
    )
    filled_at_result = evaluate_recent_manual_smoke_test_order_match(
        [filled_at_order],
        ticker="AAPL",
        side="buy",
        quantity=Decimal("1"),
        now=now,
    )
    if filled_at_result.duplicate_recent_order_check != "blocked_recent_matching_order_exists":
        failures.append("filled_at closed broker order fixture should be detected")
    if filled_at_result.recent_order_match_status != "filled":
        failures.append("enum-like filled status should normalize to filled")
    if filled_at_result.recent_order_match_time_field_used != "filled_at":
        failures.append("filled_at should be preferred as match time field for filled orders")


def verify_postcheck_uses_shared_helper(failures: list[str]) -> None:
    now = datetime.now(timezone.utc)
    inputs = {"ticker": "AAPL", "side": "buy", "quantity": "1"}
    filled = recent_orders_row("2026-06-16T10:00:00+00:00", inputs, [order("AAPL", "buy", "1", "filled", now)])
    if filled["check_status"] != FILLED_LABEL:
        failures.append("postcheck should report filled matching broker order with filled label")
    if str(filled["recent_order_match_found"]).lower() != "true":
        failures.append("postcheck filled row should expose recent_order_match_found=true")
    if filled["broker_order_history_matching_candidate_count"] != 1:
        failures.append("postcheck filled row should expose matching candidate count")

    submitted = recent_orders_row("2026-06-16T10:00:00+00:00", inputs, [order("AAPL", "buy", "1", "new", now)])
    if submitted["check_status"] != OPEN_LABEL:
        failures.append("postcheck should report active/submitted matching broker order with open/queued label")

    none = recent_orders_row("2026-06-16T10:00:00+00:00", inputs, [])
    if none["check_status"] != NO_MATCH_LABEL:
        failures.append("postcheck should report no matching order when broker history has no match")

    uncertain = recent_orders_row(
        "2026-06-16T10:00:00+00:00",
        inputs,
        [SimpleNamespace(symbol="AAPL", side="buy", qty="1", status="filled")],
    )
    if uncertain["check_status"] != MANUAL_REVIEW_LABEL:
        failures.append("postcheck should require manual review when broker history is ambiguous")

    for row in [filled, submitted, none, uncertain]:
        for flag in ["order_execution_approved", "execution_approved", "scheduling_approved", "followup_order_approved"]:
            if row.get(flag) is not False:
                failures.append(f"{flag} should remain false in postcheck matching row")
        details = " ".join(str(value) for value in row.values()).lower()
        for forbidden in ["order_id", "account_id", "api_key", "secret", "webhook"]:
            if forbidden in details:
                failures.append(f"postcheck matching diagnostics should not expose {forbidden}")


def verify_source_boundaries(failures: list[str]) -> None:
    gate_source = read_text(ROOT / "bot.py")
    postcheck_source = read_text(ROOT / "trading_bot" / "research" / "paper_order_smoke_test_postcheck.py")
    helper_source = read_text(ROOT / "trading_bot" / "safety" / "manual_paper_smoke_test_gate.py")
    if "evaluate_recent_manual_smoke_test_order_match(" not in gate_source:
        failures.append("gate should call shared recent-order matching helper")
    if "evaluate_recent_manual_smoke_test_order_match(" not in postcheck_source:
        failures.append("postcheck should call shared recent-order matching helper")
    for source_name, source in [("postcheck", postcheck_source), ("helper", helper_source)]:
        for forbidden in [
            ".submit_order(",
            ".cancel_order(",
            ".replace_order(",
            "insert_trade_log(",
            "send_discord_alert(",
            "send_telegram",
            "Register-ScheduledTask",
            "schtasks /create",
            "crontab",
        ]:
            if forbidden in source:
                failures.append(f"{source_name} source must not touch execution/alert/scheduling path: {forbidden}")


def verify_order_history_request_design(failures: list[str]) -> None:
    postcheck_source = read_text(ROOT / "trading_bot" / "research" / "paper_order_smoke_test_postcheck.py")
    bot_source = read_text(ROOT / "bot.py")
    for source_name, source in [("postcheck", postcheck_source), ("gate", bot_source)]:
        for token in [
            "QueryOrderStatus.CLOSED",
            "RECENT_ORDER_LOOKBACK_MINUTES",
            "after",
            "Sort.DESC",
            "limit",
            "500",
        ]:
            if token not in source:
                failures.append(f"{source_name} broker order history request missing {token}")
    for token in [
        "broker_order_history_status_filter_used",
        "broker_order_history_rows_seen",
        "broker_order_history_symbol_rows_seen",
        "broker_order_history_matching_candidate_count",
        "recent_order_match_time_field_used",
    ]:
        if token not in postcheck_source:
            failures.append(f"postcheck diagnostics missing {token}")


def order(symbol: str, side: str, qty: str, status: str, submitted_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(symbol=symbol, side=side, qty=qty, status=status, submitted_at=submitted_at)


def enum_value(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


if __name__ == "__main__":
    raise SystemExit(main())
