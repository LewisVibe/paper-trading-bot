"""Saved-output-only crypto containment review for the multi-sleeve lead."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.research import multi_sleeve_portfolio_backtest as backtest


MISSING = "missing_saved_output"

SELECTED_LEAD = "higher_growth_70_20_5_5"
PREVIOUS_BASELINE = "current_75_15_5_5"
CRYPTO_SLEEVE = "crypto_btc_eth_research_sleeve"
BTC_SLEEVE = "btc_trend_vol_gate_research_sleeve"
ETH_SLEEVE = "eth_trend_research_sleeve"
LTC_STATE = "ltc_paused_not_active"

STATUS_ACCEPTABLE = "crypto_containment_5pct_acceptable_research_only"
STATUS_VOL_SENSITIVE = "crypto_containment_5pct_promising_but_vol_sensitive"
STATUS_REDUCE_OR_PAUSE = "crypto_containment_reduce_or_pause_manual_review"
STATUS_BLOCKED = "crypto_containment_blocked_missing_saved_streams"

NEXT_MANUAL_REVIEW = "manual_review_crypto_containment_before_further_candidate_label_change"
NEXT_MISSING = "refresh_saved_crypto_return_streams_before_containment_review"
NEXT_REDUCE_OR_PAUSE = "manual_review_reduce_or_pause_crypto_before_candidate_label_change"

INPUT_FILES = {
    "crypto_stream": Path("data/crypto_return_streams.csv"),
    "crypto_metrics": Path("data/crypto_return_stream_metrics.csv"),
    "crypto_review": Path("data/multi_sleeve_crypto_review.csv"),
    "weight_sensitivity": Path("data/multi_sleeve_weight_sensitivity.csv"),
    "lead_state": Path("data/multi_sleeve_lead_state.csv"),
    "lead_state_summary": Path("data/multi_sleeve_lead_state_summary.csv"),
    "high_growth_drawdown": Path("data/multi_sleeve_high_growth_drawdown_decomposition.csv"),
    "high_growth_drawdown_summary": Path("data/multi_sleeve_high_growth_drawdown_summary.csv"),
    "portfolio_backtest": Path("data/multi_sleeve_portfolio_backtest.csv"),
}

OUTPUT_FILES = {
    "review": Path("data/multi_sleeve_crypto_containment_review.csv"),
    "summary": Path("data/multi_sleeve_crypto_containment_summary.csv"),
    "drawdowns": Path("data/multi_sleeve_crypto_containment_drawdowns.csv"),
    "blockers": Path("data/multi_sleeve_crypto_containment_blockers.csv"),
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
    "yfinance_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]

REVIEW_COLUMNS = [
    "created_at",
    "review_name",
    "selected_lead_candidate",
    "previous_research_baseline",
    "lead_state_status",
    "crypto_sleeve_name",
    "crypto_weight_in_selected_lead",
    "ltc_state",
    "selected_lead_CAGR",
    "selected_lead_Sharpe",
    "selected_lead_MaxDD",
    "selected_lead_Calmar",
    "combined_crypto_CAGR",
    "combined_crypto_Sharpe",
    "combined_crypto_MaxDD",
    "combined_crypto_Calmar",
    "btc_CAGR",
    "btc_Sharpe",
    "btc_MaxDD",
    "btc_Calmar",
    "eth_CAGR",
    "eth_Sharpe",
    "eth_MaxDD",
    "eth_Calmar",
    "crypto_warning_status",
    "crypto_containment_status",
    "crypto_drawdown_contribution_status",
    "crypto_weight_sensitivity_status",
    "required_next_step",
    *SAFETY_COLUMNS,
]

DRAWDOWN_COLUMNS = [
    "created_at",
    "row_type",
    "sleeve_name",
    "period_start",
    "period_trough",
    "selected_lead_MaxDD",
    "crypto_weight",
    "crypto_period_return",
    "crypto_weighted_contribution",
    "total_period_return",
    "crypto_share_of_period_loss",
    "worst_drawdown_start",
    "worst_drawdown_trough",
    "max_drawdown",
    "recovery_date",
    "recovery_rows",
    "drawdown_status",
    *SAFETY_COLUMNS,
]

SUMMARY_COLUMNS = ["created_at", "summary_name", "summary_value", "details", *SAFETY_COLUMNS]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "blocker_status",
    "blocker_severity",
    "blocker_detail",
    "required_next_step",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
]


@dataclass
class MultiSleeveCryptoContainmentResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    drawdown_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_multi_sleeve_crypto_containment_review(root_dir: Path | str = ".") -> MultiSleeveCryptoContainmentResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    stream_rows = backtest.normalize_crypto_stream_rows(inputs["crypto_stream"])
    by_candidate = backtest.stream_returns_by_candidate(stream_rows)
    missing = missing_inputs(inputs, by_candidate)
    drawdown_rows = build_drawdown_rows(created_at, inputs, by_candidate)
    final_status = final_containment_status(inputs, drawdown_rows, missing)
    review_rows = [build_review_row(created_at, inputs, drawdown_rows, final_status, missing)]
    summary_rows = build_summary_rows(created_at, review_rows[0], drawdown_rows, inputs, final_status, missing)
    blocker_rows = build_blocker_rows(created_at, review_rows[0], drawdown_rows, inputs, final_status, missing)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["drawdowns"], DRAWDOWN_COLUMNS, drawdown_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return MultiSleeveCryptoContainmentResult(
        output_paths=output_paths,
        review_rows=review_rows,
        summary_rows=summary_rows,
        drawdown_rows=drawdown_rows,
        blocker_rows=blocker_rows,
        summary_lines=summary_lines(summary_rows, output_paths["review"]),
    )


def show_multi_sleeve_crypto_containment_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    path = root / OUTPUT_FILES["summary"]
    if not path.exists():
        return 1, [
            "Multi-sleeve crypto containment review is missing.",
            "Run `python bot.py --multi-sleeve-crypto-containment-review` first.",
            "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
        ]
    summary = summary_map(read_csv_rows(path))
    return 0, [
        "Multi-sleeve crypto containment review. Saved-output-only research; no execution path.",
        f"final crypto containment status: {summary.get('final_crypto_containment_status', MISSING)}",
        f"selected lead candidate: {summary.get('selected_lead_candidate', MISSING)}",
        f"crypto weight: {summary.get('crypto_weight', MISSING)}",
        f"combined crypto sleeve metrics: {summary.get('combined_crypto_sleeve_metrics', MISSING)}",
        f"crypto contribution during lead worst drawdown: {summary.get('crypto_contribution_during_lead_worst_drawdown', MISSING)}",
        f"no-crypto vs higher-crypto sensitivity: {summary.get('no_crypto_vs_higher_crypto_sensitivity', MISSING)}",
        f"standalone crypto drawdown summary: {summary.get('standalone_crypto_drawdown_summary', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def missing_inputs(inputs: dict[str, list[dict[str, str]]], by_candidate: dict[str, dict[str, float]]) -> list[str]:
    missing = []
    if CRYPTO_SLEEVE not in by_candidate:
        missing.append("crypto_btc_eth_saved_return_stream")
    if not inputs["crypto_metrics"]:
        missing.append("crypto_return_stream_metrics")
    if not selected_lead_row(inputs["weight_sensitivity"]):
        missing.append("selected_lead_weight_sensitivity_row")
    return missing


def build_review_row(
    created_at: str,
    inputs: dict[str, list[dict[str, str]]],
    drawdown_rows: list[dict[str, Any]],
    final_status: str,
    missing: list[str],
) -> dict[str, Any]:
    lead = lead_metrics(inputs)
    combined = metrics_row(inputs["crypto_metrics"], CRYPTO_SLEEVE)
    btc = metrics_row(inputs["crypto_metrics"], BTC_SLEEVE)
    eth = metrics_row(inputs["crypto_metrics"], ETH_SLEEVE)
    contribution = contribution_row(drawdown_rows)
    return {
        "created_at": created_at,
        "review_name": "multi_sleeve_crypto_containment_review",
        "selected_lead_candidate": lead.get("candidate_name", SELECTED_LEAD),
        "previous_research_baseline": PREVIOUS_BASELINE,
        "lead_state_status": lead.get("lead_state_status", MISSING),
        "crypto_sleeve_name": CRYPTO_SLEEVE,
        "crypto_weight_in_selected_lead": lead.get("crypto_weight", "5"),
        "ltc_state": LTC_STATE,
        "selected_lead_CAGR": lead.get("CAGR", MISSING),
        "selected_lead_Sharpe": lead.get("Sharpe", MISSING),
        "selected_lead_MaxDD": lead.get("MaxDD", MISSING),
        "selected_lead_Calmar": lead.get("Calmar", MISSING),
        "combined_crypto_CAGR": metric_value(combined, "CAGR"),
        "combined_crypto_Sharpe": metric_value(combined, "Sharpe"),
        "combined_crypto_MaxDD": metric_value(combined, "MaxDD"),
        "combined_crypto_Calmar": metric_value(combined, "Calmar"),
        "btc_CAGR": metric_value(btc, "CAGR"),
        "btc_Sharpe": metric_value(btc, "Sharpe"),
        "btc_MaxDD": metric_value(btc, "MaxDD"),
        "btc_Calmar": metric_value(btc, "Calmar"),
        "eth_CAGR": metric_value(eth, "CAGR"),
        "eth_Sharpe": metric_value(eth, "Sharpe"),
        "eth_MaxDD": metric_value(eth, "MaxDD"),
        "eth_Calmar": metric_value(eth, "Calmar"),
        "crypto_warning_status": crypto_warning_status(combined, inputs),
        "crypto_containment_status": final_status,
        "crypto_drawdown_contribution_status": contribution.get("drawdown_status", "missing_drawdown_contribution"),
        "crypto_weight_sensitivity_status": crypto_weight_sensitivity_status(inputs),
        "required_next_step": next_step_for(final_status, missing),
        **safety_flags(),
    }


def build_drawdown_rows(
    created_at: str,
    inputs: dict[str, list[dict[str, str]]],
    by_candidate: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [lead_period_contribution_row(created_at, inputs)]
    for sleeve in [CRYPTO_SLEEVE, BTC_SLEEVE, ETH_SLEEVE]:
        returns_by_date = by_candidate.get(sleeve, {})
        if returns_by_date:
            dates = sorted(returns_by_date)
            returns = [returns_by_date[day] for day in dates]
            rows.append(standalone_drawdown_row(created_at, sleeve, dates, returns))
        else:
            rows.append(blocked_standalone_drawdown_row(created_at, sleeve))
    return rows


def lead_period_contribution_row(created_at: str, inputs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    row = next(
        (item for item in inputs["high_growth_drawdown"] if item.get("allocation_name") == SELECTED_LEAD and item.get("row_type") == "period_contribution"),
        {},
    )
    crypto_weighted = row.get("crypto_weighted_contribution", MISSING)
    total_period = row.get("total_period_return", MISSING)
    share = period_loss_share(crypto_weighted, total_period)
    return {
        "created_at": created_at,
        "row_type": "selected_lead_worst_period_contribution",
        "sleeve_name": CRYPTO_SLEEVE,
        "period_start": row.get("period_start", MISSING),
        "period_trough": row.get("period_trough", MISSING),
        "selected_lead_MaxDD": selected_lead_row(inputs["weight_sensitivity"]).get("MaxDD", MISSING),
        "crypto_weight": row.get("crypto_weight", "5"),
        "crypto_period_return": row.get("crypto_period_return", MISSING),
        "crypto_weighted_contribution": crypto_weighted,
        "total_period_return": total_period,
        "crypto_share_of_period_loss": share,
        "worst_drawdown_start": "",
        "worst_drawdown_trough": "",
        "max_drawdown": "",
        "recovery_date": "",
        "recovery_rows": "",
        "drawdown_status": contribution_status(crypto_weighted, total_period),
        **safety_flags(),
    }


def standalone_drawdown_row(created_at: str, sleeve: str, dates: list[str], returns: list[float]) -> dict[str, Any]:
    window = drawdown_window(dates, returns)
    return {
        "created_at": created_at,
        "row_type": "standalone_crypto_drawdown",
        "sleeve_name": sleeve,
        "period_start": "",
        "period_trough": "",
        "selected_lead_MaxDD": "",
        "crypto_weight": "100",
        "crypto_period_return": "",
        "crypto_weighted_contribution": "",
        "total_period_return": "",
        "crypto_share_of_period_loss": "",
        "worst_drawdown_start": window["start"],
        "worst_drawdown_trough": window["trough"],
        "max_drawdown": rounded(window["maxdd"]),
        "recovery_date": window["recovery"],
        "recovery_rows": window["recovery_rows"],
        "drawdown_status": standalone_drawdown_status(window["maxdd"]),
        **safety_flags(),
    }


def blocked_standalone_drawdown_row(created_at: str, sleeve: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "row_type": "standalone_crypto_drawdown",
        "sleeve_name": sleeve,
        "period_start": "",
        "period_trough": "",
        "selected_lead_MaxDD": "",
        "crypto_weight": "100",
        "crypto_period_return": "",
        "crypto_weighted_contribution": "",
        "total_period_return": "",
        "crypto_share_of_period_loss": "",
        "worst_drawdown_start": MISSING,
        "worst_drawdown_trough": MISSING,
        "max_drawdown": MISSING,
        "recovery_date": MISSING,
        "recovery_rows": MISSING,
        "drawdown_status": "blocked_missing_saved_streams",
        **safety_flags(),
    }


def drawdown_window(dates: list[str], returns: list[float]) -> dict[str, Any]:
    equity = 1.0
    peak = 1.0
    peak_index = 0
    curve: list[float] = []
    worst = {"start": dates[0], "trough": dates[0], "maxdd": 0.0, "trough_index": 0, "peak": 1.0}
    for index, value in enumerate(returns):
        equity *= 1.0 + value
        curve.append(equity)
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = (equity / peak - 1.0) * 100.0 if peak else 0.0
        if drawdown < worst["maxdd"]:
            worst = {
                "start": dates[peak_index],
                "trough": dates[index],
                "maxdd": drawdown,
                "trough_index": index,
                "peak": peak,
            }
    recovery = "unrecovered_or_not_available"
    recovery_rows: str | int = "unrecovered_or_not_available"
    for index in range(int(worst["trough_index"]) + 1, len(curve)):
        if curve[index] >= float(worst["peak"]):
            recovery = dates[index]
            recovery_rows = index - int(worst["trough_index"])
            break
    return {
        "start": worst["start"],
        "trough": worst["trough"],
        "maxdd": worst["maxdd"],
        "recovery": recovery,
        "recovery_rows": recovery_rows,
    }


def final_containment_status(inputs: dict[str, list[dict[str, str]]], drawdown_rows: list[dict[str, Any]], missing: list[str]) -> str:
    if missing:
        return STATUS_BLOCKED
    sensitivity = crypto_weight_sensitivity_status(inputs)
    contribution = contribution_row(drawdown_rows)
    combined = metrics_row(inputs["crypto_metrics"], CRYPTO_SLEEVE)
    maxdd = parse_float(metric_value(combined, "MaxDD"))
    if sensitivity == "crypto_weight_reduce_or_pause_manual_review" or parse_float(contribution.get("crypto_share_of_period_loss")) >= 15:
        return STATUS_REDUCE_OR_PAUSE
    if maxdd <= -50:
        return STATUS_VOL_SENSITIVE
    return STATUS_ACCEPTABLE


def crypto_weight_sensitivity_status(inputs: dict[str, list[dict[str, str]]]) -> str:
    no_crypto = candidate_row(inputs["weight_sensitivity"], "no_crypto_80_15_0_5")
    higher_crypto = candidate_row(inputs["weight_sensitivity"], "higher_crypto_73_15_7_5")
    if not no_crypto or not higher_crypto:
        return "missing_weight_sensitivity_review"
    no_crypto_return_drag = parse_float(no_crypto.get("delta_CAGR_vs_current_75_15_5_5"))
    no_crypto_drawdown_help = parse_float(no_crypto.get("delta_MaxDD_vs_current_75_15_5_5"))
    higher_crypto_return = parse_float(higher_crypto.get("delta_CAGR_vs_current_75_15_5_5"))
    higher_crypto_drawdown = parse_float(higher_crypto.get("delta_MaxDD_vs_current_75_15_5_5"))
    if no_crypto_return_drag < -0.25 and no_crypto_drawdown_help > 0 and higher_crypto_return < 0.5 and higher_crypto_drawdown < 0:
        return "crypto_5pct_cap_preferred_no_increase_research_only"
    if no_crypto_drawdown_help > 0.5:
        return "crypto_weight_reduce_or_pause_manual_review"
    return "crypto_weight_manual_review_required"


def contribution_status(crypto_weighted: Any, total_period: Any) -> str:
    share = parse_float(period_loss_share(crypto_weighted, total_period))
    if share >= 15:
        return "crypto_drawdown_contribution_too_large_manual_review"
    if share > 0:
        return "crypto_drawdown_contribution_contained_but_negative"
    return "crypto_drawdown_contribution_missing_or_neutral"


def standalone_drawdown_status(maxdd: Any) -> str:
    value = parse_float(maxdd)
    if value <= -70:
        return "standalone_crypto_extreme_drawdown_manual_review"
    if value <= -50:
        return "standalone_crypto_high_drawdown_warning"
    return "standalone_crypto_drawdown_review_required"


def build_summary_rows(
    created_at: str,
    review: dict[str, Any],
    drawdown_rows: list[dict[str, Any]],
    inputs: dict[str, list[dict[str, str]]],
    final_status: str,
    missing: list[str],
) -> list[dict[str, Any]]:
    items = [
        ("final_crypto_containment_status", final_status, "Cautious saved-output crypto containment label."),
        ("selected_lead_candidate", review.get("selected_lead_candidate", SELECTED_LEAD), "Current canonical multi-sleeve research lead."),
        ("crypto_weight", str(review.get("crypto_weight_in_selected_lead", "5")), "Crypto sleeve weight in selected lead."),
        ("combined_crypto_sleeve_metrics", format_crypto_metrics(review), "Combined BTC/ETH saved crypto sleeve metrics."),
        ("crypto_contribution_during_lead_worst_drawdown", format_contribution(contribution_row(drawdown_rows)), "Saved same-window crypto contribution during lead worst drawdown."),
        ("no_crypto_vs_higher_crypto_sensitivity", format_weight_sensitivity(inputs), "Saved nearby crypto weight sensitivity."),
        ("standalone_crypto_drawdown_summary", format_standalone_drawdowns(drawdown_rows), "Standalone crypto sleeve drawdown windows from saved streams."),
        ("missing_saved_inputs", ",".join(missing) or "none", "Missing saved inputs block review when present."),
        ("required_next_step", next_step_for(final_status, missing), "Next research step only."),
    ]
    return [{"created_at": created_at, "summary_name": name, "summary_value": value, "details": details, **safety_flags()} for name, value, details in items]


def build_blocker_rows(
    created_at: str,
    review: dict[str, Any],
    drawdown_rows: list[dict[str, Any]],
    inputs: dict[str, list[dict[str, str]]],
    final_status: str,
    missing: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if missing:
        rows.append(blocker_row(created_at, "saved_output_completeness", STATUS_BLOCKED, "high", "missing_saved_inputs=" + ",".join(missing), NEXT_MISSING))
    rows.extend(
        [
            blocker_row(created_at, "crypto_weight_cap", crypto_weight_sensitivity_status(inputs), "medium", format_weight_sensitivity(inputs), next_step_for(final_status, missing)),
            blocker_row(created_at, "crypto_worst_period_contribution", review.get("crypto_drawdown_contribution_status", MISSING), "medium", format_contribution(contribution_row(drawdown_rows)), next_step_for(final_status, missing)),
            blocker_row(created_at, "standalone_crypto_drawdown", "manual_review_required", "medium", format_standalone_drawdowns(drawdown_rows), next_step_for(final_status, missing)),
            blocker_row(created_at, "execution_boundary", "blocked_non_executable_research_only", "high", "crypto containment review is not an execution path", next_step_for(final_status, missing)),
            blocker_row(created_at, "scheduling_boundary", "blocked_no_scheduling_change", "high", "crypto containment review is not a schedule or cron change", next_step_for(final_status, missing)),
        ]
    )
    return rows


def blocker_row(created_at: str, name: str, status: str, severity: str, detail: str, next_step: str) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": name,
        "blocker_status": status,
        "blocker_severity": severity,
        "blocker_detail": detail,
        "required_next_step": next_step,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "scheduling_approved": False,
    }


def lead_metrics(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    row = selected_lead_row(inputs["weight_sensitivity"])
    summary = summary_map(inputs["lead_state_summary"])
    if row:
        lead = dict(row)
    else:
        lead = {"candidate_name": summary.get("current_research_lead_candidate", SELECTED_LEAD), "crypto_weight": "5"}
        metrics = parse_metric_bundle(summary.get("selected_candidate_metrics", ""))
        lead.update(metrics)
    lead["lead_state_status"] = summary.get("lead_state_status", MISSING)
    return lead


def selected_lead_row(rows: list[dict[str, str]]) -> dict[str, str]:
    return candidate_row(rows, SELECTED_LEAD)


def candidate_row(rows: list[dict[str, str]], candidate: str) -> dict[str, str]:
    return next((row for row in rows if row.get("candidate_name") == candidate), {})


def metrics_row(rows: list[dict[str, str]], candidate: str) -> dict[str, str]:
    return next((row for row in rows if row.get("candidate_name") == candidate or row.get("sleeve_name") == candidate), {})


def metric_value(row: dict[str, str], name: str) -> str:
    aliases = {
        "CAGR": ["CAGR", "cagr"],
        "Sharpe": ["Sharpe", "sharpe"],
        "MaxDD": ["MaxDD", "max_drawdown"],
        "Calmar": ["Calmar", "calmar"],
    }
    for key in aliases.get(name, [name]):
        if row.get(key) not in {"", None}:
            return str(row.get(key))
    return MISSING


def parse_metric_bundle(value: str) -> dict[str, str]:
    metrics: dict[str, str] = {}
    for token in value.replace(";", " ").split():
        if "=" not in token:
            continue
        key, item = token.split("=", 1)
        if key in {"CAGR", "Sharpe", "MaxDD", "Calmar"}:
            metrics[key] = item.rstrip(",;")
    return metrics


def contribution_row(drawdown_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return next((row for row in drawdown_rows if row.get("row_type") == "selected_lead_worst_period_contribution"), {})


def crypto_warning_status(combined: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> str:
    if combined.get("warning_status"):
        return combined["warning_status"]
    review = inputs["crypto_review"][0] if inputs["crypto_review"] else {}
    if review.get("review_status"):
        return review["review_status"]
    if parse_float(metric_value(combined, "MaxDD")) <= -50:
        return "crypto_high_volatility_and_drawdown_warning"
    return "crypto_warning_status_missing"


def period_loss_share(crypto_weighted: Any, total_period: Any) -> str:
    crypto = abs(parse_float(crypto_weighted))
    total = abs(parse_float(total_period))
    if total <= 0 or crypto <= 0:
        return MISSING
    return rounded((crypto / total) * 100.0)


def format_crypto_metrics(review: dict[str, Any]) -> str:
    return (
        f"{CRYPTO_SLEEVE}: CAGR={review.get('combined_crypto_CAGR')}; "
        f"Sharpe={review.get('combined_crypto_Sharpe')}; "
        f"MaxDD={review.get('combined_crypto_MaxDD')}; "
        f"Calmar={review.get('combined_crypto_Calmar')}; "
        f"BTC_MaxDD={review.get('btc_MaxDD')}; ETH_MaxDD={review.get('eth_MaxDD')}; LTC={review.get('ltc_state')}"
    )


def format_contribution(row: dict[str, Any]) -> str:
    if not row:
        return MISSING
    return (
        f"period={row.get('period_start')}->{row.get('period_trough')}; "
        f"crypto_return={row.get('crypto_period_return')}; "
        f"crypto_weighted={row.get('crypto_weighted_contribution')}; "
        f"total_period={row.get('total_period_return')}; "
        f"share_of_loss={row.get('crypto_share_of_period_loss')}; "
        f"status={row.get('drawdown_status')}"
    )


def format_weight_sensitivity(inputs: dict[str, list[dict[str, str]]]) -> str:
    no_crypto = candidate_row(inputs["weight_sensitivity"], "no_crypto_80_15_0_5")
    higher_crypto = candidate_row(inputs["weight_sensitivity"], "higher_crypto_73_15_7_5")
    if not no_crypto or not higher_crypto:
        return "missing_weight_sensitivity_review"
    return (
        "no_crypto_80_15_0_5 "
        f"delta_CAGR={no_crypto.get('delta_CAGR_vs_current_75_15_5_5')}; "
        f"delta_MaxDD={no_crypto.get('delta_MaxDD_vs_current_75_15_5_5')}; "
        "higher_crypto_73_15_7_5 "
        f"delta_CAGR={higher_crypto.get('delta_CAGR_vs_current_75_15_5_5')}; "
        f"delta_MaxDD={higher_crypto.get('delta_MaxDD_vs_current_75_15_5_5')}; "
        f"status={crypto_weight_sensitivity_status(inputs)}"
    )


def format_standalone_drawdowns(rows: list[dict[str, Any]]) -> str:
    pieces = []
    for row in rows:
        if row.get("row_type") != "standalone_crypto_drawdown":
            continue
        pieces.append(
            f"{row.get('sleeve_name')}: start={row.get('worst_drawdown_start')}; "
            f"trough={row.get('worst_drawdown_trough')}; MaxDD={row.get('max_drawdown')}; "
            f"recovery={row.get('recovery_date')}; rows={row.get('recovery_rows')}; status={row.get('drawdown_status')}"
        )
    return " | ".join(pieces) if pieces else MISSING


def next_step_for(status: str, missing: list[str]) -> str:
    if missing or status == STATUS_BLOCKED:
        return NEXT_MISSING
    if status == STATUS_REDUCE_OR_PAUSE:
        return NEXT_REDUCE_OR_PAUSE
    return NEXT_MANUAL_REVIEW


def summary_lines(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    summary = summary_map(rows)
    return [
        "Multi-sleeve crypto containment review created. Saved-output-only research; no execution path.",
        f"final crypto containment status: {summary.get('final_crypto_containment_status', MISSING)}",
        f"selected lead candidate: {summary.get('selected_lead_candidate', MISSING)}",
        f"crypto weight: {summary.get('crypto_weight', MISSING)}",
        f"combined crypto sleeve metrics: {summary.get('combined_crypto_sleeve_metrics', MISSING)}",
        f"crypto contribution during lead worst drawdown: {summary.get('crypto_contribution_during_lead_worst_drawdown', MISSING)}",
        f"no-crypto vs higher-crypto sensitivity: {summary.get('no_crypto_vs_higher_crypto_sensitivity', MISSING)}",
        f"standalone crypto drawdown summary: {summary.get('standalone_crypto_drawdown_summary', MISSING)}",
        f"required next step: {summary.get('required_next_step', MISSING)}",
        f"Saved review: {output_path}",
        "execution_approved=false; crypto_execution_approved=false; scheduling_approved=false",
    ]


def summary_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row.get("summary_name") or ""): str(row.get("summary_value") or "") for row in rows if row.get("summary_name")}


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rounded(value: Any) -> str:
    return str(round(parse_float(value), 4))


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
        "yfinance_called": False,
        "live_position_read": False,
        "sqlite_trade_log_written": False,
        "discord_alert_sent": False,
        "telegram_alert_sent": False,
        "execution_approved": False,
        "paper_execution_approved": False,
        "crypto_execution_approved": False,
        "live_trading_approved": False,
        "scheduling_approved": False,
        "shorting_approved": False,
        "leverage_approved": False,
        "margin_approved": False,
    }
