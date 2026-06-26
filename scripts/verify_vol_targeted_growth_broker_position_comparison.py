from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.vol_targeted_growth_broker_position_comparison as module  # noqa: E402


COMMANDS = [
    "--vol-targeted-growth-broker-position-comparison",
    "--show-vol-targeted-growth-broker-position-comparison",
]
EXPECTED_OUTPUTS = [str(path).replace("\\", "/") for path in module.OUTPUT_FILES.values()]
FALSE_FLAGS = [
    "order_instructions_created",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "portfolio_execution_wired",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "paper_live_candidate_approved",
    "paper_live_discussion_approved",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
]
TRUE_FLAGS = ["research_only", "report_only", "manual_review_only", "preview_only", "readonly_comparison_only", "never_schedule_order_capable_commands"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_broker_position_comparison.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_unconfirmed_fixture(failures)
    verify_confirmed_fixture_without_network(failures)
    if failures:
        print("Volatility-targeted growth broker-position comparison verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth broker-position comparison verification passed.")
    return 0


def verify_commands(source: str, failures: list[str]) -> None:
    load_config = source.find("config = load_config(")
    if load_config < 0:
        load_config = len(source)
    for command in COMMANDS:
        if command not in source:
            failures.append(f"missing command: {command}")
    early = source.find('if "--vol-targeted-growth-broker-position-comparison" in sys.argv[1:]:')
    if early < 0:
        failures.append("missing early confirmed/unconfirmed route")
    elif early > load_config:
        failures.append("broker comparison route appears after config loading")
    show_early = source.find('sys.argv[1:] == ["--show-vol-targeted-growth-broker-position-comparison"]')
    if show_early < 0:
        failures.append("missing early show route")
    elif show_early > load_config:
        failures.append("broker comparison show route appears after config loading")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in EXPECTED_OUTPUTS:
        result = subprocess.run(["git", "check-ignore", output], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"generated output is not ignored: {output}")


def verify_source(source: str, failures: list[str]) -> None:
    for token in [
        module.CONFIRMED_STATUS,
        module.UNCONFIRMED_STATUS,
        "--confirm-readonly-alpaca-check",
        "force_dry_run=True",
        "paper=True",
        "get_all_positions",
        "order_instructions_created",
        "execution_approved",
        "scheduling_approved",
        "strategy_plain_english",
    ]:
        if token not in source:
            failures.append(f"missing required token: {token}")
    for forbidden in [
        "submit_order",
        "MarketOrderRequest",
        "cancel_order",
        "replace_order",
        "insert_trade_log",
        "send_discord",
        "send_telegram",
        "Register-ScheduledTask",
        "schtasks /create",
        "crontab",
        "systemctl",
        "yf.download",
        "import yfinance",
    ]:
        if forbidden in source:
            failures.append(f"forbidden token: {forbidden}")
    show_body = source_slice(source, "def show_vol_targeted_growth_broker_position_comparison", "def determine_final_status")
    if "write_rows" in show_body or "generate_vol_targeted_growth_broker_position_comparison" in show_body:
        failures.append("show command must not regenerate output")
    for forbidden_field in ["order_side", "order_quantity", "order_type", "account_id", "api_key", "webhook", "secret_key", "order_id"]:
        if f'"{forbidden_field}"' in source:
            failures.append(f"forbidden output field: {forbidden_field}")


def verify_unconfirmed_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = module.generate_vol_targeted_growth_broker_position_comparison(root, confirm_readonly_alpaca_check=False)
        if summary_value(result.summary_rows, "final_comparison_status") != module.UNCONFIRMED_STATUS:
            failures.append("unconfirmed fixture should not run broker comparison")
        if summary_value(result.summary_rows, "broker_position_read_status") != "readonly_confirmation_missing":
            failures.append("unconfirmed fixture should report missing confirmation")
        for row in result.summary_rows + result.comparison_rows + result.evidence_rows + result.blocker_rows:
            if str(row.get("alpaca_called", "")).lower() != "false":
                failures.append("unconfirmed path must not call Alpaca")
                return
            if str(row.get("paper_positions_read", "")).lower() != "false":
                failures.append("unconfirmed path must not read positions")
                return
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag}")
                    return
            for flag in TRUE_FLAGS:
                if str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag}")
                    return
        code, lines = module.show_vol_targeted_growth_broker_position_comparison(root)
        if code != 0 or module.UNCONFIRMED_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved unconfirmed comparison")


def verify_confirmed_fixture_without_network(failures: list[str]) -> None:
    original_loader = module.load_readonly_broker_positions
    try:
        module.load_readonly_broker_positions = lambda root: module.ReadonlyPositionSnapshot(  # type: ignore[assignment]
            status="paper_positions_read_readonly",
            positions_by_symbol={"QQQ": "1"},
            alpaca_called=True,
            paper_positions_read=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_inputs(root)
            result = module.generate_vol_targeted_growth_broker_position_comparison(root, confirm_readonly_alpaca_check=True)
            if summary_value(result.summary_rows, "final_comparison_status") != module.CONFIRMED_STATUS:
                failures.append("confirmed fixture should produce completed read-only status")
            if summary_value(result.summary_rows, "broker_position_read_status") != "paper_positions_read_readonly":
                failures.append("confirmed fixture should report read-only position context")
            qqq_rows = [row for row in result.comparison_rows if row.get("broker_symbol_proxy") == "QQQ"]
            if not qqq_rows or qqq_rows[0].get("broker_position_quantity_if_readonly") != "1":
                failures.append("confirmed fixture should include redacted QQQ quantity context")
            for row in result.summary_rows + result.comparison_rows + result.evidence_rows + result.blocker_rows:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in confirmed fixture")
                        return
    finally:
        module.load_readonly_broker_positions = original_loader


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_csv(
        data / "vol_targeted_growth_broker_comparison_run_readiness_summary.csv",
        ["summary_name", "summary_value"],
        [
            {
                "summary_name": "final_run_readiness_status",
                "summary_value": "vol_targeted_growth_readonly_broker_comparison_ready_for_explicit_manual_approval_required",
            }
        ],
    )
    write_csv(
        data / "vol_targeted_growth_action_preview_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_action_preview_status", "summary_value": "vol_targeted_growth_action_preview_created_saved_output_only"}],
    )
    write_csv(
        data / "vol_targeted_growth_preview_signal_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_signal_status", "summary_value": "vol_targeted_growth_preview_signal_created_saved_output_only"}],
    )
    write_csv(
        data / "vol_targeted_growth_action_preview.csv",
        ["sleeve_name", "target_weight", "sleeve_status"],
        [
            {"sleeve_name": "qqq100_core_trend_sleeve", "target_weight": "0.70", "sleeve_status": "clean_main_stock_etf_lead"},
            {"sleeve_name": "high_growth_stock_research_sleeve", "target_weight": "0.20", "sleeve_status": "high_growth_research_only"},
            {"sleeve_name": "crypto_research_sleeve", "target_weight": "0.05", "sleeve_status": "crypto_research_only"},
            {"sleeve_name": "defensive_cash_or_bond_sleeve", "target_weight": "0.05", "sleeve_status": "defensive_buffer_research_only"},
        ],
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start_token: str, end_token: str) -> str:
    start = source.find(start_token)
    end = source.find(end_token, start + 1) if start >= 0 else -1
    return source[start:end] if start >= 0 and end >= 0 else source[start:] if start >= 0 else ""


def summary_value(rows: list[dict[str, object]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
