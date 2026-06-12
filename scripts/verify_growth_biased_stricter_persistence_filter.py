from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "growth_biased_stricter_persistence_filter.py"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--growth-biased-stricter-persistence-filter",
    "--show-growth-biased-stricter-persistence-filter",
]

OUTPUTS = [
    "data/growth_biased_stricter_persistence_filter.csv",
    "data/growth_biased_stricter_persistence_filter_summary.csv",
]

VARIANTS = [
    "stricter_55_reference",
    "stricter_55_min_hold_2m",
    "stricter_55_min_hold_3m",
    "stricter_55_momentum_gap_5pp",
    "stricter_55_near_top2_hold",
    "stricter_55_combined_persistence",
    "codex_ambitious_concentrated_growth_persistence",
]

REQUIRED_TOKENS = [
    'ACTIVE_RESEARCH_LEAD = "growth_biased_rotation_breadth_stricter_gate"',
    'PREVIOUS_RESEARCH_LEAD = "growth_biased_rotation_crash_gate"',
    'MONTHLY_ROTATION_REFERENCE = "monthly_etf_momentum_rotation_reference"',
    'SPY_BENCHMARK = "spy_buy_and_hold_benchmark"',
    'EQUAL_WEIGHT_BENCHMARK = "equal_weight_etf_buy_and_hold_benchmark"',
    "COST_LEVELS_BPS = [0, 10, 25, 50]",
    "persistence_filter_improved_cost_survival",
    "persistence_filter_promising_but_cost_sensitive",
    "persistence_filter_return_drag",
    "persistence_filter_turnover_reduced_but_edge_lost",
    "persistence_filter_not_useful",
    "ambitious_candidate_promising",
    "ambitious_candidate_high_return_high_risk",
    "ambitious_candidate_cost_sensitive",
    "ambitious_candidate_not_useful",
    "ambitious_candidate_needs_manual_review",
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
        failures.append("persistence filter module is missing")

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Growth-biased stricter persistence filter verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Growth-biased stricter persistence filter verification passed.")
    print("Verified fixed persistence variants, Codex ambitious candidate, false approval flags, and display-only command.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--growth-biased-stricter-persistence-filter", "if args.growth_biased_stricter_persistence_filter:"),
        ("--show-growth-biased-stricter-persistence-filter", "if args.show_growth_biased_stricter_persistence_filter:"),
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
    for variant in VARIANTS:
        if variant not in module_source:
            failures.append(f"missing persistence variant or Codex strategy: {variant}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required persistence token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in persistence module: {token}")

    display_start = module_source.find("def show_growth_biased_stricter_persistence_filter_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_growth_biased_stricter_persistence_filter" in display_source:
            failures.append("display command must not regenerate the persistence report")
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
