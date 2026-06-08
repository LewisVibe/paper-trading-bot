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

import trading_bot.research.defensive_execution_readiness as defensive_execution_readiness
from trading_bot.research.defensive_execution_readiness import (
    DEFENSIVE_EXECUTION_READINESS_COLUMNS,
    generate_defensive_execution_readiness_report,
)


EXPECTED_AREAS = {
    "defensive_lead_reference",
    "allocation_preview_safety",
    "allocation_risk_blockers",
    "defensive_allocation_decision",
    "paper_kill_switch_gate",
    "kill_switch_contract_verifier",
    "execution_eligibility",
    "portfolio_risk_policy",
    "overall_readiness",
    "next_gate",
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
    verify_missing_inputs(failures)
    verify_static_safety(failures)

    if failures:
        print("Defensive execution readiness report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Defensive execution readiness report verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        script_dir = root / "scripts"
        data_dir.mkdir(parents=True, exist_ok=True)
        script_dir.mkdir(parents=True, exist_ok=True)
        (script_dir / "verify_paper_kill_switch_enforcement_contract.py").write_text("# fixture\n", encoding="utf-8")
        write_fixture_csvs(data_dir)
        result = generate_defensive_execution_readiness_report(
            data_dir=data_dir,
            script_dir=script_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.output_path.name != "defensive_execution_readiness_report.csv":
            failures.append("output path should be defensive_execution_readiness_report.csv")
        if not result.output_path.exists():
            failures.append("defensive execution readiness report CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            fieldnames = csv.DictReader(file).fieldnames
        if fieldnames != DEFENSIVE_EXECUTION_READINESS_COLUMNS:
            failures.append("defensive execution readiness columns changed unexpectedly")
        if FORBIDDEN_OUTPUT_COLUMNS.intersection(DEFENSIVE_EXECUTION_READINESS_COLUMNS):
            failures.append("readiness schema contains order-instruction columns")
        areas = {row.get("readiness_area") for row in result.rows}
        if areas != EXPECTED_AREAS:
            failures.append(f"expected readiness areas changed: {sorted(str(area) for area in areas)}")
        overall = find_row(result.rows, "overall_readiness")
        if overall.get("readiness_status") != "blocked":
            failures.append("fixture overall readiness should be blocked")
        if overall.get("can_progress_to_execution_design") is not False:
            failures.append("fixture should not progress to execution design")
        contract = find_row(result.rows, "kill_switch_contract_verifier")
        if contract.get("readiness_status") != "pass":
            failures.append("contract verifier presence should pass as spec coverage only")
        verify_safety_flags(result.rows, failures)

        summary = "\n".join(result.summary_lines)
        for expected in [
            "DEFENSIVE EXECUTION READINESS REPORT. SAVED-DATA ONLY. NOT EXECUTION.",
            "No execution design was added.",
            "No enforcement was added to order paths.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "defensive_execution_readiness_report.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected safety text: {expected}")


def verify_missing_inputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        script_dir = root / "scripts"
        data_dir.mkdir(parents=True, exist_ok=True)
        script_dir.mkdir(parents=True, exist_ok=True)
        result = generate_defensive_execution_readiness_report(
            data_dir=data_dir,
            script_dir=script_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        overall = find_row(result.rows, "overall_readiness")
        if overall.get("readiness_status") != "blocked":
            failures.append("missing inputs should block overall readiness")
        if overall.get("can_progress_to_execution_design") is not False:
            failures.append("missing inputs should not progress to execution design")
        verify_safety_flags(result.rows, failures)


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--defensive-execution-readiness-report" not in help_text:
        failures.append("command inventory should include --defensive-execution-readiness-report")
    source = inspect.getsource(defensive_execution_readiness)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"defensive execution readiness report references forbidden term: {term}")


def verify_safety_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"safety flags failed for readiness area {row.get('readiness_area')}")


def find_row(rows: list[dict[str, object]], readiness_area: str) -> dict[str, object]:
    return next((row for row in rows if row.get("readiness_area") == readiness_area), {})


def write_fixture_csvs(data_dir: Path) -> None:
    write_csv(
        data_dir / "defensive_allocation_preview.csv",
        [
            {"component": "monthly_etf_momentum_rotation", "preview_label": "lead_reference", "execution_approved": "False"},
        ],
    )
    write_csv(
        data_dir / "defensive_allocation_decision_report.csv",
        [
            {
                "decision_area": "overall_decision",
                "decision_label": "blocked_not_ready_for_execution_design",
                "can_progress_to_execution_design": "False",
                "execution_approved": "False",
            },
            {
                "decision_area": "preview_safety",
                "decision_label": "preview_safe_non_executable",
                "can_progress_to_execution_design": "False",
                "execution_approved": "False",
            },
        ],
    )
    write_csv(
        data_dir / "defensive_allocation_risk_preview.csv",
        [
            {"risk_check": "no_execution_approved_rows", "risk_status": "pass", "blocker": "False", "execution_approved": "False"},
            {"risk_check": "execution_gate_blocked", "risk_status": "blocked", "blocker": "True", "execution_approved": "False"},
        ],
    )
    write_csv(
        data_dir / "paper_kill_switch_gate_report.csv",
        [
            {
                "gate_check": "kill_switch_enforcement_not_implemented",
                "gate_status": "future_work_required",
                "blocks_future_execution_design": "True",
                "execution_approved": "False",
            },
            {
                "gate_check": "future_execution_requires_kill_switch_gate",
                "gate_status": "blocked",
                "blocks_future_execution_design": "True",
                "execution_approved": "False",
            },
        ],
    )
    write_csv(
        data_dir / "execution_eligibility_report.csv",
        [
            {
                "eligibility_check_name": "final_execution_eligibility",
                "eligibility_status": "blocked_for_review",
                "execution_approved": "False",
            },
        ],
    )
    write_csv(
        data_dir / "portfolio_risk_policy_report.csv",
        [
            {
                "risk_policy_name": "strategy_disagreement_policy",
                "risk_policy_status": "blocked_for_review",
                "execution_approved": "False",
            },
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
