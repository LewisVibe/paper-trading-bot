"""Report-only next ladder candidate scope checkpoint.

This checkpoint records which branch should be reviewed next in the paper-live
promotion ladder. It does not promote any branch, create order instructions,
call Alpaca, read positions, refresh market data, schedule anything, or approve
execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OUTPUT_FILES = {
    "report": Path("data/paper_live_next_ladder_candidate_scope.csv"),
    "summary": Path("data/paper_live_next_ladder_candidate_scope_summary.csv"),
    "blockers": Path("data/paper_live_next_ladder_candidate_scope_blockers.csv"),
    "evidence": Path("data/paper_live_next_ladder_candidate_scope_evidence.csv"),
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
    "scope_only": True,
    "saved_output_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "portfolio_execution_wired": False,
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
    "candidate_scope",
    "scope_rank",
    "scope_status",
    "why_this_rank",
    "required_before_candidate_discussion",
    "blocked_until",
    "recommended_next_step",
    "research_only",
    "report_only",
    "scope_only",
    "saved_output_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "portfolio_execution_wired",
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
class CandidateScope:
    candidate_scope: str
    scope_rank: str
    scope_status: str
    why_this_rank: str
    required_before_candidate_discussion: str
    blocked_until: str
    recommended_next_step: str


@dataclass
class NextLadderCandidateScopeResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_next_ladder_candidate_scope(root_dir: Path | str = ".") -> NextLadderCandidateScopeResult:
    root = Path(root_dir)
    scopes = build_candidate_scopes()
    report_rows = [scope_to_row(scope) for scope in scopes]
    summary_rows = build_summary_rows(scopes)
    blocker_rows = build_blocker_rows()
    evidence_rows = build_evidence_rows()
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return NextLadderCandidateScopeResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_next_ladder_candidate_scope(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live next ladder candidate scope is missing.",
            "Run `python bot.py --paper-live-next-ladder-candidate-scope` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; promotion_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live next ladder candidate scope saved display. Report only; no promotion or orders approved.",
        f"final_scope_status: {summary_value(rows, 'final_scope_status')}",
        f"recommended_next_scope: {summary_value(rows, 'recommended_next_scope')}",
        f"scope_reason: {summary_value(rows, 'scope_reason')}",
        f"second_scope: {summary_value(rows, 'second_scope')}",
        f"blocked_scope: {summary_value(rows, 'blocked_scope')}",
        f"portfolio_backtest_evidence_status: {summary_value(rows, 'portfolio_backtest_evidence_status')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; promotion_approved=false; portfolio_backtest_promotion_evidence_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def build_candidate_scopes() -> list[CandidateScope]:
    return [
        CandidateScope(
            candidate_scope="defensive_sleeve",
            scope_rank="1",
            scope_status="recommended_next_scope_report_only_review",
            why_this_rank="Narrowest next review after QQQ100: defensive behaviour can be checked before allocator complexity or high-growth risk.",
            required_before_candidate_discussion="saved_defensive_sleeve_review_pack;F6_unknown_position_boundary;F7_accounting_checkpoint_accepted;no_order_instructions",
            blocked_until="manual_review_defensive_sleeve_saved_evidence",
            recommended_next_step="create_defensive_sleeve_ladder_scope_review_report_only",
        ),
        CandidateScope(
            candidate_scope="multi_sleeve_allocator",
            scope_rank="2",
            scope_status="future_scope_after_defensive_review",
            why_this_rank="Allocator depends on sleeve evidence, F7 accounting, conflicts, and allocation policy; it is broader than a defensive-sleeve review.",
            required_before_candidate_discussion="defensive_sleeve_review;allocation_policy_review;conflict_review;portfolio_backtests_not_promotion_evidence_without_separate_review",
            blocked_until="manual_review_allocator_scope_after_defensive_sleeve",
            recommended_next_step="defer_allocator_until_defensive_scope_review_exists",
        ),
        CandidateScope(
            candidate_scope="high_growth_branch",
            scope_rank="3",
            scope_status="not_next_scope_research_only",
            why_this_rank="High-growth remains concentration/outlier/drawdown sensitive and should not be the next paper-live ladder candidate.",
            required_before_candidate_discussion="concentration_control;drawdown_attribution;component_review;risk_policy_review;separate_manual_review",
            blocked_until="high_growth_research_only_blockers_resolved",
            recommended_next_step="keep_high_growth_research_only",
        ),
        CandidateScope(
            candidate_scope="crypto_branch",
            scope_rank="blocked",
            scope_status="not_next_scope_research_only",
            why_this_rank="Crypto remains capped/future-only research and has no execution approval.",
            required_before_candidate_discussion="crypto_containment_review;custody_execution_policy;separate_manual_review",
            blocked_until="crypto_execution_not_approved",
            recommended_next_step="keep_crypto_research_only",
        ),
    ]


def scope_to_row(scope: CandidateScope) -> dict[str, Any]:
    return {
        "candidate_scope": scope.candidate_scope,
        "scope_rank": scope.scope_rank,
        "scope_status": scope.scope_status,
        "why_this_rank": scope.why_this_rank,
        "required_before_candidate_discussion": scope.required_before_candidate_discussion,
        "blocked_until": scope.blocked_until,
        "recommended_next_step": scope.recommended_next_step,
        **ROW_SAFETY,
    }


def build_summary_rows(scopes: list[CandidateScope]) -> list[dict[str, Any]]:
    recommended = scopes[0]
    second = scopes[1]
    blocked = scopes[2]
    items = [
        ("final_scope_status", "next_ladder_candidate_scope_report_only", "Scope decision only; no promotion or execution approval."),
        ("recommended_next_scope", recommended.candidate_scope, "Defensive sleeve is the first report-only scope to review next."),
        ("scope_reason", recommended.why_this_rank, "Reason for selecting the first scope."),
        ("second_scope", second.candidate_scope, "Allocator remains second because it is broader and depends on sleeve evidence."),
        ("blocked_scope", blocked.candidate_scope, "High-growth remains research-only and not the next ladder scope."),
        ("portfolio_backtest_evidence_status", "f7_accounting_proof_accepted_portfolio_backtests_still_not_promotion_evidence", "F7 is accepted, but portfolio metrics still require separate promotion review."),
        ("recommended_next_step", recommended.recommended_next_step, "Next step is a defensive-sleeve ladder-scope review report only."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
        ("promotion_approved", "False", "Promotion approval remains false."),
        ("portfolio_backtest_promotion_evidence_approved", "False", "Portfolio backtest promotion evidence approval remains false."),
        ("never_schedule_order_capable_commands", "True", "Order-capable commands must not be scheduled."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in items]


def build_blocker_rows() -> list[dict[str, Any]]:
    blockers = [
        ("promotion_not_approved", "blocked", "critical", "This scope checkpoint does not approve promotion.", "Do not promote any branch from this report."),
        ("execution_not_approved", "blocked", "critical", "Execution and paper execution remain unapproved.", "Do not run order-capable commands from this report."),
        ("defensive_scope_needs_review_pack", "manual_review_required", "medium", "Defensive sleeve needs its own saved-output ladder-scope review before candidate discussion.", "Create defensive sleeve ladder-scope review report only."),
        ("allocator_not_next", "blocked", "high", "Allocator review is broader and should wait until defensive scope review exists.", "Defer allocator scope."),
        ("high_growth_not_next", "blocked", "high", "High-growth remains research-only due to concentration/outlier/drawdown risk.", "Keep high-growth out of the paper-live ladder."),
        ("scheduled_execution_forbidden", "blocked", "critical", "Order-capable commands must never be scheduled.", "Keep Hermes/VPS monitoring-only."),
    ]
    return [
        {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows() -> list[dict[str, Any]]:
    rows = [
        ("current_seed", "qqq_100_trend_gate:QQQ", "QQQ100 remains the only current seed."),
        ("f7_accounting_checkpoint", "accepted", "F7 accounting proof is accepted as a static accounting checkpoint."),
        ("recommended_next_scope", "defensive_sleeve", "Defensive sleeve is the narrowest next report-only scope."),
        ("portfolio_backtest_evidence_status", "not_promotion_evidence_without_separate_review", "Portfolio metrics still require separate promotion review."),
        ("approval_flags", "all_false", "Execution, paper execution, scheduling, live trading, follow-up, repeat, promotion, and portfolio-evidence approvals remain false."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live next ladder candidate scope complete. Report only; no promotion, orders, or scheduling approved.",
        f"final_scope_status={summary_value(summary_rows, 'final_scope_status')}",
        f"recommended_next_scope={summary_value(summary_rows, 'recommended_next_scope')}",
        f"scope_reason={summary_value(summary_rows, 'scope_reason')}",
        f"second_scope={summary_value(summary_rows, 'second_scope')}",
        f"blocked_scope={summary_value(summary_rows, 'blocked_scope')}",
        f"portfolio_backtest_evidence_status={summary_value(summary_rows, 'portfolio_backtest_evidence_status')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false; promotion_approved=false; portfolio_backtest_promotion_evidence_approved=false",
        "never_schedule_order_capable_commands=true",
    ]


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "")).strip()
    return "unavailable"


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
