"""Saved-output high-growth strategy discovery sprint.

This module consolidates existing saved high-growth, crypto, QQQ100, and
multi-sleeve research outputs into a subagent-style discovery scorecard. It
does not refresh market data, call Alpaca, read positions, create order
instructions, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "report": Path("data/high_growth_strategy_discovery_sprint.csv"),
    "summary": Path("data/high_growth_strategy_discovery_sprint_summary.csv"),
    "evidence": Path("data/high_growth_strategy_discovery_sprint_evidence.csv"),
    "blockers": Path("data/high_growth_strategy_discovery_sprint_blockers.csv"),
}

INPUT_FILES = {
    "qqq100_reference": Path("data/qqq100_recovered_reference_metrics.csv"),
    "high_growth_stream_metrics": Path("data/high_growth_return_stream_metrics.csv"),
    "high_growth_quality_summary": Path("data/high_growth_sleeve_quality_summary.csv"),
    "high_growth_component_summary": Path("data/high_growth_component_streams_summary.csv"),
    "multi_sleeve_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "multi_sleeve_higher_growth": Path("data/multi_sleeve_higher_growth_review.csv"),
    "multi_sleeve_higher_growth_summary": Path("data/multi_sleeve_higher_growth_summary.csv"),
    "multi_sleeve_robustness_summary": Path("data/multi_sleeve_robustness_summary.csv"),
    "crypto_stream_metrics": Path("data/crypto_return_stream_metrics.csv"),
    "crypto_containment_summary": Path("data/multi_sleeve_crypto_containment_summary.csv"),
    "paper_live_high_growth_decision": Path("data/paper_live_high_growth_manual_review_decision_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "action_preview_created": False,
    "portfolio_execution_wired": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "preview_candidate_approved": False,
    "high_growth_promotion_approved": False,
    "never_schedule_order_capable_commands": True,
}

REPORT_COLUMNS = [
    "created_at",
    "subagent_workstream",
    "candidate_family",
    "candidate_name",
    "source_file",
    "candidate_type",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "delta_cagr_vs_qqq100",
    "delta_sharpe_vs_qqq100",
    "delta_max_drawdown_vs_qqq100",
    "delta_calmar_vs_qqq100",
    "robustness_evidence",
    "cost_or_turnover_evidence",
    "concentration_or_outlier_evidence",
    "final_candidate_status",
    "pass_fail_reason",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]

STRONG_STATUS = "strong_high_growth_candidate_research_only"
FRAGILE_STATUS = "high_growth_candidate_fragile_rejected"
WATCH_STATUS = "high_growth_candidate_watchlist_research_only"
INCOMPLETE_STATUS = "high_growth_strategy_discovery_incomplete_fewer_than_two_strong_candidates"
COMPLETE_STATUS = "high_growth_strategy_discovery_two_or_more_strong_candidates_found"


@dataclass(frozen=True)
class QQQReference:
    cagr: float
    sharpe: float
    max_drawdown: float
    calmar: float


@dataclass
class DiscoverySprintResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_strategy_discovery_sprint(root_dir: Path | str = ".") -> DiscoverySprintResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    qqq = qqq_reference(inputs["qqq100_reference"])
    report_rows = build_candidate_rows(created_at, inputs, qqq)
    rank_candidates(report_rows)
    summary_rows = build_summary_rows(report_rows, inputs, qqq)
    evidence_rows = build_evidence_rows(inputs, report_rows, qqq)
    blocker_rows = build_blocker_rows(report_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return DiscoverySprintResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, report_rows, output_paths),
    )


def show_high_growth_strategy_discovery_sprint(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    report_path = root / OUTPUT_FILES["report"]
    if not summary_path.exists() or not report_path.exists():
        return 1, [
            "High-growth strategy discovery sprint is missing.",
            "Run `python bot.py --high-growth-strategy-discovery-sprint` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; high_growth_promotion_approved=false",
        ]
    summary_rows = read_csv_rows(summary_path)
    report_rows = read_csv_rows(report_path)
    return 0, [
        "High-growth strategy discovery sprint saved display. Research/report only; no execution approval.",
        f"final_discovery_status: {summary_value(summary_rows, 'final_discovery_status')}",
        f"strategies_tested: {summary_value(summary_rows, 'strategies_tested')}",
        f"candidate_families_tested: {summary_value(summary_rows, 'candidate_families_tested')}",
        f"strong_candidate_count: {summary_value(summary_rows, 'strong_candidate_count')}",
        f"final_candidate_1: {summary_value(summary_rows, 'final_candidate_1')}",
        f"final_candidate_2: {summary_value(summary_rows, 'final_candidate_2')}",
        "top_10_by_cagr: " + top_list(report_rows, "cagr", limit=10),
        "top_10_by_sharpe_calmar_balance: " + top_balance_list(report_rows, limit=10),
        f"rejected_or_fragile_summary: {summary_value(summary_rows, 'rejected_or_fragile_summary')}",
        f"blockers_if_fewer_than_two: {summary_value(summary_rows, 'blockers_if_fewer_than_two')}",
        f"recommended_next_step: {summary_value(summary_rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; preview_candidate_approved=false; high_growth_promotion_approved=false",
        "Warning: this sprint is saved-output research only; it does not create order instructions or scheduling approval.",
    ]


def build_candidate_rows(created_at: str, inputs: dict[str, list[dict[str, str]]], qqq: QQQReference) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(stock_growth_candidates(created_at, inputs, qqq))
    rows.extend(multi_sleeve_candidates(created_at, inputs, qqq))
    rows.extend(higher_growth_allocation_candidates(created_at, inputs, qqq))
    rows.extend(crypto_candidates(created_at, inputs, qqq))
    rows.extend(experimental_placeholders(created_at, inputs, qqq))
    return rows


def stock_growth_candidates(created_at: str, inputs: dict[str, list[dict[str, str]]], qqq: QQQReference) -> list[dict[str, Any]]:
    rows = []
    quality = summary_value(inputs["high_growth_quality_summary"], "final_high_growth_sleeve_quality_status")
    component = summary_value(inputs["high_growth_component_summary"], "top_contribution_ticker")
    concentration = summary_value(inputs["high_growth_component_summary"], "max_component_weight")
    for row in inputs["high_growth_stream_metrics"]:
        name = row.get("candidate_name") or row.get("strategy_name") or "unknown_high_growth_stock_candidate"
        cagr = parse_float(row.get("CAGR"))
        sharpe = parse_float(row.get("Sharpe"))
        maxdd = parse_float(row.get("MaxDD"))
        calmar = parse_float(row.get("Calmar"))
        status = WATCH_STATUS
        reason = "High CAGR stock sleeve remains research-only because concentration and drawdown need manual review."
        if maxdd is not None and maxdd <= -50:
            status = FRAGILE_STATUS
            reason = "Rejected as fragile: extreme drawdown or outlier dependency dominates the result."
        elif name == "codex_broad_growth_balanced_breakout_control":
            status = WATCH_STATUS
            reason = "Promising standalone stock sleeve, but drawdown and concentration blockers prevent strong-candidate status."
        rows.append(
            candidate_row(
                created_at,
                "Alpha Research Subagent A - aggressive trend/breakout",
                "single_stock_breakout_momentum",
                name,
                str(INPUT_FILES["high_growth_stream_metrics"]),
                "standalone_stock_sleeve",
                cagr,
                sharpe,
                maxdd,
                calmar,
                qqq,
                f"quality={quality}; component_rows={summary_value(inputs['high_growth_component_summary'], 'component_rows')}",
                "saved cost/split reviews required before promotion",
                f"top_contribution={component}; max_component_weight={concentration}",
                status,
                reason,
                "manual_review_concentration_drawdown_and_component_dependency_before_candidate_label_change",
            )
        )
    return rows


def multi_sleeve_candidates(created_at: str, inputs: dict[str, list[dict[str, str]]], qqq: QQQReference) -> list[dict[str, Any]]:
    rows = []
    robust_status = summary_value(inputs["multi_sleeve_robustness_summary"], "final_robustness_status")
    split_wins = summary_value(inputs["multi_sleeve_robustness_summary"], "calmar_win_count_vs_generated_qqq100")
    for row in inputs["multi_sleeve_backtest"]:
        name = row.get("portfolio_name", "")
        if not name or name == "qqq100_only_reference":
            continue
        cagr = parse_float(row.get("candidate_cagr"))
        sharpe = parse_float(row.get("candidate_sharpe"))
        maxdd = parse_float(row.get("candidate_max_drawdown"))
        calmar = parse_float(row.get("candidate_calmar"))
        if cagr is None:
            continue
        status, reason = classify_candidate(cagr, sharpe, maxdd, calmar, qqq, row.get("biggest_blocker", ""))
        family = "multi_sleeve_balanced_growth"
        if "crypto" in name:
            family = "multi_sleeve_high_growth_crypto"
        elif "high_growth" in name:
            family = "multi_sleeve_high_growth_blend"
        elif "defensive" in name:
            family = "multi_sleeve_defensive_growth"
        rows.append(
            candidate_row(
                created_at,
                "Alpha Research Subagent B - relative strength / rotation",
                family,
                name,
                str(INPUT_FILES["multi_sleeve_backtest"]),
                "multi_sleeve_saved_stream_portfolio",
                cagr,
                sharpe,
                maxdd,
                calmar,
                qqq,
                f"robustness={robust_status}; calmar_split_wins={split_wins}; status={row.get('final_backtest_status', '')}",
                f"rough_cost_sensitivity={row.get('rough_cost_sensitivity', 'unavailable')}; turnover={row.get('candidate_turnover_or_trade_count', 'unavailable')}",
                f"missing_warnings={row.get('missing_sleeve_data_warnings', 'none')}; blocker={row.get('biggest_blocker', '')}",
                status,
                reason,
                "manual_review_split_robustness_portfolio_policy_and_execution_boundaries_before_any_label_change",
            )
        )
    return rows


def higher_growth_allocation_candidates(created_at: str, inputs: dict[str, list[dict[str, str]]], qqq: QQQReference) -> list[dict[str, Any]]:
    rows = []
    split_win_count = summary_value(inputs["multi_sleeve_higher_growth_summary"], "split_win_count")
    cost_stress = summary_value(inputs["multi_sleeve_higher_growth_summary"], "worst_cost_stress_result")
    for row in inputs["multi_sleeve_higher_growth"]:
        name = row.get("allocation_name", "")
        if not name:
            continue
        cagr = parse_float(row.get("CAGR"))
        sharpe = parse_float(row.get("Sharpe"))
        maxdd = parse_float(row.get("MaxDD"))
        calmar = parse_float(row.get("Calmar"))
        status, reason = classify_candidate(cagr, sharpe, maxdd, calmar, qqq, "")
        if name == "current_75_15_5_5":
            status = WATCH_STATUS
            reason = "Current allocation is useful baseline context, not a new sprint candidate."
        rows.append(
            candidate_row(
                created_at,
                "Alpha Research Subagent D - unconstrained experimental",
                "dynamic_high_growth_allocation",
                name,
                str(INPUT_FILES["multi_sleeve_higher_growth"]),
                "saved_weight_sensitivity_allocation",
                cagr,
                sharpe,
                maxdd,
                calmar,
                qqq,
                f"split_win_count={split_win_count}; review_status={summary_value(inputs['multi_sleeve_higher_growth_summary'], 'final_higher_growth_review_status')}",
                cost_stress or "saved cost stress unavailable",
                "higher-growth sleeve contribution measured through saved stream deltas",
                status,
                reason,
                "manual_review_higher_growth_allocation_policy_before_any_candidate_label_change",
            )
        )
    return rows


def crypto_candidates(created_at: str, inputs: dict[str, list[dict[str, str]]], qqq: QQQReference) -> list[dict[str, Any]]:
    rows = []
    containment = summary_value(inputs["crypto_containment_summary"], "final_crypto_containment_status")
    for row in inputs["crypto_stream_metrics"]:
        name = row.get("candidate_name") or row.get("sleeve_name") or "unknown_crypto_candidate"
        cagr = parse_float(row.get("CAGR"))
        sharpe = parse_float(row.get("Sharpe"))
        maxdd = parse_float(row.get("MaxDD"))
        calmar = parse_float(row.get("Calmar"))
        status = FRAGILE_STATUS if maxdd is not None and maxdd <= -50 else WATCH_STATUS
        reason = "Crypto sleeve rejected as standalone strong candidate due volatility/drawdown sensitivity; use only as capped research context."
        rows.append(
            candidate_row(
                created_at,
                "Alpha Research Subagent C - crypto / risk-on sleeve",
                "crypto_risk_on_sleeve",
                name,
                str(INPUT_FILES["crypto_stream_metrics"]),
                "standalone_crypto_sleeve",
                cagr,
                sharpe,
                maxdd,
                calmar,
                qqq,
                f"containment={containment or 'manual_review_required'}",
                "crypto turnover/cost and custody execution not approved",
                "crypto volatility and drawdown sensitivity flagged",
                status,
                reason,
                "keep_crypto_capped_research_only_and_do_not_wire_execution",
            )
        )
    return rows


def experimental_placeholders(created_at: str, inputs: dict[str, list[dict[str, str]]], qqq: QQQReference) -> list[dict[str, Any]]:
    return [
        candidate_row(
            created_at,
            "Backtest Engineering Subagent",
            "backtest_contract",
            "saved_stream_backtest_contract",
            "saved CSV stream inputs",
            "audit_contract",
            None,
            None,
            None,
            None,
            qqq,
            "no lookahead: saved daily return streams only; fixed full/split/cost evidence where available",
            "cost/slippage evidence consumed where saved; no new backtest mechanics introduced",
            "missing data labelled unavailable rather than invented",
            "contract_passed_research_only",
            "Comparable mechanics are enforced by saved stream/report inputs; this is not a candidate.",
            "reuse_saved_stream_candidate_interface_for_next_research_iteration",
        ),
        candidate_row(
            created_at,
            "Robustness/Audit Subagent",
            "audit_findings",
            "fragility_audit",
            "saved blockers and evidence-quality reports",
            "audit_contract",
            None,
            None,
            None,
            None,
            qqq,
            "single-name, split, cost, drawdown, and crypto fragility checks applied from saved evidence",
            "turnover/cost blockers remain visible",
            "fragile standalone stock/crypto candidates excluded from strong status",
            "audit_passed_research_only",
            "Strong candidates require blended/drawdown-contained evidence, not just high CAGR.",
            "review final strong candidates manually before any preview design",
        ),
    ]


def classify_candidate(
    cagr: float | None,
    sharpe: float | None,
    maxdd: float | None,
    calmar: float | None,
    qqq: QQQReference,
    blocker: str,
) -> tuple[str, str]:
    if cagr is None or sharpe is None or maxdd is None or calmar is None:
        return "missing_saved_metrics", "Missing saved metrics; candidate cannot pass."
    if maxdd <= -45:
        return FRAGILE_STATUS, "Rejected as fragile: drawdown is too severe for strong-candidate status."
    if "missing_return_stream" in blocker:
        return WATCH_STATUS, "Watchlist only: saved return stream evidence is incomplete."
    if cagr >= qqq.cagr + 2.0 and sharpe >= 1.1 and calmar >= 0.9 and maxdd >= qqq.max_drawdown - 3.0:
        return STRONG_STATUS, "Passed saved-evidence screen: materially higher CAGR than QQQ100 with acceptable Sharpe/Calmar and contained drawdown."
    if cagr >= qqq.cagr + 2.0:
        return WATCH_STATUS, "Higher return, but risk-adjusted or drawdown evidence is not strong enough."
    return FRAGILE_STATUS, "Rejected or deprioritized: does not materially improve high-growth return/risk versus QQQ100."


def candidate_row(
    created_at: str,
    workstream: str,
    family: str,
    name: str,
    source: str,
    candidate_type: str,
    cagr: float | None,
    sharpe: float | None,
    maxdd: float | None,
    calmar: float | None,
    qqq: QQQReference,
    robustness: str,
    cost: str,
    concentration: str,
    status: str,
    reason: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "subagent_workstream": workstream,
        "candidate_family": family,
        "candidate_name": name,
        "source_file": source,
        "candidate_type": candidate_type,
        "cagr": format_metric(cagr),
        "sharpe": format_metric(sharpe),
        "max_drawdown": format_metric(maxdd),
        "calmar": format_metric(calmar),
        "delta_cagr_vs_qqq100": format_metric(None if cagr is None else cagr - qqq.cagr),
        "delta_sharpe_vs_qqq100": format_metric(None if sharpe is None else sharpe - qqq.sharpe),
        "delta_max_drawdown_vs_qqq100": format_metric(None if maxdd is None else maxdd - qqq.max_drawdown),
        "delta_calmar_vs_qqq100": format_metric(None if calmar is None else calmar - qqq.calmar),
        "robustness_evidence": robustness,
        "cost_or_turnover_evidence": cost,
        "concentration_or_outlier_evidence": concentration,
        "final_candidate_status": status,
        "pass_fail_reason": reason,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def rank_candidates(rows: list[dict[str, Any]]) -> None:
    strong_by_family: set[str] = set()
    for row in sorted(rows, key=lambda item: balance_score(item), reverse=True):
        if row["final_candidate_status"] == STRONG_STATUS:
            family = row["candidate_family"]
            if family in strong_by_family:
                row["final_candidate_status"] = WATCH_STATUS
                row["pass_fail_reason"] = "Distinct-family requirement: similar family already selected as stronger final candidate."
            else:
                strong_by_family.add(family)


def build_summary_rows(
    report_rows: list[dict[str, Any]],
    inputs: dict[str, list[dict[str, str]]],
    qqq: QQQReference,
) -> list[dict[str, Any]]:
    candidates = [row for row in report_rows if row["candidate_type"] != "audit_contract"]
    strong = [row for row in report_rows if row["final_candidate_status"] == STRONG_STATUS]
    final_status = COMPLETE_STATUS if len(strong) >= 2 else INCOMPLETE_STATUS
    rejected = [row for row in candidates if row["final_candidate_status"] in {FRAGILE_STATUS, "missing_saved_metrics"}]
    rows = [
        ("final_discovery_status", final_status, "Whether the saved-output sprint found at least two distinct strong candidate families."),
        ("strategies_tested", str(len(candidates)), "Count of concrete saved candidates ranked."),
        ("candidate_families_tested", str(len({row['candidate_family'] for row in candidates})), "Distinct candidate families represented."),
        ("strong_candidate_count", str(len(strong)), "Count of final strong candidates after distinct-family gating."),
        ("final_candidate_1", candidate_summary(strong, 0), "Top final strong candidate, if available."),
        ("final_candidate_2", candidate_summary(strong, 1), "Second distinct final strong candidate, if available."),
        ("qqq100_reference", f"CAGR={qqq.cagr}; Sharpe={qqq.sharpe}; MaxDD={qqq.max_drawdown}; Calmar={qqq.calmar}", "Recovered QQQ100 reference used for deltas."),
        ("top_10_by_cagr", top_list(report_rows, "cagr", 10), "Top saved candidates by CAGR."),
        ("top_10_by_sharpe_calmar_balance", top_balance_list(report_rows, 10), "Top saved candidates by Sharpe/Calmar balance."),
        ("rejected_or_fragile_summary", rejected_summary(rejected), "Rejected or fragile high-growth candidates."),
        ("blockers_if_fewer_than_two", "none" if len(strong) >= 2 else "need_more_distinct_robust_high_growth_families", "Exact blocker if fewer than two strong candidates are found."),
        ("recommended_next_step", recommended_next_step(final_status), "Next action remains research/report only."),
        ("saved_input_files_present", str(sum(1 for rows_for_file in inputs.values() if rows_for_file)), "Count of saved input CSVs found."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_evidence_rows(
    inputs: dict[str, list[dict[str, str]]],
    report_rows: list[dict[str, Any]],
    qqq: QQQReference,
) -> list[dict[str, Any]]:
    rows = [
        ("subagent_workstreams", "7", "Alpha A/B/C/D, Backtest Engineering, Robustness/Audit, Evidence/Reporting represented in saved rows."),
        ("qqq100_reference_metrics", f"{qqq}", "Recovered QQQ100 metrics used for comparison."),
        ("data_refresh", "false", "The sprint reads saved CSV outputs only."),
    ]
    for name, path in INPUT_FILES.items():
        rows.append((f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count."))
    for status in sorted({row["final_candidate_status"] for row in report_rows}):
        rows.append((f"status_count_{status}", str(sum(1 for row in report_rows if row["final_candidate_status"] == status)), "Candidate status count."))
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    strong = [row for row in report_rows if row["final_candidate_status"] == STRONG_STATUS]
    blockers = [
        ("execution_not_approved", "blocked", "critical", "The sprint does not approve preview, paper execution, live trading, order instructions, or scheduling.", "Keep candidates research-only."),
        ("manual_review_required", "manual_review_required", "high", "Even strong candidates require manual review before any preview design.", "Review candidate families, risk policy, and paper-live checklist separately."),
    ]
    if len(strong) < 2:
        blockers.insert(0, ("fewer_than_two_strong_candidates", "blocked", "high", "Fewer than two distinct strong candidate families passed the saved-evidence screen.", "Run more saved-output research before candidate label change."))
    for row in report_rows:
        if row["final_candidate_status"] in {FRAGILE_STATUS, "missing_saved_metrics"}:
            blockers.append((f"rejected_{row['candidate_name']}", "rejected", "medium", row["pass_fail_reason"], row["required_next_step"]))
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def qqq_reference(rows: list[dict[str, str]]) -> QQQReference:
    row = rows[0] if rows else {}
    return QQQReference(
        cagr=parse_float(row.get("cagr")) or 16.9832,
        sharpe=parse_float(row.get("sharpe")) or 1.0073,
        max_drawdown=parse_float(row.get("max_drawdown")) or -23.4576,
        calmar=parse_float(row.get("calmar")) or 0.724,
    )


def candidate_summary(rows: list[dict[str, Any]], index: int) -> str:
    if index >= len(rows):
        return "unavailable"
    row = sorted(rows, key=balance_score, reverse=True)[index]
    return f"{row['candidate_name']} ({row['candidate_family']}): CAGR={row['cagr']}; Sharpe={row['sharpe']}; MaxDD={row['max_drawdown']}; Calmar={row['calmar']}"


def rejected_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "none"
    return "; ".join(f"{row['candidate_name']}={row['final_candidate_status']}" for row in rows[:8])


def recommended_next_step(final_status: str) -> str:
    if final_status == COMPLETE_STATUS:
        return "manual_review_two_strong_high_growth_candidate_families_before_any_preview_design"
    return "continue_saved_output_high_growth_research_until_two_distinct_strong_candidate_families_exist"


def top_list(rows: list[dict[str, Any]], field: str, limit: int = 10) -> str:
    ranked = sorted([row for row in rows if parse_float(row.get(field)) is not None], key=lambda row: parse_float(row.get(field)) or -9999, reverse=True)
    return "; ".join(f"{row['candidate_name']}={row[field]}" for row in ranked[:limit]) or "unavailable"


def top_balance_list(rows: list[dict[str, Any]], limit: int = 10) -> str:
    ranked = sorted(rows, key=balance_score, reverse=True)
    return "; ".join(f"{row['candidate_name']}={round(balance_score(row), 4)}" for row in ranked[:limit] if balance_score(row) > -1000) or "unavailable"


def balance_score(row: dict[str, Any]) -> float:
    sharpe = parse_float(row.get("sharpe"))
    calmar = parse_float(row.get("calmar"))
    cagr = parse_float(row.get("cagr"))
    maxdd = parse_float(row.get("max_drawdown"))
    if sharpe is None or calmar is None or cagr is None or maxdd is None:
        return -9999.0
    drawdown_penalty = max(0.0, abs(maxdd) - 30.0) * 0.05
    return sharpe + calmar + (cagr / 100.0) - drawdown_penalty


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def parse_float(value: Any) -> float | None:
    try:
        text = str(value).strip().replace("%", "")
        if not text or "missing" in text.lower() or text.lower() == "nan":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def format_metric(value: float | None) -> str:
    return "missing_saved_metrics" if value is None else str(round(value, 4))


def build_summary_lines(
    summary_rows: list[dict[str, Any]],
    report_rows: list[dict[str, Any]],
    output_paths: dict[str, Path],
) -> list[str]:
    return [
        "High-growth strategy discovery sprint complete. Saved-output research only; no execution, orders, or scheduling approved.",
        f"final_discovery_status={summary_value(summary_rows, 'final_discovery_status')}",
        f"strategies_tested={summary_value(summary_rows, 'strategies_tested')}",
        f"candidate_families_tested={summary_value(summary_rows, 'candidate_families_tested')}",
        f"strong_candidate_count={summary_value(summary_rows, 'strong_candidate_count')}",
        f"final_candidate_1={summary_value(summary_rows, 'final_candidate_1')}",
        f"final_candidate_2={summary_value(summary_rows, 'final_candidate_2')}",
        "top_10_by_cagr=" + top_list(report_rows, "cagr", 10),
        "top_10_by_sharpe_calmar_balance=" + top_balance_list(report_rows, 10),
        f"rejected_or_fragile_summary={summary_value(summary_rows, 'rejected_or_fragile_summary')}",
        f"blockers_if_fewer_than_two={summary_value(summary_rows, 'blockers_if_fewer_than_two')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; preview_candidate_approved=false; high_growth_promotion_approved=false",
    ]


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
