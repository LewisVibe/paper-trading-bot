from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (  # noqa: E402
    ACTION_PACK_OUTPUT_FILES,
    ACTION_PACK_STATUS,
    ALLOCATION_POLICY_OUTPUT_FILES,
    ALLOCATION_POLICY_STATUS,
    CANDIDATE_APPROVAL_OUTPUT_FILES,
    CANDIDATE_APPROVAL_STATUS,
    GATE_OUTPUT_FILES,
    GATE_STATUS,
    ORDER_TICKET_BOUNDARY_OUTPUT_FILES,
    ORDER_TICKET_BOUNDARY_STATUS,
    RECONCILIATION_OUTPUT_FILES,
    RECONCILIATION_STATUS,
    REPORT_COLUMNS,
    SAFETY_FLAGS,
    TARGET_POSITION_PLAN_OUTPUT_FILES,
    TARGET_POSITION_PLAN_STATUS,
    generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy,
    generate_vol_targeted_growth_broker_comparison_reconciliation,
    generate_vol_targeted_growth_non_executable_target_position_plan,
    generate_vol_targeted_growth_order_ticket_boundary_design,
    generate_vol_targeted_growth_paper_live_action_preview_pack,
    generate_vol_targeted_growth_paper_live_candidate_approval_record,
    generate_vol_targeted_growth_paper_live_manual_approval_gate,
    show_vol_targeted_growth_allocation_cap_sleeve_mapping_policy,
    show_vol_targeted_growth_broker_comparison_reconciliation,
    show_vol_targeted_growth_non_executable_target_position_plan,
    show_vol_targeted_growth_order_ticket_boundary_design,
    show_vol_targeted_growth_paper_live_action_preview_pack,
    show_vol_targeted_growth_paper_live_candidate_approval_record,
    show_vol_targeted_growth_paper_live_manual_approval_gate,
)


COMMANDS = [
    "--vol-targeted-growth-paper-live-manual-approval-gate",
    "--show-vol-targeted-growth-paper-live-manual-approval-gate",
    "--vol-targeted-growth-paper-live-action-preview-pack",
    "--show-vol-targeted-growth-paper-live-action-preview-pack",
    "--vol-targeted-growth-broker-comparison-reconciliation",
    "--show-vol-targeted-growth-broker-comparison-reconciliation",
    "--vol-targeted-growth-paper-live-candidate-approval-record",
    "--show-vol-targeted-growth-paper-live-candidate-approval-record",
    "--vol-targeted-growth-allocation-cap-sleeve-mapping-policy",
    "--show-vol-targeted-growth-allocation-cap-sleeve-mapping-policy",
    "--vol-targeted-growth-non-executable-target-position-plan",
    "--show-vol-targeted-growth-non-executable-target-position-plan",
    "--vol-targeted-growth-order-ticket-boundary-design",
    "--show-vol-targeted-growth-order-ticket-boundary-design",
]

FALSE_FLAGS = [
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
    "order_instructions_created",
    "executable_target_positions_created",
    "portfolio_execution_wired",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "paper_live_candidate_approved",
    "allocation_cap_approved",
    "sleeve_mapping_approved",
    "target_position_design_approved",
    "manual_paper_live_approval_recorded",
    "order_ticket_design_approved",
    "executable_order_ticket_created",
    "action_preview_approved",
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
    "preview_only",
    "never_schedule_order_capable_commands",
]

FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient",
    "GetOrdersRequest",
    "get_all_positions",
    "submit_order",
    "MarketOrderRequest",
    "cancel_order",
    "replace_order",
    "insert_trade_log",
    "send_discord",
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

