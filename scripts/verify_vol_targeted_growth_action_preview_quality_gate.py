from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_action_preview_quality_gate import (  # noqa: E402
    FORBIDDEN_COLUMNS,
    OUTPUT_FILES,
    READY_STATUS,
    SAFETY_FLAGS,
    SELECTED_CANDIDATE,
    generate_vol_targeted_growth_action_preview_quality_gate,
    show_vol_targeted_growth_action_preview_quality_gate,
)


COMMANDS = [
    "--vol-targeted-growth-action-preview-quality-gate",
    "--show-vol-targeted-growth-action-preview-quality-gate",
]

EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_action_preview_quality_gate.csv",
    "data/vol_targeted_growth_action_preview_quality_gate_summary.csv",
    "data/vol_targeted_growth_action_preview_quality_gate_evidence.csv",
    "data/vol_targeted_growth_action_preview_quality_gate_blockers.csv",
]

FALSE_FLAGS = [
    "broker_positions_compared",
    "current_positions_read",
    "order_instructions_created",
    "market_data_refreshed",
    "yfinance_called",
    "alpaca_called",
    "live_positions_read",
    "paper_positions_read",
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
    "paper_live_candidate_approved",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
]

TRUE_FLAGS = [
    "research_only",
    "report_only",
    "saved_output_only",
    "preview_only",
    "quality_gate_only",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_action_preview_quality_gate.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth action-preview quality gate verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth action-preview quality gate verification passed.")
    print("Verified saved-output quality gate, no broker/config/order/scheduling paths, forbidden order fields blocked, and false approvals.")
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
        READY_STATUS,
        "broker_position_comparison_not_completed",
        "forbidden_order_columns_absent",
        "current_exposure_loudly_unknown",
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
    show_body = source_slice(module_source, "def show_vol_targeted_growth_action_preview_quality_gate", "def build_gate_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_action_preview_quality_gate" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_fixture_files(data)

        result = generate_vol_targeted_growth_action_preview_quality_gate(root)
        status = summary_value(result.summary_rows, "final_quality_gate_status")
        if status != READY_STATUS:
            failures.append(f"fixture should produce quality-gate ready/manual-review status, got {status}")
        if summary_value(result.summary_rows, "quality_error_count") != "0":
            failures.append("quality gate should have zero fixture errors")
        if summary_value(result.summary_rows, "largest_blocker") != "broker_position_comparison_not_completed":
            failures.append("largest blocker should remain broker-position comparison not completed")
        for row in result.gate_rows + result.summary_rows + result.evidence_rows + result.blocker_rows:
            for flag in FALSE_FLAGS:
                if flag in row and str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag} in output row")
                    return
            for flag in TRUE_FLAGS:
                if flag in row and str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag} in output row")
                    return

        code, lines = show_vol_targeted_growth_action_preview_quality_gate(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [READY_STATUS, SELECTED_CANDIDATE, "broker_positions_compared=false", "order_instructions_created=false", "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display output missing token: {token}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_fixture_files(data, include_forbidden_column=True)
        result = generate_vol_targeted_growth_action_preview_quality_gate(root)
        forbidden_check = next((row for row in result.gate_rows if row.get("check_name") == "forbidden_order_columns_absent"), {})
        if forbidden_check.get("status") != "error":
            failures.append("forbidden order columns must block the quality gate")
        forbidden_values = set(str(forbidden_check.get("evidence_value", "")).split(";"))
        if not forbidden_values.intersection(FORBIDDEN_COLUMNS):
            failures.append("forbidden order column evidence should name the bad field")


def write_fixture_files(data: Path, include_forbidden_column: bool = False) -> None:
    preview_fields = [
        "selected_candidate",
        "sleeve_name",
        "target_weight",
        "current_exposure_status",
        "manual_review_label",
        "broker_positions_compared",
        "order_instructions_created",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
    ]
    row = {
        "selected_candidate": SELECTED_CANDIDATE,
        "sleeve_name": "qqq100_core_trend_sleeve",
        "target_weight": "0.70",
        "current_exposure_status": "current_exposure_not_read",
        "manual_review_label": "current_exposure_not_read_manual_review_required",
        "broker_positions_compared": "False",
        "order_instructions_created": "False",
        "execution_approved": "False",
        "paper_execution_approved": "False",
        "scheduling_approved": "False",
    }
    if include_forbidden_column:
        preview_fields.append("order_quantity")
        row["order_quantity"] = "1"
    write_csv(data / "vol_targeted_growth_action_preview.csv", preview_fields, [row])
    write_csv(
        data / "vol_targeted_growth_action_preview_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_action_preview_status", "summary_value": "vol_targeted_growth_action_preview_created_saved_output_only"}],
    )
    write_csv(
        data / "vol_targeted_growth_action_preview_blockers.csv",
        ["blocker_name", "status"],
        [{"blocker_name": "broker_position_comparison_not_approved", "status": "blocked"}],
    )
    write_csv(
        data / "vol_targeted_growth_active_seed_readiness_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_active_seed_readiness_status", "summary_value": "vol_targeted_growth_active_seed_monitoring_ready_manual_review_required"}],
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summary_value(rows: list[dict[str, object]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""


def source_slice(source: str, start_token: str, end_token: str) -> str:
    start = source.find(start_token)
    if start < 0:
        return ""
    end = source.find(end_token, start + len(start_token))
    return source[start:] if end < 0 else source[start:end]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
