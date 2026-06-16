"""Saved-output-only multi-strategy portfolio preview combiner.

This module reads existing CSV outputs and produces a non-executable overlap
view. It does not call Alpaca, refresh market data, read positions, create
orders, write SQLite trade logs, send alerts, schedule jobs, or approve
execution.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "preview": Path("data/multi_strategy_portfolio_preview.csv"),
    "summary": Path("data/multi_strategy_portfolio_preview_summary.csv"),
    "exposures": Path("data/multi_strategy_portfolio_preview_exposures.csv"),
    "conflicts": Path("data/multi_strategy_portfolio_preview_conflicts.csv"),
    "blockers": Path("data/multi_strategy_portfolio_preview_blockers.csv"),
}

INPUT_FILES = {
    "qqq100_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action": Path("data/qqq100_action_preview.csv"),
    "promoted_preview": Path("data/promoted_strategy_preview.csv"),
    "promoted_decision": Path("data/promoted_decision_preview.csv"),
    "defensive_state": Path("data/defensive_research_state_report.csv"),
    "defensive_preview": Path("data/defensive_allocation_preview.csv"),
    "defensive_decision": Path("data/defensive_allocation_decision_report.csv"),
    "high_growth_final": Path("data/high_growth_stock_final_validation_pack.csv"),
    "high_growth_branch": Path("data/high_growth_stock_branch_decision_checkpoint.csv"),
    "crypto_state": Path("data/crypto_research_state_report.csv"),
    "crypto_manual": Path("data/expanded_crypto_manual_review_pack.csv"),
    "project_state": Path("data/project_research_state_summary.csv"),
    "execution_eligibility": Path("data/execution_eligibility_report.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
}

QQQ100 = "qqq_100_trend_gate"
QQQ_TICKER = "QQQ"
HIGH_GROWTH = "codex_broad_growth_balanced_breakout_control"
CRYPTO_LEAD = "crypto_research_lead"

PREVIEW_COLUMNS = [
    "created_at",
    "sleeve_name",
    "strategy_name",
    "ticker_or_asset_group",
    "desired_position",
    "preview_status",
    "research_status",
    "source_file",
    "source_status",
    "proposed_portfolio_role",
    "proposed_weight_placeholder",
    "exposure_bucket",
    "overlap_group",
    "conflict_status",
    "blocker",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "portfolio_preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "portfolio_preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]

EXPOSURE_COLUMNS = [
    "exposure_bucket",
    "overlap_group",
    "sleeve_count",
    "sleeves",
    "tickers_or_asset_groups",
    "exposure_status",
    "details",
    "research_only",
    "preview_only",
    "portfolio_preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]

CONFLICT_COLUMNS = [
    "conflict_name",
    "conflict_status",
    "severity",
    "sleeves_involved",
    "details",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "portfolio_preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "portfolio_preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]


@dataclass
class MultiStrategyPortfolioPreviewResult:
    output_paths: dict[str, Path]
    preview_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    exposure_rows: list[dict[str, Any]]
    conflict_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_strategy_portfolio_preview(root_dir: Path | str = ".") -> MultiStrategyPortfolioPreviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv(root / path) for name, path in INPUT_FILES.items()}
    preview_rows = build_preview_rows(created_at, inputs)
    conflict_rows = build_conflict_rows(preview_rows)
    exposure_rows = build_exposure_rows(preview_rows)
    blocker_rows = build_blocker_rows(preview_rows, conflict_rows, inputs)
    summary_rows = build_summary_rows(preview_rows, conflict_rows, blocker_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["preview"], PREVIEW_COLUMNS, preview_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["exposures"], EXPOSURE_COLUMNS, exposure_rows)
    write_rows(output_paths["conflicts"], CONFLICT_COLUMNS, conflict_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return MultiStrategyPortfolioPreviewResult(
        output_paths=output_paths,
        preview_rows=preview_rows,
        summary_rows=summary_rows,
        exposure_rows=exposure_rows,
        conflict_rows=conflict_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["preview"]),
    )


def show_multi_strategy_portfolio_preview(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Multi-strategy portfolio preview is missing.",
            "Run `python bot.py --multi-strategy-portfolio-preview` first.",
            "execution_approved=false",
            "scheduling_approved=false",
        ]
    summary_rows = read_csv(summary_path)
    value = {row.get("summary_name", ""): row.get("summary_value", "") for row in summary_rows}
    return 0, [
        "Multi-strategy portfolio preview saved display. Preview/report only; not execution.",
        f"final_portfolio_preview_status: {value.get('final_portfolio_preview_status', 'unavailable')}",
        f"sleeves_detected: {value.get('sleeves_detected', 'unavailable')}",
        f"active_preview_candidates: {value.get('active_preview_candidate_count', 'unavailable')}",
        f"blocked_research_only_sleeves: {value.get('research_only_blocked_sleeve_count', 'unavailable')}",
        f"main_overlap_warnings: {value.get('major_overlap_warnings', 'unavailable')}",
        f"biggest_blocker: {value.get('biggest_blocker', 'unavailable')}",
        f"recommended_next_step: {value.get('recommended_next_step', 'unavailable')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "orders_created=false; orders_submitted=false; orders_cancelled=false",
    ]


def build_preview_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        qqq100_row(created_at, inputs),
        defensive_row(created_at, inputs),
        high_growth_row(created_at, inputs),
        crypto_row(created_at, inputs),
    ]
    rows.extend(promoted_preview_rows(created_at, inputs))
    missing = [name for name, data in inputs.items() if not data]
    if missing:
        rows.append(missing_inputs_row(created_at, missing))
    return rows


def qqq100_row(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    signal = first(inputs["qqq100_signal"])
    action = first(inputs["qqq100_action"])
    if not signal:
        return preview_row(
            created_at,
            "qqq100_trend_sleeve",
            QQQ100,
            QQQ_TICKER,
            "unknown",
            "missing_required_for_specific_check",
            "clean_main_lead_missing_saved_signal",
            str(INPUT_FILES["qqq100_signal"]),
            "missing_required_for_specific_check",
            "core_growth_trend_candidate",
            "40_percent_placeholder",
            "nasdaq_growth_tech",
            "growth_tech",
            "missing_required_for_specific_check",
            "missing_qqq100_preview_signal_pack",
            "Run python bot.py --qqq100-preview-signal-pack before portfolio combiner review.",
        )
    desired = clean(signal.get("desired_position") or action.get("desired_position") or "unknown")
    data_status = clean(signal.get("data_status") or "unknown")
    preview_status = "qqq100_core_growth_preview_candidate" if data_status == "ok" else "missing_required_for_specific_check"
    return preview_row(
        created_at,
        "qqq100_trend_sleeve",
        QQQ100,
        QQQ_TICKER,
        desired,
        preview_status,
        "clean_main_lead_promoted_preview_review",
        str(INPUT_FILES["qqq100_signal"]),
        data_status,
        "core_growth_trend_candidate",
        "40_percent_placeholder",
        "nasdaq_growth_tech",
        "growth_tech",
        "portfolio_combiner_preview_only",
        "none" if data_status == "ok" else "qqq100_saved_signal_not_ok",
        "Review combined exposure before any separate preview-mode or execution discussion.",
    )


def defensive_row(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    source_name = first_present_source(inputs, ["defensive_decision", "defensive_preview", "defensive_state"])
    source_status = "present" if source_name else "missing_optional_input"
    return preview_row(
        created_at,
        "defensive_etf_sleeve",
        "defensive_etf_context",
        infer_defensive_asset_group(inputs),
        "context_only",
        "defensive_sleeve_optional_context" if source_name else "missing_optional_input",
        "defensive_or_risk_control_candidate",
        str(INPUT_FILES[source_name]) if source_name else "defensive saved inputs",
        source_status,
        "defensive_or_risk_control_candidate",
        "40_percent_placeholder",
        "defensive_or_risk_control",
        "defensive",
        "potentially_complementary",
        "none" if source_name else "missing_defensive_saved_context",
        "Use defensive context as optional complement; do not execute.",
    )


def high_growth_row(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    source_name = first_present_source(inputs, ["high_growth_final", "high_growth_branch"])
    return preview_row(
        created_at,
        "high_growth_stock_research_sleeve",
        HIGH_GROWTH,
        "high_growth_stocks",
        "blocked",
        "high_growth_branch_blocked_research_only",
        "research_only_not_preview_ready",
        str(INPUT_FILES[source_name]) if source_name else "high-growth saved inputs",
        "present" if source_name else "missing_optional_input",
        "high_risk_research_only",
        "0_percent_execution_blocked_or_20_percent_research_discussion_placeholder",
        "high_growth_stock",
        "growth_tech",
        "blocked_not_preview_ready",
        "high_growth_branch_not_preview_ready",
        "Keep high-growth branch research-only; do not include in preview or execution.",
    )


def crypto_row(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    source_name = first_present_source(inputs, ["crypto_state", "crypto_manual"])
    return preview_row(
        created_at,
        "crypto_research_sleeve",
        CRYPTO_LEAD,
        "crypto",
        "blocked",
        "crypto_blocked_research_only",
        "research_only_not_preview_ready",
        str(INPUT_FILES[source_name]) if source_name else "crypto saved inputs",
        "present" if source_name else "missing_optional_input",
        "research_only_off_hours_monitoring_candidate",
        "0_percent_execution_blocked",
        "high_beta_crypto",
        "high_beta",
        "blocked_research_only",
        "crypto_not_preview_or_execution_approved",
        "Keep crypto research-only and separate from Alpaca/paper execution.",
    )


def promoted_preview_rows(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = []
    for source in inputs["promoted_preview"]:
        strategy = clean(source.get("strategy_name"))
        ticker = clean(source.get("ticker"))
        if not strategy or strategy == QQQ100:
            continue
        rows.append(
            preview_row(
                created_at,
                "promoted_preview_sleeve",
                strategy,
                ticker or "promoted_preview_asset",
                clean(source.get("desired_position")) or "unknown",
                clean(source.get("promotion_status")) or "preview_review_only",
                "promoted_preview_review_only",
                str(INPUT_FILES["promoted_preview"]),
                "present",
                "preview_review_only",
                "discussion_placeholder_only",
                exposure_bucket_for(ticker, strategy),
                overlap_group_for(ticker, strategy),
                conflict_status_for(ticker, strategy),
                "none",
                "Review alongside QQQ100 and defensive context before any separate execution discussion.",
            )
        )
    return rows


def missing_inputs_row(created_at: str, missing_input_names: list[str]) -> dict[str, Any]:
    missing_files = ",".join(str(INPUT_FILES[name]) for name in missing_input_names)
    return preview_row(
        created_at,
        "unavailable_or_missing_sleeve",
        "saved_input_availability_context",
        "unavailable_or_missing",
        "not_applicable",
        "missing_optional_or_required_saved_inputs",
        "saved_output_context_incomplete",
        missing_files,
        "missing_saved_inputs",
        "unavailable_context_only",
        "0_percent_execution_blocked",
        "unavailable",
        "unavailable",
        "saved_input_incomplete_warning",
        "missing_saved_outputs_for_full_portfolio_review",
        "Run the relevant saved-output reports before treating this preview as a complete portfolio review.",
    )


def build_conflict_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    qqq_long = any(row["sleeve_name"] == "qqq100_trend_sleeve" and row["desired_position"] == "long" for row in rows)
    high_growth = any(row["sleeve_name"] == "high_growth_stock_research_sleeve" for row in rows)
    crypto = any(row["sleeve_name"] == "crypto_research_sleeve" for row in rows)
    defensive = any(row["sleeve_name"] == "defensive_etf_sleeve" and row["source_status"] == "present" for row in rows)
    tech_etf = any(clean(row["ticker_or_asset_group"]).upper() == "XLK" for row in rows)
    if qqq_long and high_growth:
        conflicts.append(conflict_row("growth_tech_overlap_warning", "growth_tech_overlap_warning", "warning", "qqq100_trend_sleeve,high_growth_stock_research_sleeve", "QQQ and high-growth mega-cap stock research can stack Nasdaq/growth/tech exposure.", "Keep high-growth blocked; review overlap before any future preview discussion."))
    if qqq_long and tech_etf:
        conflicts.append(conflict_row("tech_overlap_warning", "tech_overlap_warning", "warning", "qqq100_trend_sleeve,defensive_or_promoted_tech_etf", "QQQ and XLK/technology ETF exposure may stack technology risk.", "Review duplicate technology exposure before any preview expansion."))
    if qqq_long and crypto:
        conflicts.append(conflict_row("high_beta_stack_warning", "high_beta_stack_warning", "warning", "qqq100_trend_sleeve,crypto_research_sleeve", "QQQ and crypto can stack high-beta risk.", "Keep crypto blocked and review high-beta exposure separately."))
    if qqq_long and defensive:
        conflicts.append(conflict_row("qqq_defensive_complement", "potentially_complementary", "info", "qqq100_trend_sleeve,defensive_etf_sleeve", "A defensive ETF sleeve may complement QQQ trend exposure in a future design review.", "Keep as discussion context only."))
    if not conflicts:
        conflicts.append(conflict_row("no_major_overlap_detected", "pass", "info", "none", "No major overlap warning was detected from saved rows.", "Continue saved-output review only."))
    return conflicts


def build_exposure_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["exposure_bucket"], row["overlap_group"])].append(row)
    exposure_rows = []
    for (bucket, overlap), bucket_rows in sorted(grouped.items()):
        status = "overlap_review_required" if len(bucket_rows) > 1 and overlap in {"growth_tech", "high_beta"} else "context_only"
        exposure_rows.append(
            {
                "exposure_bucket": bucket,
                "overlap_group": overlap,
                "sleeve_count": len(bucket_rows),
                "sleeves": ",".join(sorted({row["sleeve_name"] for row in bucket_rows})),
                "tickers_or_asset_groups": ",".join(sorted({row["ticker_or_asset_group"] for row in bucket_rows})),
                "exposure_status": status,
                "details": "Saved-output exposure grouping only; no sizing or orders.",
                **safety_flags(),
            }
        )
    return exposure_rows


def build_blocker_rows(
    rows: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    blockers = [
        blocker_row("execution_blocked", "blocked", "critical", "Portfolio combiner does not approve execution.", "Keep all strategy sleeves disconnected from execution."),
        blocker_row("scheduling_not_approved", "blocked", "high", "Scheduling is not approved.", "Do not schedule this preview as an execution workflow."),
    ]
    for row in rows:
        if clean(row.get("blocker")) not in {"", "none"}:
            blockers.append(blocker_row(clean(row["blocker"]), "blocked" if "blocked" in clean(row["blocker"]) else "warning", "warning", f"{row['sleeve_name']}: {row['source_status']}", row["recommended_next_step"]))
    for conflict in conflicts:
        if conflict["severity"] == "warning":
            blockers.append(blocker_row(conflict["conflict_name"], "warning", "warning", conflict["details"], conflict["recommended_next_step"]))
    for name, path in INPUT_FILES.items():
        if not inputs[name] and name not in {"qqq100_signal"}:
            blockers.append(blocker_row(f"missing_optional_input_{name}", "missing_optional_input", "info", f"{path} was not present; command continued.", "Run the source report later if that sleeve needs review."))
    return dedupe_blockers(blockers)


def build_summary_rows(
    rows: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    active_preview_count = sum(1 for row in rows if row["preview_status"] in {"qqq100_core_growth_preview_candidate", "preview_candidate"})
    blocked_research_count = sum(1 for row in rows if "blocked" in row["preview_status"] or row["research_status"].startswith("research_only"))
    warning_names = [row["conflict_name"] for row in conflicts if row["severity"] == "warning"]
    biggest_blocker = next((row["blocker_name"] for row in blockers if row["severity"] in {"critical", "warning"}), "none")
    final_status = "multi_strategy_portfolio_preview_created"
    next_step = "Review overlap warnings and blockers manually; do not create orders or execution wiring."
    return [
        summary_row("final_portfolio_preview_status", final_status, "Saved-output portfolio combiner preview was created."),
        summary_row("sleeves_detected", ",".join(sorted({row["sleeve_name"] for row in rows})), "Sleeves detected from saved inputs and fixed research-only blockers."),
        summary_row("active_preview_candidate_count", str(active_preview_count), "Count of saved rows currently usable as preview candidates."),
        summary_row("research_only_blocked_sleeve_count", str(blocked_research_count), "Research-only or blocked sleeves remain non-executable."),
        summary_row("major_overlap_warnings", ",".join(warning_names) or "none", "Conflict rows with warning severity."),
        summary_row("biggest_blocker", biggest_blocker, "Largest blocker from saved-output portfolio preview."),
        summary_row("recommended_next_step", next_step, "Manual review only; no execution."),
        summary_row("execution_status", "execution_blocked", "Execution remains blocked."),
        summary_row("scheduling_status", "scheduling_not_approved", "Scheduling remains unapproved."),
    ]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    values = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "Multi-strategy portfolio preview complete. Saved-output only; not execution.",
        f"final_portfolio_preview_status: {values.get('final_portfolio_preview_status', 'unavailable')}",
        f"sleeves_detected: {values.get('sleeves_detected', 'unavailable')}",
        f"active_preview_candidates: {values.get('active_preview_candidate_count', 'unavailable')}",
        f"blocked_research_only_sleeves: {values.get('research_only_blocked_sleeve_count', 'unavailable')}",
        f"main_overlap_warnings: {values.get('major_overlap_warnings', 'unavailable')}",
        f"biggest_blocker: {values.get('biggest_blocker', 'unavailable')}",
        f"recommended_next_step: {values.get('recommended_next_step', 'unavailable')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        f"Saved portfolio preview to {output_path}",
    ]


def preview_row(
    created_at: str,
    sleeve_name: str,
    strategy_name: str,
    ticker_or_asset_group: str,
    desired_position: str,
    preview_status: str,
    research_status: str,
    source_file: str,
    source_status: str,
    role: str,
    weight: str,
    exposure_bucket: str,
    overlap_group: str,
    conflict_status: str,
    blocker: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "sleeve_name": sleeve_name,
        "strategy_name": strategy_name,
        "ticker_or_asset_group": ticker_or_asset_group,
        "desired_position": desired_position,
        "preview_status": preview_status,
        "research_status": research_status,
        "source_file": source_file,
        "source_status": source_status,
        "proposed_portfolio_role": role,
        "proposed_weight_placeholder": weight,
        "exposure_bucket": exposure_bucket,
        "overlap_group": overlap_group,
        "conflict_status": conflict_status,
        "blocker": blocker,
        "recommended_next_step": next_step,
        **safety_flags(),
    }


def conflict_row(name: str, status: str, severity: str, sleeves: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "conflict_name": name,
        "conflict_status": status,
        "severity": severity,
        "sleeves_involved": sleeves,
        "details": details,
        "recommended_next_step": next_step,
        **safety_flags(),
    }


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "recommended_next_step": next_step,
        **safety_flags(),
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {
        "summary_name": name,
        "summary_value": value,
        "details": details,
        **safety_flags(),
    }


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": True,
        "portfolio_preview_only": True,
        "execution_approved": False,
        "paper_execution_approved": False,
        "scheduling_approved": False,
        "orders_created": False,
        "orders_submitted": False,
        "orders_cancelled": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
    }


def first(rows: list[dict[str, str]]) -> dict[str, str]:
    return rows[0] if rows else {}


def first_present_source(inputs: dict[str, list[dict[str, str]]], names: list[str]) -> str:
    return next((name for name in names if inputs[name]), "")


def infer_defensive_asset_group(inputs: dict[str, list[dict[str, str]]]) -> str:
    for name in ["defensive_preview", "defensive_decision", "defensive_state"]:
        for row in inputs[name]:
            for key in ["ticker", "ticker_or_asset_group", "asset_group", "component", "symbol"]:
                value = clean(row.get(key))
                if value:
                    return value
    return "defensive_etf"


def exposure_bucket_for(ticker: str, strategy: str) -> str:
    text = f"{ticker} {strategy}".upper()
    if "XLK" in text or "TECH" in text:
        return "technology_equity"
    if "QQQ" in text or "NASDAQ" in text:
        return "nasdaq_growth_tech"
    return "promoted_preview"


def overlap_group_for(ticker: str, strategy: str) -> str:
    bucket = exposure_bucket_for(ticker, strategy)
    if bucket in {"technology_equity", "nasdaq_growth_tech"}:
        return "growth_tech"
    return "promoted_preview"


def conflict_status_for(ticker: str, strategy: str) -> str:
    return "tech_overlap_warning" if exposure_bucket_for(ticker, strategy) == "technology_equity" else "portfolio_combiner_preview_only"


def dedupe_blockers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for row in rows:
        key = (row["blocker_name"], row["status"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def clean(value: Any) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                return []
            return [row for row in reader if any(clean(value) for value in row.values())]
    except FileNotFoundError:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
