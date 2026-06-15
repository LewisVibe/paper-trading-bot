"""Saved-signal action preview shell for qqq_100_trend_gate.

Default mode reads the saved QQQ100 preview signal only. Optional paper-position
context is read-only and requires both explicit flags; it never creates orders,
writes SQLite, sends alerts, schedules anything, or approves execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

INPUT_FILES = {
    "signal": Path("data/qqq100_preview_signal_pack.csv"),
}

OUTPUT_FILES = {
    "preview": Path("data/qqq100_action_preview.csv"),
    "summary": Path("data/qqq100_action_preview_summary.csv"),
    "blockers": Path("data/qqq100_action_preview_blockers.csv"),
}

PREVIEW_COLUMNS = [
    "strategy_name",
    "ticker",
    "desired_position",
    "signal_date",
    "latest_close_if_saved",
    "trend_state",
    "preview_signal_status",
    "current_position_status",
    "current_position_source",
    "current_position_quantity_if_readonly",
    "position_read_mode",
    "alignment_state",
    "non_executable_preview_action",
    "blocker",
    "next_step",
    "research_only",
    "preview_only",
    "action_preview_only",
    "alpaca_called",
    "alpaca_readonly",
    "paper_positions_read",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
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
    "action_preview_only",
    "alpaca_called",
    "alpaca_readonly",
    "paper_positions_read",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
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
    "action_preview_only",
    "alpaca_called",
    "alpaca_readonly",
    "paper_positions_read",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]

BASE_SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": True,
    "action_preview_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
}


@dataclass
class Qqq100ActionPreviewResult:
    output_paths: dict[str, Path]
    preview_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


@dataclass
class ReadonlyPositionContext:
    current_position_status: str
    current_position_source: str
    current_position_quantity_if_readonly: str
    position_read_mode: str
    alpaca_called: bool
    alpaca_readonly: bool
    paper_positions_read: bool
    data_error: str = ""


def generate_qqq100_action_preview(
    root_dir: Path | str = ".",
    *,
    use_paper_positions_readonly: bool = False,
    confirm_readonly_alpaca_check: bool = False,
) -> Qqq100ActionPreviewResult:
    root = Path(root_dir)
    signal = load_saved_signal(root)
    position_context = build_position_context(
        root,
        use_paper_positions_readonly=use_paper_positions_readonly,
        confirm_readonly_alpaca_check=confirm_readonly_alpaca_check,
    )
    preview_row = build_preview_row(signal, position_context)
    summary_rows = build_summary_rows(preview_row)
    blocker_rows = build_blocker_rows(preview_row, position_context)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["preview"], PREVIEW_COLUMNS, [preview_row])
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return Qqq100ActionPreviewResult(
        output_paths=output_paths,
        preview_rows=[preview_row],
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, preview_row, output_paths),
    )


def show_qqq100_action_preview(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    preview_path = root / OUTPUT_FILES["preview"]
    if not summary_path.exists() or not preview_path.exists():
        return 1, ["Run `python bot.py --qqq100-action-preview` first."]
    summary_rows = read_csv_rows(summary_path)
    preview_rows = read_csv_rows(preview_path)
    preview = preview_rows[0] if preview_rows else {}
    return 0, [
        "QQQ100 action preview saved display. Action-preview only; execution_approved=False.",
        f"Final action preview status: {summary_value(summary_rows, 'final_action_preview_status')}",
        f"Strategy: {preview.get('strategy_name', '')}",
        f"Ticker: {preview.get('ticker', '')}",
        f"Desired position: {preview.get('desired_position', '')}",
        f"Current position status: {preview.get('current_position_status', '')}",
        f"Current position source: {preview.get('current_position_source', '')}",
        f"Alignment state: {preview.get('alignment_state', '')}",
        f"Non-executable preview action: {preview.get('non_executable_preview_action', '')}",
        f"Blocker: {preview.get('blocker', '')}",
        f"Next step: {preview.get('next_step', '')}",
        "research_only=true; preview_only=true; action_preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: this is saved action-preview context only, not an order instruction, paper execution, live trading, or scheduling approval.",
    ]


def load_saved_signal(root: Path) -> dict[str, Any]:
    rows = read_csv_rows(root / INPUT_FILES["signal"])
    for row in rows:
        if row.get("strategy_name") == STRATEGY_NAME and row.get("ticker") == TICKER:
            return row
    if rows:
        return rows[0]
    return {
        "strategy_name": STRATEGY_NAME,
        "ticker": TICKER,
        "desired_position": "unavailable",
        "signal_date": "",
        "latest_close": "",
        "trend_state": "saved_signal_unavailable",
        "data_status": "saved_signal_missing",
    }


def build_position_context(
    root: Path,
    *,
    use_paper_positions_readonly: bool,
    confirm_readonly_alpaca_check: bool,
) -> ReadonlyPositionContext:
    if not use_paper_positions_readonly:
        return ReadonlyPositionContext(
            current_position_status="position_not_read",
            current_position_source="saved_signal_only",
            current_position_quantity_if_readonly="",
            position_read_mode="saved_signal_only",
            alpaca_called=False,
            alpaca_readonly=False,
            paper_positions_read=False,
        )
    if not confirm_readonly_alpaca_check:
        return ReadonlyPositionContext(
            current_position_status="position_context_unavailable",
            current_position_source="readonly_confirmation_missing",
            current_position_quantity_if_readonly="",
            position_read_mode="readonly_confirmation_missing",
            alpaca_called=False,
            alpaca_readonly=False,
            paper_positions_read=False,
            data_error="--confirm-readonly-alpaca-check is required before reading paper positions.",
        )
    return load_readonly_paper_position(root)


def load_readonly_paper_position(root: Path) -> ReadonlyPositionContext:
    try:
        from alpaca.trading.client import TradingClient
        from trading_bot.config import load_config

        config = load_config(root / "config.json", force_dry_run=True)
        if not config.alpaca_paper:
            return position_unavailable("Alpaca config is not paper mode.", alpaca_called=False, alpaca_readonly=True)
        if not config.alpaca_api_key or not config.alpaca_secret_key:
            return position_unavailable("Alpaca paper credentials are unavailable.", alpaca_called=False, alpaca_readonly=True)
        client = TradingClient(config.alpaca_api_key, config.alpaca_secret_key, paper=True)
        positions = client.get_all_positions()
        for position in positions:
            if str(getattr(position, "symbol", "")).upper() == TICKER:
                qty = float(getattr(position, "qty", 0.0) or 0.0)
                if qty > 0:
                    return ReadonlyPositionContext(
                        current_position_status="paper_position_long",
                        current_position_source="alpaca_paper_positions_readonly",
                        current_position_quantity_if_readonly=format_quantity(qty),
                        position_read_mode="confirmed_readonly_alpaca_paper",
                        alpaca_called=True,
                        alpaca_readonly=True,
                        paper_positions_read=True,
                    )
        return ReadonlyPositionContext(
            current_position_status="paper_position_flat",
            current_position_source="alpaca_paper_positions_readonly",
            current_position_quantity_if_readonly="0",
            position_read_mode="confirmed_readonly_alpaca_paper",
            alpaca_called=True,
            alpaca_readonly=True,
            paper_positions_read=True,
        )
    except Exception as exc:
        return position_unavailable(str(exc), alpaca_called=True, alpaca_readonly=True)


def position_unavailable(message: str, *, alpaca_called: bool, alpaca_readonly: bool) -> ReadonlyPositionContext:
    return ReadonlyPositionContext(
        current_position_status="position_context_unavailable",
        current_position_source="alpaca_paper_positions_readonly_unavailable",
        current_position_quantity_if_readonly="",
        position_read_mode="confirmed_readonly_alpaca_paper",
        alpaca_called=alpaca_called,
        alpaca_readonly=alpaca_readonly,
        paper_positions_read=False,
        data_error=message,
    )


def build_preview_row(signal: dict[str, Any], position: ReadonlyPositionContext) -> dict[str, Any]:
    desired_position = normalize_desired_position(signal.get("desired_position"))
    alignment_state, preview_action, blocker, next_step = alignment_decision(desired_position, position.current_position_status)
    return {
        "strategy_name": STRATEGY_NAME,
        "ticker": TICKER,
        "desired_position": desired_position,
        "signal_date": signal.get("signal_date", ""),
        "latest_close_if_saved": signal.get("latest_close", ""),
        "trend_state": signal.get("trend_state", ""),
        "preview_signal_status": signal.get("data_status", "saved_signal_loaded"),
        "current_position_status": position.current_position_status,
        "current_position_source": position.current_position_source,
        "current_position_quantity_if_readonly": position.current_position_quantity_if_readonly,
        "position_read_mode": position.position_read_mode,
        "alignment_state": alignment_state,
        "non_executable_preview_action": preview_action,
        "blocker": blocker,
        "next_step": next_step,
        **safety_flags(position),
    }


def alignment_decision(desired_position: str, current_position_status: str) -> tuple[str, str, str, str]:
    if current_position_status == "position_not_read":
        return (
            "review_required_position_unknown",
            "manual_review_required_position_unknown",
            "position_not_read",
            "rerun_with_explicit_readonly_flags_for_position_context_or_review_manually",
        )
    if current_position_status == "position_context_unavailable":
        return (
            "position_context_unavailable",
            "manual_review_required_position_unavailable",
            "position_context_unavailable",
            "resolve_readonly_position_context_before_any_manual_preview_discussion",
        )
    if desired_position == "long" and current_position_status == "paper_position_flat":
        return (
            "review_required_not_aligned",
            "manual_review_required_for_possible_open_long",
            "manual_review_required",
            "manual_review_required_before_any_preview_mode_change",
        )
    if desired_position == "long" and current_position_status == "paper_position_long":
        return ("aligned_long", "no_action_preview_only", "none", "continue_saved_preview_review")
    if desired_position == "flat" and current_position_status == "paper_position_long":
        return (
            "review_required_not_aligned",
            "manual_review_required_for_possible_flatten",
            "manual_review_required",
            "manual_review_required_before_any_preview_mode_change",
        )
    if desired_position == "flat" and current_position_status == "paper_position_flat":
        return ("aligned_flat", "no_action_preview_only", "none", "continue_saved_preview_review")
    return (
        "position_context_unavailable",
        "manual_review_required_position_unavailable",
        "signal_or_position_context_unavailable",
        "refresh_saved_signal_or_review_readonly_position_context",
    )


def build_summary_rows(preview: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        summary_row("final_action_preview_status", "qqq100_action_preview_created", "Saved action-preview shell was created for qqq_100_trend_gate.", preview),
        summary_row("signal_status", "saved_signal_loaded", "Saved QQQ100 preview signal was read when available.", preview),
        summary_row("strategy_name", STRATEGY_NAME, "Only qqq_100_trend_gate is included.", preview),
        summary_row("ticker", TICKER, "QQQ is the only ticker in this action preview.", preview),
        summary_row("desired_position", str(preview.get("desired_position", "")), "Desired position comes from the saved preview signal.", preview),
        summary_row("current_position_status", str(preview.get("current_position_status", "")), "Position context is saved-only by default or explicit read-only Alpaca paper context.", preview),
        summary_row("current_position_source", str(preview.get("current_position_source", "")), "Default source is saved_signal_only.", preview),
        summary_row("readonly_position_status", "paper_positions_readonly_loaded" if preview.get("paper_positions_read") else "paper_positions_readonly_not_loaded", "Read-only paper positions are loaded only when both explicit flags are present.", preview),
        summary_row("alignment_state", str(preview.get("alignment_state", "")), "Alignment state is manual-review context only.", preview),
        summary_row("non_executable_preview_action", str(preview.get("non_executable_preview_action", "")), "Preview action text is non-executable.", preview),
        summary_row("recommended_next_step", str(preview.get("next_step", "")), "Next step remains manual review.", preview),
        summary_row("execution_status", "execution_blocked", "Paper/live execution remains blocked.", preview),
        summary_row("paper_execution_status", "paper_execution_not_approved", "Paper execution is not approved.", preview),
        summary_row("orders_status", "orders_created_false", "No orders are created, submitted, or cancelled.", preview),
    ]


def build_blocker_rows(preview: dict[str, Any], position: ReadonlyPositionContext) -> list[dict[str, Any]]:
    rows = [
        blocker_row("execution_blocked", "blocked", "critical", "Paper/live execution is not approved.", "Keep this output disconnected from execution paths.", preview),
        blocker_row("paper_execution_not_approved", "blocked", "critical", "Paper execution is not approved.", "Do not treat alignment as permission to trade.", preview),
        blocker_row("orders_created_false", "blocked", "critical", "No orders are created, submitted, or cancelled by this command.", "Manual review only.", preview),
        blocker_row("scheduling_not_approved", "blocked", "high", "Scheduling is not approved.", "Do not schedule this action preview.", preview),
    ]
    if preview.get("current_position_status") == "position_not_read":
        rows.append(blocker_row("position_not_read", "review_required", "high", "Default mode does not read paper positions.", "Use both explicit read-only flags only after manual approval.", preview))
    if preview.get("alignment_state") == "review_required_not_aligned":
        rows.append(blocker_row("review_required_not_aligned", "review_required", "high", "Saved signal and read-only paper position context are not aligned.", "Manual review required; no execution is approved.", preview))
    if preview.get("alignment_state") == "position_context_unavailable":
        details = position.data_error or "Position context was unavailable."
        rows.append(blocker_row("position_context_unavailable", "review_required", "high", details, "Resolve saved signal or read-only position context before any preview discussion.", preview))
    return rows


def summary_row(name: str, value: str, details: str, preview: dict[str, Any]) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags_from_preview(preview)}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str, preview: dict[str, Any]) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **safety_flags_from_preview(preview)}


def build_summary_lines(summary_rows: list[dict[str, Any]], preview: dict[str, Any], output_paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ100 action preview complete. Action-preview only; execution_approved=False.",
        f"Final action preview status: {summary_value(summary_rows, 'final_action_preview_status')}",
        f"Strategy: {preview.get('strategy_name', '')}",
        f"Ticker: {preview.get('ticker', '')}",
        f"Desired position: {preview.get('desired_position', '')}",
        f"Current position status: {preview.get('current_position_status', '')}",
        f"Current position source: {preview.get('current_position_source', '')}",
        f"Alignment state: {preview.get('alignment_state', '')}",
        f"Non-executable preview action: {preview.get('non_executable_preview_action', '')}",
        f"Next step: {preview.get('next_step', '')}",
        f"Saved preview to {output_paths['preview']}",
        f"Saved summary/blockers to {output_paths['summary']}; {output_paths['blockers']}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; sqlite_trade_log_written=false; discord_alert_sent=false",
        "research_only=true; preview_only=true; action_preview_only=true; paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: this is saved action-preview context only, not an order instruction, paper execution, live trading, or scheduling approval.",
    ]


def normalize_desired_position(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"long", "flat"}:
        return text
    return "unavailable"


def format_quantity(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def safety_flags(position: ReadonlyPositionContext) -> dict[str, Any]:
    flags = dict(BASE_SAFETY_FLAGS)
    flags.update(
        {
            "alpaca_called": position.alpaca_called,
            "alpaca_readonly": position.alpaca_readonly,
            "paper_positions_read": position.paper_positions_read,
        }
    )
    return flags


def safety_flags_from_preview(preview: dict[str, Any]) -> dict[str, Any]:
    flags = dict(BASE_SAFETY_FLAGS)
    flags.update(
        {
            "alpaca_called": preview.get("alpaca_called", False),
            "alpaca_readonly": preview.get("alpaca_readonly", False),
            "paper_positions_read": preview.get("paper_positions_read", False),
        }
    )
    return flags


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
