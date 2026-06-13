"""Research-only QQQ adaptive trend/leverage lab.

This module compares fixed QQQ trend-gated references with two fixed adaptive
synthetic exposure ideas. It does not call Alpaca, read config or positions,
create orders, write SQLite, send alerts, schedule anything, or approve
leverage, margin, or execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location
from trading_bot.research.qqq_leverage_validation import (
    FINANCING_BPS,
    HISTORY_PERIOD,
    STARTING_EQUITY,
    TRANSACTION_COST_BPS,
    TREND_WINDOW,
    apply_benchmark,
    build_cost_rows as build_reference_cost_rows,
    build_drawdown_rows as build_reference_drawdown_rows,
    build_report_row,
    build_split_rows as build_reference_split_rows,
    buy_and_hold_item,
    cash_item,
    common_row,
    daily_returns,
    download_daily_price_data,
    insufficient_item,
    is_candidate,
    simulate_trend_gate,
    split_sensitivity_label,
    stressed_metrics,
)
from trading_bot.research.short_leverage_research_lab import (
    average,
    drawdown_window,
    metrics_for_curve,
    parse_float,
    sample_stdev,
)


OUTPUT_FILES = {
    "report": Path("data/qqq_adaptive_leverage_lab.csv"),
    "summary": Path("data/qqq_adaptive_leverage_lab_summary.csv"),
    "costs": Path("data/qqq_adaptive_leverage_lab_costs.csv"),
    "splits": Path("data/qqq_adaptive_leverage_lab_splits.csv"),
    "drawdowns": Path("data/qqq_adaptive_leverage_lab_drawdowns.csv"),
}

VOL_LOOKBACK = 20
VOL_MEDIAN_LOOKBACK = 252
FAVOURABLE_VOL_MULTIPLE = 0.90
ELEVATED_VOL_MULTIPLE = 1.25
ROLLING_DRAWDOWN_LOOKBACK = 63
DRAWDOWN_BRAKE_TRIGGER = -0.08
RECOVERY_CONFIRMATION_DAYS = 20

REPORT_COLUMNS = [
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
    "average_exposure",
    "max_exposure",
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

COST_COLUMNS = REPORT_COLUMNS + [
    "cost_bps",
    "financing_bps_annual",
    "cost_stress_cagr_pct",
    "cost_stress_calmar_ratio",
    "cost_sensitivity_label",
]

SPLIT_COLUMNS = REPORT_COLUMNS + [
    "split_name",
    "split_fraction",
    "split_start_date",
    "split_end_date",
    "split_sensitivity_label",
]

DRAWDOWN_COLUMNS = REPORT_COLUMNS + [
    "drawdown_start",
    "drawdown_trough",
    "drawdown_recovery",
    "drawdown_recovered",
    "drawdown_days",
]


@dataclass
class QqqAdaptiveLeverageLabResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq_adaptive_leverage_lab(root_dir: Path | str = ".") -> QqqAdaptiveLeverageLabResult:
    root = Path(root_dir)
    configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    price_data, data_errors = download_daily_price_data(["QQQ", "SPY"])
    variants = build_adaptive_variants(created_at, price_data, data_errors)
    report_rows = [build_adaptive_report_row(created_at, variant, "full_period") for variant in variants]
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
    return QqqAdaptiveLeverageLabResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        drawdown_rows=drawdown_rows,
        summary_lines=build_summary_lines(output_paths, report_rows, cost_rows, split_rows, data_errors),
    )


def show_qqq_adaptive_leverage_lab(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    report_path = root / OUTPUT_FILES["report"]
    if not summary_path.exists() or not report_path.exists():
        return 1, ["Run `python bot.py --qqq-adaptive-leverage-lab` first."]
    summary_rows = read_csv_rows(summary_path)
    report_rows = read_csv_rows(report_path)
    lines = ["QQQ ADAPTIVE LEVERAGE LAB SAVED DISPLAY. RESEARCH ONLY. NOT EXECUTION."]
    for row in summary_rows:
        lines.append(f"{row.get('summary_name')}: {row.get('summary_value')} - {row.get('details')}")
    best = best_candidate(report_rows)
    baseline = row_by_name(report_rows, "qqq_100_trend_gate")
    if best:
        lines.append(f"Best saved candidate: {best['variant_name']} Calmar={best['calmar_ratio']} Sharpe={best['sharpe_ratio']}")
    if baseline:
        lines.append(f"Saved qqq_100_trend_gate baseline: Calmar={baseline['calmar_ratio']} Sharpe={baseline['sharpe_ratio']}")
    lines.append("execution_approved=false; leverage_execution_approved=false; margin_approved=false; scheduling_approved=false")
    lines.append("Warning: saved display only; no Alpaca calls, order instructions, margin approval, leverage approval, or scheduling approval.")
    return 0, lines


def build_adaptive_variants(
    created_at: str,
    price_data: dict[str, list[dict[str, Any]]],
    data_errors: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    qqq_rows = price_data.get("QQQ", [])
    spy_rows = price_data.get("SPY", [])
    variants = [
        buy_and_hold_item("qqq_buy_and_hold", "QQQ buy-and-hold", qqq_rows),
        buy_and_hold_item("spy_buy_and_hold", "SPY buy-and-hold", spy_rows),
        simulate_trend_gate("qqq_100_trend_gate", 1.0, qqq_rows),
        simulate_trend_gate("qqq_125_trend_gate", 1.25, qqq_rows),
        simulate_trend_gate("qqq_150_trend_gate", 1.5, qqq_rows),
        simulate_adaptive_trend_exposure(qqq_rows),
        simulate_drawdown_brake_trend(qqq_rows),
        cash_item(qqq_rows),
    ]
    benchmark = next((row for row in variants if row["variant_name"] == "qqq_100_trend_gate"), variants[0])
    for variant in variants:
        variant["created_at"] = created_at
        apply_benchmark(variant, benchmark)
        add_exposure_fields(variant)
        if variant["data_status"] != "ok" and data_errors:
            variant["notes"] = variant["notes"] + " Data errors: " + "; ".join(f"{k}:{v}" for k, v in sorted(data_errors.items())[:2])
    apply_adaptive_decisions(variants)
    return variants


def simulate_adaptive_trend_exposure(qqq_rows: list[dict[str, Any]]) -> dict[str, Any]:
    name = "codex_qqq_adaptive_trend_exposure"
    if len(qqq_rows) < TREND_WINDOW + VOL_MEDIAN_LOOKBACK + 2:
        return insufficient_item(name, 1.5, "Missing usable QQQ daily history for volatility-gated adaptive exposure.")
    equity = STARTING_EQUITY
    curve = [{"date": qqq_rows[VOL_MEDIAN_LOOKBACK]["date"], "equity": equity, "invested": 0.0}]
    exposure_change_count = 0
    previous_exposure = 0.0
    for index in range(VOL_MEDIAN_LOOKBACK + 1, len(qqq_rows)):
        prev_close = qqq_rows[index - 1]["close"]
        close = qqq_rows[index]["close"]
        sma = average([row["close"] for row in qqq_rows[index - TREND_WINDOW : index]])
        vol = realised_volatility_pct(qqq_rows[index - VOL_LOOKBACK : index])
        median_vol = median([realised_volatility_pct(qqq_rows[start - VOL_LOOKBACK : start]) for start in range(index - VOL_MEDIAN_LOOKBACK + VOL_LOOKBACK, index)])
        if prev_close <= sma:
            exposure = 0.0
        elif vol >= median_vol * ELEVATED_VOL_MULTIPLE:
            exposure = 1.0
        elif vol <= median_vol * FAVOURABLE_VOL_MULTIPLE:
            exposure = 1.5
        else:
            exposure = 1.25
        if exposure != previous_exposure:
            exposure_change_count += 1
        equity = apply_daily_exposure(equity, prev_close, close, exposure, previous_exposure)
        curve.append({"date": qqq_rows[index]["date"], "equity": equity, "invested": exposure})
        previous_exposure = exposure
    return adaptive_item(
        name,
        curve,
        exposure_change_count,
        "cash below SMA200; 1.0x in elevated volatility; 1.25x in normal positive trend; 1.5x only when volatility is below 90% of its 252-day median.",
    )


def simulate_drawdown_brake_trend(qqq_rows: list[dict[str, Any]]) -> dict[str, Any]:
    name = "codex_qqq_drawdown_brake_trend"
    if len(qqq_rows) < TREND_WINDOW + ROLLING_DRAWDOWN_LOOKBACK + RECOVERY_CONFIRMATION_DAYS + 2:
        return insufficient_item(name, 1.25, "Missing usable QQQ daily history for drawdown-brake adaptive exposure.")
    equity = STARTING_EQUITY
    curve = [{"date": qqq_rows[TREND_WINDOW]["date"], "equity": equity, "invested": 0.0}]
    exposure_change_count = 0
    previous_exposure = 0.0
    brake_active = False
    recovery_count = 0
    for index in range(TREND_WINDOW + 1, len(qqq_rows)):
        prev_close = qqq_rows[index - 1]["close"]
        close = qqq_rows[index]["close"]
        sma = average([row["close"] for row in qqq_rows[index - TREND_WINDOW : index]])
        rolling_window = [row["close"] for row in qqq_rows[max(0, index - ROLLING_DRAWDOWN_LOOKBACK) : index]]
        rolling_dd = (prev_close / max(rolling_window) - 1.0) if rolling_window else 0.0
        trend_positive = prev_close > sma
        if rolling_dd <= DRAWDOWN_BRAKE_TRIGGER:
            brake_active = True
            recovery_count = 0
        if brake_active and trend_positive and prev_close > average([row["close"] for row in qqq_rows[index - RECOVERY_CONFIRMATION_DAYS : index]]):
            recovery_count += 1
        elif brake_active:
            recovery_count = 0
        if brake_active and recovery_count >= RECOVERY_CONFIRMATION_DAYS:
            brake_active = False
            recovery_count = 0
        if not trend_positive:
            exposure = 0.0
        elif brake_active:
            exposure = 0.75
        else:
            exposure = 1.25
        if exposure != previous_exposure:
            exposure_change_count += 1
        equity = apply_daily_exposure(equity, prev_close, close, exposure, previous_exposure)
        curve.append({"date": qqq_rows[index]["date"], "equity": equity, "invested": exposure})
        previous_exposure = exposure
    return adaptive_item(
        name,
        curve,
        exposure_change_count,
        "cash below SMA200; 1.25x in positive trend; reduce to 0.75x after an 8% rolling 63-day drawdown until 20-day recovery confirmation.",
    )


def adaptive_item(name: str, curve: list[dict[str, Any]], exposure_change_count: int, notes: str) -> dict[str, Any]:
    metrics = metrics_for_curve(curve)
    returns = daily_returns(curve)
    annual_vol = sample_stdev(returns) * (252.0**0.5) * 100.0 if returns else 0.0
    row = {
        "variant_name": name,
        "period": "full_period",
        "data_status": "ok",
        "leverage_multiple": 1.5,
        "curve": curve,
        "exposure_change_count": exposure_change_count,
        "turnover": round(sum(abs(float(curve[index]["invested"]) - float(curve[index - 1]["invested"])) for index in range(1, len(curve))), 4),
        "time_invested_pct": round(average([float(row.get("invested", 0.0)) > 0 for row in curve]) * 100.0, 4),
        "cash_time_pct": round(average([float(row.get("invested", 0.0)) <= 0 for row in curve]) * 100.0, 4),
        "annualised_volatility_pct": round(annual_vol, 4),
        "benchmark_name": "qqq_100_trend_gate",
        "benchmark_cagr_pct": "",
        "benchmark_sharpe_ratio": "",
        "benchmark_max_drawdown_pct": "",
        "benchmark_calmar_ratio": "",
        "decision_label": "synthetic_only_not_execution_ready",
        "notes": "Fixed Codex-designed adaptive QQQ research rule: " + notes,
        **metrics,
    }
    add_exposure_fields(row)
    return row


def add_exposure_fields(row: dict[str, Any]) -> None:
    curve = row.get("curve", [])
    exposures = [float(item.get("invested", 0.0)) for item in curve]
    row["average_exposure"] = round(average(exposures), 4) if exposures else 0.0
    row["max_exposure"] = round(max(exposures), 4) if exposures else 0.0
    if "turnover" not in row:
        row["turnover"] = round(sum(abs(exposures[index] - exposures[index - 1]) for index in range(1, len(exposures))), 4)


def apply_daily_exposure(equity: float, prev_close: float, close: float, exposure: float, previous_exposure: float) -> float:
    daily_return = (close / prev_close) - 1.0
    daily_financing = max(0.0, exposure - 1.0) * (300 / 10000.0) / 252.0
    daily_trade_cost = abs(exposure - previous_exposure) * (10 / 10000.0)
    return equity * (1.0 + (daily_return * exposure) - daily_financing - daily_trade_cost)


def apply_adaptive_decisions(variants: list[dict[str, Any]]) -> None:
    baseline = next((row for row in variants if row["variant_name"] == "qqq_100_trend_gate"), None)
    if baseline is None or baseline["data_status"] != "ok":
        return
    baseline_calmar = parse_float(baseline.get("calmar_ratio"))
    baseline_sharpe = parse_float(baseline.get("sharpe_ratio"))
    baseline_drawdown = abs(parse_float(baseline.get("max_drawdown_pct")))
    best = best_candidate(variants)
    for row in variants:
        if not is_lab_candidate(row) or row["data_status"] != "ok":
            continue
        if row["variant_name"] == "qqq_100_trend_gate":
            row["decision_label"] = "qqq_100_trend_gate_remains_lead" if best.get("variant_name") == "qqq_100_trend_gate" else "synthetic_only_not_execution_ready"
            continue
        calmar = parse_float(row.get("calmar_ratio"))
        sharpe = parse_float(row.get("sharpe_ratio"))
        drawdown = abs(parse_float(row.get("max_drawdown_pct")))
        if row["variant_name"].startswith("codex_") and calmar > baseline_calmar and sharpe >= baseline_sharpe and drawdown <= baseline_drawdown * 1.05:
            row["decision_label"] = "qqq_adaptive_research_lead"
        elif row["variant_name"].startswith("codex_") and calmar < baseline_calmar * 0.85:
            row["decision_label"] = "qqq_adaptive_rejected_return_drag"
        elif drawdown > baseline_drawdown * 1.20:
            row["decision_label"] = "qqq_adaptive_promising_but_high_drawdown"
        else:
            row["decision_label"] = "synthetic_only_not_execution_ready"


def build_adaptive_report_row(created_at: str, variant: dict[str, Any], period: str) -> dict[str, Any]:
    row = common_row(created_at, variant, period)
    row["average_exposure"] = variant.get("average_exposure", 0.0)
    row["max_exposure"] = variant.get("max_exposure", 0.0)
    return row


def build_cost_rows(created_at: str, variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for variant in variants:
        if not is_lab_candidate(variant):
            continue
        for cost_bps in TRANSACTION_COST_BPS:
            for financing_bps in FINANCING_BPS:
                stressed = stressed_metrics(variant, cost_bps, financing_bps)
                label = cost_sensitivity_label(variant, stressed)
                row = build_adaptive_report_row(created_at, {**variant, **stressed, "decision_label": label}, "full_period")
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
        if not is_lab_candidate(variant):
            continue
        base_calmar = parse_float(variant.get("calmar_ratio"))
        curve = variant.get("curve", [])
        for split_name, fraction in [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]:
            if len(curve) < 4:
                split_variant = {**variant, **metrics_for_curve([]), "decision_label": "insufficient_market_data"}
                split_curve = []
            else:
                split_index = max(1, min(len(curve) - 2, int(len(curve) * fraction)))
                split_curve = curve[split_index:]
                split_variant = {**variant, **metrics_for_curve(split_curve)}
                split_variant["annualised_volatility_pct"] = round(sample_stdev(daily_returns(split_curve)) * (252.0**0.5) * 100.0, 4)
                split_variant["decision_label"] = split_sensitivity_label(base_calmar, parse_float(split_variant.get("calmar_ratio")))
                add_exposure_fields(split_variant)
            row = build_adaptive_report_row(created_at, split_variant, "out_of_sample")
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
        if not is_lab_candidate(variant):
            continue
        row = build_adaptive_report_row(created_at, variant, "worst_drawdown_period")
        row.update(drawdown_window(variant.get("curve", [])))
        rows.append(row)
    return rows


def build_summary_rows(
    created_at: str,
    report_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    best = best_candidate(report_rows)
    baseline = row_by_name(report_rows, "qqq_100_trend_gate")
    adaptive_best = best_adaptive_candidate(report_rows)
    worst = min([row for row in report_rows if is_lab_candidate(row) and row.get("data_status") == "ok"], key=lambda row: parse_float(row.get("max_drawdown_pct")), default={})
    cost_sensitive = sorted({row["variant_name"] for row in cost_rows if row.get("cost_sensitivity_label") in {"qqq_adaptive_cost_sensitive", "qqq_adaptive_financing_sensitive"}})
    split_sensitive = sorted({row["variant_name"] for row in split_rows if row.get("split_sensitivity_label") == "qqq_adaptive_split_sensitive"})
    rejected = sorted({row["variant_name"] for row in report_rows if str(row.get("decision_label", "")).startswith("qqq_adaptive_rejected")})
    final = final_conclusion(best, baseline)
    entries = [
        ("best_adaptive_qqq_candidate", adaptive_best.get("variant_name", "none") if adaptive_best else "none", format_candidate(adaptive_best)),
        ("comparison_vs_qqq_100_trend_gate", best.get("variant_name", "none") if best else "none", comparison_details(best, baseline)),
        ("qqq_100_trend_gate_lead_status", "remains_lead" if final == "qqq_100_trend_gate_remains_lead" else "adaptive_or_other_review", final),
        ("worst_drawdown_warning", worst.get("variant_name", "none"), f"max_drawdown_pct={worst.get('max_drawdown_pct', '')}"),
        ("rejected_candidates", ", ".join(rejected) if rejected else "none", "Rejected labels are research-only and do not approve execution."),
        ("cost_financing_sensitivity_warning", ", ".join(cost_sensitive) if cost_sensitive else "none", "Placeholder costs only; not broker-specific financing terms."),
        ("split_sensitivity_warning", ", ".join(split_sensitive) if split_sensitive else "none", "Split weakness blocks any execution interpretation."),
        ("final_research_conclusion", final, "Research label only; execution, margin, leverage, and scheduling remain false."),
    ]
    return [summary_row(created_at, name, value, details) for name, value, details in entries]


def summary_row(created_at: str, name: str, value: str, details: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "summary_name": name,
        "summary_value": value,
        "details": details,
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


def cost_sensitivity_label(variant: dict[str, Any], stressed: dict[str, float]) -> str:
    calmar_drop = parse_float(variant.get("calmar_ratio")) - parse_float(stressed.get("calmar_ratio"))
    cagr_drop = parse_float(variant.get("cagr_pct")) - parse_float(stressed.get("cagr_pct"))
    if calmar_drop > 0.08:
        return "qqq_adaptive_cost_sensitive"
    if cagr_drop > 1.0 and parse_float(variant.get("max_exposure")) > 1.0:
        return "qqq_adaptive_financing_sensitive"
    return "synthetic_only_not_execution_ready"


def best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if is_lab_candidate(row) and row.get("data_status") == "ok"]
    return max(candidates, key=lambda row: (parse_float(row.get("calmar_ratio")), parse_float(row.get("sharpe_ratio"))), default={})


def best_adaptive_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if str(row.get("variant_name", "")).startswith("codex_") and row.get("data_status") == "ok"]
    return max(candidates, key=lambda row: (parse_float(row.get("calmar_ratio")), parse_float(row.get("sharpe_ratio"))), default={})


def row_by_name(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next((row for row in rows if row.get("variant_name") == name), {})


def final_conclusion(best: dict[str, Any], baseline: dict[str, Any]) -> str:
    if not best:
        return "insufficient_market_data"
    if best.get("variant_name") == "qqq_100_trend_gate":
        return "qqq_100_trend_gate_remains_lead"
    if str(best.get("variant_name", "")).startswith("codex_") and best.get("decision_label") == "qqq_adaptive_research_lead":
        return "qqq_adaptive_research_lead"
    if baseline and parse_float(best.get("calmar_ratio")) <= parse_float(baseline.get("calmar_ratio")):
        return "qqq_100_trend_gate_remains_lead"
    return "synthetic_only_not_execution_ready"


def is_lab_candidate(row: dict[str, Any]) -> bool:
    name = str(row.get("variant_name", ""))
    return (name.startswith("qqq_") and name.endswith("_trend_gate")) or name.startswith("codex_")


def format_candidate(row: dict[str, Any] | None) -> str:
    if not row:
        return "no usable candidate"
    return f"Calmar={row.get('calmar_ratio')}; Sharpe={row.get('sharpe_ratio')}; MaxDD={row.get('max_drawdown_pct')}; decision={row.get('decision_label')}"


def comparison_details(best: dict[str, Any], baseline: dict[str, Any]) -> str:
    if not best or not baseline:
        return "insufficient_market_data"
    return (
        f"best_calmar={best.get('calmar_ratio')}; baseline_calmar={baseline.get('calmar_ratio')}; "
        f"best_sharpe={best.get('sharpe_ratio')}; baseline_sharpe={baseline.get('sharpe_ratio')}; "
        f"best_max_drawdown={best.get('max_drawdown_pct')}; baseline_max_drawdown={baseline.get('max_drawdown_pct')}"
    )


def build_summary_lines(
    output_paths: dict[str, Path],
    report_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
) -> list[str]:
    best = best_candidate(report_rows)
    baseline = row_by_name(report_rows, "qqq_100_trend_gate")
    adaptive_best = best_adaptive_candidate(report_rows)
    worst = min([row for row in report_rows if is_lab_candidate(row) and row.get("data_status") == "ok"], key=lambda row: parse_float(row.get("max_drawdown_pct")), default={})
    cost_sensitive = sorted({row["variant_name"] for row in cost_rows if row.get("cost_sensitivity_label") in {"qqq_adaptive_cost_sensitive", "qqq_adaptive_financing_sensitive"}})
    split_sensitive = sorted({row["variant_name"] for row in split_rows if row.get("split_sensitivity_label") == "qqq_adaptive_split_sensitive"})
    final = final_conclusion(best, baseline)
    return [
        "QQQ ADAPTIVE LEVERAGE LAB. SYNTHETIC RESEARCH ONLY. NOT EXECUTION.",
        f"Saved report: {output_paths['report']}",
        f"Saved summary/costs/splits/drawdowns: {output_paths['summary']}; {output_paths['costs']}; {output_paths['splits']}; {output_paths['drawdowns']}",
        f"Best adaptive QQQ candidate: {adaptive_best.get('variant_name', 'none') if adaptive_best else 'none'} ({format_candidate(adaptive_best)})",
        f"Comparison versus qqq_100_trend_gate: {comparison_details(best, baseline)}",
        f"qqq_100_trend_gate lead status: {'remains lead' if final == 'qqq_100_trend_gate_remains_lead' else 'adaptive review'}",
        f"Worst drawdown warning: {worst.get('variant_name', 'none')} max_drawdown_pct={worst.get('max_drawdown_pct', '')}",
        f"Cost/financing sensitivity warning: {', '.join(cost_sensitive) if cost_sensitive else 'placeholder stress rows produced; no broker-specific claim'}",
        f"Split sensitivity warning: {', '.join(split_sensitive) if split_sensitive else 'none'}",
        f"Data issues: {len(data_errors)} ticker errors" if data_errors else "Data issues: none reported by yfinance",
        f"Final research conclusion: {final}.",
        "execution_approved=false; leverage_execution_approved=false; margin_approved=false; scheduling_approved=false",
        "No Alpaca commands, order instructions, margin approval, leverage approval, short approval, or scheduling approval are produced.",
    ]


def realised_volatility_pct(rows: list[dict[str, Any]]) -> float:
    returns = [(rows[index]["close"] / rows[index - 1]["close"]) - 1.0 for index in range(1, len(rows)) if rows[index - 1]["close"] > 0]
    return sample_stdev(returns) * (252.0**0.5) * 100.0 if returns else 0.0


def median(values: list[float]) -> float:
    clean = sorted(value for value in values if value >= 0)
    if not clean:
        return 0.0
    midpoint = len(clean) // 2
    if len(clean) % 2:
        return clean[midpoint]
    return (clean[midpoint - 1] + clean[midpoint]) / 2.0


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
