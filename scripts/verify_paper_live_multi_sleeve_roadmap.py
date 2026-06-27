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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_multi_sleeve_roadmap.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-multi-sleeve-roadmap",
    "--show-paper-live-multi-sleeve-roadmap",
]

OUTPUTS = [
    "data/paper_live_multi_sleeve_roadmap.csv",
    "data/paper_live_multi_sleeve_roadmap_summary.csv",
    "data/paper_live_multi_sleeve_roadmap_blockers.csv",
    "data/paper_live_multi_sleeve_roadmap_evidence.csv",
]

REQUIRED_SLEEVES = [
    "qqq100_core_sleeve",
    "defensive_sleeve",
    "high_growth_sleeve",
    "crypto_sleeve",
    "multi_sleeve_allocator",
]

REQUIRED_REPORT_COLUMNS = [
    "sleeve_name",
    "current_status",
    "future_ladder_stage",
    "required_evidence_before_next_stage",
    "current_blocker",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "never_schedule_order_capable_commands",
]

REQUIRED_MODULE_TOKENS = [
    "qqq100_core_sleeve",
    "previous_seed_context_aligned_long_one_monitor_only_no_action_required",
    "defensive_sleeve",
    "future_review_only",
    "high_growth_sleeve",
    "research_only",
    "concentration_drawdown_attribution_review_required_before_preview_or_paper_live_discussion",
    "crypto_sleeve",
    "research_only_capped_future_only_no_crypto_execution_approved",
    "multi_sleeve_allocator",
    "current_report_status_seed_no_portfolio_execution_wiring_no_order_instructions_no_scheduling",
    "portfolio_execution_wiring_forbidden",
    "scheduled_execution_forbidden",
    "paper_live_multi_sleeve_roadmap_report_only",
    "vol_targeted_multi_sleeve_report_status_seed_from_research",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x_report_status_seed",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"never_schedule_order_capable_commands": True',
    '"portfolio_execution_wired": False',
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
        print("Paper-live multi-sleeve roadmap verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live multi-sleeve roadmap verification passed.")
    print("Verified report-only volatility multi-sleeve roadmap, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-multi-sleeve-roadmap": 'if sys.argv[1:] == ["--paper-live-multi-sleeve-roadmap"]:',
        "--show-paper-live-multi-sleeve-roadmap": 'if sys.argv[1:] == ["--show-paper-live-multi-sleeve-roadmap"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live multi-sleeve roadmap module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")


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
        "QQQ-led multi-sleeve",
        "QQQ100 core sleeve",
        "High-growth sleeve",
        "Crypto sleeve",
        "no portfolio execution",
        "no scheduled execution",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_report_output_from_fixture(failures: list[str]) -> None:
    from trading_bot.research.paper_live_multi_sleeve_roadmap import (  # noqa: PLC0415
        generate_paper_live_multi_sleeve_roadmap,
        show_paper_live_multi_sleeve_roadmap,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = generate_paper_live_multi_sleeve_roadmap(root)
        status_code, lines = show_paper_live_multi_sleeve_roadmap(root)
        report_rows = read_csv_rows(result.output_paths["report"])
        summary_rows = read_csv_rows(result.output_paths["summary"])

    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "paper_live_multi_sleeve_roadmap_report_only",
        "vol_targeted_multi_sleeve_report_status_seed_from_research",
        "previous_seed_context_aligned_long_one_monitor_only",
        "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x_report_status_seed",
        "future_review_only_must_pass_ladder_separately",
        "research_only_concentration_drawdown_attribution_required",
        "research_only_capped_future_only_no_execution_approved",
        "current_report_status_seed_no_portfolio_execution_wiring",
        "observe_enabled_status_cron_then_review_non_executable_action_preview_design",
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
    if "previous_seed_context" not in by_sleeve.get("qqq100_core_sleeve", {}).get("current_status", ""):
        failures.append("QQQ100 core sleeve must stay previous-seed context / monitor-only")
    if "research_only" not in by_sleeve.get("high_growth_sleeve", {}).get("current_status", ""):
        failures.append("high-growth sleeve must remain research-only")
    if "no_crypto_execution_approved" not in by_sleeve.get("crypto_sleeve", {}).get("current_status", ""):
        failures.append("crypto sleeve must preserve no crypto execution approved")
    if "current_report_status_seed" not in by_sleeve.get("multi_sleeve_allocator", {}).get("current_status", ""):
        failures.append("allocator must identify the volatility seed as report/status only")


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
