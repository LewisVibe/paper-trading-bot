from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_paper_live_checkpoints import (  # noqa: E402
    EXECUTION_BLOCKER_ROLLUP_STATUS,
    generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy,
    generate_vol_targeted_growth_broker_comparison_reconciliation,
    generate_vol_targeted_growth_executable_ticket_prerequisites_review,
    generate_vol_targeted_growth_non_executable_target_position_plan,
    generate_vol_targeted_growth_order_ticket_boundary_design,
    generate_vol_targeted_growth_paper_live_action_preview_pack,
    generate_vol_targeted_growth_paper_live_candidate_approval_record,
    generate_vol_targeted_growth_paper_live_execution_blocker_rollup,
    generate_vol_targeted_growth_paper_live_manual_approval_gate,
)
from trading_bot.research.vps_daily_monitoring_summary import build_vps_daily_monitoring_summary_lines  # noqa: E402


FALSE_SUMMARY_FLAGS = [
    "paper_live_candidate_approved",
    "executable_ticket_prerequisites_met",
    "executable_ticket_design_allowed",
    "order_ticket_design_approved",
    "executable_order_ticket_created",
    "order_instructions_created",
    "execution_blocker_rollup_cleared",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
]


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)

        generate_vol_targeted_growth_paper_live_manual_approval_gate(root)
        generate_vol_targeted_growth_paper_live_action_preview_pack(root)
        generate_vol_targeted_growth_broker_comparison_reconciliation(root)
        generate_vol_targeted_growth_paper_live_candidate_approval_record(root)
        generate_vol_targeted_growth_allocation_cap_sleeve_mapping_policy(root)
        generate_vol_targeted_growth_non_executable_target_position_plan(root)
        generate_vol_targeted_growth_order_ticket_boundary_design(root)
        generate_vol_targeted_growth_executable_ticket_prerequisites_review(root)
        rollup = generate_vol_targeted_growth_paper_live_execution_blocker_rollup(root)

        verify_rollup(rollup.summary_rows, failures)
        verify_daily_summary(root, failures)

    if failures:
        print("Volatility-targeted paper-live execution blocker chain verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted paper-live execution blocker chain verification passed.")
    print("Verified the saved-output paper-live chain rolls up blockers and daily monitoring surfaces the blocked/non-executable state.")
    return 0


def verify_rollup(summary_rows: list[dict[str, object]], failures: list[str]) -> None:
    if summary_value(summary_rows, "final_execution_blocker_rollup_status") != EXECUTION_BLOCKER_ROLLUP_STATUS:
        failures.append("rollup did not produce the expected final status")
    if summary_value(summary_rows, "largest_blocker") != "execution_not_approved":
        failures.append("rollup did not preserve execution_not_approved as the final largest blocker")
    if summary_value(summary_rows, "criteria_source_reviewed_closed") != "True":
        failures.append("rollup should recognise criteria_source_reviewed as closed from saved evidence")
    if summary_value(summary_rows, "criteria_resolution_plan_open_closed") != "True":
        failures.append("rollup should recognise criteria_resolution_plan_open as closed from saved evidence")
    if summary_value(summary_rows, "approval_criteria_not_approval_closed") != "True":
        failures.append("rollup should recognise approval_criteria_not_approval as closed from saved evidence")
    if summary_value(summary_rows, "ticket_values_not_approved_closed") != "True":
        failures.append("rollup should recognise ticket_values_not_approved as closed from saved evidence")
    if summary_value(summary_rows, "executable_ticket_prerequisites_not_met_closed") != "True":
        failures.append("rollup should recognise executable_ticket_prerequisites_not_met as closed from saved evidence")
    if summary_value(summary_rows, "closed_blocker_count") != "5":
        failures.append("rollup should count five closed blockers from saved evidence")
    remaining = summary_value(summary_rows, "remaining_known_blockers_after_closeout")
    if remaining != "none":
        failures.append("rollup should show no remaining checklist blockers after final closeout")
    for flag in FALSE_SUMMARY_FLAGS:
        if summary_or_flag_value(summary_rows, flag) != "False":
            failures.append(f"rollup summary flag must be False: {flag}")


