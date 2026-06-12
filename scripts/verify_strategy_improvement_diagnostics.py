from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "strategy_improvement_diagnostics.py"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--strategy-improvement-diagnostics",
    "--show-strategy-improvement-diagnostics",
]

OUTPUTS = [
    "data/strategy_improvement_diagnostics.csv",
    "data/growth_biased_rotation_diagnostics.csv",
]

SAVED_INPUTS = [
    "data/strategy_improvement_lab_results.csv",
    "data/strategy_improvement_lab_trades.csv",
    "data/strategy_improvement_lab_equity_curve.csv",
    "data/strategy_improvement_lab_summary.csv",
    "data/strategy_improvement_robustness_report.csv",
    "data/strategy_improvement_cost_stress_report.csv",
    "data/strategy_improvement_drawdown_report.csv",
    "data/strategy_improvement_candidate_comparison.csv",
]

DIAGNOSTIC_TOPICS = [
    "split_sensitivity",
    "benchmark_relative",
    "cost_sensitivity",
    "drawdown_behavior",
    "cash_drag",
    "candidate_status",
    "next_fixed_hypothesis",
    "cost_refinement",
    "defensive_sleeve_refinement",
    "remaining_refinement_batch",
    "split_stability_check",
]

NEXT_HYPOTHESES = [
    "growth_biased_rotation_breadth_stricter_split_validation",
    "growth_biased_rotation_breadth_stricter_cost_stress_review",
    "growth_biased_rotation_breadth_stricter_drawdown_period_review",
    "growth_biased_rotation_breadth_stricter_promotion_checkpoint",
]

TESTED_REJECTED_REFINEMENTS = [
    "growth_biased_rotation_cost_aware_rebalance",
    "growth_biased_rotation_partial_defensive_sleeve",
    "growth_biased_rotation_reentry_filter",
    "growth_biased_rotation_regime_recovery_filter",
    "growth_biased_rotation_breadth_threshold_review",
]

COST_REFINEMENT_STATUSES = [
    "cost_refinement_improved",
    "cost_refinement_return_drag",
    "cost_refinement_no_material_change",
    "cost_refinement_promising",
    "cost_refinement_not_useful",
]

DEFENSIVE_SLEEVE_STATUSES = [
    "defensive_sleeve_improved_stability",
    "defensive_sleeve_return_drag",
    "defensive_sleeve_no_material_improvement",
    "defensive_sleeve_promising",
    "defensive_sleeve_not_useful",
]

REMAINING_REFINEMENT_STATUSES = [
    "reentry_filter_improved",
    "reentry_filter_return_drag",
    "reentry_filter_no_material_improvement",
    "recovery_filter_improved",
    "recovery_filter_return_drag",
    "recovery_filter_no_material_improvement",
    "breadth_threshold_improved",
    "breadth_threshold_return_drag",
    "breadth_threshold_no_material_improvement",
    "new_active_research_lead",
    "split_stability_improved",
    "split_stability_no_material_improvement",
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
    "run_strategy_improvement_lab_files",
    "generate_strategy_improvement_robustness(",
    "allow_shorting = True",
    "leverage",
    "margin",
    "sched.scheduler",
    "Task Scheduler",
    "cron",
]

