from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_live_defensive_sleeve_ladder_scope_review.py"
README = ROOT / "README.md"
COMMAND_REFERENCE = ROOT / "docs" / "COMMAND_REFERENCE.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-defensive-sleeve-ladder-scope-review",
    "--show-paper-live-defensive-sleeve-ladder-scope-review",
]

OUTPUTS = [
    "data/paper_live_defensive_sleeve_ladder_scope_review.csv",
    "data/paper_live_defensive_sleeve_ladder_scope_review_summary.csv",
    "data/paper_live_defensive_sleeve_ladder_scope_review_blockers.csv",
    "data/paper_live_defensive_sleeve_ladder_scope_review_evidence.csv",
]

REQUIRED_MODULE_TOKENS = [
    "defensive_sleeve_ladder_scope_review_ready_for_manual_review",
    "defensive_sleeve_ladder_scope_missing_saved_evidence_manual_review_required",
    "defensive_sleeve_selected_for_report_only_review",
    "defensive_sleeve_not_promoted",
    "refresh_or_create_missing_defensive_saved_reports_before_candidate_discussion",
    "manual_review_defensive_sleeve_scope_before_any_candidate_label_change",
    "defensive_sleeve_promoted",
    "order_instructions_created",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"promotion_approved": False',
    '"defensive_sleeve_promoted": False',
    '"alpaca_called": False',
    '"live_positions_read": False',
    '"market_data_refreshed": False',
    '"yfinance_called": False',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
]

EXPECTED_EVIDENCE_FILES = [
    "data/defensive_strategy_report.csv",
    "data/defensive_candidate_comparison.csv",
    "data/defensive_research_state_report.csv",
    "data/defensive_allocation_preview.csv",
    "data/defensive_allocation_risk_preview.csv",
    "data/defensive_allocation_decision_report.csv",
    "data/etf_defensive_drawdown_comparison.csv",
    "data/vol_managed_etf_robustness.csv",
    "data/defensive_research_refresh_summary.csv",
]

FORBIDDEN_CALL_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_all_positions(",
    "get_alpaca_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "yf.",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(
        read_text(path)
        for path in [README, COMMAND_REFERENCE, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST]
    )

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_docs(docs_source, failures)
    verify_fixture_output(failures)

    if failures:
        print("Paper-live defensive sleeve ladder-scope review verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live defensive sleeve ladder-scope review verification passed.")
    print("Verified saved-output-only defensive scope review, missing-evidence/manual-review states, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    branches = {
        "--paper-live-defensive-sleeve-ladder-scope-review": 'if sys.argv[1:] == ["--paper-live-defensive-sleeve-ladder-scope-review"]:',
        "--show-paper-live-defensive-sleeve-ladder-scope-review": 'if sys.argv[1:] == ["--show-paper-live-defensive-sleeve-ladder-scope-review"]:',
    }
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live defensive sleeve ladder-scope review module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for evidence_file in EXPECTED_EVIDENCE_FILES:
        if evidence_file not in module_source:
            failures.append(f"missing expected defensive evidence path: {evidence_file}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    display_start = module_source.find("def show_paper_live_defensive_sleeve_ladder_scope_review")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_paper_live_defensive_sleeve_ladder_scope_review" in module_source[display_start:]:
        failures.append("display command must not regenerate the report")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(
            ["git", "check-ignore", output],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS[:3]:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "defensive sleeve ladder-scope review",
        "saved defensive evidence",
        "defensive sleeve is not promoted",
        "no promotion",
        "no orders",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    from trading_bot.research.paper_live_defensive_sleeve_ladder_scope_review import (  # noqa: PLC0415
        DEFENSIVE_EVIDENCE_FILES,
        generate_paper_live_defensive_sleeve_ladder_scope_review,
        show_paper_live_defensive_sleeve_ladder_scope_review,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        for path in DEFENSIVE_EVIDENCE_FILES.values():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("placeholder\n", encoding="utf-8")
        complete_result = generate_paper_live_defensive_sleeve_ladder_scope_review(root)
        complete_code, complete_lines = show_paper_live_defensive_sleeve_ladder_scope_review(root)
        complete_summary = read_csv_rows(complete_result.output_paths["summary"])

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        missing_result = generate_paper_live_defensive_sleeve_ladder_scope_review(root)
        missing_summary = read_csv_rows(missing_result.output_paths["summary"])

    if complete_code != 0:
        failures.append("saved display should return 0 after report generation")
    complete_output = "\n".join(complete_result.summary_lines + complete_lines)
    for phrase in [
        "defensive_sleeve_ladder_scope_review_ready_for_manual_review",
        "candidate_scope=defensive_sleeve",
        "saved_defensive_evidence_status=complete",
        "missing_evidence_count=0",
        "manual_review_defensive_sleeve_scope_before_any_candidate_label_change",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "promotion_approved=false",
        "defensive_sleeve_promoted=false",
        "never_schedule_order_capable_commands=true",
    ]:
        if phrase not in complete_output:
            failures.append(f"complete fixture output missing phrase: {phrase}")
    complete = {row.get("summary_name"): row.get("summary_value") for row in complete_summary}
    if complete.get("final_defensive_scope_status") != "defensive_sleeve_ladder_scope_review_ready_for_manual_review":
        failures.append("complete fixture should be ready for manual review")
    missing = {row.get("summary_name"): row.get("summary_value") for row in missing_summary}
    if missing.get("final_defensive_scope_status") != "defensive_sleeve_ladder_scope_missing_saved_evidence_manual_review_required":
        failures.append("missing fixture should report missing saved evidence")
    if missing.get("saved_defensive_evidence_status") != "missing_saved_evidence":
        failures.append("missing fixture should label saved evidence as missing")
    for row in complete_summary + missing_summary:
        assert_false_flags(row, failures)


def assert_false_flags(row: dict[str, str], failures: list[str]) -> None:
    for field in [
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "live_trading_approved",
        "followup_order_approved",
        "repeat_execution_approved",
        "promotion_approved",
        "portfolio_backtest_promotion_evidence_approved",
        "defensive_sleeve_promoted",
    ]:
        if field in row and str(row.get(field, "")).lower() != "false":
            failures.append(f"{field} must be false in output rows")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
