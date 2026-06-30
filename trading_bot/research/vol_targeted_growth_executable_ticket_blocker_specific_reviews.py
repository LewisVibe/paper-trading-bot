"""Saved-output blocker-specific reviews for volatility executable-ticket criteria.

These reports review individual criteria blockers and a combined rollup. They
do not close blockers, change approval readiness, request approval, create
ticket values, create executable tickets, call Alpaca, or approve execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"

COMMAND_CONFIGS = {
    "criteria_source": {
        "slug": "criteria_source_blocker_review",
        "label": "criteria source blocker review",
        "status": "vol_targeted_growth_criteria_source_blocker_review_manual_review_required",
        "decision": "CRITERIA_SOURCE_BLOCKER_REVIEWED_NOT_CLOSED",
        "blocker": "criteria_source_reviewed",
        "review_state": "review_ready_not_closed",
        "evidence_key": "source_review_decision",
        "interpretation": "Criteria source evidence exists and can support manual closeout discussion, but this report does not close the blocker.",
        "next_step": "manual_review_criteria_source_evidence_before_closeout",
    },
    "resolution_plan": {
        "slug": "criteria_resolution_plan_blocker_review",
        "label": "criteria resolution plan blocker review",
        "status": "vol_targeted_growth_criteria_resolution_plan_blocker_review_manual_review_required",
        "decision": "CRITERIA_RESOLUTION_PLAN_REVIEWED_STILL_OPEN",
        "blocker": "criteria_resolution_plan_open",
        "review_state": "open_manual_review_required",
        "evidence_key": "resolution_plan_decision",
        "interpretation": "The criteria resolution plan exists and is ordered, but it remains an open worklist.",
        "next_step": "manual_review_resolution_plan_steps_before_closeout",
    },
    "approval_criteria": {
        "slug": "approval_criteria_not_approval_blocker_review",
        "label": "approval criteria not approval blocker review",
        "status": "vol_targeted_growth_approval_criteria_not_approval_blocker_review_manual_review_required",
        "decision": "APPROVAL_CRITERIA_REVIEWED_APPROVAL_STILL_NOT_REQUESTED",
        "blocker": "approval_criteria_not_approval",
        "review_state": "open_manual_review_required",
        "evidence_key": "approval_criteria_decision",
        "interpretation": "Approval criteria are documented, but no approval was requested or recorded.",
        "next_step": "manual_review_approval_criteria_before_any_approval_request",
    },
}

ROLLUP_STATUS = "vol_targeted_growth_criteria_blocker_specific_review_rollup_manual_review_required"
ROLLUP_DECISION = "CRITERIA_BLOCKER_SPECIFIC_REVIEWS_CREATED_NONE_CLOSED"
ROLLUP_NEXT_STEP = "manual_review_blocker_specific_reviews_before_any_closeout"

INPUT_FILES = {
    "approval_criteria": Path("data/vol_targeted_growth_executable_ticket_approval_criteria_summary.csv"),
    "resolution_plan": Path("data/vol_targeted_growth_executable_ticket_criteria_resolution_plan_summary.csv"),
    "source_review": Path("data/vol_targeted_growth_executable_ticket_criteria_source_review_summary.csv"),
    "blocker_closeout_review": Path("data/vol_targeted_growth_executable_ticket_criteria_blocker_closeout_review_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "blocker_specific_review_only": True,
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
    "review_name",
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
class BlockerSpecificReviewResult:
    output_paths: dict[str, Path]
    review_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_criteria_source_blocker_review(root_dir: Path | str = ".") -> BlockerSpecificReviewResult:
    return generate_single_review("criteria_source", root_dir)


def show_vol_targeted_growth_criteria_source_blocker_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_single_review("criteria_source", root_dir)


def generate_vol_targeted_growth_criteria_resolution_plan_blocker_review(root_dir: Path | str = ".") -> BlockerSpecificReviewResult:
    return generate_single_review("resolution_plan", root_dir)


def show_vol_targeted_growth_criteria_resolution_plan_blocker_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_single_review("resolution_plan", root_dir)


def generate_vol_targeted_growth_approval_criteria_not_approval_blocker_review(root_dir: Path | str = ".") -> BlockerSpecificReviewResult:
    return generate_single_review("approval_criteria", root_dir)


def show_vol_targeted_growth_approval_criteria_not_approval_blocker_review(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_single_review("approval_criteria", root_dir)


def generate_vol_targeted_growth_criteria_blocker_specific_review_rollup(root_dir: Path | str = ".") -> BlockerSpecificReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    review_rows = [single_review_row(key, context) for key in COMMAND_CONFIGS]
    blocker_rows = build_common_blockers(context, inputs)
    summary_rows = build_rollup_summary_rows(review_rows, blocker_rows, context)
    evidence_rows = build_evidence_rows(inputs)
    paths = output_paths(root, "criteria_blocker_specific_review_rollup")
    write_standard_outputs(paths, review_rows, summary_rows, blocker_rows, evidence_rows)
    return BlockerSpecificReviewResult(paths, review_rows, summary_rows, blocker_rows, evidence_rows, build_summary_lines(summary_rows, paths, "criteria blocker specific review rollup"))


def show_vol_targeted_growth_criteria_blocker_specific_review_rollup(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    return show_review("criteria_blocker_specific_review_rollup", "criteria blocker specific review rollup", root_dir)


def generate_single_review(config_key: str, root_dir: Path | str) -> BlockerSpecificReviewResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    config = COMMAND_CONFIGS[config_key]
    review_rows = [single_review_row(config_key, context)]
    blocker_rows = build_common_blockers(context, inputs)
    summary_rows = build_single_summary_rows(config, review_rows, blocker_rows, context)
    evidence_rows = build_evidence_rows(inputs)
    paths = output_paths(root, config["slug"])
    write_standard_outputs(paths, review_rows, summary_rows, blocker_rows, evidence_rows)
    return BlockerSpecificReviewResult(paths, review_rows, summary_rows, blocker_rows, evidence_rows, build_summary_lines(summary_rows, paths, config["label"]))


def show_single_review(config_key: str, root_dir: Path | str) -> tuple[int, list[str]]:
    config = COMMAND_CONFIGS[config_key]
    return show_review(config["slug"], config["label"], root_dir)


def show_review(slug: str, label: str, root_dir: Path | str) -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / f"data/vol_targeted_growth_executable_ticket_{slug}_summary.csv"
    if not summary_path.exists():
        return 1, [
            f"Volatility-targeted executable-ticket {label} is missing.",
            f"Run the matching report command first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        f"Volatility-targeted executable-ticket {label} saved display. Report only; no blockers closed.",
        f"final_review_status: {summary_value(rows, 'final_review_status')}",
        f"final_review_decision: {summary_value(rows, 'final_review_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"reviewed_blocker_count: {summary_value(rows, 'reviewed_blocker_count')}",
        f"review_ready_blocker_count: {summary_value(rows, 'review_ready_blocker_count')}",
        f"open_blocker_count: {summary_value(rows, 'open_blocker_count')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "criteria_changed=false; blockers_resolved=false; blockers_closed=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
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
        "approval_criteria_decision": summary_value(inputs["approval_criteria"], "final_approval_criteria_decision") or "missing_approval_criteria",
        "resolution_plan_decision": summary_value(inputs["resolution_plan"], "final_resolution_plan_decision") or "missing_resolution_plan",
        "source_review_decision": summary_value(inputs["source_review"], "final_source_review_decision") or "missing_source_review",
        "source_review_result": summary_value(inputs["source_review"], "source_review_result") or "missing_source_review_result",
        "closeout_review_decision": summary_value(inputs["blocker_closeout_review"], "final_blocker_closeout_review_decision") or "missing_blocker_closeout_review",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def single_review_row(config_key: str, context: dict[str, str]) -> dict[str, Any]:
    config = COMMAND_CONFIGS[config_key]
    return {
        "review_name": config["slug"],
        "blocker_name": config["blocker"],
        "review_state": config["review_state"],
        "risk_level": "critical" if config_key != "criteria_source" else "high",
        "saved_evidence": context[config["evidence_key"]],
        "manual_review_interpretation": config["interpretation"],
        "required_next_step": config["next_step"],
        **SAFETY_FLAGS,
    }


def build_single_summary_rows(
    config: dict[str, str],
    review_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    context: dict[str, str],
) -> list[dict[str, Any]]:
    review_ready_count = sum(1 for row in review_rows if row["review_state"] == "review_ready_not_closed")
    data = [
        ("final_review_status", config["status"], "Blocker-specific review is saved-output/manual-review only."),
        ("final_review_decision", config["decision"], "The blocker was reviewed but not closed."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("reviewed_blocker_count", str(len(review_rows)), "Reviewed blocker row count."),
        ("review_ready_blocker_count", str(review_ready_count), "Items ready for manual review but not closeout."),
        ("open_blocker_count", str(len(blocker_rows)), "Open blocker row count."),
        ("source_review_decision", context["source_review_decision"], "Saved source review decision."),
        ("resolution_plan_decision", context["resolution_plan_decision"], "Saved resolution plan decision."),
        ("approval_criteria_decision", context["approval_criteria_decision"], "Saved approval criteria decision."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go decision."),
        ("largest_blocker", "blocker_reviewed_but_not_closed", "Primary blocker."),
        ("recommended_next_step", config["next_step"], "Manual review before blocker closeout."),
    ]
    return [summary_row(*item) for item in data]


def build_rollup_summary_rows(
    review_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    context: dict[str, str],
) -> list[dict[str, Any]]:
    review_ready_count = sum(1 for row in review_rows if row["review_state"] == "review_ready_not_closed")
    open_review_count = sum(1 for row in review_rows if row["review_state"] != "review_ready_not_closed")
    data = [
        ("final_review_status", ROLLUP_STATUS, "Blocker-specific review rollup is saved-output/manual-review only."),
        ("final_review_decision", ROLLUP_DECISION, "The blocker-specific reviews were created but no blockers were closed."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("reviewed_blocker_count", str(len(review_rows)), "Reviewed blocker row count."),
        ("review_ready_blocker_count", str(review_ready_count), "Items ready for manual review but not closeout."),
        ("open_specific_review_count", str(open_review_count), "Items that remain open/manual-review-required."),
        ("open_blocker_count", str(len(blocker_rows)), "Open blocker row count."),
        ("source_review_decision", context["source_review_decision"], "Saved source review decision."),
        ("resolution_plan_decision", context["resolution_plan_decision"], "Saved resolution plan decision."),
        ("approval_criteria_decision", context["approval_criteria_decision"], "Saved approval criteria decision."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go decision."),
        ("largest_blocker", "blocker_specific_reviews_do_not_close_blockers", "Primary blocker."),
        ("recommended_next_step", ROLLUP_NEXT_STEP, "Manual review before blocker closeout."),
    ]
    return [summary_row(*item) for item in data]


def build_common_blockers(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("blocker_specific_reviews_do_not_close_blockers", "blocked", "critical", "blockers_closed=false", "manual_review_before_closeout"),
        blocker_row("approval_request_not_allowed", "blocked", "critical", "approval_requested=false; approval_recorded=false", "do_not_request_approval_from_review"),
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


def build_summary_lines(summary_rows: list[dict[str, Any]], paths: dict[str, Path], label: str) -> list[str]:
    return [
        f"Executable-ticket {label} complete. Report only; no blockers closed.",
        f"final_review_status={summary_value(summary_rows, 'final_review_status')}",
        f"final_review_decision={summary_value(summary_rows, 'final_review_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"reviewed_blocker_count={summary_value(summary_rows, 'reviewed_blocker_count')}",
        f"review_ready_blocker_count={summary_value(summary_rows, 'review_ready_blocker_count')}",
        f"open_blocker_count={summary_value(summary_rows, 'open_blocker_count')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={paths['review']}",
        "criteria_changed=false; blockers_resolved=false; blockers_closed=false; approval_readiness_changed=false; approval_requested=false; approval_recorded=false; order_values_populated=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def write_standard_outputs(
    paths: dict[str, Path],
    review_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> None:
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
