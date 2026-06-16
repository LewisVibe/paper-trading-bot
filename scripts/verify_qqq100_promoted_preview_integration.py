from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "promoted_preview.py"
OUTPUT = "data/promoted_strategy_preview.csv"
QQQ100 = "qqq_100_trend_gate"
QQQ150 = "qqq_150_trend_gate"
HIGH_GROWTH = "codex_broad_growth_balanced_breakout_control"

FORBIDDEN_PROMOTED_PREVIEW_COLUMNS = {
    "order_quantity",
    "quantity",
    "order_side",
    "side",
    "order_type",
    "account_id",
    "api_key",
    "webhook",
    "secret",
}


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)

    verify_source_wiring(bot_source, module_source, failures)
    verify_helper_rows(failures)
    verify_outputs_ignored(failures)
    verify_no_execution_path_changes(bot_source, module_source, failures)

    if failures:
        print("QQQ100 promoted preview integration verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("QQQ100 promoted preview integration verification passed.")
    print("Verified qqq_100_trend_gate / QQQ promoted preview row, high-growth exclusion, rejected QQQ150 exclusion, false approval flags, no order columns, and unchanged execution boundaries.")
    return 0


def verify_source_wiring(bot_source: str, module_source: str, failures: list[str]) -> None:
    for token in [
        "append_qqq100_promoted_preview_candidate",
        "build_qqq100_promoted_preview_row",
        "qqq100_preview_signal_pack.csv",
        QQQ100,
        "qqq100_clean_lead_promoted_to_preview_review",
        "missing_qqq100_preview_signal_input",
        "preview_only",
        "execution_approved",
        "paper_execution_approved",
        "scheduling_approved",
        "orders_created",
        "orders_submitted",
        "orders_cancelled",
    ]:
        if token not in module_source and token not in bot_source:
            failures.append(f"missing promoted preview integration token: {token}")
    if "append_qqq100_promoted_preview_candidate(rows, warnings)" not in bot_source:
        failures.append("--preview-promoted-strategies should append QQQ100 promoted preview candidate")
    missing_report_branch = function_block(
        bot_source,
        'if not promotion_path.exists():',
        'candidates = read_preview_candidates(promotion_path)',
    )
    if not missing_report_branch:
        failures.append("could not locate missing strategy_promotion_report branch")
    else:
        for token in [
            "Missing legacy strategy promotion report",
            "append_qqq100_promoted_preview_candidate(rows, warnings)",
            "write_promoted_preview(output_path, rows)",
            "qqq100_available",
            "return 0",
            "return 1",
        ]:
            if token not in missing_report_branch:
                failures.append(f"missing legacy-report branch should handle QQQ100-only output: {token}")
    if HIGH_GROWTH not in module_source or QQQ150 not in module_source:
        failures.append("high-growth and QQQ150 exclusions should be explicit in promoted preview module")
    if "BLOCKED_PROMOTED_PREVIEW_STRATEGIES" not in module_source:
        failures.append("blocked promoted-preview strategy allow/deny list is missing")


def verify_helper_rows(failures: list[str]) -> None:
    from trading_bot.research.promoted_preview import (  # noqa: PLC0415
        PROMOTED_PREVIEW_COLUMNS,
        append_qqq100_promoted_preview_candidate,
        read_preview_candidates,
        write_promoted_preview,
    )

    forbidden_present = sorted(FORBIDDEN_PROMOTED_PREVIEW_COLUMNS.intersection(PROMOTED_PREVIEW_COLUMNS))
    if forbidden_present:
        failures.append("promoted preview schema contains order/secret-like columns: " + ", ".join(forbidden_present))

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = root / "data"
        data_dir.mkdir()
        write_csv(
            data_dir / "qqq100_preview_signal_pack.csv",
            [
                {
                    "strategy_name": QQQ100,
                    "ticker": "QQQ",
                    "signal_date": "2026-06-15",
                    "latest_close": "555.12",
                    "sma_100": "520.11",
                    "trend_state": "above_sma100_trend_gate",
                    "desired_position": "long",
                    "signal_reason": "QQQ latest close is above the 100-day SMA trend gate.",
                    "data_status": "ok",
                    "data_error": "",
                    "research_only": "True",
                    "preview_only": "True",
                    "action_preview_added": "False",
                    "execution_approved": "False",
                    "paper_execution_approved": "False",
                    "scheduling_approved": "False",
                }
            ],
        )
        rows: list[dict[str, object]] = []
        warnings: list[str] = []
        append_qqq100_promoted_preview_candidate(rows, warnings, root_dir=root, created_at="2026-06-16T00:00:00Z")
        if len(rows) != 1:
            failures.append("expected exactly one QQQ100 promoted preview row")
            return
        row = rows[0]
        if row.get("strategy_name") != QQQ100 or row.get("ticker") != "QQQ":
            failures.append("QQQ100 promoted preview row should use qqq_100_trend_gate / QQQ")
        if row.get("desired_position") != "long":
            failures.append("QQQ100 desired_position should come from saved preview signal")
        if row.get("signal_source") != "qqq100_preview_signal_pack":
            failures.append("QQQ100 promoted row should identify saved signal source")
        if row.get("promotion_status") != "preview_candidate":
            failures.append("QQQ100 saved ok signal should be a preview_candidate")
        if row.get("promotion_label") != "qqq100_clean_lead_promoted_to_preview_review":
            failures.append("QQQ100 promoted row should carry the clean-lead preview label")
        for flag in ["research_only", "preview_only", "preview_candidate"]:
            if row.get(flag) is not True:
                failures.append(f"{flag} should be true for QQQ100 promoted row")
        for flag in ["execution_approved", "paper_execution_approved", "scheduling_approved", "orders_created", "orders_submitted", "orders_cancelled"]:
            if row.get(flag) is not False:
                failures.append(f"{flag} should be false for QQQ100 promoted row")
        if warnings:
            failures.append("saved ok QQQ100 row should not emit warnings")
        output_path = data_dir / "promoted_strategy_preview.csv"
        write_promoted_preview(output_path, rows)
        with output_path.open(newline="", encoding="utf-8") as handle:
            written_rows = list(csv.DictReader(handle))
        if not written_rows or written_rows[0].get("strategy_name") != QQQ100:
            failures.append("promoted_strategy_preview.csv should be writable with only the saved QQQ100 signal")
        if written_rows and written_rows[0].get("signal_source") != "qqq100_preview_signal_pack":
            failures.append("written QQQ100-only promoted row should preserve qqq100_preview_signal_pack source")
        for flag in ["execution_approved", "paper_execution_approved", "scheduling_approved"]:
            if written_rows and written_rows[0].get(flag, "").lower() != "false":
                failures.append(f"written QQQ100-only promoted row should keep {flag}=false")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        rows = []
        warnings = []
        append_qqq100_promoted_preview_candidate(rows, warnings, root_dir=root, created_at="2026-06-16T00:00:00Z")
        row = rows[0]
        if row.get("promotion_status") != "blocked_missing_signal_input":
            failures.append("missing QQQ100 saved signal should create a blocked missing-input row")
        if "missing_qqq100_preview_signal_input" not in warnings:
            failures.append("missing QQQ100 saved signal should emit a warning")

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "strategy_promotion_report.csv"
        write_csv(
            path,
            [
                {
                    "strategy_name": HIGH_GROWTH,
                    "strategy_family": "high_growth",
                    "ticker_or_portfolio": "portfolio",
                    "promotion_status": "preview_candidate",
                    "required_next_step": "do_not_promote",
                },
                {
                    "strategy_name": QQQ150,
                    "strategy_family": "qqq",
                    "ticker_or_portfolio": "portfolio",
                    "promotion_status": "preview_candidate",
                    "required_next_step": "do_not_promote",
                },
            ],
        )
        candidates = read_preview_candidates(path)
        names = {row.get("strategy_name") for row in candidates}
        if HIGH_GROWTH in names:
            failures.append("high-growth branch must not be promoted")
        if QQQ150 in names:
            failures.append("qqq_150_trend_gate must remain rejected/not promoted")


def verify_outputs_ignored(failures: list[str]) -> None:
    completed = subprocess.run(["git", "check-ignore", OUTPUT], cwd=ROOT, text=True, capture_output=True, timeout=10)
    if completed.returncode != 0:
        failures.append(f"generated output is not ignored by git: {OUTPUT}")


def verify_no_execution_path_changes(bot_source: str, module_source: str, failures: list[str]) -> None:
    for token in [
        ".submit_order(",
        ".cancel_order(",
        ".replace_order(",
        "MarketOrderRequest(",
        "LimitOrderRequest(",
        "insert_trade_log(",
        "send_discord_alert(",
        "send_telegram",
        "TradingClient(",
        "get_alpaca_positions",
        "load_config(",
        "Register-ScheduledTask",
        "schtasks /create",
        "crontab",
        "systemctl",
    ]:
        if token in module_source:
            failures.append(f"promoted preview integration must not contain execution/config/scheduler token: {token}")
    normal_source = function_block(bot_source, "def run_bot(", "def run_paper_order_test(")
    slow_source = function_block(bot_source, "def run_slow_sma_paper_execution(", "def parse_args(")
    if "qqq_100_trend_gate" in normal_source:
        failures.append("normal bot path must not mention qqq_100_trend_gate promotion")
    if "qqq_100_trend_gate" in slow_source:
        failures.append("slow-SMA paper execution path must not mention qqq_100_trend_gate promotion")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def function_block(source: str, start_marker: str, end_marker: str) -> str:
    try:
        start = source.index(start_marker)
        end = source.index(end_marker, start)
    except ValueError:
        return ""
    return source[start:end]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
