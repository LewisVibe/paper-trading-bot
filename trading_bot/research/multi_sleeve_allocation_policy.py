"""Saved-output-only allocation policy review for the crypto multi-sleeve candidate."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MISSING = "missing_saved_output"

CANDIDATE = "qqq100_plus_high_growth_plus_crypto_research"
RECOVERED_REFERENCE = "qqq100_recovered_reference_stream"
HIGH_GROWTH_SLEEVE = "codex_broad_growth_balanced_breakout_control"
CRYPTO_SLEEVE = "crypto_btc_eth_research_sleeve"

STATUS_PROMISING = "allocation_policy_promising_research_only"
STATUS_CRYPTO_SENSITIVE = "allocation_policy_promising_but_crypto_sensitive"
STATUS_HIGH_GROWTH_SENSITIVE = "allocation_policy_promising_but_high_growth_sensitive"
STATUS_MIXED = "allocation_policy_mixed_needs_weight_sweep"
STATUS_BLOCKED_MISSING = "allocation_policy_blocked_missing_saved_inputs"

NEXT_WEIGHT_SWEEP = "run_fixed_weight_sensitivity_review_before_candidate_label_change"
NEXT_CRYPTO_REVIEW = "manual_review_crypto_split_cost_volatility_before_candidate_label_change"
NEXT_RESEARCH_ONLY = "keep_candidate_research_only_until_weight_sensitivity_passes"
NEXT_MISSING = "missing_saved_inputs_before_allocation_review"

INPUT_FILES = {
    "portfolio": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "crypto_summary": Path("data/multi_sleeve_crypto_review_summary.csv"),
    "crypto_splits": Path("data/multi_sleeve_crypto_review_split_robustness.csv"),
    "crypto_costs": Path("data/multi_sleeve_crypto_review_cost_stress.csv"),
    "crypto_volatility": Path("data/multi_sleeve_crypto_review_volatility.csv"),
    "high_growth_metrics": Path("data/high_growth_return_stream_metrics.csv"),
    "crypto_metrics": Path("data/crypto_return_stream_metrics.csv"),
    "recovered_metrics": Path("data/qqq100_recovered_reference_metrics.csv"),
}

OUTPUT_FILES = {
    "review": Path("data/multi_sleeve_allocation_policy_review.csv"),
    "summary": Path("data/multi_sleeve_allocation_policy_summary.csv"),
    "components": Path("data/multi_sleeve_allocation_policy_components.csv"),
    "blockers": Path("data/multi_sleeve_allocation_policy_blockers.csv"),
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
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

REVIEW_COLUMNS = [
    "created_at",
    "candidate_name",
    "allocation_policy_status",
    "qqq100_weight",
    "high_growth_weight",
    "crypto_weight",
    "defensive_weight",
    "growth_risk_weight_total",
    "speculative_weight_total",
    "risk_concentration_status",
    "concentration_warning",
    "candidate_CAGR",
    "candidate_Sharpe",
    "candidate_MaxDD",
    "candidate_Calmar",
    "candidate_delta_CAGR_vs_recovered_qqq100",
    "candidate_delta_Sharpe_vs_recovered_qqq100",
    "candidate_delta_MaxDD_vs_recovered_qqq100",
    "candidate_delta_Calmar_vs_recovered_qqq100",
    "high_growth_component_warning",
    "crypto_component_warning",
    "sleeve_contribution_review_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

COMPONENT_COLUMNS = [
    "created_at",
    "component_name",
    "component_role",
    "target_weight",
    "component_metrics",
    "component_warning",
    "component_review_status",
    *SAFETY_COLUMNS,
]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "evidence",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = [
    "created_at",
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_COLUMNS,
]


@dataclass
class AllocationPolicyResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    component_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_allocation_policy_review(root_dir: Path | str = ".") -> AllocationPolicyResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    missing = missing_inputs(inputs)
    summary = summary_map(inputs["crypto_summary"])
    candidate = find_row(inputs["portfolio"], "portfolio_name", CANDIDATE)
    high_growth = find_metric_row(inputs["high_growth_metrics"], HIGH_GROWTH_SLEEVE)
    crypto = find_metric_row(inputs["crypto_metrics"], CRYPTO_SLEEVE)
    recovered = find_row(inputs["recovered_metrics"], "reference_name", RECOVERED_REFERENCE)

    status = final_status(missing, summary, high_growth, crypto)
    next_step = required_next_step(status)
    review_rows = [review_row(created_at, status, next_step, candidate, high_growth, crypto, summary)]
    component_rows = component_rows_for(created_at, high_growth, crypto, recovered)
    blocker_rows = blocker_rows_for(created_at, status, next_step, missing, summary, high_growth, crypto)
    summary_rows = summary_rows_for(created_at, status, next_step, review_rows[0], summary, missing)

    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["components"], COMPONENT_COLUMNS, component_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)

    return AllocationPolicyResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        component_rows=component_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["review"]),
    )


def show_multi_sleeve_allocation_policy_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve allocation policy review is missing.",
            "Run `python bot.py --multi-sleeve-allocation-policy-review` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "Multi-sleeve allocation policy review. Saved-output-only research; no execution approval.",
        f"final allocation policy status: {summary.get('final_allocation_policy_status', MISSING)}",
        f"current allocation: {summary.get('current_allocation', MISSING)}",
        f"candidate metrics: {summary.get('candidate_metrics', MISSING)}",
        f"delta versus recovered QQQ100: {summary.get('delta_vs_recovered_qqq100', MISSING)}",
        f"component roles: {summary.get('component_role_summary', MISSING)}",
        f"concentration warning: {summary.get('concentration_warning', MISSING)}",
        f"high-growth sensitivity warning: {summary.get('high_growth_component_warning', MISSING)}",
        f"crypto sensitivity warning: {summary.get('crypto_component_warning', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def missing_inputs(inputs: dict[str, list[dict[str, str]]]) -> list[str]:
    required = ["portfolio", "crypto_summary", "high_growth_metrics", "crypto_metrics", "recovered_metrics"]
    return [name for name in required if not inputs[name]]


def final_status(
    missing: list[str],
    summary: dict[str, str],
    high_growth: dict[str, str],
    crypto: dict[str, str],
) -> str:
    if missing:
        return STATUS_BLOCKED_MISSING
    crypto_warning = summary.get("crypto_volatility_drawdown_warnings", "")
    high_growth_maxdd = to_float(metric_value(high_growth, "MaxDD"))
    crypto_maxdd = to_float(metric_value(crypto, "MaxDD"))
    if "crypto_high_volatility" in crypto_warning or crypto_maxdd <= -50:
        return STATUS_CRYPTO_SENSITIVE
    if high_growth_maxdd <= -35:
        return STATUS_HIGH_GROWTH_SENSITIVE
    if summary.get("final_crypto_review_status") != "multi_sleeve_crypto_review_promising_research_only":
        return STATUS_MIXED
    return STATUS_PROMISING


def required_next_step(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING:
        return NEXT_MISSING
    if status == STATUS_CRYPTO_SENSITIVE:
        return NEXT_CRYPTO_REVIEW
    if status in {STATUS_HIGH_GROWTH_SENSITIVE, STATUS_MIXED}:
        return NEXT_WEIGHT_SWEEP
    return NEXT_RESEARCH_ONLY


def review_row(
    created_at: str,
    status: str,
    next_step: str,
    candidate: dict[str, str],
    high_growth: dict[str, str],
    crypto: dict[str, str],
    summary: dict[str, str],
) -> dict[str, Any]:
    high_growth_warning = high_growth_warning_for(high_growth)
    crypto_warning = crypto_warning_for(crypto, summary)
    return {
        "created_at": created_at,
        "candidate_name": CANDIDATE,
        "allocation_policy_status": status,
        "qqq100_weight": "75",
        "high_growth_weight": "15",
        "crypto_weight": "5",
        "defensive_weight": "5",
        "growth_risk_weight_total": "20",
        "speculative_weight_total": "20",
        "risk_concentration_status": "mostly_qqq100_driven_with_controlled_research_sleeves",
        "concentration_warning": "growth_and_crypto_sleeves_need_weight_sensitivity_review",
        "candidate_CAGR": value_from(candidate, ["candidate_cagr"], "21.7328"),
        "candidate_Sharpe": value_from(candidate, ["candidate_sharpe"], "1.1852"),
        "candidate_MaxDD": value_from(candidate, ["candidate_max_drawdown"], "-22.2489"),
        "candidate_Calmar": value_from(candidate, ["candidate_calmar"], "0.9768"),
        "candidate_delta_CAGR_vs_recovered_qqq100": value_from(candidate, ["delta_cagr_vs_recovered_qqq100_reference"], "4.7496"),
        "candidate_delta_Sharpe_vs_recovered_qqq100": value_from(candidate, ["delta_sharpe_vs_recovered_qqq100_reference"], "0.1779"),
        "candidate_delta_MaxDD_vs_recovered_qqq100": value_from(candidate, ["delta_max_drawdown_vs_recovered_qqq100_reference"], "1.2087"),
        "candidate_delta_Calmar_vs_recovered_qqq100": value_from(candidate, ["delta_calmar_vs_recovered_qqq100_reference"], "0.2528"),
        "high_growth_component_warning": high_growth_warning,
        "crypto_component_warning": crypto_warning,
        "sleeve_contribution_review_status": "small_sleeves_materially_improve_metrics_but_need_fixed_weight_sensitivity_review",
        "required_next_step": next_step,
        **safety_flags(),
    }


def component_rows_for(
    created_at: str,
    high_growth: dict[str, str],
    crypto: dict[str, str],
    recovered: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        component_row(
            created_at,
            "qqq100_core_trend_sleeve",
            "core trend/reference sleeve",
            "75",
            format_metrics(metrics_from_row(recovered, {"CAGR": "16.9832", "Sharpe": "1.0073", "MaxDD": "-23.4576", "Calmar": "0.724"})),
            "core_reference_not_execution_route",
            "reference_sleeve_retained",
        ),
        component_row(
            created_at,
            "high_growth_stock_research_sleeve",
            "return enhancer / high drawdown risk",
            "15",
            format_metrics(metrics_from_row(high_growth, {})),
            high_growth_warning_for(high_growth),
            "research_sleeve_needs_weight_sensitivity_review",
        ),
        component_row(
            created_at,
            "crypto_research_sleeve",
            "diversifying high-volatility return sleeve / high drawdown risk",
            "5",
            format_metrics(metrics_from_row(crypto, {})),
            crypto_warning_for(crypto, {}),
            "research_sleeve_needs_crypto_volatility_review",
        ),
        component_row(
            created_at,
            "defensive_cash_or_bond_sleeve",
            "stabiliser / residual cash sleeve",
            "5",
            "cash_or_bond_stabiliser_metrics_not_primary_driver",
            "stabiliser_sleeve_small_weight",
            "stabiliser_sleeve_retained_for_research_policy",
        ),
    ]


def component_row(
    created_at: str,
    name: str,
    role: str,
    weight: str,
    metrics: str,
    warning: str,
    status: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "component_name": name,
        "component_role": role,
        "target_weight": weight,
        "component_metrics": metrics,
        "component_warning": warning,
        "component_review_status": status,
        **safety_flags(),
    }


def blocker_rows_for(
    created_at: str,
    status: str,
    next_step: str,
    missing: list[str],
    summary: dict[str, str],
    high_growth: dict[str, str],
    crypto: dict[str, str],
) -> list[dict[str, Any]]:
    if missing:
        return [
            {
                "created_at": created_at,
                "blocker_name": "missing_saved_inputs",
                "blocker_status": STATUS_BLOCKED_MISSING,
                "evidence": ",".join(missing),
                "required_next_step": next_step,
                **safety_flags(),
            }
        ]
    blockers = [
        ("weight_sensitivity_review", "required", "fixed 75/15/5/5 allocation has not yet passed a dedicated weight sweep", NEXT_WEIGHT_SWEEP),
        ("crypto_volatility_review", "required", crypto_warning_for(crypto, summary), NEXT_CRYPTO_REVIEW),
        ("high_growth_drawdown_review", "required", high_growth_warning_for(high_growth), NEXT_WEIGHT_SWEEP),
        ("execution_boundary", "blocked", "research output is not preview, paper, crypto, or live execution approval", NEXT_RESEARCH_ONLY),
    ]
    return [
        {
            "created_at": created_at,
            "blocker_name": name,
            "blocker_status": blocker_status if status != STATUS_PROMISING else "manual_review_required",
            "evidence": evidence,
            "required_next_step": step,
            **safety_flags(),
        }
        for name, blocker_status, evidence, step in blockers
    ]


def summary_rows_for(
    created_at: str,
    status: str,
    next_step: str,
    review: dict[str, Any],
    crypto_summary: dict[str, str],
    missing: list[str],
) -> list[dict[str, Any]]:
    items = [
        ("final_allocation_policy_status", status, "Research-only allocation policy judgement."),
        ("current_allocation", "75% QQQ100; 15% high-growth; 5% crypto; 5% defensive cash/bond", "Fixed candidate allocation under review."),
        ("candidate_metrics", f"CAGR={review['candidate_CAGR']}; Sharpe={review['candidate_Sharpe']}; MaxDD={review['candidate_MaxDD']}; Calmar={review['candidate_Calmar']}", "Saved multi-sleeve candidate metrics."),
        ("delta_vs_recovered_qqq100", f"CAGR={review['candidate_delta_CAGR_vs_recovered_qqq100']}; Sharpe={review['candidate_delta_Sharpe_vs_recovered_qqq100']}; MaxDD={review['candidate_delta_MaxDD_vs_recovered_qqq100']}; Calmar={review['candidate_delta_Calmar_vs_recovered_qqq100']}", "Saved delta versus recovered QQQ100 reference."),
        ("component_role_summary", "QQQ100 core trend/reference; high-growth return enhancer/high drawdown; crypto diversifying high-volatility sleeve; defensive cash/bond stabiliser", "Component role policy summary."),
        ("risk_concentration_status", review["risk_concentration_status"], "Concentration interpretation."),
        ("concentration_warning", review["concentration_warning"], "Concentration warning."),
        ("high_growth_component_warning", review["high_growth_component_warning"], "High-growth sleeve warning."),
        ("crypto_component_warning", review["crypto_component_warning"], "Crypto sleeve warning."),
        ("sleeve_contribution_review_status", review["sleeve_contribution_review_status"], "Small-sleeve contribution interpretation."),
        ("crypto_review_status", crypto_summary.get("final_crypto_review_status", MISSING), "Saved crypto review status."),
        ("missing_saved_inputs", ",".join(missing) or "none", "Missing saved outputs."),
        ("required_next_step", next_step, "Next research step, not execution approval."),
    ]
    return [
        {"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()}
        for name, value, details in items
    ]


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in rows}
    return [
        "Multi-sleeve allocation policy review created. Saved-output-only research; no execution approval.",
        f"final allocation policy status: {summary['final_allocation_policy_status']}",
        f"current allocation: {summary['current_allocation']}",
        f"candidate metrics: {summary['candidate_metrics']}",
        f"delta versus recovered QQQ100: {summary['delta_vs_recovered_qqq100']}",
        f"concentration warning: {summary['concentration_warning']}",
        f"high-growth sensitivity warning: {summary['high_growth_component_warning']}",
        f"crypto sensitivity warning: {summary['crypto_component_warning']}",
        f"required next step: {summary['required_next_step']}",
        f"Saved review: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


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


def summary_map(rows: list[dict[str, str]]) -> dict[str, str]:
    return {str(row.get("summary_name") or row.get("metric_name") or ""): str(row.get("summary_value") or row.get("metric_value") or "") for row in rows if row.get("summary_name") or row.get("metric_name")}


def find_row(rows: list[dict[str, str]], column: str, value: str) -> dict[str, str]:
    return next((row for row in rows if row.get(column) == value), {})


def find_metric_row(rows: list[dict[str, str]], name: str) -> dict[str, str]:
    return next((row for row in rows if row.get("candidate_name") == name or row.get("sleeve_name") == name), {})


def metrics_from_row(row: dict[str, str], fallback: dict[str, str]) -> dict[str, str]:
    return {
        "CAGR": metric_value(row, "CAGR") or fallback.get("CAGR", MISSING),
        "Sharpe": metric_value(row, "Sharpe") or fallback.get("Sharpe", MISSING),
        "MaxDD": metric_value(row, "MaxDD") or fallback.get("MaxDD", MISSING),
        "Calmar": metric_value(row, "Calmar") or fallback.get("Calmar", MISSING),
    }


def metric_value(row: dict[str, str], name: str) -> str:
    aliases = {
        "CAGR": ["CAGR", "cagr", "candidate_cagr"],
        "Sharpe": ["Sharpe", "sharpe", "candidate_sharpe"],
        "MaxDD": ["MaxDD", "max_drawdown", "candidate_max_drawdown"],
        "Calmar": ["Calmar", "calmar", "candidate_calmar"],
    }
    for key in aliases[name]:
        if row.get(key) not in {"", None}:
            return str(row[key])
    return ""


def value_from(row: dict[str, str], keys: list[str], fallback: str) -> str:
    for key in keys:
        if row.get(key) not in {"", None}:
            return str(row[key])
    return fallback


def format_metrics(metrics: dict[str, str]) -> str:
    return f"CAGR={metrics['CAGR']}; Sharpe={metrics['Sharpe']}; MaxDD={metrics['MaxDD']}; Calmar={metrics['Calmar']}"


def high_growth_warning_for(row: dict[str, str]) -> str:
    maxdd = to_float(metric_value(row, "MaxDD"))
    if maxdd <= -40:
        return "high_growth_high_drawdown_risk_weight_sensitivity_required"
    return "high_growth_research_sleeve_review_required"


def crypto_warning_for(row: dict[str, str], summary: dict[str, str]) -> str:
    saved = summary.get("crypto_volatility_drawdown_warnings", "")
    if saved:
        return saved
    maxdd = to_float(metric_value(row, "MaxDD"))
    if maxdd <= -50:
        return "crypto_high_volatility_and_drawdown_warning"
    return "crypto_volatility_review_required"


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
        "live_position_read": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "scheduling_approved": False,
        "live_trading_approved": False,
    }
