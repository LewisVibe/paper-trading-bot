from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.crypto_return_streams import (  # noqa: E402
    BTC_SLEEVE,
    COMBINED_SLEEVE,
    ETH_SLEEVE,
    OUTPUT_FILES,
    STATUS_CREATED_RESEARCH_ONLY,
    generate_crypto_return_streams,
    show_crypto_return_streams,
)
from trading_bot.research.multi_sleeve_portfolio_backtest import (  # noqa: E402
    generate_multi_sleeve_portfolio_backtest,
)


EXPECTED_OUTPUTS = [
    "data/crypto_return_streams.csv",
    "data/crypto_return_stream_metrics.csv",
    "data/crypto_return_stream_summary.csv",
    "data/crypto_return_stream_blockers.csv",
]

REQUIRED_STREAM_COLUMNS = [
    "date",
    "sleeve_name",
    "sleeve_family",
    "symbol",
    "daily_return",
    "equity",
    "exposure",
    "invested_flag",
    "source_strategy",
    "source_status",
    "research_status",
    "warning_status",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
    "scheduling_approved",
]

REQUIRED_METRIC_COLUMNS = [
    "CAGR",
    "Sharpe",
    "MaxDD",
    "Calmar",
    "row_count",
    "first_date",
    "last_date",
    "invested_pct",
    "trade_count",
    "exposure_change_count",
    "source_status",
    "research_status",
    "warning_status",
    "required_next_step",
    "execution_approved",
    "scheduling_approved",
]

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


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "crypto_return_streams.py")
    backtest_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_portfolio_backtest.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, backtest_source, failures)
    verify_display_saved_read_only(failures)
    verify_temp_generation(failures)

    if failures:
        print("Crypto return streams verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto return streams verification passed.")
    print("Verified BTC/ETH research streams, LTC pause, multi-sleeve consumption, schemas, and false execution/scheduling flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--crypto-return-streams",
        "--show-crypto-return-streams",
        "generate_crypto_return_streams",
        "show_crypto_return_streams",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing crypto return stream token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized_outputs = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized_outputs:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, backtest_source: str, failures: list[str]) -> None:
    required = [
        "btc_trend_vol_gate_research_sleeve",
        "eth_trend_research_sleeve",
        "crypto_btc_eth_research_sleeve",
        "paused_ltc_diagnostic",
        "crypto_buy_above_200_with_vol_gate",
        "crypto_buy_above_200_exit_below_200",
        "crypto_taker_fee_bps",
        "crypto_spread_bps",
        "crypto_slippage_bps",
        "configure_yfinance_cache_location",
        "execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"crypto return stream module missing required token: {token}")

    backtest_required = [
        "crypto_return_streams.csv",
        "normalize_crypto_stream_rows",
        "crypto_btc_eth_research_sleeve",
        "qqq100_plus_high_growth_plus_crypto_research",
        "multi_sleeve_crypto_candidate_promising_research_only",
        "multi_sleeve_crypto_candidate_mixed_research_only",
        "multi_sleeve_crypto_candidate_not_better_than_existing",
        "multi_sleeve_crypto_candidate_blocked_missing_streams",
    ]
    for token in backtest_required:
        if token not in backtest_source:
            failures.append(f"multi-sleeve backtest missing crypto integration token: {token}")

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
        "create_scheduled_task",
        "automation_update",
        "load_config",
        "run_execute_qqq100_paper",
        "run_paper_order_test",
        "promotion-ready",
        "execution-ready",
        "promotion_ready",
        "execution_ready",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"crypto return stream module must not contain forbidden token: {token}")


