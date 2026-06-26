from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_action_preview import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    PREVIEW_COLUMNS,
    SAFETY_FLAGS,
    SELECTED_CANDIDATE,
    generate_vol_targeted_growth_action_preview,
    show_vol_targeted_growth_action_preview,
)


EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_action_preview.csv",
    "data/vol_targeted_growth_action_preview_summary.csv",
    "data/vol_targeted_growth_action_preview_evidence.csv",
    "data/vol_targeted_growth_action_preview_blockers.csv",
]

COMMANDS = [
    "--vol-targeted-growth-action-preview",
    "--show-vol-targeted-growth-action-preview",
]

FALSE_FLAGS = [
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
    "action_preview_only",
    "action_preview_created",
    "never_schedule_order_capable_commands",
]

FORBIDDEN_COLUMNS = {
    "side",
    "quantity",
    "order_qty",
    "order_quantity",
    "order_side",
    "order_type",
    "time_in_force",
    "account_id",
    "api_key",
    "webhook",
    "secret",
    "token",
    "order_id",
    "execution_instruction",
}


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_action_preview.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_output_schema(failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth action preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth action preview verification passed.")
    print("Verified saved-output action-preview scope, unknown current exposure handling, no broker/config/order/scheduling paths, and false approvals.")
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
    for token in ["generate_vol_targeted_growth_action_preview", "show_vol_targeted_growth_action_preview"]:
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
        "current_exposure_not_read",
        "manual_review",
        "broker_positions_compared",
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

    show_body = source_slice(module_source, "def show_vol_targeted_growth_action_preview", "def build_preview_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_action_preview" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_output_schema(failures: list[str]) -> None:
    forbidden_columns = FORBIDDEN_COLUMNS.intersection(PREVIEW_COLUMNS)
    if forbidden_columns:
        failures.append(f"preview schema contains forbidden order/security columns: {sorted(forbidden_columns)}")
    for required in ["target_weight", "current_exposure_status", "manual_review_label", "execution_approved", "paper_execution_approved", "scheduling_approved"]:
        if required not in PREVIEW_COLUMNS:
            failures.append(f"preview schema missing required column: {required}")


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
            ],
        )
        write_csv(
            data / "vol_targeted_growth_preview_signal.csv",
            ["signal_item", "sleeve_name", "target_weight", "sleeve_status"],
            [
                {"signal_item": "target_sleeve_weight", "sleeve_name": "qqq100_core_trend_sleeve", "target_weight": "0.70", "sleeve_status": "clean_main_stock_etf_lead"},
                {"signal_item": "target_sleeve_weight", "sleeve_name": "high_growth_stock_research_sleeve", "target_weight": "0.20", "sleeve_status": "high_growth_research_only"},
            ],
        )
        write_csv(
            data / "vol_targeted_growth_action_preview_design_summary.csv",
            ["summary_name", "summary_value"],
            [{"summary_name": "final_design_status", "summary_value": "vol_targeted_growth_action_preview_design_ready_manual_review_required"}],
        )

        result = generate_vol_targeted_growth_action_preview(root)
        status = summary_value(result.summary_rows, "final_action_preview_status")
        if status != FINAL_STATUS:
            failures.append(f"fixture should produce action-preview status, got {status}")
        if len(result.preview_rows) != 2:
            failures.append(f"fixture should create two sleeve rows, got {len(result.preview_rows)}")
        for row in result.preview_rows:
            if row.get("current_exposure_status") != "current_exposure_not_read":
                failures.append("current exposure must remain not read")
            if row.get("manual_review_label") != "current_exposure_not_read_manual_review_required":
                failures.append("manual review label should be loud when exposure is unknown")

        for collection in [result.preview_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
            for row in collection:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return

        code, lines = show_vol_targeted_growth_action_preview(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [FINAL_STATUS, SELECTED_CANDIDATE, "broker_positions_compared=false", "execution_approved=false", "scheduling_approved=false"]:
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
