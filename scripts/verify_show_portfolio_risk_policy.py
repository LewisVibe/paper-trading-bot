from __future__ import annotations

import csv
import inspect
import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research import portfolio_risk_policy as policy
from trading_bot.research.portfolio_risk_policy import (
    PORTFOLIO_RISK_POLICY_COLUMNS,
    build_show_portfolio_risk_policy_lines,
    show_portfolio_risk_policy_file,
)
from trading_bot.runners import research_reports


FORBIDDEN_SOURCE_TOKENS = [
    "yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_open_orders_for_ticker",
    "decide_trade",
    "download_close_prices",
    "download_backtest_prices",
    "download_slow_sma_preview_prices",
    "configure_yfinance_cache",
    "sqlite3",
]


def main() -> int:
    failures: list[str] = []
    verify_no_forbidden_source_paths(failures)
    verify_missing_csv(failures)
    verify_normal_csv_display(failures)
    verify_execution_warning(failures)
    verify_command_output_warning(failures)

    if failures:
        print("Show portfolio risk policy verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Show portfolio risk policy verification passed.")
    return 0


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = "\n".join(
        [
            inspect.getsource(policy.build_show_portfolio_risk_policy_lines),
            inspect.getsource(policy.build_missing_portfolio_risk_policy_lines),
            inspect.getsource(policy.show_portfolio_risk_policy_file),
            inspect.getsource(policy.read_csv_rows),
        ]
    )
    command_source = inspect.getsource(research_reports.run_show_portfolio_risk_policy_command)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in helper_source:
            failures.append(f"show portfolio-risk-policy helpers should not reference {token}")
        if token in command_source:
            failures.append(f"run_show_portfolio_risk_policy_command should not reference {token}")


def verify_missing_csv(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        missing_path = Path(temp_dir) / "portfolio_risk_policy_report.csv"
        status_code, lines = show_portfolio_risk_policy_file(missing_path)
    output = "\n".join(lines)
    if status_code != 1:
        failures.append("missing CSV should return status code 1")
    for expected_text in [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "does not refresh data, read positions, enforce risk, or submit orders",
        "python bot.py --portfolio-risk-policy-report",
        "python bot.py --show-portfolio-risk-policy",
        "No risk policy was enforced by this display command.",
    ]:
        if expected_text not in output:
            failures.append(f"missing CSV output missing expected text: {expected_text}")


def verify_normal_csv_display(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "portfolio_risk_policy_report.csv"
        rows = [
            policy_row("paper_only_policy", "pass", "high", "alpaca.paper=True"),
            policy_row(
                "strategy_disagreement_policy",
                "blocked_for_review",
                "high",
                "blocked_strategy_disagreement=AAPL, SPY",
                "Saved promoted decision preview has strategy disagreement rows; this blocks execution discussion.",
                "Keep promoted candidates research-only until disagreements are resolved and reviewed.",
            ),
            policy_row(
                "kill_switch_policy",
                "not_implemented_future_work",
                "high",
                "future requirement",
                "Paper-only kill switch policy is documented as future risk-management work.",
                "Design and verify a paper-only kill switch separately.",
            ),
            policy_row(
                "max_total_desired_notional_policy",
                "warning",
                "medium",
                "estimated_unique_desired_notional=250.0000",
            ),
        ]
        with input_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=PORTFOLIO_RISK_POLICY_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        original_contents = input_path.read_text(encoding="utf-8")
        status_code, lines = show_portfolio_risk_policy_file(input_path)
        output = "\n".join(lines)
        after_contents = input_path.read_text(encoding="utf-8")

    if status_code != 0:
        failures.append("normal CSV display should return status code 0")
    if original_contents != after_contents:
        failures.append("show-portfolio-risk-policy should not modify the input CSV")
    for expected_text in [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "Rows: 4",
        "- blocked_for_review: 1",
        "- not_implemented_future_work: 1",
        "- pass: 1",
        "- warning: 1",
        "- high: 3",
        "- medium: 1",
        "Blocked-for-review rows:",
        "strategy_disagreement_policy",
        "Future-work rows:",
        "kill_switch_policy",
        "Execution approved: False for all rows.",
        "No risk policy was enforced by this display command.",
    ]:
        if expected_text not in output:
            failures.append(f"display output missing expected text: {expected_text}")


def verify_execution_warning(failures: list[str]) -> None:
    lines = build_show_portfolio_risk_policy_lines(
        Path("data/portfolio_risk_policy_report.csv"),
        [policy_row("execution_approval_policy", "blocked_for_review", "high", "fixture", execution_approved="True")],
    )
    output = "\n".join(lines)
    if "WARNING: at least one row has execution_approved=True; manual review required." not in output:
        failures.append("display should warn if any fixture row has execution_approved=True")


def verify_command_output_warning(failures: list[str]) -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        research_reports.run_show_portfolio_risk_policy_command()
    output = buffer.getvalue()
    first_line = output.splitlines()[0] if output.splitlines() else ""
    if first_line != "READ-ONLY DISPLAY. NOT EXECUTION.":
        failures.append("command output should start with the read-only warning")
    if "does not refresh data, read positions, enforce risk, or submit orders" not in output:
        failures.append("command output should include the no-refresh/no-risk/no-order warning")


def policy_row(
    risk_policy_name: str,
    risk_policy_status: str,
    risk_level: str,
    current_value_or_limit: str,
    finding: str = "Fixture finding.",
    required_next_step: str = "Fixture next step.",
    execution_approved: str = "False",
) -> dict[str, str]:
    return {
        "created_at": "2026-06-08T00:00:00+00:00",
        "risk_policy_name": risk_policy_name,
        "risk_policy_status": risk_policy_status,
        "risk_level": risk_level,
        "current_value_or_limit": current_value_or_limit,
        "finding": finding,
        "required_next_step": required_next_step,
        "research_only": "True",
        "preview_only": "True",
        "execution_approved": execution_approved,
    }


if __name__ == "__main__":
    raise SystemExit(main())
