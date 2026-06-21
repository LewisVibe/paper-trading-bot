from __future__ import annotations

import csv
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_crypto_review import (  # noqa: E402
    CANDIDATE,
    CRYPTO_SLEEVE,
    HIGH_GROWTH_CANDIDATE,
    HIGH_GROWTH_SLEEVE,
    OUTPUT_FILES,
    RECOVERED_REFERENCE,
    STATUS_BLOCKED_MISSING_STREAMS,
    STATUS_COST_SENSITIVE,
    STATUS_MIXED,
    STATUS_PROMISING,
    STATUS_VOLATILITY_BLOCKED,
    generate_multi_sleeve_crypto_review,
    show_multi_sleeve_crypto_review,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_crypto_review.csv",
    "data/multi_sleeve_crypto_review_summary.csv",
    "data/multi_sleeve_crypto_review_cost_stress.csv",
    "data/multi_sleeve_crypto_review_split_robustness.csv",
    "data/multi_sleeve_crypto_review_volatility.csv",
]

VALID_FINAL_STATUSES = {
    STATUS_PROMISING,
    STATUS_MIXED,
    STATUS_COST_SENSITIVE,
    STATUS_VOLATILITY_BLOCKED,
    STATUS_BLOCKED_MISSING_STREAMS,
}

FALSE_FLAGS = [
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
    "paper_execution_approved",
    "crypto_execution_approved",
    "scheduling_approved",
    "live_trading_approved",
]

