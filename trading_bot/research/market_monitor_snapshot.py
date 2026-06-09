"""Research-only intraday market monitoring snapshot."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location
from trading_bot.research.ticker_universe_readiness import DEFAULT_TICKER_UNIVERSE_CANDIDATES


MARKET_MONITOR_SNAPSHOT_COLUMNS = [
    "created_at",
    "ticker",
    "instrument_group",
    "latest_timestamp",
    "latest_close",
    "previous_close",
    "intraday_change_pct",
    "latest_volume",
    "data_status",
    "data_error",
    "monitoring_only",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "notes",
]

INTRADAY_PERIOD = "5d"
INTRADAY_INTERVAL = "15m"


@dataclass
class MarketMonitorSnapshotResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_market_monitor_snapshot(
    root_dir: Path | str = ".",
    output_filename: str = "data/market_monitor_snapshot.csv",
) -> MarketMonitorSnapshotResult:
    root = Path(root_dir)
    configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    market_data = fetch_intraday_market_data(
        [ticker for ticker, _, _ in DEFAULT_TICKER_UNIVERSE_CANDIDATES]
    )
    rows = build_market_monitor_snapshot_rows(created_at, market_data)
    output_path = root / output_filename
    write_market_monitor_snapshot(output_path, rows)
    return MarketMonitorSnapshotResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_market_monitor_snapshot_summary(rows, output_path),
    )


def build_market_monitor_snapshot_rows(
    created_at: str,
    market_data: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    market_data = market_data or {}
    rows: list[dict[str, Any]] = []
    for ticker, instrument_group, _included_for in DEFAULT_TICKER_UNIVERSE_CANDIDATES:
        ticker_data = market_data.get(
            ticker,
            data_failure_row("Ticker was not checked by the intraday monitor snapshot."),
        )
        data_status = ticker_data.get("data_status", "market_data_unavailable")
        rows.append(
            {
                "created_at": created_at,
                "ticker": ticker,
                "instrument_group": instrument_group,
                "latest_timestamp": ticker_data.get("latest_timestamp", ""),
                "latest_close": ticker_data.get("latest_close", ""),
                "previous_close": ticker_data.get("previous_close", ""),
                "intraday_change_pct": ticker_data.get("intraday_change_pct", ""),
                "latest_volume": ticker_data.get("latest_volume", ""),
                "data_status": data_status,
                "data_error": ticker_data.get("data_error", ""),
                "monitoring_only": True,
                "research_only": True,
                "preview_only": True,
                "execution_approved": False,
                "paper_execution_approved": False,
                "notes": monitor_notes(data_status),
            }
        )
    return rows


def fetch_intraday_market_data(tickers: list[str]) -> dict[str, dict[str, Any]]:
    try:
        import yfinance as yf
    except Exception as exc:
        return {ticker: data_failure_row(f"yfinance import failed: {exc}") for ticker in tickers}

    data_by_ticker: dict[str, dict[str, Any]] = {}
    for ticker in tickers:
        try:
            data = yf.download(
                ticker,
                period=INTRADAY_PERIOD,
                interval=INTRADAY_INTERVAL,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if data is None or data.empty:
                data_by_ticker[ticker] = data_failure_row(
                    "No recent intraday market data returned by yfinance."
                )
                continue

            close_series = market_data_series(data, "Close")
            if close_series is None:
                data_by_ticker[ticker] = data_failure_row("Intraday yfinance data had no Close column.")
                continue

            close_series = close_series.dropna()
            if close_series.empty:
                data_by_ticker[ticker] = data_failure_row("Intraday yfinance data had no usable close rows.")
                continue

            latest_timestamp = close_series.index[-1]
            latest_close = numeric_or_blank(close_series.iloc[-1])
            previous_close = numeric_or_blank(close_series.iloc[-2]) if len(close_series) >= 2 else ""
            intraday_change_pct = calculate_change_pct(latest_close, previous_close)

            latest_volume: Any = ""
            volume_series = market_data_series(data, "Volume")
            if volume_series is not None and latest_timestamp in volume_series.index:
                latest_volume = numeric_or_blank(volume_series.loc[latest_timestamp])

            data_by_ticker[ticker] = {
                "latest_timestamp": timestamp_to_text(latest_timestamp),
                "latest_close": latest_close,
                "previous_close": previous_close,
                "intraday_change_pct": intraday_change_pct,
                "latest_volume": latest_volume,
                "data_status": "ok",
                "data_error": "",
            }
        except Exception as exc:
            data_by_ticker[ticker] = data_failure_row(str(exc))
    return data_by_ticker


def market_data_series(data: Any, column_name: str) -> Any:
    if column_name in data.columns:
        column = data[column_name]
    else:
        matches = [
            column
            for column in data.columns
            if isinstance(column, tuple) and column_name in [str(part) for part in column]
        ]
        if not matches:
            return None
        column = data[matches[0]]

    if hasattr(column, "columns"):
        if len(column.columns) == 0:
            return None
        return column.iloc[:, 0]
    return column


def data_failure_row(message: str) -> dict[str, Any]:
    return {
        "latest_timestamp": "",
        "latest_close": "",
        "previous_close": "",
        "intraday_change_pct": "",
        "latest_volume": "",
        "data_status": "market_data_unavailable",
        "data_error": message,
    }


def numeric_or_blank(value: Any) -> Any:
    try:
        if value != value:
            return ""
        return round(float(value), 6)
    except Exception:
        return ""


def calculate_change_pct(latest_close: Any, previous_close: Any) -> Any:
    if latest_close == "" or previous_close == "":
        return ""
    try:
        previous = float(previous_close)
        if previous == 0:
            return ""
        return round(((float(latest_close) - previous) / previous) * 100, 4)
    except Exception:
        return ""


def timestamp_to_text(value: Any) -> str:
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def monitor_notes(data_status: str) -> str:
    notes = [
        "Monitoring/report-only snapshot; not trading approval.",
        "More frequent price checks do not mean more frequent trades.",
        "Daily strategies are not intraday trading strategies without separate research.",
    ]
    if data_status != "ok":
        notes.append("Market data error was recorded and execution remains unapproved.")
    return " ".join(notes)


def write_market_monitor_snapshot(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MARKET_MONITOR_SNAPSHOT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_market_monitor_snapshot_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    rows_with_data = [row for row in rows if row["data_status"] == "ok"]
    rows_with_errors = [row for row in rows if row["data_status"] != "ok"]
    return [
        f"Rows written: {len(rows)}",
        f"Tickers with data: {len(rows_with_data)}",
        f"Tickers with errors: {len(rows_with_errors)}",
        f"Biggest positive intraday_change_pct: {format_extreme_change(rows_with_data, highest=True)}",
        f"Biggest negative intraday_change_pct: {format_extreme_change(rows_with_data, highest=False)}",
        "Warning: this monitoring snapshot does not approve orders or paper execution.",
        f"Saved market monitor snapshot to {output_path}",
    ]


def format_extreme_change(rows: list[dict[str, Any]], *, highest: bool) -> str:
    usable_rows = [row for row in rows if row.get("intraday_change_pct") != ""]
    if not usable_rows:
        return "n/a"
    selected = max(usable_rows, key=lambda row: row["intraday_change_pct"])
    if not highest:
        selected = min(usable_rows, key=lambda row: row["intraday_change_pct"])
    return f"{selected['ticker']} {selected['intraday_change_pct']}%"
