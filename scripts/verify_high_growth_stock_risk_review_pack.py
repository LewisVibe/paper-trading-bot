from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "high_growth_stock_risk_review_pack.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"

COMMANDS = ["--high-growth-stock-risk-review-pack", "--show-high-growth-stock-risk-review-pack"]
OUTPUTS = [
    "data/high_growth_stock_risk_review_pack.csv",
    "data/high_growth_stock_risk_review_summary.csv",
    "data/high_growth_stock_risk_review_evidence.csv",
    "data/high_growth_stock_risk_review_blockers.csv",
]

REQUIRED_TOKENS = [
    "high_growth_risk_review_required",
    "cost_review_required",
    "split_review_required",
    "concentration_review_required",
    "drawdown_review_required",
    "survivorship_bias_warning",
    "outlier_dependence_warning",
    "high_risk_branch_research_only",
    "preview_candidate_still_blocked",
    "execution_blocked",
    "qqq_100_trend_gate",
    "codex_broad_growth_balanced_breakout_control",
    "broad_liquid_growth_50:concentrated_growth_momentum_top1",
    '"research_only": True',
    '"preview_only": True',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
]

FORBIDDEN_TOKENS = [
    "download_daily_price_data",
    "yf.",
    "import yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "replace_order",
    "create_order",
    "get_alpaca_positions",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "load_config(",
    "config.json",
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
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, V2_CHECKPOINT, HERMES_TASK_BOARD])

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(failures)

    if failures:
        print("High-growth stock risk review pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("High-growth stock risk review pack verification passed.")
    print("Verified saved-output-only risk review, clean lead retention, high-risk research-only label, rejected Top1 reference, ignored outputs, and non-execution boundaries.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--high-growth-stock-risk-review-pack", 'if sys.argv[1:] == ["--high-growth-stock-risk-review-pack"]:'),
        ("--show-high-growth-stock-risk-review-pack", 'if sys.argv[1:] == ["--show-high-growth-stock-risk-review-pack"]:'),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early safe branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("risk review pack module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required risk-review token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/refresh/config/scheduling token in module: {token}")
    if "read_csv_rows" not in module_source:
        failures.append("risk review pack should read saved CSV outputs only")
    display_start = module_source.find("def show_high_growth_stock_risk_review_pack")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_high_growth_stock_risk_review_pack" in display_source:
            failures.append("display command must not regenerate the pack")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in ["high-growth stock risk review pack", "saved-output", "research-only", "does not approve execution"]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(["git", "check-ignore", output], cwd=ROOT, check=False, capture_output=True, text=True, timeout=10)
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