TRUE_FLAGS = ["research_only", "preview_only", "saved_output_only"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_crypto_review.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_streams_blocked(failures)

    if failures:
        print("Multi-sleeve crypto review verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Multi-sleeve crypto review verification passed.")
    print("Verified saved-output-only split, cost, volatility review, display safety, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-crypto-review",
        "--show-multi-sleeve-crypto-review",
        "generate_multi_sleeve_crypto_review",
        "show_multi_sleeve_crypto_review",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing multi-sleeve crypto review token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, bot_source: str, failures: list[str]) -> None:
    required = [
        "multi_sleeve_crypto_review_promising_research_only",
        "multi_sleeve_crypto_review_mixed_split_sensitive",
        "multi_sleeve_crypto_review_cost_sensitive",
        "multi_sleeve_crypto_review_volatility_blocked",
        "multi_sleeve_crypto_review_blocked_missing_saved_streams",
        CANDIDATE,
        HIGH_GROWTH_CANDIDATE,
        RECOVERED_REFERENCE,
        CRYPTO_SLEEVE,
        "split_60_40",
        "split_70_30",
        "split_80_20",
        "plus_100bps_crypto_turnover",
        "crypto_high_volatility_and_drawdown_warning",
        "execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"multi-sleeve crypto review module missing required token: {token}")

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
        "subprocess.run",
        "create_scheduled_task",
        "automation_update",
        "load_config",
        "promotion-ready",
        "promotion_ready",
        "execution-ready",
        "execution_ready",
        "approved_for_execution",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"multi-sleeve crypto review module must not contain forbidden token: {token}")

    show_slice = source_slice(module_source, "def show_multi_sleeve_crypto_review", "def build_saved_stream_rows")
    if "write_rows" in show_slice or "generate_multi_sleeve_crypto_review" in show_slice:
        failures.append("display command must be saved-read-only and must not regenerate outputs")

    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--multi-sleeve-crypto-review"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("multi-sleeve crypto review route must not call execution commands")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture_files(root)
        result = generate_multi_sleeve_crypto_review(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.summary_rows or not result.split_rows or not result.cost_rows or not result.volatility_rows:
            failures.append("review should generate summary, split, cost, and volatility rows")
            return

        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        final_status = summary.get("final_crypto_review_status")
        if final_status not in VALID_FINAL_STATUSES:
            failures.append(f"unexpected final status: {final_status}")

        for rows, name in [
            (result.review_rows, "review"),
            (result.summary_rows, "summary"),
            (result.split_rows, "split"),
            (result.cost_rows, "cost"),
            (result.volatility_rows, "volatility"),
        ]:
            verify_safety_flags(rows, name, failures)

        split_names = {row.get("split_name") for row in result.split_rows}
        for expected in {"split_60_40", "split_70_30", "split_80_20"}:
            if expected not in split_names:
                failures.append(f"missing split robustness row: {expected}")

        split_candidates = {row.get("candidate_name") for row in result.split_rows}
        for expected in {CANDIDATE, HIGH_GROWTH_CANDIDATE, RECOVERED_REFERENCE, CRYPTO_SLEEVE}:
            if expected not in split_candidates:
                failures.append(f"missing split candidate/context row: {expected}")

        cost_names = {row.get("cost_stress_name") for row in result.cost_rows}
        for expected in {"baseline_saved_costs", "plus_10bps_crypto_turnover", "plus_25bps_crypto_turnover", "plus_50bps_crypto_turnover", "plus_100bps_crypto_turnover"}:
            if expected not in cost_names:
                failures.append(f"missing cost stress row: {expected}")

        if not all(row.get("approximation_status") == "crypto_exposure_change_proxy_from_saved_signal_state" for row in result.cost_rows):
            failures.append("cost rows should disclose crypto exposure-change proxy approximation")

        volatility = result.volatility_rows[0]
        if "warning" not in str(volatility.get("crypto_volatility_warning", "")):
            failures.append("volatility row should preserve a crypto volatility/drawdown warning")

        code, lines = show_multi_sleeve_crypto_review(root)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        display = "\n".join(lines)
        for token in ["final crypto review status", "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display missing expected token: {token}")


def verify_missing_streams_blocked(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_multi_sleeve_crypto_review(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_crypto_review_status") != STATUS_BLOCKED_MISSING_STREAMS:
            failures.append("missing saved streams should block crypto review")
        if not all(row.get("split_status", "").startswith("missing_saved_streams=") for row in result.split_rows):
            failures.append("missing-stream split rows should explain missing streams")
        verify_safety_flags(result.summary_rows + result.review_rows, "blocked", failures)


def verify_safety_flags(rows: list[dict[str, object]], label: str, failures: list[str]) -> None:
    for index, row in enumerate(rows):
        for flag in TRUE_FLAGS:
            if str(row.get(flag, "")).lower() != "true":
                failures.append(f"{label} row {index} should keep {flag}=true")
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).lower() != "false":
                failures.append(f"{label} row {index} should keep {flag}=false")


def write_fixture_files(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    dates = [(date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(300)]
    write_stream(data / "sleeve_return_streams.csv", "cash_default_defensive_sleeve", dates, lambda _i: 0.0)
    write_stream(
        data / "high_growth_return_streams.csv",
        HIGH_GROWTH_SLEEVE,
        dates,
        lambda i: -0.035 if i in {95, 96, 97} else 0.0009,
    )
    write_crypto_stream(data / "crypto_return_streams.csv", dates)
    write_recovered_stream(data / "qqq100_recovered_reference_stream.csv", dates)
    write_csv(
        data / "crypto_return_stream_metrics.csv",
        [
            {
                "candidate_name": CRYPTO_SLEEVE,
                "MaxDD": "-60.1453",
                "annual_volatility": "72.0000",
                "CAGR": "37.0042",
                "Sharpe": "0.9127",
                "Calmar": "0.6152",
                **false_flags_as_strings(),
            }
        ],
    )
    write_csv(
        data / "qqq100_recovered_reference_metrics.csv",
        [
            {
                "reference_name": RECOVERED_REFERENCE,
                "reference_status": "qqq100_reconstruction_close_enough_for_research_review",
                "gap_threshold_status": "all_metric_gaps_within_research_review_thresholds",
                "cagr": "16.9832",
                "sharpe": "1.0073",
                "max_drawdown": "-23.4576",
                "calmar": "0.724",
                "annual_volatility": "16.5000",
                "cash_percentage": "0",
                "trade_signal_change_count": "12",
                **false_flags_as_strings(),
            }
        ],
    )
    write_csv(
        data / "multi_sleeve_portfolio_backtest.csv",
        [
            {
                "portfolio_name": CANDIDATE,
                "candidate_cagr": "21.7328",
                "candidate_sharpe": "1.1852",
                "candidate_max_drawdown": "-22.2489",
                "candidate_calmar": "0.9768",
            }
        ],
    )


def write_stream(path: Path, candidate_name: str, dates: list[str], return_for_index) -> None:
    rows = [
        {
            "date": day,
            "candidate_name": candidate_name,
            "daily_strategy_return": str(return_for_index(index)),
            **false_flags_as_strings(),
        }
        for index, day in enumerate(dates)
    ]
    write_csv(path, rows)


def write_crypto_stream(path: Path, dates: list[str]) -> None:
    rows = []
    for index, day in enumerate(dates):
        daily_return = -0.08 if index in {60, 61, 140} else 0.0015
        rows.append(
            {
                "date": day,
                "sleeve_name": CRYPTO_SLEEVE,
                "daily_return": str(daily_return),
                "signal_state": "invested" if (index // 35) % 2 == 0 else "cash",
                **false_flags_as_strings(),
            }
        )
    write_csv(path, rows)


def write_recovered_stream(path: Path, dates: list[str]) -> None:
    rows = [
        {
            "date": day,
            "candidate_name": RECOVERED_REFERENCE,
            "daily_strategy_return": str(-0.02 if index in {85, 86} else 0.00055),
            "reference_status": "qqq100_reconstruction_close_enough_for_research_review",
            **false_flags_as_strings(),
        }
        for index, day in enumerate(dates)
    ]
    write_csv(path, rows)


def false_flags_as_strings() -> dict[str, str]:
    return {
        "orders_created": "false",
        "orders_submitted": "false",
        "orders_cancelled": "false",
        "orders_replaced": "false",
        "alpaca_called": "false",
        "live_position_read": "false",
        "sqlite_trade_log_written": "false",
        "discord_alert_sent": "false",
        "telegram_alert_sent": "false",
        "execution_approved": "false",
        "paper_execution_approved": "false",
        "crypto_execution_approved": "false",
        "scheduling_approved": "false",
        "live_trading_approved": "false",
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def source_slice(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index == -1:
        return ""
    end_index = source.find(end, start_index + len(start))
    return source[start_index:] if end_index == -1 else source[start_index:end_index]


if __name__ == "__main__":
    raise SystemExit(main())
