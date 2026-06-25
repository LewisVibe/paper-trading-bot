from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_manual_review_pack import (  # noqa: E402
    FINAL_STATUS_READY,
    MULTI_SLEEVE_STATUS,
    OUTPUT_FILES,
    PRIMARY_HIGH_RETURN_CANDIDATE,
    PRIMARY_MULTI_SLEEVE_CANDIDATE,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_manual_review_pack,
    show_vol_targeted_growth_manual_review_pack,
)


EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_manual_review_pack.csv",
    "data/vol_targeted_growth_manual_review_summary.csv",
    "data/vol_targeted_growth_manual_review_evidence.csv",
    "data/vol_targeted_growth_manual_review_blockers.csv",
]

COMMANDS = [
    "--vol-targeted-growth-manual-review-pack",
    "--show-vol-targeted-growth-manual-review-pack",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_manual_review_pack.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth manual review pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth manual review pack verification passed.")
    print("Verified saved-output manual review, side-by-side candidate comparison, false approvals, and no broker/order/config/scheduling paths.")
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

    for token in ["generate_vol_targeted_growth_manual_review_pack", "show_vol_targeted_growth_manual_review_pack"]:
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
        PRIMARY_HIGH_RETURN_CANDIDATE,
        PRIMARY_MULTI_SLEEVE_CANDIDATE,
        "vol_targeted_growth_manual_review_required",
        "multi_sleeve_vol_targeted_growth_more_credible_research_path",
        "high_return_vol_targeted_growth_high_risk_manual_review_required",
        "preview_design_not_approved",
        "run_saved_output_robustness_checkpoint_before_preview_design",
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

    show_body = source_slice(module_source, "def show_vol_targeted_growth_manual_review_pack", "def build_pack_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_manual_review_pack" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
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
                "final_candidate_status",
                "execution_approved",
                "scheduling_approved",
            ],
            [
                {
                    "candidate_name": PRIMARY_HIGH_RETURN_CANDIDATE,
                    "candidate_family": "high_growth_balanced_vol_targeted",
                    "cagr": "33.5011",
                    "sharpe": "1.2296",
                    "max_drawdown": "-28.3531",
                    "calmar": "1.1816",
                    "realized_volatility": "26.3073",
                    "final_candidate_status": "strong_vol_targeted_growth_candidate_research_only",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                },
                {
                    "candidate_name": PRIMARY_MULTI_SLEEVE_CANDIDATE,
                    "candidate_family": "multi_sleeve_vol_targeted_growth",
                    "cagr": "19.0011",
                    "sharpe": "1.2861",
                    "max_drawdown": "-18.1016",
                    "calmar": "1.0497",
                    "realized_volatility": "14.331",
                    "final_candidate_status": "strong_vol_targeted_growth_candidate_research_only",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                },
                {
                    "candidate_name": "qqq100_target_vol_25_win_20_cap_1x",
                    "candidate_family": "qqq100_vol_targeted_growth",
                    "cagr": "16.5",
                    "sharpe": "1.01",
                    "max_drawdown": "-23.4",
                    "calmar": "0.70",
                    "realized_volatility": "16.0",
                    "final_candidate_status": "vol_targeted_growth_fragile_or_low_return_rejected",
                    "execution_approved": "False",
                    "scheduling_approved": "False",
                },
            ],
        )
        write_csv(
            data / "vol_targeted_growth_candidate_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "final_research_status", "summary_value": "vol_targeted_growth_research_two_or_more_strong_candidates_found"},
                {"summary_name": "strong_candidate_count", "summary_value": "4"},
                {"summary_name": "candidate_families_tested", "summary_value": "7"},
            ],
        )
        write_csv(data / "vol_targeted_growth_rejected_candidates.csv", ["candidate_name", "rejection_status"], [{"candidate_name": "high_growth_top1_target_vol_25_win_20_cap_1x", "rejection_status": "vol_targeted_growth_fragile_or_low_return_rejected"}])
        write_csv(data / "vol_targeted_growth_robustness_audit.csv", ["audit_name", "audit_value"], [{"audit_name": "hidden_leverage_policy", "audit_value": "passed"}])
        write_csv(data / "vol_targeted_growth_parameter_sensitivity.csv", ["candidate_family", "strong_candidate_count"], [{"candidate_family": "multi_sleeve_vol_targeted_growth", "strong_candidate_count": "2"}])

        result = generate_vol_targeted_growth_manual_review_pack(root)
        status = summary_value(result.summary_rows, "final_manual_review_status")
        if status != FINAL_STATUS_READY:
            failures.append(f"fixture should produce manual-review status, got {status}")
        preferred = summary_value(result.summary_rows, "preferred_research_path")
        if preferred != PRIMARY_MULTI_SLEEVE_CANDIDATE:
            failures.append(f"preferred path should be {PRIMARY_MULTI_SLEEVE_CANDIDATE}, got {preferred}")
        if not any(row.get("status") == MULTI_SLEEVE_STATUS for row in result.pack_rows):
            failures.append("fixture should mark multi-sleeve candidate as more credible research path")
        for collection in [result.pack_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
            for row in collection:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return
        code, lines = show_vol_targeted_growth_manual_review_pack(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [FINAL_STATUS_READY, PRIMARY_MULTI_SLEEVE_CANDIDATE, "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display output missing token: {token}")


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
