from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.etf_rotation_robustness as robustness
from trading_bot.research.etf_rotation_robustness import (
    ETF_ROTATION_ROBUSTNESS_COLUMNS,
    generate_etf_rotation_robustness_report,
)
from trading_bot.research.vol_managed_etf_robustness import FIXED_SPLITS


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
]


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        write_equity_fixture(data_dir / "etf_rotation_equity_curve.csv")
        write_trade_fixture(data_dir / "etf_rotation_trades.csv")
        result = generate_etf_rotation_robustness_report(
            data_dir=data_dir,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if not result.output_path.exists():
            failures.append("etf_rotation_robustness_report.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            if csv.DictReader(file).fieldnames != ETF_ROTATION_ROBUSTNESS_COLUMNS:
                failures.append("ETF rotation robustness columns changed unexpectedly")
        verify_rows(result.rows, failures)
        verify_summary(result.summary_lines, failures)
    verify_static_safety(failures)

    if failures:
        print("ETF rotation robustness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ETF rotation robustness verification passed.")
    return 0


def write_equity_fixture(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "equity"])
        writer.writeheader()
        start = date(2024, 1, 1)
        for index in range(100):
            writer.writerow(
                {
                    "date": (start + timedelta(days=index)).isoformat(),
                    "equity": 100_000 + index * 100,
                }
            )


def write_trade_fixture(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "ticker", "side"])
        writer.writeheader()
        for day in [10, 65, 75, 85]:
            writer.writerow({"date": (date(2024, 1, 1) + timedelta(days=day)).isoformat(), "ticker": "SPY", "side": "buy"})


def verify_rows(rows: list[dict[str, object]], failures: list[str]) -> None:
    expected = {split_name for split_name, _ in FIXED_SPLITS}
    actual = {row["split_name"] for row in rows}
    if actual != expected:
        failures.append(f"ETF rotation robustness split rows changed unexpectedly: {sorted(actual)}")
    for row in rows:
        if row["strategy_name"] != "monthly_etf_momentum_rotation":
            failures.append("ETF rotation robustness should only report monthly_etf_momentum_rotation")
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"safety flags failed for {row['split_name']}")
        for column in [
            "out_of_sample_cagr_pct",
            "out_of_sample_sharpe",
            "out_of_sample_max_drawdown_pct",
            "out_of_sample_calmar",
        ]:
            if row[column] == "":
                failures.append(f"missing metric {column} for {row['split_name']}")
    counts = {row["split_name"]: int(row["out_of_sample_trade_count"]) for row in rows}
    if counts.get("split_60_40") != 3:
        failures.append("60/40 OOS trade count should use matching saved trade dates")
    if counts.get("split_80_20") != 1:
        failures.append("80/20 OOS trade count should use matching saved trade dates")


def verify_summary(summary_lines: list[str], failures: list[str]) -> None:
    summary = "\n".join(summary_lines)
    if "ETF ROTATION ROBUSTNESS REPORT. RESEARCH ONLY. NOT EXECUTION." not in summary:
        failures.append("summary should clearly mark ETF rotation robustness research-only")
    if "not execution approval" not in summary:
        failures.append("summary should deny execution approval")


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--etf-rotation-robustness" not in help_text:
        failures.append("command inventory should include --etf-rotation-robustness")
    source = inspect.getsource(robustness)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"ETF rotation robustness module references forbidden term: {term}")


if __name__ == "__main__":
    raise SystemExit(main())
