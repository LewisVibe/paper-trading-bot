"""Research-only crypto cost stress report helpers.

This module reruns the existing crypto strategy lab with fixed cost scenarios.
It does not add strategies, call Alpaca, read positions, create orders, write
SQLite, send Discord alerts, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research.crypto_lab import (
    CRYPTO_STRATEGIES,
    CRYPTO_SYMBOL_MAP,
    CryptoResearchCostModel,
    build_crypto_strategy_lab_outputs,
    download_crypto_daily_history,
)


CRYPTO_COST_STRESS_COLUMNS = [
    "created_at",
    "symbol",
    "strategy_name",
    "period",
    "cost_scenario",
    "crypto_total_one_way_cost_bps",
    "cagr_pct",
    "sharpe_ratio",
    "max_drawdown_pct",
    "calmar_ratio",
    "number_of_trades",
    "cagr_change_vs_default",
    "calmar_change_vs_default",
    "survives_cost_stress",
    "stress_status",
    "research_only",
    "preview_only",
    "execution_approved",
]

CRYPTO_COST_SCENARIOS = {
    "zero_cost": CryptoResearchCostModel(taker_fee_bps=0.0, spread_bps=0.0, slippage_bps=0.0, name="crypto_research_zero_cost"),
    "default_cost": CryptoResearchCostModel(taker_fee_bps=10.0, spread_bps=5.0, slippage_bps=10.0, name="crypto_research_default_cost"),
    "high_cost": CryptoResearchCostModel(taker_fee_bps=20.0, spread_bps=10.0, slippage_bps=20.0, name="crypto_research_high_cost"),
    "extreme_cost": CryptoResearchCostModel(taker_fee_bps=40.0, spread_bps=20.0, slippage_bps=40.0, name="crypto_research_extreme_cost"),
}


@dataclass
class CryptoCostStressReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_cost_stress_report(
    data_dir: Path | str = "data",
    output_filename: str = "crypto_cost_stress_report.csv",
) -> CryptoCostStressReportResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    price_data = {
        symbol: download_crypto_daily_history(data_symbol)
        for symbol, data_symbol in CRYPTO_SYMBOL_MAP.items()
    }
    rows = build_crypto_cost_stress_rows(price_data, created_at)
    output_path = data_path / output_filename
    write_crypto_cost_stress_report(output_path, rows)
    return CryptoCostStressReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_crypto_cost_stress_summary(rows),
    )


def build_crypto_cost_stress_rows(
    price_data: dict[str, list[dict[str, Any]]],
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    scenario_results: list[dict[str, Any]] = []
    for scenario_name, cost_model in CRYPTO_COST_SCENARIOS.items():
        result_rows, _trade_rows, _iteration_rows = build_crypto_strategy_lab_outputs(
            price_data,
            created_at=timestamp,
            cost_model=cost_model,
        )
        for row in result_rows:
            if row["strategy_name"] not in CRYPTO_STRATEGIES:
                continue
            scenario_results.append(build_base_stress_row(timestamp, scenario_name, row))

    default_rows = {
        stress_key(row): row
        for row in scenario_results
        if row["cost_scenario"] == "default_cost"
    }
    out_of_sample_status = build_out_of_sample_stress_status(scenario_results)
    rows = []
    for row in scenario_results:
        default_row = default_rows.get(stress_key(row))
        row["cagr_change_vs_default"] = metric_change(row, default_row, "cagr_pct")
        row["calmar_change_vs_default"] = metric_change(row, default_row, "calmar_ratio")
        row["survives_cost_stress"] = survives_cost_stress(row)
        row["stress_status"] = out_of_sample_status.get(
            (row["symbol"], row["strategy_name"]),
            classify_stress_status_from_rows([row]),
        )
        rows.append(row)
    return sorted(
        rows,
        key=lambda row: (
            row["symbol"],
            row["strategy_name"],
            period_sort_order(row["period"]),
            scenario_sort_order(row["cost_scenario"]),
        ),
    )


def build_base_stress_row(created_at: str, scenario_name: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "symbol": row["symbol"],
        "strategy_name": row["strategy_name"],
        "period": row["period"],
        "cost_scenario": scenario_name,
        "crypto_total_one_way_cost_bps": row["crypto_total_one_way_cost_bps"],
        "cagr_pct": row["cagr_pct"],
        "sharpe_ratio": row["sharpe_ratio"],
        "max_drawdown_pct": row["max_drawdown_pct"],
        "calmar_ratio": row["calmar_ratio"],
        "number_of_trades": row["number_of_trades"],
        "cagr_change_vs_default": "",
        "calmar_change_vs_default": "",
        "survives_cost_stress": False,
        "stress_status": "",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_out_of_sample_stress_status(rows: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if row["period"] != "out_of_sample":
            continue
        grouped.setdefault((row["symbol"], row["strategy_name"]), []).append(row)
    return {
        key: classify_stress_status_from_rows(group_rows)
        for key, group_rows in grouped.items()
    }


def classify_stress_status_from_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "insufficient_data"
    by_scenario = {row["cost_scenario"]: row for row in rows}
    high_survives = survives_cost_stress(by_scenario.get("high_cost"))
    extreme_survives = survives_cost_stress(by_scenario.get("extreme_cost"))
    if high_survives and extreme_survives:
        return "robust_to_costs"
    if high_survives and not extreme_survives:
        return "sensitive_to_costs"
    if "high_cost" in by_scenario or "extreme_cost" in by_scenario:
        return "fails_high_costs"
    return "insufficient_data"


def survives_cost_stress(row: dict[str, Any] | None) -> bool:
    if row is None:
        return False
    cagr = row.get("cagr_pct")
    calmar = row.get("calmar_ratio")
    return isinstance(cagr, (int, float)) and isinstance(calmar, (int, float)) and float(cagr) > 0 and float(calmar) > 0.25


def metric_change(row: dict[str, Any], default_row: dict[str, Any] | None, metric_key: str) -> float | str:
    if default_row is None:
        return ""
    value = row.get(metric_key)
    default_value = default_row.get(metric_key)
    if not isinstance(value, (int, float)) or not isinstance(default_value, (int, float)):
        return ""
    return round(float(value) - float(default_value), 4)


def stress_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (row["symbol"], row["strategy_name"], row["period"])


def write_crypto_cost_stress_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CRYPTO_COST_STRESS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CRYPTO_COST_STRESS_COLUMNS})


def build_crypto_cost_stress_summary(rows: list[dict[str, Any]]) -> list[str]:
    robust = sorted({
        f"{row['symbol']}:{row['strategy_name']}"
        for row in rows
        if row["period"] == "out_of_sample" and row["stress_status"] == "robust_to_costs"
    })
    return [
        "CRYPTO COST STRESS REPORT. RESEARCH ONLY. NOT EXECUTION.",
        best_line(rows, "BTC/USD", "default_cost", "Best BTC strategy under default cost by out-of-sample Calmar"),
        best_line(rows, "BTC/USD", "high_cost", "Best BTC strategy under high cost by out-of-sample Calmar"),
        best_line(rows, "ETH/USD", "default_cost", "Best ETH strategy under default cost by out-of-sample Calmar"),
        best_line(rows, "ETH/USD", "high_cost", "Best ETH strategy under high cost by out-of-sample Calmar"),
        "Robust under high/extreme costs: " + (", ".join(robust) if robust else "none"),
        "Warning: crypto cost stress is not execution approval.",
    ]


def best_line(rows: list[dict[str, Any]], symbol: str, scenario: str, label: str) -> str:
    matches = [
        row
        for row in rows
        if row["symbol"] == symbol
        and row["cost_scenario"] == scenario
        and row["period"] == "out_of_sample"
        and isinstance(row.get("calmar_ratio"), (int, float))
    ]
    if not matches:
        return f"{label}: unavailable"
    best = sorted(matches, key=lambda row: (-float(row["calmar_ratio"]), row["strategy_name"]))[0]
    return f"{label}: {best['strategy_name']} (calmar_ratio={best['calmar_ratio']})"


def period_sort_order(period: str) -> int:
    return {"full_period": 0, "in_sample": 1, "out_of_sample": 2}.get(period, 99)


def scenario_sort_order(scenario: str) -> int:
    return {"zero_cost": 0, "default_cost": 1, "high_cost": 2, "extreme_cost": 3}.get(scenario, 99)
