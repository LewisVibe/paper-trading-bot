"""Saved-output QQQ100 follow-up/no-action policy report.

This report interprets saved QQQ100 evidence only. It does not call Alpaca,
read live positions, refresh market data, create executable order instructions,
submit/cancel/replace orders, write SQLite, send alerts, schedule anything, or
approve follow-up/repeat execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trading_bot.research.paper_live_evidence_audit import evaluate_paper_live_saved_evidence


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

OUTPUT_FILES = {
    "report": Path("data/qqq100_followup_policy_report.csv"),
    "summary": Path("data/qqq100_followup_policy_summary.csv"),
    "blockers": Path("data/qqq100_followup_policy_blockers.csv"),
    "evidence": Path("data/qqq100_followup_policy_evidence.csv"),
}

SAFETY_FLAGS = {
    "repeat_execution_approved": False,
    "followup_order_approved": False,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "live_positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    **SAFETY_FLAGS,
}

REPORT_COLUMNS = [
    "check_name",
    "policy_status",
    "desired_state",
    "saved_position_state",
    "saved_position_quantity",
    "alignment_state",
    "no_action_required",
    "finding",
    "blocker",
    "recommended_next_step",
    "research_only",
    "report_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "alpaca_called",
    "live_positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    *SAFETY_FLAGS.keys(),
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    *SAFETY_FLAGS.keys(),
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]

EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_value",
    "details",
    *SAFETY_FLAGS.keys(),
]


@dataclass(frozen=True)
class Qqq100FollowupPolicy:
    desired_state: str
    saved_position_state: str
    saved_position_quantity: str
    alignment_state: str
    final_policy_status: str
    no_action_required: bool
    blocker: str
    recommended_next_step: str


@dataclass
class Qqq100FollowupPolicyReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_followup_policy_report(
    root_dir: Path | str = ".",
) -> Qqq100FollowupPolicyReportResult:
    root = Path(root_dir)
    policy = evaluate_followup_policy(root)
    report_rows = build_report_rows(policy)
    summary_rows = build_summary_rows(policy)
    blocker_rows = build_blocker_rows(policy)
    evidence_rows = build_evidence_rows(policy)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return Qqq100FollowupPolicyReportResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_qqq100_followup_policy_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "QQQ100 follow-up policy report is missing.",
            "Run `python bot.py --qqq100-followup-policy-report` first.",
            "execution_approved=false; paper_execution_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "QQQ100 follow-up policy saved display. Report only; no orders approved.",
        f"final_followup_policy_status: {summary_value(rows, 'final_followup_policy_status')}",
        f"desired_state: {summary_value(rows, 'desired_state')}",
        f"saved_position_state: {summary_value(rows, 'saved_position_state')}",
        f"saved_position_quantity: {summary_value(rows, 'saved_position_quantity')}",
        f"alignment_state: {summary_value(rows, 'alignment_state')}",
        f"no_action_required: {summary_value(rows, 'no_action_required')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "Warning: this policy report does not create order instructions or approve repeat execution.",
    ]


def evaluate_followup_policy(root_dir: Path | str = ".") -> Qqq100FollowupPolicy:
    snapshot = evaluate_paper_live_saved_evidence(root_dir)
    desired_state = snapshot.desired_state
    saved_state = snapshot.saved_current_position_state
    quantity = snapshot.saved_current_position_quantity
    alignment_state = snapshot.current_alignment_state
    quantity_status = classify_quantity(quantity)

    if quantity_status != "valid":
        return Qqq100FollowupPolicy(
            desired_state,
            saved_state,
            quantity,
            alignment_state,
            "manual_review_required_quantity_unverified",
            False,
            f"invalid_or_unavailable_saved_quantity:{quantity}",
            "regenerate_or_review_saved_quantity_evidence_before_any_followup_discussion",
        )
    quantity_decimal = Decimal(quantity)
    if quantity_decimal > Decimal("1"):
        return Qqq100FollowupPolicy(
            desired_state,
            saved_state,
            quantity,
            alignment_state,
            "manual_review_required_excess_saved_quantity",
            False,
            "saved_quantity_above_one",
            "manual_review_required_before_any_reduce_or_followup_discussion",
        )
    if quantity_decimal not in {Decimal("0"), Decimal("1")}:
        return Qqq100FollowupPolicy(
            desired_state,
            saved_state,
            quantity,
            alignment_state,
            "manual_review_required_fractional_saved_quantity",
            False,
            "saved_quantity_fractional_or_unsupported",
            "manual_review_required_before_any_followup_discussion",
        )
    if desired_state == "long" and saved_state == "paper_position_long" and quantity_decimal == Decimal("1"):
        return Qqq100FollowupPolicy(
            desired_state,
            saved_state,
            quantity,
            alignment_state,
            "no_action_required_already_aligned",
            True,
            "none_for_no_action_policy",
            "hold_no_action_and_do_not_repeat_buy",
        )
    if desired_state == "flat" and saved_state == "paper_position_long" and quantity_decimal == Decimal("1"):
        return Qqq100FollowupPolicy(
            desired_state,
            saved_state,
            quantity,
            alignment_state,
            "future_manual_flatten_discussion_possible",
            False,
            "separate_flatten_readiness_and_manual_approval_required",
            "separate_manual_flatten_readiness_review_required_before_any_action",
        )
    if desired_state == "long" and saved_state in {"paper_position_flat", "unavailable"} and quantity_decimal == Decimal("0"):
        return Qqq100FollowupPolicy(
            desired_state,
            saved_state,
            quantity,
            alignment_state,
            "future_manual_buy_discussion_possible",
            False,
            "separate_buy_readiness_and_manual_approval_required",
            "separate_manual_buy_readiness_review_required_before_any_action",
        )
    if desired_state == "flat" and quantity_decimal == Decimal("0"):
        return Qqq100FollowupPolicy(
            desired_state,
            saved_state,
            quantity,
            alignment_state,
            "no_action_required_already_flat",
            True,
            "none_for_no_action_policy",
            "hold_no_action_and_do_not_open_position",
        )
    return Qqq100FollowupPolicy(
        desired_state,
        saved_state,
        quantity,
        alignment_state,
        "manual_review_required_contradictory_saved_state",
        False,
        "contradictory_desired_position_or_saved_position_state",
        "manual_review_required_before_any_followup_discussion",
    )


def classify_quantity(value: str) -> str:
    try:
        Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "invalid"
    return "valid"


def build_report_rows(policy: Qqq100FollowupPolicy) -> list[dict[str, Any]]:
    rows = [
        report_row(
            "qqq100_followup_policy",
            policy.final_policy_status,
            policy,
            "QQQ100 saved state interpreted for no-action/follow-up policy.",
        ),
        report_row(
            "repeat_execution_boundary",
            "blocked_repeat_execution_not_approved",
            policy,
            "Repeat execution is not approved even when saved state is aligned.",
        ),
        report_row(
            "followup_order_boundary",
            "blocked_followup_order_not_approved",
            policy,
            "Follow-up orders are not approved by this report.",
        ),
    ]
    return rows


def build_summary_rows(policy: Qqq100FollowupPolicy) -> list[dict[str, Any]]:
    rows = [
        ("final_followup_policy_status", policy.final_policy_status, "Saved-state QQQ100 follow-up/no-action policy status."),
        ("candidate_strategy", STRATEGY_NAME, "Only QQQ100 is in scope."),
        ("candidate_ticker", TICKER, "Only QQQ is in scope."),
        ("desired_state", policy.desired_state, "Saved desired QQQ100 state."),
        ("saved_position_state", policy.saved_position_state, "Saved paper QQQ position state."),
        ("saved_position_quantity", policy.saved_position_quantity, "Saved absolute QQQ quantity."),
        ("alignment_state", policy.alignment_state, "Saved alignment state."),
        ("no_action_required", str(policy.no_action_required), "True only when saved state requires no paper action."),
        ("largest_blocker", policy.blocker, "Largest blocker or none for no-action status."),
        ("recommended_next_step", policy.recommended_next_step, "Next step remains manual review/no-action, not execution."),
        ("repeat_execution_approved", "False", "Repeat execution remains false."),
        ("followup_order_approved", "False", "Follow-up order approval remains false."),
        ("execution_approved", "False", "Execution approval remains false."),
        ("paper_execution_approved", "False", "Paper execution approval remains false."),
        ("scheduling_approved", "False", "Scheduling approval remains false."),
        ("live_trading_approved", "False", "Live trading approval remains false."),
    ]
    return [{"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in rows]


def build_blocker_rows(policy: Qqq100FollowupPolicy) -> list[dict[str, Any]]:
    blockers = [
        ("repeat_execution_not_approved", "blocked", "critical", "Repeat execution is not approved.", "Do not rerun QQQ100 paper execution from this report."),
        ("followup_order_not_approved", "blocked", "critical", "Follow-up orders are not approved.", "Do not create order instructions from this report."),
        ("execution_not_approved", "blocked", "critical", "This policy report does not approve execution or paper execution.", "Use separate explicit approval for any future broker-read or action workflow."),
        ("scheduling_not_approved", "blocked", "critical", "Scheduling remains prohibited for order-capable commands.", "Do not schedule QQQ100 execution or follow-up workflows."),
    ]
    if policy.blocker != "none_for_no_action_policy":
        blockers.insert(
            0,
            (
                policy.blocker,
                "manual_review_required",
                "high",
                f"Policy status: {policy.final_policy_status}.",
                policy.recommended_next_step,
            ),
        )
    return [
        {
            "blocker_name": name,
            "status": status,
            "severity": severity,
            "details": details,
            "required_next_step": next_step,
            **SAFETY_FLAGS,
        }
        for name, status, severity, details, next_step in blockers
    ]


def build_evidence_rows(policy: Qqq100FollowupPolicy) -> list[dict[str, Any]]:
    values = [
        ("desired_state", policy.desired_state, "Saved desired position."),
        ("saved_position_state", policy.saved_position_state, "Saved paper position state."),
        ("saved_position_quantity", policy.saved_position_quantity, "Saved absolute QQQ quantity."),
        ("alignment_state", policy.alignment_state, "Saved alignment state."),
        ("no_action_required", str(policy.no_action_required), "No-action policy result."),
    ]
    return [{"evidence_name": name, "evidence_value": value, "details": details, **SAFETY_FLAGS} for name, value, details in values]


def report_row(
    name: str,
    status: str,
    policy: Qqq100FollowupPolicy,
    finding: str,
) -> dict[str, Any]:
    return {
        "check_name": name,
        "policy_status": status,
        "desired_state": policy.desired_state,
        "saved_position_state": policy.saved_position_state,
        "saved_position_quantity": policy.saved_position_quantity,
        "alignment_state": policy.alignment_state,
        "no_action_required": policy.no_action_required,
        "finding": finding,
        "blocker": policy.blocker,
        "recommended_next_step": policy.recommended_next_step,
        **ROW_SAFETY,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "QQQ100 follow-up policy report complete. Saved-output report only; no orders approved.",
        f"Final policy status: {summary_value(summary_rows, 'final_followup_policy_status')}",
        f"Desired state: {summary_value(summary_rows, 'desired_state')}",
        f"Saved position: {summary_value(summary_rows, 'saved_position_state')} quantity={summary_value(summary_rows, 'saved_position_quantity')}",
        f"Alignment state: {summary_value(summary_rows, 'alignment_state')}",
        f"No action required: {summary_value(summary_rows, 'no_action_required')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report/summary/blockers/evidence to {output_paths['report']}; {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false; followup_order_approved=false; repeat_execution_approved=false",
        "Warning: this policy report does not create executable order instructions or approve repeat execution.",
    ]


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
