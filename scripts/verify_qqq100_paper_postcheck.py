from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.qqq100_paper_postcheck import (  # noqa: E402
    FINAL_FILLED_ALIGNED,
    OUTPUT_PATH,
    SUMMARY_PATH,
    BLOCKERS_PATH,
    choose_final_status,
    generate_qqq100_paper_postcheck,
    report_row,
    show_qqq100_paper_postcheck,
)


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "qqq100_paper_postcheck.py")

    verify_command_registration(bot_source, failures)
    verify_source_boundaries(module_source, failures)
    verify_outputs_ignored(failures)
    verify_static_generation(failures)
    verify_status_recognition(failures)
    verify_no_execution_wiring(bot_source, module_source, failures)

    if failures:
        print("QQQ100 paper postcheck verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 paper postcheck verification passed.")
    print("Verified read-only confirmation gate, saved outputs, filled/aligned recognition, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--qqq100-paper-postcheck",
        "--show-qqq100-paper-postcheck",
        "generate_qqq100_paper_postcheck",
        "show_qqq100_paper_postcheck",
        "confirm_readonly_alpaca_check=args.confirm_readonly_alpaca_check",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing postcheck command token: {token}")


def verify_source_boundaries(module_source: str, failures: list[str]) -> None:
    required = [
        "confirm_readonly_alpaca_check",
        "GetOrdersRequest",
        "QueryOrderStatus.CLOSED",
        "QueryOrderStatus.ALL",
        "get_all_positions",
        "evaluate_recent_manual_smoke_test_order_match",
        "qqq100_postcheck_order_observed_filled_aligned_long",
        "orders_created",
        "orders_submitted",
        "orders_cancelled",
        "orders_replaced",
        "sqlite_trade_log_written",
        "discord_alert_sent",
        "telegram_alert_sent",
        "followup_order_approved",
        "repeat_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"postcheck module missing required token: {token}")

    forbidden = [
        "submit_order",
        "submit_alpaca_order",
        "MarketOrderRequest",
        "cancel_order",
        "replace_order",
        "insert_trade_log",
        "send_discord_alert",
        "send_telegram",
        "download_",
        "yfinance",
        "order_id",
        "account_id",
        "webhook",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"postcheck module must not contain execution/secret token: {token}")

    confirmed_index = module_source.find("if confirm_readonly_alpaca_check:")
    broker_index = module_source.find("TradingClient")
    if confirmed_index == -1 or broker_index == -1 or broker_index < confirmed_index:
        failures.append("TradingClient import/use must be gated behind confirm_readonly_alpaca_check")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    for path in [OUTPUT_PATH, SUMMARY_PATH, BLOCKERS_PATH]:
        normalized = str(path).replace("\\", "/")
        if not normalized.startswith("data/") or "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {path}")


def verify_static_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_qqq100_paper_postcheck(False, root)
        if not (root / OUTPUT_PATH).exists() or not (root / SUMMARY_PATH).exists() or not (root / BLOCKERS_PATH).exists():
            failures.append("postcheck should write report, summary, and blockers in non-confirmed mode")
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_postcheck_status") != "qqq100_postcheck_requires_confirmed_readonly_check":
            failures.append("non-confirmed postcheck should require readonly confirmation")
        for collection in [result.rows, result.summary_rows, result.blocker_rows]:
            for row in collection:
                for flag in [
                    "orders_created",
                    "orders_submitted",
                    "orders_cancelled",
                    "orders_replaced",
                    "sqlite_trade_log_written",
                    "discord_alert_sent",
                    "telegram_alert_sent",
                    "execution_approved",
                    "paper_execution_approved",
                    "qqq100_execution_approved",
                    "followup_order_approved",
                    "repeat_execution_approved",
                    "scheduling_approved",
                ]:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false in postcheck outputs")
        code, lines = show_qqq100_paper_postcheck(root)
        if code != 0 or not any("qqq100_postcheck_requires_confirmed_readonly_check" in line for line in lines):
            failures.append("saved display should show non-confirmed postcheck status")


def verify_status_recognition(failures: list[str]) -> None:
    rows = [
        report_row(
            "2026-06-16T10:00:00+00:00",
            "readonly_recent_qqq_buy_1_order",
            "blocked_recent_matching_order_exists",
            "info",
            "long",
            "alpaca_paper_recent_orders",
            "fixture",
            False,
            "continue",
            recent_order_match_found=True,
            recent_order_match_status="filled",
            recent_order_match_count=1,
            alpaca_called=True,
            alpaca_readonly=True,
        ),
        report_row(
            "2026-06-16T10:00:00+00:00",
            "readonly_current_qqq_position",
            "pass",
            "info",
            "long",
            "alpaca_paper_positions_readonly",
            "fixture",
            False,
            "continue",
            position_status="paper_position_long",
            position_quantity_abs="1",
            alignment_state="aligned_long",
            alpaca_called=True,
            alpaca_readonly=True,
            paper_positions_read=True,
        ),
    ]
    if choose_final_status(rows, True) != FINAL_FILLED_ALIGNED:
        failures.append("filled recent QQQ buy 1 plus aligned_long position should produce final filled/aligned status")
    if choose_final_status([], False) != "qqq100_postcheck_requires_confirmed_readonly_check":
        failures.append("missing readonly confirmation should block broker checks")


def verify_no_execution_wiring(bot_source: str, module_source: str, failures: list[str]) -> None:
    postcheck_route = function_block(bot_source, 'if "--qqq100-paper-postcheck" in sys.argv[1:]:', 'if sys.argv[1:] == ["--show-qqq100-paper-postcheck"]:')
    if "run_execute_qqq100_paper" in postcheck_route or "run_paper_order_test" in postcheck_route:
        failures.append("postcheck route must not run execution commands")
    combined = bot_source + "\n" + module_source
    if "--paper-order-test AAPL buy 1 --confirm-paper-order" in combined:
        failures.append("postcheck verifier/module must not include runnable AAPL paper-order command")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def function_block(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index == -1:
        return ""
    end_index = source.find(end, start_index + len(start))
    if end_index == -1:
        return source[start_index:]
    return source[start_index:end_index]


if __name__ == "__main__":
    raise SystemExit(main())
