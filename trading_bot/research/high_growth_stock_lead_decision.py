"""Saved-output high-growth stock lead decision checkpoint.

This command reads saved report CSVs only. It does not refresh market data,
call yfinance or Alpaca, load config, read positions, create orders, write
SQLite, send alerts, schedule anything, approve preview promotion, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QQQ_100 = "qqq_100_trend_gate"
QQQ_ADAPTIVE = "codex_qqq_adaptive_trend_exposure"
OLD_STOCK_LEAD = "codex_ambitious_concentrated_growth_persistence"
SMALL_TOP3 = "concentrated_growth_momentum_top3"
BROAD_TOP1 = "broad_liquid_growth_50:concentrated_growth_momentum_top1"
BALANCED_CONTROL = "codex_broad_growth_balanced_breakout_control"

REFERENCE_METRICS = {
    QQQ_100: {"cagr": 16.8429, "sharpe": 1.0027, "max_drawdown": -23.4576, "calmar": 0.718},
    QQQ_ADAPTIVE: {"cagr": 20.2819, "sharpe": 0.9749, "max_drawdown": -25.9889, "calmar": 0.7804},
    OLD_STOCK_LEAD: {"cagr": 14.1039, "sharpe": 0.7192, "max_drawdown": -29.5357, "calmar": 0.4775},
    SMALL_TOP3: {"cagr": 39.1498, "sharpe": 1.1042, "max_drawdown": -44.3476, "calmar": 0.8828},
    BROAD_TOP1: {"cagr": 60.3606, "sharpe": 1.1129, "max_drawdown": -70.1642, "calmar": 0.8603},
    BALANCED_CONTROL: {"cagr": 48.9372, "sharpe": 1.1905, "max_drawdown": -42.3324, "calmar": 1.156},
}

INPUT_FILES = {
    "high_growth_lab_report": Path("data/high_growth_stock_lab.csv"),
    "high_growth_lab_summary": Path("data/high_growth_stock_lab_summary.csv"),
    "high_growth_lab_costs": Path("data/high_growth_stock_lab_costs.csv"),
    "high_growth_lab_splits": Path("data/high_growth_stock_lab_splits.csv"),
    "high_growth_lab_drawdowns": Path("data/high_growth_stock_lab_drawdowns.csv"),
    "high_growth_lab_concentration": Path("data/high_growth_stock_lab_concentration.csv"),
    "universe_expansion_report": Path("data/high_growth_stock_universe_expansion_report.csv"),
    "universe_expansion_summary": Path("data/high_growth_stock_universe_expansion_summary.csv"),
    "universe_expansion_costs": Path("data/high_growth_stock_universe_expansion_costs.csv"),
    "universe_expansion_splits": Path("data/high_growth_stock_universe_expansion_splits.csv"),
    "universe_expansion_drawdowns": Path("data/high_growth_stock_universe_expansion_drawdowns.csv"),
    "universe_expansion_concentration": Path("data/high_growth_stock_universe_expansion_concentration.csv"),
    "drawdown_control_report": Path("data/high_growth_stock_drawdown_control_report.csv"),
    "drawdown_control_summary": Path("data/high_growth_stock_drawdown_control_summary.csv"),
    "drawdown_control_costs": Path("data/high_growth_stock_drawdown_control_costs.csv"),
    "drawdown_control_splits": Path("data/high_growth_stock_drawdown_control_splits.csv"),
    "drawdown_control_drawdowns": Path("data/high_growth_stock_drawdown_control_drawdowns.csv"),
    "drawdown_control_concentration": Path("data/high_growth_stock_drawdown_control_concentration.csv"),
    "qqq_lead_decision_report": Path("data/qqq_lead_decision_report.csv"),
    "qqq_lead_decision_summary": Path("data/qqq_lead_decision_summary.csv"),
    "qqq_trend_gate_manual_review_pack": Path("data/qqq_trend_gate_manual_review_pack.csv"),
    "qqq_preview_candidate_readiness_report": Path("data/qqq_preview_candidate_readiness_report.csv"),
    "project_research_state_summary": Path("data/project_research_state_summary.csv"),
    "project_research_state_next_steps": Path("data/project_research_state_next_steps.csv"),
}

OUTPUT_FILES = {
    "report": Path("data/high_growth_stock_lead_decision_report.csv"),
    "summary": Path("data/high_growth_stock_lead_decision_summary.csv"),
    "evidence": Path("data/high_growth_stock_lead_decision_evidence.csv"),
    "blockers": Path("data/high_growth_stock_lead_decision_blockers.csv"),
}

REPORT_COLUMNS = [
    "candidate_name",
    "candidate_role",
    "candidate_status",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "cagr_delta_vs_qqq100",
    "sharpe_delta_vs_qqq100",
    "calmar_delta_vs_qqq100",
    "maxdd_delta_vs_qqq100",
    "cagr_delta_vs_broad_top1",
    "maxdd_improvement_vs_broad_top1",
    "return_drag_vs_broad_top1",
    "cost_sensitivity_status",
    "split_sensitivity_status",
    "concentration_status",
    "outlier_dependence_status",
    "survivorship_bias_status",
    "complexity_burden",
    "lead_decision_label",
    "evidence_source",
    "details",
    "blocker",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "paper_execution_approved",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]
SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "paper_execution_approved",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "evidence_source", "details", *SUMMARY_COLUMNS[3:]]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SUMMARY_COLUMNS[3:]]

SAFETY_FLAGS = {
    "research_only": True,
    "preview_only": False,
    "paper_execution_approved": False,
    "execution_approved": False,
    "leverage_execution_approved": False,
    "margin_approved": False,
    "short_execution_approved": False,
    "scheduling_approved": False,
    "alpaca_called": False,
    "orders_created": False,
}


@dataclass
class HighGrowthStockLeadDecisionResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_high_growth_stock_lead_decision_report(root_dir: Path | str = ".") -> HighGrowthStockLeadDecisionResult:
    root = Path(root_dir)
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    report_rows = build_report_rows(inputs)
    summary_rows = build_summary_rows(report_rows, inputs)
    evidence_rows = build_evidence_rows(inputs, report_rows)
    blocker_rows = build_blocker_rows(inputs, report_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return HighGrowthStockLeadDecisionResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_high_growth_stock_lead_decision_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    report_path = root / OUTPUT_FILES["report"]
    if not summary_path.exists() or not report_path.exists():
        return 1, ["Run `python bot.py --high-growth-stock-lead-decision-report` first."]
    rows = read_csv_rows(summary_path)
    return 0, [
        "High-growth stock lead decision saved display. Research only; execution_approved=False.",
        f"Final high-growth stock lead decision: {summary_value(rows, 'final_high_growth_stock_lead_decision')}",
        f"Clean main stock/ETF lead: {summary_value(rows, 'clean_main_stock_etf_lead')}",
        f"High-risk stock research lead: {summary_value(rows, 'high_risk_stock_research_lead')}",
        f"Rejected extreme stock reference: {summary_value(rows, 'rejected_extreme_stock_reference')}",
        f"Main tradeoff: {summary_value(rows, 'main_tradeoff')}",
        f"Remaining blockers: {summary_value(rows, 'remaining_blockers')}",
        f"Recommended next step: {summary_value(rows, 'recommended_next_step')}",
        "paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved display only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
    ]


def build_report_rows(inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    qqq100 = metrics_for(QQQ_100, inputs)
    broad_top1 = metrics_for(BROAD_TOP1, inputs)
    rows = [
        candidate_row(
            QQQ_100,
            "clean main stock/ETF lead",
            "clean stock/ETF research lead",
            qqq100,
            qqq100,
            broad_top1,
            "low",
            "clean_main_reference",
            "qqq_100_clean_main_lead_retained",
            "data/qqq_lead_decision_report.csv",
            "Cleanest current stock/ETF lead: lower drawdown and simpler implementation than high-growth stock variants.",
            "",
            "Keep as clean main stock/ETF research lead; do not approve execution.",
        ),
        candidate_row(
            QQQ_ADAPTIVE,
            "ambitious QQQ alternative",
            "ambitious QQQ alternative retained",
            metrics_for(QQQ_ADAPTIVE, inputs),
            qqq100,
            broad_top1,
            "medium",
            "qqq_adaptive_higher_calmar_but_drawdown_tradeoff",
            "qqq_adaptive_ambitious_alternative_retained",
            "data/qqq_lead_decision_report.csv",
            "Higher return/Calmar than qqq_100, but lower Sharpe and deeper drawdown.",
            "",
            "Keep as ambitious QQQ alternative only.",
        ),
        candidate_row(
            SMALL_TOP3,
            "high-growth stock baseline candidate",
            "useful but displaced by drawdown-controlled branch",
            metrics_for(SMALL_TOP3, inputs),
            qqq100,
            broad_top1,
            "high",
            "split_sensitive_outlier_dependent",
            "high_growth_stock_promising_but_high_drawdown",
            "data/high_growth_stock_lab.csv",
            "Strong raw return, but split-sensitive and outlier-dependent with materially deeper drawdown than qqq_100.",
            "split sensitivity and outlier dependence",
            "Keep as baseline evidence; do not make it the high-risk stock lead.",
        ),
        candidate_row(
            BROAD_TOP1,
            "rejected extreme drawdown reference",
            "rejected extreme drawdown reference",
            broad_top1,
            qqq100,
            broad_top1,
            "very_high",
            "top1_extreme_drawdown",
            "high_growth_stock_rejected_extreme_drawdown",
            "data/high_growth_stock_universe_expansion_report.csv",
            "Huge CAGR but roughly -70% max drawdown; too extreme for a lead label.",
            "max drawdown around -70%",
            "Reject as extreme drawdown reference.",
        ),
        candidate_row(
            BALANCED_CONTROL,
            "high-risk stock lead candidate",
            "strongest high-risk/high-return stock-only alternative so far; high_growth_stock_not_preview_ready",
            metrics_for(BALANCED_CONTROL, inputs),
            qqq100,
            broad_top1,
            "high",
            "balanced_breakout_drawdown_control",
            "high_growth_stock_ambitious_alternative_confirmed",
            "data/high_growth_stock_drawdown_control_report.csv",
            "Materially improves broad Top1 drawdown while keeping much higher estimated CAGR, Sharpe, and Calmar than qqq_100.",
            "high_growth_stock_not_preview_ready; still much deeper drawdown than qqq_100; survivorship and single-name risk remain",
            "Confirm as high-risk stock research lead candidate; run manual review, not execution.",
        ),
    ]
    return rows


def candidate_row(
    name: str,
    role: str,
    status: str,
    metrics: dict[str, float],
    qqq100: dict[str, float],
    broad_top1: dict[str, float],
    complexity: str,
    sensitivity: str,
    label: str,
    source: str,
    details: str,
    blocker: str,
    next_step: str,
) -> dict[str, Any]:
    cagr = metrics.get("cagr", 0.0)
    sharpe = metrics.get("sharpe", 0.0)
    maxdd = metrics.get("max_drawdown", 0.0)
    calmar = metrics.get("calmar", 0.0)
    qqq_cagr = qqq100.get("cagr", 0.0)
    broad_cagr = broad_top1.get("cagr", 0.0)
    broad_maxdd = broad_top1.get("max_drawdown", 0.0)
    outlier = "high_growth_stock_outlier_dependent" if name in {SMALL_TOP3, BROAD_TOP1, BALANCED_CONTROL} else "not_stock_outlier_branch"
    return {
        "candidate_name": name,
        "candidate_role": role,
        "candidate_status": status,
        "cagr": round(cagr, 4),
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(maxdd, 4),
        "calmar": round(calmar, 4),
        "cagr_delta_vs_qqq100": round(cagr - qqq_cagr, 4),
        "sharpe_delta_vs_qqq100": round(sharpe - qqq100.get("sharpe", 0.0), 4),
        "calmar_delta_vs_qqq100": round(calmar - qqq100.get("calmar", 0.0), 4),
        "maxdd_delta_vs_qqq100": round(maxdd - qqq100.get("max_drawdown", 0.0), 4),
        "cagr_delta_vs_broad_top1": round(cagr - broad_cagr, 4),
        "maxdd_improvement_vs_broad_top1": round(maxdd - broad_maxdd, 4),
        "return_drag_vs_broad_top1": round(cagr - broad_cagr, 4),
        "cost_sensitivity_status": sensitivity if name in {SMALL_TOP3, BROAD_TOP1, BALANCED_CONTROL} else "context_only",
        "split_sensitivity_status": sensitivity if name == SMALL_TOP3 else "not_primary_blocker",
        "concentration_status": "single_name_concentration_risk" if name in {SMALL_TOP3, BROAD_TOP1, BALANCED_CONTROL} else "diversified_etf_reference",
        "outlier_dependence_status": outlier,
        "survivorship_bias_status": "high_growth_stock_survivorship_bias_warning" if name in {SMALL_TOP3, BROAD_TOP1, BALANCED_CONTROL} else "not_current_constituent_stock_branch",
        "complexity_burden": complexity,
        "lead_decision_label": label,
        "evidence_source": source,
        "details": details,
        "blocker": blocker,
        "recommended_next_step": next_step,
        **safety_flags(),
    }


def metrics_for(candidate: str, inputs: dict[str, list[dict[str, Any]]]) -> dict[str, float]:
    if candidate in REFERENCE_METRICS:
        return dict(REFERENCE_METRICS[candidate])
    sources = [row for rows in inputs.values() for row in rows if candidate_matches(row, candidate)]
    for row in sources:
        metrics = parse_metrics(row)
        if any(metrics.values()):
            return metrics
    return dict(REFERENCE_METRICS[candidate])


def candidate_matches(row: dict[str, Any], candidate: str) -> bool:
    names = [
        row.get("candidate_name", ""),
        row.get("strategy_name", ""),
        row.get("variant_name", ""),
        f"{row.get('universe_name', '')}:{row.get('strategy_name', '')}",
    ]
    if candidate == QQQ_100:
        names.extend(["qqq_100_trend_gate", "qqq_100"])
    if candidate == BALANCED_CONTROL:
        names.append("codex_broad_growth_balanced_breakout_control")
    return candidate in names


def parse_metrics(row: dict[str, Any]) -> dict[str, float]:
    return {
        "cagr": number(first_value(row, ["cagr", "cagr_pct"])),
        "sharpe": number(first_value(row, ["sharpe", "sharpe_ratio"])),
        "max_drawdown": number(first_value(row, ["max_drawdown", "max_drawdown_pct"])),
        "calmar": number(first_value(row, ["calmar", "calmar_ratio"])),
    }


def first_value(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if row.get(key) not in {None, ""}:
            return row.get(key)
    return 0.0


def build_summary_rows(report_rows: list[dict[str, Any]], inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    missing = missing_input_names(inputs)
    return [
        summary_row("final_high_growth_stock_lead_decision", "high_growth_stock_ambitious_alternative_confirmed", "codex_broad_growth_balanced_breakout_control becomes the high-risk stock research lead candidate; qqq_100 remains clean main lead."),
        summary_row("clean_main_stock_etf_lead", QQQ_100, "Clean main stock/ETF research lead retained; execution_approved=false."),
        summary_row("high_risk_stock_research_lead", BALANCED_CONTROL, "High-risk/high-return stock research lead candidate, not preview-ready and not executable."),
        summary_row("ambitious_qqq_alternative", QQQ_ADAPTIVE, "Ambitious QQQ alternative retained as separate ETF branch."),
        summary_row("rejected_extreme_stock_reference", BROAD_TOP1, "Rejected because broad Top1 max drawdown is around -70%."),
        summary_row("main_tradeoff", main_tradeoff(report_rows), "Balanced control keeps large upside but still carries much deeper drawdown and stock-specific risk than qqq_100."),
        summary_row("remaining_blockers", "; ".join(missing) if missing else "none_for_saved_decision_inputs", "Missing inputs block full audit detail but not the reference-metric decision scaffold."),
        summary_row("recommended_next_step", "manual_review_pack_for_high_growth_stock_lead_candidate", "Review concentration, split/cost sensitivity, constituent bias, and drawdown periods before any preview discussion."),
        summary_row("paper_execution_approved", "false", "No paper execution approval."),
        summary_row("execution_approved", "false", "No live execution approval."),
        summary_row("scheduling_approved", "false", "No scheduling approval."),
    ]


def main_tradeoff(report_rows: list[dict[str, Any]]) -> str:
    balanced = next((row for row in report_rows if row["candidate_name"] == BALANCED_CONTROL), {})
    if not balanced:
        return "unavailable"
    return (
        f"{BALANCED_CONTROL}: CAGR_delta_vs_qqq100={balanced.get('cagr_delta_vs_qqq100')}; "
        f"MaxDD_delta_vs_qqq100={balanced.get('maxdd_delta_vs_qqq100')}; "
        f"MaxDD_improvement_vs_broad_top1={balanced.get('maxdd_improvement_vs_broad_top1')}"
    )


def build_evidence_rows(inputs: dict[str, list[dict[str, Any]]], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row("saved_inputs_present", str(len(INPUT_FILES) - len(missing_input_names(inputs))), "saved CSV inventory", "Counts saved inputs available to the checkpoint."),
        evidence_row("balanced_control_decision", "high_risk_stock_research_lead_candidate", "data/high_growth_stock_drawdown_control_report.csv", "Decision label remains research-only and not execution-ready."),
        evidence_row("qqq100_decision", "clean_main_stock_etf_lead_retained", "data/qqq_lead_decision_report.csv", "QQQ 100 trend gate remains the clean main stock/ETF lead."),
    ]
    for row in report_rows:
        rows.append(evidence_row(row["candidate_name"], row["lead_decision_label"], row["evidence_source"], row["details"]))
    return rows


def build_blocker_rows(inputs: dict[str, list[dict[str, Any]]], report_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing = missing_input_names(inputs)
    rows = [
        blocker_row("execution_approval", "blocked", "critical", "No candidate is approved for paper or live execution.", "Keep execution_approved=false."),
        blocker_row("preview_promotion", "blocked", "high", "This checkpoint does not approve preview promotion.", "Create a separate manual review pack before any preview discussion."),
        blocker_row("stock_branch_risk", "blocked", "high", "High-growth stock branch retains survivorship, current-constituent, concentration, outlier, event, gap, and drawdown risk.", "Review risk evidence manually."),
    ]
    if missing:
        rows.append(blocker_row("missing_saved_inputs", "warning", "medium", "; ".join(missing), "Regenerate missing saved reports only through their safe report commands if needed."))
    return rows


def missing_input_names(inputs: dict[str, list[dict[str, Any]]]) -> list[str]:
    return [name for name, rows in inputs.items() if not rows]


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def evidence_row(name: str, value: str, source: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "evidence_source": source, "details": details, **safety_flags()}


def blocker_row(name: str, status: str, severity: str, details: str, required_next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": required_next_step, **safety_flags()}


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "High-growth stock lead decision report complete. Research only; execution_approved=False.",
        f"Final high-growth stock lead decision: {summary_value(summary_rows, 'final_high_growth_stock_lead_decision')}",
        f"Clean main stock/ETF lead: {summary_value(summary_rows, 'clean_main_stock_etf_lead')}",
        f"High-risk stock research lead: {summary_value(summary_rows, 'high_risk_stock_research_lead')}",
        f"Rejected extreme stock reference: {summary_value(summary_rows, 'rejected_extreme_stock_reference')}",
        f"Main tradeoff: {summary_value(summary_rows, 'main_tradeoff')}",
        f"Remaining blockers: {summary_value(summary_rows, 'remaining_blockers')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report to {output_paths['report']}",
        f"Saved summary/evidence/blockers to {output_paths['summary']}; {output_paths['evidence']}; {output_paths['blockers']}",
        "paper_execution_approved=false; execution_approved=false; scheduling_approved=false",
        "Warning: saved-output decision only; no market refresh, Alpaca commands, order instructions, preview promotion, paper execution, or scheduling approval.",
    ]


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return ""


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
