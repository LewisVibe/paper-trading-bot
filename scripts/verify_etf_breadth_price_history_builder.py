from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.etf_breadth_regime as breadth
from trading_bot.research.etf_breadth_regime import (
    ETF_BREADTH_PRICE_HISTORY_COLUMNS,
    ETF_BREADTH_UNIVERSE,
    build_etf_breadth_price_history,
)


FORBIDDEN_SOURCE_TERMS = [
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_simulated_positions",
    "decide_trade",
    "sqlite3",
]


@dataclass
class FakeConfig:
    pass


class FakeIndex:
    def __init__(self, value: date):
        self.value = value

    def date(self) -> date:
        return self.value


class FakeFrame:
    def __init__(self, rows: list[tuple[date, object]]):
        self.rows = rows

    def iterrows(self):
        for row_date, close in self.rows:
            yield FakeIndex(row_date), {"close": close}


def main() -> int:
    failures: list[str] = []
    verify_builder_output(failures)
    verify_empty_failure_handling(failures)
    verify_static_safety(failures)

    if failures:
        print("ETF breadth price history builder verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ETF breadth price history builder verification passed.")
    return 0


def verify_builder_output(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        result = build_etf_breadth_price_history(
            FakeConfig(),
            logger=None,
            data_dir=data_dir,
            downloader=fake_downloader,
        )
        if not result.output_path.exists():
            failures.append("etf_breadth_price_history.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if reader.fieldnames != ETF_BREADTH_PRICE_HISTORY_COLUMNS:
                failures.append("price history columns should be exactly date,ticker,close")
        if not rows:
            failures.append("fixture should produce saved price rows")
            return
        if rows != sorted(rows, key=lambda row: (row["date"], row["ticker"])):
            failures.append("price history rows should be sorted by date then ticker")
        if any(row["close"] == "" or float(row["close"]) <= 0 for row in rows):
            failures.append("missing or non-positive close rows should be dropped")
        saved_tickers = {row["ticker"] for row in rows}
        if "SPY" not in saved_tickers:
            failures.append("SPY must be included in saved ETF breadth universe data")
        if "BAD" in saved_tickers:
            failures.append("unexpected ticker appeared in saved ETF breadth data")
        if len(result.tickers_attempted) != len(ETF_BREADTH_UNIVERSE):
            failures.append("builder should attempt the configured ETF breadth universe")
        summary = "\n".join(result.summary_lines)
        for expected in [
            "ETF BREADTH PRICE HISTORY BUILDER. RESEARCH DATA ONLY. NOT EXECUTION.",
            "Tickers attempted:",
            "Tickers saved:",
            "Rows saved:",
            "Date range saved:",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected text: {expected}")


def verify_empty_failure_handling(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        result = build_etf_breadth_price_history(
            FakeConfig(),
            logger=None,
            data_dir=data_dir,
            downloader=failing_downloader,
        )
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if reader.fieldnames != ETF_BREADTH_PRICE_HISTORY_COLUMNS:
                failures.append("empty output should still keep exact headers")
            if rows:
                failures.append("failing downloader should write headers only")
        if "No valid rows were downloaded; wrote an empty CSV with headers only." not in "\n".join(result.summary_lines):
            failures.append("empty download summary should be explicit")


def verify_static_safety(failures: list[str]) -> None:
    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--build-etf-breadth-price-history" not in help_text:
        failures.append("command inventory should include --build-etf-breadth-price-history")
    source = inspect.getsource(breadth)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"ETF breadth price-history builder references forbidden term: {term}")


def fake_downloader(_config, ticker: str) -> FakeFrame:
    start = date(2024, 1, 1)
    rows: list[tuple[date, object]] = []
    for offset in [2, 0, 1]:
        close: object = 100 + offset
        if ticker == "SPY" and offset == 1:
            close = ""
        rows.append((start + timedelta(days=offset), close))
    return FakeFrame(rows)


def failing_downloader(_config, ticker: str) -> FakeFrame:
    raise RuntimeError(f"fixture failure for {ticker}")


if __name__ == "__main__":
    raise SystemExit(main())
