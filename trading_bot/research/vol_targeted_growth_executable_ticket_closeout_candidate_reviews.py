"""Saved-output closeout-candidate reviews for volatility executable-ticket criteria.

These reports assess whether reviewed blockers are candidates for human
closeout consideration. They do not close blockers, change approval readiness,
request approval, create ticket values, create executable tickets, call Alpaca,
or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"

CONFIGS = {
    "criteria_source": {
        "slug": "criteria_source_closeout_candidate_review",
        "label": "criteria source closeout-candidate review",
        "status": "vol_targeted_growth_criteria_source_closeout_candidate_review_manual_review_required",
        "decision": "CLOSEOUT_CANDIDATE_READY_FOR_MANUAL_REVIEW",
        "blocker": "criteria_source_reviewed",
        "candidate_state": "candidate_ready_not_closed",
        "evidence_key": "criteria_source_review_decision",
        "next_step": "manual_review_criteria_source_closeout_candidate_before_closure",
    },
    "resolution_plan": {
        "slug": "criteria_resolution_plan_closeout_candidate_review",
        "label": "criteria resolution plan closeout-candidate review",
        "status": "vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review_manual_review_required",
        "decision": "CLOSEOUT_CANDIDATE_NOT_READY_STILL_OPEN",
        "blocker": "criteria_resolution_plan_open",
        "candidate_state": "not_ready_still_open",
        "evidence_key": "criteria_resolution_plan_review_decision",
        "next_step": "manual_review_resolution_plan_open_items_before_closeout",
    },
    "approval_criteria": {
        "slug": "approval_criteria_not_approval_closeout_candidate_review",
        "label": "approval criteria not approval closeout-candidate review",
        "status": "vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review_manual_review_required",
        "decision": "CLOSEOUT_CANDIDATE_NOT_READY_NO_APPROVAL",
        "blocker": "approval_criteria_not_approval",
        "candidate_state": "not_ready_no_approval",
        "evidence_key": "approval_criteria_review_decision",
        "next_step": "manual_review_approval_boundary_before_any_closeout",
    },
}

ROLLUP_STATUS = "vol_targeted_growth_criteria_closeout_candidate_review_rollup_manual_review_required"
ROLLUP_DECISION = "CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED"
ROLLUP_NEXT_STEP = "manual_review_closeout_candidates_before_any_blocker_closure"

INPUT_FILES = {
    "criteria_source_review": Path("data/vol_targeted_growth_executable_ticket_criteria_source_blocker_review_summary.csv"),
    "criteria_resolution_review": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_blocker_review_summary.csv"),
    "approval_criteria_review": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_not_approval_blocker_review_summary.csv"),
    "blocker_specific_rollup": Path("data/vol_targeted_growth_executable_ticket_criteria_blocker_specific_review_rollup_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "closeout_candidate_review_only": True,
    "manual_review_only": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
    "criteria_changed": False,
    "blockers_resolved": False,
    "blockers_closed": False,
    "closeout_candidate_only": True,
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

REVIEW_COLUMNS = ["review_name", "blocker_name", "candidate_state", "risk_level", "saved_evidence", "required_next_step", *SAFETY_FLAGS.keys()]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class CloseoutCandidateReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_criteria_source_closeout_candidate_review(root_dir: Path | str = ".") -> CloseoutCandidateReviewResult:
    return generate_single("criteria_source", root_dir)


def show_vol_targeted_growth_criteria_source_closeout_candidate_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_single("criteria_source", root_dir)


def generate_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review(root_dir: Path | str = ".") -> CloseoutCandidateReviewResult:
    return generate_single("resolution_plan", root_dir)


def show_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_single("resolution_plan", root_dir)


def generate_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review(root_dir: Path | str = ".") -> CloseoutCandidateReviewResult:
    return generate_single("approval_criteria", root_dir)


def show_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_single("approval_criteria", root_dir)


def generate_vol_targeted_growth_criteria_closeout_candidate_review_rollup(root_dir: Path | str = ".") -> CloseoutCandidateReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    review_rows = [review_row(key, context) for key in CONFIGS]
    blocker_rows = common_blockers(context, inputs)
    summary_rows = rollup_summary_rows(review_rows, blocker_rows, context)
    evidence_rows = evidence_rows_from_inputs(inputs)
    paths = output_paths(root, "criteria_closeout_candidate_review_rollup")
    write_outputs(paths, review_rows, summary_rows, blocker_rows, evidence_rows)
    return CloseoutCandidateReviewResult(paths, review_rows, summary_rows, blocker_rows, evidence_rows, summary_lines(summary_rows, paths, "criteria closeout-candidate review rollup"))


def show_vol_targeted_growth_criteria_closeout_candidate_review_rollup(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_review("criteria_closeout_candidate_review_rollup", "criteria closeout-candidate review rollup", root_dir)


def generate_single(config_key: str, root_dir: Path | str) -> CloseoutCandidateReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    config = CONFIGS[config_key]
    review_rows = [review_row(config_key, context)]
    blocker_rows = common_blockers(context, inputs)
    summary_rows = single_summary_rows(config, review_rows, blocker_rows, context)
    evidence_rows = evidence_rows_from_inputs(inputs)
    paths = output_paths(root, config["slug"])
    write_outputs(paths, review_rows, summary_rows, blocker_rows, evidence_rows)
    return CloseoutCandidateReviewResult(paths, review_rows, summary_rows, blocker_rows, evidence_rows, summary_lines(summary_rows, paths, config["label"]))


def show_single(config_key: str, root_dir: Path | str) -> tuple[int, list[str]]:
    config = CONFIGS[config_key]
    return show_review(config["slug"], config["label"], root_dir)


def show_review(slug: str, label: str, root_dir: Path | str) -> tuple[int, list[str]]:
    path = Path(root_dir) / f"data/vol_targeted_growth_executable_ticket_{slug}_summary.csv"
    if not path.exists():
        return 1, [
            f"Volatility-targeted executable-ticket {label} is missing.",
            "Run the matching report command first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        f"Volatility-targeted executable-ticket {label} saved display. Report only; no blockers closed.",
        f"final_candidate_review_status: {summary_value(rows, 'final_candidate_review_status')}",
        f"final_candidate_review_decision: {summary_value(rows, 'final_candidate_review_decision')}",
        f"candidate_ready_count: {summary_value(rows, 'candidate_ready_count')}",
        f"not_ready_count: {summary_value(rows, 'not_ready_count')}",
        f"open_blocker_count: {summary_value(rows, 'open_blocker_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "closeout_candidate_only=true; blockers_resolved=false; blockers_closed=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def output_paths(root: Path, slug: str) -> dict[str, Path]:
    base = f"data/vol_targeted_growth_executable_ticket_{slug}"
    return {
        "review": root / f"{base}.csv",
        "summary": root / f"{base}_summary.csv",
        "blockers": root / f"{base}_blockers.csv",
        "evidence": root / f"{base}_evidence.csv",
    }


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "criteria_source_review_decision": summary_value(inputs["criteria_source_review"], "final_review_decision") or "missing_criteria_source_review",
        "criteria_resolution_plan_review_decision": summary_value(inputs["criteria_resolution_review"], "final_review_decision") or "missing_resolution_plan_review",
        "approval_criteria_review_decision": summary_value(inputs["approval_criteria_review"], "final_review_decision") or "missing_approval_criteria_review",
        "blocker_specific_rollup_decision": summary_value(inputs["blocker_specific_rollup"], "final_review_decision") or "missing_blocker_specific_rollup",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def review_row(config_key: str, context: dict[str, str]) -> dict[str, Any]:
    config = CONFIGS[config_key]
    return {
        "review_name": config["slug"],
        "blocker_name": config["blocker"],
        "candidate_state": config["candidate_state"],
        "risk_level": "critical" if config_key != "criteria_source" else "high",
        "saved_evidence": context[config["evidence_key"]],
        "required_next_step": config["next_step"],
        **SAFETY_FLAGS,
    }


def single_summary_rows(config: dict[str, str], review_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], context: dict[str, str]) -> list[dict[str, Any]]:
    ready = count_state(review_rows, "candidate_ready_not_closed")
    not_ready = len(review_rows) - ready
    rows = [
        ("final_candidate_review_status", config["status"], "Closeout-candidate review is saved-output/manual-review only."),
        ("final_candidate_review_decision", config["decision"], "The blocker was assessed as a closeout candidate, but not closed."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("candidate_ready_count", str(ready), "Candidate-ready count."),
        ("not_ready_count", str(not_ready), "Not-ready count."),
        ("reviewed_candidate_count", str(len(review_rows)), "Reviewed candidate count."),
        ("open_blocker_count", str(len(blocker_rows)), "Open blocker row count."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go decision."),
        ("largest_blocker", "closeout_candidate_review_does_not_close_blockers", "Primary blocker."),
        ("recommended_next_step", config["next_step"], "Manual review before blocker closure."),
    ]
    return [summary_row(*row) for row in rows]


def rollup_summary_rows(review_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], context: dict[str, str]) -> list[dict[str, Any]]:
    ready = count_state(review_rows, "candidate_ready_not_closed")
    not_ready = len(review_rows) - ready
    rows = [
        ("final_candidate_review_status", ROLLUP_STATUS, "Closeout-candidate review rollup is saved-output/manual-review only."),
        ("final_candidate_review_decision", ROLLUP_DECISION, "Closeout candidates were reviewed but no blockers were closed."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("candidate_ready_count", str(ready), "Candidate-ready count."),
        ("not_ready_count", str(not_ready), "Not-ready count."),
        ("reviewed_candidate_count", str(len(review_rows)), "Reviewed candidate count."),
        ("open_blocker_count", str(len(blocker_rows)), "Open blocker row count."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go decision."),
        ("largest_blocker", "closeout_candidates_reviewed_none_closed", "Primary blocker."),
        ("recommended_next_step", ROLLUP_NEXT_STEP, "Manual review before blocker closure."),
    ]
    return [summary_row(*row) for row in rows]


def common_blockers(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("closeout_candidates_reviewed_none_closed", "blocked", "critical", "blockers_closed=false", "manual_review_before_closure"),
        blocker_row("approval_request_not_allowed", "blocked", "critical", "approval_requested=false; approval_recorded=false", "do_not_request_approval_from_candidate_review"),
        blocker_row("approval_readiness_not_changed", "blocked", "critical", "approval_readiness_changed=false", "keep_approval_readiness_blocked"),
        blocker_row("go_no_go_remains_no_go", "blocked", "critical", context["go_no_go_decision"], "keep_dashboard_no_go"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_all_approval_flags_false"),
    ]
    for name, input_rows in inputs.items():
        if not input_rows:
            rows.insert(0, blocker_row(f"missing_{name}", "blocked", "high", f"Missing saved input: {INPUT_FILES[name]}", f"refresh_{name}_report_only"))
    return rows


def evidence_rows_from_inputs(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [evidence_row(f"{name}_input", f"{path}; rows={len(inputs[name])}", "Saved input row count.") for name, path in INPUT_FILES.items()]
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def summary_lines(rows: list[dict[str, Any]], paths: dict[str, Path], label: str) -> list[str]:
    return [
        f"Executable-ticket {label} complete. Report only; no blockers closed.",
        f"final_candidate_review_status={summary_value(rows, 'final_candidate_review_status')}",
        f"final_candidate_review_decision={summary_value(rows, 'final_candidate_review_decision')}",
        f"active_seed={summary_value(rows, 'active_seed')}",
        f"candidate_ready_count={summary_value(rows, 'candidate_ready_count')}",
        f"not_ready_count={summary_value(rows, 'not_ready_count')}",
        f"open_blocker_count={summary_value(rows, 'open_blocker_count')}",
        f"largest_blocker={summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(rows, 'recommended_next_step')}",
        f"saved_report={paths['review']}",
        "closeout_candidate_only=true; blockers_resolved=false; blockers_closed=false; approval_readiness_changed=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def count_state(rows: list[dict[str, Any]], state: str) -> int:
    return sum(1 for row in rows if row["candidate_state"] == state)


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def write_outputs(paths: dict[str, Path], review_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> None:
    write_rows(paths["review"], REVIEW_COLUMNS, review_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)


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
