"""Preview helpers for promoted research strategies.

This module prepares preview rows only. It does not submit orders, read paper
positions, write SQLite trade logs, or send alerts.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.strategies.breakout import (
    average_volume,
    is_252_day_high_breakout,
    rolling_high,
    simple_moving_average,
    volume_confirmation,
)


SUPPORTED_PREVIEW_STRATEGIES = {
    "sma_50_200_trend",
    "buy_above_200_exit_below_200",
    "fifty_two_week_high_breakout",
}
QQQ100_STRATEGY = "qqq_100_trend_gate"
QQQ100_TICKER = "QQQ"
QQQ100_SIGNAL_PATH = Path("data/qqq100_preview_signal_pack.csv")
HIGH_GROWTH_BRANCH = "codex_broad_growth_balanced_breakout_control"
QQQ150_REJECTED = "qqq_150_trend_gate"
BLOCKED_PROMOTED_PREVIEW_STRATEGIES = {
    QQQ100_STRATEGY,
    HIGH_GROWTH_BRANCH,
    QQQ150_REJECTED,
}

PROMOTED_PREVIEW_COLUMNS = [
    "created_at",
    "strategy_name",
    "strategy_family",
    "ticker",
    "signal_source",
    "latest_close",
    "signal",
    "desired_position",
    "reason",
    "regime_ticker",
    "regime_latest_close",
    "regime_sma_200",
    "regime_state",
    "close_sma_200",
    "distance_to_sma_200_pct",
    "trailing_252_high",
    "distance_to_252_high_pct",
    "volume",
    "volume_20_day_avg",
    "volume_confirmation",
    "diagnostic_warning",
    "sma_50",
    "sma_200",
    "sma_50_vs_200_state",
    "distance_sma_50_to_sma_200_pct",
    "close_above_sma_200",
    "trend_state",
    "promotion_status",
    "promotion_label",
    "required_next_step",
    "preview_candidate",
    "research_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
]


@dataclass
class PromotedStrategyPreviewResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def read_preview_candidates(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [
            row
            for row in reader
            if row.get("promotion_status") == "preview_candidate"
            and row.get("ticker_or_portfolio") == "portfolio"
            and row.get("strategy_name") not in BLOCKED_PROMOTED_PREVIEW_STRATEGIES
        ]


def unsupported_preview_row(
    created_at: str,
    candidate: dict[str, str],
    ticker: str,
    reason: str = "unsupported_preview_strategy",
    regime_ticker: str = "",
    regime_state: str = "unavailable",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": candidate.get("strategy_name", ""),
        "strategy_family": candidate.get("strategy_family", ""),
        "ticker": ticker,
        "signal_source": "promoted_strategy_preview",
        "latest_close": "",
        "signal": "SKIP",
        "desired_position": "unknown",
        "reason": reason,
        "regime_ticker": regime_ticker,
        "regime_latest_close": "",
        "regime_sma_200": "",
        "regime_state": regime_state,
        "close_sma_200": "",
        "distance_to_sma_200_pct": "",
        "trailing_252_high": "",
        "distance_to_252_high_pct": "",
        "volume": "",
        "volume_20_day_avg": "",
        "volume_confirmation": "",
        "diagnostic_warning": reason,
        "sma_50": "",
        "sma_200": "",
        "sma_50_vs_200_state": "",
        "distance_sma_50_to_sma_200_pct": "",
        "close_above_sma_200": "",
        "trend_state": "unknown",
        "promotion_status": candidate.get("promotion_status", ""),
        "promotion_label": reason,
        "required_next_step": candidate.get("required_next_step", ""),
        **preview_safety_flags(),
    }


def build_promoted_preview_rows(
    candidates: list[dict[str, str]],
    data_by_ticker: dict[str, Any],
    regime_ticker: str = "SPY",
    regime_price_data: Any | None = None,
    created_at: str | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    regime = regime_diagnostics(regime_ticker, regime_price_data)

    for candidate in candidates:
        strategy_name = candidate.get("strategy_name", "")
        if strategy_name not in SUPPORTED_PREVIEW_STRATEGIES:
            warnings.append(f"Unsupported preview strategy skipped: {strategy_name}")
            for ticker in data_by_ticker:
                rows.append(
                    unsupported_preview_row(
                        timestamp,
                        candidate,
                        ticker,
                        regime_ticker=regime["regime_ticker"],
                        regime_state=regime["regime_state"],
                    )
                )
            continue

        for ticker, price_data in data_by_ticker.items():
            try:
                rows.append(preview_strategy_for_ticker(timestamp, candidate, ticker, price_data, regime))
            except Exception as exc:
                warnings.append(f"{strategy_name} preview failed for {ticker}: {exc}")
                rows.append(
                    unsupported_preview_row(
                        timestamp,
                        candidate,
                        ticker,
                        reason=str(exc),
                        regime_ticker=regime["regime_ticker"],
                        regime_state=regime["regime_state"],
                    )
                )

    return rows, warnings


def preview_strategy_for_ticker(
    created_at: str,
    candidate: dict[str, str],
    ticker: str,
    price_data: Any,
    regime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    strategy_name = candidate.get("strategy_name", "")
    rows = price_rows(price_data)
    if len(rows) < 252:
        raise RuntimeError("not_enough_history_for_preview")

    latest_close = float(rows[-1]["close"])
    close_sma_200: float | str = ""
    distance_to_sma_200: float | str = ""
    sma_50: float | str = ""
    sma_200: float | str = ""
    sma_50_vs_200_state = ""
    distance_sma_50_to_sma_200: float | str = ""
    close_above_sma_200: bool | str = ""
    trailing_252: float | str = ""
    distance_to_252_high: float | str = ""
    latest_volume: float | str = round(float(rows[-1]["volume"]), 4)
    volume_20_avg: float | str = ""
    volume_ok: bool | str = ""
    diagnostic_warning = ""
    if strategy_name == "sma_50_200_trend":
        short_sma = simple_moving_average(rows, 50)
        long_sma = simple_moving_average(rows, 200)
        sma_50 = round(short_sma, 4)
        sma_200 = round(long_sma, 4)
        close_sma_200 = round(long_sma, 4)
        distance_to_sma_200 = pct_distance(latest_close, long_sma)
        distance_sma_50_to_sma_200 = pct_distance(short_sma, long_sma)
        close_above_sma_200 = latest_close > long_sma
        sma_50_vs_200_state = "bullish" if short_sma > long_sma else "bearish"
        trend_state = sma_50_vs_200_state
        desired_position = "long" if short_sma > long_sma else "flat"
        signal = "TARGET_LONG" if desired_position == "long" else "TARGET_FLAT"
        reason = f"50-day SMA {'above' if desired_position == 'long' else 'not above'} 200-day SMA"
    elif strategy_name == "buy_above_200_exit_below_200":
        long_sma = simple_moving_average(rows, 200)
        sma_200 = round(long_sma, 4)
        close_sma_200 = round(long_sma, 4)
        distance_to_sma_200 = pct_distance(latest_close, long_sma)
        close_above_sma_200 = latest_close > long_sma
        trend_state = "bullish" if latest_close > long_sma else "bearish"
        desired_position = "long" if latest_close > long_sma else "flat"
        signal = "TARGET_LONG" if desired_position == "long" else "TARGET_FLAT"
        reason = f"close {'above' if desired_position == 'long' else 'not above'} 200-day SMA"
    elif strategy_name == "fifty_two_week_high_breakout":
        trailing_252_value = rolling_high(rows, 252)
        trailing_252 = round(trailing_252_value, 4)
        distance_to_252_high = pct_distance(latest_close, trailing_252_value)
        if len(rows) >= 20:
            volume_avg = average_volume(rows, 20)
            volume_20_avg = round(volume_avg, 4)
            volume_ok = volume_confirmation(rows, 20)
        else:
            diagnostic_warning = "not_enough_volume_history"
        breakout_active = is_252_day_high_breakout(rows)
        trend_state = "breakout_active" if breakout_active else "no_breakout"
        desired_position = "long" if breakout_active else "flat"
        signal = "BREAKOUT_ACTIVE" if breakout_active else "HOLD"
        reason = "latest close reaches trailing 252-day high" if breakout_active else "latest close below trailing 252-day high"
    else:
        raise RuntimeError("unsupported_preview_strategy")

    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "strategy_family": candidate.get("strategy_family", ""),
        "ticker": ticker,
        "signal_source": "promoted_strategy_preview",
        "latest_close": round(latest_close, 4),
        "signal": signal,
        "desired_position": desired_position,
        "reason": reason,
        "regime_ticker": (regime or {}).get("regime_ticker", ""),
        "regime_latest_close": (regime or {}).get("regime_latest_close", ""),
        "regime_sma_200": (regime or {}).get("regime_sma_200", ""),
        "regime_state": (regime or {}).get("regime_state", "unavailable"),
        "close_sma_200": close_sma_200,
        "distance_to_sma_200_pct": distance_to_sma_200,
        "trailing_252_high": trailing_252,
        "distance_to_252_high_pct": distance_to_252_high,
        "volume": latest_volume,
        "volume_20_day_avg": volume_20_avg,
        "volume_confirmation": volume_ok,
        "diagnostic_warning": diagnostic_warning,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "sma_50_vs_200_state": sma_50_vs_200_state,
        "distance_sma_50_to_sma_200_pct": distance_sma_50_to_sma_200,
        "close_above_sma_200": close_above_sma_200,
        "trend_state": trend_state,
        "promotion_status": candidate.get("promotion_status", ""),
        "promotion_label": "legacy_promoted_preview_candidate",
        "required_next_step": candidate.get("required_next_step", ""),
        **preview_safety_flags(),
    }


def append_qqq100_promoted_preview_candidate(
    rows: list[dict[str, Any]],
    warnings: list[str],
    root_dir: Path | str = ".",
    created_at: str | None = None,
) -> None:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    row = build_qqq100_promoted_preview_row(timestamp, Path(root_dir) / QQQ100_SIGNAL_PATH)
    rows.append(row)
    if row.get("diagnostic_warning"):
        warnings.append(str(row["diagnostic_warning"]))


def build_qqq100_promoted_preview_row(created_at: str, signal_path: Path) -> dict[str, Any]:
    signal_rows = read_csv_rows(signal_path)
    if not signal_rows:
        return qqq100_missing_signal_row(created_at)
    signal = signal_rows[0]
    if signal.get("strategy_name") != QQQ100_STRATEGY or signal.get("ticker") != QQQ100_TICKER:
        row = qqq100_missing_signal_row(created_at)
        row["reason"] = "saved QQQ100 preview signal input does not match qqq_100_trend_gate / QQQ."
        row["diagnostic_warning"] = "invalid_qqq100_preview_signal_input"
        row["promotion_label"] = "missing_qqq100_preview_signal_input"
        return row
    data_status = str(signal.get("data_status", ""))
    ok = data_status == "ok"
    desired_position = normalize_desired_position(signal.get("desired_position", ""))
    if desired_position not in {"long", "flat"}:
        desired_position = "unknown"
    return {
        "created_at": created_at,
        "strategy_name": QQQ100_STRATEGY,
        "strategy_family": "qqq_trend_gate",
        "ticker": QQQ100_TICKER,
        "signal_source": "qqq100_preview_signal_pack",
        "latest_close": signal.get("latest_close", ""),
        "signal": "TARGET_LONG" if desired_position == "long" else ("TARGET_FLAT" if desired_position == "flat" else "SKIP"),
        "desired_position": desired_position,
        "reason": signal.get("signal_reason", "") or "Saved QQQ100 preview signal imported for promoted review.",
        "regime_ticker": "",
        "regime_latest_close": "",
        "regime_sma_200": "",
        "regime_state": "not_applicable_saved_qqq100_signal",
        "close_sma_200": "",
        "distance_to_sma_200_pct": "",
        "trailing_252_high": "",
        "distance_to_252_high_pct": "",
        "volume": "",
        "volume_20_day_avg": "",
        "volume_confirmation": "",
        "diagnostic_warning": "" if ok else f"qqq100_preview_signal_data_status={data_status or 'missing'}",
        "sma_50": "",
        "sma_200": "",
        "sma_50_vs_200_state": "",
        "distance_sma_50_to_sma_200_pct": "",
        "close_above_sma_200": "",
        "trend_state": signal.get("trend_state", ""),
        "promotion_status": "preview_candidate" if ok else "blocked_missing_or_invalid_signal",
        "promotion_label": (
            "qqq100_clean_lead_promoted_to_preview_review"
            if ok
            else "missing_qqq100_preview_signal_input"
        ),
        "required_next_step": (
            "Continue promoted preview review only; do not create execution wiring."
            if ok
            else "Run python bot.py --qqq100-preview-signal-pack before promoted preview review."
        ),
        **preview_safety_flags(),
    }


def qqq100_missing_signal_row(created_at: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": QQQ100_STRATEGY,
        "strategy_family": "qqq_trend_gate",
        "ticker": QQQ100_TICKER,
        "signal_source": "qqq100_preview_signal_pack",
        "latest_close": "",
        "signal": "SKIP",
        "desired_position": "unknown",
        "reason": "Missing saved QQQ100 preview signal input.",
        "regime_ticker": "",
        "regime_latest_close": "",
        "regime_sma_200": "",
        "regime_state": "not_applicable_saved_qqq100_signal",
        "close_sma_200": "",
        "distance_to_sma_200_pct": "",
        "trailing_252_high": "",
        "distance_to_252_high_pct": "",
        "volume": "",
        "volume_20_day_avg": "",
        "volume_confirmation": "",
        "diagnostic_warning": "missing_qqq100_preview_signal_input",
        "sma_50": "",
        "sma_200": "",
        "sma_50_vs_200_state": "",
        "distance_sma_50_to_sma_200_pct": "",
        "close_above_sma_200": "",
        "trend_state": "unknown",
        "promotion_status": "blocked_missing_signal_input",
        "promotion_label": "missing_qqq100_preview_signal_input",
        "required_next_step": "Run python bot.py --qqq100-preview-signal-pack before promoted preview review.",
        **preview_safety_flags(),
    }


def normalize_desired_position(value: Any) -> str:
    return str(value or "").strip().lower()


def preview_safety_flags() -> dict[str, bool]:
    return {
        "preview_candidate": True,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "scheduling_approved": False,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
    }


def regime_diagnostics(regime_ticker: str, regime_price_data: Any | None) -> dict[str, Any]:
    result = {
        "regime_ticker": regime_ticker,
        "regime_latest_close": "",
        "regime_sma_200": "",
        "regime_state": "unavailable",
    }
    if regime_price_data is None:
        return result
    rows = price_rows(regime_price_data)
    if len(rows) < 200:
        return result
    latest_close = float(rows[-1]["close"])
    regime_sma = simple_moving_average(rows, 200)
    result["regime_latest_close"] = round(latest_close, 4)
    result["regime_sma_200"] = round(regime_sma, 4)
    result["regime_state"] = "bullish" if latest_close > regime_sma else "bearish"
    return result


def pct_distance(value: float, threshold: float) -> float | str:
    if threshold == 0:
        return ""
    return round(((float(value) - float(threshold)) / float(threshold)) * 100, 4)


def price_rows(price_data: Any) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for _, row in price_data.iterrows():
        rows.append(
            {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
        )
    return rows


def write_promoted_preview(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PROMOTED_PREVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in PROMOTED_PREVIEW_COLUMNS})


def build_promoted_preview_summary(rows: list[dict[str, Any]], warnings: list[str]) -> list[str]:
    strategies = sorted({str(row.get("strategy_name", "")) for row in rows if row.get("strategy_name")})
    tickers = sorted({str(row.get("ticker", "")) for row in rows if row.get("ticker")})
    return [
        "Promoted strategy preview summary",
        "WARNING: This command is preview-only and does not approve execution.",
        f"Strategies previewed: {', '.join(strategies) if strategies else 'none'}",
        f"Tickers previewed: {len(tickers)}",
        f"Warnings: {len(warnings)}",
        "QQQ100 promoted preview candidate is sourced from saved qqq100_preview_signal_pack only.",
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                return []
            return [
                row
                for row in reader
                if any((value or "").strip() for value in row.values())
            ]
    except FileNotFoundError:
        return []
