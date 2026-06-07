"""Research-only robustness report for the vol-managed ETF strategy."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from trading_bot.config import AppConfig
from trading_bot.market_data import configure_yfinance_cache, download_backtest_prices
from trading_bot.research.backtesting import calculate_cagr_pct, calculate_max_drawdown, calculate_sharpe_ratio
from trading_bot.research.costs import CostModel
from trading_bot.research.vol_managed_etf import (
    VOL_MANAGED_ETF_UNIVERSE,
    VOL_MANAGED_STRATEGY_NAME,
    align_price_rows,
    build_and_write_vol_managed_etf_outputs,
    parse_float,
)


VOL_MANAGED_ROBUSTNESS_COLUMNS = [
    "created_at",
    "strategy_name",
    "ticker_or_portfolio",
    "split_name",
    "in_sample_fraction",
    "out_of_sample_cagr_pct",
    "out_of_sample_sharpe",
    "out_of_sample_max_drawdown_pct",
    "out_of_sample_calmar",
    "out_of_sample_trade_count",
    "benchmark_strategy_name",
    "benchmark_oos_cagr_pct",
    "benchmark_oos_sharpe",
    "benchmark_oos_max_drawdown_pct",
    "benchmark_oos_calmar",
    "cagr_gap_vs_benchmark_oos",
    "sharpe_gap_vs_benchmark_oos",
    "calmar_gap_vs_benchmark_oos",
    "drawdown_reduction_vs_benchmark_oos",
    "comparison_splits_available",
    "comparison_splits_won",
    "comparison_splits_lost",
    "robustness_status",
    "robustness_reason",
    "research_only",
    "preview_only",
    "execution_approved",
]

FIXED_SPLITS = [
    ("split_60_40", Decimal("0.60")),
    ("split_70_30", Decimal("0.70")),
    ("split_80_20", Decimal("0.80")),
]


@dataclass
class VolManagedEtfRobustnessResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_managed_etf_robustness_report(
    config: AppConfig,
    logger,
    data_dir: Path | str = "data",
) -> VolManagedEtfRobustnessResult:
    configure_yfinance_cache(config, logger)
    price_by_ticker: dict[str, list[dict[str, Any]]] = {}
    for ticker in VOL_MANAGED_ETF_UNIVERSE:
        frame = download_backtest_prices(config, ticker)
        price_by_ticker[ticker] = [
            {"date": index.date().isoformat(), "close": float(row["close"])}
            for index, row in frame.iterrows()
            if float(row["close"]) > 0
        ]
    created_at = datetime.now(timezone.utc).isoformat()
    cost_model = CostModel(slippage_bps=Decimal(str(config.backtest.slippage_bps)))
    return build_and_write_vol_managed_etf_robustness_report(
        price_by_ticker=price_by_ticker,
        starting_cash=config.backtest.starting_cash,
        cost_model=cost_model,
        data_dir=Path(data_dir),
        created_at=created_at,
    )


def build_and_write_vol_managed_etf_robustness_report(
    price_by_ticker: dict[str, list[dict[str, Any]]],
    starting_cash: float,
    cost_model: CostModel,
    data_dir: Path,
    created_at: str,
) -> VolManagedEtfRobustnessResult:
    rows = build_vol_managed_etf_robustness_rows(price_by_ticker, starting_cash, cost_model, created_at)
    output_path = data_dir / "vol_managed_etf_robustness_report.csv"
    write_rows(output_path, rows)
    return VolManagedEtfRobustnessResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, output_path),
    )


def build_vol_managed_etf_robustness_rows(
    price_by_ticker: dict[str, list[dict[str, Any]]],
    starting_cash: float,
    cost_model: CostModel,
    created_at: str,
) -> list[dict[str, Any]]:
    aligned_rows = align_price_rows(price_by_ticker)
    if not aligned_rows:
        return [insufficient_row(created_at, split_name, fraction, "vol-managed price data unavailable") for split_name, fraction in FIXED_SPLITS]

    with_output = build_and_write_vol_managed_etf_outputs(
        price_by_ticker=price_by_ticker,
        starting_cash=starting_cash,
        cost_model=cost_model,
        data_dir=Path(".tmp_vol_managed_robustness_unused"),
        created_at=created_at,
    )
    strategy_equity = [float(row["equity"]) for row in with_output.equity_rows]
    dates = [str(row["date"]) for row in aligned_rows]
    rows: list[dict[str, Any]] = []
    for split_name, fraction in FIXED_SPLITS:
        split_index = fixed_split_index(strategy_equity, fraction)
        oos_curve = strategy_equity[split_index:]
        oos_trade_count = count_trades_for_oos(with_output.trade_rows, dates, split_index)
        benchmark = benchmark_for_split(split_name, fraction)
        rows.append(
            robustness_row(
                created_at,
                split_name,
                fraction,
                oos_curve,
                oos_trade_count,
                benchmark,
            )
        )
    apply_cross_split_status(rows)
    return rows


def robustness_row(
    created_at: str,
    split_name: str,
    fraction: Decimal,
    oos_curve: list[float],
    trade_count: int,
    benchmark: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = metrics_for_curve(oos_curve)
    benchmark_name = "monthly_etf_momentum_rotation" if benchmark else "monthly_etf_momentum_rotation_unavailable"
    benchmark_metrics = benchmark_metrics_from_row(benchmark)
    gaps = metric_gaps(metrics, benchmark_metrics)
    status, reason = row_status(metrics, benchmark_metrics)
    return {
        "created_at": created_at,
        "strategy_name": VOL_MANAGED_STRATEGY_NAME,
        "ticker_or_portfolio": "portfolio",
        "split_name": split_name,
        "in_sample_fraction": fraction,
        "out_of_sample_cagr_pct": metrics["cagr_pct"],
        "out_of_sample_sharpe": metrics["sharpe_ratio"],
        "out_of_sample_max_drawdown_pct": metrics["max_drawdown_pct"],
        "out_of_sample_calmar": metrics["calmar_ratio"],
        "out_of_sample_trade_count": trade_count,
        "benchmark_strategy_name": benchmark_name,
        "benchmark_oos_cagr_pct": benchmark_metrics.get("cagr_pct", ""),
        "benchmark_oos_sharpe": benchmark_metrics.get("sharpe_ratio", ""),
        "benchmark_oos_max_drawdown_pct": benchmark_metrics.get("max_drawdown_pct", ""),
        "benchmark_oos_calmar": benchmark_metrics.get("calmar_ratio", ""),
        "cagr_gap_vs_benchmark_oos": gaps.get("cagr_gap", ""),
        "sharpe_gap_vs_benchmark_oos": gaps.get("sharpe_gap", ""),
        "calmar_gap_vs_benchmark_oos": gaps.get("calmar_gap", ""),
        "drawdown_reduction_vs_benchmark_oos": gaps.get("drawdown_reduction", ""),
        "comparison_splits_available": "",
        "comparison_splits_won": "",
        "comparison_splits_lost": "",
        "robustness_status": status,
        "robustness_reason": reason,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def insufficient_row(created_at: str, split_name: str, fraction: Decimal, reason: str) -> dict[str, Any]:
    row = {column: "" for column in VOL_MANAGED_ROBUSTNESS_COLUMNS}
    row.update(
        {
            "created_at": created_at,
            "strategy_name": VOL_MANAGED_STRATEGY_NAME,
            "ticker_or_portfolio": "portfolio",
            "split_name": split_name,
            "in_sample_fraction": fraction,
            "benchmark_strategy_name": "monthly_etf_momentum_rotation_unavailable",
            "robustness_status": "insufficient_data",
            "robustness_reason": reason,
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
        }
    )
    return row


def apply_cross_split_status(rows: list[dict[str, Any]]) -> None:
    comparable = [row for row in rows if row["benchmark_strategy_name"] == "monthly_etf_momentum_rotation"]
    wins = [
        row
        for row in comparable
        if parse_float(row["sharpe_gap_vs_benchmark_oos"]) > 0 and parse_float(row["calmar_gap_vs_benchmark_oos"]) > 0
    ]
    losses = [
        row
        for row in comparable
        if not (parse_float(row["sharpe_gap_vs_benchmark_oos"]) > 0 and parse_float(row["calmar_gap_vs_benchmark_oos"]) > 0)
    ]
    available = len(comparable)
    won = len(wins)
    lost = len(losses)
    for row in rows:
        row["comparison_splits_available"] = available
        row["comparison_splits_won"] = won
        row["comparison_splits_lost"] = lost
    if len(comparable) == len(FIXED_SPLITS) and len(wins) == len(FIXED_SPLITS):
        for row in rows:
            row["robustness_status"] = "robust_candidate"
            row["robustness_reason"] = "Vol-managed ETF beats monthly ETF rotation on out-of-sample Sharpe and Calmar across all fixed splits."
    elif len(comparable) == len(FIXED_SPLITS) and wins:
        losing_splits = ", ".join(str(row["split_name"]) for row in losses)
        for row in rows:
            row["robustness_status"] = "promising_but_split_sensitive"
            row["robustness_reason"] = (
                f"Vol-managed ETF beats ETF rotation on {won} of {available} fixed splits, "
                f"but ETF rotation leads on {losing_splits}; keep research-only."
            )
    elif wins:
        for row in rows:
            if row["robustness_status"] != "insufficient_data":
                row["robustness_status"] = "promising_but_split_sensitive"
                row["robustness_reason"] = "Vol-managed ETF beats monthly ETF rotation on some comparable splits, but not all fixed splits are proven."


def fixed_split_index(curve: list[float], fraction: Decimal) -> int:
    if len(curve) < 3:
        return len(curve)
    return max(1, min(len(curve) - 1, int(len(curve) * float(fraction))))


def count_trades_for_oos(trades: list[dict[str, Any]], dates: list[str], split_index: int) -> int:
    if not dates or split_index >= len(dates):
        return 0
    start_date = dates[split_index]
    end_date = dates[-1]
    return sum(1 for row in trades if start_date <= str(row["date"]) <= end_date)


def metrics_for_curve(curve: list[float]) -> dict[str, float]:
    if not curve:
        return {"cagr_pct": 0.0, "sharpe_ratio": 0.0, "max_drawdown_pct": 0.0, "calmar_ratio": 0.0}
    cagr = calculate_cagr_pct(curve[0], curve[-1], len(curve))
    sharpe = calculate_sharpe_ratio(curve)
    max_drawdown = calculate_max_drawdown(curve) * 100
    calmar = cagr / abs(max_drawdown) if max_drawdown else 0.0
    return {
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_drawdown,
        "calmar_ratio": calmar,
    }


def benchmark_for_split(split_name: str, fraction: Decimal) -> dict[str, Any] | None:
    robustness_path = Path("data/etf_rotation_robustness_report.csv")
    if robustness_path.exists():
        with robustness_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                if row.get("strategy_name") == "monthly_etf_momentum_rotation" and row.get("split_name") == split_name:
                    return row
    if split_name != "split_70_30":
        return None
    path = Path("data/etf_rotation_results.csv")
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row.get("strategy_name") == "monthly_etf_momentum_rotation" and row.get("period") == "out_of_sample":
                return row
    return None


def benchmark_metrics_from_row(row: dict[str, Any] | None) -> dict[str, float]:
    if not row:
        return {}
    if "out_of_sample_cagr_pct" in row:
        return {
            "cagr_pct": parse_float(row.get("out_of_sample_cagr_pct")),
            "sharpe_ratio": parse_float(row.get("out_of_sample_sharpe")),
            "max_drawdown_pct": parse_float(row.get("out_of_sample_max_drawdown_pct")),
            "calmar_ratio": parse_float(row.get("out_of_sample_calmar")),
        }
    return {
        "cagr_pct": parse_float(row.get("cagr_pct")),
        "sharpe_ratio": parse_float(row.get("sharpe_ratio")),
        "max_drawdown_pct": parse_float(row.get("max_drawdown_pct")),
        "calmar_ratio": parse_float(row.get("calmar_ratio")),
    }


def metric_gaps(metrics: dict[str, float], benchmark: dict[str, float]) -> dict[str, float]:
    if not benchmark:
        return {}
    return {
        "cagr_gap": metrics["cagr_pct"] - benchmark["cagr_pct"],
        "sharpe_gap": metrics["sharpe_ratio"] - benchmark["sharpe_ratio"],
        "calmar_gap": metrics["calmar_ratio"] - benchmark["calmar_ratio"],
        "drawdown_reduction": benchmark["max_drawdown_pct"] - metrics["max_drawdown_pct"],
    }


def row_status(metrics: dict[str, float], benchmark: dict[str, float]) -> tuple[str, str]:
    if not benchmark:
        return (
            "insufficient_data",
            "Matching monthly ETF rotation benchmark is not available for this fixed split.",
        )
    beats_sharpe = metrics["sharpe_ratio"] > benchmark["sharpe_ratio"]
    beats_calmar = metrics["calmar_ratio"] > benchmark["calmar_ratio"]
    reduces_drawdown = metrics["max_drawdown_pct"] < benchmark["max_drawdown_pct"]
    if beats_sharpe and beats_calmar:
        return (
            "promising_but_split_sensitive",
            "This split beats monthly ETF rotation on out-of-sample Sharpe and Calmar; all fixed splits must confirm before robust_candidate.",
        )
    if reduces_drawdown:
        return (
            "defensive_candidate",
            "This split reduces drawdown versus monthly ETF rotation but does not beat both Sharpe and Calmar.",
        )
    return (
        "weak_candidate",
        "This split does not improve out-of-sample risk-adjusted metrics versus monthly ETF rotation.",
    )


def build_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    scored = [row for row in rows if row.get("out_of_sample_calmar") != ""]
    best = max(scored, key=lambda row: parse_float(row["out_of_sample_calmar"]), default=None)
    worst = min(scored, key=lambda row: parse_float(row["out_of_sample_calmar"]), default=None)
    beats_all = all(
        row.get("benchmark_strategy_name") == "monthly_etf_momentum_rotation"
        and parse_float(row.get("sharpe_gap_vs_benchmark_oos")) > 0
        and parse_float(row.get("calmar_gap_vs_benchmark_oos")) > 0
        for row in rows
    )
    statuses = sorted(set(str(row["robustness_status"]) for row in rows))
    lines = [
        "VOL-MANAGED ETF ROBUSTNESS REPORT. RESEARCH ONLY. NOT EXECUTION.",
        "Fixed splits: split_60_40, split_70_30, split_80_20.",
        "Best split result: " + (f"{best['split_name']} Calmar={float(best['out_of_sample_calmar']):.4f}" if best else "not_available"),
        "Worst split result: " + (f"{worst['split_name']} Calmar={float(worst['out_of_sample_calmar']):.4f}" if worst else "not_available"),
        f"Beats monthly ETF rotation across all fixed splits: {beats_all}",
        "Robustness status: " + ", ".join(statuses),
        "Warning: this is research only and not execution approval.",
        f"Saved vol-managed ETF robustness report to {output_path}",
    ]
    return lines


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=VOL_MANAGED_ROBUSTNESS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in VOL_MANAGED_ROBUSTNESS_COLUMNS})
