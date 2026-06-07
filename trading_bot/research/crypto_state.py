"""Saved-data-only crypto research state report.

This checkpoint report combines existing crypto research CSVs. It does not
refresh market data, call Alpaca, read positions, create orders, write SQLite,
send Discord alerts, add symbols, add strategies, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CRYPTO_RESEARCH_STATE_SYMBOLS = ["BTC/USD", "ETH/USD", "LTC/USD"]
CRYPTO_RESEARCH_STATE_COLUMNS = [
    "created_at",
    "symbol",
    "data_symbol",
    "universe_status",
    "best_research_candidate",
    "decision_status",
    "current_desired_position",
    "current_signal_reason",
    "robustness_summary",
    "all_strategy_robustness_statuses",
    "cost_stress_summary",
    "all_strategy_cost_statuses",
    "period_diagnostic_summary",
    "research_conclusion",
    "next_research_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoResearchStateReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_research_state_report(
    data_dir: Path | str = "data",
    output_filename: str = "crypto_research_state_report.csv",
) -> CryptoResearchStateReportResult:
    data_path = Path(data_dir)
    inputs = {
        "preview": read_optional_csv_rows(data_path / "crypto_research_preview.csv"),
        "strategy_report": read_optional_csv_rows(data_path / "crypto_strategy_report.csv"),
        "decision": read_optional_csv_rows(data_path / "crypto_strategy_decision_report.csv"),
        "cost_stress": read_optional_csv_rows(data_path / "crypto_cost_stress_report.csv"),
        "robustness": read_optional_csv_rows(data_path / "crypto_robustness_report.csv"),
        "diagnostics": read_optional_csv_rows(data_path / "crypto_period_diagnostics.csv"),
        "signals": read_optional_csv_rows(data_path / "crypto_signal_preview.csv"),
    }
    rows = build_crypto_research_state_rows(inputs)
    output_path = data_path / output_filename
    write_crypto_research_state_report(output_path, rows)
    return CryptoResearchStateReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_crypto_research_state_summary(rows, data_path / "crypto_signal_preview.csv", output_path),
    )


def build_crypto_research_state_rows(
    inputs: dict[str, list[dict[str, str]]],
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    preview_by_symbol = {row.get("symbol", ""): row for row in inputs.get("preview", [])}
    decision_by_symbol = {row.get("symbol", ""): row for row in inputs.get("decision", [])}
    signal_by_symbol = {row.get("symbol", ""): row for row in inputs.get("signals", [])}
    all_robustness_by_symbol = summarize_statuses(inputs.get("robustness", []), "symbol", "robustness_status")
    all_cost_by_symbol = summarize_statuses(inputs.get("cost_stress", []), "symbol", "stress_status")
    robustness_by_candidate = summarize_statuses_by_symbol_and_strategy(
        inputs.get("robustness", []),
        "robustness_status",
    )
    cost_by_candidate = summarize_statuses_by_symbol_and_strategy(
        inputs.get("cost_stress", []),
        "stress_status",
    )
    diagnostics_by_symbol = summarize_statuses(inputs.get("diagnostics", []), "symbol", "diagnostic_label")

    rows: list[dict[str, Any]] = []
    for symbol in CRYPTO_RESEARCH_STATE_SYMBOLS:
        decision_row = decision_by_symbol.get(symbol, {})
        signal_row = signal_by_symbol.get(symbol, {})
        best_candidate = best_research_candidate_for_state(decision_row, signal_row)
        rows.append(
            build_symbol_state_row(
                timestamp,
                symbol,
                preview_by_symbol.get(symbol, {}),
                decision_row,
                signal_row,
                robustness_by_candidate.get((symbol, best_candidate), "not_available"),
                all_robustness_by_symbol.get(symbol, "not_available"),
                cost_by_candidate.get((symbol, best_candidate), "not_available"),
                all_cost_by_symbol.get(symbol, "not_available"),
                diagnostics_by_symbol.get(symbol, "not_available"),
            )
        )
    return rows


def build_symbol_state_row(
    created_at: str,
    symbol: str,
    preview_row: dict[str, str],
    decision_row: dict[str, str],
    signal_row: dict[str, str],
    robustness_summary: str,
    all_strategy_robustness_statuses: str,
    cost_stress_summary: str,
    all_strategy_cost_statuses: str,
    period_diagnostic_summary: str,
) -> dict[str, Any]:
    decision_status = decision_row.get("decision_status", "not_available") or "not_available"
    best_candidate = best_research_candidate_for_state(decision_row, signal_row)
    current_desired_position = signal_row.get("desired_position", "not_available") or "not_available"
    current_signal_reason = signal_row.get("signal_reason", "not_available") or "not_available"
    conclusion, next_step = crypto_research_conclusion(symbol, decision_status, current_desired_position)
    return {
        "created_at": created_at,
        "symbol": symbol,
        "data_symbol": symbol.replace("/", "-"),
        "universe_status": preview_row.get("research_status", "not_available") or "not_available",
        "best_research_candidate": best_candidate,
        "decision_status": decision_status,
        "current_desired_position": current_desired_position,
        "current_signal_reason": current_signal_reason,
        "robustness_summary": robustness_summary,
        "all_strategy_robustness_statuses": all_strategy_robustness_statuses,
        "cost_stress_summary": cost_stress_summary,
        "all_strategy_cost_statuses": all_strategy_cost_statuses,
        "period_diagnostic_summary": period_diagnostic_summary,
        "research_conclusion": conclusion,
        "next_research_step": decision_row.get("next_research_step") or next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def crypto_research_conclusion(
    symbol: str,
    decision_status: str,
    current_desired_position: str,
) -> tuple[str, str]:
    if decision_status == "not_useful":
        return (
            "researched_but_not_useful_pause",
            f"Pause {symbol} unless new evidence appears.",
        )
    if decision_status == "strongest_research_candidate":
        return (
            "useful_but_research_only_keep_monitoring",
            "Keep monitoring; no execution approval.",
        )
    if decision_status in {"research_watchlist", "inconclusive"}:
        return (
            "useful_but_split_sensitive_keep_monitoring",
            "Keep monitoring split-sensitive research; no execution.",
        )
    if decision_status in {"insufficient_data", "not_available"}:
        return (
            "insufficient_or_missing_research_data",
            "Regenerate crypto research reports before adding decisions.",
        )
    if current_desired_position == "flat":
        return (
            "research_only_currently_flat",
            "Keep monitoring; no execution approval.",
        )
    return (
        "research_only_no_execution_approval",
        "Keep as research only; no execution approval.",
    )


def best_research_candidate_for_state(
    decision_row: dict[str, str],
    signal_row: dict[str, str],
) -> str:
    return (
        decision_row.get("best_oos_strategy")
        or signal_row.get("strategy_name")
        or "not_available"
    )


def summarize_statuses(rows: list[dict[str, str]], symbol_key: str, status_key: str) -> dict[str, str]:
    grouped: dict[str, set[str]] = {}
    for row in rows:
        symbol = row.get(symbol_key, "")
        status = row.get(status_key, "")
        if not symbol or not status:
            continue
        grouped.setdefault(symbol, set()).add(status)
    return {
        symbol: ", ".join(sorted(statuses))
        for symbol, statuses in grouped.items()
    }


def summarize_statuses_by_symbol_and_strategy(
    rows: list[dict[str, str]],
    status_key: str,
) -> dict[tuple[str, str], str]:
    grouped: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        symbol = row.get("symbol", "")
        strategy_name = row.get("strategy_name", "")
        status = row.get(status_key, "")
        if not symbol or not strategy_name or not status:
            continue
        grouped.setdefault((symbol, strategy_name), set()).add(status)
    return {
        key: ", ".join(sorted(statuses))
        for key, statuses in grouped.items()
    }


def write_crypto_research_state_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CRYPTO_RESEARCH_STATE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CRYPTO_RESEARCH_STATE_COLUMNS})


def build_crypto_research_state_summary(
    rows: list[dict[str, Any]],
    signal_path: Path,
    output_path: Path,
) -> list[str]:
    paused = [
        row["symbol"]
        for row in rows
        if row.get("decision_status") == "not_useful"
        or "pause" in str(row.get("research_conclusion", ""))
    ]
    lines = [
        "CRYPTO RESEARCH STATE REPORT. RESEARCH ONLY. NOT EXECUTION.",
        "Current symbol conclusions:",
    ]
    lines.extend(
        f"- {row['symbol']}: {row['research_conclusion']} ({row['current_desired_position']})"
        for row in rows
    )
    lines.append(
        "Current signal summary: "
        + ", ".join(f"{row['symbol']}={row['current_desired_position']}" for row in rows)
    )
    lines.append("Symbols paused or not useful: " + (", ".join(paused) if paused else "none"))
    if any(row.get("current_desired_position") == "not_available" for row in rows):
        lines.append(f"Missing signal preview data; run: python bot.py --preview-crypto-signals ({signal_path})")
    lines.extend(
        [
            "Warning: no crypto execution approval.",
            f"Saved crypto research state report to {output_path}",
        ]
    )
    return lines


def read_optional_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [row for row in reader if any((value or "").strip() for value in row.values())]
