"""Saved-output-only reconstruction of the QQQ100 benchmark inputs.

This report documents the likely source and assumptions behind the saved
QQQ100 benchmark metrics. It does not refresh market data, call Alpaca, read
positions, create orders, write SQLite, send alerts, schedule anything, or
approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BENCHMARK_NAME = "qqq_100_trend_gate"
SAVED_CAGR = "16.8429"
SAVED_SHARPE = "1.0027"
SAVED_MAXDD = "-23.4576"
SAVED_CALMAR = "0.718"
RECOVERED_SOURCE_STATUS = "source_partially_recovered"
CONFIDENCE_LEVEL = "medium_confidence_source_code_recovered_daily_stream_missing"
REQUIRED_NEXT_STEP = "recover_or_regenerate_original_qqq_leverage_validation_daily_stream_before_updating_stream_generation"
SOURCE_STATUS_LABELS = [
    "source_partially_recovered",
    "source_not_recovered_constants_only",
    "benchmark_definition_unknown",
]

OUTPUT_FILES = {
    "report": Path("data/qqq100_benchmark_inputs_report.csv"),
    "summary": Path("data/qqq100_benchmark_inputs_summary.csv"),
    "gaps": Path("data/qqq100_benchmark_input_gaps.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "preview_only",
    "report_only",
    "saved_output_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": True,
    "report_only": True,
    "saved_output_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "live_position_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

REPORT_COLUMNS = [
    "created_at",
    "benchmark_name",
    "saved_CAGR",
    "saved_Sharpe",
    "saved_MaxDD",
    "saved_Calmar",
    "recovered_source_status",
    "likely_strategy_source",
    "likely_data_source",
    "likely_date_range",
    "likely_signal_timing",
    "likely_price_field",
    "likely_adjustment_status",
    "likely_warmup_rule",
    "likely_cost_assumption",
    "likely_cash_handling",
    "likely_metric_method",
    "likely_annualisation",
    "confidence_level",
    "unresolved_gap",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_COLUMNS,
]

GAP_COLUMNS = [
    "created_at",
    "gap_name",
    "gap_status",
    "evidence",
    "impact",
    "required_next_step",
    *SAFETY_COLUMNS,
]


@dataclass
class QQQ100BenchmarkInputsResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    gap_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_benchmark_inputs_report(root_dir: Path | str = ".") -> QQQ100BenchmarkInputsResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report_rows = [build_report_row(created_at)]
    gap_rows = build_gap_rows(created_at)
    summary_rows = build_summary_rows(created_at, report_rows[0], gap_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["gaps"], GAP_COLUMNS, gap_rows)
    return QQQ100BenchmarkInputsResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        gap_rows=gap_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["report"]),
    )


def show_qqq100_benchmark_inputs(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "QQQ100 benchmark inputs report is missing.",
            "Run `python bot.py --qqq100-benchmark-inputs-report` first.",
            "execution_approved=false; scheduling_approved=false",
        ]
    summary = {row.get("summary_name", ""): row.get("summary_value", "") for row in read_csv_rows(path)}
    return 0, [
        "QQQ100 benchmark inputs. Saved-output-only research; no execution wiring approved.",
        f"saved benchmark metrics: {summary.get('saved_benchmark_metrics', 'missing')}",
        f"recovered source status: {summary.get('recovered_source_status', 'missing')}",
        f"likely original parameter set: {summary.get('likely_original_parameter_set', 'missing')}",
        f"confidence level: {summary.get('confidence_level', 'missing')}",
        f"unresolved gaps: {summary.get('unresolved_gaps', 'missing')}",
        f"required next step: {summary.get('required_next_step', 'missing')}",
        "execution_approved=false; scheduling_approved=false",
    ]


def build_report_row(created_at: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "benchmark_name": BENCHMARK_NAME,
        "saved_CAGR": SAVED_CAGR,
        "saved_Sharpe": SAVED_SHARPE,
        "saved_MaxDD": SAVED_MAXDD,
        "saved_Calmar": SAVED_CALMAR,
        "recovered_source_status": RECOVERED_SOURCE_STATUS,
        "likely_strategy_source": (
            "fa1d63d:trading_bot/research/qqq_leverage_validation.py;"
            " ae0ab7f:trading_bot/research/qqq_lead_decision.py;"
            " 4aebc22:trading_bot/research/project_research_state_refresh.py"
        ),
        "likely_data_source": "yfinance QQQ daily data from qqq_leverage_validation with period='10y' and interval='1d'; SPY used for context only",
        "likely_date_range": "period='10y' yfinance window at report run time; exact saved run dates not recovered",
        "likely_signal_timing": "next-bar close-to-close return; exposure based on prior close greater than prior 200-day SMA",
        "likely_price_field": "Close values from yfinance with auto_adjust=True",
        "likely_adjustment_status": "dividend/split adjusted by yfinance auto_adjust=True, exact original downloaded rows missing",
        "likely_warmup_rule": "starts after TREND_WINDOW=200; initial curve point at qqq_rows[200], returns from qqq_rows[201]",
        "likely_cost_assumption": "10 bps transaction cost on exposure changes; 300 bps financing placeholder but no excess leverage for 1.00x QQQ100",
        "likely_cash_handling": "flat/cash days earn zero return",
        "likely_metric_method": "metrics_for_curve from short_leverage_research_lab over equity curve",
        "likely_annualisation": "252 trading-day annualisation inferred from shared metrics helpers",
        "confidence_level": CONFIDENCE_LEVEL,
        "unresolved_gap": "original_daily_stream_missing; exact yfinance snapshot/date range unavailable; saved metrics may be constants copied from generated CSV",
        "required_next_step": REQUIRED_NEXT_STEP,
        **safety_flags(),
    }


def build_gap_rows(created_at: str) -> list[dict[str, Any]]:
    gaps = [
        (
            "original_daily_stream_missing",
            "blocked",
            "No tracked source contains the original daily equity/return stream behind the saved QQQ100 metrics.",
            "Cannot prove exact reconciliation or overwrite current stream safely.",
        ),
        (
            "exact_run_date_range_unknown",
            "manual_review_required",
            "The source used yfinance period='10y', so the exact date range depended on when the original report ran.",
            "Date-range drift can explain part of the generated benchmark gap.",
        ),
        (
            "saved_metrics_promoted_as_constants",
            "manual_review_required",
            "The exact metrics first appear in tracked source in commit 4aebc22 as saved QQQ lead context and constants.",
            "Current reports should treat them as saved benchmark metrics, not as a recoverable stream.",
        ),
        (
            "price_snapshot_and_adjustment_unverified",
            "manual_review_required",
            "Source code shows yfinance auto_adjust=True, but the original downloaded rows are not tracked.",
            "Dividend/split and provider revisions may prevent exact replay.",
        ),
        (
            "cost_and_cash_assumptions_partially_recovered",
            "partial",
            "Source code shows 10 bps trade cost, 300 bps financing placeholder, and zero cash return.",
            "Assumptions are likely but exact saved output still needs original CSV or regenerated validation.",
        ),
    ]
    return [
        {
            "created_at": created_at,
            "gap_name": name,
            "gap_status": status,
            "evidence": evidence,
            "impact": impact,
            "required_next_step": REQUIRED_NEXT_STEP,
            **safety_flags(),
        }
        for name, status, evidence, impact in gaps
    ]


def build_summary_rows(created_at: str, report: dict[str, Any], gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unresolved = "; ".join(row["gap_name"] for row in gaps if row["gap_status"] in {"blocked", "manual_review_required"})
    parameter_set = (
        "QQQ ETF; yfinance 10y 1d auto_adjust=True; SMA200 trend gate; "
        "prior-close signal; next-bar close-to-close returns; 1.00x exposure; zero cash return; 10 bps exposure-change cost"
    )
    items = [
        ("saved_benchmark_metrics", f"CAGR={SAVED_CAGR}; Sharpe={SAVED_SHARPE}; MaxDD={SAVED_MAXDD}; Calmar={SAVED_CALMAR}", "Saved benchmark metrics under review."),
        ("recovered_source_status", report["recovered_source_status"], "Source is partially recovered from tracked code/history; original daily stream is missing."),
        ("likely_original_parameter_set", parameter_set, "Likely parameter set from qqq_leverage_validation.py."),
        ("source_evidence", report["likely_strategy_source"], "Tracked commit/file evidence."),
        ("confidence_level", report["confidence_level"], "Confidence is limited by the missing original daily stream and yfinance snapshot."),
        ("unresolved_gaps", unresolved, "Remaining blockers before changing stream generation."),
        ("required_next_step", REQUIRED_NEXT_STEP, "Do not update stream generation until the original stream is recovered or validation is regenerated."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "QQQ100 benchmark inputs report created. Saved-output-only research; no execution wiring approved.",
        f"saved benchmark metrics: {summary['saved_benchmark_metrics']}",
        f"recovered source status: {summary['recovered_source_status']}",
        f"likely original parameter set: {summary['likely_original_parameter_set']}",
        f"confidence level: {summary['confidence_level']}",
        f"unresolved gaps: {summary['unresolved_gaps']}",
        f"required next step: {summary['required_next_step']}",
        f"Saved report: {output_path}",
        "execution_approved=false; scheduling_approved=false",
    ]


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
