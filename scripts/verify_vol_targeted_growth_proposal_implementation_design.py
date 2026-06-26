from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_proposal_implementation_design import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_proposal_implementation_design,
    show_vol_targeted_growth_proposal_implementation_design,
)


COMMANDS = [
    "--vol-targeted-growth-proposal-implementation-design",
    "--show-vol-targeted-growth-proposal-implementation-design",
]
EXPECTED_OUTPUTS = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
FALSE_FLAGS = [
    "implementation_added",
    "preview_action_added",
    "alpaca_called",
    "live_positions_read",
    "paper_positions_read",
    "broker_positions_read_now",
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
    "vol_targeted_paper_live_candidate_approved",
    "preview_implementation_approved",
    "gate_enforced",
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
    "manual_review_only",
    "design_only",
    "proposal_only",
    "preview_only",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_proposal_implementation_design.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth proposal implementation design verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth proposal implementation design verification passed.")
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
        "design_only_no_implementation_added",
        "implementation_not_added_and_not_approved",
        "qqq_100_trend_gate",
        "order_instructions_created",
        "implementation_added",
        "preview_action_added",
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
    for forbidden in [
        "TradingClient",
        "get_all_positions",
        "submit_order",
        "MarketOrderRequest",
        "cancel_order",
        "replace_order",
        "load_config(",
        "config.json",
        "insert_trade_log",
        "send_discord",
        "send_telegram",
        "yf.download",
        "import yfinance",
        "Register-ScheduledTask",
        "schtasks /create",
        "crontab",
        "systemctl",
    ]:
        if forbidden in source:
            failures.append(f"forbidden token: {forbidden}")
    show_body = source_slice(source, "def show_vol_targeted_growth_proposal_implementation_design", "def determine_final_status")
    if "write_rows" in show_body or "generate_vol_targeted_growth_proposal_implementation_design" in show_body:
        failures.append("show command must not regenerate output")
    for forbidden_field in ["order_side", "order_quantity", "order_type", "account_id", "api_key", "webhook", "secret_key", "order_id"]:
        if f'"{forbidden_field}"' in source:
            failures.append(f"forbidden output field: {forbidden_field}")


def verify_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_proposal_implementation_design(root)
        if summary_value(result.summary_rows, "final_design_status") != FINAL_STATUS:
            failures.append("fixture did not produce expected final design status")
        if summary_value(result.summary_rows, "implementation_status") != "design_only_no_implementation_added":
            failures.append("implementation must remain design-only")
        if summary_value(result.summary_rows, "incumbent_seed") != "qqq_100_trend_gate":
            failures.append("QQQ100 should remain incumbent seed")
        if summary_value(result.summary_rows, "largest_blocker") != "implementation_not_added_and_not_approved":
            failures.append("largest blocker should keep implementation unadded/unapproved")
        for row in result.summary_rows + result.design_rows + result.evidence_rows + result.blocker_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag}")
                    return
            for flag in TRUE_FLAGS:
                if str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag}")
                    return
        code, lines = show_vol_targeted_growth_proposal_implementation_design(root)
        if code != 0 or FINAL_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved proposal implementation design")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_csv(
        data / "vol_targeted_growth_candidate_discussion_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_candidate_discussion_status", "summary_value": "vol_targeted_growth_non_executable_candidate_proposal_ready_manual_review_required"}],
    )
    write_csv(data / "vol_targeted_growth_candidate_discussion_blockers.csv", ["blocker_name"], [{"blocker_name": "implementation_not_added"}])
    write_csv(
        data / "vol_targeted_growth_gate_review_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_gate_review_status", "summary_value": "vol_targeted_growth_limited_manual_candidate_discussion_ready_gate_review_required"}],
    )
    write_csv(
        data / "qqq100_followup_policy_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_followup_policy_status", "summary_value": "no_action_required_already_aligned"}],
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
