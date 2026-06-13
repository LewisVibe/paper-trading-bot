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

import trading_bot.research.qqq_lead_decision as report


EXPECTED_OUTPUTS = {
    "data/qqq_lead_decision_report.csv",
    "data/qqq_lead_decision_summary.csv",
    "data/qqq_lead_decision_evidence.csv",
}

FORBIDDEN_RUNTIME_TOKENS = [
    "import yfinance",
    "yf.download",
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
    verify_deterministic_saved_output_decision(failures)

    if failures:
        print("QQQ lead decision verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ lead decision verification passed.")
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
    for command in ["--qqq-lead-decision-report", "--show-qqq-lead-decision-report"]:
        if command not in help_text:
            failures.append(f"missing command in help inventory: {command}")


def verify_static_safety(failures: list[str]) -> None:
    source = inspect.getsource(report)
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    for output in EXPECTED_OUTPUTS:
        if output not in source:
            failures.append(f"expected output path is not documented in module: {output}")
    for token in FORBIDDEN_RUNTIME_TOKENS:
        if token in source:
            failures.append(f"QQQ lead decision references forbidden runtime token: {token}")
    early_index = bot_source.find('if sys.argv[1:] == ["--qqq-lead-decision-report"]')
    alpaca_index = bot_source.find("from alpaca.trading.client import TradingClient")
    if early_index < 0:
        failures.append("QQQ lead decision should be handled by the early report-only route")
    elif alpaca_index >= 0 and early_index > alpaca_index:
        failures.append("QQQ lead decision route must appear before Alpaca imports")
    if "--leverage-execution" in bot_source or "--margin-execution" in bot_source:
        failures.append("no leverage or margin execution command should be added")


def verify_deterministic_saved_output_decision(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        write_input_files(root)
        result = report.generate_qqq_lead_decision_report(root)
        for path in result.output_paths.values():
            if not path.exists():
                failures.append(f"missing output file: {path.name}")
        verify_flags(result.report_rows + result.summary_rows + result.evidence_rows, failures)
        final = summary_value(result.summary_rows, "final_lead_decision")
        active = summary_value(result.summary_rows, "active_stock_etf_research_lead")
        if final != "qqq_100_trend_gate_new_research_lead":
            failures.append(f"expected qqq_100_trend_gate_new_research_lead, got {final}")
        if active != "qqq_100_trend_gate":
            failures.append(f"expected active lead qqq_100_trend_gate, got {active}")
        qqq100 = next(row for row in result.report_rows if row["candidate_name"] == "qqq_100_trend_gate")
        adaptive = next(row for row in result.report_rows if row["candidate_name"] == "codex_qqq_adaptive_trend_exposure")
        qqq150 = next(row for row in result.report_rows if row["candidate_name"] == "qqq_150_trend_gate")
        if qqq100["lead_decision_label"] != "qqq_100_simpler_lower_drawdown_candidate":
            failures.append("qqq_100 should be labelled as the simpler lower-drawdown candidate")
        if adaptive["lead_decision_label"] != "qqq_adaptive_higher_calmar_but_drawdown_tradeoff":
            failures.append("adaptive QQQ should be labelled as higher-Calmar drawdown tradeoff")
        if qqq150["lead_decision_label"] != "qqq_150_rejected_high_drawdown":
            failures.append("qqq_150 should stay rejected/high-drawdown reference")
        verify_summary_text(result.summary_lines, failures)


def write_input_files(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    write_csv(
        data / "qqq_leverage_validation_report.csv",
        [
            qqq_row("qqq_100_trend_gate", 0.0, 1.0027, -23.4576, 0.718, 0.718, 1.0, "ok"),
            qqq_row("qqq_150_trend_gate", 0.0, 0.91, -32.376, 0.52, 0.52, 1.5, "ok"),
            qqq_row("qqq_175_trend_gate", 0.0, 0.83, -38.2, 0.41, 0.41, 1.75, "ok"),
            qqq_row("qqq_200_trend_gate", 0.0, 0.76, -43.141, 0.33, 0.33, 2.0, "ok"),
            qqq_row("qqq_buy_and_hold", 0.0, 0.71, -34.0, 0.40, 0.40, 1.0, "ok"),
            qqq_row("spy_buy_and_hold", 0.0, 0.62, -33.0, 0.36, 0.36, 1.0, "ok"),
        ],
    )
    write_csv(
        data / "qqq_adaptive_leverage_lab.csv",
        [
            qqq_row("codex_qqq_adaptive_trend_exposure", 0.0, 0.9749, -25.989, 0.7804, 0.7804, 1.5, "ok"),
        ],
    )
    write_csv(
        data / "qqq_leverage_validation_costs.csv",
        [{"variant_name": "qqq_100_trend_gate", "cost_sensitivity_label": "synthetic_only_not_execution_ready"}],
    )
    write_csv(
        data / "qqq_adaptive_leverage_lab_costs.csv",
        [{"variant_name": "codex_qqq_adaptive_trend_exposure", "cost_sensitivity_label": "qqq_adaptive_financing_sensitive"}],
    )
    write_csv(
        data / "qqq_leverage_validation_splits.csv",
        [{"variant_name": "qqq_100_trend_gate", "split_sensitivity_label": "synthetic_only_not_execution_ready"}],
    )
    write_csv(
        data / "qqq_adaptive_leverage_lab_splits.csv",
        [{"variant_name": "codex_qqq_adaptive_trend_exposure", "split_sensitivity_label": "synthetic_only_not_execution_ready"}],
    )
    for filename in [
        "qqq_leverage_validation_summary.csv",
        "qqq_leverage_validation_drawdowns.csv",
        "qqq_adaptive_leverage_lab_summary.csv",
        "qqq_adaptive_leverage_lab_drawdowns.csv",
        "project_research_state_summary.csv",
        "project_research_state_next_steps.csv",
        "codex_ambitious_lead_decision_summary.csv",
        "codex_ambitious_lead_decision_evidence.csv",
    ]:
        write_csv(data / filename, [{"summary_name": "fixture", "summary_value": "fixture"}])
    write_csv(
        data / "codex_ambitious_lead_decision.csv",
        [
            {
                "check_name": "full_period_evidence",
                "metric_value": "CAGR=14.1039, Sharpe=0.7192, MaxDD=-29.5357, Calmar=0.4775, cash=9.9651, turnover=19.0",
                "status": "full_period_beats_core_references",
            },
            {
                "check_name": "final_decision_label",
                "status": "codex_ambitious_active_research_lead_cost_review_required",
                "metric_value": "codex_ambitious_active_research_lead_cost_review_required",
            },
        ],
    )


def qqq_row(name: str, cagr: float, sharpe: float, maxdd: float, calmar: float, total: float, leverage: float, status: str) -> dict[str, object]:
    return {
        "variant_name": name,
        "data_status": status,
        "cagr_pct": cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": maxdd,
        "calmar_ratio": calmar,
        "total_return_pct": total,
        "leverage_multiple": leverage,
        "turnover": 4,
        "cash_time_pct": 30,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
                failures.append(f"{field} must be false for {row.get('candidate_name', row.get('summary_name'))}")
        if row.get("research_only") is not True:
            failures.append("research_only must be true for every row")
        if row.get("preview_only") is not False:
            failures.append("preview_only must be false for every row")


def verify_summary_text(lines: list[str], failures: list[str]) -> None:
    summary = "\n".join(lines)
    for token in [
        "SAVED OUTPUT ONLY. NOT EXECUTION.",
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


def summary_value(rows: list[dict[str, object]], name: str) -> str:
    return str(next((row.get("summary_value", "") for row in rows if row.get("summary_name") == name), ""))


if __name__ == "__main__":
    raise SystemExit(main())
