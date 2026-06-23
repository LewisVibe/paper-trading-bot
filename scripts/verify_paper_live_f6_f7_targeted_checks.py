from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

QQQ100_ACTION_PREVIEW = ROOT / "trading_bot" / "research" / "qqq100_action_preview.py"
PROMOTED_ACTIONS = ROOT / "trading_bot" / "research" / "promoted_actions.py"
MULTI_SLEEVE_BACKTEST = ROOT / "trading_bot" / "research" / "multi_sleeve_portfolio_backtest.py"
F6_F7_AUDIT = ROOT / "trading_bot" / "research" / "paper_live_f6_f7_audit.py"

DOCS = [
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "CODEX_WORKFLOW.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md",
]

FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_all_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "yf.",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []

    verify_f6_qqq100_unknown_positions(failures)
    verify_f6_promoted_actions_unknown_positions(failures)
    verify_f7_portfolio_accounting_boundary(failures)
    verify_static_boundaries(failures)
    verify_docs(failures)

    if failures:
        print("Paper-live F6/F7 targeted checks verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live F6/F7 targeted checks verification passed.")
    print("Verified loud unknown-position handling and blocked portfolio accounting promotion evidence.")
    print("No broker reads, orders, config loading, market-data refresh, alerts, or scheduling are required.")
    return 0


def verify_f6_qqq100_unknown_positions(failures: list[str]) -> None:
    from trading_bot.research.qqq100_action_preview import (  # noqa: PLC0415
        ReadonlyPositionContext,
        alignment_decision,
        build_preview_row,
    )

    unknown_cases = [
        ("long", "position_not_read", "review_required_position_unknown", "manual_review_required_position_unknown"),
        ("flat", "position_not_read", "review_required_position_unknown", "manual_review_required_position_unknown"),
        ("long", "position_context_unavailable", "position_context_unavailable", "manual_review_required_position_unavailable"),
        ("flat", "position_context_unavailable", "position_context_unavailable", "manual_review_required_position_unavailable"),
    ]
    for desired_position, current_status, expected_alignment, expected_action in unknown_cases:
        alignment_state, preview_action, blocker, next_step = alignment_decision(desired_position, current_status)
        if alignment_state != expected_alignment:
            failures.append(f"F6 QQQ100 {desired_position}/{current_status} alignment should be {expected_alignment}, got {alignment_state}")
        if preview_action != expected_action:
            failures.append(f"F6 QQQ100 {desired_position}/{current_status} action should be {expected_action}, got {preview_action}")
        if "position" not in blocker and "manual_review" not in blocker:
            failures.append(f"F6 QQQ100 {desired_position}/{current_status} blocker is not loud enough: {blocker}")
        if "review" not in next_step and "resolve" not in next_step and "rerun" not in next_step:
            failures.append(f"F6 QQQ100 {desired_position}/{current_status} next step is not conservative: {next_step}")

    signal = {
        "desired_position": "long",
        "signal_date": "2026-01-01",
        "latest_close": "100.0",
        "trend_state": "trend_on",
        "data_status": "saved_signal_loaded",
    }
    unknown_position = ReadonlyPositionContext(
        current_position_status="position_not_read",
        current_position_source="saved_signal_only",
        current_position_quantity_if_readonly="",
        position_read_mode="saved_signal_only",
        alpaca_called=False,
        alpaca_readonly=False,
        paper_positions_read=False,
    )
    unknown_row = build_preview_row(signal, unknown_position)
    assert_false_approval_flags(unknown_row, failures, "F6 QQQ100 unknown preview")
    for forbidden in ["aligned_long", "aligned_flat", "no_action_preview_only"]:
        if forbidden in {unknown_row.get("alignment_state"), unknown_row.get("non_executable_preview_action")}:
            failures.append(f"F6 QQQ100 unknown position silently became {forbidden}")

    unavailable_position = ReadonlyPositionContext(
        current_position_status="position_context_unavailable",
        current_position_source="readonly_confirmation_missing",
        current_position_quantity_if_readonly="",
        position_read_mode="readonly_confirmation_missing",
        alpaca_called=False,
        alpaca_readonly=False,
        paper_positions_read=False,
        data_error="fixture unavailable",
    )
    unavailable_row = build_preview_row({**signal, "desired_position": "flat"}, unavailable_position)
    assert_false_approval_flags(unavailable_row, failures, "F6 QQQ100 unavailable preview")
    if unavailable_row.get("alignment_state") != "position_context_unavailable":
        failures.append("F6 QQQ100 unavailable position should remain position_context_unavailable")


