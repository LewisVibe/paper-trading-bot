from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.execution_eligibility as eligibility
from trading_bot.research.execution_eligibility import generate_execution_eligibility_report
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
    verify_missing_inputs(failures)
    verify_execution_approved_true_blocks(failures)
    verify_source_safety(failures)

    if failures:
        print("Execution eligibility report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Execution eligibility report verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture_project(root)
        result = generate_execution_eligibility_report(root)
        if not result.output_path.exists():
            failures.append("execution_eligibility_report.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != eligibility.EXECUTION_ELIGIBILITY_COLUMNS:
                failures.append("execution eligibility columns changed unexpectedly")
            rows = list(reader)

        if len(rows) < 8:
            failures.append("execution eligibility report should include all expected checks")
        for row in rows:
            if row["research_only"] != "True" or row["preview_only"] != "True" or row["execution_approved"] != "False":
                failures.append(f"safety flags failed for {row['eligibility_check_name']}")

        checks = {row["eligibility_check_name"]: row for row in rows}
        for required in [
            "promoted_decision_approval",
            "promoted_strategy_disagreement",
            "no_action_flat_tickers",
            "portfolio_risk_policy_blockers",
            "kill_switch_readiness",
            "deployment_readiness",
            "high_risk_commands_gated",
            "final_execution_eligibility",
        ]:
            if required not in checks:
                failures.append(f"missing eligibility check: {required}")

        if checks["promoted_strategy_disagreement"]["eligibility_status"] != "blocked_for_review":
            failures.append("strategy disagreement should block execution eligibility")
        disagreement_finding = checks["promoted_strategy_disagreement"]["finding"]
        if "AAPL" not in disagreement_finding or "SPY" not in disagreement_finding:
            failures.append("strategy disagreement finding should identify AAPL and SPY")
        if checks["no_action_flat_tickers"]["eligibility_status"] != "pass":
            failures.append("no_action_unanimous_flat should be treated as no action required")
        if "MSFT" not in checks["no_action_flat_tickers"]["finding"]:
            failures.append("no-action row should identify MSFT")
        if checks["kill_switch_readiness"]["eligibility_status"] != "not_ready":
            failures.append("kill-switch future work should make eligibility not ready")
        if checks["final_execution_eligibility"]["eligibility_status"] != "blocked_for_review":
            failures.append("final eligibility should remain blocked when blockers/not-ready rows exist")
        if checks["final_execution_eligibility"]["execution_approved"] != "False":
            failures.append("final eligibility must not approve execution")

        summary = "\n".join(result.summary_lines)
        for expected_text in [
            "EXECUTION ELIGIBILITY REPORT. RESEARCH ONLY. NOT EXECUTION.",
            "Execution eligible: False",
            "Strategy disagreement blocks execution discussion.",
            "No runtime paper kill-switch enforcement exists yet.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "Saved execution eligibility report",
        ]:
            if expected_text not in summary:
                failures.append(f"summary missing expected text: {expected_text}")


def verify_missing_inputs(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_minimal_bot_help(root)
        result = generate_execution_eligibility_report(root)
        checks = {row["eligibility_check_name"]: row for row in result.rows}
        for check in [
            "promoted_decision_approval",
            "promoted_strategy_disagreement",
            "portfolio_risk_policy_blockers",
            "kill_switch_readiness",
            "deployment_readiness",
        ]:
            if checks[check]["eligibility_status"] != "missing_input":
                failures.append(f"{check} should be missing_input when saved CSV is absent")
        summary = "\n".join(result.summary_lines)
        for command in eligibility.REQUIRED_INPUT_COMMANDS:
            if command not in summary:
                failures.append(f"missing-input summary should mention {command}")


def verify_execution_approved_true_blocks(failures: list[str]) -> None:
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
        result = generate_execution_eligibility_report(root)
        checks = {row["eligibility_check_name"]: row for row in result.rows}
        if checks["promoted_decision_approval"]["eligibility_status"] != "blocked_for_review":
            failures.append("execution_approved=True promoted decision should block approval check")
        if "execution_approved=True" not in checks["promoted_decision_approval"]["finding"]:
            failures.append("execution_approved=True finding should be explicit")


def verify_source_safety(failures: list[str]) -> None:
    source = inspect.getsource(eligibility)
    runner_source = inspect.getsource(research_reports.run_execution_eligibility_report_command)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"execution eligibility report should not reference {token}")
        if token in runner_source:
            failures.append(f"execution eligibility runner should not reference {token}")


def write_fixture_project(root: Path) -> None:
    write_minimal_bot_help(root)
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
                "ticker": "SPY",
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
        root / "data" / "portfolio_risk_policy_report.csv",
        [
            {
                "risk_policy_name": "strategy_disagreement_policy",
                "risk_policy_status": "blocked_for_review",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            }
        ],
    )
    write_csv(
        root / "data" / "paper_kill_switch_readiness_report.csv",
        [
            {
                "check_name": "no_existing_kill_switch_enforcement",
                "check_status": "not_implemented_future_work",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            },
            {
                "check_name": "future_execution_integration_needed",
                "check_status": "not_implemented_future_work",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            },
            {
                "check_name": "required_future_tests",
                "check_status": "not_implemented_future_work",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            },
            {
                "check_name": "high_risk_commands_still_gated",
                "check_status": "pass",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            },
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


def write_minimal_bot_help(root: Path) -> None:
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "bot.py").write_text(
        'parser.add_argument("--paper-order-test")\n'
        'parser.add_argument("--confirm-paper-order")\n'
        'parser.add_argument("--execute-slow-sma-paper")\n'
        'parser.add_argument("--confirm-slow-sma-paper")\n',
        encoding="utf-8",
    )


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
