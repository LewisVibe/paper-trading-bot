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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_high_growth_manual_review_decision.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-high-growth-manual-review-decision",
    "--show-paper-live-high-growth-manual-review-decision",
]

OUTPUTS = [
    "data/paper_live_high_growth_manual_review_decision.csv",
    "data/paper_live_high_growth_manual_review_decision_summary.csv",
    "data/paper_live_high_growth_manual_review_decision_blockers.csv",
    "data/paper_live_high_growth_manual_review_decision_evidence.csv",
]

REQUIRED_COLUMNS = [
    "final_decision_status",
    "high_growth_preview_candidate",
    "high_growth_paper_live_candidate",
    "high_growth_promotion_approved",
    "current_manual_review_reason",
    "qqq100_relative_status",
    "future_reconsideration_requirements",
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
    "paper_live_high_growth_manual_review_decision.csv",
    "paper_live_high_growth_evidence_gap_summary.csv",
    "paper_live_high_growth_evidence_quality_summary.csv",
    "high_growth_remains_research_only_manual_review_required",
    "high_growth_preview_candidate",
    "high_growth_paper_live_candidate",
    "high_growth_promotion_approved",
    "qqq100_remains_cleaner_current_paper_live_monitor_base",
    "concentration_cap_or_concentration_control_evidence",
    "component_drawdown_attribution_acceptable_dependency",
    "split_robustness_and_cost_review",
    "portfolio_accounting_consistency",
    "f6_f7_compatibility",
    "risk_policy_review",
    "no_order_instructions_or_scheduling",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"never_schedule_order_capable_commands": True',
    '"market_data_refreshed": False',
    '"yfinance_called": False',
    '"alpaca_called": False',
    '"live_positions_read": False',
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
    verify_fixture_output(failures)

    if failures:
        print("Paper-live high-growth manual-review decision verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live high-growth manual-review decision verification passed.")
    print("Verified saved-output-only decision, QQQ100 relative boundary, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    branches = {
        "--paper-live-high-growth-manual-review-decision": 'if sys.argv[1:] == ["--paper-live-high-growth-manual-review-decision"]:',
        "--show-paper-live-high-growth-manual-review-decision": 'if sys.argv[1:] == ["--show-paper-live-high-growth-manual-review-decision"]:',
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
        failures.append("paper-live high-growth manual-review decision module is missing")
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
        "high-growth manual-review decision",
        "QQQ100 remains the cleaner current paper-live monitor base",
        "high-growth remains research-only",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    from trading_bot.research.paper_live_high_growth_manual_review_decision import (  # noqa: PLC0415
        generate_paper_live_high_growth_manual_review_decision,
        show_paper_live_high_growth_manual_review_decision,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture_files(root)
        result = generate_paper_live_high_growth_manual_review_decision(root)
        status_code, lines = show_paper_live_high_growth_manual_review_decision(root)
        decision_rows = read_csv_rows(result.output_paths["decision"])
        summary_rows = read_csv_rows(result.output_paths["summary"])
        blocker_rows = read_csv_rows(result.output_paths["blockers"])

    if status_code != 0:
        failures.append("saved display should return 0 after decision report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "high_growth_remains_research_only_manual_review_required",
        "high_growth_preview_candidate=False",
        "high_growth_paper_live_candidate=False",
        "high_growth_promotion_approved=False",
        "qqq100_remains_cleaner_current_paper_live_monitor_base",
        "concentration_cap_or_concentration_control_evidence",
        "component_drawdown_attribution_acceptable_dependency",
        "split_robustness_and_cost_review",
        "portfolio_accounting_consistency",
        "f6_f7_compatibility",
        "risk_policy_review",
        "no_order_instructions_or_scheduling",
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
    if not decision_rows:
        failures.append("decision output should include one decision row")
        return
    row = decision_rows[0]
    for column in REQUIRED_COLUMNS:
        if column not in row:
            failures.append(f"decision output missing required column: {column}")
    expected_values = {
        "final_decision_status": "high_growth_remains_research_only_manual_review_required",
        "high_growth_preview_candidate": "False",
        "high_growth_paper_live_candidate": "False",
        "high_growth_promotion_approved": "False",
        "qqq100_relative_status": "qqq100_remains_cleaner_current_paper_live_monitor_base",
    }
    for column, expected in expected_values.items():
        if row.get(column) != expected:
            failures.append(f"{column} expected {expected}, got {row.get(column)}")
    for token in [
        "concentration_cap_or_concentration_control_evidence",
        "component_drawdown_attribution_acceptable_dependency",
        "split_robustness_and_cost_review",
        "portfolio_accounting_consistency",
        "f6_f7_compatibility",
        "risk_policy_review",
        "no_order_instructions_or_scheduling",
    ]:
        if token not in row.get("future_reconsideration_requirements", ""):
            failures.append(f"future requirements missing token: {token}")
    blocker_names = {blocker.get("blocker_name") for blocker in blocker_rows}
    for blocker_name in [
        "high_growth_preview_candidate_false",
        "high_growth_paper_live_candidate_false",
        "high_growth_promotion_not_approved",
        "qqq100_remains_cleaner_current_monitor_base",
        "future_reconsideration_requires_stronger_evidence",
    ]:
        if blocker_name not in blocker_names:
            failures.append(f"blocker output missing {blocker_name}")
    for output_row in decision_rows + summary_rows + blocker_rows:
        assert_false_flags(output_row, failures)


def create_fixture_files(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(
        data / "paper_live_high_growth_evidence_gap_summary.csv",
        ["summary_name", "summary_value"],
        [
            ["areas_missing_evidence", "0"],
            ["final_high_growth_evidence_gap_status", "paper_live_high_growth_evidence_gap_manual_review_required"],
        ],
    )
    write_csv(
        data / "paper_live_high_growth_evidence_gap_blockers.csv",
        ["blocker_name", "details"],
        [["high_growth_saved_evidence_quality_required", "quality review still required"]],
    )
    write_csv(
        data / "paper_live_high_growth_evidence_quality_summary.csv",
        ["summary_name", "summary_value"],
        [
            ["final_quality_status", "high_growth_evidence_quality_manual_review_required"],
            [
                "top_outlier_dependency",
                "top_contributor=TSLA:147.66%;MU:122.88%;PLTR:89.66%; max_single_name_concentration=1.0; warnings=survivorship_bias_warning=true;current_constituent_bias_warning=true;outlier_dependence_warning=true",
            ],
            [
                "worst_drawdown_context",
                "best_candidate=codex_broad_growth_balanced_breakout_control; worst_drawdown=-70.1642; conclusion=decision=high_growth_stock_outlier_dependent; qqq_trend_gate_remains_cleaner_lead",
            ],
            ["largest_manual_review_blocker", "high_growth_quality_manual_review_required"],
        ],
    )
    write_csv(
        data / "paper_live_high_growth_evidence_quality.csv",
        ["review_area", "quality_status", "key_manual_review_issue"],
        [["concentration_quality", "concentration_outlier_manual_review_required", "outlier dependence warning visible"]],
    )
    write_csv(
        data / "paper_live_high_growth_evidence_quality_blockers.csv",
        ["blocker_name", "details"],
        [["high_growth_promotion_not_approved", "High-growth remains research-only."]],
    )
    write_csv(
        data / "paper_live_high_growth_evidence_quality_evidence.csv",
        ["evidence_name", "evidence_value"],
        [["rows_summarized_only", "true"]],
    )


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
        failures.append("never_schedule_order_capable_commands must be true in decision rows")


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


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
