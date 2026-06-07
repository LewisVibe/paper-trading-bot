"""Research-only crypto strategy report helpers.

This module reads saved crypto strategy lab results and ranks them against the
matching buy-and-hold benchmark by symbol and period. It does not fetch data,
call Alpaca, read positions, write SQLite, send Discord alerts, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CRYPTO_REPORT_COLUMNS = [
    "created_at",
    "strategy_name",
    "symbol",
    "data_symbol",
    "period",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "trade_count",
    "beats_buy_and_hold",
    "drawdown_reduction_vs_buy_and_hold_pct",
    "cagr_gap_vs_buy_and_hold_pct",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoStrategyReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_strategy_report(
    data_dir: Path | str = "data",
    input_filename: str = "crypto_strategy_lab_results.csv",
    output_filename: str = "crypto_strategy_report.csv",
) -> CryptoStrategyReportResult:
    data_path = Path(data_dir)
    input_path = data_path / input_filename
    if not input_path.exists():
        raise RuntimeError(f"Missing required crypto strategy lab results: {input_path}")
    input_rows = read_csv_rows(input_path)
    if not input_rows:
        raise RuntimeError(f"No usable rows in required crypto strategy lab results: {input_path}")

    rows = build_crypto_strategy_report_rows(input_rows)
    output_path = data_path / output_filename
    write_crypto_strategy_report(output_path, rows)
    return CryptoStrategyReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_crypto_strategy_report_summary(rows),
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [
            row
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def build_crypto_strategy_report_rows(input_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    created_at = datetime.now(timezone.utc).isoformat()
    benchmarks = {
        (row.get("symbol", ""), row.get("period", "")): row
        for row in input_rows
        if row.get("strategy_name") == "crypto_buy_and_hold_baseline"
    }
    rows = [
        build_crypto_strategy_report_row(created_at, row, benchmarks.get((row.get("symbol", ""), row.get("period", "")), {}))
        for row in input_rows
    ]
    rows.sort(
        key=lambda row: (
            row["symbol"],
            period_sort_order(row["period"]),
            -number_or_default(row["calmar_ratio"]),
            row["strategy_name"],
        )
    )
    return rows


def build_crypto_strategy_report_row(
    created_at: str,
    row: dict[str, str],
    benchmark_row: dict[str, str],
) -> dict[str, Any]:
    cagr = number_or_blank(row.get("cagr_pct", ""))
    sharpe = number_or_blank(row.get("sharpe_ratio", ""))
    drawdown = number_or_blank(row.get("max_drawdown_pct", ""))
    calmar = number_or_blank(row.get("calmar_ratio", ""))
    benchmark_cagr = number_or_blank(benchmark_row.get("cagr_pct", ""))
    benchmark_drawdown = number_or_blank(benchmark_row.get("max_drawdown_pct", ""))
    benchmark_calmar = number_or_blank(benchmark_row.get("calmar_ratio", ""))

    beats_buy_and_hold = (
        isinstance(cagr, (int, float))
        and isinstance(calmar, (int, float))
        and isinstance(benchmark_cagr, (int, float))
        and isinstance(benchmark_calmar, (int, float))
        and float(cagr) > float(benchmark_cagr)
        and float(calmar) > float(benchmark_calmar)
    )
    drawdown_reduction = (
        round(float(benchmark_drawdown) - float(drawdown), 4)
        if isinstance(benchmark_drawdown, (int, float)) and isinstance(drawdown, (int, float))
        else ""
    )
    cagr_gap = (
        round(float(cagr) - float(benchmark_cagr), 4)
        if isinstance(cagr, (int, float)) and isinstance(benchmark_cagr, (int, float))
        else ""
    )

    return {
        "created_at": created_at,
        "strategy_name": row.get("strategy_name", ""),
        "symbol": row.get("symbol", ""),
        "data_symbol": row.get("data_symbol", ""),
        "period": row.get("period", ""),
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": drawdown,
        "calmar_ratio": calmar,
        "trade_count": number_or_blank(row.get("number_of_trades", "")),
        "beats_buy_and_hold": beats_buy_and_hold,
        "drawdown_reduction_vs_buy_and_hold_pct": drawdown_reduction,
        "cagr_gap_vs_buy_and_hold_pct": cagr_gap,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def write_crypto_strategy_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CRYPTO_REPORT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CRYPTO_REPORT_COLUMNS})


def build_crypto_strategy_report_summary(rows: list[dict[str, Any]]) -> list[str]:
    return [
        "CRYPTO STRATEGY REPORT. RESEARCH ONLY. NOT EXECUTION.",
        best_symbol_period_line(rows, "BTC/USD", "full_period", "best BTC strategy by full-period Calmar"),
        best_symbol_period_line(rows, "ETH/USD", "full_period", "best ETH strategy by full-period Calmar"),
        best_symbol_period_line(rows, "BTC/USD", "out_of_sample", "best BTC strategy by out-of-sample Calmar"),
        best_symbol_period_line(rows, "ETH/USD", "out_of_sample", "best ETH strategy by out-of-sample Calmar"),
        "Warning: crypto research is not execution approval.",
    ]


def best_symbol_period_line(rows: list[dict[str, Any]], symbol: str, period: str, label: str) -> str:
    matches = [
        row
        for row in rows
        if row.get("symbol") == symbol and row.get("period") == period and isinstance(row.get("calmar_ratio"), (int, float))
    ]
    if not matches:
        return f"{label}: unavailable"
    best = sorted(matches, key=lambda row: (-float(row["calmar_ratio"]), row["strategy_name"]))[0]
    return f"{label}: {best['strategy_name']} (calmar_ratio={best['calmar_ratio']})"


def period_sort_order(period: str) -> int:
    return {"full_period": 0, "in_sample": 1, "out_of_sample": 2}.get(period, 99)


def number_or_blank(value: Any) -> float | str:
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def number_or_default(value: Any, default: float = -999999.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return default
