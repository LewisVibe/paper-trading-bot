from __future__ import annotations

import ast
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "qqq100_preview_signal_pack.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"

COMMANDS = ["--qqq100-preview-signal-pack", "--show-qqq100-preview-signal-pack"]
OUTPUTS = [
    "data/qqq100_preview_signal_pack.csv",
    "data/qqq100_preview_signal_summary.csv",
    "data/qqq100_preview_signal_design.csv",
    "data/qqq100_preview_signal_blockers.csv",
]

REQUIRED_TOKENS = [
    "qqq100_preview_signal_pack_created",
    "qqq100_clean_lead_preview_enabled",
    "preview_signal_only",
    "action_preview_not_added",
    "execution_blocked",
    "paper_execution_not_approved",
    "high_growth_branch_excluded_from_preview",
    "adaptive_qqq_alternative_not_previewed",
    "qqq150_high_drawdown_reference_rejected",
    "qqq_100_trend_gate",
    "codex_qqq_adaptive_trend_exposure",
    "qqq_150_trend_gate",
    '"action_preview_added": False',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
]

FORBIDDEN_TOKENS = [
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

FORBIDDEN_SIGNAL_COLUMNS = {
    "order_quantity",
    "order_side",
    "order_type",
    "account_id",
    "api_key",
    "webhook",
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
        print("QQQ100 preview signal pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 preview signal pack verification passed.")
    print("Verified non-execution preview signal, QQQ100-only strategy scope, no action preview, no order-instruction columns, ignored outputs, and blocked execution.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command registration/routing: {command}")
    for command, branch in [
        ("--qqq100-preview-signal-pack", 'if sys.argv[1:] == ["--qqq100-preview-signal-pack"]:'),
        ("--show-qqq100-preview-signal-pack", 'if sys.argv[1:] == ["--show-qqq100-preview-signal-pack"]:'),
    ]:
        branch_index = bot_source.find(branch)
        if branch_index == -1:
            failures.append(f"missing early safe branch for {command}")
        elif load_config_index != -1 and branch_index > load_config_index:
            failures.append(f"{command} must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("QQQ100 preview signal module is missing")
    for output in OUTPUTS:
        if output not in module_source:
            failures.append(f"missing expected output path in module: {output}")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"missing required preview-signal token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in module: {token}")
    if "yfinance_cache" not in module_source or "set_tz_cache_location" not in module_source:
        failures.append("preview signal should configure a local yfinance cache before fetching")
    if "STRATEGY_NAME = \"qqq_100_trend_gate\"" not in module_source:
        failures.append("qqq_100_trend_gate must be the only previewed strategy")
    if "high_growth_branch_excluded_from_preview" not in module_source:
        failures.append("high-growth branch exclusion must be explicit")
    verify_signal_columns(module_source, failures)
    display_start = module_source.find("def show_qqq100_preview_signal_pack")
    if display_start == -1:
        failures.append("missing saved-display function")
    else:
        display_source = module_source[display_start:]
        if "generate_qqq100_preview_signal_pack" in display_source:
            failures.append("display command must not regenerate the signal pack")


def verify_signal_columns(module_source: str, failures: list[str]) -> None:
    try:
        tree = ast.parse(module_source)
    except SyntaxError as exc:
        failures.append(f"module does not parse: {exc}")
        return
    signal_columns: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SIGNAL_COLUMNS":
                    try:
                        signal_columns = list(ast.literal_eval(node.value))
                    except Exception as exc:
                        failures.append(f"could not inspect SIGNAL_COLUMNS: {exc}")
                    break
    if not signal_columns:
        failures.append("SIGNAL_COLUMNS not found")
        return
    required = {"strategy_name", "ticker", "signal_date", "latest_close", "sma_100", "trend_state", "desired_position", "signal_reason", "data_status", "research_only", "preview_only", "action_preview_added", "execution_approved", "paper_execution_approved", "scheduling_approved"}
    missing = sorted(required - set(signal_columns))
    if missing:
        failures.append(f"missing required signal columns: {', '.join(missing)}")
    forbidden = sorted(FORBIDDEN_SIGNAL_COLUMNS & set(signal_columns))
    if forbidden:
        failures.append(f"forbidden order/execution instruction columns present: {', '.join(forbidden)}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in docs_source:
            failures.append(f"missing docs for command: {command}")
    for output in OUTPUTS:
        if output not in docs_source:
            failures.append(f"missing docs for output: {output}")
    for phrase in ["QQQ100 preview signal pack", "non-execution", "preview signal only", "does not approve execution"]:
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
