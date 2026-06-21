from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.current_research_state import (  # noqa: E402
    CRYPTO_COMBINED_SLEEVE,
    HIGH_GROWTH_SLEEVE,
    MULTI_SLEEVE_CANDIDATE,
    RECOVERED_QQQ100_REFERENCE,
    show_current_research_state,
)


BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "current_research_state.py"
README = ROOT / "README.md"
CURRENT_STATE = ROOT / "docs" / "CURRENT_STATE.md"
V2_CHECKPOINT = ROOT / "docs" / "V2_RESEARCH_CHECKPOINT.md"
HERMES_TASK_BOARD = ROOT / "docs" / "HERMES_TASK_BOARD.md"

COMMAND = "--show-current-research-state"

EXPECTED_INPUTS = [
    "qqq100_stream_reconciliation_summary.csv",
    "qqq100_benchmark_inputs_summary.csv",
    "qqq100_recovered_reference_metrics.csv",
    "high_growth_return_stream_metrics.csv",
    "crypto_return_stream_metrics.csv",
    "multi_sleeve_portfolio_backtest.csv",
    "multi_sleeve_crypto_review_summary.csv",
    "multi_sleeve_crypto_review_split_robustness.csv",
    "multi_sleeve_crypto_review_cost_stress.csv",
    "multi_sleeve_crypto_review_volatility.csv",
]

REQUIRED_MODULE_TOKENS = [
    RECOVERED_QQQ100_REFERENCE,
    HIGH_GROWTH_SLEEVE,
    CRYPTO_COMBINED_SLEEVE,
    MULTI_SLEEVE_CANDIDATE,
    "A. QQQ100 reference",
    "B. High-growth sleeve",
    "C. Crypto sleeve",
    "D. Multi-sleeve candidate",
    "E. Safety state",
    "missing_saved_output",
    "execution_approved=false",
    "crypto_execution_approved=false",
    "scheduling_approved=false",
    "order paths touched=false",
]

FORBIDDEN_MODULE_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "create_order",
    "get_alpaca_positions",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "load_config(",
    "config.json",
    "import yfinance",
    "yf.download",
    "allow_shorting = True",
    "enable_margin",
    "sched.scheduler",
    "Task Scheduler",
    "Hermes cron",
    "promotion-ready",
    "promotion_ready",
    "execution-ready",
    "execution_ready",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)
    docs_source = "\n".join(read_text(path) for path in [README, CURRENT_STATE, V2_CHECKPOINT, HERMES_TASK_BOARD])

    verify_command_registration(bot_source, failures)
    verify_module(module_source, failures)
    verify_missing_outputs(failures)
    verify_saved_fixture(failures)
    verify_docs(docs_source, failures)

    if failures:
        print("Show current research state verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Show current research state verification passed.")
    print("Verified compact saved-output-only multi-sleeve research display and false approval wording.")
    return 0


def verify_command_registration(bot_source: str, failures: list[str]) -> None:
    if COMMAND not in bot_source:
        failures.append(f"missing command registration/routing: {COMMAND}")
    early_index = bot_source.find(f'if sys.argv[1:] == ["{COMMAND}"]')
    load_config_index = bot_source.find("config = load_config(")
    if early_index == -1:
        failures.append("missing early saved-output route for show-current-research-state")
    elif load_config_index != -1 and early_index > load_config_index:
        failures.append("show-current-research-state must route before config loading")


def verify_module(module_source: str, failures: list[str]) -> None:
    for filename in EXPECTED_INPUTS:
        if filename not in module_source:
            failures.append(f"missing expected saved input reference: {filename}")
    for token in REQUIRED_MODULE_TOKENS:
        if token not in module_source:
            failures.append(f"missing display token: {token}")
    for token in FORBIDDEN_MODULE_TOKENS:
        if token in module_source:
            failures.append(f"forbidden execution/config/scheduling token in display module: {token}")
    for token in ["open(\"w\"", ".write(", "writerow", "writerows", "DictWriter"]:
        if token in module_source:
            failures.append("display module should not write files")


