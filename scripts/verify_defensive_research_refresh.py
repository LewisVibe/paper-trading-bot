from __future__ import annotations

import csv
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.defensive_refresh as refresh
from trading_bot.research.defensive_refresh import refresh_defensive_research


FORBIDDEN_TERMS = [
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
]


@dataclass
class DummyResult:
    output_path: Path


def main() -> int:
    failures: list[str] = []

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        calls: list[str] = []
        steps = [
            ("etf_rotation_robustness", "python bot.py --etf-rotation-robustness", step("etf_rotation_robustness", data_dir, calls)),
            ("vol_managed_etf_robustness", "python bot.py --vol-managed-etf-robustness", step("vol_managed_etf_robustness", data_dir, calls)),
            ("defensive_candidate_comparison", "python bot.py --defensive-candidate-comparison", step("defensive_candidate_comparison", data_dir, calls)),
            ("etf_defensive_drawdown_comparison", "python bot.py --etf-defensive-drawdown-comparison", step("etf_defensive_drawdown_comparison", data_dir, calls)),
            ("plot_etf_defensive_comparison", "python bot.py --plot-etf-defensive-comparison", step("plot_etf_defensive_comparison", data_dir, calls)),
        ]
        result = refresh_defensive_research(data_dir=data_dir, steps=steps)
        expected_order = [name for name, _, _ in steps]
        if calls != expected_order:
            failures.append(f"refresh steps ran out of order: {calls}")
        if not result.output_path.exists():
            failures.append("defensive_research_refresh_summary.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != refresh.DEFENSIVE_REFRESH_COLUMNS:
                failures.append("defensive refresh summary columns changed unexpectedly")
            rows = list(reader)
        if len(rows) != len(expected_order):
            failures.append("defensive refresh summary should include one row per step")
        for row in rows:
            if row["status"] != "passed":
                failures.append(f"mocked refresh step should pass: {row['step_name']}")
            if row["research_only"] != "True" or row["preview_only"] != "True" or row["execution_approved"] != "False":
                failures.append(f"safety flags failed for {row['step_name']}")
        summary = "\n".join(result.summary_lines)
        if "DEFENSIVE RESEARCH REFRESH. RESEARCH ONLY. NOT EXECUTION." not in summary:
            failures.append("terminal summary should clearly deny execution")

    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        result = refresh_defensive_research(data_dir=data_dir)
        if not result.output_path.exists():
            failures.append("missing-input refresh should still write a summary CSV")
        if not any(row["status"] == "failed" for row in result.rows):
            failures.append("missing-input refresh should record failed steps")
        messages = "\n".join(str(row["message"]) for row in result.rows)
        if "python bot.py --etf-rotation-backtest" not in messages or "python bot.py --vol-managed-etf-backtest" not in messages:
            failures.append("missing-input messages should explain how to refresh saved inputs")
        for row in result.rows:
            if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
                failures.append(f"missing-input safety flags failed for {row['step_name']}")

    source = inspect.getsource(refresh)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"defensive research refresh references forbidden term: {term}")
    if "run_vol_managed_etf_backtest_files" in source:
        failures.append("refresh command must not rerun vol-managed ETF backtest")
    if "run_etf_rotation_backtest" in source:
        failures.append("refresh command must not rerun ETF rotation backtest")

    if failures:
        print("Defensive research refresh verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Defensive research refresh verification passed.")
    return 0


def step(name: str, data_dir: Path, calls: list[str]):
    def run() -> DummyResult:
        calls.append(name)
        output_path = data_dir / f"{name}.csv"
        output_path.write_text("ok\n", encoding="utf-8")
        return DummyResult(output_path=output_path)

    return run


if __name__ == "__main__":
    raise SystemExit(main())
