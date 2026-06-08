from __future__ import annotations

import csv
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.research.deployment_readiness as readiness
from trading_bot.research.deployment_readiness import generate_deployment_readiness_report


FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient",
    "MarketOrderRequest",
    "download_close_prices",
    "download_backtest_prices",
    "download_slow_sma_preview_prices",
    "configure_yfinance_cache",
    "get_alpaca_positions",
    "get_open_orders_for_ticker",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "decide_trade",
    "init_database",
    "sqlite3",
]


def main() -> int:
    failures: list[str] = []
    verify_fixture_report(failures)
    verify_missing_git_handling(failures)
    verify_source_safety(failures)

    if failures:
        print("Deployment readiness verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Deployment readiness verification passed.")
    return 0


def verify_fixture_report(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_fixture_project(root)
        result = generate_deployment_readiness_report(root)
        if not result.output_path.exists():
            failures.append("deployment_readiness_report.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != readiness.DEPLOYMENT_READINESS_COLUMNS:
                failures.append("deployment readiness columns changed unexpectedly")
            rows = list(reader)
        if not rows:
            failures.append("deployment readiness report should contain rows")
        for row in rows:
            if row["research_only"] != "True" or row["preview_only"] != "True" or row["execution_approved"] != "False":
                failures.append(f"safety flags failed for {row['check_name']}")
        checks = {row["check_name"]: row for row in rows}
        for required_check in [
            "python_version_compatible",
            "required_packages_importable",
            "config_json_local_presence",
            "core_gitignore_patterns_present",
            "safe_scheduled_command_candidates_documented",
            "must_not_schedule_commands_documented",
        ]:
            if required_check not in checks:
                failures.append(f"missing readiness check: {required_check}")
        config_row = checks.get("config_json_local_presence", {})
        if "super-secret" in config_row.get("finding", ""):
            failures.append("report must not print config.json contents")
        summary = "\n".join(result.summary_lines)
        for expected_text in [
            "DEPLOYMENT READINESS REPORT. REPORTING ONLY. NOT EXECUTION.",
            "--refresh-defensive-research",
            "--refresh-promoted-review",
            "--paper-order-test",
            "--execute-slow-sma-paper",
            "No deployment, scheduling, or execution approval was performed.",
        ]:
            if expected_text not in summary:
                failures.append(f"summary missing expected text: {expected_text}")


def verify_missing_git_handling(failures: list[str]) -> None:
    original = readiness.git_executable
    try:
        readiness.git_executable = lambda: None  # type: ignore[assignment]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_fixture_project(root)
            result = generate_deployment_readiness_report(root)
            checks = {row["check_name"]: row for row in result.rows}
            if checks["git_working_tree_status"]["check_status"] != "not_applicable":
                failures.append("missing Git should mark working tree status not_applicable")
            if checks["git_remote_configured"]["check_status"] != "not_applicable":
                failures.append("missing Git should mark remote status not_applicable")
    finally:
        readiness.git_executable = original  # type: ignore[assignment]


def verify_source_safety(failures: list[str]) -> None:
    source = inspect.getsource(readiness)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in source:
            failures.append(f"deployment readiness should not reference {token}")
    if 'read_text(root / "config.json")' in source or "open(root / \"config.json\"" in source:
        failures.append("deployment readiness must not read config.json contents")


def write_fixture_project(root: Path) -> None:
    (root / "trading_bot").mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "data" / ".gitkeep").write_text("", encoding="utf-8")
    (root / "logs" / ".gitkeep").write_text("", encoding="utf-8")
    (root / "docs" / "CURRENT_STATE.md").write_text("current", encoding="utf-8")
    (root / "requirements.txt").write_text(
        "yfinance>=0.2.54,<0.3.0\nalpaca-py>=0.40.0,<1.0.0\nrequests>=2.32.0,<3.0.0\nmatplotlib>=3.9.0,<4.0.0\n",
        encoding="utf-8",
    )
    (root / "config.example.json").write_text('{"dry_run": true, "allow_shorting": false, "alpaca": {"paper": true}}\n', encoding="utf-8")
    (root / "config.json").write_text('{"api_key": "super-secret"}\n', encoding="utf-8")
    (root / ".gitignore").write_text(
        "\n".join(
            [
                "config.json",
                ".env",
                ".env.*",
                ".venv/",
                "logs/*",
                "!logs/.gitkeep",
                "*.log",
                "data/*",
                "!data/.gitkeep",
                "*.db",
            ]
        ),
        encoding="utf-8",
    )
    (root / "trading_bot" / "config.py").write_text(
        'parse_config_bool(raw, "dry_run", True)\n'
        'parse_config_bool(raw, "allow_shorting", False)\n'
        'raise ConfigError("alpaca.paper must be true")\n',
        encoding="utf-8",
    )
    (root / "bot.py").write_text(
        'parser.add_argument("--paper-order-test")\n'
        'parser.add_argument("--confirm-paper-order")\n'
        'parser.add_argument("--execute-slow-sma-paper")\n'
        'parser.add_argument("--confirm-slow-sma-paper")\n'
        'parser.add_argument("--refresh-defensive-research")\n'
        'parser.add_argument("--refresh-promoted-review")\n'
        'parser.add_argument("--show-promoted-decision")\n'
        'parser.add_argument("--show-crypto-monitor")\n',
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "Windows Task Scheduler setup must be report/display only and is not execution approval.\n"
        "--refresh-defensive-research --refresh-promoted-review --show-promoted-decision --show-crypto-monitor\n",
        encoding="utf-8",
    )
    (root / "scripts" / "verify_repo_safety.py").write_text("print('Result: passed')\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
