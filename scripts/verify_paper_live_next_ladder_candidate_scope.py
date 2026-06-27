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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_next_ladder_candidate_scope.py"
README = ROOT / "README.md"
COMMAND_REFERENCE = ROOT / "docs" / "COMMAND_REFERENCE.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-next-ladder-candidate-scope",
    "--show-paper-live-next-ladder-candidate-scope",
]

OUTPUTS = [
    "data/paper_live_next_ladder_candidate_scope.csv",
    "data/paper_live_next_ladder_candidate_scope_summary.csv",
    "data/paper_live_next_ladder_candidate_scope_blockers.csv",
    "data/paper_live_next_ladder_candidate_scope_evidence.csv",
]

REQUIRED_MODULE_TOKENS = [
    "next_ladder_candidate_scope_report_only",
    "recommended_next_scope",
    "vol_targeted_multi_sleeve_action_preview_design",
    "defensive_sleeve",
    "multi_sleeve_allocator",
    "high_growth_branch",
    "crypto_branch",
    "create_vol_targeted_non_executable_action_preview_design_report_only",
    "f7_accounting_proof_accepted_portfolio_backtests_still_not_promotion_evidence",
    "portfolio_backtest_promotion_evidence_approved",
    "order_instructions_created",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"promotion_approved": False',
    '"portfolio_backtest_promotion_evidence_approved": False',
    '"alpaca_called": False',
    '"live_positions_read": False',
    '"market_data_refreshed": False',
    '"yfinance_called": False',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
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
        print("Paper-live next ladder candidate scope verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live next ladder candidate scope verification passed.")
    print("Verified volatility action-preview design is next report-only scope, defensive/allocator/high-growth remain blocked, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    branches = {
        "--paper-live-next-ladder-candidate-scope": 'if sys.argv[1:] == ["--paper-live-next-ladder-candidate-scope"]:',
        "--show-paper-live-next-ladder-candidate-scope": 'if sys.argv[1:] == ["--show-paper-live-next-ladder-candidate-scope"]:',
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
        failures.append("paper-live next ladder candidate scope module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    display_start = module_source.find("def show_paper_live_next_ladder_candidate_scope")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_paper_live_next_ladder_candidate_scope" in module_source[display_start:]:
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
        "next ladder candidate scope",
        "defensive sleeve",
        "multi-sleeve allocator",
        "high-growth remains research-only",
        "not promotion evidence",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    from trading_bot.research.paper_live_next_ladder_candidate_scope import (  # noqa: PLC0415
        generate_paper_live_next_ladder_candidate_scope,
        show_paper_live_next_ladder_candidate_scope,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = generate_paper_live_next_ladder_candidate_scope(root)
        status_code, lines = show_paper_live_next_ladder_candidate_scope(root)
        report_rows = read_csv_rows(result.output_paths["report"])
        summary_rows = read_csv_rows(result.output_paths["summary"])

    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "next_ladder_candidate_scope_report_only",
        "recommended_next_scope=vol_targeted_multi_sleeve_action_preview_design",
        "second_scope=defensive_sleeve",
        "blocked_scope=high_growth_branch",
        "portfolio_backtest_evidence_status=f7_accounting_proof_accepted_portfolio_backtests_still_not_promotion_evidence",
        "recommended_next_step=create_vol_targeted_non_executable_action_preview_design_report_only",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "promotion_approved=false",
        "portfolio_backtest_promotion_evidence_approved=false",
        "never_schedule_order_capable_commands=true",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")

    scopes = {row.get("candidate_scope"): row for row in report_rows}
    if scopes.get("vol_targeted_multi_sleeve_action_preview_design", {}).get("scope_rank") != "1":
        failures.append("vol_targeted_multi_sleeve_action_preview_design must be rank 1")
    if scopes.get("defensive_sleeve", {}).get("scope_rank") != "2":
        failures.append("defensive_sleeve must be rank 2")
    if scopes.get("multi_sleeve_allocator", {}).get("scope_rank") != "3":
        failures.append("multi_sleeve_allocator must be rank 3")
    if scopes.get("high_growth_branch", {}).get("scope_status") != "not_next_scope_research_only":
        failures.append("high_growth_branch must remain research-only and not next")
    summary = {row.get("summary_name"): row.get("summary_value") for row in summary_rows}
    if summary.get("recommended_next_scope") != "vol_targeted_multi_sleeve_action_preview_design":
        failures.append("summary recommended_next_scope must be vol_targeted_multi_sleeve_action_preview_design")
    for row in report_rows + summary_rows:
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
    ]:
        if field in row and str(row.get(field, "")).lower() != "false":
            failures.append(f"{field} must be false in output rows")
    if "never_schedule_order_capable_commands" in row and str(row.get("never_schedule_order_capable_commands", "")).lower() != "true":
        failures.append("never_schedule_order_capable_commands must be true in report rows")


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
