"""Saved-output-only quality review for the high-growth research sleeve."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import multi_sleeve_portfolio_backtest as backtest


MISSING = "missing_saved_output"

HIGH_GROWTH_SLEEVE = "codex_broad_growth_balanced_breakout_control"
SELECTED_LEAD = "higher_growth_70_20_5_5"
PREVIOUS_BASELINE = "current_75_15_5_5"

STATUS_PROMISING = "high_growth_sleeve_quality_promising_but_drawdown_sensitive"
STATUS_SPLIT_SENSITIVE = "high_growth_sleeve_quality_split_sensitive_manual_review"
STATUS_BLOCKED = "high_growth_sleeve_quality_blocked_missing_saved_streams"
STATUS_NOT_SUITABLE = "high_growth_sleeve_quality_not_suitable_for_lead_component"

NEXT_MANUAL_REVIEW = "manual_review_high_growth_sleeve_quality_before_further_candidate_label_change"
NEXT_MISSING = "refresh_saved_high_growth_return_streams_before_sleeve_quality_review"
NEXT_NOT_SUITABLE = "keep_higher_growth_under_manual_review_until_sleeve_quality_improves"

INPUT_FILES = {
    "high_growth_stream": Path("data/high_growth_return_streams.csv"),
    "lead_state": Path("data/multi_sleeve_lead_state.csv"),
    "drawdown_summary": Path("data/multi_sleeve_high_growth_drawdown_summary.csv"),
    "drawdown_decomposition": Path("data/multi_sleeve_high_growth_drawdown_decomposition.csv"),
    "weight_sensitivity": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "higher_growth_review": Path("data/multi_sleeve_higher_growth_review.csv"),
    "research_lead_decision": Path("data/multi_sleeve_research_lead_decision.csv"),
    "portfolio_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
}

OUTPUT_FILES = {
    "review": Path("data/high_growth_sleeve_quality_review.csv"),
    "summary": Path("data/high_growth_sleeve_quality_summary.csv"),
    "splits": Path("data/high_growth_sleeve_quality_splits.csv"),
    "drawdowns": Path("data/high_growth_sleeve_quality_drawdowns.csv"),
    "blockers": Path("data/high_growth_sleeve_quality_blockers.csv"),
}

SAFETY_COLUMNS = [
    "research_only",
    "preview_only",
    "saved_output_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "yfinance_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]

REVIEW_COLUMNS = [
    "created_at",
    "review_name",
    "sleeve_name",
    "selected_lead_candidate",
    "high_growth_weight_in_lead",
    "high_growth_weight_in_previous_baseline",
    "delta_high_growth_weight",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "annual_volatility",
    "return_status",
    "drawdown_status",
    "sleeve_quality_status",
    "incremental_drawdown_contributor",
    "net_incremental_drawdown_effect",
    "portfolio_CAGR_delta",
    "portfolio_Sharpe_delta",
    "portfolio_MaxDD_delta",
    "portfolio_Calmar_delta",
    "contribution_interpretation",
    "concentration_dependency_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SPLIT_COLUMNS = [
    "created_at",
    "split_name",
    "sleeve_name",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "split_quality_status",
    *SAFETY_COLUMNS,
]

DRAWDOWN_COLUMNS = [
    "created_at",
    "sleeve_name",
    "drawdown_start",
    "drawdown_trough",
    "max_drawdown",
    "recovery_date",
    "recovery_rows",
    "recovery_days",
    "post_trough_63d_return",
    "post_trough_126d_return",
    "drawdown_recovery_status",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = ["created_at", "summary_name", "summary_value", "details", *SAFETY_COLUMNS]
BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "blocker_severity",
    "blocker_detail",
    "required_next_step",
    "execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
]


@dataclass
class HighGrowthSleeveQualityResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_sleeve_quality_review(root_dir: Path | str = ".") -> HighGrowthSleeveQualityResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    stream_rows = backtest.normalize_high_growth_stream_rows(inputs["high_growth_stream"])
    by_candidate = backtest.stream_returns_by_candidate(stream_rows)
    returns_by_date = by_candidate.get(HIGH_GROWTH_SLEEVE, {})
    if not returns_by_date:
        review_rows = [blocked_review_row(created_at)]
        split_rows = blocked_split_rows(created_at)
        drawdown_rows = [blocked_drawdown_row(created_at)]
        final_status = STATUS_BLOCKED
    else:
        dates = sorted(returns_by_date)
        returns = [returns_by_date[date] for date in dates]
        metrics = backtest.metrics_for_returns(returns)
        split_rows = build_split_rows(created_at, dates, returns)
        drawdown_rows = [build_drawdown_row(created_at, dates, returns)]
        final_status = final_quality_status(metrics, split_rows, drawdown_rows[0])
        review_rows = [build_review_row(created_at, metrics, final_status, inputs)]
    summary_rows = build_summary_rows(created_at, final_status, review_rows[0], split_rows, drawdown_rows[0])
    blocker_rows = build_blocker_rows(created_at, final_status, review_rows[0], split_rows, drawdown_rows[0], inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["splits"], SPLIT_COLUMNS, split_rows)
    write_rows(output_paths["drawdowns"], DRAWDOWN_COLUMNS, drawdown_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthSleeveQualityResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        split_rows=split_rows,
        drawdown_rows=drawdown_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["review"]),
    )


def show_high_growth_sleeve_quality_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "High-growth sleeve quality review is missing.",
            "Run `python bot.py --high-growth-sleeve-quality-review` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "High-growth sleeve quality review. Saved-output-only research; no execution path.",
        f"final high-growth sleeve quality status: {summary.get('final_high_growth_sleeve_quality_status', MISSING)}",
        f"selected high-growth sleeve: {summary.get('selected_high_growth_sleeve', MISSING)}",
        f"sleeve metrics: {summary.get('sleeve_metrics', MISSING)}",
        f"split summary and worst split: {summary.get('split_summary', MISSING)}",
        f"worst drawdown and recovery: {summary.get('worst_drawdown_and_recovery', MISSING)}",
        f"contribution to selected lead: {summary.get('contribution_to_selected_lead', MISSING)}",
        f"concentration/dependency finding: {summary.get('concentration_dependency_finding', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def build_review_row(created_at: str, metrics: dict[str, str], final_status: str, inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    lead = inputs["lead_state"][0] if inputs["lead_state"] else {}
    decision = inputs["research_lead_decision"][0] if inputs["research_lead_decision"] else {}
    drawdown_summary = summary_map(inputs["drawdown_summary"])
    concentration_status = concentration_status_for(inputs["high_growth_stream"])
    return {
        "created_at": created_at,
        "review_name": "high_growth_sleeve_quality",
        "sleeve_name": HIGH_GROWTH_SLEEVE,
        "selected_lead_candidate": lead.get("current_research_lead_candidate", SELECTED_LEAD),
        "high_growth_weight_in_lead": "20",
        "high_growth_weight_in_previous_baseline": "15",
        "delta_high_growth_weight": "5",
        "CAGR": metrics["cagr"],
        "Sharpe": metrics["sharpe"],
        "MaxDD": metrics["max_drawdown"],
        "Calmar": metrics["calmar"],
        "annual_volatility": metrics["annualised_volatility"],
        "return_status": "high_growth_returns_strong_research_only" if parse_float(metrics["cagr"]) > 0 else "high_growth_returns_weak_manual_review",
        "drawdown_status": "high_growth_standalone_drawdown_sensitive" if parse_float(metrics["max_drawdown"]) < -35 else "high_growth_drawdown_within_watch_range",
        "sleeve_quality_status": final_status,
        "incremental_drawdown_contributor": drawdown_summary.get("main_incremental_drawdown_contributor", MISSING),
        "net_incremental_drawdown_effect": net_incremental_effect(drawdown_summary),
        "portfolio_CAGR_delta": decision.get("delta_CAGR", lead.get("delta_CAGR", MISSING)),
        "portfolio_Sharpe_delta": decision.get("delta_Sharpe", lead.get("delta_Sharpe", MISSING)),
        "portfolio_MaxDD_delta": decision.get("delta_MaxDD", lead.get("delta_MaxDD", MISSING)),
        "portfolio_Calmar_delta": decision.get("delta_Calmar", lead.get("delta_Calmar", MISSING)),
        "contribution_interpretation": contribution_interpretation(drawdown_summary, decision),
        "concentration_dependency_status": concentration_status,
        "required_next_step": next_step_for(final_status),
        **safety_flags(),
    }


def build_split_rows(created_at: str, dates: list[str], returns: list[float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split_name, fraction in [("split_60_40", 0.60), ("split_70_30", 0.70), ("split_80_20", 0.80)]:
        start = max(1, int(len(dates) * fraction))
        split_returns = returns[start:]
        metrics = backtest.metrics_for_returns(split_returns)
        rows.append(
            {
                "created_at": created_at,
                "split_name": split_name,
                "sleeve_name": HIGH_GROWTH_SLEEVE,
                "CAGR": metrics["cagr"],
                "Sharpe": metrics["sharpe"],
                "MaxDD": metrics["max_drawdown"],
                "Calmar": metrics["calmar"],
                "split_quality_status": split_quality_status(metrics),
                **safety_flags(),
            }
        )
    return rows


def build_drawdown_row(created_at: str, dates: list[str], returns: list[float]) -> dict[str, Any]:
    window = drawdown_window(dates, returns)
    trough_index = int(window["trough_index"])
    recovery_index = window.get("recovery_index")
    recovery_rows = int(recovery_index) - trough_index if recovery_index is not None else -1
    recovery_days = days_between(window["trough"], window["recovery"]) if recovery_index is not None else -1
    post_63 = window_return(returns, trough_index + 1, min(len(returns) - 1, trough_index + 63))
    post_126 = window_return(returns, trough_index + 1, min(len(returns) - 1, trough_index + 126))
    return {
        "created_at": created_at,
        "sleeve_name": HIGH_GROWTH_SLEEVE,
        "drawdown_start": window["start"],
        "drawdown_trough": window["trough"],
        "max_drawdown": rounded(window["maxdd"]),
        "recovery_date": window["recovery"],
        "recovery_rows": str(recovery_rows) if recovery_rows >= 0 else "unrecovered_or_not_available",
        "recovery_days": str(recovery_days) if recovery_days >= 0 else "unrecovered_or_not_available",
        "post_trough_63d_return": rounded(post_63),
        "post_trough_126d_return": rounded(post_126),
        "drawdown_recovery_status": drawdown_recovery_status(window["maxdd"], post_63, post_126, recovery_index is not None),
        **safety_flags(),
    }


def drawdown_window(dates: list[str], returns: list[float]) -> dict[str, Any]:
    equity = 1.0
    peak = 1.0
    peak_index = 0
    curve: list[float] = []
    worst = {
        "start": dates[0] if dates else "",
        "trough": dates[0] if dates else "",
        "maxdd": 0.0,
        "trough_index": 0,
        "peak": 1.0,
        "recovery": "unrecovered_or_not_available",
        "recovery_index": None,
    }
    for index, value in enumerate(returns):
        equity *= 1.0 + value
        curve.append(equity)
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = (equity / peak - 1.0) * 100.0 if peak else 0.0
        if drawdown < worst["maxdd"]:
            worst = {
                "start": dates[peak_index],
                "trough": dates[index],
                "maxdd": drawdown,
                "trough_index": index,
                "peak": peak,
                "recovery": "unrecovered_or_not_available",
                "recovery_index": None,
            }
    for index in range(int(worst["trough_index"]) + 1, len(curve)):
        if curve[index] >= float(worst["peak"]):
            worst["recovery"] = dates[index]
            worst["recovery_index"] = index
            break
    return worst


def final_quality_status(metrics: dict[str, str], split_rows: list[dict[str, Any]], drawdown_row: dict[str, Any]) -> str:
    if parse_float(metrics["max_drawdown"]) < -55:
        return STATUS_NOT_SUITABLE
    weak_splits = [row for row in split_rows if row.get("split_quality_status") == "split_quality_weak_or_unstable"]
    if len(weak_splits) >= 2:
        return STATUS_SPLIT_SENSITIVE
    if parse_float(drawdown_row.get("max_drawdown")) < -35:
        return STATUS_PROMISING
    return STATUS_PROMISING


def split_quality_status(metrics: dict[str, str]) -> str:
    if parse_float(metrics["calmar"]) > 0.5 and parse_float(metrics["sharpe"]) > 0.5:
        return "split_quality_pass_research_only"
    if parse_float(metrics["cagr"]) > 0:
        return "split_quality_mixed_manual_review"
    return "split_quality_weak_or_unstable"


def drawdown_recovery_status(maxdd: Any, post_63: float, post_126: float, recovered: bool) -> str:
    if not recovered:
        return "drawdown_recovery_manual_review_unrecovered"
    if parse_float(maxdd) < -35 and (post_63 > 0 or post_126 > 0):
        return "drawdown_sensitive_but_recovered_research_only"
    return "drawdown_recovery_pass_research_only"


def concentration_status_for(stream_rows: list[dict[str, str]]) -> str:
    component_fields = {"ticker_contribution", "component_contribution", "top_ticker_contribution", "selected_ticker_weight"}
    if any(component_fields & set(row) for row in stream_rows):
        return "ticker_concentration_data_available_for_manual_review"
    return "ticker_concentration_data_missing"


def build_summary_rows(
    created_at: str,
    final_status: str,
    review: dict[str, Any],
    split_rows: list[dict[str, Any]],
    drawdown: dict[str, Any],
) -> list[dict[str, Any]]:
    worst_split = min(split_rows, key=lambda row: parse_float(row.get("Calmar")), default={})
    items = [
        ("final_high_growth_sleeve_quality_status", final_status, "Cautious saved-output sleeve quality label."),
        ("selected_high_growth_sleeve", HIGH_GROWTH_SLEEVE, "Selected high-growth research sleeve."),
        ("sleeve_metrics", format_metrics(review), "High-growth sleeve headline metrics."),
        ("split_summary", format_split_summary(split_rows, worst_split), "Fixed split quality summary."),
        ("worst_drawdown_and_recovery", format_drawdown(drawdown), "Standalone sleeve drawdown and recovery."),
        ("contribution_to_selected_lead", format_contribution(review), "Portfolio contribution context copied from saved reports."),
        ("concentration_dependency_finding", review.get("concentration_dependency_status", MISSING), "Ticker/component attribution availability."),
        ("required_next_step", next_step_for(final_status), "Next research step only."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(
    created_at: str,
    final_status: str,
    review: dict[str, Any],
    split_rows: list[dict[str, Any]],
    drawdown: dict[str, Any],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    if final_status == STATUS_BLOCKED:
        return [blocker_row(created_at, "saved_output_completeness", STATUS_BLOCKED, "high", "missing high-growth saved return stream", NEXT_MISSING)]
    worst_split = min(split_rows, key=lambda row: parse_float(row.get("Calmar")), default={})
    rows = [
        blocker_row(created_at, "drawdown_sensitivity", drawdown.get("drawdown_recovery_status", MISSING), "medium", format_drawdown(drawdown), next_step_for(final_status)),
        blocker_row(created_at, "split_consistency", worst_split.get("split_quality_status", MISSING), "medium", format_split_summary(split_rows, worst_split), next_step_for(final_status)),
        blocker_row(created_at, "portfolio_contribution_context", "manual_review_required", "medium", format_contribution(review), next_step_for(final_status)),
        blocker_row(created_at, "execution_boundary", "blocked_non_executable_research_only", "high", "sleeve quality review is not an execution path", next_step_for(final_status)),
        blocker_row(created_at, "scheduling_boundary", "blocked_no_scheduling_change", "high", "sleeve quality review is not a schedule or cron change", next_step_for(final_status)),
    ]
    if review.get("concentration_dependency_status") == "ticker_concentration_data_missing":
        rows.append(
            blocker_row(
                created_at,
                "ticker_concentration_data_missing",
                "manual_review_required",
                "medium",
                "saved sleeve stream is available but ticker-level component attribution is not available",
                "consider_future_saved_output_only_component_concentration_report",
            )
        )
    if not inputs["lead_state"]:
        rows.append(blocker_row(created_at, "lead_state_context_missing", "manual_review_required", "medium", "multi_sleeve_lead_state.csv missing", next_step_for(final_status)))
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
        "crypto_execution_approved": False,
        "scheduling_approved": False,
    }


def blocked_review_row(created_at: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "review_name": "high_growth_sleeve_quality",
        "sleeve_name": HIGH_GROWTH_SLEEVE,
        "selected_lead_candidate": SELECTED_LEAD,
        "high_growth_weight_in_lead": "20",
        "high_growth_weight_in_previous_baseline": "15",
        "delta_high_growth_weight": "5",
        "CAGR": MISSING,
        "Sharpe": MISSING,
        "MaxDD": MISSING,
        "Calmar": MISSING,
        "annual_volatility": MISSING,
        "return_status": "blocked_missing_saved_stream",
        "drawdown_status": "blocked_missing_saved_stream",
        "sleeve_quality_status": STATUS_BLOCKED,
        "incremental_drawdown_contributor": MISSING,
        "net_incremental_drawdown_effect": MISSING,
        "portfolio_CAGR_delta": MISSING,
        "portfolio_Sharpe_delta": MISSING,
        "portfolio_MaxDD_delta": MISSING,
        "portfolio_Calmar_delta": MISSING,
        "contribution_interpretation": "blocked_missing_saved_stream",
        "concentration_dependency_status": "ticker_concentration_data_missing",
        "required_next_step": NEXT_MISSING,
        **safety_flags(),
    }


def blocked_split_rows(created_at: str) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "split_name": split,
            "sleeve_name": HIGH_GROWTH_SLEEVE,
            "CAGR": MISSING,
            "Sharpe": MISSING,
            "MaxDD": MISSING,
            "Calmar": MISSING,
            "split_quality_status": "split_quality_blocked_missing_saved_stream",
            **safety_flags(),
        }
        for split in ["split_60_40", "split_70_30", "split_80_20"]
    ]


def blocked_drawdown_row(created_at: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "sleeve_name": HIGH_GROWTH_SLEEVE,
        "drawdown_start": "",
        "drawdown_trough": "",
        "max_drawdown": MISSING,
        "recovery_date": "unrecovered_or_not_available",
        "recovery_rows": "unrecovered_or_not_available",
        "recovery_days": "unrecovered_or_not_available",
        "post_trough_63d_return": MISSING,
        "post_trough_126d_return": MISSING,
        "drawdown_recovery_status": "blocked_missing_saved_stream",
        **safety_flags(),
    }


def contribution_interpretation(drawdown_summary: dict[str, str], decision: dict[str, str]) -> str:
    contributor = drawdown_summary.get("main_incremental_drawdown_contributor", MISSING)
    net = net_incremental_effect(drawdown_summary)
    cagr = decision.get("delta_CAGR", MISSING)
    sharpe = decision.get("delta_Sharpe", MISSING)
    calmar = decision.get("delta_Calmar", MISSING)
    return f"20pct_high_growth_research_weight; contributor={contributor}; net_incremental_drawdown={net}; portfolio_deltas=CAGR={cagr},Sharpe={sharpe},Calmar={calmar}; manual_review_required"


def net_incremental_effect(drawdown_summary: dict[str, str]) -> str:
    value = drawdown_summary.get("incremental_high_growth_risk_summary", "")
    for token in value.replace(";", " ").split():
        if token.startswith("net="):
            return token.split("=", 1)[1].rstrip(",;")
    return MISSING


def next_step_for(status: str) -> str:
    if status == STATUS_BLOCKED:
        return NEXT_MISSING
    if status == STATUS_NOT_SUITABLE:
        return NEXT_NOT_SUITABLE
    return NEXT_MANUAL_REVIEW


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return [
        "High-growth sleeve quality review created. Saved-output-only research; no execution path.",
        f"final high-growth sleeve quality status: {summary.get('final_high_growth_sleeve_quality_status', MISSING)}",
        f"selected high-growth sleeve: {summary.get('selected_high_growth_sleeve', MISSING)}",
        f"sleeve metrics: {summary.get('sleeve_metrics', MISSING)}",
        f"split summary and worst split: {summary.get('split_summary', MISSING)}",
        f"worst drawdown and recovery: {summary.get('worst_drawdown_and_recovery', MISSING)}",
        f"contribution to selected lead: {summary.get('contribution_to_selected_lead', MISSING)}",
        f"concentration/dependency finding: {summary.get('concentration_dependency_finding', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        f"Saved review: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def format_metrics(row: dict[str, Any]) -> str:
    return f"{row.get('sleeve_name')}: CAGR={row.get('CAGR')}; Sharpe={row.get('Sharpe')}; MaxDD={row.get('MaxDD')}; Calmar={row.get('Calmar')}; annual_volatility={row.get('annual_volatility')}"


def format_split_summary(rows: list[dict[str, Any]], worst: dict[str, Any]) -> str:
    pass_count = sum(1 for row in rows if row.get("split_quality_status") == "split_quality_pass_research_only")
    return f"pass_count={pass_count}; worst={worst.get('split_name', MISSING)}; Calmar={worst.get('Calmar', MISSING)}; MaxDD={worst.get('MaxDD', MISSING)}; status={worst.get('split_quality_status', MISSING)}"


def format_drawdown(row: dict[str, Any]) -> str:
    return f"start={row.get('drawdown_start')}; trough={row.get('drawdown_trough')}; MaxDD={row.get('max_drawdown')}; recovery={row.get('recovery_date')}; rows={row.get('recovery_rows')}; 63d={row.get('post_trough_63d_return')}; 126d={row.get('post_trough_126d_return')}; status={row.get('drawdown_recovery_status')}"


def format_contribution(row: dict[str, Any]) -> str:
    return f"lead={row.get('selected_lead_candidate')}; weight={row.get('high_growth_weight_in_lead')}; previous_weight={row.get('high_growth_weight_in_previous_baseline')}; delta_weight={row.get('delta_high_growth_weight')}; contributor={row.get('incremental_drawdown_contributor')}; net_drawdown={row.get('net_incremental_drawdown_effect')}; portfolio_deltas=CAGR={row.get('portfolio_CAGR_delta')},Sharpe={row.get('portfolio_Sharpe_delta')},MaxDD={row.get('portfolio_MaxDD_delta')},Calmar={row.get('portfolio_Calmar_delta')}"


def window_return(returns: list[float], start: int, end: int) -> float:
    if start >= len(returns) or start > end:
        return 0.0
    equity = 1.0
    for value in returns[max(0, start) : min(len(returns), end + 1)]:
        equity *= 1.0 + value
    return (equity - 1.0) * 100.0


def days_between(start: str, end: str) -> int:
    try:
        from datetime import date

        return (date.fromisoformat(end) - date.fromisoformat(start)).days
    except (TypeError, ValueError):
        return -1


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rounded(value: Any) -> str:
    return str(round(parse_float(value), 4))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": True,
        "saved_output_only": True,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
        "orders_replaced": False,
        "alpaca_called": False,
        "yfinance_called": False,
        "live_position_read": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "live_trading_approved": False,
        "scheduling_approved": False,
        "shorting_approved": False,
        "leverage_approved": False,
        "margin_approved": False,
    }
