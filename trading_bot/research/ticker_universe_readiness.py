"""Research-only ticker universe readiness report."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TICKER_UNIVERSE_READINESS_COLUMNS = [
    "created_at",
    "ticker",
    "instrument_group",
    "included_for",
    "monitoring_allowed",
    "research_allowed",
    "preview_allowed",
    "execution_approved",
    "paper_execution_approved",
    "requires_liquidity_review",
    "requires_risk_limits_before_execution",
    "duplicate_in_static_universe",
    "latest_close",
    "latest_volume",
    "data_status",
    "data_error",
    "notes",
]

DEFAULT_TICKER_UNIVERSE_CANDIDATES = [
    ("SPY", "ETF", "broad_market_etf"),
    ("QQQ", "ETF", "large_cap_growth_etf"),
    ("IWM", "ETF", "small_cap_etf"),
    ("DIA", "ETF", "dow_large_cap_etf"),
    ("XLK", "ETF", "sector_etf_technology"),
    ("XLF", "ETF", "sector_etf_financials"),
    ("XLY", "ETF", "sector_etf_consumer_discretionary"),
    ("XLE", "ETF", "sector_etf_energy"),
    ("XLI", "ETF", "sector_etf_industrials"),
    ("XLU", "ETF", "sector_etf_utilities"),
    ("XLV", "ETF", "sector_etf_healthcare"),
    ("XLP", "ETF", "sector_etf_consumer_staples"),
    ("AAPL", "stock", "large_liquid_us_stock"),
    ("MSFT", "stock", "large_liquid_us_stock"),
    ("NVDA", "stock", "large_liquid_us_stock"),
    ("AMZN", "stock", "large_liquid_us_stock"),
    ("META", "stock", "large_liquid_us_stock"),
    ("GOOGL", "stock", "large_liquid_us_stock"),
    ("TSLA", "stock", "large_liquid_us_stock"),
    ("JPM", "stock", "large_liquid_us_stock"),
    ("BAC", "stock", "large_liquid_us_stock"),
    ("XOM", "stock", "large_liquid_us_stock"),
    ("CVX", "stock", "large_liquid_us_stock"),
    ("UNH", "stock", "large_liquid_us_stock"),
    ("JNJ", "stock", "large_liquid_us_stock"),
    ("PG", "stock", "large_liquid_us_stock"),
    ("KO", "stock", "large_liquid_us_stock"),
]


@dataclass
class TickerUniverseReadinessReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_ticker_universe_readiness_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/ticker_universe_readiness_report.csv",
) -> TickerUniverseReadinessReportResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    market_data = fetch_recent_market_data([ticker for ticker, _, _ in DEFAULT_TICKER_UNIVERSE_CANDIDATES])
    rows = build_ticker_universe_readiness_rows(created_at, market_data)
    output_path = root / output_filename
    write_ticker_universe_readiness_report(output_path, rows)
    return TickerUniverseReadinessReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_ticker_universe_readiness_summary(rows, output_path),
    )


def build_ticker_universe_readiness_rows(
    created_at: str,
    market_data: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    market_data = market_data or {}
    ticker_counts = Counter(ticker for ticker, _, _ in DEFAULT_TICKER_UNIVERSE_CANDIDATES)
    rows: list[dict[str, Any]] = []
    for ticker, instrument_group, included_for in DEFAULT_TICKER_UNIVERSE_CANDIDATES:
        ticker_data = market_data.get(ticker, {})
        is_duplicate = ticker_counts[ticker] > 1
        rows.append(
            {
                "created_at": created_at,
                "ticker": ticker,
                "instrument_group": instrument_group,
                "included_for": included_for,
                "monitoring_allowed": True,
                "research_allowed": True,
                "preview_allowed": True,
                "execution_approved": False,
                "paper_execution_approved": False,
                "requires_liquidity_review": True,
                "requires_risk_limits_before_execution": True,
                "duplicate_in_static_universe": is_duplicate,
                "latest_close": ticker_data.get("latest_close", ""),
                "latest_volume": ticker_data.get("latest_volume", ""),
                "data_status": ticker_data.get("data_status", "not_checked"),
                "data_error": ticker_data.get("data_error", ""),
                "notes": readiness_notes(is_duplicate, ticker_data.get("data_status", "not_checked")),
            }
        )
    return rows


def fetch_recent_market_data(tickers: list[str]) -> dict[str, dict[str, Any]]:
    try:
        import yfinance as yf
    except Exception as exc:
        return {ticker: data_failure_row(f"yfinance import failed: {exc}") for ticker in tickers}

    data_by_ticker: dict[str, dict[str, Any]] = {}
    for ticker in tickers:
        try:
            data = yf.download(
                ticker,
                period="5d",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if data is None or data.empty:
                data_by_ticker[ticker] = data_failure_row("No recent daily market data returned by yfinance.")
                continue
            latest = data.dropna(how="all").tail(1)
            if latest.empty:
                data_by_ticker[ticker] = data_failure_row("Recent yfinance data contained no complete rows.")
                continue
            data_by_ticker[ticker] = {
                "latest_close": value_or_blank(latest.iloc[0].get("Close", "")),
                "latest_volume": value_or_blank(latest.iloc[0].get("Volume", "")),
                "data_status": "ok",
                "data_error": "",
            }
        except Exception as exc:
            data_by_ticker[ticker] = data_failure_row(str(exc))
    return data_by_ticker


def data_failure_row(message: str) -> dict[str, Any]:
    return {
        "latest_close": "",
        "latest_volume": "",
        "data_status": "market_data_unavailable",
        "data_error": message,
    }


def value_or_blank(value: Any) -> Any:
    try:
        if value != value:
            return ""
    except Exception:
        return ""
    return value


def readiness_notes(is_duplicate: bool, data_status: str) -> str:
    notes = [
        "Research/preview monitoring only; not execution approval.",
        "More tickers do not mean more trades.",
        "Frequent monitoring should start as observe/report/preview only.",
    ]
    if is_duplicate:
        notes.append("Duplicate ticker in static universe; remove before any execution review.")
    if data_status != "ok":
        notes.append("Market data needs review before relying on monitoring output.")
    return " ".join(notes)


def write_ticker_universe_readiness_report(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TICKER_UNIVERSE_READINESS_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_ticker_universe_readiness_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    duplicate_count = sum(1 for row in rows if row["duplicate_in_static_universe"])
    data_ok_count = sum(1 for row in rows if row["data_status"] == "ok")
    return [
        f"Ticker universe readiness rows: {len(rows)}",
        f"Duplicate ticker rows: {duplicate_count}",
        f"Rows with recent yfinance data: {data_ok_count}",
        "Execution approved: False for all rows.",
        "Paper execution approved: False for all rows.",
        "This report is research/preview monitoring only and does not approve orders.",
        f"Saved ticker universe readiness report to {output_path}",
    ]
