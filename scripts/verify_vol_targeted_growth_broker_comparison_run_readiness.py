from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_broker_comparison_run_readiness import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_broker_comparison_run_readiness,
    show_vol_targeted_growth_broker_comparison_run_readiness,
)


COMMANDS = [
    "--vol-targeted-growth-broker-comparison-run-readiness",
    "--show-vol-targeted-growth-broker-comparison-run-readiness",
]
EXPECTED_OUTPUTS = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
FALSE_FLAGS = [
    "readonly_broker_comparison_run_approved",
    "paper_live_candidate_approved",
    "paper_live_discussion_approved",
    "broker_position_comparison_approved",
    "broker_positions_compared",
    "alpaca_called",
    "live_positions_read",
    "paper_positions_read",
    "order_instructions_created",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "portfolio_execution_wired",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]
TRUE_FLAGS = [
    "research_only",
    "report_only",
    "saved_output_only",
    "manual_review_only",
    "run_readiness_only",
    "preview_only",
    "readonly_broker_comparison_ready_for_manual_approval",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_broker_comparison_run_readiness.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth broker-comparison run-readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth broker-comparison run-readiness verification passed.")
    return 0


def verify_commands(source: str, failures: list[str]) -> None:
    load_config = source.find("config = load_config(")
    if load_config < 0:
        load_config = len(source)
    for command in COMMANDS:
        if command not in source:
            failures.append(f"missing command: {command}")
        early = source.find(f'sys.argv[1:] == ["{command}"]')
        if early < 0:
            failures.append(f"missing early route: {command}")
        elif early > load_config:
            failures.append(f"route appears after config loading: {command}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in EXPECTED_OUTPUTS:
        result = subprocess.run(["git", "check-ignore", output], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"generated output is not ignored: {output}")


def verify_source(source: str, failures: list[str]) -> None:
    for token in [
        FINAL_STATUS,
        "ready_to_request_manual_approval_not_run",
        "explicit_manual_approval_required_before_any_broker_read",
        "readonly_broker_comparison_run_approved",
        "broker_positions_compared",
        "paper_live_discussion_not_approved_research_only",
        "execution_approved",
        "scheduling_approved",
    ]:
        if token not in source:
            failures.append(f"missing required token: {token}")
    for flag in FALSE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not False:
            failures.append(f"flag must be false: {flag}")
    for flag in TRUE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not True:
            failures.append(f"flag must be true: {flag}")
    for token in [
        "TradingClient",
        "get_all_positions",
        "submit_order",
        "MarketOrderRequest",
        "cancel_order",
        "replace_order",
        "load_config(",
        "config.json",
        "import yfinance",
        "yf.download",
        "insert_trade_log",
        "send_discord",
        "send_telegram",
        "Register-ScheduledTask",
        "schtasks /create",
        "crontab",
        "systemctl",
    ]:
        if token in source:
            failures.append(f"forbidden token: {token}")
    show_body = source_slice(source, "def show_vol_targeted_growth_broker_comparison_run_readiness", "def determine_final_status")
    if "write_rows" in show_body or "generate_vol_targeted_growth_broker_comparison_run_readiness" in show_body:
        failures.append("show command must not regenerate output")


def verify_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "vol_targeted_growth_paper_live_decision_summary.csv",
            ["summary_name", "summary_value"],
            [
                {
                    "summary_name": "final_decision_status",
                    "summary_value": "vol_targeted_growth_research_only_broker_comparison_discussion_ready_manual_review_required",
                }
            ],
        )
        write_csv(
            data / "vol_targeted_growth_broker_position_comparison_design_summary.csv",
            ["summary_name", "summary_value"],
            [
                {
                    "summary_name": "final_design_status",
                    "summary_value": "vol_targeted_growth_broker_position_comparison_design_ready_manual_review_required",
                }
            ],
        )
        write_csv(
            data / "vol_targeted_growth_action_preview_summary.csv",
            ["summary_name", "summary_value"],
            [{"summary_name": "final_action_preview_status", "summary_value": "vol_targeted_growth_action_preview_created_saved_output_only"}],
        )
        write_csv(
            data / "vol_targeted_growth_portfolio_risk_policy_design_summary.csv",
            ["summary_name", "summary_value"],
            [
                {
                    "summary_name": "final_policy_design_status",
                    "summary_value": "vol_targeted_growth_portfolio_risk_policy_design_ready_manual_review_required",
                }
            ],
        )
        result = generate_vol_targeted_growth_broker_comparison_run_readiness(root)
        if summary_value(result.summary_rows, "final_run_readiness_status") != FINAL_STATUS:
            failures.append("fixture did not produce expected run-readiness status")
        if summary_value(result.summary_rows, "readonly_broker_comparison_status") != "ready_to_request_manual_approval_not_run":
            failures.append("read-only comparison should be ready to request approval, not run")
        if summary_value(result.summary_rows, "manual_approval_status") != "explicit_manual_approval_required_before_any_broker_read":
            failures.append("manual approval must still be required")
        if summary_value(result.summary_rows, "broker_positions_compared") != "false":
            failures.append("broker positions must not be compared")
        for row in result.summary_rows + result.readiness_rows + result.evidence_rows + result.blocker_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag}")
                    return
            for flag in TRUE_FLAGS:
                if str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag}")
                    return
        code, lines = show_vol_targeted_growth_broker_comparison_run_readiness(root)
        if code != 0 or FINAL_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved run-readiness report")


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
