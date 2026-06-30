"""Manual ticket-value design checkpoint for the volatility seed.

This report reads saved outputs only and documents which ticket values would
need a future manual decision. It does not populate side, quantity, order type,
time-in-force, account, broker order id, or any executable order instruction.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_SEED = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"
FINAL_STATUS = "vol_targeted_growth_manual_ticket_value_design_manual_review_required"
FINAL_DECISION = "TICKET_VALUE_DESIGN_REVIEW_ONLY_VALUES_NOT_APPROVED"
NEXT_STEP = "manual_review_ticket_value_design_before_any_executable_ticket_or_order_approval"

OUTPUT_FILES = {
    "report": Path("data/vol_targeted_growth_manual_ticket_value_design.csv"),
    "summary": Path("data/vol_targeted_growth_manual_ticket_value_design_summary.csv"),
    "ticket_values": Path("data/vol_targeted_growth_manual_ticket_value_design_values.csv"),
    "blockers": Path("data/vol_targeted_growth_manual_ticket_value_design_blockers.csv"),
}

INPUT_FILES = {
    "post_gate_review": Path("data/vol_targeted_growth_post_gate_review_summary.csv"),
    "ticket_instance_design": Path("data/vol_targeted_growth_non_submitting_ticket_instance_design_summary.csv"),
    "go_no_go_dashboard": Path("data/paper_live_go_no_go_dashboard_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "ticket_value_design_only": True,
    "non_submitting": True,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
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

REPORT_COLUMNS = [
    "check_name",
    "status",
    "risk_level",
    "evidence",
    "interpretation",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
VALUE_COLUMNS = [
    "ticket_value_field",
    "value_status",
    "draft_value",
    "reason_unpopulated",
    "future_manual_requirement",
    "safety_boundary",
    *SAFETY_FLAGS.keys(),
]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]


@dataclass
class VolTargetedGrowthManualTicketValueDesignResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    value_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_manual_ticket_value_design(
    root_dir: Path | str = ".",
) -> VolTargetedGrowthManualTicketValueDesignResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    context = build_context(inputs)
    report_rows = build_report_rows(context)
    value_rows = build_value_rows(context)
    summary_rows = build_summary_rows(context, value_rows)
    blocker_rows = build_blocker_rows(context, inputs)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["ticket_values"], VALUE_COLUMNS, value_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    return VolTargetedGrowthManualTicketValueDesignResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        value_rows=value_rows,
        blocker_rows=blocker_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_vol_targeted_growth_manual_ticket_value_design(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    summary_path = Path(root_dir) / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Volatility-targeted manual ticket-value design is missing.",
            "Run `python bot.py --vol-targeted-growth-manual-ticket-value-design` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Volatility-targeted manual ticket-value design saved display. Review only; no values approved.",
        f"final_ticket_value_design_status: {summary_value(rows, 'final_ticket_value_design_status')}",
        f"final_ticket_value_design_decision: {summary_value(rows, 'final_ticket_value_design_decision')}",
        f"active_seed: {summary_value(rows, 'active_seed')}",
        f"post_gate_review_status: {summary_value(rows, 'post_gate_review_status')}",
        f"saved_qqq_position_quantity_if_readonly: {summary_value(rows, 'saved_qqq_position_quantity_if_readonly')}",
        f"ticket_value_field_count: {summary_value(rows, 'ticket_value_field_count')}",
        f"populated_ticket_value_count: {summary_value(rows, 'populated_ticket_value_count')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "order_instructions_created=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: this is design/review only; side, quantity, order type, time-in-force, account, and broker order id stay blank.",
    ]


def build_context(inputs: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    post_gate = inputs["post_gate_review"]
    return {
        "post_gate_review_status": summary_value(post_gate, "final_post_gate_review_status") or "missing_post_gate_review",
        "post_gate_review_decision": summary_value(post_gate, "final_post_gate_review_decision") or "missing_post_gate_review_decision",
        "saved_qqq_position_quantity_if_readonly": summary_value(post_gate, "saved_qqq_position_quantity_if_readonly") or "unavailable",
        "ticket_instance_design_decision": summary_value(inputs["ticket_instance_design"], "final_ticket_instance_design_decision") or "missing_ticket_instance_design",
        "go_no_go_decision": summary_value(inputs["go_no_go_dashboard"], "final_go_no_go_decision") or "missing_go_no_go_dashboard",
    }


def build_report_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    return [
        report_row(
            "post_gate_context",
            "manual_review_required",
            "high",
            context["post_gate_review_decision"],
            "Saved broker context exists only as review evidence; it does not approve values.",
            "review_post_gate_context_before_values",
        ),
        report_row(
            "ticket_value_scope",
            "design_only",
            "critical",
            f"{ACTIVE_SEED}/{ACTIVE_TICKER}",
            "Ticket value design is scoped to the active volatility seed only.",
            NEXT_STEP,
        ),
        report_row(
            "order_value_boundary",
            "blocked",
            "critical",
            "side_quantity_order_type_time_in_force_account_broker_id_blank",
            "No executable order values are populated.",
            "separate_explicit_order_value_approval_required",
        ),
        report_row(
            "go_no_go_boundary",
            "blocked",
            "critical",
            context["go_no_go_decision"],
            "The paper-live go/no-go dashboard remains no-go for execution.",
            "keep_go_no_go_blocking_execution",
        ),
    ]


def build_value_rows(context: dict[str, str]) -> list[dict[str, Any]]:
    rows = [
        ("strategy_name", "context_only", ACTIVE_SEED, "Strategy context is not an order value.", f"Must remain scoped to {ACTIVE_SEED}.", "Not executable."),
        ("ticker_scope", "context_only", ACTIVE_TICKER, "Portfolio label is not a broker symbol order.", f"Must remain scoped to {ACTIVE_TICKER}.", "Not executable."),
        ("previous_seed_context", "context_only", f"{PREVIOUS_SEED}/{PREVIOUS_TICKER}", "Previous seed context is not a repeat order.", "Must preserve QQQ100 no-repeat boundary.", "No QQQ repeat order approved."),
        ("saved_qqq_position_context", "context_only", context["saved_qqq_position_quantity_if_readonly"], "Saved QQQ quantity is review evidence only.", "Manual review must consider existing QQQ exposure.", "No follow-up order approved."),
        ("order_side", "blocked_blank", "", "Side is not approved.", "Requires separate explicit value approval.", "No buy/sell instruction."),
        ("order_quantity", "blocked_blank", "", "Quantity is not approved.", "Requires separate exact sizing review.", "No quantity instruction."),
        ("order_type", "blocked_blank", "", "Order type is not approved.", "Requires separate order-design approval.", "No market/limit instruction."),
        ("time_in_force", "blocked_blank", "", "Time-in-force is not approved.", "Requires separate order-design approval.", "No routing instruction."),
        ("account_reference", "forbidden_blank", "", "Account identifiers must never be stored here.", "Do not store account IDs.", "No account identifiers."),
        ("broker_order_id", "forbidden_blank", "", "Broker order IDs do not exist in design reports.", "Do not store broker order IDs.", "No broker IDs."),
        ("submit_ready", "blocked_false", "False", "The design cannot be submitted.", "Requires a later executable-ticket approval chain.", "Not executable."),
    ]
    return [value_row(*item) for item in rows]


def build_summary_rows(context: dict[str, str], value_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    populated_count = sum(1 for row in value_rows if row["value_status"] not in {"blocked_blank", "forbidden_blank", "blocked_false", "context_only"})
    data = [
        ("final_ticket_value_design_status", FINAL_STATUS, "Manual ticket-value design checkpoint status."),
        ("final_ticket_value_design_decision", FINAL_DECISION, "No ticket values are approved."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("active_ticker", ACTIVE_TICKER, "Current report/status ticker label."),
        ("previous_seed", PREVIOUS_SEED, "Previous QQQ100 seed context."),
        ("previous_ticker", PREVIOUS_TICKER, "Previous QQQ100 ticker context."),
        ("post_gate_review_status", context["post_gate_review_status"], "Saved post-gate review status."),
        ("post_gate_review_decision", context["post_gate_review_decision"], "Saved post-gate review decision."),
        ("saved_qqq_position_quantity_if_readonly", context["saved_qqq_position_quantity_if_readonly"], "Saved QQQ quantity from prior read-only gate."),
        ("ticket_instance_design_decision", context["ticket_instance_design_decision"], "Saved non-submitting ticket-instance design decision."),
        ("go_no_go_decision", context["go_no_go_decision"], "Saved go/no-go dashboard decision."),
        ("ticket_value_field_count", str(len(value_rows)), "Number of ticket value fields reviewed."),
        ("populated_ticket_value_count", str(populated_count), "Executable ticket value count."),
        ("order_values_populated", "False", "No executable order values are populated."),
        ("order_instructions_created", "False", "No order instruction exists."),
        ("executable_ticket_created", "False", "No executable ticket exists."),
        ("largest_blocker", "ticket_values_not_approved", "Primary blocker."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any future executable-ticket or order approval."),
    ]
    return [summary_row(*item) for item in data]


def build_blocker_rows(context: dict[str, str], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = [
        ("ticket_values_not_approved", "blocked", "critical", "Side, quantity, order type, time-in-force, account, and broker order id remain blank.", NEXT_STEP),
        ("executable_ticket_not_created", "blocked", "critical", "No executable ticket exists.", "separate_executable_ticket_checkpoint_required"),
        ("execution_not_approved", "blocked", "critical", "No paper execution, live trading, repeat order, or scheduling is approved.", "keep_all_approval_flags_false"),
    ]
    if context["go_no_go_decision"] != "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY":
        rows.insert(0, ("go_no_go_state_unexpected", "blocked", "high", context["go_no_go_decision"], "review_go_no_go_dashboard"))
    for name, path in INPUT_FILES.items():
        if not inputs[name]:
            rows.insert(0, (f"missing_{name}", "blocked", "high", f"Saved input is missing: {path}", f"refresh_{name}_report_only"))
    return [blocker_row(*item) for item in rows]


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Volatility-targeted manual ticket-value design complete. Review only; no executable ticket or execution approved.",
        f"final_ticket_value_design_status={summary_value(summary_rows, 'final_ticket_value_design_status')}",
        f"final_ticket_value_design_decision={summary_value(summary_rows, 'final_ticket_value_design_decision')}",
        f"active_seed={summary_value(summary_rows, 'active_seed')}",
        f"post_gate_review_decision={summary_value(summary_rows, 'post_gate_review_decision')}",
        f"saved_qqq_position_quantity_if_readonly={summary_value(summary_rows, 'saved_qqq_position_quantity_if_readonly')}",
        f"ticket_value_field_count={summary_value(summary_rows, 'ticket_value_field_count')}",
        f"populated_ticket_value_count={summary_value(summary_rows, 'populated_ticket_value_count')}",
        f"order_values_populated={summary_value(summary_rows, 'order_values_populated')}",
        f"largest_blocker={summary_value(summary_rows, 'largest_blocker')}",
        f"recommended_next_step={summary_value(summary_rows, 'recommended_next_step')}",
        f"saved_report={output_paths['report']}",
        "order_instructions_created=false; executable_ticket_created=false; orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def report_row(name: str, status: str, risk: str, evidence: str, interpretation: str, next_step: str) -> dict[str, Any]:
    return {
        "check_name": name,
        "status": status,
        "risk_level": risk,
        "evidence": evidence,
        "interpretation": interpretation,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def value_row(field: str, status: str, value: str, reason: str, requirement: str, boundary: str) -> dict[str, Any]:
    return {
        "ticket_value_field": field,
        "value_status": status,
        "draft_value": value,
        "reason_unpopulated": reason,
        "future_manual_requirement": requirement,
        "safety_boundary": boundary,
        **SAFETY_FLAGS,
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {"blocker_name": name, "status": status, "severity": severity, "details": details, "required_next_step": next_step, **SAFETY_FLAGS}


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
