"""Saved-output blocker closeout review for volatility executable-ticket criteria.

This report classifies criteria blockers for manual review. It does not close
blockers, change approval readiness, request approval, create ticket values,
create executable tickets, call Alpaca, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
FINAL_STATUS = "vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_manual_review_required"
FINAL_DECISION = "CRITERIA_BLOCKERS_REVIEWED_NONE_CLOSED"
NEXT_STEP = "manual_review_each_criteria_blocker_before_any_closeout"

OUTPUT_FILES = {
    "review": Path("data/vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review.csv"),
    "summary": Path("data/vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_evidence.csv"),
}

INPUT_FILES = {
    "approval_criteria": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_summary.csv"),
    "resolution_plan": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_summary.csv"),
    "source_review": Path("data/vol_targeted_growth_executable_ticket_criteria_source_review_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "closeout_review_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "criteria_changed": False,
    "blockers_resolved": False,
    "blockers_closed": False,
    "approval_readiness_changed": False,
    "approval_requested": False,
    "approval_recorded": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "order_values_populated": False,
    "order_instructions_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "never_schedule_order_capable_commands": True,
}

REVIEW_COLUMNS = [
    "blocker_name",
    "review_state",
    "risk_level",
    "saved_evidence",
    "manual_review_interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class CriteriaBlockerCloseoutReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review(
    root_dir: Path | str = ".",
) -> CriteriaBlockerCloseoutReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    review_rows = build_review_rows(context)
    blocker_rows = build_blocker_rows(context, inputs)
    summary_rows = build_summary_rows(context, review_rows, blocker_rows)
    evidence_rows = build_evidence_rows(inputs)
    paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return CriteriaBlockerCloseoutReviewResult(
        paths,
        review_rows,
        summary_rows,
        blocker_rows,
        evidence_rows,
        build_summary_lines(summary_rows, paths),
    )


def show_vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review(
    root_dir: Path | str = ".",
) -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted executable-ticket criteria blocker closeout review is missing.",
            "Run `python bot.py --vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted executable-ticket criteria blocker closeout review saved display. Report only; no blockers closed.",
        f"final_blocker_closeout_review_status: {summary_value(rows, 'final_blocker_closeout_review_status')}",
        f"final_blocker_closeout_review_decision: {summary_value(rows, 'final_blocker_closeout_review_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"source_review_decision: {summary_value(rows, 'source_review_decision')}",
        f"review_ready_blocker_count: {summary_value(rows, 'review_ready_blocker_count')}",
        f"open_blocker_count: {summary_value(rows, 'open_blocker_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "criteria_changed=false; blockers_resolved=false; blockers_closed=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "criteria_decision": summary_value(inputs["approval_criteria"], "final_approval_criteria_decision") or "missing_approval_criteria",
        "resolution_decision": summary_value(inputs["resolution_plan"], "final_resolution_plan_decision") or "missing_resolution_plan",
        "source_review_decision": summary_value(inputs["source_review"], "final_source_review_decision") or "missing_source_review",
        "source_review_result": summary_value(inputs["source_review"], "source_review_result") or "missing_source_review_result",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_review_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    raw_rows = [
        (
            "criteria_source_reviewed",
            "review_ready_not_closed" if context["source_review_decision"] == "CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED" else "blocked_missing_source_review",
            "high",
            context["source_review_decision"],
            "Source wording can inform manual review, but it does not close criteria blockers.",
            "manual_review_source_before_closeout",
        ),
        (
            "criteria_resolution_plan_open",
            "open_manual_review_required",
            "critical",
            context["resolution_decision"],
            "Resolution plan remains an open worklist, not a completed closeout.",
            "review_resolution_plan_steps_one_by_one",
        ),
        (
            "approval_criteria_not_approval",
            "open_manual_review_required",
            "critical",
            context["criteria_decision"],
            "Approval criteria are defined, but approval was not requested or recorded.",
            "do_not_request_approval_from_closeout_review",
        ),
        (
            "go_no_go_still_blocks_execution",
            "blocked_no_go",
            "critical",
            context["go_no_go_decision"],
            "The go/no-go dashboard must remain no-go while blockers are open.",
            "keep_dashboard_no_go",
        ),
        (
            "ticket_values_still_blank",
            "open_manual_review_required",
            "critical",
            "order_values_populated=false; executable_ticket_created=false",
            "No side, quantity, order type, or executable ticket may be created here.",
            "separate_explicit_ticket_value_review_if_ever_needed",
        ),
    ]
    return [review_row(*row) for row in raw_rows]


def build_summary_rows(
    context: dict[str, str],
    review_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    review_ready_count = sum(1 for row in review_rows if row["review_state"] == "review_ready_not_closed")
    data = [
        ("final_blocker_closeout_review_status", FINAL_STATUS, "Blocker closeout review is saved-output/manual-review only."),
        ("final_blocker_closeout_review_decision", FINAL_DECISION, "No blockers were closed."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("criteria_decision", context["criteria_decision"], "Saved approval criteria decision."),
        ("resolution_plan_decision", context["resolution_decision"], "Saved resolution plan decision."),
        ("source_review_decision", context["source_review_decision"], "Saved source review decision."),
        ("source_review_result", context["source_review_result"], "Saved source review result."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go decision."),
        ("review_ready_blocker_count", str(review_ready_count), "Items ready for manual review but not closeout."),
        ("review_row_count", str(len(review_rows)), "Review row count."),
        ("open_blocker_count", str(len(blocker_rows)), "Open blocker row count."),
        ("largest_blocker", "criteria_blockers_reviewed_but_not_closed", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Manual review before closing any blocker."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("criteria_blockers_reviewed_but_not_closed", "blocked", "critical", FINAL_DECISION, "manual_review_each_criteria_blocker"),
        blocker_row("approval_request_not_allowed", "blocked", "critical", "approval_requested=false; approval_recorded=false", "do_not_request_approval_from_closeout_review"),
        blocker_row("approval_readiness_not_changed", "blocked", "critical", "approval_readiness_changed=false", "keep_approval_readiness_blocked"),
        blocker_row("go_no_go_remains_no_go", "blocked", "critical", context["go_no_go_decision"], "keep_dashboard_no_go"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_all_approval_flags_false"),
    ]
    for name, input_rows in inputs.items():
        if not input_rows:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def build_evidence_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.")
        for name, path in INPUT_FILES.items()
    ]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path]) -> list[str]:
    return [
        "Executable-ticket criteria blocker closeout review complete. Report only; no blockers closed.",
        f"final_blocker_closeout_review_status={summary_value(summary_rows, 'final_blocker_closeout_review_status')}",
        f"final_blocker_closeout_review_decision={summary_value(summary_rows, 'final_blocker_closeout_review_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"review_ready_blocker_count={summary_value(summary_rows, 'review_ready_blocker_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={paths['review']}",
        "criteria_changed=false; blockers_resolved=false; blockers_closed=false; approval_readiness_changed=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def review_row(name: str, state: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "review_state": state, "risk_level": risk, "saved_evidence": evidence, "manual_review_interpretation": interpretation, "required_next_step": next_step, **SAFETY_FLAGS}


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


def evidence_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
