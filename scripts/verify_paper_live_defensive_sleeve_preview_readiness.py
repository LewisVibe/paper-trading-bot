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
MODULE = ROOT / "trading_bot" / "research" / "paper_live_defensive_sleeve_preview_readiness.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = [
    "--paper-live-defensive-sleeve-preview-readiness",
    "--show-paper-live-defensive-sleeve-preview-readiness",
]

OUTPUTS = [
    "data/paper_live_defensive_sleeve_preview_readiness.csv",
    "data/paper_live_defensive_sleeve_preview_readiness_summary.csv",
    "data/paper_live_defensive_sleeve_preview_readiness_blockers.csv",
    "data/paper_live_defensive_sleeve_preview_readiness_evidence.csv",
]

REQUIRED_TOKENS = [
    "defensive_sleeve_preview_candidate_not_approved_manual_review_required",
    "defensive_preview_candidate_not_approved",
    "defensive_sleeve_research_only",
    "qqq100_clean_lead_retained",
    "qqq_100_trend_gate",
    "execution_blocked",
    "preview_candidate_approved",
    "defensive_sleeve_promoted",
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
        print("Paper-live defensive sleeve preview-readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live defensive sleeve preview-readiness verification passed.")
    print("Verified saved-output-only preview readiness, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
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
        failures.append("preview-readiness module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling token in module: {token}")
    display_start = module_source.find("def show_paper_live_defensive_sleeve_preview_readiness")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_paper_live_defensive_sleeve_preview_readiness" in module_source[display_start:]:
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
    for phrase in ["defensive sleeve preview-readiness", "defensive_sleeve_preview_candidate_not_approved_manual_review_required", "not approve", "execution"]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_fixture_output(failures: list[str]) -> None:
    from trading_bot.research.paper_live_defensive_sleeve_preview_readiness import (  # noqa: PLC0415
        generate_paper_live_defensive_sleeve_preview_readiness,
        show_paper_live_defensive_sleeve_preview_readiness,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        data_dir = root / "data"
        data_dir.mkdir()
        write_manual_summary(data_dir / "paper_live_defensive_sleeve_manual_review_summary.csv")
        write_scope_summary(data_dir / "paper_live_defensive_sleeve_ladder_scope_review_summary.csv")
        result = generate_paper_live_defensive_sleeve_preview_readiness(root)
        code, lines = show_paper_live_defensive_sleeve_preview_readiness(root)
        summary = read_csv_rows(result.output_paths["summary"])

    output = "\n".join(result.summary_lines + lines)
    if code != 0:
        failures.append("saved display should return 0 after report generation")
    for phrase in [
        "defensive_sleeve_preview_candidate_not_approved_manual_review_required",
        "preview_candidate_status=defensive_preview_candidate_not_approved",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
        "promotion_approved=false",
        "preview_candidate_approved=false",
        "defensive_sleeve_promoted=false",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")
    for row in summary:
        assert_false_flags(row, failures)


def write_manual_summary(path: Path) -> None:
    path.write_text(
        "summary_name,summary_value,details,execution_approved,paper_execution_approved,scheduling_approved,live_trading_approved,followup_order_approved,repeat_execution_approved,promotion_approved,preview_candidate_approved,defensive_sleeve_promoted\n"
        "final_manual_review_status,defensive_sleeve_manual_review_required,Manual review required,False,False,False,False,False,False,False,False,False\n"
        "preferred_defensive_candidate,volatility_managed_dual_momentum_etf,Candidate context,False,False,False,False,False,False,False,False,False\n",
        encoding="utf-8",
    )


def write_scope_summary(path: Path) -> None:
    path.write_text(
        "summary_name,summary_value,details,execution_approved,paper_execution_approved,scheduling_approved,live_trading_approved,followup_order_approved,repeat_execution_approved,promotion_approved,portfolio_backtest_promotion_evidence_approved,defensive_sleeve_promoted\n"
        "final_defensive_scope_status,defensive_sleeve_ladder_scope_review_ready_for_manual_review,Ready,False,False,False,False,False,False,False,False,False\n",
        encoding="utf-8",
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
