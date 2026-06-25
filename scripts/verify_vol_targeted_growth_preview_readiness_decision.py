from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_preview_readiness_decision import (  # noqa: E402
    AGGRESSIVE_CHALLENGER,
    FINAL_STATUS,
    NEAREST_HIGHER_VOL_CHALLENGER,
    OUTPUT_FILES,
    PREVIEW_IMPLEMENTATION_STATUS,
    READINESS_STATUS,
    SAFETY_FLAGS,
    SELECTED_CANDIDATE,
    generate_vol_targeted_growth_preview_readiness_decision,
    show_vol_targeted_growth_preview_readiness_decision,
)


EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_preview_readiness_decision.csv",
    "data/vol_targeted_growth_preview_readiness_summary.csv",
    "data/vol_targeted_growth_preview_readiness_evidence.csv",
    "data/vol_targeted_growth_preview_readiness_blockers.csv",
]

COMMANDS = [
    "--vol-targeted-growth-preview-readiness-decision",
    "--show-vol-targeted-growth-preview-readiness-decision",
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
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_preview_readiness_decision.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth preview-readiness decision verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth preview-readiness decision verification passed.")
    print("Verified saved-output decision, selected/challenger labels, false approvals, and no broker/order/config/scheduling paths.")
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
    for token in ["generate_vol_targeted_growth_preview_readiness_decision", "show_vol_targeted_growth_preview_readiness_decision"]:
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
        SELECTED_CANDIDATE,
        NEAREST_HIGHER_VOL_CHALLENGER,
        AGGRESSIVE_CHALLENGER,
        FINAL_STATUS,
        READINESS_STATUS,
        PREVIEW_IMPLEMENTATION_STATUS,
        "create_saved_output_preview_design_for_vol_targeted_growth_15_20_in_separate_prompt",
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

    show_body = source_slice(module_source, "def show_vol_targeted_growth_preview_readiness_decision", "def build_decision_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_preview_readiness_decision" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "vol_targeted_growth_nearby_variants_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "final_nearby_review_status", "summary_value": "vol_targeted_growth_nearby_variants_manual_review_required"},
                {"summary_name": "variant_interpretation", "summary_value": "preferred_15_20_retains_best_calmar_and_sharpe_but_requires_manual_review"},
            ],
        )
        write_csv(
            data / "vol_targeted_growth_nearby_variants_review.csv",
            ["candidate_name", "cagr", "sharpe", "max_drawdown", "calmar"],
            [
                row(SELECTED_CANDIDATE, "19.0011", "1.2861", "-18.1016", "1.0497"),
                row(NEAREST_HIGHER_VOL_CHALLENGER, "21.5042", "1.2511", "-21.0717", "1.0205"),
                row(AGGRESSIVE_CHALLENGER, "22.8683", "1.2376", "-22.6334", "1.0104"),
            ],
        )
        write_csv(data / "vol_targeted_growth_robustness_checkpoint_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "final_robustness_status", "summary_value": "vol_targeted_growth_robustness_manual_review_required"}])
        write_csv(data / "vol_targeted_growth_manual_review_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "final_manual_review_status", "summary_value": "vol_targeted_growth_manual_review_required"}])

        result = generate_vol_targeted_growth_preview_readiness_decision(root)
        status = summary_value(result.summary_rows, "final_decision_status")
        if status != FINAL_STATUS:
            failures.append(f"fixture should produce final decision status, got {status}")
        if summary_value(result.summary_rows, "preview_design_readiness_status") != READINESS_STATUS:
            failures.append("fixture should mark preview-design discussion ready/manual-review")
        if summary_value(result.summary_rows, "preview_implementation_status") != PREVIEW_IMPLEMENTATION_STATUS:
            failures.append("preview implementation must remain not added")
        if SELECTED_CANDIDATE not in summary_value(result.summary_rows, "selected_candidate"):
            failures.append("selected candidate summary missing selected candidate")
        if AGGRESSIVE_CHALLENGER not in summary_value(result.summary_rows, "aggressive_challenger"):
            failures.append("aggressive challenger summary missing 25/20")

        for collection in [result.decision_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
            for output_row in collection:
                for flag in FALSE_FLAGS:
                    if str(output_row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(output_row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return
        code, lines = show_vol_targeted_growth_preview_readiness_decision(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [FINAL_STATUS, SELECTED_CANDIDATE, "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display output missing token: {token}")


def row(candidate_name: str, cagr: str, sharpe: str, max_drawdown: str, calmar: str) -> dict[str, str]:
    return {"candidate_name": candidate_name, "cagr": cagr, "sharpe": sharpe, "max_drawdown": max_drawdown, "calmar": calmar}


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
    for output_row in rows:
        if output_row.get("summary_name") == name:
            return str(output_row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
