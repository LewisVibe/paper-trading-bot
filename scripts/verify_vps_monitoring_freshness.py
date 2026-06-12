from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRESHNESS_MODULE = ROOT / "trading_bot" / "research" / "monitoring_freshness.py"
STATUS_MODULE = ROOT / "trading_bot" / "research" / "vps_monitoring_status.py"

EXPECTED_PATHS = [
    "data/promoted_review_refresh_summary.csv",
    "data/promoted_decision_preview.csv",
    "data/defensive_research_refresh_summary.csv",
    "data/market_monitor_scheduling_readiness_report.csv",
    "data/monitor_lockfile_readiness_report.csv",
]

EXPECTED_LABELS = ["fresh", "warning_stale", "stale", "missing"]
FORBIDDEN_CALLS = [
    "TradingClient(",
    "get_alpaca_positions(",
    "submit_order(",
    "cancel_order(",
    "create_order(",
    "send_discord_alert(",
    "sqlite3.connect(",
    "insert_trade_log(",
    "yf.download(",
    "download_close_prices(",
    "download_backtest_prices(",
    "load_config(",
    "open(\"config.json\"",
    "read_text(\"config.json\"",
]


def main() -> int:
    failures: list[str] = []
    verify_freshness_helper(failures)
    verify_status_uses_freshness(failures)

    if failures:
        print("VPS monitoring freshness verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("VPS monitoring freshness verification passed.")
    print("Verified saved-output freshness labels, mtime-only helper behavior, report-only status use, and no forbidden calls.")
    return 0


def verify_freshness_helper(failures: list[str]) -> None:
    source = read_text(FRESHNESS_MODULE)
    if "def build_freshness_statuses" not in source or "def freshness_for_path" not in source:
        failures.append("Freshness helper functions are missing")
    for path in EXPECTED_PATHS:
        if path not in source:
            failures.append(f"Freshness helper missing expected path: {path}")
    for label in EXPECTED_LABELS:
        if label not in source:
            failures.append(f"Freshness helper missing label: {label}")
    for token in ["csv.", "DictReader", ".read_text(", ".open("]:
        if token in source:
            failures.append(f"Freshness helper must not read full CSV contents: {token}")
    for token in FORBIDDEN_CALLS:
        if token in source:
            failures.append(f"Freshness helper contains forbidden token: {token}")


def verify_status_uses_freshness(failures: list[str]) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from trading_bot.research.vps_monitoring_status import build_vps_monitoring_status_lines  # noqa: PLC0415

    source = read_text(STATUS_MODULE)
    if "build_freshness_statuses" not in source or "Saved-output freshness:" not in source:
        failures.append("VPS monitoring status should include saved-output freshness")
    for token in FORBIDDEN_CALLS:
        if token in source:
            failures.append(f"VPS monitoring status contains forbidden token: {token}")
    output = "\n".join(build_vps_monitoring_status_lines(ROOT))
    for phrase in ["Saved-output freshness:", "execution_approved=False", "scheduling_approved=False"]:
        if phrase not in output:
            failures.append(f"VPS monitoring status output missing phrase: {phrase}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
