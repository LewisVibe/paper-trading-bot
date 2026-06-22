from __future__ import annotations

import csv
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_crypto_containment import (  # noqa: E402
    BTC_SLEEVE,
    CRYPTO_SLEEVE,
    ETH_SLEEVE,
    OUTPUT_FILES,
    SELECTED_LEAD,
    STATUS_BLOCKED,
    STATUS_VOL_SENSITIVE,
    generate_multi_sleeve_crypto_containment_review,
    show_multi_sleeve_crypto_containment_review,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_crypto_containment_review.csv",
    "data/multi_sleeve_crypto_containment_summary.csv",
    "data/multi_sleeve_crypto_containment_drawdowns.csv",
    "data/multi_sleeve_crypto_containment_blockers.csv",
]

FALSE_FLAGS = [
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "orders_replaced",
    "alpaca_called",
    "yfinance_called",
    "live_position_read",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
    "execution_approved",
    "paper_execution_approved",
    "crypto_execution_approved",
    "live_trading_approved",
    "scheduling_approved",
    "shorting_approved",
    "leverage_approved",
    "margin_approved",
]

TRUE_FLAGS = ["research_only", "preview_only", "saved_output_only"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_crypto_containment.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_inputs_blocked(failures)

    if failures:
        print("Multi-sleeve crypto containment verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Multi-sleeve crypto containment verification passed.")
    print("Verified saved-output-only containment, drawdown contribution, weight sensitivity, standalone drawdowns, display, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-crypto-containment-review",
        "--show-multi-sleeve-crypto-containment-review",
        "generate_multi_sleeve_crypto_containment_review",
        "show_multi_sleeve_crypto_containment_review",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing crypto containment token: {token}")


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
        "crypto_containment_5pct_acceptable_research_only",
        "crypto_containment_5pct_promising_but_vol_sensitive",
        "crypto_containment_reduce_or_pause_manual_review",
        "crypto_containment_blocked_missing_saved_streams",
        SELECTED_LEAD,
        CRYPTO_SLEEVE,
        BTC_SLEEVE,
        ETH_SLEEVE,
        "ltc_paused_not_active",
        "crypto_weight_in_selected_lead",
        "crypto_weighted_contribution",
        "crypto_share_of_period_loss",
        "no_crypto_80_15_0_5",
        "higher_crypto_73_15_7_5",
        "standalone_crypto_drawdown",
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"crypto containment module missing required token: {token}")

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
        "config.json",
        "promotion-ready",
        "promotion_ready",
        "execution-ready",
        "execution_ready",
        "order-ready",
        "order_ready",
        "crypto-execution-ready",
        "crypto_execution_ready",
        "approved_for_execution",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"crypto containment module must not contain forbidden token: {token}")

    approval_clean = module_source
    for allowed in [
        "execution_approved",
        "paper_execution_approved",
        "crypto_execution_approved",
        "live_trading_approved",
        "scheduling_approved",
        "shorting_approved",
        "leverage_approved",
        "margin_approved",
    ]:
        approval_clean = approval_clean.replace(allowed, "")
    if "approved" in approval_clean.lower():
        failures.append("approved wording should only appear in explicit false approval fields")

    show_slice = source_slice(module_source, "def show_multi_sleeve_crypto_containment_review", "def missing_inputs")
    if "write_rows" in show_slice or "generate_multi_sleeve_crypto_containment_review" in show_slice:
        failures.append("display command must be saved-read-only and must not regenerate outputs")

    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--multi-sleeve-crypto-containment-review"]',
        'if sys.argv[1:] == ["--show-current-research-state"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("crypto containment route must not call execution commands")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture_files(root)
        result = generate_multi_sleeve_crypto_containment_review(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.review_rows or not result.summary_rows or not result.drawdown_rows or not result.blocker_rows:
            failures.append("containment review should generate review, summary, drawdown, and blocker rows")
            return

        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_crypto_containment_status") != STATUS_VOL_SENSITIVE:
            failures.append(f"fixture should classify as vol-sensitive, got {summary.get('final_crypto_containment_status')}")
        if summary.get("selected_lead_candidate") != SELECTED_LEAD:
            failures.append("selected lead candidate should be included in summary")
        if summary.get("crypto_weight") != "5":
            failures.append("selected lead crypto weight should be 5")
        if CRYPTO_SLEEVE not in summary.get("combined_crypto_sleeve_metrics", ""):
            failures.append("combined BTC/ETH crypto sleeve should appear in summary")
        if "no_crypto_80_15_0_5" not in summary.get("no_crypto_vs_higher_crypto_sensitivity", ""):
            failures.append("no-crypto sensitivity should be included")
        if "higher_crypto_73_15_7_5" not in summary.get("no_crypto_vs_higher_crypto_sensitivity", ""):
            failures.append("higher-crypto sensitivity should be included")

        standalone_sleeves = {row.get("sleeve_name") for row in result.drawdown_rows if row.get("row_type") == "standalone_crypto_drawdown"}
        for expected in {CRYPTO_SLEEVE, BTC_SLEEVE, ETH_SLEEVE}:
            if expected not in standalone_sleeves:
                failures.append(f"missing standalone crypto drawdown row: {expected}")

        contribution = next((row for row in result.drawdown_rows if row.get("row_type") == "selected_lead_worst_period_contribution"), {})
        for field in ["period_start", "period_trough", "crypto_period_return", "crypto_weighted_contribution", "total_period_return", "crypto_share_of_period_loss"]:
            if field not in contribution:
                failures.append(f"drawdown contribution row missing field: {field}")

        verify_safety_flags(result.review_rows + result.summary_rows + result.drawdown_rows, "generated", failures)
        for row in result.blocker_rows:
            for flag in ["execution_approved", "paper_execution_approved", "crypto_execution_approved", "scheduling_approved"]:
                if str(row.get(flag, "")).lower() != "false":
                    failures.append(f"blocker row should keep {flag}=false")

        code, lines = show_multi_sleeve_crypto_containment_review(root)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        display = "\n".join(lines)
        for token in ["final crypto containment status", "crypto weight", "standalone crypto drawdown summary", "execution_approved=false", "scheduling_approved=false"]:
            if token not in display:
                failures.append(f"display missing expected token: {token}")


def verify_missing_inputs_blocked(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_multi_sleeve_crypto_containment_review(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_crypto_containment_status") != STATUS_BLOCKED:
            failures.append("missing saved streams should block crypto containment review")
        if not any(row.get("blocker_name") == "saved_output_completeness" for row in result.blocker_rows):
            failures.append("missing input path should write saved-output completeness blocker")
        verify_safety_flags(result.review_rows + result.summary_rows + result.drawdown_rows, "blocked", failures)


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
    dates = [(date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(260)]
    write_crypto_stream(data / "crypto_return_streams.csv", dates)
    write_csv(
        data / "crypto_return_stream_metrics.csv",
        [
            metric_row(BTC_SLEEVE, "45.9331", "0.9979", "-73.0752", "0.6286"),
            metric_row(ETH_SLEEVE, "38.3233", "0.8614", "-71.6092", "0.5352"),
            metric_row(CRYPTO_SLEEVE, "37.0042", "0.9127", "-60.1453", "0.6152"),
        ],
    )
    write_csv(
        data / "multi_sleeve_weight_sensitivity.csv",
        [
            weight_row("current_75_15_5_5", 75, 15, 5, 5, "21.7328", "1.1852", "-22.2489", "0.9768", "0.0", "0.0"),
            weight_row("no_crypto_80_15_0_5", 80, 15, 0, 5, "21.1246", "1.1428", "-22.0191", "0.9594", "-0.6082", "0.2298"),
            weight_row("higher_crypto_73_15_7_5", 73, 15, 7, 5, "21.9623", "1.1981", "-22.6454", "0.9698", "0.2295", "-0.3965"),
            weight_row(SELECTED_LEAD, 70, 20, 5, 5, "23.6634", "1.2232", "-22.5209", "1.0507", "1.9306", "-0.272"),
        ],
    )
    write_csv(
        data / "multi_sleeve_lead_state_summary.csv",
        [
            {"summary_name": "lead_state_status", "summary_value": "higher_growth_selected_manual_review_required", **false_flags_as_strings()},
            {"summary_name": "current_research_lead_candidate", "summary_value": SELECTED_LEAD, **false_flags_as_strings()},
        ],
    )
    write_csv(
        data / "multi_sleeve_high_growth_drawdown_decomposition.csv",
        [
            {
                "row_type": "period_contribution",
                "period_start": "2020-02-19",
                "period_trough": "2020-03-20",
                "allocation_name": SELECTED_LEAD,
                "crypto_weight": "5.0",
                "crypto_period_return": "-32.5965",
                "crypto_weighted_contribution": "-1.6298",
                "total_period_return": "-22.2142",
                **false_flags_as_strings(),
            }
        ],
    )
    write_csv(
        data / "multi_sleeve_crypto_review.csv",
        [{"review_status": "multi_sleeve_crypto_review_promising_research_only", **false_flags_as_strings()}],
    )


def metric_row(sleeve: str, cagr: str, sharpe: str, maxdd: str, calmar: str) -> dict[str, str]:
    return {
        "sleeve_name": sleeve,
        "candidate_name": sleeve,
        "CAGR": cagr,
        "Sharpe": sharpe,
        "MaxDD": maxdd,
        "Calmar": calmar,
        "warning_status": "crypto_high_volatility_and_drawdown_warning",
        **false_flags_as_strings(),
    }


def weight_row(candidate: str, qqq: int, growth: int, crypto: int, defensive: int, cagr: str, sharpe: str, maxdd: str, calmar: str, delta_cagr: str, delta_maxdd: str) -> dict[str, str]:
    return {
        "candidate_name": candidate,
        "qqq100_weight": str(qqq),
        "high_growth_weight": str(growth),
        "crypto_weight": str(crypto),
        "defensive_weight": str(defensive),
        "CAGR": cagr,
        "Sharpe": sharpe,
        "MaxDD": maxdd,
        "Calmar": calmar,
        "delta_CAGR_vs_current_75_15_5_5": delta_cagr,
        "delta_MaxDD_vs_current_75_15_5_5": delta_maxdd,
        **false_flags_as_strings(),
    }


def write_crypto_stream(path: Path, dates: list[str]) -> None:
    rows = []
    for sleeve in [BTC_SLEEVE, ETH_SLEEVE, CRYPTO_SLEEVE]:
        for index, day in enumerate(dates):
            if sleeve == BTC_SLEEVE:
                daily_return = -0.07 if 70 <= index <= 78 else 0.0015
            elif sleeve == ETH_SLEEVE:
                daily_return = -0.065 if 80 <= index <= 88 else 0.0014
            else:
                daily_return = -0.055 if 75 <= index <= 85 else 0.0012
            rows.append(
                {
                    "date": day,
                    "sleeve_name": sleeve,
                    "candidate_name": sleeve,
                    "daily_return": str(daily_return),
                    "daily_strategy_return": str(daily_return),
                    **false_flags_as_strings(),
                }
            )
    write_csv(path, rows)


def false_flags_as_strings() -> dict[str, str]:
    return {
        "orders_created": "false",
        "orders_submitted": "false",
        "orders_cancelled": "false",
        "orders_replaced": "false",
        "alpaca_called": "false",
        "yfinance_called": "false",
        "live_position_read": "false",
        "sqlite_trade_log_written": "false",
        "discord_alert_sent": "false",
        "telegram_alert_sent": "false",
        "execution_approved": "false",
        "paper_execution_approved": "false",
        "crypto_execution_approved": "false",
        "live_trading_approved": "false",
        "scheduling_approved": "false",
        "shorting_approved": "false",
        "leverage_approved": "false",
        "margin_approved": "false",
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
