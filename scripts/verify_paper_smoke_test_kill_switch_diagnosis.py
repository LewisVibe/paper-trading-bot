from __future__ import annotations

import ast
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "paper_smoke_test_kill_switch_diagnosis.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"

COMMANDS = ["--paper-smoke-test-kill-switch-diagnosis", "--show-paper-smoke-test-kill-switch-diagnosis"]
OUTPUTS = [
    "data/paper_smoke_test_kill_switch_diagnosis.csv",
    "data/paper_smoke_test_kill_switch_diagnosis_summary.csv",
    "data/paper_smoke_test_kill_switch_diagnosis_blockers.csv",
    "data/paper_smoke_test_kill_switch_diagnosis_recommendations.csv",
]

REQUIRED_TOKENS = [
    "smoke_test_kill_switch_diagnosis_required",
    "live_preflight_passed_but_order_gate_blocked",
    "broad_execution_gate_blocks_smoke_test",
    "separate_manual_smoke_test_gate_review_required",
    "keep_order_blocked_until_reviewed",
    "no_order_submitted_confirmed",
    "paper_kill_switch_enabled_not_explicitly_true",
    "execution_eligibility_blocked",
    "defensive_allocation_decision_blocked",
    "promoted_strategy_disagreement",
    "portfolio_risk_policy_missing_or_blocked",
    "deployment_readiness_missing_or_blocked",
    "smoke_test_live_preflight_passed",
    "no_matching_order_found_after_blocked_attempt",
    "open_order_count_zero",
    "existing_aapl_position_context",
    "keep_smoke_test_blocked",
    "design_separate_manual_smoke_test_gate",
    "refresh_missing_saved_inputs_first",
    "do_not_retry_order_until_gate_reviewed",
    '"research_only": True',
    '"report_only": True',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"smoke_test_order_approved": False',
    '"scheduling_approved": False',
    '"orders_created": False',
    '"orders_submitted": False',
    '"orders_cancelled": False',
    '"sqlite_trade_log_written": False',
    '"discord_alert_sent": False',
    '"telegram_alert_sent": False',
    '"alpaca_called": False',
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


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, V2_CHECKPOINT, HERMES_TASK_BOARD])

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_docs(docs_source, failures)
    verify_outputs_ignored(failures)
    verify_order_gate_unchanged(bot_source, failures)

    if failures:
        print("Paper smoke-test kill-switch diagnosis verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Paper smoke-test kill-switch diagnosis verification passed.")
    print("Verified saved-output-only diagnosis, unchanged paper-order gate, ignored outputs, and blocked smoke-test execution.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--paper-smoke-test-kill-switch-diagnosis", 'if sys.argv[1:] == ["--paper-smoke-test-kill-switch-diagnosis"]:'),
        ("--show-paper-smoke-test-kill-switch-diagnosis", 'if sys.argv[1:] == ["--show-paper-smoke-test-kill-switch-diagnosis"]:'),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early safe branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before normal config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("diagnosis module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required diagnosis token: {token}")
    for token in FORBIDDEN_MODULE_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/refresh/config/scheduling token in module: {token}")
    if "read_csv_rows" not in module_source or "INPUT_FILES" not in module_source:
        failures.append("diagnosis report must read saved CSV outputs only")
    verify_columns(module_source, failures)
    display_start = module_source.find("def show_paper_smoke_test_kill_switch_diagnosis")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_paper_smoke_test_kill_switch_diagnosis" in display_source:
            failures.append("display command must not regenerate the diagnosis report")


def verify_columns(module_source: str, failures: list[str]) -> None:
    try:
        tree = ast.parse(module_source)
    except SyntaxError as exc:
        failures.append(f"module does not parse: {exc}")
        return
    for constant in ["DIAGNOSIS_COLUMNS", "SUMMARY_COLUMNS", "BLOCKER_COLUMNS", "RECOMMENDATION_COLUMNS"]:
        columns = extract_list_constant(tree, constant, failures)
        if not columns:
            continue
        required = {
            "research_only",
            "report_only",
            "execution_approved",
            "paper_execution_approved",
            "smoke_test_order_approved",
            "scheduling_approved",
            "orders_created",
            "orders_submitted",
            "orders_cancelled",
            "sqlite_trade_log_written",
            "discord_alert_sent",
            "telegram_alert_sent",
            "alpaca_called",
        }
        missing = sorted(required - set(columns))
        if missing:
            failures.append(f"{constant} missing safety columns: {', '.join(missing)}")


def verify_order_gate_unchanged(bot_source: str, failures: list[str]) -> None:
    required = [
        "def run_paper_order_test(",
        "evaluate_paper_kill_switch_gate(",
        "paper_kill_switch_enabled=getattr(config, \"paper_kill_switch_enabled\", None)",
        "manual_paper_order_execution_eligibility_blocked()",
        "manual_paper_order_defensive_decision_blocked()",
        "Manual paper-order test blocked by paper kill-switch preflight",
    ]
    for token in required:
        if token not in bot_source:
            failures.append(f"paper-order kill-switch gate token missing or changed: {token}")


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
    docs_lower = docs_source.lower()
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in ["paper smoke-test kill-switch diagnosis", "saved-output", "does not approve"]:
        if phrase not in docs_lower:
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
