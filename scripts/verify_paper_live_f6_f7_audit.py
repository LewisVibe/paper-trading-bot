from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_live_f6_f7_audit.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = ["--paper-live-f6-f7-audit", "--show-paper-live-f6-f7-audit"]
OUTPUTS = [
    "data/paper_live_f6_f7_audit.csv",
    "data/paper_live_f6_f7_audit_summary.csv",
    "data/paper_live_f6_f7_audit_blockers.csv",
    "data/paper_live_f6_f7_audit_evidence.csv",
]

REQUIRED_MODULE_TOKENS = [
    "audit_item",
    "review_finding",
    "severity",
    "affected_area",
    "current_status",
    "future_action_required",
    "F6_position_unknown_not_assumed_flat",
    "F7_multi_sleeve_portfolio_accounting",
    "position_unknown",
    "position_unavailable",
    "manual_review_required",
    "not_assumed_flat",
    "no_issue_found",
    "needs_manual_review",
    "future_fix_required",
    "insufficient_static_evidence",
    "paper_live_f6_f7_audit_manual_review_required",
    "add_targeted_f6_f7_tests_or_verifiers_before_generic_promotion_ladder",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
    '"followup_order_approved": False',
    '"repeat_execution_approved": False',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
    '"alpaca_called": False',
    '"live_positions_read": False',
]

FORBIDDEN_CALL_TOKENS = [
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
        print("Paper-live F6/F7 audit verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live F6/F7 audit verification passed.")
    print("Verified static F6/F7 audit, false approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-f6-f7-audit": 'if sys.argv[1:] == ["--paper-live-f6-f7-audit"]:',
        "--show-paper-live-f6-f7-audit": 'if sys.argv[1:] == ["--show-paper-live-f6-f7-audit"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live F6/F7 audit module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    if "SourceBundle" not in module_source:
        failures.append("audit should use static source inspection only")


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
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "F6/F7 audit",
        "position unknown",
        "starting-cash",
        "generic promotion ladder",
        "does not approve execution",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_report_output_from_fixture(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.paper_live_f6_f7_audit import (  # noqa: PLC0415
        generate_paper_live_f6_f7_audit,
        show_paper_live_f6_f7_audit,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        copy_static_sources(root)
        result = generate_paper_live_f6_f7_audit(root)
        status_code, lines = show_paper_live_f6_f7_audit(root)

    output = "\n".join(result.summary_lines + lines)
    if status_code != 0:
        failures.append("saved display should return 0 after report generation")
    for phrase in [
        "paper_live_f6_f7_audit_manual_review_required",
        "f6_loud_unknown_position_boundaries_partially_confirmed_manual_review_required",
        "f7_accounting_consistency_manual_review_required",
        "add_targeted_f6_f7_tests_or_verifiers_before_generic_promotion_ladder",
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
    findings = {row.get("review_finding") for row in result.audit_rows}
    for expected in {"no_issue_found", "needs_manual_review", "future_fix_required"}:
        if expected not in findings:
            failures.append(f"fixture audit rows missing finding: {expected}")


def copy_static_sources(root: Path) -> None:
    paths = [
        "trading_bot/research/qqq100_action_preview.py",
        "trading_bot/research/promoted_actions.py",
        "trading_bot/research/promoted_risk.py",
        "trading_bot/research/multi_strategy_portfolio_preview.py",
        "trading_bot/research/multi_sleeve_portfolio_backtest.py",
        "trading_bot/research/sleeve_return_streams.py",
        "docs/PAPER_LIVE_CHECKLIST.md",
    ]
    for relative in paths:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(read_text(source), encoding="utf-8")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
