from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "qqq_preview_candidate_readiness.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"
GITIGNORE = ROOT / ".gitignore"

COMMANDS = [
    "--qqq-preview-candidate-readiness-report",
    "--show-qqq-preview-candidate-readiness-report",
]

OUTPUTS = [
    "data/qqq_preview_candidate_readiness_report.csv",
    "data/qqq_preview_candidate_readiness_summary.csv",
    "data/qqq_preview_candidate_readiness_evidence.csv",
    "data/qqq_preview_candidate_readiness_blockers.csv",
]

INPUTS = [
    "data/qqq_trend_gate_manual_review_pack.csv",
    "data/qqq_trend_gate_manual_review_summary.csv",
    "data/qqq_trend_gate_manual_review_evidence.csv",
    "data/qqq_trend_gate_manual_review_blockers.csv",
    "data/qqq_lead_decision_report.csv",
    "data/qqq_lead_decision_summary.csv",
    "data/qqq_lead_decision_evidence.csv",
    "data/qqq_leverage_validation_report.csv",
    "data/qqq_leverage_validation_splits.csv",
    "data/qqq_leverage_validation_costs.csv",
    "data/qqq_leverage_validation_drawdowns.csv",
    "data/project_research_state_summary.csv",
    "data/project_research_state_next_steps.csv",
    "data/stock_etf_paper_execution_readiness_report.csv",
    "data/paper_order_smoke_test_readiness_pack.csv",
]

REQUIRED_TOKENS = [
    "qqq_100_trend_gate",
    "qqq_100_trend_gate_new_research_lead",
    "qqq_trend_gate_research_lead_confirmed_not_execution_ready",
    "qqq_preview_candidate_ready_for_manual_discussion",
    "qqq_preview_candidate_needs_cost_review",
    "qqq_preview_candidate_needs_drawdown_review",
    "qqq_preview_candidate_blocked_missing_inputs",
    "qqq_preview_candidate_not_ready",
    "codex_qqq_adaptive_trend_exposure",
    "qqq_150_trend_gate",
    "codex_ambitious_concentrated_growth_persistence",
    "Monday paper smoke test remains connectivity/order-path only",
    '"paper_execution_approved": False',
    '"execution_approved": False',
    '"leverage_execution_approved": False',
    '"margin_approved": False',
    '"scheduling_approved": False',
    '"alpaca_called": False',
    '"orders_created": False',
]

FORBIDDEN_TOKENS = [
    "import yfinance",
    "yf.download",
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
    gitignore = read_text(GITIGNORE)

    if not MODULE.exists():
        failures.append("QQQ preview-candidate readiness module is missing")
    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(gitignore, failures)

    if failures:
        print("QQQ preview-candidate readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ preview-candidate readiness verification passed.")
    print("Verified saved-output preview readiness report, false paper/execution flags, non-execution wording, and ignored outputs.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--qqq-preview-candidate-readiness-report", 'if sys.argv[1:] == ["--qqq-preview-candidate-readiness-report"]:'),
        ("--show-qqq-preview-candidate-readiness-report", 'if sys.argv[1:] == ["--show-qqq-preview-candidate-readiness-report"]:'),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early safe branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    for path in OUTPUTS + INPUTS:
        if path not in module_source:
            failures.append(f"missing expected path in module: {path}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing preview-readiness token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in module: {token}")
    display_start = module_source.find("def show_qqq_preview_candidate_readiness_report")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_qqq_preview_candidate_readiness_report" in display_source:
            failures.append("display command must not regenerate the readiness report")
        if "read_csv" not in display_source:
            failures.append("display command should read saved CSVs")
        for forbidden in ["python bot.py --paper-order-test", "--execute-slow-sma-paper", "--confirm-readonly-alpaca-check"]:
            if forbidden in display_source:
                failures.append(f"terminal display must not print execution-capable command: {forbidden}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in [
        "QQQ preview-candidate readiness report",
        "research/report-only",
        "manual discussion only",
        "does not approve paper execution",
        "does not approve execution",
        "does not connect strategies to Alpaca or paper orders",
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
