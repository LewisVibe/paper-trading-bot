from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.multi_sleeve_allocation_policy import (  # noqa: E402
    CANDIDATE,
    CRYPTO_SLEEVE,
    HIGH_GROWTH_SLEEVE,
    OUTPUT_FILES,
    STATUS_BLOCKED_MISSING,
    generate_multi_sleeve_allocation_policy_review,
    show_multi_sleeve_allocation_policy_review,
)


EXPECTED_OUTPUTS = [
    "data/multi_sleeve_allocation_policy_review.csv",
    "data/multi_sleeve_allocation_policy_summary.csv",
    "data/multi_sleeve_allocation_policy_components.csv",
    "data/multi_sleeve_allocation_policy_blockers.csv",
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

TRUE_FLAGS = ["research_only", "preview_only", "saved_output_only"]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(ROOT / "bot.py")
    module_source = read_text(ROOT / "trading_bot" / "research" / "multi_sleeve_allocation_policy.py")

    verify_command_registration(bot_source, failures)
    verify_outputs_ignored(failures)
    verify_source_boundaries(module_source, bot_source, failures)
    verify_temp_generation(failures)
    verify_missing_inputs(failures)

    if failures:
        print("Multi-sleeve allocation policy review verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Multi-sleeve allocation policy review verification passed.")
    print("Verified saved-output-only allocation, component, blocker schemas, display safety, and false approval flags.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    for token in [
        "--multi-sleeve-allocation-policy-review",
        "--show-multi-sleeve-allocation-policy-review",
        "generate_multi_sleeve_allocation_policy_review",
        "show_multi_sleeve_allocation_policy_review",
    ]:
        if token not in bot_source:
            failures.append(f"bot.py missing allocation policy token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    normalized = [str(path).replace("\\", "/") for path in OUTPUT_FILES.values()]
    for expected in EXPECTED_OUTPUTS:
        if expected not in normalized:
            failures.append(f"module missing expected output filename: {expected}")
        if "data/*" not in gitignore:
            failures.append(f"generated output should remain ignored: {expected}")


def verify_source_boundaries(module_source: str, bot_source: str, failures: list[str]) -> None:
    required = [
        "allocation_policy_promising_research_only",
        "allocation_policy_promising_but_crypto_sensitive",
        "allocation_policy_promising_but_high_growth_sensitive",
        "allocation_policy_mixed_needs_weight_sweep",
        "allocation_policy_blocked_missing_saved_inputs",
        "qqq100_weight",
        "high_growth_weight",
        "crypto_weight",
        "defensive_weight",
        "growth_risk_weight_total",
        "speculative_weight_total",
        "risk_concentration_status",
        "concentration_warning",
        "high_growth_component_warning",
        "crypto_component_warning",
        CANDIDATE,
        HIGH_GROWTH_SLEEVE,
        CRYPTO_SLEEVE,
        "execution_approved",
        "crypto_execution_approved",
        "scheduling_approved",
    ]
    for token in required:
        if token not in module_source:
            failures.append(f"allocation policy module missing required token: {token}")

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
        "Register-ScheduledTask",
        "create_scheduled_task",
        "automation_update",
        "load_config",
        "config.json",
        "promotion-ready",
        "promotion_ready",
        "execution-ready",
        "execution_ready",
        "approved_for_execution",
    ]
    for token in forbidden:
        if token in module_source:
            failures.append(f"allocation policy module must not contain forbidden token: {token}")

    show_slice = source_slice(module_source, "def show_multi_sleeve_allocation_policy_review", "def missing_inputs")
    if "write_rows" in show_slice or "generate_multi_sleeve_allocation_policy_review" in show_slice:
        failures.append("allocation policy display command must be saved-read-only and must not regenerate outputs")

    route = source_slice(
        bot_source,
        'if sys.argv[1:] == ["--multi-sleeve-allocation-policy-review"]',
        'if sys.argv[1:] == ["--paper-execution-state-summary"]',
    )
    if "run_execute_qqq100_paper" in route or "run_paper_order_test" in route:
        failures.append("allocation policy route must not call execution commands")


def verify_temp_generation(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        write_fixture(root / "data")
        result = generate_multi_sleeve_allocation_policy_review(root)

        for path in OUTPUT_FILES.values():
            if not (root / path).exists():
                failures.append(f"expected generated output missing in temp dir: {path}")

        if not result.review_rows or not result.summary_rows or not result.component_rows or not result.blocker_rows:
            failures.append("allocation policy review should generate review, summary, component, and blocker rows")
            return

        review = result.review_rows[0]
        for column in [
            "qqq100_weight",
            "high_growth_weight",
            "crypto_weight",
            "defensive_weight",
            "growth_risk_weight_total",
            "speculative_weight_total",
            "risk_concentration_status",
            "concentration_warning",
            "candidate_delta_CAGR_vs_recovered_qqq100",
            "high_growth_component_warning",
            "crypto_component_warning",
            "sleeve_contribution_review_status",
        ]:
            if column not in review:
                failures.append(f"review row missing required column: {column}")

        if review.get("qqq100_weight") != "75" or review.get("high_growth_weight") != "15" or review.get("crypto_weight") != "5":
            failures.append("allocation weights should preserve the fixed 75/15/5/5 candidate")
        if "crypto_sensitive" not in str(review.get("allocation_policy_status", "")):
            failures.append("fixture should classify policy as crypto-sensitive research-only")

        components = {row.get("component_name") for row in result.component_rows}
        for expected in [
            "qqq100_core_trend_sleeve",
            "high_growth_stock_research_sleeve",
            "crypto_research_sleeve",
            "defensive_cash_or_bond_sleeve",
        ]:
            if expected not in components:
                failures.append(f"missing component row: {expected}")

        verify_safety_flags(result.review_rows + result.summary_rows + result.component_rows + result.blocker_rows, "generated", failures)

        code, lines = show_multi_sleeve_allocation_policy_review(root)
        output = "\n".join(lines)
        if code != 0:
            failures.append("saved display should return success when summary exists")
        for token in [
            "final allocation policy status",
            "current allocation",
            "candidate metrics",
            "component roles",
            "execution_approved=false",
            "crypto_execution_approved=false",
            "scheduling_approved=false",
        ]:
            if token not in output:
                failures.append(f"display missing expected token: {token}")


def verify_missing_inputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        result = generate_multi_sleeve_allocation_policy_review(root)
        summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if summary.get("final_allocation_policy_status") != STATUS_BLOCKED_MISSING:
            failures.append("missing saved inputs should block allocation policy review")
        if "missing_saved_inputs" not in {row.get("blocker_name") for row in result.blocker_rows}:
            failures.append("missing-input path should write a missing_saved_inputs blocker row")
        verify_safety_flags(result.review_rows + result.summary_rows + result.blocker_rows, "missing", failures)


def verify_safety_flags(rows: list[dict[str, object]], label: str, failures: list[str]) -> None:
    for index, row in enumerate(rows):
        for flag in TRUE_FLAGS:
            if str(row.get(flag, "")).lower() != "true":
                failures.append(f"{label} row {index} should keep {flag}=true")
        for flag in FALSE_FLAGS:
            if str(row.get(flag, "")).lower() != "false":
                failures.append(f"{label} row {index} should keep {flag}=false")


def write_fixture(data: Path) -> None:
    data.mkdir(parents=True, exist_ok=True)
    write_csv(
        data / "multi_sleeve_portfolio_backtest.csv",
        [
            {
                "portfolio_name": CANDIDATE,
                "candidate_cagr": "21.7328",
                "candidate_sharpe": "1.1852",
                "candidate_max_drawdown": "-22.2489",
                "candidate_calmar": "0.9768",
                "delta_cagr_vs_recovered_qqq100_reference": "4.7496",
                "delta_sharpe_vs_recovered_qqq100_reference": "0.1779",
                "delta_max_drawdown_vs_recovered_qqq100_reference": "1.2087",
                "delta_calmar_vs_recovered_qqq100_reference": "0.2528",
            }
        ],
    )
    write_csv(
        data / "multi_sleeve_crypto_review_summary.csv",
        [
            summary_row("final_crypto_review_status", "multi_sleeve_crypto_review_promising_research_only"),
            summary_row("crypto_volatility_drawdown_warnings", "crypto_high_volatility_and_drawdown_warning; candidate_drawdown_improves_vs_recovered_qqq100"),
        ],
    )
    write_csv(
        data / "high_growth_return_stream_metrics.csv",
        [
            {
                "candidate_name": HIGH_GROWTH_SLEEVE,
                "CAGR": "48.7551",
                "Sharpe": "1.186",
                "MaxDD": "-42.3324",
                "Calmar": "1.1517",
            }
        ],
    )
    write_csv(
        data / "crypto_return_stream_metrics.csv",
        [
            {
                "candidate_name": CRYPTO_SLEEVE,
                "CAGR": "37.0042",
                "Sharpe": "0.9127",
                "MaxDD": "-60.1453",
                "Calmar": "0.6152",
            }
        ],
    )
    write_csv(
        data / "qqq100_recovered_reference_metrics.csv",
        [
            {
                "reference_name": "qqq100_recovered_reference_stream",
                "cagr": "16.9832",
                "sharpe": "1.0073",
                "max_drawdown": "-23.4576",
                "calmar": "0.724",
            }
        ],
    )


def summary_row(name: str, value: str) -> dict[str, str]:
    return {"summary_name": name, "summary_value": value}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
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
