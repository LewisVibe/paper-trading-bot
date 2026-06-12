from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "crypto_equal_weight_volatility_scaling.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--crypto-equal-weight-volatility-scaling",
    "--show-crypto-equal-weight-volatility-scaling",
]

OUTPUTS = [
    "data/crypto_equal_weight_volatility_scaling.csv",
    "data/crypto_equal_weight_volatility_scaling_summary.csv",
    "data/crypto_equal_weight_volatility_scaling_trades.csv",
    "data/crypto_equal_weight_volatility_scaling_equity_curves.csv",
    "data/crypto_equal_weight_volatility_scaling_costs.csv",
    "data/crypto_equal_weight_volatility_scaling_splits.csv",
    "data/crypto_equal_weight_volatility_scaling_drawdowns.csv",
]

REQUIRED_TOKENS = [
    "equal_weight_eligible_crypto_benchmark",
    "equal_weight_inception_aware",
    "crypto_equal_weight_volatility_scaled_allocator",
    "crypto_equal_weight_drawdown_scaled_allocator",
    "crypto_equal_weight_combined_vol_drawdown_scaler",
    "codex_ambitious_crypto_core_alt_volatility_throttle",
    "codex_ambitious_crypto_",
    "crypto_risk_on_momentum_persistence",
    "codex_ambitious_crypto_btc_eth_core_alt_accelerator",
    "btc_buy_and_hold_benchmark",
    "eth_buy_and_hold_benchmark",
    "btc_eth_50_50_monthly_rebalanced_benchmark",
    "cash_benchmark",
    "POL-USD",
    "MATIC-USD",
    "TRANSITION_BLOCKED",
    "crypto_vol_scaler_promising",
    "crypto_vol_scaler_drawdown_improved",
    "crypto_vol_scaler_return_drag_too_high",
    "crypto_vol_scaler_cost_sensitive",
    "crypto_vol_scaler_split_sensitive",
    "crypto_vol_scaler_new_defensive_crypto_candidate",
    "crypto_vol_scaler_not_useful",
    "equal_weight_still_best_high_drawdown",
    "codex_crypto_risk_control_promising",
    "codex_crypto_risk_control_not_useful",
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
        failures.append("crypto equal-weight volatility-scaling module is missing")
    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Crypto equal-weight volatility-scaling verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto equal-weight volatility-scaling verification passed.")
    print("Verified fixed partial-exposure scalers, Codex risk-control idea, false execution approval, transition blocking, and ignored outputs.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--crypto-equal-weight-volatility-scaling", "if args.crypto_equal_weight_volatility_scaling:"),
        ("--show-crypto-equal-weight-volatility-scaling", "if args.show_crypto_equal_weight_volatility_scaling:"),
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
            failures.append(f"missing volatility-scaling token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config token in volatility-scaling module: {token}")
    display_start = module_source.find("def show_crypto_equal_weight_volatility_scaling_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_crypto_equal_weight_volatility_scaling" in display_source:
            failures.append("display command must not regenerate crypto volatility-scaling data")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")
    if "configure_yfinance_cache_location" not in module_source:
        failures.append("report should configure a local yfinance cache before fetching")
    if "return {}" in module_source and "fully cash" in module_source.lower():
        failures.append("volatility-scaling strategies should avoid full-cash crash-gate behaviour")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    if "partial volatility/drawdown exposure scaling" not in docs_source:
        failures.append("docs must mention partial volatility/drawdown exposure scaling")
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
