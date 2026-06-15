from __future__ import annotations

import ast
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "qqq100_paper_readiness_blocker_report.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"

COMMANDS = ["--qqq100-paper-readiness-blocker-report", "--show-qqq100-paper-readiness-blocker-report"]
OUTPUTS = [
    "data/qqq100_paper_readiness_blocker_report.csv",
    "data/qqq100_paper_readiness_blocker_summary.csv",
    "data/qqq100_paper_readiness_blocker_evidence.csv",
    "data/qqq100_paper_readiness_blocker_blockers.csv",
]

REQUIRED_TOKENS = [
    "qqq100_paper_readiness_blocked",
    "qqq100_preview_chain_ready",
    "smoke_test_required_first",
    "execution_design_not_added",
    "sizing_not_approved",
    "kill_switch_review_required",
    "portfolio_risk_review_required",
    "manual_confirmation_required",
    "postcheck_required",
    "scheduling_not_approved",
    "execution_blocked",
    "high_growth_branch_excluded",
    "qqq_100_trend_gate",
    "QQQ",
    '"research_only": True',
    '"preview_only": True',
    '"action_preview_only": True',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
    '"sqlite_trade_log_written": False',
    '"discord_alert_sent": False',
    '"telegram_alert_sent": False',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
]

FORBIDDEN_MODULE_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "OrderSide",
    "TimeInForce",
    "submit_order",
    "cancel_order",
    "replace_order",
    "create_order",
    "get_all_positions",
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
    "yf.",
    "import yfinance",
    "download(",
]

FORBIDDEN_COLUMNS = {
    "order_quantity",
    "order_side",
    "order_type",
    "account_id",
    "api_key",
    "secret_key",
    "webhook",
    "token",
    "execution_instruction",
}


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
        print("QQQ100 paper-readiness blocker report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 paper-readiness blocker report verification passed.")
    print("Verified saved-output-only blocker report, QQQ100-only strategy scope, ignored outputs, blocked execution, and no order-instruction schema.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--qqq100-paper-readiness-blocker-report", 'if sys.argv[1:] == ["--qqq100-paper-readiness-blocker-report"]:'),
        ("--show-qqq100-paper-readiness-blocker-report", 'if sys.argv[1:] == ["--show-qqq100-paper-readiness-blocker-report"]:'),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early safe branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before normal config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("QQQ100 paper-readiness blocker report module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required blocker-report token: {token}")
    for token in FORBIDDEN_MODULE_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/refresh/config/scheduling token in module: {token}")
    if "read_csv_rows" not in module_source or "INPUT_FILES" not in module_source:
        failures.append("blocker report must read saved CSV outputs only")
    if "data/qqq100_action_preview.csv" not in module_source:
        failures.append("blocker report must read saved QQQ100 action preview output")
    verify_columns(module_source, failures)
    display_start = module_source.find("def show_qqq100_paper_readiness_blocker_report")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_qqq100_paper_readiness_blocker_report" in display_source:
            failures.append("display command must not regenerate the blocker report")


def verify_columns(module_source: str, failures: list[str]) -> None:
    try:
        tree = ast.parse(module_source)
    except SyntaxError as exc:
        failures.append(f"module does not parse: {exc}")
        return
    for constant_name in ["REPORT_COLUMNS", "SUMMARY_COLUMNS", "EVIDENCE_COLUMNS", "BLOCKER_COLUMNS"]:
        columns = extract_list_constant(tree, constant_name, failures)
        if not columns:
            continue
        required = {
            "research_only",
            "preview_only",
            "action_preview_only",
            "orders_created",
            "orders_submitted",
            "orders_cancelled",
            "sqlite_trade_log_written",
            "discord_alert_sent",
            "telegram_alert_sent",
            "execution_approved",
            "paper_execution_approved",
            "scheduling_approved",
        }
        missing = sorted(required - set(columns))
        if missing:
            failures.append(f"{constant_name} missing required safety columns: {', '.join(missing)}")
        forbidden = sorted(FORBIDDEN_COLUMNS & set(columns))
        if forbidden:
            failures.append(f"{constant_name} has forbidden sensitive/order columns: {', '.join(forbidden)}")
    report_columns = extract_list_constant(tree, "REPORT_COLUMNS", failures)
    if report_columns:
        for required in ["strategy_name", "ticker", "check_name", "status", "risk_label", "blocker", "required_next_step"]:
            if required not in report_columns:
                failures.append(f"REPORT_COLUMNS missing {required}")


def extract_list_constant(tree: ast.Module, name: str, failures: list[str]) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return list(ast.literal_eval(node.value))
                    except Exception as exc:
                        failures.append(f"could not inspect {name}: {exc}")
                        return []
    failures.append(f"{name} not found")
    return []


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in ["QQQ100 paper-readiness blocker report", "saved-output", "does not approve execution"]:
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
