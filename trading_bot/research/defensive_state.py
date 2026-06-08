"""Saved-data-only defensive research state checkpoint report."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFENSIVE_RESEARCH_STATE_COLUMNS = [
    "created_at",
    "component",
    "category",
    "state_label",
    "evidence_source",
    "headline_metric",
    "headline_value",
    "comparison_context",
    "interpretation",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class DefensiveResearchStateResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_defensive_research_state_report(
    data_dir: Path | str = "data",
    created_at: str | None = None,
) -> DefensiveResearchStateResult:
    data_path = Path(data_dir)
    created = created_at or datetime.now(timezone.utc).isoformat()
    inputs = read_defensive_state_inputs(data_path)
    rows = build_defensive_state_rows(created, inputs)
    output_path = data_path / "defensive_research_state_report.csv"
    write_rows(output_path, rows)
    return DefensiveResearchStateResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_summary(rows, output_path),
    )


def read_defensive_state_inputs(data_path: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "defensive_candidate_comparison": read_csv_rows(data_path / "defensive_candidate_comparison.csv"),
        "defensive_strategy_report": read_csv_rows(data_path / "defensive_strategy_report.csv"),
        "etf_breadth_decision": read_csv_rows(data_path / "etf_breadth_regime_decision_report.csv"),
        "etf_breadth_robustness": read_csv_rows(data_path / "etf_breadth_regime_robustness_report.csv"),
        "short_hedge": read_csv_rows(data_path / "short_hedge_backtest_results.csv"),
        "short_strategy_lab": read_csv_rows(data_path / "short_strategy_lab_results.csv"),
        "execution_eligibility": read_csv_rows(data_path / "execution_eligibility_report.csv"),
        "promoted_decision": read_csv_rows(data_path / "promoted_decision_preview.csv"),
        "portfolio_risk_policy": read_csv_rows(data_path / "portfolio_risk_policy_report.csv"),
    }


def build_defensive_state_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    comparison = inputs["defensive_candidate_comparison"]
    breadth_decision = inputs["etf_breadth_decision"]
    breadth_robustness = inputs["etf_breadth_robustness"]
    return [
        monthly_etf_row(created_at, comparison),
        vol_managed_row(created_at, comparison),
        adaptive_row(created_at, comparison),
        breadth_row(created_at, breadth_decision, breadth_robustness),
        short_research_row(created_at, inputs["short_hedge"], inputs["short_strategy_lab"]),
        execution_state_row(
            created_at,
            inputs["execution_eligibility"],
            inputs["promoted_decision"],
            inputs["portfolio_risk_policy"],
        ),
    ]


def monthly_etf_row(created_at: str, comparison_rows: list[dict[str, str]]) -> dict[str, Any]:
    row = strategy_row(comparison_rows, "monthly_etf_momentum_rotation")
    if not row:
        return missing_component_row(
            created_at,
            "monthly_etf_momentum_rotation",
            "defensive_candidate",
            "missing_input",
            "data/defensive_candidate_comparison.csv",
            "Run python bot.py --defensive-candidate-comparison.",
        )
    return state_row(
        created_at,
        "monthly_etf_momentum_rotation",
        "defensive_candidate",
        row.get("comparison_status") or "preferred_defensive_candidate",
        "data/defensive_candidate_comparison.csv",
        "policy_rank",
        row.get("policy_rank", ""),
        "Preferred defensive candidate unless saved comparison policy changes.",
        row.get("comparison_reason", "") or "Monthly ETF rotation remains the preferred defensive candidate.",
        row.get("next_research_step", "") or "Keep research-only; continue comparing new defensive ideas against this baseline.",
    )


def vol_managed_row(created_at: str, comparison_rows: list[dict[str, str]]) -> dict[str, Any]:
    row = strategy_row(comparison_rows, "volatility_managed_dual_momentum_etf")
    if not row:
        return missing_component_row(
            created_at,
            "volatility_managed_dual_momentum_etf",
            "defensive_candidate",
            "missing_input",
            "data/defensive_candidate_comparison.csv",
            "Run python bot.py --defensive-candidate-comparison.",
        )
    return state_row(
        created_at,
        "volatility_managed_dual_momentum_etf",
        "defensive_candidate",
        row.get("comparison_status") or "promising_but_split_sensitive",
        "data/defensive_candidate_comparison.csv",
        "fixed_split_win_count",
        row.get("fixed_split_win_count", ""),
        row.get("split_comparison_summary", "") or "Compare fixed splits versus monthly ETF rotation.",
        row.get("comparison_reason", "") or "Vol-managed ETF remains promising but split-sensitive.",
        row.get("next_research_step", "") or "Keep research-only; require stronger split consistency before promotion discussion.",
    )


def adaptive_row(created_at: str, comparison_rows: list[dict[str, str]]) -> dict[str, Any]:
    row = strategy_row(comparison_rows, "adaptive_risk_on_off_momentum")
    if not row:
        return missing_component_row(
            created_at,
            "adaptive_risk_on_off_momentum",
            "defensive_candidate",
            "missing_input",
            "data/defensive_candidate_comparison.csv",
            "Run python bot.py --defensive-candidate-comparison.",
        )
    status = row.get("comparison_status") or "secondary_complex_candidate"
    if status == "secondary_defensive_candidate":
        status = "secondary_complex_candidate"
    return state_row(
        created_at,
        "adaptive_risk_on_off_momentum",
        "defensive_candidate",
        status,
        "data/defensive_candidate_comparison.csv",
        "trade_count",
        row.get("trade_count", ""),
        row.get("relative_turnover_note", "") or "Adaptive is assessed against simpler defensive candidates.",
        row.get("comparison_reason", "") or "Adaptive remains secondary because complexity/turnover burden is higher.",
        row.get("next_research_step", "") or "Keep research-only; compare turnover and cost burden before reconsidering.",
    )


def breadth_row(
    created_at: str,
    decision_rows: list[dict[str, str]],
    robustness_rows: list[dict[str, str]],
) -> dict[str, Any]:
    decision = first_row(decision_rows)
    robustness = first_row(robustness_rows)
    if not decision and not robustness:
        return missing_component_row(
            created_at,
            "etf_breadth_regime_allocation",
            "diagnostic_filter",
            "missing_input",
            "data/etf_breadth_regime_decision_report.csv; data/etf_breadth_regime_robustness_report.csv",
            "Run python bot.py --etf-breadth-regime-decision-report and python bot.py --etf-breadth-regime-robustness.",
        )
    robustness_label = robustness.get("robustness_label", "") if robustness else ""
    decision_label = decision.get("decision_label", "") if decision else ""
    state_label = "robust_diagnostic_candidate_not_strategy" if robustness_label == "robust_diagnostic_candidate" else (decision_label or robustness_label or "useful_diagnostic_not_strategy")
    return state_row(
        created_at,
        "etf_breadth_regime_allocation",
        "diagnostic_filter",
        state_label,
        "data/etf_breadth_regime_decision_report.csv; data/etf_breadth_regime_robustness_report.csv",
        "robustness_label",
        robustness_label or "not_available",
        "Breadth regime is assessed as a market-state diagnostic/filter, not as a promoted allocation strategy.",
        (decision.get("finding", "") if decision else "") or (robustness.get("finding", "") if robustness else "") or "ETF breadth regime remains diagnostic-only.",
        breadth_next_step(decision, robustness, robustness_label),
    )


def breadth_next_step(
    decision: dict[str, str] | None,
    robustness: dict[str, str] | None,
    robustness_label: str,
) -> str:
    if robustness_label == "robust_diagnostic_candidate":
        return "Use breadth as a diagnostic/filter idea; compare against ETF rotation and vol-managed ETF before any strategy discussion."
    return (decision.get("required_next_step", "") if decision else "") or (robustness.get("required_next_step", "") if robustness else "") or "Keep research-only; do not promote automatically."


def short_research_row(
    created_at: str,
    short_hedge_rows: list[dict[str, str]],
    short_strategy_rows: list[dict[str, str]],
) -> dict[str, Any]:
    hedge = first_strategy_like_row(short_hedge_rows, "research_spy_short_hedge")
    lab = first_strategy_like_row(short_strategy_rows, "research_weak_etf_short_momentum")
    if not hedge and not lab:
        return missing_component_row(
            created_at,
            "short_research",
            "paused_research",
            "missing_input",
            "data/short_hedge_backtest_results.csv; data/short_strategy_lab_results.csv",
            "Run short research reports only if intentionally reviewing paused short research.",
        )
    conclusion = first_non_empty(
        [hedge.get("research_conclusion", "") if hedge else "", lab.get("research_conclusion", "") if lab else ""]
    )
    status = first_non_empty(
        [hedge.get("research_status", "") if hedge else "", lab.get("research_status", "") if lab else ""]
    )
    return state_row(
        created_at,
        "short_research",
        "paused_research",
        "paused_not_useful" if status in {"not_useful", "pause"} or conclusion else "paused_not_useful",
        "data/short_hedge_backtest_results.csv; data/short_strategy_lab_results.csv",
        "research_status",
        status or "not_useful",
        "Short research remains paused and is not part of execution readiness.",
        conclusion or "Short hedge and weak ETF short momentum research remain not useful/paused.",
        "Do not add short preview or execution; only revisit with a new fixed hypothesis and borrow constraints.",
    )


def execution_state_row(
    created_at: str,
    eligibility_rows: list[dict[str, str]],
    promoted_rows: list[dict[str, str]],
    policy_rows: list[dict[str, str]],
) -> dict[str, Any]:
    final = find_by_key(eligibility_rows, "eligibility_check_name", "final_execution_eligibility")
    blockers = [
        row.get("ticker", "")
        for row in promoted_rows
        if row.get("decision_state") == "blocked_strategy_disagreement" and row.get("ticker")
    ]
    policy_blockers = [
        row.get("risk_policy_name", "")
        for row in policy_rows
        if row.get("risk_policy_status") == "blocked_for_review" and row.get("risk_policy_name")
    ]
    if not final and not promoted_rows and not policy_rows:
        return missing_component_row(
            created_at,
            "execution_state",
            "execution_boundary",
            "missing_input",
            "data/execution_eligibility_report.csv; data/promoted_decision_preview.csv; data/portfolio_risk_policy_report.csv",
            "Run python bot.py --execution-eligibility-report and related saved review reports.",
        )
    context_parts = []
    if blockers:
        context_parts.append("strategy disagreement: " + ", ".join(sorted(blockers)))
    if policy_blockers:
        context_parts.append("risk policy blockers: " + ", ".join(sorted(policy_blockers)))
    return state_row(
        created_at,
        "execution_state",
        "execution_boundary",
        "blocked_no_execution_approval",
        "data/execution_eligibility_report.csv; data/promoted_decision_preview.csv; data/portfolio_risk_policy_report.csv",
        "eligibility_status",
        final.get("eligibility_status", "blocked_for_review") if final else "blocked_for_review",
        "; ".join(context_parts) if context_parts else "Execution approval remains false in saved reports.",
        "Execution remains blocked/no approval.",
        "Resolve preview, consensus, risk policy, kill-switch, and explicit confirmation requirements before any execution discussion.",
    )


def state_row(
    created_at: str,
    component: str,
    category: str,
    state_label: str,
    evidence_source: str,
    headline_metric: str,
    headline_value: Any,
    comparison_context: str,
    interpretation: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "component": component,
        "category": category,
        "state_label": state_label,
        "evidence_source": evidence_source,
        "headline_metric": headline_metric,
        "headline_value": headline_value,
        "comparison_context": comparison_context,
        "interpretation": interpretation,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def missing_component_row(
    created_at: str,
    component: str,
    category: str,
    state_label: str,
    evidence_source: str,
    required_next_step: str,
) -> dict[str, Any]:
    return state_row(
        created_at,
        component,
        category,
        state_label,
        evidence_source,
        "input_status",
        "missing",
        "Saved evidence was unavailable.",
        "This component could not be fully summarized from saved CSVs.",
        required_next_step,
    )


def strategy_row(rows: list[dict[str, str]], strategy_name: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("strategy_name") == strategy_name:
            return row
    return None


def first_strategy_like_row(rows: list[dict[str, str]], strategy_name: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("strategy_name") == strategy_name:
            return row
    return rows[0] if rows else None


def first_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    return rows[0] if rows else None


def find_by_key(rows: list[dict[str, str]], key: str, expected: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == expected:
            return row
    return None


def first_non_empty(values: list[str]) -> str:
    for value in values:
        if value:
            return value
    return ""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEFENSIVE_RESEARCH_STATE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEFENSIVE_RESEARCH_STATE_COLUMNS})


def build_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    labels = ", ".join(f"{row['component']}={row['state_label']}" for row in rows)
    return [
        "DEFENSIVE RESEARCH STATE REPORT. SAVED-DATA ONLY. NOT EXECUTION.",
        "State labels: " + labels,
        f"Saved defensive research state report to {output_path}",
        "No strategy was promoted.",
        "No orders were created, submitted, or cancelled.",
        "No execution approval was granted.",
    ]
