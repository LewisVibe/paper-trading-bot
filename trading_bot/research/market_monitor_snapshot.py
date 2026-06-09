"""Research-only intraday market monitoring snapshot."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

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

MARKET_MONITOR_QUALITY_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "ticker",
    "value",
    "blocked",
    "details",
    "monitoring_only",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
]

INTRADAY_PERIOD = "5d"
INTRADAY_INTERVAL = "15m"
STALE_TIMESTAMP_MINUTES = 60
ABNORMAL_INTRADAY_MOVE_PCT = 5.0


@dataclass
class MarketMonitorSnapshotResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class MarketMonitorQualityReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_market_monitor_snapshot(
    root_dir: Path | str = ".",
    output_filename: str = "data/market_monitor_snapshot.csv",
) -> MarketMonitorSnapshotResult:
    from trading_bot.market_data import configure_yfinance_cache_location

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


def generate_market_monitor_quality_report(
    root_dir: Path | str = ".",
    snapshot_filename: str = "data/market_monitor_snapshot.csv",
    output_filename: str = "data/market_monitor_quality_report.csv",
) -> MarketMonitorQualityReportResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    snapshot_path = root / snapshot_filename
    output_path = root / output_filename
    rows = build_market_monitor_quality_rows(created_at, snapshot_path)
    write_market_monitor_quality_report(output_path, rows)
    return MarketMonitorQualityReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_market_monitor_quality_summary(rows, output_path),
    )


def build_market_monitor_quality_rows(created_at: str, snapshot_path: Path) -> list[dict[str, Any]]:
    quality_rows: list[dict[str, Any]] = []
    if not snapshot_path.exists():
        quality_rows.append(
            quality_row(
                created_at,
                "csv_exists",
                "error",
                "",
                str(snapshot_path),
                True,
                "Snapshot CSV is missing. Run `python bot.py --market-monitor-snapshot` first.",
            )
        )
        return quality_rows

    quality_rows.append(
        quality_row(created_at, "csv_exists", "pass", "", str(snapshot_path), False, "Snapshot CSV exists.")
    )
    with snapshot_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        snapshot_rows = list(reader)
        fieldnames = reader.fieldnames or []

    missing_columns = [column for column in MARKET_MONITOR_SNAPSHOT_COLUMNS if column not in fieldnames]
    if missing_columns:
        quality_rows.append(
            quality_row(
                created_at,
                "required_columns",
                "error",
                "",
                ", ".join(missing_columns),
                True,
                "Snapshot CSV is missing required columns.",
            )
        )
    else:
        quality_rows.append(
            quality_row(
                created_at,
                "required_columns",
                "pass",
                "",
                str(len(MARKET_MONITOR_SNAPSHOT_COLUMNS)),
                False,
                "All required snapshot columns are present.",
            )
        )

    quality_rows.extend(row_count_quality_rows(created_at, snapshot_rows))
    quality_rows.extend(duplicate_ticker_quality_rows(created_at, snapshot_rows))
    quality_rows.extend(missing_value_quality_rows(created_at, snapshot_rows, "latest_close"))
    quality_rows.extend(missing_value_quality_rows(created_at, snapshot_rows, "latest_timestamp"))
    quality_rows.extend(stale_timestamp_quality_rows(created_at, snapshot_rows))
    quality_rows.extend(data_error_quality_rows(created_at, snapshot_rows))
    quality_rows.extend(abnormal_move_quality_rows(created_at, snapshot_rows))
    quality_rows.extend(boolean_flag_quality_rows(created_at, snapshot_rows))
    return quality_rows


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


def row_count_quality_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    status = "pass" if rows else "warning"
    details = "Snapshot contains rows." if rows else "Snapshot CSV has no data rows."
    return [quality_row(created_at, "row_count", status, "", str(len(rows)), False, details)]


def duplicate_ticker_quality_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ticker_counts = Counter(row.get("ticker", "") for row in rows if row.get("ticker"))
    duplicate_tickers = [ticker for ticker, count in sorted(ticker_counts.items()) if count > 1]
    if not duplicate_tickers:
        return [
            quality_row(
                created_at,
                "duplicate_tickers",
                "pass",
                "",
                "0",
                False,
                "No duplicate ticker rows found.",
            )
        ]
    return [
        quality_row(
            created_at,
            "duplicate_tickers",
            "warning",
            ticker,
            str(ticker_counts[ticker]),
            False,
            "Duplicate ticker rows should be reviewed before relying on monitoring output.",
        )
        for ticker in duplicate_tickers
    ]


def missing_value_quality_rows(
    created_at: str,
    rows: list[dict[str, Any]],
    column_name: str,
) -> list[dict[str, Any]]:
    missing_rows = [row for row in rows if not str(row.get(column_name, "")).strip()]
    if not missing_rows:
        return [
            quality_row(
                created_at,
                f"missing_{column_name}",
                "pass",
                "",
                "0",
                False,
                f"No rows are missing {column_name}.",
            )
        ]
    return [
        quality_row(
            created_at,
            f"missing_{column_name}",
            "warning",
            row.get("ticker", ""),
            "",
            False,
            f"Ticker row is missing {column_name}.",
        )
        for row in missing_rows
    ]


def stale_timestamp_quality_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed_rows = [
        (row, parse_timestamp(row.get("latest_timestamp", "")))
        for row in rows
        if str(row.get("latest_timestamp", "")).strip()
    ]
    parsed_rows = [(row, timestamp) for row, timestamp in parsed_rows if timestamp is not None]
    if not parsed_rows:
        return [
            quality_row(
                created_at,
                "stale_timestamps",
                "warning",
                "",
                "no_parseable_timestamps",
                False,
                "No parseable timestamps were available for stale-row review.",
            )
        ]

    newest_timestamp = max(timestamp for _row, timestamp in parsed_rows)
    stale_cutoff = newest_timestamp - timedelta(minutes=STALE_TIMESTAMP_MINUTES)
    stale_rows = [(row, timestamp) for row, timestamp in parsed_rows if timestamp < stale_cutoff]
    if not stale_rows:
        return [
            quality_row(
                created_at,
                "stale_timestamps",
                "pass",
                "",
                newest_timestamp.isoformat(),
                False,
                f"No timestamps are more than {STALE_TIMESTAMP_MINUTES} minutes older than the newest timestamp.",
            )
        ]
    return [
        quality_row(
            created_at,
            "stale_timestamps",
            "warning",
            row.get("ticker", ""),
            timestamp.isoformat(),
            False,
            f"Timestamp is more than {STALE_TIMESTAMP_MINUTES} minutes older than the newest timestamp {newest_timestamp.isoformat()}.",
        )
        for row, timestamp in stale_rows
    ]


def data_error_quality_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    error_rows = [row for row in rows if str(row.get("data_error", "")).strip()]
    if not error_rows:
        return [quality_row(created_at, "data_error_rows", "pass", "", "0", False, "No data_error rows found.")]
    return [
        quality_row(
            created_at,
            "data_error_rows",
            "warning",
            row.get("ticker", ""),
            row.get("data_status", ""),
            False,
            str(row.get("data_error", "")),
        )
        for row in error_rows
    ]


def abnormal_move_quality_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    abnormal_rows: list[tuple[dict[str, Any], float]] = []
    for row in rows:
        change = parse_float(row.get("intraday_change_pct", ""))
        if change is not None and abs(change) > ABNORMAL_INTRADAY_MOVE_PCT:
            abnormal_rows.append((row, change))
    if not abnormal_rows:
        return [
            quality_row(
                created_at,
                "abnormal_intraday_moves",
                "pass",
                "",
                f"threshold={ABNORMAL_INTRADAY_MOVE_PCT}%",
                False,
                "No rows exceeded the abnormal intraday move threshold.",
            )
        ]
    return [
        quality_row(
            created_at,
            "abnormal_intraday_moves",
            "warning",
            row.get("ticker", ""),
            f"{change}%",
            False,
            f"Absolute intraday move is above {ABNORMAL_INTRADAY_MOVE_PCT}%; review before relying on monitoring output.",
        )
        for row, change in abnormal_rows
    ]


def boolean_flag_quality_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("execution_approved_false", "execution_approved", False),
        ("paper_execution_approved_false", "paper_execution_approved", False),
        ("monitoring_only_true", "monitoring_only", True),
        ("research_only_true", "research_only", True),
        ("preview_only_true", "preview_only", True),
    ]
    quality_rows: list[dict[str, Any]] = []
    for check_name, column_name, expected in checks:
        bad_rows = [row for row in rows if parse_bool(row.get(column_name)) is not expected]
        if not bad_rows:
            quality_rows.append(
                quality_row(
                    created_at,
                    check_name,
                    "pass",
                    "",
                    str(expected),
                    False,
                    f"All rows have {column_name}={expected}.",
                )
            )
            continue
        quality_rows.extend(
            quality_row(
                created_at,
                check_name,
                "error",
                row.get("ticker", ""),
                str(row.get(column_name, "")),
                True,
                f"Expected {column_name}={expected}; review snapshot safety flags.",
            )
            for row in bad_rows
        )
    return quality_rows


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


def write_market_monitor_quality_report(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MARKET_MONITOR_QUALITY_COLUMNS)
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


def build_market_monitor_quality_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts = Counter(row.get("check_status", "unknown") for row in rows)
    blocked_rows = [row for row in rows if parse_bool(row.get("blocked")) is True]
    return [
        f"Market monitor quality checks: {len(rows)}",
        f"Pass: {counts['pass']}, warning: {counts['warning']}, error: {counts['error']}",
        "Blocked rows: " + format_blocked_rows(blocked_rows),
        "Warning: this quality report does not approve execution or orders.",
        f"Saved market monitor quality report to {output_path}",
    ]


def format_blocked_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "none"
    return "; ".join(
        f"{row.get('check_name', '')}:{row.get('ticker', '') or 'snapshot'}"
        for row in rows[:10]
    )


def show_market_monitor_file(
    path: Path = Path("data") / "market_monitor_snapshot.csv",
) -> tuple[int, list[str]]:
    if not path.exists():
        return (
            1,
            [
                f"Market monitor snapshot CSV not found: {path}",
                "Run `python bot.py --market-monitor-snapshot` first.",
            ],
        )

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    data_status_counts = Counter(row.get("data_status", "") or "blank" for row in rows)
    rows_with_data = [row for row in rows if row.get("data_status") == "ok"]
    rows_with_errors = [row for row in rows if row.get("data_status") != "ok"]
    unsafe_rows = [
        row
        for row in rows
        if not is_false_flag(row.get("execution_approved"))
        or not is_false_flag(row.get("paper_execution_approved"))
    ]

    lines = [
        f"Market monitor snapshot rows: {len(rows)}",
        "Data status counts:",
        *format_status_counts(data_status_counts),
        f"Tickers with data: {len(rows_with_data)}",
        f"Tickers with errors: {len(rows_with_errors)}",
        "Top 5 positive intraday_change_pct:",
        *format_change_rows(rows, highest=True),
        "Top 5 negative intraday_change_pct:",
        *format_change_rows(rows, highest=False),
        "Rows with data_error:",
        *format_error_rows(rows),
    ]
    if unsafe_rows:
        lines.append(
            f"Warning: {len(unsafe_rows)} rows have execution approval flags that are not false."
        )
    lines.append("Warning: this is monitoring/display only and does not approve orders.")
    return 0, lines


def format_status_counts(counts: Counter[str]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {status}: {count}" for status, count in sorted(counts.items())]


def format_change_rows(rows: list[dict[str, Any]], *, highest: bool) -> list[str]:
    usable_rows = []
    for row in rows:
        try:
            change = float(row.get("intraday_change_pct", ""))
        except (TypeError, ValueError):
            continue
        if highest and change <= 0:
            continue
        if not highest and change >= 0:
            continue
        usable_rows.append((change, row))

    if not usable_rows:
        return ["- n/a"]

    selected_rows = sorted(usable_rows, key=lambda item: item[0], reverse=highest)[:5]
    return [
        f"- {row.get('ticker', '')}: {round(change, 4)}% "
        f"close={row.get('latest_close', '')} timestamp={row.get('latest_timestamp', '')}"
        for change, row in selected_rows
    ]


def format_error_rows(rows: list[dict[str, Any]]) -> list[str]:
    error_rows = [row for row in rows if row.get("data_error")]
    if not error_rows:
        return ["- none"]
    return [
        f"- {row.get('ticker', '')}: {row.get('data_status', '')} - {row.get('data_error', '')}"
        for row in error_rows
    ]


def is_false_flag(value: Any) -> bool:
    return str(value).strip().lower() == "false"


def quality_row(
    created_at: str,
    check_name: str,
    check_status: str,
    ticker: str,
    value: str,
    blocked: bool,
    details: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "ticker": ticker,
        "value": value,
        "blocked": blocked,
        "details": details,
        "monitoring_only": True,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
    }


def parse_bool(value: Any) -> bool | None:
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def parse_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_timestamp(value: Any) -> datetime | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
