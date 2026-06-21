"""Saved-output-only crypto-inclusive multi-sleeve review.

This report reads existing saved return streams and portfolio backtest CSVs to
review the crypto-inclusive multi-sleeve candidate. It does not refresh market
data, call Alpaca, read positions, create orders, write SQLite, send alerts,
schedule anything, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import multi_sleeve_portfolio_backtest as backtest


CANDIDATE = "qqq100_plus_high_growth_plus_crypto_research"
HIGH_GROWTH_CANDIDATE = "qqq100_plus_high_growth_research"
RECOVERED_REFERENCE = backtest.RECOVERED_QQQ100_REFERENCE
HIGH_GROWTH_SLEEVE = "codex_broad_growth_balanced_breakout_control"
CRYPTO_SLEEVE = "crypto_btc_eth_research_sleeve"
CASH_SLEEVE = "cash_default_defensive_sleeve"

STATUS_PROMISING = "multi_sleeve_crypto_review_promising_research_only"
STATUS_MIXED = "multi_sleeve_crypto_review_mixed_split_sensitive"
STATUS_COST_SENSITIVE = "multi_sleeve_crypto_review_cost_sensitive"
STATUS_VOLATILITY_BLOCKED = "multi_sleeve_crypto_review_volatility_blocked"
STATUS_BLOCKED_MISSING_STREAMS = "multi_sleeve_crypto_review_blocked_missing_saved_streams"

REQUIRED_NEXT_STEP_REVIEW = "manual_review_crypto_split_cost_volatility_before_candidate_label_change"
REQUIRED_NEXT_STEP_STREAMS = "create_or_refresh_saved_crypto_high_growth_and_qqq100_streams_before_review"

INPUT_FILES = {
    "multi_sleeve_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
    "sleeve_return_streams": Path("data/sleeve_return_streams.csv"),
    "high_growth_return_streams": Path("data/high_growth_return_streams.csv"),
    "crypto_return_streams": Path("data/crypto_return_streams.csv"),
    "crypto_return_metrics": Path("data/crypto_return_stream_metrics.csv"),
    "qqq100_recovered_reference_stream": Path("data/qqq100_recovered_reference_stream.csv"),
    "qqq100_recovered_reference_metrics": Path("data/qqq100_recovered_reference_metrics.csv"),
}

OUTPUT_FILES = {
    "review": Path("data/multi_sleeve_crypto_review.csv"),
    "summary": Path("data/multi_sleeve_crypto_review_summary.csv"),
    "cost_stress": Path("data/multi_sleeve_crypto_review_cost_stress.csv"),
    "split_robustness": Path("data/multi_sleeve_crypto_review_split_robustness.csv"),
    "volatility": Path("data/multi_sleeve_crypto_review_volatility.csv"),
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

SAFETY_FLAGS = {
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

REVIEW_COLUMNS = [
    "created_at",
    "review_name",
    "review_status",
    "candidate_name",
    "reference_name",
    "evidence",
    "required_next_step",
    *SAFETY_COLUMNS,
]

SPLIT_COLUMNS = [
    "created_at",
    "split_name",
    "candidate_name",
    "row_count",
    "first_date",
    "last_date",
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "delta_CAGR_vs_recovered_qqq100",
    "delta_Sharpe_vs_recovered_qqq100",
    "delta_MaxDD_vs_recovered_qqq100",
    "delta_Calmar_vs_recovered_qqq100",
    "split_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

COST_COLUMNS = [
    "created_at",
    "cost_stress_name",
    "additional_crypto_turnover_cost_bps",
    "stressed_CAGR",
    "stressed_Sharpe",
    "stressed_MaxDD",
    "stressed_Calmar",
    "delta_CAGR_vs_baseline_candidate",
    "delta_Sharpe_vs_baseline_candidate",
    "delta_MaxDD_vs_baseline_candidate",
    "delta_Calmar_vs_baseline_candidate",
    "crypto_exposure_change_count",
    "cost_stress_status",
    "approximation_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

VOLATILITY_COLUMNS = [
    "created_at",
    "review_name",
    "crypto_allocation_pct",
    "crypto_sleeve_MaxDD",
    "crypto_sleeve_annual_volatility",
    "portfolio_candidate_MaxDD",
    "recovered_QQQ100_MaxDD",
    "high_growth_sleeve_MaxDD",
    "candidate_drawdown_delta_vs_recovered_QQQ100",
    "crypto_volatility_warning",
    "drawdown_status",
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

SPLITS = [
    ("split_60_40", 0.60),
    ("split_70_30", 0.70),
    ("split_80_20", 0.80),
]

COST_STRESSES = [
    ("baseline_saved_costs", 0.0),
    ("plus_10bps_crypto_turnover", 10.0),
    ("plus_25bps_crypto_turnover", 25.0),
    ("plus_50bps_crypto_turnover", 50.0),
    ("plus_100bps_crypto_turnover", 100.0),
]


@dataclass
class MultiSleeveCryptoReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    volatility_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_crypto_review(root_dir: Path | str = ".") -> MultiSleeveCryptoReviewResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    streams = build_saved_stream_rows(inputs)
    by_candidate = backtest.stream_returns_by_candidate(streams)
    backtest_candidate = saved_backtest_candidate(inputs["multi_sleeve_backtest"])
    missing = missing_required_streams(by_candidate)
    if missing:
        split_rows = blocked_split_rows(created_at, missing)
        cost_rows = blocked_cost_rows(created_at, missing)
        volatility_rows = blocked_volatility_rows(created_at, missing)
        final_status = STATUS_BLOCKED_MISSING_STREAMS
    else:
        split_rows = build_split_rows(created_at, by_candidate)
        cost_rows = build_cost_rows(created_at, streams, by_candidate)
        volatility_rows = build_volatility_rows(created_at, by_candidate, inputs, backtest_candidate)
        final_status = final_review_status(split_rows, cost_rows, volatility_rows)
    review_rows = build_review_rows(created_at, final_status, missing)
    summary_rows = build_summary_rows(created_at, final_status, split_rows, cost_rows, volatility_rows, backtest_candidate, missing)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["cost_stress"], COST_COLUMNS, cost_rows)
    write_rows(output_paths["split_robustness"], SPLIT_COLUMNS, split_rows)
    write_rows(output_paths["volatility"], VOLATILITY_COLUMNS, volatility_rows)
    return MultiSleeveCryptoReviewResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        volatility_rows=volatility_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths["review"]),
    )


def show_multi_sleeve_crypto_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Multi-sleeve crypto review is missing.",
            "Run `python bot.py --multi-sleeve-crypto-review` first.",
            "execution_approved=false; scheduling_approved=false",
        ]
    summary = {row.get("summary_name", ""): row.get("summary_value", "") for row in read_csv_rows(summary_path)}
    return 0, [
        "Multi-sleeve crypto review. Saved-output-only research; no execution wiring approved.",
        f"final crypto review status: {summary.get('final_crypto_review_status', 'missing')}",
        f"split count: {summary.get('split_count', 'missing')}",
        f"cost stress count: {summary.get('cost_stress_count', 'missing')}",
        f"candidate beats recovered QQQ100 on most splits: {summary.get('candidate_beats_recovered_qqq100_on_most_splits', 'missing')}",
        f"worst split by Calmar: {summary.get('worst_split_by_calmar', 'missing')}",
        f"worst split by MaxDD: {summary.get('worst_split_by_maxdd', 'missing')}",
        f"worst cost stress row: {summary.get('worst_cost_stress_row', 'missing')}",
        f"crypto volatility/drawdown warnings: {summary.get('crypto_volatility_drawdown_warnings', 'missing')}",
        f"required next step: {summary.get('required_next_step', 'missing')}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def build_saved_stream_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    return (
        inputs["sleeve_return_streams"]
        + backtest.normalize_high_growth_stream_rows(inputs["high_growth_return_streams"])
        + backtest.normalize_crypto_stream_rows(inputs["crypto_return_streams"])
        + backtest.normalize_recovered_reference_stream_rows(inputs["qqq100_recovered_reference_stream"])
    )


def missing_required_streams(by_candidate: dict[str, dict[str, float]]) -> list[str]:
    required = [RECOVERED_REFERENCE, HIGH_GROWTH_SLEEVE, CRYPTO_SLEEVE, CASH_SLEEVE]
    return [candidate for candidate in required if candidate not in by_candidate]


def build_split_rows(created_at: str, by_candidate: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    required = [RECOVERED_REFERENCE, HIGH_GROWTH_SLEEVE, CRYPTO_SLEEVE, CASH_SLEEVE]
    common_dates = sorted(set.intersection(*(set(by_candidate[candidate]) for candidate in required)))
    rows: list[dict[str, Any]] = []
    for split_name, train_fraction in SPLITS:
        start_index = max(1, int(len(common_dates) * train_fraction))
        dates = common_dates[start_index:]
        if len(dates) < 2:
            rows.append(blocked_split_row(created_at, split_name, "split_has_too_few_oos_rows"))
            continue
        reference = returns_for_dates(dates, by_candidate[RECOVERED_REFERENCE])
        qqq_high_growth = weighted_returns(dates, by_candidate, {RECOVERED_REFERENCE: 0.80, HIGH_GROWTH_SLEEVE: 0.15, CASH_SLEEVE: 0.05})
        qqq_high_growth_crypto = weighted_returns(dates, by_candidate, {RECOVERED_REFERENCE: 0.75, HIGH_GROWTH_SLEEVE: 0.15, CRYPTO_SLEEVE: 0.05, CASH_SLEEVE: 0.05})
        crypto = returns_for_dates(dates, by_candidate[CRYPTO_SLEEVE])
        comparisons = [
            (CANDIDATE, qqq_high_growth_crypto),
            (HIGH_GROWTH_CANDIDATE, qqq_high_growth),
            (RECOVERED_REFERENCE, reference),
            (CRYPTO_SLEEVE, crypto),
        ]
        reference_metrics = backtest.metrics_for_returns(reference)
        for candidate_name, returns in comparisons:
            metrics = backtest.metrics_for_returns(returns)
            rows.append(split_row(created_at, split_name, candidate_name, dates, metrics, reference_metrics))
    return rows


def split_row(
    created_at: str,
    split_name: str,
    candidate_name: str,
    dates: list[str],
    metrics: dict[str, str],
    reference_metrics: dict[str, str],
) -> dict[str, Any]:
    delta_calmar = backtest.metric_delta(metrics["calmar"], reference_metrics["calmar"])
    status = (
        "split_reference_row"
        if candidate_name == RECOVERED_REFERENCE
        else "split_crypto_sleeve_context_row"
        if candidate_name == CRYPTO_SLEEVE
        else ("split_beats_recovered_qqq100" if parse_float(delta_calmar) > 0 else "split_needs_review")
    )
    return {
        "created_at": created_at,
        "split_name": split_name,
        "candidate_name": candidate_name,
        "row_count": len(dates),
        "first_date": dates[0] if dates else "",
        "last_date": dates[-1] if dates else "",
        "CAGR": metrics["cagr"],
        "Sharpe": metrics["sharpe"],
        "MaxDD": metrics["max_drawdown"],
        "Calmar": metrics["calmar"],
        "delta_CAGR_vs_recovered_qqq100": backtest.metric_delta(metrics["cagr"], reference_metrics["cagr"]),
        "delta_Sharpe_vs_recovered_qqq100": backtest.metric_delta(metrics["sharpe"], reference_metrics["sharpe"]),
        "delta_MaxDD_vs_recovered_qqq100": backtest.metric_delta(metrics["max_drawdown"], reference_metrics["max_drawdown"]),
        "delta_Calmar_vs_recovered_qqq100": delta_calmar,
        "split_status": status,
        "required_next_step": REQUIRED_NEXT_STEP_REVIEW,
        **safety_flags(),
    }


def build_cost_rows(
    created_at: str,
    stream_rows: list[dict[str, str]],
    by_candidate: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    weights = {RECOVERED_REFERENCE: 0.75, HIGH_GROWTH_SLEEVE: 0.15, CRYPTO_SLEEVE: 0.05, CASH_SLEEVE: 0.05}
    common_dates = sorted(set.intersection(*(set(by_candidate[candidate]) for candidate in weights)))
    baseline_returns = weighted_returns(common_dates, by_candidate, weights)
    baseline_metrics = backtest.metrics_for_returns(baseline_returns)
    change_dates = crypto_exposure_change_dates(stream_rows)
    rows = []
    for stress_name, bps in COST_STRESSES:
        stressed_returns = []
        daily_cost = (bps / 10_000.0) * weights[CRYPTO_SLEEVE]
        for date, value in zip(common_dates, baseline_returns):
            stressed_returns.append(value - daily_cost if date in change_dates else value)
        metrics = backtest.metrics_for_returns(stressed_returns)
        delta_cagr = backtest.metric_delta(metrics["cagr"], baseline_metrics["cagr"])
        rows.append(
            {
                "created_at": created_at,
                "cost_stress_name": stress_name,
                "additional_crypto_turnover_cost_bps": bps,
                "stressed_CAGR": metrics["cagr"],
                "stressed_Sharpe": metrics["sharpe"],
                "stressed_MaxDD": metrics["max_drawdown"],
                "stressed_Calmar": metrics["calmar"],
                "delta_CAGR_vs_baseline_candidate": delta_cagr,
                "delta_Sharpe_vs_baseline_candidate": backtest.metric_delta(metrics["sharpe"], baseline_metrics["sharpe"]),
                "delta_MaxDD_vs_baseline_candidate": backtest.metric_delta(metrics["max_drawdown"], baseline_metrics["max_drawdown"]),
                "delta_Calmar_vs_baseline_candidate": backtest.metric_delta(metrics["calmar"], baseline_metrics["calmar"]),
                "crypto_exposure_change_count": len(change_dates),
                "cost_stress_status": cost_status(delta_cagr, bps),
                "approximation_status": "crypto_exposure_change_proxy_from_saved_signal_state",
                "required_next_step": REQUIRED_NEXT_STEP_REVIEW,
                **safety_flags(),
            }
        )
    return rows


def build_volatility_rows(
    created_at: str,
    by_candidate: dict[str, dict[str, float]],
    inputs: dict[str, list[dict[str, str]]],
    backtest_candidate: dict[str, str],
) -> list[dict[str, Any]]:
    crypto_metrics = metrics_row_for_candidate(inputs["crypto_return_metrics"], CRYPTO_SLEEVE)
    high_growth_metrics = backtest.stream_metric_bundle(
        [{"candidate_name": HIGH_GROWTH_SLEEVE, "date": date, "daily_strategy_return": value} for date, value in by_candidate[HIGH_GROWTH_SLEEVE].items()],
        HIGH_GROWTH_SLEEVE,
    )
    reference_metrics = recovered_reference_metrics(inputs["qqq100_recovered_reference_metrics"])
    candidate_maxdd = backtest_candidate.get("candidate_max_drawdown") or backtest.MISSING
    reference_maxdd = reference_metrics.get("max_drawdown", backtest.MISSING)
    delta_maxdd = backtest.metric_delta(candidate_maxdd, reference_maxdd)
    crypto_maxdd = crypto_metrics.get("MaxDD") or crypto_metrics.get("max_drawdown") or backtest.MISSING
    crypto_vol = crypto_metrics.get("annual_volatility", backtest.MISSING)
    warning = crypto_warning(crypto_maxdd, crypto_vol)
    drawdown_status = "candidate_drawdown_improves_vs_recovered_qqq100" if parse_float(delta_maxdd) >= 0 else "candidate_drawdown_worse_than_recovered_qqq100"
    return [
        {
            "created_at": created_at,
            "review_name": "crypto_volatility_drawdown_contribution",
            "crypto_allocation_pct": "5",
            "crypto_sleeve_MaxDD": crypto_maxdd,
            "crypto_sleeve_annual_volatility": crypto_vol,
            "portfolio_candidate_MaxDD": candidate_maxdd,
            "recovered_QQQ100_MaxDD": reference_maxdd,
            "high_growth_sleeve_MaxDD": high_growth_metrics["max_drawdown"],
            "candidate_drawdown_delta_vs_recovered_QQQ100": delta_maxdd,
            "crypto_volatility_warning": warning,
            "drawdown_status": drawdown_status,
            "required_next_step": REQUIRED_NEXT_STEP_REVIEW,
            **safety_flags(),
        }
    ]


def final_review_status(
    split_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    volatility_rows: list[dict[str, Any]],
) -> str:
    candidate_splits = [row for row in split_rows if row.get("candidate_name") == CANDIDATE]
    split_wins = sum(1 for row in candidate_splits if parse_float(row.get("delta_Calmar_vs_recovered_qqq100")) > 0 and parse_float(row.get("delta_Sharpe_vs_recovered_qqq100")) > 0)
    worst_cost = min((parse_float(row.get("delta_CAGR_vs_baseline_candidate")) for row in cost_rows), default=0.0)
    vol_status = volatility_rows[0].get("drawdown_status", "") if volatility_rows else ""
    if vol_status == "candidate_drawdown_worse_than_recovered_qqq100" and split_wins < 2:
        return STATUS_VOLATILITY_BLOCKED
    if worst_cost <= -1.0:
        return STATUS_COST_SENSITIVE
    if split_wins >= 2:
        return STATUS_PROMISING
    return STATUS_MIXED


def build_review_rows(created_at: str, final_status: str, missing: list[str]) -> list[dict[str, Any]]:
    evidence = "missing_saved_streams=" + ",".join(missing) if missing else "saved_streams_available; review_outputs_created"
    return [
        {
            "created_at": created_at,
            "review_name": "crypto_inclusive_multi_sleeve_review",
            "review_status": final_status,
            "candidate_name": CANDIDATE,
            "reference_name": RECOVERED_REFERENCE,
            "evidence": evidence,
            "required_next_step": REQUIRED_NEXT_STEP_STREAMS if missing else REQUIRED_NEXT_STEP_REVIEW,
            **safety_flags(),
        }
    ]


def build_summary_rows(
    created_at: str,
    final_status: str,
    split_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    volatility_rows: list[dict[str, Any]],
    backtest_candidate: dict[str, str],
    missing: list[str],
) -> list[dict[str, Any]]:
    candidate_splits = [row for row in split_rows if row.get("candidate_name") == CANDIDATE]
    split_count = len(candidate_splits)
    most_splits = sum(1 for row in candidate_splits if parse_float(row.get("delta_Calmar_vs_recovered_qqq100")) > 0 and parse_float(row.get("delta_Sharpe_vs_recovered_qqq100")) > 0) >= 2
    worst_calmar = min(candidate_splits, key=lambda row: parse_float(row.get("Calmar")), default={})
    worst_maxdd = min(candidate_splits, key=lambda row: parse_float(row.get("MaxDD")), default={})
    worst_cost = min(cost_rows, key=lambda row: parse_float(row.get("delta_CAGR_vs_baseline_candidate")), default={})
    volatility = volatility_rows[0] if volatility_rows else {}
    required_next_step = REQUIRED_NEXT_STEP_STREAMS if missing else REQUIRED_NEXT_STEP_REVIEW
    items = [
        ("final_crypto_review_status", final_status, "Report-only crypto-inclusive candidate review status."),
        ("candidate_name", CANDIDATE, "Reviewed multi-sleeve candidate."),
        ("candidate_metrics", format_candidate_metrics(backtest_candidate), "Saved full-period candidate metrics from multi-sleeve backtest."),
        ("split_count", str(split_count), "Number of candidate split rows."),
        ("cost_stress_count", str(len(cost_rows)), "Number of fixed cost stress rows."),
        ("candidate_beats_recovered_qqq100_on_most_splits", str(most_splits).lower(), "Requires Calmar and Sharpe wins in at least two out-of-sample splits."),
        ("worst_split_by_calmar", format_split(worst_calmar, "Calmar"), "Lowest candidate Calmar split."),
        ("worst_split_by_maxdd", format_split(worst_maxdd, "MaxDD"), "Worst candidate drawdown split."),
        ("worst_cost_stress_row", format_cost(worst_cost), "Largest CAGR drag from additional crypto turnover cost stress."),
        ("crypto_volatility_drawdown_warnings", f"{volatility.get('crypto_volatility_warning', 'missing')}; {volatility.get('drawdown_status', 'missing')}", "Crypto sleeve and portfolio drawdown interpretation."),
        ("missing_saved_streams", ",".join(missing) or "none", "Missing saved streams block review when present."),
        ("required_next_step", required_next_step, "Next review step; not execution approval."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def blocked_split_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [blocked_split_row(created_at, split_name, "missing_saved_streams=" + ",".join(missing)) for split_name, _ in SPLITS]


def blocked_split_row(created_at: str, split_name: str, reason: str) -> dict[str, Any]:
    missing = backtest.MISSING
    return {
        "created_at": created_at,
        "split_name": split_name,
        "candidate_name": CANDIDATE,
        "row_count": 0,
        "first_date": "",
        "last_date": "",
        "CAGR": missing,
        "Sharpe": missing,
        "MaxDD": missing,
        "Calmar": missing,
        "delta_CAGR_vs_recovered_qqq100": missing,
        "delta_Sharpe_vs_recovered_qqq100": missing,
        "delta_MaxDD_vs_recovered_qqq100": missing,
        "delta_Calmar_vs_recovered_qqq100": missing,
        "split_status": reason,
        "required_next_step": REQUIRED_NEXT_STEP_STREAMS,
        **safety_flags(),
    }


def blocked_cost_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "cost_stress_name": name,
            "additional_crypto_turnover_cost_bps": bps,
            "stressed_CAGR": backtest.MISSING,
            "stressed_Sharpe": backtest.MISSING,
            "stressed_MaxDD": backtest.MISSING,
            "stressed_Calmar": backtest.MISSING,
            "delta_CAGR_vs_baseline_candidate": backtest.MISSING,
            "delta_Sharpe_vs_baseline_candidate": backtest.MISSING,
            "delta_MaxDD_vs_baseline_candidate": backtest.MISSING,
            "delta_Calmar_vs_baseline_candidate": backtest.MISSING,
            "crypto_exposure_change_count": 0,
            "cost_stress_status": "blocked_missing_saved_streams",
            "approximation_status": "blocked_missing_saved_streams=" + ",".join(missing),
            "required_next_step": REQUIRED_NEXT_STEP_STREAMS,
            **safety_flags(),
        }
        for name, bps in COST_STRESSES
    ]


def blocked_volatility_rows(created_at: str, missing: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "created_at": created_at,
            "review_name": "crypto_volatility_drawdown_contribution",
            "crypto_allocation_pct": "5",
            "crypto_sleeve_MaxDD": backtest.MISSING,
            "crypto_sleeve_annual_volatility": backtest.MISSING,
            "portfolio_candidate_MaxDD": backtest.MISSING,
            "recovered_QQQ100_MaxDD": backtest.MISSING,
            "high_growth_sleeve_MaxDD": backtest.MISSING,
            "candidate_drawdown_delta_vs_recovered_QQQ100": backtest.MISSING,
            "crypto_volatility_warning": "blocked_missing_saved_streams=" + ",".join(missing),
            "drawdown_status": "blocked_missing_saved_streams",
            "required_next_step": REQUIRED_NEXT_STEP_STREAMS,
            **safety_flags(),
        }
    ]


def weighted_returns(dates: list[str], by_candidate: dict[str, dict[str, float]], weights: dict[str, float]) -> list[float]:
    return [sum(by_candidate[candidate][date] * weight for candidate, weight in weights.items()) for date in dates]


def returns_for_dates(dates: list[str], returns_by_date: dict[str, float]) -> list[float]:
    return [returns_by_date[date] for date in dates]


def crypto_exposure_change_dates(rows: list[dict[str, str]]) -> set[str]:
    crypto_rows = sorted(
        [row for row in rows if row.get("candidate_name") == CRYPTO_SLEEVE],
        key=lambda row: row.get("date", ""),
    )
    changes: set[str] = set()
    previous = None
    for row in crypto_rows:
        state = row.get("signal_state") or row.get("invested_flag") or row.get("exposure")
        if previous is not None and state != previous:
            changes.add(str(row.get("date", "")))
        previous = state
    return {date for date in changes if date}


def cost_status(delta_cagr: str, bps: float) -> str:
    if bps == 0:
        return "baseline_saved_costs"
    drag = parse_float(delta_cagr)
    if drag <= -1.0:
        return "cost_sensitive_research_review_required"
    return "cost_stress_tolerated_research_only"


def crypto_warning(maxdd: str, annual_vol: str) -> str:
    if parse_float(maxdd) <= -50 or parse_float(annual_vol) >= 60:
        return "crypto_high_volatility_and_drawdown_warning"
    return "crypto_volatility_review_required"


def saved_backtest_candidate(rows: list[dict[str, str]]) -> dict[str, str]:
    return next((row for row in rows if row.get("portfolio_name") == CANDIDATE), {})


def metrics_row_for_candidate(rows: list[dict[str, str]], candidate: str) -> dict[str, str]:
    return next((row for row in rows if row.get("candidate_name") == candidate or row.get("sleeve_name") == candidate), {})


def recovered_reference_metrics(rows: list[dict[str, str]]) -> dict[str, str]:
    row = next((item for item in rows if item.get("reference_name") == RECOVERED_REFERENCE), {})
    return backtest.recovered_metrics_from_row(row)


def format_candidate_metrics(row: dict[str, str]) -> str:
    if not row:
        return "missing_saved_metrics"
    return (
        f"CAGR={row.get('candidate_cagr', backtest.MISSING)}; "
        f"Sharpe={row.get('candidate_sharpe', backtest.MISSING)}; "
        f"MaxDD={row.get('candidate_max_drawdown', backtest.MISSING)}; "
        f"Calmar={row.get('candidate_calmar', backtest.MISSING)}"
    )


def format_split(row: dict[str, Any], metric: str) -> str:
    if not row:
        return "missing"
    return f"{row.get('split_name')} {metric}={row.get(metric)}; MaxDD={row.get('MaxDD')}; Calmar={row.get('Calmar')}"


def format_cost(row: dict[str, Any]) -> str:
    if not row:
        return "missing"
    return (
        f"{row.get('cost_stress_name')} CAGR={row.get('stressed_CAGR')}; "
        f"delta_CAGR={row.get('delta_CAGR_vs_baseline_candidate')}; status={row.get('cost_stress_status')}"
    )


def build_summary_lines(summary_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = {row["summary_name"]: row["summary_value"] for row in summary_rows}
    return [
        "Multi-sleeve crypto review created. Saved-output-only research; no execution wiring approved.",
        f"final crypto review status: {summary['final_crypto_review_status']}",
        f"split count: {summary['split_count']}",
        f"cost stress count: {summary['cost_stress_count']}",
        f"candidate beats recovered QQQ100 on most splits: {summary['candidate_beats_recovered_qqq100_on_most_splits']}",
        f"worst split by Calmar: {summary['worst_split_by_calmar']}",
        f"worst split by MaxDD: {summary['worst_split_by_maxdd']}",
        f"worst cost stress row: {summary['worst_cost_stress_row']}",
        f"crypto volatility/drawdown warnings: {summary['crypto_volatility_drawdown_warnings']}",
        f"required next step: {summary['required_next_step']}",
        f"Saved review: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
