from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "crypto_lead_split_sensitivity_diagnosis.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--crypto-lead-split-sensitivity-diagnosis",
    "--show-crypto-lead-split-sensitivity-diagnosis",
]

OUTPUTS = [
    "data/crypto_lead_split_sensitivity_diagnosis.csv",
    "data/crypto_lead_split_sensitivity_summary.csv",
    "data/crypto_lead_split_sensitivity_periods.csv",
    "data/crypto_lead_split_sensitivity_exclusions.csv",
    "data/crypto_lead_split_sensitivity_contributions.csv",
]

REQUIRED_TOKENS = [
    "crypto_equal_weight_ex_highest_vol_2",
    "split_60_40",
    "split_70_30",
    "split_80_20",
    "crypto_lead_split_sensitivity_explained",
    "crypto_lead_split_sensitive_but_still_lead",
    "crypto_lead_outlier_dependent_review",
    "crypto_lead_exclusion_rule_unstable",
    "crypto_lead_late_period_decay",
    "crypto_lead_broad_market_decay",
    "crypto_lead_not_stable_enough",
    "insufficient_saved_inputs",
    "manual_review_required",
    "BNB-USD",
    "TRX-USD",
    "top_contributor",
    "outlier",
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
        failures.append("crypto lead split-sensitivity diagnosis module is missing")
    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("Crypto lead split-sensitivity diagnosis verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto lead split-sensitivity diagnosis verification passed.")
    print("Verified saved-output split diagnosis, outlier/exclusion checks, false execution approval, and ignored outputs.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--crypto-lead-split-sensitivity-diagnosis", "if args.crypto_lead_split_sensitivity_diagnosis:"),
        ("--show-crypto-lead-split-sensitivity-diagnosis", "if args.show_crypto_lead_split_sensitivity_diagnosis:"),
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
            failures.append(f"missing diagnosis token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config token in diagnosis module: {token}")
    display_start = module_source.find("def show_crypto_lead_split_sensitivity_diagnosis_file")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_crypto_lead_split_sensitivity_diagnosis" in display_source:
            failures.append("display command must not regenerate diagnosis data")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    if "split-sensitivity diagnosis for the current crypto research lead" not in docs_source:
        failures.append("docs must describe the split-sensitivity diagnosis purpose")
    if "research/report-only" not in docs_source:
        failures.append("docs must state this is research/report-only")
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
