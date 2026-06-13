from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "expanded_crypto_manual_review_pack.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--expanded-crypto-manual-review-pack",
    "--show-expanded-crypto-manual-review-pack",
]

OUTPUTS = [
    "data/expanded_crypto_manual_review_pack.csv",
    "data/expanded_crypto_manual_review_summary.csv",
    "data/expanded_crypto_manual_review_evidence.csv",
    "data/expanded_crypto_manual_review_blockers.csv",
]

INPUTS = [
    "data/crypto_universe_readiness_summary.csv",
    "data/expanded_crypto_strategy_lab_summary.csv",
    "data/expanded_crypto_robustness_summary.csv",
    "data/expanded_crypto_equal_weight_reality_check.csv",
    "data/crypto_equal_weight_crash_gate_summary.csv",
    "data/crypto_equal_weight_volatility_scaling_summary.csv",
    "data/crypto_equal_weight_capped_risk_summary.csv",
    "data/crypto_equal_weight_capped_risk_contributions.csv",
    "data/expanded_crypto_lead_decision_summary.csv",
    "data/expanded_crypto_lead_decision_evidence.csv",
    "data/crypto_lead_split_sensitivity_summary.csv",
    "data/crypto_lead_split_sensitivity_diagnosis.csv",
    "data/crypto_lead_split_sensitivity_exclusions.csv",
    "data/crypto_lead_split_sensitivity_contributions.csv",
]

REQUIRED_TOKENS = [
    "crypto_equal_weight_ex_highest_vol_2",
    "equal_weight_eligible_crypto_benchmark",
    "equal_weight_inception_aware",
    "equal_weight_crypto_robust_benchmark",
    "split sensitivity",
    "exclusion",
    "outlier",
    "top-contributor",
    "hard crash gates rejected due return drag",
    "volatility/drawdown throttles downgraded",
    "crypto_manual_review_lead_confirmed_manual_only",
    "crypto_manual_review_split_sensitive",
    "crypto_manual_review_outlier_dependent",
    "crypto_manual_review_exclusion_rule_unstable",
    "crypto_manual_review_cost_review_required",
    "crypto_manual_review_not_ready_for_preview_discussion",
    "crypto_manual_review_blocked_missing_inputs",
    "manual_review_required",
    '"research_only": True',
    '"preview_only": True',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"promotion_approved": False',
    '"scheduling_approved": False',
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
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("expanded crypto manual review pack module is missing")
    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Expanded crypto manual review pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Expanded crypto manual review pack verification passed.")
    print("Verified saved-output manual review pack, false approval flags, non-execution wording, and ignored outputs.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--expanded-crypto-manual-review-pack", "if args.expanded_crypto_manual_review_pack:"),
        ("--show-expanded-crypto-manual-review-pack", "if args.show_expanded_crypto_manual_review_pack:"),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing pre-config branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    for path in OUTPUTS + INPUTS:
        if path not in module_source:
            failures.append(f"missing expected path in module: {path}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing manual-review token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in module: {token}")
    display_start = module_source.find("def show_expanded_crypto_manual_review_pack_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_expanded_crypto_manual_review_pack" in display_source:
            failures.append("display command must not regenerate the manual review pack")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "research/report-only",
        "manual review pack for the current crypto research lead",
        "does not approve crypto execution",
        "does not approve preview promotion",
        "does not connect crypto to Alpaca or paper orders",
        "manual-review-only",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


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
