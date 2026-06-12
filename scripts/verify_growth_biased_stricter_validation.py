from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "growth_biased_stricter_validation.py"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--growth-biased-stricter-validation",
    "--show-growth-biased-stricter-validation",
]

OUTPUTS = [
    "data/growth_biased_stricter_validation.csv",
    "data/growth_biased_stricter_split_validation.csv",
    "data/growth_biased_stricter_cost_review.csv",
    "data/growth_biased_stricter_drawdown_review.csv",
    "data/growth_biased_stricter_promotion_checkpoint.csv",
]

SAVED_INPUTS = [
    "data/strategy_improvement_lab_results.csv",
    "data/strategy_improvement_lab_summary.csv",
    "data/strategy_improvement_robustness_report.csv",
    "data/strategy_improvement_cost_stress_report.csv",
    "data/strategy_improvement_drawdown_report.csv",
    "data/strategy_improvement_candidate_comparison.csv",
    "data/strategy_improvement_diagnostics.csv",
    "data/growth_biased_rotation_diagnostics.csv",
]

REQUIRED_TOKENS = [
    "ACTIVE_RESEARCH_LEAD = \"growth_biased_rotation_breadth_stricter_gate\"",
    "PREVIOUS_RESEARCH_LEAD = \"growth_biased_rotation_crash_gate\"",
    "growth_biased_rotation_cost_aware_rebalance",
    "growth_biased_rotation_partial_defensive_sleeve",
    "growth_biased_rotation_reentry_filter",
    "growth_biased_rotation_regime_recovery_filter",
    "growth_biased_rotation_breadth_looser_gate",
    "validation_pass_research_lead",
    "validation_promising_needs_more_splits",
    "validation_cost_sensitive",
    "validation_drawdown_watch",
    "validation_benchmark_lagging",
    "validation_not_ready_for_preview",
    "stricter_cost_resilient",
    "stricter_cost_sensitive",
    "stricter_cost_advantage_lost",
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"research_only": True',
    '"preview_only": True',
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
        failures.append("growth-biased stricter validation module is missing")

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Growth-biased stricter validation verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Growth-biased stricter validation verification passed.")
    print("Verified saved-output validation, false approval flags, and display-only command.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--growth-biased-stricter-validation", "if args.growth_biased_stricter_validation:"),
        ("--show-growth-biased-stricter-validation", "if args.show_growth_biased_stricter_validation:"),
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
    for saved_input in SAVED_INPUTS:
        if saved_input not in module_source:
            failures.append(f"missing saved input file path: {saved_input}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required validation token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in validation module: {token}")
    display_start = module_source.find("def show_growth_biased_stricter_validation_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_growth_biased_stricter_validation" in display_source:
            failures.append("display command must not regenerate validation")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")


def verify_outputs_ignored(gitignore: str, failures: list[str]) -> None:
    if "data/*" not in gitignore:
        failures.append("generated data outputs must remain ignored by git")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
