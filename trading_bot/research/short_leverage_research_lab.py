"""Research-only synthetic short/leverage hypothesis lab.

This module tests a small fixed set of synthetic hypotheses. It does not call
Alpaca, read positions, create orders, write SQLite, send alerts, schedule
anything, or approve shorting, margin, leverage, or execution.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location


OUTPUT_FILES = {
    "results": Path("data/short_leverage_research_lab.csv"),
    "summary": Path("data/short_leverage_research_lab_summary.csv"),
    "costs": Path("data/short_leverage_research_lab_costs.csv"),
    "splits": Path("data/short_leverage_research_lab_splits.csv"),
    "drawdowns": Path("data/short_leverage_research_lab_drawdowns.csv"),
}

HISTORY_PERIOD = "10y"
DAILY_INTERVAL = "1d"
STARTING_EQUITY = 10000.0
TREND_WINDOW = 200
MOMENTUM_WINDOW = 126
MONTHLY_REBALANCE_DAYS = 21
TRANSACTION_COST_BPS = [0, 10, 25, 50]
BORROW_FEE_BPS = [0, 300, 700]
FINANCING_BPS = [0, 300, 600]
SECTOR_ETFS = ["XLK", "XLY", "XLF", "XLI", "XLE", "XLP", "XLU", "XLV", "XLB", "XLRE", "XLC"]
DEFENSIVE_BASKET = ["XLP", "XLU", "XLV"]
CYCLICAL_BASKET = ["XLY", "XLF", "XLI"]
MARKET_TICKERS = sorted(set(["SPY", "QQQ"] + SECTOR_ETFS + DEFENSIVE_BASKET + CYCLICAL_BASKET))
ACTIVE_LEAD_CANDIDATES = [
    "codex_ambitious_concentrated_growth_persistence",
    "growth_biased_rotation_breadth_stricter_gate",
]

COMMON_COLUMNS = [
    "created_at",
    "hypothesis_name",
    "hypothesis_family",
    "period",
    "data_status",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "total_return_pct",
    "turnover",
    "time_invested_pct",
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
    "short_execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

RESULT_COLUMNS = COMMON_COLUMNS + [
    "synthetic_leverage_multiple",
    "synthetic_short_exposure",
    "borrow_fee_bps_annual",
    "financing_bps_annual",
    "cost_bps",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "execution_approved",
    "short_execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

COST_COLUMNS = COMMON_COLUMNS + [
    "cost_bps",
    "borrow_fee_bps_annual",
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
]

DRAWDOWN_COLUMNS = COMMON_COLUMNS + [
    "drawdown_start",
    "drawdown_trough",
    "drawdown_recovery",
    "drawdown_recovered",
    "drawdown_days",
]


@dataclass
class ShortLeverageLabResult:
    output_paths: dict[str, Path]
    result_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    summary_lines: list[str]


def run_short_leverage_research_lab(root_dir: Path | str = ".") -> ShortLeverageLabResult:
    root = Path(root_dir)
    configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    price_data, data_errors = download_daily_price_data(MARKET_TICKERS)
    lead_curve, lead_status = read_saved_active_lead_equity_curve(root)
    hypotheses = build_hypotheses(price_data, lead_curve, lead_status, created_at, data_errors)
    result_rows = [build_result_row(created_at, item, "full_period") for item in hypotheses]
    split_rows = build_split_rows(created_at, hypotheses)
    cost_rows = build_cost_rows(created_at, hypotheses)
    drawdown_rows = build_drawdown_rows(created_at, hypotheses)
    summary_rows = build_summary_rows(created_at, result_rows, cost_rows)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["results"], RESULT_COLUMNS, result_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["costs"], COST_COLUMNS, cost_rows)
    write_rows(output_paths["splits"], SPLIT_COLUMNS, split_rows)
    write_rows(output_paths["drawdowns"], DRAWDOWN_COLUMNS, drawdown_rows)
    return ShortLeverageLabResult(
        output_paths=output_paths,
        result_rows=result_rows,
        summary_rows=summary_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        drawdown_rows=drawdown_rows,
        summary_lines=build_summary_lines(output_paths, result_rows, cost_rows, data_errors),
    )


def show_short_leverage_research_lab(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    results_path = root / OUTPUT_FILES["results"]
    if not summary_path.exists() or not results_path.exists():
        return 1, ["Run `python bot.py --short-leverage-research-lab` first."]
    summary_rows = read_csv_rows(summary_path)
    result_rows = read_csv_rows(results_path)
    lines = ["SHORT/LEVERAGE RESEARCH LAB SAVED DISPLAY. NOT EXECUTION."]
    for row in summary_rows:
        lines.append(f"{row.get('summary_name')}: {row.get('summary_value')} - {row.get('details')}")
    best = best_row(result_rows, "synthetic_leverage")
    short_best = best_row(result_rows, "synthetic_short_or_spread")
    if best:
        lines.append(f"Best saved synthetic leverage candidate: {best['hypothesis_name']} Calmar={best['calmar_ratio']}")
    if short_best:
        lines.append(f"Best saved synthetic short/spread candidate: {short_best['hypothesis_name']} Calmar={short_best['calmar_ratio']}")
    lines.append("execution_approved=false; short_execution_approved=false; leverage_execution_approved=false; margin_approved=false")
    lines.append("Warning: saved display only; no orders, Alpaca calls, short approval, margin approval, or scheduling approval.")
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
            if len(rows) < TREND_WINDOW + MOMENTUM_WINDOW:
                data_errors[ticker] = f"Not enough daily history; got {len(rows)} usable rows."
                continue
            price_data[ticker] = rows
        except Exception as exc:
            data_errors[ticker] = str(exc)
    return price_data, data_errors


def value_from_row(row: Any, column_name: str) -> float | None:
    try:
        value = row[column_name]
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        return float(value)
    except Exception:
        return None


def read_saved_active_lead_equity_curve(root: Path) -> tuple[list[dict[str, Any]], str]:
    path = root / "data/strategy_improvement_lab_equity_curve.csv"
    if not path.exists():
        return [], "insufficient_saved_inputs"
    try:
        rows = read_csv_rows(path)
    except Exception:
        return [], "insufficient_saved_inputs"
    for strategy_name in ACTIVE_LEAD_CANDIDATES:
        curve = [
            {"date": row["date"], "equity": float(row["equity"])}
            for row in rows
            if row.get("strategy_name") == strategy_name and row.get("period") == "full_period" and parse_float(row.get("equity")) > 0
        ]
        if len(curve) > 2:
            return curve, f"saved_active_lead_equity_curve:{strategy_name}"
    return [], "insufficient_saved_inputs"


def build_hypotheses(
    price_data: dict[str, list[dict[str, Any]]],
    lead_curve: list[dict[str, Any]],
    lead_status: str,
    created_at: str,
    data_errors: dict[str, str],
) -> list[dict[str, Any]]:
    items = [
        trend_gate_item("synthetic_spy_150_trend_gate", "SPY", 1.5, 300, price_data),
        trend_gate_item("synthetic_spy_200_trend_gate", "SPY", 2.0, 600, price_data),
        trend_gate_item("synthetic_qqq_150_trend_gate", "QQQ", 1.5, 300, price_data),
        lead_proxy_item("growth_lead_125_synthetic_leverage_proxy", 1.25, 300, lead_curve, lead_status),
        lead_proxy_item("growth_lead_150_synthetic_leverage_proxy", 1.5, 600, lead_curve, lead_status),
        spy_short_hedge_item(price_data),
        sector_relative_long_short_item(price_data),
        defensive_vs_cyclical_spread_item(price_data),
    ]
    for item in items:
        item["created_at"] = created_at
        if item["data_status"] == "insufficient_market_data" and data_errors:
            item["notes"] = item["notes"] + " Data errors: " + "; ".join(f"{k}:{v}" for k, v in sorted(data_errors.items())[:4])
    return items


def trend_gate_item(name: str, ticker: str, leverage: float, financing_bps: int, price_data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = price_data.get(ticker, [])
    if len(rows) < TREND_WINDOW + 2:
        return insufficient_item(name, "synthetic_leverage", f"Missing usable {ticker} history.")
    equity = STARTING_EQUITY
    curve = [{"date": rows[TREND_WINDOW]["date"], "equity": equity, "invested": 0.0}]
    trades = 0
    previous_invested = 0.0
    for index in range(TREND_WINDOW + 1, len(rows)):
        prev_close = rows[index - 1]["close"]
        close = rows[index]["close"]
        sma = average([row["close"] for row in rows[index - TREND_WINDOW : index]])
        invested = leverage if prev_close > sma else 0.0
        daily_return = (close / prev_close) - 1.0
        daily_financing = max(0.0, invested - 1.0) * (financing_bps / 10000.0) / 252.0
        if invested != previous_invested:
            trades += 1
        equity *= 1.0 + (daily_return * invested) - daily_financing
        curve.append({"date": rows[index]["date"], "equity": equity, "invested": invested})
        previous_invested = invested
    return item(name, "synthetic_leverage", curve, trades, leverage, 0.0, 0, financing_bps, "SPY buy-and-hold benchmark")


def lead_proxy_item(name: str, leverage: float, financing_bps: int, lead_curve: list[dict[str, Any]], lead_status: str) -> dict[str, Any]:
    if len(lead_curve) < 3:
        return insufficient_item(name, "synthetic_leverage", f"{lead_status}; no saved active-lead equity curve was used.")
    equity = STARTING_EQUITY
    curve = [{"date": lead_curve[0]["date"], "equity": equity, "invested": leverage}]
    for index in range(1, len(lead_curve)):
        previous = float(lead_curve[index - 1]["equity"])
        current = float(lead_curve[index]["equity"])
        daily_return = (current / previous) - 1.0 if previous > 0 else 0.0
        daily_financing = max(0.0, leverage - 1.0) * (financing_bps / 10000.0) / 252.0
        equity *= 1.0 + (daily_return * leverage) - daily_financing
        curve.append({"date": lead_curve[index]["date"], "equity": equity, "invested": leverage})
    return item(name, "synthetic_leverage", curve, 1, leverage, 0.0, 0, financing_bps, "saved active stock/ETF research lead")


def spy_short_hedge_item(price_data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = price_data.get("SPY", [])
    if len(rows) < TREND_WINDOW + 2:
        return insufficient_item("synthetic_spy_short_hedge_weak_regime", "synthetic_short_or_spread", "Missing usable SPY history.")
    equity = STARTING_EQUITY
    curve = [{"date": rows[TREND_WINDOW]["date"], "equity": equity, "invested": 0.0}]
    trades = 0
    previous_exposure = 0.0
    for index in range(TREND_WINDOW + 1, len(rows)):
        prev_close = rows[index - 1]["close"]
        close = rows[index]["close"]
        sma = average([row["close"] for row in rows[index - TREND_WINDOW : index]])
        exposure = -1.0 if prev_close < sma else 0.0
        if exposure != previous_exposure:
            trades += 1
        daily_return = (close / prev_close) - 1.0
        borrow_drag = abs(exposure) * (300 / 10000.0) / 252.0
        equity *= 1.0 + (daily_return * exposure) - borrow_drag
        curve.append({"date": rows[index]["date"], "equity": equity, "invested": abs(exposure)})
        previous_exposure = exposure
    return item("synthetic_spy_short_hedge_weak_regime", "synthetic_short_or_spread", curve, trades, 1.0, -1.0, 300, 0, "cash and SPY buy-and-hold")


def sector_relative_long_short_item(price_data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    aligned = align_prices({ticker: price_data.get(ticker, []) for ticker in SECTOR_ETFS})
    if len(aligned) < MOMENTUM_WINDOW + 2:
        return insufficient_item("sector_relative_long_short_fixed", "synthetic_short_or_spread", "Missing usable sector ETF history.")
    equity = STARTING_EQUITY
    curve = [{"date": aligned[MOMENTUM_WINDOW]["date"], "equity": equity, "invested": 0.0}]
    weights: dict[str, float] = {}
    trades = 0
    for index in range(MOMENTUM_WINDOW + 1, len(aligned)):
        if (index - MOMENTUM_WINDOW) % MONTHLY_REBALANCE_DAYS == 1:
            momentum = {
                ticker: (aligned[index - 1][ticker] / aligned[index - MOMENTUM_WINDOW][ticker]) - 1.0
                for ticker in SECTOR_ETFS
            }
            ranked = sorted(momentum, key=momentum.get, reverse=True)
            new_weights = {ticker: 0.5 for ticker in ranked[:2]}
            new_weights.update({ticker: -0.25 for ticker in ranked[-2:]})
            trades += count_weight_changes(weights, new_weights)
            weights = new_weights
        daily_return = sum(weights.get(ticker, 0.0) * ((aligned[index][ticker] / aligned[index - 1][ticker]) - 1.0) for ticker in weights)
        borrow_drag = sum(abs(weight) for weight in weights.values() if weight < 0) * (300 / 10000.0) / 252.0
        equity *= 1.0 + daily_return - borrow_drag
        curve.append({"date": aligned[index]["date"], "equity": equity, "invested": sum(abs(weight) for weight in weights.values())})
    return item("sector_relative_long_short_fixed", "synthetic_short_or_spread", curve, trades, 1.5, -0.5, 300, 0, "SPY and cash benchmark")


def defensive_vs_cyclical_spread_item(price_data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    tickers = sorted(set(["SPY"] + DEFENSIVE_BASKET + CYCLICAL_BASKET))
    aligned = align_prices({ticker: price_data.get(ticker, []) for ticker in tickers})
    if len(aligned) < TREND_WINDOW + 2:
        return insufficient_item("defensive_vs_cyclical_spread_fixed", "synthetic_short_or_spread", "Missing usable defensive/cyclical ETF history.")
    equity = STARTING_EQUITY
    curve = [{"date": aligned[TREND_WINDOW]["date"], "equity": equity, "invested": 0.0}]
    weights: dict[str, float] = {}
    trades = 0
    for index in range(TREND_WINDOW + 1, len(aligned)):
        spy_sma = average([row["SPY"] for row in aligned[index - TREND_WINDOW : index]])
        weak_regime = aligned[index - 1]["SPY"] < spy_sma
        new_weights = {}
        if weak_regime:
            new_weights.update({ticker: 1.0 / len(DEFENSIVE_BASKET) for ticker in DEFENSIVE_BASKET})
            new_weights.update({ticker: -0.5 / len(CYCLICAL_BASKET) for ticker in CYCLICAL_BASKET})
        if new_weights != weights:
            trades += count_weight_changes(weights, new_weights)
            weights = new_weights
        daily_return = sum(weights.get(ticker, 0.0) * ((aligned[index][ticker] / aligned[index - 1][ticker]) - 1.0) for ticker in weights)
        borrow_drag = sum(abs(weight) for weight in weights.values() if weight < 0) * (300 / 10000.0) / 252.0
        equity *= 1.0 + daily_return - borrow_drag
        curve.append({"date": aligned[index]["date"], "equity": equity, "invested": sum(abs(weight) for weight in weights.values())})
    return item("defensive_vs_cyclical_spread_fixed", "synthetic_short_or_spread", curve, trades, 1.5, -0.5, 300, 0, "SPY and cash benchmark")


def item(
    name: str,
    family: str,
    curve: list[dict[str, Any]],
    trades: int,
    leverage: float,
    short_exposure: float,
    borrow_bps: int,
    financing_bps: int,
    benchmark_name: str,
) -> dict[str, Any]:
    metrics = metrics_for_curve(curve)
    label = decision_label(name, family, metrics, borrow_bps, financing_bps)
    notes = "Synthetic research-only hypothesis. Costs are placeholders, not broker-specific terms."
    if "200" in name or "150" in name:
        notes += " Higher drawdown, leverage decay, and financing risk require manual review."
    return {
        "hypothesis_name": name,
        "hypothesis_family": family,
        "data_status": "ok",
        "curve": curve,
        "trade_count": trades,
        "turnover": round(trades / max(1, len(curve) / 252.0), 4),
        "time_invested_pct": round(average([float(row.get("invested", 0.0)) > 0 for row in curve]) * 100.0, 4),
        "synthetic_leverage_multiple": leverage,
        "synthetic_short_exposure": short_exposure,
        "borrow_fee_bps_annual": borrow_bps,
        "financing_bps_annual": financing_bps,
        "cost_bps": 0,
        "benchmark_name": benchmark_name,
        "decision_label": label,
        "notes": notes,
        **metrics,
    }


def insufficient_item(name: str, family: str, notes: str) -> dict[str, Any]:
    return {
        "hypothesis_name": name,
        "hypothesis_family": family,
        "data_status": "insufficient_saved_inputs" if "lead" in name else "insufficient_market_data",
        "curve": [],
        "trade_count": 0,
        "turnover": 0.0,
        "time_invested_pct": 0.0,
        "synthetic_leverage_multiple": 0.0,
        "synthetic_short_exposure": 0.0,
        "borrow_fee_bps_annual": 0,
        "financing_bps_annual": 0,
        "cost_bps": 0,
        "benchmark_name": "unavailable",
        "decision_label": "insufficient_saved_inputs",
        "notes": notes,
        "cagr_pct": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown_pct": 0.0,
        "calmar_ratio": 0.0,
        "total_return_pct": 0.0,
    }


def build_result_row(created_at: str, item_row: dict[str, Any], period: str) -> dict[str, Any]:
    row = common_row(created_at, item_row, period)
    row.update(
        {
            "synthetic_leverage_multiple": item_row["synthetic_leverage_multiple"],
            "synthetic_short_exposure": item_row["synthetic_short_exposure"],
            "borrow_fee_bps_annual": item_row["borrow_fee_bps_annual"],
            "financing_bps_annual": item_row["financing_bps_annual"],
            "cost_bps": item_row["cost_bps"],
        }
    )
    return row


def build_split_rows(created_at: str, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for hypothesis in hypotheses:
        curve = hypothesis.get("curve", [])
        for split_name, fraction in [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]:
            if len(curve) < 4:
                split_metrics = insufficient_item(hypothesis["hypothesis_name"], hypothesis["hypothesis_family"], hypothesis["notes"])
                split_curve = []
            else:
                split_index = max(1, min(len(curve) - 2, int(len(curve) * fraction)))
                split_curve = curve[split_index:]
                split_metrics = {**hypothesis, **metrics_for_curve(split_curve)}
            row = common_row(created_at, split_metrics, "out_of_sample")
            row.update(
                {
                    "split_name": split_name,
                    "split_fraction": fraction,
                    "split_start_date": split_curve[0]["date"] if split_curve else "",
                    "split_end_date": split_curve[-1]["date"] if split_curve else "",
                }
            )
            rows.append(row)
    return rows


def build_cost_rows(created_at: str, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for hypothesis in hypotheses:
        cost_levels = BORROW_FEE_BPS if hypothesis["hypothesis_family"] == "synthetic_short_or_spread" else FINANCING_BPS
        for trade_cost in TRANSACTION_COST_BPS:
            for annual_cost in cost_levels:
                stressed = stressed_metrics(hypothesis, trade_cost, annual_cost)
                row = common_row(created_at, {**hypothesis, **stressed}, "full_period")
                row.update(
                    {
                        "cost_bps": trade_cost,
                        "borrow_fee_bps_annual": annual_cost if hypothesis["hypothesis_family"] == "synthetic_short_or_spread" else 0,
                        "financing_bps_annual": annual_cost if hypothesis["hypothesis_family"] == "synthetic_leverage" else 0,
                        "cost_stress_cagr_pct": stressed["cagr_pct"],
                        "cost_stress_calmar_ratio": stressed["calmar_ratio"],
                        "cost_sensitivity_label": cost_sensitivity_label(hypothesis, stressed),
                    }
                )
                rows.append(row)
    return rows


def build_drawdown_rows(created_at: str, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for hypothesis in hypotheses:
        dd = drawdown_window(hypothesis.get("curve", []))
        row = common_row(created_at, hypothesis, "worst_drawdown_period")
        row.update(dd)
        rows.append(row)
    return rows


def build_summary_rows(created_at: str, result_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_leverage = best_row(result_rows, "synthetic_leverage")
    best_short = best_row(result_rows, "synthetic_short_or_spread")
    worst = min(result_rows, key=lambda row: parse_float(row.get("max_drawdown_pct")), default={})
    cost_sensitive = [row["hypothesis_name"] for row in cost_rows if row.get("cost_sensitivity_label") in {"leverage_candidate_cost_sensitive", "short_candidate_borrow_fee_sensitive"}]
    entries = [
        ("best_synthetic_leverage_candidate", best_leverage.get("hypothesis_name", "none") if best_leverage else "none", format_candidate(best_leverage)),
        ("best_synthetic_short_spread_candidate", best_short.get("hypothesis_name", "none") if best_short else "none", format_candidate(best_short)),
        ("worst_drawdown_warning", worst.get("hypothesis_name", "none"), f"max_drawdown_pct={worst.get('max_drawdown_pct', '')}"),
        ("cost_borrow_sensitivity_warning", str(len(set(cost_sensitive))), "Placeholder cost/borrow/financing sensitivity only; not broker-specific."),
        ("final_research_conclusion", "synthetic_only_not_execution_ready", "No row approves shorting, leverage, margin, scheduling, orders, or Alpaca execution."),
    ]
    return [summary_row(created_at, name, value, details) for name, value, details in entries]


def common_row(created_at: str, item_row: dict[str, Any], period: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "hypothesis_name": item_row["hypothesis_name"],
        "hypothesis_family": item_row["hypothesis_family"],
        "period": period,
        "data_status": item_row["data_status"],
        "cagr_pct": round(parse_float(item_row.get("cagr_pct")), 4),
        "sharpe_ratio": round(parse_float(item_row.get("sharpe_ratio")), 4),
        "max_drawdown_pct": round(parse_float(item_row.get("max_drawdown_pct")), 4),
        "calmar_ratio": round(parse_float(item_row.get("calmar_ratio")), 4),
        "total_return_pct": round(parse_float(item_row.get("total_return_pct")), 4),
        "turnover": item_row.get("turnover", 0.0),
        "time_invested_pct": item_row.get("time_invested_pct", 0.0),
        "benchmark_name": item_row.get("benchmark_name", "unavailable"),
        "benchmark_cagr_pct": "",
        "benchmark_sharpe_ratio": "",
        "benchmark_max_drawdown_pct": "",
        "benchmark_calmar_ratio": "",
        "decision_label": item_row.get("decision_label", "synthetic_only_not_execution_ready"),
        "notes": item_row.get("notes", ""),
        **safety_flags(),
    }


def summary_row(created_at: str, name: str, value: str, details: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "summary_name": name,
        "summary_value": value,
        "details": details,
        **safety_flags(),
    }


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": False,
        "execution_approved": False,
        "short_execution_approved": False,
        "leverage_execution_approved": False,
        "margin_approved": False,
        "scheduling_approved": False,
        "alpaca_called": False,
        "orders_created": False,
    }


def metrics_for_curve(curve: list[dict[str, Any]]) -> dict[str, float]:
    if len(curve) < 2:
        return {"cagr_pct": 0.0, "sharpe_ratio": 0.0, "max_drawdown_pct": 0.0, "calmar_ratio": 0.0, "total_return_pct": 0.0}
    values = [float(row["equity"]) for row in curve]
    total_return = ((values[-1] / values[0]) - 1.0) * 100.0 if values[0] > 0 else 0.0
    cagr = (((values[-1] / values[0]) ** (252.0 / max(1, len(values) - 1))) - 1.0) * 100.0 if values[0] > 0 else 0.0
    returns = [(values[index] / values[index - 1]) - 1.0 for index in range(1, len(values)) if values[index - 1] > 0]
    sharpe = (average(returns) / sample_stdev(returns) * math.sqrt(252.0)) if sample_stdev(returns) > 0 else 0.0
    max_dd = max_drawdown_pct(values)
    calmar = cagr / abs(max_dd) if max_dd < 0 else 0.0
    return {"cagr_pct": cagr, "sharpe_ratio": sharpe, "max_drawdown_pct": max_dd, "calmar_ratio": calmar, "total_return_pct": total_return}


def max_drawdown_pct(values: list[float]) -> float:
    peak = values[0] if values else 0.0
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, ((value / peak) - 1.0) * 100.0)
    return worst


def drawdown_window(curve: list[dict[str, Any]]) -> dict[str, Any]:
    if len(curve) < 2:
        return {"drawdown_start": "", "drawdown_trough": "", "drawdown_recovery": "", "drawdown_recovered": False, "drawdown_days": 0}
    peak_value = float(curve[0]["equity"])
    peak_index = 0
    worst_dd = 0.0
    start_index = 0
    trough_index = 0
    for index, row in enumerate(curve):
        value = float(row["equity"])
        if value > peak_value:
            peak_value = value
            peak_index = index
        drawdown = (value / peak_value) - 1.0 if peak_value > 0 else 0.0
        if drawdown < worst_dd:
            worst_dd = drawdown
            start_index = peak_index
            trough_index = index
    recovery_index = None
    start_peak = float(curve[start_index]["equity"])
    for index in range(trough_index, len(curve)):
        if float(curve[index]["equity"]) >= start_peak:
            recovery_index = index
            break
    return {
        "drawdown_start": curve[start_index]["date"],
        "drawdown_trough": curve[trough_index]["date"],
        "drawdown_recovery": curve[recovery_index]["date"] if recovery_index is not None else "",
        "drawdown_recovered": recovery_index is not None,
        "drawdown_days": max(0, (recovery_index or trough_index) - start_index),
    }


def decision_label(name: str, family: str, metrics: dict[str, float], borrow_bps: int, financing_bps: int) -> str:
    if family == "synthetic_short_or_spread" and borrow_bps >= 300:
        return "short_candidate_borrow_fee_sensitive"
    if family == "synthetic_leverage" and financing_bps >= 600:
        return "leverage_candidate_cost_sensitive"
    if metrics["max_drawdown_pct"] < -35.0:
        return "leverage_candidate_promising_but_high_drawdown" if family == "synthetic_leverage" else "short_leverage_candidate_rejected"
    if metrics["calmar_ratio"] > 0.4 and metrics["sharpe_ratio"] > 0.5:
        return "synthetic_only_not_execution_ready"
    return "short_leverage_candidate_rejected"


def stressed_metrics(hypothesis: dict[str, Any], trade_cost_bps: int, annual_cost_bps: int) -> dict[str, float]:
    curve = hypothesis.get("curve", [])
    if len(curve) < 2:
        return metrics_for_curve([])
    years = max(1.0 / 252.0, (len(curve) - 1) / 252.0)
    turnover = parse_float(hypothesis.get("turnover"))
    time_invested = parse_float(hypothesis.get("time_invested_pct")) / 100.0
    drag_pct = (turnover * trade_cost_bps / 100.0) + (annual_cost_bps / 100.0 * years * time_invested)
    values = [float(row["equity"]) for row in curve]
    stressed_final = max(0.01, values[-1] * (1.0 - drag_pct / 100.0))
    stressed_curve = [*curve[:-1], {**curve[-1], "equity": stressed_final}]
    return metrics_for_curve(stressed_curve)


def cost_sensitivity_label(hypothesis: dict[str, Any], stressed: dict[str, float]) -> str:
    delta = parse_float(stressed.get("calmar_ratio")) - parse_float(hypothesis.get("calmar_ratio"))
    if hypothesis["hypothesis_family"] == "synthetic_short_or_spread" and delta < -0.05:
        return "short_candidate_borrow_fee_sensitive"
    if hypothesis["hypothesis_family"] == "synthetic_leverage" and delta < -0.05:
        return "leverage_candidate_cost_sensitive"
    return "synthetic_only_not_execution_ready"


def align_prices(price_by_ticker: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    date_sets = [{row["date"] for row in rows} for rows in price_by_ticker.values() if rows]
    if not date_sets or len(date_sets) != len(price_by_ticker):
        return []
    common_dates = sorted(set.intersection(*date_sets))
    lookup = {ticker: {row["date"]: row["close"] for row in rows} for ticker, rows in price_by_ticker.items()}
    return [{"date": date, **{ticker: lookup[ticker][date] for ticker in price_by_ticker}} for date in common_dates]


def count_weight_changes(old: dict[str, float], new: dict[str, float]) -> int:
    tickers = set(old) | set(new)
    return sum(1 for ticker in tickers if abs(old.get(ticker, 0.0) - new.get(ticker, 0.0)) > 0.000001)


def best_row(rows: list[dict[str, Any]], family: str) -> dict[str, Any]:
    candidates = [row for row in rows if row.get("hypothesis_family") == family and row.get("data_status") == "ok"]
    return max(candidates, key=lambda row: (parse_float(row.get("calmar_ratio")), parse_float(row.get("sharpe_ratio"))), default={})


def format_candidate(row: dict[str, Any] | None) -> str:
    if not row:
        return "no usable candidate"
    return f"Calmar={row.get('calmar_ratio')}; Sharpe={row.get('sharpe_ratio')}; MaxDD={row.get('max_drawdown_pct')}; decision={row.get('decision_label')}"


def build_summary_lines(
    output_paths: dict[str, Path],
    result_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
) -> list[str]:
    best_leverage = best_row(result_rows, "synthetic_leverage")
    best_short = best_row(result_rows, "synthetic_short_or_spread")
    worst = min(result_rows, key=lambda row: parse_float(row.get("max_drawdown_pct")), default={})
    rejected = [row["hypothesis_name"] for row in result_rows if row.get("decision_label") in {"short_leverage_candidate_rejected", "insufficient_saved_inputs"}]
    sensitive = sorted({row["hypothesis_name"] for row in cost_rows if row.get("cost_sensitivity_label") != "synthetic_only_not_execution_ready"})
    return [
        "SHORT/LEVERAGE RESEARCH LAB. SYNTHETIC ONLY. NOT EXECUTION.",
        f"Saved results: {output_paths['results']}",
        f"Saved summary: {output_paths['summary']}",
        f"Saved costs/splits/drawdowns: {output_paths['costs']}; {output_paths['splits']}; {output_paths['drawdowns']}",
        f"Best synthetic leverage candidate by Calmar/Sharpe: {best_leverage.get('hypothesis_name', 'none')} ({format_candidate(best_leverage)})",
        f"Best synthetic short/spread candidate by Calmar/Sharpe: {best_short.get('hypothesis_name', 'none')} ({format_candidate(best_short)})",
        f"Worst drawdown warning: {worst.get('hypothesis_name', 'none')} max_drawdown_pct={worst.get('max_drawdown_pct', '')}",
        f"Cost/borrow/financing sensitivity warning: {', '.join(sensitive) if sensitive else 'placeholder stress rows produced; no broker-specific claim'}",
        f"Rejected or insufficient candidates: {', '.join(rejected) if rejected else 'none'}",
        f"Data issues: {len(data_errors)} ticker errors" if data_errors else "Data issues: none reported by yfinance",
        "Final research conclusion: synthetic_only_not_execution_ready.",
        "execution_approved=false; short_execution_approved=false; leverage_execution_approved=false; margin_approved=false",
        "No Alpaca commands, order instructions, margin approval, short execution approval, or scheduling approval are produced.",
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


def average(values: list[Any]) -> float:
    numeric = [float(value) for value in values]
    return sum(numeric) / len(numeric) if numeric else 0.0


def sample_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = average(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
