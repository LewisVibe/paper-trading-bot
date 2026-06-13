from __future__ import annotations

import csv
import inspect
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.qqq_adaptive_leverage_lab as lab


EXPECTED_OUTPUTS = {
    "data/qqq_adaptive_leverage_lab.csv",
    "data/qqq_adaptive_leverage_lab_summary.csv",
    "data/qqq_adaptive_leverage_lab_costs.csv",
    "data/qqq_adaptive_leverage_lab_splits.csv",
    "data/qqq_adaptive_leverage_lab_drawdowns.csv",
}

FORBIDDEN_RUNTIME_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "insert_trade_log(",
    "send_discord_alert(",
    "send_telegram",
    "load_config(",
    "get_alpaca_positions(",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab -e",
    "systemctl enable",
]

FORBIDDEN_SUMMARY_TOKENS = [
    "--paper-order-test",
    "--execute-slow-sma-paper",
    "--confirm-paper-order",
    "--confirm-slow-sma-paper",
    "submit order",
    "create order",
    "cancel order",
]


def main() -> int:
    failures: list[str] = []
    verify_help_inventory(failures)
    verify_static_safety(failures)
    verify_default_safety_config(failures)
    verify_deterministic_outputs(failures)

    if failures:
        print("QQQ adaptive leverage lab verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ adaptive leverage lab verification passed.")
    return 0


