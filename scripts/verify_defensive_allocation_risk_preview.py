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

import trading_bot.research.defensive_allocation_risk as defensive_allocation_risk
from trading_bot.research.defensive_allocation_risk import (
    DEFENSIVE_ALLOCATION_RISK_COLUMNS,
    ORDER_INSTRUCTION_COLUMNS,
    generate_defensive_allocation_risk_preview,
)


EXPECTED_RISK_CHECKS = {
    "input_file_available",
    "expected_components_present",
    "no_execution_approved_rows",
    "no_order_instruction_columns",
    "lead_candidate_research_only",
    "vol_managed_split_sensitive",
    "breadth_diagnostic_only",
    "adaptive_secondary_complex",
    "short_research_excluded",
    "execution_gate_blocked",
    "decision_report_prerequisites",
}

FORBIDDEN_SOURCE_TERMS = [
    "yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
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
    verify_blocked_when_execution_approved(failures)
    verify_blocked_when_order_columns_exist(failures)
    verify_static_safety(failures)

    if failures:
        print("Defensive allocation risk preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Defensive allocation risk preview verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_allocation_fixture(data_dir / "defensive_allocation_preview.csv")
        result = generate_defensive_allocation_risk_preview(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.output_path.name != "defensive_allocation_risk_preview.csv":
            failures.append("output path should be defensive_allocation_risk_preview.csv")
        if not result.output_path.exists():
            failures.append("defensive allocation risk preview CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            fieldnames = csv.DictReader(file).fieldnames
        if fieldnames != DEFENSIVE_ALLOCATION_RISK_COLUMNS:
            failures.append("defensive allocation risk preview columns changed unexpectedly")
        if ORDER_INSTRUCTION_COLUMNS.intersection(DEFENSIVE_ALLOCATION_RISK_COLUMNS):
            failures.append("risk preview schema contains order-instruction columns")

        risk_checks = {row.get("risk_check") for row in result.rows}
        if risk_checks != EXPECTED_RISK_CHECKS:
            failures.append(f"expected risk checks changed: {sorted(str(check) for check in risk_checks)}")
        statuses = {row.get("risk_check"): row.get("risk_status") for row in result.rows}
        if statuses.get("no_execution_approved_rows") != "pass":
            failures.append("execution approval risk check should pass for all-False fixture")
        if statuses.get("no_order_instruction_columns") != "pass":
            failures.append("order-column risk check should pass for safe fixture")
        if statuses.get("execution_gate_blocked") != "blocked":
            failures.append("execution gate should be blocked as a non-execution checkpoint")
        verify_safety_flags(result.rows, failures)

        summary = "\n".join(result.summary_lines)
        for expected in [
            "DEFENSIVE ALLOCATION RISK PREVIEW. SAVED-DATA ONLY. NOT EXECUTION.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "defensive_allocation_risk_preview.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected safety text: {expected}")


def verify_missing_input(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_defensive_allocation_risk_preview(
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )
        if len(result.rows) != 1:
            failures.append("missing input should produce one clear missing_input row")
        row = result.rows[0]
        if row.get("risk_check") != "input_file_available" or row.get("risk_status") != "missing_input":
            failures.append("missing input row should be input_file_available/missing_input")
        if row.get("blocker") is not True:
            failures.append("missing input should be a blocker for this risk preview")
        verify_safety_flags(result.rows, failures)


def verify_blocked_when_execution_approved(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_allocation_fixture(data_dir / "defensive_allocation_preview.csv", execution_approved="True")
        result = generate_defensive_allocation_risk_preview(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        row = find_row(result.rows, "no_execution_approved_rows")
        if row.get("risk_status") != "fail" or row.get("blocker") is not True:
            failures.append("execution_approved=True fixture should fail and block")
        verify_safety_flags(result.rows, failures)


def verify_blocked_when_order_columns_exist(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_allocation_fixture(data_dir / "defensive_allocation_preview.csv", extra_columns={"quantity": "1"})
        result = generate_defensive_allocation_risk_preview(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        row = find_row(result.rows, "no_order_instruction_columns")
        if row.get("risk_status") != "fail" or row.get("blocker") is not True:
            failures.append("order-instruction column fixture should fail and block")
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
    if "--defensive-allocation-risk-preview" not in help_text:
        failures.append("command inventory should include --defensive-allocation-risk-preview")
    source = inspect.getsource(defensive_allocation_risk)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"defensive allocation risk preview references forbidden term: {term}")


def verify_safety_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"safety flags failed for risk check {row.get('risk_check')}")


def find_row(rows: list[dict[str, object]], risk_check: str) -> dict[str, object]:
    return next((row for row in rows if row.get("risk_check") == risk_check), {})


def write_allocation_fixture(
    path: Path,
    execution_approved: str = "False",
    extra_columns: dict[str, str] | None = None,
) -> None:
    rows = [
        {"component": "monthly_etf_momentum_rotation", "preview_label": "lead_reference"},
        {"component": "volatility_managed_dual_momentum_etf", "preview_label": "secondary_check_split_sensitive"},
        {"component": "etf_breadth_regime_allocation", "preview_label": "robust_diagnostic_filter_not_strategy"},
        {"component": "adaptive_risk_on_off_momentum", "preview_label": "secondary_complex_candidate"},
        {"component": "short_research", "preview_label": "paused_not_useful"},
        {"component": "execution_state", "preview_label": "blocked_no_execution_approval"},
    ]
    for row in rows:
        row.update(
            {
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
                "execution_approved": execution_approved,
            }
        )
        if extra_columns:
            row.update(extra_columns)
    write_csv(path, rows)


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
