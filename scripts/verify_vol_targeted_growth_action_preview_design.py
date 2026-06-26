from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_action_preview_design import (  # noqa: E402
    FINAL_STATUS,
    NEXT_STEP,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    SELECTED_CANDIDATE,
    generate_vol_targeted_growth_action_preview_design,
    show_vol_targeted_growth_action_preview_design,
)


EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_action_preview_design.csv",
    "data/vol_targeted_growth_action_preview_design_summary.csv",
    "data/vol_targeted_growth_action_preview_design_evidence.csv",
    "data/vol_targeted_growth_action_preview_design_blockers.csv",
]

COMMANDS = [
    "--vol-targeted-growth-action-preview-design",
    "--show-vol-targeted-growth-action-preview-design",
]

FALSE_FLAGS = [
    "action_preview_created",
    "order_instructions_created",
    "market_data_refreshed",
    "yfinance_called",
    "alpaca_called",
    "live_positions_read",
    "broker_positions_compared",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "portfolio_execution_wired",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "preview_candidate_approved",
    "preview_implementation_approved",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
    "high_growth_promotion_approved",
    "crypto_execution_approved",
]

TRUE_FLAGS = [
    "research_only",
    "report_only",
    "saved_output_only",
    "preview_only",
    "action_preview_design_only",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_action_preview_design.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth action-preview design verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth action-preview design verification passed.")
    print("Verified design-only scope, saved preview-signal input, no action rows, no broker/config/order/scheduling paths, and false approvals.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    load_config_index = bot_source.find("config = load_config(")
    if load_config_index < 0:
        failures.append("bot.py missing expected load_config marker")
        load_config_index = len(bot_source)
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"bot.py missing command: {command}")
        early_index = bot_source.find(f'sys.argv[1:] == ["{command}"]')
        if early_index < 0:
            failures.append(f"bot.py missing early report-only route for {command}")
        elif early_index > load_config_index:
            failures.append(f"early report-only route for {command} appears after config loading")
    for token in ["generate_vol_targeted_growth_action_preview_design", "show_vol_targeted_growth_action_preview_design"]:
        if token not in bot_source:
            failures.append(f"bot.py missing function token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        result = subprocess.run(["git", "check-ignore", expected], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"generated output is not ignored by git: {expected}")


def verify_source_boundaries(module_source: str, failures: list[str]) -> None:
    required = [
        SELECTED_CANDIDATE,
        FINAL_STATUS,
        NEXT_STEP,
        "saved-state comparison design only",
        "manual-review labels only",
        "broker_positions_compared",
        "action_preview_created",
        "order_instructions_created",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "never_schedule_order_capable_commands",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")

    for flag in FALSE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not False:
            failures.append(f"safety flag must be false: {flag}")
    for flag in TRUE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not True:
            failures.append(f"safety flag must be true: {flag}")

    forbidden = [
        "TradingClient",
        "GetOrdersRequest",
        "get_all_positions",
        "submit_order",
        "MarketOrderRequest",
        "cancel_order",
        "replace_order",
        "insert_trade_log",
        "send_discord_alert",
        "send_telegram",
        "import yfinance",
        "yf.download",
        "load_config(",
        "config.json",
        "Register-ScheduledTask",
        "schtasks /create",
        "crontab",
        "systemctl",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"module must not contain forbidden token: {token}")

    show_body = source_slice(module_source, "def show_vol_targeted_growth_action_preview_design", "def build_design_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_action_preview_design" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "vol_targeted_growth_preview_signal_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "final_signal_status", "summary_value": "vol_targeted_growth_preview_signal_created_saved_output_only"},
                {"summary_name": "selected_candidate", "summary_value": SELECTED_CANDIDATE},
                {"summary_name": "target_sleeve_weights", "summary_value": "70% qqq100_core_trend_sleeve; 20% high_growth_stock_research_sleeve; 5% crypto_research_sleeve; 5% defensive_cash_or_bond_sleeve"},
            ],
        )
        write_csv(
            data / "vol_targeted_growth_preview_signal.csv",
            ["signal_item", "selected_candidate", "target_weight"],
            [{"signal_item": "target_sleeve_weight", "selected_candidate": SELECTED_CANDIDATE, "target_weight": "0.70"}],
        )
        write_csv(
            data / "vol_targeted_growth_preview_signal_blockers.csv",
            ["blocker_name", "status"],
            [{"blocker_name": "action_preview_not_created", "status": "blocked"}],
        )
        write_csv(
            data / "vol_targeted_growth_preview_design_summary.csv",
            ["summary_name", "summary_value"],
            [{"summary_name": "final_design_status", "summary_value": "vol_targeted_growth_preview_design_ready_for_future_preview_implementation"}],
        )

        result = generate_vol_targeted_growth_action_preview_design(root)
        status = summary_value(result.summary_rows, "final_design_status")
        if status != FINAL_STATUS:
            failures.append(f"fixture should produce design-ready status, got {status}")
        if SELECTED_CANDIDATE not in summary_value(result.summary_rows, "selected_candidate"):
            failures.append("selected candidate missing from summary")
        if "saved-state comparison design only" not in summary_value(result.summary_rows, "future_action_preview_scope"):
            failures.append("future action-preview scope should remain design-only")

        for collection in [result.design_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
            for row in collection:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return

        code, lines = show_vol_targeted_growth_action_preview_design(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [FINAL_STATUS, SELECTED_CANDIDATE, "action_preview_created=false", "broker_positions_compared=false", "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display output missing token: {token}")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start_token: str, end_token: str) -> str:
    start = source.find(start_token)
    if start < 0:
        return ""
    end = source.find(end_token, start + len(start_token))
    if end < 0:
        return source[start:]
    return source[start:end]


def summary_value(rows: list[dict[str, object]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