def verify_f6_promoted_actions_unknown_positions(failures: list[str]) -> None:
    from trading_bot.research.promoted_actions import build_promoted_action_preview_row  # noqa: PLC0415

    base_preview = {
        "strategy_name": "qqq_100_trend_gate",
        "strategy_family": "stock_etf",
        "ticker": "QQQ",
        "promotion_status": "preview_candidate",
        "required_next_step": "manual_review_required",
    }
    for desired_position in ["long", "flat"]:
        row = build_promoted_action_preview_row(
            "2026-01-01T00:00:00+00:00",
            {**base_preview, "desired_position": desired_position},
            position=None,
            current_available=False,
            position_source="not_loaded",
            default_quantity=Decimal("1"),
        )
        if row.get("preview_action") != "position_unavailable":
            failures.append(f"F6 promoted action {desired_position} should be position_unavailable, got {row.get('preview_action')}")
        if row.get("current_position") != "unavailable":
            failures.append(f"F6 promoted action {desired_position} should keep current_position unavailable")
        if row.get("preview_quantity") not in {"", None}:
            failures.append(f"F6 promoted action {desired_position} should not emit preview quantity when position is unknown")
        for forbidden in ["no_action_already_flat", "no_action_already_long", "would_open_long", "would_close_long"]:
            if row.get("preview_action") == forbidden:
                failures.append(f"F6 promoted action unknown position silently became {forbidden}")


def verify_f7_portfolio_accounting_boundary(failures: list[str]) -> None:
    from trading_bot.research.multi_sleeve_portfolio_backtest import (  # noqa: PLC0415
        portfolio_metrics_from_streams,
    )

    rows = [
        stream_row("2026-01-01", "qqq_100_trend_gate", "0.0100"),
        stream_row("2026-01-02", "qqq_100_trend_gate", "0.0000"),
        stream_row("2026-01-03", "qqq_100_trend_gate", "-0.0100"),
        stream_row("2026-01-01", "codex_broad_growth_balanced_breakout_control", "0.0200"),
        stream_row("2026-01-02", "codex_broad_growth_balanced_breakout_control", "0.0100"),
        stream_row("2026-01-03", "codex_broad_growth_balanced_breakout_control", "0.0000"),
        stream_row("2026-01-01", "cash_default_defensive_sleeve", "0.0000"),
        stream_row("2026-01-02", "cash_default_defensive_sleeve", "0.0000"),
        stream_row("2026-01-03", "cash_default_defensive_sleeve", "0.0000"),
    ]
    metrics = portfolio_metrics_from_streams(
        "qqq100_plus_high_growth_research",
        rows,
        qqq_reference_candidate="qqq_100_trend_gate",
    )
    if metrics is None:
        failures.append("F7 fixture portfolio metrics should be calculable from in-memory return streams")
        return
    if metrics.get("turnover_or_trade_count") in {"", None}:
        failures.append("F7 portfolio metrics should expose turnover_or_trade_count for review context")

    source = read_text(MULTI_SLEEVE_BACKTEST)
    if "sum(by_candidate[candidate][date] * weight for candidate, weight in weights.items())" not in source:
        failures.append("F7 multi-sleeve portfolio should aggregate weighted returns, not independent starting capital sleeves")
    for token in [
        "manual_review_required_before_candidate_label_change",
        "not_promotion_ready_research_only",
        '"execution_approved": False',
        '"general_execution_approved": False',
        '"qqq100_execution_approved": False',
        '"scheduling_approved": False',
        '"live_trading_approved": False',
    ]:
        if token not in source:
            failures.append(f"F7 source boundary missing token: {token}")

    audit_source = read_text(F6_F7_AUDIT)
    for token in [
        "F7_multi_sleeve_portfolio_accounting",
        "f7_accounting_consistency_manual_review_required",
        "build F7 accounting verifier before any multi-sleeve paper-live promotion discussion",
    ]:
        if token not in audit_source:
            failures.append(f"F7 audit boundary missing token: {token}")


def verify_static_boundaries(failures: list[str]) -> None:
    for path in [QQQ100_ACTION_PREVIEW, PROMOTED_ACTIONS, MULTI_SLEEVE_BACKTEST, F6_F7_AUDIT]:
        source = read_text(path)
        for token in FORBIDDEN_SOURCE_TOKENS:
            if token in source and path not in {QQQ100_ACTION_PREVIEW}:
                failures.append(f"forbidden broker/order/config/market/scheduling token in {path.name}: {token}")
        if path == QQQ100_ACTION_PREVIEW:
            for token in [".submit_order(", ".cancel_order(", ".replace_order(", "MarketOrderRequest(", "insert_trade_log("]:
                if token in source:
                    failures.append(f"forbidden order/write token in {path.name}: {token}")


def verify_docs(failures: list[str]) -> None:
    docs_source = "\n".join(read_text(path) for path in DOCS)
    for token in [
        "F6/F7 targeted checks",
        "verify_paper_live_f6_f7_targeted_checks.py",
        "unknown positions",
        "portfolio backtests",
        "not promotion evidence",
    ]:
        if token not in docs_source:
            failures.append(f"docs missing targeted-checks token: {token}")


def stream_row(date: str, candidate: str, daily_return: str) -> dict[str, str]:
    return {
        "date": date,
        "candidate_name": candidate,
        "daily_strategy_return": daily_return,
        "weight": "1.0",
        "signal": "held",
        "source": "fixture",
    }


def assert_false_approval_flags(row: dict[str, object], failures: list[str], context: str) -> None:
    for field in [
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "orders_created",
        "orders_submitted",
        "orders_cancelled",
        "alpaca_called",
        "live_positions_read",
    ]:
        if field in row and row.get(field) is not False:
            failures.append(f"{context} should preserve {field}=False")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
