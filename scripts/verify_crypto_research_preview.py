from __future__ import annotations

import csv
import inspect
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.crypto as crypto
from trading_bot.research.crypto import run_crypto_research_preview_files


FORBIDDEN_TERMS = [
    "TradingClient",
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "get_alpaca_positions",
    "get_simulated_positions",
    "decide_trade",
    "execute",
]


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        result = run_crypto_research_preview_files(Path(tmp))
        if not result.output_path.exists():
            failures.append("crypto_research_preview.csv was not created")

        rows_by_symbol = {row["symbol"]: row for row in result.rows}
        if set(rows_by_symbol) != {"BTC/USD", "ETH/USD", "LTC/USD"}:
            failures.append(f"unexpected crypto symbols: {sorted(rows_by_symbol)}")
        if "SOL/USD" in rows_by_symbol:
            failures.append("SOL/USD should not be added in this task")

        for symbol, row in rows_by_symbol.items():
            if row["asset_class"] != "crypto":
                failures.append(f"{symbol} asset_class should be crypto")
            if row["research_status"] != "research_candidate":
                failures.append(f"{symbol} research_status should be research_candidate")
            for key in ["execution_enabled", "shorting_enabled", "margin_enabled", "execution_approved"]:
                if row[key] is not False:
                    failures.append(f"{symbol} {key} should be False")
            for key in ["research_only", "preview_only"]:
                if row[key] is not True:
                    failures.append(f"{symbol} {key} should be True")

        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != crypto.CRYPTO_RESEARCH_COLUMNS:
                failures.append("crypto preview columns changed unexpectedly")
            csv_rows = list(reader)
            if len(csv_rows) != 3:
                failures.append("crypto preview CSV should contain three rows")

        summary = "\n".join(result.summary_lines)
        for expected in [
            "CRYPTO RESEARCH ONLY. NOT EXECUTION.",
            "Symbols previewed: BTC/USD, ETH/USD, LTC/USD",
            "Execution enabled: false",
            "Shorting enabled: false",
            "Margin enabled: false",
        ]:
            if expected not in summary:
                failures.append(f"summary missing: {expected}")

    source = inspect.getsource(crypto)
    for term in FORBIDDEN_TERMS:
        if term in source:
            failures.append(f"crypto research preview references forbidden term: {term}")

    if failures:
        print("Crypto research preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Crypto research preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
