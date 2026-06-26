from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_seed_change_remaining_evidence_reviews import (  # noqa: E402
    ACTION_STATUS,
    BROKER_EXPOSURE_STATUS,
    COMPONENT_STATUS,
    OUTPUT_FILES,
    PROPOSAL_STATUS,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_seed_change_broker_exposure_review,
    generate_vol_targeted_growth_seed_change_action_preview_design,
    generate_vol_targeted_growth_seed_change_component_sleeve_review,
    generate_vol_targeted_growth_seed_change_proposal_document,
    show_vol_targeted_growth_seed_change_broker_exposure_review,
    show_vol_targeted_growth_seed_change_action_preview_design,
    show_vol_targeted_growth_seed_change_component_sleeve_review,
    show_vol_targeted_growth_seed_change_proposal_document,
)


COMMANDS = [
    "--vol-targeted-growth-seed-change-component-sleeve-review",
    "--show-vol-targeted-growth-seed-change-component-sleeve-review",
    "--vol-targeted-growth-seed-change-action-preview-design",
    "--show-vol-targeted-growth-seed-change-action-preview-design",
    "--vol-targeted-growth-seed-change-proposal-document",
    "--show-vol-targeted-growth-seed-change-proposal-document",
    "--vol-targeted-growth-seed-change-broker-exposure-review",
    "--show-vol-targeted-growth-seed-change-broker-exposure-review",
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
    "proposal_only",
    "preview_only",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_remaining_evidence_reviews.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth remaining seed-change evidence reviews verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth remaining seed-change evidence reviews verification passed.")
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
        COMPONENT_STATUS,
        ACTION_STATUS,
        PROPOSAL_STATUS,
        BROKER_EXPOSURE_STATUS,
        "broker_exposure_context_manual_review_required",
        "no_fresh_broker_read_performed",
        "qqq100_displacement_approved",
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
            failures.append(f"flag must default false: {flag}")
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
        component = generate_vol_targeted_growth_seed_change_component_sleeve_review(root)
        action = generate_vol_targeted_growth_seed_change_action_preview_design(root)
        proposal = generate_vol_targeted_growth_seed_change_proposal_document(root)
        broker = generate_vol_targeted_growth_seed_change_broker_exposure_review(root)
        expected = [
            (component, "final_component_sleeve_status", COMPONENT_STATUS, "component_sleeve_review_only"),
            (action, "final_action_preview_design_status", ACTION_STATUS, "action_preview_design_only"),
            (proposal, "final_proposal_document_status", PROPOSAL_STATUS, "proposal_document_draft_only"),
            (broker, "final_broker_exposure_status", BROKER_EXPOSURE_STATUS, "broker_exposure_review_only"),
        ]
        for result, key, status, true_flag in expected:
            if summary_value(result.summary_rows, key) != status:
                failures.append(f"fixture did not produce expected status: {key}")
            for row in result.summary_rows + result.review_rows + result.evidence_rows + result.blocker_rows:
                verify_row_flags(row, true_flag, failures)
        if summary_value(proposal.summary_rows, "largest_blocker") != "proposal_document_draft_only_broker_exposure_context_still_manual_review":
            failures.append("proposal document must keep broker exposure as a blocker")
        if summary_value(broker.summary_rows, "largest_blocker") != "broker_exposure_review_present_but_seed_change_still_not_approved":
            failures.append("broker exposure review must not approve seed change")
        show_checks = [
            (show_vol_targeted_growth_seed_change_component_sleeve_review, COMPONENT_STATUS),
            (show_vol_targeted_growth_seed_change_action_preview_design, ACTION_STATUS),
            (show_vol_targeted_growth_seed_change_proposal_document, PROPOSAL_STATUS),
            (show_vol_targeted_growth_seed_change_broker_exposure_review, BROKER_EXPOSURE_STATUS),
        ]
        for show_func, status in show_checks:
            code, lines = show_func(root)
            if code != 0 or status not in "\n".join(lines):
                failures.append(f"show command did not display status: {status}")


def verify_row_flags(row: dict[str, object], true_flag: str, failures: list[str]) -> None:
    for flag in FALSE_FLAGS:
        if flag == "proposal_document_draft_saved":
            continue
        if str(row.get(flag, "")).lower() != "false":
            failures.append(f"expected false flag {flag}")
            return
    for flag in TRUE_FLAGS + [true_flag]:
        if str(row.get(flag, "")).lower() != "true":
            failures.append(f"expected true flag {flag}")
            return


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    for path in [
        "vol_targeted_growth_proposal_preview_summary.csv",
        "vol_targeted_growth_candidate_discussion_summary.csv",
        "vol_targeted_growth_gate_review_summary.csv",
        "vol_targeted_growth_portfolio_risk_review_summary.csv",
        "vol_targeted_growth_seed_change_evidence_summary.csv",
        "vol_targeted_growth_seed_change_risk_reward_summary.csv",
        "vol_targeted_growth_seed_change_drawdown_stress_summary.csv",
        "vol_targeted_growth_seed_change_cost_turnover_summary.csv",
        "vol_targeted_growth_seed_change_split_stability_summary.csv",
        "qqq100_followup_policy_summary.csv",
        "vol_targeted_growth_broker_position_comparison_summary.csv",
    ]:
        write_csv(data / path, ["summary_name", "summary_value"], [{"summary_name": "fixture", "summary_value": "present"}])
    write_csv(
        data / "vol_targeted_growth_broker_position_comparison_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "final_comparison_status", "summary_value": "vol_targeted_growth_broker_position_comparison_completed_readonly_manual_review_required"},
            {"summary_name": "broker_position_read_status", "summary_value": "paper_positions_read_readonly"},
        ],
    )


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