def verify_help_inventory(failures: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    help_text = (result.stdout or "") + "\n" + (result.stderr or "")
    for command in ["--qqq-adaptive-leverage-lab", "--show-qqq-adaptive-leverage-lab"]:
        if command not in help_text:
            failures.append(f"missing command in help inventory: {command}")


def verify_static_safety(failures: list[str]) -> None:
    source = inspect.getsource(lab)
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    for output in EXPECTED_OUTPUTS:
        if output not in source:
            failures.append(f"expected output path is not documented in module: {output}")
    for token in FORBIDDEN_RUNTIME_TOKENS:
        if token in source:
            failures.append(f"QQQ adaptive lab references forbidden runtime token: {token}")
    for expected_rule in [
        "cash below SMA200; 1.0x in elevated volatility",
        "reduce to 0.75x after an 8% rolling 63-day drawdown",
    ]:
        if expected_rule not in source:
            failures.append(f"adaptive fixed-rule description missing: {expected_rule}")
    early_index = bot_source.find('if sys.argv[1:] == ["--qqq-adaptive-leverage-lab"]')
    alpaca_index = bot_source.find("from alpaca.trading.client import TradingClient")
    if early_index < 0:
        failures.append("QQQ adaptive lab should be handled by the early report-only route")
    elif alpaca_index >= 0 and early_index > alpaca_index:
        failures.append("QQQ adaptive lab route must appear before Alpaca imports")
    if "--leverage-execution" in bot_source or "--margin-execution" in bot_source:
        failures.append("no leverage or margin execution command should be added")


def verify_default_safety_config(failures: list[str]) -> None:
    config_source = (ROOT / "trading_bot" / "config.py").read_text(encoding="utf-8")
    for expected in [
        'parse_config_bool(raw, "allow_shorting", False)',
        'parse_config_bool(raw, "dry_run", True)',
        'parse_config_bool(alpaca, "paper", True, parent="alpaca")',
    ]:
        if expected not in config_source:
            failures.append(f"default safety config changed or could not be verified: {expected}")


def verify_deterministic_outputs(failures: list[str]) -> None:
    price_data = deterministic_prices()
    variants = lab.build_adaptive_variants(
        created_at="2026-01-01T00:00:00+00:00",
        price_data=price_data,
        data_errors={},
    )
    report_rows = [lab.build_adaptive_report_row("2026-01-01T00:00:00+00:00", row, "full_period") for row in variants]
    cost_rows = lab.build_cost_rows("2026-01-01T00:00:00+00:00", variants)
    split_rows = lab.build_split_rows("2026-01-01T00:00:00+00:00", variants)
    drawdown_rows = lab.build_drawdown_rows("2026-01-01T00:00:00+00:00", variants)
    summary_rows = lab.build_summary_rows("2026-01-01T00:00:00+00:00", report_rows, cost_rows, split_rows)

    expected_variants = {
        "qqq_buy_and_hold",
        "spy_buy_and_hold",
        "qqq_100_trend_gate",
        "qqq_125_trend_gate",
        "qqq_150_trend_gate",
        "codex_qqq_adaptive_trend_exposure",
        "codex_qqq_drawdown_brake_trend",
        "cash_benchmark",
    }
    if {row["variant_name"] for row in variants} != expected_variants:
        failures.append("fixed QQQ adaptive validation set changed unexpectedly")
    verify_flags(report_rows + cost_rows + split_rows + drawdown_rows + summary_rows, failures)
    verify_labels(report_rows, cost_rows, split_rows, failures)
    verify_drawdowns(drawdown_rows, failures)
    verify_summary_text(report_rows, cost_rows, split_rows, failures)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_paths = {name: Path(tmpdir) / path.name for name, path in lab.OUTPUT_FILES.items()}
        lab.write_rows(output_paths["report"], lab.REPORT_COLUMNS, report_rows)
        lab.write_rows(output_paths["summary"], lab.SUMMARY_COLUMNS, summary_rows)
        lab.write_rows(output_paths["costs"], lab.COST_COLUMNS, cost_rows)
        lab.write_rows(output_paths["splits"], lab.SPLIT_COLUMNS, split_rows)
        lab.write_rows(output_paths["drawdowns"], lab.DRAWDOWN_COLUMNS, drawdown_rows)
        for name, path in output_paths.items():
            if not path.exists():
                failures.append(f"missing deterministic output file: {name}")
            with path.open(newline="", encoding="utf-8") as file:
                if not list(csv.DictReader(file)):
                    failures.append(f"deterministic output should contain rows: {name}")


def deterministic_prices() -> dict[str, list[dict[str, object]]]:
    start = date(2020, 1, 1)
    rows_by_ticker: dict[str, list[dict[str, object]]] = {"QQQ": [], "SPY": []}
    qqq = 100.0
    spy = 100.0
    for index in range(820):
        if index < 270:
            qqq_drift = 0.0011
            spy_drift = 0.00065
        elif index < 390:
            qqq_drift = -0.0021
            spy_drift = -0.0011
        elif index < 610:
            qqq_drift = 0.0014
            spy_drift = 0.0008
        else:
            qqq_drift = 0.00035
            spy_drift = 0.0003
        qqq *= 1.0 + qqq_drift
        spy *= 1.0 + spy_drift
        current_date = (start + timedelta(days=index)).isoformat()
        rows_by_ticker["QQQ"].append({"date": current_date, "close": round(qqq, 4)})
        rows_by_ticker["SPY"].append({"date": current_date, "close": round(spy, 4)})
    return rows_by_ticker


def verify_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        for field in [
            "execution_approved",
            "leverage_execution_approved",
            "margin_approved",
            "short_execution_approved",
            "scheduling_approved",
            "alpaca_called",
            "orders_created",
        ]:
            if row.get(field) is not False:
                failures.append(f"{field} must be false for {row.get('variant_name', row.get('summary_name'))}")
        if row.get("research_only") is not True:
            failures.append("research_only must be true for every row")
        if row.get("preview_only") is not False:
            failures.append("preview_only must be false for every row")


def verify_labels(
    report_rows: list[dict[str, object]],
    cost_rows: list[dict[str, object]],
    split_rows: list[dict[str, object]],
    failures: list[str],
) -> None:
    allowed = {
        "qqq_adaptive_research_lead",
        "qqq_100_trend_gate_remains_lead",
        "qqq_adaptive_promising_but_high_drawdown",
        "qqq_adaptive_cost_sensitive",
        "qqq_adaptive_financing_sensitive",
        "qqq_adaptive_split_sensitive",
        "qqq_adaptive_overfit_risk_review",
        "qqq_adaptive_rejected_return_drag",
        "synthetic_only_not_execution_ready",
        "insufficient_market_data",
        "benchmark_not_candidate",
        "qqq_leverage_validation_lead",
        "qqq_leverage_lower_drawdown_preferred",
        "qqq_leverage_promising_but_high_drawdown",
    }
    labels = {str(row.get("decision_label")) for row in report_rows}
    unexpected = labels - allowed
    if unexpected:
        failures.append(f"unexpected report decision labels: {sorted(unexpected)}")
    if not any(row.get("variant_name") == "codex_qqq_adaptive_trend_exposure" for row in report_rows):
        failures.append("adaptive trend exposure candidate must remain in the fixed set")
    if not any(row.get("variant_name") == "codex_qqq_drawdown_brake_trend" for row in report_rows):
        failures.append("drawdown brake candidate must remain in the fixed set")
    if not cost_rows:
        failures.append("cost/financing stress rows should be produced")
    if not split_rows:
        failures.append("split validation rows should be produced")


def verify_drawdowns(drawdown_rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in drawdown_rows:
        start = str(row.get("drawdown_start", ""))
        trough = str(row.get("drawdown_trough", ""))
        recovery = str(row.get("drawdown_recovery", ""))
        if start and trough and start > trough:
            failures.append(f"drawdown start after trough for {row['variant_name']}")
        if recovery and trough and recovery < trough:
            failures.append(f"drawdown recovery before trough for {row['variant_name']}")
        if int(row.get("drawdown_days", 0) or 0) < 0:
            failures.append(f"drawdown days negative for {row['variant_name']}")


def verify_summary_text(
    report_rows: list[dict[str, object]],
    cost_rows: list[dict[str, object]],
    split_rows: list[dict[str, object]],
    failures: list[str],
) -> None:
    lines = lab.build_summary_lines(
        output_paths={name: path for name, path in lab.OUTPUT_FILES.items()},
        report_rows=report_rows,
        cost_rows=cost_rows,
        split_rows=split_rows,
        data_errors={},
    )
    summary = "\n".join(lines)
    for token in [
        "SYNTHETIC RESEARCH ONLY. NOT EXECUTION.",
        "execution_approved=false",
        "leverage_execution_approved=false",
        "margin_approved=false",
        "scheduling_approved=false",
    ]:
        if token not in summary:
            failures.append(f"summary missing safety text: {token}")
    lower_summary = summary.lower()
    for token in FORBIDDEN_SUMMARY_TOKENS:
        if token in lower_summary:
            failures.append(f"summary should not print execution command/instruction token: {token}")


if __name__ == "__main__":
    raise SystemExit(main())