FORBIDDEN_COLUMNS = {
    "side",
    "quantity",
    "order_quantity",
    "order_qty",
    "order_side",
    "order_type",
    "account_id",
    "api_key",
    "webhook",
    "secret",
    "token",
    "order_id",
}


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_paper_live_checkpoints.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_output_schema(failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth paper-live checkpoint verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth paper-live checkpoint verification passed.")
    print("Verified paper-live checkpoints, candidate-discussion approval, and allocation/sleeve policy remain report-only with false execution approvals.")
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
            failures.append(f"bot.py missing early route for {command}")
        elif early_index > load_config_index:
            failures.append(f"early route for {command} appears after config loading")


def verify_outputs_ignored(failures: list[str]) -> None:
    for mapping in [
        GATE_OUTPUT_FILES,
        ACTION_PACK_OUTPUT_FILES,
        RECONCILIATION_OUTPUT_FILES,
        CANDIDATE_APPROVAL_OUTPUT_FILES,
        ALLOCATION_POLICY_OUTPUT_FILES,
        TARGET_POSITION_PLAN_OUTPUT_FILES,
        ORDER_TICKET_BOUNDARY_OUTPUT_FILES,
    ]:
        for path in mapping.values():
            normalized = str(path).replace("\\", "/")
            result = subprocess.run(["git", "check-ignore", normalized], cwd=ROOT, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                failures.append(f"generated output is not ignored by git: {normalized}")


def verify_source_boundaries(module_source: str, failures: list[str]) -> None:
    required = [
        GATE_STATUS,
        ACTION_PACK_STATUS,
        RECONCILIATION_STATUS,
        CANDIDATE_APPROVAL_STATUS,
        ALLOCATION_POLICY_STATUS,
        TARGET_POSITION_PLAN_STATUS,
        ORDER_TICKET_BOUNDARY_STATUS,
        "manual_paper_live_approval_recorded",
        "paper_live_candidate_discussion_approved",
        "allocation_cap_approved",
        "sleeve_mapping_approved",
        "target_position_design_approved",
        "executable_target_positions_created",
        "order_ticket_design_approved",
        "executable_order_ticket_created",
        "default_total_paper_allocation_cap=0_until_separate_execution_design",
        "blocked_research_only_unmapped",
        "QQQ_review_only_no_order_quantity",
        "QQQ_review_only_no_side_no_quantity",
        "order_ticket_design_not_approved",
        "executable_order_ticket_design_not_approved",
        "broker_positions_read_now",
        "order_instructions_created",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "never_schedule_order_capable_commands",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")

    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in module_source:
            failures.append(f"module must not contain forbidden token: {token}")

    for flag in FALSE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not False:
            failures.append(f"safety flag must be false: {flag}")
    for flag in TRUE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not True:
            failures.append(f"safety flag must be true: {flag}")

    for show_name in [
        "show_vol_targeted_growth_paper_live_manual_approval_gate",
        "show_vol_targeted_growth_paper_live_action_preview_pack",
        "show_vol_targeted_growth_broker_comparison_reconciliation",
        "show_vol_targeted_growth_paper_live_candidate_approval_record",
        "show_vol_targeted_growth_allocation_cap_sleeve_mapping_policy",
        "show_vol_targeted_growth_non_executable_target_position_plan",
        "show_vol_targeted_growth_order_ticket_boundary_design",
    ]:
        show_body = source_slice(module_source, f"def {show_name}", "\n\ndef ")
        if "write_rows" in show_body or "generate_vol_targeted" in show_body:
            failures.append(f"{show_name} must display saved outputs only and must not regenerate reports")


def verify_output_schema(failures: list[str]) -> None:
    forbidden = FORBIDDEN_COLUMNS.intersection(REPORT_COLUMNS)
    if forbidden:
        failures.append(f"report schema contains forbidden order/security columns: {sorted(forbidden)}")
    for required in ["checkpoint_name", "status", "risk_level", "execution_approved", "paper_execution_approved", "scheduling_approved"]:
        if required not in REPORT_COLUMNS:
            failures.append(f"report schema missing required column: {required}")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)

        gate = generate_vol_targeted_growth_paper_live_manual_approval_gate(root)
        action = generate_vol_targeted_growth_paper_live_action_preview_pack(root)
        reconciliation = generate_vol_targeted_growth_broker_comparison_reconciliation(root)
        approval = generate_vol_targeted_growth_paper_live_candidate_approval_record(root)
        allocation = generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy(root)
        target_plan = generate_vol_targeted_growth_non_executable_target_position_plan(root)
        order_boundary = generate_vol_targeted_growth_order_ticket_boundary_design(root)

        if summary_value(gate.summary_rows, "final_manual_gate_status") != GATE_STATUS:
            failures.append("manual gate fixture did not produce expected status")
        if summary_value(action.summary_rows, "final_action_preview_pack_status") != ACTION_PACK_STATUS:
            failures.append("action-preview pack fixture did not produce expected status")
        if summary_value(reconciliation.summary_rows, "final_reconciliation_status") != RECONCILIATION_STATUS:
            failures.append("broker reconciliation fixture did not produce expected status")
        if summary_value(approval.summary_rows, "final_candidate_approval_status") != CANDIDATE_APPROVAL_STATUS:
            failures.append("candidate approval fixture did not produce expected status")
        if summary_value(approval.summary_rows, "paper_live_candidate_discussion_approved") != "True":
            failures.append("candidate approval should approve discussion only")
        if summary_value(approval.summary_rows, "paper_live_candidate_approved") != "False":
            failures.append("candidate approval must not approve paper-live candidacy")
        if summary_value(allocation.summary_rows, "final_allocation_policy_status") != ALLOCATION_POLICY_STATUS:
            failures.append("allocation policy fixture did not produce expected status")
        if summary_value(allocation.summary_rows, "allocation_cap_approved") != "False":
            failures.append("allocation policy must not approve allocation cap")
        if summary_value(allocation.summary_rows, "sleeve_mapping_approved") != "False":
            failures.append("allocation policy must not approve sleeve mapping")
        if summary_value(allocation.summary_rows, "target_position_design_approved") != "False":
            failures.append("allocation policy must not approve target-position design")
        if summary_value(target_plan.summary_rows, "final_target_position_plan_status") != TARGET_POSITION_PLAN_STATUS:
            failures.append("target-position plan fixture did not produce expected status")
        if summary_value(target_plan.summary_rows, "paper_live_candidate_discussion_approved") != "True":
            failures.append("target-position plan should preserve discussion-only approval")
        if summary_value(target_plan.summary_rows, "target_position_design_approved") != "False":
            failures.append("target-position plan must not approve target-position design")
        if summary_value(target_plan.summary_rows, "executable_target_positions_created") != "False":
            failures.append("target-position plan must not create executable target positions")
        if summary_value(target_plan.summary_rows, "order_instructions_created") != "False":
            failures.append("target-position plan must not create order instructions")
        if summary_value(target_plan.summary_rows, "qqq100_review_context") != "QQQ_review_only_no_order_quantity":
            failures.append("target-position plan must keep QQQ as review-only with no order quantity")
        if summary_value(order_boundary.summary_rows, "final_order_ticket_boundary_status") != ORDER_TICKET_BOUNDARY_STATUS:
            failures.append("order-ticket boundary fixture did not produce expected status")
        if summary_value(order_boundary.summary_rows, "paper_live_candidate_discussion_approved") != "True":
            failures.append("order-ticket boundary should preserve discussion-only approval")
        if summary_value(order_boundary.summary_rows, "order_ticket_design_approved") != "False":
            failures.append("order-ticket boundary must not approve order-ticket design")
        if summary_value(order_boundary.summary_rows, "executable_order_ticket_created") != "False":
            failures.append("order-ticket boundary must not create an executable order ticket")
        if summary_value(order_boundary.summary_rows, "order_instructions_created") != "False":
            failures.append("order-ticket boundary must not create order instructions")
        if summary_value(order_boundary.summary_rows, "qqq100_order_ticket_context") != "QQQ_review_only_no_side_no_quantity":
            failures.append("order-ticket boundary must keep QQQ as review-only with no side or quantity")

        for result in [gate, action, reconciliation, approval, allocation, target_plan, order_boundary]:
            for collection in [result.report_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
                for row in collection:
                    for flag in FALSE_FLAGS:
                        if str(row.get(flag, "")).lower() != "false":
                            failures.append(f"expected false flag {flag} in output row")
                            return
                    for flag in TRUE_FLAGS:
                        if str(row.get(flag, "")).lower() != "true":
                            failures.append(f"expected true flag {flag} in output row")
                            return

        displays = [
            show_vol_targeted_growth_paper_live_manual_approval_gate(root),
            show_vol_targeted_growth_paper_live_action_preview_pack(root),
            show_vol_targeted_growth_broker_comparison_reconciliation(root),
            show_vol_targeted_growth_paper_live_candidate_approval_record(root),
            show_vol_targeted_growth_allocation_cap_sleeve_mapping_policy(root),
            show_vol_targeted_growth_non_executable_target_position_plan(root),
            show_vol_targeted_growth_order_ticket_boundary_design(root),
        ]
        for code, lines in displays:
            display = "\n".join(lines)
            if code != 0:
                failures.append(f"show command should succeed after generation, got {code}")
            for token in ["execution_approved=false", "paper_execution_approved=false", "scheduling_approved=false"]:
                if token not in display:
                    failures.append(f"display missing safety token: {token}")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_csv(
        data / "vol_targeted_growth_active_seed_readiness_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "final_active_seed_readiness_status", "summary_value": "vol_targeted_growth_active_seed_monitoring_ready_manual_review_required"},
            {"summary_name": "active_seed", "summary_value": "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"},
            {"summary_name": "active_ticker", "summary_value": "MULTI_SLEEVE"},
        ],
    )
    write_csv(
        data / "vol_targeted_growth_action_preview_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_action_preview_status", "summary_value": "vol_targeted_growth_action_preview_created_saved_output_only"}],
    )
    write_csv(
        data / "vol_targeted_growth_action_preview.csv",
        ["sleeve_name", "target_weight", "manual_review_label"],
        [
            {"sleeve_name": "qqq100_core_trend_sleeve", "target_weight": "0.70", "manual_review_label": "current_exposure_not_read_manual_review_required"},
            {"sleeve_name": "high_growth_stock_research_sleeve", "target_weight": "0.20", "manual_review_label": "current_exposure_not_read_manual_review_required"},
        ],
    )
    write_csv(
        data / "vol_targeted_growth_action_preview_quality_gate_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_quality_gate_status", "summary_value": "vol_targeted_growth_action_preview_quality_gate_manual_review_required"}],
    )
    write_csv(
        data / "vol_targeted_growth_broker_position_comparison_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_comparison_status", "summary_value": "vol_targeted_growth_broker_position_comparison_completed_readonly_manual_review_required"}],
    )
    write_csv(
        data / "vol_targeted_growth_broker_position_comparison.csv",
        ["sleeve_name", "broker_position_status", "comparison_status"],
        [{"sleeve_name": "qqq100_core_trend_sleeve", "broker_position_status": "paper_position_present", "comparison_status": "broker_position_context_available_manual_review_required"}],
    )
    write_csv(
        data / "vol_targeted_growth_post_comparison_decision_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_post_comparison_decision_status", "summary_value": "vol_targeted_growth_stricter_paper_live_discussion_gate_ready_manual_review_required"}],
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index < 0:
        return ""
    end_index = source.find(end, start_index + len(start))
    if end_index < 0:
        return source[start_index:]
    return source[start_index:end_index]


def summary_value(rows: list[dict[str, object]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
