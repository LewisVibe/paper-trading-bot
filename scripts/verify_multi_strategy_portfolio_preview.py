from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BOT = ROOT / "bot.py"
MODULE = ROOT / "trading_bot" / "research" / "multi_strategy_portfolio_preview.py"
COMMANDS = ["--multi-strategy-portfolio-preview", "--show-multi-strategy-portfolio-preview"]
OUTPUTS = [
    "data/multi_strategy_portfolio_preview.csv",
    "data/multi_strategy_portfolio_preview_summary.csv",
    "data/multi_strategy_portfolio_preview_exposures.csv",
    "data/multi_strategy_portfolio_preview_conflicts.csv",
    "data/multi_strategy_portfolio_preview_blockers.csv",
]

REQUIRED_SCHEMA = [
    "sleeve_name",
    "strategy_name",
    "ticker_or_asset_group",
    "desired_position",
    "preview_status",
    "research_status",
    "source_file",
    "source_status",
    "proposed_portfolio_role",
    "proposed_weight_placeholder",
    "exposure_bucket",
    "overlap_group",
    "conflict_status",
    "blocker",
    "recommended_next_step",
    "research_only",
    "preview_only",
    "portfolio_preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]

SAFETY_FLAG_COLUMNS = [
    "research_only",
    "preview_only",
    "portfolio_preview_only",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "orders_created",
    "orders_submitted",
    "orders_cancelled",
    "sqlite_trade_log_written",
    "discord_alert_sent",
    "telegram_alert_sent",
]

FORBIDDEN_SCHEMA = {
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

FORBIDDEN_SOURCE_PATTERNS = [
    "TradingClient",
    "yfinance",
    "yf.download",
    "download_backtest_prices",
    "get_alpaca_positions",
    "get_open_position",
    "submit_order",
    "cancel_order",
    "replace_order",
    "MarketOrderRequest",
    "LimitOrderRequest",
    "insert_trade_log",
    "send_discord_alert",
    "send_telegram",
    "load_config(",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT)
    module_source = read_text(MODULE)

    verify_command_registered(bot_source, failures)
    verify_source_safety(module_source, failures)
    verify_outputs_ignored(failures)
    verify_generation_with_missing_and_present_inputs(failures)

    if failures:
        print("Multi-strategy portfolio preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Multi-strategy portfolio preview verification passed.")
    print("Verified saved-output-only command, ignored outputs, missing-input tolerance, QQQ100 candidate row, research-only high-growth/crypto blockers, false approvals, and no order/secret columns.")
    return 0


def verify_command_registered(bot_source: str, failures: list[str]) -> None:
    for command in COMMANDS:
        if command not in bot_source:
            failures.append(f"missing command in bot.py: {command}")
    early_route = bot_source.find('["--multi-strategy-portfolio-preview"]')
    broker_import = bot_source.find("from alpaca.trading.client import TradingClient")
    if early_route == -1:
        failures.append("missing early route for multi-strategy portfolio preview")
    elif broker_import != -1 and early_route > broker_import:
        failures.append("multi-strategy portfolio preview should route before Alpaca imports")


def verify_source_safety(module_source: str, failures: list[str]) -> None:
    for token in [
        "multi_strategy_portfolio_preview.csv",
        "multi_strategy_portfolio_preview_summary.csv",
        "multi_strategy_portfolio_preview_exposures.csv",
        "multi_strategy_portfolio_preview_conflicts.csv",
        "multi_strategy_portfolio_preview_blockers.csv",
        "qqq100_core_growth_preview_candidate",
        "high_growth_branch_blocked_research_only",
        "crypto_blocked_research_only",
        "unavailable_or_missing_sleeve",
        "growth_tech_overlap_warning",
        "high_beta_stack_warning",
        "portfolio_combiner_preview_only",
        "execution_blocked",
        "scheduling_not_approved",
        *REQUIRED_SCHEMA,
    ]:
        if token not in module_source:
            failures.append(f"module missing required token: {token}")
    for token in FORBIDDEN_SOURCE_PATTERNS:
        if token in module_source:
            failures.append(f"module must not contain forbidden pattern: {token}")
    forbidden_schema = sorted(FORBIDDEN_SCHEMA.intersection(set(extract_preview_columns(module_source))))
    if forbidden_schema:
        failures.append("preview schema contains forbidden order/secret column(s): " + ", ".join(forbidden_schema))


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in OUTPUTS:
        completed = subprocess.run(["git", "check-ignore", output], cwd=ROOT, text=True, capture_output=True, timeout=10)
        if completed.returncode != 0:
            failures.append(f"generated output is not ignored by git: {output}")


def verify_generation_with_missing_and_present_inputs(failures: list[str]) -> None:
    from trading_bot.research.multi_strategy_portfolio_preview import (  # noqa: PLC0415
        generate_multi_strategy_portfolio_preview,
    )

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = generate_multi_strategy_portfolio_preview(root)
        if not result.preview_rows:
            failures.append("missing inputs should still produce preview rows")
        if not any(row.get("sleeve_name") == "unavailable_or_missing_sleeve" for row in result.preview_rows):
            failures.append("missing-input run should include unavailable_or_missing_sleeve context")
        missing_summary = {row["summary_name"]: row["summary_value"] for row in result.summary_rows}
        if missing_summary.get("final_portfolio_preview_status") != "multi_strategy_portfolio_preview_created":
            failures.append("missing-input run should still create a portfolio preview status")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = root / "data"
        data.mkdir()
        write_csv(
            data / "qqq100_preview_signal_pack.csv",
            [
                {
                    "strategy_name": "qqq_100_trend_gate",
                    "ticker": "QQQ",
                    "desired_position": "long",
                    "data_status": "ok",
                    "trend_state": "above_sma100_trend_gate",
                    "execution_approved": "False",
                    "paper_execution_approved": "False",
                    "scheduling_approved": "False",
                }
            ],
        )
        write_csv(
            data / "high_growth_stock_final_validation_pack.csv",
            [{"final_validation_status": "research_only", "strategy_name": "codex_broad_growth_balanced_breakout_control"}],
        )
        write_csv(
            data / "crypto_research_state_report.csv",
            [{"crypto_status": "research_only", "strategy_name": "crypto_equal_weight_ex_highest_vol_2"}],
        )
        result = generate_multi_strategy_portfolio_preview(root)
        preview_path = root / OUTPUTS[0]
        if not preview_path.exists():
            failures.append("preview output was not written")
            return
        rows = read_csv(preview_path)
        qqq = next((row for row in rows if row.get("strategy_name") == "qqq_100_trend_gate"), {})
        if not qqq:
            failures.append("QQQ100 row missing when saved signal exists")
        elif qqq.get("ticker_or_asset_group") != "QQQ" or qqq.get("desired_position") != "long":
            failures.append("QQQ100 row should preserve QQQ and desired_position from saved signal")
        for flag in [
            "execution_approved",
            "paper_execution_approved",
            "scheduling_approved",
            "orders_created",
            "orders_submitted",
            "orders_cancelled",
            "sqlite_trade_log_written",
            "discord_alert_sent",
            "telegram_alert_sent",
        ]:
            if not rows or any(row.get(flag, "").lower() != "false" for row in rows):
                failures.append(f"{flag} must be false for every preview row")
        high_growth = next((row for row in rows if row.get("sleeve_name") == "high_growth_stock_research_sleeve"), {})
        if high_growth.get("preview_status") != "high_growth_branch_blocked_research_only":
            failures.append("high-growth branch must remain research-only/blocked")
        crypto = next((row for row in rows if row.get("sleeve_name") == "crypto_research_sleeve"), {})
        if crypto.get("preview_status") != "crypto_blocked_research_only":
            failures.append("crypto sleeve must remain research-only/blocked")
        conflicts = read_csv(root / OUTPUTS[3])
        names = {row.get("conflict_name") for row in conflicts}
        if "growth_tech_overlap_warning" not in names:
            failures.append("QQQ + high-growth overlap warning should be present")
        if "high_beta_stack_warning" not in names:
            failures.append("QQQ + crypto high-beta stack warning should be present")
        for column in REQUIRED_SCHEMA:
            if rows and column not in rows[0]:
                failures.append(f"preview output missing schema column: {column}")
        forbidden = FORBIDDEN_SCHEMA.intersection(rows[0].keys()) if rows else set()
        if forbidden:
            failures.append("preview output contains forbidden order/secret columns: " + ", ".join(sorted(forbidden)))
        for output in OUTPUTS:
            output_rows = read_csv(root / output)
            if not output_rows:
                failures.append(f"{output} should contain at least one row")
                continue
            for column in SAFETY_FLAG_COLUMNS:
                if column not in output_rows[0]:
                    failures.append(f"{output} missing safety flag column: {column}")
            for flag in [
                "execution_approved",
                "paper_execution_approved",
                "scheduling_approved",
                "orders_created",
                "orders_submitted",
                "orders_cancelled",
                "sqlite_trade_log_written",
                "discord_alert_sent",
                "telegram_alert_sent",
            ]:
                if any(row.get(flag, "").lower() != "false" for row in output_rows):
                    failures.append(f"{flag} must be false for every row in {output}")


def extract_preview_columns(source: str) -> list[str]:
    start = source.find("PREVIEW_COLUMNS = [")
    end = source.find("]", start)
    if start == -1 or end == -1:
        return []
    block = source[start:end]
    return [part.strip().strip('"') for part in block.splitlines() if part.strip().startswith('"')]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
