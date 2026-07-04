"""Concrete sleeve mapping and non-executable action proposal for the volatility seed.

The goal is to move from abstract sleeves to reviewable broker symbols without
creating orders. Symbols and target weights are populated for manual review,
but side, quantity, order type, account, and submission fields remain blank.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_SEED = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
MAPPING_STATUS = "vol_targeted_growth_sleeve_symbol_mapping_created_manual_review_required"
MAPPING_DECISION = "SLEEVE_SYMBOL_MAPPING_PROPOSED_REVIEW_ONLY_NOT_APPROVED"
ACTION_STATUS = "vol_targeted_growth_broker_ready_action_proposal_created_manual_review_required"
ACTION_DECISION = "BROKER_SYMBOL_ACTION_PROPOSAL_CREATED_NO_ORDER_INSTRUCTIONS"
NEXT_STEP = "manual_review_sleeve_symbol_mapping_and_action_proposal_before_any_order_values"

SLEEVE_MAPPINGS = [
    {
        "sleeve_name": "qqq100_core_trend_sleeve",
        "target_weight": "0.70",
        "broker_symbol": "QQQ",
        "instrument_type": "etf",
        "mapping_status": "candidate_symbol_review_required",
        "mapping_reason": "Existing clean QQQ100 paper context and obvious single-symbol proxy.",
        "risk_note": "Existing QQQ paper exposure must be reviewed before any future order.",
    },
    {
        "sleeve_name": "high_growth_stock_research_sleeve",
        "target_weight": "0.20",
        "broker_symbol": "MGK",
        "instrument_type": "etf",
        "mapping_status": "candidate_proxy_review_required",
        "mapping_reason": "Liquid broad mega-cap growth ETF proxy avoids single-stock concentration.",
        "risk_note": "This is not approval to promote the high-growth research sleeve.",
    },
    {
        "sleeve_name": "crypto_research_sleeve",
        "target_weight": "0.05",
        "broker_symbol": "IBIT",
        "instrument_type": "spot_bitcoin_etf",
        "mapping_status": "candidate_proxy_review_required",
        "mapping_reason": "Liquid BTC ETF proxy for review if crypto exposure is ever allowed.",
        "risk_note": "Crypto execution policy remains unapproved.",
    },
    {
        "sleeve_name": "defensive_cash_or_bond_sleeve",
        "target_weight": "0.05",
        "broker_symbol": "SGOV",
        "instrument_type": "treasury_bill_etf",
        "mapping_status": "candidate_proxy_review_required",
        "mapping_reason": "Short Treasury ETF proxy for defensive/cash-like sleeve review.",
        "risk_note": "Defensive proxy must be manually accepted before use.",
    },
]

MAPPING_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_sleeve_symbol_mapping.csv"),
    "summary": Path("data/vol_targeted_growth_sleeve_symbol_mapping_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_sleeve_symbol_mapping_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_sleeve_symbol_mapping_evidence.csv"),
}

ACTION_OUTPUTS = {
    "report": Path("data/vol_targeted_growth_broker_ready_action_proposal.csv"),
    "summary": Path("data/vol_targeted_growth_broker_ready_action_proposal_summary.csv"),
    "blockers": Path("data/vol_targeted_growth_broker_ready_action_proposal_blockers.csv"),
    "evidence": Path("data/vol_targeted_growth_broker_ready_action_proposal_evidence.csv"),
}

INPUT_FILES = {
    "preview_signal": Path("data/vol_targeted_growth_preview_signal_summary.csv"),
    "action_preview": Path("data/vol_targeted_growth_action_preview_summary.csv"),
    "fresh_broker_gate": Path("data/vol_targeted_growth_fresh_broker_pre_ticket_gate_run_summary.csv"),
    "ticket_instance_checkpoint": Path("data/vol_targeted_growth_non_submitting_ticket_instance_checkpoint_summary.csv"),
}

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "saved_output_only": True,
    "manual_review_only": True,
    "preview_only": True,
    "sleeve_symbol_mapping_created": True,
    "broker_symbol_mapping_populated": True,
    "broker_ready_action_proposal_created": False,
    "broker_ready_order_values_populated": False,
    "order_values_populated": False,
    "order_instructions_created": False,
    "ticket_instance_created": False,
    "executable_ticket_created": False,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "orders_replaced": False,
    "alpaca_called": False,
    "broker_positions_read": False,
    "paper_positions_read": False,
    "market_data_refreshed": False,
    "yfinance_called": False,
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

MAPPING_COLUMNS = [
    "sleeve_name",
    "target_weight",
    "broker_symbol",
    "instrument_type",
    "mapping_status",
    "mapping_reason",
    "risk_note",
    "manual_review_required",
    *SAFETY_FLAGS.keys(),
]
ACTION_COLUMNS = [
    "sleeve_name",
    "target_weight",
    "broker_symbol",
    "proposal_status",
    "proposed_action_label",
    "order_side",
    "order_quantity",
    "order_type",
    "time_in_force",
    "account_reference",
    "broker_order_id",
    "reason",
    "required_next_step",
    *SAFETY_FLAGS.keys(),
]
SUMMARY_COLUMNS = ["summary_name", "summary_value", "details", *SAFETY_FLAGS.keys()]
BLOCKER_COLUMNS = ["blocker_name", "status", "severity", "details", "required_next_step", *SAFETY_FLAGS.keys()]
EVIDENCE_COLUMNS = ["evidence_name", "evidence_value", "details", *SAFETY_FLAGS.keys()]


@dataclass
class MappingProposalResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_vol_targeted_growth_sleeve_symbol_mapping(root_dir: Path | str = ".") -> MappingProposalResult:
    root = Path(root_dir)
    inputs = load_inputs(root)
    report_rows = [mapping_row(item) for item in SLEEVE_MAPPINGS]
    summary_rows = mapping_summary_rows(inputs, report_rows)
    blocker_rows = common_blockers("mapping_not_approved")
    evidence_rows = evidence_rows_for(inputs)
    output_paths = write_outputs(root, MAPPING_OUTPUTS, MAPPING_COLUMNS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return MappingProposalResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, mapping_lines(summary_rows, output_paths["report"]))


def show_vol_targeted_growth_sleeve_symbol_mapping(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / MAPPING_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted sleeve-symbol mapping is missing.",
            "Run `python bot.py --vol-targeted-growth-sleeve-symbol-mapping` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted sleeve-symbol mapping saved display. Review only; no order values.",
        f"final_sleeve_symbol_mapping_status: {summary_value(rows, 'final_sleeve_symbol_mapping_status')}",
        f"final_sleeve_symbol_mapping_decision: {summary_value(rows, 'final_sleeve_symbol_mapping_decision')}",
        f"mapped_symbol_count: {summary_value(rows, 'mapped_symbol_count')}",
        f"mapped_symbols: {summary_value(rows, 'mapped_symbols')}",
        f"mapping_approved: {summary_value(rows, 'mapping_approved')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def generate_vol_targeted_growth_broker_ready_action_proposal(root_dir: Path | str = ".") -> MappingProposalResult:
    root = Path(root_dir)
    inputs = {**load_inputs(root), "mapping": read_csv_rows(root / MAPPING_OUTPUTS["report"])}
    mapping_rows = inputs["mapping"] or [mapping_row(item) for item in SLEEVE_MAPPINGS]
    report_rows = [action_row(row) for row in mapping_rows]
    summary_rows = action_summary_rows(inputs, report_rows)
    blocker_rows = common_blockers("broker_ready_order_values_not_approved")
    evidence_rows = evidence_rows_for(inputs)
    output_paths = write_outputs(root, ACTION_OUTPUTS, ACTION_COLUMNS, report_rows, summary_rows, blocker_rows, evidence_rows)
    return MappingProposalResult(output_paths, report_rows, summary_rows, blocker_rows, evidence_rows, action_lines(summary_rows, output_paths["report"]))


def show_vol_targeted_growth_broker_ready_action_proposal(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    path = Path(root_dir) / ACTION_OUTPUTS["summary"]
    if not path.exists():
        return 1, [
            "Volatility-targeted broker-ready action proposal is missing.",
            "Run `python bot.py --vol-targeted-growth-broker-ready-action-proposal` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(path)
    return 0, [
        "Volatility-targeted broker-ready action proposal saved display. Real symbols only; no order instructions.",
        f"final_broker_ready_action_proposal_status: {summary_value(rows, 'final_broker_ready_action_proposal_status')}",
        f"final_broker_ready_action_proposal_decision: {summary_value(rows, 'final_broker_ready_action_proposal_decision')}",
        f"proposal_row_count: {summary_value(rows, 'proposal_row_count')}",
        f"broker_symbols: {summary_value(rows, 'broker_symbols')}",
        f"broker_ready_action_proposal_created: {summary_value(rows, 'broker_ready_action_proposal_created')}",
        f"order_values_populated: {summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created: {summary_value(rows, 'order_instructions_created')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def mapping_row(item: dict[str, str]) -> dict[str, Any]:
    return {
        **item,
        "manual_review_required": True,
        **SAFETY_FLAGS,
    }


def action_row(row: dict[str, Any]) -> dict[str, Any]:
    flags = dict(SAFETY_FLAGS)
    flags["broker_ready_action_proposal_created"] = True
    return {
        "sleeve_name": row.get("sleeve_name", ""),
        "target_weight": row.get("target_weight", ""),
        "broker_symbol": row.get("broker_symbol", ""),
        "proposal_status": "real_symbol_review_only_no_order_values",
        "proposed_action_label": "manual_review_required_no_buy_sell_instruction",
        "order_side": "",
        "order_quantity": "",
        "order_type": "",
        "time_in_force": "",
        "account_reference": "",
        "broker_order_id": "",
        "reason": "Real broker symbol is present for review, but side and quantity require a later explicit order-value approval.",
        "required_next_step": NEXT_STEP,
        **flags,
    }


def mapping_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = [
        ("final_sleeve_symbol_mapping_status", MAPPING_STATUS, "Concrete sleeve-to-symbol mapping exists for manual review only."),
        ("final_sleeve_symbol_mapping_decision", MAPPING_DECISION, "Mappings are proposed but not approved for execution."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("mapped_symbol_count", str(len(rows)), "Number of mapped review symbols."),
        ("mapped_symbols", ",".join(row["broker_symbol"] for row in rows), "Review symbols only."),
        ("mapping_approved", "False", "Separate manual approval required."),
        ("broker_ready_order_values_populated", "False", "No side/quantity/order values exist."),
        ("order_values_populated", "False", "No executable order values exist."),
        ("order_instructions_created", "False", "No buy/sell instructions exist."),
        ("missing_saved_input_count", str(sum(1 for value in inputs.values() if not value)), "Missing saved context count."),
        ("recommended_next_step", "manual_review_mapping_before_action_proposal", "Review mapped symbols before action proposal."),
    ]
    return [summary_row(*item) for item in data]


def action_summary_rows(inputs: dict[str, list[dict[str, str]]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flags = dict(SAFETY_FLAGS)
    flags["broker_ready_action_proposal_created"] = True
    data = [
        ("final_broker_ready_action_proposal_status", ACTION_STATUS, "Real-symbol proposal exists for manual review only."),
        ("final_broker_ready_action_proposal_decision", ACTION_DECISION, "No order instructions or order values are created."),
        ("active_seed", ACTIVE_SEED, "Current report/status seed."),
        ("proposal_row_count", str(len(rows)), "Number of proposal rows."),
        ("broker_symbols", ",".join(row.get("broker_symbol", "") for row in rows), "Real symbols for review only."),
        ("broker_ready_action_proposal_created", "True", "A real-symbol proposal artifact exists."),
        ("broker_ready_order_values_populated", "False", "No side/quantity/order values exist."),
        ("order_values_populated", "False", "No executable order values exist."),
        ("order_instructions_created", "False", "No buy/sell instructions exist."),
        ("mapping_decision", summary_value(inputs.get("mapping", []), "final_sleeve_symbol_mapping_decision") or MAPPING_DECISION, "Mapping context."),
        ("recommended_next_step", NEXT_STEP, "Manual review before any order values."),
    ]
    return [summary_row(*item, flags=flags) for item in data]


def common_blockers(name: str) -> list[dict[str, Any]]:
    return [
        blocker_row(name, "blocked", "critical", "Mappings/proposals are review-only and not approved.", NEXT_STEP),
        blocker_row("order_values_not_populated", "blocked", "critical", "order_side and order_quantity remain blank.", "separate_future_order_value_approval_required"),
        blocker_row("execution_not_approved", "blocked", "critical", "execution_approved=false; paper_execution_approved=false", "keep_execution_blocked"),
        blocker_row("scheduling_not_approved", "blocked", "critical", "scheduling_approved=false", "keep_order_capable_commands_unscheduled"),
    ]


def evidence_rows_for(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows = []
    for name, path in INPUT_FILES.items():
        rows.append(evidence_row(f"{name}_input", f"{path}; rows={len(inputs.get(name, []))}", "Saved input row count."))
    if "mapping" in inputs:
        rows.append(evidence_row("mapping_input", f"{MAPPING_OUTPUTS['report']}; rows={len(inputs.get('mapping', []))}", "Saved mapping row count."))
    rows.append(evidence_row("runtime_boundary", "saved_output_only_no_broker_or_market_refresh", "No Alpaca, yfinance, config, positions, order, alert, SQLite, or scheduling path is used."))
    return rows


def load_inputs(root: Path) -> dict[str, list[dict[str, str]]]:
    return {name: read_csv_rows(root / path) for name, path in INPUT_FILES.items()}


def write_outputs(
    root: Path,
    outputs: dict[str, Path],
    report_columns: list[str],
    report_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    paths = {name: root / path for name, path in outputs.items()}
    write_rows(paths["report"], report_columns, report_rows)
    write_rows(paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return paths


def mapping_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Sleeve-symbol mapping complete. Review only; no order values approved.",
        f"final_sleeve_symbol_mapping_status={summary_value(rows, 'final_sleeve_symbol_mapping_status')}",
        f"final_sleeve_symbol_mapping_decision={summary_value(rows, 'final_sleeve_symbol_mapping_decision')}",
        f"mapped_symbols={summary_value(rows, 'mapped_symbols')}",
        f"mapping_approved={summary_value(rows, 'mapping_approved')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def action_lines(rows: list[dict[str, Any]], report_path: Path) -> list[str]:
    return [
        "Broker-ready action proposal complete. Real symbols only; no order instructions approved.",
        f"final_broker_ready_action_proposal_status={summary_value(rows, 'final_broker_ready_action_proposal_status')}",
        f"final_broker_ready_action_proposal_decision={summary_value(rows, 'final_broker_ready_action_proposal_decision')}",
        f"broker_symbols={summary_value(rows, 'broker_symbols')}",
        f"broker_ready_action_proposal_created={summary_value(rows, 'broker_ready_action_proposal_created')}",
        f"order_values_populated={summary_value(rows, 'order_values_populated')}",
        f"order_instructions_created={summary_value(rows, 'order_instructions_created')}",
        f"saved_report={report_path}",
        "orders_submitted=false; execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
    ]


def summary_row(name: str, value: str, details: str, *, flags: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **(flags or SAFETY_FLAGS)}


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
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""
