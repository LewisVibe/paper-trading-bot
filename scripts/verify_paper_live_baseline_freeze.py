from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "1463e72"
DANGEROUS_PATTERNS = (
    "config.json",
    ".env",
    "data/",
    "logs/",
    ".db",
    ".sqlite",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".webhook",
    "token",
    "secret",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read_text(path: str) -> str:
    full_path = ROOT / path
    if not full_path.exists():
        fail(f"Missing required file: {path}")
    return full_path.read_text(encoding="utf-8")


def function_body(source: str, name: str) -> str:
    match = re.search(rf"^def {re.escape(name)}\(", source, flags=re.MULTILINE)
    if not match:
        fail(f"Missing function: {name}")
    next_match = re.search(r"^def \w+\(", source[match.end() :], flags=re.MULTILINE)
    if next_match:
        return source[match.start() : match.end() + next_match.start()]
    return source[match.start() :]


def git_output(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        fail(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout


def verify_baseline_commit_present() -> None:
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT.as_posix()}",
            "-C",
            str(ROOT),
            "merge-base",
            "--is-ancestor",
            BASELINE_COMMIT,
            "HEAD",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        fail(f"Expected baseline commit {BASELINE_COMMIT} to be an ancestor of HEAD.")


def verify_pytest_foundation() -> None:
    if not (ROOT / "pytest.ini").exists():
        fail("pytest.ini is missing.")
    tests_dir = ROOT / "tests"
    if not tests_dir.is_dir():
        fail("tests/ directory is missing.")
    expected_tests = {
        "test_config.py",
        "test_execution.py",
        "test_qqq100_alignment.py",
    }
    present = {path.name for path in tests_dir.glob("test_*.py")}
    missing = expected_tests - present
    if missing:
        fail(f"Missing expected pytest files: {', '.join(sorted(missing))}")


def verify_normal_bot_monitoring_only(bot_source: str) -> None:
    process_ticker = function_body(bot_source, "process_ticker")
    if "monitor_only" not in process_ticker:
        fail("process_ticker does not record monitor_only status.")
    if "submit_alpaca_order(" in process_ticker:
        fail("process_ticker still calls submit_alpaca_order.")
    if "client.submit_order(" in process_ticker or "MarketOrderRequest(" in process_ticker:
        fail("process_ticker still contains direct order construction/submission.")
    if "position_after=position_before" not in process_ticker:
        fail("process_ticker does not keep position_after at position_before for monitor-only rows.")


def verify_order_submit_calls_are_isolated(
    parser_source: str,
    application_source: str,
    vol_runner_source: str,
    gateway_source: str,
) -> None:
    direct_submitters = []
    for path in (ROOT / "trading_bot").rglob("*.py"):
        if ".submit_order(" in path.read_text(encoding="utf-8"):
            direct_submitters.append(path.relative_to(ROOT).as_posix())
    if direct_submitters != ["trading_bot/paper_orders.py"]:
        fail(f"Direct broker submission must stay isolated to the paper gateway: {direct_submitters}")

    gateway_body = function_body(gateway_source, "submit_paper_order")
    if "client.submit_order(" not in gateway_body:
        fail("The audited paper-order gateway does not contain the broker submission call.")

    manual_body = function_body(application_source, "run_paper_order_test")
    qqq100_body = function_body(application_source, "run_execute_qqq100_paper")
    slow_sma_body = function_body(application_source, "run_slow_sma_paper_execution")
    slow_sma_ticker_body = function_body(application_source, "process_slow_sma_execution_ticker")
    vol_targeted_body = function_body(vol_runner_source, "run_execute_vol_targeted_growth_paper")
    for name, body in {
        "manual paper order": manual_body,
        "QQQ100 paper execution": qqq100_body,
        "slow-SMA paper execution": slow_sma_ticker_body,
        "volatility-targeted paper execution": vol_targeted_body,
    }.items():
        if "submit_paper_order(" not in body:
            fail(f"{name} does not route through the audited paper-order gateway.")

    if "--confirm-paper-order" not in parser_source or "confirm_paper_order" not in manual_body:
        fail("Manual paper-order path is not visibly confirmation-gated.")
    if "--confirm-qqq100-paper" not in parser_source or "confirm_qqq100_paper" not in qqq100_body:
        fail("QQQ100 paper execution path is not visibly confirmation-gated.")
    if "--confirm-slow-sma-paper" not in parser_source or "confirm_slow_sma_paper" not in slow_sma_body:
        fail("Slow-SMA paper execution path is not visibly confirmation-gated.")
    if "--confirm-vol-targeted-growth-paper" not in parser_source or "if not confirmed" not in vol_targeted_body:
        fail("Volatility-targeted paper execution path is not visibly confirmation-gated.")


def verify_paper_only_policy(bot_source: str, config_source: str) -> None:
    if "paper=True" not in bot_source:
        fail("No hardcoded Alpaca paper=True TradingClient usage found.")
    if "paper=False" in bot_source or "paper = False" in bot_source:
        fail("Potential live Alpaca paper=False usage found in bot.py.")
    if "alpaca.paper must be true" not in config_source:
        fail("Config live-mode refusal message is missing.")
    if "paper_kill_switch_enabled" not in config_source:
        fail("paper_kill_switch_enabled is not loaded in config.")


def verify_docs_policy() -> None:
    checklist = read_text("docs/PAPER_LIVE_CHECKLIST.md")
    readme = read_text("README.md")
    workflow = read_text("docs/CODEX_WORKFLOW.md")
    task_board = read_text("docs/HERMES_TASK_BOARD.md")
    review = read_text("docs/external-review/REVIEW.md")
    testing_plan = read_text("docs/external-review/TESTING_PLAN.md")
    combined = "\n".join([checklist, readme, workflow, task_board])

    required_phrases = [
        "normal `python bot.py`",
        "monitoring-only",
        "Alpaca paper only",
        "must not run QQQ100 execution",
        "must not run slow-SMA execution",
        "must not run paper-order tests",
        "Do not use the SMA or slow-SMA strategy as the paper-live strategy",
        "execution_approved",
    ]
    for phrase in required_phrases:
        if phrase not in combined:
            fail(f"Missing paper-live policy documentation phrase: {phrase}")

    for finding in ("F1", "F2", "F3", "F5", "F6", "F7"):
        if finding not in checklist:
            fail(f"PAPER_LIVE_CHECKLIST does not track external review finding {finding}.")
    if "F2" not in review or "F7" not in review:
        fail("External review docs are missing expected F2/F7 finding context.")
    if "qqq100_alignment_action" not in testing_plan:
        fail("External testing plan is missing expected QQQ100 alignment test context.")


def verify_no_dangerous_staged_files() -> None:
    status = git_output(["status", "--porcelain"])
    dangerous: list[str] = []
    for raw_line in status.splitlines():
        if len(raw_line) < 4:
            continue
        staged_status = raw_line[:2]
        path = raw_line[3:].replace("\\", "/")
        if staged_status == "??":
            continue
        if staged_status[0] == " ":
            continue
        normalized = path.lower()
        if any(pattern in normalized for pattern in DANGEROUS_PATTERNS):
            dangerous.append(path)
    if dangerous:
        fail(f"Dangerous/private/generated files are staged: {', '.join(dangerous)}")


def main() -> int:
    normal_runner_source = read_text("trading_bot/runners/paper_execution.py")
    parser_source = read_text("trading_bot/cli/parser.py")
    application_source = read_text("trading_bot/cli/application.py")
    vol_runner_source = read_text("trading_bot/runners/vol_targeted_growth_paper.py")
    gateway_source = read_text("trading_bot/paper_orders.py")
    runtime_source = "\n".join([application_source, vol_runner_source, gateway_source])
    config_source = read_text("trading_bot/config.py")
    verify_baseline_commit_present()
    verify_pytest_foundation()
    verify_normal_bot_monitoring_only(normal_runner_source)
    verify_order_submit_calls_are_isolated(parser_source, application_source, vol_runner_source, gateway_source)
    verify_paper_only_policy(runtime_source, config_source)
    verify_docs_policy()
    verify_no_dangerous_staged_files()
    print("Paper-live baseline freeze verification passed.")
    print("Verified pytest foundation, monitoring-only normal bot, isolated confirmed paper paths, paper-only policy docs, and no dangerous staged files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
