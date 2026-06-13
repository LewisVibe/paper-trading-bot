"""Project-wide saved research state refresh checkpoint.

This report consolidates stock/ETF and crypto research state from saved CSVs.
It is research/report-only and never touches broker, position, database, alert,
config, scheduling, order, or execution paths.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STOCK_ETF_LEAD = "qqq_100_trend_gate"
STOCK_ETF_STATUS = "qqq_100_trend_gate_new_research_lead"
STOCK_ETF_AMBITIOUS_ALTERNATIVE = "codex_qqq_adaptive_trend_exposure"
STOCK_ETF_REJECTED_HIGH_DRAWDOWN_REFERENCE = "qqq_150_trend_gate"
PREVIOUS_STOCK_ETF_LEAD = "codex_ambitious_concentrated_growth_persistence"
CRYPTO_LEAD = "crypto_equal_weight_ex_highest_vol_2"
CRYPTO_STATUS = "crypto_manual_review_not_ready_for_preview_discussion"

STOCK_INPUT_FILES = {
    "qqq_lead_decision_summary": Path("data/qqq_lead_decision_summary.csv"),
    "qqq_lead_decision_report": Path("data/qqq_lead_decision_report.csv"),
    "qqq_lead_decision_evidence": Path("data/qqq_lead_decision_evidence.csv"),
    "codex_lead_summary": Path("data/codex_ambitious_lead_decision_summary.csv"),
    "codex_lead_evidence": Path("data/codex_ambitious_lead_decision_evidence.csv"),
    "codex_validation_summary": Path("data/codex_ambitious_validation_summary.csv"),
    "codex_split_drawdown": Path("data/codex_ambitious_split_drawdown_validation.csv"),
    "stricter_manual_pack": Path("data/growth_biased_stricter_manual_review_pack.csv"),
    "stricter_cost_stress": Path("data/growth_biased_stricter_cost_turnover_stress_summary.csv"),
    "stricter_persistence": Path("data/growth_biased_stricter_persistence_filter_summary.csv"),
}

CRYPTO_INPUT_FILES = {
    "crypto_universe_summary": Path("data/crypto_universe_readiness_summary.csv"),
    "crypto_strategy_summary": Path("data/expanded_crypto_strategy_lab_summary.csv"),
    "crypto_robustness_summary": Path("data/expanded_crypto_robustness_summary.csv"),
    "crypto_crash_gate_summary": Path("data/crypto_equal_weight_crash_gate_summary.csv"),
    "crypto_volatility_summary": Path("data/crypto_equal_weight_volatility_scaling_summary.csv"),
    "crypto_capped_summary": Path("data/crypto_equal_weight_capped_risk_summary.csv"),
    "crypto_lead_summary": Path("data/expanded_crypto_lead_decision_summary.csv"),
    "crypto_split_summary": Path("data/crypto_lead_split_sensitivity_summary.csv"),
    "crypto_manual_review": Path("data/expanded_crypto_manual_review_summary.csv"),
}

OUTPUT_FILES = {
    "refresh": Path("data/project_research_state_refresh.csv"),
    "summary": Path("data/project_research_state_summary.csv"),
    "next_steps": Path("data/project_research_state_next_steps.csv"),
}

NEXT_STEP_LABELS = [
    "stock_etf_cost_review_next",
    "stock_etf_monitoring_dashboard_next",
    "crypto_manual_review_next",
    "crypto_cost_and_outlier_review_next",
    "project_dashboard_refresh_next",
    "pause_strategy_iterations_and_improve_reporting",
    "vps_monitoring_refresh_review",
    "insufficient_saved_inputs",
]

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "section",
    "check_name",
    "branch",
    "strategy_name",
    "metric_name",
    "metric_value",
    "status",
    "summary_label",
    "evidence",
    "recommended_next_step",
    "research_only",
    "preview_promotion_approved",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "leverage_execution_approved",
    "margin_approved",
    "short_execution_approved",
    "scheduling_approved",
    "alpaca_called",
    "orders_created",
]

DEFAULT_RECOMMENDATION = "pause_strategy_iterations_and_improve_reporting"


@dataclass
class ProjectResearchStateRefreshResult:
    refresh_path: Path
    summary_path: Path
    next_steps_path: Path
    refresh_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    next_step_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_project_research_state_refresh(data_dir: Path | str = "data") -> ProjectResearchStateRefreshResult:
    data_path = Path(data_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    stock_inputs = {name: read_csv(data_path / path.name) for name, path in STOCK_INPUT_FILES.items()}
    crypto_inputs = {name: read_csv(data_path / path.name) for name, path in CRYPTO_INPUT_FILES.items()}
    refresh_rows = build_refresh_rows(created_at, stock_inputs, crypto_inputs)
    next_step_rows = build_next_step_rows(created_at, stock_inputs, crypto_inputs)
    recommended = choose_recommended_next_step(stock_inputs, crypto_inputs, next_step_rows)
    summary_rows = build_summary_rows(created_at, stock_inputs, crypto_inputs, refresh_rows, next_step_rows, recommended)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["refresh"], refresh_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["next_steps"], next_step_rows)
    return ProjectResearchStateRefreshResult(
        refresh_path=output_paths["refresh"],
        summary_path=output_paths["summary"],
        next_steps_path=output_paths["next_steps"],
        refresh_rows=refresh_rows,
        summary_rows=summary_rows,
        next_step_rows=next_step_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_project_research_state_refresh_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    refresh = read_csv(data_path / OUTPUT_FILES["refresh"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    next_steps = read_csv(data_path / OUTPUT_FILES["next_steps"].name)
    if not refresh or not summary:
        return 1, ["Run `python bot.py --project-research-state-refresh` first."]
    execution_values = {str(row.get("execution_approved", "")).lower() for row in refresh + summary + next_steps}
    scheduling_values = {str(row.get("scheduling_approved", "")).lower() for row in refresh + summary + next_steps}
    return 0, [
        "Project research state refresh. Display only; execution_approved=False; scheduling_approved=False.",
        f"Stock/ETF active research lead: {summary_value(summary, 'stock_etf_active_research_lead')}",
        f"Stock/ETF status and blocker: {summary_value(summary, 'stock_etf_status_and_blocker')}",
        f"Crypto research lead: {summary_value(summary, 'crypto_research_lead')}",
        f"Crypto status and blockers: {summary_value(summary, 'crypto_status_and_blockers')}",
        f"Rejected/downgraded families: {summary_value(summary, 'rejected_or_downgraded_families')}",
        f"Recommended next step: {summary_value(summary, 'recommended_next_step')}",
        f"execution_approved values: {', '.join(sorted(execution_values)) or 'false'}",
        f"scheduling_approved values: {', '.join(sorted(scheduling_values)) or 'false'}",
        "Warning: this checkpoint does not approve preview promotion, execution, crypto execution, scheduling, or order instructions.",
    ]


def build_refresh_rows(
    created_at: str,
    stock_inputs: dict[str, list[dict[str, Any]]],
    crypto_inputs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    qqq_summary = stock_inputs.get("qqq_lead_decision_summary", [])
    rows = [
        row(created_at, "stock_etf_research_lead", "active_lead", "stock_etf", STOCK_ETF_LEAD, "lead_status", stock_status(stock_inputs), STOCK_ETF_STATUS, "stock_etf_cost_review_next", stock_evidence(stock_inputs)),
        row(created_at, "stock_etf_research_lead", "ambitious_alternative", "stock_etf", STOCK_ETF_AMBITIOUS_ALTERNATIVE, "lead_status", qqq_summary_value(qqq_summary, "ambitious_qqq_candidate") or STOCK_ETF_AMBITIOUS_ALTERNATIVE, "qqq_adaptive_higher_calmar_but_drawdown_tradeoff", "review_qqq_trend_gate_as_new_stock_etf_research_lead", "Higher CAGR/Calmar than qqq_100 trend gate, but lower Sharpe and deeper drawdown."),
        row(created_at, "stock_etf_research_lead", "rejected_high_drawdown_reference", "stock_etf", STOCK_ETF_REJECTED_HIGH_DRAWDOWN_REFERENCE, "lead_status", qqq_summary_value(qqq_summary, "rejected_high_drawdown_reference") or STOCK_ETF_REJECTED_HIGH_DRAWDOWN_REFERENCE, "qqq_150_rejected_high_drawdown", "review_qqq_trend_gate_as_new_stock_etf_research_lead", "Higher leverage reference is not a lead candidate because drawdown/financing sensitivity are too high."),
        row(created_at, "stock_etf_research_lead", "previous_lead", "stock_etf", PREVIOUS_STOCK_ETF_LEAD, "lead_status", "previous_stock_etf_research_lead", "superseded_by_qqq_100_trend_gate", "review_qqq_trend_gate_as_new_stock_etf_research_lead", "Previous Codex ambitious lead remains research context only."),
        row(created_at, "crypto_research_lead", "manual_review_lead", "crypto", CRYPTO_LEAD, "lead_status", crypto_status(crypto_inputs), CRYPTO_STATUS, "crypto_manual_review_next", crypto_evidence(crypto_inputs)),
        row(created_at, "stock_etf_blockers", "main_blocker", "stock_etf", STOCK_ETF_LEAD, "blocker", stock_blockers(stock_inputs), "research_only_no_execution_approval", "review_qqq_trend_gate_as_new_stock_etf_research_lead", "QQQ lead remains research-only; no preview, paper execution, leverage, margin, or order approval."),
        row(created_at, "crypto_blockers", "main_blockers", "crypto", CRYPTO_LEAD, "blockers", crypto_blockers(crypto_inputs), "manual_review_required", "crypto_cost_and_outlier_review_next", "Crypto blockers remain manual-review-only."),
        row(created_at, "rejected_or_downgraded_stock_etf_branches", "stock_branch_context", "stock_etf", STOCK_ETF_LEAD, "branch_context", stock_rejected_summary(stock_inputs), "manual_review_required", "stock_etf_monitoring_dashboard_next", "Previous stock/ETF variants remain research context, not execution routes."),
        row(created_at, "rejected_or_downgraded_crypto_branches", "crypto_branch_context", "crypto", CRYPTO_LEAD, "branch_context", crypto_rejected_summary(crypto_inputs), "manual_review_required", "crypto_manual_review_next", "Rejected crypto risk-control families should not be revived without a fixed hypothesis."),
        row(created_at, "execution_safety_state", "execution_boundary", "project", "project_research_state", "execution_approved", "false", "execution_not_approved", "project_dashboard_refresh_next", "Research leads are not preview candidates or order instructions."),
        row(created_at, "scheduling_safety_state", "scheduling_boundary", "project", "project_research_state", "scheduling_approved", "false", "scheduling_not_approved", "vps_monitoring_refresh_review", "This checkpoint does not create or approve scheduling."),
    ]
    for name, rows_for_input in {**stock_inputs, **crypto_inputs}.items():
        rows.append(
            row(
                created_at,
                "saved_input_status",
                name,
                "project",
                "saved_input",
                "saved_input_present",
                str(bool(rows_for_input)),
                "input_available" if rows_for_input else "missing_saved_input",
                "insufficient_saved_inputs" if not rows_for_input else DEFAULT_RECOMMENDATION,
                f"Saved input {input_path(name)} {'was found' if rows_for_input else 'was missing or empty'}.",
            )
        )
    return rows


def build_next_step_rows(
    created_at: str,
    stock_inputs: dict[str, list[dict[str, Any]]],
    crypto_inputs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    stock_missing = [name for name, rows_for_input in stock_inputs.items() if not rows_for_input]
    crypto_missing = [name for name, rows_for_input in crypto_inputs.items() if not rows_for_input]
    return [
        row(created_at, "suggested_next_research_options", "review_qqq_trend_gate_as_new_stock_etf_research_lead", "stock_etf", STOCK_ETF_LEAD, "next_step_option", "Review qqq_100_trend_gate as the new stock/ETF research lead in docs and dashboards without approving execution.", "open", "review_qqq_trend_gate_as_new_stock_etf_research_lead", stock_evidence(stock_inputs)),
        row(created_at, "suggested_next_research_options", "stock_etf_cost_review_next", "stock_etf", PREVIOUS_STOCK_ETF_LEAD, "next_step_option", "Keep the previous Codex ambitious cost-review context available, but do not treat it as the active lead.", "open", "stock_etf_cost_review_next", stock_blockers(stock_inputs)),
        row(created_at, "suggested_next_research_options", "stock_etf_monitoring_dashboard_next", "stock_etf", STOCK_ETF_LEAD, "next_step_option", "Improve stock/ETF monitoring dashboard/reporting for the active research lead.", "open", "stock_etf_monitoring_dashboard_next", stock_evidence(stock_inputs)),
        row(created_at, "suggested_next_research_options", "crypto_manual_review_next", "crypto", CRYPTO_LEAD, "next_step_option", "Manual crypto split/regime review before preview discussion.", "open", "crypto_manual_review_next", crypto_blockers(crypto_inputs)),
        row(created_at, "suggested_next_research_options", "crypto_cost_and_outlier_review_next", "crypto", CRYPTO_LEAD, "next_step_option", "Review crypto cost, outlier, BNB/TRX, exclusion-rule instability, and high drawdown.", "open", "crypto_cost_and_outlier_review_next", crypto_blockers(crypto_inputs)),
        row(created_at, "suggested_next_research_options", "project_dashboard_refresh_next", "project", "project_research_state", "next_step_option", "Refresh project dashboard/reporting once both branches have current saved outputs.", "open", "project_dashboard_refresh_next", "Useful when current state needs clearer display rather than another strategy variant."),
        row(created_at, "suggested_next_research_options", "pause_strategy_iterations_and_improve_reporting", "project", "project_research_state", "next_step_option", "Pause random strategy iterations and improve reporting/checkpoints around known leads.", "open", "pause_strategy_iterations_and_improve_reporting", "Both branches have research leads with blockers; more variants should not be automatic."),
        row(created_at, "suggested_next_research_options", "vps_monitoring_refresh_review", "project", "project_research_state", "next_step_option", "Review VPS monitoring/reporting refresh workflow without scheduling or execution approval.", "open", "vps_monitoring_refresh_review", "Monitoring/reporting can improve without trading approval."),
        row(created_at, "suggested_next_research_options", "insufficient_saved_inputs", "project", "project_research_state", "next_step_option", f"Missing saved inputs: stock={stock_missing or 'none'}; crypto={crypto_missing or 'none'}", "warning" if stock_missing or crypto_missing else "closed", "insufficient_saved_inputs", "Regenerate missing saved reports if their evidence is required."),
    ]


def choose_recommended_next_step(
    stock_inputs: dict[str, list[dict[str, Any]]],
    crypto_inputs: dict[str, list[dict[str, Any]]],
    next_step_rows: list[dict[str, Any]],
) -> str:
    if not any(stock_inputs.values()) and not any(crypto_inputs.values()):
        return "insufficient_saved_inputs"
    if qqq_summary_value(stock_inputs.get("qqq_lead_decision_summary", []), "final_lead_decision") == STOCK_ETF_STATUS:
        return "review_qqq_trend_gate_as_new_stock_etf_research_lead"
    stock_has_cost_blocker = "25 bps" in stock_blockers(stock_inputs) or "cost" in stock_status(stock_inputs).lower()
    crypto_has_manual_blockers = "not_ready" in crypto_status(crypto_inputs) or "outlier" in crypto_blockers(crypto_inputs)
    if stock_has_cost_blocker and crypto_has_manual_blockers:
        return "pause_strategy_iterations_and_improve_reporting"
    if stock_has_cost_blocker:
        return "stock_etf_cost_review_next"
    if crypto_has_manual_blockers:
        return "crypto_cost_and_outlier_review_next"
    return DEFAULT_RECOMMENDATION if next_step_rows else "project_dashboard_refresh_next"


def build_summary_rows(
    created_at: str,
    stock_inputs: dict[str, list[dict[str, Any]]],
    crypto_inputs: dict[str, list[dict[str, Any]]],
    refresh_rows: list[dict[str, Any]],
    next_step_rows: list[dict[str, Any]],
    recommended: str,
) -> list[dict[str, Any]]:
    return [
        summary_row(created_at, "stock_etf_active_research_lead", STOCK_ETF_LEAD, STOCK_ETF_STATUS, stock_evidence(stock_inputs), recommended),
        summary_row(created_at, "stock_etf_ambitious_alternative", STOCK_ETF_AMBITIOUS_ALTERNATIVE, "qqq_adaptive_higher_calmar_but_drawdown_tradeoff", stock_ambitious_alternative_evidence(stock_inputs), recommended),
        summary_row(created_at, "stock_etf_rejected_high_drawdown_reference", STOCK_ETF_REJECTED_HIGH_DRAWDOWN_REFERENCE, "qqq_150_rejected_high_drawdown", stock_rejected_high_drawdown_evidence(stock_inputs), recommended),
        summary_row(created_at, "stock_etf_previous_research_lead", PREVIOUS_STOCK_ETF_LEAD, "superseded_by_qqq_100_trend_gate", previous_stock_lead_evidence(stock_inputs), recommended),
        summary_row(created_at, "stock_etf_status_and_blocker", f"{stock_status(stock_inputs)}; blocker={stock_blockers(stock_inputs)}", STOCK_ETF_STATUS, "Stock/ETF lead is an active research lead with cost review open.", recommended),
        summary_row(created_at, "crypto_research_lead", CRYPTO_LEAD, CRYPTO_STATUS, crypto_evidence(crypto_inputs), recommended),
        summary_row(created_at, "crypto_status_and_blockers", f"{crypto_status(crypto_inputs)}; blockers={crypto_blockers(crypto_inputs)}", CRYPTO_STATUS, "Crypto lead remains manual-review-only and not preview-ready.", recommended),
        summary_row(created_at, "rejected_or_downgraded_families", f"stock_etf={stock_rejected_summary(stock_inputs)}; crypto={crypto_rejected_summary(crypto_inputs)}", "manual_review_required", "Rejected or downgraded branches remain research context.", recommended),
        summary_row(created_at, "recommended_next_step", recommended, recommended, "Recommendation chooses reporting/review direction, not execution.", recommended),
        summary_row(created_at, "execution_safety_state", "execution_approved=False; paper_execution_approved=False; crypto_execution_approved=False; preview_promotion_approved=False", "execution_not_approved", "No strategy is connected to execution.", recommended),
        summary_row(created_at, "scheduling_safety_state", "scheduling_approved=False", "scheduling_not_approved", "No scheduling is created or approved.", recommended),
        summary_row(created_at, "saved_input_coverage", status_counts(refresh_rows), "manual_review_required", "Saved input coverage is conservative.", recommended),
        summary_row(created_at, "next_step_options", status_counts(next_step_rows), "manual_review_required", "Next-step options are research/reporting options only.", recommended),
    ]


def stock_status(stock_inputs: dict[str, list[dict[str, Any]]]) -> str:
    qqq_status = qqq_summary_value(stock_inputs.get("qqq_lead_decision_summary", []), "final_lead_decision")
    if qqq_status:
        return qqq_status
    saved = summary_value(stock_inputs["codex_lead_summary"], "final_lead_decision_label")
    return saved if saved != "unavailable" else STOCK_ETF_STATUS


def stock_evidence(stock_inputs: dict[str, list[dict[str, Any]]]) -> str:
    qqq_summary = stock_inputs.get("qqq_lead_decision_summary", [])
    conservative = qqq_summary_details(qqq_summary, "conservative_qqq_candidate")
    tradeoff = qqq_summary_value(qqq_summary, "main_tradeoff")
    if conservative:
        return f"{conservative}; main_tradeoff={tradeoff}"
    saved = summary_value(stock_inputs["codex_lead_summary"], "full_period_evidence")
    if saved != "unavailable":
        return saved
    return "CAGR=14.1039; Sharpe=0.7192; MaxDD=-29.5357; Calmar=0.4775; Cash=9.9651; Turnover=19.0; beats_SPY=True; beats_stricter_gate=True; beats_original_crash_gate=True"


def stock_blockers(stock_inputs: dict[str, list[dict[str, Any]]]) -> str:
    qqq_summary = stock_inputs.get("qqq_lead_decision_summary", [])
    if qqq_summary_value(qqq_summary, "final_lead_decision") == STOCK_ETF_STATUS:
        return "research_only_no_execution_approval; adaptive_QQQ remains ambitious alternative; high leverage references rejected"
    saved = summary_value(stock_inputs["codex_lead_summary"], "remaining_blockers")
    if saved != "unavailable":
        return saved
    return "25 bps cost review not survived; survives_10_bps=True; survives_25_bps=False"


def stock_rejected_summary(stock_inputs: dict[str, list[dict[str, Any]]]) -> str:
    qqq_summary = stock_inputs.get("qqq_lead_decision_summary", [])
    rejected = qqq_summary_value(qqq_summary, "rejected_high_drawdown_reference")
    ambitious = qqq_summary_value(qqq_summary, "ambitious_qqq_candidate")
    if rejected or ambitious:
        return f"ambitious_alternative={ambitious or STOCK_ETF_AMBITIOUS_ALTERNATIVE}; rejected_high_drawdown_reference={rejected or STOCK_ETF_REJECTED_HIGH_DRAWDOWN_REFERENCE}; qqq_175_and_qqq_200_rejected_high_drawdown"
    persistence = summary_value(stock_inputs["stricter_persistence"], "final_summary_label")
    cost = summary_value(stock_inputs["stricter_cost_stress"], "final_summary_label")
    return f"previous stricter-gate branch superseded by {STOCK_ETF_LEAD}; persistence_context={persistence}; cost_context={cost}; rejected_or_downgraded_stock_etf_branches where available"


def stock_ambitious_alternative_evidence(stock_inputs: dict[str, list[dict[str, Any]]]) -> str:
    return qqq_summary_details(stock_inputs.get("qqq_lead_decision_summary", []), "ambitious_qqq_candidate") or "CAGR=20.2819; Sharpe=0.9749; MaxDD=-25.9889; Calmar=0.7804; higher Calmar but worse Sharpe/drawdown than qqq_100_trend_gate"


def stock_rejected_high_drawdown_evidence(stock_inputs: dict[str, list[dict[str, Any]]]) -> str:
    return qqq_summary_details(stock_inputs.get("qqq_lead_decision_summary", []), "rejected_high_drawdown_reference") or "CAGR=23.3903; Sharpe=0.9542; MaxDD=-33.892; Calmar=0.6901; rejected high-drawdown reference"


def previous_stock_lead_evidence(stock_inputs: dict[str, list[dict[str, Any]]]) -> str:
    saved = summary_value(stock_inputs["codex_lead_summary"], "full_period_evidence")
    if saved != "unavailable":
        return saved
    return "CAGR=14.1039; Sharpe=0.7192; MaxDD=-29.5357; Calmar=0.4775; previous active stock/ETF lead"


def crypto_status(crypto_inputs: dict[str, list[dict[str, Any]]]) -> str:
    saved = summary_value(crypto_inputs["crypto_manual_review"], "final_manual_review_status")
    return saved if saved != "unavailable" else CRYPTO_STATUS


def crypto_evidence(crypto_inputs: dict[str, list[dict[str, Any]]]) -> str:
    saved = summary_value(crypto_inputs["crypto_manual_review"], "lead_evidence_summary")
    if saved != "unavailable":
        return saved
    return "CAGR=54.0976; Sharpe=0.9574; Calmar=0.6975; MaxDD=-77.5564; manual-review-only"


def crypto_blockers(crypto_inputs: dict[str, list[dict[str, Any]]]) -> str:
    saved = summary_value(crypto_inputs["crypto_manual_review"], "blocker_counts")
    split = summary_value(crypto_inputs["crypto_split_summary"], "final_diagnosis_label")
    return f"fixed split sensitivity; exclusion-rule instability; BNB/TRX outlier dependence; cost review; high drawdown review; manual_review_blockers={saved}; split_diagnosis={split}"


def crypto_rejected_summary(crypto_inputs: dict[str, list[dict[str, Any]]]) -> str:
    crash = summary_value(crypto_inputs["crypto_crash_gate_summary"], "final_summary_label")
    vol = summary_value(crypto_inputs["crypto_volatility_summary"], "final_summary_label")
    return f"hard crash gates rejected for return drag; volatility/drawdown throttles downgraded because drawdown barely improved or return collapsed; crash_gate={crash}; volatility_scaling={vol}"


def summary_row(created_at: str, metric_name: str, metric_value: str, label: str, evidence: str, recommended: str) -> dict[str, Any]:
    return row(created_at, "summary", metric_name, "project", "project_research_state", metric_name, metric_value, label, recommended, evidence)


def row(
    created_at: str,
    section: str,
    check_name: str,
    branch: str,
    strategy_name: str,
    metric_name: str,
    metric_value: Any,
    status: str,
    summary_label: str,
    evidence: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "project_research_state_refresh",
        "section": section,
        "check_name": check_name,
        "branch": branch,
        "strategy_name": strategy_name,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "status": status,
        "summary_label": summary_label,
        "evidence": evidence,
        "recommended_next_step": summary_label,
        "research_only": True,
        "preview_promotion_approved": False,
        "preview_only": False,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "leverage_execution_approved": False,
        "margin_approved": False,
        "short_execution_approved": False,
        "scheduling_approved": False,
        "alpaca_called": False,
        "orders_created": False,
    }


def input_path(name: str) -> str:
    return str(STOCK_INPUT_FILES.get(name) or CRYPTO_INPUT_FILES.get(name) or name)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for item in rows:
        if item.get("strategy_name") == key or item.get("metric_name") == key or item.get("check_name") == key:
            return str(item.get("metric_value", "unavailable"))
    return "unavailable"


def qqq_summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for item in rows:
        if item.get("summary_name") == key:
            return str(item.get("summary_value", ""))
    return ""


def qqq_summary_details(rows: list[dict[str, Any]], key: str) -> str:
    for item in rows:
        if item.get("summary_name") == key:
            return str(item.get("details", ""))
    return ""


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(str(item.get("status", "")) for item in rows if item)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Project research state refresh complete. Research/report only; execution_approved=False; scheduling_approved=False.",
        f"Stock/ETF active research lead: {summary_value(summary_rows, 'stock_etf_active_research_lead')}",
        f"Stock/ETF ambitious alternative: {summary_value(summary_rows, 'stock_etf_ambitious_alternative')}",
        f"Stock/ETF rejected high-drawdown reference: {summary_value(summary_rows, 'stock_etf_rejected_high_drawdown_reference')}",
        f"Stock/ETF status and blocker: {summary_value(summary_rows, 'stock_etf_status_and_blocker')}",
        f"Crypto research lead: {summary_value(summary_rows, 'crypto_research_lead')}",
        f"Crypto status and blockers: {summary_value(summary_rows, 'crypto_status_and_blockers')}",
        f"Rejected/downgraded families: {summary_value(summary_rows, 'rejected_or_downgraded_families')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved refresh to {paths['refresh']}",
        f"Saved summary to {paths['summary']}",
        f"Saved next steps to {paths['next_steps']}",
        "Warning: this checkpoint does not approve preview promotion, paper execution, crypto execution, live trading, scheduling, or strategy-to-execution wiring.",
    ]


def read_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMMON_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for item in rows:
            writer.writerow(item)
