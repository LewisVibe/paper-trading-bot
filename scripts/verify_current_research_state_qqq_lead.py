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

from trading_bot.research.current_research_state import show_current_research_state
from trading_bot.research.project_research_state_refresh import generate_project_research_state_refresh


BOT = ROOT / "bot.py"
REFRESH_MODULE = ROOT / "trading_bot" / "research" / "project_research_state_refresh.py"
DISPLAY_MODULE = ROOT / "trading_bot" / "research" / "current_research_state.py"

FORBIDDEN_TOKENS = [
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


def main() -> int:
    failures: list[str] = []
    verify_commands(failures)
    verify_static_safety(failures)
    verify_saved_fixture(failures)

    if failures:
        print("Current research state QQQ lead verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Current research state QQQ lead verification passed.")
    return 0


def verify_commands(failures: list[str]) -> None:
    source = BOT.read_text(encoding="utf-8")
    for command in ["--project-research-state-refresh", "--show-current-research-state"]:
        if command not in source:
            failures.append(f"missing command: {command}")


def verify_static_safety(failures: list[str]) -> None:
    combined = REFRESH_MODULE.read_text(encoding="utf-8") + "\n" + DISPLAY_MODULE.read_text(encoding="utf-8")
    for token in [
        "qqq_100_trend_gate",
        "qqq_100_trend_gate_new_research_lead",
        "codex_qqq_adaptive_trend_exposure",
        "qqq_150_trend_gate",
        "crypto_equal_weight_ex_highest_vol_2",
        "crypto_manual_review_not_ready_for_preview_discussion",
        "review_qqq_trend_gate_as_new_stock_etf_research_lead",
        '"execution_approved": False',
        '"scheduling_approved": False',
        '"leverage_execution_approved": False',
        '"margin_approved": False',
        '"short_execution_approved": False',
    ]:
        if token not in combined:
            failures.append(f"missing expected QQQ current-state token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in combined:
            failures.append(f"forbidden runtime/execution token in current-state modules: {token}")
    if "write" in DISPLAY_MODULE.read_text(encoding="utf-8"):
        failures.append("show-current-research-state display module should not write files")


def verify_saved_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "qqq_lead_decision_summary.csv",
            [
                row("final_lead_decision", "qqq_100_trend_gate_new_research_lead", "Research label only."),
                row("active_stock_etf_research_lead", "qqq_100_trend_gate", "Lead after decision."),
                row("conservative_qqq_candidate", "qqq_100_trend_gate", "CAGR=16.8429; Sharpe=1.0027; MaxDD=-23.4576; Calmar=0.718"),
                row("ambitious_qqq_candidate", "codex_qqq_adaptive_trend_exposure", "CAGR=20.2819; Sharpe=0.9749; MaxDD=-25.9889; Calmar=0.7804"),
                row("rejected_high_drawdown_reference", "qqq_150_trend_gate", "CAGR=23.3903; Sharpe=0.9542; MaxDD=-33.892; Calmar=0.6901"),
                row("recommended_next_step", "review_qqq_trend_gate_as_new_stock_etf_research_lead", "Manual review only."),
            ],
        )
        write_csv(data / "qqq_lead_decision_report.csv", [{"candidate_name": "qqq_100_trend_gate"}])
        write_csv(data / "qqq_lead_decision_evidence.csv", [{"candidate_name": "qqq_100_trend_gate"}])
        write_csv(
            data / "expanded_crypto_manual_review_summary.csv",
            [
                {"summary_name": "final_manual_review_status", "summary_value": "crypto_manual_review_not_ready_for_preview_discussion"},
                {"summary_name": "blocker_counts", "summary_value": "manual_review_blockers=present"},
            ],
        )
        write_csv(
            data / "expanded_crypto_lead_decision_summary.csv",
            [{"summary_name": "selected_crypto_research_lead", "summary_value": "crypto_equal_weight_ex_highest_vol_2"}],
        )
        result = generate_project_research_state_refresh(data)
        verify_all_false(result.refresh_rows + result.summary_rows + result.next_step_rows, failures)
        summary = {item["metric_name"]: item["metric_value"] for item in result.summary_rows}
        if summary.get("stock_etf_active_research_lead") != "qqq_100_trend_gate":
            failures.append("project refresh did not surface qqq_100_trend_gate as stock/ETF lead")
        if summary.get("stock_etf_ambitious_alternative") != "codex_qqq_adaptive_trend_exposure":
            failures.append("project refresh did not preserve QQQ adaptive ambitious alternative")
        if summary.get("stock_etf_rejected_high_drawdown_reference") != "qqq_150_trend_gate":
            failures.append("project refresh did not preserve qqq_150 rejected reference")
        if summary.get("crypto_research_lead") != "crypto_equal_weight_ex_highest_vol_2":
            failures.append("crypto lead was overwritten")
        status, lines = show_current_research_state(data)
        output = "\n".join(lines)
        if status != 0:
            failures.append("show-current-research-state fixture should exit 0")
        for token in [
            "Stock/ETF lead: qqq_100_trend_gate",
            "Stock/ETF status: qqq_100_trend_gate_new_research_lead",
            "Stock/ETF ambitious alternative: codex_qqq_adaptive_trend_exposure",
            "Stock/ETF rejected high-drawdown reference: qqq_150_trend_gate",
            "Crypto lead: crypto_equal_weight_ex_highest_vol_2",
            "execution_approved=false; scheduling_approved=false",
        ]:
            if token not in output:
                failures.append(f"display output missing token: {token}")


def verify_all_false(rows: list[dict[str, object]], failures: list[str]) -> None:
    for row in rows:
        for field in ["execution_approved", "scheduling_approved"]:
            if row.get(field) is not False:
                failures.append(f"{field} must be false for {row.get('metric_name')}")


def row(name: str, value: str, details: str) -> dict[str, str]:
    return {"summary_name": name, "summary_value": value, "details": details}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = sorted({key for item in rows for key in item})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
