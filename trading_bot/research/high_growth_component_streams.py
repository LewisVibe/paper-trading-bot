"""Research-only component streams for the high-growth sleeve."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import high_growth_return_streams as return_streams
from trading_bot.research import high_growth_stock_drawdown_control as drawdown_control
from trading_bot.research import high_growth_stock_lab as lab


SELECTED_SLEEVE = "codex_broad_growth_balanced_breakout_control"
SLEEVE_NAME = SELECTED_SLEEVE
WEIGHTING_METHOD = "equal_weight_component_sleeve"
ATTRIBUTION_CONFIDENCE = "approximate_from_reconstructed_research_stream"

STATUS_CREATED = "high_growth_component_streams_created_research_only"
STATUS_PARTIAL = "high_growth_component_streams_partial_manual_review_required"
STATUS_BLOCKED_HOLDINGS = "high_growth_component_streams_blocked_missing_reconstructable_holdings"
STATUS_BLOCKED_MARKET_DATA = "high_growth_component_streams_blocked_market_data_unavailable"

NEXT_REVIEW = "rerun_high_growth_component_attribution_after_component_streams"
NEXT_MARKET_DATA = "fix_high_growth_market_data_before_component_stream_builder"
NEXT_HOLDINGS = "review_high_growth_simulation_holding_reconstruction_before_component_streams"

INPUT_PRICE_FIXTURE = return_streams.PRICE_FIXTURE

OUTPUT_FILES = {
    "streams": Path("data/high_growth_component_streams.csv"),
    "summary": Path("data/high_growth_component_streams_summary.csv"),
    "blockers": Path("data/high_growth_component_streams_blockers.csv"),
    "drawdown_contributions": Path("data/high_growth_component_drawdown_contributions.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "preview_only",
    "component_stream_only",
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
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": True,
    "component_stream_only": True,
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
    "crypto_execution_approved": False,
    "live_trading_approved": False,
    "scheduling_approved": False,
    "shorting_approved": False,
    "leverage_approved": False,
    "margin_approved": False,
}

STREAM_COLUMNS = [
    "created_at",
    "date",
    "sleeve_name",
    "selected_sleeve",
    "component_ticker",
    "component_role",
    "selection_reason",
    "component_weight",
    "component_return",
    "weighted_contribution",
    "close_or_return_source",
    "weighting_method",
    "attribution_confidence",
    "regime_status",
    "data_source",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "blocker_severity",
    "blocker_detail",
    "required_next_step",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
]

DRAWDOWN_COLUMNS = [
    "created_at",
    "drawdown_start",
    "drawdown_trough",
    "component_ticker",
    "component_period_return",
    "component_weighted_contribution",
    "contribution_share_of_high_growth_drawdown",
    "drawdown_contribution_status",
    *SAFETY_COLUMNS,
]


@dataclass
class HighGrowthComponentStreamsResult:
    output_paths: dict[str, Path]
    stream_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_component_streams(root_dir: Path | str = ".") -> HighGrowthComponentStreamsResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    price_data, data_errors, data_source = return_streams.load_price_data(root)
    simulation = selected_simulation(price_data, data_errors)
    if simulation is None or simulation.data_status != "ok":
        status = STATUS_BLOCKED_MARKET_DATA
        stream_rows: list[dict[str, Any]] = []
        drawdown_rows: list[dict[str, Any]] = []
    else:
        stream_rows = component_rows_from_simulation(created_at, simulation, price_data, data_source)
        drawdown_rows = drawdown_contribution_rows(created_at, stream_rows)
        status = final_status(stream_rows, drawdown_rows)
    summary_rows = build_summary_rows(created_at, status, stream_rows, drawdown_rows, data_errors, data_source)
    blocker_rows = build_blocker_rows(created_at, status, stream_rows, drawdown_rows, data_errors, data_source)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["streams"], STREAM_COLUMNS, stream_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    if drawdown_rows:
        write_rows(output_paths["drawdown_contributions"], DRAWDOWN_COLUMNS, drawdown_rows)
    return HighGrowthComponentStreamsResult(
        output_paths=output_paths,
        stream_rows=stream_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        drawdown_rows=drawdown_rows,
        summary_lines=summary_lines(summary_rows, output_paths["streams"]),
    )


def show_high_growth_component_streams(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "High-growth component streams are missing.",
            "Run `python bot.py --high-growth-component-streams` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "High-growth component streams. Research-only component rows; no execution path.",
        f"component stream status: {summary.get('component_stream_status', 'missing')}",
        f"selected sleeve: {summary.get('selected_sleeve', 'missing')}",
        f"row count: {summary.get('component_rows', 'missing')}",
        f"unique ticker count: {summary.get('unique_tickers', 'missing')}",
        f"date range: {summary.get('first_date', 'missing')} -> {summary.get('last_date', 'missing')}",
        f"average active components: {summary.get('average_active_components', 'missing')}",
        f"max component weight: {summary.get('max_component_weight', 'missing')}",
        f"top contribution ticker: {summary.get('top_contribution_ticker', 'missing')}",
        f"worst contribution ticker: {summary.get('worst_contribution_ticker', 'missing')}",
        f"concentration data available: {summary.get('concentration_data_available', 'missing')}",
        f"required next step: {summary.get('required_next_step', 'missing')}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def selected_simulation(
    price_data: dict[str, list[dict[str, Any]]],
    data_errors: dict[str, str],
) -> lab.StrategySimulation | None:
    simulations = drawdown_control.build_simulations(price_data, data_errors)
    return next((simulation for simulation in simulations if simulation.name == SELECTED_SLEEVE), None)


def component_rows_from_simulation(
    created_at: str,
    simulation: lab.StrategySimulation,
    price_data: dict[str, list[dict[str, Any]]],
    data_source: str,
) -> list[dict[str, Any]]:
    trades_by_date = {str(trade.get("rebalance_date")): trade for trade in simulation.trades}
    current_weights: dict[str, float] = {}
    previous_prices: dict[str, float] = {}
    reason = "initial_no_component_selection"
    regime = "initial"
    rows: list[dict[str, Any]] = []
    for point in simulation.curve:
        date = str(point.get("date", ""))
        if current_weights and previous_prices:
            for ticker, weight in sorted(current_weights.items()):
                current_price = lab.price_on(price_data.get(ticker, []), date)
                prior = previous_prices.get(ticker, current_price)
                component_return = current_price / prior - 1.0 if prior > 0 else 0.0
                rows.append(
                    {
                        "created_at": created_at,
                        "date": date,
                        "sleeve_name": SLEEVE_NAME,
                        "selected_sleeve": SELECTED_SLEEVE,
                        "component_ticker": ticker,
                        "component_role": "high_growth_component_holding",
                        "selection_reason": reason,
                        "component_weight": round(weight, 6),
                        "component_return": round(component_return, 10),
                        "weighted_contribution": round(weight * component_return, 10),
                        "close_or_return_source": "reconstructed_from_research_price_history",
                        "weighting_method": WEIGHTING_METHOD,
                        "attribution_confidence": ATTRIBUTION_CONFIDENCE,
                        "regime_status": regime,
                        "data_source": data_source,
                        "required_next_step": NEXT_REVIEW,
                        **safety_flags(),
                    }
                )
        if date in trades_by_date:
            trade = trades_by_date[date]
            current_weights = parse_weights(str(trade.get("weights", "")))
            reason = str(trade.get("reason", "reconstructed_rebalance_selection"))
            regime = str(trade.get("regime_status", "reconstructed_regime"))
        previous_prices = {ticker: lab.price_on(price_data.get(ticker, []), date) for ticker in current_weights}
    return rows


def parse_weights(value: str) -> dict[str, float]:
    if not value or value == "cash":
        return {}
    weights: dict[str, float] = {}
    for token in value.split(";"):
        if ":" not in token:
            continue
        ticker, weight = token.split(":", 1)
        try:
            parsed = float(weight)
        except ValueError:
            continue
        if parsed >= 0:
            weights[ticker] = parsed
    return weights


def drawdown_contribution_rows(created_at: str, stream_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not stream_rows:
        return []
    daily = daily_sleeve_returns(stream_rows)
    if not daily:
        return []
    window = drawdown_window(sorted(daily), [daily[date] for date in sorted(daily)])
    start = str(window["start"])
    trough = str(window["trough"])
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in stream_rows:
        row_date = str(row.get("date", ""))
        if start <= row_date <= trough:
            grouped.setdefault(str(row.get("component_ticker", "")), []).append(row)
    total_abs = sum(abs(sum(parse_float(row.get("weighted_contribution")) for row in rows)) for rows in grouped.values()) or 0.0
    output = []
    for ticker, rows in sorted(grouped.items()):
        weighted = sum(parse_float(row.get("weighted_contribution")) for row in rows)
        period_return = compound(parse_float(row.get("component_return")) for row in rows) * 100.0
        share = abs(weighted) / total_abs * 100.0 if total_abs else 0.0
        output.append(
            {
                "created_at": created_at,
                "drawdown_start": start,
                "drawdown_trough": trough,
                "component_ticker": ticker,
                "component_period_return": rounded(period_return),
                "component_weighted_contribution": rounded(weighted),
                "contribution_share_of_high_growth_drawdown": rounded(share),
                "drawdown_contribution_status": "component_drawdown_contribution_available_research_only",
                **safety_flags(),
            }
        )
    return output


def daily_sleeve_returns(rows: list[dict[str, Any]]) -> dict[str, float]:
    daily: dict[str, float] = {}
    for row in rows:
        date = str(row.get("date", ""))
        daily[date] = daily.get(date, 0.0) + parse_float(row.get("weighted_contribution"))
    return daily


def drawdown_window(dates: list[str], returns: list[float]) -> dict[str, Any]:
    equity = 1.0
    peak = 1.0
    peak_index = 0
    worst = {"start": dates[0], "trough": dates[0], "maxdd": 0.0}
    for index, value in enumerate(returns):
        equity *= 1.0 + value
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = (equity / peak - 1.0) * 100.0 if peak else 0.0
        if drawdown < worst["maxdd"]:
            worst = {"start": dates[peak_index], "trough": dates[index], "maxdd": drawdown}
    return worst


def final_status(stream_rows: list[dict[str, Any]], drawdown_rows: list[dict[str, Any]]) -> str:
    if not stream_rows:
        return STATUS_BLOCKED_HOLDINGS
    if not drawdown_rows:
        return STATUS_PARTIAL
    return STATUS_CREATED


def build_summary_rows(
    created_at: str,
    status: str,
    stream_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
    data_source: str,
) -> list[dict[str, Any]]:
    dates = sorted({str(row.get("date")) for row in stream_rows if row.get("date")})
    tickers = sorted({str(row.get("component_ticker")) for row in stream_rows if row.get("component_ticker")})
    active_counts = active_component_counts(stream_rows)
    top = top_contributor(stream_rows, reverse=True)
    worst = top_contributor(stream_rows, reverse=False)
    items = [
        ("component_stream_status", status, "Research-only component stream status."),
        ("selected_sleeve", SELECTED_SLEEVE, "Selected high-growth sleeve."),
        ("component_rows", str(len(stream_rows)), "Daily component rows written."),
        ("unique_tickers", str(len(tickers)), "Unique component tickers."),
        ("first_date", dates[0] if dates else "", "First component row date."),
        ("last_date", dates[-1] if dates else "", "Last component row date."),
        ("max_component_weight", rounded(max((parse_float(row.get("component_weight")) for row in stream_rows), default=0.0)), "Maximum component weight as fraction."),
        ("average_active_components", rounded(sum(active_counts.values()) / len(active_counts)) if active_counts else "0.0", "Average active components per day."),
        ("max_active_components", str(max(active_counts.values(), default=0)), "Maximum active components on any day."),
        ("min_active_components", str(min(active_counts.values(), default=0)), "Minimum active components on component-row days."),
        ("top_weight_ticker", top_weight_ticker(stream_rows), "Ticker with highest observed component weight."),
        ("top_contribution_ticker", top, "Ticker with largest positive weighted contribution."),
        ("worst_contribution_ticker", worst, "Ticker with most negative weighted contribution."),
        ("concentration_data_available", str(bool(stream_rows)).lower(), "Whether component ticker/weight/contribution rows exist."),
        ("drawdown_contribution_rows", str(len(drawdown_rows)), "Drawdown-window component contribution rows."),
        ("data_source", data_source, "Saved fixture or research market-data source."),
        ("market_data_errors", f"ticker_errors={len(data_errors)}", "Sanitized market-data issue count."),
        ("required_next_step", required_next_step(status), "Next research step only."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **summary_safety_flags()} for name, value, details in items]


def build_blocker_rows(
    created_at: str,
    status: str,
    stream_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
    data_errors: dict[str, str],
    data_source: str,
) -> list[dict[str, Any]]:
    rows = []
    if status == STATUS_BLOCKED_MARKET_DATA:
        rows.append(blocker_row(created_at, "high_growth_component_streams_blocked_market_data_unavailable", status, "high", f"component stream builder could not reconstruct selected sleeve from market data; source={data_source}; ticker_errors={len(data_errors)}", NEXT_MARKET_DATA))
    if status == STATUS_BLOCKED_HOLDINGS:
        rows.append(blocker_row(created_at, "high_growth_component_streams_blocked_missing_reconstructable_holdings", status, "high", "selected high-growth simulation did not expose reconstructable component holdings", NEXT_HOLDINGS))
    if not drawdown_rows:
        rows.append(blocker_row(created_at, "high_growth_component_drawdown_contributions_missing", "manual_review_required", "medium", "drawdown contribution rows require component stream rows across a reconstructed drawdown window", required_next_step(status)))
    rows.extend(
        [
            blocker_row(created_at, "execution_boundary", "blocked_non_executable_research_only", "high", "component streams are not order instructions", required_next_step(status)),
            blocker_row(created_at, "scheduling_boundary", "blocked_no_scheduling_change", "high", "component streams are not a schedule or cron change", required_next_step(status)),
        ]
    )
    return rows


def blocker_row(created_at: str, name: str, status: str, severity: str, detail: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "blocker_status": status,
        "blocker_severity": severity,
        "blocker_detail": detail,
        "required_next_step": next_step,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "scheduling_approved": False,
    }


def active_component_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        date = str(row.get("date", ""))
        counts[date] = counts.get(date, 0) + 1
    return counts


def top_weight_ticker(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "missing_component_rows"
    row = max(rows, key=lambda item: parse_float(item.get("component_weight")))
    return f"{row.get('component_ticker')}: max_weight={row.get('component_weight')}"


def top_contributor(rows: list[dict[str, Any]], reverse: bool) -> str:
    if not rows:
        return "missing_component_rows"
    totals: dict[str, float] = {}
    for row in rows:
        ticker = str(row.get("component_ticker", ""))
        totals[ticker] = totals.get(ticker, 0.0) + parse_float(row.get("weighted_contribution"))
    ticker, value = sorted(totals.items(), key=lambda item: item[1], reverse=reverse)[0]
    return f"{ticker}: weighted_contribution={rounded(value)}"


def required_next_step(status: str) -> str:
    if status == STATUS_BLOCKED_MARKET_DATA:
        return NEXT_MARKET_DATA
    if status == STATUS_BLOCKED_HOLDINGS:
        return NEXT_HOLDINGS
    return NEXT_REVIEW


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return [
        "High-growth component streams created. Research-only component rows; no execution path.",
        f"component stream status: {summary.get('component_stream_status', 'missing')}",
        f"selected sleeve: {summary.get('selected_sleeve', 'missing')}",
        f"row count: {summary.get('component_rows', 'missing')}",
        f"unique ticker count: {summary.get('unique_tickers', 'missing')}",
        f"date range: {summary.get('first_date', 'missing')} -> {summary.get('last_date', 'missing')}",
        f"average active components: {summary.get('average_active_components', 'missing')}",
        f"max component weight: {summary.get('max_component_weight', 'missing')}",
        f"top contribution ticker: {summary.get('top_contribution_ticker', 'missing')}",
        f"worst contribution ticker: {summary.get('worst_contribution_ticker', 'missing')}",
        f"concentration data available: {summary.get('concentration_data_available', 'missing')}",
        f"required next step: {summary.get('required_next_step', 'missing')}",
        f"Saved streams: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


def compound(values: Any) -> float:
    equity = 1.0
    for value in values:
        equity *= 1.0 + float(value)
    return equity - 1.0


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rounded(value: Any) -> str:
    return str(round(parse_float(value), 4))


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def summary_safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "live_trading_approved": False,
        "scheduling_approved": False,
    }


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
