from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_seed_change_manual_approval_record import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_seed_change_manual_approval_record,
    show_vol_targeted_growth_seed_change_manual_approval_record,
)


COMMANDS = [
    "--vol-targeted-growth-seed-change-manual-approval-record",
    "--show-vol-targeted-growth-seed-change-manual-approval-record",
]
FALSE_FLAGS = [
    "seed_changed",
    "seed_change_implemented",
    "qqq100_displacement_implemented",
    "qqq100_displacement_approved",
    "vol_targeted_seed_approved",
    "action_preview_added",
    "order_instructions_created",
    "market_data_refreshed",
    "yfinance_called",
    "alpaca_called",
    "live_positions_read",
    "paper_positions_read",
    "broker_positions_read_now",
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
    "manual_approval_record_only",
    "proposal_only",
    "preview_only",
    "manual_approval_recorded",
    "seed_change_approved_for_implementation_design",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_manual_approval_record.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth seed-change manual approval record verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth seed-change manual approval record verification passed.")
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
    for path in OUTPUT_FILES.values():
        output = str(path).replace("\\", "/")
        result = subprocess.run(["git", "check-ignore", output], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"generated output is not ignored: {output}")


def verify_source(source: str, failures: list[str]) -> None:
    for token in [
        FINAL_STATUS,
        "approval_to_design_seed_change_implementation_not_to_execute",
        "seed_not_changed_qqq100_retained_until_separate_implementation",
        "implementation_not_added",
        "design_seed_change_implementation_without_execution",
        "manual_approval_recorded",
        "seed_change_approved_for_implementation_design",
        "seed_changed",
        "qqq100_displacement_approved",
        "vol_targeted_seed_approved",
        "order_instructions_created",
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
    for forbidden_field in ["order_side", "order_quantity", "order_type", "account_id", "api_key", "webhook", "secret_key", "order_id"]:
        if f'"{forbidden_field}"' in source:
            failures.append(f"forbidden output field: {forbidden_field}")


def verify_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_seed_change_manual_approval_record(root)
        if summary_value(result.summary_rows, "final_manual_approval_status") != FINAL_STATUS:
            failures.append("fixture did not produce expected manual approval status")
        if summary_value(result.summary_rows, "manual_approval_scope") != "approval_to_design_seed_change_implementation_not_to_execute":
            failures.append("manual approval scope must be design-only")
        if summary_value(result.summary_rows, "seed_change_decision") != "seed_not_changed_qqq100_retained_until_separate_implementation":
            failures.append("seed must remain unchanged until separate implementation")
        if summary_value(result.summary_rows, "implementation_status") != "implementation_not_added":
            failures.append("implementation must not be added")
        for row in result.summary_rows + result.record_rows + result.evidence_rows + result.blocker_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag}")
                    return
            for flag in TRUE_FLAGS:
                if str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag}")
                    return
        code, lines = show_vol_targeted_growth_seed_change_manual_approval_record(root)
        joined = "\n".join(lines)
        if code != 0 or FINAL_STATUS not in joined:
            failures.append("show command did not display saved manual approval record")
        if "seed_changed=false" not in joined or "execution_approved=false" not in joined:
            failures.append("show command must preserve false approval flags")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_formal_seed_change_proposal_summary.csv",
        {
            "final_proposal_status": "vol_targeted_growth_formal_seed_change_proposal_created_manual_approval_required",
            "proposal_decision": "proposal_created_for_manual_review_not_approved",
            "manual_approval_status": "manual_approval_not_recorded",
            "seed_change_decision": "seed_not_changed_qqq100_retained",
        },
    )


def write_summary(path: Path, values: dict[str, str]) -> None:
    write_csv(path, ["summary_name", "summary_value"], [{"summary_name": key, "summary_value": value} for key, value in values.items()])


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def summary_value(rows: list[dict[str, object]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
