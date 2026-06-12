from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "codex_ambitious_split_drawdown_validation.py"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--codex-ambitious-split-drawdown-validation",
    "--show-codex-ambitious-split-drawdown-validation",
]

OUTPUTS = [
    "data/codex_ambitious_split_drawdown_validation.csv",
    "data/codex_ambitious_split_validation.csv",
    "data/codex_ambitious_drawdown_windows.csv",
    "data/codex_ambitious_lead_change_checkpoint.csv",
]

REQUIRED_TOKENS = [
    'TARGET_STRATEGY = CODEX_AMBITIOUS_STRATEGY',
    "codex_ambitious_concentrated_growth_persistence",
    "split_60_40",
    "split_70_30",
    "split_80_20",
    "codex_ambitious_new_active_research_lead",
    "codex_ambitious_active_lead_candidate_needs_cost_review",
    "codex_ambitious_split_sensitive",
    "codex_ambitious_drawdown_concentrated_review",
    "codex_ambitious_not_ready_for_lead_change",
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
        failures.append("Codex ambitious split/drawdown validation module is missing")

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(gitignore, failures)
    verify_drawdown_contract(failures)

    if failures:
        print("Codex ambitious split/drawdown validation verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Codex ambitious split/drawdown validation verification passed.")
    print("Verified split/drawdown report, false approval flags, and display-only command.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        (
            "--codex-ambitious-split-drawdown-validation",
            "if args.codex_ambitious_split_drawdown_validation:",
        ),
        (
            "--show-codex-ambitious-split-drawdown-validation",
            "if args.show_codex_ambitious_split_drawdown_validation:",
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
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required split/drawdown token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in split/drawdown module: {token}")

    display_start = module_source.find("def show_codex_ambitious_split_drawdown_validation_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_codex_ambitious_split_drawdown_validation" in display_source:
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


def verify_drawdown_contract(failures: list[str]) -> None:
    sys.path.insert(0, str(ROOT))
    from trading_bot.research.codex_ambitious_split_drawdown_validation import (
        window_drawdown,
        worst_drawdown_window,
    )

    rows = [
        {"date": "2020-01-01", "equity": 100.0},
        {"date": "2020-03-23", "equity": 50.0},
        {"date": "2020-12-17", "equity": 100.0},
        {"date": "2025-10-29", "equity": 120.0},
    ]
    window = worst_drawdown_window(rows)
    if window["start_date"] > window["trough_date"]:
        failures.append("drawdown start date must not be after trough date")
    if window["recovery_date"] and window["recovery_date"] < window["trough_date"]:
        failures.append("drawdown recovery date must not be before trough date")
    if window["recovery_rows"] != "" and int(window["recovery_rows"]) < 0:
        failures.append("drawdown recovery rows must not be negative")
    if window["start_date"] != "2020-01-01":
        failures.append("drawdown start must be the prior equity peak before the trough")
    if window["trough_date"] != "2020-03-23":
        failures.append("drawdown trough must match the max drawdown row")
    if round(float(window["max_drawdown_pct"]), 4) != -50.0:
        failures.append("max drawdown must correspond to the selected trough")

    missing_overlap = window_drawdown([{"date": "2020-01-01", "equity": 100.0}], "2020-01-01", "2020-03-23")
    if missing_overlap is not None:
        failures.append("missing overlap data must be unavailable, not 0.0")
    overlap = window_drawdown(rows, "2020-01-01", "2020-12-17")
    if overlap is None or round(overlap, 4) != -50.0:
        failures.append("overlap drawdown must use chronological peak-to-trough logic")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
