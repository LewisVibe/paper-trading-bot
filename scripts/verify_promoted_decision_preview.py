from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bot
from trading_bot.research import promoted_decision
from trading_bot.research.promoted_decision import (
    PROMOTED_DECISION_COLUMNS,
    build_promoted_decision_rows,
    run_promoted_decision_preview_files,
)


FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "OrderSide",
    "TimeInForce",
    "download_close_prices",
    "download_backtest_prices",
    "download_slow_sma_preview_prices",
    "configure_yfinance_cache",
    "get_alpaca_positions",
    "get_open_orders_for_ticker",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "decide_trade",
    "submit_alpaca_order",
    "init_database",
    "sqlite3",
]


def consensus_row(ticker: str, state: str, long_votes: str = "0", flat_votes: str = "0") -> dict[str, str]:
    return {
        "ticker": ticker,
        "consensus_state": state,
        "long_votes": long_votes,
        "flat_votes": flat_votes,
    }


def action_row(ticker: str, preview_action: str) -> dict[str, str]:
    return {
        "ticker": ticker,
        "preview_action": preview_action,
    }


def risk_row(ticker: str, risk_status: str) -> dict[str, str]:
    return {
        "ticker": ticker,
        "risk_status": risk_status,
    }


def add_failure(failures: list[str], message: str) -> None:
    failures.append(message)


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = inspect.getsource(promoted_decision)
    command_source = inspect.getsource(bot.run_promoted_decision_preview)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in helper_source:
            add_failure(failures, f"promoted decision helper should not reference {token}")
        if token in command_source:
            add_failure(failures, f"run_promoted_decision_preview should not reference {token}")


