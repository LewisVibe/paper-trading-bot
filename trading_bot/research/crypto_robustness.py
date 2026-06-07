"""Research-only crypto robustness report across fixed chronological splits.

This module reruns the existing per-symbol crypto research strategies across
fixed split points. It does not add strategies, call Alpaca, read positions,
create orders, write SQLite, send Discord alerts, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research.crypto_lab import (
    CRYPTO_STRATEGIES,
    CRYPTO_SYMBOL_MAP,
    CryptoResearchCostModel,
    crypto_data_symbol,
    crypto_result_row,
    download_crypto_daily_history,
    filter_crypto_trades_for_period,
    normalize_crypto_price_rows,
    simulate_crypto_strategy,
)


CRYPTO_ROBUSTNESS_SPLITS = [
    ("split_60_40", 0.60),
    ("split_70_30", 0.70),
    ("split_80_20", 0.80),
]

CRYPTO_ROBUSTNESS_COLUMNS = [
    "created_at",
    "symbol",
    "strategy_name",
    "split_name",
    "in_sample_fraction",
    "split_start_date",
    "split_point_date",
    "out_of_sample_start_date",
    "out_of_sample_end_date",
    "out_of_sample_cagr_pct",
    "out_of_sample_sharpe",
    "out_of_sample_max_drawdown_pct",
    "out_of_sample_calmar",
    "out_of_sample_trade_count",
    "benchmark_oos_cagr_pct",
    "benchmark_oos_sharpe",
    "benchmark_oos_max_drawdown_pct",
    "benchmark_oos_calmar",
    "cagr_gap_vs_benchmark_oos",
    "calmar_gap_vs_benchmark_oos",
    "beats_buy_and_hold_oos",
    "drawdown_reduction_oos_pct",
    "robustness_status",
    "robustness_reason",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoRobustnessReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_robustness_report(
    data_dir: Path | str = "data",
    output_filename: str = "crypto_robustness_report.csv",
) -> CryptoRobustnessReportResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    price_data = {
        symbol: download_crypto_daily_history(data_symbol)
        for symbol, data_symbol in CRYPTO_SYMBOL_MAP.items()
    }
    rows = build_crypto_robustness_rows(price_data, created_at)
    output_path = data_path / output_filename
    write_crypto_robustness_report(output_path, rows)
    return CryptoRobustnessReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_crypto_robustness_summary(rows),
    )


def build_crypto_robustness_rows(
    price_data: dict[str, list[dict[str, Any]]],
    created_at: str | None = None,
    cost_model: CryptoResearchCostModel | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    crypto_cost_model = cost_model or CryptoResearchCostModel()
    rows: list[dict[str, Any]] = []

    for symbol, raw_rows in price_data.items():
        data_symbol = crypto_data_symbol(symbol)
        price_rows = normalize_crypto_price_rows(raw_rows)
        if len(price_rows) < 205:
            rows.extend(build_insufficient_rows(timestamp, symbol))
            continue

        symbol_rows: list[dict[str, Any]] = []
        for strategy_name in CRYPTO_STRATEGIES:
            equity_curve, trades = simulate_crypto_strategy(
                strategy_name,
                price_rows,
                timestamp,
                symbol,
                data_symbol,
                crypto_cost_model,
            )
            for split_name, split_fraction in CRYPTO_ROBUSTNESS_SPLITS:
                symbol_rows.append(
                    build_split_metric_row(
                        timestamp,
                        symbol,
                        strategy_name,
                        split_name,
                        split_fraction,
                        equity_curve,
                        trades,
                        crypto_cost_model,
                    )
                )
        rows.extend(add_benchmark_comparisons_and_status(symbol_rows))

    return sorted(
        rows,
        key=lambda row: (
            row["symbol"],
            row["strategy_name"],
            split_sort_order(row["split_name"]),
        ),
    )


def build_split_metric_row(
    created_at: str,
    symbol: str,
    strategy_name: str,
    split_name: str,
    split_fraction: float,
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    cost_model: CryptoResearchCostModel,
) -> dict[str, Any]:
    split_index = split_index_for_length(len(equity_curve), split_fraction)
    out_of_sample_curve = equity_curve[split_index:]
    out_of_sample_trades = filter_crypto_trades_for_period(trades, out_of_sample_curve)
    metric_row = crypto_result_row(
        created_at,
        strategy_name,
        symbol,
        crypto_data_symbol(symbol),
        "out_of_sample",
        [float(row["equity"]) for row in out_of_sample_curve],
        len(out_of_sample_trades),
        cost_model,
    )
    return {
        "created_at": created_at,
        "symbol": symbol,
        "strategy_name": strategy_name,
        "split_name": split_name,
        "in_sample_fraction": split_fraction,
        "split_start_date": date_at(equity_curve, 0),
        "split_point_date": date_at(equity_curve, split_index),
        "out_of_sample_start_date": date_at(out_of_sample_curve, 0),
        "out_of_sample_end_date": date_at(out_of_sample_curve, len(out_of_sample_curve) - 1),
        "out_of_sample_cagr_pct": metric_row["cagr_pct"],
        "out_of_sample_sharpe": metric_row["sharpe_ratio"],
        "out_of_sample_max_drawdown_pct": metric_row["max_drawdown_pct"],
        "out_of_sample_calmar": metric_row["calmar_ratio"],
        "out_of_sample_trade_count": metric_row["number_of_trades"],
        "benchmark_oos_cagr_pct": "",
        "benchmark_oos_sharpe": "",
        "benchmark_oos_max_drawdown_pct": "",
        "benchmark_oos_calmar": "",
        "cagr_gap_vs_benchmark_oos": "",
        "calmar_gap_vs_benchmark_oos": "",
        "beats_buy_and_hold_oos": False,
        "drawdown_reduction_oos_pct": "",
        "robustness_status": "",
        "robustness_reason": "",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def split_index_for_length(row_count: int, split_fraction: float) -> int:
    if row_count < 3:
        return 0
    split_index = int(row_count * split_fraction)
    return max(1, min(row_count - 1, split_index))


def date_at(rows: list[dict[str, Any]], index: int) -> str:
    if not rows:
        return ""
    safe_index = max(0, min(len(rows) - 1, index))
    return str(rows[safe_index].get("date", ""))


def add_benchmark_comparisons_and_status(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    benchmarks = {
        (row["symbol"], row["split_name"]): row
        for row in rows
        if row["strategy_name"] == "crypto_buy_and_hold_baseline"
    }
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        benchmark = benchmarks.get((row["symbol"], row["split_name"]))
        add_benchmark_metrics(row, benchmark)
        row["beats_buy_and_hold_oos"] = beats_benchmark(row, benchmark)
        row["drawdown_reduction_oos_pct"] = drawdown_reduction(row, benchmark)
        grouped.setdefault((row["symbol"], row["strategy_name"]), []).append(row)

    for group_rows in grouped.values():
        status, reason = classify_crypto_robustness(group_rows)
        for row in group_rows:
            row["robustness_status"] = status
            row["robustness_reason"] = reason
    return rows


def add_benchmark_metrics(row: dict[str, Any], benchmark: dict[str, Any] | None) -> None:
    if benchmark is None:
        return
    row["benchmark_oos_cagr_pct"] = benchmark.get("out_of_sample_cagr_pct", "")
    row["benchmark_oos_sharpe"] = benchmark.get("out_of_sample_sharpe", "")
    row["benchmark_oos_max_drawdown_pct"] = benchmark.get("out_of_sample_max_drawdown_pct", "")
    row["benchmark_oos_calmar"] = benchmark.get("out_of_sample_calmar", "")
    row["cagr_gap_vs_benchmark_oos"] = round(
        number(row.get("out_of_sample_cagr_pct")) - number(benchmark.get("out_of_sample_cagr_pct")),
        4,
    )
    row["calmar_gap_vs_benchmark_oos"] = round(
        number(row.get("out_of_sample_calmar")) - number(benchmark.get("out_of_sample_calmar")),
        4,
    )


def beats_benchmark(row: dict[str, Any], benchmark: dict[str, Any] | None) -> bool:
    if benchmark is None or row["strategy_name"] == "crypto_buy_and_hold_baseline":
        return False
    return (
        number(row.get("out_of_sample_cagr_pct")) > number(benchmark.get("out_of_sample_cagr_pct"))
        and number(row.get("out_of_sample_calmar")) > number(benchmark.get("out_of_sample_calmar"))
    )


def drawdown_reduction(row: dict[str, Any], benchmark: dict[str, Any] | None) -> float | str:
    if benchmark is None:
        return ""
    return round(
        number(benchmark.get("out_of_sample_max_drawdown_pct"))
        - number(row.get("out_of_sample_max_drawdown_pct")),
        4,
    )


def classify_crypto_robustness(rows: list[dict[str, Any]]) -> tuple[str, str]:
    if len(rows) < len(CRYPTO_ROBUSTNESS_SPLITS):
        return "insufficient_data", "Missing one or more fixed split rows."
    usable_rows = [
        row for row in rows if isinstance(row.get("out_of_sample_cagr_pct"), (int, float))
    ]
    if len(usable_rows) < len(CRYPTO_ROBUSTNESS_SPLITS):
        return "insufficient_data", "Missing numeric out-of-sample metrics."

    positive_splits = [
        row
        for row in usable_rows
        if number(row.get("out_of_sample_cagr_pct")) > 0
        and number(row.get("out_of_sample_calmar")) > 0.25
        and number(row.get("out_of_sample_max_drawdown_pct")) < 65
    ]
    benchmark_beats = [row for row in usable_rows if row.get("beats_buy_and_hold_oos") is True]
    negative_splits = [row for row in usable_rows if number(row.get("out_of_sample_cagr_pct")) <= 0]

    if len(positive_splits) == len(CRYPTO_ROBUSTNESS_SPLITS) and len(benchmark_beats) >= 2:
        return "robust_candidate", "Positive OOS CAGR and usable Calmar across all fixed splits, with benchmark improvement on multiple splits."
    if len(positive_splits) >= 2:
        return "split_sensitive", "Looks usable on more than one split but does not consistently beat benchmark across fixed splits."
    if negative_splits:
        return "weak_candidate", "One or more fixed splits has negative out-of-sample CAGR."
    return "weak_candidate", "Out-of-sample risk-adjusted metrics are not strong enough across fixed splits."


def build_insufficient_rows(created_at: str, symbol: str) -> list[dict[str, Any]]:
    rows = []
    for strategy_name in CRYPTO_STRATEGIES:
        for split_name, split_fraction in CRYPTO_ROBUSTNESS_SPLITS:
            rows.append(
                {
                    "created_at": created_at,
                    "symbol": symbol,
                    "strategy_name": strategy_name,
                    "split_name": split_name,
                    "in_sample_fraction": split_fraction,
                    "split_start_date": "",
                    "split_point_date": "",
                    "out_of_sample_start_date": "",
                    "out_of_sample_end_date": "",
                    "out_of_sample_cagr_pct": "",
                    "out_of_sample_sharpe": "",
                    "out_of_sample_max_drawdown_pct": "",
                    "out_of_sample_calmar": "",
                    "out_of_sample_trade_count": 0,
                    "benchmark_oos_cagr_pct": "",
                    "benchmark_oos_sharpe": "",
                    "benchmark_oos_max_drawdown_pct": "",
                    "benchmark_oos_calmar": "",
                    "cagr_gap_vs_benchmark_oos": "",
                    "calmar_gap_vs_benchmark_oos": "",
                    "beats_buy_and_hold_oos": False,
                    "drawdown_reduction_oos_pct": "",
                    "robustness_status": "insufficient_data",
                    "robustness_reason": "Not enough crypto daily history for fixed split robustness checks.",
                    "research_only": True,
                    "preview_only": True,
                    "execution_approved": False,
                }
            )
    return rows


def write_crypto_robustness_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CRYPTO_ROBUSTNESS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CRYPTO_ROBUSTNESS_COLUMNS})


def build_crypto_robustness_summary(rows: list[dict[str, Any]]) -> list[str]:
    robust = sorted({
        f"{row['symbol']}:{row['strategy_name']}"
        for row in rows
        if row["robustness_status"] == "robust_candidate"
    })
    sensitive = sorted({
        f"{row['symbol']}:{row['strategy_name']}"
        for row in rows
        if row["robustness_status"] == "split_sensitive"
    })
    return [
        "CRYPTO ROBUSTNESS REPORT. RESEARCH ONLY. NOT EXECUTION.",
        best_strategy_line(rows, "BTC/USD", "Best BTC strategy across splits"),
        best_strategy_line(rows, "ETH/USD", "Best ETH strategy across splits"),
        "Robust candidates: " + (", ".join(robust) if robust else "none"),
        "Split-sensitive candidates: " + (", ".join(sensitive) if sensitive else "none"),
        negative_benchmark_note(rows),
        "Warning: crypto robustness report is not execution approval.",
    ]


def negative_benchmark_note(rows: list[dict[str, Any]]) -> str:
    matches = [
        row
        for row in rows
        if row.get("beats_buy_and_hold_oos") is True
        and number(row.get("out_of_sample_cagr_pct")) < 0
    ]
    if not matches:
        return "Negative absolute CAGR benchmark wins: none"
    labels = sorted({
        f"{row['symbol']}:{row['strategy_name']}:{row['split_name']}"
        for row in matches
    })
    return (
        "Some rows beat buy-and-hold only because buy-and-hold was worse in that split: "
        + ", ".join(labels)
    )


def best_strategy_line(rows: list[dict[str, Any]], symbol: str, label: str) -> str:
    candidates = [
        row for row in rows
        if row["symbol"] == symbol and isinstance(row.get("out_of_sample_calmar"), (int, float))
    ]
    if not candidates:
        return f"{label}: unavailable"
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in candidates:
        grouped.setdefault(row["strategy_name"], []).append(row)
    scores = []
    for strategy_name, group_rows in grouped.items():
        average_calmar = sum(number(row["out_of_sample_calmar"]) for row in group_rows) / len(group_rows)
        average_sharpe = sum(number(row["out_of_sample_sharpe"]) for row in group_rows) / len(group_rows)
        scores.append((strategy_name, average_calmar, average_sharpe))
    best = sorted(scores, key=lambda item: (-item[1], -item[2], item[0]))[0]
    return f"{label}: {best[0]} (average_oos_calmar={round(best[1], 4)})"


def split_sort_order(split_name: str) -> int:
    return {"split_60_40": 0, "split_70_30": 1, "split_80_20": 2}.get(split_name, 99)


def number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