NEW_STRATEGY_IMPLEMENTATION_TOKENS = [
    "def factor_",
    "def sector_",
    "def adaptive_",
    "target_weights_for_strategy",
    "simulate_strategy",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("strategy improvement diagnostics module is missing")

    verify_commands(bot_source, failures)
    verify_module_contract(module_source, failures)
    verify_outputs_ignored(gitignore, failures)
    verify_display_saved_csv_only(module_source, failures)

    if failures:
        print("Strategy improvement diagnostics verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Strategy improvement diagnostics verification passed.")
    print("Verified saved-CSV diagnostics, false approval flags, and suggestion-only next hypotheses.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--strategy-improvement-diagnostics", "if args.strategy_improvement_diagnostics:"),
        ("--show-strategy-improvement-diagnostics", "if args.show_strategy_improvement_diagnostics:"),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing pre-config branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module_contract(module_source: str, failures: list[str]) -> None:
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected diagnostics output path: {output}")
    for saved_input in SAVED_INPUTS:
        if saved_input not in module_source:
            failures.append(f"missing saved input reference: {saved_input}")
    for topic in DIAGNOSTIC_TOPICS:
        if topic not in module_source:
            failures.append(f"missing diagnostic topic: {topic}")
    for hypothesis in NEXT_HYPOTHESES:
        if hypothesis not in module_source:
            failures.append(f"missing suggestion-only next hypothesis: {hypothesis}")
    start = module_source.find("hypotheses = [")
    end = module_source.find("return [", start)
    next_hypothesis_source = module_source[start:end] if start != -1 and end != -1 else module_source
    for rejected in TESTED_REJECTED_REFINEMENTS:
        if rejected in next_hypothesis_source:
            failures.append(f"tested rejected refinement should not remain a next hypothesis: {rejected}")
    for status in COST_REFINEMENT_STATUSES:
        if status not in module_source:
            failures.append(f"missing cost refinement diagnostic status: {status}")
    for status in DEFENSIVE_SLEEVE_STATUSES:
        if status not in module_source:
            failures.append(f"missing defensive sleeve diagnostic status: {status}")
    for status in REMAINING_REFINEMENT_STATUSES:
        if status not in module_source:
            failures.append(f"missing remaining refinement diagnostic status: {status}")
    for strategy_name in [
        "growth_biased_rotation_crash_gate",
        "growth_biased_rotation_cost_aware_rebalance",
        "growth_biased_rotation_partial_defensive_sleeve",
        "growth_biased_rotation_reentry_filter",
        "growth_biased_rotation_regime_recovery_filter",
        "growth_biased_rotation_breadth_looser_gate",
        "growth_biased_rotation_breadth_stricter_gate",
        "growth_biased_rotation_split_stability_check",
        "ACTIVE_RESEARCH_LEAD = BREADTH_STRICTER_STRATEGY",
        "PREVIOUS_RESEARCH_LEAD = TARGET_STRATEGY",
    ]:
        if strategy_name not in module_source:
            failures.append(f"missing direct growth-biased comparison strategy: {strategy_name}")
    for token in [
        '"execution_approved": False',
        '"paper_execution_approved": False',
        '"research_only": True',
        '"preview_only": True',
        "performance_drag",
        "excessive_return_drag",
        "Sharpe delta",
        "partial_defensive_sleeve_decision",
        "new active research lead",
        "Previous growth-biased baseline",
        "suggestion_only",
        "This is a future fixed-hypothesis suggestion, not an implemented strategy.",
    ]:
        if token not in module_source:
            failures.append(f"missing research-only/suggestion safety token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/refresh/scheduling token in diagnostics module: {token}")
    for token in NEW_STRATEGY_IMPLEMENTATION_TOKENS:
        if token in module_source:
            failures.append(f"diagnostics must not implement new strategy logic: {token}")


def verify_outputs_ignored(gitignore: str, failures: list[str]) -> None:
    if "data/*" not in gitignore:
        failures.append("generated data outputs must remain ignored by git")


def verify_display_saved_csv_only(module_source: str, failures: list[str]) -> None:
    start = module_source.find("def show_strategy_improvement_diagnostics_file")
    if start == -1:
        failures.append("display function is missing")
        return
    display_source = module_source[start:]
    for token in ["generate_strategy_improvement_diagnostics", "read_csv(path)"]:
        if token in display_source and token == "generate_strategy_improvement_diagnostics":
            failures.append(f"display path must not regenerate diagnostics: {token}")
    if "read_csv(path)" not in display_source:
        failures.append("display path should read saved diagnostics CSV")
    if "Run `python bot.py --strategy-improvement-diagnostics` first." not in display_source:
        failures.append("display path should print helpful missing-file guidance")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
