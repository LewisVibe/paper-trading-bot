"""Saved strategy-result plotting helpers."""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def safe_chart_filename(strategy_name: str) -> str:
    safe = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in strategy_name
    )
    return safe.strip("_") or "strategy"


def load_portfolio_equity_curve_rows(csv_path: Path) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped_rows: dict[str, dict[str, list[dict[str, Any]]]] = {}

    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} was not found. Run python bot.py --compare-strategies first."
        )

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required_columns = {"date", "period", "strategy_name", "equity", "drawdown_pct"}
        if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
            raise ValueError(f"{csv_path} does not have the expected equity curve columns.")

        for row in reader:
            strategy_name = row["strategy_name"]
            period = row["period"]
            try:
                parsed_row = {
                    "date": datetime.fromisoformat(row["date"]),
                    "equity": float(row["equity"]),
                    "drawdown_pct": float(row["drawdown_pct"]),
                }
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{csv_path} contains an unreadable row: {row}") from exc

            grouped_rows.setdefault(strategy_name, {}).setdefault(period, []).append(parsed_row)

    for period_rows in grouped_rows.values():
        for rows in period_rows.values():
            rows.sort(key=lambda row: row["date"])

    return grouped_rows


def plot_strategy_results() -> int:
    portfolio_curve_path = Path("data/strategy_portfolio_equity_curves.csv")
    chart_dir = Path("data/charts")
    chart_dir.mkdir(parents=True, exist_ok=True)

    try:
        grouped_rows = load_portfolio_equity_curve_rows(portfolio_curve_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Plot error: {exc}", file=sys.stderr)
        return 2

    if not grouped_rows:
        print(
            "No portfolio equity curve rows were found. "
            "Run python bot.py --compare-strategies after market data is available."
        )
        return 0

    # Import matplotlib only for the optional plotting command so the normal bot
    # startup stays as lightweight and beginner-friendly as possible.
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "Plot error: matplotlib is not installed. "
            "Run python -m pip install -r requirements.txt, then try again.",
            file=sys.stderr,
        )
        return 2

    created_files: list[Path] = []
    for strategy_name, period_rows in sorted(grouped_rows.items()):
        figure, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
        figure.suptitle(f"{strategy_name} portfolio")

        for period, rows in sorted(period_rows.items()):
            dates = [row["date"] for row in rows]
            equities = [row["equity"] for row in rows]
            drawdowns = [-row["drawdown_pct"] for row in rows]
            axes[0].plot(dates, equities, label=period)
            axes[1].plot(dates, drawdowns, label=period)

        axes[0].set_ylabel("Equity")
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()

        axes[1].set_ylabel("Drawdown %")
        axes[1].set_xlabel("Date")
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()

        figure.autofmt_xdate()
        figure.tight_layout()

        output_path = chart_dir / f"{safe_chart_filename(strategy_name)}_portfolio.png"
        figure.savefig(output_path, dpi=140)
        plt.close(figure)
        created_files.append(output_path)

    print(f"Saved {len(created_files)} chart(s) to {chart_dir}")
    for path in created_files:
        print(path)
    return 0
