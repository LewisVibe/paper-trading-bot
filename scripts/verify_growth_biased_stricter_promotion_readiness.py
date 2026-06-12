from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "growth_biased_stricter_promotion_readiness.py"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--growth-biased-stricter-promotion-readiness",
    "--show-growth-biased-stricter-promotion-readiness",
]

OUTPUTS = [
    "data/growth_biased_stricter_promotion_readiness.csv",
    "data/growth_biased_stricter_promotion_blockers.csv",
]

SAVED_INPUTS = [
    "data/growth_biased_stricter_validation.csv",
    "data/growth_biased_stricter_split_validation.csv",
    "data/growth_biased_stricter_cost_review.csv",
    "data/growth_biased_stricter_drawdown_review.csv",
    "data/growth_biased_stricter_benchmark_comparison.csv",
    "data/growth_biased_stricter_promotion_checkpoint.csv",
    "data/strategy_improvement_candidate_comparison.csv",
    "data/strategy_improvement_diagnostics.csv",
    "data/growth_biased_rotation_diagnostics.csv",
]

REQUIRED_TOKENS = [
    'ACTIVE_RESEARCH_LEAD = "growth_biased_rotation_breadth_stricter_gate"',
    "benchmark_lagging_but_acceptable_for_active_candidate",
    "benchmark_gap_requires_review",
    "benchmark_comparison_pass",
    "split_validation_pass",
    "split_validation_mixed_requires_review",
    "split_validation_fail",
    "cost_resilient",
    "cost_sensitive_requires_review",
    "cost_advantage_lost",
    "drawdown_acceptable_for_return",
    "drawdown_watch_requires_review",
    "drawdown_unacceptable",
    "saved_outputs_current",
    "saved_outputs_stale",
    "saved_outputs_missing",
    "not_ready_for_preview",
    "nearly_ready_needs_manual_review",
    "ready_for_future_preview_discussion",
    '"research_only": True',
    '"preview_only": True',
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
    "load_config(",
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
        failures.append("promotion-readiness module is missing")

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Growth-biased stricter promotion-readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Growth-biased stricter promotion-readiness verification passed.")
    print("Verified saved-output blocker report, false approval flags, and display-only command.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        (
            "--growth-biased-stricter-promotion-readiness",
            "if args.growth_biased_stricter_promotion_readiness:",
        ),
        (
            "--show-growth-biased-stricter-promotion-readiness",
            "if args.show_growth_biased_stricter_promotion_readiness:",
        ),
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
            failures.append(f"missing required readiness token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in readiness module: {token}")

    display_start = module_source.find("def show_growth_biased_stricter_promotion_readiness_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_growth_biased_stricter_promotion_readiness" in display_source:
            failures.append("display command must not regenerate readiness report")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")

    if "new strategy" in module_source.lower():
        failures.append("readiness report must not add or describe new strategy variants")


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
