"""Research-only high-growth daily return streams for portfolio research.

This module creates saved daily return streams for existing high-growth stock
research candidates. It reuses the fixed high-growth drawdown-control research
logic and does not call Alpaca, read positions, create orders, write SQLite,
send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import high_growth_stock_lab as lab
from trading_bot.research import high_growth_stock_drawdown_control as drawdown_control


STATUS_CREATED = "high_growth_return_streams_created"
STATUS_PARTIAL_CREATED = "high_growth_return_streams_partial_created"
STATUS_BLOCKED_NO_VALID_MARKET_DATA = "high_growth_return_streams_blocked_no_valid_market_data"
STATUS_BLOCKED_INVALID_UNIVERSE = "high_growth_return_streams_blocked_invalid_universe"
STATUS_BLOCKED_ALL_ROWS_DROPPED = "high_growth_return_streams_blocked_all_rows_dropped"
SLEEVE_NAME = "high_growth_stock_research_sleeve"
SLEEVE_FAMILY = "high_growth_stock"
PRIMARY_CANDIDATE = "codex_broad_growth_balanced_breakout_control"
REFERENCE_CANDIDATE = "broad_growth_top1_reference"
AMBITIOUS_REFERENCE = "codex_ambitious_concentrated_growth_persistence"
BIGGEST_BLOCKER = "high_growth_streams_remain_research_only_not_execution_ready"
NEXT_STEP_REVIEW_STREAMS = "rerun_multi_sleeve_portfolio_backtest_after_reviewing_high_growth_stream_risk"
NEXT_STEP_FIX_MARKET_DATA = "fix_high_growth_market_data_or_candidate_universe_before_multi_sleeve_backtest"
RECOMMENDED_NEXT_STEP = NEXT_STEP_REVIEW_STREAMS
PRICE_FIXTURE = Path("data/high_growth_return_stream_price_fixture.csv")

OUTPUT_FILES = {
    "streams": Path("data/high_growth_return_streams.csv"),
    "metrics": Path("data/high_growth_return_stream_metrics.csv"),
    "summary": Path("data/high_growth_return_stream_summary.csv"),
    "blockers": Path("data/high_growth_return_stream_blockers.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "preview_only",
    "return_stream_only",
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
    "general_execution_approved",
    "high_growth_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": True,
    "return_stream_only": True,
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
    "general_execution_approved": False,
    "high_growth_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

STREAM_COLUMNS = [
    "created_at",
    "date",
    "sleeve_name",
    "sleeve_family",
    "candidate_name",
    "strategy_name",
    "daily_return",
    "daily_strategy_return",
    "equity",
    "invested_flag",
    "exposure",
    "cash_weight",
    "source_status",
    "data_source",
    "research_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

METRIC_COLUMNS = [
    "created_at",
    "sleeve_name",
    "sleeve_family",
    "candidate_name",
    "strategy_name",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "annual_volatility",
    "cash_percentage",
    "row_count",
    "first_date",
    "last_date",
    "trade_count",
    "source_status",
    "research_status",
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

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_COLUMNS,
]


@dataclass
class HighGrowthReturnStreamsResult:
    output_paths: dict[str, Path]
    stream_rows: list[dict[str, Any]]
    metric_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_return_streams(root_dir: Path | str = ".") -> HighGrowthReturnStreamsResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    price_data, data_errors, data_source = load_price_data(root)
    diagnostics = build_market_data_diagnostics(price_data, data_errors)
    simulations = drawdown_control.build_simulations(price_data, data_errors)
    candidate_names = {PRIMARY_CANDIDATE, REFERENCE_CANDIDATE}
    candidate_sims = [simulation for simulation in simulations if simulation.name in candidate_names]
    stream_rows = [
        row
        for simulation in candidate_sims
        for row in stream_rows_from_simulation(created_at, simulation, data_source)
    ]
    provisional_status = final_stream_status(candidate_sims, stream_rows, diagnostics)
    required_next_step = required_next_step_for_status(provisional_status)
    metric_rows = [
        metric_row_from_simulation(created_at, simulation, data_source, required_next_step)
        for simulation in candidate_sims
    ]
    if not metric_rows:
        metric_rows = [missing_metric_row(created_at, PRIMARY_CANDIDATE, "missing_market_data", data_errors)]
    summary_rows = build_summary_rows(created_at, metric_rows, stream_rows, data_errors, diagnostics, provisional_status)
    blocker_rows = build_blocker_rows(created_at, data_errors, diagnostics, provisional_status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["streams"], STREAM_COLUMNS, stream_rows)
    write_rows(output_paths["metrics"], METRIC_COLUMNS, metric_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthReturnStreamsResult(
        output_paths=output_paths,
        stream_rows=stream_rows,
        metric_rows=metric_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["streams"]),
    )


def show_high_growth_return_streams(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    metrics_path = root / OUTPUT_FILES["metrics"]
    if not summary_path.exists() or not metrics_path.exists():
        return 1, [
            "High-growth return streams are missing.",
            "Run `python bot.py --high-growth-return-streams` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    summary = {row.get("summary_name", ""): row.get("summary_value", "") for row in read_csv_rows(summary_path)}
    return 0, [
        "High-growth return streams. Saved-output research only; no execution wiring approved.",
        f"final_stream_status: {summary.get('final_stream_status', 'missing')}",
        f"generated stream count: {summary.get('generated_stream_count', 'missing')}",
        f"candidate metrics: {summary.get('candidate_metrics', 'missing')}",
        f"status counts: {summary.get('status_counts', 'missing')}",
        f"ticker diagnostics: total={summary.get('total_ticker_count', 'missing')}; successful={summary.get('successful_ticker_count', 'missing')}; failed={summary.get('failed_ticker_count', 'missing')}",
        f"failure reason counts: {summary.get('failure_reason_counts', 'missing')}",
        f"example failures: {summary.get('example_failed_tickers', 'missing')}",
        f"candidate status: {summary.get('candidate_status', 'missing')}",
        f"best Calmar candidate: {summary.get('best_calmar_candidate', 'missing')}",
        f"best Sharpe candidate: {summary.get('best_sharpe_candidate', 'missing')}",
        f"warnings: {summary.get('warnings', 'missing')}",
        f"biggest blocker: {summary.get('biggest_blocker', BIGGEST_BLOCKER)}",
        f"recommended next step: {summary.get('recommended_next_step', RECOMMENDED_NEXT_STEP)}",
        "execution_approved=false; paper_execution_approved=false; high_growth_execution_approved=false; scheduling_approved=false",
    ]


def load_price_data(root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str], str]:
    fixture = root / PRICE_FIXTURE
    if fixture.exists():
        return load_fixture_prices(fixture), {}, "saved_price_fixture"
    tickers = drawdown_control.BROAD_UNIVERSE + lab.BENCHMARK_TICKERS
    price_data, data_errors = lab.download_daily_price_data(tickers, root / "data" / "yfinance_cache")
    return price_data, data_errors, "yfinance_research_download"


def load_fixture_prices(path: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_ticker: dict[str, list[dict[str, Any]]] = {}
    for row in read_csv_rows(path):
        ticker = str(row.get("ticker", "")).upper()
        if not ticker:
            continue
        try:
            close = float(row.get("close") or row.get("adj_close") or row.get("adjusted_close"))
        except (TypeError, ValueError):
            continue
        rows_by_ticker.setdefault(ticker, []).append({"date": row.get("date", ""), "close": close})
    for rows in rows_by_ticker.values():
        rows.sort(key=lambda item: str(item["date"]))
    return rows_by_ticker


def stream_rows_from_simulation(created_at: str, simulation: lab.StrategySimulation, data_source: str) -> list[dict[str, Any]]:
    rows = []
    previous_equity = None
    for point in simulation.curve:
        equity = float(point.get("equity", 0.0) or 0.0)
        daily_return = 0.0 if previous_equity in {None, 0.0} else equity / float(previous_equity) - 1.0
        cash_weight = float(point.get("cash", 0.0) or 0.0)
        exposure = 1.0 - cash_weight
        rows.append(
            {
                "created_at": created_at,
                "date": point.get("date", ""),
                "sleeve_name": SLEEVE_NAME,
                "sleeve_family": SLEEVE_FAMILY,
                "candidate_name": simulation.name,
                "strategy_name": simulation.name,
                "daily_return": round(daily_return, 10),
                "daily_strategy_return": round(daily_return, 10),
                "equity": round(equity, 6),
                "invested_flag": exposure > 0,
                "exposure": round(exposure, 6),
                "cash_weight": round(cash_weight, 6),
                "source_status": "generated_from_high_growth_drawdown_control_simulation" if simulation.data_status == "ok" else simulation.data_status,
                "data_source": data_source,
                "research_status": "high_growth_research_only_not_preview_or_execution",
                "required_next_step": RECOMMENDED_NEXT_STEP,
                **safety_flags(),
            }
        )
        previous_equity = equity
    return rows


def metric_row_from_simulation(
    created_at: str,
    simulation: lab.StrategySimulation,
    data_source: str,
    required_next_step: str,
) -> dict[str, Any]:
    if simulation.data_status != "ok" or not simulation.curve:
        row = missing_metric_row(created_at, simulation.name, simulation.data_status, {})
        row["data_source"] = data_source
        row["required_next_step"] = required_next_step
        return row
    metrics = lab.metrics_for_curve(simulation.curve)
    first_date = simulation.curve[0]["date"] if simulation.curve else ""
    last_date = simulation.curve[-1]["date"] if simulation.curve else ""
    return {
        "created_at": created_at,
        "sleeve_name": SLEEVE_NAME,
        "sleeve_family": SLEEVE_FAMILY,
        "candidate_name": simulation.name,
        "strategy_name": simulation.name,
        "CAGR": round(float(metrics["cagr_pct"]), 4),
        "Sharpe": round(float(metrics["sharpe_ratio"]), 4),
        "MaxDD": round(float(metrics["max_drawdown_pct"]), 4),
        "Calmar": round(float(metrics["calmar_ratio"]), 4),
        "annual_volatility": round(float(metrics["annualised_volatility_pct"]), 4),
        "cash_percentage": round(lab.concentration_stats(simulation)["time_in_cash_pct"], 4),
        "row_count": len(simulation.curve),
        "first_date": first_date,
        "last_date": last_date,
        "trade_count": len(simulation.trades),
        "source_status": "generated_from_high_growth_drawdown_control_simulation" if simulation.data_status == "ok" else simulation.data_status,
        "research_status": "high_growth_research_only_not_preview_or_execution",
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def missing_metric_row(created_at: str, candidate_name: str, source_status: str, data_errors: dict[str, str]) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "sleeve_name": SLEEVE_NAME,
        "sleeve_family": SLEEVE_FAMILY,
        "candidate_name": candidate_name,
        "strategy_name": candidate_name,
        "CAGR": "missing_saved_metrics",
        "Sharpe": "missing_saved_metrics",
        "MaxDD": "missing_saved_metrics",
        "Calmar": "missing_saved_metrics",
        "annual_volatility": "missing_saved_metrics",
        "cash_percentage": "missing_saved_metrics",
        "row_count": 0,
        "first_date": "",
        "last_date": "",
        "trade_count": 0,
        "source_status": source_status,
        "research_status": "data_unavailable_research_only",
        "required_next_step": f"Resolve high-growth market data errors; count={len(data_errors)}.",
        **safety_flags(),
    }


def build_summary_rows(
    created_at: str,
    metrics: list[dict[str, Any]],
    streams: list[dict[str, Any]],
    data_errors: dict[str, str],
    diagnostics: dict[str, Any],
    status: str,
) -> list[dict[str, Any]]:
    generated = [
        row
        for row in metrics
        if str(row.get("source_status", "")).startswith("generated") and safe_float(row.get("row_count")) > 0
    ]
    best_calmar = best_metric_row(generated, "Calmar")
    best_sharpe = best_metric_row(generated, "Sharpe")
    status_counts = counts(row.get("source_status", "") for row in metrics)
    stream_count = len({row["candidate_name"] for row in streams})
    required_next_step = required_next_step_for_status(status)
    items = [
        ("final_stream_status", status, "Created only when at least one candidate has real daily return rows; blocked statuses identify missing market data or dropped rows."),
        ("generated_stream_count", str(stream_count), "Number of candidate streams with real daily rows written."),
        ("candidate_metrics", format_metric_rows(generated or metrics), "Candidate metrics from generated daily streams."),
        ("status_counts", status_counts, "Source status counts."),
        ("total_ticker_count", str(diagnostics["total_ticker_count"]), "Total intended ticker count for the high-growth return-stream market-data request."),
        ("successful_ticker_count", str(diagnostics["successful_ticker_count"]), "Tickers with usable daily rows."),
        ("failed_ticker_count", str(diagnostics["failed_ticker_count"]), "Tickers with market-data errors."),
        ("failure_reason_counts", diagnostics["failure_reason_counts"], "Compact market-data failure reason counts."),
        ("example_failed_tickers", diagnostics["example_failed_tickers"], "Up to five example failed tickers and sanitized reasons."),
        ("candidate_status", candidate_status(metrics, streams), "Per-candidate stream creation status."),
        ("best_calmar_candidate", format_metric_row(best_calmar), "Highest Calmar among generated high-growth stream candidates."),
        ("best_sharpe_candidate", format_metric_row(best_sharpe), "Highest Sharpe among generated high-growth stream candidates."),
        ("warnings", "survivorship_bias_warning; concentration_risk; outlier_dependence; high_growth_research_only", "High-growth branch remains high risk and not preview/execution approved."),
        ("biggest_blocker", BIGGEST_BLOCKER, "High-growth streams are research data only and do not approve portfolio execution."),
        ("recommended_next_step", required_next_step, "Use market-data repair first when no real high-growth stream rows exist."),
        ("data_errors", f"ticker_errors={len(data_errors)}", "; ".join(f"{key}={value}" for key, value in sorted(data_errors.items()))[:500]),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(
    created_at: str,
    data_errors: dict[str, str],
    diagnostics: dict[str, Any],
    status: str,
) -> list[dict[str, Any]]:
    required_next_step = required_next_step_for_status(status)
    blockers = [
        (BIGGEST_BLOCKER, "blocked", "high", "High-growth daily streams are research-only and cannot approve preview, execution, or scheduling.", required_next_step),
        ("concentration_and_survivorship_risk", "warning", "high", "The stream uses current-constituent high-growth universes and can depend heavily on a few stocks.", "Keep concentration, survivorship, and outlier warnings visible."),
        ("crypto_stream_still_missing", "blocked", "medium", "This command does not create crypto return streams.", "Create crypto streams separately only from real daily data."),
        (
            "market_data_errors",
            "blocked" if status == STATUS_BLOCKED_NO_VALID_MARKET_DATA else ("warning" if data_errors else "pass"),
            "high" if status == STATUS_BLOCKED_NO_VALID_MARKET_DATA else "medium",
            f"ticker_errors={len(data_errors)}; total_tickers={diagnostics['total_ticker_count']}; successful_tickers={diagnostics['successful_ticker_count']}; reason_counts={diagnostics['failure_reason_counts']}; examples={diagnostics['example_failed_tickers']}",
            required_next_step,
        ),
        (
            "high_growth_stream_generation_status",
            "blocked" if status.startswith("high_growth_return_streams_blocked") else "pass",
            "high" if status.startswith("high_growth_return_streams_blocked") else "low",
            f"status={status}; candidate_status={diagnostics.get('candidate_status', 'see_summary')}",
            required_next_step,
        ),
        ("execution_wiring_blocked", "blocked", "critical", "No execution, Alpaca, order, live-position, SQLite, alert, scheduling, or Hermes path is approved.", "Keep this layer saved-output research-only."),
    ]
    return [
        {
            "created_at": created_at,
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **safety_flags(),
        }
        for name, status, severity, details, next_step in blockers
    ]


def best_metric_row(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    return max(rows, key=lambda row: safe_float(row.get(metric)), default={})


def format_metric_rows(rows: list[dict[str, Any]]) -> str:
    return " | ".join(format_metric_row(row) for row in rows) or "none"


def format_metric_row(row: dict[str, Any]) -> str:
    if not row:
        return "none"
    return f"{row.get('candidate_name')}: CAGR={row.get('CAGR')}; Sharpe={row.get('Sharpe')}; MaxDD={row.get('MaxDD')}; Calmar={row.get('Calmar')}; rows={row.get('row_count')}"


def counts(values: Any) -> str:
    result: dict[str, int] = {}
    for value in values:
        key = str(value or "missing")
        result[key] = result.get(key, 0) + 1
    return "; ".join(f"{key}={value}" for key, value in sorted(result.items())) or "none"


def build_market_data_diagnostics(
    price_data: dict[str, list[dict[str, Any]]],
    data_errors: dict[str, str],
) -> dict[str, Any]:
    intended_tickers = list(dict.fromkeys(drawdown_control.BROAD_UNIVERSE + lab.BENCHMARK_TICKERS))
    successful = [ticker for ticker in intended_tickers if ticker in price_data and price_data[ticker]]
    failed = [ticker for ticker in intended_tickers if ticker in data_errors]
    total = len(intended_tickers)
    reason_counts = counts(classify_error_reason(value) for value in data_errors.values())
    examples = "; ".join(
        f"{ticker}={classify_error_reason(data_errors[ticker])}"
        for ticker in sorted(data_errors)[:5]
    ) or "none"
    return {
        "total_ticker_count": total,
        "successful_ticker_count": len(successful),
        "failed_ticker_count": len(failed),
        "failure_reason_counts": reason_counts,
        "example_failed_tickers": examples,
    }


def classify_error_reason(reason: str) -> str:
    normalized = str(reason or "").lower()
    if "no module named 'yfinance'" in normalized or "yfinance unavailable" in normalized:
        return "yfinance_unavailable"
    if "unable to open database file" in normalized:
        return "yfinance_cache_database_unavailable"
    if "timeout" in normalized or "timed out" in normalized:
        return "market_data_timeout"
    if "no daily market data returned" in normalized:
        return "no_daily_market_data_returned"
    if "not enough daily history" in normalized:
        return "not_enough_daily_history"
    if "insufficient market data" in normalized:
        return "insufficient_market_data"
    if "invalid" in normalized and "ticker" in normalized:
        return "invalid_ticker"
    return "market_data_error"


def final_stream_status(
    simulations: list[lab.StrategySimulation],
    streams: list[dict[str, Any]],
    diagnostics: dict[str, Any],
) -> str:
    intended_tickers = drawdown_control.BROAD_UNIVERSE + lab.BENCHMARK_TICKERS
    if not intended_tickers:
        return STATUS_BLOCKED_INVALID_UNIVERSE
    generated_candidates = {row["candidate_name"] for row in streams}
    if generated_candidates and len(generated_candidates) < len(simulations):
        return STATUS_PARTIAL_CREATED
    if generated_candidates:
        return STATUS_CREATED
    if diagnostics["successful_ticker_count"] == 0:
        return STATUS_BLOCKED_NO_VALID_MARKET_DATA
    return STATUS_BLOCKED_ALL_ROWS_DROPPED


def required_next_step_for_status(status: str) -> str:
    if status.startswith("high_growth_return_streams_blocked"):
        return NEXT_STEP_FIX_MARKET_DATA
    return NEXT_STEP_REVIEW_STREAMS


def candidate_status(metrics: list[dict[str, Any]], streams: list[dict[str, Any]]) -> str:
    generated = {str(row.get("candidate_name", "")) for row in streams}
    statuses = []
    for row in metrics:
        name = str(row.get("candidate_name", "missing_candidate"))
        if name in generated:
            statuses.append(f"{name}=real_daily_rows")
        else:
            statuses.append(f"{name}={row.get('source_status', 'missing_stream_rows')}")
    return "; ".join(statuses) or "none"


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "High-growth return streams created. Saved-output research only; no execution wiring approved.",
        f"final_stream_status: {summary['final_stream_status']}",
        f"generated stream count: {summary['generated_stream_count']}",
        f"candidate metrics: {summary['candidate_metrics']}",
        f"status counts: {summary['status_counts']}",
        f"ticker diagnostics: total={summary.get('total_ticker_count', 'missing')}; successful={summary.get('successful_ticker_count', 'missing')}; failed={summary.get('failed_ticker_count', 'missing')}",
        f"failure reason counts: {summary.get('failure_reason_counts', 'missing')}",
        f"example failures: {summary.get('example_failed_tickers', 'missing')}",
        f"candidate status: {summary.get('candidate_status', 'missing')}",
        f"best Calmar candidate: {summary['best_calmar_candidate']}",
        f"best Sharpe candidate: {summary['best_sharpe_candidate']}",
        f"warnings: {summary['warnings']}",
        f"biggest blocker: {summary['biggest_blocker']}",
        f"recommended next step: {summary['recommended_next_step']}",
        f"Saved streams: {output_path}",
        "execution_approved=false; paper_execution_approved=false; high_growth_execution_approved=false; scheduling_approved=false",
    ]


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


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