def verify_daily_summary(root: Path, failures: list[str]) -> None:
    output = "\n".join(build_vps_daily_monitoring_summary_lines(root))
    required = [
        "Volatility paper-live execution blocker rollup:",
        "vol_execution_blocker_rollup_present: True",
        f"final_execution_blocker_rollup_status: {EXECUTION_BLOCKER_ROLLUP_STATUS}",
        "execution_blocker_count:",
        "closed_blocker_count: 5",
        "criteria_source_reviewed_closed: True",
        "criteria_resolution_plan_open_closed: True",
        "approval_criteria_not_approval_closed: True",
        "ticket_values_not_approved_closed: True",
        "executable_ticket_prerequisites_not_met_closed: True",
        "remaining_known_blockers_after_closeout: none",
        "largest_blocker: execution_not_approved",
        "executable_ticket_prerequisites_met: False",
        "executable_ticket_design_allowed: False",
        "order_instructions_created: False",
        "execution_approved: False",
        "paper_execution_approved: False",
        "scheduling_approved: False",
        "vol_execution_blocker_rollup_warning: monitor only;",
    ]
    for phrase in required:
        if phrase not in output:
            failures.append(f"daily summary missing rollup phrase: {phrase}")


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
            {"summary_name": "previous_seed", "summary_value": "qqq_100_trend_gate"},
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
        [{"sleeve_name": "qqq100_core_trend_sleeve", "target_weight": "0.70", "manual_review_label": "current_exposure_not_read_manual_review_required"}],
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
    write_csv(
        data / "vol_targeted_growth_executable_ticket_criteria_source_closeout_record_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "final_closeout_record_decision", "summary_value": "CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY"},
            {"summary_name": "closed_blocker", "summary_value": "criteria_source_reviewed"},
            {
                "summary_name": "remaining_known_blockers",
                "summary_value": "criteria_resolution_plan_open;approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met",
            },
        ],
    )
    write_csv(
        data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_closeout_record_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "final_closeout_record_decision", "summary_value": "CRITERIA_RESOLUTION_PLAN_OPEN_BLOCKER_CLOSED_ONLY"},
            {"summary_name": "closed_blocker", "summary_value": "criteria_resolution_plan_open"},
            {
                "summary_name": "remaining_known_blockers",
                "summary_value": "approval_criteria_not_approval;ticket_values_not_approved;executable_ticket_prerequisites_not_met",
            },
        ],
    )
    write_csv(
        data / "vol_targeted_growth_executable_ticket_approval_criteria_closeout_record_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "final_closeout_record_decision", "summary_value": "APPROVAL_CRITERIA_NOT_APPROVAL_BLOCKER_CLOSED_ONLY"},
            {"summary_name": "closed_blocker", "summary_value": "approval_criteria_not_approval"},
            {"summary_name": "remaining_known_blockers", "summary_value": "ticket_values_not_approved;executable_ticket_prerequisites_not_met"},
        ],
    )
    write_csv(
        data / "vol_targeted_growth_final_ticket_blockers_closeout_record_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "final_closeout_record_decision", "summary_value": "FINAL_TICKET_BLOCKERS_CLOSED_NO_EXECUTION_APPROVAL"},
            {"summary_name": "closed_blocker", "summary_value": "ticket_values_not_approved;executable_ticket_prerequisites_not_met"},
            {"summary_name": "remaining_known_blockers", "summary_value": "none"},
        ],
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summary_value(rows: list[dict[str, object]], key: str) -> str:
    for row in rows:
        if row.get("summary_name") == key:
            return str(row.get("summary_value", "")).strip()
    return ""


def summary_or_flag_value(rows: list[dict[str, object]], key: str) -> str:
    value = summary_value(rows, key)
    if value:
        return value
    for row in rows:
        if key in row:
            return str(row.get(key, "")).strip()
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
