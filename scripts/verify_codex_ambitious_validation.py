from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "codex_ambitious_validation.py"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--codex-ambitious-validation",
    "--show-codex-ambitious-validation",
]

OUTPUTS = [
    "data/codex_ambitious_validation.csv",
    "data/codex_ambitious_validation_summary.csv",
    "data/codex_ambitious_validation_splits.csv",
    "data/codex_ambitious_validation_costs.csv",
    "data/codex_ambitious_validation_drawdowns.csv",
]

REQUIRED_TOKENS = [
    'TARGET_STRATEGY = "codex_ambitious_concentrated_growth_persistence"',
    'SPY_BENCHMARK = "spy_buy_and_hold_benchmark"',
    'EQUAL_WEIGHT_BENCHMARK = "equal_weight_etf_buy_and_hold_benchmark"',
    'MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"',
    'PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"',
    'STRICTER_GATE = "growth_biased_rotation_breadth_stricter_gate"',
    'STRICTER_55_REFERENCE = "stricter_55_reference"',
    "codex_ambitious_new_active_research_lead",
    "codex_ambitious_promising_needs_cost_review",
    "codex_ambitious_promising_but_split_sensitive",
    "codex_ambitious_high_return_high_risk",
    "codex_ambitious_cost_fragile",
    "codex_ambitious_not_validated",
    "insufficient_saved_inputs",
    "manual_review_required",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"promotion_approved": False',
    '"scheduling_approved": False',
    "does not approve orders",
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
    "download_daily_price_data",
    "allow_shorting = True",
    "leverage",
    "margin",
    "sched.scheduler",
    "Task Scheduler",
    "cron",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("Codex ambitious validation module is missing")

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Codex ambitious validation verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Codex ambitious validation verification passed.")
    print("Verified saved-output validation, false approval flags, and display-only command.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--codex-ambitious-validation", "if args.codex_ambitious_validation:"),
        ("--show-codex-ambitious-validation", "if args.show_codex_ambitious_validation:"),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing pre-config branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing output file path: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required validation token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in validation module: {token}")

    display_start = module_source.find("def show_codex_ambitious_validation_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_codex_ambitious_validation" in display_source:
            failures.append("display command must not regenerate validation")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")


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
