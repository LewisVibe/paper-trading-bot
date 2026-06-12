"""Research-only robustness reports for the ETF strategy improvement lab."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research.strategy_improvement_lab import (
    ALL_ETFS,
    STARTING_EQUITY,
    STRATEGY_NAMES,
    build_result_row,
    build_strategy_improvement_outputs,
    download_daily_price_data,
    find_result_row,
    write_rows,
)


ROBUSTNESS_OUTPUT_FILES = {
    "robustness": Path("data/strategy_improvement_robustness_report.csv"),
    "cost": Path("data/strategy_improvement_cost_stress_report.csv"),
    "drawdown": Path("data/strategy_improvement_drawdown_report.csv"),
    "comparison": Path("data/strategy_improvement_candidate_comparison.csv"),
}

FIXED_SPLITS = [
    ("split_60_40", 0.60),
    ("split_70_30", 0.70),
    ("split_80_20", 0.80),
]

FIXED_COSTS = [
    ("low_cost", 5.0),
    ("default_cost", 10.0),
    ("high_cost", 25.0),
]

BENCHMARK_NAME = "monthly_etf_momentum_rotation_reference"
SPY_BENCHMARK_NAME = "spy_buy_and_hold_benchmark"
GROWTH_BIASED_ORIGINAL = "growth_biased_rotation_crash_gate"
COST_AWARE_REFINEMENT = "growth_biased_rotation_cost_aware_rebalance"

COMMON_COLUMNS = [
    "created_at",
    "strategy_name",
    "period",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "trade_count",
    "turnover",
    "benchmark_strategy_name",
    "benchmark_cagr_pct",
    "benchmark_sharpe_ratio",
    "benchmark_max_drawdown_pct",
    "benchmark_calmar_ratio",
    "cagr_delta_vs_benchmark",
    "sharpe_delta_vs_benchmark",
    "max_drawdown_delta_vs_benchmark",
    "calmar_delta_vs_benchmark",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
]

ROBUSTNESS_COLUMNS = COMMON_COLUMNS + [
    "split_name",
    "split_fraction",
    "split_start_date",
    "split_end_date",
    "average_cash_weight_pct",
    "cash_drag_delta_vs_benchmark",
    "split_label",
    "notes",
]

COST_COLUMNS = COMMON_COLUMNS + [
    "cost_label",
    "one_way_cost_bps",
    "estimated_cost_return_drag_pct",
    "cost_adjusted_cagr_pct",
    "cost_adjusted_calmar_ratio",
    "cost_sensitive",
    "notes",
]

DRAWDOWN_COLUMNS = COMMON_COLUMNS + [
    "worst_drawdown_start",
    "worst_drawdown_end",
    "worst_drawdown_pct",
    "return_drawdown_tradeoff",
    "average_cash_weight_pct",
    "notes",
]

COMPARISON_COLUMNS = COMMON_COLUMNS + [
    "average_cash_weight_pct",
    "cash_drag_delta_vs_benchmark",
    "cagr_delta_vs_growth_biased",
    "sharpe_delta_vs_growth_biased",
    "max_drawdown_delta_vs_growth_biased",
    "calmar_delta_vs_growth_biased",
    "cash_delta_vs_growth_biased",
    "trade_count_delta_vs_growth_biased",
    "turnover_delta_vs_growth_biased",
    "cost_sensitivity_delta_vs_growth_biased",
    "split_sensitivity_delta_vs_growth_biased",
    "trails_spy_buy_and_hold",
    "beats_rotation_cagr",
    "beats_rotation_sharpe",
    "beats_rotation_calmar",
    "beats_rotation_drawdown",
    "best_metric_flags",
    "split_sensitive",
    "cost_sensitive",
    "comparison_label",
    "notes",
]


@dataclass
class StrategyImprovementRobustnessResult:
    robustness_path: Path
    cost_path: Path
    drawdown_path: Path
    comparison_path: Path
    robustness_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    comparison_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_strategy_improvement_robustness(
    data_dir: Path | str = "data",
) -> StrategyImprovementRobustnessResult:
    created_at = datetime.now(timezone.utc).isoformat()
    from trading_bot.market_data import configure_yfinance_cache_location

    configure_yfinance_cache_location(Path("data") / "yfinance_cache")
    price_data, data_errors = download_daily_price_data(ALL_ETFS)
    result_rows, trade_rows, equity_rows, summary_rows, _iteration_rows = build_strategy_improvement_outputs(
        created_at=created_at,
        price_data=price_data,
        data_errors=data_errors,
    )
    robustness_rows = build_robustness_rows(created_at, equity_rows, trade_rows)
    cost_rows = build_cost_rows(created_at, summary_rows)
    drawdown_rows = build_drawdown_rows(created_at, result_rows, equity_rows)
    comparison_rows = build_comparison_rows(created_at, summary_rows, robustness_rows, cost_rows)

    data_path = Path(data_dir)
    output_paths = {name: data_path / path.name for name, path in ROBUSTNESS_OUTPUT_FILES.items()}
    write_rows(output_paths["robustness"], ROBUSTNESS_COLUMNS, robustness_rows)
    write_rows(output_paths["cost"], COST_COLUMNS, cost_rows)
    write_rows(output_paths["drawdown"], DRAWDOWN_COLUMNS, drawdown_rows)
    write_rows(output_paths["comparison"], COMPARISON_COLUMNS, comparison_rows)
    return StrategyImprovementRobustnessResult(
        robustness_path=output_paths["robustness"],
        cost_path=output_paths["cost"],
        drawdown_path=output_paths["drawdown"],
        comparison_path=output_paths["comparison"],
        robustness_rows=robustness_rows,
        cost_rows=cost_rows,
        drawdown_rows=drawdown_rows,
        comparison_rows=comparison_rows,
        summary_lines=build_summary_lines(comparison_rows, data_errors, output_paths),
    )


def build_robustness_rows(
    created_at: str,
    equity_rows: list[dict[str, Any]],
    trade_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    equity_by_strategy = group_rows(equity_rows, "strategy_name")
    trade_by_strategy = group_rows(trade_rows, "strategy_name")
    for split_name, split_fraction in FIXED_SPLITS:
        split_rows = []
        for strategy_name in STRATEGY_NAMES:
            strategy_equity = equity_by_strategy.get(strategy_name, [])
            split_index = max(2, int(len(strategy_equity) * split_fraction))
            period_equity = strategy_equity[split_index - 1 :]
            result = build_result_row(
                created_at,
                strategy_name,
                "out_of_sample",
                period_equity,
                trade_by_strategy.get(strategy_name, []),
            )
            result.update(
                {
                    "split_name": split_name,
                    "split_fraction": split_fraction,
                    "split_start_date": period_equity[0]["date"] if period_equity else "",
                    "split_end_date": period_equity[-1]["date"] if period_equity else "",
                    "average_cash_weight_pct": average_float(period_equity, "cash_weight") * 100.0,
                    "split_label": "pending_benchmark_comparison",
                    "notes": "Fixed chronological split; research-only robustness row.",
                }
            )
            split_rows.append(result)
        apply_split_benchmark(split_rows)
        rows.extend(split_rows)
    return rows


def apply_split_benchmark(rows: list[dict[str, Any]]) -> None:
    benchmark = next((row for row in rows if row["strategy_name"] == BENCHMARK_NAME), None)
    if not benchmark:
        return
    benchmark_cash = float(benchmark.get("average_cash_weight_pct", 0) or 0)
    for row in rows:
        row["benchmark_strategy_name"] = BENCHMARK_NAME
        row["benchmark_cagr_pct"] = benchmark["cagr_pct"]
        row["benchmark_sharpe_ratio"] = benchmark["sharpe_ratio"]
        row["benchmark_max_drawdown_pct"] = benchmark["max_drawdown_pct"]
        row["benchmark_calmar_ratio"] = benchmark["calmar_ratio"]
        row["cagr_delta_vs_benchmark"] = round(float(row["cagr_pct"]) - float(benchmark["cagr_pct"]), 4)
        row["sharpe_delta_vs_benchmark"] = round(float(row["sharpe_ratio"]) - float(benchmark["sharpe_ratio"]), 4)
        row["max_drawdown_delta_vs_benchmark"] = round(
            float(row["max_drawdown_pct"]) - float(benchmark["max_drawdown_pct"]),
            4,
        )
        row["calmar_delta_vs_benchmark"] = round(float(row["calmar_ratio"]) - float(benchmark["calmar_ratio"]), 4)
        row["cash_drag_delta_vs_benchmark"] = round(float(row["average_cash_weight_pct"]) - benchmark_cash, 4)
        row["split_label"] = split_label(row)


def split_label(row: dict[str, Any]) -> str:
    if row["strategy_name"].endswith("_benchmark"):
        return "benchmark_reference"
    if float(row.get("cagr_delta_vs_benchmark", 0) or 0) > 0 and float(row.get("calmar_delta_vs_benchmark", 0) or 0) > 0:
        return "split_promising"
    if float(row.get("max_drawdown_delta_vs_benchmark", 0) or 0) > 5:
        return "split_defensive_return_check"
    return "split_watch"


def build_cost_rows(created_at: str, summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    full_rows = [row for row in summary_rows if row.get("period") == "full_period"]
    for source in full_rows:
        for cost_label, one_way_cost_bps in FIXED_COSTS:
            turnover = float(source.get("turnover", 0) or 0)
            cost_drag = turnover * one_way_cost_bps / 100.0
            adjusted_cagr = float(source.get("cagr_pct", 0) or 0) - cost_drag
            max_drawdown = float(source.get("max_drawdown_pct", 0) or 0)
            adjusted_calmar = adjusted_cagr / abs(max_drawdown) if max_drawdown < 0 else 0.0
            row = copy_common(source, created_at)
            row.update(
                {
                    "cost_label": cost_label,
                    "one_way_cost_bps": one_way_cost_bps,
                    "estimated_cost_return_drag_pct": round(cost_drag, 4),
                    "cost_adjusted_cagr_pct": round(adjusted_cagr, 4),
                    "cost_adjusted_calmar_ratio": round(adjusted_calmar, 4),
                    "cost_sensitive": adjusted_calmar < float(source.get("calmar_ratio", 0) or 0) * 0.75,
                    "notes": "Simple fixed one-way cost stress from turnover; not an optimisation.",
                }
            )
            rows.append(row)
    return rows


def build_drawdown_rows(
    created_at: str,
    result_rows: list[dict[str, Any]],
    equity_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    equity_by_strategy = group_rows(equity_rows, "strategy_name")
    for strategy_name in STRATEGY_NAMES:
        metrics = find_result_row(result_rows, strategy_name, "full_period") or {}
        drawdown = worst_drawdown_window(equity_by_strategy.get(strategy_name, []))
        row = copy_common(metrics, created_at)
        row.update(
            {
                "worst_drawdown_start": drawdown["start"],
                "worst_drawdown_end": drawdown["end"],
                "worst_drawdown_pct": drawdown["drawdown_pct"],
                "return_drawdown_tradeoff": drawdown_tradeoff_label(metrics),
                "average_cash_weight_pct": metrics.get("average_cash_weight_pct", ""),
                "notes": "Worst full-period drawdown window from generated research equity curve.",
            }
        )
        rows.append(row)
    return rows


def worst_drawdown_window(equity_rows: list[dict[str, Any]]) -> dict[str, Any]:
    peak_equity = None
    peak_date = ""
    worst = 0.0
    worst_start = ""
    worst_end = ""
    for row in equity_rows:
        equity = float(row.get("equity", 0) or 0)
        date = str(row.get("date", ""))
        if peak_equity is None or equity > peak_equity:
            peak_equity = equity
            peak_date = date
        if peak_equity and peak_equity > 0:
            drawdown = (equity / peak_equity - 1.0) * 100.0
            if drawdown < worst:
                worst = drawdown
                worst_start = peak_date
                worst_end = date
    return {"start": worst_start, "end": worst_end, "drawdown_pct": round(worst, 4)}


def drawdown_tradeoff_label(row: dict[str, Any]) -> str:
    cagr_delta = float(row.get("cagr_delta_vs_benchmark", 0) or 0)
    drawdown_delta = float(row.get("max_drawdown_delta_vs_benchmark", 0) or 0)
    if cagr_delta > 2 and drawdown_delta < -5:
        return "improved_return_with_drawdown_increase"
    if cagr_delta < 0 and drawdown_delta > 5:
        return "lower_drawdown_with_return_drag"
    if cagr_delta > 0 and drawdown_delta >= -5:
        return "improved_return_acceptable_drawdown"
    return "no_clear_improvement"


def build_comparison_rows(
    created_at: str,
    summary_rows: list[dict[str, Any]],
    robustness_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full_rows = [row for row in summary_rows if row.get("period") == "full_period"]
    active_rows = [row for row in full_rows if not row["strategy_name"].endswith("_benchmark")]
    best_cagr = max(active_rows, key=lambda row: float(row.get("cagr_pct", 0) or 0), default={}).get("strategy_name", "")
    best_sharpe = max(active_rows, key=lambda row: float(row.get("sharpe_ratio", 0) or 0), default={}).get("strategy_name", "")
    best_calmar = max(active_rows, key=lambda row: float(row.get("calmar_ratio", 0) or 0), default={}).get("strategy_name", "")
    best_drawdown = min(active_rows, key=lambda row: abs(float(row.get("max_drawdown_pct", 0) or 0)), default={}).get("strategy_name", "")
    lowest_cash = min(active_rows, key=lambda row: float(row.get("average_cash_weight_pct", 999) or 999), default={}).get("strategy_name", "")
    spy = next((row for row in full_rows if row["strategy_name"] == SPY_BENCHMARK_NAME), None)
    growth_biased = next((row for row in full_rows if row["strategy_name"] == GROWTH_BIASED_ORIGINAL), None)
    rows = []
    for source in full_rows:
        strategy_name = source["strategy_name"]
        split_sensitive = is_split_sensitive(strategy_name, robustness_rows)
        cost_sensitive = is_cost_sensitive(strategy_name, cost_rows)
        flags = metric_flags(strategy_name, best_cagr, best_sharpe, best_calmar, best_drawdown, lowest_cash)
        row = copy_common(source, created_at)
        row.update(
            {
                "average_cash_weight_pct": source.get("average_cash_weight_pct", ""),
                "cash_drag_delta_vs_benchmark": cash_drag_delta(source, full_rows),
                "cagr_delta_vs_growth_biased": metric_delta(source, growth_biased, "cagr_pct"),
                "sharpe_delta_vs_growth_biased": metric_delta(source, growth_biased, "sharpe_ratio"),
                "max_drawdown_delta_vs_growth_biased": metric_delta(source, growth_biased, "max_drawdown_pct"),
                "calmar_delta_vs_growth_biased": metric_delta(source, growth_biased, "calmar_ratio"),
                "cash_delta_vs_growth_biased": metric_delta(source, growth_biased, "average_cash_weight_pct"),
                "trade_count_delta_vs_growth_biased": metric_delta(source, growth_biased, "trade_count"),
                "turnover_delta_vs_growth_biased": metric_delta(source, growth_biased, "turnover"),
                "cost_sensitivity_delta_vs_growth_biased": "",
                "split_sensitivity_delta_vs_growth_biased": "",
                "trails_spy_buy_and_hold": trails_spy(source, spy),
                "beats_rotation_cagr": float(source.get("cagr_delta_vs_benchmark", 0) or 0) > 0,
                "beats_rotation_sharpe": float(source.get("sharpe_delta_vs_benchmark", 0) or 0) > 0,
                "beats_rotation_calmar": float(source.get("calmar_delta_vs_benchmark", 0) or 0) > 0,
                "beats_rotation_drawdown": float(source.get("max_drawdown_delta_vs_benchmark", 0) or 0) > 0,
                "best_metric_flags": ",".join(flags),
                "split_sensitive": split_sensitive,
                "cost_sensitive": cost_sensitive,
                "comparison_label": comparison_label(source, flags, split_sensitive, cost_sensitive),
                "notes": "Research-only candidate comparison; labels are not execution approval.",
            }
        )
        rows.append(row)
    apply_growth_biased_sensitivity_deltas(rows)
    return rows


def apply_growth_biased_sensitivity_deltas(rows: list[dict[str, Any]]) -> None:
    original = next((row for row in rows if row["strategy_name"] == GROWTH_BIASED_ORIGINAL), None)
    if not original:
        return
    for row in rows:
        row["cost_sensitivity_delta_vs_growth_biased"] = bool_delta(row.get("cost_sensitive"), original.get("cost_sensitive"))
        row["split_sensitivity_delta_vs_growth_biased"] = bool_delta(row.get("split_sensitive"), original.get("split_sensitive"))


def metric_delta(row: dict[str, Any], reference: dict[str, Any] | None, metric: str) -> float | str:
    if not reference:
        return ""
    return round(float(row.get(metric, 0) or 0) - float(reference.get(metric, 0) or 0), 4)


def bool_delta(value: Any, reference: Any) -> str:
    current_bool = parse_bool(value)
    reference_bool = parse_bool(reference)
    if current_bool == reference_bool:
        return "no_change"
    if reference_bool and not current_bool:
        return "improved"
    return "worse"


def comparison_label(row: dict[str, Any], flags: list[str], split_sensitive: bool, cost_sensitive: bool) -> str:
    if row["strategy_name"].endswith("_benchmark"):
        return "benchmark_reference"
    if not row or (
        float(row.get("trade_count", 0) or 0) == 0
        and float(row.get("cagr_pct", 0) or 0) == 0
        and float(row.get("calmar_ratio", 0) or 0) == 0
    ):
        return "insufficient_data"
    if split_sensitive:
        return "split_sensitive"
    if cost_sensitive:
        return "cost_sensitive"
    cagr_delta = float(row.get("cagr_delta_vs_benchmark", 0) or 0)
    sharpe_delta = float(row.get("sharpe_delta_vs_benchmark", 0) or 0)
    calmar_delta = float(row.get("calmar_delta_vs_benchmark", 0) or 0)
    drawdown_delta = float(row.get("max_drawdown_delta_vs_benchmark", 0) or 0)
    if {"best_cagr", "best_sharpe", "best_calmar"}.issubset(set(flags)):
        return "strongest_overall_research_candidate"
    if "best_calmar" in flags or "best_sharpe" in flags:
        return "strongest_risk_adjusted_candidate"
    if "best_cagr" in flags:
        return "strongest_growth_candidate"
    if row["strategy_name"] == "adaptive_multi_sleeve_growth_allocator" and cagr_delta > 0:
        return "ambitious_growth_candidate"
    if cagr_delta > 0 and drawdown_delta < -5:
        return "promising_but_drawdown_heavy"
    if cagr_delta < 0 and drawdown_delta > 0:
        return "defensive_but_return_drag"
    if cagr_delta > 0 and (sharpe_delta > 0 or calmar_delta > 0):
        return "ambitious_growth_candidate"
    return "not_useful"


def metric_flags(strategy_name: str, best_cagr: str, best_sharpe: str, best_calmar: str, best_drawdown: str, lowest_cash: str) -> list[str]:
    flags = []
    for flag, winner in [
        ("best_cagr", best_cagr),
        ("best_sharpe", best_sharpe),
        ("best_calmar", best_calmar),
        ("best_drawdown_control", best_drawdown),
        ("lowest_cash_drag", lowest_cash),
    ]:
        if strategy_name == winner:
            flags.append(flag)
    return flags


def is_split_sensitive(strategy_name: str, robustness_rows: list[dict[str, Any]]) -> bool:
    rows = [row for row in robustness_rows if row["strategy_name"] == strategy_name]
    if not rows or strategy_name.endswith("_benchmark"):
        return False
    if all(
        float(row.get("trade_count", 0) or 0) == 0
        and float(row.get("cagr_pct", 0) or 0) == 0
        and float(row.get("calmar_ratio", 0) or 0) == 0
        for row in rows
    ):
        return False
    promising = [
        row
        for row in rows
        if float(row.get("cagr_delta_vs_benchmark", 0) or 0) > 0 and float(row.get("calmar_delta_vs_benchmark", 0) or 0) > 0
    ]
    return len(promising) <= 1


def is_cost_sensitive(strategy_name: str, cost_rows: list[dict[str, Any]]) -> bool:
    rows = [row for row in cost_rows if row["strategy_name"] == strategy_name]
    return any(parse_bool(row.get("cost_sensitive")) for row in rows if row.get("cost_label") == "high_cost")


def cash_drag_delta(row: dict[str, Any], rows: list[dict[str, Any]]) -> float | str:
    benchmark = next((item for item in rows if item["strategy_name"] == BENCHMARK_NAME), None)
    if not benchmark:
        return ""
    return round(float(row.get("average_cash_weight_pct", 0) or 0) - float(benchmark.get("average_cash_weight_pct", 0) or 0), 4)


def trails_spy(row: dict[str, Any], spy: dict[str, Any] | None) -> bool:
    if not spy or row["strategy_name"] == SPY_BENCHMARK_NAME:
        return False
    return float(row.get("cagr_pct", 0) or 0) < float(spy.get("cagr_pct", 0) or 0)


def copy_common(row: dict[str, Any], created_at: str) -> dict[str, Any]:
    copied = {column: row.get(column, "") for column in COMMON_COLUMNS}
    copied["created_at"] = created_at
    copied["research_only"] = True
    copied["preview_only"] = True
    copied["execution_approved"] = False
    copied["paper_execution_approved"] = False
    return copied


def group_rows(rows: list[dict[str, Any]], column: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get(column, "")), []).append(row)
    return grouped


def average_float(rows: list[dict[str, Any]], column: str) -> float:
    if not rows:
        return 0.0
    values = [float(row.get(column, 0) or 0) for row in rows]
    return sum(values) / len(values)


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def build_summary_lines(
    comparison_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
    output_paths: dict[str, Path],
) -> list[str]:
    active = [row for row in comparison_rows if not row["strategy_name"].endswith("_benchmark")]
    best_overall = next((row for row in active if row.get("comparison_label") == "strongest_overall_research_candidate"), None)
    best_calmar = max(active, key=lambda row: float(row.get("calmar_ratio", 0) or 0), default=None)
    best_cagr = max(active, key=lambda row: float(row.get("cagr_pct", 0) or 0), default=None)
    lines = [
        "Strategy improvement robustness complete. Research/preview only; execution_approved=False.",
        f"Candidates compared: {len(active)} active strategies.",
        f"Tickers with data errors: {len(data_errors)}.",
    ]
    if best_overall:
        lines.append(f"Strongest overall research candidate: {best_overall['strategy_name']}.")
    if best_calmar:
        lines.append(
            f"Best active Calmar: {best_calmar['strategy_name']} "
            f"(CAGR {best_calmar['cagr_pct']}%, Sharpe {best_calmar['sharpe_ratio']}, Calmar {best_calmar['calmar_ratio']})."
        )
    if best_cagr:
        lines.append(f"Best active CAGR: {best_cagr['strategy_name']} at {best_cagr['cagr_pct']}%.")
    lines.extend(
        [
            f"Saved robustness report to {output_paths['robustness']}",
            f"Saved cost stress report to {output_paths['cost']}",
            f"Saved drawdown report to {output_paths['drawdown']}",
            f"Saved candidate comparison to {output_paths['comparison']}",
            "Warning: robustness labels are research labels only and do not approve orders, scheduling, or paper execution.",
        ]
    )
    return lines


def show_strategy_improvement_robustness_file(
    comparison_path: Path | str = ROBUSTNESS_OUTPUT_FILES["comparison"],
) -> tuple[int, list[str]]:
    path = Path(comparison_path)
    if not path.exists():
        return 1, ["Run `python bot.py --strategy-improvement-robustness` first."]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return 1, [f"No rows found in {path}. Run `python bot.py --strategy-improvement-robustness` first."]

    active = [row for row in rows if not row["strategy_name"].endswith("_benchmark")]
    lines = [
        "Strategy improvement robustness saved comparison. Display only; execution_approved=False.",
        f"Rows: {len(rows)}",
    ]
    for label, row in [
        ("Best active by Calmar", max(active, key=lambda item: float(item.get("calmar_ratio", 0) or 0), default=None)),
        ("Best active by Sharpe", max(active, key=lambda item: float(item.get("sharpe_ratio", 0) or 0), default=None)),
        ("Best active by CAGR", max(active, key=lambda item: float(item.get("cagr_pct", 0) or 0), default=None)),
        ("Best drawdown control", min(active, key=lambda item: abs(float(item.get("max_drawdown_pct", 0) or 0)), default=None)),
        ("Lowest cash drag", min(active, key=lambda item: float(item.get("average_cash_weight_pct", 999) or 999), default=None)),
    ]:
        if row:
            lines.append(format_display_line(label, row))
    strongest = next((row for row in active if row.get("comparison_label") == "strongest_overall_research_candidate"), None)
    if strongest:
        lines.append(format_display_line("Strongest overall research candidate", strongest))
    multi = next((row for row in rows if row["strategy_name"] == "adaptive_multi_sleeve_growth_allocator"), None)
    if multi:
        lines.append(format_display_line("Adaptive multi-sleeve allocator", multi))
    cost_aware = next((row for row in rows if row["strategy_name"] == COST_AWARE_REFINEMENT), None)
    if cost_aware:
        lines.append(format_growth_biased_comparison_line(cost_aware))
    warnings = [
        f"{row['strategy_name']}={row['comparison_label']}"
        for row in active
        if row.get("comparison_label") in {"split_sensitive", "cost_sensitive", "promising_but_drawdown_heavy"}
        or parse_bool(row.get("trails_spy_buy_and_hold"))
    ]
    if warnings:
        lines.append("Warnings: " + "; ".join(warnings))
    lines.append("Warning: this display reads saved CSV only and does not approve orders.")
    return 0, lines


def format_display_line(label: str, row: dict[str, Any]) -> str:
    return (
        f"{label}: {row['strategy_name']} | label={row.get('comparison_label')} | "
        f"CAGR={row.get('cagr_pct')}% | Sharpe={row.get('sharpe_ratio')} | "
        f"MaxDD={row.get('max_drawdown_pct')}% | Calmar={row.get('calmar_ratio')} | "
        f"Cash={row.get('average_cash_weight_pct')}%"
    )


def format_growth_biased_comparison_line(row: dict[str, Any]) -> str:
    return (
        "Cost-aware vs original growth-biased: "
        f"CAGR delta={row.get('cagr_delta_vs_growth_biased')}, "
        f"Sharpe delta={row.get('sharpe_delta_vs_growth_biased')}, "
        f"Calmar delta={row.get('calmar_delta_vs_growth_biased')}, "
        f"MaxDD delta={row.get('max_drawdown_delta_vs_growth_biased')}, "
        f"cash delta={row.get('cash_delta_vs_growth_biased')}, "
        f"trade delta={row.get('trade_count_delta_vs_growth_biased')}, "
        f"turnover delta={row.get('turnover_delta_vs_growth_biased')}, "
        f"cost sensitivity={row.get('cost_sensitivity_delta_vs_growth_biased')}, "
        f"split sensitivity={row.get('split_sensitivity_delta_vs_growth_biased')}."
    )
