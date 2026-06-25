"""Report-only F7 accounting proof checkpoint for paper-live promotion work.

This checkpoint statically inspects the saved-output multi-sleeve portfolio
research implementation and records whether the known F7 accounting boundary is
covered well enough for manual review. It does not rerun backtests, refresh
market data, call Alpaca, read positions, create order instructions, write
SQLite, send alerts, schedule anything, or approve promotion/execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MULTI_SLEEVE_BACKTEST = Path("trading_bot/research/multi_sleeve_portfolio_backtest.py")

OUTPUT_FILES = {
    "report": Path("data/paper_live_f7_accounting_proof.csv"),
    "summary": Path("data/paper_live_f7_accounting_proof_summary.csv"),
    "blockers": Path("data/paper_live_f7_accounting_proof_blockers.csv"),
    "evidence": Path("data/paper_live_f7_accounting_proof_evidence.csv"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "promotion_approved": False,
    "portfolio_backtest_promotion_evidence_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "static_analysis_only": True,
    "saved_output_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "never_schedule_order_capable_commands": True,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "check_name",
    "check_status",
    "risk_level",
    "evidence",
    "required_next_step",
    "research_only",
    "report_only",
    "static_analysis_only",
    "saved_output_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "alpaca_called",
    "live_positions_read",
    "market_data_refreshed",
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "never_schedule_order_capable_commands",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass(frozen=True)
class F7AccountingProof:
    final_status: str
    weighted_return_aggregation_status: str
    independent_starting_cash_status: str
    turnover_context_status: str
    promotion_evidence_status: str
    primary_blocker: str
    recommended_next_step: str


@dataclass
class F7AccountingProofResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_f7_accounting_proof(root_dir: Path | str = ".") -> F7AccountingProofResult:
    root = Path(root_dir)
    proof = evaluate_f7_accounting_proof(root)
    report_rows = build_report_rows(proof)
    summary_rows = build_summary_rows(proof)
    blocker_rows = build_blocker_rows(proof)
    evidence_rows = build_evidence_rows(proof)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return F7AccountingProofResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_f7_accounting_proof(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live F7 accounting proof is missing.",
            "Run `python bot.py --paper-live-f7-accounting-proof` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live F7 accounting proof saved display. Report only; no promotion or orders approved.",
        f"final_f7_accounting_status: {summary_value(rows, 'final_f7_accounting_status')}",
        f"weighted_return_aggregation_status: {summary_value(rows, 'weighted_return_aggregation_status')}",
        f"independent_starting_cash_status: {summary_value(rows, 'independent_starting_cash_status')}",
        f"turnover_context_status: {summary_value(rows, 'turnover_context_status')}",
        f"promotion_evidence_status: {summary_value(rows, 'promotion_evidence_status')}",
        f"primary_blocker: {summary_value(rows, 'primary_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; promotion_approved=false; portfolio_backtest_promotion_evidence_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def evaluate_f7_accounting_proof(root_dir: Path | str = ".") -> F7AccountingProof:
    root = Path(root_dir)
    source = read_text(root / MULTI_SLEEVE_BACKTEST)
    weighted_ok = "sum(by_candidate[candidate][date] * weight for candidate, weight in weights.items())" in source
    no_starting_cash = "starting_cash" not in source
    turnover_ok = '"turnover_or_trade_count"' in source and "stream_signal_change_count" in source
    safety_ok = all(
        token in source
        for token in [
            '"execution_approved": False',
            '"general_execution_approved": False',
            '"qqq100_execution_approved": False',
            '"scheduling_approved": False',
            '"live_trading_approved": False',
            "not_promotion_ready_research_only",
        ]
    )

    if weighted_ok and no_starting_cash and turnover_ok and safety_ok:
        final_status = "f7_accounting_static_proof_ready_for_manual_review"
        weighted_status = "weighted_daily_return_aggregation_confirmed"
        starting_cash_status = "no_independent_starting_cash_detected"
        turnover_status = "turnover_context_present"
        promotion_status = "portfolio_backtests_not_promotion_evidence_pending_manual_review"
        blocker = "manual_review_required_before_portfolio_metrics_become_promotion_evidence"
        next_step = "manual_review_f7_accounting_proof_before_any_broader_promotion_ladder_use"
    else:
        final_status = "f7_accounting_static_proof_incomplete_manual_review_required"
        weighted_status = "weighted_daily_return_aggregation_missing_or_unconfirmed" if not weighted_ok else "weighted_daily_return_aggregation_confirmed"
        starting_cash_status = "independent_starting_cash_risk_detected" if not no_starting_cash else "no_independent_starting_cash_detected"
        turnover_status = "turnover_context_missing_or_unconfirmed" if not turnover_ok else "turnover_context_present"
        promotion_status = "portfolio_backtests_blocked_from_promotion_evidence"
        blocker = "missing_or_unconfirmed_f7_accounting_boundary"
        next_step = "fix_or_review_f7_accounting_static_checks_before_promotion_ladder_use"

    return F7AccountingProof(
        final_status=final_status,
        weighted_return_aggregation_status=weighted_status,
        independent_starting_cash_status=starting_cash_status,
        turnover_context_status=turnover_status,
        promotion_evidence_status=promotion_status,
        primary_blocker=blocker,
        recommended_next_step=next_step,
    )


def build_report_rows(proof: F7AccountingProof) -> list[dict[str, Any]]:
    checks = [
        ("weighted_return_aggregation", proof.weighted_return_aggregation_status, "low", "Portfolio returns should be weighted daily returns, not independent sleeve equity curves.", "manual review of weighted return aggregation"),
        ("independent_starting_cash", proof.independent_starting_cash_status, "high", "No independent starting_cash token should appear in multi-sleeve portfolio backtest source.", "keep portfolio accounting proof under manual review"),
        ("turnover_context", proof.turnover_context_status, "medium", "Portfolio metrics should expose turnover/trade context for review.", "keep turnover context visible before promotion evidence use"),
        ("promotion_evidence_boundary", proof.promotion_evidence_status, "high", "Portfolio backtests remain blocked from promotion evidence until manual review accepts F7 proof.", proof.recommended_next_step),
    ]
    return [
        {
            "check_name": name,
            "check_status": status,
            "risk_level": risk,
            "evidence": evidence,
            "required_next_step": next_step,
            **ROW_SAFETY,
        }
        for name, status, risk, evidence, next_step in checks
    ]


def build_summary_rows(proof: F7AccountingProof) -> list[dict[str, Any]]:
    rows = [
        ("final_f7_accounting_status", proof.final_status, "F7 accounting proof status."),
        ("weighted_return_aggregation_status", proof.weighted_return_aggregation_status, "Weighted daily return aggregation status."),
        ("independent_starting_cash_status", proof.independent_starting_cash_status, "Starting-cash duplication risk status."),
        ("turnover_context_status", proof.turnover_context_status, "Turnover/trade-count review context status."),
        ("promotion_evidence_status", proof.promotion_evidence_status, "Whether portfolio backtests may be promotion evidence."),
        ("primary_blocker", proof.primary_blocker, "Primary remaining F7 blocker."),
        ("recommended_next_step", proof.recommended_next_step, "Next step remains manual review, not execution."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("repeat_execution_approved", "False", "Repeat execution approval remains false."),
        ("promotion_approved", "False", "Promotion approval remains false."),
        ("portfolio_backtest_promotion_evidence_approved", "False", "Portfolio backtest promotion evidence approval remains false."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must never be scheduled."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(proof: F7AccountingProof) -> list[dict[str, Any]]:
    rows = [
        (proof.primary_blocker, "manual_review_required", "high", "F7 accounting proof requires manual review before portfolio metrics can be used for promotion evidence.", proof.recommended_next_step),
        ("promotion_not_approved", "blocked", "critical", "This proof does not approve any promotion.", "Do not promote strategies from this report."),
        ("execution_not_approved", "blocked", "critical", "This proof does not approve execution or paper execution.", "Do not run order-capable commands from this report."),
        ("scheduling_not_approved", "blocked", "critical", "Scheduling remains prohibited for order-capable commands.", "Keep Hermes/VPS monitoring-only."),
    ]
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in rows
    ]


def build_evidence_rows(proof: F7AccountingProof) -> list[dict[str, Any]]:
    rows = [
        ("source_file", str(MULTI_SLEEVE_BACKTEST), "Static source inspected; no backtest rerun."),
        ("weighted_return_aggregation_status", proof.weighted_return_aggregation_status, "Weighted daily returns should represent shared portfolio capital."),
        ("independent_starting_cash_status", proof.independent_starting_cash_status, "No duplicated starting cash should be present in the portfolio backtest source."),
        ("promotion_evidence_status", proof.promotion_evidence_status, "Promotion evidence remains blocked pending manual review."),
        ("approval_flags", "all_false", "Execution, scheduling, promotion, and portfolio-evidence approvals remain false."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live F7 accounting proof complete. Report only; no promotion, orders, or scheduling approved.",
        f"final_f7_accounting_status={summary_value(summary_rows, 'final_f7_accounting_status')}",
        f"weighted_return_aggregation_status={summary_value(summary_rows, 'weighted_return_aggregation_status')}",
        f"independent_starting_cash_status={summary_value(summary_rows, 'independent_starting_cash_status')}",
        f"turnover_context_status={summary_value(summary_rows, 'turnover_context_status')}",
        f"promotion_evidence_status={summary_value(summary_rows, 'promotion_evidence_status')}",
        f"primary_blocker={summary_value(summary_rows, 'primary_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; promotion_approved=false; portfolio_backtest_promotion_evidence_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
