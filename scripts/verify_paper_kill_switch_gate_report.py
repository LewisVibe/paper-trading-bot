from __future__ import annotations

import csv
import inspect
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.paper_kill_switch_gate as paper_kill_switch_gate
from trading_bot.research.paper_kill_switch_gate import (
    PAPER_KILL_SWITCH_GATE_COLUMNS,
    generate_paper_kill_switch_gate_report,
)


EXPECTED_GATE_CHECKS = {
    "config_example_dry_run_default_true",
    "config_example_alpaca_paper_default_true",
    "config_example_allow_shorting_default_false",
    "high_risk_commands_confirmation_gated",
    "existing_kill_switch_readiness_available",
    "kill_switch_enforcement_not_implemented",
    "defensive_allocation_decision_blocks_execution_design",
    "execution_eligibility_blocks_execution",
    "future_execution_requires_kill_switch_gate",
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

    if failures:
        print("Paper kill-switch gate report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper kill-switch gate report verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        write_fixture_files(root)
        result = generate_paper_kill_switch_gate_report(
            root_dir=root,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.output_path.name != "paper_kill_switch_gate_report.csv":
            failures.append("output path should be paper_kill_switch_gate_report.csv")
        if not result.output_path.exists():
            failures.append("paper kill-switch gate report CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            fieldnames = csv.DictReader(file).fieldnames
        if fieldnames != PAPER_KILL_SWITCH_GATE_COLUMNS:
            failures.append("paper kill-switch gate columns changed unexpectedly")
        if FORBIDDEN_OUTPUT_COLUMNS.intersection(PAPER_KILL_SWITCH_GATE_COLUMNS):
            failures.append("paper kill-switch gate schema contains order-instruction columns")

        checks = {row.get("gate_check") for row in result.rows}
        if checks != EXPECTED_GATE_CHECKS:
            failures.append(f"expected gate checks changed: {sorted(str(check) for check in checks)}")
        statuses = {row.get("gate_check"): row.get("gate_status") for row in result.rows}
        if statuses.get("kill_switch_enforcement_not_implemented") != "future_work_required":
            failures.append("kill-switch enforcement should be marked future_work_required")
        if statuses.get("future_execution_requires_kill_switch_gate") != "blocked":
            failures.append("future execution should remain blocked by kill-switch gate")
        blockers = [
            row
            for row in result.rows
            if row.get("blocks_future_execution_design") is True
        ]
        if not blockers:
            failures.append("fixture should block future execution design")
        verify_safety_flags(result.rows, failures)

        summary = "\n".join(result.summary_lines)
        for expected in [
            "PAPER KILL-SWITCH GATE REPORT. DESIGN/REPORT ONLY. NOT EXECUTION.",
            "No enforcement was added to order paths.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "paper_kill_switch_gate_report.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected safety text: {expected}")


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--paper-kill-switch-gate-report" not in help_text:
        failures.append("command inventory should include --paper-kill-switch-gate-report")
    source = inspect.getsource(paper_kill_switch_gate)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"paper kill-switch gate report references forbidden term: {term}")


def verify_safety_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"safety flags failed for gate check {row.get('gate_check')}")


def write_fixture_files(root: Path) -> None:
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "config.example.json").write_text(
        json.dumps(
            {
                "dry_run": True,
                "allow_shorting": False,
                "alpaca": {"paper": True, "api_key": "", "secret_key": ""},
            }
        ),
        encoding="utf-8",
    )
    write_csv(
        root / "data" / "paper_kill_switch_readiness_report.csv",
        [
            {
                "check_name": "no_existing_kill_switch_enforcement",
                "check_status": "not_implemented_future_work",
                "execution_approved": "False",
            }
        ],
    )
    write_csv(
        root / "data" / "defensive_allocation_decision_report.csv",
        [
            {
                "decision_area": "overall_decision",
                "decision_label": "blocked_not_ready_for_execution_design",
                "can_progress_to_execution_design": "False",
                "execution_approved": "False",
            }
        ],
    )
    write_csv(
        root / "data" / "execution_eligibility_report.csv",
        [
            {
                "eligibility_check_name": "final_execution_eligibility",
                "eligibility_status": "blocked_for_review",
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
