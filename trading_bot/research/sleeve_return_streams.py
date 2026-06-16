"""Research-only saved daily return streams for portfolio sleeves.

This module can generate QQQ/cash/defensive QQQ return streams from research
price data and labels unsupported high-growth/crypto streams as missing. It
does not call Alpaca, read live positions, create orders, write SQLite, send
alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FINAL_STREAM_STATUS = "sleeve_return_streams_partial_created"
QQQ100_SLEEVE = "qqq100_core_trend_sleeve"
QQQ100_STRATEGY = "qqq_100_trend_gate"
BEST_DEFENSIVE_CANDIDATE = "qqq100_combined_trend_spy_regime_drawdown_gate"
BIGGEST_BLOCKER = "high_growth_crypto_saved_return_streams_missing"
RECOMMENDED_NEXT_STEP = "rerun_multi_sleeve_portfolio_backtest_with_saved_streams"
MISSING = "missing_saved_metrics"
MISSING_STREAM = "missing_saved_return_stream"
PRICE_FIXTURE = Path("data/sleeve_return_stream_price_fixture.csv")

OUTPUT_FILES = {
    "streams": Path("data/sleeve_return_streams.csv"),
    "summary": Path("data/sleeve_return_streams_summary.csv"),
    "sleeves": Path("data/sleeve_return_streams_sleeves.csv"),
    "quality": Path("data/sleeve_return_streams_quality.csv"),
    "blockers": Path("data/sleeve_return_streams_blockers.csv"),
    "next_steps": Path("data/sleeve_return_streams_next_steps.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "report_only",
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
    "general_execution_approved",
    "qqq100_execution_approved",
    "codex_experimental_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "high_growth_execution_approved",
    "crypto_execution_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
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
    "general_execution_approved": False,
    "qqq100_execution_approved": False,
    "codex_experimental_execution_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "high_growth_execution_approved": False,
    "crypto_execution_approved": False,
}

STREAM_COLUMNS = [
    "date",
    "sleeve_name",
    "candidate_name",
    "ticker_or_assets",
    "signal_state",
    "daily_asset_return",
    "daily_strategy_return",
    "exposure",
    "cash_weight",
    "data_source",
    "data_quality",
    *SAFETY_COLUMNS,
]

QUALITY_COLUMNS = [
    "sleeve_name",
    "candidate_name",
    "stream_status",
    "row_count",
    "start_date",
    "end_date",
    "missing_return_count",
    "data_source",
    "metric_alignment_status",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "annual_volatility",
    "cash_percentage",
    "trade_count_or_signal_changes",
    "blocker",
    "recommended_next_step",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_COLUMNS,
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_COLUMNS,
]

NEXT_STEP_COLUMNS = [
    "step_name",
    "step_status",
    "details",
    "required_before_candidate_label_change",
    *SAFETY_COLUMNS,
]


@dataclass
class SleeveReturnStreamsResult:
    output_paths: dict[str, Path]
    stream_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    sleeve_rows: list[dict[str, Any]]
    quality_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    next_step_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_sleeve_return_streams(root_dir: Path | str = ".") -> SleeveReturnStreamsResult:
    root = Path(root_dir)
    prices, data_source, errors = load_research_price_series(root)
    stream_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    if "QQQ" in prices:
        qqq_rows = build_qqq100_stream(prices["QQQ"], data_source)
        stream_rows.extend(qqq_rows)
        quality_rows.append(quality_row_from_stream(QQQ100_SLEEVE, QQQ100_STRATEGY, qqq_rows, "approximate_or_needs_reconciliation"))
        cash_rows = build_cash_stream(prices["QQQ"], data_source)
        stream_rows.extend(cash_rows)
        quality_rows.append(quality_row_from_stream("defensive_cash_or_bond_sleeve", "cash_default_defensive_sleeve", cash_rows, "cash_stream_no_metric_alignment_required"))
    else:
        quality_rows.append(missing_quality_row(QQQ100_SLEEVE, QQQ100_STRATEGY, "missing_qqq_price_data", errors.get("QQQ", "QQQ price data unavailable")))

    if "QQQ" in prices and "SPY" in prices:
        for candidate_name, rows in build_defensive_streams(prices["QQQ"], prices["SPY"], data_source).items():
            stream_rows.extend(rows)
            quality_rows.append(quality_row_from_stream("qqq_defensive_crash_gate_research_sleeve", candidate_name, rows, "research_metrics_generated"))
        codex_rows = clone_stream(
            [row for row in stream_rows if row["candidate_name"] == BEST_DEFENSIVE_CANDIDATE],
            "codex_experimental_research_sleeve",
            "codex_qqq_calmar_optimised_defensive_gate_sleeve",
        )
        stream_rows.extend(codex_rows)
        quality_rows.append(quality_row_from_stream("codex_experimental_research_sleeve", "codex_qqq_calmar_optimised_defensive_gate_sleeve", codex_rows, "research_metrics_generated"))
    else:
        quality_rows.append(missing_quality_row("qqq_defensive_crash_gate_research_sleeve", "qqq100_defensive_gate_candidates", "missing_saved_data", errors.get("SPY", "SPY price data unavailable")))
        quality_rows.append(missing_quality_row("codex_experimental_research_sleeve", "codex_qqq_calmar_optimised_defensive_gate_sleeve", "missing_saved_data", "Codex experimental sleeve points to defensive QQQ stream after QQQ/SPY data exists."))

    quality_rows.append(missing_quality_row("high_growth_stock_research_sleeve", "codex_broad_growth_balanced_breakout_control", MISSING_STREAM, "Only summary metrics are available; daily returns are not invented."))
    quality_rows.append(missing_quality_row("crypto_research_sleeve", "crypto_off_hours_research_route", MISSING_STREAM, "No reliable saved crypto daily return stream is available."))

    generated = [row for row in quality_rows if row["stream_status"] in {"qqq100_return_stream_created", "defensive_qqq_streams_created", "cash_return_stream_created", "codex_experimental_stream_created"}]
    missing = [row for row in quality_rows if "missing" in row["stream_status"]]
    final_status = "sleeve_return_streams_created" if not missing else FINAL_STREAM_STATUS
    summary_rows = build_summary_rows(final_status, generated, missing, quality_rows)
    blocker_rows = build_blocker_rows()
    next_step_rows = build_next_step_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["streams"], STREAM_COLUMNS, stream_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["sleeves"], QUALITY_COLUMNS, quality_rows)
    write_rows(output_paths["quality"], QUALITY_COLUMNS, quality_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["next_steps"], NEXT_STEP_COLUMNS, next_step_rows)
    return SleeveReturnStreamsResult(
        output_paths=output_paths,
        stream_rows=stream_rows,
        summary_rows=summary_rows,
        sleeve_rows=quality_rows,
        quality_rows=quality_rows,
        blocker_rows=blocker_rows,
        next_step_rows=next_step_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["streams"]),
    )


def show_sleeve_return_streams(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Sleeve return streams are missing.",
            "Run `python bot.py --sleeve-return-streams` first.",
            "execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
        ]
    summary = {row.get("summary_name", ""): row.get("summary_value", "") for row in read_csv_rows(path)}
    return 0, [
        "Sleeve return streams. Research-only saved daily streams; no execution wiring approved.",
        f"final_stream_status: {summary.get('final_stream_status', 'missing')}",
        f"generated sleeve streams: {summary.get('generated_sleeve_streams', 'missing')}",
        f"missing sleeve streams: {summary.get('missing_sleeve_streams', 'missing')}",
        f"QQQ100 stream metrics: {summary.get('qqq100_stream_metrics', 'missing')}",
        f"best defensive QQQ stream candidate: {summary.get('best_defensive_qqq_stream_candidate', 'missing')}",
        f"biggest blocker: {summary.get('biggest_blocker', BIGGEST_BLOCKER)}",
        f"recommended next step: {summary.get('recommended_next_step', RECOMMENDED_NEXT_STEP)}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; qqq100_execution_approved=false; codex_experimental_execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def load_research_price_series(root: Path) -> tuple[dict[str, list[dict[str, Any]]], str, dict[str, str]]:
    fixture = root / PRICE_FIXTURE
    if fixture.exists():
        return load_fixture_prices(fixture), "saved_price_fixture", {}
    try:
        return download_yfinance_prices(root), "yfinance_research_download", {}
    except Exception as exc:  # pragma: no cover - exercised only when market data is unavailable.
        return {}, "missing_saved_data", {"QQQ": str(exc), "SPY": str(exc)}


def load_fixture_prices(path: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_ticker: dict[str, list[dict[str, Any]]] = {}
    for row in read_csv_rows(path):
        ticker = str(row.get("ticker", "")).upper()
        if not ticker:
            continue
        close_text = row.get("close") or row.get("adj_close") or row.get("adjusted_close")
        try:
            close = float(close_text)
        except (TypeError, ValueError):
            continue
        rows_by_ticker.setdefault(ticker, []).append({"date": row.get("date", ""), "close": close})
    for rows in rows_by_ticker.values():
        rows.sort(key=lambda item: str(item["date"]))
    return rows_by_ticker


def download_yfinance_prices(root: Path) -> dict[str, list[dict[str, Any]]]:
    import yfinance as yf

    cache_dir = root / "data" / "yfinance_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        yf.set_tz_cache_location(str(cache_dir))
    except AttributeError:
        pass
    prices: dict[str, list[dict[str, Any]]] = {}
    for ticker in ["QQQ", "SPY"]:
        data = yf.download(ticker, period="10y", interval="1d", auto_adjust=True, progress=False, threads=False)
        if data is None or data.empty:
            continue
        close = extract_close_from_yfinance_frame(data, ticker).dropna()
        prices[ticker] = [
            {"date": str(index.date()) if hasattr(index, "date") else str(index)[:10], "close": float(value)}
            for index, value in close.items()
        ]
    if "QQQ" not in prices:
        raise RuntimeError("No QQQ research price data returned.")
    return prices


def extract_close_from_yfinance_frame(data: Any, ticker: str) -> Any:
    columns = data.columns
    has_multi_index = getattr(columns, "nlevels", 1) > 1
    if has_multi_index:
        for key in (("Close", ticker), (ticker, "Close")):
            if key in columns:
                return first_series(data[key])
        if "Close" in columns.get_level_values(0):
            return first_series(data.xs("Close", axis=1, level=0))
        if "Close" in columns.get_level_values(1):
            return first_series(data.xs("Close", axis=1, level=1))
    if "Close" not in data:
        raise RuntimeError("Downloaded data does not contain a Close price column.")
    return first_series(data["Close"])


def first_series(value: Any) -> Any:
    if getattr(value, "ndim", 1) == 2:
        return value.iloc[:, 0]
    return value


def build_qqq100_stream(qqq: list[dict[str, Any]], data_source: str) -> list[dict[str, Any]]:
    rows = []
    for index in range(1, len(qqq)):
        asset_return = daily_return(qqq, index)
        exposure = 1.0 if above_sma(qqq, index - 1, 100) else 0.0
        rows.append(
            stream_row(
                qqq[index]["date"],
                QQQ100_SLEEVE,
                QQQ100_STRATEGY,
                "QQQ",
                "long" if exposure else "flat",
                asset_return,
                asset_return * exposure,
                exposure,
                1.0 - exposure,
                data_source,
                "research_price_stream",
            )
        )
    return rows


def build_cash_stream(qqq: list[dict[str, Any]], data_source: str) -> list[dict[str, Any]]:
    return [
        stream_row(row["date"], "defensive_cash_or_bond_sleeve", "cash_default_defensive_sleeve", "cash", "cash", 0.0, 0.0, 0.0, 1.0, data_source, "cash_stream")
        for row in qqq[1:]
    ]


def build_defensive_streams(qqq: list[dict[str, Any]], spy: list[dict[str, Any]], data_source: str) -> dict[str, list[dict[str, Any]]]:
    spy_by_date = {row["date"]: row for row in spy}
    qqq_peak = qqq[0]["close"] if qqq else 0.0
    variants = {
        "qqq100_spy_sma200_regime_filter": [],
        "qqq100_rolling_drawdown_15_filter": [],
        BEST_DEFENSIVE_CANDIDATE: [],
    }
    for index in range(1, len(qqq)):
        date = qqq[index]["date"]
        asset_return = daily_return(qqq, index)
        prior_date = qqq[index - 1]["date"]
        spy_index = next((i for i, row in enumerate(spy) if row["date"] == prior_date), -1)
        qqq_trend = above_sma(qqq, index - 1, 100)
        spy_regime = spy_index >= 0 and above_sma(spy, spy_index, 200)
        qqq_peak = max(qqq_peak, float(qqq[index - 1]["close"]))
        drawdown_ok = (float(qqq[index - 1]["close"]) / qqq_peak - 1.0) >= -0.15 if qqq_peak > 0 else False
        exposures = {
            "qqq100_spy_sma200_regime_filter": 1.0 if qqq_trend and spy_regime else 0.0,
            "qqq100_rolling_drawdown_15_filter": 1.0 if qqq_trend and drawdown_ok else 0.0,
            BEST_DEFENSIVE_CANDIDATE: 1.0 if qqq_trend and spy_regime and drawdown_ok else 0.0,
        }
        if date not in spy_by_date:
            continue
        for candidate_name, exposure in exposures.items():
            variants[candidate_name].append(
                stream_row(
                    date,
                    "qqq_defensive_crash_gate_research_sleeve",
                    candidate_name,
                    "QQQ/SPY/cash",
                    "long" if exposure else "flat",
                    asset_return,
                    asset_return * exposure,
                    exposure,
                    1.0 - exposure,
                    data_source,
                    "research_price_stream",
                )
            )
    return variants


def clone_stream(rows: list[dict[str, Any]], sleeve_name: str, candidate_name: str) -> list[dict[str, Any]]:
    cloned = []
    for row in rows:
        new_row = dict(row)
        new_row["sleeve_name"] = sleeve_name
        new_row["candidate_name"] = candidate_name
        cloned.append(new_row)
    return cloned


def stream_row(
    date: str,
    sleeve_name: str,
    candidate_name: str,
    ticker_or_assets: str,
    signal_state: str,
    daily_asset_return: float,
    daily_strategy_return: float,
    exposure: float,
    cash_weight: float,
    data_source: str,
    data_quality: str,
) -> dict[str, Any]:
    return {
        "date": date,
        "sleeve_name": sleeve_name,
        "candidate_name": candidate_name,
        "ticker_or_assets": ticker_or_assets,
        "signal_state": signal_state,
        "daily_asset_return": round(daily_asset_return, 10),
        "daily_strategy_return": round(daily_strategy_return, 10),
        "exposure": round(exposure, 6),
        "cash_weight": round(cash_weight, 6),
        "data_source": data_source,
        "data_quality": data_quality,
        **safety_flags(),
    }


def quality_row_from_stream(sleeve_name: str, candidate_name: str, rows: list[dict[str, Any]], alignment: str) -> dict[str, Any]:
    metrics = metrics_for_stream(rows)
    status = stream_status_for(sleeve_name)
    return {
        "sleeve_name": sleeve_name,
        "candidate_name": candidate_name,
        "stream_status": status,
        "row_count": len(rows),
        "start_date": rows[0]["date"] if rows else "",
        "end_date": rows[-1]["date"] if rows else "",
        "missing_return_count": sum(1 for row in rows if row.get("daily_strategy_return") in {"", None}),
        "data_source": rows[0]["data_source"] if rows else "missing_saved_data",
        "metric_alignment_status": alignment if sleeve_name == QQQ100_SLEEVE else "research_metrics_generated",
        "cagr": metrics["cagr"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
        "calmar": metrics["calmar"],
        "annual_volatility": metrics["annual_volatility"],
        "cash_percentage": metrics["cash_percentage"],
        "trade_count_or_signal_changes": signal_changes(rows),
        "blocker": "none" if rows else "missing_return_stream",
        "recommended_next_step": "Use saved stream in multi-sleeve portfolio backtest; do not approve execution.",
        **safety_flags(),
    }


def missing_quality_row(sleeve_name: str, candidate_name: str, status: str, blocker: str) -> dict[str, Any]:
    return {
        "sleeve_name": sleeve_name,
        "candidate_name": candidate_name,
        "stream_status": status,
        "row_count": 0,
        "start_date": "",
        "end_date": "",
        "missing_return_count": 0,
        "data_source": "missing_saved_data",
        "metric_alignment_status": "missing_return_stream",
        "cagr": MISSING,
        "sharpe": MISSING,
        "max_drawdown": MISSING,
        "calmar": MISSING,
        "annual_volatility": MISSING,
        "cash_percentage": MISSING,
        "trade_count_or_signal_changes": MISSING,
        "blocker": blocker,
        "recommended_next_step": "Collect a real saved daily return stream; do not invent returns from summary metrics.",
        **safety_flags(),
    }


def stream_status_for(sleeve_name: str) -> str:
    if sleeve_name == QQQ100_SLEEVE:
        return "qqq100_return_stream_created"
    if sleeve_name == "defensive_cash_or_bond_sleeve":
        return "cash_return_stream_created"
    if sleeve_name == "codex_experimental_research_sleeve":
        return "codex_experimental_stream_created"
    return "defensive_qqq_streams_created"


def metrics_for_stream(rows: list[dict[str, Any]]) -> dict[str, str]:
    if len(rows) < 2:
        return {key: MISSING for key in ["cagr", "sharpe", "max_drawdown", "calmar", "annual_volatility", "cash_percentage"]}
    returns = [float(row["daily_strategy_return"]) for row in rows]
    equity = 1.0
    curve = []
    for value in returns:
        equity *= 1.0 + value
        curve.append(equity)
    years = max(len(returns) / 252.0, 1 / 252.0)
    cagr = (equity ** (1.0 / years) - 1.0) * 100.0
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / max(1, len(returns) - 1)
    annual_vol = math.sqrt(variance) * math.sqrt(252.0) * 100.0
    sharpe = (mean / math.sqrt(variance) * math.sqrt(252.0)) if variance > 0 else 0.0
    maxdd = max_drawdown_pct(curve)
    calmar = cagr / abs(maxdd) if maxdd < 0 else 0.0
    cash = sum(float(row["cash_weight"]) for row in rows) / len(rows) * 100.0
    return {
        "cagr": str(round(cagr, 4)),
        "sharpe": str(round(sharpe, 4)),
        "max_drawdown": str(round(maxdd, 4)),
        "calmar": str(round(calmar, 4)),
        "annual_volatility": str(round(annual_vol, 4)),
        "cash_percentage": str(round(cash, 4)),
    }


def max_drawdown_pct(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value / peak - 1.0) * 100.0)
    return worst


def signal_changes(rows: list[dict[str, Any]]) -> int:
    changes = 0
    previous = None
    for row in rows:
        state = row.get("signal_state")
        if previous is not None and state != previous:
            changes += 1
        previous = state
    return changes


def build_summary_rows(final_status: str, generated: list[dict[str, Any]], missing: list[dict[str, Any]], quality: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qqq = next((row for row in quality if row["sleeve_name"] == QQQ100_SLEEVE), {})
    defensive = best_defensive_row(quality)
    items = [
        ("final_stream_status", final_status, "Return streams are generated where data exists and missing streams are labelled."),
        ("generated_sleeve_streams", ", ".join(row["candidate_name"] for row in generated) or "none", "Generated saved stream candidates."),
        ("missing_sleeve_streams", ", ".join(row["sleeve_name"] for row in missing) or "none", "Missing streams are explicit blockers."),
        ("qqq100_stream_metrics", format_quality_metrics(qqq), "QQQ100 generated stream metrics."),
        ("best_defensive_qqq_stream_candidate", defensive.get("candidate_name", "unavailable"), "Best defensive candidate by Calmar where available."),
        ("defensive_etf_stream_status", "missing_saved_data_cash_only", "Cash stream is available; defensive ETF proxy is not generated."),
        ("biggest_blocker", BIGGEST_BLOCKER, "High-growth and crypto daily streams are missing."),
        ("recommended_next_step", RECOMMENDED_NEXT_STEP, "Run the multi-sleeve portfolio backtest using saved stream rows."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def best_defensive_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if row["sleeve_name"] == "qqq_defensive_crash_gate_research_sleeve" and row["calmar"] != MISSING]
    if not candidates:
        return {}
    return max(candidates, key=lambda row: safe_float(row["calmar"]))


def format_quality_metrics(row: dict[str, Any]) -> str:
    if not row:
        return "missing"
    return f"CAGR={row.get('cagr')}; Sharpe={row.get('sharpe')}; MaxDD={row.get('max_drawdown')}; Calmar={row.get('calmar')}; alignment={row.get('metric_alignment_status')}"


def build_blocker_rows() -> list[dict[str, Any]]:
    blockers = [
        ("high_growth_stream_missing", "blocked", "high", "No saved daily high-growth return stream exists; summary metrics are not converted into daily returns.", "Build a real high-growth daily stream before inclusion."),
        ("crypto_stream_missing", "blocked", "high", "No reliable saved crypto daily return stream exists.", "Build a real crypto daily stream before inclusion."),
        ("qqq100_metric_alignment_needs_reconciliation", "warning", "medium", "Generated QQQ100 stream may not exactly match saved reference metrics without identical original backtest details.", "Compare generated stream metrics with saved QQQ100 reference."),
        ("execution_wiring_blocked", "blocked", "critical", "Return streams are research data only.", "Do not connect streams to order logic."),
        ("scheduling_not_approved", "blocked", "critical", "No scheduling, Hermes cron, service, loop, or Task Scheduler use is approved.", "Keep command manual/research-only."),
    ]
    return [{"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **safety_flags()} for name, status, severity, details, next_step in blockers]


def build_next_step_rows() -> list[dict[str, Any]]:
    steps = [
        ("rerun_multi_sleeve_portfolio_backtest_with_saved_streams", "recommended", "Use generated QQQ/cash/defensive streams to compute feasible reduced portfolio metrics."),
        ("reconcile_qqq100_metric_alignment", "required", "Compare QQQ100 generated stream metrics against saved reference metrics."),
        ("add_high_growth_daily_stream_only_if_real", "required", "Do not invent high-growth returns from summary metrics."),
        ("add_crypto_daily_stream_only_if_real", "required", "Do not invent crypto returns from summary metrics."),
        ("keep_execution_boundaries_false", "required", "Do not wire return streams to orders, QQQ100 execution, repeat execution, or scheduling."),
    ]
    return [{"step_name": name, "step_status": status, "details": details, "required_before_candidate_label_change": True, **safety_flags()} for name, status, details in steps]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "Sleeve return streams created. Research-only; no execution wiring approved.",
        f"final_stream_status: {summary['final_stream_status']}",
        f"generated sleeve streams: {summary['generated_sleeve_streams']}",
        f"missing sleeve streams: {summary['missing_sleeve_streams']}",
        f"QQQ100 stream metrics: {summary['qqq100_stream_metrics']}",
        f"best defensive QQQ stream candidate: {summary['best_defensive_qqq_stream_candidate']}",
        f"biggest blocker: {summary['biggest_blocker']}",
        f"recommended next step: {summary['recommended_next_step']}",
        f"Saved streams: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; qqq100_execution_approved=false; codex_experimental_execution_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def above_sma(rows: list[dict[str, Any]], index: int, window: int) -> bool:
    if index < window - 1:
        return False
    values = [float(row["close"]) for row in rows[index - window + 1 : index + 1]]
    return float(rows[index]["close"]) > (sum(values) / len(values))


def daily_return(rows: list[dict[str, Any]], index: int) -> float:
    previous = float(rows[index - 1]["close"])
    current = float(rows[index]["close"])
    if previous <= 0:
        return 0.0
    return (current / previous) - 1.0


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
