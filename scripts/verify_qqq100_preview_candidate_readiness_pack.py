from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "qqq100_preview_candidate_readiness_pack.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"

COMMANDS = ["--qqq100-preview-candidate-readiness-pack", "--show-qqq100-preview-candidate-readiness-pack"]
OUTPUTS = [
    "data/qqq100_preview_candidate_readiness_pack.csv",
    "data/qqq100_preview_candidate_readiness_summary.csv",
    "data/qqq100_preview_candidate_readiness_evidence.csv",
    "data/qqq100_preview_candidate_readiness_blockers.csv",
]

REQUIRED_TOKENS = [
    "qqq100_preview_discussion_ready",
    "qqq100_preview_discussion_needs_more_review",
    "qqq100_clean_lead_retained",
    "qqq150_high_drawdown_reference_rejected",
    "adaptive_qqq_ambitious_alternative_only",
    "high_growth_branch_not_ready_for_preview",
    "preview_implementation_not_added",
    "execution_blocked",
    "qqq_100_trend_gate",
    "qqq_100_trend_gate_new_research_lead",
    "codex_qqq_adaptive_trend_exposure",
    "qqq_150_trend_gate",
    '"research_only": True',
    '"preview_only": True',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
]

FORBIDDEN_TOKENS = [
    "download_daily_price_data",
    "yf.",
    "import yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "replace_order",
    "create_order",
    "get_alpaca_positions",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "load_config(",
    "config.json",
    "sched.scheduler",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, V2_CHECKPOINT, HERMES_TASK_BOARD])

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(failures)

    if failures:
        print("QQQ100 preview-candidate readiness pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 preview-candidate readiness pack verification passed.")
    print("Verified saved-output-only QQQ100 readiness pack, clean lead retention, rejected QQQ150 reference, adaptive alternative boundary, ignored outputs, and blocked preview implementation/execution.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--qqq100-preview-candidate-readiness-pack", 'if sys.argv[1:] == ["--qqq100-preview-candidate-readiness-pack"]:'),
        ("--show-qqq100-preview-candidate-readiness-pack", 'if sys.argv[1:] == ["--show-qqq100-preview-candidate-readiness-pack"]:'),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early safe branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("QQQ100 readiness pack module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required QQQ100 readiness token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/refresh/config/scheduling token in module: {token}")
    if "read_csv_rows" not in module_source:
        failures.append("QQQ100 readiness pack should read saved CSV outputs only")
    display_start = module_source.find("def show_qqq100_preview_candidate_readiness_pack")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_qqq100_preview_candidate_readiness_pack" in display_source:
            failures.append("display command must not regenerate the readiness pack")
    for phrase in ["preview implementation is not added", "Paper/live execution remains blocked", "High-growth branch is not promoted"]:
        if phrase not in module_source:
            failures.append(f"missing safety phrase: {phrase}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in ["QQQ100 preview-candidate readiness pack", "saved-output", "research-only", "does not approve execution"]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(["git", "check-ignore", output], cwd=ROOT, check=False, capture_output=True, text=True, timeout=10)
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
