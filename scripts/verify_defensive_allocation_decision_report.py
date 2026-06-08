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

import trading_bot.research.defensive_allocation_decision as defensive_allocation_decision
from trading_bot.research.defensive_allocation_decision import (
    DEFENSIVE_ALLOCATION_DECISION_COLUMNS,
    ORDER_INSTRUCTION_COLUMNS,
    generate_defensive_allocation_decision_report,
)


EXPECTED_DECISION_LABELS = {
    "blocked_not_ready_for_execution_design",
    "lead_defensive_reference_identified",
    "preview_safe_non_executable",
    "warnings_require_review",
    "blockers_prevent_execution_design",
    "kill_switch_and_execution_readiness_required",
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
    verify_missing_input(failures)
    verify_static_safety(failures)

    if failures:
        print("Defensive allocation decision report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Defensive allocation decision report verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_preview_fixture(data_dir / "defensive_allocation_preview.csv")
        write_risk_fixture(data_dir / "defensive_allocation_risk_preview.csv")
        result = generate_defensive_allocation_decision_report(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.output_path.name != "defensive_allocation_decision_report.csv":
            failures.append("output path should be defensive_allocation_decision_report.csv")
        if not result.output_path.exists():
            failures.append("defensive allocation decision report CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            fieldnames = csv.DictReader(file).fieldnames
        if fieldnames != DEFENSIVE_ALLOCATION_DECISION_COLUMNS:
            failures.append("defensive allocation decision columns changed unexpectedly")
        if ORDER_INSTRUCTION_COLUMNS.intersection(DEFENSIVE_ALLOCATION_DECISION_COLUMNS):
            failures.append("decision report schema contains order-instruction columns")

        labels = {row.get("decision_label") for row in result.rows}
        if labels != EXPECTED_DECISION_LABELS:
            failures.append(f"expected decision labels changed: {sorted(str(label) for label in labels)}")
        overall = find_row(result.rows, "overall_decision")
        if overall.get("decision_label") != "blocked_not_ready_for_execution_design":
            failures.append("overall decision should be blocked_not_ready_for_execution_design for blocked fixture")
        if overall.get("can_progress_to_execution_design") is not False:
            failures.append("blocked fixture should not progress to execution design")
        verify_safety_flags(result.rows, failures)

        summary = "\n".join(result.summary_lines)
        for expected in [
            "DEFENSIVE ALLOCATION DECISION REPORT. SAVED-DATA ONLY. NOT EXECUTION.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "defensive_allocation_decision_report.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected safety text: {expected}")


def verify_missing_input(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_defensive_allocation_decision_report(
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )
        overall = find_row(result.rows, "overall_decision")
        if overall.get("decision_label") != "missing_input":
            failures.append("missing inputs should produce missing_input overall decision")
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
    if "--defensive-allocation-decision-report" not in help_text:
        failures.append("command inventory should include --defensive-allocation-decision-report")
    source = inspect.getsource(defensive_allocation_decision)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"defensive allocation decision report references forbidden term: {term}")


def verify_safety_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"safety flags failed for decision area {row.get('decision_area')}")


def find_row(rows: list[dict[str, object]], decision_area: str) -> dict[str, object]:
    return next((row for row in rows if row.get("decision_area") == decision_area), {})


def write_preview_fixture(path: Path) -> None:
    write_csv(
        path,
        [
            {"component": "monthly_etf_momentum_rotation", "preview_label": "lead_reference"},
            {"component": "volatility_managed_dual_momentum_etf", "preview_label": "secondary_check_split_sensitive"},
            {"component": "etf_breadth_regime_allocation", "preview_label": "robust_diagnostic_filter_not_strategy"},
            {"component": "adaptive_risk_on_off_momentum", "preview_label": "secondary_complex_candidate"},
            {"component": "short_research", "preview_label": "paused_not_useful"},
            {"component": "execution_state", "preview_label": "blocked_no_execution_approval"},
        ],
        defaults={
            "created_at": "2026-01-01T00:00:00+00:00",
            "preview_category": "fixture",
            "source": "fixture",
            "desired_role": "fixture",
            "current_state": "fixture",
            "posture_signal": "fixture",
            "confidence_label": "fixture",
            "blocker_status": "fixture",
            "interpretation": "fixture",
            "required_next_step": "fixture",
            "research_only": "True",
            "preview_only": "True",
            "execution_approved": "False",
        },
    )


def write_risk_fixture(path: Path) -> None:
    write_csv(
        path,
        [
            {"risk_check": "input_file_available", "risk_status": "pass", "blocker": "False"},
            {"risk_check": "expected_components_present", "risk_status": "pass", "blocker": "False"},
            {"risk_check": "no_execution_approved_rows", "risk_status": "pass", "blocker": "False"},
            {"risk_check": "no_order_instruction_columns", "risk_status": "pass", "blocker": "False"},
            {"risk_check": "lead_candidate_research_only", "risk_status": "pass", "blocker": "False"},
            {"risk_check": "vol_managed_split_sensitive", "risk_status": "warning", "blocker": "False"},
            {"risk_check": "breadth_diagnostic_only", "risk_status": "warning", "blocker": "False"},
            {"risk_check": "adaptive_secondary_complex", "risk_status": "warning", "blocker": "False"},
            {"risk_check": "short_research_excluded", "risk_status": "pass", "blocker": "False"},
            {"risk_check": "execution_gate_blocked", "risk_status": "blocked", "blocker": "True"},
            {"risk_check": "decision_report_prerequisites", "risk_status": "blocked", "blocker": "True"},
        ],
        defaults={
            "created_at": "2026-01-01T00:00:00+00:00",
            "component": "fixture",
            "severity": "fixture",
            "source": "fixture",
            "finding": "fixture",
            "required_next_step": "fixture",
            "research_only": "True",
            "preview_only": "True",
            "execution_approved": "False",
        },
    )


def write_csv(path: Path, rows: list[dict[str, str]], defaults: dict[str, str]) -> None:
    merged_rows = []
    for row in rows:
        merged = dict(defaults)
        merged.update(row)
        merged_rows.append(merged)
    fieldnames: list[str] = []
    for row in merged_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_rows)


if __name__ == "__main__":
    raise SystemExit(main())
