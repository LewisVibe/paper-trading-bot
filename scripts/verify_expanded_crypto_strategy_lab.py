from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "expanded_crypto_strategy_lab.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--expanded-crypto-strategy-lab",
    "--show-expanded-crypto-strategy-lab",
]

OUTPUTS = [
    "data/expanded_crypto_strategy_lab.csv",
    "data/expanded_crypto_strategy_lab_summary.csv",
    "data/expanded_crypto_strategy_lab_trades.csv",
    "data/expanded_crypto_strategy_lab_equity_curves.csv",
    "data/expanded_crypto_strategy_lab_costs.csv",
    "data/expanded_crypto_strategy_lab_splits.csv",
]

REQUIRED_TOKENS = [
    "crypto_risk_on_momentum_persistence",
    "codex_ambitious_crypto_",
    "codex_ambitious_crypto_btc_eth_core_alt_accelerator",
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "ATOM-USD",
    "POL-USD",
    "MATIC-USD",
    "TRANSITION_BLOCKED_SYMBOLS",
    "expanded_crypto_strategy_promising",
    "expanded_crypto_strategy_high_return_high_risk",
    "expanded_crypto_strategy_cost_sensitive",
    "expanded_crypto_strategy_split_sensitive",
    "expanded_crypto_strategy_drawdown_extreme_review",
    "expanded_crypto_strategy_not_useful",
    "codex_crypto_candidate_promising",
    "codex_crypto_candidate_cost_sensitive",
    "codex_crypto_candidate_not_useful",
    "insufficient_saved_inputs",
    "manual_review_required",
    '"execution_approved": False',
    '"research_only": True',
    '"preview_only": True',
    "does not approve crypto execution",
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
    "enable_margin",
    "sched.scheduler",
    "Task Scheduler",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, HERMES_TASK_BOARD])
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("expanded crypto strategy lab module is missing")

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Expanded crypto strategy lab verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Expanded crypto strategy lab verification passed.")
    print("Verified expanded crypto strategies, transition blocking, false execution approval, and ignored outputs.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--expanded-crypto-strategy-lab", "if args.expanded_crypto_strategy_lab:"),
        ("--show-expanded-crypto-strategy-lab", "if args.show_expanded_crypto_strategy_lab:"),
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
            failures.append(f"missing expanded crypto lab token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config token in expanded crypto lab module: {token}")

    display_start = module_source.find("def show_expanded_crypto_strategy_lab_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_expanded_crypto_strategy_lab" in display_source:
            failures.append("display command must not regenerate lab data")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    if "does not approve crypto execution" not in docs_source:
        failures.append("docs must state crypto execution is not approved")


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
