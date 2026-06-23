"""Saved-output paper-live promotion gate for the first QQQ100 candidate.

This gate is report-only. It reads saved CSV evidence and static verifier
presence only. It does not call Alpaca, read positions, create order
instructions, submit/cancel/replace orders, write SQLite, send alerts, load
config, schedule anything, or connect strategy output to execution.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"
ADAPTIVE_ALTERNATIVE = "codex_qqq_adaptive_trend_exposure"
REJECTED_QQQ_REFERENCE = "qqq_150_trend_gate"

OUTPUT_FILES = {
    "gate": Path("data/paper_live_promotion_gate.csv"),
    "summary": Path("data/paper_live_promotion_gate_summary.csv"),
    "blockers": Path("data/paper_live_promotion_gate_blockers.csv"),
    "evidence": Path("data/paper_live_promotion_gate_evidence.csv"),
}

SAVED_EVIDENCE_FILES = {
    "qqq100_preview_candidate_readiness": Path("data/qqq100_preview_candidate_readiness_summary.csv"),
    "qqq100_preview_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview_summary.csv"),
    "qqq100_paper_readiness_blockers": Path("data/qqq100_paper_readiness_blocker_summary.csv"),
    "qqq100_paper_execution_readiness": Path("data/qqq100_paper_execution_readiness_summary.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "multi_strategy_portfolio_preview": Path("data/multi_strategy_portfolio_preview.csv"),
    "execution_eligibility": Path("data/execution_eligibility_report.csv"),
    "paper_execution_protection": Path("data/paper_execution_protection_report.csv"),
    "paper_kill_switch_gate": Path("data/paper_kill_switch_gate_report.csv"),
    "project_research_state": Path("data/project_research_state_summary.csv"),
}

STATIC_VERIFIERS = {
    "baseline_freeze": Path("scripts/verify_paper_live_baseline_freeze.py"),
    "qqq100_exact_alignment": Path("scripts/verify_qqq100_exact_alignment.py"),
    "qqq100_paper_execution": Path("scripts/verify_execute_qqq100_paper.py"),
}

GATE_COLUMNS = [
    "check_name",
    "check_status",
    "promotion_label",
    "candidate_strategy",
    "ticker",
    "paper_live_candidate",
    "finding",
    "evidence_source",
    "blocker",
    "required_next_step",
    "research_only",
    "report_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "order_instructions_created",
    "alpaca_called",
    "positions_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]

SUMMARY_COLUMNS = [
    "summary_name",
    "summary_value",
    "details",
    "research_only",
    "report_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]

BLOCKER_COLUMNS = [
    "blocker_name",
    "status",
    "severity",
    "details",
    "required_next_step",
    "research_only",
    "report_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]

EVIDENCE_COLUMNS = [
    "evidence_name",
    "evidence_status",
    "evidence_source",
    "details",
    "research_only",
    "report_only",
    "preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]

SAFETY_FLAGS = {
    "research_only": True,
    "report_only": True,
    "preview_only": True,
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
}

GATE_SAFETY_FLAGS = {
    **SAFETY_FLAGS,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
}


@dataclass
class PaperLivePromotionGateResult:
    output_paths: dict[str, Path]
    gate_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_promotion_gate(root_dir: Path | str = ".") -> PaperLivePromotionGateResult:
    root = Path(root_dir)
    saved_inputs = {name: read_csv_rows(root / path) for name, path in SAVED_EVIDENCE_FILES.items()}
    static_inputs = {name: (root / path).exists() for name, path in STATIC_VERIFIERS.items()}
    context = build_context(saved_inputs, static_inputs)
    gate_rows = build_gate_rows(context)
    evidence_rows = build_evidence_rows(saved_inputs, static_inputs)
    blocker_rows = build_blocker_rows(context)
    summary_rows = build_summary_rows(context)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["gate"], GATE_COLUMNS, gate_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLivePromotionGateResult(
        output_paths=output_paths,
        gate_rows=gate_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_promotion_gate(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live promotion gate is missing.",
            "Run `python bot.py --paper-live-promotion-gate` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live promotion gate saved display. Report only; no execution approved.",
        f"final_promotion_gate_status: {summary_value(rows, 'final_promotion_gate_status')}",
        f"candidate_strategy: {summary_value(rows, 'candidate_strategy')}",
        f"paper_live_candidate: {summary_value(rows, 'paper_live_candidate')}",
        f"candidate_scope: {summary_value(rows, 'candidate_scope')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: paper_live_candidate is discussion status only, not order approval.",
    ]


def build_context(
    saved_inputs: dict[str, list[dict[str, Any]]],
    static_inputs: dict[str, bool],
) -> dict[str, Any]:
    missing_saved = [name for name, rows in saved_inputs.items() if not rows]
    missing_static = [name for name, present in static_inputs.items() if not present]
    hard_blockers = []
    if missing_static:
        hard_blockers.append("static_verifier_missing")
    required_saved = [
        "qqq100_preview_candidate_readiness",
        "qqq100_preview_signal",
        "qqq100_action_preview",
        "qqq100_paper_readiness_blockers",
        "qqq100_paper_execution_readiness",
        "portfolio_risk_policy",
        "execution_eligibility",
        "paper_execution_protection",
    ]
    missing_required_saved = [name for name in required_saved if name in missing_saved]
    if missing_required_saved:
        hard_blockers.append("missing_required_saved_evidence")

    if hard_blockers:
        final_status = "paper_live_promotion_blocked_manual_review_required"
        paper_live_candidate = False
        largest_blocker = hard_blockers[0]
        next_step = "regenerate_or_review_missing_saved_static_evidence_before_candidate_label"
    else:
        final_status = "paper_live_candidate_ready_for_manual_discussion"
        paper_live_candidate = True
        largest_blocker = "explicit_human_approval_still_required"
        next_step = "manual_discussion_only_before_any_separate_paper_execution_prompt"

    return {
        "final_status": final_status,
        "paper_live_candidate": paper_live_candidate,
        "largest_blocker": largest_blocker,
        "recommended_next_step": next_step,
        "missing_saved": missing_saved,
        "missing_required_saved": missing_required_saved,
        "missing_static": missing_static,
    }


def build_gate_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    paper_live_candidate = bool(context["paper_live_candidate"])
    return [
        gate_row("candidate_scope", "pass", "qqq100_only_first_paper_live_candidate", paper_live_candidate, f"{STRATEGY_NAME} / {TICKER} is the only supported first paper-live candidate.", "static policy", "none_for_candidate_scope", "Keep all other strategies excluded from paper-live promotion."),
        gate_row("adaptive_alternative", "pass", "adaptive_qqq_ambitious_alternative_only", paper_live_candidate, f"{ADAPTIVE_ALTERNATIVE} remains an ambitious alternative only.", "saved QQQ decision context", "none_for_adaptive_alternative", "Do not promote adaptive QQQ in this gate."),
        gate_row("qqq150_rejected", "pass", "qqq150_high_drawdown_reference_rejected", paper_live_candidate, f"{REJECTED_QQQ_REFERENCE} remains rejected.", "saved QQQ decision context", "none_for_qqq150_reference", "Do not promote QQQ150."),
        gate_row("sma_slow_sma_excluded", "pass", "sma_and_slow_sma_not_paper_live_candidates", paper_live_candidate, "SMA and slow-SMA are excluded from first paper-live promotion.", "docs/PAPER_LIVE_CHECKLIST.md", "none_for_sma_exclusion", "Keep SMA/slow-SMA out of paper-live promotion."),
        gate_row("high_growth_excluded", "pass", "high_growth_research_only", paper_live_candidate, "High-growth remains research-only.", "saved high-growth research context", "high_growth_not_paper_live_candidate", "Do not promote high-growth in this gate."),
        gate_row("crypto_excluded", "pass", "crypto_research_only", paper_live_candidate, "Crypto remains research-only.", "saved crypto research context", "crypto_not_paper_live_candidate", "Do not promote crypto in this gate."),
        gate_row("qqq100_exact_alignment_verifier", status_for_missing("qqq100_exact_alignment", context["missing_static"]), "qqq100_exact_alignment_verifier_present", paper_live_candidate, "QQQ100 exact zero/one-share alignment verifier exists.", "scripts/verify_qqq100_exact_alignment.py", blocker_for_missing("qqq100_exact_alignment", context["missing_static"]), "Run the verifier before manual discussion."),
        gate_row("baseline_freeze_verifier", status_for_missing("baseline_freeze", context["missing_static"]), "baseline_freeze_verifier_present", paper_live_candidate, "Baseline-freeze verifier exists.", "scripts/verify_paper_live_baseline_freeze.py", blocker_for_missing("baseline_freeze", context["missing_static"]), "Run the verifier before manual discussion."),
        gate_row("saved_qqq100_research_preview_action_readiness", "pass" if not context["missing_required_saved"] else "blocked", "saved_evidence_required", paper_live_candidate, "Saved QQQ100 research/preview/action/readiness evidence is required where expected.", "saved CSV evidence inventory", "none" if not context["missing_required_saved"] else "missing_required_saved_evidence", "Regenerate missing safe saved report outputs before candidate label."),
        gate_row("portfolio_risk_review", status_for_missing("portfolio_risk_policy", context["missing_saved"]), "portfolio_risk_review_required", paper_live_candidate, "Portfolio/risk review evidence is required or listed as a blocker.", "data/portfolio_risk_policy_report.csv", blocker_for_missing("portfolio_risk_policy", context["missing_saved"]), "Review portfolio risk before any paper execution discussion."),
        gate_row("execution_readiness_review", status_for_missing("qqq100_paper_execution_readiness", context["missing_saved"]), "execution_readiness_evidence_required", paper_live_candidate, "Execution-readiness evidence is required or listed as a blocker.", "data/qqq100_paper_execution_readiness_summary.csv", blocker_for_missing("qqq100_paper_execution_readiness", context["missing_saved"]), "Review execution readiness before any paper command."),
        gate_row("human_approval_boundary", "blocked", "explicit_human_approval_still_required", paper_live_candidate, "Explicit human approval is still required before any future manually confirmed paper execution command.", "manual approval boundary", "human_approval_required", "Use a separate prompt before any paper execution command."),
        gate_row("execution_flags", "pass", "execution_flags_false", paper_live_candidate, "General execution, paper execution, and scheduling approvals remain false.", "report schema", "none_for_false_approval_flags", "Keep false approval flags in every row."),
    ]


def build_evidence_rows(
    saved_inputs: dict[str, list[dict[str, Any]]],
    static_inputs: dict[str, bool],
) -> list[dict[str, Any]]:
    rows = [
        evidence_row("candidate_strategy", "pass", STRATEGY_NAME, "Only QQQ100 is supported by this gate."),
        evidence_row("ticker", "pass", TICKER, "Only QQQ is supported by this gate."),
        evidence_row("paper_live_meaning", "pass", "paper_live_candidate_is_discussion_only", "Candidate status does not approve execution, paper execution, or scheduling."),
    ]
    rows.extend(
        evidence_row(name, "present" if present else "missing", str(STATIC_VERIFIERS[name]), "Static verifier presence check.")
        for name, present in static_inputs.items()
    )
    rows.extend(
        evidence_row(name, "present" if rows_ else "missing", str(SAVED_EVIDENCE_FILES[name]), "Saved CSV evidence presence check.")
        for name, rows_ in saved_inputs.items()
    )
    return rows


def build_blocker_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("human_approval_required", "blocked", "critical", "Human approval is required before any future manually confirmed paper execution command.", "Use a separate explicit execution prompt only after review."),
        blocker_row("execution_not_approved", "blocked", "critical", "This gate does not approve execution or paper execution.", "Do not create, prepare, submit, cancel, or replace orders."),
        blocker_row("scheduling_not_approved", "blocked", "critical", "This gate does not approve scheduling.", "Do not schedule order-capable commands."),
    ]
    for name in context["missing_static"]:
        rows.append(blocker_row(f"missing_static_verifier_{name}", "blocked", "critical", f"Missing static verifier: {name}.", "Add or restore the verifier before candidate discussion."))
    for name in context["missing_required_saved"]:
        rows.append(blocker_row(f"missing_required_saved_evidence_{name}", "blocked", "high", f"Missing saved evidence: {name}.", "Run or review the corresponding safe report command before candidate discussion."))
    optional_missing = sorted(set(context["missing_saved"]) - set(context["missing_required_saved"]))
    for name in optional_missing:
        rows.append(blocker_row(f"missing_optional_saved_evidence_{name}", "warning", "medium", f"Optional saved context missing: {name}.", "Regenerate only if needed for manual review completeness."))
    return rows


def build_summary_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        summary_row("final_promotion_gate_status", context["final_status"], "Paper-live candidate gate status for manual discussion only."),
        summary_row("candidate_strategy", STRATEGY_NAME, "Only supported first paper-live candidate."),
        summary_row("ticker", TICKER, "Only supported ticker for this first gate."),
        summary_row("paper_live_candidate", str(context["paper_live_candidate"]), "Candidate label only; not execution approval."),
        summary_row("candidate_scope", "qqq100_only", "No SMA, slow-SMA, high-growth, crypto, QQQ150, or adaptive QQQ promotion."),
        summary_row("largest_blocker", context["largest_blocker"], "Largest remaining blocker before candidate label or paper execution discussion."),
        summary_row("recommended_next_step", context["recommended_next_step"], "Next step remains manual review, not order execution."),
        summary_row("execution_approved", "False", "General execution approval remains false."),
        summary_row("paper_execution_approved", "False", "Paper execution approval remains false."),
        summary_row("scheduling_approved", "False", "Scheduling approval remains false."),
    ]


def gate_row(
    name: str,
    status: str,
    label: str,
    paper_live_candidate: bool,
    finding: str,
    source: str,
    blocker: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "check_name": name,
        "check_status": status,
        "promotion_label": label,
        "candidate_strategy": STRATEGY_NAME,
        "ticker": TICKER,
        "paper_live_candidate": paper_live_candidate,
        "finding": finding,
        "evidence_source": source,
        "blocker": blocker,
        "required_next_step": next_step,
        **GATE_SAFETY_FLAGS,
    }


def summary_row(name: str, value: str, details: str) -> dict[str, Any]:
    return {"summary_name": name, "summary_value": value, "details": details, **SAFETY_FLAGS}


def blocker_row(name: str, status: str, severity: str, details: str, next_step: str) -> dict[str, Any]:
    return {
        "blocker_name": name,
        "status": status,
        "severity": severity,
        "details": details,
        "required_next_step": next_step,
        **SAFETY_FLAGS,
    }


def evidence_row(name: str, status: str, source: str, details: str) -> dict[str, Any]:
    return {
        "evidence_name": name,
        "evidence_status": status,
        "evidence_source": source,
        "details": details,
        **SAFETY_FLAGS,
    }


def build_summary_lines(summary_rows: list[dict[str, Any]], output_paths: dict[str, Path]) -> list[str]:
    return [
        "Paper-live promotion gate complete. Report only; no execution approved.",
        f"Final gate status: {summary_value(summary_rows, 'final_promotion_gate_status')}",
        f"Candidate strategy: {summary_value(summary_rows, 'candidate_strategy')}",
        f"Paper-live candidate: {summary_value(summary_rows, 'paper_live_candidate')}",
        f"Candidate scope: {summary_value(summary_rows, 'candidate_scope')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report to {output_paths['gate']}",
        f"Saved summary/blockers/evidence to {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false",
        "Warning: paper_live_candidate is manual-discussion status only; it is not order approval.",
    ]


def status_for_missing(name: str, missing: list[str]) -> str:
    return "blocked" if name in missing else "pass"


def blocker_for_missing(name: str, missing: list[str]) -> str:
    return f"missing_{name}" if name in missing else "none"


def summary_value(rows: list[dict[str, Any]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", "unavailable"))
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
