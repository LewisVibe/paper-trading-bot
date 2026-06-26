from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_seed_change_manual_review_checkpoint import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_seed_change_manual_review_checkpoint,
    show_vol_targeted_growth_seed_change_manual_review_checkpoint,
)


COMMANDS = [
    "--vol-targeted-growth-seed-change-manual-review-checkpoint",
    "--show-vol-targeted-growth-seed-change-manual-review-checkpoint",
]
FALSE_FLAGS = [
    "seed_changed",
    "seed_change_proposal_created",
    "formal_seed_change_proposal_created",
    "qqq100_displacement_requested",
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
    "manual_review_checkpoint_only",
    "proposal_only",
    "preview_only",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_manual_review_checkpoint.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth seed-change manual-review checkpoint verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth seed-change manual-review checkpoint verification passed.")
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
        "ready_for_human_formal_proposal_review_not_approved",
        "formal_seed_change_proposal_not_created",
        "qqq100_seed_retained_no_displacement_approved",
        "seed_change_proposal_created",
        "formal_seed_change_proposal_created",
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


def verify_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_seed_change_manual_review_checkpoint(root)
        if summary_value(result.summary_rows, "final_manual_review_status") != FINAL_STATUS:
            failures.append("fixture did not produce expected manual-review checkpoint status")
        if summary_value(result.summary_rows, "evidence_missing_count") != "0":
            failures.append("fixture should have zero missing evidence")
        if summary_value(result.summary_rows, "manual_review_readiness") != "ready_for_human_formal_proposal_review_not_approved":
            failures.append("manual review readiness should not approve proposal")
        if summary_value(result.summary_rows, "seed_change_decision") != "qqq100_seed_retained_no_displacement_approved":
            failures.append("QQQ100 should remain retained")
        for row in result.summary_rows + result.checkpoint_rows + result.evidence_rows + result.blocker_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag}")
                    return
            for flag in TRUE_FLAGS:
                if str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag}")
                    return
        code, lines = show_vol_targeted_growth_seed_change_manual_review_checkpoint(root)
        if code != 0 or FINAL_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved manual-review checkpoint")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_csv(
        data / "vol_targeted_growth_seed_change_evidence_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "final_evidence_pack_status", "summary_value": "vol_targeted_growth_seed_change_evidence_pack_incomplete_manual_review_required"},
            {"summary_name": "missing_required_evidence_count", "summary_value": "0"},
            {"summary_name": "seed_change_readiness", "summary_value": "all_evidence_present_manual_review_required"},
        ],
    )
    write_csv(data / "vol_targeted_growth_seed_change_evidence_pack.csv", ["evidence_item", "evidence_status"], [{"evidence_item": "fixture", "evidence_status": "present_manual_review_required"}])
    write_csv(data / "vol_targeted_growth_seed_change_proposal_document_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "final_proposal_document_status", "summary_value": "vol_targeted_growth_seed_change_proposal_document_draft_created_manual_review_required"}])
    write_csv(data / "vol_targeted_growth_seed_change_broker_exposure_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "final_broker_exposure_status", "summary_value": "vol_targeted_growth_broker_exposure_evidence_created_manual_review_required"}])
    write_csv(data / "qqq100_followup_policy_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "final_followup_policy_status", "summary_value": "no_action_required_already_aligned"}])


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
