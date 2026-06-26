from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_seed_change_drawdown_stress_review import (  # noqa: E402
    FINAL_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_seed_change_drawdown_stress_review,
    show_vol_targeted_growth_seed_change_drawdown_stress_review,
)


COMMANDS = [
    "--vol-targeted-growth-seed-change-drawdown-stress-review",
    "--show-vol-targeted-growth-seed-change-drawdown-stress-review",
]
EXPECTED_OUTPUTS = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
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
TRUE_FLAGS = [
    "research_only",
    "report_only",
    "saved_output_only",
    "manual_review_only",
    "drawdown_stress_review_only",
    "proposal_only",
    "preview_only",
    "never_schedule_order_capable_commands",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(
        ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_drawdown_stress_review.py"
    )
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_fixture(failures)
    if failures:
        print("Volatility-targeted growth seed-change drawdown/stress review verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth seed-change drawdown/stress review verification passed.")
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
    for output in EXPECTED_OUTPUTS:
        result = subprocess.run(["git", "check-ignore", output], cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"generated output is not ignored: {output}")


def verify_source(source: str, failures: list[str]) -> None:
    for token in [
        FINAL_STATUS,
        "saved_drawdown_metric_not_fresh_apples_to_apples_stress_regeneration_manual_review_required",
        "drawdown_metric_favorable_but_stress_window_evidence_incomplete",
        "manual_review_required_not_fresh_stress_regeneration",
        "qqq100_displacement_approved",
        "seed_change_proposal_created",
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
    show_body = source_slice(source, "def show_vol_targeted_growth_seed_change_drawdown_stress_review", "def build_review_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_seed_change_drawdown_stress_review" in show_body:
        failures.append("show command must not regenerate output")
    for forbidden_field in ["order_side", "order_quantity", "order_type", "account_id", "api_key", "webhook", "secret_key", "order_id"]:
        if f'"{forbidden_field}"' in source:
            failures.append(f"forbidden output field: {forbidden_field}")


def verify_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_inputs(root)
        result = generate_vol_targeted_growth_seed_change_drawdown_stress_review(root)
        if summary_value(result.summary_rows, "final_drawdown_stress_status") != FINAL_STATUS:
            failures.append("fixture did not produce expected drawdown/stress status")
        comparison = summary_value(result.summary_rows, "drawdown_comparison")
        for expected in ["qqq100_MaxDD=-23.4576", "vol_targeted_MaxDD=-18.1016", "delta=5.356"]:
            if expected not in comparison:
                failures.append(f"missing drawdown comparison fragment: {expected}")
        if summary_value(result.summary_rows, "drawdown_winner") != "vol_targeted_growth":
            failures.append("volatility candidate should win saved MaxDD comparison")
        if summary_value(result.summary_rows, "stress_review_status") != "manual_review_required_not_fresh_stress_regeneration":
            failures.append("stress review should remain manual-review required")
        for row in result.summary_rows + result.review_rows + result.evidence_rows + result.blocker_rows:
            for flag in FALSE_FLAGS:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"expected false flag {flag}")
                    return
            for flag in TRUE_FLAGS:
                if str(row.get(flag, "")).lower() != "true":
                    failures.append(f"expected true flag {flag}")
                    return
        code, lines = show_vol_targeted_growth_seed_change_drawdown_stress_review(root)
        if code != 0 or FINAL_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved drawdown/stress review")


def seed_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    write_csv(
        data / "qqq100_benchmark_inputs_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "saved_benchmark_metrics", "summary_value": "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718"}],
    )
    write_csv(
        data / "qqq100_preview_candidate_readiness_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "strongest_evidence_for_preview_discussion", "summary_value": "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718"}],
    )
    write_csv(
        data / "vol_targeted_growth_nearby_variants_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "preferred_candidate", "summary_value": "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x: CAGR=19.0011; Sharpe=1.2861; MaxDD=-18.1016; Calmar=1.0497"}],
    )
    write_csv(
        data / "vol_targeted_growth_manual_review_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "multi_sleeve_candidate", "summary_value": "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x: CAGR=19.0011; Sharpe=1.2861; MaxDD=-18.1016; Calmar=1.0497"}],
    )
    write_csv(
        data / "vol_targeted_growth_robustness_checkpoint_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_robustness_status", "summary_value": "vol_targeted_growth_robustness_manual_review_required"}],
    )
    write_csv(
        data / "vol_targeted_growth_seed_change_evidence_summary.csv",
        ["summary_name", "summary_value"],
        [{"summary_name": "final_evidence_pack_status", "summary_value": "vol_targeted_growth_seed_change_evidence_pack_incomplete_manual_review_required"}],
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start_token: str, end_token: str) -> str:
    start = source.find(start_token)
    end = source.find(end_token, start + 1) if start >= 0 else -1
    return source[start:end] if start >= 0 and end >= 0 else source[start:] if start >= 0 else ""


def summary_value(rows: list[dict[str, object]], name: str) -> str:
    for row in rows:
        if row.get("summary_name") == name:
            return str(row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
