from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.high_growth_strategy_discovery_sprint import (  # noqa: E402
    COMPLETE_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    STRONG_STATUS,
    generate_high_growth_strategy_discovery_sprint,
    show_high_growth_strategy_discovery_sprint,
)


EXPECTED_OUTPUTS = [
    "data/high_growth_strategy_discovery_sprint.csv",
    "data/high_growth_strategy_discovery_sprint_summary.csv",
    "data/high_growth_strategy_discovery_sprint_evidence.csv",
    "data/high_growth_strategy_discovery_sprint_blockers.csv",
]

COMMANDS = [
    "--high-growth-strategy-discovery-sprint",
    "--show-high-growth-strategy-discovery-sprint",
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
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
    "preview_candidate_approved",
    "high_growth_promotion_approved",
]

TRUE_FLAGS = [
    "research_only",
    "report_only",
    "saved_output_only",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_path = ROOT / "trading_bot" / "research" / "high_growth_strategy_discovery_sprint.py"
    module_source = read_text(module_path)

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_fixture_generation(failures)

    if failures:
        print("High-growth strategy discovery sprint verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("High-growth strategy discovery sprint verification passed.")
    print("Verified saved-output-only sprint generation, two distinct strong candidates, fragile exclusions, display safety, and false approval flags.")
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

    for token in [
        "generate_high_growth_strategy_discovery_sprint",
        "show_high_growth_strategy_discovery_sprint",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing sprint function token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        result = subprocess.run(
            ["git", "check-ignore", expected],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"generated output is not ignored by git: {expected}")


def verify_source_boundaries(module_source: str, bot_source: str, failures: list[str]) -> None:
    required = [
        "Alpha Research Subagent A - aggressive trend/breakout",
        "Alpha Research Subagent B - relative strength / rotation",
        "Alpha Research Subagent C - crypto / risk-on sleeve",
        "Alpha Research Subagent D - unconstrained experimental",
        "Backtest Engineering Subagent",
        "Robustness/Audit Subagent",
        "high_growth_strategy_discovery_two_or_more_strong_candidates_found",
        "high_growth_strategy_discovery_incomplete_fewer_than_two_strong_candidates",
        "strong_high_growth_candidate_research_only",
        "high_growth_candidate_fragile_rejected",
        "never_schedule_order_capable_commands",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "live_trading_approved",
        "high_growth_promotion_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"sprint module missing required token: {token}")

    for flag in FALSE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not False:
            failures.append(f"sprint safety flag must be false: {flag}")
    for flag in TRUE_FLAGS:
        if SAFETY_FLAGS.get(flag) is not True:
            failures.append(f"sprint safety flag must be true: {flag}")

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
            failures.append(f"sprint module must not contain forbidden token: {token}")

    show_body = source_slice(module_source, "def show_high_growth_strategy_discovery_sprint", "def build_candidate_rows")
    if "write_rows" in show_body or "generate_high_growth_strategy_discovery_sprint" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")

    if "high_growth_strategy_discovery_sprint" not in bot_source:
        failures.append("bot.py should reference the sprint module/command family")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "qqq100_recovered_reference_metrics.csv",
            ["cagr", "sharpe", "max_drawdown", "calmar"],
            [{"cagr": "16.9832", "sharpe": "1.0073", "max_drawdown": "-23.4576", "calmar": "0.724"}],
        )
        write_csv(
            data / "high_growth_return_stream_metrics.csv",
            ["candidate_name", "CAGR", "Sharpe", "MaxDD", "Calmar"],
            [
                {"candidate_name": "broad_growth_top1_reference", "CAGR": "62.0588", "Sharpe": "1.1297", "MaxDD": "-70.1642", "Calmar": "0.8845"},
                {"candidate_name": "codex_broad_growth_balanced_breakout_control", "CAGR": "48.7551", "Sharpe": "1.186", "MaxDD": "-42.3324", "Calmar": "1.1517"},
            ],
        )
        write_csv(
            data / "high_growth_sleeve_quality_summary.csv",
            ["summary_name", "summary_value"],
            [{"summary_name": "final_high_growth_sleeve_quality_status", "summary_value": "high_growth_sleeve_quality_promising_but_drawdown_sensitive"}],
        )
        write_csv(
            data / "high_growth_component_streams_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "component_rows", "summary_value": "3872"},
                {"summary_name": "top_contribution_ticker", "summary_value": "SE"},
                {"summary_name": "max_component_weight", "summary_value": "1.0"},
            ],
        )
        write_csv(
            data / "multi_sleeve_portfolio_backtest.csv",
            [
                "portfolio_name",
                "candidate_cagr",
                "candidate_sharpe",
                "candidate_max_drawdown",
                "candidate_calmar",
                "rough_cost_sensitivity",
                "candidate_turnover_or_trade_count",
                "missing_sleeve_data_warnings",
                "biggest_blocker",
                "final_backtest_status",
            ],
            [
                {"portfolio_name": "qqq100_plus_high_growth_research", "candidate_cagr": "20.9511", "candidate_sharpe": "1.1462", "candidate_max_drawdown": "-22.0191", "candidate_calmar": "0.9515", "rough_cost_sensitivity": "stable", "candidate_turnover_or_trade_count": "saved", "missing_sleeve_data_warnings": "none", "biggest_blocker": "manual_review_required", "final_backtest_status": "research_only"},
                {"portfolio_name": "balanced_multi_sleeve_research_portfolio", "candidate_cagr": "20.9941", "candidate_sharpe": "1.1947", "candidate_max_drawdown": "-21.6286", "candidate_calmar": "0.9707", "rough_cost_sensitivity": "stable", "candidate_turnover_or_trade_count": "saved", "missing_sleeve_data_warnings": "none", "biggest_blocker": "manual_review_required", "final_backtest_status": "research_only"},
                {"portfolio_name": "qqq100_plus_high_growth_plus_crypto_research", "candidate_cagr": "21.7328", "candidate_sharpe": "1.1852", "candidate_max_drawdown": "-22.2489", "candidate_calmar": "0.9768", "rough_cost_sensitivity": "stable", "candidate_turnover_or_trade_count": "saved", "missing_sleeve_data_warnings": "none", "biggest_blocker": "manual_review_required", "final_backtest_status": "research_only"},
            ],
        )
        write_csv(
            data / "multi_sleeve_higher_growth_review.csv",
            ["allocation_name", "CAGR", "Sharpe", "MaxDD", "Calmar"],
            [
                {"allocation_name": "current_75_15_5_5", "CAGR": "21.7328", "Sharpe": "1.1852", "MaxDD": "-22.2489", "Calmar": "0.9768"},
                {"allocation_name": "higher_growth_70_20_5_5", "CAGR": "23.6634", "Sharpe": "1.2232", "MaxDD": "-22.5209", "Calmar": "1.0507"},
            ],
        )
        write_csv(
            data / "multi_sleeve_higher_growth_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "split_win_count", "summary_value": "3"},
                {"summary_name": "worst_cost_stress_result", "summary_value": "beats_current"},
                {"summary_name": "final_higher_growth_review_status", "summary_value": "higher_growth_review_promising_but_drawdown_sensitive"},
            ],
        )
        write_csv(
            data / "multi_sleeve_robustness_summary.csv",
            ["summary_name", "summary_value"],
            [
                {"summary_name": "final_robustness_status", "summary_value": "multi_sleeve_robustness_promising"},
                {"summary_name": "calmar_win_count_vs_generated_qqq100", "summary_value": "3"},
            ],
        )
        write_csv(
            data / "crypto_return_stream_metrics.csv",
            ["candidate_name", "CAGR", "Sharpe", "MaxDD", "Calmar"],
            [{"candidate_name": "btc_trend_vol_gate", "CAGR": "45.9331", "Sharpe": "0.9979", "MaxDD": "-73.0752", "Calmar": "0.6286"}],
        )
        write_csv(
            data / "multi_sleeve_crypto_containment_summary.csv",
            ["summary_name", "summary_value"],
            [{"summary_name": "final_crypto_containment_status", "summary_value": "crypto_containment_research_only"}],
        )

        result = generate_high_growth_strategy_discovery_sprint(root)
        status = summary_value(result.summary_rows, "final_discovery_status")
        strong_count = int(summary_value(result.summary_rows, "strong_candidate_count"))
        if status != COMPLETE_STATUS:
            failures.append(f"fixture should produce complete status, got {status}")
        if strong_count < 2:
            failures.append(f"fixture should produce at least two strong candidates, got {strong_count}")

        strong_rows = [row for row in result.report_rows if row["final_candidate_status"] == STRONG_STATUS]
        strong_families = {row["candidate_family"] for row in strong_rows}
        if len(strong_families) < 2:
            failures.append("strong candidates should span at least two distinct families")
        if any("broad_growth_top1_reference" == row["candidate_name"] and row["final_candidate_status"] == STRONG_STATUS for row in result.report_rows):
            failures.append("fragile broad Top1 reference must not become a strong candidate")
        if any("btc_trend_vol_gate" == row["candidate_name"] and row["final_candidate_status"] == STRONG_STATUS for row in result.report_rows):
            failures.append("standalone crypto drawdown candidate must not become a strong candidate")

        for collection in [result.report_rows, result.summary_rows, result.evidence_rows, result.blocker_rows]:
            for row in collection:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return

        code, lines = show_high_growth_strategy_discovery_sprint(root)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        display = "\n".join(lines)
        for token in [COMPLETE_STATUS, "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display output missing token: {token}")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index < 0:
        return ""
    end_index = source.find(end, start_index + len(start))
    return source[start_index:] if end_index < 0 else source[start_index:end_index]


def summary_value(rows: list[dict[str, object]], key: str) -> str:
    for row in rows:
        if str(row.get("summary_name", "")) == key:
            return str(row.get("summary_value", ""))
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
