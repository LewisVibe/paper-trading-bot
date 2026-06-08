from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.normal_bot_execution_policy as normal_bot_execution_policy
from trading_bot.research.normal_bot_execution_policy import (
    NORMAL_BOT_EXECUTION_POLICY_COLUMNS,
    generate_normal_bot_execution_policy_report,
)


EXPECTED_POLICY_AREAS = {
    "normal_bot_path_policy",
    "paper_order_test_policy",
    "slow_sma_paper_execution_policy",
    "future_defensive_execution_policy",
    "overall_policy",
    "execution_approval_policy",
}

EXPECTED_POLICY_STATUSES = {
    "normal_bot_path_policy": "deliberately_non_defensive_execution_path",
    "paper_order_test_policy": "explicit_confirmed_kill_switch_gated_path",
    "slow_sma_paper_execution_policy": "explicit_confirmed_kill_switch_gated_path",
    "future_defensive_execution_policy": "separate_command_required",
    "overall_policy": "option_a_keep_normal_bot_dry_run_first",
    "execution_approval_policy": "blocked_no_execution_approval",
}

FORBIDDEN_OUTPUT_COLUMNS = {
    "side",
    "quantity",
    "order_type",
    "order_id",
    "target_order",
    "submit" + "_order",
}

FORBIDDEN_SOURCE_TERMS = [
    "yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit" + "_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_simulated_positions",
    "decide_trade",
    "download_close_prices",
    "download_backtest_prices",
    "configure_yfinance_cache",
    "sqlite3",
]


def main() -> int:
    failures: list[str] = []
    verify_fixture_report(failures)
    verify_static_safety(failures)
    verify_command_registered(failures)

    if failures:
        print("Normal bot execution policy report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Normal bot execution policy report verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        write_fixture_files(root)
        result = generate_normal_bot_execution_policy_report(
            root_dir=root,
            created_at="2026-01-01T00:00:00+00:00",
        )
        if result.output_path.name != "normal_bot_execution_policy_report.csv":
            failures.append("output path should be normal_bot_execution_policy_report.csv")
        if not result.output_path.exists():
            failures.append("normal bot execution policy report CSV was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            fieldnames = csv.DictReader(file).fieldnames
        if fieldnames != NORMAL_BOT_EXECUTION_POLICY_COLUMNS:
            failures.append("normal bot execution policy columns changed unexpectedly")
        if FORBIDDEN_OUTPUT_COLUMNS.intersection(NORMAL_BOT_EXECUTION_POLICY_COLUMNS):
            failures.append("policy report schema contains order-instruction columns")

        areas = {row.get("policy_area") for row in result.rows}
        if areas != EXPECTED_POLICY_AREAS:
            failures.append(f"expected policy areas changed: {sorted(str(area) for area in areas)}")

        statuses = {row.get("policy_area"): row.get("policy_status") for row in result.rows}
        for area, expected in EXPECTED_POLICY_STATUSES.items():
            if statuses.get(area) != expected:
                failures.append(f"{area} should have policy_status={expected}")

        for row in result.rows:
            if row.get("research_only") is not True or row.get("preview_only") is not True or row.get("execution_approved") is not False:
                failures.append(f"safety flags failed for policy area {row.get('policy_area')}")

        summary = "\n".join(result.summary_lines)
        for expected in [
            "NORMAL BOT EXECUTION POLICY REPORT. SAVED-DATA/STATIC CHECK ONLY. NOT EXECUTION.",
            "Normal python bot.py remains deliberately separate from defensive paper execution.",
            "No execution design was added.",
            "No additional order paths were wired.",
            "No strategy was promoted.",
            "No orders were created, submitted, or cancelled.",
            "No execution approval was granted.",
            "normal_bot_execution_policy_report.csv",
        ]:
            if expected not in summary:
                failures.append(f"summary missing expected safety text: {expected}")


def verify_static_safety(failures: list[str]) -> None:
    source = inspect.getsource(normal_bot_execution_policy)
    for term in FORBIDDEN_SOURCE_TERMS:
        if term in source:
            failures.append(f"normal bot execution policy report references forbidden term: {term}")
    if "normal_bot_execution_policy_report.csv" not in source:
        failures.append("report source should reference output path")
    for expected in EXPECTED_POLICY_AREAS.union(set(EXPECTED_POLICY_STATUSES.values())):
        if expected not in source:
            failures.append(f"report source should mention policy label/status {expected}")
    for expected in [
        "Normal python bot.py remains separate from defensive paper execution",
        "separate scoped command",
    ]:
        if expected not in source:
            failures.append(f"report source should include wording: {expected}")


def verify_command_registered(failures: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (result.stdout or "") + "\n" + (result.stderr or "")
    if "--normal-bot-execution-policy-report" not in help_text:
        failures.append("command inventory should include --normal-bot-execution-policy-report")


def write_fixture_files(root: Path) -> None:
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "bot.py").write_text(
        "\n".join(
            [
                "def run_bot():",
                "    # --paper-order-test --confirm-paper-order",
                "    # --execute-slow-sma-paper --confirm-slow-sma-paper",
                "    pass",
                "",
                "def run_paper_order_test():",
                "    evaluate_paper_kill_switch_gate()",
                "    init_database()",
                "    TradingClient()",
                "    submit_alpaca_order()",
                "",
                "def estimate_manual_position_after():",
                "    pass",
                "",
                "def run_slow_sma_paper_execution():",
                "    evaluate_paper_kill_switch_gate()",
                "    configure_yfinance_cache()",
                "    init_database()",
                "    send_discord_alert()",
                "    TradingClient()",
                "    get_alpaca_positions()",
                "",
                "def validate_slow_sma_execution_safety():",
                "    pass",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_csv(
        root / "data" / "paper_execution_protection_report.csv",
        [
            {
                "execution_path": "manual_paper_order_test",
                "protection_status": "protected_by_kill_switch_preflight",
                "execution_approved": "False",
            },
            {
                "execution_path": "slow_sma_paper_execution",
                "protection_status": "protected_by_kill_switch_preflight",
                "execution_approved": "False",
            },
            {
                "execution_path": "normal_bot_order_path",
                "protection_status": "deliberately_unchanged_future_work",
                "execution_approved": "False",
            },
        ],
    )
    write_csv(
        root / "data" / "defensive_execution_readiness_report.csv",
        [
            {
                "readiness_area": "overall_readiness",
                "readiness_status": "blocked",
                "execution_approved": "False",
            }
        ],
    )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
