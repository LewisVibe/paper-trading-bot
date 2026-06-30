from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "vol_targeted_growth_executable_ticket_closeout_candidate_reviews.py"
DASHBOARD_MODULE = ROOT / "trading_bot" / "research" / "paper_live_go_no_go_dashboard.py"

COMMANDS = [
    "--vol-targeted-growth-criteria-source-closeout-candidate-review",
    "--show-vol-targeted-growth-criteria-source-closeout-candidate-review",
    "--vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review",
    "--show-vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review",
    "--vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review",
    "--show-vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review",
    "--vol-targeted-growth-criteria-closeout-candidate-review-rollup",
    "--show-vol-targeted-growth-criteria-closeout-candidate-review-rollup",
]

SLUGS = [
    "criteria_source_closeout_candidate_review",
    "criteria_resolution_plan_closeout_candidate_review",
    "approval_criteria_not_approval_closeout_candidate_review",
    "criteria_closeout_candidate_review_rollup",
]

OUTPUTS = [
    f"data/vol_targeted_growth_executable_ticket_{slug}{suffix}.csv"
    for slug in SLUGS
    for suffix in ["", "_summary", "_blockers", "_evidence"]
]

REQUIRED_TOKENS = [
    "CLOSEOUT_CANDIDATE_READY_FOR_MANUAL_REVIEW",
    "CLOSEOUT_CANDIDATE_NOT_READY_STILL_OPEN",
    "CLOSEOUT_CANDIDATE_NOT_READY_NO_APPROVAL",
    "CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED",
    '"closeout_candidate_only": True',
    '"blockers_resolved": False',
    '"blockers_closed": False',
    '"approval_readiness_changed": False',
    '"approval_requested": False',
    '"approval_recorded": False',
    '"order_values_populated": False',
    '"order_instructions_created": False',
    '"executable_ticket_created": False',
    '"orders_submitted": False',
    '"execution_approved": False',
    '"paper_execution_approved": False',
    '"scheduling_approved": False',
]

FORBIDDEN_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    "LimitOrderRequest(",
    "submit_order(",
    "cancel_order(",
    "replace_order(",
    "get_all_positions(",
    "get_alpaca_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "config.json",
    "yf.",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)

    verify_commands(bot_source, failures)
    verify_module(module_source, failures)
    verify_outputs_ignored(failures)
    verify_fixture_output(failures)
    verify_dashboard_integration(failures)

    if failures:
        print("Volatility-targeted executable-ticket closeout-candidate reviews verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted executable-ticket closeout-candidate reviews verification passed.")
    print("Verified three closeout-candidate reviews, rollup, no blocker closure, false approvals, ignored outputs, and dashboard integration.")
    return 0


def verify_commands(bot_source: str, failures: list[str]) -> None:
    inventory_source = read_text(ROOT / "scripts" / "verify_command_inventory.py")
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command in bot.py: {command}")
        if command not in inventory_source:
            failures.append(f"missing command in inventory verifier: {command}")


def verify_module(module_source: str, failures: list[str]) -> None:
    if not MODULE.exists():
        failures.append("closeout-candidate reviews module is missing")
    for token in REQUIRED_TOKENS:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in module_source:
            failures.append(f"module contains forbidden token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(
            ["git", "check-ignore", output],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_fixture_output(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.vol_targeted_growth_executable_ticket_closeout_candidate_reviews import (  # noqa: PLC0415
        generate_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review,
        generate_vol_targeted_growth_criteria_closeout_candidate_review_rollup,
        generate_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review,
        generate_vol_targeted_growth_criteria_source_closeout_candidate_review,
        show_vol_targeted_growth_criteria_closeout_candidate_review_rollup,
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_summary(data / "vol_targeted_growth_executable_ticket_criteria_source_blocker_review_summary.csv", {"final_review_decision": "CRITERIA_SOURCE_BLOCKER_REVIEWED_NOT_CLOSED"})
        write_summary(data / "vol_targeted_growth_executable_ticket_criteria_resolution_plan_blocker_review_summary.csv", {"final_review_decision": "CRITERIA_RESOLUTION_PLAN_REVIEWED_STILL_OPEN"})
        write_summary(data / "vol_targeted_growth_executable_ticket_approval_criteria_not_approval_blocker_review_summary.csv", {"final_review_decision": "APPROVAL_CRITERIA_REVIEWED_APPROVAL_STILL_NOT_REQUESTED"})
        write_summary(data / "vol_targeted_growth_executable_ticket_criteria_blocker_specific_review_rollup_summary.csv", {"final_review_decision": "CRITERIA_BLOCKER_SPECIFIC_REVIEWS_CREATED_NONE_CLOSED"})
        write_summary(data / "paper_live_go_no_go_dashboard_summary.csv", {"final_go_no_go_decision": "NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY"})

        results = [
            generate_vol_targeted_growth_criteria_source_closeout_candidate_review(root),
            generate_vol_targeted_growth_criteria_resolution_plan_closeout_candidate_review(root),
            generate_vol_targeted_growth_approval_criteria_not_approval_closeout_candidate_review(root),
            generate_vol_targeted_growth_criteria_closeout_candidate_review_rollup(root),
        ]
        status_code, lines = show_vol_targeted_growth_criteria_closeout_candidate_review_rollup(root)

    output = "\n".join(line for result in results for line in result.summary_lines) + "\n" + "\n".join(lines)
    if status_code != 0:
        failures.append("closeout-candidate rollup display should return 0 after generation")
    for phrase in [
        "CLOSEOUT_CANDIDATE_READY_FOR_MANUAL_REVIEW",
        "CLOSEOUT_CANDIDATE_NOT_READY_STILL_OPEN",
        "CLOSEOUT_CANDIDATE_NOT_READY_NO_APPROVAL",
        "CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED",
        "candidate_ready_count=1",
        "not_ready_count=2",
        "blockers_resolved=false",
        "blockers_closed=false",
        "approval_requested=false",
        "approval_recorded=false",
        "order_values_populated=false",
        "executable_ticket_created=false",
        "execution_approved=false",
        "paper_execution_approved=false",
        "scheduling_approved=false",
    ]:
        if phrase not in output:
            failures.append(f"fixture output missing phrase: {phrase}")


def verify_dashboard_integration(failures: list[str]) -> None:
    source = read_text(DASHBOARD_MODULE)
    for phrase in [
        "vol_ticket_closeout_candidate_review_rollup",
        "vol_targeted_growth_executable_ticket_criteria_closeout_candidate_review_rollup_summary.csv",
        "vol_ticket_closeout_candidate_review_rollup_status",
        "vol_ticket_closeout_candidate_review_rollup_decision",
        "executable_ticket_closeout_candidate_reviews_do_not_close_blockers",
    ]:
        if phrase not in source:
            failures.append(f"go/no-go dashboard missing closeout-candidate review integration phrase: {phrase}")


def write_summary(path: Path, values: dict[str, str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
