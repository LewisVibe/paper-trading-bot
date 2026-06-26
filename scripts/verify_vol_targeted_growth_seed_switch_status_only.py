from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULES = [
    ROOT / "trading_bot" / "research" / "paper_live_monitoring_status.py",
    ROOT / "trading_bot" / "research" / "paper_live_promotion_ladder_status.py",
    ROOT / "trading_bot" / "research" / "paper_live_checklist_status.py",
    ROOT / "trading_bot" / "research" / "vps_monitoring_status.py",
    ROOT / "trading_bot" / "research" / "vps_daily_monitoring_summary.py",
]

ACTIVE_STRATEGY = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
ACTIVE_TICKER = "MULTI_SLEEVE"
PREVIOUS_STRATEGY = "qqq_100_trend_gate"
PREVIOUS_TICKER = "QQQ"

FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_all_positions(",
    "get_alpaca_positions(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "yf.",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]

FALSE_APPROVALS = [
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "followup_order_approved",
    "repeat_execution_approved",
]


def main() -> int:
    failures: list[str] = []
    verify_sources(failures)
    verify_fixture_outputs(failures)
    if failures:
        print("Volatility-targeted growth seed switch status-only verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted growth seed switch status-only verification passed.")
    return 0


def verify_sources(failures: list[str]) -> None:
    joined = "\n".join(read_text(path) for path in MODULES)
    for token in [
        ACTIVE_STRATEGY,
        ACTIVE_TICKER,
        PREVIOUS_STRATEGY,
        PREVIOUS_TICKER,
        "previous_seed_strategy",
        "previous_seed_ticker",
        '"execution_approved": False',
        '"paper_execution_approved": False',
        '"scheduling_approved": False',
    ]:
        if token not in joined:
            failures.append(f"missing required status-only source token: {token}")
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in joined:
            failures.append(f"forbidden broker/order/config/market/scheduling token found: {token}")


def verify_fixture_outputs(failures: list[str]) -> None:
    from trading_bot.research.paper_live_checklist_status import generate_paper_live_checklist_status  # noqa: PLC0415
    from trading_bot.research.paper_live_monitoring_status import generate_paper_live_monitoring_status  # noqa: PLC0415
    from trading_bot.research.paper_live_promotion_ladder_status import generate_paper_live_promotion_ladder_status  # noqa: PLC0415
    from trading_bot.research.vps_monitoring_status import build_paper_live_monitoring_context  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        seed_fixture(root)
        monitoring = generate_paper_live_monitoring_status(root)
        ladder = generate_paper_live_promotion_ladder_status(root)
        checklist = generate_paper_live_checklist_status(root)
        context = build_paper_live_monitoring_context(root)

    monitoring_summary = rows_to_map(monitoring.summary_rows)
    ladder_summary = rows_to_map(ladder.summary_rows)
    checklist_summary = rows_to_map(checklist.summary_rows)

    expected_pairs = {
        "active_strategy": ACTIVE_STRATEGY,
        "active_ticker": ACTIVE_TICKER,
        "previous_seed_strategy": PREVIOUS_STRATEGY,
        "previous_seed_ticker": PREVIOUS_TICKER,
    }
    for name, expected in expected_pairs.items():
        if monitoring_summary.get(name) != expected:
            failures.append(f"monitoring summary {name} expected {expected}, got {monitoring_summary.get(name)}")
    if ladder_summary.get("current_seed") != f"{ACTIVE_STRATEGY}:{ACTIVE_TICKER}":
        failures.append("ladder current_seed should be the volatility candidate")
    if ladder_summary.get("previous_seed") != f"{PREVIOUS_STRATEGY}:{PREVIOUS_TICKER}":
        failures.append("ladder previous_seed should retain QQQ100")
    if checklist_summary.get("active_strategy") != ACTIVE_STRATEGY:
        failures.append("checklist active_strategy should be the volatility candidate")
    if checklist_summary.get("previous_seed_strategy") != PREVIOUS_STRATEGY:
        failures.append("checklist previous_seed_strategy should retain QQQ100")
    if not context.consistent:
        failures.append(f"VPS paper-live monitoring context should be consistent: {context.missing_or_mismatched}")

    for row in monitoring.summary_rows + ladder.summary_rows + checklist.summary_rows:
        for column in FALSE_APPROVALS:
            value = str(row.get(column, "")).strip().lower()
            if value not in {"false", ""}:
                failures.append(f"{column} must remain false, got {value}")
                return


def seed_fixture(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_summary(
        data / "qqq100_followup_policy_summary.csv",
        {
            "final_followup_policy_status": "no_action_required_already_aligned",
            "no_action_required": "True",
            "recommended_next_step": "hold_no_action_and_do_not_repeat_buy",
            "largest_blocker": "none",
        },
    )
    write_summary(data / "paper_live_promotion_ladder_design_summary.csv", {"final_design_status": "paper_live_promotion_ladder_design_report_only"})
    write_summary(data / "qqq100_daily_decision_summary.csv", {"daily_decision_status": "qqq100_daily_decision_hold_no_action_aligned_long"})
    write_summary(data / "qqq100_manual_flatten_readiness_summary.csv", {"flatten_readiness_status": "flatten_not_needed_currently"})
    write_summary(data / "qqq100_manual_flatten_runbook_summary.csv", {"runbook_status": "manual_flatten_runbook_not_needed_currently"})
    write_summary(data / "paper_live_f7_accounting_proof_summary.csv", {"final_f7_accounting_status": "f7_accounting_static_proof_ready_for_manual_review"})
    write_summary(data / "paper_live_defensive_sleeve_manual_review_summary.csv", {"final_manual_review_status": "defensive_sleeve_manual_review_required"})
    write_summary(
        data / "paper_live_defensive_sleeve_preview_readiness_summary.csv",
        {
            "final_preview_readiness_status": "defensive_sleeve_preview_candidate_not_approved_manual_review_required",
            "preview_candidate_status": "defensive_preview_candidate_not_approved",
        },
    )
    write_csv(data / "qqq100_preview_signal_pack.csv", ["desired_position"], [["long"]])
    write_csv(
        data / "qqq100_paper_postcheck.csv",
        ["position_status", "position_quantity_abs", "alignment_state"],
        [["paper_position_long", "1", "aligned_long"]],
    )
    write_summary(data / "qqq100_paper_execution_summary.csv", {"order_status": "filled"})


def write_summary(path: Path, values: dict[str, str]) -> None:
    write_csv(path, ["summary_name", "summary_value"], [[key, value] for key, value in values.items()])


def write_csv(path: Path, fieldnames: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


def rows_to_map(rows: list[dict[str, object]]) -> dict[str, str]:
    return {str(row.get("summary_name", "")): str(row.get("summary_value", "")) for row in rows}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
