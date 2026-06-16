from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "qqq100_paper_execution_readiness_report.py"
COMMANDS = [
    "--qqq100-paper-execution-readiness-report",
    "--show-qqq100-paper-execution-readiness-report",
]
OUTPUTS = [
    "data/qqq100_paper_execution_readiness_report.csv",
    "data/qqq100_paper_execution_readiness_summary.csv",
    "data/qqq100_paper_execution_readiness_evidence.csv",
    "data/qqq100_paper_execution_readiness_blockers.csv",
]
SAFETY_COLUMNS = [
    "research_only",
    "report_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "qqq100_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "alpaca_called",
]
FORBIDDEN_SOURCE_PATTERNS = [
    "TradingClient",
    "get_open_position",
    "get_alpaca_positions",
    "submit_order",
    "cancel_order",
    "replace_order",
    "MarketOrderRequest",
    "LimitOrderRequest",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "load_config(",
    "yf.download",
    "yfinance",
    "download_backtest_prices",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
    "--execute-qqq100-paper",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)

    verify_command_registered(bot_source, failures)
    verify_source_safety(module_source, bot_source, failures)
    verify_outputs_ignored(failures)
    verify_saved_output_fixture(failures)

    if failures:
        print("QQQ100 paper execution readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 paper execution readiness verification passed.")
    print("Verified saved-output-only report/display, smoke-test evidence recognition, QQQ100 preview/action/promoted evidence, false approvals, blocked execution/scheduling, and no QQQ100 execution command.")
    return 0


