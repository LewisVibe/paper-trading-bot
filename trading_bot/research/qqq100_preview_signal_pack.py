"""Non-execution preview signal pack for qqq_100_trend_gate.

This pack may fetch QQQ daily market data to calculate the fixed SMA100 trend
gate. It does not call Alpaca, load config, read positions, create orders,
write SQLite, send alerts, schedule anything, add action preview, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"
SMA_DAYS = 100
READINESS_STATUS = "qqq100_preview_discussion_ready"
QQQ_ADAPTIVE = "codex_qqq_adaptive_trend_exposure"
QQQ150 = "qqq_150_trend_gate"
HIGH_GROWTH = "codex_broad_growth_balanced_breakout_control"

OUTPUT_FILES = {
    "pack": Path("data/qqq100_preview_signal_pack.csv"),
    "summary": Path("data/qqq100_preview_signal_summary.csv"),
    "design": Path("data/qqq100_preview_signal_design.csv"),
    "blockers": Path("data/qqq100_preview_signal_blockers.csv"),
}

SIGNAL_COLUMNS = [
    "strategy_name",
    "ticker",
    "signal_date",
    "latest_close",
    "sma_100",
    "trend_state",
    "desired_position",
    "signal_reason",
    "data_status",
    "data_error",
    "research_only",
    "preview_only",
    "action_preview_added",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "action_preview_added",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
DESIGN_COLUMNS = [
    "checkpoint_name",
    "checkpoint_status",
    "checkpoint_label",
    "details",
    "required_next_step",
    "research_only",
    "preview_only",
    "action_preview_added",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]
BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    "research_only",
    "preview_only",
    "action_preview_added",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": True,
    "action_preview_added": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
}


@dataclass
class Qqq100PreviewSignalPackResult:
    output_paths: dict[str, Path]
    signal_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    design_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_preview_signal_pack(root_dir: Path | str = ".") -> Qqq100PreviewSignalPackResult:
    root = Path(root_dir)
    market_data = fetch_qqq_daily_data(root)
    signal_row_data = build_signal_row(market_data)
    signal_rows = [signal_row_data]
    summary_rows = build_summary_rows(signal_row_data)
    design_rows = build_design_rows()
    blocker_rows = build_blocker_rows(signal_row_data)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["pack"], SIGNAL_COLUMNS, signal_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["design"], DESIGN_COLUMNS, design_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return Qqq100PreviewSignalPackResult(
        output_paths=output_paths,
        signal_rows=signal_rows,
        summary_rows=summary_rows,
        design_rows=design_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, signal_row_data, output_paths),
    )


def show_qqq100_preview_signal_pack(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    pack_path = root / OUTPUT_FILES["pack"]
    if not summary_path.exists() or not pack_path.exists():
        return 1, ["Run `python bot.py --qqq100-preview-signal-pack` first."]
    summary_rows = read_csv_rows(summary_path)
    signal_rows = read_csv_rows(pack_path)
    signal = signal_rows[0] if signal_rows else {}
    return 0, [
        "QQQ100 preview signal pack saved display. Preview signal only; execution_approved=False.",
        f"Final preview status: {summary_value(summary_rows, 'final_preview_status')}",
        f"Ticker: {signal.get('ticker', '')}",
        f"Latest close: {signal.get('latest_close', '')}",
        f"SMA100: {signal.get('sma_100', '')}",
        f"Trend state: {signal.get('trend_state', '')}",
        f"Desired position: {signal.get('desired_position', '')}",
        f"Signal reason: {signal.get('signal_reason', '')}",
        f"Data status: {signal.get('data_status', '')}",
        f"Next step: {summary_value(summary_rows, 'recommended_next_step')}",
        "action_preview_added=false; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: this is a saved preview signal only, not an action preview, order instruction, paper execution, live trading, or scheduling approval.",
    ]


def fetch_qqq_daily_data(root: Path) -> dict[str, Any]:
    cache_dir = root / "data" / "yfinance_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        import yfinance as yf
    except Exception as exc:
        return data_failure(f"yfinance import failed: {exc}")
    try:
        yf.set_tz_cache_location(str(cache_dir))
    except AttributeError:
        pass

    try:
        data = yf.download(TICKER, period="1y", interval="1d", auto_adjust=True, progress=False, threads=False)
    except Exception as exc:
        return data_failure(str(exc))
    if data is None or data.empty:
        return data_failure("No daily market data returned by yfinance.")

    close_series = market_data_series(data, "Close")
    if close_series is None:
        return data_failure("Daily market data had no Close column.")
    close_series = close_series.dropna()
    if len(close_series) < SMA_DAYS:
        return data_failure(f"Insufficient daily close rows for SMA{SMA_DAYS}: rows={len(close_series)}")

    latest_close = round(float(close_series.iloc[-1]), 6)
    sma_100 = round(float(close_series.tail(SMA_DAYS).mean()), 6)
    signal_date = timestamp_to_text(close_series.index[-1])
    return {
        "signal_date": signal_date,
        "latest_close": latest_close,
        "sma_100": sma_100,
        "data_status": "ok",
        "data_error": "",
    }


def build_signal_row(market_data: dict[str, Any]) -> dict[str, Any]:
    data_status = str(market_data.get("data_status", "market_data_unavailable"))
    latest_close = market_data.get("latest_close", "")
    sma_100 = market_data.get("sma_100", "")
    if data_status == "ok" and latest_close != "" and sma_100 != "":
        close = float(latest_close)
        sma = float(sma_100)
        if close > sma:
            trend_state = "above_sma100_trend_gate"
            desired_position = "long"
            signal_reason = "QQQ latest close is above the 100-day SMA trend gate."
        else:
            trend_state = "at_or_below_sma100_trend_gate"
            desired_position = "flat"
            signal_reason = "QQQ latest close is at or below the 100-day SMA trend gate."
    else:
        trend_state = "market_data_unavailable"
        desired_position = "flat"
        signal_reason = "QQQ100 preview signal could not be calculated from available daily data."
    return {
        "strategy_name": STRATEGY_NAME,
        "ticker": TICKER,
        "signal_date": market_data.get("signal_date", ""),
        "latest_close": latest_close,
        "sma_100": sma_100,
        "trend_state": trend_state,
        "desired_position": desired_position,
        "signal_reason": signal_reason,
        "data_status": data_status,
        "data_error": market_data.get("data_error", ""),
        **safety_flags(),
    }


def build_summary_rows(signal: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        summary_row("final_preview_status", "qqq100_preview_signal_pack_created", "Saved non-execution preview signal was created for qqq_100_trend_gate."),
        summary_row("strategy_name", STRATEGY_NAME, "Only qqq_100_trend_gate is previewed."),
        summary_row("ticker", TICKER, "QQQ is the only ticker in this preview signal pack."),
        summary_row("desired_position", str(signal.get("desired_position", "")), "Long above SMA100, flat at or below SMA100, with no action preview."),
        summary_row("data_status", str(signal.get("data_status", "")), str(signal.get("data_error", ""))),
        summary_row("recommended_next_step", "separate_saved_output_action_preview_design_not_execution", "If manually approved later, design a separate saved-output action-preview pack; do not execute."),
        summary_row("preview_boundary", "preview_signal_only", "Preview signal does not compare to paper positions and does not create actions."),
        summary_row("execution_status", "execution_blocked", "Paper/live execution remains blocked."),
    ]


def build_design_rows() -> list[dict[str, Any]]:
    return [
        design_row("clean_lead", "confirmed", "qqq100_clean_lead_preview_enabled", f"{STRATEGY_NAME} is the clean stock/ETF research lead.", "Keep preview limited to QQQ100 signal only."),
        design_row("signal_scope", "created", "preview_signal_only", "The pack calculates close versus SMA100 and writes a saved preview signal.", "Do not compare against paper positions in this command."),
        design_row("action_preview_boundary", "blocked", "action_preview_not_added", "Action preview versus paper positions is not added.", "Consider only a separate saved-output action-preview design after manual review."),
        design_row("execution_boundary", "blocked", "execution_blocked", "Paper execution remains blocked.", "Do not connect this signal to execution."),
        design_row("paper_execution_boundary", "blocked", "paper_execution_not_approved", "Paper execution is not approved.", "Keep paper execution behind separate readiness and protection gates."),
        design_row("high_growth_boundary", "excluded", "high_growth_branch_excluded_from_preview", f"{HIGH_GROWTH} is excluded from preview. High-growth branch is not promoted.", "Keep high-growth branch research-only."),
        design_row("adaptive_boundary", "alternative_only", "adaptive_qqq_alternative_not_previewed", f"{QQQ_ADAPTIVE} remains an ambitious alternative only.", "Do not preview the adaptive alternative in this pack."),
        design_row("qqq150_boundary", "rejected", "qqq150_high_drawdown_reference_rejected", f"{QQQ150} remains rejected as a high-drawdown reference.", "Do not preview the higher-drawdown reference."),
    ]


def build_blocker_rows(signal: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("action_preview_not_added", "blocked", "critical", "No action preview versus paper positions was added.", "Design a separate saved-output action-preview pack if manually approved later."),
        blocker_row("execution_blocked", "blocked", "critical", "Paper/live execution remains blocked.", "Do not create execution wiring."),
        blocker_row("paper_execution_not_approved", "blocked", "critical", "Paper execution is not approved.", "Keep strategy disconnected from paper execution."),
        blocker_row("scheduling_not_approved", "blocked", "high", "Scheduling is not approved.", "Do not schedule this preview command."),
    ]
    if signal.get("data_status") != "ok":
        rows.append(blocker_row("market_data_unavailable", "warning", "medium", str(signal.get("data_error", "")), "Rerun only when QQQ daily market data is available."))
    return rows


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def design_row(name: str, status: str, label: str, details: str, next_step: str) -> dict[str, Any]:
    return {"checkpoint_name": name, "checkpoint_status": status, "checkpoint_label": label, "details": details, "required_next_step": next_step, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **safety_flags()}


def build_summary_lines(summary_rows: list[dict[str, Any]], signal: dict[str, Any], output_paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ100 preview signal pack complete. Preview signal only; execution_approved=False.",
        f"Final preview status: {summary_value(summary_rows, 'final_preview_status')}",
        f"Ticker: {signal.get('ticker', '')}",
        f"Latest close: {signal.get('latest_close', '')}",
        f"SMA100: {signal.get('sma_100', '')}",
        f"Trend state: {signal.get('trend_state', '')}",
        f"Desired position: {signal.get('desired_position', '')}",
        f"Signal reason: {signal.get('signal_reason', '')}",
        f"Data status: {signal.get('data_status', '')}",
        f"Next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved pack to {output_paths['pack']}",
        f"Saved summary/design/blockers to {output_paths['summary']}; {output_paths['design']}; {output_paths['blockers']}",
        "action_preview_added=false; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: this is a saved preview signal only, not an action preview, order instruction, paper execution, live trading, or scheduling approval.",
    ]


def market_data_series(data: Any, column_name: str) -> Any:
    if column_name in data.columns:
        column = data[column_name]
    else:
        matches = [
            column
            for column in data.columns
            if isinstance(column, tuple) and column_name in [str(part) for part in column]
        ]
        if not matches:
            return None
        column = data[matches[0]]
    if hasattr(column, "columns"):
        if len(column.columns) == 0:
            return None
        return column.iloc[:, 0]
    return column


def data_failure(message: str) -> dict[str, Any]:
    return {
        "signal_date": "",
        "latest_close": "",
        "sma_100": "",
        "data_status": "market_data_unavailable",
        "data_error": message,
    }


def timestamp_to_text(value: Any) -> str:
    try:
        return value.date().isoformat()
    except Exception:
        try:
            return value.isoformat()
        except Exception:
            return str(value)


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
