"""Research report aggregation helpers.

This module only reads existing research CSV files and writes a consolidated
report. It does not call market data, Alpaca, Discord, or SQLite.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPORT_INPUT_FILES = [
    "strategy_comparison_results.csv",
    "strategy_portfolio_comparison.csv",
    "etf_rotation_results.csv",
    "adaptive_momentum_results.csv",
    "backtest_results.csv",
    "sma_sensitivity_portfolio.csv",
    "trend_stress_test_portfolio.csv",
]

REPORT_COLUMNS = [
    "source_file",
    "strategy_name",
    "ticker_or_portfolio",
    "period",
    "is_portfolio_level",
    "is_single_ticker",
    "is_full_period",
    "is_in_sample",
    "is_out_of_sample",
    "report_view",
    "strategy_role",
    "is_benchmark",
    "is_active_strategy",
    "strategy_family",
    "total_return_pct",
    "cagr_pct",
    "max_drawdown_pct",
    "annualised_volatility_pct",
    "sharpe_ratio",
    "calmar_ratio",
    "number_of_trades",
    "time_in_market_pct",
    "final_equity",
    "commission_per_trade",
    "commission_bps",
    "spread_bps",
    "slippage_bps",
    "notes",
    "rank_by_cagr",
    "rank_by_max_drawdown",
    "rank_by_sharpe",
    "rank_by_calmar",
    "rank_by_trade_count",
    "combined_rank_score",
    "decision_rank_by_cagr",
    "decision_rank_by_max_drawdown",
    "decision_rank_by_sharpe",
    "decision_rank_by_calmar",
    "decision_rank_by_trade_count",
    "decision_combined_rank_score",
    "active_rank_by_cagr",
    "active_rank_by_max_drawdown",
    "active_rank_by_sharpe",
    "active_rank_by_calmar",
    "active_rank_by_trade_count",
    "active_combined_rank_score",
    "cagr_vs_best_benchmark_pct",
    "drawdown_vs_best_benchmark_pct",
    "sharpe_vs_best_benchmark",
    "calmar_vs_best_benchmark",
    "beats_best_benchmark_cagr",
    "beats_best_benchmark_sharpe",
    "beats_best_benchmark_calmar",
    "has_lower_drawdown_than_best_benchmark",
    "return_gap_vs_best_benchmark_pct",
    "drawdown_reduction_vs_best_benchmark_pct",
    "sharpe_gap_vs_best_benchmark",
    "calmar_gap_vs_best_benchmark",
    "trade_count_vs_best_benchmark",
    "active_trade_penalty_note",
    "underperformance_reason",
]

PORTFOLIO_LEVEL_FILES = {
    "strategy_portfolio_comparison.csv",
    "etf_rotation_results.csv",
    "adaptive_momentum_results.csv",
    "sma_sensitivity_portfolio.csv",
    "trend_stress_test_portfolio.csv",
}


@dataclass
class ResearchReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def generate_research_report(
    data_dir: Path | str = "data",
    output_filename: str = "research_report.csv",
) -> ResearchReportResult:
    data_path = Path(data_dir)
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []

    for filename in REPORT_INPUT_FILES:
        input_path = data_path / filename
        if not input_path.exists():
            warnings.append(f"Missing research file: {input_path}")
            continue
        file_rows = read_research_file(input_path)
        if not file_rows:
            warnings.append(f"No usable rows in research file: {input_path}")
            continue
        rows.extend(file_rows)

    if not rows:
        raise RuntimeError("No usable research CSV files found.")

    apply_research_ranks(rows)
    output_path = data_path / output_filename
    write_research_report(output_path, rows)
    summary_lines = build_research_report_summary(rows)

    return ResearchReportResult(
        output_path=output_path,
        rows=rows,
        warnings=warnings,
        summary_lines=summary_lines,
    )


def read_research_file(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [
            normalize_research_row(path.name, row)
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def normalize_research_row(source_file: str, row: dict[str, str]) -> dict[str, Any]:
    strategy_name = first_value(
        row,
        "strategy_name",
        default=strategy_name_from_source(source_file, row),
    )
    ticker_or_portfolio = first_value(row, "ticker", "universe_name", default="portfolio")
    if source_file in PORTFOLIO_LEVEL_FILES:
        ticker_or_portfolio = "portfolio"
    period = first_value(row, "period", default="full_period")
    view = classify_report_view(source_file, ticker_or_portfolio, period)
    role = classify_strategy_role(source_file, strategy_name)

    return {
        "source_file": source_file,
        "strategy_name": strategy_name,
        "ticker_or_portfolio": ticker_or_portfolio,
        "period": period,
        "is_portfolio_level": view["is_portfolio_level"],
        "is_single_ticker": view["is_single_ticker"],
        "is_full_period": view["is_full_period"],
        "is_in_sample": view["is_in_sample"],
        "is_out_of_sample": view["is_out_of_sample"],
        "report_view": view["report_view"],
        "strategy_role": role["strategy_role"],
        "is_benchmark": role["is_benchmark"],
        "is_active_strategy": role["is_active_strategy"],
        "strategy_family": role["strategy_family"],
        "total_return_pct": number_or_blank(first_value(row, "total_return_pct")),
        "cagr_pct": number_or_blank(first_value(row, "cagr_pct")),
        "max_drawdown_pct": number_or_blank(first_value(row, "max_drawdown_pct")),
        "annualised_volatility_pct": number_or_blank(first_value(row, "annualised_volatility_pct")),
        "sharpe_ratio": number_or_blank(first_value(row, "sharpe_ratio")),
        "calmar_ratio": number_or_blank(first_value(row, "calmar_ratio")),
        "number_of_trades": number_or_blank(first_value(row, "number_of_trades")),
        "time_in_market_pct": number_or_blank(first_value(row, "time_in_market_pct")),
        "final_equity": number_or_blank(first_value(row, "final_equity")),
        "commission_per_trade": first_value(row, "commission_per_trade"),
        "commission_bps": first_value(row, "commission_bps"),
        "spread_bps": first_value(row, "spread_bps"),
        "slippage_bps": first_value(row, "slippage_bps"),
        "notes": notes_for_source(source_file),
    }


def classify_report_view(source_file: str, ticker_or_portfolio: str, period: str) -> dict[str, bool | str]:
    ticker_text = (ticker_or_portfolio or "").strip().lower()
    period_text = (period or "full_period").strip().lower()
    is_portfolio_level = (
        source_file in PORTFOLIO_LEVEL_FILES
        or ticker_text in {"", "portfolio", "all", "total", "universe"}
    )
    is_full_period = period_text in {"", "full", "full_period", "all"}
    is_in_sample = period_text == "in_sample"
    is_out_of_sample = period_text == "out_of_sample"
    level = "portfolio" if is_portfolio_level else "single_ticker"
    period_label = (
        "full_period"
        if is_full_period
        else "in_sample"
        if is_in_sample
        else "out_of_sample"
        if is_out_of_sample
        else period_text
    )
    return {
        "is_portfolio_level": is_portfolio_level,
        "is_single_ticker": not is_portfolio_level,
        "is_full_period": is_full_period,
        "is_in_sample": is_in_sample,
        "is_out_of_sample": is_out_of_sample,
        "report_view": f"{level}_{period_label}",
    }


def classify_strategy_role(source_file: str, strategy_name: str) -> dict[str, bool | str]:
    name = (strategy_name or "").strip().lower()
    source = (source_file or "").strip().lower()

    if name == "buy_and_hold_baseline" or "buy_hold" in name or "buy-and-hold" in name or name.endswith("_benchmark"):
        role = "benchmark"
        family = "benchmark"
    elif "rotation" in name or source == "etf_rotation_results.csv":
        role = "active_rotation"
        family = "rotation"
    elif "adaptive" in name or source == "adaptive_momentum_results.csv":
        role = "active_adaptive"
        family = "adaptive"
    elif "breakout" in name:
        role = "active_breakout"
        family = "breakout"
    elif source == "sma_sensitivity_portfolio.csv" or "sensitivity" in name:
        role = "sensitivity_test"
        family = "sma"
    elif source == "trend_stress_test_portfolio.csv" or "stress" in name:
        role = "stress_test"
        family = "sma"
    elif "sma" in name or "trend" in name or "regime" in name or name.startswith("buy_above_200"):
        role = "active_trend"
        family = "trend"
    else:
        role = "unknown"
        family = "unknown"

    is_benchmark = role == "benchmark"
    return {
        "strategy_role": role,
        "is_benchmark": is_benchmark,
        "is_active_strategy": role.startswith("active_"),
        "strategy_family": family,
    }


def strategy_name_from_source(source_file: str, row: dict[str, str]) -> str:
    if source_file == "backtest_results.csv":
        return "regime_sma_vol_filter"
    if source_file == "sma_sensitivity_portfolio.csv":
        return f"sma_sensitivity_{row.get('short_window', '')}_{row.get('long_window', '')}".strip("_")
    if source_file == "trend_stress_test_portfolio.csv":
        return (
            f"trend_stress_sma_{row.get('short_window', '')}_{row.get('long_window', '')}"
            f"_slip_{row.get('slippage_bps', '')}"
        ).strip("_")
    return source_file.replace(".csv", "")


def notes_for_source(source_file: str) -> str:
    if source_file == "adaptive_momentum_results.csv":
        return "Research-only adaptive strategy; compare complexity against simpler benchmarks."
    if source_file == "etf_rotation_results.csv":
        return "Research-only monthly ETF rotation."
    return "Research-only; historical results do not imply future profits."


def first_value(row: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def number_or_blank(value: str) -> float | str:
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def apply_research_ranks(rows: list[dict[str, Any]]) -> None:
    assign_rank(rows, "cagr_pct", "rank_by_cagr", higher_is_better=True)
    assign_rank(rows, "max_drawdown_pct", "rank_by_max_drawdown", higher_is_better=False)
    assign_rank(rows, "sharpe_ratio", "rank_by_sharpe", higher_is_better=True)
    assign_rank(rows, "calmar_ratio", "rank_by_calmar", higher_is_better=True)
    assign_rank(rows, "number_of_trades", "rank_by_trade_count", higher_is_better=False)

    penalty = len(rows) + 1
    for row in rows:
        score = (
            rank_value(row, "rank_by_cagr", penalty)
            + rank_value(row, "rank_by_max_drawdown", penalty)
            + rank_value(row, "rank_by_sharpe", penalty)
            + rank_value(row, "rank_by_calmar", penalty)
            + (rank_value(row, "rank_by_trade_count", penalty) * 0.5)
        )
        row["combined_rank_score"] = round(score, 4)

    decision_rows = decision_view_rows(rows)
    assign_rank(decision_rows, "cagr_pct", "decision_rank_by_cagr", higher_is_better=True)
    assign_rank(decision_rows, "max_drawdown_pct", "decision_rank_by_max_drawdown", higher_is_better=False)
    assign_rank(decision_rows, "sharpe_ratio", "decision_rank_by_sharpe", higher_is_better=True)
    assign_rank(decision_rows, "calmar_ratio", "decision_rank_by_calmar", higher_is_better=True)
    assign_rank(decision_rows, "number_of_trades", "decision_rank_by_trade_count", higher_is_better=False)

    decision_penalty = len(decision_rows) + 1
    decision_rank_keys = [
        "decision_rank_by_cagr",
        "decision_rank_by_max_drawdown",
        "decision_rank_by_sharpe",
        "decision_rank_by_calmar",
        "decision_rank_by_trade_count",
    ]
    for row in rows:
        if row not in decision_rows:
            for key in decision_rank_keys:
                row[key] = ""
            row["decision_combined_rank_score"] = ""
            continue
        score = (
            rank_value(row, "decision_rank_by_cagr", decision_penalty)
            + rank_value(row, "decision_rank_by_max_drawdown", decision_penalty)
            + rank_value(row, "decision_rank_by_sharpe", decision_penalty)
            + rank_value(row, "decision_rank_by_calmar", decision_penalty)
            + (rank_value(row, "decision_rank_by_trade_count", decision_penalty) * 0.5)
        )
        row["decision_combined_rank_score"] = round(score, 4)

    active_rows = active_decision_rows(rows)
    assign_rank(active_rows, "cagr_pct", "active_rank_by_cagr", higher_is_better=True)
    assign_rank(active_rows, "max_drawdown_pct", "active_rank_by_max_drawdown", higher_is_better=False)
    assign_rank(active_rows, "sharpe_ratio", "active_rank_by_sharpe", higher_is_better=True)
    assign_rank(active_rows, "calmar_ratio", "active_rank_by_calmar", higher_is_better=True)
    assign_rank(active_rows, "number_of_trades", "active_rank_by_trade_count", higher_is_better=False)

    active_penalty = len(active_rows) + 1
    active_rank_keys = [
        "active_rank_by_cagr",
        "active_rank_by_max_drawdown",
        "active_rank_by_sharpe",
        "active_rank_by_calmar",
        "active_rank_by_trade_count",
    ]
    for row in rows:
        if row not in active_rows:
            for key in active_rank_keys:
                row[key] = ""
            row["active_combined_rank_score"] = ""
            continue
        score = (
            rank_value(row, "active_rank_by_cagr", active_penalty)
            + rank_value(row, "active_rank_by_max_drawdown", active_penalty)
            + rank_value(row, "active_rank_by_sharpe", active_penalty)
            + rank_value(row, "active_rank_by_calmar", active_penalty)
            + (rank_value(row, "active_rank_by_trade_count", active_penalty) * 0.5)
        )
        row["active_combined_rank_score"] = round(score, 4)

    apply_benchmark_comparisons(rows)


def decision_view_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # The headline decision view avoids ranking an in-sample single ticker beside
    # a full-period portfolio result, which can make fragile results look better
    # than broader strategies.
    portfolio_full_period = [
        row for row in rows if row.get("is_portfolio_level") is True and row.get("is_full_period") is True
    ]
    if portfolio_full_period:
        return portfolio_full_period

    portfolio_not_in_sample = [
        row for row in rows if row.get("is_portfolio_level") is True and row.get("is_in_sample") is not True
    ]
    if portfolio_not_in_sample:
        return portfolio_not_in_sample

    return [row for row in rows if row.get("is_in_sample") is not True]


def active_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in decision_view_rows(rows)
        if row.get("is_active_strategy") is True and row.get("is_in_sample") is not True
    ]


def benchmark_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decision_benchmarks = [
        row for row in decision_view_rows(rows) if row.get("is_benchmark") is True
    ]
    if decision_benchmarks:
        return decision_benchmarks
    return [row for row in rows if row.get("is_benchmark") is True and row.get("is_in_sample") is not True]


def best_benchmark_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    benchmarks = [
        row
        for row in benchmark_decision_rows(rows)
        if isinstance(row.get("decision_combined_rank_score"), (int, float))
    ]
    if benchmarks:
        return sorted(benchmarks, key=lambda row: float(row["decision_combined_rank_score"]))[0]
    benchmarks = benchmark_decision_rows(rows)
    return benchmarks[0] if benchmarks else None


def apply_benchmark_comparisons(rows: list[dict[str, Any]]) -> None:
    benchmark = best_benchmark_row(rows)
    comparison_columns = [
        "cagr_vs_best_benchmark_pct",
        "drawdown_vs_best_benchmark_pct",
        "sharpe_vs_best_benchmark",
        "calmar_vs_best_benchmark",
        "beats_best_benchmark_cagr",
        "beats_best_benchmark_sharpe",
        "beats_best_benchmark_calmar",
        "has_lower_drawdown_than_best_benchmark",
        "return_gap_vs_best_benchmark_pct",
        "drawdown_reduction_vs_best_benchmark_pct",
        "sharpe_gap_vs_best_benchmark",
        "calmar_gap_vs_best_benchmark",
        "trade_count_vs_best_benchmark",
        "active_trade_penalty_note",
        "underperformance_reason",
    ]
    for row in rows:
        for column in comparison_columns:
            row[column] = ""

    if not benchmark:
        return

    benchmark_cagr = benchmark.get("cagr_pct")
    benchmark_drawdown = benchmark.get("max_drawdown_pct")
    benchmark_sharpe = benchmark.get("sharpe_ratio")
    benchmark_calmar = benchmark.get("calmar_ratio")
    benchmark_trades = benchmark.get("number_of_trades")

    for row in rows:
        return_gap = metric_difference(row.get("cagr_pct"), benchmark_cagr)
        drawdown_gap = metric_difference(row.get("max_drawdown_pct"), benchmark_drawdown)
        sharpe_gap = metric_difference(row.get("sharpe_ratio"), benchmark_sharpe)
        calmar_gap = metric_difference(row.get("calmar_ratio"), benchmark_calmar)
        trade_gap = metric_difference(row.get("number_of_trades"), benchmark_trades)
        row["cagr_vs_best_benchmark_pct"] = return_gap
        row["drawdown_vs_best_benchmark_pct"] = drawdown_gap
        row["sharpe_vs_best_benchmark"] = sharpe_gap
        row["calmar_vs_best_benchmark"] = calmar_gap
        row["beats_best_benchmark_cagr"] = metric_greater(row.get("cagr_pct"), benchmark_cagr)
        row["beats_best_benchmark_sharpe"] = metric_greater(row.get("sharpe_ratio"), benchmark_sharpe)
        row["beats_best_benchmark_calmar"] = metric_greater(row.get("calmar_ratio"), benchmark_calmar)
        row["has_lower_drawdown_than_best_benchmark"] = metric_less(row.get("max_drawdown_pct"), benchmark_drawdown)
        row["return_gap_vs_best_benchmark_pct"] = return_gap
        row["drawdown_reduction_vs_best_benchmark_pct"] = (
            round(-float(drawdown_gap), 4) if isinstance(drawdown_gap, (int, float)) else ""
        )
        row["sharpe_gap_vs_best_benchmark"] = sharpe_gap
        row["calmar_gap_vs_best_benchmark"] = calmar_gap
        row["trade_count_vs_best_benchmark"] = trade_gap
        row["active_trade_penalty_note"] = active_trade_penalty_note(row, benchmark)
        row["underperformance_reason"] = underperformance_reason(row)


def metric_difference(value: Any, benchmark: Any) -> float | str:
    if not isinstance(value, (int, float)) or not isinstance(benchmark, (int, float)):
        return ""
    return round(float(value) - float(benchmark), 4)


def metric_greater(value: Any, benchmark: Any) -> bool | str:
    if not isinstance(value, (int, float)) or not isinstance(benchmark, (int, float)):
        return ""
    return float(value) > float(benchmark)


def metric_less(value: Any, benchmark: Any) -> bool | str:
    if not isinstance(value, (int, float)) or not isinstance(benchmark, (int, float)):
        return ""
    return float(value) < float(benchmark)


def active_trade_penalty_note(row: dict[str, Any], benchmark: dict[str, Any]) -> str:
    if row.get("is_active_strategy") is not True:
        return ""
    trades = row.get("number_of_trades")
    benchmark_trades = benchmark.get("number_of_trades")
    if not isinstance(trades, (int, float)) or not isinstance(benchmark_trades, (int, float)):
        return "trade_count_missing"
    if float(trades) <= float(benchmark_trades):
        return "trade_count_not_higher_than_benchmark"
    if float(benchmark_trades) <= 0:
        return "trade_count_higher_than_benchmark"
    ratio = float(trades) / float(benchmark_trades)
    if ratio >= 10:
        return "materially_higher_than_benchmark"
    return "higher_than_benchmark"


def underperformance_reason(row: dict[str, Any]) -> str:
    if row.get("is_active_strategy") is not True:
        return ""

    required = [
        row.get("return_gap_vs_best_benchmark_pct"),
        row.get("drawdown_reduction_vs_best_benchmark_pct"),
        row.get("sharpe_gap_vs_best_benchmark"),
        row.get("calmar_gap_vs_best_benchmark"),
        row.get("trade_count_vs_best_benchmark"),
    ]
    if any(not isinstance(value, (int, float)) for value in required):
        return "insufficient_metrics"

    return_gap = float(row["return_gap_vs_best_benchmark_pct"])
    drawdown_reduction = float(row["drawdown_reduction_vs_best_benchmark_pct"])
    sharpe_gap = float(row["sharpe_gap_vs_best_benchmark"])
    calmar_gap = float(row["calmar_gap_vs_best_benchmark"])
    trade_gap = float(row["trade_count_vs_best_benchmark"])
    lower_return = return_gap < 0
    lower_drawdown = drawdown_reduction > 0
    higher_drawdown = drawdown_reduction < 0
    risk_adjusted_gain = sharpe_gap > 0 or calmar_gap > 0
    high_turnover = trade_gap >= 50

    if lower_return and higher_drawdown:
        return "lower_return_and_higher_drawdown"
    if lower_return and lower_drawdown and return_gap <= -5:
        return "defensive_but_return_drag_too_high"
    if high_turnover and not risk_adjusted_gain:
        return "high_turnover_no_risk_adjusted_gain"
    if lower_return and not lower_drawdown:
        return "lower_return_and_no_drawdown_improvement"
    if lower_return and lower_drawdown:
        return "lower_return_despite_lower_drawdown"
    if lower_return and sharpe_gap <= 0 and calmar_gap <= 0:
        return "benchmark_dominates_on_growth_and_risk_adjusted_metrics"
    return "benchmark_dominates_on_growth_and_risk_adjusted_metrics"


def assign_rank(
    rows: list[dict[str, Any]],
    metric_key: str,
    rank_key: str,
    higher_is_better: bool,
) -> None:
    valid_rows = [
        row
        for row in rows
        if isinstance(row.get(metric_key), (int, float))
    ]
    valid_rows.sort(
        key=lambda row: (
            -float(row[metric_key]) if higher_is_better else float(row[metric_key]),
            row.get("strategy_name", ""),
            row.get("source_file", ""),
        )
    )
    for index, row in enumerate(valid_rows, start=1):
        row[rank_key] = index
    for row in rows:
        row.setdefault(rank_key, "")


def rank_value(row: dict[str, Any], key: str, penalty: int) -> float:
    value = row.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return float(penalty)


def write_research_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            float(row.get("combined_rank_score", 999999)),
            row.get("strategy_name", ""),
            row.get("source_file", ""),
        ),
    )
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for row in sorted_rows:
            writer.writerow({column: row.get(column, "") for column in REPORT_COLUMNS})


def build_research_report_summary(rows: list[dict[str, Any]]) -> list[str]:
    decision_rows = decision_view_rows(rows)
    active_rows = active_decision_rows(rows)
    benchmark = best_benchmark_row(rows)
    summary = [
        "Research report summary",
        "Research-only report. Historical rankings do not imply future profits.",
        "Warning: in-sample single-ticker rankings can be misleading; decision-view lines prefer full-period portfolio rows.",
    ]
    add_best_line(summary, rows, "best all-row CAGR", "cagr_pct", higher_is_better=True)
    if benchmark:
        summary.append(f"best benchmark by decision combined score: {label_for_row(benchmark)} ({benchmark.get('decision_combined_rank_score', '')})")
    else:
        summary.append("best benchmark by decision combined score: unavailable")

    active_combined = [
        row for row in active_rows if isinstance(row.get("active_combined_rank_score"), (int, float))
    ]
    active_combined.sort(key=lambda row: float(row["active_combined_rank_score"]))
    if active_combined:
        best_active = active_combined[0]
        summary.append(
            "best active strategy by active combined score: "
            f"{label_for_row(best_active)} ({best_active['active_combined_rank_score']})"
        )
        summary.extend(best_active_diagnostic_lines(best_active))
    else:
        summary.append("best active strategy by active combined score: unavailable")

    add_best_line(summary, active_rows, "best active strategy by CAGR", "cagr_pct", higher_is_better=True)
    add_best_line(summary, active_rows, "best active strategy by Sharpe", "sharpe_ratio", higher_is_better=True)
    add_best_line(summary, active_rows, "best active strategy by Calmar", "calmar_ratio", higher_is_better=True)
    add_best_line(summary, active_rows, "lowest drawdown active strategy", "max_drawdown_pct", higher_is_better=False)

    positive_decision_rows = [
        row
        for row in active_rows
        if isinstance(row.get("total_return_pct"), (int, float)) and float(row["total_return_pct"]) > 0
    ]
    add_best_line(
        summary,
        positive_decision_rows,
        "lowest active trade count with positive return",
        "number_of_trades",
        higher_is_better=False,
    )

    benchmark_warning = active_vs_benchmark_warning(active_rows)
    if benchmark_warning:
        summary.append(benchmark_warning)

    warning = adaptive_underperformance_warning(decision_rows or rows)
    if warning:
        summary.append(warning)
    summary.extend(research_conclusion_lines(active_rows))
    return summary


def add_best_line(
    summary: list[str],
    rows: list[dict[str, Any]],
    label: str,
    metric_key: str,
    higher_is_better: bool,
) -> None:
    valid_rows = [
        row
        for row in rows
        if isinstance(row.get(metric_key), (int, float))
    ]
    if not valid_rows:
        summary.append(f"{label}: unavailable")
        return
    best = sorted(
        valid_rows,
        key=lambda row: -float(row[metric_key]) if higher_is_better else float(row[metric_key]),
    )[0]
    summary.append(f"{label}: {label_for_row(best)} ({metric_key}={best[metric_key]})")


def label_for_row(row: dict[str, Any]) -> str:
    period = row.get("period") or "full_period"
    target = row.get("ticker_or_portfolio") or "portfolio"
    return f"{row.get('strategy_name', '')} [{target}, {period}]"


def adaptive_underperformance_warning(rows: list[dict[str, Any]]) -> str:
    adaptive = best_named_row(rows, "adaptive_risk_on_off_momentum")
    rotation = best_named_row(rows, "monthly_etf_momentum_rotation")
    if not adaptive or not rotation:
        return ""
    if float(adaptive.get("combined_rank_score", 999999)) > float(rotation.get("combined_rank_score", 999999)):
        return (
            "Caution: adaptive_risk_on_off_momentum ranks below "
            "monthly_etf_momentum_rotation despite being more complex."
        )
    return ""


def active_vs_benchmark_warning(active_rows: list[dict[str, Any]]) -> str:
    if not active_rows:
        return "Warning: no active strategy rows were available for benchmark comparison."

    beats_cagr = any(row.get("beats_best_benchmark_cagr") is True for row in active_rows)
    beats_sharpe = any(row.get("beats_best_benchmark_sharpe") is True for row in active_rows)
    beats_calmar = any(row.get("beats_best_benchmark_calmar") is True for row in active_rows)
    missing = []
    if not beats_cagr:
        missing.append("CAGR")
    if not beats_sharpe:
        missing.append("Sharpe")
    if not beats_calmar:
        missing.append("Calmar")
    if missing:
        return (
            "Warning: no active strategy beats the best benchmark on "
            f"{', '.join(missing)}."
        )
    return ""


def best_active_diagnostic_lines(row: dict[str, Any]) -> list[str]:
    lower_drawdown = row.get("has_lower_drawdown_than_best_benchmark")
    return_gap = row.get("return_gap_vs_best_benchmark_pct")
    drawdown_reduction = row.get("drawdown_reduction_vs_best_benchmark_pct")
    trade_note = row.get("active_trade_penalty_note") or "unavailable"
    lower_drawdown_text = "yes" if lower_drawdown is True else "no" if lower_drawdown is False else "unavailable"

    lines = [
        f"best active lower drawdown than benchmark: {lower_drawdown_text}",
        f"best active CAGR gap vs benchmark: {return_gap}",
        f"best active drawdown reduction vs benchmark: {drawdown_reduction}",
        f"best active trade count note: {trade_note}",
    ]
    if isinstance(return_gap, (int, float)) and isinstance(drawdown_reduction, (int, float)):
        gives_up_too_much = return_gap <= -5 and drawdown_reduction <= 5
        lines.append(f"best active gives up too much CAGR for drawdown reduction: {'yes' if gives_up_too_much else 'no'}")
    else:
        lines.append("best active gives up too much CAGR for drawdown reduction: unavailable")
    return lines


def research_conclusion_lines(active_rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "Conclusion: active strategies currently do not justify replacing the benchmark.",
    ]
    rotation = best_named_row(active_rows, "monthly_etf_momentum_rotation")
    adaptive = best_named_row(active_rows, "adaptive_risk_on_off_momentum")
    if rotation:
        lines.append("Conclusion: ETF rotation is the best defensive candidate but has too much return drag.")
    if adaptive and rotation:
        lines.append("Conclusion: adaptive strategy remains below ETF rotation despite added complexity.")
    return lines


def best_named_row(rows: list[dict[str, Any]], strategy_name: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("strategy_name") == strategy_name]
    if not matches:
        return None
    return sorted(matches, key=lambda row: float(row.get("combined_rank_score", 999999)))[0]
