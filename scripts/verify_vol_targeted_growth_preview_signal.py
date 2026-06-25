from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_preview_signal import (  # noqa: E402
    FINAL_STATUS,
    NEXT_STEP,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    SELECTED_CANDIDATE,
    SIGNAL_COLUMNS,
    SLEEVE_WEIGHTS,
    generate_vol_targeted_growth_preview_signal,
    show_vol_targeted_growth_preview_signal,
)


EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_preview_signal.csv",
    "data/vol_targeted_growth_preview_signal_summary.csv",
    "data/vol_targeted_growth_preview_signal_evidence.csv",
    "data/vol_targeted_growth_preview_signal_blockers.csv",
]

COMMANDS = [
    "--vol-targeted-growth-preview-signal",
    "--show-vol-targeted-growth-preview-signal",
]

FALSE_FLAGS = [
    "action_preview_created",
    "order_instructions_created",
    "market_data_refreshed",
    "yfinance_called",
    "alpaca_called",
    "live_positions_read",
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
    "preview_signal_only",
    "preview_signal_saved",
    "never_schedule_order_capable_commands",
]

FORBIDDEN_OUTPUT_COLUMNS = {
    "side",
    "quantity",
    "order_qty",
    "order_quantity",
    "order_type",
    "time_in_force",
    "account_id",
    "api_key",
    "webhook",
    "secret",
    "order_id",
}


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_preview_signal.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_output_schema(failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth preview signal verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth preview signal verification passed.")
    print("Verified saved-output preview-signal scope, selected 15/20 candidate, sleeve weights, no order fields, false approvals, and no broker/config/scheduling paths.")
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
    for token in ["generate_vol_targeted_growth_preview_signal", "show_vol_targeted_growth_preview_signal"]:
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
        "volatility_target=15%",
        "volatility_window=20",
        "exposure_cap=1x",
        "leverage_allowed=false",
        "target_weight",
        "preview_weight_only_not_order_quantity",
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

    show_body = source_slice(module_source, "def show_vol_targeted_growth_preview_signal", "def build_signal_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_preview_signal" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_output_schema(failures: list[str]) -> None:
    forbidden_columns = FORBIDDEN_OUTPUT_COLUMNS.intersection(SIGNAL_COLUMNS)
    if forbidden_columns:
        failures.append(f"signal schema contains forbidden order/security columns: {sorted(forbidden_columns)}")
    for required in ["target_weight", "sleeve_name", "selected_candidate", "execution_approved", "paper_execution_approved", "scheduling_approved"]:
        if required not in SIGNAL_COLUMNS:
            failures.append(f"signal schema missing required column: {required}")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "vol_targeted_growth_preview_design_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "final_design_status", "summary_value": "vol_targeted_growth_preview_design_ready_for_future_preview_implementation"},
                {"summary_name": "selected_candidate", "summary_value": SELECTED_CANDIDATE},
            ],
        )
        write_csv(
            data / "vol_targeted_growth_preview_design.csv",
            ["design_item", "status"],
            [{"design_item": "target_sleeve_weights", "status": "design_recorded"}],
        )
        write_csv(
            data / "vol_targeted_growth_preview_design_evidence.csv",
            ["evidence_name", "evidence_value"],
            [{"evidence_name": "target_metrics", "evidence_value": "CAGR=19.0011; Sharpe=1.2861"}],
        )
        write_csv(
            data / "vol_targeted_growth_preview_readiness_summary.csv",
            ["summary_name", "summary_value"],
            [{"summary_name": "final_decision_status", "summary_value": "vol_targeted_growth_15_20_selected_for_preview_design_review"}],
        )
        write_csv(
            data / "vol_targeted_growth_nearby_variants_review.csv",
            ["candidate_name", "cagr", "sharpe", "max_drawdown", "calmar"],
            [{"candidate_name": SELECTED_CANDIDATE, "cagr": "19.0011", "sharpe": "1.2861", "max_drawdown": "-18.1016", "calmar": "1.0497"}],
        )

        result = generate_vol_targeted_growth_preview_signal(root)
        status = summary_value(result.summary_rows, "final_signal_status")
        if status != FINAL_STATUS:
            failures.append(f"fixture should produce saved preview signal status, got {status}")
        if SELECTED_CANDIDATE not in summary_value(result.summary_rows, "selected_candidate"):
            failures.append("selected candidate missing from summary")
        if "70% qqq100_core_trend_sleeve" not in summary_value(result.summary_rows, "target_sleeve_weights"):
            failures.append("target sleeve weights missing QQQ100 70% sleeve")

        expected_weights = {sleeve: weight for sleeve, weight, _ in SLEEVE_WEIGHTS}
        actual_weights = {
            row.get("sleeve_name"): row.get("target_weight")
            for row in result.signal_rows
            if row.get("signal_item") == "target_sleeve_weight"
        }
        if actual_weights != expected_weights:
            failures.append(f"target sleeve weights mismatch: {actual_weights}")

        for collection in [result.signal_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
            for row in collection:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return

        signal_header = list(result.signal_rows[0].keys())
        if FORBIDDEN_OUTPUT_COLUMNS.intersection(signal_header):
            failures.append("generated signal row contains forbidden order/security columns")

        code, lines = show_vol_targeted_growth_preview_signal(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [FINAL_STATUS, SELECTED_CANDIDATE, "action_preview_created=false", "execution_approved=false", "scheduling_approved=false"]:
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
