from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_robustness_checkpoint import (  # noqa: E402
    FINAL_STATUS_REVIEW,
    OUTPUT_FILES,
    PREFERRED_CANDIDATE,
    PREVIEW_READY_STATUS,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_robustness_checkpoint,
    show_vol_targeted_growth_robustness_checkpoint,
)


EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_robustness_checkpoint.csv",
    "data/vol_targeted_growth_robustness_checkpoint_summary.csv",
    "data/vol_targeted_growth_robustness_checkpoint_evidence.csv",
    "data/vol_targeted_growth_robustness_checkpoint_blockers.csv",
]

COMMANDS = [
    "--vol-targeted-growth-robustness-checkpoint",
    "--show-vol-targeted-growth-robustness-checkpoint",
]

FALSE_FLAGS = [
    "market_data_refreshed",
    "yfinance_called",
    "alpaca_called",
    "live_positions_read",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "order_instructions_created",
    "action_preview_created",
    "portfolio_execution_wired",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "preview_candidate_approved",
    "preview_implementation_approved",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "high_growth_promotion_approved",
    "crypto_execution_approved",
]

TRUE_FLAGS = ["research_only", "report_only", "saved_output_only", "manual_review_only", "preview_only", "never_schedule_order_capable_commands"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_robustness_checkpoint.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth robustness checkpoint verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth robustness checkpoint verification passed.")
    print("Verified saved-output robustness, parameter/split/drawdown checks, false approvals, and no broker/order/config/scheduling paths.")
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
            failures.append(f"bot.py missing early report-only route for {command}")
        elif early_index > load_config_index:
            failures.append(f"early report-only route for {command} appears after config loading")
    for token in ["generate_vol_targeted_growth_robustness_checkpoint", "show_vol_targeted_growth_robustness_checkpoint"]:
        if token not in bot_source:
            failures.append(f"bot.py missing function token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        result = subprocess.run(["git", "check-ignore", expected], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"generated output is not ignored by git: {expected}")


def verify_source_boundaries(module_source: str, failures: list[str]) -> None:
    required = [
        PREFERRED_CANDIDATE,
        "parameter_neighborhood_supportive_manual_review_required",
        "split_stability_supportive_manual_review_required",
        "drawdown_tradeoff_supportive_lower_drawdown_manual_review_required",
        PREVIEW_READY_STATUS,
        "manual_review_vol_targeted_robustness_then_decide_preview_design_or_more_research",
        "preview_candidate_approved",
        "preview_implementation_approved",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "never_schedule_order_capable_commands",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")

    for flag in FALSE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not False:
            failures.append(f"safety flag must be false: {flag}")
    for flag in TRUE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not True:
            failures.append(f"safety flag must be true: {flag}")

    forbidden = [
        "TradingClient",
        "GetOrdersRequest",
        "get_all_positions",
        "submit_order",
        "MarketOrderRequest",
        "cancel_order",
        "replace_order",
        "insert_trade_log",
        "send_discord_alert",
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
    for token in forbidden:
        if token in module_source:
            failures.append(f"module must not contain forbidden token: {token}")

    show_body = source_slice(module_source, "def show_vol_targeted_growth_robustness_checkpoint", "def build_checkpoint_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_robustness_checkpoint" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_sprint_fixture(data)
        write_csv(
            data / "vol_targeted_growth_candidate_summary.csv",
            ["summary_name", "summary_value"],
            [{"summary_name": "final_research_status", "summary_value": "vol_targeted_growth_research_two_or_more_strong_candidates_found"}],
        )
        write_csv(
            data / "vol_targeted_growth_manual_review_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "final_manual_review_status", "summary_value": "vol_targeted_growth_manual_review_required"},
                {"summary_name": "preferred_research_path", "summary_value": PREFERRED_CANDIDATE},
            ],
        )
        write_csv(data / "vol_targeted_growth_rejected_candidates.csv", ["candidate_name", "rejection_status"], [{"candidate_name": "high_growth_top1_target_vol_25_win_20_cap_1x", "rejection_status": "vol_targeted_growth_fragile_or_low_return_rejected"}])
        write_csv(data / "vol_targeted_growth_robustness_audit.csv", ["audit_name", "audit_value"], [{"audit_name": "hidden_leverage_policy", "audit_value": "passed"}])
        write_csv(data / "vol_targeted_growth_parameter_sensitivity.csv", ["candidate_family", "candidate_count", "best_candidate", "strong_candidate_count", "fragile_candidate_count"], [{"candidate_family": "multi_sleeve_vol_targeted_growth", "candidate_count": "12", "best_candidate": PREFERRED_CANDIDATE, "strong_candidate_count": "2", "fragile_candidate_count": "6"}])

        result = generate_vol_targeted_growth_robustness_checkpoint(root)
        status = summary_value(result.summary_rows, "final_robustness_status")
        if status != FINAL_STATUS_REVIEW:
            failures.append(f"fixture should produce robustness manual-review status, got {status}")
        if summary_value(result.summary_rows, "parameter_sensitivity_status") != "parameter_neighborhood_supportive_manual_review_required":
            failures.append("fixture should mark parameter neighborhood supportive/manual-review")
        if summary_value(result.summary_rows, "split_stability_status") != "split_stability_supportive_manual_review_required":
            failures.append("fixture should mark split stability supportive/manual-review")
        if summary_value(result.summary_rows, "drawdown_tradeoff_status") != "drawdown_tradeoff_supportive_lower_drawdown_manual_review_required":
            failures.append("fixture should mark drawdown tradeoff supportive/manual-review")
        if summary_value(result.summary_rows, "preview_readiness_status") != PREVIEW_READY_STATUS:
            failures.append("fixture should keep preview design blocked")

        for collection in [result.checkpoint_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
            for row in collection:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return
        code, lines = show_vol_targeted_growth_robustness_checkpoint(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [FINAL_STATUS_REVIEW, PREFERRED_CANDIDATE, "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display output missing token: {token}")


def write_sprint_fixture(data: Path) -> None:
    rows = [
        sprint_row(PREFERRED_CANDIDATE, "multi_sleeve_vol_targeted_growth", "19.0011", "1.2861", "-18.1016", "1.0497", "14.331", "15.2", "22.1", "1.2", "1.6"),
        sprint_row("higher_growth_multi_sleeve_target_vol_10_win_20_cap_1x", "multi_sleeve_vol_targeted_growth", "14.5", "1.10", "-15.5", "0.90", "10.2", "11.0", "16.1", "1.0", "1.1"),
        sprint_row("higher_growth_multi_sleeve_target_vol_20_win_20_cap_1x", "multi_sleeve_vol_targeted_growth", "21.0", "1.19", "-20.4", "1.02", "18.8", "17.1", "24.1", "1.1", "1.4"),
        sprint_row("high_growth_balanced_target_vol_25_win_20_cap_1x", "high_growth_balanced_vol_targeted", "33.5011", "1.2296", "-28.3531", "1.1816", "26.3073", "30.0", "37.0", "1.1", "1.5"),
        sprint_row("qqq100_target_vol_25_win_20_cap_1x", "qqq100_vol_targeted_growth", "16.5", "1.01", "-23.4", "0.70", "16.0", "13.0", "17.0", "0.8", "0.9"),
        sprint_row("balanced_multi_sleeve_target_vol_15_win_20_cap_1x", "balanced_multi_sleeve_vol_targeted_growth", "17.9", "1.25", "-18.2", "0.98", "14.2", "14.0", "19.0", "1.1", "1.2"),
    ]
    write_csv(
        data / "vol_targeted_growth_research_sprint.csv",
        [
            "candidate_name",
            "candidate_family",
            "cagr",
            "sharpe",
            "max_drawdown",
            "calmar",
            "realized_volatility",
            "in_sample_cagr",
            "out_of_sample_cagr",
            "out_of_sample_sharpe",
            "out_of_sample_calmar",
            "final_candidate_status",
        ],
        rows,
    )


def sprint_row(candidate_name: str, family: str, cagr: str, sharpe: str, max_dd: str, calmar: str, vol: str, is_cagr: str, oos_cagr: str, oos_sharpe: str, oos_calmar: str) -> dict[str, str]:
    return {
        "candidate_name": candidate_name,
        "candidate_family": family,
        "cagr": cagr,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "realized_volatility": vol,
        "in_sample_cagr": is_cagr,
        "out_of_sample_cagr": oos_cagr,
        "out_of_sample_sharpe": oos_sharpe,
        "out_of_sample_calmar": oos_calmar,
        "final_candidate_status": "strong_vol_targeted_growth_candidate_research_only",
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start_token: str, end_token: str) -> str:
    start = source.find(start_token)
    if start < 0:
        return ""
    end = source.find(end_token, start + len(start_token))
    if end < 0:
        return source[start:]
    return source[start:end]


def summary_value(rows: list[dict[str, object]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
