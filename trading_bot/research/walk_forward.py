"""Walk-forward report helpers.

This module reads existing research CSV outputs and compares in-sample rows
against out-of-sample rows. It does not call market data, Alpaca, Discord, or
SQLite, and it does not rerun backtests.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_bot.research.reporting import REPORT_INPUT_FILES, classify_strategy_role, read_research_file


WALK_FORWARD_COLUMNS = [
    "source_file",
    "strategy_name",
    "ticker_or_portfolio",
    "is_portfolio_level",
    "is_single_ticker",
    "is_benchmark",
    "is_active_strategy",
    "strategy_family",
    "walk_forward_view",
    "has_in_sample",
    "has_out_of_sample",
    "in_sample_cagr_pct",
    "out_of_sample_cagr_pct",
    "cagr_decay_pct",
    "in_sample_sharpe",
    "out_of_sample_sharpe",
    "sharpe_decay",
    "in_sample_calmar",
    "out_of_sample_calmar",
    "calmar_decay",
    "in_sample_max_drawdown_pct",
    "out_of_sample_max_drawdown_pct",
    "drawdown_worsening_pct",
    "robustness_label",
    "wf_active_rank_by_oos_cagr",
    "wf_active_rank_by_oos_sharpe",
    "wf_active_rank_by_oos_calmar",
    "wf_active_rank_by_drawdown",
    "wf_active_combined_rank_score",
    "notes",
]


@dataclass
class WalkForwardReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def generate_walk_forward_report(
    data_dir: Path | str = "data",
    output_filename: str = "walk_forward_report.csv",
) -> WalkForwardReportResult:
    data_path = Path(data_dir)
    warnings: list[str] = []
    source_rows: list[dict[str, Any]] = []

    for filename in REPORT_INPUT_FILES:
        input_path = data_path / filename
        if not input_path.exists():
            warnings.append(f"Missing research file: {input_path}")
            continue
        rows = read_research_file(input_path)
        if not rows:
            warnings.append(f"No usable rows in research file: {input_path}")
            continue
        source_rows.extend(rows)

    if not source_rows:
        raise RuntimeError("No usable research CSV files found for walk-forward report.")

    report_rows = build_walk_forward_rows(source_rows)
    output_path = data_path / output_filename
    write_walk_forward_report(output_path, report_rows)
    summary_lines = build_walk_forward_summary(report_rows)

    return WalkForwardReportResult(
        output_path=output_path,
        rows=report_rows,
        warnings=warnings,
        summary_lines=summary_lines,
    )


def build_walk_forward_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = {}
    for row in source_rows:
        key = (
            str(row.get("source_file", "")),
            str(row.get("strategy_name", "")),
            str(row.get("ticker_or_portfolio", "")),
        )
        period = str(row.get("period") or "full_period")
        grouped.setdefault(key, {})[period] = row

    report_rows = []
    for (source_file, strategy_name, ticker_or_portfolio), periods in sorted(grouped.items()):
        in_row = periods.get("in_sample")
        out_row = periods.get("out_of_sample")
        report_row = build_walk_forward_row(source_file, strategy_name, ticker_or_portfolio, in_row, out_row)
        report_rows.append(report_row)
    apply_walk_forward_active_ranks(report_rows)
    return report_rows


def build_walk_forward_row(
    source_file: str,
    strategy_name: str,
    ticker_or_portfolio: str,
    in_row: dict[str, Any] | None,
    out_row: dict[str, Any] | None,
) -> dict[str, Any]:
    has_in_sample = in_row is not None
    has_out_of_sample = out_row is not None
    is_portfolio_level = classify_portfolio_level(ticker_or_portfolio)
    role = classify_strategy_role(source_file, strategy_name)

    in_cagr = metric_from_row(in_row, "cagr_pct")
    out_cagr = metric_from_row(out_row, "cagr_pct")
    in_sharpe = metric_from_row(in_row, "sharpe_ratio")
    out_sharpe = metric_from_row(out_row, "sharpe_ratio")
    in_calmar = metric_from_row(in_row, "calmar_ratio")
    out_calmar = metric_from_row(out_row, "calmar_ratio")
    in_drawdown = metric_from_row(in_row, "max_drawdown_pct")
    out_drawdown = metric_from_row(out_row, "max_drawdown_pct")

    row = {
        "source_file": source_file,
        "strategy_name": strategy_name,
        "ticker_or_portfolio": ticker_or_portfolio,
        "is_portfolio_level": is_portfolio_level,
        "is_single_ticker": not is_portfolio_level,
        "is_benchmark": role["is_benchmark"],
        "is_active_strategy": role["is_active_strategy"],
        "strategy_family": role["strategy_family"],
        "walk_forward_view": walk_forward_view(is_portfolio_level, bool(role["is_benchmark"]), bool(role["is_active_strategy"]), has_in_sample and has_out_of_sample),
        "has_in_sample": has_in_sample,
        "has_out_of_sample": has_out_of_sample,
        "in_sample_cagr_pct": in_cagr,
        "out_of_sample_cagr_pct": out_cagr,
        "cagr_decay_pct": metric_difference(out_cagr, in_cagr),
        "in_sample_sharpe": in_sharpe,
        "out_of_sample_sharpe": out_sharpe,
        "sharpe_decay": metric_difference(out_sharpe, in_sharpe),
        "in_sample_calmar": in_calmar,
        "out_of_sample_calmar": out_calmar,
        "calmar_decay": metric_difference(out_calmar, in_calmar),
        "in_sample_max_drawdown_pct": in_drawdown,
        "out_of_sample_max_drawdown_pct": out_drawdown,
        "drawdown_worsening_pct": metric_difference(out_drawdown, in_drawdown),
        "robustness_label": "",
        "notes": "",
    }
    row["robustness_label"] = classify_robustness(row)
    row["notes"] = notes_for_robustness(row)
    return row


def classify_portfolio_level(ticker_or_portfolio: str) -> bool:
    return (ticker_or_portfolio or "").strip().lower() in {"", "portfolio", "all", "total", "universe"}


def walk_forward_view(
    is_portfolio_level: bool,
    is_benchmark: bool,
    is_active_strategy: bool,
    has_period_data: bool,
) -> str:
    if not has_period_data:
        return "insufficient_data"
    if is_portfolio_level and is_benchmark:
        return "portfolio_benchmark"
    if is_portfolio_level and is_active_strategy:
        return "portfolio_active"
    if not is_portfolio_level and is_benchmark:
        return "single_ticker_benchmark"
    if not is_portfolio_level and is_active_strategy:
        return "single_ticker_active"
    return "insufficient_data"


def metric_from_row(row: dict[str, Any] | None, key: str) -> float | str:
    if row is None:
        return ""
    value = row.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return ""


def metric_difference(value: Any, baseline: Any) -> float | str:
    if not isinstance(value, (int, float)) or not isinstance(baseline, (int, float)):
        return ""
    return round(float(value) - float(baseline), 4)


def classify_robustness(row: dict[str, Any]) -> str:
    if row.get("has_in_sample") is not True or row.get("has_out_of_sample") is not True:
        return "insufficient_period_data"

    out_cagr = row.get("out_of_sample_cagr_pct")
    cagr_decay = row.get("cagr_decay_pct")
    sharpe_decay = row.get("sharpe_decay")
    calmar_decay = row.get("calmar_decay")
    in_sharpe = row.get("in_sample_sharpe")
    out_sharpe = row.get("out_of_sample_sharpe")
    in_calmar = row.get("in_sample_calmar")
    out_calmar = row.get("out_of_sample_calmar")

    metrics = [out_cagr, cagr_decay, sharpe_decay, calmar_decay, in_sharpe, out_sharpe, in_calmar, out_calmar]
    if any(not isinstance(value, (int, float)) for value in metrics):
        return "insufficient_period_data"

    if float(out_cagr) < 0:
        return "out_of_sample_failure"

    # The difference fields use out-of-sample minus in-sample. Positive values
    # mean improvement, while negative values mean decay.
    improved_cagr = float(cagr_decay) >= 0
    improved_sharpe = float(sharpe_decay) >= 0
    improved_calmar = float(calmar_decay) >= 0
    if improved_cagr and improved_sharpe and improved_calmar:
        return "improved_out_of_sample"

    sharpe_collapse = float(in_sharpe) > 0 and float(out_sharpe) < (float(in_sharpe) * 0.5)
    calmar_collapse = float(in_calmar) > 0 and float(out_calmar) < (float(in_calmar) * 0.5)
    if float(cagr_decay) <= -10 or sharpe_collapse or calmar_collapse:
        return "severe_decay"

    close_cagr = abs(float(cagr_decay)) <= 3
    close_sharpe = abs(float(sharpe_decay)) <= 0.2
    close_calmar = abs(float(calmar_decay)) <= 0.2
    if close_cagr and close_sharpe and close_calmar:
        return "robust"

    if float(out_cagr) > 0:
        return "moderate_decay"
    return "out_of_sample_failure"


def apply_walk_forward_active_ranks(rows: list[dict[str, Any]]) -> None:
    active_rows = [
        row
        for row in rows
        if row.get("walk_forward_view") == "portfolio_active"
        and row.get("robustness_label") != "insufficient_period_data"
    ]
    assign_rank(active_rows, "out_of_sample_cagr_pct", "wf_active_rank_by_oos_cagr", higher_is_better=True)
    assign_rank(active_rows, "out_of_sample_sharpe", "wf_active_rank_by_oos_sharpe", higher_is_better=True)
    assign_rank(active_rows, "out_of_sample_calmar", "wf_active_rank_by_oos_calmar", higher_is_better=True)
    assign_rank(active_rows, "out_of_sample_max_drawdown_pct", "wf_active_rank_by_drawdown", higher_is_better=False)

    rank_keys = [
        "wf_active_rank_by_oos_cagr",
        "wf_active_rank_by_oos_sharpe",
        "wf_active_rank_by_oos_calmar",
        "wf_active_rank_by_drawdown",
    ]
    penalty = len(active_rows) + 1
    for row in rows:
        if row not in active_rows:
            for key in rank_keys:
                row[key] = ""
            row["wf_active_combined_rank_score"] = ""
            continue
        score = (
            rank_value(row, "wf_active_rank_by_oos_cagr", penalty)
            + rank_value(row, "wf_active_rank_by_oos_sharpe", penalty)
            + rank_value(row, "wf_active_rank_by_oos_calmar", penalty)
            + rank_value(row, "wf_active_rank_by_drawdown", penalty)
        )
        row["wf_active_combined_rank_score"] = round(score, 4)


def assign_rank(
    rows: list[dict[str, Any]],
    metric_key: str,
    rank_key: str,
    higher_is_better: bool,
) -> None:
    valid_rows = [row for row in rows if isinstance(row.get(metric_key), (int, float))]
    valid_rows.sort(
        key=lambda row: (
            -float(row[metric_key]) if higher_is_better else float(row[metric_key]),
            row.get("strategy_name", ""),
            row.get("ticker_or_portfolio", ""),
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


def notes_for_robustness(row: dict[str, Any]) -> str:
    label = row.get("robustness_label")
    if label == "improved_out_of_sample":
        return "Out-of-sample CAGR, Sharpe, and Calmar are equal to or better than in-sample."
    if label == "robust":
        return "Out-of-sample metrics are close to in-sample metrics."
    if label == "moderate_decay":
        return "Out-of-sample remains positive but weaker than in-sample."
    if label == "severe_decay":
        return "Out-of-sample risk-adjusted performance decayed heavily."
    if label == "out_of_sample_failure":
        return "Out-of-sample CAGR is negative."
    return "Missing in-sample or out-of-sample period data."


def write_walk_forward_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=WALK_FORWARD_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in WALK_FORWARD_COLUMNS})


def build_walk_forward_summary(rows: list[dict[str, Any]]) -> list[str]:
    portfolio_benchmarks = [row for row in rows if row.get("walk_forward_view") == "portfolio_benchmark"]
    portfolio_active = [row for row in rows if row.get("walk_forward_view") == "portfolio_active"]
    single_ticker_rows = [row for row in rows if str(row.get("walk_forward_view", "")).startswith("single_ticker_")]
    summary = [
        "Walk-forward report summary",
        "Research-only validation. Historical out-of-sample results do not imply future profits.",
        "Warning: single-ticker out-of-sample winners are diagnostics, not portfolio-level strategy approval.",
    ]
    add_best_line(summary, portfolio_benchmarks, "best portfolio benchmark by out-of-sample CAGR", "out_of_sample_cagr_pct")
    add_best_line(summary, portfolio_benchmarks, "best portfolio benchmark by out-of-sample Sharpe", "out_of_sample_sharpe")
    add_best_line(summary, portfolio_benchmarks, "best portfolio benchmark by out-of-sample Calmar", "out_of_sample_calmar")
    add_best_line(summary, portfolio_active, "best portfolio active by out-of-sample CAGR", "out_of_sample_cagr_pct")
    add_best_line(summary, portfolio_active, "best portfolio active by out-of-sample Sharpe", "out_of_sample_sharpe")
    add_best_line(summary, portfolio_active, "best portfolio active by out-of-sample Calmar", "out_of_sample_calmar")
    add_label_line(summary, portfolio_active, "robust portfolio active strategies", "robust")
    add_label_line(summary, portfolio_active, "moderate-decay portfolio active strategies", "moderate_decay")
    add_label_line(summary, portfolio_active, "severe-decay portfolio active strategies", "severe_decay")
    add_label_line(summary, portfolio_active, "out-of-sample-failure portfolio active strategies", "out_of_sample_failure")
    add_best_line(summary, single_ticker_rows, "single-ticker diagnostic best out-of-sample CAGR", "out_of_sample_cagr_pct")
    add_best_line(summary, single_ticker_rows, "single-ticker diagnostic best out-of-sample Sharpe", "out_of_sample_sharpe")
    add_best_line(summary, single_ticker_rows, "single-ticker diagnostic best out-of-sample Calmar", "out_of_sample_calmar")
    add_label_line(summary, rows, "insufficient period data", "insufficient_period_data")
    insufficient_names = {
        str(row.get("strategy_name", ""))
        for row in rows
        if row.get("robustness_label") == "insufficient_period_data"
    }
    missing_period_strategies = [
        name
        for name in ["monthly_etf_momentum_rotation", "adaptive_risk_on_off_momentum"]
        if name in insufficient_names
    ]
    if missing_period_strategies:
        summary.append(
            "Note: "
            + " and ".join(missing_period_strategies)
            + " currently have insufficient period data for walk-forward judgement unless their backtests are later split into in_sample/out_of_sample."
        )
    return summary


def add_best_line(summary: list[str], rows: list[dict[str, Any]], label: str, metric_key: str) -> None:
    valid_rows = [row for row in rows if isinstance(row.get(metric_key), (int, float))]
    if not valid_rows:
        summary.append(f"{label}: unavailable")
        return
    best = sorted(valid_rows, key=lambda row: -float(row[metric_key]))[0]
    summary.append(f"{label}: {label_for_row(best)} ({metric_key}={best[metric_key]})")


def add_label_line(summary: list[str], rows: list[dict[str, Any]], label: str, robustness_label: str) -> None:
    matches = [label_for_row(row) for row in rows if row.get("robustness_label") == robustness_label]
    if not matches:
        summary.append(f"{label}: none")
        return
    preview = ", ".join(matches[:5])
    if len(matches) > 5:
        preview += f", ... ({len(matches)} total)"
    summary.append(f"{label}: {preview}")


def label_for_row(row: dict[str, Any]) -> str:
    return f"{row.get('strategy_name', '')} [{row.get('ticker_or_portfolio', '')}]"
