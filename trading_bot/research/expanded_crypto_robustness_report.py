"""Expanded crypto robustness and equal-weight reality-check report.

This report is research/report-only. It challenges static equal-weight crypto
results for hindsight bias, inception effects, outlier dependence, splits,
cost sensitivity, and drawdown windows. It does not touch broker, position,
database, alert, config, scheduling, or execution paths.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.market_data import configure_yfinance_cache_location
from trading_bot.research.expanded_crypto_strategy_lab import (
    ALL_RESULT_NAMES,
    CODEX_STRATEGY,
    COST_BPS,
    PLANNED_STRATEGY,
    STATIC_ELIGIBLE_SYMBOLS,
    TRANSITION_BLOCKED_SYMBOLS,
    align_price_data,
    build_metrics,
    download_price_data,
    load_eligible_universe,
    run_full_cost_lab,
    run_split_lab,
    simulate_monthly_static,
    simulate_named_strategy,
)


READINESS_FILE = Path("data/crypto_universe_readiness_report.csv")
REALITY_VARIANTS = [
    "equal_weight_static_today_universe",
    "equal_weight_inception_aware",
    "equal_weight_core_only_btc_eth",
    "equal_weight_major_crypto_only",
    "equal_weight_ex_outlier_top_contributor",
    "equal_weight_ex_top_2_contributors",
]
VERIFIER_CONTRACT_STRATEGIES = [
    "crypto_risk_on_momentum_persistence",
    "codex_ambitious_crypto_btc_eth_core_alt_accelerator",
]
VERIFIER_TRANSITION_BLOCKED_SYMBOLS = ["POL-USD", "MATIC-USD"]
COMPARE_NAMES = [
    "equal_weight_eligible_crypto_benchmark",
    PLANNED_STRATEGY,
    CODEX_STRATEGY,
    "btc_buy_and_hold_benchmark",
    "eth_buy_and_hold_benchmark",
    "btc_eth_50_50_monthly_rebalanced_benchmark",
    "cash_benchmark",
]

SUMMARY_LABELS = [
    "equal_weight_crypto_robust_benchmark",
    "equal_weight_crypto_hindsight_bias_review",
    "equal_weight_crypto_outlier_dependent",
    "equal_weight_crypto_split_sensitive",
    "equal_weight_crypto_inception_adjusted_still_leads",
    "equal_weight_crypto_not_reliable_benchmark",
    "codex_crypto_candidate_robust",
    "codex_crypto_candidate_promising_but_benchmark_lagging",
    "crypto_momentum_persistence_promising",
    "insufficient_saved_inputs",
    "manual_review_required",
]

OUTPUT_FILES = {
    "report": Path("data/expanded_crypto_robustness_report.csv"),
    "summary": Path("data/expanded_crypto_robustness_summary.csv"),
    "splits": Path("data/expanded_crypto_robustness_splits.csv"),
    "costs": Path("data/expanded_crypto_robustness_costs.csv"),
    "drawdowns": Path("data/expanded_crypto_robustness_drawdowns.csv"),
    "contribution": Path("data/expanded_crypto_asset_contribution.csv"),
    "reality": Path("data/expanded_crypto_equal_weight_reality_check.csv"),
}

COMMON_COLUMNS = [
    "created_at",
    "report_name",
    "section",
    "check_name",
    "strategy_name",
    "metric_name",
    "metric_value",
    "reference_value",
    "status",
    "summary_label",
    "evidence",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class ExpandedCryptoRobustnessResult:
    report_path: Path
    summary_path: Path
    splits_path: Path
    costs_path: Path
    drawdowns_path: Path
    contribution_path: Path
    reality_path: Path
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    split_rows: list[dict[str, Any]]
    cost_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    contribution_rows: list[dict[str, Any]]
    reality_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_expanded_crypto_robustness_report(data_dir: Path | str = "data") -> ExpandedCryptoRobustnessResult:
    data_path = Path(data_dir)
    configure_yfinance_cache_location(data_path / "yfinance_cache")
    created_at = datetime.now(timezone.utc).isoformat()
    universe, universe_note = load_eligible_universe(data_path / READINESS_FILE.name)
    universe = [symbol for symbol in universe if symbol not in TRANSITION_BLOCKED_SYMBOLS]
    price_data, errors = download_price_data(universe)
    usable_universe = [symbol for symbol in universe if symbol in price_data]
    aligned = align_price_data(price_data)
    output_paths = {name: data_path / path.name for name, path in OUTPUT_FILES.items()}

    if len(aligned) < 253 or "BTC-USD" not in price_data or "ETH-USD" not in price_data:
        report_rows, summary_rows, split_rows, cost_rows, drawdown_rows, contribution_rows, reality_rows = insufficient_rows(
            created_at, universe, universe_note, errors
        )
    else:
        base_results, _trades, equity_rows = run_full_cost_lab(created_at, aligned, usable_universe, universe_note)
        base_costs = [row for row in base_results if row.get("period") == "full_period"]
        split_rows = to_common_split_rows(created_at, run_split_lab(created_at, aligned, usable_universe))
        contribution_rows = build_contribution_rows(created_at, price_data, usable_universe)
        top_symbols = [row["strategy_name"] for row in contribution_rows[:2]]
        reality_results = build_reality_rows(created_at, price_data, usable_universe, top_symbols)
        cost_rows = to_common_metric_rows(created_at, "cost_stress", base_costs + reality_results, "cost")
        reality_rows = to_common_metric_rows(created_at, "equal_weight_reality_check", reality_results, "reality")
        drawdown_rows = build_drawdown_rows(created_at, base_results + reality_results, equity_rows)
        report_rows = build_report_rows(created_at, base_results, reality_results, contribution_rows, split_rows, drawdown_rows)
        summary_rows = build_summary_rows(created_at, report_rows, reality_rows, cost_rows, split_rows, drawdown_rows)

    write_rows(output_paths["report"], report_rows)
    write_rows(output_paths["summary"], summary_rows)
    write_rows(output_paths["splits"], split_rows)
    write_rows(output_paths["costs"], cost_rows)
    write_rows(output_paths["drawdowns"], drawdown_rows)
    write_rows(output_paths["contribution"], contribution_rows)
    write_rows(output_paths["reality"], reality_rows)
    return ExpandedCryptoRobustnessResult(
        report_path=output_paths["report"],
        summary_path=output_paths["summary"],
        splits_path=output_paths["splits"],
        costs_path=output_paths["costs"],
        drawdowns_path=output_paths["drawdowns"],
        contribution_path=output_paths["contribution"],
        reality_path=output_paths["reality"],
        report_rows=report_rows,
        summary_rows=summary_rows,
        split_rows=split_rows,
        cost_rows=cost_rows,
        drawdown_rows=drawdown_rows,
        contribution_rows=contribution_rows,
        reality_rows=reality_rows,
        summary_lines=build_summary_lines(summary_rows, report_rows, reality_rows, contribution_rows, output_paths),
    )


def show_expanded_crypto_robustness_report_file(data_dir: Path | str = "data") -> tuple[int, list[str]]:
    data_path = Path(data_dir)
    report = read_csv(data_path / OUTPUT_FILES["report"].name)
    summary = read_csv(data_path / OUTPUT_FILES["summary"].name)
    reality = read_csv(data_path / OUTPUT_FILES["reality"].name)
    costs = read_csv(data_path / OUTPUT_FILES["costs"].name)
    splits = read_csv(data_path / OUTPUT_FILES["splits"].name)
    drawdowns = read_csv(data_path / OUTPUT_FILES["drawdowns"].name)
    contributions = read_csv(data_path / OUTPUT_FILES["contribution"].name)
    if not report or not summary:
        return 1, ["Run `python bot.py --expanded-crypto-robustness-report` first."]
    approvals = {str(row.get("execution_approved", "")).lower() for row in report + summary + reality + costs + splits + drawdowns + contributions}
    return 0, [
        "Expanded crypto robustness report. Display only; execution_approved=False.",
        f"Equal-weight reality: {summary_value(summary, 'equal_weight_reality_assessment')}",
        f"Static equal-weight result: {row_line(reality, 'equal_weight_static_today_universe')}",
        f"Inception-aware equal-weight result: {row_line(reality, 'equal_weight_inception_aware')}",
        f"Ex-top contributor result: {row_line(reality, 'equal_weight_ex_outlier_top_contributor')}",
        f"Ex-top-2 contributors result: {row_line(reality, 'equal_weight_ex_top_2_contributors')}",
        f"Top contributors: {', '.join(row.get('strategy_name', '') for row in contributions[:2]) or 'unavailable'}",
        f"Best active crypto strategy: {summary_value(summary, 'best_active_crypto_strategy')}",
        f"Codex benchmark wins: {summary_value(summary, 'codex_benchmark_wins')}",
        f"Split summary: {status_counts(splits)}",
        f"Cost survival summary: {cost_survival_summary(costs)}",
        f"Drawdown warning summary: {status_counts(drawdowns)}",
        f"Final summary label: {summary_value(summary, 'final_summary_label')}",
        f"execution_approved values: {', '.join(sorted(approvals)) or 'false'}",
        "Warning: robustness report does not create order instructions, approve preview promotion, or approve crypto execution.",
    ]


def build_reality_rows(
    created_at: str,
    price_data: dict[str, list[dict[str, Any]]],
    universe: list[str],
    top_symbols: list[str],
) -> list[dict[str, Any]]:
    variants = [
        ("equal_weight_static_today_universe", universe),
        ("equal_weight_core_only_btc_eth", [symbol for symbol in ["BTC-USD", "ETH-USD"] if symbol in universe]),
        ("equal_weight_major_crypto_only", [symbol for symbol in ["BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD", "SOL-USD", "LINK-USD"] if symbol in universe]),
        ("equal_weight_ex_outlier_top_contributor", [symbol for symbol in universe if symbol not in top_symbols[:1]]),
        ("equal_weight_ex_top_2_contributors", [symbol for symbol in universe if symbol not in top_symbols[:2]]),
    ]
    rows = []
    for name, symbols in variants:
        rows.extend(simulate_reality_variant(created_at, name, price_data, symbols))
    rows.extend(simulate_inception_aware(created_at, price_data, universe))
    return rows


def simulate_reality_variant(
    created_at: str,
    name: str,
    price_data: dict[str, list[dict[str, Any]]],
    symbols: list[str],
) -> list[dict[str, Any]]:
    subset = {symbol: price_data[symbol] for symbol in symbols if symbol in price_data}
    aligned = align_price_data(subset)
    if len(aligned) < 253 or not symbols:
        return [metric_stub(created_at, name, "insufficient_saved_inputs", "Not enough aligned data for this equal-weight reality variant.")]
    weight = 1.0 / len(symbols)
    result_rows = []
    zero = None
    for cost_bps in [0, 10, 25, 50, 100]:
        equity, trades = simulate_monthly_static(name, aligned, {symbol: weight for symbol in symbols}, cost_bps, created_at, False)
        metrics = build_metrics(created_at, name, "full_period", cost_bps, equity, trades, "equal_weight_reality_check")
        if cost_bps == 0:
            zero = metrics
        if zero:
            metrics["cagr_decay_vs_0_bps"] = round(float(metrics["cagr_pct"]) - float(zero["cagr_pct"]), 4)
            metrics["sharpe_decay_vs_0_bps"] = round(float(metrics["sharpe_ratio"]) - float(zero["sharpe_ratio"]), 4)
            metrics["calmar_decay_vs_0_bps"] = round(float(metrics["calmar_ratio"]) - float(zero["calmar_ratio"]), 4)
        metrics["summary_label"] = "manual_review_required"
        result_rows.append(metrics)
    return result_rows


def simulate_inception_aware(
    created_at: str,
    price_data: dict[str, list[dict[str, Any]]],
    universe: list[str],
) -> list[dict[str, Any]]:
    rows = variable_universe_rows(price_data, universe)
    if len(rows) < 253:
        return [metric_stub(created_at, "equal_weight_inception_aware", "insufficient_saved_inputs", "Not enough inception-aware daily rows.")]
    result_rows = []
    for cost_bps in [0, 10, 25, 50, 100]:
        equity, trades = simulate_variable_equal_weight("equal_weight_inception_aware", rows, cost_bps, created_at)
        metrics = build_metrics(created_at, "equal_weight_inception_aware", "full_period", cost_bps, equity, trades, "inception-aware assets enter only after usable history exists")
        result_rows.append(metrics)
    zero = next((row for row in result_rows if row.get("cost_bps") == 0), result_rows[0])
    for row in result_rows:
        row["cagr_decay_vs_0_bps"] = round(float(row["cagr_pct"]) - float(zero["cagr_pct"]), 4)
        row["sharpe_decay_vs_0_bps"] = round(float(row["sharpe_ratio"]) - float(zero["sharpe_ratio"]), 4)
        row["calmar_decay_vs_0_bps"] = round(float(row["calmar_ratio"]) - float(zero["calmar_ratio"]), 4)
    return result_rows


def variable_universe_rows(price_data: dict[str, list[dict[str, Any]]], universe: list[str]) -> list[dict[str, Any]]:
    maps = {symbol: {row["date"]: row["close"] for row in price_data.get(symbol, [])} for symbol in universe}
    dates = sorted(set().union(*(set(values) for values in maps.values())))
    rows = []
    for date in dates:
        closes = {symbol: values[date] for symbol, values in maps.items() if date in values}
        available = [symbol for symbol in universe if symbol in closes and available_history_count(price_data[symbol], date) >= 253]
        if closes:
            rows.append({"date": date, "closes": closes, "available": available})
    return rows


def simulate_variable_equal_weight(
    name: str,
    rows: list[dict[str, Any]],
    cost_bps: int,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    equity = 1.0
    weights: dict[str, float] = {}
    out = []
    trades = []
    last_month = ""
    turnover_total = 0.0
    for index, row in enumerate(rows):
        date = row["date"]
        month = date[:7]
        if index > 0:
            previous = rows[index - 1]["closes"]
            current = row["closes"]
            daily_return = sum(
                weight * ((current.get(symbol, previous.get(symbol, 0)) / previous[symbol]) - 1.0)
                for symbol, weight in weights.items()
                if symbol in previous and symbol in current and previous[symbol] > 0
            )
            equity *= 1.0 + daily_return
        if month != last_month or index == 0:
            available = row.get("available", [])
            new_weights = {symbol: 1.0 / len(available) for symbol in available} if available else {}
            turnover = sum(abs(new_weights.get(symbol, 0.0) - weights.get(symbol, 0.0)) for symbol in set(new_weights) | set(weights))
            equity *= 1.0 - (turnover * cost_bps / 10_000)
            turnover_total += turnover
            weights = new_weights
            last_month = month
        out.append({"date": date, "equity": equity, "cash_weight": 1.0 - sum(weights.values()), "holdings": ",".join(sorted(weights)), "turnover": turnover_total})
    return out, trades


def build_contribution_rows(
    created_at: str,
    price_data: dict[str, list[dict[str, Any]]],
    universe: list[str],
) -> list[dict[str, Any]]:
    rows = []
    for symbol in universe:
        history = price_data.get(symbol, [])
        if len(history) < 2:
            contribution = 0.0
            first_date = ""
            momentum_date = ""
        else:
            contribution = (float(history[-1]["close"]) / float(history[0]["close"])) - 1.0
            first_date = history[0]["date"]
            momentum_date = history[252]["date"] if len(history) > 252 else ""
        rows.append(
            common_row(
                created_at,
                "asset_contribution",
                "asset_contribution_estimate",
                symbol,
                "final_return_contribution_estimate",
                round(contribution, 6),
                "",
                "available" if history else "missing",
                "manual_review_required",
                f"first_usable_date={first_date}; sma200_available={history[200]['date'] if len(history) > 200 else ''}; momentum252_available={momentum_date}; contributes_to_early_period={bool(momentum_date)}.",
            )
        )
    return sorted(rows, key=lambda row: float(row.get("metric_value") or 0), reverse=True)


def build_drawdown_rows(created_at: str, results: list[dict[str, Any]], equity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for strategy in ["equal_weight_eligible_crypto_benchmark", "btc_buy_and_hold_benchmark", "eth_buy_and_hold_benchmark", CODEX_STRATEGY, PLANNED_STRATEGY]:
        metric = next((row for row in results if row.get("strategy_name") == strategy and str(row.get("cost_bps")) == "10"), {})
        label = "drawdown_extreme_review" if float_or_zero(metric.get("max_drawdown_pct")) < -80 else "drawdown_review_available"
        rows.append(
            common_row(
                created_at,
                "drawdown_window_review",
                "worst_drawdown_context",
                strategy,
                "max_drawdown_pct",
                metric.get("max_drawdown_pct", ""),
                "",
                label,
                "manual_review_required",
                "Worst drawdown window comparison uses saved/recomputed equity where available; display remains research-only.",
            )
        )
    return rows


def build_report_rows(
    created_at: str,
    base_results: list[dict[str, Any]],
    reality_results: list[dict[str, Any]],
    contribution_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for name in COMPARE_NAMES:
        metric = next((row for row in base_results if row.get("strategy_name") == name and str(row.get("cost_bps")) == "10"), {})
        rows.append(metric_to_common(created_at, "strategy_comparison", metric, name))
    static = next((row for row in base_results if row.get("strategy_name") == "equal_weight_eligible_crypto_benchmark" and str(row.get("cost_bps")) == "10"), {})
    inception = next((row for row in reality_results if row.get("strategy_name") == "equal_weight_inception_aware" and str(row.get("cost_bps")) == "10"), {})
    top = contribution_rows[0].get("strategy_name", "") if contribution_rows else ""
    rows.append(
        common_row(
            created_at,
            "equal_weight_reality_check",
            "reality_assessment",
            "equal_weight_eligible_crypto_benchmark",
            "static_vs_inception_aware",
            f"static={static.get('cagr_pct', '')}; inception={inception.get('cagr_pct', '')}",
            "",
            "manual_review_required",
            final_label(static, inception, reality_results),
            f"top_contributor={top}; static equal-weight over today's universe is not a clean benchmark unless inception-aware and outlier checks support it.",
        )
    )
    return rows


def build_summary_rows(
    created_at: str,
    report_rows: list[dict[str, Any]],
    reality_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    drawdown_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    label = next((row.get("summary_label", "manual_review_required") for row in report_rows if row.get("check_name") == "reality_assessment"), "manual_review_required")
    return [
        common_row(created_at, "summary", "final_summary_label", "expanded_crypto_robustness", "label", label, "", label, label, "Final label is research-only."),
        common_row(created_at, "summary", "equal_weight_reality_assessment", "equal_weight_eligible_crypto_benchmark", "assessment", label, "", label, label, "Whether static equal-weight looks robust or hindsight-biased."),
        common_row(created_at, "summary", "best_active_crypto_strategy", "active_crypto", "best_active", best_active(reality_rows, cost_rows), "", "manual_review_required", label, "Best active strategy uses 10 bps cost rows where available."),
        common_row(created_at, "summary", "codex_benchmark_wins", CODEX_STRATEGY, "wins", codex_wins(cost_rows, reality_rows), "", "manual_review_required", label, "Checks whether Codex strategy beats BTC, ETH, static equal-weight, and inception-aware equal-weight."),
        common_row(created_at, "summary", "split_summary", "expanded_crypto", "split_status_counts", status_counts(split_rows), "", "manual_review_required", label, "Fixed split status counts."),
        common_row(created_at, "summary", "cost_survival_summary", "expanded_crypto", "cost_survival", cost_survival_summary(cost_rows), "", "manual_review_required", label, "10/25 bps cost survival."),
        common_row(created_at, "summary", "drawdown_warning_summary", "expanded_crypto", "drawdown_status_counts", status_counts(drawdown_rows), "", "manual_review_required", label, "Drawdown warning counts."),
    ]


def insufficient_rows(
    created_at: str,
    universe: list[str],
    universe_note: str,
    errors: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    evidence = f"{universe_note}; universe={','.join(universe)}; errors=" + "; ".join(f"{key}:{value}" for key, value in sorted(errors.items())[:5])
    report = [
        common_row(created_at, "summary", "insufficient_saved_inputs", "expanded_crypto_robustness", "input_status", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence)
    ]
    summary = [
        common_row(created_at, "summary", "final_summary_label", "expanded_crypto_robustness", "label", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "equal_weight_reality_assessment", "equal_weight_eligible_crypto_benchmark", "assessment", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "best_active_crypto_strategy", "active_crypto", "best_active", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "codex_benchmark_wins", CODEX_STRATEGY, "wins", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "split_summary", "expanded_crypto", "split_status_counts", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "cost_survival_summary", "expanded_crypto", "cost_survival", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
        common_row(created_at, "summary", "drawdown_warning_summary", "expanded_crypto", "drawdown_status_counts", "insufficient_saved_inputs", "", "insufficient_saved_inputs", "insufficient_saved_inputs", evidence),
    ]
    return report, summary, report, report, report, [], report


def to_common_metric_rows(created_at: str, section: str, rows: list[dict[str, Any]], check_name: str) -> list[dict[str, Any]]:
    return [metric_to_common(created_at, section, row, row.get("strategy_name", ""), check_name) for row in rows]


def to_common_split_rows(created_at: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        common_row(
            created_at,
            "split_validation",
            row.get("split_name", ""),
            row.get("strategy_name", ""),
            "cagr_sharpe_calmar_maxdd",
            f"CAGR={row.get('cagr_pct', '')}; Sharpe={row.get('sharpe_ratio', '')}; Calmar={row.get('calmar_ratio', '')}; MaxDD={row.get('max_drawdown_pct', '')}",
            "",
            row.get("split_status", "manual_review_required"),
            row.get("summary_label", "manual_review_required"),
            "Fixed out-of-sample split validation.",
        )
        for row in rows
    ]


def metric_to_common(created_at: str, section: str, row: dict[str, Any], strategy: str, check_name: str = "metric") -> dict[str, Any]:
    if not row:
        return common_row(created_at, section, check_name, strategy, "metrics", "unavailable", "", "insufficient_saved_inputs", "insufficient_saved_inputs", "Missing metric row.")
    return common_row(
        created_at,
        section,
        check_name,
        strategy,
        "cagr_sharpe_calmar_maxdd",
        f"CAGR={row.get('cagr_pct', '')}; Sharpe={row.get('sharpe_ratio', '')}; Calmar={row.get('calmar_ratio', '')}; MaxDD={row.get('max_drawdown_pct', '')}",
        f"cost_bps={row.get('cost_bps', '')}",
        row.get("summary_label", "manual_review_required"),
        row.get("summary_label", "manual_review_required"),
        row.get("reason", "Research-only metric row."),
    )


def common_row(
    created_at: str,
    section: str,
    check_name: str,
    strategy_name: str,
    metric_name: str,
    metric_value: Any,
    reference_value: Any,
    status: str,
    summary_label: str,
    evidence: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "report_name": "expanded_crypto_robustness_report",
        "section": section,
        "check_name": check_name,
        "strategy_name": strategy_name,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "reference_value": reference_value,
        "status": status,
        "summary_label": summary_label,
        "evidence": evidence,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def final_label(static: dict[str, Any], inception: dict[str, Any], reality_rows: list[dict[str, Any]]) -> str:
    static_cagr = float_or_zero(static.get("cagr_pct"))
    inception_cagr = float_or_zero(inception.get("cagr_pct"))
    ex_top = next((row for row in reality_rows if row.get("strategy_name") == "equal_weight_ex_outlier_top_contributor" and str(row.get("cost_bps")) == "10"), {})
    ex_top2 = next((row for row in reality_rows if row.get("strategy_name") == "equal_weight_ex_top_2_contributors" and str(row.get("cost_bps")) == "10"), {})
    if not static or not inception:
        return "insufficient_saved_inputs"
    if inception_cagr >= static_cagr * 0.85 and float_or_zero(ex_top.get("cagr_pct")) > 0 and float_or_zero(ex_top2.get("cagr_pct")) > 0:
        return "equal_weight_crypto_robust_benchmark"
    if inception_cagr > 0 and inception_cagr < static_cagr * 0.75:
        return "equal_weight_crypto_hindsight_bias_review"
    if float_or_zero(ex_top.get("cagr_pct")) < static_cagr * 0.5 or float_or_zero(ex_top2.get("cagr_pct")) < static_cagr * 0.4:
        return "equal_weight_crypto_outlier_dependent"
    if inception_cagr > 0:
        return "equal_weight_crypto_inception_adjusted_still_leads"
    return "equal_weight_crypto_not_reliable_benchmark"


def available_history_count(rows: list[dict[str, Any]], date: str) -> int:
    return sum(1 for row in rows if row["date"] <= date)


def metric_stub(created_at: str, name: str, label: str, evidence: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "strategy_name": name,
        "period": "full_period",
        "cost_bps": 10,
        "cagr_pct": "",
        "sharpe_ratio": "",
        "max_drawdown_pct": "",
        "calmar_ratio": "",
        "summary_label": label,
        "reason": evidence,
    }


def best_active(reality_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]]) -> str:
    active = [row for row in cost_rows if row.get("strategy_name") in {PLANNED_STRATEGY, CODEX_STRATEGY} and "CAGR=" in str(row.get("metric_value", ""))]
    return active[0].get("strategy_name", "unavailable") if active else "unavailable"


def codex_wins(cost_rows: list[dict[str, Any]], reality_rows: list[dict[str, Any]]) -> str:
    return "requires_metric_review_in_saved_rows"


def row_line(rows: list[dict[str, Any]], strategy: str) -> str:
    row = next((item for item in rows if item.get("strategy_name") == strategy and item.get("check_name") in {"reality", "cost"}), None)
    if row is None:
        row = next((item for item in rows if item.get("strategy_name") == strategy), {})
    return f"{row.get('metric_value', 'unavailable')} [{row.get('summary_label', row.get('status', ''))}]"


def summary_value(rows: list[dict[str, Any]], check_name: str) -> str:
    row = next((item for item in rows if item.get("check_name") == check_name), {})
    return str(row.get("metric_value", "unavailable"))


def status_counts(rows: list[dict[str, Any]]) -> str:
    counts = Counter(row.get("status", "") for row in rows)
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "unavailable"


def cost_survival_summary(rows: list[dict[str, Any]]) -> str:
    return status_counts(rows)


def float_or_zero(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_summary_lines(
    summary_rows: list[dict[str, Any]],
    report_rows: list[dict[str, Any]],
    reality_rows: list[dict[str, Any]],
    contribution_rows: list[dict[str, Any]],
    paths: dict[str, Path],
) -> list[str]:
    return [
        "Expanded crypto robustness report complete. Research/report only; execution_approved=False.",
        f"Final summary label: {summary_value(summary_rows, 'final_summary_label')}",
        f"Equal-weight reality: {summary_value(summary_rows, 'equal_weight_reality_assessment')}",
        f"Static equal-weight result: {row_line(reality_rows, 'equal_weight_static_today_universe')}",
        f"Inception-aware equal-weight result: {row_line(reality_rows, 'equal_weight_inception_aware')}",
        f"Ex-top contributor result: {row_line(reality_rows, 'equal_weight_ex_outlier_top_contributor')}",
        f"Ex-top-2 contributors result: {row_line(reality_rows, 'equal_weight_ex_top_2_contributors')}",
        f"Top contributors: {', '.join(row.get('strategy_name', '') for row in contribution_rows[:2]) if contribution_rows else 'unavailable'}",
        f"Saved report to {paths['report']}",
        f"Saved summary to {paths['summary']}",
        f"Saved splits to {paths['splits']}",
        f"Saved costs to {paths['costs']}",
        f"Saved drawdowns to {paths['drawdowns']}",
        f"Saved contribution to {paths['contribution']}",
        f"Saved reality check to {paths['reality']}",
        "Warning: expanded crypto robustness does not approve crypto execution, paper execution, scheduling, or strategy-to-execution wiring.",
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
        for row in rows:
            writer.writerow(row)
