"""Concise terminal display for current saved research state."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


STOCK_ETF_LEAD = "codex_ambitious_concentrated_growth_persistence"
STOCK_ETF_STATUS = "codex_ambitious_active_research_lead_cost_review_required"
STOCK_ETF_BLOCKER = "25 bps cost review not survived; survives 10 bps but not 25 bps"
CRYPTO_LEAD = "crypto_equal_weight_ex_highest_vol_2"
CRYPTO_STATUS = "crypto_manual_review_not_ready_for_preview_discussion"
CRYPTO_BLOCKERS = "fixed split sensitivity; exclusion-rule instability; BNB/TRX outlier dependence; cost review; high drawdown review"
RECOMMENDED_NEXT_STEP = "pause_strategy_iterations_and_improve_reporting"

PROJECT_STATE_FILES = {
    "summary": Path("data/project_research_state_summary.csv"),
    "refresh": Path("data/project_research_state_refresh.csv"),
    "next_steps": Path("data/project_research_state_next_steps.csv"),
}

FALLBACK_FILES = {
    "stock_summary": Path("data/codex_ambitious_lead_decision_summary.csv"),
    "crypto_manual_summary": Path("data/expanded_crypto_manual_review_summary.csv"),
    "crypto_lead_summary": Path("data/expanded_crypto_lead_decision_summary.csv"),
}


def show_current_research_state(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    project_rows = {
        name: read_csv(data_path / path.name)
        for name, path in PROJECT_STATE_FILES.items()
    }
    fallback_rows = {
        name: read_csv(data_path / path.name)
        for name, path in FALLBACK_FILES.items()
    }
    summary = project_rows["summary"]
    refresh = project_rows["refresh"]
    next_steps = project_rows["next_steps"]
    if not summary:
        return 1, [
            "CURRENT RESEARCH STATE",
            "Saved project research state is missing.",
            "Run `python bot.py --project-research-state-refresh` first.",
            "Note: display-only; no preview promotion or execution approval.",
        ]

    stock_status_and_blocker = summary_value(summary, "stock_etf_status_and_blocker")
    crypto_status_and_blockers = summary_value(summary, "crypto_status_and_blockers")
    execution_values = approval_values(summary + refresh + next_steps, "execution_approved")
    scheduling_values = approval_values(summary + refresh + next_steps, "scheduling_approved")
    return 0, [
        "CURRENT RESEARCH STATE",
        f"Stock/ETF lead: {summary_value(summary, 'stock_etf_active_research_lead') or fallback_value(fallback_rows['stock_summary'], 'selected_research_lead') or STOCK_ETF_LEAD}",
        f"Stock/ETF status: {status_part(stock_status_and_blocker) or STOCK_ETF_STATUS}",
        f"Stock/ETF blocker: {blocker_part(stock_status_and_blocker) or STOCK_ETF_BLOCKER}",
        "",
        f"Crypto lead: {summary_value(summary, 'crypto_research_lead') or fallback_value(fallback_rows['crypto_lead_summary'], 'selected_crypto_research_lead') or CRYPTO_LEAD}",
        f"Crypto status: {status_part(crypto_status_and_blockers) or fallback_value(fallback_rows['crypto_manual_summary'], 'final_manual_review_status') or CRYPTO_STATUS}",
        f"Crypto blockers: {blocker_part(crypto_status_and_blockers) or fallback_value(fallback_rows['crypto_manual_summary'], 'blocker_counts') or CRYPTO_BLOCKERS}",
        "",
        f"Recommended next step: {summary_value(summary, 'recommended_next_step') or RECOMMENDED_NEXT_STEP}",
        f"Safety: execution_approved={false_only(execution_values)}; scheduling_approved={false_only(scheduling_values)}",
        "Note: display-only; no preview promotion or execution approval; no Alpaca or paper-order connection.",
    ]


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("metric_name") == key or row.get("check_name") == key or row.get("strategy_name") == key:
            return str(row.get("metric_value", ""))
    return ""


def fallback_value(rows: list[dict[str, Any]], key: str) -> str:
    return summary_value(rows, key)


def status_part(value: str) -> str:
    if "; blocker=" in value:
        return value.split("; blocker=", 1)[0]
    if "; blockers=" in value:
        return value.split("; blockers=", 1)[0]
    return value


def blocker_part(value: str) -> str:
    if "; blocker=" in value:
        return value.split("; blocker=", 1)[1]
    if "; blockers=" in value:
        return value.split("; blockers=", 1)[1]
    return ""


def approval_values(rows: list[dict[str, Any]], column: str) -> set[str]:
    return {str(row.get(column, "")).lower() for row in rows if str(row.get(column, "")) != ""}


def false_only(values: set[str]) -> str:
    if not values:
        return "false"
    if values == {"false"}:
        return "false"
    return ",".join(sorted(values))
