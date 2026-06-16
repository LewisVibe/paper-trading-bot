"""Saved-output-only QQQ100 repeat/alignment workflow design report.

This module is a design checkpoint only. It reads saved CSV artefacts, writes
static design CSVs, and does not call Alpaca, refresh market data, read live
positions, create orders, write SQLite, send alerts, schedule anything, or
approve repeat execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"
MAX_QQQ_PAPER_POSITION = "1"
FINAL_DESIGN_STATUS = "qqq100_repeat_alignment_design_created"
BIGGEST_BLOCKER = "repeat_execution_requires_separate_manual_approval"
RECOMMENDED_NEXT_STEP = "review_design_before_any_repeat_execution_command_change"

INPUT_FILES = {
    "qqq100_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_postcheck": Path("data/qqq100_paper_postcheck.csv"),
    "paper_execution_state_summary": Path("data/paper_execution_state_summary.csv"),
    "qqq100_readiness": Path("data/qqq100_paper_execution_readiness_report.csv"),
    "portfolio_preview": Path("data/multi_strategy_portfolio_preview.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "alpaca_connectivity": Path("data/alpaca_connectivity_diagnostics.csv"),
}

OUTPUT_FILES = {
    "design": Path("data/qqq100_repeat_alignment_workflow_design.csv"),
    "states": Path("data/qqq100_repeat_alignment_workflow_states.csv"),
    "blockers": Path("data/qqq100_repeat_alignment_workflow_blockers.csv"),
    "checklist": Path("data/qqq100_repeat_alignment_workflow_checklist.csv"),
}

SAFETY_COLUMNS = [
    "report_only",
    "design_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "yfinance_called",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "general_execution_approved",
    "qqq100_execution_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

SAFETY_FLAGS = {
    "report_only": True,
    "design_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "yfinance_called": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    "execution_approved": False,
    "general_execution_approved": False,
    "qqq100_execution_approved": False,
    "followup_order_approved": False,
    "repeat_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

DESIGN_COLUMNS = [
    "created_at",
    "design_name",
    "final_design_status",
    "strategy_name",
    "ticker",
    "current_saved_milestone_state",
    "current_saved_qqq_alignment_state",
    "proposed_max_qqq_paper_position",
    "biggest_blocker",
    "recommended_next_step",
    "details",
    *SAFETY_COLUMNS,
]

STATE_COLUMNS = [
    "created_at",
    "state_name",
    "desired_position",
    "paper_position_state",
    "workflow_label",
    "state_category",
    "allowed_future_state",
    "blocked_state",
    "required_conditions",
    "design_rule",
    "required_next_step",
    *SAFETY_COLUMNS,
]

BLOCKER_COLUMNS = [
    "created_at",
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    *SAFETY_COLUMNS,
]

CHECKLIST_COLUMNS = [
    "created_at",
    "step_number",
    "checklist_item",
    "check_status",
    "details",
    "required_before_repeat_workflow",
    *SAFETY_COLUMNS,
]


@dataclass
class Qqq100RepeatAlignmentWorkflowDesignResult:
    output_paths: dict[str, Path]
    design_rows: list[dict[str, Any]]
    state_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    checklist_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_qqq100_repeat_alignment_workflow_design(
    root_dir: Path | str = ".",
) -> Qqq100RepeatAlignmentWorkflowDesignResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inputs = {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}
    context = build_context(inputs)
    design_rows = build_design_rows(created_at, context)
    state_rows = build_state_rows(created_at)
    blocker_rows = build_blocker_rows(created_at, context)
    checklist_rows = build_checklist_rows(created_at)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["design"], DESIGN_COLUMNS, design_rows)
    write_rows(output_paths["states"], STATE_COLUMNS, state_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["checklist"], CHECKLIST_COLUMNS, checklist_rows)
    return Qqq100RepeatAlignmentWorkflowDesignResult(
        output_paths=output_paths,
        design_rows=design_rows,
        state_rows=state_rows,
        blocker_rows=blocker_rows,
        checklist_rows=checklist_rows,
        summary_lines=build_summary_lines(context, state_rows, output_paths["design"]),
    )


def show_qqq100_repeat_alignment_workflow_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    design_path = root / OUTPUT_FILES["design"]
    states_path = root / OUTPUT_FILES["states"]
    if not design_path.exists() or not states_path.exists():
        return 1, [
            "QQQ100 repeat/alignment workflow design is missing.",
            "Run `python bot.py --qqq100-repeat-alignment-workflow-design` first.",
            "repeat_execution_approved=false; scheduling_approved=false; execution_approved=false",
        ]
    design_rows = read_csv_rows(design_path)
    state_rows = read_csv_rows(states_path)
    design = design_rows[0] if design_rows else {}
    allowed = [row.get("workflow_label", "") for row in state_rows if trueish(row.get("allowed_future_state", ""))]
    blocked = [row.get("workflow_label", "") for row in state_rows if trueish(row.get("blocked_state", ""))]
    return 0, [
        "QQQ100 repeat/alignment workflow design. Saved-output-only design; no repeat execution approved.",
        f"final_design_status: {design.get('final_design_status', 'missing')}",
        f"current saved milestone state: {design.get('current_saved_milestone_state', 'missing')}",
        f"current saved QQQ alignment state: {design.get('current_saved_qqq_alignment_state', 'missing')}",
        f"proposed max QQQ paper position: {design.get('proposed_max_qqq_paper_position', MAX_QQQ_PAPER_POSITION)}",
        f"allowed future states: {', '.join(allowed) if allowed else 'none'}",
        f"blocked states: {', '.join(blocked) if blocked else 'none'}",
        f"biggest blocker: {design.get('biggest_blocker', BIGGEST_BLOCKER)}",
        f"recommended next step: {design.get('recommended_next_step', RECOMMENDED_NEXT_STEP)}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    return {
        "current_saved_milestone_state": saved_summary_value(
            inputs["paper_execution_state_summary"],
            "final_state_summary_status",
            "saved_milestone_state_unavailable",
        ),
        "current_saved_qqq_alignment_state": saved_summary_value(
            inputs["paper_execution_state_summary"],
            "qqq100_alignment_status",
            first_nonempty(inputs["qqq100_postcheck"], ["alignment_state"]) or "saved_alignment_unavailable",
        ),
        "desired_position": first_nonempty(inputs["qqq100_signal"], ["desired_position"])
        or first_nonempty(inputs["qqq100_action_preview"], ["desired_position"])
        or "unavailable",
        "position_status": first_nonempty(inputs["qqq100_postcheck"], ["position_status"])
        or first_nonempty(inputs["qqq100_action_preview"], ["current_position_status"])
        or "unavailable",
        "position_quantity_abs": first_nonempty(inputs["qqq100_postcheck"], ["position_quantity_abs"])
        or first_nonempty(inputs["qqq100_action_preview"], ["current_position_quantity_if_readonly"])
        or "unavailable",
        "alpaca_connectivity_status": first_nonempty(inputs["alpaca_connectivity"], ["diagnostic_status"])
        or "saved_connectivity_unavailable",
        "saved_inputs_present": ", ".join(name for name, rows in inputs.items() if rows) or "none",
    }


def build_design_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    details = (
        "Design for future manual QQQ100 repeat/alignment review only. "
        f"Saved desired_position={context['desired_position']}; "
        f"saved position={context['position_status']} quantity={context['position_quantity_abs']}."
    )
    return [
        {
            "created_at": created_at,
            "design_name": "qqq100_repeat_alignment_workflow_design",
            "final_design_status": FINAL_DESIGN_STATUS,
            "strategy_name": STRATEGY_NAME,
            "ticker": TICKER,
            "current_saved_milestone_state": context["current_saved_milestone_state"],
            "current_saved_qqq_alignment_state": context["current_saved_qqq_alignment_state"],
            "proposed_max_qqq_paper_position": MAX_QQQ_PAPER_POSITION,
            "biggest_blocker": BIGGEST_BLOCKER,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
            "details": details,
            **safety_flags(),
        }
    ]


def build_state_rows(created_at: str) -> list[dict[str, Any]]:
    return [
        state_row(
            created_at,
            "desired_long_position_flat",
            "long",
            "flat",
            "possible_manual_open_long_candidate",
            "allowed_after_manual_review",
            True,
            False,
            "Fresh signal, read-only broker check, market-open preflight, no open QQQ orders, no recent duplicate filled order, explicit manual confirmation.",
            "QQQ only; qqq_100_trend_gate only; max one share.",
            "Separate manual approval required before any future command change.",
        ),
        state_row(
            created_at,
            "desired_long_position_long_one",
            "long",
            "long_1",
            "aligned_long_no_action",
            "allowed_no_action",
            True,
            False,
            "Saved desired long and paper QQQ position already long exactly one share.",
            "No extra buy allowed; no duplicate buy while already long one share.",
            "Keep as no-action state.",
        ),
        state_row(
            created_at,
            "desired_long_position_long_above_one",
            "long",
            "long_above_1",
            "over_allocated_manual_review_required",
            "blocked_manual_review",
            False,
            True,
            "Any QQQ position above one share violates the current manual workflow cap.",
            "No automatic sell or rebalance.",
            "Manual review required; do not add automatic flattening.",
        ),
        state_row(
            created_at,
            "desired_flat_position_flat",
            "flat",
            "flat",
            "aligned_flat_no_action",
            "allowed_no_action",
            True,
            False,
            "Saved desired flat and paper QQQ position flat.",
            "No order is needed.",
            "Keep as no-action state.",
        ),
        state_row(
            created_at,
            "desired_flat_position_long",
            "flat",
            "long",
            "possible_manual_flatten_review",
            "blocked_manual_review",
            False,
            True,
            "Flattening would require a separate explicit review before implementation.",
            "No automatic sell or flatten implementation yet.",
            "Design flatten review separately.",
        ),
        state_row(
            created_at,
            "desired_position_missing_stale_invalid",
            "missing_stale_invalid",
            "any",
            "block_repeat_workflow",
            "blocked",
            False,
            True,
            "Desired position must be fresh, valid, and saved before any future repeat workflow.",
            "No config ticker dependency and no fallback to strategy execution.",
            "Refresh safe QQQ100 preview signal and review saved outputs.",
        ),
        state_row(
            created_at,
            "open_qqq_order_exists",
            "any",
            "any",
            "block_due_to_open_order",
            "blocked",
            False,
            True,
            "A read-only broker check must show no open QQQ order.",
            "Open orders block any future manual repeat command.",
            "Wait or manually review broker state.",
        ),
        state_row(
            created_at,
            "recent_qqq_manual_order_in_cooldown",
            "any",
            "any",
            "block_due_to_recent_order_cooldown",
            "blocked",
            False,
            True,
            "Recent QQQ manual execution or broker order inside the cooldown window blocks repeat use.",
            "Cooldown is duplicate-order protection only; it is not execution approval.",
            "Wait for cooldown or perform manual review.",
        ),
        state_row(
            created_at,
            "market_closed_or_unknown",
            "any",
            "any",
            "block_due_to_market_status",
            "blocked",
            False,
            True,
            "Market-open preflight must be open before any future manual order path.",
            "Market closed or unknown blocks repeat workflow.",
            "Rerun read-only preflight when market state is known.",
        ),
        state_row(
            created_at,
            "broker_unreadable_or_connectivity_failed",
            "any",
            "any",
            "block_due_to_broker_read_failure",
            "blocked",
            False,
            True,
            "Broker/order/position state must be readable through a separately confirmed read-only check.",
            "Connectivity failure blocks repeat workflow.",
            "Resolve broker connectivity before manual review.",
        ),
    ]


def build_blocker_rows(created_at: str, context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        blocker_row(created_at, BIGGEST_BLOCKER, "blocked", "critical", "Future repeat QQQ100 paper execution is not approved by this design.", RECOMMENDED_NEXT_STEP),
        blocker_row(created_at, "followup_order_not_approved", "blocked", "critical", "No follow-up order is approved.", "Require a separate manual confirmation gate before any future order path."),
        blocker_row(created_at, "duplicate_buy_already_long_one_blocked", "blocked", "critical", "If QQQ is already long one share, the only designed state is aligned_long_no_action.", "Do not buy an additional QQQ share."),
        blocker_row(created_at, "max_position_one_share", "blocked", "critical", "Current manual workflow design caps QQQ at one paper share.", "No scaling above one share without separate approval."),
        blocker_row(created_at, "automatic_flatten_not_implemented", "blocked", "high", "Desired flat while long is manual flatten review only.", "Design a separate flatten review before implementation."),
        blocker_row(created_at, "high_growth_and_crypto_excluded", "blocked", "critical", "High-growth and crypto remain research-only and excluded from execution.", "Do not link other branches to QQQ100 repeat workflow."),
        blocker_row(created_at, "scheduling_not_approved", "blocked", "critical", "No scheduling, Hermes cron, loop, service, or Task Scheduler use is approved.", "Keep any future command manual unless separately approved."),
        blocker_row(created_at, "saved_state_context_only", "warning", "medium", f"Saved inputs present: {context['saved_inputs_present']}.", "Use saved context for review only; refresh safe reports separately if stale."),
    ]


def build_checklist_rows(created_at: str) -> list[dict[str, Any]]:
    items = [
        "refresh QQQ100 preview signal",
        "run read-only QQQ100 action preview",
        "run read-only QQQ100 paper postcheck",
        "check saved paper execution state summary",
        "verify desired_position",
        "verify current QQQ paper position",
        "verify no open QQQ orders",
        "verify no recent duplicate order/cooldown issue",
        "verify max QQQ position remains 1 share unless separately approved",
        "verify no high-growth/crypto/other ticker linkage",
        "verify no scheduling approval",
        "require explicit manual confirmation for any future order",
    ]
    return [
        {
            "created_at": created_at,
            "step_number": index,
            "checklist_item": item,
            "check_status": "required_future_manual_review_step",
            "details": "Checklist item for future design review only; this report does not perform the step.",
            "required_before_repeat_workflow": True,
            **safety_flags(),
        }
        for index, item in enumerate(items, start=1)
    ]


def state_row(
    created_at: str,
    state_name: str,
    desired_position: str,
    paper_position_state: str,
    workflow_label: str,
    state_category: str,
    allowed: bool,
    blocked: bool,
    required_conditions: str,
    design_rule: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "state_name": state_name,
        "desired_position": desired_position,
        "paper_position_state": paper_position_state,
        "workflow_label": workflow_label,
        "state_category": state_category,
        "allowed_future_state": allowed,
        "blocked_state": blocked,
        "required_conditions": required_conditions,
        "design_rule": design_rule,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def blocker_row(
    created_at: str,
    blocker_name: str,
    status: str,
    severity: str,
    details: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "blocker_name": blocker_name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": required_next_step,
        **safety_flags(),
    }


def build_summary_lines(context: dict[str, str], state_rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    allowed = [str(row["workflow_label"]) for row in state_rows if row["allowed_future_state"]]
    blocked = [str(row["workflow_label"]) for row in state_rows if row["blocked_state"]]
    return [
        "QQQ100 repeat/alignment workflow design created. Saved-output design only; no repeat execution approved.",
        f"final_design_status: {FINAL_DESIGN_STATUS}",
        f"current saved milestone state: {context['current_saved_milestone_state']}",
        f"current saved QQQ alignment state: {context['current_saved_qqq_alignment_state']}",
        f"proposed max QQQ paper position: {MAX_QQQ_PAPER_POSITION}",
        f"allowed future states: {', '.join(allowed)}",
        f"blocked states: {', '.join(blocked)}",
        f"biggest blocker: {BIGGEST_BLOCKER}",
        f"recommended next step: {RECOMMENDED_NEXT_STEP}",
        f"Saved design: {output_path}",
        "orders_created=false; orders_submitted=false; orders_cancelled=false; orders_replaced=false",
        "execution_approved=false; followup_order_approved=false; repeat_execution_approved=false; scheduling_approved=false",
    ]


def saved_summary_value(rows: list[dict[str, str]], summary_name: str, default: str) -> str:
    for row in rows:
        if row.get("summary_name") == summary_name:
            value = str(row.get("summary_value", "")).strip()
            if value:
                return value
    return default


def first_nonempty(rows: list[dict[str, str]], keys: list[str]) -> str:
    for row in rows:
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
    return ""


def trueish(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


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
