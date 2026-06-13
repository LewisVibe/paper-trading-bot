from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "crypto_equal_weight_capped_risk_report.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--crypto-equal-weight-capped-risk-report",
    "--show-crypto-equal-weight-capped-risk-report",
]

OUTPUTS = [
    "data/crypto_equal_weight_capped_risk_report.csv",
    "data/crypto_equal_weight_capped_risk_summary.csv",
    "data/crypto_equal_weight_capped_risk_trades.csv",
    "data/crypto_equal_weight_capped_risk_equity_curves.csv",
    "data/crypto_equal_weight_capped_risk_costs.csv",
    "data/crypto_equal_weight_capped_risk_splits.csv",
    "data/crypto_equal_weight_capped_risk_drawdowns.csv",
    "data/crypto_equal_weight_capped_risk_contributions.csv",
]

REQUIRED_TOKENS = [
    "equal_weight_eligible_crypto_benchmark",
    "equal_weight_inception_aware",
    "crypto_equal_weight_cap_10pct",
    "crypto_equal_weight_cap_15pct",
    "crypto_equal_weight_ex_highest_vol_2",
    "crypto_equal_weight_ex_top_contributor_pair",
    "crypto_inverse_volatility_weighted",
    "crypto_equal_risk_contribution_proxy",
    "crypto_risk_on_momentum_persistence",
    "codex_ambitious_crypto_btc_eth_core_alt_accelerator",
    "btc_buy_and_hold_benchmark",
    "eth_buy_and_hold_benchmark",
    "btc_eth_50_50_monthly_rebalanced_benchmark",
    "cash_benchmark",
    "BNB-USD",
    "TRX-USD",
    "POL-USD",
    "MATIC-USD",
    "TRANSITION_BLOCKED",
    "contribution_diagnostics",
    "top_contributor",
    "Herfindahl",
    "outlier",
    "crypto_capped_risk_promising",
    "crypto_capped_risk_concentration_improved",
    "crypto_capped_risk_drawdown_improved",
    "crypto_capped_risk_return_drag_too_high",
    "crypto_capped_risk_cost_sensitive",
    "crypto_capped_risk_split_sensitive",
    "crypto_capped_risk_not_useful",
    "equal_weight_still_best_high_drawdown",
    "equal_weight_outlier_dependence_reduced",
    "insufficient_saved_inputs",
    "manual_review_required",
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
        failures.append("crypto equal-weight capped-risk module is missing")
    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Crypto equal-weight capped-risk verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto equal-weight capped-risk verification passed.")
    print("Verified capped/equal-risk variants, contribution diagnostics, false execution approval, transition blocking, and ignored outputs.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--crypto-equal-weight-capped-risk-report", "if args.crypto_equal_weight_capped_risk_report:"),
        ("--show-crypto-equal-weight-capped-risk-report", "if args.show_crypto_equal_weight_capped_risk_report:"),
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
            failures.append(f"missing capped-risk token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config token in capped-risk module: {token}")
    display_start = module_source.find("def show_crypto_equal_weight_capped_risk_report_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_crypto_equal_weight_capped_risk_report" in display_source:
            failures.append("display command must not regenerate capped-risk data")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")
    if "configure_yfinance_cache_location" not in module_source:
        failures.append("report should configure a local yfinance cache before fetching")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    if "capped/equal-risk crypto allocation" not in docs_source:
        failures.append("docs must mention capped/equal-risk crypto allocation")
    if "outlier-dependence diagnostics" not in docs_source:
        failures.append("docs must mention outlier-dependence diagnostics")
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