def verify_rows(failures: list[str]) -> None:
    rows = build_promoted_decision_rows(
        [
            consensus_row("AAA", "mixed_long_flat", "1", "1"),
            consensus_row("BBB", "unanimous_flat", "0", "2"),
            consensus_row("CCC", "unanimous_long", "2", "0"),
            consensus_row("DDD", "unanimous_long", "2", "0"),
            consensus_row("EEE", "unknown", "0", "0"),
        ],
        [
            action_row("AAA", "would_open_long"),
            action_row("BBB", "no_action_already_flat"),
            action_row("CCC", "would_open_long"),
            action_row("DDD", "would_open_long"),
            action_row("EEE", "position_unavailable"),
        ],
        [
            risk_row("AAA", "blocked_for_review"),
            risk_row("BBB", "ok"),
            risk_row("CCC", "warning"),
            risk_row("DDD", "ok"),
            risk_row("EEE", "ok"),
        ],
        created_at="2026-06-06T00:00:00Z",
    )
    by_ticker = {row["ticker"]: row for row in rows}
    expected_states = {
        "AAA": "blocked_strategy_disagreement",
        "BBB": "no_action_unanimous_flat",
        "CCC": "review_warning",
        "DDD": "research_only_unanimous_long",
        "EEE": "unknown",
    }
    for ticker, state in expected_states.items():
        if by_ticker[ticker]["decision_state"] != state:
            add_failure(failures, f"{ticker} expected {state}, got {by_ticker[ticker]['decision_state']}")
    if by_ticker["AAA"]["risk_status_summary"] != "blocked_for_review":
        add_failure(failures, "decision row should summarize risk statuses")
    if by_ticker["CCC"]["action_summary"] != "would_open_long":
        add_failure(failures, "decision row should summarize preview actions")
    if any(row.get("execution_approved") is not False for row in rows):
        add_failure(failures, "execution_approved should be False for every row")
    if any(row.get("research_only") is not True or row.get("preview_only") is not True for row in rows):
        add_failure(failures, "all decision rows should be research_only and preview_only")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def verify_file_runner(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        consensus_path = temp_path / "promoted_consensus_preview.csv"
        action_path = temp_path / "promoted_strategy_action_preview.csv"
        risk_path = temp_path / "promoted_risk_preview.csv"
        output_path = temp_path / "promoted_decision_preview.csv"

        status_code, lines = run_promoted_decision_preview_files(
            consensus_path,
            action_path,
            risk_path,
            output_path,
        )
        if status_code != 1:
            add_failure(failures, "missing decision inputs should return status code 1")
        if output_path.exists():
            add_failure(failures, "missing decision inputs should not create output CSV")
        missing_summary = "\n".join(lines)
        for expected_text in [
            "python bot.py --promoted-consensus-preview",
            "python bot.py --preview-promoted-actions",
            "python bot.py --promoted-risk-preview",
        ]:
            if expected_text not in missing_summary:
                add_failure(failures, f"missing input output should mention {expected_text}")

        write_csv(
            consensus_path,
            ["ticker", "consensus_state", "long_votes", "flat_votes"],
            [
                consensus_row("AAA", "mixed_long_flat", "1", "1"),
                consensus_row("BBB", "unanimous_flat", "0", "2"),
                consensus_row("CCC", "unanimous_long", "2", "0"),
                consensus_row("DDD", "unanimous_long", "2", "0"),
            ],
        )
        write_csv(
            action_path,
            ["ticker", "preview_action"],
            [
                action_row("AAA", "would_open_long"),
                action_row("BBB", "no_action_already_flat"),
                action_row("CCC", "would_open_long"),
                action_row("DDD", "would_open_long"),
            ],
        )
        write_csv(
            risk_path,
            ["ticker", "risk_status"],
            [
                risk_row("AAA", "blocked_for_review"),
                risk_row("BBB", "ok"),
                risk_row("CCC", "blocked_for_review"),
                risk_row("DDD", "ok"),
            ],
        )
        status_code, lines = run_promoted_decision_preview_files(
            consensus_path,
            action_path,
            risk_path,
            output_path,
        )
        if status_code != 0:
            add_failure(failures, "valid decision preview inputs should return status code 0")
        if not output_path.exists():
            add_failure(failures, "valid decision preview should create output CSV")
            return
        with output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            output_rows = list(reader)
            if reader.fieldnames != PROMOTED_DECISION_COLUMNS:
                add_failure(failures, "decision output columns changed unexpectedly")
        by_ticker = {row["ticker"]: row for row in output_rows}
        if by_ticker["AAA"]["decision_state"] != "blocked_strategy_disagreement":
            add_failure(failures, "strategy disagreement should be highest-priority block")
        if by_ticker["BBB"]["decision_state"] != "no_action_unanimous_flat":
            add_failure(failures, "unanimous flat should produce no_action_unanimous_flat")
        if by_ticker["CCC"]["decision_state"] != "blocked_risk_review":
            add_failure(failures, "blocked risk should override unanimous long")
        if by_ticker["DDD"]["decision_state"] != "research_only_unanimous_long":
            add_failure(failures, "unanimous long without risk block should remain research-only")
        if any(row.get("execution_approved") != "False" for row in output_rows):
            add_failure(failures, "output CSV should mark every row execution_approved=False")
        if any(row.get("research_only") != "True" or row.get("preview_only") != "True" for row in output_rows):
            add_failure(failures, "output CSV should mark every row research_only=True and preview_only=True")
        summary = "\n".join(lines)
        for expected_text in [
            "RESEARCH ONLY. PREVIEW ONLY. NOT EXECUTION.",
            "Rows: 4",
            "blocked_risk_review=1",
            "blocked_strategy_disagreement=1",
            "no_action_unanimous_flat=1",
            "research_only_unanimous_long=1",
            "Saved promoted decision preview",
        ]:
            if expected_text not in summary:
                add_failure(failures, f"summary missing expected text: {expected_text}")


def main() -> int:
    failures: list[str] = []
    verify_no_forbidden_source_paths(failures)
    verify_rows(failures)
    verify_file_runner(failures)

    if failures:
        print("Promoted decision preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Promoted decision preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
