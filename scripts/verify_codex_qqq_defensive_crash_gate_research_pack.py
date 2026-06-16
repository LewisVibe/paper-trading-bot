from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.codex_qqq_defensive_crash_gate_research_pack import (  # noqa: E402
    BASELINE_CANDIDATE,
    BIGGEST_BLOCKER,
    FINAL_RESEARCH_STATUS,
    OUTPUT_FILES,
    RECOMMENDED_NEXT_STEP,
    TOP_CANDIDATE,
    generate_codex_qqq_defensive_crash_gate_research_pack,
    show_codex_qqq_defensive_crash_gate_research_pack,
)


EXPECTED_OUTPUTS = [
    "data/codex_qqq_defensive_crash_gate_research_pack.csv",
    "data/codex_qqq_defensive_crash_gate_candidates.csv",
    "data/codex_qqq_defensive_crash_gate_rankings.csv",
    "data/codex_qqq_defensive_crash_gate_splits.csv",
    "data/codex_qqq_defensive_crash_gate_blockers.csv",
    "data/codex_qqq_defensive_crash_gate_next_steps.csv",
]

REQUIRED_CANDIDATE_COLUMNS = [
    "candidate_name",
    "candidate_role",
    "cagr",
    "sharpe",
    "max_drawdown",
    "calmar",
    "annualised_volatility",
    "cash_percentage",
    "turnover_or_trade_count",
    "rough_cost_sensitivity",
    "split_stability",
    "delta_cagr_vs_reference",
    "delta_sharpe_vs_reference",
    "delta_max_drawdown_vs_reference",
    "delta_calmar_vs_reference",
    "balanced_research_score",
    "final_candidate_status",
    "recommended_next_step",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "codex_qqq_defensive_crash_gate_research_pack.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_no_execution_expansion(bot_source, failures)
    verify_temp_generation(failures)

    if failures:
        print("Codex QQQ defensive crash-gate research pack verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Codex QQQ defensive crash-gate research pack verification passed.")
    print("Verified research-only candidates, baseline/improvement fields, missing-metric labels, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--codex-qqq-defensive-crash-gate-research-pack",
        "--show-codex-qqq-defensive-crash-gate-research-pack",
        "generate_codex_qqq_defensive_crash_gate_research_pack",
        "show_codex_qqq_defensive_crash_gate_research_pack",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing Codex QQQ defensive command token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, failures: list[str]) -> None:
    required = [
        "qqq100_trend_gate_reference",
        "codex_qqq_cash_crash_gate_sleeve",
        "codex_qqq_spy_defensive_gate_sleeve",
        "codex_qqq_partial_defensive_sleeve",
        "codex_qqq_fast_crash_exit_reentry_sleeve",
        "codex_qqq_calmar_optimised_defensive_gate_sleeve",
        "baseline_cagr",
        "baseline_source",
        "candidate_delta_cagr",
        "delta_calmar_vs_reference",
        "balanced_research_score",
        "split_60_40",
        "split_70_30",
        "split_80_20",
        "missing_saved_metrics",
        "missing_saved_data",
        "missing_exact_qqq100_saved_metrics",
        "qqq_100_trend_gate_saved_metrics",
        "codex_qqq_defensive_research_pack_created",
        "codex_qqq_defensive_needs_more_validation",
        "codex_experimental_execution_approved",
        "repeat_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"research pack module missing required token: {token}")

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
        "download(",
        "subprocess.run",
        "create_scheduled_task",
        "automation_update",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"research pack module must not contain runtime/scheduling token: {token}")


def verify_no_execution_expansion(bot_source: str, failures: list[str]) -> None:
    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--codex-qqq-defensive-crash-gate-research-pack"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("Codex QQQ defensive research route must not call execution commands")
    execute_block = source_slice(bot_source, "def run_execute_qqq100_paper", "def run_strategy")
    if "--codex-qqq-defensive-crash-gate-research-pack" in execute_block:
        failures.append("existing --execute-qqq100-paper behavior should not be expanded by the research pack")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(
            root / "data" / "qqq_lead_decision_report.csv",
            ["candidate_name", "CAGR", "Sharpe", "MaxDD", "Calmar"],
            [["codex_ambitious_concentrated_growth_persistence", "14.1039", "0.7192", "-29.5357", "0.4775"]],
        )
        write_fixture(
            root / "data" / "sleeve_research_candidates.csv",
            ["candidate_name", "estimated_or_observed_cagr", "estimated_or_observed_sharpe", "estimated_or_observed_max_drawdown", "estimated_or_observed_calmar"],
            [["qqq_100_trend_gate", "16.8429", "1.0027", "-23.4576", "0.718"]],
        )
        result = generate_codex_qqq_defensive_crash_gate_research_pack(root)
        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        pack = result.pack_rows[0]
        if pack.get("final_research_status") != FINAL_RESEARCH_STATUS:
            failures.append("final research status should be codex_qqq_defensive_research_pack_created")
        if pack.get("baseline_candidate") != BASELINE_CANDIDATE:
            failures.append("baseline candidate should be qqq100_trend_gate_reference")
        if pack.get("top_defensive_crash_gate_candidate") != TOP_CANDIDATE:
            failures.append("top candidate should be Codex Calmar-optimised defensive gate")
        if pack.get("baseline_cagr") != "16.8429":
            failures.append("baseline metrics should be read from saved candidate fixture when available")
        if pack.get("baseline_source") != "qqq100_core_trend_sleeve_saved_metrics":
            failures.append("baseline source should identify exact QQQ100/sleeve saved metrics")
        if old_ambitious_metrics_used(pack):
            failures.append("baseline must not use old codex_ambitious_concentrated_growth_persistence metrics")
        if pack.get("biggest_blocker") != BIGGEST_BLOCKER:
            failures.append("biggest blocker should require saved market metrics before label change")
        if pack.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
            failures.append("recommended next step should be saved/research-data backtest")

        for column in REQUIRED_CANDIDATE_COLUMNS:
            if column not in result.candidate_rows[0]:
                failures.append(f"candidate output missing required column: {column}")
        candidate_names = {row["candidate_name"] for row in result.candidate_rows}
        for expected in [
            BASELINE_CANDIDATE,
            "codex_qqq_cash_crash_gate_sleeve",
            "codex_qqq_spy_defensive_gate_sleeve",
            "codex_qqq_partial_defensive_sleeve",
            "codex_qqq_fast_crash_exit_reentry_sleeve",
            TOP_CANDIDATE,
        ]:
            if expected not in candidate_names:
                failures.append(f"missing defensive candidate: {expected}")
        if not any("missing_saved_metrics" in str(value) for row in result.candidate_rows for value in row.values()):
            failures.append("missing metrics should be labelled rather than invented")
        if not result.ranking_rows or "balanced_research_score" not in result.ranking_rows[0]:
            failures.append("rankings should include balanced_research_score")
        if not result.split_rows or "split_60_40" not in {row["split_name"] for row in result.split_rows}:
            failures.append("split rows should include fixed 60/40 split placeholder")
        if not result.blocker_rows or "required_next_step" not in result.blocker_rows[0]:
            failures.append("blockers should include required next steps")

        for collection in [
            result.pack_rows,
            result.candidate_rows,
            result.ranking_rows,
            result.split_rows,
            result.blocker_rows,
            result.next_step_rows,
        ]:
            for row in collection:
                for flag in [
                    "orders_created",
                    "orders_submitted",
                    "orders_cancelled",
                    "orders_replaced",
                    "alpaca_called",
                    "live_position_read",
                    "sqlite_trade_log_written",
                    "discord_alert_sent",
                    "telegram_alert_sent",
                    "execution_approved",
                    "general_execution_approved",
                    "qqq100_execution_approved",
                    "codex_experimental_execution_approved",
                    "followup_order_approved",
                    "repeat_execution_approved",
                    "scheduling_approved",
                    "live_trading_approved",
                ]:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false in research pack outputs")
        code, lines = show_codex_qqq_defensive_crash_gate_research_pack(root)
        if code != 0 or not any(FINAL_RESEARCH_STATUS in line for line in lines):
            failures.append("saved display should show final research status")
        if not any("baseline_source:" in line for line in lines):
            failures.append("saved display should show baseline_source")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(
            root / "data" / "qqq_lead_decision_report.csv",
            ["candidate_name", "CAGR", "Sharpe", "MaxDD", "Calmar"],
            [["codex_ambitious_concentrated_growth_persistence", "14.1039", "0.7192", "-29.5357", "0.4775"]],
        )
        result = generate_codex_qqq_defensive_crash_gate_research_pack(root)
        pack = result.pack_rows[0]
        if pack.get("baseline_source") != "missing_exact_qqq100_saved_metrics":
            failures.append("old non-QQQ metrics alone should leave baseline_source as missing exact QQQ100 metrics")
        for key in ["baseline_cagr", "baseline_sharpe", "baseline_max_drawdown", "baseline_calmar"]:
            if pack.get(key) != "missing_saved_metrics":
                failures.append(f"{key} should remain missing when only old ambitious metrics exist")
        if old_ambitious_metrics_used(pack):
            failures.append("known old ambitious metrics should be blocked when no exact QQQ100 row exists")


def write_fixture(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def old_ambitious_metrics_used(pack: dict[str, str]) -> bool:
    return (
        pack.get("baseline_cagr") == "14.1039"
        and pack.get("baseline_sharpe") == "0.7192"
        and pack.get("baseline_max_drawdown") == "-29.5357"
        and pack.get("baseline_calmar") == "0.4775"
    )


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index == -1:
        return ""
    end_index = source.find(end, start_index + len(start))
    if end_index == -1:
        return source[start_index:]
    return source[start_index:end_index]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
