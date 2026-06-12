from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
LAB_MODULE = ROOT / "trading_bot" / "research" / "strategy_improvement_lab.py"
ROBUSTNESS_MODULE = ROOT / "trading_bot" / "research" / "strategy_improvement_robustness.py"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--strategy-improvement-robustness",
    "--show-strategy-improvement-robustness",
]

OUTPUTS = [
    "data/strategy_improvement_robustness_report.csv",
    "data/strategy_improvement_cost_stress_report.csv",
    "data/strategy_improvement_drawdown_report.csv",
    "data/strategy_improvement_candidate_comparison.csv",
]

NEW_VARIANTS = [
    "factor_style_rotation_absolute_gate",
    "sector_52_week_high_continuation",
    "adaptive_multi_sleeve_growth_allocator",
]

FIXED_SPLITS = ["split_60_40", "split_70_30", "split_80_20"]
FIXED_COSTS = ["low_cost", "default_cost", "high_cost"]

COMPARISON_LABELS = [
    "strongest_growth_candidate",
    "strongest_risk_adjusted_candidate",
    "strongest_overall_research_candidate",
    "ambitious_growth_candidate",
    "promising_but_drawdown_heavy",
    "defensive_but_return_drag",
    "split_sensitive",
    "cost_sensitive",
    "not_useful",
    "insufficient_data",
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
    "allow_shorting = True",
    "leverage",
    "margin",
    "sched.scheduler",
    "Task Scheduler",
    "cron",
]

BROAD_SEARCH_TOKENS = [
    "param_grid",
    "grid_search",
    "itertools.product",
    "optimize",
    "random.",
    "sklearn",
    "tensorflow",
    "torch",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    lab_source = read_text(LAB_MODULE)
    robustness_source = read_text(ROBUSTNESS_MODULE)
    gitignore = read_text(GITIGNORE)

    if not ROBUSTNESS_MODULE.exists():
        failures.append("strategy improvement robustness module is missing")

    verify_commands(bot_source, failures)
    verify_lab_variants(lab_source, failures)
    verify_robustness_contract(robustness_source, failures)
    verify_outputs_ignored(gitignore, failures)
    verify_display_saved_csv_only(robustness_source, failures)

    if failures:
        print("Strategy improvement robustness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Strategy improvement robustness verification passed.")
    print("Verified fixed variants, fixed split/cost reports, saved display path, and false approval flags.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--strategy-improvement-robustness", "if args.strategy_improvement_robustness:"),
        ("--show-strategy-improvement-robustness", "if args.show_strategy_improvement_robustness:"),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing pre-config branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_lab_variants(lab_source: str, failures: list[str]) -> None:
    for variant in NEW_VARIANTS:
        if variant not in lab_source:
            failures.append(f"missing new fixed strategy variant: {variant}")
    for token in [
        "FACTOR_STYLE_ETFS",
        "SECTOR_52_WEEK_ETFS",
        "MULTI_SLEEVE_GROWTH_ETFS",
        "MULTI_SLEEVE_FACTOR_ETFS",
        "MULTI_SLEEVE_DEFENSIVE_ETFS",
        "rank_by_sector_continuation",
        "rank_by_multi_sleeve_score",
    ]:
        if token not in lab_source:
            failures.append(f"missing fixed strategy implementation token: {token}")


def verify_robustness_contract(robustness_source: str, failures: list[str]) -> None:
    for output in OUTPUTS:
        if output not in robustness_source:
            failures.append(f"missing generated robustness output: {output}")
    for split in FIXED_SPLITS:
        if split not in robustness_source:
            failures.append(f"missing fixed chronological split: {split}")
    for cost in FIXED_COSTS:
        if cost not in robustness_source:
            failures.append(f"missing fixed cost assumption: {cost}")
    for label in COMPARISON_LABELS:
        if label not in robustness_source:
            failures.append(f"missing comparison label: {label}")
    for token in [
        '"execution_approved"] = False',
        '"paper_execution_approved"] = False',
        "research_only",
        "preview_only",
        "Warning: robustness labels are research labels only",
    ]:
        if token not in robustness_source:
            failures.append(f"missing research-only safety token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in robustness_source:
            failures.append(f"forbidden execution/scheduling/config token in robustness module: {token}")
    for token in BROAD_SEARCH_TOKENS:
        if token in robustness_source:
            failures.append(f"forbidden broad-search/ML token in robustness module: {token}")


def verify_outputs_ignored(gitignore: str, failures: list[str]) -> None:
    if "data/*" not in gitignore:
        failures.append("generated data outputs must remain ignored by git")


def verify_display_saved_csv_only(robustness_source: str, failures: list[str]) -> None:
    start = robustness_source.find("def show_strategy_improvement_robustness_file")
    if start == -1:
        failures.append("saved robustness display function is missing")
        return
    display_source = robustness_source[start:]
    for token in ["download_daily_price_data", "generate_strategy_improvement_robustness", "yf.download"]:
        if token in display_source:
            failures.append(f"display path must not refresh market data: {token}")
    if "csv.DictReader" not in display_source:
        failures.append("display path should read saved CSV rows")
    if "Run `python bot.py --strategy-improvement-robustness` first." not in display_source:
        failures.append("display path should print helpful missing-file guidance")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
