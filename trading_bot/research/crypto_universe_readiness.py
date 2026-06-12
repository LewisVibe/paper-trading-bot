"""Research-only crypto universe readiness report.

This report expands the crypto research universe and classifies saved data
quality for later research-only strategy design. It uses yfinance-compatible
daily symbols only and does not touch broker, position, order, database,
notification, config, scheduling, or execution paths.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location


CRYPTO_UNIVERSE = [
    ("BTC-USD", "Bitcoin"),
    ("ETH-USD", "Ethereum"),
    ("SOL-USD", "Solana"),
    ("BNB-USD", "BNB"),
    ("XRP-USD", "XRP"),
    ("ADA-USD", "Cardano"),
    ("AVAX-USD", "Avalanche"),
    ("LINK-USD", "Chainlink"),
    ("DOT-USD", "Polkadot"),
    ("LTC-USD", "Litecoin"),
    ("BCH-USD", "Bitcoin Cash"),
    ("DOGE-USD", "Dogecoin"),
    ("TRX-USD", "TRON"),
    ("ATOM-USD", "Cosmos"),
    ("POL-USD", "Polygon Ecosystem Token"),
    ("MATIC-USD", "Polygon"),
]

STATUS_LABELS = [
    "crypto_strategy_research_eligible",
    "crypto_watchlist_data_short",
    "crypto_watchlist_high_volatility",
    "crypto_reject_missing_data",
    "crypto_reject_insufficient_history",
    "crypto_reject_duplicate_or_transition_unclear",
    "crypto_manual_review_required",
]

OUTPUT_FILES = {
    "report": Path("data/crypto_universe_readiness_report.csv"),
    "summary": Path("data/crypto_universe_readiness_summary.csv"),
}

REPORT_COLUMNS = [
    "created_at",
    "symbol",
    "display_asset_name",
    "data_status",
    "first_date",
    "latest_date",
    "row_count",
    "latest_close",
    "missing_close_count",
    "duplicate_date_count",
    "enough_history_for_200d_trend",
    "enough_history_for_252d_volatility",
    "enough_history_for_fixed_split_research",
    "approx_daily_volatility",
    "approx_annualised_volatility",
    "max_drawdown",
    "latest_200d_trend_state",
    "latest_126d_momentum",
    "latest_252d_momentum",
    "research_universe_status",
    "strategy_research_eligible",
    "reason",
    "research_only",
    "preview_only",
    "execution_approved",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "metric_name",
    "metric_value",
    "evidence",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoUniverseReadinessResult:
    report_path: Path
    summary_path: Path
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_universe_readiness_report(data_dir: Path | str = "data") -> CryptoUniverseReadinessResult:
    data_path = Path(data_dir)
    configure_yfinance_cache_location(data_path / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    downloaded = download_universe_daily_history([symbol for symbol, _name in CRYPTO_UNIVERSE])
    transition_symbols = symbols_with_transition_issue(downloaded)
    report_rows = [
        build_symbol_row(created_at, symbol, display_name, downloaded.get(symbol, {}), transition_symbols)
        for symbol, display_name in CRYPTO_UNIVERSE
    ]
    summary_rows = build_summary_rows(created_at, report_rows)
    report_path = data_path / OUTPUT_FILES["report"].name
    summary_path = data_path / OUTPUT_FILES["summary"].name
    write_rows(report_path, REPORT_COLUMNS, report_rows)
    write_rows(summary_path, SUMMARY_COLUMNS, summary_rows)
    return CryptoUniverseReadinessResult(
        report_path=report_path,
        summary_path=summary_path,
        report_rows=report_rows,
        summary_rows=summary_rows,
        summary_lines=build_summary_lines(report_rows, report_path, summary_path),
    )


def show_crypto_universe_readiness_report_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    report_rows = read_csv(data_path / OUTPUT_FILES["report"].name)
    summary_rows = read_csv(data_path / OUTPUT_FILES["summary"].name)
    if not report_rows:
        return 1, ["Run `python bot.py --crypto-universe-readiness-report` first."]
    approval_values = {str(row.get("execution_approved", "")).lower() for row in report_rows + summary_rows}
    return 0, [
        "Crypto universe readiness report. Display only; execution_approved=False.",
        f"Count by research_universe_status: {status_counts(report_rows)}",
        f"Eligible symbols: {symbols_by_status(report_rows, ['crypto_strategy_research_eligible'])}",
        f"Watchlist symbols: {symbols_by_status(report_rows, ['crypto_watchlist_data_short', 'crypto_watchlist_high_volatility', 'crypto_manual_review_required'])}",
        f"Rejected symbols: {symbols_by_status(report_rows, ['crypto_reject_missing_data', 'crypto_reject_insufficient_history', 'crypto_reject_duplicate_or_transition_unclear'])}",
        f"Insufficient history: {symbols_by_status(report_rows, ['crypto_watchlist_data_short', 'crypto_reject_insufficient_history'])}",
        f"Missing/latest data issues: {symbols_with_data_issues(report_rows)}",
        f"Top 5 by latest 252-day momentum: {top_symbols(report_rows, 'latest_252d_momentum', descending=True)}",
        f"Highest volatility symbols: {top_symbols(report_rows, 'approx_annualised_volatility', descending=True)}",
        f"execution_approved values: {', '.join(sorted(approval_values)) or 'false'}",
        "Warning: crypto universe readiness does not add strategies, approve preview promotion, or approve execution; it does not approve execution.",
    ]


def download_universe_daily_history(symbols: list[str]) -> dict[str, dict[str, Any]]:
    try:
        import yfinance as yf
    except Exception as exc:  # pragma: no cover - environment dependent
        return {symbol: {"rows": [], "error": f"yfinance import failed: {exc}", "missing_close_count": 0, "duplicate_date_count": 0} for symbol in symbols}

    results: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        try:
            data = yf.download(symbol, period="10y", interval="1d", progress=False, auto_adjust=False, threads=False)
        except Exception as exc:
            results[symbol] = {"rows": [], "error": str(exc), "missing_close_count": 0, "duplicate_date_count": 0}
            continue
        results[symbol] = normalize_history(data, symbol)
    return results


def normalize_history(data: Any, symbol: str) -> dict[str, Any]:
    if data is None or getattr(data, "empty", True):
        return {"rows": [], "error": "No daily crypto data returned by yfinance.", "missing_close_count": 0, "duplicate_date_count": 0}

    seen_dates: set[str] = set()
    rows: list[dict[str, Any]] = []
    missing_close_count = 0
    duplicate_date_count = 0
    for index, row in data.iterrows():
        date_value = index.date().isoformat()
        if date_value in seen_dates:
            duplicate_date_count += 1
            continue
        seen_dates.add(date_value)
        close = value_from_row(row, "Close", symbol)
        if close is None or close <= 0:
            missing_close_count += 1
            continue
        rows.append({"date": date_value, "close": close})
    return {"rows": rows, "error": "", "missing_close_count": missing_close_count, "duplicate_date_count": duplicate_date_count}


def build_symbol_row(
    created_at: str,
    symbol: str,
    display_name: str,
    result: dict[str, Any],
    transition_symbols: set[str],
) -> dict[str, Any]:
    rows = result.get("rows", [])
    error = result.get("error", "")
    closes = [float(row["close"]) for row in rows]
    returns = daily_returns(closes)
    row_count = len(rows)
    latest_close = closes[-1] if closes else ""
    first_date = rows[0]["date"] if rows else ""
    latest_date = rows[-1]["date"] if rows else ""
    missing_close_count = int(result.get("missing_close_count", 0))
    duplicate_date_count = int(result.get("duplicate_date_count", 0))
    enough_200d = row_count >= 201
    enough_252d = row_count >= 253
    enough_split = row_count >= 504
    daily_vol = statistics.stdev(returns) if len(returns) >= 2 else ""
    annual_vol = daily_vol * math.sqrt(365) if daily_vol != "" else ""
    max_dd = max_drawdown(closes) if closes else ""
    trend_state = trend_200d_state(closes) if enough_200d else ""
    momentum_126 = momentum(closes, 126) if row_count > 126 else ""
    momentum_252 = momentum(closes, 252) if row_count > 252 else ""
    status, eligible, reason = classify_symbol(
        symbol=symbol,
        row_count=row_count,
        error=error,
        missing_close_count=missing_close_count,
        duplicate_date_count=duplicate_date_count,
        enough_200d=enough_200d,
        enough_252d=enough_252d,
        enough_split=enough_split,
        annual_vol=annual_vol,
        transition_symbols=transition_symbols,
    )
    return {
        "created_at": created_at,
        "symbol": symbol,
        "display_asset_name": display_name,
        "data_status": "data_available" if rows else "data_unavailable",
        "first_date": first_date,
        "latest_date": latest_date,
        "row_count": row_count,
        "latest_close": round(latest_close, 8) if latest_close != "" else "",
        "missing_close_count": missing_close_count,
        "duplicate_date_count": duplicate_date_count,
        "enough_history_for_200d_trend": enough_200d,
        "enough_history_for_252d_volatility": enough_252d,
        "enough_history_for_fixed_split_research": enough_split,
        "approx_daily_volatility": round(daily_vol, 6) if daily_vol != "" else "",
        "approx_annualised_volatility": round(annual_vol, 6) if annual_vol != "" else "",
        "max_drawdown": round(max_dd, 6) if max_dd != "" else "",
        "latest_200d_trend_state": trend_state,
        "latest_126d_momentum": round(momentum_126, 6) if momentum_126 != "" else "",
        "latest_252d_momentum": round(momentum_252, 6) if momentum_252 != "" else "",
        "research_universe_status": status,
        "strategy_research_eligible": eligible,
        "reason": reason if not error else f"{reason}; data_error={error}",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def classify_symbol(
    *,
    symbol: str,
    row_count: int,
    error: str,
    missing_close_count: int,
    duplicate_date_count: int,
    enough_200d: bool,
    enough_252d: bool,
    enough_split: bool,
    annual_vol: float | str,
    transition_symbols: set[str],
) -> tuple[str, bool, str]:
    if row_count == 0:
        return "crypto_reject_missing_data", False, "No usable daily close data was available."
    if symbol in transition_symbols:
        return "crypto_reject_duplicate_or_transition_unclear", False, "POL/MATIC transition requires manual symbol review before strategy eligibility."
    if duplicate_date_count > 0:
        return "crypto_reject_duplicate_or_transition_unclear", False, "Duplicate daily rows require manual data review."
    if missing_close_count > 0:
        return "crypto_manual_review_required", False, "Missing close rows require manual data review."
    if not enough_200d or not enough_252d:
        return "crypto_reject_insufficient_history", False, "Not enough history for 200-day trend and 252-day volatility."
    if not enough_split:
        return "crypto_watchlist_data_short", False, "Enough trend/volatility history, but not enough for fixed split research."
    if isinstance(annual_vol, float) and annual_vol > 2.5:
        return "crypto_watchlist_high_volatility", False, "Very high realised volatility; keep for manual research review rather than automatic eligibility."
    if error:
        return "crypto_manual_review_required", False, "Data returned with a provider warning that requires review."
    if symbol in {"BTC-USD", "ETH-USD"}:
        return "crypto_strategy_research_eligible", True, "Core crypto benchmark with sufficient clean history."
    return "crypto_strategy_research_eligible", True, "Sufficient clean history for later research-only strategy testing."


def symbols_with_transition_issue(downloaded: dict[str, dict[str, Any]]) -> set[str]:
    pol_has_data = bool(downloaded.get("POL-USD", {}).get("rows"))
    matic_has_data = bool(downloaded.get("MATIC-USD", {}).get("rows"))
    return {"POL-USD", "MATIC-USD"} if pol_has_data and matic_has_data else set()


def build_summary_rows(created_at: str, report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["research_universe_status"] for row in report_rows)
    eligible = [row["symbol"] for row in report_rows if str(row["strategy_research_eligible"]).lower() == "true"]
    watchlist = [
        row["symbol"]
        for row in report_rows
        if row["research_universe_status"] in {"crypto_watchlist_data_short", "crypto_watchlist_high_volatility", "crypto_manual_review_required"}
    ]
    rejected = [
        row["symbol"]
        for row in report_rows
        if row["research_universe_status"].startswith("crypto_reject")
    ]
    return [
        summary_row(created_at, "status_counts", ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))),
        summary_row(created_at, "eligible_symbols", ", ".join(eligible) or "none"),
        summary_row(created_at, "watchlist_symbols", ", ".join(watchlist) or "none"),
        summary_row(created_at, "rejected_symbols", ", ".join(rejected) or "none"),
        summary_row(created_at, "pol_matic_transition", transition_summary(report_rows)),
        summary_row(created_at, "execution_boundary", "execution_approved=False for all rows; no crypto execution approved"),
    ]


def build_summary_lines(report_rows: list[dict[str, Any]], report_path: Path, summary_path: Path) -> list[str]:
    return [
        "Crypto universe readiness report complete. Research/report only; execution_approved=False.",
        f"Symbols tested: {', '.join(row['symbol'] for row in report_rows)}",
        f"Count by research_universe_status: {status_counts(report_rows)}",
        f"Eligible symbols: {symbols_by_status(report_rows, ['crypto_strategy_research_eligible'])}",
        f"Watchlist symbols: {symbols_by_status(report_rows, ['crypto_watchlist_data_short', 'crypto_watchlist_high_volatility', 'crypto_manual_review_required'])}",
        f"Rejected symbols: {symbols_by_status(report_rows, ['crypto_reject_missing_data', 'crypto_reject_insufficient_history', 'crypto_reject_duplicate_or_transition_unclear'])}",
        f"POL/MATIC transition: {transition_summary(report_rows)}",
        f"Saved report to {report_path}",
        f"Saved summary to {summary_path}",
        "Warning: crypto readiness does not add strategies, create order instructions, or approve execution.",
    ]


def summary_row(created_at: str, metric_name: str, metric_value: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "summary_name": "crypto_universe_readiness",
        "metric_name": metric_name,
        "metric_value": metric_value,
        "evidence": "Research-only universe readiness summary.",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def daily_returns(closes: list[float]) -> list[float]:
    return [(closes[index] / closes[index - 1]) - 1.0 for index in range(1, len(closes)) if closes[index - 1] > 0]


def momentum(closes: list[float], lookback: int) -> float | str:
    if len(closes) <= lookback or closes[-lookback - 1] <= 0:
        return ""
    return (closes[-1] / closes[-lookback - 1]) - 1.0


def trend_200d_state(closes: list[float]) -> str:
    sma200 = sum(closes[-200:]) / 200
    return "above_200d_sma" if closes[-1] >= sma200 else "below_200d_sma"


def max_drawdown(closes: list[float]) -> float:
    peak = closes[0]
    worst = 0.0
    for close in closes:
        if close > peak:
            peak = close
        if peak > 0:
            worst = min(worst, (close / peak) - 1.0)
    return worst


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(row.get("research_universe_status", "") for row in rows)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def symbols_by_status(rows: list[dict[str, Any]], statuses: list[str]) -> str:
    symbols = [row["symbol"] for row in rows if row.get("research_universe_status") in set(statuses)]
    return ", ".join(symbols) or "none"


def symbols_with_data_issues(rows: list[dict[str, Any]]) -> str:
    symbols = [
        row["symbol"]
        for row in rows
        if row.get("data_status") != "data_available"
        or str(row.get("missing_close_count", "0")) not in {"0", ""}
        or row.get("latest_close") in {"", None}
    ]
    return ", ".join(symbols) or "none"


def top_symbols(rows: list[dict[str, Any]], field: str, *, descending: bool) -> str:
    values = []
    for row in rows:
        try:
            value = float(row.get(field, ""))
        except (TypeError, ValueError):
            continue
        values.append((row["symbol"], value))
    values.sort(key=lambda item: item[1], reverse=descending)
    return ", ".join(f"{symbol}={round(value, 4)}" for symbol, value in values[:5]) or "unavailable"


def transition_summary(rows: list[dict[str, Any]]) -> str:
    statuses = {row["symbol"]: row["research_universe_status"] for row in rows if row["symbol"] in {"POL-USD", "MATIC-USD"}}
    if statuses.get("POL-USD") == "crypto_reject_duplicate_or_transition_unclear" and statuses.get("MATIC-USD") == "crypto_reject_duplicate_or_transition_unclear":
        return "both POL-USD and MATIC-USD returned data; transition requires manual review"
    return "no duplicate POL/MATIC data transition issue detected"


def value_from_row(row: Any, column_name: str, symbol: str) -> float | None:
    for key in (column_name, (column_name, symbol), (symbol, column_name)):
        try:
            value = row[key]
        except Exception:
            continue
        try:
            if hasattr(value, "iloc"):
                value = value.iloc[0]
            return float(value)
        except (TypeError, ValueError):
            return None
    return None


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
