from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.portfolio_risk_policy as policy
from trading_bot.research.portfolio_risk_policy import generate_portfolio_risk_policy_report
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
    verify_fixture_report(failures)
    verify_missing_saved_csvs(failures)
    verify_execution_approval_detection(failures)
    verify_source_safety(failures)

    if failures:
        print("Portfolio risk policy report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Portfolio risk policy report verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture_project(root)
        result = generate_portfolio_risk_policy_report(root)
        if not result.output_path.exists():
            failures.append("portfolio_risk_policy_report.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != policy.PORTFOLIO_RISK_POLICY_COLUMNS:
                failures.append("portfolio risk policy columns changed unexpectedly")
            rows = list(reader)

        if len(rows) < 10:
            failures.append("portfolio risk policy report should include all expected policy rows")
        for row in rows:
            if row["research_only"] != "True" or row["preview_only"] != "True" or row["execution_approved"] != "False":
                failures.append(f"safety flags failed for {row['risk_policy_name']}")

        checks = {row["risk_policy_name"]: row for row in rows}
        expected_checks = [
            "paper_only_policy",
            "dry_run_default_policy",
            "shorting_policy",
            "max_open_positions_policy",
            "max_single_position_notional_policy",
            "max_total_desired_notional_policy",
            "duplicate_ticker_exposure_policy",
            "strategy_disagreement_policy",
            "execution_approval_policy",
            "safe_scheduling_policy",
            "kill_switch_policy",
            "discord_daily_summary_policy",
        ]
        for check in expected_checks:
            if check not in checks:
                failures.append(f"missing policy check: {check}")

        if checks["duplicate_ticker_exposure_policy"]["risk_policy_status"] != "warning":
            failures.append("duplicate desired-long exposure should produce a warning")
        if "AAPL:2" not in checks["duplicate_ticker_exposure_policy"]["current_value_or_limit"]:
            failures.append("duplicate exposure row should identify AAPL as duplicated")
        if checks["strategy_disagreement_policy"]["risk_policy_status"] != "blocked_for_review":
            failures.append("blocked_strategy_disagreement should block execution discussion")
        if "AAPL" not in checks["strategy_disagreement_policy"]["current_value_or_limit"]:
            failures.append("strategy disagreement row should identify AAPL")
        if checks["execution_approval_policy"]["risk_policy_status"] != "pass":
            failures.append("all-false execution_approved fixture should pass execution approval policy")
        if checks["kill_switch_policy"]["risk_policy_status"] != "not_implemented_future_work":
            failures.append("kill switch should be labelled future work, not enforced")
        if checks["discord_daily_summary_policy"]["risk_policy_status"] != "not_implemented_future_work":
            failures.append("daily summary should be labelled future work, not enforced")

        summary = "\n".join(result.summary_lines)
        for expected_text in [
            "PORTFOLIO RISK POLICY REPORT. RESEARCH ONLY. NOT EXECUTION.",
            "No risk policy was enforced and no execution approval was granted.",
            "A blocked result means do not discuss execution yet",
            "Saved portfolio risk policy report",
        ]:
            if expected_text not in summary:
                failures.append(f"summary missing expected text: {expected_text}")


def verify_missing_saved_csvs(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "data").mkdir(parents=True, exist_ok=True)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "config.example.json").write_text(
            '{"dry_run": true, "allow_shorting": false, "alpaca": {"paper": true}}\n',
            encoding="utf-8",
        )
        result = generate_portfolio_risk_policy_report(root)
        checks = {row["risk_policy_name"]: row for row in result.rows}
        for check in [
            "max_open_positions_policy",
            "strategy_disagreement_policy",
            "safe_scheduling_policy",
        ]:
            if checks[check]["risk_policy_status"] != "insufficient_data":
                failures.append(f"{check} should handle missing saved CSVs as insufficient_data")


def verify_execution_approval_detection(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture_project(root)
        write_csv(
            root / "data" / "promoted_decision_preview.csv",
            [
                {
                    "ticker": "XYZ",
                    "decision_state": "research_only_unanimous_long",
                    "execution_approved": "True",
                    "research_only": "True",
                    "preview_only": "True",
                }
            ],
        )
        result = generate_portfolio_risk_policy_report(root)
        checks = {row["risk_policy_name"]: row for row in result.rows}
        if checks["execution_approval_policy"]["risk_policy_status"] != "blocked_for_review":
            failures.append("execution_approved=True fixture should block execution approval policy")


def verify_source_safety(failures: list[str]) -> None:
    source = inspect.getsource(policy)
    runner_source = inspect.getsource(research_reports.run_portfolio_risk_policy_report_command)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"portfolio risk policy report should not reference {token}")
        if token in runner_source:
            failures.append(f"portfolio risk policy runner should not reference {token}")


def write_fixture_project(root: Path) -> None:
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "CURRENT_STATE.md").write_text("paper-only current state\n", encoding="utf-8")
    (root / "config.example.json").write_text(
        '{"dry_run": true, "allow_shorting": false, "alpaca": {"paper": true}}\n',
        encoding="utf-8",
    )
    write_csv(
        root / "data" / "promoted_risk_preview.csv",
        [
            risk_row("sma_50_200_trend", "AAPL", "long", "100.0"),
            risk_row("buy_above_200_exit_below_200", "AAPL", "long", "100.0"),
            risk_row("sma_50_200_trend", "MSFT", "flat", "0"),
        ],
    )
    write_csv(
        root / "data" / "promoted_decision_preview.csv",
        [
            {
                "ticker": "AAPL",
                "decision_state": "blocked_strategy_disagreement",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            },
            {
                "ticker": "MSFT",
                "decision_state": "no_action_unanimous_flat",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            },
        ],
    )
    write_csv(
        root / "data" / "defensive_candidate_comparison.csv",
        [
            {
                "strategy_name": "monthly_etf_momentum_rotation",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            }
        ],
    )
    write_csv(
        root / "data" / "deployment_readiness_report.csv",
        [
            {
                "check_name": "must_not_schedule_commands_documented",
                "check_status": "pass",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            }
        ],
    )
    write_csv(
        root / "data" / "promoted_strategy_action_preview.csv",
        [
            {
                "ticker": "AAPL",
                "desired_position": "long",
                "preview_action": "would_open_long",
                "preview_only": "True",
            }
        ],
    )


def risk_row(strategy_name: str, ticker: str, desired_position: str, notional: str) -> dict[str, str]:
    return {
        "strategy_name": strategy_name,
        "ticker": ticker,
        "desired_position": desired_position,
        "current_position": "unavailable",
        "preview_action": "position_unavailable",
        "latest_close": notional,
        "assumed_quantity": "1",
        "estimated_desired_notional": notional,
        "risk_check": "fixture",
        "risk_status": "warning",
        "risk_reason": "fixture",
        "research_only": "True",
        "preview_only": "True",
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
