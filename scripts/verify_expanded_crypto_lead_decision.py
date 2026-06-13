from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "expanded_crypto_lead_decision.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--expanded-crypto-lead-decision",
    "--show-expanded-crypto-lead-decision",
]

OUTPUTS = [
    "data/expanded_crypto_lead_decision.csv",
    "data/expanded_crypto_lead_decision_summary.csv",
    "data/expanded_crypto_lead_decision_evidence.csv",
]

REQUIRED_TOKENS = [
    "equal_weight_eligible_crypto_benchmark",
    "equal_weight_inception_aware",
    "crypto_equal_weight_ex_highest_vol_2",
    "crypto_risk_on_momentum_persistence",
    "codex_ambitious_crypto_btc_eth_core_alt_accelerator",
    "btc_buy_and_hold_benchmark",
    "eth_buy_and_hold_benchmark",
    "btc_eth_50_50_monthly_rebalanced_benchmark",
    "cash_benchmark",
    "crypto_equal_weight_ex_highest_vol_2_research_lead",
    "crypto_equal_weight_benchmark_lead_high_drawdown",
    "crypto_risk_on_momentum_persistence_lead_candidate",
    "codex_crypto_accelerator_lead_candidate",
    "crypto_research_lead_split_sensitive",
    "crypto_research_lead_outlier_dependent",
    "crypto_research_lead_cost_review_required",
    "crypto_research_not_ready_for_lead_decision",
    "insufficient_saved_inputs",
    "manual_review_required",
    "hard crash gates rejected for return drag",
    "defensive throttles",
    '"research_only": True',
    '"preview_only": True',
    '"execution_approved": False',
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
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, V2_CHECKPOINT, HERMES_TASK_BOARD])
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("expanded crypto lead decision module is missing")
    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Expanded crypto lead decision verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Expanded crypto lead decision verification passed.")
    print("Verified saved-output crypto lead labels, rejected-family evidence, false execution approval, and ignored outputs.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--expanded-crypto-lead-decision", "if args.expanded_crypto_lead_decision:"),
        ("--show-expanded-crypto-lead-decision", "if args.show_expanded_crypto_lead_decision:"),
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
            failures.append(f"missing lead-decision token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config token in lead-decision module: {token}")
    display_start = module_source.find("def show_expanded_crypto_lead_decision_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_expanded_crypto_lead_decision" in display_source:
            failures.append("display command must not regenerate lead-decision data")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    if "current crypto research lead as a research label only" not in docs_source:
        failures.append("docs must state this decides the current crypto research lead as a research label only")
    if "high-drawdown/manual-review-only" not in docs_source:
        failures.append("docs must state any crypto lead remains high-drawdown/manual-review-only")
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
