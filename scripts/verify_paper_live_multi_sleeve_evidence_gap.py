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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_multi_sleeve_evidence_gap.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-multi-sleeve-evidence-gap",
    "--show-paper-live-multi-sleeve-evidence-gap",
]

OUTPUTS = [
    "data/paper_live_multi_sleeve_evidence_gap.csv",
    "data/paper_live_multi_sleeve_evidence_gap_summary.csv",
    "data/paper_live_multi_sleeve_evidence_gap_blockers.csv",
    "data/paper_live_multi_sleeve_evidence_gap_evidence.csv",
]

REQUIRED_SLEEVES = [
    "qqq100_core",
    "defensive_sleeve",
    "high_growth_sleeve",
    "crypto_sleeve",
    "multi_sleeve_allocator",
]

REQUIRED_REPORT_COLUMNS = [
    "sleeve_name",
    "saved_evidence_present",
    "key_saved_outputs_found",
    "missing_evidence",
    "current_status",
    "blocker",
    "allowed_next_action",
    "forbidden_action",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "never_schedule_order_capable_commands",
]

REQUIRED_MODULE_TOKENS = [
    "saved_output_file_presence_only",
    "does not read generated report contents",
    "qqq100_core",
    "current_monitor_only_base_aligned_long_one_no_action_required_only_existing_paper_live_monitor_base",
    "defensive_sleeve",
    "missing_defensive_promotion_evidence",
    "high_growth_sleeve",
    "missing_high_growth_blocker_evidence",
    "crypto_sleeve",
    "crypto_research_only_no_crypto_execution_approved",
    "multi_sleeve_allocator",
    "allocator_future_only_no_portfolio_execution_wiring",
    "missing_saved_outputs_are_manual_review_blockers",
    "no_research_rerun_no_market_refresh_no_action_preview_no_order_instructions_no_sleeve_promotion",
    "paper_live_multi_sleeve_evidence_gap_manual_review_required",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"never_schedule_order_capable_commands": True',
    '"market_data_refreshed": False',
    '"portfolio_execution_wired": False',
    '"action_preview_created": False',
]

FORBIDDEN_CALL_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_all_positions(",
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
        for path in [README, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST]
    )

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_docs(docs_source, failures)
    verify_report_output_from_fixture(failures)

    if failures:
        print("Paper-live multi-sleeve evidence-gap verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live multi-sleeve evidence-gap verification passed.")
    print("Verified saved-output evidence-gap audit, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-multi-sleeve-evidence-gap": 'if sys.argv[1:] == ["--paper-live-multi-sleeve-evidence-gap"]:',
        "--show-paper-live-multi-sleeve-evidence-gap": 'if sys.argv[1:] == ["--show-paper-live-multi-sleeve-evidence-gap"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live multi-sleeve evidence-gap module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    if "read_csv_rows(" in module_source and "show_paper_live_multi_sleeve_evidence_gap" not in module_source:
        failures.append("module should not read generated CSV contents while building evidence gap")


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
        "evidence-gap audit",
        "saved-output file presence",
        "QQQ100 core",
        "missing saved outputs",
        "No sleeve is promoted",
        "no action previews",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_report_output_from_fixture(failures: list[str]) -> None:
    from trading_bot.research.paper_live_multi_sleeve_evidence_gap import (  # noqa: PLC0415
        generate_paper_live_multi_sleeve_evidence_gap,
        show_paper_live_multi_sleeve_evidence_gap,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture_files(root)
        result = generate_paper_live_multi_sleeve_evidence_gap(root)
        status_code, lines = show_paper_live_multi_sleeve_evidence_gap(root)
        report_rows = read_csv_rows(result.output_paths["report"])
        summary_rows = read_csv_rows(result.output_paths["summary"])

    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "paper_live_multi_sleeve_evidence_gap_manual_review_required",
        "saved_output_evidence_gap_review_only",
        "missing_saved_outputs_are_manual_review_blockers",
        "no_research_rerun_no_market_refresh_no_action_preview_no_order_instructions_no_sleeve_promotion",
        "choose_one_missing_evidence_blocker_for_saved_output_review",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "live_trading_approved=false",
        "followup_order_approved=false",
        "repeat_execution_approved=false",
        "never_schedule_order_capable_commands=true",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")

    sleeves = {row.get("sleeve_name") for row in report_rows}
    for sleeve in REQUIRED_SLEEVES:
        if sleeve not in sleeves:
            failures.append(f"report missing sleeve: {sleeve}")
    for column in REQUIRED_REPORT_COLUMNS:
        if report_rows and column not in report_rows[0]:
            failures.append(f"report missing required column: {column}")
    for row in report_rows + summary_rows:
        assert_false_flags(row, failures)

    by_sleeve = {row.get("sleeve_name"): row for row in report_rows}
    if by_sleeve.get("qqq100_core", {}).get("saved_evidence_present") != "True":
        failures.append("fixture should mark qqq100_core saved evidence present")
    if by_sleeve.get("defensive_sleeve", {}).get("saved_evidence_present") != "False":
        failures.append("fixture should mark defensive saved evidence missing")
    if "no_crypto_execution_approved" not in by_sleeve.get("crypto_sleeve", {}).get("current_status", ""):
        failures.append("crypto sleeve must preserve no crypto execution approved")
    if "no_portfolio_execution_wiring" not in by_sleeve.get("multi_sleeve_allocator", {}).get("current_status", ""):
        failures.append("allocator must preserve no portfolio execution wiring")


def create_fixture_files(root: Path) -> None:
    for relative in [
        "data/paper_live_monitoring_status.csv",
        "data/qqq100_followup_policy_report.csv",
        "data/paper_live_checklist_status.csv",
        "data/paper_live_multi_sleeve_roadmap.csv",
        "data/paper_live_next_phase_backlog.csv",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def assert_false_flags(row: dict[str, str], failures: list[str]) -> None:
    for field in [
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "live_trading_approved",
        "followup_order_approved",
        "repeat_execution_approved",
    ]:
        if str(row.get(field, "")).lower() != "false":
            failures.append(f"{field} must be false in output rows")
    if "never_schedule_order_capable_commands" in row and str(row.get("never_schedule_order_capable_commands", "")).lower() != "true":
        failures.append("never_schedule_order_capable_commands must be true in report rows")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
