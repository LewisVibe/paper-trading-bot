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

import trading_bot.research.defensive_state as defensive_state
from trading_bot.research.defensive_state import (
    DEFENSIVE_RESEARCH_STATE_COLUMNS,
    generate_defensive_research_state_report,
)


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


EXPECTED_COMPONENTS = {
    "monthly_etf_momentum_rotation",
    "volatility_managed_dual_momentum_etf",
    "adaptive_risk_on_off_momentum",
    "etf_breadth_regime_allocation",
    "short_research",
    "execution_state",
}


def main() -> int:
    failures: list[str] = []
    verify_fixture_report(failures)
    verify_missing_inputs(failures)
    verify_static_safety(failures)

    if failures:
        print("Defensive research state verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Defensive research state verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_fixture_data(data_dir)
        result = generate_defensive_research_state_report(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.output_path.name != "defensive_research_state_report.csv":
            failures.append("output path should be defensive_research_state_report.csv")
        if not result.output_path.exists():
            failures.append("defensive research state report CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            if csv.DictReader(file).fieldnames != DEFENSIVE_RESEARCH_STATE_COLUMNS:
                failures.append("defensive state columns changed unexpectedly")
        components = {row.get("component") for row in result.rows}
        if components != EXPECTED_COMPONENTS:
            failures.append(f"expected state components changed: {sorted(str(component) for component in components)}")
        labels = {row.get("component"): row.get("state_label") for row in result.rows}
        expected_labels = {
            "monthly_etf_momentum_rotation": "preferred_defensive_candidate",
            "volatility_managed_dual_momentum_etf": "promising_but_split_sensitive",
            "adaptive_risk_on_off_momentum": "secondary_complex_candidate",
            "etf_breadth_regime_allocation": "robust_diagnostic_candidate_not_strategy",
            "short_research": "paused_not_useful",
            "execution_state": "blocked_no_execution_approval",
        }
        for component, expected in expected_labels.items():
            if labels.get(component) != expected:
                failures.append(f"{component} state label should be {expected}, got {labels.get(component)}")
        breadth_row = next((row for row in result.rows if row.get("component") == "etf_breadth_regime_allocation"), {})
        if "fixed-split robustness" in str(breadth_row.get("required_next_step", "")):
            failures.append("ETF breadth state next step should not say fixed-split robustness is still required")
        if "compare against ETF rotation and vol-managed ETF" not in str(breadth_row.get("required_next_step", "")):
            failures.append("ETF breadth state next step should point to ETF rotation / vol-managed comparison")
        verify_safety_flags(result.rows, failures)
        summary = "\n".join(result.summary_lines)
        for expected in [
            "DEFENSIVE RESEARCH STATE REPORT. SAVED-DATA ONLY. NOT EXECUTION.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "defensive_research_state_report.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected safety text: {expected}")


def verify_missing_inputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        result = generate_defensive_research_state_report(
            data_dir=Path(tmpdir),
            created_at="2026-01-01T00:00:00+00:00",
        )
        labels = {row.get("state_label") for row in result.rows}
        if "missing_input" not in labels:
            failures.append("missing saved CSVs should produce missing_input rows")
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
    if "--defensive-research-state-report" not in help_text:
        failures.append("command inventory should include --defensive-research-state-report")
    source = inspect.getsource(defensive_state)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"defensive state report references forbidden term: {term}")


def verify_safety_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
            failures.append(f"safety flags failed for component {row.get('component')}")


def write_fixture_data(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        data_dir / "defensive_candidate_comparison.csv",
        [
            {
                "strategy_name": "monthly_etf_momentum_rotation",
                "comparison_status": "preferred_defensive_candidate",
                "policy_rank": "1",
                "comparison_reason": "ETF rotation remains preferred.",
                "next_research_step": "Keep research-only.",
            },
            {
                "strategy_name": "volatility_managed_dual_momentum_etf",
                "comparison_status": "promising_but_split_sensitive",
                "fixed_split_win_count": "2",
                "split_comparison_summary": "wins 2 of 3 splits",
                "comparison_reason": "Promising but split-sensitive.",
                "next_research_step": "Review split sensitivity.",
            },
            {
                "strategy_name": "adaptive_risk_on_off_momentum",
                "comparison_status": "secondary_defensive_candidate",
                "trade_count": "405",
                "relative_turnover_note": "Higher turnover than ETF rotation.",
                "comparison_reason": "Secondary due to complexity.",
                "next_research_step": "Compare cost burden.",
            },
        ],
    )
    write_csv(
        data_dir / "etf_breadth_regime_decision_report.csv",
        [
            {
                "candidate_name": "etf_breadth_regime_allocation",
                "decision_label": "useful_diagnostic_not_strategy",
                "finding": "Useful diagnostic, not promoted.",
                "required_next_step": "Use as diagnostic only.",
            }
        ],
    )
    write_csv(
        data_dir / "etf_breadth_regime_robustness_report.csv",
        [
            {
                "strategy_name": "etf_breadth_regime_allocation",
                "robustness_label": "robust_diagnostic_candidate",
                "finding": "Positive across splits.",
                "required_next_step": "Keep diagnostic-only.",
            }
        ],
    )
    write_csv(
        data_dir / "short_hedge_backtest_results.csv",
        [
            {
                "strategy_name": "research_spy_short_hedge",
                "research_status": "not_useful",
                "research_conclusion": "Negative metrics; pause.",
            }
        ],
    )
    write_csv(
        data_dir / "execution_eligibility_report.csv",
        [
            {
                "eligibility_check_name": "final_execution_eligibility",
                "eligibility_status": "blocked_for_review",
            }
        ],
    )
    write_csv(
        data_dir / "promoted_decision_preview.csv",
        [
            {"ticker": "AAPL", "decision_state": "blocked_strategy_disagreement", "execution_approved": "False"},
            {"ticker": "SPY", "decision_state": "blocked_strategy_disagreement", "execution_approved": "False"},
        ],
    )
    write_csv(
        data_dir / "portfolio_risk_policy_report.csv",
        [
            {"risk_policy_name": "strategy_disagreement_policy", "risk_policy_status": "blocked_for_review", "execution_approved": "False"}
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
