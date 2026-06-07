"""Saved-data-only defensive candidate comparison report.

This report compares ETF rotation, volatility-managed ETF momentum, and adaptive
momentum as defensive portfolio candidates. It reads existing CSV reports only
and does not call market data, Alpaca, Discord, SQLite, or execution helpers.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFENSIVE_CANDIDATES = [
    "monthly_etf_momentum_rotation",
    "volatility_managed_dual_momentum_etf",
    "adaptive_risk_on_off_momentum",
]

DEFENSIVE_CANDIDATE_COMPARISON_COLUMNS = [
    "created_at",
    "strategy_name",
    "strategy_family",
    "ticker_or_portfolio",
    "out_of_sample_cagr_pct",
    "out_of_sample_sharpe",
    "out_of_sample_calmar",
    "out_of_sample_max_drawdown_pct",
    "robustness_label",
    "defensive_score",
    "defensive_status",
    "trade_count",
    "relative_turnover_note",
    "complexity_note",
    "fixed_split_win_count",
    "fixed_split_loss_count",
    "split_comparison_summary",
    "metric_rank",
    "policy_rank",
    "comparison_rank",
    "comparison_status",
    "comparison_reason",
    "next_research_step",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class DefensiveCandidateComparisonResult:
    output_path: Path
    rows: list[dict[str, Any]]
    warnings: list[str]
    summary_lines: list[str]


def generate_defensive_candidate_comparison(
    data_dir: Path | str = "data",
    output_filename: str = "defensive_candidate_comparison.csv",
) -> DefensiveCandidateComparisonResult:
    data_path = Path(data_dir)
    warnings: list[str] = []
    walk_forward_path = data_path / "walk_forward_report.csv"
    defensive_path = data_path / "defensive_strategy_report.csv"
    promotion_path = data_path / "strategy_promotion_report.csv"
    vol_results_path = data_path / "vol_managed_etf_results.csv"
    vol_robustness_path = data_path / "vol_managed_etf_robustness_report.csv"

    if not walk_forward_path.exists():
        raise RuntimeError(f"Missing required walk-forward report: {walk_forward_path}")
    if not defensive_path.exists():
        raise RuntimeError(f"Missing required defensive strategy report: {defensive_path}")

    walk_forward_rows = read_csv_rows(walk_forward_path)
    defensive_rows = read_csv_rows(defensive_path)
    promotion_rows = read_csv_rows(promotion_path) if promotion_path.exists() else []
    vol_result_rows = read_csv_rows(vol_results_path) if vol_results_path.exists() else []
    vol_robustness_rows = read_csv_rows(vol_robustness_path) if vol_robustness_path.exists() else []
    if not walk_forward_rows:
        raise RuntimeError(f"No usable rows in required walk-forward report: {walk_forward_path}")
    if not defensive_rows:
        raise RuntimeError(f"No usable rows in required defensive strategy report: {defensive_path}")
    if not promotion_rows:
        warnings.append(f"Missing optional promotion report: {promotion_path}")

    rows = build_defensive_candidate_comparison_rows(
        walk_forward_rows,
        defensive_rows,
        promotion_rows,
        vol_result_rows,
        vol_robustness_rows,
    )
    output_path = data_path / output_filename
    write_defensive_candidate_comparison(output_path, rows)
    return DefensiveCandidateComparisonResult(
        output_path=output_path,
        rows=rows,
        warnings=warnings,
        summary_lines=build_defensive_candidate_comparison_summary(rows),
    )


def build_defensive_candidate_comparison_rows(
    walk_forward_rows: list[dict[str, str]],
    defensive_rows: list[dict[str, str]],
    promotion_rows: list[dict[str, str]] | None = None,
    vol_result_rows: list[dict[str, str]] | None = None,
    vol_robustness_rows: list[dict[str, str]] | None = None,
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    walk_forward_by_name = portfolio_rows_by_strategy(walk_forward_rows)
    defensive_by_name = portfolio_rows_by_strategy(defensive_rows)
    promotion_by_name = portfolio_rows_by_strategy(promotion_rows or [])
    vol_result_by_name = portfolio_result_rows_by_strategy(vol_result_rows or [])
    vol_robustness_by_name = robustness_rows_by_strategy(vol_robustness_rows or [])

    rows = [
        build_candidate_row(
            timestamp,
            strategy_name,
            candidate_walk_forward_row(
                strategy_name,
                walk_forward_by_name.get(strategy_name, {}),
                vol_result_by_name.get(strategy_name, {}),
            ),
            defensive_by_name.get(strategy_name, {}),
            promotion_by_name.get(strategy_name, {}),
            vol_robustness_by_name.get(strategy_name, []),
        )
        for strategy_name in DEFENSIVE_CANDIDATES
    ]
    apply_candidate_comparison(rows)
    return sorted(
        rows,
        key=lambda row: (
            comparison_status_sort_order(row["comparison_status"]),
            number_or_large(row["policy_rank"]),
            row["strategy_name"],
        ),
    )


def build_candidate_row(
    created_at: str,
    strategy_name: str,
    walk_forward_row: dict[str, str],
    defensive_row: dict[str, str],
    promotion_row: dict[str, str],
    robustness_rows: list[dict[str, str]],
) -> dict[str, Any]:
    split_summary = split_comparison_summary(robustness_rows)
    return {
        "created_at": created_at,
        "strategy_name": strategy_name,
        "strategy_family": defensive_row.get("strategy_family") or strategy_family(strategy_name),
        "ticker_or_portfolio": "portfolio",
        "out_of_sample_cagr_pct": number_or_blank(walk_forward_row.get("out_of_sample_cagr_pct", "")),
        "out_of_sample_sharpe": number_or_blank(walk_forward_row.get("out_of_sample_sharpe", "")),
        "out_of_sample_calmar": number_or_blank(walk_forward_row.get("out_of_sample_calmar", "")),
        "out_of_sample_max_drawdown_pct": number_or_blank(walk_forward_row.get("out_of_sample_max_drawdown_pct", "")),
        "robustness_label": walk_forward_row.get("robustness_label", "insufficient_period_data") or "insufficient_period_data",
        "defensive_score": candidate_defensive_score(strategy_name, defensive_row, split_summary),
        "defensive_status": candidate_defensive_status(strategy_name, defensive_row, split_summary),
        "trade_count": number_or_blank(promotion_row.get("trade_count", "")),
        "relative_turnover_note": "",
        "complexity_note": complexity_note(strategy_name),
        "fixed_split_win_count": split_summary["wins"],
        "fixed_split_loss_count": split_summary["losses"],
        "split_comparison_summary": split_summary["summary"],
        "metric_rank": "",
        "policy_rank": "",
        "comparison_rank": "",
        "comparison_status": "",
        "comparison_reason": "",
        "next_research_step": "",
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def apply_candidate_comparison(rows: list[dict[str, Any]]) -> None:
    valid_rows = [row for row in rows if has_required_comparison_data(row)]
    etf = next((row for row in rows if row["strategy_name"] == "monthly_etf_momentum_rotation"), {})
    vol = next((row for row in rows if row["strategy_name"] == "volatility_managed_dual_momentum_etf"), {})
    adaptive = next((row for row in rows if row["strategy_name"] == "adaptive_risk_on_off_momentum"), {})
    vol_beats_all = bool(vol) and vol_managed_beats_all_splits(vol)

    for row in rows:
        row["relative_turnover_note"] = relative_turnover_note(row, etf, adaptive)

    if not valid_rows:
        for row in rows:
            mark_insufficient(row)
        apply_policy_ranks(rows)
        return

    ranked = sorted(
        valid_rows,
        key=lambda row: (
            -float(row["out_of_sample_calmar"]),
            -float(row["out_of_sample_sharpe"]),
            float(row["out_of_sample_max_drawdown_pct"]),
            turnover_sort_value(row),
            row["strategy_name"],
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["metric_rank"] = rank

    for row in rows:
        if row not in valid_rows:
            mark_insufficient(row)
            continue
        if row["strategy_name"] == "monthly_etf_momentum_rotation" and (row["metric_rank"] == 1 or not vol_beats_all):
            row["comparison_status"] = "preferred_defensive_candidate"
            row["comparison_reason"] = "ETF rotation remains the preferred defensive candidate because vol-managed ETF has not beaten it across all fixed splits."
            row["next_research_step"] = "Keep as the lead defensive research candidate; continue preview and risk analysis only."
            continue
        if row["strategy_name"] == "volatility_managed_dual_momentum_etf":
            if vol_managed_beats_all_splits(row) and row["metric_rank"] == 1:
                row["comparison_status"] = "preferred_defensive_candidate"
                row["comparison_reason"] = "Vol-managed ETF leads risk-adjusted defensive metrics and beats ETF rotation across all fixed split comparisons."
                row["next_research_step"] = "Keep research-only; review turnover, drawdown periods, and preview-risk process before any execution discussion."
                continue
            if has_split_wins(row):
                row["comparison_status"] = "promising_but_split_sensitive"
                row["comparison_reason"] = (
                    f"Vol-managed ETF has strong OOS metrics and {row['split_comparison_summary']}; "
                    "keep research-only until split sensitivity is resolved."
                )
                row["next_research_step"] = "Keep as promising research; compare drawdown periods, turnover, and portfolio role against ETF rotation."
                continue
            if row.get("defensive_status") in {"defensive_candidate", "strongest_defensive_candidate"}:
                row["comparison_status"] = "secondary_defensive_candidate"
                row["comparison_reason"] = "Vol-managed ETF has defensive evidence, but does not displace ETF rotation in fixed-split comparison."
                row["next_research_step"] = "Keep secondary and require stronger fixed-split evidence before promotion."
                continue
        if row["strategy_name"] == "adaptive_risk_on_off_momentum":
            if materially_higher_turnover(row, etf):
                row["comparison_status"] = "research_only_high_turnover"
                row["comparison_reason"] = "Adaptive has usable defensive metrics, but its trade count is materially higher than ETF rotation and it trails on key defensive candidates."
                row["next_research_step"] = "Keep secondary; compare turnover and cost burden before any further research."
                continue
            if row.get("defensive_status") in {"defensive_candidate", "strongest_defensive_candidate"}:
                row["comparison_status"] = "secondary_defensive_candidate"
                row["comparison_reason"] = "Adaptive has positive defensive evidence, but does not displace ETF rotation in the direct comparison."
                row["next_research_step"] = "Keep secondary and review only after ETF rotation analysis."
                continue
        row["comparison_status"] = "not_competitive"
        row["comparison_reason"] = "Candidate does not currently lead the defensive comparison."
        row["next_research_step"] = "Keep in saved research reports; do not promote from this comparison."

    apply_policy_ranks(rows)


def apply_policy_ranks(rows: list[dict[str, Any]]) -> None:
    ranked = sorted(
        rows,
        key=lambda row: (
            comparison_status_sort_order(row["comparison_status"]),
            number_or_large(row.get("metric_rank", "")),
            row["strategy_name"],
        ),
    )
    for rank, row in enumerate(ranked, start=1):
        row["policy_rank"] = rank
        row["comparison_rank"] = rank


def mark_insufficient(row: dict[str, Any]) -> None:
    row["comparison_status"] = "insufficient_data"
    row["comparison_reason"] = "Missing walk-forward or defensive report metrics for this candidate."
    row["next_research_step"] = "Regenerate walk-forward and defensive strategy reports before comparing."


def has_required_comparison_data(row: dict[str, Any]) -> bool:
    required = [
        row.get("out_of_sample_cagr_pct"),
        row.get("out_of_sample_sharpe"),
        row.get("out_of_sample_calmar"),
        row.get("out_of_sample_max_drawdown_pct"),
        row.get("defensive_score"),
    ]
    return all(isinstance(value, (int, float)) for value in required) and row.get("defensive_status") != "insufficient_data"


def vol_managed_beats_all_splits(row: dict[str, Any]) -> bool:
    wins = row.get("fixed_split_win_count")
    losses = row.get("fixed_split_loss_count")
    return isinstance(wins, (int, float)) and isinstance(losses, (int, float)) and int(wins) >= 3 and int(losses) == 0


def has_split_wins(row: dict[str, Any]) -> bool:
    wins = row.get("fixed_split_win_count")
    return isinstance(wins, (int, float)) and int(wins) > 0


def materially_higher_turnover(row: dict[str, Any], etf_row: dict[str, Any]) -> bool:
    trade_count = row.get("trade_count")
    etf_trade_count = etf_row.get("trade_count")
    if not isinstance(trade_count, (int, float)):
        return False
    if isinstance(etf_trade_count, (int, float)) and etf_trade_count > 0:
        return float(trade_count) >= max(float(etf_trade_count) * 1.5, float(etf_trade_count) + 50)
    return float(trade_count) >= 250


def relative_turnover_note(row: dict[str, Any], etf_row: dict[str, Any], adaptive_row: dict[str, Any]) -> str:
    if row["strategy_name"] == "monthly_etf_momentum_rotation":
        adaptive_trade_count = adaptive_row.get("trade_count")
        etf_trade_count = row.get("trade_count")
        if isinstance(adaptive_trade_count, (int, float)) and isinstance(etf_trade_count, (int, float)):
            return f"Lower turnover than adaptive ({int(etf_trade_count)} vs {int(adaptive_trade_count)} trades)."
        return "Monthly rotation is the simpler comparison baseline."
    if row["strategy_name"] == "volatility_managed_dual_momentum_etf":
        if row.get("fixed_split_win_count") != "":
            return str(row.get("split_comparison_summary", "Fixed-split comparison unavailable."))
        return "Vol-managed turnover comparison unavailable."
    etf_trade_count = etf_row.get("trade_count")
    adaptive_trade_count = row.get("trade_count")
    if isinstance(adaptive_trade_count, (int, float)) and isinstance(etf_trade_count, (int, float)):
        return f"Higher turnover than ETF rotation ({int(adaptive_trade_count)} vs {int(etf_trade_count)} trades)."
    if isinstance(adaptive_trade_count, (int, float)):
        return f"Adaptive trade count is high ({int(adaptive_trade_count)} trades)."
    return "Turnover comparison unavailable."


def turnover_sort_value(row: dict[str, Any]) -> float:
    value = row.get("trade_count")
    if isinstance(value, (int, float)):
        return float(value)
    return 999999.0


def complexity_note(strategy_name: str) -> str:
    if strategy_name == "monthly_etf_momentum_rotation":
        return "Simple monthly ETF rotation with top-N selection."
    if strategy_name == "adaptive_risk_on_off_momentum":
        return "More complex risk-on/off allocation with defensive sleeve and higher turnover burden."
    if strategy_name == "volatility_managed_dual_momentum_etf":
        return "Advanced long-only ETF momentum with inverse-volatility sizing and volatility cap."
    return "Complexity not classified."


def strategy_family(strategy_name: str) -> str:
    if strategy_name == "monthly_etf_momentum_rotation":
        return "rotation"
    if strategy_name == "adaptive_risk_on_off_momentum":
        return "adaptive"
    if strategy_name == "volatility_managed_dual_momentum_etf":
        return "volatility_managed"
    return "unknown"


def portfolio_rows_by_strategy(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if str(row.get("ticker_or_portfolio", "portfolio") or "portfolio") != "portfolio":
            continue
        strategy_name = row.get("strategy_name", "")
        if strategy_name in DEFENSIVE_CANDIDATES:
            result[strategy_name] = row
    return result


def portfolio_result_rows_by_strategy(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if str(row.get("ticker_or_portfolio", "portfolio") or "portfolio") != "portfolio":
            continue
        if row.get("period") != "out_of_sample":
            continue
        strategy_name = row.get("strategy_name", "")
        if strategy_name in DEFENSIVE_CANDIDATES:
            result[strategy_name] = row
    return result


def robustness_rows_by_strategy(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        strategy_name = row.get("strategy_name", "")
        if strategy_name in DEFENSIVE_CANDIDATES:
            result.setdefault(strategy_name, []).append(row)
    return result


def candidate_walk_forward_row(strategy_name: str, walk_forward_row: dict[str, str], vol_result_row: dict[str, str]) -> dict[str, str]:
    if walk_forward_row:
        return walk_forward_row
    if strategy_name != "volatility_managed_dual_momentum_etf" or not vol_result_row:
        return walk_forward_row
    return {
        "strategy_name": strategy_name,
        "ticker_or_portfolio": "portfolio",
        "out_of_sample_cagr_pct": vol_result_row.get("cagr_pct", ""),
        "out_of_sample_sharpe": vol_result_row.get("sharpe_ratio", ""),
        "out_of_sample_calmar": vol_result_row.get("calmar_ratio", ""),
        "out_of_sample_max_drawdown_pct": vol_result_row.get("max_drawdown_pct", ""),
        "robustness_label": vol_result_row.get("research_status", "saved_result_only"),
    }


def candidate_defensive_score(strategy_name: str, defensive_row: dict[str, str], split_summary: dict[str, Any]) -> float | str:
    score = number_or_blank(defensive_row.get("defensive_score", ""))
    if score != "" or strategy_name != "volatility_managed_dual_momentum_etf":
        return score
    wins = split_summary.get("wins", "")
    losses = split_summary.get("losses", "")
    if isinstance(wins, int) and isinstance(losses, int):
        return 86.0 if wins > losses else 74.0
    return ""


def candidate_defensive_status(strategy_name: str, defensive_row: dict[str, str], split_summary: dict[str, Any]) -> str:
    status = defensive_row.get("defensive_status", "")
    if status:
        return status
    if strategy_name != "volatility_managed_dual_momentum_etf":
        return "insufficient_data"
    wins = split_summary.get("wins", "")
    losses = split_summary.get("losses", "")
    if isinstance(wins, int) and isinstance(losses, int):
        return "strongest_defensive_candidate" if wins >= 3 and losses == 0 else "defensive_candidate"
    return "insufficient_data"


def split_comparison_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    comparable = [row for row in rows if row.get("benchmark_strategy_name") == "monthly_etf_momentum_rotation"]
    if not comparable:
        return {"wins": "", "losses": "", "summary": "Fixed-split ETF rotation comparison unavailable."}
    wins = [
        row
        for row in comparable
        if number_or_blank(row.get("sharpe_gap_vs_benchmark_oos")) != ""
        and number_or_blank(row.get("calmar_gap_vs_benchmark_oos")) != ""
        and float(number_or_blank(row.get("sharpe_gap_vs_benchmark_oos"))) > 0
        and float(number_or_blank(row.get("calmar_gap_vs_benchmark_oos"))) > 0
    ]
    losses = [row for row in comparable if row not in wins]
    losing = ", ".join(str(row.get("split_name", "unknown")) for row in losses) or "none"
    return {
        "wins": len(wins),
        "losses": len(losses),
        "summary": f"wins {len(wins)} of {len(comparable)} fixed splits versus ETF rotation; losing splits: {losing}.",
    }


def write_defensive_candidate_comparison(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEFENSIVE_CANDIDATE_COMPARISON_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEFENSIVE_CANDIDATE_COMPARISON_COLUMNS})


def build_defensive_candidate_comparison_summary(rows: list[dict[str, Any]]) -> list[str]:
    preferred = first_status(rows, "preferred_defensive_candidate")
    secondary = first_status(rows, "secondary_defensive_candidate") or first_status(rows, "research_only_high_turnover")
    adaptive = next((row for row in rows if row["strategy_name"] == "adaptive_risk_on_off_momentum"), {})
    vol = next((row for row in rows if row["strategy_name"] == "volatility_managed_dual_momentum_etf"), {})
    lines = [
        "Defensive candidate comparison summary",
        "Research-only comparison. This is not execution approval.",
        f"preferred defensive candidate: {preferred.get('strategy_name', 'unavailable') if preferred else 'unavailable'}",
    ]
    if vol.get("comparison_status") == "promising_but_split_sensitive":
        lines.append("promising defensive research candidate: volatility_managed_dual_momentum_etf")
        lines.append("vol-managed split note: " + str(vol.get("split_comparison_summary", "")))
    lines.append(f"secondary defensive candidate: {secondary.get('strategy_name', 'unavailable') if secondary else 'unavailable'}")
    if adaptive.get("comparison_status") == "research_only_high_turnover":
        lines.append("adaptive turnover warning: " + str(adaptive.get("relative_turnover_note", "")))
    lines.append("Warning: research_only=True, preview_only=True, and execution_approved=False for every row.")
    return lines


def first_status(rows: list[dict[str, Any]], status: str) -> dict[str, Any] | None:
    return next((row for row in rows if row.get("comparison_status") == status), None)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        return [row for row in reader if any((value or "").strip() for value in row.values())]


def number_or_blank(value: Any) -> float | str:
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return ""


def number_or_large(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 999999.0


def comparison_status_sort_order(status: str) -> int:
    order = {
        "preferred_defensive_candidate": 0,
        "promising_but_split_sensitive": 1,
        "secondary_defensive_candidate": 2,
        "research_only_high_turnover": 3,
        "not_competitive": 4,
        "insufficient_data": 4,
    }
    return order.get(status, 99)
