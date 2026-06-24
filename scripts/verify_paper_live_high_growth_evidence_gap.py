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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_high_growth_evidence_gap.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-high-growth-evidence-gap",
    "--show-paper-live-high-growth-evidence-gap",
]

OUTPUTS = [
    "data/paper_live_high_growth_evidence_gap.csv",
    "data/paper_live_high_growth_evidence_gap_summary.csv",
    "data/paper_live_high_growth_evidence_gap_blockers.csv",
    "data/paper_live_high_growth_evidence_gap_evidence.csv",
]

REQUIRED_AREAS = [
    "high_growth_saved_lead_evidence",
    "concentration_evidence",
    "drawdown_evidence",
    "attribution_evidence",
    "bias_risk_warnings",
    "promotion_readiness",
]

REQUIRED_REPORT_COLUMNS = [
    "evidence_area",
    "saved_evidence_present",
    "expected_saved_outputs",
    "key_missing_evidence",
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
    "high_growth_promotion_approved",
    "never_schedule_order_capable_commands",
]

REQUIRED_MODULE_TOKENS = [
    "saved_output_file_presence_only",
    "does not read generated report contents",
    "high_growth_saved_lead_evidence",
    "missing_high_growth_saved_lead_or_decision_evidence",
    "concentration_evidence",
    "missing_concentration_or_top_contributor_dependency_evidence",
    "drawdown_evidence",
    "missing_high_growth_drawdown_window_or_contribution_evidence",
    "data/high_growth_stock_drawdown_control_report.csv",
    "data/high_growth_stock_drawdown_control_summary.csv",
    "data/high_growth_stock_drawdown_control_drawdowns.csv",
    "exact_missing_evidence_blockers",
    "attribution_evidence",
    "missing_component_ticker_weight_or_contribution_attribution",
    "data/high_growth_component_attribution_summary.csv",
    "data/high_growth_component_contributions.csv",
    "data/high_growth_component_drawdown_contributions.csv",
    "bias_risk_warnings",
    "missing_survivorship_concentration_or_outlier_warning_evidence",
    "promotion_readiness",
    "missing_promotion_ladder_f6_f7_or_portfolio_risk_review_evidence",
    "paper_live_high_growth_evidence_gap_manual_review_required",
    "high_growth_missing_saved_evidence_blocks_promotion",
    "no_research_rerun_no_market_refresh_no_action_preview_no_order_instructions_no_high_growth_promotion",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"high_growth_promotion_approved": False',
    '"never_schedule_order_capable_commands": True',
    '"market_data_refreshed": False',
    '"yfinance_called": False',
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
        print("Paper-live high-growth evidence-gap verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live high-growth evidence-gap verification passed.")
    print("Verified saved-output high-growth evidence audit, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-high-growth-evidence-gap": 'if sys.argv[1:] == ["--paper-live-high-growth-evidence-gap"]:',
        "--show-paper-live-high-growth-evidence-gap": 'if sys.argv[1:] == ["--show-paper-live-high-growth-evidence-gap"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live high-growth evidence-gap module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    if '"data/high_growth_stock_drawdown_control.csv"' in module_source:
        failures.append("module must not expect non-canonical high_growth_stock_drawdown_control.csv")
    if '"data/high_growth_component_attribution_evidence.csv"' in module_source:
        failures.append("module must not expect non-canonical high_growth_component_attribution_evidence.csv")
    if "read_csv_rows(" in module_source and "show_paper_live_high_growth_evidence_gap" not in module_source:
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
        "high-growth evidence-gap audit",
        "saved-output file presence",
        "top-contributor dependency",
        "survivorship",
        "high-growth promotion",
        "No high-growth sleeve is promoted",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_report_output_from_fixture(failures: list[str]) -> None:
    from trading_bot.research.paper_live_high_growth_evidence_gap import (  # noqa: PLC0415
        generate_paper_live_high_growth_evidence_gap,
        show_paper_live_high_growth_evidence_gap,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture_files(root)
        result = generate_paper_live_high_growth_evidence_gap(root)
        status_code, lines = show_paper_live_high_growth_evidence_gap(root)
        report_rows = read_csv_rows(result.output_paths["report"])
        summary_rows = read_csv_rows(result.output_paths["summary"])

    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "paper_live_high_growth_evidence_gap_manual_review_required",
        "saved_output_high_growth_evidence_review_only",
        "high_growth_missing_saved_evidence_blocks_promotion",
        "no_research_rerun_no_market_refresh_no_action_preview_no_order_instructions_no_high_growth_promotion",
        "choose_one_high_growth_missing_evidence_blocker_for_saved_output_review",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "live_trading_approved=false",
        "followup_order_approved=false",
        "repeat_execution_approved=false",
        "high_growth_promotion_approved=false",
        "never_schedule_order_capable_commands=true",
        "exact_missing_evidence_blockers",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")

    areas = {row.get("evidence_area") for row in report_rows}
    for area in REQUIRED_AREAS:
        if area not in areas:
            failures.append(f"report missing evidence area: {area}")
    for column in REQUIRED_REPORT_COLUMNS:
        if report_rows and column not in report_rows[0]:
            failures.append(f"report missing required column: {column}")
    for row in report_rows + summary_rows:
        assert_false_flags(row, failures)

    by_area = {row.get("evidence_area"): row for row in report_rows}
    if by_area.get("high_growth_saved_lead_evidence", {}).get("saved_evidence_present") != "True":
        failures.append("fixture should mark high-growth saved lead evidence present")
    if by_area.get("concentration_evidence", {}).get("saved_evidence_present") != "True":
        failures.append("fixture should mark concentration saved evidence present")
    if by_area.get("drawdown_evidence", {}).get("saved_evidence_present") != "True":
        failures.append("fixture should mark drawdown saved evidence present from canonical saved files")
    if by_area.get("drawdown_evidence", {}).get("key_missing_evidence") != "none":
        failures.append("fixture should not report missing drawdown evidence when canonical saved files exist")
    if by_area.get("attribution_evidence", {}).get("saved_evidence_present") != "True":
        failures.append("fixture should mark attribution saved evidence present from canonical saved files")
    if by_area.get("attribution_evidence", {}).get("key_missing_evidence") != "none":
        failures.append("fixture should not report missing attribution evidence when canonical saved files exist")
    if "not_approved" not in by_area.get("promotion_readiness", {}).get("current_status", ""):
        failures.append("promotion readiness must preserve high-growth not approved")
    if "preview_or_paper_live" not in by_area.get("attribution_evidence", {}).get("blocker", ""):
        failures.append("attribution evidence must block preview or paper-live movement")


def create_fixture_files(root: Path) -> None:
    for relative in [
        "data/high_growth_stock_lead_decision_report.csv",
        "data/high_growth_stock_manual_review_pack.csv",
        "data/high_growth_component_streams.csv",
        "data/high_growth_component_streams_summary.csv",
        "data/high_growth_component_attribution.csv",
        "data/high_growth_component_attribution_summary.csv",
        "data/high_growth_component_contributions.csv",
        "data/high_growth_component_drawdown_contributions.csv",
        "data/multi_sleeve_high_growth_drawdown_decomposition.csv",
        "data/multi_sleeve_high_growth_drawdown_summary.csv",
        "data/multi_sleeve_high_growth_drawdown_periods.csv",
        "data/high_growth_stock_drawdown_control_report.csv",
        "data/high_growth_stock_drawdown_control_summary.csv",
        "data/high_growth_stock_drawdown_control_drawdowns.csv",
        "data/paper_live_multi_sleeve_evidence_gap.csv",
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
        "high_growth_promotion_approved",
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