def verify_missing_outputs(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "data"
        data.mkdir()
        status, lines = show_current_research_state(data)
        output = "\n".join(lines)
        if status != 0:
            failures.append("missing saved outputs should be handled gracefully with exit 0")
        for token in ["CURRENT RESEARCH STATE", "missing_saved_output", "A. QQQ100 reference", "E. Safety state"]:
            if token not in output:
                failures.append(f"missing-output display missing token: {token}")


def verify_saved_fixture(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "data"
        data.mkdir()
        write_fixture(data)
        status, lines = show_current_research_state(data)
        output = "\n".join(lines)
        if status != 0:
            failures.append("saved fixture display should exit 0")
        for token in [
            "A. QQQ100 reference",
            "saved benchmark: qqq_100_trend_gate / qqq100_core_trend_sleeve",
            "recovered reference: qqq100_recovered_reference_stream",
            "B. High-growth sleeve",
            HIGH_GROWTH_SLEEVE,
            "C. Crypto sleeve",
            "combined BTC/ETH",
            CRYPTO_COMBINED_SLEEVE,
            "D. Multi-sleeve candidate",
            MULTI_SLEEVE_CANDIDATE,
            "multi_sleeve_crypto_review_promising_research_only",
            "plus_100bps_crypto_turnover",
            "crypto_high_volatility_and_drawdown_warning",
            "E. Safety state",
            "execution_approved=false",
            "crypto_execution_approved=false",
            "scheduling_approved=false",
            "order paths touched=false",
        ]:
            if token not in output:
                failures.append(f"saved fixture display missing token: {token}")
        for forbidden in ["promotion-ready", "execution-ready"]:
            if forbidden in output:
                failures.append(f"display should not use forbidden wording: {forbidden}")


def verify_docs(docs_source: str, failures: list[str]) -> None:
    for phrase in [
        COMMAND,
        "compact saved-output-only",
        "multi-sleeve research state",
        "does not refresh market data",
        "does not approve execution",
    ]:
        if phrase not in docs_source:
            failures.append(f"missing docs phrase: {phrase}")


def write_fixture(data: Path) -> None:
    write_csv(
        data / "qqq100_benchmark_inputs_summary.csv",
        [
            summary_row("saved_qqq100_benchmark_cagr", "16.8429"),
            summary_row("saved_qqq100_benchmark_sharpe", "1.0027"),
            summary_row("saved_qqq100_benchmark_max_drawdown", "-23.4576"),
            summary_row("saved_qqq100_benchmark_calmar", "0.718"),
        ],
    )
    write_csv(
        data / "qqq100_recovered_reference_metrics.csv",
        [
            {
                "reference_name": RECOVERED_QQQ100_REFERENCE,
                "reference_status": "qqq100_reconstruction_close_enough_for_research_review",
                "cagr": "16.9832",
                "sharpe": "1.0073",
                "max_drawdown": "-23.4576",
                "calmar": "0.724",
            }
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
            {"candidate_name": "btc_trend_vol_gate_research_sleeve", "CAGR": "45.9331", "Sharpe": "0.9979", "MaxDD": "-73.0752", "Calmar": "0.6286"},
            {"candidate_name": "eth_trend_research_sleeve", "CAGR": "38.3233", "Sharpe": "0.8614", "MaxDD": "-71.6092", "Calmar": "0.5352"},
            {"candidate_name": CRYPTO_COMBINED_SLEEVE, "CAGR": "37.0042", "Sharpe": "0.9127", "MaxDD": "-60.1453", "Calmar": "0.6152"},
        ],
    )
    write_csv(
        data / "multi_sleeve_portfolio_backtest.csv",
        [
            {
                "portfolio_name": MULTI_SLEEVE_CANDIDATE,
                "candidate_cagr": "21.7328",
                "candidate_sharpe": "1.1852",
                "candidate_max_drawdown": "-22.2489",
                "candidate_calmar": "0.9768",
                "delta_cagr_vs_recovered_qqq100_reference": "4.7496",
                "delta_sharpe_vs_recovered_qqq100_reference": "0.1779",
                "delta_max_drawdown_vs_recovered_qqq100_reference": "1.2087",
                "delta_calmar_vs_recovered_qqq100_reference": "0.2528",
                "qqq100_reference_source_used": RECOVERED_QQQ100_REFERENCE,
                "old_generated_reference_status": "diagnostic_only",
            }
        ],
    )
    write_csv(
        data / "multi_sleeve_crypto_review_summary.csv",
        [
            summary_row("final_crypto_review_status", "multi_sleeve_crypto_review_promising_research_only"),
            summary_row("worst_split_by_calmar", "split_80_20 Calmar=2.2834"),
            summary_row("worst_split_by_maxdd", "split_60_40 MaxDD=-13.3269"),
            summary_row("worst_cost_stress_row", "plus_100bps_crypto_turnover CAGR=21.4695; delta_CAGR=-0.2633; status=cost_stress_tolerated_research_only"),
            summary_row("crypto_volatility_drawdown_warnings", "crypto_high_volatility_and_drawdown_warning; candidate_drawdown_improves_vs_recovered_qqq100"),
            summary_row("required_next_step", "manual_review_crypto_split_cost_volatility_before_candidate_label_change"),
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
