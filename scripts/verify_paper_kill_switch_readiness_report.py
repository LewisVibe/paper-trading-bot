from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.paper_kill_switch as kill_switch
from trading_bot.research.paper_kill_switch import generate_paper_kill_switch_readiness_report
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
        print("Paper kill-switch readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper kill-switch readiness verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture_project(root)
        result = generate_paper_kill_switch_readiness_report(root)
        if not result.output_path.exists():
            failures.append("paper_kill_switch_readiness_report.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != kill_switch.PAPER_KILL_SWITCH_READINESS_COLUMNS:
                failures.append("paper kill-switch readiness columns changed unexpectedly")
            rows = list(reader)
        if len(rows) < 12:
            failures.append("paper kill-switch readiness report should include all expected checks")
        for row in rows:
            if row["research_only"] != "True" or row["preview_only"] != "True" or row["execution_approved"] != "False":
                failures.append(f"safety flags failed for {row['check_name']}")

        checks = {row["check_name"]: row for row in rows}
        for required in [
            "paper_only_boundary",
            "dry_run_default_boundary",
            "allow_shorting_boundary",
            "high_risk_commands_still_gated",
            "normal_execution_path_not_modified",
            "no_existing_kill_switch_enforcement",
            "future_config_design_needed",
            "future_execution_integration_needed",
            "future_preview_surface_needed",
            "promoted_decision_state",
            "portfolio_risk_policy_state",
            "safe_scheduling_boundary",
            "required_future_tests",
        ]:
            if required not in checks:
                failures.append(f"missing readiness check: {required}")

        if checks["promoted_decision_state"]["check_status"] != "blocked_for_review":
            failures.append("strategy disagreement fixture should block promoted_decision_state")
        if "AAPL" not in checks["promoted_decision_state"]["finding"]:
            failures.append("promoted decision blocker should identify AAPL")
        for future_check in [
            "no_existing_kill_switch_enforcement",
            "future_config_design_needed",
            "future_execution_integration_needed",
            "future_preview_surface_needed",
            "portfolio_risk_policy_state",
            "required_future_tests",
        ]:
            if checks[future_check]["check_status"] != "not_implemented_future_work":
                failures.append(f"{future_check} should be labelled not_implemented_future_work")

        summary = "\n".join(result.summary_lines)
        for expected_text in [
            "PAPER KILL-SWITCH READINESS REPORT. REPORTING ONLY. NOT EXECUTION.",
            "No kill-switch enforcement was added.",
            "No order path was changed.",
            "No execution approval was granted.",
            "Saved paper kill-switch readiness report",
        ]:
            if expected_text not in summary:
                failures.append(f"summary missing expected text: {expected_text}")


def verify_missing_saved_csvs(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_minimal_static_project(root)
        result = generate_paper_kill_switch_readiness_report(root)
        checks = {row["check_name"]: row for row in result.rows}
        if checks["promoted_decision_state"]["check_status"] != "not_applicable":
            failures.append("missing promoted decision CSV should be handled as not_applicable")
        if checks["portfolio_risk_policy_state"]["check_status"] != "not_applicable":
            failures.append("missing portfolio risk policy CSV should be handled as not_applicable")


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
        result = generate_paper_kill_switch_readiness_report(root)
        checks = {row["check_name"]: row for row in result.rows}
        if checks["promoted_decision_state"]["check_status"] != "blocked_for_review":
            failures.append("execution_approved=True fixture should block promoted_decision_state")
        if checks["portfolio_risk_policy_state"]["check_status"] != "blocked_for_review":
            failures.append("execution_approved=True fixture should block portfolio_risk_policy_state")


def verify_source_safety(failures: list[str]) -> None:
    source = inspect.getsource(kill_switch)
    runner_source = inspect.getsource(research_reports.run_paper_kill_switch_readiness_report_command)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"paper kill-switch readiness should not reference {token}")
        if token in runner_source:
            failures.append(f"paper kill-switch readiness runner should not reference {token}")
    if "paper_kill_switch_enabled" in source and "this report does not add it" not in source:
        failures.append("paper kill-switch readiness must not add a runtime config setting")


def write_fixture_project(root: Path) -> None:
    write_minimal_static_project(root)
    write_csv(
        root / "data" / "promoted_decision_preview.csv",
        [
            {
                "ticker": "AAPL",
                "decision_state": "blocked_strategy_disagreement",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            }
        ],
    )
    write_csv(
        root / "data" / "portfolio_risk_policy_report.csv",
        [
            {
                "risk_policy_name": "kill_switch_policy",
                "risk_policy_status": "not_implemented_future_work",
                "execution_approved": "False",
                "research_only": "True",
                "preview_only": "True",
            }
        ],
    )


def write_minimal_static_project(root: Path) -> None:
    (root / "trading_bot").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "config.example.json").write_text(
        '{"dry_run": true, "allow_shorting": false, "alpaca": {"paper": true}}\n',
        encoding="utf-8",
    )
    (root / "trading_bot" / "config.py").write_text(
        'parse_config_bool(raw, "dry_run", True)\n'
        'parse_config_bool(raw, "allow_shorting", False)\n'
        'raise ConfigError("alpaca.paper must be true")\n',
        encoding="utf-8",
    )
    (root / "bot.py").write_text(
        'parser.add_argument("--paper-order-test")\n'
        'parser.add_argument("--confirm-paper-order")\n'
        'parser.add_argument("--execute-slow-sma-paper")\n'
        'parser.add_argument("--confirm-slow-sma-paper")\n',
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "Do not schedule execution-capable commands. --paper-order-test --execute-slow-sma-paper\n",
        encoding="utf-8",
    )
    (root / "docs" / "VPS_SETUP_CHECKLIST.md").write_text(
        "Commands Never To Schedule Automatically\n"
        "Do not schedule python bot.py --paper-order-test or python bot.py --execute-slow-sma-paper\n",
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
