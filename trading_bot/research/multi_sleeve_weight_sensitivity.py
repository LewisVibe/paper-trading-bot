"""Saved-output-only fixed weight-sensitivity review for multi-sleeve research."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import multi_sleeve_portfolio_backtest as backtest


MISSING = "missing_saved_output"

RECOVERED_REFERENCE = backtest.RECOVERED_QQQ100_REFERENCE
HIGH_GROWTH_SLEEVE = "codex_broad_growth_balanced_breakout_control"
CRYPTO_SLEEVE = "crypto_btc_eth_research_sleeve"
CURRENT_ALLOCATION = "current_75_15_5_5"

STATUS_CURRENT_PROMISING = "weight_sensitivity_current_allocation_promising"
STATUS_CURRENT_MIXED = "weight_sensitivity_current_allocation_mixed"
STATUS_CRYPTO_RETURN_VOL = "weight_sensitivity_crypto_adds_return_but_vol_sensitive"
STATUS_HIGH_GROWTH_RETURN_DD = "weight_sensitivity_high_growth_drives_return_and_drawdown"
STATUS_NEEDS_REVIEW = "weight_sensitivity_needs_manual_review"
STATUS_BLOCKED_MISSING = "weight_sensitivity_blocked_missing_saved_streams"

NEXT_WEIGHT_REVIEW = "run_fixed_weight_sensitivity_review_before_candidate_label_change"
NEXT_CRYPTO_REVIEW = "manual_review_crypto_split_cost_volatility_before_candidate_label_change"
NEXT_RESEARCH_ONLY = "keep_candidate_research_only_until_weight_sensitivity_passes"
NEXT_MISSING = "missing_saved_streams_before_weight_sensitivity_review"

INPUT_FILES = {
    "qqq100_recovered_reference_stream": Path("data/qqq100_recovered_reference_stream.csv"),
    "high_growth_return_streams": Path("data/high_growth_return_streams.csv"),
    "crypto_return_streams": Path("data/crypto_return_streams.csv"),
    "multi_sleeve_portfolio_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "allocation_policy_summary": Path("data/multi_sleeve_allocation_policy_summary.csv"),
    "crypto_review_summary": Path("data/multi_sleeve_crypto_review_summary.csv"),
}

OUTPUT_FILES = {
    "review": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "summary": Path("data/multi_sleeve_weight_sensitivity_summary.csv"),
    "blockers": Path("data/multi_sleeve_weight_sensitivity_blockers.csv"),
}

ALLOCATIONS = [
    ("current_75_15_5_5", 75, 15, 5, 5),
    ("lower_crypto_77_15_3_5", 77, 15, 3, 5),
    ("no_crypto_80_15_0_5", 80, 15, 0, 5),
    ("lower_growth_80_10_5_5", 80, 10, 5, 5),
    ("balanced_lower_risk_85_10_0_5", 85, 10, 0, 5),
    ("higher_crypto_73_15_7_5", 73, 15, 7, 5),
    ("higher_growth_70_20_5_5", 70, 20, 5, 5),
]

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
    "qqq100_weight",
    "high_growth_weight",
    "crypto_weight",
    "defensive_weight",
    "weight_sum",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "delta_CAGR_vs_recovered_qqq100",
    "delta_Sharpe_vs_recovered_qqq100",
    "delta_MaxDD_vs_recovered_qqq100",
    "delta_Calmar_vs_recovered_qqq100",
    "delta_CAGR_vs_current_75_15_5_5",
    "delta_Sharpe_vs_current_75_15_5_5",
    "delta_MaxDD_vs_current_75_15_5_5",
    "delta_Calmar_vs_current_75_15_5_5",
    "risk_status",
    "allocation_policy_status",
    "warning_status",
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

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "evidence",
    "required_next_step",
    *SAFETY_COLUMNS,
]


@dataclass
class WeightSensitivityResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_weight_sensitivity(root_dir: Path | str = ".") -> WeightSensitivityResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    streams = (
        backtest.normalize_recovered_reference_stream_rows(inputs["qqq100_recovered_reference_stream"])
        + backtest.normalize_high_growth_stream_rows(inputs["high_growth_return_streams"])
        + backtest.normalize_crypto_stream_rows(inputs["crypto_return_streams"])
    )
    by_candidate = backtest.stream_returns_by_candidate(streams)
    missing = missing_streams(by_candidate)
    if missing:
        review_rows = blocked_review_rows(created_at, missing)
        final_status = STATUS_BLOCKED_MISSING
    else:
        review_rows = build_review_rows(created_at, by_candidate, inputs)
        final_status = final_review_status(review_rows)
    summary_rows = build_summary_rows(created_at, final_status, review_rows, missing, inputs)
    blocker_rows = build_blocker_rows(created_at, final_status, review_rows, missing)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return WeightSensitivityResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["review"]),
    )


def show_multi_sleeve_weight_sensitivity(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve weight sensitivity is missing.",
            "Run `python bot.py --multi-sleeve-weight-sensitivity` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "Multi-sleeve weight sensitivity. Saved-output-only research; no execution approval.",
        f"final weight-sensitivity status: {summary.get('final_weight_sensitivity_status', MISSING)}",
        f"fixed allocations tested: {summary.get('fixed_allocations_tested', MISSING)}",
        f"current allocation metrics: {summary.get('current_allocation_metrics', MISSING)}",
        f"best Calmar allocation: {summary.get('best_calmar_allocation', MISSING)}",
        f"best Sharpe allocation: {summary.get('best_sharpe_allocation', MISSING)}",
        f"lowest MaxDD allocation: {summary.get('lowest_maxdd_allocation', MISSING)}",
        f"no-crypto result: {summary.get('no_crypto_result', MISSING)}",
        f"higher-crypto interpretation: {summary.get('higher_crypto_interpretation', MISSING)}",
        f"higher-growth interpretation: {summary.get('higher_growth_interpretation', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def missing_streams(by_candidate: dict[str, dict[str, float]]) -> list[str]:
    required = [RECOVERED_REFERENCE, HIGH_GROWTH_SLEEVE, CRYPTO_SLEEVE]
    return [candidate for candidate in required if candidate not in by_candidate]


def build_review_rows(
    created_at: str,
    by_candidate: dict[str, dict[str, float]],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    common_dates = sorted(
        set(by_candidate[RECOVERED_REFERENCE])
        & set(by_candidate[HIGH_GROWTH_SLEEVE])
        & set(by_candidate[CRYPTO_SLEEVE])
    )
    reference_returns = returns_for_dates(common_dates, by_candidate[RECOVERED_REFERENCE])
    reference_metrics = backtest.metrics_for_returns(reference_returns)
    baseline_returns = allocation_returns(common_dates, by_candidate, ALLOCATIONS[0])
    baseline_metrics = backtest.metrics_for_returns(baseline_returns)
    allocation_policy_status = summary_map(inputs["allocation_policy_summary"]).get(
        "final_allocation_policy_status",
        "allocation_policy_promising_but_crypto_sensitive",
    )
    rows = []
    for allocation in ALLOCATIONS:
        name, qqq_weight, high_growth_weight, crypto_weight, defensive_weight = allocation
        returns = allocation_returns(common_dates, by_candidate, allocation)
        metrics = backtest.metrics_for_returns(returns)
        warning = warning_status(name, high_growth_weight, crypto_weight, metrics, baseline_metrics)
        rows.append(
            {
                "created_at": created_at,
                "candidate_name": name,
                "qqq100_weight": qqq_weight,
                "high_growth_weight": high_growth_weight,
                "crypto_weight": crypto_weight,
                "defensive_weight": defensive_weight,
                "weight_sum": qqq_weight + high_growth_weight + crypto_weight + defensive_weight,
                "CAGR": metrics["cagr"],
                "Sharpe": metrics["sharpe"],
                "MaxDD": metrics["max_drawdown"],
                "Calmar": metrics["calmar"],
                "delta_CAGR_vs_recovered_qqq100": backtest.metric_delta(metrics["cagr"], reference_metrics["cagr"]),
                "delta_Sharpe_vs_recovered_qqq100": backtest.metric_delta(metrics["sharpe"], reference_metrics["sharpe"]),
                "delta_MaxDD_vs_recovered_qqq100": backtest.metric_delta(metrics["max_drawdown"], reference_metrics["max_drawdown"]),
                "delta_Calmar_vs_recovered_qqq100": backtest.metric_delta(metrics["calmar"], reference_metrics["calmar"]),
                "delta_CAGR_vs_current_75_15_5_5": backtest.metric_delta(metrics["cagr"], baseline_metrics["cagr"]),
                "delta_Sharpe_vs_current_75_15_5_5": backtest.metric_delta(metrics["sharpe"], baseline_metrics["sharpe"]),
                "delta_MaxDD_vs_current_75_15_5_5": backtest.metric_delta(metrics["max_drawdown"], baseline_metrics["max_drawdown"]),
                "delta_Calmar_vs_current_75_15_5_5": backtest.metric_delta(metrics["calmar"], baseline_metrics["calmar"]),
                "risk_status": risk_status(name, high_growth_weight, crypto_weight),
                "allocation_policy_status": allocation_policy_status,
                "warning_status": warning,
                "required_next_step": NEXT_WEIGHT_REVIEW if name != CURRENT_ALLOCATION else NEXT_CRYPTO_REVIEW,
                **safety_flags(),
            }
        )
    return rows


def allocation_returns(
    dates: list[str],
    by_candidate: dict[str, dict[str, float]],
    allocation: tuple[str, int, int, int, int],
) -> list[float]:
    _name, qqq_weight, high_growth_weight, crypto_weight, _defensive_weight = allocation
    return [
        by_candidate[RECOVERED_REFERENCE][date] * (qqq_weight / 100.0)
        + by_candidate[HIGH_GROWTH_SLEEVE][date] * (high_growth_weight / 100.0)
        + by_candidate[CRYPTO_SLEEVE][date] * (crypto_weight / 100.0)
        for date in dates
    ]


def returns_for_dates(dates: list[str], returns_by_date: dict[str, float]) -> list[float]:
    return [returns_by_date[date] for date in dates]


def final_review_status(rows: list[dict[str, Any]]) -> str:
    current = row_named(rows, CURRENT_ALLOCATION)
    no_crypto = row_named(rows, "no_crypto_80_15_0_5")
    higher_crypto = row_named(rows, "higher_crypto_73_15_7_5")
    higher_growth = row_named(rows, "higher_growth_70_20_5_5")
    if not current:
        return STATUS_NEEDS_REVIEW
    if parse_float(no_crypto.get("delta_CAGR_vs_current_75_15_5_5")) < -0.5 and parse_float(higher_crypto.get("delta_MaxDD_vs_current_75_15_5_5")) < 0:
        return STATUS_CRYPTO_RETURN_VOL
    if parse_float(higher_growth.get("delta_CAGR_vs_current_75_15_5_5")) > 0 and parse_float(higher_growth.get("delta_MaxDD_vs_current_75_15_5_5")) < 0:
        return STATUS_HIGH_GROWTH_RETURN_DD
    best_calmar = max(rows, key=lambda row: parse_float(row.get("Calmar")))
    if best_calmar.get("candidate_name") == CURRENT_ALLOCATION:
        return STATUS_CURRENT_PROMISING
    return STATUS_CURRENT_MIXED


def build_summary_rows(
    created_at: str,
    final_status: str,
    rows: list[dict[str, Any]],
    missing: list[str],
    inputs: dict[str, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    current = row_named(rows, CURRENT_ALLOCATION)
    best_calmar = max(rows, key=lambda row: parse_float(row.get("Calmar")), default={})
    best_sharpe = max(rows, key=lambda row: parse_float(row.get("Sharpe")), default={})
    lowest_maxdd = max(rows, key=lambda row: parse_float(row.get("MaxDD")), default={})
    no_crypto = row_named(rows, "no_crypto_80_15_0_5")
    higher_crypto = row_named(rows, "higher_crypto_73_15_7_5")
    higher_growth = row_named(rows, "higher_growth_70_20_5_5")
    allocation_status = summary_map(inputs["allocation_policy_summary"]).get("final_allocation_policy_status", MISSING)
    next_step = required_next_step(final_status)
    items = [
        ("final_weight_sensitivity_status", final_status, "Research-only fixed allocation sensitivity status."),
        ("fixed_allocations_tested", str(len(rows)), "Number of fixed allocations tested."),
        ("current_allocation_metrics", format_metrics(current), "Current 75/15/5/5 allocation metrics."),
        ("best_calmar_allocation", format_metrics(best_calmar), "Best allocation by Calmar."),
        ("best_sharpe_allocation", format_metrics(best_sharpe), "Best allocation by Sharpe."),
        ("lowest_maxdd_allocation", format_metrics(lowest_maxdd), "Least severe max drawdown allocation."),
        ("no_crypto_result", interpret_no_crypto(no_crypto), "No-crypto comparison."),
        ("higher_crypto_interpretation", interpret_variant(higher_crypto, "higher_crypto"), "Higher-crypto comparison."),
        ("higher_growth_interpretation", interpret_variant(higher_growth, "higher_growth"), "Higher-growth comparison."),
        ("allocation_policy_status", allocation_status, "Saved allocation policy context."),
        ("missing_saved_streams", ",".join(missing) or "none", "Missing saved streams."),
        ("required_next_step", next_step, "Next research step, not execution approval."),
    ]
    return [
        {"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()}
        for name, value, details in items
    ]


def build_blocker_rows(
    created_at: str,
    final_status: str,
    rows: list[dict[str, Any]],
    missing: list[str],
) -> list[dict[str, Any]]:
    if missing:
        return [
            {
                "created_at": created_at,
                "blocker_name": "missing_saved_streams",
                "blocker_status": STATUS_BLOCKED_MISSING,
                "evidence": ",".join(missing),
                "required_next_step": NEXT_MISSING,
                **safety_flags(),
            }
        ]
    current = row_named(rows, CURRENT_ALLOCATION)
    blockers = [
        ("weight_sensitivity_manual_review", final_status, "fixed nearby weights tested; manual interpretation still required", required_next_step(final_status)),
        ("current_allocation_context", current.get("warning_status", MISSING), format_metrics(current), NEXT_CRYPTO_REVIEW),
        ("execution_boundary", "blocked", "research output is not preview, paper, crypto, or live execution approval", NEXT_RESEARCH_ONLY),
    ]
    return [
        {
            "created_at": created_at,
            "blocker_name": name,
            "blocker_status": status,
            "evidence": evidence,
            "required_next_step": step,
            **safety_flags(),
        }
        for name, status, evidence, step in blockers
    ]


def blocked_review_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    rows = []
    for name, qqq_weight, high_growth_weight, crypto_weight, defensive_weight in ALLOCATIONS:
        rows.append(
            {
                "created_at": created_at,
                "candidate_name": name,
                "qqq100_weight": qqq_weight,
                "high_growth_weight": high_growth_weight,
                "crypto_weight": crypto_weight,
                "defensive_weight": defensive_weight,
                "weight_sum": qqq_weight + high_growth_weight + crypto_weight + defensive_weight,
                "CAGR": MISSING,
                "Sharpe": MISSING,
                "MaxDD": MISSING,
                "Calmar": MISSING,
                "delta_CAGR_vs_recovered_qqq100": MISSING,
                "delta_Sharpe_vs_recovered_qqq100": MISSING,
                "delta_MaxDD_vs_recovered_qqq100": MISSING,
                "delta_Calmar_vs_recovered_qqq100": MISSING,
                "delta_CAGR_vs_current_75_15_5_5": MISSING,
                "delta_Sharpe_vs_current_75_15_5_5": MISSING,
                "delta_MaxDD_vs_current_75_15_5_5": MISSING,
                "delta_Calmar_vs_current_75_15_5_5": MISSING,
                "risk_status": "blocked_missing_saved_streams",
                "allocation_policy_status": STATUS_BLOCKED_MISSING,
                "warning_status": "missing_saved_streams=" + ",".join(missing),
                "required_next_step": NEXT_MISSING,
                **safety_flags(),
            }
        )
    return rows


def required_next_step(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING:
        return NEXT_MISSING
    if status == STATUS_CRYPTO_RETURN_VOL:
        return NEXT_CRYPTO_REVIEW
    if status == STATUS_HIGH_GROWTH_RETURN_DD:
        return NEXT_WEIGHT_REVIEW
    if status == STATUS_CURRENT_PROMISING:
        return NEXT_RESEARCH_ONLY
    return NEXT_WEIGHT_REVIEW


def risk_status(name: str, high_growth_weight: int, crypto_weight: int) -> str:
    if name == CURRENT_ALLOCATION:
        return "current_allocation_reference"
    if crypto_weight == 0:
        return "no_crypto_safety_comparison"
    if crypto_weight > 5:
        return "higher_crypto_risk_comparison"
    if high_growth_weight > 15:
        return "higher_high_growth_risk_comparison"
    if high_growth_weight < 15 or crypto_weight < 5:
        return "lower_risk_comparison"
    return "fixed_weight_comparison"


def warning_status(
    name: str,
    high_growth_weight: int,
    crypto_weight: int,
    metrics: dict[str, str],
    baseline_metrics: dict[str, str],
) -> str:
    cagr_delta = parse_float(backtest.metric_delta(metrics["cagr"], baseline_metrics["cagr"]))
    maxdd_delta = parse_float(backtest.metric_delta(metrics["max_drawdown"], baseline_metrics["max_drawdown"]))
    if name == CURRENT_ALLOCATION:
        return "current_allocation_crypto_sensitive_research_only"
    if crypto_weight == 0 and cagr_delta < -0.5:
        return "removing_crypto_reduces_return_materially"
    if crypto_weight > 5 and maxdd_delta < 0:
        return "higher_crypto_increases_drawdown_risk"
    if high_growth_weight > 15 and maxdd_delta < 0:
        return "higher_growth_increases_drawdown_risk"
    if high_growth_weight < 15 and cagr_delta < -0.5:
        return "lower_growth_reduces_return_materially"
    return "nearby_weight_variant_needs_manual_review"


def interpret_no_crypto(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return (
        f"{row.get('candidate_name')}: CAGR={row.get('CAGR')}; MaxDD={row.get('MaxDD')}; "
        f"delta_CAGR_vs_current={row.get('delta_CAGR_vs_current_75_15_5_5')}; "
        f"delta_MaxDD_vs_current={row.get('delta_MaxDD_vs_current_75_15_5_5')}; "
        f"warning={row.get('warning_status')}"
    )


def interpret_variant(row: dict[str, Any], label: str) -> str:
    if not row:
        return MISSING
    return (
        f"{label}: {row.get('candidate_name')}; CAGR={row.get('CAGR')}; MaxDD={row.get('MaxDD')}; "
        f"delta_CAGR_vs_current={row.get('delta_CAGR_vs_current_75_15_5_5')}; "
        f"delta_MaxDD_vs_current={row.get('delta_MaxDD_vs_current_75_15_5_5')}; "
        f"warning={row.get('warning_status')}"
    )


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in rows}
    return [
        "Multi-sleeve weight sensitivity created. Saved-output-only research; no execution approval.",
        f"final weight-sensitivity status: {summary['final_weight_sensitivity_status']}",
        f"fixed allocations tested: {summary['fixed_allocations_tested']}",
        f"current allocation metrics: {summary['current_allocation_metrics']}",
        f"best Calmar allocation: {summary['best_calmar_allocation']}",
        f"best Sharpe allocation: {summary['best_sharpe_allocation']}",
        f"lowest MaxDD allocation: {summary['lowest_maxdd_allocation']}",
        f"no-crypto result: {summary['no_crypto_result']}",
        f"higher-crypto interpretation: {summary['higher_crypto_interpretation']}",
        f"higher-growth interpretation: {summary['higher_growth_interpretation']}",
        f"required next step: {summary['required_next_step']}",
        f"Saved review: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def format_metrics(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return (
        f"{row.get('candidate_name')}: CAGR={row.get('CAGR')}; Sharpe={row.get('Sharpe')}; "
        f"MaxDD={row.get('MaxDD')}; Calmar={row.get('Calmar')}"
    )


def row_named(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next((row for row in rows if row.get("candidate_name") == name), {})


def summary_map(rows: list[dict[str, str]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


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
