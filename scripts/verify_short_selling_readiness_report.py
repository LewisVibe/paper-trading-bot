from __future__ import annotations

import csv
import inspect
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.short_selling_readiness as readiness
from trading_bot.research.short_selling_readiness import generate_short_selling_readiness_report


FORBIDDEN_TERMS = [
    "yfinance",
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_simulated_positions",
    "decide_trade",
]


def main() -> int:
    failures: list[str] = []

    result = generate_short_selling_readiness_report(ROOT)
    if not result.output_path.exists():
        failures.append("short_selling_readiness_report.csv was not created")

    rows = {row["check_name"]: row for row in result.rows}
    for required in [
        "allow_shorting_default_false",
        "config_example_allow_shorting_false",
        "alpaca_paper_required",
        "normal_shorting_rules_gated",
        "slow_sma_long_only",
        "promoted_pipeline_long_flat_only",
        "crypto_shorting_disabled",
        "no_short_execution_command",
        "no_research_preview_short_approval",
        "docs_warn_short_risk",
    ]:
        if required not in rows:
            failures.append(f"missing readiness check: {required}")

    if rows.get("allow_shorting_default_false", {}).get("check_status") != "pass":
        failures.append("allow_shorting default false should be detected")
    if rows.get("config_example_allow_shorting_false", {}).get("check_status") != "pass":
        failures.append("config.example allow_shorting=false should be detected")
    if rows.get("crypto_shorting_disabled", {}).get("check_status") != "pass":
        failures.append("crypto shorting disabled should be detected")
    if rows.get("no_short_execution_command", {}).get("check_status") != "pass":
        failures.append("no short execution command check should pass")

    for row in result.rows:
        if row["research_only"] is not True or row["preview_only"] is not True or row["execution_approved"] is not False:
            failures.append(f"safety flags failed for {row['check_name']}")
    with result.output_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != readiness.SHORT_SELLING_READINESS_COLUMNS:
            failures.append("short-selling readiness columns changed unexpectedly")

    summary = "\n".join(result.summary_lines)
    if "SHORT SELLING READINESS REPORT. RESEARCH ONLY. NOT EXECUTION." not in summary:
        failures.append("readiness summary header missing")
    if "Short selling is not enabled and is not execution-approved." not in summary:
        failures.append("readiness summary should clearly deny short execution approval")

    help_result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    if "--short-selling-readiness-report" not in help_text:
        failures.append("command inventory should include --short-selling-readiness-report")
    for forbidden_command in readiness.DANGEROUS_SHORT_COMMAND_PATTERNS:
        if forbidden_command in help_text:
            failures.append(f"short execution-like command should not exist: {forbidden_command}")

    source = inspect.getsource(readiness)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"short-selling readiness report references forbidden term: {term}")

    if failures:
        print("Short-selling readiness report verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Short-selling readiness report verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
