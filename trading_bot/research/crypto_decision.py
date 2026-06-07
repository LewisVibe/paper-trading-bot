"""Research-only crypto strategy decision report helpers.

This module reads saved crypto research CSV files and produces a symbol-level
decision report. It does not refresh data, call Alpaca, read positions, create
orders, write SQLite, send Discord alerts, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CRYPTO_DECISION_COLUMNS = [
    "created_at",
    "symbol",
    "best_full_period_strategy",
    "best_oos_strategy",
    "best_oos_calmar",
    "best_oos_sharpe",
    "best_oos_cagr_pct",
    "beats_buy_and_hold_oos",
    "drawdown_reduction_oos_pct",
    "decision_status",
    "decision_reason",
    "next_research_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoStrategyDecisionReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_strategy_decision_report(
    data_dir: Path | str = "data",
    lab_filename: str = "crypto_strategy_lab_results.csv",
    report_filename: str = "crypto_strategy_report.csv",
    output_filename: str = "crypto_strategy_decision_report.csv",
) -> CryptoStrategyDecisionReportResult:
    data_path = Path(data_dir)
    lab_path = data_path / lab_filename
    report_path = data_path / report_filename
    if not lab_path.exists():
        raise RuntimeError(f"Missing required crypto strategy lab results: {lab_path}")
    if not report_path.exists():
        raise RuntimeError(f"Missing required crypto strategy report: {report_path}")

    lab_rows = read_csv_rows(lab_path)
    report_rows = read_csv_rows(report_path)
    if not lab_rows:
        raise RuntimeError(f"No usable rows in required crypto strategy lab results: {lab_path}")
    if not report_rows:
        raise RuntimeError(f"No usable rows in required crypto strategy report: {report_path}")

    rows = build_crypto_strategy_decision_rows(lab_rows, report_rows)
    output_path = data_path / output_filename
    write_crypto_strategy_decision_report(output_path, rows)
    return CryptoStrategyDecisionReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_crypto_strategy_decision_summary(rows),
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


def build_crypto_strategy_decision_rows(
    lab_rows: list[dict[str, str]],
    report_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    created_at = datetime.now(timezone.utc).isoformat()
    symbols = sorted({row.get("symbol", "") for row in lab_rows if row.get("symbol", "")})
    return [
        build_crypto_strategy_decision_row(
            created_at,
            symbol,
            [row for row in report_rows if row.get("symbol") == symbol],
        )
        for symbol in symbols
    ]


def build_crypto_strategy_decision_row(
    created_at: str,
    symbol: str,
    report_rows: list[dict[str, str]],
) -> dict[str, Any]:
    full_rows = [normalize_report_row(row) for row in report_rows if row.get("period") == "full_period"]
    oos_rows = [normalize_report_row(row) for row in report_rows if row.get("period") == "out_of_sample"]
    best_full = best_by_calmar(full_rows)
    best_oos = best_by_calmar(oos_rows)

    if best_oos is None:
        status, reason, next_step = (
            "insufficient_data",
            "Missing out-of-sample crypto strategy report rows.",
            "Run the crypto strategy lab and report before making a research decision.",
        )
    else:
        status, reason, next_step = classify_crypto_decision(best_oos, best_full)

    return {
        "created_at": created_at,
        "symbol": symbol,
        "best_full_period_strategy": best_full.get("strategy_name", "") if best_full else "",
        "best_oos_strategy": best_oos.get("strategy_name", "") if best_oos else "",
        "best_oos_calmar": best_oos.get("calmar_ratio", "") if best_oos else "",
        "best_oos_sharpe": best_oos.get("sharpe_ratio", "") if best_oos else "",
        "best_oos_cagr_pct": best_oos.get("cagr_pct", "") if best_oos else "",
        "beats_buy_and_hold_oos": best_oos.get("beats_buy_and_hold", "") if best_oos else "",
        "drawdown_reduction_oos_pct": best_oos.get("drawdown_reduction_vs_buy_and_hold_pct", "") if best_oos else "",
        "decision_status": status,
        "decision_reason": reason,
        "next_research_step": next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def normalize_report_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "strategy_name": row.get("strategy_name", ""),
        "symbol": row.get("symbol", ""),
        "period": row.get("period", ""),
        "cagr_pct": number_or_blank(row.get("cagr_pct", "")),
        "sharpe_ratio": number_or_blank(row.get("sharpe_ratio", "")),
        "max_drawdown_pct": number_or_blank(row.get("max_drawdown_pct", "")),
        "calmar_ratio": number_or_blank(row.get("calmar_ratio", "")),
        "trade_count": number_or_blank(row.get("trade_count", "")),
        "beats_buy_and_hold": bool_or_blank(row.get("beats_buy_and_hold", "")),
        "drawdown_reduction_vs_buy_and_hold_pct": number_or_blank(row.get("drawdown_reduction_vs_buy_and_hold_pct", "")),
        "cagr_gap_vs_buy_and_hold_pct": number_or_blank(row.get("cagr_gap_vs_buy_and_hold_pct", "")),
    }


def best_by_calmar(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid_rows = [row for row in rows if isinstance(row.get("calmar_ratio"), (int, float))]
    if not valid_rows:
        return None
    return sorted(
        valid_rows,
        key=lambda row: (
            -float(row["calmar_ratio"]),
            -float(row["sharpe_ratio"]) if isinstance(row.get("sharpe_ratio"), (int, float)) else 0,
            row["strategy_name"],
        ),
    )[0]


def classify_crypto_decision(
    best_oos: dict[str, Any],
    best_full: dict[str, Any] | None,
) -> tuple[str, str, str]:
    cagr_gap = best_oos.get("cagr_gap_vs_buy_and_hold_pct")
    drawdown_reduction = best_oos.get("drawdown_reduction_vs_buy_and_hold_pct")
    calmar = best_oos.get("calmar_ratio")
    sharpe = best_oos.get("sharpe_ratio")
    beats_benchmark = best_oos.get("beats_buy_and_hold") is True

    if not all(isinstance(value, (int, float)) for value in [cagr_gap, drawdown_reduction, calmar, sharpe]):
        return (
            "insufficient_data",
            "Missing numeric out-of-sample comparison metrics.",
            "Regenerate crypto strategy lab and report outputs.",
        )

    full_strategy = best_full.get("strategy_name", "") if best_full else ""
    if best_full and full_strategy != best_oos.get("strategy_name") and not beats_benchmark:
        return (
            "inconclusive",
            "Best full-period strategy differs from best out-of-sample strategy and the out-of-sample winner does not beat buy-and-hold.",
            "Keep researching with fixed rules; do not add execution.",
        )

    if beats_benchmark and float(drawdown_reduction) > 0 and float(calmar) >= 0.4:
        return (
            "strongest_research_candidate",
            "Best out-of-sample strategy beats buy-and-hold and reduces drawdown.",
            "Continue research with more out-of-sample checks before any execution discussion.",
        )

    if float(drawdown_reduction) > 0 and float(calmar) >= 0.25 and float(sharpe) > 0:
        if float(cagr_gap) <= -20:
            return (
                "inconclusive",
                "Out-of-sample drawdown improves but CAGR drag versus buy-and-hold is large.",
                "Review whether defensive value justifies the return drag.",
            )
        return (
            "research_watchlist",
            "Out-of-sample drawdown or risk-adjusted profile is interesting, but buy-and-hold is not clearly beaten.",
            "Keep on research watchlist; do not add execution.",
        )

    if float(calmar) <= 0 or float(sharpe) <= 0:
        return (
            "not_useful",
            "Out-of-sample risk-adjusted metrics are weak.",
            "Do not continue this crypto strategy without new evidence.",
        )

    return (
        "inconclusive",
        "Out-of-sample results are mixed and do not justify a stronger research status.",
        "Keep as research only and compare after more validation.",
    )


def write_crypto_strategy_decision_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CRYPTO_DECISION_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CRYPTO_DECISION_COLUMNS})


def build_crypto_strategy_decision_summary(rows: list[dict[str, Any]]) -> list[str]:
    return [
        "CRYPTO STRATEGY DECISION REPORT. RESEARCH ONLY. NOT EXECUTION.",
        candidate_line(rows, "BTC/USD", "Best BTC research candidate"),
        candidate_line(rows, "ETH/USD", "Best ETH research candidate"),
        "Decision status by symbol: " + ", ".join(f"{row['symbol']}={row['decision_status']}" for row in rows),
        "Warning: crypto research is not execution approval.",
    ]


def candidate_line(rows: list[dict[str, Any]], symbol: str, label: str) -> str:
    match = next((row for row in rows if row.get("symbol") == symbol), None)
    if match is None:
        return f"{label}: unavailable"
    return f"{label}: {match['best_oos_strategy']} ({match['decision_status']})"


def number_or_blank(value: Any) -> float | str:
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def bool_or_blank(value: Any) -> bool | str:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return ""
