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

import trading_bot.research.defensive_allocation_preview as defensive_allocation_preview
from trading_bot.research.defensive_allocation_preview import (
    DEFENSIVE_ALLOCATION_PREVIEW_COLUMNS,
    generate_defensive_allocation_preview,
)


EXPECTED_COMPONENTS = {
    "monthly_etf_momentum_rotation",
    "volatility_managed_dual_momentum_etf",
    "etf_breadth_regime_allocation",
    "adaptive_risk_on_off_momentum",
    "short_research",
    "execution_state",
}

EXPECTED_PREVIEW_LABELS = {
    "lead_reference",
    "secondary_check_split_sensitive",
    "robust_diagnostic_filter_not_strategy",
    "secondary_complex_candidate",
    "paused_not_useful",
    "blocked_no_execution_approval",
}

FORBIDDEN_OUTPUT_COLUMNS = {
    "side",
    "quantity",
    "order_type",
    "order_id",
    "target_order",
    "submit_order",
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
    verify_fixture_preview(failures)
    verify_missing_input_preview(failures)
    verify_static_safety(failures)

    if failures:
        print("Defensive allocation preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Defensive allocation preview verification passed.")
    return 0


def verify_fixture_preview(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_state_fixture(data_dir)
        result = generate_defensive_allocation_preview(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.output_path.name != "defensive_allocation_preview.csv":
            failures.append("output path should be defensive_allocation_preview.csv")
        if not result.output_path.exists():
            failures.append("defensive allocation preview CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            fieldnames = csv.DictReader(file).fieldnames
        if fieldnames != DEFENSIVE_ALLOCATION_PREVIEW_COLUMNS:
            failures.append("defensive allocation preview columns changed unexpectedly")
        if FORBIDDEN_OUTPUT_COLUMNS.intersection(DEFENSIVE_ALLOCATION_PREVIEW_COLUMNS):
            failures.append("defensive allocation preview contains order-instruction columns")

        components = {row.get("component") for row in result.rows}
        if components != EXPECTED_COMPONENTS:
            failures.append(f"expected preview components changed: {sorted(str(component) for component in components)}")
        labels = {row.get("preview_label") for row in result.rows}
        if labels != EXPECTED_PREVIEW_LABELS:
            failures.append(f"expected preview labels changed: {sorted(str(label) for label in labels)}")
        verify_safety_flags(result.rows, failures)

        summary = "\n".join(result.summary_lines)
        for expected in [
            "DEFENSIVE ALLOCATION PREVIEW. PREVIEW ONLY. NOT EXECUTION.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "defensive_allocation_preview.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected safety text: {expected}")


def verify_missing_input_preview(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_defensive_allocation_preview(
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )
        labels = {row.get("preview_label") for row in result.rows}
        if labels != {"missing_input"}:
            failures.append("missing state input should produce missing_input preview rows")
        posture_signals = {row.get("posture_signal") for row in result.rows}
        if posture_signals != {"insufficient_data"}:
            failures.append("missing state input should produce insufficient_data posture rows")
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
    if "--defensive-allocation-preview" not in help_text:
        failures.append("command inventory should include --defensive-allocation-preview")
    source = inspect.getsource(defensive_allocation_preview)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"defensive allocation preview references forbidden term: {term}")


def verify_safety_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"safety flags failed for component {row.get('component')}")


def write_state_fixture(data_dir: Path) -> None:
    write_csv(
        data_dir / "defensive_research_state_report.csv",
        [
            {
                "component": "monthly_etf_momentum_rotation",
                "category": "defensive_candidate",
                "state_label": "preferred_defensive_candidate",
                "evidence_source": "data/defensive_candidate_comparison.csv",
                "interpretation": "ETF rotation remains preferred.",
                "required_next_step": "Keep research-only.",
                "research_only": "True",
                "preview_only": "True",
                "execution_approved": "False",
            },
            {
                "component": "volatility_managed_dual_momentum_etf",
                "category": "defensive_candidate",
                "state_label": "promising_but_split_sensitive",
                "evidence_source": "data/defensive_candidate_comparison.csv",
                "interpretation": "Promising but split-sensitive.",
                "required_next_step": "Review split sensitivity.",
                "research_only": "True",
                "preview_only": "True",
                "execution_approved": "False",
            },
            {
                "component": "adaptive_risk_on_off_momentum",
                "category": "defensive_candidate",
                "state_label": "secondary_complex_candidate",
                "evidence_source": "data/defensive_candidate_comparison.csv",
                "interpretation": "Secondary due to complexity.",
                "required_next_step": "Monitor only.",
                "research_only": "True",
                "preview_only": "True",
                "execution_approved": "False",
            },
            {
                "component": "etf_breadth_regime_allocation",
                "category": "diagnostic_filter",
                "state_label": "robust_diagnostic_candidate_not_strategy",
                "evidence_source": "data/etf_breadth_regime_robustness_report.csv",
                "interpretation": "Diagnostic only.",
                "required_next_step": "Compare against ETF rotation and vol-managed ETF.",
                "research_only": "True",
                "preview_only": "True",
                "execution_approved": "False",
            },
            {
                "component": "short_research",
                "category": "paused_research",
                "state_label": "paused_not_useful",
                "evidence_source": "data/short_hedge_backtest_results.csv",
                "interpretation": "Short research remains paused.",
                "required_next_step": "Do not add short preview or execution.",
                "research_only": "True",
                "preview_only": "True",
                "execution_approved": "False",
            },
            {
                "component": "execution_state",
                "category": "execution_boundary",
                "state_label": "blocked_no_execution_approval",
                "evidence_source": "data/execution_eligibility_report.csv",
                "interpretation": "Execution remains blocked.",
                "required_next_step": "Resolve review requirements.",
                "research_only": "True",
                "preview_only": "True",
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
