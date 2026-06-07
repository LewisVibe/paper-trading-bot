"""Preview current crypto research candidate signals.

This module is preview-only. It uses daily research market data to show whether
the current split-sensitive crypto research candidates would prefer long or
flat today. It does not call Alpaca, read positions, create orders, write
SQLite, send Discord alerts, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research.crypto_lab import (
    crypto_data_symbol,
    crypto_desired_long,
    download_crypto_daily_history,
    normalize_crypto_price_rows,
    rolling_average,
    rolling_median,
    rolling_realized_volatility,
    volatility_gate_allows_entry,
)


CRYPTO_SIGNAL_CANDIDATES: dict[str, str | None] = {
    "BTC/USD": "crypto_buy_above_200_with_vol_gate",
    "ETH/USD": "crypto_buy_above_200_exit_below_200",
    "LTC/USD": None,
}

CRYPTO_SIGNAL_PREVIEW_COLUMNS = [
    "created_at",
    "symbol",
    "data_symbol",
    "strategy_name",
    "latest_close",
    "sma_200",
    "close_above_sma_200",
    "realised_vol_20",
    "median_realised_vol_252",
    "vol_gate_threshold",
    "vol_gate_passed",
    "desired_position",
    "signal_reason",
    "research_status",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoSignalPreviewResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_signal_preview(
    data_dir: Path | str = "data",
    output_filename: str = "crypto_signal_preview.csv",
) -> CryptoSignalPreviewResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    decision_rows = read_optional_decision_rows(data_path / "crypto_strategy_decision_report.csv")
    price_data = {
        symbol: download_crypto_daily_history(crypto_data_symbol(symbol))
        for symbol, strategy_name in CRYPTO_SIGNAL_CANDIDATES.items()
        if strategy_name is not None
    }
    rows = build_crypto_signal_preview_rows(price_data, created_at, decision_rows)
    output_path = data_path / output_filename
    write_crypto_signal_preview(output_path, rows)
    return CryptoSignalPreviewResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_crypto_signal_preview_summary(rows, output_path),
    )


def build_crypto_signal_preview_rows(
    price_data: dict[str, list[dict[str, Any]]],
    created_at: str | None = None,
    decision_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    decisions_by_symbol = {str(row.get("symbol", "")): row for row in (decision_rows or [])}
    rows = []
    for symbol, strategy_name in CRYPTO_SIGNAL_CANDIDATES.items():
        if strategy_name is None:
            rows.append(build_no_decision_candidate_row(timestamp, symbol, decisions_by_symbol.get(symbol)))
        else:
            rows.append(build_crypto_signal_preview_row(timestamp, symbol, strategy_name, price_data.get(symbol, [])))
    return rows


def build_no_decision_candidate_row(
    created_at: str,
    symbol: str,
    decision_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision_status = str((decision_row or {}).get("decision_status", "")).strip()
    if decision_status:
        reason = f"{symbol_without_suffix(symbol)} decision status is {decision_status}; no signal candidate is selected."
        research_status = f"{decision_status}_research_only"
    else:
        reason = (
            f"No best {symbol_without_suffix(symbol)} research candidate has been selected yet; "
            "run crypto lab/report/decision research before previewing a signal."
        )
        research_status = "no_decision_candidate_yet_research_only"
    return base_preview_row(
        created_at,
        symbol,
        crypto_data_symbol(symbol),
        "no_decision_candidate_yet",
        reason,
        desired_position="flat",
        research_status=research_status,
    )


def symbol_without_suffix(symbol: str) -> str:
    return symbol.split("/", 1)[0]


def build_crypto_signal_preview_row(
    created_at: str,
    symbol: str,
    strategy_name: str,
    raw_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    data_symbol = crypto_data_symbol(symbol)
    rows = normalize_crypto_price_rows(raw_rows)
    if len(rows) < 272:
        return base_preview_row(
            created_at,
            symbol,
            data_symbol,
            strategy_name,
            signal_reason="Not enough daily history for SMA200 plus 252-day volatility median.",
        )

    closes = [float(row["close"]) for row in rows]
    latest_close = closes[-1]
    sma_200 = rolling_average(closes, 200)[-1]
    realised_vol_20 = rolling_realized_volatility(closes, 20)[-1]
    median_realised_vol_252 = rolling_median(rolling_realized_volatility(closes, 20), 252)[-1]
    close_above_sma_200 = sma_200 is not None and latest_close > sma_200
    vol_gate_threshold = (
        round(1.5 * median_realised_vol_252, 6)
        if median_realised_vol_252 is not None
        else ""
    )
    vol_gate_passed = volatility_gate_allows_entry(realised_vol_20, median_realised_vol_252)

    if strategy_name == "crypto_buy_above_200_with_vol_gate":
        desired_long = crypto_desired_long(
            "close_above_200_vol_gate",
            latest_close,
            None,
            sma_200,
            realised_vol_20,
            median_realised_vol_252,
            already_long=False,
        )
        reason = btc_signal_reason(close_above_sma_200, vol_gate_passed)
    else:
        desired_long = crypto_desired_long("close_above_200", latest_close, None, sma_200)
        reason = eth_signal_reason(close_above_sma_200)

    return {
        "created_at": created_at,
        "symbol": symbol,
        "data_symbol": data_symbol,
        "strategy_name": strategy_name,
        "latest_close": round(latest_close, 6),
        "sma_200": round(sma_200, 6) if sma_200 is not None else "",
        "close_above_sma_200": close_above_sma_200,
        "realised_vol_20": round(realised_vol_20, 6) if realised_vol_20 is not None else "",
        "median_realised_vol_252": round(median_realised_vol_252, 6) if median_realised_vol_252 is not None else "",
        "vol_gate_threshold": vol_gate_threshold,
        "vol_gate_passed": vol_gate_passed if strategy_name == "crypto_buy_above_200_with_vol_gate" else "",
        "desired_position": "long" if desired_long else "flat",
        "signal_reason": reason,
        "research_status": "split_sensitive_research_candidate_not_execution_approved",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def base_preview_row(
    created_at: str,
    symbol: str,
    data_symbol: str,
    strategy_name: str,
    signal_reason: str,
    desired_position: str = "flat",
    research_status: str = "split_sensitive_research_candidate_not_execution_approved",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "symbol": symbol,
        "data_symbol": data_symbol,
        "strategy_name": strategy_name,
        "latest_close": "",
        "sma_200": "",
        "close_above_sma_200": "",
        "realised_vol_20": "",
        "median_realised_vol_252": "",
        "vol_gate_threshold": "",
        "vol_gate_passed": "",
        "desired_position": desired_position,
        "signal_reason": signal_reason,
        "research_status": research_status,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def btc_signal_reason(close_above_sma_200: bool, vol_gate_passed: bool) -> str:
    if close_above_sma_200 and vol_gate_passed:
        return "BTC close is above SMA200 and the fixed volatility gate passes."
    if not close_above_sma_200:
        return "BTC close is at or below SMA200."
    return "BTC close is above SMA200, but the fixed volatility gate blocks new long exposure."


def eth_signal_reason(close_above_sma_200: bool) -> str:
    if close_above_sma_200:
        return "ETH close is above SMA200."
    return "ETH close is at or below SMA200."


def write_crypto_signal_preview(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CRYPTO_SIGNAL_PREVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CRYPTO_SIGNAL_PREVIEW_COLUMNS})


def read_optional_decision_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [row for row in reader if any((value or "").strip() for value in row.values())]


def build_crypto_signal_preview_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    return [
        "CRYPTO SIGNAL PREVIEW. RESEARCH ONLY. NOT EXECUTION.",
        preview_line(rows, "BTC/USD"),
        preview_line(rows, "ETH/USD"),
        preview_line(rows, "LTC/USD"),
        "Warning: these are split-sensitive research candidates, not execution approval.",
        f"Saved crypto signal preview to {output_path}",
    ]


def preview_line(rows: list[dict[str, Any]], symbol: str) -> str:
    row = next((candidate for candidate in rows if candidate.get("symbol") == symbol), None)
    if row is None:
        return f"{symbol}: unavailable"
    return f"{symbol}: desired_position={row['desired_position']} ({row['signal_reason']})"
