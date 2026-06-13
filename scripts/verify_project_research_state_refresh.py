from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "project_research_state_refresh.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--project-research-state-refresh",
    "--show-project-research-state-refresh",
]

OUTPUTS = [
    "data/project_research_state_refresh.csv",
    "data/project_research_state_summary.csv",
    "data/project_research_state_next_steps.csv",
]

REQUIRED_TOKENS = [
    "qqq_100_trend_gate",
    "qqq_100_trend_gate_new_research_lead",
    "codex_qqq_adaptive_trend_exposure",
    "qqq_150_trend_gate",
    "codex_ambitious_concentrated_growth_persistence",
    "crypto_equal_weight_ex_highest_vol_2",
    "crypto_manual_review_not_ready_for_preview_discussion",
    "stock_etf_ambitious_alternative",
    "stock_etf_rejected_high_drawdown_reference",
    "review_qqq_trend_gate_as_new_stock_etf_research_lead",
    "stock_etf_blockers",
    "crypto_blockers",
    "stock_etf_cost_review_next",
    "stock_etf_monitoring_dashboard_next",
    "crypto_manual_review_next",
    "crypto_cost_and_outlier_review_next",
    "project_dashboard_refresh_next",
    "pause_strategy_iterations_and_improve_reporting",
    "vps_monitoring_refresh_review",
    "insufficient_saved_inputs",
    '"execution_approved": False',
    '"scheduling_approved": False',
    '"paper_execution_approved": False',
    '"crypto_execution_approved": False',
    '"leverage_execution_approved": False',
    '"margin_approved": False',
    '"short_execution_approved": False',
    '"alpaca_called": False',
    '"orders_created": False',
    '"preview_promotion_approved": False',
    "does not approve preview promotion",
]

FORBIDDEN_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "create_order",
    "get_alpaca_positions",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "load_config(",
    "config.json",
    "yfinance",
    "yf.download",
    "allow_shorting = True",
    "enable_margin",
    "sched.scheduler",
    "Task Scheduler",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, V2_CHECKPOINT, HERMES_TASK_BOARD])
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("project research state refresh module is missing")
    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Project research state refresh verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Project research state refresh verification passed.")
    print("Verified saved-output project checkpoint, false approval flags, non-execution wording, and ignored outputs.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--project-research-state-refresh", "if args.project_research_state_refresh:"),
        ("--show-project-research-state-refresh", "if args.show_project_research_state_refresh:"),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing pre-config branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing project-refresh token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in module: {token}")
    display_start = module_source.find("def show_project_research_state_refresh_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_project_research_state_refresh" in display_source:
            failures.append("display command must not regenerate the project refresh")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "research/report-only",
        "consolidates current stock/ETF and crypto research state",
        "does not approve preview promotion",
        "does not approve execution",
        "does not connect strategies to Alpaca or paper orders",
        "choose the next research/reporting direction",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_outputs_ignored(gitignore: str, failures: list[str]) -> None:
    if "data/*" not in gitignore:
        failures.append("generated data outputs must remain ignored by git")
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
