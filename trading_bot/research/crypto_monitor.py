"""Read-only terminal monitor for saved crypto research previews.

This command only reads saved CSV files. It does not refresh market data, call
Alpaca, read positions, create orders, write SQLite, send Discord alerts, or
approve execution.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def show_crypto_monitor_file(
    data_dir: Path | str = "data",
) -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    signal_path = data_path / "crypto_signal_preview.csv"
    if not signal_path.exists():
        return 1, build_missing_crypto_monitor_lines(signal_path)

    signal_rows = read_csv_rows(signal_path)
    decision_rows = read_optional_csv_rows(data_path / "crypto_strategy_decision_report.csv")
    robustness_rows = read_optional_csv_rows(data_path / "crypto_robustness_report.csv")
    diagnostic_rows = read_optional_csv_rows(data_path / "crypto_period_diagnostics.csv")
    return 0, build_crypto_monitor_lines(
        signal_path,
        signal_rows,
        decision_rows,
        robustness_rows,
        diagnostic_rows,
    )


def build_missing_crypto_monitor_lines(signal_path: Path) -> list[str]:
    return [
        "CRYPTO MONITOR. READ-ONLY. NOT EXECUTION.",
        "This command only reads saved crypto CSVs and does not refresh data or submit orders.",
        f"Missing input file: {signal_path}",
        "Run this first:",
        "python bot.py --preview-crypto-signals",
    ]


def build_crypto_monitor_lines(
    signal_path: Path,
    signal_rows: list[dict[str, str]],
    decision_rows: list[dict[str, str]],
    robustness_rows: list[dict[str, str]],
    diagnostic_rows: list[dict[str, str]],
) -> list[str]:
    decision_by_symbol = {row.get("symbol", ""): row for row in decision_rows}
    robustness_by_symbol_strategy = summarize_robustness(robustness_rows)
    diagnostics_by_symbol_strategy = summarize_diagnostics(diagnostic_rows)

    lines = [
        "CRYPTO MONITOR. READ-ONLY. NOT EXECUTION.",
        "This command only reads saved crypto CSVs and does not refresh data or submit orders.",
        f"Input file: {signal_path}",
        f"Rows: {len(signal_rows)}",
        "",
        "Symbol | Candidate | Desired | Close | SMA200 | Above SMA200 | Vol Gate | Decision | Robustness | Execution Approved | Reason",
        "-" * 160,
    ]
    for row in signal_rows:
        symbol = row.get("symbol", "")
        strategy_name = row.get("strategy_name", "")
        decision = decision_by_symbol.get(symbol, {})
        robustness = robustness_by_symbol_strategy.get((symbol, strategy_name), "not available")
        diagnostic = diagnostics_by_symbol_strategy.get((symbol, strategy_name), "")
        reason = row.get("signal_reason", "")
        if diagnostic:
            reason = f"{reason} Diagnostic: {diagnostic}"
        lines.append(
            " | ".join(
                [
                    symbol,
                    strategy_name,
                    row.get("desired_position", ""),
                    row.get("latest_close", ""),
                    row.get("sma_200", ""),
                    row.get("close_above_sma_200", ""),
                    value_or_not_applicable(row.get("vol_gate_passed", "")),
                    decision.get("decision_status", "not available"),
                    robustness,
                    "False",
                    reason,
                ]
            )
        )

    lines.extend(
        [
            "",
            "Execution approved: False for all rows.",
            "Warning: crypto monitor is read-only and not execution approval.",
        ]
    )
    return lines


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [row for row in reader if any((value or "").strip() for value in row.values())]


def read_optional_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv_rows(path)


def summarize_robustness(rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    grouped: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        key = (row.get("symbol", ""), row.get("strategy_name", ""))
        if not all(key):
            continue
        status = row.get("robustness_status", "") or "not available"
        grouped.setdefault(key, set()).add(status)
    return {
        key: ", ".join(sorted(values))
        for key, values in grouped.items()
    }


def summarize_diagnostics(rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    grouped: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        key = (row.get("symbol", ""), row.get("strategy_name", ""))
        label = row.get("diagnostic_label", "")
        if not all(key) or not label:
            continue
        grouped.setdefault(key, set()).add(label)
    return {
        key: ", ".join(sorted(values))
        for key, values in grouped.items()
    }


def value_or_not_applicable(value: Any) -> str:
    value_text = str(value)
    return value_text if value_text not in {"", "None"} else "n/a"
