"""Split and drawdown-window validation for the Codex ambitious candidate.

This module is research/report-only. It uses existing ETF research simulation
helpers, writes generated CSV reports, and never touches broker, position,
SQLite, alert, scheduler, config, or execution paths.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location
from trading_bot.research.growth_biased_stricter_persistence_filter import (
    CODEX_AMBITIOUS_STRATEGY,
    PERSISTENCE_VARIANTS,
    simulate_persistence_strategy,
)
from trading_bot.research.strategy_improvement_lab import (
    ALL_ETFS,
    build_result_row,
    download_daily_price_data,
    align_price_rows,
    simulate_strategy,
)


TARGET_STRATEGY_NAME = "codex_ambitious_concentrated_growth_persistence"
TARGET_STRATEGY = CODEX_AMBITIOUS_STRATEGY
SPY_BENCHMARK = "spy_buy_and_hold_benchmark"
MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"
EQUAL_WEIGHT_BENCHMARK = "equal_weight_etf_buy_and_hold_benchmark"
PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"
STRICTER_GATE = "growth_biased_rotation_breadth_stricter_gate"
SPLITS = [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]
LEAD_CHANGE_LABELS = [
    "codex_ambitious_new_active_research_lead",
    "codex_ambitious_active_lead_candidate_needs_cost_review",
    "codex_ambitious_split_sensitive",
    "codex_ambitious_drawdown_concentrated_review",
    "codex_ambitious_not_ready_for_lead_change",
    "insufficient_saved_inputs",
    "manual_review_required",
]

OUTPUT_FILES = {
    "validation": Path("data/codex_ambitious_split_drawdown_validation.csv"),
    "splits": Path("data/codex_ambitious_split_validation.csv"),
    "drawdowns": Path("data/codex_ambitious_drawdown_windows.csv"),
    "checkpoint": Path("data/codex_ambitious_lead_change_checkpoint.csv"),
}

SAVED_COST_INPUT = Path("data/codex_ambitious_validation_costs.csv")

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "validation_area",
    "check_name",
    "strategy_name",
    "comparison_strategy",
    "split_name",
    "period",
    "metric_name",
    "metric_value",
    "reference_value",
    "metric_delta",
    "status",
    "severity",
    "evidence",
    "interpretation",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "promotion_approved",
    "scheduling_approved",
]


@dataclass
class SplitDrawdownValidationResult:
    validation_path: Path
    splits_path: Path
    drawdowns_path: Path
    checkpoint_path: Path
    validation_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    checkpoint_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_codex_ambitious_split_drawdown_validation(data_dir: Path | str = "data") -> SplitDrawdownValidationResult:
    root = Path(".")
    data_path = Path(data_dir)
    configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    price_data, data_errors = download_daily_price_data(ALL_ETFS)
    aligned_rows = align_price_rows(price_data)
    saved_cost_rows = read_csv(data_path / SAVED_COST_INPUT.name)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}

    if not aligned_rows:
        validation_rows, split_rows, drawdown_rows, checkpoint_rows = insufficient_outputs(created_at, data_errors)
    else:
        equity_by_strategy, trades_by_strategy = simulate_validation_universe(created_at, aligned_rows)
        split_rows = build_split_rows(created_at, equity_by_strategy, trades_by_strategy)
        drawdown_rows = build_drawdown_rows(created_at, equity_by_strategy)
        checkpoint_rows = [build_checkpoint_row(created_at, split_rows, drawdown_rows, saved_cost_rows)]
        validation_rows = build_validation_rows(created_at, split_rows, drawdown_rows, checkpoint_rows, saved_cost_rows)

    write_rows(output_paths["validation"], validation_rows)
    write_rows(output_paths["splits"], split_rows)
    write_rows(output_paths["drawdowns"], drawdown_rows)
    write_rows(output_paths["checkpoint"], checkpoint_rows)
    return SplitDrawdownValidationResult(
        validation_path=output_paths["validation"],
        splits_path=output_paths["splits"],
        drawdowns_path=output_paths["drawdowns"],
        checkpoint_path=output_paths["checkpoint"],
        validation_rows=validation_rows,
        split_rows=split_rows,
        drawdown_rows=drawdown_rows,
        checkpoint_rows=checkpoint_rows,
        summary_lines=build_summary_lines(checkpoint_rows, split_rows, drawdown_rows, output_paths),
    )


def simulate_validation_universe(
    created_at: str,
    aligned_rows: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    strategies = [
        SPY_BENCHMARK,
        EQUAL_WEIGHT_BENCHMARK,
        MONTHLY_ROTATION_REFERENCE,
        PREVIOUS_RESEARCH_LEAD,
        STRICTER_GATE,
    ]
    equity_by_strategy: dict[str, list[dict[str, Any]]] = {}
    trades_by_strategy: dict[str, list[dict[str, Any]]] = {}
    for strategy in strategies:
        equity_rows, trade_rows = simulate_strategy(strategy, aligned_rows, created_at)
        equity_by_strategy[strategy] = equity_rows
        trades_by_strategy[strategy] = trade_rows
    target_equity, target_trades = simulate_persistence_strategy(
        TARGET_STRATEGY,
        PERSISTENCE_VARIANTS[TARGET_STRATEGY],
        aligned_rows,
        created_at,
    )
    equity_by_strategy[TARGET_STRATEGY] = target_equity
    trades_by_strategy[TARGET_STRATEGY] = target_trades
    return equity_by_strategy, trades_by_strategy


def build_split_rows(
    created_at: str,
    equity_by_strategy: dict[str, list[dict[str, Any]]],
    trades_by_strategy: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    target_equity = equity_by_strategy[TARGET_STRATEGY]
    for split_name, fraction in SPLITS:
        split_index = max(2, int(len(target_equity) * fraction))
        target_oos = target_equity[split_index - 1 :]
        target_metrics = build_result_row(created_at, TARGET_STRATEGY, split_name, target_oos, trades_by_strategy[TARGET_STRATEGY])
        reference_metrics = {
            strategy: build_result_row(
                created_at,
                strategy,
                split_name,
                equity_by_strategy[strategy][split_index - 1 :],
                trades_by_strategy[strategy],
            )
            for strategy in [SPY_BENCHMARK, STRICTER_GATE, PREVIOUS_RESEARCH_LEAD, MONTHLY_ROTATION_REFERENCE, EQUAL_WEIGHT_BENCHMARK]
        }
        wins = count_metric_wins(target_metrics, reference_metrics)
        status = split_status(wins, target_metrics)
        rows.append(
            report_row(
                created_at,
                "split_validation",
                f"{split_name}_oos_result",
                split_name=split_name,
                period="out_of_sample",
                metric_name="cagr_sharpe_calmar_maxdd_cash_turnover",
                metric_value=format_split_metrics(target_metrics),
                reference_value=format_reference_deltas(target_metrics, reference_metrics),
                metric_delta=f"wins={wins['wins']}/{wins['total']}",
                status=status,
                severity="pass" if status == "split_credible" else "review_required",
                evidence=f"{split_name}: {format_split_metrics(target_metrics)}; {format_reference_deltas(target_metrics, reference_metrics)}.",
                interpretation="A split can be credible without beating SPY in every metric.",
                required_next_step="Review split consistency before research-lead change.",
            )
        )
    return rows


def build_drawdown_rows(created_at: str, equity_by_strategy: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    target_window = worst_drawdown_window(equity_by_strategy[TARGET_STRATEGY])
    overlap_end = target_window["recovery_date"] or target_window["trough_date"]
    spy_overlap = window_drawdown(equity_by_strategy[SPY_BENCHMARK], target_window["start_date"], overlap_end)
    stricter_overlap = window_drawdown(equity_by_strategy[STRICTER_GATE], target_window["start_date"], overlap_end)
    status = drawdown_status(target_window, spy_overlap, stricter_overlap)
    return [
        report_row(
            created_at,
            "drawdown_window",
            "worst_drawdown_window",
            metric_name="max_drawdown_pct",
            metric_value=round(target_window["max_drawdown_pct"], 4),
            reference_value=format_drawdown_references(spy_overlap, stricter_overlap),
            metric_delta=format_drawdown_deltas(target_window["max_drawdown_pct"], spy_overlap, stricter_overlap),
            status=status,
            severity="pass" if status == "drawdown_acceptable_for_return" else "review_required",
            evidence=(
                f"start={target_window['start_date']}; trough={target_window['trough_date']}; "
                f"recovery={target_window['recovery_date'] or 'not_recovered'}; recovery_rows={target_window['recovery_rows']}; "
                f"recovery_days={target_window['recovery_days']}; overlap_end={overlap_end}; "
                f"regime={regime_label(target_window['start_date'], target_window['trough_date'])}."
            ),
            interpretation="Drawdown window is research risk context only, not execution approval.",
            required_next_step="Review whether the drawdown concentration is acceptable for an ambitious lead.",
        )
    ]


def build_checkpoint_row(
    created_at: str,
    split_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
    saved_cost_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    credible_splits = sum(1 for row in split_rows if row.get("status") == "split_credible")
    broken_splits = sum(1 for row in split_rows if row.get("status") == "split_broken")
    drawdown_status_value = drawdown_rows[0].get("status", "manual_review_required") if drawdown_rows else "manual_review_required"
    survives_10 = any(row.get("cost_level_bps") == "10" and row.get("status") == "cost_survives" for row in saved_cost_rows)
    if credible_splits >= 2 and drawdown_status_value != "drawdown_catastrophic_review" and survives_10:
        label = "codex_ambitious_new_active_research_lead"
    elif credible_splits >= 2 and survives_10:
        label = "codex_ambitious_active_lead_candidate_needs_cost_review"
    elif broken_splits >= 2:
        label = "codex_ambitious_split_sensitive"
    elif drawdown_status_value != "drawdown_acceptable_for_return":
        label = "codex_ambitious_drawdown_concentrated_review"
    else:
        label = "manual_review_required"
    return report_row(
        created_at,
        "lead_change_checkpoint",
        "final_lead_change_label",
        metric_name="lead_change_label",
        metric_value=label,
        status=label,
        severity="pass" if label == "codex_ambitious_new_active_research_lead" else "review_required",
        evidence=(
            f"credible_splits={credible_splits}/3; broken_splits={broken_splits}/3; "
            f"drawdown_status={drawdown_status_value}; survives_10_bps={survives_10}."
        ),
        interpretation="New active research lead is a research label only and does not approve preview promotion or execution.",
        required_next_step=required_next_step(label),
    )


def build_validation_rows(
    created_at: str,
    split_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
    checkpoint_rows: list[dict[str, Any]],
    saved_cost_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cost_ack = report_row(
        created_at,
        "cost_acknowledgement",
        "existing_cost_survival",
        metric_name="survives_10_bps",
        metric_value=any(row.get("cost_level_bps") == "10" and row.get("status") == "cost_survives" for row in saved_cost_rows),
        status="cost_acknowledged",
        severity="review_required",
        evidence="Existing Codex ambitious validation cost rows are acknowledged; this report focuses on splits and drawdown windows.",
        interpretation="Surviving 10 bps supports research-lead discussion but does not approve execution.",
    )
    return [*split_rows, *drawdown_rows, cost_ack, *checkpoint_rows]


def insufficient_outputs(created_at: str, data_errors: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    evidence = "; ".join(f"{ticker}: {error}" for ticker, error in sorted(data_errors.items())[:8]) or "No aligned daily data."
    row = report_row(
        created_at,
        "lead_change_checkpoint",
        "missing_saved_inputs",
        status="insufficient_saved_inputs",
        severity="insufficient_data",
        evidence=evidence,
        interpretation="Split/drawdown validation requires research price data but does not call any broker or execution path.",
        required_next_step="Rerun when yfinance/cache market data is available; do not approve execution.",
    )
    return [row], [row], [row], [row]


def show_codex_ambitious_split_drawdown_validation_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    validation = read_csv(data_path / OUTPUT_FILES["validation"].name)
    splits = read_csv(data_path / OUTPUT_FILES["splits"].name)
    drawdowns = read_csv(data_path / OUTPUT_FILES["drawdowns"].name)
    checkpoint = read_csv(data_path / OUTPUT_FILES["checkpoint"].name)
    if not validation or not checkpoint:
        return 1, ["Run `python bot.py --codex-ambitious-split-drawdown-validation` first."]
    final = checkpoint[0]
    drawdown = drawdowns[0] if drawdowns else {}
    approval_values = {str(row.get("execution_approved", "")).lower() for row in validation + splits + drawdowns + checkpoint}
    return 0, [
        "Codex ambitious split/drawdown validation. Display only; execution_approved=False.",
        f"Final lead-change label: {final.get('status', 'insufficient_saved_inputs')}",
        f"split_60_40 result: {split_line(splits, 'split_60_40')}",
        f"split_70_30 result: {split_line(splits, 'split_70_30')}",
        f"split_80_20 result: {split_line(splits, 'split_80_20')}",
        f"Worst drawdown start/trough/recovery: {drawdown.get('evidence', 'unavailable')}",
        f"Drawdown comparison: {drawdown.get('reference_value', 'unavailable')}",
        f"Lead-change outcome: {final.get('metric_value', final.get('status', ''))}",
        f"Required next review step: {final.get('required_next_step', '')}",
        f"execution_approved values: {', '.join(sorted(approval_values)) or 'false'}",
        "Warning: saved split/drawdown validation does not approve orders, preview promotion, scheduling, or execution.",
    ]


def build_summary_lines(
    checkpoint_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
    output_paths: dict[str, Path],
) -> list[str]:
    checkpoint = checkpoint_rows[0] if checkpoint_rows else {}
    drawdown = drawdown_rows[0] if drawdown_rows else {}
    return [
        "Codex ambitious split/drawdown validation complete. Research/report only; execution_approved=False.",
        f"Final lead-change label: {checkpoint.get('status', 'insufficient_saved_inputs')}",
        f"split_60_40 result: {split_line(split_rows, 'split_60_40')}",
        f"split_70_30 result: {split_line(split_rows, 'split_70_30')}",
        f"split_80_20 result: {split_line(split_rows, 'split_80_20')}",
        f"Worst drawdown summary: {drawdown.get('evidence', 'unavailable')}",
        f"Saved validation to {output_paths['validation']}",
        f"Saved split validation to {output_paths['splits']}",
        f"Saved drawdown windows to {output_paths['drawdowns']}",
        f"Saved lead checkpoint to {output_paths['checkpoint']}",
        "Warning: validation does not approve orders, paper execution, preview promotion, scheduling, or strategy-to-execution wiring.",
    ]


def worst_drawdown_window(equity_rows: list[dict[str, Any]]) -> dict[str, Any]:
    peak_value = float(equity_rows[0]["equity"])
    peak_date = str(equity_rows[0]["date"])
    peak_index = 0
    worst = 0.0
    worst_peak_value = peak_value
    worst_peak_date = peak_date
    worst_peak_index = peak_index
    trough_date = peak_date
    recovery_date = ""
    trough_index = 0
    for index, row in enumerate(equity_rows):
        value = float(row["equity"])
        if value > peak_value:
            peak_value = value
            peak_date = str(row["date"])
            peak_index = index
        drawdown = ((value / peak_value) - 1.0) * 100.0
        if drawdown < worst:
            worst = drawdown
            worst_peak_value = peak_value
            worst_peak_date = peak_date
            worst_peak_index = peak_index
            trough_date = str(row["date"])
            trough_index = index
            recovery_date = ""
            for later in equity_rows[index + 1 :]:
                if float(later["equity"]) >= worst_peak_value:
                    recovery_date = str(later["date"])
                    break
    recovery_rows = 0
    recovery_days: int | str = ""
    if recovery_date:
        recovery_rows = next((i for i, row in enumerate(equity_rows[trough_index:], start=0) if str(row["date"]) == recovery_date), 0)
        recovery_days = max(0, date_delta_days(trough_date, recovery_date))
    return {
        "start_date": worst_peak_date,
        "start_index": worst_peak_index,
        "trough_date": trough_date,
        "trough_index": trough_index,
        "recovery_date": recovery_date,
        "recovery_rows": recovery_rows if recovery_date else "",
        "recovery_days": recovery_days,
        "max_drawdown_pct": worst,
    }


def window_drawdown(equity_rows: list[dict[str, Any]], start_date: str, end_date: str) -> float | None:
    window = [row for row in equity_rows if start_date <= str(row["date"]) <= end_date]
    if len(window) < 2:
        return None
    peak = float(window[0]["equity"])
    worst = 0.0
    for row in window:
        value = float(row["equity"])
        if value > peak:
            peak = value
        if peak <= 0:
            return None
        worst = min(worst, ((value / peak) - 1.0) * 100.0)
    return worst


def count_metric_wins(target: dict[str, Any], references: dict[str, dict[str, Any]]) -> dict[str, int]:
    wins = 0
    total = 0
    for reference in references.values():
        for metric in ["cagr_pct", "sharpe_ratio", "calmar_ratio"]:
            total += 1
            if as_float(target.get(metric)) >= as_float(reference.get(metric)):
                wins += 1
    return {"wins": wins, "total": total}


def split_status(wins: dict[str, int], target: dict[str, Any]) -> str:
    if wins["total"] <= 0:
        return "insufficient_saved_inputs"
    if as_float(target.get("cagr_pct")) <= 0 or as_float(target.get("calmar_ratio")) <= 0:
        return "split_broken"
    if wins["wins"] >= wins["total"] / 2:
        return "split_credible"
    return "split_mixed_review"


def drawdown_status(target: dict[str, Any], spy_overlap: float | None, stricter_overlap: float | None) -> str:
    if spy_overlap is None or stricter_overlap is None:
        return "drawdown_comparison_unavailable"
    if target["max_drawdown_pct"] < spy_overlap - 15 and target["max_drawdown_pct"] < stricter_overlap - 10:
        return "drawdown_catastrophic_review"
    if target["max_drawdown_pct"] < spy_overlap - 5:
        return "drawdown_concentrated_review"
    return "drawdown_acceptable_for_return"


def report_row(
    created_at: str,
    validation_area: str,
    check_name: str,
    *,
    comparison_strategy: str = "",
    split_name: str = "",
    period: str = "",
    metric_name: Any = "",
    metric_value: Any = "",
    reference_value: Any = "",
    metric_delta: Any = "",
    status: str,
    severity: str,
    evidence: str,
    interpretation: str,
    required_next_step: str = "Manual research review only; do not connect to execution.",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "codex_ambitious_split_drawdown_validation",
        "validation_area": validation_area,
        "check_name": check_name,
        "strategy_name": TARGET_STRATEGY,
        "comparison_strategy": comparison_strategy,
        "split_name": split_name,
        "period": period,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "reference_value": reference_value,
        "metric_delta": metric_delta,
        "status": status,
        "severity": severity,
        "evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "promotion_approved": False,
        "scheduling_approved": False,
    }


def format_split_metrics(row: dict[str, Any]) -> str:
    return (
        f"CAGR={row.get('cagr_pct', '')}; Sharpe={row.get('sharpe_ratio', '')}; "
        f"MaxDD={row.get('max_drawdown_pct', '')}; Calmar={row.get('calmar_ratio', '')}; "
        f"cash={row.get('average_cash_weight_pct', '')}; trades={row.get('trade_count', '')}; turnover={row.get('turnover', '')}"
    )


def format_reference_deltas(target: dict[str, Any], references: dict[str, dict[str, Any]]) -> str:
    parts = []
    for name, reference in references.items():
        parts.append(
            f"{name}: cagr_delta={round(as_float(target.get('cagr_pct')) - as_float(reference.get('cagr_pct')), 4)}, "
            f"calmar_delta={round(as_float(target.get('calmar_ratio')) - as_float(reference.get('calmar_ratio')), 4)}"
        )
    return "; ".join(parts)


def format_drawdown_references(spy_overlap: float | None, stricter_overlap: float | None) -> str:
    return f"spy_overlap={format_optional_pct(spy_overlap)}; stricter_overlap={format_optional_pct(stricter_overlap)}"


def format_drawdown_deltas(target_drawdown: float, spy_overlap: float | None, stricter_overlap: float | None) -> str:
    spy_delta = "unavailable" if spy_overlap is None else round(target_drawdown - spy_overlap, 4)
    stricter_delta = "unavailable" if stricter_overlap is None else round(target_drawdown - stricter_overlap, 4)
    return f"vs_spy={spy_delta}; vs_stricter={stricter_delta}"


def format_optional_pct(value: float | None) -> str:
    return "unavailable" if value is None else str(round(value, 4))


def date_delta_days(start_date: str, end_date: str) -> int:
    try:
        start = datetime.fromisoformat(start_date[:10])
        end = datetime.fromisoformat(end_date[:10])
    except ValueError:
        return 0
    return (end - start).days


def regime_label(start_date: str, trough_date: str) -> str:
    if start_date[:4] in {"2020", "2022"} or trough_date[:4] in {"2020", "2022"}:
        return "known_bear_or_shock_window"
    return "general_market_window"


def required_next_step(label: str) -> str:
    if label == "codex_ambitious_new_active_research_lead":
        return "Update docs only after manual review; execution and preview promotion remain unapproved."
    if label == "codex_ambitious_active_lead_candidate_needs_cost_review":
        return "Review cost sensitivity before declaring active research lead."
    if label == "codex_ambitious_split_sensitive":
        return "Investigate split dependence before lead change."
    if label == "codex_ambitious_drawdown_concentrated_review":
        return "Review drawdown concentration versus SPY and stricter gate before lead change."
    return "Manual review required; do not connect to execution."


def split_line(rows: list[dict[str, Any]], split_name: str) -> str:
    row = next((item for item in rows if item.get("split_name") == split_name), None)
    if not row:
        return "unavailable"
    return f"{row.get('status')}: {row.get('metric_value')}"


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMMON_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
