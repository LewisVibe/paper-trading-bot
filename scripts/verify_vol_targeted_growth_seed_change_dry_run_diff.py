from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_seed_change_dry_run_diff import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_seed_change_dry_run_diff,
    show_vol_targeted_growth_seed_change_dry_run_diff,
)


COMMANDS = [
    "--vol-targeted-growth-seed-change-dry-run-diff",
    "--show-vol-targeted-growth-seed-change-dry-run-diff",
]
FALSE_FLAGS = [
    "seed_changed",
    "seed_change_implemented",
    "active_seed_changed",
    "qqq100_displacement_implemented",
    "qqq100_displacement_approved",
    "vol_targeted_seed_approved",
    "files_modified_by_diff",
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
    "dry_run_diff_only",
    "implementation_plan_only",
    "preview_only",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_dry_run_diff.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth seed-change dry-run diff verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth seed-change dry-run diff verification passed.")
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
        "list_future_seed_switch_changes_without_applying_them",
        "seed_not_changed_dry_run_diff_only",
        "manual_review_required_before_seed_switch_code_change",
        "files_modified_by_diff",
        "future_change_identified_not_applied",
        "do_not_touch_execution_paths",
        "order_instructions_not_allowed",
        "execution_not_approved",
        "active_seed_changed",
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
    show_body = source_slice(source, "def show_vol_targeted_growth_seed_change_dry_run_diff", "def implementation_design_ready")
    if "write_rows" in show_body or "generate_vol_targeted_growth_seed_change_dry_run_diff" in show_body:
        failures.append("show command must not regenerate output")
    for forbidden_field in ["order_side", "order_quantity", "order_type", "account_id", "api_key", "webhook", "secret_key", "order_id"]:
        if f'"{forbidden_field}"' in source:
            failures.append(f"forbidden output field: {forbidden_field}")


def verify_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_seed_change_dry_run_diff(root)
        if summary_value(result.summary_rows, "final_dry_run_diff_status") != FINAL_STATUS:
            failures.append("fixture did not produce expected dry-run diff status")
        if summary_value(result.summary_rows, "dry_run_scope") != "list_future_seed_switch_changes_without_applying_them":
            failures.append("dry-run scope must be non-mutating")
        if summary_value(result.summary_rows, "seed_change_decision") != "seed_not_changed_dry_run_diff_only":
            failures.append("seed must remain unchanged")
        if summary_value(result.summary_rows, "largest_blocker") != "manual_review_required_before_seed_switch_code_change":
            failures.append("largest blocker should require manual review before code change")
        if int(summary_value(result.summary_rows, "future_change_count") or "0") < 5:
            failures.append("dry-run should list multiple future change surfaces")
        joined_targets = "\n".join(str(row.get("target_file", "")) for row in result.diff_rows)
        for target in [
            "paper_live_monitoring_status.py",
            "vps_daily_monitoring_summary.py",
            "paper_live_promotion_ladder_status.py",
            "paper_live_checklist_status.py",
        ]:
            if target not in joined_targets:
                failures.append(f"missing future target: {target}")
        for row in result.summary_rows + result.diff_rows + result.evidence_rows + result.blocker_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag}")
                    return
            for flag in TRUE_FLAGS:
                if str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag}")
                    return
        code, lines = show_vol_targeted_growth_seed_change_dry_run_diff(root)
        joined = "\n".join(lines)
        if code != 0 or FINAL_STATUS not in joined:
            failures.append("show command did not display saved dry-run diff")
        if "files_modified_by_diff=false" not in joined or "execution_approved=false" not in joined:
            failures.append("show command must preserve false mutation/execution flags")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(
        data / "vol_targeted_growth_seed_change_implementation_design_summary.csv",
        {
            "final_design_status": "vol_targeted_growth_seed_change_implementation_design_created_manual_review_required",
            "implementation_scope": "design_seed_change_implementation_without_execution",
            "seed_change_decision": "seed_not_changed_qqq100_retained_until_separate_implementation",
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
