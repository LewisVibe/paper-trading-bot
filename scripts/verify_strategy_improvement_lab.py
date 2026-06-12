from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "strategy_improvement_lab.py"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--strategy-improvement-lab",
    "--show-strategy-improvement-lab",
]

OUTPUTS = [
    "data/strategy_improvement_lab_results.csv",
    "data/strategy_improvement_lab_trades.csv",
    "data/strategy_improvement_lab_equity_curve.csv",
    "data/strategy_improvement_lab_summary.csv",
    "data/strategy_improvement_lab_iteration_log.csv",
]

FIXED_VARIANTS = [
    "monthly_etf_momentum_rotation_reference",
    "balanced_dual_momentum_defensive_sleeve",
    "breadth_aware_risk_on_rotation",
    "growth_biased_rotation_crash_gate",
    "factor_style_rotation_absolute_gate",
    "sector_52_week_high_continuation",
    "adaptive_multi_sleeve_growth_allocator",
]

DECISION_LABELS = [
    "promising_growth_candidate",
    "promising_but_drawdown_heavy",
    "defensive_but_return_drag",
    "split_sensitive",
    "not_useful",
    "insufficient_data",
]

FORBIDDEN_MODULE_TOKENS = [
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
    "gross_exposure_cap = 2",
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
    module_source = read_text(MODULE)
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("strategy improvement lab module is missing")

    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing bot.py command registration/routing: {command}")

    verify_pre_config_routing(bot_source, failures)
    verify_module_static_contract(module_source, failures)
    verify_display_saved_csv_only(module_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Strategy improvement lab verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Strategy improvement lab verification passed.")
    print("Verified fixed research-only variants, saved display path, false approval flags, and ignored generated outputs.")
    return 0


def verify_pre_config_routing(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command, branch in [
        ("--strategy-improvement-lab", "if args.strategy_improvement_lab:"),
        ("--show-strategy-improvement-lab", "if args.show_strategy_improvement_lab:"),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing pre-config branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module_static_contract(module_source: str, failures: list[str]) -> None:
    required_tokens = [
        "research_only",
        "preview_only",
        '"execution_approved": False',
        '"paper_execution_approved": False',
        "HISTORY_PERIOD = \"10y\"",
        "DAILY_INTERVAL = \"1d\"",
        "MOMENTUM_LOOKBACK_DAYS = 126",
        "TREND_WINDOW_DAYS = 200",
        "STRONG_BREADTH_THRESHOLD = 0.60",
        "MIXED_BREADTH_THRESHOLD = 0.40",
        "WEAK_BREADTH_THRESHOLD = 0.30",
        "VOLATILITY_WINDOW_DAYS = 20",
        "VOLATILITY_MEDIAN_WINDOW_DAYS = 252",
    ]
    for token in required_tokens:
        if token not in module_source:
            failures.append(f"missing required research-only/fixed-parameter token: {token}")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing generated output path: {output}")
    for variant in FIXED_VARIANTS:
        if variant not in module_source:
            failures.append(f"missing fixed strategy variant: {variant}")
    for label in DECISION_LABELS:
        if label not in module_source:
            failures.append(f"missing decision label: {label}")
    for token in FORBIDDEN_MODULE_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/scheduling/config token in module: {token}")
    for token in BROAD_SEARCH_TOKENS:
        if token in module_source:
            failures.append(f"forbidden broad-search/ML token in module: {token}")


def verify_display_saved_csv_only(module_source: str, failures: list[str]) -> None:
    start = module_source.find("def show_strategy_improvement_lab_file")
    if start == -1:
        failures.append("display function is missing")
        return
    display_source = module_source[start:]
    for token in ["yf.download", "download_daily_price_data", "run_strategy_improvement_lab_files", "configure_yfinance_cache_location"]:
        if token in display_source:
            failures.append(f"display path must not refresh market data: {token}")
    if "csv.DictReader" not in display_source:
        failures.append("display path should read saved CSV rows")
    if "Run `python bot.py --strategy-improvement-lab` first." not in display_source:
        failures.append("display path should print helpful missing-file guidance")


def verify_outputs_ignored(gitignore: str, failures: list[str]) -> None:
    if "data/*" not in gitignore:
        failures.append("generated data outputs must remain ignored by git")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
