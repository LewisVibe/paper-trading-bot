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

import trading_bot.research.short_leverage_research_lab as lab


EXPECTED_OUTPUTS = {
    "data/short_leverage_research_lab.csv",
    "data/short_leverage_research_lab_summary.csv",
    "data/short_leverage_research_lab_costs.csv",
    "data/short_leverage_research_lab_splits.csv",
    "data/short_leverage_research_lab_drawdowns.csv",
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
        print("Short/leverage research lab verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Short/leverage research lab verification passed.")
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
    for command in ["--short-leverage-research-lab", "--show-short-leverage-research-lab"]:
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
            failures.append(f"short/leverage lab references forbidden runtime token: {token}")
    early_index = bot_source.find('if sys.argv[1:] == ["--short-leverage-research-lab"]')
    alpaca_index = bot_source.find("from alpaca.trading.client import TradingClient")
    if early_index < 0:
        failures.append("short/leverage lab should be handled by the early report-only route")
    elif alpaca_index >= 0 and early_index > alpaca_index:
        failures.append("short/leverage lab route must appear before Alpaca imports")
    if "--short-execution" in bot_source or "--leverage-execution" in bot_source:
        failures.append("no short or leverage execution command should be added")


def verify_default_safety_config(failures: list[str]) -> None:
    config_source = (ROOT / "trading_bot" / "config.py").read_text(encoding="utf-8")
    if 'parse_config_bool(raw, "allow_shorting", False)' not in config_source:
        failures.append("allow_shorting default should remain false")
    for expected in ['parse_config_bool(raw, "dry_run", True)', 'parse_config_bool(alpaca, "paper", True, parent="alpaca")']:
        if expected not in config_source:
            failures.append(f"default safety config changed or could not be verified: {expected}")


def verify_deterministic_outputs(failures: list[str]) -> None:
    price_data = deterministic_prices()
    lead_curve = [{"date": row["date"], "equity": 10000.0 + index * 8.0} for index, row in enumerate(price_data["SPY"])]
    hypotheses = lab.build_hypotheses(
        price_data=price_data,
        lead_curve=lead_curve,
        lead_status="saved_active_lead_equity_curve:test",
        created_at="2026-01-01T00:00:00+00:00",
        data_errors={},
    )
    if {row["hypothesis_name"] for row in hypotheses} != {
        "synthetic_spy_150_trend_gate",
        "synthetic_spy_200_trend_gate",
        "synthetic_qqq_150_trend_gate",
        "growth_lead_125_synthetic_leverage_proxy",
        "growth_lead_150_synthetic_leverage_proxy",
        "synthetic_spy_short_hedge_weak_regime",
        "sector_relative_long_short_fixed",
        "defensive_vs_cyclical_spread_fixed",
    }:
        failures.append("fixed hypothesis set changed unexpectedly")
    result_rows = [lab.build_result_row("2026-01-01T00:00:00+00:00", row, "full_period") for row in hypotheses]
    split_rows = lab.build_split_rows("2026-01-01T00:00:00+00:00", hypotheses)
    cost_rows = lab.build_cost_rows("2026-01-01T00:00:00+00:00", hypotheses)
    drawdown_rows = lab.build_drawdown_rows("2026-01-01T00:00:00+00:00", hypotheses)
    summary_rows = lab.build_summary_rows("2026-01-01T00:00:00+00:00", result_rows, cost_rows)

    verify_flags(result_rows + split_rows + cost_rows + drawdown_rows + summary_rows, failures)
    verify_decision_labels(result_rows, failures)
    verify_drawdowns(drawdown_rows, failures)
    verify_summary_text(result_rows, cost_rows, failures)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_paths = {name: Path(tmpdir) / path.name for name, path in lab.OUTPUT_FILES.items()}
        lab.write_rows(output_paths["results"], lab.RESULT_COLUMNS, result_rows)
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
    rows_by_ticker: dict[str, list[dict[str, object]]] = {}
    for ticker_index, ticker in enumerate(lab.MARKET_TICKERS):
        rows: list[dict[str, object]] = []
        price = 100.0 + ticker_index
        for index in range(520):
            if index < 260:
                drift = 0.0007 + ticker_index * 0.00002
            elif index < 360:
                drift = -0.0012 + ticker_index * 0.00001
            else:
                drift = 0.0009 - ticker_index * 0.00001
            price *= 1.0 + drift
            rows.append({"date": (start + timedelta(days=index)).isoformat(), "close": round(price, 4)})
        rows_by_ticker[ticker] = rows
    return rows_by_ticker


def verify_flags(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        for field in [
            "execution_approved",
            "short_execution_approved",
            "leverage_execution_approved",
            "margin_approved",
            "scheduling_approved",
            "alpaca_called",
            "orders_created",
        ]:
            if row.get(field) is not False:
                failures.append(f"{field} must be false for {row.get('hypothesis_name', row.get('summary_name'))}")
        if row.get("research_only") is not True:
            failures.append("research_only must be true for every row")
        if row.get("preview_only") is not False:
            failures.append("preview_only must be false for every row")


def verify_decision_labels(result_rows: list[dict[str, object]], failures: list[str]) -> None:
    labels = {str(row.get("decision_label")) for row in result_rows}
    allowed = {
        "short_leverage_candidate_rejected",
        "leverage_candidate_promising_but_high_drawdown",
        "leverage_candidate_cost_sensitive",
        "short_candidate_borrow_fee_sensitive",
        "synthetic_only_not_execution_ready",
        "insufficient_saved_inputs",
    }
    unexpected = labels - allowed
    if unexpected:
        failures.append(f"unexpected decision labels: {sorted(unexpected)}")
    if "synthetic_only_not_execution_ready" not in labels:
        failures.append("at least one synthetic-only non-execution label should be produced in deterministic fixture")


def verify_drawdowns(drawdown_rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in drawdown_rows:
        start = str(row.get("drawdown_start", ""))
        trough = str(row.get("drawdown_trough", ""))
        recovery = str(row.get("drawdown_recovery", ""))
        if start and trough and start > trough:
            failures.append(f"drawdown start after trough for {row['hypothesis_name']}")
        if recovery and trough and recovery < trough:
            failures.append(f"drawdown recovery before trough for {row['hypothesis_name']}")
        if int(row.get("drawdown_days", 0) or 0) < 0:
            failures.append(f"drawdown days negative for {row['hypothesis_name']}")


def verify_summary_text(result_rows: list[dict[str, object]], cost_rows: list[dict[str, object]], failures: list[str]) -> None:
    lines = lab.build_summary_lines(
        output_paths={name: path for name, path in lab.OUTPUT_FILES.items()},
        result_rows=result_rows,
        cost_rows=cost_rows,
        data_errors={},
    )
    summary = "\n".join(lines)
    for token in [
        "SYNTHETIC ONLY. NOT EXECUTION.",
        "execution_approved=false",
        "short_execution_approved=false",
        "leverage_execution_approved=false",
        "margin_approved=false",
    ]:
        if token not in summary:
            failures.append(f"summary missing safety text: {token}")
    lower_summary = summary.lower()
    for token in FORBIDDEN_SUMMARY_TOKENS:
        if token in lower_summary:
            failures.append(f"summary should not print execution command/instruction token: {token}")


if __name__ == "__main__":
    raise SystemExit(main())
