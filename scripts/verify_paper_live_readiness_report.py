from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_live_readiness_report.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
CODEX_WORKFLOW = ROOT / "docs" / "CODEX_WORKFLOW.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
PAPER_LIVE_CHECKLIST = ROOT / "docs" / "PAPER_LIVE_CHECKLIST.md"

COMMANDS = ["--paper-live-readiness-report", "--show-paper-live-readiness-report"]
OUTPUTS = [
    "data/paper_live_readiness_report.csv",
    "data/paper_live_readiness_summary.csv",
    "data/paper_live_readiness_blockers.csv",
    "data/paper_live_readiness_evidence.csv",
]

REQUIRED_MODULE_TOKENS = [
    "qqq_100_trend_gate",
    "QQQ",
    "repo_safety_verifier_exists",
    "baseline_freeze_verifier_exists",
    "paper_live_promotion_gate_exists",
    "qqq100_exact_alignment_verifier_exists",
    "execute_qqq100_verifier_exists",
    "normal_bot_monitoring_only",
    "alpaca_paper_only_boundary",
    "qqq100_fixed_ticker",
    "qqq100_fixed_strategy",
    "qqq100_exact_zero_one_alignment",
    "sma_slow_sma_not_promoted",
    "high_growth_not_promoted",
    "crypto_not_promoted",
    "paper_execution_separate_confirmed",
    "open_order_checks_required",
    "duplicate_order_checks_required",
    "position_readability_postcheck_required",
    "portfolio_risk_review_evidence",
    "execution_readiness_evidence",
    "scheduling_false_no_order_cron",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
    '"live_trading_approved": False',
]

FORBIDDEN_CALL_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    "submit_alpaca_order(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_alpaca_positions(",
    "get_all_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "download_daily_price_data(",
    "yf.",
    "import yfinance",
    "sched.scheduler",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, CODEX_WORKFLOW, HERMES_TASK_BOARD, PAPER_LIVE_CHECKLIST])

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(failures)

    if failures:
        print("Paper-live readiness report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper-live readiness report verification passed.")
    print("Verified saved-output QQQ100 readiness report, false execution/paper/scheduling/live approvals, ignored outputs, and no broker/order/config/scheduling calls.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = {
        "--paper-live-readiness-report": 'if sys.argv[1:] == ["--paper-live-readiness-report"]:',
        "--show-paper-live-readiness-report": 'if sys.argv[1:] == ["--show-paper-live-readiness-report"]:',
    }
    for command, branch in branches.items():
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early report-only route for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("paper-live readiness report module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing required module token: {token}")
    for token in FORBIDDEN_CALL_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broker/order/config/market/scheduling call token in module: {token}")
    if "read_csv_rows" not in module_source:
        failures.append("readiness report should read saved CSV evidence only")
    display_start = module_source.find("def show_paper_live_readiness_report")
    if display_start == -1:
        failures.append("missing saved-display function")
    elif "generate_paper_live_readiness_report" in module_source[display_start:]:
        failures.append("display command must not regenerate the report")
    for phrase in [
        "not order approval",
        "Live trading remains out of scope",
        "Scheduling order-capable commands remains prohibited",
    ]:
        if phrase not in module_source:
            failures.append(f"missing boundary phrase: {phrase}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "paper-live readiness report",
        "qqq_100_trend_gate",
        "does not approve execution",
        "live_trading_approved",
        "scheduling_approved",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


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


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
