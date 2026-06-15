from __future__ import annotations

import ast
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "qqq100_action_preview.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"

COMMANDS = ["--qqq100-action-preview", "--show-qqq100-action-preview"]
OUTPUTS = [
    "data/qqq100_action_preview.csv",
    "data/qqq100_action_preview_summary.csv",
    "data/qqq100_action_preview_blockers.csv",
]

REQUIRED_TOKENS = [
    "qqq100_action_preview_created",
    "saved_signal_loaded",
    "position_not_read",
    "saved_signal_only",
    "paper_positions_readonly_loaded",
    "aligned_long",
    "aligned_flat",
    "review_required_not_aligned",
    "position_context_unavailable",
    "execution_blocked",
    "paper_execution_not_approved",
    "orders_created_false",
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
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
]

FORBIDDEN_MODULE_TOKENS = [
    "MarketOrderRequest",
    "OrderSide",
    "TimeInForce",
    "submit_order",
    "cancel_order",
    "replace_order",
    "create_order",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "sched.scheduler",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
    "yf.",
    "import yfinance",
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
        print("QQQ100 action preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 action preview verification passed.")
    print("Verified saved-signal default mode, explicit read-only position context, ignored outputs, blocked execution, and no order-instruction schema.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--qqq100-action-preview", "if _is_qqq100_action_preview_early_args(sys.argv[1:]):"),
        ("--show-qqq100-action-preview", 'if sys.argv[1:] == ["--show-qqq100-action-preview"]:'),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early safe branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before normal config loading")
    if "--use-paper-positions-readonly can only be used with --preview-promoted-actions or --qqq100-action-preview" not in bot_source:
        failures.append("read-only paper positions guard should allow only promoted actions or qqq100 action preview")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("QQQ100 action preview module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required action-preview token: {token}")
    for token in FORBIDDEN_MODULE_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/refresh/scheduling token in module: {token}")
    if "data/qqq100_preview_signal_pack.csv" not in module_source or "load_saved_signal" not in module_source:
        failures.append("action preview must read the saved QQQ100 preview signal")
    if "def fetch_" in module_source or "download(" in module_source:
        failures.append("action preview must not refresh market data")
    if "confirm_readonly_alpaca_check" not in module_source or "use_paper_positions_readonly" not in module_source:
        failures.append("read-only paper-position mode must require explicit flags")
    if "TradingClient" in module_source and "load_readonly_paper_position" not in module_source:
        failures.append("TradingClient, if present, must be scoped to the read-only position loader")
    if "get_all_positions" in module_source and "submit_order" in module_source:
        failures.append("read-only positions check must not be paired with order submission")
    verify_preview_columns(module_source, failures)
    display_start = module_source.find("def show_qqq100_action_preview")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_qqq100_action_preview" in display_source:
            failures.append("display command must not regenerate the action preview")


def verify_preview_columns(module_source: str, failures: list[str]) -> None:
    try:
        tree = ast.parse(module_source)
    except SyntaxError as exc:
        failures.append(f"module does not parse: {exc}")
        return
    preview_columns: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PREVIEW_COLUMNS":
                    try:
                        preview_columns = list(ast.literal_eval(node.value))
                    except Exception as exc:
                        failures.append(f"could not inspect PREVIEW_COLUMNS: {exc}")
                    break
    if not preview_columns:
        failures.append("PREVIEW_COLUMNS not found")
        return
    required = {
        "strategy_name",
        "ticker",
        "desired_position",
        "signal_date",
        "latest_close_if_saved",
        "trend_state",
        "preview_signal_status",
        "current_position_status",
        "current_position_source",
        "current_position_quantity_if_readonly",
        "position_read_mode",
        "alignment_state",
        "non_executable_preview_action",
        "blocker",
        "next_step",
        "research_only",
        "preview_only",
        "action_preview_only",
        "alpaca_called",
        "alpaca_readonly",
        "paper_positions_read",
        "orders_created",
        "orders_submitted",
        "orders_cancelled",
        "sqlite_trade_log_written",
        "discord_alert_sent",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
    }
    missing = sorted(required - set(preview_columns))
    if missing:
        failures.append(f"missing required preview columns: {', '.join(missing)}")
    forbidden = sorted(FORBIDDEN_COLUMNS & set(preview_columns))
    if forbidden:
        failures.append(f"forbidden sensitive/order columns present: {', '.join(forbidden)}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in ["QQQ100 action preview", "saved-signal", "read-only", "does not approve execution"]:
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
