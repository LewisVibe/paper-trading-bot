from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.paper_execution_protection as paper_execution_protection
from trading_bot.research.paper_execution_protection import (
    PAPER_EXECUTION_PROTECTION_COLUMNS,
    generate_paper_execution_protection_report,
)


EXPECTED_EXECUTION_PATHS = {
    "manual_paper_order_test",
    "slow_sma_paper_execution",
    "normal_bot_order_path",
    "execution_readiness",
    "overall_protection_state",
}

FORBIDDEN_OUTPUT_COLUMNS = {
    "side",
    "quantity",
    "order_type",
    "order_id",
    "target_order",
    "submit" + "_order",
}

FORBIDDEN_SOURCE_TERMS = [
    "yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit" + "_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_simulated_positions",
    "decide_trade",
    "download_close_prices",
    "download_backtest_prices",
    "configure_yfinance_cache",
    "sqlite3",
]


def main() -> int:
    failures: list[str] = []
    verify_fixture_report(failures)
    verify_static_safety(failures)
    verify_command_registered(failures)

    if failures:
        print("Paper execution protection report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper execution protection report verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        write_fixture_files(root)
        result = generate_paper_execution_protection_report(
            root_dir=root,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.output_path.name != "paper_execution_protection_report.csv":
            failures.append("output path should be paper_execution_protection_report.csv")
        if not result.output_path.exists():
            failures.append("paper execution protection report CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            fieldnames = csv.DictReader(file).fieldnames
        if fieldnames != PAPER_EXECUTION_PROTECTION_COLUMNS:
            failures.append("paper execution protection columns changed unexpectedly")
        if FORBIDDEN_OUTPUT_COLUMNS.intersection(PAPER_EXECUTION_PROTECTION_COLUMNS):
            failures.append("protection report schema contains order-instruction columns")

        paths = {row.get("execution_path") for row in result.rows}
        if paths != EXPECTED_EXECUTION_PATHS:
            failures.append(f"expected execution path rows changed: {sorted(str(path) for path in paths)}")

        statuses = {row.get("execution_path"): row.get("protection_status") for row in result.rows}
        if statuses.get("manual_paper_order_test") != "protected_by_kill_switch_preflight":
            failures.append("manual paper-order test should be protected by kill-switch preflight")
        if statuses.get("slow_sma_paper_execution") != "protected_by_kill_switch_preflight":
            failures.append("slow SMA paper execution should be protected by kill-switch preflight")
        if statuses.get("normal_bot_order_path") != "deliberately_unchanged_future_work":
            failures.append("normal bot order path should remain deliberately unchanged/future work")
        if statuses.get("execution_readiness") != "blocked":
            failures.append("execution readiness should remain blocked")
        if statuses.get("overall_protection_state") != "explicit_paper_paths_protected_but_execution_blocked":
            failures.append("overall protection state should remain protected-but-blocked")

        for row in result.rows:
            if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
                failures.append(f"safety flags failed for execution path {row.get('execution_path')}")
            if row.get("execution_approved") is True:
                failures.append(f"execution should never be approved for {row.get('execution_path')}")

        summary = "\n".join(result.summary_lines)
        for expected in [
            "PAPER EXECUTION PROTECTION REPORT. SAVED-DATA/STATIC CHECK ONLY. NOT EXECUTION.",
            "No execution design was added.",
            "No additional order paths were wired.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "paper_execution_protection_report.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected safety text: {expected}")


def verify_static_safety(failures: list[str]) -> None:
    source = inspect.getsource(paper_execution_protection)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"paper execution protection report references forbidden term: {term}")
    if "paper_execution_protection_report.csv" not in source:
        failures.append("report source should reference output path")
    for expected in EXPECTED_EXECUTION_PATHS:
        if expected not in source:
            failures.append(f"report source should mention execution path {expected}")


def verify_command_registered(failures: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (result.stdout or "") + "\n" + (result.stderr or "")
    if "--paper-execution-protection-report" not in help_text:
        failures.append("command inventory should include --paper-execution-protection-report")


def write_fixture_files(root: Path) -> None:
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "bot.py").write_text(
        "\n".join(
            [
                "def run_bot():",
                "    pass",
                "",
                "def run_paper_order_test():",
                "    evaluate_paper_kill_switch_gate()",
                "    init_database()",
                "    TradingClient()",
                "    submit_alpaca_order()",
                "",
                "def estimate_manual_position_after():",
                "    pass",
                "",
                "def run_slow_sma_paper_execution():",
                "    evaluate_paper_kill_switch_gate()",
                "    configure_yfinance_cache()",
                "    init_database()",
                "    send_discord_alert()",
                "    TradingClient()",
                "    get_alpaca_positions()",
                "    process_slow_sma_execution_ticker()",
                "",
                "def validate_slow_sma_execution_safety():",
                "    pass",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_csv(
        root / "data" / "paper_kill_switch_gate_report.csv",
        [
            {
                "gate_check": "manual_paper_order_test_kill_switch_preflight",
                "gate_status": "pass",
                "blocks_future_execution_design": "False",
                "execution_approved": "False",
            },
            {
                "gate_check": "slow_sma_paper_execution_kill_switch_preflight",
                "gate_status": "pass",
                "blocks_future_execution_design": "False",
                "execution_approved": "False",
            },
            {
                "gate_check": "normal_bot_order_path_kill_switch_preflight_missing",
                "gate_status": "future_work_required",
                "blocks_future_execution_design": "True",
                "execution_approved": "False",
            },
        ],
    )
    write_csv(
        root / "data" / "defensive_execution_readiness_report.csv",
        [
            {
                "readiness_area": "overall_readiness",
                "readiness_status": "blocked",
                "can_progress_to_execution_design": "False",
                "execution_approved": "False",
            }
        ],
    )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
