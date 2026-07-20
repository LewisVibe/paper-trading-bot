"""Read-only broker-position comparison for volatility-targeted growth 15/20.

The default mode is saved-output-only and does not call Alpaca. A future run may
read Alpaca paper positions only when --confirm-readonly-alpaca-check is passed.
Even confirmed mode is comparison context only: it creates no orders, order
instructions, scheduling, or paper-live approval.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SELECTED_CANDIDATE = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
CONFIRMED_STATUS = "vol_targeted_growth_broker_position_comparison_completed_readonly_manual_review_required"
UNCONFIRMED_STATUS = "vol_targeted_growth_broker_position_comparison_not_run_confirmation_required"
BLOCKED_STATUS = "vol_targeted_growth_broker_position_comparison_blocked_missing_run_readiness"
NEXT_STEP = "manual_review_readonly_broker_position_comparison_before_any_paper_live_discussion"

OUTPUT_FILES = {
    "comparison": Path("data/vol_targeted_growth_broker_position_comparison.csv"),
    "summary": Path("data/vol_targeted_growth_broker_position_comparison_summary.csv"),
    "evidence": Path("data/vol_targeted_growth_broker_position_comparison_evidence.csv"),
    "blockers": Path("data/vol_targeted_growth_broker_position_comparison_blockers.csv"),
}

INPUT_FILES = {
    "run_readiness_summary": Path("data/vol_targeted_growth_broker_comparison_run_readiness_summary.csv"),
    "action_preview": Path("data/vol_targeted_growth_action_preview.csv"),
    "action_preview_summary": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "preview_signal_summary": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
}

SLEEVE_PROXY_SYMBOLS = {
    "qqq100_core_trend_sleeve": "QQQ",
    "high_growth_stock_research_sleeve": "MGK",
    "crypto_research_sleeve": "IBIT",
    "defensive_cash_or_bond_sleeve": "SGOV",
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "readonly_comparison_only": True,
    "alpaca_called": False,
    "alpaca_readonly": False,
    "live_positions_read": False,
    "paper_positions_read": False,
    "broker_positions_compared": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "paper_live_candidate_approved": False,
    "paper_live_discussion_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

COMPARISON_COLUMNS = [
    "created_at",
    "selected_candidate",
    "sleeve_name",
    "target_weight",
    "sleeve_status",
    "broker_symbol_proxy",
    "broker_position_status",
    "broker_position_quantity_if_readonly",
    "broker_position_source",
    "comparison_status",
    "manual_review_label",
    "blocker",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class ReadonlyPositionSnapshot:
    status: str
    positions_by_symbol: dict[str, str]
    error_type: str = ""
    details: str = ""
    alpaca_called: bool = False
    paper_positions_read: bool = False


@dataclass
class VolTargetedGrowthBrokerPositionComparisonResult:
    output_paths: dict[str, Path]
    comparison_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_broker_position_comparison(
    root_dir: Path | str = ".",
    *,
    confirm_readonly_alpaca_check: bool = False,
) -> VolTargetedGrowthBrokerPositionComparisonResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    readiness_status = summary_value(inputs["run_readiness_summary"], "final_run_readiness_status")
    action_status = summary_value(inputs["action_preview_summary"], "final_action_preview_status")
    can_attempt_read = readiness_status == "vol_targeted_growth_readonly_broker_comparison_ready_for_explicit_manual_approval_required"
    final_status = determine_final_status(confirm_readonly_alpaca_check, can_attempt_read)
    snapshot = load_readonly_broker_positions(root) if confirm_readonly_alpaca_check and can_attempt_read else unconfirmed_snapshot(confirm_readonly_alpaca_check, can_attempt_read)
    comparison_rows = build_comparison_rows(created_at, inputs["action_preview"], snapshot)
    summary_rows = build_summary_rows(inputs, comparison_rows, snapshot, final_status, action_status)
    evidence_rows = build_evidence_rows(inputs, snapshot, confirm_readonly_alpaca_check)
    blocker_rows = build_blocker_rows(final_status, snapshot, confirm_readonly_alpaca_check, can_attempt_read)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["comparison"], COMPARISON_COLUMNS, comparison_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthBrokerPositionComparisonResult(
        output_paths=output_paths,
        comparison_rows=comparison_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_broker_position_comparison(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, ["Run `python bot.py --vol-targeted-growth-broker-position-comparison` first."]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted growth broker-position comparison saved display. Read-only/manual-review context; no execution approval.",
        f"final_comparison_status: {summary_value(rows, 'final_comparison_status')}",
        f"selected_candidate: {summary_value(rows, 'selected_candidate')}",
        f"readonly_confirmation_status: {summary_value(rows, 'readonly_confirmation_status')}",
        f"broker_position_read_status: {summary_value(rows, 'broker_position_read_status')}",
        f"comparison_row_count: {summary_value(rows, 'comparison_row_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false; paper_live_candidate_approved=false",
    ]


def determine_final_status(confirm_readonly_alpaca_check: bool, can_attempt_read: bool) -> str:
    if not can_attempt_read:
        return BLOCKED_STATUS
    if not confirm_readonly_alpaca_check:
        return UNCONFIRMED_STATUS
    return CONFIRMED_STATUS


def unconfirmed_snapshot(confirm_readonly_alpaca_check: bool, can_attempt_read: bool) -> ReadonlyPositionSnapshot:
    if not can_attempt_read:
        return ReadonlyPositionSnapshot(status="blocked_missing_run_readiness", positions_by_symbol={})
    if not confirm_readonly_alpaca_check:
        return ReadonlyPositionSnapshot(status="readonly_confirmation_missing", positions_by_symbol={})
    return ReadonlyPositionSnapshot(status="readonly_check_not_attempted", positions_by_symbol={})


def load_readonly_broker_positions(root: Path) -> ReadonlyPositionSnapshot:
    try:
        from alpaca.trading.client import TradingClient
        from trading_bot.config import load_config

        config = load_config(root / "config.json", force_dry_run=True)
        if not config.alpaca_paper:
            return ReadonlyPositionSnapshot(status="blocked_not_paper_mode", positions_by_symbol={}, details="alpaca.paper is not true")
        if not config.alpaca_api_key or not config.alpaca_secret_key:
            return ReadonlyPositionSnapshot(status="blocked_missing_paper_credentials", positions_by_symbol={}, details="paper credentials missing")
        client = TradingClient(config.alpaca_api_key, config.alpaca_secret_key, paper=True)
        positions = client.get_all_positions()
        positions_by_symbol: dict[str, str] = {}
        for position in positions:
            symbol = str(getattr(position, "symbol", "")).upper()
            if not symbol:
                continue
            positions_by_symbol[symbol] = format_quantity(getattr(position, "qty", ""))
        return ReadonlyPositionSnapshot(
            status="paper_positions_read_readonly",
            positions_by_symbol=positions_by_symbol,
            alpaca_called=True,
            paper_positions_read=True,
        )
    except Exception as exc:  # noqa: BLE001
        return ReadonlyPositionSnapshot(
            status="blocked_readonly_broker_position_read_failed",
            positions_by_symbol={},
            error_type=type(exc).__name__,
            details="Read-only broker-position comparison failed safely. Sensitive details were not printed.",
            alpaca_called=True,
            paper_positions_read=False,
        )


def build_comparison_rows(
    created_at: str,
    action_rows: list[dict[str, str]],
    snapshot: ReadonlyPositionSnapshot,
) -> list[dict[str, Any]]:
    sleeves = [row for row in action_rows if row.get("sleeve_name")]
    if not sleeves:
        sleeves = [
            {"sleeve_name": "qqq100_core_trend_sleeve", "target_weight": "0.70", "sleeve_status": "clean_main_stock_etf_lead"},
            {"sleeve_name": "high_growth_stock_research_sleeve", "target_weight": "0.20", "sleeve_status": "high_growth_research_only"},
            {"sleeve_name": "crypto_research_sleeve", "target_weight": "0.05", "sleeve_status": "crypto_research_only"},
            {"sleeve_name": "defensive_cash_or_bond_sleeve", "target_weight": "0.05", "sleeve_status": "defensive_buffer_research_only"},
        ]
    return [comparison_row(created_at, row, snapshot) for row in sleeves]


def comparison_row(created_at: str, row: dict[str, str], snapshot: ReadonlyPositionSnapshot) -> dict[str, Any]:
    sleeve_name = row.get("sleeve_name", "")
    symbol = SLEEVE_PROXY_SYMBOLS.get(sleeve_name, "")
    quantity = snapshot.positions_by_symbol.get(symbol, "") if symbol else ""
    if snapshot.status != "paper_positions_read_readonly":
        position_status = snapshot.status
        comparison_status = "comparison_not_run_manual_review_required"
        label = "broker_position_read_not_completed"
        blocker = "readonly_confirmation_or_run_readiness_required"
    elif not symbol:
        position_status = "sleeve_not_mapped_to_single_broker_symbol"
        comparison_status = "manual_review_required_unmapped_sleeve"
        label = "manual_review_required_unmapped_sleeve"
        blocker = "sleeve_mapping_required_before_actionable_comparison"
    elif quantity:
        position_status = "paper_position_present"
        comparison_status = "broker_position_context_available_manual_review_required"
        label = "manual_review_required_position_present"
        blocker = "comparison_context_not_order_instruction"
    else:
        position_status = "paper_position_absent_or_zero"
        comparison_status = "broker_position_context_available_manual_review_required"
        label = "manual_review_required_position_absent"
        blocker = "comparison_context_not_order_instruction"
    return {
        "created_at": created_at,
        "selected_candidate": SELECTED_CANDIDATE,
        "sleeve_name": sleeve_name,
        "target_weight": row.get("target_weight", ""),
        "sleeve_status": row.get("sleeve_status", ""),
        "broker_symbol_proxy": symbol or "not_single_symbol_mapped",
        "broker_position_status": position_status,
        "broker_position_quantity_if_readonly": quantity,
        "broker_position_source": "alpaca_paper_positions_readonly" if snapshot.status == "paper_positions_read_readonly" else "not_read",
        "comparison_status": comparison_status,
        "manual_review_label": label,
        "blocker": blocker,
        "required_next_step": NEXT_STEP,
        **flags_for_snapshot(snapshot),
    }


def build_summary_rows(
    inputs: dict[str, list[dict[str, str]]],
    comparison_rows: list[dict[str, Any]],
    snapshot: ReadonlyPositionSnapshot,
    final_status: str,
    action_status: str,
) -> list[dict[str, Any]]:
    rows = [
        ("final_comparison_status", final_status, "Read-only broker-position comparison status."),
        ("selected_candidate", SELECTED_CANDIDATE, "Selected volatility-targeted growth candidate."),
        ("strategy_plain_english", strategy_explanation(), "What the strategy is trying to do."),
        ("readonly_confirmation_status", "confirmed" if snapshot.status == "paper_positions_read_readonly" else snapshot.status, "Whether the broker-read confirmation path completed."),
        ("broker_position_read_status", snapshot.status, "Broker-position read status."),
        ("source_action_preview_status", action_status or "missing_action_preview_status", "Saved action-preview status."),
        ("run_readiness_status", summary_value(inputs["run_readiness_summary"], "final_run_readiness_status") or "missing_run_readiness_status", "Saved run-readiness status."),
        ("comparison_row_count", str(len(comparison_rows)), "Sleeve-level comparison row count."),
        ("position_symbol_count_if_readonly", str(len(snapshot.positions_by_symbol)), "Number of paper position symbols seen if confirmed. Sensitive IDs are not printed."),
        ("largest_blocker", largest_blocker(final_status, snapshot), "Primary manual-review blocker."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any paper-live discussion."),
    ]
    return [{"summary_name": n, "summary_value": v, "details": d, **flags_for_snapshot(snapshot)} for n, v, d in rows]


def build_evidence_rows(
    inputs: dict[str, list[dict[str, str]]],
    snapshot: ReadonlyPositionSnapshot,
    confirm_readonly_alpaca_check: bool,
) -> list[dict[str, Any]]:
    rows = [(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(("readonly_confirmation_flag", str(confirm_readonly_alpaca_check).lower(), "Broker reads require explicit confirmation."))
    rows.append(("broker_read_error_type", snapshot.error_type or "none", snapshot.details or "No error details."))
    return [{"evidence_name": n, "evidence_value": v, "details": d, **flags_for_snapshot(snapshot)} for n, v, d in rows]


def build_blocker_rows(
    final_status: str,
    snapshot: ReadonlyPositionSnapshot,
    confirm_readonly_alpaca_check: bool,
    can_attempt_read: bool,
) -> list[dict[str, Any]]:
    rows = [
        ("order_instructions_not_allowed", "blocked", "critical", "This comparison must not produce order side, quantity, type, account, order ID, API key, webhook, or secret fields.", "Keep comparison manual-review-only."),
        ("paper_live_candidate_not_approved", "blocked", "critical", "The 15/20 candidate remains research-only.", "Do not promote from this comparison."),
        ("execution_not_approved", "blocked", "critical", "No execution, paper execution, live trading, follow-up order, repeat order, or scheduling is approved.", "Keep all approval flags false."),
    ]
    if not can_attempt_read:
        rows.insert(0, ("missing_run_readiness", "blocked", "critical", "Saved run-readiness checkpoint is missing or not in the expected state.", "run_and_review_run_readiness_checkpoint_first"))
    elif not confirm_readonly_alpaca_check:
        rows.insert(0, ("readonly_confirmation_missing", "blocked", "critical", "--confirm-readonly-alpaca-check was not provided, so no broker positions were read.", "rerun_only_after_explicit_manual_readonly_approval"))
    elif snapshot.status != "paper_positions_read_readonly":
        rows.insert(0, ("readonly_position_read_failed", "blocked", "critical", f"status={snapshot.status}; error_type={snapshot.error_type or 'none'}", "manual_review_required_for_readonly_broker_failure"))
    return [
        {"blocker_name": n, "status": s, "severity": sev, "details": d, "required_next_step": ns, **flags_for_snapshot(snapshot)}
        for n, s, sev, d, ns in rows
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted growth broker-position comparison complete. Read-only/manual-review context; no execution or scheduling approved.",
        f"final_comparison_status={summary_value(summary_rows, 'final_comparison_status')}",
        f"readonly_confirmation_status={summary_value(summary_rows, 'readonly_confirmation_status')}",
        f"broker_position_read_status={summary_value(summary_rows, 'broker_position_read_status')}",
        f"comparison_row_count={summary_value(summary_rows, 'comparison_row_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_comparison={output_paths['comparison']}",
        "order_instructions_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false; paper_live_candidate_approved=false",
    ]


def flags_for_snapshot(snapshot: ReadonlyPositionSnapshot) -> dict[str, Any]:
    flags = dict(SAFETY_FLAGS)
    if snapshot.status == "paper_positions_read_readonly":
        flags["alpaca_called"] = True
        flags["alpaca_readonly"] = True
        flags["paper_positions_read"] = True
        flags["broker_positions_compared"] = True
    elif snapshot.alpaca_called:
        flags["alpaca_called"] = True
        flags["alpaca_readonly"] = True
    return flags


def largest_blocker(final_status: str, snapshot: ReadonlyPositionSnapshot) -> str:
    if final_status == BLOCKED_STATUS:
        return "missing_run_readiness"
    if final_status == UNCONFIRMED_STATUS:
        return "readonly_confirmation_missing"
    if snapshot.status != "paper_positions_read_readonly":
        return "readonly_position_read_failed"
    return "manual_review_required_no_order_instructions_or_paper_live_approval"


def strategy_explanation() -> str:
    return (
        "The candidate is a research-only multi-sleeve growth portfolio: 70% QQQ100 core trend, "
        "20% high-growth research sleeve, 5% crypto research sleeve, and 5% defensive buffer. "
        "A 15% volatility target over a 20-day window scales exposure up or down within a 1x cap, "
        "so it tries to keep growth exposure while reducing risk when recent volatility rises."
    )


def format_quantity(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return "unavailable"
    return str(int(number)) if number.is_integer() else f"{number:.6f}".rstrip("0").rstrip(".")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summary_value(rows: list[dict[str, Any]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""
