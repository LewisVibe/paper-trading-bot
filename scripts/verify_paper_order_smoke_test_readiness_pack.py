from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_order_smoke_test_readiness.py"
COMMAND = "--paper-order-smoke-test-readiness-pack"
OUTPUT = "data/paper_order_smoke_test_readiness_pack.csv"

REQUIRED_TOKENS = [
    OUTPUT,
    "smoke_test_discussion_blocked",
    "smoke_test_discussion_needs_manual_review",
    "smoke_test_discussion_ready_for_explicit_manual_confirmation",
    "proposed_manual_review_only",
    "order_execution_approved",
    "execution_approved",
    "scheduling_approved",
    "run_command_now",
    "alpaca_called",
    "Warning: this summary intentionally does not print a paper-order command.",
]

FORBIDDEN_SOURCE_PATTERNS = [
    "TradingClient",
    ".get_account(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "MarketOrderRequest(",
    "LimitOrderRequest(",
    "StopOrderRequest(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "download_close_prices(",
    "download_backtest_prices(",
    "yf.download(",
    "yfinance.download(",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab -e",
    "systemctl enable",
]

PASTEABLE_COMMAND_PATTERNS = [
    "python bot.py --paper-order-test",
    ".venv\\Scripts\\python.exe bot.py --paper-order-test",
]


def main() -> int:
    failures: list[str] = []
    verify_command_registered(failures)
    verify_module_source(failures)
    verify_generated_output_ignored(failures)
    verify_fixture_run(failures)

    if failures:
        print("Paper-order smoke-test readiness pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-order smoke-test readiness pack verification passed.")
    print("Verified command, ignored output, static/no-Alpaca behaviour, false approval flags, no order/alert/scheduler calls, and no pasteable order command in terminal summary.")
    return 0


def verify_command_registered(failures: list[str]) -> None:
    source = read_text(BOT)
    if COMMAND not in source:
        failures.append(f"{COMMAND} is missing from bot.py")
    early_route_index = source.find(f'sys.argv[1:] == ["{COMMAND}"]')
    alpaca_import_index = source.find("from alpaca.trading.client import TradingClient")
    if early_route_index == -1:
        failures.append("missing exact early route for paper-order smoke-test readiness pack")
    elif alpaca_import_index != -1 and early_route_index > alpaca_import_index:
        failures.append("paper-order smoke-test readiness route should be before broker imports")
    branch_index = source.find("if args.paper_order_smoke_test_readiness_pack:")
    load_config_index = source.find("config = load_config(")
    if branch_index == -1:
        failures.append("missing argparse branch for paper-order smoke-test readiness pack")
    elif load_config_index != -1 and branch_index > load_config_index:
        failures.append("paper-order smoke-test readiness pack must route before normal config loading")


def verify_module_source(failures: list[str]) -> None:
    source = read_text(MODULE)
    for token in REQUIRED_TOKENS:
        if token not in source:
            failures.append(f"missing readiness-pack token: {token}")
    for pattern in FORBIDDEN_SOURCE_PATTERNS:
        if pattern in source:
            failures.append(f"forbidden execution/config/alert/scheduler pattern in pack: {pattern}")
    for pattern in PASTEABLE_COMMAND_PATTERNS:
        if pattern in source:
            failures.append(f"pack source must not include pasteable paper-order command: {pattern}")
    if "limit=80" not in source:
        failures.append("pack should read saved CSVs with a conservative row limit")


def verify_generated_output_ignored(failures: list[str]) -> None:
    completed = subprocess.run(
        ["git", "check-ignore", OUTPUT],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        failures.append(f"generated output is not ignored by git: {OUTPUT}")


def verify_fixture_run(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture(root)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        code = (
            "from trading_bot.research.paper_order_smoke_test_readiness import "
            "generate_paper_order_smoke_test_readiness_pack; "
            "r=generate_paper_order_smoke_test_readiness_pack(r'.'); "
            "print('\\n'.join(r.summary_lines))"
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0:
            failures.append(f"fixture run should not fail: {completed.stderr.strip()}")
            return
        for pattern in PASTEABLE_COMMAND_PATTERNS:
            if pattern in completed.stdout:
                failures.append(f"terminal summary printed pasteable order command: {pattern}")
        output = root / OUTPUT
        if not output.exists():
            failures.append("fixture run did not write expected readiness pack CSV")
            return
        with output.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            failures.append("fixture readiness pack wrote no rows")
            return
        for column in ["order_execution_approved", "execution_approved", "scheduling_approved", "run_command_now", "alpaca_called"]:
            if not all(str(row.get(column, "")).lower() == "false" for row in rows):
                failures.append(f"{column} must remain false for every row")
        final = next((row for row in rows if row.get("check_name") == "final_smoke_test_discussion_status"), {})
        if final.get("check_status") != "smoke_test_discussion_needs_manual_review":
            failures.append(f"fixture final status should need manual review, got {final.get('check_status')}")
        proposal = next((row for row in rows if row.get("check_name") == "proposed_future_manual_smoke_test_template"), {})
        if proposal.get("proposed_ticker") != "AAPL" or proposal.get("proposed_side") != "buy" or proposal.get("proposed_quantity") != "1":
            failures.append("proposal row should include conservative AAPL buy 1 manual-review-only template")


def write_fixture(root: Path) -> None:
    (root / "data").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "config.example.json").write_text(
        '{"dry_run": true, "allow_shorting": false, "alpaca": {"paper": true}}',
        encoding="utf-8",
    )
    (root / "bot.py").write_text(
        "--paper-order-test --confirm-paper-order confirm_paper_order "
        "Re-run with --confirm-paper-order",
        encoding="utf-8",
    )
    hermes = (
        "paper-bot-vps-status-check --vps-daily-monitoring-summary "
        "does not run refresh commands paper-order high-risk/manual-only"
    )
    for name in ["HERMES_CRON_JOB_DESIGN.md", "HERMES_TASK_BOARD.md", "CURRENT_STATE.md"]:
        (root / "docs" / name).write_text(hermes, encoding="utf-8")
    write_csv(
        root / "data" / "alpaca_paper_readiness_report.csv",
        ["check_name", "check_status"],
        [
            {"check_name": "final_readiness_status", "check_status": "alpaca_paper_readonly_check_passed_manual_smoke_test_next"},
        ],
    )
    write_csv(
        root / "data" / "stock_etf_paper_execution_readiness_report.csv",
        ["check_name", "check_status"],
        [
            {"check_name": "final_paper_execution_discussion_status", "check_status": "paper_execution_discussion_blocked_by_cost_review_and_execution_gates"},
        ],
    )
    write_csv(
        root / "data" / "project_research_state_summary.csv",
        ["metric_name", "metric_value"],
        [
            {"metric_name": "stock_etf_active_research_lead", "metric_value": "codex_ambitious_concentrated_growth_persistence"},
            {"metric_name": "stock_etf_status_and_blocker", "metric_value": "research_only_cost_review_required"},
            {"metric_name": "crypto_status_and_blockers", "metric_value": "crypto_manual_review_not_ready"},
        ],
    )
    write_csv(root / "data" / "project_research_state_next_steps.csv", ["check_name"], [{"check_name": "manual_review"}])
    write_csv(root / "data" / "execution_eligibility_report.csv", ["eligibility_status"], [{"eligibility_status": "pass"}])
    write_csv(root / "data" / "paper_execution_protection_report.csv", ["protection_status"], [{"protection_status": "pass"}])
    write_csv(root / "data" / "paper_kill_switch_gate_report.csv", ["gate_status"], [{"gate_status": "pass"}])


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
