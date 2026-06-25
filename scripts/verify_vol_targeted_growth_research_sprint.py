from __future__ import annotations

import csv
import math
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.vol_targeted_growth_research_sprint import (  # noqa: E402
    COMPLETE_STATUS,
    INCOMPLETE_STATUS,
    OUTPUT_FILES,
    SAFETY_FLAGS,
    STRONG_STATUS,
    generate_vol_targeted_growth_research_sprint,
    show_vol_targeted_growth_research_sprint,
)


EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_research_sprint.csv",
    "data/vol_targeted_growth_candidate_summary.csv",
    "data/vol_targeted_growth_rejected_candidates.csv",
    "data/vol_targeted_growth_robustness_audit.csv",
    "data/vol_targeted_growth_parameter_sensitivity.csv",
]

COMMANDS = [
    "--vol-targeted-growth-research-sprint",
    "--show-vol-targeted-growth-research-sprint",
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

TRUE_FLAGS = ["research_only", "report_only", "saved_output_only", "backtest_only", "never_schedule_order_capable_commands"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "vol_targeted_growth_research_sprint.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, failures)
    verify_fixture_generation(failures)

    if failures:
        print("Volatility-targeted growth research sprint verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Volatility-targeted growth research sprint verification passed.")
    print("Verified saved-stream research, distinct strong candidates, fragile exclusions, parameter sensitivity, display safety, and false approval flags.")
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
    for token in ["generate_vol_targeted_growth_research_sprint", "show_vol_targeted_growth_research_sprint"]:
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
        "Volatility Targeting Subagent",
        "Drawdown Control Subagent",
        "Growth Momentum + Risk Overlay Subagent",
        "Multi-Sleeve Risk Allocation Subagent",
        "Backtest Engineering",
        "Robustness/Audit",
        "vol_targeted_growth_research_two_or_more_strong_candidates_found",
        "vol_targeted_growth_research_incomplete_fewer_than_two_strong_candidates",
        "strong_vol_targeted_growth_candidate_research_only",
        "hidden_leverage_policy",
        "single_name_policy",
        "never_schedule_order_capable_commands",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
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

    show_body = source_slice(module_source, "def show_vol_targeted_growth_research_sprint", "def build_source_streams")
    if "write_rows" in show_body or "generate_vol_targeted_growth_research_sprint" in show_body:
        failures.append("show command must display saved outputs only and must not regenerate reports")


def verify_fixture_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        dates = [(date(2020, 1, 1) + timedelta(days=index)).isoformat() for index in range(760)]
        qqq_returns = synthetic_returns(len(dates), 0.00055, 0.006, shock_scale=1.8)
        high_growth_returns = synthetic_returns(len(dates), 0.00185, 0.020, shock_scale=2.7)
        top1_returns = synthetic_returns(len(dates), 0.00240, 0.045, shock_scale=3.5)
        crypto_returns = synthetic_returns(len(dates), 0.00120, 0.030, shock_scale=3.0)
        defensive_returns = synthetic_returns(len(dates), 0.00045, 0.005, shock_scale=1.5)

        write_stream(data / "qqq100_recovered_reference_stream.csv", dates, "qqq100_recovered_reference_stream", qqq_returns)
        write_stream(data / "high_growth_return_streams.csv", dates, "codex_broad_growth_balanced_breakout_control", high_growth_returns)
        append_stream(data / "high_growth_return_streams.csv", dates, "broad_growth_top1_reference", top1_returns)
        write_stream(data / "crypto_return_streams.csv", dates, "crypto_btc_eth_research_sleeve", crypto_returns)
        write_stream(data / "sleeve_return_streams.csv", dates, "qqq100_spy_sma200_regime_filter", defensive_returns)
        write_csv(
            data / "qqq100_recovered_reference_metrics.csv",
            ["cagr", "sharpe", "max_drawdown", "calmar"],
            [{"cagr": "16.9832", "sharpe": "1.0073", "max_drawdown": "-23.4576", "calmar": "0.724"}],
        )
        write_csv(data / "high_growth_return_stream_metrics.csv", ["candidate_name", "CAGR"], [{"candidate_name": "codex_broad_growth_balanced_breakout_control", "CAGR": "48.7"}])
        write_csv(data / "higher_growth_candidate_selection_summary.csv", ["summary_name", "summary_value"], [{"summary_name": "selected_candidate", "summary_value": "higher_growth_70_20_5_5"}])

        result = generate_vol_targeted_growth_research_sprint(root)
        status = summary_value(result.summary_rows, "final_research_status")
        if status not in {COMPLETE_STATUS, INCOMPLETE_STATUS}:
            failures.append(f"fixture should produce a known final status, got {status}")
        if not result.sprint_rows:
            failures.append("fixture should produce sprint candidate rows")
        if any(row["candidate_family"] == "high_growth_concentrated_vol_targeted" and row["final_candidate_status"] == STRONG_STATUS for row in result.sprint_rows):
            failures.append("concentrated Top1 source must not become a strong candidate")
        if not result.sensitivity_rows:
            failures.append("parameter sensitivity rows should be produced")

        for collection in [result.sprint_rows, result.summary_rows, result.rejected_rows, result.audit_rows, result.sensitivity_rows]:
            for row in collection:
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"expected false flag {flag} in output row")
                        return
                for flag in TRUE_FLAGS:
                    if str(row.get(flag, "")).lower() != "true":
                        failures.append(f"expected true flag {flag} in output row")
                        return
        code, lines = show_vol_targeted_growth_research_sprint(root)
        display = "\n".join(lines)
        if code != 0:
            failures.append(f"show command should succeed after generation, got {code}")
        for token in [status, "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display output missing token: {token}")


def synthetic_returns(count: int, drift: float, amplitude: float, shock_scale: float) -> list[float]:
    returns = []
    for index in range(count):
        wave = math.sin(index / 3.0) * amplitude
        shock = -amplitude * shock_scale if index in {180, 390, 610} else 0.0
        returns.append(drift + wave + shock)
    return returns


def write_stream(path: Path, dates: list[str], candidate_name: str, returns: list[float]) -> None:
    write_csv(
        path,
        ["date", "candidate_name", "daily_strategy_return", "research_only", "execution_approved"],
        [{"date": date, "candidate_name": candidate_name, "daily_strategy_return": value, "research_only": "True", "execution_approved": "False"} for date, value in zip(dates, returns)],
    )


def append_stream(path: Path, dates: list[str], candidate_name: str, returns: list[float]) -> None:
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "candidate_name", "daily_strategy_return", "research_only", "execution_approved"])
        writer.writerows([{"date": date, "candidate_name": candidate_name, "daily_strategy_return": value, "research_only": "True", "execution_approved": "False"} for date, value in zip(dates, returns)])


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
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
