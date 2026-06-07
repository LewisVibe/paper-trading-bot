"""Saved-data-only crypto period diagnostics.

This report explains weak fixed-split crypto robustness periods. It reads saved
research CSVs only and does not fetch data, call Alpaca, read positions, create
orders, write SQLite, send Discord alerts, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FOCUS_CANDIDATES = {
    ("BTC/USD", "crypto_buy_above_200_with_vol_gate"),
    ("ETH/USD", "crypto_buy_above_200_exit_below_200"),
}

CRYPTO_PERIOD_DIAGNOSTICS_COLUMNS = [
    "created_at",
    "symbol",
    "strategy_name",
    "split_name",
    "out_of_sample_start_date",
    "out_of_sample_end_date",
    "strategy_oos_cagr_pct",
    "benchmark_oos_cagr_pct",
    "cagr_gap_vs_benchmark_oos",
    "strategy_oos_max_drawdown_pct",
    "benchmark_oos_max_drawdown_pct",
    "drawdown_reduction_oos_pct",
    "number_of_oos_trades",
    "percentage_time_in_market",
    "percentage_time_in_cash",
    "average_holding_period_days",
    "worst_drawdown_start_date",
    "worst_drawdown_end_date",
    "diagnostic_label",
    "diagnostic_reason",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoPeriodDiagnosticsResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_period_diagnostics(
    data_dir: Path | str = "data",
    robustness_filename: str = "crypto_robustness_report.csv",
    lab_results_filename: str = "crypto_strategy_lab_results.csv",
    lab_trades_filename: str = "crypto_strategy_lab_trades.csv",
    output_filename: str = "crypto_period_diagnostics.csv",
) -> CryptoPeriodDiagnosticsResult:
    data_path = Path(data_dir)
    robustness_path = data_path / robustness_filename
    lab_results_path = data_path / lab_results_filename
    lab_trades_path = data_path / lab_trades_filename
    if not robustness_path.exists():
        raise RuntimeError(f"Missing required crypto robustness report: {robustness_path}")
    robustness_rows = read_csv_rows(robustness_path)
    lab_result_rows = read_csv_rows(lab_results_path) if lab_results_path.exists() else []
    trade_rows = read_csv_rows(lab_trades_path) if lab_trades_path.exists() else []

    rows = build_crypto_period_diagnostic_rows(robustness_rows, lab_result_rows, trade_rows)
    output_path = data_path / output_filename
    write_crypto_period_diagnostics(output_path, rows)
    return CryptoPeriodDiagnosticsResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_crypto_period_diagnostics_summary(rows),
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [row for row in reader if any((value or "").strip() for value in row.values())]


def build_crypto_period_diagnostic_rows(
    robustness_rows: list[dict[str, str]],
    lab_result_rows: list[dict[str, str]] | None = None,
    trade_rows: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    created_at = datetime.now(timezone.utc).isoformat()
    trades = trade_rows or []
    lab_lookup = {
        (row.get("symbol", ""), row.get("strategy_name", ""), row.get("period", "")): row
        for row in (lab_result_rows or [])
    }
    rows = []
    for row in robustness_rows:
        key = (row.get("symbol", ""), row.get("strategy_name", ""))
        if key not in FOCUS_CANDIDATES:
            continue
        diagnostic = build_diagnostic_row(created_at, row, lab_lookup, trades)
        rows.append(diagnostic)
    return sorted(rows, key=lambda row: (row["symbol"], row["strategy_name"], row["split_name"]))


def build_diagnostic_row(
    created_at: str,
    robustness_row: dict[str, str],
    lab_lookup: dict[tuple[str, str, str], dict[str, str]],
    trade_rows: list[dict[str, str]],
) -> dict[str, Any]:
    symbol = robustness_row.get("symbol", "")
    strategy_name = robustness_row.get("strategy_name", "")
    split_name = robustness_row.get("split_name", "")
    start_date = robustness_row.get("out_of_sample_start_date", "")
    end_date = robustness_row.get("out_of_sample_end_date", "")
    matching_trades = trades_in_window(trade_rows, symbol, strategy_name, start_date, end_date)
    trade_count = int_or_number(robustness_row.get("out_of_sample_trade_count", ""), len(matching_trades))
    time_in_market = estimate_time_in_market_pct(
        start_date,
        end_date,
        matching_trades,
        default_if_trades_missing(symbol, strategy_name, lab_lookup),
    )
    average_holding_days = average_holding_period_days(matching_trades, end_date)
    label, reason = classify_period_diagnostic(
        strategy_cagr=number_or_blank(robustness_row.get("out_of_sample_cagr_pct", "")),
        benchmark_cagr=number_or_blank(robustness_row.get("benchmark_oos_cagr_pct", "")),
        cagr_gap=number_or_blank(robustness_row.get("cagr_gap_vs_benchmark_oos", "")),
        calmar=number_or_blank(robustness_row.get("out_of_sample_calmar", "")),
        trade_count=trade_count,
        time_in_market_pct=time_in_market,
    )
    return {
        "created_at": created_at,
        "symbol": symbol,
        "strategy_name": strategy_name,
        "split_name": split_name,
        "out_of_sample_start_date": start_date,
        "out_of_sample_end_date": end_date,
        "strategy_oos_cagr_pct": number_or_blank(robustness_row.get("out_of_sample_cagr_pct", "")),
        "benchmark_oos_cagr_pct": number_or_blank(robustness_row.get("benchmark_oos_cagr_pct", "")),
        "cagr_gap_vs_benchmark_oos": number_or_blank(robustness_row.get("cagr_gap_vs_benchmark_oos", "")),
        "strategy_oos_max_drawdown_pct": number_or_blank(robustness_row.get("out_of_sample_max_drawdown_pct", "")),
        "benchmark_oos_max_drawdown_pct": number_or_blank(robustness_row.get("benchmark_oos_max_drawdown_pct", "")),
        "drawdown_reduction_oos_pct": number_or_blank(robustness_row.get("drawdown_reduction_oos_pct", "")),
        "number_of_oos_trades": trade_count,
        "percentage_time_in_market": round(time_in_market, 4),
        "percentage_time_in_cash": round(100.0 - time_in_market, 4),
        "average_holding_period_days": average_holding_days,
        "worst_drawdown_start_date": "",
        "worst_drawdown_end_date": "",
        "diagnostic_label": label,
        "diagnostic_reason": reason,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def classify_period_diagnostic(
    strategy_cagr: float | str,
    benchmark_cagr: float | str,
    cagr_gap: float | str,
    calmar: float | str,
    trade_count: int,
    time_in_market_pct: float,
) -> tuple[str, str]:
    if not isinstance(strategy_cagr, (int, float)) or not isinstance(benchmark_cagr, (int, float)):
        return "insufficient_data", "Missing numeric out-of-sample CAGR diagnostics."
    if strategy_cagr < 0 and benchmark_cagr < strategy_cagr:
        return (
            "benchmark_also_weak",
            "Strategy return is negative, but buy-and-hold was worse in the same split.",
        )
    if time_in_market_pct < 35 and strategy_cagr <= 5:
        return (
            "cash_drag",
            "Strategy spent most of the out-of-sample window in cash and return was weak.",
        )
    if trade_count >= 4 and strategy_cagr <= 0:
        return (
            "whipsaw_sensitive",
            "Many trades occurred in a weak out-of-sample window with poor returns.",
        )
    if strategy_cagr > 0 and isinstance(calmar, (int, float)) and calmar < 0.35:
        return (
            "profitable_but_weakening",
            "Out-of-sample return is positive, but risk-adjusted performance is weak.",
        )
    if strategy_cagr <= 3 and isinstance(cagr_gap, (int, float)) and cagr_gap > 0:
        return (
            "defensive_but_low_return",
            "Strategy improved versus benchmark but absolute return remains low.",
        )
    return (
        "defensive_but_low_return",
        "Strategy appears defensive, but diagnostics do not support calling it robust.",
    )


def trades_in_window(
    trade_rows: list[dict[str, str]],
    symbol: str,
    strategy_name: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, str]]:
    return [
        trade
        for trade in trade_rows
        if trade.get("symbol") == symbol
        and trade.get("strategy_name") == strategy_name
        and start_date <= trade.get("date", "") <= end_date
    ]


def estimate_time_in_market_pct(
    start_date: str,
    end_date: str,
    trades: list[dict[str, str]],
    default_pct: float,
) -> float:
    total_days = days_between(start_date, end_date)
    if total_days <= 0 or not trades:
        return default_pct
    sorted_trades = sorted(trades, key=lambda trade: trade.get("date", ""))
    in_position = False
    current_start = ""
    market_days = 0
    for trade in sorted_trades:
        side = (trade.get("side") or "").lower()
        trade_date = trade.get("date", "")
        if side == "buy" and not in_position:
            in_position = True
            current_start = max(start_date, trade_date)
        elif side == "sell" and in_position:
            market_days += max(0, days_between(current_start, trade_date))
            in_position = False
            current_start = ""
    if in_position:
        market_days += max(0, days_between(current_start, end_date))
    return min(100.0, max(0.0, (market_days / total_days) * 100))


def average_holding_period_days(trades: list[dict[str, str]], end_date: str) -> float | str:
    holding_periods: list[int] = []
    entry_date = ""
    for trade in sorted(trades, key=lambda trade: trade.get("date", "")):
        side = (trade.get("side") or "").lower()
        if side == "buy" and not entry_date:
            entry_date = trade.get("date", "")
        elif side == "sell" and entry_date:
            holding_periods.append(days_between(entry_date, trade.get("date", "")))
            entry_date = ""
    if entry_date:
        holding_periods.append(days_between(entry_date, end_date))
    if not holding_periods:
        return ""
    return round(sum(holding_periods) / len(holding_periods), 2)


def default_if_trades_missing(
    symbol: str,
    strategy_name: str,
    lab_lookup: dict[tuple[str, str, str], dict[str, str]],
) -> float:
    lab_row = lab_lookup.get((symbol, strategy_name, "out_of_sample"), {})
    if number_or_blank(lab_row.get("number_of_trades", "")) == 0:
        return 0.0
    return 50.0


def days_between(start_date: str, end_date: str) -> int:
    try:
        start = datetime.fromisoformat(start_date[:10])
        end = datetime.fromisoformat(end_date[:10])
    except ValueError:
        return 0
    return max(0, (end - start).days + 1)


def write_crypto_period_diagnostics(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CRYPTO_PERIOD_DIAGNOSTICS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CRYPTO_PERIOD_DIAGNOSTICS_COLUMNS})


def build_crypto_period_diagnostics_summary(rows: list[dict[str, Any]]) -> list[str]:
    btc_80 = row_for(rows, "BTC/USD", "crypto_buy_above_200_with_vol_gate", "split_80_20")
    eth_80 = row_for(rows, "ETH/USD", "crypto_buy_above_200_exit_below_200", "split_80_20")
    cash_drag = label_rows(rows, "cash_drag")
    whipsaw = label_rows(rows, "whipsaw_sensitive")
    return [
        "CRYPTO PERIOD DIAGNOSTICS. RESEARCH ONLY. NOT EXECUTION.",
        diagnostic_line("BTC 80/20", btc_80),
        diagnostic_line("ETH 80/20", eth_80),
        "Cash-drag periods: " + (", ".join(cash_drag) if cash_drag else "none"),
        "Whipsaw-sensitive periods: " + (", ".join(whipsaw) if whipsaw else "none"),
        "Warning: crypto diagnostics are research-only and not execution approval.",
    ]


def row_for(rows: list[dict[str, Any]], symbol: str, strategy_name: str, split_name: str) -> dict[str, Any] | None:
    return next(
        (
            row for row in rows
            if row.get("symbol") == symbol
            and row.get("strategy_name") == strategy_name
            and row.get("split_name") == split_name
        ),
        None,
    )


def diagnostic_line(label: str, row: dict[str, Any] | None) -> str:
    if row is None:
        return f"{label}: unavailable"
    return f"{label}: {row['diagnostic_label']} - {row['diagnostic_reason']}"


def label_rows(rows: list[dict[str, Any]], label: str) -> list[str]:
    return sorted({
        f"{row['symbol']}:{row['strategy_name']}:{row['split_name']}"
        for row in rows
        if row.get("diagnostic_label") == label
    })


def number_or_blank(value: Any) -> float | str:
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def int_or_number(value: Any, fallback: int = 0) -> int:
    parsed = number_or_blank(value)
    if isinstance(parsed, (int, float)):
        return int(parsed)
    return fallback