def verify_command_registered(bot_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command in bot.py: {command}")
    early_route = bot_source.find('["--qqq100-paper-execution-readiness-report"]')
    broker_import = bot_source.find("from alpaca.trading.client import TradingClient")
    if early_route == -1:
        failures.append("missing early route for QQQ100 paper execution readiness report")
    elif broker_import != -1 and early_route > broker_import:
        failures.append("QQQ100 paper execution readiness report should route before broker imports")


def verify_source_safety(module_source: str, bot_source: str, failures: list[str]) -> None:
    required = [
        "qqq100_ready_for_manual_execution_design_review",
        "qqq100_needs_more_readiness_inputs",
        "qqq100_execution_design_blocked",
        "qqq100_insufficient_saved_evidence",
        "smoke_test_success_confirmed",
        "qqq100_preview_chain_ready",
        "qqq100_promoted_preview_present",
        "portfolio_overlap_review_required",
        "sizing_policy_not_approved",
        "qqq100_execution_command_not_added",
        "qqq100_kill_switch_required",
        "qqq100_postcheck_required",
        "execution_blocked",
        "scheduling_not_approved",
        *OUTPUTS,
        *SAFETY_COLUMNS,
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")
    for pattern in FORBIDDEN_SOURCE_PATTERNS:
        if pattern in module_source:
            failures.append(f"module must not contain forbidden source pattern: {pattern}")
    if "--execute-qqq100-paper" in bot_source:
        failures.append("bot.py must not add a QQQ100 execution command")
    if "submit_alpaca_order(" in module_source:
        failures.append("readiness report must not call lower-level order submission")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(["git", "check-ignore", output], cwd=ROOT, text=True, capture_output=True, timeout=10)
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_saved_output_fixture(failures: list[str]) -> None:
    from trading_bot.research.qqq100_paper_execution_readiness_report import (  # noqa: PLC0415
        generate_qqq100_paper_execution_readiness_report,
        show_qqq100_paper_execution_readiness_report,
    )

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "paper_order_smoke_test_postcheck.csv",
            [
                {
                    "check_name": "final_postcheck_status",
                    "check_status": "postcheck_order_observed_filled_manual_review",
                    "recent_order_match_found": "true",
                    "recent_order_match_status": "filled",
                    "recent_order_match_count": "1",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                }
            ],
        )
        write_csv(data / "paper_order_smoke_test_gate_report.csv", [{"gate_status": "allowed", "orders_submitted": "True"}])
        write_csv(data / "paper_order_smoke_test_live_preflight.csv", [{"check_name": "final_live_preflight_status", "check_status": "live_preflight_ready_for_manual_confirmation"}])
        write_csv(data / "alpaca_connectivity_diagnostics.csv", [{"endpoint": "paper-api.alpaca.markets", "diagnostic_status": "alpaca_api_reachable"}])
        write_csv(data / "qqq100_preview_signal_pack.csv", [{"ticker": "QQQ", "desired_position": "long", "trend_state": "above_sma100_trend_gate", "data_status": "ok"}])
        write_csv(data / "qqq100_action_preview.csv", [{"ticker": "QQQ", "desired_position": "long", "preview_only": "True"}])
        write_csv(data / "promoted_strategy_preview.csv", [{"strategy_name": "qqq_100_trend_gate", "ticker": "QQQ", "preview_only": "True"}])
        write_csv(data / "promoted_decision_preview.csv", [{"decision_status": "preview_review_only"}])
        write_csv(data / "multi_strategy_portfolio_preview.csv", [{"sleeve_name": "qqq100_trend_sleeve", "strategy_name": "qqq_100_trend_gate"}])
        write_csv(data / "multi_strategy_portfolio_preview_conflicts.csv", [{"conflict_name": "growth_tech_overlap_warning", "severity": "warning"}])
        write_csv(data / "portfolio_risk_policy_report.csv", [{"policy_name": "sizing", "execution_approved": "False"}])
        write_csv(data / "execution_eligibility_report.csv", [{"eligibility_check_name": "final_execution_eligibility", "execution_approved": "False"}])
        write_csv(data / "paper_kill_switch_readiness_report.csv", [{"check_name": "kill_switch", "execution_approved": "False"}])
        write_csv(data / "paper_kill_switch_gate_report.csv", [{"gate_name": "paper_kill_switch", "execution_approved": "False"}])
        write_csv(data / "paper_execution_protection_report.csv", [{"check_name": "protection", "execution_approved": "False"}])
        write_csv(data / "project_research_state_summary.csv", [{"summary_name": "stock_etf_lead", "summary_value": "qqq_100_trend_gate"}])

        result = generate_qqq100_paper_execution_readiness_report(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_readiness_status") != "qqq100_ready_for_manual_execution_design_review":
            failures.append("fixture should be ready for manual execution-design review only")
        if summary.get("smoke_test_status") != "smoke_test_success_confirmed":
            failures.append("successful AAPL smoke-test postcheck was not recognised")
        if summary.get("qqq100_preview_status") != "qqq100_preview_chain_ready":
            failures.append("QQQ100 preview signal was not recognised")
        if summary.get("qqq100_action_preview_status") != "qqq100_action_preview_present":
            failures.append("QQQ100 action preview was not recognised")
        if summary.get("promoted_preview_status") != "qqq100_promoted_preview_present":
            failures.append("QQQ100 promoted preview row was not recognised")
        if summary.get("portfolio_overlap_warning_status") != "portfolio_overlap_review_required":
            failures.append("portfolio overlap warning was not surfaced")
        for output in OUTPUTS:
            rows = read_csv(root / output)
            if not rows:
                failures.append(f"fixture did not write rows for {output}")
                continue
            for column in SAFETY_COLUMNS:
                if column not in rows[0]:
                    failures.append(f"{output} missing safety column: {column}")
            for false_flag in [
                "execution_approved",
                "paper_execution_approved",
                "qqq100_execution_approved",
                "scheduling_approved",
                "orders_created",
                "orders_submitted",
                "orders_cancelled",
                "sqlite_trade_log_written",
                "discord_alert_sent",
                "telegram_alert_sent",
                "alpaca_called",
            ]:
                if any(row.get(false_flag, "").lower() != "false" for row in rows):
                    failures.append(f"{false_flag} must remain false for every row in {output}")
        report_text = " ".join(str(value) for row in result.report_rows for value in row.values())
        if "high_growth_branch_research_only_excluded" not in report_text:
            failures.append("high-growth branch exclusion should be represented")
        if "crypto_research_only_excluded" not in report_text:
            failures.append("crypto exclusion should be represented")
        code, lines = show_qqq100_paper_execution_readiness_report(root)
        if code != 0 or not any("execution_approved=false" in line for line in lines):
            failures.append("saved display should succeed and print false execution flags")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


if __name__ == "__main__":
    raise SystemExit(main())
