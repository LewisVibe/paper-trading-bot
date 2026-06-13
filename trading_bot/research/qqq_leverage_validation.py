"""Research-only QQQ synthetic leverage validation report.

This validates fixed QQQ trend-gated synthetic leverage variants. It does not
call Alpaca, read config or positions, create orders, write SQLite, send
alerts, schedule anything, or approve leverage, margin, or execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location
from trading_bot.research.short_leverage_research_lab import (
    average,
    drawdown_window,
    max_drawdown_pct,
    metrics_for_curve,
    parse_float,
    sample_stdev,
    value_from_row,
)


OUTPUT_FILES = {
    "report": Path("data/qqq_leverage_validation_report.csv"),
    "summary": Path("data/qqq_leverage_validation_summary.csv"),
    "costs": Path("data/qqq_leverage_validation_costs.csv"),
    "splits": Path("data/qqq_leverage_validation_splits.csv"),
    "drawdowns": Path("data/qqq_leverage_validation_drawdowns.csv"),
}

HISTORY_PERIOD = "10y"
DAILY_INTERVAL = "1d"
STARTING_EQUITY = 10000.0
TREND_WINDOW = 200
TRANSACTION_COST_BPS = [0, 10, 25, 50]
FINANCING_BPS = [0, 300, 600]
VARIANTS = [
    ("qqq_100_trend_gate", 1.00),
    ("qqq_125_trend_gate", 1.25),
    ("qqq_150_trend_gate", 1.50),
    ("qqq_175_trend_gate", 1.75),
    ("qqq_200_trend_gate", 2.00),
]

COMMON_COLUMNS = [
    "created_at",
    "variant_name",
    "period",
    "data_status",
    "leverage_multiple",
    "cagr_pct",
    "annualised_volatility_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "total_return_pct",
    "exposure_change_count",
    "turnover",
    "time_invested_pct",
    "cash_time_pct",
    "benchmark_name",
    "benchmark_cagr_pct",
    "benchmark_sharpe_ratio",
    "benchmark_max_drawdown_pct",
    "benchmark_calmar_ratio",
    "decision_label",
    "notes",
    "research_only",
    "preview_only",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

REPORT_COLUMNS = COMMON_COLUMNS

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

COST_COLUMNS = COMMON_COLUMNS + [
    "cost_bps",
    "financing_bps_annual",
    "cost_stress_cagr_pct",
    "cost_stress_calmar_ratio",
    "cost_sensitivity_label",
]

SPLIT_COLUMNS = COMMON_COLUMNS + [
    "split_name",
    "split_fraction",
    "split_start_date",
    "split_end_date",
    "split_sensitivity_label",
]

DRAWDOWN_COLUMNS = COMMON_COLUMNS + [
    "drawdown_start",
    "drawdown_trough",
    "drawdown_recovery",
    "drawdown_recovered",
    "drawdown_days",
]


@dataclass
class QqqLeverageValidationResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq_leverage_validation_report(root_dir: Path | str = ".") -> QqqLeverageValidationResult:
    root = Path(root_dir)
    configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    price_data, data_errors = download_daily_price_data(["QQQ", "SPY"])
    variants = build_validation_variants(created_at, price_data, data_errors)
    report_rows = [build_report_row(created_at, variant, "full_period") for variant in variants]
    cost_rows = build_cost_rows(created_at, variants)
    split_rows = build_split_rows(created_at, variants)
    drawdown_rows = build_drawdown_rows(created_at, variants)
    summary_rows = build_summary_rows(created_at, report_rows, cost_rows, split_rows)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["costs"], COST_COLUMNS, cost_rows)
    write_rows(output_paths["splits"], SPLIT_COLUMNS, split_rows)
    write_rows(output_paths["drawdowns"], DRAWDOWN_COLUMNS, drawdown_rows)
    return QqqLeverageValidationResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        drawdown_rows=drawdown_rows,
        summary_lines=build_summary_lines(output_paths, report_rows, cost_rows, split_rows, data_errors),
    )


def show_qqq_leverage_validation_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    report_path = root / OUTPUT_FILES["report"]
    if not summary_path.exists() or not report_path.exists():
        return 1, ["Run `python bot.py --qqq-leverage-validation-report` first."]
    summary_rows = read_csv_rows(summary_path)
    report_rows = read_csv_rows(report_path)
    lines = ["QQQ LEVERAGE VALIDATION SAVED DISPLAY. RESEARCH ONLY. NOT EXECUTION."]
    for row in summary_rows:
        lines.append(f"{row.get('summary_name')}: {row.get('summary_value')} - {row.get('details')}")
    best = best_candidate(report_rows)
    if best:
        lines.append(f"Best saved candidate: {best['variant_name']} Calmar={best['calmar_ratio']} Sharpe={best['sharpe_ratio']}")
    lines.append("execution_approved=false; leverage_execution_approved=false; margin_approved=false; scheduling_approved=false")
    lines.append("Warning: saved display only; no Alpaca calls, order instructions, margin approval, leverage approval, or scheduling approval.")
    return 0, lines


def download_daily_price_data(tickers: list[str]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    import yfinance as yf

    price_data: dict[str, list[dict[str, Any]]] = {}
    data_errors: dict[str, str] = {}
    for ticker in tickers:
        try:
            frame = yf.download(ticker, period=HISTORY_PERIOD, interval=DAILY_INTERVAL, auto_adjust=True, progress=False, threads=False)
            if frame is None or frame.empty:
                data_errors[ticker] = "No daily market data returned by yfinance."
                continue
            rows = []
            for index, row in frame.iterrows():
                close = value_from_row(row, "Close")
                if close is not None and close > 0:
                    rows.append({"date": index.date().isoformat(), "close": float(close)})
            if len(rows) < TREND_WINDOW + 2:
                data_errors[ticker] = f"Not enough daily history; got {len(rows)} usable rows."
                continue
            price_data[ticker] = rows
        except Exception as exc:
            data_errors[ticker] = str(exc)
    return price_data, data_errors


def build_validation_variants(
    created_at: str,
    price_data: dict[str, list[dict[str, Any]]],
    data_errors: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    qqq_rows = price_data.get("QQQ", [])
    spy_rows = price_data.get("SPY", [])
    variants = [simulate_trend_gate(name, leverage, qqq_rows) for name, leverage in VARIANTS]
    qqq_benchmark = buy_and_hold_item("qqq_buy_and_hold", "QQQ buy-and-hold", qqq_rows)
    spy_benchmark = buy_and_hold_item("spy_buy_and_hold", "SPY buy-and-hold", spy_rows)
    cash_benchmark = cash_item(qqq_rows)
    benchmark = qqq_benchmark if qqq_benchmark["data_status"] == "ok" else spy_benchmark
    for variant in variants:
        variant["created_at"] = created_at
        apply_benchmark(variant, benchmark)
        if variant["data_status"] != "ok" and data_errors:
            variant["notes"] = variant["notes"] + " Data errors: " + "; ".join(f"{k}:{v}" for k, v in sorted(data_errors.items())[:2])
    for benchmark_item in [qqq_benchmark, spy_benchmark, cash_benchmark]:
        benchmark_item["created_at"] = created_at
        apply_benchmark(benchmark_item, benchmark)
    return variants + [qqq_benchmark, spy_benchmark, cash_benchmark]


def simulate_trend_gate(name: str, leverage: float, qqq_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(qqq_rows) < TREND_WINDOW + 2:
        return insufficient_item(name, leverage, "Missing usable QQQ daily history.")
    equity = STARTING_EQUITY
    curve = [{"date": qqq_rows[TREND_WINDOW]["date"], "equity": equity, "invested": 0.0}]
    exposure_change_count = 0
    previous_exposure = 0.0
    for index in range(TREND_WINDOW + 1, len(qqq_rows)):
        prev_close = qqq_rows[index - 1]["close"]
        close = qqq_rows[index]["close"]
        sma = average([row["close"] for row in qqq_rows[index - TREND_WINDOW : index]])
        exposure = leverage if prev_close > sma else 0.0
        if exposure != previous_exposure:
            exposure_change_count += 1
        daily_return = (close / prev_close) - 1.0
        daily_financing = max(0.0, exposure - 1.0) * (300 / 10000.0) / 252.0
        daily_trade_cost = abs(exposure - previous_exposure) * (10 / 10000.0)
        equity *= 1.0 + (daily_return * exposure) - daily_financing - daily_trade_cost
        curve.append({"date": qqq_rows[index]["date"], "equity": equity, "invested": exposure})
        previous_exposure = exposure
    return item(name, leverage, curve, exposure_change_count, "QQQ buy-and-hold")


def buy_and_hold_item(name: str, benchmark_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) < 2:
        return insufficient_item(name, 1.0, f"Missing usable {benchmark_name} history.")
    start = rows[0]["close"]
    curve = [{"date": row["date"], "equity": STARTING_EQUITY * row["close"] / start, "invested": 1.0} for row in rows]
    result = item(name, 1.0, curve, 1, benchmark_name)
    result["decision_label"] = "benchmark_not_candidate"
    result["notes"] = "Benchmark row for context only; not a leverage candidate."
    return result


def cash_item(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) < 2:
        return insufficient_item("cash_benchmark", 0.0, "Missing usable date index.")
    curve = [{"date": row["date"], "equity": STARTING_EQUITY, "invested": 0.0} for row in rows]
    result = item("cash_benchmark", 0.0, curve, 0, "cash benchmark")
    result["decision_label"] = "benchmark_not_candidate"
    result["notes"] = "Cash benchmark for context only."
    return result


def item(name: str, leverage: float, curve: list[dict[str, Any]], exposure_change_count: int, benchmark_name: str) -> dict[str, Any]:
    metrics = metrics_for_curve(curve)
    returns = daily_returns(curve)
    annual_vol = sample_stdev(returns) * (252.0**0.5) * 100.0 if returns else 0.0
    decision = decision_label(name, leverage, metrics)
    return {
        "variant_name": name,
        "period": "full_period",
        "data_status": "ok",
        "leverage_multiple": leverage,
        "curve": curve,
        "exposure_change_count": exposure_change_count,
        "turnover": round(exposure_change_count * leverage, 4),
        "time_invested_pct": round(average([float(row.get("invested", 0.0)) > 0 for row in curve]) * 100.0, 4),
        "cash_time_pct": round(average([float(row.get("invested", 0.0)) <= 0 for row in curve]) * 100.0, 4),
        "annualised_volatility_pct": round(annual_vol, 4),
        "benchmark_name": benchmark_name,
        "benchmark_cagr_pct": "",
        "benchmark_sharpe_ratio": "",
        "benchmark_max_drawdown_pct": "",
        "benchmark_calmar_ratio": "",
        "decision_label": decision,
        "notes": "Fixed QQQ SMA200 trend-gated synthetic leverage validation. Financing and costs are placeholders only.",
        **metrics,
    }


def insufficient_item(name: str, leverage: float, notes: str) -> dict[str, Any]:
    return {
        "variant_name": name,
        "period": "full_period",
        "data_status": "insufficient_market_data",
        "leverage_multiple": leverage,
        "curve": [],
        "exposure_change_count": 0,
        "turnover": 0.0,
        "time_invested_pct": 0.0,
        "cash_time_pct": 0.0,
        "annualised_volatility_pct": 0.0,
        "benchmark_name": "unavailable",
        "benchmark_cagr_pct": "",
        "benchmark_sharpe_ratio": "",
        "benchmark_max_drawdown_pct": "",
        "benchmark_calmar_ratio": "",
        "decision_label": "insufficient_market_data",
        "notes": notes,
        "cagr_pct": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown_pct": 0.0,
        "calmar_ratio": 0.0,
        "total_return_pct": 0.0,
    }


def apply_benchmark(row: dict[str, Any], benchmark: dict[str, Any]) -> None:
    if benchmark.get("data_status") != "ok":
        return
    row["benchmark_name"] = benchmark["variant_name"]
    row["benchmark_cagr_pct"] = round(parse_float(benchmark.get("cagr_pct")), 4)
    row["benchmark_sharpe_ratio"] = round(parse_float(benchmark.get("sharpe_ratio")), 4)
    row["benchmark_max_drawdown_pct"] = round(parse_float(benchmark.get("max_drawdown_pct")), 4)
    row["benchmark_calmar_ratio"] = round(parse_float(benchmark.get("calmar_ratio")), 4)


def build_report_row(created_at: str, variant: dict[str, Any], period: str) -> dict[str, Any]:
    row = common_row(created_at, variant, period)
    return row


def build_cost_rows(created_at: str, variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for variant in variants:
        if not is_candidate(variant):
            continue
        for cost_bps in TRANSACTION_COST_BPS:
            for financing_bps in FINANCING_BPS:
                stressed = stressed_metrics(variant, cost_bps, financing_bps)
                label = cost_sensitivity_label(variant, stressed)
                row = common_row(created_at, {**variant, **stressed, "decision_label": label}, "full_period")
                row.update(
                    {
                        "cost_bps": cost_bps,
                        "financing_bps_annual": financing_bps,
                        "cost_stress_cagr_pct": round(stressed["cagr_pct"], 4),
                        "cost_stress_calmar_ratio": round(stressed["calmar_ratio"], 4),
                        "cost_sensitivity_label": label,
                    }
                )
                rows.append(row)
    return rows


def build_split_rows(created_at: str, variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for variant in variants:
        if not is_candidate(variant):
            continue
        base_calmar = parse_float(variant.get("calmar_ratio"))
        curve = variant.get("curve", [])
        for split_name, fraction in [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]:
            if len(curve) < 4:
                split_metrics = {**variant, **metrics_for_curve([]), "decision_label": "insufficient_market_data"}
                split_curve = []
            else:
                split_index = max(1, min(len(curve) - 2, int(len(curve) * fraction)))
                split_curve = curve[split_index:]
                split_metrics = {**variant, **metrics_for_curve(split_curve)}
                split_metrics["annualised_volatility_pct"] = round(sample_stdev(daily_returns(split_curve)) * (252.0**0.5) * 100.0, 4)
                split_metrics["decision_label"] = split_sensitivity_label(base_calmar, parse_float(split_metrics.get("calmar_ratio")))
            row = common_row(created_at, split_metrics, "out_of_sample")
            row.update(
                {
                    "split_name": split_name,
                    "split_fraction": fraction,
                    "split_start_date": split_curve[0]["date"] if split_curve else "",
                    "split_end_date": split_curve[-1]["date"] if split_curve else "",
                    "split_sensitivity_label": row["decision_label"],
                }
            )
            rows.append(row)
    return rows


def build_drawdown_rows(created_at: str, variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for variant in variants:
        if not is_candidate(variant):
            continue
        row = common_row(created_at, variant, "worst_drawdown_period")
        row.update(drawdown_window(variant.get("curve", [])))
        rows.append(row)
    return rows


def build_summary_rows(
    created_at: str,
    report_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates = [row for row in report_rows if is_candidate(row) and row.get("data_status") == "ok"]
    best = best_candidate(candidates)
    lower = lower_drawdown_candidate(candidates, best)
    worst = min(candidates, key=lambda row: parse_float(row.get("max_drawdown_pct")), default={})
    overlevered = [row["variant_name"] for row in candidates if row.get("decision_label") == "qqq_leverage_overlevered_reject"]
    cost_sensitive = sorted({row["variant_name"] for row in cost_rows if row.get("cost_sensitivity_label") == "qqq_leverage_cost_sensitive"})
    split_sensitive = sorted({row["variant_name"] for row in split_rows if row.get("split_sensitivity_label") == "qqq_leverage_split_sensitive"})
    final = final_conclusion(best, lower)
    entries = [
        ("best_qqq_leverage_candidate", best.get("variant_name", "none") if best else "none", format_candidate(best)),
        ("best_lower_drawdown_candidate", lower.get("variant_name", "none") if lower else "none", format_candidate(lower)),
        ("worst_drawdown_warning", worst.get("variant_name", "none"), f"max_drawdown_pct={worst.get('max_drawdown_pct', '')}"),
        ("rejected_overlevered_candidates", ", ".join(overlevered) if overlevered else "none", "Higher CAGR alone is not enough when drawdown/Calmar deteriorate."),
        ("cost_financing_sensitivity_warning", ", ".join(cost_sensitive) if cost_sensitive else "none", "Placeholder costs only; not broker-specific financing terms."),
        ("split_sensitivity_warning", ", ".join(split_sensitive) if split_sensitive else "none", "Split weakness blocks any execution interpretation."),
        ("final_validation_conclusion", final, "Research label only; execution, margin, leverage, and scheduling remain false."),
    ]
    return [summary_row(created_at, name, value, details) for name, value, details in entries]


def common_row(created_at: str, variant: dict[str, Any], period: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "variant_name": variant["variant_name"],
        "period": period,
        "data_status": variant["data_status"],
        "leverage_multiple": variant["leverage_multiple"],
        "cagr_pct": round(parse_float(variant.get("cagr_pct")), 4),
        "annualised_volatility_pct": round(parse_float(variant.get("annualised_volatility_pct")), 4),
        "sharpe_ratio": round(parse_float(variant.get("sharpe_ratio")), 4),
        "max_drawdown_pct": round(parse_float(variant.get("max_drawdown_pct")), 4),
        "calmar_ratio": round(parse_float(variant.get("calmar_ratio")), 4),
        "total_return_pct": round(parse_float(variant.get("total_return_pct")), 4),
        "exposure_change_count": variant.get("exposure_change_count", 0),
        "turnover": variant.get("turnover", 0.0),
        "time_invested_pct": variant.get("time_invested_pct", 0.0),
        "cash_time_pct": variant.get("cash_time_pct", 0.0),
        "benchmark_name": variant.get("benchmark_name", ""),
        "benchmark_cagr_pct": variant.get("benchmark_cagr_pct", ""),
        "benchmark_sharpe_ratio": variant.get("benchmark_sharpe_ratio", ""),
        "benchmark_max_drawdown_pct": variant.get("benchmark_max_drawdown_pct", ""),
        "benchmark_calmar_ratio": variant.get("benchmark_calmar_ratio", ""),
        "decision_label": variant.get("decision_label", "synthetic_only_not_execution_ready"),
        "notes": variant.get("notes", ""),
        **safety_flags(),
    }


def summary_row(created_at: str, name: str, value: str, details: str) -> dict[str, Any]:
    return {"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": False,
        "execution_approved": False,
        "leverage_execution_approved": False,
        "margin_approved": False,
        "short_execution_approved": False,
        "scheduling_approved": False,
        "alpaca_called": False,
        "orders_created": False,
    }


def decision_label(name: str, leverage: float, metrics: dict[str, float]) -> str:
    if metrics["cagr_pct"] == 0.0 and metrics["calmar_ratio"] == 0.0:
        return "insufficient_market_data"
    if leverage >= 1.75 and metrics["max_drawdown_pct"] < -38.0:
        return "qqq_leverage_overlevered_reject"
    if leverage == 1.25 and metrics["max_drawdown_pct"] > -30.0 and metrics["calmar_ratio"] > 0.5:
        return "qqq_leverage_lower_drawdown_preferred"
    if leverage == 1.5 and metrics["calmar_ratio"] > 0.6 and metrics["sharpe_ratio"] > 0.75:
        return "qqq_leverage_validation_lead"
    if metrics["max_drawdown_pct"] < -32.0:
        return "qqq_leverage_promising_but_high_drawdown"
    return "synthetic_only_not_execution_ready"


def cost_sensitivity_label(variant: dict[str, Any], stressed: dict[str, float]) -> str:
    if parse_float(stressed.get("calmar_ratio")) < parse_float(variant.get("calmar_ratio")) - 0.08:
        return "qqq_leverage_cost_sensitive"
    return "synthetic_only_not_execution_ready"


def split_sensitivity_label(base_calmar: float, split_calmar: float) -> str:
    if split_calmar < 0 or split_calmar < base_calmar * 0.5:
        return "qqq_leverage_split_sensitive"
    return "synthetic_only_not_execution_ready"


def stressed_metrics(variant: dict[str, Any], cost_bps: int, financing_bps: int) -> dict[str, float]:
    curve = variant.get("curve", [])
    if len(curve) < 2:
        return metrics_for_curve([])
    years = max(1.0 / 252.0, (len(curve) - 1) / 252.0)
    excess_leverage = max(0.0, parse_float(variant.get("leverage_multiple")) - 1.0)
    time_invested = parse_float(variant.get("time_invested_pct")) / 100.0
    turnover = parse_float(variant.get("turnover"))
    drag_pct = (turnover * cost_bps / 100.0) + (financing_bps / 100.0 * years * excess_leverage * time_invested)
    stressed_final = max(0.01, float(curve[-1]["equity"]) * (1.0 - drag_pct / 100.0))
    return metrics_for_curve([*curve[:-1], {**curve[-1], "equity": stressed_final}])


def best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if is_candidate(row) and row.get("data_status") == "ok"]
    return max(candidates, key=lambda row: (parse_float(row.get("calmar_ratio")), parse_float(row.get("sharpe_ratio"))), default={})


def lower_drawdown_candidate(rows: list[dict[str, Any]], best: dict[str, Any]) -> dict[str, Any]:
    candidates = [row for row in rows if is_candidate(row) and row.get("data_status") == "ok"]
    if not best:
        return {}
    best_dd = abs(parse_float(best.get("max_drawdown_pct")))
    best_calmar = parse_float(best.get("calmar_ratio"))
    lower = [
        row
        for row in candidates
        if abs(parse_float(row.get("max_drawdown_pct"))) <= best_dd * 0.85
        and parse_float(row.get("calmar_ratio")) >= best_calmar * 0.85
    ]
    return max(lower, key=lambda row: (parse_float(row.get("calmar_ratio")), parse_float(row.get("sharpe_ratio"))), default={})


def final_conclusion(best: dict[str, Any], lower: dict[str, Any]) -> str:
    if not best:
        return "insufficient_market_data"
    if lower and lower.get("variant_name") != best.get("variant_name"):
        return "qqq_leverage_lower_drawdown_preferred"
    if best.get("variant_name") == "qqq_150_trend_gate":
        return "qqq_leverage_validation_lead"
    return "synthetic_only_not_execution_ready"


def format_candidate(row: dict[str, Any] | None) -> str:
    if not row:
        return "no usable candidate"
    return f"Calmar={row.get('calmar_ratio')}; Sharpe={row.get('sharpe_ratio')}; MaxDD={row.get('max_drawdown_pct')}; decision={row.get('decision_label')}"


def is_candidate(row: dict[str, Any]) -> bool:
    return str(row.get("variant_name", "")).startswith("qqq_") and str(row.get("variant_name")) not in {"qqq_buy_and_hold"}


def daily_returns(curve: list[dict[str, Any]]) -> list[float]:
    values = [float(row["equity"]) for row in curve]
    return [(values[index] / values[index - 1]) - 1.0 for index in range(1, len(values)) if values[index - 1] > 0]


def build_summary_lines(
    output_paths: dict[str, Path],
    report_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
) -> list[str]:
    candidates = [row for row in report_rows if is_candidate(row) and row.get("data_status") == "ok"]
    best = best_candidate(candidates)
    lower = lower_drawdown_candidate(candidates, best)
    worst = min(candidates, key=lambda row: parse_float(row.get("max_drawdown_pct")), default={})
    overlevered = [row["variant_name"] for row in candidates if row.get("decision_label") == "qqq_leverage_overlevered_reject"]
    cost_sensitive = sorted({row["variant_name"] for row in cost_rows if row.get("cost_sensitivity_label") == "qqq_leverage_cost_sensitive"})
    split_sensitive = sorted({row["variant_name"] for row in split_rows if row.get("split_sensitivity_label") == "qqq_leverage_split_sensitive"})
    return [
        "QQQ LEVERAGE VALIDATION REPORT. SYNTHETIC RESEARCH ONLY. NOT EXECUTION.",
        f"Saved report: {output_paths['report']}",
        f"Saved summary/costs/splits/drawdowns: {output_paths['summary']}; {output_paths['costs']}; {output_paths['splits']}; {output_paths['drawdowns']}",
        f"Best QQQ leverage candidate by Calmar/Sharpe: {best.get('variant_name', 'none')} ({format_candidate(best)})",
        f"Best lower-drawdown candidate: {lower.get('variant_name', 'none') if lower else 'none'} ({format_candidate(lower)})",
        f"Worst drawdown warning: {worst.get('variant_name', 'none')} max_drawdown_pct={worst.get('max_drawdown_pct', '')}",
        f"Rejected over-levered candidates: {', '.join(overlevered) if overlevered else 'none'}",
        f"Cost/financing sensitivity warning: {', '.join(cost_sensitive) if cost_sensitive else 'placeholder stress rows produced; no broker-specific claim'}",
        f"Split sensitivity warning: {', '.join(split_sensitive) if split_sensitive else 'none'}",
        f"Data issues: {len(data_errors)} ticker errors" if data_errors else "Data issues: none reported by yfinance",
        f"Final validation conclusion: {final_conclusion(best, lower)}.",
        "execution_approved=false; leverage_execution_approved=false; margin_approved=false; scheduling_approved=false",
        "No Alpaca commands, order instructions, margin approval, leverage approval, short approval, or scheduling approval are produced.",
    ]


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
