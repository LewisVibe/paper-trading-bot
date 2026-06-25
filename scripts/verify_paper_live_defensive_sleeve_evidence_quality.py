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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_defensive_sleeve_evidence_quality.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-defensive-sleeve-evidence-quality",
    "--show-paper-live-defensive-sleeve-evidence-quality",
]

OUTPUTS = [
    "data/paper_live_defensive_sleeve_evidence_quality.csv",
    "data/paper_live_defensive_sleeve_evidence_quality_summary.csv",
    "data/paper_live_defensive_sleeve_evidence_quality_blockers.csv",
    "data/paper_live_defensive_sleeve_evidence_quality_evidence.csv",
]

REQUIRED_TOKENS = [
    "defensive_sleeve_evidence_quality_manual_review_required",
    "split_sensitivity_manual_review_required",
    "full_period_drawdown_manual_review_required",
    "qqq100_clean_lead_retained",
    "defensive_preview_candidate_not_approved",
    "manual_review_split_drawdown_and_allocation_blockers_before_defensive_preview_design",
    "volatility_managed_dual_momentum_etf",
    "monthly_etf_momentum_rotation",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"promotion_approved": False',
    '"preview_candidate_approved": False',
    '"defensive_sleeve_promoted": False',
    '"alpaca_called": False',
    '"live_positions_read": False',
    '"market_data_refreshed": False',
    '"yfinance_called": False',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
]

FORBIDDEN_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_alpaca_positions(",
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
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, PAPER_LIVE_CHECKLIST])

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_docs(docs_source, failures)
    verify_fixture_output(failures)

    if failures:
        print("Paper-live defensive sleeve evidence-quality verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live defensive sleeve evidence-quality verification passed.")
    print("Verified saved-output-only evidence quality review, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
        branch = f'if sys.argv[1:] == ["{command}"]:'
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("defensive evidence-quality module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling token in module: {token}")
    display_start = module_source.find("def show_paper_live_defensive_sleeve_evidence_quality")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_paper_live_defensive_sleeve_evidence_quality" in module_source[display_start:]:
        failures.append("display command must not regenerate the report")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(["git", "check-ignore", output], cwd=ROOT, check=False, capture_output=True, text=True, timeout=10)
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for phrase in [
        "defensive sleeve evidence-quality",
        "defensive_sleeve_evidence_quality_manual_review_required",
        "split",
        "drawdown",
        "not approve",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    from trading_bot.research.paper_live_defensive_sleeve_evidence_quality import (  # noqa: PLC0415
        generate_paper_live_defensive_sleeve_evidence_quality,
        show_paper_live_defensive_sleeve_evidence_quality,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        create_fixture_files(root)
        result = generate_paper_live_defensive_sleeve_evidence_quality(root)
        code, lines = show_paper_live_defensive_sleeve_evidence_quality(root)
        review_rows = read_csv_rows(result.output_paths["review"])
        summary_rows = read_csv_rows(result.output_paths["summary"])

    output = "\n".join(result.summary_lines + lines)
    if code != 0:
        failures.append("saved display should return 0 after report generation")
    for phrase in [
        "defensive_sleeve_evidence_quality_manual_review_required",
        "volatility_managed_dual_momentum_etf",
        "split_sensitivity_manual_review_required",
        "full_period_drawdown_manual_review_required",
        "blocked_not_ready_for_execution_design",
        "defensive_preview_candidate_not_approved",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "promotion_approved=false",
        "preview_candidate_approved=false",
        "defensive_sleeve_promoted=false",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")
    areas = {row.get("review_area") for row in review_rows}
    for area in ["candidate_strength", "split_sensitivity", "full_period_drawdown", "allocation_decision", "qqq100_role_boundary", "preview_execution_boundary"]:
        if area not in areas:
            failures.append(f"review output missing area: {area}")
    for row in review_rows + summary_rows:
        assert_false_flags(row, failures)


def create_fixture_files(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(
        data / "paper_live_defensive_sleeve_manual_review_summary.csv",
        ["summary_name", "summary_value"],
        [
            ["final_manual_review_status", "defensive_sleeve_manual_review_required"],
            ["preferred_defensive_candidate", "volatility_managed_dual_momentum_etf"],
        ],
    )
    write_csv(
        data / "paper_live_defensive_sleeve_preview_readiness_summary.csv",
        ["summary_name", "summary_value"],
        [
            ["final_preview_readiness_status", "defensive_sleeve_preview_candidate_not_approved_manual_review_required"],
            ["preview_candidate_status", "defensive_preview_candidate_not_approved"],
        ],
    )
    write_csv(
        data / "defensive_candidate_comparison.csv",
        ["strategy_name", "out_of_sample_cagr_pct", "out_of_sample_sharpe", "out_of_sample_calmar", "out_of_sample_max_drawdown_pct", "defensive_score"],
        [["volatility_managed_dual_momentum_etf", "16.46", "1.26", "1.62", "10.15", "86"]],
    )
    write_csv(
        data / "vol_managed_etf_robustness_report.csv",
        ["strategy_name", "split_name", "out_of_sample_calmar"],
        [
            ["volatility_managed_dual_momentum_etf", "split_60_40", "1.2753"],
            ["volatility_managed_dual_momentum_etf", "split_80_20", "1.6342"],
        ],
    )
    write_csv(
        data / "etf_defensive_drawdown_comparison.csv",
        ["comparison_period", "strategy_name", "drawdown_depth_pct"],
        [
            ["full_period_worst_drawdown", "monthly_etf_momentum_rotation", "20.1858"],
            ["full_period_worst_drawdown", "volatility_managed_dual_momentum_etf", "25.7488"],
            ["split_80_20_out_of_sample", "monthly_etf_momentum_rotation", "11.2666"],
            ["split_80_20_out_of_sample", "volatility_managed_dual_momentum_etf", "10.1051"],
        ],
    )
    write_csv(data / "defensive_allocation_preview.csv", ["component", "preview_label"], [["execution_state", "blocked_no_execution_approval"]])
    write_csv(
        data / "defensive_allocation_risk_preview.csv",
        ["risk_check", "risk_status"],
        [["vol_managed_split_sensitive", "warning"], ["execution_gate_blocked", "blocked"]],
    )
    write_csv(
        data / "defensive_allocation_decision_report.csv",
        ["decision_area", "decision_label"],
        [["overall_decision", "blocked_not_ready_for_execution_design"]],
    )


def assert_false_flags(row: dict[str, str], failures: list[str]) -> None:
    for field in [
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "live_trading_approved",
        "promotion_approved",
        "preview_candidate_approved",
        "defensive_sleeve_promoted",
    ]:
        if field in row and str(row.get(field, "")).lower() != "false":
            failures.append(f"{field} must be false in output rows")


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


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
