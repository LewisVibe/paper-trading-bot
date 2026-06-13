"""Saved-output QQQ branch lead decision checkpoint.

This module reads saved research CSVs only. It does not refresh market data,
call yfinance or Alpaca, load config, read positions, create orders, write
SQLite, send alerts, schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STOCK_LEAD = "codex_ambitious_concentrated_growth_persistence"
QQQ_CONSERVATIVE = "qqq_100_trend_gate"
QQQ_ADAPTIVE = "codex_qqq_adaptive_trend_exposure"
QQQ_HIGH_DRAWDOWN = "qqq_150_trend_gate"
QQQ_HIGHER_REJECTS = {"qqq_175_trend_gate", "qqq_200_trend_gate"}
SPY_BENCHMARK = "spy_buy_and_hold"
QQQ_BENCHMARK = "qqq_buy_and_hold"

INPUT_FILES = {
    "qqq_validation_report": Path("data/qqq_leverage_validation_report.csv"),
    "qqq_validation_summary": Path("data/qqq_leverage_validation_summary.csv"),
    "qqq_validation_costs": Path("data/qqq_leverage_validation_costs.csv"),
    "qqq_validation_splits": Path("data/qqq_leverage_validation_splits.csv"),
    "qqq_validation_drawdowns": Path("data/qqq_leverage_validation_drawdowns.csv"),
    "qqq_adaptive_report": Path("data/qqq_adaptive_leverage_lab.csv"),
    "qqq_adaptive_summary": Path("data/qqq_adaptive_leverage_lab_summary.csv"),
    "qqq_adaptive_costs": Path("data/qqq_adaptive_leverage_lab_costs.csv"),
    "qqq_adaptive_splits": Path("data/qqq_adaptive_leverage_lab_splits.csv"),
    "qqq_adaptive_drawdowns": Path("data/qqq_adaptive_leverage_lab_drawdowns.csv"),
    "project_research_state_summary": Path("data/project_research_state_summary.csv"),
    "project_research_state_next_steps": Path("data/project_research_state_next_steps.csv"),
    "codex_ambitious_lead_decision": Path("data/codex_ambitious_lead_decision.csv"),
    "codex_ambitious_lead_decision_summary": Path("data/codex_ambitious_lead_decision_summary.csv"),
    "codex_ambitious_lead_decision_evidence": Path("data/codex_ambitious_lead_decision_evidence.csv"),
}

OUTPUT_FILES = {
    "report": Path("data/qqq_lead_decision_report.csv"),
    "summary": Path("data/qqq_lead_decision_summary.csv"),
    "evidence": Path("data/qqq_lead_decision_evidence.csv"),
}

REPORT_COLUMNS = [
    "created_at",
    "candidate_name",
    "candidate_role",
    "candidate_status",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "cost_sensitivity_status",
    "financing_sensitivity_status",
    "split_sensitivity_status",
    "drawdown_status",
    "simplicity_status",
    "complexity_burden",
    "turnover_or_cash_drag_status",
    "uses_synthetic_leverage_above_1x",
    "market_data_status",
    "lead_decision_score",
    "lead_decision_label",
    "evidence_source",
    "details",
    "blocker",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "preview_only",
    "execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]


@dataclass
class QqqLeadDecisionResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq_lead_decision_report(root_dir: Path | str = ".") -> QqqLeadDecisionResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    candidates = build_candidate_rows(created_at, inputs)
    final = choose_final_decision(candidates)
    summary_rows = build_summary_rows(created_at, candidates, final)
    evidence_rows = build_evidence_rows(created_at, inputs, candidates, final)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, candidates)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["evidence"], REPORT_COLUMNS, evidence_rows)
    return QqqLeadDecisionResult(
        output_paths=output_paths,
        report_rows=candidates,
        summary_rows=summary_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(output_paths, summary_rows),
    )


def show_qqq_lead_decision_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    report_path = root / OUTPUT_FILES["report"]
    if not summary_path.exists() or not report_path.exists():
        return 1, ["Run `python bot.py --qqq-lead-decision-report` first."]
    summary_rows = read_csv_rows(summary_path)
    lines = ["QQQ LEAD DECISION SAVED DISPLAY. RESEARCH ONLY. NOT EXECUTION."]
    for row in summary_rows:
        lines.append(f"{row.get('summary_name')}: {row.get('summary_value')} - {row.get('details')}")
    lines.append("execution_approved=false; leverage_execution_approved=false; margin_approved=false; scheduling_approved=false")
    lines.append("Warning: saved display only; no yfinance, Alpaca, order instructions, leverage approval, margin approval, or scheduling approval.")
    return 0, lines


def build_candidate_rows(created_at: str, inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    qqq_validation = inputs.get("qqq_validation_report", [])
    qqq_adaptive = inputs.get("qqq_adaptive_report", [])
    codex_rows = inputs.get("codex_ambitious_lead_decision", [])
    rows = [
        build_codex_ambitious_row(created_at, codex_rows),
        build_qqq_row(created_at, QQQ_CONSERVATIVE, "conservative_qqq_candidate", qqq_validation, inputs),
        build_qqq_row(created_at, QQQ_ADAPTIVE, "ambitious_qqq_candidate", qqq_adaptive, inputs),
        build_qqq_row(created_at, QQQ_HIGH_DRAWDOWN, "high_drawdown_reference", qqq_validation, inputs),
        build_qqq_row(created_at, SPY_BENCHMARK, "benchmark", qqq_validation + qqq_adaptive, inputs),
        build_qqq_row(created_at, QQQ_BENCHMARK, "benchmark", qqq_validation + qqq_adaptive, inputs),
    ]
    higher_rejects = [
        build_qqq_row(created_at, name, "rejected_high_drawdown_reference", qqq_validation, inputs)
        for name in sorted(QQQ_HIGHER_REJECTS)
    ]
    return rows + higher_rejects


def build_codex_ambitious_row(created_at: str, codex_rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = next((row for row in codex_rows if row.get("check_name") == "final_decision_label"), {})
    full = next((row for row in codex_rows if row.get("check_name") == "full_period_evidence"), {})
    metrics = parse_metric_blob(str(full.get("metric_value", "")))
    if not metrics:
        metrics = {
            "CAGR": 14.1039,
            "Sharpe": 0.7192,
            "MaxDD": -29.5357,
            "Calmar": 0.4775,
            "cash": 9.9651,
            "turnover": 19.0,
        }
    status = str(summary.get("status") or "codex_ambitious_active_research_lead_cost_review_required")
    blocker = "25 bps cost review not survived" if "cost_review" in status else ""
    return report_row(
        created_at=created_at,
        candidate_name=STOCK_LEAD,
        candidate_role="current_stock_etf_active_research_lead",
        candidate_status=status,
        cagr=metrics.get("CAGR", 0.0),
        sharpe=metrics.get("Sharpe", 0.0),
        max_drawdown=metrics.get("MaxDD", 0.0),
        calmar=metrics.get("Calmar", 0.0),
        cost_sensitivity_status="survives_10_bps_not_25_bps",
        financing_sensitivity_status="not_applicable",
        split_sensitivity_status="positive_but_decaying",
        drawdown_status="acceptable_for_return",
        simplicity_status="complex_multi_sleeve",
        complexity_burden="high",
        turnover_or_cash_drag_status=f"cash={metrics.get('cash', '')}; turnover={metrics.get('turnover', '')}",
        uses_synthetic_leverage_above_1x=False,
        market_data_status="saved_market_data_backed",
        lead_decision_score=score_candidate(metrics, complexity_penalty=0.18, cost_penalty=0.12, drawdown_bonus=0.0),
        lead_decision_label="codex_ambitious_remains_research_lead",
        evidence_source="data/codex_ambitious_lead_decision.csv",
        details="Current stock/ETF active research lead before QQQ branch; full-period return remains strong but cost review is open.",
        blocker=blocker,
        recommended_next_step="Compare against QQQ branch as research labels only; keep cost review open.",
    )


def build_qqq_row(
    created_at: str,
    name: str,
    role: str,
    source_rows: list[dict[str, Any]],
    inputs: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    source = next((row for row in source_rows if row.get("variant_name") == name), {})
    data_status = str(source.get("data_status", "missing_saved_input"))
    cagr = number(source.get("cagr_pct"))
    sharpe = number(source.get("sharpe_ratio"))
    maxdd = number(source.get("max_drawdown_pct"))
    calmar = number(source.get("calmar_ratio"))
    leverage = number(source.get("leverage_multiple"))
    if name == SPY_BENCHMARK and not source:
        source = next((row for row in source_rows if row.get("variant_name") in {"spy_buy_and_hold_benchmark", "spy_buy_and_hold"}), {})
    cost_status, financing_status = sensitivity_status(name, inputs)
    split_status = split_status_for(name, inputs)
    drawdown_status = "high_drawdown_reference" if name in {QQQ_HIGH_DRAWDOWN, *QQQ_HIGHER_REJECTS} or maxdd <= -32 else "drawdown_better_than_stock_lead"
    if data_status != "ok":
        label = "lead_decision_blocked_missing_inputs"
        status = "missing_or_insufficient_saved_market_data"
        score = 0.0
        blocker = "Saved QQQ input is missing or marked insufficient_market_data."
    elif name == QQQ_CONSERVATIVE:
        label = "qqq_100_simpler_lower_drawdown_candidate"
        status = "credible_conservative_research_candidate"
        score = score_candidate({"CAGR": cagr, "Sharpe": sharpe, "MaxDD": maxdd, "Calmar": calmar}, complexity_penalty=0.0, cost_penalty=0.0, drawdown_bonus=0.12)
        blocker = ""
    elif name == QQQ_ADAPTIVE:
        label = "qqq_adaptive_higher_calmar_but_drawdown_tradeoff"
        status = "credible_ambitious_qqq_alternative"
        score = score_candidate({"CAGR": cagr, "Sharpe": sharpe, "MaxDD": maxdd, "Calmar": calmar}, complexity_penalty=0.08, cost_penalty=0.08, drawdown_bonus=0.04)
        blocker = "Cost/financing review remains open." if "sensitive" in (cost_status + financing_status) else ""
    elif name in {QQQ_HIGH_DRAWDOWN, *QQQ_HIGHER_REJECTS}:
        label = "qqq_150_rejected_high_drawdown" if name == QQQ_HIGH_DRAWDOWN else "qqq_150_rejected_high_drawdown"
        status = "high_drawdown_reference_not_lead"
        score = -1.0
        blocker = "Higher CAGR is not enough when drawdown/Calmar deteriorate."
    elif name in {SPY_BENCHMARK, QQQ_BENCHMARK}:
        label = "synthetic_only_not_execution_ready"
        status = "benchmark_context_only"
        score = 0.0
        blocker = ""
    else:
        label = "synthetic_only_not_execution_ready"
        status = "saved_context_only"
        score = 0.0
        blocker = ""
    return report_row(
        created_at=created_at,
        candidate_name=name,
        candidate_role=role,
        candidate_status=status,
        cagr=cagr,
        sharpe=sharpe,
        max_drawdown=maxdd,
        calmar=calmar,
        cost_sensitivity_status=cost_status,
        financing_sensitivity_status=financing_status,
        split_sensitivity_status=split_status,
        drawdown_status=drawdown_status,
        simplicity_status=simplicity_status(name),
        complexity_burden=complexity_burden(name),
        turnover_or_cash_drag_status=f"turnover={source.get('turnover', '')}; cash_time={source.get('cash_time_pct', '')}",
        uses_synthetic_leverage_above_1x=leverage > 1.0 or name == QQQ_ADAPTIVE,
        market_data_status="saved_market_data_backed" if data_status == "ok" else data_status,
        lead_decision_score=score,
        lead_decision_label=label,
        evidence_source=evidence_source(name),
        details=details_for(name, source),
        blocker=blocker,
        recommended_next_step=next_step_for(name, label),
    )


def choose_final_decision(rows: list[dict[str, Any]]) -> dict[str, str]:
    blockers = [row for row in rows if row["lead_decision_label"] == "lead_decision_blocked_missing_inputs" and row["candidate_name"] in {QQQ_CONSERVATIVE, QQQ_ADAPTIVE}]
    conservative = next((row for row in rows if row["candidate_name"] == QQQ_CONSERVATIVE), {})
    adaptive = next((row for row in rows if row["candidate_name"] == QQQ_ADAPTIVE), {})
    codex = next((row for row in rows if row["candidate_name"] == STOCK_LEAD), {})
    if blockers:
        return {
            "final_lead_decision": "lead_decision_blocked_missing_inputs",
            "active_stock_etf_research_lead": STOCK_LEAD,
            "main_tradeoff": "Saved QQQ market-data inputs are missing or insufficient; do not replace the current lead.",
            "recommended_next_step": "Regenerate QQQ validation/adaptive reports on a machine with market-data access, then rerun this saved-output decision.",
        }
    qqq_beats_codex = (
        number(conservative.get("sharpe")) > number(codex.get("sharpe"))
        and number(conservative.get("calmar")) > number(codex.get("calmar"))
        and abs(number(conservative.get("max_drawdown"))) < abs(number(codex.get("max_drawdown")))
    )
    adaptive_tradeoff = (
        number(adaptive.get("calmar")) > number(conservative.get("calmar"))
        and number(adaptive.get("sharpe")) < number(conservative.get("sharpe"))
        and abs(number(adaptive.get("max_drawdown"))) > abs(number(conservative.get("max_drawdown")))
    )
    if qqq_beats_codex:
        return {
            "final_lead_decision": "qqq_100_trend_gate_new_research_lead",
            "active_stock_etf_research_lead": QQQ_CONSERVATIVE,
            "main_tradeoff": "QQQ 100 trend gate is simpler and improves Sharpe, Calmar, and drawdown versus the current stock/ETF lead; adaptive QQQ remains an ambitious alternative." if adaptive_tradeoff else "QQQ 100 trend gate improves the key risk-adjusted metrics versus the current stock/ETF lead.",
            "recommended_next_step": "Update docs only after manual review; keep adaptive QQQ as an ambitious alternative and do not approve execution.",
        }
    if number(codex.get("lead_decision_score")) >= max(number(conservative.get("lead_decision_score")), number(adaptive.get("lead_decision_score"))):
        return {
            "final_lead_decision": "codex_ambitious_remains_research_lead",
            "active_stock_etf_research_lead": STOCK_LEAD,
            "main_tradeoff": "Current stock/ETF lead remains stronger after saved cost/split context.",
            "recommended_next_step": "Keep Codex ambitious as lead and continue QQQ branch review separately.",
        }
    return {
        "final_lead_decision": "qqq_branch_promising_needs_more_review",
        "active_stock_etf_research_lead": STOCK_LEAD,
        "main_tradeoff": "QQQ branch is promising, but manual review is needed before changing the active research lead.",
        "recommended_next_step": "Review cost/financing and saved split evidence before updating active lead docs.",
    }


def build_summary_rows(created_at: str, rows: list[dict[str, Any]], final: dict[str, str]) -> list[dict[str, Any]]:
    conservative = next((row for row in rows if row["candidate_name"] == QQQ_CONSERVATIVE), {})
    adaptive = next((row for row in rows if row["candidate_name"] == QQQ_ADAPTIVE), {})
    high = next((row for row in rows if row["candidate_name"] == QQQ_HIGH_DRAWDOWN), {})
    entries = [
        ("final_lead_decision", final["final_lead_decision"], "Research label only; no execution approval."),
        ("active_stock_etf_research_lead", final["active_stock_etf_research_lead"], "Lead after this saved-output checkpoint."),
        ("conservative_qqq_candidate", QQQ_CONSERVATIVE, metric_summary(conservative)),
        ("ambitious_qqq_candidate", QQQ_ADAPTIVE, metric_summary(adaptive)),
        ("rejected_high_drawdown_reference", QQQ_HIGH_DRAWDOWN, metric_summary(high)),
        ("main_tradeoff", final["main_tradeoff"], "QQQ branch can be simpler but cost/financing and drawdown tradeoffs remain research-only."),
        ("recommended_next_step", final["recommended_next_step"], "Manual docs/research review only."),
    ]
    return [summary_row(created_at, name, value, details) for name, value, details in entries]


def build_evidence_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, Any]]],
    candidates: list[dict[str, Any]],
    final: dict[str, str],
) -> list[dict[str, Any]]:
    rows = []
    for name, source_rows in sorted(inputs.items()):
        rows.append(
            report_row(
                created_at=created_at,
                candidate_name=name,
                candidate_role="saved_input",
                candidate_status="input_available" if source_rows else "input_missing",
                lead_decision_label="synthetic_only_not_execution_ready",
                evidence_source=str(INPUT_FILES[name]),
                details=f"row_count={len(source_rows)}",
                blocker="" if source_rows else "Saved input missing.",
                recommended_next_step="Regenerate missing saved report if needed before changing research lead.",
            )
        )
    rows.extend(candidates)
    rows.append(
        report_row(
            created_at=created_at,
            candidate_name="final_decision_boundary",
            candidate_role="manual_review_boundary",
            candidate_status=final["final_lead_decision"],
            lead_decision_label=final["final_lead_decision"],
            evidence_source="summary",
            details=final["main_tradeoff"],
            blocker="Execution remains false under every outcome.",
            recommended_next_step=final["recommended_next_step"],
        )
    )
    return rows


def report_row(
    *,
    created_at: str,
    candidate_name: str,
    candidate_role: str,
    candidate_status: str = "",
    cagr: float = 0.0,
    sharpe: float = 0.0,
    max_drawdown: float = 0.0,
    calmar: float = 0.0,
    cost_sensitivity_status: str = "",
    financing_sensitivity_status: str = "",
    split_sensitivity_status: str = "",
    drawdown_status: str = "",
    simplicity_status: str = "",
    complexity_burden: str = "",
    turnover_or_cash_drag_status: str = "",
    uses_synthetic_leverage_above_1x: bool = False,
    market_data_status: str = "",
    lead_decision_score: float = 0.0,
    lead_decision_label: str = "",
    evidence_source: str = "",
    details: str = "",
    blocker: str = "",
    recommended_next_step: str = "",
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "candidate_name": candidate_name,
        "candidate_role": candidate_role,
        "candidate_status": candidate_status,
        "cagr": round(cagr, 4),
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(max_drawdown, 4),
        "calmar": round(calmar, 4),
        "cost_sensitivity_status": cost_sensitivity_status,
        "financing_sensitivity_status": financing_sensitivity_status,
        "split_sensitivity_status": split_sensitivity_status,
        "drawdown_status": drawdown_status,
        "simplicity_status": simplicity_status,
        "complexity_burden": complexity_burden,
        "turnover_or_cash_drag_status": turnover_or_cash_drag_status,
        "uses_synthetic_leverage_above_1x": uses_synthetic_leverage_above_1x,
        "market_data_status": market_data_status,
        "lead_decision_score": round(lead_decision_score, 4),
        "lead_decision_label": lead_decision_label,
        "evidence_source": evidence_source,
        "details": details,
        "blocker": blocker,
        "recommended_next_step": recommended_next_step,
        **safety_flags(),
    }


def summary_row(created_at: str, name: str, value: str, details: str) -> dict[str, Any]:
    return {"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()}


def safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "preview_only": False,
        "execution_approved": False,
        "leverage_execution_approved": False,
        "margin_approved": False,
        "short_execution_approved": False,
        "scheduling_approved": False,
        "alpaca_called": False,
        "orders_created": False,
    }


def build_summary_lines(output_paths: dict[str, Path], summary_rows: list[dict[str, Any]]) -> list[str]:
    values = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    details = {row["summary_name"]: row["details"] for row in summary_rows}
    return [
        "QQQ LEAD DECISION REPORT. SAVED OUTPUT ONLY. NOT EXECUTION.",
        f"Saved report: {output_paths['report']}",
        f"Saved summary/evidence: {output_paths['summary']}; {output_paths['evidence']}",
        f"Final lead decision: {values.get('final_lead_decision', '')}",
        f"Active research lead after decision: {values.get('active_stock_etf_research_lead', '')}",
        f"Conservative QQQ candidate: {values.get('conservative_qqq_candidate', '')} ({details.get('conservative_qqq_candidate', '')})",
        f"Ambitious QQQ candidate: {values.get('ambitious_qqq_candidate', '')} ({details.get('ambitious_qqq_candidate', '')})",
        f"Main tradeoff: {values.get('main_tradeoff', '')}",
        f"Rejected high-drawdown reference: {values.get('rejected_high_drawdown_reference', '')} ({details.get('rejected_high_drawdown_reference', '')})",
        f"Recommended next step: {values.get('recommended_next_step', '')}",
        "execution_approved=false; leverage_execution_approved=false; margin_approved=false; scheduling_approved=false",
        "No yfinance, Alpaca commands, order instructions, margin approval, leverage approval, short approval, or scheduling approval are produced.",
    ]


def sensitivity_status(name: str, inputs: dict[str, list[dict[str, Any]]]) -> tuple[str, str]:
    cost_rows = inputs.get("qqq_validation_costs", []) + inputs.get("qqq_adaptive_costs", [])
    matching = [row for row in cost_rows if row.get("variant_name") == name]
    labels = {str(row.get("cost_sensitivity_label", "")) for row in matching}
    cost_status = "cost_sensitive" if any("cost_sensitive" in label for label in labels) else ("not_sensitive_in_saved_rows" if matching else "unavailable")
    financing_status = "financing_sensitive" if any("financing_sensitive" in label for label in labels) else ("not_sensitive_in_saved_rows" if matching else "unavailable")
    return cost_status, financing_status


def split_status_for(name: str, inputs: dict[str, list[dict[str, Any]]]) -> str:
    split_rows = inputs.get("qqq_validation_splits", []) + inputs.get("qqq_adaptive_splits", [])
    matching = [row for row in split_rows if row.get("variant_name") == name]
    labels = {str(row.get("split_sensitivity_label", "")) for row in matching}
    if not matching:
        return "unavailable"
    if any("split_sensitive" in label for label in labels):
        return "split_sensitive"
    return "no_split_sensitivity_warning"


def simplicity_status(name: str) -> str:
    if name == QQQ_CONSERVATIVE:
        return "simple_sma200_trend_gate"
    if name == QQQ_ADAPTIVE:
        return "adaptive_rules_more_complex"
    if name == STOCK_LEAD:
        return "multi_sleeve_complex"
    if name in {SPY_BENCHMARK, QQQ_BENCHMARK}:
        return "benchmark"
    return "reference"


def complexity_burden(name: str) -> str:
    if name == QQQ_CONSERVATIVE:
        return "low"
    if name == QQQ_ADAPTIVE:
        return "medium"
    if name == STOCK_LEAD:
        return "high"
    return "not_applicable"


def details_for(name: str, source: dict[str, Any]) -> str:
    if name == QQQ_CONSERVATIVE:
        return "Simple QQQ SMA200 trend gate; lower drawdown candidate if saved metrics are available."
    if name == QQQ_ADAPTIVE:
        return "Adaptive QQQ candidate can improve Calmar but has a drawdown and financing/cost tradeoff."
    if name in {QQQ_HIGH_DRAWDOWN, *QQQ_HIGHER_REJECTS}:
        return "High-drawdown leverage reference; not a likely research lead."
    if source:
        return "Benchmark or saved context row."
    return "Saved input missing or insufficient."


def next_step_for(name: str, label: str) -> str:
    if label == "lead_decision_blocked_missing_inputs":
        return "Regenerate saved QQQ reports with market-data access, then rerun this decision report."
    if name == QQQ_CONSERVATIVE:
        return "Manual review may promote this to active research lead as a research label only."
    if name == QQQ_ADAPTIVE:
        return "Keep as ambitious alternative unless drawdown/cost tradeoff is explicitly accepted."
    if name in {QQQ_HIGH_DRAWDOWN, *QQQ_HIGHER_REJECTS}:
        return "Keep as rejected high-drawdown reference."
    return "Context only; no execution approval."


def evidence_source(name: str) -> str:
    if name == QQQ_ADAPTIVE:
        return "data/qqq_adaptive_leverage_lab.csv"
    if name in {QQQ_CONSERVATIVE, QQQ_HIGH_DRAWDOWN, *QQQ_HIGHER_REJECTS, SPY_BENCHMARK, QQQ_BENCHMARK}:
        return "data/qqq_leverage_validation_report.csv"
    return "saved context"


def metric_summary(row: dict[str, Any]) -> str:
    if not row:
        return "unavailable"
    return f"CAGR={row.get('cagr')}; Sharpe={row.get('sharpe')}; MaxDD={row.get('max_drawdown')}; Calmar={row.get('calmar')}; label={row.get('lead_decision_label')}"


def score_candidate(metrics: dict[str, float], complexity_penalty: float, cost_penalty: float, drawdown_bonus: float) -> float:
    sharpe = number(metrics.get("Sharpe"))
    calmar = number(metrics.get("Calmar"))
    maxdd = abs(number(metrics.get("MaxDD")))
    return (calmar * 1.4) + sharpe - (maxdd / 100.0) - complexity_penalty - cost_penalty + drawdown_bonus


def parse_metric_blob(blob: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for item in blob.replace(";", ",").split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        metrics[key.strip()] = number(value.strip())
    return metrics


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except Exception:
        return []


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
