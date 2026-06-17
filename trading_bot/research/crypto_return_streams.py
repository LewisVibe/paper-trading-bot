"""Research-only crypto daily return streams for multi-sleeve research.

This module creates saved daily return streams for the existing BTC and ETH
crypto research candidates. It may fetch yfinance data for this research report
only, but it does not call Alpaca, read positions, create orders, write SQLite,
send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import crypto_lab as lab


STATUS_CREATED = "crypto_return_streams_created"
STATUS_PARTIAL_CREATED = "crypto_return_streams_partial_created"
STATUS_BLOCKED_NO_VALID_MARKET_DATA = "crypto_return_streams_blocked_no_valid_market_data"
STATUS_BLOCKED_MISSING_SAVED_CRYPTO_DECISION = "crypto_return_streams_blocked_missing_saved_crypto_decision"
STATUS_CREATED_RESEARCH_ONLY = "crypto_return_streams_created_research_only"
NEXT_STEP_MULTI_SLEEVE = "rerun_multi_sleeve_portfolio_backtest_with_crypto_streams_for_research_only_review"
NEXT_STEP_FIX_MARKET_DATA = "fix_crypto_market_data_or_saved_decision_before_multi_sleeve_backtest"
BIGGEST_BLOCKER = "crypto_streams_remain_research_only_not_preview_or_execution_approved"
PRICE_FIXTURE = Path("data/crypto_return_stream_price_fixture.csv")

BTC_SLEEVE = "btc_trend_vol_gate_research_sleeve"
ETH_SLEEVE = "eth_trend_research_sleeve"
COMBINED_SLEEVE = "crypto_btc_eth_research_sleeve"
CRYPTO_RESEARCH_SLEEVE = "crypto_research_sleeve"
PAUSED_LTC_DIAGNOSTIC = "paused_ltc_diagnostic"

ACTIVE_CANDIDATES = [
    {
        "symbol": "BTC/USD",
        "data_symbol": "BTC-USD",
        "sleeve_name": BTC_SLEEVE,
        "candidate_name": BTC_SLEEVE,
        "source_strategy": "crypto_buy_above_200_with_vol_gate",
        "rule_name": "close_above_200_vol_gate",
        "source_status": "btc_existing_crypto_research_candidate_useful_but_split_sensitive",
        "research_status": "btc_research_only_split_sensitive",
        "warning_status": "split_sensitivity_warning",
    },
    {
        "symbol": "ETH/USD",
        "data_symbol": "ETH-USD",
        "sleeve_name": ETH_SLEEVE,
        "candidate_name": ETH_SLEEVE,
        "source_strategy": "crypto_buy_above_200_exit_below_200",
        "rule_name": "close_above_200",
        "source_status": "eth_existing_crypto_research_candidate_useful_research_only",
        "research_status": "eth_research_only",
        "warning_status": "crypto_volatility_warning",
    },
]

OUTPUT_FILES = {
    "streams": Path("data/crypto_return_streams.csv"),
    "metrics": Path("data/crypto_return_stream_metrics.csv"),
    "summary": Path("data/crypto_return_stream_summary.csv"),
    "blockers": Path("data/crypto_return_stream_blockers.csv"),
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
    "crypto_execution_approved",
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
    "crypto_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

STREAM_COLUMNS = [
    "created_at",
    "date",
    "sleeve_name",
    "sleeve_family",
    "candidate_name",
    "symbol",
    "data_symbol",
    "daily_return",
    "daily_strategy_return",
    "equity",
    "exposure",
    "invested_flag",
    "signal_state",
    "source_strategy",
    "source_status",
    "research_status",
    "warning_status",
    "required_next_step",
    "cost_model_name",
    "crypto_taker_fee_bps",
    "crypto_spread_bps",
    "crypto_slippage_bps",
    "crypto_total_one_way_cost_bps",
    *SAFETY_COLUMNS,
]

METRIC_COLUMNS = [
    "created_at",
    "sleeve_name",
    "sleeve_family",
    "candidate_name",
    "symbol",
    "source_strategy",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "annual_volatility",
    "row_count",
    "first_date",
    "last_date",
    "invested_pct",
    "trade_count",
    "exposure_change_count",
    "source_status",
    "research_status",
    "warning_status",
    "required_next_step",
    "cost_model_name",
    "crypto_taker_fee_bps",
    "crypto_spread_bps",
    "crypto_slippage_bps",
    "crypto_total_one_way_cost_bps",
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
class CryptoReturnStreamsResult:
    output_paths: dict[str, Path]
    stream_rows: list[dict[str, Any]]
    metric_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_crypto_return_streams(root_dir: Path | str = ".") -> CryptoReturnStreamsResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cost_model = lab.CryptoResearchCostModel()
    price_data, data_errors, data_source = load_price_data(root)
    stream_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []

    for candidate in ACTIVE_CANDIDATES:
        rows = price_data.get(candidate["symbol"]) or price_data.get(candidate["data_symbol"]) or []
        normalized = lab.normalize_crypto_price_rows(rows)
        if len(normalized) < 205:
            metric_rows.append(missing_metric_row(created_at, candidate, data_source, data_errors, "not_enough_daily_history"))
            continue
        sleeve_rows = build_candidate_stream_rows(created_at, candidate, normalized, cost_model, data_source)
        stream_rows.extend(sleeve_rows)
        metric_rows.append(metric_row_from_stream(created_at, candidate, sleeve_rows, cost_model))

    combined_rows = build_combined_btc_eth_stream(created_at, stream_rows, cost_model)
    if combined_rows:
        stream_rows.extend(combined_rows)
        metric_rows.append(combined_metric_row(created_at, combined_rows, cost_model))

    status = final_stream_status(stream_rows, data_errors)
    summary_rows = build_summary_rows(created_at, stream_rows, metric_rows, data_errors, data_source, status)
    blocker_rows = build_blocker_rows(created_at, data_errors, status)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["streams"], STREAM_COLUMNS, stream_rows)
    write_rows(output_paths["metrics"], METRIC_COLUMNS, metric_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return CryptoReturnStreamsResult(
        output_paths=output_paths,
        stream_rows=stream_rows,
        metric_rows=metric_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["streams"]),
    )


def show_crypto_return_streams(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    metrics_path = root / OUTPUT_FILES["metrics"]
    if not summary_path.exists() or not metrics_path.exists():
        return 1, [
            "Crypto return streams are missing.",
            "Run `python bot.py --crypto-return-streams` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = {row.get("summary_name", ""): row.get("summary_value", "") for row in read_csv_rows(summary_path)}
    return 0, [
        "Crypto return streams. Research-only saved daily streams; no crypto execution wiring approved.",
        f"final crypto stream status: {summary.get('final_stream_status', 'missing')}",
        f"stream count: {summary.get('generated_stream_count', 'missing')}",
        f"active crypto sleeves: {summary.get('active_crypto_sleeves', 'missing')}",
        f"metrics summary: {summary.get('candidate_metrics', 'missing')}",
        f"BTC status: {summary.get('btc_status', 'missing')}",
        f"ETH status: {summary.get('eth_status', 'missing')}",
        f"LTC status: {summary.get('ltc_status', 'paused_ltc_diagnostic_not_active')}",
        f"warnings / blockers: {summary.get('warnings', 'missing')}",
        f"required next step: {summary.get('recommended_next_step', NEXT_STEP_MULTI_SLEEVE)}",
        "execution_approved=false; paper_execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def load_price_data(root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str], str]:
    fixture = root / PRICE_FIXTURE
    if fixture.exists():
        return load_fixture_prices(fixture), {}, "saved_price_fixture"
    price_data: dict[str, list[dict[str, Any]]] = {}
    data_errors: dict[str, str] = {}
    try:
        from trading_bot.market_data import configure_yfinance_cache_location

        configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    except ModuleNotFoundError as exc:
        if exc.name == "yfinance":
            return {}, {candidate["symbol"]: "yfinance unavailable" for candidate in ACTIVE_CANDIDATES}, "yfinance_unavailable"
        raise
    for candidate in ACTIVE_CANDIDATES:
        try:
            rows = lab.download_crypto_daily_history(candidate["data_symbol"])
            price_data[candidate["symbol"]] = rows
        except Exception as exc:  # yfinance/provider failures are recorded per ticker.
            data_errors[candidate["symbol"]] = sanitize_error(exc)
    return price_data, data_errors, "yfinance_research_download"


def load_fixture_prices(path: Path) -> dict[str, list[dict[str, Any]]]:
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for row in read_csv_rows(path):
        symbol = str(row.get("symbol") or row.get("ticker") or row.get("data_symbol") or "").upper()
        if symbol in {"BTC-USD", "BTC/USD"}:
            key = "BTC/USD"
        elif symbol in {"ETH-USD", "ETH/USD"}:
            key = "ETH/USD"
        else:
            continue
        try:
            close = float(row.get("close") or row.get("adj_close") or row.get("adjusted_close"))
        except (TypeError, ValueError):
            continue
        if close <= 0:
            continue
        by_symbol.setdefault(key, []).append({"date": row.get("date", ""), "close": close})
    for rows in by_symbol.values():
        rows.sort(key=lambda item: str(item["date"]))
    return by_symbol


def build_candidate_stream_rows(
    created_at: str,
    candidate: dict[str, str],
    rows: list[dict[str, Any]],
    cost_model: lab.CryptoResearchCostModel,
    data_source: str,
) -> list[dict[str, Any]]:
    equity_curve, trades = lab.simulate_crypto_strategy(
        candidate["source_strategy"],
        rows,
        created_at,
        candidate["symbol"],
        candidate["data_symbol"],
        cost_model,
    )
    exposures = exposure_series(candidate["rule_name"], rows)
    output: list[dict[str, Any]] = []
    previous_equity: float | None = None
    for index, point in enumerate(equity_curve):
        equity = float(point.get("equity", 0.0) or 0.0)
        daily_return = 0.0 if previous_equity in {None, 0.0} else equity / float(previous_equity) - 1.0
        exposure = exposures[index] if index < len(exposures) else 0.0
        output.append(
            {
                "created_at": created_at,
                "date": point.get("date", ""),
                "sleeve_name": candidate["sleeve_name"],
                "sleeve_family": "crypto",
                "candidate_name": candidate["candidate_name"],
                "symbol": candidate["symbol"],
                "data_symbol": candidate["data_symbol"],
                "daily_return": round(daily_return, 10),
                "daily_strategy_return": round(daily_return, 10),
                "equity": round(equity, 6),
                "exposure": round(exposure, 6),
                "invested_flag": exposure > 0,
                "signal_state": "crypto_long" if exposure > 0 else "crypto_flat",
                "source_strategy": candidate["source_strategy"],
                "source_status": f"{candidate['source_status']}; data_source={data_source}",
                "research_status": candidate["research_status"],
                "warning_status": candidate["warning_status"],
                "required_next_step": NEXT_STEP_MULTI_SLEEVE,
                **cost_fields(cost_model),
                **safety_flags(),
            }
        )
        previous_equity = equity
    return output


def exposure_series(rule_name: str, rows: list[dict[str, Any]]) -> list[float]:
    closes = [float(row["close"]) for row in rows]
    sma_50 = lab.rolling_average(closes, 50)
    sma_200 = lab.rolling_average(closes, 200)
    realized_vol_20 = lab.rolling_realized_volatility(closes, 20)
    realized_vol_20_median_252 = lab.rolling_median(realized_vol_20, 252)
    exposures: list[float] = []
    already_long = False
    for index, row in enumerate(rows):
        desired_long = lab.crypto_desired_long(
            rule_name,
            float(row["close"]),
            sma_50[index],
            sma_200[index],
            realized_vol_20[index],
            realized_vol_20_median_252[index],
            already_long,
        )
        exposures.append(1.0 if desired_long else 0.0)
        already_long = desired_long
    return exposures


def build_combined_btc_eth_stream(
    created_at: str,
    rows: list[dict[str, Any]],
    cost_model: lab.CryptoResearchCostModel,
) -> list[dict[str, Any]]:
    by_sleeve: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_sleeve.setdefault(str(row["sleeve_name"]), {})[str(row["date"])] = row
    btc = by_sleeve.get(BTC_SLEEVE, {})
    eth = by_sleeve.get(ETH_SLEEVE, {})
    common_dates = sorted(set(btc) & set(eth))
    if len(common_dates) < 2:
        return []
    equity = 1.0
    output = []
    for date in common_dates:
        btc_return = safe_float(btc[date].get("daily_strategy_return"), 0.0)
        eth_return = safe_float(eth[date].get("daily_strategy_return"), 0.0)
        daily_return = (btc_return + eth_return) / 2.0
        equity *= 1.0 + daily_return
        exposure = (safe_float(btc[date].get("exposure"), 0.0) + safe_float(eth[date].get("exposure"), 0.0)) / 2.0
        output.append(
            {
                "created_at": created_at,
                "date": date,
                "sleeve_name": CRYPTO_RESEARCH_SLEEVE,
                "sleeve_family": "crypto",
                "candidate_name": COMBINED_SLEEVE,
                "symbol": "BTC/USD+ETH/USD",
                "data_symbol": "BTC-USD+ETH-USD",
                "daily_return": round(daily_return, 10),
                "daily_strategy_return": round(daily_return, 10),
                "equity": round(equity, 6),
                "exposure": round(exposure, 6),
                "invested_flag": exposure > 0,
                "signal_state": "crypto_weighted_long" if exposure > 0 else "crypto_flat",
                "source_strategy": "btc_eth_equal_weight_saved_research_stream",
                "source_status": "combined_from_btc_eth_saved_return_streams",
                "research_status": "crypto_btc_eth_research_only",
                "warning_status": "crypto_volatility_and_split_sensitivity_warning",
                "required_next_step": NEXT_STEP_MULTI_SLEEVE,
                **cost_fields(cost_model),
                **safety_flags(),
            }
        )
    return output


def metric_row_from_stream(
    created_at: str,
    candidate: dict[str, str],
    rows: list[dict[str, Any]],
    cost_model: lab.CryptoResearchCostModel,
) -> dict[str, Any]:
    return metric_row(
        created_at,
        candidate["sleeve_name"],
        candidate["candidate_name"],
        candidate["symbol"],
        candidate["source_strategy"],
        rows,
        candidate["source_status"],
        candidate["research_status"],
        candidate["warning_status"],
        cost_model,
    )


def combined_metric_row(
    created_at: str,
    rows: list[dict[str, Any]],
    cost_model: lab.CryptoResearchCostModel,
) -> dict[str, Any]:
    return metric_row(
        created_at,
        CRYPTO_RESEARCH_SLEEVE,
        COMBINED_SLEEVE,
        "BTC/USD+ETH/USD",
        "btc_eth_equal_weight_saved_research_stream",
        rows,
        "combined_from_btc_eth_saved_return_streams",
        "crypto_btc_eth_research_only",
        "crypto_volatility_and_split_sensitivity_warning",
        cost_model,
    )


def metric_row(
    created_at: str,
    sleeve_name: str,
    candidate_name: str,
    symbol: str,
    source_strategy: str,
    rows: list[dict[str, Any]],
    source_status: str,
    research_status: str,
    warning_status: str,
    cost_model: lab.CryptoResearchCostModel,
) -> dict[str, Any]:
    returns = [safe_float(row.get("daily_strategy_return"), 0.0) for row in rows]
    equities = [safe_float(row.get("equity"), 0.0) for row in rows]
    metrics = metrics_for_returns(returns, equities)
    exposure_changes = exposure_change_count(rows)
    return {
        "created_at": created_at,
        "sleeve_name": sleeve_name,
        "sleeve_family": "crypto",
        "candidate_name": candidate_name,
        "symbol": symbol,
        "source_strategy": source_strategy,
        "CAGR": metrics["CAGR"],
        "Sharpe": metrics["Sharpe"],
        "MaxDD": metrics["MaxDD"],
        "Calmar": metrics["Calmar"],
        "annual_volatility": metrics["annual_volatility"],
        "row_count": len(rows),
        "first_date": rows[0]["date"] if rows else "",
        "last_date": rows[-1]["date"] if rows else "",
        "invested_pct": round(100.0 * sum(1 for row in rows if truthy(row.get("invested_flag"))) / len(rows), 4) if rows else 0.0,
        "trade_count": exposure_changes,
        "exposure_change_count": exposure_changes,
        "source_status": source_status,
        "research_status": research_status,
        "warning_status": warning_status,
        "required_next_step": NEXT_STEP_MULTI_SLEEVE,
        **cost_fields(cost_model),
        **safety_flags(),
    }


def missing_metric_row(
    created_at: str,
    candidate: dict[str, str],
    data_source: str,
    data_errors: dict[str, str],
    source_status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "sleeve_name": candidate["sleeve_name"],
        "sleeve_family": "crypto",
        "candidate_name": candidate["candidate_name"],
        "symbol": candidate["symbol"],
        "source_strategy": candidate["source_strategy"],
        "CAGR": "missing_saved_metrics",
        "Sharpe": "missing_saved_metrics",
        "MaxDD": "missing_saved_metrics",
        "Calmar": "missing_saved_metrics",
        "annual_volatility": "missing_saved_metrics",
        "row_count": 0,
        "first_date": "",
        "last_date": "",
        "invested_pct": 0,
        "trade_count": 0,
        "exposure_change_count": 0,
        "source_status": f"{source_status}; data_source={data_source}; errors={len(data_errors)}",
        "research_status": "data_unavailable_research_only",
        "warning_status": "market_data_gap",
        "required_next_step": NEXT_STEP_FIX_MARKET_DATA,
        **cost_fields(lab.CryptoResearchCostModel()),
        **safety_flags(),
    }


def metrics_for_returns(returns: list[float], equities: list[float]) -> dict[str, str]:
    valid_returns = returns[1:] if len(returns) > 1 else returns
    if not returns or not equities or equities[0] <= 0 or equities[-1] <= 0:
        return {"CAGR": "0.0", "Sharpe": "0.0", "MaxDD": "0.0", "Calmar": "0.0", "annual_volatility": "0.0"}
    years = max(len(returns) / 365.0, 1 / 365.0)
    cagr = ((equities[-1] / equities[0]) ** (1.0 / years) - 1.0) * 100.0
    mean_return = sum(valid_returns) / len(valid_returns) if valid_returns else 0.0
    variance = (
        sum((value - mean_return) ** 2 for value in valid_returns) / max(1, len(valid_returns) - 1)
        if valid_returns
        else 0.0
    )
    annual_vol = math.sqrt(variance) * math.sqrt(365.0) * 100.0 if variance > 0 else 0.0
    sharpe = (mean_return / math.sqrt(variance) * math.sqrt(365.0)) if variance > 0 else 0.0
    maxdd = max_drawdown_pct(equities)
    calmar = cagr / abs(maxdd) if maxdd < 0 else 0.0
    return {
        "CAGR": str(round(cagr, 4)),
        "Sharpe": str(round(sharpe, 4)),
        "MaxDD": str(round(maxdd, 4)),
        "Calmar": str(round(calmar, 4)),
        "annual_volatility": str(round(annual_vol, 4)),
    }


def max_drawdown_pct(curve: list[float]) -> float:
    if not curve:
        return 0.0
    peak = curve[0]
    worst = 0.0
    for value in curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value / peak - 1.0) * 100.0)
    return worst


def exposure_change_count(rows: list[dict[str, Any]]) -> int:
    changes = 0
    previous: str | None = None
    for row in rows:
        state = str(row.get("signal_state", ""))
        if previous is not None and state != previous:
            changes += 1
        previous = state
    return changes


def build_summary_rows(
    created_at: str,
    streams: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    data_errors: dict[str, str],
    data_source: str,
    status: str,
) -> list[dict[str, Any]]:
    generated = [row for row in metrics if int(safe_float(row.get("row_count"), 0)) > 0]
    metric_by_candidate = {row.get("candidate_name"): row for row in metrics}
    items = [
        ("final_stream_status", status, "Crypto streams are saved research data only and do not approve crypto execution."),
        ("generated_stream_count", str(len({row.get("candidate_name") for row in streams})), "Number of active crypto sleeve streams with daily rows."),
        ("active_crypto_sleeves", ", ".join(sorted({str(row.get("sleeve_name")) for row in streams})) or "none", "Active BTC/ETH/combined crypto sleeves only; LTC remains paused."),
        ("candidate_metrics", format_metric_rows(generated or metrics), "Saved daily stream metrics."),
        ("btc_status", candidate_summary(metric_by_candidate.get(BTC_SLEEVE)), "BTC uses the existing split-sensitive volatility-gated research candidate."),
        ("eth_status", candidate_summary(metric_by_candidate.get(ETH_SLEEVE)), "ETH uses the existing above-SMA200 research candidate."),
        ("ltc_status", f"{PAUSED_LTC_DIAGNOSTIC}=not_active_not_useful_pause", "LTC is not included as an active sleeve."),
        ("cost_assumptions", "crypto_taker_fee_bps=10; crypto_spread_bps=5; crypto_slippage_bps=10", "Existing crypto research cost assumptions from crypto_lab.CryptoResearchCostModel."),
        ("warnings", "crypto_volatility; split_sensitivity; crypto_research_only; no_crypto_execution", "Crypto remains high volatility and research-only."),
        ("data_source", data_source, "Research data source used for generation."),
        ("data_errors", f"crypto_symbol_errors={len(data_errors)}", "; ".join(f"{key}={value}" for key, value in sorted(data_errors.items()))[:500]),
        ("biggest_blocker", BIGGEST_BLOCKER, "Crypto streams do not approve preview, execution, scheduling, margin, leverage, or shorting."),
        ("recommended_next_step", NEXT_STEP_MULTI_SLEEVE if streams else NEXT_STEP_FIX_MARKET_DATA, "Use streams only for multi-sleeve research review."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(
    created_at: str,
    data_errors: dict[str, str],
    status: str,
) -> list[dict[str, Any]]:
    blockers = [
        (BIGGEST_BLOCKER, "blocked", "high", "Crypto streams are research-only and cannot approve preview, execution, or scheduling.", NEXT_STEP_MULTI_SLEEVE),
        ("ltc_paused_not_active", "pass", "medium", "LTC/USD remains paused/not useful and is not emitted as an active sleeve.", "Keep LTC out of active multi-sleeve candidates."),
        ("market_data_errors", "blocked" if status == STATUS_BLOCKED_NO_VALID_MARKET_DATA else ("warning" if data_errors else "pass"), "high", f"crypto_symbol_errors={len(data_errors)}", NEXT_STEP_FIX_MARKET_DATA if data_errors else NEXT_STEP_MULTI_SLEEVE),
        ("execution_wiring_blocked", "blocked", "critical", "No Alpaca, order, position, SQLite, alert, scheduling, Hermes, shorting, margin, leverage, or live-trading path is approved.", "Keep crypto as saved research streams only."),
    ]
    return [
        {
            "created_at": created_at,
            "blocker_name": name,
            "status": row_status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **safety_flags(),
        }
        for name, row_status, severity, details, next_step in blockers
    ]


def final_stream_status(streams: list[dict[str, Any]], data_errors: dict[str, str]) -> str:
    generated = {row.get("candidate_name") for row in streams}
    has_btc = BTC_SLEEVE in generated
    has_eth = ETH_SLEEVE in generated
    has_combined = COMBINED_SLEEVE in generated
    if has_btc and has_eth and has_combined:
        return STATUS_CREATED_RESEARCH_ONLY
    if has_btc or has_eth:
        return STATUS_PARTIAL_CREATED
    if data_errors:
        return STATUS_BLOCKED_NO_VALID_MARKET_DATA
    return STATUS_BLOCKED_MISSING_SAVED_CRYPTO_DECISION


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "Crypto return streams created. Research-only saved daily streams; no execution wiring approved.",
        f"final crypto stream status: {summary['final_stream_status']}",
        f"stream count: {summary['generated_stream_count']}",
        f"active crypto sleeves: {summary['active_crypto_sleeves']}",
        f"metrics summary: {summary['candidate_metrics']}",
        f"BTC status: {summary['btc_status']}",
        f"ETH status: {summary['eth_status']}",
        f"LTC status: {summary['ltc_status']}",
        f"warnings / blockers: {summary['warnings']}",
        f"recommended next step: {summary['recommended_next_step']}",
        f"Saved streams: {output_path}",
        "execution_approved=false; paper_execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def format_metric_rows(rows: list[dict[str, Any]]) -> str:
    return " | ".join(format_metric_row(row) for row in rows) or "none"


def format_metric_row(row: dict[str, Any]) -> str:
    if not row:
        return "none"
    return (
        f"{row.get('candidate_name')}: CAGR={row.get('CAGR')}; Sharpe={row.get('Sharpe')}; "
        f"MaxDD={row.get('MaxDD')}; Calmar={row.get('Calmar')}; rows={row.get('row_count')}"
    )


def candidate_summary(row: dict[str, Any] | None) -> str:
    if not row:
        return "missing_stream"
    return f"{row.get('candidate_name')}={row.get('research_status')}; rows={row.get('row_count')}; warning={row.get('warning_status')}"


def cost_fields(cost_model: lab.CryptoResearchCostModel) -> dict[str, Any]:
    return {
        "cost_model_name": cost_model.name,
        "crypto_taker_fee_bps": cost_model.taker_fee_bps,
        "crypto_spread_bps": cost_model.spread_bps,
        "crypto_slippage_bps": cost_model.slippage_bps,
        "crypto_total_one_way_cost_bps": cost_model.total_one_way_cost_bps,
    }


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def truthy(value: Any) -> bool:
    return str(value).lower() == "true" or value is True


def safe_float(value: Any, default: float = float("-inf")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def sanitize_error(exc: Exception) -> str:
    text = str(exc).replace("\n", " ").replace("\r", " ")
    return text[:180] or exc.__class__.__name__


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
