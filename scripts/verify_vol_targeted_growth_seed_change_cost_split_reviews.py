from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_seed_change_cost_turnover_review import (  # noqa: E402
    FINAL_STATUS as COST_FINAL_STATUS,
    OUTPUT_FILES as COST_OUTPUT_FILES,
    SAFETY_FLAGS as COST_SAFETY_FLAGS,
    generate_vol_targeted_growth_seed_change_cost_turnover_review,
    show_vol_targeted_growth_seed_change_cost_turnover_review,
)
from trading_bot.research.vol_targeted_growth_seed_change_split_stability_review import (  # noqa: E402
    FINAL_STATUS as SPLIT_FINAL_STATUS,
    OUTPUT_FILES as SPLIT_OUTPUT_FILES,
    SAFETY_FLAGS as SPLIT_SAFETY_FLAGS,
    generate_vol_targeted_growth_seed_change_split_stability_review,
    show_vol_targeted_growth_seed_change_split_stability_review,
)


COMMANDS = [
    "--vol-targeted-growth-seed-change-cost-turnover-review",
    "--show-vol-targeted-growth-seed-change-cost-turnover-review",
    "--vol-targeted-growth-seed-change-split-stability-review",
    "--show-vol-targeted-growth-seed-change-split-stability-review",
]
FALSE_FLAGS = [
    "seed_changed",
    "seed_change_proposal_created",
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
BASE_TRUE_FLAGS = [
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
    cost_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_cost_turnover_review.py")
    split_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_split_stability_review.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(cost_source, COST_SAFETY_FLAGS, ["cost_turnover_review_only"], COST_FINAL_STATUS, failures)
    verify_source(split_source, SPLIT_SAFETY_FLAGS, ["split_stability_review_only"], SPLIT_FINAL_STATUS, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth seed-change cost/split reviews verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth seed-change cost/split reviews verification passed.")
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
    for path in list(COST_OUTPUT_FILES.values()) + list(SPLIT_OUTPUT_FILES.values()):
        output = str(path).replace("\\", "/")
        result = subprocess.run(["git", "check-ignore", output], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"generated output is not ignored: {output}")


def verify_source(source: str, flags: dict[str, bool], extra_true: list[str], final_status: str, failures: list[str]) -> None:
    for token in [
        final_status,
        "qqq100_displacement_approved",
        "seed_change_proposal_created",
        "order_instructions_created",
        "execution_approved",
        "scheduling_approved",
    ]:
        if token not in source:
            failures.append(f"missing required token: {token}")
    for flag in FALSE_FLAGS:
        if flags.get(flag) is not False:
            failures.append(f"flag must be false: {flag}")
    for flag in BASE_TRUE_FLAGS + extra_true:
        if flags.get(flag) is not True:
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
        cost = generate_vol_targeted_growth_seed_change_cost_turnover_review(root)
        split = generate_vol_targeted_growth_seed_change_split_stability_review(root)
        if summary_value(cost.summary_rows, "final_cost_turnover_status") != COST_FINAL_STATUS:
            failures.append("cost/turnover fixture did not produce expected status")
        if summary_value(cost.summary_rows, "cost_turnover_review_status") != "cost_turnover_exact_metrics_missing_manual_review_required":
            failures.append("cost/turnover review should disclose exact metric gap")
        if summary_value(split.summary_rows, "final_split_stability_status") != SPLIT_FINAL_STATUS:
            failures.append("split fixture did not produce expected status")
        if summary_value(split.summary_rows, "saved_split_status") != "split_stability_supportive_manual_review_required":
            failures.append("split review should preserve saved supportive manual-review label")
        for row in cost.summary_rows + cost.review_rows + cost.evidence_rows + cost.blocker_rows:
            verify_row_flags(row, COST_SAFETY_FLAGS, ["cost_turnover_review_only"], failures)
        for row in split.summary_rows + split.review_rows + split.evidence_rows + split.blocker_rows:
            verify_row_flags(row, SPLIT_SAFETY_FLAGS, ["split_stability_review_only"], failures)
        code, lines = show_vol_targeted_growth_seed_change_cost_turnover_review(root)
        if code != 0 or COST_FINAL_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved cost/turnover review")
        code, lines = show_vol_targeted_growth_seed_change_split_stability_review(root)
        if code != 0 or SPLIT_FINAL_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved split-stability review")


def verify_row_flags(row: dict[str, object], flags: dict[str, bool], extra_true: list[str], failures: list[str]) -> None:
    for flag in FALSE_FLAGS:
        if str(row.get(flag, "")).lower() != "false":
            failures.append(f"expected false flag {flag}")
            return
    for flag in BASE_TRUE_FLAGS + extra_true:
        if str(row.get(flag, "")).lower() != "true":
            failures.append(f"expected true flag {flag}")
            return


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_csv(
        data / "vol_targeted_growth_robustness_checkpoint_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "final_robustness_status", "summary_value": "vol_targeted_growth_robustness_manual_review_required"},
            {"summary_name": "parameter_sensitivity_status", "summary_value": "parameter_neighborhood_fragile_manual_review_required"},
            {"summary_name": "split_stability_status", "summary_value": "split_stability_supportive_manual_review_required"},
        ],
    )
    write_csv(
        data / "vol_targeted_growth_robustness_checkpoint.csv",
        ["check_name", "status", "candidate_metrics"],
        [{"check_name": "split_stability_review", "status": "split_stability_supportive_manual_review_required", "candidate_metrics": "in_sample_cagr=12.712; out_of_sample_cagr=29.0988; out_of_sample_sharpe=1.7564; out_of_sample_calmar=2.6559"}],
    )
    write_csv(
        data / "vol_targeted_growth_nearby_variants_summary.csv",
        ["summary_name", "summary_value"],
        [
            {"summary_name": "preferred_candidate", "summary_value": "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x: CAGR=19.0011; Sharpe=1.2861; MaxDD=-18.1016; Calmar=1.0497"},
            {"summary_name": "variant_count", "summary_value": "12"},
            {"summary_name": "variant_interpretation", "summary_value": "preferred_15_20_retains_best_calmar_and_sharpe_but_requires_manual_review"},
        ],
    )
    write_csv(data / "vol_targeted_growth_nearby_variants_review.csv", ["candidate_name"], [{"candidate_name": "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"}])
    write_csv(data / "vol_targeted_growth_manual_review_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "multi_sleeve_candidate", "summary_value": "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"}])
    write_csv(data / "vol_targeted_growth_seed_change_evidence_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "final_evidence_pack_status", "summary_value": "vol_targeted_growth_seed_change_evidence_pack_incomplete_manual_review_required"}])


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
