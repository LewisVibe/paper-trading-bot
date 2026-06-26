from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_formal_seed_change_proposal import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_formal_seed_change_proposal,
    show_vol_targeted_growth_formal_seed_change_proposal,
)


COMMANDS = [
    "--vol-targeted-growth-formal-seed-change-proposal",
    "--show-vol-targeted-growth-formal-seed-change-proposal",
]
FALSE_FLAGS = [
    "seed_changed",
    "manual_approval_recorded",
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
    "formal_proposal_document_only",
    "proposal_only",
    "preview_only",
    "seed_change_proposal_created",
    "formal_seed_change_proposal_created",
    "qqq100_displacement_requested",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_formal_seed_change_proposal.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth formal seed-change proposal verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth formal seed-change proposal verification passed.")
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
        "proposal_created_for_manual_review_not_approved",
        "manual_approval_not_recorded",
        "seed_not_changed_qqq100_retained",
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
        result = generate_vol_targeted_growth_formal_seed_change_proposal(root)
        if summary_value(result.summary_rows, "final_proposal_status") != FINAL_STATUS:
            failures.append("fixture did not produce expected proposal status")
        if summary_value(result.summary_rows, "proposal_decision") != "proposal_created_for_manual_review_not_approved":
            failures.append("proposal should be created for review only")
        if summary_value(result.summary_rows, "manual_approval_status") != "manual_approval_not_recorded":
            failures.append("manual approval must not be recorded")
        if summary_value(result.summary_rows, "seed_change_decision") != "seed_not_changed_qqq100_retained":
            failures.append("seed must remain unchanged")
        for row in result.summary_rows + result.proposal_rows + result.evidence_rows + result.approval_rows + result.blocker_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag}")
                    return
            for flag in TRUE_FLAGS:
                if str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag}")
                    return
        code, lines = show_vol_targeted_growth_formal_seed_change_proposal(root)
        if code != 0 or FINAL_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved formal proposal")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_summary(data / "vol_targeted_growth_seed_change_manual_review_summary.csv", {
        "final_manual_review_status": "vol_targeted_growth_seed_change_ready_for_formal_proposal_manual_review",
        "evidence_missing_count": "0",
    })
    write_summary(data / "vol_targeted_growth_seed_change_evidence_summary.csv", {"seed_change_readiness": "all_evidence_present_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_risk_reward_summary.csv", {"final_risk_reward_status": "vol_targeted_growth_risk_reward_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_drawdown_stress_summary.csv", {"final_drawdown_stress_status": "vol_targeted_growth_drawdown_stress_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_cost_turnover_summary.csv", {"final_cost_turnover_status": "vol_targeted_growth_cost_turnover_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_split_stability_summary.csv", {"final_split_stability_status": "vol_targeted_growth_split_stability_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_component_sleeve_summary.csv", {"final_component_sleeve_status": "vol_targeted_growth_component_sleeve_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_broker_exposure_summary.csv", {"final_broker_exposure_status": "vol_targeted_growth_broker_exposure_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_proposal_document_summary.csv", {"final_proposal_document_status": "vol_targeted_growth_seed_change_proposal_document_draft_created_manual_review_required"})
    write_summary(data / "qqq100_followup_policy_summary.csv", {"final_followup_policy_status": "no_action_required_already_aligned"})


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