def verify_display_saved_read_only(failures: list[str]) -> None:
    from trading_bot.research import crypto_return_streams as module

    source = inspect.getsource(module.show_crypto_return_streams)
    for token in ["generate_crypto_return_streams", "download_crypto_daily_history", "yfinance", "write_rows", "configure_yfinance_cache_location"]:
        if token in source:
            failures.append(f"display helper should not refresh or write data: {token}")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_price_fixture(root / "data" / "crypto_return_stream_price_fixture.csv")
        write_sleeve_stream_fixture(root / "data" / "sleeve_return_streams.csv")
        write_high_growth_stream_fixture(root / "data" / "high_growth_return_streams.csv")
        write_project_state_fixture(root / "data" / "project_research_state_summary.csv")
        write_recovered_reference_fixture(root)
        result = generate_crypto_return_streams(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.stream_rows:
            failures.append("fixture should generate crypto stream rows")
            return
        if not result.metric_rows:
            failures.append("fixture should generate crypto metric rows")
            return

        for column in REQUIRED_STREAM_COLUMNS:
            if column not in result.stream_rows[0]:
                failures.append(f"stream output missing required column: {column}")
        for column in REQUIRED_METRIC_COLUMNS:
            if column not in result.metric_rows[0]:
                failures.append(f"metric output missing required column: {column}")

        candidates = {row.get("candidate_name") for row in result.metric_rows}
        for expected in [BTC_SLEEVE, ETH_SLEEVE, COMBINED_SLEEVE]:
            if expected not in candidates:
                failures.append(f"expected crypto candidate missing: {expected}")
        if any("ltc" in str(row.get("candidate_name", "")).lower() for row in result.stream_rows):
            failures.append("LTC should not be emitted as an active stream")

        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_stream_status") != STATUS_CREATED_RESEARCH_ONLY:
            failures.append("fixture should produce research-only created stream status")
        if "paused_ltc_diagnostic" not in summary.get("ltc_status", ""):
            failures.append("summary should preserve paused LTC diagnostic context")

        for collection in [result.stream_rows, result.metric_rows, result.summary_rows, result.blocker_rows]:
            for row in collection:
                if str(row.get("research_only", "")).lower() != "true":
                    failures.append("research_only should remain true")
                if str(row.get("preview_only", "")).lower() != "true":
                    failures.append("preview_only should remain true")
                for flag in FALSE_FLAGS:
                    if str(row.get(flag, "")).lower() != "false":
                        failures.append(f"{flag} should remain false")

        code, lines = show_crypto_return_streams(root)
        if code != 0 or not any("final crypto stream status" in line for line in lines):
            failures.append("saved display should show final stream status")
        if not any("execution_approved=false" in line for line in lines):
            failures.append("saved display should preserve false execution flag")

        backtest = generate_multi_sleeve_portfolio_backtest(root)
        sleeve_by_name = {row["sleeve_name"]: row for row in backtest.sleeve_rows}
        crypto_sleeve = sleeve_by_name.get("crypto_research_sleeve", {})
        if crypto_sleeve.get("return_stream_status") != "saved_return_stream_metrics_available":
            failures.append("multi-sleeve backtest should consume saved crypto return streams")
        names = {row["portfolio_name"] for row in backtest.backtest_rows}
        if "qqq100_plus_high_growth_plus_crypto_research" not in names:
            failures.append("multi-sleeve backtest should include high-growth plus crypto candidate")
        crypto_candidate = next((row for row in backtest.backtest_rows if row["portfolio_name"] == "qqq100_plus_high_growth_plus_crypto_research"), {})
        if crypto_candidate.get("data_quality") != "saved_return_stream_metrics_available":
            failures.append("high-growth plus crypto candidate should be computed from saved streams")
        if crypto_candidate.get("final_backtest_status") not in {
            "multi_sleeve_crypto_candidate_promising_research_only",
            "multi_sleeve_crypto_candidate_mixed_research_only",
            "multi_sleeve_crypto_candidate_not_better_than_existing",
        }:
            failures.append("crypto candidate should use explicit research-only crypto status")
        warnings = {row["summary_name"]: row["summary_value"] for row in backtest.summary_rows}.get("missing_sleeve_data_warnings", "")
        if "crypto" in warnings:
            failures.append("multi-sleeve warnings should not label crypto missing when stream exists")


def write_price_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    start = date(2023, 1, 1)
    rows = []
    btc = 100.0
    eth = 50.0
    for index in range(420):
        current = start + timedelta(days=index)
        btc *= 1.004 if index % 17 else 0.98
        eth *= 1.003 if index % 19 else 0.975
        rows.append([current.isoformat(), "BTC-USD", round(btc, 6)])
        rows.append([current.isoformat(), "ETH-USD", round(eth, 6)])
    write_fixture(path, ["date", "symbol", "close"], rows)


def write_sleeve_stream_fixture(path: Path) -> None:
    headers = ["date", "candidate_name", "daily_strategy_return", "signal_state"]
    candidates = {
        "qqq_100_trend_gate": [0.010, -0.004, 0.006, -0.002, 0.005, -0.003, 0.004, 0.002],
        "cash_default_defensive_sleeve": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "qqq100_combined_trend_spy_regime_drawdown_gate": [0.004, 0.0, 0.003, 0.0, 0.003, 0.0, 0.002, 0.001],
        "codex_qqq_calmar_optimised_defensive_gate_sleeve": [0.005, -0.001, 0.003, 0.0, 0.002, 0.0, 0.002, 0.001],
    }
    rows: list[list[str]] = []
    for day_index in range(8):
        current_date = f"2024-01-{day_index + 2:02d}"
        for candidate, returns in candidates.items():
            rows.append([current_date, candidate, str(returns[day_index]), "risk_on"])
    write_fixture(path, headers, rows)


def write_high_growth_stream_fixture(path: Path) -> None:
    rows = []
    returns = [0.012, -0.003, 0.007, -0.001, 0.006, -0.002, 0.005, 0.003]
    for day_index, value in enumerate(returns):
        rows.append([f"2024-01-{day_index + 2:02d}", "codex_broad_growth_balanced_breakout_control", str(value), "risk_on"])
    write_fixture(path, ["date", "candidate_name", "daily_strategy_return", "signal_state"], rows)


def write_project_state_fixture(path: Path) -> None:
    write_fixture(
        path,
        ["metric_name", "metric_value", "evidence"],
        [["stock_etf_clean_main_lead", "qqq_100_trend_gate", "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718"]],
    )


def write_recovered_reference_fixture(root: Path) -> None:
    write_fixture(
        root / "data" / "qqq100_recovered_reference_metrics.csv",
        [
            "reference_name",
            "source_candidate_name",
            "reference_status",
            "gap_threshold_status",
            "cagr",
            "sharpe",
            "max_drawdown",
            "calmar",
            "annual_volatility",
            "cash_percentage",
            "trade_signal_change_count",
            "execution_approved",
            "scheduling_approved",
            "orders_created",
            "orders_submitted",
            "orders_cancelled",
        ],
        [[
            "qqq100_recovered_reference_stream",
            "qqq100_recovered_inputs_sma200_close_to_close_10bps",
            "qqq100_reconstruction_close_enough_for_research_review",
            "all_metric_gaps_within_research_review_thresholds",
            "16.9832",
            "1.0073",
            "-23.4576",
            "0.724",
            "18.0",
            "35",
            "22",
            "false",
            "false",
            "false",
            "false",
            "false",
        ]],
    )
    rows = []
    returns = [0.011, -0.003, 0.007, -0.001, 0.006, -0.002, 0.005, 0.003]
    for day_index, value in enumerate(returns):
        rows.append([
            f"2024-01-{day_index + 2:02d}",
            "qqq100_recovered_reference_stream",
            "qqq100_reconstruction_close_enough_for_research_review",
            str(value),
            "risk_on",
            "false",
            "false",
            "false",
            "false",
            "false",
        ])
    write_fixture(
        root / "data" / "qqq100_recovered_reference_stream.csv",
        ["date", "candidate_name", "reference_status", "daily_strategy_return", "signal_state", "execution_approved", "scheduling_approved", "orders_created", "orders_submitted", "orders_cancelled"],
        rows,
    )


def write_fixture(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
