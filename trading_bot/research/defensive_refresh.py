"""Research-only defensive report refresh orchestration."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from trading_bot.research.defensive_comparison import generate_defensive_candidate_comparison
from trading_bot.research.etf_defensive_charts import plot_etf_defensive_comparison_charts
from trading_bot.research.etf_defensive_drawdowns import generate_etf_defensive_drawdown_comparison
from trading_bot.research.etf_rotation_robustness import generate_etf_rotation_robustness_report


DEFENSIVE_REFRESH_COLUMNS = [
    "created_at",
    "step_name",
    "command_or_report",
    "status",
    "output_path",
    "message",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class DefensiveRefreshResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def refresh_defensive_research(
    data_dir: Path | str = "data",
    output_filename: str = "defensive_research_refresh_summary.csv",
    steps: list[tuple[str, str, Callable[[], Any]]] | None = None,
) -> DefensiveRefreshResult:
    data_path = Path(data_dir)
    timestamp = datetime.now(timezone.utc).isoformat()
    refresh_steps = steps or default_defensive_refresh_steps(data_path)
    rows: list[dict[str, Any]] = []
    for step_name, command_or_report, step in refresh_steps:
        rows.append(run_refresh_step(timestamp, step_name, command_or_report, step))
    output_path = data_path / output_filename
    write_defensive_refresh_summary(output_path, rows)
    return DefensiveRefreshResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_defensive_refresh_summary(rows, output_path),
    )


def default_defensive_refresh_steps(data_path: Path) -> list[tuple[str, str, Callable[[], Any]]]:
    return [
        (
            "etf_rotation_robustness",
            "python bot.py --etf-rotation-robustness",
            lambda: generate_etf_rotation_robustness_report(data_dir=data_path),
        ),
        (
            "vol_managed_etf_robustness",
            "python bot.py --vol-managed-etf-robustness",
            lambda: require_saved_file(
                data_path / "vol_managed_etf_robustness_report.csv",
                "Use the existing saved vol-managed robustness report; rerun python bot.py --vol-managed-etf-robustness separately only when market-data refresh is intended.",
            ),
        ),
        (
            "defensive_candidate_comparison",
            "python bot.py --defensive-candidate-comparison",
            lambda: generate_defensive_candidate_comparison(data_dir=data_path),
        ),
        (
            "etf_defensive_drawdown_comparison",
            "python bot.py --etf-defensive-drawdown-comparison",
            lambda: generate_etf_defensive_drawdown_comparison(data_dir=data_path),
        ),
        (
            "plot_etf_defensive_comparison",
            "python bot.py --plot-etf-defensive-comparison",
            lambda: plot_etf_defensive_comparison_charts(data_dir=data_path),
        ),
    ]


def run_refresh_step(
    created_at: str,
    step_name: str,
    command_or_report: str,
    step: Callable[[], Any],
) -> dict[str, Any]:
    try:
        result = step()
    except Exception as exc:
        return refresh_row(
            created_at,
            step_name,
            command_or_report,
            "failed",
            "",
            clear_failure_message(exc),
        )
    return refresh_row(
        created_at,
        step_name,
        command_or_report,
        "passed",
        output_paths_for_result(result),
        "Refreshed from saved research CSV inputs.",
    )


def refresh_row(
    created_at: str,
    step_name: str,
    command_or_report: str,
    status: str,
    output_path: str,
    message: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "step_name": step_name,
        "command_or_report": command_or_report,
        "status": status,
        "output_path": output_path,
        "message": message,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def output_paths_for_result(result: Any) -> str:
    if hasattr(result, "output_path"):
        return str(result.output_path)
    if hasattr(result, "chart_paths"):
        return "; ".join(str(path) for path in result.chart_paths)
    return ""


@dataclass
class SavedFileRefreshResult:
    output_path: Path
    summary_lines: list[str]


def require_saved_file(path: Path, message: str) -> SavedFileRefreshResult:
    if not path.exists():
        raise RuntimeError(f"Missing required saved report: {path}. {message}")
    return SavedFileRefreshResult(output_path=path, summary_lines=[message])


def clear_failure_message(exc: Exception) -> str:
    message = str(exc)
    if "Missing" in message or "missing" in message:
        return (
            f"{message} Refresh saved inputs first as needed: python bot.py --etf-rotation-backtest; "
            "python bot.py --vol-managed-etf-backtest; python bot.py --etf-rotation-robustness; "
            "python bot.py --vol-managed-etf-robustness."
        )
    return message


def write_defensive_refresh_summary(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEFENSIVE_REFRESH_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEFENSIVE_REFRESH_COLUMNS})


def build_defensive_refresh_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    lines = [
        "DEFENSIVE RESEARCH REFRESH. RESEARCH ONLY. NOT EXECUTION.",
        "This command refreshes saved defensive reports/charts only and does not approve execution.",
    ]
    for row in rows:
        output = f" -> {row['output_path']}" if row.get("output_path") else ""
        lines.append(f"{row['step_name']}: {row['status']}{output}")
        if row.get("status") != "passed":
            lines.append(f"  {row['message']}")
    lines.append(f"Saved defensive research refresh summary to {output_path}")
    lines.append("Warning: research_only=True, preview_only=True, and execution_approved=False for every row.")
    return lines
