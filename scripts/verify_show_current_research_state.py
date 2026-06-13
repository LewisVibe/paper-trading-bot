from __future__ import annotations

import inspect
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "current_research_state.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"

COMMAND = "--show-current-research-state"

EXPECTED_INPUTS = [
    "data/project_research_state_summary.csv",
    "data/project_research_state_refresh.csv",
    "data/project_research_state_next_steps.csv",
    "data/codex_ambitious_lead_decision_summary.csv",
    "data/expanded_crypto_manual_review_summary.csv",
    "data/expanded_crypto_lead_decision_summary.csv",
]

REQUIRED_TOKENS = [
    "codex_ambitious_concentrated_growth_persistence",
    "crypto_equal_weight_ex_highest_vol_2",
    "execution_approved",
    "scheduling_approved",
    "display-only",
    "project-research-state-refresh",
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

    if COMMAND not in bot_source:
        failures.append(f"missing command registration/routing: {COMMAND}")
    branch_index = bot_source.find("if args.show_current_research_state:")
    load_config_index = bot_source.find("config = load_config(")
    if branch_index == -1:
        failures.append("missing pre-config branch for show_current_research_state")
    elif load_config_index != -1 and branch_index > load_config_index:
        failures.append("show-current-research-state must route before config loading")
    if not MODULE.exists():
        failures.append("current research state display module is missing")
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)

    if failures:
        print("Show current research state verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Show current research state verification passed.")
    print("Verified concise saved-state display command, false approval wording, and non-execution source.")
    return 0


def verify_module(module_source: str, failures: list[str]) -> None:
    for path in EXPECTED_INPUTS:
        if path not in module_source:
            failures.append(f"missing expected saved input reference: {path}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing display token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in display module: {token}")
    if "write" in module_source:
        failures.append("display module should not write files")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for phrase in [
        COMMAND,
        "concise terminal display helper",
        "reads saved project research state",
        "does not refresh market data",
        "does not approve preview promotion",
        "does not approve execution",
        "does not connect strategies to Alpaca or paper orders",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
