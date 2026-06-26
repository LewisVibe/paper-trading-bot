from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_active_seed_readiness import (  # noqa: E402
    ACTIVE_SEED,
    ACTIVE_TICKER,
    FINAL_STATUS,
    INCOMPLETE_STATUS,
    OUTPUT_FILES,
    PREVIOUS_SEED,
    PREVIOUS_TICKER,
    SAFETY_FLAGS,
    generate_vol_targeted_growth_active_seed_readiness,
    show_vol_targeted_growth_active_seed_readiness,
)


COMMANDS = [
    "--vol-targeted-growth-active-seed-readiness",
    "--show-vol-targeted-growth-active-seed-readiness",
]
EXPECTED_OUTPUTS = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
FALSE_FLAGS = [
    "active_seed_status_changed",
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
    "monitoring_only",
    "manual_review_only",
    "active_seed_readiness_only",
    "preview_only",
    "never_schedule_order_capable_commands",
]
FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_all_positions(",
    "get_alpaca_positions(",
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
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_active_seed_readiness.py")
    verify_commands(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source(module_source, failures)
    verify_ready_fixture(failures)
    verify_incomplete_fixture(failures)
    if failures:
        print("Volatility-targeted growth active-seed readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth active-seed readiness verification passed.")
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
        ACTIVE_SEED,
        ACTIVE_TICKER,
        PREVIOUS_SEED,
        PREVIOUS_TICKER,
        FINAL_STATUS,
        INCOMPLETE_STATUS,
        "saved_output_only",
        "action_preview_added",
        "order_instructions_created",
        "execution_approved",
        "scheduling_approved",
    ]:
        if token not in source:
            failures.append(f"missing required token: {token}")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"forbidden source token: {token}")
    show_body = source_slice(source, "def show_vol_targeted_growth_active_seed_readiness", "def build_readiness_rows")
    if "write_rows" in show_body or "generate_vol_targeted_growth_active_seed_readiness" in show_body:
        failures.append("show command must not regenerate output")
    for flag in FALSE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not False:
            failures.append(f"flag must be false: {flag}")
    for flag in TRUE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not True:
            failures.append(f"flag must be true: {flag}")


def verify_ready_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_ready_inputs(root)
        result = generate_vol_targeted_growth_active_seed_readiness(root)
        summary = rows_to_map(result.summary_rows)
        if summary.get("final_active_seed_readiness_status") != FINAL_STATUS:
            failures.append(f"ready fixture expected {FINAL_STATUS}, got {summary.get('final_active_seed_readiness_status')}")
        if summary.get("active_seed") != ACTIVE_SEED or summary.get("active_ticker") != ACTIVE_TICKER:
            failures.append("ready fixture should preserve volatility active seed and ticker")
        if summary.get("previous_seed") != PREVIOUS_SEED or summary.get("previous_ticker") != PREVIOUS_TICKER:
            failures.append("ready fixture should preserve previous QQQ100 context")
        if summary.get("readiness_warning_count") != "0":
            failures.append("ready fixture should have no readiness warnings")
        verify_false_and_true_flags(result, failures)
        code, lines = show_vol_targeted_growth_active_seed_readiness(root)
        if code != 0 or FINAL_STATUS not in "\n".join(lines):
            failures.append("show command did not display saved active-seed readiness")


def verify_incomplete_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seed_ready_inputs(root)
        write_summary(root / "data" / "paper_live_monitoring_status.csv", {"active_strategy": "qqq_100_trend_gate"})
        result = generate_vol_targeted_growth_active_seed_readiness(root)
        summary = rows_to_map(result.summary_rows)
        if summary.get("final_active_seed_readiness_status") != INCOMPLETE_STATUS:
            failures.append("stale active-seed fixture should be incomplete/manual-review required")
        if summary.get("readiness_warning_count") == "0":
            failures.append("stale active-seed fixture should create a warning")
        verify_false_and_true_flags(result, failures)


def verify_false_and_true_flags(result, failures: list[str]) -> None:
    rows = result.summary_rows + result.readiness_rows + result.evidence_rows + result.blocker_rows
    for row in rows:
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).lower() != "false":
                failures.append(f"expected false flag {flag}")
                return
        for flag in TRUE_FLAGS:
            if str(row.get(flag, "")).lower() != "true":
                failures.append(f"expected true flag {flag}")
                return


def seed_ready_inputs(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_summary(
        data / "paper_live_monitoring_status.csv",
        {
            "active_strategy": ACTIVE_SEED,
            "active_ticker": ACTIVE_TICKER,
            "previous_seed_strategy": PREVIOUS_SEED,
            "previous_seed_ticker": PREVIOUS_TICKER,
        },
    )
    write_summary(data / "paper_live_promotion_ladder_status_summary.csv", {"current_seed": f"{ACTIVE_SEED}:{ACTIVE_TICKER}"})
    write_summary(data / "paper_live_checklist_status_summary.csv", {"active_strategy": ACTIVE_SEED})
    write_summary(data / "vps_daily_monitoring_summary.csv", {"final_status": "healthy_monitoring_state"})
    write_summary(data / "vol_targeted_growth_proposal_preview_summary.csv", {"final_proposal_preview_status": "vol_targeted_growth_proposal_preview_created_saved_output_only"})
    write_summary(data / "vol_targeted_growth_seed_change_risk_reward_summary.csv", {"final_risk_reward_status": "vol_targeted_growth_risk_reward_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_drawdown_stress_summary.csv", {"final_drawdown_stress_status": "vol_targeted_growth_drawdown_stress_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_cost_turnover_summary.csv", {"final_cost_turnover_status": "vol_targeted_growth_cost_turnover_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_split_stability_summary.csv", {"final_split_stability_status": "vol_targeted_growth_split_stability_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_component_sleeve_summary.csv", {"final_component_sleeve_status": "vol_targeted_growth_component_sleeve_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_broker_exposure_summary.csv", {"final_broker_exposure_status": "vol_targeted_growth_broker_exposure_evidence_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_manual_approval_summary.csv", {"final_manual_approval_status": "vol_targeted_growth_seed_change_manual_approval_recorded_implementation_required"})
    write_summary(data / "vol_targeted_growth_seed_change_implementation_design_summary.csv", {"final_design_status": "vol_targeted_growth_seed_change_implementation_design_created_manual_review_required"})
    write_summary(data / "vol_targeted_growth_seed_change_dry_run_diff_summary.csv", {"final_dry_run_diff_status": "vol_targeted_growth_seed_change_dry_run_diff_created_manual_review_required"})


def write_summary(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["summary_name", "summary_value"])
        writer.writeheader()
        for key, value in values.items():
            writer.writerow({"summary_name": key, "summary_value": value})


def rows_to_map(rows: list[dict[str, object]]) -> dict[str, str]:
    return {str(row.get("summary_name", "")): str(row.get("summary_value", "")) for row in rows}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index < 0:
        return ""
    end_index = source.find(end, start_index + len(start))
    if end_index < 0:
        return source[start_index:]
    return source[start_index:end_index]


if __name__ == "__main__":
    raise SystemExit(main())
