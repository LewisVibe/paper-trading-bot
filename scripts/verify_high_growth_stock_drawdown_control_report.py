from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "high_growth_stock_drawdown_control.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--high-growth-stock-drawdown-control-report",
    "--show-high-growth-stock-drawdown-control-report",
]

OUTPUTS = [
    "data/high_growth_stock_drawdown_control_report.csv",
    "data/high_growth_stock_drawdown_control_summary.csv",
    "data/high_growth_stock_drawdown_control_trades.csv",
    "data/high_growth_stock_drawdown_control_costs.csv",
    "data/high_growth_stock_drawdown_control_splits.csv",
    "data/high_growth_stock_drawdown_control_drawdowns.csv",
    "data/high_growth_stock_drawdown_control_concentration.csv",
]

REQUIRED_TOKENS = [
    "broad_liquid_growth_50",
    "broad_growth_top1_reference",
    "broad_growth_top2_reference",
    "broad_growth_top3_reference",
    "broad_growth_top1_drawdown_brake",
    "broad_growth_top1_volatility_gate",
    "broad_growth_top1_cooldown_after_crash",
    "codex_broad_growth_balanced_breakout_control",
    "high_growth_stock_survivorship_bias_warning",
    "current_constituent_bias_warning",
    "outlier_dependence_warning",
    "stock_specific_gap_risk_warning",
    "drawdown_warning",
    "drawdown_control_high_growth_research_lead",
    "drawdown_control_promising_but_concentrated",
    "drawdown_control_reduces_drawdown_with_return_drag",
    "drawdown_control_rejected_return_drag",
    "drawdown_control_still_too_deep",
    "qqq_trend_gate_remains_cleaner_lead",
    '"research_only": True',
    '"preview_only": False',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"leverage_execution_approved": False',
    '"margin_approved": False',
    '"short_execution_approved": False',
    '"scheduling_approved": False',
    '"alpaca_called": False',
    '"orders_created": False',
]

FORBIDDEN_TOKENS = [
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
    "python bot.py --paper-order-test",
    "--execute-slow-sma-paper",
    "--confirm-readonly-alpaca-check",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, V2_CHECKPOINT, HERMES_TASK_BOARD])
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("high-growth stock drawdown-control module is missing")
    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("High-growth stock drawdown-control verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("High-growth stock drawdown-control verification passed.")
    print("Verified fixed broad stock universe, ETF benchmark-only use, ignored outputs, safety flags, and non-execution boundaries.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    branches = [
        ("--high-growth-stock-drawdown-control-report", 'if sys.argv[1:] == ["--high-growth-stock-drawdown-control-report"]:'),
        ("--show-high-growth-stock-drawdown-control-report", 'if sys.argv[1:] == ["--show-high-growth-stock-drawdown-control-report"]:'),
    ]
    for command, branch in branches:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early safe branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required drawdown-control token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in module: {token}")
    if "lab.BENCHMARK_TICKERS" not in module_source:
        failures.append("QQQ/SPY should be benchmark/regime references only")
    if "simulate_buy_and_hold_if_available(\"qqq_buy_and_hold_benchmark\", \"QQQ\"" not in module_source:
        failures.append("QQQ should appear as benchmark only")
    if "simulate_buy_and_hold_if_available(\"spy_buy_and_hold_benchmark\", \"SPY\"" not in module_source:
        failures.append("SPY should appear as benchmark only")
    display_start = module_source.find("def show_high_growth_stock_drawdown_control_report")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_high_growth_stock_drawdown_control_report" in display_source:
            failures.append("display command must not regenerate the report")
        for forbidden in ["python bot.py --paper-order-test", "--execute-slow-sma-paper", "--confirm-readonly-alpaca-check"]:
            if forbidden in display_source:
                failures.append(f"terminal display must not print execution-capable command: {forbidden}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "high-growth stock drawdown-control",
        "research-only",
        "survivorship bias",
        "concentration risk",
        "does not approve execution",
        "does not connect strategies to Alpaca or paper orders",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_outputs_ignored(gitignore: str, failures: list[str]) -> None:
    if "data/*" not in gitignore:
        failures.append("generated data outputs must remain ignored by git")
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
