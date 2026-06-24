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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_high_growth_evidence_quality.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-high-growth-evidence-quality",
    "--show-paper-live-high-growth-evidence-quality",
]

OUTPUTS = [
    "data/paper_live_high_growth_evidence_quality.csv",
    "data/paper_live_high_growth_evidence_quality_summary.csv",
    "data/paper_live_high_growth_evidence_quality_blockers.csv",
    "data/paper_live_high_growth_evidence_quality_evidence.csv",
]

REQUIRED_COLUMNS = [
    "review_area",
    "evidence_present",
    "quality_status",
    "key_manual_review_issue",
    "current_blocker",
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
    "paper_live_high_growth_evidence_quality.csv",
    "concentration_quality",
    "drawdown_quality",
    "attribution_quality",
    "bias_risk_warnings",
    "promotion_readiness",
    "high_growth_evidence_quality_manual_review_required",
    "high_growth_research_only_not_promotion_ready",
    "TSLA",
    "Saved-output/manual-review only",
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
    verify_fixture_output(failures)

    if failures:
        print("Paper-live high-growth evidence quality verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live high-growth evidence quality verification passed.")
    print("Verified saved-output manual-review quality report, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-high-growth-evidence-quality": 'if sys.argv[1:] == ["--paper-live-high-growth-evidence-quality"]:',
        "--show-paper-live-high-growth-evidence-quality": 'if sys.argv[1:] == ["--show-paper-live-high-growth-evidence-quality"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live high-growth evidence quality module is missing")
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
        "high-growth evidence quality",
        "manual-review context",
        "No high-growth sleeve is promoted",
        "outlier",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    from trading_bot.research.paper_live_high_growth_evidence_quality import (  # noqa: PLC0415
        generate_paper_live_high_growth_evidence_quality,
        show_paper_live_high_growth_evidence_quality,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture_files(root)
        result = generate_paper_live_high_growth_evidence_quality(root)
        status_code, lines = show_paper_live_high_growth_evidence_quality(root)
        review_rows = read_csv_rows(result.output_paths["review"])
        summary_rows = read_csv_rows(result.output_paths["summary"])

    if status_code != 0:
        failures.append("saved display should return 0 after quality report generation")
    output = "\n".join(result.summary_lines + lines)
    for phrase in [
        "high_growth_evidence_quality_manual_review_required",
        "TSLA",
        "-70.1642",
        "high_growth_quality_manual_review_required",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "live_trading_approved=false",
        "followup_order_approved=false",
        "repeat_execution_approved=false",
        "high_growth_promotion_approved=false",
        "never_schedule_order_capable_commands=true",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")
    for column in REQUIRED_COLUMNS:
        if review_rows and column not in review_rows[0]:
            failures.append(f"review output missing required column: {column}")
    areas = {row.get("review_area") for row in review_rows}
    for area in ["concentration_quality", "drawdown_quality", "attribution_quality", "bias_risk_warnings", "promotion_readiness"]:
        if area not in areas:
            failures.append(f"review output missing area: {area}")
    for row in review_rows + summary_rows:
        assert_false_flags(row, failures)


def create_fixture_files(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(data / "paper_live_high_growth_evidence_gap_summary.csv", ["summary_name", "summary_value"], [["areas_missing_evidence", "0"]])
    write_csv(
        data / "high_growth_stock_drawdown_control_summary.csv",
        ["summary_name", "summary_value"],
        [
            ["best_drawdown_control_candidate", "codex_broad_growth_balanced_breakout_control"],
            ["final_research_conclusion", "high_growth_stock_outlier_dependent; qqq_trend_gate_remains_cleaner_lead"],
        ],
    )
    write_csv(
        data / "high_growth_stock_drawdown_control_drawdowns.csv",
        ["strategy_name", "max_drawdown", "largest_contributor", "outlier_dependence_warning"],
        [["broad_growth_top1_reference", "-70.1642", "TSLA", "true"]],
    )
    write_csv(
        data / "high_growth_stock_drawdown_control_concentration.csv",
        [
            "strategy_name",
            "max_single_name_concentration",
            "largest_contributor",
            "survivorship_bias_warning",
            "current_constituent_bias_warning",
            "outlier_dependence_warning",
        ],
        [["broad_growth_top1_reference", "1.0", "TSLA", "true", "true", "true"]],
    )
    write_csv(data / "high_growth_stock_drawdown_control_report.csv", ["strategy_name", "decision_label"], [["codex_broad_growth_balanced_breakout_control", "high_growth_stock_outlier_dependent"]])
    write_csv(data / "high_growth_component_attribution.csv", ["component_ticker", "component_weighted_contribution"], [["TSLA", "0.12"]])
    write_csv(data / "high_growth_component_attribution_summary.csv", ["summary_name", "summary_value"], [["final_component_attribution_status", "component_attribution_created_research_only"]])
    write_csv(data / "high_growth_component_contributions.csv", ["component_ticker", "weighted_contribution"], [["TSLA", "0.12"]])
    write_csv(data / "high_growth_component_drawdown_contributions.csv", ["component_ticker", "contribution_share_of_high_growth_drawdown"], [["TSLA", "0.42"]])
    write_csv(data / "high_growth_component_streams_summary.csv", ["summary_name", "summary_value"], [["component_stream_status", "high_growth_component_streams_created_research_only"]])
    write_csv(data / "high_growth_stock_manual_review_blockers.csv", ["blocker_name", "details"], [["survivorship_bias_warning", "survivorship warning visible"]])
    write_csv(data / "high_growth_stock_risk_review_blockers.csv", ["blocker_name", "details"], [["outlier_dependence_warning", "outlier dependence warning visible"]])


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
        failures.append("never_schedule_order_capable_commands must be true in review rows")


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
