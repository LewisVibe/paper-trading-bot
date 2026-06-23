"""Saved-output paper-live readiness report for future manual QQQ100 action.

This report is static/saved-output only. It does not call Alpaca, read
positions, refresh market data, load config.json, create order instructions,
submit/cancel/replace orders, write SQLite, send alerts, schedule anything, or
connect strategy output to execution.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_bot.research.paper_live_evidence_audit import evaluate_paper_live_saved_evidence


STRATEGY_NAME = "qqq_100_trend_gate"
TICKER = "QQQ"

OUTPUT_FILES = {
    "report": Path("data/paper_live_readiness_report.csv"),
    "summary": Path("data/paper_live_readiness_summary.csv"),
    "blockers": Path("data/paper_live_readiness_blockers.csv"),
    "evidence": Path("data/paper_live_readiness_evidence.csv"),
}

SAVED_EVIDENCE_FILES = {
    "paper_live_promotion_gate": Path("data/paper_live_promotion_gate_summary.csv"),
    "qqq100_preview_signal": Path("data/qqq100_preview_signal_pack.csv"),
    "qqq100_action_preview": Path("data/qqq100_action_preview.csv"),
    "qqq100_action_preview_summary": Path("data/qqq100_action_preview_summary.csv"),
    "qqq100_paper_execution_result": Path("data/qqq100_paper_execution_result.csv"),
    "qqq100_paper_readiness_blockers": Path("data/qqq100_paper_readiness_blocker_summary.csv"),
    "qqq100_paper_execution_readiness": Path("data/qqq100_paper_execution_readiness_summary.csv"),
    "qqq100_paper_postcheck": Path("data/qqq100_paper_postcheck.csv"),
    "qqq100_paper_postcheck_summary": Path("data/qqq100_paper_postcheck_summary.csv"),
    "paper_execution_state_positions": Path("data/paper_execution_state_positions.csv"),
    "paper_execution_state_milestones": Path("data/paper_execution_state_milestones.csv"),
    "portfolio_risk_policy": Path("data/portfolio_risk_policy_report.csv"),
    "execution_eligibility": Path("data/execution_eligibility_report.csv"),
    "paper_execution_protection": Path("data/paper_execution_protection_report.csv"),
}

STATIC_FILES = {
    "repo_safety_verifier": Path("scripts/verify_repo_safety.py"),
    "baseline_freeze_verifier": Path("scripts/verify_paper_live_baseline_freeze.py"),
    "paper_live_promotion_gate_verifier": Path("scripts/verify_paper_live_promotion_gate.py"),
    "qqq100_exact_alignment_verifier": Path("scripts/verify_qqq100_exact_alignment.py"),
    "execute_qqq100_verifier": Path("scripts/verify_execute_qqq100_paper.py"),
    "bot": Path("bot.py"),
    "readme": Path("README.md"),
    "current_state": Path("docs/CURRENT_STATE.md"),
    "codex_workflow": Path("docs/CODEX_WORKFLOW.md"),
    "hermes_task_board": Path("docs/HERMES_TASK_BOARD.md"),
    "paper_live_checklist": Path("docs/PAPER_LIVE_CHECKLIST.md"),
    "qqq100_helper": Path("trading_bot/safety/qqq100_paper_execution.py"),
}

SAFETY_FLAGS = {
    "execution_approved": False,
    "paper_execution_approved": False,
    "scheduling_approved": False,
    "live_trading_approved": False,
}

REPORT_COLUMNS = [
    "check_name",
    "check_status",
    "risk_level",
    "finding",
    "evidence_source",
    "blocker",
    "required_next_step",
    "research_only",
    "report_only",
    "preview_only",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "order_instructions_created",
    "alpaca_called",
    "positions_read",
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
    "evidence_status",
    "evidence_source",
    "details",
    *SAFETY_FLAGS.keys(),
]

ROW_SAFETY = {
    "research_only": True,
    "report_only": True,
    "preview_only": True,
    "orders_created": False,
    "orders_submitted": False,
    "orders_cancelled": False,
    "order_instructions_created": False,
    "alpaca_called": False,
    "positions_read": False,
    "sqlite_trade_log_written": False,
    "discord_alert_sent": False,
    "telegram_alert_sent": False,
    **SAFETY_FLAGS,
}


@dataclass
class PaperLiveReadinessReportResult:
    output_paths: dict[str, Path]
    report_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]
    blocker_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_paper_live_readiness_report(root_dir: Path | str = ".") -> PaperLiveReadinessReportResult:
    root = Path(root_dir)
    static_texts = {name: read_text(root / path) for name, path in STATIC_FILES.items()}
    saved_inputs = {name: read_csv_rows(root / path) for name, path in SAVED_EVIDENCE_FILES.items()}
    context = build_context(root, static_texts, saved_inputs)
    report_rows = build_report_rows(context)
    blocker_rows = build_blocker_rows(report_rows, context)
    evidence_rows = build_evidence_rows(context, saved_inputs)
    summary_rows = build_summary_rows(context, blocker_rows)
    output_paths = {name: root / path for name, path in OUTPUT_FILES.items()}
    write_rows(output_paths["report"], REPORT_COLUMNS, report_rows)
    write_rows(output_paths["summary"], SUMMARY_COLUMNS, summary_rows)
    write_rows(output_paths["blockers"], BLOCKER_COLUMNS, blocker_rows)
    write_rows(output_paths["evidence"], EVIDENCE_COLUMNS, evidence_rows)
    return PaperLiveReadinessReportResult(
        output_paths=output_paths,
        report_rows=report_rows,
        summary_rows=summary_rows,
        blocker_rows=blocker_rows,
        evidence_rows=evidence_rows,
        summary_lines=build_summary_lines(summary_rows, output_paths),
    )


def show_paper_live_readiness_report(root_dir: Path | str = ".") -> tuple[int, list[str]]:
    root = Path(root_dir)
    summary_path = root / OUTPUT_FILES["summary"]
    if not summary_path.exists():
        return 1, [
            "Paper-live readiness report is missing.",
            "Run `python bot.py --paper-live-readiness-report` first.",
            "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false",
        ]
    rows = read_csv_rows(summary_path)
    return 0, [
        "Paper-live readiness saved display. Report only; no execution approved.",
        f"final_readiness_status: {summary_value(rows, 'final_readiness_status')}",
        f"candidate_strategy: {summary_value(rows, 'candidate_strategy')}",
        f"candidate_ticker: {summary_value(rows, 'candidate_ticker')}",
        f"ready_for_manual_qqq100_paper_action_discussion: {summary_value(rows, 'ready_for_manual_qqq100_paper_action_discussion')}",
        f"blocked_or_warning_rows: {summary_value(rows, 'blocked_or_warning_rows')}",
        f"largest_blocker: {summary_value(rows, 'largest_blocker')}",
        f"recommended_next_step: {summary_value(rows, 'recommended_next_step')}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false",
        "Warning: readiness is manual-review status only, not order approval.",
    ]


def build_context(
    root: Path,
    static_texts: dict[str, str],
    saved_inputs: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    combined_docs = "\n".join(
        static_texts[name]
        for name in ["readme", "current_state", "codex_workflow", "hermes_task_board", "paper_live_checklist"]
    )
    bot_source = static_texts["bot"]
    missing_static = [name for name, path in STATIC_FILES.items() if not (root / path).exists()]
    missing_saved = [name for name, rows in saved_inputs.items() if not rows]
    saved_snapshot = evaluate_paper_live_saved_evidence(inputs=saved_inputs)
    return {
        "root": root,
        "bot_source": bot_source,
        "all_static_text": "\n".join(static_texts.values()),
        "combined_docs": combined_docs,
        "missing_static": missing_static,
        "missing_saved": missing_saved,
        "saved_snapshot": saved_snapshot,
    }


def build_report_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    bot_source = context["bot_source"]
    docs = context["combined_docs"]
    all_static_text = context["all_static_text"]
    missing_static = context["missing_static"]
    missing_saved = context["missing_saved"]
    saved_snapshot = context["saved_snapshot"]
    process_ticker = function_body(bot_source, "process_ticker")
    run_qqq100 = function_body(bot_source, "run_execute_qqq100_paper")
    submit_call_token = "submit_alpaca_" + "order("

    return [
        check_static("repo_safety_verifier_exists", "repo_safety_verifier", missing_static, "scripts/verify_repo_safety.py", "Run repo safety before any paper-live discussion."),
        check_static("baseline_freeze_verifier_exists", "baseline_freeze_verifier", missing_static, "scripts/verify_paper_live_baseline_freeze.py", "Run baseline freeze before any paper-live discussion."),
        check_static("paper_live_promotion_gate_exists", "paper_live_promotion_gate_verifier", missing_static, "scripts/verify_paper_live_promotion_gate.py", "Run promotion gate before readiness discussion."),
        check_static("qqq100_exact_alignment_verifier_exists", "qqq100_exact_alignment_verifier", missing_static, "scripts/verify_qqq100_exact_alignment.py", "Run exact alignment verifier before any paper action."),
        check_static("execute_qqq100_verifier_exists", "execute_qqq100_verifier", missing_static, "scripts/verify_execute_qqq100_paper.py", "Run QQQ100 execution verifier before any paper action."),
        check_text("normal_bot_monitoring_only", "monitor_only" in process_ticker and submit_call_token not in process_ticker, "Normal bot remains monitoring-only.", "bot.py process_ticker", "Restore monitoring-only normal bot boundary."),
        check_text("alpaca_paper_only_boundary", "Alpaca paper only" in docs and "live_trading_approved" in docs, "Alpaca paper-only and no-live boundaries are documented.", "docs", "Document and preserve paper-only/no-live boundary."),
        check_text("qqq100_fixed_ticker", "QQQ100_TICKER" in run_qqq100 and "saved signal ticker must be QQQ" in bot_source, "QQQ100 path is fixed to ticker QQQ.", "bot.py / qqq100 helper", "Keep QQQ100 fixed to QQQ."),
        check_text("qqq100_fixed_strategy", STRATEGY_NAME in run_qqq100 and STRATEGY_NAME in docs, "QQQ100 path is fixed to qqq_100_trend_gate.", "bot.py / docs", "Keep QQQ100 fixed to qqq_100_trend_gate."),
        check_text("qqq100_exact_zero_one_alignment", "blocked_excess_long_position" in all_static_text and "exact zero/one" in docs, "QQQ100 exact zero/one-share alignment policy is present.", "qqq100 helper / docs", "Keep >1 and fractional QQQ states blocked/manual-review."),
        check_text("sma_slow_sma_not_promoted", "SMA/slow-SMA are excluded" in docs or "SMA and slow-SMA are excluded" in docs, "SMA and slow-SMA are not paper-live candidates.", "docs", "Keep SMA and slow-SMA out of paper-live promotion."),
        check_text("high_growth_not_promoted", "High-growth remains research-only" in docs or "high-growth plus crypto remain research-only" in docs, "High-growth remains research-only.", "docs", "Do not promote high-growth to paper-live."),
        check_text("crypto_not_promoted", "crypto remain research-only" in docs.lower(), "Crypto remains research-only.", "docs", "Do not promote crypto to paper-live."),
        check_text("paper_execution_separate_confirmed", "--confirm-qqq100-paper" in bot_source and "--execute-qqq100-paper" in bot_source, "Paper execution commands remain separate and confirmation-gated.", "bot.py", "Keep paper execution behind explicit confirmation."),
        check_text("open_order_checks_required", "get_open_orders_for_ticker" in run_qqq100 and "open_order_count" in run_qqq100, "Open-order checks are required before QQQ100 paper action.", "bot.py run_execute_qqq100_paper", "Keep open-order checks before any QQQ100 paper action."),
        check_text("duplicate_order_checks_required", "recent_matching_manual_smoke_test_order_check" in run_qqq100, "Recent duplicate-order checks are required before QQQ100 paper action.", "bot.py run_execute_qqq100_paper", "Keep duplicate-order checks before any QQQ100 paper action."),
        check_saved("position_readability_postcheck_required", "qqq100_paper_postcheck", missing_saved, "data/qqq100_paper_postcheck_summary.csv", "Position readability/postcheck evidence is required before any future QQQ100 paper action."),
        check_text("saved_state_reconciled", saved_snapshot.complete_for_state_reconciliation, "Saved QQQ100 desired state, saved paper position, saved order result, and alignment state reconcile.", "saved QQQ100 evidence audit", "Review exact missing saved files or fields before readiness label."),
        check_text("saved_state_aligned_long_after_fill", saved_snapshot.aligned_long_after_saved_fill, "Saved QQQ100 evidence shows desired long, QQQ long 1, filled saved order, and aligned_long state.", "saved QQQ100 evidence audit", "Keep follow-up order approval false and review manually before any separate follow-up design."),
        check_text("followup_order_not_approved", not saved_snapshot.aligned_long_after_saved_fill, "Reconciled saved aligned-long state does not approve a follow-up or repeat QQQ100 paper order.", "manual approval boundary", "Design and approve any follow-up order separately."),
        check_saved("portfolio_risk_review_evidence", "portfolio_risk_policy", missing_saved, "data/portfolio_risk_policy_report.csv", "Portfolio/risk review evidence is required before any future QQQ100 paper action."),
        check_saved("execution_readiness_evidence", "qqq100_paper_execution_readiness", missing_saved, "data/qqq100_paper_execution_readiness_summary.csv", "Execution-readiness evidence is required before any future QQQ100 paper action."),
        check_text("scheduling_false_no_order_cron", "Do not schedule order-capable commands" in docs and "scheduling_approved" in docs, "Scheduling remains false; order-capable commands are not schedulable.", "docs", "Do not schedule order-capable commands."),
    ]


def build_blocker_rows(report_rows: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        blocker_row("execution_not_approved", "blocked", "critical", "This readiness report does not approve execution or paper execution.", "Use a separate explicit manual confirmation prompt before any paper action."),
        blocker_row("live_trading_not_approved", "blocked", "critical", "Live trading remains out of scope.", "Keep Alpaca paper-only; do not add live trading."),
        blocker_row("scheduling_not_approved", "blocked", "critical", "Scheduling order-capable commands remains prohibited.", "Do not schedule QQQ100 execution, paper-order tests, slow-SMA, or normal bot execution."),
    ]
    for row in report_rows:
        if row["check_status"] in {"blocked", "warning"}:
            rows.append(
                blocker_row(
                    str(row["check_name"]),
                    str(row["check_status"]),
                    str(row["risk_level"]),
                    str(row["finding"]),
                    str(row["required_next_step"]),
                )
            )
    for missing in context["saved_snapshot"].exact_missing_items:
        rows.append(
            blocker_row(
                f"exact_missing_saved_evidence_{missing.replace(':', '_').replace('/', '_').replace(chr(92), '_')}",
                "blocked",
                "high",
                missing,
                "Regenerate or review the exact saved evidence item before readiness discussion.",
            )
        )
    if context["missing_saved"]:
        rows.append(
            blocker_row(
                "missing_saved_evidence_files",
                "warning",
                "medium",
                "; ".join(f"{name}:{SAVED_EVIDENCE_FILES[name]}" for name in context["missing_saved"]),
                "Regenerate or review missing saved reports with safe report-only commands if needed.",
            )
        )
    return rows


def build_evidence_rows(context: dict[str, Any], saved_inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = [
        evidence_row("candidate_strategy", "present", STRATEGY_NAME, "First paper-live candidate remains QQQ100 only."),
        evidence_row("candidate_ticker", "present", TICKER, "First paper-live ticker remains QQQ only."),
    ]
    rows.extend(
        evidence_row(name, "present" if rows_ else "missing", str(SAVED_EVIDENCE_FILES[name]), "Saved evidence presence check.")
        for name, rows_ in saved_inputs.items()
    )
    rows.extend(
        evidence_row(name, "present" if name not in context["missing_static"] else "missing", str(STATIC_FILES[name]), "Static file/verifier presence check.")
        for name in STATIC_FILES
    )
    return rows


def build_summary_rows(context: dict[str, Any], blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    saved_snapshot = context["saved_snapshot"]
    actionable_blockers = [
        row
        for row in blocker_rows
        if row["blocker_name"] not in {"execution_not_approved", "live_trading_not_approved", "scheduling_not_approved"}
        and row["status"] in {"blocked", "warning"}
    ]
    ready = False
    if saved_snapshot.aligned_long_after_saved_fill:
        final_status = "paper_live_readiness_reconciled_aligned_manual_review_required"
        largest_blocker = "followup_order_not_approved_after_reconciled_saved_state"
    elif saved_snapshot.complete_for_state_reconciliation and not actionable_blockers:
        final_status = "paper_live_ready_for_manual_qqq100_paper_action_discussion"
        largest_blocker = "explicit_human_approval_still_required"
        ready = True
    else:
        final_status = "paper_live_readiness_manual_review_required"
        largest_blocker = (
            "; ".join(saved_snapshot.exact_missing_items)
            if saved_snapshot.exact_missing_items
            else actionable_blockers[0]["blocker_name"]
            if actionable_blockers
            else "explicit_human_approval_still_required"
        )
    next_step = (
        "manual_discussion_only_before_any_separate_qqq100_paper_execution_prompt"
        if ready
        else "review_reconciled_saved_state_or_exact_missing_evidence_before_any_manual_qqq100_paper_action"
    )
    return [
        summary_row("final_readiness_status", final_status, "Readiness for future manual QQQ100 paper action discussion only."),
        summary_row("candidate_strategy", STRATEGY_NAME, "Only supported first paper-live candidate."),
        summary_row("candidate_ticker", TICKER, "Only supported first paper-live ticker."),
        summary_row("ready_for_manual_qqq100_paper_action_discussion", str(ready), "Manual discussion only; not order approval."),
        summary_row("blocked_or_warning_rows", str(len(actionable_blockers)), "Evidence blockers/warnings excluding always-false approval boundaries."),
        summary_row("largest_blocker", largest_blocker, "Largest readiness blocker before manual discussion."),
        summary_row("recommended_next_step", next_step, "Next step remains review, not execution."),
        summary_row("exact_missing_saved_evidence", "; ".join(saved_snapshot.exact_missing_items) if saved_snapshot.exact_missing_items else "none", "Exact missing saved files or fields for reconciliation."),
        summary_row("saved_state_reconciled", str(saved_snapshot.complete_for_state_reconciliation), "Reconciled saved QQQ100 desired/position/order/alignment evidence."),
        summary_row("aligned_long_after_saved_fill", str(saved_snapshot.aligned_long_after_saved_fill), "Saved aligned long state after a saved filled order; not follow-up approval."),
        summary_row("followup_order_approved", "False", "Follow-up or repeat order approval remains false."),
        summary_row("execution_approved", "False", "Execution approval remains false."),
        summary_row("paper_execution_approved", "False", "Paper execution approval remains false."),
        summary_row("scheduling_approved", "False", "Scheduling approval remains false."),
        summary_row("live_trading_approved", "False", "Live trading approval remains false."),
    ]


def check_static(name: str, static_name: str, missing: list[str], source: str, next_step: str) -> dict[str, Any]:
    passed = static_name not in missing
    return report_row(name, "pass" if passed else "blocked", "low" if passed else "high", f"{static_name} {'exists' if passed else 'is missing'}.", source, "none" if passed else f"missing_{static_name}", next_step)


def check_saved(name: str, saved_name: str, missing: list[str], source: str, next_step: str) -> dict[str, Any]:
    passed = saved_name not in missing
    return report_row(name, "pass" if passed else "blocked", "medium" if passed else "high", f"{saved_name} saved evidence {'exists' if passed else 'is missing'}.", source, "none" if passed else f"missing_{saved_name}", next_step)


def check_text(name: str, passed: bool, finding: str, source: str, next_step: str) -> dict[str, Any]:
    return report_row(name, "pass" if passed else "blocked", "medium" if passed else "high", finding, source, "none" if passed else f"{name}_not_confirmed", next_step)


def report_row(
    name: str,
    status: str,
    risk: str,
    finding: str,
    source: str,
    blocker: str,
    next_step: str,
) -> dict[str, Any]:
    return {
        "check_name": name,
        "check_status": status,
        "risk_level": risk,
        "finding": finding,
        "evidence_source": source,
        "blocker": blocker,
        "required_next_step": next_step,
        **ROW_SAFETY,
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
        "Paper-live readiness report complete. Report only; no execution approved.",
        f"Final readiness status: {summary_value(summary_rows, 'final_readiness_status')}",
        f"Candidate strategy: {summary_value(summary_rows, 'candidate_strategy')}",
        f"Candidate ticker: {summary_value(summary_rows, 'candidate_ticker')}",
        f"Ready for manual QQQ100 paper action discussion: {summary_value(summary_rows, 'ready_for_manual_qqq100_paper_action_discussion')}",
        f"Blocked/warning rows: {summary_value(summary_rows, 'blocked_or_warning_rows')}",
        f"Largest blocker: {summary_value(summary_rows, 'largest_blocker')}",
        f"Recommended next step: {summary_value(summary_rows, 'recommended_next_step')}",
        f"Saved report to {output_paths['report']}",
        f"Saved summary/blockers/evidence to {output_paths['summary']}; {output_paths['blockers']}; {output_paths['evidence']}",
        "execution_approved=false; paper_execution_approved=false; scheduling_approved=false; live_trading_approved=false",
        "Warning: readiness is manual-review status only; it is not order approval.",
    ]


def function_body(source: str, name: str) -> str:
    match = re.search(rf"^def {re.escape(name)}\(", source, flags=re.MULTILINE)
    if not match:
        return ""
    next_match = re.search(r"^def \w+\(", source[match.end() :], flags=re.MULTILINE)
    if next_match:
        return source[match.start() : match.end() + next_match.start()]
    return source[match.start() :]


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


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
